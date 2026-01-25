# Implementation: Token Usage Capture & Backfill

**Status**: Planning
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
 ├── UPDATE _templates/skills/check.md.j2    # Use lifecycle commands
 └── regenerate all skills via `make assemble-skills`
```

## What Already Exists (from audit-log implementation)

- `analysis_logs` table with: `id`, `source_id`, `pass`, `status`, `tool`, `model`, `tokens_in`, `tokens_out`, `total_tokens`, `cost_usd`, `stages_json`, etc.
- `usage_capture.py` with `parse_usage_from_source()` for Claude/Codex/Amp
- `--usage-from <provider>:<path>` flag on `rc-db analysis add`
- Cost estimation via `--estimate-cost` and pricing table

## New Functionality Required

### Schema Additions

Add to `analysis_logs`:

| Field | Type | Description |
|-------|------|-------------|
| `tokens_baseline` | int (nullable) | Session token count at check start |
| `tokens_final` | int (nullable) | Session token count at check end |
| `tokens_check` | int (nullable) | Total tokens for this check (final - baseline) |
| `usage_provider` | str (nullable) | Provider: claude\|codex\|amp\|manual\|other |
| `usage_mode` | str (nullable) | Method: per_message_sum\|windowed_sum\|counter_delta\|manual |
| `usage_session_id` | str (nullable) | Session UUID (portable, no full paths) |
| `inputs_source_ids` | list[str] (nullable) | Source IDs feeding a synthesis (synthesis-only) |
| `inputs_analysis_ids` | list[str] (nullable) | Analysis log IDs feeding a synthesis (synthesis-only) |

### New CLI Commands

```bash
# Lifecycle commands (new)
rc-db analysis start --source-id <id> --tool <claude|codex|amp> [--model M] [--usage-session-id UUID]
  # → Returns ANALYSIS-YYYY-NNN; captures baseline snapshot

rc-db analysis mark --id <id> --stage <stage-name>
  # → Snapshots current tokens, appends to stages_json

rc-db analysis complete --id <id> [--status completed|failed] [--notes "..."]
  # → Snapshots final tokens, computes tokens_check

# Backfill command (new)
rc-db analysis backfill-usage [--tool T] [--since DATE] [--until DATE] [--dry-run] [--limit N] [--force]
  # → Best-effort fill of missing token fields for historical entries

# Session discovery helper (new)
rc-db analysis sessions list --tool <claude|codex|amp> [--limit N]
  # → Lists candidate sessions with (uuid, path, last_modified, tokens_so_far)
```

### Session Auto-Detection

Add to `usage_capture.py`:

```python
def get_current_session_path(tool: str) -> tuple[Path, str]:
    """Auto-detect current session file and UUID.

    Returns (session_path, session_uuid).
    Raises if no session found or multiple ambiguous candidates.
    """

def get_session_token_count(path: Path, tool: str) -> int:
    """Compute current cumulative token count for session."""
```

---

## Punchlist

### Phase 1: Tests First (per Spec→Plan→Test→Implement)

- [ ] **tests/test_usage_capture.py**: Session detection tests
  - [ ] `test_get_current_session_path_claude` - finds Claude session
  - [ ] `test_get_current_session_path_codex` - finds Codex session
  - [ ] `test_get_current_session_path_amp` - finds Amp session
  - [ ] `test_get_current_session_path_ambiguous` - errors on multiple candidates
  - [ ] `test_get_session_token_count_claude` - sums per-message usage
  - [ ] `test_get_session_token_count_codex` - counter delta method
  - [ ] `test_get_session_token_count_amp` - sums per-message usage

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

- [ ] **tests/test_validate.py**: New field validation
  - [ ] `test_validate_analysis_log_tokens_check_computed_correctly`
  - [ ] `test_validate_analysis_log_synthesis_inputs_exist`

- [ ] **tests/test_export.py**: Export tests
  - [ ] `test_export_analysis_logs_includes_delta_fields`
  - [ ] `test_export_analysis_logs_includes_synthesis_links`

### Phase 2: Schema Updates

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
- [ ] Update `get_analysis_log()` / `list_analysis_logs()` to return new fields

### Phase 3: Session Detection (usage_capture.py)

- [ ] Add session path constants for each tool:
  - Claude: `~/.claude/projects/<project>/<uuid>.jsonl`
  - Codex: `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl`
  - Amp: `~/.local/share/amp/threads/T-<uuid>.json`
- [ ] Implement `get_current_session_path(tool)`:
  - Find most recently modified session file
  - Extract UUID from filename
  - Return (path, uuid) or raise on ambiguity
- [ ] Implement `get_session_token_count(path, tool)`:
  - Claude/Amp: sum all per-message usage
  - Codex: read final `total_token_usage` counter
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

- [ ] Update `docs/SCHEMA.md` with new `analysis_logs` fields
- [ ] Update `docs/WORKFLOWS.md` with lifecycle workflow example
- [ ] Update `docs/TODO.md` status

### Phase 9: Integration Templates

- [ ] Update `integrations/_templates/skills/check.md.j2` to use lifecycle commands:
  ```bash
  ANALYSIS_ID=$(rc-db analysis start --source-id "$SOURCE_ID" --tool claude)
  # ... stage 1 ...
  rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage1
  # ... stage 2 ...
  rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage2
  # ... stage 3 ...
  rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage3
  # ... register claims ...
  rc-db analysis complete --id "$ANALYSIS_ID" --status completed
  ```
- [ ] Run `make assemble-skills` to regenerate all integration skills

---

## Resolved Decisions

_(None yet - document decisions as they're made)_

---

## Open Questions

1. **Session detection edge case**: What happens if user has multiple terminal sessions active?
   - Proposed: Require explicit `--usage-session-id` when ambiguous (error message lists candidates)

2. **Backfill window heuristics**: How much padding around `started_at`/`completed_at`?
   - Proposed: Use exact window if timestamps present; skip entry if missing

3. **Schema migration**: How to add new columns to existing `analysis_logs` tables?
   - Proposed: LanceDB supports adding columns; wrap in try/except for existing DBs

4. **Backwards compatibility**: Should `analysis add` continue working for manual one-shot entry?
   - Proposed: Yes, keep `analysis add` for manual entries; lifecycle commands are the new default for automated checks

---

## Worklog

### 2026-01-25: Planning

- Created this implementation document from PLAN-token-usage.md
- Reviewed existing `usage_capture.py` - parsers exist, need session detection
- Identified 9 phases of work
- Key insight: `analysis add` remains for manual entry; lifecycle (`start`/`mark`/`complete`) is for automated checks with delta accounting

---

*Last updated: 2026-01-25*
