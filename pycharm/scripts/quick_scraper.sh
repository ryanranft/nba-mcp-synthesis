#!/bin/bash
# Quick scraper generation from terminal
# Usage: ./quick_scraper.sh "https://example.com" "Extract player stats"

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_DIR"

URL="${1:-}"
DESCRIPTION="${2:-}"

if [ -z "$URL" ]; then
    echo "Usage: $0 <url> <description>"
    echo "Example: $0 'https://nba.com/stats' 'Extract player statistics'"
    exit 1
fi

python3 pycharm/mcp_external_tool.py scraper \
    --url "$URL" \
    --description "$DESCRIPTION" \
    --output "generated_scraper_$(date +%Y%m%d_%H%M%S).py"

echo ""
echo "✅ Scraper generated and saved!"
