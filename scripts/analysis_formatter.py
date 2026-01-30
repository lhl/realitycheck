#!/usr/bin/env python3
"""Format Reality Check analysis files to match the Output Contract.

This script inserts missing elements (legends, sections, tables) into analysis
markdown files. It's idempotent - safe to run multiple times.

Usage:
    python scripts/analysis_formatter.py analysis/sources/example.md
    python scripts/analysis_formatter.py --profile quick analysis/sources/example.md
    python scripts/analysis_formatter.py --dry-run analysis/sources/example.md

"""

import argparse
import re
import sys
from pathlib import Path

import yaml


# =============================================================================
# Claim ID Helpers
# =============================================================================

# Regex patterns for claim ID extraction
BARE_CLAIM_ID_RE = re.compile(r"^([A-Z]+-\d{4}-\d{3})$")
LINKED_CLAIM_ID_RE = re.compile(r"^\[([A-Z]+-\d{4}-\d{3})\]\(([^)]+)\)$")


def extract_claim_id(cell_text: str) -> str | None:
    """Extract a claim ID from table cell text.

    Handles both bare IDs and markdown-linked IDs:
    - "TECH-2026-001" -> "TECH-2026-001"
    - "[TECH-2026-001](../reasoning/TECH-2026-001.md)" -> "TECH-2026-001"

    Returns None if the text doesn't match either format.
    """
    text = cell_text.strip()

    # Try bare ID first
    bare_match = BARE_CLAIM_ID_RE.match(text)
    if bare_match:
        return bare_match.group(1)

    # Try linked ID
    linked_match = LINKED_CLAIM_ID_RE.match(text)
    if linked_match:
        return linked_match.group(1)

    return None


def is_linked_claim_id(cell_text: str) -> bool:
    """Check if cell text is a markdown-linked claim ID."""
    return bool(LINKED_CLAIM_ID_RE.match(cell_text.strip()))


# =============================================================================
# Template Snippets (from Jinja2 templates)
# =============================================================================

LEGENDS = """> **Claim types**: `[F]` fact, `[T]` theory, `[H]` hypothesis, `[P]` prediction, `[A]` assumption, `[C]` counterfactual, `[S]` speculation, `[X]` contradiction
> **Evidence**: **E1** systematic review/meta-analysis; **E2** peer-reviewed/official stats; **E3** expert consensus/preprint; **E4** credible journalism/industry; **E5** opinion/anecdote; **E6** unsupported/speculative
"""

KEY_CLAIMS_TABLE = """### Key Claims

| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | [claim text] | DOMAIN-YYYY-NNN | [F/T/H/P/A/C/S/X] | DOMAIN | E1-E6 | 0.00-1.00 | [source or ?] | [what would refute] |

"""

CLAIM_SUMMARY_TABLE = """### Claim Summary

| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| DOMAIN-YYYY-NNN | [F/T/H/P/A/C/S/X] | DOMAIN | E1-E6 | 0.00 | [claim text] |

"""

CLAIMS_YAML_BLOCK = """### Claims to Register

```yaml
claims:
  - id: "DOMAIN-YYYY-NNN"
    text: "[Precise claim statement]"
    type: "[F/T/H/P/A/C/S/X]"
    domain: "[DOMAIN]"
    evidence_level: "E[1-6]"
    credence: 0.XX
    source_ids: ["[source-id]"]
```

"""

CREDENCE_SECTION = """---

**Analysis Date**: [YYYY-MM-DD]
**Analyst**: [human/claude/gpt/etc.]
**Credence in Analysis**: [0.0-1.0]

**Credence Reasoning**:
- [Why this credence level?]
- [What would increase/decrease credence?]
- [Key uncertainties remaining]
"""

