# Implementation: Epistemic Provenance (Reasoning Trails)

**Status**: Complete (Phase 1-9)
**Plan**: [PLAN-epistemic-provenance.md](PLAN-epistemic-provenance.md)
**Started**: 2026-01-30
**Last Updated**: 2026-01-30

## Summary

Implement structured provenance for claim credence assignments:

- **`evidence_links` table**: Explicit links between claims and supporting/contradicting sources
- **`reasoning_trails` table**: Capture reasoning chain for credence assignments
- **Rendered artifacts**: Per-claim reasoning docs in data repo (`analysis/reasoning/`)
- **Validation**: Configurable enforcement that high-credence claims have backing
- **Workflow integration**: Evidence linking + reasoning capture in `/check`

## Affected Files

```
scripts/
 ├── UPDATE db.py                    # New tables + CLI subcommands
 ├── UPDATE validate.py              # High-credence backing validation
 ├── UPDATE export.py                # Reasoning rendering + provenance export
 ├── UPDATE analysis_validator.py    # Support markdown-linked IDs in tables
 └── UPDATE analysis_formatter.py    # Support markdown-linked IDs in tables

tests/
 ├── UPDATE test_db.py               # evidence/reasoning CRUD + CLI tests
 ├── UPDATE test_validate.py         # High-credence backing validation tests
 ├── UPDATE test_export.py           # Reasoning rendering tests
 ├── UPDATE test_e2e.py              # End-to-end with evidence linking
 ├── UPDATE test_analysis_validator.py  # Linked ID tests
 └── UPDATE test_analysis_formatter.py  # Linked ID tests

docs/
 ├── UPDATE SCHEMA.md                # Add evidence_links + reasoning_trails tables
 ├── UPDATE WORKFLOWS.md             # Document reasoning capture workflow
 ├── UPDATE TODO.md                  # Mark as in-progress/complete
 └── THIS FILE                       # Implementation tracking

integrations/_templates/
 ├── UPDATE skills/check.md.j2       # Add evidence linking + reasoning steps
 ├── UPDATE tables/claim-summary.md.j2  # Support reasoning links in ID column
 ├── UPDATE partials/db-commands.md.j2  # Add evidence/reasoning CLI reference
 └── NEW partials/provenance-workflow.md.j2  # Reusable provenance capture section

methodology/
 └── NEW reasoning-trails.md         # Methodology for reasoning capture
```

## Resolved Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Versioning model | Explicit `status`/`supersedes_id` | Rigorous audit trail, supports agent disagreement tracking |
| Auto-linking from `source_ids` | Explicit only (v1) | Extraction ≠ support; avoid false confidence |
| Formatter/validator linked IDs | Update to support `[ID](path)` | Cleanest UX, enables inline reasoning links |
| Validation threshold | Reuse existing `--strict` flag | High-credence backing emits WARNs; existing `--strict` escalates to errors |
| CLI namespace | Flat (`rc-db evidence`, `rc-db reasoning`) | Simpler, follows existing pattern |
| ID format | `EVLINK-YYYY-NNN`, `REASON-YYYY-NNN` | No domain prefix needed for supporting data |
| Evidence granularity | Per-source with optional `location` | Specific locations when needed, not required |
| Rendering trigger | On-demand (`rc-export md reasoning`) | Avoid heavyweight auto-generation |
| `reasoning_text` storage | Both explicit text + structured fields | Text is publishable rationale, structured enables analysis |
| Evidence snapshots | Deferred to future | Out of scope for v1 |

---

## Punchlist

### Phase 1: Tests First (per Spec→Plan→Test→Implement) ✅ COMPLETE

#### 1.1 DB Tests (`tests/test_db.py`) ✅

- [x] `TestEvidenceLinksCRUD` - All 14 tests passing
- [x] `TestReasoningTrailsCRUD` - All 11 tests passing
- [x] `TestEvidenceCLI` - All 10 tests passing
- [x] `TestReasoningCLI` - All 8 tests passing

#### 1.2 Validation Tests (`tests/test_validate.py`) ✅

- [x] `TestEvidenceLinksValidation` - All 5 tests passing
- [x] `TestReasoningTrailsValidation` - All 4 tests passing
- [x] `TestHighCredenceBackingValidation` - All 8 tests passing

#### 1.3 Export Tests (`tests/test_export.py`) ✅

- [x] `TestExportReasoningMarkdown` - All 7 tests passing
- [x] `TestExportEvidenceIndex` - All 2 tests passing
- [x] `TestExportProvenanceYAML` - All 4 tests passing

#### 1.4 Validator/Formatter Tests ✅

- [x] `tests/test_analysis_validator.py` - TestExtractClaimId (5 tests), linked ID tests (2 tests)
- [x] `tests/test_analysis_formatter.py` - TestLinkedClaimIds (9 tests)

