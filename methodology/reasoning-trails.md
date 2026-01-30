# Reasoning Trails: Epistemic Provenance for Credence Assignments

## Why Provenance Matters

Reality Check assigns credence values (0.0-1.0) to claims, but a number alone doesn't explain *why* we believe something to that degree. Reasoning trails capture:

1. **The evidence balance** - Which sources support or contradict the claim
2. **The reasoning chain** - How evidence was weighted and interpreted
3. **Considered alternatives** - Counterarguments and why they were integrated, discounted, or remain unresolved
4. **Assumptions made** - Explicit dependencies that could change the credence

This transforms credence from an opaque number into an auditable, revisable judgment.

## The Minimum Provenance Contract

For high-credence claims (≥ 0.7) or claims with strong evidence (E1/E2), Reality Check expects:

1. **At least one evidence link** connecting the claim to a source
2. **A reasoning trail** documenting why the credence was assigned

Validation will warn if these are missing. With `--strict`, warnings become errors.

## Evidence Links

Evidence links connect claims to sources with explicit directionality:

| Direction | Meaning |
|-----------|---------|
| `supports` | Source provides positive evidence for the claim |
| `contradicts` | Source provides evidence against the claim |
| `strengthens` | Source increases credence but isn't decisive |
| `weakens` | Source decreases credence but isn't decisive |

### Quality Fields (Recommended)

- **location**: Where in the source? (e.g., "Table 3, p.15", "Section 4.2")
- **quote**: Relevant excerpt (for easy verification)
- **reasoning**: Why this evidence matters for this claim
- **strength**: Coarse impact estimate (0.0-1.0)

### Versioning

Evidence links can be superseded when understanding changes:

```bash
rc-db evidence supersede EVLINK-2026-001 \
  --direction weakens \
  --reasoning "Re-evaluated after methodology review"
```

This creates a new link with updated direction/reasoning while preserving the original for audit.

## Reasoning Trails

A reasoning trail documents the full chain of reasoning for a credence assignment:

### Required Fields

- **credence_at_time**: The credence being explained
- **evidence_level_at_time**: The evidence level (E1-E6)
- **reasoning_text**: A publishable rationale

### Recommended Fields

- **evidence_summary**: Brief summary of evidence balance
- **supporting_evidence**: List of evidence link IDs
- **contradicting_evidence**: List of evidence link IDs
- **assumptions_made**: Explicit dependencies
- **counterarguments_json**: Structured counterargument tracking

### Writing Good `reasoning_text`

The `reasoning_text` field should be a clear, human-readable explanation that could stand alone in a published document. Guidelines:

1. **Start with the conclusion**: "Assigned 0.75 because..."
2. **Cite the evidence**: Reference specific sources and what they show
3. **Address counterevidence**: Explain why contradicting evidence was weighted lower
4. **Acknowledge uncertainty**: Note what could change the assessment

**Good example:**
```
Assigned 0.75 because: (1) Two independent studies (Epoch 2024, Stanford 2023)
directly measured compute growth and found consistent 6-month doubling;
(2) One study (MIT 2022) claims slower growth but uses pre-2020 data only,
discounted due to sample period; (3) Uncertainty from potential measurement
definition differences across studies.
```

**Poor example:**
```
Seems about right based on the evidence.
```

### Counterarguments Format

The `counterarguments_json` field tracks how counterarguments were handled:

```json
[
  {
    "text": "Compute growth may have slowed since 2023",
    "disposition": "integrated",
    "response": "Incorporated by widening uncertainty bounds on the trend"
  },
  {
    "text": "Algorithmic efficiency gains may substitute for compute",
    "disposition": "unresolved",
    "response": "Valid concern; claim is specifically about compute, not capability"
  }
]
```

Dispositions:
- **integrated**: Incorporated into the reasoning (credence adjusted or bounds widened)
- **discounted**: Considered but rejected (explain why)
- **unresolved**: Valid concern that remains open

## When to Update Provenance

Reasoning trails should be updated (superseded) when:

1. **New evidence emerges** that changes the balance
2. **Old evidence is reevaluated** (e.g., methodology concerns)
3. **Credence changes significantly** (> 0.1 delta)
4. **Assumptions are invalidated** by new information

Use `rc-db reasoning supersede` to create a new trail while preserving history.

## Workflow Integration

In the `/check` workflow, provenance capture happens after claim registration:

1. Extract claims → Register claims
2. **Link evidence** → Connect each claim to sources (supports/contradicts)
3. **Capture reasoning** → Document why credence was assigned
4. Validate → Ensure provenance meets minimum contract

For routine analyses with many claims, focus provenance on:
- High-credence claims (≥ 0.7)
- Claims with strong evidence (E1/E2)
- Novel or controversial claims
- Claims that may inform decisions

## Rendering Provenance

Export provenance for human review:

```bash
# Per-claim reasoning docs
rc-export md reasoning --all --output-dir analysis/reasoning

# Full provenance for archival
rc-export provenance --format yaml -o provenance.yaml
```

The rendered reasoning docs include:
- Evidence table (all linked sources)
- Counterarguments considered
- Trail history (how reasoning evolved)
- Portable YAML block (for reimport)

## Design Philosophy

Reality Check's provenance system follows several principles:

1. **Explicit over implicit**: Extraction from a source ≠ support. Evidence links must be explicitly created.

2. **Versioned not mutable**: Supersession creates new records rather than editing old ones, preserving the audit trail.

3. **Soft enforcement**: Provenance is encouraged (warnings) not required (errors) by default. Use `--strict` for stricter enforcement.

4. **Human-readable output**: Reasoning trails are designed to be publishable, not just machine-readable.

5. **On-demand rendering**: Provenance docs are exported when needed, not auto-generated on every change.
