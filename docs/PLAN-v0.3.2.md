# Plan: Verification Loop for Factual Claims (v0.3.2)

**Status**: Spec Draft
**Created**: 2026-02-15
**Version**: 0.3.2 (point release: methodology/template/config changes + small validator addition)

## Motivation

Reality Check's `$check` workflow successfully parses and enumerates claims, assigns evidence levels and credence, and flags unverified items for follow-up. However, it **does not actively chase down or verify factual claims**. The workflow tells agents *what* to verify but doesn't give procedural steps or tool access for *how*.

This gap was identified during review of `aakashgupta-2026-amodei-hawkish-china-thread.md` (produced by Codex/gpt-5.2, committed in realitycheck-data `3ee7019`). The analysis correctly:
- Typed a Davos/H200 export claim as `[F]` (fact),
- Rated it `E6` (unsupported),
- Marked it `?` (unverified),
- Flagged it for follow-up in the "Claims to Cross-Reference" section.

But no follow-up occurred within the workflow. The claim was eventually verified in a manual second pass using a BIS press release and TechCrunch reporting -- both easily discoverable via web search. The analysis reached `[REVIEWED]` status with a crux factual claim still unverified.

This is exactly the kind of failure Reality Check exists to prevent: confident-looking outputs with unresolved epistemic gaps.

## Problem Statement

Four root causes contribute to this verification gap:

### 1. `WebSearch` is not in the allowed tools for `$check`

The Claude Code `check` skill's `allowed_tools` list (`integrations/_config/skills.yaml:37-46`) includes `WebFetch` (for fetching a provided URL) but **not `WebSearch`** (for discovering URLs). This means the agent can read a page it's given but cannot search the web to find corroborating or disconfirming evidence.

Codex skills don't have an `allowed_tools` mechanism, but the Codex `$check` skill likewise lacks explicit instructions to use web search for verification.

### 2. No explicit verification loop in the workflow

The methodology's Stage 2 ("Key Factual Claims Verified" table) defines the *output shape* -- columns for Source Says, Actual, External Source, Status -- but provides no procedural instructions for how to populate the "Actual" and "External Source" columns. Agents are expected to verify facts but given no tool guidance, search strategy, or decision procedure for when/how to search.

### 3. `[F]` + `E6` + `?` is a semantic inconsistency the validator doesn't catch

A claim typed as `[F]` (fact -- "checkable, verifiable proposition") with evidence level `E6` (unsupported/speculative) and verification status `?` (unverified) is internally inconsistent: if it's a fact, it should be checkable; if it's checkable and we didn't check it, we shouldn't rate the analysis as reviewed. The current `analysis_validator.py` does not flag this combination.

### 4. Single-pass analysis has no gate preventing `[REVIEWED]` with unverified crux claims

The workflow allows an analysis to reach `[REVIEWED]` status even when crux factual claims (marked `Crux? = Y`) remain unverified (`? status`). There is no validation gate requiring crux facts to be resolved before the analysis is considered reviewed.

## Goals

1. **Enable web search for fact verification**: Add `WebSearch` to the `$check` skill's allowed tools so agents can discover corroborating/disconfirming evidence.
2. **Add a procedural verification loop**: Give agents explicit instructions for when and how to search for evidence on `[F]`-typed claims during Stage 2.
3. **Catch semantic inconsistencies**: Add a validator warning for `[F]` + `E6` + `?` and similar incoherent combinations.
4. **Gate `[REVIEWED]` status**: Prevent analyses from reaching `[REVIEWED]` when crux factual claims remain unverified.

## Non-goals

- Full automated fact-checking pipeline (out of scope; this is about giving agents the tools and instructions to verify within the existing workflow).
- Changes to the DB schema or LanceDB tables (this is a methodology/template/config change).
- Rearchitecting the multi-pass workflow (covered by `PLAN-analysis-rigor-improvement.md`).
- Adding `WebSearch` to all skills (only `check` and potentially `fetch` need it).