#### 1.5 E2E Tests (`tests/test_e2e.py`)

- [x] Provenance validation integrated into existing E2E tests
- [ ] `test_provenance_workflow_full` - Future enhancement
- [ ] `test_provenance_supersede_workflow` - Future enhancement

---

### Phase 2: Schema + CRUD (`scripts/db.py`) ✅ COMPLETE

- [x] Add `EVIDENCE_LINKS_SCHEMA` with fields:
  - `id` (string, required) - `EVLINK-YYYY-NNN`
  - `claim_id` (string, required)
  - `source_id` (string, required)
  - `direction` (string, required) - supports/contradicts/strengthens/weakens
  - `status` (string, required) - active/superseded/retracted
  - `supersedes_id` (string, nullable) - pointer for corrections
  - `strength` (float32, nullable) - coarse impact estimate
  - `location` (string, nullable) - specific location in source
  - `quote` (string, nullable) - relevant excerpt
  - `reasoning` (string, nullable) - why this evidence matters
  - `analysis_log_id` (string, nullable) - link to audit log pass
  - `created_at` (string, required)
  - `created_by` (string, required)

- [x] Add `REASONING_TRAILS_SCHEMA` with fields:
  - `id` (string, required) - `REASON-YYYY-NNN`
  - `claim_id` (string, required)
  - `status` (string, required) - active/superseded
  - `supersedes_id` (string, nullable)
  - `credence_at_time` (float32, required)
  - `evidence_level_at_time` (string, required)
  - `evidence_summary` (string, nullable)
  - `supporting_evidence` (list[string], nullable) - evidence link IDs
  - `contradicting_evidence` (list[string], nullable) - evidence link IDs
  - `assumptions_made` (list[string], nullable)
  - `counterarguments_json` (string, nullable) - JSON-encoded list
  - `reasoning_text` (string, required) - publishable rationale
  - `analysis_pass` (int32, nullable)
  - `analysis_log_id` (string, nullable)
  - `created_at` (string, required)
  - `created_by` (string, required)

- [x] Update `init_tables()` to create `evidence_links` and `reasoning_trails`
- [x] Update `drop_tables()` to include new tables
- [x] Update `get_stats()` to include new table counts
- [x] Implement all evidence link CRUD functions
- [x] Implement all reasoning trail CRUD functions

---

### Phase 3: CLI (`scripts/db.py`) ✅ COMPLETE

- [x] Add `evidence` subparser with all subcommands (add, get, list, supersede)
- [x] Add `reasoning` subparser with all subcommands (add, get, list, history)
- [x] Add text format output for evidence_link and reasoning_trail records

---

### Phase 4: Validation (`scripts/validate.py`) ✅ COMPLETE

- [x] Add evidence links validation (claim/source exist, direction/status valid, supersedes reference)
- [x] Add reasoning trails validation (claim exists, evidence links exist, credence/level staleness)
- [x] Add high-credence backing validation (≥0.7 or E1/E2 requires evidence)
- [x] Support `--strict` flag to escalate warnings to errors
- [x] Wire new validation into `validate_db()` main function

---

### Phase 5: Export / Render (`scripts/export.py`) ✅ COMPLETE

- [x] Implement `export_reasoning_md()` - per-claim reasoning docs with evidence table, counterarguments, history
- [x] Implement `export_reasoning_all_md()` - export all claims with trails
- [x] Implement `export_evidence_by_claim_md()` - evidence links for a claim
- [x] Implement `export_evidence_by_source_md()` - evidence links from a source
- [x] Implement `export_provenance_yaml()` - deterministic YAML export
- [x] Implement `export_provenance_json()` - deterministic JSON export
- [x] Add CLI commands:
  - `rc-export md reasoning --id CLAIM-ID` / `--all --output DIR`
  - `rc-export md evidence-by-claim --id CLAIM-ID`
  - `rc-export md evidence-by-source --id SOURCE-ID`
  - `rc-export provenance --format yaml|json`

---

### Phase 6: Validator/Formatter Updates ✅ COMPLETE

- [x] Update `scripts/analysis_validator.py`:
  - Added `BARE_CLAIM_ID_RE` and `LINKED_CLAIM_ID_RE` regex patterns
  - Added `extract_claim_id()` helper function
  - Validation already handles linked IDs (regex matches inside links)

- [x] Update `scripts/analysis_formatter.py`:
  - Added `extract_claim_id()` and `is_linked_claim_id()` helpers
  - `extract_claims_from_key_claims_table()` stores `id_display` for linked IDs
  - `build_claim_summary_table()` uses `id_display` if present (preserves links)

