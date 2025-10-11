#!/usr/bin/env bash
#
# auto_archive.sh - Automatically archive old/completed documentation files
#
# Purpose: Move completed, old, or inactive files to archive based on rules
# Usage: ./scripts/auto_archive.sh [--age=DAYS] [--dry-run] [--interactive]
#
# Features:
#   - Archives files based on age (default: 30 days since last modification)
#   - Archives completion documents (*_COMPLETE.md, *_SUCCESS.md, etc.)
#   - Archives old sprint documents
#   - Configurable retention policies
#   - Creates archive index automatically
#   - Preserves git history

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ARCHIVE_BASE="${PROJECT_ROOT}/docs/archive"
AGE_THRESHOLD=30  # Days
DRY_RUN=0
INTERACTIVE=0

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Counters
ARCHIVED_COUNT=0
SKIPPED_COUNT=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --age=*)
            AGE_THRESHOLD="${1#*=}"
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=1
            shift
            ;;
        --interactive|-i)
            INTERACTIVE=1
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--age=DAYS] [--dry-run] [--interactive]"
            echo ""
            echo "Options:"
            echo "  --age=DAYS        Archive files older than DAYS (default: 30)"
            echo "  --dry-run, -n     Show what would be archived without doing it"
            echo "  --interactive, -i Prompt before archiving each file"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Archive Rules:"
            echo "  1. Files with *_COMPLETE.md, *_SUCCESS.md, *_DONE.md patterns"
            echo "  2. Files not modified in AGE_THRESHOLD days"
            echo "  3. Old sprint documents (completed sprints)"
            echo "  4. Session summary files older than 60 days"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to determine if file should be archived
should_archive() {
    local file="$1"
    local basename=$(basename "$file")
    local age_days=0

    # Get file age in days
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        age_days=$(( ( $(date +%s) - $(stat -f %m "$file") ) / 86400 ))
    else
        # Linux
        age_days=$(( ( $(date +%s) - $(stat -c %Y "$file") ) / 86400 ))
    fi

    # Rule 1: Completion documents (always archive)
    if [[ "$basename" =~ _COMPLETE\.md$|_SUCCESS\.md$|_DONE\.md$|_FINISHED\.md$ ]]; then
        echo "completion"
        return 0
    fi

    # Rule 2: Session summaries (archive after 60 days)
    if [[ "$basename" =~ _SESSION.*\.md$|SESSION.*SUMMARY\.md$ ]] && [[ $age_days -gt 60 ]]; then
        echo "session"
        return 0
    fi

    # Rule 3: Old sprint documents (archive after 30 days if not active)
    if [[ "$basename" =~ SPRINT_[0-9]+.*\.md$ ]] && [[ $age_days -gt $AGE_THRESHOLD ]]; then
        # Check if it's a completion document or old plan
        if [[ "$basename" =~ COMPLETE|PLAN|STATUS ]] && [[ $age_days -gt $AGE_THRESHOLD ]]; then
            echo "sprint"
            return 0
        fi
    fi

    # Rule 4: Old documentation (archive after AGE_THRESHOLD days)
    if [[ $age_days -gt $AGE_THRESHOLD ]]; then
        # Skip if in certain protected locations
        if [[ "$file" =~ /permanent/|/guides/|PROJECT_STATUS|DOCUMENTATION_MAP|index\.md$ ]]; then
            return 1
        fi
        echo "old"
        return 0
    fi

    return 1
}

# Function to determine archive subdirectory
get_archive_subdir() {
    local file="$1"
    local reason="$2"
    local month=$(date -r "$file" '+%Y-%m' 2>/dev/null || date '+%Y-%m')

    case "$reason" in
        completion)
            echo "${month}/completion"
            ;;
        session)
            echo "${month}/sessions"
            ;;
        sprint)
            echo "${month}/sprints"
            ;;
        old)
            if [[ "$file" =~ /analysis/ ]]; then
                echo "${month}/analysis"
            elif [[ "$file" =~ /plans/ ]]; then
                echo "${month}/plans"
            else
                echo "${month}/docs"
            fi
            ;;
        *)
            echo "${month}/misc"
            ;;
    esac
}

