# Reality Check Workflows

Common workflows for using the Reality Check framework.

## CLI Commands (v0.1.0-beta)

The `db.py` script (or `rc-db` if installed via pip) provides all database operations:

| Command | Description |
|---------|-------------|
| `db.py init` | Initialize database tables |
| `db.py init-project [--path DIR]` | Create new project with config + database |
| `db.py stats` | Show database statistics |
| `db.py reset` | Reset database (destructive!) |
| `db.py search "query"` | Semantic search across claims |
| `db.py claim add/get/list/update` | Claim CRUD operations |
| `db.py source add/get/list` | Source CRUD operations |
| `db.py chain add/get/list` | Chain CRUD operations |
| `db.py prediction add/list` | Prediction operations |
| `db.py analysis add/get/list` | Analysis audit log operations |
| `db.py related <claim-id>` | Find related claims |
| `db.py import <file>` | Bulk import from YAML |

Other scripts:
- `validate.py` - Data integrity validation
- `export.py` - Export to YAML/Markdown
- `migrate.py` - Migrate from legacy YAML
- `embed.py` - Generate/re-generate missing embeddings
- `html_extract.py` - Extract `{title, published, text}` from HTML (useful pre-processing for analysis)
- `resolve-project.sh` - Find project root and set `REALITYCHECK_DATA` env var
- `update-readme-stats.sh` - Update data repo README.md with current database statistics

## Project Setup

### Create a New Project

```bash
# From the realitycheck repo directory:
uv run python scripts/db.py init-project --path ~/my-research

# Or if you're in the target directory:
cd ~/my-research
uv run python /path/to/realitycheck/scripts/db.py init-project
```

This creates:
- `.realitycheck.yaml` - Project configuration
- `data/realitycheck.lance/` - Database
- `analysis/sources/` - Analysis documents
- `tracking/` - Prediction tracking
- `inbox/` - Sources to process

### Set Environment Variable

```bash
export REALITYCHECK_DATA="data/realitycheck.lance"

# Or in your project directory:
cd ~/my-research
export REALITYCHECK_DATA="$(pwd)/data/realitycheck.lance"
```

**Note:** If `REALITYCHECK_DATA` is not set, most commands will only work when a default database exists at `./data/realitycheck.lance/` (relative to your current directory). Otherwise, the CLI will exit with a helpful error prompting you to set `REALITYCHECK_DATA` or create a project via `rc-db init-project`.

## Claim Workflows

### Add a Claim

```bash
# With auto-generated ID (DOMAIN-YYYY-NNN)
uv run python scripts/db.py claim add \
  --text "AI training compute doubles every 6 months" \
  --type "[T]" \
  --domain "TECH" \
  --evidence-level "E2" \
  --credence 0.75 \
  --source-ids "epoch-2024-training"

# With explicit ID
uv run python scripts/db.py claim add \
  --id "TECH-2026-001" \
  --text "AI training compute doubles every 6 months" \
  --type "[T]" \
  --domain "TECH" \
  --evidence-level "E2"
```

### Get a Claim

```bash
# JSON output (default)
uv run python scripts/db.py claim get TECH-2026-001

# Human-readable text
uv run python scripts/db.py claim get TECH-2026-001 --format text
```

### List Claims

```bash
# All claims (JSON)
uv run python scripts/db.py claim list

# Filter by domain
uv run python scripts/db.py claim list --domain TECH

# Filter by type
uv run python scripts/db.py claim list --type "[P]"

# Human-readable format
uv run python scripts/db.py claim list --format text
```

### Update a Claim

```bash
# Update credence
uv run python scripts/db.py claim update TECH-2026-001 --credence 0.85

# Add notes
uv run python scripts/db.py claim update TECH-2026-001 --notes "Updated based on 2026 data"
```

## Source Workflows

### Add a Source

```bash
uv run python scripts/db.py source add \
  --id "epoch-2024-training" \
  --title "Training Compute Trends" \
  --type "REPORT" \
  --author "Epoch AI" \
  --year 2024 \
  --url "https://epochai.org/blog/training-compute-trends"
```

### List Sources

```bash
# All sources
uv run python scripts/db.py source list

# Filter by type
uv run python scripts/db.py source list --type PAPER

# Filter by analysis status
uv run python scripts/db.py source list --status ANALYZED
```

## Chain Workflows

### Add an Argument Chain

