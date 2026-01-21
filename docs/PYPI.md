# PyPI Release Process

This document describes how to release new versions of `realitycheck` to PyPI.

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
# Ensure clean working tree
git status

# Run tests
REALITYCHECK_EMBED_SKIP=1 uv run pytest -v

# Check current version
grep "version" pyproject.toml
```

### 2. Update Version

Edit `pyproject.toml`:
```toml
version = "X.Y.Z"
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (X): Breaking changes
- **MINOR** (Y): New features, backward compatible
- **PATCH** (Z): Bug fixes, documentation

### 3. Commit Version Bump

```bash
git add pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
git push
```

### 4. Build Package

```bash
# Clean previous builds
rm -rf dist/

# Build wheel and sdist
uv build

# Verify contents
ls -la dist/
```

### 5. Upload to PyPI

```bash
# Upload using twine (reads ~/.pypirc)
uv tool run twine upload dist/*

# Or specify token directly:
uv tool run twine upload dist/* -u __token__ -p pypi-YOUR-TOKEN
```

### 6. Verify Installation

```bash
# Test in fresh environment
uv venv /tmp/test-install && source /tmp/test-install/bin/activate
pip install realitycheck==X.Y.Z
rc-db --help
deactivate && rm -rf /tmp/test-install
```

### 7. Tag Release

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

### 8. Create GitHub Release (Optional)

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --notes "Release notes here"
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
