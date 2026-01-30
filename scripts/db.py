#!/usr/bin/env python3
"""
LanceDB wrapper for Reality Check.

Provides schema definitions, CRUD operations, and semantic search
for claims, sources, chains, predictions, contradictions, and definitions.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Optional

import lancedb
import pyarrow as pa

if __package__:
    from .analysis_log_writer import upsert_analysis_log_section
    from .usage_capture import (
        estimate_cost_usd,
        parse_usage_from_source,
        get_current_session_path,
        get_session_token_count,
        get_session_token_count_by_uuid,
        list_sessions,
        NoSessionFoundError,
        AmbiguousSessionError,
        _tool_to_provider,
        _extract_uuid_from_filename,
        _get_session_paths,
    )
else:
    from analysis_log_writer import upsert_analysis_log_section
    from usage_capture import (
        estimate_cost_usd,
        parse_usage_from_source,
        get_current_session_path,
        get_session_token_count,
        get_session_token_count_by_uuid,
        list_sessions,
        NoSessionFoundError,
        AmbiguousSessionError,
        _tool_to_provider,
        _extract_uuid_from_filename,
        _get_session_paths,
    )

# Configuration
DB_PATH = Path(os.getenv("REALITYCHECK_DATA", "data/realitycheck.lance"))
EMBEDDING_MODEL = os.getenv("REALITYCHECK_EMBED_MODEL") or os.getenv("EMBEDDING_MODEL") or "all-MiniLM-L6-v2"
EMBEDDING_DIM = int(os.getenv("REALITYCHECK_EMBED_DIM") or os.getenv("EMBEDDING_DIM") or "384")  # default: all-MiniLM-L6-v2 dimension

# Lazy-loaded embedding model
_embedder = None
_embedder_key: Optional[tuple[Any, ...]] = None


def should_skip_embeddings() -> bool:
    """Return True if embedding generation should be skipped (tests/CI/offline)."""
    value = os.getenv("REALITYCHECK_EMBED_SKIP")
    if value is None:
        # Backwards-compatible alias.
        value = os.getenv("SKIP_EMBEDDING_TESTS")
    if not value:
        return False
    normalized = value.strip().lower()
    if normalized in {"0", "false", "no", "off"}:
        return False
    return True


def configure_embedding_threads(*, device: str) -> int:
    """
    Configure CPU threading defaults for embedding workloads.

    On some systems, large OpenMP thread counts can dramatically reduce embedding throughput.
    We force a conservative default unless overridden by REALITYCHECK_EMBED_THREADS.

    Returns the configured thread count (0 for non-CPU devices).
    """
    if device != "cpu":
        return 0

    threads_env = os.getenv("REALITYCHECK_EMBED_THREADS")
    if threads_env is None:
        # Backwards-compatible alias (older naming before EMBED_* standardization).
        threads_env = os.getenv("REALITYCHECK_EMBEDDING_THREADS")
    if threads_env is None:
        # Backwards-compatible alias (pre-namespace cleanup).
        threads_env = os.getenv("EMBEDDING_CPU_THREADS")
    if threads_env is None:
        threads_env = "4"

    try:
        threads = int(threads_env)
    except ValueError:
        threads = 4
    if threads < 1:
        return 0

    # Force thread counts for common runtimes used by PyTorch / tokenizers.
    for var in [
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ]:
        os.environ[var] = str(threads)

    # If torch is already imported, clamp its thread pools too.
    if "torch" in sys.modules:
        try:
            import torch  # type: ignore
        except Exception:
            return threads
        try:
            torch.set_num_threads(threads)
        except Exception:
            pass
        try:
            torch.set_num_interop_threads(max(1, min(threads, 4)))
        except Exception:
            pass

    return threads


class OpenAICompatEmbedder:
    """
    Minimal OpenAI-compatible embeddings client.

    Intended for opt-in remote embedding backends (e.g., OpenAI, vLLM, etc).
    """

    def __init__(self, *, model: str, api_base: str, api_key: str, timeout_seconds: float = 60.0):
        self.model = model
        self.api_base = (api_base or "").rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = float(timeout_seconds)

    def encode(self, texts: Any, **_: Any) -> list[list[float]]:
        if isinstance(texts, str):
            inputs = [texts]
        else:
            inputs = list(texts)

        if not inputs:
            return []

        url = f"{self.api_base}/embeddings"
        payload = {"model": self.model, "input": inputs, "encoding_format": "float"}
        body = json.dumps(payload).encode("utf-8")

        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        req = Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read()
        except HTTPError as e:
            details = ""
            try:
                details = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise ValueError(f"Remote embeddings HTTP {e.code}: {details or e.reason}") from e

        data = json.loads(raw.decode("utf-8"))
        items = data.get("data")
        if not isinstance(items, list):
            raise ValueError(f"Unexpected embeddings response shape: missing 'data' list. keys={sorted(data.keys())}")

        out: list[Optional[list[float]]] = [None] * len(inputs)
        for item in items:
            if not isinstance(item, dict):
                continue
            idx = item.get("index", 0)
            emb = item.get("embedding")
            if not isinstance(idx, int) or idx < 0 or idx >= len(inputs):
                continue
            if not isinstance(emb, list):
                continue
            out[idx] = [float(x) for x in emb]

        if any(v is None for v in out):
            raise ValueError("Remote embeddings response missing one or more vectors.")

        return [v for v in out if v is not None]


def get_embedder():
    """Lazy-load the sentence transformer model."""
    global _embedder, _embedder_key

    provider = (os.getenv("REALITYCHECK_EMBED_PROVIDER") or os.getenv("EMBEDDING_PROVIDER") or "local").strip().lower()
    model_id = os.getenv("REALITYCHECK_EMBED_MODEL") or os.getenv("EMBEDDING_MODEL") or EMBEDDING_MODEL

    if provider == "openai":
        api_base = (
            os.getenv("REALITYCHECK_EMBED_API_BASE")
            or os.getenv("EMBEDDING_API_BASE")
            or os.getenv("OPENAI_API_BASE")
            or "https://api.openai.com/v1"
        )
        api_key = (
            os.getenv("REALITYCHECK_EMBED_API_KEY")
            or os.getenv("EMBEDDING_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )
        if not api_key:
            raise ValueError("REALITYCHECK_EMBED_PROVIDER=openai requires REALITYCHECK_EMBED_API_KEY (or OPENAI_API_KEY).")

        key = ("openai", model_id, api_base)
        if _embedder is None or _embedder_key != key:
            _embedder_key = key
            _embedder = OpenAICompatEmbedder(model=model_id, api_base=api_base, api_key=api_key)
        return _embedder

    if provider not in {"local", "sentence-transformers"}:
        raise ValueError(f"Unknown REALITYCHECK_EMBED_PROVIDER='{provider}'. Supported: local, openai.")

    # Force CPU to avoid GPU driver crashes (especially with ROCm)
    # Users can override with REALITYCHECK_EMBED_DEVICE env var
    device = os.getenv("REALITYCHECK_EMBED_DEVICE") or os.getenv("EMBEDDING_DEVICE") or "cpu"
    key = ("local", model_id, device)
    if _embedder is None or _embedder_key != key:
        _embedder_key = key
        if device == "cpu":
            configure_embedding_threads(device=device)
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer(model_id, device=device)
        if device == "cpu":
            configure_embedding_threads(device=device)
    return _embedder


def embed_text(text: str) -> list[float]:
    """Generate embedding for a text string."""
    return embed_texts([text])[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts (batched)."""
    if not texts:
        return []

    embedder = get_embedder()
    raw = embedder.encode(texts)

    if hasattr(raw, "tolist"):
        raw = raw.tolist()

    # Some embedders return a single vector for a single input. Normalize to list[list[float]].
    if raw and isinstance(raw, list) and raw and isinstance(raw[0], (int, float)):
        embeddings: list[list[float]] = [[float(x) for x in raw]]
    else:
        embeddings = [[float(x) for x in row] for row in raw]

    expected_dim = EMBEDDING_DIM
    for vec in embeddings:
        if len(vec) != expected_dim:
            raise ValueError(
                f"Embedding dim mismatch: got {len(vec)}, expected {expected_dim}. "
                "Set REALITYCHECK_EMBED_DIM to match your model and re-init/migrate the DB schema."
            )

    return embeddings


def get_table_names(db: "lancedb.DBConnection") -> list[str]:
    """Get list of table names from database (handles API changes)."""
    result = db.list_tables()
    # Handle both old API (returns list) and new API (returns ListTablesResponse)
    if hasattr(result, 'tables'):
        return result.tables
    return list(result)


# =============================================================================
# Schema Definitions (PyArrow)
# =============================================================================

CLAIMS_SCHEMA = pa.schema([
    pa.field("id", pa.string(), nullable=False),
    pa.field("text", pa.string(), nullable=False),
    pa.field("type", pa.string(), nullable=False),  # [F]/[T]/[H]/[P]/[A]/[C]/[S]/[X]
    pa.field("domain", pa.string(), nullable=False),
    pa.field("evidence_level", pa.string(), nullable=False),  # E1-E6
    pa.field("credence", pa.float32(), nullable=False),  # 0.0-1.0

    # Operationalization (v1.0 additions)
    pa.field("operationalization", pa.string(), nullable=True),
    pa.field("assumptions", pa.list_(pa.string()), nullable=True),
    pa.field("falsifiers", pa.list_(pa.string()), nullable=True),

    # Provenance
    pa.field("source_ids", pa.list_(pa.string()), nullable=False),
    pa.field("first_extracted", pa.string(), nullable=False),
    pa.field("extracted_by", pa.string(), nullable=False),

    # Relationships
    pa.field("supports", pa.list_(pa.string()), nullable=True),
    pa.field("contradicts", pa.list_(pa.string()), nullable=True),
    pa.field("depends_on", pa.list_(pa.string()), nullable=True),
    pa.field("modified_by", pa.list_(pa.string()), nullable=True),
    pa.field("part_of_chain", pa.string(), nullable=True),

    # Versioning
    pa.field("version", pa.int32(), nullable=False),
    pa.field("last_updated", pa.string(), nullable=False),
    pa.field("notes", pa.string(), nullable=True),

    # Vector embedding
    pa.field("embedding", pa.list_(pa.float32(), EMBEDDING_DIM), nullable=True),
])

SOURCES_SCHEMA = pa.schema([
    pa.field("id", pa.string(), nullable=False),
    pa.field("type", pa.string(), nullable=False),  # PAPER/BOOK/REPORT/ARTICLE/BLOG/SOCIAL/CONVO/INTERVIEW/DATA/FICTION/KNOWLEDGE
    pa.field("title", pa.string(), nullable=False),
    pa.field("author", pa.list_(pa.string()), nullable=False),
    pa.field("year", pa.int32(), nullable=False),
    pa.field("url", pa.string(), nullable=True),
    pa.field("doi", pa.string(), nullable=True),
    pa.field("accessed", pa.string(), nullable=True),
    pa.field("reliability", pa.float32(), nullable=True),  # 0.0-1.0
    pa.field("bias_notes", pa.string(), nullable=True),
    pa.field("claims_extracted", pa.list_(pa.string()), nullable=True),
    pa.field("analysis_file", pa.string(), nullable=True),
    pa.field("topics", pa.list_(pa.string()), nullable=True),
    pa.field("domains", pa.list_(pa.string()), nullable=True),
    pa.field("status", pa.string(), nullable=True),  # cataloged/analyzed/etc.

    # Vector embedding
    pa.field("embedding", pa.list_(pa.float32(), EMBEDDING_DIM), nullable=True),
])

CHAINS_SCHEMA = pa.schema([
    pa.field("id", pa.string(), nullable=False),
    pa.field("name", pa.string(), nullable=False),
    pa.field("thesis", pa.string(), nullable=False),
    pa.field("credence", pa.float32(), nullable=False),  # MIN of step credences
    pa.field("claims", pa.list_(pa.string()), nullable=False),
    pa.field("analysis_file", pa.string(), nullable=True),
    pa.field("weakest_link", pa.string(), nullable=True),
    pa.field("scoring_method", pa.string(), nullable=True),  # MIN/RANGE/CUSTOM

    # Vector embedding
    pa.field("embedding", pa.list_(pa.float32(), EMBEDDING_DIM), nullable=True),
])

PREDICTIONS_SCHEMA = pa.schema([
    pa.field("claim_id", pa.string(), nullable=False),
    pa.field("source_id", pa.string(), nullable=False),
    pa.field("date_made", pa.string(), nullable=True),
    pa.field("target_date", pa.string(), nullable=True),
    pa.field("falsification_criteria", pa.string(), nullable=True),
    pa.field("verification_criteria", pa.string(), nullable=True),
    pa.field("status", pa.string(), nullable=False),  # [P+]/[P~]/[P→]/[P?]/[P←]/[P!]/[P-]/[P∅]
    pa.field("last_evaluated", pa.string(), nullable=True),
    pa.field("evidence_updates", pa.string(), nullable=True),  # JSON-encoded list
])

CONTRADICTIONS_SCHEMA = pa.schema([
    pa.field("id", pa.string(), nullable=False),
    pa.field("claim_a", pa.string(), nullable=False),
    pa.field("claim_b", pa.string(), nullable=False),
    pa.field("conflict_type", pa.string(), nullable=True),  # direct/scope/definition/timescale
    pa.field("likely_cause", pa.string(), nullable=True),
    pa.field("resolution_path", pa.string(), nullable=True),
    pa.field("status", pa.string(), nullable=True),  # open/resolved
])

DEFINITIONS_SCHEMA = pa.schema([
    pa.field("term", pa.string(), nullable=False),
    pa.field("definition", pa.string(), nullable=False),
    pa.field("operational_proxy", pa.string(), nullable=True),
    pa.field("notes", pa.string(), nullable=True),
    pa.field("domain", pa.string(), nullable=True),
    pa.field("analysis_id", pa.string(), nullable=True),
])

ANALYSIS_LOGS_SCHEMA = pa.schema([
    pa.field("id", pa.string(), nullable=False),  # ANALYSIS-YYYY-NNN
    pa.field("source_id", pa.string(), nullable=False),
    pa.field("analysis_file", pa.string(), nullable=True),
    pa.field("pass", pa.int32(), nullable=False),  # Pass number for this source
    pa.field("status", pa.string(), nullable=False),  # started|completed|failed|canceled|draft
    pa.field("tool", pa.string(), nullable=False),  # claude-code|codex|amp|manual|other
    pa.field("command", pa.string(), nullable=True),  # check|analyze|extract|...
    pa.field("model", pa.string(), nullable=True),
    pa.field("framework_version", pa.string(), nullable=True),
    pa.field("methodology_version", pa.string(), nullable=True),
    pa.field("started_at", pa.string(), nullable=True),  # ISO timestamp
    pa.field("completed_at", pa.string(), nullable=True),  # ISO timestamp
    pa.field("duration_seconds", pa.int32(), nullable=True),
    pa.field("tokens_in", pa.int32(), nullable=True),
    pa.field("tokens_out", pa.int32(), nullable=True),
    pa.field("total_tokens", pa.int32(), nullable=True),
    pa.field("cost_usd", pa.float32(), nullable=True),
    # Delta accounting fields (token usage capture)
    pa.field("tokens_baseline", pa.int32(), nullable=True),  # Session tokens at check start
    pa.field("tokens_final", pa.int32(), nullable=True),  # Session tokens at check end
    pa.field("tokens_check", pa.int32(), nullable=True),  # Total for this check (final - baseline)
    pa.field("usage_provider", pa.string(), nullable=True),  # claude|codex|amp
    pa.field("usage_mode", pa.string(), nullable=True),  # per_message_sum|windowed_sum|counter_delta|manual
    pa.field("usage_session_id", pa.string(), nullable=True),  # Session UUID (portable)
    # Synthesis linking fields
    pa.field("inputs_source_ids", pa.list_(pa.string()), nullable=True),  # Source IDs feeding synthesis
    pa.field("inputs_analysis_ids", pa.list_(pa.string()), nullable=True),  # Analysis log IDs feeding synthesis
    pa.field("stages_json", pa.string(), nullable=True),  # JSON-encoded per-stage metrics
    pa.field("claims_extracted", pa.list_(pa.string()), nullable=True),
    pa.field("claims_updated", pa.list_(pa.string()), nullable=True),
    pa.field("notes", pa.string(), nullable=True),
    pa.field("git_commit", pa.string(), nullable=True),
    pa.field("created_at", pa.string(), nullable=False),  # ISO timestamp
])

# Valid analysis log statuses
VALID_ANALYSIS_STATUSES = {"started", "completed", "failed", "canceled", "draft"}

# Valid analysis log tools
VALID_ANALYSIS_TOOLS = {"claude-code", "codex", "amp", "manual", "other"}

# =============================================================================
# Evidence Links Schema (Epistemic Provenance)
# =============================================================================

EVIDENCE_LINKS_SCHEMA = pa.schema([
    pa.field("id", pa.string(), nullable=False),  # EVLINK-YYYY-NNN
    pa.field("claim_id", pa.string(), nullable=False),
    pa.field("source_id", pa.string(), nullable=False),
    pa.field("direction", pa.string(), nullable=False),  # supports|contradicts|strengthens|weakens
    pa.field("status", pa.string(), nullable=False),  # active|superseded|retracted
    pa.field("supersedes_id", pa.string(), nullable=True),  # Pointer for corrections
    pa.field("strength", pa.float32(), nullable=True),  # Coarse impact estimate
    pa.field("location", pa.string(), nullable=True),  # Specific location in source
    pa.field("quote", pa.string(), nullable=True),  # Relevant excerpt
    pa.field("reasoning", pa.string(), nullable=True),  # Why this evidence matters
    pa.field("analysis_log_id", pa.string(), nullable=True),  # Link to audit log pass
    pa.field("created_at", pa.string(), nullable=False),  # ISO timestamp
    pa.field("created_by", pa.string(), nullable=False),  # Tool/user that created this
])

# Valid evidence link directions
VALID_EVIDENCE_DIRECTIONS = {"supports", "contradicts", "strengthens", "weakens"}

# Valid evidence link statuses
VALID_EVIDENCE_STATUSES = {"active", "superseded", "retracted"}

