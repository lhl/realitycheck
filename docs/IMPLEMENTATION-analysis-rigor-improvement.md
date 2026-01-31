# Implementation: Analysis Rigor Improvements (Primary Evidence, Layering, Corrections, Auditability)

**Status**: Spec Locked (ready to implement)  
**Plan**: [PLAN-analysis-rigor-improvement.md](PLAN-analysis-rigor-improvement.md)  
**Depends On**:
- [IMPLEMENTATION-epistemic-provenance.md](IMPLEMENTATION-epistemic-provenance.md) (complete)
- [IMPLEMENTATION-audit-log.md](IMPLEMENTATION-audit-log.md) (complete)
- [IMPLEMENTATION-token-usage.md](IMPLEMENTATION-token-usage.md) (complete)
**Started**: 2026-01-31  
**Last Updated**: 2026-01-31  

## Summary

Upgrade the analysis workflow so “rigor” is enforced by the analysis *interface* (tables + provenance), not only by prose:

- **Layer separation**: ASSERTED vs LAWFUL vs PRACTICED vs EFFECT are explicit and hard to conflate.
- **Primary-first**: high-impact claims preferentially cite and capture primary documents (or record why not).
- **Corrections-aware**: updates/corrections are recorded and their impact on claims is tracked (append-only).
- **Actor & scope discipline**: ICE vs CBP vs DHS vs DOJ vs courts are attributed explicitly; scope/quantifiers are bounded.
- **No “confidence theater”**: high credence requires auditable evidence links with locators + publishable reasoning trails.

This implementation focuses on **templates + workflow + validation gates + capture tooling**.

## What Already Exists (Prereqs)

These features already exist and should be reused (not re-invented):

- **Analysis audit log**: `analysis_logs` table + workflow docs + exports. See [IMPLEMENTATION-audit-log.md](IMPLEMENTATION-audit-log.md).
- **Token usage capture lifecycle**: `rc-db analysis start/mark/complete` and backfill. See [IMPLEMENTATION-token-usage.md](IMPLEMENTATION-token-usage.md).
- **Epistemic provenance**:
  - `evidence_links` and `reasoning_trails` tables
  - High-credence backing validation (requires evidence links, plus `location` + `reasoning` fields on supporting links)
  - Append-only superseding semantics (`status` + `supersedes_id`)
  See [IMPLEMENTATION-epistemic-provenance.md](IMPLEMENTATION-epistemic-provenance.md).

## High-Level Approach (Implementation Strategy)

1. **Decide the new “rigor contract”**: enumerations + scope schema + where the structured fields live (analysis-only vs DB).
2. **Ship template + workflow changes first** (with validators/formatters updated), so new analyses are forced into the new shape.
3. **Add capture tooling** to make “primary-first” feasible in practice.
4. **Add guardrails** (validation + ergonomics) that prevent DB credence changes without captured/linked evidence.

## Affected Files (Expected)

Framework repo (this repo):

```
docs/
 ├── NEW IMPLEMENTATION-analysis-rigor-improvement.md    # This file
 ├── UPDATE TODO.md                                     # Link this implementation file; status
 ├── UPDATE WORKFLOWS.md                                # Multi-pass rigor workflow; primary capture; corrections
 ├── UPDATE SCHEMA.md                                   # Only if we add/extend tables/columns
 └── (optional) UPDATE CHANGELOG.md                     # When feature ships

integrations/_templates/
 ├── UPDATE tables/key-claims.md.j2                     # Add Layer/Actor/Scope/Quantifier (rigor-v1 contract)
 ├── UPDATE tables/claim-summary.md.j2                  # Add Layer/Actor/Scope/Quantifier (rigor-v1 contract)
 ├── NEW   tables/corrections-updates.md.j2             # New required section/table
 ├── UPDATE skills/check.md.j2                          # Add explicit multi-pass steps + primary capture + corrections
 ├── UPDATE skills/analyze.md.j2                        # Document new rigor contract for manual analysis
 ├── (optional) UPDATE partials/legends.md.j2           # If we add enumerations (layer/quantifier/etc)
 └── regenerate all skills via `make assemble-skills`

scripts/
 ├── UPDATE analysis_validator.py                       # Enforce/optionally warn on new table columns + new section
 ├── UPDATE analysis_formatter.py                       # Insert new tables/sections and keep snippets in sync
 ├── (optional) NEW capture.py                          # Primary artifact capture CLI
 ├── (optional) UPDATE db.py                            # If we add fields/tables and/or add a capture command
 ├── (optional) UPDATE validate.py                      # New validation gates based on chosen schema
 └── (optional) UPDATE export.py                        # If we add new exports (primary index, corrections index)

tests/
 ├── UPDATE test_analysis_validator.py                  # New contract tests (tables + section)
 ├── UPDATE test_analysis_formatter.py                  # New insertion snippets tests
 ├── (optional) UPDATE test_db.py                       # If schema/CLI changes
 ├── (optional) UPDATE test_validate.py                 # If new validation gates
 ├── (optional) NEW test_capture.py                     # If we add capture tooling
 └── (optional) UPDATE test_e2e.py                      # If we add an end-to-end “rigor workflow” test
```

