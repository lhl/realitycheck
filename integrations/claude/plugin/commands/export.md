---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-export.sh *)"]
description: Export data to Markdown or YAML formats
---

# /reality:export - Data Export

Export data to Markdown or YAML formats.

## Usage

```
/reality:export <format> <type> [--id ID] [-o OUTPUT]
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
/reality:export yaml claims -o registry.yaml
/reality:export yaml sources -o sources.yaml
/reality:export md claim --id TECH-2026-001
/reality:export md chain --id CHAIN-2026-001
/reality:export md predictions -o predictions.md
/reality:export md summary -o dashboard.md
```

## Related Commands

- `/reality:validate` - Check data integrity
- `/reality:search` - Semantic search
- `/reality:stats` - Database statistics

## Legacy Format

YAML exports use the legacy format with:
- `confidence` instead of `credence`
- `counters` for claim numbering
- Compatible with postsingularity-economic-theories structure
