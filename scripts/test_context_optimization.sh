#!/bin/bash

# test_context_optimization.sh - Comprehensive test suite for context optimization
# Usage: ./scripts/test_context_optimization.sh

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

echo -e "${BLUE}🧪 Context Optimization Test Suite${NC}"
echo "================================"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "\n${BLUE}Testing: $test_name${NC}"

    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC}"
        echo "  Expected: $expected_result"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to check file exists
check_file_exists() {
    local file="$1"
    local description="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "\n${BLUE}Checking: $description${NC}"

    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅ PASS${NC} - $file exists"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC} - $file missing"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to check directory exists
check_directory_exists() {
    local dir="$1"
    local description="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "\n${BLUE}Checking: $description${NC}"

    if [ -d "$dir" ]; then
        echo -e "  ${GREEN}✅ PASS${NC} - $dir exists"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC} - $dir missing"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to check script is executable
check_script_executable() {
    local script="$1"
    local description="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "\n${BLUE}Checking: $description${NC}"

    if [ -x "$script" ]; then
        echo -e "  ${GREEN}✅ PASS${NC} - $script is executable"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC} - $script not executable"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to check file content
check_file_content() {
    local file="$1"
    local pattern="$2"
    local description="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "\n${BLUE}Checking: $description${NC}"

    if [ -f "$file" ] && grep -q "$pattern" "$file"; then
        echo -e "  ${GREEN}✅ PASS${NC} - $file contains '$pattern'"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}❌ FAIL${NC} - $file missing or doesn't contain '$pattern'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo -e "${BLUE}🚀 Starting Context Optimization Tests${NC}"

# Phase 3: Archive & Prune Strategy Tests
echo -e "\n${YELLOW}📦 Phase 3: Archive & Prune Strategy${NC}"
check_directory_exists "docs/archive/2025-10" "Archive directory structure"
check_directory_exists "docs/archive/2025-10/completion" "Completion archive directory"
check_directory_exists "docs/archive/2025-10/sessions" "Sessions archive directory"
check_file_exists "docs/archive/2025-10/index.md" "Archive index file"

# Check that completion and sessions directories are empty (moved to archive)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ ! "$(ls -A docs/completion 2>/dev/null)" ]; then
    echo -e "\n${BLUE}Checking: Completion directory is empty${NC}"
    echo -e "  ${GREEN}✅ PASS${NC} - docs/completion is empty (moved to archive)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "\n${BLUE}Checking: Completion directory is empty${NC}"
    echo -e "  ${RED}❌ FAIL${NC} - docs/completion still contains files"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ ! "$(ls -A docs/sessions 2>/dev/null)" ]; then
    echo -e "\n${BLUE}Checking: Sessions directory is empty${NC}"
    echo -e "  ${GREEN}✅ PASS${NC} - docs/sessions is empty (moved to archive)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "\n${BLUE}Checking: Sessions directory is empty${NC}"
    echo -e "  ${RED}❌ FAIL${NC} - docs/sessions still contains files"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Phase 6: Index System Implementation Tests
echo -e "\n${YELLOW}📑 Phase 6: Index System Implementation${NC}"
check_file_exists "docs/index.md" "Master documentation index"
check_file_exists "docs/guides/index.md" "Guides index"
check_file_exists "docs/sprints/index.md" "Sprints index"
check_file_exists "docs/tracking/index.md" "Tracking index"
check_file_exists "docs/analysis/index.md" "Analysis index"
check_file_exists "docs/enhancements/index.md" "Enhancements index"
check_file_exists "docs/planning/index.md" "Planning index"
check_file_exists "docs/plans/index.md" "Plans index"
check_file_exists ".ai/daily/index.md" "Daily sessions index"
check_file_exists ".ai/monthly/index.md" "Monthly summaries index"
check_file_exists ".ai/permanent/index.md" "Permanent references index"
check_file_exists ".ai/permanent/tool-registry.md" "Tool registry"

