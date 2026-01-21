---
name: extract
description: Quick claim extraction from a source without full 3-stage analysis. Use for rapid scanning of sources to identify key claims.
argument-hint: "<source>"
allowed-tools: ["WebFetch", "Read", "Write"]
---

# Reality Check Claim Extraction

Quick claim extraction from a source without full 3-stage analysis.

## Usage

Extract claims from: $ARGUMENTS

## Process

1. Parse the source content
2. Identify extractable claims
3. For each claim:
   - Assign claim ID: `[DOMAIN]-[YYYY]-[NNN]`
   - Determine type: `[F]`/`[T]`/`[H]`/`[P]`/`[A]`/`[C]`/`[S]`/`[X]`
   - Rate evidence level (E1-E6)
   - Assign credence (0.0-1.0)
   - Note operationalization, assumptions, falsifiers

## Output Format

```yaml
claims:
  - id: "[DOMAIN]-[YYYY]-[NNN]"
    text: "[Precise claim statement]"
    type: "[F/T/H/P/A/C/S/X]"
    domain: "[DOMAIN]"
    evidence_level: "E[1-6]"
    credence: 0.XX
    operationalization: "[How to test]"
    assumptions: ["..."]
    falsifiers: ["..."]
    source_ids: ["[source-id]"]
```

## Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified, consensus reality |
| Theory | `[T]` | Coherent explanatory framework with support |
| Hypothesis | `[H]` | Testable proposition, awaiting evidence |
| Prediction | `[P]` | Future-oriented claim with conditions |
| Assumption | `[A]` | Unstated premise underlying other claims |
| Counterfactual | `[C]` | Alternative scenario for comparison |
| Speculation | `[S]` | Untestable or unfalsifiable claim |
| Contradiction | `[X]` | Identified logical inconsistency |

Good for:
- Quick scanning of sources
- Extracting obvious claims
- Processing multiple sources rapidly

For full 3-stage analysis, use `/rc-analyze` or `/check`.
