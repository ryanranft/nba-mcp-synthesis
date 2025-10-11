#!/usr/bin/env bash
#
# track_context_budget.sh - Track context token usage against budgets
#
# Purpose: Monitor and report on context budget compliance
# Usage: ./scripts/track_context_budget.sh [--session|--weekly-report|--monthly-report]
#
# Features:
#   - Real-time budget tracking
#   - Historical trend analysis
#   - Budget compliance reporting
#   - Optimization recommendations

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUDGET_CONFIG="${PROJECT_ROOT}/.ai/permanent/context_budget.json"
BASELINE_FILE="${PROJECT_ROOT}/.ai/monitoring/baselines.json"
TRACKING_LOG="${PROJECT_ROOT}/.ai/monitoring/budget_tracking.log"
MODE="session"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --session|-s)
            MODE="session"
            shift
            ;;
        --weekly-report|-w)
            MODE="weekly"
            shift
            ;;
        --monthly-report|-m)
            MODE="monthly"
            shift
            ;;
        --analyze|-a)
            MODE="analyze"
            shift
            ;;
        --recommendations|-r)
            MODE="recommendations"
            shift
            ;;
        --export-history)
            MODE="export"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [MODE]"
            echo ""
            echo "Modes:"
            echo "  --session, -s           Show current session budget status (default)"
            echo "  --weekly-report, -w     Generate weekly budget report"
            echo "  --monthly-report, -m    Generate monthly budget report"
            echo "  --analyze, -a           Analyze budget usage patterns"
            echo "  --recommendations, -r   Generate optimization recommendations"
            echo "  --export-history        Export historical data to CSV"
            echo "  --help, -h              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to estimate tokens from lines
estimate_tokens() {
    local lines=$1
    echo $((lines * 20))
}

# Function to get budget from config
get_budget() {
    local operation=$1

    if [[ ! -f "$BUDGET_CONFIG" ]]; then
        # Default budgets if config doesn't exist
        case "$operation" in
            session_start) echo "300" ;;
            status_check) echo "150" ;;
            tool_lookup) echo "100" ;;
            progress_update) echo "10" ;;
            status_update) echo "50" ;;
            decision_recording) echo "30" ;;
            *) echo "0" ;;
        esac
        return
    fi

    # Extract from JSON (requires jq)
    if command -v jq &> /dev/null; then
        jq -r ".budgets.${operation} // 0" "$BUDGET_CONFIG" 2>/dev/null || echo "0"
    else
        # Fallback defaults
        case "$operation" in
            session_start) echo "300" ;;
            status_check) echo "150" ;;
            tool_lookup) echo "100" ;;
            progress_update) echo "10" ;;
            status_update) echo "50" ;;
            decision_recording) echo "30" ;;
            *) echo "0" ;;
        esac
    fi
}

# Function to calculate status color
get_status_color() {
    local current=$1
    local budget=$2
    local percentage=$((current * 100 / budget))

    if [[ $percentage -le 80 ]]; then
        echo "$GREEN"
    elif [[ $percentage -le 100 ]]; then
        echo "$YELLOW"
    else
        echo "$RED"
    fi
}

# Function to log tracking data
log_tracking() {
    local operation=$1
    local tokens=$2
    local budget=$3

    mkdir -p "$(dirname "$TRACKING_LOG")"
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')|$operation|$tokens|$budget" >> "$TRACKING_LOG"
}

