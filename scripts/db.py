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
    for table_name in ["claims", "sources", "chains", "predictions", "contradictions", "definitions"]:
        if table_name in existing_tables:
            db.drop_table(table_name)


# =============================================================================
# CRUD Operations - Claims
# =============================================================================

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

    # Merge updates
    existing.update(updates)

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
    return True


def delete_claim(claim_id: str, db: Optional[lancedb.DBConnection] = None) -> bool:
    """Delete a claim by ID."""
    if db is None:
        db = get_db()

    table = db.open_table("claims")
    table.delete(f"id = '{claim_id}'")
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
# Statistics
# =============================================================================

def get_stats(db: Optional[lancedb.DBConnection] = None) -> dict:
    """Get statistics about the database."""
    if db is None:
        db = get_db()

    stats = {}
    existing_tables = get_table_names(db)
    for table_name in ["claims", "sources", "chains", "predictions", "contradictions", "definitions"]:
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
    source_add.add_argument("--no-embedding", action="store_true", help="Skip embedding generation")

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
    import_parser.add_argument("--no-embedding", action="store_true", help="Skip embedding generation")

    # -------------------------------------------------------------------------
    # Parse and execute
    # -------------------------------------------------------------------------
    args = parser.parse_args()

    def ensure_data_selected_for_command(command: Optional[str]) -> None:
        """
        Fail early with a friendly message when the database location is ambiguous.

        If REALITYCHECK_DATA is unset, we only proceed without error when:
        - The command is creating a new DB (`init`, `reset`) or creating a project (`init-project`), or
        - A default `./data/realitycheck.lance` exists in the current directory.
        """
        if not command:
            return

        if os.getenv("REALITYCHECK_DATA"):
            return

        default_db = Path("data/realitycheck.lance")

        if command == "init-project":
            return

        if command in {"init", "reset"}:
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
                "claims_extracted": [],
                "analysis_file": None,
                "topics": [],
                "domains": [],
                "status": args.status,
            }
            result_id = add_source(source, db, generate_embedding=should_generate_embedding(args))
            print(f"Created source: {result_id}", flush=True)

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

        imported_claims = 0
        imported_sources = 0

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

                add_claim(claim, db, generate_embedding=should_generate_embedding(args))
                imported_claims += 1

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

                add_source(source, db, generate_embedding=should_generate_embedding(args))
                imported_sources += 1

        print(f"Imported {imported_claims} claims, {imported_sources} sources", flush=True)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
