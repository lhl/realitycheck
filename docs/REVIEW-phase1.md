# Phase 1 Review (v0.1.0-alpha)

**Date**: 2026-01-20
**Reviewed range**: `origin/main` (`ef64c3b`) → `v0.1.0-alpha` (`48b537f`)
**Scope**: Phase 1 deliverables in `docs/IMPLEMENTATION.md` (port framework code + tests, set up packaging, create initial plugin/methodology/docs scaffolding).

**Review updated**: 2026-01-20 with inline resolutions.

## Summary

Phase 1 is functionally complete: core scripts/tests are ported, `uv` packaging exists (`pyproject.toml`, `uv.lock`), and the repo is tagged `v0.1.0-alpha`. The groundwork for separating "framework" vs "analysis data" is in place.

The main follow-up is **docs/implementation drift**: several new docs describe CLI commands and schemas that **do not match** what is implemented in `scripts/*.py` right now. This will create immediate confusion for anyone trying to use the project, and it will make Phase 2 harder (because we won't know which interface is "real").

## What's Solid

- **Port completeness**: `scripts/` and `tests/` are fully carried over; `uv run pytest` passes with embedding tests skipped (as documented).
- **Packaging baseline**: `pyproject.toml` defines console scripts (`rc-db`, `rc-validate`, `rc-export`, `rc-migrate`, `rc-embed`) and pins core deps.
- **Repo hygiene**: `.gitignore`, `.gitattributes` (LFS), and `LICENSE` exist.
- **Methodology extraction**: `methodology/` + templates exist and are cleanly separated from tooling code.
- **Plugin skeleton**: `plugin/.claude-plugin/plugin.json` and command markdown files exist (good starting point for Phase 2 wiring).

## Key Gaps / Risks (Prioritized)

### P0: CLI docs don't match current CLI

Current `scripts/db.py` CLI supports only:
- `rc-db init`
- `rc-db stats`
- `rc-db reset`
- `rc-db search <query>`

But `docs/WORKFLOWS.md` currently documents commands that **do not exist**, e.g.:
- `rc-db add claim ...`
- `rc-db add source ...`
- `rc-db related ...`
- `rc-db import ...`
- `rc-db update-domain ...`

This is a blocking clarity problem because it's impossible to tell whether:
1) the docs are "future interface" (planned), or
2) Phase 1 intended to implement these subcommands but didn't.

**Recommendation** (pick one explicitly in Phase 2 planning, and make docs reflect it):
- **Option A (fastest)**: rewrite `docs/WORKFLOWS.md` to only use commands that exist today, and mark the rest as "Planned (Phase 2)".
- **Option B (more powerful)**: implement the CLI subcommands documented in `docs/WORKFLOWS.md` (and update tests accordingly).

> **Resolution**: Fixed. Applied Option A. `docs/WORKFLOWS.md` now:
> - Lists only implemented commands in a table at the top
> - Documents only real commands (`init`, `stats`, `reset`, `search`, `status`, `generate`, `regenerate`)
> - Adds "Planned Features (Phase 2)" section listing unimplemented commands
> - Provides "Programmatic Access" section for operations not in CLI

### P0: `docs/SCHEMA.md` does not match the actual LanceDB schemas

`docs/SCHEMA.md` currently documents fields that are not present in `scripts/db.py` schemas (e.g., `created_at`, `updated_at`, `related_ids`), and omits fields that do exist (e.g., claim provenance fields like `first_extracted`, `extracted_by`).

**Recommendation**:
- Treat `scripts/db.py` schemas as canonical for v0.1.0-alpha and update `docs/SCHEMA.md` accordingly.
- If the intent is to evolve schemas (add timestamps, rename fields, etc.), capture that as a Phase 2/3 spec and apply via tests + implementation.

> **Resolution**: Fixed. `docs/SCHEMA.md` completely rewritten to match actual `scripts/db.py` schemas:
> - Claims: Added `first_extracted`, `extracted_by`, `supports`, `contradicts`, `depends_on`, `modified_by`, `part_of_chain`, `version`, `last_updated`, `notes`; removed fictional `created_at`, `updated_at`, `related_ids`
> - Sources: Fixed to use `author` (list), `year` (int32), added `reliability`, `bias_notes`, `claims_extracted`, `analysis_file`, `topics`, `domains`, `status`
> - Predictions: Fixed to use `claim_id`/`source_id` as keys (no separate `id`), added all actual fields
> - Contradictions: Fixed to use `claim_a`/`claim_b` instead of `claim_ids` list
> - Definitions: Fixed to match actual schema with `analysis_id` instead of `source_ids`
> - Added Source Types enum documentation
> - Decision logged: "Code schemas are canonical for v0.1.x"

### P0: Plugin docs imply wrapper scripts that don't exist yet

`docs/PLUGIN.md` describes shell wrappers in `plugin/scripts/` (e.g., `validate.sh`, `embed.sh`, `export.sh`) and optional hooks, but:
- `plugin/scripts/` is empty
- `plugin/lib/` is empty
- `plugin/commands/*.md` currently read like usage docs/methodology, not "executable" command definitions

This is fine if Phase 1's intent was "plugin docs only", but then `docs/PLUGIN.md` should clearly label wrappers/hooks as "Planned (Phase 2)" to avoid implying the plugin already automates execution.

