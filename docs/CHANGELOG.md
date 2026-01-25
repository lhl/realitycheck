# Changelog

All notable changes to `realitycheck` are documented here.

This project follows [Semantic Versioning](https://semver.org/) and the structure is inspired by [Keep a Changelog](https://keepachangelog.com/).

## Unreleased

- (Add changes here; move them into a versioned section when releasing.)

## 0.1.4 - 2026-01-25

Audit logs, synthesis workflows, and agent ergonomics improvements.

### Added

- Analysis audit log system (schema, CLI, validation, export) and token/cost usage capture.
- Cross-source synthesis support (`synthesize`) across integrations.
- Agent ergonomics improvements (commands + docs).
- Added `rc-html-extract` to analysis skills for structured HTML extraction workflows.

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

- `rc-html-extract` utility for structured HTML extraction.
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
