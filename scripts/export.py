#!/usr/bin/env python3
"""
Export script for generating human-readable outputs from LanceDB.

Supports:
- YAML export (legacy registry format)
- Markdown export (analysis documents)
- Full registry dump
- Individual record export
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

import yaml

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from db import (
    get_db,
    list_claims,
    list_sources,
    list_chains,
    list_predictions,
    list_contradictions,
    list_definitions,
    get_claim,
    get_source,
    get_chain,
    get_stats,
)


# =============================================================================
# YAML Export (Legacy Format)
# =============================================================================

def export_claims_yaml(db_path: Optional[Path] = None) -> str:
    """Export claims to legacy YAML format."""
    db = get_db(db_path)
    claims = list_claims(limit=100000, db=db)
    chains = list_chains(limit=100000, db=db)

    # Build counters from existing claims
    counters: dict[str, int] = {}
    for claim in claims:
        domain = claim["domain"]
        claim_id = claim["id"]
        _, year_str, num_str = claim_id.split("-")
        num = int(num_str)
        if domain not in counters or num > counters[domain]:
            counters[domain] = num

    # Convert claims to legacy format
    claims_dict = {}
    for claim in sorted(claims, key=lambda c: c["id"]):
        claim_data = {
            "text": claim["text"],
            "type": claim["type"],
            "domain": claim["domain"],
            "evidence_level": claim["evidence_level"],
            "confidence": float(claim["credence"]),  # Back to 'confidence' for legacy
            "source_ids": claim.get("source_ids") or [],
            "first_extracted": claim.get("first_extracted", ""),
            "extracted_by": claim.get("extracted_by", ""),
            "supports": claim.get("supports") or [],
            "contradicts": claim.get("contradicts") or [],
            "depends_on": claim.get("depends_on") or [],
            "modified_by": claim.get("modified_by") or [],
            "part_of_chain": claim.get("part_of_chain") or "",
            "version": claim.get("version", 1),
            "last_updated": claim.get("last_updated", ""),
        }
        if claim.get("notes"):
            claim_data["notes"] = claim["notes"]
        claims_dict[claim["id"]] = claim_data

    # Convert chains to legacy format
    chains_dict = {}
    for chain in sorted(chains, key=lambda c: c["id"]):
        chains_dict[chain["id"]] = {
            "name": chain["name"],
            "thesis": chain["thesis"],
            "confidence": float(chain["credence"]),  # Back to 'confidence'
            "claims": chain.get("claims") or [],
            "analysis_file": chain.get("analysis_file") or "",
            "weakest_link": chain.get("weakest_link") or "",
        }

    output = {
        "counters": counters,
        "claims": claims_dict,
        "chains": chains_dict,
    }

    # Custom YAML dump with nice formatting
    yaml_str = yaml.dump(output, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Add header comment
    header = f"""# Claim Registry
# Exported from LanceDB on {date.today()}
# Total claims: {len(claims)}
# Total chains: {len(chains)}

"""
    return header + yaml_str


def export_sources_yaml(db_path: Optional[Path] = None) -> str:
    """Export sources to legacy YAML format."""
    db = get_db(db_path)
    sources = list_sources(limit=100000, db=db)

    sources_dict = {}
    for source in sorted(sources, key=lambda s: s["id"]):
        source_data = {
            "type": source["type"],
            "title": source["title"],
            "author": source.get("author") or [],
            "year": source.get("year", 0),
            "url": source.get("url") or "",
            "accessed": source.get("accessed") or "",
            "reliability": float(source["reliability"]) if source.get("reliability") else 0.5,
            "bias_notes": source.get("bias_notes") or "",
            "claims_extracted": source.get("claims_extracted") or [],
            "analysis_file": source.get("analysis_file") or "",
            "topics": source.get("topics") or [],
            "domains": source.get("domains") or [],
        }
        if source.get("status"):
            source_data["status"] = source["status"]
        sources_dict[source["id"]] = source_data

    output = {"sources": sources_dict}
    yaml_str = yaml.dump(output, default_flow_style=False, sort_keys=False, allow_unicode=True)

    header = f"""# Source Registry
# Exported from LanceDB on {date.today()}
# Total sources: {len(sources)}

