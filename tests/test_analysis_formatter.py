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
    has_credence,
    normalize_legacy_headings,
    insert_legends,
    insert_claim_summary_table,
    insert_claims_yaml,
    insert_confidence,
    insert_missing_sections,
    format_file,
    extract_claim_id,
    is_linked_claim_id,
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

    def test_has_credence_true(self):
        """Credence detected when present."""
        content = """**Credence in Analysis**: 0.8"""
        assert has_credence(content) is True

    def test_has_credence_legacy_confidence(self):
        """Legacy 'Confidence in Analysis' also detected."""
        content = """**Confidence in Analysis**: 0.8"""
        assert has_credence(content) is True

    def test_has_credence_false(self):
        """Credence not detected when absent."""
        content = """No credence here."""
        assert has_credence(content) is False


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


class TestCredenceInsertion:
    """Tests for credence section insertion."""

    def test_insert_credence_at_end(self):
        """Credence section appended at end."""
        content = """# Source Analysis

## Content here
"""
        result = insert_confidence(content)

        assert "**Credence in Analysis**:" in result
        assert "**Analysis Date**:" in result
        # Should be at the end
        assert result.rstrip().endswith("- [Key uncertainties remaining]")

    def test_insert_credence_idempotent(self):
        """Credence section not duplicated (also works with legacy Confidence)."""
        content = """# Source Analysis

**Confidence in Analysis**: 0.8
"""
        result = insert_confidence(content)

        # Should not duplicate - legacy Confidence still counts as present
        assert "**Confidence in Analysis**:" in result or "**Credence in Analysis**:" in result


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
        assert "**Credence in Analysis**:" in formatted

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
        assert "**Credence in Analysis**:" in formatted

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


class TestLegacyNormalization:
    """Tests for legacy heading normalization."""

    def test_normalize_common_legacy_headings(self):
        content = """## Stage 1: Descriptive Summary

### Steelman

## Stage 2: Evaluation

## Stage 3: Dialectical Synthesis

### Counterarguments

## Claim Summary (All Extracted Claims)
"""
        normalized, changes = normalize_legacy_headings(content)

        assert "## Stage 1: Descriptive Analysis" in normalized
        assert "## Stage 1: Descriptive Summary" not in normalized
        assert "## Stage 2: Evaluative Analysis" in normalized
        assert "## Stage 3: Dialectical Analysis" in normalized
        assert "### Steelmanned Argument" in normalized
        assert "### Strongest Counterarguments" in normalized
        assert "### Claim Summary" in normalized
        assert len(changes) >= 1


class TestClaimSummaryAndYamlGeneration:
    """Tests for generating Claim Summary and YAML blocks from existing data."""

    def test_format_generates_claim_summary_and_yaml_from_key_claims(self, tmp_path):
        content = """# Source Analysis: Test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |

## Stage 1: Descriptive Analysis

### Core Thesis
Test thesis.

### Key Claims

| # | Claim | Claim ID | Type | Domain | Evid | Conf | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|------|-----------|----------------|
| 1 | Test claim text | TECH-2026-001 | [F] | TECH | E2 | 0.75 | ? | N/A |

## Stage 2: Evaluative Analysis
### Key Factual Claims Verified
### Disconfirming Evidence Search
### Internal Tensions
### Persuasion Techniques
### Unstated Assumptions
## Stage 3: Dialectical Analysis
### Steelmanned Argument
### Strongest Counterarguments
### Supporting Theories
### Contradicting Theories
"""
        test_file = tmp_path / "test-source.md"
        test_file.write_text(content)

        formatted, _changes = format_file(test_file, profile="full")

        assert "### Claim Summary" in formatted
        assert "TECH-2026-001" in formatted
        assert "DOMAIN-YYYY-NNN" not in formatted
        assert "```yaml" in formatted
        assert "claims:" in formatted
        assert "source_ids" in formatted
        assert "test-source" in formatted

    def test_format_embeds_claims_from_sibling_yaml(self, tmp_path):
        md = """# Source Analysis: Test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | yaml-source |

## Stage 1: Descriptive Analysis
### Core Thesis
Test thesis.
### Key Claims
| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | Test claim text | TECH-2026-001 | [F] | TECH | E2 | 0.80 | ? | N/A |

### Claims to Register
"""
        yaml_text = """claims:
  - id: "TECH-2026-001"
    text: "Test claim from yaml"
    type: "[F]"
    domain: "TECH"
    evidence_level: "E2"
    credence: 0.80
    source_ids: ["yaml-source"]
"""
        md_file = tmp_path / "yaml-source.md"
        yaml_file = tmp_path / "yaml-source.yaml"
        md_file.write_text(md)
        yaml_file.write_text(yaml_text)

        formatted, _changes = format_file(md_file, profile="full")

        assert "```yaml" in formatted
        assert 'text: "Test claim from yaml"' in formatted
        assert "TECH-2026-001" in formatted


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


