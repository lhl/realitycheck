# Plan: Ergonomics (To Decide)

**Status**: TBD decisions
**Created**: 2026-01-24

This document captures agent-ergonomics ideas that are clearly valuable, but require product/workflow decisions before implementation.

## A) One-shot finish / publish command

### Goal

Provide a single command (or script) that takes an analysis artifact and “finishes” the workflow end-to-end:

1. `rc-db import analysis/sources/<id>.yaml --type all`
2. `rc-db analysis add ...` (including usage/cost capture if available)
3. `rc-validate`
4. update README stats and insert/update a README table row
5. `git add/commit` (and optionally `push`)

### Decisions Needed

- **Where does this run?**
  - data repo only? framework repo? both?
- **Git behavior defaults**
  - Should it ever `push` by default?
  - Should it require a clean working tree?
  - Commit message format: deterministic vs. freeform notes?
  - Branch handling: current branch only vs. configurable?
- **README updates**
  - Which README is updated (data repo README vs. something else)?
  - How is the “analysis row” keyed (by `source_id`?) and what columns exist?
  - Should it update a per-source index as well?
- **Failure policy**
  - Stop-on-first-failure vs. best-effort continuation with summary?
  - Rollback expectations (if import succeeds but validate fails)?
- **Integration parity**
  - Should this mirror Claude plugin hooks (post-db-modify / auto-commit) or stay separate?

### Proposed Output Artifacts (tentative)

- updated `analysis/sources/<id>.md` (includes in-document Analysis Log)
- DB updated and validated
- `README.md` updated via `scripts/update-readme-stats.sh`

## B) `rc-analysis new <source-id> --from-url URL` skeleton generator

### Goal

Help agents start from a known-good artifact shape by generating:

- `analysis/sources/<source-id>.md` skeleton (correct headings + Analysis Log placeholder)
- `analysis/sources/<source-id>.yaml` stub (source metadata + empty claim list in canonical format)

### Decisions Needed

- **ID generation**
  - Require explicit `<source-id>` always, or allow deriving from URL/title?
- **Template source of truth**
  - Use `methodology/templates/`? a new `integrations/_templates/` artifact? or embed in code?
- **YAML schema**
  - What exact YAML structure is “canonical” for `rc-db import --type all`?
  - How do we represent partially known metadata (author/year/doi)?
- **URL handling**
  - Should we fetch the URL (network) to auto-fill title/author/date?
  - If yes, which extractor (`scripts/html_extract.py`?) and what is the fallback behavior?
- **Where does it live**
  - `rc-analysis` as a new CLI? or `rc-db analysis new`?

