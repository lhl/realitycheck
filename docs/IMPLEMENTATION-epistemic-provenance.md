# Implementation: Epistemic Provenance (Reasoning Trails)

**Status**: Not Started
**Plan**: [PLAN-epistemic-provenance.md](PLAN-epistemic-provenance.md)
**Started**: 2026-01-30

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

### Phase 1: Tests First (per Spec→Plan→Test→Implement)

#### 1.1 DB Tests (`tests/test_db.py`)

- [ ] `TestEvidenceLinksCRUD`
  - [ ] `test_add_evidence_link_creates_record`
  - [ ] `test_add_evidence_link_validates_claim_exists`
  - [ ] `test_add_evidence_link_validates_source_exists`
  - [ ] `test_add_evidence_link_auto_generates_id`
  - [ ] `test_add_evidence_link_all_directions` (supports/contradicts/strengthens/weakens)
  - [ ] `test_get_evidence_link_by_id`
  - [ ] `test_get_evidence_link_not_found`
  - [ ] `test_list_evidence_links_by_claim`
  - [ ] `test_list_evidence_links_by_source`
  - [ ] `test_list_evidence_links_by_direction`
  - [ ] `test_list_evidence_links_active_only_default`
  - [ ] `test_list_evidence_links_include_superseded`
  - [ ] `test_update_evidence_link_status_superseded`
  - [ ] `test_supersede_evidence_link_creates_new_with_reference`

- [ ] `TestReasoningTrailsCRUD`
  - [ ] `test_add_reasoning_trail_creates_record`
  - [ ] `test_add_reasoning_trail_validates_claim_exists`
  - [ ] `test_add_reasoning_trail_auto_generates_id`
  - [ ] `test_add_reasoning_trail_validates_evidence_links_exist`
  - [ ] `test_get_reasoning_trail_by_id`
  - [ ] `test_get_reasoning_trail_by_claim`
  - [ ] `test_get_reasoning_trail_not_found`
  - [ ] `test_list_reasoning_trails_by_claim`
  - [ ] `test_list_reasoning_trails_active_only_default`
  - [ ] `test_reasoning_history_shows_credence_evolution`
  - [ ] `test_supersede_reasoning_trail_creates_new_with_reference`

- [ ] `TestEvidenceCLI`
  - [ ] `test_evidence_add_minimal`
  - [ ] `test_evidence_add_full_options`
  - [ ] `test_evidence_add_missing_claim_errors`
  - [ ] `test_evidence_add_missing_source_errors`
  - [ ] `test_evidence_get_json_format`
  - [ ] `test_evidence_get_text_format`
  - [ ] `test_evidence_list_by_claim`
  - [ ] `test_evidence_list_by_source`
  - [ ] `test_evidence_list_format_options`
  - [ ] `test_evidence_supersede`

- [ ] `TestReasoningCLI`
  - [ ] `test_reasoning_add_minimal`
  - [ ] `test_reasoning_add_full_options`
  - [ ] `test_reasoning_add_with_evidence_refs`
  - [ ] `test_reasoning_add_with_counterarguments_json`
  - [ ] `test_reasoning_get_json_format`
  - [ ] `test_reasoning_get_text_format`
  - [ ] `test_reasoning_list_by_claim`
  - [ ] `test_reasoning_history`

#### 1.2 Validation Tests (`tests/test_validate.py`)

- [ ] `TestEvidenceLinksValidation`
  - [ ] `test_evidence_link_missing_claim_errors`
  - [ ] `test_evidence_link_missing_source_errors`
  - [ ] `test_evidence_link_invalid_direction_errors`
  - [ ] `test_evidence_link_invalid_status_errors`
  - [ ] `test_evidence_link_supersedes_nonexistent_warns`

- [ ] `TestReasoningTrailsValidation`
  - [ ] `test_reasoning_trail_missing_claim_errors`
  - [ ] `test_reasoning_trail_missing_evidence_link_warns`
  - [ ] `test_reasoning_trail_credence_mismatch_warns`
  - [ ] `test_reasoning_trail_evidence_level_mismatch_warns`

