---
name: rc-synthesize
description: Create a cross-source synthesis across multiple source analyses and claims. Use after checking multiple sources or when producing a higher-level, decision-oriented view.
license: Apache-2.0
compatibility: pi
metadata:
  project: realitycheck
---

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

# Cross-Source Synthesis

Create a cross-source synthesis across multiple source analyses and claims. Use after checking multiple sources or when producing a higher-level, decision-oriented view.

## Usage

```
/skill:rc-synthesize <topic> [source-ids/claim-ids in prompt]
```

Create a **cross-source synthesis** across multiple source analyses and existing claims.

Use this after running `/skill:check` on multiple sources (or when you already have relevant source analyses and want a higher-level conclusion).

Note: For multi-source prompts, `/skill:check` should typically produce the synthesis automatically; `/skill:rc-synthesize` is the standalone/iterative version of that workflow.

## Prerequisites

### Environment

Set `REALITYCHECK_DATA` to point to your data repository:

```bash
export REALITYCHECK_DATA=/path/to/realitycheck-data/data/realitycheck.lance
```

The `PROJECT_ROOT` is derived from this path - all analysis files go there.

### CLI Commands

Reality Check provides CLI tools (`rc-db`, `rc-validate`, `rc-export`, `rc-embed`).

**Check availability:**
```bash
which rc-db  # Should show path if pip-installed
```

**If commands are not found**, either:
1. Install: `pip install realitycheck` (recommended)
2. Use `uv run` from framework directory: `uv run python scripts/db.py ...`
3. Add framework as submodule and use: `.framework/scripts/db.py ...`

### Red Flags: Wrong Repository

**IMPORTANT**: Always write to the DATA repository, never to the framework repository.

If you see these directories, you're in the **framework** repo (wrong place for data):
- `scripts/`
- `tests/`
- `integrations/`
- `methodology/`

Stop and verify `REALITYCHECK_DATA` is set correctly.

### Data Source of Truth

**LanceDB is the source of truth**, not YAML files.

- Query sources: `rc-db source get <id>` or `rc-db source list`
- Query claims: `rc-db claim get <id>` or `rc-db claim list`
- Search: `rc-db search "query"`

**Ignore YAML files** like `claims/registry.yaml` or `reference/sources.yaml` - these are exports/legacy format.

## When to Use

Run synthesis when the task is inherently **multi-source**:
- compare/contrast competing approaches
- reconcile conflicting claims
- summarize the overall state of evidence on a topic
- produce a decision-oriented “what should we believe?” output

## Output Contract

Write a synthesis document to:
`PROJECT_ROOT/analysis/syntheses/<synth-id>.md`

