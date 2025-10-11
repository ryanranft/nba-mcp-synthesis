#!/usr/bin/env bash
#
# context_dashboard.sh - Visual dashboard for context usage metrics
#
# Purpose: Provide at-a-glance overview of context optimization status
# Usage: ./scripts/context_dashboard.sh [--detailed] [--export=FILE]
#
# Displays:
#   - Current context usage vs targets
#   - File size distribution
#   - Recent trends
#   - Health status indicators

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BASELINE_FILE="${PROJECT_ROOT}/.ai/monitoring/baselines.json"
DETAILED=0
EXPORT_FILE=""

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --detailed|-d)
            DETAILED=1
            shift
            ;;
        --export=*)
            EXPORT_FILE="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--detailed] [--export=FILE]"
            echo ""
            echo "Options:"
            echo "  --detailed, -d    Show detailed statistics"
            echo "  --export=FILE     Export metrics to JSON file"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to estimate tokens from lines (rough estimate: 1 line ≈ 20 tokens)
estimate_tokens() {
    local lines=$1
    echo $((lines * 20))
}

# Function to create progress bar
progress_bar() {
    local current=$1
    local target=$2
    local width=40
    local percentage=$((current * 100 / target))
    local filled=$((width * current / target))

    # Determine color based on percentage
    local color=$GREEN
    if [[ $percentage -gt 80 ]]; then
        color=$RED
    elif [[ $percentage -gt 60 ]]; then
        color=$YELLOW
    fi

    echo -n -e "${color}"
    printf '['
    printf '%*s' "$filled" '' | tr ' ' '█'
    printf '%*s' "$((width - filled))" '' | tr ' ' '░'
    printf ']'
    echo -n -e "${NC}"
    printf ' %3d%%' "$percentage"
}

# Function to get file counts by category
get_file_stats() {
    local category=$1
    local pattern=$2
    local count=$(find "$PROJECT_ROOT" -type f -path "$pattern" 2>/dev/null | wc -l | tr -d ' ')
    local total_lines=0

    while IFS= read -r -d '' file; do
        local lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        total_lines=$((total_lines + lines))
    done < <(find "$PROJECT_ROOT" -type f -path "$pattern" -print0 2>/dev/null || true)

    echo "$count:$total_lines"
}

# Function to calculate trend
calculate_trend() {
    local current=$1
    local baseline=$2

    if [[ $baseline -eq 0 ]]; then
        echo "N/A"
        return
    fi

    local diff=$((current - baseline))
    local percent=$((diff * 100 / baseline))

    if [[ $percent -gt 0 ]]; then
        echo -e "${RED}↑ +${percent}%${NC}"
    elif [[ $percent -lt 0 ]]; then
        echo -e "${GREEN}↓ ${percent}%${NC}"
    else
        echo -e "${BLUE}→ 0%${NC}"
    fi
}

# Header
clear
echo -e "${BOLD}${CYAN}=====================================================${NC}"
echo -e "${BOLD}${CYAN}     Context Optimization Dashboard${NC}"
echo -e "${BOLD}${CYAN}=====================================================${NC}"
echo ""
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ============================================================================
# Section 1: Context Budget Overview
# ============================================================================
echo -e "${BOLD}${BLUE}📊 Context Budget Overview${NC}"
echo "─────────────────────────────────────────────────────"
echo ""

# Calculate current session context cost
SESSION_START_LINES=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md" 2>/dev/null || echo "0")
SESSION_START_TOKENS=$(estimate_tokens $SESSION_START_LINES)
SESSION_START_TARGET=300

STATUS_CHECK_LINES=$(wc -l < "$PROJECT_ROOT/PROJECT_STATUS.md" 2>/dev/null || echo "0")
STATUS_CHECK_TOKENS=$(estimate_tokens $STATUS_CHECK_LINES)
STATUS_CHECK_TARGET=150

TOOL_LOOKUP_LINES=$(wc -l < "$PROJECT_ROOT/.ai/permanent/tool-registry.md" 2>/dev/null || echo "0")
TOOL_LOOKUP_TOKENS=$(estimate_tokens $TOOL_LOOKUP_LINES)
TOOL_LOOKUP_TARGET=100

