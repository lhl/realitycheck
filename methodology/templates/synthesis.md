# Synthesis Template

Cross-cutting analysis across multiple sources and claims.

---

## Synthesis Metadata

- **Synthesis ID**: `SYNTH-[YYYY]-[NNN]`
- **Topic**:
- **Source Analyses**:
  - [source-id](../sources/source-id.md)
  - ...
- **Claims Referenced**: [list claim IDs]
- **Date**:

---

**Provenance note**: A synthesis should usually be grounded in existing source analyses. If relevant sources exist but no `analysis/sources/...` files are available yet, either create them first (preferred) or explicitly record the gap. In rare cases a synthesis may be based on claim/evidence artifacts without analyzable sources; document that clearly.

## Landscape Overview

### The Question
[What question or topic is this synthesis addressing?]

### Key Positions
[Summarize the major viewpoints on this topic]

| Position | Key Proponents | Core Claim | Credence |
|----------|----------------|------------|----------|
| Position A | [sources] | [central thesis] | 0.XX |
| Position B | [sources] | [central thesis] | 0.XX |
| Position C | [sources] | [central thesis] | 0.XX |

---

## Points of Agreement

[Where do different sources converge?]

| Claim | Sources in Agreement | Credence |
|-------|---------------------|----------|
| [claim text] | [source IDs] | 0.XX |

---

## Points of Disagreement

[Where do sources conflict? Why?]

| Issue | Position A | Position B | Resolution |
|-------|------------|------------|------------|
| [topic] | [claim A] | [claim B] | [which is correct/why they differ] |

### Root Causes of Disagreement

- [ ] Different assumptions (which?)
- [ ] Different evidence (what?)
- [ ] Different definitions (which terms?)
- [ ] Different values (what priorities?)
- [ ] Different time horizons
- [ ] Different scope

---

## Argument Chains

### Chain Analysis

For major argument chains, trace the logic:

#### [Chain Name]
**Thesis**: [final conclusion]
**Credence**: [MIN of step credences]

| Step | Claim | Evidence | Credence | Status |
|------|-------|----------|----------|--------|
| 1 | [premise] | E[1-6] | 0.XX | SOLID/CONTESTED/WEAK |
| 2 | [inference] | E[1-6] | 0.XX | SOLID/CONTESTED/WEAK |
| → | [conclusion] | - | 0.XX | - |

**Weakest Link**: [which step?]
**If Link Breaks**: [what happens to conclusion?]

---

## Base Rates and Precedents

### Historical Analogs

| Analog | Relevance | Similarities | Differences | Lesson |
|--------|-----------|--------------|-------------|--------|
| [event] | [why compare] | [parallels] | [key differences] | [what it suggests] |

### Base Rate Data

| Phenomenon | Historical Rate | Current Claim | Divergence |
|------------|-----------------|---------------|------------|
| [thing being predicted] | [what history shows] | [what sources claim] | [how different] |

---

## Intervention Analysis

### What Would Change These Claims?

| Intervention | Claims Affected | Direction | Mechanism | Feasibility |
|--------------|-----------------|-----------|-----------|-------------|
| [policy/event] | [claim IDs] | ↑/↓ | [how] | Low/Med/High |

### Indicators to Watch

| Indicator | Current Value | Threshold | What It Signals |
|-----------|---------------|-----------|-----------------|
| [metric] | [now] | [trigger level] | [interpretation] |

---

## Synthesis Conclusions

### Summary Assessment
[What's the bottom line? What should we believe given all the evidence?]

### Confidence-Weighted View
[State the synthesized position with calibrated credence]

| Claim | Credence | Key Support | Key Uncertainty |
|-------|----------|-------------|-----------------|
| [synthesized claim 1] | 0.XX | [why believe] | [what could change it] |
| [synthesized claim 2] | 0.XX | [why believe] | [what could change it] |

### Open Questions
[What remains unresolved? What would help resolve it?]

1. [Question 1]: Would be resolved by [type of evidence]
2. [Question 2]: Would be resolved by [type of evidence]

### Predictions from Synthesis
[What predictions follow from this analysis?]

```yaml
predictions:
  - id: "[DOMAIN]-[YYYY]-[NNN]"
    text: "[prediction]"
    type: "[P]"
    conditions: "[trigger conditions]"
    timeframe: "[by when]"
    credence: 0.XX
    resolution_criteria: "[how to judge]"
```

---

## Quick Reference

### Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified, consensus reality |
| Theory | `[T]` | Coherent framework with empirical support |
| Hypothesis | `[H]` | Testable proposition, awaiting evidence |
| Prediction | `[P]` | Future-oriented with specified conditions |
| Assumption | `[A]` | Underlying premise (stated or unstated) |
| Counterfactual | `[C]` | Alternative scenario for comparison |
| Speculation | `[S]` | Unfalsifiable or untestable claim |
| Contradiction | `[X]` | Identified logical inconsistency |

### Evidence Hierarchy

| Level | Strength | Description |
|-------|----------|-------------|
| E1 | Strong Empirical | Replicated studies, systematic reviews, meta-analyses |
| E2 | Moderate Empirical | Single peer-reviewed study, official statistics |
| E3 | Strong Theoretical | Expert consensus, working papers, preprints |
| E4 | Weak Theoretical | Industry reports, credible journalism |
| E5 | Opinion/Forecast | Personal observation, anecdote, expert opinion |
| E6 | Unsupported | Pure speculation, unfalsifiable claims |

---

## Methodology Notes

[Any notes on how this synthesis was conducted, limitations, biases to be aware of]
