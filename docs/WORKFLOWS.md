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
| `db.py doctor` | Detect project root/DB and print setup guidance |
| `db.py repair` | Repair database invariants (safe/idempotent) |
| `db.py search "query"` | Semantic search across claims |
| `db.py claim add/get/list/update` | Claim CRUD operations |
| `db.py source add/get/list/update` | Source CRUD operations |
| `db.py chain add/get/list` | Chain CRUD operations |
| `db.py prediction add/list` | Prediction operations |
| `db.py analysis add/get/list` | Analysis audit log operations |
| `db.py related <claim-id>` | Find related claims |
| `db.py import <file>` | Bulk import from YAML (supports `--on-conflict`) |

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

**Note:** If `REALITYCHECK_DATA` is not set, the CLIs will try to auto-detect a data project by walking up from your current directory for `.realitycheck.yaml` or `data/realitycheck.lance/`. If nothing is detected, set `REALITYCHECK_DATA` (or pass `--db-path` where supported), or create a project via `rc-db init-project`.

You can also use `db.py doctor` to print detected project/DB paths and copy-paste setup commands.

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

Notes:
- If `--source-ids` references an existing source, the claim ID is automatically added to that source's `claims_extracted`.
- If a claim has type `[P]` and no prediction record exists yet, a stub prediction is auto-created with status `[P?]`.

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
  --url "https://epochai.org/blog/training-compute-trends" \
  --analysis-file "analysis/sources/epoch-2024-training.md" \
  --topics "ai-compute,training" \
  --domains "TECH,ECON"
```

### Update a Source

```bash
uv run python scripts/db.py source update epoch-2024-training \
  --analysis-file "analysis/sources/epoch-2024-training.md" \
  --topics "ai-compute,training,history" \
  --domains "TECH,ECON" \
  --claims-extracted "TECH-2026-001,TECH-2026-002"
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

# Safe reruns (no manual deletes)
uv run python scripts/db.py import data.yaml --type all --on-conflict skip
uv run python scripts/db.py import data.yaml --type all --on-conflict update
```

Notes:
- `--on-conflict error` is the default (fail fast).
- `--on-conflict skip` ignores existing IDs (idempotent reruns).
- `--on-conflict update` updates existing rows with incoming fields.

### Register From An Analysis YAML (Recommended)

If you have an analysis artifact like `analysis/sources/<source-id>.yaml` (the format produced by the skills), you can register the source + claims in one command:

```bash
uv run python scripts/db.py import analysis/sources/<source-id>.yaml --type all
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

If validation fails with mechanical integrity issues (e.g., `SOURCE_CLAIM_NOT_LISTED`, `SOURCE_BACKLINK_MISSING`, `PREDICTIONS_MISSING`), run:

```bash
uv run python scripts/db.py repair
```

## Analysis Audit Log Workflow

After completing an analysis (and registering the source/claims), record an audit log entry:

Notes:
- `--source-id` must already exist in the `sources` table (unless you pass `--allow-missing-source`).
- Relative `--analysis-file` paths are resolved relative to the data project root (derived from `REALITYCHECK_DATA`).

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

## Analysis Lifecycle Workflow (Token Usage Tracking)

For automated checks with accurate per-check token attribution, use the lifecycle commands:

### Start an Analysis

```bash
# Start analysis with automatic session detection (Claude Code)
ANALYSIS_ID=$(uv run python scripts/db.py analysis start \
  --source-id test-source-001 \
  --tool claude-code \
  --model claude-sonnet-4)

# Start with explicit session ID
ANALYSIS_ID=$(uv run python scripts/db.py analysis start \
  --source-id test-source-001 \
  --tool codex \
  --usage-session-id abc12345-1234-5678-9abc-def012345678)
```

This captures `tokens_baseline` from the current session token count.

### Mark Stage Checkpoints (Optional)

```bash
# After completing each stage
uv run python scripts/db.py analysis mark \
  --id "$ANALYSIS_ID" \
  --stage check_stage1

uv run python scripts/db.py analysis mark \
  --id "$ANALYSIS_ID" \
  --stage check_stage2
```

### Complete the Analysis

```bash
# Complete with automatic token capture
uv run python scripts/db.py analysis complete \
  --id "$ANALYSIS_ID" \
  --claims-extracted TECH-2026-001,TECH-2026-002

# Or with explicit final tokens
uv run python scripts/db.py analysis complete \
  --id "$ANALYSIS_ID" \
  --tokens-final 5000 \
  --estimate-cost
```

This captures `tokens_final` and computes `tokens_check = tokens_final - tokens_baseline`.

### Discover Available Sessions

```bash
# List Claude Code sessions
uv run python scripts/db.py analysis sessions list --tool claude-code

# List Codex sessions
uv run python scripts/db.py analysis sessions list --tool codex --limit 20
```