echo -e "${BOLD}Session Start${NC} (current-session.md)"
echo -n "  Target: ${SESSION_START_TARGET} tokens | Current: ${SESSION_START_TOKENS} tokens "
progress_bar $SESSION_START_TOKENS $SESSION_START_TARGET
echo ""
echo ""

echo -e "${BOLD}Status Check${NC} (PROJECT_STATUS.md)"
echo -n "  Target: ${STATUS_CHECK_TARGET} tokens | Current: ${STATUS_CHECK_TOKENS} tokens "
progress_bar $STATUS_CHECK_TOKENS $STATUS_CHECK_TARGET
echo ""
echo ""

echo -e "${BOLD}Tool Lookup${NC} (tool-registry.md)"
echo -n "  Target: ${TOOL_LOOKUP_TARGET} tokens | Current: ${TOOL_LOOKUP_TOKENS} tokens "
progress_bar $TOOL_LOOKUP_TOKENS $TOOL_LOOKUP_TARGET
echo ""
echo ""

# Overall session budget
OVERALL_CURRENT=$((SESSION_START_TOKENS + STATUS_CHECK_TOKENS + TOOL_LOOKUP_TOKENS))
OVERALL_TARGET=550
echo -e "${BOLD}Overall Session Budget${NC}"
echo -n "  Target: ${OVERALL_TARGET} tokens | Current: ${OVERALL_CURRENT} tokens "
progress_bar $OVERALL_CURRENT $OVERALL_TARGET
echo ""
echo ""

# ============================================================================
# Section 2: File Size Distribution
# ============================================================================
echo -e "${BOLD}${BLUE}📁 File Size Distribution${NC}"
echo "─────────────────────────────────────────────────────"
echo ""

# Get stats for different categories
INDEX_STATS=$(get_file_stats "Index Files" "*/index.md")
INDEX_COUNT=$(echo "$INDEX_STATS" | cut -d: -f1)
INDEX_LINES=$(echo "$INDEX_STATS" | cut -d: -f2)

STATUS_STATS=$(get_file_stats "Status Files" "*/status/*.md")
STATUS_COUNT=$(echo "$STATUS_STATS" | cut -d: -f1)
STATUS_LINES=$(echo "$STATUS_STATS" | cut -d: -f2)

GUIDE_STATS=$(get_file_stats "Guide Files" "*/guides/*.md")
GUIDE_COUNT=$(echo "$GUIDE_STATS" | cut -d: -f1)
GUIDE_LINES=$(echo "$GUIDE_STATS" | cut -d: -f2)

DAILY_STATS=$(get_file_stats "Daily Sessions" "*/.ai/daily/*.md")
DAILY_COUNT=$(echo "$DAILY_STATS" | cut -d: -f1)
DAILY_LINES=$(echo "$DAILY_STATS" | cut -d: -f2)

printf "%-20s %10s %15s %15s\n" "Category" "Count" "Total Lines" "Avg Lines/File"
printf "%-20s %10s %15s %15s\n" "────────────────────" "─────" "───────────" "──────────────"

if [[ $INDEX_COUNT -gt 0 ]]; then
    printf "%-20s %10d %15d %15d\n" "Index Files" "$INDEX_COUNT" "$INDEX_LINES" $((INDEX_LINES / INDEX_COUNT))
else
    printf "%-20s %10d %15d %15s\n" "Index Files" "0" "0" "N/A"
fi

if [[ $STATUS_COUNT -gt 0 ]]; then
    printf "%-20s %10d %15d %15d\n" "Status Files" "$STATUS_COUNT" "$STATUS_LINES" $((STATUS_LINES / STATUS_COUNT))
else
    printf "%-20s %10d %15d %15s\n" "Status Files" "0" "0" "N/A"
fi

if [[ $GUIDE_COUNT -gt 0 ]]; then
    printf "%-20s %10d %15d %15d\n" "Guide Files" "$GUIDE_COUNT" "$GUIDE_LINES" $((GUIDE_LINES / GUIDE_COUNT))
else
    printf "%-20s %10d %15d %15s\n" "Guide Files" "0" "0" "N/A"
fi