# Mode: Session Budget Status
if [[ "$MODE" == "session" ]]; then
    echo "======================================"
    echo "Current Session Budget Status"
    echo "======================================"
    echo ""
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Core operations
    echo -e "${BOLD}${BLUE}Core Operations${NC}"
    echo "─────────────────────────────────────"
    echo ""

    TOTAL_USED=0
    TOTAL_BUDGET=0

    # Session Start
    if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
        LINES=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md")
        TOKENS=$(estimate_tokens $LINES)
        BUDGET=$(get_budget "session_start")
        TOTAL_USED=$((TOTAL_USED + TOKENS))
        TOTAL_BUDGET=$((TOTAL_BUDGET + BUDGET))

        COLOR=$(get_status_color $TOKENS $BUDGET)
        PERCENTAGE=$((TOKENS * 100 / BUDGET))
        echo -e "Session Start:       ${COLOR}${TOKENS}${NC}/${BUDGET} tokens (${PERCENTAGE}%)"

        log_tracking "session_start" "$TOKENS" "$BUDGET"
    fi

    # Status Check
    if [[ -f "$PROJECT_ROOT/PROJECT_STATUS.md" ]]; then
        LINES=$(wc -l < "$PROJECT_ROOT/PROJECT_STATUS.md")
        TOKENS=$(estimate_tokens $LINES)
        BUDGET=$(get_budget "status_check")
        TOTAL_USED=$((TOTAL_USED + TOKENS))
        TOTAL_BUDGET=$((TOTAL_BUDGET + BUDGET))

        COLOR=$(get_status_color $TOKENS $BUDGET)
        PERCENTAGE=$((TOKENS * 100 / BUDGET))
        echo -e "Status Check:        ${COLOR}${TOKENS}${NC}/${BUDGET} tokens (${PERCENTAGE}%)"

        log_tracking "status_check" "$TOKENS" "$BUDGET"
    fi

    # Tool Lookup
    if [[ -f "$PROJECT_ROOT/.ai/permanent/tool-registry.md" ]]; then
        LINES=$(wc -l < "$PROJECT_ROOT/.ai/permanent/tool-registry.md")
        TOKENS=$(estimate_tokens $LINES)
        BUDGET=$(get_budget "tool_lookup")
        TOTAL_USED=$((TOTAL_USED + TOKENS))
        TOTAL_BUDGET=$((TOTAL_BUDGET + BUDGET))

        COLOR=$(get_status_color $TOKENS $BUDGET)
        PERCENTAGE=$((TOKENS * 100 / BUDGET))
        echo -e "Tool Lookup:         ${COLOR}${TOKENS}${NC}/${BUDGET} tokens (${PERCENTAGE}%)"

        log_tracking "tool_lookup" "$TOKENS" "$BUDGET"
    fi

    echo ""
    echo "─────────────────────────────────────"

    OVERALL_COLOR=$(get_status_color $TOTAL_USED $TOTAL_BUDGET)
    OVERALL_PERCENTAGE=$((TOTAL_USED * 100 / TOTAL_BUDGET))
    echo -e "Core Total:          ${OVERALL_COLOR}${TOTAL_USED}${NC}/${TOTAL_BUDGET} tokens (${OVERALL_PERCENTAGE}%)"
    echo ""

    # Session budget estimate
    SESSION_BUDGET=10000  # 10K target
    REMAINING=$((SESSION_BUDGET - TOTAL_USED))

    echo -e "${BOLD}${BLUE}Session Budget${NC}"
    echo "─────────────────────────────────────"
    echo ""
    echo "Target:              10,000 tokens"
    echo -e "Used (core ops):     ${OVERALL_COLOR}${TOTAL_USED}${NC} tokens"
    echo "Remaining:           ${REMAINING} tokens"
    echo ""

    # Recommendations
    if [[ $TOTAL_USED -gt $((TOTAL_BUDGET * 120 / 100)) ]]; then
        echo -e "${RED}⚠ WARNING: Core operations exceed budget${NC}"
        echo ""
        echo "Recommended actions:"
        echo "  1. Regenerate current-session.md: ./scripts/session_start.sh"
        echo "  2. Check file sizes: ./scripts/monitor_file_sizes.sh"
        echo "  3. Review optimization guide: docs/guides/CONTEXT_BUDGET_GUIDE.md"
        echo ""
    elif [[ $TOTAL_USED -gt $((TOTAL_BUDGET * 80 / 100)) ]]; then
        echo -e "${YELLOW}⚠ NOTICE: Approaching budget limits${NC}"
        echo ""
        echo "Consider:"
        echo "  - Review dashboard: ./scripts/context_dashboard.sh"
        echo "  - Optimize files nearing limits"
        echo ""
    else
        echo -e "${GREEN}✓ Budget status: Healthy${NC}"
        echo ""
    fi

fi

