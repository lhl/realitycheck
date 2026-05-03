# Deployment / Release

Quick overview:

1. Update release notes + version:
   - `pyproject.toml` - Bump version number
   - `make release-metadata` - Sync README version/test count + CITATION.cff
   - `make assemble-skills` - Sync plugin.json version + regenerate skill files
   - `docs/CHANGELOG.md` - Add version section with changes
   - `README.md` - Update Status summary (version + test count are auto-synced)
   - `REALITYCHECK_EMBED_SKIP=1 uv run pytest -q` - Verify tests pass
2. Commit and push:
   - `git add ... && git commit -m "release: vX.Y.Z - summary"`
   - `git push origin main`
3. Tag and push:
   - `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
4. Build and upload:
   - `rm -rf dist/ && uv build && uv publish dist/realitycheck-X.Y.Z*`
5. Post-publish:
   - `uvx --refresh --from "realitycheck==X.Y.Z" rc-db --help`
   - `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <path> --latest`

For the full checklist: `docs/PUBLISH.md`
