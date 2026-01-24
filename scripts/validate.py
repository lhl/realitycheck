#!/usr/bin/env python3
"""
Validation script for Reality Check.

Supports two modes:
- DB mode (default): Validates LanceDB database integrity
- YAML mode: Validates legacy YAML files (for migration verification)

Checks:
- Schema compliance
- Referential integrity (claims ↔ sources, chains → claims)
- Domain validity
- ID format compliance
- Prediction sync (all [P] claims have prediction records)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from db import (
    VALID_DOMAINS,
    VALID_ANALYSIS_STATUSES,
    VALID_ANALYSIS_TOOLS,
    find_project_root,
    resolve_db_path_from_project_root,
    get_db,
    get_table_names,
    list_claims,
    list_sources,
    list_chains,
    list_predictions,
    list_contradictions,
    list_definitions,
    list_analysis_logs,
    get_stats,
)


# Validation patterns
CLAIM_ID_RE = re.compile(r"^[A-Z]+-\d{4}-\d{3}$")
CHAIN_ID_RE = re.compile(r"^CHAIN-\d{4}-\d{3}$")
CONTRADICTION_ID_RE = re.compile(r"^TENS-\d{4}-\d{3}$")

ALLOWED_CLAIM_TYPES = {"[F]", "[T]", "[H]", "[P]", "[A]", "[C]", "[S]", "[X]"}
ALLOWED_EVIDENCE_LEVELS = {f"E{i}" for i in range(1, 7)}
ALLOWED_PREDICTION_STATUSES = {"[P+]", "[P~]", "[P→]", "[P?]", "[P←]", "[P!]", "[P-]", "[P∅]"}
ALLOWED_SOURCE_TYPES = {"PAPER", "BOOK", "REPORT", "ARTICLE", "BLOG", "SOCIAL", "CONVO", "INTERVIEW", "DATA", "FICTION", "KNOWLEDGE"}


@dataclass(frozen=True)
class Finding:
    """A validation finding (error or warning)."""
    level: str  # "ERROR" | "WARN"
    code: str
    message: str


def _is_probability(value: Any) -> bool:
    """Check if value is a valid probability [0, 1]."""
    if value is None:
        return False
    if not isinstance(value, (int, float)):
        return False
    return 0.0 <= float(value) <= 1.0


# =============================================================================
# Database Validation
# =============================================================================

def validate_db(db_path: Optional[Path] = None) -> list[Finding]:
    """Validate LanceDB database integrity."""
    findings: list[Finding] = []

    if db_path is None and not os.getenv("REALITYCHECK_DATA"):
        default_db = Path("data/realitycheck.lance")
        if default_db.exists():
            db_path = default_db
        else:
            project_root = find_project_root(Path.cwd())
            if project_root:
                detected = resolve_db_path_from_project_root(project_root)
                if detected.exists():
                    db_path = detected

    if db_path is None and not os.getenv("REALITYCHECK_DATA"):
        default_db = Path("data/realitycheck.lance")
        return [
            Finding(
                "ERROR",
                "REALITYCHECK_DATA_MISSING",
                "REALITYCHECK_DATA is not set and no database was found at "
                f"'{default_db}' (or via project auto-detect). Set REALITYCHECK_DATA or pass --db-path.",
            )
        ]

    try:
        db = get_db(db_path)
    except Exception as e:
        return [Finding("ERROR", "DB_CONNECTION", f"Cannot connect to database: {e}")]

    # Check tables exist
    expected_tables = {"claims", "sources", "chains", "predictions", "contradictions", "definitions"}
    existing_tables = set(get_table_names(db))
    missing_tables = expected_tables - existing_tables

    if missing_tables:
        findings.append(Finding("ERROR", "DB_TABLES_MISSING", f"Missing tables: {', '.join(sorted(missing_tables))}"))
        # Can't continue validation without tables
        return findings

    # Load all data
    try:
        claims = {c["id"]: c for c in list_claims(limit=100000, db=db)}
        sources = {s["id"]: s for s in list_sources(limit=100000, db=db)}
        chains = {c["id"]: c for c in list_chains(limit=100000, db=db)}
        predictions = {p["claim_id"]: p for p in list_predictions(limit=100000, db=db)}
    except Exception as e:
        return [Finding("ERROR", "DB_READ", f"Error reading database: {e}")]

    claim_ids = set(claims.keys())
    source_ids = set(sources.keys())
    chain_ids = set(chains.keys())

    # Validate claims
    for claim_id, claim in claims.items():
        # ID format
        if not CLAIM_ID_RE.match(claim_id):
            findings.append(Finding("ERROR", "CLAIM_ID_FORMAT", f"Invalid claim ID format: {claim_id}"))
            continue

        # Domain from ID matches field
        domain_from_id = claim_id.split("-")[0]
        if claim.get("domain") != domain_from_id:
            findings.append(Finding("ERROR", "CLAIM_DOMAIN_MISMATCH",
                f"{claim_id}: ID domain '{domain_from_id}' != field domain '{claim.get('domain')}'"))

        # Domain is valid
        if claim.get("domain") not in VALID_DOMAINS:
            findings.append(Finding("ERROR", "CLAIM_DOMAIN_INVALID",
                f"{claim_id}: Invalid domain '{claim.get('domain')}'"))

        # Type is valid
        if claim.get("type") not in ALLOWED_CLAIM_TYPES:
            findings.append(Finding("ERROR", "CLAIM_TYPE_INVALID",
                f"{claim_id}: Invalid type '{claim.get('type')}'"))

        # Evidence level is valid
        if claim.get("evidence_level") not in ALLOWED_EVIDENCE_LEVELS:
            findings.append(Finding("ERROR", "CLAIM_EVIDENCE_INVALID",
                f"{claim_id}: Invalid evidence_level '{claim.get('evidence_level')}'"))

        # Credence is valid probability
        if not _is_probability(claim.get("credence")):
            findings.append(Finding("ERROR", "CLAIM_CREDENCE_INVALID",
                f"{claim_id}: Invalid credence '{claim.get('credence')}'"))

        # Text is non-empty
        if not claim.get("text") or not claim["text"].strip():
            findings.append(Finding("ERROR", "CLAIM_TEXT_EMPTY",
                f"{claim_id}: Missing or empty text"))

        # Source IDs exist
        for source_id in claim.get("source_ids", []) or []:
            if source_id not in source_ids:
                findings.append(Finding("ERROR", "CLAIM_SOURCE_MISSING",
                    f"{claim_id}: References unknown source '{source_id}'"))

        # Relationship targets exist
        for rel_field in ("supports", "contradicts", "depends_on", "modified_by"):
            for target_id in claim.get(rel_field, []) or []:
                if target_id not in claim_ids:
                    findings.append(Finding("ERROR", "CLAIM_REL_MISSING",
                        f"{claim_id}: {rel_field} references unknown claim '{target_id}'"))

        # Chain reference exists
        chain_ref = claim.get("part_of_chain")
        if chain_ref and chain_ref not in chain_ids:
            findings.append(Finding("ERROR", "CLAIM_CHAIN_MISSING",
                f"{claim_id}: References unknown chain '{chain_ref}'"))

        # Embedding exists (warning only)
        if not claim.get("embedding"):
            findings.append(Finding("WARN", "CLAIM_NO_EMBEDDING",
                f"{claim_id}: Missing embedding"))

    # Validate sources
    for source_id, source in sources.items():
        # Type is valid
        if source.get("type") not in ALLOWED_SOURCE_TYPES:
            findings.append(Finding("ERROR", "SOURCE_TYPE_INVALID",
                f"{source_id}: Invalid type '{source.get('type')}'"))

        # Reliability is valid probability (if set)
        if source.get("reliability") is not None and not _is_probability(source.get("reliability")):
            findings.append(Finding("ERROR", "SOURCE_RELIABILITY_INVALID",
                f"{source_id}: Invalid reliability '{source.get('reliability')}'"))

        # Claims extracted exist and have backlinks
        for claim_id in source.get("claims_extracted", []) or []:
            if claim_id not in claim_ids:
                findings.append(Finding("ERROR", "SOURCE_CLAIM_MISSING",
                    f"{source_id}: claims_extracted references unknown claim '{claim_id}'"))
            else:
                # Check backlink
                claim = claims[claim_id]
                if source_id not in (claim.get("source_ids") or []):
                    findings.append(Finding("ERROR", "SOURCE_BACKLINK_MISSING",
                        f"{source_id}: lists {claim_id} but claim doesn't reference this source"))

        # Check reverse: claims citing this source should be in claims_extracted
        for claim_id, claim in claims.items():
            if source_id in (claim.get("source_ids") or []):
                if claim_id not in (source.get("claims_extracted") or []):
                    findings.append(Finding("ERROR", "SOURCE_CLAIM_NOT_LISTED",
                        f"{source_id}: claim {claim_id} cites this source but not in claims_extracted"))

    # Validate chains
    for chain_id, chain in chains.items():
        # ID format
        if not CHAIN_ID_RE.match(chain_id):
            findings.append(Finding("ERROR", "CHAIN_ID_FORMAT",
                f"Invalid chain ID format: {chain_id}"))
            continue

        # Credence is valid probability
        if not _is_probability(chain.get("credence")):
            findings.append(Finding("ERROR", "CHAIN_CREDENCE_INVALID",
                f"{chain_id}: Invalid credence '{chain.get('credence')}'"))

        # Claims exist
        for claim_id in chain.get("claims", []) or []:
            if claim_id not in claim_ids:
                findings.append(Finding("ERROR", "CHAIN_CLAIM_MISSING",
                    f"{chain_id}: References unknown claim '{claim_id}'"))

        # Verify MIN scoring: chain credence <= min(claim credences)
        chain_claims = [claims[cid] for cid in (chain.get("claims") or []) if cid in claims]
        if chain_claims:
            min_credence = min(c.get("credence", 1.0) for c in chain_claims)
            chain_credence = chain.get("credence", 0)
            if chain_credence > min_credence + 0.01:  # Small tolerance
                findings.append(Finding("WARN", "CHAIN_CREDENCE_EXCEEDS_MIN",
                    f"{chain_id}: Chain credence {chain_credence} > min claim credence {min_credence}"))

    # Validate predictions
    prediction_claim_ids = {cid for cid, c in claims.items() if c.get("type") == "[P]"}

    for claim_id, pred in predictions.items():
        # Status is valid
        if pred.get("status") not in ALLOWED_PREDICTION_STATUSES:
            findings.append(Finding("ERROR", "PREDICTION_STATUS_INVALID",
                f"Prediction {claim_id}: Invalid status '{pred.get('status')}'"))

        # Claim exists and is type [P]
        if claim_id not in claim_ids:
            findings.append(Finding("ERROR", "PREDICTION_CLAIM_MISSING",
                f"Prediction references unknown claim '{claim_id}'"))
        elif claims[claim_id].get("type") != "[P]":
            findings.append(Finding("ERROR", "PREDICTION_CLAIM_NOT_P",
                f"Prediction {claim_id}: Claim is not type [P]"))

        # Source exists
        source_id = pred.get("source_id")
        if source_id and source_id not in source_ids:
            findings.append(Finding("ERROR", "PREDICTION_SOURCE_MISSING",
                f"Prediction {claim_id}: References unknown source '{source_id}'"))

    # Check all [P] claims have predictions
    prediction_ids = set(predictions.keys())
    missing_predictions = prediction_claim_ids - prediction_ids
    if missing_predictions:
        findings.append(Finding("ERROR", "PREDICTIONS_MISSING",
            f"{len(missing_predictions)} [P] claims without prediction records: {', '.join(sorted(missing_predictions)[:5])}..."))

    # Validate analysis logs (if table exists)
    if "analysis_logs" in existing_tables:
        try:
            analysis_logs = list_analysis_logs(limit=100000, db=db)
        except Exception as e:
            findings.append(Finding("ERROR", "ANALYSIS_LOGS_READ", f"Error reading analysis_logs: {e}"))
            analysis_logs = []

        for log in analysis_logs:
            log_id = log.get("id", "UNKNOWN")

            # Status validation
            status = log.get("status")
            if status not in VALID_ANALYSIS_STATUSES:
                findings.append(Finding("ERROR", "ANALYSIS_STATUS_INVALID",
                    f"{log_id}: Invalid status '{status}'"))

            # Tool validation
            tool = log.get("tool")
            if tool not in VALID_ANALYSIS_TOOLS:
                findings.append(Finding("ERROR", "ANALYSIS_TOOL_INVALID",
                    f"{log_id}: Invalid tool '{tool}'"))

            # If completed, source_id must exist in sources
            if status == "completed":
                source_id = log.get("source_id")
                if source_id and source_id not in source_ids:
                    findings.append(Finding("ERROR", "ANALYSIS_SOURCE_MISSING",
                        f"{log_id}: Completed analysis references unknown source '{source_id}'"))

            # If claims_extracted/updated and status != draft, claims must exist
            if status != "draft":
                for claim_id in log.get("claims_extracted") or []:
                    if claim_id not in claim_ids:
                        findings.append(Finding("ERROR", "ANALYSIS_CLAIM_MISSING",
                            f"{log_id}: claims_extracted references unknown claim '{claim_id}'"))

                for claim_id in log.get("claims_updated") or []:
                    if claim_id not in claim_ids:
                        findings.append(Finding("ERROR", "ANALYSIS_CLAIM_MISSING",
                            f"{log_id}: claims_updated references unknown claim '{claim_id}'"))

            # Validate stages_json is valid JSON if present
            stages_json = log.get("stages_json")
            if stages_json:
                try:
                    json.loads(stages_json)
                except json.JSONDecodeError:
                    findings.append(Finding("ERROR", "ANALYSIS_STAGES_INVALID_JSON",
                        f"{log_id}: stages_json is not valid JSON"))

            # Check for impossible metrics
            duration = log.get("duration_seconds")
            if duration is not None and duration < 0:
                findings.append(Finding("ERROR", "ANALYSIS_DURATION_NEGATIVE",
                    f"{log_id}: Negative duration_seconds: {duration}"))

            cost = log.get("cost_usd")
            if cost is not None and cost < 0:
                findings.append(Finding("ERROR", "ANALYSIS_COST_NEGATIVE",
                    f"{log_id}: Negative cost_usd: {cost}"))

    return findings


# =============================================================================
# YAML Validation (Legacy)
# =============================================================================

def _load_yaml(path: Path) -> Any:
    """Load a YAML file."""
    try:
        return yaml.safe_load(path.read_text())
    except FileNotFoundError:
        raise  # Let FileNotFoundError propagate
    except Exception as e:
        raise ValueError(f"Failed to parse YAML: {path}: {e}")


def validate_yaml(repo_root: Path, strict_paths: bool = False) -> list[Finding]:
    """Validate legacy YAML files."""
    findings: list[Finding] = []

    claims_path = repo_root / "claims" / "registry.yaml"
    sources_path = repo_root / "reference" / "sources.yaml"
    predictions_path = repo_root / "tracking" / "predictions.md"

    # Load files
    try:
        claims_data = _load_yaml(claims_path)
    except FileNotFoundError:
        return [Finding("ERROR", "CLAIMS_MISSING", f"Missing {claims_path}")]
    except ValueError as e:
        return [Finding("ERROR", "CLAIMS_PARSE", str(e))]

    try:
        sources_data = _load_yaml(sources_path)
    except FileNotFoundError:
        return [Finding("ERROR", "SOURCES_MISSING", f"Missing {sources_path}")]
    except ValueError as e:
        return [Finding("ERROR", "SOURCES_PARSE", str(e))]

    claims = claims_data.get("claims", {})
    chains = claims_data.get("chains", {})
    sources = sources_data.get("sources", {})

    claim_ids = set(claims.keys())
    source_ids = set(sources.keys())
    chain_ids = set(chains.keys())

    # Validate claims (similar to DB validation but for YAML structure)
    for claim_id, claim in claims.items():
        if not CLAIM_ID_RE.match(claim_id):
            findings.append(Finding("ERROR", "CLAIM_ID_FORMAT", f"Invalid claim ID: {claim_id}"))
            continue

        if not isinstance(claim, dict):
            findings.append(Finding("ERROR", "CLAIM_NOT_DICT", f"{claim_id}: Claim must be a dict"))
            continue

        # Type
        if claim.get("type") not in ALLOWED_CLAIM_TYPES:
            findings.append(Finding("ERROR", "CLAIM_TYPE_INVALID",
                f"{claim_id}: Invalid type '{claim.get('type')}'"))

        # Evidence level
        if claim.get("evidence_level") not in ALLOWED_EVIDENCE_LEVELS:
            findings.append(Finding("ERROR", "CLAIM_EVIDENCE_INVALID",
                f"{claim_id}: Invalid evidence_level '{claim.get('evidence_level')}'"))

        # Credence (legacy YAML may use 'confidence', new uses 'credence')
        conf = claim.get("credence") or claim.get("confidence")
        if not _is_probability(conf):
            findings.append(Finding("ERROR", "CLAIM_CREDENCE_INVALID",
                f"{claim_id}: Invalid credence '{conf}'"))

        # Source refs
        for sid in claim.get("source_ids", []) or []:
            if sid not in source_ids:
                findings.append(Finding("ERROR", "CLAIM_SOURCE_MISSING",
                    f"{claim_id}: Unknown source '{sid}'"))

        # Relationship refs
        for rel in ("supports", "contradicts", "depends_on", "modified_by"):
            for ref in claim.get(rel, []) or []:
                if ref not in claim_ids:
                    findings.append(Finding("ERROR", "CLAIM_REL_MISSING",
                        f"{claim_id}: {rel} references unknown claim '{ref}'"))

    # Validate sources
    for source_id, source in sources.items():
        if not isinstance(source, dict):
            findings.append(Finding("ERROR", "SOURCE_NOT_DICT", f"{source_id}: Source must be a dict"))
            continue

        for claim_id in source.get("claims_extracted", []) or []:
            if claim_id not in claim_ids:
                findings.append(Finding("ERROR", "SOURCE_CLAIM_MISSING",
                    f"{source_id}: Unknown claim '{claim_id}'"))

    # Validate chains
    for chain_id, chain in chains.items():
        if not CHAIN_ID_RE.match(chain_id):
            findings.append(Finding("ERROR", "CHAIN_ID_FORMAT", f"Invalid chain ID: {chain_id}"))
            continue

        for claim_id in chain.get("claims", []) or []:
            if claim_id not in claim_ids:
                findings.append(Finding("ERROR", "CHAIN_CLAIM_MISSING",
                    f"{chain_id}: Unknown claim '{claim_id}'"))

    # Validate predictions.md
    if predictions_path.exists():
        text = predictions_path.read_text()
        pred_claim_ids = set(re.findall(r"\*\*Claim ID\*\*:\s*([A-Z]+-\d{4}-\d{3})", text))

        # Check all [P] claims are in predictions.md
        p_claims = {cid for cid, c in claims.items() if c.get("type") == "[P]"}
        missing = p_claims - pred_claim_ids
        if missing:
            findings.append(Finding("ERROR", "PREDICTIONS_MISSING",
                f"Missing from predictions.md: {', '.join(sorted(missing)[:5])}..."))

        # Check referenced claims exist
        unknown = pred_claim_ids - claim_ids
        if unknown:
            findings.append(Finding("ERROR", "PREDICTIONS_UNKNOWN",
                f"predictions.md references unknown claims: {', '.join(sorted(unknown))}"))

    return findings


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Reality Check data integrity"
    )
    parser.add_argument(
        "--mode",
        choices=["db", "yaml"],
        default="db",
        help="Validation mode: 'db' for LanceDB, 'yaml' for legacy YAML files"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Database path (for db mode)"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (for yaml mode)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if args.mode == "db":
        findings = validate_db(args.db_path)
    else:
        repo_root = args.repo_root or Path.cwd()
        findings = validate_yaml(repo_root, strict_paths=args.strict)

    errors = [f for f in findings if f.level == "ERROR"]
    warnings = [f for f in findings if f.level == "WARN"]

    if args.strict:
        errors.extend(warnings)
        warnings = []

    if args.json:
        output = {
            "ok": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "findings": [asdict(f) for f in findings],
        }
        print(json.dumps(output, indent=2))
    else:
        if errors:
            print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        else:
            print(f"OK: {len(errors)} error(s), {len(warnings)} warning(s)")

        for f in findings:
            print(f"{f.level} [{f.code}] {f.message}")

        codes = {f.code for f in findings}
        remediation: list[str] = []
        if codes & {"SOURCE_CLAIM_NOT_LISTED", "SOURCE_BACKLINK_MISSING", "PREDICTIONS_MISSING"}:
            remediation.append("rc-db repair")
        if "REALITYCHECK_DATA_MISSING" in codes or "DB_CONNECTION" in codes:
            remediation.append("rc-db doctor")

        if remediation:
            print("\nSuggested remediation:")
            for cmd in remediation:
                print(f"  {cmd}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
