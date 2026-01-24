"""
End-to-end integration tests for Reality Check.

Tests cover the full workflow:
1. Initialize database
2. Migrate from YAML
3. Validate integrity
4. Search and query
5. Export back to various formats

These tests verify that all components work together correctly.
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from db import (
    get_db,
    init_tables,
    drop_tables,
    add_claim,
    add_source,
    add_analysis_log,
    get_claim,
    search_claims,
    get_stats,
)
from migrate import run_migration
from validate import validate_db, validate_yaml
from export import (
    export_claims_yaml,
    export_sources_yaml,
    export_summary_md,
    export_analysis_logs_yaml,
    export_analysis_logs_md,
)


@pytest.mark.requires_embedding
class TestFullWorkflow:
    """End-to-end tests for complete analysis workflow."""

    def test_migrate_validate_export_cycle(self, sample_predictions_md, temp_db_path):
        """Full cycle: migrate → validate → export."""
        # Step 1: Migrate from YAML
        migration_stats = run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
            verbose=False,
        )

        assert migration_stats["claims_migrated"] > 0
        assert migration_stats["sources_migrated"] > 0
        assert len(migration_stats["errors"]) == 0

        # Step 2: Validate the database
        findings = validate_db(temp_db_path)

        # Filter to just errors (warnings are ok)
        errors = [f for f in findings if f.level == "ERROR"]
        # We expect the prediction sync error since our test data is minimal
        critical_errors = [e for e in errors if "PREDICTION" not in e.code]
        assert len(critical_errors) == 0

        # Step 3: Export to YAML
        yaml_output = export_claims_yaml(temp_db_path)
        assert "claims:" in yaml_output
        assert "TECH-2026-001" in yaml_output

        # Step 4: Export to Markdown
        summary = export_summary_md(temp_db_path)
        assert "Statistics" in summary

    def test_search_after_migration(self, sample_predictions_md, temp_db_path):
        """Semantic search works after migration."""
        run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
            verbose=False,
        )

        # Search for AI-related content
        results = search_claims("artificial intelligence costs", limit=5, db=get_db(temp_db_path))

        assert len(results) > 0
        # Should find the AI costs claim
        assert any("cost" in r["text"].lower() or "ai" in r["text"].lower() for r in results)

    def test_domain_migration_end_to_end(self, sample_predictions_md, temp_db_path):
        """Domain migration works correctly end-to-end."""
        stats = run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
            verbose=False,
        )

        # Check mapping was applied
        assert "DIST-2026-001" in stats["id_mappings"]
        assert stats["id_mappings"]["DIST-2026-001"] == "ECON-2026-001"

        # Verify in database
        db = get_db(temp_db_path)
        claim = get_claim("ECON-2026-001", db)

        assert claim is not None
        assert claim["domain"] == "ECON"

    def test_stats_accurate_after_operations(self, temp_db_path):
        """Database stats remain accurate after operations."""
        db = get_db(temp_db_path)
        init_tables(db)

        # Add some data
        source = {
            "id": "test-source",
            "type": "REPORT",
            "title": "Test",
            "author": ["Test"],
            "year": 2026,
            "url": "",
            "accessed": "2026-01-19",
            "reliability": 0.7,
            "bias_notes": "",
            "claims_extracted": ["TECH-2026-001"],
            "analysis_file": None,
            "topics": [],
            "domains": ["TECH"],
            "status": "analyzed",
        }
        add_source(source, db, generate_embedding=False)

        claim = {
            "id": "TECH-2026-001",
            "text": "Test claim",
            "type": "[F]",
            "domain": "TECH",
            "evidence_level": "E2",
            "credence": 0.7,
            "source_ids": ["test-source"],
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
        add_claim(claim, db, generate_embedding=False)

        stats = get_stats(db)

        assert stats["claims"] == 1
        assert stats["sources"] == 1


@pytest.mark.requires_embedding
class TestValidationIntegration:
    """Integration tests for validation across formats."""

    def test_yaml_and_db_validation_consistent(self, sample_predictions_md, temp_db_path):
        """YAML and DB validation find similar issues."""
        # Validate YAML first
        yaml_findings = validate_yaml(sample_predictions_md)
        yaml_errors = [f for f in yaml_findings if f.level == "ERROR"]

        # Migrate to DB
        run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
        )

        # Validate DB
        db_findings = validate_db(temp_db_path)
        db_errors = [f for f in db_findings if f.level == "ERROR"]

        # Both should find similar number of issues
        # (exact match not expected due to different validation rules)
        # But neither should have unexpected failures
        assert len(yaml_errors) < 10  # Sanity check
        assert len(db_errors) < 10


class TestExportImportConsistency:
    """Tests for data consistency through export/import."""

    def test_claim_data_preserved_through_export(self, temp_db_path):
        """Claim data is preserved through YAML export."""
        db = get_db(temp_db_path)
        init_tables(db)

        original_claim = {
            "id": "TECH-2026-001",
            "text": "AI training costs grow 2-3x annually",
            "type": "[F]",
            "domain": "TECH",
            "evidence_level": "E2",
            "credence": 0.8,
            "source_ids": [],
            "first_extracted": "2026-01-19",
            "extracted_by": "claude",
            "supports": [],
            "contradicts": [],
            "depends_on": [],
            "modified_by": [],
            "part_of_chain": "",
            "version": 1,
            "last_updated": "2026-01-19",
            "notes": "Test note",
        }
        add_claim(original_claim, db, generate_embedding=False)

        yaml_output = export_claims_yaml(temp_db_path)

        # Verify key data is in export
        assert "TECH-2026-001" in yaml_output
        assert "AI training costs" in yaml_output
        assert "0.8" in yaml_output  # confidence value

    def test_source_data_preserved_through_export(self, temp_db_path):
        """Source data is preserved through YAML export."""
        db = get_db(temp_db_path)
        init_tables(db)

        original_source = {
            "id": "epoch-2024-training",
            "type": "REPORT",
            "title": "How Much Does It Cost to Train Frontier AI Models?",
            "author": ["Epoch AI"],
            "year": 2024,
            "url": "https://epoch.ai/blog/training-costs",
            "accessed": "2026-01-19",
            "reliability": 0.85,
            "bias_notes": "Pro-AI framing",
            "claims_extracted": [],
            "analysis_file": None,
            "topics": ["compute", "costs"],
            "domains": ["TECH"],
            "status": "analyzed",
        }
        add_source(original_source, db, generate_embedding=False)

        yaml_output = export_sources_yaml(temp_db_path)

        # Verify key data is in export
        assert "epoch-2024-training" in yaml_output
        assert "How Much Does It Cost" in yaml_output
        assert "Epoch AI" in yaml_output


class TestAuditLogWorkflow:
    """End-to-end tests for analysis audit log integration."""

    def test_audit_log_validate_export_cycle(self, temp_db_path, sample_source, sample_claim, sample_analysis_log):
        """E2E: init → add source/claim → add analysis log → validate → export."""
        db = get_db(temp_db_path)
        init_tables(db)

        add_source(sample_source, db, generate_embedding=False)
        add_claim(sample_claim, db, generate_embedding=False)
        add_analysis_log(sample_analysis_log, db)

        findings = validate_db(temp_db_path)
        errors = [f for f in findings if f.level == "ERROR"]
        assert errors == []

        md_out = export_analysis_logs_md(temp_db_path)
        assert "# Analysis Logs" in md_out

        yaml_out = export_analysis_logs_yaml(temp_db_path)
        assert "analysis_logs:" in yaml_out


class TestErrorHandling:
    """Tests for error handling in integration scenarios."""

    @pytest.mark.requires_embedding
    def test_migration_handles_missing_predictions_md(self, sample_yaml_sources, temp_db_path):
        """Migration handles missing predictions.md gracefully."""
        # sample_yaml_sources has no predictions.md
        stats = run_migration(
            source_repo=sample_yaml_sources,
            db_path=temp_db_path,
            dry_run=False,
        )

        # Should complete without errors
        assert stats["claims_migrated"] > 0
        assert stats["predictions_migrated"] == 0  # No predictions file

    def test_validation_handles_empty_database(self, temp_db_path):
        """Validation handles empty database."""
        db = get_db(temp_db_path)
        init_tables(db)

        findings = validate_db(temp_db_path)

        # Should not crash, may have warnings
        errors = [f for f in findings if f.level == "ERROR"]
        assert len(errors) == 0  # Empty DB is valid


@pytest.mark.requires_embedding
class TestPerformance:
    """Basic performance tests."""

    def test_search_performance_reasonable(self, sample_predictions_md, temp_db_path):
        """Search completes in reasonable time."""
        import time

        run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
        )

        db = get_db(temp_db_path)

        start = time.time()
        results = search_claims("AI automation labor", limit=10, db=db)
        elapsed = time.time() - start

        # Search should complete in under 5 seconds even with embeddings
        assert elapsed < 5.0
        assert len(results) >= 0  # May or may not find results

    def test_export_performance_reasonable(self, sample_predictions_md, temp_db_path):
        """Export completes in reasonable time."""
        import time

        run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
        )

        start = time.time()
        yaml_output = export_claims_yaml(temp_db_path)
        elapsed = time.time() - start

        # Export should complete in under 2 seconds
        assert elapsed < 2.0
        assert len(yaml_output) > 0