# Section templates for full profile
FULL_SECTIONS = {
    "## Stage 1: Descriptive Analysis": "\n## Stage 1: Descriptive Analysis\n",
    "### Core Thesis": "\n### Core Thesis\n\n[1-3 sentence summary of main argument]\n",
    "### Argument Structure": "\n### Argument Structure\n\n```\n[Premise 1]\n    +\n[Premise 2]\n    ↓\n[Conclusion]\n```\n",
    "### Theoretical Lineage": "\n### Theoretical Lineage\n\n- **Builds on**: [prior work/theories]\n- **Departs from**: [rejected approaches]\n- **Novel contribution**: [what's new here]\n",
    "## Stage 2: Evaluative Analysis": "\n## Stage 2: Evaluative Analysis\n",
    "### Key Factual Claims Verified": """\n### Key Factual Claims Verified

| Claim | Verification Source | Status | Notes | Crux? |
|-------|---------------------|--------|-------|-------|
| [claim] | [source] | ✓/✗/? | [notes] | Y/N |

""",
    "### Disconfirming Evidence Search": """\n### Disconfirming Evidence Search

| Claim | Counter-Evidence Sought | Found? | Impact |
|-------|------------------------|--------|--------|
| [claim] | [what would disprove] | Y/N | [if found, how does it affect credence?] |

""",
    "### Internal Tensions": """\n### Internal Tensions

| Tension | Claims Involved | Resolution Possible? |
|---------|-----------------|---------------------|
| [description] | [IDs] | [Y/N + how] |

""",
    "### Persuasion Techniques": """\n### Persuasion Techniques

| Technique | Example | Effect on Analysis |
|-----------|---------|-------------------|
| [e.g., appeal to authority] | [quote/reference] | [how to adjust for this] |

""",
    "### Unstated Assumptions": """\n### Unstated Assumptions

| Assumption | Required For | If False |
|------------|--------------|----------|
| [hidden premise] | [which claims depend on this] | [impact on argument] |

""",
    "## Stage 3: Dialectical Analysis": "\n## Stage 3: Dialectical Analysis\n",
    "### Steelmanned Argument": "\n### Steelmanned Argument\n\n[Strongest possible version of this position]\n",
    "### Strongest Counterarguments": "\n### Strongest Counterarguments\n\n1. [Counter + source if available]\n2. [Counter + source if available]\n",
    "### Supporting Theories": """\n### Supporting Theories

| Theory/Source | How It Supports | Claim IDs Affected |
|---------------|-----------------|-------------------|
| [theory] | [mechanism] | [IDs] |

""",
    "### Contradicting Theories": """\n### Contradicting Theories

| Theory/Source | How It Contradicts | Claim IDs Affected |
|---------------|-------------------|-------------------|
| [theory] | [mechanism] | [IDs] |

""",
}

# Section order for full profile (for proper insertion)
FULL_SECTION_ORDER = [
    "## Metadata",
    "## Stage 1: Descriptive Analysis",
    "### Core Thesis",
    "### Key Claims",
    "### Argument Structure",
    "### Theoretical Lineage",
    "## Stage 2: Evaluative Analysis",
    "### Key Factual Claims Verified",
    "### Disconfirming Evidence Search",
    "### Internal Tensions",
    "### Persuasion Techniques",
    "### Unstated Assumptions",
    "## Stage 3: Dialectical Analysis",
    "### Steelmanned Argument",
    "### Strongest Counterarguments",
    "### Supporting Theories",
    "### Contradicting Theories",
    "### Claim Summary",
    "### Claims to Register",
]

QUICK_SECTION_ORDER = [
    "## Metadata",
    "## Summary",
    "### Claim Summary",
    "### Claims to Register",
]

