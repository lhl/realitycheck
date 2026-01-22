"""
Unit tests for scripts/validate.py

Tests cover:
- Database validation
- YAML validation (legacy mode)
- Error detection for various integrity issues
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate import (
    validate_db,
    validate_yaml,
    Finding,
    ALLOWED_CLAIM_TYPES,
    ALLOWED_EVIDENCE_LEVELS,
    ALLOWED_PREDICTION_STATUSES,
    ALLOWED_SOURCE_TYPES,
)
from db import (
    get_db,
    init_tables,
    add_claim,
    add_source,
    add_chain,
    add_prediction,
)


class TestConstants:
    """Tests for validation constants."""

    def test_claim_types_complete(self):
        """All claim types are defined."""
        expected = {"[F]", "[T]", "[H]", "[P]", "[A]", "[C]", "[S]", "[X]"}
        assert ALLOWED_CLAIM_TYPES == expected

    def test_evidence_levels_complete(self):
        """All evidence levels are defined."""
        expected = {"E1", "E2", "E3", "E4", "E5", "E6"}
        assert ALLOWED_EVIDENCE_LEVELS == expected

    def test_prediction_statuses_complete(self):
        """All prediction statuses are defined."""
        expected = {"[P+]", "[P~]", "[P→]", "[P?]", "[P←]", "[P!]", "[P-]", "[P∅]"}
        assert ALLOWED_PREDICTION_STATUSES == expected


class TestDatabaseValidation:
    """Tests for database integrity validation."""

    def test_validate_db_reports_missing_data_env_when_no_db(self, monkeypatch, tmp_path: Path):
        """Missing REALITYCHECK_DATA and missing default DB reports a clear error."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("REALITYCHECK_DATA", raising=False)

        findings = validate_db(None)

        assert any(f.code == "REALITYCHECK_DATA_MISSING" for f in findings)

    def test_valid_database_passes(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Valid database produces no errors."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        errors = [f for f in findings if f.level == "ERROR"]
        assert len(errors) == 0

    def test_invalid_claim_type_detected(self, initialized_db, temp_db_path, sample_claim):
        """Invalid claim type produces error."""
        sample_claim["type"] = "[INVALID]"
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        type_errors = [f for f in findings if f.code == "CLAIM_TYPE_INVALID"]
        assert len(type_errors) >= 1

    def test_invalid_evidence_level_detected(self, initialized_db, temp_db_path, sample_claim):
        """Invalid evidence level produces error."""
        sample_claim["evidence_level"] = "E99"
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        evidence_errors = [f for f in findings if f.code == "CLAIM_EVIDENCE_INVALID"]
        assert len(evidence_errors) >= 1

    def test_invalid_credence_detected(self, initialized_db, temp_db_path, sample_claim):
        """Credence outside [0,1] produces error."""
        sample_claim["credence"] = 1.5
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        credence_errors = [f for f in findings if f.code == "CLAIM_CREDENCE_INVALID"]
        assert len(credence_errors) >= 1

    def test_missing_source_detected(self, initialized_db, temp_db_path, sample_claim):
        """Reference to non-existent source produces error."""
        sample_claim["source_ids"] = ["nonexistent-source"]
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        source_errors = [f for f in findings if f.code == "CLAIM_SOURCE_MISSING"]
        assert len(source_errors) >= 1

    def test_missing_claim_relationship_detected(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Reference to non-existent claim in relationships produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["supports"] = ["NONEXISTENT-2026-001"]
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        rel_errors = [f for f in findings if f.code == "CLAIM_REL_MISSING"]
        assert len(rel_errors) >= 1

    def test_domain_mismatch_detected(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Mismatched domain in ID vs field produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["domain"] = "LABOR"  # But ID is TECH-2026-001
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        domain_errors = [f for f in findings if f.code == "CLAIM_DOMAIN_MISMATCH"]
        assert len(domain_errors) >= 1

    def test_missing_backlink_detected(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Source not listing claim in claims_extracted produces error."""
        # Source doesn't list the claim
        sample_source["claims_extracted"] = []
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        backlink_errors = [f for f in findings if f.code == "SOURCE_CLAIM_NOT_LISTED"]
        assert len(backlink_errors) >= 1

    def test_chain_credence_warning(self, initialized_db, temp_db_path, sample_claim, sample_source, sample_chain):
        """Chain credence exceeding MIN of claims produces warning."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.3
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        sample_chain["credence"] = 0.8  # Higher than claim credence
        add_chain(sample_chain, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        chain_warnings = [f for f in findings if f.code == "CHAIN_CREDENCE_EXCEEDS_MIN"]
        assert len(chain_warnings) >= 1

    def test_prediction_missing_for_p_claim(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """[P] type claim without prediction record produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["type"] = "[P]"
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Don't add prediction record

        findings = validate_db(temp_db_path)

        pred_errors = [f for f in findings if f.code == "PREDICTIONS_MISSING"]
        assert len(pred_errors) >= 1

    def test_empty_text_detected(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """Empty claim text produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["text"] = ""
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)

        text_errors = [f for f in findings if f.code == "CLAIM_TEXT_EMPTY"]
        assert len(text_errors) >= 1


class TestYamlValidation:
    """Tests for legacy YAML validation."""

    def test_valid_yaml_passes(self, sample_yaml_sources):
        """Valid YAML produces no errors."""
        findings = validate_yaml(sample_yaml_sources)

        errors = [f for f in findings if f.level == "ERROR"]
        # May have some warnings but should pass basic validation
        # The predictions.md might not exist yet
        critical_errors = [f for f in errors if "MISSING" not in f.code or "PREDICTION" not in f.code]
        assert len(critical_errors) == 0

    def test_missing_claims_file_detected(self, tmp_path):
        """Missing registry.yaml produces error."""
        findings = validate_yaml(tmp_path)

        assert any(f.code == "CLAIMS_MISSING" for f in findings)

    def test_invalid_claim_type_in_yaml(self, sample_yaml_sources):
        """Invalid claim type in YAML produces error."""
        import yaml

        registry_path = sample_yaml_sources / "claims" / "registry.yaml"
        with open(registry_path) as f:
            data = yaml.safe_load(f)

        data["claims"]["TECH-2026-001"]["type"] = "[INVALID]"

        with open(registry_path, "w") as f:
            yaml.dump(data, f)

        findings = validate_yaml(sample_yaml_sources)

        type_errors = [f for f in findings if f.code == "CLAIM_TYPE_INVALID"]
        assert len(type_errors) >= 1

    def test_invalid_confidence_in_yaml(self, sample_yaml_sources):
        """Invalid confidence in YAML produces error."""
        import yaml

        registry_path = sample_yaml_sources / "claims" / "registry.yaml"
        with open(registry_path) as f:
            data = yaml.safe_load(f)

        data["claims"]["TECH-2026-001"]["confidence"] = 2.0  # Invalid

        with open(registry_path, "w") as f:
            yaml.dump(data, f)

        findings = validate_yaml(sample_yaml_sources)

        conf_errors = [f for f in findings if f.code == "CLAIM_CREDENCE_INVALID"]
        assert len(conf_errors) >= 1

    def test_missing_source_reference_in_yaml(self, sample_yaml_sources):
        """Reference to non-existent source produces error."""
        import yaml

        registry_path = sample_yaml_sources / "claims" / "registry.yaml"
        with open(registry_path) as f:
            data = yaml.safe_load(f)

        data["claims"]["TECH-2026-001"]["source_ids"] = ["nonexistent"]

        with open(registry_path, "w") as f:
            yaml.dump(data, f)

        findings = validate_yaml(sample_yaml_sources)

        source_errors = [f for f in findings if f.code == "CLAIM_SOURCE_MISSING"]
        assert len(source_errors) >= 1


class TestFinding:
    """Tests for Finding dataclass."""

    def test_finding_creation(self):
        """Findings can be created."""
        f = Finding("ERROR", "TEST_CODE", "Test message")

        assert f.level == "ERROR"
        assert f.code == "TEST_CODE"
        assert f.message == "Test message"

    def test_finding_immutable(self):
        """Findings are immutable (frozen dataclass)."""
        f = Finding("ERROR", "TEST", "Message")

        with pytest.raises(AttributeError):
            f.level = "WARN"
