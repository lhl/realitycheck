---
name: stats
description: Show Reality Check database statistics including counts for claims, sources, chains, and predictions
argument-hint: ""
allowed-tools: ["Bash(uv run python scripts/db.py stats)"]
---

# Reality Check Database Statistics

Show statistics about the Reality Check database.

Run the stats command:

```!
uv run python scripts/db.py stats
```

This displays counts for all tables:
- Claims
- Sources
- Chains
- Predictions
- Contradictions
- Definitions
