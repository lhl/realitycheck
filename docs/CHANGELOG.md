# Changelog

All notable changes to `realitycheck` are documented here.

This project follows [Semantic Versioning](https://semver.org/) and the structure is inspired by [Keep a Changelog](https://keepachangelog.com/).

## Unreleased

## 0.3.2 - 2026-02-19

**Verification Loop + Upgrade Sync Hardening** — closes factual-verification gaps and ensures end users pick up refreshed integrations after upgrading.

### Added

- Stage 2 factual verification contract update across templates/formatter/workflow docs:
  - `Claim ID | Claim (paraphrased) | Crux? | Source Says | Actual | External Source | Search Notes | Status`
  - status semantics: `ok`, `x`, `nf`, `blocked`, `?`
- Claude `check` integration enables `WebSearch`; shared skill text adds tool-agnostic DB-first + web discovery verification loop.
- New validator gating for factual verification rigor (`analysis_validator.py`):
  - reviewed crux `Status=?` gate
  - reviewed crux unresolved (`nf`/`blocked`) requires Search Notes
  - reviewed crux `ok`/`x` requires External Source
  - reviewed analysis must include at least one crux factual row
  - high-credence unresolved factual warnings (`credence >= 0.7`)
- New `rc-db backup` command to create timestamped `.tar.gz` snapshots of the LanceDB directory (optional `--output-dir`, `--prefix`).
- New integration sync module (`scripts/integration_sync.py`) and manual CLI:
  - `rc-db integrations sync --install-missing|--all|--dry-run`
  - first-run auto-sync after framework version change (opt-out: `REALITYCHECK_AUTO_SYNC=0`)

### Changed

- Validator hardening after review:
  - normalize factual type parsing (`F`, `[f]`, markdown-wrapped variants)
  - treat unknown/blank reviewed crux status values as unresolved (fail closed)
  - tolerate simple markdown wrappers around claim IDs
  - restrict `[REVIEWED]` detection to metadata rigor-level field
- Formatter/validator markdown table parsing hardening:
  - tolerate simple markdown wrappers in table headers/cells (e.g. `**Claim ID**`, ``Type``)
  - handle escaped pipes (`\\|`) in markdown tables without breaking column alignment
  - reduce false negatives and prevent duplicate table insertion in formatter
- Analysis log timestamps now use timezone-aware UTC (removes `datetime.utcnow()` deprecation warnings).
- Packaging now includes integration assets in wheel installs via hatch `force-include` (`integrations/**`, `methodology/workflows/check-core.md`, `README.md`) so pip/uv users can sync integrations without a source checkout.

### Tested

- `uv run pytest tests/test_analysis_formatter.py tests/test_analysis_validator.py -q` → `110 passed`
- `uv run pytest tests/test_db.py::TestBackupCLI -q` → `1 passed`
- `uv run pytest -q` → `454 passed`

## 0.3.1 - 2026-02-11

**Claim ID Ticketing & Reservation Cleanup** - Reduces agent cognitive load and collision risk during concurrent claim registration.

### Added

- `rc-db claim ticket --domain DOMAIN [--count N]` to reserve monotonic claim IDs without immediate insertion
- `rc-db claim ticket release` subcommand for reservation cleanup:
  - `--id CLAIM-ID` (repeatable) for explicit release
  - `--abandoned --older-than-days N` for stale reservation cleanup
  - `--all`, `--domain`, and `--dry-run` selectors
- Reservation file lock + persistent reservation store to prevent reissuing ticketed IDs across sessions

### Changed

- `rc-db claim add` auto-ID path now uses the same reservation allocator as `claim ticket`
- Reservation records are auto-cleared when matching claims are created
- Check skills/templates updated to document ticket-first claim ID workflow and stale reservation cleanup command

### Tested

- Added CLI tests for ticket reserve/release behavior (sequential reservations, explicit release, abandoned release, invalid count)
- Full non-embedding test suite passes (`395 passed, 17 skipped`)

## 0.3.0 - 2026-02-01

**Analysis Rigor & Inbox Workflow** - Enforces structured claim metadata and streamlines source processing.

This release introduces "rigor-v1" analysis tables with Layer/Actor/Scope/Quantifier columns, a new `--rigor` validation flag, and a complete inbox-to-reference filing workflow.

### Added

#### Analysis Rigor (v1)

- **Key Claims table** now includes Layer/Actor/Scope/Quantifier columns with column guide
- **Claim Summary table** updated with matching rigor columns
- **Corrections & Updates section** added to full-profile analyses for tracking source changes
- **`--rigor` flag** for `rc-validate` and `analysis_validator.py`:
  - WARN by default when rigor-v1 columns are missing
  - ERROR with `--rigor` flag for strict enforcement
- **Layer enum validation**: ASSERTED/LAWFUL/PRACTICED/EFFECT (N/A when genuinely inapplicable)

#### Evidence Links (rigor-v1 fields)

- `evidence_type`: LAW/REG/COURT_ORDER/FILING/MEMO/POLICY/REPORTING/VIDEO/DATA/STUDY/TESTIMONY/OTHER:\<text\>
- `claim_match`: How directly evidence supports the claim phrasing
- `court_posture`: stay/merits/preliminary_injunction/appeal/emergency/OTHER:\<text\>
- `court_voice`: majority/concurrence/dissent/per_curiam
- CLI: `rc-db evidence add --evidence-type LAW --court-posture merits --court-voice majority`

#### Reasoning Trails

- New statuses: `proposed` and `retracted` (in addition to active/superseded)
- CLI: `rc-db reasoning add --status proposed` for review workflows
- Validation enforces valid status values

#### Sources

- `last_checked` field for tracking when sources were last verified for changes
- CLI: `rc-db source update <id> --last-checked 2026-02-01`

#### Inbox Workflow

- **Filing guidance** in `/check` skill (Step 13: File Inbox)
- **Reference folder structure**:
  - `reference/primary/` - Primary documents renamed to source-id
  - `reference/captured/` - Supporting materials with original filenames
- **Generated .gitignore** includes rules for captured copyrighted content
- **WORKFLOWS.md** documents complete inbox processing flow

#### Project Structure

- `rc-db init-project` now creates `reference/primary/` and `reference/captured/`
- Simplified `inbox/` (single folder instead of subfolders)

### Changed

- `supersede_evidence_link()` now inherits rigor-v1 fields from old link
- Analysis formatter inserts Corrections & Updates section for full profile
- Skill templates updated with 16-step workflow (added File Inbox step)

### Fixed

- Layer validation allows N/A when genuinely inapplicable (documented)
- SCHEMA.md validation rules section updated for new statuses
- `validate.py` now enforces `REASONING_STATUS_INVALID` check

### Documentation

- `docs/WORKFLOWS.md`: New "Inbox Workflow" section with filing destinations
- `docs/WORKFLOWS.md`: Updated "Analysis Rigor Contract (v1)" with N/A guidance
- `docs/SCHEMA.md`: Documented all new fields and status options
- `docs/TODO.md`: Analysis Rigor Improvements marked as ✅ Implemented

## 0.2.0 - 2026-01-31

**Epistemic Provenance** - A major feature release adding structured audit trails for claim credence assignments.

This release introduces two new database tables (`evidence_links` and `reasoning_trails`) that capture *why* claims are assigned particular credence values, enabling rigorous review, agent disagreement tracking, and full epistemic audit trails.

### Added

#### Evidence Links (`rc-db evidence`)
- Link claims to supporting/contradicting sources with explicit directionality
- Track evidence strength, location (e.g., "Table 3, p.15"), quotes, and reasoning
- Versioning support via `status` (active/superseded/retracted) and `supersedes_id`
- CLI commands: `evidence add`, `evidence get`, `evidence list`, `evidence supersede`

#### Reasoning Trails (`rc-db reasoning`)
- Document the full reasoning chain for credence assignments
- Capture credence/evidence-level at time of assessment
- Track supporting and contradicting evidence link references
- Structured counterarguments with dispositions (integrated/discounted/unresolved)
- Publishable `reasoning_text` field for human-readable rationales
- CLI commands: `reasoning add`, `reasoning get`, `reasoning list`, `reasoning history`

#### Validation
- High-credence claims (≥0.7) or strong evidence (E1/E2) now require:
  - At least one supporting evidence link (`HIGH_CREDENCE_NO_BACKING`)
  - At least one active reasoning trail (`HIGH_CREDENCE_NO_REASONING_TRAIL`)
- Staleness warnings when claim credence differs from latest reasoning trail
- Evidence link validation (claim/source refs, direction/status enums)
- Reasoning trail validation (evidence link refs, counterarguments schema)
- Use `--strict` to escalate warnings to errors

#### Export
- `rc-export md reasoning --id CLAIM-ID` - Per-claim reasoning docs with evidence tables
- `rc-export md reasoning --all --output-dir DIR` - Bulk export all claims with trails
- `rc-export md evidence-by-claim --id CLAIM-ID` - Evidence index for a claim
- `rc-export md evidence-by-source --id SOURCE-ID` - Evidence index for a source
- `rc-export provenance --format yaml|json` - Deterministic bulk provenance export

#### Documentation
- `docs/SCHEMA.md` updated with `evidence_links` and `reasoning_trails` tables
- `docs/WORKFLOWS.md` updated with Evidence Linking, Reasoning Trails, and Export Provenance sections
- `methodology/reasoning-trails.md` - Full provenance methodology and design philosophy

#### Migration
- `rc-db migrate` creates new tables automatically for existing databases
- `rc-db init-project` creates provenance directories (`analysis/reasoning/`, `analysis/evidence/`)

#### Integration Templates
- `/check` workflow updated with Step 9: Provenance for high-credence claims
- `partials/provenance-workflow.md.j2` - Reusable evidence linking section
- All integration skills regenerated (Claude, Codex, Amp, OpenCode)

### Changed

- `list_reasoning_trails()` now returns results sorted by `created_at` descending
- `get_reasoning_trail(claim_id=...)` returns the latest active trail (deterministic)
- Counterarguments field standardized on `text` (legacy `argument` still accepted)

### Fixed

- Validator/formatter now support markdown-linked claim IDs (`[ID](path)`)
- `--output-dir` added as alias for `-o/--output` in export CLI

## 0.1.9 - 2026-01-28

Added OpenCode integration with full skill support.

### Added

- OpenCode integration with 9 skills (check, search, validate, stats, analyze, extract, register, export, synthesize)
- OpenCode README and installation via `make install-skills-opencode`
- OpenCode section in main README

### Fixed

- README stats now include INST and RISK domain codes

## 0.1.8 - 2026-01-26

Improved documentation for CLI availability and embedding troubleshooting.

### Added

- CLI Commands section in prerequisites explaining `rc-db` availability and fallbacks
- Command Availability section in db-commands with pip vs uv invocation options
- Embedding Management section with `rc-embed status/generate/regenerate` commands
- Embedding troubleshooting notes in search skill template
- Prerequisites section in Codex README with installation and embedding commands

### Fixed

- Backfilled 8 claims missing embeddings (GOV-2026-043 through GOV-2026-051)

## 0.1.7 - 2026-01-26

Fixed package imports that broke pip-installed distributions.

### Fixed

- Package imports now work correctly when installed via pip (not just from source).
- Replaced fragile `sys.path.insert()` workarounds with proper `if __package__:` conditional imports in embed.py, export.py, migrate.py, and validate.py.
- Consolidated inline `usage_capture` imports in db.py that caused `ModuleNotFoundError`.

### Added

- `tests/test_installation.py`: 22 new tests verifying package imports, cross-module imports, CLI entry points, and package structure to catch installation issues before release.

## 0.1.6 - 2026-01-26

Re-release of 0.1.5 with corrected README (PyPI is immutable).

## 0.1.5 - 2026-01-26

Token usage delta accounting and schema migration tooling.

### Added

- Token usage delta accounting system with lifecycle commands (`analysis start`, `analysis mark`, `analysis complete`).
- `rc-db migrate` command for schema updates on existing databases.
- Session auto-detection for Claude Code, Codex, and Amp agent logs.
- `analysis sessions list` command for session discovery/debugging.
- `analysis backfill-usage` command for best-effort historical token capture.

### Fixed

- `analysis start` session auto-detection tuple unpacking.
- `analysis mark` now captures `tokens_cumulative` and `tokens_delta` in stage entries.
- Validation level consistency (`WARN` instead of `WARNING`).
- Export fallback for `tokens_check=0` (explicit None check prevents incorrect fallback).
- Codex backfill now warns about cumulative counter limitation and uses `cumulative_snapshot` mode.

## 0.1.4 - 2026-01-25

Audit logs, synthesis workflows, and agent ergonomics improvements.

### Added

- Analysis audit log system (schema, CLI, validation, export) and token/cost usage capture.
- Cross-source synthesis support (`synthesize`) across integrations.
- Agent ergonomics improvements (commands + docs).
- Integrated `rc-html-extract` into analysis skills/templates and `check-core` workflow docs for structured HTML extraction.

### Changed

- Standardized terminology on `credence` (vs `confidence`).
- Hardened workflow tooling around commit/push/release hygiene.

### Fixed

- Restored `scripts.db` package imports and related packaging issues.
- Improved analysis log export/registration behavior.
- Prevented accidental DB init inside the framework repo.

## 0.1.3 - 2026-01-22

Analysis formatter/validator (Phase 10) plus a Jinja2-based skill template system.

### Added

- Jinja2-based skill template system and regenerated cross-tool skills (Codex/Amp/Claude).
- Analysis formatter and validator utilities to enforce the `check` output contract.
- Initial inbox + synthesis workflow planning docs.

### Changed

- Simplified skill structure and supporting `make` workflows.

### Fixed

- Ensured Codex skill frontmatter is always at the start of files.

## 0.1.2 - 2026-01-21

Documentation-only patch improving repo separation and “source of truth” guidance.

### Changed

- Clarified framework repo vs data repo responsibilities across check skills and docs.
- Documented LanceDB as the primary source of truth (YAML exports are derived artifacts).

## 0.1.1 - 2026-01-21

Integrations refactor + iterative analysis support + improved plugin discovery.

### Added

- `rc-html-extract` CLI utility for structured HTML extraction (`scripts/html_extract.py`).
- `--continue` flag for iterative / multi-pass analysis workflows.
- PyPI release checklist documentation (`docs/PYPI.md`).

### Changed

- Moved Claude plugin + skills into `integrations/claude/` and improved hook/skill sync guidance.

### Fixed

- Fixed plugin command discovery (YAML frontmatter placement, `plugin.json` command list).
- Ignored analysis outputs in the framework repo to prevent accidental commits.

## 0.1.0 - 2026-01-21

Initial PyPI release: core CLI + plugin + skills for end-to-end analysis workflows.

### Added

- Codex skills integration (plus data-persistence automation hooks).
- Auto-update README stats hook and example knowledge base link (`realitycheck-data`).
- Quick Reference section (claim types + evidence hierarchy) added to templates.

### Changed

- Standardized on `REALITYCHECK_DATA` for DB path configuration.
- Adopted Apache 2.0 licensing for the framework repo.
- Stabilized embeddings on systems with flaky GPU drivers by defaulting to CPU.

### Fixed

- Prevented duplicate claim IDs and added a delete command to the CLI.
- Improved CLI output formatting for credence and related-claim output.

## 0.1.0-beta - 2026-01-21

Pre-release git tag: extended CLI + plugin wiring + lifecycle hooks.

### Added

- Phase 2: extended `rc-db` CLI (CRUD + workflows) and plugin command wiring/hooks.

### Fixed

- Addressed Phase 2 review feedback (embedding/test guards, schema drift, workflow docs).

## 0.1.0-alpha - 2026-01-20

Pre-release git tag: initial framework port with CLI, plugin commands, methodology, and tests.

### Added

- Core scripts and CLI entrypoints (`rc-db`, `rc-validate`, `rc-export`, `rc-migrate`, `rc-embed`).
- Claude Code plugin commands (`/analyze`, `/extract`, `/search`, `/validate`, `/export`).
- Methodology templates, evidence hierarchy, and claim taxonomy docs.
- Full pytest suite for the core framework.
