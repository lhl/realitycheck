---
name: realitycheck
description: "Reality Check utilities for Codex (data, stats, search, validate, export) via rc-* CLIs."
metadata:
  short-description: Reality Check utilities for Codex
---

# Reality Check `$realitycheck` (Codex)

Use this skill when the user asks for Reality Check utility commands in Codex.

If this skill does not auto-trigger, explicitly invoke it with `$realitycheck` and repeat the request.

Note: Codex CLI reserves `/...` for built-in commands. Custom `/reality:*` commands are not supported; use `$realitycheck ...` instead.

## Preconditions

- Assume the `realitycheck` Python package is installed (so `rc-db`, `rc-validate`, `rc-export`, `rc-migrate` are on `PATH`).
- Prefer using `REALITYCHECK_DATA` for database selection.

If `REALITYCHECK_DATA` is not set, guide the user to set it (or use `data <path>` below).

## Subcommands

### `data <path>`

Set (or override) `REALITYCHECK_DATA` for the current Codex session.

Behavior:
1. Resolve the path to an absolute path and confirm it points to a LanceDB directory (typically ends with `.lance/`).
2. Remember it for subsequent commands in this Codex session.
3. Explain how to persist it for the user’s shell:
   - `export REALITYCHECK_DATA="/abs/path/to/realitycheck.lance"`

Important: this cannot permanently change the user’s shell environment; it only affects commands executed by Codex in this session.

### `stats`

Run:
- `rc-db stats`

### `search <query> [--domain DOMAIN] [--limit N] [--format json|text]`

Run:
- `rc-db search "<query>" ...`

### `validate [--strict] [--json]`

Run:
- `rc-validate ...`

### `export ...`

Pass through to `rc-export`. Common patterns:
- `rc-export yaml claims -o claims.yaml`
- `rc-export yaml sources -o sources.yaml`
- `rc-export md summary -o summary.md`

### `help`

Print a concise help message listing the supported subcommands and examples.

### `embed ...`

Pass through to `rc-embed`. Common patterns:
- `rc-embed status`
- `rc-embed generate --batch-size 32 -v`

## Execution rules

- Prefer installed entry points (`rc-*`) over `uv run python scripts/*.py`.
- When running commands, ensure they target the intended DB:
  - If `REALITYCHECK_DATA` is set in the environment, use it as-is.
  - If the user used `data <path>`, prefix commands with `REALITYCHECK_DATA="<path>"` for every invocation.
