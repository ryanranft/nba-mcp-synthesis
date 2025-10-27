# NBA MCP Model Training & Experimentation

**Phase 10A Week 2 - Agent 5: Model Training & Experimentation**

Complete machine learning training infrastructure with MLflow experiment tracking, advanced hyperparameter optimization, and comprehensive pipeline orchestration.

---

## Overview

This system provides production-ready ML training infrastructure for the NBA MCP Synthesis project. It integrates MLflow for experiment tracking, supports advanced hyperparameter optimization (including Bayesian optimization), and provides a complete training pipeline with automated monitoring and error handling.

### Key Components

1. **MLflow Integration** (`mcp_server/mlflow_integration.py`)
   - Experiment tracking and run management
   - Model versioning and registry
   - Artifact storage and retrieval
   - Run comparison and analysis
   - Mock mode for testing without MLflow server

2. **Hyperparameter Tuning** (`mcp_server/hyperparameter_tuning.py`)
   - Grid search with cross-validation
   - Random search with cross-validation
   - Bayesian optimization with Gaussian Processes
   - Early stopping support
   - MLflow logging throughout

3. **Training Pipeline** (`mcp_server/training_pipeline.py`)
   - Multi-stage orchestration (validation → training → evaluation → deployment)
   - Automatic MLflow tracking
   - Week 1 integration (error handling, monitoring, RBAC)
   - Run history and comparison
   - Graceful error recovery

---

## Quick Start

### 1. MLflow Experiment Tracking

```python
from mcp_server.mlflow_integration import get_mlflow_tracker

# Create tracker (mock mode for testing)
tracker = get_mlflow_tracker(
    experiment_name="nba_model_training",
    mock_mode=True  # Set to False for production
)

# Track experiment
with tracker.start_run("baseline_model") as run_id:
    # Log hyperparameters
    tracker.log_params({
        "n_estimators": 100,
        "max_depth": 10,
        "learning_rate": 0.01
    })

    # Train your model
    model = train_model(params)

    # Log metrics
    tracker.log_metric("accuracy", 0.92)
    tracker.log_metric("f1_score", 0.89)
    tracker.log_metric("roc_auc", 0.94)

    # Log artifacts (model, plots, etc.)
    tracker.log_artifact("model.pkl")
    tracker.log_artifact("confusion_matrix.png")

print(f"Run ID: {run_id}")
```

### 2. Hyperparameter Tuning

```python
from mcp_server.hyperparameter_tuning import HyperparameterTuner

# Initialize tuner with MLflow
tuner = HyperparameterTuner(
    mlflow_tracker=tracker,
    enable_mlflow=True,
    enable_early_stopping=True,
    early_stopping_patience=5
)

# Define training and evaluation functions
def train_fn(params):
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    return model

def eval_fn(model):
    y_pred = model.predict(X_test)
    return accuracy_score(y_test, y_pred)

# Grid search with cross-validation
best_params = tuner.grid_search(
    param_grid={
        "n_estimators": [50, 100, 200],
        "max_depth": [5, 10, 15],
        "min_samples_split": [2, 5, 10]
    },
    train_fn=train_fn,
    eval_fn=eval_fn,
    maximize=True,
    cv_folds=5  # 5-fold cross-validation
)

print(f"Best params: {best_params['params']}")
print(f"Best score: {best_params['score']}")

# Get tuning summary
summary = tuner.get_tuning_summary()
print(f"Total trials: {summary['total_trials']}")
print(f"Best score: {summary['best_score']}")
print(f"Mean score: {summary['mean_score']:.4f}")
```

### 3. Complete Training Pipeline

```python
from mcp_server.training_pipeline import TrainingPipeline, PipelineStage
import pandas as pd

# Create pipeline with MLflow
pipeline = TrainingPipeline(
    name="nba_player_performance",
    config={
        "test_size": 0.2,
        "algorithm": "random_forest",
        "n_estimators": 100
    },
    mlflow_tracker=tracker,
    enable_mlflow=True
)

# Define stage functions
def validate_data(config, data):
    """Validate data quality"""
    from mcp_server.data_validation_pipeline import DataValidationPipeline
    validator = DataValidationPipeline()
    result = validator.validate(data, 'player_stats')
    if not result.passed:
        raise ValueError(f"Validation failed: {result.issues}")
    return {"validation_passed": True}

def prepare_data(config, data):
    """Prepare data for training"""
    X = data.drop(columns=['target'])
    y = data['target']
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config['test_size'], random_state=42
    )
    return {
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test
    }

def train_model(config, prepared_data):
    """Train the model"""
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(
        n_estimators=config['n_estimators'],
        random_state=42
    )
    model.fit(prepared_data['X_train'], prepared_data['y_train'])
    return {"model": model}

def evaluate_model(config, trained_model, prepared_data):
    """Evaluate model performance"""
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    model = trained_model['model']
    y_pred = model.predict(prepared_data['X_test'])
    y_proba = model.predict_proba(prepared_data['X_test'])[:, 1]

    return {
        "accuracy": accuracy_score(prepared_data['y_test'], y_pred),
        "f1_score": f1_score(prepared_data['y_test'], y_pred),
        "roc_auc": roc_auc_score(prepared_data['y_test'], y_proba)
    }

# Add stages to pipeline
pipeline.add_stage(PipelineStage.DATA_VALIDATION, validate_data)
pipeline.add_stage(PipelineStage.DATA_PREPARATION, prepare_data)
pipeline.add_stage(PipelineStage.MODEL_TRAINING, train_model)
pipeline.add_stage(PipelineStage.MODEL_EVALUATION, evaluate_model)

# Load your data
player_data = pd.read_csv('player_stats.csv')

# Execute pipeline
run = pipeline.execute(data=player_data)

print(f"Pipeline run: {run.run_id}")
print(f"Status: {run.status}")
print(f"Duration: {run.end_time - run.start_time:.2f}s")
print(f"Metrics: {run.metrics}")

# Get run history
history = pipeline.get_run_history(limit=10)
for past_run in history:
    print(f"Run {past_run.run_id}: {past_run.metrics.get('accuracy', 'N/A')}")

# Compare runs
comparison = pipeline.compare_runs([run.run_id, history[0].run_id])
print(f"Comparison: {comparison}")
```

