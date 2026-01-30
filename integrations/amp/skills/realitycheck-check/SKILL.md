<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/ + _config/skills.yaml -->
<!-- Regenerate: make assemble-skills -->

---
name: realitycheck-check
description: Full Reality Check analysis - fetch source, perform 3-stage analysis, extract claims, register to database, and validate. The flagship command for rigorous source analysis.
---

# Full Analysis Workflow

Full Reality Check analysis - fetch source, perform 3-stage analysis, extract claims, register to database, and validate. The flagship command for rigorous source analysis.

## When This Skill Activates

- "Analyze this article for claims"
- "Reality check this URL"
- "Run a check on"
- "Perform a full analysis"

The flagship Reality Check command for rigorous source analysis.

## Prerequisites

### Environment

Set `REALITYCHECK_DATA` to point to your data repository:

```bash
export REALITYCHECK_DATA=/path/to/realitycheck-data/data/realitycheck.lance
```

The `PROJECT_ROOT` is derived from this path - all analysis files go there.

### CLI Commands

Reality Check provides CLI tools (`rc-db`, `rc-validate`, `rc-export`, `rc-embed`).

**Check availability:**
```bash
which rc-db  # Should show path if pip-installed
```

**If commands are not found**, either:
1. Install: `pip install realitycheck` (recommended)
2. Use `uv run` from framework directory: `uv run python scripts/db.py ...`
3. Add framework as submodule and use: `.framework/scripts/db.py ...`

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

## Workflow Steps

1. **Start Tracking** - Begin token usage capture (lifecycle mode)
2. **Fetch** - Retrieve and parse source content
   - Primary: `WebFetch` for most URLs
   - Alternative: `curl -L -sS "URL" | rc-html-extract - --format json`
   - `rc-html-extract` returns structured `{title, published, text, headings, word_count}`
   - Use the extract tool when you need clean metadata or main text extraction
3. **Metadata** - Extract title, author, date, type, generate source-id
4. **Stage 1: Descriptive** - Neutral summary, key claims, argument structure
5. **Stage 2: Evaluative** - Evidence quality, fact-checking, disconfirming evidence
6. **Stage 3: Dialectical** - Steelman, counterarguments, synthesis
7. **Extract** - Format claims as YAML
8. **Register** - Add source and claims to database
9. **Provenance** (for high-credence claims) - Link evidence + capture reasoning trails
10. **Complete Tracking** - Finalize token usage + register `analysis_logs` row
11. **Validate** - Run integrity checks
12. **README** - Update data project analysis index
13. **Commit** - Stage and commit changes to data repo
14. **Push** - Push to remote
15. **Report** - Generate summary

---

## Multi-source Requests (Compare / Contrast)

If the prompt includes **multiple sources** (multiple URLs/repos/papers) or explicitly asks for **compare/contrast**, `$check` is responsible for the **full** multi-source workflow **end-to-end**:

1. Run the source-analysis workflow **once per source** (one `analysis/sources/<source-id>.md` per source)
2. Then, **in the same run**, also write a single cross-source synthesis at `analysis/syntheses/<synth-id>.md`

The synthesis should link back to the relevant source analyses and resolve (or clearly frame) points of agreement and disagreement.

Use `$synthesize` as a standalone command when you want to:
- create a synthesis later from existing source analyses
- update/refine an existing synthesis without re-running checks

---

## Analysis Output Contract

Every analysis must produce a **human-auditable analysis** file at:
`PROJECT_ROOT/analysis/sources/<source-id>.md`

The analysis **must** include:

1. **Metadata** (Source ID, URL, author, date/type)
2. **Legends** (top-of-file quick reference)
3. **Three-stage analysis** (Stages 1-3)
4. **Claim tables with evidence + credence**
5. **Extracted claims artifact** (embedded YAML or separate file)
6. **Analysis Log** (append-only pass history + tool/model/tokens/cost when available)

If an analysis lacks claim tables (IDs, evidence levels, credence) it is **not complete**.