- [x] Tests added:
  - `tests/test_analysis_validator.py`: TestExtractClaimId class, linked ID tests
  - `tests/test_analysis_formatter.py`: TestLinkedClaimIds class

---

### Phase 7: Integration Templates ✅ COMPLETE

- [x] Create `integrations/_templates/partials/provenance-workflow.md.j2`:
  - Reusable section for evidence linking + reasoning capture
  - CLI examples for `rc-db evidence add` and `rc-db reasoning add`
  - Guidelines for when to capture provenance

- [x] Update `integrations/_templates/skills/check.md.j2`:
  - Added Step 9: Provenance (for high-credence claims)
  - Included provenance-workflow partial after db-commands

- [x] Update `integrations/_templates/partials/db-commands.md.j2`:
  - Added `evidence` CLI section (add, list, get, supersede)
  - Added `reasoning` CLI section (add, get, list, history)
  - Added provenance export commands
  - Added `--strict` flag documentation

- [x] Run `make assemble-skills` - 5 files regenerated (check skills + check-core.md)

---

### Phase 8: Documentation ✅ COMPLETE

- [x] Update `docs/SCHEMA.md`:
  - Added `evidence_links` table definition (13 fields)
  - Added `reasoning_trails` table definition (16 fields)
  - Added validation rules 10-12 for provenance
  - Documented counterarguments JSON format

- [x] Update `docs/WORKFLOWS.md`:
  - Added "Evidence Linking Workflow" section
  - Added "Reasoning Trails Workflow" section
  - Added "Export Provenance" section
  - Documented all CLI commands with examples

- [x] Create `methodology/reasoning-trails.md`:
  - Explained why provenance matters
  - Documented minimum provenance contract
  - Guidelines for writing good `reasoning_text`
  - Counterarguments format documentation
  - Design philosophy section

- [x] Update `docs/TODO.md`:
  - Updated Epistemic Provenance status to Phase 1-8 Complete

---

### Phase 9: Migration Support ✅ COMPLETE

- [x] Update `rc-db migrate` to handle new tables:
  - Added `evidence_links` and `reasoning_trails` to expected_schemas
  - Migrate now creates new tables if they don't exist (not just columns)
  - Updated output to show created tables

- [x] Update `rc-db init-project` to create provenance directories:
  - Added `analysis/reasoning/` to directory list
  - Added `analysis/evidence/by-claim/` to directory list
  - Added `analysis/evidence/by-source/` to directory list

- [x] All tests pass (366 passed, 17 skipped)

---

## Test Commands

```bash
# Run all tests
uv run pytest -v

# Run only provenance-related tests
uv run pytest -v -k "evidence or reasoning or provenance"

# Run with coverage
uv run pytest --cov=scripts --cov-report=term-missing -k "evidence or reasoning"

# Validate after implementation
uv run rc-validate
uv run rc-validate --strict
```

---

## CLI Reference (Planned)

```bash
# Evidence linking
rc-db evidence add --claim-id TECH-2026-042 --source-id author-2024 \
  --direction supports --strength 0.8 --location "Table 3, p.15" \
  --reasoning "Direct measurement of X supports the claim"

rc-db evidence list --claim-id TECH-2026-042
rc-db evidence list --source-id author-2024
rc-db evidence list --direction supports --limit 20

rc-db evidence get EVLINK-2026-001
rc-db evidence get EVLINK-2026-001 --format text

rc-db evidence supersede EVLINK-2026-001 --direction weakens \
  --reasoning "Re-evaluated: methodology concerns reduce support"

# Reasoning trails
rc-db reasoning add --claim-id TECH-2026-042 --credence 0.75 \
  --evidence-level E2 \
  --evidence-summary "E2 based on 2 supporting sources, 1 weak counter" \
  --supporting-evidence EVLINK-2026-001,EVLINK-2026-002 \
  --contradicting-evidence EVLINK-2026-003 \
  --reasoning-text "Assigned 0.75 because: (1) Two independent studies... (2) One contradicting..."

rc-db reasoning get --claim-id TECH-2026-042
rc-db reasoning get --id REASON-2026-001 --format text

rc-db reasoning list --claim-id TECH-2026-042
rc-db reasoning history --claim-id TECH-2026-042

# Export / Render (follows existing rc-export <format> <type> pattern)
rc-export md reasoning --id TECH-2026-042 -o analysis/reasoning/TECH-2026-042.md
rc-export md reasoning --all --output-dir analysis/reasoning
rc-export md evidence-by-claim --id TECH-2026-042 -o analysis/evidence/by-claim/TECH-2026-042.md
rc-export md evidence-by-source --id author-2024 -o analysis/evidence/by-source/author-2024.md
rc-export provenance --format yaml -o analysis/provenance.yaml
rc-export provenance --format json -o analysis/provenance.json

# Validation (--strict already exists, escalates WARNs to errors)
rc-validate                    # Warnings for missing backing
rc-validate --strict           # Errors for missing backing
```