LEGACY_HEADING_REWRITES: list[tuple[re.Pattern[str], str]] = [
    # Stage headings (legacy variants)
    (re.compile(r"^##\s*Stage\s*1:\s*Descriptive\s*Summary\s*$", re.IGNORECASE | re.MULTILINE),
     "## Stage 1: Descriptive Analysis"),
    (re.compile(r"^##\s*Stage\s*2:\s*Evaluation(?:\s*Analysis)?\s*$", re.IGNORECASE | re.MULTILINE),
     "## Stage 2: Evaluative Analysis"),
    (re.compile(r"^##\s*Stage\s*2:\s*Evaluative\s*$", re.IGNORECASE | re.MULTILINE),
     "## Stage 2: Evaluative Analysis"),
    (re.compile(r"^##\s*Stage\s*3:\s*Dialectical\s*Synthesis\s*$", re.IGNORECASE | re.MULTILINE),
     "## Stage 3: Dialectical Analysis"),
    # Common subsection aliases
    (re.compile(r"^###\s*Steelman\s*$", re.IGNORECASE | re.MULTILINE),
     "### Steelmanned Argument"),
    (re.compile(r"^###\s*Counterarguments\s*$", re.IGNORECASE | re.MULTILINE),
     "### Strongest Counterarguments"),
    # Claim summary sometimes appears as a level-2 heading in legacy analyses
    (re.compile(r"^##\s*Claim\s+Summary\b.*$", re.IGNORECASE | re.MULTILINE),
     "### Claim Summary"),
]


def detect_profile(content: str) -> str:
    """Detect the analysis profile from the content."""
    if re.search(r"\*\*Analysis Depth\*\*.*quick", content, re.IGNORECASE):
        return "quick"
    return "full"


def has_legends(content: str) -> bool:
    """Check if the content has the legends block."""
    return bool(re.search(r">\s*\*\*Claim types\*\*:", content))


def has_section(content: str, section: str) -> bool:
    """Check if a section header exists."""
    pattern = re.escape(section)
    return bool(re.search(pattern, content, re.IGNORECASE))


def has_claims_yaml(content: str) -> bool:
    """Check if the claims YAML block exists."""
    return bool(re.search(r"```yaml\s*\nclaims:", content))


def has_credence(content: str) -> bool:
    """Check if the credence score exists."""
    # Support both old "Confidence" and new "Credence" terminology
    return bool(re.search(r"\*\*(Confidence|Credence) in Analysis\*\*:", content))


def normalize_legacy_headings(content: str) -> tuple[str, list[str]]:
    """Normalize common legacy headings to match the Output Contract.

    Returns:
        Tuple of (updated_content, list_of_changes_made)
    """
    changes: list[str] = []
    updated = content
    for pattern, replacement in LEGACY_HEADING_REWRITES:
        if pattern.search(updated):
            updated = pattern.sub(replacement, updated)
            changes.append(f"Normalized heading to: {replacement}")
    return updated, changes


def _split_md_table_row(line: str) -> list[str]:
    """Split a Markdown table row into cells (best-effort)."""
    if not line.strip().startswith("|"):
        return []
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    return parts


def _is_table_separator_row(cells: list[str]) -> bool:
    """Heuristic: markdown separator row is mostly dashes/colons."""
    if not cells:
        return False
    for cell in cells:
        stripped = cell.replace(":", "").replace("-", "").strip()
        if stripped:
            return False
    return True


