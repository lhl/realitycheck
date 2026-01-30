"""
Unit tests for scripts/export.py

Tests cover:
- YAML export (legacy format)
- Markdown export (claims, chains, predictions, summary)
- Export correctness and formatting
"""

import pytest
import yaml
from pathlib import Path
import subprocess
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from export import (
    export_claims_yaml,
    export_sources_yaml,
    export_claim_md,
    export_chain_md,
    export_predictions_md,
    export_summary_md,
    export_analysis_logs_yaml,
    export_analysis_logs_md,
    export_reasoning_md,
    export_reasoning_all_md,
    export_evidence_by_claim_md,
    export_evidence_by_source_md,
    export_provenance_yaml,
    export_provenance_json,
)
from db import (
    get_db,
    init_tables,
    add_claim,
    add_source,
    add_chain,
    add_prediction,
    add_analysis_log,
    add_evidence_link,
    add_reasoning_trail,
)


class TestYamlExport:
    """Tests for YAML export functionality."""

    def test_export_claims_yaml_structure(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported YAML has correct structure."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        yaml_str = export_claims_yaml(temp_db_path)

        # Parse the YAML (skip header comments)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        assert "counters" in data
        assert "claims" in data
        assert "chains" in data

    def test_export_claims_yaml_has_counters(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported YAML has correct counters."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        yaml_str = export_claims_yaml(temp_db_path)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        assert data["counters"]["TECH"] >= 1

    def test_export_claims_yaml_uses_credence(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported YAML uses 'credence' (standardized name)."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        yaml_str = export_claims_yaml(temp_db_path)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        claim = data["claims"]["TECH-2026-001"]
        assert "credence" in claim
        assert "confidence" not in claim
        assert claim["credence"] == pytest.approx(0.75, rel=0.01)

    def test_export_sources_yaml_structure(self, initialized_db, temp_db_path, sample_source):
        """Exported sources YAML has correct structure."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        yaml_str = export_sources_yaml(temp_db_path)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        assert "sources" in data
        assert "test-source-001" in data["sources"]

    def test_export_sources_yaml_fields(self, initialized_db, temp_db_path, sample_source):
        """Exported source has all required fields."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        yaml_str = export_sources_yaml(temp_db_path)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        source = data["sources"]["test-source-001"]
        assert source["type"] == "REPORT"
        assert source["title"] == "Test Report on AI"
        assert source["reliability"] == pytest.approx(0.8, rel=0.01)


class TestMarkdownExport:
    """Tests for Markdown export functionality."""

    def test_export_claim_md_header(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported claim MD has correct header."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        md = export_claim_md("TECH-2026-001", temp_db_path)

        assert md.startswith("# TECH-2026-001")

    def test_export_claim_md_contains_text(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported claim MD contains claim text."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        md = export_claim_md("TECH-2026-001", temp_db_path)

        assert sample_claim["text"] in md

    def test_export_claim_md_contains_metadata(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported claim MD contains metadata."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        md = export_claim_md("TECH-2026-001", temp_db_path)

        assert "[F]" in md  # Type
        assert "TECH" in md  # Domain
        assert "E2" in md  # Evidence level
        assert "0.75" in md  # Credence

    def test_export_claim_md_not_found(self, initialized_db, temp_db_path):
        """Non-existent claim produces not found message."""
        md = export_claim_md("NONEXISTENT-2026-001", temp_db_path)

        assert "Not Found" in md

    def test_export_chain_md_header(self, initialized_db, temp_db_path, sample_claim, sample_source, sample_chain):
        """Exported chain MD has correct header."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_chain(sample_chain, initialized_db, generate_embedding=False)

        md = export_chain_md("CHAIN-2026-001", temp_db_path)

        assert "CHAIN-2026-001" in md
        assert sample_chain["name"] in md

    def test_export_chain_md_contains_thesis(self, initialized_db, temp_db_path, sample_claim, sample_source, sample_chain):
        """Exported chain MD contains thesis."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_chain(sample_chain, initialized_db, generate_embedding=False)

        md = export_chain_md("CHAIN-2026-001", temp_db_path)

        assert sample_chain["thesis"] in md

    def test_export_chain_md_contains_scoring_rule(self, initialized_db, temp_db_path, sample_claim, sample_source, sample_chain):
        """Exported chain MD mentions MIN scoring rule."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_chain(sample_chain, initialized_db, generate_embedding=False)

        md = export_chain_md("CHAIN-2026-001", temp_db_path)

        assert "MIN" in md

    def test_export_predictions_md_header(self, initialized_db, temp_db_path, sample_prediction):
        """Exported predictions MD has header."""
        # Need to add the claim first
        claim = {
            "id": "TECH-2026-002",
            "text": "Test prediction claim",
            "type": "[P]",
            "domain": "TECH",
            "evidence_level": "E5",
            "credence": 0.3,
            "source_ids": [],
            "first_extracted": "2026-01-19",
            "extracted_by": "test",
            "supports": [],
            "contradicts": [],
            "depends_on": [],
            "modified_by": [],
            "part_of_chain": "",
            "version": 1,
            "last_updated": "2026-01-19",
            "notes": None,
        }
        add_claim(claim, initialized_db, generate_embedding=False)
        add_prediction(sample_prediction, initialized_db)

        md = export_predictions_md(temp_db_path)

        assert "# Prediction Tracking" in md

    def test_export_predictions_md_groups_by_status(self, initialized_db, temp_db_path, sample_prediction):
        """Predictions are grouped by status."""
        claim = {
            "id": "TECH-2026-002",
            "text": "Test prediction claim",
            "type": "[P]",
            "domain": "TECH",
            "evidence_level": "E5",
            "credence": 0.3,
            "source_ids": [],
            "first_extracted": "2026-01-19",
            "extracted_by": "test",
            "supports": [],
            "contradicts": [],
            "depends_on": [],
            "modified_by": [],
            "part_of_chain": "",
            "version": 1,
            "last_updated": "2026-01-19",
            "notes": None,
        }
        add_claim(claim, initialized_db, generate_embedding=False)
        add_prediction(sample_prediction, initialized_db)

        md = export_predictions_md(temp_db_path)

        assert "On Track" in md  # [P→] status group

    def test_export_summary_md_has_statistics(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Summary MD contains statistics table."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        md = export_summary_md(temp_db_path)

        assert "## Statistics" in md
        assert "claims" in md.lower()
        assert "sources" in md.lower()

    def test_export_summary_md_has_domain_breakdown(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Summary MD contains domain breakdown."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        md = export_summary_md(temp_db_path)

        assert "Claims by Domain" in md
        assert "TECH" in md

    def test_export_summary_md_has_type_breakdown(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Summary MD contains type breakdown."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        md = export_summary_md(temp_db_path)

        assert "Claims by Type" in md
        assert "[F]" in md


class TestExportRoundTrip:
    """Tests for export/import round-trip consistency."""

    def test_yaml_export_parseable(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported YAML can be parsed back."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        yaml_str = export_claims_yaml(temp_db_path)

        # Remove header comments
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )

        # Should not raise
        data = yaml.safe_load(yaml_content)
        assert data is not None

    def test_yaml_preserves_data_types(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported YAML preserves correct data types."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        yaml_str = export_claims_yaml(temp_db_path)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        claim = data["claims"]["TECH-2026-001"]

        # Check types
        assert isinstance(claim["credence"], float)
        assert isinstance(claim["version"], int)
        assert isinstance(claim["source_ids"], list)
        assert isinstance(claim["supports"], list)


class TestAnalysisLogsExport:
    """Tests for analysis logs export."""

    def test_export_analysis_logs_yaml(self, initialized_db, temp_db_path, sample_analysis_log):
        """YAML export includes all fields."""
        add_analysis_log(sample_analysis_log, initialized_db)

        yaml_str = export_analysis_logs_yaml(temp_db_path)

        # Parse the YAML (skip header comments)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        assert "analysis_logs" in data
        assert len(data["analysis_logs"]) == 1

        log = data["analysis_logs"][0]
        assert log["id"] == "ANALYSIS-2026-001"
        assert log["source_id"] == "test-source-001"
        assert log["tool"] == "claude-code"
        assert log["status"] == "completed"
        assert log["total_tokens"] == 3700
        assert log["cost_usd"] == pytest.approx(0.08, rel=0.01)

    def test_export_analysis_logs_md(self, initialized_db, temp_db_path, sample_analysis_log):
        """Markdown export produces table format."""
        add_analysis_log(sample_analysis_log, initialized_db)

        md_str = export_analysis_logs_md(temp_db_path)

        # Check structure
        assert "# Analysis Logs" in md_str
        assert "## Log Entries" in md_str
        assert "| Pass | Date | Source | Tool | Model | Duration | Tokens | Cost | Notes |" in md_str
        assert "test-source-001" in md_str
        assert "claude-code" in md_str

    def test_export_analysis_logs_md_totals(self, initialized_db, temp_db_path, sample_analysis_log):
        """Markdown export includes token/cost totals."""
        add_analysis_log(sample_analysis_log, initialized_db)

        # Add a second log (set both tokens_check and total_tokens - export prefers tokens_check)
        log2 = sample_analysis_log.copy()
        log2["id"] = "ANALYSIS-2026-002"
        log2["total_tokens"] = 5000
        log2["tokens_check"] = 5000  # Export prefers tokens_check over total_tokens
        log2["cost_usd"] = 0.12
        add_analysis_log(log2, initialized_db)

        md_str = export_analysis_logs_md(temp_db_path)

        # Check totals section
        assert "## Summary Totals" in md_str
        assert "**Total Logs**: 2" in md_str
        assert "**Total Tokens**: 8,700" in md_str
        assert "$0.20" in md_str  # 0.08 + 0.12

    def test_export_analysis_logs_md_does_not_truncate_source_or_notes(self, initialized_db, temp_db_path, sample_analysis_log):
        """Markdown export should not truncate long source IDs or notes."""
        log = sample_analysis_log.copy()
        log["source_id"] = "source-with-a-very-long-id-1234567890"
        log["notes"] = "This is a long note that should not be truncated by the export."
        add_analysis_log(log, initialized_db)

        md_str = export_analysis_logs_md(temp_db_path)

        assert log["source_id"] in md_str
        assert log["notes"] in md_str

    def test_export_analysis_logs_md_tracks_unknown_tokens_and_cost(self, initialized_db, temp_db_path, sample_analysis_log):
        """Markdown totals should distinguish known values from unknown/missing."""
        # Log with unknown tokens (both tokens_check and total_tokens are None)
        unknown = sample_analysis_log.copy()
        unknown["id"] = "ANALYSIS-2026-002"
        unknown["total_tokens"] = None
        unknown["tokens_check"] = None  # Export prefers tokens_check, so must also be None
        unknown["cost_usd"] = None
        add_analysis_log(unknown, initialized_db)

        # Log with zero tokens
        zero = sample_analysis_log.copy()
        zero["id"] = "ANALYSIS-2026-003"
        zero["total_tokens"] = 0
        zero["tokens_check"] = 0  # Export prefers tokens_check
        zero["cost_usd"] = 0.0
        add_analysis_log(zero, initialized_db)

        md_str = export_analysis_logs_md(temp_db_path)

        assert "**Total Logs**: 2" in md_str
        assert "**Total Tokens**: 0 (known; 1 unknown)" in md_str
        assert "**Total Cost**: $0.0000 (known; 1 unknown)" in md_str

    def test_export_analysis_logs_md_tokens_check_zero_not_fallback(self, initialized_db, temp_db_path, sample_analysis_log):
        """tokens_check=0 should render as 0, not fall back to total_tokens.

        Regression test: the `or` pattern (tokens_check or total_tokens) would
        incorrectly treat 0 as falsy and fall back to total_tokens.
        """
        log = sample_analysis_log.copy()
        log["id"] = "ANALYSIS-2026-ZERO"
        log["tokens_check"] = 0       # Should use this (0)
        log["total_tokens"] = 12345   # Should NOT fall back to this
        log["cost_usd"] = 0.0
        add_analysis_log(log, initialized_db)

        md_str = export_analysis_logs_md(temp_db_path)

        # If the bug exists, total would be 12345. With fix, total should be 0.
        # The sample_analysis_log has total_tokens=3700, so total would be 3700 + 0 = 3700
        # (or 3700 + 12345 = 16045 if bug exists)
        assert "**Total Tokens**: 3,700" in md_str or "**Total Tokens**: 0" in md_str
        assert "16,045" not in md_str, "Bug: tokens_check=0 fell back to total_tokens=12345"


class TestExportCLI:
    """CLI tests for scripts/export.py."""

    def test_export_cli_autodetects_project_db_from_subdir(self, tmp_path: Path):
        """When REALITYCHECK_DATA is unset, export auto-detects a project DB from a subdirectory."""
        project_path = tmp_path / "test-project"

        init_project = subprocess.run(
            [
                sys.executable,
                "scripts/db.py",
                "init-project",
                "--path",
                str(project_path),
                "--no-git",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert init_project.returncode == 0, init_project.stderr

        env = os.environ.copy()
        env.pop("REALITYCHECK_DATA", None)
        cwd = project_path / "analysis" / "sources"
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "export.py"), "stats"],
            env=env,
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")
        combined = (result.stdout or "") + (result.stderr or "")
        assert "Database Statistics" in combined

    def test_cli_md_analysis_logs(self, initialized_db, temp_db_path, sample_analysis_log):
        """`rc-export md analysis-logs` exports analysis logs in Markdown."""
        add_analysis_log(sample_analysis_log, initialized_db)

        result = subprocess.run(
            [
                sys.executable,
                "scripts/export.py",
                "--db-path",
                str(temp_db_path),
                "md",
                "analysis-logs",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0, result.stderr
        assert "# Analysis Logs" in result.stdout

    def test_cli_yaml_analysis_logs(self, initialized_db, temp_db_path, sample_analysis_log):
        """`rc-export yaml analysis-logs` exports analysis logs in YAML."""
        add_analysis_log(sample_analysis_log, initialized_db)

        result = subprocess.run(
            [
                sys.executable,
                "scripts/export.py",
                "--db-path",
                str(temp_db_path),
                "yaml",
                "analysis-logs",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0, result.stderr
        assert "analysis_logs:" in result.stdout


# =============================================================================
# Reasoning/Provenance Export Tests
# =============================================================================


class TestExportReasoningMarkdown:
    """Tests for reasoning trail Markdown export."""

    def test_export_reasoning_single_claim(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """export_reasoning_md returns Markdown for a single claim."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)
        add_reasoning_trail(sample_reasoning_trail, db=initialized_db)

        md = export_reasoning_md("TECH-2026-001", temp_db_path)

        assert "# Reasoning: TECH-2026-001" in md
        assert sample_claim["text"] in md

    def test_export_reasoning_includes_evidence_table(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """Exported reasoning includes evidence table."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)
        add_reasoning_trail(sample_reasoning_trail, db=initialized_db)

        md = export_reasoning_md("TECH-2026-001", temp_db_path)

        assert "## Evidence Summary" in md
        assert "| Direction | Source | Location | Strength | Summary |" in md
        assert "supports" in md.lower()

    def test_export_reasoning_includes_counterarguments(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """Exported reasoning includes counterarguments when present."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)
        add_reasoning_trail(sample_reasoning_trail, db=initialized_db)

        md = export_reasoning_md("TECH-2026-001", temp_db_path)

        assert "## Counterarguments Considered" in md
        assert "Study X found opposite result" in md
        assert "Discounted" in md

    def test_export_reasoning_includes_trail_history(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """Exported reasoning includes trail history."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)
        add_reasoning_trail(sample_reasoning_trail, db=initialized_db)

        md = export_reasoning_md("TECH-2026-001", temp_db_path)

        assert "## Trail History" in md
        assert "| Date | Credence | Evidence | Status | Pass |" in md

    def test_export_reasoning_includes_yaml_block(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """Exported reasoning includes portable YAML block."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)
        add_reasoning_trail(sample_reasoning_trail, db=initialized_db)

        md = export_reasoning_md("TECH-2026-001", temp_db_path)

        assert "## Data (portable)" in md
        assert "```yaml" in md
        assert 'claim_id: "TECH-2026-001"' in md

    def test_export_reasoning_skips_claims_without_trails(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """export_reasoning_all_md only exports claims with trails."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        # No reasoning trail added

        results = export_reasoning_all_md(temp_db_path)

        assert len(results) == 0

    def test_export_reasoning_all_claims(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """export_reasoning_all_md exports all claims with trails."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)
        add_reasoning_trail(sample_reasoning_trail, db=initialized_db)

        results = export_reasoning_all_md(temp_db_path)

        assert "TECH-2026-001" in results
        assert "# Reasoning: TECH-2026-001" in results["TECH-2026-001"]


class TestExportEvidenceIndex:
    """Tests for evidence index exports."""

    def test_export_evidence_by_claim_single(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link):
        """Export evidence links for a single claim."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)

        md = export_evidence_by_claim_md("TECH-2026-001", temp_db_path)

        assert "# Evidence: TECH-2026-001" in md
        assert "EVLINK-2026-001" in md
        assert "test-source-001" in md

    def test_export_evidence_by_source_single(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link):
        """Export evidence links from a single source."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)

        md = export_evidence_by_source_md("test-source-001", temp_db_path)

        assert "# Evidence from: test-source-001" in md
        assert "EVLINK-2026-001" in md
        assert "TECH-2026-001" in md


class TestExportProvenanceYAML:
    """Tests for provenance YAML/JSON export."""

    def test_export_provenance_yaml_evidence_links(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link):
        """Provenance YAML includes evidence links."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)

        yaml_str = export_provenance_yaml(temp_db_path)

        # Parse (skip header)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        assert "evidence_links" in data
        assert len(data["evidence_links"]) == 1
        assert data["evidence_links"][0]["id"] == "EVLINK-2026-001"

    def test_export_provenance_yaml_reasoning_trails(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """Provenance YAML includes reasoning trails."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)
        add_reasoning_trail(sample_reasoning_trail, db=initialized_db)

        yaml_str = export_provenance_yaml(temp_db_path)

        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        assert "reasoning_trails" in data
        assert len(data["reasoning_trails"]) == 1
        assert data["reasoning_trails"][0]["id"] == "REASON-2026-001"

    def test_export_provenance_yaml_deterministic_order(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Provenance YAML output is deterministic."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add multiple evidence links with different IDs
        for i in range(3):
            add_evidence_link({
                "id": f"EVLINK-2026-{i+1:03d}",
                "claim_id": "TECH-2026-001",
                "source_id": "test-source-001",
                "direction": "supports",
                "created_by": "test",
            }, db=initialized_db)

        yaml1 = export_provenance_yaml(temp_db_path)
        yaml2 = export_provenance_yaml(temp_db_path)

        # Remove timestamp from header for comparison
        def strip_header(s):
            return "\n".join(line for line in s.split("\n") if not line.startswith("#"))

        assert strip_header(yaml1) == strip_header(yaml2)

    def test_export_provenance_json_format(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link):
        """Provenance JSON is valid JSON."""
        import json as json_module

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)

        json_str = export_provenance_json(temp_db_path)

        # Should not raise
        data = json_module.loads(json_str)

        assert "evidence_links" in data
        assert "reasoning_trails" in data
        assert len(data["evidence_links"]) == 1
