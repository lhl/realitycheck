# Reality Check - Development Guide

Please refer to `README.md`, `docs/PLAN-separation.md`, `docs/IMPLEMENTATION.md`, and `docs/DEPLOY.md` for project-specific details.
This `AGENTS.md`/`CLAUDE.md` is specifically for ground rules, process, and behavior notes.

## Project Overview

Reality Check is a framework for rigorous, systematic analysis of claims, sources, predictions, and argument chains. It provides:
- LanceDB-backed storage with semantic search
- Structured methodology for claim extraction and evaluation
- Evidence hierarchy and prediction tracking
- Claude Code plugin for workflow automation

## Key Directories

```
realitycheck/
├── scripts/          # Core Python CLI tools (db.py, validate.py, export.py, migrate.py)
├── tests/            # pytest test suite
├── integrations/     # Tool-specific integrations
│   ├── claude/       # Claude Code plugin and skills
│   │   ├── plugin/   # Plugin (commands/, hooks/, scripts/)
│   │   └── skills/   # Global skills (alternative to plugin)
│   └── codex/        # OpenAI Codex skills
├── methodology/      # Analysis methodology docs (extracted from framework)
├── docs/             # Development docs (PLAN-*.md, IMPLEMENTATION.md)
└── examples/         # Minimal example data
```

## Development Philosophy: Spec → Plan → Test → Implement

**This project is strictly spec/plan/test-driven.** The goal is a high-quality, maintainable framework that's easy to update and extend. Every feature follows this cycle:

### The Cycle

1. **Spec**: Define requirements clearly in `docs/` before writing any code
2. **Plan**: Create implementation plan with affected files (tree diagram)
3. **Test**: Write unit tests AND e2e tests BEFORE implementation
4. **Implement**: Write minimal code to pass the tests
5. **Validate**: Run full test suite - all tests must pass
6. **Commit**: Atomic commits with passing tests only

### Why Tests First?

- **Clarifies requirements** - Writing tests forces you to think through edge cases
- **Prevents scope creep** - You only implement what the tests require
- **Enables refactoring** - Tests catch regressions when you improve code later
- **Documents behavior** - Tests are executable specifications
- **Catches bugs early** - Faster to fix issues before code is "done"

### Test Coverage Requirements

- **Unit tests**: Every public function in `scripts/*.py` must have tests
- **E2E tests**: Every user workflow must have integration tests
- **Edge cases**: Error paths, empty inputs, boundary conditions
- **No skipping**: If a test fails, fix it before proceeding

## Documentation as Source of Truth

- Treat `docs/` as the source of truth and always prioritize keeping them up to date
- `docs/PLAN-separation.md` - Architecture and implementation plan
- `docs/IMPLEMENTATION.md` - Progress tracking (punchlist + worklog)
- `docs/DEPLOY.md` - Release checklist (PyPI + GitHub)
- `docs/CHANGELOG.md` - Release notes
- When making changes: update docs, run tests, then commit

## Workflow Expectations

### Before Picking Up Work
- Check git status/log for recent changes
- Review open items in `docs/IMPLEMENTATION.md`
- Confirm your plan aligns with documented approach
- **Review existing tests** to understand expected behavior

### During Execution
- **Write tests first** for the feature/fix you're implementing
- Leave breadcrumbs in IMPLEMENTATION.md (commands run, decisions made)
- Run tests incrementally as you go
- Keep commits atomic and focused

### After Changes
- Update IMPLEMENTATION.md (check items, add notes)
- Run `uv run pytest` and `uv run python scripts/validate.py`
- **All tests must pass** before committing
- Commit with descriptive message

### Running Tests

```bash
# Run all tests
uv run pytest -v

# Skip embedding tests if torch issues
REALITYCHECK_EMBED_SKIP=1 uv run pytest -v

# Run with coverage
uv run pytest --cov=scripts --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_db.py

# Run specific test class
uv run pytest tests/test_db.py::TestClaimsCRUD
```

### Test Structure

