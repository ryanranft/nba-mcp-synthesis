# GitHub Actions Workflows

## Workflows

### test.yml - Continuous Integration
**Trigger:** Every push and pull request to main/develop

**Jobs:**
- **test** - Runs on Python 3.9, 3.10, 3.11
  - Install dependencies
  - Lint with flake8
  - Run unit tests with coverage
  - Upload coverage to Codecov
  - Test import integrity

- **lint** - Code quality checks
  - Black formatting
  - isort import sorting
  - mypy type checking

### benchmark.yml - Performance Benchmarks
**Trigger:** Weekly (Sunday) or manual

**Jobs:**
- Run complete benchmark suite
- Upload results as artifacts
- Comment on PRs with benchmark comparison

## Setup Required

### GitHub Secrets
Add these secrets to your repository settings:

```
RDS_HOST
RDS_DATABASE
RDS_USERNAME
RDS_PASSWORD
S3_BUCKET
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
DEEPSEEK_API_KEY
ANTHROPIC_API_KEY
```

### Codecov (Optional)
- Sign up at codecov.io
- Add repository
- Token is automatically detected

## Usage

### Run Tests Locally
```bash
pytest tests/ -v --cov=synthesis --cov=mcp_server
```

### Run Benchmarks Locally
```bash
python scripts/benchmark_system.py
```

### Manual Benchmark Run
Go to Actions > Performance Benchmarks > Run workflow
