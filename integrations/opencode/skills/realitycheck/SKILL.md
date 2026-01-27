---
name: realitycheck
description: Full Reality Check analysis workflow - fetch source, analyze, extract claims, register to database, and validate. The main entry point for rigorous source analysis.
license: Apache-2.0
compatibility: opencode
metadata:
  project: realitycheck
---

# Reality Check - Full Analysis Workflow

This is the main entry point for Reality Check. It performs a complete analysis workflow on a source URL.

## Usage

```
realitycheck <url> [--domain DOMAIN] [--quick] [--no-register]
```

## Workflow

1. **Fetch** - Retrieve source content
2. **Metadata** - Extract title, author, date, type
3. **Stage 1** - Descriptive analysis (claims, assumptions, key terms)
4. **Stage 2** - Evaluative analysis (evidence quality, coherence, disconfirmation search)
5. **Stage 3** - Dialectical analysis (steelman, counterarguments, synthesis)
6. **Extract** - Format claims with IDs, credence, evidence levels
7. **Register** - Add source and claims to database
8. **Validate** - Ensure data integrity
9. **Report** - Generate summary

## Prerequisites

Set `REALITYCHECK_DATA` environment variable:

```bash
export REALITYCHECK_DATA=/path/to/data/realitycheck.lance
```

Install Reality Check CLI tools:

```bash
pip install realitycheck
```

## Arguments

- `url`: URL to analyze
- `--domain`: Primary domain (TECH/LABOR/ECON/GOV/SOC/RESOURCE/TRANS/GEO/INST/RISK/META)
- `--quick`: Skip dialectical analysis (Stage 3)
- `--no-register`: Analyze without registering to database

## Related Skills

- `realitycheck-check` - Full analysis with all options
- `realitycheck-analyze` - Manual 3-stage analysis
- `realitycheck-extract` - Quick claim extraction
- `realitycheck-search` - Search existing claims
- `realitycheck-validate` - Validate database integrity
- `realitycheck-export` - Export data to YAML/Markdown
- `realitycheck-stats` - Show database statistics
- `realitycheck-synthesize` - Cross-source synthesis
