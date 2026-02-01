"""
Unit tests for scripts/analysis_validator.py

Tests cover:
- Full profile validation (required sections, tables, elements)
- Quick profile validation (minimal required sections)
- Profile detection
- Claim ID validation
- Framework repo detection
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from analysis_validator import (
    detect_profile,
    validate_file,
    validate_sections,
    validate_tables,
    validate_elements,
    validate_claim_ids,
    check_framework_repo,
    extract_claim_id,
    has_section,
    FULL_PROFILE_REQUIRED,
    QUICK_PROFILE_REQUIRED,
)


class TestProfileDetection:
    """Tests for profile detection."""

    def test_detect_quick_profile(self):
        """Quick profile detected from Analysis Depth marker."""
        content = """# Source Analysis: Test
**Analysis Depth**: quick
"""
        assert detect_profile(content) == "quick"

    def test_detect_quick_profile_case_insensitive(self):
        """Profile detection is case-insensitive."""
        content = """**Analysis Depth**: QUICK"""
        assert detect_profile(content) == "quick"

    def test_detect_full_profile_default(self):
        """Full profile is default when no quick marker."""
        content = """# Source Analysis: Test
**Analysis Depth**: full
"""
        assert detect_profile(content) == "full"

    def test_detect_full_profile_missing_marker(self):
        """Full profile when no Analysis Depth marker present."""
        content = """# Source Analysis: Test
## Metadata
Some content here.
"""
        assert detect_profile(content) == "full"


class TestSectionValidation:
    """Tests for section validation."""

    def test_all_sections_present(self):
        """No errors when all required sections present."""
        content = """# Source Analysis
## Metadata
## Summary
### Claim Summary
### Claims to Register
"""
        errors = validate_sections(content, QUICK_PROFILE_REQUIRED["sections"])
        assert len(errors) == 0

    def test_missing_section_detected(self):
        """Missing section produces error."""
        content = """# Source Analysis
## Metadata
### Claims to Register
"""
        # Missing ## Summary and ### Claim Summary
        errors = validate_sections(content, QUICK_PROFILE_REQUIRED["sections"])
        assert len(errors) >= 2
        assert any("## Summary" in e for e in errors)
        assert any("### Claim Summary" in e for e in errors)

    def test_section_case_insensitive(self):
        """Section matching is case-insensitive."""
        content = """# Source Analysis
## metadata
## summary
### claim summary
### claims to register
"""
        errors = validate_sections(content, QUICK_PROFILE_REQUIRED["sections"])
        assert len(errors) == 0


class TestTableValidation:
    """Tests for table validation."""

    def test_claim_summary_table_present(self):
        """Claim Summary table detected."""
        content = """### Claim Summary

| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | E2 | 0.75 | Test claim |
"""
        errors = validate_tables(content, QUICK_PROFILE_REQUIRED["tables"])
        assert len(errors) == 0

    def test_missing_table_detected(self):
        """Missing table produces error."""
        content = """### Claim Summary

No table here.
"""
        errors = validate_tables(content, QUICK_PROFILE_REQUIRED["tables"])
        assert len(errors) >= 1
        assert any("Claim Summary table" in e for e in errors)

    def test_key_claims_table_full_profile(self):
        """Key Claims table detected for full profile."""
        content = """### Key Claims

| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | Test | TECH-2026-001 | [F] | TECH | E2 | 0.75 | Yes | Nothing |
"""
        errors = validate_tables(content, FULL_PROFILE_REQUIRED["tables"])
        # Should find Key Claims table
        key_claims_errors = [e for e in errors if "Key Claims table" in e]
        assert len(key_claims_errors) == 0


class TestElementValidation:
    """Tests for element validation."""

    def test_legends_present(self):
        """Legends block detected."""
        content = """> **Claim types**: `[F]` fact, `[T]` theory
> **Evidence**: **E1** systematic review
"""
        elements = [e for e in QUICK_PROFILE_REQUIRED["elements"] if "legend" in e[1].lower()]
        errors = validate_elements(content, elements)
        assert len(errors) == 0

    def test_missing_legends_detected(self):
        """Missing legends produces error."""
        content = """# Source Analysis
