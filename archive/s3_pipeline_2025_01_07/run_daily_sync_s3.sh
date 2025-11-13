#!/bin/bash
#
# Daily NBA Data Sync - Cron Wrapper Script
#
# This script runs the daily data synchronization and handles:
# - Environment setup
# - Secret loading
# - Local scraping → S3 upload
# - S3 → Database loading
# - Shot zone classification
# - Error handling
# - Email/SMS notifications on failure
#
# Schedule with cron (runs at 1:30 AM daily):
#   30 1 * * * /Users/ryanranft/nba-mcp-synthesis/scripts/run_daily_sync.sh
#
# WORKFLOW:
# 1. Scrape yesterday's games from ESPN API (local)
# 2. Upload scraped data to S3
# 3. Download from S3 and load into database
# 4. Classify shot zones automatically during insertion
#

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-mcp-synthesis"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/daily_sync_$(date +%Y%m%d).log"
PYTHON_BIN="python3"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log start
echo "========================================" >> "$LOG_FILE"
echo "Daily NBA Data Sync - $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR"

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$PROJECT_DIR"

# Load secrets
source /Users/ryanranft/load_secrets_universal.sh

if [ "$SECRETS_LOADED" != "true" ]; then
    echo "❌ Failed to load secrets" >> "$LOG_FILE"

    # TODO: Send alert notification
    # python3 scripts/send_alert.py --subject "Daily Sync Failed" --message "Secret loading failed"

    exit 1
fi

# Step 1: Scrape data locally and upload to S3
echo "Step 1: Scraping data from ESPN API..." >> "$LOG_FILE"

if $PYTHON_BIN scripts/daily_data_sync.py >> "$LOG_FILE" 2>&1; then
    echo "✅ Data scraped and uploaded to S3" >> "$LOG_FILE"
else
    echo "❌ Scraping/upload failed" >> "$LOG_FILE"

    # TODO: Send alert notification
    # python3 scripts/send_alert.py --subject "Daily Sync Failed" --message "Scraping failed. Check logs at $LOG_FILE"

    exit 1
fi

# Step 2: Load data from S3 to database (with shot zone classification)
echo "Step 2: Loading data from S3 to database..." >> "$LOG_FILE"

if $PYTHON_BIN scripts/load_from_s3.py >> "$LOG_FILE" 2>&1; then
    echo "✅ Data loaded successfully from S3" >> "$LOG_FILE"
    echo "✅ Daily sync completed successfully" >> "$LOG_FILE"
    exit 0
else
    echo "❌ Database load failed" >> "$LOG_FILE"

    # TODO: Send alert notification
    # python3 scripts/send_alert.py --subject "Daily Sync Failed" --message "Database load failed. Check logs at $LOG_FILE"

    exit 1
fi
