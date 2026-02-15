# Implementation: Verification Loop for Factual Claims (v0.3.2)

**Status**: Planned (ready for execution)
**Plan**: [PLAN-v0.3.2.md](PLAN-v0.3.2.md)
**Started**: 2026-02-15
**Last Updated**: 2026-02-15

## Summary

Implement a concrete, tool-agnostic verification loop so `$check` does not stop at "flag for follow-up" on crux factual claims.

Primary outcomes for v0.3.2:

- Add web discovery capability and instructions for factual verification.
- Add an explicit Stage 2 verification procedure (DB-first, then web search, timeboxed).
- Update Stage 2 factual verification table contract (Claim ID + Search Notes + explicit unresolved statuses).
- Add validator checks that block `[REVIEWED]` when crux factual claims are unattempted.
- Add validator warnings for high-credence factual claims that are not verified/refuted.

## Pre-Analysis Note (2026-02-15)

**Scope**:
- Methodology, template, skill config, and validator changes for v0.3.2.
- No DB schema changes.

**Main risks**:
- Drift between templates and validator expectations.
- Overly strict validator gates that block normal draft workflows.
- Integration mismatch (Claude tool gating vs Codex/Amp/OpenCode tool availability).

**Validation plan**:
- Tests first for `analysis_validator.py` and formatter/table-contract side effects.
- Regenerate skills and verify generated skill docs pass checks.
- Re-run targeted regression on the Amodei/H200 case after implementation.

## Acceptance Criteria (Definition of Done)

- `$check` instructions explicitly require verification attempts for crux factual claims.
- Claude `check` allows `WebSearch`; other integrations use tool-agnostic wording.
- Stage 2 "Key Factual Claims Verified" table contract includes Claim ID and Search Notes.
- `analysis_validator.py` warns/errors (under `--rigor`) for:
  - `[REVIEWED]` with crux `Status = ?`
  - `[REVIEWED]` with crux `Status in {nf, blocked}` and missing Search Notes
  - high-credence factual claims not verified/refuted
- Targeted tests pass for new validator behavior.
- `make assemble-skills` and `make check-skills` pass cleanly.
- Manual regression confirms Davos/H200-style claims are verified in first pass workflow when evidence is available.

## Affected Files (Expected)

```
docs/
 ├── NEW IMPLEMENTATION-v0.3.2.md                  # This file
 ├── UPDATE PLAN-v0.3.2.md                         # Spec updates (already in progress)
 └── UPDATE TODO.md                                # Link and status tracking (optional in this pass)

integrations/_config/
 └── UPDATE skills.yaml                            # Claude: add WebSearch to check (and optionally analyze)

integrations/_templates/
 ├── UPDATE skills/check.md.j2                     # Tool-agnostic verification loop instructions
 └── UPDATE tables/factual-claims-verified.md.j2   # Claim ID + Search Notes + status guide

methodology/workflows/
 └── UPDATE check-core.md                          # Stage 2 verification procedure + updated table contract

scripts/
 └── UPDATE analysis_validator.py                  # Crux reviewed gate + high-credence unresolved warning

tests/
 ├── UPDATE test_analysis_validator.py             # New gate/warning behavior
 └── UPDATE test_analysis_formatter.py             # If table contract changes affect formatter assumptions

integrations/claude/skills/
integrations/codex/skills/
integrations/amp/skills/
integrations/opencode/skills/
 └── REGENERATED SKILL.md files via `make assemble-skills`
```

## Open Decisions

No blocker-level open decisions remain, but track these toggles during implementation:

- Whether to add `WebSearch` to Claude `analyze` in v0.3.2 or defer.
- Whether missing Search Notes for unresolved non-crux rows should warn now or later.
- Exact high-credence threshold (`>= 0.7` currently planned).

## Punchlist

### Phase 0: Spec Lock and Contracts

