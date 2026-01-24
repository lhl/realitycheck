# Implementation: Agent Ergonomics (Upsert, Doctor, Repair, Actionable Errors)

**Status**: Not started
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

- [ ] Add import conflict-policy tests (sources + claims) (`tests/test_db.py`)
- [ ] Add repair command tests (backlinks + prediction stubs) (`tests/test_db.py`)
- [ ] Add validate output “remediation command” tests (`tests/test_validate.py`)
- [ ] (Optional) Add doctor path detection tests (pure filesystem) (`tests/test_*`)

### Phase 2: `--on-conflict` for import and key adds

- [ ] Add duplicate ID detection for `add_source()` (currently missing)
- [ ] Implement conflict policy for sources during import: error|skip|update
- [ ] Implement conflict policy for claims during import: error|skip|update
- [ ] Wire `--on-conflict` into `rc-db import` CLI
- [ ] Decide and implement whether `rc-db source add` / `rc-db claim add` get `--on-conflict`
- [ ] Update docs/examples for reruns and `--continue` workflows

### Phase 3: `rc-db repair` (safe/idempotent)

- [ ] Implement `rc-db repair` CLI skeleton + help text
- [ ] Implement backlinks recomputation (`sources.claims_extracted` from `claims.source_ids`)
- [ ] Implement `[P]` prediction stub enforcement (status `[P?]`)
- [ ] Implement duplicate ID report mode (at least detect + report)
- [ ] Optional: dedupe-identical mode (report-first; conservative)

### Phase 4: Doctor + auto-detect DB path

- [ ] Implement shared project path detection helper (module TBD)
- [ ] Add `rc-db doctor` output with copy-paste fix commands
- [ ] Improve “DB missing” errors across `rc-db`, `rc-validate`, `rc-export`

### Phase 5: Actionable validation errors

- [ ] Add remediation command suggestions to validation findings output
- [ ] Prefer suggesting `rc-db repair` when the fix is mechanical
- [ ] Document common remediation patterns in `docs/WORKFLOWS.md`

### Phase 6: Documentation and integration sync

- [ ] Update `docs/WORKFLOWS.md` with `--on-conflict`, `doctor`, `repair`
- [ ] Update `docs/SCHEMA.md` invariants section (no schema changes expected)
- [ ] Update skills/templates only if command shapes change materially

## Worklog

### 2026-01-24: Planning docs created

- Added `docs/PLAN-agent-ergonomics.md`
- Added `docs/PLAN-ergonomics-todecide.md` (deferred decisions)
- Created this implementation punchlist/worklog

