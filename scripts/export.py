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
import numbers
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

import yaml

if __package__:
    from .db import (
        find_project_root,
        resolve_db_path_from_project_root,
        get_db,
        list_claims,
        list_sources,
        list_chains,
        list_predictions,
        list_contradictions,
        list_definitions,
        list_analysis_logs,
        list_evidence_links,
        list_reasoning_trails,
        get_reasoning_history,
        get_claim,
        get_source,
        get_chain,
        get_stats,
    )
else:
    from db import (
        find_project_root,
        resolve_db_path_from_project_root,
        get_db,
        list_claims,
        list_sources,
        list_chains,
        list_predictions,
        list_contradictions,
        list_definitions,
        list_analysis_logs,
        list_evidence_links,
        list_reasoning_trails,
        get_reasoning_history,
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
            "credence": float(claim["credence"]),
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
            "credence": float(chain["credence"]),
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
# Analysis Logs Export
# =============================================================================

def export_analysis_logs_yaml(db_path: Optional[Path] = None) -> str:
    """Export analysis logs to YAML format."""
    db = get_db(db_path)
    logs = list_analysis_logs(limit=100000, db=db)

    # Convert to serializable format
    logs_list = []
    for log in sorted(logs, key=lambda x: x.get("created_at", "")):
        log_data = {
            "id": log["id"],
            "source_id": log["source_id"],
            "analysis_file": log.get("analysis_file"),
            "pass": log.get("pass"),
            "status": log["status"],
            "tool": log["tool"],
            "command": log.get("command"),
            "model": log.get("model"),
            "framework_version": log.get("framework_version"),
            "methodology_version": log.get("methodology_version"),
            "started_at": log.get("started_at"),
            "completed_at": log.get("completed_at"),
            "duration_seconds": log.get("duration_seconds"),
            "tokens_in": log.get("tokens_in"),
            "tokens_out": log.get("tokens_out"),
            "total_tokens": log.get("total_tokens"),
            "cost_usd": float(log["cost_usd"]) if log.get("cost_usd") is not None else None,
            # Delta accounting fields
            "tokens_baseline": log.get("tokens_baseline"),
            "tokens_final": log.get("tokens_final"),
            "tokens_check": log.get("tokens_check"),
            "usage_provider": log.get("usage_provider"),
            "usage_mode": log.get("usage_mode"),
            "usage_session_id": log.get("usage_session_id"),
            # Synthesis linking fields
            "inputs_source_ids": list(log.get("inputs_source_ids") or []),
            "inputs_analysis_ids": list(log.get("inputs_analysis_ids") or []),
            "stages_json": log.get("stages_json"),
            "claims_extracted": list(log.get("claims_extracted") or []),
            "claims_updated": list(log.get("claims_updated") or []),
            "notes": log.get("notes"),
            "git_commit": log.get("git_commit"),
            "created_at": log.get("created_at"),
        }
        logs_list.append(log_data)

    output = {
        "analysis_logs": logs_list,
    }

    header = f"# Reality Check Analysis Logs Export\n# Generated: {date.today().isoformat()}\n\n"
    return header + yaml.dump(output, default_flow_style=False, sort_keys=False, allow_unicode=True)


def export_analysis_logs_md(db_path: Optional[Path] = None) -> str:
    """Export analysis logs to Markdown format with summary totals."""
    db = get_db(db_path)
    logs = list_analysis_logs(limit=100000, db=db)

    def _cell(value: object) -> str:
        text = "" if value is None else str(value)
        return text.replace("|", "\\|").replace("\n", " ").strip()

    lines = [
        "# Analysis Logs",
        "",
        f"*Exported: {date.today().isoformat()}*",
        "",
    ]

    if not logs:
        lines.append("*No analysis logs found.*")
        return "\n".join(lines)

    # Summary table
    lines.extend([
        "## Log Entries",
        "",
        "| Pass | Date | Source | Tool | Model | Duration | Tokens | Cost | Notes |",
        "|------|------|--------|------|-------|----------|--------|------|-------|",
    ])

    total_tokens_known = 0
    total_tokens_unknown = 0
    total_cost_known = 0.0
    total_cost_unknown = 0

    for log in sorted(logs, key=lambda x: x.get("created_at", "")):
        pass_num = log.get("pass", "?")
        date_str = (log.get("started_at") or log.get("created_at") or "")[:10]
        source_id = _cell(log.get("source_id", ""))
        tool = _cell(log.get("tool", ""))
        model = _cell(log.get("model") or "?")
        duration = log.get("duration_seconds")
        duration_str = (
            f"{int(duration) // 60}m{int(duration) % 60}s"
            if isinstance(duration, numbers.Real)
            else "?"
        )
        # Prefer tokens_check (delta accounting) over total_tokens (legacy)
        tokens_check = log.get("tokens_check")
        tokens = tokens_check if tokens_check is not None else log.get("total_tokens")
        tokens_str = f"{int(tokens):,}" if isinstance(tokens, numbers.Integral) else "?"
        cost = log.get("cost_usd")
        cost_str = f"${cost:.4f}" if cost is not None else "?"
        notes = _cell(log.get("notes") or "")

        if isinstance(tokens, numbers.Integral):
            total_tokens_known += int(tokens)
        else:
            total_tokens_unknown += 1
        if cost is not None:
            total_cost_known += cost
        else:
            total_cost_unknown += 1

        lines.append(f"| {pass_num} | {date_str} | {source_id} | {tool} | {model} | {duration_str} | {tokens_str} | {cost_str} | {notes} |")

    # Totals
    tokens_suffix = f" (known; {total_tokens_unknown} unknown)" if total_tokens_unknown else ""
    cost_suffix = f" (known; {total_cost_unknown} unknown)" if total_cost_unknown else ""
    lines.extend([
        "",
        "## Summary Totals",
        "",
        f"- **Total Logs**: {len(logs)}",
        f"- **Total Tokens**: {total_tokens_known:,}{tokens_suffix}",
        f"- **Total Cost**: ${total_cost_known:.4f}{cost_suffix}",
    ])

    # Breakdown by tool
    tool_counts: dict[str, int] = {}
    tool_tokens: dict[str, int] = {}
    tool_costs: dict[str, float] = {}
    for log in logs:
        tool = log.get("tool", "unknown") or "unknown"
        tool_counts[tool] = tool_counts.get(tool, 0) + 1
        # Prefer tokens_check (delta accounting) over total_tokens (legacy)
        tokens_check = log.get("tokens_check")
        tokens = tokens_check if tokens_check is not None else log.get("total_tokens")
        if tokens is not None:
            tool_tokens[tool] = tool_tokens.get(tool, 0) + tokens
        if log.get("cost_usd") is not None:
            tool_costs[tool] = tool_costs.get(tool, 0.0) + log["cost_usd"]

    lines.extend([
        "",
        "### By Tool",
        "",
        "| Tool | Logs | Tokens | Cost |",
        "|------|------|--------|------|",
    ])
    for tool in sorted(tool_counts.keys()):
        tokens_str = f"{tool_tokens.get(tool, 0):,}"
        cost_str = f"${tool_costs.get(tool, 0.0):.4f}"
        lines.append(f"| {tool} | {tool_counts[tool]} | {tokens_str} | {cost_str} |")

    return "\n".join(lines)


# =============================================================================
# Reasoning/Provenance Export
# =============================================================================

def export_reasoning_md(claim_id: str, db_path: Optional[Path] = None, output_dir: Optional[Path] = None) -> str:
    """Export reasoning trail for a single claim as Markdown.

    Args:
        claim_id: ID of the claim to export reasoning for
        db_path: Path to LanceDB database
        output_dir: If provided, generate relative links to sources

    Returns:
        Markdown string with reasoning trail
    """
    db = get_db(db_path)
    claim = get_claim(claim_id, db)

    if not claim:
        return f"# Reasoning: {claim_id}\n\nClaim not found."

    # Get active reasoning trail for this claim
    trails = list_reasoning_trails(claim_id=claim_id, db=db)
    trail = trails[0] if trails else None

    # Get evidence links for this claim
    evidence_links = list_evidence_links(claim_id=claim_id, db=db)

    # Build source links (relative if output_dir provided)
    def source_link(source_id: str) -> str:
        if output_dir:
            return f"[{source_id}](../sources/{source_id}.md)"
        return source_id

    lines = [
        f"# Reasoning: {claim_id}",
        "",
        f"> **Claim**: {claim['text']}",
        f"> **Credence**: {claim.get('credence', 0):.2f} ({claim.get('evidence_level', 'N/A')})",
        f"> **Domain**: {claim.get('domain', 'N/A')}",
        "",
        "## Evidence Summary",
        "",
    ]

    if evidence_links:
        lines.extend([
            "| Direction | Source | Location | Strength | Summary |",
            "|-----------|--------|----------|----------|---------|",
        ])
        for link in evidence_links:
            direction = link.get("direction", "")
            source_id = link.get("source_id", "")
            location = link.get("location", "")
            strength = link.get("strength")
            strength_str = f"{strength:.1f}" if strength is not None else ""
            reasoning = (link.get("reasoning") or "")[:50]
            if len(link.get("reasoning", "")) > 50:
                reasoning += "..."
            lines.append(f"| {direction.title()} | {source_link(source_id)} | {location} | {strength_str} | {reasoning} |")
        lines.append("")
    else:
        lines.append("*No evidence links found for this claim.*")
        lines.append("")

    # Reasoning Chain
    lines.extend([
        "## Reasoning Chain",
        "",
    ])

    if trail:
        if trail.get("reasoning_text"):
            lines.append(trail["reasoning_text"])
            lines.append("")

        # Counterarguments
        counterarguments_json = trail.get("counterarguments_json")
        if counterarguments_json:
            try:
                counterarguments = json.loads(counterarguments_json) if isinstance(counterarguments_json, str) else counterarguments_json
                if counterarguments:
                    lines.extend([
                        "## Counterarguments Considered",
                        "",
                    ])
                    for ca in counterarguments:
                        # Accept both 'text' (canonical) and 'argument' (legacy) field names
                        arg_text = ca.get('text') or ca.get('argument', 'Unknown')
                        lines.append(f"### \"{arg_text}\"")
                        lines.append(f"**Response**: {ca.get('response', '')}")
                        lines.append(f"**Disposition**: {ca.get('disposition', 'unresolved').title()}")
                        lines.append("")
            except (json.JSONDecodeError, TypeError):
                pass

        # Assumptions
        assumptions = trail.get("assumptions_made") or []
        if assumptions:
            lines.extend([
                "## Assumptions",
                "",
            ])
            for assumption in assumptions:
                lines.append(f"- {assumption}")
            lines.append("")
    else:
        lines.append("*No reasoning trail found for this claim.*")
        lines.append("")

    # Trail History
    history = get_reasoning_history(claim_id, db=db)
    if history:
        lines.extend([
            "## Trail History",
            "",
            "| Date | Credence | Evidence | Status | Pass |",
            "|------|----------|----------|--------|------|",
        ])
        for h in history:
            created = (h.get("created_at") or "")[:10]
            credence = h.get("credence_at_time")
            credence_str = f"{credence:.2f}" if credence is not None else "?"
            ev_level = h.get("evidence_level_at_time", "?")
            status = h.get("status", "?")
            analysis_pass = h.get("analysis_pass", "?")
            lines.append(f"| {created} | {credence_str} | {ev_level} | {status} | {analysis_pass} |")
        lines.append("")

    # Portable YAML block
    if trail:
        lines.extend([
            "## Data (portable)",
            "",
            "```yaml",
            f"claim_id: \"{claim_id}\"",
            f"reasoning_trail_id: \"{trail.get('id', 'N/A')}\"",
            f"credence_at_time: {trail.get('credence_at_time', 'null')}",
            f"evidence_level_at_time: \"{trail.get('evidence_level_at_time', 'N/A')}\"",
            f"supporting_evidence: {json.dumps(trail.get('supporting_evidence') or [])}",
            f"contradicting_evidence: {json.dumps(trail.get('contradicting_evidence') or [])}",
            "```",
            "",
        ])

    return "\n".join(lines)


def export_reasoning_all_md(db_path: Optional[Path] = None, output_dir: Optional[Path] = None) -> dict[str, str]:
    """Export reasoning trails for all claims with trails.

    Args:
        db_path: Path to LanceDB database
        output_dir: Output directory for generated files

    Returns:
        Dict mapping claim_id to markdown content
    """
    db = get_db(db_path)
    trails = list_reasoning_trails(include_superseded=False, limit=100000, db=db)

    # Get unique claim IDs that have trails
    claim_ids_with_trails = set(t.get("claim_id") for t in trails if t.get("claim_id"))

    results = {}
    for claim_id in sorted(claim_ids_with_trails):
        results[claim_id] = export_reasoning_md(claim_id, db_path, output_dir)

    return results


def export_evidence_by_claim_md(claim_id: str, db_path: Optional[Path] = None) -> str:
    """Export all evidence links for a specific claim."""
    db = get_db(db_path)
    claim = get_claim(claim_id, db)
    evidence_links = list_evidence_links(claim_id=claim_id, include_superseded=True, db=db)

    lines = [
        f"# Evidence: {claim_id}",
        "",
    ]

    if claim:
        lines.append(f"> {claim['text']}")
        lines.append("")

    if not evidence_links:
        lines.append("*No evidence links found for this claim.*")
        return "\n".join(lines)

    lines.extend([
        "| ID | Direction | Source | Location | Strength | Status |",
        "|----|-----------|--------|----------|----------|--------|",
    ])

    for link in evidence_links:
        link_id = link.get("id", "")
        direction = link.get("direction", "")
        source_id = link.get("source_id", "")
        location = link.get("location", "")
        strength = link.get("strength")
        strength_str = f"{strength:.2f}" if strength is not None else ""
        status = link.get("status", "active")
        lines.append(f"| {link_id} | {direction} | {source_id} | {location} | {strength_str} | {status} |")

    return "\n".join(lines)


def export_evidence_by_source_md(source_id: str, db_path: Optional[Path] = None) -> str:
    """Export all evidence links from a specific source."""
    db = get_db(db_path)
    source = get_source(source_id, db)
    evidence_links = list_evidence_links(source_id=source_id, include_superseded=True, db=db)

    lines = [
        f"# Evidence from: {source_id}",
        "",
    ]

    if source:
        lines.append(f"> {source.get('title', 'Unknown title')}")
        lines.append("")

    if not evidence_links:
        lines.append("*No evidence links found from this source.*")
        return "\n".join(lines)

    lines.extend([
        "| ID | Claim | Direction | Location | Strength | Status |",
        "|----|-------|-----------|----------|----------|--------|",
    ])

    for link in evidence_links:
        link_id = link.get("id", "")
        claim_id = link.get("claim_id", "")
        direction = link.get("direction", "")
        location = link.get("location", "")
        strength = link.get("strength")
        strength_str = f"{strength:.2f}" if strength is not None else ""
        status = link.get("status", "active")
        lines.append(f"| {link_id} | {claim_id} | {direction} | {location} | {strength_str} | {status} |")

    return "\n".join(lines)


def _clean_for_export(obj: Any) -> Any:
    """Clean an object for YAML/JSON export."""
    if hasattr(obj, 'tolist'):  # numpy array
        return obj.tolist()
    elif hasattr(obj, 'to_pylist'):  # pyarrow array
        return obj.to_pylist()
    elif isinstance(obj, (list, tuple)):
        return [_clean_for_export(v) for v in obj]
    elif isinstance(obj, dict):
        return {k: _clean_for_export(v) for k, v in obj.items()}
    elif hasattr(obj, 'as_py'):  # pyarrow scalar
        return obj.as_py()
    return obj


def export_provenance_yaml(db_path: Optional[Path] = None) -> str:
    """Export evidence_links and reasoning_trails as YAML.

    Output is deterministic (sorted by claim_id, then created_at, then id).
    """
    db = get_db(db_path)

    evidence_links = list_evidence_links(include_superseded=True, limit=100000, db=db)
    reasoning_trails = list_reasoning_trails(include_superseded=True, limit=100000, db=db)

    # Sort deterministically
    evidence_links_sorted = sorted(
        evidence_links,
        key=lambda x: (x.get("claim_id", ""), x.get("created_at", ""), x.get("id", ""))
    )
    reasoning_trails_sorted = sorted(
        reasoning_trails,
        key=lambda x: (x.get("claim_id", ""), x.get("created_at", ""), x.get("id", ""))
    )

    # Clean for export
    output = {
        "evidence_links": [_clean_for_export(e) for e in evidence_links_sorted],
        "reasoning_trails": [_clean_for_export(r) for r in reasoning_trails_sorted],
    }

    header = f"# Reality Check Provenance Export\n# Generated: {date.today().isoformat()}\n\n"
    return header + yaml.dump(output, default_flow_style=False, sort_keys=False, allow_unicode=True)


def export_provenance_json(db_path: Optional[Path] = None) -> str:
    """Export evidence_links and reasoning_trails as JSON.

    Output is deterministic (sorted by claim_id, then created_at, then id).
    """
    db = get_db(db_path)

    evidence_links = list_evidence_links(include_superseded=True, limit=100000, db=db)
    reasoning_trails = list_reasoning_trails(include_superseded=True, limit=100000, db=db)

    # Sort deterministically
    evidence_links_sorted = sorted(
        evidence_links,
        key=lambda x: (x.get("claim_id", ""), x.get("created_at", ""), x.get("id", ""))
    )
    reasoning_trails_sorted = sorted(
        reasoning_trails,
        key=lambda x: (x.get("claim_id", ""), x.get("created_at", ""), x.get("id", ""))
    )

    # Clean for export
    output = {
        "evidence_links": [_clean_for_export(e) for e in evidence_links_sorted],
        "reasoning_trails": [_clean_for_export(r) for r in reasoning_trails_sorted],
    }

    return json.dumps(output, indent=2, default=str)


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
        choices=["claims", "sources", "analysis-logs", "all"],
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
        choices=["claim", "chain", "predictions", "summary", "analysis-logs", "reasoning", "evidence-by-claim", "evidence-by-source"],
        help="What to export"
    )
    md_parser.add_argument(
        "--id",
        help="ID for claim/chain/reasoning/evidence export"
    )
    md_parser.add_argument(
        "--all",
        action="store_true",
        help="Export all (for reasoning type)"
    )
    md_parser.add_argument(
        "-o", "--output", "--output-dir",
        type=Path,
        dest="output",
        help="Output file or directory (default: stdout)"
    )

    # provenance command
    provenance_parser = subparsers.add_parser("provenance", help="Export provenance data (evidence links + reasoning trails)")
    provenance_parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)"
    )
    provenance_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)"
    )

    # stats command
    subparsers.add_parser("stats", help="Show database statistics")

    args = parser.parse_args()

    selected_db_path = args.db_path
    if args.command and selected_db_path is None and not os.getenv("REALITYCHECK_DATA"):
        default_db = Path("data/realitycheck.lance")
        if default_db.exists():
            selected_db_path = default_db
        else:
            project_root = find_project_root(Path.cwd())
            if project_root:
                detected = resolve_db_path_from_project_root(project_root)
                if detected.exists():
                    selected_db_path = detected

    if args.command and selected_db_path is None and not os.getenv("REALITYCHECK_DATA"):
        default_db = Path("data/realitycheck.lance")
        print(
            "Error: REALITYCHECK_DATA is not set and no database was found at "
            f"'{default_db}' (or via project auto-detect). Set REALITYCHECK_DATA or pass --db-path.",
            file=sys.stderr,
        )
        sys.exit(2)

    def output_result(content: str, output_path: Optional[Path]):
        if output_path:
            output_path.write_text(content)
            print(f"Exported to {output_path}")
        else:
            print(content)

    if args.command == "yaml":
        if args.type == "claims":
            content = export_claims_yaml(selected_db_path)
        elif args.type == "sources":
            content = export_sources_yaml(selected_db_path)
        elif args.type == "analysis-logs":
            content = export_analysis_logs_yaml(selected_db_path)
        else:  # all
            content = export_claims_yaml(selected_db_path) + "\n---\n\n" + export_sources_yaml(selected_db_path)
        output_result(content, args.output)

    elif args.command == "md":
        if args.type == "claim":
            if not args.id:
                print("Error: --id required for claim export", file=sys.stderr)
                sys.exit(1)
            content = export_claim_md(args.id, selected_db_path)
        elif args.type == "chain":
            if not args.id:
                print("Error: --id required for chain export", file=sys.stderr)
                sys.exit(1)
            content = export_chain_md(args.id, selected_db_path)
        elif args.type == "predictions":
            content = export_predictions_md(selected_db_path)
        elif args.type == "analysis-logs":
            content = export_analysis_logs_md(selected_db_path)
        elif args.type == "reasoning":
            if getattr(args, "all", False):
                # Export all reasoning trails
                results = export_reasoning_all_md(selected_db_path, args.output)
                if args.output:
                    args.output.mkdir(parents=True, exist_ok=True)
                    for claim_id, md_content in results.items():
                        out_file = args.output / f"{claim_id}.md"
                        out_file.write_text(md_content)
                    print(f"Exported {len(results)} reasoning files to {args.output}")
                else:
                    for claim_id, md_content in results.items():
                        print(md_content)
                        print("\n---\n")
                content = None  # Already handled
            else:
                if not args.id:
                    print("Error: --id required for reasoning export (or use --all)", file=sys.stderr)
                    sys.exit(1)
                content = export_reasoning_md(args.id, selected_db_path, args.output.parent if args.output else None)
        elif args.type == "evidence-by-claim":
            if not args.id:
                print("Error: --id required for evidence-by-claim export", file=sys.stderr)
                sys.exit(1)
            content = export_evidence_by_claim_md(args.id, selected_db_path)
        elif args.type == "evidence-by-source":
            if not args.id:
                print("Error: --id required for evidence-by-source export", file=sys.stderr)
                sys.exit(1)
            content = export_evidence_by_source_md(args.id, selected_db_path)
        else:  # summary
            content = export_summary_md(selected_db_path)

        if content is not None:  # Some exports handle their own output
            output_result(content, args.output)

    elif args.command == "provenance":
        if args.format == "json":
            content = export_provenance_json(selected_db_path)
        else:
            content = export_provenance_yaml(selected_db_path)
        output_result(content, args.output)

    elif args.command == "stats":
        stats = get_stats(get_db(selected_db_path))
        print("Database Statistics:")
        for table, count in stats.items():
            print(f"  {table}: {count}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
