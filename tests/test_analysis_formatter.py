"""
Unit tests for scripts/analysis_formatter.py

Tests cover:
- Legend insertion
- Section insertion
- Table insertion
- YAML block insertion
- Idempotency
- Profile detection and handling
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from analysis_formatter import (
    detect_profile,
    has_legends,
    has_section,
    has_claims_yaml,
    has_confidence,
    insert_legends,
    insert_claim_summary_table,
    insert_claims_yaml,
    insert_confidence,
    insert_missing_sections,
    format_file,
)


class TestHelperFunctions:
    """Tests for detection helper functions."""

    def test_has_legends_true(self):
        """Legends detected when present."""
        content = """> **Claim types**: `[F]` fact
> **Evidence**: **E1** test
"""
        assert has_legends(content) is True

    def test_has_legends_false(self):
        """Legends not detected when absent."""
        content = """# Source Analysis
Some other content.
"""
        assert has_legends(content) is False

    def test_has_section_true(self):
        """Section detected when present."""
        content = """## Metadata
Some metadata here.
"""
        assert has_section(content, "## Metadata") is True

    def test_has_section_false(self):
        """Section not detected when absent."""
        content = """# Source Analysis
No metadata section.
"""
        assert has_section(content, "## Metadata") is False

    def test_has_section_case_insensitive(self):
        """Section detection is case-insensitive."""
        content = """## METADATA
Some content.
"""
        assert has_section(content, "## Metadata") is True

    def test_has_claims_yaml_true(self):
        """YAML block detected when present."""
        content = """### Claims to Register

```yaml
claims:
  - id: "TEST-2026-001"
```
"""
        assert has_claims_yaml(content) is True

    def test_has_claims_yaml_false(self):
        """YAML block not detected when absent."""
        content = """### Claims to Register

- Claim 1
- Claim 2
"""
        assert has_claims_yaml(content) is False

    def test_has_confidence_true(self):
        """Confidence detected when present."""
        content = """**Confidence in Analysis**: 0.8"""
        assert has_confidence(content) is True

    def test_has_confidence_false(self):
        """Confidence not detected when absent."""
        content = """No confidence here."""
        assert has_confidence(content) is False


class TestLegendInsertion:
    """Tests for legend insertion."""

    def test_insert_legends_after_title(self):
        """Legends inserted after title."""
        content = """# Source Analysis: Test

## Metadata
"""
        result = insert_legends(content)

        assert "> **Claim types**:" in result
        assert "> **Evidence**:" in result
        # Legends should come before Metadata
        assert result.index("> **Claim types**:") < result.index("## Metadata")

    def test_insert_legends_idempotent(self):
        """Legends not duplicated if already present."""
        content = """# Source Analysis: Test

> **Claim types**: `[F]` fact
> **Evidence**: **E1** test

## Metadata
"""
        result = insert_legends(content)

        # Should have exactly one legend block
        assert result.count("> **Claim types**:") == 1

    def test_insert_legends_no_title(self):
        """Legends prepended if no title found."""
        content = """## Metadata
Some content.
"""
        result = insert_legends(content)

        assert result.startswith("> **Claim types**:")


class TestTableInsertion:
    """Tests for table insertion."""

    def test_insert_claim_summary_after_header(self):
        """Claim Summary table inserted after header."""
        content = """# Source Analysis

### Claim Summary

### Claims to Register
"""
        result = insert_claim_summary_table(content)

        assert "| ID | Type | Domain | Evidence | Credence | Claim |" in result
        # Table should be after the header
        header_pos = result.index("### Claim Summary")
        table_pos = result.index("| ID | Type |")
        assert table_pos > header_pos

    def test_insert_claim_summary_idempotent(self):
        """Claim Summary table not duplicated."""
        content = """# Source Analysis

### Claim Summary

| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | E2 | 0.75 | Test |

"""
        result = insert_claim_summary_table(content)

        # Should have exactly one table
        assert result.count("| ID | Type | Domain | Evidence | Credence | Claim |") == 1


class TestYamlInsertion:
    """Tests for YAML block insertion."""

    def test_insert_yaml_after_header(self):
        """YAML block inserted after Claims to Register header."""
        content = """# Source Analysis

### Claims to Register

---
"""
        result = insert_claims_yaml(content)

        assert "```yaml" in result
        assert "claims:" in result
        # YAML should be after the header
        header_pos = result.index("### Claims to Register")
        yaml_pos = result.index("```yaml")
        assert yaml_pos > header_pos

    def test_insert_yaml_idempotent(self):
        """YAML block not duplicated."""
        content = """### Claims to Register

```yaml
claims:
  - id: "TEST-2026-001"
```
"""
        result = insert_claims_yaml(content)

        # Should have exactly one YAML block
        assert result.count("```yaml") == 1
        assert result.count("claims:") == 1


class TestConfidenceInsertion:
    """Tests for confidence section insertion."""

    def test_insert_confidence_at_end(self):
        """Confidence section appended at end."""
        content = """# Source Analysis

