---
name: realitycheck-validate
description: Validates Reality Check database integrity and referential consistency. Use after making changes or when verifying data quality.
---

# Reality Check - Data Validation

Check database integrity and referential consistency.

## When This Skill Activates

- "Validate the database"
- "Check data integrity"
- "Are there any validation errors?"
- "Run validation"

## Prerequisites

- `realitycheck` package installed (`pip install realitycheck`)
- `REALITYCHECK_DATA` environment variable set

## Usage

```bash
rc-validate
rc-validate --strict
rc-validate --json
```

## Options

| Option | Description |
|--------|-------------|
| `--strict` | Treat warnings as errors |
| `--json` | Output results as JSON |
| `--mode db\|yaml` | Validation mode (default: db) |

## Checks Performed

### Schema Validation
- Claim ID format: `DOMAIN-YYYY-NNN`
- Chain ID format: `CHAIN-YYYY-NNN`
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
- Chain credence ≤ MIN(claim credences)
- All `[P]` claims have prediction records

## Exit Codes

- `0` - All checks pass
- `1` - Errors found
- `2` - Warnings found (with `--strict`)
