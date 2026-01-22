#!/bin/bash
# Install Reality Check skills for Amp
# Symlinks skills to ~/.config/agents/skills/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="${HOME}/.config/agents/skills"

# Skills to install
SKILLS=(
    "realitycheck-analyze"
    "realitycheck-check"
    "realitycheck-export"
    "realitycheck-extract"
    "realitycheck-search"
    "realitycheck-stats"
    "realitycheck-validate"
)

echo "Installing Reality Check skills for Amp..."
echo ""

# Create destination directory if needed
mkdir -p "$SKILLS_DST"

for skill in "${SKILLS[@]}"; do
    src="$SKILLS_SRC/$skill"
    dst="$SKILLS_DST/$skill"
    
    if [ ! -d "$src" ]; then
        echo "  Warning: $skill not found at $src"
        continue
    fi
    
    # Remove existing symlink or warn about directory
    if [ -L "$dst" ]; then
        rm "$dst"
    elif [ -d "$dst" ]; then
        echo "  Warning: $dst exists as directory, skipping"
        continue
    fi
    
    ln -s "$src" "$dst"
    echo "  Installed: $skill"
done

echo ""
echo "Skills installed to $SKILLS_DST"
echo ""
echo "Restart Amp to use the new skills."
echo "Skills activate on natural language triggers like:"
echo "  - 'Analyze this article for claims'"
echo "  - 'Search for claims about AI'"
echo "  - 'Validate the database'"
