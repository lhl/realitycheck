ChatGPT 5.2 Pro (Deep Research)
# https://chatgpt.com/c/697ee645-d460-83a3-b6dc-ce544dbf0039

> I'm working on a new project called Reality Check https://github.com/lhl/realitycheck (sample data here https://github.com/lhl/realitycheck-data) that is an analysis framework for AI agents to do better analysis on any sort of content. This system seems to work well and has had recent upgrades that improves claims checking (originally it was strongest simply as a lens to separate rhetoric from claims, but over real world testing I've been addressing weaknesses. I'm curious to get a full analysis, summary of this tool from the research analyst hat but also, since it's been a sort of first principles style project, I'm interested in what other related projects there are, what core research or other principles we could apply, the academic and theoretical landscape, etc. My background is primarily coming from the knowledge management side of things, but I'm familiar with some past discourse systems - I'm interested in more background/grounding on fact, claims checking, reasoning chains, and anything else that might apply. I'm also interested finally if there are any "lightweight" easy wins we can get for improving our system (eg, additional lenses for our critical analysis, any easy things we might want to track or add to our DB, improving our claims search/synthesis) and also if there's anything that makes sense to streamline or that is redundant (I've been on a sprint adding features, and wanted to review to make sure that we're building something elegant, maintainable, and no more complex than it needs to be).

Here’s what I can infer—and what I’d recommend—from a “research analyst / systems reviewer” angle, based on the public docs in your two repos (framework + sample KB). ([GitHub][1])

## What Reality Check is, in one sentence

Reality Check is an “epistemic ledger” + workflow that lets an AI agent (or a human) turn messy content into **atomic, typed claims** linked to **sources, evidence, and reasoning**, then maintain those claims over time inside a unified, searchable knowledge base. ([GitHub][1])

## What you’ve built (functional summary)

### 1) A knowledge base with a clear ontology (claims, sources, links, trails, predictions, chains)

From the framework README, the core objects and their intent are:

* **Claims**: have IDs, domains, types, evidence levels, credence, relationships, plus “analysis rigor” columns like layer/actor/scope/quantifier. ([GitHub][1])
* **Sources**: registered items (paper/report/article/etc.) that claims can link to. ([GitHub][1])
* **Evidence links**: connect a claim to a specific source location/quote + direction (supporting/refuting) + strength rating. ([GitHub][1])
* **Reasoning trails**: the “why” behind credence assignments (epistemic provenance). ([GitHub][1])
* **Predictions**: future-oriented tracking with falsification criteria/status updates. ([GitHub][1])
* **Argument chains**: dependencies between claims, highlighting weak links. ([GitHub][1])

That ontology is already a big differentiator: most “fact checking” tooling stops at *one-off* verification, while you’re building a durable knowledge system.

### 2) A structured analysis methodology (descriptive → evaluative → dialectical)

You’ve embedded an explicit 3-stage workflow in both docs and automation: descriptive extraction, evaluation, then dialectical (steelman/counters / “what would change my mind”). ([GitHub][1])

That last stage is particularly valuable: it’s closer to *argumentation* and *epistemic humility* than typical “LLM verifier” pipelines.

### 3) Agent integrations + a CLI “thin waist”

Reality Check has a CLI (`rc-db`, plus validation/export tooling) and then multiple “adapters” (plugin/skills) for different agent environments:

* Plugin for Anthropic’s Claude Code, plus skills for OpenAI Codex, Sourcegraph Amp, and OpenCode. ([GitHub][1])

This is good architecture if you keep the CLI + schema as the stable interface and treat everything else as wrappers.

### 4) Semantic search across the claim graph

You’re using LanceDB + embeddings to support “find related claims across the whole KB,” with an explicit embedding model choice and device configuration. ([GitHub][1])

### 5) Evidence hierarchy + claim taxonomy baked into the system

You’ve operationalized:

* Claim types `[F][T][H][P][A][C][S][X]` (fact/theory/hypothesis/prediction/assumption/counterfactual/speculation/contradiction) ([GitHub][1])
* Evidence hierarchy `E1–E6` from strong empirical to unsupported ([GitHub][1])

That explicit taxonomy is a major “first principles” win: it forces the system to distinguish **what kind of statement** something is, not just whether it “sounds true.”

### 6) The sample KB shows the system is actually usable

Your sample data repo shows non-trivial scale (hundreds of claims/sources) and that you’re tracking argument chains + predictions, not just doing one-off checks. ([GitHub][2])

## Strengths (what’s unusually good here)

### A. You’re solving the right problem: “analysis over time,” not “one answer”

Most LLM “fact checking” discussions assume a single interaction. Reality Check assumes real analysis is iterative: claims get revised, superseded, and synthesized.

### B. You’ve separated *representation* from *judgment*

* Representation: atomic claims, IDs, domains, evidence links.
* Judgment: evidence level, credence, reasoning trails.

That separation is what lets you be rigorous without forcing premature certainty.

### C. You’ve created a native home for epistemic provenance

Wiring evidence links + reasoning trails into the core data model is a huge step toward auditable agent reasoning. ([GitHub][1])

### D. “Dialectical” stage is an underused superpower

Your own “framework efficacy” meta-analysis calls out cleaner dialectical modules (steelman/counters, “what would change my mind”). ([GitHub][3])
That’s exactly the kind of structure that reduces motivated reasoning and makes synthesis better.

## Likely failure modes (the ones worth designing against)

### 1) “Checkability” vs “truth”

Realistic fact-checking work points out that **many claims are not checkable**, especially under realistic constraints (e.g., evidence available at the time; evidence simply not on the web). ([arXiv][4])
If your system doesn’t explicitly represent “not checkable / not enough info,” agents will tend to convert uncertainty into bogus precision.

### 2) Credence inflation and calibration drift

If credence is too easy to set and too hard to audit/regress-test, it will drift toward overconfidence—especially when agents generate plausible rationales.

### 3) Over-trusting chain-of-thought style rationales

Research shows CoT explanations can be **systematically unfaithful**—plausible narratives that don’t reflect what drove the model’s output. ([arXiv][5])
Your “reasoning trails” concept is better than raw CoT, but it’s still worth designing trails as *evidence-backed decision logs*, not “verbose thinking.”

### 4) Duplicate / near-duplicate claims and contradiction blindness

At hundreds → thousands of claims, you’ll get:

* duplicates phrased differently
* claims that are conditionally compatible (different scope/time/population) but look contradictory
* true contradictions

If the system doesn’t help users reconcile these, synthesis quality plateaus.

---

# Where this sits in the academic / theoretical landscape

Below are “adjacent pillars” that map cleanly onto what you’re building.

## 1) Automated fact-checking pipelines (NLP)

The mainstream pipeline is typically:

1. **claim detection** → 2) **evidence retrieval** → 3) **veracity prediction** ([arXiv][6])

Reality Check covers (1) and (2) in spirit, but goes beyond by persisting outcomes and linking them into a longer-lived knowledge graph.

Key anchors:

* **FEVER**: large-scale fact extraction & verification benchmark. ([ACL Anthology][7])
* **SciFact / SciFact-Open**: scientific claim verification with evidence/rationales. ([ACL Anthology][8])
* Agentic iteration: **FIRE** argues for iterative retrieve↔verify loops governed by confidence (more like human search). ([ACL Anthology][9])
* “Realistic retrieval” settings emphasize time-bounded evidence and checkability limits. ([arXiv][4])

**Reality Check implication:**
You can borrow evaluation ideas (supported/refuted/NEI; evidence sufficiency; retrieval realism) without turning your project into “just another FEVER model.”

## 2) Argument mining & argumentation theory

Argument mining tries to extract claims/premises/relations from text; surveys emphasize it’s hard precisely because “real reasoning in language is messy.” ([ACL Anthology][10])

Useful theory bridges:

* **Toulmin model** (claim/grounds/warrant/backing/qualifier/rebuttal) is still a practical lens for “what’s missing in this argument.” ([Purdue OWL][11])
* **AIF (Argument Interchange Format)** is a graph-based interchange representation for arguments. ([Centre for Argument Technology][12])
* **IBIS** is a discourse/issue mapping approach for “wicked problems,” representing issues/positions/arguments/references. ([Wikipedia][13])
* Tools like Kialo popularize structured debate trees. ([Kialo][14])

**Reality Check implication:**
Your “argument chains” could evolve toward a Toulmin-ish or IBIS-ish representation *without* turning into a full argument-mining research project. The trick is: keep it optional and layered.

## 3) Provenance / epistemic traceability

Your “evidence links” + “reasoning trails” map directly onto provenance concepts: provenance is information about entities/activities/people used to assess reliability/trustworthiness. ([W3C][15])

The World Wide Web Consortium PROV data model is a canonical reference here. ([W3C][15])

**Reality Check implication:**
You don’t need full PROV compliance, but borrowing *terminology* and a couple of core relations (entity, activity, agent) can make your trails more interoperable and conceptually crisp.

## 4) Evidence grading / evidence synthesis

Your E1–E6 hierarchy resembles evidence-based medicine’s impulse: grade evidence quality, not just “truthiness.” ([GitHub][1])

Nearby standards:

* GRADE Working Group: structured approach for rating certainty of evidence and why it’s downgraded/upgraded. ([Grade Working Group][16])
* Oxford Centre for Evidence-Based Medicine levels of evidence: another well-known evidence hierarchy. ([cebm.ox.ac.uk][17])

