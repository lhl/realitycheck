---
allowed-tools:
  - "Read"
  - "Write"
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh *)"
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-export.sh *)"
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh *)"
description: Create a cross-source synthesis across multiple source analyses and claims
---

# /reality:synthesize - Cross-Source Synthesis

Create a **cross-source synthesis** across multiple source analyses and existing claims.

Use this after running `/reality:check` on multiple sources (or when relevant source analyses already exist and you want a higher-level conclusion).

## Usage

```
/reality:synthesize <topic>
```

## Output

Write a synthesis document to:
`analysis/syntheses/<synth-id>.md`

The synthesis should link back to relevant source analyses in:
`analysis/sources/<source-id>.md`

## Workflow

1. **Define the question**
   - What is this synthesis trying to answer?
2. **Collect inputs**
   - Prefer existing source analyses in `analysis/sources/`
   - If a relevant source has no analysis yet, run `/reality:check` first (or explicitly record the gap)
3. **Write the synthesis**
   - Points of agreement (which claims converge?)
   - Points of disagreement (where do they conflict, and why?)
   - Conclusions with calibrated credence + key uncertainties
   - Link claim IDs and source analysis files wherever possible
4. **(Optional) Register an argument chain**
   - If the synthesis centers on a specific argument chain, register it and point `--analysis-file` at the synthesis document:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-db.sh" chain add \
  --id "CHAIN-YYYY-NNN" \
  --name "..." \
  --thesis "..." \
  --claims "TECH-2026-001,ECON-2026-002" \
  --analysis-file "analysis/syntheses/<synth-id>.md"
```

5. **Validate**

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh"
```

6. **Update README**
   - Add a row to the "Syntheses" table (kept above "Source Analyses") in your data repo `README.md`.
7. **Commit and push**
   - If you ran a DB write command (e.g., `chain add`), the plugin hook may auto-commit.
   - Otherwise, commit your `analysis/` + `README.md` changes manually.

## Template

Uses `methodology/templates/synthesis.md`

## Related Commands

- `/reality:check` - Create source analyses first
- `/reality:search` - Find related claims and sources
- `/reality:validate` - Validate database integrity