Output includes UUID, token count, and context snippet for identification.

### Backfill Historical Entries

For existing analysis logs without token data:

```bash
# Preview what would be updated
uv run python scripts/db.py analysis backfill-usage --dry-run

# Backfill Claude Code entries from 2026
uv run python scripts/db.py analysis backfill-usage \
  --tool claude-code \
  --since 2026-01-01 \
  --limit 50

# Force overwrite existing values
uv run python scripts/db.py analysis backfill-usage --force
```

## Evidence Linking Workflow

Link claims to their supporting and contradicting sources for epistemic provenance.

### Add an Evidence Link

```bash
# Basic link
uv run python scripts/db.py evidence add \
  --claim-id "TECH-2026-001" \
  --source-id "epoch-2024-training" \
  --direction supports

# Full detail
uv run python scripts/db.py evidence add \
  --claim-id "TECH-2026-001" \
  --source-id "epoch-2024-training" \
  --direction supports \
  --strength 0.8 \
  --location "Table 3, p.15" \
  --quote "Training compute has doubled every 6 months since 2012" \
  --reasoning "Direct measurement of compute growth supports the trend claim"
```

Directions: `supports`, `contradicts`, `strengthens`, `weakens`

### List Evidence for a Claim

```bash
# All evidence for a claim
uv run python scripts/db.py evidence list --claim-id "TECH-2026-001"

# Filter by direction
uv run python scripts/db.py evidence list --claim-id "TECH-2026-001" --direction supports
```

### List Evidence from a Source

```bash
uv run python scripts/db.py evidence list --source-id "epoch-2024-training"
```

### Supersede an Evidence Link

When your understanding of evidence changes:

```bash
uv run python scripts/db.py evidence supersede EVLINK-2026-001 \
  --direction weakens \
  --reasoning "Re-evaluated: methodology concerns reduce support"
```

This marks the original link as `superseded` and creates a new link with updated direction/reasoning.

## Reasoning Trails Workflow

Document why you assigned a particular credence to a claim.

### Add a Reasoning Trail

```bash
uv run python scripts/db.py reasoning add \
  --claim-id "TECH-2026-001" \
  --credence 0.75 \
  --evidence-level E2 \
  --evidence-summary "E2 based on 2 supporting sources, 1 weak counter" \
  --supporting-evidence "EVLINK-2026-001,EVLINK-2026-002" \
  --contradicting-evidence "EVLINK-2026-003" \
  --reasoning-text "Assigned 0.75 because: (1) Two independent studies confirm the trend, (2) One methodologically weak study contradicts, discounted due to small sample size"
```

### Get Active Reasoning for a Claim

```bash
# Returns only the active (non-superseded) reasoning trail
uv run python scripts/db.py reasoning get --claim-id "TECH-2026-001"

# Human-readable format
uv run python scripts/db.py reasoning get --claim-id "TECH-2026-001" --format text
```

### View Reasoning History

```bash
# All reasoning trails, including superseded
uv run python scripts/db.py reasoning history --claim-id "TECH-2026-001"
```

### When to Capture Reasoning

- **Required** for claims with credence ≥ 0.7 (validation warns if missing)
- **Required** for claims with E1/E2 evidence (high-quality evidence needs documented reasoning)
- **Recommended** for controversial or novel claims
- **Optional** for routine factual claims with obvious sourcing

## Export Provenance

### Export Reasoning Documents

```bash
# Single claim reasoning doc
uv run python scripts/export.py md reasoning --id TECH-2026-001 -o analysis/reasoning/TECH-2026-001.md

# All claims with reasoning trails
uv run python scripts/export.py md reasoning --all --output-dir analysis/reasoning
```

### Export Evidence Indexes

```bash
# Evidence for a claim
uv run python scripts/export.py md evidence-by-claim --id TECH-2026-001 -o analysis/evidence/by-claim/TECH-2026-001.md

# Evidence from a source
uv run python scripts/export.py md evidence-by-source --id epoch-2024-training -o analysis/evidence/by-source/epoch-2024-training.md
```

### Export Full Provenance

```bash
# YAML format (deterministic, git-friendly)
uv run python scripts/export.py provenance --format yaml -o provenance.yaml

# JSON format
uv run python scripts/export.py provenance --format json -o provenance.json
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

### Schema Migration

When upgrading the Reality Check framework, existing databases may need schema updates (new columns added to tables). Run the migrate command:

```bash
# Preview changes
uv run python scripts/db.py migrate --dry-run

# Apply migrations
uv run python scripts/db.py migrate
```

The migrate command:
- Compares current table schemas against expected schemas
- Adds missing columns with appropriate defaults
- Reports what was changed
- Safe to run multiple times (idempotent)

**Note**: This is for schema updates within the LanceDB format. For migrating from legacy YAML files, see below.

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
