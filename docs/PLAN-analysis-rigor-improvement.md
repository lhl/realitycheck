# Plan: Analysis Rigor Improvements (Primary Evidence, Layering, Corrections, Auditability)

**Status**: Spec Locked (ready to implement)  
**Created**: 2026-01-25  
**Updated**: 2026-01-31  

## Motivation

Reality Check’s core promise is to help users separate **rhetorical framing** from **checkable claims**, then assign **evidence levels** and **credences** in a way that is:

- **auditable** (a reader can trace “why 0.75?”),
- **layer-aware** (what’s asserted vs what’s lawful vs what’s practiced),
- **resistant to fast-moving information hazards** (updates/corrections),
- **precise about scope** (who/where/when/process/actor),
- **safe against confidence theater** (numbers that look calibrated but aren’t justified).

In recent “ICE enforcement powers / Minnesota incidents” work (analyzed from an X post), we iterated through multiple rounds and still saw persistent conflicts between what “should be true” (law/constraints) and what might “actually be happening” (agency positions and field practice). Reviewers converged on the same systemic failure modes:

- We often cite **secondary reporting** about primary documents even when primary documents are available.
- We don’t yet have a **first-class mechanism for corrections/updates**.
- We don’t consistently enforce **actor attribution** (ICE vs CBP/Border Patrol vs DHS vs DOJ).
- Our claim tables don’t *force* a split between **asserted authority**, **lawful authority**, and **practiced reality**; we rely on prose to do that work.
- Credence adjustments get proposed based on **uncaptured sources**, making the DB non-auditable if we accept them.

This plan captures the improvements required to make the analysis workflow reliably produce “reader-auditable” outputs and reduce recurring failure cases—especially for politically charged, legally technical topics where scope, attribution, and updates matter.

## Background (Case Study: ICE Analysis Review Loop)

The following artifacts are illustrative inputs to this plan:

- A source analysis of an X post listing “positions ICE has taken” (data repo analysis document).
- External reviewer transcripts (ChatGPT and Claude) that recommended:
  - primary-document capture (memo PDFs, court orders),
  - correction tracking (e.g., Reason article correction),
  - stricter ICE vs CBP attribution,
  - explicit “asserted vs lawful vs practiced” split,
  - ingestion of missing primary sources before making credence changes (e.g., “Mobile Fortify” PTA, ProPublica/Senate PSI).

This plan is **not** about adjudicating the truth of those specific claims; it is about upgrading the framework so the next analysis run produces outputs that *make those disagreements legible and resolvable*.

## Problem Statement

Today, the analysis workflow can produce tables with evidence levels and credences that appear rigorous but are not consistently:

1. **Layer-separated** (asserted vs lawful vs practiced),
2. **Source-auditable** (primary docs captured; citations include locators),
3. **Update-aware** (corrections captured; stale citations flagged),
4. **Attribution-correct** (actor named precisely and consistently),
5. **Scope-bounded** (quantifiers and conditions enforced in structured form).

When any of these fail, we get an epistemic failure mode:

> “High-confidence summaries of ambiguous powers.”

That failure mode is exactly what Reality Check exists to prevent.

## Goals

1. **Layered Claims by Default**: Make it hard to conflate “ICE asserts X” with “X is lawful” or “X is practiced.”
2. **Primary-First Evidence**: Where primary documents exist and are accessible, capture them (or explicitly record why not).
3. **Corrections as First-Class**: Detect and record corrections/updates and propagate their impact to affected claims.
4. **Actor & Scope Discipline**: Enforce structured attribution and scope conditions in the claim tables (not only in prose).
5. **Auditable Credence**: Every credence (especially high credence) has a traceable rationale tied to specific evidence.
6. **Controlled Credence Changes**: Prevent DB credence updates based on uncaptured/unlinked evidence.
7. **Repeatable Review Workflow**: Enable multi-pass, reviewer-inclusive refinement without muddying provenance.

## Non-goals (This Plan)

- Perfect truth: Reality Check improves auditability and error-correction, not omniscience.
- Full legal analysis: We are not building a law firm; we are building a disciplined evidence workflow.
- Storing private chain-of-thought: we want publishable rationales, not hidden reasoning.
- Solving paywalls/network restrictions: we will record access constraints and use alternative sources, but cannot guarantee access.
- Replacing the existing E1–E6 hierarchy wholesale (we may extend it, but avoid a full rewrite unless necessary).

## Terminology (Core Distinctions We Must Enforce)

### Claim “layer” (deconflicts “should” vs “is”)

For legal/policy topics, claims must be explicitly tagged as one of:

1. **ASSERTED**: “Agency/officials assert X” (memos, litigation positions, statements).
2. **LAWFUL**: “X is lawful/authorized under controlling law” (statutes/regulations/case holdings).
3. **PRACTICED**: “X is done in practice” (incidents, patterns, implementation evidence).
4. **EFFECT**: “X leads to outcome Y” (systemic effects; requires additional causal evidence).

Rhetorical framings (e.g., “totalitarianism”) are not layers; they are treated as **framing** (often a synthesis-level claim, not a single factual claim).

### Actor attribution (who is doing what)

For DHS ecosystem topics, the “actor” must be explicit:

- ICE (and when possible: ERO vs HSI),
- CBP (and when possible: Border Patrol vs OFO),
- DHS (leadership / secretary statements),
- DOJ (memos, prosecutions),
- Courts (holdings, stays, dissents),
- State/local law enforcement (when relevant).

### Scope conditions (when “can” becomes “always”)

Claims must record structured scope:

- **Who**: target population (citizens/noncitizens; final order; asylum seeker; etc.).
- **Where**: home vs public space; border zone vs interior; detention facility vs street stop.
- **Process**: expedited removal vs removal proceedings; pre-removal vs post-removal detention.
- **Time**: typical notice vs short notice; emergency actions.
- **Predicate**: final order, probable cause, consent, warrant type, etc.

### Quantifiers (avoid unverifiable “generally/always/anywhere”)

Claims using quantifiers must be explicit and testable:

- none / some / often / most / nearly all / always

If we do not have statistics, we should avoid “most” and “generally” unless it is clearly bounded (“in expedited removal cases…”).

## Failure Modes Targeted (Observed + Generalized)

