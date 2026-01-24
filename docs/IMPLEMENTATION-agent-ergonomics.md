# Implementation: Agent Ergonomics (Upsert, Doctor, Repair, Actionable Errors)

**Status**: Implemented (pending commit)
**Plan**: [PLAN-agent-ergonomics.md](PLAN-agent-ergonomics.md)
**Started**: 2026-01-24

## Summary

Reduce operational friction for analysis agents by adding:

- conflict-safe import/upsert (`--on-conflict`)
- project/DB auto-detection + `doctor` command
- safe, idempotent `rc-db repair` to recompute invariants
- validation errors that include exact remediation commands

## Punchlist

### Phase 1: Tests (write FIRST per Spec→Plan→Test→Implement)

- [x] Add import conflict-policy tests (sources + claims) (`tests/test_db.py`)
- [x] Add repair command tests (backlinks + prediction stubs) (`tests/test_db.py`)
- [x] Add validate output “remediation command” tests (`tests/test_validate.py`)
- [x] Add doctor path detection tests (pure filesystem) (`tests/test_db.py`)
- [x] Add validate/export auto-detect tests (`tests/test_validate.py`, `tests/test_export.py`)

### Phase 2: `--on-conflict` for import and key adds

- [x] Add duplicate ID detection for `add_source()` (currently missing)
- [x] Implement conflict policy for sources during import: error|skip|update
- [x] Implement conflict policy for claims during import: error|skip|update
- [x] Wire `--on-conflict` into `rc-db import` CLI
- [ ] Decide and implement whether `rc-db source add` / `rc-db claim add` get `--on-conflict`
- [x] Update docs/examples for reruns and `--continue` workflows

### Phase 3: `rc-db repair` (safe/idempotent)

- [x] Implement `rc-db repair` CLI skeleton + help text
- [x] Implement backlinks recomputation (`sources.claims_extracted` from `claims.source_ids`)
- [x] Implement `[P]` prediction stub enforcement (status `[P?]`)
- [ ] Implement duplicate ID report mode (at least detect + report)
- [ ] Optional: dedupe-identical mode (report-first; conservative)

### Phase 4: Doctor + auto-detect DB path

- [x] Implement shared project path detection helper
- [x] Add `rc-db doctor` output with copy-paste fix commands
- [x] Improve “DB missing” errors across `rc-db`, `rc-validate`, `rc-export`

### Phase 5: Actionable validation errors

- [x] Add remediation command suggestions to validation findings output
- [x] Prefer suggesting `rc-db repair` when the fix is mechanical
- [x] Document common remediation patterns in `docs/WORKFLOWS.md`

### Phase 6: Documentation and integration sync

- [x] Update `docs/WORKFLOWS.md` with `--on-conflict`, `doctor`, `repair`
- [x] Update `docs/SCHEMA.md` invariants section (no schema changes expected)
- [ ] Update skills/templates only if command shapes change materially

## Worklog

### 2026-01-24: Planning docs created

- Added `docs/PLAN-agent-ergonomics.md`
- Added `docs/PLAN-ergonomics-todecide.md` (deferred decisions)
- Created this implementation punchlist/worklog

### 2026-01-24: Implemented core ergonomics

- Added `--on-conflict {error,skip,update}` to `rc-db import` (sources + claims)
- Added `rc-db doctor` (project/DB auto-detection) and auto-detection in `rc-db`, `rc-export`, `rc-validate`
- Added `rc-db repair` to recompute backlinks and ensure `[P]` prediction stubs
- Made `rc-validate` output include actionable remediation commands
