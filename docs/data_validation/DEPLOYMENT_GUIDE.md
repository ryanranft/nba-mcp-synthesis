# Data Validation Infrastructure Deployment Guide

**Phase 10A Week 2 - Agent 4 - Phase 5**
**Created**: 2025-10-25
**Status**: Production Ready

Complete guide for deploying the NBA MCP data validation infrastructure.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Health Checks](#health-checks)
7. [Deployment Steps](#deployment-steps)
8. [Post-Deployment Validation](#post-deployment-validation)
9. [Rollback Procedures](#rollback-procedures)
10. [Monitoring Setup](#monitoring-setup)

---

## Overview

This guide covers deploying the complete data validation infrastructure including:

- Data validation pipeline
- Data cleaning module
- Data profiling module
- Integrity checking module
- Great Expectations integration (optional)

**Deployment Time:** 30-45 minutes
**Complexity:** Medium
**Required Access:** Admin/deployment role

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 10 GB | 20+ GB |
| Python | 3.9+ | 3.11+ |

### Software Dependencies

```bash
# Python 3.9 or higher
python --version  # Should be >= 3.9

# pip (latest version)
pip --version  # Should be >= 23.0

# Git
git --version

# Virtual environment (recommended)
python -m venv --help
```

### Access Requirements

- [ ] SSH access to deployment server
- [ ] Git repository access
- [ ] AWS credentials (if using AWS services)
- [ ] Database credentials (if using database features)
- [ ] Secrets manager access
- [ ] Monitoring system access

### Network Requirements

- Outbound internet access for pip packages
- Access to internal package repositories (if applicable)
- Database connectivity (if applicable)
- Monitoring endpoints accessible

---

## Environment Setup

### 1. Create Python Virtual Environment

```bash
# Navigate to project directory
cd /path/to/nba-mcp-synthesis

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Verify activation
which python  # Should point to venv/bin/python
```

### 2. Set Environment Variables

```bash
# Create .env file
cat > .env <<EOF
# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# Resource Limits
MAX_DATASET_ROWS=1000000
MAX_MEMORY_MB=2048
VALIDATION_TIMEOUT_SECONDS=120

# Database (if applicable)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nba_mcp
DB_USER=validation_user
# DB_PASSWORD set via secrets manager

# Monitoring
MONITORING_ENABLED=true
METRICS_PORT=9090

# Feature Flags
ENABLE_GE_INTEGRATION=false
ENABLE_ADVANCED_PROFILING=true
ENABLE_RBAC=false
EOF

# Load environment variables
source .env

# Or export individually
export ENVIRONMENT=production
export LOG_LEVEL=INFO
```

### 3. Configure Secrets

```bash
# Using environment variables (development)
export DB_PASSWORD='your_db_password'
export API_KEY='your_api_key'

# Using AWS Secrets Manager (production)
aws secretsmanager create-secret \
    --name nba-mcp/validation/db-password \
    --secret-string "your_db_password"

# Using secrets file (not recommended for production)
cat > secrets.yaml <<EOF
database:
  password: "your_db_password"
api:
  key: "your_api_key"
EOF
chmod 600 secrets.yaml
```

---

## Installation

### 1. Clone Repository

```bash
# Clone from Git
git clone https://github.com/your-org/nba-mcp-synthesis.git
cd nba-mcp-synthesis

# Checkout specific version/tag
git checkout tags/v1.0.0  # Or specific branch
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "pandas|numpy|scikit-learn"

# Expected output:
# numpy                 1.24.3
# pandas                2.0.3
# scikit-learn          1.3.0
```

### 3. Install Validation Package

```bash
# Install in development mode (for testing)
pip install -e .

# OR install as package (for production)
pip install .

# Verify installation
python -c "from mcp_server.data_validation_pipeline import DataValidationPipeline; print('OK')"
# Should print: OK
```

---

## Configuration

### 1. Validation Configuration

Create `config/validation_config.yaml`:

```yaml
# config/validation_config.yaml
validation:
  # Resource limits
  max_rows: 1_000_000
  max_columns: 1000
  max_memory_mb: 2048
  timeout_seconds: 120

  # Feature flags
  enable_schema_validation: true
  enable_quality_checks: true
  enable_business_rules: true
  enable_integrity_checks: true

  # Cleaning configuration
  cleaning:
    remove_duplicates: true
    impute_missing: true
    imputation_strategy: "median"  # mean, median, mode
    detect_outliers: true
    outlier_method: "iqr"  # iqr, zscore, isolation_forest

  # Profiling configuration
  profiling:
    generate_statistics: true
    detect_drift: true
    calculate_quality_score: true

  # Business rules
  business_rules:
    player_stats:
      - name: "valid_points_range"
        expression: "points >= 0 and points <= 100"
      - name: "valid_games_played"
        expression: "games_played >= 0 and games_played <= 82"

# Logging configuration
logging:
  level: INFO
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  file: "/var/log/nba-mcp/validation.log"
  max_bytes: 10485760  # 10 MB
  backup_count: 5
```

### 2. Load Configuration

```python
# In your application code
from mcp_server.data_validation_pipeline import DataValidationPipeline
import yaml

# Load config
with open('config/validation_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize pipeline with config
pipeline = DataValidationPipeline(config=config['validation'])
```

---

## Health Checks

### 1. System Health

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check disk space
df -h

# Check memory
free -h

# Check CPU
top -n 1
```

### 2. Application Health

```bash
# Test import
python -c "from mcp_server.data_validation_pipeline import DataValidationPipeline; print('OK')"

# Run simple validation test
python <<EOF
import pandas as pd
from mcp_server.data_validation_pipeline import DataValidationPipeline

df = pd.DataFrame({
    'player_id': [1, 2, 3],
    'points': [25, 30, 22],
})

pipeline = DataValidationPipeline()
result = pipeline.validate(df, 'player_stats')
print(f"Validation result: {result.current_stage}")
print("Health check: PASSED")
EOF
```

### 3. Dependency Health

```bash
# Run security scan
pip install safety
safety check

# Check for outdated packages
pip list --outdated
```

---

## Deployment Steps

### Step 1: Pre-Deployment Checks

```bash
# Run this before deploying
./scripts/pre_deployment_check.sh

# Or manually:
# 1. Check all tests pass
pytest tests/ -v --tb=short

# 2. Check code quality
# flake8 mcp_server/

# 3. Check security
safety check

# 4. Verify configuration
python -c "import yaml; yaml.safe_load(open('config/validation_config.yaml'))"
```

### Step 2: Deploy Using Automation Script

```bash
# Use the automated deployment script
./scripts/deploy_validation_infrastructure.sh

# With specific environment
./scripts/deploy_validation_infrastructure.sh production

# Dry run (show what would be done)
./scripts/deploy_validation_infrastructure.sh --dry-run
```

### Step 3: Manual Deployment (Alternative)

```bash
# 1. Stop existing services (if applicable)
# systemctl stop nba-mcp-validation  # If using systemd

# 2. Backup current version
cp -r /opt/nba-mcp/validation /opt/nba-mcp/validation.backup.$(date +%Y%m%d_%H%M%S)

# 3. Deploy new version
cd /opt/nba-mcp/validation
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 4. Run migrations (if applicable)
# python scripts/migrate_data.py

# 5. Start services
# systemctl start nba-mcp-validation
```

### Step 4: Service Configuration (Systemd)

Create `/etc/systemd/system/nba-mcp-validation.service`:

```ini
[Unit]
Description=NBA MCP Data Validation Service
After=network.target

[Service]
Type=simple
User=nba-mcp
Group=nba-mcp
WorkingDirectory=/opt/nba-mcp/validation
Environment="PATH=/opt/nba-mcp/validation/venv/bin"
Environment="ENVIRONMENT=production"
EnvironmentFile=/opt/nba-mcp/validation/.env
ExecStart=/opt/nba-mcp/validation/venv/bin/python -m mcp_server.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable nba-mcp-validation

# Start service
sudo systemctl start nba-mcp-validation

# Check status
sudo systemctl status nba-mcp-validation
```

---

## Post-Deployment Validation

### 1. Smoke Tests

```bash
# Test validation endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Test validation functionality
python <<EOF
import pandas as pd
from mcp_server.data_validation_pipeline import DataValidationPipeline

# Sample data
df = pd.DataFrame({
    'player_id': range(100),
    'points': [25] * 100,
    'games_played': [10] * 100,
})

pipeline = DataValidationPipeline()
result = pipeline.validate(df, 'player_stats')

assert result.current_stage == 'COMPLETE'
print("✓ Validation pipeline working")
EOF
```

### 2. Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# Expected: All tests passing
```

### 3. Performance Tests

```bash
# Run performance benchmarks
pytest tests/benchmarks/test_validation_performance.py -v

# Verify performance meets baselines
```

### 4. End-to-End Tests

```bash
# Run E2E workflow tests
pytest tests/e2e/test_complete_workflows.py -v

# Expected: All workflows completing successfully
```

---

## Rollback Procedures

### Automated Rollback

```bash
# Use deployment script rollback feature
./scripts/deploy_validation_infrastructure.sh --rollback

# This will:
# 1. Stop current service
# 2. Restore previous backup
# 3. Restart service
# 4. Verify health
```

### Manual Rollback

```bash
# 1. Stop service
sudo systemctl stop nba-mcp-validation

# 2. Find backup
ls -lt /opt/nba-mcp/validation.backup.*

# 3. Restore backup
BACKUP_DIR="/opt/nba-mcp/validation.backup.20251025_143000"
rm -rf /opt/nba-mcp/validation
cp -r $BACKUP_DIR /opt/nba-mcp/validation

# 4. Restart service
sudo systemctl start nba-mcp-validation

# 5. Verify
sudo systemctl status nba-mcp-validation
curl http://localhost:8000/health
```

### Rollback Verification

```bash
# Check version
python -c "from mcp_server import __version__; print(__version__)"

# Run health checks
./scripts/health_check.sh

# Verify tests pass
pytest tests/test_data_validation_pipeline.py -v
```

---

## Monitoring Setup

### 1. Application Metrics

```python
# In your application
from mcp_server.monitoring import MetricsCollector

metrics = MetricsCollector()

# Track validation metrics
metrics.increment('validations_total')
metrics.histogram('validation_duration_seconds', duration)
metrics.gauge('validation_dataset_rows', len(df))
```

### 2. Health Check Endpoint

```python
# health_check.py
from flask import Flask, jsonify
from mcp_server.data_validation_pipeline import DataValidationPipeline

app = Flask(__name__)

@app.route('/health')
def health_check():
    try:
        # Test validation pipeline
        pipeline = DataValidationPipeline()
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8000)
```

### 3. Monitoring Dashboards

**CloudWatch (AWS):**

```bash
# Push custom metrics
aws cloudwatch put-metric-data \
    --namespace NBA-MCP/Validation \
    --metric-name ValidationsPerMinute \
    --value 100 \
    --unit Count
```

**Prometheus:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'nba-mcp-validation'
    static_configs:
      - targets: ['localhost:9090']
```

**Datadog:**

```python
from datadog import initialize, statsd

initialize(api_key='your_api_key')

# Track metrics
statsd.increment('nba_mcp.validation.count')
statsd.histogram('nba_mcp.validation.duration', duration)
```

---

## Troubleshooting

For common issues and solutions, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

**Common issues:**
- Import errors → Check Python version and dependencies
- Memory errors → Check resource limits and dataset size
- Performance issues → Review performance benchmarks
- Configuration errors → Validate YAML syntax

---

## Additional Resources

- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md) - Pre/post deployment checks
- [Troubleshooting Guide](./TROUBLESHOOTING.md) - Common issues and solutions
- [Security Guide](./SECURITY.md) - Security best practices
- [Performance Benchmarks](./PERFORMANCE_BENCHMARKS.md) - Expected performance

---

## Support

**For deployment issues:**
- Email: ops@nba-mcp.example.com
- Slack: #deployment-support
- PagerDuty: Escalate to ops team

**For technical questions:**
- Documentation: `/docs/data_validation/`
- Code: `mcp_server/data_validation_pipeline.py`
- Tests: `tests/test_data_validation_pipeline.py`

---

**Last Updated**: 2025-10-25
**Version**: 1.0
**Maintainer**: Agent 4 - Data Validation Team
