#!/bin/bash
#
# Setup Cron Jobs for NBA Betting Automation
#
# This script installs cron jobs for automated daily betting analysis and
# live arbitrage monitoring during NBA game hours.
#
# Cron Schedule:
# - Daily Betting Analysis: 10:00 AM CT (before games start)
# - Arbitrage Monitor: Every 5 min, 6:00 PM - 11:00 PM CT (during games)
# - Odds Freshness Check: Every 15 min, 9:00 AM - 11:00 PM CT
#
# Usage:
#     ./scripts/setup_cron_jobs.sh
#     ./scripts/setup_cron_jobs.sh --dry-run
#     ./scripts/setup_cron_jobs.sh --remove
#
# Author: NBA MCP Synthesis Team
# Date: 2025-01-05

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_DIR="/Users/ryanranft/nba-mcp-synthesis"
PYTHON_BIN="/usr/local/bin/python3"  # Adjust if needed
CONTEXT="production"

# Parse arguments
DRY_RUN=false
REMOVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --remove)
            REMOVE=true
            shift
            ;;
        --python)
            PYTHON_BIN="$2"
            shift 2
            ;;
        --context)
            CONTEXT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}NBA Betting Automation - Cron Job Setup${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Verify project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    exit 1
fi

# Verify Python exists
if [ ! -f "$PYTHON_BIN" ]; then
    echo -e "${YELLOW}⚠️  Python binary not found at: $PYTHON_BIN${NC}"
    echo -e "${YELLOW}   Trying to detect Python...${NC}"
    PYTHON_BIN=$(which python3 || which python)
    if [ -z "$PYTHON_BIN" ]; then
        echo -e "${RED}❌ Python not found. Please specify with --python${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Found Python at: $PYTHON_BIN${NC}"
fi

echo -e "${GREEN}✅ Project directory: $PROJECT_DIR${NC}"
echo -e "${GREEN}✅ Python binary: $PYTHON_BIN${NC}"
echo -e "${GREEN}✅ Context: $CONTEXT${NC}"
echo ""

# Define cron jobs
# Note: Times are in CT (Central Time)
# Adjust HOUR values if your system uses a different timezone

CRON_JOBS=(
    # Daily betting analysis at 10:00 AM CT
    "0 10 * * * cd $PROJECT_DIR && $PYTHON_BIN scripts/daily_betting_analysis.py --email --sms-critical-only --context $CONTEXT >> logs/daily_analysis.log 2>&1"

    # Arbitrage monitor every 5 minutes from 6:00 PM to 11:00 PM CT (during games)
    # Disabled by default - uncomment to enable
    # "*/5 18-23 * * * cd $PROJECT_DIR && $PYTHON_BIN scripts/live_arbitrage_monitor.py --email --min-profit 0.015 --context $CONTEXT >> logs/arbitrage_monitor.log 2>&1"

    # Odds freshness check every 15 minutes from 9:00 AM to 11:00 PM CT
    # "*/15 9-23 * * * cd $PROJECT_DIR && $PYTHON_BIN scripts/check_odds_freshness.py --context $CONTEXT >> logs/odds_freshness.log 2>&1"
)

# Remove existing cron jobs
if [ "$REMOVE" = true ]; then
    echo -e "${YELLOW}🗑️  Removing NBA betting automation cron jobs...${NC}"

    # Get current crontab
    CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")

    # Filter out NBA betting automation jobs
    FILTERED_CRON=$(echo "$CURRENT_CRON" | grep -v "daily_betting_analysis.py" | grep -v "live_arbitrage_monitor.py" | grep -v "check_odds_freshness.py" || true)

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}🔍 DRY RUN - Would install:${NC}"
        echo "$FILTERED_CRON"
    else
        echo "$FILTERED_CRON" | crontab -
        echo -e "${GREEN}✅ Cron jobs removed${NC}"
    fi

    exit 0
fi

# Create logs directory
echo -e "${BLUE}📁 Creating logs directory...${NC}"
mkdir -p "$PROJECT_DIR/logs"
echo -e "${GREEN}✅ Logs directory created${NC}"
echo ""

