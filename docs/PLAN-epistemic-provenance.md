# Plan: Epistemic Provenance (Reasoning Trails)

**Status**: Ready for Implementation
**Created**: 2026-01-24
**Implementation**: [IMPLEMENTATION-epistemic-provenance.md](IMPLEMENTATION-epistemic-provenance.md)

## Motivation

Reality Check extracts claims and assigns credence ratings, but currently lacks structured traceability for *why* a claim has a given credence. The Analysis MD files contain prose reasoning, but:

- No explicit link between a claim's credence and the evidence that supports it
- No queryable record of counter-arguments considered
- No way to audit whether high-credence claims actually have backing
- We become a potential source of unconfirmable bias

If Reality Check is an epistemic tool, **we must be rigorous about backing up our credence analysis**. Users should be able to follow the chain: Claim → Evidence → Reasoning → Credence.

## Current State

### What exists

1. **Claims** have `source_ids` (list of source references) - but this just means "extracted from these sources", not "supported by these sources"
2. **Claims** have `evidence_level` (E1-E6) - but no link to *which* evidence justifies that level
3. **Claims** have relationship fields (`supports`, `contradicts`, `depends_on`) - for inter-claim links
4. **Analysis MD** contains prose reasoning - but unstructured and not linked to DB records
5. **Sources** exist as bibliography - but no structured "this source supports claim X because Y"

### The gap

- **Support vs. Origin**: `source_ids` conflates "where extracted from" with "what supports this"
- **Evidence linking**: No structured way to say "Claim X has E2 because of Source Y, Table 3"
- **Reasoning capture**: The *why* of credence assignment lives only in ephemeral chat/prose
- **Auditability**: Can't programmatically check "do all high-credence claims have backing?"

## Goals

1. **Trace credence to evidence**: Every credence rating should link to supporting evidence
2. **Capture reasoning**: Record *why* we believe X to degree Y (not just the conclusion)
3. **Counter-argument trail**: Document what was considered and rejected
4. **Render to repo**: Export reasoning trails as browsable markdown (not just DB queries)
5. **Link from Analysis MD**: Tables/prose should link to backing documentation
6. **Validation**: Enforce that high-credence claims (≥0.7) have explicit backing
7. **Reader-auditable outputs**: "Credence" should never be a "trust us" number; every high-credence claim must have enough citation + rationale for a reader to independently check

## Non-goals (for v1)

- Full formal argument mapping (Toulmin diagrams, etc.) - too complex
- Capturing every LLM reasoning step verbatim ("chain-of-thought") - too noisy, privacy concerns
- Real-time reasoning capture during analysis - requires deeper integration
- Replacing prose reasoning with structured-only - prose remains primary, structured is supplementary

## Provenance contract (v1)

To avoid "trust us bro" credence, v1 needs a **minimum provenance contract** for claims a reader is likely to rely on.

### Minimum requirements

For any claim with **credence ≥ 0.7** *or* evidence level **E1/E2**:

- **At least one supporting link**: ≥1 `evidence_links` row with `direction` in `{supports,strengthens}`.
- **Specificity**: Each supporting link should include a **concrete locator** (`location` like page/section/table/timecode) and a short rationale (`reasoning`).
- **Current rationale**: ≥1 `reasoning_trails` row for the claim that explains *why* the current credence/evidence level was assigned, referencing the relevant `evidence_links`.
- **Counterevidence handling**: Any known significant counterevidence/counterargument is either linked (`direction` in `{contradicts,weakens}`) or explicitly noted as "not found yet" in the reasoning trail.

### "Publishable rationale", not hidden reasoning

`reasoning_trails.reasoning_text` is intended to be reader-facing and exportable. It should be a concise justification that cites evidence links and summarizes trade-offs/uncertainty. Do **not** store private prompts, full transcripts, or raw chain-of-thought.

## Proposed Design

### 1) New table: `evidence_links`

Explicit links between claims and their supporting/contradicting evidence.

```yaml
evidence_links:
  id: "EVLINK-2026-001"
  claim_id: "TECH-2026-042"           # The claim being supported/contradicted
  source_id: "author-2026-title"      # The source providing evidence
  direction: "supports"               # supports|contradicts|weakens|strengthens
  status: "active"                    # active|superseded|retracted
  supersedes_id: null                 # OPTIONAL: pointer for corrections
  strength: 0.8                       # OPTIONAL: coarse impact estimate (avoid false precision)
  location: "Table 3, p.15"           # Specific location in source (optional)
  quote: "The study found..."         # Relevant excerpt (optional, short)
  reasoning: "This directly measures X, which is what the claim asserts"
  analysis_log_id: "ANALYSIS-2026-001"  # OPTIONAL: link to audit-log pass (once implemented)
  created_at: "2026-01-24T10:00:00Z"
  created_by: "claude-code"           # Tool/user that created this link
```