1. **Layer collapse**: “asserted position” silently becomes “lawful authority” (or “practiced reality”).
2. **Compound claim bundling**: multiple propositions share a single evidence level/credence.
3. **Secondary-source anchoring**: credible reporting is treated as “best available” when primary docs exist.
4. **Correction blindness**: updated/corrected articles continue to support strong claims.
5. **Actor attribution leakage**: CBP incidents are used as evidence for “ICE did X” without marking the actor split.
6. **Scope erasure**: “can” becomes “can anywhere/always/no matter what.”
7. **Evidence type conflation**: “Evidence level” mixes evidence type, source reliability, and claim-match precision.
8. **Unauditable credence**: numbers appear calibrated but do not cite specific evidence and locators.
9. **Stale analyses**: analyses aren’t updated when new court orders or memos appear, but are still treated as current.
10. **Normative drift**: “should be illegal” vs “is illegal” gets entangled unless we explicitly layer-tag.

## Proposed Improvements (Decisions + Rationale)

This section is written in an “ADR-like” style: what we are changing, why, and what failure cases it addresses.

### 1) Enforce Layer/Actor/Scope in claim tables (template-level enforcement)

**Decision**: Extend the analysis output contract so claim tables *require* structured fields:

- `Layer` (ASSERTED/LAWFUL/PRACTICED/EFFECT),
- `Actor` (ICE/CBP/DHS/DOJ/Court/etc),
- `Scope` (minimal structured summary),
- `Quantifier` (none/some/often/most/always),
- `Evidence Level` (E1–E6),
- `Credence` (0–1).

**Why**:
- Prose already discusses asserted vs lawful vs practiced, but tables don’t enforce the split.
- Tables are the “interface” most readers rely on; enforcement must happen there.

**Targets failure modes**: 1, 2, 5, 6, 10.

**Tradeoffs**:
- Increases table complexity and authoring friction.
- Requires updates to templates, skill instructions, and (optionally) validators.

**Acceptance criteria**:
- Any claim row with mixed layers must be split.
- Any claim row referencing an incident must have an explicit actor (ICE vs CBP).
- Any claim row with “generally/always/anywhere” must include a quantifier and a scope field.

### 2) Primary-source-first rule + capture requirement (workflow-level gate)

**Decision**: For claims about law/policy/memos/court actions, prefer primary sources in this order:

1. primary doc (PDF, order, filing, statute/reg text),
2. high-quality reporting summarizing the primary,
3. commentary/analysis.

For high-impact claims (see below), require capture of the primary artifact when available.

**High-impact thresholds (initial proposal)**:
- any claim with `credence ≥ 0.7`, or
- any claim with evidence level `E1/E2`, or
- any “LAWFUL” layer claim (controlling law).

**Why**:
- Without primary capture, we can’t audit whether the summary matches the document.
- This is the single most consistent gap surfaced by reviewers.

**Targets failure modes**: 3, 7, 8, 9.

**Tradeoffs**:
- Requires building (or adopting) PDF extraction/capture tooling.
- Paywalls and JS-blocked sources may block capture; we must record constraints.

**Acceptance criteria**:
- If a primary doc is accessible, it is captured under `reference/primary/...` in the data repo with a stable path.
- If it is not accessible, analysis must record “capture failed” + reason + fallback evidence used.
- Credence for “ASSERTED” claims may be high based on a captured memo; “LAWFUL” and “PRACTICED” must be justified independently.

### 3) Corrections / updates tracking (sources and evidence links become versioned)

**Decision**: Add a dedicated “Corrections & Updates” section (and later structured storage) with:

- URL
- published date (if available)
- updated/correction date (if available)
- correction text summary (quote if brief)
- impacted claim IDs + what changes (evidence level, credence, or claim split)

Additionally, adopt **append-only semantics** for corrections in provenance (supersedes/retracts), aligning with `PLAN-epistemic-provenance.md`.

**Why**:
- “Correction blindness” converts journalism into a time bomb: old claims linger with old credences.
- Corrections are common in precisely the topics where we most need rigor.

**Targets failure modes**: 4, 9.

**Tradeoffs**:
- Adds “maintenance burden” for long-lived analyses.
- Requires discipline: “last checked” dates and update routines.

**Acceptance criteria**:
- Any source used to support a claim must record `accessed` and (when refreshed) `last_checked`.
- If a correction meaningfully changes a claim, the claim must be split or downgraded and the change logged.

### 4) Separate “evidence type” from “evidence strength” (reduce E-level overload)

**Decision**: Keep E1–E6 as a coarse **strength** scale, but explicitly record:

- `Evidence Type` (what kind of thing is this?),
- `Source Reliability` (how reliable is this source?),
- `Claim Match` (how directly does it support the exact phrasing?).

Where possible, we should stop treating “E4 = credible journalism” as sufficient; journalism can be credible but still mismatch the precise claim.

**Why**:
- The E hierarchy currently conflates three different axes and encourages overconfidence.

**Targets failure modes**: 7, 8.

**Tradeoffs**:
- Adds more fields and a bit more subjectivity (especially claim-match).
- Requires calibration guidance so we don’t invent false precision.

**Acceptance criteria**:
- Every high-credence claim explicitly records evidence type + claim-match reasoning.
- Evidence level alone is no longer treated as the full justification.

### 5) “Lawfulness” discipline for court citations (opinion voice + procedural posture)

**Decision**: When citing courts/SCOTUS, analyses must record:

- whether the cited language is from a holding vs reasoning vs dicta,
- majority vs concurrence vs dissent,
- posture (stay order, merits opinion, preliminary injunction, etc.),
- whether it is controlling in the relevant jurisdiction (when knowable).

**Why**:
- Readers overweight “SCOTUS said…” even when the text is a dissent or emergency posture.

**Targets failure modes**: 1, 8.

**Tradeoffs**:
- Requires more legal hygiene and careful phrasing.

**Acceptance criteria**:
- Any “LAWFUL” claim citing a case includes the posture and voice classification.

### 6) Make credence auditable via structured provenance (implement epistemic provenance plan)

**Decision**: Implement `docs/PLAN-epistemic-provenance.md` as a prerequisite for “trustworthy credence,” including:

- `evidence_links` (claim ↔ evidence with locator and rationale),
- `reasoning_trails` (publishable rationale that cites evidence links),
- append-only + supersedes for corrections,
- support for multiple concurrent trails (disagreement by agent/reviewer).

**Why**:
- This is the only scalable way to prevent “confidence theater.”
- It also gives us a clean way to encode reviewer disagreements without overwriting history.

**Targets failure modes**: 8, 9, (and indirectly 1–7).

**Acceptance criteria**:
- Any claim with `credence ≥ 0.7` has ≥1 supporting evidence link with a locator and a reasoning trail referencing it.
- Credence changes are recorded as new trails (append-only), not silent edits.