### Multi-source Output

For multi-source requests, produce:
- **One** source analysis per source: `analysis/sources/<source-id>.md`
- **One** synthesis (required unless the user explicitly asks not to): `analysis/syntheses/<synth-id>.md`

### Required Elements

**Stage 1 (Descriptive)**:
- Source Metadata table
- Core Thesis (1-3 sentences)
- Key Claims table (with Verified? and Falsifiable By columns)
- Argument Structure diagram
- Theoretical Lineage
- Scope & Limitations

**Stage 2 (Evaluative)**:
- Key Factual Claims Verified (with Crux? column)
- Disconfirming Evidence Search
- Internal Tensions / Self-Contradictions
- Persuasion Techniques
- Unstated Assumptions
- Evidence Assessment
- Credence Assessment

**Stage 3 (Dialectical)**:
- Steelmanned Argument
- Strongest Counterarguments
- Supporting Theories (with source IDs)
- Contradicting Theories (with source IDs)
- Synthesis Notes
- Claims to Cross-Reference

**End**:
- Claim Summary table (all claims)
- Claims to Register (YAML)
- Credence in Analysis (0.0-1.0)

---

## Analysis Template

Use this structure for analysis documents:

```markdown
# Source Analysis: [Title]

> **Claim types**: `[F]` fact, `[T]` theory, `[H]` hypothesis, `[P]` prediction, `[A]` assumption, `[C]` counterfactual, `[S]` speculation, `[X]` contradiction
> **Evidence**: **E1** systematic review/meta-analysis; **E2** peer-reviewed/official stats; **E3** expert consensus/preprint; **E4** credible journalism/industry; **E5** opinion/anecdote; **E6** unsupported/speculative

## Metadata

| Field | Value |
|-------|-------|
| **Source ID** | [author-year-shorttitle] |
| **Title** | [extracted from source] |
| **Author(s)** | [name(s)] |
| **Date** | [YYYY-MM-DD or YYYY] |
| **Type** | [PAPER/ARTICLE/BLOG/REPORT/INTERVIEW/etc.] |
| **URL** | [source URL] |
| **Reliability** | [0.0-1.0] |
| **Rigor Level** | [SPITBALL/DRAFT/REVIEWED/CANONICAL] |

## Stage 1: Descriptive Analysis

### Core Thesis
[1-3 sentence summary of main argument]

### Key Claims

| # | Claim | Claim ID | Type | Domain | Evid | Credence | Verified? | Falsifiable By |
|---|-------|----------|------|--------|------|----------|-----------|----------------|
| 1 | [claim text] | DOMAIN-YYYY-NNN | [F/T/H/P/A/C/S/X] | DOMAIN | E1-E6 | 0.00-1.00 | [source or ?] | [what would refute] |
| 2 | | | | | | | | |
| 3 | | | | | | | | |

**Column guide**:
- **Claim**: Concise statement of the claim
- **Claim ID**: Format `DOMAIN-YYYY-NNN` (e.g., TECH-2026-001)
- **Type**: `[F]` fact, `[T]` theory, `[H]` hypothesis, `[P]` prediction, `[A]` assumption, `[C]` counterfactual, `[S]` speculation, `[X]` contradiction
- **Domain**: Primary domain code (TECH/LABOR/ECON/GOV/SOC/RESOURCE/TRANS/GEO/INST/RISK/META)
- **Evid**: Evidence level E1-E6
- **Credence**: Probability estimate 0.00-1.00
- **Verified?**: Source reference if verified, `?` if unverified
- **Falsifiable By**: What evidence would refute this claim

### Argument Structure

[Is this a chain argument? What's the logical flow?]

```
[Claim A]
    | implies
    v
[Claim B]
    | requires
    v
[Claim C]
    | leads to
    v
