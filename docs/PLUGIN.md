# Reality Check Claude Code Plugin

Integrate Reality Check methodology and database operations into Claude Code sessions.

## Status: v0.1.0-beta

The plugin provides:
- **Command definitions** - 7 slash commands for analysis workflows
- **Shell wrappers** - CLI integration via `plugin/scripts/`
- **Full workflow automation** - `/check` command for end-to-end analysis

## Installation

### Option 1: Makefile (Recommended)

```bash
cd /path/to/realitycheck
make install-plugin
```

### Option 2: Manual Symlink

```bash
mkdir -p ~/.claude/plugins/local
ln -s /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck
```

### Option 3: Copy (Standalone)

```bash
cp -r /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck
```

### Verify Installation

```bash
ls -la ~/.claude/plugins/local/realitycheck
# Should show: realitycheck -> /path/to/realitycheck/plugin
```

Restart Claude Code to load the plugin.

## Commands

### /check - Full Analysis Workflow (Flagship)

The primary command for end-to-end source analysis.

```
/check <url>
/check <url> --domain TECH --quick
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

### /realitycheck - Alias

Alias for `/check`. Identical functionality.

### /rc-analyze - Manual Analysis

3-stage analysis without automatic database registration.

```
/rc-analyze <url_or_source_id>
```

Use when you want to:
- Analyze without committing to database
- Re-analyze an existing source
- Have more control over the process

After analysis, register manually:
```bash
uv run python scripts/db.py source add --id "..." --title "..." ...
uv run python scripts/db.py claim add --text "..." --type "[F]" ...
```

### /rc-extract - Quick Extraction

Fast claim extraction without full 3-stage analysis.

```
/rc-extract <source>
```

Good for:
- Quick scanning of sources
- Extracting obvious claims
- Processing multiple sources rapidly

### /rc-search - Semantic Search

Search claims using natural language.

```
/rc-search <query> [--domain DOMAIN] [--limit N] [--format json|text]
```

**Examples:**
```
/rc-search "AI automation labor displacement"
/rc-search "training costs" --domain TECH --limit 5
```

**Backend:** Runs `uv run python scripts/db.py search "..."`.

### /rc-validate - Data Integrity

Check database for errors and inconsistencies.

```
/rc-validate [--strict] [--json]
```

**Checks:**
- Schema validation (ID formats, valid types, credence range)
- Referential integrity (source/claim links)
- Logical consistency (domain matching, chain credence)

**Backend:** Runs `uv run python scripts/validate.py`.

### /rc-export - Data Export

Export data to YAML or Markdown.

```
/rc-export yaml claims -o registry.yaml
/rc-export yaml sources -o sources.yaml
/rc-export md claim --id TECH-2026-001
/rc-export md predictions -o predictions.md
```

**Backend:** Runs `uv run python scripts/export.py ...`.

### /rc-stats - Database Statistics

Show counts for all tables.

```
/rc-stats
```

**Backend:** Runs `uv run python scripts/db.py stats`.

## Shell Wrappers

The plugin includes shell wrappers in `plugin/scripts/`:

| Script | Purpose |
|--------|---------|
| `resolve-project.sh` | Find project root, set REALITYCHECK_DATA |
| `run-db.sh` | Wrapper for db.py |
| `run-validate.sh` | Wrapper for validate.py |
| `run-export.sh` | Wrapper for export.py |

These scripts:
1. Detect project context (via `.realitycheck.yaml` or `data/*.lance`)
2. Set environment variables
3. Invoke Python scripts with `uv run` (development) or installed commands

## Configuration

### Plugin Manifest

`plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "realitycheck",
  "version": "0.1.0",
  "commands": [
    {"name": "check", "file": "commands/check.md"},
    {"name": "realitycheck", "file": "commands/realitycheck.md"},
    {"name": "rc-analyze", "file": "commands/rc-analyze.md"},
    {"name": "rc-extract", "file": "commands/rc-extract.md"},
    {"name": "rc-validate", "file": "commands/rc-validate.md"},
    {"name": "rc-search", "file": "commands/rc-search.md"},
    {"name": "rc-export", "file": "commands/rc-export.md"},
    {"name": "rc-stats", "file": "commands/rc-stats.md"}
  ]
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REALITYCHECK_DATA` | `data/realitycheck.lance` | Path to LanceDB database |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |

## Dependencies

The plugin requires:

1. **Python 3.11+** with dependencies installed (`uv sync`)
2. **LanceDB database** initialized (`uv run python scripts/db.py init`)
3. **Embeddings** for search (generated automatically on first claim)

## Troubleshooting

### Commands not appearing

1. Verify symlink: `ls -la ~/.claude/plugins/local/`
2. Check plugin.json syntax: `cat ~/.claude/plugins/local/realitycheck/.claude-plugin/plugin.json`
3. Restart Claude Code session

### Database errors

```bash
# Initialize database
uv run python scripts/db.py init

# Check database location
echo $REALITYCHECK_DATA

# Verify data directory
ls -la data/
```

### Search returns no results

```bash
# Check if data exists
uv run python scripts/db.py stats

# Verify embeddings (claims need embeddings for search)
uv run python scripts/db.py claim list --format text
```

### Shell wrapper issues

```bash
# Test wrapper directly
./plugin/scripts/run-db.sh --help

# Check if uv is available
which uv

# Verify Python scripts
uv run python scripts/db.py --help
```

## Development

### Testing Commands

1. Make changes to `plugin/commands/*.md`
2. Commands reload on next invocation (no restart needed)
3. Test in Claude Code session

### Adding New Commands

1. Create `plugin/commands/newcommand.md`
2. Add entry to `plugin/.claude-plugin/plugin.json`
3. Restart Claude Code

### Command Markdown Format

```markdown
# /commandname - Short Description

Description of what the command does.

---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh *)"]
---

## Usage

\`\`\`
/commandname <args> [--options]
\`\`\`

## CLI Invocation

\`\`\`bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" subcommand args
\`\`\`

...
```

## Lifecycle Hooks

The plugin includes lifecycle hooks that run automatically:

### hooks.json

```json
{
  "hooks": {
    "Stop": [...],           // Runs when session ends
    "PostToolUse": [...]     // Runs after db.py commands
  }
}
```

### Available Hooks

| Hook | Script | Purpose |
|------|--------|---------|
| Stop | `on-stop.sh` | Runs validation when session ends, alerts on errors |
| PostToolUse | `post-db-modify.sh` | Runs after database modifications (silent by default) |

### How They Work

**on-stop.sh**: When you end a Claude Code session, this hook automatically runs `validate.py` and alerts you if there are any database integrity errors. Warnings are suppressed to keep output clean.

**post-db-modify.sh**: Runs after any Bash command matching `*db.py*`. Currently silent by default - the Stop hook handles validation. Can be enabled for per-operation reminders.

### Customizing Hooks

To disable hooks, rename or remove `plugin/hooks/hooks.json`.

To modify behavior, edit the shell scripts in `plugin/hooks/`.

## Methodology Templates

The plugin references methodology from:

- `methodology/evidence-hierarchy.md` - E1-E6 rating scale
- `methodology/claim-taxonomy.md` - Claim types and domains
- `methodology/templates/source-analysis.md` - 3-stage analysis
- `methodology/templates/claim-extraction.md` - Quick extraction
- `methodology/templates/synthesis.md` - Cross-source synthesis
