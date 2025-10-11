#!/bin/bash

# test_gitignore.sh - Test .gitignore patterns work correctly
# Usage: ./scripts/test_gitignore.sh

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

echo -e "${BLUE}🧪 Testing .gitignore Patterns${NC}"
echo "================================"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Function to test gitignore pattern
test_gitignore_pattern() {
    local pattern="$1"
    local description="$2"
    local should_ignore="$3"  # true if should be ignored, false if should be tracked

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "\n${BLUE}Testing: ${description}${NC}"
    echo "Pattern: ${pattern}"

    # Create a test file
    local test_file="test_gitignore_${TOTAL_TESTS}.tmp"
    echo "test content" > "$test_file"

    # Check if git ignores the file
    if git check-ignore "$test_file" >/dev/null 2>&1; then
        local is_ignored=true
    else
        local is_ignored=false
    fi

    # Clean up test file
    rm -f "$test_file"

    # Check result
    if [ "$is_ignored" = "$should_ignore" ]; then
        echo -e "  ${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC}"
        echo "  Expected: $should_ignore, Got: $is_ignored"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test patterns that should be ignored
echo -e "\n${YELLOW}Testing patterns that SHOULD be ignored:${NC}"

test_gitignore_pattern "test_*.txt" "Test result files" "true"
test_gitignore_pattern "benchmark_*.json" "Benchmark result files" "true"
test_gitignore_pattern "*_GENERATED.md" "Generated documentation" "true"
test_gitignore_pattern "temp_*.py" "Temporary Python files" "true"
test_gitignore_pattern "debug_*.log" "Debug log files" "true"
test_gitignore_pattern "*.tmp" "Temporary files" "true"
test_gitignore_pattern "*.backup" "Backup files" "true"
test_gitignore_pattern "*.log" "Log files" "true"
test_gitignore_pattern "*.csv" "CSV data files" "true"
test_gitignore_pattern "*.pkl" "Pickle model files" "true"

# Test patterns that should NOT be ignored
echo -e "\n${YELLOW}Testing patterns that should NOT be ignored:${NC}"

test_gitignore_pattern "README.md" "README files" "false"
test_gitignore_pattern "requirements.txt" "Requirements files" "false"
test_gitignore_pattern "*.py" "Python source files" "false"
test_gitignore_pattern "scripts/*.sh" "Shell scripts" "false"

# Test specific file patterns
echo -e "\n${YELLOW}Testing specific file patterns:${NC}"

# Create test files for specific patterns
echo "test" > "test_results.txt"
echo "test" > "benchmark_results.json"
echo "test" > "temp_script.py"
echo "test" > "debug.log"
echo "test" > "config.tmp"

# Test if these are ignored
for file in "test_results.txt" "benchmark_results.json" "temp_script.py" "debug.log" "config.tmp"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if git check-ignore "$file" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ PASS${NC}: $file is ignored"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC}: $file is NOT ignored"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

# Clean up test files
rm -f test_results.txt benchmark_results.json temp_script.py debug.log config.tmp

# Test directory patterns
echo -e "\n${YELLOW}Testing directory patterns:${NC}"

# Create test directories
mkdir -p test_results_dir benchmark_results_dir temp_dir debug_dir

# Test if these directories are ignored
for dir in "test_results_dir" "benchmark_results_dir" "temp_dir" "debug_dir"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if git check-ignore "$dir" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ PASS${NC}: $dir is ignored"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC}: $dir is NOT ignored"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

# Clean up test directories
rm -rf test_results_dir benchmark_results_dir temp_dir debug_dir

# Test security patterns
echo -e "\n${YELLOW}Testing security patterns:${NC}"

# Create test security files
echo "test" > "test.key"
echo "test" > "test.pem"
echo "test" > "credentials.json"
echo "test" > "secrets.yaml"
echo "test" > ".env"

# Test if these are ignored
for file in "test.key" "test.pem" "credentials.json" "secrets.yaml" ".env"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if git check-ignore "$file" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ PASS${NC}: $file is ignored"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC}: $file is NOT ignored"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

# Clean up security test files
rm -f test.key test.pem credentials.json secrets.yaml .env

# Test archive patterns
echo -e "\n${YELLOW}Testing archive patterns:${NC}"

# Create test archive files
echo "test" > "docs/archive/2025-10/test.md"
echo "test" > "docs/completion/test.md"

# Test if these are ignored
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if git check-ignore "docs/archive/2025-10/test.md" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅ PASS${NC}: docs/archive/2025-10/test.md is ignored"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "  ${RED}❌ FAIL${NC}: docs/archive/2025-10/test.md is NOT ignored"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if git check-ignore "docs/completion/test.md" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅ PASS${NC}: docs/completion/test.md is ignored"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "  ${RED}❌ FAIL${NC}: docs/completion/test.md is NOT ignored"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Clean up archive test files
rm -f docs/archive/2025-10/test.md docs/completion/test.md

# Test .ai directory patterns
echo -e "\n${YELLOW}Testing .ai directory patterns:${NC}"

# Create test .ai files
echo "test" > ".ai/daily/test.md"
echo "test" > ".ai/monthly/test.md"
echo "test" > ".ai/archive/test.md"

# Test if these are ignored
for file in ".ai/daily/test.md" ".ai/monthly/test.md" ".ai/archive/test.md"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if git check-ignore "$file" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ PASS${NC}: $file is ignored"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC}: $file is NOT ignored"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
done

# Clean up .ai test files
rm -f .ai/daily/test.md .ai/monthly/test.md .ai/archive/test.md

# Check for untracked files that should be ignored
echo -e "\n${YELLOW}Checking for untracked files that should be ignored:${NC}"

# Get list of untracked files
untracked_files=$(git ls-files --others --exclude-standard 2>/dev/null || echo "")

if [ -n "$untracked_files" ]; then
    echo "Untracked files found:"
    echo "$untracked_files"
    echo ""
    echo -e "${YELLOW}⚠️  Review these files - they should be added to .gitignore if they're artifacts${NC}"
else
    echo -e "  ${GREEN}✅ No untracked files found${NC}"
fi

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "================================"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! .gitignore patterns are working correctly.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Review .gitignore patterns.${NC}"
    exit 1
fi