## Open Decisions

None. D1–D10 are resolved in [PLAN-analysis-rigor-improvement.md](PLAN-analysis-rigor-improvement.md#decision-log) and summarized below.

If new questions arise during coding, log them in the Worklog and update the Plan Decision Log.

## Punchlist

### Phase 0: Decisions + Spec Lock (docs-only)

- [x] Decide D1–D10 and record final choices in this file ("Resolved Decisions" section)
- [x] Update [PLAN-analysis-rigor-improvement.md](PLAN-analysis-rigor-improvement.md) with Decision Log section
- [x] Add a "Rigor Contract (v1)" section to [docs/WORKFLOWS.md](WORKFLOWS.md) describing:
  - required table columns and their intended semantics
  - minimal scope writing convention
  - how to handle non-applicable values (e.g., `N/A`)

### Phase 1: Tests First (framework repo)

Add/extend tests before implementing behavior changes.

#### 1.1 Output Contract Validator (`tests/test_analysis_validator.py`)

- [ ] Add a “rigor v1” table header test for Key Claims:
  - passes when new required columns are present
  - fails (or warns, if chosen) when missing
- [ ] Add a “rigor v1” table header test for Claim Summary (if updated)
- [ ] Add a test that the new “Corrections & Updates” section is required (or warned) under the full profile
- [ ] Add tests for enum enforcement (only if we choose strict enums)

#### 1.2 Output Contract Formatter (`tests/test_analysis_formatter.py`)

- [ ] Update insertion snippet expectations to match new templates:
  - Key Claims table header (new columns)
  - Claim Summary header (new columns)
  - New Corrections/Updates table insertion
- [ ] Add idempotency tests for the new inserted section/table

#### 1.3 (Optional) Validation Gates (`tests/test_validate.py`)

Only if we add DB-level rules beyond existing high-credence backing:

- [ ] Primary-first gate tests (warn/error depending on decision):
  - e.g., “LAWFUL + high-credence claim must have supporting evidence_type=LAW and captured artifact”
- [ ] Reasoning trail status tests if adding `proposed`

#### 1.4 (Optional) Capture Tool (`tests/test_capture.py`)

Only if we implement capture tooling in the framework repo:

- [ ] Fetch+store a local fixture PDF via a test HTTP server
- [ ] Verify hashing/deduping, metadata sidecar creation, and stable output paths
- [ ] Verify “non-PDF by default” is rejected (if that is the licensing rule)

### Phase 2: Template + Skill Contract Updates

#### 2.1 Update templates (source of truth)

- [ ] Update `integrations/_templates/tables/key-claims.md.j2` to include the new columns and a clear column guide
- [ ] Update `integrations/_templates/tables/claim-summary.md.j2` to include the new columns (if chosen)
- [ ] Add `integrations/_templates/tables/corrections-updates.md.j2` with a required table:
  - `Item` | `URL` | `Published` | `Corrected/Updated` | `What Changed` | `Impacted Claim IDs` | `Action Taken`
- [ ] Update `integrations/_templates/skills/check.md.j2`:
  - Add explicit “multi-pass” structure (A–E) and the expectation that each pass is logged
  - Add a “Primary Capture” step for high-impact claims (with failure recording)
  - Add a “Corrections & Updates” step and guidance
  - Ensure provenance step references evidence links/trails rather than duplicating prose
- [ ] Update `integrations/_templates/skills/analyze.md.j2` similarly (manual workflow)

#### 2.2 Regenerate skill docs

- [ ] Run `make assemble-skills`
- [ ] Run `make check-skills` (should be clean)

### Phase 3: Validator/Formatter Sync (framework repo)

Keep `scripts/analysis_validator.py` and `scripts/analysis_formatter.py` aligned with the templates (this is a common drift risk).

- [ ] Update `scripts/analysis_validator.py`:
  - Enforce (or warn) for new table columns using robust header regex patterns
  - Require (or warn) on Corrections/Updates section presence for full profile
  - If we add a “rigor profile” flag, implement `--profile rigor` or `--rigor` and document it
- [ ] Update `scripts/analysis_formatter.py`:
  - Update `KEY_CLAIMS_TABLE` and `CLAIM_SUMMARY_TABLE` constants
  - Add a `CORRECTIONS_UPDATES_TABLE` insertion snippet
  - Ensure formatter insertion order places corrections in a sensible spot (e.g., near end or after Stage 2)

### Phase 4: Primary Evidence Capture Tooling (optional but recommended)

If implemented, keep it deliberately narrow (primary docs) and safe by default.

#### 4.1 CLI surface (choose one)

- [ ] New standalone: `rc-capture primary --url ... --out reference/primary/...`
- [ ] OR `rc-db source capture-primary ...` (ties into DB sources directly)

#### 4.2 Storage conventions (data repo)

- [ ] Define canonical path template (stable):
  - `reference/primary/<source-id>/<sha256>.pdf`
  - `reference/primary/<source-id>/<sha256>.meta.yaml`
  - `reference/primary/<source-id>/<sha256>.txt` (optional extracted text)
- [ ] Define required metadata fields:
  - `url`, `content_type`, `sha256`, `fetched_at`, `captured_by`, `notes` (optional)
- [ ] Define whether capture also creates/updates a `sources` row (recommended if DB should be auditable)

#### 4.3 Extraction/searchability (optional v1)

- [ ] Decide and document whether we do PDF → text extraction in framework tooling (and which library)
- [ ] If not implemented, document the manual fallback (“store PDF + cite page numbers”)

### Phase 5: Corrections/Updates Workflow + Guardrails

Leverage existing supersedes semantics instead of inventing a parallel system unless needed.

- [ ] Define a correction workflow that is:
  - append-only (new evidence links/trails supersede old)
  - easy to execute (explicit commands)
- [ ] Decide whether we need a dedicated DB table for corrections, or whether:
  - “Corrections & Updates” live in analysis markdown only, and
  - DB-level corrections are encoded as `supersedes_id` relationships in evidence links/trails.
- [ ] If DB-level: add schema + CLI + validation + export + tests

### Phase 6: Review/Disagreement Ergonomics (optional v1)

- [ ] Decide whether to add `reasoning_trails.status=proposed` (recommended)
- [ ] If adding statuses:
  - update schema, CLI choices, validation rules, and exports
  - ensure proposed trails do not trigger “staleness” warnings
  - ensure proposed trails do not satisfy high-credence backing requirements
- [ ] Add workflow docs:
  - how to register a review transcript as a source (`type=CONVO`)
  - how to attach review feedback as proposed trails without mutating claim credence

## Resolved Decisions

### D1: Where do Layer/Actor/Scope/Quantifier/Evidence Type live?

**Resolution**: Hybrid A + C
- **Claim-level fields** (Layer, Actor, Scope, Quantifier) → Analysis tables only
- **Evidence-level fields** (evidence_type, claim_match, court_posture, court_voice) → `evidence_links` table

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d1-where-do-layeractorscopequantifierevidence-type-live) for full analysis.