- [ ] `TestHighCredenceBackingValidation`
  - [ ] `test_high_credence_no_backing_warns` (≥0.7, no evidence links)
  - [ ] `test_high_credence_with_backing_passes`
  - [ ] `test_e1_e2_no_backing_warns`
  - [ ] `test_e1_e2_with_backing_passes`
  - [ ] `test_high_credence_backing_requires_location_warns` (soft)
  - [ ] `test_high_credence_backing_requires_reasoning_warns` (soft)
  - [ ] `test_strict_mode_errors_instead_of_warns`
  - [ ] `test_low_credence_no_backing_passes` (<0.7, E3-E6)

#### 1.3 Export Tests (`tests/test_export.py`)

- [ ] `TestExportReasoningMarkdown`
  - [ ] `test_export_reasoning_single_claim`
  - [ ] `test_export_reasoning_all_claims`
  - [ ] `test_export_reasoning_includes_evidence_table`
  - [ ] `test_export_reasoning_includes_counterarguments`
  - [ ] `test_export_reasoning_includes_trail_history`
  - [ ] `test_export_reasoning_includes_yaml_block`
  - [ ] `test_export_reasoning_relative_links_valid`
  - [ ] `test_export_reasoning_skips_claims_without_trails`

- [ ] `TestExportEvidenceIndex`
  - [ ] `test_export_evidence_by_source_single`
  - [ ] `test_export_evidence_by_source_all`
  - [ ] `test_export_evidence_by_claim_single`
  - [ ] `test_export_evidence_by_claim_all`

- [ ] `TestExportProvenanceYAML`
  - [ ] `test_export_provenance_yaml_evidence_links`
  - [ ] `test_export_provenance_yaml_reasoning_trails`
  - [ ] `test_export_provenance_yaml_deterministic_order`
  - [ ] `test_export_provenance_json_format`

#### 1.4 Validator/Formatter Tests

- [ ] `tests/test_analysis_validator.py`
  - [ ] `test_validate_linked_claim_id_extracts_id`
  - [ ] `test_validate_linked_claim_id_with_path`
  - [ ] `test_validate_mixed_linked_and_bare_ids`

- [ ] `tests/test_analysis_formatter.py`
  - [ ] `test_formatter_preserves_linked_ids`
  - [ ] `test_formatter_linkify_claim_ids_option` (optional enhancement)

#### 1.5 E2E Tests (`tests/test_e2e.py`)

- [ ] `test_provenance_workflow_full`
  - init → add source → add claim → add evidence link → add reasoning → validate → export reasoning

- [ ] `test_provenance_supersede_workflow`
  - add evidence → supersede with correction → validate shows current only → history shows both

---

### Phase 2: Schema + CRUD (`scripts/db.py`)

- [ ] Add `EVIDENCE_LINKS_SCHEMA` with fields:
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

- [ ] Add `REASONING_TRAILS_SCHEMA` with fields:
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

- [ ] Update `init_tables()` to create `evidence_links` and `reasoning_trails`
- [ ] Update `drop_tables()` to include new tables
- [ ] Update `get_stats()` to include new table counts

- [ ] Implement `add_evidence_link()`:
  - Auto-generate ID if not provided
  - Validate claim_id exists in claims
  - Validate source_id exists in sources
  - Set created_at timestamp
  - Return created record

- [ ] Implement `get_evidence_link(id)`:
  - Return single record or None

- [ ] Implement `list_evidence_links(claim_id=None, source_id=None, direction=None, include_superseded=False)`:
  - Filter by claim, source, direction
  - Default: only active status
  - Option to include superseded

- [ ] Implement `update_evidence_link(id, **fields)`:
  - Partial update support
  - For status changes, handle supersedes logic

- [ ] Implement `supersede_evidence_link(old_id, **new_fields)`:
  - Create new record with supersedes_id pointing to old
  - Update old record status to 'superseded'
  - Return new record

- [ ] Implement `add_reasoning_trail()`:
  - Auto-generate ID if not provided
  - Validate claim_id exists
  - Validate supporting_evidence/contradicting_evidence IDs exist (if provided)
  - Set created_at timestamp
  - Return created record

- [ ] Implement `get_reasoning_trail(id=None, claim_id=None)`:
  - Get by ID, or get **current active** trail for claim
  - Return single record or None
  - **Note**: Multiple trails can exist for a claim (agent disagreement, corrections).
    This function returns only the single active trail. Use `list_reasoning_trails()`
    or `get_reasoning_history()` to see all trails including superseded ones.

