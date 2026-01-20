# /search - Semantic Search

Search claims and sources using natural language queries.

## Usage

```
/search <query> [--domain DOMAIN] [--limit N]
```

## Arguments

- `query`: Natural language search query

## Options

- `--domain`: Filter by domain (LABOR, ECON, GOV, TECH, SOC, etc.)
- `--limit`: Maximum results to return (default: 10)

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
/search "AI automation labor displacement"
/search "training costs" --domain TECH --limit 5
/search "wealth concentration inequality"
```

## Related Commands

- `/analyze`: Full source analysis
- `/extract`: Quick claim extraction
- `/export`: Export search results
