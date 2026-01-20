# /realitycheck - Full Analysis Workflow (Alias)

Alias for `/check`. Runs the full RealityCheck analysis pipeline.

## Usage

```
/realitycheck <url>
/realitycheck <url> --domain TECH --quick
```

This command is identical to `/check`. See `/check` documentation for full details.

## Quick Reference

The RealityCheck workflow:

1. **Fetch** - Retrieve source content via WebFetch
2. **Metadata** - Extract title, author, date, type
3. **Stage 1** - Descriptive analysis (claims, assumptions, terms)
4. **Stage 2** - Evaluative analysis (evidence, coherence, disconfirmation)
5. **Stage 3** - Dialectical analysis (steelman, counterarguments, synthesis)
6. **Extract** - Format claims with IDs, credence, evidence levels
7. **Register** - Add source and claims to database
8. **Validate** - Ensure data integrity
9. **Report** - Generate summary

## Arguments

- `url`: URL to analyze
- `--domain`: Primary domain (TECH/LABOR/ECON/GOV/SOC/RESOURCE/TRANS/GEO/INST/RISK/META)
- `--quick`: Skip dialectical analysis
- `--no-register`: Analyze without registering

## Examples

```
/realitycheck https://example.com/ai-paper
/realitycheck https://blog.example.com/post --domain ECON
```

## See Also

- `/check` - Primary command (this is an alias)
- `/analyze` - Manual analysis without database
- `/extract` - Quick claim extraction
