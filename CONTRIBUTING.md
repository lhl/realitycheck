# Contributing to Reality Check

Guidelines for contributing to the Reality Check framework.

## Development Philosophy

This project follows **Spec → Plan → Test → Implement**:

1. **Spec**: Define requirements in `docs/` before writing code
2. **Plan**: Create implementation plan with affected files
3. **Test**: Write tests BEFORE implementation
4. **Implement**: Write minimal code to pass tests
5. **Validate**: Run full test suite
6. **Commit**: Atomic commits with passing tests only

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone repository
git clone https://github.com/lhl/realitycheck.git
cd realitycheck

# Install dependencies
uv sync

# Run tests
uv run pytest -v

# Initialize database
uv run python scripts/db.py init
```

## Code Style

### Python

- Follow PEP 8
- Use type hints for function signatures
- Docstrings for public functions
- Keep functions focused and small

### Commit Messages

Use conventional commits:

```
type: short summary (imperative mood)

- Details if needed
- What changed and why
```

Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring

### Git Practices

- **NEVER** use `git add .` or `git add -A`
- **ALWAYS** explicitly add specific files
- Keep commits atomic and focused
- Run tests before committing

## Testing

### Running Tests

```bash
# All tests
uv run pytest -v

# Skip embedding tests (faster)
REALITYCHECK_EMBED_SKIP=1 uv run pytest -v

# With coverage
uv run pytest --cov=scripts --cov-report=term-missing

# Specific file
uv run pytest tests/test_db.py

# Specific test
uv run pytest tests/test_db.py::TestClaimsCRUD::test_add_claim
```

### Writing Tests

- Test files: `tests/test_*.py`
- Use fixtures from `tests/conftest.py`
- Test both success and error paths
- Cover edge cases

Example:

```python
def test_add_claim(self, initialized_db, sample_claim):
    """Test adding a claim to database."""
    from scripts.db import add_claim, get_claim

    add_claim(initialized_db, sample_claim)
    result = get_claim(initialized_db, sample_claim["id"])

    assert result is not None
    assert result["text"] == sample_claim["text"]
```

### Test Coverage Requirements

- Every public function must have tests
- E2E tests for user workflows
- Error paths and edge cases
- No skipping failing tests

## Documentation

### Updating Docs

When making changes:

1. Update relevant docs in `docs/`
2. Update README.md if user-facing
3. Update CLAUDE.md if methodology changes
4. Add docstrings to new functions

### Doc Locations

- `README.md` - Overview and quick start
- `docs/SCHEMA.md` - Database schema
- `docs/WORKFLOWS.md` - Usage workflows
- `docs/PLUGIN.md` - Claude Code plugin
- `docs/PLAN-*.md` - Implementation plans
- `docs/IMPLEMENTATION.md` - Progress tracking
- `methodology/` - Analysis methodology

## Pull Request Process

1. **Fork** the repository
2. **Branch** from `main`: `git checkout -b feat/my-feature`
3. **Implement** following Spec → Plan → Test → Implement
4. **Test**: All tests must pass
5. **Document**: Update relevant docs
6. **Commit**: Atomic commits with clear messages
7. **Push**: `git push origin feat/my-feature`
8. **PR**: Open pull request with description

### PR Checklist

- [ ] Tests pass: `uv run pytest`
- [ ] Validation passes: `uv run python scripts/validate.py`
- [ ] Documentation updated
- [ ] Commits are atomic and well-described
- [ ] No unrelated changes included

## Project Structure

```
realitycheck/
├── scripts/           # Python CLI tools
│   ├── db.py          # Database operations
│   ├── validate.py    # Data validation
│   ├── export.py      # Export utilities
│   ├── migrate.py     # Migration tools
│   └── embed.py       # Embedding generation
├── tests/             # pytest test suite
│   ├── conftest.py    # Shared fixtures
│   └── test_*.py      # Test files
├── integrations/      # Tool integrations
│   ├── _templates/    # Jinja2 templates (SOURCE OF TRUTH)
│   ├── _config/       # Skill definitions
│   ├── assemble.py    # Skill generator
│   ├── amp/skills/    # Generated Amp skills
│   ├── claude/        # Claude plugin + skills
│   └── codex/skills/  # Generated Codex skills
├── methodology/       # Analysis methodology
│   ├── evidence-hierarchy.md
│   ├── claim-taxonomy.md
│   └── templates/
├── docs/              # Documentation
└── examples/          # Example data
```

## Skill Development

Skills are **generated from Jinja2 templates** - do not edit `SKILL.md` files directly.

### Modifying Skills

1. Edit templates in `integrations/_templates/`
2. Regenerate: `make assemble-skills`
3. Commit both templates and generated files

### Template Locations

| What to Edit | Location |
|--------------|----------|
| Evidence hierarchy, claim types | `_templates/partials/` |
| Analysis tables (Key Claims, etc.) | `_templates/tables/` |
| Analysis sections | `_templates/sections/` |
| Skill-specific content | `_templates/skills/` |
| Integration wrappers | `_templates/wrappers/` |
| Skill definitions | `_config/skills.yaml` |

### Adding a New Skill

1. Create `_templates/skills/newskill.md.j2`
2. Add entry to `_config/skills.yaml` with per-integration metadata
3. Run `make assemble-skills`
4. Update install scripts if needed

### Checking Skills

```bash
# Regenerate all skills
make assemble-skills

# Check if generated files are up-to-date (CI)
make check-skills
```

## Reporting Issues

### Bug Reports

Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version)
- Error messages/logs

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative approaches considered

## Questions?

- Check existing documentation
- Search closed issues
- Open a discussion

## License

Apache 2.0 License - see LICENSE file.
