#!/bin/bash

# audit_cross_references.sh - Find duplicated content across documentation
# Usage: ./scripts/audit_cross_references.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🔍 Auditing Cross-References${NC}"
echo "================================"

# Create temporary directory for analysis
TEMP_DIR=$(mktemp -d)
AUDIT_REPORT="$TEMP_DIR/audit_report.md"

# Function to extract text content from markdown
extract_content() {
    local file="$1"
    # Remove markdown syntax, headers, links, and code blocks
    sed -E 's/^#+ .*$//g; s/\[([^\]]*)\]\([^)]*\)/\1/g; s/```[^`]*```//g; s/`[^`]*`//g; s/^\*+ //g; s/^- //g' "$file" | \
    grep -v '^$' | \
    tr -d '\n' | \
    tr '[:upper:]' '[:lower:]' | \
    sed 's/[^a-z0-9 ]/ /g' | \
    sed 's/  */ /g' | \
    sed 's/^ *//g; s/ *$//g'
}

# Function to find similar content
find_similar_content() {
    local threshold="${1:-80}"  # Similarity threshold (percentage)
    local min_length="${2:-50}"  # Minimum content length

    echo -e "\n${BLUE}🔍 Finding Similar Content (${threshold}% similarity, min ${min_length} chars)${NC}"

    # Create content database
    local content_db="$TEMP_DIR/content_db.txt"
    local file_db="$TEMP_DIR/file_db.txt"

    echo "File,Content" > "$content_db"

    # Process all markdown files
    find . -name "*.md" -type f | grep -v ".git" | while read -r file; do
        if [ -f "$file" ]; then
            local content=$(extract_content "$file")
            local content_length=${#content}

            if [ "$content_length" -ge "$min_length" ]; then
                echo "$file,$content" >> "$content_db"
                echo "$file" >> "$file_db"
            fi
        fi
    done

    # Find duplicates using simple similarity
    local duplicates_found=0

    while IFS=',' read -r file1 content1; do
        if [ "$file1" = "File" ]; then continue; fi

        while IFS=',' read -r file2 content2; do
            if [ "$file2" = "File" ] || [ "$file1" = "$file2" ]; then continue; fi

            # Calculate similarity (simple word overlap)
            local words1=$(echo "$content1" | tr ' ' '\n' | sort | uniq)
            local words2=$(echo "$content2" | tr ' ' '\n' | sort | uniq)
            local common_words=$(comm -12 <(echo "$words1") <(echo "$words2") | wc -l)
            local total_words=$(comm -12 <(echo "$words1") <(echo "$words2") | wc -l)
            local unique_words=$(comm -3 <(echo "$words1") <(echo "$words2") | wc -l)
            local similarity=$((common_words * 100 / (common_words + unique_words)))

            if [ "$similarity" -ge "$threshold" ]; then
                echo -e "${YELLOW}⚠️  Similar content found (${similarity}%):${NC}"
                echo "   File 1: $file1"
                echo "   File 2: $file2"
                echo "   Common words: $common_words"
                echo ""
                duplicates_found=$((duplicates_found + 1))
            fi
        done < "$content_db"
    done < "$content_db"

    if [ "$duplicates_found" -eq 0 ]; then
        echo -e "${GREEN}✅ No significant duplicates found${NC}"
    else
        echo -e "${RED}❌ Found $duplicates_found potential duplicates${NC}"
    fi
}

# Function to find specific duplicated topics
find_duplicated_topics() {
    echo -e "\n${BLUE}🔍 Finding Specific Duplicated Topics${NC}"

    # Common topics to check for duplication
    local topics=(
        "tool registration"
        "sprint status"
        "session management"
        "context optimization"
        "MCP tools"
        "project status"
        "deployment"
        "testing"
        "setup"
        "configuration"
    )

    local total_duplicates=0

    for topic in "${topics[@]}"; do
        echo -e "\n${YELLOW}Checking topic: $topic${NC}"

        local files_with_topic=()
        while IFS= read -r file; do
            if grep -qi "$topic" "$file" 2>/dev/null; then
                files_with_topic+=("$file")
            fi
        done < <(find . -name "*.md" -type f | grep -v ".git")

        local count=${#files_with_topic[@]}
        if [ "$count" -gt 3 ]; then
            echo -e "${RED}❌ Topic '$topic' found in $count files:${NC}"
            for file in "${files_with_topic[@]}"; do
                echo "   - $file"
            done
            total_duplicates=$((total_duplicates + 1))
        elif [ "$count" -gt 1 ]; then
            echo -e "${YELLOW}⚠️  Topic '$topic' found in $count files:${NC}"
            for file in "${files_with_topic[@]}"; do
                echo "   - $file"
            done
        else
            echo -e "${GREEN}✅ Topic '$topic' found in $count file(s)${NC}"
        fi
    done

    echo -e "\n${BLUE}📊 Topic Duplication Summary${NC}"
    echo "Total topics with potential duplication: $total_duplicates"
}

# Function to analyze link patterns
analyze_links() {
    echo -e "\n${BLUE}🔍 Analyzing Link Patterns${NC}"

    local link_report="$TEMP_DIR/link_report.txt"
    echo "File,Link,Target,Status" > "$link_report"

    local total_links=0
    local broken_links=0
    local internal_links=0
    local external_links=0

    find . -name "*.md" -type f | grep -v ".git" | while read -r file; do
        if [ -f "$file" ]; then
            # Extract links from markdown
            grep -o '\[[^\]]*\]\([^)]*\)' "$file" | while read -r link; do
                local link_text=$(echo "$link" | sed 's/\[\([^\]]*\)\].*/\1/')
                local link_target=$(echo "$link" | sed 's/.*(\([^)]*\)).*/\1/')

                total_links=$((total_links + 1))

                # Check if it's an internal or external link
                if [[ "$link_target" =~ ^(http|https|ftp):// ]]; then
                    external_links=$((external_links + 1))
                    echo "$file,$link_text,$link_target,external" >> "$link_report"
                else
                    internal_links=$((internal_links + 1))

                    # Check if internal link exists
                    local target_file=""
                    if [[ "$link_target" =~ ^\./ ]]; then
                        target_file="$PROJECT_ROOT/${link_target#./}"
                    elif [[ "$link_target" =~ ^/ ]]; then
                        target_file="$link_target"
                    else
                        target_file="$PROJECT_ROOT/$link_target"
                    fi

                    if [ -f "$target_file" ]; then
                        echo "$file,$link_text,$link_target,valid" >> "$link_report"
                    else
                        echo "$file,$link_text,$link_target,broken" >> "$link_report"
                        broken_links=$((broken_links + 1))
                    fi
                fi
            done
        fi
    done

    echo -e "${GREEN}📊 Link Analysis Summary${NC}"
    echo "Total links: $total_links"
    echo "Internal links: $internal_links"
    echo "External links: $external_links"
    echo "Broken links: $broken_links"

    if [ "$broken_links" -gt 0 ]; then
        echo -e "${RED}❌ Found $broken_links broken links${NC}"
        echo "Broken links:"
        grep "broken" "$link_report" | while IFS=',' read -r file link_text link_target status; do
            echo "   $file: $link_text -> $link_target"
        done
    else
        echo -e "${GREEN}✅ No broken links found${NC}"
    fi
}

# Function to generate recommendations
generate_recommendations() {
    echo -e "\n${BLUE}💡 Recommendations${NC}"
    echo "================================"

    echo -e "\n${YELLOW}1. Create Canonical Documentation${NC}"
    echo "   - Create docs/DOCUMENTATION_MAP.md"
    echo "   - Define single source of truth for each topic"
    echo "   - Replace duplicates with cross-references"

    echo -e "\n${YELLOW}2. Refactor High-Duplication Topics${NC}"
    echo "   - Tool registration process"
    echo "   - Sprint status information"
    echo "   - Session management details"
    echo "   - Context optimization guide"

    echo -e "\n${YELLOW}3. Implement Cross-Reference Strategy${NC}"
    echo "   - Use 'See [Topic](link) for details' pattern"
    echo "   - Create topic-specific index files"
    echo "   - Maintain single authoritative source"

    echo -e "\n${YELLOW}4. Regular Maintenance${NC}"
    echo "   - Run this audit monthly"
    echo "   - Update documentation map"
    echo "   - Refactor new duplicates"
}

# Main execution
echo -e "${BLUE}🚀 Starting Cross-Reference Audit${NC}"

# Find similar content
find_similar_content 80 50

# Find duplicated topics
find_duplicated_topics

# Analyze links
analyze_links

# Generate recommendations
generate_recommendations

# Generate report
cat > "$AUDIT_REPORT" << EOF
# Cross-Reference Audit Report

**Generated**: $(date)
**Purpose**: Identify duplicated content and cross-reference opportunities

## Summary

This audit analyzed the documentation for:
- Content duplication
- Topic overlap
- Link patterns
- Cross-reference opportunities

## Recommendations

1. **Create Documentation Map**: Define canonical locations for each topic
2. **Refactor Duplicates**: Replace duplicated content with cross-references
3. **Implement Cross-Reference Strategy**: Use consistent linking patterns
4. **Regular Maintenance**: Run monthly audits

## Next Steps

1. Create docs/DOCUMENTATION_MAP.md
2. Refactor top duplicated topics
3. Implement cross-reference strategy
4. Schedule regular audits

EOF

echo -e "\n${GREEN}📊 Audit Complete${NC}"
echo "================================"
echo "Report saved to: $AUDIT_REPORT"
echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo "1. Review audit results"
echo "2. Create docs/DOCUMENTATION_MAP.md"
echo "3. Refactor duplicated topics"
echo "4. Implement cross-reference strategy"
echo ""
echo -e "${GREEN}🎯 Cross-reference audit complete!${NC}"

# Cleanup
rm -rf "$TEMP_DIR"
