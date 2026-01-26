#!/bin/bash
#
# update-readme-stats.sh - Update README.md with current database statistics
#
# This script updates the "Current Status" and "Claim Domains" sections
# in the data repository's README.md with live database stats.
#
# Usage:
#   update-readme-stats.sh [PROJECT_ROOT]
#
# Environment:
#   REALITYCHECK_DATA - Path to the LanceDB database

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source project context
source "$SCRIPT_DIR/resolve-project.sh" 2>/dev/null || true

# Use provided path or PROJECT_ROOT
TARGET_ROOT="${1:-$PROJECT_ROOT}"

if [[ -z "$TARGET_ROOT" || ! -d "$TARGET_ROOT" ]]; then
    echo "Error: No valid project root found" >&2
    exit 1
fi

README_PATH="$TARGET_ROOT/README.md"

if [[ ! -f "$README_PATH" ]]; then
    echo "Error: README.md not found at $README_PATH" >&2
    exit 1
fi

# Get stats from database.
#
# Prefer importing the local checkout (development mode) if available; otherwise fall back
# to the installed `realitycheck` package (which ships the `scripts.*` modules).
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
# In a dev checkout the plugin lives at: integrations/claude/plugin/
# The framework repo root is three levels up from PLUGIN_ROOT.
FRAMEWORK_ROOT="$(cd "$PLUGIN_ROOT/../../.." && pwd)"

PYTHON_RUNNER=("python3")
if command -v uv &> /dev/null && [[ -f "$FRAMEWORK_ROOT/pyproject.toml" ]]; then
    PYTHON_RUNNER=("uv" "run" "python")
fi

PYTHON_CWD=""
if [[ -f "$FRAMEWORK_ROOT/scripts/db.py" ]]; then
    PYTHON_CWD="$FRAMEWORK_ROOT"
fi

# Get counts using Python.
if [[ -n "$PYTHON_CWD" ]]; then
    STATS=$(cd "$PYTHON_CWD" && "${PYTHON_RUNNER[@]}" -c "
from scripts.db import get_db, get_stats

db = get_db()
stats = get_stats(db)

# Get domain counts
claims_table = db.open_table('claims')
all_claims = claims_table.search().limit(1000).to_list()

from collections import Counter
domain_counts = Counter(c.get('domain', 'UNKNOWN') for c in all_claims)

print(f'CLAIMS={stats[\"claims\"]}')
print(f'SOURCES={stats[\"sources\"]}')
print(f'CHAINS={stats[\"chains\"]}')
print(f'PREDICTIONS={stats[\"predictions\"]}')

# Print domain counts
for domain in ['TECH', 'LABOR', 'ECON', 'GOV', 'SOC', 'TRANS', 'RESOURCE', 'GEO', 'INST', 'RISK', 'META']:
    print(f'DOMAIN_{domain}={domain_counts.get(domain, 0)}')
" 2>/dev/null)
else
    STATS=$("${PYTHON_RUNNER[@]}" -c "
from scripts.db import get_db, get_stats

db = get_db()
stats = get_stats(db)

claims_table = db.open_table('claims')
all_claims = claims_table.search().limit(1000).to_list()

from collections import Counter
domain_counts = Counter(c.get('domain', 'UNKNOWN') for c in all_claims)

print(f'CLAIMS={stats[\"claims\"]}')
print(f'SOURCES={stats[\"sources\"]}')
print(f'CHAINS={stats[\"chains\"]}')
print(f'PREDICTIONS={stats[\"predictions\"]}')

for domain in ['TECH', 'LABOR', 'ECON', 'GOV', 'SOC', 'TRANS', 'RESOURCE', 'GEO', 'INST', 'RISK', 'META']:
    print(f'DOMAIN_{domain}={domain_counts.get(domain, 0)}')
" 2>/dev/null)
fi

if [[ -z "$STATS" ]]; then
    echo "Error: Failed to get database stats" >&2
    exit 1
fi

# Parse stats
eval "$STATS"

# Get current date
TODAY=$(date +%Y-%m-%d)

# Create the new Current Status section
STATUS_TABLE="| Metric | Count |
|--------|-------|
| **Claims** | $CLAIMS |
| **Sources** | $SOURCES |
| **Argument Chains** | $CHAINS |
| **Predictions Tracked** | $PREDICTIONS |"

# Create the new Claim Domains section
DOMAINS_TABLE="| Domain | Description | Claims |
|--------|-------------|--------|
| TECH | Technology & AI | $DOMAIN_TECH |
| LABOR | Labor & Employment | $DOMAIN_LABOR |
| ECON | Economics & Markets | $DOMAIN_ECON |
| GOV | Governance & Policy | $DOMAIN_GOV |
| SOC | Social Dynamics | $DOMAIN_SOC |
| TRANS | Transition Dynamics | $DOMAIN_TRANS |
| RESOURCE | Resource Constraints | $DOMAIN_RESOURCE |
| GEO | Geopolitics | $DOMAIN_GEO |
| INST | Institutions & Organizations | $DOMAIN_INST |
| RISK | Risk Assessment | $DOMAIN_RISK |
| META | Framework & Methodology | $DOMAIN_META |"

# Update README using Python for reliable text replacement
python3 << EOF
import re

with open('$README_PATH', 'r') as f:
    content = f.read()

# Update Current Status table
status_pattern = r'(\| Metric \| Count \|.*?\| \*\*Predictions Tracked\*\* \| )\d+( \|)'
status_repl = r'''| Metric | Count |
|--------|-------|
| **Claims** | $CLAIMS |
| **Sources** | $SOURCES |
| **Argument Chains** | $CHAINS |
| **Predictions Tracked** | $PREDICTIONS |'''
content = re.sub(
    r'\| Metric \| Count \|[\s\S]*?\| \*\*Predictions Tracked\*\* \| \d+ \|',
    status_repl,
    content
)

# Update Claim Domains table
domains_repl = '''| Domain | Description | Claims |
|--------|-------------|--------|
| TECH | Technology & AI | $DOMAIN_TECH |
| LABOR | Labor & Employment | $DOMAIN_LABOR |
| ECON | Economics & Markets | $DOMAIN_ECON |
| GOV | Governance & Policy | $DOMAIN_GOV |
| SOC | Social Dynamics | $DOMAIN_SOC |
| TRANS | Transition Dynamics | $DOMAIN_TRANS |
| RESOURCE | Resource Constraints | $DOMAIN_RESOURCE |
| GEO | Geopolitics | $DOMAIN_GEO |
| INST | Institutions & Organizations | $DOMAIN_INST |
| RISK | Risk Assessment | $DOMAIN_RISK |
| META | Framework & Methodology | $DOMAIN_META |'''
content = re.sub(
    r'\| Domain \| Description \| Claims \|[\s\S]*?\| META \| Framework & Methodology \| \d+ \|',
    domains_repl,
    content
)

# Update last updated date
content = re.sub(
    r'\*Last updated: \d{4}-\d{2}-\d{2}\*',
    '*Last updated: $TODAY*',
    content
)

with open('$README_PATH', 'w') as f:
    f.write(content)

print(f"Updated README.md: {$CLAIMS} claims, {$SOURCES} sources, {$CHAINS} chains, {$PREDICTIONS} predictions")
EOF
