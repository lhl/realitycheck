# Plan: Verification Loop for Factual Claims (v0.3.2)

**Status**: Implemented (framework changes committed; release cut pending)
**Created**: 2026-02-15
**Last Updated**: 2026-02-16
**Version**: 0.3.2 (methodology/template/config + validator/formatter hardening)
**Implementation**: [IMPLEMENTATION-v0.3.2.md](IMPLEMENTATION-v0.3.2.md)

## Motivation

Reality Check's `$check` workflow successfully parses and enumerates claims, assigns evidence levels and credence, and flags unverified items for follow-up. However, it **does not actively chase down or verify factual claims**. The workflow tells agents *what* to verify but doesn't give procedural steps or tool access for *how*.

This gap was identified during review of `aakashgupta-2026-amodei-hawkish-china-thread.md` (produced by Codex/gpt-5.2, committed in realitycheck-data `3ee7019` on 2026-02-15). The analysis correctly:
- Typed a Davos/H200 export claim as `[F]` (fact),
- Rated it `E6` (unsupported),
- Marked it `?` (unverified),
- Flagged it for follow-up in the "Claims to Cross-Reference" section.

But no follow-up occurred within the workflow. The claim was later verified in a manual second pass (realitycheck-data `460e8d5` on 2026-02-15; wording follow-up `21b0c4b`) using a BIS press release and TechCrunch reporting — both easily discoverable via basic web search. The first-pass analysis had reached `[REVIEWED]` status with a crux factual claim still unverified.

This is exactly the kind of failure Reality Check exists to prevent: confident-looking outputs with unresolved epistemic gaps.

## Problem Statement

Four root causes contribute to this verification gap:

### 1. No tool-agnostic "web discovery" capability in `$check`

The workflow needs a **web discovery** step (finding sources to cite) but currently lacks a consistent, integration-agnostic way to do that.

- **Claude Code**: the `check` skill's `allowed_tools` list (`integrations/_config/skills.yaml:37-46`) includes `WebFetch` (fetch a provided URL) but **not `WebSearch`** (discover URLs). Agents can read what they're given, but can't search for corroborating/disconfirming evidence.
- **Codex / Amp / OpenCode**: there is no `allowed_tools` gate, but the skill text does not clearly instruct which web search facility to use (or require a minimum attempt), so agents default to "flag for follow-up" rather than actually verifying.

### 2. No explicit verification loop in the workflow

The methodology's Stage 2 ("Key Factual Claims Verified" table) defines the *output shape* -- columns for Source Says, Actual, External Source, Status -- but provides no procedural instructions for how to populate the "Actual" and "External Source" columns. Agents are expected to verify facts but given no tool guidance, search strategy, or decision procedure for when/how to search.

### 3. Validator doesn't warn on high-stakes "unverified-but-sounding-confident" states

The combination `[F]` + `E6` + `?` is not inherently inconsistent; it can mean "checkable, but not yet checked." The failure mode is that this state can coexist with:
- **`[REVIEWED]` analyses** (giving a false sense that verification happened), and/or
- **high credence** on factual claims without citations, and/or
- **no recorded search attempts** for crux factual claims.

The current `analysis_validator.py` does not warn on these "looks reviewed / sounds confident / but not actually verified" patterns.

### 4. Single-pass analysis has no gate preventing `[REVIEWED]` with unverified crux claims

The workflow allows an analysis to reach `[REVIEWED]` status even when crux factual claims (marked `Crux? = Y`) remain unverified (`? status`). There is no validation gate requiring crux facts to be resolved before the analysis is considered reviewed.

## Goals

1. **Enable web discovery for fact verification**: Ensure `$check` can discover corroborating/disconfirming sources (Claude: add `WebSearch`; other integrations: specify the available web search facility).
2. **Add a procedural verification loop**: Make Stage 2 explicitly require a minimum verification attempt (DB-first, then web search) for crux factual claims, with recorded queries and citations (or a documented failure mode).
3. **Catch "reviewed/confident without verification" patterns**: Add validator warnings when factual claims remain unverified but the analysis is marked `[REVIEWED]`, or when high-credence factual claims lack citations/verification attempts.
4. **Gate `[REVIEWED]` status**: Prevent `[REVIEWED]` when crux factual claims have not been verified/refuted *or* explicitly marked as "searched, not found/blocked" with documented attempts.

## Non-goals

- Full automated fact-checking pipeline (out of scope; this is about giving agents the tools and instructions to verify within the existing workflow).
- Changes to the DB schema or LanceDB tables (this is a methodology/template/config change).
- Rearchitecting the multi-pass workflow (covered by `PLAN-analysis-rigor-improvement.md`).
- Adding web discovery/search to all skills in v0.3.2 (scope this release to `$check`; defer `$analyze` parity to v0.3.3).

