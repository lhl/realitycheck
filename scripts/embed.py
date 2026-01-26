#!/usr/bin/env python3
"""
Embedding generation utilities for Reality Check.

Supports:
- Batch embedding generation for existing records
- Re-embedding after model change
- Embedding status check
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

if __package__:
    from .db import (
        get_db,
        embed_text,
        embed_texts,
        list_claims,
        list_sources,
        list_chains,
        get_claim,
        get_source,
        get_chain,
        EMBEDDING_MODEL,
    )
else:
    from db import (
        get_db,
        embed_text,
        embed_texts,
        list_claims,
        list_sources,
        list_chains,
        get_claim,
        get_source,
        get_chain,
        EMBEDDING_MODEL,
    )


def check_embeddings(db_path: Optional[Path] = None) -> dict:
    """Check embedding status for all tables."""
    db = get_db(db_path)

    status = {
        "claims": {"total": 0, "with_embedding": 0, "missing": []},
        "sources": {"total": 0, "with_embedding": 0, "missing": []},
        "chains": {"total": 0, "with_embedding": 0, "missing": []},
    }

    # Check claims
    claims = list_claims(limit=100000, db=db)
    status["claims"]["total"] = len(claims)
    for claim in claims:
        if claim.get("embedding"):
            status["claims"]["with_embedding"] += 1
        else:
            status["claims"]["missing"].append(claim["id"])

    # Check sources
    sources = list_sources(limit=100000, db=db)
    status["sources"]["total"] = len(sources)
    for source in sources:
        if source.get("embedding"):
            status["sources"]["with_embedding"] += 1
        else:
            status["sources"]["missing"].append(source["id"])

    # Check chains
    chains = list_chains(limit=100000, db=db)
    status["chains"]["total"] = len(chains)
    for chain in chains:
        if chain.get("embedding"):
            status["chains"]["with_embedding"] += 1
        else:
            status["chains"]["missing"].append(chain["id"])

    return status


def generate_missing_embeddings(
    db_path: Optional[Path] = None,
    verbose: bool = False,
    batch_size: int = 32,
) -> dict:
    """Generate embeddings for records that don't have them."""
    db = get_db(db_path)

    stats = {
        "claims_embedded": 0,
        "sources_embedded": 0,
        "chains_embedded": 0,
        "errors": [],
    }

    # Process claims
    claims = list_claims(limit=100000, db=db)
    claims_to_embed = [c for c in claims if not c.get("embedding")]

    if verbose and claims_to_embed:
        print(f"Generating embeddings for {len(claims_to_embed)} claims...")

    for i in range(0, len(claims_to_embed), batch_size):
        batch = claims_to_embed[i:i + batch_size]
        texts = [c["text"] for c in batch]

        try:
            embeddings = embed_texts(texts)

            table = db.open_table("claims")
            for claim, embedding in zip(batch, embeddings):
                claim["embedding"] = embedding
                table.delete(f"id = '{claim['id']}'")
                table.add([claim])
                stats["claims_embedded"] += 1

                if verbose:
                    print(f"  ✓ {claim['id']}")
        except Exception as e:
            stats["errors"].append(f"Claims batch {i}: {e}")
            if verbose:
                print(f"  ✗ Batch error: {e}")

    # Process sources
    sources = list_sources(limit=100000, db=db)
    sources_to_embed = [s for s in sources if not s.get("embedding")]

    if verbose and sources_to_embed:
        print(f"\nGenerating embeddings for {len(sources_to_embed)} sources...")

    for source in sources_to_embed:
        try:
            embed_parts = [source.get("title", "")]
            if source.get("bias_notes"):
                embed_parts.append(source["bias_notes"])
            embedding = embed_text(". ".join(embed_parts))

            source["embedding"] = embedding
            table = db.open_table("sources")
            table.delete(f"id = '{source['id']}'")
            table.add([source])
            stats["sources_embedded"] += 1

            if verbose:
                print(f"  ✓ {source['id']}")
        except Exception as e:
            stats["errors"].append(f"Source {source['id']}: {e}")
            if verbose:
                print(f"  ✗ {source['id']}: {e}")

    # Process chains
    chains = list_chains(limit=100000, db=db)
    chains_to_embed = [c for c in chains if not c.get("embedding")]

    if verbose and chains_to_embed:
        print(f"\nGenerating embeddings for {len(chains_to_embed)} chains...")

    for chain in chains_to_embed:
        try:
            embed_text_str = f"{chain.get('name', '')}. {chain.get('thesis', '')}"
            embedding = embed_text(embed_text_str)

            chain["embedding"] = embedding
            table = db.open_table("chains")
            table.delete(f"id = '{chain['id']}'")
            table.add([chain])
            stats["chains_embedded"] += 1

            if verbose:
                print(f"  ✓ {chain['id']}")
        except Exception as e:
            stats["errors"].append(f"Chain {chain['id']}: {e}")
            if verbose:
                print(f"  ✗ {chain['id']}: {e}")

    return stats


