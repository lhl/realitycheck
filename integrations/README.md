# Integrations

Reality Check supports tool-specific integrations (plugins, skills, wrappers) for AI coding assistants.

## Directory Structure

```
integrations/
├── amp/
│   └── skills/           # Amp skills
├── claude/
│   ├── plugin/           # Claude Code plugin (commands, hooks)
│   └── skills/           # Claude Code global skills
└── codex/
    └── skills/           # OpenAI Codex skills
```

## Amp

Skills for [Amp](https://ampcode.com) - activate on natural language triggers.

```bash
# Install
make install-amp-skills

# Triggers: "Analyze this article", "Search for claims", "Validate database", etc.
```

See [amp/README.md](amp/README.md) for details.

## Claude Code

### Plugin

The plugin provides slash commands for Reality Check workflows.

```bash
# Install
make install-claude-plugin

# Usage (local plugin discovery is currently broken, use --plugin-dir):
claude --plugin-dir /path/to/realitycheck/integrations/claude/plugin

# Commands: /reality:check, /reality:analyze, /reality:search, etc.
```

### Global Skills

Skills are auto-activated based on context.

```bash
# Install
make install-claude-skills

# View installed skills
/skills
```

## Codex

Codex skills for OpenAI's Codex CLI.

```bash
# Install
make install-codex-skills

# Usage: $check, $realitycheck, etc.
```

See [codex/README.md](codex/README.md) for details.
