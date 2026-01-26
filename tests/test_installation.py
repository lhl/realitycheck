#!/usr/bin/env python3
"""
Installation verification tests for Reality Check.

These tests verify that the package works correctly when installed,
catching import issues that might not be detected when running from source.

Tests cover:
- Entry point imports work as installed package
- CLI commands can be invoked
- Inter-module imports resolve correctly
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestPackageImports:
    """Test that all package modules can be imported correctly."""

    def test_import_scripts_db(self):
        """scripts.db should be importable."""
        from scripts import db
        assert hasattr(db, "main")
        assert hasattr(db, "get_db")
        assert hasattr(db, "init_tables")

    def test_import_scripts_validate(self):
        """scripts.validate should be importable."""
        from scripts import validate
        assert hasattr(validate, "main")
        assert hasattr(validate, "validate_db")

    def test_import_scripts_export(self):
        """scripts.export should be importable."""
        from scripts import export
        assert hasattr(export, "main")
        assert hasattr(export, "export_claims_yaml")

    def test_import_scripts_migrate(self):
        """scripts.migrate should be importable."""
        from scripts import migrate
        assert hasattr(migrate, "main")
        assert hasattr(migrate, "migrate_domain")

    def test_import_scripts_embed(self):
        """scripts.embed should be importable."""
        from scripts import embed
        assert hasattr(embed, "main")
        assert hasattr(embed, "check_embeddings")

    def test_import_scripts_html_extract(self):
        """scripts.html_extract should be importable."""
        from scripts import html_extract
        assert hasattr(html_extract, "main")

    def test_import_scripts_usage_capture(self):
        """scripts.usage_capture should be importable."""
        from scripts import usage_capture
        assert hasattr(usage_capture, "estimate_cost_usd")
        assert hasattr(usage_capture, "get_session_token_count")

    def test_import_scripts_analysis_log_writer(self):
        """scripts.analysis_log_writer should be importable."""
        from scripts import analysis_log_writer
        assert hasattr(analysis_log_writer, "upsert_analysis_log_section")


class TestCrossModuleImports:
    """Test that cross-module imports work correctly when installed."""

    def test_db_imports_usage_capture(self):
        """db.py should successfully import from usage_capture."""
        from scripts.db import (
            estimate_cost_usd,
            get_current_session_path,
            get_session_token_count,
        )
        # These are re-exported from usage_capture, verify they exist
        assert callable(estimate_cost_usd)
        # get_current_session_path and get_session_token_count may not be re-exported
        # but the import should not fail

    def test_db_imports_analysis_log_writer(self):
        """db.py should successfully import from analysis_log_writer."""
        from scripts.db import upsert_analysis_log_section
        assert callable(upsert_analysis_log_section)

    def test_validate_imports_db(self):
        """validate.py should successfully import from db."""
        from scripts.validate import (
            VALID_DOMAINS,
            get_db,
            list_claims,
        )
        assert isinstance(VALID_DOMAINS, (list, tuple, set, frozenset))
        assert callable(get_db)
        assert callable(list_claims)

    def test_export_imports_db(self):
        """export.py should successfully import from db."""
        from scripts.export import (
            get_db,
            list_claims,
            list_sources,
        )
        assert callable(get_db)
        assert callable(list_claims)
        assert callable(list_sources)

    def test_migrate_imports_db(self):
        """migrate.py should successfully import from db."""
        from scripts.migrate import (
            DOMAIN_MIGRATION,
            add_claim,
            get_db,
        )
        assert isinstance(DOMAIN_MIGRATION, dict)
        assert callable(add_claim)
        assert callable(get_db)

    def test_embed_imports_db(self):
        """embed.py should successfully import from db."""
        from scripts.embed import (
            get_db,
            embed_text,
            list_claims,
        )
        assert callable(get_db)
        assert callable(embed_text)
        assert callable(list_claims)


class TestEntryPointsCLI:
    """Test that CLI entry points can be invoked."""

    def test_rc_db_help(self):
        """rc-db --help should run without error."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.db", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Reality Check Database CLI" in result.stdout

    def test_rc_validate_help(self):
        """rc-validate --help should run without error."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.validate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Validate Reality Check" in result.stdout

    def test_rc_export_help(self):
        """rc-export --help should run without error."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.export", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Export Reality Check" in result.stdout

    def test_rc_embed_help(self):
        """rc-embed --help should run without error."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.embed", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Embedding" in result.stdout

    def test_rc_migrate_help(self):
        """rc-migrate --help should run without error."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.migrate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Migrate" in result.stdout


class TestPackageStructure:
    """Test that the package structure is correct."""

    def test_scripts_is_package(self):
        """scripts directory should be a Python package."""
        import scripts
        assert hasattr(scripts, "__path__")
        assert hasattr(scripts, "__file__")

    def test_scripts_has_init(self):
        """scripts/__init__.py should exist."""
        import scripts
        init_path = Path(scripts.__file__)
        assert init_path.name == "__init__.py"
        assert init_path.exists()

    def test_all_modules_accessible(self):
        """All core modules should be accessible from scripts package."""
        from scripts import db
        from scripts import validate
        from scripts import export
        from scripts import migrate
        from scripts import embed
        from scripts import html_extract
        from scripts import usage_capture
        from scripts import analysis_log_writer

        # Verify they're all modules
        for mod in [db, validate, export, migrate, embed, html_extract,
                    usage_capture, analysis_log_writer]:
            assert hasattr(mod, "__name__")
            assert mod.__name__.startswith("scripts.")
