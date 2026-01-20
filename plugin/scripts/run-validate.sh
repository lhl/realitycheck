#!/bin/bash
#
# run-validate.sh - Shell wrapper for the RealityCheck validation CLI (validate.py)
#
# This script resolves the project context and runs validate.py with proper environment.
#
# Usage:
#   run-validate.sh                  # Validate database (default)
#   run-validate.sh --yaml /path     # Validate YAML files
#   run-validate.sh --strict         # Treat warnings as errors

set -e

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
FRAMEWORK_ROOT="$(dirname "$PLUGIN_ROOT")"

# Source project context
source "$SCRIPT_DIR/resolve-project.sh"

# Determine which Python/validate.py to use
VALIDATE_PY=""

# First: Check if we're in the framework repo (development mode)
if [[ -f "$FRAMEWORK_ROOT/scripts/validate.py" ]]; then
    VALIDATE_PY="$FRAMEWORK_ROOT/scripts/validate.py"
# Second: Check bundled scripts in plugin/lib/
elif [[ -f "$PLUGIN_ROOT/lib/validate.py" ]]; then
    VALIDATE_PY="$PLUGIN_ROOT/lib/validate.py"
# Third: Use installed package
elif command -v rc-validate &> /dev/null; then
    exec rc-validate "$@"
elif python -c "import realitycheck" &> /dev/null; then
    exec python -m realitycheck.validate "$@"
fi

if [[ -z "$VALIDATE_PY" ]]; then
    echo "Error: Could not find validate.py or installed realitycheck package" >&2
    exit 1
fi

# Check if uv is available (preferred for development)
if command -v uv &> /dev/null && [[ -f "$FRAMEWORK_ROOT/pyproject.toml" ]]; then
    cd "$FRAMEWORK_ROOT"
    exec uv run python "$VALIDATE_PY" "$@"
else
    exec python "$VALIDATE_PY" "$@"
fi
