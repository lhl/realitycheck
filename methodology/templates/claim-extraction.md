# Claim Extraction Template

Quick claim extraction without full 3-stage analysis.

---

## Source

- **Input**: [URL, file path, or pasted text]
- **Type**: [paper/article/quote/video/etc.]

---

## Extraction Process

### 1. Identify Claims

Read the source and identify statements that:
- Assert something about reality (facts, theories)
- Make predictions about the future
- State assumptions underlying other claims
- Identify contradictions

List each potential claim:

| # | Raw Text | Notes |
|---|----------|-------|
| 1 | "[exact quote or paraphrase]" | [context, caveats] |
| 2 | ... | ... |

### 2. Classify Each Claim

For each identified claim, determine:

**Type Classification**:
- `[F]` Fact - empirically verified
- `[T]` Theory - explanatory framework with support
- `[H]` Hypothesis - testable, awaiting evidence
- `[P]` Prediction - future-oriented with conditions
- `[A]` Assumption - premise underlying other claims
- `[C]` Counterfactual - alternative scenario
- `[S]` Speculation - untestable/unfalsifiable
- `[X]` Contradiction - logical inconsistency

**Domain**:
LABOR, ECON, GOV, TECH, SOC, RESOURCE, TRANS, GEO, INST, RISK, META

**Evidence Level** (see evidence-hierarchy.md):
E1 (strong empirical) through E6 (unsupported)

### 3. Assign Credence

Rate credence 0.0-1.0 based on:
- Evidence quality
- Source reliability
- Logical coherence
- Consistency with other claims

### 4. Document Requirements

For each claim, specify:

**Operationalization**: How could this be tested?
**Assumptions**: What must be true for this to hold?
**Falsifiers**: What evidence would refute this?

---

## Claims Output

```yaml
claims:
  - id: "[DOMAIN]-[YYYY]-[NNN]"
    text: "[claim text]"
    type: "[F/T/H/P/A/C/S/X]"
    domain: "[DOMAIN]"
    evidence_level: "E[1-6]"
    credence: 0.XX
    operationalization: "[how to test]"
    assumptions:
      - "[assumption 1]"
      - "[assumption 2]"
    falsifiers:
      - "[what would refute]"
    source_ids:
      - "[source ID]"
    related_ids: []
```

---

## Extraction Checklist

- [ ] All claims identified
- [ ] Types assigned correctly
- [ ] Domains match claim content
- [ ] Evidence levels justified
- [ ] Credence calibrated (not all 0.8!)
- [ ] Operationalization is specific
- [ ] Assumptions surfaced
- [ ] Falsifiers identified
- [ ] Source backlinks added

---

## Common Pitfalls

1. **Over-extraction**: Not every statement is a claim. Focus on substantive assertions.

2. **Under-specification**: Vague claims are hard to evaluate. Make them specific.

3. **Credence clustering**: Avoid defaulting to 0.7-0.8 for everything. Calibrate carefully.

4. **Missing assumptions**: The most important assumptions are often unstated.

5. **Weak falsifiers**: "More evidence to the contrary" is not a good falsifier. Be specific.

6. **Type confusion**:
   - `[T]` vs `[H]`: Theories explain, hypotheses predict
   - `[P]` vs `[H]`: Predictions have timeframes
   - `[A]` vs `[T]`: Assumptions are premises, not conclusions