### 7) Guardrails for “credence bump proposals” (don’t update DB without captured evidence)

**Decision**: Treat reviewer recommendations (including from LLMs) as **inputs to investigation**, not evidence.

Operational rule:

- If a reviewer cites an uncaptured source, we create a “to-ingest” task and do **not** update DB credence until we capture and link it.

**Why**:
- Prevents “citation laundering” where credence changes rely on sources that aren’t in the repo.

**Targets failure modes**: 3, 8, 9.

**Acceptance criteria**:
- DB credence changes can be traced to captured evidence links (not to transcript suggestions).

### 8) Multi-pass workflow definition (repeatable refinement without mixing layers)

**Decision**: Codify a multi-pass analysis/refinement workflow:

1. **Pass A (Extraction)**: extract claims from the source with initial layering and scope.
2. **Pass B (Primary capture)**: capture primary docs for all high-impact claims.
3. **Pass C (Evaluation)**: refine evidence levels/credences based on captured evidence; run disconfirming search.
4. **Pass D (Provenance)**: write evidence links + reasoning trails; record corrections/updates.
5. **Pass E (Review integration)**: incorporate external reviews as competing trails or “open questions,” not as direct evidence.

**Why**:
- Makes iteration structured and keeps provenance clean.

**Targets failure modes**: 1–10.

**Acceptance criteria**:
- Each pass is recorded in the analysis log, with explicit “what changed and why.”

## Implementation Plan (High Level)

This plan spans **templates**, **tooling**, **schema/validation**, and **workflow docs**. We expect it to land in phases to keep changes reviewable.

### Phase 0: Document the contract (docs-only)

- Update workflow docs to formalize layer/actor/scope and correction tracking requirements.
- Define field definitions and minimal scope schema for claim rows.

### Phase 1: Template enforcement (analysis output shape)

- Update analysis templates to add required columns/sections:
  - Key claims table columns (layer/actor/scope/quantifier/evidence-type),
  - claim summary fields,
  - corrections/updates table.
- Update `$check` and `$analyze` skill docs to match new contract.

### Phase 2: Evidence capture tooling (primary docs)

- Add a capture workflow/tooling for PDFs and durable primary artifacts:
  - PDF fetch + hashing + storage in data repo `reference/primary/...`,
  - extraction (text) for searchability,
  - metadata fields: accessed, last_checked, source URL.

### Phase 3: Provenance storage + validation gates

- Implement evidence links + reasoning trails (see `PLAN-epistemic-provenance.md`).
- Add validation rules:
  - high-credence claims require at least one supporting evidence link with locator,
  - corrections/updates must supersede prior links/trails rather than overwrite.

### Phase 4: Review/disagreement ergonomics

- Make it easy to add a reviewer trail without mutating existing credence:
  - import transcript as a “review” source,
  - attach as a reasoning trail with status “proposed” until evidence is ingested.

## Affected Files / Areas (Expected)

Framework repo (this repo):

- `integrations/_templates/tables/key-claims.md.j2` (add Layer/Actor/Scope/etc)
- `integrations/_templates/tables/claim-summary.md.j2` (expand summary)
- `integrations/_templates/skills/check.md.j2` and `integrations/_templates/skills/analyze.md.j2` (contract updates)
- `docs/WORKFLOWS.md` (document multi-pass rigor workflow)
- `docs/SCHEMA.md` (if new fields/tables are added)
- `docs/PLAN-epistemic-provenance.md` (implementation linkages)
- `scripts/validate.py` (future: enforce provenance gates)
- (Potential) `scripts/capture.py` or a new CLI wrapper for primary capture

Data repo (realitycheck-data) expectations:

- `reference/primary/...` (captured PDFs, memos, court orders, PTAs)
- `analysis/sources/...` (updated analyses with new table contract)
- (Future) exports/rendered provenance artifacts if/when added

## Validation / Testing Strategy

This plan introduces behavioral requirements that should be test-driven:

- Unit tests for any new parsing/validation logic in `scripts/validate.py`.
- Golden-file style tests for template rendering (if templates are assembled).
- Validation tests for provenance gates (e.g., “credence ≥ 0.7 requires evidence link”).

## Risks and Tradeoffs

- **Increased friction**: More required fields and capture steps slow analyses. Mitigation: tooling + defaults.
- **Access constraints**: Paywalls/JS blockers limit capture. Mitigation: record constraints; use alternative accessible sources.
- **Storage/licensing**: Capturing full-text articles may raise licensing concerns. Mitigation: prioritize primary public documents; store minimal excerpts when needed; store metadata + locators.
- **False precision**: Adding more fields (claim match, reliability) can invite overprecision. Mitigation: keep scales coarse and require prose rationale.

## Open Questions

All questions from the initial planning pass are resolved in the **Decision Log (D1–D10)** below.

## Appendix: Mapping Reviewer Feedback → Plan Items

- “Capture primary docs (memo PDFs/court orders), not just articles” → Primary-first + capture tooling (Sections 2, 8).
- “Track source corrections; downweight Reason ‘merely filming’ correction” → Corrections/updates system + superseding semantics (Section 3).
- “Enforce ICE vs CBP attribution” → Actor field + table-level enforcement (Section 1).
- “Explicit asserted vs lawful vs practiced split” → Layer field + split rules (Section 1).
- "Ingest uncaptured items (Mobile Fortify PTA, ProPublica/Senate PSI) before credence changes" → Credence bump guardrails + provenance gates (Sections 6, 7).

## Decision Log

This section documents the decision-making process for implementation choices. Each decision includes options considered, analysis, and final resolution.

### D1: Where do Layer/Actor/Scope/Quantifier/Evidence Type live?

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

The plan introduces several new structured fields for claims and evidence:
- **Claim-level fields**: Layer, Actor, Scope, Quantifier
- **Evidence-level fields**: Evidence Type, Claim Match, Court Posture, Court Voice

We need to decide where these fields are stored and enforced.

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Analysis-only** | Required in analysis markdown tables; not stored in DB | No schema changes; fast to ship; iteration is cheap | Not queryable at DB level; can't enforce via `rc-validate`; downstream tooling can't rely on them |
| **B: Claims schema** | Add columns to `claims` table (`layer`, `actor`, `scope`, `quantifier`, `evidence_type`) | First-class in DB; searchable; can enforce with `rc-validate` | Schema migration required; more CLI surface area; couples claim to analysis-time metadata; some fields (evidence_type) describe evidence, not claims |
| **C: Evidence/provenance schema** | Add evidence-specific fields to `evidence_links` / `reasoning_trails`; keep claim-level fields in analysis only | Evidence-specific fields live with evidence (correct domain); claim fields stay flexible | Hybrid approach requires understanding which fields go where; some fields in DB, some not |

