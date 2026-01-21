# Implementation: Skill Template Refactor

**Status**: In Progress
**Plan**: [PLAN-skill-template-refactor.md](PLAN-skill-template-refactor.md)
**Related**: [PLAN-quality-regression-fix.md](PLAN-quality-regression-fix.md)
**Started**: 2026-01-22

## Summary

Refactor skill generation to use Jinja2 templates with DRY partials. This consolidates 15 manually-maintained SKILL.md files into a template system that generates 24 skills (8 per integration) from ~30 template files.

**Key goals:**
1. Single source of truth for methodology content
2. Restore quality lost during over-trimming (see quality regression fix)
3. Generate all skills for all integrations (Amp, Claude, Codex)
4. Add validator/formatter for machine-checkable output contract

---

## Punchlist

### Phase 1: Template Structure + Partials (from POC)
- [ ] Create `integrations/_templates/` directory structure
- [ ] `partials/legends.md.j2` - Claim types + evidence quick reference
- [ ] `partials/evidence-hierarchy.md.j2` - Full table with weights
- [ ] `partials/claim-types.md.j2` - With definitions
- [ ] `partials/domain-codes.md.j2`
- [ ] `partials/claim-relationships.md.j2` - →+, →✗, →?, etc.
- [ ] `partials/confidence-calibration.md.j2`
- [ ] `partials/db-commands.md.j2`
- [ ] `partials/prerequisites.md.j2`

### Phase 2: Table Templates (Quality Restoration)
- [ ] `tables/key-claims.md.j2` - Full table with Verified?/Falsifiable By
- [ ] `tables/claim-summary.md.j2`
- [ ] `tables/factual-claims-verified.md.j2` - With Crux? column
- [ ] `tables/disconfirming-evidence.md.j2`
- [ ] `tables/internal-tensions.md.j2`
- [ ] `tables/persuasion-techniques.md.j2`
- [ ] `tables/unstated-assumptions.md.j2`
- [ ] `tables/supporting-contradicting.md.j2`

### Phase 3: Section Templates
- [ ] `sections/argument-structure.md.j2`
- [ ] `sections/theoretical-lineage.md.j2`
- [ ] `sections/confidence-assessment.md.j2`

### Phase 4: Skill Templates
- [ ] `skills/check.md.j2` - Full workflow with all tables/sections
- [ ] `skills/analyze.md.j2` - Manual 3-stage
- [ ] `skills/extract.md.j2` - Quick extraction
- [ ] `skills/search.md.j2`
- [ ] `skills/validate.md.j2`
- [ ] `skills/export.md.j2`
- [ ] `skills/stats.md.j2`

### Phase 5: Integration Wrappers
- [ ] `wrappers/amp.md.j2`
- [ ] `wrappers/claude.md.j2`
- [ ] `wrappers/codex.md.j2`

### Phase 6: Configuration
- [ ] `_config/skills.yaml` - All skill definitions + per-integration metadata

### Phase 7: Build Script
- [ ] `integrations/assemble.py`
- [ ] `--integration` filter (amp/claude/codex/all)
- [ ] `--skill` filter
- [ ] `--dry-run` mode
- [ ] `--diff` mode
- [ ] `--check` mode
- [ ] Frontmatter validation

### Phase 8: Makefile & CI
- [ ] `make assemble-skills` target
- [ ] `make check-skills` target
- [ ] Update install scripts
- [ ] Generated file header markers

### Phase 9: Cleanup & Documentation
- [ ] Remove old manual skill files
- [ ] Update `integrations/README.md`
- [ ] Update `CONTRIBUTING.md`
- [ ] Remove `methodology/workflows/check-core.md`

### Phase 10: Validator & Formatter
- [ ] `scripts/analysis_validator.py`
- [ ] `scripts/analysis_formatter.py`
- [ ] Tests for validator/formatter
- [ ] Claude plugin hook integration
- [ ] Document manual invocation

---

## Worklog

### 2026-01-22: Planning

- Created PLAN-skill-template-refactor.md
- Integrated quality regression fix requirements
- Identified ~30 template files needed
- Estimated 15-20 hours total effort
- Created this implementation tracking doc

---

## Files to Create

| Path | Purpose |
|------|---------|
| `integrations/_templates/partials/*.md.j2` | 8 shared partials |
| `integrations/_templates/tables/*.md.j2` | 8 table templates |
| `integrations/_templates/sections/*.md.j2` | 3 section templates |
| `integrations/_templates/skills/*.md.j2` | 7 skill templates |
| `integrations/_templates/wrappers/*.md.j2` | 3 integration wrappers |
| `integrations/_config/skills.yaml` | Skill definitions |
| `integrations/assemble.py` | Build script |
| `scripts/analysis_validator.py` | Output contract checker |
| `scripts/analysis_formatter.py` | Missing element inserter |

## Files to Remove (after migration)

| Path | Reason |
|------|--------|
| `integrations/amp/skills/*/SKILL.md` | Replaced by generated |
| `integrations/claude/skills/*/SKILL.md` | Replaced by generated |
| `integrations/codex/skills/*/SKILL.md` | Replaced by generated |
| `methodology/workflows/check-core.md` | Content moved to templates |

---

*Last updated: 2026-01-22*
