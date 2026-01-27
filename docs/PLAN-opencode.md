# Plan: OpenCode Integration

**Status**: Planning
**Created**: 2026-01-27

## Motivation

[OpenCode](https://opencode.ai) is an open-source AI coding agent with 80K+ GitHub stars and 1.5M+ monthly users. It supports a skill system similar to Claude Code's, making it a natural target for Reality Check integration.

OpenCode skills allow agents to discover and load reusable instructions on-demand via a native `skill` tool. This aligns well with Reality Check's existing skill-based architecture.

## Goals

- **Add OpenCode as a supported integration** alongside Claude, Codex, and Amp
- **Leverage existing template infrastructure** (no duplication of methodology content)
- **Document the process** for adding future integrations
- **Maintain consistency** across all skill outputs

## Non-goals

- Changing OpenCode's skill format (we adapt to their spec)
- Custom OpenCode-only features (same methodology, different packaging)
- GUI or desktop app integration (CLI/TUI only)

## OpenCode Skill Specification

Based on [OpenCode docs](https://opencode.ai/docs/skills/):

### File Location & Discovery

OpenCode searches these locations for skills:

| Location | Scope |
|----------|-------|
| `.opencode/skills/<name>/SKILL.md` | Project-local |
| `~/.config/opencode/skills/<name>/SKILL.md` | Global (user) |
| `.claude/skills/<name>/SKILL.md` | Project-local (Claude-compatible) |
| `~/.claude/skills/<name>/SKILL.md` | Global (Claude-compatible) |

For project-local paths, OpenCode walks up from CWD to git worktree root.

### Frontmatter Schema

OpenCode SKILL.md files use YAML frontmatter with **only these recognized fields**:

```yaml
---
name: skill-name          # Required, 1-64 chars, lowercase alphanumeric + hyphens
description: Short desc   # Required, 1-1024 chars
license: MIT              # Optional
compatibility: opencode   # Optional
metadata:                 # Optional, string-to-string map
  key: value
---
```

**Important restrictions:**
- `name` must match regex: `^[a-z0-9]+(-[a-z0-9]+)*$`
- `name` must match the containing directory name
- Unknown frontmatter fields are **ignored** (not errors, just stripped)

### Loading Mechanism

Skills are loaded on-demand via the `skill` tool:

```javascript
skill({ name: "skill-name" })
```

Agents see available skills in the tool description:

```xml
<available_skills>
  <skill>
    <name>realitycheck</name>
    <description>Full Reality Check analysis workflow</description>
  </skill>
</available_skills>
```

### Permissions

Configured in `opencode.json`:

```json
{
  "permission": {
    "skill": {
      "*": "allow",
      "internal-*": "deny"
    }
  }
}
```

## Comparison: OpenCode vs Current Integrations

| Aspect | Claude Code | Codex | Amp | OpenCode |
|--------|-------------|-------|-----|----------|
| **Name format** | `check` | `check` | `realitycheck-check` | `realitycheck-check` |
| **Frontmatter** | `argument-hint`, `allowed-tools` | Simple | `triggers` | Only `name`, `description`, `license`, `compatibility`, `metadata` |
| **Invocation** | `/check` | `$check` | Natural language | Via `skill()` tool |
| **Install path** | `~/.claude/skills/` | Custom | `~/.config/agents/skills/` | `~/.config/opencode/skills/` |

### Key Differences for OpenCode

1. **Stricter frontmatter** - Claude's `argument-hint` and `allowed-tools` are not recognized
2. **Stricter naming** - Must use hyphens, lowercase only, no special chars
3. **Different install path** - `~/.config/opencode/skills/` (global)
4. **Directory name must match `name`** - Enforced at load time

## Design Decisions

### Skill Naming Convention

**Decision**: Use `realitycheck-*` prefix (like Amp)

**Rationale**:
- Avoids collision with other skills (generic names like `check`, `validate`)
- Consistent with Amp naming which also uses global install
- Clear provenance for users browsing their skills directory
- Matches OpenCode's naming regex requirements

**Skill names**:
- `realitycheck` - Main entry point (alias for check workflow)
- `realitycheck-check` - Full analysis workflow
- `realitycheck-analyze` - Manual 3-stage analysis
- `realitycheck-extract` - Quick claim extraction
- `realitycheck-search` - Semantic search
- `realitycheck-validate` - Data validation
- `realitycheck-export` - Data export
- `realitycheck-stats` - Database statistics
- `realitycheck-synthesize` - Cross-source synthesis

### Frontmatter Mapping

OpenCode ignores unsupported frontmatter fields, but we should emit clean files:

| Claude Field | OpenCode Mapping |
|--------------|------------------|
| `name` | `name` (with prefix) |
| `description` | `description` |
| `argument-hint` | Move to body (Usage section) |
| `allowed-tools` | Omit (OpenCode doesn't restrict tools this way) |

### Template Wrapper Structure

Create `integrations/_templates/wrappers/opencode.md.j2`:

```jinja2
---
name: {{ name }}
description: {{ description }}
license: Apache-2.0
compatibility: opencode
metadata:
  project: realitycheck
  version: "0.1"
---

# {{ title }}

{{ description }}

{% if argument_hint %}
## Usage

```
{{ invocation_prefix }}{{ name | replace('realitycheck-', '') }} {{ argument_hint }}
```
{% endif %}

{% include "partials/prerequisites.md.j2" %}

{% include "skills/" ~ template %}

{% if related %}
## Related Skills

{% for r in related %}
- `realitycheck-{{ r }}`
{% endfor %}
{% endif %}
```

### Configuration Updates

Add to `integrations/_config/skills.yaml`:

```yaml
defaults:
  opencode:
    name_prefix: "realitycheck-"
    skill_dir: "opencode/skills"

skills:
  check:
    # ... existing config ...
    opencode:
      # No special config needed - uses defaults
      # argument_hint moved to body, allowed_tools omitted
```

## Implementation Plan

### Files to Create

```
integrations/
├── _templates/
│   └── wrappers/
│       └── NEW opencode.md.j2
├── NEW opencode/
│   ├── README.md
│   ├── install.sh
│   ├── uninstall.sh
│   └── skills/
│       └── (generated by assemble.py)
```

### Files to Update

```
integrations/
├── _config/
│   └── UPDATE skills.yaml          # Add opencode defaults
├── UPDATE assemble.py              # Add "opencode" to INTEGRATIONS

UPDATE Makefile                     # Add install/uninstall targets
UPDATE README.md                    # Add OpenCode section
```

### New Documentation

```
docs/
├── NEW EXTENDING-SKILLS.md         # Guide for adding new integrations
```

## Affected Files Tree

```
integrations/
├── _templates/
│   └── wrappers/
│       └── NEW opencode.md.j2
├── _config/
│   └── UPDATE skills.yaml
├── UPDATE assemble.py
├── NEW opencode/
│   ├── README.md
│   ├── install.sh
│   ├── uninstall.sh
│   └── skills/
│       ├── realitycheck/SKILL.md           (generated)
│       ├── realitycheck-check/SKILL.md     (generated)
│       ├── realitycheck-analyze/SKILL.md   (generated)
│       ├── realitycheck-extract/SKILL.md   (generated)
│       ├── realitycheck-search/SKILL.md    (generated)
│       ├── realitycheck-validate/SKILL.md  (generated)
│       ├── realitycheck-export/SKILL.md    (generated)
│       ├── realitycheck-stats/SKILL.md     (generated)
│       └── realitycheck-synthesize/SKILL.md (generated)

docs/
├── NEW PLAN-opencode.md            (this file)
├── NEW IMPLEMENTATION-opencode.md
├── NEW EXTENDING-SKILLS.md

UPDATE Makefile
UPDATE README.md
```

## Testing Strategy

### Manual Testing

1. Run `make assemble-skills` and verify OpenCode skills are generated
2. Run `make check-skills` to verify no drift
3. Install skills: `make install-skills-opencode`
4. Launch OpenCode in a test project
5. Verify skills appear in `/skills` or skill tool description
6. Test loading a skill: "Load the realitycheck skill"
7. Run a basic workflow: "Run a reality check on <url>"

### Automated Testing

- `make check-skills` in CI ensures generated files stay in sync
- Frontmatter validation in `assemble.py` catches schema violations

## Rollout Plan

1. Create PLAN and IMPLEMENTATION docs (this work)
2. Implement wrapper template and config updates
3. Update assemble.py and Makefile
4. Generate skills and verify
5. Create install/uninstall scripts
6. Update README with OpenCode section
7. Create EXTENDING-SKILLS.md for future integrations
8. Test manually with OpenCode
9. Commit and tag

## Success Criteria

- [ ] `make assemble-skills` generates 9 OpenCode skills
- [ ] `make check-skills` passes (no drift)
- [ ] `make install-skills-opencode` symlinks to `~/.config/opencode/skills/`
- [ ] Skills load successfully in OpenCode TUI
- [ ] `/check` equivalent workflow works end-to-end
- [ ] EXTENDING-SKILLS.md documents the process for future integrations

## Estimated Effort

| Task | Effort |
|------|--------|
| Create opencode.md.j2 wrapper | 15 min |
| Update skills.yaml | 10 min |
| Update assemble.py | 5 min |
| Create install/uninstall scripts | 15 min |
| Create opencode/README.md | 10 min |
| Update Makefile | 10 min |
| Update main README.md | 10 min |
| Create EXTENDING-SKILLS.md | 30 min |
| Manual testing | 20 min |
| **Total** | ~2 hours |

## Related Documents

- [PLAN-skill-template-refactor.md](PLAN-skill-template-refactor.md) - Template architecture
- [IMPLEMENTATION-skill-template-refactor.md](IMPLEMENTATION-skill-template-refactor.md) - Template implementation status
- [OpenCode Skills Docs](https://opencode.ai/docs/skills/) - Official specification

---

*Created: 2026-01-27*
