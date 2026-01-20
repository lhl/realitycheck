#!/bin/bash
#
# on-stop.sh - Hook that runs when Claude Code session ends
#
# This hook runs validation to catch any data integrity issues
# before the session ends.

set -e

# Get plugin root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

# Source project context
if [[ -f "$PLUGIN_ROOT/scripts/resolve-project.sh" ]]; then
    source "$PLUGIN_ROOT/scripts/resolve-project.sh" 2>/dev/null || true
fi

# Only run if we have a database
if [[ -z "$ANALYSIS_DB_PATH" ]] || [[ ! -d "$ANALYSIS_DB_PATH" ]]; then
    exit 0
fi

# Run validation quietly - only output if there are errors
FRAMEWORK_ROOT="$(dirname "$PLUGIN_ROOT")"

if [[ -f "$FRAMEWORK_ROOT/scripts/validate.py" ]]; then
    RESULT=$(cd "$FRAMEWORK_ROOT" && uv run python scripts/validate.py 2>&1) || true

    # Check if there are errors (not just warnings)
    if echo "$RESULT" | grep -q "ERROR"; then
        echo ""
        echo "⚠️  Reality Check Validation Issues Detected:"
        echo "$RESULT" | grep -E "(ERROR|error)" | head -5
        echo ""
        echo "Run '/validate' for full details."
    fi
fi
