# /analyze - Source Analysis

Perform a full 3-stage analysis of a source following the RealityCheck methodology.

## Usage

```
/analyze <url_or_source_id>
```

## Arguments

- `url_or_source_id`: URL to analyze or existing source ID to re-analyze

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

## Output

The analysis will:
1. Guide you through 3-stage methodology
2. Help extract and classify claims with unique IDs
3. Generate an analysis document in `analysis/sources/`

**Phase 2** will add automatic:
- Source record creation in database
- Claim registration and cross-references
- Embedding generation

## Template

Uses `methodology/templates/source-analysis.md`

## Examples

```
/analyze https://example.com/ai-labor-report
/analyze epoch-2024-training
```
