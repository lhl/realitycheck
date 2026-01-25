# Plan: Token Usage Capture & Backfill

**Status**: Planning
**Created**: 2026-01-25
**Updated**: 2026-01-25

## Motivation

Reality Check's `analysis_logs` table includes optional token/cost fields (`tokens_in`, `tokens_out`, `total_tokens`, `cost_usd`), but in practice many entries are missing them.

We *can* extract usage totals from local tool session logs (Claude Code, Codex CLI, Amp), but today this is:

- **manual**: `rc-db analysis add` requires explicit `--usage-from ...` and (optionally) time windows
- **inconsistent**: many analyses don't record run start/end timestamps, so "this check's tokens" is ambiguous
- **not backfilled**: existing `analysis_logs` rows remain `?` even when local usage data exists

This plan defines:

1. **Default capture** for new checks (tokens by default, with minimal friction).
2. **Backfill** for existing `analysis_logs` rows.
3. (Optional) **Per-stage** token deltas for check stages and workflow steps.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Session** | The tool's conversation context, identified by UUID. One session file per terminal instance. Resumes continue the same session. |
| **Check** | One Reality Check analysis run (the unit we're tracking tokens for). A session may contain multiple checks. |
| **Synthesis** | One cross-source synthesis run (typically produced after 2+ checks). A session may contain multiple syntheses. |
| **Stage** | A step within a run (check or synthesis). Stages should be namespaced: `check_stage1`, `check_stage2`, `check_stage3`, `check_register`, `check_validate`, `synthesize_draft`, `synthesize_revision`, etc. |

---

## Session Storage Reference

### Where Session Files Live

| Tool | Path Pattern | Session ID Format |
|------|--------------|-------------------|
| Claude Code | `~/.claude/projects/<project-path>/<uuid>.jsonl` | UUID v4 (e.g., `0c502700-ae37-4047-a0cb-e541897dae9d`) |
| Codex CLI | `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl` | UUID in filename |
| Amp | `~/.local/share/amp/threads/T-<uuid>.json` | UUID in filename |

### Session Semantics

- **Claude Code**: One `.jsonl` file per session. **Resume continues the same file** (same UUID). Sessions can span multiple days.
- **Codex**: Session logs are stored as `rollout-*.jsonl` files (UUID in filename). Resume should continue the same session UUID; confirm whether it appends to the same file or creates a new rollout file for the same UUID.
- **Amp**: Each thread is a session, stored as a single JSON file.

### Current Session Auto-Detection

At any moment, the "current session" can be identified.

However, **"most recently modified file" is only a heuristic**, and is unsafe when multiple sessions are active (multiple terminals, concurrent runs, etc.).

**Recommendation**:

- `analysis start` should capture and persist `usage_session_id` (and the resolved session file path internally) so later `mark/complete` calls do not rely on heuristics.
- When auto-detection finds multiple plausible candidates, the CLI should **refuse** and print a short candidate list, requiring explicit selection.

Proposed explicit overrides (CLI flags and/or env vars):

- `--usage-session-id <uuid>` (preferred)
- `--usage-session-path <path>` (fallback)
- `REALITYCHECK_USAGE_SESSION_ID` / `REALITYCHECK_USAGE_SESSION_PATH` (for integrations)

Proposed manual check / selection helper (for humans and debugging):

- `rc-db analysis sessions list --tool <claude|codex|amp> [--limit N]`
  - prints candidate sessions with `(usage_session_id, path, last_seen, total_tokens_so_far)`
  - user can re-run `analysis start` with `--usage-session-id ...`

### Token Data Location by Tool

| Tool | Location in Session File | Structure |
|------|--------------------------|-----------|
| Claude Code | Per-message: `message.usage` | `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` |
| Codex CLI | `event_msg` with `payload.type=token_count` | `total_token_usage` (cumulative), `last_token_usage` (per-turn) |
| Amp | Per-message: `messages[i].usage` | `inputTokens`, `outputTokens`, `cacheCreationInputTokens`, `cacheReadInputTokens`, `totalInputTokens`, `credits` |

---

## Delta Accounting Approach

Since a session may contain multiple checks (or non-check work), we use **delta accounting**:

```
check_start:      baseline = get_session_token_count()
check_stage1:     stage1_end = get_session_token_count()
check_stage2:     stage2_end = get_session_token_count()
check_stage3:     stage3_end = get_session_token_count()
check_end:        final = get_session_token_count()

# Computed values:
check_total_tokens = final - baseline
stage1_tokens = stage1_end - baseline
stage2_tokens = stage2_end - stage1_end
stage3_tokens = stage3_end - stage2_end
```

### Token Count Methods by Tool

| Tool | Method | Notes |
|------|--------|-------|
| Claude Code | **Per-message sum** | Sum all `message.usage` entries in file up to current point |
| Codex CLI | **Windowed sum** OR **counter delta** | Sum `last_token_usage` per event in window, OR read `total_token_usage` and compute delta |
| Amp | **Per-message sum** | Sum all `messages[i].usage` entries up to current point |

**Codex note**: Codex emits both `total_token_usage` (cumulative) and `last_token_usage` (per-turn). Windowed sum of `last_token_usage` is preferred for stage-level granularity; counter delta on `total_token_usage` works for check-level totals.

### Why This Works

As long as we know which session we're in (trivially auto-detected), computing check token count is:

1. **At check start**: snapshot current session tokens → `baseline`
2. **At check end**: snapshot current session tokens → `final`
3. **Check tokens** = `final - baseline`

This holds regardless of what else happened in the session before the check started.

Critically, it also supports **multiple runs in one session**:

- Each run gets its own `baseline` snapshot at run start.
- Each run’s tokens are a delta against that baseline.

## Goals

- Make tokens/cost fields "present by default" for new `analysis_logs` entries via automatic session detection.
- Enable **repeatable backfills** for existing `analysis_logs` entries.
- Support tool-appropriate accounting:
  - **Per-message sums** (Claude Code, Amp)
  - **Windowed sums / counter deltas** (Codex)
- Enable (optional) **per-stage** token deltas (`check_stage1`, `check_stage2`, `check_stage3`, `check_register`, etc.).

## Non-goals (v1)

- Storing transcripts, prompts, or tool call content in the database.
- Perfect disambiguation across overlapping sessions on different machines (backfill is local-machine best-effort).
- Billing-accurate cost ingestion from vendor dashboards (we estimate cost when model+pricing is known).

## Requirements

### Functional

- **Default capture**: `rc-db analysis start/complete` automatically detects current session and computes deltas.
- **Backfill**: CLI workflow to fill missing `tokens_*` fields for existing analysis logs.
- **Stage accounting** (optional): per-stage token deltas in `analysis_logs.stages_json`.

### UX

- "Happy path" requires no manual session file discovery - auto-detection handles it.
- Output is explainable: record baseline, final, and computation method.

### Privacy / data hygiene

- Usage capture remains **usage-only** (no transcript retention); this matches `scripts/usage_capture.py`.
- No transcript snippets are persisted for boundary inference.

## Proposed Design

### A) Schema additions to `analysis_logs`

Add fields to support delta accounting and provenance:

```yaml
# Token accounting
tokens_baseline: 45000           # session tokens at check start
tokens_final: 58500              # session tokens at check end
tokens_check: 13500              # total for this check (final - baseline)

# Provenance
usage_provider: "claude"         # claude|codex|amp|manual|other
usage_mode: "per_message_sum"    # per_message_sum|windowed_sum|counter_delta|cumulative_snapshot|manual
usage_session_id: "0c502700..."  # session UUID (not full path)

# Per-stage breakdown (optional, in stages_json)
stages_json: |
  [
    {"stage": "check_stage1", "tokens_delta": 4200, "tokens_in": 3500, "tokens_out": 700},
    {"stage": "check_stage2", "tokens_delta": 5100, "tokens_in": 4200, "tokens_out": 900},
    {"stage": "check_stage3", "tokens_delta": 3800, "tokens_in": 3000, "tokens_out": 800},
    {"stage": "check_register", "tokens_delta": 400, "tokens_in": 350, "tokens_out": 50}
  ]
```

Rationale:
- `tokens_baseline` + `tokens_final` make computation reproducible/auditable.
- `usage_session_id` is portable (no absolute paths); sufficient to identify session.
- `usage_mode` documents how the numbers were computed.

### A2) Multi-source + synthesis attribution

For multi-source workflows, we want audit logs to support both:

1) **Per-source accountability** (each source analysis has its own detailed stage-level log), and  
2) **End-to-end synthesis totals** (a synthesis can report “total tokens spent on inputs + synthesis work”).

