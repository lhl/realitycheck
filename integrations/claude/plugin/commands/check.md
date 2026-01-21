---
allowed-tools: ["WebFetch", "Read", "Write", "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh *)", "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh *)"]
description: Full Reality Check analysis workflow - fetch, analyze, extract claims, register, validate
---

# /reality:check - Full Analysis Workflow

The flagship Reality Check command for rigorous source analysis.

**Core Methodology**: See `methodology/workflows/check-core.md` for the complete 3-stage analysis methodology, evidence hierarchy, claim types, and extraction format.

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
6. **Validate** - Run integrity checks
7. **README** - Update data project analysis index
8. **Report** - Generate summary

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

- `/reality:analyze` - Manual 3-stage analysis without registration
- `/reality:extract` - Quick claim extraction
- `/reality:search` - Find related claims
- `/reality:validate` - Check database integrity
- `/reality:stats` - Show database statistics
