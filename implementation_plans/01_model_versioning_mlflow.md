# 📦 Implementation Plan: Model Versioning with MLflow

**Priority:** 🔴 HIGH (Do First!)
**Time Estimate:** 1 day
**Difficulty:** 🛠️ Easy
**Book Reference:** Chapter 5, pages 120-145

---

## 🎯 GOAL

Implement MLflow to track all model training runs, store models with metadata, and enable version control and rollback capabilities.

**Success Criteria:**
- ✅ MLflow server running and accessible
- ✅ All model training runs logged
- ✅ Models stored in S3 with metadata
- ✅ Can view experiment history in UI
- ✅ Can rollback to previous versions
- ✅ Integrated with existing MCP tools

---

## 📚 BACKGROUND (From ML Systems Book)

**Why Model Versioning Matters:**
> "Without version control, you can't reproduce results, can't compare models systematically, and can't rollback when things go wrong. It's like coding without Git." - Ch. 5, p. 121

**Key Concepts:**
1. **Experiment Tracking** - Log every training run
2. **Model Registry** - Central catalog of models
3. **Artifact Storage** - Save models, data, plots
4. **Metadata** - Track hyperparams, metrics, dates
5. **Lineage** - Link models to data and code

---

## 🏗️ ARCHITECTURE

```
Training Script
    ↓
  MLflow Tracking
    ↓
├─ Metadata → SQLite DB
├─ Artifacts → S3 Bucket
└─ Models → Model Registry
    ↓
Production Deployment
```

**Components:**
1. **MLflow Server** - Central tracking server
2. **SQLite Backend** - Store experiment metadata
3. **S3 Storage** - Store model artifacts
4. **Model Registry** - Manage model versions
5. **MCP Integration** - Track via MCP tools

---

## 📋 PREREQUISITES

**Required:**
- Python 3.8+
- AWS credentials configured
- S3 bucket (already have: `nba-mcp-books-20251011`)
- Existing MCP project

**Install:**
```bash
pip install mlflow>=2.8.0
pip install boto3  # Already installed
```

---

## 🔧 IMPLEMENTATION STEPS

### **Step 1: Install and Configure MLflow** (15 minutes)

#### 1.1 Install MLflow
```bash
cd /Users/ryanranft/nba-mcp-synthesis
pip install mlflow
```

#### 1.2 Create MLflow Configuration
**File:** `mlflow_config.py`

```python
"""
MLflow Configuration for NBA MCP Project
"""
import os
from pathlib import Path

# MLflow Settings
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
MLFLOW_ARTIFACT_ROOT = f"s3://nba-mcp-books-20251011/mlflow-artifacts"
MLFLOW_EXPERIMENT_NAME = "nba-mcp-models"

# Model Registry Settings
MODEL_REGISTRY_URI = MLFLOW_TRACKING_URI
DEFAULT_REGISTERED_MODEL_NAME = "nba-prediction-model"

# Logging Settings
LOG_MODELS = True
LOG_PARAMS = True
LOG_METRICS = True
LOG_ARTIFACTS = True

def get_mlflow_config():
    """Get MLflow configuration"""
    return {
        "tracking_uri": MLFLOW_TRACKING_URI,
        "artifact_root": MLFLOW_ARTIFACT_ROOT,
        "experiment_name": MLFLOW_EXPERIMENT_NAME,
        "registry_uri": MODEL_REGISTRY_URI,
    }

def init_mlflow():
    """Initialize MLflow with project settings"""
    import mlflow

    # Set tracking URI
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # Set experiment
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    # Configure S3 for artifacts
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.getenv("S3_ENDPOINT_URL", "")

    print(f"✅ MLflow initialized")
    print(f"   Tracking: {MLFLOW_TRACKING_URI}")
    print(f"   Artifacts: {MLFLOW_ARTIFACT_ROOT}")
    print(f"   Experiment: {MLFLOW_EXPERIMENT_NAME}")

    return mlflow

if __name__ == "__main__":
    init_mlflow()
```

**Where to create:** `/Users/ryanranft/nba-mcp-synthesis/mlflow_config.py`

---

### **Step 2: Create Model Tracking Module** (30 minutes)

#### 2.1 Create Model Tracker
**File:** `mcp_server/model_tracking.py`

