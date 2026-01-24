# Plan: Agent Ergonomics (Upsert, Doctor, Repair, Actionable Errors)

**Status**: Planning
**Created**: 2026-01-24

## Motivation

Reality Check is increasingly used by analysis agents in iterative, restartable workflows. In first real use, the biggest remaining friction points were:

- reruns of `rc-db import ... --type all` require manual deletes when IDs already exist
- agents must think about `REALITYCHECK_DATA` / correct working directory
- validation failures do not provide actionable remediation commands
- existing DBs can drift from invariants (e.g., source↔claim backlinks, `[P]` prediction stubs)

This plan reduces “muss/fuss” while preserving safety and reproducibility.

## Goals

- **Idempotent reruns**: make it safe/easy to re-run import and registration steps.
- **Low-friction setup**: minimize user/agent time spent debugging DB path configuration.
- **Actionable failures**: errors should include *the exact command* to fix or repair.
- **Repairability**: provide a safe, idempotent `rc-db repair` to recompute invariants.

## Non-goals (in this plan)

- “One-shot finish/publish” command (deferred to `PLAN-ergonomics-todecide.md`).
- `rc-analysis new` skeleton generator (deferred to `PLAN-ergonomics-todecide.md`).
- Any schema redesign (no new tables required).
- Storing prompts/transcripts (audit log remains usage-only).

## Requirements

### 1) `--on-conflict` upsert behavior for import (and key adds)

Add `--on-conflict {error,skip,update}` to places agents re-run:

- `rc-db import <file> --type {claims,sources,all} --on-conflict ...`
- (Optional but likely) `rc-db source add ... --on-conflict ...`
- (Optional but likely) `rc-db claim add ... --on-conflict ...`

Semantics:

- `error` (default): fail fast when an ID already exists.
- `skip`: do nothing for existing IDs; continue.
- `update`: update the existing record with the incoming fields.

Constraints:

- Preserve current behaviors where possible (e.g., `update_claim()` increments `version` and updates `last_updated`).
- Import must report counts: created / updated / skipped / failed.

### 2) Project “doctor” / DB auto-detection

Reduce dependence on `REALITYCHECK_DATA` by auto-detecting a data project root and DB path:

- Walk upward from CWD looking for:
  - `.realitycheck.yaml` (future configuration point), OR
  - `data/realitycheck.lance` (default DB location), OR
  - a repo root marker (optional; e.g., `.git`) + `data/realitycheck.lance`

Provide an explicit doctor command (proposed):

- `rc-db doctor` (prints detected root + DB path + “here’s the fix” commands)

Also improve “DB not found” errors in `rc-db`, `rc-validate`, and `rc-export` to:

- show detected candidate project roots (if any)
- print one copy-paste command to set `REALITYCHECK_DATA`

### 3) `rc-db repair` (safe, idempotent)

Add `rc-db repair` to recompute invariants on an existing DB:

Default repairs (safe/idempotent):

- **Backlinks**: recompute `sources.claims_extracted` from `claims.source_ids`.
- **Prediction stubs**: for `[P]` claims with a `source_id`, ensure a prediction row exists (status `[P?]`).

Optional/report-only behaviors:

- **Duplicate ID detection**: report duplicate IDs per table.
- (Optional) **Obvious dedupe**: if duplicates are byte-identical, keep one and delete the rest; otherwise report for manual resolution.

CLI shape (proposed):

- `rc-db repair` (runs default repairs)
- `rc-db repair --backlinks --predictions` (explicit selection)
- `rc-db repair --report-duplicates [--dedupe-identical]`
- `rc-db repair --dry-run` (print planned changes)

### 4) More actionable validation/CLI errors

When validation fails, print the most direct remediation command:

- Missing source referenced by claim → suggest `rc-db source add ...` (stub) or `rc-db import ... --type sources`.
- Missing prediction for `[P]` claim → suggest `rc-db repair --predictions` or `rc-db prediction add ...`.
- Missing backlinks → suggest `rc-db repair --backlinks`.

Prefer suggesting `rc-db repair` when the fix is mechanical and safe.

## Proposed Implementation (High Level)

### A) Centralize project path detection

Create a small shared helper (module name TBD) used by:

- `scripts/db.py`
- `scripts/validate.py`
- `scripts/export.py`

Responsibilities:

- find project root
- infer default DB path
- format “actionable fix” messages

### B) Add conflict policy plumbing

Implement conflict detection for `sources` and `claims`:

- **Sources**: currently `add_source()` does not check for duplicate IDs → must add duplicate check for safety.
- **Claims**: already checked for duplicate IDs and raises; extend call sites to handle `skip/update`.

### C) Implement `rc-db repair`

Use existing CRUD helpers where possible:

- backlinks can reuse the same update logic used by claim CRUD (but computed in batch)
- prediction stub creation can reuse `_ensure_prediction_for_claim()`

### D) Actionable errors

Extend `scripts/validate.py` output formatting to include a suggested command per finding.

## Tests (Must Be Written First)

- `tests/test_db.py`
  - Import `--on-conflict` behaviors for sources/claims (`error|skip|update`)
  - Repair behavior fixes missing backlinks and missing prediction stubs
  - Duplicate ID detection report mode (minimal)
- `tests/test_validate.py`
  - Validation failure output includes remediation command(s)
- (Optional) New unit tests for doctor path detection (pure filesystem tests; no DB required)

## Documentation Updates

- `docs/WORKFLOWS.md`: add `--on-conflict` examples, `rc-db doctor`, and `rc-db repair`
- `docs/SCHEMA.md`: no schema change expected; document invariants and repair semantics
- Skills/templates: update only if command shapes change materially

## Risks / Design Notes

- **Update semantics**: `update_claim()` increments `version`; import “update” should be explicit about this.
- **Duplicates**: LanceDB does not enforce uniqueness; repair/dedupe must be conservative and report-first.
- **Auto-detection surprises**: doctor should be explicit about what it inferred; avoid silently writing to unexpected DBs.