# Mode: Weekly Report
if [[ "$MODE" == "weekly" ]]; then
    echo "======================================"
    echo "Weekly Budget Report"
    echo "======================================"
    echo ""
    echo "Period: Last 7 days"
    echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    if [[ ! -f "$TRACKING_LOG" ]]; then
        echo -e "${YELLOW}No tracking data available yet${NC}"
        echo ""
        echo "Run: $0 --session"
        echo "This will start collecting data for future reports"
        exit 0
    fi

    # Calculate date 7 days ago
    if [[ "$OSTYPE" == "darwin"* ]]; then
        WEEK_AGO=$(date -v-7d '+%Y-%m-%d')
    else
        WEEK_AGO=$(date -d '7 days ago' '+%Y-%m-%d')
    fi

    # Analyze tracking log for last 7 days
    echo -e "${BOLD}${BLUE}Average Token Usage (Last 7 Days)${NC}"
    echo "─────────────────────────────────────"
    echo ""

    # Parse log and calculate averages
    declare -A op_totals
    declare -A op_counts

    while IFS='|' read -r timestamp operation tokens budget; do
        # Check if within last 7 days
        log_date=$(echo "$timestamp" | cut -d'T' -f1)
        if [[ "$log_date" > "$WEEK_AGO" ]] || [[ "$log_date" == "$WEEK_AGO" ]]; then
            if [[ -n "${op_totals[$operation]}" ]]; then
                op_totals[$operation]=$((${op_totals[$operation]} + tokens))
                op_counts[$operation]=$((${op_counts[$operation]} + 1))
            else
                op_totals[$operation]=$tokens
                op_counts[$operation]=1
            fi
        fi
    done < "$TRACKING_LOG"

    # Display averages
    for operation in "${!op_totals[@]}"; do
        avg=$((${op_totals[$operation]} / ${op_counts[$operation]}))
        count=${op_counts[$operation]}
        budget=$(get_budget "$operation")
        percentage=$((avg * 100 / budget))

        color=$(get_status_color $avg $budget)
        printf "%-20s ${color}%6d${NC}/%d tokens (avg, %d samples)\n" "${operation}:" "$avg" "$budget" "$count"
    done

    echo ""

    # Trend analysis
    echo -e "${BOLD}${BLUE}Trend Analysis${NC}"
    echo "─────────────────────────────────────"
    echo ""

    if [[ -f "$BASELINE_FILE" ]] && command -v jq &> /dev/null; then
        BASELINE_SESSION=$(jq -r '.context_budget.session_start.tokens_estimated' "$BASELINE_FILE" 2>/dev/null || echo "0")
        CURRENT_SESSION=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md" 2>/dev/null || echo "0")
        CURRENT_SESSION=$((CURRENT_SESSION * 20))

        if [[ $CURRENT_SESSION -lt $BASELINE_SESSION ]]; then
            IMPROVEMENT=$((BASELINE_SESSION - CURRENT_SESSION))
            echo -e "${GREEN}↓ Improvement${NC}: Session start reduced by ${IMPROVEMENT} tokens"
        elif [[ $CURRENT_SESSION -gt $BASELINE_SESSION ]]; then
            REGRESSION=$((CURRENT_SESSION - BASELINE_SESSION))
            echo -e "${RED}↑ Regression${NC}: Session start increased by ${REGRESSION} tokens"
        else
            echo -e "${BLUE}→ Stable${NC}: No change from baseline"
        fi
    else
        echo "No baseline available for comparison"
        echo "Run: ./scripts/establish_baselines.sh"
    fi

    echo ""
fi

# Mode: Monthly Report
if [[ "$MODE" == "monthly" ]]; then
    echo "======================================"
    echo "Monthly Budget Report"
    echo "======================================"
    echo ""
    echo "Period: Last 30 days"
    echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    if [[ ! -f "$TRACKING_LOG" ]]; then
        echo -e "${YELLOW}No tracking data available yet${NC}"
        exit 0
    fi

    # Calculate date 30 days ago
    if [[ "$OSTYPE" == "darwin"* ]]; then
        MONTH_AGO=$(date -v-30d '+%Y-%m-%d')
    else
        MONTH_AGO=$(date -d '30 days ago' '+%Y-%m-%d')
    fi

    # Similar analysis as weekly but for 30 days
    echo -e "${BOLD}${BLUE}Monthly Statistics${NC}"
    echo "─────────────────────────────────────"
    echo ""

    # Count total tracking entries
    TOTAL_ENTRIES=$(grep -c "^" "$TRACKING_LOG" || echo "0")
    MONTH_ENTRIES=$(awk -F'|' -v cutoff="$MONTH_AGO" '$1 >= cutoff' "$TRACKING_LOG" | wc -l | tr -d ' ')

    echo "Total tracking entries: $TOTAL_ENTRIES"
    echo "Last 30 days: $MONTH_ENTRIES"
    echo ""

    # Calculate savings
    if [[ -f "$BASELINE_FILE" ]] && command -v jq &> /dev/null; then
        BASELINE_TOTAL=$(jq -r '.context_budget.overall.tokens_estimated' "$BASELINE_FILE" 2>/dev/null || echo "0")
        CURRENT_TOTAL=0

        # Calculate current from tracking data
        for operation in session_start status_check tool_lookup; do
            if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
                LINES=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md")
                CURRENT_TOTAL=$((CURRENT_TOTAL + LINES * 20))
                break
            fi
        done

        if [[ $BASELINE_TOTAL -gt 0 && $CURRENT_TOTAL -gt 0 ]]; then
            SAVINGS=$((BASELINE_TOTAL - CURRENT_TOTAL))
            PERCENTAGE=$((SAVINGS * 100 / BASELINE_TOTAL))
            echo -e "${GREEN}Total Savings: ${SAVINGS} tokens (${PERCENTAGE}%)${NC}"
        fi
    fi

    echo ""
