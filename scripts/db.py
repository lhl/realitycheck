#!/usr/bin/env python3
"""
LanceDB wrapper for RealityCheck.

Provides schema definitions, CRUD operations, and semantic search
for claims, sources, chains, predictions, contradictions, and definitions.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Optional

import lancedb
import pyarrow as pa

# Configuration
DB_PATH = Path(os.getenv("ANALYSIS_DB_PATH", "data/realitycheck.lance"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 dimension

# Lazy-loaded embedding model
_embedder = None


def get_embedder():
    """Lazy-load the sentence transformer model."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def embed_text(text: str) -> list[float]:
    """Generate embedding for a text string."""
    embedder = get_embedder()
    return embedder.encode(text).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts (batched)."""
    embedder = get_embedder()
    return embedder.encode(texts).tolist()


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
    pa.field("type", pa.string(), nullable=False),  # PAPER/BOOK/REPORT/ARTICLE/BLOG/SOCIAL/CONVO/KNOWLEDGE
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
    """Add a claim to the database. Returns the claim ID."""
    if db is None:
        db = get_db()

    table = db.open_table("claims")

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
# CLI
# =============================================================================

def main():
    """CLI entry point."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="RealityCheck Database CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init command
    subparsers.add_parser("init", help="Initialize database tables")

    # stats command
    subparsers.add_parser("stats", help="Show database statistics")

    # reset command
    subparsers.add_parser("reset", help="Drop all tables and reinitialize")

    # search command
    search_parser = subparsers.add_parser("search", help="Search claims semantically")
    search_parser.add_argument("query", help="Search query text")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results")
    search_parser.add_argument("--domain", help="Filter by domain")

    args = parser.parse_args()

    if args.command == "init":
        db = get_db()
        tables = init_tables(db)
        print(f"Initialized {len(tables)} tables at {DB_PATH}")
        for name in tables:
            print(f"  - {name}")

    elif args.command == "stats":
        stats = get_stats()
        print("Database Statistics:")
        for table, count in stats.items():
            print(f"  {table}: {count} rows")

    elif args.command == "reset":
        db = get_db()
        drop_tables(db)
        tables = init_tables(db)
        print(f"Reset complete. Initialized {len(tables)} tables.")

    elif args.command == "search":
        results = search_claims(args.query, limit=args.limit, domain=args.domain)
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result['id']}] {result['text'][:80]}...")
            print(f"   Type: {result['type']} | Domain: {result['domain']} | Credence: {result['credence']}")
            print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