def extract_claims_from_key_claims_table(content: str) -> list[dict]:
    """Extract claim records from the first 'Key Claims' table found in the content.

    Returns a list of dicts with keys: id, text, type, domain, evidence_level, credence.
    """
    lines = content.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if re.search(r"^\|\s*#\s*\|.*\|\s*Claim\s+ID\s*\|", line, re.IGNORECASE):
            header_idx = i
            break
    if header_idx is None or header_idx + 2 >= len(lines):
        return []

    header_cells = _split_md_table_row(lines[header_idx])
    sep_cells = _split_md_table_row(lines[header_idx + 1])
    if not _is_table_separator_row(sep_cells):
        return []

    def norm(name: str) -> str:
        return re.sub(r"\s+", " ", name.strip().lower())

    col_map = {norm(name): idx for idx, name in enumerate(header_cells)}
    claim_idx = col_map.get("claim")
    claim_id_idx = col_map.get("claim id")
    type_idx = col_map.get("type")
    domain_idx = col_map.get("domain")
    evidence_idx = col_map.get("evid", col_map.get("evidence"))
    credence_idx = col_map.get("credence", col_map.get("conf"))

    if claim_idx is None or claim_id_idx is None or type_idx is None or domain_idx is None:
        return []

    extracted: list[dict] = []
    for line in lines[header_idx + 2:]:
        if not line.strip().startswith("|"):
            break
        row_cells = _split_md_table_row(line)
        if not row_cells or len(row_cells) < len(header_cells):
            continue

        claim_id_cell = row_cells[claim_id_idx].strip()
        # Extract bare ID from linked or bare format
        claim_id = extract_claim_id(claim_id_cell)
        if not claim_id:
            continue

        claim_text = row_cells[claim_idx].strip()
        claim_type = row_cells[type_idx].strip()
        domain = row_cells[domain_idx].strip()
        evidence_level = row_cells[evidence_idx].strip() if evidence_idx is not None else ""
        credence_raw = row_cells[credence_idx].strip() if credence_idx is not None else ""

        credence: float | None = None
        try:
            credence = float(credence_raw)
        except Exception:
            credence = None

        claim_record: dict = {
            "id": claim_id,
            "text": claim_text,
            "type": claim_type,
            "domain": domain,
            "evidence_level": evidence_level,
            "credence": credence,
        }
        # Preserve linked format if present
        if is_linked_claim_id(claim_id_cell):
            claim_record["id_display"] = claim_id_cell

        extracted.append(claim_record)

    return extracted


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def build_claim_summary_table(claims: list[dict]) -> str:
    """Build a Claim Summary table.

    Falls back to placeholder if claims is empty.
    Preserves linked claim IDs if present in id_display field.
    """
    if not claims:
        return CLAIM_SUMMARY_TABLE

    lines = [
        "| ID | Type | Domain | Evidence | Credence | Claim |",
        "|----|------|--------|----------|----------:|-------|",
    ]
    for claim in claims:
        # Use id_display (linked format) if present, otherwise bare id
        claim_id = str(claim.get("id_display", claim.get("id", ""))).strip()
        claim_type = str(claim.get("type", "")).strip()
        domain = str(claim.get("domain", "")).strip()
        evidence = str(claim.get("evidence_level", "")).strip()
        credence_val = claim.get("credence", None)
        credence = f"{credence_val:.2f}" if isinstance(credence_val, (int, float)) else ""
        text = _collapse_ws(str(claim.get("text", "")).strip()).replace("|", "\\|")
        lines.append(f"| {claim_id} | {claim_type} | {domain} | {evidence} | {credence} | {text} |")

    return "### Claim Summary\n\n" + "\n".join(lines) + "\n\n"


def _extract_claims_block_from_yaml_file(yaml_path: Path) -> str | None:
    """Extract the top-level 'claims:' block from a YAML file, if present."""
    try:
        text = yaml_path.read_text()
    except Exception:
        return None

    match = re.search(r"^claims:\s*$", text, re.MULTILINE)
    if not match:
        return None
    return text[match.start():].rstrip() + "\n"


def derive_claims(path: Path, content: str) -> tuple[list[dict], str | None]:
    """Derive claim records and (optionally) a YAML claims block for embedding.

    Returns:
        (claims_list, yaml_claims_block_or_none)
    """
    yaml_path = path.with_suffix(".yaml")
    yaml_block = _extract_claims_block_from_yaml_file(yaml_path) if yaml_path.exists() else None

    if yaml_block:
        try:
            parsed = yaml.safe_load(yaml_block) or {}
            claims = parsed.get("claims") or []
            if isinstance(claims, list):
                normalized: list[dict] = []
                for item in claims:
                    if not isinstance(item, dict):
                        continue
                    normalized.append(
                        {
                            "id": item.get("id"),
                            "text": _collapse_ws(str(item.get("text", ""))),
                            "type": item.get("type"),
                            "domain": item.get("domain"),
                            "evidence_level": item.get("evidence_level"),
                            "credence": item.get("credence"),
                        }
                    )
                return normalized, yaml_block
        except Exception:
            # Fall through to key-claims parsing
            pass

    return extract_claims_from_key_claims_table(content), None


