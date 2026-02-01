# Reality Check v0.3.0 — State of the Union (2026-02-01)

This is a “state of the union” for Reality Check as of **v0.3.0** (released **2026-02-01**). It covers:

- What the framework is *now* (capabilities + contracts)
- What problems v0.3.0 addresses (and what it still doesn’t)
- Relevant prior art: principles, research areas, and adjacent systems
- A shortlist of **lightweight** improvements and **complexity reductions** worth considering next

---

## TL;DR

Reality Check has evolved from “claim extraction + semantic search” into a framework with a credible **epistemic audit trail**:

- **Claims** are explicit objects with type, evidence level, credence, and relationships.
- **Evidence links** and **reasoning trails** turn credence into an auditable judgment (not a vibe).
- **Rigor-v1** analysis tables force critical disambiguations that were previously easy to blur:
  - **Layer**: ASSERTED vs LAWFUL vs PRACTICED vs EFFECT
  - **Actor** attribution, **Scope** discipline, and **Quantifier** control
- **Append-only corrections** (superseding semantics + corrections table) mitigate “analysis drift” as sources change.

The main open frontier is less “more features” and more: **make the structure queryable, reviewable, and synthesizable without bloating the system**.

---

## If you only read a few Reality Check docs

- `docs/WORKFLOWS.md` (the operational contract)
- `docs/SCHEMA.md` (the data model contract)
- `methodology/claim-taxonomy.md` and `methodology/evidence-hierarchy.md` (the epistemic vocabulary)
- `methodology/reasoning-trails.md` (why provenance exists, and how to use it)

---

## What v0.3.0 added (why it matters)

See `docs/CHANGELOG.md` for the full list; the core impact is that the **analysis interface** is now the primary enforcement point.

### 1) Rigor-v1 claim tables (Layer / Actor / Scope / Quantifier)

This directly targets the classic failure mode in real-world analysis: mixing multiple kinds of statements in one “claim” bucket.

- **ASSERTED**: “X said Y.”
- **LAWFUL**: “The law authorizes/requires/prohibits Y.”
- **PRACTICED**: “Y happens in reality.”
- **EFFECT**: “Y causes Z.”

These are related, but they are not interchangeable. Treating them as interchangeable produces *confidence theater*.

### 2) Evidence links grew “evidence typing” fields (rigor-v1)

Evidence is now typed (LAW/REG/COURT_ORDER/…/OTHER) and can store court posture/voice, plus an explicit “claim match” field.

This strengthens two important moves:

- **Primary-first** evidence capture for high-impact claims
- Review workflows where evidence is checked for *what it is*, not just *that it exists*

### 3) Reasoning trails gained review workflow statuses (proposed / retracted)

This is a quiet but important design principle: **reviewer suggestions are not evidence**.

- Proposed changes can be recorded without “contaminating” the official assessment.
- Retraction is explicit and auditable.

### 4) Source staleness tracking and inbox workflow

Reality isn’t static; your analysis shouldn’t silently become wrong.

- `sources.last_checked` creates a minimum viable change-monitoring loop.
- Inbox → reference filing creates a path from “I read a thing” to “I have a stable artifact pointer for evidence.”

---

## Where Reality Check stands today (conceptual model)

Reality Check is (increasingly) an opinionated way to make analysis **inspectable**.

### Core objects (current schema)

See `docs/SCHEMA.md` for canonical fields, but conceptually:

- **Source**: what we looked at (metadata + staleness tracking)
- **Claim**: what is asserted as a proposition (typed, scoped, assigned credence)
- **Evidence link**: “this source supports/contradicts this claim at this location”
- **Reasoning trail**: “here’s why the credence is what it is (including counterarguments)”
- **Chain**: curated argument chain (A → B → C) with weakest-link scoring
- **Prediction**: resolution criteria + status for future claims
- **Analysis log**: audit log for runs/passes, including token usage where available

### Claim chains: what got better, what’s still hard

Reality Check’s chains are deliberately **lightweight** (ordered claim lists + weakest-link scoring). The weakness you likely felt in earlier iterations is that “A → B → C” can smuggle in:

- missing inference steps (“therefore…” handwaves)
- untracked assumptions (the real weakest links)
- category errors (ASSERTED treated as EFFECT)

What v0.3.0 improves is that each step can now be backed by:

- explicit **evidence links** (what in the world supports/contradicts it)
- explicit **reasoning trails** (why the credence is what it is)
- rigor-v1 table fields that block common category errors (Layer/Actor/Scope/Quantifier)

Practical guidance (until/unless you build a richer argument-graph model):