## Affected Files

```
realitycheck/
 ├── integrations/
 │    └── _config/
 │         └── UPDATE skills.yaml                    # Add WebSearch to check skill allowed_tools
 ├── integrations/
 │    └── _templates/
 │         └── skills/
 │              └── UPDATE check.md.j2               # Add verification loop instructions
 ├── methodology/
 │    └── workflows/
 │         └── UPDATE check-core.md                  # Add verification procedure to Stage 2
 ├── scripts/
 │    └── UPDATE analysis_validator.py               # Add F+E6+? warning; add crux-unverified gate
 └── docs/
      ├── NEW PLAN-v0.3.2.md                         # This document
      └── UPDATE TODO.md                             # Add this item to roadmap
```

## Implementation

### Change 1: Add `WebSearch` to `check` skill allowed tools

**File**: `integrations/_config/skills.yaml`

Add `"WebSearch"` to the `check` skill's Claude `allowed_tools` list:

```yaml
    claude:
      argument_hint: "<url> [--domain DOMAIN] [--quick] [--no-register] [--continue]"
      allowed_tools:
        - "WebFetch"
        - "WebSearch"          # NEW: enable fact verification via web search
        - "Read"
        - "Write"
        - "Bash(uv run python scripts/db.py *)"
        # ... rest unchanged
```

Also consider adding `WebSearch` to the `fetch` skill if URL discovery during source fetching is useful.

**Rationale**: `WebFetch` lets agents read a known URL; `WebSearch` lets them discover URLs. Verification requires discovery ("find reporting on Amodei's Davos remarks") not just retrieval.

### Change 2: Add verification loop to Stage 2 methodology

**Files**: `methodology/workflows/check-core.md`, `integrations/_templates/skills/check.md.j2`

Add an explicit verification procedure to Stage 2 between claim extraction and the "Key Factual Claims Verified" table. The procedure should:

