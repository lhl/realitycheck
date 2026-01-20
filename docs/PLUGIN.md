# RealityCheck Claude Code Plugin

Integrate RealityCheck methodology into your Claude Code sessions.

## Current Status (v0.1.0-alpha)

The plugin currently provides:
- **Command definitions** (`plugin/commands/*.md`) - Methodology templates for analysis workflows
- **Plugin manifest** (`plugin/.claude-plugin/plugin.json`) - Plugin registration

**Not yet implemented** (planned for Phase 2):
- Shell wrapper scripts (`plugin/scripts/`)
- Bundled Python scripts (`plugin/lib/`)
- Lifecycle hooks (`plugin/hooks/`)

The current plugin is **methodology-only**: it provides templates and guidance for analysis but does not directly execute database operations. Use the CLI tools (`rc-db`, `rc-validate`, etc.) for actual data manipulation.

## Installation

### Local Development

For development and testing, symlink the plugin:

```bash
ln -s /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck
```

### From Package (Coming Soon)

```bash
pip install realitycheck
# Plugin auto-registers with Claude Code
```

## Commands

### /analyze - Source Analysis

Full 3-stage analysis of a source. Provides the methodology template.

```
/analyze <url_or_source_id>
```

**Process** (methodology-guided):
1. Stage 1: Descriptive (summarize, extract claims, identify assumptions)
2. Stage 2: Evaluative (assess coherence, rate evidence, find disconfirming evidence)
3. Stage 3: Dialectical (steelman, counterarguments, synthesis)

**Note**: After analysis, use `rc-db` commands or Python API to persist results.

### /extract - Claim Extraction

Quick claim extraction without full analysis.

```
/extract <source>
```

**Process**:
1. Parse source content
2. Identify claims
3. Classify by type and domain
4. Assign evidence level and credence

**Note**: Use Python API to register claims in database.

### /search - Semantic Search

Search claims and sources using natural language.

```
/search <query> [--domain DOMAIN] [--limit N]
```

**Options**:
- `--domain`: Filter by domain (LABOR, ECON, GOV, TECH, etc.)
- `--limit`: Max results (default: 10)

**Backend (Phase 2)**: Will run `rc-db search` command.

### /validate - Data Integrity

Check database integrity.

```
/validate [--strict] [--json]
```

**Options**:
- `--strict`: Treat warnings as errors
- `--json`: Output as JSON

**Backend (Phase 2)**: Will run `rc-validate` command.

### /export - Data Export

Export to Markdown or YAML.

```
/export <format> <type> [--id ID] [-o OUTPUT]
```

**YAML Export** (legacy format):
```
/export yaml claims -o registry.yaml
/export yaml sources -o sources.yaml
```

**Markdown Export**:
```
/export md claim --id TECH-2026-001
/export md predictions -o predictions.md
```

**Backend (Phase 2)**: Will run `rc-export` command.

## Methodology Templates

The plugin references methodology from:

- `methodology/evidence-hierarchy.md` - E1-E6 rating scale
- `methodology/claim-taxonomy.md` - Claim types and domains
- `methodology/templates/source-analysis.md` - 3-stage analysis
- `methodology/templates/claim-extraction.md` - Quick extraction
- `methodology/templates/synthesis.md` - Cross-source synthesis

## Configuration

### Plugin Manifest

`plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "realitycheck",
  "version": "0.1.0",
  "description": "Rigorous claim analysis framework",
  "commands": [
    {"name": "analyze", "file": "commands/analyze.md"},
    {"name": "extract", "file": "commands/extract.md"},
    {"name": "validate", "file": "commands/validate.md"},
    {"name": "search", "file": "commands/search.md"},
    {"name": "export", "file": "commands/export.md"}
  ]
}
```

## Dependencies

The plugin requires:

1. **Python scripts** installed (`uv sync` in realitycheck repo)
2. **LanceDB database** initialized (`rc-db init`)
3. **Embeddings** generated for search (`rc-embed generate`)

## Troubleshooting

### Commands not appearing

1. Verify symlink exists: `ls -la ~/.claude/plugins/local/`
2. Restart Claude Code session
3. Check plugin.json syntax

### Database errors

1. Initialize database: `uv run rc-db init`
2. Check path: `echo $ANALYSIS_DB_PATH`
3. Verify permissions on data directory

### Search returns no results

1. Generate embeddings: `uv run rc-embed generate`
2. Verify data exists: `uv run rc-db stats`
3. Try broader query

## Development

### Testing Commands

1. Make changes to `plugin/commands/*.md`
2. Test in Claude Code session
3. Commands reload on next invocation

### Adding New Commands

1. Create `plugin/commands/newcommand.md`
2. Add entry to `plugin/.claude-plugin/plugin.json`

---

## Planned Features (Phase 2)

### Shell Wrappers

`plugin/scripts/` will contain shell wrappers that invoke CLI tools:

```bash
# plugin/scripts/validate.sh (planned)
#!/bin/bash
uv run rc-validate "$@"
```

### Bundled Scripts

`plugin/lib/` will contain bundled Python scripts for plugin-only installations (no separate `uv sync` required).

### Lifecycle Hooks

`plugin/hooks/hooks.json` will support:

```json
{
  "post-analyze": ["scripts/validate.sh"],
  "post-extract": ["scripts/embed.sh"]
}
```

These hooks would automatically validate and embed after analysis operations.
