#!/bin/bash
# Simple terminal dashboard

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

clear
echo "==========================================="
echo "   NBA MCP Synthesis - System Dashboard   "
echo "==========================================="
echo ""

# Server status
echo "🖥️  Server Status"
if [ -f "$PROJECT_DIR/.mcp_server.pid" ]; then
    PID=$(cat "$PROJECT_DIR/.mcp_server.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "  Status: ✅ Running (PID: $PID)"
    else
        echo "  Status: ❌ Stopped"
    fi
else
    echo "  Status: ⚠️  Not Started"
fi

# Disk usage
echo ""
echo "💾 Disk Usage"
df -h "$PROJECT_DIR" | tail -1 | awk '{print "  " $5 " used (" $3 " / " $2 ")"}'

# Recent activity
echo ""
echo "📊 Recent Activity (last hour)"
if [ -d "$PROJECT_DIR/logs" ]; then
    RECENT_ERRORS=$(find "$PROJECT_DIR/logs" -type f -mmin -60 -exec grep -i "error" {} \; 2>/dev/null | wc -l)
    echo "  Errors: $RECENT_ERRORS"
else
    echo "  No logs found"
fi

# Latest metrics
echo ""
echo "📈 Latest Metrics"
LATEST_METRICS=$(ls -t "$PROJECT_DIR/monitoring"/metrics_*.json 2>/dev/null | head -1)
if [ -n "$LATEST_METRICS" ]; then
    echo "  File: $(basename $LATEST_METRICS)"
    cat "$LATEST_METRICS" | python3 -m json.tool 2>/dev/null | grep -E "(total|error_rate|cost)" | head -5
else
    echo "  No metrics collected yet"
fi

echo ""
echo "==========================================="
echo "  Press Ctrl+C to exit | Run: ./monitoring/collect_metrics.sh"
echo "==========================================="