def build_claims_yaml_block(claims: list[dict], source_id: str) -> str:
    """Build a minimal claims YAML block for embedding (used when no sibling YAML exists)."""
    if not claims:
        return CLAIMS_YAML_BLOCK

    payload: dict = {"claims": []}
    for claim in claims:
        claim_id = str(claim.get("id", "")).strip()
        claim_text = _collapse_ws(str(claim.get("text", "")).strip())
        payload["claims"].append(
            {
                "id": claim_id,
                "text": claim_text,
                "type": str(claim.get("type", "")).strip(),
                "domain": str(claim.get("domain", "")).strip(),
                "evidence_level": str(claim.get("evidence_level", "")).strip(),
                "credence": claim.get("credence"),
                "source_ids": [source_id],
            }
        )

    yaml_text = yaml.safe_dump(
        payload,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=88,
        indent=2,
    )
    return "### Claims to Register\n\n```yaml\n" + yaml_text.rstrip() + "\n```\n\n"


def find_section_position(content: str, section: str, section_order: list[str]) -> int:
    """Find the position where a section should be inserted.

    Returns the character position where the section should be inserted,
    based on the order of sections in section_order.
    """
    section_idx = section_order.index(section) if section in section_order else -1
    if section_idx == -1:
        return len(content)

    # Find the next existing section after this one
    for next_section in section_order[section_idx + 1:]:
        match = re.search(re.escape(next_section), content, re.IGNORECASE)
        if match:
            # Insert before the next section (find the start of its line)
            pos = match.start()
            # Walk back to find the start of the line
            while pos > 0 and content[pos - 1] != '\n':
                pos -= 1
            # Include preceding newlines/separators
            if pos > 0 and content[pos - 1] == '\n':
                pos -= 1
            return pos

    # If no next section found, find the previous section and insert after it
    for prev_section in reversed(section_order[:section_idx]):
        match = re.search(re.escape(prev_section), content, re.IGNORECASE)
        if match:
            # Find the end of this section (next ## or ### or end of file)
            section_start = match.end()
            next_header = re.search(r'\n##', content[section_start:])
            if next_header:
                return section_start + next_header.start()
            return len(content)

    return len(content)


def insert_legends(content: str) -> str:
    """Insert legends block after the title."""
    if has_legends(content):
        return content

    # Find the first # heading (title)
    match = re.search(r'^# .+\n', content, re.MULTILINE)
    if match:
        insert_pos = match.end()
        return content[:insert_pos] + "\n" + LEGENDS + "\n" + content[insert_pos:]

    # No title found, prepend
    return LEGENDS + "\n" + content


def insert_key_claims_table(content: str) -> str:
    """Insert Key Claims table if missing (full profile only)."""
    if re.search(r"\|\s*#\s*\|.*Claim.*\|.*Claim ID.*\|.*Type.*\|.*Domain.*\|", content, re.IGNORECASE):
        return content

    # Insert after ### Key Claims header, or create the section
    if has_section(content, "### Key Claims"):
        # Find the header and insert table after it
        match = re.search(r"### Key Claims\s*\n", content, re.IGNORECASE)
        if match:
            insert_pos = match.end()
            # Check if there's already content (skip if so, but allow insertion before next section)
            remaining = content[insert_pos:insert_pos + 50]
            remaining_stripped = remaining.strip()
            is_placeholder = remaining_stripped.startswith('[TODO')
            is_section = remaining_stripped.startswith('#')
            is_table = remaining_stripped.startswith('|')
            if remaining_stripped and not is_placeholder and not is_section and not is_table:
                return content
            # Remove TODO placeholder if present
            if is_placeholder:
                todo_end = content.find('\n', insert_pos)
                if todo_end != -1:
                    content = content[:insert_pos] + content[todo_end + 1:]
                    match = re.search(r"### Key Claims\s*\n", content, re.IGNORECASE)
                    if match:
                        insert_pos = match.end()
            table_content = """
| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | [claim text] | DOMAIN-YYYY-NNN | [F/T/H/P/A/C/S/X] | DOMAIN | E1-E6 | 0.00-1.00 | [source or ?] | [what would refute] |

"""
            return content[:insert_pos] + table_content + content[insert_pos:]

    # Need to create the section - find position
    pos = find_section_position(content, "### Key Claims", FULL_SECTION_ORDER)
    return content[:pos] + "\n" + KEY_CLAIMS_TABLE + content[pos:]


