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
- [ ] Copy tests/ from analysis-framework
- [ ] Create plugin/ directory structure
  - [ ] .claude-plugin/plugin.json
  - [ ] commands/*.md
  - [ ] scripts/*.sh (wrappers)
- [ ] Create methodology/ directory
  - [ ] Extract from CLAUDE.md
  - [ ] evidence-hierarchy.md
  - [ ] claim-taxonomy.md
  - [ ] templates/
- [ ] Create pyproject.toml (uv-managed)
- [ ] Create .gitignore
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

*Last updated: 2026-01-20 (PLAN consistency fixes, uv decision, PyPI publishing)*
