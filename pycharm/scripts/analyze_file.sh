#!/bin/bash
# Analyze a code file with MCP
# Usage: ./analyze_file.sh my_script.py "Find bugs"

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_DIR"

FILE="${1:-}"
REQUEST="${2:-Analyze this code for issues and improvements}"

if [ -z "$FILE" ]; then
    echo "Usage: $0 <file> [request]"
    echo "Example: $0 scraper.py 'Find performance issues'"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "Error: File '$FILE' not found"
    exit 1
fi

python3 pycharm/mcp_external_tool.py analyze \
    --file "$FILE" \
    --request "$REQUEST"

echo ""
echo "✅ Analysis complete!"
