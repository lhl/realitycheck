---
name: realitycheck-export
description: Exports Reality Check data to YAML or Markdown formats. Use for documentation, backups, or generating human-readable reports.
---

# Reality Check - Data Export

Export data to YAML or Markdown formats.

## When This Skill Activates

- "Export claims to YAML"
- "Generate a summary report"
- "Export the database"
- "Create a markdown report"

## Prerequisites

- `realitycheck` package installed (`pip install realitycheck`)
- `REALITYCHECK_DATA` environment variable set

## Usage

```bash
rc-export yaml claims
rc-export yaml sources
rc-export md summary
rc-export md predictions
```

## Formats

### YAML Export

| Type | Description |
|------|-------------|
| `claims` | All claims with counters and chains |
| `sources` | All sources |
| `all` | Both claims and sources |

```bash
rc-export yaml claims -o claims/registry.yaml
rc-export yaml sources -o reference/sources.yaml
```

### Markdown Export

| Type | Description |
|------|-------------|
| `claim --id ID` | Single claim as Markdown |
| `chain --id ID` | Argument chain as Markdown |
| `predictions` | All predictions by status |
| `summary` | Dashboard with statistics |

```bash
rc-export md summary -o dashboard.md
rc-export md predictions -o tracking/predictions.md
rc-export md claim --id TECH-2026-001
```

## Options

| Option | Description |
|--------|-------------|
| `-o, --output FILE` | Output file (default: stdout) |
| `--id ID` | Required for claim/chain export |

## Common Workflows

### Backup to YAML
```bash
rc-export yaml claims -o claims/registry.yaml
rc-export yaml sources -o reference/sources.yaml
```

### Generate Documentation
```bash
rc-export md summary -o README-stats.md
rc-export md predictions -o tracking/predictions.md
```
