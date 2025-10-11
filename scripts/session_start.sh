#!/bin/bash

# session_start.sh - Generate compact current-session.md for optimal context usage
# Usage: ./scripts/session_start.sh [--new-session] [--restore SESSION_ID] [--health-check]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
NEW_SESSION=false
RESTORE_SESSION=""
HEALTH_CHECK=false

for arg in "$@"; do
    case $arg in
        --new-session)
            NEW_SESSION=true
            ;;
        --restore=*)
            RESTORE_SESSION="${arg#*=}"
            ;;
        --health-check)
            HEALTH_CHECK=true
            ;;
        --help)
            echo "Usage: $0 [--new-session] [--restore=SESSION_ID] [--health-check] [--help]"
            echo ""
            echo "Options:"
            echo "  --new-session    Create a new daily session file"
            echo "  --restore=ID     Restore session from S3 (requires S3 setup)"
            echo "  --health-check   Run health checks and report issues"
            echo "  --help          Show this help message"
            exit 0
            ;;
    esac
done

# Detect project root (look for .ai directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Health check function
run_health_check() {
    echo -e "${BLUE}🔍 Running Health Checks${NC}"
    echo "================================"

    local issues=0

    # Check git status
    if ! git status >/dev/null 2>&1; then
        echo -e "${RED}❌ Git repository not found${NC}"
        issues=$((issues + 1))
    else
        echo -e "${GREEN}✅ Git repository OK${NC}"

        # Check for uncommitted changes
        local uncommitted=$(git status --porcelain | wc -l | tr -d ' ')
        if [ "$uncommitted" -gt 0 ]; then
            echo -e "${YELLOW}⚠️  $uncommitted uncommitted changes${NC}"
            echo "   Run 'git status' to see details"
        else
            echo -e "${GREEN}✅ No uncommitted changes${NC}"
        fi
    fi

    # Check .ai directory structure
    if [ ! -d ".ai" ]; then
        echo -e "${RED}❌ .ai directory not found${NC}"
        issues=$((issues + 1))
    else
        echo -e "${GREEN}✅ .ai directory exists${NC}"

        # Check subdirectories
        for subdir in daily monthly permanent archive; do
            if [ ! -d ".ai/$subdir" ]; then
                echo -e "${YELLOW}⚠️  .ai/$subdir directory missing${NC}"
                mkdir -p ".ai/$subdir"
                echo -e "${GREEN}✅ Created .ai/$subdir${NC}"
            fi
        done
    fi

    # Check S3 availability (optional)
    if command -v aws &> /dev/null; then
        if aws sts get-caller-identity >/dev/null 2>&1; then
            echo -e "${GREEN}✅ AWS CLI configured${NC}"
        else
            echo -e "${YELLOW}⚠️  AWS CLI not configured${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  AWS CLI not installed (S3 features unavailable)${NC}"
    fi

    # Check session archive script
    if [ -f "scripts/session_archive.sh" ]; then
        echo -e "${GREEN}✅ Session archive script available${NC}"
    else
        echo -e "${RED}❌ Session archive script missing${NC}"
        issues=$((issues + 1))
    fi

    # Check PROJECT_STATUS.md
    if [ -f "PROJECT_STATUS.md" ]; then
        echo -e "${GREEN}✅ PROJECT_STATUS.md exists${NC}"
    else
        echo -e "${RED}❌ PROJECT_STATUS.md missing${NC}"
        issues=$((issues + 1))
    fi

    echo ""
    echo -e "${BLUE}📁 File Management Check${NC}"
    echo "================================"

    # Check for archival candidates in root
    local completion_docs=$(find . -maxdepth 1 -name "*_COMPLETE.md" -o -name "*_VERIFICATION*.md" -o -name "*_REPORT.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$completion_docs" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Found $completion_docs completion document(s) in root${NC}"
        echo "   Consider archiving: ./scripts/auto_archive.sh --interactive"
    else
        echo -e "${GREEN}✅ No completion documents in root${NC}"
    fi

    # Check root directory markdown file count
    local root_md_count=$(ls -1 *.md 2>/dev/null | wc -l | tr -d ' ')
    if [ "$root_md_count" -gt 20 ]; then
        echo -e "${RED}⚠️  Root has $root_md_count markdown files (target: <20)${NC}"
        echo "   Run archive script: ./scripts/auto_archive.sh"
    elif [ "$root_md_count" -gt 15 ]; then
        echo -e "${YELLOW}⚠️  Root has $root_md_count markdown files (target: <15)${NC}"
        echo "   Consider running: ./scripts/auto_archive.sh --dry-run"
    else
        echo -e "${GREEN}✅ Root file count OK: $root_md_count files${NC}"
    fi

    # Summary
    echo ""
    if [ $issues -eq 0 ]; then
        echo -e "${GREEN}🎉 All health checks passed!${NC}"
    else
        echo -e "${RED}❌ $issues issues found${NC}"
        echo "   Review the issues above before starting your session"
    fi

    return $issues
}

# Restore session function
restore_session() {
    local session_id="$1"
    echo -e "${BLUE}📥 Restoring Session: $session_id${NC}"
    echo "================================"

    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found. Cannot restore from S3.${NC}"
        echo "   Install AWS CLI: brew install awscli"
        return 1
    fi

    # Check S3 bucket
    local s3_bucket="${NBA_MCP_S3_BUCKET:-nba-mcp-sessions}"
    if ! aws s3 ls "s3://$s3_bucket/" >/dev/null 2>&1; then
        echo -e "${RED}❌ S3 bucket '$s3_bucket' not accessible${NC}"
        echo "   Check your AWS credentials and bucket name"
        return 1
    fi

    # Try to restore from different locations
    local restored=false

    # Try daily sessions
    if aws s3 ls "s3://$s3_bucket/daily/$session_id" >/dev/null 2>&1; then
        echo -e "${GREEN}📥 Found in daily sessions${NC}"
        aws s3 cp "s3://$s3_bucket/daily/$session_id" ".ai/daily/"
        restored=true
    fi

    # Try monthly sessions
    if aws s3 ls "s3://$s3_bucket/monthly/$session_id" >/dev/null 2>&1; then
        echo -e "${GREEN}📥 Found in monthly sessions${NC}"
        aws s3 cp "s3://$s3_bucket/monthly/$session_id" ".ai/monthly/"
        restored=true
    fi

    # Try archive
    if aws s3 ls "s3://$s3_bucket/archive/$session_id" >/dev/null 2>&1; then
        echo -e "${GREEN}📥 Found in archive${NC}"
        aws s3 cp "s3://$s3_bucket/archive/$session_id" ".ai/archive/"
        restored=true
    fi

    if [ "$restored" = true ]; then
        echo -e "${GREEN}✅ Session restored successfully${NC}"
    else
        echo -e "${RED}❌ Session '$session_id' not found in S3${NC}"
        echo "   Available sessions:"
        aws s3 ls "s3://$s3_bucket/daily/" 2>/dev/null | head -10
        aws s3 ls "s3://$s3_bucket/monthly/" 2>/dev/null | head -10
        aws s3 ls "s3://$s3_bucket/archive/" 2>/dev/null | head -10
        return 1
    fi
}

# Handle different modes
if [ "$HEALTH_CHECK" = true ]; then
    run_health_check
    exit $?
fi

if [ -n "$RESTORE_SESSION" ]; then
    restore_session "$RESTORE_SESSION"
    exit $?
fi

echo -e "${BLUE}🚀 Starting New Session${NC}"
echo "================================"

# Run quick health check
echo -e "${BLUE}🔍 Quick Health Check${NC}"
if ! git status >/dev/null 2>&1; then
    echo -e "${RED}❌ Git repository not found${NC}"
    echo "   Run with --health-check for detailed diagnostics"
    exit 1
fi

# Check for uncommitted changes
uncommitted=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$uncommitted" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $uncommitted uncommitted changes${NC}"
    echo "   Consider committing changes before starting new session"
fi

# Create .ai directory if it doesn't exist
mkdir -p .ai/daily .ai/monthly .ai/permanent .ai/archive

# Get today's date
TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d\ %H:%M:%S)

