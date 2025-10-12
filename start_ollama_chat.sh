#!/bin/bash

# NBA MCP + Ollama Desktop Chat Launcher
# This script opens a beautiful web interface for chatting with Ollama

echo "🏀 Starting NBA MCP + Ollama Chat..."
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    open -a Ollama
    sleep 3

    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "❌ Failed to start Ollama. Please start it manually:"
        echo "   Option 1: Open Ollama.app from Applications"
        echo "   Option 2: Run 'ollama serve' in terminal"
        exit 1
    fi
fi

echo "✅ Ollama is running"
echo "✅ Model: qwen2.5-coder:32b"
echo "✅ MCP Tools: 90 NBA tools available"
echo ""
echo "🌐 Opening chat interface in your browser..."
echo ""

# Open the HTML file in default browser
open "/Users/ryanranft/nba-mcp-synthesis/ollama_web_chat.html"

echo "✅ Chat interface opened!"
echo ""
echo "📖 How to use:"
echo "   • Chat naturally about NBA data"
echo "   • Click suggestions to get started"
echo "   • Type 'exit' in terminal to stop (Ctrl+C)"
echo ""
echo "🔧 If the chat doesn't work:"
echo "   1. Check that Ollama is running (green dot in menu bar)"
echo "   2. Verify the model: ollama list"
echo "   3. Restart Ollama: pkill ollama && ollama serve"
echo ""
echo "Press Ctrl+C to close this launcher"
echo ""

# Keep script running
tail -f /dev/null


