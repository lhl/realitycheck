#!/bin/bash
# Uninstall Reality Check skills for Amp

set -e

SKILLS_DST="${HOME}/.config/agents/skills"

SKILLS=(
    "realitycheck-check"
    "realitycheck-search"
    "realitycheck-validate"
    "realitycheck-export"
    "realitycheck-stats"
)

echo "Removing Reality Check skills for Amp..."

for skill in "${SKILLS[@]}"; do
    dst="$SKILLS_DST/$skill"
    
    if [ -L "$dst" ]; then
        rm "$dst"
        echo "  Removed: $skill"
    elif [ -d "$dst" ]; then
        echo "  Warning: $dst is a directory, not removing"
    fi
done

echo ""
echo "Skills removed."
