# Plan: Analysis Linking + Backfill Tooling (v0.4.0)

**Status**: Draft (review requested)
**Created**: 2026-02-21
**Last Updated**: 2026-02-21
**Version**: 0.4.0 (proposed)
**Implementation**: [IMPLEMENTATION-v0.4.0.md](IMPLEMENTATION-v0.4.0.md)
**Research / State Snapshot**: [ANALYSIS-linking.md](ANALYSIS-linking.md)

## Motivation

Reality Check knowledge bases are valuable, but navigation is currently higher-friction than it should be:

- Syntheses often don’t link back to per-source analyses.
- Source analyses often don’t link to internal captures/archives (`reference/`), even when they exist.
- Evidence/reasoning exports exist, but cross-linking is inconsistent, so users can’t “click through” the provenance graph.

This makes GitHub browsing (and any future static-site “digital garden” publishing) less pleasant than it could be, and creates unnecessary overhead for reviewers.

## Problem Statement

We have three intertwined problems:

### 1) No lightweight linking contract for Markdown docs

Docs don’t consistently specify:

- what must be linked in a synthesis,
- how to represent internal capture links in source analyses,
- when/where to link claim IDs to reasoning docs,
- how to keep links stable under GitHub browsing and static-site builds.

### 2) Linking is not “low overhead” for analyst agents

Even when an internal artifact exists, the agent usually has to:

- remember to add the link,
- compute the correct relative path,
- avoid inconsistencies in section naming and formatting.

This makes linking behave like “extra work” rather than “free leverage.”

### 3) No backfill tooling for existing knowledge bases

We already have substantial corpora (`analysis/`, `reference/`, exported `analysis/reasoning/`, `analysis/evidence/`), but we lack a safe, idempotent “linker” that can:

- find link opportunities (“if it exists locally, link it”),
- apply minimal diffs,
- report ambiguities rather than guessing.

## Goals (v0.4.0)

1. **Adopt a small Linking Contract v1** for data-repo markdown that is:
   - low-overhead for analysts,
   - GitHub-friendly (relative links),
   - scriptable and idempotent.
2. **Provide an `rc-link` helper** that can `scan` and `apply` link improvements to a data repo.
3. **Make new outputs link-ready by default** by updating templates so syntheses and analyses include the right sections/fields (even if blank).
4. **Enable practical backfill** so existing KBs can become navigable without manual editing.

## Non-goals

- Building a full static-site generator (Quartz/MkDocs/etc.) as part of v0.4.0.
- Capturing new artifacts from the web (this plan focuses on linking **existing** local artifacts).
- DB schema changes.
- Enforcing strict “link completeness” gates in validators (warnings may be acceptable, hard errors are out of scope for v0.4.0).

## Proposed Design

### A) Linking Contract v1 (Markdown, data repo)

These requirements are deliberately minimal and “mechanically checkable.”

**Syntheses** (`analysis/syntheses/*.md`):

- Must include a `## Source Analyses` section with markdown links to each available `analysis/sources/<source-id>.md`:

```markdown
## Source Analyses

- [source-id-1](../sources/source-id-1.md)
- [source-id-2](../sources/source-id-2.md)
```

**Source analyses** (`analysis/sources/*.md`):

- Must include a canonical external `URL` when one exists (or `N/A` for local memos).
- Should include a canonical internal capture link **when an artifact exists**, using markdown links (not code spans) to:
  - `reference/primary/...` (public/redistributable), or
  - `reference/captured/...` (captured copyrighted content / metadata), or
  - `reference/transcripts/...` (AI transcript inputs).

**Reasoning exports** (`analysis/reasoning/*.md`):

- Already link to per-source analyses via `../sources/<source-id>.md` (keep).

**Claim IDs** (optional-but-recommended):

- If `analysis/reasoning/<claim-id>.md` exists, link claim IDs in tables:
  - `TECH-2026-001` → `[TECH-2026-001](../reasoning/TECH-2026-001.md)`

This is backwards-compatible: the validator already supports linked claim IDs.

### B) New CLI: `rc-link`

Add a new helper CLI designed for safe, idempotent markdown linking in data repos:

```bash
rc-link scan  --project-root /path/to/data-repo
rc-link apply --project-root /path/to/data-repo [--dry-run] [--only ...]
```