# =============================================================================
# Reasoning Trails Schema (Epistemic Provenance)
# =============================================================================

REASONING_TRAILS_SCHEMA = pa.schema([
    pa.field("id", pa.string(), nullable=False),  # REASON-YYYY-NNN
    pa.field("claim_id", pa.string(), nullable=False),
    pa.field("status", pa.string(), nullable=False),  # active|superseded
    pa.field("supersedes_id", pa.string(), nullable=True),
    pa.field("credence_at_time", pa.float32(), nullable=False),
    pa.field("evidence_level_at_time", pa.string(), nullable=False),
    pa.field("evidence_summary", pa.string(), nullable=True),
    pa.field("supporting_evidence", pa.list_(pa.string()), nullable=True),  # Evidence link IDs
    pa.field("contradicting_evidence", pa.list_(pa.string()), nullable=True),  # Evidence link IDs
    pa.field("assumptions_made", pa.list_(pa.string()), nullable=True),
    pa.field("counterarguments_json", pa.string(), nullable=True),  # JSON-encoded list
    pa.field("reasoning_text", pa.string(), nullable=False),  # Publishable rationale
    pa.field("analysis_pass", pa.int32(), nullable=True),
    pa.field("analysis_log_id", pa.string(), nullable=True),  # Link to audit log pass
    pa.field("created_at", pa.string(), nullable=False),  # ISO timestamp
    pa.field("created_by", pa.string(), nullable=False),  # Tool/user that created this
])

# Valid reasoning trail statuses
VALID_REASONING_STATUSES = {"active", "superseded"}

# Valid counterargument dispositions (for validation)
VALID_COUNTERARGUMENT_DISPOSITIONS = {"integrated", "discounted", "unresolved"}

# Domain mapping for migration (old -> new)
DOMAIN_MIGRATION = {
    "VALUE": "ECON",
    "DIST": "ECON",
    "SOCIAL": "SOC",
}

# All valid domains in v1.0
VALID_DOMAINS = {
    "LABOR", "ECON", "GOV", "TECH", "SOC", "RESOURCE", "TRANS", "META",
    "GEO", "INST", "RISK"
}


# =============================================================================
# Database Connection
# =============================================================================

def get_db(db_path: Optional[Path] = None) -> lancedb.DBConnection:
    """Get a connection to the LanceDB database."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(path))


def init_tables(db: Optional[lancedb.DBConnection] = None) -> dict[str, Any]:
    """Initialize all tables with their schemas. Returns table references."""
    if db is None:
        db = get_db()

    tables = {}
    table_configs = [
        ("claims", CLAIMS_SCHEMA),
        ("sources", SOURCES_SCHEMA),
        ("chains", CHAINS_SCHEMA),
        ("predictions", PREDICTIONS_SCHEMA),
        ("contradictions", CONTRADICTIONS_SCHEMA),
        ("definitions", DEFINITIONS_SCHEMA),
        ("analysis_logs", ANALYSIS_LOGS_SCHEMA),
        ("evidence_links", EVIDENCE_LINKS_SCHEMA),
        ("reasoning_trails", REASONING_TRAILS_SCHEMA),
    ]

    existing_tables = get_table_names(db)
    for table_name, schema in table_configs:
        if table_name in existing_tables:
            tables[table_name] = db.open_table(table_name)
        else:
            tables[table_name] = db.create_table(table_name, schema=schema)

    return tables


def drop_tables(db: Optional[lancedb.DBConnection] = None) -> None:
    """Drop all tables (for testing/reset)."""
    if db is None:
        db = get_db()

    existing_tables = get_table_names(db)
    for table_name in ["claims", "sources", "chains", "predictions", "contradictions", "definitions", "analysis_logs", "evidence_links", "reasoning_trails"]:
        if table_name in existing_tables:
            db.drop_table(table_name)


# =============================================================================
# CRUD Operations - Claims
# =============================================================================

def _upsert_source_claim_backlink(source_id: str, claim_id: str, db: lancedb.DBConnection) -> None:
    source = get_source(source_id, db)
    if not source:
        return

    source = _ensure_python_types(source)
    claims_extracted = list(source.get("claims_extracted") or [])
    if claim_id in claims_extracted:
        return

    claims_extracted.append(claim_id)
    db.open_table("sources").update(where=f"id = '{source_id}'", values={"claims_extracted": claims_extracted})


def _remove_source_claim_backlink(source_id: str, claim_id: str, db: lancedb.DBConnection) -> None:
    source = get_source(source_id, db)
    if not source:
        return

    source = _ensure_python_types(source)
    claims_extracted = list(source.get("claims_extracted") or [])
    if claim_id not in claims_extracted:
        return

    claims_extracted = [cid for cid in claims_extracted if cid != claim_id]
    # LanceDB update can error when setting list fields to an empty list.
    value: list[str] | None = claims_extracted if claims_extracted else None
    db.open_table("sources").update(where=f"id = '{source_id}'", values={"claims_extracted": value})


def _sync_source_claim_backlinks(
    claim_id: str,
    old_source_ids: list[str],
    new_source_ids: list[str],
    db: lancedb.DBConnection,
) -> None:
    old_set = set(old_source_ids or [])
    new_set = set(new_source_ids or [])

    for source_id in sorted(old_set - new_set):
        _remove_source_claim_backlink(source_id, claim_id, db)

    for source_id in sorted(new_set - old_set):
        _upsert_source_claim_backlink(source_id, claim_id, db)


def _ensure_prediction_for_claim(claim: dict, db: lancedb.DBConnection) -> None:
    """Create a stub prediction record for [P] claims if missing.

    This keeps `validate.py` happy without forcing manual prediction entry on first pass.
    """
    if claim.get("type") != "[P]":
        return

    claim_id = claim.get("id")
    if not claim_id:
        return

    if get_prediction(claim_id, db):
        return

    source_ids = list(claim.get("source_ids") or [])
    if not source_ids:
        return

    prediction = {
        "claim_id": claim_id,
        "source_id": source_ids[0],
        "date_made": str(date.today()),
        "target_date": None,
        "falsification_criteria": None,
        "verification_criteria": None,
        "status": "[P?]",
        "last_evaluated": None,
        "evidence_updates": None,
    }
    add_prediction(prediction, db)


def add_claim(claim: dict, db: Optional[lancedb.DBConnection] = None, generate_embedding: bool = True) -> str:
    """Add a claim to the database. Returns the claim ID.

    Raises ValueError if a claim with the same ID already exists.
    """
    if db is None:
        db = get_db()

    table = db.open_table("claims")

    # Check for duplicate ID
    claim_id = claim.get("id")
    if claim_id:
        existing = table.search().where(f"id = '{claim_id}'", prefilter=True).limit(1).to_list()
        if existing:
            raise ValueError(f"Claim with ID '{claim_id}' already exists. Use update_claim() to modify or delete first.")

    # Generate embedding if requested and not provided
    if generate_embedding and claim.get("embedding") is None:
        claim["embedding"] = embed_text(claim["text"])

    # Ensure list fields are lists
    for list_field in ["source_ids", "supports", "contradicts", "depends_on", "modified_by", "assumptions", "falsifiers"]:
        if claim.get(list_field) is None:
            claim[list_field] = []

    table.add([claim])

    claim_id = claim["id"]
    for source_id in claim.get("source_ids") or []:
        _upsert_source_claim_backlink(source_id, claim_id, db)

    _ensure_prediction_for_claim(claim, db)
    return claim["id"]


def get_claim(claim_id: str, db: Optional[lancedb.DBConnection] = None) -> Optional[dict]:
    """Get a claim by ID."""
    if db is None:
        db = get_db()

    table = db.open_table("claims")
    results = table.search().where(f"id = '{claim_id}'", prefilter=True).limit(1).to_list()
    return results[0] if results else None


def _ensure_python_types(record: dict) -> dict:
    """Ensure all values in a record are Python native types (not PyArrow types)."""
    result = {}
    for key, value in record.items():
        if hasattr(value, 'tolist'):  # numpy array
            result[key] = value.tolist()
        elif hasattr(value, 'to_pylist'):  # pyarrow array
            result[key] = value.to_pylist()
        elif isinstance(value, (list, tuple)):
            result[key] = [v.as_py() if hasattr(v, 'as_py') else v for v in value]
        elif hasattr(value, 'as_py'):  # pyarrow scalar
            result[key] = value.as_py()
        else:
            result[key] = value
    return result


def update_claim(claim_id: str, updates: dict, db: Optional[lancedb.DBConnection] = None) -> bool:
    """Update a claim. Returns True if successful."""
    if db is None:
        db = get_db()

    # Get existing claim
    existing = get_claim(claim_id, db)
    if not existing:
        return False

    # Convert to Python native types
    existing = _ensure_python_types(existing)
    old_source_ids = list(existing.get("source_ids") or [])

    # Merge updates
    existing.update(updates)
    new_source_ids = list(existing.get("source_ids") or [])

    # Regenerate embedding if text changed
    if "text" in updates:
        existing["embedding"] = embed_text(existing["text"])

    # Increment version
    existing["version"] = existing.get("version", 1) + 1
    existing["last_updated"] = str(date.today())

    # Convert to PyArrow table with explicit schema to avoid type inference issues
    table = db.open_table("claims")
    target_schema = table.schema

    # Create arrays with explicit types for each field
    arrays = []
    for field in target_schema:
        value = existing.get(field.name)
        if pa.types.is_list(field.type):
            # For list fields, ensure proper typing even for empty lists
            if value is None or len(value) == 0:
                arr = pa.array([[]], type=field.type)
            else:
                arr = pa.array([value], type=field.type)
        elif pa.types.is_fixed_size_list(field.type):
            # Handle embedding field
            arr = pa.array([value], type=field.type)
        else:
            arr = pa.array([value], type=field.type)
        arrays.append(arr)

    pa_table = pa.Table.from_arrays(arrays, schema=target_schema)

    # Delete and re-add (LanceDB doesn't have native update)
    table.delete(f"id = '{claim_id}'")
    table.add(pa_table)

    _sync_source_claim_backlinks(claim_id, old_source_ids, new_source_ids, db)
    _ensure_prediction_for_claim(existing, db)
    return True


def _replace_claim_row_for_import(
    claim_id: str,
    incoming: dict,
    db: lancedb.DBConnection,
    *,
    generate_embedding: bool,
) -> None:
    """Replace an existing claim row during import without bumping version/last_updated.

    Semantics: merge the incoming fields onto the existing claim record, then write the
    merged record back to the DB, syncing backlinks and ensuring [P] prediction stubs.
    """
    existing = get_claim(claim_id, db)
    if not existing:
        raise ValueError(f"Claim not found: {claim_id}")

    existing_py = _ensure_python_types(existing)
    old_source_ids = list(existing_py.get("source_ids") or [])

    merged = dict(existing_py)
    merged.update(incoming)
    merged["id"] = claim_id

    # Normalize list fields.
    for list_field in ["source_ids", "supports", "contradicts", "depends_on", "modified_by", "assumptions", "falsifiers"]:
        if merged.get(list_field) is None:
            merged[list_field] = []

    incoming_embedding_provided = "embedding" in incoming and incoming.get("embedding") is not None
    text_changed = merged.get("text") != existing_py.get("text")

    # Keep embeddings consistent with the text when possible.
    if generate_embedding:
        if not incoming_embedding_provided and (text_changed or merged.get("embedding") is None):
            merged["embedding"] = embed_text(str(merged.get("text") or ""))
    else:
        # Avoid keeping a stale embedding when the text changed but we aren't allowed to regenerate.
        if text_changed and not incoming_embedding_provided:
            merged["embedding"] = None

    new_source_ids = list(merged.get("source_ids") or [])

    table = db.open_table("claims")
    target_schema = table.schema

    arrays = []
    for field in target_schema:
        value = merged.get(field.name)
        if pa.types.is_list(field.type):
            if value is None or len(value) == 0:
                arr = pa.array([[]], type=field.type)
            else:
                arr = pa.array([value], type=field.type)
        elif pa.types.is_fixed_size_list(field.type):
            arr = pa.array([value], type=field.type)
        else:
            arr = pa.array([value], type=field.type)
        arrays.append(arr)

    pa_table = pa.Table.from_arrays(arrays, schema=target_schema)

    table.delete(f"id = '{claim_id}'")
    table.add(pa_table)

    _sync_source_claim_backlinks(claim_id, old_source_ids, new_source_ids, db)
    _ensure_prediction_for_claim(merged, db)


def delete_claim(claim_id: str, db: Optional[lancedb.DBConnection] = None) -> bool:
    """Delete a claim by ID."""
    if db is None:
        db = get_db()

    existing = get_claim(claim_id, db)
    source_ids = list(existing.get("source_ids") or []) if existing else []

    table = db.open_table("claims")
    table.delete(f"id = '{claim_id}'")

    # Remove backlinks from sources (best-effort).
    for source_id in source_ids:
        _remove_source_claim_backlink(source_id, claim_id, db)

    # Delete any prediction record associated with this claim.
    try:
        db.open_table("predictions").delete(f"claim_id = '{claim_id}'")
    except Exception:
        pass
    return True


def list_claims(
    domain: Optional[str] = None,
    claim_type: Optional[str] = None,
    limit: int = 100,
    db: Optional[lancedb.DBConnection] = None
) -> list[dict]:
    """List claims with optional filtering."""
    if db is None:
        db = get_db()

    table = db.open_table("claims")
    query = table.search()

    filters = []
    if domain:
        filters.append(f"domain = '{domain}'")
    if claim_type:
        filters.append(f"type = '{claim_type}'")

    if filters:
        query = query.where(" AND ".join(filters), prefilter=True)

    return query.limit(limit).to_list()


def search_claims(
    query_text: str,
    limit: int = 10,
    domain: Optional[str] = None,
    db: Optional[lancedb.DBConnection] = None
) -> list[dict]:
    """Semantic search for claims."""
    if db is None:
        db = get_db()

    table = db.open_table("claims")
    query_embedding = embed_text(query_text)

    search = table.search(query_embedding)

    if domain:
        search = search.where(f"domain = '{domain}'", prefilter=True)

    return search.limit(limit).to_list()


def get_related_claims(claim_id: str, db: Optional[lancedb.DBConnection] = None) -> dict:
    """Get all claims related to a given claim."""
    if db is None:
        db = get_db()

    claim = get_claim(claim_id, db)
    if not claim:
        return {}

    result = {
        "supports": [],
        "contradicts": [],
        "depends_on": [],
        "modified_by": [],
        "supported_by": [],
        "contradicted_by": [],
        "depended_on_by": [],
        "modifies": [],
    }

    # Forward relationships
    for rel_type in ["supports", "contradicts", "depends_on", "modified_by"]:
        for related_id in claim.get(rel_type, []):
            related = get_claim(related_id, db)
            if related:
                result[rel_type].append(related)

    # Reverse relationships (find claims that point to this one)
    all_claims = list_claims(limit=10000, db=db)
    for other in all_claims:
        if other["id"] == claim_id:
            continue
        if claim_id in other.get("supports", []):
            result["supported_by"].append(other)
        if claim_id in other.get("contradicts", []):
            result["contradicted_by"].append(other)
        if claim_id in other.get("depends_on", []):
            result["depended_on_by"].append(other)
        if claim_id in other.get("modified_by", []):
            result["modifies"].append(other)

    return result


# =============================================================================
# CRUD Operations - Sources
# =============================================================================

def add_source(source: dict, db: Optional[lancedb.DBConnection] = None, generate_embedding: bool = True) -> str:
    """Add a source to the database."""
    if db is None:
        db = get_db()

    table = db.open_table("sources")

    # Check for duplicate ID
    source_id = source.get("id")
    if source_id:
        existing = table.search().where(f"id = '{source_id}'", prefilter=True).limit(1).to_list()
        if existing:
            raise ValueError(f"Source with ID '{source_id}' already exists. Use update_source() to modify or delete first.")

    # Generate embedding from title + bias_notes
    if generate_embedding and source.get("embedding") is None:
        embed_text_parts = [source.get("title", "")]
        if source.get("bias_notes"):
            embed_text_parts.append(source["bias_notes"])
        source["embedding"] = embed_text(". ".join(embed_text_parts))

    # Ensure list fields
    for list_field in ["author", "claims_extracted", "topics", "domains"]:
        if source.get(list_field) is None:
            source[list_field] = []

    table.add([source])
    return source["id"]


def get_source(source_id: str, db: Optional[lancedb.DBConnection] = None) -> Optional[dict]:
    """Get a source by ID."""
    if db is None:
        db = get_db()

    table = db.open_table("sources")
    results = table.search().where(f"id = '{source_id}'", prefilter=True).limit(1).to_list()
    return results[0] if results else None


def update_source(
    source_id: str,
    updates: dict,
    db: Optional[lancedb.DBConnection] = None,
    generate_embedding: bool = True,
) -> bool:
    """Update a source. Returns True if successful."""
    if db is None:
        db = get_db()

    existing = get_source(source_id, db)
    if not existing:
        return False

    # Regenerate embedding if title or bias_notes changed.
    updates_to_apply = dict(updates)
    if generate_embedding and ("title" in updates or "bias_notes" in updates):
        merged = _ensure_python_types(existing)
        merged.update(updates)
        embed_text_parts = [merged.get("title", "")]
        if merged.get("bias_notes"):
            embed_text_parts.append(merged["bias_notes"])
        updates_to_apply["embedding"] = embed_text(". ".join(embed_text_parts))

    # Normalize list fields. For nullable list fields, prefer None over [] to avoid
    # LanceDB update issues when writing an empty list.
    if "author" in updates_to_apply and updates_to_apply["author"] is None:
        updates_to_apply["author"] = []
    for list_field in ["claims_extracted", "topics", "domains"]:
        if list_field in updates_to_apply and (updates_to_apply[list_field] is None or updates_to_apply[list_field] == []):
            updates_to_apply[list_field] = None

    table = db.open_table("sources")
    table.update(where=f"id = '{source_id}'", values=updates_to_apply)
    return True


def list_sources(
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Optional[lancedb.DBConnection] = None
) -> list[dict]:
    """List sources with optional filtering."""
    if db is None:
        db = get_db()

    table = db.open_table("sources")
    query = table.search()

    filters = []
    if source_type:
        filters.append(f"type = '{source_type}'")
    if status:
        filters.append(f"status = '{status}'")

    if filters:
        query = query.where(" AND ".join(filters), prefilter=True)

    return query.limit(limit).to_list()


def search_sources(query_text: str, limit: int = 10, db: Optional[lancedb.DBConnection] = None) -> list[dict]:
    """Semantic search for sources."""
    if db is None:
        db = get_db()

    table = db.open_table("sources")
    query_embedding = embed_text(query_text)
    return table.search(query_embedding).limit(limit).to_list()


# =============================================================================
# CRUD Operations - Chains
# =============================================================================

def add_chain(chain: dict, db: Optional[lancedb.DBConnection] = None, generate_embedding: bool = True) -> str:
    """Add an argument chain to the database."""
    if db is None:
        db = get_db()

    table = db.open_table("chains")

    if generate_embedding and chain.get("embedding") is None:
        chain["embedding"] = embed_text(f"{chain['name']}. {chain['thesis']}")

    if chain.get("claims") is None:
        chain["claims"] = []

    table.add([chain])
    return chain["id"]


def get_chain(chain_id: str, db: Optional[lancedb.DBConnection] = None) -> Optional[dict]:
    """Get a chain by ID."""
    if db is None:
        db = get_db()

    table = db.open_table("chains")
    results = table.search().where(f"id = '{chain_id}'", prefilter=True).limit(1).to_list()
    return results[0] if results else None


def list_chains(limit: int = 100, db: Optional[lancedb.DBConnection] = None) -> list[dict]:
    """List all chains."""
    if db is None:
        db = get_db()

    table = db.open_table("chains")
    return table.search().limit(limit).to_list()


# =============================================================================
# CRUD Operations - Predictions
# =============================================================================

def add_prediction(prediction: dict, db: Optional[lancedb.DBConnection] = None) -> str:
    """Add a prediction to the database."""
    if db is None:
        db = get_db()

    table = db.open_table("predictions")
    table.add([prediction])
    return prediction["claim_id"]


def get_prediction(claim_id: str, db: Optional[lancedb.DBConnection] = None) -> Optional[dict]:
    """Get a prediction by claim ID."""
    if db is None:
        db = get_db()

    table = db.open_table("predictions")
    results = table.search().where(f"claim_id = '{claim_id}'", prefilter=True).limit(1).to_list()
    return results[0] if results else None


def list_predictions(status: Optional[str] = None, limit: int = 100, db: Optional[lancedb.DBConnection] = None) -> list[dict]:
    """List predictions with optional status filter."""
    if db is None:
        db = get_db()

    table = db.open_table("predictions")
    query = table.search()

    if status:
        query = query.where(f"status = '{status}'", prefilter=True)

    return query.limit(limit).to_list()


# =============================================================================
# CRUD Operations - Contradictions
# =============================================================================

def add_contradiction(contradiction: dict, db: Optional[lancedb.DBConnection] = None) -> str:
    """Add a contradiction to the database."""
    if db is None:
        db = get_db()

    table = db.open_table("contradictions")
    table.add([contradiction])
    return contradiction["id"]


def list_contradictions(status: Optional[str] = None, limit: int = 100, db: Optional[lancedb.DBConnection] = None) -> list[dict]:
    """List contradictions."""
    if db is None:
        db = get_db()

    table = db.open_table("contradictions")
    query = table.search()

    if status:
        query = query.where(f"status = '{status}'", prefilter=True)

    return query.limit(limit).to_list()


# =============================================================================
# CRUD Operations - Definitions
# =============================================================================

def add_definition(definition: dict, db: Optional[lancedb.DBConnection] = None) -> str:
    """Add a working definition to the database."""
    if db is None:
        db = get_db()

    table = db.open_table("definitions")
    table.add([definition])
    return definition["term"]


def get_definition(term: str, db: Optional[lancedb.DBConnection] = None) -> Optional[dict]:
    """Get a definition by term."""
    if db is None:
        db = get_db()

    table = db.open_table("definitions")
    results = table.search().where(f"term = '{term}'", prefilter=True).limit(1).to_list()
    return results[0] if results else None


def list_definitions(domain: Optional[str] = None, limit: int = 100, db: Optional[lancedb.DBConnection] = None) -> list[dict]:
    """List definitions."""
    if db is None:
        db = get_db()

    table = db.open_table("definitions")
    query = table.search()

    if domain:
        query = query.where(f"domain = '{domain}'", prefilter=True)

    return query.limit(limit).to_list()


# =============================================================================
# CRUD Operations - Analysis Logs
# =============================================================================

def _generate_analysis_id(db: Optional[lancedb.DBConnection] = None) -> str:
    """Generate the next analysis log ID."""
    if db is None:
        db = get_db()

    year = date.today().year
    existing = list_analysis_logs(limit=10000, db=db)

    max_counter = 0
    prefix = f"ANALYSIS-{year}-"
    for log in existing:
        if log["id"].startswith(prefix):
            try:
                counter = int(log["id"].split("-")[-1])
                max_counter = max(max_counter, counter)
            except ValueError:
                pass

    return f"ANALYSIS-{year}-{max_counter + 1:03d}"


def _compute_pass_number(source_id: str, db: Optional[lancedb.DBConnection] = None) -> int:
    """Compute the next pass number for a source_id."""
    if db is None:
        db = get_db()

    existing = list_analysis_logs(source_id=source_id, limit=10000, db=db)
    if not existing:
        return 1

    max_pass = max(log.get("pass", 0) for log in existing)
    return max_pass + 1


def add_analysis_log(
    log: dict,
    db: Optional[lancedb.DBConnection] = None,
    auto_pass: bool = True,
) -> str:
    """Add an analysis log to the database. Returns the log ID.

    If auto_pass is True and 'pass' is not provided, automatically computes
    the next pass number for the source_id.
    """
    if db is None:
        db = get_db()

    table = db.open_table("analysis_logs")

    # Generate ID if not provided
    if not log.get("id"):
        log["id"] = _generate_analysis_id(db)

    # Auto-compute pass number if not provided
    if auto_pass and log.get("pass") is None:
        log["pass"] = _compute_pass_number(log["source_id"], db)

    # Set created_at if not provided
    if not log.get("created_at"):
        from datetime import datetime
        log["created_at"] = datetime.utcnow().isoformat() + "Z"

    # Ensure list fields are lists (pyarrow requires actual lists, not None)
    for list_field in ["claims_extracted", "claims_updated", "inputs_source_ids", "inputs_analysis_ids"]:
        if log.get(list_field) is None:
            log[list_field] = []

    table.add([log])
    return log["id"]


def _project_root_from_db_path(db_path: Path) -> Path:
    resolved = db_path.expanduser().resolve()
    if resolved.parent.name == "data":
        return resolved.parent.parent
    return resolved.parent


def find_project_root(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find a Reality Check data project root by searching upward from start_dir.

    Project markers (first match wins):
    - `.realitycheck.yaml` (preferred)
    - `data/realitycheck.lance` (default DB location; requires basic project structure)
    """
    current = (start_dir or Path.cwd()).expanduser().resolve()
    while True:
        if (current / ".realitycheck.yaml").is_file():
            return current
        db_dir = current / "data" / "realitycheck.lance"
        if db_dir.is_dir():
            # Avoid false positives in arbitrary directories by requiring some minimal
            # project structure alongside the DB directory.
            if any((current / name).exists() for name in ["analysis", "tracking", "inbox", ".git"]):
                return current
        if current.parent == current:
            return None
        current = current.parent


