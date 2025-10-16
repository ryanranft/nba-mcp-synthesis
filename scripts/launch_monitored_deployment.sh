#!/bin/bash
# Launch Monitored Multi-Pass Deployment
# Wrapper script that sets up environment and launches the monitoring system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Multi-Pass Book Deployment Launcher${NC}"
echo -e "${CYAN}========================================${NC}"

# Check if we're in the right directory
if [ ! -f "scripts/multi_pass_book_deployment.py" ]; then
    echo -e "${RED}Error: Not in NBA MCP Synthesis directory${NC}"
    echo -e "${YELLOW}Please run this script from the project root${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${BLUE}Setting up directories...${NC}"
mkdir -p synthesis_output
mkdir -p logs

# Check for API keys
echo -e "${BLUE}Checking API keys...${NC}"
if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${YELLOW}Warning: GOOGLE_API_KEY not set${NC}"
fi
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo -e "${YELLOW}Warning: DEEPSEEK_API_KEY not set${NC}"
fi
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}Warning: ANTHROPIC_API_KEY not set${NC}"
fi
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}Warning: OPENAI_API_KEY not set${NC}"
fi

# Load API keys from .env file if it exists
if [ -f ".env" ]; then
    echo -e "${BLUE}Loading API keys from .env file...${NC}"
    set -a
    source <(grep -E '^[A-Z_]+=' .env 2>/dev/null || true)
    set +a
fi

# Load API keys from .env.workflow if it exists
if [ -f ".env.workflow" ]; then
    echo -e "${BLUE}Loading API keys from .env.workflow file...${NC}"
    set -a
    source <(grep -E '^[A-Z_]+=' .env.workflow 2>/dev/null || true)
    set +a
fi

# Verify Python dependencies
echo -e "${BLUE}Checking Python dependencies...${NC}"
python3 -c "import json, subprocess, signal, datetime" 2>/dev/null || {
    echo -e "${RED}Error: Required Python modules not available${NC}"
    exit 1
}

# Make monitor script executable
chmod +x scripts/monitor_deployment.py

# Launch monitoring system
echo -e "${GREEN}Launching Multi-Pass Book Deployment Monitor...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
echo ""

# Run the monitoring script
python3 scripts/monitor_deployment.py

# Cleanup on exit
echo -e "${CYAN}Monitoring session ended${NC}"
echo -e "${BLUE}Log files saved to: logs/deployment_monitor.log${NC}"
echo -e "${BLUE}Progress file: synthesis_output/multi_pass_progress.json${NC}"
