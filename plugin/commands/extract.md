# /extract - Claim Extraction

Quick claim extraction from a source without full 3-stage analysis.

## Usage

```
/extract <source>
```

## Arguments

- `source`: URL, file path, or pasted text to extract claims from

## Process

1. Parse the source content
2. Identify extractable claims
3. For each claim:
   - Assign claim ID: `[DOMAIN]-[YYYY]-[NNN]`
   - Determine type: `[F]`/`[T]`/`[H]`/`[P]`/`[A]`/`[C]`/`[S]`/`[X]`
   - Rate evidence level (E1-E6)
   - Assign credence (0.0-1.0)
   - Note operationalization, assumptions, falsifiers
4. Register claims in database
5. Generate embeddings for semantic search
6. Update source backlinks

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

## Template

Uses `methodology/templates/claim-extraction.md`

## Examples

```
/extract https://arxiv.org/abs/2301.xxxxx
/extract "AI will automate 50% of jobs by 2030"
```