## Affected Files

```
realitycheck/
 ├── integrations/
 │    └── _config/
 │         └── UPDATE skills.yaml                    # Claude: add WebSearch to check (and maybe analyze) allowed_tools
 ├── integrations/
 │    └── _templates/
 │         ├── skills/
 │         │    └── UPDATE check.md.j2               # Add verification loop instructions (tool-agnostic wording)
 │         └── tables/
 │              └── UPDATE factual-claims-verified.md.j2  # Add Claim ID + Search Notes + status codes
 ├── methodology/
 │    └── workflows/
 │         └── REGENERATED check-core.md             # Generated from templates via make assemble-skills (do not edit directly)
 ├── scripts/
 │    ├── UPDATE analysis_formatter.py               # Align inserted Stage2 table with updated verification contract
 │    └── UPDATE analysis_validator.py               # Add reviewed/crux gate + high-credence-unverified warnings
 ├── tests/
 │    ├── UPDATE test_analysis_formatter.py          # Updated Stage2 table contract and status codes
 │    └── UPDATE test_analysis_validator.py          # Validator warnings/gates for factual verification rigor
 └── docs/
      ├── NEW PLAN-v0.3.2.md                         # This document
      └── UPDATE TODO.md                             # Add this item to roadmap
```

## Implementation

### Change 1: Ensure a web discovery tool is available to `$check` (per integration)

**File**: `integrations/_config/skills.yaml`

Add `"WebSearch"` to the `check` skill's Claude `allowed_tools` list:

```yaml
    claude:
      argument_hint: "<url> [--domain DOMAIN] [--quick] [--no-register] [--continue]"
      allowed_tools:
        - "WebFetch"
        - "WebSearch"          # NEW: enable fact verification via web search
        - "Read"
        - "Write"
        - "Bash(uv run python scripts/db.py *)"
        # ... rest unchanged
```

**Decision (v0.3.2 scope)**: Add `WebSearch` to Claude `check` only. Defer `analyze` parity to v0.3.3 to keep this release tightly scoped to `$check`.

**Skill text (all integrations)**: Update the `$check` skill template to refer to "web search/web discovery" generically, with integration examples rather than hard-coding a single tool name. For example:
- Claude Code: `WebSearch`
- OpenAI/Codex toolings: `web.run` (`search_query`, then `open`) or equivalent
- Amp/OpenCode: whichever web search tool is available in that runtime

This keeps the template portable across Codex/Amp/OpenCode while still being concrete.

**Rationale**: `WebFetch` lets agents read a known URL; verification requires discovery ("find reporting on Amodei's Davos remarks") not just retrieval.

### Change 2: Add verification loop to Stage 2 methodology

**Source-of-truth files**: `integrations/_templates/skills/check.md.j2`, `integrations/_templates/tables/factual-claims-verified.md.j2`

**Regenerated output**: `methodology/workflows/check-core.md` via `make assemble-skills` (do not hand-edit).

Add an explicit verification procedure to Stage 2 between claim extraction and the "Key Factual Claims Verified" table. The procedure should:

1. **Identify verification targets**:
   - All claims typed `[F]` with `Crux? = Y` (required),
   - plus any `[F]` claims with weak evidence (`E5`/`E6`) or high credence (e.g., `>= 0.7`).
2. **DB-first check**: Before using the web, search the local RC database for existing coverage/citations:
   - `rc-db search "<neutral keywords>"` (and/or search by named entities + date + venue).
   - If a suitable source already exists in the DB, cite it and (if needed) register it as supporting evidence.
