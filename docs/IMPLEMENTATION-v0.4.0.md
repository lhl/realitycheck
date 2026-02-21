# Implementation: Analysis Linking + Backfill Tooling (v0.4.0)

**Status**: Planned (spec + plan ready for review)
**Plan**: [PLAN-v0.4.0.md](PLAN-v0.4.0.md)
**Started**: 2026-02-21
**Last Updated**: 2026-02-21

## Summary

Implement a low-overhead linking system for Reality Check data repositories so GitHub navigation becomes “click-through” across:

- syntheses → per-source analyses
- analyses → internal captures (when present)
- claim IDs → reasoning docs (when present)

Primary outcomes intended for v0.4.0:

- New `rc-link scan|apply` helper (safe + idempotent).
- Template improvements so new syntheses/analyses include link-friendly sections/fields by default.
- Optional export rendering improvements for evidence locations that include artifact pointers.

## Pre-Analysis Note (2026-02-21)

**Scope**:

- Framework-side tooling and template updates only.
- No DB schema changes.
- No network capture tooling (link what exists; don’t fetch).

**Main risks**:

- Over-aggressive markdown rewriting (linker must be minimal-diff and conservative).
- Heterogeneous legacy markdown shapes (syntheses and analyses vary).
- Incorrect relative path computation breaking GitHub browsing.

**Validation plan**:

- Tests-first for `rc-link` behaviors (fixtures simulating a data repo).
- Idempotency tests (apply twice → second run no diff).
- Run `make assemble-skills` to ensure template changes propagate cleanly.

## Acceptance Criteria (Definition of Done)

- `rc-link scan` reports missing-link opportunities without modifying files.
- `rc-link apply` performs conservative, idempotent edits:
  - adds `## Source Analyses` links to syntheses when source IDs and targets are unambiguous
  - upgrades existing `reference/...` path mentions to markdown links **only when the target exists**
  - (optional flag) links claim IDs to `analysis/reasoning/<claim-id>.md` when present
- Template updates land:
  - synthesis template includes a canonical `## Source Analyses` section in its minimal snippet
  - source analysis templates include optional metadata slots for internal captures/transcripts (blank by default)
- Targeted tests pass:
  - new linker tests
  - existing suite remains green (no unintended regressions)
- Documentation parity:
  - `docs/ANALYSIS-linking.md` reflects the final v0.4.0 contract and commands.
  - Plan and implementation docs updated with final decisions.

## Affected Files (Expected)

```
docs/
  UPDATE ANALYSIS-linking.md
  NEW    PLAN-v0.4.0.md
  NEW    IMPLEMENTATION-v0.4.0.md

scripts/
  NEW    link.py (or linker.py)

tests/
  NEW    test_link.py (or test_linker.py)

integrations/_templates/
  UPDATE skills/synthesize.md.j2
  UPDATE analysis/source-analysis-full.md.j2
  UPDATE analysis/source-analysis-quick.md.j2

scripts/export.py (optional stretch)
  UPDATE evidence export rendering
```

## Open Decisions

- **Link style** inside syntheses:
  - Option A: section-relative (`../sources/<id>.md`) (preferred for “within analysis/” navigation)
  - Option B: repo-relative (`analysis/sources/<id>.md`) (preferred for “paste into README-style indexes”)
- **Artifact discovery**:
  - v0.4.0 baseline: link targets that are already referenced in-doc + synthesis→analysis links
  - stretch: heuristic discovery of likely captures for a given source-id (must be conservative / report ambiguities)
- **Validator posture**:
  - likely: no gating; optional WARN-only checks later if needed

## Punchlist

### Phase 0: Spec Lock

- [ ] Confirm Linking Contract v1 (required sections + link styles).
- [ ] Confirm `rc-link` CLI naming and scope (`scan|apply`, flags).
- [ ] Decide whether export rendering improvements are in-scope for v0.4.0.

### Phase 1: Tests First

- [ ] Add fixture-based tests for synthesis link insertion.
- [ ] Add tests for path-to-link upgrades (`reference/...`, `analysis/...`).
- [ ] Add idempotency tests (apply twice → no diff).
- [ ] Add tests for “non-existent target → no change”.
- [ ] Add tests for ambiguity reporting (no silent choice).

### Phase 2: Implement `rc-link`

- [ ] Implement `scan` report (structured output; human-readable summary).
- [ ] Implement `apply` with minimal diffs and conservative rules.
- [ ] Add `--dry-run` and `--only`/`--include` style filtering.
- [ ] Add entry point so users can run `rc-link ...` (packaging / CLI wiring).

### Phase 3: Template Updates + Regeneration

- [ ] Update `integrations/_templates/skills/synthesize.md.j2` to include `## Source Analyses`.
- [ ] Update analysis templates to include optional capture/transcript slots.
- [ ] Regenerate skills (`make assemble-skills`) and verify no drift.

### Phase 4 (Optional): Export Rendering Improvements

- [ ] If `location` contains `artifact=reference/...`, render as a clickable markdown link in evidence exports.
- [ ] Add tests for relative path computation from evidence export directories.

### Phase 5: Validation

- [ ] Run targeted tests for linker.
- [ ] Run full suite (`uv run pytest`).
- [ ] Run skill regeneration checks as needed.

### Phase 6: Docs + Release Prep (Docs-only until reviewer signoff)

- [ ] Update `docs/ANALYSIS-linking.md` with final decisions and usage examples.
- [ ] Draft changelog entry for v0.4.0 (after code merges, not in docs-only review pass).

## Worklog

### 2026-02-21: Plan + implementation trackers created

- Added v0.4.0 planning docs:
  - `docs/PLAN-v0.4.0.md`
  - `docs/IMPLEMENTATION-v0.4.0.md`
- Added linking research/state snapshot:
  - `docs/ANALYSIS-linking.md`

Next: circulate docs for review before any code changes.

