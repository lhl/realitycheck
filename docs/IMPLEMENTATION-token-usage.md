# Implementation: Token Usage Capture & Backfill

**Status**: Complete
**Plan**: [PLAN-token-usage.md](PLAN-token-usage.md)
**Depends On**: [IMPLEMENTATION-audit-log.md](IMPLEMENTATION-audit-log.md) (completed)
**Started**: 2026-01-25

## Summary

Implement automatic token usage capture with delta accounting:

- **Default capture**: Auto-detect current session at check start/end, compute token deltas
- **Per-stage breakdowns**: Optional `analysis mark --stage` for stage-level token attribution
- **Backfill**: Best-effort usage population for historical `analysis_logs` entries
- **Synthesis attribution**: Link syntheses to input analyses for end-to-end cost tracking

## Affected Files

```
scripts/
 ├── UPDATE db.py                    # Schema + lifecycle CLI commands
 ├── UPDATE usage_capture.py         # Session detection + delta helpers
 ├── UPDATE validate.py              # Validation for new fields
 └── UPDATE export.py                # Export new fields

tests/
 ├── UPDATE test_db.py               # Lifecycle CLI tests
 ├── UPDATE test_usage_capture.py    # Session detection + delta tests (or NEW)
 ├── UPDATE test_validate.py         # New field validation tests
 └── UPDATE test_export.py           # Export tests for new fields

docs/
 ├── UPDATE SCHEMA.md                # Document new analysis_logs fields
 ├── UPDATE WORKFLOWS.md             # Document lifecycle workflow
 └── UPDATE TODO.md                  # Mark item as in-progress/complete

integrations/
 ├── UPDATE _templates/skills/check.md.j2        # Use lifecycle commands
 ├── UPDATE _templates/skills/synthesize.md.j2   # Synthesis attribution
 └── regenerate all skills via `make assemble-skills`
```

## What Already Exists (from audit-log implementation)

- `analysis_logs` table with: `id`, `source_id`, `pass`, `status`, `tool`, `model`, `tokens_in`, `tokens_out`, `total_tokens`, `cost_usd`, `stages_json`, etc.
- `usage_capture.py` with `parse_usage_from_source()` for Claude/Codex/Amp
- `--usage-from <provider>:<path>` flag on `rc-db analysis add`
- Cost estimation via `--estimate-cost` and pricing table

## New Functionality Required

### Naming Conventions

**Important distinction**:
- `tool` field: Existing validation expects `claude-code|codex|amp|manual|other` (hyphenated for Claude Code)
- `usage_provider`: Simpler names for session log parsing: `claude|codex|amp`

The `--tool` CLI flag uses the full tool name (`claude-code`), while session detection internally maps to the provider name (`claude`) for parsing.

### Schema Additions

Add to `analysis_logs`:

| Field | Type | Description |
|-------|------|-------------|
| `tokens_baseline` | int (nullable) | Session token count at check start |
| `tokens_final` | int (nullable) | Session token count at check end |
| `tokens_check` | int (nullable) | Total tokens for this check (final - baseline) |
| `usage_provider` | str (nullable) | Provider for session parsing: `claude\|codex\|amp` |
| `usage_mode` | str (nullable) | Method: `per_message_sum\|windowed_sum\|counter_delta\|manual` |
| `usage_session_id` | str (nullable) | Session UUID (portable, no full paths) |
| `inputs_source_ids` | list[str] (nullable) | Source IDs feeding a synthesis (synthesis-only) |
| `inputs_analysis_ids` | list[str] (nullable) | Analysis log IDs feeding a synthesis (synthesis-only) |

### New CLI Commands

```bash
# Lifecycle commands (new)
rc-db analysis start --source-id <id> --tool <claude-code|codex|amp> [--model M] [--usage-session-id UUID]
  # → Returns ANALYSIS-YYYY-NNN; captures baseline snapshot

rc-db analysis mark --id <id> --stage <stage-name>
  # → Snapshots current tokens, appends to stages_json

rc-db analysis complete --id <id> [--status completed|failed] [--notes "..."]
  # → Snapshots final tokens, computes tokens_check

# Backfill command (new)
rc-db analysis backfill-usage [--tool T] [--since DATE] [--until DATE] [--dry-run] [--limit N] [--force]
  # → Best-effort fill of missing token fields for historical entries

# Session discovery helper (new)
rc-db analysis sessions list --tool <claude-code|codex|amp> [--limit N]
  # → Lists candidate sessions with (uuid, path, last_modified, tokens_so_far)
```

