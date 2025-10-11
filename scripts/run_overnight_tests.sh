#!/bin/bash
################################################################################
# Overnight Test Runner Script
# Complete automated testing suite for FastMCP server
#
# Usage:
#   ./scripts/run_overnight_tests.sh
#
# Or run in background:
#   nohup ./scripts/run_overnight_tests.sh > overnight.log 2>&1 &
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp function
timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# Print colored header
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Print step
print_step() {
    echo -e "${GREEN}▶ [$(timestamp)] $1${NC}"
}

# Print warning
print_warning() {
    echo -e "${YELLOW}⚠ [$(timestamp)] $1${NC}"
}

# Print error
print_error() {
    echo -e "${RED}✗ [$(timestamp)] $1${NC}"
}

# Print success
print_success() {
    echo -e "${GREEN}✓ [$(timestamp)] $1${NC}"
}

################################################################################
# Main Script
################################################################################

print_header "🌙 NBA MCP Overnight Test Suite"
echo "Started: $(timestamp)"
echo ""

# Create results directories
print_step "Creating result directories..."
mkdir -p test_results
mkdir -p benchmark_results
mkdir -p reports

# Step 1: Validate deployment
print_header "1. Deployment Validation"
print_step "Running deployment validation..."

if python scripts/validate_deployment.py; then
    print_success "Deployment validation passed"
else
    print_error "Deployment validation failed!"
    print_warning "Continuing with tests anyway..."
fi

# Step 2: Run comprehensive test suite
print_header "2. Comprehensive Test Suite"
print_step "Running full test suite..."

if python scripts/overnight_test_suite.py; then
    print_success "Test suite completed"
else
    print_error "Test suite encountered errors"
fi

# Step 3: Run performance benchmarks
print_header "3. Performance Benchmarks"
print_step "Running performance benchmarks..."

if python scripts/benchmark_suite.py; then
    print_success "Benchmarks completed"
else
    print_error "Benchmarks encountered errors"
fi

# Step 4: Run FastMCP component tests
print_header "4. FastMCP Component Tests"
print_step "Running FastMCP component tests..."

if python scripts/test_fastmcp_server.py; then
    print_success "Component tests completed"
else
    print_error "Component tests encountered errors"
fi

# Step 5: Generate consolidated reports
print_header "5. Report Generation"
print_step "Generating consolidated reports..."

if python scripts/generate_test_report.py; then
    print_success "Reports generated"
else
    print_warning "Report generation encountered errors"
fi

# Step 6: Summary
print_header "📊 Test Suite Summary"

echo "Results saved to:"
echo "  • test_results/     - Individual test results"
echo "  • benchmark_results/ - Performance benchmarks"
echo "  • reports/          - Consolidated reports"
echo ""

# Count results
TEST_FILES=$(find test_results -name "*.json" 2>/dev/null | wc -l)
BENCHMARK_FILES=$(find benchmark_results -name "*.json" 2>/dev/null | wc -l)
REPORT_FILES=$(find reports -name "*.html" 2>/dev/null | wc -l)

echo "Files generated:"
echo "  • Test results:  $TEST_FILES"
echo "  • Benchmarks:    $BENCHMARK_FILES"
echo "  • Reports:       $REPORT_FILES"
echo ""

# Find latest HTML report
LATEST_REPORT=$(find reports -name "*.html" -type f -print0 2>/dev/null | xargs -0 ls -t | head -1)

if [ -n "$LATEST_REPORT" ]; then
    print_success "Latest report: $LATEST_REPORT"
    echo ""
    echo "To view the report, run:"
    echo "  open $LATEST_REPORT"
else
    print_warning "No HTML reports found"
fi

echo ""
print_header "✅ Overnight Test Suite Complete"
echo "Finished: $(timestamp)"
echo ""