**Reality Check implication:**
Your E-levels are a good start; adding a few “GRADE-like dimensions” as lightweight tags (risk of bias, indirectness, inconsistency…) can improve rigor without exploding complexity.

## 5) “Truthfulness / hallucination” evaluation for LLM systems

This space is exploding, and you can borrow parts tactically:

* **RAGAs** explicitly defines “faithfulness” as “all claims in the response are supported by retrieved context,” and computes a 0–1 score. ([arXiv][18])
* **TruLens** focuses on evaluating/tracing agentic workflows with feedback functions (context relevance, groundedness, etc.). ([TruLens][19])
* **LettuceDetect**: lightweight hallucination detection for RAG, highlighting unsupported spans. ([PyPI][20])
* **TruthTorchLM**: library unifying many “truthfulness prediction” approaches + calibration tooling. ([truthtorchlm.com][21])

**Reality Check implication:**
These are less about “building a KB” and more about **evaluating** whether an agent output is grounded. That’s perfect for your pipeline QA.

## 6) Reasoning chains and why you should be careful

CoT can be misleading as interpretability, and papers argue it’s neither necessary nor sufficient for trustworthy explainability. ([Oxford Martin AIGI][22])

But there *are* methods that improve reliability of reasoning outputs:

* **Self-consistency**: sample multiple reasoning paths and aggregate. ([arXiv][23])
* **Tree of Thoughts**: search over reasoning paths with evaluation/backtracking. ([arXiv][24])

**Reality Check implication:**
Use “multi-path reasoning” internally to *decide* what to register; store a compact, evidence-linked trail rather than raw verbose thought.

---

# Lightweight “easy wins” that fit your current system

I’ll focus on low-effort additions that improve rigor and reduce long-run complexity.

## 1) Add an explicit “Checkability / Verdict state” field for claims

Right now, you have evidence level + credence, which is great—but you’ll benefit from a discrete state like:

* **SUPPORTED**
* **REFUTED**
* **MIXED / DEPENDS**
* **NOT ENOUGH INFO**
* **NOT CHECKABLE** (in principle or in practice)
* **STALE / TIME-SENSITIVE** (true at time t, unknown now)

Why: realistic fact-checking settings emphasize that many claims can’t be checked with available evidence, and systems should emphasize evidence returned, not just label accuracy. ([arXiv][4])

This single field prevents agents from “hallucinating certainty” by forcing a state that matches evidence availability.

## 2) Canonicalize claims into a structured “claim frame” (but keep it minimal)

You already added Layer/Actor/Scope/Quantifier columns—excellent. ([GitHub][1])
The next easy step is to add a “canonical form” that helps dedupe and detect contradictions:

* **subject / entity** (who/what)
* **predicate** (what relation)
* **object/value** (what outcome/value)
* **time** (as-of / during / forecast horizon)
* **population / scope** (who it applies to)
* **units** (if numeric)

Even if it’s imperfect, it enables:

* duplicate detection (“same claim, different phrasing”)
* conditional compatibility (“contradiction” vs “different scope”)
* better synthesis (“group claims by predicate & subject”)

This is also a bridge to Toulmin-style analysis (qualifiers, rebuttals). ([Purdue OWL][11])

## 3) Add 3–5 “GRADE-like” evidence-quality tags (don’t overbuild)

Keep your E1–E6 hierarchy. ([GitHub][1])
Add lightweight tags that explain *why* an E-level is what it is:

* **risk_of_bias** (low/med/high/unknown)
* **indirectness** (direct vs proxy)
* **inconsistency** (conflicting studies?)
* **imprecision** (wide uncertainty / small n)
* **publication_bias** (suspected?)

These map to well-known evidence grading practice. ([Medwave][25])

You don’t need the full GRADE process—just the dimensions as “analysis breadcrumbs.”

## 4) Make evidence links first-class “quotable, locatable” objects everywhere

You already have evidence links with location/quotes/strength. ([GitHub][1])
Easy win: enforce (via validation) that any claim above some threshold must have:

* ≥1 supporting link with quote + location
* ≥1 counterevidence link if claim is controversial/high-impact (optional rule)

This turns `rc-validate` into a genuine “rigor gate” rather than a schema checker. ([GitHub][1])

## 5) Add “review cadence” metadata

Long-lived KBs rot. Add fields like:

* `last_reviewed_at`
* `review_interval` (or `review_due_at`)
* `staleness_risk` (low/med/high)

Then your inbox workflow becomes a **maintenance engine**, not just an ingestion engine. Your repo already frames the KB as something you maintain over time. ([GitHub][1])

## 6) Borrow evaluation metrics from RAG tooling to regression-test your agent workflows

If `/reality:check` fetches → analyzes → registers → validates, you can create a lightweight “golden set” of 20–50 sources and track:

* extraction completeness (how many key claims extracted)
* grounding (are evidence links real / do quotes match)
* “faithfulness” style metrics (claims supported by retrieved context) ([Ragas][26])

This is the easiest path to measurable improvement without inventing new theory.

## 7) Add “confidence-driven iterative retrieval” for claim checking

Your system already supports semantic search + evidence links. ([GitHub][1])
A low-effort algorithmic improvement inspired by FIRE:

* verify claims with **K** evidence docs
* if confidence < threshold, generate a refined query and retrieve more
* stop when confidence sufficient or budget reached ([ACL Anthology][9])

This can dramatically reduce wasted retrieval and improve evidence quality.

## 8) Surface “What would change my mind?” as a required dialectical artifact for important claims

Your meta doc calls this out as a good module. ([GitHub][3])
Operationalize it:

* For claims with high impact *or* high uncertainty, store:

  * what evidence would move credence by ≥X
  * what observation would falsify it
  * what alternative hypothesis is plausible

This is a structured analytic technique vibe (key assumptions / alternative hypotheses) without heavy formalism. ([IALEIA][27])

---

# Streamlining & redundancy review (how to keep it elegant)

Based on your README, the system already has multiple interfaces (CLI + plugin + skills across agents) and multiple artifacts (DB + analysis docs + audit logs). ([GitHub][1])
That’s powerful, but here’s how it can get messy—and what to do.

## 1) Establish a “single source of truth” rule for each kind of information

A clean approach:

* **DB is canonical** for structured facts: claims, sources, evidence links, credence history.
* **Markdown analysis documents** are canonical for human narrative & interpretive synthesis (but should reference claim IDs).
* **Exports** are derived artifacts, never edited manually.

If you already follow this implicitly, make it explicit in docs, because it prevents drift.

## 2) Generate integrations from one command spec (avoid drift across Claude/Codex/Amp/OpenCode)

You’ve got:

* Claude plugin commands (`/reality:*`)
* Codex skills (`$check`, `$realitycheck`)
* Amp and OpenCode skills ([GitHub][1])

These are easy to let diverge.

Easy win: define **one** “capability manifest” (a declarative spec) from which you generate:

* help text
* integration wrappers
* docs tables

This is the classic “thin waist” architecture: keep the CLI stable; auto-generate adapters.

## 3) Watch for versioning confusion (it’s already visible)

Your README “Status” calls out v0.3.0, but the repo UI section shows a latest release tag of v0.1.7 (dated January 26, 2026). ([GitHub][1])
That mismatch is a small paper cut that signals “possible drift” to users.

Easy win: make **pyproject version / tags / README status** consistent.

## 4) Keep the schema intentionally small; make “lenses” composable checklists

You’re explicitly adding “lenses” and columns—good. The risk is schema bloat.

Rule of thumb:

* Add a field only if it enables:

  * validation (prevent errors),
  * retrieval (better search),
  * synthesis (better grouping), or
  * maintenance (review cycles).

Everything else should be a lens/checklist *inside analysis docs* rather than a DB field.

## 5) Add “claim lifecycle” states to support maintainability

Your inbox workflow is great for ingestion; add lifecycle states for claims:

* drafted → registered → reviewed → contested → deprecated/superseded

This reduces redundant “where do I track this?” notes scattered across docs.

---

# A “next 2 weeks” upgrade path that’s still lightweight

If I were trying to improve rigor *without* adding complexity:

1. **Add claim verdict/checkability state** + enforce it in validation. ([arXiv][4])
2. **Implement claim canonical frames** (minimal subject/predicate/object/time/scope/units) for dedupe + contradiction detection.
3. **Introduce 3–5 evidence quality tags** (GRADE-inspired) without changing the E-levels. ([CDC][28])
4. **Add regression tests for analysis workflows** using RAG-style groundedness/faithfulness metrics. ([Ragas][26])
5. **Unify integration specs** so plugin/skills stay consistent. ([GitHub][1])

If you do only these, you’ll get a noticeable jump in:

* fewer uncheckable claims being “over-scored”
* less duplicate noise
* more auditable evidence assignments
* better long-run maintainability

---

If you want, I can also draft a concrete “schema delta” (fields + validation rules) and a minimal “lens pack” (a short, repeatable checklist for evaluative + dialectical stages) that fits your existing claim taxonomy and evidence hierarchy—no new moving parts, just clearer defaults.

