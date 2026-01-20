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

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from export import (
    export_claims_yaml,
    export_sources_yaml,
    export_claim_md,
    export_chain_md,
    export_predictions_md,
    export_summary_md,
)
from db import (
    get_db,
    init_tables,
    add_claim,
    add_source,
    add_chain,
    add_prediction,
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

    def test_export_claims_yaml_credence_to_confidence(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Exported YAML uses 'confidence' (legacy name)."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        yaml_str = export_claims_yaml(temp_db_path)
        yaml_content = "\n".join(
            line for line in yaml_str.split("\n")
            if not line.startswith("#")
        )
        data = yaml.safe_load(yaml_content)

        claim = data["claims"]["TECH-2026-001"]
        assert "confidence" in claim
        assert "credence" not in claim
        assert claim["confidence"] == pytest.approx(0.75, rel=0.01)

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
        assert isinstance(claim["confidence"], float)
        assert isinstance(claim["version"], int)
        assert isinstance(claim["source_ids"], list)
        assert isinstance(claim["supports"], list)