**Key distinction**: This separates "extracted from" (`source_ids`) from "supported by" (`evidence_links`).

### 2) New table: `reasoning_trails`

Capture the reasoning chain for a claim's credence assignment.

```yaml
reasoning_trails:
  id: "REASON-2026-001"
  claim_id: "TECH-2026-042"
  status: "active"                    # active|superseded
  supersedes_id: null                 # OPTIONAL: pointer for corrections
  credence_at_time: 0.75              # The credence this reasoning produced
  evidence_level_at_time: "E2"        # Evidence level assigned under this reasoning
  evidence_summary: "E2 based on 2 supporting sources, 1 weak counter"
  
  # Structured reasoning components
  supporting_evidence: ["EVLINK-2026-001", "EVLINK-2026-002"]
  contradicting_evidence: ["EVLINK-2026-003"]
  assumptions_made: ["Assumes current trends continue"]
  counterarguments_considered:
    - argument: "Study X found opposite result"
      response: "Study X used different methodology; not directly comparable"
      disposition: "discounted"  # integrated|discounted|unresolved
  
  # Overall reasoning
  reasoning_text: |
    Assigned 0.75 credence because:
    1. Two independent studies support the core mechanism
    2. One contradicting study exists but uses incompatible methodology
    3. No direct replication yet (prevents E1)
  
  # Meta
  analysis_pass: 1                    # Which analysis pass produced this
  analysis_log_id: "ANALYSIS-2026-001"  # OPTIONAL: link to audit-log pass (once implemented)
  created_at: "2026-01-24T10:00:00Z"
  created_by: "claude-code"
```

### 2b) Immutability + disagreement semantics (v1)

To preserve epistemic provenance over time (and across agents), both `evidence_links` and `reasoning_trails` should be **append-only**:

- **No in-place edits for meaning changes**: correcting/adjusting a link or trail creates a new row and sets `supersedes_id` on the new row.
- **Current view is a projection**: "active" rows are the default for rendering and validation; history remains queryable.
- **Reasoning cites stable evidence IDs**: a trail references specific `evidence_links` rows; later corrections produce new evidence links and (optionally) a new trail.
- **Agent disagreement is first-class**: multiple trails can exist for a claim; `analysis_log_id` (when available) attributes trails to specific tool/model/pass for later bias/consensus analysis.

### 3) Rendered artifacts in data repo

Generate browsable markdown files from DB:

```
analysis/
  sources/
    author-2026-title.md              # Existing analysis markdown
  
  reasoning/                          # NEW: rendered reasoning trails
    TECH-2026-042.md                  # Per-claim reasoning documentation
    
  evidence/                           # NEW: rendered evidence links
    by-claim/
      TECH-2026-042.md                # All evidence for a claim
    by-source/
      author-2026-title.md            # All claims supported by a source
```

**Per-claim reasoning file** (`reasoning/TECH-2026-042.md`):

````markdown
# Reasoning: TECH-2026-042

> **Claim**: [The claim text]
> **Credence**: 0.75 (E2)
> **Domain**: TECH

## Evidence Summary

| Direction | Source | Location | Strength | Summary |
|-----------|--------|----------|----------|---------|
| Supports | [Author 2024](../sources/author-2024-title.md) | Table 3 | 0.8 | Direct measurement of X |
| Supports | [Smith 2023](../sources/smith-2023-study.md) | §4.2 | 0.6 | Corroborating mechanism |
| Contradicts | [Jones 2022](../sources/jones-2022-review.md) | p.45 | 0.3 | Different methodology |

## Reasoning Chain

Assigned 0.75 credence because:
1. Two independent studies support the core mechanism
2. One contradicting study exists but uses incompatible methodology
3. No direct replication yet (prevents E1)

## Counterarguments Considered

### "Study X found opposite result"
**Response**: Study X used different methodology; not directly comparable
**Disposition**: Acknowledged but discounted

## Assumptions

- Assumes current trends continue

## Trail History

| Date | Credence | Pass | Tool | Notes |
|------|----------|------|------|-------|
| 2026-01-24 | 0.75 | 1 | claude-code | Initial analysis |

## Data (portable)

```yaml
claim_id: "TECH-2026-042"
reasoning_trail_id: "REASON-2026-001"
credence_at_time: 0.75
evidence_level_at_time: "E2"
supporting_evidence: ["EVLINK-2026-001", "EVLINK-2026-002"]
contradicting_evidence: ["EVLINK-2026-003"]
```
````

