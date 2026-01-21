#!/bin/bash
#
# run-db.sh - Shell wrapper for the Reality Check database CLI (db.py)
#
# This script resolves the project context and runs db.py with proper environment.
#
# Usage:
#   run-db.sh init
#   run-db.sh claim add --text "..." --type "[F]" --domain "TECH" --evidence-level "E3"
#   run-db.sh search "AI automation"
#   run-db.sh stats

set -e

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
# In a dev checkout the plugin lives at: integrations/claude/plugin/
# The framework repo root is three levels up from PLUGIN_ROOT.
FRAMEWORK_ROOT="$(cd "$PLUGIN_ROOT/../../.." && pwd)"

# Source project context
source "$SCRIPT_DIR/resolve-project.sh"

# Determine which Python/db.py to use
DB_PY=""

# First: Check if we're in the framework repo (development mode)
if [[ -f "$FRAMEWORK_ROOT/scripts/db.py" ]]; then
    DB_PY="$FRAMEWORK_ROOT/scripts/db.py"
# Second: Check bundled scripts in plugin/lib/
elif [[ -f "$PLUGIN_ROOT/lib/db.py" ]]; then
    DB_PY="$PLUGIN_ROOT/lib/db.py"
# Third: Use installed package (via pip install realitycheck)
elif command -v rc-db &> /dev/null; then
    exec rc-db "$@"
fi

if [[ -z "$DB_PY" ]]; then
    echo "Error: Could not find db.py or installed realitycheck package" >&2
    exit 1
fi

# Check if uv is available (preferred for development)
if command -v uv &> /dev/null && [[ -f "$FRAMEWORK_ROOT/pyproject.toml" ]]; then
    cd "$FRAMEWORK_ROOT"
    exec uv run python "$DB_PY" "$@"
else
    exec python "$DB_PY" "$@"
fi
