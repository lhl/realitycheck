# Implementation: Claim-Evidence Alignment and Reader-First Writing

**Status**: Phases A–C implemented; Doctorow acceptance runs pending
**Started**: 2026-11-20
**Last Updated**: 2026-11-20
**Input**: Editorial/methodological review (2026-11) of the Jouzu writing skills
(`jouzu-clear-writing`, `jouzu-anti-slop`), `shisa-ai/glm53f-vs-ds41f-vs-qw38fn/HOWTO-ANALYSIS.md`,
Reality Check's prose pass and templates, and three analyses in `realitycheck-data`.

## Summary

The review found that the most consequential output problem is not wordiness
but claims that say more than their evidence, with different surfaces of the
same analysis disagreeing. Its example: `doctorow-2026-llms-real-ai-fake`
(TECH-2026-102) has a Stage 2 note saying the evidence supports tool
involvement but the causal interpretation differs, yet the row is `ok`, Key
Claims `Verified?` is `?`, and the registered claim states the causal
interpretation as `[F]`. Later update sections explain the distinction better
than the active claim does.

This work keeps the detailed Reality Check method and makes two separate
changes, each in its own commit:

1. **Analysis pass** (Phase A): a Claim-Evidence Alignment Pass that runs after
   Stage 3 and before any prose work; a stricter meaning for `ok`; consistency
   across summary, tables, YAML, and database; corrected chain-credence
   guidance; one validator check for a mechanically detectable mismatch.
2. **Writing pass** (Phase B): the opening answers the reader's question,
   anti-slop word lists become a diagnostic rather than a deletion rule, and
   templates put the assessment before workflow metadata.

The passes are separate because a prose pass that runs on a misaligned claim
makes the error more persuasive. The prose pass must not change analysis
results; if it surfaces an analysis problem, return to the alignment pass.

## Review Findings → IDs

| ID | Finding | Phase |
|----|---------|-------|
| R1 | Verification must apply to the exact claim; split event / attribution / interpretation; state the strongest alternative for contested conclusions (no ceremonial counterargument) | A |
| R1b | Evidence hierarchy and synthesis template present MIN(step credence) as the chain credence; it is an upper bound for a conjunctive chain, and the conclusion may have outside support | A |
| R1c | Updates are appended without correcting the active claim, summary, verification row, YAML, and DB | A |
| R2 | Generalize "decision first" to "answer the reader's question first", by task type (choice / fact-check / explanation / unresolved dispute); examples, not frames | B |
| R3 | Clear-writing governs; anti-slop is a diagnostic. Replace "delete every match" / "replace every not-X-but-Y" with "what would a careful reader lose?" | B |
| R4 | Opening gives answer + evidence carrying the most weight + limitation most likely to change interpretation; citations beside inferences; coverage gap in opening only if it could reverse the answer | B |
| R5 | Cross-model A/B evaluation (old vs revised guidance, frozen evidence packets, blind evidence + reader tests) | Deferred (D-R5) |

## Pre-analysis

- **Scope**: templates under `integrations/_templates/`, `methodology/`, hand-written
  Claude plugin commands, `docs/WORKFLOWS.md`, `docs/SCHEMA.md`, and one
  validator check in `scripts/analysis_validator.py`. No DB schema change.
- **Not in scope**: editing `realitycheck-data` analyses (the Doctorow case is
  kept as the acceptance test); editing the Jouzu skills (separate repo).
- **Risks**:
  - The new validator warning fires on existing analyses whose Key Claims
    `Verified?` column holds `?` while Stage 2 says `ok`/`nf`. This is intended
    (WARN, not ERROR, unless `--rigor`).
  - `_extract_section_content` now matches a heading title at any level
    (`##`-`######`). Analyses that nest Stage 2 under `####` are now checked
    and may surface warnings that were previously hidden.
  - Reordering templates (Phase B) must not break `analysis_validator.py`
    required-section checks; those check presence, not order.
- **Validation plan**: targeted validator tests first (failing → passing), run
  validator on the real Doctorow file, `make check-skills`, full suite.

## Punchlist

### Phase A — Analysis pass (R1, R1b, R1c)

- [x] Tests first: `TestVerificationStatusConsistency` in `tests/test_analysis_validator.py`
- [x] `analysis_validator.py`: warn when Key Claims `Verified?` leading status code disagrees with Stage 2 `Status`
- [x] `analysis_validator.py`: section lookup tolerates heading level (`####` Stage 2 tables)
- [x] New partial `partials/claim-evidence-alignment.md.j2`; included in check / analyze / synthesize
- [x] `check.md.j2`: workflow step 7 (alignment, analysis) precedes step 8 (prose, writing); `--continue` propagates changes to every surface
- [x] `factual-claims-verified.md.j2`: `ok` = verified as worded
- [x] `key-claims.md.j2`: `Verified?` carries the Stage 2 status code (superseded in Phase C: column removed)
- [x] Chain credence wording: `methodology/evidence-hierarchy.md`, `partials/credence-calibration.md.j2`, `methodology/templates/synthesis.md`, `docs/SCHEMA.md`, `docs/WORKFLOWS.md`
- [x] Claude plugin commands (`check.md`, `analyze.md`, `synthesize.md`) — hand-written, updated to match
- [x] `docs/WORKFLOWS.md` section
- [x] Regenerate skills + `check-core.md`

