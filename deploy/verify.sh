#!/bin/bash
#
# Post-Deployment Verification Script
# Verifies the system is properly deployed and functioning
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}NBA MCP Synthesis - Deployment Verification${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

check() {
    local name="$1"
    local command="$2"

    echo -en "Checking $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

# Verification checks
echo -e "${BLUE}Running verification checks...${NC}"
echo ""

# 1. Python environment
check "Python 3.9+" "python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)'"

# 2. Virtual environment
check "Virtual environment" "[ -d '$PROJECT_ROOT/venv' ]"

# 3. Critical Python packages
check "boto3 package" "python3 -c 'import boto3'"
check "psycopg2 package" "python3 -c 'import psycopg2'"
check "anthropic package" "python3 -c 'import anthropic'"
check "mcp package" "python3 -c 'import mcp'"

# 4. Configuration files
check ".env file" "[ -f '$PROJECT_ROOT/.env' ]"
check ".env.example file" "[ -f '$PROJECT_ROOT/.env.example' ]"
check "requirements.txt" "[ -f '$PROJECT_ROOT/requirements.txt' ]"

# 5. Project structure
check "mcp_server directory" "[ -d '$PROJECT_ROOT/mcp_server' ]"
check "synthesis directory" "[ -d '$PROJECT_ROOT/synthesis' ]"
check "scripts directory" "[ -d '$PROJECT_ROOT/scripts' ]"
check "tests directory" "[ -d '$PROJECT_ROOT/tests' ]"

# 6. Required directories
check "logs directory" "[ -d '$PROJECT_ROOT/logs' ]"
check "synthesis_output directory" "[ -d '$PROJECT_ROOT/synthesis_output' ]"

# 7. Critical scripts
check "validate_environment.py" "[ -f '$PROJECT_ROOT/scripts/validate_environment.py' ]"
check "start_mcp_server.sh" "[ -x '$PROJECT_ROOT/scripts/start_mcp_server.sh' ]"
check "stop_mcp_server.sh" "[ -x '$PROJECT_ROOT/scripts/stop_mcp_server.sh' ]"
check "test_e2e_workflow.py" "[ -f '$PROJECT_ROOT/tests/test_e2e_workflow.py' ]"

# 8. Environment validation
echo -en "Validating environment configuration... "
if python3 "${PROJECT_ROOT}/scripts/validate_environment.py" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo -e "  ${YELLOW}Run: python scripts/validate_environment.py${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# 9. MCP server status
echo -en "MCP server status... "
if [ -f "${PROJECT_ROOT}/.mcp_server.pid" ]; then
    PID=$(cat "${PROJECT_ROOT}/.mcp_server.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ RUNNING (PID: $PID)${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${YELLOW}⚠️  STOPPED${NC}"
        echo -e "  ${YELLOW}Start with: ./scripts/start_mcp_server.sh${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  NOT STARTED${NC}"
    echo -e "  ${YELLOW}Start with: ./scripts/start_mcp_server.sh${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Checks passed: ${GREEN}${PASS_COUNT}${NC}"
echo -e "Checks failed: ${RED}${FAIL_COUNT}${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ All verification checks passed!${NC}"
    echo ""
    echo -e "${BLUE}System is ready to use!${NC}"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo -e "  1. Start MCP server: ${GREEN}./scripts/start_mcp_server.sh${NC}"
    echo -e "  2. Run E2E tests:    ${GREEN}python tests/test_e2e_workflow.py${NC}"
    echo -e "  3. Try synthesis:    ${GREEN}python scripts/test_synthesis_direct.py${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ ${FAIL_COUNT} verification check(s) failed${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. Check .env file has correct credentials"
    echo -e "  2. Run: ${GREEN}python scripts/validate_environment.py${NC}"
    echo -e "  3. See: ${GREEN}DEPLOYMENT.md${NC} for detailed setup"
    echo ""
    exit 1
fi
