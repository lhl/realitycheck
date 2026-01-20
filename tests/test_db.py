"""
Unit tests for scripts/db.py

Tests cover:
- Database initialization
- CRUD operations for all tables
- Semantic search functionality
- Statistics and utilities
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
    get_claim,
    update_claim,
    delete_claim,
    list_claims,
    search_claims,
    get_related_claims,
    add_source,
    get_source,
    list_sources,
    search_sources,
    add_chain,
    get_chain,
    list_chains,
    add_prediction,
    get_prediction,
    list_predictions,
    add_contradiction,
    list_contradictions,
    add_definition,
    get_definition,
    list_definitions,
    get_stats,
    VALID_DOMAINS,
    DOMAIN_MIGRATION,
)


class TestDatabaseInitialization:
    """Tests for database setup and teardown."""

    def test_get_db_creates_directory(self, tmp_path: Path):
        """Database directory is created if it doesn't exist."""
        db_path = tmp_path / "subdir" / "test.lance"
        db = get_db(db_path)
        assert db is not None

    def test_init_tables_creates_all_tables(self, temp_db_path: Path):
        """All expected tables are created."""
        db = get_db(temp_db_path)
        tables = init_tables(db)

        expected_tables = {"claims", "sources", "chains", "predictions", "contradictions", "definitions"}
        assert set(tables.keys()) == expected_tables

    def test_drop_tables_removes_all_tables(self, initialized_db):
        """All tables are dropped."""
        drop_tables(initialized_db)
        # After dropping, list_tables should be empty or tables recreated
        # We verify by checking stats returns zeros
        stats = get_stats(initialized_db)
        for count in stats.values():
            assert count == 0


class TestClaimsCRUD:
    """Tests for claim operations."""

    def test_add_claim(self, initialized_db, sample_claim):
        """Claims can be added."""
        claim_id = add_claim(sample_claim, initialized_db, generate_embedding=False)
        assert claim_id == "TECH-2026-001"

    @pytest.mark.requires_embedding
    def test_add_claim_generates_embedding(self, initialized_db, sample_claim):
        """Embeddings are generated when requested."""
        add_claim(sample_claim, initialized_db, generate_embedding=True)
        retrieved = get_claim("TECH-2026-001", initialized_db)
        assert retrieved is not None
        assert retrieved.get("embedding") is not None
        assert len(retrieved["embedding"]) > 0

    def test_get_claim_returns_claim(self, initialized_db, sample_claim):
        """Claims can be retrieved by ID."""
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        retrieved = get_claim("TECH-2026-001", initialized_db)

        assert retrieved is not None
        assert retrieved["id"] == "TECH-2026-001"
        assert retrieved["text"] == sample_claim["text"]
        assert retrieved["credence"] == pytest.approx(0.75, rel=0.01)

    def test_get_claim_returns_none_for_missing(self, initialized_db):
        """None is returned for non-existent claims."""
        result = get_claim("NONEXISTENT-2026-001", initialized_db)
        assert result is None

    def test_update_claim(self, initialized_db, sample_claim):
        """Claims can be updated."""
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        update_claim("TECH-2026-001", {"credence": 0.9, "notes": "Updated"}, initialized_db)

        retrieved = get_claim("TECH-2026-001", initialized_db)
        assert retrieved["credence"] == pytest.approx(0.9, rel=0.01)
        assert retrieved["notes"] == "Updated"
        assert retrieved["version"] == 2  # Version incremented

    def test_delete_claim(self, initialized_db, sample_claim):
        """Claims can be deleted."""
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        delete_claim("TECH-2026-001", initialized_db)

        result = get_claim("TECH-2026-001", initialized_db)
        assert result is None

    def test_list_claims_returns_all(self, initialized_db, sample_claim):
        """All claims are listed."""
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add another claim
        claim2 = sample_claim.copy()
        claim2["id"] = "LABOR-2026-001"
        claim2["domain"] = "LABOR"
        add_claim(claim2, initialized_db, generate_embedding=False)

        claims = list_claims(db=initialized_db)
        assert len(claims) == 2

    def test_list_claims_filters_by_domain(self, initialized_db, sample_claim):
        """Claims can be filtered by domain."""
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        claim2 = sample_claim.copy()
        claim2["id"] = "LABOR-2026-001"
        claim2["domain"] = "LABOR"
        add_claim(claim2, initialized_db, generate_embedding=False)

        tech_claims = list_claims(domain="TECH", db=initialized_db)
        assert len(tech_claims) == 1
        assert tech_claims[0]["domain"] == "TECH"

    def test_list_claims_filters_by_type(self, initialized_db, sample_claim):
        """Claims can be filtered by type."""
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        claim2 = sample_claim.copy()
        claim2["id"] = "TECH-2026-002"
        claim2["type"] = "[P]"
        add_claim(claim2, initialized_db, generate_embedding=False)

        predictions = list_claims(claim_type="[P]", db=initialized_db)
        assert len(predictions) == 1
        assert predictions[0]["type"] == "[P]"