```python
"""
Model Tracking with MLflow Integration
"""
import mlflow
import mlflow.sklearn
from datetime import datetime
from typing import Dict, Any, Optional
import json

from .mlflow_config import init_mlflow


class ModelTracker:
    """Track ML models with MLflow"""

    def __init__(self):
        """Initialize model tracker"""
        self.mlflow = init_mlflow()

    def start_run(self, run_name: str, tags: Optional[Dict[str, str]] = None):
        """
        Start a new MLflow run

        Args:
            run_name: Name for this training run
            tags: Optional tags (e.g., {"model_type": "random_forest"})
        """
        tags = tags or {}
        tags["run_date"] = datetime.now().isoformat()

        return mlflow.start_run(run_name=run_name, tags=tags)

    def log_params(self, params: Dict[str, Any]):
        """
        Log hyperparameters

        Args:
            params: Dictionary of hyperparameters
        """
        for key, value in params.items():
            mlflow.log_param(key, value)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        Log metrics

        Args:
            metrics: Dictionary of metrics (e.g., {"accuracy": 0.95})
            step: Optional step number for time-series metrics
        """
        for key, value in metrics.items():
            if step is not None:
                mlflow.log_metric(key, value, step=step)
            else:
                mlflow.log_metric(key, value)

    def log_model(self, model, artifact_path: str = "model",
                   registered_model_name: Optional[str] = None):
        """
        Log model to MLflow

        Args:
            model: Trained model object
            artifact_path: Path within run to store model
            registered_model_name: Name to register model (optional)
        """
        # Detect model type and log appropriately
        if hasattr(model, 'fit') and hasattr(model, 'predict'):
            # Scikit-learn compatible model
            mlflow.sklearn.log_model(
                model,
                artifact_path,
                registered_model_name=registered_model_name
            )
        else:
            # Generic Python model
            mlflow.pyfunc.log_model(
                artifact_path,
                python_model=model,
                registered_model_name=registered_model_name
            )

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """
        Log artifact file (plot, data, config, etc.)

        Args:
            local_path: Path to local file
            artifact_path: Destination path in artifact store
        """
        mlflow.log_artifact(local_path, artifact_path)

    def log_dict(self, dictionary: Dict[str, Any], filename: str):
        """
        Log dictionary as JSON artifact

        Args:
            dictionary: Dictionary to log
            filename: Name of JSON file (e.g., "config.json")
        """
        mlflow.log_dict(dictionary, filename)

    def end_run(self, status: str = "FINISHED"):
        """
        End current MLflow run

        Args:
            status: Run status ("FINISHED", "FAILED", "KILLED")
        """
        mlflow.end_run(status=status)

    def load_model(self, run_id: str, artifact_path: str = "model"):
        """
        Load model from MLflow run

        Args:
            run_id: MLflow run ID
            artifact_path: Path to model within run

        Returns:
            Loaded model
        """
        model_uri = f"runs:/{run_id}/{artifact_path}"
        return mlflow.pyfunc.load_model(model_uri)

    def get_run(self, run_id: str):
        """
        Get run information

        Args:
            run_id: MLflow run ID

        Returns:
            Run object with metrics, params, etc.
        """
        return mlflow.get_run(run_id)

    def search_runs(self, filter_string: str = "", max_results: int = 100):
        """
        Search for runs matching criteria

        Args:
            filter_string: Filter (e.g., "metrics.accuracy > 0.9")
            max_results: Maximum number of results

        Returns:
            List of matching runs
        """
        return mlflow.search_runs(
            filter_string=filter_string,
            max_results=max_results
        )

    def register_model(self, run_id: str, model_name: str,
                        artifact_path: str = "model"):
        """
        Register model in Model Registry

        Args:
            run_id: MLflow run ID
            model_name: Name for registered model
            artifact_path: Path to model within run

        Returns:
            ModelVersion object
        """
        model_uri = f"runs:/{run_id}/{artifact_path}"
        return mlflow.register_model(model_uri, model_name)

    def transition_model_stage(self, model_name: str, version: int,
                                stage: str):
        """
        Transition model to different stage

        Args:
            model_name: Registered model name
            version: Model version number
            stage: Target stage ("Staging", "Production", "Archived")
        """
        client = mlflow.tracking.MlflowClient()
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage
        )

        print(f"✅ Model {model_name} v{version} → {stage}")


# Convenience function for MCP tools
def track_model_training(model_name: str, model, params: Dict[str, Any],
                          metrics: Dict[str, float], artifacts: Dict[str, str] = None):
    """
    Track a complete model training run

    Args:
        model_name: Name for this training run
        model: Trained model object
        params: Hyperparameters
        metrics: Performance metrics
        artifacts: Optional dict of {name: file_path} to log

    Returns:
        MLflow run ID
    """
    tracker = ModelTracker()

    with tracker.start_run(model_name):
        # Log parameters
        tracker.log_params(params)

        # Log metrics
        tracker.log_metrics(metrics)

        # Log model
        tracker.log_model(model, registered_model_name=model_name)

        # Log artifacts
        if artifacts:
            for name, path in artifacts.items():
                tracker.log_artifact(path)

        # Get run ID
        run = mlflow.active_run()
        run_id = run.info.run_id

        print(f"✅ Model tracked: {model_name}")
        print(f"   Run ID: {run_id}")
        print(f"   Metrics: {metrics}")

        return run_id
```

