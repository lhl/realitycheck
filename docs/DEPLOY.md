# Deployment / Release

Quick overview:

1. Update release notes + version:
   - `docs/CHANGELOG.md`
   - `pyproject.toml`
2. Tag and push:
   - `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
3. Build and upload:
   - `rm -rf dist/ && uv build && uv tool run twine upload --non-interactive dist/*`

For a full checklist, follow:

- Release notes: `docs/CHANGELOG.md`
- PyPI publish checklist: `docs/PYPI.md`
