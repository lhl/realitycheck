"""
Unit tests for scripts/migrate.py

Tests cover:
- ID mapping generation
- Domain migration
- Claim reference updates
- Full migration workflow
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from migrate import (
    build_id_mapping,
    migrate_domain,
    update_claim_references,
    migrate_claim,
    migrate_source,
    migrate_chain,
    run_migration,
)
from db import get_db, list_claims, list_sources, list_chains, list_predictions


class TestDomainMigration:
    """Tests for domain name migration."""

    def test_migrate_value_to_econ(self):
        """VALUE domain migrates to ECON."""
        assert migrate_domain("VALUE") == "ECON"

    def test_migrate_dist_to_econ(self):
        """DIST domain migrates to ECON."""
        assert migrate_domain("DIST") == "ECON"

    def test_migrate_social_to_soc(self):
        """SOCIAL domain migrates to SOC."""
        assert migrate_domain("SOCIAL") == "SOC"

    def test_unchanged_domains_preserved(self):
        """Other domains are unchanged."""
        assert migrate_domain("TECH") == "TECH"
        assert migrate_domain("LABOR") == "LABOR"
        assert migrate_domain("GOV") == "GOV"
        assert migrate_domain("RESOURCE") == "RESOURCE"
        assert migrate_domain("TRANS") == "TRANS"
        assert migrate_domain("META") == "META"


class TestIdMapping:
    """Tests for claim ID mapping generation."""

    def test_dist_claims_renumbered_to_econ(self):
        """DIST claims get new ECON IDs."""
        claims = {
            "DIST-2026-001": {"domain": "DIST"},
            "DIST-2026-002": {"domain": "DIST"},
        }
        mapping = build_id_mapping(claims)

        assert mapping["DIST-2026-001"] == "ECON-2026-001"
        assert mapping["DIST-2026-002"] == "ECON-2026-002"

    def test_value_claims_continue_after_dist(self):
        """VALUE claims continue numbering after DIST max."""
        claims = {
            "DIST-2026-001": {"domain": "DIST"},
            "DIST-2026-002": {"domain": "DIST"},
            "VALUE-2026-001": {"domain": "VALUE"},
        }
        mapping = build_id_mapping(claims)

        # DIST gets 1-2, VALUE continues at 3
        assert mapping["VALUE-2026-001"] == "ECON-2026-003"

    def test_social_renamed_to_soc(self):
        """SOCIAL claims renamed to SOC keeping number."""
        claims = {
            "SOCIAL-2026-001": {"domain": "SOCIAL"},
            "SOCIAL-2026-002": {"domain": "SOCIAL"},
        }
        mapping = build_id_mapping(claims)

        assert mapping["SOCIAL-2026-001"] == "SOC-2026-001"
        assert mapping["SOCIAL-2026-002"] == "SOC-2026-002"

    def test_other_domains_unchanged(self):
        """Non-migrated domains keep original IDs."""
        claims = {
            "TECH-2026-001": {"domain": "TECH"},
            "LABOR-2026-001": {"domain": "LABOR"},
        }
        mapping = build_id_mapping(claims)

        assert mapping["TECH-2026-001"] == "TECH-2026-001"
        assert mapping["LABOR-2026-001"] == "LABOR-2026-001"

    def test_deterministic_ordering(self):
        """ID mapping is deterministic regardless of input order."""
        claims1 = {
            "VALUE-2026-001": {"domain": "VALUE"},
            "DIST-2026-001": {"domain": "DIST"},
        }
        claims2 = {
            "DIST-2026-001": {"domain": "DIST"},
            "VALUE-2026-001": {"domain": "VALUE"},
        }

        mapping1 = build_id_mapping(claims1)
        mapping2 = build_id_mapping(claims2)

        assert mapping1 == mapping2


class TestClaimReferenceUpdates:
    """Tests for updating claim references with new IDs."""

    def test_supports_updated(self):
        """supports field references are updated."""
        claim = {
            "supports": ["DIST-2026-001", "TECH-2026-001"],
            "contradicts": [],
            "depends_on": [],
            "modified_by": [],
        }
        mapping = {"DIST-2026-001": "ECON-2026-001"}

        updated = update_claim_references(claim, mapping)

        assert "ECON-2026-001" in updated["supports"]
        assert "TECH-2026-001" in updated["supports"]

    def test_contradicts_updated(self):
        """contradicts field references are updated."""
        claim = {
            "supports": [],
            "contradicts": ["VALUE-2026-001"],
            "depends_on": [],
            "modified_by": [],
        }
        mapping = {"VALUE-2026-001": "ECON-2026-003"}

        updated = update_claim_references(claim, mapping)

        assert updated["contradicts"] == ["ECON-2026-003"]

    def test_depends_on_updated(self):
        """depends_on field references are updated."""
        claim = {
            "supports": [],
            "contradicts": [],
            "depends_on": ["SOCIAL-2026-001"],
            "modified_by": [],
        }
        mapping = {"SOCIAL-2026-001": "SOC-2026-001"}

        updated = update_claim_references(claim, mapping)

        assert updated["depends_on"] == ["SOC-2026-001"]

    def test_original_claim_not_mutated(self):
        """Original claim dict is not modified."""
        claim = {
            "supports": ["DIST-2026-001"],
            "contradicts": [],
            "depends_on": [],
            "modified_by": [],
        }
        mapping = {"DIST-2026-001": "ECON-2026-001"}

        update_claim_references(claim, mapping)

        # Original should be unchanged
        assert claim["supports"] == ["DIST-2026-001"]


class TestMigrateClaim:
    """Tests for full claim migration."""

    def test_confidence_renamed_to_credence(self):
        """confidence field becomes credence."""
        claim = {
            "text": "Test claim",
            "type": "[T]",
            "domain": "TECH",
            "evidence_level": "E3",
            "confidence": 0.75,
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
        }
        mapping = {"TECH-2026-001": "TECH-2026-001"}

        migrated = migrate_claim("TECH-2026-001", claim, mapping)

        assert "credence" in migrated
        assert migrated["credence"] == 0.75
        assert "confidence" not in migrated

    def test_domain_migrated(self):
        """Domain is updated for migrated claims."""
        claim = {
            "text": "Test claim",
            "type": "[T]",
            "domain": "DIST",
            "evidence_level": "E3",
            "confidence": 0.5,
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
        }
        mapping = {"DIST-2026-001": "ECON-2026-001"}

        migrated = migrate_claim("DIST-2026-001", claim, mapping)

        assert migrated["domain"] == "ECON"
        assert migrated["id"] == "ECON-2026-001"

    def test_new_v1_fields_added(self):
        """New v1.0 fields are added."""
        claim = {
            "text": "Test claim",
            "type": "[T]",
            "domain": "TECH",
            "evidence_level": "E3",
            "confidence": 0.5,
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
        }
        mapping = {"TECH-2026-001": "TECH-2026-001"}

        migrated = migrate_claim("TECH-2026-001", claim, mapping)

        assert "operationalization" in migrated
        assert "assumptions" in migrated
        assert "falsifiers" in migrated


class TestMigrateSource:
    """Tests for source migration."""

    def test_claims_extracted_updated(self):
        """claims_extracted references are updated."""
        source = {
            "type": "REPORT",
            "title": "Test",
            "author": ["Test"],
            "year": 2026,
            "url": "",
            "accessed": "2026-01-19",
            "reliability": 0.7,
            "bias_notes": "",
            "claims_extracted": ["DIST-2026-001", "TECH-2026-001"],
            "analysis_file": "",
            "topics": [],
            "domains": ["DIST", "TECH"],
        }
        mapping = {"DIST-2026-001": "ECON-2026-001"}

        migrated = migrate_source("test-source", source, mapping)

        assert "ECON-2026-001" in migrated["claims_extracted"]
        assert "TECH-2026-001" in migrated["claims_extracted"]

    def test_domains_migrated(self):
        """Domain list is updated."""
        source = {
            "type": "REPORT",
            "title": "Test",
            "author": ["Test"],
            "year": 2026,
            "url": "",
            "accessed": "2026-01-19",
            "reliability": 0.7,
            "bias_notes": "",
            "claims_extracted": [],
            "analysis_file": "",
            "topics": [],
            "domains": ["DIST", "VALUE", "SOCIAL"],
        }
        mapping = {}

        migrated = migrate_source("test-source", source, mapping)

        # All three should become ECON or SOC
        assert "ECON" in migrated["domains"]
        assert "SOC" in migrated["domains"]
        assert "DIST" not in migrated["domains"]
        assert "VALUE" not in migrated["domains"]


class TestMigrateChain:
    """Tests for chain migration."""

    def test_chain_claims_updated(self):
        """Chain claim IDs are updated."""
        chain = {
            "name": "Test Chain",
            "thesis": "Test thesis",
            "confidence": 0.5,
            "claims": ["DIST-2026-001", "TECH-2026-001"],
            "analysis_file": "",
            "weakest_link": "DIST-2026-001",
        }
        mapping = {"DIST-2026-001": "ECON-2026-001"}

        migrated = migrate_chain("CHAIN-2026-001", chain, mapping)

        assert "ECON-2026-001" in migrated["claims"]
        assert "TECH-2026-001" in migrated["claims"]

    def test_weakest_link_updated(self):
        """Weakest link reference is updated."""
        chain = {
            "name": "Test Chain",
            "thesis": "Test thesis",
            "confidence": 0.5,
            "claims": ["DIST-2026-001"],
            "analysis_file": "",
            "weakest_link": "DIST-2026-001 (weak assumption)",
        }
        mapping = {"DIST-2026-001": "ECON-2026-001"}

        migrated = migrate_chain("CHAIN-2026-001", chain, mapping)

        assert "ECON-2026-001" in migrated["weakest_link"]

    def test_confidence_renamed_to_credence(self):
        """Chain confidence becomes credence."""
        chain = {
            "name": "Test Chain",
            "thesis": "Test thesis",
            "confidence": 0.4,
            "claims": [],
            "analysis_file": "",
            "weakest_link": "",
        }
        mapping = {}

        migrated = migrate_chain("CHAIN-2026-001", chain, mapping)

        assert migrated["credence"] == 0.4


@pytest.mark.requires_embedding
class TestFullMigration:
    """Integration tests for full migration workflow."""

    def test_dry_run_does_not_modify_db(self, sample_predictions_md, temp_db_path):
        """Dry run doesn't create database."""
        stats = run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=True,
        )

        # Database should not exist or be empty
        assert stats["claims_migrated"] == 0
        assert stats["sources_migrated"] == 0

    def test_full_migration_creates_records(self, sample_predictions_md, temp_db_path):
        """Full migration creates all records."""
        stats = run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
            verbose=False,
        )

        assert stats["claims_migrated"] == 4  # TECH-001, TECH-002, DIST-001, VALUE-001
        assert stats["sources_migrated"] == 1
        assert stats["chains_migrated"] == 1
        assert stats["predictions_migrated"] == 1

    def test_migration_applies_id_mapping(self, sample_predictions_md, temp_db_path):
        """Migration correctly applies ID mapping."""
        run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
            verbose=False,
        )

        db = get_db(temp_db_path)
        claims = list_claims(limit=100, db=db)
        claim_ids = [c["id"] for c in claims]

        # DIST should be migrated to ECON
        assert "ECON-2026-001" in claim_ids
        assert "DIST-2026-001" not in claim_ids

        # VALUE should be migrated to ECON (continuing after DIST)
        assert "ECON-2026-002" in claim_ids
        assert "VALUE-2026-001" not in claim_ids

    def test_migration_updates_references(self, sample_predictions_md, temp_db_path):
        """Migration updates cross-references."""
        run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
            verbose=False,
        )

        db = get_db(temp_db_path)
        sources = list_sources(db=db)

        # Source should have updated claim IDs
        source = sources[0]
        assert "ECON-2026-001" in source["claims_extracted"]
        assert "ECON-2026-002" in source["claims_extracted"]

    def test_migration_extracts_predictions(self, sample_predictions_md, temp_db_path):
        """Migration extracts predictions from markdown."""
        run_migration(
            source_repo=sample_predictions_md,
            db_path=temp_db_path,
            dry_run=False,
            verbose=False,
        )

        db = get_db(temp_db_path)
        predictions = list_predictions(db=db)

        assert len(predictions) == 1
        assert predictions[0]["claim_id"] == "TECH-2026-002"
        assert predictions[0]["status"] == "[P→]"
