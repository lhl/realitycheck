---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh search *)"]
description: Search claims and sources using natural language queries
---

# /reality:search - Semantic Search

Search claims and sources using natural language queries.

## Usage

```
/reality:search <query> [--domain DOMAIN] [--limit N] [--format json|text]
```

## CLI Invocation

Run search using the shell wrapper:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" search "QUERY" [OPTIONS]
```

Or directly via the Python script:

```bash
uv run python scripts/db.py search "QUERY" [OPTIONS]
```

## Arguments

- `query`: Natural language search query

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
/reality:search "AI automation labor displacement"
/reality:search "training costs" --domain TECH --limit 5
/reality:search "wealth concentration inequality"
```

## Related Commands

- `/reality:analyze` - Full source analysis
- `/reality:extract` - Quick claim extraction
- `/reality:export` - Export search results
- `/reality:stats` - Database statistics
