#!/bin/bash

# Configure local MCP to use AWS Ollama instance

echo "🔧 Configure NBA MCP to use AWS Ollama"
echo "======================================"
echo ""

# Check if connection file exists
if [ ! -f "ollama-aws-connection.txt" ]; then
    echo "❌ ollama-aws-connection.txt not found"
    echo "   Run ./deploy_ollama_aws.sh first"
    exit 1
fi

# Extract IP from connection file
AWS_IP=$(grep "Public IP:" ollama-aws-connection.txt | awk '{print $3}')

if [ -z "$AWS_IP" ]; then
    echo "❌ Could not find AWS IP address"
    exit 1
fi

echo "📡 AWS Ollama Instance: $AWS_IP"
echo ""

# Test connection
echo "🧪 Testing connection to AWS Ollama..."
if curl -s "http://${AWS_IP}:11434/api/tags" > /dev/null 2>&1; then
    echo "✅ Connection successful!"

    # List available models
    echo ""
    echo "📦 Available models on AWS:"
    curl -s "http://${AWS_IP}:11434/api/tags" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for model in data.get('models', []):
    size_gb = model.get('size', 0) / (1024**3)
    print(f\"  • {model.get('name')}: {size_gb:.1f}GB\")
"
else
    echo "⚠️  Cannot connect to AWS Ollama yet"
    echo "   The instance may still be setting up (15-30 minutes)"
    echo "   Check status with:"
    echo "   ssh -i ollama-mcp-key.pem ubuntu@${AWS_IP}"
    echo "   sudo journalctl -u ollama -f"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Update web interface
echo "🌐 Updating web chat interface..."
sed -i.bak "s|http://localhost:11434|http://${AWS_IP}:11434|g" ollama_web_chat.html
echo "✅ Web interface updated"

# Update Python chat
echo "🐍 Updating Python chat script..."
sed -i.bak "s|http://localhost:11434|http://${AWS_IP}:11434|g" ollama_mcp_chat.py
sed -i.bak "s|http://localhost:11434|http://${AWS_IP}:11434|g" test_ollama_mcp.py
echo "✅ Python scripts updated"

# Update Cursor settings
if [ -f "$HOME/Library/Application Support/Cursor/User/settings.json" ]; then
    echo "⚙️  Updating Cursor settings..."
    SETTINGS_FILE="$HOME/Library/Application Support/Cursor/User/settings.json"

    # Backup
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"

    # Update baseURL
    python3 << EOPYTHON
import json

with open("$SETTINGS_FILE", 'r') as f:
    settings = json.load(f)

# Update Ollama baseURL
if 'cursor.chat.models' in settings:
    for model in settings['cursor.chat.models']:
        if 'ollama' in model.get('id', '').lower():
            model['baseURL'] = "http://${AWS_IP}:11434/v1"
            # Update to larger model
            model['model'] = "qwen2.5-coder:72b"
            model['name'] = "Ollama AWS Qwen2.5-Coder 72B"

with open("$SETTINGS_FILE", 'w') as f:
    json.dump(settings, f, indent=4)

print("✅ Cursor settings updated")
EOPYTHON
else
    echo "⚠️  Cursor settings not found"
fi

echo ""

# Create environment variable file
cat > ollama_aws_env.sh << EOF
# Source this file to use AWS Ollama
export OLLAMA_HOST="http://${AWS_IP}:11434"
export OLLAMA_AWS_IP="${AWS_IP}"

# Usage:
# source ollama_aws_env.sh
EOF

echo "✅ Configuration complete!"
echo ""
echo "═══════════════════════════════════════════════════════"
echo "🎉 Ready to use AWS Ollama!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🚀 Start chatting:"
echo "  1. Web interface: ./start_ollama_chat.sh"
echo "  2. Terminal: python3 ollama_mcp_chat.py"
echo "  3. Cursor: Reload window (Cmd+Shift+P → Reload)"
echo ""
echo "🔧 The configuration now points to:"
echo "  AWS IP: $AWS_IP"
echo "  Model: qwen2.5-coder:72b (72B parameters!)"
echo "  GPU: NVIDIA A10G (24GB VRAM)"
echo ""
echo "⚡ Benefits of 72B model:"
echo "  • Much better reasoning"
echo "  • More accurate tool usage"
echo "  • Better context understanding"
echo "  • Higher quality responses"
echo ""
echo "💰 Remember to stop the instance when not in use!"
echo "  aws ec2 stop-instances --instance-ids [ID]"
echo ""
echo "📚 See AWS_OLLAMA_GUIDE.md for more info"
echo "═══════════════════════════════════════════════════════"


