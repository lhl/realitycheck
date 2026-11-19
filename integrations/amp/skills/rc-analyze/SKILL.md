---
name: rc-analyze
description: Perform a full 3-stage analysis following the Reality Check methodology. Use for manual analysis without automatic database registration.
---

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

# Manual 3-Stage Analysis

Perform a full 3-stage analysis following the Reality Check methodology. Use for manual analysis without automatic database registration.

## When This Skill Activates

- "Analyze this source"
- "Do a 3-stage analysis"
- "Manual analysis of"

Perform a full 3-stage analysis following the Reality Check methodology. Use this for manual analysis when you want to review claims before registering them.

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

## Fetching Content

To retrieve and parse source content:
- Primary: `WebFetch` for most URLs
- Alternative: `curl -L -sS "URL" | rc-html-extract - --format json`
- `rc-html-extract` returns structured `{title, published, text, headings, word_count}`

## Methodology

### Stage 1: Descriptive Analysis
- Summarize the source neutrally
- Extract key claims, predictions, and assumptions
- Identify theoretical lineage (what traditions/thinkers it builds on)
- Map argument structure (chain arguments, logical flow)
- Note scope and domain (what does this attempt to explain?)
- Define key terms with operational proxies

### Stage 2: Evaluative Analysis
- Assess internal coherence and logical consistency
- Evaluate evidence quality using Evidence Hierarchy (E1-E6)
- Verify key factual claims (especially crux claims)
- Search for disconfirming evidence (5 min minimum)
- Check for internal tensions/self-contradictions
- Note persuasion techniques and rhetorical devices
- Identify unstated assumptions and dependencies
- Flag unfalsifiable claims

### Stage 3: Dialectical Analysis
- Steelman the strongest version of the argument
- Identify strongest counterarguments and counterfactuals
- Consider base rates and historical analogs
- Map relationships to other theories (supporting/contradicting)
- Synthesize: where does this fit in the broader landscape?

---

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

---

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

---

## Evidence Hierarchy

Use this hierarchy to rate **strength of evidential support** for claims.

| Level | Strength | Description | Credence Range |
|-------|----------|-------------|----------------|
| **E1** | Strong Empirical | Systematic review, meta-analysis, replicated experiments | 0.9-1.0 |
| **E2** | Moderate Empirical | Single peer-reviewed study, official statistics | 0.6-0.8 |
| **E3** | Strong Theoretical | Expert consensus, working papers, preprints | 0.5-0.7 |
| **E4** | Weak Theoretical | Industry reports, credible journalism | 0.3-0.5 |
| **E5** | Opinion/Forecast | Personal observation, anecdote, expert opinion | 0.2-0.4 |
| **E6** | Unsupported | Pure speculation, unfalsifiable claims | 0.0-0.2 |

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

## Output

Generate:
1. Analysis document following the 3-stage methodology
2. Extracted claims formatted for database registration

**Rigor contract (v1)**:
- Claim tables should include `Layer`, `Actor`, `Scope`, and `Quantifier` fields (see `docs/WORKFLOWS.md` → “Analysis Rigor Contract (v1)”).
- Include a `Corrections & Updates` section (including capture failures and recency checks) for auditability.

After analysis, register manually:
```bash
rc-db source add --id "..." --title "..." --type "..." --author "..." --year YYYY --url "..."
rc-db claim add --id "..." --text "..." --type "[F]" --domain "..." --evidence-level "E2" --credence 0.XX --source-ids "..."
```

Or use `$check` for fully automated analysis + registration.

---

## Related Skills

- `check`
- `rc-extract`
