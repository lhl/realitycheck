#!/usr/bin/env python3
"""Validate Reality Check analysis files against the Output Contract.

This script checks that analysis markdown files contain all required elements
based on their analysis depth profile (full or quick).

Usage:
    python scripts/analysis_validator.py analysis/sources/example.md
    python scripts/analysis_validator.py analysis/sources/*.md
    python scripts/analysis_validator.py --profile quick analysis/sources/example.md
    python scripts/analysis_validator.py --strict analysis/sources/example.md
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple


class ValidationResult(NamedTuple):
    """Result of validating a single file."""
    path: Path
    profile: str
    errors: list[str]
    warnings: list[str]


# Regex patterns for claim ID extraction
BARE_CLAIM_ID_RE = re.compile(r"^([A-Z]+-\d{4}-\d{3})$")
LINKED_CLAIM_ID_RE = re.compile(r"^\[([A-Z]+-\d{4}-\d{3})\]\([^)]+\)$")
MARKDOWN_WRAPPER_MARKERS = ("**", "__", "`", "*", "_")

# Stage 2 factual verification status allowlist (v0.3.2)
VALID_STAGE2_STATUSES = {"ok", "x", "nf", "blocked", "?"}


def _strip_simple_markdown_wrappers(text: str) -> str:
    """Strip simple markdown wrappers around a whole cell value.

    Handles common wrappers used in markdown tables such as:
    - `TECH-2026-001`
    - **TECH-2026-001**
    - *TECH-2026-001*
    """
    cleaned = text.strip()
    while cleaned:
        updated = False
        for marker in MARKDOWN_WRAPPER_MARKERS:
            marker_len = len(marker)
            if (
                cleaned.startswith(marker)
                and cleaned.endswith(marker)
                and len(cleaned) > marker_len * 2
            ):
                cleaned = cleaned[marker_len:-marker_len].strip()
                updated = True
                break
        if not updated:
            break
    return cleaned


def extract_claim_id(cell_text: str) -> str | None:
    """Extract a claim ID from table cell text.

    Handles both bare IDs and markdown-linked IDs:
    - "TECH-2026-001" -> "TECH-2026-001"
    - "[TECH-2026-001](../reasoning/TECH-2026-001.md)" -> "TECH-2026-001"

    Returns None if the text doesn't match either format.
    """
    text = _strip_simple_markdown_wrappers(cell_text)

    # Try bare ID first
    bare_match = BARE_CLAIM_ID_RE.match(text)
    if bare_match:
        return bare_match.group(1)

    # Try linked ID
    linked_match = LINKED_CLAIM_ID_RE.match(text)
    if linked_match:
        return linked_match.group(1)

    return None


# Valid Layer enum values (strict enforcement in rigor mode)
VALID_LAYER_VALUES = {"ASSERTED", "LAWFUL", "PRACTICED", "EFFECT"}

# Required elements for full analysis profile
FULL_PROFILE_REQUIRED = {
    "sections": [
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
    ],
    "tables": [
        # Key Claims table with required columns
        (r"\|\s*#\s*\|.*Claim.*\|.*Claim ID.*\|.*Type.*\|.*Domain.*\|", "Key Claims table"),
        # Claim Summary table
        (r"\|\s*ID\s*\|.*Type.*\|.*Domain.*\|.*Evidence.*\|.*Credence.*\|", "Claim Summary table"),
    ],
    "elements": [
        # Legends (claim types + evidence)
        (r">\s*\*\*Claim types\*\*:", "Claim types legend"),
        (r">\s*\*\*Evidence\*\*:", "Evidence legend"),
        # Claims YAML block
        (r"```yaml\s*\nclaims:", "Claims YAML block"),
        # Credence in Analysis (also accept legacy "Confidence")
        (r"\*\*(Credence|Confidence) in Analysis\*\*:", "Credence in Analysis score"),
    ],
}

# Rigor-v1 additional requirements (WARN by default, ERROR with --rigor)
RIGOR_V1_REQUIRED = {
    "sections": [
        "### Corrections & Updates",
    ],
    "rigor_columns": {
        # Check that claim tables have Layer/Actor/Scope/Quantifier columns
        "key_claims": (r"\|\s*#\s*\|.*\|.*Layer.*\|.*Actor.*\|.*Scope.*\|.*Quantifier.*\|", "Key Claims table rigor columns"),
        "claim_summary": (r"\|\s*ID\s*\|.*\|.*Layer.*\|.*Actor.*\|.*Scope.*\|.*Quantifier.*\|", "Claim Summary table rigor columns"),
    },
}

# Required elements for quick analysis profile
QUICK_PROFILE_REQUIRED = {
    "sections": [
        "## Metadata",
        "## Summary",
        "### Claim Summary",
        "### Claims to Register",
    ],
    "tables": [
        # Claim Summary table
        (r"\|\s*ID\s*\|.*Type.*\|.*Domain.*\|.*Evidence.*\|.*Credence.*\|", "Claim Summary table"),
    ],
    "elements": [
        # Legends (claim types + evidence)
        (r">\s*\*\*Claim types\*\*:", "Claim types legend"),
        (r">\s*\*\*Evidence\*\*:", "Evidence legend"),
        # Claims YAML block
        (r"```yaml\s*\nclaims:", "Claims YAML block"),
        # Analysis Depth marker
        (r"\*\*Analysis Depth\*\*.*quick", "Analysis Depth: quick marker"),
    ],
}

# Framework repo indicators (should NOT be writing here)
FRAMEWORK_INDICATORS = [
    "scripts/",
    "tests/",
    "integrations/",
    "methodology/",
]


def detect_profile(content: str) -> str:
    """Detect the analysis profile from the content."""
    if re.search(r"\*\*Analysis Depth\*\*.*quick", content, re.IGNORECASE):
        return "quick"
    return "full"


def has_section(content: str, section: str) -> bool:
    """Check if a section header exists (case-insensitive)."""
    pattern = re.escape(section)
    return bool(re.search(pattern, content, re.IGNORECASE))


def check_framework_repo(path: Path) -> list[str]:
    """Check if the path appears to be in the framework repo (wrong place)."""
    warnings = []
    path_str = str(path.resolve())

    for indicator in FRAMEWORK_INDICATORS:
        # Check if any parent directory contains framework indicators
        if f"/{indicator}" in path_str and "/analysis/" not in path_str:
            warnings.append(
                f"Path may be in framework repo (contains '{indicator}'). "
                "Analysis files should be in the DATA repository."
            )
            break

    return warnings


def validate_sections(content: str, required_sections: list[str]) -> list[str]:
    """Check that all required sections are present."""
    errors = []
    for section in required_sections:
        # Escape special regex characters in section header
        pattern = re.escape(section)
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Missing section: {section}")
    return errors


def validate_tables(content: str, required_tables: list[tuple[str, str]]) -> list[str]:
    """Check that all required tables are present with correct columns."""
    errors = []
    for pattern, name in required_tables:
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Missing or malformed: {name}")
    return errors


def validate_elements(content: str, required_elements: list[tuple[str, str]]) -> list[str]:
    """Check that all required elements are present."""
    errors = []
    for pattern, name in required_elements:
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Missing: {name}")
    return errors


def validate_claim_ids(content: str) -> list[str]:
    """Check that claim IDs follow the correct format.

    Recognizes both bare IDs (TECH-2026-001) and markdown-linked IDs
    ([TECH-2026-001](path)).
    """
    warnings = []

    # Find claim IDs in tables and YAML - matches both bare and linked formats
    # This pattern captures the ID portion whether bare or in a markdown link
    claim_id_pattern = r"([A-Z]+)-(\d{4})-(\d{3})"
    matches = re.findall(claim_id_pattern, content)

    if not matches:
        warnings.append("No claim IDs found matching DOMAIN-YYYY-NNN format")

    # Check for placeholder IDs (both bare and linked formats)
    if re.search(r"DOMAIN-YYYY-NNN", content):
        warnings.append("Contains placeholder claim ID (DOMAIN-YYYY-NNN) - replace with actual ID")

    return warnings


def validate_rigor_sections(content: str) -> list[str]:
    """Check for rigor-v1 required sections (returns warnings, not errors)."""
    warnings = []
    for section in RIGOR_V1_REQUIRED["sections"]:
        if not has_section(content, section):
            warnings.append(f"Missing rigor-v1 section: {section}")
    return warnings


def validate_rigor_columns(content: str) -> list[str]:
    """Check that claim tables have rigor-v1 columns (Layer/Actor/Scope/Quantifier)."""
    warnings = []

    # Only check if tables exist at all
    for table_name, (pattern, description) in RIGOR_V1_REQUIRED["rigor_columns"].items():
        # Check if the table exists with basic pattern first
        basic_pattern = r"\|\s*#\s*\|" if table_name == "key_claims" else r"\|\s*ID\s*\|"
        if re.search(basic_pattern, content, re.IGNORECASE):
            # Table exists, check for rigor columns
            if not re.search(pattern, content, re.IGNORECASE):
                warnings.append(f"Missing {description} (Layer/Actor/Scope/Quantifier)")

    return warnings


def validate_layer_values(content: str) -> list[str]:
    """Check that Layer column values are valid (ASSERTED/LAWFUL/PRACTICED/EFFECT)."""
    warnings = []

    # Find Layer values in tables
    # Look for table rows that might have a Layer column
    # We look for patterns like: | ... | SOMETHING | ... | where SOMETHING might be a layer value
    layer_pattern = re.compile(
        r"\|\s*Layer\s*\|",
        re.IGNORECASE
    )

    if not layer_pattern.search(content):
        # No Layer column found, skip validation
        return warnings

    # Extract potential layer values from table rows
    # Look for cells that contain values that look like they might be layer values
    lines = content.split('\n')
    in_table = False
    layer_col_idx = None

    for line in lines:
        if not line.strip().startswith('|'):
            in_table = False
            layer_col_idx = None
            continue

        cells = [c.strip() for c in line.split('|')]
        if not cells:
            continue

        # Check if this is a header row with Layer column
        for idx, cell in enumerate(cells):
            if cell.lower() == 'layer':
                in_table = True
                layer_col_idx = idx
                break

        # If we're in a table with a Layer column, check the value
        if in_table and layer_col_idx is not None and layer_col_idx < len(cells):
            cell_value = cells[layer_col_idx].strip()
            # Skip header row and separator row
            if cell_value.lower() == 'layer' or cell_value.startswith('-') or not cell_value:
                continue
            # Check if value is valid
            if cell_value not in VALID_LAYER_VALUES and cell_value != 'N/A':
                # Allow placeholder values in templates
                if 'ASSERTED/LAWFUL/PRACTICED/EFFECT' not in cell_value:
                    warnings.append(f"Invalid Layer value '{cell_value}' - must be ASSERTED/LAWFUL/PRACTICED/EFFECT")

    return warnings


def _split_md_table_row(line: str) -> list[str]:
    """Split a markdown table row into cells."""
    if not line.strip().startswith("|"):
        return []
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_table_separator_row(cells: list[str]) -> bool:
    """Check whether cells represent a markdown separator row."""
    if not cells:
        return False
    for cell in cells:
        stripped = cell.replace(":", "").replace("-", "").strip()
        if stripped:
            return False
    return True


def _extract_section_content(content: str, section_header: str) -> str:
    """Extract a section body from a markdown document."""
    section_pattern = re.compile(rf"^\s*{re.escape(section_header)}\s*$", re.IGNORECASE | re.MULTILINE)
    section_match = section_pattern.search(content)
    if not section_match:
        return ""

    start = section_match.end()
    remainder = content[start:]
    next_heading = re.search(r"^\s*#{2,6}\s+", remainder, re.MULTILINE)
    if next_heading:
        end = start + next_heading.start()
    else:
        end = len(content)
    return content[start:end]


def _parse_first_markdown_table(section_content: str) -> tuple[list[str], list[list[str]]]:
    """Parse the first markdown table found inside a section body."""
    lines = section_content.splitlines()
    for index in range(len(lines) - 1):
        header_cells = _split_md_table_row(lines[index])
        if not header_cells:
            continue

        separator_cells = _split_md_table_row(lines[index + 1])
        if not _is_table_separator_row(separator_cells):
            continue

        rows: list[list[str]] = []
        row_index = index + 2
        while row_index < len(lines):
            row_cells = _split_md_table_row(lines[row_index])
            if not row_cells:
                break
            if not _is_table_separator_row(row_cells):
                rows.append(row_cells)
            row_index += 1
        return header_cells, rows

    return [], []


def _normalize_column_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _find_column_index(column_map: dict[str, int], *candidates: str) -> int | None:
    for candidate in candidates:
        if candidate in column_map:
            return column_map[candidate]
    return None


def _normalize_status(status: str) -> str:
    cleaned = _strip_simple_markdown_wrappers(status)
    cleaned = re.sub(r"[`*]", "", cleaned).strip().lower()
    if cleaned.startswith("[") and cleaned.endswith("]") and len(cleaned) >= 3:
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _is_crux_value(value: str) -> bool:
    cleaned = re.sub(r"[`*\s]", "", value).upper()
    return cleaned == "Y"


def _normalize_claim_type(claim_type: str) -> str:
    """Normalize claim type values for robust comparisons."""
    cleaned = _strip_simple_markdown_wrappers(claim_type)
    cleaned = re.sub(r"\s+", "", cleaned).upper()
    if cleaned.startswith("[") and cleaned.endswith("]") and len(cleaned) >= 3:
        cleaned = cleaned[1:-1]
    return cleaned


def _is_reviewed_analysis(content: str) -> bool:
    """Detect whether an analysis metadata marks rigor level REVIEWED."""
    metadata_content = _extract_section_content(content, "## Metadata")
    search_space = metadata_content if metadata_content else content

    reviewed_patterns = [
        r"\|\s*\*{0,2}Rigor Level\*{0,2}\s*\|\s*\[?REVIEWED\]?\s*\|",
        r"\*{0,2}Rigor Level\*{0,2}\s*:\s*\[?REVIEWED\]?",
    ]
    return any(re.search(pattern, search_space, re.IGNORECASE) for pattern in reviewed_patterns)


def _extract_stage2_factual_rows(content: str) -> tuple[list[dict[str, str]], list[str]]:
    """Extract rows from the Stage 2 factual verification table."""
    warnings: list[str] = []
    section_content = _extract_section_content(content, "### Key Factual Claims Verified")
    if not section_content:
        return [], warnings

    headers, rows = _parse_first_markdown_table(section_content)
    if not headers:
        return [], warnings

    column_map = {_normalize_column_name(name): idx for idx, name in enumerate(headers)}

    claim_id_idx = _find_column_index(column_map, "claim id", "id")
    claim_idx = _find_column_index(column_map, "claim (paraphrased)", "claim")
    crux_idx = _find_column_index(column_map, "crux?")
    source_says_idx = _find_column_index(column_map, "source says")
    actual_idx = _find_column_index(column_map, "actual")
    external_source_idx = _find_column_index(column_map, "external source", "verification source")
    search_notes_idx = _find_column_index(column_map, "search notes", "notes")
    status_idx = _find_column_index(column_map, "status")

    missing_required = []
    if claim_id_idx is None:
        missing_required.append("Claim ID")
    if claim_idx is None:
        missing_required.append("Claim (paraphrased)")
    if crux_idx is None:
        missing_required.append("Crux?")
    if source_says_idx is None:
        missing_required.append("Source Says")
    if actual_idx is None:
        missing_required.append("Actual")
    if external_source_idx is None:
        missing_required.append("External Source")
    if search_notes_idx is None:
        missing_required.append("Search Notes")
    if status_idx is None:
        missing_required.append("Status")

    if missing_required:
        warnings.append(
            "Key Factual Claims Verified table is missing required columns for factual verification gating: "
            + ", ".join(missing_required)
        )

    def cell(row_cells: list[str], index: int | None) -> str:
        if index is None:
            return ""
        if index >= len(row_cells):
            return ""
        return row_cells[index].strip()

    extracted_rows: list[dict[str, str]] = []
    for row_cells in rows:
        extracted_rows.append(
            {
                "claim_id": cell(row_cells, claim_id_idx),
                "claim": cell(row_cells, claim_idx),
                "crux": cell(row_cells, crux_idx),
                "source_says": cell(row_cells, source_says_idx),
                "actual": cell(row_cells, actual_idx),
                "external_source": cell(row_cells, external_source_idx),
                "search_notes": cell(row_cells, search_notes_idx),
                "status": cell(row_cells, status_idx),
            }
        )

    return extracted_rows, warnings


def _extract_key_claim_rows(content: str) -> list[dict[str, str | float]]:
    """Extract claim IDs, types, and credence values from Key Claims table."""
    lines = content.splitlines()
    header_index = None
    for index, line in enumerate(lines):
        if re.search(r"^\|\s*#\s*\|.*\|\s*Claim ID\s*\|", line, re.IGNORECASE):
            header_index = index
            break

    if header_index is None or header_index + 2 >= len(lines):
        return []

    header_cells = _split_md_table_row(lines[header_index])
    separator_cells = _split_md_table_row(lines[header_index + 1])
    if not _is_table_separator_row(separator_cells):
        return []

    column_map = {_normalize_column_name(name): idx for idx, name in enumerate(header_cells)}
    claim_id_idx = _find_column_index(column_map, "claim id")
    claim_type_idx = _find_column_index(column_map, "type")
    credence_idx = _find_column_index(column_map, "credence", "conf")

    if claim_id_idx is None or claim_type_idx is None or credence_idx is None:
        return []

    claims: list[dict[str, str | float]] = []
    for line in lines[header_index + 2:]:
        if not line.strip().startswith("|"):
            break
        row_cells = _split_md_table_row(line)
        if not row_cells or len(row_cells) <= max(claim_id_idx, claim_type_idx, credence_idx):
            continue

        claim_id = extract_claim_id(row_cells[claim_id_idx])
        if not claim_id:
            continue

        claim_type = row_cells[claim_type_idx].strip()
        try:
            credence = float(row_cells[credence_idx].strip())
        except ValueError:
            continue

        claims.append(
            {
                "claim_id": claim_id,
                "claim_type": claim_type,
                "credence": credence,
            }
        )

    return claims


def validate_factual_verification_rigor(content: str) -> list[str]:
    """Validate Stage 2 factual verification rigor checks (v0.3.2)."""
    warnings: list[str] = []
    reviewed = _is_reviewed_analysis(content)

    stage2_rows, stage2_warnings = _extract_stage2_factual_rows(content)
    warnings.extend(stage2_warnings)

    crux_rows = [row for row in stage2_rows if _is_crux_value(row.get("crux", ""))]

    if reviewed and not crux_rows:
        warnings.append(
            "Analysis marked [REVIEWED] but Stage 2 does not identify any crux factual claim (Crux?=Y required)"
        )

    status_by_claim_id: dict[str, str] = {}
    for row in stage2_rows:
        claim_id = extract_claim_id(row.get("claim_id", ""))
        if claim_id:
            status_by_claim_id[claim_id] = _normalize_status(row.get("status", ""))

    for row in crux_rows:
        claim_id = extract_claim_id(row.get("claim_id", "")) or row.get("claim_id", "").strip() or "<unknown>"
        status_raw = row.get("status", "").strip()
        status = _normalize_status(status_raw)
        search_notes = row.get("search_notes", "").strip()
        external_source = row.get("external_source", "").strip()

        if not extract_claim_id(row.get("claim_id", "")):
            warnings.append(
                "Crux factual verification row is missing Claim ID (required for auditable gating)"
            )

        if reviewed and status not in VALID_STAGE2_STATUSES:
            status_display = status_raw if status_raw else "<blank>"
            warnings.append(
                f"Crux factual claim {claim_id} has unknown Status '{status_display}' — use one of: ok, x, nf, blocked, ?"
            )
            # Fail closed in reviewed analyses: treat unknown/blank statuses as not attempted.
            status = "?"

        if reviewed and status == "?":
            warnings.append(
                f"Analysis marked [REVIEWED] but crux factual claim {claim_id} is not attempted (Status=?)"
            )

        if reviewed and status in {"nf", "blocked"} and not search_notes:
            warnings.append(
                f"Crux factual claim {claim_id} is unresolved but lacks Search Notes documenting the attempt"
            )

        if reviewed and status in {"ok", "x"} and not external_source:
            warnings.append(
                f"Crux factual claim {claim_id} marked verified/refuted but lacks an External Source citation"
            )

    key_claim_rows = _extract_key_claim_rows(content)
    for claim in key_claim_rows:
        claim_id = str(claim["claim_id"])
        claim_type = _normalize_claim_type(str(claim["claim_type"]))
        credence = float(claim["credence"])
        status = status_by_claim_id.get(claim_id, "")

        if claim_type == "F" and credence >= 0.7 and status not in {"ok", "x"}:
            warnings.append(
                f"High-credence factual claim {claim_id} is not verified/refuted — add citation/verification or lower credence"
            )

    return warnings


def validate_file(path: Path, profile: str | None = None, rigor: bool = False) -> ValidationResult:
    """Validate a single analysis file.

    Args:
        path: Path to the analysis file
        profile: Override detected profile ('full' or 'quick')
        rigor: If True, rigor-v1 warnings become errors

    Returns:
        ValidationResult with errors, warnings, and profile info
    """
    errors = []
    warnings = []

    # Read file
    try:
        content = path.read_text()
    except Exception as e:
        return ValidationResult(path, "unknown", [f"Could not read file: {e}"], [])

    # Check for framework repo indicators
    warnings.extend(check_framework_repo(path))

    # Detect or use specified profile
    detected_profile = detect_profile(content)
    if profile and profile != detected_profile:
        warnings.append(
            f"Specified profile '{profile}' differs from detected '{detected_profile}'"
        )
    actual_profile = profile or detected_profile

    # Get requirements for profile
    if actual_profile == "quick":
        requirements = QUICK_PROFILE_REQUIRED
    else:
        requirements = FULL_PROFILE_REQUIRED

    # Validate sections
    errors.extend(validate_sections(content, requirements["sections"]))

    # Validate tables
    errors.extend(validate_tables(content, requirements["tables"]))

    # Validate elements
    errors.extend(validate_elements(content, requirements["elements"]))

    # Validate claim IDs
    warnings.extend(validate_claim_ids(content))

    # Rigor-v1 validation (full profile only)
    if actual_profile == "full":
        rigor_warnings = []
        rigor_warnings.extend(validate_rigor_sections(content))
        rigor_warnings.extend(validate_rigor_columns(content))
        rigor_warnings.extend(validate_layer_values(content))
        rigor_warnings.extend(validate_factual_verification_rigor(content))

        if rigor:
            # In rigor mode, rigor warnings become errors
            errors.extend(rigor_warnings)
        else:
            warnings.extend(rigor_warnings)

    return ValidationResult(path, actual_profile, errors, warnings)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Reality Check analysis files against Output Contract"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Analysis file(s) to validate",
    )
    parser.add_argument(
        "--profile",
        choices=["full", "quick"],
        help="Force a specific profile (default: auto-detect)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--rigor",
        action="store_true",
        help="Enable rigor-v1 mode: require Layer/Actor/Scope/Quantifier columns and Corrections & Updates section",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output errors (no summary)",
    )
    args = parser.parse_args()

    results = []
    total_errors = 0
    total_warnings = 0

    for file_path in args.files:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            total_errors += 1
            continue

        result = validate_file(file_path, args.profile, rigor=args.rigor)
        results.append(result)
        total_errors += len(result.errors)
        total_warnings += len(result.warnings)

        if args.strict:
            total_errors += len(result.warnings)

    # Output results
    if args.json:
        import json
        output = {
            "results": [
                {
                    "path": str(r.path),
                    "profile": r.profile,
                    "errors": r.errors,
                    "warnings": r.warnings,
                }
                for r in results
            ],
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "status": "FAIL" if total_errors > 0 else "OK",
        }
        print(json.dumps(output, indent=2))
    else:
        for result in results:
            if result.errors or result.warnings or not args.quiet:
                print(f"\n{result.path} [{result.profile}]")

                for error in result.errors:
                    print(f"  ERROR: {error}")

                for warning in result.warnings:
                    prefix = "ERROR" if args.strict else "WARNING"
                    print(f"  {prefix}: {warning}")

        if not args.quiet:
            print(f"\n{'='*50}")
            print(f"Files checked: {len(results)}")
            print(f"Errors: {total_errors}")
            print(f"Warnings: {total_warnings}")
            print(f"Status: {'FAIL' if total_errors > 0 else 'OK'}")

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
