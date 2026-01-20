# RealityCheck Database Schema

LanceDB-backed storage for claims, sources, chains, and predictions.

## Overview

RealityCheck uses LanceDB for vector storage with semantic search capabilities. The database is stored at `data/realitycheck.lance/` by default (configurable via `ANALYSIS_DB_PATH` environment variable).

## Tables

### claims

Individual claims extracted from sources.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `[DOMAIN]-[YYYY]-[NNN]` |
| `text` | string | Yes | The claim text |
| `type` | string | Yes | Epistemic type: `[F]`/`[T]`/`[H]`/`[P]`/`[A]`/`[C]`/`[S]`/`[X]` |
| `domain` | string | Yes | Domain code (see Domains) |
| `evidence_level` | string | Yes | E1-E6 (see Evidence Hierarchy) |
| `credence` | float | Yes | 0.0-1.0 probability estimate |
| `operationalization` | string | No | How to test this claim |
| `assumptions` | list[string] | No | What must be true |
| `falsifiers` | list[string] | No | What would refute |
| `source_ids` | list[string] | No | References to sources table |
| `related_ids` | list[string] | No | Related claim IDs |
| `created_at` | string | Auto | ISO timestamp |
| `updated_at` | string | Auto | ISO timestamp |
| `embedding` | vector[384] | Auto | Sentence-transformer embedding |

### sources

Bibliography and provenance tracking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique source ID |
| `title` | string | Yes | Source title |
| `authors` | list[string] | No | Author names |
| `date` | string | No | Publication date |
| `url` | string | No | URL or DOI |
| `source_type` | string | No | paper/book/article/report/video/podcast |
| `summary` | string | No | Brief summary |
| `claim_ids` | list[string] | No | Backlinks to extracted claims |
| `created_at` | string | Auto | ISO timestamp |
| `updated_at` | string | Auto | ISO timestamp |
| `embedding` | vector[384] | Auto | Sentence-transformer embedding |

### chains

Argument chains (A → B → C → Conclusion).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `CHAIN-[YYYY]-[NNN]` |
| `name` | string | Yes | Chain name/title |
| `thesis` | string | Yes | Final conclusion |
| `claim_ids` | list[string] | Yes | Ordered list of claim IDs in chain |
| `credence` | float | Yes | MIN(step credences) |
| `weakest_link` | string | No | ID of weakest claim |
| `analysis` | string | No | Chain analysis notes |
| `created_at` | string | Auto | ISO timestamp |
| `updated_at` | string | Auto | ISO timestamp |

### predictions

Tracking for `[P]` type claims.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique prediction ID |
| `claim_id` | string | Yes | Reference to claims table |
| `status` | string | Yes | `[P+]`/`[P~]`/`[P→]`/`[P?]`/`[P←]`/`[P!]`/`[P-]`/`[P∅]` |
| `conditions` | string | No | Trigger conditions |
| `timeframe` | string | No | Resolution timeframe |
| `resolution_criteria` | string | No | How to judge outcome |
| `resolution_date` | string | No | When resolved |
| `resolution_notes` | string | No | Outcome details |
| `created_at` | string | Auto | ISO timestamp |
| `updated_at` | string | Auto | ISO timestamp |

### contradictions

Identified logical inconsistencies.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique contradiction ID |
| `claim_ids` | list[string] | Yes | Conflicting claim IDs |
| `description` | string | Yes | Nature of contradiction |
| `resolution` | string | No | How resolved (if at all) |
| `created_at` | string | Auto | ISO timestamp |

### definitions

Working definitions for key terms.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique definition ID |
| `term` | string | Yes | The term being defined |
| `definition` | string | Yes | Meaning in context |
| `operational_proxy` | string | No | How to measure/detect |
| `notes` | string | No | Ambiguities, edge cases |
| `source_ids` | list[string] | No | Where term is used |
| `created_at` | string | Auto | ISO timestamp |

## Domains

Valid domain codes:

| Code | Description |
|------|-------------|
| LABOR | Employment, automation, human work |
| ECON | Value theory, pricing, distribution, ownership |
| GOV | Governance, policy, regulation |
| TECH | Technology trajectories, capabilities |
| SOC | Social structures, culture, behavior |
| RESOURCE | Scarcity, abundance, allocation |
| TRANS | Transition dynamics, pathways |
| GEO | International relations, state competition |
| INST | Institutions, organizations |
| RISK | Risk assessment, failure modes |
| META | Claims about the framework/analysis itself |

## Evidence Levels

| Level | Description | Credence Range |
|-------|-------------|----------------|
| E1 | Strong Empirical | 0.9-1.0 |
| E2 | Moderate Empirical | 0.6-0.8 |
| E3 | Strong Theoretical | 0.5-0.7 |
| E4 | Weak Theoretical | 0.3-0.5 |
| E5 | Opinion/Forecast | 0.2-0.4 |
| E6 | Unsupported | 0.0-0.2 |

## Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified |
| Theory | `[T]` | Explanatory framework |
| Hypothesis | `[H]` | Testable proposition |
| Prediction | `[P]` | Future-oriented claim |
| Assumption | `[A]` | Underlying premise |
| Counterfactual | `[C]` | Alternative scenario |
| Speculation | `[S]` | Untestable claim |
| Contradiction | `[X]` | Logical inconsistency |

## Prediction Statuses

| Status | Symbol | Criteria |
|--------|--------|----------|
| Confirmed | `[P+]` | Occurred as specified |
| Partially Confirmed | `[P~]` | Core correct, details differ |
| On Track | `[P→]` | Intermediate indicators align |
| Uncertain | `[P?]` | Insufficient data |
| Off Track | `[P←]` | Indicators diverge |
| Partially Refuted | `[P!]` | Core problematic |
| Refuted | `[P-]` | Clearly failed |
| Unfalsifiable | `[P∅]` | Cannot be tested |

## Embeddings

All text fields are embedded using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Embeddings enable:

- Semantic search across claims/sources
- Finding related claims
- Clustering analysis

Generate embeddings with:
```bash
rc-embed generate
```

## Validation Rules

The `/validate` command checks:

1. **ID Format**: Claim IDs match `[DOMAIN]-[YYYY]-[NNN]`
2. **Referential Integrity**: All foreign keys resolve
3. **Domain Consistency**: ID domain matches `domain` field
4. **Credence Range**: Values in [0.0, 1.0]
5. **Type Values**: Only allowed type symbols
6. **Chain Credence**: Chain credence ≤ MIN(claim credences)
7. **Prediction Links**: All `[P]` claims have prediction records
