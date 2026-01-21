# Reality Check Database Schema

LanceDB-backed storage for claims, sources, chains, predictions, contradictions, and definitions.

## Overview

Reality Check uses LanceDB for vector storage with semantic search capabilities. The database is stored at `data/realitycheck.lance/` by default (configurable via `REALITYCHECK_DATA` environment variable).

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
| `credence` | float32 | Yes | 0.0-1.0 probability estimate |
| `operationalization` | string | No | How to test this claim |
| `assumptions` | list[string] | No | What must be true |
| `falsifiers` | list[string] | No | What would refute |
| `source_ids` | list[string] | Yes | References to sources table |
| `first_extracted` | string | Yes | ISO date of first extraction |
| `extracted_by` | string | Yes | Who/what extracted this claim |
| `supports` | list[string] | No | Claim IDs this supports |
| `contradicts` | list[string] | No | Claim IDs this contradicts |
| `depends_on` | list[string] | No | Claim IDs this depends on |
| `modified_by` | list[string] | No | Claim IDs that modify this |
| `part_of_chain` | string | No | Chain ID if part of argument chain |
| `version` | int32 | Yes | Version number for updates |
| `last_updated` | string | Yes | ISO timestamp of last update |
| `notes` | string | No | Additional notes |
| `embedding` | vector[384] | No | Sentence-transformer embedding |

### sources

Bibliography and provenance tracking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique source ID |
| `type` | string | Yes | PAPER/BOOK/REPORT/ARTICLE/BLOG/SOCIAL/CONVO/KNOWLEDGE |
| `title` | string | Yes | Source title |
| `author` | list[string] | Yes | Author names |
| `year` | int32 | Yes | Publication year |
| `url` | string | No | URL |
| `doi` | string | No | DOI identifier |
| `accessed` | string | No | Date accessed |
| `reliability` | float32 | No | 0.0-1.0 source reliability rating |
| `bias_notes` | string | No | Notes on potential biases |
| `claims_extracted` | list[string] | No | Backlinks to extracted claims |
| `analysis_file` | string | No | Path to analysis document |
| `topics` | list[string] | No | Topic tags |
| `domains` | list[string] | No | Domain codes |
| `status` | string | No | cataloged/analyzed/etc. |
| `embedding` | vector[384] | No | Sentence-transformer embedding |

### chains

Argument chains (A → B → C → Conclusion).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `CHAIN-[YYYY]-[NNN]` |
| `name` | string | Yes | Chain name/title |
| `thesis` | string | Yes | Final conclusion |
| `credence` | float32 | Yes | MIN(step credences) |
| `claims` | list[string] | Yes | Ordered list of claim IDs in chain |
| `analysis_file` | string | No | Path to analysis document |
| `weakest_link` | string | No | ID of weakest claim |
| `scoring_method` | string | No | MIN/RANGE/CUSTOM |
| `embedding` | vector[384] | No | Sentence-transformer embedding |

### predictions

Tracking for `[P]` type claims.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim_id` | string | Yes | Reference to claims table |
| `source_id` | string | Yes | Reference to sources table |
| `date_made` | string | No | When prediction was made |
| `target_date` | string | No | When prediction should resolve |
| `falsification_criteria` | string | No | What would falsify |
| `verification_criteria` | string | No | What would verify |
| `status` | string | Yes | `[P+]`/`[P~]`/`[P→]`/`[P?]`/`[P←]`/`[P!]`/`[P-]`/`[P∅]` |
| `last_evaluated` | string | No | Last evaluation date |
| `evidence_updates` | string | No | JSON-encoded list of updates |

### contradictions

Identified logical inconsistencies.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique contradiction ID |
| `claim_a` | string | Yes | First conflicting claim ID |
| `claim_b` | string | Yes | Second conflicting claim ID |
| `conflict_type` | string | No | direct/scope/definition/timescale |
| `likely_cause` | string | No | Why they conflict |
| `resolution_path` | string | No | How to resolve |
| `status` | string | No | open/resolved |

### definitions

Working definitions for key terms.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `term` | string | Yes | The term being defined |
| `definition` | string | Yes | Meaning in context |
| `operational_proxy` | string | No | How to measure/detect |
| `notes` | string | No | Ambiguities, edge cases |
| `domain` | string | No | Domain this definition applies to |
| `analysis_id` | string | No | Source analysis where defined |

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

### Domain Migration

Legacy domains are automatically migrated:
- `VALUE` → `ECON`
- `DIST` → `ECON`
- `SOCIAL` → `SOC`

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

## Source Types

| Type | Description |
|------|-------------|
| PAPER | Academic paper |
| BOOK | Book or book chapter |
| REPORT | Industry/org report |
| ARTICLE | News or magazine article |
| BLOG | Blog post |
| SOCIAL | Social media post |
| CONVO | Conversation or interview |
| KNOWLEDGE | General knowledge/common understanding |

## Embeddings

All text fields can be embedded using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Embeddings enable:

- Semantic search across claims/sources
- Finding related claims
- Clustering analysis

Generate embeddings with:
```bash
uv run rc-embed generate
```

## Validation Rules

The `rc-validate` command checks:

1. **ID Format**: Claim IDs match `[DOMAIN]-[YYYY]-[NNN]`
2. **Referential Integrity**: All foreign keys resolve
3. **Domain Consistency**: ID domain matches `domain` field
4. **Credence Range**: Values in [0.0, 1.0]
5. **Type Values**: Only allowed type symbols
6. **Chain Credence**: Chain credence ≤ MIN(claim credences)
7. **Prediction Links**: All `[P]` claims have prediction records
