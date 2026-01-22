#!/bin/bash
#
# resolve-project.sh - Find Reality Check project root and set environment variables
#
# This script searches upward from the current directory to find:
# 1. A .realitycheck.yaml config file (data project)
# 2. A data/realitycheck.lance database
#
# It exports:
# - PROJECT_ROOT: Path to the project root
# - REALITYCHECK_DATA: Path to the LanceDB database
# - REALITYCHECK_FRAMEWORK: Path to the realitycheck framework (if installed)
#
# Usage:
#   source resolve-project.sh
#   # or
#   eval "$(./resolve-project.sh)"

set -e

# If REALITYCHECK_DATA is already set and valid, respect it
if [[ -n "$REALITYCHECK_DATA" && -d "$REALITYCHECK_DATA" ]]; then
    # Derive PROJECT_ROOT from REALITYCHECK_DATA if not set
    if [[ -z "$PROJECT_ROOT" ]]; then
        # Assume standard layout: PROJECT_ROOT/data/realitycheck.lance
        PROJECT_ROOT="$(dirname "$(dirname "$REALITYCHECK_DATA")")"
    fi
    export PROJECT_ROOT
    export REALITYCHECK_DATA
    # Skip search - env var takes precedence
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        echo "export PROJECT_ROOT=\"$PROJECT_ROOT\""
        echo "export REALITYCHECK_DATA=\"$REALITYCHECK_DATA\""
        echo "export REALITYCHECK_FRAMEWORK=\"$REALITYCHECK_FRAMEWORK\""
    fi
    return 0 2>/dev/null || exit 0
fi

# Start from current directory or provided path
START_DIR="${1:-$(pwd)}"
CURRENT="$START_DIR"

PROJECT_ROOT=""
REALITYCHECK_DATA=""

# Search upward for project markers
while [[ "$CURRENT" != "/" ]]; do
    # Check for .realitycheck.yaml config
    if [[ -f "$CURRENT/.realitycheck.yaml" ]]; then
        PROJECT_ROOT="$CURRENT"
        # Try to read db_path from config
        if command -v yq &> /dev/null; then
            DB_PATH_CONF=$(yq -r '.db_path // empty' "$CURRENT/.realitycheck.yaml" 2>/dev/null || true)
            if [[ -n "$DB_PATH_CONF" ]]; then
                REALITYCHECK_DATA="$CURRENT/$DB_PATH_CONF"
            fi
        fi
        break
    fi

    # Check for data/realitycheck.lance
    if [[ -d "$CURRENT/data/realitycheck.lance" ]]; then
        PROJECT_ROOT="$CURRENT"
        REALITYCHECK_DATA="$CURRENT/data/realitycheck.lance"
        break
    fi

    # Check for data directory with any .lance file
    if [[ -d "$CURRENT/data" ]]; then
        LANCE_DB=$(find "$CURRENT/data" -maxdepth 1 -name "*.lance" -type d 2>/dev/null | head -1)
        if [[ -n "$LANCE_DB" ]]; then
            PROJECT_ROOT="$CURRENT"
            REALITYCHECK_DATA="$LANCE_DB"
            break
        fi
    fi

    CURRENT=$(dirname "$CURRENT")
done

# Default database path if not found
if [[ -z "$REALITYCHECK_DATA" && -n "$PROJECT_ROOT" ]]; then
    REALITYCHECK_DATA="$PROJECT_ROOT/data/realitycheck.lance"
fi

# Try to find the realitycheck framework
REALITYCHECK_FRAMEWORK=""
if command -v realitycheck &> /dev/null; then
    REALITYCHECK_FRAMEWORK=$(dirname "$(dirname "$(which realitycheck)")")
elif [[ -f "$HOME/.local/share/realitycheck/scripts/db.py" ]]; then
    REALITYCHECK_FRAMEWORK="$HOME/.local/share/realitycheck"
elif [[ -d "/opt/realitycheck" ]]; then
    REALITYCHECK_FRAMEWORK="/opt/realitycheck"
fi

# Export variables
export PROJECT_ROOT
export REALITYCHECK_DATA
export REALITYCHECK_FRAMEWORK

# If sourced, variables are already exported
# If run as script, print for eval
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "export PROJECT_ROOT=\"$PROJECT_ROOT\""
    echo "export REALITYCHECK_DATA=\"$REALITYCHECK_DATA\""
    echo "export REALITYCHECK_FRAMEWORK=\"$REALITYCHECK_FRAMEWORK\""
fi
