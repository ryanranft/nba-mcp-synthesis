# Data Validation Troubleshooting Guide

**Phase 10A Week 2 - Agent 4 - Phase 5**
**Created**: 2025-10-25

Comprehensive troubleshooting guide for common issues with the data validation infrastructure.

---

## Table of Contents

1. [Import Errors](#import-errors)
2. [Memory Issues](#memory-issues)
3. [Performance Issues](#performance-issues)
4. [Validation Errors](#validation-errors)
5. [Configuration Issues](#configuration-issues)
6. [Database Issues](#database-issues)
7. [Deployment Issues](#deployment-issues)
8. [Monitoring Issues](#monitoring-issues)

---

## Import Errors

### Issue: "ModuleNotFoundError: No module named 'mcp_server'"

**Symptoms:**
```python
>>> from mcp_server.data_validation_pipeline import DataValidationPipeline
ModuleNotFoundError: No module named 'mcp_server'
```

**Causes:**
- Package not installed
- Wrong Python environment
- PYTHONPATH not set

**Solutions:**

```bash
# 1. Verify you're in the correct virtual environment
which python
# Should point to your venv, e.g., /path/to/venv/bin/python

# 2. Install the package
pip install -e .

# 3. Verify installation
python -c "import mcp_server; print(mcp_server.__file__)"

# 4. If still failing, add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/nba-mcp-synthesis"
```

### Issue: "ImportError: cannot import name 'DataValidationPipeline'"

**Symptoms:**
```python
>>> from mcp_server.data_validation_pipeline import DataValidationPipeline
ImportError: cannot import name 'DataValidationPipeline'
```

**Causes:**
- Outdated package cache
- Circular import
- File name conflict

**Solutions:**

```bash
# 1. Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name '*.pyc' -delete

# 2. Reinstall package
pip uninstall -y mcp-server
pip install -e .

# 3. Check for file conflicts
ls -la mcp_server/data_validation_pipeline.py
```

### Issue: Dependency version conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**Solutions:**

```bash
# 1. Check conflicting packages
pip check

# 2. Update requirements
pip install --upgrade -r requirements.txt

# 3. Create fresh virtual environment
deactivate
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Memory Issues

### Issue: "MemoryError" during validation

**Symptoms:**
```python
MemoryError: Unable to allocate array with shape (1000000, 100)
```

**Causes:**
- Dataset too large
- Insufficient memory
- Memory leak

**Solutions:**

```python
# 1. Check dataset size before validation
import pandas as pd

df = pd.read_csv('large_file.csv')
print(f"Dataset: {len(df):,} rows × {len(df.columns)} columns")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# 2. Process in chunks
chunk_size = 10000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    result = pipeline.validate(chunk, 'player_stats')

# 3. Reduce memory usage
df = df.astype({
    'player_id': 'int32',  # Instead of int64
    'points': 'float32',   # Instead of float64
})

# 4. Free memory after validation
import gc
result = pipeline.validate(df, 'player_stats')
del df
gc.collect()
```

**Configuration:**

```yaml
# config/validation_config.yaml
validation:
  max_rows: 100000  # Reduce max rows
  max_memory_mb: 1024  # Reduce memory limit
```

### Issue: Memory usage grows over time

**Symptoms:**
- Memory usage increases with each validation
- Process eventually crashes with OOM

**Diagnosis:**

```python
import tracemalloc

tracemalloc.start()

# Run validation
result = pipeline.validate(df, 'player_stats')

# Check memory
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024**2:.2f} MB, Peak: {peak / 1024**2:.2f} MB")
tracemalloc.stop()
```

**Solutions:**

```python
# 1. Explicitly delete large objects
result = pipeline.validate(df, 'player_stats')
del df
import gc
gc.collect()

# 2. Reinitialize pipeline periodically
for i, df_chunk in enumerate(chunks):
    if i % 100 == 0:
        # Reinitialize every 100 validations
        pipeline = DataValidationPipeline()
    result = pipeline.validate(df_chunk, 'player_stats')
```

---

## Performance Issues

### Issue: Validation taking too long

**Symptoms:**
- Validation of 10K rows taking > 10 seconds
- Timeout errors

**Diagnosis:**

```python
import time

start = time.time()
result = pipeline.validate(df, 'player_stats')
duration = time.time() - start

print(f"Validation took {duration:.2f} seconds for {len(df):,} rows")
print(f"Throughput: {len(df)/duration:.0f} rows/second")
```

**Expected performance (see PERFORMANCE_BENCHMARKS.md):**
- 1K rows: < 500ms
- 10K rows: < 5s
- 100K rows: < 30s

**Solutions:**

```python
# 1. Disable expensive operations
pipeline = DataValidationPipeline(config={
    'enable_schema_validation': True,
    'enable_quality_checks': False,  # Disable if not needed
    'enable_business_rules': True,
    'enable_integrity_checks': False,  # Can be expensive
})

# 2. Optimize data types
df = df.astype({
    'player_id': 'int32',
    'points': 'float32',
})

# 3. Sample large datasets for profiling
if len(df) > 100000:
    df_sample = df.sample(n=10000)
    profile = profiler.profile_dataframe(df_sample)
```

### Issue: High CPU usage

**Symptoms:**
- CPU at 100% during validation
- Server becomes unresponsive

**Diagnosis:**

```bash
# Monitor CPU during validation
top -p $(pgrep -f "python.*validation")

# Or use htop for better visualization
htop
```

**Solutions:**

```python
# 1. Limit outlier detection complexity
from mcp_server.data_cleaning import DataCleaner

cleaner = DataCleaner()
# Use faster IQR method instead of isolation forest
cleaned_df, report = cleaner.clean(
    df,
    outlier_method='iqr'  # Much faster than 'isolation_forest'
)

# 2. Process in smaller batches
batch_size = 5000
for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i+batch_size]
    result = pipeline.validate(batch, 'player_stats')
```

---

## Validation Errors

### Issue: "ValidationError: Schema validation failed"

**Symptoms:**
```
ValidationError: Schema validation failed: Missing required columns: ['player_id']
```

**Diagnosis:**

```python
# Check DataFrame columns
print("DataFrame columns:", df.columns.tolist())

# Check expected schema
from mcp_server.data_validation_pipeline import DATASET_SCHEMAS
print("Expected schema:", DATASET_SCHEMAS.get('player_stats'))
```

**Solutions:**

```python
# 1. Rename columns to match schema
df = df.rename(columns={
    'id': 'player_id',
    'pts': 'points',
})

# 2. Add missing columns with defaults
if 'team_id' not in df.columns:
    df['team_id'] = None

# 3. Use custom schema
custom_schema = {
    'columns': list(df.columns),
    'required_columns': ['player_id'],
}
result = pipeline.validate(df, 'player_stats', schema=custom_schema)
```

### Issue: All data flagged as outliers

**Symptoms:**
- Outlier detection flags >50% of data
- Unrealistic outlier counts

**Diagnosis:**

```python
from mcp_server.data_cleaning import DataCleaner

cleaner = DataCleaner()
outliers = cleaner.detect_outliers(df, column='points', method='iqr')
print(f"Outliers: {outliers.sum()} / {len(df)} ({outliers.sum()/len(df)*100:.1f}%)")
```

**Solutions:**

```python
# 1. Adjust outlier sensitivity
# IQR method: increase multiplier (default 1.5)
outliers = cleaner.detect_outliers(df, column='points', method='iqr', threshold=3.0)

# 2. Use different method
outliers = cleaner.detect_outliers(df, column='points', method='zscore', threshold=4.0)

# 3. Don't remove outliers, just flag them
# In config:
# outlier_action: "flag"  # Instead of "remove"
```

### Issue: Business rules failing unexpectedly

**Symptoms:**
```
BusinessRuleViolation: Rule 'valid_points_range' failed for 100 rows
```

**Diagnosis:**

```python
# Check data distribution
print(df['points'].describe())
print("Points range:", df['points'].min(), "-", df['points'].max())

# Check specific violations
violation_mask = ~((df['points'] >= 0) & (df['points'] <= 100))
print("Violations:")
print(df[violation_mask][['player_id', 'points']])
```

**Solutions:**

```python
# 1. Adjust business rule
# Instead of: points >= 0 and points <= 100
# Use: points >= 0 and points <= 150  # Allow higher scores

# 2. Clean data first
df['points'] = df['points'].clip(lower=0, upper=100)

# 3. Disable strict mode
pipeline = DataValidationPipeline(config={
    'strict_mode': False  # Allow violations, don't fail
})
```

---

## Configuration Issues

### Issue: "FileNotFoundError: config/validation_config.yaml"

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config/validation_config.yaml'
```

**Solutions:**

```bash
# 1. Create config directory and file
mkdir -p config
cp config/validation_config.yaml.example config/validation_config.yaml

# 2. Use absolute path
export VALIDATION_CONFIG=/opt/nba-mcp/config/validation_config.yaml

# 3. Provide config programmatically
from mcp_server.data_validation_pipeline import DataValidationPipeline

pipeline = DataValidationPipeline(config={
    'enable_schema_validation': True,
    'enable_quality_checks': True,
})
```

### Issue: Environment variables not loading

**Symptoms:**
- Configuration not being applied
- Using default values instead of configured values

**Solutions:**

```bash
# 1. Verify environment variables are set
printenv | grep VALIDATION

# 2. Load .env file
source .env
# Or use python-dotenv
pip install python-dotenv

# In Python:
from dotenv import load_dotenv
load_dotenv()

# 3. Check .env file syntax
# No spaces around =
# CORRECT:
MAX_ROWS=1000000
# INCORRECT:
# MAX_ROWS = 1000000
```

---

## Database Issues

### Issue: "OperationalError: could not connect to server"

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server: Connection refused
```

**Diagnosis:**

```bash
# Check database is running
pg_isready -h localhost -p 5432

# Test connection
psql -h localhost -U validation_user -d nba_mcp

# Check network connectivity
nc -zv localhost 5432
```

**Solutions:**

```bash
# 1. Start database
sudo systemctl start postgresql

# 2. Check firewall
sudo ufw status
sudo ufw allow 5432/tcp

# 3. Verify database exists
psql -U postgres -c "\l" | grep nba_mcp

# 4. Create database if missing
createdb -U postgres nba_mcp
```

### Issue: "AuthenticationError: password authentication failed"

**Solutions:**

```bash
# 1. Verify credentials
psql -h localhost -U validation_user -d nba_mcp
# If fails, reset password

# 2. Update password
sudo -u postgres psql
ALTER USER validation_user WITH PASSWORD 'new_password';

# 3. Update .env file
DB_PASSWORD=new_password
```

---

## Deployment Issues

### Issue: Service won't start after deployment

**Symptoms:**
```bash
$ sudo systemctl start nba-mcp-validation
Job for nba-mcp-validation.service failed.
```

**Diagnosis:**

```bash
# Check service status
sudo systemctl status nba-mcp-validation

# View recent logs
sudo journalctl -u nba-mcp-validation -n 50

# Check for port conflicts
sudo lsof -i :8000
```

**Solutions:**

```bash
# 1. Fix permissions
sudo chown -R nba-mcp:nba-mcp /opt/nba-mcp/validation
sudo chmod +x /opt/nba-mcp/validation/venv/bin/python

# 2. Fix systemd service file
sudo systemctl daemon-reload
sudo systemctl restart nba-mcp-validation

# 3. Run manually to see errors
cd /opt/nba-mcp/validation
source venv/bin/activate
python -m mcp_server.server
```

### Issue: Health check failing after deployment

**Symptoms:**
```bash
$ curl http://localhost:8000/health
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**Diagnosis:**

```bash
# Check if service is running
sudo systemctl status nba-mcp-validation

# Check which port service is using
sudo netstat -tlnp | grep python

# Test locally
curl http://127.0.0.1:8000/health
```

**Solutions:**

```bash
# 1. Verify service configuration
cat /etc/systemd/system/nba-mcp-validation.service

# 2. Check logs for startup errors
sudo journalctl -u nba-mcp-validation -f

# 3. Restart service
sudo systemctl restart nba-mcp-validation
```

---

## Monitoring Issues

### Issue: Metrics not appearing in dashboard

**Symptoms:**
- Dashboard shows no data
- Metrics endpoint returns 404

**Diagnosis:**

```bash
# Check metrics endpoint
curl http://localhost:9090/metrics

# Verify Prometheus is scraping
curl http://prometheus:9090/api/v1/targets
```

**Solutions:**

```python
# 1. Verify metrics are being collected
from mcp_server.monitoring import MetricsCollector

metrics = MetricsCollector()
metrics.increment('test_metric')
print("Metrics:", metrics.get_all())

# 2. Check Prometheus configuration
# prometheus.yml should have:
# scrape_configs:
#   - job_name: 'nba-mcp-validation'
#     static_configs:
#       - targets: ['localhost:9090']

# 3. Restart Prometheus
sudo systemctl restart prometheus
```

---

## Debug Mode

### Enable verbose logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# Now run validation
from mcp_server.data_validation_pipeline import DataValidationPipeline
pipeline = DataValidationPipeline()
result = pipeline.validate(df, 'player_stats')
```

### Interactive debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use ipdb for better interface
import ipdb; ipdb.set_trace()

# Run code, execution will pause at breakpoint
```

---

## Getting Help

### Before asking for help, collect:

1. **Error message** (full traceback)
2. **Python version** (`python --version`)
3. **Package versions** (`pip list`)
4. **Data sample** (first few rows of DataFrame)
5. **Configuration** (relevant config settings)
6. **Logs** (last 50 lines)

### Support channels:

- **Documentation**: `/docs/data_validation/`
- **GitHub Issues**: Create issue with template
- **Slack**: #data-validation-support
- **Email**: support@nba-mcp.example.com

### Issue template:

```markdown
**Environment:**
- Python version: 3.11.3
- pandas version: 2.0.3
- OS: Ubuntu 22.04

**Issue:**
Brief description of the issue

**Steps to reproduce:**
1. Step 1
2. Step 2
3. ...

**Expected behavior:**
What should happen

**Actual behavior:**
What actually happens

**Error message:**
```
Full error traceback
```

**Data sample:**
```python
# Sample data that reproduces issue
df = pd.DataFrame({...})
```
```

---

**Last Updated**: 2025-10-25
**Version**: 1.0
**Maintainer**: Agent 4 - Data Validation Team
