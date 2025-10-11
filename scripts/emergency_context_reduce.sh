#!/usr/bin/env bash
#
# emergency_context_reduce.sh - Emergency context reduction procedures
#
# Purpose: Rapidly reduce context usage when approaching/exceeding limits
# Usage: ./scripts/emergency_context_reduce.sh [--level=1|2|3] [--dry-run]
#
# Levels:
#   1 - Warning (8-9K tokens): Quick optimizations
#   2 - Critical (9-10K tokens): Aggressive reduction
#   3 - Emergency (>10K tokens): Maximum reduction

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LEVEL=1
DRY_RUN=0

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --level=*)
            LEVEL="${1#*=}"
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=1
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--level=1|2|3] [--dry-run]"
            echo ""
            echo "Emergency Levels:"
            echo "  --level=1  Warning (8-9K tokens) - Quick optimizations"
            echo "  --level=2  Critical (9-10K tokens) - Aggressive reduction"
            echo "  --level=3  Emergency (>10K tokens) - Maximum reduction"
            echo ""
            echo "Options:"
            echo "  --dry-run, -n  Show what would be done without doing it"
            echo "  --help, -h     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to estimate current context usage
estimate_context() {
    local total=0

    # Session start
    if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
        local lines=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md")
        total=$((total + lines * 20))
    fi

    # Status check
    if [[ -f "$PROJECT_ROOT/PROJECT_STATUS.md" ]]; then
        local lines=$(wc -l < "$PROJECT_ROOT/PROJECT_STATUS.md")
        total=$((total + lines * 20))
    fi

    # Tool registry
    if [[ -f "$PROJECT_ROOT/.ai/permanent/tool-registry.md" ]]; then
        local lines=$(wc -l < "$PROJECT_ROOT/.ai/permanent/tool-registry.md")
        total=$((total + lines * 20))
    fi

    echo $total
}

echo "======================================"
echo "Emergency Context Reduction"
echo "======================================"
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
    echo ""
fi

# Estimate current context
INITIAL_CONTEXT=$(estimate_context)
echo "Initial context estimate: ${INITIAL_CONTEXT} tokens"
echo "Emergency level: $LEVEL"
echo ""

# Level 1: Warning (Quick Optimizations)
if [[ $LEVEL -ge 1 ]]; then
    echo -e "${BOLD}${BLUE}Level 1: Quick Optimizations${NC}"
    echo "─────────────────────────────────────"
    echo ""

    # 1. Regenerate current-session.md (minimal mode)
    echo "1. Regenerating current-session.md..."
    if [[ $DRY_RUN -eq 0 ]]; then
        if [[ -x "$SCRIPT_DIR/session_start.sh" ]]; then
            "$SCRIPT_DIR/session_start.sh" --minimal > /dev/null 2>&1 || true
            echo -e "   ${GREEN}✓${NC} Session file regenerated"
        fi
    else
        echo "   Would regenerate session file"
    fi

    # 2. Archive sessions older than 3 days
    echo "2. Archiving old sessions..."
    DAILY_COUNT=$(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" -mtime +3 2>/dev/null | wc -l | tr -d ' ')
    if [[ $DAILY_COUNT -gt 0 ]]; then
        if [[ $DRY_RUN -eq 0 ]]; then
            mkdir -p "$PROJECT_ROOT/.ai/archive"
            find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" -mtime +3 -exec mv {} "$PROJECT_ROOT/.ai/archive/" \; 2>/dev/null || true
            echo -e "   ${GREEN}✓${NC} Archived $DAILY_COUNT old session(s)"
        else
            echo "   Would archive $DAILY_COUNT session(s)"
        fi
    else
        echo "   No old sessions to archive"
    fi

    # 3. Clean temporary files
    echo "3. Cleaning temporary files..."
    TEMP_COUNT=$(find "$PROJECT_ROOT" -name "*.tmp" -o -name "*~" -o -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $TEMP_COUNT -gt 0 ]]; then
        if [[ $DRY_RUN -eq 0 ]]; then
            find "$PROJECT_ROOT" \( -name "*.tmp" -o -name "*~" -o -name ".DS_Store" \) -delete 2>/dev/null || true
            echo -e "   ${GREEN}✓${NC} Removed $TEMP_COUNT temp file(s)"
        else
            echo "   Would remove $TEMP_COUNT temp file(s)"
        fi
    else
        echo "   No temp files found"
    fi

    echo ""
fi

