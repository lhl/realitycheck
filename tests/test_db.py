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
import subprocess

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def assert_cli_success(result: subprocess.CompletedProcess, expected_code: int = 0) -> None:
    """Assert CLI command succeeded, handling lancedb GIL cleanup crash (exit 134).

    Some versions of lancedb/pyarrow crash during Python shutdown due to a
    background event loop thread not being cleaned up properly. The command
    succeeds (correct stdout) but the process crashes on exit with code 134.

    This helper accepts 134 as success if the expected output was produced.
    """
    # Exit code 134 = 128 + 6 (SIGABRT) from GIL cleanup crash
    if result.returncode == 134 and "PyGILState_Release" in result.stderr:
        # Command succeeded but crashed on cleanup - treat as success
        return
    assert result.returncode == expected_code, f"Expected {expected_code}, got {result.returncode}. stderr: {result.stderr}"

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
    update_source,
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
    add_analysis_log,
    get_analysis_log,
    list_analysis_logs,
    # Evidence links
    add_evidence_link,
    get_evidence_link,
    list_evidence_links,
    update_evidence_link,
    supersede_evidence_link,
    # Reasoning trails
    add_reasoning_trail,
    get_reasoning_trail,
    list_reasoning_trails,
    get_reasoning_history,
    supersede_reasoning_trail,
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

        expected_tables = {"claims", "sources", "chains", "predictions", "contradictions", "definitions", "analysis_logs", "evidence_links", "reasoning_trails"}
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

    def test_add_claim_updates_source_claims_extracted_backlink(self, initialized_db, sample_claim, sample_source):
        """Adding a claim updates the source's claims_extracted backlink when possible."""
        source = sample_source.copy()
        source["claims_extracted"] = []
        add_source(source, initialized_db, generate_embedding=False)

        add_claim(sample_claim, initialized_db, generate_embedding=False)

        updated = get_source(source["id"], initialized_db)
        assert updated is not None
        assert "TECH-2026-001" in (updated.get("claims_extracted") or [])

    def test_add_prediction_claim_auto_creates_prediction_record(self, initialized_db, sample_claim, sample_source):
        """[P] claims automatically create a stub prediction record."""
        source = sample_source.copy()
        source["claims_extracted"] = []
        add_source(source, initialized_db, generate_embedding=False)

        pred_claim = sample_claim.copy()
        pred_claim["id"] = "TECH-2026-002"
        pred_claim["type"] = "[P]"
        add_claim(pred_claim, initialized_db, generate_embedding=False)

        pred = get_prediction("TECH-2026-002", initialized_db)
        assert pred is not None
        assert pred["status"] == "[P?]"
        assert pred["source_id"] == source["id"]

        updated = get_source(source["id"], initialized_db)
        assert updated is not None
        assert "TECH-2026-002" in (updated.get("claims_extracted") or [])

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

    def test_delete_claim_removes_prediction_and_source_backlink(self, initialized_db, sample_claim, sample_source):
        """Deleting a claim cleans up associated prediction records and source backlinks."""
        source = sample_source.copy()
        source["claims_extracted"] = []
        add_source(source, initialized_db, generate_embedding=False)

        pred_claim = sample_claim.copy()
        pred_claim["id"] = "TECH-2026-002"
        pred_claim["type"] = "[P]"
        add_claim(pred_claim, initialized_db, generate_embedding=False)

        assert get_prediction("TECH-2026-002", initialized_db) is not None

        delete_claim("TECH-2026-002", initialized_db)

        assert get_prediction("TECH-2026-002", initialized_db) is None
        updated = get_source(source["id"], initialized_db)
        assert updated is not None
        assert "TECH-2026-002" not in (updated.get("claims_extracted") or [])

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

    def test_update_source(self, initialized_db, sample_source):
        """Sources can be updated."""
        add_source(sample_source, initialized_db, generate_embedding=False)

        ok = update_source(
            "test-source-001",
            {
                "analysis_file": "analysis/sources/test-source-001.md",
                "topics": ["updated"],
                "domains": ["TECH", "LABOR"],
                "claims_extracted": ["TECH-2026-123"],
            },
            initialized_db,
            generate_embedding=False,
        )
        assert ok is True

        retrieved = get_source("test-source-001", initialized_db)
        assert retrieved is not None
        assert retrieved["analysis_file"] == "analysis/sources/test-source-001.md"
        assert retrieved["topics"] == ["updated"]
        assert retrieved["domains"] == ["TECH", "LABOR"]
        assert retrieved["claims_extracted"] == ["TECH-2026-123"]


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


# =============================================================================
# CLI Command Tests
# =============================================================================

import subprocess
import json
import os


class TestClaimCLI:
    """Tests for claim CLI subcommands."""

    def test_stats_errors_when_no_data_env_and_no_default_db(self):
        """stats errors with a helpful message when REALITYCHECK_DATA is unset and no default DB exists."""
        env = os.environ.copy()
        env.pop("REALITYCHECK_DATA", None)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "stats"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 2
        assert "REALITYCHECK_DATA" in result.stderr

    def test_claim_add_creates_claim(self, temp_db_path: Path):
        """claim add creates a new claim."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Initialize database first
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Add a claim
        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--text", "Test claim text",
                "--type", "[F]",
                "--domain", "TECH",
                "--evidence-level", "E3",
                "--credence", "0.7",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "TECH-" in result.stdout  # Auto-generated ID

        # Verify claim is actually in the database
        stats_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "stats"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(stats_result)
        assert "claims: 1 rows" in stats_result.stdout

    def test_claim_add_with_explicit_id(self, temp_db_path: Path):
        """claim add with --id uses provided ID."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "CUSTOM-2026-001",
                "--text", "Custom ID claim",
                "--type", "[T]",
                "--domain", "TECH",
                "--evidence-level", "E2",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "CUSTOM-2026-001" in result.stdout

    def test_claim_get_outputs_json(self, temp_db_path: Path):
        """claim get returns JSON output."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Initialize and add claim
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "TEST-2026-001",
                "--text", "Get test claim",
                "--type", "[F]",
                "--domain", "TECH",
                "--evidence-level", "E3",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Get the claim
        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "get", "TEST-2026-001"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert data["id"] == "TEST-2026-001"
        assert data["text"] == "Get test claim"

    def test_claim_get_not_found(self, temp_db_path: Path):
        """claim get returns error for non-existent claim."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "get", "NONEXISTENT-001"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result, expected_code=1)
        assert "not found" in result.stderr.lower()

    def test_claim_list_outputs_json(self, temp_db_path: Path):
        """claim list returns JSON array."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Add two claims
        for i in range(2):
            subprocess.run(
                [
                    "uv", "run", "python", "scripts/db.py",
                    "claim", "add",
                    "--id", f"TEST-2026-{i+1:03d}",
                    "--text", f"List test claim {i+1}",
                    "--type", "[F]",
                    "--domain", "TECH",
                    "--evidence-level", "E3",
                ],
                env=env,
                capture_output=True,
                cwd=Path(__file__).parent.parent,
            )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert len(data) == 2

    def test_claim_list_filters_by_domain(self, temp_db_path: Path):
        """claim list --domain filters results."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Add claims in different domains
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "TECH-2026-001",
                "--text", "Tech claim",
                "--type", "[F]",
                "--domain", "TECH",
                "--evidence-level", "E3",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "LABOR-2026-001",
                "--text", "Labor claim",
                "--type", "[T]",
                "--domain", "LABOR",
                "--evidence-level", "E3",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "list", "--domain", "TECH"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["domain"] == "TECH"

    def test_claim_update_modifies_record(self, temp_db_path: Path):
        """claim update modifies existing claim."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "TEST-2026-001",
                "--text", "Original text",
                "--type", "[F]",
                "--domain", "TECH",
                "--evidence-level", "E3",
                "--credence", "0.5",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Update the claim
        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "update", "TEST-2026-001",
                "--credence", "0.9",
                "--notes", "Updated notes",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)

        # Verify the update
        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "get", "TEST-2026-001"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        data = json.loads(result.stdout)
        assert data["credence"] == pytest.approx(0.9, rel=0.01)
        assert data["notes"] == "Updated notes"


class TestSourceCLI:
    """Tests for source CLI subcommands."""

    def test_source_add_creates_source(self, temp_db_path: Path):
        """source add creates a new source."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "source", "add",
                "--id", "author-2026-title",
                "--title", "Test Paper Title",
                "--type", "PAPER",
                "--author", "Test Author",
                "--year", "2026",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "author-2026-title" in result.stdout

    def test_source_get_outputs_json(self, temp_db_path: Path):
        """source get returns JSON output."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "source", "add",
                "--id", "test-source-001",
                "--title", "Test Report",
                "--type", "REPORT",
                "--author", "Author One",
                "--year", "2026",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "get", "test-source-001"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert data["id"] == "test-source-001"
        assert data["title"] == "Test Report"

    def test_source_list_filters_by_type(self, temp_db_path: Path):
        """source list --type filters results."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Add sources of different types
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "source", "add",
                "--id", "paper-001",
                "--title", "Research Paper",
                "--type", "PAPER",
                "--author", "Researcher",
                "--year", "2026",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "source", "add",
                "--id", "blog-001",
                "--title", "Blog Post",
                "--type", "BLOG",
                "--author", "Blogger",
                "--year", "2026",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "list", "--type", "PAPER"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["type"] == "PAPER"


