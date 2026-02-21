# Reality Check v0.4.0 (proposed) — Analysis Linking (state as of v0.3.3; 2026-02-21)

This document is a “state of the union” for how Reality Check **links** (or fails to link) analysis artifacts as of **v0.3.3**, and the v0.4.0 linking direction.

Goal: make Reality Check knowledge bases feel like a navigable, low-friction **hypertext system** (sources ↔ analyses ↔ syntheses ↔ evidence ↔ reasoning ↔ archives) without imposing high overhead on the analyst/agent.

---

## TL;DR

- **External URLs are necessary but not sufficient**: they support discovery and re-fetching, but do not guarantee reproducibility (link rot + moving targets).
- **Our intended “auditability posture” already exists** in the framework: high-impact claims should point to **captured artifacts + locators** via `evidence_links.location` (see `docs/WORKFLOWS.md` and `docs/SCHEMA.md`).
- **Our actual markdown linking in the data repo is inconsistent**:
  - Repo README provides an index of syntheses + source analyses (good).
  - Syntheses usually list *source IDs* but often do **not** link to the per-source analysis files (bad for navigation).
  - Source analyses usually have a canonical URL but often omit (or don’t link to) internal captures/archives.
- **Next step**: adopt a lightweight “Linking Contract v1” for markdown docs plus a small helper (`rc-link`) that makes linking **automatic and idempotent**: *if it exists locally, link it*.

---

## Terminology: what we want to link

Reality Check typically lives as two repositories:

- **Framework repo** (this repo): code + templates + contracts.
- **Data repo** (your knowledge base): the actual DB + analyses + reference artifacts.

Within a data repo, these are the main “linkable” objects:

- `analysis/sources/<source-id>.md` — per-source analysis (human-auditable).
- `analysis/syntheses/<synth-id>.md` — cross-source synthesis.
- `analysis/reasoning/<claim-id>.md` — exported reasoning trails (human-auditable).
- `analysis/evidence/by-claim/<claim-id>.md` and `analysis/evidence/by-source/<source-id>.md` — exported evidence indexes.
- `reference/primary/**` — captured redistributable artifacts (e.g., court PDFs, official docs).
- `reference/captured/**` — captured copyrighted materials and/or metadata sidecars (depending on your repo posture).
- `reference/transcripts/**` — captured AI conversation transcripts used in analyses.
- `README.md` + `reference/README.md` — navigation and indexes.

DB-side objects (canonical “truth”):

- `sources.url` (canonical external URL when available).
- `sources.analysis_file` (points to `analysis/sources/...`).
- `evidence_links.location` (rigor-v1 mini-schema: `artifact=...; locator=...` or `capture_failed=...`).

---

## Current “policy” (as documented/implemented in the framework)

### 1) URLs: canonical external pointer for a source

- The schema supports `sources.url` and `sources.doi` (`docs/SCHEMA.md`).
- The analysis templates include a **URL** field in Metadata (`integrations/_templates/analysis/source-analysis-full.md.j2`).

This is the *canonical pointer* to the live source, not an archival guarantee.

### 2) High-impact provenance: captured artifacts + locators (not just URLs)

For high-impact claims, our documented posture is:

- Prefer **primary-first** (gov/court/official docs when applicable).
- Capture the primary artifact when possible.
- In `evidence_links.location`, record either:
  - `artifact=<repo-relative-path>; locator=<page/section/lines>; notes=<optional>`, or
  - `capture_failed=<reason>; primary_url=<url>; fallback=<what was used instead>`.

See:
- `docs/WORKFLOWS.md` (“Primary Evidence + Artifact Linkage” and “Capture tiers”)
- `docs/SCHEMA.md` (`evidence_links.location`)

### 3) Syntheses should link back to per-source analyses

This is already the stated workflow contract:

- The `check` workflow requires that a multi-source run produces per-source analyses and “the synthesis should link back.” See `integrations/_templates/skills/check.md.j2`.
- The `synthesize` workflow output contract explicitly asks for **source analysis links** (prefer linking `analysis/sources/<source-id>.md`). See `integrations/_templates/skills/synthesize.md.j2`.
- The methodology synthesis template demonstrates this: `methodology/templates/synthesis.md`.

