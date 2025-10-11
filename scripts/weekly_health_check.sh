#!/usr/bin/env bash
#
# weekly_health_check.sh - Comprehensive weekly health check for context optimization
#
# Purpose: Run comprehensive health checks and generate weekly report
# Usage: ./scripts/weekly_health_check.sh [--email=ADDRESS] [--report=FILE]
#
# Performs:
#   - File size monitoring
#   - Context budget analysis
#   - Baseline comparison
#   - Git repository health
#   - Documentation integrity
#   - Archive status

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORT_DIR="${PROJECT_ROOT}/.ai/monitoring/reports"
REPORT_FILE="${REPORT_DIR}/weekly_$(date +%Y%m%d).md"
BASELINE_FILE="${PROJECT_ROOT}/.ai/monitoring/baselines.json"
EMAIL_TO=""

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNING_CHECKS=0
FAILED_CHECKS=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --email=*)
            EMAIL_TO="${1#*=}"
            shift
            ;;
        --report=*)
            REPORT_FILE="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--email=ADDRESS] [--report=FILE]"
            echo ""
            echo "Options:"
            echo "  --email=ADDRESS   Send report to email address"
            echo "  --report=FILE     Specify report file location"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create report directory
mkdir -p "$REPORT_DIR"

# Function to record check result
record_check() {
    local status=$1  # PASS, WARN, FAIL
    local message=$2

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    case $status in
        PASS)
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            echo -e "${GREEN}✓${NC} $message"
            echo "- ✓ $message" >> "$REPORT_FILE"
            ;;
        WARN)
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            echo -e "${YELLOW}⚠${NC} $message"
            echo "- ⚠️ $message" >> "$REPORT_FILE"
            ;;
        FAIL)
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            echo -e "${RED}✗${NC} $message"
            echo "- ✗ $message" >> "$REPORT_FILE"
            ;;
    esac
}

# Initialize report
cat > "$REPORT_FILE" <<EOF
# Weekly Context Optimization Health Report

**Generated**: $(date '+%Y-%m-%d %H:%M:%S')
**Report Period**: Week of $(date -v-7d '+%Y-%m-%d') to $(date '+%Y-%m-%d')
**Project**: NBA MCP Synthesis

---

EOF

# Header
echo "======================================"
echo "Weekly Context Optimization Health Check"
echo "======================================"
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ============================================================================
# Check 1: File Size Monitoring
# ============================================================================
echo -e "${BOLD}${BLUE}1. File Size Monitoring${NC}"
echo "─────────────────────────────────────"
echo "" | tee -a "$REPORT_FILE"
echo "## 1. File Size Monitoring" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [[ -x "$SCRIPT_DIR/monitor_file_sizes.sh" ]]; then
    set +e
    "$SCRIPT_DIR/monitor_file_sizes.sh" > /tmp/filesize_check.txt 2>&1
    EXIT_CODE=$?
    set -e

    ERROR_COUNT=$(grep -c "^ERROR:" /tmp/filesize_check.txt 2>/dev/null || echo "0")
    WARNING_COUNT=$(grep -c "^WARNING:" /tmp/filesize_check.txt 2>/dev/null || echo "0")

    if [[ $EXIT_CODE -eq 0 && $WARNING_COUNT -eq 0 ]]; then
        record_check "PASS" "All files within size limits"
    elif [[ $ERROR_COUNT -eq 0 && $WARNING_COUNT -gt 0 ]]; then
        record_check "WARN" "$WARNING_COUNT file(s) approaching size limits"
        echo "  Files approaching limits:" >> "$REPORT_FILE"
        grep "WARNING:" /tmp/filesize_check.txt | sed 's/^/    /' >> "$REPORT_FILE" 2>/dev/null || true
    else
        record_check "FAIL" "$ERROR_COUNT file(s) exceed size limits"
        echo "  Files exceeding limits:" >> "$REPORT_FILE"
        grep "ERROR:" /tmp/filesize_check.txt | sed 's/^/    /' >> "$REPORT_FILE" 2>/dev/null || true
    fi

    rm -f /tmp/filesize_check.txt
else
    record_check "FAIL" "File size monitoring script not found"
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# Check 2: Context Budget Compliance
# ============================================================================
echo ""
echo -e "${BOLD}${BLUE}2. Context Budget Compliance${NC}"
echo "─────────────────────────────────────"
echo "" | tee -a "$REPORT_FILE"
echo "## 2. Context Budget Compliance" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Session start check
if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
    LINES=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md")
    TOKENS=$((LINES * 20))
    TARGET=300

    if [[ $TOKENS -le $TARGET ]]; then
        record_check "PASS" "Session start: ${TOKENS} tokens (target: ${TARGET})"
    elif [[ $TOKENS -le $((TARGET * 120 / 100)) ]]; then
        record_check "WARN" "Session start: ${TOKENS} tokens (target: ${TARGET})"
    else
        record_check "FAIL" "Session start: ${TOKENS} tokens (exceeds target: ${TARGET})"
    fi