# Phase 7: .gitignore Optimization Tests
echo -e "\n${YELLOW}🚫 Phase 7: .gitignore Optimization${NC}"
check_file_exists ".gitignore" ".gitignore file"
check_file_content ".gitignore" "docs/archive/2025-\*" "Archive patterns in .gitignore"
check_file_content ".gitignore" "docs/completion/" "Completion directory in .gitignore"
check_file_content ".gitignore" "test_results/" "Test artifacts in .gitignore"
check_file_content ".gitignore" "benchmark_results/" "Benchmark artifacts in .gitignore"
check_file_content ".gitignore" "\*_GENERATED.md" "Generated docs in .gitignore"
check_file_content ".gitignore" "temp_\*" "Temporary files in .gitignore"
check_file_content ".gitignore" "debug_\*" "Debug files in .gitignore"
check_file_content ".gitignore" "\.ai/daily/\*" "AI daily files in .gitignore"
check_file_content ".gitignore" "\.ai/monthly/\*" "AI monthly files in .gitignore"
check_file_content ".gitignore" "\.ai/archive/" "AI archive in .gitignore"

# Phase 5: Session Management Enhancement Tests
echo -e "\n${YELLOW}🔧 Phase 5: Session Management Enhancement${NC}"
check_file_exists ".ai/index.md" "AI session management guide"
check_file_content ".ai/index.md" "Session Management Guide" "Session management guide content"
check_file_content ".ai/index.md" "Context Optimization" "Context optimization content"
check_file_content "QUICKSTART.md" "Session Management" "Session management in QUICKSTART"
check_file_content "QUICKSTART.md" "\.ai/index\.md" "AI index link in QUICKSTART"

# Phase 8: Quick Reference Enhancement Tests
echo -e "\n${YELLOW}📊 Phase 8: Quick Reference Enhancement${NC}"
check_file_exists "PROJECT_STATUS.md" "Project status file"
check_file_content "PROJECT_STATUS.md" "Last Updated" "Status file has timestamp"
check_file_content "PROJECT_STATUS.md" "Current Status" "Status file has current status"
check_file_content "PROJECT_STATUS.md" "Quick Numbers" "Status file has quick numbers"
check_file_content "PROJECT_STATUS.md" "Recent Activity" "Status file has recent activity"

# Phase 9: Documentation Cross-References Tests
echo -e "\n${YELLOW}🔗 Phase 9: Documentation Cross-References${NC}"
check_file_exists "docs/DOCUMENTATION_MAP.md" "Documentation map"
check_file_content "docs/DOCUMENTATION_MAP.md" "Canonical Location" "Documentation map has canonical locations"
check_file_content "docs/DOCUMENTATION_MAP.md" "Cross-Reference" "Documentation map has cross-reference patterns"
check_file_content "docs/DOCUMENTATION_MAP.md" "Duplication Prevention" "Documentation map has duplication prevention"

# Script Tests
echo -e "\n${YELLOW}🛠️ Script Tests${NC}"
check_script_executable "scripts/session_start.sh" "Session start script"
check_script_executable "scripts/session_archive.sh" "Session archive script"
check_script_executable "scripts/update_status.sh" "Status update script"
check_script_executable "scripts/test_gitignore.sh" "Gitignore test script"
check_script_executable "scripts/audit_cross_references.sh" "Cross-reference audit script"

# Test script functionality
echo -e "\n${YELLOW}🧪 Script Functionality Tests${NC}"
run_test "Session start script help" "./scripts/session_start.sh --help" "Help output"
run_test "Session start health check" "./scripts/session_start.sh --health-check" "Health check passes"
run_test "Status update script" "./scripts/update_status.sh" "Status update succeeds"
run_test "Gitignore test script" "./scripts/test_gitignore.sh" "Gitignore tests pass"

