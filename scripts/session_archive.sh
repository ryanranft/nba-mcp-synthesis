#!/bin/bash

# session_archive.sh - Archive old session files to S3 or local archive
# Usage: ./scripts/session_archive.sh [--to-s3] [--monthly] [--dry-run]

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

# Parse arguments
TO_S3=false
MONTHLY=false
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --to-s3)
            TO_S3=true
            ;;
        --monthly)
            MONTHLY=true
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
    esac
done

echo -e "${BLUE}📦 Session Archive Tool${NC}"
echo "================================"

# Configuration
S3_BUCKET="${NBA_MCP_S3_BUCKET:-nba-mcp-sessions}"  # Set via env var
ARCHIVE_DIR=".ai/archive"
DAILY_DIR=".ai/daily"
MONTHLY_DIR=".ai/monthly"
RETENTION_DAYS=7
RETENTION_MONTHS=3

mkdir -p "$ARCHIVE_DIR"

# Archive old daily sessions (older than 7 days)
echo -e "\n${BLUE}🗂️  Checking daily sessions...${NC}"

OLD_DAILY_FILES=$(find "$DAILY_DIR" -name "*.md" -type f -mtime +${RETENTION_DAYS} ! -name "template.md" 2>/dev/null || echo "")

if [ -z "$OLD_DAILY_FILES" ]; then
    echo "  No daily sessions older than ${RETENTION_DAYS} days"
else
    DAILY_COUNT=$(echo "$OLD_DAILY_FILES" | wc -l | tr -d ' ')
    echo -e "  Found ${YELLOW}${DAILY_COUNT}${NC} daily session(s) to archive"

    for file in $OLD_DAILY_FILES; do
        filename=$(basename "$file")
        echo "  - $filename"

        if [ "$DRY_RUN" = false ]; then
            # Move to archive
            mv "$file" "$ARCHIVE_DIR/"

            # Upload to S3 if enabled
            if [ "$TO_S3" = true ]; then
                if command -v aws &> /dev/null; then
                    echo "    ↳ Uploading to S3..."
                    aws s3 cp "$ARCHIVE_DIR/$filename" "s3://${S3_BUCKET}/daily/$filename" 2>/dev/null || echo -e "    ${RED}⚠️  S3 upload failed${NC}"
                else
                    echo -e "    ${YELLOW}⚠️  AWS CLI not found, skipping S3 upload${NC}"
                fi
            fi
        fi
    done

    if [ "$DRY_RUN" = false ]; then
        echo -e "  ${GREEN}✅ Archived ${DAILY_COUNT} daily session(s)${NC}"
    else
        echo -e "  ${YELLOW}[DRY RUN] Would archive ${DAILY_COUNT} daily session(s)${NC}"
    fi
fi

# Archive old monthly summaries (older than 3 months)
if [ "$MONTHLY" = true ]; then
    echo -e "\n${BLUE}📅 Checking monthly summaries...${NC}"

    OLD_MONTHLY_FILES=$(find "$MONTHLY_DIR" -name "*.md" -type f -mtime +$((RETENTION_MONTHS * 30)) ! -name "template.md" 2>/dev/null || echo "")

    if [ -z "$OLD_MONTHLY_FILES" ]; then
        echo "  No monthly summaries older than ${RETENTION_MONTHS} months"
    else
        MONTHLY_COUNT=$(echo "$OLD_MONTHLY_FILES" | wc -l | tr -d ' ')
        echo -e "  Found ${YELLOW}${MONTHLY_COUNT}${NC} monthly summar(ies) to archive"

        for file in $OLD_MONTHLY_FILES; do
            filename=$(basename "$file")
            echo "  - $filename"

            if [ "$DRY_RUN" = false ]; then
                # Move to archive
                mv "$file" "$ARCHIVE_DIR/"

                # Upload to S3 if enabled
                if [ "$TO_S3" = true ]; then
                    if command -v aws &> /dev/null; then
                        echo "    ↳ Uploading to S3..."
                        aws s3 cp "$ARCHIVE_DIR/$filename" "s3://${S3_BUCKET}/monthly/$filename" 2>/dev/null || echo -e "    ${RED}⚠️  S3 upload failed${NC}"
                    else
                        echo -e "    ${YELLOW}⚠️  AWS CLI not found, skipping S3 upload${NC}"
                    fi
                fi
            fi
        done

        if [ "$DRY_RUN" = false ]; then
            echo -e "  ${GREEN}✅ Archived ${MONTHLY_COUNT} monthly summar(ies)${NC}"
        else
            echo -e "  ${YELLOW}[DRY RUN] Would archive ${MONTHLY_COUNT} monthly summar(ies)${NC}"
        fi
    fi
fi

# Upload archived files to S3 if enabled
if [ "$TO_S3" = true ] && [ "$DRY_RUN" = false ]; then
    echo -e "\n${BLUE}☁️  Syncing archive to S3...${NC}"

    if command -v aws &> /dev/null; then
        # Upload any remaining files in archive/
        ARCHIVE_FILES=$(find "$ARCHIVE_DIR" -name "*.md" -type f 2>/dev/null || echo "")

        if [ -n "$ARCHIVE_FILES" ]; then
            ARCHIVE_COUNT=$(echo "$ARCHIVE_FILES" | wc -l | tr -d ' ')
            echo "  Uploading ${ARCHIVE_COUNT} archived file(s) to S3..."

            for file in $ARCHIVE_FILES; do
                filename=$(basename "$file")
                aws s3 cp "$file" "s3://${S3_BUCKET}/archive/$filename" 2>/dev/null && rm "$file" || echo -e "    ${RED}⚠️  Failed to upload $filename${NC}"
            done

            echo -e "  ${GREEN}✅ Archive synced to S3${NC}"
        else
            echo "  No files in archive to upload"
        fi
    else
        echo -e "  ${RED}⚠️  AWS CLI not found, cannot upload to S3${NC}"
        echo "  Install: brew install awscli"
    fi
fi

# Summary
echo -e "\n${BLUE}📊 Archive Summary${NC}"
echo "================================"
echo "Daily retention: ${RETENTION_DAYS} days"
echo "Monthly retention: ${RETENTION_MONTHS} months"
echo "S3 enabled: ${TO_S3}"
echo "S3 bucket: s3://${S3_BUCKET}"
echo ""

if [ "$TO_S3" = true ]; then
    echo -e "${YELLOW}💡 Restore from S3:${NC}"
    echo "  aws s3 cp s3://${S3_BUCKET}/daily/2025-10-11-session-1.md .ai/daily/"
    echo ""
fi

echo -e "${GREEN}✅ Archive process complete${NC}"

# Cost estimate for S3
if [ "$TO_S3" = true ]; then
    echo ""
    echo -e "${BLUE}💰 S3 Cost Estimate:${NC}"
    echo "  Storage: \$0.023/GB/month (Standard)"
    echo "  Typical session: ~50KB"
    echo "  100 sessions: ~\$0.0001/month"
    echo "  1000 sessions: ~\$0.0012/month"
fi
