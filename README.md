# Reality Check

A framework for rigorous, systematic analysis of claims, sources, predictions, and argument chains.

> With so many hot takes, plausible theories, misinformation, and AI-generated content, sometimes, you just need a `realitycheck`.

## Overview

Reality Check helps you build and maintain a **unified knowledge base** with:

- **Claim Registry**: Track claims with evidence levels, credence scores, and relationships
- **Source Analysis**: Structured 3-stage methodology (descriptive → evaluative → dialectical)
- **Prediction Tracking**: Monitor forecasts with falsification criteria and status updates
- **Argument Chains**: Map logical dependencies and identify weak links
- **Semantic Search**: Find related claims across your entire knowledge base

## Status

**v0.1.0-beta** - Core functionality complete. Extended CLI, Claude Code plugin with full workflow automation, and 112 passing tests.

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
  ```bash
  # Install uv (macOS/Linux)
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Or with pip
  pip install uv
  ```
- **[Claude Code](https://claude.ai/code)** (optional) - For plugin integration

## Installation

```bash
# Clone the framework
git clone https://github.com/lhl/realitycheck.git
cd realitycheck

# Install dependencies
uv sync

# Verify installation
REALITYCHECK_EMBED_SKIP=1 uv run pytest -v
```

### GPU Support (Optional)

The default install uses CPU-only PyTorch. For GPU-accelerated embeddings:

```bash
# NVIDIA CUDA 12.8
uv sync --extra-index-url https://download.pytorch.org/whl/cu128

# AMD ROCm 6.4
uv sync --extra-index-url https://download.pytorch.org/whl/rocm6.4
```

**AMD TheRock nightly (e.g., gfx1151 / Strix Halo):**

TheRock nightlies provide support for newer AMD GPUs not yet in stable ROCm. Replace `gfx1151` with your GPU arch.

> **Note:** TheRock support is experimental. Newer architectures (gfx1151/RDNA 3.5, gfx1200/RDNA 4) may require matching system ROCm kernel drivers. Memory allocation may work but kernel execution can fail if there's a version mismatch between pip ROCm userspace and system kernel module.

```bash
# 1. Install matching ROCm SDK (system-wide)
pip install --index-url https://rocm.nightlies.amd.com/v2/gfx1151/ "rocm[libraries]" -U

# 2. Create fresh venv with ROCm torch
rm -rf .venv && uv venv --python 3.12
VIRTUAL_ENV=$(pwd)/.venv uv pip install --index-url https://rocm.nightlies.amd.com/v2/gfx1151/ torch
VIRTUAL_ENV=$(pwd)/.venv uv pip install sentence-transformers lancedb pyarrow pyyaml tabulate

# 3. Set library path and verify
export LD_LIBRARY_PATH="$(pip show rocm-sdk-core | grep Location | cut -d' ' -f2)/_rocm_sdk_devel/lib:$LD_LIBRARY_PATH"
.venv/bin/python -c "import torch; print(torch.version.hip); print(torch.cuda.is_available())"
```

Or set `UV_EXTRA_INDEX_URL` in your shell profile for persistent configuration.

**Note:** If switching GPU backends, force reinstall torch:
```bash
rm -rf .venv && uv sync --extra-index-url <your-index-url>
```

## Quick Start

### 1. Create Your Knowledge Base

```bash
# Create a new directory for your data
mkdir my-research && cd my-research

# Initialize a Reality Check project (creates structure + database)
uv run python /path/to/realitycheck/scripts/db.py init-project

# This creates:
#   .realitycheck.yaml    - Project config
#   data/realitycheck.lance/  - Database
#   analysis/sources/     - For analysis documents
#   tracking/             - For prediction tracking
#   inbox/                - For sources to process
```

### 2. Set Environment Variable

```bash
# Tell Reality Check where your database is
export REALITYCHECK_DATA="data/realitycheck.lance"

# Add to your shell profile for persistence:
echo 'export REALITYCHECK_DATA="data/realitycheck.lance"' >> ~/.bashrc
```

### 3. Add Your First Claim

```bash
# From your project directory:
uv run python /path/to/realitycheck/scripts/db.py claim add \
  --text "AI training costs double annually" \
  --type "[F]" \
  --domain "TECH" \
  --evidence-level "E2" \
  --credence 0.8

# Output: Created claim: TECH-2026-001
```

### 4. Add a Source

```bash
uv run python /path/to/realitycheck/scripts/db.py source add \
  --id "epoch-2024-training" \
  --title "Training Compute Trends" \
  --type "REPORT" \
  --author "Epoch AI" \
  --year 2024 \
  --url "https://epochai.org/blog/training-compute-trends"
```

### 5. Search and Explore

```bash
# Semantic search
uv run python /path/to/realitycheck/scripts/db.py search "AI costs"

# List all claims
uv run python /path/to/realitycheck/scripts/db.py claim list --format text

# Check database stats
uv run python /path/to/realitycheck/scripts/db.py stats
```

## Using with Framework as Submodule

For easier access to scripts, add the framework as a git submodule:

```bash
cd my-research
git submodule add https://github.com/lhl/realitycheck.git .framework

# Now use shorter paths:
.framework/scripts/db.py claim list --format text
.framework/scripts/db.py search "AI"
```

## CLI Reference

All commands require `REALITYCHECK_DATA` to be set, or run from a directory with `.realitycheck.yaml`.

```bash
# Database management
db.py init                              # Initialize database tables
db.py init-project [--path DIR]         # Create new project structure
db.py stats                             # Show statistics
db.py reset                             # Reset database (destructive!)

# Claim operations
db.py claim add --text "..." --type "[F]" --domain "TECH" --evidence-level "E3"
db.py claim add --id "TECH-2026-001" --text "..." ...  # With explicit ID
db.py claim get <id>                    # Get single claim (JSON)
db.py claim list [--domain D] [--type T] [--format json|text]
db.py claim update <id> --credence 0.9 [--notes "..."]

# Source operations
db.py source add --id "..." --title "..." --type "PAPER" --author "..." --year 2024
db.py source get <id>
db.py source list [--type T] [--status S]

# Chain operations (argument chains)
db.py chain add --id "..." --name "..." --thesis "..." --claims "ID1,ID2,ID3"
db.py chain get <id>
db.py chain list

# Prediction operations
db.py prediction add --claim-id "..." --source-id "..." --status "[P→]"
db.py prediction list [--status S]

# Search and relationships
db.py search "query" [--domain D] [--limit N]
db.py related <claim-id>                # Find related claims

# Import/Export
db.py import <file.yaml> --type claims|sources|all
validate.py                             # Check database integrity
export.py yaml claims -o claims.yaml    # Export to YAML
```

## Claude Code Plugin

[Claude Code](https://claude.ai/code) is Anthropic's AI coding assistant. Reality Check includes a plugin that adds slash commands for analysis workflows.

### Install the Plugin

```bash
# From the realitycheck repo directory:
make install-plugin

# Or manually:
mkdir -p ~/.claude/plugins/local
ln -s /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck
```

Restart Claude Code to load the plugin.

### Plugin Commands

| Command | Description |
|---------|-------------|
| `/check <url>` | **Flagship** - Full analysis workflow (fetch → analyze → register → validate) |
| `/realitycheck <url>` | Alias for `/check` |
| `/analyze <source>` | Manual 3-stage analysis without auto-registration |
| `/extract <source>` | Quick claim extraction |
| `/search <query>` | Semantic search across claims |
| `/validate` | Check database integrity |
| `/export <format> <type>` | Export to YAML/Markdown |

### Example Session

```
> /check https://arxiv.org/abs/2401.00001

Claude will:
1. Fetch the paper content
2. Run 3-stage analysis (descriptive → evaluative → dialectical)
3. Extract and classify claims
4. Register source and claims in your database
5. Validate data integrity
6. Report summary with claim IDs
```

See `docs/PLUGIN.md` for full documentation.

## Taxonomy Reference

### Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified, consensus reality |
| Theory | `[T]` | Coherent framework with empirical support |
| Hypothesis | `[H]` | Testable proposition, awaiting evidence |
| Prediction | `[P]` | Future-oriented with specified conditions |
| Assumption | `[A]` | Underlying premise (stated or unstated) |
| Counterfactual | `[C]` | Alternative scenario for comparison |
| Speculation | `[S]` | Unfalsifiable or untestable claim |
| Contradiction | `[X]` | Identified logical inconsistency |

### Evidence Hierarchy

| Level | Strength | Description |
|-------|----------|-------------|
| E1 | Strong Empirical | Replicated studies, systematic reviews, meta-analyses |
| E2 | Moderate Empirical | Single peer-reviewed study, official statistics |
| E3 | Strong Theoretical | Expert consensus, working papers, preprints |
| E4 | Weak Theoretical | Industry reports, credible journalism |
| E5 | Opinion/Forecast | Personal observation, anecdote, expert opinion |
| E6 | Unsupported | Pure speculation, unfalsifiable claims |

### Domain Codes

| Domain | Code | Description |
|--------|------|-------------|
| Technology | `TECH` | AI capabilities, tech trajectories |
| Labor | `LABOR` | Employment, automation, work |
| Economics | `ECON` | Value, pricing, distribution |
| Governance | `GOV` | Policy, regulation, institutions |
| Social | `SOC` | Social structures, culture, behavior |
| Resource | `RESOURCE` | Scarcity, abundance, allocation |
| Transition | `TRANS` | Transition dynamics, pathways |
| Geopolitics | `GEO` | International relations, competition |
| Institutional | `INST` | Organizations, coordination |
| Risk | `RISK` | Risk assessment, failure modes |
| Meta | `META` | Claims about the framework itself |

## Project Structure

```
realitycheck/                 # Framework repo (this)
├── scripts/                  # Python CLI tools
│   ├── db.py                 # Database operations + CLI
│   ├── validate.py           # Data integrity checks
│   ├── export.py             # YAML/Markdown export
│   └── migrate.py            # Legacy YAML migration
├── plugin/                   # Claude Code plugin
│   ├── commands/             # Slash command definitions
│   └── scripts/              # Shell wrappers
├── methodology/              # Analysis templates
│   ├── evidence-hierarchy.md
│   ├── claim-taxonomy.md
│   └── templates/
├── tests/                    # pytest suite (112 tests)
└── docs/                     # Documentation

my-research/                  # Your data repo (separate)
├── .realitycheck.yaml        # Project config
├── data/realitycheck.lance/  # LanceDB database
├── analysis/sources/         # Analysis documents
├── tracking/                 # Prediction tracking
└── inbox/                    # Sources to process
```

## Why a Unified Knowledge Base?

Reality Check recommends **one knowledge base per user**, not per topic:

- Claims build on each other across domains (AI claims inform economics claims)
- Shared evidence hierarchy enables consistent evaluation
- Cross-domain synthesis becomes possible
- Semantic search works across your entire knowledge base

Create separate databases only for: organizational boundaries, privacy requirements, or team collaboration.

## Embedding Model

Reality Check uses `all-MiniLM-L6-v2` for semantic search embeddings. This model provides the best balance of performance and quality for CPU inference:

| Model | Dim | Load Time | Throughput | Memory |
|-------|-----|-----------|------------|--------|
| **all-MiniLM-L6-v2** | 384 | 2.9s | 7.8 q/s | 1.2 GB |
| all-mpnet-base-v2 | 768 | 3.0s | 3.3 q/s | 1.4 GB |
| granite-embedding-278m | 768 | 6.0s | 3.4 q/s | 2.5 GB |
| stella_en_400M_v5 | 1024 | 4.4s | 1.7 q/s | 2.7 GB |

The 384-dimension vectors are stored in LanceDB and used for similarity search across claims.

**Note:** Embeddings default to CPU to avoid GPU driver crashes. To use GPU:
```bash
export REALITYCHECK_EMBED_DEVICE="cuda"  # or "mps" for Apple Silicon
```

## Development

```bash
# Run tests (skip slow embedding tests)
REALITYCHECK_EMBED_SKIP=1 uv run pytest -v

# Run all tests including embeddings
uv run pytest -v

# Run with coverage
uv run pytest --cov=scripts --cov-report=term-missing
```

See [CLAUDE.md](CLAUDE.md) for development workflow and contribution guidelines.

## Documentation

- [docs/PLUGIN.md](docs/PLUGIN.md) - Claude Code plugin guide
- [docs/SCHEMA.md](docs/SCHEMA.md) - Database schema reference
- [docs/WORKFLOWS.md](docs/WORKFLOWS.md) - Common usage workflows
- [methodology/](methodology/) - Analysis methodology and templates

## License

Apache 2.0