```bash
uv run python scripts/db.py chain add \
  --id "CHAIN-2026-001" \
  --name "AI Cost Deflation" \
  --thesis "Compute costs will decline faster than wages" \
  --claims "TECH-2026-001,TECH-2026-002,ECON-2026-001"
```

Note: If `--credence` is not specified, it defaults to MIN of the claims' credences.

### List Chains

```bash
uv run python scripts/db.py chain list --format text
```

## Prediction Workflows

### Add a Prediction

```bash
uv run python scripts/db.py prediction add \
  --claim-id "TECH-2026-003" \
  --source-id "epoch-2024-training" \
  --status "[P->]"
```

### List Predictions

```bash
# All predictions
uv run python scripts/db.py prediction list

# Filter by status
uv run python scripts/db.py prediction list --status "[P+]"
```

## Search Workflow

### Semantic Search

```bash
# Search claims by natural language
uv run python scripts/db.py search "AI automation labor displacement"

# Limit results
uv run python scripts/db.py search "compute costs" --limit 5
```

## Bulk Import

### Import from YAML

```bash
# Import claims
uv run python scripts/db.py import claims.yaml --type claims

# Import sources
uv run python scripts/db.py import sources.yaml --type sources

# Import everything
uv run python scripts/db.py import data.yaml --type all
```

## Validation Workflow

### Regular Validation

```bash
# Standard validation
uv run python scripts/validate.py

# Strict mode (warnings = errors)
uv run python scripts/validate.py --strict

# JSON output for automation
uv run python scripts/validate.py --json

# Validate legacy YAML files
uv run python scripts/validate.py --mode yaml --repo-root /path/to/data
```

### What Gets Checked

1. **Schema**: ID formats, field types, value ranges
2. **Referential Integrity**: All references resolve
3. **Logical Consistency**: Chain credences, prediction links
4. **Data Quality**: No empty text, embeddings present (warning)

## Analysis Audit Log Workflow

After completing an analysis (and registering the source/claims), record an audit log entry:

```bash
# Minimal (pass auto-computed)
uv run python scripts/db.py analysis add \
  --source-id test-source-001 \
  --tool codex \
  --cmd check \
  --analysis-file analysis/sources/test-source-001.md \
  --notes "Initial 3-stage analysis + registration"

# Optional: parse token usage from local session logs (usage-only; no transcript retention)
uv run python scripts/db.py analysis add \
  --source-id test-source-001 \
  --tool codex \
  --cmd check \
  --analysis-file analysis/sources/test-source-001.md \
  --model gpt-4o \
  --usage-from codex:/path/to/rollout-*.jsonl \
  --estimate-cost \
  --notes "Initial 3-stage analysis + registration"

# Optional: manual timestamps + token/cost entry (when available)
uv run python scripts/db.py analysis add \
  --source-id test-source-001 \
  --tool codex \
  --status completed \
  --started-at 2026-01-23T10:00:00Z \
  --completed-at 2026-01-23T10:08:00Z \
  --duration 480 \
  --tokens-in 2500 \
  --tokens-out 1200 \
  --total-tokens 3700 \
  --cost-usd 0.08 \
  --claims-extracted TECH-2026-001,TECH-2026-002 \
  --notes "Updated credences after disconfirming evidence search"
```

Then validate:

```bash
uv run python scripts/validate.py
```

## Export Workflow

### Export to YAML

```bash
# Export claims
uv run python scripts/export.py yaml claims -o claims.yaml

# Export sources
uv run python scripts/export.py yaml sources -o sources.yaml

# Export all
uv run python scripts/export.py yaml all -o full-export.yaml

# Export analysis logs
uv run python scripts/export.py yaml analysis-logs -o analysis-logs.yaml
```

### Export to Markdown

```bash
# Single claim
uv run python scripts/export.py md claim --id TECH-2026-001

# Argument chain
uv run python scripts/export.py md chain --id CHAIN-2026-001

# Dashboard summary
uv run python scripts/export.py md summary -o dashboard.md

# Analysis logs
uv run python scripts/export.py md analysis-logs -o analysis-logs.md
```

## Migration Workflow

### Migrate from Legacy YAML

```bash
# Dry run
uv run python scripts/migrate.py /path/to/legacy/repo --dry-run -v

# Run migration
uv run python scripts/migrate.py /path/to/legacy/repo -v

# Validate result
uv run python scripts/validate.py
```

## Claude Code Plugin

If using the Reality Check plugin with Claude Code:

### Full Analysis Workflow

```
> /check https://arxiv.org/abs/2401.00001
```

