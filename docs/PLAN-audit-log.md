# Plan: Analysis Audit Log

**Status**: Planning
**Created**: 2026-01-22

## Motivation

Reality Check produces analysis markdown files and registers claims/sources to LanceDB, but we do not yet have a **standard, queryable provenance record** for *how* an analysis was produced (who/what/when/with which tool/model/methodology, what changed, and what it cost).

Today, provenance is split across:
- chat transcripts (hard to search and not durable)
- git history (helpful, but not structured for cost/tokens/model attribution)
- ad hoc notes in analysis documents (inconsistent)

An **analysis audit log** provides a durable, structured record that is:
- **human-readable** (embedded in the analysis document)
- **machine-queryable** (stored in the database for reporting)
- **tool-agnostic** (works across Claude Code, Codex, Amp, manual workflows)

## Goals

- Standardize per-analysis provenance without relying on commit-message footers.
- Support **multi-pass / continuation** analyses with clear pass history.
- Enable **cost + token usage reporting** (when available; optional otherwise).
- Make audit metadata **exportable** for sharing and reporting.
- Add integrity validation so audit references (source/claim IDs) stay consistent.

## Non-goals (for v1)

- Storing full prompts, tool transcripts, or source text (privacy + size).
- Enforcing analysis quality/structure (handled by `docs/PLAN-quality-regression-fix.md`).
- Building a full tracing system for every tool call (possible later via Agent SDK/MCP).

## Definitions

- **Analysis document**: `analysis/sources/<source-id>.md` in a data repo.
- **Analysis run**: one pass that creates or updates an analysis document and (optionally) registers claims/sources.
- **Stage**: the three Reality Check stages: descriptive / evaluative / dialectical.

## Requirements

### Functional

- Create, list, and fetch audit log entries by ID and by `source_id`.
- Record, at minimum:
  - `source_id`
  - timestamps (start/end) and duration
  - tool/integration attribution (Claude Code / Codex / Amp / manual)
  - model(s) when known
  - framework/methodology version markers when feasible
  - claim IDs extracted/registered (when applicable)
  - freeform notes (what changed)
- Work when token/cost numbers are **unknown** (nullable fields).
- Prefer append-only history: new run = new log row.

### Data integrity

- When a run is marked `completed`, `source_id` should exist in `sources`.
- When claim IDs are listed, they should exist in `claims` (or the log should have `status=draft`).
- Audit logs must be exportable (YAML/Markdown) without requiring DB access.

### UX / workflow fit

- Minimal “happy path” friction: one `rc-db analysis add ...` call at the end of `/check`.
- Provide a standard “Analysis Log” section to append to the analysis markdown file.

## Proposed Design

### 1) In-document Analysis Log (human-facing)

Append this section at the bottom of every analysis markdown file:

```markdown
---

## Analysis Log

| Pass | Date | Tool | Model | Duration | Tokens | Cost | Notes |
|------|------|------|-------|----------|--------|------|-------|
| 1 | 2026-01-22 10:00 | Codex | gpt-5.2 | 8m | 12,500 | $0.08 | Initial 3-stage analysis |
| 2 | 2026-01-23 09:15 | Claude Code | claude-sonnet-4 | 3m | ? | ? | Added counterarguments + updated credences |

### Revision Notes

**Pass 2**: Updated claims TECH-2026-014..016; added a stronger steelman; registered 2 new predictions.
```

Rules:
- **Pass numbers** are per `source-id`.
- `Tokens` and `Cost` are optional (`?` if unknown).
- Notes should summarize material changes (what was added/changed and why).

### 2) LanceDB table: `analysis_logs` (machine-facing)

Add a new table `analysis_logs` to the database.

**Row model**: one row per analysis run/pass.

**ID format**: `ANALYSIS-YYYY-NNN` (similar to chain IDs).

**Schema draft (YAML-ish)**:

```yaml
analysis_logs:
  id: "ANALYSIS-2026-001"
  source_id: "author-2026-title"
  analysis_file: "analysis/sources/author-2026-title.md"  # optional
  pass: 1
  status: "completed"  # started|completed|failed|canceled|draft
  tool: "codex"        # claude-code|codex|amp|manual|other
  command: "check"     # optional: check|analyze|extract|...
  model: "gpt-5.2"     # optional
  framework_version: "0.1.4"  # optional (package version)
  methodology_version: "check-core@<hash-or-date>"  # optional/TBD
  started_at: "2026-01-22T10:00:00Z"
  completed_at: "2026-01-22T10:08:00Z"
  duration_seconds: 480        # optional
  tokens_in: 2500              # optional
  tokens_out: 1200             # optional
  total_tokens: 3700           # optional
  cost_usd: 0.08               # optional
  stages_json: "[...]"         # optional: JSON list of per-stage metrics
  claims_extracted: ["TECH-2026-001", "TECH-2026-002"]
  claims_updated: ["TECH-2026-010"]
  notes: "Initial analysis + registration"
  git_commit: "abcd1234"       # optional (data repo commit SHA)
  created_at: "2026-01-22T10:09:00Z"
```

Design notes:
- Keep token/cost fields nullable to support tools that don’t expose them.
- Store per-stage detail as JSON initially to avoid complex nested schemas while iterating.

### 3) CLI: `rc-db analysis ...`

Add `rc-db analysis` subcommands:

- `rc-db analysis add ...` (create row)
- `rc-db analysis get <analysis-id>` (`--format json|text`)
- `rc-db analysis list [--source-id ...] [--status ...] [--tool ...] [--limit N] [--format json|text]`
- (Optional) `rc-db analysis report --by month|tool|model` (cost summaries)

### 4) Workflow integration points

- Update `integrations/_templates/skills/check.md.j2` to require:
  - appending the in-document “Analysis Log” section (for human auditability)
  - writing a corresponding row to `analysis_logs` (for reporting)
- Update Claude plugin command docs (`integrations/claude/plugin/commands/check.md`) to reference the audit step.
- Regenerate skills (`make assemble-skills`) so Codex/Amp/Claude skills stay in sync.

### 5) Validation

Extend `scripts/validate.py` to validate `analysis_logs`:

- When `status=completed`, require `source_id` exists in `sources`
- When `claims_extracted` / `claims_updated` present and `status != draft`, require those IDs exist in `claims`
- Flag malformed `stages_json` and impossible metrics (negative duration/cost)

### 6) Export

Extend export support to include audit logs (TBD interface):

- YAML export for machine use and backups
- Markdown export for human reporting (including cost rollups)

## Affected files (planned)

```text
docs/
  PLAN-audit-log.md                 # this document (new)
  IMPLEMENTATION-audit-log.md       # implementation tracking (new)
  IMPLEMENTATION.md                 # link from Future Work (update)
  SCHEMA.md                         # document analysis_logs table (update)
  WORKFLOWS.md                      # document audit logging workflow (update)

scripts/
  db.py                             # new table + rc-db analysis subcommands
  validate.py                       # analysis_logs integrity checks
  export.py                         # export analysis_logs

tests/
  test_db.py                        # rc-db analysis CLI tests
  test_validate.py                  # validate analysis_logs references
  test_export.py                    # export analysis_logs
  test_e2e.py                       # end-to-end audit log workflow

integrations/
  _templates/skills/check.md.j2     # add audit log requirement + template snippet
  _templates/partials/analysis-log.md.j2  # (new) shared in-document audit section
  claude/plugin/commands/check.md   # reference audit step (update)
  claude/skills/check/SKILL.md      # regenerated
  codex/skills/check/SKILL.md       # regenerated
  amp/skills/realitycheck-check/SKILL.md  # regenerated

methodology/
  workflows/check-core.md           # regenerated
```

## Test plan (must be written first)

1. **Unit** (`scripts/db.py`)
   - `analysis add` creates a row and returns an ID
   - `analysis list` filters by `source_id` / `tool` / `status`
   - `analysis get` returns the expected record
2. **Unit** (`scripts/validate.py`)
   - Fails when analysis log references missing `source_id` or claim IDs
   - Passes when references exist
3. **Unit** (`scripts/export.py`)
   - YAML export includes expected keys
   - Markdown export renders a stable table and summary totals
4. **E2E** (`tests/test_e2e.py`)
   - init DB → add source → add claims → add analysis log → validate → export

## Implementation plan (Spec → Plan → Test → Implement)

1. **Spec**: finalize this plan (fields + workflow)
2. **Tests**
   - Add unit + e2e tests for analysis logging
3. **Implement**
   - Add `ANALYSIS_LOGS_SCHEMA`
   - Include in `init_tables()` / `drop_tables()`
   - Add `add_analysis_log()` / `get_analysis_log()` / `list_analysis_logs()`
   - Wire `rc-db analysis ...` CLI
   - Extend `rc-validate` and `rc-export`
4. **Integrations**
   - Update templates, regenerate skills
5. **Validate**
   - `REALITYCHECK_EMBED_SKIP=1 uv run pytest -v`
   - `uv run python scripts/validate.py` (when real data exists)

## Open questions / TBD

- Should `pass` be auto-computed by counting existing logs for `source_id` (preferred) vs requiring explicit `--pass`.
- Should we store a hash of the analysis markdown file (sha256) for tamper-evident provenance.
- Later extension: a general DB "event log" for non-analysis mutations (claim updates, deletes).

---

## Appendix: Token/Cost Capture

> **See [PLAN-token-usage.md](PLAN-token-usage.md)** for the full token capture design, including delta accounting, session auto-detection, and per-stage breakdowns.

### Session Storage Quick Reference

| Tool | Session Path | Token Data |
|------|--------------|------------|
| Claude Code | `~/.claude/projects/<project>/<uuid>.jsonl` | Per-message: `message.usage` |
| Codex CLI | `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl` | Cumulative: `total_token_usage`, Per-turn: `last_token_usage` |
| Amp | `~/.local/share/amp/threads/T-<uuid>.json` | Per-message: `messages[i].usage` |

### Delta Accounting (Summary)

To attribute tokens to a specific check (not the whole session):

1. **At check start**: snapshot session token count → `baseline`
2. **At check end**: snapshot session token count → `final`
3. **Check tokens** = `final - baseline`

This works because we can always compute the current session token count by:
- **Claude/Amp**: Sum all per-message usage entries
- **Codex**: Sum `last_token_usage` per event OR read cumulative `total_token_usage`

### Pricing Reference (as of 2026-01)

| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| Claude Sonnet 4 | $3.00 | $15.00 |
| Claude Opus 4 | $15.00 | $75.00 |
| GPT-4o | $2.50 | $10.00 |
| o1-preview | $15.00 | $60.00 |

*Note: Prices change frequently; check current pricing before manual entry.*
