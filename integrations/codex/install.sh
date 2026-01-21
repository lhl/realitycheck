#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DEST="${CODEX_HOME}/skills"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${ROOT}/skills"

if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "Error: skills directory not found: $SKILLS_DIR" >&2
  exit 1
fi

mkdir -p "$DEST"

installed=0
for skill_dir in "$SKILLS_DIR"/*; do
  [[ -d "$skill_dir" ]] || continue
  name="$(basename "$skill_dir")"
  target="${DEST}/${name}"

  if [[ -L "$target" ]]; then
    existing="$(readlink "$target" || true)"
    if [[ "$(readlink -f "$target")" == "$(readlink -f "$skill_dir")" ]]; then
      echo "Already installed: ${name}"
      continue
    fi
    echo "Error: ${target} exists (symlink to ${existing})" >&2
    echo "Remove it or run: bash integrations/codex/uninstall.sh" >&2
    exit 1
  fi

  if [[ -e "$target" ]]; then
    echo "Error: ${target} already exists (not a symlink)" >&2
    echo "Remove it manually or choose a different CODEX_HOME." >&2
    exit 1
  fi

  ln -s "$skill_dir" "$target"
  echo "Installed: ${name} -> ${skill_dir}"
  installed=$((installed + 1))
done

echo ""
echo "Installed ${installed} skill(s) into ${DEST}"
echo "Restart Codex to pick up new skills."