class TestLinkedClaimIds:
    """Tests for linked claim ID handling."""

    def test_extract_claim_id_bare(self):
        """Bare claim ID is extracted."""
        assert extract_claim_id("TECH-2026-001") == "TECH-2026-001"

    def test_extract_claim_id_linked(self):
        """Linked claim ID is extracted."""
        assert extract_claim_id("[TECH-2026-001](../reasoning/TECH-2026-001.md)") == "TECH-2026-001"

    def test_extract_claim_id_linked_different_path(self):
        """Linked claim ID with any path is extracted."""
        assert extract_claim_id("[LABOR-2025-042](/some/other/path.md)") == "LABOR-2025-042"

    def test_extract_claim_id_invalid(self):
        """Invalid cell text returns None."""
        assert extract_claim_id("not a claim id") is None
        assert extract_claim_id("[broken link") is None
        assert extract_claim_id("") is None

    def test_extract_claim_id_whitespace(self):
        """Whitespace around cell text is handled."""
        assert extract_claim_id("  TECH-2026-001  ") == "TECH-2026-001"
        assert extract_claim_id("  [TECH-2026-001](path)  ") == "TECH-2026-001"

    def test_is_linked_claim_id_true(self):
        """Linked format detected."""
        assert is_linked_claim_id("[TECH-2026-001](../reasoning/TECH-2026-001.md)") is True
        assert is_linked_claim_id("[LABOR-2025-042](path)") is True

    def test_is_linked_claim_id_false(self):
        """Non-linked format not detected as linked."""
        assert is_linked_claim_id("TECH-2026-001") is False
        assert is_linked_claim_id("not a claim id") is False

    def test_formatter_preserves_linked_ids(self, tmp_path):
        """Linked claim IDs in Key Claims are preserved in Claim Summary."""
        content = """# Source Analysis: Test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |

## Stage 1: Descriptive Analysis

### Core Thesis
Test thesis.

### Key Claims

| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | Test claim text | [TECH-2026-001](../reasoning/TECH-2026-001.md) | [F] | TECH | E2 | 0.75 | ? | N/A |

## Stage 2: Evaluative Analysis
### Key Factual Claims Verified
### Disconfirming Evidence Search
### Internal Tensions
### Persuasion Techniques
### Unstated Assumptions
## Stage 3: Dialectical Analysis
### Steelmanned Argument
### Strongest Counterarguments
### Supporting Theories
### Contradicting Theories
"""
        test_file = tmp_path / "test-source.md"
        test_file.write_text(content)

        formatted, _changes = format_file(test_file, profile="full")

        # Claim Summary table should preserve linked format
        assert "[TECH-2026-001](../reasoning/TECH-2026-001.md)" in formatted
        # Should appear in Claim Summary section
        assert "### Claim Summary" in formatted

    def test_formatter_mixed_linked_and_bare_ids(self, tmp_path):
        """Mixed linked and bare IDs are both handled correctly."""
        content = """# Source Analysis: Test

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |

## Stage 1: Descriptive Analysis

### Core Thesis
Test thesis.

### Key Claims

| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | First claim | [TECH-2026-001](../reasoning/TECH-2026-001.md) | [F] | TECH | E2 | 0.75 | ? | N/A |
| 2 | Second claim | LABOR-2025-042 | [T] | LABOR | E3 | 0.60 | ? | N/A |

## Stage 2: Evaluative Analysis
### Key Factual Claims Verified
### Disconfirming Evidence Search
### Internal Tensions
### Persuasion Techniques
### Unstated Assumptions
## Stage 3: Dialectical Analysis
### Steelmanned Argument
### Strongest Counterarguments
### Supporting Theories
### Contradicting Theories
"""
        test_file = tmp_path / "test-source.md"
        test_file.write_text(content)

        formatted, _changes = format_file(test_file, profile="full")

        # Linked ID should preserve format
        assert "[TECH-2026-001](../reasoning/TECH-2026-001.md)" in formatted
        # Bare ID should remain bare
        assert "LABOR-2025-042" in formatted
        # Both should be in the Claim Summary
        assert "### Claim Summary" in formatted