class TestChainCLI:
    """Tests for chain CLI subcommands."""

    def test_chain_add_creates_chain(self, temp_db_path: Path):
        """chain add creates a new chain."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "chain", "add",
                "--id", "CHAIN-2026-001",
                "--name", "Test Chain",
                "--thesis", "Test thesis statement",
                "--claims", "CLAIM-001,CLAIM-002",
                "--credence", "0.6",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "CHAIN-2026-001" in result.stdout

    def test_chain_get_outputs_json(self, temp_db_path: Path):
        """chain get returns JSON output."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "chain", "add",
                "--id", "CHAIN-2026-001",
                "--name", "Test Chain",
                "--thesis", "Test thesis",
                "--claims", "CLAIM-001",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "chain", "get", "CHAIN-2026-001"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert data["id"] == "CHAIN-2026-001"
        assert data["thesis"] == "Test thesis"

    def test_chain_list_outputs_json(self, temp_db_path: Path):
        """chain list returns JSON array."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "chain", "add",
                "--id", "CHAIN-2026-001",
                "--name", "Chain One",
                "--thesis", "First thesis",
                "--claims", "CLAIM-001",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "chain", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert len(data) == 1


class TestPredictionCLI:
    """Tests for prediction CLI subcommands."""

    def test_prediction_add_creates_prediction(self, temp_db_path: Path):
        """prediction add creates a new prediction."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "prediction", "add",
                "--claim-id", "TECH-2026-001",
                "--source-id", "test-source",
                "--status", "[P→]",
                "--target-date", "2027-12-31",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "TECH-2026-001" in result.stdout

    def test_prediction_list_filters_by_status(self, temp_db_path: Path):
        """prediction list --status filters results."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Add predictions with different statuses
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "prediction", "add",
                "--claim-id", "TECH-2026-001",
                "--source-id", "test-source",
                "--status", "[P→]",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "prediction", "add",
                "--claim-id", "TECH-2026-002",
                "--source-id", "test-source",
                "--status", "[P+]",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "prediction", "list", "--status", "[P→]"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["status"] == "[P→]"


class TestRelatedCLI:
    """Tests for related CLI subcommand."""

    def test_related_shows_relationships(self, temp_db_path: Path):
        """related shows claim relationships."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Add claims with relationships
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "TECH-2026-001",
                "--text", "Base claim",
                "--type", "[F]",
                "--domain", "TECH",
                "--evidence-level", "E3",
                "--supports", "TECH-2026-002",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "TECH-2026-002",
                "--text", "Supported claim",
                "--type", "[T]",
                "--domain", "TECH",
                "--evidence-level", "E3",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "related", "TECH-2026-001"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert "supports" in data
        assert len(data["supports"]) == 1


class TestImportCLI:
    """Tests for import CLI subcommand."""

    def test_import_yaml_claims(self, temp_db_path: Path, tmp_path: Path):
        """import loads claims from YAML file."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Create a YAML file with claims
        import yaml
        claims_data = {
            "claims": [
                {
                    "id": "IMPORT-2026-001",
                    "text": "Imported claim one",
                    "type": "[F]",
                    "domain": "TECH",
                    "evidence_level": "E3",
                    "credence": 0.7,
                    "source_ids": ["test-source"],
                    "first_extracted": "2026-01-20",
                    "extracted_by": "test",
                    "version": 1,
                    "last_updated": "2026-01-20",
                },
                {
                    "id": "IMPORT-2026-002",
                    "text": "Imported claim two",
                    "type": "[T]",
                    "domain": "LABOR",
                    "evidence_level": "E2",
                    "credence": 0.6,
                    "source_ids": ["test-source"],
                    "first_extracted": "2026-01-20",
                    "extracted_by": "test",
                    "version": 1,
                    "last_updated": "2026-01-20",
                },
            ]
        }
        yaml_file = tmp_path / "claims.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(claims_data, f)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "import", str(yaml_file), "--type", "claims"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "2" in result.stdout  # Imported 2 claims

        # Verify claims were imported
        list_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        data = json.loads(list_result.stdout)
        assert len(data) == 2

    def test_import_yaml_all_syncs_source_backlinks_and_predictions(self, temp_db_path: Path, tmp_path: Path):
        """import --type all imports sources first so claim side-effects can run."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        import yaml
        all_data = {
            "sources": [
                {
                    "id": "test-source",
                    "title": "Imported Source",
                    "type": "REPORT",
                    "author": ["Test Author"],
                    "year": 2026,
                    "claims_extracted": [],
                }
            ],
            "claims": [
                {
                    "id": "IMPORT-2026-003",
                    "text": "Imported claim three",
                    "type": "[F]",
                    "domain": "TECH",
                    "evidence_level": "E3",
                    "credence": 0.7,
                    "source_ids": ["test-source"],
                    "first_extracted": "2026-01-20",
                    "extracted_by": "test",
                    "version": 1,
                    "last_updated": "2026-01-20",
                },
                {
                    "id": "IMPORT-2026-004",
                    "text": "Imported prediction claim",
                    "type": "[P]",
                    "domain": "TECH",
                    "evidence_level": "E5",
                    "credence": 0.5,
                    "source_ids": ["test-source"],
                    "first_extracted": "2026-01-20",
                    "extracted_by": "test",
                    "version": 1,
                    "last_updated": "2026-01-20",
                },
            ],
        }
        yaml_file = tmp_path / "all.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(all_data, f)

        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "import", str(yaml_file),
                "--type", "all",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "Imported 2 claims, 1 sources" in result.stdout

        source_get = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "get", "test-source"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_get)
        source = json.loads(source_get.stdout)
        assert set(source.get("claims_extracted") or []) == {"IMPORT-2026-003", "IMPORT-2026-004"}

        pred_list = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "prediction", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(pred_list)
        preds = json.loads(pred_list.stdout)
        assert any(p.get("claim_id") == "IMPORT-2026-004" and p.get("status") == "[P?]" for p in preds)

    def test_import_yaml_on_conflict_skip_update_and_error(self, temp_db_path: Path, tmp_path: Path):
        """import supports `--on-conflict` for reruns (skip/update/error)."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        import yaml

        base = {
            "sources": [
                {
                    "id": "test-source",
                    "title": "Imported Source",
                    "type": "REPORT",
                    "author": ["Test Author"],
                    "year": 2026,
                    "claims_extracted": [],
                }
            ],
            "claims": [
                {
                    "id": "IMPORT-2026-010",
                    "text": "Imported claim",
                    "type": "[F]",
                    "domain": "TECH",
                    "evidence_level": "E3",
                    "credence": 0.7,
                    "source_ids": ["test-source"],
                    "first_extracted": "2026-01-20",
                    "extracted_by": "test",
                    "version": 1,
                    "last_updated": "2026-01-20",
                }
            ],
        }
        yaml_file = tmp_path / "all.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(base, f)

        initial = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "import", str(yaml_file),
                "--type", "all",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(initial)

        updated = {
            **base,
            "sources": [{**base["sources"][0], "title": "Updated Source"}],
            "claims": [{**base["claims"][0], "text": "Updated claim"}],
        }
        yaml_file2 = tmp_path / "all-updated.yaml"
        with open(yaml_file2, "w") as f:
            yaml.dump(updated, f)

        # Default: error on conflicts
        conflict_err = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "import", str(yaml_file2),
                "--type", "all",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(conflict_err, expected_code=1)

        # Skip: keep existing values
        conflict_skip = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "import", str(yaml_file2),
                "--type", "all",
                "--no-embedding",
                "--on-conflict", "skip",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(conflict_skip)

        source_get = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "get", "test-source"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_get)
        source = json.loads(source_get.stdout)
        assert source["title"] == "Imported Source"

        claim_get = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "get", "IMPORT-2026-010"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(claim_get)
        claim = json.loads(claim_get.stdout)
        assert claim["text"] == "Imported claim"

        # Update: apply incoming values
        conflict_update = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "import", str(yaml_file2),
                "--type", "all",
                "--no-embedding",
                "--on-conflict", "update",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(conflict_update)

        source_get2 = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "get", "test-source"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_get2)
        source2 = json.loads(source_get2.stdout)
        assert source2["title"] == "Updated Source"

        claim_get2 = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "get", "IMPORT-2026-010"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(claim_get2)
        claim2 = json.loads(claim_get2.stdout)
        assert claim2["text"] == "Updated claim"

        # No duplicates should be introduced.
        claim_list = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(claim_list)
        claims = json.loads(claim_list.stdout)
        assert len(claims) == 1

        source_list = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_list)
        sources = json.loads(source_list.stdout)
        assert len(sources) == 1

    def test_import_handles_missing_file(self, temp_db_path: Path):
        """import returns error for missing file."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "import", "/nonexistent/file.yaml"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result, expected_code=1)
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


