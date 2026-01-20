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

**Tagged**: v0.1.0-alpha (`68bacb6`)

---

## Phase 2: Create Plugin Commands

### Punchlist

**Flagship commands:**
- [x] `/check <url>` - Full analysis workflow (fetch → extract → analyze → register → report)
- [x] `/realitycheck <url>` - Alias for `/check`

**CRUD commands (extend rc-db CLI):**
- [x] `rc-db claim add/get/list/update` - Claim operations via CLI
- [x] `rc-db source add/get/list` - Source operations via CLI
- [x] `rc-db chain add/get/list` - Chain operations via CLI
- [x] `rc-db prediction add/list` - Prediction operations via CLI
- [x] `rc-db related <claim-id>` - Find related claims
- [x] `rc-db import <file>` - Bulk import from YAML

**Plugin wiring:**
- [x] Shell wrapper scripts in `plugin/scripts/`
  - resolve-project.sh - Find project root, set env vars
  - run-db.sh - Wrapper for db.py
  - run-validate.sh - Wrapper for validate.py
  - run-export.sh - Wrapper for export.py
- [x] Update `/analyze`, `/extract`, `/validate`, `/export`, `/search` to invoke CLI
- [x] Lifecycle hooks (`plugin/hooks/hooks.json`)
  - on-stop.sh - Auto-validate on session end
  - post-db-modify.sh - Post-database-operation hook (silent by default)
- [x] CLI tests (20 new tests) - all passing

**Release:**
- [ ] Tag as v0.1.0-beta

### Worklog

#### 2026-01-21: Phase 2 Implementation

**CLI Extension (db.py)**

Extended db.py with comprehensive nested subparsers:

```
rc-db init                              # Initialize database
rc-db stats                             # Show statistics
rc-db reset                             # Reset database

rc-db claim add --text "..." --type "[F]" --domain "TECH" --evidence-level "E3"
rc-db claim get <id>                    # JSON output
rc-db claim list [--domain D] [--type T] [--format json|text]
rc-db claim update <id> --credence 0.9

rc-db source add --id "..." --title "..." --type "PAPER" --author "..." --year 2026
rc-db source get <id>
rc-db source list [--type T] [--status S]

rc-db chain add --id "..." --name "..." --thesis "..." --claims "ID1,ID2"
rc-db chain get <id>
rc-db chain list

rc-db prediction add --claim-id "..." --source-id "..." --status "[P→]"
rc-db prediction list [--status S]

rc-db related <claim-id>                # Show relationships

rc-db import <file.yaml> --type claims  # Bulk import
rc-db search "query" --limit 10         # Semantic search
```

Key features:
- Auto-ID generation for claims (DOMAIN-YYYY-NNN format)
- JSON output by default, `--format text` for human-readable
- Embedded CLI helper functions for output formatting

**Tests Added (tests/test_db.py)**

18 new CLI tests covering:
- TestClaimCLI: add, get, list, update, filters
- TestSourceCLI: add, get, list with type filters
- TestChainCLI: add, get, list
- TestPredictionCLI: add, list with status filters
- TestRelatedCLI: relationship traversal
- TestImportCLI: YAML import, error handling
- TestTextFormatOutput: human-readable format

All tests pass: `SKIP_EMBEDDING_TESTS=1 uv run pytest -v` (110 passed, 17 skipped)

**Shell Wrapper Scripts (plugin/scripts/)**

Created shell wrappers for plugin integration:
- `resolve-project.sh` - Find project root via .realitycheck.yaml or data/*.lance
- `run-db.sh` - Wrapper for db.py with project context
- `run-validate.sh` - Wrapper for validate.py
- `run-export.sh` - Wrapper for export.py

Scripts support:
- Framework repo (development mode) - uses uv run
- Bundled scripts in plugin/lib/ - for distribution
- Installed package - uses rc-db/rc-validate/rc-export commands

**Flagship Commands (plugin/commands/)**

Created flagship `/check` command (`check.md`):
- Full 7-step analysis workflow
- Fetch → Metadata → 3-Stage Analysis → Extract → Register → Validate → Report
- Includes evidence hierarchy reference, claim types
- CLI invocation examples for registration

Created `/realitycheck` alias (`realitycheck.md`):
- Quick reference for /check workflow
- Links to full documentation

**Updated Existing Commands**

Updated to include CLI integration:
- `validate.md` - Added allowed-tools and CLI invocation
- `search.md` - Added allowed-tools and CLI invocation
- `export.md` - Added allowed-tools and CLI invocation
- `analyze.md` - Added database registration examples
- `extract.md` - Added claim registration examples

**Files Created/Modified**

| File | Status | Description |
|------|--------|-------------|
| scripts/db.py | UPDATE | Extended CLI with nested subparsers |
| tests/test_db.py | UPDATE | Added 18 CLI tests |
| plugin/scripts/resolve-project.sh | NEW | Project context detection |
| plugin/scripts/run-db.sh | NEW | db.py wrapper |
| plugin/scripts/run-validate.sh | NEW | validate.py wrapper |
| plugin/scripts/run-export.sh | NEW | export.py wrapper |
| plugin/commands/check.md | NEW | Flagship analysis command |
| plugin/commands/realitycheck.md | NEW | Alias for /check |
| plugin/commands/validate.md | UPDATE | CLI integration |
| plugin/commands/search.md | UPDATE | CLI integration |
| plugin/commands/export.md | UPDATE | CLI integration |
| plugin/commands/analyze.md | UPDATE | Registration examples |
| plugin/commands/extract.md | UPDATE | Registration examples |

#### 2026-01-21: Phase 2 Review Fixes

Addressed feedback from docs/REVIEW-phase2.md:

**P0 - Fixed:**
- Added `should_generate_embedding()` helper to respect SKIP_EMBEDDING_TESTS env var
- Fixed .realitycheck.yaml schema drift in PLAN-separation.md (database.path → db_path)

**P1 - Fixed:**
- Aligned validate.md docs with actual validate.py flags (--mode, --repo-root)
- Fixed chain credence default to actually compute MIN of claims when not specified
- Updated docs/WORKFLOWS.md with complete Phase 2 CLI documentation

**P2 - Fixed:**
- Removed non-working `python -m realitycheck.*` fallback from shell wrappers
- Added allowed-tools directive to /check command for automation

All tests pass: 112 passed, 17 skipped (embedding tests)

**Ready for v0.1.0-beta tag**

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

*Last updated: 2026-01-21 (Phase 2 review fixes complete, ready for v0.1.0-beta tag)*