#### Analysis

**Claim-level fields (Layer/Actor/Scope/Quantifier)**:
- These describe the claim itself and are useful during analysis
- Primary consumers are human readers of analysis tables
- DB-level queries ("show me all LAWFUL claims") are not a current use case
- Schema stability is valuable; can always promote to DB later if needed

**Evidence-level fields (Evidence Type, Claim Match, Court Posture, Court Voice)**:
- `Evidence Type` describes what kind of evidence is being linked (LAW, MEMO, COURT_ORDER, etc.)—this is a property of the evidence link, not the claim
- `Claim Match` describes how directly this specific evidence supports the claim phrasing
- `Court Posture` and `Court Voice` are relevant only for court document evidence
- These belong on `evidence_links` because one claim can have multiple evidence links with different types

**Codex's input** (2026-01-31):
> "Hybrid: A + C. Enforce Layer/Actor/Scope/Quantifier in analysis tables (the reader-facing interface). Put evidence-specific fields (e.g., evidence_type, claim_match, court_posture, court_voice) on evidence_links/reasoning_trails so DB validation can reason about 'what kind of evidence is this?' without bloating claims. Defer claims schema changes unless we later need DB-side querying/enforcement for Layer/Actor/Scope."

#### Decision

**Hybrid A + C**:
- **Claim-level fields** (Layer, Actor, Scope, Quantifier) → **Analysis tables only** (Option A)
- **Evidence-level fields** → **`evidence_links` table** (Option C)

#### Implementation Details

**Analysis tables** (enforced by templates and `analysis_validator.py`):

| Field | Required | Values |
|-------|----------|--------|
| Layer | Yes | ASSERTED \| LAWFUL \| PRACTICED \| EFFECT |
| Actor | Yes (N/A allowed) | Free-text with canonical suggestions (ICE, CBP, DHS, DOJ, COURT, etc.) |
| Scope | Yes (N/A allowed) | Mini-schema string (see D2) |
| Quantifier | Yes (N/A allowed) | Free-text with canonical suggestions (none, some, often, most, always) |

