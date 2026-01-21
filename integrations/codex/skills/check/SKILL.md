---
name: check
description: "Reality Check analysis workflow for Codex - fetch, analyze, extract claims, register, validate."
---

# Reality Check `$check` (Codex)

The flagship Reality Check command for rigorous source analysis.

**Core Methodology**: See `methodology/workflows/check-core.md` for the complete 3-stage analysis methodology, evidence hierarchy, claim types, and extraction format.

## Invocation

```
$check <url>
$check <url> --domain TECH --quick
$check <source-id> --continue
$check --continue
```

Note: Codex CLI reserves `/...` for built-in commands. Use `$check ...` instead of `/check ...`.

## Arguments

- `url`: URL of the source to analyze
- `--domain`: Primary domain hint (TECH/LABOR/ECON/GOV/SOC/RESOURCE/TRANS/GEO/INST/RISK/META)
- `--quick`: Skip Stage 3 (dialectical analysis) for faster processing
- `--no-register`: Analyze without registering to database
- `--continue`: Continue/iterate on an existing analysis instead of starting fresh

## Preconditions

- The `realitycheck` Python package must be installed (`rc-db` and `rc-validate` on PATH)
- `REALITYCHECK_DATA` must be set

If `REALITYCHECK_DATA` is not set, prompt the user to either:
- Export it in their shell, or
- Use `$realitycheck data <path>` to set it for the current session

## Project Root + Analysis Files

**IMPORTANT**: Always write to the DATA repository, never to the framework repository. The framework repo (`realitycheck`) contains only code and methodology - no analysis data.

Derive the data project root from `REALITYCHECK_DATA`:

- If path ends with `.lance/` (typical): `PROJECT_ROOT = parent.parent`
- Otherwise: `PROJECT_ROOT = parent`

Store analysis files at: `PROJECT_ROOT/analysis/sources/<source-id>.md`

If you find yourself writing to a directory containing `scripts/`, `tests/`, `integrations/`, or `methodology/` - STOP. That's the framework repo, not the data repo.

## Workflow Steps

1. **Fetch** - Use `curl -L <url>` or similar to retrieve source content
2. **Extract HTML** - If HTML, use `rc-html-extract` to get `{title, published, text}`
3. **Metadata** - Extract title, author, date, type, generate source-id
4. **Analysis** - Perform 3-stage analysis (see methodology)
5. **Extract** - Format claims as YAML (see methodology)
6. **Register** - Add source and claims to database
7. **Validate** - Run integrity checks
8. **README** - Update data project analysis index
9. **Report** - Generate summary

## Database Commands

```bash
# Register source
rc-db source add \
  --id "SOURCE_ID" \
  --title "TITLE" \
  --type "TYPE" \
  --author "AUTHOR" \
  --year YEAR \
  --url "URL"

# Register each claim
rc-db claim add \
  --id "CLAIM_ID" \
  --text "CLAIM_TEXT" \
  --type "[TYPE]" \
  --domain "DOMAIN" \
  --evidence-level "EX" \
  --credence 0.XX \
  --source-ids "SOURCE_ID"

# Validate
rc-validate
```

## Embeddings Policy

By default, **do not skip embeddings**.

- Do not add `--no-embedding` unless:
  - The user explicitly asks to skip embeddings, or
  - Embedding generation fails and the user confirms they want to proceed anyway
- If embeddings are skipped, note it and suggest running `rc-embed generate` later
- If `REALITYCHECK_EMBED_SKIP` is set, treat that as explicit instruction to skip

## Data Repo Version Control (Codex)

Codex skills do not have hooks. After registration, explicitly handle version control:

1. If `PROJECT_ROOT/.git` exists and there are changes:
   ```bash
   # Optional: update README stats (if framework repo is available)
   bash <framework-root>/integrations/claude/plugin/scripts/update-readme-stats.sh "$PROJECT_ROOT"

   # Stage and commit
   git add data/ analysis/ tracking/ README.md
   git commit -m "data: add source(s)"

   # Push if REALITYCHECK_AUTO_PUSH=true
   git push
   ```

2. If unsure about auto-commit/push, ask before pushing.

**Commit messages** (match Claude plugin defaults):
- `data: add claim(s)` / `data: add source(s)` / `data: add chain(s)` / `data: add prediction(s)`
- `data: import data` / `data: initialize database` / `data: reset database`

## Related Skills

- `$realitycheck stats` - Database statistics
- `$realitycheck search <query>` - Find related claims
- `$realitycheck validate` - Check database integrity
