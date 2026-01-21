---
name: check
description: Full Reality Check analysis workflow - fetch source, perform 3-stage analysis, extract claims, register to database, and validate. The flagship command for rigorous source analysis.
argument-hint: "<url> [--domain DOMAIN] [--quick] [--no-register]"
allowed-tools: ["WebFetch", "Read", "Write", "Bash(uv run python scripts/db.py *)", "Bash(uv run python scripts/validate.py *)"]
---

# Reality Check - Full Analysis Workflow

The flagship Reality Check command for rigorous source analysis.

## Usage

Analyze the source: $ARGUMENTS

## Arguments

- `url`: URL of the source to analyze
- `--domain`: Primary domain for claims (TECH/LABOR/ECON/GOV/etc.)
- `--quick`: Skip Stage 3 (dialectical analysis) for faster processing
- `--no-register`: Analyze without registering to database

## Workflow

This command orchestrates the full Reality Check analysis pipeline:

### Step 1: Fetch Source

Use `WebFetch` to retrieve the source content.

### Step 2: Source Metadata

Extract and confirm source metadata:

| Field | Value |
|-------|-------|
| **Title** | [extracted from page] |
| **Author** | [extracted or "Unknown"] |
| **Date** | [publication date if available] |
| **Type** | [PAPER/ARTICLE/BLOG/REPORT/etc.] |
| **Source ID** | [auto-generated: author-year-slug] |

### Step 3: Three-Stage Analysis

Perform the Reality Check 3-stage methodology:

#### Stage 1: Descriptive Analysis

1. **Summary**: Neutral 2-3 paragraph summary of the source
2. **Key Claims**: List all claims with preliminary type classification
3. **Predictions**: Any explicit or implicit predictions with timeframes
4. **Assumptions**: Stated and unstated premises
5. **Key Terms**: Define ambiguous terms with operational proxies

#### Stage 2: Evaluative Analysis

1. **Internal Coherence**: Check for logical consistency
2. **Evidence Quality**: Rate using Evidence Hierarchy (E1-E6)
3. **Unfalsifiable Claims**: Flag untestable claims
4. **Disconfirming Evidence**: Actively search for contradictions
5. **Persuasion Techniques**: Note rhetorical devices

**Evidence Hierarchy Reference:**
- **E1**: Systematic review, meta-analysis, replicated experiments
- **E2**: Single peer-reviewed study, official data
- **E3**: Expert consensus, working papers
- **E4**: Industry reports, credible journalism
- **E5**: Personal observation, anecdote
- **E6**: Pure speculation, unfalsifiable claims

#### Stage 3: Dialectical Analysis

1. **Steelman**: Present the strongest version
2. **Counterarguments**: Best objections
3. **Base Rates**: Historical analogs
4. **Synthesis**: Where does this fit?

### Step 4: Extract Claims

Format claims for database registration:

```yaml
claims:
  - id: "[DOMAIN]-[YYYY]-[NNN]"
    text: "[Precise claim statement]"
    type: "[F/T/H/P/A/C/S/X]"
    domain: "[DOMAIN]"
    evidence_level: "E[1-6]"
    credence: 0.XX
    operationalization: "[How to test]"
    assumptions: ["..."]
    falsifiers: ["..."]
    source_ids: ["[source-id]"]
```

**Claim Types:**
- `[F]` Fact: Empirically verified
- `[T]` Theory: Explanatory framework
- `[H]` Hypothesis: Testable, awaiting evidence
- `[P]` Prediction: Future-oriented with conditions
- `[A]` Assumption: Underlying premise
- `[C]` Counterfactual: Alternative scenario
- `[S]` Speculation: Unfalsifiable
- `[X]` Contradiction: Logical inconsistency

### Step 5: Register in Database

Use the CLI to register the source and claims:

```bash
# Register source
uv run python scripts/db.py source add \
  --id "SOURCE_ID" \
  --title "TITLE" \
  --type "TYPE" \
  --author "AUTHOR" \
  --year YEAR \
  --url "URL"

# Register each claim
uv run python scripts/db.py claim add \
  --id "CLAIM_ID" \
  --text "CLAIM_TEXT" \
  --type "[TYPE]" \
  --domain "DOMAIN" \
  --evidence-level "EX" \
  --credence 0.XX \
  --source-ids "SOURCE_ID"
```

### Step 6: Validation

Run validation to ensure data integrity:

```bash
uv run python scripts/validate.py
```

### Step 7: Update Data Project README

After completing the analysis, update the data project's `README.md` analysis index:

1. **Add to Source Analyses table**: Insert a new row **at the top** of the table (reverse chronological order - newest first):

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

2. **Stats are auto-generated**: The counts table at the top will be updated by the auto-commit hook (if running in plugin mode) or manually via `update-readme-stats.sh`.

### Step 8: Summary Report

Generate a summary report:

```
## Analysis Summary

**Source**: [title] ([source-id])
**Claims Extracted**: X
**Domains**: [list]

### Claim Summary

| ID | Type | Credence | Evidence |
|----|------|----------|----------|
| ... | ... | ... | ... |

### Key Findings
- [Most significant insight]
- [Notable assumption or gap]
- [Relationship to existing claims]

### Validation Status
✓ All claims registered
✓ Source linked
✓ Embeddings generated
✓ README index updated
```

## Requirements

- Database must be initialized (`uv run python scripts/db.py init`)
- For URL sources: internet access for WebFetch
- For best results: provide `--domain` hint

## Examples

```
/check https://arxiv.org/abs/2024.12345
/check https://example.com/ai-report --domain TECH
/check https://blog.example.com/post --domain ECON --quick
```

## Related Commands

- `/rc-analyze` - Manual 3-stage analysis without database registration
- `/rc-extract` - Quick claim extraction without full analysis
- `/rc-search` - Find related claims in database
- `/rc-validate` - Check database integrity
- `/rc-stats` - Show database statistics
