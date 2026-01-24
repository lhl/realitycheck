---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh stats)"]
description: Show statistics about the Reality Check database
---

# /reality:stats - Database Statistics

Show statistics about the Reality Check database.

## Usage

```
/reality:stats
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

- `/reality:validate` - Check data integrity
- `/reality:export` - Export data to files
