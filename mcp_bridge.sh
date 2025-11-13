#!/bin/bash
# MCP HTTP Bridge Startup Script
# ================================
# Starts the HTTP MCP wrapper and exposes it via ngrok
#
# Usage:
#   ./mcp_bridge.sh [port]
#
# Prerequisites:
#   - Python 3.11+ with fastapi and uvicorn installed
#   - ngrok installed (brew install ngrok on Mac)
#   - MCP servers configured in http_mcp_wrapper.py

set -e

PORT=${1:-8080}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting MCP HTTP Bridge..."
echo "================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

# Check if ngrok is available
if ! command -v ngrok &> /dev/null; then
    echo "❌ Error: ngrok not found"
    echo ""
    echo "Install ngrok:"
    echo "  Mac: brew install ngrok"
    echo "  Linux: snap install ngrok"
    echo ""
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Installing dependencies..."
    pip install fastapi uvicorn
fi

echo "✅ Prerequisites check passed"
echo ""

# Start the HTTP wrapper in the background
echo "🔧 Starting HTTP MCP wrapper on port $PORT..."
cd "$SCRIPT_DIR"
python3 http_mcp_wrapper.py --host 0.0.0.0 --port "$PORT" &
WRAPPER_PID=$!

# Wait for server to start
sleep 3

# Check if wrapper started successfully
if ! ps -p $WRAPPER_PID > /dev/null; then
    echo "❌ Failed to start HTTP wrapper"
    exit 1
fi

echo "✅ HTTP wrapper started (PID: $WRAPPER_PID)"
echo ""

# Start ngrok tunnel
echo "🌐 Starting ngrok tunnel..."
ngrok http "$PORT" &
NGROK_PID=$!

sleep 3

echo ""
echo "✅ MCP Bridge is running!"
echo "================================"
echo ""
echo "📡 Your MCP servers are now accessible via HTTPS"
echo ""
echo "To get your ngrok URL:"
echo "  1. Open http://localhost:4040 in your browser"
echo "  2. Copy the HTTPS forwarding URL"
echo "  3. Use it in your .mcp.json config"
echo ""
echo "Example .mcp.json config:"
echo '{'
echo '  "mcpServers": {'
echo '    "nba-mcp-server": {'
echo '      "transport": "http",'
echo '      "url": "https://YOUR-NGROK-URL.ngrok.io/mcp/nba-mcp-server"'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "Press Ctrl+C to stop the bridge"
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping MCP bridge..."
    kill $WRAPPER_PID 2>/dev/null || true
    kill $NGROK_PID 2>/dev/null || true
    echo "✅ Stopped"
}

trap cleanup EXIT INT TERM

# Wait for user interrupt
wait $WRAPPER_PID