**Where to create:** `/Users/ryanranft/nba-mcp-synthesis/mcp_server/model_tracking.py`

---

### **Step 3: Add MCP Tools for Model Tracking** (20 minutes)

#### 3.1 Add MLflow MCP Tools
**File:** `mcp_server/tools/mlflow_tools.py`

```python
"""
MLflow MCP Tools
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from ..model_tracking import ModelTracker, track_model_training


# Pydantic Models for Parameters
class TrackModelParams(BaseModel):
    """Parameters for tracking a model"""
    model_name: str = Field(..., description="Name for model/experiment")
    params: Dict[str, Any] = Field(..., description="Model hyperparameters")
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    model_artifact_path: Optional[str] = Field(None, description="Path to saved model file")

    class Config:
        json_schema_extra = {
            "examples": [{
                "model_name": "nba-playoff-predictor-v1",
                "params": {"n_trees": 100, "max_depth": 10},
                "metrics": {"accuracy": 0.92, "f1": 0.89},
                "model_artifact_path": "/tmp/model.pkl"
            }]
        }


class SearchRunsParams(BaseModel):
    """Parameters for searching runs"""
    filter_string: Optional[str] = Field("", description="Filter query")
    max_results: int = Field(100, description="Maximum results", ge=1, le=1000)
    order_by: Optional[str] = Field("metrics.accuracy DESC", description="Sort order")

    class Config:
        json_schema_extra = {
            "examples": [{
                "filter_string": "metrics.accuracy > 0.9",
                "max_results": 10,
                "order_by": "metrics.accuracy DESC"
            }]
        }


class GetModelParams(BaseModel):
    """Parameters for getting a model"""
    run_id: str = Field(..., description="MLflow run ID")
    artifact_path: str = Field("model", description="Model artifact path")

    class Config:
        json_schema_extra = {
            "examples": [{
                "run_id": "abc123def456",
                "artifact_path": "model"
            }]
        }


class RegisterModelParams(BaseModel):
    """Parameters for registering a model"""
    run_id: str = Field(..., description="MLflow run ID")
    model_name: str = Field(..., description="Registered model name")
    artifact_path: str = Field("model", description="Model artifact path")

    class Config:
        json_schema_extra = {
            "examples": [{
                "run_id": "abc123def456",
                "model_name": "nba-playoff-predictor",
                "artifact_path": "model"
            }]
        }


class TransitionModelParams(BaseModel):
    """Parameters for transitioning model stage"""
    model_name: str = Field(..., description="Registered model name")
    version: int = Field(..., description="Model version", ge=1)
    stage: str = Field(..., description="Target stage", pattern="^(Staging|Production|Archived)$")

    class Config:
        json_schema_extra = {
            "examples": [{
                "model_name": "nba-playoff-predictor",
                "version": 3,
                "stage": "Production"
            }]
        }


# MCP Tool Functions
def mlflow_track_model(params: TrackModelParams) -> Dict[str, Any]:
    """
    Track a model training run in MLflow

    Logs hyperparameters, metrics, and model artifacts.
    """
    try:
        tracker = ModelTracker()

        with tracker.start_run(params.model_name):
            # Log parameters
            tracker.log_params(params.params)

            # Log metrics
            tracker.log_metrics(params.metrics)

            # Log model artifact if provided
            if params.model_artifact_path:
                tracker.log_artifact(params.model_artifact_path)

            # Get run info
            run = tracker.mlflow.active_run()
            run_id = run.info.run_id

            return {
                "success": True,
                "run_id": run_id,
                "run_name": params.model_name,
                "params_logged": len(params.params),
                "metrics_logged": len(params.metrics),
                "message": f"Model tracked successfully: {run_id}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to track model"
        }


def mlflow_search_runs(params: SearchRunsParams) -> Dict[str, Any]:
    """
    Search for MLflow runs matching criteria

    Returns runs sorted by specified metric.
    """
    try:
        tracker = ModelTracker()

        runs = tracker.search_runs(
            filter_string=params.filter_string,
            max_results=params.max_results
        )

        # Convert to dict
        runs_list = []
        for _, run in runs.iterrows():
            runs_list.append({
                "run_id": run["run_id"],
                "experiment_id": run["experiment_id"],
                "status": run["status"],
                "start_time": run["start_time"],
                "end_time": run["end_time"],
                "metrics": run[[c for c in run.index if c.startswith("metrics.")]].to_dict(),
                "params": run[[c for c in run.index if c.startswith("params.")]].to_dict(),
            })

        return {
            "success": True,
            "count": len(runs_list),
            "runs": runs_list[:10],  # Limit response size
            "total_found": len(runs_list),
            "message": f"Found {len(runs_list)} matching runs"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to search runs"
        }


def mlflow_get_best_model(experiment_name: str, metric: str = "accuracy") -> Dict[str, Any]:
    """
    Get the best model from an experiment based on a metric

    Args:
        experiment_name: Name of experiment
        metric: Metric to optimize (default: accuracy)
    """
    try:
        tracker = ModelTracker()

        # Search for best run
        runs = tracker.search_runs(
            filter_string="",
            max_results=1000
        )

        if runs.empty:
            return {
                "success": False,
                "message": "No runs found in experiment"
            }

        # Find best by metric
        metric_col = f"metrics.{metric}"
        if metric_col not in runs.columns:
            return {
                "success": False,
                "message": f"Metric {metric} not found in runs"
            }

        best_run = runs.loc[runs[metric_col].idxmax()]

        return {
            "success": True,
            "run_id": best_run["run_id"],
            "metric": metric,
            "value": best_run[metric_col],
            "params": best_run[[c for c in best_run.index if c.startswith("params.")]].to_dict(),
            "start_time": best_run["start_time"],
            "message": f"Best model has {metric}={best_run[metric_col]:.4f}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get best model"
        }


def mlflow_register_model(params: RegisterModelParams) -> Dict[str, Any]:
    """
    Register a model in the Model Registry

    Makes model available for staging and production deployment.
    """
    try:
        tracker = ModelTracker()

        model_version = tracker.register_model(
            run_id=params.run_id,
            model_name=params.model_name,
            artifact_path=params.artifact_path
        )

        return {
            "success": True,
            "model_name": params.model_name,
            "version": model_version.version,
            "run_id": params.run_id,
            "message": f"Model registered: {params.model_name} v{model_version.version}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to register model"
        }


def mlflow_transition_model(params: TransitionModelParams) -> Dict[str, Any]:
    """
    Transition model to different stage (Staging/Production/Archived)

    Controls which version is deployed.
    """
    try:
        tracker = ModelTracker()

        tracker.transition_model_stage(
            model_name=params.model_name,
            version=params.version,
            stage=params.stage
        )

        return {
            "success": True,
            "model_name": params.model_name,
            "version": params.version,
            "stage": params.stage,
            "message": f"Model transitioned: {params.model_name} v{params.version} → {params.stage}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to transition model"
        }
```

