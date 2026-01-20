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


# =============================================================================
# CLI Command Tests
# =============================================================================

import subprocess
import json
import os


class TestClaimCLI:
    """Tests for claim CLI subcommands."""

    def test_claim_add_creates_claim(self, temp_db_path: Path):
        """claim add creates a new claim."""
        env = os.environ.copy()
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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

    def test_import_handles_missing_file(self, temp_db_path: Path):
        """import returns error for missing file."""
        env = os.environ.copy()
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
        env["ANALYSIS_DB_PATH"] = str(temp_db_path)

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
