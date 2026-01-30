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


def validate_file(path: Path, profile: str | None = None) -> ValidationResult:
    """Validate a single analysis file."""
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

        result = validate_file(file_path, args.profile)
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