**`evidence_links` schema additions** (migration required):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence_type` | string | No | LAW \| REG \| COURT_ORDER \| FILING \| MEMO \| POLICY \| REPORTING \| VIDEO \| DATA \| STUDY \| TESTIMONY \| OTHER |
| `claim_match` | string | No | Free-text description of how directly this evidence supports the claim |
| `court_posture` | string | No | stay \| merits \| preliminary_injunction \| appeal \| OTHER (court docs only) |
| `court_voice` | string | No | majority \| concurrence \| dissent \| per_curiam (court docs only) |

#### Rationale

1. **Separation of concerns**: Evidence-level metadata belongs with evidence links, not claims
2. **Schema stability**: Claim-level fields can be enforced without DB changes; promotes to DB later if needed
3. **Queryability where it matters**: DB can answer "does this high-credence claim have LAW-type evidence?" via evidence_links
4. **Flexibility**: Analysis tables can evolve faster than DB schema

#### Migration Path

If we later need DB-level Layer/Actor/Scope/Quantifier:
1. Add optional columns to `claims` schema
2. Update `rc-db import` to populate from analysis tables
3. Add `rc-validate` rules
4. Backfill existing claims from analysis markdown (or leave as NULL for legacy)

---

### D2: Minimal "Scope schema"

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

Claims need structured scope conditions to prevent "scope erasure" (failure mode #6: "can" becomes "can anywhere/always"). The Scope field must capture who/where/when/process/predicate without being so rigid it becomes a burden.

#### Options Considered

| Option | Format | Pros | Cons |
|--------|--------|------|------|
| **Free-text** | Single prose cell | Flexible; no learning curve | Inconsistent; can't validate; easy to skip details |
| **Mini-schema string** | `who=...; where=...; when=...` | Human-readable; loosely validatable; documented convention | Requires discipline; not fully machine-parseable |
| **Structured JSON/YAML** | `{"who": "...", "where": "..."}` | Fully machine-parseable; can validate schema | Hard to read/write in tables; high friction |
| **Multiple columns** | Separate Who, Where, When, Process columns | Most structured; each field explicit | Very wide tables; overkill for many claims |

#### Analysis

**Codex's input** (2026-01-31):
> "Mini-schema string in one Scope column. It's structured enough for consistency, but cheap to write and validate."

**Key considerations**:
- Primary consumers are human readers—readability matters
- Scope requirements vary by claim type (some claims don't need all keys)
- We want consistency without rigidity; can iterate on keys as we learn
- Validation should catch "empty scope on high-impact claims", not parse every field

#### Decision

**Mini-schema string** with documented convention and light validation.

#### Specification

**Format**: Key-value pairs separated by semicolons.

**Canonical keys** (use when applicable):
- `who` — target population (citizens, noncitizens, asylum seekers, final order holders, etc.)
- `where` — location/jurisdiction (interior, border zone, port of entry, home, public space, etc.)
- `when` — timing/conditions (post-notice, emergency, typical processing, etc.)
- `process` — procedural context (expedited removal, removal proceedings, detention, etc.)
- `predicate` — legal predicate (final order, probable cause, warrant, consent, etc.)
- `conditions` — other limiting conditions

**Examples**:
```
who=noncitizens w/ final order; where=interior (not border zone); process=removal proceedings
who=any person; where=within 100mi of border; predicate=reasonable suspicion
who=detained noncitizens; where=ICE detention; when=pre-hearing
N/A
```

**Validation approach**:
- High-impact claims (Layer=LAWFUL, credence≥0.7, E1/E2) must have non-empty Scope (not `N/A`)
- Validator does NOT parse key-value structure (avoids brittle regex)
- Optional future enhancement: WARN if claim mentions populations but `who=` is missing

**Iteration policy**: Key set is intentionally fluid for v1. Add keys as domain needs emerge; document in methodology when patterns stabilize.

---

### D3: Enumerations + enforcement level

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

The new structured fields need stable enumerations to enable consistency and validation. The question is how strictly to enforce these values—too strict creates friction; too loose allows drift.

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Strict enums** | Validator errors on unknown values | Consistency; catches typos; enables reliable queries | Inflexible; blocks edge cases; requires schema changes to add values |
| **Guidance-only** | Canonical values documented but not enforced | Maximum flexibility; no friction | Drift risk; inconsistent data; typos go unnoticed |
| **Hybrid** | Strict enums with escape hatch (`OTHER:<free text>` or `N/A`) | Consistency for common cases; flexibility for edge cases | Requires discipline to not overuse escape hatch |

#### Analysis

**Codex's input** (2026-01-31):
> "Hybrid. Strict for Layer and Quantifier (small sets; high value). Strict-ish for Actor and Evidence Type with OTHER:<...> allowed. Require values for claims where the field matters; allow N/A only when truly not applicable."

**Key considerations**:
- `Layer` is the core methodological distinction—conflating layers is the primary failure mode we're targeting
- `Quantifier` prevents scope erasure but has natural edge cases ("rarely", "nearly all")
- `Actor` and `Evidence Type` need flexibility for new agencies, unusual evidence types
- `OTHER:<...>` pattern forces acknowledgment of going off-script while preserving auditability

#### Decision

**Hybrid enforcement** with varying strictness by field.

#### Specification

| Field | Enforcement | Canonical Values | Escape Hatch |
|-------|-------------|------------------|--------------|
| `Layer` | **Strict** | ASSERTED, LAWFUL, PRACTICED, EFFECT | None (must use one of these) |
| `Quantifier` | **Strict + escape** | none, some, often, most, always | `OTHER:<text>` allowed (e.g., `OTHER:nearly all`) |
| `Actor` | **Guidance + escape** | ICE, ICE-ERO, ICE-HSI, CBP, CBP-BP, CBP-OFO, DHS, DOJ, COURT, STATE/LOCAL, PRIVATE | `OTHER:<text>` allowed; `N/A` for non-actor claims |
| `Evidence Type` | **Guidance + escape** | LAW, REG, COURT_ORDER, FILING, MEMO, POLICY, REPORTING, VIDEO, DATA, STUDY, TESTIMONY | `OTHER:<text>` allowed |

**Validation behavior**:
- Layer: WARN on unknown value (default); ERROR with `--rigor` flag
- Quantifier: WARN if not in canonical set and not `OTHER:<...>` pattern
- Actor/Evidence Type: No enforcement in v1 (guidance only); can tighten later

**`N/A` usage**:
- Allowed when field is genuinely not applicable (e.g., Actor for pure economics claim)
- Should NOT be used to avoid filling in a field that does apply
- High-impact claims (LAWFUL, credence≥0.7) should rarely use `N/A`

**Required for all domains**: Yes. Every claim gets these fields. Use `N/A` only when truly not applicable, not as a default.

---

### D4: High-impact thresholds + primary capture gate severity

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

The "primary-first" rule (Plan section 2) requires capturing primary documents for high-impact claims. We need to define:
1. What triggers "high-impact" status
2. How strictly to enforce capture
3. How to handle cases where capture isn't possible

#### Options Considered

**Threshold rules**:
| Option | Triggers |
|--------|----------|
| **Plan default** | credence ≥ 0.7 OR E1/E2 OR Layer=LAWFUL |
| **Expanded** | Add domain-specific triggers (enforcement powers, broad authority claims) |
| **Minimal** | Only credence ≥ 0.7 |

**Enforcement severity**:
| Option | Behavior |
|--------|----------|
| **WARN default** | Warning by default; ERROR with `--strict`/`--rigor` |
| **ERROR default** | Strict by default (painful during transition) |
| **Process-only** | Documented requirement, not validated |

#### Analysis

**Codex's input** (2026-01-31):
> "Plan thresholds + WARN-by-default, ERROR with --strict. Add an explicit 'capture failed + reason' path so the workflow is realistic (paywalls/JS blockers)."

**Key considerations**:
- Plan thresholds cover the critical cases without being overly broad
- WARN-by-default matches existing `--strict` pattern for high-credence backing
- "Capture failed" escape hatch is essential—not all primary docs are capturable
- Expanding triggers can happen later if needed; start conservative

#### Decision

**Plan thresholds + WARN default + explicit capture-failed path**.

#### Specification

**High-impact claim triggers** (any one qualifies):
1. `credence ≥ 0.7`
2. `evidence_level ∈ {E1, E2}`
3. `Layer == LAWFUL`

**Enforcement**:
- Default: WARN if high-impact claim lacks captured primary evidence
- With `--rigor` flag: ERROR (blocks completion)
- Validator checks: claim has ≥1 supporting evidence link where either:
  - `location` includes an `artifact=...` repo-relative path to a captured artifact (or captured metadata sidecar) **and the referenced file exists**, or
  - `location` includes `capture_failed=<reason>` + `primary_url=...` (explicitly recording why capture was not possible).

**Captured artifact linkage**:

We standardize `evidence_links.location` as a **mini-schema string** (similar to Scope):

```
artifact=<repo-relative-path>; locator=<page/section/lines>; notes=<optional>
```

When capture is not possible:

```
capture_failed=<reason>; primary_url=<url>; fallback=<what was used instead>
```

**Capture-failed documentation**:
When a primary document exists but wasn't captured, record it as `capture_failed=...` in the evidence link `location` (and optionally mirror it in the analysis document’s Corrections & Updates section for human readers).

**Valid capture-failed reasons**:
| Reason | Description |
|--------|-------------|
| `paywall` | Subscription/payment required |
| `js-blocked` | JavaScript-heavy site prevents download |
| `in-person-only` | Requires physical access (courthouse, archive, FOIA) |
| `redistribution-prohibited` | Source explicitly prohibits copying |
| `transient` | Content no longer available (deleted, live stream) |
| `access-restricted` | Login/credentials required (not public) |
| `format-unsupported` | Format we can't reliably capture (video, interactive) |

**Future expansion**: Can add domain-specific triggers (e.g., "any claim about enforcement powers") if plan thresholds prove insufficient.

---

### D5: Copyright/licensing posture for capture

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

The primary-first rule requires capturing documents. We need to define what we're allowed to store and where, balancing:
- Academic rigor and historical archival value
- Fair use protections for research
- Avoiding redistribution of copyrighted material

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Primary-doc-only** | Only capture gov/court/official PDFs | Lowest legal risk | Misses important journalism; incomplete record |
| **Metadata-only for journalism** | URL + date + locators + short quotes | Safe; no redistribution | Can't verify article content later if source changes/disappears |
| **Capture everything** | Full capture of all sources | Complete archival record; academic rigor | Redistribution risk for copyrighted material |
| **Capture + gitignore** | Capture everything; copyrighted material in .gitignored directory | Complete record locally; no public redistribution | Requires discipline; two storage locations |

#### Analysis

**Codex's input** (conservative):
> "Primary-doc-only by default. Store journalism as metadata + locators + minimal excerpts; don't store full article text unless explicitly permitted."

**Human reviewer's position**:
> "We should capture everything—it qualifies as fair use and it's important for historical data. News articles should go in a .gitignored part of the data repo. Future: particularly litigious/controversial items go to a private archivebox-type crawl."

**Key considerations**:
- Fair use doctrine supports research/academic use, especially for verification and criticism
- The risk is *redistribution*, not *possession*—.gitignore solves this
- News articles change, get corrected, or disappear; local capture preserves the record
- Government/legal docs are unambiguously safe to redistribute (public domain/record)
- A complete local archive enables rigorous verification even if not publicly shared

#### Decision

**Capture everything; manage redistribution via storage location**.

#### Specification

**Storage tiers**:

| Tier | Location | Git status | Contents |
|------|----------|------------|----------|
| **Public** | `reference/primary/` | Tracked | Government docs, court filings, official memos, public domain |
| **Captured (metadata tracked)** | `reference/captured/` | Mixed | `*.meta.yaml` tracked; captured content (PDF/HTML/TXT) ignored |
| **Private archive** (future) | External (archivebox) | Not in repo | Particularly litigious or controversial items |

**Capture rules by source type**:

| Source Type | Capture? | Storage Tier | Notes |
|-------------|----------|--------------|-------|
| Statutes, regulations, CFR | ✅ Yes | Public | Public domain |
| Court filings, orders, opinions | ✅ Yes | Public | Public record |
| Agency memos, guidance, PTAs | ✅ Yes | Public | Government works |
| Regulatory filings (SEC, FCC) | ✅ Yes | Public | Public record |
| News articles | ✅ Yes | Captured | Fair use; do not redistribute content |
| Academic papers | ✅ Yes | Captured | Fair use; do not redistribute content |
| Blog posts, commentary | ✅ Yes | Captured | Fair use; do not redistribute content |
| Social media | ⚠️ Case-by-case | Captured | May disappear; ToS varies |

**File structure**:
```
reference/
├── primary/           # Public (tracked in git)
│   └── <source-id>/
│       ├── <sha256>.pdf
│       ├── <sha256>.meta.yaml
│       └── <sha256>.txt (optional extracted text)
├── captured/          # Metadata tracked; content ignored
│   └── <source-id>/
│       ├── <sha256>.meta.yaml
│       ├── <sha256>.pdf (ignored)
│       ├── <sha256>.html (ignored)
│       └── <sha256>.txt (ignored)
└── .gitignore         # Ignores captured content (not metadata)
```

**Metadata sidecar** (`*.meta.yaml`):
```yaml
url: https://example.com/article
content_type: application/pdf
sha256: abc123...
fetched_at: 2026-01-31T12:00:00Z
captured_by: rc-capture
storage_tier: captured  # or "public"
fair_use_basis: research/verification
notes: ""
```

**Fair use rationale** (documented for each capture):
- Purpose: Non-commercial research and verification
- Nature: Factual reporting/analysis
- Amount: Full document (necessary for verification)
- Effect: No market substitution (not redistributed)

**Future: Private archive**:
- For sources with active litigation risk or explicit takedown requests
- Store in external system (archivebox, private S3, etc.)
- Reference by hash in DB; access requires separate credentials

---

### D6: Review/disagreement representation

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

Reviewers (human or LLM) often propose credence changes based on sources not yet captured or reasoning not yet verified. We need a way to:
1. Record these suggestions without immediately adopting them
2. Track disagreements between reviewers
3. Preserve the investigation trail when suggestions are later accepted or rejected

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Notes-only** | Keep reviews outside DB entirely | Simple; no schema changes | No structured tracking; suggestions get lost |
| **CONVO source only** | Store transcript as `sources(type=CONVO)`; no evidence links | Preserves transcript; searchable | No structured link to claims; hard to track what was suggested |
| **Add `proposed` status** | New reasoning_trails status for unverified suggestions | Structured; visible; doesn't affect validation | Schema change; need clear workflow |
| **Full disagreement model** | Separate "reviews" table with voting/resolution | Most structured | Over-engineered for v1 |

#### Analysis

**Codex's input** (2026-01-31):
> "Add reasoning_trails.status=proposed. Treat review suggestions as investigation inputs, not evidence. Ensure proposed trails do not satisfy high-credence backing and do not trigger staleness warnings."

**Key considerations**:
- Reviews are inputs to investigation, not evidence themselves
- `sources(type=CONVO)` already exists for storing transcripts
- Proposed trails create a clean "suggestion → verification → adoption" workflow
- `retracted` status handles explicit withdrawals (distinct from superseding)

#### Decision

**Add `proposed` and `retracted` statuses + formalize review workflow**.

#### Specification

**Schema change** — `reasoning_trails.status` enum:

| Status | Meaning | Satisfies backing? | Triggers staleness? |
|--------|---------|-------------------|---------------------|
| `active` | Currently adopted reasoning | ✅ Yes | ✅ Yes (if old) |
| `superseded` | Replaced by newer trail | ❌ No | ❌ No |
| `proposed` | Suggested; not yet adopted | ❌ No | ❌ No |
| `retracted` | Explicitly withdrawn | ❌ No | ❌ No |

**Review workflow**:

```
1. Receive review feedback (transcript, comments, suggestions)
   ↓