[Conclusion]
```

**Chain Analysis** (if applicable):
- **Weakest Link**: [Which step?]
- **Why Weak**: [Explanation]
- **If Link Breaks**: [What happens to conclusion?]
- **Alternative Paths**: [Can conclusion be reached differently?]

### Theoretical Lineage

[What traditions/thinkers does this build on?]

- **Primary influences**: [List key thinkers, schools of thought]
- **Builds on**: [Specific theories or frameworks this extends]
- **Departs from**: [Where this diverges from its intellectual predecessors]
- **Novel contributions**: [What's genuinely new here]

### Scope & Limitations
[What does this source attempt to explain? What does it explicitly not address?]

## Stage 2: Evaluative Analysis

### Internal Coherence
[Does the argument follow logically? Any contradictions?]

### Key Factual Claims Verified

> **Requirement**: Must include >=1 **crux claim** (central to thesis), not just peripheral numerics.

| Claim (paraphrased) | Crux? | Source Says | Actual | External Source | Status |
|---------------------|-------|-------------|--------|-----------------|--------|
| [e.g., "China makes 50% of X"] | N | [assertion] | [verified value] | [URL/ref] | ok / x / ? |
| [e.g., "Elite consensus on Y"] | **Y** | [assertion] | [verified or ?] | [URL/ref] | ok / x / ? |

**Column guide**:
- **Claim**: Paraphrased factual claim from the source
- **Crux?**: Is this claim central to the argument? Mark crux claims with **Y**
- **Source Says**: What the source asserts
- **Actual**: What verification found (or `?` if unverified)
- **External Source**: URL or reference used for verification
- **Status**: `ok` = verified, `x` = refuted, `?` = unverified

### Disconfirming Evidence Search

> For top 2-3 claims, actively search for counterevidence or alternative explanations (even 5 min changes behavior).

| Claim | Counterevidence Found | Alternative Explanation | Search Notes |
|-------|----------------------|-------------------------|--------------|
| [top claim 1] | [what contradicts it, or "none found"] | [other way to explain the data] | [what you searched] |
| [top claim 2] | [what contradicts it, or "none found"] | [other way to explain the data] | [what you searched] |
| [top claim 3] | [what contradicts it, or "none found"] | [other way to explain the data] | [what you searched] |

**Purpose**: Combat confirmation bias by explicitly searching for evidence against the source's claims.

### Internal Tensions / Self-Contradictions

| Tension | Parts in Conflict | Implication |
|---------|-------------------|-------------|
| [description of tension] | [Premise A] vs [Conclusion B] | [what it means for validity] |
| | | |

**Purpose**: Identify logical inconsistencies within the source's own argument.

### Persuasion Techniques

| Technique | Example from Source | Effect on Reader |
|-----------|---------------------|------------------|
| [e.g., Composition fallacy] | [quote or paraphrase] | [how it biases interpretation] |
| [e.g., Appeal to authority] | [quote or paraphrase] | [how it biases interpretation] |
| | | |

**Common techniques to watch for**:
- Composition/division fallacies
- Appeal to authority/emotion
- Cherry-picking data
- Motte-and-bailey
- Strawmanning alternatives
- False dichotomies
- Weasel words / hedging
- Anchoring with extreme examples

### Unstated Assumptions

| Assumption | Claim ID | Critical? | Problematic? |
|------------|----------|-----------|--------------|
| [assumption text] | [which claim depends on this] | Y/N | Y/N |
| | | | |

**Column guide**:
- **Assumption**: The unstated premise underlying the argument
- **Claim ID**: Which claim(s) depend on this assumption
- **Critical?**: Would the argument fail if this assumption is false?
- **Problematic?**: Is this assumption questionable or likely false?

**Purpose**: Surface hidden premises that may not be shared by all readers.

### Evidence Assessment
[Quality and relevance of supporting evidence]

### Credence Assessment
- **Overall Credence**: [0.0-1.0]
- **Reasoning**: [why this level?]

## Stage 3: Dialectical Analysis

### Steelmanned Argument
[Strongest possible version of this position]

### Strongest Counterarguments
1. [Counter + source if available]
2. [Counter + source if available]

### Supporting Theories

| Theory/Framework | Source ID | How It Supports |
|------------------|-----------|-----------------|
| [theory name] | [source-id] | [brief explanation of alignment] |
| | | |

### Contradicting Theories

| Theory/Framework | Source ID | Point of Conflict |
|------------------|-----------|-------------------|
| [theory name] | [source-id] | [brief explanation of conflict] |
| | | |

**Purpose**: Place this source in the broader theoretical landscape. Link to existing analyses where available.

### Synthesis Notes
[How does this update our overall understanding?]

### Claims to Cross-Reference
[Which claims should be checked against other sources?]

---

### Claim Summary

| ID | Type | Domain | Evidence | Credence | Claim |
|----|------|--------|----------|----------|-------|
| DOMAIN-YYYY-NNN | [F/T/H/P/A/C/S/X] | DOMAIN | E1-E6 | 0.00 | [claim text] |

**Notes**:
- All claims extracted from the source should appear in this table
- Use this for the complete claim inventory
- Key Claims table (above) highlights the most significant claims with additional columns

### Claims to Register

\`\`\`yaml
claims:
  - id: "DOMAIN-YYYY-NNN"
    text: "[Precise claim statement]"
    type: "[F/T/H/P/A/C/S/X]"
    domain: "[DOMAIN]"
    evidence_level: "E[1-6]"
    credence: 0.XX
    operationalization: "[How to test/measure this claim]"
    assumptions: ["..."]
    falsifiers: ["What would refute this"]
    source_ids: ["[source-id]"]
\`\`\`

---

**Analysis Date**: [YYYY-MM-DD]
**Analyst**: [human/claude/gpt/etc.]
**Credence in Analysis**: [0.0-1.0]

**Credence Reasoning**:
- [Why this credence level?]
- [What would increase/decrease credence?]
- [Key uncertainties remaining]

---

## Analysis Log

| Pass | Date | Tool | Model | Duration | Tokens | Cost | Notes |
|------|------|------|-------|----------|--------|------|-------|
| 1 | YYYY-MM-DD HH:MM | claude-code | claude-sonnet-4 | 8m | ? | ? | Initial 3-stage analysis |

**Token tracking**: Use lifecycle commands (`analysis start` / `analysis complete`) for accurate per-check token attribution. The `tokens_check` field captures only the tokens used for this specific analysis, not the entire session.

### Revision Notes

**Pass 1**: [What changed in this pass? What was added/updated and why?]
```