**Required elements**:
1. **Assessment** (first section after the title: the analyst's answer to the synthesis question, the evidence carrying the most weight, and what remains unsettled; metadata goes after it)
2. **Synthesis metadata** (topic, date, synthesis ID)
3. **Claims referenced** (claim IDs)
4. **Source analysis links** for relevant sources (prefer linking `analysis/sources/<source-id>.md`)
5. **Agreement/disagreement** with explanations
6. **Synthesis conclusions** with calibrated credence and key uncertainties

**Corner case**: If you have *claims/evidence but no analyzable sources*, explicitly say so and explain why (e.g., internal notes, private sources, offline materials). Still reference claim IDs and any evidence artifacts available.

## Workflow

1. **Start Tracking** - Begin token usage capture with synthesis attribution
2. **Define the question** - What is this synthesis trying to answer?
3. **Collect inputs**
   - Prefer existing source analyses in `analysis/sources/`
   - If a relevant source has no analysis yet, run `/skill:check` first (or document the gap)
4. **Build a cross-source map**
   - Points of agreement (which claims converge?)
   - Points of disagreement (where do they conflict, and why?)
5. **Write the synthesis**
   - Write the Assessment first: answer the question defined in step 2 before the landscape and chain sections
   - Link each major claim back to source analyses (when available)
   - Resolve conflicts where possible; otherwise record open questions + what would resolve them
6. **Claim-Evidence Alignment Pass** (analysis)
   - Apply the pass below to each synthesized conclusion. Corroboration of an event is not corroboration of its cause; sources that share an upstream source are not independent
   - For disputed conclusions, state the strongest alternative and what would distinguish it
   - Make the Assessment, tables, and any registered chain agree
7. **Neutral Analyst Prose Pass** (writing)
   - Clean up analyst-authored prose without changing source content, quotes, claim IDs, evidence levels, or credences
8. **(Optional) Register an argument chain**
   - Use `rc-db chain add ... --analysis-file "analysis/syntheses/<synth-id>.md" --claims "ID1,ID2,..."` for the central claim chain
   - Chain credence defaults to the minimum step credence, which is a ceiling for a conjunctive chain; pass `--credence` with a lower value when step dependence warrants it
9. **Complete Tracking** - Finalize token usage with synthesis attribution
10. **Update README**
   - Add the synthesis to the "Syntheses" table (kept **above** "Source Analyses")
11. **Commit and push**
   - Commit changes to `analysis/` and `README.md` (and any generated exports), then push

## Claim-Evidence Alignment Pass

Run after the last analysis stage and before the prose pass. Fix conclusions
here; the prose pass must not change them.

For each crux claim and each claim with credence >= 0.7:

1. Ask: **could the cited evidence be accurate while this claim is materially
   wrong at its stated scope or credence?** Uncertainty already reflected in
   the credence does not count.
2. If yes, fix the claim. Split it when parts have different support. Example:
   "layoffs followed the software rollout" (an event the records document) and
   "the rollout caused the layoffs" (a disputed cause). Record the cause as
   `[H]`, or as an attributed fact ("the author attributes the layoffs to the
   rollout"). Otherwise narrow the wording or scope, or change the type,
   evidence level, or credence.
3. Mark `ok` in Key Factual Claims Verified only when the evidence verifies the
   claim as worded. That Status is the claim's only verification status.
4. If the conclusion is disputed, name the strongest alternative and the
   evidence that would tell them apart. Skip this when no alternative would
   change the answer.

Then make every copy of each claim match:

- Key Claims, Claim Summary, and the Claims to Register YAML use the same text,
  type, evidence level, and credence.
- The Assessment or Summary says nothing stronger than those claims.

When revising an existing analysis, correct the claim in all of these places.
An appended update section does not replace the correction.

## Neutral Analyst Prose Pass

Run after the Claim-Evidence Alignment Pass. Change how the analysis reads, not
what it concludes. If you find a claim stronger than its evidence, or an opening
that disagrees with the claim tables, go back to the alignment pass. Accuracy
outranks every style rule below.

Edit only the analyst's prose. Leave source text, direct quotes, titles, and
quoted slogans as written; in rhetoric/persuasion sections, label source
wording as the source's rather than adopting it.

### Opening

Put the opening directly below the title, before legends and metadata.

- **Full analysis or synthesis** (`## Assessment`): the answer to the reader's
  question, the evidence that carries the most weight (with claim IDs), and the
  limitation most likely to change the interpretation. Mention a coverage or
  capture gap only if it could reverse the answer. For an unresolved dispute,
  say why the evidence cannot settle it and name the record that would.
- **Quick extraction** (`## Summary`): what the source says and the most
  important thing the extraction did not check, in one or two sentences. No
  verdict, counterargument, or limitations paragraph.

Fit the opening to the task. Examples, not required wording:

- Fact-check: "The evidence establishes X. It does not settle Y, because …"
- Choice: "Pick X for this use because … Choose Y instead if …"
- Unresolved dispute: "Both accounts fit X. They differ on Y; the available
  evidence cannot distinguish them."

Keep the full record (tables, verification rows, search notes, logs) below the
opening. State each qualification once, beside the claim it qualifies.

### Sentences

- Before cutting a sentence, ask what a careful reader would lose. Keep it if
  they would lose an explanation, inference, qualification, comparison, or link
  to evidence. Cut it if only emphasis or tone would go.
- Word lists (intensifiers, marketing terms, hedge stacks, "not X but Y",
  recaps) find candidates; they do not decide. Keep a contrast that separates
  things a reader could confuse (event vs cause, policy vs practice); cut one
  that argues with an imagined objection.
- Replace hedge stacks with the specific unknown. Replace vague quantifiers
  (`many`, `several`) with counts, IDs, or `unknown`.
- Do not change claim IDs, evidence levels, credences, source-backed facts, or
  quotes.

Check: after reading only the opening, can a reader say what the answer is, why,
and what remains unsettled?

## Token Usage Tracking (Synthesis Mode)

For syntheses, use the lifecycle commands with attribution flags to track which source analyses feed into the synthesis:

```bash
# 1. At workflow START
ANALYSIS_ID=$(rc-db analysis start \
  --source-id "SYNTH-[YYYY]-[NNN]" \
  --tool claude-code \
  --model "claude-sonnet-4" \
  --cmd synthesize)

# 2. At workflow END (after writing synthesis)
# Include --inputs-source-ids and --inputs-analysis-ids for cost attribution
rc-db analysis complete \
  --id "$ANALYSIS_ID" \
  --analysis-file "analysis/syntheses/[synth-id].md" \
  --inputs-source-ids "source-id-1,source-id-2" \
  --inputs-analysis-ids "ANALYSIS-2026-001,ANALYSIS-2026-002" \
  --estimate-cost \
  --notes "Cross-source synthesis"
```

The `inputs_source_ids` and `inputs_analysis_ids` fields enable end-to-end cost tracking: you can trace a synthesis back to its constituent analyses and sum their costs.

## Minimal Template Snippet

```markdown
# Synthesis: [Topic]

## Assessment

[The analyst's answer to the synthesis question, the evidence that carries the most weight (with claim IDs and source-analysis links), and what remains unsettled. Where sources agree on an event but differ on cause or motive, say so and say whether the evidence can distinguish them.]

## Synthesis Metadata

- **Synthesis ID**: `SYNTH-[YYYY]-[NNN]`
- **Topic**: [question or topic]
- **Date**: YYYY-MM-DD
- **Source Analyses**:
  - [source-id](../sources/source-id.md)
  - ...
- **Claims Referenced**: TECH-2026-001, ...
```

---

## Related Skills

- `/skill:check`
- `/skill:rc-search`
- `/skill:rc-validate`
- `/skill:rc-export`
- `/skill:rc-stats`