[1]: https://github.com/lhl/realitycheck?utm_source=chatgpt.com "lhl/realitycheck: A framework for rigorous, systematic ..."
[2]: https://github.com/lhl/realitycheck-data "https://github.com/lhl/realitycheck-data"
[3]: https://github.com/lhl/realitycheck-data/blob/main/analysis/meta/framework-efficacy-greenland-test.md "https://github.com/lhl/realitycheck-data/blob/main/analysis/meta/framework-efficacy-greenland-test.md"
[4]: https://arxiv.org/pdf/2305.11859 "https://arxiv.org/pdf/2305.11859"
[5]: https://arxiv.org/abs/2305.04388 "https://arxiv.org/abs/2305.04388"
[6]: https://www.arxiv.org/pdf/2408.14317 "https://www.arxiv.org/pdf/2408.14317"
[7]: https://aclanthology.org/N18-1074/ "https://aclanthology.org/N18-1074/"
[8]: https://aclanthology.org/2020.emnlp-main.609/ "https://aclanthology.org/2020.emnlp-main.609/"
[9]: https://aclanthology.org/2025.findings-naacl.158.pdf "https://aclanthology.org/2025.findings-naacl.158.pdf"
[10]: https://aclanthology.org/J19-4006/ "https://aclanthology.org/J19-4006/"
[11]: https://owl.purdue.edu/owl/general_writing/academic_writing/historical_perspectives_on_argumentation/toulmin_argument.html "https://owl.purdue.edu/owl/general_writing/academic_writing/historical_perspectives_on_argumentation/toulmin_argument.html"
[12]: https://www.arg-tech.org/wp-content/uploads/2011/09/aif-spec.pdf "https://www.arg-tech.org/wp-content/uploads/2011/09/aif-spec.pdf"
[13]: https://en.wikipedia.org/wiki/Issue-based_information_system "https://en.wikipedia.org/wiki/Issue-based_information_system"
[14]: https://www.kialo-edu.com/ "https://www.kialo-edu.com/"
[15]: https://www.w3.org/TR/prov-dm/ "https://www.w3.org/TR/prov-dm/"
[16]: https://www.gradeworkinggroup.org/ "https://www.gradeworkinggroup.org/"
[17]: https://www.cebm.ox.ac.uk/resources/levels-of-evidence/ocebm-levels-of-evidence "https://www.cebm.ox.ac.uk/resources/levels-of-evidence/ocebm-levels-of-evidence"
[18]: https://arxiv.org/abs/2309.15217 "https://arxiv.org/abs/2309.15217"
[19]: https://www.trulens.org/ "https://www.trulens.org/"
[20]: https://pypi.org/project/lettucedetect/ "https://pypi.org/project/lettucedetect/"
[21]: https://www.truthtorchlm.com/ "https://www.truthtorchlm.com/"
[22]: https://aigi.ox.ac.uk/wp-content/uploads/2025/07/Cot_Is_Not_Explainability.pdf "https://aigi.ox.ac.uk/wp-content/uploads/2025/07/Cot_Is_Not_Explainability.pdf"
[23]: https://arxiv.org/abs/2203.11171 "https://arxiv.org/abs/2203.11171"
[24]: https://arxiv.org/pdf/2305.10601 "https://arxiv.org/pdf/2305.10601"
[25]: https://www.medwave.cl/revisiones/metodinvestreport/8109.html?lang=en "https://www.medwave.cl/revisiones/metodinvestreport/8109.html?lang=en"
[26]: https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/faithfulness/ "https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/faithfulness/"
[27]: https://www.ialeia.org/docs/Psychology_of_Intelligence_Analysis.pdf "https://www.ialeia.org/docs/Psychology_of_Intelligence_Analysis.pdf"
[28]: https://www.cdc.gov/acip-grade-handbook/hcp/chapter-7-grade-criteria-determining-certainty-of-evidence/index.html "https://www.cdc.gov/acip-grade-handbook/hcp/chapter-7-grade-criteria-determining-certainty-of-evidence/index.html"