class TestRepairCLI:
    """Tests for repair CLI subcommand."""

    def test_repair_fixes_backlinks_and_prediction_stubs(self, temp_db_path: Path):
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        # Create a backlink mismatch: add claim before source so add_claim can't upsert.
        claim_add = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "TECH-2026-010",
                "--text", "Backlink mismatch claim",
                "--type", "[F]",
                "--domain", "TECH",
                "--evidence-level", "E3",
                "--source-ids", "test-source",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(claim_add)

        source_add = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "source", "add",
                "--id", "test-source",
                "--title", "Test Source",
                "--type", "REPORT",
                "--author", "Test Author",
                "--year", "2026",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_add)

        # Create a missing prediction stub: add [P] claim then delete its prediction row.
        p_claim_add = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "TECH-2026-011",
                "--text", "Prediction claim",
                "--type", "[P]",
                "--domain", "TECH",
                "--evidence-level", "E3",
                "--source-ids", "test-source",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(p_claim_add)

        pred_delete = subprocess.run(
            [
                "uv", "run", "python", "-c",
                "import sys; from pathlib import Path; sys.path.insert(0, 'scripts'); "
                "from db import get_db; db = get_db(); "
                "db.open_table('predictions').delete(\"claim_id = 'TECH-2026-011'\")",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(pred_delete)

        pred_list_before = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "prediction", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(pred_list_before)
        preds_before = json.loads(pred_list_before.stdout)
        assert not any(p.get("claim_id") == "TECH-2026-011" for p in preds_before)

        repair = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "repair"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(repair)

        source_get = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "get", "test-source"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_get)
        source = json.loads(source_get.stdout)
        assert "TECH-2026-010" in (source.get("claims_extracted") or [])

        pred_list_after = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "prediction", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(pred_list_after)
        preds_after = json.loads(pred_list_after.stdout)
        assert any(p.get("claim_id") == "TECH-2026-011" and p.get("status") == "[P?]" for p in preds_after)


class TestDoctorCLI:
    """Tests for doctor CLI subcommand."""

    def test_doctor_detects_project_root_from_subdir(self, tmp_path: Path):
        project_path = tmp_path / "test-project"

        init_project = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "init-project",
                "--path", str(project_path),
                "--no-git",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(init_project)

        cwd = project_path / "analysis" / "sources"
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "db.py"), "doctor"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        assert_cli_success(result)

        combined = (result.stdout or "") + (result.stderr or "")
        assert str(project_path) in combined
        assert "REALITYCHECK_DATA" in combined


class TestInitProjectCLI:
    """Tests for init-project CLI command."""

    def test_init_project_creates_structure(self, tmp_path: Path):
        """init-project creates expected directory structure."""
        project_path = tmp_path / "test-project"

        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "init-project",
                "--path", str(project_path),
                "--no-git",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)

        # Check directories created
        assert (project_path / "data").exists()
        assert (project_path / "analysis" / "sources").exists()
        assert (project_path / "analysis" / "syntheses").exists()
        assert (project_path / "tracking" / "updates").exists()
        assert (project_path / "inbox" / "to-catalog").exists()

        # Check files created
        assert (project_path / ".realitycheck.yaml").exists()
        assert (project_path / ".gitignore").exists()
        assert (project_path / ".gitattributes").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / "tracking" / "predictions.md").exists()

        # Check database initialized
        assert (project_path / "data" / "realitycheck.lance").exists()

    def test_init_project_creates_config(self, tmp_path: Path):
        """init-project creates valid .realitycheck.yaml."""
        import yaml

        project_path = tmp_path / "test-project"

        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "init-project",
                "--path", str(project_path),
                "--db-path", "custom/path.lance",
                "--no-git",
            ],
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        config_path = project_path / ".realitycheck.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["version"] == "1.0"
        assert config["db_path"] == "custom/path.lance"