if [[ $DAILY_COUNT -gt 0 ]]; then
    printf "%-20s %10d %15d %15d\n" "Daily Sessions" "$DAILY_COUNT" "$DAILY_LINES" $((DAILY_LINES / DAILY_COUNT))
else
    printf "%-20s %10d %15d %15s\n" "Daily Sessions" "0" "0" "N/A"
fi

echo ""

# ============================================================================
# Section 3: Health Indicators
# ============================================================================
echo -e "${BOLD}${BLUE}🏥 Health Indicators${NC}"
echo "─────────────────────────────────────────────────────"
echo ""

# Run silent file size check to get counts
ERROR_COUNT=0
WARNING_COUNT=0
if [[ -x "$SCRIPT_DIR/monitor_file_sizes.sh" ]]; then
    # Run and capture exit code
    set +e
    "$SCRIPT_DIR/monitor_file_sizes.sh" > /tmp/monitor_output.txt 2>&1
    EXIT_CODE=$?
    set -e

    # Parse output for counts
    ERROR_COUNT=$(grep -c "^ERROR:" /tmp/monitor_output.txt 2>/dev/null || echo "0")
    WARNING_COUNT=$(grep -c "^WARNING:" /tmp/monitor_output.txt 2>/dev/null || echo "0")
    rm -f /tmp/monitor_output.txt
fi

# Display health indicators
if [[ $ERROR_COUNT -eq 0 && $WARNING_COUNT -eq 0 ]]; then
    echo -e "  File Sizes:      ${GREEN}✓ All within limits${NC}"
else
    if [[ $ERROR_COUNT -gt 0 ]]; then
        echo -e "  File Sizes:      ${RED}✗ $ERROR_COUNT file(s) exceed limits${NC}"
    else
        echo -e "  File Sizes:      ${YELLOW}⚠ $WARNING_COUNT file(s) approaching limits${NC}"
    fi
fi

# Check session system
if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
    echo -e "  Session System:  ${GREEN}✓ Active${NC}"
else
    echo -e "  Session System:  ${RED}✗ Not initialized${NC}"
fi

# Check git status
if git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "  Git Repository:  ${GREEN}✓ Active${NC}"
else
    echo -e "  Git Repository:  ${RED}✗ Not a git repository${NC}"
fi

# Check documentation map
if [[ -f "$PROJECT_ROOT/docs/DOCUMENTATION_MAP.md" ]]; then
    echo -e "  Documentation:   ${GREEN}✓ Map available${NC}"
else
    echo -e "  Documentation:   ${YELLOW}⚠ No documentation map${NC}"
fi

echo ""

# ============================================================================
# Section 4: Archive Metrics
# ============================================================================
echo -e "${BOLD}${BLUE}📦 Archive Metrics${NC}"
echo "─────────────────────────────────────────────────────"
echo ""