3. **Web discovery strategy (timeboxed)**:
   - For each crux target, run **>=2 distinct queries** (required, measurable) with a bounded effort target (e.g., 5–10 minutes).
   - Prefer primary sources (official docs, transcripts, video) then reputable secondary reporting.
   - Use neutral query terms (avoid the source's rhetoric framing).
4. **Record results in Stage 2**:
   - Use this final column order:
     - `Claim ID | Claim (paraphrased) | Crux? | Source Says | Actual | External Source | Search Notes | Status`
   - Update the "Key Factual Claims Verified" table to include:
     - **Claim ID** (reference extracted claim IDs; required for crux rows)
     - **Search Notes** (queries tried + date/timebox notes)
   - Expand the **Status** codes so we can distinguish "not attempted" from "attempted but unresolved":
     - `ok` = verified
     - `x` = refuted
     - `nf` = searched, not found (no credible external source after timeboxed search)
     - `blocked` = access/capture blocked (paywall/JS/region/etc.)
     - `?` = not yet attempted
   - For each target, record: what the source said, what verification found, the external citation(s), and the queries attempted if unresolved (`nf`/`blocked`).
5. **Update claim metadata + provenance**:
   - If verification changes the claim materially (evidence level/credence/status), update the claim table and add `evidence_links` + `reasoning_trails` rows (append-only provenance).
6. **Decision gate**:
   - Do **not** mark the analysis `[REVIEWED]` if any crux `[F]` claim is still `?`.
   - Allow `[REVIEWED]` with a crux claim in `nf`/`blocked` only if `Search Notes` is filled and the analysis summary explicitly treats the claim as unresolved/unknown (i.e., does not smuggle it in as a settled fact).
   - If a claim turns out not to be checkable/verifiable, retype it (e.g., `[H]`) with an explicit operationalization note; otherwise keep it `[F]` and use `nf`/`blocked` as the documented failure mode.

Example template addition:

```markdown
### Verification Procedure (Stage 2)

For each `[F]`-typed claim, especially crux claims:

0. **DB-first**: `rc-db search "<keywords>"` to reuse existing sources/citations.
1. **Search**: Use your environment's web search tool with neutral terms to find primary or secondary sources.
   - Try the specific factual assertion (e.g., "Amodei Davos H200 exports China")
   - Try the broader context (e.g., "Davos 2026 AI chip exports")
   - Required: >=2 distinct queries per crux claim
   - Target effort: 5–10 minutes per crux claim
2. **Evaluate**: Check discovered sources against the claim.
   - Does the source confirm the claim? Record URL + relevant excerpt.
   - Does the source contradict or modify the claim? Record and adjust.
   - No relevant sources found? Mark `Status = nf` and record queries/timebox in Search Notes.
   - Access blocked? Mark `Status = blocked` and record queries + failure mode in Search Notes.
3. **Update**: Adjust evidence level and credence based on what was found.
4. **Gate**: Do not mark analysis as [REVIEWED] if crux [F] claims remain `?` (not attempted).
```

### Change 2b: Align formatter output contract with the Stage 2 verification table

**Files**: `scripts/analysis_formatter.py`, `tests/test_analysis_formatter.py`

The framework formatter currently inserts a legacy "Key Factual Claims Verified" table schema that does not match the methodology/template contract.

Update the formatter to insert the updated Stage 2 table contract (Claim ID + Search Notes + `ok/x/nf/blocked/?` statuses, in the exact column order above), so new analyses produced/normalized by the formatter do not immediately violate the verification gate expectations.

### Change 3: Add verification-rigor checks to validator

**File**: `scripts/analysis_validator.py`

Add validation warnings for "reviewed/confident without verification" patterns:

| Condition | Severity | Message |
|-------------|----------|---------|
| `[REVIEWED]` + Stage2 `Crux? = Y` + `Status = ?` | WARN (ERROR with `--rigor`) | "Analysis marked [REVIEWED] but crux factual claim {id} is not attempted (Status=?)" |
| `[REVIEWED]` + Stage2 `Crux? = Y` + (`Status = nf` or `blocked`) + missing Search Notes | WARN (ERROR with `--rigor`) | "Crux factual claim {id} is unresolved but lacks Search Notes documenting the attempt" |
| Stage2 `Crux? = Y` + missing Claim ID | WARN | "Crux factual verification row is missing Claim ID (required for auditable gating)" |
| `[REVIEWED]` + Stage2 has **no** `Crux? = Y` rows | WARN (ERROR with `--rigor`) | "Analysis marked [REVIEWED] but Stage 2 does not identify any crux factual claim (Crux?=Y required)" |
| `[REVIEWED]` + Stage2 `Crux? = Y` + `Status in {ok, x}` + missing External Source | WARN (ERROR with `--rigor`) | "Crux factual claim {id} marked verified/refuted but lacks an External Source citation" |
| Claim table: `[F]` + (`Status != ok` and `Status != x`) + `credence >= 0.7` | WARN | "High-credence factual claim {id} is not verified/refuted — add citation/verification or lower credence" |

This aligns with the existing validator pattern: WARN by default, ERROR with `--rigor`.

### Change 4: Add `[REVIEWED]` gate for crux claims

**File**: `scripts/analysis_validator.py`

Add a validation check that prevents `[REVIEWED]` status when crux factual claims remain unverified:

- Parse the "Key Factual Claims Verified" table (updated to include Claim IDs).
- For any row where `Crux? = Y` and `Status = ?` and the analysis is `[REVIEWED]`, emit a warning (or error with `--rigor`).
- For any row where `Crux? = Y` and `Status in {nf, blocked}` but `Search Notes` is empty, emit a warning (or error with `--rigor`).
- Optionally (future-hardening): require that unresolved crux rows include documented search attempts (query strings + date) before they can be considered "handled" even in non-reviewed drafts.

## Relationship to Other Plans

- **PLAN-analysis-rigor-improvement.md**: That plan addresses structural rigor (layer/actor/scope, primary capture, corrections tracking). This plan addresses *procedural* rigor (actually performing verification within the workflow). They are complementary and independent.
- **PLAN-epistemic-provenance.md**: Provenance tracks *why* credence was assigned; this plan ensures the verification step that informs credence actually happens.
- **PLAN-quality-regression-fix.md**: That plan restored missing templates; this plan adds a missing *procedural step* to the existing templates.

## Tests and Verification Strategy

### Validator tests (`tests/test_analysis_validator.py`)

1. **High-credence unverified factual claim warning**:
   - Test that `[F]` + `Status=?` + `credence>=0.7` triggers a WARN.
   - Test that `[F]` + `Status=?` + `credence<0.7` does NOT trigger this warning.

2. **Crux-unverified gate**:
   - Test that Stage2 `Crux? = Y` + `Status = ?` with `[REVIEWED]` triggers a WARN.
   - Test that `Crux? = Y` + `Status = ?` without `[REVIEWED]` does NOT trigger (analysis still in progress).
   - Test that `Crux? = Y` + `Status = ok` with `[REVIEWED]` passes cleanly.
   - Test that `Crux? = Y` + `Status = nf` with `[REVIEWED]` passes if Search Notes is present.
   - Test that `Crux? = Y` + `Status = nf` with `[REVIEWED]` triggers a WARN if Search Notes is missing.
   - Test that `Crux? = Y` + `Status = blocked` with `[REVIEWED]` passes if Search Notes is present.
   - Test that `Crux? = Y` + `Status = blocked` with `[REVIEWED]` triggers a WARN if Search Notes is missing.
   - Test that `Crux? = N` + `Status = ?` with `[REVIEWED]` does NOT trigger (non-crux unverified is acceptable).
   - Test that missing Claim ID on a crux row triggers a WARN.
   - Test that `[REVIEWED]` with **no** `Crux? = Y` row triggers a WARN (Stage2 requires >=1 crux).
   - Test that `[REVIEWED]` + crux `Status=ok` with missing External Source triggers a WARN.

3. **`--rigor` escalation**:
   - Test that the above WARNs become ERRORs when `--rigor` flag is set.

4. **Realistic markdown fixtures**:
   - Use full markdown tables (header + separator + multi-row body), not simplified row stubs, for all Stage 2 parsing tests.

### Manual verification

- Re-run `$check` on a source with verifiable factual claims and confirm that:
  - The agent uses web discovery (search) to look up crux facts.
  - The "Key Factual Claims Verified" table is populated with actual external sources.
  - Crux `[F]` claims that cannot be verified are either retyped or explicitly documented as `nf/blocked` with Search Notes.
  - The analysis does not reach `[REVIEWED]` with crux claims still `?`.

### Regression test

- Re-analyze `aakashgupta-2026-amodei-hawkish-china-thread` with the updated workflow and confirm that the Davos/H200 claim (GEO-2026-033) is verified in the first pass rather than requiring manual follow-up. (Note: the original analysis from `3ee7019` is being reworked with a fact-checking focus as of 2026-02-15.)

## Release Notes (v0.3.2)

### Added
- Web discovery enabled for `$check` (Claude: `WebSearch`) so agents can discover corroborating/disconfirming evidence during fact verification.
- Explicit verification loop procedure in Stage 2 methodology for `[F]`-typed claims.
- Validator warnings for "reviewed/confident without verification" patterns (crux unresolved in `[REVIEWED]`, high-credence unverified `[F]` claims).
- Validator gate preventing `[REVIEWED]` status when crux factual claims are still `?` (not attempted).

### Changed
- Claude `check` skill allowed tools list now includes `WebSearch`.
- Stage 2 "Key Factual Claims Verified" table includes Claim IDs + Search Notes, with explicit `nf/blocked/?` status codes.
- Stage 2 methodology includes procedural verification instructions alongside existing output templates.

### Fixed
- Analyses could reach `[REVIEWED]` status with crux factual claims still `?` (no verification attempt recorded).

## Post-Implementation Addenda (2026-02-16)

The following follow-ups were included in the v0.3.2 implementation pass to reduce drift and improve end-user safety:

- End-user integration update path: `scripts/integration_sync.py`, auto-sync on first `rc-*` run after version change, and manual `rc-db integrations sync`.
- Markdown parsing hardening in formatter/validator to tolerate simple markdown wrappers and escaped pipes in tables (reduces false negatives and fail-open states).
- New `rc-db backup` command to create timestamped `.tar.gz` snapshots of the LanceDB directory.