"""
    return header + yaml_str


# =============================================================================
# Markdown Export
# =============================================================================

def export_claim_md(claim_id: str, db_path: Optional[Path] = None) -> str:
    """Export a single claim as Markdown."""
    db = get_db(db_path)
    claim = get_claim(claim_id, db)

    if not claim:
        return f"# Claim Not Found: {claim_id}\n"

    lines = [
        f"# {claim_id}",
        "",
        f"**Text**: {claim['text']}",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Type | {claim['type']} |",
        f"| Domain | {claim['domain']} |",
        f"| Evidence Level | {claim['evidence_level']} |",
        f"| Credence | {claim['credence']:.2f} |",
        "",
    ]

    # Operationalization (v1.0)
    if claim.get("operationalization"):
        lines.extend([
            "## Operationalization",
            "",
            claim["operationalization"],
            "",
        ])

    if claim.get("assumptions"):
        lines.extend([
            "## Assumptions",
            "",
        ])
        for assumption in claim["assumptions"]:
            lines.append(f"- {assumption}")
        lines.append("")

    if claim.get("falsifiers"):
        lines.extend([
            "## Falsifiers",
            "",
        ])
        for falsifier in claim["falsifiers"]:
            lines.append(f"- {falsifier}")
        lines.append("")

    # Relationships
    lines.extend([
        "## Relationships",
        "",
    ])

    for rel_type in ["supports", "contradicts", "depends_on", "modified_by"]:
        refs = claim.get(rel_type) or []
        if refs:
            lines.append(f"**{rel_type.replace('_', ' ').title()}**: {', '.join(refs)}")

    if claim.get("part_of_chain"):
        lines.append(f"**Part of Chain**: {claim['part_of_chain']}")

    lines.append("")

    # Provenance
    lines.extend([
        "## Provenance",
        "",
        f"- **Sources**: {', '.join(claim.get('source_ids') or [])}",
        f"- **First Extracted**: {claim.get('first_extracted', 'Unknown')}",
        f"- **Extracted By**: {claim.get('extracted_by', 'Unknown')}",
        f"- **Version**: {claim.get('version', 1)}",
        f"- **Last Updated**: {claim.get('last_updated', 'Unknown')}",
        "",
    ])

    if claim.get("notes"):
        lines.extend([
            "## Notes",
            "",
            claim["notes"],
            "",
        ])

    return "\n".join(lines)


def export_chain_md(chain_id: str, db_path: Optional[Path] = None) -> str:
    """Export an argument chain as Markdown."""
    db = get_db(db_path)
    chain = get_chain(chain_id, db)

    if not chain:
        return f"# Chain Not Found: {chain_id}\n"

    lines = [
        f"# Chain: {chain_id} \"{chain['name']}\"",
        "",
        f"**Thesis**: {chain['thesis']}",
        "",
        f"**Credence**: {chain['credence']:.2f}",
        "",
        f"> **Scoring Rule**: Chain credence = MIN(step credences)",
        "",
        "## Claims in Chain",
        "",
    ]

    # Load and display each claim
    claim_ids = chain.get("claims") or []
    for i, claim_id in enumerate(claim_ids, 1):
        claim = get_claim(claim_id, db)
        if claim:
            lines.extend([
                f"### {i}. {claim_id}",
                "",
                f"**{claim['type']}** {claim['text']}",
                "",
                f"- Evidence: {claim['evidence_level']}",
                f"- Credence: {claim['credence']:.2f}",
                "",
            ])
            if i < len(claim_ids):
                lines.extend([
                    "↓",
                    "",
                ])

    lines.extend([
        "## Analysis",
        "",
        f"**Weakest Link**: {chain.get('weakest_link', 'Not specified')}",
        "",
    ])

    if chain.get("analysis_file"):
        lines.append(f"**Analysis File**: {chain['analysis_file']}")

    return "\n".join(lines)


def export_predictions_md(db_path: Optional[Path] = None) -> str:
    """Export predictions to Markdown format."""
    db = get_db(db_path)
    predictions = list_predictions(limit=100000, db=db)

    lines = [
        "# Prediction Tracking",
        "",
        f"*Generated {date.today()}*",
        "",
        "## Active Predictions",
        "",
    ]

    # Group by status
    status_groups = {
        "[P→]": "On Track",
        "[P?]": "Uncertain",
        "[P←]": "Off Track",
        "[P+]": "Confirmed",
        "[P~]": "Partially Confirmed",
        "[P!]": "Partially Refuted",
        "[P-]": "Refuted",
        "[P∅]": "Unfalsifiable",
    }

    for status_code, status_name in status_groups.items():
        status_preds = [p for p in predictions if p.get("status") == status_code]
        if status_preds:
            lines.extend([
                f"### {status_name} ({status_code})",
                "",
            ])
            for pred in status_preds:
                claim = get_claim(pred["claim_id"], db)
                claim_text = claim["text"] if claim else "Unknown claim"

                lines.extend([
                    f"#### {pred['claim_id']}",
                    "",
                    f"> {claim_text}",
                    "",
                    f"- **Status**: {pred['status']}",
                    f"- **Source**: {pred.get('source_id', 'Unknown')}",
                ])

                if pred.get("target_date"):
                    lines.append(f"- **Target Date**: {pred['target_date']}")
                if pred.get("falsification_criteria"):
                    lines.append(f"- **Falsification**: {pred['falsification_criteria']}")
                if pred.get("verification_criteria"):
                    lines.append(f"- **Verification**: {pred['verification_criteria']}")
                if pred.get("last_evaluated"):
                    lines.append(f"- **Last Evaluated**: {pred['last_evaluated']}")

                lines.append("")

    return "\n".join(lines)


def export_summary_md(db_path: Optional[Path] = None) -> str:
    """Export a summary dashboard."""
    db = get_db(db_path)
    stats = get_stats(db)

    claims = list_claims(limit=100000, db=db)
    sources = list_sources(limit=100000, db=db)
    chains = list_chains(limit=100000, db=db)

    lines = [
        "# Reality Check Summary",
        "",
        f"*Generated {date.today()}*",
        "",
        "## Statistics",
        "",
        "| Table | Count |",
        "|-------|-------|",
    ]

    for table, count in stats.items():
        lines.append(f"| {table} | {count} |")

    lines.extend(["", "## Claims by Domain", ""])

    # Count by domain
    domain_counts: dict[str, int] = {}
    for claim in claims:
        domain = claim.get("domain", "UNKNOWN")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    lines.append("| Domain | Count |")
    lines.append("|--------|-------|")
    for domain, count in sorted(domain_counts.items()):
        lines.append(f"| {domain} | {count} |")

    lines.extend(["", "## Claims by Type", ""])

    # Count by type
    type_counts: dict[str, int] = {}
    for claim in claims:
        ctype = claim.get("type", "Unknown")
        type_counts[ctype] = type_counts.get(ctype, 0) + 1

    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    for ctype, count in sorted(type_counts.items()):
        lines.append(f"| {ctype} | {count} |")

    lines.extend(["", "## Sources by Type", ""])

    source_type_counts: dict[str, int] = {}
    for source in sources:
        stype = source.get("type", "Unknown")
        source_type_counts[stype] = source_type_counts.get(stype, 0) + 1

    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    for stype, count in sorted(source_type_counts.items()):
        lines.append(f"| {stype} | {count} |")

    lines.extend(["", "## Argument Chains", ""])

    for chain in chains:
        lines.append(f"- **{chain['id']}**: {chain['name']} (credence: {chain['credence']:.2f})")

    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Export Reality Check data"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Database path",
    )

    subparsers = parser.add_subparsers(dest="command", help="Export commands")

    # yaml command
    yaml_parser = subparsers.add_parser("yaml", help="Export to YAML format")
    yaml_parser.add_argument(
        "type",
        choices=["claims", "sources", "all"],
        help="What to export"
    )
    yaml_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)"
    )

    # md command
    md_parser = subparsers.add_parser("md", help="Export to Markdown format")
    md_parser.add_argument(
        "type",
        choices=["claim", "chain", "predictions", "summary"],
        help="What to export"
    )
    md_parser.add_argument(
        "--id",
        help="ID for claim/chain export"
    )
    md_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)"
    )

    # stats command
    subparsers.add_parser("stats", help="Show database statistics")

    args = parser.parse_args()

    def output_result(content: str, output_path: Optional[Path]):
        if output_path:
            output_path.write_text(content)
            print(f"Exported to {output_path}")
        else:
            print(content)

    if args.command == "yaml":
        if args.type == "claims":
            content = export_claims_yaml(args.db_path)
        elif args.type == "sources":
            content = export_sources_yaml(args.db_path)
        else:  # all
            content = export_claims_yaml(args.db_path) + "\n---\n\n" + export_sources_yaml(args.db_path)
        output_result(content, args.output)

    elif args.command == "md":
        if args.type == "claim":
            if not args.id:
                print("Error: --id required for claim export", file=sys.stderr)
                sys.exit(1)
            content = export_claim_md(args.id, args.db_path)
        elif args.type == "chain":
            if not args.id:
                print("Error: --id required for chain export", file=sys.stderr)
                sys.exit(1)
            content = export_chain_md(args.id, args.db_path)
        elif args.type == "predictions":
            content = export_predictions_md(args.db_path)
        else:  # summary
            content = export_summary_md(args.db_path)
        output_result(content, args.output)

    elif args.command == "stats":
        stats = get_stats(get_db(args.db_path))
        print("Database Statistics:")
        for table, count in stats.items():
            print(f"  {table}: {count}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