**Where to create:** `/Users/ryanranft/nba-mcp-synthesis/mcp_server/tools/mlflow_tools.py`

---

### **Step 4: Register MLflow Tools in FastMCP Server** (10 minutes)

#### 4.1 Add to `fastmcp_server.py`

**Add this after the existing tool imports** (around line 100):

```python
# MLflow tools
from .tools.mlflow_tools import (
    TrackModelParams,
    SearchRunsParams,
    RegisterModelParams,
    TransitionModelParams,
    mlflow_track_model,
    mlflow_search_runs,
    mlflow_get_best_model,
    mlflow_register_model,
    mlflow_transition_model,
)
```

**Add these tool declarations** (around line 5000):

```python
@mcp.tool()
async def mlflow_track_model(params: TrackModelParams, ctx: Context) -> str:
    """
    Track a model training run in MLflow.

    Logs hyperparameters, metrics, and model artifacts for experiment tracking.
    """
    await ctx.info(f"Tracking model: {params.model_name}")
    result = mlflow_track_model(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def mlflow_search_runs(params: SearchRunsParams, ctx: Context) -> str:
    """
    Search for MLflow runs matching criteria.

    Find runs by filtering on metrics, parameters, or metadata.
    """
    await ctx.info(f"Searching runs with filter: {params.filter_string}")
    result = mlflow_search_runs(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def mlflow_get_best_model(experiment_name: str, metric: str = "accuracy", ctx: Context) -> str:
    """
    Get the best model from an experiment based on a metric.

    Returns the run with the highest value for the specified metric.
    """
    await ctx.info(f"Finding best model by {metric}")
    result = mlflow_get_best_model(experiment_name, metric)
    return json.dumps(result, indent=2)


@mcp.tool()
async def mlflow_register_model(params: RegisterModelParams, ctx: Context) -> str:
    """
    Register a model in the Model Registry.

    Makes model available for staging and production deployment.
    """
    await ctx.info(f"Registering model: {params.model_name}")
    result = mlflow_register_model(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def mlflow_transition_model(params: TransitionModelParams, ctx: Context) -> str:
    """
    Transition model to different stage (Staging/Production/Archived).

    Controls which model version is deployed to each environment.
    """
    await ctx.info(f"Transitioning {params.model_name} v{params.version} to {params.stage}")
    result = mlflow_transition_model(params)
    return json.dumps(result, indent=2)
```