---

## Production Setup

### MLflow Server Setup

For production use, you'll need to set up an MLflow tracking server:

```bash
# Install MLflow
pip install mlflow

# Start MLflow server
mlflow server \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlflow-artifacts \
    --host 0.0.0.0 \
    --port 5000
```

Then configure the tracker:

```python
tracker = get_mlflow_tracker(
    experiment_name="nba_production",
    tracking_uri="http://localhost:5000",
    mock_mode=False
)
```

See [MLFLOW_GUIDE.md](MLFLOW_GUIDE.md) for detailed setup instructions.

### Environment Variables

Set these environment variables for production:

```bash
# MLflow
export MLFLOW_TRACKING_URI="http://mlflow-server:5000"
export MLFLOW_EXPERIMENT_NAME="nba_production"

# Authentication (if using MLflow with auth)
export MLFLOW_TRACKING_USERNAME="your_username"
export MLFLOW_TRACKING_PASSWORD="your_password"
```

---

## Advanced Usage

### Bayesian Optimization

For efficient hyperparameter search, use Bayesian optimization:

```python
# Note: Requires scikit-optimize
# pip install scikit-optimize

best_params = tuner.bayesian_optimization(
    param_space={
        "learning_rate": (0.0001, 0.1, "log-uniform"),
        "max_depth": (3, 15),
        "n_estimators": (50, 500)
    },
    train_fn=train_fn,
    eval_fn=eval_fn,
    n_calls=50,  # Number of iterations
    random_state=42,
    cv_folds=5
)
```

See [HYPERPARAMETER_TUNING.md](HYPERPARAMETER_TUNING.md) for detailed tuning strategies.

### Cross-Validation

All tuning methods support k-fold cross-validation:

```python
best_params = tuner.random_search(
    param_distributions={
        "n_estimators": [50, 100, 200, 500],
        "max_depth": [5, 10, 15, 20],
        "learning_rate": [0.01, 0.05, 0.1, 0.2]
    },
    n_iter=20,
    train_fn=train_fn,
    eval_fn=eval_fn,
    cv_folds=5,  # 5-fold CV
    maximize=True
)
```

### Early Stopping

Save computation time with early stopping:

```python
tuner = HyperparameterTuner(
    mlflow_tracker=tracker,
    enable_early_stopping=True,
    early_stopping_patience=10  # Stop after 10 iterations without improvement
)
```

---

## Integration with Week 1 Components

All training modules integrate seamlessly with Week 1 infrastructure:

### Error Handling

```python
from mcp_server.error_handling import handle_errors

@handle_errors(reraise=True, notify=True)
def train_with_error_handling(data):
    pipeline = TrainingPipeline(name="safe_training")
    return pipeline.execute(data=data)
```

### Monitoring

```python
from mcp_server.monitoring import track_metric

with track_metric("training.pipeline.execution"):
    result = pipeline.execute(data=data)
```

### RBAC Permissions

```python
from mcp_server.rbac import require_permission, Permission

@require_permission(Permission.WRITE)
def train_model_with_auth(data):
    pipeline = TrainingPipeline(name="authorized_training")
    return pipeline.execute(data=data)
```

---

## Testing

### Running Tests

```bash
# Run all model training tests
pytest tests/test_mlflow_integration.py \
       tests/test_hyperparameter_tuning.py \
       tests/test_training_pipeline.py -v

# Run with coverage
pytest tests/test_mlflow_integration.py \
       tests/test_hyperparameter_tuning.py \
       tests/test_training_pipeline.py \
       --cov=mcp_server --cov-report=html
```

### Mock Mode

All tests use mock mode for MLflow (no server required):

```python
# In tests
tracker = get_mlflow_tracker(
    experiment_name="test_experiment",
    mock_mode=True  # No MLflow server needed
)
```

---

## Best Practices

### 1. Always Use MLflow Tracking

Track all experiments for reproducibility:

```python
# Good
with tracker.start_run("experiment_name") as run_id:
    tracker.log_params(params)
    model = train_model(params)
    tracker.log_metrics(metrics)

# Bad - no tracking
model = train_model(params)  # Lost experiment data
```

### 2. Use Cross-Validation

Always validate with CV for robust results:

```python
# Good
best = tuner.grid_search(..., cv_folds=5)

# Bad - no cross-validation
best = tuner.grid_search(...)  # May overfit
```

### 3. Enable Early Stopping

Save computation on long searches:

```python
# Good
tuner = HyperparameterTuner(
    enable_early_stopping=True,
    early_stopping_patience=10
)

# Less efficient
tuner = HyperparameterTuner()  # Runs all trials
```

### 4. Validate Data First

Always validate before training:

```python
# Good
pipeline.add_stage(PipelineStage.DATA_VALIDATION, validate_fn)
pipeline.add_stage(PipelineStage.MODEL_TRAINING, train_fn)

# Bad - no validation
pipeline.add_stage(PipelineStage.MODEL_TRAINING, train_fn)  # May train on bad data
```

### 5. Compare Multiple Runs

Track progress over time:

```python
# Get run history
history = pipeline.get_run_history(limit=10)

# Compare runs
comparison = pipeline.compare_runs([run1_id, run2_id])
print(f"Accuracy improvement: {comparison['metrics']['accuracy']['diff']}")
```

---

## Architecture

### Component Interaction

```
┌─────────────────────────────────────────────────────┐
│                  Training Pipeline                   │
│  (Orchestrates entire training workflow)             │
└───────────────┬─────────────────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
┌───────▼──────┐  ┌────▼─────────────────┐
│   MLflow     │  │  Hyperparameter      │
│  Integration │  │     Tuning           │
│              │  │                      │
│ - Tracking   │  │ - Grid Search        │
│ - Versioning │  │ - Random Search      │
│ - Artifacts  │  │ - Bayesian Opt       │
└──────────────┘  └──────────────────────┘
        │
        │
┌───────▼──────────────────────────────┐
│      Week 1 Infrastructure            │
│                                       │
│ - Error Handling                      │
│ - Monitoring & Metrics                │
│ - RBAC & Permissions                  │
│ - Logging & Alerting                  │
└───────────────────────────────────────┘
```

---

## Troubleshooting

### MLflow Connection Issues

If you get connection errors:

```python
# Use mock mode for local development/testing
tracker = get_mlflow_tracker(mock_mode=True)

# Or verify tracking URI
import mlflow
print(mlflow.get_tracking_uri())
```

### Bayesian Optimization Not Available

Install scikit-optimize:

```bash
pip install scikit-optimize
```

Or use Grid/Random search instead:

```python
# Falls back automatically if scikit-optimize not available
best = tuner.random_search(...)  # Always available
```

### Memory Issues with Large Parameter Grids

Use random search or Bayesian optimization instead:

```python
# Instead of grid search with 1000s of combinations
best = tuner.random_search(
    param_distributions=large_param_space,
    n_iter=50  # Only try 50 random combinations
)
```

---

## Related Documentation

- [Hyperparameter Tuning Guide](HYPERPARAMETER_TUNING.md)
- [MLflow Setup Guide](MLFLOW_GUIDE.md)
- [Data Validation](../data_validation/README.md) (Agent 4)
- [Error Handling](../ERROR_HANDLING.md) (Week 1)
- [Monitoring](../MONITORING.md) (Week 1)

---

## API Reference

### MLflowExperimentTracker

See `mcp_server/mlflow_integration.py` for complete API:

- `start_run(run_name, tags)` - Start tracking run
- `end_run(status)` - End current run
- `log_param(key, value)` - Log parameter
- `log_params(params)` - Log multiple parameters
- `log_metric(key, value, step)` - Log metric
- `log_metrics(metrics, step)` - Log multiple metrics
- `log_artifact(file_path, artifact_path)` - Log artifact
- `get_run(run_id)` - Get run by ID
- `search_runs(filter_string, max_results)` - Search runs
- `compare_runs(run_ids)` - Compare multiple runs

### HyperparameterTuner

See `mcp_server/hyperparameter_tuning.py` for complete API:

- `grid_search(param_grid, train_fn, eval_fn, ...)` - Grid search
- `random_search(param_distributions, n_iter, ...)` - Random search
- `bayesian_optimization(param_space, n_calls, ...)` - Bayesian optimization
- `get_tuning_summary()` - Get tuning summary
- `get_top_results(n)` - Get top N results

### TrainingPipeline

See `mcp_server/training_pipeline.py` for complete API:

- `add_stage(stage, func)` - Add pipeline stage
- `execute(data)` - Execute pipeline
- `get_run_history(limit)` - Get run history
- `compare_runs(run_ids)` - Compare runs
- `get_current_config()` - Get current config

---

**Document Status:** AGENT 5 - PHASE 4 DOCUMENTATION
**Created:** October 25, 2025
**Component:** Model Training & Experimentation
**See Also:** [HYPERPARAMETER_TUNING.md](HYPERPARAMETER_TUNING.md) | [MLFLOW_GUIDE.md](MLFLOW_GUIDE.md)
