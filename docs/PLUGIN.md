# RealityCheck Claude Code Plugin

Integrate RealityCheck methodology into your Claude Code sessions.

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

Full 3-stage analysis of a source.

```
/analyze <url_or_source_id>
```

**Process**:
1. Stage 1: Descriptive (summarize, extract claims, identify assumptions)
2. Stage 2: Evaluative (assess coherence, rate evidence, find disconfirming evidence)
3. Stage 3: Dialectical (steelman, counterarguments, synthesis)

**Examples**:
```
/analyze https://example.com/ai-labor-report
/analyze epoch-2024-training
```

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
5. Register in database

**Examples**:
```
/extract https://arxiv.org/abs/2301.xxxxx
/extract "AI will automate 50% of jobs by 2030"
```

### /search - Semantic Search

Search claims and sources using natural language.

```
/search <query> [--domain DOMAIN] [--limit N]
```

**Options**:
- `--domain`: Filter by domain (LABOR, ECON, GOV, TECH, etc.)
- `--limit`: Max results (default: 10)

**Examples**:
```
/search "AI automation labor displacement"
/search "training costs" --domain TECH --limit 5
```

### /validate - Data Integrity

Check database integrity.

```
/validate [--strict] [--json]
```

**Options**:
- `--strict`: Treat warnings as errors
- `--json`: Output as JSON

**Checks**:
- Schema validation (ID format, types, ranges)
- Referential integrity (all references resolve)
- Logical consistency (chain credences, prediction links)

### /export - Data Export

Export to Markdown or YAML.

```
/export <format> <type> [--id ID] [-o OUTPUT]
```

**YAML Export** (legacy format):
```
/export yaml claims -o registry.yaml
/export yaml sources -o sources.yaml
/export yaml all -o data/
```

**Markdown Export**:
```
/export md claim --id TECH-2026-001
/export md chain --id CHAIN-2026-001
/export md predictions -o predictions.md
/export md summary -o dashboard.md
```

## Methodology Templates

The plugin injects methodology from:

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

### Hooks (Optional)

`plugin/hooks/hooks.json`:

```json
{
  "post-analyze": ["scripts/validate.sh"],
  "post-extract": ["scripts/embed.sh"]
}
```

## Script Wrappers

Shell scripts in `plugin/scripts/` wrap Python CLI tools:

- `validate.sh` - Run validation
- `embed.sh` - Generate embeddings
- `export.sh` - Export data

## Dependencies

The plugin requires:

1. **Python scripts** installed (`pip install realitycheck` or `uv sync`)
2. **LanceDB database** initialized (`rc-db init`)
3. **Embeddings** generated for search (`rc-embed generate`)

## Troubleshooting

### Commands not appearing

1. Verify symlink exists: `ls -la ~/.claude/plugins/local/`
2. Restart Claude Code session
3. Check plugin.json syntax

### Database errors

1. Initialize database: `rc-db init`
2. Check path: `echo $ANALYSIS_DB_PATH`
3. Verify permissions on data directory

### Search returns no results

1. Generate embeddings: `rc-embed generate`
2. Check data exists: `rc-db list claims`
3. Try broader query

## Development

### Testing Commands

1. Make changes to `plugin/commands/*.md`
2. Test in Claude Code session
3. Commands auto-reload on next invocation

### Adding New Commands

1. Create `plugin/commands/newcommand.md`
2. Add entry to `plugin/.claude-plugin/plugin.json`
3. Create wrapper script if needed in `plugin/scripts/`

### Command Template

```markdown
# /command - Short Description

Long description of what this command does.

## Usage

\`\`\`
/command <args> [--options]
\`\`\`

## Arguments

- `arg`: Description

## Options

- `--option`: Description (default: value)

## Examples

\`\`\`
/command example1
/command example2 --option value
\`\`\`

## Related Commands

- `/other`: Related functionality
```