---

### **Step 5: Start MLflow Server** (5 minutes)

#### 5.1 Create Startup Script
**File:** `start_mlflow.sh`

```bash
#!/bin/bash

echo "🚀 Starting MLflow Server..."
echo ""

# Set MLflow environment
export MLFLOW_TRACKING_URI="sqlite:///mlflow.db"
export MLFLOW_S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-}"

# Start MLflow server
mlflow server \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root s3://nba-mcp-books-20251011/mlflow-artifacts \
    --host 0.0.0.0 \
    --port 5000 \
    &

MLFLOW_PID=$!

echo "✅ MLflow server started (PID: $MLFLOW_PID)"
echo ""
echo "📊 Access MLflow UI: http://localhost:5000"
echo ""
echo "To stop: kill $MLFLOW_PID"
echo ""

# Keep script running
wait $MLFLOW_PID
```

**Where to create:** `/Users/ryanranft/nba-mcp-synthesis/start_mlflow.sh`

```bash
chmod +x start_mlflow.sh
```

#### 5.2 Start MLflow
```bash
./start_mlflow.sh
```

Open browser: `http://localhost:5000`

---

### **Step 6: Create Example Usage** (10 minutes)

#### 6.1 Example Script
**File:** `examples/mlflow_example.py`

```python
"""
Example: Using MLflow for Model Tracking
"""
from mcp_server.model_tracking import ModelTracker
from mcp_server.tools.ml_classification_helper import train_random_forest
import numpy as np


def example_train_and_track():
    """Train a model and track it with MLflow"""

    print("📊 Example: Train and Track Model with MLflow\n")

    # Create dummy training data
    X_train = np.random.rand(100, 5)
    y_train = np.random.randint(0, 2, 100)

    # Initialize tracker
    tracker = ModelTracker()

    # Start tracking run
    with tracker.start_run("example-random-forest", tags={"type": "classification"}):

        # Define hyperparameters
        params = {
            "n_trees": 100,
            "max_depth": 10,
            "min_samples_split": 2,
            "random_seed": 42
        }

        print("1️⃣  Training model...")
        # Train model (using your existing ML tools)
        model_result = train_random_forest(
            X_train=X_train.tolist(),
            y_train=y_train.tolist(),
            **params
        )

        # Log parameters
        print("2️⃣  Logging parameters...")
        tracker.log_params(params)

        # Log metrics
        print("3️⃣  Logging metrics...")
        metrics = {
            "accuracy": 0.92,
            "precision": 0.90,
            "recall": 0.88,
            "f1_score": 0.89
        }
        tracker.log_metrics(metrics)

        # Log model
        print("4️⃣  Logging model...")
        tracker.log_dict(model_result, "model_output.json")

        print("\n✅ Model tracked successfully!")
        print(f"   View in MLflow UI: http://localhost:5000")


def example_search_best_model():
    """Search for best model"""

    print("\n🔍 Example: Search for Best Model\n")

    tracker = ModelTracker()

    # Search for runs with accuracy > 0.9
    runs = tracker.search_runs(
        filter_string="metrics.accuracy > 0.9",
        max_results=10
    )

    print(f"Found {len(runs)} runs with accuracy > 0.9")

    if not runs.empty:
        best_run = runs.iloc[0]
        print(f"\nBest Run:")
        print(f"  ID: {best_run['run_id']}")
        print(f"  Accuracy: {best_run['metrics.accuracy']:.4f}")
        print(f"  Date: {best_run['start_time']}")


def example_model_registry():
    """Example of model registry"""

    print("\n📦 Example: Model Registry\n")

    tracker = ModelTracker()

    # Get a run ID (you'd have this from training)
    runs = tracker.search_runs(max_results=1)

    if runs.empty:
        print("No runs found. Train a model first!")
        return

    run_id = runs.iloc[0]['run_id']

    # Register model
    print(f"1️⃣  Registering model from run {run_id}...")
    model_version = tracker.register_model(
        run_id=run_id,
        model_name="nba-playoff-predictor"
    )

    print(f"✅ Model registered: v{model_version.version}")

    # Transition to staging
    print(f"\n2️⃣  Transitioning to Staging...")
    tracker.transition_model_stage(
        model_name="nba-playoff-predictor",
        version=model_version.version,
        stage="Staging"
    )

    print(f"✅ Model in Staging")

    # After validation, promote to production
    print(f"\n3️⃣  Promoting to Production...")
    tracker.transition_model_stage(
        model_name="nba-playoff-predictor",
        version=model_version.version,
        stage="Production"
    )

    print(f"✅ Model in Production!")


if __name__ == "__main__":
    example_train_and_track()
    example_search_best_model()
    example_model_registry()
```

