---
name: export
description: Export Reality Check data to YAML or Markdown formats for backup, sharing, or documentation.
argument-hint: "<format> <type> [--id ID] [-o OUTPUT]"
allowed-tools: ["Bash(uv run python scripts/export.py *)", "Bash(rc-export *)"]
---

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

# /export - Data Export
Export Reality Check data to YAML or Markdown formats for backup, sharing, or documentation.

## Usage

```
/export <format> <type> [--id ID] [-o OUTPUT]
```

Export Reality Check data to YAML or Markdown formats.

## Usage

```bash
rc-export <format> <type> [--id ID] [-o OUTPUT]
# or: uv run python scripts/export.py <format> <type> ...
```

## Arguments

- `format`: Output format (`yaml` or `markdown`)
- `type`: What to export (`claims`, `sources`, `chains`, `all`)

## Options

- `--id`: Export specific record by ID
- `-o, --output`: Output file path (default: stdout)
- `--domain`: Filter by domain (for claims)
- `--include-embeddings`: Include vector embeddings (large!)

## Examples

```bash
# Export all claims as YAML
rc-export yaml claims -o claims.yaml

# Export specific source as Markdown
rc-export markdown source --id doctorow-2026-reverse-centaur

# Export all data as YAML
rc-export yaml all -o full-export.yaml

# Export TECH domain claims
rc-export yaml claims --domain TECH -o tech-claims.yaml
```

## Output Formats

**YAML**: Machine-readable, suitable for backup/migration
```yaml
claims:
  - id: "TECH-2026-001"
    text: "..."
    type: "[T]"
    ...
```

**Markdown**: Human-readable, suitable for documentation
```markdown
# Claims Export

## TECH-2026-001
**Text**: ...
**Type**: [T]
...
```

---

## Related Commands

- `/stats`
- `/validate`