def resolve_db_path_from_project_root(project_root: Path) -> Path:
    """Resolve the LanceDB path for a data project root (best-effort)."""
    config_path = project_root / ".realitycheck.yaml"
    if config_path.is_file():
        try:
            import yaml

            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            db_path = data.get("db_path")
            if isinstance(db_path, str) and db_path.strip():
                candidate = (project_root / db_path.strip()).expanduser()
                return candidate.resolve()
        except Exception:
            pass
    return (project_root / "data" / "realitycheck.lance").resolve()


def _maybe_autodetect_db_path(command: Optional[str]) -> bool:
    """If REALITYCHECK_DATA is unset, try to auto-detect and set it.

    Returns True if a DB path was detected and set.
    """
    global DB_PATH

    if os.getenv("REALITYCHECK_DATA"):
        return True

    project_root = find_project_root(Path.cwd())
    if not project_root:
        return False

    detected_db = resolve_db_path_from_project_root(project_root)
    os.environ["REALITYCHECK_DATA"] = str(detected_db)
    DB_PATH = Path(str(detected_db))

    # Avoid noisy output for commands that already print their own guidance.
    if command not in {"doctor"}:
        print(
            f"Note: REALITYCHECK_DATA is not set; auto-detected database at '{detected_db}'.",
            file=sys.stderr,
        )
    return True


def get_analysis_log(log_id: str, db: Optional[lancedb.DBConnection] = None) -> Optional[dict]:
    """Get an analysis log by ID."""
    if db is None:
        db = get_db()

    table = db.open_table("analysis_logs")
    results = table.search().where(f"id = '{log_id}'", prefilter=True).limit(1).to_list()
    return results[0] if results else None


def list_analysis_logs(
    source_id: Optional[str] = None,
    tool: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Optional[lancedb.DBConnection] = None,
) -> list[dict]:
    """List analysis logs with optional filters."""
    if db is None:
        db = get_db()

    table = db.open_table("analysis_logs")
    query = table.search()

    filters = []
    if source_id:
        filters.append(f"source_id = '{source_id}'")
    if tool:
        filters.append(f"tool = '{tool}'")
    if status:
        filters.append(f"status = '{status}'")

    if filters:
        query = query.where(" AND ".join(filters), prefilter=True)

    return query.limit(limit).to_list()


def update_analysis_log(
    log_id: str,
    db: Optional[lancedb.DBConnection] = None,
    **fields,
) -> None:
    """Update an existing analysis log with partial fields.

    Raises ValueError if log_id is not found.

    Usage:
        update_analysis_log("ANALYSIS-2026-001", status="completed", tokens_check=500)
    """
    if db is None:
        db = get_db()

    # Get existing record
    existing = get_analysis_log(log_id, db)
    if not existing:
        raise ValueError(f"Analysis log '{log_id}' not found")

    # Merge updates into existing record
    updated = dict(existing)
    for key, value in fields.items():
        if value is not None:
            updated[key] = value

    # Ensure all schema fields exist with proper defaults for new fields
    # (handles migration from old schema to new)
    list_fields = ["claims_extracted", "claims_updated", "inputs_source_ids", "inputs_analysis_ids"]
    for field in list_fields:
        val = updated.get(field)
        if val is None:
            updated[field] = []
        else:
            # Convert pyarrow/numpy arrays back to plain Python lists
            updated[field] = list(val) if hasattr(val, '__iter__') and not isinstance(val, str) else []

    nullable_fields = [
        "tokens_baseline", "tokens_final", "tokens_check",
        "usage_provider", "usage_mode", "usage_session_id",
    ]
    for field in nullable_fields:
        if field not in updated:
            updated[field] = None

    # Remove any fields that aren't in the schema (e.g., _rowid from LanceDB)
    schema_fields = {
        "id", "source_id", "analysis_file", "pass", "status", "tool", "command",
        "model", "framework_version", "methodology_version", "started_at",
        "completed_at", "duration_seconds", "tokens_in", "tokens_out",
        "total_tokens", "cost_usd", "tokens_baseline", "tokens_final",
        "tokens_check", "usage_provider", "usage_mode", "usage_session_id",
        "inputs_source_ids", "inputs_analysis_ids", "stages_json",
        "claims_extracted", "claims_updated", "notes", "git_commit", "created_at",
    }
    updated = {k: v for k, v in updated.items() if k in schema_fields}

    # Delete old record and add updated one (LanceDB pattern for updates)
    table = db.open_table("analysis_logs")
    table.delete(f"id = '{log_id}'")
    table.add([updated])


# =============================================================================
# CRUD Operations - Evidence Links
# =============================================================================

def _generate_evidence_link_id(db: lancedb.DBConnection) -> str:
    """Generate next evidence link ID."""
    year = date.today().year
    existing_tables = get_table_names(db)
    if "evidence_links" not in existing_tables:
        return f"EVLINK-{year}-001"

    table = db.open_table("evidence_links")
    rows = table.search().select(["id"]).limit(10000).to_list()
    existing_ids = [r["id"] for r in rows if r["id"].startswith(f"EVLINK-{year}-")]

    if not existing_ids:
        return f"EVLINK-{year}-001"

    max_num = 0
    for eid in existing_ids:
        try:
            num = int(eid.split("-")[-1])
            max_num = max(max_num, num)
        except ValueError:
            continue
    return f"EVLINK-{year}-{max_num + 1:03d}"


def add_evidence_link(
    link_data: dict,
    db: Optional[lancedb.DBConnection] = None,
) -> dict:
    """Add an evidence link.

    Args:
        link_data: Evidence link data with required fields:
            - claim_id: Claim this evidence supports/contradicts
            - source_id: Source providing the evidence
            - direction: supports|contradicts|strengthens|weakens
            - created_by: Tool/user that created this
        db: Database connection (optional, uses default if not provided)

    Returns:
        The created evidence link record.

    Raises:
        ValueError: If claim_id or source_id don't exist, or direction is invalid.
    """
    if db is None:
        db = get_db()

    claim_id = link_data.get("claim_id")
    source_id = link_data.get("source_id")
    direction = link_data.get("direction")

    # Validate claim exists
    if not claim_id or not get_claim(claim_id, db):
        raise ValueError(f"Claim '{claim_id}' not found")

    # Validate source exists
    if not source_id or not get_source(source_id, db):
        raise ValueError(f"Source '{source_id}' not found")

    # Validate direction
    if direction not in VALID_EVIDENCE_DIRECTIONS:
        raise ValueError(f"Invalid direction '{direction}'. Must be one of: {VALID_EVIDENCE_DIRECTIONS}")

    # Generate ID if not provided
    link_id = link_data.get("id") or _generate_evidence_link_id(db)

    # Set defaults
    now = date.today().isoformat()
    record = {
        "id": link_id,
        "claim_id": claim_id,
        "source_id": source_id,
        "direction": direction,
        "status": link_data.get("status", "active"),
        "supersedes_id": link_data.get("supersedes_id"),
        "strength": link_data.get("strength"),
        "location": link_data.get("location"),
        "quote": link_data.get("quote"),
        "reasoning": link_data.get("reasoning"),
        "analysis_log_id": link_data.get("analysis_log_id"),
        "created_at": link_data.get("created_at", now),
        "created_by": link_data.get("created_by", "unknown"),
    }

    # Ensure table exists
    init_tables(db)
    table = db.open_table("evidence_links")
    table.add([record])

    return record


def get_evidence_link(link_id: str, db: Optional[lancedb.DBConnection] = None) -> Optional[dict]:
    """Get an evidence link by ID."""
    if db is None:
        db = get_db()

    existing_tables = get_table_names(db)
    if "evidence_links" not in existing_tables:
        return None

    table = db.open_table("evidence_links")
    results = table.search().where(f"id = '{link_id}'").limit(1).to_list()
    return dict(results[0]) if results else None


def list_evidence_links(
    claim_id: Optional[str] = None,
    source_id: Optional[str] = None,
    direction: Optional[str] = None,
    include_superseded: bool = False,
    limit: int = 100,
    db: Optional[lancedb.DBConnection] = None,
) -> list[dict]:
    """List evidence links with optional filters.

    Args:
        claim_id: Filter by claim
        source_id: Filter by source
        direction: Filter by direction (supports/contradicts/etc.)
        include_superseded: Include superseded/retracted links
        limit: Maximum results to return
        db: Database connection (optional, uses default if not provided)

    Returns:
        List of evidence link records.
    """
    if db is None:
        db = get_db()

    existing_tables = get_table_names(db)
    if "evidence_links" not in existing_tables:
        return []

    table = db.open_table("evidence_links")
    query = table.search()

    # Build filter conditions
    conditions = []
    if claim_id:
        conditions.append(f"claim_id = '{claim_id}'")
    if source_id:
        conditions.append(f"source_id = '{source_id}'")
    if direction:
        conditions.append(f"direction = '{direction}'")
    if not include_superseded:
        conditions.append("status = 'active'")

    if conditions:
        query = query.where(" AND ".join(conditions))

    results = query.limit(limit).to_list()
    return [dict(r) for r in results]


def update_evidence_link(
    link_id: str,
    db: Optional[lancedb.DBConnection] = None,
    **fields: Any,
) -> None:
    """Update an evidence link.

    Args:
        link_id: ID of link to update
        db: Database connection (optional)
        **fields: Fields to update

    Raises:
        ValueError: If link_id not found.
    """
    if db is None:
        db = get_db()

    existing = get_evidence_link(link_id, db)
    if not existing:
        raise ValueError(f"Evidence link '{link_id}' not found")

    # Merge updates
    updated = dict(existing)
    for key, value in fields.items():
        if value is not None:
            updated[key] = value

    # Remove internal fields
    schema_fields = {f.name for f in EVIDENCE_LINKS_SCHEMA}
    updated = {k: v for k, v in updated.items() if k in schema_fields}

    # Delete and re-add (LanceDB pattern)
    table = db.open_table("evidence_links")
    table.delete(f"id = '{link_id}'")
    table.add([updated])


def supersede_evidence_link(
    old_link_id: str,
    db: Optional[lancedb.DBConnection] = None,
    **new_fields: Any,
) -> dict:
    """Create a new evidence link that supersedes an existing one.

    The old link is marked as superseded, and a new link is created
    with supersedes_id pointing to the old one.

    Args:
        old_link_id: ID of link to supersede
        db: Database connection (optional)
        **new_fields: Fields for the new link (inherits from old if not specified)

    Returns:
        The new evidence link record.

    Raises:
        ValueError: If old_link_id not found.
    """
    if db is None:
        db = get_db()

    old_link = get_evidence_link(old_link_id, db)
    if not old_link:
        raise ValueError(f"Evidence link '{old_link_id}' not found")

    # Mark old link as superseded
    update_evidence_link(old_link_id, db, status="superseded")

    # Create new link inheriting from old
    new_link_data = {
        "claim_id": old_link["claim_id"],
        "source_id": old_link["source_id"],
        "direction": new_fields.get("direction", old_link["direction"]),
        "status": "active",
        "supersedes_id": old_link_id,
        "strength": new_fields.get("strength", old_link.get("strength")),
        "location": new_fields.get("location", old_link.get("location")),
        "quote": new_fields.get("quote", old_link.get("quote")),
        "reasoning": new_fields.get("reasoning", old_link.get("reasoning")),
        "analysis_log_id": new_fields.get("analysis_log_id"),
        "created_by": new_fields.get("created_by", old_link.get("created_by", "unknown")),
    }

    return add_evidence_link(new_link_data, db)