---

## Worklog

### 2026-01-30: Planning

- Created this implementation document
- Resolved all open questions from PLAN
- Defined 9 implementation phases
- Detailed test plan with ~60 test cases
- Ready for Phase 1 (tests first)

### 2026-01-30: Review Feedback Fixes

Applied fixes from code review:

1. **--strict reuse**: Removed "add --strict" from Phase 4; existing flag in validate.py:547 already escalates warnings to errors
2. **Export CLI alignment**: Updated Phase 5 to follow existing `rc-export <format> <type>` pattern instead of new subcommands
3. **Output-dir semantics**: Changed export functions to write directly to caller-specified path (no auto-created subdirectories)
4. **Missing tests**: Added `test_export_evidence_by_claim_single` and `test_export_evidence_by_claim_all` to Phase 1
5. **Multiple trails clarification**: Added API semantics note explaining `get_reasoning_trail()` returns active only, while `list/history` show all
6. **init-project dirs**: Added `analysis/reasoning/` and `analysis/evidence/` to Phase 9

Also fixed in PLAN doc:
- Normalized counterargument disposition enum to `integrated|discounted|unresolved`
- Fixed template reference from `claim-table.md.j2` to `tables/claim-summary.md.j2`

### 2026-01-30: Implementation (Phases 1-5 Complete)

Completed core implementation of epistemic provenance feature:

**Phase 1-3 (Schema + CRUD + CLI)**:
- Added `EVIDENCE_LINKS_SCHEMA` (13 fields) and `REASONING_TRAILS_SCHEMA` (16 fields)
- Implemented all CRUD functions: `add_evidence_link`, `get_evidence_link`, `list_evidence_links`, `update_evidence_link`, `supersede_evidence_link`
- Implemented reasoning functions: `add_reasoning_trail`, `get_reasoning_trail`, `list_reasoning_trails`, `get_reasoning_history`, `supersede_reasoning_trail`
- Added CLI subparsers: `rc-db evidence` and `rc-db reasoning` with add/get/list/supersede/history commands
- Added text format output for evidence_link and reasoning_trail records

**Phase 4 (Validation)**:
- Added evidence links validation (claim/source references, direction/status enums, supersedes references)
- Added reasoning trails validation (claim references, evidence link references, credence/level staleness warnings)
- Added high-credence backing validation (≥0.7 or E1/E2 requires evidence, location/reasoning soft warnings)
- Wired `strict` parameter to `validate_db()` for error escalation

**Phase 5 (Export)**:
- Implemented `export_reasoning_md()` with evidence table, counterarguments, trail history, portable YAML block
- Implemented `export_reasoning_all_md()` for bulk export
- Implemented `export_evidence_by_claim_md()` and `export_evidence_by_source_md()`
- Implemented `export_provenance_yaml()` and `export_provenance_json()` with deterministic ordering
- Added CLI: `rc-export md reasoning`, `rc-export md evidence-by-claim`, `rc-export md evidence-by-source`, `rc-export provenance`

**Test Results**: 350 passed, 17 skipped (embedding tests)

### 2026-01-30: Phases 6-9 Complete

Completed remaining implementation phases:

**Phase 6 (Validator/Formatter)**:
- Added `extract_claim_id()` and `is_linked_claim_id()` helpers to both validator and formatter
- Formatter now preserves linked IDs through `id_display` field in claim records
- Added TestExtractClaimId (5 tests) and TestLinkedClaimIds (9 tests)
- All 74 validator/formatter tests pass

**Phase 7 (Integration Templates)**:
- Created `partials/provenance-workflow.md.j2` for evidence linking + reasoning capture
- Updated `skills/check.md.j2` with Step 9: Provenance + included partial
- Updated `partials/db-commands.md.j2` with evidence/reasoning CLI + provenance exports
- Ran `make assemble-skills` - regenerated 5 files

**Phase 8 (Documentation)**:
- Updated `docs/SCHEMA.md` with evidence_links and reasoning_trails tables
- Added validation rules 10-12 for provenance
- Updated `docs/WORKFLOWS.md` with Evidence Linking, Reasoning Trails, and Export Provenance sections
- Created `methodology/reasoning-trails.md` with full provenance methodology
- Updated `docs/TODO.md` status

**Phase 9 (Migration Support)**:
- Updated `rc-db migrate` to create missing tables (evidence_links, reasoning_trails)
- Added tables to expected_schemas for column migration
- Updated `rc-db init-project` to create provenance directories

**Test Results**: 366 passed, 17 skipped (embedding tests)

---

*Last updated: 2026-01-30*
