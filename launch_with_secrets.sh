#!/bin/bash
# Load secrets from test_export3.sh and launch overnight run

set -e

echo "============================================================"
echo "🔐 NBA MCP Synthesis - Loading Secrets and Launching"
echo "============================================================"
echo ""

# Step 1: Load secrets from test_export3.sh
echo "📦 Step 1: Loading API keys from test_export3.sh..."
if [ ! -f "/Users/ryanranft/test_export3.sh" ]; then
    echo "❌ ERROR: test_export3.sh not found at /Users/ryanranft/"
    exit 1
fi

source /Users/ryanranft/test_export3.sh

echo "   ✅ Secrets loaded from test_export3.sh"
echo ""

# Step 2: Create simple name aliases for launch_overnight_convergence.sh
echo "🔗 Step 2: Creating simple name aliases..."
export GEMINI_API_KEY="$GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"
export CLAUDE_API_KEY="$ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"

if [ -z "$GEMINI_API_KEY" ] || [ -z "$CLAUDE_API_KEY" ]; then
    echo "❌ ERROR: Failed to create aliases"
    echo "   GEMINI_API_KEY: ${#GEMINI_API_KEY} chars"
    echo "   CLAUDE_API_KEY: ${#CLAUDE_API_KEY} chars"
    exit 1
fi

echo "   ✅ GEMINI_API_KEY: ${#GEMINI_API_KEY} chars"
echo "   ✅ CLAUDE_API_KEY: ${#CLAUDE_API_KEY} chars"
echo ""

# Step 3: Launch overnight convergence run with auto-confirmation
echo "🚀 Step 3: Launching overnight convergence run (auto-confirming)..."
echo ""

echo "START" | ./launch_overnight_convergence.sh
