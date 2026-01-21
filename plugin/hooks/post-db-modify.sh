#!/bin/bash
#
# post-db-modify.sh - Hook that runs after database modifications
#
# This hook:
# 1. Auto-commits data changes to the data repository (if enabled)
# 2. Provides reminders about validation
#
# Environment:
#   REALITYCHECK_AUTO_COMMIT - Set to "true" to enable auto-commit (default: true)
#   REALITYCHECK_AUTO_PUSH - Set to "true" to also push after commit (default: false)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# This hook runs after Bash commands matching *db.py*
# Only trigger on write operations
if echo "$BASH_COMMAND" 2>/dev/null | grep -qE "(claim add|source add|chain add|prediction add|update|import|init|reset)"; then
    # Auto-commit if enabled (default: true)
    if [[ "${REALITYCHECK_AUTO_COMMIT:-true}" == "true" ]]; then
        "$SCRIPT_DIR/auto-commit-data.sh" "$BASH_COMMAND" 2>/dev/null || true
    fi
fi

exit 0
