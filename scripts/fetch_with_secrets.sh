#!/bin/bash
# Fetch player panel data with secrets loaded

set -e

echo "Loading secrets..."
eval $(python3 /Users/ryanranft/load_env_hierarchical.py nba-mcp-synthesis NBA production 2>&1 | grep "^export")

echo ""
echo "Running fetch script..."
python3 scripts/fetch_complete_panel.py
