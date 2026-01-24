---
name: synthesize
description: "Create a cross-source synthesis across multiple source analyses and claims. Use after checking multiple sources or when producing a higher-level, decision-oriented view."
---

<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

# Cross-Source Synthesis (Codex)

Create a cross-source synthesis across multiple source analyses and claims. Use after checking multiple sources or when producing a higher-level, decision-oriented view.

## Invocation

```
$synthesize <topic>
```

Note: Codex reserves `/...` for built-in commands. Use `$synthesize` instead.

Create a **cross-source synthesis** across multiple source analyses and existing claims.

Use this after running `$check` on multiple sources (or when you already have relevant source analyses and want a higher-level conclusion).

## Prerequisites

### Environment

Set `REALITYCHECK_DATA` to point to your data repository:

```bash
export REALITYCHECK_DATA=/path/to/realitycheck-data/data/realitycheck.lance
```

The `PROJECT_ROOT` is derived from this path - all analysis files go there.

### Red Flags: Wrong Repository

**IMPORTANT**: Always write to the DATA repository, never to the framework repository.

If you see these directories, you're in the **framework** repo (wrong place for data):
- `scripts/`
- `tests/`
- `integrations/`
- `methodology/`

Stop and verify `REALITYCHECK_DATA` is set correctly.

### Data Source of Truth

**LanceDB is the source of truth**, not YAML files.

- Query sources: `rc-db source get <id>` or `rc-db source list`
- Query claims: `rc-db claim get <id>` or `rc-db claim list`
- Search: `rc-db search "query"`

**Ignore YAML files** like `claims/registry.yaml` or `reference/sources.yaml` - these are exports/legacy format.

## When to Use

Run synthesis when the task is inherently **multi-source**:
- compare/contrast competing approaches
- reconcile conflicting claims
- summarize the overall state of evidence on a topic
- produce a decision-oriented “what should we believe?” output

## Output Contract

Write a synthesis document to:
`PROJECT_ROOT/analysis/syntheses/<synth-id>.md`

**Required elements**:
1. **Synthesis metadata** (topic, date, synthesis ID)
2. **Claims referenced** (claim IDs)
3. **Source analysis links** for relevant sources (prefer linking `analysis/sources/<source-id>.md`)
4. **Agreement/disagreement** with explanations
5. **Synthesis conclusions** with calibrated credence and key uncertainties

**Corner case**: If you have *claims/evidence but no analyzable sources*, explicitly say so and explain why (e.g., internal notes, private sources, offline materials). Still reference claim IDs and any evidence artifacts available.

## Workflow

1. **Define the question** - What is this synthesis trying to answer?
2. **Collect inputs**
   - Prefer existing source analyses in `analysis/sources/`
   - If a relevant source has no analysis yet, run `$check` first (or document the gap)
3. **Build a cross-source map**
   - Points of agreement (which claims converge?)
   - Points of disagreement (where do they conflict, and why?)
4. **Write the synthesis**
   - Link each major claim back to source analyses (when available)
   - Resolve conflicts where possible; otherwise record open questions + what would resolve them
5. **(Optional) Register an argument chain**
   - Use `rc-db chain add ... --analysis-file "analysis/syntheses/<synth-id>.md" --claims "ID1,ID2,..."` for the central claim chain
6. **Update README**
   - Add the synthesis to the “Syntheses” table (kept **above** “Source Analyses”)
7. **Commit and push**
   - Commit changes to `analysis/` and `README.md` (and any generated exports), then push

## Minimal Template Snippet

```markdown
# Synthesis: [Topic]

## Synthesis Metadata

- **Synthesis ID**: `SYNTH-[YYYY]-[NNN]`
- **Topic**: [question or topic]
- **Date**: YYYY-MM-DD
- **Source Analyses**:
  - [source-id](../sources/source-id.md)
  - ...
- **Claims Referenced**: TECH-2026-001, ...
```


---

## Related Skills

- `$check`
- `$search`
- `$validate`
- `$export`
- `$stats`