---

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

## Credence Calibration

To maintain well-calibrated credence:

| Range | Interpretation |
|-------|----------------|
| 0.9-1.0 | Would bet significant resources; very strong evidence |
| 0.7-0.8 | High credence but acknowledge meaningful uncertainty |
| 0.5-0.6 | Genuine uncertainty; could go either way |
| 0.3-0.4 | Lean against but not high credence |
| 0.1-0.2 | Strongly doubt but can't rule out |
| 0.0-0.1 | Would bet heavily against; extraordinary evidence needed |

**Aggregation notes**:
- A theory with many 0.7 credence claims is not itself 0.7 credence
- Credence in overall theory depends on logical structure and weakest critical links
- Chain arguments: overall credence <= weakest link
- Explicitly model dependencies when possible

---

## Database Commands

### Command Availability

Reality Check commands can be invoked in two ways:

1. **`rc-db` / `rc-validate` / etc.** - Works if you pip-installed `realitycheck`
2. **`uv run python scripts/db.py`** - Works from the framework repo with uv

**Check which is available:**

```bash
# Test pip-installed version
which rc-db && rc-db --version

# If not installed, use uv from framework directory
# (requires being in realitycheck repo or having it as submodule)
uv run python scripts/db.py --help
```

**If neither works:**
- Install: `pip install realitycheck` or `uv pip install realitycheck`
- Or clone/submodule the framework and use `uv run` from that directory

### Usage Examples

Use installed commands if available, otherwise fall back to uv:

