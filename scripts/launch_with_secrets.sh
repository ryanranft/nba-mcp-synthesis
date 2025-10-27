#!/bin/bash
# Launch overnight convergence with proper secrets loading

set -e

echo "🔐 Loading secrets from hierarchical structure..."
python3 /Users/ryanranft/load_env_hierarchical.py nba-mcp-synthesis NBA WORKFLOW

# Export the loaded secrets
eval "$(python3 /Users/ryanranft/load_env_hierarchical.py nba-mcp-synthesis NBA WORKFLOW --export)"

echo "✅ Secrets loaded"
echo ""

# Now launch the overnight convergence script
cd /Users/ryanranft/nba-mcp-synthesis
./launch_overnight_convergence.sh


