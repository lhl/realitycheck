# Reality Check Codex Skills

This directory contains Codex CLI “skills” that approximate Claude Code-style slash commands:

- `/check ...` → `integrations/codex/skills/check/SKILL.md`
- `/reality:* ...` → `integrations/codex/skills/realitycheck/SKILL.md`

## Install

Install via Makefile:

```bash
make install-codex-skills
```

Or run the installer directly:

```bash
bash integrations/codex/install.sh
```

This symlinks skills into `$CODEX_HOME/skills` (default: `~/.codex/skills`).

## Uninstall

```bash
make uninstall-codex-skills
```

or:

```bash
bash integrations/codex/uninstall.sh
```

## Usage

If Codex doesn’t auto-trigger the skill, explicitly invoke it with `$check` or `$realitycheck`.

Examples:

```text
/check https://example.com/report --domain TECH
/reality:data ~/my-realitycheck-data/data/realitycheck.lance
/reality:stats
/reality:search "automation wages" --domain LABOR --limit 5 --format text
/reality:validate --strict
```
