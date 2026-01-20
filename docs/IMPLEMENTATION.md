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
- [ ] Update requirements.txt
- [ ] Create .gitignore
- [ ] Verify tests pass
- [ ] Tag as v0.1.0-alpha

### Worklog

#### 2026-01-20: Initial Setup

- Created realitycheck repo at /home/lhl/github/lhl/realitycheck
- Created AGENTS.md with development-focused workflow
- Created CLAUDE.md -> AGENTS.md symlink
- Created README.md with project overview
- Copied PLAN-separation.md from analysis-framework
- Created this IMPLEMENTATION.md

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

## Phase 4: Clean Up

### Punchlist

- [ ] Remove analysis data from framework repo
- [ ] Update README with installation guide
- [ ] Tag realitycheck as v1.0.0
- [ ] Archive analysis-framework repo

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-20 | Use ANALYSIS_DB_PATH env var | Matches existing db.py, simpler than --db-path flag |
| 2026-01-20 | Bundle Python scripts in plugin/lib/ | Plugin-only mode needs to be self-contained |
| 2026-01-20 | Single unified KB default | Epistemological advantage: cross-domain synthesis |

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

*Last updated: 2026-01-20*
