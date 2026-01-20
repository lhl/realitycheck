#!/bin/bash
#
# post-db-modify.sh - Hook that runs after database modifications
#
# This hook provides a gentle reminder about validation after
# database operations.

# This hook runs after Bash commands matching *db.py*
# We keep it lightweight to not slow down operations

# Only output occasionally (not on every single db command)
# Use a simple heuristic: only remind on 'add' or 'update' operations
if echo "$BASH_COMMAND" 2>/dev/null | grep -qE "(claim add|source add|chain add|prediction add|update|import|reset)"; then
    # Silent by default - validation runs on Stop anyway
    # Uncomment below to enable reminders:
    # echo "💡 Tip: Run '/validate' to check data integrity"
    :
fi

exit 0