```bash
# Check database stats
rc-db stats
# or: uv run python scripts/db.py stats

# Register source
rc-db source add \
  --id "SOURCE_ID" \
  --title "TITLE" \
  --type "TYPE" \
  --author "AUTHOR" \
  --year YEAR \
  --url "URL" \
  --analysis-file "analysis/sources/SOURCE_ID.md" \
  --topics "tag1,tag2" \
  --domains "TECH,LABOR"

# Update source metadata later
rc-db source update "SOURCE_ID" \
  --analysis-file "analysis/sources/SOURCE_ID.md" \
  --topics "tag1,tag2" \
  --domains "TECH,LABOR" \
  --claims-extracted "DOMAIN-YYYY-NNN,DOMAIN-YYYY-NNN"

# Register claim
rc-db claim add \
  --id "CLAIM_ID" \
  --text "CLAIM_TEXT" \
  --type "[TYPE]" \
  --domain "DOMAIN" \
  --evidence-level "EX" \
  --credence 0.XX \
  --source-ids "SOURCE_ID"

# Recommended: import source + claims in one step (format: analysis/sources/<source-id>.yaml)
rc-db import "analysis/sources/SOURCE_ID.yaml" --type all

# Search claims
rc-db search "query" --limit 10

# Get specific record
rc-db claim get CLAIM_ID
rc-db source get SOURCE_ID

# List records
rc-db claim list --domain TECH
rc-db source list --type ARTICLE

# Analysis lifecycle (recommended for accurate token tracking)
# 1. Start: capture baseline tokens
ANALYSIS_ID=$(rc-db analysis start \
  --source-id "SOURCE_ID" \
  --tool claude-code \
  --model "claude-sonnet-4")

# 2. (Optional) Mark stage checkpoints
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage1
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage2

# 3. Complete: capture final tokens and compute delta
rc-db analysis complete \
  --id "$ANALYSIS_ID" \
  --analysis-file "analysis/sources/SOURCE_ID.md" \
  --claims-extracted "DOMAIN-YYYY-001,DOMAIN-YYYY-002" \
  --estimate-cost \
  --notes "Initial analysis + registration"

# Session discovery (if auto-detection fails)
rc-db analysis sessions list --tool claude-code --limit 10

# Alternative: one-shot add (legacy, less accurate for multi-check sessions)
rc-db analysis add \
  --source-id "SOURCE_ID" \
  --tool codex \
  --cmd check \
  --analysis-file "analysis/sources/SOURCE_ID.md" \
  --model "gpt-4o" \
  --usage-from codex:"/path/to/rollout-*.jsonl" \
  --estimate-cost \
  --notes "Initial analysis + registration"

# Query analysis logs
rc-db analysis list --source-id "SOURCE_ID"
rc-db analysis get ANALYSIS-YYYY-NNN
```

### Evidence Links

```bash
# Add evidence link (connects claim to supporting/contradicting source)
rc-db evidence add \
  --claim-id "DOMAIN-YYYY-NNN" \
  --source-id "source-id" \
  --direction supports \
  --strength 0.8 \
  --location "Table 3, p.15" \
  --reasoning "Direct measurement supports the claim"

# List evidence for a claim
rc-db evidence list --claim-id "DOMAIN-YYYY-NNN"

# List evidence from a source
rc-db evidence list --source-id "source-id"

# Get specific evidence link
rc-db evidence get EVLINK-2026-001

# Supersede (correct) an evidence link
rc-db evidence supersede EVLINK-2026-001 \
  --direction weakens \
  --reasoning "Re-evaluated: methodology concerns reduce support"
```

### Reasoning Trails