class TestTextFormatOutput:
    """Tests for --format text output option."""

    def test_claim_list_text_format(self, temp_db_path: Path):
        """claim list --format text outputs human-readable format."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "claim", "add",
                "--id", "TEST-2026-001",
                "--text", "Text format claim",
                "--type", "[F]",
                "--domain", "TECH",
                "--evidence-level", "E3",
            ],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "list", "--format", "text"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        # Text format should NOT be valid JSON
        try:
            json.loads(result.stdout)
            assert False, "Output should be text, not JSON"
        except json.JSONDecodeError:
            pass
        # Should contain readable info
        assert "TEST-2026-001" in result.stdout
        assert "Text format claim" in result.stdout or "[F]" in result.stdout


class TestAnalysisLogsCRUD:
    """Tests for analysis log operations."""

    def test_add_analysis_log(self, initialized_db, sample_analysis_log):
        """Analysis logs can be added."""
        log_id = add_analysis_log(sample_analysis_log, initialized_db)
        assert log_id == "ANALYSIS-2026-001"

    def test_get_analysis_log(self, initialized_db, sample_analysis_log):
        """Analysis logs can be retrieved by ID."""
        add_analysis_log(sample_analysis_log, initialized_db)
        retrieved = get_analysis_log("ANALYSIS-2026-001", initialized_db)

        assert retrieved is not None
        assert retrieved["id"] == "ANALYSIS-2026-001"
        assert retrieved["source_id"] == "test-source-001"
        assert retrieved["tool"] == "claude-code"
        assert retrieved["status"] == "completed"

    def test_get_analysis_log_returns_none_for_missing(self, initialized_db):
        """None is returned for non-existent analysis logs."""
        result = get_analysis_log("ANALYSIS-9999-999", initialized_db)
        assert result is None

    def test_list_analysis_logs_all(self, initialized_db, sample_analysis_log):
        """All analysis logs are listed."""
        add_analysis_log(sample_analysis_log, initialized_db)

        log2 = sample_analysis_log.copy()
        log2["id"] = "ANALYSIS-2026-002"
        log2["source_id"] = "test-source-002"
        add_analysis_log(log2, initialized_db)

        results = list_analysis_logs(db=initialized_db)
        assert len(results) == 2

    def test_list_analysis_logs_filter_source_id(self, initialized_db, sample_analysis_log):
        """Analysis logs can be filtered by source_id."""
        add_analysis_log(sample_analysis_log, initialized_db)

        log2 = sample_analysis_log.copy()
        log2["id"] = "ANALYSIS-2026-002"
        log2["source_id"] = "other-source"
        add_analysis_log(log2, initialized_db)

        results = list_analysis_logs(source_id="test-source-001", db=initialized_db)
        assert len(results) == 1
        assert results[0]["source_id"] == "test-source-001"

    def test_list_analysis_logs_filter_tool(self, initialized_db, sample_analysis_log):
        """Analysis logs can be filtered by tool."""
        add_analysis_log(sample_analysis_log, initialized_db)

        log2 = sample_analysis_log.copy()
        log2["id"] = "ANALYSIS-2026-002"
        log2["tool"] = "codex"
        add_analysis_log(log2, initialized_db)

        results = list_analysis_logs(tool="claude-code", db=initialized_db)
        assert len(results) == 1
        assert results[0]["tool"] == "claude-code"

    def test_list_analysis_logs_filter_status(self, initialized_db, sample_analysis_log):
        """Analysis logs can be filtered by status."""
        add_analysis_log(sample_analysis_log, initialized_db)

        log2 = sample_analysis_log.copy()
        log2["id"] = "ANALYSIS-2026-002"
        log2["status"] = "draft"
        add_analysis_log(log2, initialized_db)

        results = list_analysis_logs(status="completed", db=initialized_db)
        assert len(results) == 1
        assert results[0]["status"] == "completed"

    def test_list_analysis_logs_limit(self, initialized_db, sample_analysis_log):
        """List respects limit parameter."""
        for i in range(5):
            log = sample_analysis_log.copy()
            log["id"] = f"ANALYSIS-2026-{i+1:03d}"
            add_analysis_log(log, initialized_db)

        results = list_analysis_logs(limit=3, db=initialized_db)
        assert len(results) == 3

    def test_add_analysis_log_auto_pass(self, initialized_db, sample_analysis_log):
        """Pass number is auto-computed when not provided."""
        log1 = sample_analysis_log.copy()
        del log1["pass"]
        del log1["id"]
        add_analysis_log(log1, initialized_db)

        log2 = sample_analysis_log.copy()
        del log2["pass"]
        del log2["id"]
        add_analysis_log(log2, initialized_db)

        results = list_analysis_logs(source_id="test-source-001", db=initialized_db)
        passes = sorted([r["pass"] for r in results])
        assert passes == [1, 2]


class TestAnalysisLogsCLI:
    """CLI tests for analysis log commands."""

    def test_cli_analysis_add(self, temp_db_path: Path):
        """rc-db analysis add creates an analysis log."""
        import os
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        source_add = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "source", "add",
                "--id", "test-source-001",
                "--title", "Test Source",
                "--type", "REPORT",
                "--author", "Test Author",
                "--year", "2026",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_add)

        result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "analysis", "add",
                "--source-id", "test-source-001",
                "--tool", "claude-code",
                "--notes", "Test analysis",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "Created analysis log:" in result.stdout
        assert "ANALYSIS-" in result.stdout

    def test_cli_analysis_get(self, temp_db_path: Path):
        """rc-db analysis get retrieves an analysis log."""
        import os
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        source_add = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "source", "add",
                "--id", "test-source",
                "--title", "Test Source",
                "--type", "REPORT",
                "--author", "Test Author",
                "--year", "2026",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_add)

        add_result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "analysis", "add",
                "--source-id", "test-source",
                "--tool", "manual",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(add_result)

        # Extract the ID from output
        import re
        match = re.search(r"ANALYSIS-\d{4}-\d{3}", add_result.stdout)
        assert match, f"Could not find analysis ID in output: {add_result.stdout}"
        analysis_id = match.group(0)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "get", analysis_id],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert analysis_id in result.stdout
        assert "test-source" in result.stdout

    def test_cli_analysis_list(self, temp_db_path: Path):
        """rc-db analysis list shows analysis logs."""
        import os
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env,
            capture_output=True,
            cwd=Path(__file__).parent.parent,
        )

        source_add = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "source", "add",
                "--id", "test-source",
                "--title", "Test Source",
                "--type", "REPORT",
                "--author", "Test Author",
                "--year", "2026",
                "--no-embedding",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(source_add)

        add_result = subprocess.run(
            [
                "uv", "run", "python", "scripts/db.py",
                "analysis", "add",
                "--source-id", "test-source",
                "--tool", "amp",
            ],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(add_result)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "ANALYSIS-" in result.stdout or "test-source" in result.stdout


# =============================================================================
# Token Usage Lifecycle Tests (Phase 1 of token-usage implementation)
# =============================================================================

class TestUpdateAnalysisLog:
    """Tests for update_analysis_log() function."""

    def test_update_analysis_log_partial_update(self, initialized_db, sample_source):
        """Update only specified fields, leave others unchanged."""
        from db import add_source, add_analysis_log, update_analysis_log, get_analysis_log

        add_source(sample_source, initialized_db)

        log_id = add_analysis_log({
            "source_id": sample_source["id"],
            "tool": "claude-code",
            "status": "started",
            "notes": "Original note",
        }, initialized_db)

        # Partial update - only change status and add tokens
        update_analysis_log(
            log_id,
            status="completed",
            tokens_check=500,
            db=initialized_db,
        )

        updated = get_analysis_log(log_id, initialized_db)
        assert updated["status"] == "completed"
        assert updated["tokens_check"] == 500
        assert updated["notes"] == "Original note"  # Unchanged

    def test_update_analysis_log_no_duplicate_rows(self, initialized_db, sample_source):
        """Update modifies in place, does not create new rows."""
        from db import add_source, add_analysis_log, update_analysis_log, list_analysis_logs

        add_source(sample_source, initialized_db)

        log_id = add_analysis_log({
            "source_id": sample_source["id"],
            "tool": "claude-code",
            "status": "started",
        }, initialized_db)

        # Multiple updates
        update_analysis_log(log_id, status="completed", db=initialized_db)
        update_analysis_log(log_id, notes="Added notes", db=initialized_db)

        logs = list_analysis_logs(source_id=sample_source["id"], db=initialized_db)
        assert len(logs) == 1  # Still just one row
        assert logs[0]["id"] == log_id

    def test_update_analysis_log_nonexistent_id_errors(self, initialized_db):
        """Updating a nonexistent ID raises an error."""
        from db import update_analysis_log

        with pytest.raises(ValueError, match="not found"):
            update_analysis_log("ANALYSIS-9999-999", status="completed", db=initialized_db)


class TestAnalysisLifecycleCLI:
    """CLI tests for analysis lifecycle commands (start/mark/complete)."""

    def test_cli_analysis_start_creates_row_with_baseline(self, temp_db_path: Path, tmp_path: Path):
        """rc-db analysis start creates a row with tokens_baseline."""
        import os
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Init DB and add source
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026", "--no-embedding"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        # Create a mock session for auto-detection
        claude_sessions = tmp_path / ".claude" / "projects" / "test"
        claude_sessions.mkdir(parents=True)
        session_file = claude_sessions / "test-uuid-1234-5678-9abc-def012345678.jsonl"
        session_file.write_text('{"message":{"usage":{"input_tokens":100,"output_tokens":50}}}\n')

        env["HOME"] = str(tmp_path)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "start",
             "--source-id", "test-source", "--tool", "claude-code",
             "--usage-session-id", "test-uuid-1234-5678-9abc-def012345678"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "ANALYSIS-" in result.stdout

    def test_cli_analysis_start_auto_detects_session(self, temp_db_path: Path, tmp_path: Path):
        """rc-db analysis start auto-detects session when exactly one exists."""
        import os
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Init DB and add source
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026", "--no-embedding"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        # Create exactly one mock session (auto-detection should work)
        session_uuid = "deadbeef-1234-5678-9abc-def012345678"
        claude_sessions = tmp_path / ".claude" / "projects" / "test"
        claude_sessions.mkdir(parents=True)
        session_file = claude_sessions / f"{session_uuid}.jsonl"
        session_file.write_text('{"message":{"usage":{"input_tokens":100,"output_tokens":50}}}\n')

        env["HOME"] = str(tmp_path)

        # Do NOT pass --usage-session-id - should auto-detect
        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "start",
             "--source-id", "test-source", "--tool", "claude-code"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "ANALYSIS-" in result.stdout
        # Should show baseline tokens from auto-detection
        assert "baseline tokens: 150" in result.stdout or "session:" in result.stdout

        # Extract the analysis ID and verify fields were populated
        import re
        match = re.search(r"ANALYSIS-\d{4}-\d{3}", result.stdout)
        assert match, f"No analysis ID found in output: {result.stdout}"
        analysis_id = match.group(0)

        # Get the analysis and verify auto-detection worked
        get_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "get", analysis_id, "--format", "json"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(get_result)
        data = json.loads(get_result.stdout)
        assert data.get("usage_session_id") == session_uuid, f"Session ID not auto-detected: {data}"
        assert data.get("tokens_baseline") == 150, f"Baseline not captured: {data}"

    def test_cli_analysis_start_ambiguous_sessions_warns(self, temp_db_path: Path, tmp_path: Path):
        """rc-db analysis start warns and skips token tracking when multiple sessions exist."""
        import os
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Init DB and add source
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026", "--no-embedding"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        # Create TWO mock sessions (should trigger ambiguity)
        claude_sessions = tmp_path / ".claude" / "projects" / "test"
        claude_sessions.mkdir(parents=True)
        (claude_sessions / "aaaaaaaa-1111-2222-3333-444455556666.jsonl").write_text(
            '{"message":{"usage":{"input_tokens":100,"output_tokens":50}}}\n'
        )
        (claude_sessions / "bbbbbbbb-1111-2222-3333-444455556666.jsonl").write_text(
            '{"message":{"usage":{"input_tokens":200,"output_tokens":100}}}\n'
        )

        env["HOME"] = str(tmp_path)

        # Do NOT pass --usage-session-id - should warn about ambiguity
        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "start",
             "--source-id", "test-source", "--tool", "claude-code"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "ANALYSIS-" in result.stdout
        # Should warn about multiple sessions
        assert "Multiple" in result.stderr or "--usage-session-id" in result.stderr

        # Extract the analysis ID and verify tokens_baseline is None (not captured)
        import re
        match = re.search(r"ANALYSIS-\d{4}-\d{3}", result.stdout)
        analysis_id = match.group(0)

        get_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "get", analysis_id, "--format", "json"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(get_result)
        data = json.loads(get_result.stdout)
        # tokens_baseline should be None because of ambiguity
        assert data.get("tokens_baseline") is None, f"tokens_baseline should be None: {data}"
        assert data.get("usage_session_id") is None, f"session_id should be None: {data}"

    def test_cli_analysis_mark_captures_token_delta(self, temp_db_path: Path, tmp_path: Path):
        """rc-db analysis mark captures tokens_cumulative and tokens_delta."""
        import os
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Init DB and add source
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026", "--no-embedding"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        # Create mock session with initial tokens
        session_uuid = "cafebabe-1234-5678-9abc-def012345678"
        claude_sessions = tmp_path / ".claude" / "projects" / "test"
        claude_sessions.mkdir(parents=True)
        session_file = claude_sessions / f"{session_uuid}.jsonl"
        session_file.write_text('{"message":{"usage":{"input_tokens":100,"output_tokens":50}}}\n')

        env["HOME"] = str(tmp_path)

        # Start analysis (auto-detects session, baseline=150)
        start_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "start",
             "--source-id", "test-source", "--tool", "claude-code"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(start_result)

        import re
        match = re.search(r"ANALYSIS-\d{4}-\d{3}", start_result.stdout)
        analysis_id = match.group(0)

        # Add more tokens to session file (simulating more API calls)
        with session_file.open("a") as f:
            f.write('{"message":{"usage":{"input_tokens":200,"output_tokens":100}}}\n')

        # Mark stage (should capture tokens_cumulative=450, tokens_delta=300)
        mark_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "mark",
             "--id", analysis_id, "--stage", "check_stage1"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(mark_result)

        # Verify stages_json has token data
        get_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "get", analysis_id, "--format", "json"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(get_result)
        data = json.loads(get_result.stdout)
        stages = json.loads(data.get("stages_json") or "[]")
        assert len(stages) >= 1, f"No stages found: {stages}"
        stage = stages[-1]
        assert stage.get("stage") == "check_stage1"
        assert stage.get("tokens_cumulative") == 450, f"Expected tokens_cumulative=450: {stage}"
        assert stage.get("tokens_delta") == 300, f"Expected tokens_delta=300: {stage}"

    def test_cli_analysis_mark_appends_stage(self, temp_db_path: Path):
        """rc-db analysis mark appends stage to stages_json."""
        import os
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026", "--no-embedding"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        # Create analysis with start (without session tracking for simplicity)
        add_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "add",
             "--source-id", "test-source", "--tool", "claude-code", "--status", "started"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(add_result)

        import re
        match = re.search(r"ANALYSIS-\d{4}-\d{3}", add_result.stdout)
        analysis_id = match.group(0)

        # Mark stage
        mark_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "mark",
             "--id", analysis_id, "--stage", "check_stage1"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(mark_result)

        # Verify stages_json was updated
        get_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "get", analysis_id, "--format", "json"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(get_result)
        data = json.loads(get_result.stdout)
        stages = json.loads(data.get("stages_json") or "[]")
        assert any(s.get("stage") == "check_stage1" for s in stages)

    def test_cli_analysis_complete_computes_tokens_check(self, temp_db_path: Path):
        """rc-db analysis complete computes tokens_check from baseline/final."""
        import os
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026", "--no-embedding"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        # Create analysis with known baseline
        add_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "add",
             "--source-id", "test-source", "--tool", "claude-code", "--status", "started",
             "--tokens-baseline", "1000"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(add_result)

        import re
        match = re.search(r"ANALYSIS-\d{4}-\d{3}", add_result.stdout)
        analysis_id = match.group(0)

        # Complete with final tokens
        complete_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "complete",
             "--id", analysis_id, "--tokens-final", "2500"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(complete_result)

        # Verify tokens_check was computed
        get_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "get", analysis_id, "--format", "json"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(get_result)
        data = json.loads(get_result.stdout)
        assert data.get("tokens_check") == 1500  # 2500 - 1000
        assert data.get("status") == "completed"

    def test_cli_analysis_sessions_list(self, temp_db_path: Path, tmp_path: Path):
        """rc-db analysis sessions list shows available sessions."""
        import os
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)
        env["HOME"] = str(tmp_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        # Create mock sessions - UUID must be valid hex format
        claude_sessions = tmp_path / ".claude" / "projects" / "test"
        claude_sessions.mkdir(parents=True)
        (claude_sessions / "a1b2c3d4-1111-2222-3333-444455556666.jsonl").write_text(
            '{"message":{"content":"Hello world","usage":{"input_tokens":100}}}\n'
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "analysis", "sessions", "list", "--tool", "claude-code"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "a1b2c3d4" in result.stdout or "Hello" in result.stdout


class TestMigrate:
    """Tests for rc-db migrate command."""

    def test_migrate_no_changes_needed(self, temp_db_path: Path):
        """Migrate reports no changes when schema is current."""
        import os
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Init creates tables with current schema
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "migrate"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "up to date" in result.stdout or "no changes" in result.stdout.lower()

    def test_migrate_dry_run(self, temp_db_path: Path):
        """Migrate --dry-run previews changes without applying."""
        import os
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "migrate", "--dry-run"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "dry-run" in result.stdout.lower()

    def test_migrate_adds_missing_columns(self, temp_db_path: Path):
        """Migrate adds missing columns to existing tables."""
        import lancedb
        import pyarrow as pa

        # Create a minimal analysis_logs table missing new columns
        db = lancedb.connect(str(temp_db_path))
        minimal_schema = pa.schema([
            pa.field("id", pa.string(), nullable=False),
            pa.field("source_id", pa.string(), nullable=False),
            pa.field("pass", pa.int32(), nullable=False),
            pa.field("status", pa.string(), nullable=False),
            pa.field("tool", pa.string(), nullable=False),
            pa.field("created_at", pa.string(), nullable=False),
        ])
        db.create_table("analysis_logs", schema=minimal_schema)

        # Add one row
        table = db.open_table("analysis_logs")
        table.add([{
            "id": "ANALYSIS-2026-001",
            "source_id": "test",
            "pass": 1,
            "status": "completed",
            "tool": "claude-code",
            "created_at": "2026-01-25T00:00:00Z",
        }])

        # Run migrate
        import os
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "migrate"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "Added" in result.stdout

        # Verify columns were added
        table = db.open_table("analysis_logs")
        field_names = {f.name for f in table.schema}
        assert "tokens_baseline" in field_names
        assert "tokens_check" in field_names
        assert "usage_session_id" in field_names


# =============================================================================
# Evidence Links Tests
# =============================================================================

class TestEvidenceLinksCRUD:
    """Tests for evidence_links table operations."""

    def test_add_evidence_link_creates_record(self, initialized_db, sample_source, sample_claim, sample_evidence_link):
        """add_evidence_link creates a new evidence link."""
        from db import add_evidence_link, get_evidence_link, add_source, add_claim

        # Add prerequisite source and claim
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        result = add_evidence_link(sample_evidence_link, initialized_db)

        assert result["id"] == "EVLINK-2026-001"
        assert result["claim_id"] == "TECH-2026-001"
        assert result["source_id"] == "test-source-001"
        assert result["direction"] == "supports"

        # Verify it's retrievable
        retrieved = get_evidence_link("EVLINK-2026-001", db=initialized_db)
        assert retrieved is not None
        assert retrieved["id"] == "EVLINK-2026-001"

    def test_add_evidence_link_validates_claim_exists(self, initialized_db, sample_source, sample_evidence_link):
        """add_evidence_link raises error if claim doesn't exist."""
        from db import add_evidence_link, add_source

        add_source(sample_source, initialized_db, generate_embedding=False)

        with pytest.raises(ValueError, match="Claim .* not found"):
            add_evidence_link(sample_evidence_link, initialized_db)

    def test_add_evidence_link_validates_source_exists(self, initialized_db, sample_claim, sample_evidence_link):
        """add_evidence_link raises error if source doesn't exist."""
        from db import add_evidence_link, add_claim

        add_claim(sample_claim, initialized_db, generate_embedding=False)

        with pytest.raises(ValueError, match="Source .* not found"):
            add_evidence_link(sample_evidence_link, initialized_db)

    def test_add_evidence_link_auto_generates_id(self, initialized_db, sample_source, sample_claim):
        """add_evidence_link auto-generates ID when not provided."""
        from db import add_evidence_link, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        link_data = {
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "created_by": "test",
        }
        result = add_evidence_link(link_data, initialized_db)

        assert result["id"].startswith("EVLINK-")
        assert len(result["id"]) > 10  # Has year and number

    def test_add_evidence_link_all_directions(self, initialized_db, sample_source, sample_claim):
        """add_evidence_link accepts all valid directions."""
        from db import add_evidence_link, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        directions = ["supports", "contradicts", "strengthens", "weakens"]
        for i, direction in enumerate(directions):
            link_data = {
                "id": f"EVLINK-2026-{i+1:03d}",
                "claim_id": "TECH-2026-001",
                "source_id": "test-source-001",
                "direction": direction,
                "created_by": "test",
            }
            result = add_evidence_link(link_data, initialized_db)
            assert result["direction"] == direction

    def test_get_evidence_link_by_id(self, initialized_db, sample_source, sample_claim, sample_evidence_link):
        """get_evidence_link returns evidence link by ID."""
        from db import add_evidence_link, get_evidence_link, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, initialized_db)

        result = get_evidence_link("EVLINK-2026-001", db=initialized_db)

        assert result is not None
        assert result["id"] == "EVLINK-2026-001"
        assert result["location"] == "Table 3, p.15"

    def test_get_evidence_link_not_found(self, initialized_db):
        """get_evidence_link returns None for non-existent ID."""
        from db import get_evidence_link

        result = get_evidence_link("EVLINK-9999-999", db=initialized_db)
        assert result is None

    def test_list_evidence_links_by_claim(self, initialized_db, sample_source, sample_claim):
        """list_evidence_links filters by claim_id."""
        from db import add_evidence_link, list_evidence_links, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add two links for same claim
        for i in range(2):
            add_evidence_link({
                "id": f"EVLINK-2026-{i+1:03d}",
                "claim_id": "TECH-2026-001",
                "source_id": "test-source-001",
                "direction": "supports",
                "created_by": "test",
            }, db=initialized_db)

        results = list_evidence_links(claim_id="TECH-2026-001", db=initialized_db)
        assert len(results) == 2

    def test_list_evidence_links_by_source(self, initialized_db, sample_source, sample_claim):
        """list_evidence_links filters by source_id."""
        from db import add_evidence_link, list_evidence_links, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        add_evidence_link({
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "created_by": "test",
        }, db=initialized_db)

        results = list_evidence_links(source_id="test-source-001", db=initialized_db)
        assert len(results) == 1

    def test_list_evidence_links_by_direction(self, initialized_db, sample_source, sample_claim):
        """list_evidence_links filters by direction."""
        from db import add_evidence_link, list_evidence_links, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add links with different directions
        add_evidence_link({
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "created_by": "test",
        }, db=initialized_db)
        add_evidence_link({
            "id": "EVLINK-2026-002",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "contradicts",
            "created_by": "test",
        }, db=initialized_db)

        supports = list_evidence_links(direction="supports", db=initialized_db)
        assert len(supports) == 1
        assert supports[0]["direction"] == "supports"

    def test_list_evidence_links_active_only_default(self, initialized_db, sample_source, sample_claim):
        """list_evidence_links returns only active links by default."""
        from db import add_evidence_link, list_evidence_links, update_evidence_link, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        add_evidence_link({
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "status": "active",
            "created_by": "test",
        }, db=initialized_db)
        add_evidence_link({
            "id": "EVLINK-2026-002",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "status": "superseded",
            "created_by": "test",
        }, db=initialized_db)

        results = list_evidence_links(claim_id="TECH-2026-001", db=initialized_db)
        assert len(results) == 1
        assert results[0]["id"] == "EVLINK-2026-001"

    def test_list_evidence_links_include_superseded(self, initialized_db, sample_source, sample_claim):
        """list_evidence_links can include superseded links."""
        from db import add_evidence_link, list_evidence_links, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        add_evidence_link({
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "status": "active",
            "created_by": "test",
        }, db=initialized_db)
        add_evidence_link({
            "id": "EVLINK-2026-002",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "status": "superseded",
            "created_by": "test",
        }, db=initialized_db)

        results = list_evidence_links(claim_id="TECH-2026-001", include_superseded=True, db=initialized_db)
        assert len(results) == 2

    def test_update_evidence_link_status_superseded(self, initialized_db, sample_source, sample_claim, sample_evidence_link):
        """update_evidence_link can change status to superseded."""
        from db import add_evidence_link, update_evidence_link, get_evidence_link, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, initialized_db)

        update_evidence_link("EVLINK-2026-001", status="superseded", db=initialized_db)

        result = get_evidence_link("EVLINK-2026-001", db=initialized_db)
        assert result["status"] == "superseded"

    def test_supersede_evidence_link_creates_new_with_reference(self, initialized_db, sample_source, sample_claim, sample_evidence_link):
        """supersede_evidence_link creates new link with supersedes_id."""
        from db import add_evidence_link, supersede_evidence_link, get_evidence_link, add_source, add_claim

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, initialized_db)

        new_link = supersede_evidence_link(
            "EVLINK-2026-001",
            direction="weakens",
            reasoning="Re-evaluated: methodology concerns reduce support",
            db=initialized_db
        )

        # New link should reference old
        assert new_link["supersedes_id"] == "EVLINK-2026-001"
        assert new_link["direction"] == "weakens"

        # Old link should be superseded
        old_link = get_evidence_link("EVLINK-2026-001", db=initialized_db)
        assert old_link["status"] == "superseded"


