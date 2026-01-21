# Integrations

Reality Check supports tool-specific integrations (plugins, skills, wrappers) kept under `integrations/` when they are not part of the core Python package.

## Claude Code

The Claude Code plugin lives in `plugin/`.

- Install (symlink): `make install-plugin`
- Uninstall: `make uninstall-plugin`

## Codex

Codex skills live in `integrations/codex/`.

- Install: `make install-codex-skills`
- Uninstall: `make uninstall-codex-skills`