```bash
# Add reasoning trail (documents why credence was assigned)
rc-db reasoning add \
  --claim-id "DOMAIN-YYYY-NNN" \
  --credence 0.75 \
  --evidence-level E2 \
  --evidence-summary "E2 based on 2 supporting, 1 weak counter" \
  --supporting-evidence "EVLINK-2026-001,EVLINK-2026-002" \
  --contradicting-evidence "EVLINK-2026-003" \
  --reasoning-text "Assigned 0.75 because..."

# Get active reasoning trail for a claim
rc-db reasoning get --claim-id "DOMAIN-YYYY-NNN"

# List all reasoning trails
rc-db reasoning list --claim-id "DOMAIN-YYYY-NNN"

# Get full reasoning history (including superseded)
rc-db reasoning history --claim-id "DOMAIN-YYYY-NNN"
```

### Validation

```bash
rc-validate
# or: uv run python scripts/validate.py

# Strict mode (treat warnings as errors, including missing provenance)
rc-validate --strict
```

### Export

```bash
rc-export yaml claims -o claims.yaml
rc-export yaml sources -o sources.yaml
rc-export yaml analysis-logs -o analysis-logs.yaml
rc-export md summary -o summary.md
rc-export md analysis-logs -o analysis-logs.md

# Provenance exports
rc-export md reasoning --id DOMAIN-YYYY-NNN -o analysis/reasoning/DOMAIN-YYYY-NNN.md
rc-export md reasoning --all --output-dir analysis/reasoning
rc-export md evidence-by-claim --id DOMAIN-YYYY-NNN -o analysis/evidence/by-claim/DOMAIN-YYYY-NNN.md
rc-export md evidence-by-source --id source-id -o analysis/evidence/by-source/source-id.md
rc-export provenance --format yaml -o provenance.yaml
rc-export provenance --format json -o provenance.json
```

### Embedding Management

Semantic search requires embeddings. Check and manage embedding status:

```bash
# Check embedding coverage
rc-embed status
# or: uv run python scripts/embed.py status

# Generate missing embeddings (backfill)
rc-embed generate --verbose
# or: uv run python scripts/embed.py generate --verbose

# Regenerate all embeddings (after model change)
rc-embed regenerate --verbose
# or: uv run python scripts/embed.py regenerate --verbose
```

**Troubleshooting:**
- If `rc-embed` not found: `pip install realitycheck` or use `uv run python scripts/embed.py`
- If embedding generation fails: check `sentence-transformers` is installed
- Default model: `all-MiniLM-L6-v2` (CPU-based, 384 dimensions)
- To skip embeddings in CI/tests: `export REALITYCHECK_EMBED_SKIP=1`

---

## Epistemic Provenance (Optional but Recommended)

For high-credence claims (≥0.7) or strong evidence (E1/E2), capture the reasoning chain:

### 1. Link Evidence to Claims

Connect claims to their supporting/contradicting sources:

```bash
# Add evidence link
rc-db evidence add \
  --claim-id "DOMAIN-YYYY-NNN" \
  --source-id "source-id" \
  --direction supports \
  --strength 0.8 \
  --location "Table 3, p.15" \
  --reasoning "Direct measurement supports the claim"

# Directions: supports, contradicts, strengthens, weakens
```

### 2. Capture Reasoning Trails

Document why you assigned a particular credence:

```bash
rc-db reasoning add \
  --claim-id "DOMAIN-YYYY-NNN" \
  --credence 0.75 \
  --evidence-level E2 \
  --evidence-summary "E2 based on 2 supporting sources, 1 weak counter" \
  --supporting-evidence "EVLINK-2026-001,EVLINK-2026-002" \
  --contradicting-evidence "EVLINK-2026-003" \
  --reasoning-text "Assigned 0.75 because: (1) Two independent studies confirm X, (2) One methodologically weak study contradicts, discounted due to sample size issues"
```

### 3. Render Provenance Docs (Optional)

Export human-readable provenance for review:

```bash
# Single claim
rc-export md reasoning --id DOMAIN-YYYY-NNN -o analysis/reasoning/DOMAIN-YYYY-NNN.md

# All claims with trails
rc-export md reasoning --all --output-dir analysis/reasoning

# Evidence by source
rc-export md evidence-by-source --id source-id -o analysis/evidence/by-source/source-id.md
```

