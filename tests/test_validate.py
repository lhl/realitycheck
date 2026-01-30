"""
Unit tests for scripts/validate.py

Tests cover:
- Database validation
- YAML validation (legacy mode)
- Error detection for various integrity issues
"""

import pytest
from pathlib import Path
import subprocess
import os

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
    add_analysis_log,
    add_evidence_link,
    add_reasoning_trail,
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
        # Add claim before source so add_claim can't auto-upsert the backlink.
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        sample_source["claims_extracted"] = []
        add_source(sample_source, initialized_db, generate_embedding=False)

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

        # Remove the auto-created prediction record.
        initialized_db.open_table("predictions").delete(f"claim_id = '{sample_claim['id']}'")

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


class TestValidateCLI:
    """Tests for validate CLI output."""

    def test_validate_cli_prints_remediation_commands(self, initialized_db, temp_db_path, sample_claim, sample_source):
        """CLI output includes actionable remediation commands for common failures."""
        # Create backlink mismatch: add claim before source so add_claim can't auto-upsert.
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        source = sample_source.copy()
        source["claims_extracted"] = []
        add_source(source, initialized_db, generate_embedding=False)

        # Create missing prediction stub: add [P] claim then delete the auto-created prediction.
        p_claim = sample_claim.copy()
        p_claim["id"] = "TECH-2026-002"
        p_claim["type"] = "[P]"
        add_claim(p_claim, initialized_db, generate_embedding=False)
        initialized_db.open_table("predictions").delete(f"claim_id = '{p_claim['id']}'")

        result = subprocess.run(
            [sys.executable, "scripts/validate.py", "--db-path", str(temp_db_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Validation should fail (exit 1) but output should be actionable.
        assert result.returncode == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "SOURCE_CLAIM_NOT_LISTED" in combined
        assert "PREDICTIONS_MISSING" in combined
        assert "rc-db repair" in combined

    def test_validate_cli_autodetects_project_db_from_subdir(self, tmp_path: Path):
        """When REALITYCHECK_DATA is unset, validate auto-detects a project DB from a subdirectory."""
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
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "validate.py")],
            env=env,
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")
        combined = (result.stdout or "") + (result.stderr or "")
        assert "OK:" in combined


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


class TestAnalysisLogsValidation:
    """Tests for analysis logs validation."""

    def test_analysis_log_completed_requires_source(self, initialized_db, temp_db_path, sample_source, sample_analysis_log):
        """Completed analysis logs require source_id to exist."""
        # Don't add the source - analysis log should fail validation
        log = sample_analysis_log.copy()
        log["status"] = "completed"
        log["source_id"] = "nonexistent-source"
        add_analysis_log(log, initialized_db)

        findings = validate_db(temp_db_path)
        source_errors = [f for f in findings if f.code == "ANALYSIS_SOURCE_MISSING"]
        assert len(source_errors) >= 1

    def test_analysis_log_draft_allows_missing_source(self, initialized_db, temp_db_path, sample_analysis_log):
        """Draft analysis logs don't require source_id to exist."""
        log = sample_analysis_log.copy()
        log["status"] = "draft"
        log["source_id"] = "nonexistent-source"
        add_analysis_log(log, initialized_db)

        findings = validate_db(temp_db_path)
        source_errors = [f for f in findings if f.code == "ANALYSIS_SOURCE_MISSING"]
        assert len(source_errors) == 0

    def test_analysis_log_claims_must_exist_when_not_draft(self, initialized_db, temp_db_path, sample_source, sample_analysis_log):
        """Non-draft analysis logs require claims to exist."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        log = sample_analysis_log.copy()
        log["status"] = "completed"
        log["claims_extracted"] = ["NONEXISTENT-2026-001"]
        add_analysis_log(log, initialized_db)

        findings = validate_db(temp_db_path)
        claim_errors = [f for f in findings if f.code == "ANALYSIS_CLAIM_MISSING"]
        assert len(claim_errors) >= 1

    def test_analysis_log_draft_allows_missing_claims(self, initialized_db, temp_db_path, sample_analysis_log):
        """Draft analysis logs allow missing claims."""
        log = sample_analysis_log.copy()
        log["status"] = "draft"
        log["claims_extracted"] = ["NONEXISTENT-2026-001"]
        add_analysis_log(log, initialized_db)

        findings = validate_db(temp_db_path)
        claim_errors = [f for f in findings if f.code == "ANALYSIS_CLAIM_MISSING"]
        assert len(claim_errors) == 0

    def test_analysis_log_valid_json_stages(self, initialized_db, temp_db_path, sample_source, sample_analysis_log):
        """Valid JSON in stages_json passes."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        log = sample_analysis_log.copy()
        log["stages_json"] = '{"descriptive": {"tokens": 100}}'
        add_analysis_log(log, initialized_db)

        findings = validate_db(temp_db_path)
        json_errors = [f for f in findings if f.code == "ANALYSIS_STAGES_INVALID_JSON"]
        assert len(json_errors) == 0

    def test_analysis_log_invalid_json_stages_detected(self, initialized_db, temp_db_path, sample_source, sample_analysis_log):
        """Invalid JSON in stages_json produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        log = sample_analysis_log.copy()
        log["stages_json"] = "not valid json {"
        add_analysis_log(log, initialized_db)

        findings = validate_db(temp_db_path)
        json_errors = [f for f in findings if f.code == "ANALYSIS_STAGES_INVALID_JSON"]
        assert len(json_errors) >= 1

    def test_analysis_log_negative_duration_detected(self, initialized_db, temp_db_path, sample_source, sample_analysis_log):
        """Negative duration produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        log = sample_analysis_log.copy()
        log["duration_seconds"] = -100
        add_analysis_log(log, initialized_db)

        findings = validate_db(temp_db_path)
        duration_errors = [f for f in findings if f.code == "ANALYSIS_DURATION_NEGATIVE"]
        assert len(duration_errors) >= 1

    def test_analysis_log_negative_cost_detected(self, initialized_db, temp_db_path, sample_source, sample_analysis_log):
        """Negative cost produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        log = sample_analysis_log.copy()
        log["cost_usd"] = -5.0
        add_analysis_log(log, initialized_db)

        findings = validate_db(temp_db_path)
        cost_errors = [f for f in findings if f.code == "ANALYSIS_COST_NEGATIVE"]
        assert len(cost_errors) >= 1


# =============================================================================
# Evidence Links Validation Tests
# =============================================================================


class TestEvidenceLinksValidation:
    """Tests for evidence links referential integrity validation."""

    def test_evidence_link_missing_claim_errors(self, initialized_db, temp_db_path, sample_source):
        """Evidence link referencing non-existent claim produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        # Add evidence link with non-existent claim (bypass validation by direct insert)
        link = {
            "id": "EVLINK-2026-001",
            "claim_id": "NONEXISTENT-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "status": "active",
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("evidence_links")
        tbl.add([link])

        findings = validate_db(temp_db_path)
        errors = [f for f in findings if f.code == "EVLINK_CLAIM_MISSING"]
        assert len(errors) >= 1

    def test_evidence_link_missing_source_errors(self, initialized_db, temp_db_path, sample_claim):
        """Evidence link referencing non-existent source produces error."""
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add evidence link with non-existent source (bypass validation)
        link = {
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "nonexistent-source",
            "direction": "supports",
            "status": "active",
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("evidence_links")
        tbl.add([link])

        findings = validate_db(temp_db_path)
        errors = [f for f in findings if f.code == "EVLINK_SOURCE_MISSING"]
        assert len(errors) >= 1

    def test_evidence_link_invalid_direction_errors(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Evidence link with invalid direction produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add evidence link with invalid direction (bypass validation)
        link = {
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "invalid_direction",
            "status": "active",
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("evidence_links")
        tbl.add([link])

        findings = validate_db(temp_db_path)
        errors = [f for f in findings if f.code == "EVLINK_DIRECTION_INVALID"]
        assert len(errors) >= 1

    def test_evidence_link_invalid_status_errors(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Evidence link with invalid status produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add evidence link with invalid status (bypass validation)
        link = {
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "status": "invalid_status",
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("evidence_links")
        tbl.add([link])

        findings = validate_db(temp_db_path)
        errors = [f for f in findings if f.code == "EVLINK_STATUS_INVALID"]
        assert len(errors) >= 1

    def test_evidence_link_supersedes_nonexistent_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Evidence link with non-existent supersedes_id produces warning."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add evidence link with non-existent supersedes_id (bypass validation)
        link = {
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "status": "active",
            "supersedes_id": "EVLINK-9999-999",  # Non-existent
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("evidence_links")
        tbl.add([link])

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "EVLINK_SUPERSEDES_MISSING"]
        assert len(warns) >= 1


# =============================================================================
# Reasoning Trails Validation Tests
# =============================================================================


class TestReasoningTrailsValidation:
    """Tests for reasoning trails referential integrity validation."""

    def test_reasoning_trail_missing_claim_errors(self, initialized_db, temp_db_path):
        """Reasoning trail referencing non-existent claim produces error."""
        # Add reasoning trail with non-existent claim (bypass validation)
        trail = {
            "id": "REASON-2026-001",
            "claim_id": "NONEXISTENT-2026-001",
            "credence_at_time": 0.75,
            "evidence_level_at_time": "E2",
            "reasoning_text": "Test reasoning",
            "status": "active",
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("reasoning_trails")
        tbl.add([trail])

        findings = validate_db(temp_db_path)
        errors = [f for f in findings if f.code == "REASONING_CLAIM_MISSING"]
        assert len(errors) >= 1

    def test_reasoning_trail_missing_evidence_link_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Reasoning trail referencing non-existent evidence link produces warning."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add reasoning trail with non-existent evidence link (bypass validation)
        trail = {
            "id": "REASON-2026-001",
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.75,
            "evidence_level_at_time": "E2",
            "reasoning_text": "Test reasoning",
            "supporting_evidence": ["EVLINK-9999-999"],  # Non-existent
            "status": "active",
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("reasoning_trails")
        tbl.add([trail])

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "REASONING_EVLINK_MISSING"]
        assert len(warns) >= 1

    def test_reasoning_trail_credence_mismatch_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Reasoning trail credence differing from current claim credence warns."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.80
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add trail with different credence
        trail = {
            "id": "REASON-2026-001",
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.60,  # Different from claim's 0.80
            "evidence_level_at_time": "E2",
            "reasoning_text": "Test reasoning",
            "status": "active",
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("reasoning_trails")
        tbl.add([trail])

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "REASONING_CREDENCE_STALE"]
        assert len(warns) >= 1

    def test_reasoning_trail_evidence_level_mismatch_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Reasoning trail evidence level differing from current claim warns."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["evidence_level"] = "E1"
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add trail with different evidence level
        trail = {
            "id": "REASON-2026-001",
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.75,
            "evidence_level_at_time": "E3",  # Different from claim's E1
            "reasoning_text": "Test reasoning",
            "status": "active",
            "created_by": "test",
            "created_at": "2026-01-30T10:00:00Z",
        }
        tbl = initialized_db.open_table("reasoning_trails")
        tbl.add([trail])

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "REASONING_EVIDENCE_STALE"]
        assert len(warns) >= 1


# =============================================================================
# High Credence Backing Validation Tests
# =============================================================================


class TestHighCredenceBackingValidation:
    """Tests for high credence backing requirements."""

    def test_high_credence_no_backing_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Claim with credence ≥0.7 and no evidence links produces warning."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.80
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "HIGH_CREDENCE_NO_BACKING"]
        assert len(warns) >= 1
        assert warns[0].level == "WARN"

    def test_high_credence_with_backing_passes(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link):
        """Claim with credence ≥0.7 and evidence link passes."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.80
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "HIGH_CREDENCE_NO_BACKING"]
        assert len(warns) == 0

    def test_e1_e2_no_backing_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Claim with E1/E2 evidence level and no evidence links produces warning."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["evidence_level"] = "E1"
        sample_claim["credence"] = 0.50  # Below 0.7 but E1
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "HIGH_CREDENCE_NO_BACKING"]
        assert len(warns) >= 1

    def test_e1_e2_with_backing_passes(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link):
        """Claim with E1/E2 evidence level and evidence link passes."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["evidence_level"] = "E1"
        sample_claim["credence"] = 0.50
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "HIGH_CREDENCE_NO_BACKING"]
        assert len(warns) == 0

    def test_high_credence_backing_requires_location_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """High credence claim with evidence link missing location warns (soft)."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.80
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add evidence link without location
        link = {
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "created_by": "test",
            # No location field
        }
        add_evidence_link(link, db=initialized_db)

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "HIGH_CREDENCE_MISSING_LOCATION"]
        assert len(warns) >= 1

    def test_high_credence_backing_requires_reasoning_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """High credence claim with evidence link missing reasoning warns (soft)."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.80
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add evidence link with location but without reasoning
        link = {
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "location": "Table 3",
            "created_by": "test",
            # No reasoning field
        }
        add_evidence_link(link, db=initialized_db)

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "HIGH_CREDENCE_MISSING_REASONING"]
        assert len(warns) >= 1

    def test_strict_mode_errors_instead_of_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """In strict mode, high credence without backing produces error."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.80
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path, strict=True)
        errors = [f for f in findings if f.code == "HIGH_CREDENCE_NO_BACKING"]
        assert len(errors) >= 1
        assert errors[0].level == "ERROR"

    def test_low_credence_no_backing_passes(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """Claim with credence <0.7 and E3-E6 passes without evidence links."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.50
        sample_claim["evidence_level"] = "E4"
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "HIGH_CREDENCE_NO_BACKING"]
        assert len(warns) == 0

    def test_high_credence_missing_reasoning_trail_warns(self, initialized_db, temp_db_path, sample_source, sample_claim):
        """High credence claim with evidence but no reasoning trail warns."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.80
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add evidence link (satisfies evidence requirement)
        link = {
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "location": "Table 3",
            "reasoning": "Direct support",
            "created_by": "test",
        }
        add_evidence_link(link, db=initialized_db)
        # No reasoning trail added

        findings = validate_db(temp_db_path)
        warns = [f for f in findings if f.code == "HIGH_CREDENCE_NO_REASONING_TRAIL"]
        assert len(warns) >= 1
        assert "reasoning trail" in warns[0].message.lower()

    def test_high_credence_full_provenance_passes(self, initialized_db, temp_db_path, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """High credence claim with evidence + reasoning trail passes."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        sample_claim["credence"] = 0.80
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, db=initialized_db)
        add_reasoning_trail(sample_reasoning_trail, db=initialized_db)

        findings = validate_db(temp_db_path)
        backing_warns = [f for f in findings if f.code == "HIGH_CREDENCE_NO_BACKING"]
        trail_warns = [f for f in findings if f.code == "HIGH_CREDENCE_NO_REASONING_TRAIL"]
        assert len(backing_warns) == 0
        assert len(trail_warns) == 0