## Content here
"""
        result = insert_confidence(content)

        assert "**Confidence in Analysis**:" in result
        assert "**Analysis Date**:" in result
        # Should be at the end
        assert result.rstrip().endswith("- [Key uncertainties remaining]")

    def test_insert_confidence_idempotent(self):
        """Confidence section not duplicated."""
        content = """# Source Analysis

**Confidence in Analysis**: 0.8
"""
        result = insert_confidence(content)

        assert result.count("**Confidence in Analysis**:") == 1


class TestSectionInsertion:
    """Tests for missing section insertion."""

    def test_insert_missing_quick_sections(self):
        """Missing quick profile sections inserted."""
        content = """# Source Analysis

## Metadata
"""
        result = insert_missing_sections(content, "quick")

        assert "## Summary" in result
        assert "### Claim Summary" in result
        assert "### Claims to Register" in result

    def test_insert_missing_full_sections(self):
        """Missing full profile sections inserted."""
        content = """# Source Analysis

## Metadata
"""
        result = insert_missing_sections(content, "full")

        assert "## Stage 1: Descriptive Analysis" in result
        assert "## Stage 2: Evaluative Analysis" in result
        assert "## Stage 3: Dialectical Analysis" in result
        assert "### Core Thesis" in result


class TestFileFormatting:
    """End-to-end file formatting tests."""

    def test_format_minimal_quick_analysis(self, tmp_path):
        """Minimal file gets all quick profile elements added."""
        content = """# Source Analysis: Test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |
| **Analysis Depth** | quick |
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        formatted, changes = format_file(test_file)

        # Should have added missing elements
        assert len(changes) > 0
        assert "> **Claim types**:" in formatted
        assert "## Summary" in formatted
        assert "### Claim Summary" in formatted
        assert "### Claims to Register" in formatted
        assert "```yaml" in formatted

    def test_format_idempotent(self, tmp_path):
        """Running formatter twice produces same result."""
        content = """# Source Analysis: Test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |
| **Analysis Depth** | quick |
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        # First run
        formatted1, changes1 = format_file(test_file)
        test_file.write_text(formatted1)

        # Second run
        formatted2, changes2 = format_file(test_file)

        # Second run should have no changes
        assert len(changes2) == 0
        assert formatted1 == formatted2

    def test_format_dry_run(self, tmp_path):
        """Dry run doesn't modify file."""
        content = """# Source Analysis: Test

## Metadata
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        original = test_file.read_text()
        format_file(test_file, dry_run=True)

        # File should be unchanged
        assert test_file.read_text() == original

    def test_format_full_profile(self, tmp_path):
        """Full profile gets all required elements."""
        content = """# Source Analysis: Test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |
| **Analysis Depth** | full |
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        formatted, changes = format_file(test_file)

        # Should have all full profile elements
        assert "## Stage 1: Descriptive Analysis" in formatted
        assert "## Stage 2: Evaluative Analysis" in formatted
        assert "## Stage 3: Dialectical Analysis" in formatted
        assert "**Confidence in Analysis**:" in formatted

    def test_format_profile_override(self, tmp_path):
        """Profile can be overridden."""
        content = """# Source Analysis: Test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |
| **Analysis Depth** | quick |
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        # Force full profile despite quick marker
        formatted, changes = format_file(test_file, profile="full")

        # Should have full profile elements
        assert "## Stage 1: Descriptive Analysis" in formatted
        assert "**Confidence in Analysis**:" in formatted

    def test_format_preserves_existing_content(self, tmp_path):
        """Existing content is preserved."""
        content = """# Source Analysis: Test

> **Claim types**: `[F]` fact, `[T]` theory
> **Evidence**: **E1** test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |
| **Analysis Depth** | quick |

## Summary

This is my existing summary that should be preserved.

### Claim Summary

| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | E2 | 0.75 | My existing claim |

### Claims to Register

```yaml
claims:
  - id: "TECH-2026-001"
    text: "My existing claim"
```
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        formatted, changes = format_file(test_file)

        # Should preserve existing content
        assert "This is my existing summary that should be preserved." in formatted
        assert "My existing claim" in formatted
        # Should have no changes
        assert len(changes) == 0

    def test_format_nonexistent_file(self, tmp_path):
        """Nonexistent file returns error."""
        test_file = tmp_path / "nonexistent.md"

        formatted, changes = format_file(test_file)

        assert formatted == ""
        assert len(changes) >= 1
        assert any("Error" in c for c in changes)


class TestProfileDetection:
    """Tests for profile detection in formatter."""

    def test_detect_quick_profile(self):
        """Quick profile detected from marker."""
        content = """**Analysis Depth**: quick"""
        assert detect_profile(content) == "quick"

    def test_detect_full_profile_default(self):
        """Full profile is default."""
        content = """# Source Analysis
No depth marker.
"""
        assert detect_profile(content) == "full"