# Level 2: Critical (Aggressive Reduction)
if [[ $LEVEL -ge 2 ]]; then
    echo -e "${BOLD}${YELLOW}Level 2: Aggressive Reduction${NC}"
    echo "─────────────────────────────────────"
    echo ""

    # 4. Archive ALL daily sessions
    echo "4. Archiving all daily sessions..."
    ALL_DAILY=$(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $ALL_DAILY -gt 0 ]]; then
        if [[ $DRY_RUN -eq 0 ]]; then
            mkdir -p "$PROJECT_ROOT/.ai/archive/emergency_$(date +%Y%m%d)"
            find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" -exec mv {} "$PROJECT_ROOT/.ai/archive/emergency_$(date +%Y%m%d)/" \; 2>/dev/null || true
            echo -e "   ${GREEN}✓${NC} Archived all $ALL_DAILY session(s)"
        else
            echo "   Would archive all $ALL_DAILY session(s)"
        fi
    else
        echo "   No sessions to archive"
    fi

    # 5. Minimize PROJECT_STATUS.md
    echo "5. Minimizing PROJECT_STATUS.md..."
    if [[ -f "$PROJECT_ROOT/PROJECT_STATUS.md" ]]; then
        LINES=$(wc -l < "$PROJECT_ROOT/PROJECT_STATUS.md")
        if [[ $LINES -gt 150 ]]; then
            if [[ $DRY_RUN -eq 0 ]]; then
                # Backup original
                cp "$PROJECT_ROOT/PROJECT_STATUS.md" "$PROJECT_ROOT/PROJECT_STATUS.md.backup"

                # Create minimal version
                cat > "$PROJECT_ROOT/PROJECT_STATUS.md" <<EOF
# Project Status

**Last Updated**: $(date '+%Y-%m-%d')
**Status**: Context emergency reduction in progress

---

## Quick Status

- Project: NBA MCP Synthesis
- Tools: 163 registered MCP tools
- Sprints: 8 completed
- Status: See project/status/ for details

---

*This is a minimal emergency version. Full status: PROJECT_STATUS.md.backup*
*Regenerate: ./scripts/update_status.sh*
EOF
                echo -e "   ${GREEN}✓${NC} Minimized PROJECT_STATUS.md ($LINES → 20 lines)"
            else
                echo "   Would minimize PROJECT_STATUS.md ($LINES lines)"
            fi
        else
            echo "   PROJECT_STATUS.md already minimal"
        fi
    fi

    # 6. Clear monitoring logs
    echo "6. Clearing old monitoring logs..."
    LOG_COUNT=$(find "$PROJECT_ROOT/.ai/monitoring" -name "*.log" -mtime +7 2>/dev/null | wc -l | tr -d ' ')
    if [[ $LOG_COUNT -gt 0 ]]; then
        if [[ $DRY_RUN -eq 0 ]]; then
            find "$PROJECT_ROOT/.ai/monitoring" -name "*.log" -mtime +7 -delete 2>/dev/null || true
            echo -e "   ${GREEN}✓${NC} Removed $LOG_COUNT old log(s)"
        else
            echo "   Would remove $LOG_COUNT log(s)"
        fi
    else
        echo "   No old logs to remove"
    fi

    echo ""
fi

# Level 3: Emergency (Maximum Reduction)
if [[ $LEVEL -ge 3 ]]; then
    echo -e "${BOLD}${RED}Level 3: Maximum Reduction${NC}"
    echo "─────────────────────────────────────"
    echo ""

    # 7. Create ultra-minimal current-session.md
    echo "7. Creating ultra-minimal session file..."
    if [[ $DRY_RUN -eq 0 ]]; then
        cat > "$PROJECT_ROOT/.ai/current-session.md" <<EOF
# Emergency Session - $(date '+%Y-%m-%d')

**Context**: Emergency reduction performed
**Status**: Continue from last commit

---

## Quick Reference

- Last commit: $(git -C "$PROJECT_ROOT" log -1 --format="%h - %s" 2>/dev/null || echo "Unknown")
- Working directory: $(git -C "$PROJECT_ROOT" diff --stat 2>/dev/null | tail -1 || echo "Clean")
- Next: Resume work from git history

---

