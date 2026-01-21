# Plan: Framework / Analysis Repo Separation

## Overview

Separate the reusable analysis framework from specific analysis projects to enable:
- Clean reuse of the framework across multiple analysis projects
- Independent versioning of framework vs analysis data
- Plugin integration that works across projects
- Clear distinction between "the tool" and "work done with the tool"

---

## How Claude Code Skills/Plugins Work

Understanding the skill system is critical for architecture decisions.

### What Skills Actually Are

**Skills are NOT:**
- ❌ Python API bindings
- ❌ New tool definitions
- ❌ Direct database access
- ❌ Custom Claude capabilities

**Skills ARE:**
- ✅ Prompt injection (markdown instructions injected into context)
- ✅ Pre-authorized Bash commands (shell scripts Claude can run)
- ✅ Lifecycle hooks (Stop, etc.)
- ✅ Structured ways to teach Claude a workflow

### Plugin Directory Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json           # Metadata: name, description, author
├── commands/
│   ├── my-command.md         # Slash command definitions
│   └── another-command.md
├── hooks/
│   └── hooks.json            # Lifecycle hooks (Stop, PreToolUse, etc.)
├── scripts/
│   └── my-script.sh          # Shell scripts commands can invoke
└── README.md
```

### How Slash Commands Work

A command like `/analyze` is defined in a markdown file with YAML frontmatter:

```markdown
# commands/analyze.md
---
description: "Analyze a source document"
argument-hint: "SOURCE_PATH"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-analysis.sh)"]
hide-from-slash-command-tool: "false"
---

# Analyze Source Command

When the user runs `/analyze <path>`, follow these steps:

1. Read the source file at the provided path
2. Execute the analysis setup:
   ```!
   "${CLAUDE_PLUGIN_ROOT}/scripts/run-analysis.sh" $ARGUMENTS
   ```
3. Follow the Source Analysis Template methodology
4. Extract claims using the taxonomy defined below
5. Save results to the database

## Source Analysis Template

[... full methodology instructions ...]

## Claim Taxonomy

