#!/bin/bash
# Quick SQL query generation from natural language
# Usage: ./quick_sql.sh "Find top 10 scorers"

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_DIR"

REQUEST="${1:-}"

if [ -z "$REQUEST" ]; then
    echo "Usage: $0 <natural language query>"
    echo "Example: $0 'Find the top 10 players by total points scored'"
    exit 1
fi

python3 pycharm/mcp_external_tool.py sql \
    --request "$REQUEST"

echo ""
echo "✅ Query generated!"