1. **Identify verification targets**: All claims typed `[F]` (fact) with `Crux? = Y`, plus any `[F]` claims with `E5` or `E6` evidence levels.
2. **Search strategy**: For each target, perform a web search using specific, neutral search terms (not the claim's framing). Try at least 2 distinct queries.
3. **Record results**: For each search, record what was found (or "no results") in the "Key Factual Claims Verified" table, including the source URL and whether it confirms, contradicts, or is ambiguous.
4. **Update evidence levels**: If verification succeeds, update the claim's evidence level (e.g., E6 -> E4 if credible journalism found, E6 -> E2 if official document found). If verification fails after reasonable search, explicitly record "searched but not found" rather than leaving `?`.
5. **Decision gate**: If a crux `[F]` claim cannot be verified after searching, downgrade it to `[H]` (hypothesis) or explicitly mark the analysis as incomplete.

Example template addition:

```markdown
### Verification Procedure (Stage 2)

For each `[F]`-typed claim, especially crux claims:

1. **Search**: Use WebSearch with neutral terms to find primary or secondary sources.
   - Try the specific factual assertion (e.g., "Amodei Davos H200 exports China")
   - Try the broader context (e.g., "Davos 2026 AI chip exports")
2. **Evaluate**: Check discovered sources against the claim.
   - Does the source confirm the claim? Record URL + relevant excerpt.
   - Does the source contradict or modify the claim? Record and adjust.
   - No relevant sources found? Record "searched, not found" with queries tried.
3. **Update**: Adjust evidence level and credence based on what was found.
4. **Gate**: Do not mark analysis as [REVIEWED] if crux [F] claims remain `?`.
```

### Change 3: Add semantic consistency check to validator

**File**: `scripts/analysis_validator.py`

Add a validation warning for semantically inconsistent claim metadata combinations:

| Combination | Severity | Message |
|-------------|----------|---------|
| `[F]` + `E6` + `?` | WARN | "Fact claim {id} has unsupported evidence (E6) and is unverified -- verify or retype as [H]" |
| `[F]` + `E5` + `?` | WARN | "Fact claim {id} has opinion-level evidence (E5) and is unverified -- verify or retype as [H]" |
| `Crux? = Y` + `?` + `[REVIEWED]` | WARN (ERROR with `--rigor`) | "Analysis marked [REVIEWED] but crux claim {id} is unverified" |

This aligns with the existing validator pattern: WARN by default, ERROR with `--rigor`.

### Change 4: Add `[REVIEWED]` gate for crux claims

**File**: `scripts/analysis_validator.py`

Add a validation check that prevents `[REVIEWED]` status when crux factual claims remain unverified:

- Parse the "Key Factual Claims Verified" table.
- For any row where `Crux? = Y` and `Status = ?`, emit a warning (or error with `--rigor`).
- The analysis should not be considered fully reviewed until all crux facts are either verified, refuted, or explicitly marked as unverifiable with documented search attempts.

## Relationship to Other Plans

- **PLAN-analysis-rigor-improvement.md**: That plan addresses structural rigor (layer/actor/scope, primary capture, corrections tracking). This plan addresses *procedural* rigor (actually performing verification within the workflow). They are complementary and independent.
- **PLAN-epistemic-provenance.md**: Provenance tracks *why* credence was assigned; this plan ensures the verification step that informs credence actually happens.
- **PLAN-quality-regression-fix.md**: That plan restored missing templates; this plan adds a missing *procedural step* to the existing templates.

## Tests and Verification Strategy

### Validator tests (`tests/test_analysis_validator.py`)

1. **Semantic consistency check**:
   - Test that `[F]` + `E6` + `?` triggers a WARN.
   - Test that `[F]` + `E4` + `ok` does NOT trigger a warning (consistent).
   - Test that `[H]` + `E6` + `?` does NOT trigger a warning (hypotheses can be unsupported).

2. **Crux-unverified gate**:
   - Test that `Crux? = Y` + `Status = ?` with `[REVIEWED]` triggers a WARN.
   - Test that `Crux? = Y` + `Status = ?` without `[REVIEWED]` does NOT trigger (analysis still in progress).
   - Test that `Crux? = Y` + `Status = ok` with `[REVIEWED]` passes cleanly.
   - Test that `Crux? = N` + `Status = ?` with `[REVIEWED]` does NOT trigger (non-crux unverified is acceptable).

3. **`--rigor` escalation**:
   - Test that the above WARNs become ERRORs when `--rigor` flag is set.

### Manual verification

- Re-run `$check` on a source with verifiable factual claims and confirm that:
  - The agent uses `WebSearch` to look up facts.
  - The "Key Factual Claims Verified" table is populated with actual external sources.
  - `[F]` claims that cannot be verified are either retyped or explicitly documented as unverifiable.
  - The analysis does not reach `[REVIEWED]` with unverified crux claims.

### Regression test

- Re-analyze `aakashgupta-2026-amodei-hawkish-china-thread` with the updated workflow and confirm that the Davos/H200 claim (GEO-2026-033) is verified in the first pass rather than requiring manual follow-up. (Note: the original analysis from `3ee7019` is being reworked with a fact-checking focus as of 2026-02-15.)

## Release Notes (v0.3.2)

### Added
- `WebSearch` tool enabled for `$check` skill, allowing agents to discover corroborating/disconfirming evidence during fact verification.
- Explicit verification loop procedure in Stage 2 methodology for `[F]`-typed claims.
- Validator warning for semantically inconsistent claim metadata (`[F]` + `E6` + `?` and similar).
- Validator gate preventing `[REVIEWED]` status when crux factual claims remain unverified.

### Changed
- `check` skill allowed tools list now includes `WebSearch`.
- Stage 2 methodology includes procedural verification instructions alongside existing output templates.

### Fixed
- Analyses could reach `[REVIEWED]` status with crux factual claims still marked as unverified.
