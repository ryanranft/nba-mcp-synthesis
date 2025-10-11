#!/bin/bash

# update_current_session.sh - Quick update to current-session.md during active work
# Usage: ./scripts/update_current_session.sh [message]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detect project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Get message from argument
UPDATE_MSG="${1:-Updated session state}"

echo -e "${BLUE}🔄 Updating current session...${NC}"

# Get current timestamp
NOW=$(date +%Y-%m-%d\ %H:%M:%S)
TODAY=$(date +%Y-%m-%d)

# Get git status info
GIT_STATUS=$(git status --short 2>/dev/null || echo "No git repo")
MODIFIED_COUNT=$(echo "$GIT_STATUS" | grep -c '^.M' || echo "0")
STAGED_COUNT=$(echo "$GIT_STATUS" | grep -c '^M' || echo "0")
UNTRACKED_COUNT=$(echo "$GIT_STATUS" | grep -c '^??' || echo "0")

# Get last 3 commits (compact format)
RECENT_COMMITS=$(git log --oneline -3 --no-decorate 2>/dev/null || echo "No commits")

# Get current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Count current session number
SESSION_NUM=$(ls -1 .ai/daily/${TODAY}-session-*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$SESSION_NUM" -eq 0 ]; then
    SESSION_NUM=1
fi

# Check for PROJECT_MASTER_TRACKER.md metrics
if [ -f "PROJECT_MASTER_TRACKER.md" ]; then
    TOOLS_REGISTERED=$(grep -o "Total MCP Tools.*: [0-9]*" PROJECT_MASTER_TRACKER.md | head -1 || echo "Unknown")
    OVERALL_PROGRESS=$(grep -o "Overall.*: [0-9]*%" PROJECT_MASTER_TRACKER.md | head -1 || echo "Unknown")
else
    TOOLS_REGISTERED="Not tracked"
    OVERALL_PROGRESS="Not tracked"
fi

# Get last session file
LAST_SESSION=$(ls -t .ai/daily/*.md 2>/dev/null | head -1)

# Quick update to current-session.md (preserve manual sections if they exist)
cat > .ai/current-session.md << EOF
# Current Session State

**Generated**: ${NOW}
**Branch**: ${CURRENT_BRANCH}
**Session**: ${SESSION_NUM} (${TODAY})
**Last Update**: ${UPDATE_MSG}

---

## 🎯 Active Work

**Status**: In Progress

### Quick Stats
- Modified files: ${MODIFIED_COUNT}
- Staged files: ${STAGED_COUNT}
- Untracked files: ${UNTRACKED_COUNT}

---

## 📝 Recent Activity

### Last 3 Commits
\`\`\`
${RECENT_COMMITS}
\`\`\`

### Uncommitted Changes (Recent)
\`\`\`
$(echo "$GIT_STATUS" | head -10)
$(if [ $(echo "$GIT_STATUS" | wc -l) -gt 10 ]; then echo "... ($(( $(echo "$GIT_STATUS" | wc -l) - 10 )) more)"; fi)
\`\`\`

---

## 📊 Project Status

**${TOOLS_REGISTERED}**
**${OVERALL_PROGRESS}**

---

## 🔍 Context

**Current Session**: ${TODAY}-session-${SESSION_NUM}
**Detailed Log**: .ai/daily/${TODAY}-session-${SESSION_NUM}.md

---

**Auto-Generated**: ${NOW}
**Context Cost**: ~80 tokens (optimized for quick status checks)
EOF

echo -e "${GREEN}✅ Current session updated${NC}"
echo ""
echo "  Branch: ${CURRENT_BRANCH}"
echo "  Changes: Modified ${MODIFIED_COUNT} | Staged ${STAGED_COUNT} | Untracked ${UNTRACKED_COUNT}"
echo ""
echo -e "${BLUE}💡 View: cat .ai/current-session.md${NC}"
