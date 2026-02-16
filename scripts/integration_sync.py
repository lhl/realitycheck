#!/usr/bin/env python3
"""Best-effort syncing for Reality Check skills/plugins across integrations."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any


SKILL_DESTINATIONS: dict[str, Path] = {
    "amp": Path(".config/agents/skills"),
    "claude": Path(".claude/skills"),
    "codex": Path(".codex/skills"),
    "opencode": Path(".config/opencode/skills"),
}

CLAUDE_PLUGIN_DESTINATION = Path(".claude/plugins/local/reality")
AUTO_SYNC_ENV_VAR = "REALITYCHECK_AUTO_SYNC"
AUTO_SYNC_STATE_PATH = Path(".cache/realitycheck/integration-sync-state.json")
MARKDOWN_SLASH = "/"


def _is_falsey(value: str) -> bool:
    return value.strip().lower() in {"0", "false", "no", "off", "disable", "disabled"}


def _state_path() -> Path:
    return Path.home() / AUTO_SYNC_STATE_PATH


def _get_framework_version() -> str:
    try:
        return metadata.version("realitycheck")
    except Exception:
        return "dev"


def _resolve_framework_root() -> Path | None:
    env_root = os.getenv("REALITYCHECK_FRAMEWORK_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if (candidate / "integrations").is_dir():
            return candidate

    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "integrations").is_dir():
        return candidate

    return None


def _normalize_path_text(path_text: str) -> str:
    return path_text.replace("\\", MARKDOWN_SLASH)


def _is_existing_path(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _is_managed_skill_symlink(path: Path, integration: str, skill_name: str) -> bool:
    if not path.is_symlink():
        return False

    expected_fragment = f"integrations/{integration}/skills/{skill_name}"
    candidates: list[str] = []

    try:
        candidates.append(_normalize_path_text(os.readlink(path)))
    except OSError:
        pass

    try:
        candidates.append(_normalize_path_text(str(path.resolve(strict=False))))
    except Exception:
        pass

    return any(expected_fragment in text and "realitycheck" in text for text in candidates)


def _is_managed_plugin_symlink(path: Path) -> bool:
    if not path.is_symlink():
        return False

    expected_fragment = "integrations/claude/plugin"
    candidates: list[str] = []

    try:
        candidates.append(_normalize_path_text(os.readlink(path)))
    except OSError:
        pass

    try:
        candidates.append(_normalize_path_text(str(path.resolve(strict=False))))
    except Exception:
        pass

    return any(expected_fragment in text and "realitycheck" in text for text in candidates)


def _relink(dst: Path, src: Path, dry_run: bool) -> None:
    if dry_run:
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    dst.symlink_to(src)


def _load_auto_sync_state() -> dict[str, Any]:
    state_path = _state_path()
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_auto_sync_state(payload: dict[str, Any]) -> None:
    state_path = _state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sync_integrations(
    *,
    install_missing: bool = False,
    install_all: bool = False,
    dry_run: bool = False,
    quiet: bool = True,
) -> dict[str, Any]:
    framework_root = _resolve_framework_root()
    result: dict[str, Any] = {
        "framework_root": str(framework_root) if framework_root else None,
        "installed": 0,
        "updated": 0,
        "unchanged": 0,
        "skipped": 0,
        "errors": [],
    }

    if framework_root is None:
        result["errors"].append("Could not locate framework integrations directory.")
        return result

    for integration, relative_dest in SKILL_DESTINATIONS.items():
        src_base = framework_root / "integrations" / integration / "skills"
        if not src_base.is_dir():
            continue

        src_skills = sorted(path for path in src_base.iterdir() if path.is_dir())
        if not src_skills:
            continue

        dest_base = Path.home() / relative_dest
        has_existing_install = any(
            _is_existing_path(dest_base / src_skill.name) for src_skill in src_skills
        )
        manage_this_integration = install_all or has_existing_install

        if not manage_this_integration and not install_missing:
            continue

        for src_skill in src_skills:
            dst_skill = dest_base / src_skill.name
            src_resolved = src_skill.resolve()

            if dst_skill.is_symlink():
                if _is_managed_skill_symlink(dst_skill, integration, src_skill.name):
                    current_target = dst_skill.resolve(strict=False)
                    if current_target == src_resolved:
                        result["unchanged"] += 1
                    else:
                        _relink(dst_skill, src_resolved, dry_run=dry_run)
                        result["updated"] += 1
                else:
                    result["skipped"] += 1
                continue

            if dst_skill.exists():
                result["skipped"] += 1
                continue

            should_install = install_all or install_missing or has_existing_install
            if should_install:
                _relink(dst_skill, src_resolved, dry_run=dry_run)
                result["installed"] += 1
            else:
                result["skipped"] += 1

    src_plugin = framework_root / "integrations" / "claude" / "plugin"
    dst_plugin = Path.home() / CLAUDE_PLUGIN_DESTINATION
    claude_skills_path = Path.home() / SKILL_DESTINATIONS["claude"]
    claude_skill_installed = any(
        _is_existing_path(claude_skills_path / skill_dir.name)
        for skill_dir in (framework_root / "integrations" / "claude" / "skills").iterdir()
        if skill_dir.is_dir()
    ) if (framework_root / "integrations" / "claude" / "skills").is_dir() else False

    if src_plugin.is_dir():
        should_manage_plugin = install_all or dst_plugin.is_symlink() or dst_plugin.exists() or claude_skill_installed
        if should_manage_plugin:
            src_plugin_resolved = src_plugin.resolve()
            if dst_plugin.is_symlink():
                if _is_managed_plugin_symlink(dst_plugin):
                    current_target = dst_plugin.resolve(strict=False)
                    if current_target == src_plugin_resolved:
                        result["unchanged"] += 1
                    else:
                        _relink(dst_plugin, src_plugin_resolved, dry_run=dry_run)
                        result["updated"] += 1
                else:
                    result["skipped"] += 1
            elif dst_plugin.exists():
                result["skipped"] += 1
            elif install_all or install_missing or claude_skill_installed:
                _relink(dst_plugin, src_plugin_resolved, dry_run=dry_run)
                result["installed"] += 1

    if not quiet:
        print(f"Framework root: {framework_root}")
        print(
            "Integration sync summary: "
            f"{result['installed']} installed, "
            f"{result['updated']} updated, "
            f"{result['unchanged']} unchanged, "
            f"{result['skipped']} skipped"
        )
        for error in result["errors"]:
            print(f"Error: {error}")

    return result


def maybe_auto_sync_integrations() -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return

    env_value = os.getenv(AUTO_SYNC_ENV_VAR, "1")
    if _is_falsey(env_value):
        return

    framework_root = _resolve_framework_root()
    if framework_root is None:
        return

    current_version = _get_framework_version()
    state = _load_auto_sync_state()
    framework_root_text = str(framework_root.resolve())

    if (
        state.get("version") == current_version
        and state.get("framework_root") == framework_root_text
    ):
        return

    result = sync_integrations(install_missing=False, install_all=False, dry_run=False, quiet=True)
    state_payload = {
        "version": current_version,
        "framework_root": framework_root_text,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "result": {
            "installed": result["installed"],
            "updated": result["updated"],
            "unchanged": result["unchanged"],
            "skipped": result["skipped"],
            "errors": result["errors"],
        },
    }

    try:
        _write_auto_sync_state(state_payload)
    except Exception:
        return
