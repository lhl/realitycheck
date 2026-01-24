# TODO

Tracking future work items.

## Epistemic Provenance / Reasoning Trails (Major Feature)

**Plan**: [PLAN-epistemic-provenance.md](PLAN-epistemic-provenance.md)

**Problem**: Reality Check extracts claims and assigns credence, but lacks structured traceability for *why* a claim has a given credence. We risk becoming a source of unconfirmable bias.

**Solution**:
- `evidence_links` table: Explicit links between claims and supporting/contradicting sources
- `reasoning_trails` table: Capture the reasoning chain for credence assignments
- Rendered markdown: Per-claim reasoning docs browsable in data repo
- Validation: Enforce that high-credence claims (≥0.7) have explicit backing
- Portability export: Deterministic YAML/JSON dump of provenance (regen from DB)
- Audit-log linkage: Attribute evidence/reasoning to specific analysis passes (tool/model)
- Workflow integration: Evidence linking + reasoning capture in `/check`

**Scope**: Large feature sprint - schema changes, CLI, validation, rendering, workflow updates.

**Status**: Planning - see PLAN doc for full design.

---

## Analysis Audit Log

**Plan**: [PLAN-audit-log.md](PLAN-audit-log.md)
**Implementation**: [IMPLEMENTATION-audit-log.md](IMPLEMENTATION-audit-log.md)

**Problem**: No durable record of *how* an analysis was produced (who/what/when/cost).

**Solution**: `analysis_logs` table + in-document "Analysis Log" section.

**Status**: Ready for implementation (tests first).

---

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