@pytest.mark.requires_embedding
class TestSemanticSearch:
    """Tests for semantic search functionality."""

    def test_search_claims_returns_relevant_results(self, initialized_db, sample_claim):
        """Semantic search returns relevant claims."""
        add_claim(sample_claim, initialized_db, generate_embedding=True)

        # Add an unrelated claim
        unrelated = sample_claim.copy()
        unrelated["id"] = "GOV-2026-001"
        unrelated["domain"] = "GOV"
        unrelated["text"] = "Government policy on agriculture"
        add_claim(unrelated, initialized_db, generate_embedding=True)

        # Search for AI-related content
        results = search_claims("artificial intelligence costs", limit=2, db=initialized_db)

        assert len(results) > 0
        # The AI-related claim should rank higher
        assert results[0]["id"] == "TECH-2026-001"

    def test_search_claims_respects_limit(self, initialized_db, sample_claim):
        """Search respects the limit parameter."""
        # Add multiple claims
        for i in range(5):
            claim = sample_claim.copy()
            claim["id"] = f"TECH-2026-{i+1:03d}"
            add_claim(claim, initialized_db, generate_embedding=True)

        results = search_claims("AI costs", limit=3, db=initialized_db)
        assert len(results) == 3

    def test_search_claims_filters_by_domain(self, initialized_db, sample_claim):
        """Search can filter by domain."""
        add_claim(sample_claim, initialized_db, generate_embedding=True)

        labor_claim = sample_claim.copy()
        labor_claim["id"] = "LABOR-2026-001"
        labor_claim["domain"] = "LABOR"
        labor_claim["text"] = "AI will automate jobs"
        add_claim(labor_claim, initialized_db, generate_embedding=True)

        results = search_claims("AI automation", domain="LABOR", db=initialized_db)
        assert all(r["domain"] == "LABOR" for r in results)


class TestRelatedClaims:
    """Tests for relationship traversal."""

    def test_get_related_claims_forward_relationships(self, initialized_db, sample_claim):
        """Forward relationships are retrieved."""
        # Add claim that supports another
        claim1 = sample_claim.copy()
        claim1["supports"] = ["TECH-2026-002"]
        add_claim(claim1, initialized_db, generate_embedding=False)

        claim2 = sample_claim.copy()
        claim2["id"] = "TECH-2026-002"
        add_claim(claim2, initialized_db, generate_embedding=False)

        related = get_related_claims("TECH-2026-001", initialized_db)
        assert len(related["supports"]) == 1
        assert related["supports"][0]["id"] == "TECH-2026-002"

    def test_get_related_claims_reverse_relationships(self, initialized_db, sample_claim):
        """Reverse relationships are found."""
        claim1 = sample_claim.copy()
        add_claim(claim1, initialized_db, generate_embedding=False)

        claim2 = sample_claim.copy()
        claim2["id"] = "TECH-2026-002"
        claim2["supports"] = ["TECH-2026-001"]
        add_claim(claim2, initialized_db, generate_embedding=False)

        related = get_related_claims("TECH-2026-001", initialized_db)
        assert len(related["supported_by"]) == 1
        assert related["supported_by"][0]["id"] == "TECH-2026-002"


