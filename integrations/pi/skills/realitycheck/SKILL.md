---
name: realitycheck
description: Alias for /skill:check - Full Reality Check analysis workflow including fetch, analyze, extract, register, and validate. The main entry point for rigorous source analysis.
license: Apache-2.0
compatibility: pi
metadata:
  project: realitycheck
---

# Reality Check (Pi)

This is an alias for `/skill:check`. Use it as the main entry point into Reality
Check's full analysis workflow, or for utility commands (stats, search, validate,
export).

## Quick Reference

```
/skill:realitycheck <url>       # Full analysis workflow
/skill:check <url>              # Same thing (canonical name)
/skill:rc-stats                 # Database statistics
/skill:rc-search "query"        # Semantic search
/skill:rc-validate              # Data integrity check
```

## Workflow

1. **Fetch** - Retrieve source content via available web tools
2. **Metadata** - Extract title, author, date, type
3. **Stage 1** - Descriptive analysis (claims, assumptions, terms)
4. **Stage 2** - Evaluative analysis (evidence, coherence, disconfirmation)
5. **Stage 3** - Dialectical analysis (steelman, counterarguments, synthesis)
6. **Extract** - Format claims with IDs, credence, evidence levels
7. **Register** - Add source and claims to database
8. **Validate** - Ensure data integrity
9. **Report** - Generate summary

## Prerequisites

Set `REALITYCHECK_DATA`:

```bash
export REALITYCHECK_DATA=/path/to/data/realitycheck.lance
```

Install CLI tools:

```bash
pip install realitycheck
```

## Web Access

Use whatever web tools are available in your environment. If none installed:

```bash
curl -L -sS "URL" | rc-html-extract - --format json
```

We recommend:

```bash
pi install npm:pi-web-access        # web search + fetch + video (most popular)
pi install npm:pi-smart-fetch       # best content extraction
pi install npm:@the-forge-flow/camoufox-pi  # stealth browser
```

## Related Skills

- `/skill:check` - Full analysis with all options
- `/skill:rc-analyze` - Manual 3-stage analysis
- `/skill:rc-extract` - Quick claim extraction
- `/skill:rc-search` - Find related claims
- `/skill:rc-validate` - Check database integrity
- `/skill:rc-export` - Export data to YAML/Markdown
- `/skill:rc-stats` - Show database statistics
- `/skill:rc-synthesize` - Cross-source synthesis