# MLflow Setup and Integration Guide

**Component:** Model Training & Experimentation
**Module:** `mcp_server/mlflow_integration.py`

Complete guide to MLflow setup, configuration, and usage in the NBA MCP Synthesis project.

---

## Overview

MLflow is an open-source platform for managing the ML lifecycle, including experimentation, reproducibility, and deployment. Our integration provides:

- **Experiment Tracking** - Log parameters, metrics, and artifacts
- **Model Registry** - Version and manage models
- **Run Comparison** - Compare multiple training runs
- **Mock Mode** - Test without MLflow server

---

## Quick Start

### Mock Mode (No Server Required)

Perfect for local development and testing:

```python
from mcp_server.mlflow_integration import get_mlflow_tracker

# Create tracker in mock mode
tracker = get_mlflow_tracker(
    experiment_name="my_experiment",
    mock_mode=True  # No MLflow server needed
)

# Use normally
with tracker.start_run("test_run") as run_id:
    tracker.log_params({"learning_rate": 0.01})
    tracker.log_metric("accuracy", 0.92)
```

### Production Mode (With MLflow Server)

For production experiment tracking:

```python
tracker = get_mlflow_tracker(
    experiment_name="nba_production",
    tracking_uri="http://mlflow-server:5000",
    mock_mode=False
)
```

---

## Installation

### Local Development

```bash
# Install MLflow
pip install mlflow

# Optional: Install database backend
pip install sqlalchemy pymysql  # For MySQL
pip install psycopg2-binary     # For PostgreSQL
```

### Production Dependencies

```bash
# Full MLflow with cloud storage support
pip install mlflow[extras]

# AWS S3 support
pip install boto3

# Azure Blob Storage support
pip install azure-storage-blob

# Google Cloud Storage support
pip install google-cloud-storage
```

---

## MLflow Server Setup

### Option 1: Local SQLite Backend (Development)

```bash
# Start MLflow server with SQLite
mlflow server \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlflow-artifacts \
    --host 0.0.0.0 \
    --port 5000

# Access UI at http://localhost:5000
```

### Option 2: PostgreSQL Backend (Production)

```bash
# Prerequisites
# - PostgreSQL server running
# - Database created: CREATE DATABASE mlflow;

# Start MLflow server
mlflow server \
    --backend-store-uri postgresql://user:password@localhost/mlflow \
    --default-artifact-root s3://my-mlflow-bucket/artifacts \
    --host 0.0.0.0 \
    --port 5000
```

### Option 3: Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.8.0
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://user:password@postgres:5432/mlflow
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://mlflow-artifacts
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    command: >
      mlflow server
      --backend-store-uri postgresql://user:password@postgres:5432/mlflow
      --default-artifact-root s3://mlflow-artifacts
      --host 0.0.0.0
      --port 5000
    depends_on:
      - postgres

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=mlflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
# Start services
docker-compose up -d

# Access UI at http://localhost:5000
```

---

## Configuration

### Environment Variables

```bash
# MLflow Tracking URI
export MLFLOW_TRACKING_URI="http://mlflow-server:5000"

# Experiment name
export MLFLOW_EXPERIMENT_NAME="nba_production"

# Authentication (if enabled)
export MLFLOW_TRACKING_USERNAME="your_username"
export MLFLOW_TRACKING_PASSWORD="your_password"

# AWS credentials (for S3 artifact storage)
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"

# Azure credentials (for Azure Blob Storage)
export AZURE_STORAGE_CONNECTION_STRING="your_connection_string"

# GCP credentials (for Google Cloud Storage)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Python Configuration

```python
# config.py
import os

MLFLOW_CONFIG = {
    "tracking_uri": os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"),
    "experiment_name": os.getenv("MLFLOW_EXPERIMENT_NAME", "nba_default"),
    "artifact_location": os.getenv("MLFLOW_ARTIFACT_LOCATION", "./mlflow-artifacts"),
    "mock_mode": os.getenv("MLFLOW_MOCK_MODE", "false").lower() == "true",
}

# Usage
from mcp_server.mlflow_integration import get_mlflow_tracker

tracker = get_mlflow_tracker(**MLFLOW_CONFIG)
```

---

## Usage Patterns

### Basic Experiment Tracking

```python
from mcp_server.mlflow_integration import get_mlflow_tracker

tracker = get_mlflow_tracker(experiment_name="nba_experiments")

# Start a run
with tracker.start_run("baseline_model") as run_id:
    # Log parameters
    tracker.log_params({
        "algorithm": "random_forest",
        "n_estimators": 100,
        "max_depth": 10
    })

    # Train model
    model = train_model()

    # Log metrics
    tracker.log_metrics({
        "accuracy": 0.92,
        "f1_score": 0.89,
        "roc_auc": 0.94
    })

    # Log artifacts
    tracker.log_artifact("model.pkl")
    tracker.log_artifact("confusion_matrix.png")

print(f"Run ID: {run_id}")
```

### Logging Metrics Over Time

