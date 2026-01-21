# Quality Regression Fix - Analysis Methodology

**Status**: Analysis complete, awaiting implementation decision
**Created**: 2026-01-22

## Problem Statement

Analyses produced after the framework separation (into `realitycheck` framework + `realitycheck-data` knowledge base) are noticeably lower quality than analyses produced before the split using the original `postsingularity-economic-theories/AGENTS.md`.

## Root Cause

When we extracted the shared methodology into `methodology/workflows/check-core.md`, we **over-trimmed** the content. The original AGENTS.md was 934 lines with comprehensive templates; our check-core.md is only 259 lines.

The trimming removed critical **structural templates** that guide agents to produce comprehensive analyses.

## Quantitative Comparison

| Document | Lines | Purpose |
|----------|------:|---------|
| `postsingularity-economic-theories/AGENTS.md` | 934 | Original full methodology |
| `methodology/workflows/check-core.md` | 259 | Current shared methodology |
| **Missing** | **~675** | **Lost detail** |

## Quality Comparison: Before vs After

### Example: High-Quality Analysis (pre-split)
**File**: `realitycheck-data/analysis/sources/doctorow-2026-reverse-centaur.md`
**Model**: GPT-5.2 xhigh

Features present:
- Key Claims table with `Verified?` and `Falsifiable By` columns
- Key Factual Claims Verified table with `Crux?` column
- Disconfirming Evidence Search table
- Internal Tensions / Self-Contradictions table
- Persuasion Techniques table
- Unstated Assumptions table
- Argument Structure diagram
- Theoretical Lineage section
- Confidence Assessment with reasoning
- Supporting/Contradicting Theories with claim IDs

### Example: Lower-Quality Analysis (post-split)
**File**: `realitycheck-data/analysis/sources/stross-2025-the-pivot-1.md`
**Model**: Claude Opus 4.5

Features **missing**:
- `Verified?` column in Key Claims table
- `Falsifiable By` column in Key Claims table
- Key Factual Claims Verified table (with `Crux?` column)
- Disconfirming Evidence Search table
- Internal Tensions / Self-Contradictions table
- Persuasion Techniques table
- Argument Structure diagram
- Theoretical Lineage section
- Confidence in Analysis score at end

## Specific Missing Templates

### 1. Key Claims Table (Stage 1)

**Original template** (full):
```markdown
| # | Claim | Claim ID | Type | Domain | Evid | Conf | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|------|-----------|----------------|
| 1 | | | | | | | [source or ?] | [what would refute] |
```

**Current template** (incomplete):
```markdown
| # | Claim | Claim ID | Type | Domain | Evidence | Credence | Verified? | Falsifiable By |
```

The template is shown in Output Contract but agents aren't following it because they reference the simpler Claim Summary table format.

### 2. Key Factual Claims Verified Table (Stage 2)

**Original** (present in AGENTS.md):
```markdown
| Claim (paraphrased) | Crux? | Source Says | Actual | External Source | Status |
|---------------------|-------|-------------|--------|-----------------|--------|
| [e.g., "China makes 50%..."] | N | [assertion] | [verified] | [URL/ref] | ✓ / ✗ / ? |
| [e.g., "Elite consensus..."] | **Y** | [assertion] | [verified or ?] | [URL/ref] | ✓ / ✗ / ? |
```

**Current**: Not present in check-core.md

### 3. Disconfirming Evidence Search Table (Stage 2)

**Original** (present in AGENTS.md):
```markdown
| Claim | Counterevidence Found | Alternative Explanation | Search Notes |
|-------|----------------------|------------------------|--------------|
| [top claim 1] | [what contradicts it, or "none found"] | [other way to explain] | [what you searched] |
```

**Current**: Not present - only text description "Actively search for contradictions"

### 4. Internal Tensions / Self-Contradictions Table (Stage 2)

**Original** (present in AGENTS.md):
```markdown
| Tension | Parts in Conflict | Implication |
|---------|-------------------|-------------|
| [description] | [Premise A] vs [Conclusion B] | [what it means for validity] |
```

**Current**: Not present

### 5. Persuasion Techniques Table (Stage 2)

**Original** (present in AGENTS.md):
```markdown
| Technique | Example from Source | Effect on Reader |
|-----------|---------------------|------------------|
| [e.g., Composition fallacy] | [quote] | [how it biases interpretation] |
```

**Current**: Only mentioned as "Note rhetorical devices" without template

### 6. Unstated Assumptions Table (Stage 2)

**Original** (present in AGENTS.md):
```markdown
| Assumption | Claim ID | Critical? | Problematic? |
|------------|----------|-----------|--------------|
```

**Current**: Not present as structured template

### 7. Supporting/Contradicting Theories (Stage 3)

**Original** (present in AGENTS.md):
```markdown
### Supporting Theories
[Other frameworks that align/support - with source IDs]

### Contradicting Theories
[Other frameworks that conflict - with source IDs]
```

**Current**: Not explicitly templated

### 8. Confidence in Analysis (End)

**Original** (present in AGENTS.md):
```markdown
**Confidence in Analysis**: [0.0-1.0]
```

**Current**: Not present

### 9. Argument Structure Diagram (Stage 1)

**Original** (present in AGENTS.md):
```markdown
### Argument Structure
[Is this a chain argument? What's the logical flow?]

```
[Claim A]
    ↓ implies
[Claim B]
    ↓ requires
[Claim C]
```
```

**Current**: Not present

### 10. Theoretical Lineage (Stage 1)

**Original** (present in AGENTS.md):
```markdown
### Theoretical Lineage
[What traditions/thinkers does this build on?]
```

**Current**: Not present

## Why This Matters

