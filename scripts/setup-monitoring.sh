#!/bin/bash
# NBA MCP Secrets Monitoring Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root"
   exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log "Setting up NBA MCP Secrets Monitoring..."

# 1. Install systemd service
log "Installing systemd service..."
sudo cp "$SCRIPT_DIR/nba-secrets-monitor.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nba-secrets-monitor.service

# 2. Create monitoring directory
MONITOR_DIR="$HOME/.nba-mcp-monitoring"
log "Creating monitoring directory: $MONITOR_DIR"
mkdir -p "$MONITOR_DIR"/{logs,alerts,reports}

# 3. Create monitoring configuration
log "Creating monitoring configuration..."
cat > "$MONITOR_DIR/config.json" << EOF
{
    "monitoring": {
        "interval_seconds": 300,
        "alert_threshold_percent": 80,
        "retry_attempts": 3,
        "retry_delay_seconds": 30
    },
    "alerts": {
        "slack_webhook": "",
        "email": "",
        "enabled": false
    },
    "projects": [
        {
            "name": "nba-mcp-synthesis",
            "context": "WORKFLOW",
            "enabled": true
        },
        {
            "name": "nba-simulator-aws",
            "context": "DEVELOPMENT",
            "enabled": true
        },
        {
            "name": "nba_mcp_synthesis_global",
            "context": "WORKFLOW",
            "enabled": true
        }
    ]
}
EOF

# 4. Create monitoring script
log "Creating monitoring script..."
cat > "$MONITOR_DIR/monitor.sh" << 'EOF'
#!/bin/bash
# NBA MCP Secrets Monitoring Script

MONITOR_DIR="$HOME/.nba-mcp-monitoring"
PROJECT_ROOT="/Users/ryanranft/nba-mcp-synthesis"
LOG_FILE="$MONITOR_DIR/logs/monitor-$(date +%Y%m%d).log"

# Load configuration
CONFIG_FILE="$MONITOR_DIR/config.json"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Parse configuration
INTERVAL=$(jq -r '.monitoring.interval_seconds' "$CONFIG_FILE")
THRESHOLD=$(jq -r '.monitoring.alert_threshold_percent' "$CONFIG_FILE")
ALERTS_ENABLED=$(jq -r '.alerts.enabled' "$CONFIG_FILE")

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Run health check for a project
check_project() {
    local project="$1"
    local context="$2"

    log "Checking project: $project ($context)"

    # Run health monitor
    cd "$PROJECT_ROOT"
    python3 mcp_server/secrets_health_monitor.py --project "$project" --context "$context" --once >> "$LOG_FILE" 2>&1

    # Check if health score is below threshold
    local health_score=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from mcp_server.secrets_health_monitor import SecretsHealthMonitor
monitor = SecretsHealthMonitor('$project', '$context')
monitor._load_secrets()
status = monitor.get_health_status()
print(status.get('overall_health_score', 0))
" 2>/dev/null || echo "0")

    if (( $(echo "$health_score < $THRESHOLD" | bc -l) )); then
        log "ALERT: Health score for $project is $health_score% (below threshold of $THRESHOLD%)"

        if [[ "$ALERTS_ENABLED" == "true" ]]; then
            # Send alert (implement based on your alerting system)
            log "Sending alert for $project..."
        fi
    else
        log "OK: Health score for $project is $health_score%"
    fi
}

# Main monitoring loop
log "Starting NBA MCP Secrets Monitoring..."
log "Interval: $INTERVAL seconds"
log "Alert threshold: $THRESHOLD%"

while true; do
    # Check each enabled project
    jq -r '.projects[] | select(.enabled == true) | "\(.name) \(.context)"' "$CONFIG_FILE" | while read -r project context; do
        check_project "$project" "$context"
    done

    log "Sleeping for $INTERVAL seconds..."
    sleep "$INTERVAL"
done
EOF

chmod +x "$MONITOR_DIR/monitor.sh"

# 5. Create startup script
log "Creating startup script..."
cat > "$MONITOR_DIR/start-monitoring.sh" << EOF
#!/bin/bash
# Start NBA MCP Secrets Monitoring

MONITOR_DIR="$MONITOR_DIR"
PROJECT_ROOT="$PROJECT_ROOT"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] \$1"
}

log "Starting NBA MCP Secrets Monitoring..."

# Start systemd service
sudo systemctl start nba-secrets-monitor.service
sudo systemctl status nba-secrets-monitor.service

log "Monitoring started. Check status with: sudo systemctl status nba-secrets-monitor"
log "View logs with: journalctl -u nba-secrets-monitor -f"
EOF

chmod +x "$MONITOR_DIR/start-monitoring.sh"

# 6. Create stop script
log "Creating stop script..."
cat > "$MONITOR_DIR/stop-monitoring.sh" << EOF
#!/bin/bash
# Stop NBA MCP Secrets Monitoring

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] \$1"
}

log "Stopping NBA MCP Secrets Monitoring..."

# Stop systemd service
sudo systemctl stop nba-secrets-monitor.service

log "Monitoring stopped."
EOF

chmod +x "$MONITOR_DIR/stop-monitoring.sh"

# 7. Test the setup
log "Testing monitoring setup..."

# Test health monitor
cd "$PROJECT_ROOT"
if python3 mcp_server/secrets_health_monitor.py --project nba-mcp-synthesis --context WORKFLOW --once; then
    log "✅ Health monitor test passed"
else
    log_warn "⚠️  Health monitor test failed"
fi

# 8. Display summary
log "✅ NBA MCP Secrets Monitoring setup complete!"
echo ""
echo "📁 Monitoring directory: $MONITOR_DIR"
echo "🔧 Configuration: $MONITOR_DIR/config.json"
echo "📊 Logs: $MONITOR_DIR/logs/"
echo "🚨 Alerts: $MONITOR_DIR/alerts/"
echo ""
echo "🚀 To start monitoring:"
echo "   $MONITOR_DIR/start-monitoring.sh"
echo ""
echo "🛑 To stop monitoring:"
echo "   $MONITOR_DIR/stop-monitoring.sh"
echo ""
echo "📋 To check status:"
echo "   sudo systemctl status nba-secrets-monitor"
echo ""
echo "📜 To view logs:"
echo "   journalctl -u nba-secrets-monitor -f"
echo ""
echo "⚙️  To configure alerts, edit: $MONITOR_DIR/config.json"