- [ ] Implement `list_reasoning_trails(claim_id=None, include_superseded=False)`:
  - Filter by claim
  - Default: only active status (one per claim unless disagreement)
  - With `include_superseded=True`: returns all trails for audit/history

- [ ] Implement `get_reasoning_history(claim_id)`:
  - Return **all** trails for claim ordered by created_at (oldest first)
  - Always includes superseded trails for full credence evolution history

- [ ] Implement `supersede_reasoning_trail(old_id, **new_fields)`:
  - Create new record with supersedes_id pointing to old
  - Update old record status to 'superseded'
  - Return new record

---

### Phase 3: CLI (`scripts/db.py`)

- [ ] Add `evidence` subparser with subcommands:
  - `add` with flags:
    - Required: `--claim-id`, `--source-id`, `--direction`
    - Optional: `--id`, `--strength`, `--location`, `--quote`, `--reasoning`, `--analysis-log-id`, `--created-by`
  - `get <id>` with `--format json|text`
  - `list` with filters:
    - `--claim-id`, `--source-id`, `--direction`
    - `--include-superseded`
    - `--format json|text`, `--limit`
  - `supersede <id>` with same flags as `add` (creates new, marks old superseded)

- [ ] Add `reasoning` subparser with subcommands:
  - `add` with flags:
    - Required: `--claim-id`, `--credence`, `--evidence-level`, `--reasoning-text`
    - Optional: `--id`, `--evidence-summary`, `--supporting-evidence` (comma-separated IDs), `--contradicting-evidence`, `--assumptions` (comma-separated), `--counterarguments-json`, `--analysis-pass`, `--analysis-log-id`, `--created-by`
  - `get` with `--id` or `--claim-id`, `--format json|text`
  - `list --claim-id` with `--include-superseded`, `--format json|text`, `--limit`
  - `history --claim-id` - show credence evolution over time

---

### Phase 4: Validation (`scripts/validate.py`)

- [ ] Add `validate_evidence_links()`:
  - Check all `claim_id` references exist
  - Check all `source_id` references exist
  - Check `direction` is valid enum
  - Check `status` is valid enum
  - Warn if `supersedes_id` references non-existent ID

- [ ] Add `validate_reasoning_trails()`:
  - Check all `claim_id` references exist
  - Check `supporting_evidence` IDs exist in evidence_links (if present)
  - Check `contradicting_evidence` IDs exist (if present)
  - Warn if `credence_at_time` differs from current claim credence
  - Warn if `evidence_level_at_time` differs from current claim evidence_level
  - Validate `counterarguments_json` is valid JSON (if present)

- [ ] Add `validate_high_credence_backing()`:
  - For claims with credence ≥ 0.7 OR evidence_level in [E1, E2]:
    - Check ≥1 evidence_links row with direction in [supports, strengthens]
    - If high-credence supporting link exists, check it has `location` (soft warn)
    - If high-credence supporting link exists, check it has `reasoning` (soft warn)
  - Emit WARN level (existing `--strict` flag escalates all warnings to errors)

- [ ] Wire new validation into `validate_db()` main function
  - Note: `--strict` flag already exists in validate.py:547, no changes needed to CLI

---

### Phase 5: Export / Render (`scripts/export.py`)

**Note**: Align with existing CLI pattern: `rc-export <format> <type> [options]`

- [ ] Implement `export_reasoning_md(claim_id, output_path)`:
  - Generate `{output_path}` (caller specifies full path) with:
    - Claim text, credence, evidence level, domain header
    - Evidence Summary table (direction, source, location, strength, summary)
    - Reasoning Chain section (from `reasoning_text`)
    - Counterarguments Considered section (from `counterarguments_json`)
    - Assumptions section
    - Trail History table (date, credence, pass, tool, notes)
    - Portable YAML block at bottom
  - Return path to generated file

- [ ] Implement `export_all_reasoning_md(output_dir)`:
  - Find all claims with reasoning trails
  - Generate `{output_dir}/{claim_id}.md` for each
  - Return list of generated paths

- [ ] Implement `export_evidence_by_source_md(source_id, output_path)`:
  - Generate `{output_path}` (caller specifies full path) with:
    - Source metadata header
    - Table of all claims this source supports/contradicts
  - Return path

- [ ] Implement `export_evidence_by_claim_md(claim_id, output_path)`:
  - Generate `{output_path}` (caller specifies full path) with:
    - Claim text header
    - Table of all evidence links for this claim
  - Return path

