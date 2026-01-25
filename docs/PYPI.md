# PyPI Release Process

This document describes how to release new versions of `realitycheck` to PyPI.

Release notes source of truth: `docs/CHANGELOG.md`.

## Prerequisites

- PyPI account with upload permissions for `realitycheck`
- `~/.pypirc` configured with API token:
  ```ini
  [pypi]
  username = __token__
  password = pypi-YOUR-API-TOKEN
  ```
- `uv` and `twine` available

## Release Checklist

### 1. Pre-release Checks

```bash
# Ensure you're up to date
git fetch origin
git status -sb

# Ensure clean working tree
git status

# Run tests
REALITYCHECK_EMBED_SKIP=1 uv run pytest -v

# Check current version
grep "version" pyproject.toml
```

Optional (recommended): run `uv run python scripts/validate.py` in a representative data project (i.e., where `REALITYCHECK_DATA` points at a real DB).

### 2. Update Release Notes

- Add an entry for `X.Y.Z` in `docs/CHANGELOG.md` (date + highlights).
- Move relevant items out of `Unreleased` into the new section.

### 3. Update Version

Edit `pyproject.toml`:
```toml
version = "X.Y.Z"
```

Also update any hard-coded references to the old version (README status line, docs examples, etc.).

Verify version consistency:
```bash
grep "## X.Y.Z" docs/CHANGELOG.md
grep "version = \"X.Y.Z\"" pyproject.toml
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (X): Breaking changes
- **MINOR** (Y): New features, backward compatible
- **PATCH** (Z): Bug fixes, documentation

### 4. Commit Release

```bash
git add pyproject.toml docs/CHANGELOG.md
git commit -m "chore: bump version to X.Y.Z"
git push
```

### 5. Tag Release

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

### 6. Build Package

```bash
# Clean previous builds
rm -rf dist/

# Build wheel and sdist
uv build

# Verify contents
ls -la dist/

# Verify package metadata
uv tool run twine check dist/*
```

### 7. Upload to PyPI

```bash
# Upload using twine (reads ~/.pypirc)
uv tool run twine upload --non-interactive dist/*

# Or specify token directly:
uv tool run twine upload dist/* -u __token__ -p pypi-YOUR-TOKEN
```

### 8. Verify Installation

```bash
# Test in fresh environment
uv venv /tmp/test-install && source /tmp/test-install/bin/activate
pip install realitycheck==X.Y.Z
rc-db --help
deactivate && rm -rf /tmp/test-install
```

Alternative (faster, if you have `uvx`):
```bash
uvx --from realitycheck==X.Y.Z rc-db --help
```

### 9. Create GitHub Release (Optional)

Use the `X.Y.Z` section from `docs/CHANGELOG.md` as your GitHub release notes.

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --notes "See docs/CHANGELOG.md"
```

## Troubleshooting

### Token Issues

If upload fails with authentication error:
1. Generate new token at https://pypi.org/manage/account/token/
2. Update `~/.pypirc` with new token
3. Ensure token has upload scope for `realitycheck` project

### Version Conflict

If version already exists on PyPI:
- PyPI does not allow re-uploading the same version
- Bump to next patch version (e.g., 0.1.1 → 0.1.2)

### Build Issues

```bash
# Force clean rebuild
rm -rf dist/ build/ *.egg-info/
uv build
```

## Package URLs

- PyPI: https://pypi.org/project/realitycheck/
- GitHub: https://github.com/lhl/realitycheck
