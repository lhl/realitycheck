---
name: check
description: "Reality Check check workflow for Codex (fetch, analyze, extract, register, validate)."
---

# Reality Check `$check` (Codex)

This skill mirrors the Claude Code `/check` workflow, but for Codex CLI.

## Invocation

- `$check <url> [--domain DOMAIN] [--quick] [--no-register]`
- `$check <source-id> --continue` - Continue an existing analysis
- `$check --continue` - Continue the most recent analysis

Note: Codex CLI reserves `/...` for built-in commands. Use `$check ...` (or plain text asking for a check) instead of `/check ...`.

## Preconditions

- Assume the `realitycheck` Python package is installed (so `rc-db` and `rc-validate` are on `PATH`).
- Assume `REALITYCHECK_DATA` is set.

If `REALITYCHECK_DATA` is not set, ask the user to either:
- Export it in their shell, or
- Use `$realitycheck data <path>` (see the `realitycheck` Codex skill) to set it for the current Codex session.

## Project Root + Analysis Files

Treat `REALITYCHECK_DATA` as the source of truth for where the data project lives:

- Let `DB_PATH = REALITYCHECK_DATA` (resolve to an absolute path).
- If `DB_PATH` ends with `.lance/` (typical), assume the data project root is `DB_PATH.parent.parent`.
- Otherwise, assume the data project root is `DB_PATH.parent`.

Store (and continue) analysis markdown files under:
- `PROJECT_ROOT/analysis/sources/<source-id>.md`

## Embeddings Policy (Important)

By default, **do not skip embeddings**.

- When registering sources/claims with `rc-db`, **do not** add `--no-embedding` unless:
  - The user explicitly asks to skip embeddings, or
  - Embedding generation fails (e.g., missing local model / offline) and the user confirms they want to proceed anyway.
- Do not add `--no-embedding` “for safety” or “to avoid dependencies”. Treat embeddings as part of the default workflow.
- If embeddings are skipped, note it in the analysis log and suggest running `rc-embed generate` later.
- If `REALITYCHECK_EMBED_SKIP` is set in the environment, treat that as an explicit instruction to skip embeddings.

## Continuation Mode

When `--continue` is specified (or when the user asks to continue an existing analysis):

1. **Find existing analysis**: Look for `analysis/sources/[source-id].md`
2. **Read current state**: Load the existing analysis and registered claims
3. **Iterate, don't overwrite**: Add to the existing analysis rather than replacing it
4. **Focus areas**:
   - Extract claims that were skipped or noted as "TODO"
   - Deepen specific sections (more counterfactuals, stronger steelman)
   - Address questions or gaps identified in the original pass
   - Cross-reference with newly added claims in the database

**Important**: Preserve all existing content. Append new sections and note what was added in this pass.

## Execution Outline

1. **Preflight**
   - Confirm `rc-db` and `rc-validate` are available.
   - Confirm `REALITYCHECK_DATA` is set (or prompt to set it).
   - Determine `PROJECT_ROOT` from `REALITYCHECK_DATA` and ensure `analysis/sources/` exists.
2. **Fetch the source**
   - Prefer `curl -L <url>` and save the raw content to a temporary file.
   - If the URL is a PDF, download it and extract text (e.g., via `pdftotext` if available).
   - If the URL is HTML, extract `{title, published, text}` with:
     - `rc-html-extract /path/to/page.html --format json`
     Use the extracted `text` as the input for the 3-stage analysis (and `title/published` for source metadata).
3. **Decide analysis target**
   - If this is a new analysis, generate a stable `source-id` and create `analysis/sources/<source-id>.md`.
   - If `--continue` is set, locate the existing `analysis/sources/<source-id>.md` (or pick the most recent) and append.
4. **Three-stage analysis**
   - Stage 1: descriptive (summary, key claims, predictions, assumptions, terms)
   - Stage 2: evaluative (coherence, evidence quality, disconfirmation, rhetoric)
   - Stage 3: dialectical (steelman, counterarguments, synthesis) unless `--quick`
5. **Extract claims**
   - Produce a YAML block of claims (type/domain/evidence_level/credence/operationalization).
6. **Register (optional)**
   - If not `--no-register`: add the source + claims via `rc-db`, then run `rc-validate`.
   - Generate embeddings by default (see Embeddings Policy).

## Commands (preferred)

Use installed entry points when available:

- `rc-db ...`
- `rc-validate ...`

If those aren’t on `PATH`, fall back to running from the framework repo:

- `uv run python scripts/db.py ...`
- `uv run python scripts/validate.py ...`

## Updating the Data Project README

After completing an analysis, update the data project's `README.md` analysis index:

1. **Add to Source Analyses table**: Insert a new row **at the top** of the "Source Analyses" table (reverse chronological order - newest first):

```markdown
| Date | Document | Status | Summary |
|------|----------|--------|---------|
| YYYY-MM-DD | [Author "Title"](analysis/sources/source-id.md) | `[REVIEWED]` | Brief 1-line summary |  ← INSERT HERE (top of table)
| ... existing rows below ... |
```

**Status values:**
- `[REVIEWED]` - Analysis complete, claims extracted and registered
- `[DRAFT]` - In progress
- `[PENDING]` - Awaiting analysis

**Example row:**
```
| 2026-01-21 | [Stross "The pivot"](analysis/sources/stross-2025-the-pivot-1.md) | `[REVIEWED]` | 2025 inflection-point thesis |
```

2. **Stats are auto-generated**: The counts table at the top is updated by `update-readme-stats.sh` (see below).

## Data Repo Version Control (Codex)

Codex skills do not support Claude Code-style hooks. After successful registration (any `rc-db` write operation), explicitly handle version control for the data project:

1. If `PROJECT_ROOT/.git` exists and there are changes under `data/`, `analysis/`, `tracking/`, or `README.md`:
   - If you can locate the framework repo (common when using these skills), update README stats (optional but recommended):
     - `bash <framework-root>/integrations/claude/plugin/scripts/update-readme-stats.sh "$PROJECT_ROOT"`
     - If you can't find it, skip this step.
   - Commit (default behavior mirrors the Claude plugin: commit is on, push is off):
     - If `REALITYCHECK_AUTO_COMMIT` is unset or `true`, run:
       - `git add data/ analysis/ tracking/ README.md`
       - `git commit -m "<message>"`
       Where `<message>` mirrors the plugin defaults:
       - `data: add claim(s)` / `data: add source(s)` / `data: add chain(s)` / `data: add prediction(s)`
       - `data: import data` / `data: initialize database` / `data: reset database`
     - If `REALITYCHECK_AUTO_PUSH=true`: `git push`
2. If the user is unsure about auto-commit/push, ask before pushing.
