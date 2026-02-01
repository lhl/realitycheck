#!/usr/bin/env python3
"""
Release metadata sync helper.

Keeps human- and machine-readable metadata in sync with the current version:

- README.md:
  - Status line version + pytest test count
  - Project tree pytest test count
  - BibTeX citation (version + accessed date)
- CITATION.cff:
  - version + date-released

Intended usage (repo root):
  uv run python scripts/release_metadata.py --write
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

try:
    import tomllib  # py>=3.11
except ImportError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


class ReleaseMetadataError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProjectMetadata:
    name: str
    title: str
    version: str
    license: str
    author_name: str
    author_email: str | None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def load_pyproject_metadata(pyproject_path: Path) -> ProjectMetadata:
    if tomllib is None:  # pragma: no cover
        raise ReleaseMetadataError("Python 3.11+ required (tomllib not available).")
    if not pyproject_path.exists():
        raise ReleaseMetadataError(f"pyproject.toml not found: {pyproject_path}")

    raw = pyproject_path.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    project = data.get("project") or {}

    version = project.get("version")
    if not version or not isinstance(version, str):
        raise ReleaseMetadataError("Missing [project].version in pyproject.toml")

    project_name = project.get("name")
    if not project_name or not isinstance(project_name, str):
        raise ReleaseMetadataError("Missing [project].name in pyproject.toml")

    license_text = None
    license_obj = project.get("license")
    if isinstance(license_obj, dict):
        license_text = license_obj.get("text")
    if not license_text or not isinstance(license_text, str):
        raise ReleaseMetadataError("Missing [project].license.text in pyproject.toml")

    authors = project.get("authors") or []
    if not authors or not isinstance(authors, list) or not isinstance(authors[0], dict):
        raise ReleaseMetadataError("Missing/invalid [project].authors in pyproject.toml")
    author_name = authors[0].get("name")
    if not author_name or not isinstance(author_name, str):
        raise ReleaseMetadataError("Missing [project].authors[0].name in pyproject.toml")
    author_email = authors[0].get("email")
    if author_email is not None and not isinstance(author_email, str):
        author_email = None

    # Human-facing title (best-effort). Prefer README heading naming over package name.
    title = "Reality Check"

    return ProjectMetadata(
        name=project_name,
        title=title,
        version=version,
        license=license_text,
        author_name=author_name,
        author_email=author_email,
    )


def find_changelog_release_date(changelog_text: str, version: str) -> str | None:
    m = re.search(rf"^##\s+{re.escape(version)}\s+-\s+(\d{{4}}-\d{{2}}-\d{{2}})\s*$", changelog_text, re.MULTILINE)
    if not m:
        return None
    return m.group(1)


def collect_pytest_item_count(repo_root: Path) -> int:
    env = os.environ.copy()
    env.setdefault("REALITYCHECK_EMBED_SKIP", "1")

    if (repo_root / "pyproject.toml").exists() and _which("uv") is not None:
        cmd = ["uv", "run", "pytest", "--collect-only", "-q"]
    else:
        cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]

    result = subprocess.run(
        cmd,
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    out = (result.stdout or "") + "\n" + (result.stderr or "")
    m = re.search(r"collected\s+(\d+)\s+items", out)
    if not m:
        raise ReleaseMetadataError(
            "Unable to determine pytest test count from output.\n"
            f"Command: {' '.join(cmd)}\n"
            f"Exit: {result.returncode}\n"
            f"Output:\n{out.strip()}\n"
        )
    return int(m.group(1))


def _which(cmd: str) -> str | None:
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(path_dir) / cmd
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _split_author_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if len(parts) == 1:
        return ("", parts[0])
    return (" ".join(parts[:-1]), parts[-1])


def render_bibtex(*, author_name: str, title: str, year: int, version: str, url: str, accessed: str) -> str:
    # Keep the key stable-ish across releases within the same year.
    family_guess = _split_author_name(author_name)[1].lower() or "author"
    key = f"{family_guess}{year}{re.sub(r'[^a-z0-9]+', '', title.lower())}"
    given, family = _split_author_name(author_name)
    bibtex_author = f"{family}, {given}" if given else family
    return (
        "@misc{"
        + key
        + ",\n"
        + f"  author  = {{{bibtex_author}}},\n"
        + f"  title   = {{{title}}},\n"
        + f"  year    = {{{year}}},\n"
        + f"  version = {{{version}}},\n"
        + f"  url     = {{{url}}},\n"
        + f"  note    = {{Accessed: {accessed}}}\n"
        + "}\n"
    )


def update_readme_content(
    *,
    readme_text: str,
    version: str,
    test_count: int,
    bibtex: str,
) -> str:
    # Status line: update version + test count; keep summary text unchanged.
    status_re = re.compile(
        r"^\*\*v(?P<version>\d+\.\d+\.\d+)\*\*\s+-\s+(?P<summary>.+?);\s+(?P<count>\d+)\s+tests\.\s*$",
        re.MULTILINE,
    )
    m = status_re.search(readme_text)
    if not m:
        raise ReleaseMetadataError("README.md Status line not found (expected '**vX.Y.Z** - ...; N tests.').")
    summary = m.group("summary")
    new_status_line = f"**v{version}** - {summary}; {test_count} tests."
    out = status_re.sub(new_status_line, readme_text, count=1)

    # Project tree line: update the pytest suite count.
    tree_re = re.compile(r"(# pytest suite \()(?P<count>\d+)( tests\))")
    out2, n_tree = tree_re.subn(rf"\g<1>{test_count}\g<3>", out)
    if n_tree == 0:
        raise ReleaseMetadataError("README.md pytest suite count not found (expected '# pytest suite (N tests)').")
    out = out2

    # BibTeX: prefer explicit markers for stability.
    begin = "<!-- BEGIN REALITYCHECK_BIBTEX -->"
    end = "<!-- END REALITYCHECK_BIBTEX -->"
    if begin in out and end in out:
        before, rest = out.split(begin, 1)
        middle, after = rest.split(end, 1)
        # Replace everything between markers (including existing code fences) with a fresh block.
        replacement = (
            begin
            + "\n```bibtex\n"
            + bibtex.rstrip("\n")
            + "\n```\n"
            + end
        )
        out = before + replacement + after
        return out

    # Fallback: replace the first bibtex fenced block under the Citation section.
    citation_block_re = re.compile(
        r"(## Citation[\s\S]*?```bibtex\n)([\s\S]*?)(\n```)",
        re.MULTILINE,
    )
    out2, n_bib = citation_block_re.subn(rf"\g<1>{bibtex.rstrip()}\g<3>", out, count=1)
    if n_bib == 0:
        raise ReleaseMetadataError(
            "README.md Citation BibTeX block not found.\n"
            "Add a fenced ```bibtex block under '## Citation' or add BEGIN/END markers."
        )
    return out2


def render_citation_cff(
    *,
    title: str,
    version: str,
    date_released: str,
    author_name: str,
    author_email: str | None,
    license_id: str,
    repo_url: str,
) -> str:
    given, family = _split_author_name(author_name)
    lines: list[str] = [
        "cff-version: 1.2.0",
        'message: "If you use this software, please cite it as below."',
        f'title: "{title}"',
        "type: software",
        f'version: "{version}"',
        f"date-released: {date_released}",
        "authors:",
        f'  - family-names: "{family}"',
        f'    given-names: "{given}"' if given else '    given-names: ""',
    ]
    if author_email:
        lines.append(f'    email: "{author_email}"')
    lines.extend(
        [
            f'license: "{license_id}"',
            f'repository-code: "{repo_url}"',
            f'url: "{repo_url}"',
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync README/CITATION metadata for a release.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root (default: cwd)")
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"), help="Path to pyproject.toml")
    parser.add_argument("--readme", type=Path, default=Path("README.md"), help="Path to README.md")
    parser.add_argument("--changelog", type=Path, default=Path("docs/CHANGELOG.md"), help="Path to docs/CHANGELOG.md")
    parser.add_argument("--citation-cff", type=Path, default=Path("CITATION.cff"), help="Path to CITATION.cff")
    parser.add_argument("--repo-url", default="https://github.com/lhl/realitycheck", help="Repository URL")
    parser.add_argument("--version", help="Override version (default: read from pyproject.toml)")
    parser.add_argument(
        "--date-released",
        help="Override release date YYYY-MM-DD (default: read from CHANGELOG entry for this version, else today)",
    )
    parser.add_argument(
        "--accessed",
        help="Accessed date for BibTeX note YYYY-MM-DD (default: date-released)",
    )
    parser.add_argument("--test-count", type=int, help="Override pytest test count (default: collect via pytest)")
    parser.add_argument("--write", action="store_true", help="Write changes to disk (default: dry-run/check only)")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if changes are needed (no writes)")
    args = parser.parse_args()

    if args.write and args.check:
        raise ReleaseMetadataError("Choose either --write or --check (not both).")

    repo_root = args.repo_root.resolve()
    pyproject_path = (repo_root / args.pyproject).resolve()
    readme_path = (repo_root / args.readme).resolve()
    changelog_path = (repo_root / args.changelog).resolve()
    citation_cff_path = (repo_root / args.citation_cff).resolve()

    project = load_pyproject_metadata(pyproject_path)
    version = args.version or project.version

    changelog_text = _read_text(changelog_path) if changelog_path.exists() else ""
    changelog_date = find_changelog_release_date(changelog_text, version)
    date_released = args.date_released or changelog_date or date.today().isoformat()

    accessed = args.accessed or date_released

    if args.test_count is not None:
        test_count = args.test_count
    else:
        test_count = collect_pytest_item_count(repo_root)

    bibtex = render_bibtex(
        author_name=project.author_name,
        title=project.title,
        year=int(date_released.split("-", 1)[0]),
        version=version,
        url=args.repo_url,
        accessed=accessed,
    )

    readme_before = _read_text(readme_path)
    readme_after = update_readme_content(
        readme_text=readme_before,
        version=version,
        test_count=test_count,
        bibtex=bibtex,
    )

    cff_before = _read_text(citation_cff_path) if citation_cff_path.exists() else ""
    cff_after = render_citation_cff(
        title=project.title,
        version=version,
        date_released=date_released,
        author_name=project.author_name,
        author_email=project.author_email,
        license_id=project.license,
        repo_url=args.repo_url,
    )

    changed = False
    if readme_after != readme_before:
        changed = True
        if args.write:
            _write_text(readme_path, readme_after)

    if cff_after != cff_before:
        changed = True
        if args.write:
            _write_text(citation_cff_path, cff_after)

    if args.check and changed:
        return 1

    if not args.write:
        # Dry-run output for humans.
        if changed:
            print("Changes needed (run with --write):")
            if readme_after != readme_before:
                print(f"  - {readme_path.relative_to(repo_root)}")
            if cff_after != cff_before:
                print(f"  - {citation_cff_path.relative_to(repo_root)}")
        else:
            print("OK: metadata already up to date")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