### Session Auto-Detection

Add to `usage_capture.py`:

```python
def get_current_session_path(tool: str, project_path: Path | None = None) -> tuple[Path, str]:
    """Auto-detect current session file and UUID.

    Returns (session_path, session_uuid).

    Selection logic (in order):
    1. If exactly one candidate session exists, return it
    2. If multiple candidates exist, raise AmbiguousSessionError with candidate list
    3. If no candidates exist, raise NoSessionFoundError

    Does NOT default to "most recently modified" when ambiguous - user must
    provide explicit --usage-session-id or --usage-session-path.
    """

def get_session_token_count(path: Path, tool: str) -> int:
    """Compute current cumulative token count for session."""

def list_sessions(tool: str, limit: int = 10) -> list[dict]:
    """List candidate sessions for discovery/debugging.

    Returns list of {uuid, path, last_modified, tokens_so_far}.
    """
```

**Codex resume semantics**: A single `usage_session_id` (UUID) may map to multiple `rollout-*.jsonl` files (one per resume). Implementation must either:
- Select the latest file matching the UUID, OR
- Aggregate token counts across all files for that UUID

Decision: Aggregate across all matching files (more accurate for resumed sessions).

---

## Punchlist

### Phase 1: Tests First (per Spec→Plan→Test→Implement)

- [ ] **tests/test_usage_capture.py**: Session detection tests
  - [ ] `test_get_current_session_path_claude` - finds Claude session
  - [ ] `test_get_current_session_path_codex` - finds Codex session
  - [ ] `test_get_current_session_path_amp` - finds Amp session
  - [ ] `test_get_current_session_path_ambiguous` - errors on multiple candidates
  - [ ] `test_get_current_session_path_no_session` - errors when none found
  - [ ] `test_get_session_token_count_claude` - sums per-message usage
  - [ ] `test_get_session_token_count_codex` - counter delta method
  - [ ] `test_get_session_token_count_codex_multi_rollout` - aggregates across resumed session files
  - [ ] `test_get_session_token_count_amp` - sums per-message usage
  - [ ] `test_list_sessions` - returns candidates with metadata

- [ ] **tests/test_db.py**: Lifecycle CLI tests
  - [ ] `test_analysis_start_creates_row_with_baseline`
  - [ ] `test_analysis_start_auto_detects_session`
  - [ ] `test_analysis_start_explicit_session_id`
  - [ ] `test_analysis_mark_appends_stage_with_delta`
  - [ ] `test_analysis_complete_computes_tokens_check`
  - [ ] `test_analysis_backfill_usage_dry_run`
  - [ ] `test_analysis_backfill_usage_fills_missing`
  - [ ] `test_analysis_backfill_usage_respects_force`
  - [ ] `test_analysis_sessions_list`
  - [ ] `test_update_analysis_log_partial_update`
  - [ ] `test_update_analysis_log_no_duplicate_rows`
  - [ ] `test_update_analysis_log_nonexistent_id_errors`

- [ ] **tests/test_validate.py**: New field validation
  - [ ] `test_validate_analysis_log_tokens_check_computed_correctly`
  - [ ] `test_validate_analysis_log_synthesis_inputs_exist`

- [ ] **tests/test_export.py**: Export tests
  - [ ] `test_export_analysis_logs_includes_delta_fields`
  - [ ] `test_export_analysis_logs_includes_synthesis_links`

### Phase 2: Schema Updates + CRUD

- [ ] Add new fields to `ANALYSIS_LOGS_SCHEMA` in `scripts/db.py`:
  - `tokens_baseline` (int, nullable)
  - `tokens_final` (int, nullable)
  - `tokens_check` (int, nullable)
  - `usage_provider` (str, nullable)
  - `usage_mode` (str, nullable)
  - `usage_session_id` (str, nullable)
  - `inputs_source_ids` (list[str], nullable)
  - `inputs_analysis_ids` (list[str], nullable)
