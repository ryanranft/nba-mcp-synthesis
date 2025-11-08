#!/bin/bash
"""
Launch Production Monitoring Dashboard

Starts the Streamlit dashboard for monitoring NBA betting system performance.

Usage:
------
    # Start dashboard (default port 8501)
    ./scripts/launch_dashboard.sh

    # Start on custom port
    ./scripts/launch_dashboard.sh --port 8502

    # Start with auto-refresh enabled
    ./scripts/launch_dashboard.sh --auto-refresh

Options:
--------
    --port PORT         Custom port (default: 8501)
    --host HOST         Custom host (default: localhost)
    --auto-refresh      Enable auto-refresh
    --help             Show this help message
"""

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PORT=8501
HOST="localhost"
AUTO_REFRESH=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --auto-refresh)
            AUTO_REFRESH=true
            shift
            ;;
        --help)
            echo "NBA Betting System - Production Monitoring Dashboard"
            echo ""
            echo "Usage: ./scripts/launch_dashboard.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT         Custom port (default: 8501)"
            echo "  --host HOST         Custom host (default: localhost)"
            echo "  --auto-refresh      Enable auto-refresh"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NBA Betting System - Dashboard Launch${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo -e "${RED}❌ Streamlit not found${NC}"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check if data files exist
echo -e "${YELLOW}📊 Checking data files...${NC}"

if [ ! -f "data/paper_trades.db" ]; then
    echo -e "${YELLOW}⚠️  Paper trading database not found (data/paper_trades.db)${NC}"
    echo -e "${YELLOW}   The dashboard will still work, but you'll need to place some bets first.${NC}"
fi

if [ ! -f "data/calibration.db" ]; then
    echo -e "${YELLOW}⚠️  Calibration database not found (data/calibration.db)${NC}"
    echo -e "${YELLOW}   Run some predictions to populate calibration data.${NC}"
fi

echo ""
echo -e "${GREEN}✅ Pre-flight checks complete${NC}"
echo ""
echo -e "${BLUE}Starting dashboard...${NC}"
echo -e "${BLUE}  Host: ${HOST}${NC}"
echo -e "${BLUE}  Port: ${PORT}${NC}"
echo -e "${BLUE}  URL:  http://${HOST}:${PORT}${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the dashboard${NC}"
echo ""

# Launch streamlit
streamlit run \
    scripts/production_monitoring_dashboard.py \
    --server.port="${PORT}" \
    --server.address="${HOST}" \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --theme.base="light"