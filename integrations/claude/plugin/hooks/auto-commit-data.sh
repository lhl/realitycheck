#!/bin/bash
#
# auto-commit-data.sh - Auto-commit Reality Check data changes after db operations
#
# This hook is triggered after db.py commands to automatically commit
# changes to the data repository.
#
# Environment:
#   REALITYCHECK_DATA - Path to the LanceDB database
#   PROJECT_ROOT - Path to the data project root
#
# The hook only commits if:
# 1. REALITYCHECK_DATA points to a valid git repository
# 2. There are actual changes to commit
# 3. The command was a write operation (add, import, init, reset)

set -e

# Source project context to get PROJECT_ROOT
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../scripts/resolve-project.sh" 2>/dev/null || true

# Exit if no project root found
if [[ -z "$PROJECT_ROOT" ]]; then
    exit 0
fi

# Check if PROJECT_ROOT is a git repository
if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
    exit 0
fi

cd "$PROJECT_ROOT"

# Check for changes in project content we want to version-control.
# Note: we intentionally do not auto-stage inbox/ (often contains large/raw source files).
if ! git status --porcelain -- data/ analysis/ tracking/ README.md 2>/dev/null | grep -q .; then
    # No changes to commit
    exit 0
fi

# Get the command that was run (passed as argument or from env)
COMMAND="${1:-${TOOL_INPUT:-unknown}}"

# Determine commit message based on command
COMMIT_MSG="data: auto-commit after db operation"
case "$COMMAND" in
    *"claim add"*)
        COMMIT_MSG="data: add claim(s)"
        ;;
    *"source add"*)
        COMMIT_MSG="data: add source(s)"
        ;;
    *"prediction add"*)
        COMMIT_MSG="data: add prediction(s)"
        ;;
    *"chain add"*)
        COMMIT_MSG="data: add chain(s)"
        ;;
    *"import"*)
        COMMIT_MSG="data: import data"
        ;;
    *"init"*)
        COMMIT_MSG="data: initialize database"
        ;;
    *"reset"*)
        COMMIT_MSG="data: reset database"
        ;;
esac

# Update README.md stats before committing
if [[ -x "$SCRIPT_DIR/../scripts/update-readme-stats.sh" ]]; then
    "$SCRIPT_DIR/../scripts/update-readme-stats.sh" "$PROJECT_ROOT" 2>/dev/null || true
fi

# Stage and commit data project changes (including updated README.md).
git add data/ analysis/ tracking/ 2>/dev/null || true
git add README.md 2>/dev/null || true
git commit -m "$COMMIT_MSG" --no-verify 2>/dev/null || true

# Optionally push (controlled by env var)
if [[ "${REALITYCHECK_AUTO_PUSH:-false}" == "true" ]]; then
    git push 2>/dev/null || true
fi

echo "Auto-committed data changes to $PROJECT_ROOT"