fi

# Mode: Analyze
if [[ "$MODE" == "analyze" ]]; then
    echo "======================================"
    echo "Budget Usage Analysis"
    echo "======================================"
    echo ""

    echo "Analyzing patterns in budget usage..."
    echo ""

    # Check common issues
    ISSUES_FOUND=0

    # Issue 1: Large session file
    if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
        LINES=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md")
        if [[ $LINES -gt 80 ]]; then
            echo -e "${YELLOW}⚠${NC} Issue: current-session.md is large ($LINES lines)"
            echo "  Impact: Exceeds session start budget"
            echo "  Fix: Regenerate with ./scripts/session_start.sh"
            echo ""
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    fi

    # Issue 2: Large status file
    if [[ -f "$PROJECT_ROOT/PROJECT_STATUS.md" ]]; then
        LINES=$(wc -l < "$PROJECT_ROOT/PROJECT_STATUS.md")
        if [[ $LINES -gt 150 ]]; then
            echo -e "${YELLOW}⚠${NC} Issue: PROJECT_STATUS.md is large ($LINES lines)"
            echo "  Impact: Exceeds status check budget"
            echo "  Fix: Split into focused files in project/status/"
            echo ""
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    fi

    # Issue 3: Many daily sessions
    DAILY_COUNT=$(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $DAILY_COUNT -gt 7 ]]; then
        echo -e "${YELLOW}⚠${NC} Issue: Too many daily sessions ($DAILY_COUNT files)"
        echo "  Impact: Clutters workspace, slows searches"
        echo "  Fix: Archive old sessions with ./scripts/session_archive.sh"
        echo ""
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi

    if [[ $ISSUES_FOUND -eq 0 ]]; then
        echo -e "${GREEN}✓ No budget issues detected${NC}"
    else
        echo "Total issues found: $ISSUES_FOUND"
    fi

    echo ""
fi

# Mode: Recommendations
if [[ "$MODE" == "recommendations" ]]; then
    echo "======================================"
    echo "Budget Optimization Recommendations"
    echo "======================================"
    echo ""

    # Run analysis and generate recommendations
    RECOMMENDATIONS=()

    # Check session start
    if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
        LINES=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md")
        BUDGET=$(get_budget "session_start")
        TOKENS=$((LINES * 20))

        if [[ $TOKENS -gt $((BUDGET * 120 / 100)) ]]; then
            RECOMMENDATIONS+=("Regenerate current-session.md to reduce size (currently $TOKENS tokens, target: $BUDGET)")
        fi
    fi

    # Check file distribution
    OVERSIZED=$(./scripts/monitor_file_sizes.sh 2>/dev/null | grep -c "^ERROR:" || echo "0")
    if [[ $OVERSIZED -gt 0 ]]; then
        RECOMMENDATIONS+=("$OVERSIZED file(s) exceed size limits - run ./scripts/monitor_file_sizes.sh for details")
    fi

    # Check daily sessions
    DAILY_COUNT=$(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $DAILY_COUNT -gt 7 ]]; then
        RECOMMENDATIONS+=("Archive old daily sessions (currently $DAILY_COUNT, recommend <7)")
    fi

    # Display recommendations
    if [[ ${#RECOMMENDATIONS[@]} -eq 0 ]]; then
        echo -e "${GREEN}✓ No optimization recommendations at this time${NC}"
        echo ""
        echo "Current budget usage is within healthy limits."
    else
        echo "Found ${#RECOMMENDATIONS[@]} recommendation(s):"
        echo ""

        for i in "${!RECOMMENDATIONS[@]}"; do
            echo "$((i + 1)). ${RECOMMENDATIONS[$i]}"
        done
    fi

    echo ""

    # Quick reference
    echo "Quick Commands:"
    echo "  Monitor files:    ./scripts/monitor_file_sizes.sh"
    echo "  View dashboard:   ./scripts/context_dashboard.sh"
    echo "  Archive sessions: ./scripts/session_archive.sh"
    echo "  Regenerate status: ./scripts/update_status.sh"
    echo ""
fi

# Mode: Export History
if [[ "$MODE" == "export" ]]; then
    if [[ ! -f "$TRACKING_LOG" ]]; then
        echo "No tracking data available"
        exit 1
    fi

    echo "timestamp,operation,tokens,budget,percentage"
    while IFS='|' read -r timestamp operation tokens budget; do
        percentage=$((tokens * 100 / budget))
        echo "$timestamp,$operation,$tokens,$budget,$percentage"
    done < "$TRACKING_LOG"
fi