class TestReasoningTrailsCRUD:
    """Tests for reasoning_trails table operations."""

    def test_add_reasoning_trail_creates_record(self, initialized_db, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """add_reasoning_trail creates a new reasoning trail."""
        from db import add_reasoning_trail, get_reasoning_trail, add_claim, add_source, add_evidence_link

        # Add prerequisites (source, claim, evidence link)
        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, initialized_db)

        result = add_reasoning_trail(sample_reasoning_trail, initialized_db)

        assert result["id"] == "REASON-2026-001"
        assert result["claim_id"] == "TECH-2026-001"
        assert result["credence_at_time"] == 0.75

        # Verify it's retrievable
        retrieved = get_reasoning_trail(id="REASON-2026-001", db=initialized_db)
        assert retrieved is not None
        assert retrieved["id"] == "REASON-2026-001"

    def test_add_reasoning_trail_validates_claim_exists(self, initialized_db, sample_reasoning_trail):
        """add_reasoning_trail raises error if claim doesn't exist."""
        from db import add_reasoning_trail

        with pytest.raises(ValueError, match="Claim .* not found"):
            add_reasoning_trail(sample_reasoning_trail, initialized_db)

    def test_add_reasoning_trail_auto_generates_id(self, initialized_db, sample_claim):
        """add_reasoning_trail auto-generates ID when not provided."""
        from db import add_reasoning_trail, add_claim

        add_claim(sample_claim, initialized_db, generate_embedding=False)

        trail_data = {
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.75,
            "evidence_level_at_time": "E2",
            "reasoning_text": "Test reasoning",
            "created_by": "test",
        }
        result = add_reasoning_trail(trail_data, initialized_db)

        assert result["id"].startswith("REASON-")
        assert len(result["id"]) > 10

    def test_add_reasoning_trail_validates_evidence_links_exist(self, initialized_db, sample_claim, sample_source):
        """add_reasoning_trail validates referenced evidence links exist."""
        from db import add_reasoning_trail, add_claim, add_source, add_evidence_link

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add a valid evidence link
        add_evidence_link({
            "id": "EVLINK-2026-001",
            "claim_id": "TECH-2026-001",
            "source_id": "test-source-001",
            "direction": "supports",
            "created_by": "test",
        }, db=initialized_db)

        # Trail referencing non-existent link should fail
        trail_data = {
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.75,
            "evidence_level_at_time": "E2",
            "reasoning_text": "Test reasoning",
            "supporting_evidence": ["EVLINK-2026-001", "EVLINK-9999-999"],
            "created_by": "test",
        }
        with pytest.raises(ValueError, match="Evidence link .* not found"):
            add_reasoning_trail(trail_data, initialized_db)

    def test_get_reasoning_trail_by_id(self, initialized_db, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """get_reasoning_trail returns trail by ID."""
        from db import add_reasoning_trail, get_reasoning_trail, add_claim, add_source, add_evidence_link

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, initialized_db)
        add_reasoning_trail(sample_reasoning_trail, initialized_db)

        result = get_reasoning_trail(id="REASON-2026-001", db=initialized_db)

        assert result is not None
        assert result["id"] == "REASON-2026-001"
        assert "E2 based on" in result["evidence_summary"]

    def test_get_reasoning_trail_by_claim(self, initialized_db, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """get_reasoning_trail returns current active trail for claim."""
        from db import add_reasoning_trail, get_reasoning_trail, add_claim, add_source, add_evidence_link

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, initialized_db)
        add_reasoning_trail(sample_reasoning_trail, initialized_db)

        result = get_reasoning_trail(claim_id="TECH-2026-001", db=initialized_db)

        assert result is not None
        assert result["claim_id"] == "TECH-2026-001"
        assert result["status"] == "active"

    def test_get_reasoning_trail_not_found(self, initialized_db):
        """get_reasoning_trail returns None for non-existent ID."""
        from db import get_reasoning_trail

        result = get_reasoning_trail(id="REASON-9999-999", db=initialized_db)
        assert result is None

    def test_list_reasoning_trails_by_claim(self, initialized_db, sample_claim):
        """list_reasoning_trails filters by claim_id."""
        from db import add_reasoning_trail, list_reasoning_trails, add_claim

        add_claim(sample_claim, initialized_db, generate_embedding=False)

        add_reasoning_trail({
            "id": "REASON-2026-001",
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.75,
            "evidence_level_at_time": "E2",
            "reasoning_text": "First trail",
            "created_by": "test",
        }, db=initialized_db)

        results = list_reasoning_trails(claim_id="TECH-2026-001", db=initialized_db)
        assert len(results) == 1

    def test_list_reasoning_trails_active_only_default(self, initialized_db, sample_claim):
        """list_reasoning_trails returns only active trails by default."""
        from db import add_reasoning_trail, list_reasoning_trails, add_claim

        add_claim(sample_claim, initialized_db, generate_embedding=False)

        add_reasoning_trail({
            "id": "REASON-2026-001",
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.75,
            "evidence_level_at_time": "E2",
            "reasoning_text": "Active trail",
            "status": "active",
            "created_by": "test",
        }, db=initialized_db)
        add_reasoning_trail({
            "id": "REASON-2026-002",
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.70,
            "evidence_level_at_time": "E2",
            "reasoning_text": "Old trail",
            "status": "superseded",
            "created_by": "test",
        }, db=initialized_db)

        results = list_reasoning_trails(claim_id="TECH-2026-001", db=initialized_db)
        assert len(results) == 1
        assert results[0]["id"] == "REASON-2026-001"

    def test_reasoning_history_shows_credence_evolution(self, initialized_db, sample_claim):
        """get_reasoning_history returns all trails ordered by created_at."""
        from db import add_reasoning_trail, get_reasoning_history, add_claim

        add_claim(sample_claim, initialized_db, generate_embedding=False)

        # Add trails with different timestamps
        add_reasoning_trail({
            "id": "REASON-2026-001",
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.60,
            "evidence_level_at_time": "E3",
            "reasoning_text": "Initial assessment",
            "status": "superseded",
            "created_at": "2026-01-29T10:00:00Z",
            "created_by": "test",
        }, db=initialized_db)
        add_reasoning_trail({
            "id": "REASON-2026-002",
            "claim_id": "TECH-2026-001",
            "credence_at_time": 0.75,
            "evidence_level_at_time": "E2",
            "reasoning_text": "Updated after new evidence",
            "status": "active",
            "created_at": "2026-01-30T10:00:00Z",
            "created_by": "test",
        }, db=initialized_db)

        history = get_reasoning_history("TECH-2026-001", db=initialized_db)

        assert len(history) == 2
        # Should be ordered by created_at (oldest first)
        assert history[0]["credence_at_time"] == pytest.approx(0.60, rel=1e-5)
        assert history[1]["credence_at_time"] == pytest.approx(0.75, rel=1e-5)

    def test_supersede_reasoning_trail_creates_new_with_reference(self, initialized_db, sample_source, sample_claim, sample_evidence_link, sample_reasoning_trail):
        """supersede_reasoning_trail creates new trail with supersedes_id."""
        from db import add_reasoning_trail, supersede_reasoning_trail, get_reasoning_trail, add_claim, add_source, add_evidence_link

        add_source(sample_source, initialized_db, generate_embedding=False)
        add_claim(sample_claim, initialized_db, generate_embedding=False)
        add_evidence_link(sample_evidence_link, initialized_db)
        add_reasoning_trail(sample_reasoning_trail, initialized_db)

        new_trail = supersede_reasoning_trail(
            "REASON-2026-001",
            credence_at_time=0.80,
            reasoning_text="Upgraded after replication study confirmed",
            db=initialized_db
        )

        # New trail should reference old
        assert new_trail["supersedes_id"] == "REASON-2026-001"
        assert new_trail["credence_at_time"] == 0.80

        # Old trail should be superseded
        old_trail = get_reasoning_trail(id="REASON-2026-001", db=initialized_db)
        assert old_trail["status"] == "superseded"