No legends here.
"""
        elements = [e for e in QUICK_PROFILE_REQUIRED["elements"] if "legend" in e[1].lower()]
        errors = validate_elements(content, elements)
        assert len(errors) >= 1

    def test_yaml_block_present(self):
        """Claims YAML block detected."""
        content = """### Claims to Register

```yaml
claims:
  - id: "TECH-2026-001"
    text: "Test claim"
```
"""
        elements = [e for e in QUICK_PROFILE_REQUIRED["elements"] if "YAML" in e[1]]
        errors = validate_elements(content, elements)
        assert len(errors) == 0

    def test_missing_yaml_block_detected(self):
        """Missing YAML block produces error."""
        content = """### Claims to Register

- Claim 1
- Claim 2
"""
        elements = [e for e in QUICK_PROFILE_REQUIRED["elements"] if "YAML" in e[1]]
        errors = validate_elements(content, elements)
        assert len(errors) >= 1


class TestClaimIdValidation:
    """Tests for claim ID format validation."""

    def test_valid_claim_ids(self):
        """Valid claim IDs produce no warnings."""
        content = """TECH-2026-001, LABOR-2025-042"""
        warnings = validate_claim_ids(content)
        # No placeholder warning, IDs found
        assert not any("No claim IDs found" in w for w in warnings)
        assert not any("placeholder" in w for w in warnings)

    def test_placeholder_id_detected(self):
        """Placeholder claim ID produces warning."""
        content = """| DOMAIN-YYYY-NNN | [F] | DOMAIN |"""
        warnings = validate_claim_ids(content)
        assert any("placeholder" in w for w in warnings)

    def test_no_claim_ids_warning(self):
        """Missing claim IDs produces warning."""
        content = """# Source Analysis
No claim IDs here at all.
"""
        warnings = validate_claim_ids(content)
        assert any("No claim IDs found" in w for w in warnings)

    def test_linked_claim_ids_recognized(self):
        """Markdown-linked claim IDs are recognized."""
        content = """| [TECH-2026-001](../reasoning/TECH-2026-001.md) | [F] | TECH |"""
        warnings = validate_claim_ids(content)
        # Should find the claim ID
        assert not any("No claim IDs found" in w for w in warnings)

    def test_mixed_linked_and_bare_ids(self):
        """Both linked and bare claim IDs are found."""
        content = """| [TECH-2026-001](path) | [F] | TECH |
| LABOR-2025-042 | [T] | LABOR |"""
        warnings = validate_claim_ids(content)
        assert not any("No claim IDs found" in w for w in warnings)


class TestExtractClaimId:
    """Tests for the extract_claim_id helper function."""

    def test_extract_bare_id(self):
        """Bare claim ID is extracted."""
        assert extract_claim_id("TECH-2026-001") == "TECH-2026-001"

    def test_extract_linked_id(self):
        """Linked claim ID is extracted."""
        assert extract_claim_id("[TECH-2026-001](../reasoning/TECH-2026-001.md)") == "TECH-2026-001"

    def test_extract_linked_id_with_different_path(self):
        """Linked claim ID with any path is extracted."""
        assert extract_claim_id("[LABOR-2025-042](/some/other/path.md)") == "LABOR-2025-042"

    def test_extract_invalid_returns_none(self):
        """Invalid cell text returns None."""
        assert extract_claim_id("not a claim id") is None
        assert extract_claim_id("[broken link") is None
        assert extract_claim_id("") is None

    def test_extract_with_whitespace(self):
        """Whitespace around cell text is handled."""
        assert extract_claim_id("  TECH-2026-001  ") == "TECH-2026-001"
        assert extract_claim_id("  [TECH-2026-001](path)  ") == "TECH-2026-001"


class TestFrameworkRepoCheck:
    """Tests for framework repo detection."""

    def test_analysis_path_ok(self, tmp_path):
        """Analysis path in analysis/ dir is OK."""
        analysis_dir = tmp_path / "analysis" / "sources"
        analysis_dir.mkdir(parents=True)
        test_file = analysis_dir / "test.md"
        test_file.touch()

        warnings = check_framework_repo(test_file)
        assert len(warnings) == 0

    def test_scripts_path_warning(self, tmp_path):
        """Path in scripts/ without analysis/ produces warning."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        test_file = scripts_dir / "test.md"
        test_file.touch()

        warnings = check_framework_repo(test_file)
        assert len(warnings) >= 1
        assert any("framework repo" in w.lower() for w in warnings)


