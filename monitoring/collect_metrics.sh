#!/bin/bash
# Collect metrics from logs

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
METRICS_FILE="$PROJECT_DIR/monitoring/metrics_$(date +%Y%m%d_%H%M%S).json"

if [ ! -d "$LOG_DIR" ]; then
    echo "{\"error\": \"Log directory not found\"}" > "$METRICS_FILE"
    exit 1
fi

# Count requests
TOTAL_REQUESTS=$(find "$LOG_DIR" -name "*.log" -exec grep -i "synthesis" {} \; 2>/dev/null | wc -l)
ERROR_COUNT=$(find "$LOG_DIR" -name "*.log" -exec grep -i "error" {} \; 2>/dev/null | wc -l)

# Calculate error rate
if [ $TOTAL_REQUESTS -gt 0 ]; then
    ERROR_RATE=$(echo "scale=4; $ERROR_COUNT / $TOTAL_REQUESTS * 100" | bc)
else
    ERROR_RATE=0
fi

# Extract costs (if logged)
TOTAL_COST=$(find "$LOG_DIR" -name "*.log" -exec grep -oP "cost.*?\K[0-9]+\.[0-9]+" {} \; 2>/dev/null | awk '{s+=$1} END {print s}')
TOTAL_COST=${TOTAL_COST:-0}

# Create JSON metrics
cat > "$METRICS_FILE" << EOFM
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "requests": {
    "total": $TOTAL_REQUESTS,
    "errors": $ERROR_COUNT,
    "error_rate": $ERROR_RATE
  },
  "cost": {
    "total": ${TOTAL_COST}
  }
}
EOFM

echo "Metrics collected: $METRICS_FILE"
cat "$METRICS_FILE"
