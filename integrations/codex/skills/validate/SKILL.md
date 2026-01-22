---
name: validate
description: "Validate Reality Check database integrity and referential consistency. Run after adding data or before committing."
---

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

# Data Validation (Codex)

Validate Reality Check database integrity and referential consistency. Run after adding data or before committing.

## Invocation

```
$validate
```

Note: Codex reserves `/...` for built-in commands. Use `$validate` instead.

Validate Reality Check database integrity and referential consistency.

## Usage

```bash
rc-validate
# or: uv run python scripts/validate.py
```

## Options

- `--strict`: Fail on warnings (not just errors)
- `--json`: Output results as JSON
- `--fix`: Attempt to auto-fix simple issues (use with caution)

## Checks Performed

1. **Schema validation** - All records match expected schema
2. **ID format** - Claim IDs match `DOMAIN-YYYY-NNN` format
3. **Referential integrity** - All source_ids point to existing sources
4. **Embedding completeness** - All records have vector embeddings
5. **Required fields** - No missing required fields
6. **Duplicate detection** - No duplicate IDs

## Output

```
Validation Results:
- Claims: 42 checked, 0 errors, 1 warning
- Sources: 15 checked, 0 errors, 0 warnings
- Chains: 3 checked, 0 errors, 0 warnings
- Predictions: 8 checked, 0 errors, 0 warnings

Status: OK (1 warning)
```

## When to Run

- After adding new claims/sources
- Before committing data changes
- As part of CI/CD pipeline
- When debugging data issues

---

## Related Skills

- `$check`
- `$stats`