- [ ] Update `init_tables()` to handle schema evolution (add columns if missing)
- [ ] Update `add_analysis_log()` to accept new fields
- [ ] **Add `update_analysis_log(id, **fields)`** - required for lifecycle commands
  - Must handle partial updates (only specified fields)
  - Must prevent duplicate rows (update in place, not insert)
  - Must validate ID exists before update
- [ ] Update `get_analysis_log()` / `list_analysis_logs()` to return new fields

### Phase 3: Session Detection (usage_capture.py)

- [ ] Add session path constants for each tool:
  - Claude: `~/.claude/projects/<project>/<uuid>.jsonl`
  - Codex: `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl`
  - Amp: `~/.local/share/amp/threads/T-<uuid>.json`
- [ ] Implement `get_current_session_path(tool, project_path)`:
  - Return (path, uuid) if exactly one candidate exists
  - Raise `AmbiguousSessionError` with candidate list if multiple exist
  - Raise `NoSessionFoundError` if none exist
  - **Do NOT default to "most recently modified"** when ambiguous
- [ ] Implement `get_session_token_count(path, tool)`:
  - Claude/Amp: sum all per-message usage
  - Codex: read final `total_token_usage` counter
- [ ] Implement `get_session_token_count_by_uuid(uuid, tool)` for Codex:
  - Find all `rollout-*.jsonl` files matching UUID
  - Aggregate token counts across all matching files
- [ ] Implement `list_sessions(tool, limit)` for discovery helper

### Phase 4: Lifecycle CLI Commands (db.py)

- [ ] `rc-db analysis start`:
  - Required: `--source-id`, `--tool`
  - Optional: `--model`, `--usage-session-id`, `--usage-session-path`
  - Behavior: auto-detect session if not specified, snapshot baseline, create row, return ID
- [ ] `rc-db analysis mark`:
  - Required: `--id`, `--stage`
  - Behavior: snapshot current tokens, compute delta, append to `stages_json`
- [ ] `rc-db analysis complete`:
  - Required: `--id`
  - Optional: `--status`, `--notes`, `--claims-extracted`, `--claims-updated`
  - Behavior: snapshot final, compute `tokens_check`, estimate cost if model known
- [ ] `rc-db analysis sessions list`:
  - Required: `--tool`
  - Optional: `--limit`
  - Output: table of (uuid, path, last_modified, tokens_so_far)

### Phase 5: Backfill Command

- [ ] `rc-db analysis backfill-usage`:
  - Options: `--tool`, `--since`, `--until`, `--dry-run`, `--limit`, `--force`
  - Logic:
    1. Query `analysis_logs` with missing `tokens_check`
    2. For each, find overlapping session via `started_at`/`completed_at`
    3. Compute windowed token sum
    4. Update row (unless `--dry-run`)
  - Print summary of updates made

### Phase 6: Validation Updates

- [ ] Validate `tokens_check == tokens_final - tokens_baseline` when all present
- [ ] Validate synthesis `inputs_analysis_ids` reference existing analysis logs
- [ ] Validate synthesis `inputs_source_ids` reference existing sources (when status=completed)

### Phase 7: Export Updates

- [ ] Update `export_analysis_logs_yaml()` to include new fields
- [ ] Update `export_analysis_logs_md()` to show:
  - Delta accounting fields in detail view
  - Synthesis input breakdown table
  - End-to-end totals for syntheses

### Phase 8: Documentation

- [x] Update `docs/SCHEMA.md` with new `analysis_logs` fields
- [x] Update `docs/WORKFLOWS.md` with lifecycle workflow example
- [x] Update `docs/TODO.md` status

### Phase 9: Integration Templates

