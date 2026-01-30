# Reality Check Database Schema

LanceDB-backed storage for claims, sources, chains, predictions, contradictions, and definitions.

## Overview

Reality Check uses LanceDB for vector storage with semantic search capabilities. The database is stored at `data/realitycheck.lance/` by default (configurable via `REALITYCHECK_DATA` environment variable).

## Tables

### claims

Individual claims extracted from sources.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `[DOMAIN]-[YYYY]-[NNN]` |
| `text` | string | Yes | The claim text |
| `type` | string | Yes | Epistemic type: `[F]`/`[T]`/`[H]`/`[P]`/`[A]`/`[C]`/`[S]`/`[X]` |
| `domain` | string | Yes | Domain code (see Domains) |
| `evidence_level` | string | Yes | E1-E6 (see Evidence Hierarchy) |
| `credence` | float32 | Yes | 0.0-1.0 probability estimate |
| `operationalization` | string | No | How to test this claim |
| `assumptions` | list[string] | No | What must be true |
| `falsifiers` | list[string] | No | What would refute |
| `source_ids` | list[string] | Yes | References to sources table |
| `first_extracted` | string | Yes | ISO date of first extraction |
| `extracted_by` | string | Yes | Who/what extracted this claim |
| `supports` | list[string] | No | Claim IDs this supports |
| `contradicts` | list[string] | No | Claim IDs this contradicts |
| `depends_on` | list[string] | No | Claim IDs this depends on |
| `modified_by` | list[string] | No | Claim IDs that modify this |
| `part_of_chain` | string | No | Chain ID if part of argument chain |
| `version` | int32 | Yes | Version number for updates |
| `last_updated` | string | Yes | ISO timestamp of last update |
| `notes` | string | No | Additional notes |
| `embedding` | vector[REALITYCHECK_EMBED_DIM] | No | Embedding vector (default 384 dims; see Embeddings) |

### sources

Bibliography and provenance tracking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique source ID |
| `type` | string | Yes | PAPER/BOOK/REPORT/ARTICLE/BLOG/SOCIAL/CONVO/INTERVIEW/DATA/FICTION/KNOWLEDGE |
| `title` | string | Yes | Source title |
| `author` | list[string] | Yes | Author names |
| `year` | int32 | Yes | Publication year |
| `url` | string | No | URL |
| `doi` | string | No | DOI identifier |
| `accessed` | string | No | Date accessed |
| `reliability` | float32 | No | 0.0-1.0 source reliability rating |
| `bias_notes` | string | No | Notes on potential biases |
| `claims_extracted` | list[string] | No | Backlinks to extracted claims |
| `analysis_file` | string | No | Path to analysis document |
| `topics` | list[string] | No | Topic tags |
| `domains` | list[string] | No | Domain codes |
| `status` | string | No | cataloged/analyzed/etc. |
| `embedding` | vector[REALITYCHECK_EMBED_DIM] | No | Embedding vector (default 384 dims; see Embeddings) |

### chains

Argument chains (A → B → C → Conclusion).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `CHAIN-[YYYY]-[NNN]` |
| `name` | string | Yes | Chain name/title |
| `thesis` | string | Yes | Final conclusion |
| `credence` | float32 | Yes | MIN(step credences) |
| `claims` | list[string] | Yes | Ordered list of claim IDs in chain |
| `analysis_file` | string | No | Path to analysis document |
| `weakest_link` | string | No | ID of weakest claim |
| `scoring_method` | string | No | MIN/RANGE/CUSTOM |
| `embedding` | vector[REALITYCHECK_EMBED_DIM] | No | Embedding vector (default 384 dims; see Embeddings) |

### predictions

