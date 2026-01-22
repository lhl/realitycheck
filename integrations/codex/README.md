# Reality Check Codex Skills

This directory contains Codex CLI “skills” that approximate Claude Code-style workflows.

Codex CLI reserves `/...` for built-in commands, so custom slash commands are not supported. Use `$...` skill invocation (or plain language) instead.

- `$check ...` → `integrations/codex/skills/check/SKILL.md`
- `$realitycheck ...` → `integrations/codex/skills/realitycheck/SKILL.md`

## Install

Install via Makefile:

```bash
make install-skills-codex
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

**Embeddings:** By default, Reality Check generates embeddings when you register sources/claims. Only use `--no-embedding` (or `REALITYCHECK_EMBED_SKIP=1`) when you explicitly want to defer embeddings (e.g., offline without a cached model).

**Commits/push:** Codex skills do not support Claude Code-style hooks. If your `REALITYCHECK_DATA` points to a separate git repo, commit/push changes manually (or run the same scripts the Claude plugin hooks call: `integrations/claude/plugin/hooks/auto-commit-data.sh`, which updates README stats and commits `data/`, `analysis/`, `tracking/`, `README.md`).

Examples:

```text
$check https://example.com/report --domain TECH --quick --no-register
$realitycheck data ~/my-realitycheck-data/data/realitycheck.lance
$realitycheck stats
$realitycheck search "automation wages" --domain LABOR --limit 5 --format text
$realitycheck validate --strict
$realitycheck embed status
rc-html-extract ./page.html --format json
```
