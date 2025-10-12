#!/bin/bash
echo "🔍 Checking All Ollama Deployments"
echo "=================================="
echo ""

echo "1. 🏠 Local Ollama:"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "   ✅ Running"
  curl -s http://localhost:11434/api/tags | \
    python3 -c "import sys,json;[print(f'   • {m[\"name\"]}') for m in json.load(sys.stdin)['models']]"
else
  echo "   ❌ Not running"
fi

echo ""
echo "2. ☁️ AWS Ollama:"
if curl -s http://34.226.246.126:11434/api/tags > /dev/null 2>&1; then
  echo "   ✅ Running"
  curl -s http://34.226.246.126:11434/api/tags | \
    python3 -c "import sys,json;[print(f'   • {m[\"name\"]}') for m in json.load(sys.stdin)['models']]"
else
  echo "   ❌ Not running"
fi

echo ""
echo "3. ⚙️ Cursor Config:"
if grep -q "cursor.chat.models" "$HOME/Library/Application Support/Cursor/User/settings.json" 2>/dev/null; then
  echo "   ✅ Configured"
  MODEL_COUNT=$(grep -c "\"id\".*ollama" "$HOME/Library/Application Support/Cursor/User/settings.json" 2>/dev/null || echo "0")
  echo "   • $MODEL_COUNT models available"
else
  echo "   ❌ Not configured"
fi

echo ""
echo "4. 🔧 MCP Tools:"
if [ -f "$HOME/.cursor/mcp.json" ]; then
  echo "   ✅ Global config exists"
fi
if [ -f "/Users/ryanranft/nba-mcp-synthesis/.cursor/mcp.json" ]; then
  echo "   ✅ nba-mcp-synthesis configured"
fi
if [ -f "/Users/ryanranft/nba-simulator-aws/.cursor/mcp.json" ]; then
  echo "   ✅ nba-simulator-aws configured"
fi

echo ""
echo "=================================="