Tracking for `[P]` type claims.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim_id` | string | Yes | Reference to claims table |
| `source_id` | string | Yes | Reference to sources table |
| `date_made` | string | No | When prediction was made |
| `target_date` | string | No | When prediction should resolve |
| `falsification_criteria` | string | No | What would falsify |
| `verification_criteria` | string | No | What would verify |
| `status` | string | Yes | `[P+]`/`[P~]`/`[P→]`/`[P?]`/`[P←]`/`[P!]`/`[P-]`/`[P∅]` |
| `last_evaluated` | string | No | Last evaluation date |
| `evidence_updates` | string | No | JSON-encoded list of updates |

### contradictions

Identified logical inconsistencies.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique contradiction ID |
| `claim_a` | string | Yes | First conflicting claim ID |
| `claim_b` | string | Yes | Second conflicting claim ID |
| `conflict_type` | string | No | direct/scope/definition/timescale |
| `likely_cause` | string | No | Why they conflict |
| `resolution_path` | string | No | How to resolve |
| `status` | string | No | open/resolved |

### definitions

Working definitions for key terms.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `term` | string | Yes | The term being defined |
| `definition` | string | Yes | Meaning in context |
| `operational_proxy` | string | No | How to measure/detect |
| `notes` | string | No | Ambiguities, edge cases |
| `domain` | string | No | Domain this definition applies to |
| `analysis_id` | string | No | Source analysis where defined |

### evidence_links

Links between claims and supporting/contradicting sources for epistemic provenance.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `EVLINK-[YYYY]-[NNN]` |
| `claim_id` | string | Yes | Reference to claims table |
| `source_id` | string | Yes | Reference to sources table |
| `direction` | string | Yes | supports/contradicts/strengthens/weakens |
| `status` | string | Yes | active/superseded/retracted |
| `supersedes_id` | string | No | ID of previous link this replaces |
| `strength` | float32 | No | Coarse impact estimate (0.0-1.0) |
| `location` | string | No | Specific location in source (e.g., "Table 3, p.15") |
| `quote` | string | No | Relevant excerpt from source |
| `reasoning` | string | No | Why this evidence matters |
| `analysis_log_id` | string | No | Link to audit log pass |
| `created_at` | string | Yes | ISO timestamp |
| `created_by` | string | Yes | Tool/agent that created this link |

### reasoning_trails

Reasoning chains for claim credence assignments.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `REASON-[YYYY]-[NNN]` |
| `claim_id` | string | Yes | Reference to claims table |
| `status` | string | Yes | active/superseded |
| `supersedes_id` | string | No | ID of previous trail this replaces |
| `credence_at_time` | float32 | Yes | Credence when trail was created |
| `evidence_level_at_time` | string | Yes | Evidence level when trail was created |
| `evidence_summary` | string | No | Brief summary of evidence balance |
| `supporting_evidence` | list[string] | No | Evidence link IDs that support |
| `contradicting_evidence` | list[string] | No | Evidence link IDs that contradict |
| `assumptions_made` | list[string] | No | Explicit assumptions in reasoning |
| `counterarguments_json` | string | No | JSON-encoded counterarguments (see below) |
| `reasoning_text` | string | Yes | Publishable rationale for credence |
| `analysis_pass` | int32 | No | Pass number when created |
| `analysis_log_id` | string | No | Link to audit log |
| `created_at` | string | Yes | ISO timestamp |
| `created_by` | string | Yes | Tool/agent that created this trail |

#### Counterarguments JSON Format

```json
[
  {
    "text": "Alternative interpretation of data",
    "disposition": "integrated",  // integrated/discounted/unresolved
    "response": "Addressed by considering X"
  }
]
```

### analysis_logs

Audit trail for analysis passes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `ANALYSIS-[YYYY]-[NNN]` |
| `source_id` | string | Yes | Reference to sources table |
| `analysis_file` | string | No | Path to analysis markdown file |
| `pass` | int32 | Yes | Pass number for this source (auto-computed) |
| `status` | string | Yes | started/completed/failed/canceled/draft |
| `tool` | string | Yes | claude-code/codex/amp/manual/other |
| `command` | string | No | Command used (check/analyze/extract) |
| `model` | string | No | Model used (e.g., claude-sonnet-4) |
| `framework_version` | string | No | Reality Check version |
| `methodology_version` | string | No | Methodology version hash |
| `started_at` | string | No | ISO timestamp of start |
| `completed_at` | string | No | ISO timestamp of completion |
| `duration_seconds` | int32 | No | Duration in seconds |
| `tokens_in` | int32 | No | Input tokens (legacy, nullable) |
| `tokens_out` | int32 | No | Output tokens (legacy, nullable) |
| `total_tokens` | int32 | No | Total tokens (legacy, nullable) |
| `cost_usd` | float32 | No | Cost in USD (nullable) |
| `tokens_baseline` | int32 | No | Session tokens at check start (delta accounting) |
| `tokens_final` | int32 | No | Session tokens at check end (delta accounting) |
| `tokens_check` | int32 | No | Tokens for this check: `tokens_final - tokens_baseline` |
| `usage_provider` | string | No | Session provider: claude/codex/amp |
| `usage_mode` | string | No | Capture method: per_message_sum/windowed_sum/counter_delta/cumulative_snapshot/manual |
| `usage_session_id` | string | No | Session UUID (portable identifier) |
| `inputs_source_ids` | list[string] | No | Source IDs feeding a synthesis (synthesis-only) |
| `inputs_analysis_ids` | list[string] | No | Analysis log IDs feeding a synthesis (synthesis-only) |
| `stages_json` | string | No | JSON-encoded per-stage metrics |
| `claims_extracted` | list[string] | No | Claim IDs extracted in this pass |
| `claims_updated` | list[string] | No | Claim IDs updated in this pass |
| `notes` | string | No | Freeform notes on what changed |
| `git_commit` | string | No | Git commit SHA (data repo) |
| `created_at` | string | Yes | ISO timestamp of log creation |

#### Delta Accounting

The `tokens_baseline`, `tokens_final`, and `tokens_check` fields enable accurate per-check token attribution:

1. **Start**: Record `tokens_baseline` from current session token count
2. **Complete**: Record `tokens_final` from current session token count
3. **Compute**: `tokens_check = tokens_final - tokens_baseline`

This is more accurate than the legacy `total_tokens` field for sessions containing multiple checks.

#### Synthesis Attribution

For synthesis passes that combine multiple source analyses:
- `inputs_source_ids`: List of source IDs being synthesized
- `inputs_analysis_ids`: List of analysis log IDs (for end-to-end cost tracking)

## Domains

Valid domain codes:

| Code | Description |
|------|-------------|
| LABOR | Employment, automation, human work |
| ECON | Value theory, pricing, distribution, ownership |
| GOV | Governance, policy, regulation |
| TECH | Technology trajectories, capabilities |
| SOC | Social structures, culture, behavior |
| RESOURCE | Scarcity, abundance, allocation |
| TRANS | Transition dynamics, pathways |
| GEO | International relations, state competition |
| INST | Institutions, organizations |
| RISK | Risk assessment, failure modes |
| META | Claims about the framework/analysis itself |

### Domain Migration

Legacy domains are automatically migrated:
- `VALUE` → `ECON`
- `DIST` → `ECON`
- `SOCIAL` → `SOC`

## Evidence Levels

| Level | Description | Credence Range |
|-------|-------------|----------------|
| E1 | Strong Empirical | 0.9-1.0 |
| E2 | Moderate Empirical | 0.6-0.8 |
| E3 | Strong Theoretical | 0.5-0.7 |
| E4 | Weak Theoretical | 0.3-0.5 |
| E5 | Opinion/Forecast | 0.2-0.4 |
| E6 | Unsupported | 0.0-0.2 |

## Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified |
| Theory | `[T]` | Explanatory framework |
| Hypothesis | `[H]` | Testable proposition |
| Prediction | `[P]` | Future-oriented claim |
| Assumption | `[A]` | Underlying premise |
| Counterfactual | `[C]` | Alternative scenario |
| Speculation | `[S]` | Untestable claim |
| Contradiction | `[X]` | Logical inconsistency |

## Prediction Statuses

| Status | Symbol | Criteria |
|--------|--------|----------|
| Confirmed | `[P+]` | Occurred as specified |
| Partially Confirmed | `[P~]` | Core correct, details differ |
| On Track | `[P→]` | Intermediate indicators align |
| Uncertain | `[P?]` | Insufficient data |
| Off Track | `[P←]` | Indicators diverge |
| Partially Refuted | `[P!]` | Core problematic |
| Refuted | `[P-]` | Clearly failed |
| Unfalsifiable | `[P∅]` | Cannot be tested |

## Source Types

| Type | Description |
|------|-------------|
| PAPER | Academic paper |
| BOOK | Book or book chapter |
| REPORT | Industry/org report |
| ARTICLE | News or magazine article |
| BLOG | Blog post |
| SOCIAL | Social media post |
| CONVO | Conversation transcript (e.g., chat logs) |
| INTERVIEW | Interview, talk, or speech transcript |
| DATA | Dataset or repository reference |
| FICTION | Fictional work (useful for narrative analysis) |
| KNOWLEDGE | General knowledge/common understanding |

## Embeddings

All text fields can be embedded using the configured embedding backend:

- Default: local `sentence-transformers` with `REALITYCHECK_EMBED_MODEL=all-MiniLM-L6-v2` (`REALITYCHECK_EMBED_DIM=384`)
- Optional: `REALITYCHECK_EMBED_PROVIDER=openai` for an OpenAI-compatible remote embeddings endpoint

Embeddings enable:

- Semantic search across claims/sources
- Finding related claims
- Clustering analysis

`REALITYCHECK_EMBED_DIM` must match the model output and the LanceDB schema (vector columns are fixed-size). Changing models/dimensions requires re-initializing or migrating the database.

For CPU-only local embeddings, Reality Check clamps threading by default (`REALITYCHECK_EMBED_THREADS=4`) to avoid pathological slowdowns on some environments.

Generate embeddings with:
```bash
uv run rc-embed generate
```

## Schema Migration

LanceDB tables are fixed-schema - columns cannot be auto-added when the framework updates. When upgrading Reality Check, run the migrate command to add new columns:

```bash
# Preview changes
rc-db migrate --dry-run