### D2: Minimal "Scope schema"

**Resolution**: Mini-schema string with key-value convention (`who=...; where=...; when=...; process=...; predicate=...; conditions=...`). Light validation (non-empty for high-impact claims); key set intentionally fluid for v1.

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d2-minimal-scope-schema) for full analysis.

### D3: Enumerations + enforcement level

**Resolution**: Hybrid enforcement. Layer is strict (ASSERTED/LAWFUL/PRACTICED/EFFECT only). Quantifier is strict with `OTHER:<text>` escape hatch. Actor and Evidence Type are guidance-only with canonical lists and `OTHER:<text>` allowed. `N/A` permitted when genuinely not applicable.

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d3-enumerations--enforcement-level) for full analysis.

### D4: High-impact thresholds + primary capture gate severity

**Resolution**: Plan thresholds (credence≥0.7 OR E1/E2 OR Layer=LAWFUL). WARN default, ERROR with `--rigor`. Explicit "capture failed: [reason]" path required when capture not possible.

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d4-high-impact-thresholds--primary-capture-gate-severity) for full analysis.

### D5: Copyright/licensing posture for capture

**Resolution**: Capture everything (fair use for research). Two storage tiers: `reference/primary/` (public, git-tracked) for government/legal docs; `reference/captured/` (metadata tracked; captured content ignored) for copyrighted material. Future: private archive for litigious items.

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d5-copyrightlicensing-posture-for-capture) for full analysis.