- treat inference steps as first-class claims (often `[A]`, `[H]`, or `[T]`)
- keep chains as a curated “topline path,” but let evidence/reasoning do the heavy lifting

### “Fact vs theory” is not one dimension (it’s at least three)

One reason real-world analysis goes off the rails is that “fact vs theory” gets treated as a single slider. Reality Check is strongest when these axes stay separate:

- **Epistemic Type** (`claims.type`): Fact vs Theory vs Hypothesis vs Prediction vs Assumption, etc.
- **Evidence Level** (`claims.evidence_level`): how strong the evidence is (E1–E6), not “how persuasive the prose is”
- **Rigor Layer** (analysis tables today): ASSERTED vs LAWFUL vs PRACTICED vs EFFECT

The practical heuristic: **EFFECT** claims should usually default to `[H]`/`[T]` unless you have unusually strong causal evidence, and they should surface confounders and alternative mechanisms explicitly.

### The “separation contract” (what must not blur)

The system’s biggest strength is the separation between:

1. **What a source says** (ASSERTED)
2. **What is true under some external standard** (LAWFUL / PRACTICED)
3. **What causes what** (EFFECT)
4. **What we believe and why** (credence + evidence links + reasoning trails)

Reality Check is strongest when it keeps these as distinct layers, even when (especially when) they are tightly related.

---

## Principles and research areas to steal from

Reality Check sits at the intersection of: epistemology, argumentation, provenance, and computational fact-checking. Below are “good theft targets” (ideas that can directly inform product decisions).

### 1) Argumentation theory (structure + attack/support)

Reality Check already models `supports` / `contradicts` relations and reasoning history. This aligns naturally with:

- **Toulmin model** (Claim, Grounds, Warrant, Backing, Qualifier, Rebuttal)
  - Reality Check mapping (roughly):
    - Claim → `claims.text`
    - Grounds/Backing → `evidence_links` (+ `location`, `quote`)
    - Qualifier → `credence`, `Scope`, `Quantifier`
    - Rebuttal → `contradicting_evidence`, `counterarguments_json`
- **Abstract argumentation** (Dung-style “arguments” with attack relations; later extended with support/bipolar variants)
  - Reality Check doesn’t need to implement formal semantics, but the literature gives vocabulary for:
    - what counts as a “counterargument”
    - how to track unresolved objections vs refutations
    - how to represent “this only works if assumption A holds”
- **Argument Interchange Format (AIF)** for interoperable argument graph representations
  - AIF helps clarify what parts of an argument graph are *claims* vs *inference steps* vs *sources*.

Why this matters: it prevents “chains” from turning into unstructured lists and gives you a path to **reviewable reasoning graphs** without overbuilding.

### 2) Provenance as a first-class concept (beyond citations)

In practice, “citation” is too vague to support rigorous review. Provenance work emphasizes:

- explicit source identity
- explicit derivation (“this claim came from this artifact, at this location”)
- explicit responsibility (“who/what asserted this”)

Relevant anchors:

- **W3C PROV** (PROV-DM / PROV-O) — a general-purpose provenance model
- **Nanopublications** — an assertion packaged with provenance + publication info (useful mental model even if you don’t adopt the tech)
- **ORKG** (Open Research Knowledge Graph) — an example of structured claims + provenance over research literature

Why this matters: Reality Check is building “auditable belief objects.” Provenance tooling is the closest existing body of practice for that.

### 3) Evidence assessment and “risk of bias” thinking

Reality Check has an evidence hierarchy (E1–E6). Adjacent bodies of work add practical structure:

- **GRADE**: separates “quality of evidence” from “strength of recommendation,” and forces explicit downgrades (bias, imprecision, indirectness, inconsistency, publication bias).
- **Cochrane-style risk-of-bias** thinking: not everything called “data” should move credence equally.

Why this matters: evidence levels are a strong abstraction, but you can get more reliability by tracking a *small number* of common downgrade reasons (without importing the entire EBM universe).

### 4) Computational fact-checking (tasks, datasets, and failure modes)

Academic fact-checking decomposes into recurring subtasks:

- **claim detection** (“what are the checkable claims?”)
- **evidence retrieval** (documents/sentences that matter)
- **stance classification** (supports/refutes/insufficient)
- **explanation generation** (why)

Key anchors (useful as a map, even if you don’t want to be “a fact-checking model”):

- FEVER (Fact Extraction and VERification)
- SciFact (scientific claim verification)
- ClaimReview (an industry schema for fact-check annotations)
- ClaimsKG and similar aggregation efforts
- Tools like ClaimBuster (claim spotting) illustrate the shape of automation that’s actually helpful

Why this matters: it suggests where automation can be used safely (assistive retrieval/triage) vs where it tends to hallucinate (final verdicts without provenance).

