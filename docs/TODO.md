# TODO

Tracking future work items.

## Pip-Friendly Skill/Plugin Installation (Next Up)

**Problem**: Integration install currently requires a source checkout (`make install-skills-claude`, etc.) or manual symlink setup. Users who install via `pip install realitycheck` have no way to install skills/plugins for their editor without cloning the repo. This is the biggest friction point for new users.

**Context**: v0.3.2 added `integration_sync.py` and bundled integration assets in the wheel (`integrations/**`, `methodology/workflows/check-core.md`), so the files are already available inside the installed package. What's missing is a user-facing command that wires them into the right editor/tool locations.

**Desired UX**:
```bash
pip install realitycheck

# Install skills/plugin for your editor(s)
rc-db integrations install claude    # symlinks/copies Claude Code plugin + skills
rc-db integrations install codex     # installs Codex skills
rc-db integrations install amp       # installs Amp skills
rc-db integrations install opencode  # installs OpenCode skills
rc-db integrations install --all     # install all available integrations

# Show what's installed and where
rc-db integrations status

# Update after upgrading realitycheck
rc-db integrations sync              # already exists (v0.3.2)
```

**Key considerations**:
- Discover the installed package's integration assets via `importlib.resources` or `pkg_resources` (not hardcoded paths)
- Each integration has different target directories (Claude: `~/.claude/plugins/` or project `.claude/`; Codex: `$CODEX_HOME/skills/`; Amp: `~/.amp/skills/`; OpenCode: `~/.opencode/skills/`)
- Symlinks vs copies: symlinks are nicer for auto-update on `pip install --upgrade`, but may not work on all platforms or if installed in an isolated tool venv
- Should work for both `pip install` and source-checkout users (detect which mode we're in)
- Existing `integration_sync.py` handles the sync/update case; this extends it with initial install from wheel assets
- Consider whether `install` should be a new subcommand or an extension of existing `sync --install-missing`

**Relationship to existing work**:
- `integration_sync.py` (v0.3.2) already handles refreshing existing symlinks and `--install-missing` for integrations that are partially set up
- The Makefile `install-skills-*` targets do the right thing for source checkouts; this is the pip-install equivalent
- The `uv tool install` TODO (below) is related but orthogonal — that's about CLI isolation, this is about getting skills into editors

**Status**: Next up — planning needed.

---

## CLI Output Ergonomics: Strip Embeddings, Improve Text Format

**Problem**: JSON output from `db.py search`, `claim list`, etc. includes full 384-dim float32 embedding vectors in every result. Each embedding is ~8.4KB of JSON — **89% of the per-claim payload**. A 10-result search dumps ~85KB of embedding noise into agent context windows, wasting tokens and polluting reasoning. This was discovered during a multi-search analysis session where agents were piping JSON through Python one-liners to get usable output.

**Secondary issue**: `--format text` for `search` truncates claim text at 80 chars and omits `source_ids`, `operationalization`, `assumptions`, and `falsifiers`. The `claim list --format text` output is better but still sparse. When JSON is the default and it dumps embeddings, agents have no good option.

**Solution** (three incremental changes):

1. ✅ **Strip embeddings from JSON by default** — `_output_result()` now strips `embedding` and `_distance` fields from JSON output by default. All 17 subcommands with `--format` gained a `--full` flag to opt into raw output. (Shipped v0.3.4, 2026-03-03)

2. **Improve `--format text` for search**: Show full text (or 200+ chars), `source_ids`, evidence level, and key metadata. Match the richer format already used by `claim list --format text`.

3. **Consider defaulting search to `--format text`**: Once JSON is clean (no embeddings), this becomes less urgent. But text is more natural for interactive/agent use. Could also add `--format compact` as a middle ground (JSON without embeddings, single-line per claim).

**Impact**: Immediate improvement for every agent session that queries the DB. The embedding strip alone reduces context burn by ~9x per search query.

**Scope**: Small — mostly changes to `_output_result()` and the `search` CLI handler. No schema changes, no new tables.

**Status**: Step 1 complete (2026-03-03). Steps 2-3 remain for future work.

---

## Source Capture Tooling (Browser-Based Fetch)

**Problem**: During analysis sessions, many source URLs are unfetchable via simple HTTP — JS-rendered pages, soft paywalls, large PDFs, and sites that block non-browser user agents. In a recent session, 2 of 6 article fetches failed entirely (iNews, Guardian blocked), 1 timed out (WaPo), and 1 PDF exceeded size limits (Campaign Legal Center). The `reference/captured/` convention exists in data repos but capture is currently manual.

**Context**: The data repo already stores captured sources (e.g., `reference/captured/deanwball-2026-clawed.html` with a corresponding `.extracted.json`). What's missing is a CLI command to automate this.

**Desired UX**:
```bash
# Capture a URL to reference/captured/ with auto-naming
rc-db source capture https://www.example.com/article \
  --source-id "example-2026-article"

# Captures HTML (rendered via headless browser), saves to:
#   reference/captured/example-2026-article.html
# Optionally extracts text:
#   reference/captured/example-2026-article.extracted.json

# For PDFs:
rc-db source capture https://example.com/report.pdf \
  --source-id "example-2026-report"
# Saves PDF directly, optionally extracts text via pdftotext/pymupdf
```

**Key considerations**:
- **playwright-cli** (or `playwright` Python package) for JS rendering — handles most JS-heavy sites, tracker dashboards, Substack, etc.
- Won't solve hard paywalls (NYT, WaPo subscriber content) — those remain manual
- Should integrate with `rc-db source add` to register the source in the DB with the captured artifact path
- Optional text extraction step (readability/trafilatura for HTML, pymupdf for PDF)
- Dependency weight: playwright is heavy (~100MB browsers). Should be an optional extra (`pip install realitycheck[capture]`) not a core dep
- Could also expose as a plugin command (`/capture <url>`) for in-session use

**Relationship to existing work**:
- `reference/captured/` convention already exists and is used by analysis workflows
- Source YAML files already reference `captured_artifact` paths
- The `/check` workflow's Stage 2 verification could invoke this for primary document capture

**Scope**: Medium — new command, optional dependency, extraction pipeline. Not blocking but would meaningfully improve analysis throughput.

**Status**: Planning — queue after CLI output ergonomics.

---

## Token Usage Capture (Backfill + Default Automation)

**Plan**: [PLAN-token-usage.md](PLAN-token-usage.md)
**Implementation**: [IMPLEMENTATION-token-usage.md](IMPLEMENTATION-token-usage.md)

**Problem**: Many `analysis_logs` entries lack token/cost fields because usage capture is optional and check boundaries are not consistently recorded.

**Solution** (delta accounting):
- Auto-detect current session by tool (Claude Code, Codex, Amp)
- At check start: snapshot session tokens → baseline
- At check end: snapshot session tokens → final; check_tokens = final - baseline
- Optional per-stage breakdown via `rc-db analysis mark --stage ...`
- Backfill historical entries (best-effort when baseline wasn't recorded)

**Key insight**: Each tool stores sessions with UUIDs. Sessions can span multiple checks, so we use delta accounting rather than session totals.

**Status**: ✅ Complete - implemented lifecycle commands (`analysis start/mark/complete`), session detection, backfill, and synthesis attribution.

---

## Epistemic Provenance / Reasoning Trails (Major Feature)

**Plan**: [PLAN-epistemic-provenance.md](PLAN-epistemic-provenance.md)
**Implementation**: [IMPLEMENTATION-epistemic-provenance.md](IMPLEMENTATION-epistemic-provenance.md)

**Problem**: Reality Check extracts claims and assigns credence, but lacks structured traceability for *why* a claim has a given credence. We risk becoming a source of unconfirmable bias.

**Solution**:
- `evidence_links` table: Explicit links between claims and supporting/contradicting sources
- `reasoning_trails` table: Capture the reasoning chain for credence assignments
- Rendered markdown: Per-claim reasoning docs browsable in data repo
- Validation: Enforce that high-credence claims (≥0.7) have explicit backing (configurable: warn default, `--strict` errors)
- Portability export: Deterministic YAML/JSON dump of provenance (regen from DB)
- Audit-log linkage: Attribute evidence/reasoning to specific analysis passes (tool/model)
- Workflow integration: Evidence linking + reasoning capture in `/check`

**Scope**: Large feature sprint - schema changes, CLI, validation, rendering, workflow updates (9 phases, ~60 test cases).

**Status**: ✅ Complete - all 9 phases implemented (schema, CRUD, CLI, validation, export, formatter/validator updates, templates, docs, migration support).

---

## Analysis Rigor Improvements (Primary Evidence, Layering, Corrections)

**Plan**: [PLAN-analysis-rigor-improvement.md](PLAN-analysis-rigor-improvement.md)
**Implementation**: [IMPLEMENTATION-analysis-rigor-improvement.md](IMPLEMENTATION-analysis-rigor-improvement.md)

**Dependency**: ✅ Epistemic Provenance is complete (2026-01-30) and satisfies part of this plan (`evidence_links`, `reasoning_trails`, validation gates, append-only corrections semantics).

**Problem**: Analyses can still produce confident-looking evidence/credence tables that conflate:
- asserted authority vs lawful authority vs practiced reality,
- ICE vs CBP/DHS actor attribution,
- scoped/conditional claims vs “can anywhere/always” overgeneralizations,
- stale sources vs corrected/updated reporting,
- secondary reporting vs accessible primary documents.

**Solution**:
- Enforce `Layer/Actor/Scope/Quantifier` in claim tables (template-level)
- Primary-document-first capture for high-impact claims (memos, court orders, filings, PDFs)
- Corrections/recency tracking as a first-class workflow step (with claim impact)
- Court citation hygiene (majority vs dissent; posture; controlling vs non-controlling)
- Multi-pass refinement workflow that preserves provenance and reviewer disagreement cleanly

**Status**: ✅ Implemented (2026-02-01) - rigor-v1 tables, `--rigor` flag, DB schema extensions complete.

---

## Verification Loop for Factual Claims (v0.3.2)

**Plan**: [PLAN-v0.3.2.md](PLAN-v0.3.2.md)
**Implementation**: [IMPLEMENTATION-v0.3.2.md](IMPLEMENTATION-v0.3.2.md)

**Problem**: `$check` can enumerate/flag factual claims but does not consistently verify crux facts; analyses can reach `[REVIEWED]` with crux factual claims still unattempted.

**Solution**:
- Enable web discovery (Claude: `WebSearch`) for `$check`
- Add an explicit Stage 2 verification procedure (DB-first, then web search, timeboxed)
- Update the Stage 2 "Key Factual Claims Verified" table contract (Claim ID + Search Notes + `nf/blocked/?`)
- Add validator warnings/gates for reviewed/unverified and high-credence-unverified factual claims

**Status**: ✅ Complete — shipped in v0.3.2 (2026-02-19).

---

## Analysis Audit Log

**Plan**: [PLAN-audit-log.md](PLAN-audit-log.md)
**Implementation**: [IMPLEMENTATION-audit-log.md](IMPLEMENTATION-audit-log.md)

**Problem**: No durable record of *how* an analysis was produced (who/what/when/cost).

**Solution**: `analysis_logs` table + in-document "Analysis Log" section.

**Status**: Complete (see implementation doc).

---

## Agent Ergonomics (Upsert, Doctor, Repair, Actionable Errors)

**Plan**: [PLAN-agent-ergonomics.md](PLAN-agent-ergonomics.md)
**Implementation**: [IMPLEMENTATION-agent-ergonomics.md](IMPLEMENTATION-agent-ergonomics.md)

**Problem**: Agents re-run workflows and frequently hit avoidable friction: duplicate IDs on import, brittle DB path configuration, non-actionable validation failures, and DB invariant drift.

**Solution**:
- `--on-conflict {error,skip,update}` for `rc-db import` (and key add paths where it matters)
- `rc-db doctor` and shared DB auto-detection (reduce reliance on `REALITYCHECK_DATA`)
- `rc-db repair` (safe/idempotent): recompute source↔claim backlinks + `[P]` prediction stubs; report duplicates
- Validation/CLI errors include exact remediation commands (prefer suggesting `rc-db repair`)

**Status**: Planning.

---

## Ergonomics (To Decide)

**Plan**: [PLAN-ergonomics-todecide.md](PLAN-ergonomics-todecide.md)

Items that are likely valuable but require workflow/product decisions first:

- One-shot finish/publish command/script (import → analysis add → validate → update README → git add/commit/push)
- `rc-analysis new <source-id> --from-url URL` skeleton generator (analysis `.md` + `.yaml` stub)

**Status**: TBD decisions; keep out of implementation until decided.

---

## Installation: `uv tool install` / `pipx` support

**Context:** Currently we recommend `uv pip install realitycheck` which installs to the active venv or system Python. A user suggested using `uv tool install realitycheck` instead, which creates an isolated venv and adds CLI tools to PATH (similar to `pipx`).

**Trade-offs to consider:**

1. **Isolation** - `uv tool install` keeps realitycheck deps separate from user projects (cleaner)
2. **Skill execution** - Skills tell agents to run `uv run python scripts/db.py` which assumes framework venv context. Would need to change to `rc-db` everywhere.
3. **Library usage** - If users want to `import scripts.db` programmatically, they need it in their project venv, not tool-isolated
4. **Dual install** - Some users may want both: CLI tools via `uv tool install` AND library in project venv

**Before changing:**
- Audit all skills to ensure they use `rc-db` / `rc-validate` / `rc-export` instead of `uv run python scripts/...`
- Test `uv tool install realitycheck` end-to-end with a fresh user
- Document when to use which installation method

**Status:** Punted - current approach works for users with managed envs (mamba, conda, project venvs)