**Core principles**:

- **No guessing**: only add links when targets exist or when parsing is unambiguous.
- **Idempotent**: repeated `apply` runs should converge to zero diffs.
- **Minimal diffs**: insert missing sections/links; do not rewrite prose.
- **Offline**: no network.

**`scan` output**:

- syntheses missing `Source Analyses` section or missing per-source links
- analyses referencing `reference/...` paths that exist but are not linked
- analyses containing claim IDs with reasoning docs available but not linked
- ambiguities (multiple candidate artifacts; conflicting patterns)

**`apply` behaviors (initial v0.4.0 scope)**:

1. **Synthesis link insertion**:
   - Parse source IDs from common patterns (e.g., `> **Source IDs**: ...`, “Primary Sources” tables).
   - Add/refresh `## Source Analyses` with `../sources/<source-id>.md` links **when those files exist**.

2. **Path-to-link upgrades**:
   - Convert existing plain-text or code-span `reference/...` paths into markdown links when the target exists.
   - Convert existing plain-text `analysis/sources/...` mentions into markdown links when the target exists.

3. **Claim ID linking (optional flag)**:
   - When `analysis/reasoning/<claim-id>.md` exists, link claim IDs in `analysis/sources/*.md` tables.

### C) Template updates (make “correct linking” the default skeleton)

Update templates so “the right place to put links” is always present:

- `integrations/_templates/skills/synthesize.md.j2`:
  - add explicit `## Source Analyses` section to the minimal snippet
  - make the “Source analysis links” requirement more explicit and easier to satisfy
- `integrations/_templates/analysis/source-analysis-full.md.j2` and `source-analysis-quick.md.j2`:
  - add optional rows/fields for `Captured Artifact` / `Transcript` (left blank if unknown)

### D) Export improvements (optional stretch)

Improve `rc-export md evidence-by-claim` and `evidence-by-source` rendering:

- If an evidence `location` contains `artifact=<repo-relative-path>`, render `artifact` as a markdown link (relative to the exported evidence doc).

This should not change DB values; it’s purely presentation.

## Affected Files (planned)

```
docs/
  NEW  PLAN-v0.4.0.md
  NEW  IMPLEMENTATION-v0.4.0.md
  UPDATE ANALYSIS-linking.md               # keep in sync with v0.4.0 scope

scripts/
  NEW  link.py (or linker.py)              # `rc-link` implementation

tests/
  NEW  test_link.py (or test_linker.py)    # unit + fixture-based tests

integrations/_templates/
  UPDATE skills/synthesize.md.j2
  UPDATE analysis/source-analysis-full.md.j2
  UPDATE analysis/source-analysis-quick.md.j2

scripts/export.py (optional stretch)
  UPDATE evidence export rendering
```

## Tests and Verification Strategy

### Unit tests (linker)

1. **Synthesis linking**:
   - Adds `## Source Analyses` when missing.
   - Links only existing `analysis/sources/<id>.md` files.
   - Idempotent: second run yields no changes.

2. **Path linking**:
   - Converts `` `reference/...` `` to `[reference/...](../../reference/...)` when target exists.
   - Leaves non-existent paths unchanged.

3. **Claim ID linking (optional)**:
   - Links claim IDs when `analysis/reasoning/<claim-id>.md` exists.
   - Leaves IDs bare when reasoning doc is missing.

4. **Safety / ambiguity**:
   - Reports ambiguous candidates; does not pick silently.

### Manual verification

- Run `rc-link scan` and `rc-link apply` on a real data repo and confirm:
  - syntheses become “click-through” navigable,
  - analyses link to existing reference artifacts without breaking,
  - GitHub browsing works (no absolute filesystem paths).

## Open Questions

1. **Canonical link style**: do we prefer repo-relative links (`analysis/sources/...`) or section-relative links (`../sources/...`) inside syntheses?
2. **Artifact matching**: should v0.4.0 attempt heuristics to “discover” captures, or only link captures already mentioned in-doc (plus syntheses → analyses)?
3. **Validator posture**: do we add WARN-only checks for syntheses missing `Source Analyses`, or keep validation strictly out of scope for v0.4.0?

