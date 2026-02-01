from __future__ import annotations

from scripts import release_metadata


def test_find_changelog_release_date() -> None:
    changelog = """# Changelog

## Unreleased

## 0.3.0 - 2026-02-01

## 0.2.0 - 2026-01-31
"""
    assert release_metadata.find_changelog_release_date(changelog, "0.3.0") == "2026-02-01"
    assert release_metadata.find_changelog_release_date(changelog, "0.2.0") == "2026-01-31"
    assert release_metadata.find_changelog_release_date(changelog, "9.9.9") is None


def test_update_readme_content_updates_status_tree_and_bibtex_marker_block() -> None:
    readme = """# Reality Check

## Status

**v0.1.0** - Example summary; 10 tests.

## Project Structure

```
realitycheck/
├── tests/                    # pytest suite (10 tests)
```

## Citation

If you use Reality Check in academic work, please cite:

<!-- BEGIN REALITYCHECK_BIBTEX -->
```bibtex
@misc{oldkey,
  title = {Old}
}
```
<!-- END REALITYCHECK_BIBTEX -->
"""
    bibtex = release_metadata.render_bibtex(
        author_name="Leonard Lin",
        title="Reality Check",
        year=2026,
        version="0.3.0",
        url="https://github.com/lhl/realitycheck",
        accessed="2026-02-01",
    )
    updated = release_metadata.update_readme_content(
        readme_text=readme,
        version="0.3.0",
        test_count=401,
        bibtex=bibtex,
    )

    assert "**v0.3.0** - Example summary; 401 tests." in updated
    assert "# pytest suite (401 tests)" in updated
    assert "@misc{lin2026realitycheck" in updated
    assert "version = {0.3.0}" in updated


def test_render_citation_cff_includes_version_and_release_date() -> None:
    cff = release_metadata.render_citation_cff(
        title="Reality Check",
        version="0.3.0",
        date_released="2026-02-01",
        author_name="Leonard Lin",
        author_email="lhl@lhl.org",
        license_id="Apache-2.0",
        repo_url="https://github.com/lhl/realitycheck",
    )
    assert 'cff-version: 1.2.0' in cff
    assert 'title: "Reality Check"' in cff
    assert 'version: "0.3.0"' in cff
    assert "date-released: 2026-02-01" in cff
    assert 'repository-code: "https://github.com/lhl/realitycheck"' in cff
    assert 'license: "Apache-2.0"' in cff