[... domain definitions, evidence levels, etc. ...]
```

### The Execution Flow

1. **User types** `/analyze paper.pdf`
2. **Claude Code** finds matching command in installed plugins
3. **Markdown content** is injected into Claude's context as system instructions
4. **Claude sees** the instructions and follows them using standard tools:
   - `Read` to read files
   - `Bash` to run allowed scripts (pre-authorized in frontmatter)
   - `Write` to create output files
   - `Edit` to modify files
5. **No new capabilities** - just structured prompting + script access

### Key Insight: Skills = Methodology + Script Access

The skill doesn't give Claude new abilities. It:
1. **Teaches Claude a workflow** via injected markdown
2. **Pre-authorizes specific scripts** so Claude can run them without prompting
3. **Provides context** (templates, taxonomies, instructions)

This means our framework's "skill" is essentially:
- The CLAUDE.md methodology, packaged as injectable commands
- Shell wrappers around our Python scripts
- Pre-authorization for those wrappers

### Hooks

Hooks let plugins react to Claude Code lifecycle events:

```json
// hooks/hooks.json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/on-stop.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/before-bash.sh"
          }
        ]
      }
    ]
  }
}
```

Available hooks:
- `Stop` - When Claude finishes/exits
- `PreToolUse` - Before a tool is invoked
- `PostToolUse` - After a tool completes
- `Notification` - On notifications

### Environment Variables Available

In scripts and command markdown:
- `$CLAUDE_PLUGIN_ROOT` - Path to the plugin directory
- `$ARGUMENTS` - Arguments passed to the slash command
- Standard env vars from the shell

### Installation Locations

Plugins can be installed:
- **User-level**: `~/.claude/plugins/cache/[marketplace]/[plugin]/[version]/`
- **Project-level**: `.claude-plugin/` in project root (not common)

---

## Architectural Implications

### What This Means for Our Design

Given that skills are prompt injection + script access:

1. **Scripts must be self-contained CLI tools**
   - Each script should be invocable from bash with arguments
   - Scripts handle their own path resolution, config loading
   - No assumption of Python import context

2. **The skill is thin**
   - Mostly markdown methodology (extracted from CLAUDE.md)
   - Shell wrappers that call Python scripts
   - Pre-authorization list for those wrappers

3. **Framework location must be discoverable**
   - Scripts need to find the database, config, templates
   - Options: env var, config file, convention (`.framework/`)

4. **Project context detection**
   - Skill commands need to know which project they're operating on
   - Look for `.realitycheck.yaml` config file

### Revised Skill Architecture

```
realitycheck/
├── plugin/                      # Claude Code plugin (was skill/)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/
│   │   ├── analyze.md           # /analyze - full source analysis
│   │   ├── claim.md             # /claim - add/search claims
│   │   ├── validate.md          # /validate - check integrity
│   │   ├── export.md            # /export - export to YAML/MD
│   │   ├── search.md            # /search - semantic search
│   │   ├── init.md              # /init - initialize new project
│   │   └── help.md              # /analysis-help - show methodology
│   ├── hooks/
│   │   └── hooks.json           # Optional: auto-validate on stop?
│   └── scripts/
│       ├── resolve-project.sh # Find framework path
│       ├── run-db.sh            # Wrapper for db.py
│       ├── run-validate.sh      # Wrapper for validate.py
│       ├── run-export.sh        # Wrapper for export.py
│       └── run-migrate.sh       # Wrapper for migrate.py
│
├── scripts/                     # Core Python (unchanged)
│   ├── db.py
│   ├── validate.py
│   ├── export.py
│   └── migrate.py
│
└── methodology/                 # Extracted from CLAUDE.md
    ├── source-analysis.md
    ├── claim-taxonomy.md
    ├── evidence-hierarchy.md
    ├── chain-analysis.md
    └── templates/
        ├── source-template.md
        ├── synthesis-template.md
        └── scenario-matrix-template.md
```

### Example Command: `/analyze`

```markdown
# plugin/commands/analyze.md
---
description: "Analyze a source document using the framework methodology"
argument-hint: "SOURCE_PATH_OR_URL"
allowed-tools: [
  "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh)",
  "Read",
  "Write",
  "WebFetch"
]
---

# Analyze Source

You are performing a structured source analysis using the Analysis Framework.

## Setup

First, resolve the framework and project paths:
```!
source "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-project.sh"
```

## Input

Source to analyze: $ARGUMENTS

## Methodology

Follow the three-stage analysis process:

### Stage 1: Descriptive Analysis
- Summarize the source neutrally
- Extract key claims (assign IDs using format DOMAIN-YYYY-NNN)
- Identify theoretical lineage
- Note scope and limitations

### Stage 2: Evaluative Analysis
- Assess internal coherence
- Rate evidence using the Evidence Hierarchy:
  | Level | Strength | Description |
  |-------|----------|-------------|
  | E1 | Strong Empirical | Replicated studies, verified data |
  | E2 | Moderate Empirical | Single studies, case studies |
  | E3 | Strong Theoretical | Logical from established principles |
  | E4 | Weak Theoretical | Plausible extrapolation |
  | E5 | Opinion/Forecast | Credentialed speculation |
  | E6 | Unsupported | Assertions without evidence |

[... rest of methodology ...]

## Output

1. Create analysis document at `analysis/sources/[source-id].md`
2. Add claims to database (use Python API via the framework scripts)
3. Update source registry in `reference/sources.yaml`
4. Run validation to ensure integrity

## Claim Taxonomy

[... full taxonomy from CLAUDE.md ...]
```

### Example Script Wrapper

```bash
# plugin/scripts/run-db.sh
#!/bin/bash
set -euo pipefail