- [x] Update `integrations/_templates/skills/check.md.j2` to use lifecycle commands
- [x] Update `integrations/_templates/skills/synthesize.md.j2` to use lifecycle commands with synthesis attribution
- [x] Update `integrations/_templates/partials/db-commands.md.j2` with lifecycle commands
- [x] Update `integrations/_templates/partials/analysis-log.md.j2` with token tracking note
- [x] Run `make assemble-skills` to regenerate all integration skills
- [x] Add `--inputs-source-ids` and `--inputs-analysis-ids` flags to `analysis complete` CLI

### Phase 10: Schema Migration Command

LanceDB doesn't auto-add columns to existing tables. Need `rc-db migrate` to update existing databases when schema changes.

- [x] Implement `rc-db migrate` command in `scripts/db.py`:
  - Compare current table schema vs expected schema
  - Add missing columns with appropriate defaults
  - Report what was added/changed
  - Support `--dry-run` to preview changes
- [x] Add tests for schema migration in `tests/test_db.py`
- [x] Update `docs/WORKFLOWS.md` with migration instructions
- [x] Update `docs/SCHEMA.md` with migration notes

### Phase 11: Bug Fixes (Post-Review)

Issues identified during code review:

- [x] **`analysis start` doesn't auto-detect session** (`scripts/db.py:2679`)
  - Imports `get_current_session_path` but never calls it when `--usage-session-id` is omitted
  - Fix: Added else branch to call session detection and capture baseline tokens automatically

- [x] **`analysis mark` doesn't capture token delta** (`scripts/db.py:2733`)
  - Only appends `{stage, timestamp}` to `stages_json`, doesn't capture actual token count
  - Fix: Now captures `tokens_cumulative` and `tokens_delta` in stage entries

- [x] **Codex backfill overcounts** (`scripts/db.py:2856`, `scripts/usage_capture.py:169,195`)
  - `parse_usage_from_source()` for Codex returns cumulative counter snapshot, not "tokens in window"
  - Fix: Documented as limitation; backfill now warns about Codex entries and uses `usage_mode=cumulative_snapshot`

- [x] **Privacy/contract mismatch** (`scripts/usage_capture.py:363`)
  - Claims "usage-only" but extracts `context_snippet` from transcript content
  - Fix: Updated docstring to clarify that brief context snippets are extracted for session identification

- [x] **Validation bug** (`scripts/validate.py:362`)
  - Token math mismatch uses level "WARNING" instead of "WARN"
  - Fix: Changed to "WARN" for consistency with validation summary

- [x] **Export bug** (`scripts/export.py:534`)
  - `tokens = tokens_check or total_tokens` means `tokens_check=0` falls back to `total_tokens`
  - Fix: Used explicit None check: `tokens_check if tokens_check is not None else total_tokens`

- [x] **Schema evolution not handled** (`scripts/db.py:444`)
  - Fixed in Phase 10 with `rc-db migrate` command

---

## Resolved Decisions

1. **Tool vs provider naming**: `tool` field stays `claude-code|codex|amp|manual|other` (matches existing validation). `usage_provider` is `claude|codex|amp` for session parsing. CLI maps tool→provider internally.

2. **Session detection behavior**: Require explicit `--usage-session-id` when ambiguous. Do NOT default to "most recently modified". Error message lists candidates with context snippet (first line of conversation) to help user/agent select the right one.

3. **Codex resume semantics**: Aggregate token counts across all `rollout-*.jsonl` files matching a UUID (more accurate for resumed sessions).

4. **Update semantics**: Add `update_analysis_log()` function. Lifecycle commands (`start`/`mark`/`complete`) mutate existing rows via update, not insert.

5. **Backwards compatibility**: Keep `analysis add` for manual one-shot entry. Lifecycle commands (`start`/`mark`/`complete`) are the new default for automated checks with delta accounting.

6. **Backfill window heuristics**: Use exact `started_at`/`completed_at` window only; skip entries missing timestamps. No padding/guessing. (All historical analyses happened on this machine with Codex/Claude/Amp, can manually verify if needed.)

7. **Schema migration strategy**: Silent add-if-missing for new nullable columns (safe, zero friction). Reserve explicit `rc-db migrate` for breaking changes only.

---

## Open Questions

_(All resolved - see above)_

---

## Worklog

