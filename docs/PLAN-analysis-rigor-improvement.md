# Plan: Analysis Rigor Improvements (Primary Evidence, Layering, Corrections, Auditability)

**Status**: Planning  
**Created**: 2026-01-25  

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
- `Evidence Type` (LAW/MEMO/COURT ORDER/REPORTING/VIDEO/DATA/TESTIMONY/etc),
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

1. What is the minimal “scope schema” that is expressive but not too burdensome?
2. Should “law/policy primary documents” get a distinct evidence type and/or special E-level mapping?
3. How do we represent “EFFECT” claims without encouraging unsupported causal leaps?
4. What is the best way to store and refresh “last checked” timestamps without excessive overhead?
5. How do we safely handle copyrighted materials while keeping analyses auditable?

## Appendix: Mapping Reviewer Feedback → Plan Items

- “Capture primary docs (memo PDFs/court orders), not just articles” → Primary-first + capture tooling (Sections 2, 8).
- “Track source corrections; downweight Reason ‘merely filming’ correction” → Corrections/updates system + superseding semantics (Section 3).
- “Enforce ICE vs CBP attribution” → Actor field + table-level enforcement (Section 1).
- “Explicit asserted vs lawful vs practiced split” → Layer field + split rules (Section 1).
- “Ingest uncaptured items (Mobile Fortify PTA, ProPublica/Senate PSI) before credence changes” → Credence bump guardrails + provenance gates (Sections 6, 7).

