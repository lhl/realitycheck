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

### Phase 1: DB Schema + Core CRUD
- [ ] Add `analysis_logs` table schema to `scripts/db.py`
- [ ] Include `analysis_logs` in `init_tables()` / `drop_tables()`
- [ ] Add `add_analysis_log()` / `get_analysis_log()` / `list_analysis_logs()`

### Phase 2: CLI (`rc-db analysis ...`)
- [ ] Add `rc-db analysis add`
- [ ] Add `rc-db analysis get <id>`
- [ ] Add `rc-db analysis list` (filters: `--source-id`, `--tool`, `--status`)

### Phase 3: Validation
- [ ] Extend `scripts/validate.py` to validate `analysis_logs` referential integrity

### Phase 4: Export
- [ ] Extend `scripts/export.py` to export `analysis_logs` (YAML + Markdown summary)

### Phase 5: Integration Templates
- [ ] Add a shared "Analysis Log" template partial in `integrations/_templates/`
- [ ] Update `integrations/_templates/skills/check.md.j2` to require audit logging
- [ ] Regenerate generated skills + `methodology/workflows/check-core.md`

### Phase 6: Token/Cost Capture (optional automation)
- [ ] Add optional parsing of local session logs (usage-only; no transcript retention)
  - [ ] Claude Code: `~/.claude/projects/<project>/<session-id>.jsonl` (`message.usage`)
  - [ ] Codex: `~/.codex/sessions/.../rollout-*.jsonl` (`payload.info.total_token_usage`)
  - [ ] Amp: `~/.local/share/amp/threads/T-*.json` (`messages[i].usage`)
- [ ] Decide the run-boundary mechanism (timestamp window vs explicit markers) for per-stage deltas

### Phase 7: Tests
- [ ] Unit tests for `rc-db analysis ...` CLI
- [ ] Unit tests for `rc-validate` analysis log checks
- [ ] Unit tests for `rc-export` analysis log export
- [ ] E2E test: init → add source/claims → add analysis log → validate → export

## Worklog

### 2026-01-23: Token usage capture research

Confirmed local usage data is available for all three agentic TUIs (details in `docs/PLAN-audit-log.md`):
- Claude Code logs include per-message usage fields.
- Codex session logs include cumulative token counters.
- Amp thread logs include per-message usage fields.

