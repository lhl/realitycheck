# Inbox and Source Pipeline Management

**Status**: Planning
**Created**: 2026-01-22

## Problem Statement

Currently there's no structured way to:
1. Queue sources for future analysis
2. Track sources through the analysis pipeline
3. Flag existing analyses for re-evaluation or synthesis
4. Collect multiple sources on a topic before synthesis

The original `postsingularity-economic-theories/AGENTS.md` had an inbox system using symlinks. We need something similar for the data repo.

## Proposed Structure

```
realitycheck-data/
├── inbox/
│   ├── to-analyze/        # URLs/references queued for analysis
│   │   ├── tech-2026-01.md
│   │   └── labor-readings.md
│   ├── in-progress/       # Currently being worked on (optional tracking)
│   ├── needs-update/      # Existing analyses flagged for re-evaluation
│   │   └── stross-2025-the-pivot-1.md -> ../analysis/sources/...
│   └── synthesis/         # Collections of sources for synthesis passes
│       └── ai-productivity-evidence.md
├── analysis/
│   ├── sources/           # Individual source analyses
│   └── syntheses/         # Cross-source synthesis documents
└── ...
```

## Inbox Item Formats

### to-analyze/ - Queued Sources

Simple markdown files containing URLs and context:

```markdown
# Tech Sources - January 2026

## Priority 1

- https://example.com/article-1
  - Why: Contradicts TECH-2026-001
  - Domain: TECH
  - Added: 2026-01-22

- https://example.com/article-2
  - Why: Primary source for training cost claims
  - Domain: TECH
  - Added: 2026-01-22

## Priority 2

- https://example.com/lower-priority
  - Why: Background context
```

Or single-source files:

```markdown
# Source: [Title or URL]

**URL**: https://example.com/article
**Added**: 2026-01-22
**Priority**: high | medium | low
**Domain**: TECH
**Why**: [Why this source matters]

## Context

[Any notes, related claims, why this is relevant]

## Related Claims

- TECH-2026-001 (may contradict)
- LABOR-2026-005 (may support)
```

### needs-update/ - Flagged Analyses

Symlinks to existing analyses with optional `.reason.md` files:

```
needs-update/
├── stross-2025-the-pivot-1.md -> ../../analysis/sources/stross-2025-the-pivot-1.md
├── stross-2025-the-pivot-1.reason.md  # Optional: why it needs update
└── openai-value-intelligence.md -> ../../analysis/sources/openai-value-intelligence.md
```

Reason file format:
```markdown
# Update Needed: stross-2025-the-pivot-1

**Flagged**: 2026-01-22
**Reason**: Missing Stage 2 evaluation tables (quality regression)
**Action**: Run `/check stross-2025-the-pivot-1 --continue`
```

### synthesis/ - Multi-Source Collections

For collecting sources before a synthesis pass:

```markdown
# Synthesis Collection: AI Productivity Evidence

**Goal**: Synthesize empirical evidence on AI-assisted coding productivity
**Status**: collecting | ready | in-progress | complete
**Created**: 2026-01-22

## Sources to Include

### Already Analyzed
- [x] peng-2023-copilot-productivity - RCT showing 55.8% speedup
- [x] chatterjee-2024-anz-copilot-study - Org A/B showing 42% speedup

### To Analyze First
- [ ] https://arxiv.org/abs/... - Another RCT on AI coding
- [ ] https://... - Industry survey

### Related Claims
- LABOR-2023-001: Copilot reduces time-to-complete by 55.8%
- LABOR-2024-001: ANZ Copilot users 42.36% faster
- LABOR-2023-002: Heterogeneous effects (experience level)

## Synthesis Questions

1. What's the range of effect sizes across studies?
2. What moderates the effect (task type, experience, domain)?
3. What's the quality gradient of evidence?
4. What are the gaps / what would change our mind?

## Output Target

- `analysis/syntheses/ai-coding-productivity-evidence.md`
- Update claims: may create LABOR-2026-XXX synthesis claim
```

## Workflow Commands

### Add to Inbox

