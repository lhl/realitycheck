# Reality Check Codex Skills

This directory contains Codex CLI "skills" that approximate Claude Code-style workflows.

Codex CLI reserves `/...` for built-in commands, so custom slash commands are not supported. Use `$...` skill invocation (or plain language) instead.

- `$check ...` → `integrations/codex/skills/check/SKILL.md`
- `$realitycheck ...` → `integrations/codex/skills/realitycheck/SKILL.md`

## Prerequisites

Reality Check CLI commands (`rc-db`, `rc-validate`, etc.) must be available.

**Option 1: pip install (recommended)**
```bash
pip install realitycheck
# Verify
rc-db --help
```

**Option 2: From source with uv**
```bash
# From the realitycheck framework directory
uv run python scripts/db.py --help
```

**Environment variable:**
```bash
export REALITYCHECK_DATA=/path/to/your-data/data/realitycheck.lance
```

## Install Skills

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

If Codex doesn't auto-trigger the skill, explicitly invoke it with `$check` or `$realitycheck`.

**Embeddings:** By default, Reality Check generates embeddings when you register sources/claims using `sentence-transformers` (CPU-based). Only use `--no-embedding` (or `REALITYCHECK_EMBED_SKIP=1`) when you explicitly want to defer embeddings (e.g., offline without a cached model).

If semantic search fails or embeddings are missing:
```bash
# Check embedding status
rc-embed status

# Generate missing embeddings
rc-embed generate --verbose
```

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