# Find project root by walking up to find .realitycheck.yaml
find_project_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/.realitycheck.yaml" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$PWD"
}

PROJECT_ROOT="$(find_project_root)"

# Read database path from config, or use default
if [[ -f "$PROJECT_ROOT/.realitycheck.yaml" ]]; then
    # Extract db_path from YAML (simple grep, could use yq for robustness)
    DB_PATH=$(grep "^db_path:" "$PROJECT_ROOT/.realitycheck.yaml" | sed 's/.*db_path:\s*["]*\([^"]*\)["]*$/\1/' || echo "data/realitycheck.lance")
else
    DB_PATH="data/realitycheck.lance"
fi

# Make path absolute if relative
if [[ "$DB_PATH" != /* ]]; then
    DB_PATH="$PROJECT_ROOT/$DB_PATH"
fi

# Determine framework location
if [[ -d "$PROJECT_ROOT/.framework/scripts" ]]; then
    # Submodule mode: use local framework
    SCRIPTS_DIR="$PROJECT_ROOT/.framework/scripts"
elif [[ -d "$(dirname "$0")/../lib" ]]; then
    # Plugin mode: use bundled scripts
    SCRIPTS_DIR="$(dirname "$0")/../lib"
else
    echo "Error: Cannot find realitycheck scripts" >&2
    exit 1
fi

# Set env var for db.py and run
export REALITYCHECK_DATA="$DB_PATH"
python "$SCRIPTS_DIR/db.py" "$@"
```

**Note**: Current db.py CLI supports: `init`, `stats`, `reset`, `search`.
Additional commands like `add-claim` are planned (see CLI Expansion below).

### Installation Flow

```bash
# Option 1: Install from GitHub (future: plugin marketplace)
# Plugin installed to ~/.claude/plugins/cache/...
# NOTE: Exact syntax TBD - depends on Claude Code plugin marketplace updates
claude plugin install github:lhl/realitycheck

# Option 2: Local development (symlink)
ln -s /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck

# Option 3: Project-local (plugin in project root)
# Just have .claude-plugin/ directory in project root
```

### Plugin Distribution: Scripts Bundling

**Problem**: In plugin-only mode (no submodule), how does the plugin find Python scripts?

**Solution**: The plugin is distributed as a self-contained bundle that includes copies of
the Python scripts. The repo structure during development has scripts/ at top level, but
the **distributed plugin** includes everything needed:

```
# Distributed plugin structure (what gets installed)
realitycheck-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── *.md
├── hooks/
│   └── hooks.json
├── scripts/              # Shell wrappers
│   └── run-*.sh
└── lib/                  # Python scripts bundled for distribution
    ├── db.py
    ├── validate.py
    ├── export.py
    └── migrate.py
```

**Build step** (part of release process):
```bash
# Copy Python scripts into plugin for distribution
cp scripts/*.py plugin/lib/

# Build and publish to PyPI
uv build
uv publish

# Package plugin for Claude Code distribution (future)
```

**Wrapper script resolution** (updated from earlier example):
```bash
# In plugin/scripts/run-db.sh
if [[ -d "$PROJECT_ROOT/.framework/scripts" ]]; then
    # Submodule mode: use local framework
    SCRIPTS_DIR="$PROJECT_ROOT/.framework/scripts"
elif [[ -d "$(dirname "$0")/../lib" ]]; then
    # Plugin mode: use bundled scripts
    SCRIPTS_DIR="$(dirname "$0")/../lib"
else
    echo "Error: Cannot find realitycheck scripts" >&2
    exit 1
fi
```

This ensures plugin-only mode is fully self-contained while submodule mode uses
version-locked scripts from the project.

### CLI Expansion Plan

Current db.py CLI commands:
- `init` - Initialize database tables
- `stats` - Show database statistics
- `reset` - Drop all tables and reinitialize
- `search <query>` - Semantic search across claims

**Planned additions** (Phase 2 work):

```bash
# Claim operations
db.py claim add --text "..." --type "[T]" --domain "TECH" --source-id "..."   # auto-allocates ID (or accept --id)
db.py claim get <claim-id>
db.py claim list [--domain TECH] [--type "[P]"]
db.py claim update <claim-id> --credence 0.7

# Source operations
db.py source add --id "author-2026-title" --title "..." --type "PAPER"
db.py source get <source-id>
db.py source list [--type PAPER]

# Relationship operations
db.py link <claim-id> supports <target-id>
db.py link <claim-id> contradicts <target-id>
db.py link <claim-id> depends_on <target-id>

# Chain operations
db.py chain add --name "..." --thesis "..." --claims TECH-2026-001 LABOR-2026-002 --analysis-file "analysis/syntheses/..."
db.py chain get <chain-id>
db.py chain list

# Prediction operations
db.py prediction add --claim-id LABOR-2026-002 --source-id "..." --target-date "2035-12-31"
db.py prediction update LABOR-2026-002 --status "[P→]" --last-evaluated "2026-01-20"
db.py prediction list [--domain LABOR]
```

**Design decision**: Expand db.py with subcommands rather than separate CLI entrypoints.
This keeps the interface unified and matches how users will invoke via plugin wrappers.

**Alternative considered**: Claude directly uses Python API functions via inline code.
The plugin's `/analyze` command could have Claude write claims programmatically rather
than via CLI. This is simpler but less composable for non-Claude automation.

---

## Proposed Repository Structure

### 1. `realitycheck` (The Tool)

The reusable methodology, scripts, plugin, and tests.

```
realitycheck/
├── README.md                 # Framework overview, installation, usage
├── AGENTS.md                 # Dev workflow for contributors
├── CLAUDE.md                 # Agent instructions (points to methodology/)
├── LICENSE
│
├── scripts/                  # Core Python CLI tools
│   ├── db.py                 # LanceDB operations (add, get, search, etc.)
│   ├── migrate.py            # YAML → LanceDB migration
│   ├── export.py             # DB → Markdown/YAML export
│   ├── embed.py              # Embedding generation
│   └── validate.py           # Data integrity validation
│
├── tests/                    # Framework test suite
│   ├── conftest.py
│   ├── test_db.py
│   ├── test_migrate.py
│   ├── test_validate.py
│   ├── test_export.py
│   └── test_e2e.py
│
├── plugin/                   # Claude Code plugin
│   ├── .claude-plugin/
│   │   └── plugin.json       # Plugin metadata
│   ├── commands/
│   │   ├── analyze.md        # /analyze - source analysis
│   │   ├── claim.md          # /claim - add/search claims
│   │   ├── validate.md       # /validate - integrity check
│   │   ├── export.md         # /export - export data
│   │   ├── search.md         # /search - semantic search
│   │   ├── init.md           # /init - new project setup
│   │   └── help.md           # /analysis-help - methodology reference
│   ├── hooks/
│   │   └── hooks.json        # Optional lifecycle hooks
│   └── scripts/
│       ├── resolve-project.sh    # Find project root & config
│       ├── run-db.sh             # Wrapper for db.py
│       ├── run-validate.sh       # Wrapper for validate.py
│       ├── run-export.sh         # Wrapper for export.py
│       └── run-migrate.sh        # Wrapper for migrate.py
│
├── methodology/              # Analysis methodology (extracted from CLAUDE.md)
│   ├── README.md             # Methodology overview
│   ├── three-stage-analysis.md
│   ├── evidence-hierarchy.md
│   ├── claim-taxonomy.md
│   ├── chain-analysis.md
│   ├── prediction-tracking.md
│   └── templates/
│       ├── source-analysis.md
│       ├── claim-record.md
│       ├── synthesis.md
│       ├── scenario-matrix.md
│       └── indicator-dashboard.md
│
├── docs/                     # Framework documentation
│   ├── SCHEMA.md             # LanceDB schema reference
│   ├── WORKFLOWS.md          # How to use the framework
│   ├── PLUGIN.md             # Plugin installation & usage
│   └── CONTRIBUTING.md       # How to contribute
│
├── examples/                 # Minimal examples (for illustration)
│   ├── example-claim.yaml
│   └── example-source.yaml
│
├── pyproject.toml            # Project config & dependencies (uv-managed)
├── uv.lock                   # Locked dependencies
└── pytest.ini
```

**Key characteristics:**
- No actual analysis data (just examples)
- Contains methodology, scripts, and plugin
- Plugin commands inject methodology + call scripts
- Tests use synthetic fixtures only
- Can be used as submodule or installed globally

---

### 2. `realitycheck-data` (User's Knowledge Base)

The default is a **single unified knowledge base** per user. Separate repos only for org/privacy boundaries.

**Why unified?**
- Claims build on each other across topics (e.g., AI claims inform economics claims)
- Shared evidence hierarchy enables consistent evaluation
- Cross-domain synthesis becomes possible (connecting tech → labor → governance)
- Semantic search works across your entire knowledge base
- Avoids siloed thinking that topic-based repos would encourage

**When to separate:**
- Different organizations (work vs personal)
- Privacy requirements (client work, confidential research)
- Collaboration (shared team knowledge base)

```
realitycheck-data/                     # User's unified knowledge base (default)
├── README.md                 # Project overview, research questions
├── CLAUDE.md                 # Project-specific instructions (extends framework)
│
├── data/
│   └── realitycheck.lance/   # LanceDB database (git-lfs)
│
├── claims/                   # Exported claim registry
│   └── registry.yaml
│
├── reference/                # Source materials
│   ├── sources.yaml
│   ├── primary/
│   └── transcripts/
│
├── inbox/                    # Symlinks only (optional WIP workflow)
│   ├── to-catalog/
│   ├── to-analyze/
│   ├── to-extract/
│   └── in-progress/
│
├── analysis/                 # Completed analyses
│   ├── sources/
│   ├── comparisons/
│   ├── syntheses/
│   └── meta/
│
├── tracking/                 # Predictions and dashboards
│   ├── predictions.md
│   ├── dashboards/
│   └── updates/
│
├── scenarios/                # Scenario matrices
│
├── frameworks/               # Project-specific taxonomies
│
├── scripts/                  # Project-local helpers (optional)
│   └── hooks/
│       └── pre-commit        # Run validation before commits
│
└── .realitycheck.yaml       # Framework config (see below)
```

**Key characteristics:**
- Contains actual research/analysis
- References the framework (doesn't duplicate it)
- Project-specific CLAUDE.md can extend/override framework methodology
- Self-contained: all data needed to understand the analysis

---

## Framework Integration Options

How does an analysis project use the framework?

### Option A: Git Submodule

```bash
# In analysis project
git submodule add https://github.com/lhl/realitycheck.git .framework
```

```
realitycheck-data/
├── .framework/              # Submodule → realitycheck repo
│   ├── scripts/
│   ├── plugin/
│   └── ...
├── data/
└── ...
```

**Pros:** Version-locked, offline-capable, explicit
**Cons:** Submodule complexity, manual updates

### Option B: Symlink / Path Reference

```bash
# Clone framework to a standard location
git clone https://github.com/lhl/realitycheck.git ~/.local/share/realitycheck

# In analysis project, reference via config
echo "FRAMEWORK_PATH=~/.local/share/realitycheck" > .env
```

**Pros:** Single framework install, easy updates
**Cons:** Not self-contained, path management

### Option C: uv/pip Install from PyPI

```bash
# Recommended: use uv for fast, reliable installs
uv add realitycheck

# Traditional pip also works
pip install realitycheck

# Or install from git for development/pre-release
uv add git+https://github.com/lhl/realitycheck.git
```

```python
from realitycheck import db, validate, export
```

**Pros:** Standard Python packaging, clean imports, automatic updates via pip
**Cons:** Requires Python environment setup

### Option D: Plugin-Only (Simplest)

The framework lives as a Claude Code plugin. Scripts are invoked through the plugin or copied as needed.

```bash
# Install plugin globally (symlink for development)
ln -s /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck
```

Analysis projects just have data. The plugin provides methodology + commands.

**Pros:** Simplest, no code duplication in projects
**Cons:** Less explicit, plugin must handle path resolution

---

## Recommended Approach: Plugin + Submodule Hybrid

Given that skills/plugins are prompt injection + script access:

1. **Framework repo** contains:
   - Core Python scripts (the actual tools)
   - Plugin definition (commands + script wrappers)
   - Methodology docs (extracted from CLAUDE.md)

2. **Analysis projects** use:
   - Framework as git submodule (`.framework/`) for script access
   - OR just rely on globally-installed plugin (simpler, less explicit)

3. **Plugin** is installed globally, discovers project context at runtime

### Project Config File: `.realitycheck.yaml`

```yaml
# .realitycheck.yaml (in each analysis project root)
version: "1.0"

# Where to find framework (if not using global plugin)
framework:
  path: ".framework"           # Submodule path, or "global" for installed plugin

# Database location
db_path: "data/realitycheck.lance"

# Custom domains (extends framework defaults)
domains:
  - id: CYBER
    name: Cybersecurity
  - id: TIC
    name: Techno-industrial complex

# Export paths
export:
  claims_yaml: "claims/registry.yaml"
  sources_yaml: "reference/sources.yaml"
  predictions_md: "tracking/predictions.md"

# Project metadata
project:
  name: "Post-Singularity Economic Analysis"
  description: "Analysis of economic theories related to AI/automation"
```

### Plugin Commands

The plugin provides these slash commands:

| Command | Description |
|---------|-------------|
| `/analyze <source>` | Full 3-stage source analysis |
| `/claim add <text>` | Add a new claim to the database |
| `/claim search <query>` | Semantic search across claims |
| `/validate` | Run integrity validation |
| `/export [format]` | Export to YAML/Markdown |
| `/init` | Initialize new analysis project |
| `/analysis-help` | Show methodology reference |

### How Commands Find the Project

Each command's script wrapper follows this resolution order:

1. Check for `.realitycheck.yaml` in current directory
2. Walk up directory tree looking for config
3. If found: use project settings
4. If not found: use sensible defaults (current dir)

```bash
# In plugin/scripts/resolve-project.sh
find_project_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/.realitycheck.yaml" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$PWD"  # Default to current directory
}
```

### Two Usage Modes

**Mode A: Plugin-only (Simplest)**
```bash
# Install plugin globally (syntax TBD, see "Still Open" section)
claude plugin install github:lhl/realitycheck

# Create project
mkdir realitycheck-data && cd realitycheck-data
claude
> /init  # Creates .realitycheck.yaml, data/, etc.
> /analyze paper.pdf
```

Plugin contains all methodology. Scripts run from plugin directory.
Project just has data + config.

**Mode B: Submodule + Plugin (Most Explicit)**
```bash
# Create project with framework submodule
mkdir realitycheck-data && cd realitycheck-data
git init
git submodule add https://github.com/lhl/realitycheck.git .framework

# Config points to local framework
cat > .realitycheck.yaml << EOF
version: "1.0"
framework_path: ".framework"
db_path: "data/realitycheck.lance"
EOF

# Plugin detects .framework/ and uses local scripts
claude
> /analyze paper.pdf
```

Project is self-contained. Scripts come from submodule.
Plugin still provides commands but defers to local scripts.

---

## Migration Plan

### Phase 1: Restructure Framework Repo

Legacy `analysis-framework` already has `scripts/` and `tests/`. `realitycheck` will copy/rename them, then:

1. [ ] Create `plugin/` directory structure
   - [ ] `.claude-plugin/plugin.json`
   - [ ] `commands/` with command markdown files
   - [ ] `scripts/` with shell wrappers
2. [ ] Create `methodology/` directory
   - [ ] Extract methodology content from CLAUDE.md
   - [ ] Split into focused documents (evidence-hierarchy.md, etc.)
   - [ ] Move templates into `methodology/templates/`
3. [ ] Update CLAUDE.md to reference methodology/ instead of inlining
4. [ ] Create `docs/PLUGIN.md` with installation instructions
5. [ ] Ensure scripts work as CLI tools (accept --db-path, etc.)
6. [ ] Tests still pass
7. [ ] Tag as v0.1.0-alpha

### Phase 2: Create Plugin Commands

1. [ ] `/init` command - create new project structure
2. [ ] `/analyze` command - full source analysis workflow
3. [ ] `/claim` command - add/search claims
4. [ ] `/validate` command - run validation
5. [ ] `/export` command - export to YAML/MD
6. [ ] `/search` command - semantic search
7. [ ] `/analysis-help` command - show methodology
8. [ ] Shell wrapper scripts that resolve project context
9. [ ] Test each command manually
10. [ ] Tag as v0.1.0-beta

### Phase 3: Separate Analysis Data

1. [ ] Create `realitycheck-data` repo (or migrate existing)
2. [ ] Move data/, claims/, reference/, analysis/, tracking/, scenarios/, frameworks/
3. [ ] Create `.realitycheck.yaml` config
4. [ ] Create project-specific CLAUDE.md (minimal, extends framework)
5. [ ] Optionally add framework as submodule
6. [ ] Verify `/validate` passes
7. [ ] Update any hardcoded paths

### Phase 4: Clean Up & Publish

1. [ ] Remove analysis data from framework repo
2. [ ] Keep only: scripts/, tests/, plugin/, methodology/, docs/, examples/
3. [ ] Update README with installation + quickstart
4. [ ] Finalize pyproject.toml for PyPI
   - [ ] Package metadata (name, version, description, author, license)
   - [ ] Entry points for CLI commands
   - [ ] Dependencies with version constraints
5. [ ] Test PyPI publishing with TestPyPI first
   - [ ] `uv publish --publish-url https://test.pypi.org/legacy/`
   - [ ] Verify install: `pip install -i https://test.pypi.org/simple/ realitycheck`
6. [ ] Publish to PyPI: `uv publish`
7. [ ] Tag as v1.0.0
8. [ ] Archive or rename old combined repo

### Phase 5: Test Full Workflow

1. [ ] Fresh clone of framework repo
2. [ ] Install plugin globally
3. [ ] Create new test project with `/init`
4. [ ] Run through analysis workflow
5. [ ] Verify everything works end-to-end
6. [ ] Document any issues found

---

## Open Questions

### Resolved

1. **How do skills work?**
   - Skills = prompt injection + pre-authorized scripts
   - NOT Python API bindings or new tool definitions
   - Plugin commands are markdown with methodology + shell wrappers

2. **Repo naming**
   - Framework: `realitycheck` (pip installable, memorable)
   - User's data: `realitycheck-data` (singular, unified knowledge base)
   - Org/private: `realitycheck-data-[org]` (e.g., `realitycheck-data-acme`) - only for privacy/collaboration boundaries
   - Starter: `realitycheck-data-example`

3. **Single unified knowledge base is the default**
   - One DB per user, not per topic
   - Topics handled via domains/tags within the single DB
   - Separation only for: org boundaries, privacy requirements, collaboration needs
   - Epistemological advantage: claims build on each other across topics, shared evidence hierarchy, cross-domain synthesis possible
   - LanceDB scales fine - no technical need to split by topic

4. **Framework versioning**
   - Semver (v1.0, v1.1, v2.0)
   - Projects pin via submodule commit or just use latest plugin

5. **PyPI publishing**
   - Package name: `realitycheck` (confirmed available)
   - Managed with `uv` (pyproject.toml + uv.lock)
   - Published via `uv publish` or GitHub Actions
   - Users install with `pip install realitycheck` or `uv add realitycheck`

### Still Open

1. **Plugin marketplace mechanics**
   - Exact `claude plugin install` syntax TBD (depends on Claude Code updates)
   - For now: symlink for development, GitHub URL for distribution

2. **Template customization**
   - Can projects override framework templates?
   - Proposal: Project `methodology/templates/` takes precedence if exists

3. **Shared claims across projects**
   - What if two projects reference the same claim?
   - Proposal: Claims are project-scoped; cross-project uses URLs (future)

4. **CLAUDE.md relationship**
   - Framework CLAUDE.md vs project CLAUDE.md - how do they interact?
   - Does project CLAUDE.md "extend" or "replace"?
   - Proposal: Project inherits framework methodology, can override specific sections

5. **Database location for plugin-only mode** ✓ RESOLVED
   - Plugin bundles Python scripts in `lib/` directory
   - Wrappers check for submodule first, fall back to bundled lib/
   - See "Plugin Distribution: Scripts Bundling" section above

6. **LFS for LanceDB**
   - Should realitycheck.lance/ be in git-lfs?
   - Or .gitignore and backup separately?
   - Trade-offs: LFS adds complexity, but keeps data versioned

---

## Example Workflows

### Starting a New Analysis Project

```bash
# 1. Create project repo
mkdir realitycheck-data && cd realitycheck-data
git init

# 2. Add framework as submodule (optional but recommended)
git submodule add https://github.com/lhl/realitycheck.git .framework

# 3. Create project structure
mkdir -p data claims reference/primary analysis/sources tracking scenarios

# 4. Configure
cat > .realitycheck.yaml << 'EOF'
version: "1.0"
framework_path: ".framework"
db_path: "data/realitycheck.lance"
export:
  claims_yaml: "claims/registry.yaml"
  sources_yaml: "reference/sources.yaml"
EOF

# 5. Initialize database
export REALITYCHECK_DATA="data/realitycheck.lance"
python .framework/scripts/db.py init

# 6. Start analyzing (use plugin or scripts directly)
```

### Using the Plugin in Any Project

```bash
# With plugin installed globally
cd ~/realitycheck-data

# Plugin auto-detects project context
claude
> /analyze https://ipcc.ch/report/ar6/

# Claims stored in project's database
# Analysis saved to project's analysis/ directory
```

### Updating Framework in a Project

```bash
cd ~/realitycheck-data

# Update submodule to latest
cd .framework
git fetch origin
git checkout v1.1.0  # or latest tag
cd ..

# Commit the update
git add .framework
git commit -m "chore: update framework to v1.1.0"

# Check for any schema changes that need migration
python .framework/scripts/validate.py
```

---

## Success Criteria

- [ ] Framework repo contains no analysis data
- [ ] Analysis project works with framework as submodule
- [ ] Plugin functions correctly in multi-project setup
- [ ] New project can be initialized in < 5 minutes
- [ ] Existing postsingularity analysis migrated successfully
- [ ] Framework tests pass independently
- [ ] Documentation is clear and complete

---

## Timeline Estimate

- Phase 1 (Framework Repo): 1-2 sessions
- Phase 2 (Plugin Commands): 1 session
- Phase 3 (Separate Analysis Data): 1-2 sessions
- Phase 4 (Clean Up & Publish): 1-2 sessions
- Phase 5 (Test Full Workflow): 1 session

Total: 5-8 focused sessions

---

*Plan created: 2026-01-20*
*Last updated: 2026-01-20*
*Status: Draft - consistency fixes applied, uv for package management, ready for implementation*