### 3b) Portability exports (v1)

Rendered markdown is for humans; portability should not depend on LanceDB internals.

Add export support so a data repo can regenerate (or share) provenance without bespoke tooling:

- **YAML/JSON export**: `rc-export yaml provenance` (or similar) to dump `evidence_links` + `reasoning_trails` (and later `analysis_logs`) in a stable, diff-friendly format.
- **Deterministic rendering**: exporters must sort consistently (e.g., by `claim_id`, then `created_at`, then `id`) so reruns are stable when DB state is unchanged.
- **Embed a minimal machine block**: per-claim reasoning markdown includes a small YAML block (as above) that points to the canonical IDs and current credence/evidence level.

### 3c) Future: Evidence snapshots (ArchiveBox / other)

Long-term epistemic robustness requires protecting against link rot and "moving targets" (updated web pages, deleted PDFs, etc.).

Future direction (out of scope for v1):

- **Snapshot sources**: when a `sources.url` exists, capture an immutable snapshot (e.g., via ArchiveBox, singlefile, wget, perma.cc, etc.).
- **Store in the data repo**: keep snapshots under a stable path (e.g., `evidence/snapshots/<source-id>/...`) so collaborators can verify without the network.
- **Record snapshot metadata**: extend `sources` with fields like `snapshot_paths`, `snapshot_captured_at`, `snapshot_tool`, `snapshot_hash` (or equivalent), and render links in `analysis/sources/<source-id>.md`.
- **Link evidence to snapshots**: allow `evidence_links` to reference a specific snapshot artifact when relevant (so "Table 3" points to the captured copy).
- **Validation (later)**: optionally require snapshots for high-credence claims supported by URL-based sources.

### 4) Analysis MD linking

Update Analysis MD format to link claims to their reasoning docs:

**Note**: Analysis document tables are governed by the existing Output Contract (`scripts/analysis_validator.py` / `scripts/analysis_formatter.py`). v1 should keep the same columns and add links *within cells*.

**Current** (Claim Summary table in Analysis MD):
```markdown
| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| TECH-2026-042 | [F] | TECH | E2 | 0.75 | The claim text |
```

**Proposed (v1, backward compatible)**: hyperlink claim IDs to rendered reasoning docs:
```markdown
| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| [TECH-2026-042](../reasoning/TECH-2026-042.md) | [F] | TECH | E2 | 0.75 | The claim text |
```

### 5) CLI extensions

```bash
# Evidence linking
rc-db evidence add --claim-id TECH-2026-042 --source-id author-2024 \
  --direction supports --strength 0.8 --location "Table 3" \
  --reasoning "Direct measurement of X"

rc-db evidence list --claim-id TECH-2026-042
rc-db evidence list --source-id author-2024

# Reasoning trails
rc-db reasoning add --claim-id TECH-2026-042 --credence 0.75 \
  --evidence-summary "E2 based on 2 supporting, 1 weak counter" \
  --reasoning-text "Assigned 0.75 because..."

rc-db reasoning get --claim-id TECH-2026-042
rc-db reasoning history --claim-id TECH-2026-042  # Show credence evolution

# Rendering
rc-export md reasoning --claim-id TECH-2026-042 --output-dir analysis/reasoning
rc-export md reasoning --all --output-dir analysis/reasoning

# Portability export
rc-export yaml provenance -o analysis/provenance.yaml
```

### 6) Validation extensions

```bash
rc-validate
```

New checks:
- **High-credence backing**: Claims with credence ≥0.7 (or E1/E2) must have ≥1 supporting `evidence_links` row (`supports`/`strengthens`)
- **Evidence integrity**: All `evidence_links.claim_id` and `source_id` must exist
- **Evidence specificity (for high-credence claims)**: supporting evidence links must include at least a locator (`location`) and a non-empty `reasoning`
- **Reasoning freshness**: Warn if claim credence/evidence level differs from latest reasoning trail (`credence_at_time` / `evidence_level_at_time`)
- **Audit-log linkage (optional)**: If `analysis_log_id` is present, it must exist in `analysis_logs` (once that table ships)

### 7) Workflow integration

Update `/check` workflow to:
1. After extracting claims, prompt for evidence linking
2. After assigning credence, capture reasoning trail
3. After registration, render reasoning docs
4. Link from Analysis MD to reasoning docs

## Affected files (planned)

