#!/bin/bash
#
# NBA MCP Synthesis - E2E Test Runner
# Safely runs end-to-end tests with MCP server management
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0.32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}NBA MCP Synthesis - E2E Test Runner${NC}"
echo "========================================"
echo ""

# Check if MCP server is already running
check_server_running() {
    if lsof -i :3000 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  MCP server already running on port 3000${NC}"
        read -p "Kill existing server and continue? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill_server
        else
            echo "Aborting tests. Stop the existing server first."
            exit 1
        fi
    fi
}

# Kill MCP server
kill_server() {
    echo "Stopping MCP server..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Start MCP server in background
start_server() {
    echo "Starting MCP server in background..."

    # Start server
    python mcp_server/server.py > logs/mcp_server_test.log 2>&1 &
    SERVER_PID=$!

    echo "MCP server PID: $SERVER_PID"

    # Wait for server to be ready
    echo "Waiting for server to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:3000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ MCP server ready${NC}"
            return 0
        fi
        sleep 2
        echo -n "."
    done

    echo -e "\n${RED}❌ MCP server failed to start${NC}"
    cat logs/mcp_server_test.log
    return 1
}

# Run tests
run_tests() {
    echo ""
    echo "Running E2E tests..."
    echo "===================="
    echo ""

    # Run pytest with timeout protection
    pytest tests/test_e2e_workflow.py \
        -v \
        --tb=short \
        --timeout=300 \
        --timeout-method=thread \
        "$@"

    TEST_EXIT_CODE=$?

    echo ""
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ All E2E tests passed${NC}"
    else
        echo -e "${RED}❌ Some E2E tests failed${NC}"
    fi

    return $TEST_EXIT_CODE
}

# Cleanup on exit
cleanup() {
    echo ""
    echo "Cleaning up..."
    kill_server
    echo -e "${GREEN}Cleanup complete${NC}"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Main execution
main() {
    # Create logs directory
    mkdir -p logs

    # Check for running server
    check_server_running

    # Start server
    if ! start_server; then
        echo -e "${RED}Failed to start MCP server. Check logs/mcp_server_test.log${NC}"
        exit 1
    fi

    # Run tests
    run_tests "$@"
    TEST_RESULT=$?

    # Return test result
    exit $TEST_RESULT
}

# Run main
main "$@"
