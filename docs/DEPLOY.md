# Deployment / Release

Quick overview:

1. Update release notes + version:
   - `docs/CHANGELOG.md` - Add version section with changes
   - `pyproject.toml` - Bump version number
   - `README.md` - Update Status summary (version + test count are auto-synced)
   - `make release-metadata` - Sync README version/test count + BibTeX + `CITATION.cff`
   - `make assemble-skills` - Sync plugin.json version + regenerate skill files
   - `REALITYCHECK_EMBED_SKIP=1 uv run pytest -q` - Verify tests pass (count should match README)
2. Commit and push:
   - `git add docs/CHANGELOG.md pyproject.toml README.md && git commit -m "release: vX.Y.Z - summary"`
   - `git push origin main`
3. Tag and push:
   - `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
4. Build and upload:
   - `rm -rf dist/ && uv build && uv tool run twine check dist/* && uv tool run twine upload --non-interactive dist/*`

For a full checklist, follow:

- Release notes: `docs/CHANGELOG.md`
- PyPI publish checklist: `docs/PYPI.md`