```text
docs/
  PLAN-epistemic-provenance.md       # This document (new)
  IMPLEMENTATION-epistemic-provenance.md  # Implementation tracking (new)
  SCHEMA.md                          # Add evidence_links + reasoning_trails tables
  WORKFLOWS.md                       # Document reasoning capture workflow
  TODO.md                            # Add this feature (update)

scripts/
  db.py                              # New tables + CLI subcommands
  validate.py                        # New validation rules
  export.py                          # render-reasoning command
  analysis_formatter.py              # (optional) preserve/add reasoning links in tables

tests/
  test_db.py                         # evidence/reasoning CRUD tests
  test_validate.py                   # High-credence backing validation
  test_export.py                     # Reasoning rendering tests
  test_e2e.py                        # End-to-end with evidence linking
  test_analysis_formatter.py         # (if linking is added to formatter)

integrations/_templates/
  skills/check.md.j2                 # Add evidence linking + reasoning steps
  tables/claim-summary.md.j2         # Update to support reasoning links in ID column

methodology/
  reasoning-trails.md                # (new) Methodology for reasoning capture
```

## Test plan (must be written first)

1. **Unit** (`scripts/db.py`)
   - `evidence add` creates link, validates claim/source exist
   - `evidence list` filters by claim or source
   - `reasoning add` creates trail with all fields
   - `reasoning history` shows credence evolution

2. **Unit** (`scripts/validate.py`)
   - Fails when claim ≥0.7 credence has no evidence links
   - Fails when evidence_link references missing claim/source
   - Warns when reasoning trail credence differs from current claim credence

3. **Unit** (`scripts/export.py`)
   - Renders claim reasoning markdown with correct structure
   - Renders evidence-by-source index
   - Links are relative and valid
   - Exports provenance YAML/JSON deterministically

4. **E2E** (`tests/test_e2e.py`)
   - init → add source → add claim → add evidence link → add reasoning → validate → render

## Implementation phases (Spec → Plan → Test → Implement)

1. **Tests first**: Write all unit + e2e tests
2. **Schema + CRUD**: `evidence_links` and `reasoning_trails` tables
3. **CLI**: `rc-db evidence ...` and `rc-db reasoning ...` subcommands
4. **Validation**: High-credence backing checks
5. **Export/Render**: `rc-export md reasoning` + `rc-export yaml provenance`
   - Prefer integrating into existing `rc-export md ...` / `rc-export yaml ...` interfaces; keep `render-reasoning` only as an optional alias if desired
6. **Workflow integration**: Update skills to include evidence/reasoning steps
7. **Docs**: SCHEMA.md, WORKFLOWS.md, methodology

## Open questions (RESOLVED)

All open questions have been resolved. See [IMPLEMENTATION-epistemic-provenance.md](IMPLEMENTATION-epistemic-provenance.md) for the full decisions log.

| Question | Resolution |
|----------|------------|
| Granularity | Per-source with optional `location` field |
| Versioning | Explicit `status`/`supersedes_id` for rigorous audit trail |
| Auto-linking | Explicit only for v1 (no inference from `source_ids`) |
| Rendering trigger | On-demand via `rc-export md reasoning` |
| Storage | Both explicit `reasoning_text` + structured fields |
| Output contract | Update validator/formatter to support `[ID](path)` links |
| Evidence snapshots | Deferred to future work (out of scope for v1) |
| Validation threshold | Configurable: warn by default, `--strict` for errors |

## Relationship to other features

- **Audit Log** (`PLAN-audit-log.md`): Tracks *process* (who/when/how analyzed); this tracks *epistemics* (why we believe X). Linking via `analysis_log_id` enables later analysis of agent/model disagreement and drift over passes.
- **Argument Chains** (existing): Chains link claims in argument sequences; evidence_links connect claims to sources
- **Contradictions** (existing): Existing table for claim-vs-claim conflicts; evidence_links can show source-level conflicts

---

## Appendix: Evidence Link Directions

| Direction | Meaning | Effect on Credence |
|-----------|---------|-------------------|
| `supports` | Evidence directly supports the claim | ↑ Increases confidence |
| `contradicts` | Evidence directly contradicts the claim | ↓ Decreases confidence |
| `strengthens` | Evidence indirectly supports (mechanism, analogy) | ↑ Mild increase |
| `weakens` | Evidence indirectly undermines (competing explanation) | ↓ Mild decrease |

## Appendix: Counterargument Dispositions

| Disposition | Meaning |
|-------------|---------|
| `integrated` | Counterargument incorporated into updated understanding |
| `discounted` | Counterargument considered but rejected with reason |
| `unresolved` | Counterargument remains open; affects credence uncertainty |