### D6: Review/disagreement representation

**Resolution**: Add `proposed` and `retracted` to `reasoning_trails.status`. Proposed trails don't satisfy backing requirements or trigger staleness. Review transcripts can be stored as `sources(type=CONVO)`. Formalized workflow: propose → investigate → adopt or retract.

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d6-reviewdisagreement-representation) for full analysis.

### D7: Evidence Type ↔ Evidence Level guidance

**Resolution**: Evidence Type is purely descriptive; no auto-mapping to E-levels. Layer-aware guidance: ASSERTED claims can get E1/E2 from primary docs; LAWFUL claims require controlling law + court hygiene (posture/voice); PRACTICED and EFFECT claims require independent evidence. Key principle: "Document proves assertion was made, not that it's lawful or practiced."

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d7-evidence-type--evidence-level-guidance) for full analysis.

### D8: EFFECT-layer guardrails (avoid causal leaps)

**Resolution**: Soft guardrails. EFFECT claims require: mechanism statement, scope bounding, alternative explanations acknowledgment. Validator WARNs if credence≥0.6 without DATA/STUDY evidence. Default EFFECT claims to type `[H]` (Hypothesis) unless strong causal evidence justifies `[F]`.

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d8-effect-layer-guardrails-avoid-causal-leaps) for full analysis.

### D9: Recency metadata (`accessed` vs `last_checked`)

**Resolution**: Add `sources.last_checked` (optional string) to schema. `accessed` = first access; `last_checked` = last verification. Enables staleness queries and corrections workflows. Capture sidecar (D5) handles per-artifact fetch timestamps.

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d9-recency-metadata-accessed-vs-last_checked) for full analysis.

### D10: Backwards-compatibility + strictness defaults

**Resolution**: Dual-support transition. WARN default for all new requirements; `--rigor` flag for ERROR mode. Support both v1 and rigor-v1 table formats indefinitely. Add `realitycheck_version` to capture sidecars. Never break existing repos silently.

See [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#d10-backwards-compatibility--strictness-defaults) for full analysis.

## Worklog

### 2026-01-31: All decisions (D1–D10) resolved

Collaborative decision session with human reviewer, Claude Opus 4.5, and Codex input. Key outcomes:

- **D1**: Hybrid A+C — claim-level fields (Layer/Actor/Scope/Quantifier) in analysis tables only; evidence-level fields (`evidence_type`, `claim_match`, `court_posture`, `court_voice`) added to `evidence_links` schema
- **D2**: Mini-schema string for Scope (`who=...; where=...; when=...`)
- **D3**: Strict enum for Layer; guidance + `OTHER:<text>` escape hatch for others
- **D4**: Plan thresholds (credence≥0.7 OR E1/E2 OR LAWFUL) + WARN default + capture-failed path
- **D5**: Capture everything (fair use); two storage tiers (`reference/primary/` public, `reference/captured/` metadata tracked; content ignored)
- **D6**: Add `proposed` and `retracted` to `reasoning_trails.status`
- **D7**: Evidence Type is descriptive only; layer-aware E-level guidance documented
- **D8**: Soft guardrails for EFFECT claims; default to type `[H]`; template prompts for mechanism/confounders
- **D9**: Add `sources.last_checked` to schema
- **D10**: Dual-support transition; WARN default; `--rigor` flag; version tracking in sidecars

Full analysis documented in [PLAN-analysis-rigor-improvement.md § Decision Log](PLAN-analysis-rigor-improvement.md#decision-log).

Next: Phase 1 (tests first), then implementation.

### 2026-01-31: Rigor contract implemented (docs + templates)

- Added `docs/WORKFLOWS.md` “Analysis Rigor Contract (v1)” section (pinned table schemas + artifact linkage).
- Updated analysis table templates and skill templates; regenerated assembled skills (`make assemble-skills`).

### 2026-01-31: Implementation punchlist created

- Reviewed [docs/TODO.md](TODO.md) and [docs/PLAN-analysis-rigor-improvement.md](PLAN-analysis-rigor-improvement.md)
- Audited current templates (`integrations/_templates/`) and analysis contract enforcement (`scripts/analysis_validator.py`, `scripts/analysis_formatter.py`)
- Wrote this implementation plan with explicit open decisions and a tests-first punchlist
