#!/usr/bin/env bash
#
# auto_update_doc_map.sh - Automatically update DOCUMENTATION_MAP.md
#
# Purpose: Scan project for new documentation files and update the documentation map
# Usage: ./scripts/auto_update_doc_map.sh [--scan-only] [--add-missing]
#
# Features:
#   - Detects new documentation files not in map
#   - Suggests categories for new files
#   - Validates existing entries
#   - Maintains canonical location references

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOC_MAP="${PROJECT_ROOT}/docs/DOCUMENTATION_MAP.md"
SCAN_ONLY=0
ADD_MISSING=0

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --scan-only|-s)
            SCAN_ONLY=1
            shift
            ;;
        --add-missing|-a)
            ADD_MISSING=1
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--scan-only] [--add-missing]"
            echo ""
            echo "Options:"
            echo "  --scan-only, -s   Only scan and report, don't modify files"
            echo "  --add-missing, -a Add missing files to documentation map"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if documentation map exists
if [[ ! -f "$DOC_MAP" ]]; then
    echo -e "${RED}Error: Documentation map not found at $DOC_MAP${NC}"
    exit 1
fi

# Function to extract purpose/description from file
extract_purpose() {
    local file="$1"

    # Try purpose statement
    local purpose=$(grep -m 1 "^\*\*Purpose\*\*:" "$file" 2>/dev/null | sed 's/\*\*Purpose\*\*: //' || true)

    # Try first heading
    if [[ -z "$purpose" ]]; then
        purpose=$(grep -m 1 "^# " "$file" 2>/dev/null | sed 's/^# //' || true)
    fi

    # Default
    if [[ -z "$purpose" ]]; then
        purpose="Documentation file"
    fi

    echo "$purpose"
}

# Function to suggest category for file
suggest_category() {
    local filepath="$1"
    local basename=$(basename "$filepath")

    # Determine category based on location and name
    if [[ "$filepath" =~ project/status ]]; then
        echo "Project Status & Tracking"
    elif [[ "$filepath" =~ project/tracking ]]; then
        echo "Project Status & Tracking"
    elif [[ "$filepath" =~ project/metrics ]]; then
        echo "Project Status & Tracking"
    elif [[ "$filepath" =~ \.ai/daily|\.ai/monthly|\.ai/current ]]; then
        echo "Session Management"
    elif [[ "$filepath" =~ \.ai/permanent ]]; then
        echo "Session Management"
    elif [[ "$filepath" =~ docs/plans ]]; then
        echo "Planning & Strategy"
    elif [[ "$filepath" =~ docs/guides ]]; then
        echo "Guides & Documentation"
    elif [[ "$filepath" =~ docs/sprints ]]; then
        echo "Sprint History"
    elif [[ "$filepath" =~ docs/analysis ]]; then
        echo "Analysis & Research"
    elif [[ "$filepath" =~ docs/enhancements ]]; then
        echo "Enhancements & Future Work"
    elif [[ "$filepath" =~ docs/archive ]]; then
        echo "Archive & Historical"
    elif [[ "$basename" =~ PLAN|STRATEGY|ROADMAP ]]; then
        echo "Planning & Strategy"
    elif [[ "$basename" =~ GUIDE|TUTORIAL ]]; then
        echo "Guides & Documentation"
    elif [[ "$basename" =~ STATUS|TRACKER ]]; then
        echo "Project Status & Tracking"
    else
        echo "Documentation"
    fi
}

# Function to check if file is in documentation map
is_in_doc_map() {
    local filepath="$1"
    local relative_path="${filepath#$PROJECT_ROOT/}"

    grep -q "$relative_path" "$DOC_MAP" 2>/dev/null
}

# Function to extract topic name from filename
extract_topic_name() {
    local basename=$(basename "$1" .md)

    # Convert underscores and hyphens to spaces
    local name=$(echo "$basename" | tr '_-' ' ')

    # Convert to title case (simple version)
    echo "$name" | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1'
}

echo "======================================"
echo "Documentation Map Update"
echo "======================================"
echo ""

if [[ $SCAN_ONLY -eq 1 ]]; then
    echo -e "${CYAN}SCAN ONLY MODE - No files will be modified${NC}"
    echo ""
fi

# Scan for important documentation files
echo -e "${BLUE}Scanning for documentation files...${NC}"
echo ""

MISSING_FILES=()
EXISTING_FILES=()

# Key directories to scan
SCAN_DIRS=(
    "docs/guides"
    "docs/plans"
    "docs/sprints"
    "docs/analysis"
    "docs/enhancements"
    "project/status"
    "project/tracking"
    ".ai/permanent"
)

# Also scan root for important files
ROOT_PATTERNS=(
    "PROJECT_STATUS.md"
    "CONTEXT_OPTIMIZATION*.md"
    "START_HERE*.md"
    "QUICKSTART.md"
    "README.md"
)