Proposed linking fields (schema + export):

- `inputs_source_ids`: list of source IDs included in a synthesis (optional; synthesis-only)
- `inputs_analysis_ids`: list of `analysis_logs.id` values for the source analyses that feed a synthesis (optional; synthesis-only)

Human-facing rendering requirement (synthesis analysis markdown):

- The synthesis audit log should include an “Inputs” table listing each source analysis (ID + tokens/cost).
- It should then show the synthesis run’s own stage token deltas.
- It should include a “Total end-to-end” line equal to:
  - `sum(tokens_check for inputs_analysis_ids) + tokens_check for synthesis run`

Note: If input source analyses are backfilled later (tokens were previously unknown), synthesis totals should be refreshable (e.g., by re-running a “refresh audit log” operation that rewrites the in-document tables from DB).

### B) Check lifecycle CLI commands

Add lifecycle commands that handle session detection and delta computation automatically:

```bash
# At check start: auto-detect session, snapshot baseline, create analysis_logs row
rc-db analysis start --source-id <source-id> --tool <claude|codex|amp> [--model ...]
# Returns: ANALYSIS-2026-NNN

# Optional: record stage boundaries for per-stage breakdown
rc-db analysis mark --id ANALYSIS-2026-NNN --stage check_stage1
rc-db analysis mark --id ANALYSIS-2026-NNN --stage check_stage2
# etc.

# At check end: snapshot final, compute deltas, update row
rc-db analysis complete --id ANALYSIS-2026-NNN [--status completed|failed] [--notes ...]
```