Without explicit templates, agents:
1. **Skip sections** - they don't know they're expected
2. **Use simpler formats** - they default to whatever's easiest
3. **Omit critical thinking steps** - e.g., no disconfirming evidence search
4. **Produce less auditable analyses** - missing verification status

The original AGENTS.md worked because it showed agents **exactly** what the output should look like, including every column and every section.

## Proposed Solutions

### Option A: Restore Full Templates to check-core.md

**Approach**: Expand check-core.md to include all the missing templates from the original AGENTS.md.

**Pros**:
- Single source of truth
- Consistent across all integrations
- Matches proven working methodology

**Cons**:
- Larger file (~900+ lines)
- More context for agents to process
- May slow down quick analyses

### Option B: Create Template Library

**Approach**: Keep check-core.md lean but add `methodology/templates/` with specific templates that skills can reference.

```
methodology/
├── workflows/
│   └── check-core.md          # Core methodology (lean)
└── templates/
    ├── stage1-claims.md       # Key Claims table template
    ├── stage2-verification.md # Fact verification tables
    ├── stage2-critique.md     # Disconfirming evidence, tensions
    └── stage3-synthesis.md    # Supporting/contradicting theories
```

**Pros**:
- Modular, can pick templates needed
- Smaller individual files
- Easier to update individual templates

**Cons**:
- More files to coordinate
- Skills must explicitly include templates
- Risk of inconsistency

### Option C: Fat Skills with Embedded Templates

**Approach**: Each skill (Claude/Codex) embeds the full templates directly, rather than referencing external files.

**Pros**:
- Self-contained
- Guaranteed agents see the templates
- No external file dependencies

**Cons**:
- Duplication across skills
- Harder to keep in sync
- Larger skill files

### Option D: Jinja-style Template Stitching

**Approach**: Use a build step to stitch together methodology + templates into per-integration skill files.

```yaml
# skill-config.yaml
base: methodology/workflows/check-core.md
includes:
  - methodology/templates/stage1-claims.md
  - methodology/templates/stage2-verification.md
  - methodology/templates/stage2-critique.md
  - methodology/templates/stage3-synthesis.md
```

**Pros**:
- Single source of truth for each piece
- Generated skills are self-contained
- Can customize per integration

**Cons**:
- Build step required
- More complexity
- Generated files need to be committed or regenerated

## Recommendation

**Option A (Restore Full Templates)** is the simplest path to quality restoration.

The original AGENTS.md proved effective at ~934 lines - modern models can handle this context size. The over-trimming was premature optimization.

**Implementation**:
1. Restore all missing templates to `check-core.md`
2. Add explicit "Required Sections" list that agents must produce
3. Add validation checklist at end of workflow

If context size becomes a problem, we can later move to Option B or D.

## Implementation Checklist

- [ ] Add Key Factual Claims Verified table to Stage 2
- [ ] Add Disconfirming Evidence Search table to Stage 2
- [ ] Add Internal Tensions table to Stage 2
- [ ] Add Persuasion Techniques table to Stage 2
- [ ] Add Unstated Assumptions table to Stage 2
- [ ] Add Argument Structure diagram to Stage 1
- [ ] Add Theoretical Lineage section to Stage 1
- [ ] Add Confidence in Analysis to end
- [ ] Add Supporting/Contradicting Theories template to Stage 3
- [ ] Ensure Key Claims table includes Verified? and Falsifiable By
- [ ] Add "Required Sections Checklist" to Output Contract
- [ ] Test with a new analysis to verify quality

## Analyses Requiring Reprocessing

After restoring the full methodology, the following analyses should be reprocessed with `--continue` to add missing sections.

### Quality Audit Results

| Analysis | Key Claims | Crux? | Counterevidence | Tensions | Persuasion | Confidence | Status |
|----------|:----------:|:-----:|:---------------:|:--------:|:----------:|:----------:|--------|
| doctorow-2026-reverse-centaur | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| teortaxes-2026-greenland-endgame | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| perera-2026-chinas-trillion-dollar-illusion | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| ronacher-2026-agent-psychosis | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **OK** |
| carney-2026-davos-wef-speech | ✓ | ✓ | ✓ | ✓ | ✓ | - | **OK** |
| openai-value-intelligence | ✓ | - | - | - | - | ✓ | Partial |
| jre-2404-elon-musk-2025-ai-woke-mind-virus | ✓ | - | - | - | ✓ | - | Partial |
| stross-2025-the-pivot-1 | - | - | - | - | - | - | **REPROCESS** |
| chatterjee-2024-anz-copilot-study | ✓ | - | - | - | - | - | Quick/OK |
| peng-2023-copilot-productivity | ✓ | - | - | - | - | - | Quick/OK |

### Reprocessing Queue

**Priority 1 - Missing most templates (full reprocess)**:
- [ ] `stross-2025-the-pivot-1` - Missing all Stage 2 evaluation tables

**Priority 2 - Missing some templates (continuation pass)**:
- [ ] `openai-value-intelligence` - Add Stage 2 tables (Crux?, Counterevidence, Tensions, Persuasion)
- [ ] `jre-2404-elon-musk-2025-ai-woke-mind-virus` - Add Stage 2 tables (Crux?, Counterevidence, Tensions), add Confidence

**No action needed**:
- `chatterjee-2024-anz-copilot-study` - Intentionally abbreviated (quick extraction for cross-reference)
- `peng-2023-copilot-productivity` - Intentionally abbreviated (quick extraction for cross-reference)

### Reprocessing Commands

After methodology is restored:

```bash
# Full reprocess
/check stross-2025-the-pivot-1 --continue

# Continuation passes
/check openai-value-intelligence --continue
/check jre-2404-elon-musk-2025-ai-woke-mind-virus --continue
```

## Version History

- 2026-01-22: Initial analysis and documentation
- 2026-01-22: Added reprocessing queue based on quality audit