### Phase B — Writing pass (R2, R3, R4)

- [x] Revise `partials/neutral-prose-pass.md.j2`: writing pass runs after alignment and does not change conclusions; accuracy outranks style; answer-first opening by task type (examples, not frames); reader-loss deletion test; word lists as diagnostics; qualification stated once beside its claim
- [x] `## Assessment` opens full source analyses (`check.md.j2` template, `analysis/source-analysis-full.md.j2`, `methodology/templates/source-analysis.md`); legends and metadata follow
- [x] Quick extraction summary: say what the source says and what was not checked; no implied verdict
- [x] Synthesis: `## Assessment` before metadata (`synthesize.md.j2` contract + snippet, `methodology/templates/synthesis.md`); removed the trailing "Summary Assessment" subsection it replaces
- [x] `analysis_formatter.insert_legends` places missing legends after an opening `## Assessment` (test first)
- [x] Plugin commands + `docs/WORKFLOWS.md` parity
- [x] Regenerate skills + `check-core.md`

### Phase C — Review round 1 remediation

Reviewer findings on `8015125` + `fbc4a8b`, plus one found while building the acceptance test.
Principle applied: instructions to analysis agents are short, imperative, and name exact fields
and commands; rationale lives once in `docs/WORKFLOWS.md`.

| ID | Finding | Resolution |
|----|---------|------------|
| RV1-H1 | Alignment pass told agents to retype and propagate to the DB, but `rc-db claim update` had no `--type`, and the DB has no verification-status field | Added `claim update --type` (tests first). Instructions name the fields each copy must share: text, type, evidence level, credence. Stage 2 `Status` stated as the only verification status. `check` tells the agent to read back with `claim get` and report failed DB corrections as outstanding |
| RV1-M1 | `export_chain_md` printed "Chain credence = MIN(step credences)" beside the stored score | Export prints the lowest step credence as a ceiling; test with a chain scored below its minimum |
| RV1-M2 | Quick extractions had conflicting opening instructions (`## Assessment` vs `## Summary` after metadata) | Quick template puts `## Summary` directly below the title; prose pass names `## Summary` as the quick opening (one or two sentences, no verdict); formatter places legends after it |
| RV1-Q2 | `Verified?` as a second hand-maintained status invites fixing the warning by editing `?` → `ok` | Column removed from new Key Claims tables (templates + formatter); validator still reads legacy cells; WORKFLOWS says not to silence the warning by editing `Verified?` |
| RV1-Q3 | 80-line alignment partial repeated in every skill; exact-claim question too literal | Partial cut to ~30 lines with the qualified question ("materially wrong at its stated scope or credence"); chain math only in credence calibration (check) and the synthesize chain step; DB mutation only in `check`; full reference in WORKFLOWS |
| RV1-N1 | Found during acceptance setup: Doctorow was never registered and its IDs TECH-2026-101/102 belong to other sources' claims in the live DB. Following the new "update the registered claim" instruction would have overwritten them | `check` and the plugin command require `claim get` first: update only if `source_ids` include this source; otherwise reserve a new ID with `claim ticket` and renumber. Acceptance workspace reproduces the collision and scores it |

- [x] Tests first: `claim update --type` (3), chain export below MIN (2), quick Summary legends (2), Key Claims without `Verified?` (2)
- [x] `scripts/db.py`, `scripts/export.py`, `scripts/analysis_formatter.py`
- [x] Partials: `claim-evidence-alignment.md.j2` (short), `neutral-prose-pass.md.j2` (short, quick opening)
- [x] Templates: quick skeleton, key-claims table, `check.md.j2` registered-claims block and continuation step
- [x] Plugin commands, `docs/WORKFLOWS.md` (full reference + field table + `claim update` example), `README.md` CLI line
- [x] Acceptance harness `_dev/acceptance/doctorow/` (setup, TASK, score, RUBRIC, README); baseline scores 3/6
- [ ] Acceptance runs: DSv4.1f 1017, GPT-6.2-Sol, GPT-6.2-Astra (jouzu), Claude Opus 5.5 (Claude Code); new vs old arm

## Deferrals

| ID | Item | Rationale | Risk | Target |
|----|------|-----------|------|--------|
| D-R5 | Cross-model evaluation of old vs revised guidance (DSv4.1f 1017, GPT-6.2-Sol, Claude Opus 5.5, Gemini Neon/Carbon; Astra and Fable on hardest cases and as independent reviewers). Cases: HOWTO forced choice, OpenAI policy-vs-practice, Doctorow disputed causal claim with later update. Blind evidence test + reader test. | Needs frozen evidence packets and a harness; guidance change should land first so there is a revised arm to test | Revised guidance is unmeasured; agreement between models is not verification | Next methodology milestone |
| D-A1 | Validator check that an `## Assessment` / opening section exists in full analyses | Backward compatibility (D10: never break existing repos silently); land guidance first | Analysts may skip the opening | After D-R5 |
| D-A2 | Reconcile E-level descriptions between `methodology/evidence-hierarchy.md` and `partials/evidence-hierarchy.md.j2` (E2/E3/E4 definitions differ) | Pre-existing, found during this review; out of scope | Analysts get different E-level definitions depending on which file they read | Next methodology milestone |
| D-A3 | Corresponding edits to `jouzu-anti-slop` / `jouzu-clear-writing` / `jouzu-analysis-writing` (separate repo; `jouzu-analysis-writing` installed at `~/.config/jouzu/agent/skills/`) | Different repo and owner | Jouzu skills keep the mechanical deletion rule and decision-only framing | Jouzu backlog |

