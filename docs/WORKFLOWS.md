# RealityCheck Workflows

Common workflows for using the RealityCheck framework.

## Current CLI Commands (v0.1.0-alpha)

The following commands are implemented:

| Command | Subcommands | Description |
|---------|-------------|-------------|
| `rc-db` | `init`, `stats`, `reset`, `search` | Database operations |
| `rc-validate` | (none) | Data integrity validation |
| `rc-export` | `yaml`, `md` | Export to YAML/Markdown |
| `rc-migrate` | (none) | Migrate from legacy YAML |
| `rc-embed` | `status`, `generate`, `regenerate` | Embedding management |

## Quick Start

### Initialize Database

```bash
# Create empty database
uv run rc-db init

# Verify
uv run rc-validate
```

### Check Database Status

```bash
# Show table counts and stats
uv run rc-db stats
```

### Migrate from Legacy YAML

```bash
# Dry run to see what will be migrated
uv run rc-migrate /path/to/legacy/repo --dry-run -v

# Run migration
uv run rc-migrate /path/to/legacy/repo -v

# Validate result
uv run rc-validate
```

## Search Workflow

### Semantic Search

```bash
# Search claims by natural language query
uv run rc-db search "AI automation labor displacement"

# Search returns ranked results with similarity scores
```

## Embedding Workflow

### Check Embedding Status

```bash
# See how many records have embeddings
uv run rc-embed status
```

### Generate Embeddings

```bash
# Generate embeddings for records missing them
uv run rc-embed generate

# Regenerate ALL embeddings (useful after model change)
uv run rc-embed regenerate
```

## Export Workflow

### Export to YAML (Legacy Format)

```bash
# Export claims
uv run rc-export yaml claims -o claims.yaml

# Export sources
uv run rc-export yaml sources -o sources.yaml

# Export all
uv run rc-export yaml all -o data/
```

### Export to Markdown

```bash
# Single claim
uv run rc-export md claim --id TECH-2026-001

# Argument chain
uv run rc-export md chain --id CHAIN-2026-001

# All predictions
uv run rc-export md predictions -o predictions.md

# Dashboard summary
uv run rc-export md summary -o dashboard.md
```

## Validation Workflow

### Regular Validation

```bash
# Standard validation
uv run rc-validate

# Strict mode (warnings = errors)
uv run rc-validate --strict

# JSON output for automation
uv run rc-validate --json
```

### What Gets Checked

1. **Schema**: ID formats, field types, value ranges
2. **Referential Integrity**: All references resolve
3. **Logical Consistency**: Chain credences, prediction links
4. **Data Quality**: No empty text, embeddings present (warning)

## Database Reset

```bash
# Drop all tables and reinitialize (destructive!)
uv run rc-db reset
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANALYSIS_DB_PATH` | `data/realitycheck.lance` | Database location |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model |
| `SKIP_EMBEDDING_TESTS` | unset | Skip embedding tests in pytest |

## Programmatic Access

For operations not exposed via CLI, use Python directly:

```python
from scripts.db import get_db, init_tables, add_claim, get_claim, search_claims

# Connect to database
db = get_db()
tables = init_tables(db)

# Add a claim (see scripts/db.py for full API)
claim_data = {
    "id": "TECH-2026-001",
    "text": "Example claim text",
    "type": "[T]",
    "domain": "TECH",
    "evidence_level": "E3",
    "credence": 0.65,
    "source_ids": ["source-001"],
    "first_extracted": "2026-01-20",
    "extracted_by": "manual",
    "version": 1,
    "last_updated": "2026-01-20",
}
add_claim(claim_data, db=db)

# Search
results = search_claims("automation", limit=10, db=db)
```

## Tips

### Credence Calibration
- Avoid clustering everything at 0.7-0.8
- Use the full range based on evidence
- Chain credence is always ≤ weakest link

### Claim Hygiene
- Always specify operationalization
- Surface hidden assumptions
- Define specific falsifiers

### Efficient Search
- Generate embeddings before searching
- Semantic search finds conceptually related claims
- Use validation to catch data issues early

---

## Planned Features (Phase 2)

The following CLI commands are planned but not yet implemented:

- `rc-db add claim|source|chain|prediction` - Add records via CLI
- `rc-db get <id>` - Retrieve single record
- `rc-db list claims|sources|chains` - List records with filters
- `rc-db update <id>` - Update existing record
- `rc-db related <claim-id>` - Find related claims
- `rc-db import <file>` - Bulk import from YAML

Until these are implemented, use programmatic access (see above) or the migration tool for bulk operations.