*Full context: Run ./scripts/session_start.sh to regenerate*
EOF
        echo -e "   ${GREEN}✓${NC} Created ultra-minimal session file (~15 lines)"
    else
        echo "   Would create ultra-minimal session file"
    fi

    # 8. Archive all monthly summaries
    echo "8. Archiving monthly summaries..."
    MONTHLY_COUNT=$(find "$PROJECT_ROOT/.ai/monthly" -type f -name "*.md" ! -name "template.md" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $MONTHLY_COUNT -gt 0 ]]; then
        if [[ $DRY_RUN -eq 0 ]]; then
            mkdir -p "$PROJECT_ROOT/.ai/archive"
            find "$PROJECT_ROOT/.ai/monthly" -type f -name "*.md" ! -name "template.md" -exec mv {} "$PROJECT_ROOT/.ai/archive/" \; 2>/dev/null || true
            echo -e "   ${GREEN}✓${NC} Archived $MONTHLY_COUNT monthly summaries"
        else
            echo "   Would archive $MONTHLY_COUNT monthly summaries"
        fi
    else
        echo "   No monthly summaries to archive"
    fi

    # 9. Create emergency resume point
    echo "9. Creating emergency resume point..."
    if [[ $DRY_RUN -eq 0 ]]; then
        mkdir -p "$PROJECT_ROOT/.ai/emergency"
        cat > "$PROJECT_ROOT/.ai/emergency/resume_$(date +%Y%m%d_%H%M%S).md" <<EOF
# Emergency Resume Point

**Timestamp**: $(date '+%Y-%m-%d %H:%M:%S')
**Reason**: Context limit exceeded

---

## Last Known State

**Git Status**:
\`\`\`
$(git -C "$PROJECT_ROOT" status --short 2>/dev/null || echo "Unknown")
\`\`\`

**Last Commit**:
$(git -C "$PROJECT_ROOT" log -1 --format="%H%n%an <%ae>%n%ai%n%n%s%n%n%b" 2>/dev/null || echo "Unknown")

**Current Branch**:
$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "Unknown")

---

## Resume Instructions

1. Check git status: \`git status\`
2. Review last commit: \`git log -1\`
3. Read this file for context
4. Continue work

---

*Auto-generated during emergency context reduction*
EOF
        echo -e "   ${GREEN}✓${NC} Created emergency resume point"
    else
        echo "   Would create emergency resume point"
    fi

    echo ""
fi

# Estimate new context
echo "======================================"
echo "Reduction Complete"
echo "======================================"
echo ""

FINAL_CONTEXT=$(estimate_context)
REDUCTION=$((INITIAL_CONTEXT - FINAL_CONTEXT))
PERCENTAGE=0
if [[ $INITIAL_CONTEXT -gt 0 ]]; then
    PERCENTAGE=$((REDUCTION * 100 / INITIAL_CONTEXT))
fi

echo "Initial context:  ${INITIAL_CONTEXT} tokens"
echo "Final context:    ${FINAL_CONTEXT} tokens"
echo -e "Reduction:        ${GREEN}${REDUCTION} tokens (${PERCENTAGE}%)${NC}"
echo ""

# Recommendations
if [[ $FINAL_CONTEXT -gt 9000 ]]; then
    echo -e "${RED}⚠ WARNING: Context still high${NC}"
    echo ""
    echo "Additional actions:"
    echo "  1. Consider hard reset: ./scripts/session_start.sh --force-reset"
    echo "  2. Split current work into smaller sessions"
    echo "  3. Review: docs/guides/CONTEXT_EMERGENCY_PROCEDURES.md"
elif [[ $FINAL_CONTEXT -gt 8000 ]]; then
    echo -e "${YELLOW}⚠ NOTICE: Context reduced but monitor closely${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Monitor dashboard: ./scripts/context_dashboard.sh"
    echo "  2. Continue work carefully"
    echo "  3. Consider checkpointing: ./scripts/checkpoint_session.sh"
else
    echo -e "${GREEN}✓ Context successfully reduced${NC}"
    echo ""
    echo "Safe to continue work. Remember to:"
    echo "  1. Monitor budget: ./scripts/track_context_budget.sh --session"
    echo "  2. Use append-only logs (never read)"
    echo "  3. Apply optimization best practices"
fi

echo ""

# If files were backed up, show how to restore
if [[ $DRY_RUN -eq 0 && $LEVEL -ge 2 ]]; then
    if [[ -f "$PROJECT_ROOT/PROJECT_STATUS.md.backup" ]]; then
        echo "────────────────────────────────────"
        echo "Backup files created:"
        echo "  PROJECT_STATUS.md.backup"
        echo ""
        echo "To restore: mv PROJECT_STATUS.md.backup PROJECT_STATUS.md"
        echo ""
    fi
fi

exit 0
