# TODO

Tracking future work items.

## Installation: `uv tool install` / `pipx` support

**Context:** Currently we recommend `uv pip install realitycheck` which installs to the active venv or system Python. A user suggested using `uv tool install realitycheck` instead, which creates an isolated venv and adds CLI tools to PATH (similar to `pipx`).

**Trade-offs to consider:**

1. **Isolation** - `uv tool install` keeps realitycheck deps separate from user projects (cleaner)
2. **Skill execution** - Skills tell agents to run `uv run python scripts/db.py` which assumes framework venv context. Would need to change to `rc-db` everywhere.
3. **Library usage** - If users want to `import scripts.db` programmatically, they need it in their project venv, not tool-isolated
4. **Dual install** - Some users may want both: CLI tools via `uv tool install` AND library in project venv

**Before changing:**
- Audit all skills to ensure they use `rc-db` / `rc-validate` / `rc-export` instead of `uv run python scripts/...`
- Test `uv tool install realitycheck` end-to-end with a fresh user
- Document when to use which installation method

**Status:** Punted - current approach works for users with managed envs (mamba, conda, project venvs)
