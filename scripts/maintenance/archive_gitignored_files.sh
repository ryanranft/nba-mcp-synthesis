#!/bin/bash
# Archive .gitignored documentation files with git SHA

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_NAME="nba-mcp-synthesis"

# Archive base
ARCHIVE_BASE="${ARCHIVE_BASE:-$HOME/nba-mcp-archives}"

# Get current git info
cd "$PROJECT_DIR"
CURRENT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT_DATE=$(git log -1 --format=%ci)
COMMIT_MSG=$(git log -1 --format=%s)

# Create archive directory structure
ARCHIVE_DIR="$ARCHIVE_BASE/$CURRENT_SHA"
mkdir -p "$ARCHIVE_DIR"

echo "📦 Archiving .gitignored files for commit: $SHORT_SHA"
echo "📁 Archive location: $ARCHIVE_DIR"

# Create git metadata file
cat > "$ARCHIVE_DIR/git-info.txt" << EOF
=================================================================
GIT SNAPSHOT METADATA
=================================================================

Project:      $PROJECT_NAME
Full SHA:     $CURRENT_SHA
Short SHA:    $SHORT_SHA
Branch:       $BRANCH
Commit Date:  $COMMIT_DATE
Commit Msg:   $COMMIT_MSG

=================================================================
ARCHIVED FILES
=================================================================

EOF

# Files to archive (from .gitignore)
FILES=(
    "IMPLEMENTATION_COMPLETE.md"
    "DEPLOYMENT_SUCCESS.md"
    "CONFIGURATION_COMPLETE_SUMMARY.md"
    "SETUP_COMPLETE_SUMMARY.md"
    "ALL_CONNECTORS_DEPLOYMENT_SUMMARY.md"
    "CONNECTORS_IMPLEMENTATION_COMPLETE.md"
    "FINAL_VERIFICATION_SUMMARY.md"
    "GREAT_EXPECTATIONS_VERIFICATION_COMPLETE.md"
    "LATEST_STATUS_UPDATE.md"
    "PYCHARM_INTEGRATION_SUMMARY.md"
    "TESTING_RESULTS.md"
    "QUICKSTART.md"
    "CLAUDE_DESKTOP_NEXT_STEPS.md"
    "OLLAMA_PRIMARY_WORKFLOW.md"
)

# Test result files
TEST_FILES=(
    "test_results.txt"
    "test_results_complete.txt"
    "final_test_report.txt"
)

# Archive each file if it exists
COUNT=0
for file in "${FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        cp "$PROJECT_DIR/$file" "$ARCHIVE_DIR/" || true
        echo "✅ $file" >> "$ARCHIVE_DIR/git-info.txt"
        echo "  ✓ Archived: $file"
        COUNT=$((COUNT + 1))
    fi
done

# Archive test files
for file in "${TEST_FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        cp "$PROJECT_DIR/$file" "$ARCHIVE_DIR/" || true
        echo "✅ $file" >> "$ARCHIVE_DIR/git-info.txt"
        echo "  ✓ Archived: $file"
        COUNT=$((COUNT + 1))
    fi
done

# Archive planning docs to subdirectory
if [ -d "$PROJECT_DIR/docs/planning/ARCHIVED" ]; then
    mkdir -p "$ARCHIVE_DIR/planning"
    for doc in "$PROJECT_DIR/docs/planning/ARCHIVED"/*.md; do
        if [ -f "$doc" ]; then
            filename=$(basename "$doc")
            cp "$doc" "$ARCHIVE_DIR/planning/" || true
            echo "✅ planning/$filename" >> "$ARCHIVE_DIR/git-info.txt"
            echo "  ✓ Archived: planning/$filename"
            COUNT=$((COUNT + 1))
        fi
    done
fi

# Archive log files (but not huge ones)
if ls "$PROJECT_DIR"/logs/*.log 1> /dev/null 2>&1; then
    mkdir -p "$ARCHIVE_DIR/logs"
    for logfile in "$PROJECT_DIR"/logs/*.log; do
        if [ -f "$logfile" ]; then
            filename=$(basename "$logfile")
            # Only archive small log files (< 1MB)
            size=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null)
            if [ "$size" -lt 1048576 ]; then
                cp "$logfile" "$ARCHIVE_DIR/logs/"
                echo "✅ logs/$filename" >> "$ARCHIVE_DIR/git-info.txt"
                echo "  ✓ Archived: logs/$filename"
                ((COUNT++))
            fi
        fi
    done
fi

# Footer in git-info.txt
cat >> "$ARCHIVE_DIR/git-info.txt" << EOF

=================================================================
Total files archived: $COUNT
Archive created: $(date)
=================================================================
EOF

# Update master index
INDEX_FILE="$ARCHIVE_BASE/README.md"
if [ ! -f "$INDEX_FILE" ]; then
    cat > "$INDEX_FILE" << EOF
# NBA MCP Synthesis Archive - Gitignored Files

This archive contains \`.gitignored\` documentation files organized by git commit SHA.

Each folder corresponds to a specific git commit and contains:
- \`git-info.txt\` - Git metadata (SHA, date, message)
- Status and completion documentation files
- Test result files
- Planning documents
- Small log files

## How to Use

1. Find the git commit SHA from your project history: \`git log --oneline\`
2. Navigate to the corresponding folder: \`cd ~/nba-mcp-archives/<sha>/\`
3. All gitignored documentation files from that commit are preserved

## Folders

EOF
fi

# Add entry to index if not already present
if ! grep -q "$CURRENT_SHA" "$INDEX_FILE"; then
    echo "- **$SHORT_SHA** - $BRANCH - $(date +%Y-%m-%d) - $COMMIT_MSG ($COUNT files)" >> "$INDEX_FILE"
    echo "  📝 Updated archive index"
fi

echo ""
echo "✅ Archive complete!"
echo "📂 Location: $ARCHIVE_DIR"
echo "📊 Files archived: $COUNT"

# Commit to local git repo (NEVER push to GitHub - stays local only)
if [ -d "$ARCHIVE_BASE/.git" ]; then
    cd "$ARCHIVE_BASE"
    git add . > /dev/null 2>&1
    if git commit -m "Archive commit $SHORT_SHA from nba-mcp-synthesis: $COMMIT_MSG" --quiet 2>/dev/null; then
        echo "  ✓ Committed to local archive git repo"
    fi
    cd "$PROJECT_DIR"
fi

echo ""
echo "To view later: ls $ARCHIVE_DIR"
echo "To see all archives: cat $INDEX_FILE"
