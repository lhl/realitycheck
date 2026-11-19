---
name: rc-analyze
description: Perform a full 3-stage analysis following the Reality Check methodology. Use for manual analysis without automatic database registration.
license: Apache-2.0
compatibility: pi
metadata:
  project: realitycheck
---

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

# Manual 3-Stage Analysis

Perform a full 3-stage analysis following the Reality Check methodology. Use for manual analysis without automatic database registration.

## Usage

```
/skill:rc-analyze <url_or_source_id>
```

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

This is a **writing** pass. Run it after the Claim-Evidence Alignment Pass. It
changes how the analysis reads, not what it concludes. If it turns up a claim
that says more than its evidence, or an opening that disagrees with the tables,
return to the alignment pass and fix the analysis first.

Accuracy and the reader's task outrank style. Do not apply a rule below when it
would make the analysis less accurate or harder to use.

**Scope**:
- Applies to the analyst's prose: the opening assessment, summaries, thesis
  statements, evidence assessments, credence reasoning, synthesis notes, and
  recommendations.
- Does not apply to source text, direct quotes, titles, quoted slogans, or
  sections that intentionally analyze rhetoric/persuasion techniques.
- Preserve source wording when it is evidence for rhetoric, framing, or
  persuasion. Label it as source language instead of adopting it as the
  analyst's voice.

### Open with the answer

The opening (`## Assessment`) answers the question the reader brought. For a
substantial analysis it gives:

1. the answer;
2. the evidence that carries the most weight, with the citation or claim ID
   beside the inference it supports;
3. the limitation most likely to change the reader's interpretation. Include a
   coverage or capture gap here only if it could reverse the answer.

The shape depends on the task. These are examples, not required sentence frames:

- **Source analysis**: what the source argues, what holds up, what does not,
  and what was not checked.
- **Quick extraction**: what the source says, and what was not checked. Do not
  imply a verdict the extraction did not reach.
- **Fact-check**: "The evidence establishes X. It does not settle Y, because …"
- **Choice**: "Pick X for this use because … Choose Y instead if …"
- **Explanation**: "X happens because … That explanation applies when …"
- **Unresolved dispute**: "Both accounts fit X. They differ on Y; the available
  evidence cannot distinguish them."
- **Synthesis**: the analyst's assessment across sources, before the landscape,
  chain, and intervention sections.

After the opening, give the argument in the order the reader needs to follow
it. Keep the full record (claim tables, verification rows, captures, search
notes, analysis log) below it for inspection; do not shorten the investigation
to shorten the page. Legends, metadata, workflow names, and capture counts go
after the opening unless they change the answer.

State each qualification once, beside the claim it qualifies. Do not repeat the
same caveat verbatim in several sections; refer back to it by claim ID or
section instead.

### Edit sentences

- State facts, claim IDs, dates, sources, methods, search results, evidence
  levels, credences, falsifiers, and open questions directly.
- For each candidate cut, ask: **what would a careful reader lose if this
  sentence disappeared?** Keep it if they would lose an explanation, an
  inference, a qualification, a comparison, or a route to the evidence. Cut it
  if only emphasis or tone would disappear.
- Use word lists (intensifiers, marketing language, hedge stacks, transition
  scaffolding, "not X but Y" frames, conclusion recaps) to find candidates, not
  to decide. A contrast that separates two things a reader could confuse (an
  event and its cause, a policy and what happened in practice, what a source
  says and whether it is right) is content; keep it. A contrast that argues with
  an imagined objection is filler.
- Replace hedge stacks with the specific unknown, condition, or evidence gap.
  Do not delete a qualifier that bounds a claim's scope.
- Replace vague quantifiers (`many`, `several`, `various`) with counts, IDs,
  bounded scopes, or `unknown`.
- Do not change claim IDs, evidence levels, credences, source-backed facts, or
  quotes unless the analysis records why.

### Check the result

- After reading only the opening, can a reader say what the answer is, why, and
  what remains unsettled?
- Can they reach the supporting evidence (claim IDs, source links, verification
  rows) without reconstructing the investigation?
- Does the opening say the same thing as the claim tables and YAML? If not,
  return to the alignment pass.

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

Or use `/skill:check` for fully automated analysis + registration.

---

## Web Access

This workflow may require web fetch and/or web search. Use whatever web
tools are available in your environment.

If you have **no web tools installed**, fall back to:

```bash
curl -L -sS "URL" | rc-html-extract - --format json
```

We recommend installing one of these pi web packages:

```bash
pi install npm:pi-web-access        # web search + fetch + video, zero-config (most popular)
pi install npm:pi-smart-fetch       # best content extraction, browser-like TLS
pi install npm:@the-forge-flow/camoufox-pi  # stealth browser for bot-protected pages
```

---

## Related Skills

- `/skill:check`
- `/skill:rc-extract`