```
tests/
├── conftest.py        # Shared fixtures (temp_db_path, sample_claim, etc.)
├── test_db.py         # Unit tests for db.py
├── test_migrate.py    # Unit tests for migrate.py
├── test_validate.py   # Unit tests for validate.py
├── test_export.py     # Unit tests for export.py
└── test_e2e.py        # End-to-end integration tests
```

### Pre-Commit Checklist

- [ ] Tests pass: `uv run pytest`
- [ ] Validation passes: `uv run python scripts/validate.py` (if data exists)
- [ ] No untracked files in commit
- [ ] Commit message is descriptive

## Git Practices

- **Commit frequently** with descriptive messages
- **No bylines** or co-author footers in commits
- **Use conventional commits**: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- **Add files explicitly** - never use `git add .` or `git add -A`
- **Atomic commits** - group related changes, separate unrelated ones
- **Run validation** before pushing

### Commit Message Format

```
type: short summary (imperative mood)

- Bullet points for details if needed
- What changed and why
```

Examples:
```
feat: add semantic search to db.py CLI
docs: update PLAN-separation.md with plugin distribution
fix: handle empty lists in PyArrow schema conversion
test: add claim relationship tests
```

## Code Quality

### Before Submitting Code
- [ ] Self-review: is this understandable without explanation?
- [ ] Modular: can each function be understood in isolation?
- [ ] Tested: are success and error paths covered?
- [ ] Documented: do complex parts have comments?

### Common Patterns

**Environment variable for DB path:**
```python
DB_PATH = Path(os.environ.get("REALITYCHECK_DATA", "data/realitycheck.lance"))
```

**CLI subcommands in db.py:**
```python
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")
subparsers.add_parser("init", help="Initialize database")
# ... etc
```

**Test fixtures:**
```python
@pytest.fixture
def sample_claim():
    return {
        "id": "TEST-2026-001",
        "text": "Test claim",
        "type": "[T]",
        "domain": "TEST",
        # ...
    }
```

## Plugin Development

The Claude Code plugin lives in `integrations/claude/plugin/` and provides slash commands that inject methodology + call scripts.

### Plugin Structure
```
integrations/claude/plugin/
├── .claude-plugin/plugin.json    # Metadata
├── commands/*.md                  # Slash command definitions
├── hooks/hooks.json               # Lifecycle hooks
├── scripts/*.sh                   # Shell wrappers for Python scripts
└── lib/                           # Bundled Python scripts (for distribution)
```

### Testing Commands
Use the `--plugin-dir` flag (local plugin discovery is currently broken):
```bash
claude --plugin-dir /path/to/realitycheck/integrations/claude/plugin
```

### Keeping Hooks and Skills in Sync

The Claude plugin includes lifecycle hooks that automate tasks like auto-commit after database operations. Codex (and other integrations) don't support hooks, so skills must document equivalent manual steps.

**Source of truth:** `integrations/claude/plugin/hooks/` scripts define the canonical behavior.

When modifying hook behavior:
1. Update the hook script (e.g., `auto-commit-data.sh`)
2. Update corresponding skill docs to describe the manual equivalent
3. Update `docs/WORKFLOWS.md` to note any cross-tool differences

Key sync points:
- **Auto-commit:** `hooks/post-db-modify.sh` → Codex skill "Data Repo Version Control" section
- **README stats:** `scripts/update-readme-stats.sh` → Codex skill optional step (also used by plugin hooks)

## Handling Blockers

If you encounter:
- **Permission issues**: Stop and flag for resolution
- **Test failures**: Fix before proceeding (don't skip)
- **Unclear requirements**: Check docs first, then ask
- **Merge conflicts**: Resolve carefully, test after

## Meta: Evolving This File

This AGENTS.md is a living document. Update it when:
- You discover a workflow pattern that helps
- Something caused confusion
- A new tool or process gets introduced
- You learn something that would help the next person

Keep changes focused on process/behavior, not project-specific details (those go in docs/).
