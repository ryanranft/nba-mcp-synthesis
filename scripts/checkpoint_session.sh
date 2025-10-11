#!/usr/bin/env bash
#
# checkpoint_session.sh - Create session checkpoints for recovery
#
# Purpose: Save current session state for quick recovery
# Usage: ./scripts/checkpoint_session.sh [--name=NAME] [--restore=ID]
#
# Features:
#   - Save current git state
#   - Save session context
#   - Quick restore capability
#   - Minimal checkpoint files (<100 lines)

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CHECKPOINT_DIR="${PROJECT_ROOT}/.ai/checkpoints"
CHECKPOINT_NAME=""
RESTORE_ID=""
ACTION="create"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name=*)
            CHECKPOINT_NAME="${1#*=}"
            shift
            ;;
        --restore=*)
            RESTORE_ID="${1#*=}"
            ACTION="restore"
            shift
            ;;
        --list|-l)
            ACTION="list"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--name=NAME] [--restore=ID] [--list]"
            echo ""
            echo "Actions:"
            echo "  (default)       Create new checkpoint"
            echo "  --restore=ID    Restore from checkpoint"
            echo "  --list, -l      List all checkpoints"
            echo ""
            echo "Options:"
            echo "  --name=NAME     Custom name for checkpoint"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create checkpoint directory
mkdir -p "$CHECKPOINT_DIR"

