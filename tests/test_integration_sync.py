"""Unit tests for scripts/integration_sync.py."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import integration_sync


def _make_skill_tree(root: Path, integration: str, skill_names: list[str]) -> None:
    base = root / "integrations" / integration / "skills"
    for skill_name in skill_names:
        skill_dir = base / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(f"# {skill_name}\n", encoding="utf-8")


def _make_plugin_tree(root: Path) -> None:
    plugin_dir = root / "integrations" / "claude" / "plugin" / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.json").write_text("{}", encoding="utf-8")


def test_sync_updates_existing_managed_symlink(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    old_root = tmp_path / "roots" / "realitycheck" / "old"
    new_root = tmp_path / "roots" / "realitycheck" / "new"
    _make_skill_tree(old_root, "codex", ["check"])
    _make_skill_tree(new_root, "codex", ["check"])

    codex_dest = home / ".codex" / "skills"
    codex_dest.mkdir(parents=True)
    (codex_dest / "check").symlink_to(
        old_root / "integrations" / "codex" / "skills" / "check"
    )

    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: new_root)

    result = integration_sync.sync_integrations(install_missing=False, quiet=True)
    assert result["updated"] == 1
    assert (codex_dest / "check").resolve() == (
        new_root / "integrations" / "codex" / "skills" / "check"
    ).resolve()


def test_sync_default_does_not_install_missing_skill_when_integration_present(
    tmp_path, monkeypatch
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "codex", ["check", "analyze"])

    codex_dest = home / ".codex" / "skills"
    codex_dest.mkdir(parents=True)
    (codex_dest / "check").symlink_to(
        root / "integrations" / "codex" / "skills" / "check"
    )

    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(install_missing=False, quiet=True)
    assert result["installed"] == 0
    assert not (codex_dest / "analyze").exists()


def test_sync_install_missing_installs_skill_when_integration_present(
    tmp_path, monkeypatch
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "codex", ["check", "analyze"])

    codex_dest = home / ".codex" / "skills"
    codex_dest.mkdir(parents=True)
    (codex_dest / "check").symlink_to(
        root / "integrations" / "codex" / "skills" / "check"
    )

    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(install_missing=True, quiet=True)
    assert result["installed"] == 1
    assert (codex_dest / "analyze").is_symlink()
    assert (codex_dest / "analyze").resolve() == (
        root / "integrations" / "codex" / "skills" / "analyze"
    ).resolve()


def test_sync_skips_install_when_no_existing_integration(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "codex", ["check"])
    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(install_missing=False, quiet=True)
    assert result["installed"] == 0
    assert not (home / ".codex" / "skills" / "check").exists()


def test_sync_install_missing_skips_when_no_existing_integration(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "codex", ["check"])
    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(install_missing=True, quiet=True)
    assert result["installed"] == 0
    assert not (home / ".codex" / "skills" / "check").exists()


def test_sync_all_installs_when_no_existing_integration(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "codex", ["check"])
    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(install_all=True, quiet=True)
    assert result["installed"] == 1
    assert (home / ".codex" / "skills" / "check").is_symlink()


def test_sync_dry_run_does_not_write_files(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "codex", ["check"])
    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(install_all=True, dry_run=True, quiet=True)
    assert result["installed"] == 1
    assert not (home / ".codex" / "skills" / "check").exists()


def test_sync_updates_existing_managed_plugin_symlink(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    old_root = tmp_path / "roots" / "realitycheck" / "old"
    new_root = tmp_path / "roots" / "realitycheck" / "new"
    _make_plugin_tree(old_root)
    _make_plugin_tree(new_root)

    plugin_dest = home / ".claude" / "plugins" / "local"
    plugin_dest.mkdir(parents=True, exist_ok=True)
    (plugin_dest / "reality").symlink_to(old_root / "integrations" / "claude" / "plugin")

    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: new_root)

    result = integration_sync.sync_integrations(quiet=True)
    assert result["updated"] == 1
    assert (plugin_dest / "reality").resolve() == (
        new_root / "integrations" / "claude" / "plugin"
    ).resolve()


def test_sync_default_does_not_install_plugin_when_missing(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "claude", ["check"])
    _make_plugin_tree(root)

    claude_skills_dest = home / ".claude" / "skills"
    claude_skills_dest.mkdir(parents=True, exist_ok=True)
    (claude_skills_dest / "check").symlink_to(
        root / "integrations" / "claude" / "skills" / "check"
    )

    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(quiet=True)
    assert result["installed"] == 0
    assert not (home / ".claude" / "plugins" / "local" / "reality").exists()


def test_sync_install_missing_installs_plugin_when_claude_present(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "claude", ["check"])
    _make_plugin_tree(root)

    claude_skills_dest = home / ".claude" / "skills"
    claude_skills_dest.mkdir(parents=True, exist_ok=True)
    (claude_skills_dest / "check").symlink_to(
        root / "integrations" / "claude" / "skills" / "check"
    )

    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(install_missing=True, quiet=True)
    assert result["installed"] == 1
    assert (home / ".claude" / "plugins" / "local" / "reality").is_symlink()


def test_sync_skips_non_managed_symlink_with_similar_path(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    root = tmp_path / "framework-root"
    _make_skill_tree(root, "codex", ["check"])

    other_root = tmp_path / "myrealitycheck-mirror"
    _make_skill_tree(other_root, "codex", ["check"])

    codex_dest = home / ".codex" / "skills"
    codex_dest.mkdir(parents=True, exist_ok=True)
    non_managed_target = other_root / "integrations" / "codex" / "skills" / "check"
    (codex_dest / "check").symlink_to(non_managed_target)

    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    result = integration_sync.sync_integrations(quiet=True)
    assert result["updated"] == 0
    assert result["skipped"] >= 1
    assert (codex_dest / "check").resolve() == non_managed_target.resolve()


def test_maybe_auto_sync_runs_once_per_version(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    root = tmp_path / "framework-root"
    (root / "integrations").mkdir(parents=True)
    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)
    monkeypatch.setattr(integration_sync, "_get_framework_version", lambda: "9.9.9")

    calls = {"count": 0}

    def _fake_sync(**kwargs):
        calls["count"] += 1
        return {
            "installed": 0,
            "updated": 0,
            "unchanged": 0,
            "skipped": 0,
            "errors": [],
        }

    monkeypatch.setattr(integration_sync, "sync_integrations", _fake_sync)

    integration_sync.maybe_auto_sync_integrations()
    integration_sync.maybe_auto_sync_integrations()

    assert calls["count"] == 1
    assert (home / ".cache" / "realitycheck" / "integration-sync-state.json").exists()


def test_maybe_auto_sync_respects_disable_env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("REALITYCHECK_AUTO_SYNC", "0")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    root = tmp_path / "framework-root"
    (root / "integrations").mkdir(parents=True)
    monkeypatch.setattr(integration_sync, "_resolve_framework_root", lambda: root)

    calls = {"count": 0}

    def _fake_sync(**kwargs):
        calls["count"] += 1
        return {}

    monkeypatch.setattr(integration_sync, "sync_integrations", _fake_sync)

    integration_sync.maybe_auto_sync_integrations()
    assert calls["count"] == 0