# Context Optimization Tests
echo -e "\n${YELLOW}📊 Context Optimization Tests${NC}"

# Check current-session.md is small
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f ".ai/current-session.md" ]; then
    session_size=$(wc -l < .ai/current-session.md)
    if [ "$session_size" -lt 100 ]; then
        echo -e "\n${BLUE}Checking: Current session file is compact${NC}"
        echo -e "  ${GREEN}✅ PASS${NC} - .ai/current-session.md is $session_size lines (<100)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "\n${BLUE}Checking: Current session file is compact${NC}"
        echo -e "  ${RED}❌ FAIL${NC} - .ai/current-session.md is $session_size lines (>=100)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "\n${BLUE}Checking: Current session file is compact${NC}"
    echo -e "  ${RED}❌ FAIL${NC} - .ai/current-session.md missing"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Check PROJECT_STATUS.md is small
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "PROJECT_STATUS.md" ]; then
    status_size=$(wc -l < PROJECT_STATUS.md)
    if [ "$status_size" -lt 150 ]; then
        echo -e "\n${BLUE}Checking: Project status file is compact${NC}"
        echo -e "  ${GREEN}✅ PASS${NC} - PROJECT_STATUS.md is $status_size lines (<150)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "\n${BLUE}Checking: Project status file is compact${NC}"
        echo -e "  ${RED}❌ FAIL${NC} - PROJECT_STATUS.md is $status_size lines (>=150)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "\n${BLUE}Checking: Project status file is compact${NC}"
    echo -e "  ${RED}❌ FAIL${NC} - PROJECT_STATUS.md missing"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Check tool registry is comprehensive
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f ".ai/permanent/tool-registry.md" ]; then
    tool_count=$(grep -c "^- \*\*" .ai/permanent/tool-registry.md || echo "0")
    if [ "$tool_count" -gt 50 ]; then
        echo -e "\n${BLUE}Checking: Tool registry is comprehensive${NC}"
        echo -e "  ${GREEN}✅ PASS${NC} - Tool registry has $tool_count tools (>50)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "\n${BLUE}Checking: Tool registry is comprehensive${NC}"
        echo -e "  ${RED}❌ FAIL${NC} - Tool registry has $tool_count tools (<=50)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "\n${BLUE}Checking: Tool registry is comprehensive${NC}"
    echo -e "  ${RED}❌ FAIL${NC} - Tool registry missing"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Integration Tests
echo -e "\n${YELLOW}🔗 Integration Tests${NC}"

# Test that all index files link to each other properly
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "docs/index.md" ] && grep -q "docs/guides/index.md" docs/index.md; then
    echo -e "\n${BLUE}Checking: Index files link to each other${NC}"
    echo -e "  ${GREEN}✅ PASS${NC} - docs/index.md links to guides index"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "\n${BLUE}Checking: Index files link to each other${NC}"
    echo -e "  ${RED}❌ FAIL${NC} - Index files don't link properly"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test that session management is integrated
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "QUICKSTART.md" ] && grep -q "session_start.sh" QUICKSTART.md; then
    echo -e "\n${BLUE}Checking: Session management is integrated${NC}"
    echo -e "  ${GREEN}✅ PASS${NC} - QUICKSTART.md includes session management"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "\n${BLUE}Checking: Session management is integrated${NC}"
    echo -e "  ${RED}❌ FAIL${NC} - Session management not integrated"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "================================"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

# Calculate success rate
if [ $TOTAL_TESTS -gt 0 ]; then
    success_rate=$((TESTS_PASSED * 100 / TOTAL_TESTS))
    echo "Success Rate: $success_rate%"
fi

# Overall result
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Context optimization is working correctly.${NC}"
    echo -e "${GREEN}✅ Context Optimization System: READY${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Review the failures above.${NC}"
    echo -e "${RED}⚠️  Context Optimization System: NEEDS ATTENTION${NC}"
    exit 1
fi
