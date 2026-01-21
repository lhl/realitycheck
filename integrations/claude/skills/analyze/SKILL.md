---
name: analyze
description: Perform a full 3-stage analysis of a source following the Reality Check methodology. Use for manual analysis without automatic database registration.
argument-hint: "<url_or_source_id>"
allowed-tools: ["WebFetch", "Read", "Write", "Bash(uv run python scripts/db.py *)"]
---

# Reality Check Source Analysis

Perform a full 3-stage analysis of a source following the Reality Check methodology.

## Usage

Analyze the source at: $ARGUMENTS

## Methodology

### Stage 1: Descriptive Analysis
- Summarize the source neutrally
- Extract key claims, predictions, and assumptions
- Identify theoretical lineage
- Note scope and domain
- Define key terms with operational proxies

### Stage 2: Evaluative Analysis
- Assess internal coherence and logical consistency
- Evaluate evidence quality and empirical grounding
- Identify unstated assumptions and dependencies
- Rate credence levels using the Evidence Hierarchy
- Flag unfalsifiable claims
- Search for disconfirming evidence
- Check for internal tensions/self-contradictions
- Note persuasion techniques used

### Stage 3: Dialectical Analysis
- Steelman the strongest version of the argument
- Identify strongest counterarguments and counterfactuals
- Consider base rates and historical analogs
- Map relationships to other theories
- Map interventions: what would change these claims?
- Synthesize: where does this fit in the broader landscape?

## Evidence Hierarchy

- **E1**: Systematic review, meta-analysis, replicated experiments
- **E2**: Single peer-reviewed study, official data
- **E3**: Expert consensus, working papers
- **E4**: Industry reports, credible journalism
- **E5**: Personal observation, anecdote
- **E6**: Pure speculation, unfalsifiable claims

## Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified, consensus reality |
| Theory | `[T]` | Coherent explanatory framework with support |
| Hypothesis | `[H]` | Testable proposition, awaiting evidence |
| Prediction | `[P]` | Future-oriented claim with conditions |
| Assumption | `[A]` | Unstated premise underlying other claims |
| Counterfactual | `[C]` | Alternative scenario for comparison |
| Speculation | `[S]` | Untestable or unfalsifiable claim |
| Contradiction | `[X]` | Identified logical inconsistency |

## Output

Generate:
1. Analysis document following the 3-stage methodology
2. Extracted claims formatted for database registration

After analysis, register manually with:
```bash
uv run python scripts/db.py source add --id "..." --title "..." ...
uv run python scripts/db.py claim add --text "..." --type "[F]" ...
```

For fully automated analysis + registration, use `/check` instead.
