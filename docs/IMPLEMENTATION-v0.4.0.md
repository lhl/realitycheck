# Implementation: Analysis Linking + Backfill Tooling (v0.4.0)

**Status**: Spec Locked (Phase 0 complete; ready for Phase 1)
**Plan**: [PLAN-v0.4.0.md](PLAN-v0.4.0.md)
**Started**: 2026-02-21
**Last Updated**: 2026-02-22

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
- Markdown-only write scope: `rc-link` may discover files on disk, but only writes links into markdown docs.
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
  - does not discover/insert capture paths not already mentioned in the doc (upgrade-only; deterministic discovery is a stretch goal)
  - links claim IDs to `analysis/reasoning/<claim-id>.md` when `claims` is enabled via `--only`
- `rc-link` CLI contract is explicit and tested:
  - `--project-root` is optional; when omitted, resolution falls back to `REALITYCHECK_DATA` (if set) then CWD auto-detect
  - `--only` is the canonical selector (`syntheses,sources,claims`; default `syntheses,sources`)
  - exit codes: `0` for completed runs (including WARN findings), `2` for fatal usage/runtime errors
- Minimal-diff boundaries are enforced:
  - do not edit fenced code blocks, frontmatter, or HTML comments
  - do not duplicate/rewrite existing valid links
- Template updates land:
  - synthesis template explicitly requires a canonical `## Source Analyses` section (and includes it in the minimal snippet)
  - methodology synthesis template mirrors the same explicit `## Source Analyses` section
  - source analysis templates include optional metadata slots for internal captures/transcripts (blank by default)
- Targeted tests pass:
  - new linker tests
  - installation/entrypoint checks for `rc-link`
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
  NEW    link.py

UPDATE pyproject.toml                    # add `rc-link` entry point

tests/
  NEW    test_link.py
  UPDATE test_installation.py

integrations/_templates/
  UPDATE skills/synthesize.md.j2
  UPDATE analysis/source-analysis-full.md.j2
  UPDATE analysis/source-analysis-quick.md.j2

methodology/templates/
  UPDATE synthesis.md

README.md
  UPDATE CLI Reference

scripts/export.py (optional stretch)
  UPDATE evidence export rendering
```

## Locked Decisions (all locked 2026-02-22)

- **Link style**: section-relative (`../sources/<id>.md`) inside `analysis/`; repo-relative reserved for README-style indexes.
- **Artifact matching**: upgrade-only — `apply` converts existing in-doc path mentions to links when target exists; `scan` may report filesystem discoveries but `apply` must not act on them. No discovery-based insertion in v0.4.0.
- **Validator posture**: no new validator WARN/ERROR gates; `rc-link scan` is the completeness check.
- **`rc-link scan` output format**: human-readable INFO/WARN text (validator-style); no structured output in v0.4.0.
- **Export rendering**: optional stretch, independent of `rc-link`.
- **DB/schema**: no DB/schema changes; `rc-link` is markdown-only and can run without opening a DB.
- **CLI contract**: `--project-root` optional (fallback: `REALITYCHECK_DATA` resolved via `Path().expanduser().resolve()` — fail if invalid, do not fall through → CWD auto-detect), `--only` canonical selector, default `syntheses,sources`, no `--include`.
- **Exit code contract**: `0` for completed scan/apply (including WARN findings), `2` for fatal usage/runtime errors.
- **Mutation boundaries**: no edits in fenced code/frontmatter/comments; avoid nested link rewrites; minimal section/cell edits only.
- **Deterministic insertion**: stable section placement and source-link ordering.
- **Template parity**: skill + methodology synthesis templates both include explicit `## Source Analyses`.

## Punchlist

### Phase 0: Spec Lock

- [x] Lock decisions in `docs/PLAN-v0.4.0.md` (link style, artifact discovery posture, validator posture, scan format, DB/schema posture). ✓ 2026-02-22
- [x] Catalog “known input patterns” from a real data repo for synthesis parsing (and add to plan). ✓ 2026-02-22
- [x] Confirm `rc-link` CLI naming and scope (`scan|apply`, flags). ✓ 2026-02-22
- [x] Decide whether export rendering improvements are in-scope for v0.4.0 (independent of `rc-link`). ✓ optional stretch, locked 2026-02-22

### Phase 1: Tests First

