"""
Regression tests for Codex skills shipped in-repo.

Codex loads SKILL.md files by parsing YAML frontmatter; invalid YAML causes the
skill to be skipped. These tests ensure the frontmatter remains parseable.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def _load_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"Missing YAML frontmatter start: {path}")

    parts = text.split("\n---\n", 2)
    if len(parts) < 2:
        raise AssertionError(f"Missing YAML frontmatter end delimiter: {path}")

    frontmatter = parts[0].removeprefix("---\n")
    data = yaml.safe_load(frontmatter)
    if not isinstance(data, dict):
        raise AssertionError(f"Frontmatter must be a mapping: {path}")
    return data


def test_codex_skill_frontmatter_is_valid_yaml():
    repo_root = Path(__file__).parent.parent
    skills_root = repo_root / "integrations" / "codex" / "skills"
    assert skills_root.exists(), "Expected integrations/codex/skills to exist"

    skill_files = sorted(skills_root.glob("*/SKILL.md"))
    assert skill_files, "Expected at least one Codex skill to exist"

    for skill_path in skill_files:
        data = _load_frontmatter(skill_path)
        assert data.get("name"), f"Missing frontmatter name: {skill_path}"
        assert data.get("description"), f"Missing frontmatter description: {skill_path}"