else
    record_check "FAIL" "Session start file not found (.ai/current-session.md)"
fi

# Status check
if [[ -f "$PROJECT_ROOT/PROJECT_STATUS.md" ]]; then
    LINES=$(wc -l < "$PROJECT_ROOT/PROJECT_STATUS.md")
    TOKENS=$((LINES * 20))
    TARGET=150

    if [[ $TOKENS -le $TARGET ]]; then
        record_check "PASS" "Status check: ${TOKENS} tokens (target: ${TARGET})"
    elif [[ $TOKENS -le $((TARGET * 120 / 100)) ]]; then
        record_check "WARN" "Status check: ${TOKENS} tokens (target: ${TARGET})"
    else
        record_check "FAIL" "Status check: ${TOKENS} tokens (exceeds target: ${TARGET})"
    fi
else
    record_check "FAIL" "Status file not found (PROJECT_STATUS.md)"
fi

# Tool lookup check
if [[ -f "$PROJECT_ROOT/.ai/permanent/tool-registry.md" ]]; then
    LINES=$(wc -l < "$PROJECT_ROOT/.ai/permanent/tool-registry.md")
    TOKENS=$((LINES * 20))
    TARGET=100

    if [[ $TOKENS -le $TARGET ]]; then
        record_check "PASS" "Tool lookup: ${TOKENS} tokens (target: ${TARGET})"
    elif [[ $TOKENS -le $((TARGET * 120 / 100)) ]]; then
        record_check "WARN" "Tool lookup: ${TOKENS} tokens (target: ${TARGET})"
    else
        record_check "FAIL" "Tool lookup: ${TOKENS} tokens (exceeds target: ${TARGET})"
    fi
else
    record_check "WARN" "Tool registry not found (.ai/permanent/tool-registry.md)"
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# Check 3: Baseline Comparison
# ============================================================================
echo ""
echo -e "${BOLD}${BLUE}3. Baseline Comparison${NC}"
echo "─────────────────────────────────────"
echo "" | tee -a "$REPORT_FILE"
echo "## 3. Baseline Comparison" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [[ -f "$BASELINE_FILE" ]]; then
    record_check "PASS" "Baseline file exists"

    # Extract baseline metrics (requires jq)
    if command -v jq &> /dev/null; then
        BASELINE_SESSION=$(jq -r '.context_budget.session_start.tokens_estimated' "$BASELINE_FILE" 2>/dev/null || echo "0")
        CURRENT_SESSION=$(($(wc -l < "$PROJECT_ROOT/.ai/current-session.md" 2>/dev/null || echo "0") * 20))

        if [[ $CURRENT_SESSION -le $BASELINE_SESSION ]]; then
            IMPROVEMENT=$((BASELINE_SESSION - CURRENT_SESSION))
            record_check "PASS" "Session start improved by ${IMPROVEMENT} tokens"
        elif [[ $CURRENT_SESSION -le $((BASELINE_SESSION * 110 / 100)) ]]; then
            record_check "WARN" "Session start increased slightly (within 10%)"
        else
            REGRESSION=$((CURRENT_SESSION - BASELINE_SESSION))
            record_check "FAIL" "Session start regressed by ${REGRESSION} tokens"
        fi
    else
        record_check "WARN" "jq not installed - cannot compare baselines"
    fi
else
    record_check "WARN" "No baseline established - run ./scripts/establish_baselines.sh"
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# Check 4: Git Repository Health
# ============================================================================
echo ""
echo -e "${BOLD}${BLUE}4. Git Repository Health${NC}"
echo "─────────────────────────────────────"
echo "" | tee -a "$REPORT_FILE"
echo "## 4. Git Repository Health" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    record_check "PASS" "Git repository active"

    # Check for uncommitted changes
    if git -C "$PROJECT_ROOT" diff-index --quiet HEAD -- 2>/dev/null; then
        record_check "PASS" "No uncommitted changes"
    else
        CHANGED_FILES=$(git -C "$PROJECT_ROOT" diff --name-only | wc -l | tr -d ' ')
        record_check "WARN" "${CHANGED_FILES} file(s) with uncommitted changes"
    fi

    # Check untracked files
    UNTRACKED=$(git -C "$PROJECT_ROOT" ls-files --others --exclude-standard | wc -l | tr -d ' ')
    if [[ $UNTRACKED -eq 0 ]]; then
        record_check "PASS" "No untracked files"
    elif [[ $UNTRACKED -le 5 ]]; then
        record_check "WARN" "${UNTRACKED} untracked file(s)"
    else
        record_check "WARN" "${UNTRACKED} untracked files (consider .gitignore)"
    fi