### 5) Forecasting and prediction evaluation (making `[P]` real)

Prediction tracking is rare in knowledge systems, but forecasting research is unusually operational:

- Proper scoring rules (e.g., **Brier score**) enable calibration measurement.
- “Superforecasting” practice emphasizes decomposition, base rates, and update logs.

Why this matters: predictions are where a knowledge base can become self-correcting. The trick is making evaluation cheap and routine.

### 6) Intelligence analysis / structured analytic techniques (SATs)

Reality Check’s “dialectical” stage overlaps with structured techniques designed to reduce cognitive failure modes:

- **Analysis of Competing Hypotheses (ACH)**: forces explicit rival explanations and evidence matrices.
- **Key assumptions check**: enumerates hidden assumptions as explicit review objects.
- **Premortem**: “assume we’re wrong; what failed?”

Why this matters: these are **lightweight lenses** that can be embedded as optional tables/prompts without expanding the DB schema much.

### 7) Causal inference thinking (especially for EFFECT)

If v0.3.0 is about “stop conflating categories,” then causal inference is the next obvious place where analysts unintentionally smuggle in conclusions.

- Treat causal claims as requiring extra structure: confounders, selection effects, measurement issues, and plausible alternative mechanisms.
- Prefer explicit counterfactual framing (“If X were different, would Y change?”) over narrative inevitability.

This doesn’t require building a causal modeling system; it mostly requires **capturing the minimum causal scaffolding** for EFFECT claims so reviews can be concrete.

---

## Related projects to reference

This is not an endorsement list; it’s a “what can we learn from existing ecosystems?” list.

### Historical / predecessor systems (useful for mental models)

- **IBIS / gIBIS** (Issue-Based Information System; early hypertext argument/discourse structuring)
  - Lesson: separating Issues/Positions/Arguments prevents debates from collapsing into freeform notes.
- **Araucaria** (argument diagramming tool)
  - Lesson: diagramming makes implicit inference steps visible, which is crucial for chain review.
- **Compendium** (design rationale / IBIS-informed mapping; now largely “legacy”)
  - Lesson: usability matters; systems fail when capture friction is too high.
- **Truth Maintenance Systems (TMS/ATMS)** (research lineage)
  - Lesson: belief revision needs explicit “support sets” and principled retraction/supersession semantics.

### Currently maintained / active-looking ecosystems (good “reference neighbors”)

Argument mapping / discourse tooling:

- **AIF / AIFdb / OVA+** (argument interchange + hosted argument databases/visualization)
- **Kialo** (debate mapping; closed source but widely used)
- **Argdown** (open text-first argument mapping format + tooling)
- **Carneades** (argumentation system with structured evaluation)

Fact-checking / claim review ecosystems:

- **ClaimReview** (schema used to publish fact-check metadata)
- **Full Fact** (fact-checking org with strong automation orientation)
- **ClaimBuster** (claim spotting / detection)
- **ClaimsKG** (aggregation of fact-check data into a knowledge graph)

Research/literature structure and provenance:

- **Wikidata / Wikibase** (structured statements with references/qualifiers)
- **OpenAlex** (open bibliographic graph; useful for source enrichment)
- **Zotero** (citation management; demonstrates “metadata first” workflows)
- **Hypothes.is** (annotation layer; demonstrates robust quoting/anchoring patterns)
- **ORKG** (structured research contributions/claims)
- **Nanopublication ecosystem** (structured, provenance-attached assertions)

Forecasting:

- **Metaculus** (community forecasting; resolution discipline is instructive)
- **Manifold Markets** (prediction market mechanics; useful for thinking about incentives and resolution criteria)
- **Good Judgment Open** (forecasting community + practice)

---

## Lightweight “easy wins” (high leverage, low complexity)

These are intentionally biased toward changes that improve rigor and synthesis **without** turning Reality Check into a full knowledge-graph platform.

### A) Add a small number of optional “rigor-v1 mirrors” to the DB (query power)

**Problem**: Layer/Actor/Scope/Quantifier live in analysis tables, but the DB can’t easily query them.

**Low-effort win**: add nullable fields on `claims`:

- `layer` (ASSERTED/LAWFUL/PRACTICED/EFFECT/N/A)
- `actor` (string; allow `OTHER:` convention)
- `scope` (string; the mini-schema)
- `quantifier` (none/some/often/most/always/OTHER:/N/A)

This unlocks:

- “Show me all LAWFUL claims with credence ≥ 0.7 lacking LAW/COURT evidence.”
- “Find EFFECT claims whose evidence is mostly REPORTING.”
- Better synthesis filters without LLM assistance.

