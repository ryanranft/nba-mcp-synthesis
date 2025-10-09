#!/bin/bash
#
# Stop MCP Server Script
# Gracefully stops the NBA MCP server
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${PROJECT_ROOT}/.mcp_server.pid"
LOG_FILE="${PROJECT_ROOT}/logs/mcp_server.log"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}NBA MCP Server - Shutdown${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  MCP server is not running (no PID file found)${NC}"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is actually running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  MCP server is not running (process $PID not found)${NC}"
    echo -e "   Removing stale PID file..."
    rm "$PID_FILE"
    exit 0
fi

echo -e "${BLUE}[1/3] Stopping MCP server (PID: $PID)...${NC}"

# Send SIGTERM for graceful shutdown
kill -TERM "$PID"

# Wait for process to stop
MAX_WAIT=15
WAIT_COUNT=0

echo -e "${BLUE}[2/3] Waiting for graceful shutdown...${NC}"

while ps -p "$PID" > /dev/null 2>&1 && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))

    if [ $((WAIT_COUNT % 3)) -eq 0 ]; then
        echo -e "   Still waiting... (${WAIT_COUNT}s)"
    fi
done

# Check if process stopped
if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Process did not stop gracefully, forcing shutdown...${NC}"
    kill -KILL "$PID"
    sleep 2

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${RED}❌ Failed to stop server${NC}"
        exit 1
    fi
fi

# Remove PID file
echo -e "${BLUE}[3/3] Cleaning up...${NC}"
rm -f "$PID_FILE"

echo -e "${GREEN}✅ MCP server stopped successfully${NC}"
echo ""
echo -e "${BLUE}Log file preserved at: $LOG_FILE${NC}"
echo ""
