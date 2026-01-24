# Implementation: Analysis Audit Log

**Status**: Complete (Phases 1-8 complete)
**Plan**: [PLAN-audit-log.md](PLAN-audit-log.md)
**Started**: 2026-01-23

## Summary

Implement a durable, queryable audit log for Reality Check analyses:

- **Human-facing**: append an "Analysis Log" section to analysis markdown files.
- **Machine-facing**: store each analysis run/pass in a LanceDB `analysis_logs` table.
- **Tool-agnostic**: works across Claude Code, Codex, Amp, and manual runs.

## Punchlist

### Phase 1: Tests (write FIRST per Spec→Plan→Test→Implement)
- [x] Unit tests for `rc-db analysis add/get/list` CLI (`tests/test_db.py`)
- [x] Unit tests for `rc-validate` analysis log checks (`tests/test_validate.py`)
- [x] Unit tests for `rc-export` analysis log export (`tests/test_export.py`)
- [x] E2E test: init → add source/claims → add analysis log → validate → export (`tests/test_e2e.py`)

### Phase 2: DB Schema + Core CRUD
- [x] Add `ANALYSIS_LOGS_SCHEMA` to `scripts/db.py` with fields:
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
- [x] Include `analysis_logs` in `init_tables()` / `drop_tables()`
- [x] Add `add_analysis_log()` / `get_analysis_log()` / `list_analysis_logs()`

### Phase 3: CLI (`rc-db analysis ...`)
- [x] `rc-db analysis add` with flags:
  - Required: `--source-id`, `--tool`
  - Optional: `--status`, `--pass` (auto-computed if omitted), `--model`, `--cmd`
  - Optional: `--started-at`, `--completed-at`, `--notes`, `--git-commit`
  - Optional: `--claims-extracted`, `--claims-updated` (comma-separated IDs)
  - Token/cost manual entry: `--tokens-in`, `--tokens-out`, `--total-tokens`, `--cost-usd`
- [x] `rc-db analysis get <id>` with `--format json|text`
- [x] `rc-db analysis list` with filters:
  - `--source-id`, `--tool`, `--status`
  - `--limit N` (default 20)
  - `--format json|text`

### Phase 4: Validation (`scripts/validate.py`)
- [x] If `status=completed`, require `source_id` exists in `sources`
- [x] If `claims_extracted`/`claims_updated` present and `status != draft`, require IDs exist in `claims`
- [x] Validate `stages_json` is valid JSON (if present)
- [x] Flag impossible metrics (negative duration, negative cost)

### Phase 5: Export (`scripts/export.py`)
- [x] YAML export with all schema fields (`export_analysis_logs_yaml`)
- [x] Markdown export with:
  - Stable table format (matches in-document Analysis Log)
  - Summary totals (token count, cost rollups)

### Phase 6: Documentation Updates
- [x] Update `docs/SCHEMA.md` with `analysis_logs` table definition
- [x] Update `docs/WORKFLOWS.md` with audit logging workflow
- [x] Update `docs/IMPLEMENTATION.md` Future Work section (link to this file)

### Phase 7: Integration Templates
- [x] Add `integrations/_templates/partials/analysis-log.md.j2` (shared in-document section)
- [x] Update `integrations/_templates/skills/check.md.j2` to require audit logging
- [x] Update `integrations/claude/plugin/commands/check.md` to reference audit step
- [x] Regenerate: `make assemble-skills`
  - `integrations/claude/skills/check/SKILL.md`
  - `integrations/codex/skills/check/SKILL.md`
  - `integrations/amp/skills/realitycheck-check/SKILL.md`
  - `methodology/workflows/check-core.md`

### Phase 8: Token/Cost Capture (optional automation, defer if needed)
- [x] Add `--usage-from <claude|codex|amp>:<path>` flag to `analysis add`
- [x] Add `--window-start`/`--window-end` for run boundary (optional)
- [x] Parse local session logs (usage-only; no transcript retention):
  - Claude Code: `~/.claude/projects/<project>/<session-id>.jsonl`
  - Codex: `~/.codex/sessions/.../rollout-*.jsonl`
  - Amp: `~/.local/share/amp/threads/T-*.json`
- [x] Best-effort update of in-document Analysis Log table when `--analysis-file` is provided

## Resolved Decisions

- [x] **Pass auto-compute**: Implemented - auto-computes `pass` by counting existing logs for `source_id` + 1. Added `--pass` override flag.

## Worklog

### 2026-01-24: Phases 1-5 implemented

Implemented core audit log functionality:

**DB Schema & CRUD (Phase 2)**
- Added `ANALYSIS_LOGS_SCHEMA` with 23 fields to `scripts/db.py`
- Added `add_analysis_log()`, `get_analysis_log()`, `list_analysis_logs()`
- Auto-pass computation: if `--pass` not provided, counts existing logs for source_id + 1

**CLI (Phase 3)**
- `rc-db analysis add --source-id X --tool Y [options]`
- `rc-db analysis get <id> [--format json|text]`
- `rc-db analysis list [--source-id X] [--tool Y] [--status Z] [--limit N] [--format json|text]`
- Note: used `--cmd` instead of `--command` to avoid argparse conflict with subparser

**Validation (Phase 4)**
- Added analysis log validation to `validate_db()` in `scripts/validate.py`
- Checks: status/tool validity, source existence (when completed), claim existence (when not draft), JSON validity, metric sanity

**Export (Phase 5)**
- Added `export_analysis_logs_yaml()` and `export_analysis_logs_md()` to `scripts/export.py`
- Markdown includes summary totals (tokens, cost) and breakdown by tool

**Tests**
- 23 new tests across test_db.py, test_validate.py, test_export.py
- All 206 tests pass (17 skipped are embedding tests)

### 2026-01-24: Phase 6 + fixes

- Wired `analysis-logs` into `rc-export` CLI (YAML + Markdown).
- Added an end-to-end test for the audit log workflow.
- Updated docs and punchlist statuses.

### 2026-01-24: Phase 7 templates

- Added the in-document Analysis Log template section and integrated it into `/check` skills and Claude plugin command docs.
- Regenerated skills and methodology docs from templates.

### 2026-01-24: Phase 8 token/cost capture

- Added usage parsers for Claude Code / Codex / Amp session logs (`--usage-from`, optional time window).
- Added best-effort cost estimation (`--estimate-cost`) using a small built-in pricing table (overrideable via `--price-*-per-1m`).
- `rc-db analysis add` now updates the referenced analysis markdown file's "## Analysis Log" section (if present, or inserts if missing).

### 2026-01-23: Token usage capture research

Confirmed local usage data is available for all three agentic TUIs (details in `docs/PLAN-audit-log.md`):
- Claude Code logs include per-message usage fields.
- Codex session logs include cumulative token counters.
- Amp thread logs include per-message usage fields.