# Apply migrations
rc-db migrate
```

The migrate command compares current table schemas against expected schemas and adds missing columns with appropriate defaults. It's safe to run multiple times (idempotent).

## Validation Rules

The `rc-validate` command checks:

1. **ID Format**: Claim IDs match `[DOMAIN]-[YYYY]-[NNN]`
2. **Referential Integrity**: All foreign keys resolve
3. **Domain Consistency**: ID domain matches `domain` field
4. **Credence Range**: Values in [0.0, 1.0]
5. **Type Values**: Only allowed type symbols
6. **Chain Credence**: Chain credence ≤ MIN(claim credences)
7. **Prediction Links**: All `[P]` claims have prediction records
8. **Source↔Claim Backlinks**: `sources.claims_extracted` matches `claims.source_ids` (repairable via `rc-db repair`)
9. **Analysis Log Integrity**:
   - `status` and `tool` must be valid enum values
   - If `status=completed`, `source_id` must exist in sources
   - If `status != draft`, `claims_extracted` and `claims_updated` must reference existing claims
   - `stages_json` must be valid JSON (if present)
   - `duration_seconds` and `cost_usd` must be non-negative (if present)
   - If `tokens_baseline`, `tokens_final`, and `tokens_check` all present, `tokens_check` must equal `tokens_final - tokens_baseline`
   - `inputs_analysis_ids` must reference existing analysis log IDs (for synthesis attribution)

10. **Evidence Links Integrity**:
    - `claim_id` must reference existing claim
    - `source_id` must reference existing source
    - `direction` must be one of: supports/contradicts/strengthens/weakens
    - `status` must be one of: active/superseded/retracted
    - If `supersedes_id` is set, it must reference existing evidence link
    - `strength` must be in [0.0, 1.0] (if present)

11. **Reasoning Trails Integrity**:
    - `claim_id` must reference existing claim
    - `status` must be one of: active/superseded
    - If `supersedes_id` is set, it must reference existing reasoning trail
    - `credence_at_time` must be in [0.0, 1.0]
    - `evidence_level_at_time` must be valid (E1-E6)
    - All IDs in `supporting_evidence` and `contradicting_evidence` must reference existing evidence links
    - `counterarguments_json` must be valid JSON (if present)

12. **High-Credence Backing** (warnings, errors with --strict):
    - Claims with credence ≥ 0.7 should have at least one evidence link
    - Claims with evidence level E1 or E2 should have at least one evidence link
    - Evidence links should have `location` and `reasoning` fields populated