# Check root files
for pattern in "${ROOT_PATTERNS[@]}"; do
    while IFS= read -r -d '' file; do
        if is_in_doc_map "$file"; then
            EXISTING_FILES+=("$file")
        else
            MISSING_FILES+=("$file")
        fi
    done < <(find "$PROJECT_ROOT" -maxdepth 1 -type f -name "$pattern" -print0 2>/dev/null || true)
done

# Check directory files
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

        if is_in_doc_map "$file"; then
            EXISTING_FILES+=("$file")
        else
            MISSING_FILES+=("$file")
        fi
    done < <(find "$PROJECT_ROOT/$dir" -type f -name "*.md" -print0 2>/dev/null || true)
done

# Report findings
echo "======================================"
echo "Scan Results"
echo "======================================"
echo ""
echo "Files in documentation map: ${#EXISTING_FILES[@]}"
echo "Files missing from map: ${#MISSING_FILES[@]}"
echo ""

if [[ ${#MISSING_FILES[@]} -eq 0 ]]; then
    echo -e "${GREEN}✓ All documentation files are mapped${NC}"
    echo ""
    exit 0
fi

# Show missing files
echo -e "${YELLOW}Missing Files:${NC}"
echo ""

declare -A category_files

for file in "${MISSING_FILES[@]}"; do
    local relative_path="${file#$PROJECT_ROOT/}"
    local category=$(suggest_category "$file")
    local topic=$(extract_topic_name "$file")
    local purpose=$(extract_purpose "$file")

    # Truncate purpose if too long
    if [[ ${#purpose} -gt 50 ]]; then
        purpose="${purpose:0:47}..."
    fi

    echo -e "${CYAN}File:${NC} $relative_path"
    echo -e "  ${BLUE}Suggested Category:${NC} $category"
    echo -e "  ${BLUE}Topic:${NC} $topic"
    echo -e "  ${BLUE}Purpose:${NC} $purpose"
    echo ""

    # Group by category for adding
    if [[ -z "${category_files[$category]}" ]]; then
        category_files[$category]="$file"
    else
        category_files[$category]="${category_files[$category]}|$file"
    fi
done

# If not adding missing files, exit here
if [[ $SCAN_ONLY -eq 1 || $ADD_MISSING -eq 0 ]]; then
    echo "======================================"
    echo "Next Steps"
    echo "======================================"
    echo ""
    echo "To add missing files to the documentation map:"
    echo "  1. Review the files above"
    echo "  2. Run: $0 --add-missing"
    echo ""
    echo "Or manually edit: $DOC_MAP"
    echo ""
    exit 0
fi

# Add missing files to documentation map
echo "======================================"
echo "Adding Missing Files"
echo "======================================"
echo ""

# Backup original
cp "$DOC_MAP" "${DOC_MAP}.backup"
echo -e "${GREEN}✓${NC} Created backup: ${DOC_MAP}.backup"

# For each category, add entries
for category in "${!category_files[@]}"; do
    echo -e "${BLUE}Adding files to category: $category${NC}"

    # Find the category section in the documentation map
    if ! grep -q "### $category" "$DOC_MAP"; then
        echo -e "${YELLOW}⚠${NC} Category '$category' not found in documentation map"
        echo "  Please add manually or create the category section"
        continue
    fi

    # For each file in this category
    IFS='|' read -ra files <<< "${category_files[$category]}"
    for file in "${files[@]}"; do
        local relative_path="${file#$PROJECT_ROOT/}"
        local topic=$(extract_topic_name "$file")
        local purpose=$(extract_purpose "$file")

        # Truncate purpose if too long
        if [[ ${#purpose} -gt 60 ]]; then
            purpose="${purpose:0:57}..."
        fi

        echo "  + $topic"

        # Create table entry
        local entry="| **${topic}** | [${relative_path}](../${relative_path}) | ${purpose} |"

        # Find insertion point (after category header, before next ###)
        local temp_file=$(mktemp)
        awk -v category="### $category" -v entry="$entry" '
            BEGIN { in_section=0; inserted=0 }
            /^### / {
                if (in_section && !inserted) {
                    print entry
                    inserted=1
                }
                in_section=0
            }
            $0 ~ "^"category {
                in_section=1
            }
            { print }
            END {
                if (in_section && !inserted) {
                    print entry
                }
            }
        ' "$DOC_MAP" > "$temp_file"

        mv "$temp_file" "$DOC_MAP"
    done
done

# Update last modified date
sed -i.tmp "s/\*\*Last Updated\*\*:.*/\*\*Last Updated\*\*: $(date '+%Y-%m-%d')/" "$DOC_MAP"
rm -f "${DOC_MAP}.tmp"

echo ""
echo -e "${GREEN}✓ Documentation map updated${NC}"
echo ""

# Show summary
echo "======================================"
echo "Summary"
echo "======================================"
echo ""
echo "Added ${#MISSING_FILES[@]} file(s) to documentation map"
echo "Backup saved: ${DOC_MAP}.backup"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff $DOC_MAP"
echo "  2. Verify entries are in correct categories"
echo "  3. Commit changes: git add $DOC_MAP && git commit -m 'docs: Update documentation map'"
echo ""
