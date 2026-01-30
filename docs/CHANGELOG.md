# Changelog

All notable changes to `realitycheck` are documented here.

This project follows [Semantic Versioning](https://semver.org/) and the structure is inspired by [Keep a Changelog](https://keepachangelog.com/).

## Unreleased

- (Add changes here; move them into a versioned section when releasing.)

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
