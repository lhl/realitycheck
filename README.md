# RealityCheck

A framework for rigorous, systematic analysis of claims, sources, predictions, and argument chains.

## Status

This repository is currently in scaffold/planning stage (docs-only). See `docs/IMPLEMENTATION.md` for the punchlist and progress log.

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

Phase 1 ports scripts/tests from the legacy `analysis-framework` repo and moves dependency management to `pyproject.toml` (uv-managed). Until that lands, there is nothing runnable here yet.

## Quick Start

### Initialize a Knowledge Base

```bash
# Create data directory
mkdir -p data

# Initialize database
export ANALYSIS_DB_PATH="data/realitycheck.lance"
python scripts/db.py init
```

### Basic Operations

```bash
# Check database stats
python scripts/db.py stats

# Search claims semantically
python scripts/db.py search "automation and labor"

# Run validation
python scripts/validate.py

# Export to YAML
python scripts/export.py claims-yaml > claims/registry.yaml
```

## Project Structure

Target structure (in progress):

```
realitycheck/
├── scripts/              # Core Python CLI tools
│   ├── db.py             # LanceDB operations
│   ├── validate.py       # Data integrity validation
│   ├── export.py         # Export to YAML/Markdown
│   └── migrate.py        # YAML → LanceDB migration
│
├── tests/                # pytest test suite
│
├── plugin/               # Claude Code plugin
│   ├── commands/         # Slash command definitions
│   └── scripts/          # Shell wrappers
│
├── methodology/          # Analysis methodology
│   ├── evidence-hierarchy.md
│   ├── claim-taxonomy.md
│   └── templates/
│
└── docs/                 # Development documentation
    ├── PLAN-separation.md
    └── IMPLEMENTATION.md
```

## Claude Code Plugin

RealityCheck will include a Claude Code plugin for workflow automation:

```bash
# Install plugin (symlink for development)
ln -s /path/to/realitycheck/plugin ~/.claude/plugins/local/realitycheck
```

Available commands:
- `/analyze <source>` - Full 3-stage source analysis
- `/claim add|search` - Manage claims
- `/validate` - Check data integrity
- `/export` - Export to YAML/Markdown
- `/init` - Initialize new project

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
# Run tests
pytest -v

# Run with coverage
pytest --cov=scripts

# Skip embedding tests (if torch issues)
SKIP_EMBEDDING_TESTS=1 pytest
```

See [AGENTS.md](AGENTS.md) for development workflow and conventions.

## License

MIT
