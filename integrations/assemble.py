#!/usr/bin/env python3
"""Assemble Reality Check skills from Jinja2 templates.

This script generates integration-specific SKILL.md files from a shared
template library and configuration file.

Usage:
    python assemble.py                    # Generate all skills for all integrations
    python assemble.py --integration claude  # Generate only Claude skills
    python assemble.py --skill check      # Generate only the 'check' skill
    python assemble.py --docs             # Also generate methodology/workflows/check-core.md
    python assemble.py --dry-run          # Show what would be generated
    python assemble.py --diff             # Show diffs vs existing files
    python assemble.py --check            # Exit non-zero if files would change
"""

import argparse
import difflib
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Paths relative to this script
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
TEMPLATES_DIR = SCRIPT_DIR / "_templates"
CONFIG_FILE = SCRIPT_DIR / "_config" / "skills.yaml"
CHECK_CORE_PATH = REPO_ROOT / "methodology" / "workflows" / "check-core.md"

INTEGRATIONS = ["amp", "claude", "codex", "opencode"]


def load_config() -> dict:
    """Load skills configuration from YAML."""
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def setup_jinja_env() -> Environment:
    """Set up Jinja2 environment with template loader."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


def get_skill_name(skill_key: str, integration: str, defaults: dict) -> str:
    """Get the skill name with integration-specific prefix."""
    prefix = defaults.get(integration, {}).get("name_prefix", "")
    return f"{prefix}{skill_key}"


def get_output_path(skill_key: str, integration: str, defaults: dict) -> Path:
    """Get the output path for a generated skill."""
    skill_dir = defaults.get(integration, {}).get("skill_dir", f"{integration}/skills")
    name = get_skill_name(skill_key, integration, defaults)
    return SCRIPT_DIR / skill_dir / name / "SKILL.md"


def render_skill(
    env: Environment,
    integration: str,
    skill_key: str,
    skill_config: dict,
    defaults: dict,
) -> str:
    """Render a skill for a specific integration."""
    # Get wrapper template for this integration
    wrapper_template = f"wrappers/{integration}.md.j2"

    try:
        template = env.get_template(wrapper_template)
    except TemplateNotFound:
        print(f"Warning: Wrapper template not found: {wrapper_template}", file=sys.stderr)
        return ""

    # Build context for template
    name = get_skill_name(skill_key, integration, defaults)
    integration_config = skill_config.get(integration, {})

    context = {
        "name": name,
        "title": skill_config.get("title", skill_key.title()),
        "description": skill_config.get("description", ""),
        "template": skill_config.get("template", f"{skill_key}.md.j2"),
        "related": skill_config.get("related", []),
        # Integration-specific
        "invocation_prefix": "/" if integration == "claude" else "$",
        "amp_prefix": defaults.get("amp", {}).get("name_prefix", "realitycheck-"),
    }

    # Merge integration-specific config
    context.update(integration_config)

    try:
        return template.render(**context)
    except Exception as e:
        print(f"Error rendering {skill_key} for {integration}: {e}", file=sys.stderr)
        return ""


def write_skill(
    output_path: Path,
    content: str,
    dry_run: bool = False,
    diff: bool = False,
    check: bool = False,
) -> bool:
    """Write skill to file, with optional dry-run/diff/check modes.

    Returns True if file was changed (or would be changed).
    """
    # Read existing content if file exists
    existing = ""
    if output_path.exists():
        existing = output_path.read_text()

    # Check if content changed
    changed = existing != content

    if dry_run:
        status = "CHANGED" if changed else "unchanged"
        print(f"[DRY-RUN] {output_path} - {status}")
        return changed

    if diff and changed:
        print(f"\n--- {output_path}")
        diff_lines = difflib.unified_diff(
            existing.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=str(output_path),
            tofile=str(output_path) + " (new)",
        )
        sys.stdout.writelines(diff_lines)
        return changed

    if check:
        if changed:
            print(f"CHANGED: {output_path}")
        return changed

    # Actually write the file
    if changed:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        print(f"WROTE: {output_path}")
    else:
        print(f"unchanged: {output_path}")

    return changed


def generate_check_core(
    env: Environment,
    dry_run: bool = False,
    diff: bool = False,
    check: bool = False,
) -> bool:
    """Generate methodology/workflows/check-core.md from templates.

    This creates a standalone methodology reference document.
    Returns True if file was changed.
    """
    # Render the check skill template directly (no wrapper)
    try:
        template = env.get_template("skills/check.md.j2")
    except TemplateNotFound:
        print("Warning: skills/check.md.j2 not found", file=sys.stderr)
        return False

    # Minimal context for standalone rendering
    context = {
        "invocation_prefix": "/",  # Use Claude-style for docs
    }

    try:
        skill_content = template.render(**context)
    except Exception as e:
        print(f"Error rendering check-core.md: {e}", file=sys.stderr)
        return False

    # Build the full document with header
    content = f"""<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Source: integrations/_templates/skills/check.md.j2 -->