class TestFileValidation:
    """End-to-end file validation tests."""

    def test_valid_quick_analysis(self, tmp_path):
        """Valid quick analysis passes validation."""
        content = """# Source Analysis: Test Source

> **Claim types**: `[F]` fact, `[T]` theory, `[H]` hypothesis, `[P]` prediction, `[A]` assumption, `[C]` counterfactual, `[S]` speculation, `[X]` contradiction
> **Evidence**: **E1** systematic review/meta-analysis; **E2** peer-reviewed/official stats; **E3** expert consensus/preprint; **E4** credible journalism/industry; **E5** opinion/anecdote; **E6** unsupported/speculative

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-2026-source |
| **Analysis Depth** | quick |

## Summary

Test summary paragraph.

### Claim Summary

| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | E2 | 0.75 | Test claim |

### Claims to Register

```yaml
claims:
  - id: "TECH-2026-001"
    text: "Test claim"
    type: "[F]"
    domain: "TECH"
    evidence_level: "E2"
    credence: 0.75
    source_ids: ["test-2026-source"]
```
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = validate_file(test_file)

        assert result.profile == "quick"
        assert len(result.errors) == 0

    def test_incomplete_analysis_fails(self, tmp_path):
        """Incomplete analysis produces errors."""
        content = """# Source Analysis: Test Source

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | test-source |

## Summary

Test summary.
"""
        # Missing: legends, Claim Summary, Claims to Register, YAML block
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = validate_file(test_file)

        assert len(result.errors) >= 3

    def test_profile_override(self, tmp_path):
        """Profile can be overridden."""
        content = """# Source Analysis: Test
**Analysis Depth**: quick
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = validate_file(test_file, profile="full")

        # Should validate as full profile despite quick marker
        assert result.profile == "full"
        assert len(result.warnings) >= 1  # Profile mismatch warning

    def test_nonexistent_file(self, tmp_path):
        """Nonexistent file produces error."""
        test_file = tmp_path / "nonexistent.md"

        result = validate_file(test_file)

        assert result.profile == "unknown"
        assert len(result.errors) >= 1
        assert any("Could not read" in e for e in result.errors)


class TestRigorV1Tables:
    """Tests for rigor-v1 table validation (Layer/Actor/Scope/Quantifier columns)."""

    def test_key_claims_rigor_v1_header_detected(self):
        """Key Claims table with rigor-v1 columns is detected."""
        content = """### Key Claims

| # | Claim | Claim ID | Layer | Actor | Scope | Quantifier | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|-------|-------|-------|------------|------|--------|------|----------|-----------|----------------|
| 1 | Test claim | TECH-2026-001 | ASSERTED | ICE | who=citizens | some | [F] | TECH | E2 | 0.75 | ? | N/A |
"""
        # Import the rigor patterns (will be added)
        from analysis_validator import FULL_PROFILE_REQUIRED
        errors = validate_tables(content, FULL_PROFILE_REQUIRED["tables"])
        key_claims_errors = [e for e in errors if "Key Claims" in e]
        assert len(key_claims_errors) == 0

    def test_key_claims_legacy_header_still_accepted(self):
        """Legacy Key Claims table (without rigor columns) still passes basic validation."""
        content = """### Key Claims

| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | Test | TECH-2026-001 | [F] | TECH | E2 | 0.75 | ? | N/A |
"""
        from analysis_validator import FULL_PROFILE_REQUIRED
        errors = validate_tables(content, FULL_PROFILE_REQUIRED["tables"])
        key_claims_errors = [e for e in errors if "Key Claims" in e]
        assert len(key_claims_errors) == 0

    def test_claim_summary_rigor_v1_header_detected(self):
        """Claim Summary table with rigor-v1 columns is detected."""
        content = """### Claim Summary

| ID | Type | Domain | Layer | Actor | Scope | Quantifier | Evidence | Credence | Claim |
|----|------|--------|-------|-------|-------|------------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | LAWFUL | DHS | who=all | most | E2 | 0.75 | Test claim |
"""
        from analysis_validator import QUICK_PROFILE_REQUIRED
        errors = validate_tables(content, QUICK_PROFILE_REQUIRED["tables"])
        claim_summary_errors = [e for e in errors if "Claim Summary" in e]
        assert len(claim_summary_errors) == 0