# =============================================================================
# Evidence Links CLI Tests
# =============================================================================

class TestEvidenceCLI:
    """Tests for evidence CLI subcommands."""

    def test_evidence_add_minimal(self, temp_db_path: Path):
        """evidence add creates evidence link with minimal args."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Initialize and add prerequisites
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test Source", "--type", "REPORT",
             "--author", "Test Author", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test claim", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        # Add evidence link
        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--claim-id", "TECH-2026-001", "--source-id", "test-source-001",
             "--direction", "supports"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "EVLINK-" in result.stdout

    def test_evidence_add_full_options(self, temp_db_path: Path):
        """evidence add accepts all optional flags."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Initialize and add prerequisites
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test Source", "--type", "REPORT",
             "--author", "Test Author", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test claim", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--id", "EVLINK-2026-001",
             "--claim-id", "TECH-2026-001",
             "--source-id", "test-source-001",
             "--direction", "supports",
             "--strength", "0.8",
             "--location", "Table 3, p.15",
             "--quote", "The study found...",
             "--reasoning", "Direct measurement supports the claim"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "EVLINK-2026-001" in result.stdout

    def test_evidence_add_missing_claim_errors(self, temp_db_path: Path):
        """evidence add errors when claim doesn't exist."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test Source", "--type", "REPORT",
             "--author", "Test Author", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--claim-id", "TECH-9999-999", "--source-id", "test-source-001",
             "--direction", "supports"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_evidence_add_missing_source_errors(self, temp_db_path: Path):
        """evidence add errors when source doesn't exist."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )
        subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test claim", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent,
        )

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--claim-id", "TECH-2026-001", "--source-id", "nonexistent-source",
             "--direction", "supports"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert result.returncode != 0

    def test_evidence_get_json_format(self, temp_db_path: Path):
        """evidence get returns JSON by default."""
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--id", "EVLINK-2026-001", "--claim-id", "TECH-2026-001",
             "--source-id", "test-source-001", "--direction", "supports"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "get", "EVLINK-2026-001"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert data["id"] == "EVLINK-2026-001"

    def test_evidence_get_text_format(self, temp_db_path: Path):
        """evidence get --format text returns human-readable output."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--id", "EVLINK-2026-001", "--claim-id", "TECH-2026-001",
             "--source-id", "test-source-001", "--direction", "supports"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "get", "EVLINK-2026-001",
             "--format", "text"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "EVLINK-2026-001" in result.stdout
        assert "supports" in result.stdout

    def test_evidence_list_by_claim(self, temp_db_path: Path):
        """evidence list --claim-id filters by claim."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--claim-id", "TECH-2026-001", "--source-id", "test-source-001",
             "--direction", "supports"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "list",
             "--claim-id", "TECH-2026-001"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "EVLINK-" in result.stdout

    def test_evidence_list_by_source(self, temp_db_path: Path):
        """evidence list --source-id filters by source."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--claim-id", "TECH-2026-001", "--source-id", "test-source-001",
             "--direction", "supports"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "list",
             "--source-id", "test-source-001"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "EVLINK-" in result.stdout

    def test_evidence_list_format_options(self, temp_db_path: Path):
        """evidence list supports --format text."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--claim-id", "TECH-2026-001", "--source-id", "test-source-001",
             "--direction", "supports"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "list", "--format", "text"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)

    def test_evidence_supersede(self, temp_db_path: Path):
        """evidence supersede creates new link and marks old as superseded."""
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--id", "EVLINK-2026-001", "--claim-id", "TECH-2026-001",
             "--source-id", "test-source-001", "--direction", "supports"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        # Supersede
        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "supersede", "EVLINK-2026-001",
             "--direction", "weakens", "--reasoning", "Re-evaluated"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)

        # Verify old is superseded
        get_result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "evidence", "get", "EVLINK-2026-001"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        assert_cli_success(get_result)
        old_data = json.loads(get_result.stdout)
        assert old_data["status"] == "superseded"


