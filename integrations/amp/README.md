# Amp Integration

Reality Check skills for [Amp](https://ampcode.com).

## Skills

| Skill | Description |
|-------|-------------|
| `realitycheck-check` | Full analysis workflow (fetch → analyze → extract → register) |
| `realitycheck-search` | Semantic search across claims and sources |
| `realitycheck-validate` | Database integrity validation |
| `realitycheck-export` | Export to YAML/Markdown |
| `realitycheck-stats` | Database statistics |

## Installation

### Option 1: Makefile (recommended)

```bash
# From the realitycheck repo root
make install-skills-amp
```

### Option 2: Install script

```bash
bash integrations/amp/install.sh
```

### Option 3: Manual symlink

```bash
# Create skills directory if needed
mkdir -p ~/.config/agents/skills

# Symlink each skill
ln -s /path/to/realitycheck/integrations/amp/skills/realitycheck-check ~/.config/agents/skills/realitycheck-check
ln -s /path/to/realitycheck/integrations/amp/skills/realitycheck-search ~/.config/agents/skills/realitycheck-search
ln -s /path/to/realitycheck/integrations/amp/skills/realitycheck-validate ~/.config/agents/skills/realitycheck-validate
ln -s /path/to/realitycheck/integrations/amp/skills/realitycheck-export ~/.config/agents/skills/realitycheck-export
ln -s /path/to/realitycheck/integrations/amp/skills/realitycheck-stats ~/.config/agents/skills/realitycheck-stats
```

## Uninstallation

```bash
make uninstall-amp-skills
# or
bash integrations/amp/uninstall.sh
```

## Usage

Skills activate on natural language triggers. Examples:

```
"Analyze this article for claims: https://example.com/article"
"Search for claims about AI automation"
"Validate the database"
"Show database stats"
"Export claims to YAML"
```

## Prerequisites

1. Install the realitycheck package:
   ```bash
   pip install realitycheck
   ```

2. Set the data path:
   ```bash
   export REALITYCHECK_DATA=/path/to/your-data/data/realitycheck.lance
   ```

## Skill Locations

Amp discovers skills from:
- **Project**: `.agents/skills/` in workspace
- **Global**: `~/.config/agents/skills/`

The install script symlinks to the global location.

## Differences from Claude/Codex Skills

| Feature | Claude | Codex | Amp |
|---------|--------|-------|-----|
| Invocation | `/check` | `$check` | Natural language |
| Frontmatter | `argument-hint`, `allowed-tools` | Same | `name`, `description` only |
| Location | `~/.claude/skills/` | `$CODEX_HOME/skills/` | `~/.config/agents/skills/` |