This runs:
1. Fetch source content
2. 3-stage analysis (descriptive -> evaluative -> dialectical)
3. Extract and classify claims
4. Register source and claims
5. Validate integrity
6. Report summary

### Quick Operations

```
> /rc-search AI costs
> /rc-validate
> /rc-export yaml claims
> /rc-stats
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REALITYCHECK_DATA` | `data/realitycheck.lance` | Database location (takes precedence over project detection) |
| `REALITYCHECK_AUTO_COMMIT` | `true` | Auto-commit data changes after db operations |
| `REALITYCHECK_AUTO_PUSH` | `false` | Auto-push after commit (requires AUTO_COMMIT=true) |
| `REALITYCHECK_EMBED_PROVIDER` | `local` | Embedding backend (`local` or `openai`) |
| `REALITYCHECK_EMBED_MODEL` | `all-MiniLM-L6-v2` | Embedding model (HF id for `local`, provider-specific for `openai`) |
| `REALITYCHECK_EMBED_DIM` | `384` | Vector dimension (must match model output + DB schema) |
| `REALITYCHECK_EMBED_DEVICE` | `cpu` | Device for local embeddings (`cpu`, `cuda:0`, etc) |
| `REALITYCHECK_EMBED_THREADS` | `4` | CPU thread clamp for local embeddings (sets `OMP_NUM_THREADS`, etc) |
| `REALITYCHECK_EMBED_API_BASE` | unset | OpenAI-compatible API base URL (e.g. `https://api.openai.com/v1`) |
| `REALITYCHECK_EMBED_API_KEY` | unset | API key for `openai` provider (or use `OPENAI_API_KEY`) |
| `REALITYCHECK_EMBED_SKIP` | unset | Skip embedding generation (intended for CI/tests or intentional deferral; leave unset by default) |

## Data Persistence

### Auto-Commit (Default Behavior)

The plugin automatically commits data changes after database write operations. This ensures your knowledge base is version-controlled without manual intervention.

**How it works:**
1. After any write command (`claim/source/chain/prediction add`, `update`, `import`, `init`, `reset`)
2. The PostToolUse hook detects changes in the data project (e.g., `data/`, `analysis/`, `tracking/`, `README.md`)
3. `README.md` stats are updated (if possible) before committing
4. Changes are staged and committed with an appropriate message (excludes `inbox/` by default)
5. Push is optional (disabled by default)

**Commit messages:**
- `data: add claim(s)` - After claim operations
- `data: add source(s)` - After source operations
- `data: add chain(s)` - After chain operations
- `data: add prediction(s)` - After prediction operations
- `data: import data` - After bulk imports
- `data: initialize database` - After init
- `data: reset database` - After reset

**Configuration:**
```bash
# Disable auto-commit (manual commits only)
export REALITYCHECK_AUTO_COMMIT=false

# Enable auto-push after commit
export REALITYCHECK_AUTO_PUSH=true
```

**Codex note:** Codex skills do not support Claude Code-style hooks. If you are using `$check` in Codex, you need to commit/push the data repo manually (or run the same scripts the plugin hooks call). To keep integrations in sync, treat `integrations/claude/plugin/hooks/auto-commit-data.sh` as the source of truth for auto-commit behavior.

### Separate Data Repository

The recommended setup separates the framework (this repo) from your data:

```
~/github/you/
├── realitycheck/           # Framework (cloned from github.com/lhl/realitycheck)
└── realitycheck-data/      # Your knowledge base (your own repo)
    ├── data/
    │   └── realitycheck.lance/
    ├── .realitycheck.yaml
    └── ...
```

**Setup:**
```bash
# Set REALITYCHECK_DATA to point to your data repo
export REALITYCHECK_DATA="$HOME/github/you/realitycheck-data/data/realitycheck.lance"

# Add to your shell profile for persistence
echo 'export REALITYCHECK_DATA="$HOME/github/you/realitycheck-data/data/realitycheck.lance"' >> ~/.bashrc
```

**Important:** When `REALITYCHECK_DATA` is set, it takes precedence over project detection. This ensures commands always target your intended database regardless of current working directory.

## Tips

### Credence Calibration
- Avoid clustering everything at 0.7-0.8
- Use the full range based on evidence
- Chain credence is always <= weakest link

### Claim Hygiene
- Always specify operationalization
- Surface hidden assumptions
- Define specific falsifiers

### Efficient Search
- Generate embeddings before searching
- Semantic search finds conceptually related claims
- Use validation to catch data issues early
