# Integrations

Reality Check supports tool-specific integrations (plugins, skills, wrappers) for AI coding assistants.

## Directory Structure

```
integrations/
├── _templates/          # Jinja2 templates (SOURCE OF TRUTH)
│   ├── partials/        # Shared content snippets
│   ├── tables/          # Analysis table templates
│   ├── sections/        # Analysis section templates
│   ├── skills/          # Skill-specific content
│   └── wrappers/        # Integration-specific wrappers
├── _config/
│   └── skills.yaml      # Skill definitions
├── assemble.py          # Build script
├── amp/
│   └── skills/          # Generated Amp skills
├── claude/
│   ├── plugin/          # Claude Code plugin (commands, hooks)
│   └── skills/          # Generated Claude Code skills
└── codex/
    └── skills/          # Generated Codex skills
```

## Skill Generation

Skills are **generated from templates** - do not edit SKILL.md files directly.

### Regenerating Skills

```bash
# Generate all skills
make assemble-skills

# Check if skills are up-to-date (for CI)
make check-skills

# Generate specific integration
python integrations/assemble.py --integration claude

# Generate specific skill
python integrations/assemble.py --skill check

# Preview changes without writing
python integrations/assemble.py --dry-run

# Show diff vs existing files
python integrations/assemble.py --diff
```

### Modifying Skills

1. Edit templates in `_templates/` (partials, tables, sections, skills, wrappers)
2. Run `make assemble-skills` to regenerate
3. Commit both templates and generated files

### Template Structure

| Directory | Purpose |
|-----------|---------|
| `partials/` | Reusable content (evidence hierarchy, claim types, etc.) |
| `tables/` | Analysis table templates (Key Claims, Disconfirming Evidence, etc.) |
| `sections/` | Analysis section templates (Argument Structure, Theoretical Lineage) |
| `skills/` | Core skill content (check, analyze, extract, etc.) |
| `wrappers/` | Integration-specific frontmatter and formatting |

### Exception: `realitycheck` Skill

The `realitycheck` skill is manually maintained (not templated) because it serves different purposes:
- **Claude**: Alias for `/check`
- **Codex**: Utilities wrapper (`$realitycheck stats`, `search`, etc.)

---

## Amp

Skills for [Amp](https://ampcode.com) - activate on natural language triggers.

```bash
# Install
make install-skills-amp

# Skills: realitycheck-{analyze,check,export,extract,search,stats,validate}
# Triggers: "Analyze this article", "Search for claims", "Validate database", etc.
```

See [amp/README.md](amp/README.md) for details.

## Claude Code

### Plugin

The plugin provides slash commands for Reality Check workflows.

```bash
# Install
make install-plugin-claude

# Usage (local plugin discovery is currently broken, use --plugin-dir):
claude --plugin-dir /path/to/realitycheck/integrations/claude/plugin

# Commands: /reality:check, /reality:analyze, /reality:search, etc.
```

### Global Skills

Skills are auto-activated based on context.

```bash
# Install
make install-skills-claude

# View installed skills
/skills

# Skills: analyze, check, export, extract, search, stats, validate, realitycheck
```

## Codex

Codex skills for OpenAI's Codex CLI.

```bash
# Install
make install-skills-codex

# Skills: $analyze, $check, $export, $extract, $search, $stats, $validate, $realitycheck
```

See [codex/README.md](codex/README.md) for details.
