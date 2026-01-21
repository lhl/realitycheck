---
name: check
description: Full Reality Check analysis workflow - fetch source, perform 3-stage analysis, extract claims, register to database, and validate. The flagship command for rigorous source analysis.
argument-hint: "<url> [--domain DOMAIN] [--quick] [--no-register] [--continue]"
allowed-tools: ["WebFetch", "Read", "Write", "Bash(uv run python scripts/db.py *)", "Bash(uv run python scripts/validate.py *)", "Bash(rc-db *)", "Bash(rc-validate *)"]
---

# /check - Full Analysis Workflow

The flagship Reality Check command for rigorous source analysis.

**Core Methodology**: See `methodology/workflows/check-core.md` for the complete 3-stage analysis methodology, evidence hierarchy, claim types, and extraction format.

Before starting, read `methodology/workflows/check-core.md` and follow its **Output Contract**. In particular: the analysis markdown must include **claim tables** with **evidence levels** and **credence** (do not omit).

**IMPORTANT**: Always write to the DATA repository (pointed to by `REALITYCHECK_DATA`), never to the framework repository. If you see `scripts/`, `tests/`, `integrations/` - you're in the wrong repo.

## Usage

```
/check <url>
/check <url> --domain TECH --quick
/check <source-id> --continue
/check --continue
```

## Arguments

- `url`: URL of the source to analyze
- `--domain`: Primary domain hint (TECH/LABOR/ECON/GOV/SOC/RESOURCE/TRANS/GEO/INST/RISK/META)
- `--quick`: Skip Stage 3 (dialectical analysis) for faster processing
- `--no-register`: Analyze without registering to database
- `--continue`: Continue/iterate on an existing analysis instead of starting fresh

## Workflow Steps

1. **Fetch** - Use `WebFetch` to retrieve source content
2. **Metadata** - Extract title, author, date, type, generate source-id
3. **Analysis** - Perform 3-stage analysis (see methodology)
4. **Extract** - Format claims as YAML (see methodology)
5. **Register** - Add source and claims to database
6. **Validate** - Run integrity checks
7. **README** - Update data project analysis index
8. **Report** - Generate summary

## Database Commands

Use installed commands if available, otherwise fall back to uv:

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

# Or with uv (from framework repo):
uv run python scripts/db.py source add ...
uv run python scripts/db.py claim add ...
```

## Validation

```bash
rc-validate
# or: uv run python scripts/validate.py
```

## Version Control

If running as a global skill (not via plugin), version control is manual:

1. After registration, check for changes in the data project
2. Stage: `git add data/ analysis/ tracking/ README.md`
3. Commit: `git commit -m "data: add source(s)"`
4. Push if desired: `git push`

## Related Commands

- `/analyze` - Manual 3-stage analysis without registration
- `/extract` - Quick claim extraction
- `/search` - Find related claims
- `/validate` - Check database integrity
- `/stats` - Show database statistics
