---
description: Perform a full 3-stage analysis of a source following the Reality Check methodology
---

# /reality:analyze - Source Analysis

Perform a full 3-stage analysis of a source following the Reality Check methodology.

## Usage

```
/reality:analyze <url_or_source_id>
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

## Database Registration

After analysis, register sources and claims using the CLI:

```bash
# Register source
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" source add \
  --id "author-year-slug" \
  --title "Title" \
  --type "PAPER" \
  --author "Author Name" \
  --year 2026 \
  --url "https://..."

# Register claims
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" claim add \
  --text "Claim text" \
  --type "[F]" \
  --domain "TECH" \
  --evidence-level "E3" \
  --credence 0.7 \
  --source-ids "source-id"
```

For fully automated analysis + registration, use `/reality:check` instead.

## Template

Uses `methodology/templates/source-analysis.md`

## Examples

```
/reality:analyze https://example.com/ai-labor-report
/reality:analyze epoch-2024-training
```

## Related Commands

- `/reality:check` - Full automated analysis workflow
- `/reality:extract` - Quick claim extraction
- `/reality:search` - Semantic search
- `/reality:stats` - Database statistics