def regenerate_all_embeddings(
    db_path: Optional[Path] = None,
    verbose: bool = False,
    batch_size: int = 32,
) -> dict:
    """Regenerate all embeddings (useful after model change)."""
    db = get_db(db_path)

    stats = {
        "claims_embedded": 0,
        "sources_embedded": 0,
        "chains_embedded": 0,
        "errors": [],
    }

    # Process all claims
    claims = list_claims(limit=100000, db=db)

    if verbose:
        print(f"Regenerating embeddings for {len(claims)} claims...")

    for i in range(0, len(claims), batch_size):
        batch = claims[i:i + batch_size]
        texts = [c["text"] for c in batch]

        try:
            embeddings = embed_texts(texts)

            table = db.open_table("claims")
            for claim, embedding in zip(batch, embeddings):
                claim["embedding"] = embedding
                table.delete(f"id = '{claim['id']}'")
                table.add([claim])
                stats["claims_embedded"] += 1
        except Exception as e:
            stats["errors"].append(f"Claims batch {i}: {e}")

    if verbose:
        print(f"  Embedded {stats['claims_embedded']} claims")

    # Process all sources
    sources = list_sources(limit=100000, db=db)

    if verbose:
        print(f"\nRegenerating embeddings for {len(sources)} sources...")

    for source in sources:
        try:
            embed_parts = [source.get("title", "")]
            if source.get("bias_notes"):
                embed_parts.append(source["bias_notes"])
            embedding = embed_text(". ".join(embed_parts))

            source["embedding"] = embedding
            table = db.open_table("sources")
            table.delete(f"id = '{source['id']}'")
            table.add([source])
            stats["sources_embedded"] += 1
        except Exception as e:
            stats["errors"].append(f"Source {source['id']}: {e}")

    if verbose:
        print(f"  Embedded {stats['sources_embedded']} sources")

    # Process all chains
    chains = list_chains(limit=100000, db=db)

    if verbose:
        print(f"\nRegenerating embeddings for {len(chains)} chains...")

    for chain in chains:
        try:
            embed_text_str = f"{chain.get('name', '')}. {chain.get('thesis', '')}"
            embedding = embed_text(embed_text_str)

            chain["embedding"] = embedding
            table = db.open_table("chains")
            table.delete(f"id = '{chain['id']}'")
            table.add([chain])
            stats["chains_embedded"] += 1
        except Exception as e:
            stats["errors"].append(f"Chain {chain['id']}: {e}")

    if verbose:
        print(f"  Embedded {stats['chains_embedded']} chains")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Embedding generation utilities"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status command
    status_parser = subparsers.add_parser("status", help="Check embedding status")
    status_parser.add_argument("--db-path", type=Path, help="Database path")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate missing embeddings")
    gen_parser.add_argument("--db-path", type=Path, help="Database path")
    gen_parser.add_argument("-v", "--verbose", action="store_true")
    gen_parser.add_argument("--batch-size", type=int, default=32)

    # regenerate command
    regen_parser = subparsers.add_parser("regenerate", help="Regenerate all embeddings")
    regen_parser.add_argument("--db-path", type=Path, help="Database path")
    regen_parser.add_argument("-v", "--verbose", action="store_true")
    regen_parser.add_argument("--batch-size", type=int, default=32)

    args = parser.parse_args()

    if args.command:
        db_path = getattr(args, "db_path", None)
        if db_path is None and not os.getenv("REALITYCHECK_DATA"):
            default_db = Path("data/realitycheck.lance")
            if not default_db.exists():
                print(
                    "Error: REALITYCHECK_DATA is not set and no default database was found at "
                    f"'{default_db}'. Set REALITYCHECK_DATA or pass --db-path.",
                    file=sys.stderr,
                )
                sys.exit(2)

    if args.command == "status":
        print(f"Embedding model: {EMBEDDING_MODEL}")
        print()

        status = check_embeddings(args.db_path)

        for table, info in status.items():
            pct = (info["with_embedding"] / info["total"] * 100) if info["total"] > 0 else 0
            print(f"{table}: {info['with_embedding']}/{info['total']} ({pct:.0f}%)")
            if info["missing"]:
                print(f"  Missing: {', '.join(info['missing'][:5])}" +
                      (f"... (+{len(info['missing']) - 5} more)" if len(info["missing"]) > 5 else ""))

    elif args.command == "generate":
        stats = generate_missing_embeddings(
            db_path=args.db_path,
            verbose=args.verbose,
            batch_size=args.batch_size,
        )
        print(f"\nGenerated embeddings:")
        print(f"  Claims: {stats['claims_embedded']}")
        print(f"  Sources: {stats['sources_embedded']}")
        print(f"  Chains: {stats['chains_embedded']}")
        if stats["errors"]:
            print(f"  Errors: {len(stats['errors'])}")

    elif args.command == "regenerate":
        confirm = input("This will regenerate ALL embeddings. Continue? [y/N] ")
        if confirm.lower() != "y":
            print("Aborted.")
            return

        stats = regenerate_all_embeddings(
            db_path=args.db_path,
            verbose=args.verbose,
            batch_size=args.batch_size,
        )
        print(f"\nRegenerated embeddings:")
        print(f"  Claims: {stats['claims_embedded']}")
        print(f"  Sources: {stats['sources_embedded']}")
        print(f"  Chains: {stats['chains_embedded']}")
        if stats["errors"]:
            print(f"  Errors: {len(stats['errors'])}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
