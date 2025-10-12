#!/bin/bash
echo "🔄 Switching to AWS Ollama..."
sed -i '' 's|localhost:11434|34.226.246.126:11434|g' ollama_web_chat.html 2>/dev/null
sed -i '' 's|localhost:11434|34.226.246.126:11434|g' ollama_mcp_chat.py 2>/dev/null
sed -i '' 's|localhost:11434|34.226.246.126:11434|g' test_ollama_mcp.py 2>/dev/null
echo "✅ Switched to AWS Ollama (34.226.246.126:11434)"
echo ""
echo "Testing connection..."
if curl -s http://34.226.246.126:11434/api/tags > /dev/null 2>&1; then
  echo "✅ AWS Ollama is reachable"
  echo ""
  echo "Available models:"
  curl -s http://34.226.246.126:11434/api/tags | \
    python3 -c "import sys,json;[print(f'  • {m[\"name\"]}') for m in json.load(sys.stdin)['models']]" 2>/dev/null
else
  echo "⚠️  Cannot reach AWS Ollama"
  echo "   Instance may be stopped. Start it with:"
  echo "   aws ec2 start-instances --instance-ids i-06ec10b8f8fbe0ee4"
fi


