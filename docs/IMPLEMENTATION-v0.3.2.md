# Implementation: Verification Loop for Factual Claims (v0.3.2)

**Status**: Implemented (ready for reviewer pass)
**Plan**: [PLAN-v0.3.2.md](PLAN-v0.3.2.md)
**Started**: 2026-02-15
**Last Updated**: 2026-02-16

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
- `analysis_formatter.py` inserts the updated Stage 2 verification table contract (Claim ID + Search Notes + `ok/x/nf/blocked/?`).
- `analysis_validator.py` warns/errors (under `--rigor`) for:
  - `[REVIEWED]` with crux `Status = ?`
  - `[REVIEWED]` with crux `Status in {nf, blocked}` and missing Search Notes
  - high-credence factual claims not verified/refuted
- Targeted tests pass for new validator behavior.
- `make assemble-skills` and `make check-skills` pass cleanly.
- Manual regression on the Amodei/H200 case confirms v0.3.2 gates catch unresolved crux factual claims in legacy outputs.
- End-user upgrades reliably refresh Reality Check-managed integrations (skills/plugin) via auto-sync and manual sync command.
- New `rc-db backup` command creates timestamped `.tar.gz` snapshots of the LanceDB directory (tested).

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
 └── REGENERATED check-core.md                     # Generated from templates via `make assemble-skills` (do not edit directly)

scripts/
 ├── UPDATE analysis_formatter.py                  # Insert updated Stage 2 verification table contract
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

No open decisions remain for coder handoff. Resolved scope choices for v0.3.2:

- `WebSearch` change applies to Claude `check` only; `$analyze` parity is deferred to v0.3.3.
- Missing Search Notes warnings apply to unresolved **crux** rows only in v0.3.2.
- High-credence unresolved factual warning threshold is fixed at `credence >= 0.7`.

## Punchlist

### Phase 0: Spec Lock and Contracts

- [x] Confirm v0.3.2 contract in `PLAN-v0.3.2.md` is final for this run.
- [x] Confirm Stage 2 status codes: `ok`, `x`, `nf`, `blocked`, `?`.
- [x] Confirm final Stage 2 column order: `Claim ID | Claim (paraphrased) | Crux? | Source Says | Actual | External Source | Search Notes | Status`.
- [x] Confirm `[REVIEWED]` gate policy for crux unresolved claims.
- [x] Resolve Stage 2 table schema drift across methodology/templates vs `analysis_formatter.py` (pick one contract; update the other).
- [x] Record Phase 0 decisions in this file's Worklog and set status to `In Progress`.

### Phase 1: Tests First

#### 1.1 Validator tests (`tests/test_analysis_validator.py`)

- [x] Add test: `[REVIEWED]` + crux `Status=?` triggers WARN (ERROR with `--rigor`).
- [x] Add test: `[REVIEWED]` + Stage2 has **no** crux row (`Crux? = Y`) triggers WARN (ERROR with `--rigor`).
- [x] Add test: `[REVIEWED]` + crux `Status=nf` + missing Search Notes triggers WARN.
- [x] Add test: `[REVIEWED]` + crux `Status=nf` + Search Notes present passes.
- [x] Add test: `[REVIEWED]` + crux `Status=blocked` + missing Search Notes triggers WARN.
- [x] Add test: `[REVIEWED]` + crux `Status=blocked` + Search Notes present passes.
- [x] Add test: `[REVIEWED]` + crux `Status=ok` + missing External Source triggers WARN (ERROR with `--rigor`).
- [x] Add test: crux row missing Claim ID triggers WARN.
- [x] Add test: high-credence `[F]` unresolved triggers WARN.
- [x] Add test: low-credence unresolved factual claim does not trigger the high-credence warning.
- [x] Use realistic markdown table fixtures (header + separator + body), not simplified stubs, for Stage 2 parsing tests.

#### 1.2 Formatter/table-contract tests (`tests/test_analysis_formatter.py`)

- [x] Run after 1.1 fixtures are finalized (depends on locked column contract).
- [x] Add/adjust tests for updated factual verification table headers.
- [x] Confirm formatter behavior remains stable with Claim ID and Search Notes columns.
- [x] Update `scripts/analysis_formatter.py` section template for "Key Factual Claims Verified" to match the updated contract.

