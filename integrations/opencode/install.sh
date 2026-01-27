#!/usr/bin/env bash
# Install Reality Check skills for OpenCode
# Symlinks skills to ~/.config/opencode/skills/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="${OPENCODE_SKILLS_DIR:-$HOME/.config/opencode/skills}"

echo "Installing Reality Check skills for OpenCode..."
mkdir -p "$SKILLS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name=$(basename "$skill_dir")
    
    # Remove existing symlink if present
    if [ -L "$SKILLS_DST/$skill_name" ]; then
        rm "$SKILLS_DST/$skill_name"
    fi
    
    # Skip if directory already exists (non-symlink)
    if [ -d "$SKILLS_DST/$skill_name" ] && [ ! -L "$SKILLS_DST/$skill_name" ]; then
        echo "  Warning: $SKILLS_DST/$skill_name exists as directory, skipping"
        continue
    fi
    
    # Create symlink
    ln -s "$skill_dir" "$SKILLS_DST/$skill_name"
    echo "  Installed: $skill_name"
done

echo ""
echo "Skills installed to $SKILLS_DST"
echo "Restart OpenCode to use them."