**`analysis start`**:
1. Determine session (prefer `--usage-session-id`/`--usage-session-path`; otherwise auto-detect and fail if ambiguous)
2. Compute current session token count (method depends on tool)
3. Store as `tokens_baseline` in new `analysis_logs` row
4. Return the new `ANALYSIS-YYYY-NNN` ID

**`analysis mark`** (optional):
1. Snapshot current token count
2. Compute delta from previous snapshot
3. Append to `stages_json`

**`analysis complete`**:
1. Snapshot final token count
2. Compute `tokens_check = final - baseline`
3. Optionally estimate cost from model pricing table
4. Update row with `status`, `completed_at`, token fields

### C) Session token count implementation by tool

**Claude Code / Amp** (per-message sum):
```python
def get_session_tokens(session_path: Path) -> int:
    total = 0
    for line in session_path.open():
        obj = json.loads(line)
        usage = obj.get("message", {}).get("usage") or obj.get("usage")
        if usage:
            total += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            total += usage.get("cache_creation_input_tokens", 0)
            total += usage.get("cache_read_input_tokens", 0)
    return total
```

**Codex CLI** (windowed sum of `last_token_usage`):
```python
def get_session_tokens(session_path: Path, since_timestamp: str = None) -> int:
    total = 0
    for line in session_path.open():
        obj = json.loads(line)
        if since_timestamp and obj.get("timestamp", "") < since_timestamp:
            continue
        info = obj.get("payload", {}).get("info", {})
        last = info.get("last_token_usage", {})
        if last:
            total += last.get("input_tokens", 0) + last.get("cached_input_tokens", 0)
            total += last.get("output_tokens", 0) + last.get("reasoning_output_tokens", 0)
    return total
```

