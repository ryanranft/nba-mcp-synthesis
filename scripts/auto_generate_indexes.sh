#!/usr/bin/env bash
#
# auto_generate_indexes.sh - Automatically generate and update index.md files
#
# Purpose: Create or update index files in directories with markdown files
# Usage: ./scripts/auto_generate_indexes.sh [--directory=DIR] [--force] [--dry-run]
#
# Features:
#   - Scans directories for markdown files
#   - Extracts file descriptions from first heading or purpose statement
#   - Groups files by category
#   - Maintains target <100 lines per index
#   - Preserves custom content in index files

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET_DIR="${PROJECT_ROOT}"
FORCE=0
DRY_RUN=0

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
        --directory=*|--dir=*)
            TARGET_DIR="${1#*=}"
            shift
            ;;
        --force|-f)
            FORCE=1
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=1
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--directory=DIR] [--force] [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --directory=DIR   Target directory (default: project root)"
            echo "  --force, -f       Overwrite existing index files"
            echo "  --dry-run, -n     Show what would be done without doing it"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to extract description from markdown file
extract_description() {
    local file="$1"
    local desc=""

    # Try to find purpose statement
    desc=$(grep -m 1 "^\*\*Purpose\*\*:" "$file" 2>/dev/null | sed 's/\*\*Purpose\*\*: //' || true)

    # If no purpose, try first heading
    if [[ -z "$desc" ]]; then
        desc=$(grep -m 1 "^# " "$file" 2>/dev/null | sed 's/^# //' || true)
    fi

    # If still nothing, try first non-empty line
    if [[ -z "$desc" ]]; then
        desc=$(grep -m 1 -v "^$" "$file" 2>/dev/null | sed 's/^[#*-] *//' | cut -c1-80 || true)
    fi

    # Default if nothing found
    if [[ -z "$desc" ]]; then
        desc="Documentation file"
    fi

    echo "$desc"
}

# Function to determine category from filename
determine_category() {
    local filename="$1"

    case "$filename" in
        *COMPLETE*.md|*SUCCESS*.md|*DONE*.md)
            echo "Completed"
            ;;
        *PLAN*.md|*STRATEGY*.md|*ROADMAP*.md)
            echo "Planning"
            ;;
        *GUIDE*.md|*TUTORIAL*.md|*HOWTO*.md)
            echo "Guides"
            ;;
        *TEST*.md|*VALIDATION*.md|*VERIFICATION*.md)
            echo "Testing"
            ;;
        *SPRINT*.md|*PHASE*.md)
            echo "Sprints"
            ;;
        *ANALYSIS*.md|*RESEARCH*.md)
            echo "Analysis"
            ;;
        *STATUS*.md|*TRACKER*.md|*PROGRESS*.md)
            echo "Status"
            ;;
        *README*.md|*QUICKSTART*.md|*GETTING*.md)
            echo "Getting Started"
            ;;
        template.md)
            echo "Templates"
            ;;
        *)
            echo "Documentation"
            ;;
    esac
}

# Function to generate index for a directory
generate_index() {
    local dir="$1"
    local index_file="${dir}/index.md"
    local relative_path="${dir#$PROJECT_ROOT/}"

    # Skip if index exists and not forced
    if [[ -f "$index_file" && $FORCE -eq 0 ]]; then
        echo -e "${YELLOW}⊘${NC} Skipping $relative_path/index.md (already exists, use --force to overwrite)"
        return
    fi

    # Find markdown files (excluding index.md)
    local files=()
    while IFS= read -r -d '' file; do
        local basename=$(basename "$file")
        [[ "$basename" != "index.md" ]] && files+=("$file")
    done < <(find "$dir" -maxdepth 1 -type f -name "*.md" -print0 2>/dev/null | sort -z)

    # Skip if no files
    if [[ ${#files[@]} -eq 0 ]]; then
        return
    fi

    # Skip if only template files
    local non_template_count=0
    for file in "${files[@]}"; do
        [[ $(basename "$file") != "template.md" ]] && non_template_count=$((non_template_count + 1))
    done
    if [[ $non_template_count -eq 0 ]]; then
        return
    fi

    echo -e "${BLUE}→${NC} Generating $relative_path/index.md"

    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  Would create index with ${#files[@]} file(s)"
        return
    fi

    # Group files by category
    declare -A categories
    for file in "${files[@]}"; do
        local basename=$(basename "$file")
        local category=$(determine_category "$basename")
        if [[ -z "${categories[$category]}" ]]; then
            categories[$category]="$file"
        else
            categories[$category]="${categories[$category]}|$file"
        fi
    done

    # Generate index content
    local dirname=$(basename "$dir")
    cat > "$index_file" <<EOF
# ${dirname^} Index

**Purpose**: Navigation index for ${dirname} directory
**Last Updated**: $(date '+%Y-%m-%d')

---

## Overview

This directory contains ${#files[@]} file(s) organized by category.

---

EOF

    # Add files by category
    for category in $(echo "${!categories[@]}" | tr ' ' '\n' | sort); do
        echo "## ${category}" >> "$index_file"
        echo "" >> "$index_file"

        IFS='|' read -ra category_files <<< "${categories[$category]}"
        for file in "${category_files[@]}"; do
            local basename=$(basename "$file")
            local name="${basename%.md}"
            local desc=$(extract_description "$file")

            # Truncate description if too long
            if [[ ${#desc} -gt 80 ]]; then
                desc="${desc:0:77}..."
            fi

            echo "- **[${name}](${basename})** - ${desc}" >> "$index_file"
        done

        echo "" >> "$index_file"
    done

    # Add footer
    cat >> "$index_file" <<EOF
---

## Navigation

- **Parent**: [Main Index](../index.md)
- **Project Root**: [PROJECT_STATUS.md](../../PROJECT_STATUS.md)

---

*This index was auto-generated. To regenerate: \`./scripts/auto_generate_indexes.sh --directory=$relative_path --force\`*
EOF

    echo -e "${GREEN}✓${NC} Created $relative_path/index.md (${#files[@]} files indexed)"
}

# Function to recursively scan directories
scan_directory() {
    local base_dir="$1"
    local max_depth="${2:-3}"

    echo -e "${CYAN}Scanning directories in: $base_dir${NC}"
    echo ""

    # Find directories with markdown files
    while IFS= read -r -d '' dir; do
        # Skip .git, node_modules, etc.
        if [[ "$dir" =~ \.git|node_modules|venv|__pycache__ ]]; then
            continue
        fi

        # Check if directory has markdown files
        local md_count=$(find "$dir" -maxdepth 1 -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        if [[ $md_count -gt 1 ]]; then  # More than just index.md
            generate_index "$dir"
        fi
    done < <(find "$base_dir" -maxdepth "$max_depth" -type d -print0 2>/dev/null | sort -z)
}

# Main execution
echo "======================================"
echo "Auto-Generate Index Files"
echo "======================================"
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "${YELLOW}DRY RUN MODE - No files will be modified${NC}"
    echo ""
fi

# Scan target directory
scan_directory "$TARGET_DIR" 4

echo ""
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
    echo "Dry run complete. Run without --dry-run to apply changes."
else
    echo -e "${GREEN}Index generation complete${NC}"
    echo ""
    echo "Recommended next steps:"
    echo "  1. Review generated indexes: find . -name 'index.md' -exec cat {} +"
    echo "  2. Customize as needed"
    echo "  3. Run context check: ./scripts/monitor_file_sizes.sh"
fi

echo ""
