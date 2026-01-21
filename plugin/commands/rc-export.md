# /rc-export - Data Export

Export data to Markdown or YAML formats.

---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-export.sh *)"]
---

## Usage

```
/rc-export <format> <type> [--id ID] [-o OUTPUT]
```

## CLI Invocation

Run export using the shell wrapper:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-export.sh" <format> <type> [OPTIONS]
```

Or directly via the Python script:

```bash
uv run python scripts/export.py <format> <type> [OPTIONS]
```

## Formats

- `yaml`: Legacy YAML format (compatible with v0 tools)
- `md`: Markdown format for documentation

## Types

### YAML Export
- `claims`: Export all claims with counters and chains
- `sources`: Export all sources
- `all`: Export both claims and sources

### Markdown Export
- `claim --id ID`: Single claim as Markdown
- `chain --id ID`: Argument chain as Markdown
- `predictions`: All predictions grouped by status
- `summary`: Dashboard with statistics

## Options

- `--id`: Required for claim/chain export
- `-o, --output`: Output file (default: stdout)

## Examples

```
/rc-export yaml claims -o registry.yaml
/rc-export yaml sources -o sources.yaml
/rc-export md claim --id TECH-2026-001
/rc-export md chain --id CHAIN-2026-001
/rc-export md predictions -o predictions.md
/rc-export md summary -o dashboard.md
```

## Related Commands

- `/rc-validate` - Check data integrity
- `/rc-search` - Semantic search
- `/rc-stats` - Database statistics

## Legacy Format

YAML exports use the legacy format with:
- `confidence` instead of `credence`
- `counters` for claim numbering
- Compatible with postsingularity-economic-theories structure