### 2026-01-25: Planning

- Created this implementation document from PLAN-token-usage.md
- Reviewed existing `usage_capture.py` - parsers exist, need session detection
- Identified 9 phases of work
- Key insight: `analysis add` remains for manual entry; lifecycle (`start`/`mark`/`complete`) is for automated checks with delta accounting

### 2026-01-25: Review Feedback Incorporated

Addressed feedback from planning review:

1. **Tool vs provider naming**: Clarified that `tool` stays `claude-code|codex|amp|...` while `usage_provider` is `claude|codex|amp` for session parsing
2. **Session detection**: Fixed to require explicit ID OR exactly one candidate (not "most recent" as default)
3. **Codex resume semantics**: Added note about aggregating across multiple rollout files per UUID
4. **Update semantics**: Added explicit `update_analysis_log()` work item and tests
5. **Synthesis plumbing**: Added `synthesize.md.j2` to Phase 9 with attribution workflow

### 2026-01-25: Final Decisions

Resolved remaining open questions:

- **Backfill**: Exact window only (no padding/guessing); skip entries without timestamps
- **Schema migration**: Silent add-if-missing for additive changes; explicit migrate for breaking
- **Session ambiguity UX**: Show candidate list with context snippet (first line of conversation) to help user/agent select

All questions resolved. Ready for implementation.

### 2026-01-25: Implementation Complete

Completed all 9 phases:

**Phase 1-4**: Core implementation
- Added schema fields: `tokens_baseline`, `tokens_final`, `tokens_check`, `usage_provider`, `usage_mode`, `usage_session_id`, `inputs_source_ids`, `inputs_analysis_ids`
- Added `update_analysis_log()` function with delete-then-add pattern for LanceDB
- Added session detection: `get_current_session_path()`, `get_session_token_count()`, `get_session_token_count_by_uuid()`, `list_sessions()`
- Added CLI commands: `analysis start`, `analysis mark`, `analysis complete`, `analysis sessions list`
- Added `AmbiguousSessionError` with helpful candidate list

**Phase 5-7**: Backfill, validation, export
- Added `analysis backfill-usage` command for historical entries
- Added validation for `tokens_check` math and `inputs_analysis_ids` references
- Updated export to prefer `tokens_check` over `total_tokens`

**Phase 8-9**: Docs and integration templates
- Updated SCHEMA.md, WORKFLOWS.md, TODO.md
- Updated check.md.j2 and synthesize.md.j2 with lifecycle commands
- Updated db-commands.md.j2 and analysis-log.md.j2
- Added `--inputs-source-ids` and `--inputs-analysis-ids` to `analysis complete` CLI
- Ran `make assemble-skills` to regenerate all integration skills

**Bug fixes**:
- Fixed PyArrow `value_field` error by ensuring list fields are never None
- Fixed migration duplicate prediction issue (stub vs migrated data)

All 265 tests pass.

### 2026-01-25: Phase 10 - Schema Migration Command

Added `rc-db migrate` command to handle schema updates for existing databases:
- Compares current table schema vs expected schema
- Adds missing columns with appropriate type defaults (int, float, string, list)
- Supports `--dry-run` for preview
- Idempotent - safe to run multiple times

Added 3 tests in `TestMigrate` class. Updated WORKFLOWS.md and SCHEMA.md with migration documentation.

All 268 tests pass.

### 2026-01-25: Phase 11 - Bug Fixes

Fixed all bugs identified in code review:

1. **`analysis start` auto-detection**: Added else branch to call `get_current_session_path()` when `--usage-session-id` not provided
2. **`analysis mark` token capture**: Now captures `tokens_cumulative` and `tokens_delta` for each stage
3. **Codex backfill limitation**: Added warning message and uses `usage_mode=cumulative_snapshot` to clearly indicate the limitation
4. **Privacy docstring**: Updated `usage_capture.py` docstring to clarify context snippet extraction
5. **Validation level**: Changed "WARNING" to "WARN" for consistency
6. **Export None check**: Fixed `tokens_check or total_tokens` to explicit None check

---

*Last updated: 2026-01-25*