2. (Optional) Store transcript as source
   - rc-db source add --type CONVO --title "Review by [reviewer]" ...
   ↓
3. Create proposed reasoning trail for each suggestion
   - rc-db reasoning add --claim-id X --status proposed --reasoning "Reviewer suggests..."
   - Link to CONVO source if stored
   ↓
4. Investigate: capture cited evidence, verify claims
   ↓
5. If suggestion is validated:
   - Create new `active` trail with captured evidence
   - Original `proposed` trail remains (historical record)

   If suggestion is rejected:
   - Update `proposed` trail to `retracted` with explanation
   - Or leave as `proposed` with note explaining why not adopted
```

**Validation behavior**:
- `proposed` trails do NOT satisfy high-credence backing requirements
- `proposed` trails do NOT trigger "stale reasoning" warnings
- `proposed` trails ARE visible in exports/renders (marked as proposals)
- Claims with only `proposed` trails (no `active`) show as "under review"

**Use cases**:
- LLM reviewer suggests higher credence based on source we haven't captured → `proposed`
- Human reviewer disagrees with current credence → `proposed` with competing reasoning
- Multiple reviewers with different views → multiple `proposed` trails, visible disagreement
- Review suggestion turns out to be wrong → `retracted` with explanation

---

### D7: Evidence Type ↔ Evidence Level guidance

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

Evidence Type (LAW, MEMO, COURT_ORDER, etc.) describes *what kind* of document backs a claim. Evidence Level (E1–E6) describes *how strongly* the evidence supports the claim. We need to clarify the relationship to avoid:
- "Memo exists → E1" (false: memo existing doesn't prove content is lawful)
- "Court said X → high credence" (false: could be dissent, dicta, or unenforced)

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Auto-mapping** | Evidence Type determines E-level | Simple; consistent | False precision; ignores claim-match and layer |
| **Guidance-only** | Evidence Type is descriptive; E-level assigned by analyst | Flexible; requires judgment | Inconsistent if guidance is unclear |
| **Multiple axes** | Replace E-level with type/reliability/match axes | Most accurate | Major redesign; not this task |

#### Analysis

**Codex's input** (2026-01-31):
> "Descriptive only + explicit guidance. Primary legal docs can justify high confidence for ASSERTED ('this memo says X'), but do not automatically justify LAWFUL ('X is lawful') or EFFECT ('X causes Y'). Require court hygiene fields (posture/voice/controlling) when Layer=LAWFUL."

**Human reviewer's insight**:
> "Lawful doesn't mean much if a court makes a decision but it's not enforced."

This reinforces why LAWFUL (what the law says) must stay distinct from PRACTICED (what actually happens). A court ruling that agencies ignore is lawful but not practiced.

#### Decision

**Evidence Type is purely descriptive; E-level guidance is layer-aware**.

#### Specification

**Core principle**: "Capturing a document proves the document exists and what it asserts. It does NOT prove the assertion is lawful, practiced, or has effects."

**Layer-aware E-level guidance**:

| Layer | What E1/E2 requires | What primary docs prove |
|-------|---------------------|------------------------|
| **ASSERTED** | Document exists showing assertion was made | ✅ Memo/filing/statement proves "agency asserted X" |
| **LAWFUL** | Controlling law + majority holding + relevant posture + actually enforced consideration | ⚠️ Document proves law exists; does NOT prove X is lawful in practice |
| **PRACTICED** | Direct observation, data, or reliable reporting of actual behavior | ⚠️ Document proves claim was made; does NOT prove behavior occurs |
| **EFFECT** | Causal evidence (study, data) with confounders addressed | ❌ Document alone cannot establish causal effects |

**Court citation hygiene** (required for LAWFUL claims citing cases):

| Field | Required for LAWFUL? | Values |
|-------|---------------------|--------|
| `court_voice` | Yes | majority, concurrence, dissent, per_curiam |
| `court_posture` | Yes | merits, stay, preliminary_injunction, appeal, emergency |
| Controlling? | Document in reasoning | "Controlling in [jurisdiction]" or "Not controlling / dicta" |

**What this means in practice**:

```
Claim: "ICE can arrest without a warrant" (Layer=LAWFUL)

