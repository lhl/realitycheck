# Plan: Analysis Linking + Backfill Tooling (v0.4.0)

**Status**: Spec Locked (Phase 0 complete)
**Created**: 2026-02-21
**Last Updated**: 2026-02-22
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

## Versioning / Sequencing Note

- This plan assumes “analysis linking + backfill tooling” is released as **v0.4.0** because it introduces a new CLI and updates multiple templates/workflows.
- “Pip-friendly skill/plugin installation” remains tracked separately in `docs/TODO.md` and can ship independently (e.g., as a v0.3.x patch/minor within the 0.x line).

## Non-goals

- Building a full static-site generator (Quartz/MkDocs/etc.) as part of v0.4.0.
- Capturing new artifacts from the web (this plan focuses on linking **existing** local artifacts).
- DB schema changes (v0.4.0 focuses on markdown navigation and can run without opening a DB).
- Enforcing strict “link completeness” gates in validators (warnings may be acceptable, hard errors are out of scope for v0.4.0).

## Locked Decisions (Phase 0)

All decisions locked as of 2026-02-22.

1. **Canonical link style inside `analysis/`**: section-relative links (e.g., `../sources/<source-id>.md`). **LOCKED (2026-02-22)**
2. **Write scope posture**: `rc-link` is **markdown-only write scope** (no DB/schema writes), but may discover files on disk to decide what links to add/report. **LOCKED (2026-02-22)**
3. **Validator posture**: no new validator WARN/ERROR gates in v0.4.0; `rc-link scan` is the completeness check. **LOCKED (2026-02-22)**
4. **`rc-link scan` output format**: human-readable text (validator-style INFO/WARN lines), no structured output required in v0.4.0. **LOCKED (2026-02-22)**
5. **Export rendering improvements**: optional stretch, independent of `rc-link`. **LOCKED (2026-02-22)**
6. **DB/schema posture**: no DB/schema changes in v0.4.0; `rc-link` must be markdown-only and runnable without opening a DB. **LOCKED (2026-02-22)**
7. **CLI root resolution**: `--project-root` is optional; default behavior auto-detects project root from CWD (same markers used by existing CLI helpers) and errors if none is found. **LOCKED (2026-02-22)**
8. **CLI filter contract**: v0.4.0 uses `--only syntheses,sources,claims` (comma-separated; default `syntheses,sources`); no `--include` alias in v0.4.0. **LOCKED (2026-02-22)**
9. **Exit codes**: success path returns `0` (including INFO/WARN findings); fatal usage/runtime/file-system errors return `2`. **LOCKED (2026-02-22)**
10. **Mutation boundaries**: never rewrite inside fenced code blocks, frontmatter, or HTML comments; avoid nested-link rewrites; edit only targeted sections/cells for minimal diffs. **LOCKED (2026-02-22)**
11. **Deterministic synthesis insertion**: `## Source Analyses` links are deduped and ordered by first source-ID appearance in the document; new section insertion is deterministic. **LOCKED (2026-02-22)**
12. **Synthesis template parity**: both `integrations/_templates/skills/synthesize.md.j2` and `methodology/templates/synthesis.md` are updated to use an explicit `## Source Analyses` section. **LOCKED (2026-02-22)**

### DB/schema changes: tradeoffs (separate milestone)

This plan’s default posture is **no DB/schema changes** in v0.4.0. If we reconsider that, the tradeoffs are:

**Pros of adding structured DB fields/tables for artifacts/locators**:

- Enables exports to render artifact links without parsing strings.
- Supports stronger validation and coverage metrics (e.g., “% of high-credence claims with primary artifacts + locators”).
- Makes it easier to build UI/static-site layers off canonical structured data.

**Cons**:

- Requires schema migration + backfill (risk of incorrect auto-population).
- Forces design decisions about “multiple artifacts per source” and artifact identity/fingerprints.
- Couples `rc-link` (markdown navigation) to DB availability and correctness; harder to run “on any folder of exported markdown.”