If you want to keep the schema lean: store these only when known (nullable), treat them as “index fields,” and keep the analysis tables as the primary authoring UI.

### B) Add 3–5 standard “downgrade reasons” for evidence / credence (risk-of-bias lite)

Instead of importing a full evidence appraisal system, track a small controlled vocabulary such as:

- `confounding`
- `selection_bias`
- `measurement_error`
- `incentive_misalignment`
- `indirectness` (evidence doesn’t match claim as stated)

This could live either:

- on `evidence_links` (as tags), or
- in `reasoning_trails` (as part of the rationale structure)

### C) Improve search/synthesis with “review-first” affordances (no new ML required)

The current semantic search is a good base. Easy upgrades tend to be:

- **Filtering**: add `--type`, `--evidence-level`, `--min-credence`, `--max-credence` to search (or a separate `rc-db claim search` with facets).
- **Diversification**: add “MMR-style” diversification for top-N results (avoid near-duplicate results crowding out alternatives).
- **Related-claim views**: `rc-db claim neighbors <id>` (embedding neighbors + explicit relation neighbors).
- **Synthesis skeleton exports**: generate a “claim card” markdown per claim (text + scope + evidence links + latest reasoning trail).

These make the DB meaningfully more usable *without* adding complex inference.

### D) Make “change over time” cheap to maintain

With `sources.last_checked` now available, consider a lightweight loop:

- `rc-db source check <id> --date YYYY-MM-DD` (just records last_checked + optional notes)
- optional later enhancement: compute content hashes for local artifacts and store them in evidence link `location` mini-schema or a new optional field

Goal: cheap “staleness hygiene” rather than ambitious crawling.

---

## Complexity audit: where to streamline vs where to lean in

### Keep / lean in (these are good complexity)

- **Append-only supersession semantics** for evidence and reasoning (auditability)
- **Dual-mode validation** (WARN default + strict flags) for incremental adoption
- **Templates as interface** (the analysis markdown is the human API; keep it stable)

### Watch / streamline (these can quietly explode)

- **Duplicate representations** of relationships:
  - claims have `supports`/`depends_on` lists; chains also contain ordered claims.
  - If both stay, treat one as canonical and define a consistency strategy.
- **Schema drift across versions**:
  - LanceDB schema is fixed; migrations must remain boring and deterministic.
  - Any new fields should be optional, and defaults should preserve old repos.
- **Overloading “credence”**:
  - Credence can become a catch-all for “I like this idea.” The new rigor contract helps; keep pushing toward “credence must be provenance-backed.”

---

## Suggested reading / references (starter set)

Argumentation and discourse:

- Toulmin, *The Uses of Argument* (1958). https://en.wikipedia.org/wiki/The_Uses_of_Argument
- Dung, “On the acceptability of arguments…” (1995). DOI: 10.1016/0004-3702(94)00041-X
- Conklin & Begeman, “gIBIS: A Hypertext Tool for Exploratory Policy Discussion” (1988). DOI: 10.1145/49097.49098
- Argument Interchange Format (AIF). https://en.wikipedia.org/wiki/Argument_Interchange_Format
- AIFdb / OVA+ overview paper. https://eprints.whiterose.ac.uk/114325/

Provenance and structured assertions:

- W3C PROV-O (Provenance Ontology). https://www.w3.org/TR/prov-o/
- W3C PROV-DM (Provenance Data Model). https://www.w3.org/TR/2013/REC-prov-dm-20130430/
- Nanopublications (overview). https://en.wikipedia.org/wiki/Nanopublication
- Nanopublication project site. https://nanopub.net/
- ORKG (Open Research Knowledge Graph). https://orkg.org/

Fact-checking / claim verification:

- ClaimReview (schema used for fact checks). https://developers.google.com/fact-check/tools/markup/claimreview
- FEVER dataset / shared task. https://fever.ai/
- SciFact dataset. https://github.com/allenai/scifact
- ClaimBuster (claim spotting). https://github.com/ClaimBuster/ClaimBuster
- ClaimsKG (fact-check data knowledge graph). https://github.com/claimskg/claimskg

Evidence assessment:

- GRADE handbook (overview). https://gdt.gradepro.org/app/handbook/handbook.html

Forecasting:

- Brier, “Verification of Forecasts Expressed in Terms of Probability” (1950). DOI: 10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2
- Metaculus. https://www.metaculus.com/
- Manifold Markets. https://manifold.markets/
- Good Judgment Open. https://www.gjopen.com/

Structured analytic techniques:

- Heuer, *The Psychology of Intelligence Analysis* (CIA, 1999). https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis/
- Premortem (overview). https://en.wikipedia.org/wiki/Premortem