```bash
# Quick add (creates minimal entry)
/inbox add <url> [--domain DOMAIN] [--priority high|medium|low] [--why "reason"]

# Add to synthesis collection
/inbox collect <url> --synthesis "ai-productivity-evidence"
```

### Process Inbox

```bash
# List inbox items
/inbox list [--to-analyze] [--needs-update] [--synthesis]

# Process next item
/inbox next [--domain DOMAIN]

# Mark as in-progress
/inbox start <item>

# Mark as done (removes from inbox)
/inbox done <item>
```

### Flag for Update

```bash
# Flag existing analysis for re-evaluation
/inbox flag <source-id> --reason "reason text"
```

### Synthesis Workflow

```bash
# Create synthesis collection
/inbox synthesis new "AI Productivity Evidence" --goal "Synthesize empirical evidence..."

# Add sources to collection
/inbox synthesis add "ai-productivity-evidence" <source-id-or-url>

# Mark collection ready for synthesis
/inbox synthesis ready "ai-productivity-evidence"

# Generate synthesis
/synthesize "ai-productivity-evidence"
```

## Integration with /check

When running `/check`:
1. If source was in `to-analyze/`, move/remove entry on completion
2. If source was in `needs-update/`, remove symlink on completion
3. If source is part of a synthesis collection, update collection status

## Synthesis Output Format

Synthesis documents follow a modified analysis template:

```markdown
# Synthesis: [Topic]

## Metadata
- **Synthesis ID**: synth-[topic-slug]-[date]
- **Sources**: [count] sources
- **Date**: YYYY-MM-DD
- **Status**: draft | reviewed

## Source Summary

| Source ID | Type | Key Finding | Evidence | Weight |
|-----------|------|-------------|----------|--------|
| peng-2023-... | RCT | 55.8% speedup | E2 | High |
| chatterjee-2024-... | Org A/B | 42% speedup | E2 | Medium |

## Convergence

[Where do sources agree?]

## Divergence

[Where do sources disagree? Why?]

## Evidence Quality Gradient

| Claim | E1 | E2 | E3 | E4 | E5 |
|-------|----|----|----|----|----|
| AI speeds up coding | - | 2 | - | 3 | 5 |
| Effect varies by experience | - | 1 | - | 1 | 2 |

## Synthesis Claims

Claims generated from this synthesis:

| ID | Claim | Type | Evidence | Credence |
|----|-------|------|----------|----------|
| LABOR-2026-XXX | [Synthesized claim] | [T] | E2 | 0.70 |

## Gaps and Open Questions

- [What evidence is missing?]
- [What would change our assessment?]

## Claims to Register

```yaml
claims:
  - id: LABOR-2026-XXX
    text: "..."
    type: "[T]"
    ...
    source_ids: ["peng-2023-...", "chatterjee-2024-..."]
```
```

## Implementation Checklist

### Phase 1: Basic Inbox Structure
- [ ] Create `inbox/` directory structure in data repo template
- [ ] Document inbox item formats
- [ ] Add `/inbox list` command
- [ ] Add `/inbox add` command

### Phase 2: Integration with /check
- [ ] Auto-remove from `to-analyze/` on successful `/check`
- [ ] Auto-remove from `needs-update/` on successful `/check --continue`
- [ ] Track `in-progress/` status (optional)

### Phase 3: Synthesis Workflow
- [ ] Add `/inbox synthesis` subcommands
- [ ] Create synthesis collection format
- [ ] Add `/synthesize` command
- [ ] Create synthesis output template

### Phase 4: Automation
- [ ] Hook to suggest inbox items when claims reference unanalyzed sources
- [ ] Periodic review prompt for `needs-update/` items
- [ ] Synthesis readiness notifications

## Migration for Existing Data Repos

For `realitycheck-data`:

```bash
mkdir -p inbox/{to-analyze,needs-update,synthesis}

# Flag analyses needing reprocessing (from quality audit)
cd inbox/needs-update
ln -s ../../analysis/sources/stross-2025-the-pivot-1.md .
echo "Missing Stage 2 tables" > stross-2025-the-pivot-1.reason.md
```

## Version History

- 2026-01-22: Initial planning document
