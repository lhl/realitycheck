---
name: export
description: Export Reality Check data to Markdown or YAML formats. Use for documentation, backups, or data portability.
argument-hint: "<format> <type> [--id ID] [-o OUTPUT]"
allowed-tools: ["Bash(uv run python scripts/export.py *)"]
---

# Reality Check Data Export

Export data to YAML or Markdown formats.

## Usage

```!
uv run python scripts/export.py $ARGUMENTS
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
/rc-export md summary -o dashboard.md
```