def insert_claim_summary_table(content: str, claims: list[dict] | None = None) -> str:
    """Insert Claim Summary table if missing."""
    if re.search(r"\|\s*ID\s*\|.*Type.*\|.*Domain.*\|.*Evidence.*\|.*Credence.*\|", content, re.IGNORECASE):
        return content

    # Insert after ### Claim Summary header, or create the section
    if has_section(content, "### Claim Summary"):
        match = re.search(r"### Claim Summary\s*\n", content, re.IGNORECASE)
        if match:
            insert_pos = match.end()
            remaining = content[insert_pos:insert_pos + 50]
            # Only skip if there's real content (not section header, table, or TODO placeholder)
            remaining_stripped = remaining.strip()
            is_placeholder = remaining_stripped.startswith('[TODO')
            is_section = remaining_stripped.startswith('#')
            is_table = remaining_stripped.startswith('|')
            if remaining_stripped and not is_placeholder and not is_section and not is_table:
                return content
            # Remove TODO placeholder if present
            if is_placeholder:
                todo_end = content.find('\n', insert_pos)
                if todo_end != -1:
                    content = content[:insert_pos] + content[todo_end + 1:]
                    # Recompute insert position after modifying content
                    match = re.search(r"### Claim Summary\s*\n", content, re.IGNORECASE)
                    if match:
                        insert_pos = match.end()
            table_content = "\n" + build_claim_summary_table(claims or []).replace("### Claim Summary\n\n", "", 1)
            return content[:insert_pos] + table_content + content[insert_pos:]

    # Need to create the section
    profile = detect_profile(content)
    section_order = QUICK_SECTION_ORDER if profile == "quick" else FULL_SECTION_ORDER
    pos = find_section_position(content, "### Claim Summary", section_order)
    return content[:pos] + "\n" + build_claim_summary_table(claims or []) + content[pos:]


def insert_claims_yaml(
    content: str,
    claims_yaml: str | None = None,
    claims: list[dict] | None = None,
    source_id: str | None = None,
) -> str:
    """Insert Claims YAML block if missing."""
    if has_claims_yaml(content):
        return content

    yaml_body = claims_yaml
    if yaml_body is None:
        yaml_body = build_claims_yaml_block(claims or [], source_id or "[source-id]").split("```yaml\n", 1)[-1].rsplit("\n```", 1)[0] + "\n"

    if has_section(content, "### Claims to Register"):
        match = re.search(r"### Claims to Register\s*\n", content, re.IGNORECASE)
        if match:
            insert_pos = match.end()
            yaml_content = "\n```yaml\n" + yaml_body.rstrip() + "\n```\n\n"
            return content[:insert_pos] + yaml_content + content[insert_pos:]

    # Need to create the section - append at end before confidence
    profile = detect_profile(content)
    section_order = QUICK_SECTION_ORDER if profile == "quick" else FULL_SECTION_ORDER
    pos = find_section_position(content, "### Claims to Register", section_order)
    block = "### Claims to Register\n\n```yaml\n" + yaml_body.rstrip() + "\n```\n\n"
    return content[:pos] + "\n" + block + content[pos:]


def insert_confidence(content: str) -> str:
    """Insert confidence section if missing (full profile only)."""
    if has_credence(content):
        return content

    # Append at the end
    if not content.endswith('\n'):
        content += '\n'
    return content + CREDENCE_SECTION