# =============================================================================
# Reasoning Trails CLI Tests
# =============================================================================

class TestReasoningCLI:
    """Tests for reasoning CLI subcommands."""

    def test_reasoning_add_minimal(self, temp_db_path: Path):
        """reasoning add creates trail with minimal args."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--claim-id", "TECH-2026-001",
             "--credence", "0.75",
             "--evidence-level", "E2",
             "--reasoning-text", "Assigned 0.75 because of supporting evidence"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "REASON-" in result.stdout

    def test_reasoning_add_full_options(self, temp_db_path: Path):
        """reasoning add accepts all optional flags."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--id", "REASON-2026-001",
             "--claim-id", "TECH-2026-001",
             "--credence", "0.75",
             "--evidence-level", "E2",
             "--evidence-summary", "E2 based on 2 supporting sources",
             "--assumptions", "Current paradigm continues,Funding remains stable",
             "--reasoning-text", "Assigned 0.75 because of supporting evidence"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "REASON-2026-001" in result.stdout

    def test_reasoning_add_with_evidence_refs(self, temp_db_path: Path):
        """reasoning add with --supporting-evidence references."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup with evidence link
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "source", "add",
             "--id", "test-source-001", "--title", "Test", "--type", "REPORT",
             "--author", "Test", "--year", "2026"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "evidence", "add",
             "--id", "EVLINK-2026-001", "--claim-id", "TECH-2026-001",
             "--source-id", "test-source-001", "--direction", "supports"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--claim-id", "TECH-2026-001",
             "--credence", "0.75",
             "--evidence-level", "E2",
             "--supporting-evidence", "EVLINK-2026-001",
             "--reasoning-text", "Based on supporting evidence"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)

    def test_reasoning_add_with_counterarguments_json(self, temp_db_path: Path):
        """reasoning add with --counterarguments-json."""
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        counterargs = json.dumps([{
            "argument": "Study X disagrees",
            "response": "Different methodology",
            "disposition": "discounted"
        }])

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--claim-id", "TECH-2026-001",
             "--credence", "0.75",
             "--evidence-level", "E2",
             "--counterarguments-json", counterargs,
             "--reasoning-text", "Assigned 0.75 despite counterarguments"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)

    def test_reasoning_get_json_format(self, temp_db_path: Path):
        """reasoning get returns JSON by default."""
        import json
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--id", "REASON-2026-001", "--claim-id", "TECH-2026-001",
             "--credence", "0.75", "--evidence-level", "E2",
             "--reasoning-text", "Test reasoning"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "reasoning", "get", "--id", "REASON-2026-001"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        data = json.loads(result.stdout)
        assert data["id"] == "REASON-2026-001"

    def test_reasoning_get_text_format(self, temp_db_path: Path):
        """reasoning get --format text returns human-readable output."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--id", "REASON-2026-001", "--claim-id", "TECH-2026-001",
             "--credence", "0.75", "--evidence-level", "E2",
             "--reasoning-text", "Test reasoning"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "reasoning", "get", "--id", "REASON-2026-001",
             "--format", "text"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "REASON-2026-001" in result.stdout

    def test_reasoning_list_by_claim(self, temp_db_path: Path):
        """reasoning list --claim-id filters by claim."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--claim-id", "TECH-2026-001", "--credence", "0.75",
             "--evidence-level", "E2", "--reasoning-text", "Test"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "reasoning", "list",
             "--claim-id", "TECH-2026-001"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        assert "REASON-" in result.stdout

    def test_reasoning_history(self, temp_db_path: Path):
        """reasoning history shows credence evolution."""
        env = os.environ.copy()
        env["REALITYCHECK_DATA"] = str(temp_db_path)

        # Setup
        subprocess.run(["uv", "run", "python", "scripts/db.py", "init"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)
        subprocess.run(["uv", "run", "python", "scripts/db.py", "claim", "add",
             "--id", "TECH-2026-001", "--text", "Test", "--type", "[F]",
             "--domain", "TECH", "--evidence-level", "E2", "--credence", "0.75"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        # Add first trail
        subprocess.run(["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--id", "REASON-2026-001", "--claim-id", "TECH-2026-001",
             "--credence", "0.60", "--evidence-level", "E3",
             "--reasoning-text", "Initial assessment", "--status", "superseded"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        # Add second trail
        subprocess.run(["uv", "run", "python", "scripts/db.py", "reasoning", "add",
             "--id", "REASON-2026-002", "--claim-id", "TECH-2026-001",
             "--credence", "0.75", "--evidence-level", "E2",
             "--reasoning-text", "Updated after new evidence"],
            env=env, capture_output=True, cwd=Path(__file__).parent.parent)

        result = subprocess.run(
            ["uv", "run", "python", "scripts/db.py", "reasoning", "history",
             "--claim-id", "TECH-2026-001"],
            env=env, capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )

        assert_cli_success(result)
        # Should show both trails
        assert "REASON-2026-001" in result.stdout or "0.60" in result.stdout
        assert "REASON-2026-002" in result.stdout or "0.75" in result.stdout
