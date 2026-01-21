# Source Analysis Template

Three-stage methodology for rigorous source analysis.

---

## Source Metadata

- **Source ID**: `[auto-generated]`
- **Title**:
- **Author(s)**:
- **Date**:
- **URL/DOI**:
- **Type**: [paper/book/article/report/video/podcast]

---

## Stage 1: Descriptive Analysis

### Summary
[Summarize the source neutrally in 2-3 paragraphs. What is it claiming? What evidence does it present?]

### Key Claims
[List the main claims made, each on its own line with preliminary type classification]

- [ ] Claim 1 (`[type]`)
- [ ] Claim 2 (`[type]`)
- [ ] ...

### Predictions
[List any explicit or implicit predictions with timeframes]

- [ ] Prediction 1 (by YYYY)
- [ ] Prediction 2 (by YYYY)
- [ ] ...

### Assumptions
[List stated or unstated assumptions the argument depends on]

- [ ] Assumption 1
- [ ] Assumption 2
- [ ] ...

### Theoretical Lineage
[What intellectual traditions does this build on? What thinkers/frameworks does it reference?]

### Scope and Domain
[What phenomena does this attempt to explain? What are the boundaries?]

### Key Terms

| Term | Definition | Operational Proxy | Notes |
|------|------------|-------------------|-------|
| [term] | [meaning in context] | [how to measure] | [ambiguities] |

---

## Stage 2: Evaluative Analysis

### Internal Coherence
[Is the argument logically consistent? Are there self-contradictions?]

- Coherence score: [High/Medium/Low]
- Identified tensions:
  - [ ] ...

### Evidence Quality
[What evidence is provided? Rate using Evidence Hierarchy]

| Claim | Evidence | Level | Notes |
|-------|----------|-------|-------|
| [claim summary] | [evidence provided] | E1-E6 | [quality notes] |

### Unstated Assumptions
[What hidden premises does the argument rely on?]

- [ ] ...

### Unfalsifiable Claims
[Flag claims that cannot be tested]

- [ ] ...

### Disconfirming Evidence
[What evidence contradicts these claims? What did the author miss or dismiss?]

- [ ] ...

### Persuasion Techniques
[Note rhetorical devices, emotional appeals, or logical fallacies]

- [ ] ...

---

## Stage 3: Dialectical Analysis

### Steelman
[Present the strongest version of the argument. What's the best case for this view?]

### Strongest Counterarguments
[What are the best objections? Be specific.]

1. [Counterargument 1]
2. [Counterargument 2]
3. ...

### Counterfactuals
[What alternative scenarios would change the conclusions?]

- If [X], then [Y] instead
- ...

### Base Rates and Historical Analogs

| Analog | Similarities | Differences | What It Suggests |
|--------|--------------|-------------|------------------|
| [event/period] | [parallels] | [key differences] | [implications] |

### Relationship to Other Theories
[How does this relate to other frameworks?]

- Supports: [theories this is consistent with]
- Contradicts: [theories this opposes]
- Extends: [theories this builds on]
- Subsumes: [theories this encompasses]

### Intervention Map
[For policy-relevant claims: what would change them?]

| Intervention | Moves Which Claims? | Mechanism | Feasibility |
|--------------|---------------------|-----------|-------------|
| [policy/action] | [claim IDs] | [how] | Low/Med/High |

### Synthesis
[Where does this fit in the broader theoretical landscape? What's the bottom line?]

---

## Claims to Register

[After analysis, list claims to add to the database]

```yaml
claims:
  - id: "[DOMAIN]-[YYYY]-[NNN]"
    text: ""
    type: "[F/T/H/P/A/C/S/X]"
    domain: ""
    evidence_level: "E1-E6"
    credence: 0.0-1.0
    operationalization: ""
    assumptions: []
    falsifiers: []
    source_ids: ["[this source ID]"]
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

## Analyst Notes

[Any additional observations, questions for follow-up, or methodological notes]
