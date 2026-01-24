---
description: Quick claim extraction from a source without full 3-stage analysis
---

# /reality:extract - Claim Extraction

Quick claim extraction from a source without full 3-stage analysis.

## Usage

```
/reality:extract <source>
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

## Registering Claims

After extraction, register claims using the CLI:

```bash
# Via shell wrapper
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" claim add \
  --id "DOMAIN-YYYY-NNN" \
  --text "Claim text" \
  --type "[F]" \
  --domain "TECH" \
  --evidence-level "E3" \
  --credence 0.7 \
  --source-ids "source-id"

# Or directly
uv run python scripts/db.py claim add [OPTIONS]
```

See `/reality:check` for fully automated analysis + registration workflow.

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
/reality:extract https://arxiv.org/abs/2301.xxxxx
/reality:extract "AI will automate 50% of jobs by 2030"
```

## Related Commands

- `/reality:check` - Full automated analysis workflow
- `/reality:analyze` - Full 3-stage analysis
- `/reality:search` - Semantic search
- `/reality:stats` - Database statistics
