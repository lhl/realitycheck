---
name: realitycheck
description: Reality Check (Codex): provides `/reality:*` utility commands (data/stats/search/validate/export/etc.) by invoking the installed `rc-*` CLIs, and can set `REALITYCHECK_DATA` for the current Codex session.
metadata:
  short-description: /reality:* commands for Codex
---

# Reality Check `/reality:*` (Codex)

Use this skill when the user types a `/reality:<subcommand> ...` message in Codex.

If this skill does not auto-trigger, explicitly invoke it with `$realitycheck` and repeat the `/reality:*` command.

## Preconditions

- Assume the `realitycheck` Python package is installed (so `rc-db`, `rc-validate`, `rc-export`, `rc-migrate` are on `PATH`).
- Prefer using `REALITYCHECK_DATA` for database selection.

If `REALITYCHECK_DATA` is not set, guide the user to set it (or use `/reality:data` below).

## Subcommands

### `/reality:data <path>`

Set (or override) `REALITYCHECK_DATA` for the current Codex session.

Behavior:
1. Resolve the path to an absolute path and confirm it points to a LanceDB directory (typically ends with `.lance/`).
2. Remember it for subsequent commands in this Codex session.
3. Explain how to persist it for the user’s shell:
   - `export REALITYCHECK_DATA="/abs/path/to/realitycheck.lance"`

Important: this cannot permanently change the user’s shell environment; it only affects commands executed by Codex in this session.

### `/reality:stats`

Run:
- `rc-db stats`

### `/reality:search <query> [--domain DOMAIN] [--limit N] [--format json|text]`

Run:
- `rc-db search "<query>" ...`

### `/reality:validate [--strict] [--json]`

Run:
- `rc-validate ...`

### `/reality:export ...`

Pass through to `rc-export`. Common patterns:
- `rc-export yaml claims -o claims.yaml`
- `rc-export yaml sources -o sources.yaml`
- `rc-export md summary -o summary.md`

### `/reality:help`

Print a concise help message listing the supported `/reality:*` subcommands and examples.

## Execution rules

- Prefer installed entry points (`rc-*`) over `uv run python scripts/*.py`.
- When running commands, ensure they target the intended DB:
  - If `REALITYCHECK_DATA` is set in the environment, use it as-is.
  - If the user used `/reality:data`, prefix commands with `REALITYCHECK_DATA="<path>"` for every invocation.