class TestCorrectionsUpdatesSection:
    """Tests for Corrections & Updates section validation."""

    def test_corrections_section_present(self):
        """Corrections & Updates section is detected when present."""
        content = """## Stage 2: Evaluative Analysis

### Corrections & Updates

| Item | URL | Published | Corrected/Updated | What Changed | Impacted Claim IDs | Action Taken |
|------|-----|-----------|-------------------|--------------|--------------------|-------------|
| 1 | https://example.com | 2026-01-01 | N/A | N/A | N/A | N/A |
"""
        from analysis_validator import has_section
        assert has_section(content, "### Corrections & Updates")

    def test_corrections_section_missing_produces_warning(self, tmp_path):
        """Missing Corrections & Updates section produces a warning for full profile."""
        # This test validates the behavior that will be implemented
        content = """# Source Analysis: Test

> **Claim types**: `[F]` fact
> **Evidence**: **E1** test

## Metadata
## Stage 1: Descriptive Analysis
### Core Thesis
### Key Claims
| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | Test | TECH-2026-001 | [F] | TECH | E2 | 0.75 | ? | N/A |
### Argument Structure
### Theoretical Lineage
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
### Claim Summary
| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | E2 | 0.75 | Test |
### Claims to Register

```yaml
claims:
  - id: "TECH-2026-001"
```

**Credence in Analysis**: 0.7
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = validate_file(test_file, profile="full")
        # Should have a warning about missing Corrections & Updates section
        corrections_warnings = [w for w in result.warnings if "Corrections" in w]
        assert len(corrections_warnings) >= 1, "Expected warning about missing Corrections & Updates section"


class TestLayerEnumValidation:
    """Tests for Layer enum validation in claim tables."""

    def test_valid_layer_values_no_warning(self, tmp_path):
        """Valid Layer values (ASSERTED/LAWFUL/PRACTICED/EFFECT) produce no warnings."""
        content = """# Source Analysis: Test

> **Claim types**: `[F]` fact
> **Evidence**: **E1** test

## Metadata
**Analysis Depth**: quick

## Summary
Test.

### Claim Summary

| ID | Type | Domain | Layer | Actor | Scope | Quantifier | Evidence | Credence | Claim |
|----|------|--------|-------|-------|-------|------------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | ASSERTED | ICE | N/A | N/A | E2 | 0.75 | Test 1 |
| TECH-2026-002 | [F] | TECH | LAWFUL | COURT | N/A | N/A | E1 | 0.80 | Test 2 |
| TECH-2026-003 | [F] | TECH | PRACTICED | CBP | N/A | N/A | E3 | 0.60 | Test 3 |
| TECH-2026-004 | [H] | TECH | EFFECT | N/A | N/A | N/A | E4 | 0.50 | Test 4 |

### Claims to Register

