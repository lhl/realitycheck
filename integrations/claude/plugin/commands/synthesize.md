---
allowed-tools:
  - "Read"
  - "Write"
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh *)"
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-export.sh *)"
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh *)"
description: Create a cross-source synthesis across multiple source analyses and claims
---

# /reality:synthesize - Cross-Source Synthesis

Create a **cross-source synthesis** across multiple source analyses and existing claims.

Use this after running `/reality:check` on multiple sources (or when relevant source analyses already exist and you want a higher-level conclusion).

## Usage

```
/reality:synthesize <topic>
```

## Output

Write a synthesis document to:
`analysis/syntheses/<synth-id>.md`

The synthesis should link back to relevant source analyses in:
`analysis/sources/<source-id>.md`

## Workflow

1. **Define the question**
   - What is this synthesis trying to answer?
2. **Collect inputs**
   - Prefer existing source analyses in `analysis/sources/`
   - If a relevant source has no analysis yet, run `/reality:check` first (or explicitly record the gap)
3. **Write the synthesis**
   - Open with an `## Assessment` that answers the synthesis question (answer, evidence carrying the most weight, what remains unsettled); metadata follows it
   - Points of agreement (which claims converge?)
   - Points of disagreement (where do they conflict, and why?)
   - Conclusions with calibrated credence + key uncertainties
   - Link claim IDs and source analysis files wherever possible
4. **Claim-Evidence Alignment Pass** (analysis)
   - For each conclusion, ask: could the cited evidence be accurate while this conclusion is materially wrong at its stated scope or credence? Corroboration of an event is not corroboration of its cause; sources sharing an upstream source are not independent.
   - For disputed conclusions, state the strongest alternative and what evidence would distinguish it.
   - For argument chains, the weakest step's credence is a ceiling on the chain, not an estimate of it.
5. **Neutral Analyst Prose Pass** (writing)
   - Apply this pass to the analyst's prose, not source text, direct quotes, titles, quoted slogans, or persuasion/rhetoric examples.
   - For each candidate cut, ask what a careful reader would lose if it disappeared. Keep explanations, qualifications, and distinctions between accounts; cut emphasis-only text, marketing language, hedge stacks, and conclusion recaps.
   - Preserve source wording when it is evidence for rhetoric, framing, or persuasion; label it as source language instead of adopting it as the analyst's voice.
6. **(Optional) Register an argument chain**
   - If the synthesis centers on a specific argument chain, register it and point `--analysis-file` at the synthesis document:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" chain add \
  --id "CHAIN-YYYY-NNN" \
  --name "..." \
  --thesis "..." \
  --claims "TECH-2026-001,ECON-2026-002" \
  --analysis-file "analysis/syntheses/<synth-id>.md"
```

7. **Validate**

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh"
```

8. **Update README**
   - Add a row to the "Syntheses" table (kept above "Source Analyses") in your data repo `README.md`.
9. **Commit and push**
   - If you ran a DB write command (e.g., `chain add`), the plugin hook may auto-commit.
   - Otherwise, commit your `analysis/` + `README.md` changes manually.

## Template

Uses `methodology/templates/synthesis.md`

## Related Commands

- `/reality:check` - Create source analyses first
- `/reality:search` - Find related claims and sources
- `/reality:validate` - Validate database integrity