else
    record_check "FAIL" "Not a git repository"
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# Check 5: Documentation Integrity
# ============================================================================
echo ""
echo -e "${BOLD}${BLUE}5. Documentation Integrity${NC}"
echo "─────────────────────────────────────"
echo "" | tee -a "$REPORT_FILE"
echo "## 5. Documentation Integrity" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Check for required files
REQUIRED_FILES=(
    ".ai/index.md"
    ".ai/current-session.md"
    "PROJECT_STATUS.md"
    "docs/DOCUMENTATION_MAP.md"
    "CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md"
    "START_HERE_FOR_CLAUDE.md"
)

MISSING_COUNT=0
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$PROJECT_ROOT/$file" ]]; then
        :  # File exists, do nothing
    else
        MISSING_COUNT=$((MISSING_COUNT + 1))
        echo "  Missing: $file" >> "$REPORT_FILE"
    fi
done

if [[ $MISSING_COUNT -eq 0 ]]; then
    record_check "PASS" "All required documentation files present"
else
    record_check "FAIL" "${MISSING_COUNT} required file(s) missing"
fi

# Check for broken links (basic check)
BROKEN_LINKS=0
while IFS= read -r -d '' file; do
    while IFS= read -r link; do
        # Extract file path from markdown link
        filepath=$(echo "$link" | sed -n 's/.*(\([^)]*\)).*/\1/p' | sed 's/#.*//')

        # Skip URLs and anchors
        if [[ "$filepath" =~ ^http || "$filepath" =~ ^# || -z "$filepath" ]]; then
            continue
        fi

        # Resolve relative path
        filedir=$(dirname "$file")
        fullpath="$filedir/$filepath"

        # Check if file exists
        if [[ ! -f "$fullpath" && ! -d "$fullpath" ]]; then
            BROKEN_LINKS=$((BROKEN_LINKS + 1))
        fi
    done < <(grep -o '\[.*\](.*\.md)' "$file" 2>/dev/null || true)
done < <(find "$PROJECT_ROOT/docs" "$PROJECT_ROOT/.ai" -type f -name "*.md" -print0 2>/dev/null || true)

if [[ $BROKEN_LINKS -eq 0 ]]; then
    record_check "PASS" "No broken documentation links detected"
elif [[ $BROKEN_LINKS -le 5 ]]; then
    record_check "WARN" "${BROKEN_LINKS} potentially broken link(s)"
else
    record_check "FAIL" "${BROKEN_LINKS} broken links detected"
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# Check 6: Archive Status
# ============================================================================
echo ""
echo -e "${BOLD}${BLUE}6. Archive Status${NC}"
echo "─────────────────────────────────────"
echo "" | tee -a "$REPORT_FILE"
echo "## 6. Archive Status" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Check daily sessions count
DAILY_COUNT=$(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" 2>/dev/null | wc -l | tr -d ' ')
if [[ $DAILY_COUNT -le 7 ]]; then
    record_check "PASS" "${DAILY_COUNT} daily session file(s) (within weekly limit)"
elif [[ $DAILY_COUNT -le 14 ]]; then
    record_check "WARN" "${DAILY_COUNT} daily sessions (consider archiving)"
else
    record_check "FAIL" "${DAILY_COUNT} daily sessions (archive needed)"
fi

# Check archive directory exists
if [[ -d "$PROJECT_ROOT/.ai/archive" ]]; then
    ARCHIVED_COUNT=$(find "$PROJECT_ROOT/.ai/archive" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    record_check "PASS" "Archive directory exists (${ARCHIVED_COUNT} archived files)"
else
    record_check "WARN" "Archive directory not found"
fi

# Check for archival candidates in root directory
ROOT_COMPLETION=$(find "$PROJECT_ROOT" -maxdepth 1 -type f \( -name "*_COMPLETE.md" -o -name "*_VERIFICATION*.md" -o -name "*_REPORT.md" -o -name "*_SUCCESS.md" \) 2>/dev/null | wc -l | tr -d ' ')
if [[ $ROOT_COMPLETION -eq 0 ]]; then
    record_check "PASS" "No completion documents in root (all archived)"
elif [[ $ROOT_COMPLETION -le 2 ]]; then
    record_check "WARN" "${ROOT_COMPLETION} completion document(s) in root (consider archiving)"
else
    record_check "FAIL" "${ROOT_COMPLETION} completion documents in root (archive recommended)"
fi

# Check root directory markdown file count
ROOT_MD_COUNT=$(ls -1 "$PROJECT_ROOT"/*.md 2>/dev/null | wc -l | tr -d ' ')
if [[ $ROOT_MD_COUNT -le 15 ]]; then
    record_check "PASS" "Root has ${ROOT_MD_COUNT} markdown files (target: <15)"
elif [[ $ROOT_MD_COUNT -le 20 ]]; then
    record_check "WARN" "Root has ${ROOT_MD_COUNT} markdown files (target: <15)"
else
    record_check "FAIL" "Root has ${ROOT_MD_COUNT} markdown files (target: <20, critical)"
fi

# Calculate estimated token savings if archiving is done
if [[ $ROOT_COMPLETION -gt 0 || $DAILY_COUNT -gt 7 ]]; then
    ARCHIVABLE_LINES=0
    # Estimate lines in root completion docs
    for file in $(find "$PROJECT_ROOT" -maxdepth 1 -type f \( -name "*_COMPLETE.md" -o -name "*_VERIFICATION*.md" -o -name "*_REPORT.md" \) 2>/dev/null); do
        if [[ -f "$file" ]]; then
            FILE_LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
            ARCHIVABLE_LINES=$((ARCHIVABLE_LINES + FILE_LINES))
        fi
    done

    # Estimate lines in old daily sessions (beyond 7 days)
    if [[ $DAILY_COUNT -gt 7 ]]; then
        for file in $(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" -mtime +7 2>/dev/null); do
            if [[ -f "$file" ]]; then
                FILE_LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
                ARCHIVABLE_LINES=$((ARCHIVABLE_LINES + FILE_LINES))
            fi
        done
    fi

    ESTIMATED_TOKEN_SAVINGS=$((ARCHIVABLE_LINES * 20))
    echo "  💾 Potential savings: ~${ESTIMATED_TOKEN_SAVINGS} tokens (${ARCHIVABLE_LINES} lines)" | tee -a "$REPORT_FILE"
    echo "  📦 Run: ./scripts/auto_archive.sh --dry-run" | tee -a "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "======================================"
echo "Summary"
echo "======================================"
echo "" | tee -a "$REPORT_FILE"
echo "## Summary" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
echo ""

# Add summary to report
cat >> "$REPORT_FILE" <<EOF
**Total Checks**: $TOTAL_CHECKS
**Passed**: $PASSED_CHECKS
**Warnings**: $WARNING_CHECKS
**Failed**: $FAILED_CHECKS

---

## Recommendations

EOF

# Generate recommendations
if [[ $FAILED_CHECKS -eq 0 && $WARNING_CHECKS -eq 0 ]]; then
    echo -e "${GREEN}✓ All systems operating optimally${NC}"
    echo "All systems operating optimally. No action required." >> "$REPORT_FILE"
else
    echo "Recommended Actions:"
    echo "" >> "$REPORT_FILE"

    if [[ $FAILED_CHECKS -gt 0 ]]; then
        echo "  1. Review and address all failed checks immediately"
        echo "1. **Immediate**: Review and address all failed checks" >> "$REPORT_FILE"
    fi

    if [[ $WARNING_CHECKS -gt 0 ]]; then
        echo "  2. Consider addressing warnings to prevent future issues"
        echo "2. **Soon**: Address warnings to prevent future issues" >> "$REPORT_FILE"
    fi

    if [[ $DAILY_COUNT -gt 7 ]]; then
        echo "  3. Run: ./scripts/session_archive.sh"
        echo "3. Archive old sessions: \`./scripts/session_archive.sh\`" >> "$REPORT_FILE"
    fi

    echo "  4. Review full report: $REPORT_FILE"
    echo "4. Review full report for details" >> "$REPORT_FILE"
fi

echo ""
echo "Report saved to: $REPORT_FILE"
echo ""

# Email report if requested
if [[ -n "$EMAIL_TO" ]]; then
    if command -v mail &> /dev/null; then
        mail -s "Weekly Context Optimization Health Report" "$EMAIL_TO" < "$REPORT_FILE"
        echo -e "${GREEN}✓ Report emailed to: $EMAIL_TO${NC}"
    else
        echo -e "${YELLOW}⚠ mail command not available - cannot send email${NC}"
    fi
fi

# Exit code based on results
if [[ $FAILED_CHECKS -gt 0 ]]; then
    exit 1
elif [[ $WARNING_CHECKS -gt 0 ]]; then
    exit 0
else
    exit 0
fi