- [ ] Add fixture-based tests for synthesis link insertion.
- [ ] Add tests for path-to-link upgrades (`reference/...`, `analysis/...`).
- [ ] Add idempotency tests (apply twice → no diff).
- [ ] Add tests for “non-existent target → no change”.
- [ ] Add tests for ambiguity reporting (no silent choice).
- [ ] Add tests for malformed/unrecognized inputs (skip + report; no crash).
- [ ] Add tests for already-linked content (no duplicates; add only missing).
- [ ] Add tests for `--dry-run` (zero modifications).
- [ ] Add tests for minimal diffs (preserve unrelated content/whitespace).
- [ ] Add path traversal / symlink safety tests (never link outside `--project-root`).
- [ ] Add tests for edit boundaries (no mutations inside fenced code/frontmatter/comments).
- [ ] Add tests for CLI root auto-detect + missing-root guidance.
- [ ] Add tests for exit code contract (`0` with WARN findings; `2` on fatal errors).
- [ ] Add tests for deterministic source-link ordering and insertion placement.

### Phase 2: Implement `rc-link`

- [ ] Implement `scan` report (human-readable INFO/WARN text + summary).
- [ ] Implement `apply` with minimal diffs and conservative rules.
- [ ] Add `--dry-run` and `--only` selector filtering (`syntheses,sources,claims`; default `syntheses,sources`).
- [ ] Add entry point so users can run `rc-link ...` (packaging / CLI wiring).
- [ ] Add project-root auto-detect behavior when `--project-root` is omitted.
- [ ] Enforce exit code + error message contract.
- [ ] Ensure relative links are computed from the edited file’s directory (normalized to POSIX slashes).

### Phase 3: Template Updates + Regeneration

- [ ] Update `integrations/_templates/skills/synthesize.md.j2` to include `## Source Analyses`.
- [ ] Update `methodology/templates/synthesis.md` to include a top-level `## Source Analyses` section (not metadata bullet-only).
- [ ] Update analysis templates to include optional capture/transcript slots.
- [ ] Regenerate skills (`make assemble-skills`) and verify no drift.

Note: Phase 2 and Phase 3 are independent and can be parallelized across agents once Phase 0 is locked.

### Phase 4 (Optional): Export Rendering Improvements

- [ ] If `location` contains `artifact=reference/...`, render as a clickable markdown link in evidence exports.
- [ ] Add tests for relative path computation from evidence export directories.

### Phase 5: Validation

- [ ] Run targeted tests for linker.
- [ ] Run installation/entrypoint checks that include `rc-link`.
- [ ] Run full suite (`uv run pytest`).
- [ ] Run skill regeneration checks as needed.

### Phase 6: Docs + Release Prep (Docs-only until reviewer signoff)

- [ ] Update `docs/ANALYSIS-linking.md` with final decisions and usage examples.
- [ ] Update `README.md` CLI reference with `rc-link` usage examples.
- [ ] Draft changelog entry for v0.4.0 (after code merges, not in docs-only review pass).

## Worklog

### 2026-02-21: Plan + implementation trackers created

- Added v0.4.0 planning docs:
  - `docs/PLAN-v0.4.0.md`
  - `docs/IMPLEMENTATION-v0.4.0.md`
- Added linking research/state snapshot:
  - `docs/ANALYSIS-linking.md`

Next: circulate docs for review before any code changes.

### 2026-02-22: Planner review incorporated (docs updates)

- Updated `docs/PLAN-v0.4.0.md` and this tracker to clarify:
  - synthesis template requirements vs snippet example
  - `rc-link` scope boundaries vs optional `rc-export` rendering improvements
  - known synthesis input patterns and scan output format expectations
  - additional test cases (malformed input, already-linked, dry-run, minimal diffs, symlink safety)

### 2026-02-22: Phase 0 complete (initial decision lock)

- Locked the initial 6 decisions: link style (section-relative), artifact discovery wording, validator posture (no new gates), scan output (INFO/WARN text), export rendering (optional stretch), DB/schema (markdown-only).
- Added `pyproject.toml` to affected files (for `rc-link` entry point).
- Removed "Open Questions" sections from both plan and implementation docs — all answers are now in the locked decisions block.
- Phase 0 punchlist complete. Ready for Phase 1 (tests first).

### 2026-02-22: Final pre-coding disambiguation pass

- Clarified that “in-doc only” means markdown-only write scope (no DB/schema mutation), not “no filesystem discovery.”
- Locked CLI semantics (`--project-root` optional auto-detect, `--only` canonical selector, exit code contract).
- Locked mutation boundaries (no fenced code/frontmatter/comment rewrites) and deterministic source-link insertion rules.
- Added methodology-template parity + README CLI docs + installation/entrypoint coverage to expected work items.
