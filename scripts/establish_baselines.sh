#!/usr/bin/env bash
#
# establish_baselines.sh - Establish baseline metrics for context optimization
#
# Purpose: Capture current state to track improvements over time
# Usage: ./scripts/establish_baselines.sh [--force] [--output=FILE]
#
# Captures:
#   - File counts by category
#   - Line counts by category
#   - Session start cost
#   - Status check cost
#   - Tool lookup cost
#   - Overall context usage patterns

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BASELINE_FILE="${PROJECT_ROOT}/.ai/monitoring/baselines.json"
FORCE=0

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=1
            shift
            ;;
        --output=*)
            BASELINE_FILE="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--force] [--output=FILE]"
            echo ""
            echo "Options:"
            echo "  --force, -f       Overwrite existing baseline"
            echo "  --output=FILE     Specify output file (default: .ai/monitoring/baselines.json)"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if baseline already exists
if [[ -f "$BASELINE_FILE" && $FORCE -eq 0 ]]; then
    echo -e "${YELLOW}Baseline already exists at: $BASELINE_FILE${NC}"
    echo "Use --force to overwrite"
    echo ""
    echo "To view current baseline:"
    echo "  cat $BASELINE_FILE | jq ."
    exit 1
fi

# Create monitoring directory
mkdir -p "$(dirname "$BASELINE_FILE")"

echo "======================================"
echo "Establishing Context Optimization Baselines"
echo "======================================"
echo ""

# Function to count files and lines
count_files_lines() {
    local pattern="$1"
    local count=0
    local lines=0

    while IFS= read -r -d '' file; do
        count=$((count + 1))
        local file_lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        lines=$((lines + file_lines))
    done < <(find "$PROJECT_ROOT" -type f -path "$pattern" -print0 2>/dev/null || true)

    echo "$count:$lines"
}

# Function to estimate tokens (1 line ≈ 20 tokens)
estimate_tokens() {
    local file=$1
    if [ -f "$file" ]; then
        # More accurate: count characters and divide by 4 (typical token/char ratio)
        local chars=$(wc -c < "$file" 2>/dev/null || echo "0")
        echo $((chars / 4))
    else
        echo "0"
    fi
}

echo -e "${BLUE}Collecting baseline metrics...${NC}"
echo ""

# 1. Session start metrics
echo "  • Session start metrics..."
SESSION_START_LINES=$(wc -l < "$PROJECT_ROOT/.ai/current-session.md" 2>/dev/null || echo "0")
SESSION_START_TOKENS=$(estimate_tokens "$PROJECT_ROOT/.ai/current-session.md")

# 2. Status check metrics
echo "  • Status check metrics..."
STATUS_CHECK_LINES=$(wc -l < "$PROJECT_ROOT/PROJECT_STATUS.md" 2>/dev/null || echo "0")
STATUS_CHECK_TOKENS=$(estimate_tokens "$PROJECT_ROOT/PROJECT_STATUS.md")

# 3. Tool lookup metrics
echo "  • Tool lookup metrics..."
TOOL_LOOKUP_LINES=$(wc -l < "$PROJECT_ROOT/.ai/permanent/tool-registry.md" 2>/dev/null || echo "0")
TOOL_LOOKUP_TOKENS=$(estimate_tokens "$PROJECT_ROOT/.ai/permanent/tool-registry.md")

# 4. File distribution metrics
echo "  • File distribution..."
INDEX_STATS=$(count_files_lines "*/index.md")
INDEX_COUNT=$(echo "$INDEX_STATS" | cut -d: -f1)
INDEX_LINES=$(echo "$INDEX_STATS" | cut -d: -f2)

STATUS_STATS=$(count_files_lines "*/status/*.md")
STATUS_COUNT=$(echo "$STATUS_STATS" | cut -d: -f1)
STATUS_LINES=$(echo "$STATUS_STATS" | cut -d: -f2)

GUIDE_STATS=$(count_files_lines "*/guides/*.md")
GUIDE_COUNT=$(echo "$GUIDE_STATS" | cut -d: -f1)
GUIDE_LINES=$(echo "$GUIDE_STATS" | cut -d: -f2)

DAILY_STATS=$(count_files_lines "*/.ai/daily/*.md")
DAILY_COUNT=$(echo "$DAILY_STATS" | cut -d: -f1)
DAILY_LINES=$(echo "$DAILY_STATS" | cut -d: -f2)

PLAN_STATS=$(count_files_lines "*/plans/*.md")
PLAN_COUNT=$(echo "$PLAN_STATS" | cut -d: -f1)
PLAN_LINES=$(echo "$PLAN_STATS" | cut -d: -f2)

# 5. Overall metrics
echo "  • Overall metrics..."
TOTAL_MD_FILES=$(find "$PROJECT_ROOT" -type f -name "*.md" ! -path "*/node_modules/*" ! -path "*/.git/*" 2>/dev/null | wc -l | tr -d ' ')
TOTAL_MD_LINES=0
while IFS= read -r -d '' file; do
    lines=$(wc -l < "$file" 2>/dev/null || echo "0")
    TOTAL_MD_LINES=$((TOTAL_MD_LINES + lines))
done < <(find "$PROJECT_ROOT" -type f -name "*.md" ! -path "*/node_modules/*" ! -path "*/.git/*" -print0 2>/dev/null || true)