```python
with tracker.start_run("training_progress") as run_id:
    for epoch in range(100):
        # Train for one epoch
        train_loss = train_epoch(model, data)
        val_loss = validate_epoch(model, val_data)

        # Log metrics with step
        tracker.log_metric("train_loss", train_loss, step=epoch)
        tracker.log_metric("val_loss", val_loss, step=epoch)
```

### Model Registration

```python
# Register model after training
tracker.register_model(
    model_uri=f"runs:/{run_id}/model",
    model_name="nba_player_classifier",
    tags={"version": "v1.0", "stage": "production"}
)
```

### Searching Runs

```python
# Find best runs
best_runs = tracker.search_runs(
    filter_string="metrics.accuracy > 0.9",
    max_results=10
)

for run in best_runs:
    print(f"Run {run['run_id']}: {run['metrics']['accuracy']:.4f}")
```

### Comparing Runs

```python
# Compare two runs
comparison = tracker.compare_runs(["run_id_1", "run_id_2"])

print("Parameter differences:")
for param, values in comparison['params'].items():
    print(f"  {param}: {values['run_1']} vs {values['run_2']}")

print("\nMetric differences:")
for metric, values in comparison['metrics'].items():
    diff = values['run_2'] - values['run_1']
    print(f"  {metric}: {diff:+.4f} ({values['run_1']:.4f} → {values['run_2']:.4f})")
```

---

## Mock Mode

Mock mode allows testing without an MLflow server. Perfect for:
- Local development
- Unit tests
- CI/CD pipelines
- Offline development

### Enabling Mock Mode

```python
# Option 1: Direct configuration
tracker = get_mlflow_tracker(
    experiment_name="test_experiment",
    mock_mode=True
)

# Option 2: Environment variable
import os
os.environ["MLFLOW_MOCK_MODE"] = "true"
tracker = get_mlflow_tracker(experiment_name="test_experiment")
```

### Mock Mode Features

```python
# All operations work in mock mode
with tracker.start_run("mock_run") as run_id:
    tracker.log_params({"param1": 1})
    tracker.log_metrics({"accuracy": 0.95})
    tracker.log_artifact("model.pkl")

# Retrieve run (from mock storage)
run = tracker.get_run(run_id)
print(f"Params: {run['params']}")
print(f"Metrics: {run['metrics']}")

# Search runs (from mock storage)
runs = tracker.search_runs()
print(f"Found {len(runs)} runs")
```

### Mock Mode Limitations

- Data stored in memory (lost when process exits)
- No persistent artifact storage
- No model registry
- No UI visualization
- Not suitable for production

---

## Artifact Storage

### Local File System

```python
# Configure local artifact storage
tracker = get_mlflow_tracker(
    experiment_name="local_exp",
    artifact_location="./mlflow-artifacts"
)

# Log artifacts
with tracker.start_run("artifact_demo") as run_id:
    tracker.log_artifact("model.pkl")
    tracker.log_artifact("metrics.json")
    tracker.log_artifact("plots/confusion_matrix.png")
```

### AWS S3

```bash
# Setup
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_DEFAULT_REGION="us-east-1"

# Start MLflow with S3
mlflow server \
    --backend-store-uri postgresql://... \
    --default-artifact-root s3://mlflow-artifacts \
    --host 0.0.0.0 \
    --port 5000
```

```python
# Use normally (artifacts automatically uploaded to S3)
tracker = get_mlflow_tracker(
    experiment_name="s3_exp",
    tracking_uri="http://mlflow-server:5000"
)

with tracker.start_run("s3_run") as run_id:
    tracker.log_artifact("large_model.pkl")  # Uploaded to S3
```

### Azure Blob Storage

```bash
# Setup
export AZURE_STORAGE_CONNECTION_STRING="your_connection_string"

# Start MLflow with Azure
mlflow server \
    --backend-store-uri postgresql://... \
    --default-artifact-root wasbs://mlflow@account.blob.core.windows.net/artifacts \
    --host 0.0.0.0 \
    --port 5000
```

### Google Cloud Storage

```bash
# Setup
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Start MLflow with GCS
mlflow server \
    --backend-store-uri postgresql://... \
    --default-artifact-root gs://mlflow-artifacts \
    --host 0.0.0.0 \
    --port 5000
```

---

## MLflow UI

### Accessing the UI

```bash
# Local server
# Navigate to: http://localhost:5000

# Remote server
# Navigate to: http://mlflow-server:5000
```

### UI Features

1. **Experiments View**
   - List all experiments
   - Filter and search runs
   - Compare metrics across runs

2. **Run Details**
   - View parameters and metrics
   - Download artifacts
   - See run metadata

3. **Charts and Visualizations**
   - Metric plots over time
   - Parallel coordinates plot
   - Scatter plots

4. **Model Registry**
   - Browse registered models
   - View model versions
   - Track model stages (staging, production)

---

## Best Practices

### 1. Use Descriptive Run Names

```python
# Good
with tracker.start_run("rf_100est_d10_2024-10-25") as run_id:
    ...

# Bad
with tracker.start_run("run1") as run_id:
    ...
```

### 2. Tag Runs for Organization

```python
with tracker.start_run("experiment", tags={
    "team": "data_science",
    "model_type": "random_forest",
    "dataset": "nba_2024",
    "environment": "production"
}) as run_id:
    ...
```