### 4) Claim IDs can be markdown links (validator already supports it)

The analysis validator recognizes both bare and markdown-linked claim IDs, e.g.:

- `TECH-2026-001`
- `[TECH-2026-001](../reasoning/TECH-2026-001.md)`

See `scripts/analysis_validator.py` and `scripts/analysis_formatter.py`.

---

## Observed state (realitycheck-data corpus snapshot)

This section is an observational snapshot from one local data repo:

- Data repo: `realitycheck-data`
- Commit: `f5704b23b5a2bb18979bf2b42a1635e43677f96f`
- Observed on: **2026-02-21**

Commands used:

```bash
cd /home/lhl/github/lhl/realitycheck-data

find analysis/sources -type f -name '*.md' | wc -l
find analysis/syntheses -type f -name '*.md' | wc -l
find analysis/reasoning -type f -name '*.md' | wc -l
find analysis/evidence/by-source -type f -name '*.md' | wc -l
```

Snapshot results:

- `analysis/sources/*.md`: **120**
- `analysis/syntheses/*.md`: **18**
- `analysis/reasoning/*.md`: **165**
- `analysis/evidence/by-source/*.md`: **56**

Qualitative findings:

1. **Top-level index links exist and work**:
   - `README.md` links to syntheses and per-source analyses.
   - `reference/README.md` links external URLs and (sometimes) internal analyses.
2. **Synthesis → source-analysis navigation is usually missing inside the synthesis docs**:
   - syntheses tend to list `Source IDs` as text/code, but do not consistently include clickable links to `analysis/sources/<source-id>.md`.
3. **Source analysis → internal archive linking is inconsistent**:
   - Many analyses have a canonical external URL.
   - Some analyses include “Captured Artifact” / “Primary capture” notes, but often as code spans or ad-hoc prose instead of consistent markdown links.
4. **Evidence link locations are not normalized to the artifact mini-schema** in exported evidence indexes:
   - Many locations are text blobs like `Analysis file: ...; URL: ...`.
   - Some use `artifact=pdf; locator=...` (not enough to locate the actual file in `reference/`).

Takeaway: we have the *ingredients* for a navigable KB (captures, reasoning docs, evidence indexes), but we don’t yet have **cheap, consistent hyperlinking** across those objects.

---

## Linking Contract v1 (low-overhead, human-facing)

This is intentionally minimal: it should be easy for a human or agent to follow, and easy for scripts to implement.

### Guiding principles

1. **If it exists locally, link it.** No treasure hunts.
2. **Prefer relative links** so navigation works on GitHub and in static-site builds.
3. **Idempotent changes**: helper scripts should only add missing links/sections, not rewrite prose.
4. **Don’t break older analyses**: linking upgrades should be optional and backwards-compatible.

### Required links (new work)

**For every synthesis** (`analysis/syntheses/*.md`):

- Include a `Source Analyses` list with markdown links:

```markdown
## Source Analyses

- [amodei-2024-machines-of-loving-grace](../sources/amodei-2024-machines-of-loving-grace.md)
- [dwarkesh-2026-amodei-end-of-exponential](../sources/dwarkesh-2026-amodei-end-of-exponential.md)
```

**For every source analysis** (`analysis/sources/*.md`):

- Keep `URL` as the canonical external URL when available (or `N/A` for local memos).
- If a local capture exists, add **one** canonical link (prefer “best available”):
  - `Captured Artifact` (for copyrighted/news/papers/blogs) OR
  - `Primary capture` (for public/redistributable primary docs)

Use a markdown link whose label is the repo-relative path:

```markdown
| **Captured Artifact** | [`reference/captured/<...>`](../../reference/captured/<...>) |
```

**For claim IDs in analysis tables** (optional-but-recommended):

- If `analysis/reasoning/<claim-id>.md` exists, link the claim ID:

```markdown
| [TECH-2026-001](../reasoning/TECH-2026-001.md) | ... |
```

