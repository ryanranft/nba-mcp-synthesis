#!/bin/bash
#
# Progress Log Rotation Script
#
# Purpose: Rotate progress.log monthly to prevent unbounded growth
# Usage: ./scripts/rotate_progress_log.sh [--keep-days=30]
# Frequency: Run monthly (or add to cron)
#

set -e

# Configuration
MONTH=$(date +%Y-%m)
LOG_FILE="project/tracking/progress.log"
ARCHIVE_FILE=".ai/monthly/${MONTH}-progress.log"
DEFAULT_KEEP_DAYS=30
KEEP_DAYS=${1#--keep-days=}
KEEP_DAYS=${KEEP_DAYS:-$DEFAULT_KEEP_DAYS}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Progress Log Rotation${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠️  No progress log found at: $LOG_FILE${NC}"
    echo "Nothing to rotate."
    exit 0
fi

# Get log file stats
LINE_COUNT=$(wc -l < "$LOG_FILE")
FILE_SIZE=$(du -h "$LOG_FILE" | cut -f1)

echo "Current log stats:"
echo "  Lines: $LINE_COUNT"
echo "  Size: $FILE_SIZE"
echo "  Keep last: $KEEP_DAYS days"
echo ""

# Check if rotation needed
if [ "$LINE_COUNT" -lt 50 ]; then
    echo -e "${GREEN}✓${NC} Log file is small ($LINE_COUNT lines), no rotation needed."
    exit 0
fi

# Create archive directory if needed
mkdir -p .ai/monthly

# Copy to archive
echo -e "${BLUE}→${NC} Archiving full log to: $ARCHIVE_FILE"
cp "$LOG_FILE" "$ARCHIVE_FILE"
echo -e "${GREEN}✓${NC} Full log archived"

# Calculate cutoff date
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CUTOFF_DATE=$(date -v-${KEEP_DAYS}d +%Y-%m-%d)
else
    # Linux
    CUTOFF_DATE=$(date -d "$KEEP_DAYS days ago" +%Y-%m-%d)
fi

echo ""
echo -e "${BLUE}→${NC} Rotating log (keeping entries since $CUTOFF_DATE)"

# Keep only recent entries
awk -v cutoff="$CUTOFF_DATE" '$0 >= cutoff' "$LOG_FILE" > "${LOG_FILE}.tmp"

# Check if we got any lines
NEW_LINE_COUNT=$(wc -l < "${LOG_FILE}.tmp")

if [ "$NEW_LINE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No entries found after $CUTOFF_DATE${NC}"
    echo "Keeping original log file."
    rm "${LOG_FILE}.tmp"
    exit 0
fi

# Replace log with rotated version
mv "${LOG_FILE}.tmp" "$LOG_FILE"

echo -e "${GREEN}✓${NC} Log rotated"
echo ""

# Show results
NEW_FILE_SIZE=$(du -h "$LOG_FILE" | cut -f1)
LINES_REMOVED=$((LINE_COUNT - NEW_LINE_COUNT))

echo "======================================="
echo -e "${GREEN}✅ Rotation Complete${NC}"
echo "======================================="
echo ""
echo "Results:"
echo "  Original lines: $LINE_COUNT"
echo "  New lines: $NEW_LINE_COUNT"
echo "  Lines removed: $LINES_REMOVED"
echo "  Original size: $FILE_SIZE"
echo "  New size: $NEW_FILE_SIZE"
echo ""
echo "Archive location: $ARCHIVE_FILE"
echo ""
echo "Next steps:"
echo "  1. Verify rotated log: head -5 $LOG_FILE"
echo "  2. Check archive: ls -lh .ai/monthly/"
echo "  3. Commit changes: git add $LOG_FILE .ai/monthly/"
echo ""

# Optional: Add to weekly health check
if [ ! -f "scripts/weekly_health_check.sh" ]; then
    echo "Tip: Add this to weekly_health_check.sh:"
    echo "  ./scripts/rotate_progress_log.sh"
fi