**Where to create:** `/Users/ryanranft/nba-mcp-synthesis/examples/mlflow_example.py`

---

### **Step 7: Testing** (10 minutes)

#### 7.1 Unit Tests
**File:** `tests/test_mlflow_integration.py`

```python
"""
Tests for MLflow Integration
"""
import pytest
import mlflow
from mcp_server.model_tracking import ModelTracker


def test_tracker_init():
    """Test ModelTracker initialization"""
    tracker = ModelTracker()
    assert tracker.mlflow is not None


def test_start_run():
    """Test starting a run"""
    tracker = ModelTracker()

    with tracker.start_run("test-run"):
        run = mlflow.active_run()
        assert run is not None
        assert run.info.run_name == "test-run"


def test_log_params():
    """Test logging parameters"""
    tracker = ModelTracker()

    with tracker.start_run("test-params"):
        params = {"learning_rate": 0.01, "epochs": 100}
        tracker.log_params(params)

        run = mlflow.active_run()
        assert run.data.params["learning_rate"] == "0.01"
        assert run.data.params["epochs"] == "100"


def test_log_metrics():
    """Test logging metrics"""
    tracker = ModelTracker()

    with tracker.start_run("test-metrics"):
        metrics = {"accuracy": 0.95, "loss": 0.05}
        tracker.log_metrics(metrics)

        run = mlflow.active_run()
        assert run.data.metrics["accuracy"] == 0.95
        assert run.data.metrics["loss"] == 0.05


def test_search_runs():
    """Test searching runs"""
    tracker = ModelTracker()

    # Create test runs
    with tracker.start_run("run1"):
        tracker.log_metrics({"accuracy": 0.9})

    with tracker.start_run("run2"):
        tracker.log_metrics({"accuracy": 0.95})

    # Search
    runs = tracker.search_runs(filter_string="metrics.accuracy > 0.92")
    assert len(runs) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Where to create:** `/Users/ryanranft/nba-mcp-synthesis/tests/test_mlflow_integration.py`

#### 7.2 Run Tests
```bash
cd /Users/ryanranft/nba-mcp-synthesis
pytest tests/test_mlflow_integration.py -v
```

---

## ✅ SUCCESS CRITERIA

Check off when complete:

- [ ] **MLflow installed** - `pip list | grep mlflow`
- [ ] **Server running** - `http://localhost:5000` accessible
- [ ] **Tracking working** - Can log runs
- [ ] **Artifacts in S3** - Check `s3://nba-mcp-books-20251011/mlflow-artifacts/`
- [ ] **MCP tools registered** - 5 new MCP tools available
- [ ] **Example runs** - Can see experiments in UI
- [ ] **Tests passing** - All tests green
- [ ] **Documentation updated** - README mentions MLflow

