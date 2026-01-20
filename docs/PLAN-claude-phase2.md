# Phase 2 Implementation Plan: Plugin Commands & CLI Expansion

## File Tree

```
/home/lhl/github/lhl/realitycheck/
├── scripts/
│   └── UPDATE db.py              # Expand CLI with add/get/list/update/related/import
├── plugin/
│   ├── commands/
│   │   ├── NEW check.md          # Flagship /check command
│   │   ├── NEW realitycheck.md   # Alias for /check
│   │   └── UPDATE *.md           # Wire existing commands to CLI
│   ├── scripts/
│   │   ├── NEW run-db.sh         # Shell wrapper for db.py
│   │   ├── NEW run-validate.sh   # Shell wrapper for validate.py
│   │   ├── NEW run-export.sh     # Shell wrapper for export.py
│   │   └── NEW resolve-project.sh # Project context detection
│   └── hooks/
│       └── NEW hooks.json        # Lifecycle hooks (optional)
├── tests/
│   └── UPDATE test_db.py         # Tests for new CLI commands
└── docs/
    └── UPDATE IMPLEMENTATION.md  # Progress tracking
```

## Implementation Tasks

### 1. Extend db.py CLI (Core Priority)

The CRUD functions already exist in db.py. We need to expose them via CLI subcommands.

**New CLI structure:**

```bash
# Claim operations
rc-db claim add --text "..." --type "[T]" --domain "TECH" [--id ID] [--credence 0.7]
rc-db claim get <claim-id>
rc-db claim list [--domain DOMAIN] [--type TYPE] [--limit N]
rc-db claim update <claim-id> --credence 0.9 [--notes "..."]

# Source operations
rc-db source add --id "author-2026-title" --title "..." --type "PAPER" --author "Name" --year 2026
rc-db source get <source-id>
rc-db source list [--type TYPE] [--status STATUS] [--limit N]

# Chain operations
rc-db chain add --id "CHAIN-2026-001" --name "..." --thesis "..." --claims ID1,ID2
rc-db chain get <chain-id>
rc-db chain list [--limit N]

# Prediction operations
rc-db prediction add --claim-id ID --source-id ID --status "[P→]" [--target-date DATE]
rc-db prediction list [--status STATUS]

# Relationship operations
rc-db related <claim-id>

# Bulk operations
rc-db import <file.yaml> [--type claims|sources|all]

# Existing commands (unchanged)
rc-db init
rc-db stats
rc-db reset
rc-db search <query>
```

**Implementation approach:**
- Add nested subparsers: `parser → claim_parser → add/get/list/update`
- Use existing CRUD functions (add_claim, get_claim, etc.)
- Output JSON by default, human-readable with `--format text`
- Auto-generate claim IDs from domain + counter when `--id` not provided

### 2. Create Shell Wrapper Scripts

**plugin/scripts/resolve-project.sh:**
```bash
#!/bin/bash
# Find project root by locating .realitycheck.yaml
# Sets PROJECT_ROOT, DB_PATH environment variables
```

**plugin/scripts/run-db.sh:**
```bash
#!/bin/bash
# Source resolve-project.sh
# Run: uv run rc-db "$@" (with ANALYSIS_DB_PATH set)
```

Similar wrappers for validate.sh, export.sh.

### 3. Create Flagship `/check` Command

**plugin/commands/check.md:**
Full analysis workflow:
1. Fetch source (WebFetch for URLs)
2. Run 3-stage analysis (using existing /analyze methodology)
3. Extract claims with IDs
4. Register source and claims in database
5. Generate embeddings
6. Run validation
7. Return summary report

**plugin/commands/realitycheck.md:**
Simple alias that includes check.md content.

### 4. Wire Existing Commands to CLI

Update plugin/commands/*.md to include shell script invocations:

```markdown
# /search command (updated)
---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh)"]
---

When the user runs `/search <query>`, execute:
```!
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" search "$ARGUMENTS"
```
```

### 5. Add Tests for New CLI Commands

**tests/test_db.py additions:**

```python
class TestClaimCLI:
    def test_claim_add_creates_claim(self, initialized_db, capsys)
    def test_claim_add_auto_generates_id(self, initialized_db)
    def test_claim_get_outputs_json(self, initialized_db, sample_claim)
    def test_claim_list_filters_work(self, initialized_db)
    def test_claim_update_modifies_record(self, initialized_db)

class TestSourceCLI:
    def test_source_add_creates_source(self, initialized_db)
    def test_source_get_outputs_json(self, initialized_db)
    def test_source_list_filters_work(self, initialized_db)

class TestImportCLI:
    def test_import_yaml_claims(self, initialized_db, tmp_path)
    def test_import_handles_missing_file(self, initialized_db)

class TestRelatedCLI:
    def test_related_shows_relationships(self, initialized_db)
```

## Execution Order

1. **CLI Extension** - Add subcommands to db.py (most critical)
   - Start with `claim add/get/list/update`
   - Then `source add/get/list`
   - Then `chain`, `prediction`, `related`, `import`

2. **Tests** - Write tests alongside each CLI addition

3. **Shell Wrappers** - Create plugin/scripts/*.sh

4. **Flagship Commands** - Create /check and /realitycheck

5. **Wire Commands** - Update existing command markdown files

6. **Documentation** - Update IMPLEMENTATION.md, PLUGIN.md

## Key Design Decisions

1. **Nested subparsers**: `rc-db claim add` rather than `rc-db add-claim`
   - Cleaner namespace, matches common CLI patterns (git, docker)
   - Easier to extend (add new claim operations without new top-level commands)

2. **JSON output default**: Machine-readable, pipe-friendly
   - Add `--format text` for human-readable output
   - Follows modern CLI conventions (gh, kubectl)

3. **Auto-ID generation**: When `--id` not provided for claims
   - Query database for highest counter in domain
   - Generate next ID: `DOMAIN-YYYY-NNN`

4. **Import from YAML**: Support legacy registry.yaml format
   - Reuse logic from migrate.py
   - Allow incremental imports (skip existing IDs)

## Verification

After implementation:

```bash
# Run all tests
uv run pytest -v

# Test CLI manually
uv run rc-db init
uv run rc-db claim add --text "Test claim" --type "[T]" --domain "TECH" --evidence-level "E3" --credence 0.7
uv run rc-db claim list --domain TECH
uv run rc-db claim get TECH-2026-001
uv run rc-db related TECH-2026-001
uv run rc-db stats

# Test shell wrappers
./plugin/scripts/run-db.sh stats

# Test plugin commands (in Claude Code session)
# /search "test query"
# /validate
```

## Open Questions

1. **ID format for sources**: Currently free-form (e.g., "author-2026-title"). Should we enforce a pattern or keep flexible?
   - **Recommendation**: Keep flexible, users have their own conventions

2. **Interactive vs flag-based add**: Should `rc-db claim add` prompt interactively if flags missing?
   - **Recommendation**: No, keep CLI non-interactive for scriptability. Require mandatory flags.

3. **Hooks implementation**: Should we implement plugin/hooks/hooks.json in Phase 2?
   - **Recommendation**: Defer to Phase 2.5 or Phase 3. Focus on core CLI + commands first.
