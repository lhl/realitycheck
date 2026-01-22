# Implementation: Skill Template Refactor

**Status**: Complete (pending review)
**Plan**: [PLAN-skill-template-refactor.md](PLAN-skill-template-refactor.md)
**Related**: [PLAN-quality-regression-fix.md](PLAN-quality-regression-fix.md)
**Started**: 2026-01-22

## Summary

Refactor skill generation to use Jinja2 templates with DRY partials. This consolidates manually-maintained SKILL.md files into a template system that generates **21 skills (7 per integration x 3 integrations)** from ~30 template files.

**Key goals:**
1. Single source of truth for methodology content
2. Restore quality lost during over-trimming (see quality regression fix)
3. Generate all skills for all integrations (Amp, Claude, Codex)
4. Add validator/formatter for machine-checkable output contract

### Exception: `realitycheck` Skill

The `realitycheck` skill is **not templated** because it serves fundamentally different purposes per integration:

| Integration | Purpose | Status |
|-------------|---------|--------|
| **Claude** | Simple alias for `/check` | Manual (unchanged) |
| **Codex** | Utilities wrapper (`$realitycheck stats`, `search`, etc.) | Manual (unchanged) |
| **Amp** | N/A (uses `realitycheck-check` instead) | - |

These manual skills don't suffer from the quality regression (they're not methodology-heavy) and work well as-is.

**Final count**: 21 generated + 2 manual = 23 total skills

---

## Punchlist

### Phase 1: Template Structure + Partials (from POC)
- [x] Create `integrations/_templates/` directory structure
- [x] `partials/legends.md.j2` - Claim types + evidence quick reference
- [x] `partials/evidence-hierarchy.md.j2` - Full table with weights
- [x] `partials/claim-types.md.j2` - With definitions
- [x] `partials/domain-codes.md.j2`
- [x] `partials/claim-relationships.md.j2` - ->+, ->x, ->?, etc.
- [x] `partials/confidence-calibration.md.j2`
- [x] `partials/db-commands.md.j2`
- [x] `partials/prerequisites.md.j2`

### Phase 2: Table Templates (Quality Restoration)
- [x] `tables/key-claims.md.j2` - Full table with Verified?/Falsifiable By
- [x] `tables/claim-summary.md.j2`
- [x] `tables/factual-claims-verified.md.j2` - With Crux? column
- [x] `tables/disconfirming-evidence.md.j2`
- [x] `tables/internal-tensions.md.j2`
- [x] `tables/persuasion-techniques.md.j2`
- [x] `tables/unstated-assumptions.md.j2`
- [x] `tables/supporting-contradicting.md.j2`

### Phase 3: Section Templates
- [x] `sections/argument-structure.md.j2`
- [x] `sections/theoretical-lineage.md.j2`
- [x] `sections/confidence-assessment.md.j2`

### Phase 4: Skill Templates
- [x] `skills/check.md.j2` - Full workflow with all tables/sections
- [x] `skills/analyze.md.j2` - Manual 3-stage
- [x] `skills/extract.md.j2` - Quick extraction
- [x] `skills/search.md.j2`
- [x] `skills/validate.md.j2`
- [x] `skills/export.md.j2`
- [x] `skills/stats.md.j2`

### Phase 5: Integration Wrappers
- [x] `wrappers/amp.md.j2`
- [x] `wrappers/claude.md.j2`
- [x] `wrappers/codex.md.j2`

### Phase 6: Configuration
- [x] `_config/skills.yaml` - All skill definitions + per-integration metadata
- [x] Added `jinja2>=3.1.0` to dev dependencies in `pyproject.toml`

### Phase 7: Build Script
- [x] `integrations/assemble.py`
- [x] `--integration` filter (amp/claude/codex/all)
- [x] `--skill` filter
- [x] `--dry-run` mode
- [x] `--diff` mode
- [x] `--check` mode
- [ ] Frontmatter validation (deferred)

