#!/bin/bash
#
# Setup Secrets and Launch Autonomous Convergence Enhancement
#
# This script:
# 1. Loads API keys from centralized secrets structure
# 2. Exports them as environment variables
# 3. Verifies all pre-flight checks pass
# 4. Launches the overnight convergence run
#

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════"
echo "  Setup Secrets and Launch - NBA MCP Synthesis"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Navigate to project root
cd "$(dirname "$0")"

# Step 1: Load secrets from hierarchical structure
echo "📦 Step 1: Loading secrets from hierarchical structure..."
python3 -c "
import sys
sys.path.insert(0, '.')
from mcp_server.unified_secrets_manager import load_secrets_hierarchical
import os

success = load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'WORKFLOW')
if not success:
    print('❌ Failed to load secrets')
    sys.exit(1)

google_key = os.getenv('GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')
anthropic_key = os.getenv('ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW')

if not google_key or not anthropic_key:
    print('❌ API keys not found in secrets structure')
    sys.exit(1)

# Export for shell
with open('/tmp/export_secrets.sh', 'w') as f:
    f.write(f'export GEMINI_API_KEY=\"{google_key}\"\\n')
    f.write(f'export CLAUDE_API_KEY=\"{anthropic_key}\"\\n')

print(f'✅ Loaded GOOGLE_API_KEY ({len(google_key)} chars)')
print(f'✅ Loaded ANTHROPIC_API_KEY ({len(anthropic_key)} chars)')
"

if [ $? -ne 0 ]; then
    echo "❌ Failed to load secrets"
    exit 1
fi

# Step 2: Export to current shell
echo ""
echo "🔑 Step 2: Exporting API keys to environment..."
source /tmp/export_secrets.sh

if [ -n "$GEMINI_API_KEY" ] && [ -n "$CLAUDE_API_KEY" ]; then
    echo "✅ GEMINI_API_KEY exported (${#GEMINI_API_KEY} chars)"
    echo "✅ CLAUDE_API_KEY exported (${#CLAUDE_API_KEY} chars)"
else
    echo "❌ Failed to export API keys"
    exit 1
fi

# Step 3: Run pre-flight checks
echo ""
echo "🔍 Step 3: Running pre-flight checks..."
echo ""
python3 scripts/pre_flight_check.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Pre-flight checks failed"
    echo "Please fix the issues above and try again"
    exit 1
fi

# Step 4: Confirm launch
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ ALL CHECKS PASSED - READY TO LAUNCH"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "The autonomous convergence enhancement will:"
echo "  • Run all 9 workflow phases"
echo "  • Extract 300-400 recommendations from 51 books"
echo "  • Take 10-15 hours to complete"
echo "  • Cost approximately \$150-250"
echo ""
echo "You can monitor progress at:"
echo "  • Dashboard: http://localhost:8080"
echo "  • Quick check: ./check_progress.sh"
echo "  • Logs: tail -f logs/overnight_convergence_*.log"
echo ""
echo "To stop gracefully: pkill -SIGTERM -f run_full_workflow.py"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

read -p "Type 'START' to launch the overnight run (or Ctrl+C to cancel): " confirm

if [ "$confirm" != "START" ]; then
    echo "❌ Launch cancelled"
    exit 1
fi

# Step 5: Launch
echo ""
echo "🚀 Launching autonomous convergence enhancement..."
echo ""

# Launch the convergence run directly
./launch_overnight_convergence.sh

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ LAUNCH COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "The overnight run is now executing autonomously."
echo "Check progress at: http://localhost:8080"
echo ""





