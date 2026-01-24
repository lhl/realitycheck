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
)
from db import (
    get_db,
    init_tables,
    add_claim,
    add_source,
    add_chain,
    add_prediction,
    add_analysis_log,
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

        # Add a second log
        log2 = sample_analysis_log.copy()
        log2["id"] = "ANALYSIS-2026-002"
        log2["total_tokens"] = 5000
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
        unknown = sample_analysis_log.copy()
        unknown["id"] = "ANALYSIS-2026-002"
        unknown["total_tokens"] = None
        unknown["cost_usd"] = None
        add_analysis_log(unknown, initialized_db)

        zero = sample_analysis_log.copy()
        zero["id"] = "ANALYSIS-2026-003"
        zero["total_tokens"] = 0
        zero["cost_usd"] = 0.0
        add_analysis_log(zero, initialized_db)

        md_str = export_analysis_logs_md(temp_db_path)

        assert "**Total Logs**: 2" in md_str
        assert "**Total Tokens**: 0 (known; 1 unknown)" in md_str
        assert "**Total Cost**: $0.0000 (known; 1 unknown)" in md_str


class TestExportCLI:
    """CLI tests for scripts/export.py."""

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