> As we scale we should be thinking about reconcilliation, revisiting claims/evidence for drift (new evidence, updates etc) - we are in effect building our own "world model" as time goes on which of course has the risk of drifting from reality (with the added danger in terms of solipism of being "logically complete". As we scale this, how do we maintain our humility and our flexibility (something that both humans and LLMs are notoriously bad at)?

You’re naming the core scaling risk correctly: once you have a large, internally consistent claim graph, it’s *very* easy for both humans and LLMs to start treating it like a closed world—where “everything important is already in here,” and where coherence starts substituting for contact with reality.

I’d frame the goal as: **make “being wrong” cheap, routine, and measurable**, and make “being logically complete” *impossible without ongoing external pressure*.

Below is a set of design principles + concrete mechanisms that tend to work in practice. I’ll anchor a few ideas in prior art from (a) truth maintenance/belief revision, (b) intelligence analysis tradecraft, and (c) forecasting calibration.

---

## 1) Treat humility as an engineered property, not a virtue

In systems terms, humility emerges when you have:

1. **Representation that can hold uncertainty + contradiction**,
2. **Processes that systematically seek disconfirmation**, and
3. **Incentives/metrics that reward calibration and updating**, not rhetorical certainty.

Humans are prone to overconfidence and biased evidence evaluation; just “being aware” doesn’t reliably fix it—process and structure are what help. ([bear.warrington.ufl.edu][1])
And LLMs can be *especially* overconfident in uncertain territory, so you can’t rely on “ask the model to be humble” as your control surface. ([arXiv][2])

---

## 2) Representation-level humility: make the KB able to be “incomplete and inconsistent” on purpose

### A. Don’t force global consistency; manage inconsistency explicitly

A classic AI result here is the **assumption-based truth maintenance system (ATMS)** idea: keep track of *which assumptions/evidence sets support which conclusions*, and allow inconsistencies without collapsing the whole belief set. This lets you retract or revise locally when an assumption breaks. ([ScienceDirect][3])

**Reality Check translation:**

* Keep contradictions **first-class**, not as “errors to eliminate.”
* Make “contexts” cheap: a claim can be supported in one evidence context and not in another.
* Track *support sets* (minimal evidence bundles) so you can see fragility: “this claim only stands if Source A and Source B are reliable.”

This is the antidote to solipsistic completeness: the system is allowed to say “these are mutually incompatible; we’re holding both until resolved,” rather than manufacturing a single tidy story.

### B. Make “unknown / not-checkable” a stable resting state

You want the KB to be comfortable with **NEI** (not enough information) and **not checkable** as *end states*, not as temporary shame.

Why this matters: fact-checking research in “realistic” settings emphasizes that many claims can’t be checked with available evidence; good systems surface evidence and uncertainty rather than pretending every claim has a crisp verdict. ([PubMed][4])

**Implementation move:** add an explicit “verdict state” orthogonal to credence:

* supported / refuted / mixed / **not enough info** / **not checkable** / time-bounded (true-as-of)

Then enforce: the agent is *allowed* (and sometimes required) to stop at NEI.

### C. Time-index everything (and embrace “truth at time t”)

Drift is often not “wrong → right,” but “right in 2021 → obsolete in 2026.”

Borrow the mindset of **living systematic reviews**: continual surveillance for new evidence + periodic incorporation to keep conclusions current. ([Jclinepi][5])

**Concrete DB fields that buy humility:**

* `as_of_date` (the time the claim asserts)
* `last_verified_at`
* `review_due_at` (or `review_interval`)
* `staleness_risk` / `domain_half_life`

Then you can show “confidence-with-age”: if a claim hasn’t been rechecked, its credence shouldn’t silently remain high.

---

## 3) Process-level humility: force systematic disconfirmation and alternative models

### A. Bake in disconfirming search as a *required step*, not a nice-to-have

For any nontrivial claim, require:

* one retrieval pass optimized for support
* one retrieval pass optimized for **refutation / disconfirmation**

This is essentially the “opponent model” idea: the KB should be adversarial to itself.

### B. Use structured analytic techniques to keep multiple hypotheses alive

In intelligence analysis, a core technique is **Analysis of Competing Hypotheses (ACH)**—explicitly enumerating plausible hypotheses and weighing evidence by how it *disconfirms* each, not how it confirms your favorite. This was designed specifically to counter confirmation bias and premature closure. ([CIA][6])

**Reality Check translation (lightweight):**
For any synthesis claim, store:

* the top 2–5 alternative hypotheses
* the “best disconfirming evidence we have” against each
* which missing evidence would discriminate between them

This keeps “flexibility” alive because the KB never collapses to a single narrative without documenting what it would take to change it.

### C. Turn important beliefs into time-bounded predictions whenever possible

This is the strongest anti-solipsism lever you can add, because reality gets a vote.

Forecasting research (e.g., geopolitical forecasting tournaments) uses **proper scoring rules** like the **Brier score** to measure calibration and accuracy. Brier score explicitly rewards honest probabilities and punishes overconfidence. ([Stanford University][7])

**Practical pattern:**

* If a claim matters and is uncertain, try to express a piece of it as a prediction with a resolution date.
* Track Brier score (or calibration curves) per agent, per domain, per time period.
* Use that score to *adjust* how much you trust future credence assignments from that agent/workflow.

This is how you keep humility from being just a vibe: it becomes measurable.

---

## 4) Drift management: treat “knowledge drift” like “concept drift”

ML has a whole literature on **concept drift**: when the relationship between inputs and outcomes changes over time, models degrade unless you detect and adapt. ([ACM Digital Library][8])

Your KB is similar: the “mapping” from evidence → belief changes as new evidence arrives or the world changes.

### A. Build a “reconciliation queue” driven by triggers

Instead of “occasionally revisit things,” make revisiting automatic when triggers fire:

**Trigger types**

1. **New evidence**: newly ingested sources semantically close to an existing claim cluster.
2. **Source change**: corrections, retractions, updated stats, revised report versions.
3. **Time decay**: claim reached review_due_at.
4. **Contradiction emergence**: new claim conflicts with entrenched claim.
5. **High-impact/decision-linked**: anything used in a downstream decision or synthesis doc.

This converts drift from a vague worry into a manageable backlog.

### B. Store “dependency graphs” so re-evaluation is localized

If you can answer: “If Source X is wrong, what breaks?” you avoid global re-analysis.

This again maps to truth maintenance: conclusions are attached to support sets; retracting a support set causes local revisions rather than ideological collapse. ([ScienceDirect][3])

---

## 5) Belief revision rules: make updating principled and boring

Belief revision theory (AGM-style) studies how a rational agent should revise beliefs given new information—often emphasizing *minimal change* plus something like an “entrenchment” ordering (which beliefs are harder to give up). ([Franz Huber][9])

You don’t need formal logic to benefit from this. You need a few heuristics:

### A. Maintain an “entrenchment” score per claim

Entrenchment is “how hard should it be to move this belief?”

Compute it from:

* evidence strength/quality
* number of independent evidence lines
* replication
* recency
* directness (primary vs secondary)
* past predictive performance of that claim cluster (if applicable)

Then, when contradictions occur:

* **Prefer revising the least entrenched claim first**
* Or split the claim (scope/time/population) until compatibility becomes clear

### B. Keep revision history explicit

Humility improves when “I changed my mind” is easy and visible.

Track:

* old credence
* new credence
* what evidence caused the change
* which dependencies changed

This is not just accountability—it reduces the psychological cost of updating for both humans and agents.

---

## 6) LLM-specific guardrails against “confident closure”

Given evidence that LLM confidence can be systematically biased, especially under uncertainty, you want to avoid “one model confidently judges itself.” ([arXiv][2])

### A. Separate roles (even if it’s the same base model)

Use role separation patterns:

* Extractor (pull claims)
* Retriever (find evidence)
* Checker (verify quotes/locators + adversarial search)
* Synthesizer (write narrative)
* Auditor (spot weak links / missing alternatives)

Even if these are all the same LLM, role separation with different prompts/tools reduces single-thread motivated reasoning.

### B. Require “disconfirming evidence search” before allowing high credence

Hard gating rule (example):

* Credence cannot exceed 0.7 unless at least one disconfirming search was performed and logged, even if it found nothing.

### C. Prefer *structured* reasoning trails over free-form chains

Free-form rationales are easy to produce and can be misleading; a better “trail” is:

* claim → evidence links (with quotes/locators) → inference type → uncertainty notes

That keeps the model grounded in artifacts you can audit.

---

## 7) Dashboards that operationalize humility

Humility at scale needs UX. A few dashboards that keep you honest:

1. **Staleness debt**

* % of claims past review_due_at, weighted by importance
* biggest stale clusters

2. **Fragility index**

* claims supported by only one source
* claims dependent on low-quality evidence

3. **Contradiction heatmap**

* unresolved contradictions by domain / claim cluster
* “minimal inconsistent sets” if you implement ATMS-like support sets ([ScienceDirect][3])

4. **Calibration scoreboard**

* Brier score by agent/workflow/domain over time ([Stanford University][7])

5. **NEI inventory**

* high-impact claims stuck at “not enough info”
* this is your “unknowns you must not paper over”

These dashboards prevent “logical completeness” because they keep pointing to the edges: what’s stale, fragile, contradictory, or unknown.

---

## 8) Five “cheap but high-leverage” additions that directly support humility

If you do nothing else, I’d prioritize these:

1. **Verdict/checkability state** (NEI, not-checkable, time-bounded) as first-class.
2. **Review cadence + time-indexing** (as-of, last-verified, due date), inspired by living evidence practice. ([Jclinepi][5])
3. **Entrenchment score** + a default contradiction resolution heuristic (revise least entrenched / split scope). ([Franz Huber][9])
4. **Forced disconfirming retrieval** (logged) before high credence or synthesis sign-off; ACH-lite for major questions. ([CIA][6])
5. **Prediction + scoring** for key uncertain beliefs (Brier), with calibration-based trust weighting. ([Stanford University][7])

---

## A mindset that helps: “world model as a portfolio of hypotheses”

The cleanest conceptual shift is: you’re not building *the* world model. You’re building a **portfolio of hypotheses with tracked evidence, time bounds, and explicit unknowns**.

That portfolio:

* can contain contradictions
* can degrade with age
* is routinely stress-tested by disconfirming search
* is evaluated by predictions that cash out against reality

That combination is what keeps both people and agents flexible without relying on “just try to be humble.”

If you want, I can propose a concrete reconciliation workflow (states, triggers, and DB fields) that fits your current schema and is implementable as a small set of `rc-validate` rules + a “reconciliation queue” command.

[1]: https://bear.warrington.ufl.edu/brenner/papers/brenner-obhdp1996.pdf?utm_source=chatgpt.com "Overconfidence in Probability and Frequency Judgments"
[2]: https://arxiv.org/html/2505.02151v2 "Large Language Models are overconfident and amplify human biasWe thank Chenrui Wang for excellent research assistance. We are grateful for comments from participants at seminars at the National University of Singapore, the University of Melbourne, Osaka University, Beijing Jiaotong University, the Stockholm School of Economics, the University of California - San Diego, the Herie School, and the University of Hong Kong. The first authorship is shared between Fengfei Sun and Ningke Li. Correspondence should be addressed to Kailong Wang (wangkl@hust.edu.cn) and Lorenz Goette (ecslfg@nus.edu.sg)"
[3]: https://www.sciencedirect.com/science/article/pii/0004370286900809?utm_source=chatgpt.com "An assumption-based TMS"
[4]: https://pubmed.ncbi.nlm.nih.gov/34550587/?utm_source=chatgpt.com "Living Systematic Reviews"
[5]: https://www.jclinepi.com/article/S0895-4356%2817%2930636-4/fulltext?utm_source=chatgpt.com "Living systematic review: 1. Introduction—the why, what, ..."
[6]: https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf?utm_source=chatgpt.com "Psychology of Intelligence Analysis"
[7]: https://web.stanford.edu/~knutson/jdm/mellers15.pdf?utm_source=chatgpt.com "Identifying and Cultivating Superforecasters as a Method of ..."
[8]: https://dl.acm.org/doi/10.1145/2523813?utm_source=chatgpt.com "A survey on concept drift adaptation"
[9]: https://huber.artsci.utoronto.ca/wp-content/uploads/2013/07/Belief-Revision-I-The-AGM-Theory.pdf?utm_source=chatgpt.com "Belief Revision I: The AGM Theory - Franz Huber"

> Sure let's propose the reconciliation workflow. Let's also explicitly think about staleness, etc. LLMs in particular have a huge time bias (unusually fixed in their training priors, have a hard time sometimes even accepting current events (or for some LLMs, that they are functioning in the present and not in their training cutoff!)) so that's also something that I want to make sure our framework is particularly careful about (temporal drift, overriding eveidence etc)

Below is a concrete **Reconciliation Workflow v1** that fits the primitives you already have (claims, sources, evidence links, reasoning trails, analysis logs, contradictions, predictions), and adds *just enough* structure to make staleness + temporal drift visible and actionable—especially given LLM “time bias”.

I’ll describe:

1. the **queue model** (what gets revisited and why),
2. the **re-check protocol** (what “reconciliation” actually does),
3. a **staleness policy** (how to compute “review due”), and
4. **temporal guardrails** that specifically counter LLM cutoff/nostalgia behavior.

I’ll also point out where this maps to your existing schema/commands. ([GitHub][1])

---

## 0) What reconciliation is in Reality Check terms

“Reconciliation” = **a repeatable update pass** over an existing belief region of the KB that:

* checks whether sources changed (or new evidence emerged),
* reweighs evidence (including recency),
* updates claim versions/credence with a new reasoning trail,
* supersedes or retracts evidence links as needed,
* resolves contradictions (or makes them explicit + time-scoped),
* evaluates predictions that have reached their resolution window.

You already have the right storage primitives for this:

* **Claims** are versioned and timestamped (`version`, `last_updated`, `first_extracted`). ([GitHub][1])
* **Sources** have `last_checked` for “verified for changes” (rigor-v1), and can store reliability. ([GitHub][1])
* **Evidence links** have `status` and `supersedes_id`, plus `location` and `quote` for pinning. ([GitHub][1])
* **Reasoning trails** have `supersedes_id`, `credence_at_time`, and can store counterarguments. ([GitHub][1])
* **Contradictions** are first-class with `status` and `conflict_type`. ([GitHub][1])
* **Analysis logs** already support multi-pass auditing + “claims updated” attribution. ([GitHub][1])

So the main missing ingredient is: **a disciplined queue + time-aware gating.**

---

## 1) Reconciliation Queue (how work gets generated)

### 1.1 Task types (minimal set)

Create a conceptual “reconciliation task” type (can be *derived* on the fly at first—no new table required):

1. **SOURCE_REFRESH**
   Triggered when a source is “due” for re-check based on its type + volatility, using `sources.last_checked`. ([GitHub][1])

2. **CLAIM_REVIEW**
   Triggered when a claim is stale, fragile, or high-impact (details below).

3. **CONTRADICTION_REVIEW**
   Triggered when `contradictions.status=open` or a new contradiction is detected. ([GitHub][1])

4. **PREDICTION_EVAL**
   Triggered when `now >= predictions.target_date` and it’s not recently evaluated. ([GitHub][1])

5. **DUPLICATE_OR_SCOPE_SPLIT**
   Triggered by embedding similarity clusters or repeated “same claim with different time scopes.” (You already store embeddings on claims/sources for semantic search. ([GitHub][1]))

You can implement (1)–(4) immediately with your existing schema; (5) is optional but becomes important as you scale.

---

### 1.2 How tasks get prioritized

Compute a priority score from four multipliers:

**Priority = Impact × Staleness × Fragility × Volatility**

* **Impact**

  * claim participates in a chain (`part_of_chain`) ([GitHub][1])
  * claim has many dependents (`supports`, `depends_on`, etc.) ([GitHub][1])
  * claim has high credence (because wrong-high-confidence is expensive)

* **Staleness**

  * “last epistemic touch” is old
  * key sources are old / unchecked / changed
  * domain/type half-life says it should be revisited

* **Fragility**

  * claim has few evidence links
  * evidence links are weak or low-reliability sources
  * reasoning trail cites assumptions heavily

* **Volatility**

  * source type is `ARTICLE`/`SOCIAL` vs `PAPER`/`DATA` (your `sources.type` supports this) ([GitHub][1])
  * claim topic is time-sensitive (politics, “current CEO”, “latest benchmark results”, etc.)

A nice property: **you don’t have to guess “importance” perfectly**—the dependency graph + chain membership naturally surfaces what matters.

---

## 2) The Re-check Protocol (“Reconciliation Pass”)

Each task runs a standard “re-check pack” that is intentionally boring and auditable.

### 2.1 Inputs

For a task involving a claim `C`:

* Claim record: `text`, `type`, `domain`, `credence`, `evidence_level`, `version`, `last_updated`, graph links. ([GitHub][1])
* Latest active reasoning trail(s) for `C` (or the most recent one). ([GitHub][1])
* Active evidence links (supporting + contradicting) with quotes/locators. ([GitHub][1])
* Related claims by embedding + graph. ([GitHub][1])
* Any contradictions referencing `C`. ([GitHub][1])
* Any prediction records if `C` is `[P]`. ([GitHub][1])

Then: run the pass under a new `analysis_logs` record so you can attribute what changed, including `claims_updated`. ([GitHub][1])

---

### 2.2 Step A — Temporal audit (LLM time-bias countermeasure #1)

Before looking for new evidence, force explicit time-scoping.

**Goal:** transform “timeless sounding” claims into “true-as-of” or “time-ranged” claims when appropriate.

**Checklist:**

* Does the claim assert a fact that’s only valid during a time window (laws, officeholders, “latest results”, “current situation”, “now”)?
* Is the claim implicitly time-bounded but written timelessly?
* Is the *evidence* time-aligned with the claim’s implicit time?

**Action outputs:**

* If time-scoped: rewrite the claim text (or add a structured field—see §4) to include an explicit **As-of date** or **time range**.

  * Example: “X is the CEO of Y” → “As of 2026‑02‑01, X is the CEO of Y.”
* If timeless: explicitly mark it as evergreen (even if just in notes / reasoning trail).

This step is *the* simplest way to prevent a coherent-but-outdated KB: **make time visible in the representation**.

---

### 2.3 Step B — Evidence refresh (LLM time-bias countermeasure #2)

Run two retrieval passes:

1. **Support search** (find best current supporting evidence)
2. **Disconfirm search** (find best current contradicting evidence)

But with an added constraint for time-sensitive claims:

> If a claim is time-sensitive, **prefer evidence published after the claim’s last review / last update** and penalize old evidence.

You already have the mechanism to store results:

* new evidence links get added,
* old ones can be superseded using the built-in evidence supersession concept (`status`, `supersedes_id`). ([GitHub][1])

If the exact quote/locator can no longer be found in the updated source:

* mark the evidence link `superseded` or `retracted` (depending on what happened), and attach the reason. ([GitHub][1])

---

### 2.4 Step C — Update decision (credence, evidence level, contradictions)

Produce a structured “delta proposal”:

* **Credence update** (new `credence` + justification)
* **Evidence level update** if warranted (E1–E6) ([GitHub][1])
* **Contradiction updates**

  * If contradiction resolves via time-scoping: set `conflict_type=timescale` and add resolution path; mark resolved if appropriate. ([GitHub][1])
  * If unresolved: keep `status=open` but document what evidence would discriminate.

This is also where you decide whether to:

* increment the claim version (update the claim row: `version`, `last_updated`), ([GitHub][1])
* supersede the old reasoning trail with a new one (`supersedes_id`, `status`). ([GitHub][1])

---

### 2.5 Step D — Commit + provenance

**Commit requirements (for maintainability):**

* Any credence change **must** create a new reasoning trail with:

  * `credence_at_time`, `evidence_level_at_time`, `supporting_evidence`, `contradicting_evidence`, and a short `evidence_summary`. ([GitHub][1])
* Any evidence update must:

  * create new evidence links, supersede old ones if replaced. ([GitHub][1])
* Update `sources.last_checked` for sources you verified/compared. ([GitHub][1])
* Attach everything to an `analysis_logs` row for that pass. ([GitHub][1])

This yields a clean, inspectable history: “what did we believe, when, and why?”

---

## 3) Staleness Model (how to decide “review due”)

Here’s a pragmatic approach that keeps the DB lean:

### 3.1 Define “last epistemic touch”

Use the newest timestamp among:

* latest reasoning trail `created_at` for the claim (preferred), ([GitHub][1])
* else claim `last_updated`, ([GitHub][1])
* else claim `first_extracted`. ([GitHub][1])

### 3.2 Assign a default review interval (policy table)

Start with defaults based on **claim type + source type volatility + domain**.

Example defaults (tune to taste):

* **Fast-changing facts** (officeholders, “latest”, current events, incidents): 7–30 days
* **TECH trend claims / benchmarks**: 30–120 days
* **ECON / macro**: 90–365 days
* **Foundational definitions / math / evergreen**: 365–∞ days
* **Predictions**: due at `target_date`, plus periodic “on track?” checks (e.g., monthly) ([GitHub][1])

The point is not “correctness”—it’s that **staleness becomes a visible, managed debt**.

### 3.3 Compute staleness status

* **fresh** if `now <= last_touch + interval`
* **due** if within, say, 10% of expiry
* **stale** if `now > last_touch + interval`

Optional but powerful: compute **effective credence** for synthesis:

> `effective_credence = credence × freshness_factor`

Where `freshness_factor` decays with age for time-sensitive claims.
You keep the *human-assigned credence* stable, but you prevent stale claims from silently dominating syntheses.

### 3.4 Add a “staleness dashboard”

Even a simple CLI view is huge:

* stale claims by domain/type
* stale high-credence claims
* stale claims with many dependents
* sources overdue for `last_checked`

(These can all be derived from existing fields, especially `sources.last_checked`, `claims.last_updated`, claim dependencies, and reasoning trail timestamps. ([GitHub][1]))

---

## 4) Temporal Guardrails to counter LLM cutoff / nostalgia bias

The main danger you named is real: LLMs can cling to training priors or past timeframes when evaluating time-sensitive facts, and can behave inconsistently about “what time it is.” Recent research explicitly studies temporal robustness, temporal generalization, and cutoff boundaries in LMs—i.e., the failure modes you’re worried about. ([arXiv][2])

Here are guardrails that work in practice:

### 4.1 The “Now Contract”

Your orchestrator should always inject:

* `NOW_UTC` and `NOW_LOCAL`
* “You are operating on real-world time now; training cutoff is irrelevant”
* If the agent cannot retrieve/verify recent evidence, it must end at **NEI / not-checkable**, not guess.

This seems trivial, but it moves “time” from the model’s fuzzy priors into a hard constraint.

### 4.2 Ban ambiguous temporal language in stored claims

Enforce via validation (rc-validate style):

Disallow in claim `text` unless rewritten:

* “currently”, “today”, “recently”, “this year”, “now”, “latest”, “as of now”

Require transformation to one of:

* “As of YYYY‑MM‑DD …”
* “Between YYYY‑MM and YYYY‑MM …”
* “In 2024 …”
* or explicitly evergreen.

This is a *huge* anti-drift win and costs almost nothing.

### 4.3 Require time-aligned evidence for time-sensitive claims

If claim is time-sensitive, require at least one evidence link whose source is:

* published / last updated after a threshold date (e.g., within last 30–90 days), **or**
* an authoritative evergreen reference (e.g., a statute text that hasn’t changed—still needs periodic check)

If you can’t enforce “published date” yet because sources only store `year`, consider adding an optional `published` ISO date to sources (very small schema upgrade). Your framework already has an HTML extraction utility that mentions extracting a `published` field. ([GitHub][3])

### 4.4 “Freshness override” rule (prevents prior lock-in)

If the reconciliation pass finds **newer, higher-quality, more direct evidence** that conflicts with the previous conclusion:

* the system must either:

  * reduce credence (and explain why), or
  * split the claim into time-scoped variants, or
  * explicitly mark unresolved contradiction + what would resolve it.

What you want to prevent is the common LLM failure mode:

> “I see new evidence, but I’m going to keep my old coherent story anyway.”

You can detect this mechanically:

* If new contradicting evidence is added with strong strength + direct claim match, and credence barely changes, flag for review. (You already have `strength` and `claim_match` fields on evidence links in rigor-v1. ([GitHub][1]))

### 4.5 Snapshotting to defeat “source drift”

Two separate problems:

* the *world* changes
* the *web page* changes (edits, link rot, silent updates)

For reconciliation, it’s useful to store both:

* **the captured snapshot** you used originally (for reproducibility),
* and a periodic “live check” to see if the source has changed.

You already have a project structure with `reference/primary` and `reference/captured` directories in the workflow. ([GitHub][3])
Leverage that: when registering evidence, store (or reference) a local snapshot and hash it. Then `sources.last_checked` can mean “I compared live vs snapshot.” ([GitHub][1])

---

## 5) Minimal implementation path (keep it elegant)

### MVP (no schema changes)

You can do a lot immediately:

* Treat “reconciliation” as a new analysis pass type:

  * create an `analysis_logs` row,
  * update claims/evidence/reasoning using existing tables/fields. ([GitHub][1])
* Build `rc-db reconcile scan` that **derives** tasks from:

  * `sources.last_checked` overdue ([GitHub][1])
  * `contradictions.status=open` ([GitHub][1])
  * `predictions.target_date <= now` and stale `last_evaluated` ([GitHub][1])
  * claim “last epistemic touch” (latest reasoning trail timestamp; fallback to claim timestamps)
* Add a “temporal lint” that rewrites/flags relative-time phrasing in claim text.

### Small upgrades that pay off immediately

If you’ll tolerate 2–4 new optional fields, I’d pick:

1. `sources.published` (ISO date) — stops you from confusing 2024‑01 vs 2024‑12
2. `claims.as_of` (ISO date or range) — makes time-scoping machine-readable
3. `claims.time_sensitivity` (enum: evergreen/slow/fast/event) — drives review interval
4. `sources.content_hash` (or snapshot hash) — makes “source changed” detection robust

Everything else (review_due, staleness score, etc.) can be computed.

---

## 6) What this buys you re: humility + flexibility

* Your KB stops pretending to be timeless.
* “Outdated but coherent” becomes a visible failure state (stale debt), not a silent drift.
* New evidence can *force* belief updates via explicit override rules.
* Contradictions don’t get “resolved by narrative”; they get time-scoped or kept open with discriminators.

If you want, I can turn the above into a concrete pseudo-spec for two CLI commands:

* `rc-db reconcile scan` (produces a prioritized task list)
* `rc-db reconcile run <task>` (executes the re-check pack and writes analysis_log + updates)

…with explicit inputs/outputs that match your current tables (`analysis_logs.claims_updated`, evidence supersession, reasoning trail supersession). ([GitHub][1])

[1]: https://raw.githubusercontent.com/lhl/realitycheck/main/docs/SCHEMA.md "raw.githubusercontent.com"
[2]: https://arxiv.org/html/2502.01220v2?utm_source=chatgpt.com "Language Models Struggle to Achieve a Consistent ..."
[3]: https://github.com/lhl/realitycheck "GitHub - lhl/realitycheck: A framework for rigorous, systematic analysis of claims, sources, predictions, and argument chains."

---

Claude Opus 4.5 Deep Research
https://claude.ai/chat/c02856cd-e87f-48c9-94b9-205a3f7d705c

> I'm working on a new project called Reality Check https://github.com/lhl/realitycheck (sample data here https://github.com/lhl/realitycheck-data) that is an analysis framework for AI agents to do better analysis on any sort of content. This system seems to work well and has had recent upgrades that improves claims checking (originally it was strongest simply as a lens to separate rhetoric from claims, but over real world testing I've been addressing weaknesses. I'm curious to get a full analysis, summary of this tool from the research analyst hat but also, since it's been a sort of first principles style project, I'm interested in what other related projects there are, what core research or other principles we could apply, the academic and theoretical landscape, etc. My background is primarily coming from the knowledge management side of things, but I'm familiar with some past discourse systems - I'm interested in more background/grounding on fact, claims checking, reasoning chains, and anything else that might apply. I'm also interested finally if there are any "lightweight" easy wins we can get for improving our system (eg, additional lenses for our critical analysis, any easy things we might want to track or add to our DB, improving our claims search/synthesis) and also if there's anything that makes sense to streamline or that is redundant (I've been on a sprint adding features, and wanted to review to make sure that we're building something elegant, maintainable, and no more complex than it needs to be).

This is a great research project to dig into! Before I launch into comprehensive research, a few quick clarifications to make sure I focus on what's most valuable:

- Primary content domain: Is Reality Check primarily aimed at news/journalism analysis, social media content, research papers, AI-generated content, or general-purpose across all content types? This affects which fact-checking and claims verification literature is most relevant.
- Deployment context: Is this primarily for personal/research use, or are you building toward something more production-oriented (API service, integration with your translation/avatar work at Shisa, etc.)? This affects whether I focus more on academic rigor vs. practical scalability patterns.
- LLM backend flexibility: Are you committed to a specific model backend, or open to exploring techniques that might require specific capabilities (e.g., citation with retrieval, structured reasoning like chain-of-thought verification, multi-agent debate patterns)?

Once you clarify, I'll dive deep into the repos, survey the academic landscape (argumentation theory, computational fact-checking, claim decomposition, epistemic logic), map out related tools (ClaimBuster, Google Fact Check Tools, various academic systems), and give you both the theoretical grounding and practical "easy wins" analysis you're looking for.

> Reality Check should be general purpose, but I want it specifically to be able to handle hot takes/opinion pieces/essays (things that sound good but maybe aren't backed by evidence), the latest news and world events (these are notoriously hard to get good grounding or reasoning on due to incomplete information, huge bias) and for newly published academic papers etc (in  the field of LLMs/AI/ML not only are the concepts potentially difficult, but increasingly sophisticated AI slop - harder to tell what's LLM psychosis and what's not) - The current project is standalone but it may grow to something bigger, we want academic grounding, but either way real world use and scaling is what matters. Even on an individual basis, we can grow to thousands of analyses and claims and sources very quickly (you can see where we are after just a couple weeks!)  The idea is to be LLM/agentic framework agnostic. We want something that any decent reasoning/deep research trained LLM can be leveraged ideally, but we start w/ frontier reasoners for highest quality atm. 
> 
> BTW, As we scale we should be thinking about reconcilliation, revisiting claims/evidence for drift (new evidence, updates etc) - we are in effect building our own "world model" as time goes on which of course has the risk of drifting from reality (with the added danger in terms of solipism of being "logically complete". As we scale this, how do we maintain our humility and our flexibility (something that both humans and LLMs are notoriously bad at)?

Your Reality Check architectural audit is ready. It covers the framework's pipeline-based architecture and 3-stage analysis methodology, maps the system to academic foundations in computational fact-checking and argumentation theory, reviews related tools like ClaimBuster and Kialo, and addresses epistemological drift and belief revision challenges. The report includes practical recommendations for schema additions (temporal validity, claim relationships, confidence intervals), integration consolidation opportunities, and a prioritized roadmap for near-term through longer-term enhancements.

# Reality Check: An architectural audit and theoretical grounding for AI claim verification

The Reality Check framework represents a thoughtful approach to epistemic knowledge management, built on a **pipeline-based architecture** with LanceDB vector storage, a rigorous 3-stage analysis methodology (descriptive → evaluative → dialectical), and multi-tool agent integrations. The system's core strength is its emphasis on *provenance*—reasoning trails, evidence links, and explicit credence tracking create an audit trail often missing from knowledge management tools. However, opportunities exist to strengthen the theoretical foundations with insights from computational fact-checking research, argumentation theory, and belief revision mechanisms.

---

## Part 1: Reality Check tool architecture and capabilities

### Core architecture

Reality Check follows a **local-first, CLI-driven monolith** pattern with plugin extensibility. The tech stack comprises Python (89.5%), LanceDB for vector storage, and sentence-transformers (all-MiniLM-L6-v2, 384 dimensions) for embeddings. All processing runs locally without external API dependencies—a deliberate design choice prioritizing data sovereignty.

The data model centers on **six interconnected tables**: Claims (with domain codes like TECH, LABOR, ECON), Sources, Evidence Links, Argument Chains, Predictions, and Reasoning Trails. The ID scheme (`{DOMAIN}-{YEAR}-{SEQUENCE}`) provides semantic identifiability, while vector embeddings enable similarity-based claim discovery across the unified knowledge base.

### The 3-stage analysis methodology

The framework's intellectual core is its structured analysis approach:

1. **Descriptive stage** extracts what the source actually says—key claims, author context, publication metadata
2. **Evaluative stage** applies the E1-E6 evidence hierarchy and assigns credence scores (0.0-1.0)
3. **Dialectical stage** cross-references claims against existing knowledge, identifies contradictions, builds argument chains

This maps cleanly to the Toulmin model: descriptive extraction yields grounds and claims, evaluative analysis provides qualifiers and backing assessment, and dialectical synthesis identifies rebuttals and warrants. The v0.3.0 additions (Layer, Actor, Scope, Quantifier) further enrich the analytical vocabulary.

### Evidence hierarchy (E1-E6)

| Level | Strength | Description |
|-------|----------|-------------|
| E1 | Strong Empirical | Replicated studies, systematic reviews, meta-analyses |
| E2 | Moderate Empirical | Single peer-reviewed study, official statistics |
| E3 | Strong Theoretical | Expert consensus, working papers, preprints |
| E4 | Weak Theoretical | Industry reports, credible journalism |
| E5 | Opinion/Forecast | Personal observation, anecdote, expert opinion |
| E6 | Unsupported | Pure speculation, unfalsifiable claims |

### Design philosophy strengths

Several design decisions stand out as particularly well-considered:

- **Credence over binary truth**: The 0.0-1.0 credence scale acknowledges epistemic uncertainty inherent in real-world claims
- **Separation of framework and data**: The `realitycheck/` framework repository is cleanly separated from user data repos, enabling versioned methodology updates
- **Reasoning trails for auditability**: Every credence assignment can be traced to its evidential justification—critical for epistemic hygiene
- **Prediction tracking with falsification criteria**: The `[P→]`, `[P✓]`, `[P✗]` status system operationalizes Popperian falsifiability

### Identified gaps

The current implementation lacks **temporal validity windows** for claims (when does evidence expire?), **explicit contradiction detection** (claims can conflict without automated flagging), and **confidence intervals** (single-point credence doesn't capture uncertainty distribution). The multi-integration surface (Claude/Codex/Amp/OpenCode) creates maintenance overhead with partially overlapping skill definitions.

---

## Part 2: Academic and theoretical foundations

### Computational fact-checking landscape

The academic field has consolidated around a **three-stage pipeline** framework (Guo, Schlichtkrull & Vlachos, 2022 TACL Survey): claim detection → evidence retrieval → claim verification. This maps surprisingly well to Reality Check's existing architecture, though the framework currently relies on human judgment rather than automated claim-worthiness scoring.

**Claim decomposition** has emerged as a critical subfield. The FActScore → VeriScore → Claimify progression shows a tension between atomicity (breaking claims into minimal units) and verifiability (maintaining semantic coherence). The **AFEV framework (2025)** uses dynamic, iterative decomposition with context-aware evidence reranking. Key finding from Hu et al. (2024): excessive decomposition can *introduce* errors through semantic drift—a cautionary note for overly aggressive claim atomization.

Major benchmarks include **FEVER** (185K synthetic Wikipedia claims), **LIAR/LIAR-PLUS** (12K political statements with fine-grained labels), **SciFact** (1.4K biomedical claims), and **AVeriTeC** (4.5K real-world claims with open web evidence). Current SOTA systems achieve **75-80% label accuracy** on FEVER with evidence, but performance drops **15+ F1 points** when moving to open-domain settings—a sobering reality check for automated verification ambitions.

### Multi-agent debate approaches

Recent work on **multi-agent debate (MAD)** shows promise for fact verification. Du et al. (2023) demonstrated that multiple LLM instances debating responses can improve factuality, achieving significant gains on reasoning tasks. The **Tool-MAD framework (2025)** equips agents with heterogeneous external tools (search APIs, RAG modules) and shows **up to 35.5% improvement** over standard MAD on fact verification benchmarks. This pattern—specialized agents with different tools debating toward consensus—could inform Reality Check's agentic workflow evolution.

### Argumentation theory foundations

**Toulmin's model** (1958) provides the most practically applicable framework for Reality Check. Its six components map directly:

| Toulmin Element | Reality Check Equivalent |
|-----------------|------------------------|
| Claim | Claim text with type classification |
| Grounds (Data) | Evidence links with source references |
| Warrant | Implicit in reasoning trails |
| Backing | E1-E6 evidence hierarchy level |
| Qualifier | Credence score (0.0-1.0) |
| Rebuttal | Contradiction claims `[X]` |

**Dung's abstract argumentation frameworks** (1995) offer a formal model for reasoning about conflicting evidence. Arguments exist in attack/support relations, and **extension semantics** (grounded, preferred, stable) determine which argument sets can be jointly accepted. This maps to the problem of determining which claims to believe when evidence conflicts.

### AGM belief revision theory

The AGM framework (Alchourrón, Gärdenfors, Makinson 1985) formalizes rational belief change through three operations:

- **Expansion** (K + φ): Add new belief without consistency check
- **Contraction** (K ÷ φ): Remove belief while preserving consistency
- **Revision** (K * φ): Add belief while maintaining consistency (may retract contradictory beliefs)

The key principle is **minimal change**—revisions should disturb existing beliefs as little as possible. Reality Check's reasoning trails implicitly support expansion, but lack formal mechanisms for contraction and revision when new evidence contradicts existing claims.

### Truth maintenance systems

**JTMS (Justification-based TMS)** and **ATMS (Assumption-based TMS)** provide operational models for dependency-directed belief management. JTMS maintains a single consistent belief set with explicit justification chains; ATMS tracks multiple consistent contexts simultaneously. Reality Check's reasoning trails approximate JTMS justifications, but lack the automated propagation and backtracking mechanisms that make TMS powerful.

---

## Part 3: Related tools and projects

### Production fact-checking tools

**ClaimBuster** (UT Arlington) pioneered end-to-end automated fact-checking with claim-worthiness scoring trained on 8K+ labeled sentences. Its public REST API provides claim scoring, similarity matching, and integration with Google Fact Check Explorer for verdicts. Reality Check could integrate ClaimBuster's scoring to prioritize which claims warrant detailed analysis.

**Google Fact Check Tools** aggregates existing fact-checks globally using the **ClaimReview schema** (schema.org/ClaimReview)—the industry standard for fact-check markup. This aggregation-only approach (no original verification) complements rather than competes with Reality Check's analysis-focused methodology.

**Full Fact AI** (UK) provides the most sophisticated statistical claim verification, automatically checking claims against UK ONS data. Their approach—claim labeling → claim matching → statistical verification—demonstrates how automated verification can work for well-structured domains with authoritative data sources.

### Argument mapping tools

**Kialo** offers visual debate trees with Pro/Con structure and impact voting—research shows argument mapping can triple critical thinking gains. **Argdown** provides a markdown-inspired syntax for argument definition that integrates with VS Code and Obsidian. Its text-based approach aligns well with Reality Check's CLI-first philosophy:

```argdown
[Thesis]: AI training costs double annually. #TECH
+ <Epoch AI Report>: Analysis of compute spending 2012-2024. #E2
- <Hardware Efficiency Gains>: May offset cost scaling. #E3
```

### Knowledge graph approaches

The current SOTA for KG-based verification uses a **hybrid pipeline**: Entity Linking (ReFinED) → Wikidata Q-IDs → DBpedia Triple Retrieval → Evidence Ranking → DeBERTa Classification → Web-RAG Fallback. This achieves **F1=0.78 on FEVER 2.0**. Reality Check's LanceDB store could be enhanced with entity linking to enable cross-referencing against external knowledge graphs.

---

## Part 4: Handling epistemological drift and belief revision

### The fundamental tension

Knowledge systems face an inherent conflict between **internal coherence** (logical consistency) and **external validity** (reality alignment). Systems can become "logically complete but reality-disconnected" by prioritizing consistency without mechanisms to detect foundational drift. A Google SRE study found **60% of production outages trace to stale assumptions**—epistemic staleness is a practical, not merely philosophical, concern.

### Contradiction detection approaches

**Minimal Inconsistent Subsets (MIS)** identify the smallest claim sets producing contradictions—localizing "iceberg inconsistencies" that aren't overtly contradictory. LLM-powered detection (e.g., "KnowledgeBase Guardian" pattern) uses vector similarity to retrieve related documents, then employs LLMs to compare and detect semantic conflicts before adding new information. Reality Check's existing embedding infrastructure could support this pattern.

### Temporal validity tracking

Three temporal dimensions matter for claims:

1. **Valid time**: When the claim was true in the world
2. **Transaction time**: When the claim was recorded in the system
3. **Validity window**: How long the claim remains fresh

The **TVCP (Temporal Validity Change Prediction)** NLP task predicts whether new information extends, shortens, or negates prior claim validity. Reality Check currently lacks explicit temporal validity—claims have `created_at`/`updated_at` timestamps but no expiration or freshness tracking.

### Confidence calibration

**Temperature scaling** provides efficient post-hoc calibration using a single learned parameter to adjust prediction confidence. The **Expected Calibration Error (ECE)** metric measures the average gap between stated confidence and actual accuracy. For Reality Check, this suggests credence scores should be periodically validated against outcomes (for predictions) and recalibrated when systematic over/under-confidence is detected.

### Non-monotonic reasoning implementations

**Defeasible Logic** offers rule-based reasoning with explicit priorities—computationally efficient (polynomial complexity) and practical for exception handling. The key insight: when new evidence arrives that contradicts existing conclusions, **dependency-directed backtracking** efficiently identifies which upstream claims need revision rather than invalidating everything.

### Practical epistemic humility mechanisms

- **Explicit "unknown" states**: Systems should distinguish "false" from "unknown/insufficient evidence"
- **Source attribution and conflict surfacing**: When evidence conflicts, surface the conflict rather than arbitrarily resolving it
- **Threshold-based abstention**: "Answer only if >X% confident" with errors penalized more than abstentions
- **Calibrated trust scoring**: Match stated confidence to actual probability of correctness

---

## Part 5: Target domain considerations

### Opinion pieces and hot takes

Opinion content requires **separating rhetoric from substance**—identifying the underlying factual claims embedded in argumentative framing. The Toulmin model is particularly useful here: extract the grounds (what facts are claimed) from the warrants (what reasoning connects facts to conclusions) and qualifiers (how certain is the claim). Reality Check's claim type taxonomy (`[F]` fact vs. `[H]` hypothesis vs. `[S]` speculation) provides the vocabulary, but automated extraction from opinionated text remains challenging.

**Key challenges**: Implicit claims (unstated assumptions), hedged language, rhetorical exaggeration, and the fact/opinion boundary itself. The pragma-dialectics framework offers a systematic approach to reconstructing implicit arguments and identifying argumentative fallacies as procedural violations.

### News and current events

Rapidly evolving stories present **temporal verification challenges**—a claim may be accurate at time T but obsolete by T+24h. The "fog of war" problem means early reporting often contains errors that are later corrected. Reality Check's prediction tracking (`[P→]` pending status) provides a model, but real-time news verification requires **explicit temporal scoping** ("as of [timestamp]") and **revision tolerance** (expecting initial assessments to change).

**Key challenges**: Incomplete information, conflicting eyewitness accounts, deliberate disinformation, and the tension between speed and accuracy. Multi-source triangulation and explicit uncertainty quantification become critical.

### Academic papers, especially AI/ML

Scientific claims require detecting **overclaims** (conclusions that exceed the evidence), **p-hacking** (selective reporting of statistically significant results), and increasingly **AI-generated content** ("slop"). The SciFact benchmark demonstrates that domain-specific verification is feasible but requires specialized knowledge.

**Key challenges for AI/ML papers**:
- Benchmark gaming (optimizing for metrics rather than genuine capability)
- Cherry-picked examples and failure case hiding
- Unreproducible results due to compute requirements
- Claims about "emergent" capabilities that may be artifacts of evaluation design
- The replication crisis extending to ML (Pineau et al. reproducibility checklist)

Reality Check's E1-E6 hierarchy maps well to scientific evidence quality, but detecting subtle methodological issues requires domain expertise beyond what current automated systems can provide.

---

## Part 6: Practical improvements ("easy wins")

### Additional lenses/analysis dimensions

**Temporal validity fields** represent the highest-impact addition. Each claim should have:
- `valid_from`: When the claim became true/relevant
- `valid_until`: When the claim expires or requires revalidation (null = indefinite)
- `freshness_check_interval`: How often to verify the claim remains current

**Claim relationship types** beyond the current argument chains:
- `supports` / `contradicts` / `qualifies`
- `generalizes` / `specializes`
- `supersedes` (newer claim replaces older)
- `depends_on` (logical prerequisite)

**Source credibility tracking** at the source level:
- `reliability_score`: Historical accuracy of this source
- `bias_indicators`: Known systematic biases
- `expertise_domains`: Where this source is authoritative

### Database schema additions

```python
# Claims table additions
valid_from: Optional[datetime]
valid_until: Optional[datetime]
freshness_interval_days: Optional[int]
superseded_by: Optional[str]  # FK to claim that replaces this one
confidence_interval_low: Optional[float]  # Lower bound of credence
confidence_interval_high: Optional[float]  # Upper bound of credence

# New: Claim Relationships table
claim_relationships = Table(
    id: str,
    source_claim_id: str,  # FK to claims
    target_claim_id: str,  # FK to claims
    relationship_type: str,  # supports|contradicts|qualifies|generalizes|specializes|supersedes|depends_on
    strength: str,  # strong|moderate|weak
    notes: Optional[str],
    created_at: datetime
)

# Sources table additions
reliability_score: Optional[float]  # 0.0-1.0 based on historical accuracy
bias_indicators: Optional[str]  # JSON array of identified biases
last_verified: Optional[datetime]
```

### Claims search and synthesis improvements

**Contradiction detection query**: When adding a new claim, automatically search for semantically similar claims with opposing evidence direction:
```bash
rc-db claim add --text "..." --check-contradictions
# Returns: "Warning: Potential contradiction with TECH-2024-003 (similarity: 0.87, direction: opposing)"
```

**Staleness alerts**: Periodic scan for claims past their freshness interval:
```bash
rc-db audit freshness
# Returns: "12 claims require freshness review (last verified >90 days ago)"
```

**Evidence strength aggregation**: Compute aggregate evidence strength for claims with multiple evidence links, weighted by source reliability and evidence direction.

### Claim deduplication and merging

**Semantic deduplication**: Use embedding similarity threshold (e.g., >0.95) to flag potential duplicates:
```bash
rc-db claim add --text "..." --dedup-threshold 0.95
# Returns: "Similar claim exists: TECH-2024-001 (similarity: 0.97). Merge? [y/n/create anyway]"
```

**Claim merging workflow**: When merging duplicates, combine evidence links, preserve reasoning trails from both, select higher-quality text, log the merge in audit trail.

### Lightweight uncertainty tracking

Replace single credence score with **confidence interval** (low, point estimate, high):
```bash
rc-db claim add --text "..." --credence 0.7 --credence-range 0.6-0.85
# Stored as: credence=0.7, confidence_interval_low=0.6, confidence_interval_high=0.85
```

This captures whether credence is based on strong evidence (narrow interval) or high uncertainty (wide interval).

---

## Part 7: Streamlining and redundancy review

### Identified redundancies

**Integration surface overlap**: The `integrations/` directory contains parallel implementations for Claude Code, Codex, Amp, and OpenCode. Each has its own skill definitions with similar functionality. Consider:
- Extract common functionality into shared modules
- Use a single configuration-driven skill definition format
- Generate tool-specific integrations from a canonical source

**Skills vs. plugins structure**: For Claude Code specifically, both skill files and a plugin structure exist. The `/reality:*` slash commands in the plugin overlap with the skills. Consolidate to plugins-only (more powerful) or skills-only (simpler).

### Simplification opportunities

**Methodology templates**: The `methodology/` directory contains templates that could be parameterized. Instead of separate files for different analysis types, use a single template with configurable sections:

```yaml
# methodology/analysis-template.yaml
stages:
  - name: descriptive
    required_fields: [claims, author, context]
    prompts: [...]
  - name: evaluative
    required_fields: [evidence_level, credence]
    optional_fields: [layer, actor, scope, quantifier]  # enabled with --rigor flag
  - name: dialectical
    required_fields: [cross_references, contradictions]
```

**CLI command consolidation**: Some commands could be merged:
- `rc-db evidence add` + `rc-db evidence supersede` → single command with `--supersede` flag
- `rc-db analysis start/mark/complete` → single `rc-db analyze` with state machine

### Maintainability improvements

**Type hints and validation**: Add Pydantic models for all data structures to catch schema mismatches early:

```python
from pydantic import BaseModel, Field

class Claim(BaseModel):
    id: str = Field(pattern=r'^[A-Z]+-\d{4}-\d{3}$')
    text: str = Field(min_length=10)
    type: Literal['[F]', '[T]', '[H]', '[P]', '[A]', '[C]', '[S]', '[X]']
    evidence_level: Literal['E1', 'E2', 'E3', 'E4', 'E5', 'E6']
    credence: float = Field(ge=0.0, le=1.0)
```

**Configuration consolidation**: Move from scattered configuration (`.realitycheck.yaml`, environment variables, CLI flags) to a single hierarchical config with clear precedence:
1. CLI flags (highest)
2. Environment variables
3. Project `.realitycheck.yaml`
4. User `~/.config/realitycheck/config.yaml`
5. System defaults (lowest)

### What can be simplified without losing capability

- **Remove legacy YAML migration code** if migration is complete for all users
- **Consolidate embedding utilities** (`embed.py` functions could live in `db.py`)
- **Simplify test structure** if 401 tests include redundant coverage (audit with coverage tools)
- **Reduce integration points** to 2-3 primary tools rather than 4+ with overlapping features

---

## Synthesis: A roadmap for Reality Check evolution

### Near-term priorities (1-3 months)

1. **Add temporal validity fields** to claims schema with freshness auditing
2. **Implement contradiction detection** using existing embeddings + LLM comparison
3. **Add claim relationships table** for explicit supports/contradicts/supersedes tracking
4. **Consolidate integrations** to reduce maintenance surface

### Medium-term enhancements (3-6 months)

1. **Integrate ClaimBuster API** for automated claim-worthiness scoring on ingested sources
2. **Add confidence intervals** to credence tracking
3. **Implement TMS-style dependency propagation** for automated credence updates when evidence changes
4. **Build staleness detection and alerting** for claims past freshness windows

### Longer-term research directions

1. **Multi-agent verification workflow** where specialized agents debate claim veracity
2. **Knowledge graph integration** linking claims to Wikidata entities for external grounding
3. **Domain-specific verification modules** (scientific claims, statistical claims, prediction tracking)
4. **Argumentation semantics engine** computing which claims survive under Dung-style attack relations

### Theoretical grounding to prioritize

The **AGM belief revision** framework and **Truth Maintenance Systems** provide the most directly applicable theoretical foundations for Reality Check's evolution. AGM's minimal change principle should guide how the system handles contradictory evidence, while TMS-style justification tracking already aligns with the existing reasoning trails architecture.

The system is well-positioned to become a reference implementation for **epistemically rigorous knowledge management**—filling a gap between simple note-taking tools and heavyweight knowledge graph systems. The combination of local-first operation, explicit uncertainty quantification, and audit trail preservation addresses real needs that existing tools don't satisfy.
