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
    from .usage_capture import estimate_cost_usd, parse_usage_from_source
else:
    from analysis_log_writer import upsert_analysis_log_section
    from usage_capture import estimate_cost_usd, parse_usage_from_source

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
    for table_name in ["claims", "sources", "chains", "predictions", "contradictions", "definitions", "analysis_logs"]:
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
# Statistics
# =============================================================================

def get_stats(db: Optional[lancedb.DBConnection] = None) -> dict:
    """Get statistics about the database."""
    if db is None:
        db = get_db()

    stats = {}
    existing_tables = get_table_names(db)
    for table_name in ["claims", "sources", "chains", "predictions", "contradictions", "definitions", "analysis_logs"]:
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
    analysis_complete.add_argument("--notes", help="Notes about completion")
    analysis_complete.add_argument("--estimate-cost", action="store_true", help="Estimate cost from tokens")

    # analysis sessions (nested subcommand)
    analysis_sessions = analysis_subparsers.add_parser("sessions", help="Session discovery helpers")
    sessions_subparsers = analysis_sessions.add_subparsers(dest="sessions_command")

    sessions_list = sessions_subparsers.add_parser("list", help="List available sessions")
    sessions_list.add_argument("--tool", required=True, help="Tool to list sessions for (claude-code/codex/amp)")
    sessions_list.add_argument("--limit", type=int, default=10, help="Max sessions to show")

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
            from usage_capture import (
                get_current_session_path,
                get_session_token_count,
                NoSessionFoundError,
                AmbiguousSessionError,
                _tool_to_provider,
            )

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
                    from usage_capture import _extract_uuid_from_filename
                    session_id = _extract_uuid_from_filename(session_path.name, provider)
            elif session_id:
                # Have ID but not path - try to find path and get tokens
                try:
                    from usage_capture import get_session_token_count_by_uuid
                    tokens_baseline = get_session_token_count_by_uuid(session_id, provider)
                except Exception:
                    pass  # OK if we can't get baseline, can still track session ID

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
            # Lifecycle: mark a stage checkpoint
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

            # Add new stage
            stage_entry = {
                "stage": stage_name,
                "timestamp": dt.utcnow().isoformat() + "Z",
            }
            if getattr(args, "notes", None):
                stage_entry["notes"] = args.notes

            stages.append(stage_entry)

            update_analysis_log(log_id, stages_json=json_module.dumps(stages), db=db)
            print(f"Marked stage '{stage_name}' for {log_id}", flush=True)

        elif args.analysis_command == "complete":
            # Lifecycle: complete an analysis with final snapshot
            import json as json_module
            from datetime import datetime as dt
            from usage_capture import get_session_token_count_by_uuid, _tool_to_provider

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
                from usage_capture import list_sessions, _tool_to_provider

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

        else:
            analysis_parser.print_help()

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