> **Resolution**: Fixed. `docs/PLUGIN.md` rewritten with:
> - New "Current Status (v0.1.0-alpha)" section explicitly stating what exists vs what's planned
> - Clear statement: "The current plugin is **methodology-only**"
> - Notes on each command indicating whether it's methodology-guided or has a backend
> - "Planned Features (Phase 2)" section at bottom covering shell wrappers, bundled scripts, and lifecycle hooks

### P1: `rc-embed` docs use a non-existent subcommand name

`scripts/embed.py` uses `rc-embed status|generate|regenerate`, but `docs/WORKFLOWS.md` says `rc-embed check`.

**Recommendation**: rename `check` → `status` in docs (or implement `check` as an alias; docs-only fix is easiest).

> **Resolution**: Fixed. `docs/WORKFLOWS.md` now uses correct command `rc-embed status`.

### P1: Versioning/tagging inconsistency

Repo tag: `v0.1.0-alpha`
Python package version: `0.1.0` (`pyproject.toml`)
Plugin version: `0.1.0` (`plugin/.claude-plugin/plugin.json`)

**Recommendation**:
- If you intend "alpha" as a real pre-release, consider making the package version PEP 440 compatible (e.g., `0.1.0a1`) and aligning plugin.json's version string.
- If the intent is "0.1.0 is the version, alpha is only a git tag", document that choice in `docs/IMPLEMENTATION.md`/Decision Log.

> **Resolution**: Documented. Decision logged in `docs/IMPLEMENTATION.md`:
> "Git tag is pre-release marker only - Package version stays `0.1.0` (PEP 440); `alpha` is git tag only, not in version string"
>
> Rationale: The git tag communicates "not production ready" to humans browsing the repo, while the package version stays clean for tooling. When we're ready for stable release, we'll tag `v1.0.0` and update pyproject.toml to `1.0.0`.

### P1: Process mismatch — commit metadata violates repo rules

`AGENTS.md` states "No bylines or co-author footers in commits", but Phase 1 commits include `Co-Authored-By:` lines and "Generated with …" trailers.

**Recommendation** (going forward):
- Keep commit messages compliant with `AGENTS.md` (no auto-generated footers).
- If you want provenance, put it in `docs/IMPLEMENTATION.md` worklog entries instead.

> **Resolution**: Documented and will follow going forward. Decision logged in `docs/IMPLEMENTATION.md`:
> "No co-author footers in commits - Project rule (AGENTS.md) wins over external tooling defaults; use worklog for provenance"
>
> The existing commits with footers will remain (rewriting history is worse), but future commits will follow the project rule.

### P2: `docs/IMPLEMENTATION.md` checklist doesn't reflect the tag

`docs/IMPLEMENTATION.md` still shows "Tag as v0.1.0-alpha" unchecked, but the repo is tagged.

**Recommendation**: tick it, and optionally record the tag SHA in the worklog.

> **Resolution**: Fixed. Checklist item now reads:
> `- [x] Tag as v0.1.0-alpha (\`48b537f\`)`

## Suggested "Sprint 2" Fix List (Actionable)

1. **Decide the "real CLI" for v0.1.x**
   - If Phase 2 will add `rc-db claim add|get|list|update` etc, write that as a spec and implement it.
   - If not, rewrite docs to match the minimal CLI and rely on direct Python calls (not recommended for plugin workflows).

   > **Status**: Docs fixed to match minimal CLI. Phase 2 spec should define extended CLI if needed.

2. **Make docs "true"**
   - Update `docs/SCHEMA.md` to match `scripts/db.py` today.
   - Update `docs/WORKFLOWS.md` to only reference real commands, or clearly mark planned commands.
   - Update `docs/PLUGIN.md` to mark wrappers/hooks as planned until `plugin/scripts/` exists.

   > **Status**: All three docs updated.

3. **Wire the plugin (or explicitly keep it methodology-only)**
   - If wiring: add wrapper scripts in `plugin/scripts/` and update `plugin/commands/*.md` to invoke them.
   - If methodology-only: adjust wording so it doesn't promise DB writes/exports.

   > **Status**: Explicitly labeled methodology-only for v0.1.0-alpha. Wiring is Phase 2.

4. **Resolve CLAUDE.md vs AGENTS.md**
   - Current `CLAUDE.md` is a symlink to `AGENTS.md` (dev workflow), while the plan suggests `CLAUDE.md` should be agent-facing methodology pointers.
   - Pick one pattern and document it (this affects how the plugin and future contributors behave).

   > **Status**: Deferred. Item remains on Phase 1 punchlist: "Decide CLAUDE.md vs AGENTS.md roles (remove symlink if needed)". Current symlink works for now; will revisit when plugin needs distinct agent-facing instructions.

## Notes

The core "separation" goal (framework repo cleanly containing reusable tooling + methodology, no analysis data) looks on track. The next risk is not technical—it's **interface clarity**: ensure docs, CLI, and plugin behavior agree before migrating a real analysis repo or building more automation.

> **Post-fix status**: Docs now accurately reflect v0.1.0-alpha capabilities. The minimal CLI, methodology-only plugin, and accurate schemas are documented. Phase 2 can confidently build on this foundation.