**Codex alternative** (counter delta on `total_token_usage`):
- Read `total_token_usage.total_tokens` at start and end
- Delta = end - start

### D) Backfill workflow for existing logs

Add a command to backfill missing token fields for historical analysis logs:

```bash
rc-db analysis backfill-usage [--tool claude|codex|amp] [--since ...] [--until ...] [--dry-run] [--limit N] [--force]
```

Backfill heuristics (best-effort):
1. Use `started_at` and `completed_at` if present to define the window
2. Fall back to `created_at` ± padding if timestamps missing
3. Search local session files for sessions overlapping the window
4. Compute windowed token sums for that window
5. Record `usage_provider`, `usage_mode`, and session ID

**Note**: Backfill is inherently best-effort when baseline wasn't recorded at check start. For accurate accounting, use `analysis start/complete` going forward.

### E) Integration updates (skills/workflows)

Update `$check` workflow templates to use lifecycle commands:

```bash
# Example check workflow with token tracking
ANALYSIS_ID=$(rc-db analysis start --source-id "$SOURCE_ID" --tool claude --model "$MODEL")

# Stage 1: Descriptive
# ... do stage 1 work ...
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage1

# Stage 2: Evaluative
# ... do stage 2 work ...
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage2

# Stage 3: Dialectical
# ... do stage 3 work ...
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage3

# Register claims
# ... registration ...
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_register

# Finalize
rc-db analysis complete --id "$ANALYSIS_ID" --status completed --notes "..."
```

This makes token capture automatic and consistent across Claude Code, Codex, and Amp.

---

## Tests (must be written first)

### `tests/test_usage_capture.py`
- Session auto-detection by tool (finds correct file)
- Claude/Amp: per-message sum correctness
- Codex: windowed sum of `last_token_usage` correctness
- Codex: counter delta on `total_token_usage` correctness

### `tests/test_db.py`
- `analysis start` creates row with baseline, returns ID
- `analysis mark` appends to `stages_json` with correct delta
- `analysis complete` computes `tokens_check = final - baseline`
- `analysis backfill-usage` updates only missing fields (unless `--force`)

### `tests/test_export.py`
- Exports include new token accounting fields (`tokens_baseline`, `tokens_final`, `tokens_check`)
- Exports include `stages_json` when present

---

## Implementation Plan (Spec → Plan → Test → Implement)

1. **Spec**: Finalize this plan ✓
2. **Tests**: Add unit tests for:
   - Session auto-detection per tool
   - Token counting methods (per-message sum, windowed sum, counter delta)
   - Lifecycle commands (`start/mark/complete`)
   - Backfill command
3. **Implement**:
   - Add `get_current_session_path(tool)` and `get_session_token_count(path, tool)` to `usage_capture.py`
   - Extend `analysis_logs` schema with new fields
   - Implement `analysis start/mark/complete` subcommands in `db.py`
   - Implement `analysis backfill-usage` subcommand
   - Update export/validate for new fields
4. **Integrations**: Update skill templates and regenerate (`make assemble-skills`)

---

## Risks / Notes

- **Codex windowed sum vs counter delta**: Prefer windowed sum of `last_token_usage` for stage-level granularity. Counter delta works for check-level totals but loses per-stage breakdown.
- **Session detection edge cases**: Multiple terminal instances could have overlapping sessions. The "most recently modified" heuristic is a fallback only; prefer explicit `usage_session_id` capture at `analysis start`, and require explicit selection when ambiguous.
- **Backfill accuracy**: Without recorded baseline, backfill must estimate the window. Results are best-effort.
- **Path portability**: Store session UUID only (not full path) in the database for portability across machines.
