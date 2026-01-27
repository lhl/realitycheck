#!/usr/bin/env bash
# Uninstall Reality Check skills for OpenCode
# Removes symlinks from ~/.config/opencode/skills/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="${OPENCODE_SKILLS_DIR:-$HOME/.config/opencode/skills}"

echo "Removing Reality Check skills for OpenCode..."

for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name=$(basename "$skill_dir")
    
    if [ -L "$SKILLS_DST/$skill_name" ]; then
        rm "$SKILLS_DST/$skill_name"
        echo "  Removed: $skill_name"
    fi
done

echo ""
echo "Skills removed from $SKILLS_DST"
