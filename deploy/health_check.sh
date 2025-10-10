#!/bin/bash
#
# NBA MCP Synthesis - System Health Check
#

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "========================================="
echo "NBA MCP Synthesis - Health Check"
echo "========================================="
echo ""

# Check MCP server status
echo "[1/4] MCP Server Status"
if [ -f "$PROJECT_DIR/.mcp_server.pid" ]; then
    PID=$(cat "$PROJECT_DIR/.mcp_server.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ MCP server is running (PID: $PID)"
    else
        echo "⚠️  PID file exists but process not running"
    fi
else
    echo "⚠️  MCP server is not running"
fi

# Check disk space
echo ""
echo "[2/4] Disk Space"
df -h "$PROJECT_DIR" | tail -1 | awk '{print "  Used: " $3 " / " $2 " (" $5 ")"}'

# Check log files
echo ""
echo "[3/4] Log Files"
if [ -d "$PROJECT_DIR/logs" ]; then
    LOG_SIZE=$(du -sh "$PROJECT_DIR/logs" | cut -f1)
    LOG_COUNT=$(find "$PROJECT_DIR/logs" -type f | wc -l)
    echo "  Size: $LOG_SIZE"
    echo "  Files: $LOG_COUNT"
    
    # Check for recent errors
    if [ $LOG_COUNT -gt 0 ]; then
        ERROR_COUNT=$(find "$PROJECT_DIR/logs" -type f -exec grep -i "error" {} \; 2>/dev/null | wc -l)
        if [ $ERROR_COUNT -gt 0 ]; then
            echo "  ⚠️  Recent errors found: $ERROR_COUNT"
        else
            echo "  ✅ No errors in logs"
        fi
    fi
else
    echo "  ⚠️  Log directory not found"
fi

# Check Python dependencies
echo ""
echo "[4/4] Python Dependencies"
python3 -c "import boto3, psycopg2, anthropic, mcp" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ All required packages available"
else
    echo "❌ Missing required packages"
fi

echo ""
echo "========================================="
echo "Health check complete"
echo "========================================="

exit 0