# Action: List checkpoints
if [[ "$ACTION" == "list" ]]; then
    echo "======================================"
    echo "Available Checkpoints"
    echo "======================================"
    echo ""

    if [[ ! -d "$CHECKPOINT_DIR" ]] || [[ -z "$(ls -A "$CHECKPOINT_DIR" 2>/dev/null)" ]]; then
        echo "No checkpoints found"
        exit 0
    fi

    # List checkpoints sorted by date
    for checkpoint in "$CHECKPOINT_DIR"/*.md; do
        if [[ -f "$checkpoint" ]]; then
            local basename=$(basename "$checkpoint" .md)
            local timestamp=$(stat -f %Sm -t "%Y-%m-%d %H:%M:%S" "$checkpoint" 2>/dev/null || stat -c %y "$checkpoint" 2>/dev/null | cut -d' ' -f1-2)
            local size=$(wc -l < "$checkpoint")

            echo -e "${CYAN}$basename${NC}"
            echo "  Created: $timestamp"
            echo "  Size: $size lines"

            # Extract description if available
            local desc=$(grep "^**Description**:" "$checkpoint" 2>/dev/null | sed 's/\*\*Description\*\*: //' || echo "")
            if [[ -n "$desc" ]]; then
                echo "  Description: $desc"
            fi

            echo ""
        fi
    done

    exit 0
fi

# Action: Restore checkpoint
if [[ "$ACTION" == "restore" ]]; then
    echo "======================================"
    echo "Restore Checkpoint"
    echo "======================================"
    echo ""

    CHECKPOINT_FILE="$CHECKPOINT_DIR/${RESTORE_ID}.md"

    if [[ ! -f "$CHECKPOINT_FILE" ]]; then
        echo -e "${YELLOW}Checkpoint not found: $RESTORE_ID${NC}"
        echo ""
        echo "Available checkpoints:"
        ls -1 "$CHECKPOINT_DIR"/*.md 2>/dev/null | xargs -n1 basename | sed 's/\.md$//' || echo "  None"
        exit 1
    fi

    echo "Restoring from: $RESTORE_ID"
    echo ""

    # Display checkpoint content
    cat "$CHECKPOINT_FILE"

    echo ""
    echo -e "${GREEN}✓ Checkpoint displayed above${NC}"
    echo ""
    echo "To resume work:"
    echo "  1. Review the checkpoint information"
    echo "  2. Check git status: git status"
    echo "  3. Continue from the documented state"
    echo ""

    exit 0
fi

# Action: Create checkpoint
echo "======================================"
echo "Create Session Checkpoint"
echo "======================================"
echo ""

# Generate checkpoint ID
if [[ -z "$CHECKPOINT_NAME" ]]; then
    CHECKPOINT_ID="checkpoint_$(date +%Y%m%d_%H%M%S)"
else
    CHECKPOINT_ID="$CHECKPOINT_NAME"
fi

CHECKPOINT_FILE="$CHECKPOINT_DIR/${CHECKPOINT_ID}.md"

echo "Creating checkpoint: $CHECKPOINT_ID"
echo ""

# Gather information
GIT_BRANCH=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "Unknown")
GIT_COMMIT=$(git -C "$PROJECT_ROOT" log -1 --format="%h - %s" 2>/dev/null || echo "Unknown")
GIT_STATUS=$(git -C "$PROJECT_ROOT" status --short 2>/dev/null || echo "Unknown")
MODIFIED_FILES=$(echo "$GIT_STATUS" | grep "^ M" | awk '{print $2}' || echo "None")
UNTRACKED_FILES=$(echo "$GIT_STATUS" | grep "^??" | awk '{print $2}' || echo "None")

# Estimate current context
CONTEXT=0
if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
    CONTEXT=$((CONTEXT + $(wc -l < "$PROJECT_ROOT/.ai/current-session.md") * 20))
fi
if [[ -f "$PROJECT_ROOT/PROJECT_STATUS.md" ]]; then
    CONTEXT=$((CONTEXT + $(wc -l < "$PROJECT_ROOT/PROJECT_STATUS.md") * 20))
fi

# Create checkpoint file
cat > "$CHECKPOINT_FILE" <<EOF
# Checkpoint: $CHECKPOINT_ID

**Created**: $(date '+%Y-%m-%d %H:%M:%S')
**Description**: Session checkpoint for recovery
**Context Estimate**: $CONTEXT tokens

---

## Git State

**Branch**: $GIT_BRANCH
**Last Commit**: $GIT_COMMIT

**Modified Files**:
\`\`\`
$MODIFIED_FILES
\`\`\`

**Untracked Files**:
\`\`\`
$UNTRACKED_FILES
\`\`\`

---

## Current Session

**Session File**: .ai/current-session.md
EOF

# Include brief excerpt from current session if it exists
if [[ -f "$PROJECT_ROOT/.ai/current-session.md" ]]; then
    echo "" >> "$CHECKPOINT_FILE"
    echo "**Session Excerpt** (first 10 lines):" >> "$CHECKPOINT_FILE"
    echo "\`\`\`" >> "$CHECKPOINT_FILE"
    head -10 "$PROJECT_ROOT/.ai/current-session.md" >> "$CHECKPOINT_FILE"
    echo "\`\`\`" >> "$CHECKPOINT_FILE"
fi

# Add working context
cat >> "$CHECKPOINT_FILE" <<EOF

---

## Working Context

**Active Files**: $(echo "$MODIFIED_FILES" | wc -l | tr -d ' ') file(s) modified
**Next Steps**: [Resume from last commit and continue work]

---

## Recovery Instructions

1. **Check git status**: \`git status\`
2. **Review changes**: \`git diff\`
3. **Continue work**: Pick up from last documented state
4. **Update session**: \`./scripts/session_start.sh\`

---

*Checkpoint ID*: $CHECKPOINT_ID
*Restore with*: \`./scripts/checkpoint_session.sh --restore=$CHECKPOINT_ID\`
EOF

# Create symlink to latest
ln -sf "$CHECKPOINT_FILE" "$CHECKPOINT_DIR/latest.md"

echo -e "${GREEN}✓ Checkpoint created${NC}"
echo ""
echo "Checkpoint: $CHECKPOINT_ID"
echo "Location: .ai/checkpoints/${CHECKPOINT_ID}.md"
echo "Size: $(wc -l < "$CHECKPOINT_FILE") lines"
echo ""
echo "To restore:"
echo "  ./scripts/checkpoint_session.sh --restore=$CHECKPOINT_ID"
echo ""
echo "To view latest:"
echo "  cat .ai/checkpoints/latest.md"
echo ""