def insert_missing_sections(content: str, profile: str) -> str:
    """Insert any missing required sections."""
    if profile == "quick":
        required = ["## Metadata", "## Summary", "### Claim Summary", "### Claims to Register"]
        section_order = QUICK_SECTION_ORDER
    else:
        required = FULL_SECTION_ORDER
        section_order = FULL_SECTION_ORDER

    for section in required:
        if not has_section(content, section):
            if section in FULL_SECTIONS:
                template = FULL_SECTIONS[section]
            elif section == "## Metadata":
                template = "\n## Metadata\n\n| Field | Value |\n|-------|-------|\n| **Source ID** | [id] |\n| **Title** | [title] |\n\n"
            elif section == "## Summary":
                template = "\n## Summary\n\n[Brief summary of the source]\n"
            elif section in {"### Key Claims", "### Claim Summary", "### Claims to Register"}:
                template = f"\n{section}\n\n"
            else:
                template = f"\n{section}\n\n[TODO: Complete this section]\n"

            pos = find_section_position(content, section, section_order)
            content = content[:pos] + template + content[pos:]

    return content


def format_file(path: Path, profile: str | None = None, dry_run: bool = False) -> tuple[str, list[str]]:
    """Format a single analysis file.

    Returns:
        Tuple of (formatted_content, list_of_changes_made)
    """
    changes = []

    try:
        content = path.read_text()
    except Exception as e:
        return "", [f"Error reading file: {e}"]

    original = content

    # Step 0: Normalize legacy headings to reduce duplication and meet the contract.
    content, normalized_changes = normalize_legacy_headings(content)
    changes.extend(normalized_changes)

    # Detect or use specified profile
    detected_profile = detect_profile(content)
    actual_profile = profile or detected_profile
    source_id = path.stem
    derived_claims, claims_yaml = derive_claims(path, content)

    # Step 1: Insert legends if missing
    if not has_legends(content):
        content = insert_legends(content)
        changes.append("Added claim types and evidence legends")

    # Step 2: Insert missing sections based on profile
    sections_needed = QUICK_SECTION_ORDER if actual_profile == "quick" else FULL_SECTION_ORDER
    missing_sections = [s for s in sections_needed if not has_section(content, s)]
    if missing_sections:
        content = insert_missing_sections(content, actual_profile)
        for section in missing_sections:
            if has_section(content, section):
                changes.append(f"Added missing section: {section}")

    # Step 3: Insert Key Claims table (full profile only)
    if actual_profile == "full":
        if not re.search(r"\|\s*#\s*\|.*Claim.*\|.*Claim ID.*\|", content, re.IGNORECASE):
            content = insert_key_claims_table(content)
            changes.append("Added Key Claims table")

    # Step 4: Insert Claim Summary table
    if not re.search(r"\|\s*ID\s*\|.*Type.*\|.*Domain.*\|.*Evidence.*\|.*Credence.*\|", content, re.IGNORECASE):
        content = insert_claim_summary_table(content, derived_claims)
        changes.append("Added Claim Summary table")

    # Step 5: Insert Claims YAML block
    if not has_claims_yaml(content):
        content = insert_claims_yaml(content, claims_yaml=claims_yaml, claims=derived_claims, source_id=source_id)
        changes.append("Added Claims YAML block")

    # Step 6: Insert confidence section (full profile only)
    if actual_profile == "full" and not has_credence(content):
        content = insert_confidence(content)
        changes.append("Added Credence in Analysis section")

    # Clean up multiple consecutive blank lines
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    if content != original and not dry_run:
        path.write_text(content)

    return content, changes


def main():
    parser = argparse.ArgumentParser(
        description="Format Reality Check analysis files to match Output Contract"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Analysis file(s) to format",
    )
    parser.add_argument(
        "--profile",
        choices=["full", "quick"],
        help="Force a specific profile (default: auto-detect)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output errors",
    )
    args = parser.parse_args()

    exit_code = 0

    for file_path in args.files:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            exit_code = 1
            continue

        _, changes = format_file(file_path, args.profile, args.dry_run)

        if changes:
            if not args.quiet:
                action = "Would change" if args.dry_run else "Formatted"
                print(f"\n{action}: {file_path}")
                for change in changes:
                    print(f"  + {change}")
        elif not args.quiet:
            print(f"\n{file_path}: No changes needed")

    if not args.quiet:
        mode = " (dry run)" if args.dry_run else ""
        print(f"\nDone{mode}.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