# Count existing sessions today
SESSION_NUM=$(ls -1 .ai/daily/${TODAY}-session-*.md 2>/dev/null | wc -l | tr -d ' ')
SESSION_NUM=$((SESSION_NUM + 1))

# Create new daily session file if --new-session flag
if [ "$NEW_SESSION" = true ]; then
    DAILY_FILE=".ai/daily/${TODAY}-session-${SESSION_NUM}.md"
    echo -e "${GREEN}📝 Creating new daily session file: ${DAILY_FILE}${NC}"

    # Copy template or create basic structure
    if [ -f ".ai/daily/template.md" ]; then
        cp .ai/daily/template.md "$DAILY_FILE"
        # Replace template placeholders
        sed -i.bak "s/YYYY-MM-DD/${TODAY}/g" "$DAILY_FILE"
        sed -i.bak "s/Session**: N/Session**: ${SESSION_NUM}/g" "$DAILY_FILE"
        rm "${DAILY_FILE}.bak" 2>/dev/null || true
    fi
fi

# Generate current-session.md
echo -e "${BLUE}📊 Generating current-session.md...${NC}"

# Get git status info
GIT_STATUS=$(git status --short 2>/dev/null || echo "No git repo")
MODIFIED_COUNT=$(echo "$GIT_STATUS" | grep -c '^.M' || echo "0")
STAGED_COUNT=$(echo "$GIT_STATUS" | grep -c '^M' || echo "0")
UNTRACKED_COUNT=$(echo "$GIT_STATUS" | grep -c '^??' || echo "0")

