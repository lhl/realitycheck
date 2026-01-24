# Reality Check Claude Code Plugin

Integrate Reality Check methodology and database operations into Claude Code sessions.

## Status: v0.1.0

The plugin provides:
- **Command definitions** - 8 slash commands for analysis workflows
- **Shell wrappers** - CLI integration via `integrations/claude/plugin/scripts/`
- **Full workflow automation** - `/reality:check` command for end-to-end analysis

## Installation

### Option 1: Makefile (Recommended)

```bash
cd /path/to/realitycheck
make install-plugin-claude
```

### Using the Plugin

**Note:** Local plugin discovery from `~/.claude/plugins/local/` is currently broken. Use the `--plugin-dir` flag:

```bash
# Start Claude Code with the plugin loaded:
claude --plugin-dir /path/to/realitycheck/integrations/claude/plugin

# Or create a shell alias:
alias claude-rc='claude --plugin-dir /path/to/realitycheck/integrations/claude/plugin'
```

### Alternative: Global Skills

If you prefer skills over plugins:

```bash
make install-skills-claude
```

Skills are installed to `~/.claude/skills/` and auto-activate based on context.

## Commands

Commands are prefixed with `/reality:`:

### /reality:check - Full Analysis Workflow (Flagship)

The primary command for end-to-end source analysis.

```
/reality:check <url>
/reality:check <url> --domain TECH --quick
/reality:check <source-id> --continue
```

**Workflow:**
1. Fetch source content (WebFetch)
2. Extract source metadata
3. Run 3-stage analysis (descriptive → evaluative → dialectical)
4. Extract and classify claims
5. Register source and claims in database
6. Validate data integrity
7. Generate summary report

**Options:**
- `--domain`: Primary domain hint (TECH/LABOR/ECON/etc.)
- `--quick`: Skip Stage 3 (dialectical analysis)
- `--no-register`: Analyze without database registration
- `--continue`: Continue/iterate on an existing analysis

### /reality:synthesize - Cross-Source Synthesis

Create a cross-source synthesis across multiple source analyses and claims.

Use this when the task is inherently multi-source (compare/contrast, reconcile conflicts, summarize state-of-evidence), typically after running `/reality:check` for each source.

```
/reality:synthesize <topic>
```

**Workflow:**
1. Identify relevant source analyses in `analysis/sources/`
2. Write a synthesis in `analysis/syntheses/` linking back to those sources
3. (Optional) Register an argument chain and set `--analysis-file` to the synthesis path
4. Update the data repo `README.md` (Syntheses section)
5. Commit and push

### /reality:analyze - Manual Analysis

3-stage analysis without automatic database registration.

```
/reality:analyze <url_or_source_id>
```

### /reality:extract - Quick Extraction

Fast claim extraction without full 3-stage analysis.

```
/reality:extract <source>
```

### /reality:search - Semantic Search

Search claims using natural language.

```
/reality:search <query> [--domain DOMAIN] [--limit N]
```

### /reality:validate - Data Integrity

Check database for errors and inconsistencies.

```
/reality:validate [--strict] [--json]
```

### /reality:export - Data Export

Export data to YAML or Markdown.

```
/reality:export yaml claims -o registry.yaml
/reality:export md claim --id TECH-2026-001
```

### /reality:stats - Database Statistics

Show counts for all tables.

```
/reality:stats
```

## Shell Wrappers

The plugin includes shell wrappers in `integrations/claude/plugin/scripts/`:

| Script | Purpose |
|--------|---------|
| `resolve-project.sh` | Find project root, set REALITYCHECK_DATA |
| `run-db.sh` | Wrapper for db.py |
| `run-validate.sh` | Wrapper for validate.py |
| `run-export.sh` | Wrapper for export.py |

## Configuration

### Plugin Manifest

`integrations/claude/plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "reality",
  "version": "0.1.0",
  "description": "Framework for rigorous analysis of claims, sources, predictions, and argument chains"
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REALITYCHECK_DATA` | `data/realitycheck.lance` | Path to LanceDB database |
| `REALITYCHECK_EMBED_MODEL` | `all-MiniLM-L6-v2` | Local embedding model |

## Lifecycle Hooks

The plugin includes lifecycle hooks:

| Hook | Script | Purpose |
|------|--------|---------|
| Stop | `on-stop.sh` | Runs validation when session ends |
| PostToolUse | `post-db-modify.sh` | Auto-commit data project changes |

Auto-commit controls:
- `REALITYCHECK_AUTO_COMMIT` (default: `true`)
- `REALITYCHECK_AUTO_PUSH` (default: `false`)

## Development

### Testing Commands

1. Make changes to `integrations/claude/plugin/commands/*.md`
2. Frontmatter must be at the very top of the file
3. Test with: `claude --plugin-dir /path/to/integrations/claude/plugin`

### Command Markdown Format

```markdown
---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh *)"]
description: Short description of the command
---

# /commandname - Title

Command documentation...
```

## Methodology Templates

The plugin references methodology from:

- `methodology/evidence-hierarchy.md` - E1-E6 rating scale
- `methodology/claim-taxonomy.md` - Claim types and domains
- `methodology/templates/source-analysis.md` - 3-stage analysis
- `methodology/templates/claim-extraction.md` - Quick extraction
- `methodology/templates/synthesis.md` - Cross-source synthesis