Recommendation for v0.4.0: keep `rc-link` markdown-only, and treat any structured artifact schema as a follow-on milestone once the linking contract is stable.

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
rc-link scan  [--project-root /path/to/data-repo] [--only syntheses,sources,claims]
rc-link apply [--project-root /path/to/data-repo] [--only syntheses,sources,claims] [--dry-run]
```

**Core principles**:

- **No guessing**: only add links when targets exist or when parsing is unambiguous.
- **Idempotent**: repeated `apply` runs should converge to zero diffs.
- **Minimal diffs**: insert missing sections/links; do not rewrite prose.
- **Offline**: no network.
- **Rooted**: never read/write outside `--project-root` (don’t follow symlinks that escape root).
- **Markdown-only writes**: filesystem discovery is allowed, but writes are limited to markdown files under `analysis/`.

**Root resolution**:

- If `--project-root` is provided, use it.
- If omitted, auto-detect project root from CWD using existing repo markers (`.realitycheck.yaml` preferred; fallback `data/realitycheck.lance` + minimal project structure).
- If no project root can be resolved, fail with usage guidance.

**`scan` output**:

- Default: line-oriented text similar to `rc-validate`, using `INFO`/`WARN` prefixes and file paths.
- Reports:
  - syntheses missing `## Source Analyses` section or missing per-source links
  - syntheses that mention source IDs but have no resolvable existing `analysis/sources/<source-id>.md`
  - analyses referencing `reference/...` paths that exist but are not linked
  - analyses containing claim IDs with reasoning docs available but not linked
  - malformed / unrecognized patterns (graceful skip + WARN)
  - ambiguities (conflicting patterns; duplicate IDs; invalid IDs)
- Exit codes:
  - `0`: scan completed (including WARN findings)
  - `2`: fatal usage/runtime/file-system error

**Known input patterns to handle (data-repo syntheses)**:

These are observed in real syntheses and should be supported in v0.4.0:

1. Blockquote metadata line: `> **Source IDs**: `...`` with comma-separated, backticked IDs.
2. A “Primary Sources” table with a `Source ID` column containing backticked IDs.
3. Existing source-analysis links/lists that should be treated as already satisfied (and should not be duplicated).

**`apply` behaviors (initial v0.4.0 scope)**:

1. **Synthesis link insertion**:
   - Parse source IDs from known patterns (see above).
   - If a synthesis already contains some source-analysis links, add only the missing ones (no duplicates).
   - Add (or fill) a `## Source Analyses` section with `../sources/<source-id>.md` links **when those files exist**.
   - If no source IDs are found, do not modify the file (report via `scan`).

2. **Path-to-link upgrades**:
   - Convert existing plain-text or code-span `reference/...` paths into markdown links when the target exists.
   - Convert existing plain-text `analysis/sources/...` mentions into markdown links when the target exists.
   - Discover candidate internal captures for a source from `reference/primary/`, `reference/captured/`, and `reference/transcripts/` when deterministic; if ambiguous, report and do not modify.

3. **Claim ID linking (selector-gated)**:
   - When `analysis/reasoning/<claim-id>.md` exists, link claim IDs in `analysis/sources/*.md` tables.
   - This behavior runs when `claims` is included in `--only` (it is not part of default `--only`).

4. **Edit boundaries (minimal-diff contract)**:
   - Do not edit fenced code blocks, frontmatter blocks, or HTML comments.
   - Do not rewrite existing markdown links whose targets already resolve.
   - Do not reorder unrelated sections or rewrite prose; only add/fill required link sections and targeted linkable cells.

**Relative path computation**:

- v0.4.0 can assume the conventional data-repo layout (`analysis/syntheses/`, `analysis/sources/`, `analysis/reasoning/`, `reference/`).
- Links inserted by `rc-link` should be computed relative to the file being edited, using filesystem path math (e.g., `os.path.relpath`) and normalized to POSIX-style slashes.
- If a computed link would escape `--project-root`, do not insert it (report via `scan`).
- Normalize all inserted links to POSIX slashes.

**Deterministic `## Source Analyses` insertion**:

