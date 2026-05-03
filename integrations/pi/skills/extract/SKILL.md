---
name: extract
description: Extract claims from a source without performing full 3-stage analysis. Use for quick claim harvesting or supporting sources.
license: Apache-2.0
compatibility: pi
metadata:
  project: realitycheck
---

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

# Quick Claim Extraction

Extract claims from a source without performing full 3-stage analysis. Use for quick claim harvesting or supporting sources.

## Usage

```
/skill:extract <source>
```

Extract claims from a source without performing full 3-stage analysis. Use for quick claim harvesting or when sources are supporting evidence rather than primary subjects.

## When to Use

- Quick extraction of claims from supporting sources
- Building cross-reference evidence for existing claims
- Initial triage before deciding on full analysis
- Sources that are data-heavy rather than argument-heavy

## Output Format

```yaml
claims:
  - id: "DOMAIN-YYYY-NNN"
    text: "[Precise claim statement]"
    type: "[F/T/H/P/A/C/S/X]"
    domain: "[DOMAIN]"
    evidence_level: "E[1-6]"
    credence: 0.XX
    source_ids: ["[source-id]"]
```

## Claim Types

| Type | Symbol | Definition |
|------|--------|------------|
| Fact | `[F]` | Empirically verified, consensus reality |
| Theory | `[T]` | Coherent explanatory framework with empirical support |
| Hypothesis | `[H]` | Testable proposition, awaiting evidence |
| Prediction | `[P]` | Future-oriented claim with specified conditions |
| Assumption | `[A]` | Underlying premise (stated or unstated) |
| Counterfactual | `[C]` | Alternative scenario for comparison |
| Speculation | `[S]` | Unfalsifiable or untestable claim |
| Contradiction | `[X]` | Identified logical inconsistency |

## Evidence Hierarchy

Use this hierarchy to rate **strength of evidential support** for claims.

| Level | Strength | Description | Credence Range |
|-------|----------|-------------|----------------|
| **E1** | Strong Empirical | Systematic review, meta-analysis, replicated experiments | 0.9-1.0 |
| **E2** | Moderate Empirical | Single peer-reviewed study, official statistics | 0.6-0.8 |
| **E3** | Strong Theoretical | Expert consensus, working papers, preprints | 0.5-0.7 |
| **E4** | Weak Theoretical | Industry reports, credible journalism | 0.3-0.5 |
| **E5** | Opinion/Forecast | Personal observation, anecdote, expert opinion | 0.2-0.4 |
| **E6** | Unsupported | Pure speculation, unfalsifiable claims | 0.0-0.2 |

## Domain Codes

| Code | Description |
|------|-------------|
| TECH | Technology, AI capabilities, tech trajectories |
| LABOR | Employment, automation, human work |
| ECON | Value theory, pricing, distribution, ownership |
| GOV | Governance, policy, regulation |
| SOC | Social structures, culture, behavior |
| RESOURCE | Scarcity, abundance, allocation |
| TRANS | Transition dynamics, pathways |
| GEO | International relations, state competition |
| INST | Institutions, organizations |
| RISK | Risk assessment, failure modes |
| META | Claims about the framework/analysis itself |

---

## Notes

- Quick extractions should be labeled with `Analysis Depth: quick` in the analysis file
- Minimum requirements: Metadata, Legends, Claim Summary table, Claims YAML
- Full Stage 2 evaluation tables (verification, counterevidence, tensions, persuasion) are optional for quick extractions
- If a source proves more significant, upgrade to full analysis with `/skill:check --continue`

---

## Web Access

This workflow may require web fetch and/or web search. Use whatever web
tools are available in your environment.

If you have **no web tools installed**, fall back to:

```bash
curl -L -sS "URL" | rc-html-extract - --format json
```

We recommend installing one of these pi web packages:

```bash
pi install npm:pi-web-access        # web search + fetch + video, zero-config (most popular)
pi install npm:pi-smart-fetch       # best content extraction, browser-like TLS
pi install npm:@the-forge-flow/camoufox-pi  # stealth browser for bot-protected pages
```

---

## Related Skills

- `/skill:check`
- `/skill:analyze`