class TestSourcesCRUD:
    """Tests for source operations."""

    def test_add_source(self, initialized_db, sample_source):
        """Sources can be added."""
        source_id = add_source(sample_source, initialized_db, generate_embedding=False)
        assert source_id == "test-source-001"

    def test_get_source(self, initialized_db, sample_source):
        """Sources can be retrieved."""
        add_source(sample_source, initialized_db, generate_embedding=False)
        retrieved = get_source("test-source-001", initialized_db)

        assert retrieved is not None
        assert retrieved["title"] == sample_source["title"]
        assert retrieved["reliability"] == pytest.approx(0.8, rel=0.01)

    def test_list_sources_filters_by_type(self, initialized_db, sample_source):
        """Sources can be filtered by type."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        blog = sample_source.copy()
        blog["id"] = "test-blog-001"
        blog["type"] = "BLOG"
        add_source(blog, initialized_db, generate_embedding=False)

        reports = list_sources(source_type="REPORT", db=initialized_db)
        assert len(reports) == 1
        assert reports[0]["type"] == "REPORT"


class TestChainsCRUD:
    """Tests for chain operations."""

    def test_add_chain(self, initialized_db, sample_chain):
        """Chains can be added."""
        chain_id = add_chain(sample_chain, initialized_db, generate_embedding=False)
        assert chain_id == "CHAIN-2026-001"

    def test_get_chain(self, initialized_db, sample_chain):
        """Chains can be retrieved."""
        add_chain(sample_chain, initialized_db, generate_embedding=False)
        retrieved = get_chain("CHAIN-2026-001", initialized_db)

        assert retrieved is not None
        assert retrieved["thesis"] == sample_chain["thesis"]
        assert retrieved["credence"] == pytest.approx(0.5, rel=0.01)


class TestPredictions:
    """Tests for prediction operations."""

    def test_add_prediction(self, initialized_db, sample_prediction):
        """Predictions can be added."""
        claim_id = add_prediction(sample_prediction, initialized_db)
        assert claim_id == "TECH-2026-002"

    def test_get_prediction(self, initialized_db, sample_prediction):
        """Predictions can be retrieved."""
        add_prediction(sample_prediction, initialized_db)
        retrieved = get_prediction("TECH-2026-002", initialized_db)

        assert retrieved is not None
        assert retrieved["status"] == "[P→]"

    def test_list_predictions_filters_by_status(self, initialized_db, sample_prediction):
        """Predictions can be filtered by status."""
        add_prediction(sample_prediction, initialized_db)

        confirmed = sample_prediction.copy()
        confirmed["claim_id"] = "TECH-2026-003"
        confirmed["status"] = "[P+]"
        add_prediction(confirmed, initialized_db)

        on_track = list_predictions(status="[P→]", db=initialized_db)
        assert len(on_track) == 1
        assert on_track[0]["status"] == "[P→]"


class TestDefinitions:
    """Tests for definition operations."""

    def test_add_definition(self, initialized_db):
        """Definitions can be added."""
        definition = {
            "term": "AGI",
            "definition": "Artificial General Intelligence",
            "operational_proxy": "Passes all human capability tests",
            "notes": "Contested term",
            "domain": "TECH",
            "analysis_id": None,
        }
        term = add_definition(definition, initialized_db)
        assert term == "AGI"

    def test_get_definition(self, initialized_db):
        """Definitions can be retrieved."""
        definition = {
            "term": "AGI",
            "definition": "Artificial General Intelligence",
            "operational_proxy": "Passes all human capability tests",
            "notes": None,
            "domain": "TECH",
            "analysis_id": None,
        }
        add_definition(definition, initialized_db)
        retrieved = get_definition("AGI", initialized_db)

        assert retrieved is not None
        assert retrieved["definition"] == "Artificial General Intelligence"


class TestStatistics:
    """Tests for statistics functions."""

    def test_get_stats_empty_db(self, initialized_db):
        """Stats work on empty database."""
        stats = get_stats(initialized_db)

        assert stats["claims"] == 0
        assert stats["sources"] == 0
        assert stats["chains"] == 0

    def test_get_stats_with_data(self, initialized_db, sample_claim, sample_source):
        """Stats reflect actual data."""
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_source(sample_source, initialized_db, generate_embedding=False)

        stats = get_stats(initialized_db)

        assert stats["claims"] == 1
        assert stats["sources"] == 1


class TestDomainConstants:
    """Tests for domain-related constants."""

    def test_valid_domains_complete(self):
        """All expected domains are present."""
        expected = {"LABOR", "ECON", "GOV", "TECH", "SOC", "RESOURCE", "TRANS", "META", "GEO", "INST", "RISK"}
        assert VALID_DOMAINS == expected

    def test_domain_migration_mappings(self):
        """Domain migration mappings are correct."""
        assert DOMAIN_MIGRATION["VALUE"] == "ECON"
        assert DOMAIN_MIGRATION["DIST"] == "ECON"
        assert DOMAIN_MIGRATION["SOCIAL"] == "SOC"