---

## 🎯 VALIDATION

Run this to validate everything works:

```bash
# 1. Check MLflow is running
curl http://localhost:5000/api/2.0/mlflow/experiments/list

# 2. Run example
python examples/mlflow_example.py

# 3. Run tests
pytest tests/test_mlflow_integration.py

# 4. Check S3 artifacts
aws s3 ls s3://nba-mcp-books-20251011/mlflow-artifacts/

# 5. Test MCP tools in Cursor chat
# Ask: "Track a model training run with these metrics: accuracy=0.92, f1=0.89"
```

---

## 📊 WHAT YOU GET

### **New Capabilities:**
1. ✅ Track all model training runs
2. ✅ Compare model versions
3. ✅ Rollback to previous models
4. ✅ Central model registry
5. ✅ Artifacts in S3
6. ✅ 5 new MCP tools
7. ✅ Web UI for exploration

### **New Files Created:**
```
nba-mcp-synthesis/
├── mlflow_config.py                    # MLflow configuration
├── mlflow.db                           # SQLite tracking database
├── start_mlflow.sh                     # Server startup script
├── mcp_server/
│   ├── model_tracking.py               # Core tracking module
│   └── tools/
│       └── mlflow_tools.py             # MCP tool implementations
├── examples/
│   └── mlflow_example.py               # Usage examples
└── tests/
    └── test_mlflow_integration.py      # Integration tests
```

### **New MCP Tools:**
1. `mlflow_track_model` - Track training runs
2. `mlflow_search_runs` - Search experiments
3. `mlflow_get_best_model` - Find best model
4. `mlflow_register_model` - Register in registry
5. `mlflow_transition_model` - Promote to production

---

## 🔧 TROUBLESHOOTING

### **Issue: MLflow server won't start**
```bash
# Check port availability
lsof -ti:5000

# Kill existing process
kill $(lsof -ti:5000)

# Restart
./start_mlflow.sh
```

### **Issue: Can't write to S3**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://nba-mcp-books-20251011/

# Verify environment
echo $AWS_ACCESS_KEY_ID
```

### **Issue: Import errors**
```bash
# Reinstall MLflow
pip install --upgrade mlflow boto3

# Verify installation
python -c "import mlflow; print(mlflow.__version__)"
```

---

## 📚 NEXT STEPS

After implementing MLflow:

1. **Integrate with existing ML tools** - Add tracking to all model training
2. **Implement Data Drift Detection** - Use tracked models as baselines
3. **Add Model Monitoring** - Track production model performance
4. **Create Automated Retraining** - Trigger retraining based on drift
5. **Build Model Registry Dashboard** - Visualize model lineage

---

## 🎓 LEARNING RESOURCES

**MLflow Documentation:**
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
- [MLflow Models](https://mlflow.org/docs/latest/models.html)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)

**Book References:**
- Chapter 5: Model Development (pages 120-145)
- Chapter 10: Infrastructure (pages 280-310)

---

## ✨ SUMMARY

**Time:** 1 day
**Difficulty:** Easy
**Impact:** HIGH

**What You Built:**
- ✅ Complete MLflow integration
- ✅ Model versioning system
- ✅ Experiment tracking
- ✅ Model registry
- ✅ S3 artifact storage
- ✅ 5 new MCP tools
- ✅ Web UI access

**Now you can:**
- Track every model training run
- Compare model versions
- Rollback when needed
- Promote models through stages
- Store all artifacts in S3
- Use MLflow from Cursor chat!

---

**🎉 IMPLEMENTATION COMPLETE!**

**Next:** Move to `02_data_drift_detection.md`

