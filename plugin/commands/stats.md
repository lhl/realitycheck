---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh stats)"]
description: Show statistics about the Reality Check database
---

# /stats - Database Statistics

Show statistics about the Reality Check database.

## Usage

```
/stats
```

## Output

Displays counts for all tables:
- Claims
- Sources
- Chains
- Predictions
- Contradictions
- Definitions

## Implementation

Run the stats command:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" stats
```

Or directly:

```bash
uv run python scripts/db.py stats
```

## Related Commands

- `/validate` - Check data integrity
- `/export` - Export data to files
