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
- [ ] Copy scripts/ from analysis-framework
  - [ ] db.py, validate.py, export.py, migrate.py
  - [ ] __init__.py (for package structure)
- [ ] Copy tests/ from analysis-framework
  - [ ] conftest.py, test_*.py files
  - [ ] __init__.py
- [ ] Create plugin/ directory structure
  - [ ] .claude-plugin/plugin.json
  - [ ] commands/*.md
  - [ ] scripts/*.sh (wrappers)
  - [ ] lib/ (for bundled scripts)
- [ ] Create methodology/ directory
  - [ ] Extract from CLAUDE.md
  - [ ] evidence-hierarchy.md
  - [ ] claim-taxonomy.md
  - [ ] templates/ (source-analysis.md, claim-extraction.md, synthesis.md)
- [ ] Create pyproject.toml (uv-managed)
- [ ] Create pytest.ini
- [ ] Create .gitignore
- [ ] Create .gitattributes
- [x] Create .claude/settings.json
- [ ] Verify tests pass (`uv run pytest`)
- [ ] Tag as v0.1.0-alpha

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

---

## Phase 2: Create Plugin Commands

### Punchlist

- [ ] `/init` command
- [ ] `/analyze` command
- [ ] `/claim` command
- [ ] `/validate` command
- [ ] `/export` command
- [ ] `/search` command
- [ ] `/help` command
- [ ] Shell wrapper scripts
- [ ] Test each command
- [ ] Tag as v0.1.0-beta

---

## Phase 3: Separate Analysis Data

### Punchlist

- [ ] Create `realitycheck-data` repo
- [ ] Move data from postsingularity-economic-theories
- [ ] Create .realitycheck.yaml config
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

---

*Last updated: 2026-01-20 (pre-implementation review, .claude/settings.json)*
