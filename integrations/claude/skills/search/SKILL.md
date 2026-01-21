---
name: search
description: Semantic search across Reality Check claims and sources using natural language queries. Use when looking for related claims or finding existing analysis.
argument-hint: "QUERY [--domain DOMAIN] [--limit N] [--format json|text]"
allowed-tools: ["Bash(uv run python scripts/db.py search *)"]
---

# Reality Check Semantic Search

Search claims and sources using natural language queries.

## Usage

```!
uv run python scripts/db.py search "$ARGUMENTS"
```

## Options

- `--domain`: Filter by domain (LABOR, ECON, GOV, TECH, SOC, etc.)
- `--limit`: Maximum results to return (default: 10)
- `--format`: Output format - `json` (default) or `text`

## How It Works

1. Convert query to embedding using sentence-transformers
2. Find nearest neighbors in the claims/sources vector index
3. Return ranked results with similarity scores

## Output

Results include:
- Claim/Source ID
- Text (truncated)
- Type, Domain, Evidence Level
- Credence score
- Similarity score

## Examples

```
/rc-search "AI automation labor displacement"
/rc-search "training costs" --domain TECH --limit 5
```
