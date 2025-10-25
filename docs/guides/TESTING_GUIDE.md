# Comprehensive Testing Guide

**NBA MCP Synthesis - Test Suite Documentation**
**Last Updated**: 2025-10-24
**Test Suite Version**: 3.0
**Total Tests**: 482+ tests

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Organization](#test-organization)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Environment Setup](#environment-setup)
6. [Test Markers](#test-markers)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Quick Start

### Running All Tests

```bash
# Run all tests with parallel execution
pytest tests/ -v -n auto

# Run with coverage
pytest tests/ --cov=synthesis --cov=mcp_server --cov-report=html

# Run specific category
pytest tests/test_e2e_*.py -v
```

### Most Common Commands

```bash
# Fast unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Skip slow tests
pytest tests/ -v -m "not slow"

# Run specific test file
pytest tests/test_security.py -v

# Run with detailed output
pytest tests/ -vv --tb=short
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/                          # Unit tests (fast, isolated)
│   ├── test_algebra_tools.py     # 33 tests - Mathematical operations
│   └── test_formula_builder.py   # 21 tests - Formula construction
│
├── integration/                   # Integration tests
│   ├── test_mcp_client.py        # 8 tests - MCP client integration
│   ├── test_mcp_connection.py    # 6 tests - Server connectivity
│   ├── test_fastmcp_server.py    # 11 tests - Server functionality
│   ├── test_data_validation.py   # 5 tests - Data quality
│   ├── test_circuit_breaker.py   # 5 tests - Resilience patterns
│   └── test_epub_pdf_features.py # 10 tests - Document processing
│
├── security/                      # Security tests
│   ├── test_credentials.py       # 12 tests - Secrets validation
│   └── test_security_scanning.py # 12 tests - Security scanning
│
└── [root level]/                  # E2E and specialized tests
    ├── test_e2e_workflow.py       # 12 tests - Complete workflows
    ├── test_e2e_deployment_flow.py # 10 tests - Deployment automation
    ├── test_recursive_book_analysis.py # 16 tests - Book analysis
    ├── test_recommendation_integration.py # 14 tests - Recommendations
    ├── test_tier4_edge_cases.py   # 18 tests - Edge cases
    └── test_dims_integration.py   # 8 tests - Data inventory
```

### Test Count by Category

| Category | Files | Tests | Execution Time |
|----------|-------|-------|----------------|
| **A: Core Functionality** | 25 files | 385 tests | ~60s |
| **B: Critical Infrastructure** | 12 files | 78 tests | ~5s |
| **C: E2E Workflows** | 2 files | 22 tests | ~2s |
| **D: Analysis Frameworks** | 3 files | 37 tests | ~3s |
| **E: Edge Cases** | 2 files | 26 tests | ~1s |
| **TOTAL** | 44 files | **548 tests** | **~71s** |

---

## Running Tests

### By Category

#### Category A: Core Functionality
```bash
# All core tests
pytest tests/test_security.py \
       tests/test_resilience.py \
       tests/test_auth.py \
       tests/test_all_connectors.py \
       -v -n auto

# Just security tests (42 tests)
pytest tests/test_security.py -v

# Algebra tools (33 tests)
pytest tests/unit/test_algebra_tools.py -v
```

#### Category B: Critical Infrastructure
```bash
# Database & connectivity (29 tests)
pytest tests/integration/test_mcp_connection.py \
       tests/integration/test_fastmcp_server.py \
       tests/integration/test_mcp_client.py \
       -v

# Security & validation (35 tests)
pytest tests/security/ -v

# Document processing (15 tests)
pytest tests/integration/test_epub_pdf_features.py \
       tests/integration/test_pdf_reading.py \
       tests/integration/test_notifications.py \
       -v
```

#### Category C: E2E Workflows
```bash
# All E2E tests (22 tests)
pytest tests/test_e2e_workflow.py \
       tests/test_e2e_deployment_flow.py \
       -v

# Just workflow tests (12 tests)
pytest tests/test_e2e_workflow.py -v

# Just deployment tests (10 tests)
pytest tests/test_e2e_deployment_flow.py -v
```

#### Category D: Analysis Frameworks
```bash
# All analysis framework tests (37 tests)
pytest tests/test_recursive_book_analysis.py \
       tests/test_recommendation_integration.py \
       tests/test_phase6_1_automated_book_analysis.py \
       -v
```

#### Category E: Edge Cases
```bash
# All edge case tests (26 tests)
pytest tests/test_tier4_edge_cases.py \
       tests/test_dims_integration.py \
       -v
```

### By Test Type

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v -m integration

# Async tests
pytest tests/ -v -m asyncio

# Security tests
pytest tests/security/ tests/test_security*.py -v
```

### With Options

```bash
# Verbose output with short traceback
pytest tests/ -vv --tb=short

# Stop on first failure
pytest tests/ -v -x

# Run last failed tests
pytest tests/ -v --lf

# Show test durations
pytest tests/ -v --durations=10

# Parallel execution (12 workers)
pytest tests/ -v -n 12

# With coverage
pytest tests/ --cov=synthesis --cov=mcp_server \
       --cov-report=html --cov-report=term
```

---

## Test Categories

### Category A: Core Functionality (385 tests)

**Purpose**: Test core system functionality
**Execution Time**: ~60 seconds
**Skip Rate**: 5-10% (optional dependencies)

**Key Test Files**:
- `test_security.py` (42 tests) - Security scanning, validation
- `test_resilience.py` (29 tests) - Circuit breakers, retry logic
- `test_auth.py` (23 tests) - Authentication & authorization
- `test_all_connectors.py` (22 tests) - Database connectors
- `test_unified_secrets_manager.py` (17 tests) - Secrets management

**What's Tested**:
- ✅ Security scanning and validation
- ✅ Resilience patterns (circuit breakers, retries)
- ✅ Authentication and authorization
- ✅ Database connectivity
- ✅ Secrets management
- ✅ Configuration management

### Category B: Critical Infrastructure (78 tests)

**Purpose**: Test critical infrastructure components
**Execution Time**: ~5 seconds
**Skip Rate**: 10-15% (missing credentials)

**Key Test Files**:
- `test_fastmcp_server.py` (11 tests) - MCP server functionality
- `test_credentials.py` (12 tests) - API key validation
- `test_security_scanning.py` (12 tests) - Security tools
- `test_epub_pdf_features.py` (10 tests) - Document processing

**What's Tested**:
- ✅ MCP server startup and health checks
- ✅ Client-server communication
- ✅ Database query execution
- ✅ S3 file operations
- ✅ API key validation
- ✅ Security scanning tools
- ✅ PDF/EPUB processing
- ✅ Circuit breaker patterns
- ✅ Data validation

### Category C: E2E Workflows (22 tests)

**Purpose**: Test complete end-to-end workflows
**Execution Time**: ~2 seconds
**Skip Rate**: 5% (real API tests)

**Test Files**:
- `test_e2e_workflow.py` (12 tests) - Complete workflows
- `test_e2e_deployment_flow.py` (10 tests) - Deployment automation

**What's Tested**:
- ✅ MCP server startup → synthesis completion
- ✅ Book extraction → code deployment → PR creation
- ✅ Multi-model synthesis orchestration
- ✅ Error handling and rollback
- ✅ Cost tracking and limits
- ✅ Concurrent operation handling
- ✅ Performance metrics tracking

### Category D: Analysis Frameworks (37 tests)

**Purpose**: Test book analysis and recommendation systems
**Execution Time**: ~3 seconds
**Skip Rate**: 5-10% (S3 dependencies)

**Test Files**:
- `test_recursive_book_analysis.py` (16 tests) - Book analysis pipeline
- `test_recommendation_integration.py` (14 tests) - Recommendation system
- `test_phase6_1_automated_book_analysis.py` (7 tests) - Formula extraction

**What's Tested**:
- ✅ Book manager S3 operations
- ✅ Recursive analyzer convergence tracking
- ✅ Recommendation generation
- ✅ Phase mapping
- ✅ Plan override management
- ✅ Formula extraction and categorization
- ✅ Formula validation

### Category E: Edge Cases & Specialized (26 tests)

**Purpose**: Test edge cases and failure scenarios
**Execution Time**: ~1 second
**Skip Rate**: 5% (optional live DB)

**Test Files**:
- `test_tier4_edge_cases.py` (18 tests) - Edge case handling
- `test_dims_integration.py` (8 tests) - Data inventory management

**What's Tested**:
- ✅ Malformed YAML handling
- ✅ Invalid SQL queries
- ✅ Concurrent conflicts
- ✅ GitHub rate limiting
- ✅ Cost limit enforcement
- ✅ Data inventory scanning
- ✅ Metrics loading
- ✅ Schema parsing

---

## Environment Setup

### Required Environment Variables

```bash
# Core MCP Configuration
export RDS_HOST="localhost"
export RDS_PORT="5432"
export RDS_DATABASE="nba_stats"
export RDS_USERNAME="your_username"
export RDS_PASSWORD="your_password"

# S3 Configuration
export S3_BUCKET="nba-mcp-books-20251011"
export S3_REGION="us-east-1"

# AWS Credentials (for integration tests)
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"

# API Keys (for integration tests)
export DEEPSEEK_API_KEY="your_deepseek_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
export OPENAI_API_KEY="your_openai_key"
export GOOGLE_API_KEY="your_google_key"
```

### Mock Credentials for Testing

For testing without real credentials:

```bash
# Mock database credentials (tests will skip if needed)
export RDS_HOST="localhost"
export RDS_PORT="5432"
export RDS_DATABASE="test_db"
export RDS_USERNAME="test_user"
export RDS_PASSWORD="test_pass"

# Mock S3 credentials
export S3_BUCKET="test-bucket"
export AWS_ACCESS_KEY_ID="test_key"
export AWS_SECRET_ACCESS_KEY="test_secret"

# Mock API keys
export DEEPSEEK_API_KEY="test_deepseek_key"
export ANTHROPIC_API_KEY="test_anthropic_key"
```

### Installing Test Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-timeout

# Install optional dependencies
pip install bandit detect-secrets great-expectations
```

---

## Test Markers

Tests are marked with pytest markers for selective execution:

### Available Markers

```python
@pytest.mark.integration    # Integration tests (may require external services)
@pytest.mark.asyncio         # Async tests
@pytest.mark.slow            # Long-running tests (>5 seconds)
@pytest.mark.security        # Security-related tests
@pytest.mark.isolation       # Tests requiring process isolation
@pytest.mark.timeout(60)     # Tests with specific timeout
```

### Running by Marker

```bash
# Run only integration tests
pytest -m integration tests/ -v

# Skip slow tests
pytest -m "not slow" tests/ -v

# Run only security tests
pytest -m security tests/ -v

# Run async tests
pytest -m asyncio tests/ -v

# Combine markers
pytest -m "integration and not slow" tests/ -v
```

---

## Troubleshooting

### Common Issues

#### 1. Async Fixture Errors

**Error**: `AttributeError: 'async_generator' object has no attribute 'X'`

**Solution**: Use `@pytest_asyncio.fixture` instead of `@pytest.fixture`

```python
# Wrong ❌
@pytest.fixture
async def my_fixture():
    ...

# Correct ✅
@pytest_asyncio.fixture
async def my_fixture():
    ...
```

#### 2. Module Import Errors

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**: Ensure project root is in Python path

```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in editable mode
pip install -e .
```

#### 3. Test Collection Warnings

**Error**: `PytestUnknownMarkWarning: Unknown pytest.mark.X`

**Solution**: Register custom marks in `pyproject.toml`

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow (>5 seconds)",
    "security: marks tests as security tests",
]
```

#### 4. Database Connection Failures

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**: Tests should skip gracefully. If they don't:

```python
@pytest.mark.skipif(not os.getenv("RDS_HOST"), reason="No database configured")
def test_database_query():
    ...
```

#### 5. MCP Server Connection Failures

**Error**: `RuntimeError: MCP server failed to start`

**Solution**: These tests require a running MCP server. Either:
- Start the server: `python mcp_server/server.py`
- Or skip these tests: `pytest -k "not mcp_client" tests/`

---

## Best Practices

### 1. Test Isolation

- Use fixtures for setup/teardown
- Clean up resources in `finally` blocks
- Don't rely on test execution order

### 2. Environment-Agnostic Testing

- Tests should work without real credentials
- Use mocks for external services
- Skip tests gracefully when dependencies unavailable

### 3. Fast Execution

- Keep unit tests under 100ms
- Use parallel execution (`-n auto`)
- Mark slow tests with `@pytest.mark.slow`

### 4. Clear Assertions

```python
# Good ✅
assert result.status == "success", f"Expected success but got {result.status}"

# Bad ❌
assert result.status == "success"
```

### 5. Descriptive Test Names

```python
# Good ✅
def test_concurrent_requests_dont_cause_race_conditions():
    ...

# Bad ❌
def test_concurrent():
    ...
```

---

## Coverage Goals

| Component | Target Coverage | Current Coverage |
|-----------|----------------|------------------|
| **Overall** | 90% | 92% ✅ |
| **Core Modules** | 95% | 96% ✅ |
| **Integration** | 85% | 88% ✅ |
| **Critical Paths** | 100% | 100% ✅ |

### Generating Coverage Reports

```bash
# HTML report
pytest tests/ --cov=synthesis --cov=mcp_server --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=synthesis --cov=mcp_server --cov-report=term

# XML report (for CI)
pytest tests/ --cov=synthesis --cov=mcp_server --cov-report=xml
```

---

## CI/CD Integration

See [CI/CD Testing Guide](./CI_CD_TESTING_GUIDE.md) for details on:
- GitHub Actions workflows
- Matrix testing across Python versions
- Coverage reporting
- Test result caching

---

## Additional Resources

- [Test Best Practices](./TEST_BEST_PRACTICES.md) - Detailed best practices
- [CI/CD Testing Guide](./CI_CD_TESTING_GUIDE.md) - CI/CD integration
- [Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md) - General troubleshooting
- [API Documentation](../API_DOCUMENTATION.md) - API reference

---

## Quick Reference Card

```bash
# Most common commands
pytest tests/ -v -n auto          # All tests, parallel
pytest tests/unit/ -v             # Fast unit tests only
pytest tests/integration/ -v      # Integration tests
pytest -m "not slow" tests/       # Skip slow tests
pytest --lf -v                    # Rerun last failures
pytest --cov=. --cov-report=html  # With coverage

# Debugging
pytest tests/test_file.py::test_name -vv --tb=long  # Single test, verbose
pytest tests/ -v -x --pdb                            # Stop on failure, debug
pytest tests/ -v --durations=10                     # Show slowest tests

# Categories
pytest tests/test_e2e_*.py -v                       # Category C: E2E
pytest tests/test_recursive_*.py -v                 # Category D: Analysis
pytest tests/test_tier4_*.py -v                     # Category E: Edge cases
```

---

**Last Updated**: 2025-10-24
**Maintainer**: NBA MCP Synthesis Team
**Version**: 3.0
