#!/bin/bash
# commit-msg hook: Strip co-author bylines and tool attribution from commit messages
#
# Install:
#   ln -sf ../../scripts/hooks/strip-coauthors.sh .git/hooks/commit-msg
#   chmod +x .git/hooks/commit-msg
#
# Or for all repos:
#   git config --global core.hooksPath /path/to/realitycheck/scripts/hooks

COMMIT_MSG_FILE="$1"

if [ -z "$COMMIT_MSG_FILE" ]; then
    echo "Usage: $0 <commit-msg-file>"
    exit 1
fi

# Create temp file
TEMP_FILE=$(mktemp)

# Strip patterns:
# - Co-Authored-By: / Co-authored-by: lines
# - Generated with [Claude Code]... lines
# - via [Happy]... lines
# - Amp-Thread-ID: lines
# - Trailing blank lines
sed -E \
    -e '/^[Cc]o-[Aa]uthored-[Bb]y:/d' \
    -e '/^Generated with \[Claude/d' \
    -e '/^via \[Happy\]/d' \
    -e '/^Amp-Thread-ID:/d' \
    "$COMMIT_MSG_FILE" | \
    # Remove trailing blank lines
    sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' > "$TEMP_FILE"

# Replace original file
mv "$TEMP_FILE" "$COMMIT_MSG_FILE"

exit 0
