# Reality Check - Core Analysis Workflow

This document defines the shared methodology for the `/check` (Claude) and `$check` (Codex) workflows. Tool-specific wrappers reference this core methodology.

## Critical: Data Repository vs Framework Repository

**Always write analysis data to the DATA repository, never to the framework repository.**

- **Framework repo** (`realitycheck`): Contains code, scripts, tests, methodology, integrations. NO data.
- **Data repo** (e.g., `realitycheck-data`): Contains your knowledge base - `data/`, `analysis/`, `tracking/`, claims, sources.

The `REALITYCHECK_DATA` environment variable points to your data repo's database. Derive `PROJECT_ROOT` from this path - that's where all analysis files go.

**Red flags you're in the wrong repo**: If you see `scripts/`, `tests/`, `integrations/`, `methodology/` directories, you're in the framework repo. Stop and check `REALITYCHECK_DATA`.

## Data Sources

**LanceDB is the source of truth**, not YAML files.

- Query sources: `rc-db source get <id>` or `rc-db source list`
- Query claims: `rc-db claim get <id>` or `rc-db claim list`
- Search: `rc-db search "query"`

**Ignore YAML files** like `claims/registry.yaml` or `reference/sources.yaml` - these are exports/legacy format, not the live registry.

**Analysis files may not exist** for every source. If `analysis/sources/<id>.md` doesn't exist, create it.

---

## Overview

The Reality Check analysis workflow performs rigorous source analysis through a structured pipeline:

1. Fetch source content
2. Extract source metadata
3. Three-stage analysis (descriptive → evaluative → dialectical)
4. Extract and classify claims
5. Register source and claims to database
6. Validate data integrity
7. Update data project README
8. Generate summary report

---

## Source Metadata

Extract and confirm source metadata before analysis:

| Field | Value |
|-------|-------|
| **Title** | [extracted from page] |
| **Author** | [extracted or "Unknown"] |
| **Date** | [publication date if available] |
| **Type** | [PAPER/ARTICLE/BLOG/REPORT/etc.] |
| **Source ID** | [auto-generated: author-year-slug] |

---

## Three-Stage Analysis

### Stage 1: Descriptive Analysis

Neutral extraction of content without judgment:

1. **Summary**: Neutral 2-3 paragraph summary of the source
2. **Key Claims**: List all claims with preliminary type classification
3. **Predictions**: Any explicit or implicit predictions with timeframes
4. **Assumptions**: Stated and unstated premises
5. **Key Terms**: Define ambiguous terms with operational proxies

### Stage 2: Evaluative Analysis

Critical assessment of claims and evidence:

1. **Internal Coherence**: Check for logical consistency
2. **Evidence Quality**: Rate using Evidence Hierarchy (E1-E6)
3. **Unfalsifiable Claims**: Flag untestable claims
4. **Disconfirming Evidence**: Actively search for contradictions
5. **Persuasion Techniques**: Note rhetorical devices

### Stage 3: Dialectical Analysis

Synthesis and contextualization:

1. **Steelman**: Present the strongest version of the argument
2. **Counterarguments**: Best objections from opposing viewpoints
3. **Base Rates**: Historical analogs and reference classes
4. **Synthesis**: Where does this fit in the broader discourse?

---

## Evidence Hierarchy

| Level | Strength | Description | Credence Range |
|-------|----------|-------------|----------------|
| **E1** | Strong Empirical | Systematic review, meta-analysis, replicated experiments | 0.9-1.0 |
| **E2** | Moderate Empirical | Single peer-reviewed study, official statistics | 0.6-0.8 |
| **E3** | Strong Theoretical | Expert consensus, working papers, preprints | 0.5-0.7 |
| **E4** | Weak Theoretical | Industry reports, credible journalism | 0.3-0.5 |
| **E5** | Opinion/Forecast | Personal observation, anecdote, expert opinion | 0.2-0.4 |
| **E6** | Unsupported | Pure speculation, unfalsifiable claims | 0.0-0.2 |

---

## Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified, consensus reality |
| Theory | `[T]` | Coherent explanatory framework with empirical support |
| Hypothesis | `[H]` | Testable proposition, awaiting evidence |
| Prediction | `[P]` | Future-oriented claim with specified conditions |
| Assumption | `[A]` | Underlying premise (stated or unstated) |
| Counterfactual | `[C]` | Alternative scenario for comparison |
| Speculation | `[S]` | Unfalsifiable or untestable claim |
| Contradiction | `[X]` | Identified logical inconsistency |

---

## Claim Extraction Format

Format claims for database registration:

```yaml
claims:
  - id: "[DOMAIN]-[YYYY]-[NNN]"
    text: "[Precise claim statement]"
    type: "[F/T/H/P/A/C/S/X]"
    domain: "[DOMAIN]"
    evidence_level: "E[1-6]"
    credence: 0.XX
    operationalization: "[How to test/measure this claim]"
    assumptions: ["..."]
    falsifiers: ["What would refute this"]
    source_ids: ["[source-id]"]
```

### Domain Codes

| Code | Description |
|------|-------------|
| TECH | Technology, AI capabilities, tech trajectories |
| LABOR | Employment, automation, human work |
| ECON | Value theory, pricing, distribution, ownership |
| GOV | Governance, policy, regulation |
| SOC | Social structures, culture, behavior |
| RESOURCE | Scarcity, abundance, allocation |
| TRANS | Transition dynamics, pathways |
| GEO | International relations, state competition |
| INST | Institutions, organizations |
| RISK | Risk assessment, failure modes |
| META | Claims about the framework/analysis itself |

---

## Updating the Data Project README

After completing an analysis, update the data project's `README.md` analysis index:

1. **Add to Source Analyses table**: Insert a new row **at the top** of the table (reverse chronological order - newest first):

```markdown
| Date | Document | Status | Summary |
|------|----------|--------|---------|
| YYYY-MM-DD | [Author "Title"](analysis/sources/source-id.md) | `[REVIEWED]` | Brief 1-line summary |  <- INSERT HERE (top of table)
| ... existing rows below ... |
```

**Status values:**
- `[REVIEWED]` - Analysis complete, claims extracted and registered
- `[DRAFT]` - In progress
- `[PENDING]` - Awaiting analysis

2. **Stats table**: The counts table at the top is auto-generated (via hooks or `update-readme-stats.sh`).

---

## Summary Report Format

Generate a summary report after completing the workflow:

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
- All claims registered
- Source linked
- Embeddings generated
- README index updated
```

---

## Continuation Mode

When continuing an existing analysis (rather than starting fresh):

1. **Find existing analysis**: Look for `analysis/sources/[source-id].md`
2. **Read current state**: Load the existing analysis and registered claims
3. **Iterate, don't overwrite**: Add to the existing analysis rather than replacing it
4. **Focus areas**:
   - Extract claims that were skipped or noted as "TODO"
   - Deepen specific sections (more counterfactuals, stronger steelman)
   - Add evidence that was found after initial analysis
   - Address questions or gaps identified in the original pass
   - Cross-reference with newly added claims in the database

**Important**: Preserve all existing content. Append new sections, update claim counts, and note what was added in this pass.
