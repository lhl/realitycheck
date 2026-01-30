# TODO

Tracking future work items.

## Token Usage Capture (Backfill + Default Automation)

**Plan**: [PLAN-token-usage.md](PLAN-token-usage.md)
**Implementation**: [IMPLEMENTATION-token-usage.md](IMPLEMENTATION-token-usage.md)

**Problem**: Many `analysis_logs` entries lack token/cost fields because usage capture is optional and check boundaries are not consistently recorded.

**Solution** (delta accounting):
- Auto-detect current session by tool (Claude Code, Codex, Amp)
- At check start: snapshot session tokens → baseline
- At check end: snapshot session tokens → final; check_tokens = final - baseline
- Optional per-stage breakdown via `rc-db analysis mark --stage ...`
- Backfill historical entries (best-effort when baseline wasn't recorded)

**Key insight**: Each tool stores sessions with UUIDs. Sessions can span multiple checks, so we use delta accounting rather than session totals.

**Status**: ✅ Complete - implemented lifecycle commands (`analysis start/mark/complete`), session detection, backfill, and synthesis attribution.

---

## Epistemic Provenance / Reasoning Trails (Major Feature)

**Plan**: [PLAN-epistemic-provenance.md](PLAN-epistemic-provenance.md)
**Implementation**: [IMPLEMENTATION-epistemic-provenance.md](IMPLEMENTATION-epistemic-provenance.md)

**Problem**: Reality Check extracts claims and assigns credence, but lacks structured traceability for *why* a claim has a given credence. We risk becoming a source of unconfirmable bias.

**Solution**:
- `evidence_links` table: Explicit links between claims and supporting/contradicting sources
- `reasoning_trails` table: Capture the reasoning chain for credence assignments
- Rendered markdown: Per-claim reasoning docs browsable in data repo
- Validation: Enforce that high-credence claims (≥0.7) have explicit backing (configurable: warn default, `--strict` errors)
- Portability export: Deterministic YAML/JSON dump of provenance (regen from DB)
- Audit-log linkage: Attribute evidence/reasoning to specific analysis passes (tool/model)
- Workflow integration: Evidence linking + reasoning capture in `/check`

**Scope**: Large feature sprint - schema changes, CLI, validation, rendering, workflow updates (9 phases, ~60 test cases).

**Status**: ✅ Complete - all 9 phases implemented (schema, CRUD, CLI, validation, export, formatter/validator updates, templates, docs, migration support).

---

## Analysis Rigor Improvements (Primary Evidence, Layering, Corrections)

**Plan**: [PLAN-analysis-rigor-improvement.md](PLAN-analysis-rigor-improvement.md)

**Dependency**: Scheduled **after** Epistemic Provenance. Implementing provenance (`evidence_links`, `reasoning_trails`, validation gates, append-only corrections semantics) will directly satisfy part of this plan.

**Problem**: Analyses can still produce confident-looking evidence/credence tables that conflate:
- asserted authority vs lawful authority vs practiced reality,
- ICE vs CBP/DHS actor attribution,
- scoped/conditional claims vs “can anywhere/always” overgeneralizations,
- stale sources vs corrected/updated reporting,
- secondary reporting vs accessible primary documents.

**Solution**:
- Enforce `Layer/Actor/Scope/Quantifier/Evidence Type` in claim tables (template-level)
- Primary-document-first capture for high-impact claims (memos, court orders, filings, PDFs)
- Corrections/recency tracking as a first-class workflow step (with claim impact)
- Court citation hygiene (majority vs dissent; posture; controlling vs non-controlling)
- Multi-pass refinement workflow that preserves provenance and reviewer disagreement cleanly

**Status**: Queued - do after Epistemic Provenance.

---

## Analysis Audit Log

**Plan**: [PLAN-audit-log.md](PLAN-audit-log.md)
**Implementation**: [IMPLEMENTATION-audit-log.md](IMPLEMENTATION-audit-log.md)

**Problem**: No durable record of *how* an analysis was produced (who/what/when/cost).

**Solution**: `analysis_logs` table + in-document "Analysis Log" section.

**Status**: Complete (see implementation doc).

---

## Agent Ergonomics (Upsert, Doctor, Repair, Actionable Errors)

**Plan**: [PLAN-agent-ergonomics.md](PLAN-agent-ergonomics.md)
**Implementation**: [IMPLEMENTATION-agent-ergonomics.md](IMPLEMENTATION-agent-ergonomics.md)

**Problem**: Agents re-run workflows and frequently hit avoidable friction: duplicate IDs on import, brittle DB path configuration, non-actionable validation failures, and DB invariant drift.

**Solution**:
- `--on-conflict {error,skip,update}` for `rc-db import` (and key add paths where it matters)
- `rc-db doctor` and shared DB auto-detection (reduce reliance on `REALITYCHECK_DATA`)
- `rc-db repair` (safe/idempotent): recompute source↔claim backlinks + `[P]` prediction stubs; report duplicates
- Validation/CLI errors include exact remediation commands (prefer suggesting `rc-db repair`)

**Status**: Planning.

---

## Ergonomics (To Decide)

**Plan**: [PLAN-ergonomics-todecide.md](PLAN-ergonomics-todecide.md)

Items that are likely valuable but require workflow/product decisions first:

- One-shot finish/publish command/script (import → analysis add → validate → update README → git add/commit/push)
- `rc-analysis new <source-id> --from-url URL` skeleton generator (analysis `.md` + `.yaml` stub)

**Status**: TBD decisions; keep out of implementation until decided.

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
