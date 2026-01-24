---
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh *)"]
description: Check database integrity and referential consistency
---

# /reality:validate - Data Integrity Check

Check database integrity and referential consistency.

## Usage

```
/reality:validate [--strict] [--json]
```

## CLI Invocation

Run validation using the shell wrapper:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run-validate.sh" [OPTIONS]
```

Or directly via the Python script:

```bash
uv run python scripts/validate.py [OPTIONS]
```

## Options

- `--strict`: Treat warnings as errors
- `--json`: Output results as JSON
- `--mode {db,yaml}`: Validation mode (default: db)
- `--db-path PATH`: Database path (for db mode)
- `--repo-root PATH`: Repository root (for yaml mode)

## Checks Performed

### Schema Validation
- Claim ID format: `[DOMAIN]-[YYYY]-[NNN]`
- Chain ID format: `CHAIN-[YYYY]-[NNN]`
- Valid claim types: `[F]`/`[T]`/`[H]`/`[P]`/`[A]`/`[C]`/`[S]`/`[X]`
- Valid evidence levels: E1-E6
- Credence in range [0.0, 1.0]
- Valid domains

### Referential Integrity
- Claims reference existing sources
- Sources list extracted claims (backlinks)
- Chains reference existing claims
- Predictions reference existing claims

### Logical Consistency
- Domain in ID matches domain field
- Chain credence ≤ MIN(claim credences)
- All `[P]` claims have prediction records

### Data Quality
- No empty claim text
- Embeddings present (warning if missing)

## Output

```
OK: 0 error(s), 2 warning(s)
WARN [CLAIM_NO_EMBEDDING] TECH-2026-001: Missing embedding
WARN [CHAIN_CREDENCE_EXCEEDS_MIN] CHAIN-2026-001: Chain credence 0.8 > min claim credence 0.75
```

## Exit Codes

- `0`: All checks passed (warnings allowed)
- `1`: Errors found

## Examples

```
/reality:validate
/reality:validate --strict
/reality:validate --json
/reality:validate --mode yaml --repo-root /path/to/data-repo
```

## Related Commands

- `/reality:export` - Export data
- `/reality:stats` - Database statistics
- `/reality:check` - Full analysis workflow