- [ ] Implement `export_provenance_yaml(output_path)`:
  - Export `evidence_links` and `reasoning_trails` tables
  - Deterministic ordering: by claim_id, then created_at, then id
  - Include active and superseded records (full history)

- [ ] Implement `export_provenance_json(output_path)`:
  - Same as YAML but JSON format

- [ ] Add CLI commands (following existing `rc-export <format> <type>` pattern):
  - Add `reasoning` type to `rc-export md`:
    - `rc-export md reasoning --id CLAIM-ID -o FILE` (single claim)
    - `rc-export md reasoning --all --output-dir DIR` (all claims)
  - Add `evidence` type to `rc-export md`:
    - `rc-export md evidence --claim-id ID -o FILE`
    - `rc-export md evidence --source-id ID -o FILE`
    - `rc-export md evidence --all --output-dir DIR`
  - Add `provenance` type to `rc-export yaml`:
    - `rc-export yaml provenance -o FILE`
  - Add `provenance` type to `rc-export json` (if json subcommand exists, else add it):
    - `rc-export json provenance -o FILE`

---

### Phase 6: Validator/Formatter Updates

- [ ] Update `scripts/analysis_validator.py`:
  - Modify claim ID extraction regex to handle `[ID](path)` format
  - Extract bare ID from markdown link for validation
  - Preserve linked format in output (don't strip links)

- [ ] Update `scripts/analysis_formatter.py`:
  - Preserve existing markdown links in claim ID cells
  - (Optional) Add `--linkify-claims` flag to convert bare IDs to links

- [ ] Add helper function `extract_claim_id(cell_text)`:
  - If bare ID: return as-is
  - If `[ID](path)`: extract and return ID
  - Handle edge cases (malformed links, etc.)

---

### Phase 7: Integration Templates

- [ ] Create `integrations/_templates/partials/provenance-workflow.md.j2`:
  - Reusable section for evidence linking + reasoning capture
  - Include CLI examples for `rc-db evidence add` and `rc-db reasoning add`

- [ ] Update `integrations/_templates/skills/check.md.j2`:
  - Add Step 5b: Evidence Linking (after claim extraction)
  - Add Step 6b: Reasoning Capture (after credence assignment)
  - Add Step 8: Render Reasoning Docs (after validation)
  - Include provenance-workflow partial

- [ ] Update `integrations/_templates/partials/db-commands.md.j2`:
  - Add `evidence` subcommand reference
  - Add `reasoning` subcommand reference

- [ ] Run `make assemble-skills` to regenerate all integration skills

---

### Phase 8: Documentation

- [ ] Update `docs/SCHEMA.md`:
  - Add `evidence_links` table definition
  - Add `reasoning_trails` table definition
  - Document validation rules for provenance
  - Add "Provenance Contract" section explaining minimum requirements

- [ ] Update `docs/WORKFLOWS.md`:
  - Add "Evidence Linking" workflow section
  - Add "Reasoning Capture" workflow section
  - Add "Rendering Provenance" section
  - Document `--strict` validation flag

- [ ] Create `methodology/reasoning-trails.md`:
  - Explain why provenance matters
  - Document the minimum provenance contract
  - Guidelines for writing good `reasoning_text`
  - Examples of counterargument documentation

- [ ] Update `docs/TODO.md`:
  - Mark Epistemic Provenance as complete

---

### Phase 9: Migration Support

- [ ] Update `rc-db migrate` to handle new tables:
  - Add `evidence_links` table if missing
  - Add `reasoning_trails` table if missing
  - Handle schema evolution for existing tables

- [ ] Update `rc-db init-project` to create provenance directories:
  - Add `analysis/reasoning/` to directory list (db.py:2037)
  - Add `analysis/evidence/by-claim/` to directory list
  - Add `analysis/evidence/by-source/` to directory list

- [ ] Test migration on existing databases

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
rc-export md evidence --claim-id TECH-2026-042 -o analysis/evidence/by-claim/TECH-2026-042.md
rc-export md evidence --source-id author-2024 -o analysis/evidence/by-source/author-2024.md
rc-export md evidence --all --output-dir analysis/evidence
rc-export yaml provenance -o analysis/provenance.yaml
rc-export json provenance -o analysis/provenance.json

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

---

*Last updated: 2026-01-30*
