---
name: realitycheck-check
description: Performs full Reality Check source analysis - fetches URL, runs 3-stage analysis (descriptive/evaluative/dialectical), extracts claims with evidence levels and credence, registers to database, validates. Use when asked to analyze a source, article, or URL for claims.
---

# Reality Check - Full Analysis Workflow

Rigorous source analysis through structured 3-stage methodology.

## When This Skill Activates

- "Analyze this article for claims"
- "Reality check this URL"
- "Extract and evaluate claims from [source]"
- "Run a check on [URL]"

## Prerequisites

1. **Install realitycheck**: `pip install realitycheck`
2. **Set data path**: `export REALITYCHECK_DATA=/path/to/data/realitycheck.lance`

If `REALITYCHECK_DATA` is not set, prompt the user to set it.

## Core Methodology

See `methodology/workflows/check-core.md` for full details. The analysis must include:

1. **Claim tables** with evidence levels (E1-E6) and credence (0.0-1.0)
2. **Three-stage analysis** (descriptive → evaluative → dialectical)
3. **Extracted claims** in YAML format for registration

## Workflow

1. **Fetch** - Retrieve source content (`read_web_page` or `curl`)
2. **Metadata** - Extract title, author, date, type; generate source-id
3. **Stage 1: Descriptive** - Neutral summary, key claims, assumptions, terms
4. **Stage 2: Evaluative** - Evidence quality, coherence, unfalsifiable claims
5. **Stage 3: Dialectical** - Steelman, counterarguments, synthesis
6. **Extract** - Format claims with IDs, credence, evidence levels
7. **Register** - Add source and claims to database
8. **Validate** - Run integrity checks
9. **Update README** - Add to data project analysis index
10. **Report** - Generate summary

## Evidence Hierarchy

| Level | Description | Credence Range |
|-------|-------------|----------------|
| E1 | Systematic review, meta-analysis | 0.9-1.0 |
| E2 | Peer-reviewed study, official stats | 0.6-0.8 |
| E3 | Expert consensus, preprints | 0.5-0.7 |
| E4 | Industry reports, journalism | 0.3-0.5 |
| E5 | Opinion, anecdote | 0.2-0.4 |
| E6 | Speculation, unfalsifiable | 0.0-0.2 |

## Claim Types

| Symbol | Type | Definition |
|--------|------|------------|
| `[F]` | Fact | Empirically verified |
| `[T]` | Theory | Explanatory framework with support |
| `[H]` | Hypothesis | Testable, awaiting evidence |
| `[P]` | Prediction | Future-oriented with conditions |
| `[A]` | Assumption | Underlying premise |
| `[C]` | Counterfactual | Alternative scenario |
| `[S]` | Speculation | Unfalsifiable |
| `[X]` | Contradiction | Logical inconsistency |

## Database Commands

```bash
# Register source
rc-db source add \
  --id "author-2026-title" \
  --title "Title" \
  --type "ARTICLE" \
  --author "Author" \
  --year 2026 \
  --url "https://..."

# Register claims
rc-db claim add \
  --text "Claim text" \
  --type "[T]" \
  --domain "TECH" \
  --evidence-level "E3" \
  --credence 0.65 \
  --source-ids "author-2026-title"

# Validate
rc-validate
```

## Output Location

**Critical**: Write to the DATA repository, not the framework repository.

Derive `PROJECT_ROOT` from `REALITYCHECK_DATA`:
- If path ends with `.lance/`: `PROJECT_ROOT = parent.parent`
- Otherwise: `PROJECT_ROOT = parent`

Analysis file: `PROJECT_ROOT/analysis/sources/<source-id>.md`

## Required Output

Every analysis must include:

### Key Claims Table

| # | Claim | ID | Type | Evidence | Credence |
|---|-------|-----|------|----------|----------|
| 1 | ... | DOMAIN-YYYY-NNN | [T] | E3 | 0.65 |

### Claim Summary Table

| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| DOMAIN-YYYY-NNN | [T] | DOMAIN | E3 | 0.65 | ... |

## Version Control

After registration:
```bash
cd $PROJECT_ROOT
git add data/ analysis/ tracking/ README.md
git commit -m "data: add source(s)"
```

## Related Skills

- `realitycheck-search` - Find related claims
- `realitycheck-validate` - Check database integrity
- `realitycheck-stats` - Database statistics
- `realitycheck-export` - Export data
