---
name: validate
description: Check Reality Check database integrity and referential consistency. Use when verifying data quality or after making changes.
argument-hint: "[--strict] [--json]"
allowed-tools: ["Bash(uv run python scripts/validate.py *)"]
---

# Reality Check Data Validation

Check database integrity and referential consistency.

## Usage

```!
uv run python scripts/validate.py $ARGUMENTS
```

## Options

- `--strict`: Treat warnings as errors
- `--json`: Output results as JSON
- `--mode {db,yaml}`: Validation mode (default: db)

## Checks Performed

### Schema Validation
- Claim ID format: `[DOMAIN]-[YYYY]-[NNN]`
- Chain ID format: `CHAIN-[YYYY]-[NNN]`
- Valid claim types: `[F]`/`[T]`/`[H]`/`[P]`/`[A]`/`[C]`/`[S]`/`[X]`
- Valid evidence levels: E1-E6
- Credence in range [0.0, 1.0]

### Referential Integrity
- Claims reference existing sources
- Sources list extracted claims (backlinks)
- Chains reference existing claims
- Predictions reference existing claims

### Logical Consistency
- Domain in ID matches domain field
- Chain credence <= MIN(claim credences)
- All `[P]` claims have prediction records
