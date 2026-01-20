# RealityCheck Workflows

Common workflows for using the RealityCheck framework.

## Quick Start

### Initialize Database

```bash
# Create empty database
rc-db init

# Verify
rc-validate
```

### Migrate from Legacy YAML

```bash
# Dry run to see what will be migrated
rc-migrate /path/to/legacy/repo --dry-run -v

# Run migration
rc-migrate /path/to/legacy/repo -v

# Validate result
rc-validate
```

## Source Analysis Workflow

### 1. Analyze a Source

Use the `/analyze` command or manually follow the template:

```bash
# With plugin
/analyze https://example.com/ai-report-2024

# Manual: copy methodology/templates/source-analysis.md
```

### 2. Extract Claims

```bash
# Quick extraction
/extract "AI will automate 50% of jobs by 2030"

# From URL
/extract https://arxiv.org/abs/2301.xxxxx
```

### 3. Add to Database

```bash
# Add a claim
rc-db add claim --id TECH-2026-001 --text "..." --type "[T]" --domain TECH --evidence E2 --credence 0.75

# Add a source
rc-db add source --id epoch-2024-training --title "Epoch AI Training Report"
```

### 4. Generate Embeddings

```bash
# Check embedding status
rc-embed check

# Generate missing embeddings
rc-embed generate
```

### 5. Validate

```bash
rc-validate
```

## Search Workflow

### Semantic Search

```bash
# Search claims
rc-db search "AI automation labor displacement"

# Filter by domain
/search "training costs" --domain TECH --limit 5
```

### Get Related Claims

```bash
rc-db related TECH-2026-001
```

## Chain Analysis Workflow

### 1. Identify Chain Structure

Trace the logical argument: A → B → C → Conclusion

### 2. Rate Each Step

Assign credence to each claim in the chain.

### 3. Calculate Chain Credence

Chain credence = MIN(step credences)

### 4. Add Chain to Database

```bash
rc-db add chain --id CHAIN-2026-001 --name "Automation Displacement" \
  --thesis "AI will cause mass unemployment" \
  --claims TECH-2026-001,LABOR-2026-002,ECON-2026-003 \
  --credence 0.45
```

## Prediction Tracking Workflow

### 1. Register Prediction

When extracting a `[P]` type claim:

```bash
rc-db add prediction --id PRED-2026-001 --claim TECH-2026-042 \
  --status "[P?]" --timeframe "2028" \
  --conditions "Continued scaling, no regulation" \
  --resolution "Published benchmark results"
```

### 2. Update Status

As evidence comes in:

```bash
rc-db update prediction PRED-2026-001 --status "[P→]" \
  --notes "Q1 2027: Intermediate indicators suggest on track"
```

### 3. Resolve

When the timeframe passes:

```bash
rc-db update prediction PRED-2026-001 --status "[P+]" \
  --resolution-date "2028-03-15" \
  --notes "Prediction confirmed: benchmark achieved"
```

## Export Workflow

### Export to YAML (Legacy)

```bash
# Export claims
rc-export yaml claims -o claims.yaml

# Export sources
rc-export yaml sources -o sources.yaml

# Export all
rc-export yaml all -o data/
```

### Export to Markdown

```bash
# Single claim
rc-export md claim --id TECH-2026-001

# Argument chain
rc-export md chain --id CHAIN-2026-001

# All predictions
rc-export md predictions -o predictions.md

# Dashboard summary
rc-export md summary -o dashboard.md
```

## Validation Workflow

### Regular Validation

```bash
# Standard validation
rc-validate

# Strict mode (warnings = errors)
rc-validate --strict

# JSON output for automation
rc-validate --json
```

### What Gets Checked

1. **Schema**: ID formats, field types, value ranges
2. **Referential Integrity**: All references resolve
3. **Logical Consistency**: Chain credences, prediction links
4. **Data Quality**: No empty text, embeddings present

## Bulk Operations

### Add Multiple Claims

Create a YAML file:

```yaml
claims:
  - id: TECH-2026-001
    text: "Claim 1 text"
    type: "[T]"
    domain: TECH
    evidence_level: E2
    credence: 0.75

  - id: TECH-2026-002
    text: "Claim 2 text"
    type: "[H]"
    domain: TECH
    evidence_level: E4
    credence: 0.50
```

Then import:

```bash
rc-db import claims.yaml
```

### Bulk Update

```bash
# Re-embed all claims
rc-embed regenerate

# Update domain for multiple claims
rc-db update-domain VALUE ECON  # Migrates VALUE-* to ECON-*
```

## Integration with Claude Code

### Local Plugin

```bash
# Symlink for development
ln -s /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck
```

### Available Commands

- `/analyze` - Full 3-stage source analysis
- `/extract` - Quick claim extraction
- `/search` - Semantic search
- `/validate` - Data integrity check
- `/export` - Export data

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANALYSIS_DB_PATH` | `data/realitycheck.lance` | Database location |
| `SKIP_EMBEDDING_TESTS` | unset | Skip embedding tests |

## Tips

### Credence Calibration
- Avoid clustering everything at 0.7-0.8
- Use the full range based on evidence
- Chain credence is always ≤ weakest link

### Claim Hygiene
- Always specify operationalization
- Surface hidden assumptions
- Define specific falsifiers

### Efficient Search
- Use domain filters to narrow results
- Combine semantic search with exact ID lookup
- Generate embeddings before searching
