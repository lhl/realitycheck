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
if [[ -z "$REALITYCHECK_DATA" ]] || [[ ! -d "$REALITYCHECK_DATA" ]]; then
    exit 0
fi

# Run validation quietly - only output if there are errors.
#
# Prefer local checkout (development mode) if available; otherwise fall back to installed
# `rc-validate` (packaged console entry point).
FRAMEWORK_ROOT="$(cd "$PLUGIN_ROOT/../../.." && pwd)"

RESULT=""
if [[ -f "$FRAMEWORK_ROOT/scripts/validate.py" ]]; then
    if command -v uv &> /dev/null && [[ -f "$FRAMEWORK_ROOT/pyproject.toml" ]]; then
        RESULT=$(cd "$FRAMEWORK_ROOT" && uv run python scripts/validate.py 2>&1) || true
    else
        RESULT=$(cd "$FRAMEWORK_ROOT" && python3 scripts/validate.py 2>&1) || true
    fi
elif command -v rc-validate &> /dev/null; then
    RESULT=$(rc-validate 2>&1) || true
fi

if [[ -n "$RESULT" ]]; then

    # Check if there are errors (not just warnings)
    if echo "$RESULT" | grep -q "ERROR"; then
        echo ""
        echo "⚠️  Reality Check Validation Issues Detected:"
        echo "$RESULT" | grep -E "(ERROR|error)" | head -5
        echo ""
        echo "Run '/validate' for full details."
    fi
fi