❌ Wrong reasoning:
   "ICE memo says they can → E1 → credence 0.9"

✅ Correct reasoning:
   "ICE memo asserts this (ASSERTED, E1, 0.9)"
   "8 USC § X authorizes warrantless arrest under conditions Y (LAWFUL, E2, 0.7)"
   "In practice, ICE conducts warrantless arrests in situations Z (PRACTICED, E3, 0.6)"
```

**No auto-mapping**: Validators do NOT enforce Evidence Type → E-level mapping. Guidance is documented in methodology; analysts apply judgment.

---

### D8: EFFECT-layer guardrails (avoid causal leaps)

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

EFFECT claims ("X leads to Y", "Policy causes outcome") are the most prone to epistemic failure:
- "Agency has power" + "Outcome occurred" ≠ "Power caused outcome"
- Correlation ≠ causation
- Confounders are often ignored
- These claims tend to be the most politically charged

We need guardrails without being so restrictive that legitimate causal claims can't be made.

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Disallow EFFECT** | Force causal claims into prose only | Prevents false precision | Loses structured tracking |
| **Hard cap** | EFFECT can't exceed E4/0.5 without study evidence | Strong guardrail | Too rigid; some causal claims are well-supported |
| **Soft guardrails** | Template prompts + validator WARNs | Flexible; educates analyst | Can be ignored |
| **Type-based** | Default EFFECT to `[H]` type | Uses existing system | Still allows high credence if justified |

#### Analysis

**Codex's input** (2026-01-31):
> "Allow with guardrails. Require: mechanism statement + at least one causal-quality evidence link (data/study) + explicit alternative explanations + strict scope. Default EFFECT claims to [H] unless backed by strong causal evidence."

**Key insight**: Using claim type `[H]` (Hypothesis) for EFFECT claims signals "this is a causal hypothesis" rather than "this is established fact." This leverages existing infrastructure.

#### Decision

**Soft guardrails + default to `[H]` type**.

#### Specification

**Requirements for EFFECT claims**:

| Requirement | Where enforced | Behavior |
|-------------|----------------|----------|
| Causal mechanism statement | Template prompt | Analyst must explain *how* X causes Y |
| Scope bounding | `Scope` field | Must specify population/time/jurisdiction |
| Alternative explanations | Template prompt | Must acknowledge confounders |
| DATA/STUDY evidence | Validator | WARN if credence ≥ 0.6 without DATA/STUDY |
| Default type `[H]` | Template/guidance | EFFECT claims should be `[H]` unless strong causal evidence justifies `[F]` |

**Template additions for EFFECT claims**:

```markdown
### Causal Mechanism
[How does X lead to Y? What is the proposed pathway?]

### Alternative Explanations
[What else could explain the observed correlation?]
- Confounder 1: ...
- Confounder 2: ...
- Reverse causation possibility: ...