<!-- Regenerate: make assemble-skills (with --docs flag) -->

# Reality Check - Core Analysis Methodology

This document is the **read-only reference** for the Reality Check analysis methodology.
It is generated from the same templates used to build integration skills.

To modify this content, edit the templates in `integrations/_templates/` and regenerate.

---

{skill_content}
"""

    return write_skill(CHECK_CORE_PATH, content, dry_run, diff, check)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Reality Check skills from templates"
    )
    parser.add_argument(
        "--integration",
        choices=INTEGRATIONS + ["all"],
        default="all",
        help="Generate skills for specific integration (default: all)",
    )
    parser.add_argument(
        "--skill",
        help="Generate only this specific skill",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show diffs between existing and new content",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any files would change (for CI)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--docs",
        action="store_true",
        help="Also generate methodology/workflows/check-core.md",
    )
    args = parser.parse_args()

    # Load config
    try:
        config = load_config()
    except FileNotFoundError:
        print(f"Error: Config file not found: {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config: {e}", file=sys.stderr)
        sys.exit(1)

    # Set up Jinja environment
    env = setup_jinja_env()

    # Determine which integrations to process
    integrations = INTEGRATIONS if args.integration == "all" else [args.integration]

    # Get defaults and skills from config
    defaults = config.get("defaults", {})
    skills = config.get("skills", {})

    # Track changes for --check mode
    any_changed = False
    total_generated = 0
    total_changed = 0

    # Generate skills
    for integration in integrations:
        if args.verbose:
            print(f"\n=== {integration.upper()} ===")

        for skill_key, skill_config in skills.items():
            # Filter by --skill if specified
            if args.skill and skill_key != args.skill:
                continue

            # Check if skill is enabled for this integration (default: True)
            if not skill_config.get(integration, {}).get("enabled", True):
                if args.verbose:
                    print(f"  {skill_key}: disabled")
                continue

            # Render the skill
            content = render_skill(env, integration, skill_key, skill_config, defaults)
            if not content:
                continue

            # Get output path
            output_path = get_output_path(skill_key, integration, defaults)

            # Write (or check) the skill
            changed = write_skill(
                output_path,
                content,
                dry_run=args.dry_run,
                diff=args.diff,
                check=args.check,
            )

            total_generated += 1
            if changed:
                total_changed += 1
                any_changed = True

    # Generate check-core.md if requested
    if args.docs:
        if args.verbose:
            print("\n=== DOCS ===")
        docs_changed = generate_check_core(
            env,
            dry_run=args.dry_run,
            diff=args.diff,
            check=args.check,
        )
        total_generated += 1
        if docs_changed:
            total_changed += 1
            any_changed = True

    # Summary
    print(f"\nGenerated: {total_generated} files, {total_changed} changed")

    # Exit with error if --check and files changed
    if args.check and any_changed:
        print("\nError: Generated files are out of date. Run 'make assemble-skills' to update.")
        sys.exit(1)


if __name__ == "__main__":
    main()