### Phase 2: Template and Workflow Updates

#### 2.1 Stage 2 table contract

- [x] Update `integrations/_templates/tables/factual-claims-verified.md.j2`:
  - set column order to `Claim ID | Claim (paraphrased) | Crux? | Source Says | Actual | External Source | Search Notes | Status`
  - include `Claim ID` column
  - include `Search Notes` column
  - document status semantics (`ok/x/nf/blocked/?`)

#### 2.2 Core workflow text

- [x] Update source templates that generate Stage 2 content (`integrations/_templates/skills/check.md.j2`, `integrations/_templates/tables/factual-claims-verified.md.j2`):
  - add DB-first step
  - add web discovery guidance (tool-agnostic)
  - add timebox guidance
  - align table column guide with template updates
- [x] Regenerate `methodology/workflows/check-core.md` via `make assemble-skills` (do not hand-edit generated file).

#### 2.3 Skill instructions

- [x] Update `integrations/_templates/skills/check.md.j2`:
  - add verification loop steps in execution workflow
  - use tool-agnostic language for search/discovery
  - include integration-specific examples where useful

### Phase 3: Integration Config

- [x] Update `integrations/_config/skills.yaml`:
  - add `WebSearch` to Claude `check` allowed tools
  - leave Claude `analyze` unchanged in v0.3.2 (deferred to v0.3.3)

### Phase 4: Validator Implementation

- [x] Update `scripts/analysis_validator.py` to parse updated Stage 2 table contract.
- [x] Keep backward compatibility: accept the legacy Stage 2 table shape, but WARN (ERROR with `--rigor`) when required columns for gating are missing.
- [x] Add reviewed gate for crux `Status=?`.
- [x] Add reviewed gate for crux unresolved (`nf/blocked`) without Search Notes.
- [x] Add high-credence unresolved factual warning.
- [x] Ensure `--rigor` escalation behavior matches existing patterns.

### Phase 5: Regenerate and Sync

- [x] Run `make assemble-skills`.
- [x] Run `make check-skills`.
- [x] Confirm generated skill docs reflect tool-agnostic verification instructions.

### Phase 6: Validation and Regression

- [x] Run targeted tests:
  - `uv run pytest tests/test_analysis_validator.py`
  - `uv run pytest tests/test_analysis_formatter.py`
- [x] Run broader test sweep as needed:
  - `uv run pytest`
- [x] Manual workflow regression:
  - Ran `uv run python scripts/analysis_validator.py /home/lhl/github/lhl/realitycheck-data/analysis/sources/aakashgupta-2026-amodei-hawkish-china-thread.md --profile full --rigor` and confirmed expected v0.3.2 gating failures on legacy Stage 2 shape (missing `Claim ID`/`Search Notes`) and unresolved high-credence factual claim.

### Phase 7: Documentation and Wrap-Up

- [x] Update `docs/TODO.md` with v0.3.2 status and link to this implementation file.
- [x] If shipping v0.3.2, follow `docs/DEPLOY.md` (update `docs/CHANGELOG.md`, bump `pyproject.toml`, run `make release-metadata`). *(N/A in this implementation pass; no release cut.)*
- [x] Final pass: ensure claim-integrity evidence is recorded (tests + runtime behavior + docs parity).

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

### 2026-02-15: v0.3.2 implemented end-to-end

- Phase 0 decisions locked and applied:
  - Stage 2 status codes: `ok | x | nf | blocked | ?`
  - Final Stage 2 column order: `Claim ID | Claim (paraphrased) | Crux? | Source Says | Actual | External Source | Search Notes | Status`
  - `check-core.md` treated as **REGENERATED** from templates only
  - Scope decision: add `WebSearch` to Claude `$check`; defer `$analyze` parity to v0.3.3