### Phase 8: Makefile & CI
- [x] `make assemble-skills` target
- [x] `make check-skills` target
- [x] Update install scripts for new skills
- [x] Generated file header markers

### Phase 9: Cleanup & Documentation
- [x] Update `integrations/README.md`
- [x] Update `CONTRIBUTING.md`
- [x] Generate `methodology/workflows/check-core.md` from templates (read-only reference)
- [x] Add `--docs` flag to `assemble.py` for check-core.md generation

### Phase 10: Validator & Formatter
- [x] `_templates/analysis/source-analysis-full.md.j2` - Analysis skeleton template
- [x] `_templates/analysis/source-analysis-quick.md.j2` - Quick analysis skeleton
- [x] `scripts/analysis_validator.py`
- [x] `scripts/analysis_formatter.py`
- [x] Tests for validator/formatter
- [ ] Claude plugin hook integration (deferred)
- [ ] Document manual invocation (deferred)

---

## Worklog

### 2026-01-22: Phase 10 complete

**Created analysis skeleton templates:**
- `_templates/analysis/source-analysis-full.md.j2` - Full 3-stage analysis skeleton with all required sections
- `_templates/analysis/source-analysis-quick.md.j2` - Quick analysis skeleton for cross-reference sources

**Created validator script (`scripts/analysis_validator.py`):**
- Validates analysis files against Output Contract
- Detects profile (full/quick) from content
- Checks required sections, tables, elements
- Validates claim ID format (DOMAIN-YYYY-NNN)
- Warns about framework repo paths
- Supports `--profile`, `--strict`, `--json`, `--quiet` flags

**Created formatter script (`scripts/analysis_formatter.py`):**
- Inserts missing legends, sections, tables, YAML blocks
- Idempotent (safe to run multiple times)
- Preserves existing content
- Supports `--profile`, `--dry-run`, `--quiet` flags

**Created tests:**
- `tests/test_analysis_validator.py` (25 tests)
- `tests/test_analysis_formatter.py` (29 tests)

**Fixed Makefile issues:**
- Changed `assemble-skills`/`check-skills` to use `uv run python` (jinja2 dependency)
- Fixed `init` target to require `REALITYCHECK_DATA` env var (prevents footgun)
- Updated help text for `init` and `clean` targets

### 2026-01-22: Phase 9 complete

- Updated `integrations/README.md` with template system documentation
- Updated `CONTRIBUTING.md` with skill development guide
- Added `--docs` flag to `assemble.py` to generate `methodology/workflows/check-core.md`
- `check-core.md` is now generated from templates (read-only reference)
- Updated Makefile to include `--docs` flag in assemble targets

### 2026-01-22: Documentation fixes

- Removed empty `_templates/analysis/` directory (placeholder for Phase 10)
- Added `jinja2>=3.1.0` to dev dependencies in `pyproject.toml`
- Fixed skill count in docs: 21 generated (7 x 3), not 24
- Documented `realitycheck` exception (manual skills, not templated)
- Clarified Phase 9: generate `check-core.md` from templates as read-only reference
- Updated install scripts for new skills (Amp, Codex)

### 2026-01-22: Implementation (Phase 1-8)

**Completed Phases 1-7 + partial Phase 8:**

1. Created directory structure: `_templates/{partials,tables,sections,skills,wrappers}`, `_config/`

2. Created 8 partials:
   - `legends.md.j2` - Top-of-file claim types + evidence quick ref
   - `evidence-hierarchy.md.j2` - Full E1-E6 table with credence ranges
   - `claim-types.md.j2` - F/T/H/P/A/C/S/X definitions
   - `domain-codes.md.j2` - TECH/LABOR/ECON/etc.
   - `claim-relationships.md.j2` - ->+, ->x, ->?, etc.
   - `confidence-calibration.md.j2` - Calibration guidelines
   - `db-commands.md.j2` - CLI reference
   - `prerequisites.md.j2` - Env setup + red flags

