<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

---
name: search
description: "Search claims and sources using natural language queries. Use when looking for related claims or finding existing analysis."
---

# Semantic Search (Codex)

Search claims and sources using natural language queries. Use when looking for related claims or finding existing analysis.

## Invocation

```
$search <query>
```

Note: Codex reserves `/...` for built-in commands. Use `$search` instead.

Search claims and sources using natural language queries.

## Usage

```bash
rc-db search "query" --limit 10
# or: uv run python scripts/db.py search "query" --limit 10
```

## Options

- `--domain`: Filter by domain (TECH/LABOR/ECON/GOV/SOC/RESOURCE/TRANS/GEO/INST/RISK/META)
- `--limit`: Maximum results to return (default: 10)
- `--format`: Output format - `json` (default) or `text`
- `--type`: Filter by record type (`claim` or `source`)

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

```bash
rc-db search "AI automation labor displacement"
rc-db search "training costs" --domain TECH --limit 5
rc-db search "economic transition" --type claim
```

---

## Related Skills

- `$stats`
- `$validate`