# =============================================================================
# CRUD Operations - Reasoning Trails
# =============================================================================

def _generate_reasoning_trail_id(db: lancedb.DBConnection) -> str:
    """Generate next reasoning trail ID."""
    year = date.today().year
    existing_tables = get_table_names(db)
    if "reasoning_trails" not in existing_tables:
        return f"REASON-{year}-001"

    table = db.open_table("reasoning_trails")
    rows = table.search().select(["id"]).limit(10000).to_list()
    existing_ids = [r["id"] for r in rows if r["id"].startswith(f"REASON-{year}-")]

    if not existing_ids:
        return f"REASON-{year}-001"

    max_num = 0
    for rid in existing_ids:
        try:
            num = int(rid.split("-")[-1])
            max_num = max(max_num, num)
        except ValueError:
            continue
    return f"REASON-{year}-{max_num + 1:03d}"


def add_reasoning_trail(
    trail_data: dict,
    db: Optional[lancedb.DBConnection] = None,
) -> dict:
    """Add a reasoning trail.

    Args:
        trail_data: Reasoning trail data with required fields:
            - claim_id: Claim this reasoning is for
            - credence_at_time: Credence rating this reasoning produced
            - evidence_level_at_time: Evidence level assigned
            - reasoning_text: Publishable rationale
            - created_by: Tool/user that created this
        db: Database connection (optional, uses default if not provided)

    Returns:
        The created reasoning trail record.

    Raises:
        ValueError: If claim_id doesn't exist or evidence links are invalid.
    """
    if db is None:
        db = get_db()

    claim_id = trail_data.get("claim_id")

    # Validate claim exists
    if not claim_id or not get_claim(claim_id, db):
        raise ValueError(f"Claim '{claim_id}' not found")

    # Validate evidence link references if provided
    supporting = trail_data.get("supporting_evidence") or []
    contradicting = trail_data.get("contradicting_evidence") or []
    for evlink_id in supporting + contradicting:
        if not get_evidence_link(evlink_id, db):
            raise ValueError(f"Evidence link '{evlink_id}' not found")

    # Validate counterarguments_json if provided
    counterarguments_json = trail_data.get("counterarguments_json")
    if counterarguments_json:
        try:
            counterarguments = json.loads(counterarguments_json) if isinstance(counterarguments_json, str) else counterarguments_json
            if not isinstance(counterarguments, list):
                raise ValueError("counterarguments_json must be a JSON array")
            for i, ca in enumerate(counterarguments):
                if not isinstance(ca, dict):
                    raise ValueError(f"counterargument[{i}] must be an object")
                # Must have 'text' (canonical) or 'argument' (legacy)
                if not ca.get("text") and not ca.get("argument"):
                    raise ValueError(f"counterargument[{i}] missing required 'text' field")
                # Validate disposition if present
                disposition = ca.get("disposition")
                if disposition and disposition not in VALID_COUNTERARGUMENT_DISPOSITIONS:
                    raise ValueError(f"counterargument[{i}] invalid disposition '{disposition}' "
                        f"(must be one of: {', '.join(sorted(VALID_COUNTERARGUMENT_DISPOSITIONS))})")
        except json.JSONDecodeError as e:
            raise ValueError(f"counterarguments_json is not valid JSON: {e}")

    # Generate ID if not provided
    trail_id = trail_data.get("id") or _generate_reasoning_trail_id(db)

    # Set defaults
    now = date.today().isoformat()
    record = {
        "id": trail_id,
        "claim_id": claim_id,
        "status": trail_data.get("status", "active"),
        "supersedes_id": trail_data.get("supersedes_id"),
        "credence_at_time": float(trail_data.get("credence_at_time", 0.5)),
        "evidence_level_at_time": trail_data.get("evidence_level_at_time", "E4"),
        "evidence_summary": trail_data.get("evidence_summary"),
        "supporting_evidence": supporting or [],
        "contradicting_evidence": contradicting or [],
        "assumptions_made": trail_data.get("assumptions_made") or [],
        "counterarguments_json": trail_data.get("counterarguments_json"),
        "reasoning_text": trail_data.get("reasoning_text", ""),
        "analysis_pass": trail_data.get("analysis_pass"),
        "analysis_log_id": trail_data.get("analysis_log_id"),
        "created_at": trail_data.get("created_at", now),
        "created_by": trail_data.get("created_by", "unknown"),
    }

    # Ensure table exists
    init_tables(db)
    table = db.open_table("reasoning_trails")
    table.add([record])

    return record


def get_reasoning_trail(
    id: Optional[str] = None,
    claim_id: Optional[str] = None,
    db: Optional[lancedb.DBConnection] = None,
) -> Optional[dict]:
    """Get a reasoning trail by ID or claim_id (returns active trail for claim).

    Args:
        id: Trail ID (takes precedence)
        claim_id: Claim ID (returns current active trail)
        db: Database connection (optional, uses default if not provided)

    Returns:
        Reasoning trail record or None.
    """
    if db is None:
        db = get_db()

    existing_tables = get_table_names(db)
    if "reasoning_trails" not in existing_tables:
        return None

    table = db.open_table("reasoning_trails")

    if id:
        results = table.search().where(f"id = '{id}'").limit(1).to_list()
    elif claim_id:
        # Get all active trails and sort by created_at to get the latest
        results = table.search().where(f"claim_id = '{claim_id}' AND status = 'active'").limit(100).to_list()
        if results:
            # Sort by created_at descending to get the most recent
            results = sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)
            return dict(results[0])
        return None
    else:
        return None

    return dict(results[0]) if results else None


def list_reasoning_trails(
    claim_id: Optional[str] = None,
    include_superseded: bool = False,
    limit: int = 100,
    db: Optional[lancedb.DBConnection] = None,
) -> list[dict]:
    """List reasoning trails with optional filters.

    Args:
        claim_id: Filter by claim
        include_superseded: Include superseded trails
        limit: Maximum results to return
        db: Database connection (optional, uses default if not provided)

    Returns:
        List of reasoning trail records.
    """
    if db is None:
        db = get_db()

    existing_tables = get_table_names(db)
    if "reasoning_trails" not in existing_tables:
        return []

    table = db.open_table("reasoning_trails")
    query = table.search()

    conditions = []
    if claim_id:
        conditions.append(f"claim_id = '{claim_id}'")
    if not include_superseded:
        conditions.append("status = 'active'")

    if conditions:
        query = query.where(" AND ".join(conditions))

    results = query.limit(limit).to_list()
    # Sort by created_at descending (latest first) for deterministic ordering
    results = sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)
    return [dict(r) for r in results]


def get_reasoning_history(
    claim_id: str,
    db: Optional[lancedb.DBConnection] = None,
) -> list[dict]:
    """Get all reasoning trails for a claim, ordered by created_at.

    Returns the full credence evolution history including superseded trails.

    Args:
        claim_id: Claim ID
        db: Database connection (optional, uses default if not provided)

    Returns:
        List of reasoning trail records ordered by created_at (oldest first).
    """
    if db is None:
        db = get_db()

    existing_tables = get_table_names(db)
    if "reasoning_trails" not in existing_tables:
        return []

    table = db.open_table("reasoning_trails")
    results = table.search().where(f"claim_id = '{claim_id}'").limit(1000).to_list()

    # Sort by created_at (oldest first)
    sorted_results = sorted(results, key=lambda r: r.get("created_at", ""))
    return [dict(r) for r in sorted_results]


def supersede_reasoning_trail(
    old_trail_id: str,
    db: Optional[lancedb.DBConnection] = None,
    **new_fields: Any,
) -> dict:
    """Create a new reasoning trail that supersedes an existing one.

    Args:
        old_trail_id: ID of trail to supersede
        db: Database connection (optional)
        **new_fields: Fields for the new trail (inherits from old if not specified)

    Returns:
        The new reasoning trail record.

    Raises:
        ValueError: If old_trail_id not found.
    """
    if db is None:
        db = get_db()

    old_trail = get_reasoning_trail(id=old_trail_id, db=db)
    if not old_trail:
        raise ValueError(f"Reasoning trail '{old_trail_id}' not found")

    # Mark old trail as superseded
    existing_tables = get_table_names(db)
    if "reasoning_trails" in existing_tables:
        table = db.open_table("reasoning_trails")
        # Update old trail
        old_updated = dict(old_trail)
        old_updated["status"] = "superseded"
        schema_fields = {f.name for f in REASONING_TRAILS_SCHEMA}
        old_updated = {k: v for k, v in old_updated.items() if k in schema_fields}
        # Ensure list fields are lists
        for field in ["supporting_evidence", "contradicting_evidence", "assumptions_made"]:
            if old_updated.get(field) is None:
                old_updated[field] = []
            elif hasattr(old_updated[field], 'tolist'):
                old_updated[field] = old_updated[field].tolist()
        table.delete(f"id = '{old_trail_id}'")
        table.add([old_updated])

    # Create new trail inheriting from old
    new_trail_data = {
        "claim_id": old_trail["claim_id"],
        "status": "active",
        "supersedes_id": old_trail_id,
        "credence_at_time": new_fields.get("credence_at_time", old_trail.get("credence_at_time")),
        "evidence_level_at_time": new_fields.get("evidence_level_at_time", old_trail.get("evidence_level_at_time")),
        "evidence_summary": new_fields.get("evidence_summary", old_trail.get("evidence_summary")),
        "supporting_evidence": new_fields.get("supporting_evidence") or (list(old_trail.get("supporting_evidence") or []) if old_trail.get("supporting_evidence") is not None else []),
        "contradicting_evidence": new_fields.get("contradicting_evidence") or (list(old_trail.get("contradicting_evidence") or []) if old_trail.get("contradicting_evidence") is not None else []),
        "assumptions_made": new_fields.get("assumptions_made") or (list(old_trail.get("assumptions_made") or []) if old_trail.get("assumptions_made") is not None else []),
        "counterarguments_json": new_fields.get("counterarguments_json", old_trail.get("counterarguments_json")),
        "reasoning_text": new_fields.get("reasoning_text", old_trail.get("reasoning_text", "")),
        "analysis_pass": new_fields.get("analysis_pass"),
        "analysis_log_id": new_fields.get("analysis_log_id"),
        "created_by": new_fields.get("created_by", old_trail.get("created_by", "unknown")),
    }

    return add_reasoning_trail(new_trail_data, db)


# =============================================================================
# Statistics
# =============================================================================

def get_stats(db: Optional[lancedb.DBConnection] = None) -> dict:
    """Get statistics about the database."""
    if db is None:
        db = get_db()

    stats = {}
    existing_tables = get_table_names(db)
    for table_name in ["claims", "sources", "chains", "predictions", "contradictions", "definitions", "analysis_logs", "evidence_links", "reasoning_trails"]:
        if table_name in existing_tables:
            table = db.open_table(table_name)
            stats[table_name] = table.count_rows()
        else:
            stats[table_name] = 0

    return stats


# =============================================================================
# CLI Helpers
# =============================================================================

def _generate_claim_id(domain: str, db: Optional["lancedb.DBConnection"] = None) -> str:
    """Generate the next claim ID for a domain."""
    from datetime import date
    if db is None:
        db = get_db()

    year = date.today().year
    existing = list_claims(domain=domain, limit=10000, db=db)

    # Find highest counter for this domain/year
    max_counter = 0
    prefix = f"{domain}-{year}-"
    for claim in existing:
        if claim["id"].startswith(prefix):
            try:
                counter = int(claim["id"].split("-")[-1])
                max_counter = max(max_counter, counter)
            except ValueError:
                pass

    return f"{domain}-{year}-{max_counter + 1:03d}"


def _format_record_text(record: dict, record_type: str = "claim") -> str:
    """Format a record for human-readable text output."""
    lines = []
    if record_type == "claim":
        lines.append(f"[{record['id']}] {record['text'][:80]}{'...' if len(record.get('text', '')) > 80 else ''}")
        credence = record.get('credence')
        credence_str = f"{credence:.2f}" if credence is not None else "N/A"
        lines.append(f"  Type: {record['type']} | Domain: {record['domain']} | Evidence: {record['evidence_level']} | Credence: {credence_str}")
        if record.get("notes"):
            lines.append(f"  Notes: {record['notes']}")
    elif record_type == "source":
        authors = record.get("author", [])
        author_str = ", ".join(authors) if isinstance(authors, list) else str(authors)
        lines.append(f"[{record['id']}] {record['title']}")
        lines.append(f"  Type: {record['type']} | Author: {author_str} | Year: {record['year']}")
        if record.get("url"):
            lines.append(f"  URL: {record['url']}")
    elif record_type == "chain":
        lines.append(f"[{record['id']}] {record['name']}")
        lines.append(f"  Thesis: {record['thesis'][:80]}{'...' if len(record.get('thesis', '')) > 80 else ''}")
        credence = record.get('credence')
        credence_str = f"{credence:.2f}" if credence is not None else "N/A"
        lines.append(f"  Credence: {credence_str} | Claims: {len(record.get('claims', []))}")
    elif record_type == "prediction":
        lines.append(f"[{record['claim_id']}] Status: {record['status']}")
        lines.append(f"  Source: {record['source_id']} | Target: {record.get('target_date', 'N/A')}")
    elif record_type == "analysis_log":
        lines.append(f"[{record['id']}] Source: {record['source_id']} | Pass: {record.get('pass', 'N/A')}")
        lines.append(f"  Tool: {record['tool']} | Status: {record['status']}")
        if record.get('model'):
            lines.append(f"  Model: {record['model']}")
        tokens = record.get('total_tokens')
        cost = record.get('cost_usd')
        tokens_str = str(tokens) if tokens is not None else "?"
        cost_str = f"${cost:.4f}" if cost is not None else "?"
        lines.append(f"  Tokens: {tokens_str} | Cost: {cost_str}")
        if record.get("notes"):
            lines.append(f"  Notes: {record['notes']}")
    elif record_type == "evidence_link":
        lines.append(f"[{record['id']}] {record['direction']} {record['claim_id']}")
        lines.append(f"  Source: {record['source_id']} | Status: {record.get('status', 'active')}")
        if record.get('location'):
            lines.append(f"  Location: {record['location']}")
        strength = record.get('strength')
        if strength is not None:
            lines.append(f"  Strength: {strength:.2f}")
        if record.get('reasoning'):
            lines.append(f"  Reasoning: {record['reasoning'][:80]}{'...' if len(record.get('reasoning', '')) > 80 else ''}")
    elif record_type == "reasoning_trail":
        lines.append(f"[{record['id']}] Claim: {record['claim_id']}")
        credence = record.get('credence_at_time')
        credence_str = f"{credence:.2f}" if credence is not None else "N/A"
        lines.append(f"  Credence: {credence_str} | Evidence: {record.get('evidence_level_at_time', 'N/A')} | Status: {record.get('status', 'active')}")
        if record.get('evidence_summary'):
            lines.append(f"  Summary: {record['evidence_summary'][:80]}{'...' if len(record.get('evidence_summary', '')) > 80 else ''}")
        if record.get('reasoning_text'):
            lines.append(f"  Reasoning: {record['reasoning_text'][:80]}{'...' if len(record.get('reasoning_text', '')) > 80 else ''}")
    return "\n".join(lines)


