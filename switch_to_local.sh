#!/bin/bash
echo "🔄 Switching to Local Ollama..."
sed -i '' 's|34.226.246.126|localhost|g' ollama_web_chat.html 2>/dev/null
sed -i '' 's|34.226.246.126|localhost|g' ollama_mcp_chat.py 2>/dev/null
sed -i '' 's|34.226.246.126|localhost|g' test_ollama_mcp.py 2>/dev/null
echo "✅ Switched to Local Ollama (localhost:11434)"
echo ""
echo "Available models:"
ollama list 2>/dev/null || echo "  (run 'ollama list' to see)"


