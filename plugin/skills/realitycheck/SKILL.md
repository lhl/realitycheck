---
name: realitycheck
description: Alias for /check - Full Reality Check analysis workflow including fetch, analyze, extract, register, and validate
argument-hint: "<url> [--domain DOMAIN] [--quick] [--no-register]"
allowed-tools: ["WebFetch", "Read", "Write", "Bash(uv run python scripts/db.py *)", "Bash(uv run python scripts/validate.py *)"]
---

# Reality Check - Full Analysis Workflow (Alias)

This is an alias for `/check`. See `/check` for full documentation.

## Quick Reference

The Reality Check workflow:

1. **Fetch** - Retrieve source content via WebFetch
2. **Metadata** - Extract title, author, date, type
3. **Stage 1** - Descriptive analysis (claims, assumptions, terms)
4. **Stage 2** - Evaluative analysis (evidence, coherence, disconfirmation)
5. **Stage 3** - Dialectical analysis (steelman, counterarguments, synthesis)
6. **Extract** - Format claims with IDs, credence, evidence levels
7. **Register** - Add source and claims to database
8. **Validate** - Ensure data integrity
9. **Report** - Generate summary

## Usage

```
/realitycheck <url>
/realitycheck <url> --domain TECH --quick
```

## Arguments

- `url`: URL to analyze
- `--domain`: Primary domain (TECH/LABOR/ECON/GOV/SOC/RESOURCE/TRANS/GEO/INST/RISK/META)
- `--quick`: Skip dialectical analysis
- `--no-register`: Analyze without registering