3. Created 8 table templates (restored from POC AGENTS.md):
   - `key-claims.md.j2` - With Verified?/Falsifiable By columns
   - `claim-summary.md.j2` - Compact all-claims table
   - `factual-claims-verified.md.j2` - With Crux? column
   - `disconfirming-evidence.md.j2` - Counterevidence search
   - `internal-tensions.md.j2` - Self-contradictions
   - `persuasion-techniques.md.j2` - Rhetorical devices
   - `unstated-assumptions.md.j2` - Hidden premises
   - `supporting-contradicting.md.j2` - Theory relationships

4. Created 3 section templates:
   - `argument-structure.md.j2` - Logical flow diagram
   - `theoretical-lineage.md.j2` - Intellectual history
   - `confidence-assessment.md.j2` - End-of-analysis score

5. Created 7 skill templates:
   - `check.md.j2` - Full workflow (comprehensive, includes all tables/sections)
   - `analyze.md.j2` - Manual 3-stage
   - `extract.md.j2` - Quick extraction
   - `search.md.j2`, `validate.md.j2`, `export.md.j2`, `stats.md.j2`

6. Created 3 integration wrappers:
   - `claude.md.j2` - /command syntax + allowed-tools
   - `codex.md.j2` - $command syntax
   - `amp.md.j2` - Natural language triggers

7. Created `_config/skills.yaml` with all skill definitions

8. Created `assemble.py` build script with --integration, --skill, --dry-run, --diff, --check modes

9. Added Makefile targets: `make assemble-skills`, `make check-skills`

10. Generated 21 skills (7 skills x 3 integrations)

**Remaining:**
- Phase 9: Update docs, generate check-core.md from templates
- Phase 10: Validator & Formatter (machine-checkable output contract)

### 2026-01-22: Planning

- Created PLAN-skill-template-refactor.md
- Integrated quality regression fix requirements
- Identified ~30 template files needed
- Estimated 15-20 hours total effort
- Created this implementation tracking doc

---

## Files Created

| Path | Purpose |
|------|---------|
| `integrations/_templates/partials/*.md.j2` | 8 shared partials |
| `integrations/_templates/tables/*.md.j2` | 8 table templates |
| `integrations/_templates/sections/*.md.j2` | 3 section templates |
| `integrations/_templates/skills/*.md.j2` | 7 skill templates |
| `integrations/_templates/wrappers/*.md.j2` | 3 integration wrappers |
| `integrations/_config/skills.yaml` | Skill definitions |
| `integrations/assemble.py` | Build script |

## Files Generated (by assemble.py)

These are **generated outputs** - edit the templates, not these files directly:

| Path | Count | Notes |
|------|-------|-------|
| `integrations/amp/skills/realitycheck-*/SKILL.md` | 7 | Generated |
| `integrations/claude/skills/*/SKILL.md` | 7 | Generated (except `realitycheck`) |
| `integrations/codex/skills/*/SKILL.md` | 7 | Generated (except `realitycheck`) |

## Files Kept Manual (Not Templated)

| Path | Reason |
|------|--------|
| `integrations/claude/skills/realitycheck/SKILL.md` | Alias skill, different purpose than check |
| `integrations/codex/skills/realitycheck/SKILL.md` | Utilities wrapper, different from other skills |

## Phase 10 Files (Created)

| Path | Purpose |
|------|---------|
| `integrations/_templates/analysis/source-analysis-full.md.j2` | Full analysis skeleton |
| `integrations/_templates/analysis/source-analysis-quick.md.j2` | Quick analysis skeleton |
| `scripts/analysis_validator.py` | Output contract checker |
| `scripts/analysis_formatter.py` | Missing element inserter |
| `tests/test_analysis_validator.py` | Validator tests (25 tests) |
| `tests/test_analysis_formatter.py` | Formatter tests (29 tests) |

---

*Last updated: 2026-01-22 (Phase 10 complete)*
