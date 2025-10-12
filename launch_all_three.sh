#!/bin/bash

echo "🚀 Launching Ollama in ALL THREE Places"
echo "========================================"
echo ""

# 1. Start web server if not running
if ! pgrep -f "python3 -m http.server 8000" > /dev/null; then
    echo "Starting web server..."
    cd /Users/ryanranft/nba-mcp-synthesis
    python3 -m http.server 8000 --directory . > /dev/null 2>&1 &
    sleep 2
fi

# 2. Open Local Web Interface
echo "1️⃣  Opening 🏠 Local Ollama Web Interface..."
open http://localhost:8000/ollama_web_chat.html
sleep 1

# 3. Open AWS Web Interface
echo "2️⃣  Opening ☁️ AWS Ollama Web Interface..."
open http://localhost:8000/ollama_web_chat_aws.html
sleep 1

# 4. Open Cursor
echo "3️⃣  Opening ⚙️ Cursor IDE..."
open -a "Cursor" /Users/ryanranft/nba-mcp-synthesis

echo ""
echo "✅ ALL THREE LAUNCHED!"
echo ""
echo "📱 You should now see:"
echo "   • Browser Tab 1: 🏠 Local Ollama (localhost)"
echo "   • Browser Tab 2: ☁️ AWS Ollama (cloud)"
echo "   • Cursor IDE: Model selector with 3 options"
echo ""
echo "🎯 In Cursor:"
echo "   1. Press Cmd+Shift+P"
echo "   2. Type 'Reload Window'"
echo "   3. Click model selector (bottom right)"
echo "   4. Choose from 3 models!"
echo ""
echo "🎉 Happy coding with AI + NBA analytics!"


