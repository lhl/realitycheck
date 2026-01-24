# Implementation: Analysis Audit Log

**Status**: Planning
**Plan**: [PLAN-audit-log.md](PLAN-audit-log.md)
**Started**: 2026-01-23

## Summary

Implement a durable, queryable audit log for Reality Check analyses:

- **Human-facing**: append an "Analysis Log" section to analysis markdown files.
- **Machine-facing**: store each analysis run/pass in a LanceDB `analysis_logs` table.
- **Tool-agnostic**: works across Claude Code, Codex, Amp, and manual runs.

## Punchlist

### Phase 1: Tests (write FIRST per Spec→Plan→Test→Implement)
- [ ] Unit tests for `rc-db analysis add/get/list` CLI (`tests/test_db.py`)
- [ ] Unit tests for `rc-validate` analysis log checks (`tests/test_validate.py`)
- [ ] Unit tests for `rc-export` analysis log export (`tests/test_export.py`)
- [ ] E2E test: init → add source/claims → add analysis log → validate → export (`tests/test_e2e.py`)

### Phase 2: DB Schema + Core CRUD
- [ ] Add `ANALYSIS_LOGS_SCHEMA` to `scripts/db.py` with fields:
  - `id` (ANALYSIS-YYYY-NNN)
  - `source_id`, `analysis_file`, `pass`
  - `status` (started|completed|failed|canceled|draft)
  - `tool` (claude-code|codex|amp|manual|other), `command`
  - `model`, `framework_version`, `methodology_version`
  - `started_at`, `completed_at`, `duration_seconds`
  - `tokens_in`, `tokens_out`, `total_tokens`, `cost_usd` (all nullable)
  - `stages_json` (nullable JSON string)
  - `claims_extracted`, `claims_updated` (list fields)
  - `notes`, `git_commit`, `created_at`
- [ ] Include `analysis_logs` in `init_tables()` / `drop_tables()`
- [ ] Add `add_analysis_log()` / `get_analysis_log()` / `list_analysis_logs()`

### Phase 3: CLI (`rc-db analysis ...`)
- [ ] `rc-db analysis add` with flags:
  - Required: `--source-id`, `--tool`
  - Optional: `--status`, `--pass` (auto-computed if omitted), `--model`, `--command`
  - Optional: `--started-at`, `--completed-at`, `--notes`, `--git-commit`
  - Optional: `--claims-extracted`, `--claims-updated` (comma-separated IDs)
  - Token/cost manual entry: `--tokens-in`, `--tokens-out`, `--total-tokens`, `--cost-usd`
- [ ] `rc-db analysis get <id>` with `--format json|text`
- [ ] `rc-db analysis list` with filters:
  - `--source-id`, `--tool`, `--status`
  - `--limit N` (default 20)
  - `--format json|text`

### Phase 4: Validation (`scripts/validate.py`)
- [ ] If `status=completed`, require `source_id` exists in `sources`
- [ ] If `claims_extracted`/`claims_updated` present and `status != draft`, require IDs exist in `claims`
- [ ] Validate `stages_json` is valid JSON (if present)
- [ ] Flag impossible metrics (negative duration, negative cost)

### Phase 5: Export (`scripts/export.py`)
- [ ] YAML export with all schema fields
- [ ] Markdown export with:
  - Stable table format (matches in-document Analysis Log)
  - Summary totals (token count, cost rollups)

### Phase 6: Documentation Updates
- [ ] Update `docs/SCHEMA.md` with `analysis_logs` table definition
- [ ] Update `docs/WORKFLOWS.md` with audit logging workflow
- [ ] Update `docs/IMPLEMENTATION.md` Future Work section (link to this file)

### Phase 7: Integration Templates
- [ ] Add `integrations/_templates/partials/analysis-log.md.j2` (shared in-document section)
- [ ] Update `integrations/_templates/skills/check.md.j2` to require audit logging
- [ ] Update `integrations/claude/plugin/commands/check.md` to reference audit step
- [ ] Regenerate: `make assemble-skills`
  - `integrations/claude/skills/check/SKILL.md`
  - `integrations/codex/skills/check/SKILL.md`
  - `integrations/amp/skills/realitycheck-check/SKILL.md`
  - `methodology/workflows/check-core.md`

### Phase 8: Token/Cost Capture (optional automation, defer if needed)
- [ ] Add `--usage-from <claude|codex|amp>:<path>` flag to `analysis add`
- [ ] Add `--window-start`/`--window-end` for run boundary (optional)
- [ ] Parse local session logs (usage-only; no transcript retention):
  - Claude Code: `~/.claude/projects/<project>/<session-id>.jsonl`
  - Codex: `~/.codex/sessions/.../rollout-*.jsonl`
  - Amp: `~/.local/share/amp/threads/T-*.json`

## Open Decisions

- [ ] **Pass auto-compute**: Prefer auto-computing `pass` by counting existing logs for `source_id` + 1. Add `--pass` override flag for edge cases.

## Worklog

### 2026-01-23: Token usage capture research

Confirmed local usage data is available for all three agentic TUIs (details in `docs/PLAN-audit-log.md`):
- Claude Code logs include per-message usage fields.
- Codex session logs include cumulative token counters.
- Amp thread logs include per-message usage fields.