# Get last 5 commits (compact format)
RECENT_COMMITS=$(git log --oneline -5 --no-decorate 2>/dev/null || echo "No commits")

# Get current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Get last session file
LAST_SESSION=$(ls -t .ai/daily/*.md 2>/dev/null | head -1)
LAST_SESSION_SUMMARY=""
if [ -n "$LAST_SESSION" ]; then
    # Extract "Next Session" section from last session if it exists
    LAST_SESSION_SUMMARY=$(grep -A 5 "## 🚀 Next Session" "$LAST_SESSION" 2>/dev/null | head -10 || echo "")
fi

# Check for PROJECT_MASTER_TRACKER.md metrics
if [ -f "PROJECT_MASTER_TRACKER.md" ]; then
    TOOLS_REGISTERED=$(grep -o "Total MCP Tools.*: [0-9]*" PROJECT_MASTER_TRACKER.md | head -1 || echo "Unknown")
    OVERALL_PROGRESS=$(grep -o "Overall.*: [0-9]*%" PROJECT_MASTER_TRACKER.md | head -1 || echo "Unknown")
else
    TOOLS_REGISTERED="Not tracked"
    OVERALL_PROGRESS="Not tracked"
fi

# Generate compact current-session.md (optimized for ~300 tokens)
cat > .ai/current-session.md << EOF
# Current Session State

**Generated**: ${NOW}
**Branch**: ${CURRENT_BRANCH}
**Modified**: ${MODIFIED_COUNT} | **Staged**: ${STAGED_COUNT} | **Untracked**: ${UNTRACKED_COUNT}

---

## 📝 Recent Commits

\`\`\`
$(echo "$RECENT_COMMITS" | head -3)
\`\`\`

---

## 📊 Status

- **${TOOLS_REGISTERED}**
- **${OVERALL_PROGRESS}**

---

## 📚 Quick Links

- **Full Status**: PROJECT_STATUS.md
- **Operations**: CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md  
- **Session Guide**: .ai/index.md

---

**Auto-Generated** by \`session_start.sh\` | **Context Cost**: ~300 tokens
EOF

echo -e "${GREEN}✅ current-session.md generated successfully${NC}"
echo ""
echo -e "${BLUE}📋 Session Summary:${NC}"
echo "  Branch: ${CURRENT_BRANCH}"
echo "  Modified: ${MODIFIED_COUNT} | Staged: ${STAGED_COUNT} | Untracked: ${UNTRACKED_COUNT}"
echo "  Last session: $(basename "$LAST_SESSION" .md 2>/dev/null || echo "None")"
echo ""
echo -e "${YELLOW}💡 Quick Start:${NC}"
echo "  Read context:  cat .ai/current-session.md"
echo "  View details:  cat ${LAST_SESSION:-PROJECT_MASTER_TRACKER.md}"
echo "  New session:   ./scripts/session_start.sh --new-session"
echo ""
echo -e "${GREEN}🎯 Ready to code!${NC}"