### When to Capture Provenance

- **Always** for claims with credence ≥ 0.7 (validation will warn if missing)
- **Always** for claims with E1/E2 evidence (high-quality evidence needs documented reasoning)
- **Recommended** for controversial or novel claims
- **Optional** for routine factual claims with obvious sourcing

---

## Token Usage Tracking (Lifecycle Mode)

For accurate per-check token attribution, use the lifecycle commands:

```bash
# 1. At workflow START (before fetch)
ANALYSIS_ID=$(rc-db analysis start \
  --source-id "[source-id]" \
  --tool claude-code \
  --model "claude-sonnet-4")

# 2. (Optional) Mark stage completions
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage1
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage2
rc-db analysis mark --id "$ANALYSIS_ID" --stage check_stage3

# 3. At workflow END (after registration, before validation)
rc-db analysis complete \
  --id "$ANALYSIS_ID" \
  --analysis-file "analysis/sources/[source-id].md" \
  --claims-extracted "DOMAIN-YYYY-001,DOMAIN-YYYY-002" \
  --estimate-cost \
  --notes "3-stage analysis + registration"
```

This captures `tokens_baseline` at start and `tokens_final` at completion, computing `tokens_check = final - baseline` for accurate cost attribution.

If session auto-detection fails (ambiguous sessions), use `rc-db analysis sessions list --tool claude-code` to find your session UUID, then pass `--usage-session-id UUID` to `analysis start`.

---

## Update README (REQUIRED)

After registration and validation, update the data project's README.md:

### 1. Add Syntheses Table Entry (if created)

If you produced a synthesis document, add a row to the "Syntheses" table (kept **above** "Source Analyses"):

```markdown
| YYYY-MM-DD | [Topic](analysis/syntheses/<synth-id>.md) | `[DRAFT/REVIEWED]` | Brief summary |
```

Insert at the **top** of the table (below header row), keeping entries reverse-chronological.

### 2. Add Source Analyses Table Entry

**Edit `$PROJECT_ROOT/README.md` now.** Find the "Source Analyses" table and insert a new row:

```markdown
| YYYY-MM-DD | [Title](analysis/sources/<source-id>.md) | `[REVIEWED]` | Brief summary |
```

Insert at the **top** of the table (below header row), keeping entries reverse-chronological.

### 3. Update Stats Tables

Run the stats update script to refresh claim/source counts:

```bash
# From the realitycheck framework directory
scripts/update-readme-stats.sh "$PROJECT_ROOT"
# or: bash scripts/update-readme-stats.sh "$(dirname "$REALITYCHECK_DATA")"
```

This updates the "Current Status" and "Claim Domains" tables automatically.

---

## Commit and Push (REQUIRED)

**You MUST commit and push after every successful analysis.** This is not optional.

```bash
# From the data project root
cd "$(dirname "$REALITYCHECK_DATA")"

# Stage all changes
git add data/ analysis/ tracking/ README.md claims/ reference/

# Commit with descriptive message
git commit -m "data: add [source-id] - [brief description]"

# Push to remote
git push
```

**Do not stop until changes are committed and pushed.** The analysis is incomplete without version control.

---

## Continuation Mode

When using `--continue` on an existing analysis:

1. **Find existing analysis**: Look for `analysis/sources/[source-id].md`
2. **Read current state**: Load the existing analysis and registered claims
3. **Iterate, don't overwrite**: Add to the existing analysis rather than replacing it
4. **Focus areas**:
   - Extract claims that were skipped or noted as "TODO"
   - Deepen specific sections (more counterfactuals, stronger steelman)
   - Add evidence that was found after initial analysis
   - Address questions or gaps identified in the original pass
   - Cross-reference with newly added claims in the database
5. **Preserve content**: Append new sections, update claim counts, note what changed

---

## Related Skills

- `realitycheck-synthesize`
- `realitycheck-search`
- `realitycheck-validate`
- `realitycheck-stats`
