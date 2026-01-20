# RealityCheck

A framework for rigorous, systematic analysis of claims, sources, predictions, and argument chains.

## Status

**v0.1.0-alpha** - Core functionality implemented. Python scripts, tests, Claude Code plugin, and methodology templates are complete. Ready for testing.

See `docs/IMPLEMENTATION.md` for detailed progress tracking.

## Overview

RealityCheck helps you build and maintain a **unified knowledge base** with:

- **Claim Registry**: Track individual claims with evidence levels, confidence scores, and relationships
- **Source Analysis**: Structured methodology for evaluating sources (3-stage: descriptive → evaluative → dialectical)
- **Prediction Tracking**: Monitor forecasts with falsification criteria and status updates
- **Argument Chains**: Map logical dependencies and identify weak links
- **Semantic Search**: Find related claims across your entire knowledge base

## Why Unified?

RealityCheck recommends a **single knowledge base per user** rather than topic-based separation:

- Claims build on each other across topics (AI claims inform economics claims)
- Shared evidence hierarchy enables consistent evaluation
- Cross-domain synthesis becomes possible
- Semantic search works across your entire knowledge base
- Avoids siloed thinking

Separate databases only for: org boundaries, privacy requirements, or collaboration needs.

## Installation

### Using uv (Recommended)

```bash
# Clone and install
git clone https://github.com/lhl/realitycheck.git
cd realitycheck
uv sync

# Verify installation
uv run pytest -v
```

### Using pip (Coming Soon)

```bash
pip install realitycheck
```

## Quick Start

### Initialize a Knowledge Base

```bash
# Initialize database (creates data/realitycheck.lance/)
uv run rc-db init

# Check database stats
uv run rc-db stats
```

### Basic Operations

```bash
# Search claims semantically
uv run rc-db search "automation and labor"

# Run validation
uv run rc-validate

# Export to YAML
uv run rc-export yaml claims -o claims.yaml

# Generate embeddings for semantic search
uv run rc-embed generate
```

### Migrate from Legacy YAML

```bash
# Dry run first
uv run rc-migrate /path/to/legacy/repo --dry-run -v

# Run migration
uv run rc-migrate /path/to/legacy/repo -v
```

## Project Structure

```
realitycheck/
├── scripts/              # Core Python CLI tools
│   ├── db.py             # LanceDB operations (rc-db)
│   ├── validate.py       # Data integrity validation (rc-validate)
│   ├── export.py         # Export to YAML/Markdown (rc-export)
│   ├── migrate.py        # YAML → LanceDB migration (rc-migrate)
│   └── embed.py          # Embedding generation (rc-embed)
│
├── tests/                # pytest test suite (108 tests)
│
├── plugin/               # Claude Code plugin
│   ├── .claude-plugin/   # Plugin manifest
│   └── commands/         # Slash command definitions
│
├── methodology/          # Analysis methodology
│   ├── evidence-hierarchy.md
│   ├── claim-taxonomy.md
│   └── templates/        # source-analysis.md, claim-extraction.md, synthesis.md
│
└── docs/                 # Development documentation
    ├── SCHEMA.md         # Database schema
    ├── WORKFLOWS.md      # Usage workflows
    ├── PLUGIN.md         # Plugin documentation
    ├── PLAN-separation.md
    └── IMPLEMENTATION.md
```

## Claude Code Plugin

RealityCheck includes a Claude Code plugin for workflow automation:

```bash
# Install plugin (symlink for development)
ln -s /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck
```

Available commands:
- `/analyze <source>` - Full 3-stage source analysis
- `/extract <source>` - Quick claim extraction
- `/search <query>` - Semantic search across claims
- `/validate` - Check data integrity
- `/export <format> <type>` - Export to YAML/Markdown

See `docs/PLUGIN.md` for full documentation.

## Data Projects

Your analysis data lives in a separate repository:

```bash
# Create your knowledge base
mkdir realitycheck-data && cd realitycheck-data
git init

# Add framework as submodule (optional)
git submodule add https://github.com/lhl/realitycheck.git .framework

# Configure
cat > .realitycheck.yaml << 'EOF'
version: "1.0"
database:
  path: "data/realitycheck.lance"
EOF

# Initialize
export ANALYSIS_DB_PATH="data/realitycheck.lance"
python .framework/scripts/db.py init
```

## Evidence Hierarchy

Claims are rated by strength of evidential support:

| Level | Strength | Description |
|-------|----------|-------------|
| E1 | Strong Empirical | Replicated studies, verified data |
| E2 | Moderate Empirical | Single studies, case studies |
| E3 | Strong Theoretical | Logical from established principles |
| E4 | Weak Theoretical | Plausible extrapolation |
| E5 | Opinion/Forecast | Credentialed speculation |
| E6 | Unsupported | Assertions without evidence |

## Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified |
| Theory | `[T]` | Coherent framework with support |
| Hypothesis | `[H]` | Testable proposition |
| Prediction | `[P]` | Future-oriented with conditions |
| Assumption | `[A]` | Underlying premise |
| Speculation | `[S]` | Unfalsifiable claim |

## Development

```bash
# Run tests (91 pass, 17 skipped for embeddings)
uv run pytest -v

# Run with coverage
uv run pytest --cov=scripts --cov-report=term-missing

# Skip embedding tests (faster, no torch download)
SKIP_EMBEDDING_TESTS=1 uv run pytest -v

# Run specific test file
uv run pytest tests/test_db.py
```

See [CLAUDE.md](CLAUDE.md) for development workflow and conventions.
See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Documentation

- [SCHEMA.md](docs/SCHEMA.md) - Database schema reference
- [WORKFLOWS.md](docs/WORKFLOWS.md) - Common usage workflows
- [PLUGIN.md](docs/PLUGIN.md) - Claude Code plugin guide
- [methodology/](methodology/) - Analysis methodology and templates

## License

MIT
