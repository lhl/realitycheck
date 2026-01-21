---
name: realitycheck-search
description: Semantic search across Reality Check claims and sources. Use when looking for related claims, finding existing analysis, or searching the knowledge base.
---

# Reality Check - Semantic Search

Search claims and sources using natural language queries.

## When This Skill Activates

- "Search for claims about AI automation"
- "Find related claims"
- "What do we have on labor displacement?"
- "Search the knowledge base for..."

## Prerequisites

- `realitycheck` package installed (`pip install realitycheck`)
- `REALITYCHECK_DATA` environment variable set

## Usage

```bash
rc-db search "your query here"
rc-db search "AI automation" --limit 5
rc-db search "labor market" --domain LABOR
```

## Options

| Option | Description |
|--------|-------------|
| `--limit N` | Maximum results (default: 10) |
| `--domain DOMAIN` | Filter by domain |
| `--format json\|text` | Output format |

## Domain Codes

| Code | Description |
|------|-------------|
| TECH | Technology, AI, capabilities |
| LABOR | Employment, automation, work |
| ECON | Value theory, pricing, distribution |
| GOV | Governance, policy, regulation |
| SOC | Social structures, culture |
| RESOURCE | Scarcity, abundance |
| TRANS | Transition dynamics |
| GEO | International relations |
| INST | Institutions, organizations |
| RISK | Risk assessment, failure modes |
| META | Meta-analysis claims |

## How It Works

1. Converts query to embedding (sentence-transformers)
2. Finds nearest neighbors in vector index
3. Returns ranked results with similarity scores

## Output

Results include:
- Claim/Source ID
- Text (truncated)
- Type, Domain, Evidence Level
- Credence score
- Similarity score

## Examples

```bash
# General search
rc-db search "training costs scaling laws"

# Domain-filtered
rc-db search "job displacement" --domain LABOR --limit 5

# JSON output for programmatic use
rc-db search "economic transition" --format json
```