### 3. Log All Relevant Information

```python
with tracker.start_run("complete_tracking") as run_id:
    # System info
    tracker.log_params({
        "python_version": "3.11",
        "sklearn_version": "1.3.0",
        "gpu": "NVIDIA A100"
    })

    # Data info
    tracker.log_params({
        "train_size": len(X_train),
        "test_size": len(X_test),
        "n_features": X_train.shape[1]
    })

    # Model params
    tracker.log_params(model.get_params())

    # Metrics
    tracker.log_metrics({
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    })

    # Artifacts
    tracker.log_artifact("model.pkl")
    tracker.log_artifact("feature_importance.csv")
    tracker.log_artifact("confusion_matrix.png")
```

### 4. Use Hierarchical Experiments

```python
# Organize by project/model type
tracker_rf = get_mlflow_tracker(experiment_name="nba/random_forest")
tracker_xgb = get_mlflow_tracker(experiment_name="nba/xgboost")
tracker_nn = get_mlflow_tracker(experiment_name="nba/neural_network")
```

### 5. Clean Up Old Experiments

```python
# Delete failed/test runs periodically
# (Use MLflow UI or API)
```

---

## Troubleshooting

### Connection Errors

```python
# Error: Cannot connect to MLflow server
# Solution 1: Check server is running
$ curl http://mlflow-server:5000/health
# Should return: OK

# Solution 2: Use mock mode for development
tracker = get_mlflow_tracker(mock_mode=True)

# Solution 3: Check firewall/network
$ telnet mlflow-server 5000
```

### Permission Errors

```bash
# Error: Permission denied when writing artifacts
# Solution: Check file permissions
chmod -R 755 mlflow-artifacts/

# Error: S3 access denied
# Solution: Verify AWS credentials
aws s3 ls s3://mlflow-artifacts
```

### Slow Artifact Uploads

```python
# Problem: Large artifacts slow down tracking
# Solution 1: Compress before uploading
import gzip
with gzip.open('model.pkl.gz', 'wb') as f:
    pickle.dump(model, f)
tracker.log_artifact('model.pkl.gz')

# Solution 2: Log only essential artifacts
# Don't log: raw data, temporary files, debug outputs
# Do log: final model, evaluation plots, configs
```

### Database Connection Pool Exhausted

```bash
# Error: Too many database connections
# Solution: Increase pool size in server config
mlflow server \
    --backend-store-uri postgresql://... \
    --default-artifact-root ... \
    --host 0.0.0.0 \
    --port 5000 \
    --gunicorn-opts "--timeout 60 --workers 4"
```

---

## Production Deployment Checklist

### Infrastructure

- [ ] MLflow server deployed with high availability
- [ ] Database backend configured (PostgreSQL/MySQL)
- [ ] Cloud artifact storage configured (S3/Azure/GCS)
- [ ] Load balancer configured for MLflow server
- [ ] Monitoring and alerting setup

### Security

- [ ] Authentication enabled on MLflow server
- [ ] TLS/SSL certificates configured
- [ ] Network security groups/firewalls configured
- [ ] Secrets management for credentials
- [ ] Access control for model registry

### Operations

- [ ] Automated backups of MLflow database
- [ ] Log rotation configured
- [ ] Artifact retention policy defined
- [ ] Disaster recovery plan documented
- [ ] Team training completed

### Integration

- [ ] Environment variables configured
- [ ] CI/CD pipelines updated
- [ ] Training scripts updated to use MLflow
- [ ] Model deployment process defined
- [ ] Documentation updated

---

## Related Documentation

- [Model Training README](README.md)
- [Hyperparameter Tuning Guide](HYPERPARAMETER_TUNING.md)
- [Training Pipeline](README.md#3-complete-training-pipeline)
- [MLflow Official Docs](https://mlflow.org/docs/latest/index.html)

---

## Example: Production Configuration

```python
# production_config.py
import os
from mcp_server.mlflow_integration import get_mlflow_tracker

class MLflowConfig:
    """Production MLflow configuration"""

    # Server settings
    TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-prod:5000")
    EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "nba_production")

    # Authentication
    USERNAME = os.getenv("MLFLOW_TRACKING_USERNAME")
    PASSWORD = os.getenv("MLFLOW_TRACKING_PASSWORD")

    # Artifact storage
    ARTIFACT_LOCATION = os.getenv(
        "MLFLOW_ARTIFACT_LOCATION",
        "s3://nba-mlflow-prod/artifacts"
    )

    @classmethod
    def get_tracker(cls):
        """Get configured MLflow tracker"""
        return get_mlflow_tracker(
            experiment_name=cls.EXPERIMENT_NAME,
            tracking_uri=cls.TRACKING_URI,
            mock_mode=False
        )

# Usage
tracker = MLflowConfig.get_tracker()
```

---

**Document Status:** AGENT 5 - PHASE 4 DOCUMENTATION
**Created:** October 25, 2025
**Component:** MLflow Integration
**See Also:** [README.md](README.md) | [HYPERPARAMETER_TUNING.md](HYPERPARAMETER_TUNING.md)