- Implemented and aligned schema contract across:
  - templates (`integrations/_templates/skills/check.md.j2`, `integrations/_templates/tables/factual-claims-verified.md.j2`)
  - formatter (`scripts/analysis_formatter.py`)
  - validator (`scripts/analysis_validator.py`)
  - tests (`tests/test_analysis_formatter.py`, `tests/test_analysis_validator.py`)
  - generated outputs (`integrations/*/skills/*check*/SKILL.md`, `methodology/workflows/check-core.md`)
- Validation evidence:
  - `make assemble-skills` → `Generated: 33 files, 0 changed`
  - `make check-skills` → `Generated: 33 files, 0 changed`
  - `uv run pytest tests/test_analysis_formatter.py tests/test_analysis_validator.py` → `99 passed`
  - `uv run pytest` → `423 passed, 2 warnings` (existing `datetime.utcnow()` deprecation warnings in `scripts/db.py`)
- Manual regression evidence (Amodei/H200 case):
  - `uv run python scripts/analysis_validator.py /home/lhl/github/lhl/realitycheck-data/analysis/sources/aakashgupta-2026-amodei-hawkish-china-thread.md --profile full --rigor`
  - Result intentionally fails legacy analysis with v0.3.2 gates (`Claim ID`/`Search Notes` missing and high-credence unresolved factual warning), confirming the new contract is actively enforced.

### 2026-02-16: post-review hardening + end-user upgrade sync

- Addressed reviewer hardening gaps in `scripts/analysis_validator.py` and tests:
  - normalized factual claim type handling (`F`, `[F]`, markdown-wrapped variants) for high-credence unresolved warning
  - fail-closed behavior for unknown/blank reviewed crux `Status` values (with explicit warning)
  - claim ID extraction now tolerates simple markdown wrappers
  - narrowed `[REVIEWED]` detection to metadata rigor-level field
- Added end-user integration update path for pre-release v0.3.2:
  - new `scripts/integration_sync.py` module for safe, best-effort sync of Reality Check-managed skill/plugin symlinks
  - auto-sync hook on first `rc-*` run after version change (configurable via `REALITYCHECK_AUTO_SYNC=0`)
  - manual command: `rc-db integrations sync [--install-missing|--all|--dry-run]`
  - packaging updated so wheel installs include integration assets (`integrations/**`, `methodology/workflows/check-core.md`, `README.md`)
- Documentation updates:
  - README section: "Keeping Integrations Updated"
  - changelog notes added under Unreleased/v0.3.2 scope
- Validation evidence for this follow-up:
  - `uv run pytest tests/test_integration_sync.py tests/test_db.py::TestIntegrationsCLI tests/test_installation.py` → `30 passed`
  - `uv run pytest` → `435 passed, 2 warnings` (existing `datetime.utcnow()` deprecation warning path)
  - `uv build --wheel` and wheel inspection confirm integration assets are included.

### 2026-02-16: parser hardening + explicit backups

- Hardened formatter/validator markdown table parsing to reduce false negatives and fail-open states:
  - tolerate simple markdown wrappers in headers/cells (e.g. `**Claim ID**`, ``Type``)
  - handle escaped pipes (`\\|`) in markdown tables without breaking column alignment
  - formatter: robust detection of existing Key Claims + Claim Summary tables to prevent duplicate insertion
  - validator: robust detection of Key Claims table for high-credence factual verification warnings
- Tightened integration sync safety semantics:
  - default sync updates existing Reality Check-managed symlinks only (no new installs)
  - `--install-missing` installs missing skills/plugins only when the integration is already present
  - managed-symlink detection uses path parts (avoids substring false positives)
- Added explicit backup workflow for safety:
  - new CLI: `rc-db backup [--output-dir DIR] [--prefix NAME] [--dry-run]`
  - `create_db_backup_archive()` creates a timestamped `.tar.gz` snapshot of the LanceDB directory
- Cleanup: analysis-log `created_at` now uses timezone-aware UTC (removes `datetime.utcnow()` deprecation warnings).
- Validation evidence:
  - `uv run pytest tests/test_analysis_formatter.py tests/test_analysis_validator.py -q` → `110 passed`
  - `uv run pytest tests/test_db.py::TestBackupCLI -q` → `1 passed`
  - `uv run pytest -q` → `449 passed`