def _output_result(data: Any, format_type: str = "json", record_type: str = "claim") -> None:
    """Output data in requested format."""
    import json
    import sys

    # Clean data for JSON serialization
    def clean_for_json(obj):
        if hasattr(obj, 'tolist'):  # numpy array
            return obj.tolist()
        elif hasattr(obj, 'to_pylist'):  # pyarrow array
            return obj.to_pylist()
        elif isinstance(obj, (list, tuple)):
            return [clean_for_json(v) for v in obj]
        elif isinstance(obj, dict):
            return {k: clean_for_json(v) for k, v in obj.items()}
        elif hasattr(obj, 'as_py'):  # pyarrow scalar
            return obj.as_py()
        return obj

    data = clean_for_json(data)

    if format_type == "json":
        print(json.dumps(data, indent=2, default=str))
    else:
        if isinstance(data, list):
            for item in data:
                print(_format_record_text(item, record_type))
                print()
        else:
            print(_format_record_text(data, record_type))

    # Flush stdout to ensure output is visible before lancedb GIL crash
    sys.stdout.flush()


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point."""
    import argparse
    import json
    import sys
    import yaml

    parser = argparse.ArgumentParser(
        description="Reality Check Database CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rc-db init                              Initialize database
  rc-db claim add --text "..." --type "[F]" --domain "TECH" --evidence-level "E3"
  rc-db claim get TECH-2026-001           Get claim by ID
  rc-db claim list --domain TECH          List claims filtered by domain
  rc-db search "AI automation"            Semantic search for claims
  rc-db import data.yaml --type claims    Import claims from YAML
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # -------------------------------------------------------------------------
    # Basic commands
    # -------------------------------------------------------------------------
    subparsers.add_parser("init", help="Initialize database tables")
    subparsers.add_parser("stats", help="Show database statistics")
    subparsers.add_parser("reset", help="Drop all tables and reinitialize")
    subparsers.add_parser("doctor", help="Detect project root and print DB setup guidance")

    repair_parser = subparsers.add_parser(
        "repair",
        help="Repair database invariants (safe, idempotent)",
    )
    repair_parser.add_argument(
        "--backlinks",
        action="store_true",
        help="Recompute sources.claims_extracted from claims.source_ids",
    )
    repair_parser.add_argument(
        "--predictions",
        action="store_true",
        help="Ensure stub prediction rows exist for [P] claims",
    )
    repair_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing",
    )

    # migrate command
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate database schema to latest version",
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )

    # init-project command
    init_project_parser = subparsers.add_parser(
        "init-project",
        help="Initialize a new Reality Check data project"
    )
    init_project_parser.add_argument(
        "--path", default=".",
        help="Path to create project (default: current directory)"
    )
    init_project_parser.add_argument(
        "--db-path", default="data/realitycheck.lance",
        help="Database path relative to project root"
    )
    init_project_parser.add_argument(
        "--no-git", action="store_true",
        help="Skip git initialization"
    )

    # search command
    search_parser = subparsers.add_parser("search", help="Search claims semantically")
    search_parser.add_argument("query", help="Search query text")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results")
    search_parser.add_argument("--domain", help="Filter by domain")
    search_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # -------------------------------------------------------------------------
    # Claim commands
    # -------------------------------------------------------------------------
    claim_parser = subparsers.add_parser("claim", help="Claim operations")
    claim_subparsers = claim_parser.add_subparsers(dest="claim_command")

    # claim add
    claim_add = claim_subparsers.add_parser("add", help="Add a new claim")
    claim_add.add_argument("--id", help="Claim ID (auto-generated if not provided)")
    claim_add.add_argument("--text", required=True, help="Claim text")
    claim_add.add_argument("--type", required=True, help="Claim type ([F]/[T]/[H]/[P]/[A]/[C]/[S]/[X])")
    claim_add.add_argument("--domain", required=True, help="Domain (TECH/LABOR/ECON/etc.)")
    claim_add.add_argument("--evidence-level", required=True, help="Evidence level (E1-E6)")
    claim_add.add_argument("--credence", type=float, default=0.5, help="Credence (0.0-1.0)")
    claim_add.add_argument("--source-ids", help="Comma-separated source IDs")
    claim_add.add_argument("--supports", help="Comma-separated claim IDs this supports")
    claim_add.add_argument("--contradicts", help="Comma-separated claim IDs this contradicts")
    claim_add.add_argument("--depends-on", help="Comma-separated claim IDs this depends on")
    claim_add.add_argument("--notes", help="Additional notes")
    claim_add.add_argument("--no-embedding", action="store_true", help="Skip embedding generation")

    # claim get
    claim_get = claim_subparsers.add_parser("get", help="Get a claim by ID")
    claim_get.add_argument("claim_id", help="Claim ID")
    claim_get.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # claim list
    claim_list = claim_subparsers.add_parser("list", help="List claims")
    claim_list.add_argument("--domain", help="Filter by domain")
    claim_list.add_argument("--type", help="Filter by type")
    claim_list.add_argument("--limit", type=int, default=100, help="Max results")
    claim_list.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # claim update
    claim_update = claim_subparsers.add_parser("update", help="Update a claim")
    claim_update.add_argument("claim_id", help="Claim ID to update")
    claim_update.add_argument("--credence", type=float, help="New credence value")
    claim_update.add_argument("--evidence-level", help="New evidence level")
    claim_update.add_argument("--notes", help="New notes")
    claim_update.add_argument("--text", help="New text (triggers re-embedding)")

    # claim delete
    claim_delete = claim_subparsers.add_parser("delete", help="Delete a claim by ID")
    claim_delete.add_argument("claim_id", help="Claim ID to delete")
    claim_delete.add_argument("--force", action="store_true", help="Skip confirmation")

    # -------------------------------------------------------------------------
    # Source commands
    # -------------------------------------------------------------------------
    source_parser = subparsers.add_parser("source", help="Source operations")
    source_subparsers = source_parser.add_subparsers(dest="source_command")

    # source add
    source_add = source_subparsers.add_parser("add", help="Add a new source")
    source_add.add_argument("--id", required=True, help="Source ID")
    source_add.add_argument("--title", required=True, help="Source title")
    source_add.add_argument("--type", required=True, help="Source type (PAPER/BOOK/REPORT/ARTICLE/BLOG/SOCIAL/CONVO/KNOWLEDGE)")
    source_add.add_argument("--author", required=True, help="Author(s) - comma-separated for multiple")
    source_add.add_argument("--year", required=True, type=int, help="Publication year")
    source_add.add_argument("--url", help="URL")
    source_add.add_argument("--doi", help="DOI")
    source_add.add_argument("--reliability", type=float, help="Reliability score (0.0-1.0)")
    source_add.add_argument("--bias-notes", help="Bias notes")
    source_add.add_argument("--status", default="cataloged", help="Status (cataloged/analyzed)")
    source_add.add_argument("--analysis-file", help="Path to analysis markdown file")
    source_add.add_argument("--topics", help="Comma-separated topic tags")
    source_add.add_argument("--domains", help="Comma-separated domain tags (TECH/LABOR/...)")
    source_add.add_argument("--claims-extracted", help="Comma-separated claim IDs extracted from this source")
    source_add.add_argument("--no-embedding", action="store_true", help="Skip embedding generation")

    # source update
    source_update = source_subparsers.add_parser("update", help="Update a source")
    source_update.add_argument("source_id", help="Source ID to update")
    source_update.add_argument("--title", help="Source title")
    source_update.add_argument("--type", help="Source type (PAPER/BOOK/REPORT/ARTICLE/BLOG/SOCIAL/CONVO/INTERVIEW/DATA/FICTION/KNOWLEDGE)")
    source_update.add_argument("--author", help="Author(s) - comma-separated for multiple")
    source_update.add_argument("--year", type=int, help="Publication year")
    source_update.add_argument("--url", help="URL")
    source_update.add_argument("--doi", help="DOI")
    source_update.add_argument("--reliability", type=float, help="Reliability score (0.0-1.0)")
    source_update.add_argument("--bias-notes", help="Bias notes")
    source_update.add_argument("--status", help="Status (cataloged/analyzed)")
    source_update.add_argument("--analysis-file", help="Path to analysis markdown file")
    source_update.add_argument("--topics", help="Comma-separated topic tags")
    source_update.add_argument("--domains", help="Comma-separated domain tags (TECH/LABOR/...)")
    source_update.add_argument("--claims-extracted", help="Comma-separated claim IDs extracted from this source")
    source_update.add_argument("--no-embedding", action="store_true", help="Skip embedding generation")

    # source get
    source_get = source_subparsers.add_parser("get", help="Get a source by ID")
    source_get.add_argument("source_id", help="Source ID")
    source_get.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # source list
    source_list = source_subparsers.add_parser("list", help="List sources")
    source_list.add_argument("--type", help="Filter by type")
    source_list.add_argument("--status", help="Filter by status")
    source_list.add_argument("--limit", type=int, default=100, help="Max results")
    source_list.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # -------------------------------------------------------------------------
    # Chain commands
    # -------------------------------------------------------------------------
    chain_parser = subparsers.add_parser("chain", help="Chain operations")
    chain_subparsers = chain_parser.add_subparsers(dest="chain_command")

    # chain add
    chain_add = chain_subparsers.add_parser("add", help="Add a new argument chain")
    chain_add.add_argument("--id", required=True, help="Chain ID")
    chain_add.add_argument("--name", required=True, help="Chain name")
    chain_add.add_argument("--thesis", required=True, help="Chain thesis")
    chain_add.add_argument("--claims", required=True, help="Comma-separated claim IDs")
    chain_add.add_argument("--credence", type=float, help="Chain credence (defaults to MIN of claims)")
    chain_add.add_argument("--scoring-method", default="MIN", help="Scoring method (MIN/RANGE/CUSTOM)")
    chain_add.add_argument("--no-embedding", action="store_true", help="Skip embedding generation")

    # chain get
    chain_get = chain_subparsers.add_parser("get", help="Get a chain by ID")
    chain_get.add_argument("chain_id", help="Chain ID")
    chain_get.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # chain list
    chain_list = chain_subparsers.add_parser("list", help="List chains")
    chain_list.add_argument("--limit", type=int, default=100, help="Max results")
    chain_list.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # -------------------------------------------------------------------------
    # Prediction commands
    # -------------------------------------------------------------------------
    prediction_parser = subparsers.add_parser("prediction", help="Prediction operations")
    prediction_subparsers = prediction_parser.add_subparsers(dest="prediction_command")

    # prediction add
    prediction_add = prediction_subparsers.add_parser("add", help="Add a prediction")
    prediction_add.add_argument("--claim-id", required=True, help="Associated claim ID")
    prediction_add.add_argument("--source-id", required=True, help="Source of prediction")
    prediction_add.add_argument("--status", required=True, help="Status ([P+]/[P~]/[P→]/[P?]/[P←]/[P!]/[P-]/[P∅])")
    prediction_add.add_argument("--date-made", help="Date prediction was made")
    prediction_add.add_argument("--target-date", help="Target date for prediction")
    prediction_add.add_argument("--falsification-criteria", help="Criteria for falsification")
    prediction_add.add_argument("--verification-criteria", help="Criteria for verification")

    # prediction list
    prediction_list = prediction_subparsers.add_parser("list", help="List predictions")
    prediction_list.add_argument("--status", help="Filter by status")
    prediction_list.add_argument("--limit", type=int, default=100, help="Max results")
    prediction_list.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # -------------------------------------------------------------------------
    # Analysis log commands
    # -------------------------------------------------------------------------
    analysis_parser = subparsers.add_parser("analysis", help="Analysis log operations")
    analysis_subparsers = analysis_parser.add_subparsers(dest="analysis_command")

    # analysis add
    analysis_add = analysis_subparsers.add_parser("add", help="Add an analysis log entry")
    analysis_add.add_argument("--source-id", required=True, help="Source ID that was analyzed")
    analysis_add.add_argument("--tool", required=True, help="Tool used (claude-code/codex/amp/manual/other)")
    analysis_add.add_argument("--status", default="completed", help="Status (started/completed/failed/canceled/draft)")
    analysis_add.add_argument("--pass", type=int, dest="pass_num", help="Pass number (auto-computed if omitted)")
    analysis_add.add_argument("--cmd", dest="analysis_cmd", help="Command used (check/analyze/extract/etc.)")
    analysis_add.add_argument("--model", help="Model used")
    analysis_add.add_argument("--analysis-file", help="Path to analysis markdown file")
    analysis_add.add_argument("--started-at", help="Start timestamp (ISO format)")
    analysis_add.add_argument("--completed-at", help="Completion timestamp (ISO format)")
    analysis_add.add_argument("--duration", type=int, help="Duration in seconds")
    analysis_add.add_argument("--tokens-in", type=int, help="Input tokens")
    analysis_add.add_argument("--tokens-out", type=int, help="Output tokens")
    analysis_add.add_argument("--total-tokens", type=int, help="Total tokens")
    analysis_add.add_argument("--cost-usd", type=float, help="Cost in USD")
    analysis_add.add_argument("--claims-extracted", help="Comma-separated list of extracted claim IDs")
    analysis_add.add_argument("--claims-updated", help="Comma-separated list of updated claim IDs")
    analysis_add.add_argument("--notes", help="Notes about this analysis pass")
    analysis_add.add_argument("--git-commit", help="Git commit SHA")
    analysis_add.add_argument(
        "--allow-missing-source",
        action="store_true",
        help="Allow adding an analysis log even if the source_id is missing from the sources table",
    )
    analysis_add.add_argument(
        "--usage-from",
        help="Parse token usage from a local session log: claude:/path/to.jsonl | codex:/path/to.jsonl | amp:/path/to.json",
    )
    analysis_add.add_argument(
        "--window-start",
        help="Usage window start timestamp (ISO-8601; optional, for per-message logs)",
    )
    analysis_add.add_argument(
        "--window-end",
        help="Usage window end timestamp (ISO-8601; optional, for per-message logs)",
    )
    analysis_add.add_argument(
        "--estimate-cost",
        action="store_true",
        help="Estimate cost_usd from tokens + model pricing (best-effort; prices change)",
    )
    analysis_add.add_argument(
        "--price-in-per-1m",
        type=float,
        help="Override input price (USD per 1M tokens) for --estimate-cost",
    )
    analysis_add.add_argument(
        "--price-out-per-1m",
        type=float,
        help="Override output price (USD per 1M tokens) for --estimate-cost",
    )
    analysis_add.add_argument(
        "--no-update-analysis-file",
        action="store_true",
        help="Do not update the in-document Analysis Log table in --analysis-file",
    )
    # Delta accounting fields
    analysis_add.add_argument("--tokens-baseline", type=int, help="Session token count at check start")
    analysis_add.add_argument("--tokens-final", type=int, help="Session token count at check end")
    analysis_add.add_argument("--tokens-check", type=int, help="Total tokens for this check (computed if baseline+final provided)")
    analysis_add.add_argument("--usage-provider", help="Provider for session parsing (claude/codex/amp)")
    analysis_add.add_argument("--usage-mode", help="Capture method (per_message_sum/windowed_sum/counter_delta/manual)")
    analysis_add.add_argument("--usage-session-id", help="Session UUID")

    # analysis get
    analysis_get = analysis_subparsers.add_parser("get", help="Get an analysis log by ID")
    analysis_get.add_argument("analysis_id", help="Analysis log ID")
    analysis_get.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # analysis list
    analysis_list = analysis_subparsers.add_parser("list", help="List analysis logs")
    analysis_list.add_argument("--source-id", help="Filter by source ID")
    analysis_list.add_argument("--tool", help="Filter by tool")
    analysis_list.add_argument("--status", help="Filter by status")
    analysis_list.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    analysis_list.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # analysis start (lifecycle command)
    analysis_start = analysis_subparsers.add_parser("start", help="Start an analysis (captures baseline tokens)")
    analysis_start.add_argument("--source-id", required=True, help="Source ID to analyze")
    analysis_start.add_argument("--tool", required=True, help="Tool (claude-code/codex/amp)")
    analysis_start.add_argument("--model", help="Model being used")
    analysis_start.add_argument("--usage-session-id", help="Explicit session UUID (auto-detected if omitted)")
    analysis_start.add_argument("--usage-session-path", help="Explicit session file path")
    analysis_start.add_argument("--cmd", dest="analysis_cmd", help="Command (check/analyze/extract/etc.)")
    analysis_start.add_argument("--notes", help="Notes about this analysis")

    # analysis mark (lifecycle command)
    analysis_mark = analysis_subparsers.add_parser("mark", help="Mark a stage checkpoint (captures delta)")
    analysis_mark.add_argument("--id", required=True, dest="analysis_id", help="Analysis ID to update")
    analysis_mark.add_argument("--stage", required=True, help="Stage name (e.g., check_stage1)")
    analysis_mark.add_argument("--notes", help="Notes for this stage")

    # analysis complete (lifecycle command)
    analysis_complete = analysis_subparsers.add_parser("complete", help="Complete an analysis (captures final tokens)")
    analysis_complete.add_argument("--id", required=True, dest="analysis_id", help="Analysis ID to complete")
    analysis_complete.add_argument("--status", default="completed", help="Final status (completed/failed)")
    analysis_complete.add_argument("--tokens-final", type=int, help="Final token count (auto-detected if session tracked)")
    analysis_complete.add_argument("--claims-extracted", help="Comma-separated list of extracted claim IDs")
    analysis_complete.add_argument("--claims-updated", help="Comma-separated list of updated claim IDs")
    analysis_complete.add_argument("--analysis-file", help="Path to analysis document")
    analysis_complete.add_argument("--inputs-source-ids", help="Comma-separated source IDs feeding a synthesis")
    analysis_complete.add_argument("--inputs-analysis-ids", help="Comma-separated analysis log IDs feeding a synthesis")
    analysis_complete.add_argument("--notes", help="Notes about completion")
    analysis_complete.add_argument("--estimate-cost", action="store_true", help="Estimate cost from tokens")

    # analysis sessions (nested subcommand)
    analysis_sessions = analysis_subparsers.add_parser("sessions", help="Session discovery helpers")
    sessions_subparsers = analysis_sessions.add_subparsers(dest="sessions_command")

    sessions_list = sessions_subparsers.add_parser("list", help="List available sessions")
    sessions_list.add_argument("--tool", required=True, help="Tool to list sessions for (claude-code/codex/amp)")
    sessions_list.add_argument("--limit", type=int, default=10, help="Max sessions to show")

    # analysis backfill-usage
    analysis_backfill = analysis_subparsers.add_parser("backfill-usage", help="Backfill token usage for historical entries")
    analysis_backfill.add_argument("--tool", help="Filter by tool (claude-code/codex/amp)")
    analysis_backfill.add_argument("--since", help="Only entries after this date (YYYY-MM-DD)")
    analysis_backfill.add_argument("--until", help="Only entries before this date (YYYY-MM-DD)")
    analysis_backfill.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    analysis_backfill.add_argument("--limit", type=int, default=100, help="Max entries to process")
    analysis_backfill.add_argument("--force", action="store_true", help="Overwrite existing token values")

    # -------------------------------------------------------------------------
    # Evidence links commands
    # -------------------------------------------------------------------------
    evidence_parser = subparsers.add_parser("evidence", help="Evidence link operations")
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command")

    # evidence add
    evidence_add = evidence_subparsers.add_parser("add", help="Add an evidence link")
    evidence_add.add_argument("--id", help="Evidence link ID (auto-generated if omitted)")
    evidence_add.add_argument("--claim-id", required=True, help="Claim this evidence supports/contradicts")
    evidence_add.add_argument("--source-id", required=True, help="Source providing the evidence")
    evidence_add.add_argument("--direction", required=True, choices=["supports", "contradicts", "strengthens", "weakens"],
                              help="How this evidence relates to the claim")
    evidence_add.add_argument("--strength", type=float, help="Impact strength (0.0-1.0)")
    evidence_add.add_argument("--location", help="Specific location in source (e.g., 'Table 3, p.15')")
    evidence_add.add_argument("--quote", help="Relevant excerpt from source")
    evidence_add.add_argument("--reasoning", help="Why this evidence matters for the claim")
    evidence_add.add_argument("--analysis-log-id", help="Link to analysis log entry")
    evidence_add.add_argument("--created-by", default="cli", help="Tool/user creating this link")

    # evidence get
    evidence_get = evidence_subparsers.add_parser("get", help="Get an evidence link by ID")
    evidence_get.add_argument("link_id", help="Evidence link ID")
    evidence_get.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # evidence list
    evidence_list = evidence_subparsers.add_parser("list", help="List evidence links")
    evidence_list.add_argument("--claim-id", help="Filter by claim ID")
    evidence_list.add_argument("--source-id", help="Filter by source ID")
    evidence_list.add_argument("--direction", help="Filter by direction")
    evidence_list.add_argument("--include-superseded", action="store_true", help="Include superseded/retracted links")
    evidence_list.add_argument("--limit", type=int, default=100, help="Max results")
    evidence_list.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # evidence supersede
    evidence_supersede = evidence_subparsers.add_parser("supersede", help="Supersede an evidence link with a new one")
    evidence_supersede.add_argument("link_id", help="ID of link to supersede")
    evidence_supersede.add_argument("--direction", help="New direction (optional)")
    evidence_supersede.add_argument("--strength", type=float, help="New strength (optional)")
    evidence_supersede.add_argument("--location", help="New location (optional)")
    evidence_supersede.add_argument("--quote", help="New quote (optional)")
    evidence_supersede.add_argument("--reasoning", help="New reasoning (required for supersede)")
    evidence_supersede.add_argument("--created-by", default="cli", help="Tool/user creating new link")

    # -------------------------------------------------------------------------
    # Reasoning trails commands
    # -------------------------------------------------------------------------
    reasoning_parser = subparsers.add_parser("reasoning", help="Reasoning trail operations")
    reasoning_subparsers = reasoning_parser.add_subparsers(dest="reasoning_command")

    # reasoning add
    reasoning_add = reasoning_subparsers.add_parser("add", help="Add a reasoning trail")
    reasoning_add.add_argument("--id", help="Reasoning trail ID (auto-generated if omitted)")
    reasoning_add.add_argument("--claim-id", required=True, help="Claim this reasoning is for")
    reasoning_add.add_argument("--credence", required=True, type=float, help="Credence rating (0.0-1.0)")
    reasoning_add.add_argument("--evidence-level", required=True, help="Evidence level (E1-E6)")
    reasoning_add.add_argument("--reasoning-text", required=True, help="Publishable rationale for the credence")
    reasoning_add.add_argument("--evidence-summary", help="Summary of evidence basis")
    reasoning_add.add_argument("--supporting-evidence", help="Comma-separated evidence link IDs that support")
    reasoning_add.add_argument("--contradicting-evidence", help="Comma-separated evidence link IDs that contradict")
    reasoning_add.add_argument("--assumptions", help="Comma-separated assumptions made")
    reasoning_add.add_argument("--counterarguments-json", help="JSON array of counterarguments considered")
    reasoning_add.add_argument("--analysis-pass", type=int, help="Analysis pass number")
    reasoning_add.add_argument("--analysis-log-id", help="Link to analysis log entry")
    reasoning_add.add_argument("--status", default="active", choices=["active", "superseded"], help="Trail status")
    reasoning_add.add_argument("--created-by", default="cli", help="Tool/user creating this trail")

    # reasoning get
    reasoning_get = reasoning_subparsers.add_parser("get", help="Get a reasoning trail")
    reasoning_get.add_argument("--id", help="Reasoning trail ID")
    reasoning_get.add_argument("--claim-id", help="Claim ID (returns current active trail)")
    reasoning_get.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # reasoning list
    reasoning_list = reasoning_subparsers.add_parser("list", help="List reasoning trails")
    reasoning_list.add_argument("--claim-id", help="Filter by claim ID")
    reasoning_list.add_argument("--include-superseded", action="store_true", help="Include superseded trails")
    reasoning_list.add_argument("--limit", type=int, default=100, help="Max results")
    reasoning_list.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # reasoning history
    reasoning_history = reasoning_subparsers.add_parser("history", help="Show credence evolution history for a claim")
    reasoning_history.add_argument("--claim-id", required=True, help="Claim ID")
    reasoning_history.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # -------------------------------------------------------------------------
    # Related command
    # -------------------------------------------------------------------------
    related_parser = subparsers.add_parser("related", help="Find claims related to a given claim")
    related_parser.add_argument("claim_id", help="Claim ID to find relationships for")
    related_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # -------------------------------------------------------------------------
    # Import command
    # -------------------------------------------------------------------------
    import_parser = subparsers.add_parser("import", help="Import data from YAML file")
    import_parser.add_argument("file", help="YAML file to import")
    import_parser.add_argument("--type", choices=["claims", "sources", "all"], default="all", help="Type of data to import")
    import_parser.add_argument(
        "--on-conflict",
        choices=["error", "skip", "update"],
        default="error",
        help="Behavior when an imported ID already exists (default: error)",
    )
    import_parser.add_argument("--no-embedding", action="store_true", help="Skip embedding generation")

    # -------------------------------------------------------------------------
    # Parse and execute
    # -------------------------------------------------------------------------
    args = parser.parse_args()

    def is_framework_repo() -> bool:
        """Check if we're in the realitycheck framework repo (not a data repo)."""
        # Check for telltale framework files
        framework_markers = [
            Path("scripts/db.py"),
            Path("CLAUDE.md"),
            Path("integrations/claude"),
            Path("methodology/workflows"),
        ]
        matches = sum(1 for m in framework_markers if m.exists())
        return matches >= 2  # At least 2 markers = likely framework repo

    def ensure_data_selected_for_command(command: Optional[str]) -> None:
        """
        Fail early with a friendly message when the database location is ambiguous.

        If REALITYCHECK_DATA is unset, we only proceed without error when:
        - The command is creating a new DB (`init`, `reset`) or creating a project (`init-project`), or
        - A default `./data/realitycheck.lance` exists in the current directory.

        Additionally, refuse to create a database inside the framework repo itself.
        """
        if not command:
            return

        if command == "doctor":
            return

        if os.getenv("REALITYCHECK_DATA"):
            return

        default_db = Path("data/realitycheck.lance")

        if command == "init-project":
            return

        # If we're inside a data project, auto-detect its DB and proceed.
        if _maybe_autodetect_db_path(command):
            return

        if command in {"init", "reset"}:
            # Check if we're in the framework repo - refuse to create data there
            if is_framework_repo():
                print(
                    "Error: You appear to be in the realitycheck framework repo.",
                    file=sys.stderr,
                )
                print(
                    "Creating a database here would mix framework code with data.",
                    file=sys.stderr,
                )
                print("\nTo create a separate data project:", file=sys.stderr)
                print("  rc-db init-project --path ~/realitycheck-data", file=sys.stderr)
                print("\nOr set REALITYCHECK_DATA explicitly:", file=sys.stderr)
                print('  export REALITYCHECK_DATA="/path/to/your/data/realitycheck.lance"', file=sys.stderr)
                sys.exit(2)

            print(
                "Note: REALITYCHECK_DATA is not set; using default database path "
                f"'{default_db}' relative to '{Path.cwd()}'.",
                file=sys.stderr,
            )
            print('Set it explicitly to avoid surprises, e.g.:', file=sys.stderr)
            print('  export REALITYCHECK_DATA="/path/to/realitycheck.lance"', file=sys.stderr)
            return

        if default_db.exists():
            return

        print(
            "Error: REALITYCHECK_DATA is not set and no default database was found at "
            f"'{default_db}'.",
            file=sys.stderr,
        )
        print('Set REALITYCHECK_DATA to your DB path, e.g.:', file=sys.stderr)
        print('  export REALITYCHECK_DATA="/path/to/realitycheck.lance"', file=sys.stderr)
        print("Or create a new project database with:", file=sys.stderr)
        print("  rc-db init-project --path /path/to/project", file=sys.stderr)
        sys.exit(2)

    ensure_data_selected_for_command(args.command)

    # Helper to determine if embeddings should be generated
    # Respects both --no-embedding flag and REALITYCHECK_EMBED_SKIP env var
    def should_generate_embedding(args_obj, attr_name="no_embedding"):
        if should_skip_embeddings():
            return False
        return not getattr(args_obj, attr_name, False)

    # Basic commands
    if args.command == "init":
        db = get_db()
        tables = init_tables(db)
        print(f"Initialized {len(tables)} tables at {DB_PATH}")
        for name in tables:
            print(f"  - {name}")
        sys.stdout.flush()

    elif args.command == "stats":
        stats = get_stats()
        print("Database Statistics:")
        for table, count in stats.items():
            print(f"  {table}: {count} rows")
        sys.stdout.flush()

    elif args.command == "reset":
        db = get_db()
        drop_tables(db)
        tables = init_tables(db)
        print(f"Reset complete. Initialized {len(tables)} tables.", flush=True)

    elif args.command == "init-project":
        import subprocess

        project_path = Path(args.path).resolve()
        db_path = args.db_path

        print(f"Initializing Reality Check project at: {project_path}")

        # Create directory structure
        directories = [
            "data",
            "analysis/sources",
            "analysis/syntheses",
            "analysis/reasoning",
            "analysis/evidence/by-claim",
            "analysis/evidence/by-source",
            "tracking/updates",
            "inbox/to-catalog",
            "inbox/to-analyze",
        ]

        for dir_name in directories:
            dir_path = project_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_name}/")

        # Create .realitycheck.yaml config
        config_path = project_path / ".realitycheck.yaml"
        if not config_path.exists():
            config_content = f'''# Reality Check Project Configuration
version: "1.0"
db_path: "{db_path}"

# Optional settings
# embedding_model: "all-MiniLM-L6-v2"
# default_domain: "TECH"
'''
            with open(config_path, "w") as f:
                f.write(config_content)
            print(f"  Created: .realitycheck.yaml")
        else:
            print(f"  Skipped: .realitycheck.yaml (already exists)")

        # Create .gitignore
        gitignore_path = project_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = '''# Reality Check
*.pyc
__pycache__/
.pytest_cache/
*.egg-info/

# Environment
.env
.venv/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
'''
            with open(gitignore_path, "w") as f:
                f.write(gitignore_content)
            print(f"  Created: .gitignore")

        # Create .gitattributes for LFS
        gitattributes_path = project_path / ".gitattributes"
        if not gitattributes_path.exists():
            gitattributes_content = '''# LanceDB files (large binary)
*.lance filter=lfs diff=lfs merge=lfs -text
data/**/*.lance filter=lfs diff=lfs merge=lfs -text
'''
            with open(gitattributes_path, "w") as f:
                f.write(gitattributes_content)
            print(f"  Created: .gitattributes (git-lfs for .lance files)")

        # Create README.md
        readme_path = project_path / "README.md"
        if not readme_path.exists():
            readme_content = '''# My Reality Check Knowledge Base

A unified knowledge base for rigorous claim analysis.

## Quick Start

```bash
# Set database path
export REALITYCHECK_DATA="data/realitycheck.lance"

# Add claims
rc-db claim add --text "Your claim" --type "[F]" --domain "TECH" --evidence-level "E3"

# Search
rc-db search "query"

# Validate
rc-validate
```

## Structure

- `data/` - LanceDB database
- `analysis/sources/` - Source analysis documents
- `analysis/syntheses/` - Cross-source syntheses
- `tracking/` - Prediction tracking and updates
- `inbox/` - Sources to process

## Research Questions

[Add your key research questions here]
'''
            with open(readme_path, "w") as f:
                f.write(readme_content)
            print(f"  Created: README.md")

        # Create tracking/predictions.md
        predictions_path = project_path / "tracking" / "predictions.md"
        if not predictions_path.exists():
            predictions_content = '''# Prediction Tracking

## Active Predictions

| Claim ID | Status | Target Date | Last Evaluated |
|----------|--------|-------------|----------------|

## Resolved Predictions

| Claim ID | Status | Resolution Date | Notes |
|----------|--------|-----------------|-------|
'''
            with open(predictions_path, "w") as f:
                f.write(predictions_content)
            print(f"  Created: tracking/predictions.md")

        # Initialize git if requested
        if not args.no_git:
            git_dir = project_path / ".git"
            if not git_dir.exists():
                try:
                    subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
                    print(f"  Initialized: git repository")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print(f"  Skipped: git init (git not available)")

        # Initialize database
        full_db_path = project_path / db_path
        os.environ["REALITYCHECK_DATA"] = str(full_db_path)
        db = get_db(full_db_path)
        tables = init_tables(db)
        print(f"  Initialized: database with {len(tables)} tables")

        print(f"\nProject ready! Next steps:")
        print(f"  cd {project_path}")
        print(f"  export REALITYCHECK_DATA=\"{db_path}\"")
        print(f"  rc-db claim add --text \"...\" --type \"[F]\" --domain \"TECH\" --evidence-level \"E3\"")
        sys.stdout.flush()

    elif args.command == "doctor":
        project_root = find_project_root(Path.cwd())
        if not project_root:
            print("No Reality Check project detected from the current directory.", file=sys.stderr)
            print("Create one with:", file=sys.stderr)
            print("  rc-db init-project --path /path/to/project", file=sys.stderr)
            sys.exit(1)

        db_path = resolve_db_path_from_project_root(project_root)
        try:
            rel_db_path = db_path.relative_to(project_root)
        except ValueError:
            rel_db_path = None

        print(f"Project root: {project_root}")
        print(f"Database: {db_path}")
        print("\nTo use this project:")
        print(f"  cd {project_root}")
        if rel_db_path is not None:
            print(f"  export REALITYCHECK_DATA=\"{rel_db_path.as_posix()}\"")
        else:
            print(f"  export REALITYCHECK_DATA=\"{db_path}\"")
        sys.stdout.flush()

    elif args.command == "repair":
        db = get_db()

        do_backlinks = bool(getattr(args, "backlinks", False))
        do_predictions = bool(getattr(args, "predictions", False))
        if not do_backlinks and not do_predictions:
            do_backlinks = True
            do_predictions = True

        dry_run = bool(getattr(args, "dry_run", False))

        updated_sources = 0
        created_prediction_stubs = 0

        claims_cache: Optional[list[dict]] = None

        if do_backlinks:
            claims_cache = list_claims(limit=100000, db=db)
            expected_by_source: dict[str, set[str]] = {}
            for claim in claims_cache:
                claim_id = claim.get("id")
                if not claim_id:
                    continue
                for source_id in claim.get("source_ids") or []:
                    if not source_id:
                        continue
                    expected_by_source.setdefault(str(source_id), set()).add(str(claim_id))

            sources = list_sources(limit=100000, db=db)
            sources_table = db.open_table("sources")
            for source in sources:
                source_id = source.get("id")
                if not source_id:
                    continue

                expected_claims = sorted(expected_by_source.get(str(source_id), set()))
                current_claims = sorted(list((_ensure_python_types(source).get("claims_extracted") or [])))

                if current_claims == expected_claims:
                    continue

                updated_sources += 1
                if not dry_run:
                    # LanceDB update can error when setting list fields to an empty list.
                    value: list[str] | None = expected_claims if expected_claims else None
                    sources_table.update(where=f"id = '{source_id}'", values={"claims_extracted": value})

        if do_predictions:
            if claims_cache is None:
                claims_cache = list_claims(limit=100000, db=db)

            for claim in claims_cache:
                claim_py = _ensure_python_types(claim)
                claim_id = claim_py.get("id")
                if not claim_id:
                    continue
                if claim_py.get("type") != "[P]":
                    continue

                if get_prediction(str(claim_id), db):
                    continue

                if dry_run:
                    created_prediction_stubs += 1
                    continue

                before = get_prediction(str(claim_id), db)
                _ensure_prediction_for_claim(claim_py, db)
                after = get_prediction(str(claim_id), db)
                if before is None and after is not None:
                    created_prediction_stubs += 1

        if dry_run:
            print("Repair dry-run:", flush=True)
            print(f"  Would update sources: {updated_sources}", flush=True)
            print(f"  Would create prediction stubs: {created_prediction_stubs}", flush=True)
        else:
            print("Repair complete:", flush=True)
            print(f"  Updated sources: {updated_sources}", flush=True)
            print(f"  Created prediction stubs: {created_prediction_stubs}", flush=True)

    elif args.command == "migrate":
        db = get_db()
        dry_run = bool(getattr(args, "dry_run", False))

        # Expected schemas for each table
        expected_schemas = {
            "claims": CLAIMS_SCHEMA,
            "sources": SOURCES_SCHEMA,
            "chains": CHAINS_SCHEMA,
            "predictions": PREDICTIONS_SCHEMA,
            "contradictions": CONTRADICTIONS_SCHEMA,
            "definitions": DEFINITIONS_SCHEMA,
            "analysis_logs": ANALYSIS_LOGS_SCHEMA,
            "evidence_links": EVIDENCE_LINKS_SCHEMA,
            "reasoning_trails": REASONING_TRAILS_SCHEMA,
        }

        total_added = 0
        table_changes: dict[str, list[str]] = {}

        tables_created = []
        for table_name, expected_schema in expected_schemas.items():
            try:
                table = db.open_table(table_name)
            except Exception:
                # Table doesn't exist - create it
                if dry_run:
                    tables_created.append(table_name)
                    continue
                else:
                    db.create_table(table_name, schema=expected_schema)
                    tables_created.append(table_name)
                    continue

            current_fields = {f.name: f for f in table.schema}
            expected_fields = {f.name: f for f in expected_schema}

            missing_fields = []
            for field_name, field in expected_fields.items():
                if field_name not in current_fields:
                    missing_fields.append(field)

            if not missing_fields:
                continue

            table_changes[table_name] = []

            for field in missing_fields:
                field_name = field.name
                field_type = field.type

                if dry_run:
                    table_changes[table_name].append(f"{field_name} ({field_type})")
                    total_added += 1
                    continue

                # Determine the default expression based on type
                if pa.types.is_list(field_type):
                    # List types need make_list()
                    try:
                        table.add_columns({field_name: "make_list()"})
                        table_changes[table_name].append(f"{field_name} ({field_type})")
                        total_added += 1
                    except Exception as e:
                        print(f"  Warning: Failed to add {table_name}.{field_name}: {e}", file=sys.stderr)
                elif pa.types.is_int32(field_type) or pa.types.is_int64(field_type):
                    # Integer types
                    try:
                        table.add_columns({field_name: "cast(null as int)"})
                        table_changes[table_name].append(f"{field_name} ({field_type})")
                        total_added += 1
                    except Exception as e:
                        print(f"  Warning: Failed to add {table_name}.{field_name}: {e}", file=sys.stderr)
                elif pa.types.is_float32(field_type) or pa.types.is_float64(field_type):
                    # Float types
                    try:
                        table.add_columns({field_name: "cast(null as float)"})
                        table_changes[table_name].append(f"{field_name} ({field_type})")
                        total_added += 1
                    except Exception as e:
                        print(f"  Warning: Failed to add {table_name}.{field_name}: {e}", file=sys.stderr)
                else:
                    # String and other types - use null
                    try:
                        table.add_columns({field_name: "null"})
                        table_changes[table_name].append(f"{field_name} ({field_type})")
                        total_added += 1
                    except Exception as e:
                        print(f"  Warning: Failed to add {table_name}.{field_name}: {e}", file=sys.stderr)

        if dry_run:
            print("Migration dry-run:", flush=True)
        else:
            print("Migration complete:", flush=True)

        if total_added == 0 and not tables_created:
            print("  Schema is up to date - no changes needed.", flush=True)
        else:
            if tables_created:
                print(f"  Created {len(tables_created)} new table(s):", flush=True)
                for table_name in tables_created:
                    print(f"    {table_name}", flush=True)
            if total_added > 0:
                print(f"  Added {total_added} column(s):", flush=True)
                for table_name, fields in table_changes.items():
                    for field_desc in fields:
                        print(f"    {table_name}.{field_desc}", flush=True)

    elif args.command == "search":
        results = search_claims(args.query, limit=args.limit, domain=args.domain)
        if args.format == "json":
            _output_result(results, "json", "claim")
        else:
            for i, result in enumerate(results, 1):
                print(f"{i}. [{result['id']}] {result['text'][:80]}...")
                credence = result.get('credence')
                credence_str = f"{credence:.2f}" if credence is not None else "N/A"
                print(f"   Type: {result['type']} | Domain: {result['domain']} | Credence: {credence_str}")
                print()
            sys.stdout.flush()

    # Claim commands
    elif args.command == "claim":
        db = get_db()

        if args.claim_command == "add":
            claim_id = args.id or _generate_claim_id(args.domain, db)
            claim = {
                "id": claim_id,
                "text": args.text,
                "type": args.type,
                "domain": args.domain,
                "evidence_level": args.evidence_level,
                "credence": args.credence,
                "source_ids": args.source_ids.split(",") if args.source_ids else [],
                "supports": args.supports.split(",") if args.supports else [],
                "contradicts": args.contradicts.split(",") if args.contradicts else [],
                "depends_on": args.depends_on.split(",") if args.depends_on else [],
                "modified_by": [],
                "first_extracted": str(date.today()),
                "extracted_by": "cli",
                "version": 1,
                "last_updated": str(date.today()),
                "notes": args.notes,
            }
            try:
                result_id = add_claim(claim, db, generate_embedding=should_generate_embedding(args))
                print(f"Created claim: {result_id}", flush=True)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        elif args.claim_command == "get":
            result = get_claim(args.claim_id, db)
            if result:
                _output_result(result, args.format, "claim")
            else:
                print(f"Claim not found: {args.claim_id}", file=sys.stderr)
                sys.exit(1)

        elif args.claim_command == "list":
            results = list_claims(domain=args.domain, claim_type=args.type, limit=args.limit, db=db)
            _output_result(results, args.format, "claim")

        elif args.claim_command == "update":
            updates = {}
            if args.credence is not None:
                updates["credence"] = args.credence
            if args.evidence_level:
                updates["evidence_level"] = args.evidence_level
            if args.notes:
                updates["notes"] = args.notes
            if args.text:
                updates["text"] = args.text

            if not updates:
                print("No updates provided", file=sys.stderr)
                sys.exit(1)

            success = update_claim(args.claim_id, updates, db)
            if success:
                print(f"Updated claim: {args.claim_id}", flush=True)
            else:
                print(f"Claim not found: {args.claim_id}", file=sys.stderr)
                sys.exit(1)

        elif args.claim_command == "delete":
            # Check if claim exists first
            existing = get_claim(args.claim_id, db)
            if not existing:
                print(f"Claim not found: {args.claim_id}", file=sys.stderr)
                sys.exit(1)

            if not args.force:
                print(f"About to delete claim: {args.claim_id}")
                print(f"  Text: {existing.get('text', '')[:80]}...")
                confirm = input("Type 'yes' to confirm: ")
                if confirm.lower() != 'yes':
                    print("Cancelled")
                    sys.exit(0)

            delete_claim(args.claim_id, db)
            print(f"Deleted claim: {args.claim_id}", flush=True)

        else:
            claim_parser.print_help()

    # Source commands
    elif args.command == "source":
        db = get_db()

        if args.source_command == "add":
            def _parse_csv(value: Optional[str]) -> list[str]:
                if value is None:
                    return []
                return [v.strip() for v in value.split(",") if v.strip()]

            source = {
                "id": args.id,
                "title": args.title,
                "type": args.type,
                "author": [a.strip() for a in args.author.split(",")],
                "year": args.year,
                "url": args.url,
                "doi": args.doi,
                "accessed": str(date.today()),
                "reliability": args.reliability,
                "bias_notes": args.bias_notes,
                "claims_extracted": _parse_csv(getattr(args, "claims_extracted", None)),
                "analysis_file": getattr(args, "analysis_file", None),
                "topics": _parse_csv(getattr(args, "topics", None)),
                "domains": _parse_csv(getattr(args, "domains", None)),
                "status": args.status,
            }
            result_id = add_source(source, db, generate_embedding=should_generate_embedding(args))
            print(f"Created source: {result_id}", flush=True)

        elif args.source_command == "update":
            def _parse_optional_csv(value: Optional[str]) -> Optional[list[str]]:
                if value is None:
                    return None
                return [v.strip() for v in value.split(",") if v.strip()]

            updates: dict[str, Any] = {}
            if args.title is not None:
                updates["title"] = args.title
            if args.type is not None:
                updates["type"] = args.type
            if args.author is not None:
                updates["author"] = [a.strip() for a in args.author.split(",") if a.strip()]
            if args.year is not None:
                updates["year"] = args.year
            if args.url is not None:
                updates["url"] = args.url
            if args.doi is not None:
                updates["doi"] = args.doi
            if args.reliability is not None:
                updates["reliability"] = args.reliability
            if args.bias_notes is not None:
                updates["bias_notes"] = args.bias_notes
            if args.status is not None:
                updates["status"] = args.status
            if getattr(args, "analysis_file", None) is not None:
                updates["analysis_file"] = args.analysis_file
            if getattr(args, "topics", None) is not None:
                updates["topics"] = _parse_optional_csv(args.topics)
            if getattr(args, "domains", None) is not None:
                updates["domains"] = _parse_optional_csv(args.domains)
            if getattr(args, "claims_extracted", None) is not None:
                updates["claims_extracted"] = _parse_optional_csv(args.claims_extracted)

            if not updates:
                print("No updates provided.", file=sys.stderr)
                sys.exit(2)

            ok = update_source(args.source_id, updates, db=db, generate_embedding=should_generate_embedding(args))
            if not ok:
                print(f"Source not found: {args.source_id}", file=sys.stderr)
                sys.exit(1)
            print(f"Updated source: {args.source_id}", flush=True)

        elif args.source_command == "get":
            result = get_source(args.source_id, db)
            if result:
                _output_result(result, args.format, "source")
            else:
                print(f"Source not found: {args.source_id}", file=sys.stderr)
                sys.exit(1)

        elif args.source_command == "list":
            results = list_sources(source_type=args.type, status=args.status, limit=args.limit, db=db)
            _output_result(results, args.format, "source")

        else:
            source_parser.print_help()

    # Chain commands
    elif args.command == "chain":
        db = get_db()

        if args.chain_command == "add":
            claims_list = [c.strip() for c in args.claims.split(",")]

            # Compute credence: use provided value or MIN of claims
            if args.credence is not None:
                chain_credence = args.credence
            else:
                # Look up each claim and compute min credence
                claim_credences = []
                for claim_id in claims_list:
                    claim = get_claim(claim_id, db)
                    if claim and claim.get("credence") is not None:
                        claim_credences.append(claim["credence"])
                chain_credence = min(claim_credences) if claim_credences else 0.5

            chain = {
                "id": args.id,
                "name": args.name,
                "thesis": args.thesis,
                "claims": claims_list,
                "credence": chain_credence,
                "analysis_file": None,
                "weakest_link": None,
                "scoring_method": args.scoring_method,
            }
            result_id = add_chain(chain, db, generate_embedding=should_generate_embedding(args))
            print(f"Created chain: {result_id}", flush=True)

        elif args.chain_command == "get":
            result = get_chain(args.chain_id, db)
            if result:
                _output_result(result, args.format, "chain")
            else:
                print(f"Chain not found: {args.chain_id}", file=sys.stderr)
                sys.exit(1)

        elif args.chain_command == "list":
            results = list_chains(limit=args.limit, db=db)
            _output_result(results, args.format, "chain")

        else:
            chain_parser.print_help()

    # Prediction commands
    elif args.command == "prediction":
        db = get_db()

        if args.prediction_command == "add":
            prediction = {
                "claim_id": args.claim_id,
                "source_id": args.source_id,
                "status": args.status,
                "date_made": args.date_made or str(date.today()),
                "target_date": args.target_date,
                "falsification_criteria": args.falsification_criteria,
                "verification_criteria": args.verification_criteria,
                "last_evaluated": str(date.today()),
                "evidence_updates": None,
            }
            result_id = add_prediction(prediction, db)
            print(f"Created prediction for: {result_id}", flush=True)

        elif args.prediction_command == "list":
            results = list_predictions(status=args.status, limit=args.limit, db=db)
            _output_result(results, args.format, "prediction")

        else:
            prediction_parser.print_help()

    # Analysis log commands
    elif args.command == "analysis":
        db = get_db()

        if args.analysis_command == "add":
            usage_totals = None
            if getattr(args, "usage_from", None):
                try:
                    provider, usage_path_str = args.usage_from.split(":", 1)
                except ValueError:
                    print(
                        "Error: --usage-from must be formatted like 'codex:/path/to/rollout.jsonl'",
                        file=sys.stderr,
                    )
                    sys.exit(2)

                usage_path = Path(usage_path_str).expanduser()
                try:
                    usage_totals = parse_usage_from_source(
                        provider,
                        usage_path,
                        window_start=getattr(args, "window_start", None),
                        window_end=getattr(args, "window_end", None),
                    )
                except Exception as e:
                    print(f"Error parsing usage from {args.usage_from}: {e}", file=sys.stderr)
                    sys.exit(2)

            log = {
                "source_id": args.source_id,
                "tool": args.tool,
                "status": args.status,
                "command": getattr(args, "analysis_cmd", None),
                "model": args.model,
                "analysis_file": getattr(args, "analysis_file", None),
                "started_at": getattr(args, "started_at", None),
                "completed_at": getattr(args, "completed_at", None),
                "duration_seconds": args.duration,
                "tokens_in": getattr(args, "tokens_in", None),
                "tokens_out": getattr(args, "tokens_out", None),
                "total_tokens": getattr(args, "total_tokens", None),
                "cost_usd": getattr(args, "cost_usd", None),
                # Delta accounting fields
                "tokens_baseline": getattr(args, "tokens_baseline", None),
                "tokens_final": getattr(args, "tokens_final", None),
                "tokens_check": getattr(args, "tokens_check", None),
                "usage_provider": getattr(args, "usage_provider", None),
                "usage_mode": getattr(args, "usage_mode", None),
                "usage_session_id": getattr(args, "usage_session_id", None),
                "notes": args.notes,
                "git_commit": getattr(args, "git_commit", None),
                "framework_version": None,
                "methodology_version": None,
                "stages_json": None,
            }

            # Compute tokens_check if baseline and final provided
            if (
                log.get("tokens_check") is None
                and isinstance(log.get("tokens_baseline"), int)
                and isinstance(log.get("tokens_final"), int)
            ):
                log["tokens_check"] = log["tokens_final"] - log["tokens_baseline"]

            if usage_totals is not None:
                if log.get("tokens_in") is None and usage_totals.tokens_in is not None:
                    log["tokens_in"] = usage_totals.tokens_in
                if log.get("tokens_out") is None and usage_totals.tokens_out is not None:
                    log["tokens_out"] = usage_totals.tokens_out
                if log.get("total_tokens") is None and usage_totals.total_tokens is not None:
                    log["total_tokens"] = usage_totals.total_tokens
                if log.get("cost_usd") is None and usage_totals.cost_usd is not None:
                    log["cost_usd"] = usage_totals.cost_usd

            # Backfill total_tokens when input/output are known.
            if log.get("total_tokens") is None and isinstance(log.get("tokens_in"), int) and isinstance(log.get("tokens_out"), int):
                log["total_tokens"] = int(log["tokens_in"]) + int(log["tokens_out"])

            # Optional cost estimation from known model pricing.
            if (
                log.get("cost_usd") is None
                and getattr(args, "estimate_cost", False)
                and isinstance(log.get("tokens_in"), int)
                and isinstance(log.get("tokens_out"), int)
                and (log.get("model") or "").strip()
            ):
                try:
                    estimated = estimate_cost_usd(
                        str(log["model"]),
                        int(log["tokens_in"]),
                        int(log["tokens_out"]),
                        price_in_per_1m=getattr(args, "price_in_per_1m", None),
                        price_out_per_1m=getattr(args, "price_out_per_1m", None),
                    )
                except Exception as e:
                    print(f"Error estimating cost: {e}", file=sys.stderr)
                    sys.exit(2)
                if estimated is not None:
                    log["cost_usd"] = estimated

            # Handle pass number
            if args.pass_num is not None:
                log["pass"] = args.pass_num

            # Handle comma-separated claim lists
            if args.claims_extracted:
                log["claims_extracted"] = [c.strip() for c in args.claims_extracted.split(",")]
            if args.claims_updated:
                log["claims_updated"] = [c.strip() for c in args.claims_updated.split(",")]

            if not get_source(str(log["source_id"]), db) and not getattr(args, "allow_missing_source", False):
                print(
                    f"Error: source not found: {log['source_id']}. Add it first with `rc-db source add`, "
                    "or pass --allow-missing-source.",
                    file=sys.stderr,
                )
                sys.exit(1)

            result_id = add_analysis_log(log, db, auto_pass=(args.pass_num is None))
            print(f"Created analysis log: {result_id}", flush=True)

            # Update the analysis markdown file's in-document Analysis Log (best-effort).
            analysis_file = log.get("analysis_file")
            if analysis_file and not getattr(args, "no_update_analysis_file", False):
                analysis_path = Path(str(analysis_file)).expanduser()
                if not analysis_path.is_absolute():
                    # Resolve relative paths from the data project root (derived from REALITYCHECK_DATA).
                    analysis_path = (_project_root_from_db_path(DB_PATH) / analysis_path).resolve()

                if analysis_path.exists():
                    try:
                        before = analysis_path.read_text(encoding="utf-8")
                        after = upsert_analysis_log_section(before, log)
                        if after != before:
                            analysis_path.write_text(after, encoding="utf-8")
                            print(f"Updated analysis file: {analysis_path}", file=sys.stderr, flush=True)
                    except Exception as e:
                        print(f"Warning: could not update analysis file {analysis_path}: {e}", file=sys.stderr)
                else:
                    print(
                        f"Warning: analysis file not found; skipping in-document log update: {analysis_path}",
                        file=sys.stderr,
                    )

        elif args.analysis_command == "get":
            result = get_analysis_log(args.analysis_id, db)
            if result:
                _output_result(result, args.format, "analysis_log")
            else:
                print(f"Analysis log not found: {args.analysis_id}", file=sys.stderr)
                sys.exit(1)

        elif args.analysis_command == "list":
            results = list_analysis_logs(
                source_id=getattr(args, "source_id", None),
                tool=args.tool,
                status=args.status,
                limit=args.limit,
                db=db,
            )
            _output_result(results, args.format, "analysis_log")

        elif args.analysis_command == "start":
            # Lifecycle: start an analysis with baseline snapshot
            from datetime import datetime as dt

            tool = args.tool
            provider = _tool_to_provider(tool)

            session_id = getattr(args, "usage_session_id", None)
            session_path = getattr(args, "usage_session_path", None)
            tokens_baseline = None

            if session_path:
                session_path = Path(session_path).expanduser()
                tokens_baseline = get_session_token_count(session_path, provider)
                if not session_id:
                    # Extract UUID from path
                    session_id = _extract_uuid_from_filename(session_path.name, provider)
            elif session_id:
                # Have ID but not path - try to find path and get tokens
                try:
                    tokens_baseline = get_session_token_count_by_uuid(session_id, provider)
                except Exception:
                    pass  # OK if we can't get baseline, can still track session ID
            else:
                # Auto-detect session
                try:
                    session_path_detected, session_id = get_current_session_path(provider)
                    tokens_baseline = get_session_token_count(session_path_detected, provider)
                except NoSessionFoundError:
                    pass  # No session found - continue without token tracking
                except AmbiguousSessionError as e:
                    print(f"Warning: {e}", file=sys.stderr)
                    print("Use --usage-session-id to specify which session to track.", file=sys.stderr)
                except Exception:
                    pass  # Other errors - continue without token tracking

            log = {
                "source_id": args.source_id,
                "tool": tool,
                "status": "started",
                "command": getattr(args, "analysis_cmd", None),
                "model": getattr(args, "model", None),
                "started_at": dt.utcnow().isoformat() + "Z",
                "tokens_baseline": tokens_baseline,
                "usage_provider": provider,
                "usage_mode": "per_message_sum" if provider in ("claude", "amp") else "counter_delta",
                "usage_session_id": session_id,
                "notes": getattr(args, "notes", None),
            }

            log_id = add_analysis_log(log, db)
            print(f"Created analysis log: {log_id}", flush=True)
            if tokens_baseline is not None:
                print(f"  baseline tokens: {tokens_baseline}", flush=True)
            if session_id:
                print(f"  session: {session_id}", flush=True)

        elif args.analysis_command == "mark":
            # Lifecycle: mark a stage checkpoint with token delta
            import json as json_module
            from datetime import datetime as dt

            log_id = args.analysis_id
            stage_name = args.stage

            existing = get_analysis_log(log_id, db)
            if not existing:
                print(f"Error: Analysis log not found: {log_id}", file=sys.stderr)
                sys.exit(1)

            # Parse existing stages
            stages_json = existing.get("stages_json") or "[]"
            try:
                stages = json_module.loads(stages_json)
            except json_module.JSONDecodeError:
                stages = []

            # Try to capture current token count
            tokens_now = None
            session_id = existing.get("usage_session_id")
            provider = existing.get("usage_provider")
            if session_id and provider:
                try:
                    tokens_now = get_session_token_count_by_uuid(session_id, provider)
                except Exception:
                    pass

            # Compute delta from baseline or previous stage
            tokens_delta = None
            if tokens_now is not None:
                # Get previous reference point (last stage tokens_cumulative, or baseline)
                if stages and "tokens_cumulative" in stages[-1]:
                    prev_tokens = stages[-1]["tokens_cumulative"]
                else:
                    prev_tokens = existing.get("tokens_baseline")
                if prev_tokens is not None:
                    tokens_delta = tokens_now - prev_tokens

            # Add new stage
            stage_entry = {
                "stage": stage_name,
                "timestamp": dt.utcnow().isoformat() + "Z",
            }
            if tokens_now is not None:
                stage_entry["tokens_cumulative"] = tokens_now
            if tokens_delta is not None:
                stage_entry["tokens_delta"] = tokens_delta
            if getattr(args, "notes", None):
                stage_entry["notes"] = args.notes

            stages.append(stage_entry)

            update_analysis_log(log_id, stages_json=json_module.dumps(stages), db=db)
            print(f"Marked stage '{stage_name}' for {log_id}", flush=True)
            if tokens_delta is not None:
                print(f"  tokens_delta: {tokens_delta}", flush=True)

        elif args.analysis_command == "complete":
            # Lifecycle: complete an analysis with final snapshot
            import json as json_module
            from datetime import datetime as dt

            log_id = args.analysis_id

            existing = get_analysis_log(log_id, db)
            if not existing:
                print(f"Error: Analysis log not found: {log_id}", file=sys.stderr)
                sys.exit(1)

            tokens_final = getattr(args, "tokens_final", None)
            session_id = existing.get("usage_session_id")
            provider = existing.get("usage_provider")

            # Try to auto-detect final tokens if session is tracked
            if tokens_final is None and session_id and provider:
                try:
                    tokens_final = get_session_token_count_by_uuid(session_id, provider)
                except Exception:
                    pass

            # Compute tokens_check
            tokens_baseline = existing.get("tokens_baseline")
            tokens_check = None
            if isinstance(tokens_baseline, int) and isinstance(tokens_final, int):
                tokens_check = tokens_final - tokens_baseline

            updates = {
                "status": args.status,
                "completed_at": dt.utcnow().isoformat() + "Z",
            }
            if tokens_final is not None:
                updates["tokens_final"] = tokens_final
            if tokens_check is not None:
                updates["tokens_check"] = tokens_check

            # Handle claims
            if getattr(args, "claims_extracted", None):
                updates["claims_extracted"] = [c.strip() for c in args.claims_extracted.split(",")]
            if getattr(args, "claims_updated", None):
                updates["claims_updated"] = [c.strip() for c in args.claims_updated.split(",")]
            if getattr(args, "analysis_file", None):
                updates["analysis_file"] = args.analysis_file
            if getattr(args, "inputs_source_ids", None):
                updates["inputs_source_ids"] = [s.strip() for s in args.inputs_source_ids.split(",")]
            if getattr(args, "inputs_analysis_ids", None):
                updates["inputs_analysis_ids"] = [a.strip() for a in args.inputs_analysis_ids.split(",")]
            if getattr(args, "notes", None):
                updates["notes"] = args.notes

            # Estimate cost if requested
            if getattr(args, "estimate_cost", False) and tokens_check:
                model = existing.get("model")
                if model:
                    estimated = estimate_cost_usd(model, tokens_check // 2, tokens_check // 2)
                    if estimated:
                        updates["cost_usd"] = estimated

            update_analysis_log(log_id, db=db, **updates)
            print(f"Completed analysis: {log_id}", flush=True)
            if tokens_check is not None:
                print(f"  tokens_check: {tokens_check}", flush=True)

        elif args.analysis_command == "sessions":
            # Session discovery helpers
            if getattr(args, "sessions_command", None) == "list":
                tool = args.tool
                provider = _tool_to_provider(tool)
                limit = getattr(args, "limit", 10)

                sessions = list_sessions(provider, limit=limit)
                if not sessions:
                    print(f"No sessions found for {tool}", file=sys.stderr)
                    sys.exit(1)

                print(f"Sessions for {tool}:", flush=True)
                for s in sessions:
                    snippet = s.get("context_snippet", "")[:50]
                    if len(s.get("context_snippet", "")) > 50:
                        snippet += "..."
                    print(f"  {s['uuid']}: {s['tokens_so_far']:,} tokens - {snippet or '(no preview)'}", flush=True)
            else:
                print("Usage: rc-db analysis sessions list --tool <claude-code|codex|amp>", file=sys.stderr)
                sys.exit(1)

        elif args.analysis_command == "backfill-usage":
            # Backfill token usage for historical entries
            from datetime import datetime as dt

            dry_run = getattr(args, "dry_run", False)
            force = getattr(args, "force", False)
            limit = getattr(args, "limit", 100)
            tool_filter = getattr(args, "tool", None)
            since = getattr(args, "since", None)
            until = getattr(args, "until", None)

            # Get all analysis logs missing tokens_check
            all_logs = list_analysis_logs(tool=tool_filter, limit=10000, db=db)

            # Filter to entries that need backfill
            candidates = []
            for log in all_logs:
                # Skip if already has tokens_check (unless force)
                if log.get("tokens_check") is not None and not force:
                    continue

                # Must have timestamps for window matching
                started_at = log.get("started_at")
                completed_at = log.get("completed_at")
                if not started_at or not completed_at:
                    continue

                # Apply date filters
                if since:
                    if started_at < since:
                        continue
                if until:
                    if started_at > until:
                        continue

                candidates.append(log)

            if not candidates:
                print("No entries found that need backfill.", flush=True)
                sys.exit(0)

            print(f"Found {len(candidates)} entries to backfill (limit: {limit})", flush=True)
            candidates = candidates[:limit]

            # Warn about Codex limitation
            codex_count = sum(1 for c in candidates if _tool_to_provider(c.get("tool", "")) == "codex")
            if codex_count > 0:
                print(
                    f"\nNote: {codex_count} Codex entries will use cumulative counter snapshot (may overcount).",
                    flush=True,
                )
                print(
                    "Codex logs store running totals; window filtering returns final counter, not delta.",
                    flush=True,
                )
                print("Consider manual review for accuracy.\n", flush=True)

            updated = 0
            skipped = 0

            for log in candidates:
                log_id = log["id"]
                tool = log.get("tool", "")
                provider = _tool_to_provider(tool)
                started_at = log.get("started_at")
                completed_at = log.get("completed_at")

                # Find session files that overlap with this time window
                session_paths = _get_session_paths(provider)
                if not session_paths:
                    print(f"  {log_id}: no sessions found for {tool}", flush=True)
                    skipped += 1
                    continue

                # Try to compute windowed usage
                best_tokens = None
                for path in session_paths:
                    try:
                        totals = parse_usage_from_source(
                            provider, path,
                            window_start=started_at,
                            window_end=completed_at,
                        )
                        if totals.total_tokens and totals.total_tokens > 0:
                            best_tokens = totals.total_tokens
                            break
                    except Exception:
                        continue

                if best_tokens is None:
                    print(f"  {log_id}: no matching usage found", flush=True)
                    skipped += 1
                    continue

                # Use appropriate usage_mode based on provider
                # Codex returns cumulative counter, not actual window delta
                mode = "cumulative_snapshot" if provider == "codex" else "windowed_sum"

                if dry_run:
                    print(f"  {log_id}: would set tokens_check={best_tokens:,} (mode={mode})", flush=True)
                else:
                    update_analysis_log(
                        log_id,
                        tokens_check=best_tokens,
                        usage_mode=mode,
                        db=db,
                    )
                    print(f"  {log_id}: set tokens_check={best_tokens:,} (mode={mode})", flush=True)
                updated += 1

            print(f"\nBackfill complete: {updated} updated, {skipped} skipped", flush=True)
            if dry_run:
                print("(dry run - no changes made)", flush=True)

        else:
            analysis_parser.print_help()

    # Evidence links commands
    elif args.command == "evidence":
        db = get_db()

        if args.evidence_command == "add":
            link_data = {
                "id": args.id,
                "claim_id": args.claim_id,
                "source_id": args.source_id,
                "direction": args.direction,
                "strength": args.strength,
                "location": args.location,
                "quote": args.quote,
                "reasoning": args.reasoning,
                "analysis_log_id": getattr(args, "analysis_log_id", None),
                "created_by": args.created_by,
            }
            try:
                result = add_evidence_link(link_data, db=db)
                print(f"Created evidence link: {result['id']}", flush=True)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        elif args.evidence_command == "get":
            result = get_evidence_link(args.link_id, db=db)
            if result:
                _output_result(result, args.format, "evidence_link")
            else:
                print(f"Evidence link not found: {args.link_id}", file=sys.stderr)
                sys.exit(1)

        elif args.evidence_command == "list":
            results = list_evidence_links(
                claim_id=getattr(args, "claim_id", None),
                source_id=getattr(args, "source_id", None),
                direction=args.direction,
                include_superseded=args.include_superseded,
                limit=args.limit,
                db=db,
            )
            _output_result(results, args.format, "evidence_link")

        elif args.evidence_command == "supersede":
            try:
                new_fields = {}
                if args.direction:
                    new_fields["direction"] = args.direction
                if args.strength is not None:
                    new_fields["strength"] = args.strength
                if args.location:
                    new_fields["location"] = args.location
                if args.quote:
                    new_fields["quote"] = args.quote
                if args.reasoning:
                    new_fields["reasoning"] = args.reasoning
                new_fields["created_by"] = args.created_by

                result = supersede_evidence_link(args.link_id, db=db, **new_fields)
                print(f"Created new evidence link: {result['id']} (supersedes {args.link_id})", flush=True)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        else:
            evidence_parser.print_help()

    # Reasoning trails commands
    elif args.command == "reasoning":
        db = get_db()

        if args.reasoning_command == "add":
            trail_data = {
                "id": args.id,
                "claim_id": args.claim_id,
                "credence_at_time": args.credence,
                "evidence_level_at_time": args.evidence_level,
                "reasoning_text": args.reasoning_text,
                "evidence_summary": getattr(args, "evidence_summary", None),
                "analysis_pass": getattr(args, "analysis_pass", None),
                "analysis_log_id": getattr(args, "analysis_log_id", None),
                "status": args.status,
                "created_by": args.created_by,
            }

            # Handle comma-separated lists
            if getattr(args, "supporting_evidence", None):
                trail_data["supporting_evidence"] = [s.strip() for s in args.supporting_evidence.split(",")]
            if getattr(args, "contradicting_evidence", None):
                trail_data["contradicting_evidence"] = [s.strip() for s in args.contradicting_evidence.split(",")]
            if getattr(args, "assumptions", None):
                trail_data["assumptions_made"] = [a.strip() for a in args.assumptions.split(",")]
            if getattr(args, "counterarguments_json", None):
                trail_data["counterarguments_json"] = args.counterarguments_json

            try:
                result = add_reasoning_trail(trail_data, db=db)
                print(f"Created reasoning trail: {result['id']}", flush=True)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        elif args.reasoning_command == "get":
            if not args.id and not args.claim_id:
                print("Error: either --id or --claim-id is required", file=sys.stderr)
                sys.exit(1)
            result = get_reasoning_trail(id=args.id, claim_id=getattr(args, "claim_id", None), db=db)
            if result:
                _output_result(result, args.format, "reasoning_trail")
            else:
                target = args.id or args.claim_id
                print(f"Reasoning trail not found for: {target}", file=sys.stderr)
                sys.exit(1)

        elif args.reasoning_command == "list":
            results = list_reasoning_trails(
                claim_id=getattr(args, "claim_id", None),
                include_superseded=args.include_superseded,
                limit=args.limit,
                db=db,
            )
            _output_result(results, args.format, "reasoning_trail")

        elif args.reasoning_command == "history":
            results = get_reasoning_history(args.claim_id, db=db)
            if not results:
                print(f"No reasoning history found for: {args.claim_id}", file=sys.stderr)
                sys.exit(1)
            if args.format == "json":
                import json
                def clean_for_json(obj):
                    if hasattr(obj, 'tolist'):
                        return obj.tolist()
                    elif isinstance(obj, dict):
                        return {k: clean_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_for_json(v) for v in obj]
                    elif hasattr(obj, 'as_py'):
                        return obj.as_py()
                    return obj
                print(json.dumps([clean_for_json(r) for r in results], indent=2, default=str), flush=True)
            else:
                print(f"Credence history for {args.claim_id}:", flush=True)
                for trail in results:
                    status = trail.get("status", "unknown")
                    credence = trail.get("credence_at_time", "?")
                    ev_level = trail.get("evidence_level_at_time", "?")
                    created = trail.get("created_at", "?")
                    print(f"  [{trail['id']}] {created}: credence={credence}, evidence={ev_level} ({status})")
                sys.stdout.flush()

        else:
            reasoning_parser.print_help()

    # Related command
    elif args.command == "related":
        db = get_db()
        result = get_related_claims(args.claim_id, db)
        if not result:
            print(f"Claim not found: {args.claim_id}", file=sys.stderr)
            sys.exit(1)
        if args.format == "json":
            import json
            # Clean the nested claims for JSON
            def clean_for_json(obj):
                if hasattr(obj, 'tolist'):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: clean_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_for_json(v) for v in obj]
                elif hasattr(obj, 'as_py'):
                    return obj.as_py()
                return obj
            print(json.dumps(clean_for_json(result), indent=2, default=str), flush=True)
        else:
            print(f"Related claims for {args.claim_id}:", flush=True)
            for rel_type, claims in result.items():
                if claims:
                    print(f"\n  {rel_type}:")
                    for claim in claims:
                        credence = claim.get('credence')
                        credence_str = f"{credence:.2f}" if credence is not None else "N/A"
                        print(f"    [{claim['id']}] {claim['text'][:60]}...")
                        print(f"      Type: {claim['type']} | Credence: {credence_str}")
            sys.stdout.flush()

    # Import command
    elif args.command == "import":
        db = get_db()

        if not Path(args.file).exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

        with open(args.file, "r") as f:
            data = yaml.safe_load(f)

        created_claims = 0
        created_sources = 0
        updated_claims = 0
        updated_sources = 0
        skipped_claims = 0
        skipped_sources = 0

        def handle_conflict(kind: str, record_id: str) -> str:
            policy = getattr(args, "on_conflict", "error")
            if policy == "skip":
                return "skip"
            if policy == "update":
                return "update"
            print(
                f"Error: {kind} with ID '{record_id}' already exists. "
                "Re-run with --on-conflict skip or --on-conflict update.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Import sources
        if args.type in ["sources", "all"] and "sources" in data:
            sources_data = data["sources"]
            # Handle both list and dict formats
            if isinstance(sources_data, dict):
                sources_list = [{"id": k, **v} for k, v in sources_data.items()]
            else:
                sources_list = sources_data

            for source in sources_list:
                # Ensure author is a list
                if isinstance(source.get("author"), str):
                    source["author"] = [source["author"]]

                # Set defaults
                source.setdefault("claims_extracted", [])
                source.setdefault("topics", [])
                source.setdefault("domains", [])

                source_id = source.get("id")
                if not source_id:
                    print("Error: source missing required field 'id'", file=sys.stderr)
                    sys.exit(1)

                existing = get_source(str(source_id), db)
                if existing:
                    action = handle_conflict("Source", str(source_id))
                    if action == "skip":
                        skipped_sources += 1
                        continue

                    updates = {k: v for k, v in source.items() if k != "id"}
                    ok = update_source(
                        str(source_id),
                        updates,
                        db=db,
                        generate_embedding=should_generate_embedding(args),
                    )
                    if not ok:
                        print(f"Error: failed to update source '{source_id}'", file=sys.stderr)
                        sys.exit(1)
                    updated_sources += 1
                else:
                    add_source(source, db, generate_embedding=should_generate_embedding(args))
                    created_sources += 1

        # Import claims
        if args.type in ["claims", "all"] and "claims" in data:
            claims_data = data["claims"]
            # Handle both list and dict formats
            if isinstance(claims_data, dict):
                claims_list = [{"id": k, **v} for k, v in claims_data.items()]
            else:
                claims_list = claims_data

            for claim in claims_list:
                # Normalize field names
                if "confidence" in claim and "credence" not in claim:
                    claim["credence"] = claim.pop("confidence")

                # Set defaults for required fields
                claim.setdefault("source_ids", [])
                claim.setdefault("first_extracted", str(date.today()))
                claim.setdefault("extracted_by", "import")
                claim.setdefault("version", 1)
                claim.setdefault("last_updated", str(date.today()))
                claim.setdefault("credence", 0.5)
                claim_id = claim.get("id")
                if not claim_id:
                    print("Error: claim missing required field 'id'", file=sys.stderr)
                    sys.exit(1)

                existing = get_claim(str(claim_id), db)
                if existing:
                    action = handle_conflict("Claim", str(claim_id))
                    if action == "skip":
                        skipped_claims += 1
                        continue

                    _replace_claim_row_for_import(
                        str(claim_id),
                        claim,
                        db,
                        generate_embedding=should_generate_embedding(args),
                    )
                    updated_claims += 1
                else:
                    add_claim(claim, db, generate_embedding=should_generate_embedding(args))
                    created_claims += 1

        total_claims = created_claims + updated_claims
        total_sources = created_sources + updated_sources
        print(f"Imported {total_claims} claims, {total_sources} sources", flush=True)
        if any([updated_claims, updated_sources, skipped_claims, skipped_sources]):
            print(
                f"  Sources: {created_sources} created, {updated_sources} updated, {skipped_sources} skipped",
                flush=True,
            )
            print(
                f"  Claims: {created_claims} created, {updated_claims} updated, {skipped_claims} skipped",
                flush=True,
            )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
