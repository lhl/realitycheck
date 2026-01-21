#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DEST="${CODEX_HOME}/skills"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${ROOT}/skills"

if [[ ! -d "$DEST" ]]; then
  echo "No Codex skills directory found at: $DEST"
  exit 0
fi

removed=0
for skill_dir in "$SKILLS_DIR"/*; do
  [[ -d "$skill_dir" ]] || continue
  name="$(basename "$skill_dir")"
  target="${DEST}/${name}"

  if [[ -L "$target" ]]; then
    if [[ "$(readlink -f "$target")" == "$(readlink -f "$skill_dir")" ]]; then
      rm "$target"
      echo "Removed: ${name}"
      removed=$((removed + 1))
    else
      echo "Skip: ${name} (installed symlink points elsewhere)"
    fi
  elif [[ -e "$target" ]]; then
    echo "Skip: ${name} (${target} exists but is not a symlink)"
  fi
done

echo ""
echo "Removed ${removed} skill(s) from ${DEST}"