# 6. Git metrics
echo "  • Git repository metrics..."
COMMIT_COUNT=$(git -C "$PROJECT_ROOT" rev-list --count HEAD 2>/dev/null || echo "0")
CURRENT_BRANCH=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
LAST_COMMIT=$(git -C "$PROJECT_ROOT" log -1 --format="%h - %s" 2>/dev/null || echo "N/A")

# Generate JSON baseline
cat > "$BASELINE_FILE" <<EOF
{
  "version": "1.0.0",
  "created_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "project": {
    "root": "$PROJECT_ROOT",
    "git_branch": "$CURRENT_BRANCH",
    "git_commit": "$LAST_COMMIT",
    "git_commit_count": $COMMIT_COUNT
  },
  "context_budget": {
    "session_start": {
      "lines": $SESSION_START_LINES,
      "tokens_estimated": $SESSION_START_TOKENS,
      "target": 300,
      "file": ".ai/current-session.md"
    },
    "status_check": {
      "lines": $STATUS_CHECK_LINES,
      "tokens_estimated": $STATUS_CHECK_TOKENS,
      "target": 150,
      "file": "PROJECT_STATUS.md"
    },
    "tool_lookup": {
      "lines": $TOOL_LOOKUP_LINES,
      "tokens_estimated": $TOOL_LOOKUP_TOKENS,
      "target": 100,
      "file": ".ai/permanent/tool-registry.md"
    },
    "overall": {
      "tokens_estimated": $((SESSION_START_TOKENS + STATUS_CHECK_TOKENS + TOOL_LOOKUP_TOKENS)),
      "target": 550
    }
  },
  "file_distribution": {
    "index_files": {
      "count": $INDEX_COUNT,
      "total_lines": $INDEX_LINES,
      "avg_lines": $([ $INDEX_COUNT -gt 0 ] && echo $((INDEX_LINES / INDEX_COUNT)) || echo 0),
      "target_per_file": 100
    },
    "status_files": {
      "count": $STATUS_COUNT,
      "total_lines": $STATUS_LINES,
      "avg_lines": $([ $STATUS_COUNT -gt 0 ] && echo $((STATUS_LINES / STATUS_COUNT)) || echo 0),
      "target_per_file": 200
    },
    "guide_files": {
      "count": $GUIDE_COUNT,
      "total_lines": $GUIDE_LINES,
      "avg_lines": $([ $GUIDE_COUNT -gt 0 ] && echo $((GUIDE_LINES / GUIDE_COUNT)) || echo 0),
      "target_per_file": 300
    },
    "daily_sessions": {
      "count": $DAILY_COUNT,
      "total_lines": $DAILY_LINES,
      "avg_lines": $([ $DAILY_COUNT -gt 0 ] && echo $((DAILY_LINES / DAILY_COUNT)) || echo 0),
      "target_per_file": 500
    },
    "plan_files": {
      "count": $PLAN_COUNT,
      "total_lines": $PLAN_LINES,
      "avg_lines": $([ $PLAN_COUNT -gt 0 ] && echo $((PLAN_LINES / PLAN_COUNT)) || echo 0),
      "target_per_file": 3000
    }
  },
  "overall_stats": {
    "total_markdown_files": $TOTAL_MD_FILES,
    "total_markdown_lines": $TOTAL_MD_LINES,
    "avg_lines_per_file": $([ $TOTAL_MD_FILES -gt 0 ] && echo $((TOTAL_MD_LINES / TOTAL_MD_FILES)) || echo 0)
  },
  "targets": {
    "context_reduction": "80-93%",
    "session_start_tokens": 300,
    "status_check_tokens": 150,
    "tool_lookup_tokens": 100,
    "overall_session_tokens": "3000-10000"
  }
}
EOF

echo ""
echo -e "${GREEN}✓ Baseline established successfully${NC}"
echo ""
echo "Location: $BASELINE_FILE"
echo ""

# Display summary
echo "======================================"
echo "Baseline Summary"
echo "======================================"
echo ""
echo "Context Budget:"
echo "  Session Start:  $SESSION_START_TOKENS tokens (target: 300)"
echo "  Status Check:   $STATUS_CHECK_TOKENS tokens (target: 150)"
echo "  Tool Lookup:    $TOOL_LOOKUP_TOKENS tokens (target: 100)"
echo "  Overall:        $((SESSION_START_TOKENS + STATUS_CHECK_TOKENS + TOOL_LOOKUP_TOKENS)) tokens (target: 550)"
echo ""
echo "File Distribution:"
echo "  Index Files:    $INDEX_COUNT files, $INDEX_LINES lines total"
echo "  Status Files:   $STATUS_COUNT files, $STATUS_LINES lines total"
echo "  Guide Files:    $GUIDE_COUNT files, $GUIDE_LINES lines total"
echo "  Daily Sessions: $DAILY_COUNT files, $DAILY_LINES lines total"
echo "  Plan Files:     $PLAN_COUNT files, $PLAN_LINES lines total"
echo ""
echo "Overall:"
echo "  Total MD Files: $TOTAL_MD_FILES"
echo "  Total Lines:    $TOTAL_MD_LINES"
echo ""

# Next steps
echo "======================================"
echo "Next Steps"
echo "======================================"
echo ""
echo "1. View baseline:   cat $BASELINE_FILE | jq ."
echo "2. Monitor changes: ./scripts/context_dashboard.sh"
echo "3. Check health:    ./scripts/weekly_health_check.sh"
echo ""
echo "Track improvements against this baseline over time."
echo ""
