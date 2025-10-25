# CI/CD Testing Guide

**NBA MCP Synthesis - Continuous Integration & Deployment Testing**
**Last Updated**: 2025-10-24
**Version**: 2.0

---

## Table of Contents

1. [Overview](#overview)
2. [Current CI/CD Setup](#current-cicd-setup)
3. [GitHub Actions Workflows](#github-actions-workflows)
4. [Recommended Updates](#recommended-updates)
5. [Local CI Simulation](#local-ci-simulation)
6. [Best Practices](#best-practices)

---

## Overview

The NBA MCP Synthesis project uses GitHub Actions for continuous integration and deployment. This guide covers:

- Current workflow configuration
- Test execution in CI/CD
- Coverage reporting
- Matrix testing across Python versions
- Recommended improvements

---

## Current CI/CD Setup

### Workflow Files

Located in `.github/workflows/`:

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `test.yml` | Run test suite | Push, PR, Manual |
| `ci-cd.yml` | Full CI/CD pipeline | Push, PR, Nightly |
| `secrets-scan.yml` | Security scanning | Push |
| `deploy-production.yml` | Production deployment | Tag push |

### Test Execution Strategy

**Current Approach**:
1. **Quality Checks**: Linting, formatting, type checking
2. **Unit Tests**: Fast, isolated tests
3. **Integration Tests**: External service tests (mocked)
4. **E2E Tests**: Complete workflow validation
5. **Security Scans**: Secret detection, vulnerability scanning

---

## GitHub Actions Workflows

### test.yml - Main Test Workflow

**File**: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov pytest-xdist

    - name: Run unit tests
      run: |
        pytest tests/ -v -m "not integration" \
               --cov=synthesis --cov=mcp_server \
               --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### ci-cd.yml - Full CI/CD Pipeline

**File**: `.github/workflows/ci-cd.yml`

```yaml
name: NBA MCP CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: "0 2 * * *"  # Nightly at 2 AM

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"

      - name: Lint with flake8
        run: |
          pip install flake8
          flake8 mcp_server/ --count --select=E9,F63,F7,F82

      - name: Security scan with bandit
        run: |
          pip install bandit
          bandit -r mcp_server/ -ll

  test:
    runs-on: ubuntu-latest
    needs: quality

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: nba_stats_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pytest tests/ -v -n auto \
                 --cov=synthesis --cov=mcp_server \
                 --cov-report=xml
```

---

## Recommended Updates

### Update 1: Add New Test Categories

**Add to test.yml**:

```yaml
- name: Run Category C (E2E Workflows)
  run: |
    pytest tests/test_e2e_workflow.py \
           tests/test_e2e_deployment_flow.py \
           -v --tb=short
  continue-on-error: false

- name: Run Category D (Analysis Frameworks)
  run: |
    pytest tests/test_recursive_book_analysis.py \
           tests/test_recommendation_integration.py \
           tests/test_phase6_1_automated_book_analysis.py \
           -v --tb=short
  continue-on-error: false

- name: Run Category E (Edge Cases)
  run: |
    pytest tests/test_tier4_edge_cases.py \
           tests/test_dims_integration.py \
           -v --tb=short
  continue-on-error: false
```

### Update 2: Enhanced Coverage Reporting

```yaml
- name: Run tests with coverage
  run: |
    pytest tests/ -v -n auto \
           --cov=synthesis \
           --cov=mcp_server \
           --cov-report=xml \
           --cov-report=html \
           --cov-report=term-missing \
           --cov-fail-under=90

- name: Upload coverage reports
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: true
```

### Update 3: Test Result Artifacts

```yaml
- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: test-results-${{ matrix.python-version }}
    path: |
      test-reports/
      htmlcov/
    retention-days: 30

- name: Publish test summary
  if: always()
  uses: dorny/test-reporter@v1
  with:
    name: Test Results (Python ${{ matrix.python-version }})
    path: test-reports/*.xml
    reporter: java-junit
```

### Update 4: Test Result Caching

```yaml
- name: Cache test results
  uses: actions/cache@v3
  with:
    path: .pytest_cache
    key: pytest-cache-${{ runner.os }}-${{ hashFiles('tests/**/*.py') }}
    restore-keys: |
      pytest-cache-${{ runner.os }}-
```

### Update 5: Matrix Testing Enhancement

```yaml
strategy:
  fail-fast: false  # Continue testing other versions on failure
  matrix:
    python-version: ['3.9', '3.10', '3.11', '3.12']
    os: [ubuntu-latest, macos-latest]
    include:
      - python-version: '3.11'
        os: ubuntu-latest
        coverage: true  # Only collect coverage on one combination
```

---

## Local CI Simulation

### Running Tests Locally Like CI

```bash
# Install CI dependencies
pip install pytest pytest-asyncio pytest-cov pytest-xdist flake8 bandit

# Run linting (like CI quality check)
flake8 mcp_server/ --count --select=E9,F63,F7,F82 --show-source

# Run security scan
bandit -r mcp_server/ -ll

# Run tests with coverage (like CI)
pytest tests/ -v -n auto \
       --cov=synthesis --cov=mcp_server \
       --cov-report=xml --cov-report=term

# Check coverage threshold
pytest tests/ --cov=synthesis --cov=mcp_server --cov-fail-under=90
```

### Using Act to Run GitHub Actions Locally

[Act](https://github.com/nektos/act) allows running GitHub Actions locally:

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflow locally
act -j test  # Run 'test' job

# Run specific workflow
act -W .github/workflows/test.yml

# Run with specific event
act pull_request
```

### Docker-Based Testing

```bash
# Build test container
docker build -t nba-mcp-test -f Dockerfile.test .

# Run tests in container
docker run --rm nba-mcp-test pytest tests/ -v -n auto

# Run with volume mount for live code
docker run --rm -v $(pwd):/app nba-mcp-test pytest tests/ -v
```

---

## Best Practices

### 1. Fast CI Execution

**Strategy**:
- Use test parallelization (`-n auto`)
- Cache dependencies
- Use matrix strategy efficiently
- Skip optional tests in CI

```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

- name: Run tests in parallel
  run: pytest tests/ -v -n auto -m "not slow"
```

### 2. Fail Fast vs. Continue

**Fail Fast** (stop on first failure):
```yaml
strategy:
  fail-fast: true
```

**Continue** (run all tests):
```yaml
strategy:
  fail-fast: false
```

**Recommendation**: Use `fail-fast: false` for comprehensive testing

### 3. Environment Variables

```yaml
env:
  # Global env vars for all steps
  RDS_HOST: localhost
  RDS_PORT: 5432

jobs:
  test:
    env:
      # Job-level env vars
      TEST_ENV: ci

    steps:
      - name: Run tests
        env:
          # Step-level env vars
          PYTEST_ADDOPTS: "-v -n auto"
        run: pytest tests/
```

### 4. Conditional Test Execution

```yaml
- name: Run integration tests
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  run: pytest tests/integration/ -v

- name: Run slow tests
  if: github.event_name == 'schedule'  # Only in nightly builds
  run: pytest tests/ -v -m slow
```

### 5. Test Result Reporting

```yaml
- name: Generate test report
  if: always()
  run: |
    pytest tests/ --junitxml=test-results/junit.xml \
           --html=test-results/report.html \
           --self-contained-html

- name: Comment test results on PR
  if: github.event_name == 'pull_request'
  uses: EnricoMi/publish-unit-test-result-action@v2
  with:
    files: test-results/*.xml
```

---

## Troubleshooting CI Issues

### Tests Pass Locally But Fail in CI

**Common Causes**:
1. **Environment differences**: Different Python version, OS, dependencies
2. **Missing environment variables**: Not set in CI
3. **Timing issues**: Race conditions in CI environment
4. **File system differences**: Path separators, permissions

**Solutions**:
```bash
# Test with same Python version as CI
pyenv install 3.11
pyenv local 3.11
pytest tests/

# Test in clean environment
python -m venv clean_env
source clean_env/bin/activate
pip install -r requirements.txt
pytest tests/

# Use Docker to match CI exactly
docker run -it python:3.11-slim bash
```

### Flaky Tests in CI

**Identification**:
```yaml
- name: Run tests with retries
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    command: pytest tests/ -v --count=3  # Run each test 3 times
```

**Fix Strategies**:
1. Add proper waits/sleeps
2. Use fixtures for setup/teardown
3. Mock time-dependent code
4. Increase timeouts for slow operations

### Coverage Drops in CI

**Debugging**:
```yaml
- name: Debug coverage
  run: |
    pytest tests/ --cov=synthesis --cov-report=term-missing
    # Shows which lines are missing coverage
```

---

## Pre-commit Hooks

### Setup

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120']

  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest-fast
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [tests/unit/, -v, -x]  # Only fast unit tests
EOF

# Install hooks
pre-commit install
```

---

## Monitoring & Metrics

### Test Execution Metrics

Track over time:
- **Total test count**: Should increase with features
- **Execution time**: Should stay under 5 minutes
- **Flaky test rate**: Should be < 1%
- **Coverage percentage**: Should stay > 90%

### Dashboards

Use GitHub Actions dashboard or tools like:
- **Codecov**: Coverage trends
- **SonarCloud**: Code quality metrics
- **TestRail**: Test case management

---

## Additional Resources

- [Testing Guide](./TESTING_GUIDE.md) - Comprehensive testing guide
- [Test Best Practices](./TEST_BEST_PRACTICES.md) - Testing best practices
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)

---

**Last Updated**: 2025-10-24
**Maintainer**: NBA MCP Synthesis Team
**Version**: 2.0
