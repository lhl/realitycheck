---
name: realitycheck-stats
description: Shows Reality Check database statistics - counts for claims, sources, chains, predictions. Use when asked about database status or counts.
---

# Reality Check - Database Statistics

Show statistics about the Reality Check database.

## When This Skill Activates

- "Show database stats"
- "How many claims do we have?"
- "What's in the knowledge base?"
- "Database status"

## Prerequisites

- `realitycheck` package installed (`pip install realitycheck`)
- `REALITYCHECK_DATA` environment variable set

## Usage

```bash
rc-db stats
```

## Output

Displays counts for all tables:

- **Claims** - Total claims in database
- **Sources** - Analyzed sources
- **Chains** - Argument chains
- **Predictions** - Prediction tracking records
- **Contradictions** - Identified contradictions
- **Definitions** - Term definitions

## Example Output

```
Reality Check Database Statistics
=================================
Claims:        85
Sources:       43
Chains:         3
Predictions:   12
Contradictions: 2
Definitions:    8
```

## Related Commands

```bash
# List claims by domain
rc-db claim list --domain TECH

# List sources by type
rc-db source list --type PAPER

# Search for specific content
rc-db search "AI capabilities"
```