## Acceptance test

The Doctorow case (`realitycheck-data/analysis/sources/doctorow-2026-llms-real-ai-fake.md`,
TECH-2026-102). A revised run passes only if both hold:

- **Evidence**: the disputed causal interpretation is not marked `ok`; the
  claim is split or retyped; summary, verification row, YAML, and DB agree.
- **Reader**: the opening states what remains disputed without the reader
  scanning the YAML.

Harness: `_dev/acceptance/doctorow/` (see its README and RUBRIC). It builds a
disposable workspace and temporary DB from the live data repo (read-only),
seeds the colliding TECH-2026-101/102 claims, and scores the result.

## Worklog

### 2026-11-20: Phase A (analysis pass)

- Tests first: added `TestVerificationStatusConsistency` (11 tests) to `tests/test_analysis_validator.py`; initial run `uv run pytest tests/test_analysis_validator.py -q` → 4 failed (expected), then 1 more failing for nested `####` headings.
- Implemented the check and heading-level tolerance; `uv run pytest tests/test_analysis_validator.py tests/test_analysis_formatter.py -q` → passed.
- Runtime check on real data: `uv run python scripts/analysis_validator.py ~/github/lhl/realitycheck-data/analysis/sources/doctorow-2026-llms-real-ai-fake.md` → now warns `Claim TECH-2026-102: Key Claims Verified? is '?' but Key Factual Claims Verified Status is 'ok'` (also TECH-2026-101, INST-2026-103), and surfaces the previously hidden missing-columns warning for its Stage 2 table.
- Checked that `rc-validate` does not run `analysis_validator.py`; partial wording says so.
- Checked that `rc-db chain add --credence` exists (defaults to MIN of claims) and that `rc-validate` warns when chain credence exceeds the minimum (`CHAIN_CREDENCE_EXCEEDS_MIN`); docs describe that as a ceiling.
- `make assemble-skills` → regenerated.
- `make check-skills` → `Generated: 41 files, 0 changed`.
- Full suite: `REALITYCHECK_EMBED_SKIP=1 uv run pytest -q` → `454 passed, 17 skipped`.

### 2026-11-20: Phase B (writing pass)

- Rewrote `partials/neutral-prose-pass.md.j2` (heading kept as "Neutral Analyst Prose Pass" for continuity with v0.3.5 docs).
- Added `## Assessment` as the first section in source-analysis and synthesis templates; legends/metadata follow. Not enforced by the validator (deferral D-A1).
- Tests first: `TestLegendInsertion::test_insert_legends_after_assessment` failed, then passed after updating `insert_legends`.
- `uv run pytest tests/test_analysis_formatter.py tests/test_analysis_validator.py -q` → `122 passed`.
- Full suite: `REALITYCHECK_EMBED_SKIP=1 uv run pytest -q` → `455 passed, 17 skipped`; `make check-skills` → `Generated: 41 files, 0 changed`.

### 2026-11-20: Phase C (review round 1)

- Tests first: `uv run pytest tests/test_export.py -k chain_md` → 2 failed; `tests/test_db.py -k claim_update` → 2 failed (invalid-type test already passed: argparse rejected the unknown flag); `tests/test_analysis_formatter.py` → 3 failed. All pass after implementation.
- Live DB check: `rc-db source get doctorow-2026-llms-real-ai-fake` → not found; `claim get TECH-2026-102` → aifutures prediction (RV1-N1).
- Duplicate-ID behavior in a temp DB: second `claim add --id TECH-2026-102` → exit 1, "already exists" (add fails closed; update did not check ownership).
- Skill size (`wc -w`, Claude skills): check 4722 (v0.3.5) → 6178 (`fbc4a8b`) → 5542; rc-analyze 954 → 2089 → 1425; rc-synthesize 959 → 2275 → 1608.
- Acceptance harness dry run: `setup.sh $SCRATCH/acc-new new` then `score.sh` on the untouched workspace → `Automated: 3/6 passed` (expected baseline).
- Replaced the alignment-pass example (originally an anonymized version of the Doctorow incident) with an unrelated layoffs/rollout example so the "new" acceptance arm is not given the answer.
- Full suite before that template-only change: `REALITYCHECK_EMBED_SKIP=1 uv run pytest -q` → `463 passed, 17 skipped`; after it: `make check-skills` → `Generated: 41 files, 0 changed`, `uv run pytest tests/test_codex_skills.py tests/test_analysis_formatter.py tests/test_analysis_validator.py -q` → `127 passed`.
