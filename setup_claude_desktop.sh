#!/bin/bash
#
# Setup Claude Desktop Integration for NBA MCP Server
#

set -e

echo "========================================"
echo "Claude Desktop MCP Setup"
echo "========================================"
echo

# Claude Desktop config location
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Check if Claude Desktop is installed
if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    echo "❌ Claude Desktop not found at: $CLAUDE_CONFIG_DIR"
    echo
    echo "Please install Claude Desktop first:"
    echo "   https://claude.ai/download"
    exit 1
fi

echo "✅ Claude Desktop found"
echo

# Backup existing config if it exists
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    BACKUP_FILE="$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backing up existing config to:"
    echo "   $BACKUP_FILE"
    cp "$CLAUDE_CONFIG_FILE" "$BACKUP_FILE"
    echo
fi

# Copy our config
echo "📝 Installing NBA MCP Server configuration..."
cp claude_desktop_config.json "$CLAUDE_CONFIG_FILE"
echo "✅ Configuration installed"
echo

# Show next steps
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo
echo "Next steps:"
echo "1. Restart Claude Desktop (quit and reopen)"
echo "2. Look for the MCP tools icon (🔌) in Claude"
echo "3. Try a test query:"
echo "   'Using the NBA MCP tools, list the available databases'"
echo
echo "Configuration file: $CLAUDE_CONFIG_FILE"
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: No .env file found"
    echo "   Make sure environment variables are set system-wide"
    echo "   or Claude Desktop won't have access to AWS credentials"
    echo
fi

echo "========================================"
