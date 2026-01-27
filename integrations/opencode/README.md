# Reality Check - OpenCode Integration

Reality Check skills for [OpenCode](https://opencode.ai), the open-source AI coding agent.

## Installation

### Via Makefile (Recommended)

```bash
make install-skills-opencode
```

### Manual Installation

```bash
bash integrations/opencode/install.sh
```

Or create symlinks manually:

```bash
mkdir -p ~/.config/opencode/skills
ln -s /path/to/realitycheck/integrations/opencode/skills/* ~/.config/opencode/skills/
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `realitycheck` | Main entry point - full analysis workflow |
| `realitycheck-check` | Full analysis with all options |
| `realitycheck-analyze` | Manual 3-stage analysis without registration |
| `realitycheck-extract` | Quick claim extraction |
| `realitycheck-search` | Semantic search across claims |
| `realitycheck-validate` | Database integrity validation |
| `realitycheck-export` | Export to YAML/Markdown |
| `realitycheck-stats` | Database statistics |
| `realitycheck-synthesize` | Cross-source synthesis |

## Usage

Skills are loaded on-demand via OpenCode's `skill` tool. You can:

1. **Ask OpenCode to load a skill directly:**
   ```
   Load the realitycheck skill
   ```

2. **Reference skills in your prompts:**
   ```
   Using the realitycheck-check skill, analyze https://example.com/article
   ```

3. **Let OpenCode discover skills automatically** based on context

### Example Session

```
> Analyze this article for claims: https://example.com/tech-article

OpenCode will:
1. Load the realitycheck-check skill
2. Fetch the article content
3. Run 3-stage analysis (descriptive → evaluative → dialectical)
4. Extract and classify claims
5. Register source and claims in your database
6. Validate data integrity
7. Report summary with claim IDs
```

## Prerequisites

### Environment Variable

Set `REALITYCHECK_DATA` to point to your data repository:

```bash
export REALITYCHECK_DATA=/path/to/realitycheck-data/data/realitycheck.lance
```

Add to your shell profile for persistence:

```bash
echo 'export REALITYCHECK_DATA="/path/to/data/realitycheck.lance"' >> ~/.bashrc
```

### CLI Tools

Install Reality Check CLI tools:

```bash
pip install realitycheck
```

Verify installation:

```bash
rc-db --help
```

## Uninstallation

```bash
make uninstall-skills-opencode
```

Or manually:

```bash
bash integrations/opencode/uninstall.sh
```

## Skill Discovery

OpenCode discovers skills from:

- Project-local: `.opencode/skills/` (walks up to git root)
- Global: `~/.config/opencode/skills/`
- Claude-compatible: `.claude/skills/` and `~/.claude/skills/`

This integration installs to `~/.config/opencode/skills/` for global access.

## Permissions

To configure skill permissions in your project, add to `opencode.json`:

```json
{
  "permission": {
    "skill": {
      "realitycheck-*": "allow"
    }
  }
}
```

## Troubleshooting

### Skills not appearing

1. Verify installation: `ls ~/.config/opencode/skills/`
2. Check skill names match directory names
3. Restart OpenCode after installation

### Database errors

1. Verify `REALITYCHECK_DATA` is set: `echo $REALITYCHECK_DATA`
2. Check database exists: `ls $REALITYCHECK_DATA`
3. Initialize if needed: `rc-db init`

### Missing CLI commands

1. Install: `pip install realitycheck`
2. Verify: `which rc-db`
3. Check PATH includes pip bin directory

## See Also

- [OpenCode Skills Documentation](https://opencode.ai/docs/skills/)
- [Reality Check README](../../README.md)
- [docs/EXTENDING-SKILLS.md](../../docs/EXTENDING-SKILLS.md) - Adding new integrations