- If section already exists, update it in place (add missing links only).
- If missing and `## Synthesis Metadata` exists, insert `## Source Analyses` immediately after that section.
- Otherwise insert after the first H1 block.
- Link list order is by first source-ID appearance in the synthesis (stable dedupe).

### C) Template updates (make “correct linking” the default skeleton)

Update templates so “the right place to put links” is always present:

- `integrations/_templates/skills/synthesize.md.j2`:
  - make `## Source Analyses` a required, explicit output section (not only a snippet example)
  - keep a minimal snippet, but also add a clear instruction in the output contract / required elements list
  - ensure the minimal snippet matches the contract (i.e., it shows a `## Source Analyses` section, not only an in-metadata bullet)
- `methodology/templates/synthesis.md`:
  - switch from metadata bullet style to an explicit `## Source Analyses` section for parity with skill contracts
- `integrations/_templates/analysis/source-analysis-full.md.j2` and `source-analysis-quick.md.j2`:
  - add optional rows/fields for `Captured Artifact` / `Transcript` (left blank if unknown)
  - place the new rows immediately after `URL` in the Metadata table

### D) Export improvements (optional stretch)

Improve `rc-export md evidence-by-claim` and `evidence-by-source` rendering:

- If an evidence `location` contains `artifact=<repo-relative-path>`, render `artifact` as a markdown link (relative to the exported evidence doc).

This should not change DB values; it’s purely presentation.

Note: This is independent of `rc-link` (which is markdown-only). It can be implemented in parallel or deferred.

## Affected Files (planned)

```
docs/
  NEW  PLAN-v0.4.0.md
  NEW  IMPLEMENTATION-v0.4.0.md
  UPDATE ANALYSIS-linking.md               # keep in sync with v0.4.0 scope

scripts/
  NEW  link.py                             # `rc-link` implementation

UPDATE pyproject.toml                       # add `rc-link` entry point

tests/
  NEW  test_link.py                         # unit + fixture-based tests
  UPDATE test_installation.py               # entry-point/import coverage for rc-link

integrations/_templates/
  UPDATE skills/synthesize.md.j2
  UPDATE analysis/source-analysis-full.md.j2
  UPDATE analysis/source-analysis-quick.md.j2

methodology/templates/
  UPDATE synthesis.md

README.md
  UPDATE CLI Reference                      # add `rc-link` usage

scripts/export.py (optional stretch)
  UPDATE evidence export rendering
```

## Tests and Verification Strategy

### Unit tests (linker)

1. **Synthesis linking**:
   - Adds `## Source Analyses` when missing.
   - Links only existing `analysis/sources/<id>.md` files.
   - Idempotent: second run yields no changes.
   - Handles malformed/unrecognized inputs gracefully (no change + report).
   - Does not duplicate existing links (adds only missing).
   - Uses deterministic section placement + link ordering.

2. **Path linking**:
   - Converts `` `reference/...` `` to `[reference/...](../../reference/...)` when target exists.
   - Leaves non-existent paths unchanged.
   - Preserves unrelated content verbatim (minimal diffs).
   - Refuses to link outside `--project-root` (path traversal / symlink safety).
   - Does not modify fenced code/frontmatter/comment blocks.

3. **Claim ID linking (optional)**:
   - Links claim IDs when `analysis/reasoning/<claim-id>.md` exists.
   - Leaves IDs bare when reasoning doc is missing.

4. **Safety / ambiguity**:
   - Reports ambiguous candidates; does not pick silently.
   - `--dry-run` produces reports but makes zero file modifications.
   - Exit code behavior matches contract (`0` for completed scan/apply with WARNs, `2` on fatal errors).

5. **CLI contract / packaging**:
   - Auto-detects project root when `--project-root` is omitted.
   - Fails with clear guidance when no project root is detected.
   - `rc-link --help` and module import are covered in installation tests.

### Manual verification

- Run `rc-link scan` and `rc-link apply` on a real data repo and confirm:
  - syntheses become “click-through” navigable,
  - analyses link to existing reference artifacts without breaking,
  - GitHub browsing works (no absolute filesystem paths).
