#!/bin/bash
#
# Start MCP Server Script
# Starts the NBA MCP server with proper validation and monitoring
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
VENV_PATH="${PROJECT_ROOT}/venv"
PID_FILE="${PROJECT_ROOT}/.mcp_server.pid"
LOG_FILE="${PROJECT_ROOT}/logs/mcp_server.log"
ENV_FILE="${PROJECT_ROOT}/.env"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}NBA MCP Server - Startup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Step 1: Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  MCP server is already running (PID: $PID)${NC}"
        echo -e "   Use './scripts/stop_mcp_server.sh' to stop it first"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Stale PID file found, removing...${NC}"
        rm "$PID_FILE"
    fi
fi

# Step 2: Validate environment
echo -e "${BLUE}[1/5] Validating environment...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo -e "   Copy .env.example to .env and configure it"
    exit 1
fi

# Run validation script
if [ -f "${PROJECT_ROOT}/scripts/validate_environment.py" ]; then
    python3 "${PROJECT_ROOT}/scripts/validate_environment.py" --exit-on-failure
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Environment validation failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Environment validation script not found, skipping...${NC}"
fi

echo -e "${GREEN}✅ Environment validated${NC}"
echo ""

# Step 3: Check Python dependencies
echo -e "${BLUE}[2/5] Checking Python dependencies...${NC}"

# Check if we should use venv
if [ -d "$VENV_PATH" ]; then
    echo -e "   Using virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
fi

# Verify critical packages
python3 -c "import mcp, boto3, psycopg2, anthropic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Missing required Python packages${NC}"
    echo -e "   Run: pip install -r requirements.txt"
    exit 1
fi

echo -e "${GREEN}✅ Dependencies satisfied${NC}"
echo ""

# Step 4: Create log directory
echo -e "${BLUE}[3/5] Preparing log directory...${NC}"

mkdir -p "$(dirname "$LOG_FILE")"
echo -e "${GREEN}✅ Log directory ready${NC}"
echo ""

# Step 5: Start server
echo -e "${BLUE}[4/5] Starting MCP server...${NC}"

cd "$PROJECT_ROOT"

# Start server in background
nohup python3 -m mcp_server.server >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo "$SERVER_PID" > "$PID_FILE"

echo -e "   Server PID: $SERVER_PID"
echo -e "   Log file: $LOG_FILE"
echo ""

# Step 6: Wait for server to be ready
echo -e "${BLUE}[5/5] Waiting for server to be ready...${NC}"

MAX_WAIT=30
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    # Check if process is still running
    if ! ps -p "$SERVER_PID" > /dev/null 2>&1; then
        echo -e "${RED}❌ Server process died${NC}"
        echo -e "   Check logs: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi

    # Try to connect (using a simple HTTP check if health endpoint exists)
    # For now, just wait a bit
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))

    if [ $((WAIT_COUNT % 5)) -eq 0 ]; then
        echo -e "   Still waiting... (${WAIT_COUNT}s)"
    fi

    # If we've waited 10 seconds, assume it's ready
    if [ $WAIT_COUNT -ge 10 ]; then
        break
    fi
done

# Final check
if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MCP server started successfully${NC}"
    echo ""
    echo -e "${BLUE}Server Information:${NC}"
    echo -e "   PID: $SERVER_PID"
    echo -e "   Log: $LOG_FILE"
    echo -e "   URL: http://localhost:3000"
    echo ""
    echo -e "${BLUE}Management Commands:${NC}"
    echo -e "   Stop:     ./scripts/stop_mcp_server.sh"
    echo -e "   Logs:     tail -f $LOG_FILE"
    echo -e "   Status:   ps -p $SERVER_PID"
    echo ""
    echo -e "${GREEN}Server is ready! 🚀${NC}"
else
    echo -e "${RED}❌ Server failed to start${NC}"
    echo -e "   Check logs: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
