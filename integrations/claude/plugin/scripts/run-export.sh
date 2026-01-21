#!/bin/bash
#
# run-export.sh - Shell wrapper for the Reality Check export CLI (export.py)
#
# This script resolves the project context and runs export.py with proper environment.
#
# Usage:
#   run-export.sh yaml claims.yaml   # Export claims to YAML
#   run-export.sh md output/         # Export to Markdown
#   run-export.sh --domain TECH      # Filter by domain

set -e

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
# In a dev checkout the plugin lives at: integrations/claude/plugin/
# The framework repo root is three levels up from PLUGIN_ROOT.
FRAMEWORK_ROOT="$(cd "$PLUGIN_ROOT/../../.." && pwd)"

# Source project context
source "$SCRIPT_DIR/resolve-project.sh"

# Determine which Python/export.py to use
EXPORT_PY=""

# First: Check if we're in the framework repo (development mode)
if [[ -f "$FRAMEWORK_ROOT/scripts/export.py" ]]; then
    EXPORT_PY="$FRAMEWORK_ROOT/scripts/export.py"
# Second: Check bundled scripts in plugin/lib/
elif [[ -f "$PLUGIN_ROOT/lib/export.py" ]]; then
    EXPORT_PY="$PLUGIN_ROOT/lib/export.py"
# Third: Use installed package (via pip install realitycheck)
elif command -v rc-export &> /dev/null; then
    exec rc-export "$@"
fi

if [[ -z "$EXPORT_PY" ]]; then
    echo "Error: Could not find export.py or installed realitycheck package" >&2
    exit 1
fi

# Check if uv is available (preferred for development)
if command -v uv &> /dev/null && [[ -f "$FRAMEWORK_ROOT/pyproject.toml" ]]; then
    cd "$FRAMEWORK_ROOT"
    exec uv run python "$EXPORT_PY" "$@"
else
    exec python "$EXPORT_PY" "$@"
fi
