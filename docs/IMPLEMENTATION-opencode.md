# OpenCode Integration - Implementation Tracking

## Overview

This document tracks implementation progress for adding OpenCode as a supported integration.
See `PLAN-opencode.md` for the full design and rationale.

---

## Current Status

**Phase**: Complete
**Started**: 2026-01-27
**Completed**: 2026-01-28

---

## Punchlist

### Phase 1: Template & Config

- [x] Create `integrations/_templates/wrappers/opencode.md.j2`
- [x] Update `integrations/_config/skills.yaml` with opencode defaults
- [x] Update `integrations/assemble.py` to include "opencode" in INTEGRATIONS list

### Phase 2: Generate & Verify

- [x] Run `make assemble-skills` to generate OpenCode skills
- [x] Verify 9 skills generated in `integrations/opencode/skills/`
- [x] Review generated frontmatter for compliance with OpenCode spec

### Phase 3: Install Infrastructure

- [x] Create `integrations/opencode/README.md`
- [x] Create `integrations/opencode/install.sh`
- [x] Create `integrations/opencode/uninstall.sh`
- [x] Add Makefile targets: `install-skills-opencode`, `uninstall-skills-opencode`
- [x] Update `install-skills-all` and `uninstall-skills-all` targets

### Phase 4: Documentation

- [x] Update main `README.md` with OpenCode section
- [x] Create `docs/EXTENDING-SKILLS.md` (guide for adding new integrations)

### Phase 5: Testing & Validation

- [ ] Test `make install-skills-opencode` creates correct symlinks
- [ ] Test `make uninstall-skills-opencode` removes symlinks
- [ ] Manual test: Launch OpenCode and verify skills are discoverable
- [ ] Manual test: Load `realitycheck` skill and run basic workflow

---

## Worklog

### 2026-01-27: Planning

- Created `docs/PLAN-opencode.md` with full design
- Created `docs/IMPLEMENTATION-opencode.md` (this file)
- Analyzed OpenCode skill spec from https://opencode.ai/docs/skills/
- Identified key differences from existing integrations:
  - Stricter frontmatter (only name, description, license, compatibility, metadata)
  - Stricter naming regex: `^[a-z0-9]+(-[a-z0-9]+)*$`
  - Install path: `~/.config/opencode/skills/`
- Decided on `realitycheck-*` prefix for all skills (matches Amp pattern)

### 2026-01-28: Implementation

**Phase 1: Template & Config**
- Created `integrations/_templates/wrappers/opencode.md.j2` with OpenCode-compliant frontmatter
- Updated `integrations/_config/skills.yaml`:
  - Added `opencode` defaults (name_prefix: "realitycheck-", skill_dir: "opencode/skills")
  - Added `opencode.argument_hint` for each skill
- Updated `integrations/assemble.py` INTEGRATIONS list to include "opencode"

**Phase 2: Generate & Verify**
- Ran `python3 integrations/assemble.py --docs`
- Generated 8 skills via template system:
  - realitycheck-check, realitycheck-synthesize, realitycheck-analyze, realitycheck-extract
  - realitycheck-search, realitycheck-validate, realitycheck-export, realitycheck-stats
- Created manual `realitycheck` alias skill (main entry point)
- Verified frontmatter compliance:
  - Only `name`, `description`, `license`, `compatibility`, `metadata` fields
  - Names match directory names
  - Names follow lowercase alphanumeric + hyphen pattern

**Phase 3: Install Infrastructure**
- Created `integrations/opencode/README.md` with full documentation
- Created `integrations/opencode/install.sh` (symlink-based, chmod +x)
- Created `integrations/opencode/uninstall.sh` (symlink removal, chmod +x)
- Updated `Makefile`:
  - Added OPENCODE_SKILLS_SRC, OPENCODE_SKILLS_DST, OPENCODE_SKILLS variables
  - Added `install-skills-opencode` target
  - Added `uninstall-skills-opencode` target
  - Updated `install-skills-all` and `uninstall-skills-all` to include opencode
  - Updated help text

**Phase 4: Documentation**
- Updated main `README.md`:
  - Added OpenCode to Prerequisites list
  - Added "OpenCode Skills" section with install instructions and skill table
- Created `docs/EXTENDING-SKILLS.md`:
  - 9-step guide for adding new integrations
  - Template variable reference
  - Platform-specific considerations (frontmatter, naming, invocation)
  - Complete checklist

---

## Files Created/Updated

### New Files

| File | Purpose |
|------|---------|
| `integrations/_templates/wrappers/opencode.md.j2` | OpenCode wrapper template |
| `integrations/opencode/README.md` | OpenCode integration guide |
| `integrations/opencode/install.sh` | Install script |
| `integrations/opencode/uninstall.sh` | Uninstall script |
| `integrations/opencode/skills/realitycheck/SKILL.md` | Main entry point (manual) |
| `integrations/opencode/skills/realitycheck-check/SKILL.md` | Full analysis (generated) |
| `integrations/opencode/skills/realitycheck-analyze/SKILL.md` | Manual analysis (generated) |
| `integrations/opencode/skills/realitycheck-extract/SKILL.md` | Claim extraction (generated) |
| `integrations/opencode/skills/realitycheck-search/SKILL.md` | Semantic search (generated) |
| `integrations/opencode/skills/realitycheck-validate/SKILL.md` | Validation (generated) |
| `integrations/opencode/skills/realitycheck-export/SKILL.md` | Export (generated) |
| `integrations/opencode/skills/realitycheck-stats/SKILL.md` | Statistics (generated) |
| `integrations/opencode/skills/realitycheck-synthesize/SKILL.md` | Synthesis (generated) |
| `docs/PLAN-opencode.md` | Design document |
| `docs/IMPLEMENTATION-opencode.md` | This file |
| `docs/EXTENDING-SKILLS.md` | Guide for adding new integrations |

### Updated Files

| File | Changes |
|------|---------|
| `integrations/_config/skills.yaml` | Added opencode defaults + per-skill argument_hint |
| `integrations/assemble.py` | Added "opencode" to INTEGRATIONS list |
| `Makefile` | Added install/uninstall targets for opencode |
| `README.md` | Added OpenCode to Prerequisites and new OpenCode Skills section |

---

## Generated Skills

| Skill Name | Description |
|------------|-------------|
| `realitycheck` | Main entry point (alias for check) |
| `realitycheck-check` | Full analysis workflow |
| `realitycheck-analyze` | Manual 3-stage analysis |
| `realitycheck-extract` | Quick claim extraction |
| `realitycheck-search` | Semantic search |
| `realitycheck-validate` | Data validation |
| `realitycheck-export` | Data export |
| `realitycheck-stats` | Database statistics |
| `realitycheck-synthesize` | Cross-source synthesis |

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-27 | Use `realitycheck-*` prefix | Avoid collisions, match Amp pattern, clear provenance |
| 2026-01-27 | Install to `~/.config/opencode/skills/` | OpenCode standard global location |
| 2026-01-27 | Omit `allowed-tools` from frontmatter | OpenCode ignores unrecognized fields; cleaner output |
| 2026-01-27 | Move `argument-hint` to body | Keep frontmatter OpenCode-compliant |
| 2026-01-28 | Create manual `realitycheck` alias skill | Not in template system; simpler entry point |

---

*Last updated: 2026-01-28*