- [ ] Confirm v0.3.2 contract in `PLAN-v0.3.2.md` is final for this run.
- [ ] Confirm Stage 2 status codes: `ok`, `x`, `nf`, `blocked`, `?`.
- [ ] Confirm `[REVIEWED]` gate policy for crux unresolved claims.
- [ ] Confirm whether Claude `analyze` also gets `WebSearch` now.

### Phase 1: Tests First

#### 1.1 Validator tests (`tests/test_analysis_validator.py`)

- [ ] Add test: `[REVIEWED]` + crux `Status=?` triggers WARN (ERROR with `--rigor`).
- [ ] Add test: `[REVIEWED]` + crux `Status=nf` + missing Search Notes triggers WARN.
- [ ] Add test: `[REVIEWED]` + crux `Status=nf` + Search Notes present passes.
- [ ] Add test: crux row missing Claim ID triggers WARN.
- [ ] Add test: high-credence `[F]` unresolved triggers WARN.
- [ ] Add test: low-credence unresolved factual claim does not trigger the high-credence warning.

#### 1.2 Formatter/table-contract tests (`tests/test_analysis_formatter.py`)

- [ ] Add/adjust tests for updated factual verification table headers.
- [ ] Confirm formatter behavior remains stable with Claim ID and Search Notes columns.

### Phase 2: Template and Workflow Updates

#### 2.1 Stage 2 table contract

- [ ] Update `integrations/_templates/tables/factual-claims-verified.md.j2`:
  - include `Claim ID` column
  - include `Search Notes` column
  - document status semantics (`ok/x/nf/blocked/?`)

#### 2.2 Core workflow text

- [ ] Update `methodology/workflows/check-core.md` Stage 2:
  - add DB-first step
  - add web discovery guidance (tool-agnostic)
  - add timebox guidance
  - align table column guide with template updates

#### 2.3 Skill instructions

- [ ] Update `integrations/_templates/skills/check.md.j2`:
  - add verification loop steps in execution workflow
  - use tool-agnostic language for search/discovery
  - include integration-specific examples where useful

### Phase 3: Integration Config

- [ ] Update `integrations/_config/skills.yaml`:
  - add `WebSearch` to Claude `check` allowed tools
  - decide and apply `analyze` change (if in-scope)

### Phase 4: Validator Implementation

- [ ] Update `scripts/analysis_validator.py` to parse updated Stage 2 table contract.
- [ ] Add reviewed gate for crux `Status=?`.
- [ ] Add reviewed gate for crux unresolved (`nf/blocked`) without Search Notes.
- [ ] Add high-credence unresolved factual warning.
- [ ] Ensure `--rigor` escalation behavior matches existing patterns.

### Phase 5: Regenerate and Sync

- [ ] Run `make assemble-skills`.
- [ ] Run `make check-skills`.
- [ ] Confirm generated skill docs reflect tool-agnostic verification instructions.

### Phase 6: Validation and Regression

- [ ] Run targeted tests:
  - `uv run pytest tests/test_analysis_validator.py`
  - `uv run pytest tests/test_analysis_formatter.py`
- [ ] Run broader test sweep as needed:
  - `uv run pytest`
- [ ] Manual workflow regression:
  - Re-run `$check` style analysis on Amodei/H200 case and confirm first-pass verification behavior.

### Phase 7: Documentation and Wrap-Up

- [ ] Update `docs/TODO.md` with v0.3.2 status and link to this implementation file.
- [ ] Add final release notes sync if v0.3.2 ships in this cycle.
- [ ] Final pass: ensure claim-integrity evidence is recorded (tests + runtime behavior + docs parity).

## Worklog

### 2026-02-15: Implementation tracker created

- Created `docs/IMPLEMENTATION-v0.3.2.md` with:
  - full execution punchlist by phase
  - explicit acceptance criteria
  - pre-analysis note (scope, risks, validation plan)
  - test-first and regression steps for one-pass implementation
- Synchronized this tracker with `docs/PLAN-v0.3.2.md` direction:
  - tool-agnostic web discovery requirement
  - Stage 2 Claim ID/Search Notes contract
  - `[REVIEWED]` crux gate and high-credence unresolved warning behavior

