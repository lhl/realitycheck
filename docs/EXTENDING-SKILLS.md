# Extending Skills to New Platforms

This guide documents how to add Reality Check skill support to a new AI coding agent or platform.

## Overview

Reality Check uses a template-based system to generate platform-specific skill files from shared methodology content. Adding a new integration requires:

1. A wrapper template (`wrappers/<platform>.md.j2`)
2. Configuration in `skills.yaml`
3. Install/uninstall scripts
4. Makefile targets

The core methodology is shared across all platforms via Jinja2 template includes.

## Architecture

```
integrations/
├── _templates/
│   ├── partials/           # Shared content snippets
│   ├── tables/             # Analysis table templates
│   ├── sections/           # Analysis section templates
│   ├── skills/             # Skill-specific content (check.md.j2, etc.)
│   └── wrappers/           # Platform-specific wrappers
│       ├── amp.md.j2
│       ├── claude.md.j2
│       ├── codex.md.j2
│       └── opencode.md.j2
├── _config/
│   └── skills.yaml         # Skill definitions + platform config
├── assemble.py             # Build script
├── amp/skills/             # Generated Amp skills
├── claude/skills/          # Generated Claude skills
├── codex/skills/           # Generated Codex skills
└── opencode/skills/        # Generated OpenCode skills
```

## Step-by-Step Guide

### 1. Research the Platform

Before implementing, document:

- **Skill file format**: What frontmatter fields are supported/required?
- **Naming conventions**: Are there restrictions on skill names?
- **Install location**: Where do skills get installed?
- **Discovery mechanism**: How does the agent find and load skills?
- **Invocation style**: Slash commands, natural language, tool calls?

Create a plan document at `docs/PLAN-<platform>.md` with your findings.

### 2. Create the Wrapper Template

Create `integrations/_templates/wrappers/<platform>.md.j2`:

```jinja2
{#- Platform-specific skill wrapper template -#}
{#- Variables: name, description, title, template, related, ... -#}

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

---
{# Platform-specific frontmatter #}
name: {{ name }}
description: {{ description }}
{# Add other required fields for this platform #}
---

# {{ title }}

{{ description }}

{# Platform-specific header content (usage, invocation) #}
{% if argument_hint %}
## Usage

```
{{ invocation_prefix }}{{ name }} {{ argument_hint }}
```
{% endif %}

{# Include shared prerequisites #}
{% include "partials/prerequisites.md.j2" %}

{# Include the skill-specific content #}
{% include "skills/" ~ template %}

{# Platform-specific footer (related skills) #}
{% if related %}
## Related Skills

{% for r in related %}
- `{{ name_prefix }}{{ r }}`
{% endfor %}
{% endif %}
```

Key template variables (available from skills.yaml + assemble.py):

| Variable | Description |
|----------|-------------|
| `name` | Full skill name (with prefix if applicable) |
| `title` | Human-readable title |
| `description` | Short description |
| `template` | Path to skill template (e.g., `check.md.j2`) |
| `related` | List of related skill keys |
| `argument_hint` | Usage hint (platform-specific) |
| `invocation_prefix` | `/` for Claude, `$` for Codex, etc. |
| `name_prefix` | Platform-specific prefix (e.g., `realitycheck-`) |

### 3. Update skills.yaml

Add platform defaults and per-skill config in `integrations/_config/skills.yaml`:

```yaml
# Global defaults per integration
defaults:
  # ... existing platforms ...
  
  newplatform:
    name_prefix: "realitycheck-"  # Or "" if no prefix needed
    skill_dir: "newplatform/skills"

# Skill definitions
skills:
  check:
    title: "Full Analysis Workflow"
    description: "..."
    template: "check.md.j2"
    related: ["search", "validate"]
    
    # Platform-specific config
    newplatform:
      # Optional: override any defaults
      argument_hint: "<url>"
      # Optional: platform-specific fields
      custom_field: "value"
```

### 4. Update assemble.py

Add the platform to the `INTEGRATIONS` list:

```python
INTEGRATIONS = ["amp", "claude", "codex", "opencode", "newplatform"]
```

The rest of the assembly logic should work automatically if your wrapper template follows the conventions.

### 5. Create Install/Uninstall Scripts

Create `integrations/<platform>/install.sh`:

```bash
#!/usr/bin/env bash
# Install Reality Check skills for <Platform>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="${PLATFORM_SKILLS_DIR:-$HOME/.config/platform/skills}"

echo "Installing Reality Check skills for <Platform>..."
mkdir -p "$SKILLS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name=$(basename "$skill_dir")
    
    # Remove existing symlink if present
    if [ -L "$SKILLS_DST/$skill_name" ]; then
        rm "$SKILLS_DST/$skill_name"
    fi
    
    # Create symlink
    ln -s "$skill_dir" "$SKILLS_DST/$skill_name"
    echo "  Installed: $skill_name"
done

echo "Skills installed to $SKILLS_DST"
```

Create `integrations/<platform>/uninstall.sh`:

```bash
#!/usr/bin/env bash
# Uninstall Reality Check skills for <Platform>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="${PLATFORM_SKILLS_DIR:-$HOME/.config/platform/skills}"

echo "Removing Reality Check skills for <Platform>..."

for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name=$(basename "$skill_dir")
    
    if [ -L "$SKILLS_DST/$skill_name" ]; then
        rm "$SKILLS_DST/$skill_name"
        echo "  Removed: $skill_name"
    fi
done
```

### 6. Add Makefile Targets

Update the main `Makefile`:

```makefile
# At top: add to .PHONY
.PHONY: install-skills-newplatform uninstall-skills-newplatform

# Platform config
NEWPLATFORM_SKILLS_SRC := $(CURDIR)/integrations/newplatform/skills
NEWPLATFORM_SKILLS_DST := $(HOME)/.config/newplatform/skills
NEWPLATFORM_SKILLS := realitycheck realitycheck-check realitycheck-analyze ...

# Install target
install-skills-newplatform:
	@echo "Installing Reality Check skills for <Platform>..."
	@mkdir -p $(NEWPLATFORM_SKILLS_DST)
	@for skill in $(NEWPLATFORM_SKILLS); do \
		if [ -L "$(NEWPLATFORM_SKILLS_DST)/$$skill" ]; then rm "$(NEWPLATFORM_SKILLS_DST)/$$skill"; fi; \
		if [ -d "$(NEWPLATFORM_SKILLS_SRC)/$$skill" ]; then \
			ln -s "$(NEWPLATFORM_SKILLS_SRC)/$$skill" "$(NEWPLATFORM_SKILLS_DST)/$$skill"; \
			echo "  Installed: $$skill"; \
		fi; \
	done
	@echo "Skills installed to $(NEWPLATFORM_SKILLS_DST)"

# Uninstall target
uninstall-skills-newplatform:
	@echo "Removing <Platform> skills..."
	@for skill in $(NEWPLATFORM_SKILLS); do \
		if [ -L "$(NEWPLATFORM_SKILLS_DST)/$$skill" ]; then \
			rm "$(NEWPLATFORM_SKILLS_DST)/$$skill"; \
			echo "  Removed: $$skill"; \
		fi; \
	done

# Update install-skills-all
install-skills-all: install-skills-amp install-skills-claude install-skills-codex install-skills-opencode install-skills-newplatform
```

### 7. Create Platform README

Create `integrations/<platform>/README.md`:

```markdown
# Reality Check - <Platform> Integration

Reality Check skills for <Platform>.

## Installation

```bash
make install-skills-<platform>
```

Or manually:

```bash
bash integrations/<platform>/install.sh
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `realitycheck` | Main entry point |
| `realitycheck-check` | Full analysis workflow |
| ... | ... |

## Usage

[Platform-specific usage examples]

## Uninstallation

```bash
make uninstall-skills-<platform>
```
```

### 8. Update Main README

Add a section to the main `README.md`:

```markdown
## <Platform> Skills

[Platform](https://platform.example) is ... Reality Check includes skills that ...

### Install Skills

```bash
make install-skills-<platform>
```

### Usage

[Brief usage example]

See `integrations/<platform>/README.md` for full documentation.
```

### 9. Test

1. Generate skills: `make assemble-skills`
2. Verify no drift: `make check-skills`
3. Install: `make install-skills-<platform>`
4. Launch the platform and verify skills are discoverable
5. Test loading and running a skill
6. Uninstall: `make uninstall-skills-<platform>`

## Platform-Specific Considerations

### Frontmatter Compatibility

Different platforms support different frontmatter fields:

| Platform | Required Fields | Optional Fields | Ignored Fields |
|----------|-----------------|-----------------|----------------|
| Claude | `name`, `description` | `argument-hint`, `allowed-tools` | - |
| Codex | `name`, `description` | - | Most extras |
| Amp | `name`, `description` | `triggers` | - |
| OpenCode | `name`, `description` | `license`, `compatibility`, `metadata` | Unknown fields |

When creating a wrapper template, only emit fields the platform recognizes.

### Naming Conventions

| Platform | Convention | Example |
|----------|------------|---------|
| Claude | No prefix, short names | `check`, `validate` |
| Codex | No prefix, short names | `check`, `validate` |
| Amp | `realitycheck-` prefix | `realitycheck-check` |
| OpenCode | `realitycheck-` prefix | `realitycheck-check` |

Use prefixes when:
- Installing to a global/shared location
- Avoiding collisions with other skills
- The platform has many users installing diverse skills

### Invocation Styles

| Platform | Style | Example |
|----------|-------|---------|
| Claude | Slash commands | `/check <url>` |
| Codex | Dollar commands | `$check <url>` |
| Amp | Natural language | "Analyze this article for claims" |
| OpenCode | Tool calls | `skill({ name: "realitycheck-check" })` |

Adjust your wrapper template's usage section accordingly.

## Checklist

When adding a new platform:

- [ ] Research platform skill specification
- [ ] Create `docs/PLAN-<platform>.md`
- [ ] Create `integrations/_templates/wrappers/<platform>.md.j2`
- [ ] Update `integrations/_config/skills.yaml`
- [ ] Update `integrations/assemble.py` INTEGRATIONS list
- [ ] Run `make assemble-skills` and verify output
- [ ] Create `integrations/<platform>/README.md`
- [ ] Create `integrations/<platform>/install.sh`
- [ ] Create `integrations/<platform>/uninstall.sh`
- [ ] Add Makefile targets
- [ ] Update main README.md
- [ ] Test installation and usage
- [ ] Create `docs/IMPLEMENTATION-<platform>.md` to track progress

## Examples

See existing integrations for reference:

- **Claude**: `integrations/claude/` + `_templates/wrappers/claude.md.j2`
- **Codex**: `integrations/codex/` + `_templates/wrappers/codex.md.j2`
- **Amp**: `integrations/amp/` + `_templates/wrappers/amp.md.j2`
- **OpenCode**: `integrations/opencode/` + `_templates/wrappers/opencode.md.j2`

---

*Last updated: 2026-01-27*
