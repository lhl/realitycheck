# RealityCheck Implementation Tracking

## Overview

This document tracks implementation progress for the RealityCheck framework.
See `PLAN-separation.md` for the full architecture and implementation plan.

---

## Current Status

**Phase**: 1 - Restructure Framework Repo
**Started**: 2026-01-20

---

## Phase 1: Restructure Framework Repo

### Punchlist

- [x] Create new `realitycheck` repo
- [x] Create AGENTS.md (development-focused)
- [x] Create CLAUDE.md symlink
- [x] Create README.md
- [x] Copy PLAN-separation.md
- [x] Copy scripts/ from analysis-framework
  - [x] db.py, validate.py, export.py, migrate.py, embed.py
  - [x] __init__.py (for package structure)
- [x] Copy tests/ from analysis-framework
  - [x] conftest.py, test_*.py files
  - [x] __init__.py
- [x] Create plugin/ directory structure
  - [x] .claude-plugin/plugin.json
  - [x] commands/*.md (analyze, extract, validate, search, export)
  - [ ] scripts/*.sh (wrappers) - deferred to Phase 2
  - [ ] lib/ (for bundled scripts) - deferred to Phase 2
- [x] Create methodology/ directory
  - [x] evidence-hierarchy.md
  - [x] claim-taxonomy.md
  - [x] templates/ (source-analysis.md, claim-extraction.md, synthesis.md)
- [x] Create pyproject.toml (uv-managed)
- [x] Create pytest.ini
- [x] Create .gitignore
- [x] Create .gitattributes
- [x] Create .claude/settings.json
- [x] Add LICENSE (MIT)
- [x] Add framework docs (SCHEMA.md, WORKFLOWS.md, PLUGIN.md, CONTRIBUTING.md)
- [ ] Decide CLAUDE.md vs AGENTS.md roles (remove symlink if needed)
- [x] Update README to reflect scaffold status
- [x] Verify tests pass (`uv run pytest`) - 91 passed, 17 skipped (embedding tests)
- [x] Tag as v0.1.0-alpha (`48b537f`)

### Worklog

#### 2026-01-20: Initial Setup

- Created realitycheck repo at /home/lhl/github/lhl/realitycheck
- Created AGENTS.md with development-focused workflow
- Created CLAUDE.md -> AGENTS.md symlink
- Created README.md with project overview
- Copied PLAN-separation.md from analysis-framework
- Created this IMPLEMENTATION.md

#### 2026-01-20: PLAN Consistency Fixes

Fixed 6 inconsistencies in PLAN-separation.md based on review feedback:

1. **DB path**: Standardized to `data/realitycheck.lance` (was mixed with `analysis.lance`)
2. **skill/ vs plugin/**: Changed Options A+D to use `plugin/` consistently
3. **pip import**: `from analysis_framework` → `from realitycheck`
4. **resolve-script**: `resolve-framework.sh` → `resolve-project.sh`
5. **Script paths**: Updated wrapper example to use `lib/` fallback consistently
6. **Plugin install**: Standardized syntax with TBD notes

#### 2026-01-20: Pre-Implementation Review

Reviewed ../analysis-framework/ and ../postsingularity-economic-theories/ for completeness.

**analysis-framework contains:**
- `scripts/`: db.py (726 lines), validate.py (464 lines), export.py (523 lines), migrate.py (487 lines), embed.py, __init__.py
- `tests/`: conftest.py (288 lines), test_db.py, test_e2e.py, test_export.py, test_migrate.py, test_validate.py, __init__.py
- `skills/analysis-framework/`: skill.md, templates/ (source-analysis.md, claim-extraction.md, synthesis.md)
- CLAUDE.md with full methodology (328 lines)
- pytest.ini, requirements.txt, .gitignore, .gitattributes

**postsingularity-economic-theories contains (real data example):**
- `claims/registry.yaml` - 85+ claims with relationships
- `reference/sources.yaml` - 30+ sources
- `analysis/sources/`, `analysis/syntheses/` - completed analyses
- `tracking/predictions.md`, `tracking/dashboards/` - prediction tracking
- `scenarios/` - scenario matrices
- `inbox/` (workflow staging: to-catalog, to-analyze, in-progress, needs-update)
- `.claude/settings.json` with comprehensive permissions

**Gaps identified (updated punchlist):**
- embed.py functions already in db.py - embed.py may be deprecated
- skills/templates/ maps to methodology/templates/ (confirmed in PLAN)
- __init__.py files needed for Python package structure
- inbox/ workflow directory not in planned realitycheck-data structure (optional enhancement)

**Created**: `.claude/settings.json` with permissions for uninterrupted work

**Next**: Copy scripts/ and tests/ from analysis-framework

#### 2026-01-20: Scripts, Tests, and Config

Ported complete Python implementation from analysis-framework:

**Scripts copied** (scripts/):
- db.py - LanceDB wrapper, CRUD operations, semantic search (updated DB_PATH default)
- validate.py - Data integrity validation for DB and legacy YAML
- export.py - YAML and Markdown export utilities
- migrate.py - YAML → LanceDB migration with domain mapping
- embed.py - Embedding generation utilities
- __init__.py - Package initialization

**Tests copied** (tests/):
- conftest.py - Pytest fixtures (sample_claim, sample_source, etc.)
- test_db.py - 31 tests for database operations
- test_validate.py - 20 tests for validation
- test_migrate.py - 25 tests for migration
- test_export.py - 20 tests for export
- test_e2e.py - 12 tests for end-to-end workflows
- __init__.py - Package initialization

**Config files created**:
- pyproject.toml - uv-managed dependencies, entry points, pytest config
- pytest.ini - Test configuration
- .gitattributes - LFS tracking for .lance and .parquet files
- LICENSE - MIT license

**Test results**: `SKIP_EMBEDDING_TESTS=1 uv run pytest -v`
- 91 passed, 17 skipped (embedding tests)
- All non-embedding tests pass

**Next**: Create plugin/ and methodology/ directories

#### 2026-01-20: Plugin and Methodology

Created plugin/ directory structure:
- plugin/.claude-plugin/plugin.json - Plugin manifest
- plugin/commands/analyze.md - 3-stage source analysis
- plugin/commands/extract.md - Quick claim extraction
- plugin/commands/validate.md - Data integrity check
- plugin/commands/search.md - Semantic search
- plugin/commands/export.md - Data export

Created methodology/ directory with extracted content from analysis-framework CLAUDE.md:
- methodology/evidence-hierarchy.md - E1-E6 rating scale with calibration guidance
- methodology/claim-taxonomy.md - Claim types, domains, prediction tracking
- methodology/templates/source-analysis.md - Full 3-stage analysis template
- methodology/templates/claim-extraction.md - Quick extraction template
- methodology/templates/synthesis.md - Cross-source synthesis template

Created framework documentation:
- docs/SCHEMA.md - Database schema reference
- docs/WORKFLOWS.md - Common workflow documentation
- docs/PLUGIN.md - Claude Code plugin installation and usage
- CONTRIBUTING.md - Contribution guidelines

**Deferred to Phase 2**: Plugin shell wrappers (scripts/*.sh) and bundled scripts (lib/)

**Next**: Tag as v0.1.0-alpha

---

## Phase 2: Create Plugin Commands

### Punchlist

**Flagship commands:**
- [ ] `/check <url>` - Full analysis workflow (fetch → extract → analyze → register → report)
- [ ] `/realitycheck <url>` - Alias for `/check`

**CRUD commands (extend rc-db CLI):**
- [ ] `rc-db add claim|source|chain|prediction` - Add records via CLI
- [ ] `rc-db get <id>` - Retrieve single record
- [ ] `rc-db list claims|sources|chains` - List records with filters
- [ ] `rc-db update <id>` - Update existing record
- [ ] `rc-db related <claim-id>` - Find related claims
- [ ] `rc-db import <file>` - Bulk import from YAML

**Plugin wiring:**
- [ ] Shell wrapper scripts in `plugin/scripts/`
- [ ] Update `/analyze`, `/extract`, `/validate`, `/export`, `/search` to invoke CLI
- [ ] Lifecycle hooks (`plugin/hooks/hooks.json`)
- [ ] Test each command end-to-end

**Release:**
- [ ] Tag as v0.1.0-beta

---

## Phase 3: Separate Analysis Data

### Punchlist

- [ ] Create `realitycheck-data` repo
- [ ] Move data from postsingularity-economic-theories
- [ ] Create .realitycheck.yaml config
- [ ] Create/retain project workflow structure (inbox/, analysis/meta/, tracking/updates/)
- [ ] Add optional pre-commit hook to run validation
- [ ] Decide git-lfs policy for `data/realitycheck.lance/` and document it
- [ ] Verify validation passes
- [ ] Tag realitycheck-data as v0.1.0

---

## Phase 4: Clean Up & Publish

### Punchlist

- [ ] Remove analysis data from framework repo
- [ ] Update README with installation guide
- [ ] Finalize pyproject.toml for PyPI
  - [ ] Package metadata (name, version, description, author, license, URLs)
  - [ ] Entry points for CLI (`realitycheck` command)
  - [ ] Classifiers and keywords
- [ ] Test with TestPyPI
  - [ ] `uv publish --publish-url https://test.pypi.org/legacy/`
  - [ ] Verify: `pip install -i https://test.pypi.org/simple/ realitycheck`
- [ ] Publish to PyPI: `uv publish`
- [ ] Verify: `pip install realitycheck` works
- [ ] Tag realitycheck as v1.0.0
- [ ] Archive analysis-framework repo

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-20 | Use ANALYSIS_DB_PATH env var | Matches existing db.py, simpler than --db-path flag |
| 2026-01-20 | Bundle Python scripts in plugin/lib/ | Plugin-only mode needs to be self-contained |
| 2026-01-20 | Code schemas are canonical for v0.1.x | Ported schemas from analysis-framework are complete and tested; docs updated to match |
| 2026-01-20 | No co-author footers in commits | Project rule (AGENTS.md) wins over external tooling defaults; use worklog for provenance |
| 2026-01-20 | Git tag is pre-release marker only | Package version stays `0.1.0` (PEP 440); `alpha` is git tag only, not in version string |
| 2026-01-20 | Single unified KB default | Epistemological advantage: cross-domain synthesis |
| 2026-01-20 | Use `uv` for package management | Fast, modern, handles both deps and Python version; future-proof replacement for pip/venv/pyenv |
| 2026-01-20 | Publish to PyPI as `realitycheck` | Name available; enables `pip install realitycheck` for easy adoption |

---

## Files Created

| File | Purpose |
|------|---------|
| AGENTS.md | Development workflow and conventions |
| CLAUDE.md | Symlink to AGENTS.md |
| README.md | Project overview and quick start |
| docs/PLAN-separation.md | Architecture and implementation plan |
| docs/IMPLEMENTATION.md | This file - progress tracking |
| scripts/db.py | LanceDB wrapper, CRUD, semantic search |
| scripts/validate.py | Data integrity validation |
| scripts/export.py | YAML and Markdown export |
| scripts/migrate.py | YAML → LanceDB migration |
| scripts/embed.py | Embedding generation utilities |
| scripts/__init__.py | Package initialization |
| tests/conftest.py | Pytest fixtures |
| tests/test_db.py | Database operation tests |
| tests/test_validate.py | Validation tests |
| tests/test_migrate.py | Migration tests |
| tests/test_export.py | Export tests |
| tests/test_e2e.py | End-to-end tests |
| tests/__init__.py | Package initialization |
| pyproject.toml | uv package configuration |
| pytest.ini | Pytest configuration |
| .gitattributes | Git LFS configuration |
| LICENSE | MIT license |
| plugin/.claude-plugin/plugin.json | Plugin manifest |
| plugin/commands/analyze.md | Source analysis command |
| plugin/commands/extract.md | Claim extraction command |
| plugin/commands/validate.md | Validation command |
| plugin/commands/search.md | Semantic search command |
| plugin/commands/export.md | Export command |
| methodology/evidence-hierarchy.md | E1-E6 rating scale |
| methodology/claim-taxonomy.md | Claim types and domains |
| methodology/templates/source-analysis.md | 3-stage analysis template |
| methodology/templates/claim-extraction.md | Quick extraction template |
| methodology/templates/synthesis.md | Cross-source synthesis template |
| docs/SCHEMA.md | Database schema reference |
| docs/WORKFLOWS.md | Workflow documentation |
| docs/PLUGIN.md | Plugin installation/usage |
| CONTRIBUTING.md | Contribution guidelines |

---

*Last updated: 2026-01-20 (Phase 1 near-complete, ready for v0.1.0-alpha tag)*