### Optional links (when relevant)

- If an analysis is based on a transcript in `reference/transcripts/`, include a transcript link.
- If an analysis depends on an internal “seed memo” in `reference/captured/`, link it (explicitly mark it as seed context, not a primary source).
- If evidence is attached via `evidence_links`, prefer `artifact=reference/...; locator=...` so audits can jump to the captured file.

---

## Automation proposal: `rc-link` (and minimal framework improvements)

We want the analyst/agent workflow to be:

- write analysis/synthesis normally,
- run one command,
- get all “obvious” internal links filled in.

### Proposed CLI (framework-side)

Add a new helper that operates on a data repo:

```bash
rc-link scan   # report missing link opportunities
rc-link apply  # apply safe, idempotent link insertions
```

Key properties:

- **Safe-by-default**: only adds links when the target file exists.
- **Idempotent**: repeated runs produce zero diffs after convergence.
- **Scoped**: can target only syntheses, only sources, or only a file list (for post-check hooks).

### Proposed behaviors

**Synthesis linker**

- Parse `Source IDs` in syntheses (common patterns: `> **Source IDs**: ...` and/or “Primary Sources” tables).
- For each `source-id` where `analysis/sources/<source-id>.md` exists, insert/update a `## Source Analyses` section with `../sources/...` links.

**Source-analysis linker**

- Determine `source_id` (from metadata, or from filename as fallback).
- Try to find a best-match captured artifact in `reference/`:
  - Prefer exact filename matches, then directory-name matches, with a filetype priority (e.g., `.pdf` > `.md` > `.html` > `.txt` > `.json` > `.zip`).
  - If multiple plausible matches exist, don’t guess silently: report ambiguity in `scan`.
- Insert a `Captured Artifact` / `Primary capture` row/link if missing.

**Claim→reasoning linker**

- For `analysis/sources/*.md`, scan claim tables for claim IDs.
- If `analysis/reasoning/<claim-id>.md` exists, link the ID (validator already supports this).

### Minimal framework improvements that make linking cheaper

These are low-risk changes that reduce analyst overhead:

1. **Add optional capture fields to analysis templates**
   - Extend `integrations/_templates/analysis/source-analysis-full.md.j2` and `source-analysis-quick.md.j2` to include optional `Captured Artifact` / `Transcript` rows (left blank if unknown).
2. **Make synthesis templates explicitly include `Source Analyses` links**
   - Ensure generated syntheses include the section in the default skeleton, matching `methodology/templates/synthesis.md`.
3. **(Optional) Improve `rc-export md evidence-*` outputs**
   - If an evidence `location` contains `artifact=reference/...`, render it as a markdown link to the artifact path (relative to the evidence doc).

---

## Backfill plan (existing KBs)

The backfill should be cheap and mostly mechanical.

### Step 0: Run a scan report

```bash
rc-link scan --project-root /path/to/realitycheck-data
```

Report should include:

- syntheses missing `Source Analyses` section
- source analyses missing capture links (when a capture file exists)
- analyses with claim IDs that have reasoning docs but aren’t linked
- ambiguities (multiple candidate capture files)

### Step 1: Apply safe link insertions

```bash
rc-link apply --project-root /path/to/realitycheck-data --only syntheses,sources,claims --dry-run
rc-link apply --project-root /path/to/realitycheck-data --only syntheses,sources,claims
```

### Step 2: Regenerate derived docs (optional)

If your evidence/reasoning indexes are exported artifacts, re-run exports after any DB-side normalization work (if performed).

### Step 3: Validate and commit

```bash
rc-validate
git status --porcelain
```

---

## Digital garden implication

If we keep links:

- relative,
- stable,
- and “repo-native” (no special GitHub-only URL formats),

then a Reality Check data repo becomes publishable as:

- a GitHub-native browsable KB, and/or
- a static site (Quartz/MkDocs/etc.) with minimal additional tooling.

The “Linking Contract v1” + `rc-link` is the shortest path to making this feel good without increasing analyst burden.
