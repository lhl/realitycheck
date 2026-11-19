---
name: rc-synthesize
description: Create a cross-source synthesis across multiple source analyses and claims. Use after checking multiple sources or when producing a higher-level, decision-oriented view.
argument-hint: "<topic> [source-ids/claim-ids in prompt]"
allowed-tools: ["Read", "Write", "Bash(uv run python scripts/db.py *)", "Bash(rc-db *)", "Bash(uv run python scripts/export.py *)", "Bash(rc-export *)", "Bash(uv run python scripts/validate.py *)", "Bash(rc-validate *)"]
---

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

# /rc-synthesize - Cross-Source Synthesis
Create a cross-source synthesis across multiple source analyses and claims. Use after checking multiple sources or when producing a higher-level, decision-oriented view.

## Usage

```
/rc-synthesize <topic> [source-ids/claim-ids in prompt]
```

Create a **cross-source synthesis** across multiple source analyses and existing claims.

Use this after running `/check` on multiple sources (or when you already have relevant source analyses and want a higher-level conclusion).

Note: For multi-source prompts, `/check` should typically produce the synthesis automatically; `/rc-synthesize` is the standalone/iterative version of that workflow.

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
1. **Synthesis metadata** (topic, date, synthesis ID)
2. **Claims referenced** (claim IDs)
3. **Source analysis links** for relevant sources (prefer linking `analysis/sources/<source-id>.md`)
4. **Agreement/disagreement** with explanations
5. **Synthesis conclusions** with calibrated credence and key uncertainties

**Corner case**: If you have *claims/evidence but no analyzable sources*, explicitly say so and explain why (e.g., internal notes, private sources, offline materials). Still reference claim IDs and any evidence artifacts available.

## Workflow

1. **Start Tracking** - Begin token usage capture with synthesis attribution
2. **Define the question** - What is this synthesis trying to answer?
3. **Collect inputs**
   - Prefer existing source analyses in `analysis/sources/`
   - If a relevant source has no analysis yet, run `/check` first (or document the gap)
4. **Build a cross-source map**
   - Points of agreement (which claims converge?)
   - Points of disagreement (where do they conflict, and why?)
5. **Write the synthesis**
   - Link each major claim back to source analyses (when available)
   - Resolve conflicts where possible; otherwise record open questions + what would resolve them
6. **Claim-Evidence Alignment Pass** (analysis)
   - Check each synthesized conclusion against the evidence it cites: corroboration of an event is not corroboration of its cause; agreement between sources that share an upstream source is not independent
   - For disputed conclusions, state the strongest alternative and what would distinguish it
   - Make the assessment, tables, and any registered chain agree
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

This is an **analysis** pass. Run it after the last analysis stage (Stage 3,
or Stage 2 when `--quick` skips Stage 3) and before the prose pass.
It checks that each claim says no more than its evidence supports, and that
every place the claim appears says the same thing. Clearer prose makes an
unsupported claim more persuasive, so fix the analysis first.

### 1. Test each crux claim as worded

For each crux claim, and each claim with credence >= 0.7, ask:

> Could the cited evidence be accurate and this sentence still be false?

If yes, identify the unsupported part and fix it in the analysis:

- **Split** the claim when it bundles parts with different support. Common
  splits: what happened; what the source or author says caused it or means; what
  the evidence can distinguish between those readings.
- **Narrow** the wording, scope, or quantifier to what the evidence covers.
- **Retype or re-score** the claim when the unsupported part is the point of the
  claim (for example, a causal interpretation stored as `[F]` usually belongs in
  `[H]` or `[T]`, or as an attributed `[F]`: "X attributes Y to Z").

Scope distinctions that apply often:

- A source establishes what its author said. It does not establish that the
  author is right.
- Two reports can corroborate an event without independently corroborating its
  cause or motive. Check whether they share an upstream source.
- A published policy, specification, or promise establishes what was stated. It
  does not establish what happened in a particular case.

### 2. Status applies to the claim as worded

In **Key Factual Claims Verified**, `ok` means the evidence verifies the claim
as worded, at its stated scope. If the evidence supports only part of the claim,
do not mark `ok`. Split the claim and give each part its own status, or record
the supported and unsupported parts in **Search Notes** and choose the status
that fits the unsupported part (`nf` when searched and not established).

### 3. Contested conclusions

When a conclusion is disputed, state the strongest plausible alternative
explanation and the evidence that would distinguish it from the analysis's
reading. If no alternative would change the answer, say so in one line; do not
add a ceremonial counterargument.

### 4. Dependencies and chains

Name the weakest dependency the conclusion relies on and what fails if it
breaks. For a conjunctive chain (every step must hold), the least credible step
is an **upper bound** on the credence that all steps hold, not an estimate of
it. The conclusion may also have support outside this chain. Do not present the
weakest step's credence as the conclusion's credence without saying which of
these applies.

### 5. Consistency across surfaces

Each claim must say the same thing, with the same type, evidence level,
credence, and verification status, everywhere it appears:

- the opening assessment or summary
- the Key Claims table (including `Verified?`)
- the Key Factual Claims Verified table (`Status`)
- the Claim Summary table
- the Claims to Register YAML
- the database record (`rc-db claim get <id>`)

When an update, correction, or `--continue` pass changes a claim, revise every
surface above. An appended update section explains the change; it does not
replace correcting the active claim. Record the change in **Corrections &
Updates** and, for registered claims, update the database row.

The framework's analysis-file validator
(`uv run python scripts/analysis_validator.py <file>`, run from the framework
repo; not part of `rc-validate`) warns when a status code in Key Claims
`Verified?` disagrees with the Stage 2 `Status` for the same claim. No validator
checks whether the wording matches the evidence; that remains the analyst's job.

## Neutral Analyst Prose Pass

Before finalizing an analysis or synthesis, run a short pass over the
analyst-authored prose.

**Scope**:
- Applies to the analyst's prose: summaries, thesis statements, evidence
  assessments, credence reasoning, synthesis notes, and recommendations.
- Does not apply to source text, direct quotes, titles, quoted slogans, or
  sections that intentionally analyze rhetoric/persuasion techniques.
- Preserve source wording when it is evidence for rhetoric, framing, or
  persuasion. Label it as source language instead of adopting it as the
  analyst's voice.

**Rewrite rules**:
- State facts, claim IDs, dates, sources, methods, search results, evidence
  levels, credences, falsifiers, and open questions directly.
- Remove rhetorical setup, marketing language, reassurance frames, vague
  intensifiers, hedge stacks, and conclusion recaps from analyst prose.
- Replace vague quantifiers (`many`, `several`, `various`) with counts, IDs,
  bounded scopes, or `unknown`.
- Do not change claim IDs, evidence levels, credences, source-backed facts, or
  quotes unless the analysis records why.

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

## Related Commands

- `/check`
- `/rc-search`
- `/rc-validate`
- `/rc-export`
- `/rc-stats`

