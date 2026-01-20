# Claim Taxonomy

Classification system for claims by epistemic status and domain.

## Claim ID Format

```
[DOMAIN]-[YYYY]-[NNN]
```

Example: `TECH-2026-001` = First technology claim registered in 2026

## Epistemic Status Types

| Status | Symbol | Definition |
|--------|--------|------------|
| Fact | `[F]` | Empirically verified, consensus reality |
| Theory | `[T]` | Coherent explanatory framework with some support |
| Hypothesis | `[H]` | Testable proposition, awaiting evidence |
| Prediction | `[P]` | Future-oriented claim with specified conditions |
| Assumption | `[A]` | Unstated or stated premise underlying other claims |
| Counterfactual | `[C]` | Alternative scenario for comparative analysis |
| Speculation | `[S]` | Untestable or unfalsifiable claim |
| Contradiction | `[X]` | Identified logical inconsistency between claims |

### Type Descriptions

**[F] Fact**: Claims that have been empirically verified and represent consensus reality. These have strong evidence (E1-E2) and high credence (0.8+).

**[T] Theory**: Coherent explanatory frameworks with some empirical support. These explain patterns and make predictions but may have contested elements.

**[H] Hypothesis**: Testable propositions awaiting evidence. These are specific enough to be falsified but haven't been tested yet.

**[P] Prediction**: Future-oriented claims with specified conditions and timeframes. Must include trigger conditions and resolution criteria.

**[A] Assumption**: Premises (stated or unstated) that other claims depend on. Surfacing assumptions is critical for chain analysis.

**[C] Counterfactual**: Alternative scenarios used for comparative analysis. "If X had happened instead of Y" claims.

**[S] Speculation**: Claims that are untestable or unfalsifiable. May be interesting but cannot be assigned meaningful credence.

**[X] Contradiction**: Identified logical inconsistencies between claims. These flag where the model breaks down.

## Domain Codes

| Domain | Code | Description |
|--------|------|-------------|
| Labor | LABOR | Employment, automation, human work |
| Economics | ECON | Value theory, pricing, distribution, ownership |
| Governance | GOV | Governance, policy, regulation |
| Technology | TECH | Technology trajectories, capabilities |
| Social | SOC | Social structures, culture, behavior |
| Resource | RESOURCE | Scarcity, abundance, allocation |
| Transition | TRANS | Transition dynamics, pathways |
| Geopolitics | GEO | International relations, state competition |
| Institutional | INST | Institutions, organizations |
| Risk | RISK | Risk assessment, failure modes |
| Meta | META | Claims about the framework/analysis itself |

## Claim Hygiene Requirements

Every claim must include:

### 1. Operationalization
How could this claim be tested? What observable evidence would confirm or refute it?

### 2. Assumptions
What must be true for this claim to hold? What hidden premises does it rely on?

### 3. Falsifiers
What evidence would show this claim is wrong? Be specific about what would update credence downward.

## Example Claim

```yaml
claim:
  id: "TECH-2026-001"
  text: "Frontier AI training costs grow 2-3x annually"
  type: "[F]"
  domain: "TECH"
  evidence_level: "E2"
  credence: 0.80

  # Required fields
  operationalization: "Track published training cost estimates for frontier models year-over-year"
  assumptions:
    - "Current scaling paradigm continues"
    - "No major efficiency breakthroughs"
  falsifiers:
    - "Training costs flat or declining for 2+ years"
    - "New paradigm achieves frontier performance at 10x lower cost"
```

## Prediction Tracking

For `[P]` type claims, track resolution status:

| Status | Symbol | Criteria |
|--------|--------|----------|
| Confirmed | `[P+]` | Prediction occurred as specified |
| Partially Confirmed | `[P~]` | Core thesis correct, details differ |
| On Track | `[P→]` | Intermediate indicators align |
| Uncertain | `[P?]` | Insufficient data to evaluate |
| Off Track | `[P←]` | Intermediate indicators diverge |
| Partially Refuted | `[P!]` | Core thesis problematic, some elements valid |
| Refuted | `[P-]` | Prediction clearly failed |
| Unfalsifiable | `[P∅]` | No possible evidence could refute |