```yaml
claims:
  - id: "TECH-2026-001"
```
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = validate_file(test_file, profile="quick")
        layer_warnings = [w for w in result.warnings if "Layer" in w]
        assert len(layer_warnings) == 0

    def test_invalid_layer_value_produces_warning(self, tmp_path):
        """Invalid Layer value produces a warning."""
        content = """# Source Analysis: Test

> **Claim types**: `[F]` fact
> **Evidence**: **E1** test

## Metadata
**Analysis Depth**: quick

## Summary
Test.

### Claim Summary

| ID | Type | Domain | Layer | Actor | Scope | Quantifier | Evidence | Credence | Claim |
|----|------|--------|-------|-------|-------|------------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | INVALID_LAYER | ICE | N/A | N/A | E2 | 0.75 | Test |

### Claims to Register

```yaml
claims:
  - id: "TECH-2026-001"
```
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = validate_file(test_file, profile="quick")
        # Quick profile doesn't run rigor checks, so test with full profile
        # Re-test with full profile to verify layer validation
        result_full = validate_file(test_file, profile="full")
        layer_warnings = [w for w in result_full.warnings if "Layer" in w or "INVALID_LAYER" in w]
        assert len(layer_warnings) >= 1, "Expected warning about invalid Layer value"


class TestRigorFlag:
    """Tests for --rigor flag behavior."""

    def test_rigor_flag_converts_warnings_to_errors(self, tmp_path):
        """With rigor=True, rigor warnings become errors."""
        # Content missing rigor-v1 columns and Corrections section
        content = """# Source Analysis: Test

> **Claim types**: `[F]` fact
> **Evidence**: **E1** test

## Metadata
**Analysis Depth**: full

## Stage 1: Descriptive Analysis
### Core Thesis
Test.
### Key Claims
| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | Test | TECH-2026-001 | [F] | TECH | E2 | 0.75 | ? | N/A |
### Argument Structure
### Theoretical Lineage
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
### Claim Summary
| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | E2 | 0.75 | Test |
### Claims to Register

```yaml
claims:
  - id: "TECH-2026-001"
```

**Credence in Analysis**: 0.7
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        # Without rigor flag: warnings
        result_warn = validate_file(test_file, profile="full", rigor=False)
        assert len(result_warn.warnings) > 0, "Should have rigor warnings"
        rigor_warnings = [w for w in result_warn.warnings if "rigor" in w.lower() or "Corrections" in w or "Layer" in w or "columns" in w.lower()]
        assert len(rigor_warnings) > 0, "Should have rigor-specific warnings"

        # With rigor flag: those warnings become errors
        result_error = validate_file(test_file, profile="full", rigor=True)
        # Rigor warnings should now be in errors
        rigor_errors = [e for e in result_error.errors if "rigor" in e.lower() or "Corrections" in e or "Layer" in e or "columns" in e.lower()]
        assert len(rigor_errors) > 0, "Rigor flag should convert warnings to errors"


class TestFullProfile:
    """Tests specific to full profile validation."""

    def test_full_profile_requires_stages(self, tmp_path):
        """Full profile requires Stage 1/2/3 sections."""
        content = """# Source Analysis: Test

> **Claim types**: `[F]` fact
> **Evidence**: **E1** test

## Metadata

Test metadata.
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = validate_file(test_file, profile="full")

        # Should be missing Stage sections
        stage_errors = [e for e in result.errors if "Stage" in e]
        assert len(stage_errors) >= 3  # Stage 1, 2, 3

    def test_full_profile_requires_credence(self, tmp_path):
        """Full profile requires Credence in Analysis."""
        content = """# Source Analysis: Test

> **Claim types**: `[F]` fact
> **Evidence**: **E1** test

## Metadata
## Stage 1: Descriptive Analysis
### Core Thesis
### Key Claims
| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | Test | TECH-2026-001 | [F] | TECH | E2 | 0.75 | ? | N/A |
### Argument Structure
### Theoretical Lineage
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
### Claim Summary
| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| TECH-2026-001 | [F] | TECH | E2 | 0.75 | Test |
### Claims to Register

```yaml
claims:
  - id: "TECH-2026-001"
```
"""
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = validate_file(test_file, profile="full")

        # Should be missing Credence in Analysis
        credence_errors = [e for e in result.errors if "Credence in Analysis" in e]
        assert len(credence_errors) >= 1
