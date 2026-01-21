---
name: check
description: "Reality Check check workflow for Codex (fetch, analyze, extract, register, validate)."
---

# Reality Check `$check` (Codex)

This skill mirrors the Claude Code `/check` workflow, but for Codex CLI.

## Invocation

- `$check <url> [--domain DOMAIN] [--quick] [--no-register]`
- `$check <source-id> --continue` - Continue an existing analysis
- `$check --continue` - Continue the most recent analysis

Note: Codex CLI reserves `/...` for built-in commands. Use `$check ...` (or plain text asking for a check) instead of `/check ...`.

## Preconditions

- Assume the `realitycheck` Python package is installed (so `rc-db` and `rc-validate` are on `PATH`).
- Assume `REALITYCHECK_DATA` is set.

If `REALITYCHECK_DATA` is not set, ask the user to either:
- Export it in their shell, or
- Use `$realitycheck data <path>` (see the `realitycheck` Codex skill) to set it for the current Codex session.

## Continuation Mode

When `--continue` is specified (or when the user asks to continue an existing analysis):

1. **Find existing analysis**: Look for `analysis/sources/[source-id].md`
2. **Read current state**: Load the existing analysis and registered claims
3. **Iterate, don't overwrite**: Add to the existing analysis rather than replacing it
4. **Focus areas**:
   - Extract claims that were skipped or noted as "TODO"
   - Deepen specific sections (more counterfactuals, stronger steelman)
   - Address questions or gaps identified in the original pass
   - Cross-reference with newly added claims in the database

**Important**: Preserve all existing content. Append new sections and note what was added in this pass.

## Execution Outline

1. **Preflight**
   - Confirm `rc-db` and `rc-validate` are available.
   - Confirm `REALITYCHECK_DATA` is set (or prompt to set it).
2. **Fetch the source**
   - Prefer `curl -L <url>` and save the raw content to a temporary file.
   - If the URL is a PDF, download it and extract text (e.g., via `pdftotext` if available).
3. **Three-stage analysis**
   - Stage 1: descriptive (summary, key claims, predictions, assumptions, terms)
   - Stage 2: evaluative (coherence, evidence quality, disconfirmation, rhetoric)
   - Stage 3: dialectical (steelman, counterarguments, synthesis) unless `--quick`
4. **Extract claims**
   - Produce a YAML block of claims (type/domain/evidence_level/credence/operationalization).
5. **Register (optional)**
   - If not `--no-register`: add the source + claims via `rc-db`, then run `rc-validate`.

## Commands (preferred)

Use installed entry points when available:

- `rc-db ...`
- `rc-validate ...`

If those aren’t on `PATH`, fall back to running from the framework repo:

- `uv run python scripts/db.py ...`
- `uv run python scripts/validate.py ...`
