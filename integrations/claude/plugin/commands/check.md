---
allowed-tools: ["WebFetch", "Read", "Write", "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh *)", "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh *)"]
description: Full Reality Check analysis workflow - fetch, analyze, extract claims, register, validate
---

# /reality:check - Full Analysis Workflow

The flagship Reality Check command for rigorous source analysis.

**Core Methodology**: See `methodology/workflows/check-core.md` for the complete 3-stage analysis methodology, evidence hierarchy, claim types, and extraction format.

Before starting, read `methodology/workflows/check-core.md` and follow its **Output Contract**. In particular: the analysis markdown must include **claim tables** with **evidence levels** and **credence** (do not omit).

**IMPORTANT**: Always write to the DATA repository (pointed to by `REALITYCHECK_DATA`), never to the framework repository. If you see `scripts/`, `tests/`, `integrations/` - you're in the wrong repo.

## Usage

```
/reality:check <url>
/reality:check <url> --domain TECH --quick
/reality:check <source-id> --continue
/reality:check --continue
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
6. **Audit Log** - Append in-document Analysis Log + register `analysis_logs` row
7. **Validate** - Run integrity checks
8. **README** - Update data project analysis index
9. **Report** - Generate summary

If the prompt includes **multiple sources** (compare/contrast), produce the per-source analyses **and** write a single synthesis document in `analysis/syntheses/` as part of the same `/reality:check` run. Use `/reality:synthesize` later for standalone/iterative syntheses.

## Database Commands

```bash
# Register source
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" source add \
  --id "SOURCE_ID" \
  --title "TITLE" \
  --type "TYPE" \
  --author "AUTHOR" \
  --year YEAR \
  --url "URL"

# Register each claim
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" claim add \
  --id "CLAIM_ID" \
  --text "CLAIM_TEXT" \
  --type "[TYPE]" \
  --domain "DOMAIN" \
  --evidence-level "EX" \
  --credence 0.XX \
  --source-ids "SOURCE_ID"
```

## Audit Log

After registration, add an analysis log entry:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" analysis add \
  --source-id "SOURCE_ID" \
  --tool claude-code \
  --cmd check \
  --analysis-file "analysis/sources/SOURCE_ID.md" \
  --notes "Initial analysis + registration"

# Optional (token/cost capture from local session logs)
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" analysis add \
  --source-id "SOURCE_ID" \
  --tool claude-code \
  --cmd check \
  --analysis-file "analysis/sources/SOURCE_ID.md" \
  --model "claude-sonnet-4" \
  --usage-from claude:"/path/to/session.jsonl" \
  --estimate-cost \
  --notes "Initial analysis + registration"
```

## Validation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh"
```

## Version Control

The plugin's PostToolUse hooks automatically:
- Update README stats after db operations
- Stage and commit changes to `data/`, `analysis/`, `tracking/`, `README.md`
- Push if `REALITYCHECK_AUTO_PUSH=true`

## Related Commands

- `/reality:synthesize` - Cross-source synthesis across multiple analyses
- `/reality:analyze` - Manual 3-stage analysis without registration
- `/reality:extract` - Quick claim extraction
- `/reality:search` - Find related claims
- `/reality:validate` - Check database integrity
- `/reality:stats` - Show database statistics