# Count markdown files in root
ROOT_MD_COUNT=$(ls -1 "$PROJECT_ROOT"/*.md 2>/dev/null | wc -l | tr -d ' ')
ROOT_MD_TARGET=15
if [[ $ROOT_MD_COUNT -le $ROOT_MD_TARGET ]]; then
    echo -e "  Root Files:      ${GREEN}✓ ${ROOT_MD_COUNT} files (target: <$ROOT_MD_TARGET)${NC}"
elif [[ $ROOT_MD_COUNT -le 20 ]]; then
    echo -e "  Root Files:      ${YELLOW}⚠ ${ROOT_MD_COUNT} files (target: <$ROOT_MD_TARGET)${NC}"
else
    echo -e "  Root Files:      ${RED}✗ ${ROOT_MD_COUNT} files (max: 20)${NC}"
fi

# Count completion documents in root
COMPLETION_DOCS=$(find "$PROJECT_ROOT" -maxdepth 1 -type f \( -name "*_COMPLETE.md" -o -name "*_VERIFICATION*.md" -o -name "*_REPORT.md" \) 2>/dev/null | wc -l | tr -d ' ')
if [[ $COMPLETION_DOCS -eq 0 ]]; then
    echo -e "  Completion Docs: ${GREEN}✓ 0 in root (all archived)${NC}"
else
    echo -e "  Completion Docs: ${YELLOW}⚠ ${COMPLETION_DOCS} in root (archive needed)${NC}"
fi

# Count archived files
ARCHIVED_COUNT=$(find "$PROJECT_ROOT/docs/archive" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo -e "  Archived Files:  ${BLUE}📁 ${ARCHIVED_COUNT} files in archive${NC}"

# Count daily sessions
DAILY_SESSION_COUNT=$(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" 2>/dev/null | wc -l | tr -d ' ')
if [[ $DAILY_SESSION_COUNT -le 7 ]]; then
    echo -e "  Daily Sessions:  ${GREEN}✓ ${DAILY_SESSION_COUNT} files (within weekly limit)${NC}"
elif [[ $DAILY_SESSION_COUNT -le 14 ]]; then
    echo -e "  Daily Sessions:  ${YELLOW}⚠ ${DAILY_SESSION_COUNT} files (consider archiving)${NC}"
else
    echo -e "  Daily Sessions:  ${RED}✗ ${DAILY_SESSION_COUNT} files (archive needed)${NC}"
fi

# Estimate archivable content and token savings
ARCHIVABLE_LINES=0
if [[ $COMPLETION_DOCS -gt 0 || $DAILY_SESSION_COUNT -gt 7 ]]; then
    # Count lines in completion docs
    for file in $(find "$PROJECT_ROOT" -maxdepth 1 -type f \( -name "*_COMPLETE.md" -o -name "*_VERIFICATION*.md" -o -name "*_REPORT.md" \) 2>/dev/null); do
        if [[ -f "$file" ]]; then
            FILE_LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
            ARCHIVABLE_LINES=$((ARCHIVABLE_LINES + FILE_LINES))
        fi
    done
    
    # Count lines in old daily sessions (beyond 7 days)
    if [[ $DAILY_SESSION_COUNT -gt 7 ]]; then
        for file in $(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" -mtime +7 2>/dev/null); do
            if [[ -f "$file" ]]; then
                FILE_LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
                ARCHIVABLE_LINES=$((ARCHIVABLE_LINES + FILE_LINES))
            fi
        done
    fi
    
    ESTIMATED_SAVINGS=$(estimate_tokens $ARCHIVABLE_LINES)
    echo -e "  ${CYAN}💾 Potential savings: ~${ESTIMATED_SAVINGS} tokens (${ARCHIVABLE_LINES} lines)${NC}"
    echo -e "  ${CYAN}   Run: ./scripts/auto_archive.sh --dry-run${NC}"
fi

echo ""

# ============================================================================
# Section 5: Recommendations
# ============================================================================
echo -e "${BOLD}${BLUE}💡 Recommendations${NC}"
echo "─────────────────────────────────────────────────────"
echo ""

RECOMMENDATIONS=()

# Check session start budget
if [[ $SESSION_START_TOKENS -gt $SESSION_START_TARGET ]]; then
    RECOMMENDATIONS+=("• Reduce current-session.md size (currently ${SESSION_START_LINES} lines)")
fi

# Check status check budget
if [[ $STATUS_CHECK_TOKENS -gt $STATUS_CHECK_TARGET ]]; then
    RECOMMENDATIONS+=("• Refactor PROJECT_STATUS.md to use more cross-references")
fi

# Check file size issues
if [[ $ERROR_COUNT -gt 0 ]]; then
    RECOMMENDATIONS+=("• Run: ./scripts/monitor_file_sizes.sh to see files exceeding limits")
fi

if [[ $WARNING_COUNT -gt 0 ]]; then
    RECOMMENDATIONS+=("• Consider proactive refactoring of files approaching limits")
fi

# Check daily session accumulation
if [[ $DAILY_COUNT -gt 7 ]]; then
    RECOMMENDATIONS+=("• Archive old daily sessions (${DAILY_COUNT} currently active)")
fi

# Check root directory file count
if [[ $ROOT_MD_COUNT -gt 20 ]]; then
    RECOMMENDATIONS+=("• CRITICAL: Root has ${ROOT_MD_COUNT} files - Run: ./scripts/auto_archive.sh")
elif [[ $ROOT_MD_COUNT -gt 15 ]]; then
    RECOMMENDATIONS+=("• Root directory has ${ROOT_MD_COUNT} files - Consider archiving")
fi

# Check for completion documents
if [[ $COMPLETION_DOCS -gt 0 ]]; then
    RECOMMENDATIONS+=("• Archive ${COMPLETION_DOCS} completion document(s) from root")
fi

# Check daily sessions for archiving
if [[ $DAILY_SESSION_COUNT -gt 14 ]]; then
    RECOMMENDATIONS+=("• ${DAILY_SESSION_COUNT} daily sessions - Run: ./scripts/session_archive.sh")
elif [[ $DAILY_SESSION_COUNT -gt 7 ]]; then
    RECOMMENDATIONS+=("• Consider archiving ${DAILY_SESSION_COUNT} daily sessions")
fi

# Show archiving opportunity if exists
if [[ $ARCHIVABLE_LINES -gt 0 ]]; then
    RECOMMENDATIONS+=("• Archive opportunity: ~${ESTIMATED_SAVINGS} token savings available")
fi

if [[ ${#RECOMMENDATIONS[@]} -eq 0 ]]; then
    echo -e "${GREEN}All systems operating within optimal parameters${NC}"
else
    for rec in "${RECOMMENDATIONS[@]}"; do
        echo "$rec"
    done
fi

echo ""

# ============================================================================
# Section 5: Quick Actions
# ============================================================================
echo -e "${BOLD}${BLUE}⚡ Quick Actions${NC}"
echo "─────────────────────────────────────────────────────"
echo ""
echo "  Monitor files:    ./scripts/monitor_file_sizes.sh"
echo "  Archive docs:     ./scripts/auto_archive.sh --dry-run"
echo "  Archive sessions: ./scripts/session_archive.sh"
echo "  Health check:     ./scripts/session_start.sh --health-check"
echo "  Weekly check:     ./scripts/weekly_health_check.sh"
echo "  Update status:    ./scripts/update_status.sh"
echo ""

# ============================================================================
# Export to JSON (if requested)
# ============================================================================
if [[ -n "$EXPORT_FILE" ]]; then
    cat > "$EXPORT_FILE" <<EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "context_budget": {
    "session_start": {
      "target": $SESSION_START_TARGET,
      "current": $SESSION_START_TOKENS,
      "percentage": $((SESSION_START_TOKENS * 100 / SESSION_START_TARGET))
    },
    "status_check": {
      "target": $STATUS_CHECK_TARGET,
      "current": $STATUS_CHECK_TOKENS,
      "percentage": $((STATUS_CHECK_TOKENS * 100 / STATUS_CHECK_TARGET))
    },
    "tool_lookup": {
      "target": $TOOL_LOOKUP_TARGET,
      "current": $TOOL_LOOKUP_TOKENS,
      "percentage": $((TOOL_LOOKUP_TOKENS * 100 / TOOL_LOOKUP_TARGET))
    },
    "overall": {
      "target": $OVERALL_TARGET,
      "current": $OVERALL_CURRENT,
      "percentage": $((OVERALL_CURRENT * 100 / OVERALL_TARGET))
    }
  },
  "file_distribution": {
    "index_files": {"count": $INDEX_COUNT, "total_lines": $INDEX_LINES},
    "status_files": {"count": $STATUS_COUNT, "total_lines": $STATUS_LINES},
    "guide_files": {"count": $GUIDE_COUNT, "total_lines": $GUIDE_LINES},
    "daily_sessions": {"count": $DAILY_COUNT, "total_lines": $DAILY_LINES}
  },
  "health": {
    "file_size_errors": $ERROR_COUNT,
    "file_size_warnings": $WARNING_COUNT,
    "session_system_active": $([ -f "$PROJECT_ROOT/.ai/current-session.md" ] && echo "true" || echo "false"),
    "git_repository_active": $(git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1 && echo "true" || echo "false")
  },
  "recommendations_count": ${#RECOMMENDATIONS[@]}
}
EOF
    echo -e "${GREEN}✓ Metrics exported to: $EXPORT_FILE${NC}"
    echo ""
fi

# Footer
echo -e "${BOLD}${CYAN}=====================================================${NC}"
echo ""
