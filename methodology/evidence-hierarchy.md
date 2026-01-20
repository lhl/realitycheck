# Evidence Hierarchy

A 6-level scale for rating evidence quality and assigning credence.

## Levels

| Level | Strength | Description | Credence Range |
|-------|----------|-------------|----------------|
| E1 | Strong Empirical | Replicated studies, historical data, verified measurements | 0.9-1.0 |
| E2 | Moderate Empirical | Single studies, case studies, natural experiments | 0.6-0.8 |
| E3 | Strong Theoretical | Logical derivation from well-established principles | 0.5-0.7 |
| E4 | Weak Theoretical | Plausible reasoning, extrapolation from trends | 0.3-0.5 |
| E5 | Opinion/Forecast | Credentialed speculation, informed forecasts | 0.2-0.4 |
| E6 | Unsupported | Unfounded claims, assertions without evidence | 0.0-0.2 |

## Usage Guidelines

### E1: Strong Empirical
- Multiple independent replications
- Large sample sizes
- Pre-registered methodology
- Peer review and meta-analysis

**Examples**: Well-established physical constants, replicated psychology findings, census data

### E2: Moderate Empirical
- Single peer-reviewed study
- Case study with documentation
- Natural experiments
- Survey data with reasonable methodology

**Examples**: New empirical findings, case studies, industry reports with data

### E3: Strong Theoretical
- Derivation from established principles
- Logical necessity given premises
- Mathematical proof (given axioms)

**Examples**: Economic models from first principles, game-theoretic predictions

### E4: Weak Theoretical
- Plausible but untested reasoning
- Extrapolation from observed trends
- Analogical reasoning

**Examples**: Trend extrapolations, "if X then probably Y" reasoning

### E5: Opinion/Forecast
- Expert forecasts
- Credentialed speculation
- Delphi method results

**Examples**: Economist predictions, technology forecasts, expert interviews

### E6: Unsupported
- No evidence provided
- Pure assertion
- Contradicted by available evidence

**Examples**: Unfounded claims, rhetoric without backing, contradicted assertions

## Credence Calibration

| Range | Interpretation |
|-------|----------------|
| 0.9-1.0 | Would bet significant resources; very strong evidence |
| 0.7-0.8 | Confident but acknowledge meaningful uncertainty |
| 0.5-0.6 | Genuine uncertainty; could go either way |
| 0.3-0.4 | Lean against but not confident |
| 0.1-0.2 | Strongly doubt but can't rule out |
| 0.0-0.1 | Would bet heavily against; extraordinary evidence needed |

## Chain Scoring Rule

> **Chain credence = MIN(step credences)**
>
> Rationale: Weakest link dominates; avoids fake precision.

A theory with many 0.7 credence claims is not itself 0.7 credence. Chain arguments have credence ≤ weakest link.