### Why we believe causation (not just correlation)
[What evidence supports the causal link specifically?]
```

**Validator behavior**:
- WARN: EFFECT claim with `credence ≥ 0.6` but no evidence link with `evidence_type ∈ {DATA, STUDY}`
- WARN: EFFECT claim with empty or `N/A` Scope field
- INFO: EFFECT claim with type `[F]` (remind to verify causal evidence is strong)

**Type guidance**:

| EFFECT claim status | Recommended type |
|--------------------|------------------|
| Causal hypothesis, limited evidence | `[H]` (Hypothesis) |
| Correlation observed, causation plausible | `[H]` with moderate credence |
| Strong causal evidence (RCT, natural experiment, robust data) | `[F]` (Fact) if replicable |
| Speculative causal claim | `[S]` (Speculation) |

**No hard cap**: Credence is not automatically capped. Analyst judgment applies, but guardrails make the reasoning visible and auditable.

---

### D9: Recency metadata (`accessed` vs `last_checked`)

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

Sources change, get corrected, or disappear. We need to track:
- When a source was first accessed (`accessed` — already exists)
- When a source was last verified/re-checked (`last_checked` — missing)

This enables staleness queries and corrections workflows.

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Markdown-only** | Keep recency in analysis prose | No schema change | Not queryable; inconsistent format |
| **Add `sources.last_checked`** | New column in sources table | Queryable; enables staleness reports | Schema migration (minor) |
| **Artifacts table** | Dedicated table for captured artifacts with timestamps | Most structured | Bigger change; overkill for v1 |

#### Analysis

**Codex's input** (2026-01-31):
> "Add sources.last_checked. Keep accessed as 'first accessed'; use last_checked for refresh/corrections tracking. Also store per-artifact fetch time in the primary-doc metadata sidecar if/when capture tooling exists."

**Key considerations**:
- `accessed` and `last_checked` serve different purposes
- Schema migration is simple (add optional string column)
- Capture tooling metadata sidecar (D5) will have `fetched_at` for artifacts
- Enables useful queries: "sources not checked in 90 days"

#### Decision

**Add `sources.last_checked` to schema**.

#### Specification

**Schema change** — `sources` table:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `accessed` | string | No | When source was first accessed (existing) |
| `last_checked` | string | No | When source was last verified for changes (new) |

**Semantics**:
- `accessed`: Set once when source is first cataloged
- `last_checked`: Updated when source is re-verified (corrections check, re-fetch, manual review)

**CLI additions**:
```bash
# Update last_checked
rc-db source update <source-id> --last-checked 2026-01-31

# Find stale sources
rc-db source list --stale-days 90

# Find sources never re-checked
rc-db source list --never-checked
```

**Workflow integration**:
- Corrections workflow updates `last_checked` after verifying source
- Capture tool updates `last_checked` when re-fetching artifacts
- Staleness reports can drive periodic source review

**Capture sidecar** (from D5):
- Per-artifact `fetched_at` in `.meta.yaml`
- Tracks each capture event independently of source-level `last_checked`

---

### D10: Backwards-compatibility + strictness defaults

**Date**: 2026-01-31
**Status**: Resolved
**Participants**: Human reviewer, Claude Opus 4.5, Codex

#### Context

Rolling out new requirements (Layer/Actor/Scope columns, new statuses, capture requirements) risks breaking existing analyses and data repos. We need a transition strategy that:
- Doesn't break existing repos silently
- Provides clear upgrade path
- Allows gradual adoption

#### Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Break immediately** | New requirements are hard errors | Forces adoption | Painful; breaks existing workflows |
| **WARN + flag** | Warnings default; `--rigor` for errors | Gradual; clear upgrade | Two modes to maintain |
| **Dual schema support** | Accept old + new table shapes | Most flexible | Most complex validator logic |

#### Analysis

**Codex's input** (2026-01-31):
> "Dual-support transition. New templates/skills generate the new shape. Validator supports old + new, with warnings until you choose to flip the default."

**Human reviewer's input**:
> "Maintaining compatibility and not making old stuff barf is important. Maybe include realitycheck version in sidecar/frontmatter metadata and audit log for better provenance."

**Key considerations**:
- People run many versions; can't assume everyone upgrades immediately
- `analysis_logs.framework_version` already exists for audit trail
- Capture sidecars should include version for artifact provenance
- Never break existing data repos silently

#### Decision

**Dual-support transition + WARN default + version tracking**.

#### Specification

**Validator behavior**:

| Check | Default | With `--rigor` |
|-------|---------|----------------|
| New table columns missing (Layer/Actor/Scope/Quantifier) | WARN | ERROR |
| Corrections section missing | WARN | ERROR |
| Layer value not in enum | WARN | ERROR |
| Primary capture missing (high-impact claim) | WARN | ERROR |
| EFFECT claim without DATA/STUDY evidence | WARN | WARN |
| Old table format detected | INFO | WARN |

**Dual schema support**:

```python
# analysis_validator.py supports both shapes

# v1 (legacy)
KEY_CLAIMS_HEADERS_V1 = ["#", "Claim", "Claim ID", "Type", "Domain", "Evid", "Credence", "Verified?", "Falsifiable By"]
CLAIM_SUMMARY_HEADERS_V1 = ["ID", "Type", "Domain", "Evidence", "Credence", "Claim"]

# rigor-v1 (new)
KEY_CLAIMS_HEADERS_RIGOR = ["#", "Claim", "Claim ID", "Layer", "Actor", "Scope", "Quantifier", "Type", "Domain", "Evid", "Credence", "Verified?", "Falsifiable By"]
CLAIM_SUMMARY_HEADERS_RIGOR = ["ID", "Type", "Domain", "Layer", "Actor", "Scope", "Quantifier", "Evidence", "Credence", "Claim"]

# Validator accepts either; warns if v1 detected
```

**Version tracking additions**:

| Location | Field | Purpose |
|----------|-------|---------|
| `analysis_logs` | `framework_version` | Already exists; audit trail |
| Capture sidecar | `realitycheck_version` | Track which version captured artifact |
| Analysis frontmatter (optional) | `realitycheck_version` | Track which version generated analysis |

**Capture sidecar** (updated from D5):
```yaml
url: https://example.com/doc.pdf
sha256: abc123...
fetched_at: 2026-01-31T12:00:00Z
captured_by: rc-capture
realitycheck_version: 0.3.0  # NEW
storage_tier: public
```

**Transition timeline**:
1. **v0.3.0**: Ship with WARN-only; document upgrade path; new templates generate rigor format
2. **v0.4.0+**: Consider making `--rigor` default for new projects (existing repos still WARN)
3. **Never**: Force-break existing repos; always support reading legacy format

**CLI flags**:
```bash
# Default: warnings only
rc-validate

# Strict mode: warnings become errors for rigor checks
rc-validate --rigor

# Check what would change
rc-validate --rigor --dry-run
```

**Documentation requirements**:
- CHANGELOG notes for each rigor-related change
- Migration guide: "Upgrading analyses to rigor format"
- Template diff showing v1 → rigor-v1 changes