# Function to archive a file
archive_file() {
    local file="$1"
    local reason="$2"
    local relative_path="${file#$PROJECT_ROOT/}"
    local basename=$(basename "$file")
    local subdir=$(get_archive_subdir "$file" "$reason")
    local archive_dir="${ARCHIVE_BASE}/${subdir}"
    local dest="${archive_dir}/${basename}"

    # Check if interactive mode
    if [[ $INTERACTIVE -eq 1 ]]; then
        echo -e "${YELLOW}?${NC} Archive $relative_path? (reason: $reason) [y/N] "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}⊘${NC} Skipped"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            return
        fi
    fi

    if [[ $DRY_RUN -eq 1 ]]; then
        echo -e "${CYAN}→${NC} Would archive: $relative_path"
        echo "  Destination: ${dest#$PROJECT_ROOT/}"
        echo "  Reason: $reason"
        ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))
        return
    fi

    # Create archive directory
    mkdir -p "$archive_dir"

    # Move file using git (preserves history)
    if git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
        git -C "$PROJECT_ROOT" mv "$file" "$dest" 2>/dev/null || mv "$file" "$dest"
    else
        mv "$file" "$dest"
    fi

    echo -e "${GREEN}✓${NC} Archived: $relative_path → ${dest#$PROJECT_ROOT/}"
    ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))

    # Add to archive index
    local month=$(echo "$subdir" | cut -d'/' -f1)
    local archive_index="${ARCHIVE_BASE}/${month}/index.md"

    if [[ ! -f "$archive_index" ]]; then
        cat > "$archive_index" <<EOF
# Archive Index - $(echo "$month" | sed 's/-/ /')

**Last Updated**: $(date '+%Y-%m-%d')

---

## Archived Files

EOF
    fi

    # Add entry if not already present
    if ! grep -q "$basename" "$archive_index"; then
        echo "- **${basename}** (archived $(date '+%Y-%m-%d'), reason: $reason)" >> "$archive_index"
    fi
}

# Main execution
echo "======================================"
echo "Auto-Archive Documentation"
echo "======================================"
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "${YELLOW}DRY RUN MODE - No files will be moved${NC}"
    echo ""
fi

echo "Configuration:"
echo "  Age threshold: $AGE_THRESHOLD days"
echo "  Interactive: $([ $INTERACTIVE -eq 1 ] && echo 'Yes' || echo 'No')"
echo ""

# Scan for files to archive
echo -e "${BLUE}Scanning for files to archive...${NC}"
echo ""

# Directories to scan
SCAN_DIRS=(
    "docs/sprints"
    "docs/plans"
    "docs/analysis"
    "docs/enhancements"
)

# Also scan root for completion documents
ROOT_PATTERNS=(
    "*_COMPLETE.md"
    "*_SUCCESS.md"
    "*_DONE.md"
    "*_SESSION*.md"
    "SESSION_*.md"
)

# Check root files
for pattern in "${ROOT_PATTERNS[@]}"; do
    while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            local reason=$(should_archive "$file" || true)
            if [[ -n "$reason" && "$reason" != "1" ]]; then
                archive_file "$file" "$reason"
            fi
        fi
    done < <(find "$PROJECT_ROOT" -maxdepth 1 -type f -name "$pattern" 2>/dev/null || true)
done

# Check directories
for dir in "${SCAN_DIRS[@]}"; do
    if [[ ! -d "$PROJECT_ROOT/$dir" ]]; then
        continue
    fi

    while IFS= read -r -d '' file; do
        # Skip index files and templates
        local basename=$(basename "$file")
        if [[ "$basename" == "index.md" || "$basename" == "template.md" ]]; then
            continue
        fi

        # Skip if already in archive
        if [[ "$file" =~ /archive/ ]]; then
            continue
        fi

        local reason=$(should_archive "$file" || true)
        if [[ -n "$reason" && "$reason" != "1" ]]; then
            archive_file "$file" "$reason"
        fi
    done < <(find "$PROJECT_ROOT/$dir" -type f -name "*.md" -print0 2>/dev/null || true)
done

# Summary
echo ""
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
    echo "Would archive: $ARCHIVED_COUNT file(s)"
    echo ""
    echo "To apply changes, run without --dry-run:"
    echo "  $0"
else
    echo "Archived: $ARCHIVED_COUNT file(s)"
    echo "Skipped: $SKIPPED_COUNT file(s)"
    echo ""

    if [[ $ARCHIVED_COUNT -gt 0 ]]; then
        echo "Archive location: ${ARCHIVE_BASE#$PROJECT_ROOT/}"
        echo ""
        echo "Next steps:"
        echo "  1. Review archives: ls -la ${ARCHIVE_BASE#$PROJECT_ROOT/}"
        echo "  2. Update .gitignore if needed"
        echo "  3. Commit changes: git add . && git commit -m 'docs: Archive old documentation'"
        echo "  4. Update documentation map: ./scripts/auto_update_doc_map.sh"
    else
        echo -e "${GREEN}No files needed archiving${NC}"
    fi
fi

echo ""
