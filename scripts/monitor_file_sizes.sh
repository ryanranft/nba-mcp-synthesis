#!/usr/bin/env bash
#
# monitor_file_sizes.sh - Proactive file size monitoring for context optimization
#
# Purpose: Scan markdown files and alert when they exceed context budget targets
# Usage: ./scripts/monitor_file_sizes.sh [--verbose] [--log=FILE]
#
# Thresholds:
#   - Index files: 100 lines (warning at 80)
#   - Status files: 200 lines (warning at 160)
#   - Guide files: 300 lines (warning at 240)
#   - Daily session files: 500 lines (warning at 400)
#   - Plan files: 3000 lines (warning at 2400)

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${PROJECT_ROOT}/.ai/monitoring/file_size_log.txt"
VERBOSE=0

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Thresholds (in lines)
declare -A ERROR_THRESHOLDS=(
    ["index"]=100
    ["status"]=200
    ["guide"]=300
    ["daily"]=500
    ["plan"]=3000
)

declare -A WARNING_THRESHOLDS=(
    ["index"]=80
    ["status"]=160
    ["guide"]=240
    ["daily"]=400
    ["plan"]=2400
)

# Counters
TOTAL_FILES=0
ERROR_COUNT=0
WARNING_COUNT=0
OK_COUNT=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --log=*)
            LOG_FILE="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--verbose] [--log=FILE]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v     Show all files, including those within limits"
            echo "  --log=FILE        Specify log file location (default: .ai/monitoring/file_size_log.txt)"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create monitoring directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to determine file type and get thresholds
get_file_type() {
    local filepath="$1"
    local basename=$(basename "$filepath")
    local dirname=$(dirname "$filepath")

    # Determine file type based on path and name
    if [[ "$basename" == "index.md" ]]; then
        echo "index"
    elif [[ "$dirname" == *"/status"* ]] || [[ "$basename" == *"STATUS"* ]]; then
        echo "status"
    elif [[ "$dirname" == *"/guides"* ]] || [[ "$basename" == *"GUIDE"* ]]; then
        echo "guide"
    elif [[ "$dirname" == *"/.ai/daily"* ]]; then
        echo "daily"
    elif [[ "$dirname" == *"/plans"* ]] || [[ "$basename" == *"PLAN"* ]]; then
        echo "plan"
    else
        echo "guide"  # Default to guide thresholds
    fi
}

# Function to check file size
check_file() {
    local filepath="$1"
    local line_count=$(wc -l < "$filepath")
    local file_type=$(get_file_type "$filepath")
    local error_threshold=${ERROR_THRESHOLDS[$file_type]}
    local warning_threshold=${WARNING_THRESHOLDS[$file_type]}
    local relative_path="${filepath#$PROJECT_ROOT/}"

    TOTAL_FILES=$((TOTAL_FILES + 1))

    # Check against thresholds
    if [[ $line_count -gt $error_threshold ]]; then
        echo -e "${RED}ERROR${NC}: $relative_path"
        echo "  Lines: $line_count (exceeds $file_type limit of $error_threshold)"
        echo "  Action: Refactor, split, or archive content"
        echo ""
        ERROR_COUNT=$((ERROR_COUNT + 1))

        # Log to file
        echo "$(date '+%Y-%m-%d %H:%M:%S') | ERROR | $relative_path | $line_count lines (limit: $error_threshold)" >> "$LOG_FILE"

    elif [[ $line_count -gt $warning_threshold ]]; then
        echo -e "${YELLOW}WARNING${NC}: $relative_path"
        echo "  Lines: $line_count (approaching $file_type limit of $error_threshold)"
        echo "  Suggestion: Consider refactoring soon"
        echo ""
        WARNING_COUNT=$((WARNING_COUNT + 1))

        # Log to file
        echo "$(date '+%Y-%m-%d %H:%M:%S') | WARNING | $relative_path | $line_count lines (limit: $error_threshold)" >> "$LOG_FILE"

    elif [[ $VERBOSE -eq 1 ]]; then
        echo -e "${GREEN}OK${NC}: $relative_path"
        echo "  Lines: $line_count (within $file_type limit of $error_threshold)"
        echo ""
        OK_COUNT=$((OK_COUNT + 1))
    else
        OK_COUNT=$((OK_COUNT + 1))
    fi
}

# Main execution
echo "======================================"
echo "Context Optimization File Size Monitor"
echo "======================================"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Scan project documentation
echo -e "${BLUE}Scanning project files...${NC}"
echo ""

# Check index files
while IFS= read -r -d '' file; do
    check_file "$file"
done < <(find "$PROJECT_ROOT" -type f -name "index.md" -print0 2>/dev/null || true)

# Check status files
while IFS= read -r -d '' file; do
    check_file "$file"
done < <(find "$PROJECT_ROOT/project/status" -type f -name "*.md" -print0 2>/dev/null || true)

# Check guide files
while IFS= read -r -d '' file; do
    check_file "$file"
done < <(find "$PROJECT_ROOT/docs/guides" -type f -name "*.md" -print0 2>/dev/null || true)

# Check daily session files
while IFS= read -r -d '' file; do
    check_file "$file"
done < <(find "$PROJECT_ROOT/.ai/daily" -type f -name "*.md" ! -name "template.md" -print0 2>/dev/null || true)

# Check plan files
while IFS= read -r -d '' file; do
    check_file "$file"
done < <(find "$PROJECT_ROOT/docs/plans" -type f -name "*.md" -print0 2>/dev/null || true)

# Check key root files
for file in "$PROJECT_ROOT/PROJECT_STATUS.md" \
            "$PROJECT_ROOT/CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md" \
            "$PROJECT_ROOT/START_HERE_FOR_CLAUDE.md" \
            "$PROJECT_ROOT/.ai/index.md"; do
    if [[ -f "$file" ]]; then
        check_file "$file"
    fi
done

# Summary
echo "======================================"
echo "Summary"
echo "======================================"
echo "Total files scanned: $TOTAL_FILES"
echo -e "${RED}Errors (exceeds limit): $ERROR_COUNT${NC}"
echo -e "${YELLOW}Warnings (approaching limit): $WARNING_COUNT${NC}"
echo -e "${GREEN}OK (within limits): $OK_COUNT${NC}"
echo ""

# Exit status based on results
if [[ $ERROR_COUNT -gt 0 ]]; then
    echo -e "${RED}Action Required:${NC} $ERROR_COUNT file(s) exceed context budget limits"
    echo "Review files above and consider:"
    echo "  1. Split into smaller focused files"
    echo "  2. Archive historical content"
    echo "  3. Use cross-references instead of duplication"
    echo ""
    echo "See: docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md for strategies"
    exit 1
elif [[ $WARNING_COUNT -gt 0 ]]; then
    echo -e "${YELLOW}Warning:${NC} $WARNING_COUNT file(s) approaching context budget limits"
    echo "Consider proactive refactoring to prevent future issues"
    exit 0
else
    echo -e "${GREEN}All files within context budget limits${NC}"
    exit 0
fi
