# NBA MCP Operations Guide

## Overview

This guide provides operational procedures for running and maintaining the NBA MCP system in production.

**Audience:** DevOps Engineers, SREs, ML Engineers
**Version:** 2.0
**Last Updated:** October 2025

---

## Table of Contents

1. [System Monitoring](#system-monitoring)
2. [Common Operations](#common-operations)
3. [Troubleshooting](#troubleshooting)
4. [Maintenance Procedures](#maintenance-procedures)
5. [Performance Tuning](#performance-tuning)
6. [Backup & Recovery](#backup--recovery)

---

## System Monitoring

### Health Checks

#### System-Wide Health Check

```python
from mcp_server.system_health import SystemHealthChecker

# Check overall system health
checker = SystemHealthChecker()
health = checker.check_system_health()

print(f"Status: {health['status']}")
print(f"Healthy: {health['healthy_components']}/{health['total_components']}")
```

**Expected Output:**
```
Status: healthy
Healthy: 8/8 components
```

#### Component-Specific Health Checks

```python
# Check data validation
val_health = checker.check_component_health('data_validation')
print(f"Data Validation: {val_health.status.value}")

# Check model deployment
deploy_health = checker.check_component_health('model_deployment')
print(f"Deployment: {deploy_health.status.value}")
```

#### Quick Health Check (CLI)

```bash
# Quick health check
python -c "from mcp_server.system_health import quick_health_check; print(quick_health_check())"

# Detailed health summary
python -c "from mcp_server.system_health import SystemHealthChecker; print(SystemHealthChecker().get_health_summary())"
```

### Monitoring Dashboards

#### MLflow Dashboard

**URL:** `http://mlflow-server:5000`

**Metrics to Monitor:**
- Active experiments
- Model training runs
- Model versions in registry
- Experiment run times

#### Model Performance Dashboard

**Key Metrics:**
- Prediction accuracy (>85% target)
- Prediction latency (<50ms target)
- Throughput (requests per second)
- Error rate (<1% target)

#### System Metrics

**Infrastructure:**
- CPU usage (<70%)
- Memory usage (<80%)
- Disk usage (<85%)
- Network I/O

**Application:**
- Active model versions
- Cache hit rate (>80% target)
- Database connection pool utilization (<80%)

### Alerts

#### Critical Alerts

**Requires Immediate Action:**
- `CRITICAL: High Error Rate` - Error rate >5%
- `CRITICAL: System Unhealthy` - Multiple components down
- `CRITICAL: Database Connection Failed`
- `CRITICAL: Model Serving Down`

**Response:** Follow [Incident Response Guide](checklists/INCIDENT_RESPONSE.md)

#### Warning Alerts

**Requires Investigation:**
- `WARNING: Feature Drift Detected` - Input distribution changed
- `WARNING: Performance Degradation` - Accuracy dropped >2%
- `WARNING: High Latency` - Response time >100ms
- `WARNING: Cache Hit Rate Low` - <70%

**Response:** Investigate within 1 hour

#### Info Alerts

**Informational:**
- `INFO: Model Promoted` - New model version promoted
- `INFO: Scheduled Maintenance` - Planned maintenance window
- `INFO: Cache Cleared` - Cache was cleared

---

## Common Operations

### Managing Models

#### List All Models

```python
from mcp_server.model_registry import ModelRegistry

registry = ModelRegistry()

# List all models
models = registry.list_models()
for model in models:
    print(f"{model['name']} v{model['version']} - {model['stage']}")
```

#### Promote Model to Production

```python
from mcp_server.model_registry import ModelRegistry, ModelStage

registry = ModelRegistry()

# Promote model to production
registry.promote_model(
    model_name="nba_win_predictor",
    version="v2.0",
    target_stage=ModelStage.PRODUCTION
)

print("Model promoted to production")
```

#### Rollback to Previous Version

```python
# Get current production model
current = registry.get_model_by_stage("nba_win_predictor", ModelStage.PRODUCTION)
print(f"Current: v{current['version']}")

# Promote previous version
registry.promote_model(
    model_name="nba_win_predictor",
    version="v1.5",  # Previous stable version
    target_stage=ModelStage.PRODUCTION
)

print("Rolled back to v1.5")
```

### Managing Deployments

#### Deploy New Model Version

```python
from mcp_server.model_serving import ModelServingManager
from mcp_server.model_registry import ModelRegistry
import joblib

# Load model from registry
registry = ModelRegistry()
model_info = registry.get_model("nba_win_predictor", "v2.0")
model = joblib.load(model_info['artifact_path'])

# Deploy model
serving = ModelServingManager()
serving.deploy_model(
    model_id="nba_win_predictor",
    version="v2.0",
    model=model,
    metadata={"description": "New season model"}
)

print("Model v2.0 deployed")
```

#### Setup A/B Testing

```python
# Deploy two versions with traffic split
serving.deploy_model("nba_win_predictor", "v2.0", model_v2)
serving.deploy_model("nba_win_predictor", "v1.5", model_v15)

# Configure A/B test: 80% v2.0, 20% v1.5
serving.configure_ab_test(
    model_id="nba_win_predictor",
    version_weights={"v2.0": 0.8, "v1.5": 0.2}
)

print("A/B test configured")
```

#### Stop A/B Testing

```python
# Remove old version
serving.undeploy_model("nba_win_predictor", "v1.5")

# 100% traffic to v2.0
serving.configure_ab_test(
    model_id="nba_win_predictor",
    version_weights={"v2.0": 1.0}
)

print("A/B test stopped, 100% to v2.0")
```

### Managing Monitoring

#### Setup Drift Monitoring

```python
from mcp_server.model_monitoring import ModelMonitor
import pandas as pd

# Initialize monitor
monitor = ModelMonitor(
    model_id="nba_win_predictor",
    model_version="v2.0",
    drift_threshold=0.05
)

# Set reference data (training data)
X_train = pd.read_csv("training_features.csv")
monitor.set_reference_data(features=X_train)

print("Drift monitoring configured")
```

#### Check for Drift

```python
# Get recent predictions
current_data = pd.read_csv("recent_predictions.csv")

# Detect drift
drift_results = monitor.detect_feature_drift(
    current_data=current_data,
    method=DriftMethod.KS_TEST
)

# Check results
for feature, result in drift_results.items():
    if result['drift_detected']:
        print(f"⚠️  Drift detected in {feature}: p={result['p_value']:.4f}")
    else:
        print(f"✓ No drift in {feature}")
```

#### Review Alerts

```python
# Get recent alerts
alerts = monitor.get_alerts(hours=24)

print(f"Alerts in last 24 hours: {len(alerts)}")

for alert in alerts:
    print(f"[{alert.severity.value}] {alert.alert_type.value}: {alert.message}")
```

### Managing Cache

#### Check Cache Statistics

```python
from mcp_server.system_optimizer import get_system_stats

stats = get_system_stats()

print(f"Model Cache Hit Rate: {stats['model_cache']['hit_rate']:.2%}")
print(f"Data Cache Hit Rate: {stats['data_cache']['hit_rate']:.2%}")
print(f"Model Cache Size: {stats['model_cache']['size']}/{stats['model_cache']['max_size']}")
```

#### Clear Cache

```python
from mcp_server.system_optimizer import clear_all_caches

# Clear all caches (use with caution)
clear_all_caches()
print("All caches cleared")
```

**Note:** Only clear cache during maintenance windows or when troubleshooting.

---

## Troubleshooting

### High Prediction Latency

**Symptoms:**
- Prediction responses taking >100ms
- Timeout errors
- Slow dashboard loading

**Diagnosis:**
```python
# Check cache hit rate
stats = get_system_stats()
print(f"Cache hit rate: {stats['model_cache']['hit_rate']:.2%}")

# Check model cache
if stats['model_cache']['hit_rate'] < 0.7:
    print("Low cache hit rate - models being reloaded frequently")
```

**Solutions:**
1. **Increase cache size:**
   ```python
   # In config
   MODEL_CACHE_SIZE = 100  # Increase from 50
   ```

2. **Warm up cache:**
   ```python
   # Preload frequently used models
   serving = ModelServingManager()
   serving.deploy_model("nba_win_predictor", "v2.0", model)
   ```

3. **Use batch predictions:**
   ```python
   # Predict multiple games at once
   predictions = serving.batch_predict("nba_win_predictor", games_list)
   ```

### Model Drift Detected

**Symptoms:**
- Drift alerts in monitoring
- Decreasing prediction accuracy
- Changed input distributions

**Diagnosis:**
```python
# Check drift details
drift_results = monitor.detect_feature_drift(current_data)

drifted_features = [
    f for f, r in drift_results.items()
    if r['drift_detected']
]

print(f"Drifted features: {drifted_features}")
```

**Solutions:**
1. **Investigate data quality:**
   - Check for data source changes
   - Validate recent data
   - Compare distributions

2. **Retrain model:**
   ```python
   from mcp_server.training_pipeline import TrainingPipeline

   # Retrain with recent data
   pipeline = TrainingPipeline()
   new_model = pipeline.train(updated_data)
   ```

3. **Update reference data:**
   ```python
   # Update baseline for drift detection
   monitor.set_reference_data(features=recent_training_data)
   ```

### Database Connection Errors

**Symptoms:**
- `DatabaseConnectionError`
- Timeouts on queries
- Models failing to load from registry

**Diagnosis:**
```bash
# Check database connectivity
python -c "from mcp_server.system_health import SystemHealthChecker; print(SystemHealthChecker().check_component_health('database').status)"
```

**Solutions:**
1. **Check connection pool:**
   ```python
   # Verify pool isn't exhausted
   # Increase pool size if needed
   ```

2. **Restart database connection:**
   ```bash
   # Reconnect to database
   service postgresql restart
   ```

3. **Check database health:**
   ```bash
   # PostgreSQL
   psql -c "SELECT 1"
   ```

### MLflow Connection Issues

**Symptoms:**
- Experiments not logging
- Models not appearing in registry
- `MLflowException`

**Diagnosis:**
```python
import mlflow

try:
    mlflow.set_tracking_uri("http://mlflow-server:5000")
    experiments = mlflow.search_experiments()
    print(f"Connected: {len(experiments)} experiments")
except Exception as e:
    print(f"MLflow error: {e}")
```

**Solutions:**
1. **Verify MLflow server:**
   ```bash
   curl http://mlflow-server:5000/health
   ```

2. **Restart MLflow:**
   ```bash
   mlflow server --host 0.0.0.0 --port 5000
   ```

3. **Check network connectivity:**
   ```bash
   ping mlflow-server
   telnet mlflow-server 5000
   ```

---

## Maintenance Procedures

### Scheduled Maintenance

**Frequency:** Monthly (first Sunday, 2-4 AM UTC)

**Checklist:**
1. ✅ Announce maintenance window (7 days prior)
2. ✅ Take database backup
3. ✅ Clear old logs (>30 days)
4. ✅ Archive old model versions (>90 days)
5. ✅ Update dependencies (security patches)
6. ✅ Run health checks
7. ✅ Verify all tests pass
8. ✅ Monitor for 24 hours post-maintenance

### Database Maintenance

**Weekly Tasks:**
```sql
-- Vacuum database
VACUUM ANALYZE;

-- Update table statistics
ANALYZE models;
ANALYZE predictions;
ANALYZE metrics;

-- Check table sizes
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size(table_name::regclass))
FROM information_schema.tables
WHERE table_schema = 'public';
```

### Log Rotation

**Configuration** (`/etc/logrotate.d/nba-mcp`):
```
/var/log/nba-mcp/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 nba-mcp nba-mcp
    sharedscripts
    postrotate
        systemctl reload nba-mcp
    endscript
}
```

### Model Cleanup

```python
from mcp_server.model_registry import ModelRegistry
from datetime import datetime, timedelta

registry = ModelRegistry()

# Archive models older than 90 days
cutoff_date = datetime.now() - timedelta(days=90)

old_models = registry.list_models(
    filter_func=lambda m: m['created_at'] < cutoff_date
)

for model in old_models:
    if model['stage'] != 'production':
        print(f"Archiving {model['name']} v{model['version']}")
        registry.archive_model(model['name'], model['version'])
```

---

## Performance Tuning

### Database Tuning

**PostgreSQL Configuration:**
```ini
# /etc/postgresql/postgresql.conf

# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB

# Connections
max_connections = 100

# Query Performance
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Cache Tuning

**Optimal Cache Sizes:**
```python
# For high-traffic production
MODEL_CACHE_SIZE = 100
MODEL_CACHE_TTL = 3600  # 1 hour

DATA_CACHE_SIZE = 200
```

### Parallel Processing

**Training Pipeline:**
```python
# Use all available CPU cores
pipeline = TrainingPipeline(n_jobs=-1)

# Or specify number of cores
pipeline = TrainingPipeline(n_jobs=4)
```

---

## Backup & Recovery

### Automated Backups

**Database Backup Script** (`backup_db.sh`):
```bash
#!/bin/bash

# Database backup
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="nba_mcp_db_${DATE}.sql.gz"

pg_dump nba_mcp | gzip > /backups/db/${BACKUP_FILE}

# Upload to S3
aws s3 cp /backups/db/${BACKUP_FILE} s3://nba-mcp-backups/db/

# Cleanup old backups (keep 7 days)
find /backups/db/ -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}"
```

**Cron Schedule:**
```cron
# Daily at 2 AM UTC
0 2 * * * /usr/local/bin/backup_db.sh
```

### Model Artifact Backup

**All model artifacts are automatically backed up to S3 on registration.**

Verify backups:
```bash
aws s3 ls s3://nba-mcp-models/ --recursive | tail -20
```

### Recovery Procedures

See [Disaster Recovery](SYSTEM_ARCHITECTURE.md#disaster-recovery) in System Architecture.

---

## Support & Escalation

### Support Tiers

**Tier 1: DevOps Team**
- Health check failures
- Deployment issues
- Infrastructure problems

**Tier 2: ML Engineering Team**
- Model performance issues
- Drift detection
- Training failures

**Tier 3: Data Science Team**
- Model accuracy degradation
- Feature engineering
- Algorithm selection

### On-Call Rotation

**Schedule:** 24/7 coverage
**Response Time:**
- Critical: 15 minutes
- High: 1 hour
- Medium: 4 hours
- Low: Next business day

---

## Conclusion

This operations guide covers the essential procedures for maintaining the NBA MCP system. For deployment procedures, see [Deployment Guide](DEPLOYMENT_GUIDE.md). For incident response, see [Incident Response Guide](checklists/INCIDENT_RESPONSE.md).

**Key Operational Metrics:**
- ✅ 99.9% uptime target
- ✅ <50ms p95 latency
- ✅ <1% error rate
- ✅ 4-hour recovery time objective (RTO)
