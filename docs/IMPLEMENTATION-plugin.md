# Reality Check Plugin Implementation

This document tracks the Claude Code plugin implementation for Reality Check.

## Overview

The Reality Check plugin provides slash commands for the Claude Code CLI, enabling:
- Full analysis workflows (`/check`, `/realitycheck`)
- Database operations (`/rc-stats`, `/rc-search`, `/rc-validate`, `/rc-export`)
- Manual analysis (`/rc-analyze`, `/rc-extract`)

## Plugin Architecture

### Claude Code Plugin System

Based on the [Claude Code plugin documentation](https://code.claude.com/docs/en/plugins):

1. **Plugin Manifest**: `.claude-plugin/plugin.json` - metadata only
2. **Skills**: `skills/<name>/SKILL.md` - model-invoked capabilities
3. **Commands**: `commands/*.md` - user-invoked slash commands (legacy, use skills/)
4. **Hooks**: `hooks/hooks.json` - event handlers
5. **MCP Servers**: `.mcp.json` - external tool integration
6. **LSP Servers**: `.lsp.json` - language server integration

**Key insight**: The `commands/` directory is legacy. New plugins should use `skills/` with `SKILL.md` files.

### Directory Structure

```
integrations/claude/plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (metadata only)
├── commands/                 # Slash command definitions (used with --plugin-dir)
│   └── *.md
├── hooks/
│   └── hooks.json           # Event handlers (auto-commit, validation)
└── scripts/                 # Shell wrappers
    ├── resolve-project.sh
    ├── run-db.sh
    ├── run-validate.sh
    └── run-export.sh

integrations/claude/skills/   # Global skills (alternative to plugin)
└── <skill-name>/
    └── SKILL.md
```

**Note:** The plugin currently uses `commands/*.md` files with the `--plugin-dir` flag (local plugin discovery from `~/.claude/plugins/local/` is broken). Global skills can be installed to `~/.claude/skills/` as an alternative.

### Skill Frontmatter

Skills use YAML frontmatter with specific fields:

```yaml
---
name: skill-name
description: What this skill does and when Claude should use it
argument-hint: "QUERY [--option VALUE]"  # Optional
allowed-tools: ["Bash(...)"]              # Tool restrictions
disable-model-invocation: true            # User-only invocation
---

Skill instructions here...
```

Key frontmatter fields:
- `name`: Skill identifier (matches directory name)
- `description`: Used for model invocation decisions
- `argument-hint`: Shows usage in help
- `allowed-tools`: Restrict which tools the skill can use
- `disable-model-invocation`: If true, only user can invoke (not Claude)

### Namespacing

Plugin skills are namespaced: `/plugin-name:skill-name`

For Reality Check:
- `/realitycheck:check` - Full analysis workflow
- `/realitycheck:rc-stats` - Database statistics
- `/realitycheck:rc-search` - Semantic search

To keep commands short, we use:
- `/check` and `/realitycheck` as main workflow commands
- `/rc-*` for utility commands

## Installation

### Development (Local Testing)

Use `--plugin-dir` flag to load plugin without installation:

```bash
claude --plugin-dir /path/to/realitycheck/integrations/claude/plugin
```

### User Installation

1. **Direct path** (for personal use):
```bash
# Add to ~/.claude/settings.json under plugins
```

2. **Marketplace** (for distribution):
```bash
claude plugin install realitycheck@marketplace-name
```

### Plugin Registration

Claude Code discovers plugins via:
1. `--plugin-dir` flag (development)
2. `~/.claude/plugins/installed_plugins.json` (installed plugins)
3. `.claude/settings.json` plugins section (configured plugins)

## Commands Reference

| Command | Skill Path | Description |
|---------|------------|-------------|
| `/check` | `skills/check/SKILL.md` | Full analysis workflow |
| `/realitycheck` | Alias for /check | Same as /check |
| `/rc-stats` | `skills/rc-stats/SKILL.md` | Database statistics |
| `/rc-search` | `skills/rc-search/SKILL.md` | Semantic search |
| `/rc-validate` | `skills/rc-validate/SKILL.md` | Data integrity check |
| `/rc-export` | `skills/rc-export/SKILL.md` | Export data |
| `/rc-analyze` | `skills/rc-analyze/SKILL.md` | Manual 3-stage analysis |
| `/rc-extract` | `skills/rc-extract/SKILL.md` | Quick claim extraction |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REALITYCHECK_DATA` | `data/realitycheck.lance` | Database path |
| `REALITYCHECK_EMBED_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `REALITYCHECK_EMBED_DEVICE` | `cpu` | Embedding device |
| `REALITYCHECK_EMBED_SKIP` | unset | Skip embedding generation |

## Implementation Worklog

### 2026-01-21: Initial Plugin Structure

**Created**:
- `plugin/.claude-plugin/plugin.json` - Plugin manifest
- `plugin/commands/*.md` - Slash command definitions
- `plugin/hooks/hooks.json` - Event handlers
- `plugin/scripts/*.sh` - Shell wrappers

**Issue**: Plugin not loading in Claude Code

**Root Cause**: Used `commands/` directory with `*.md` files, but Claude Code expects:
1. `skills/` directory with `<name>/SKILL.md` structure
2. Different frontmatter format
3. Registration via `--plugin-dir` or proper installation

### 2026-01-21: Plugin Restructure (TODO)

Need to:
1. Convert `commands/*.md` to `skills/<name>/SKILL.md` format
2. Update frontmatter to use Claude Code expected fields
3. Test with `claude --plugin-dir ./plugin`
4. Update documentation

### Migration Plan

Convert each command file:

| Old Path | New Path |
|----------|----------|
| `commands/check.md` | `skills/check/SKILL.md` |
| `commands/realitycheck.md` | `skills/realitycheck/SKILL.md` |
| `commands/rc-stats.md` | `skills/rc-stats/SKILL.md` |
| `commands/rc-search.md` | `skills/rc-search/SKILL.md` |
| `commands/rc-validate.md` | `skills/rc-validate/SKILL.md` |
| `commands/rc-export.md` | `skills/rc-export/SKILL.md` |
| `commands/rc-analyze.md` | `skills/rc-analyze/SKILL.md` |
| `commands/rc-extract.md` | `skills/rc-extract/SKILL.md` |

Frontmatter changes:
```yaml
# Old format
---
allowed-tools: ["Bash(...)"]
---

# New format
---
name: rc-stats
description: Show Reality Check database statistics
argument-hint: ""
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh stats)"]
---
```

## Testing

### Local Development

```bash
# Start Claude Code with plugin loaded
claude --plugin-dir /path/to/realitycheck/integrations/claude/plugin

# Test commands
/reality:stats
/reality:check https://example.com/article
```

### Verification Checklist

- [ ] Plugin loads without errors
- [ ] `/realitycheck:rc-stats` shows database statistics
- [ ] `/realitycheck:rc-search` performs semantic search
- [ ] `/realitycheck:rc-validate` runs validation
- [ ] `/realitycheck:check` performs full analysis workflow
- [ ] Environment variables are respected

## References

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference)
- [Skills Documentation](https://code.claude.com/docs/en/skills)