# Display cron jobs to be installed
echo -e "${BLUE}📅 Cron jobs to install:${NC}"
echo -e "${BLUE}============================================================${NC}"
for job in "${CRON_JOBS[@]}"; do
    # Skip commented jobs
    if [[ $job =~ ^[[:space:]]*# ]]; then
        echo -e "${YELLOW}# (Disabled) ${job}${NC}"
    else
        echo -e "${GREEN}${job}${NC}"
    fi
done
echo -e "${BLUE}============================================================${NC}"
echo ""

# Verify scripts exist
echo -e "${BLUE}🔍 Verifying scripts exist...${NC}"

REQUIRED_SCRIPTS=(
    "scripts/daily_betting_analysis.py"
    # "scripts/live_arbitrage_monitor.py"  # Not created yet
    # "scripts/check_odds_freshness.py"    # Not created yet
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ -f "$PROJECT_DIR/$script" ]; then
        echo -e "${GREEN}✅ Found: $script${NC}"
    else
        echo -e "${RED}❌ Missing: $script${NC}"
        exit 1
    fi
done
echo ""

# Test daily_betting_analysis.py
echo -e "${BLUE}🧪 Testing daily_betting_analysis.py...${NC}"
cd "$PROJECT_DIR"
if $PYTHON_BIN scripts/daily_betting_analysis.py --dry-run --context $CONTEXT > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Script test passed${NC}"
else
    echo -e "${RED}❌ Script test failed${NC}"
    echo -e "${YELLOW}   Run manually to debug: $PYTHON_BIN scripts/daily_betting_analysis.py --dry-run${NC}"
    exit 1
fi
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}🔍 DRY RUN MODE - No changes will be made${NC}"
    echo ""
    echo -e "${BLUE}Would install the following crontab:${NC}"
    echo -e "${BLUE}============================================================${NC}"

    # Get current crontab
    CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")

    # Add header if crontab is empty
    if [ -z "$CURRENT_CRON" ]; then
        echo "# Crontab"
    else
        echo "$CURRENT_CRON"
    fi

    echo ""
    echo "# NBA Betting Automation (added by setup_cron_jobs.sh)"
    for job in "${CRON_JOBS[@]}"; do
        # Skip commented jobs
        if [[ ! $job =~ ^[[:space:]]*# ]]; then
            echo "$job"
        fi
    done

    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo -e "${YELLOW}To actually install, run without --dry-run${NC}"
    exit 0
fi

# Install cron jobs
echo -e "${BLUE}⚙️  Installing cron jobs...${NC}"

# Get current crontab
CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")

# Remove any existing NBA betting automation jobs
FILTERED_CRON=$(echo "$CURRENT_CRON" | grep -v "daily_betting_analysis.py" | grep -v "live_arbitrage_monitor.py" | grep -v "check_odds_freshness.py" || true)

# Create new crontab
NEW_CRON="$FILTERED_CRON"

# Add header
if [ -n "$NEW_CRON" ]; then
    NEW_CRON="${NEW_CRON}\n"
fi

NEW_CRON="${NEW_CRON}# NBA Betting Automation (added by setup_cron_jobs.sh on $(date))\n"

# Add jobs
for job in "${CRON_JOBS[@]}"; do
    # Skip commented jobs
    if [[ ! $job =~ ^[[:space:]]*# ]]; then
        NEW_CRON="${NEW_CRON}${job}\n"
    fi
done

# Install new crontab
echo -e "$NEW_CRON" | crontab -

echo -e "${GREEN}✅ Cron jobs installed successfully${NC}"
echo ""

# Display installed crontab
echo -e "${BLUE}📋 Installed crontab:${NC}"
echo -e "${BLUE}============================================================${NC}"
crontab -l | tail -n 10
echo -e "${BLUE}============================================================${NC}"
echo ""

# Summary
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}✅ SETUP COMPLETE${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "${BLUE}Scheduled jobs:${NC}"
echo -e "  • Daily betting analysis: 10:00 AM CT"
echo -e "  • Email notifications: Enabled"
echo -e "  • SMS notifications: Critical bets only (edge > 10%)"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  • Daily analysis: $PROJECT_DIR/logs/daily_analysis.log"
echo -e "  • Arbitrage monitor: $PROJECT_DIR/logs/arbitrage_monitor.log"
echo -e "  • Odds freshness: $PROJECT_DIR/logs/odds_freshness.log"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Monitor logs: tail -f logs/daily_analysis.log"
echo -e "  2. Verify email delivery tomorrow at 10 AM"
echo -e "  3. Check SMS delivery for critical bets (edge > 10%)"
echo -e "  4. Review recommendations in database"
echo ""
echo -e "${BLUE}To view installed cron jobs:${NC}"
echo -e "  crontab -l"
echo ""
echo -e "${BLUE}To remove cron jobs:${NC}"
echo -e "  ./scripts/setup_cron_jobs.sh --remove"
echo ""
echo -e "${GREEN}============================================================${NC}"
