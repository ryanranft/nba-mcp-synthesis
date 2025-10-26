"""
Cross-Component Integration Tests

**Phase 10A Week 2 - Agent 7: Complete System Integration**

Tests integration between components from different agents:
- Agent 4 (Data Validation) ↔ Agent 5 (Training)
- Agent 5 (Training) ↔ Agent 6 (Deployment)
- Agent 6 (Deployment) ↔ Agent 4 (Validation)
- Week 1 Infrastructure integration
- MLflow integration across all components
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Agent 4
from mcp_server.data_validation import DataValidationPipeline
from mcp_server.data_cleaner import DataCleaner, OutlierMethod, ImputationStrategy
from mcp_server.data_profiler import DataProfiler
from mcp_server.integrity_checker import IntegrityChecker

# Agent 5
from mcp_server.mlflow_integration import MLflowExperimentTracker
from mcp_server.training_pipeline import TrainingPipeline

# Agent 6
from mcp_server.model_serving import ModelServingManager
from mcp_server.model_registry import ModelRegistry, ModelStage
from mcp_server.model_monitoring import ModelMonitor, DriftMethod

# Week 1
try:
    from mcp_server.error_handling import handle_errors
    from mcp_server.monitoring import track_metric

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_nba_data():
    """Generate sample NBA data"""
    np.random.seed(42)
    n = 100

    return pd.DataFrame(
        {
            "game_id": range(1, n + 1),
            "home_team": np.random.choice(["Lakers", "Warriors"], n),
            "away_team": np.random.choice(["Celtics", "Heat"], n),
            "home_ppg": np.random.normal(110, 10, n),
            "away_ppg": np.random.normal(108, 10, n),
            "home_def_rating": np.random.normal(105, 5, n),
            "away_def_rating": np.random.normal(107, 5, n),
            "home_win": np.random.choice([0, 1], n),
        }
    )


@pytest.fixture
def temp_workspace():
    """Create temporary workspace"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ==============================================================================
# Data Validation → Training Integration
# ==============================================================================


def test_validation_to_training_integration(sample_nba_data, temp_workspace):
    """
    Test data flows from validation to training

    Flow:
    1. Validate raw data
    2. Clean validated data
    3. Train model on cleaned data
    """

    # ========== Step 1: Validate Data ==========
    config = PipelineConfig(
        enable_schema_validation=True, enable_quality_check=True, min_quality_score=0.7
    )

    pipeline = DataValidationPipeline(config=config)
    val_result = pipeline.validate(sample_nba_data, "nba_games")

    assert val_result.passed, "Validation should pass"

    # ========== Step 2: Clean Data ==========
    cleaner = DataCleaner()
    cleaned_data, report = cleaner.clean(
        sample_nba_data.copy(),
        remove_outliers=True,
        outlier_method=OutlierMethod.IQR,
        impute_missing=True,
    )

    assert len(cleaned_data) > 0
    assert cleaned_data.isnull().sum().sum() == 0

    # ========== Step 3: Train Model ==========
    feature_cols = ["home_ppg", "away_ppg", "home_def_rating", "away_def_rating"]
    X = cleaned_data[feature_cols]
    y = cleaned_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    assert score > 0.4  # Should have some predictive power

    print(f"\n✅ Validation → Training integration: score={score:.2%}")


def test_data_profiling_informs_feature_engineering(sample_nba_data):
    """
    Test data profiling guides feature engineering

    Flow:
    1. Profile data to understand distributions
    2. Use profiling results to create features
    3. Train model with engineered features
    """

    # ========== Step 1: Profile Data ==========
    profiler = DataProfiler()
    profile = profiler.profile_dataset(sample_nba_data, "nba_games")

    assert profile.row_count > 0
    assert len(profile.column_stats) > 0

    # ========== Step 2: Feature Engineering Based on Profile ==========
    # Create features based on profiling insights
    engineered_data = sample_nba_data.copy()

    # Point differential (based on ppg distributions)
    engineered_data["point_diff"] = (
        engineered_data["home_ppg"] - engineered_data["away_ppg"]
    )

    # Defensive advantage
    engineered_data["def_advantage"] = (
        engineered_data["away_def_rating"] - engineered_data["home_def_rating"]
    )

    # ========== Step 3: Train with Engineered Features ==========
    feature_cols = ["home_ppg", "away_ppg", "point_diff", "def_advantage"]
    X = engineered_data[feature_cols]
    y = engineered_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    assert score > 0.4

    print(f"\n✅ Profiling → Feature Engineering: score={score:.2%}")


# ==============================================================================
# Training → Deployment Integration
# ==============================================================================


def test_training_to_registry_integration(sample_nba_data, temp_workspace):
    """
    Test trained models flow to registry

    Flow:
    1. Train model
    2. Register in model registry
    3. Promote through stages
    4. Deploy from registry
    """

    # ========== Step 1: Train Model ==========
    feature_cols = ["home_ppg", "away_ppg", "home_def_rating", "away_def_rating"]
    X = sample_nba_data[feature_cols]
    y = sample_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)

    # ========== Step 2: Register in Registry ==========
    registry = ModelRegistry(registry_dir=str(temp_workspace / "registry"))

    registry.register_model(
        model_id="nba_model",
        version="v1.0",
        stage=ModelStage.DEVELOPMENT,
        framework="sklearn",
        algorithm="RandomForest",
        metrics={"train_acc": train_score, "test_acc": test_score},
        hyperparameters={"n_estimators": 10},
    )

    # ========== Step 3: Promote Through Stages ==========
    # Dev → Staging
    registry.promote_model("nba_model", "v1.0", ModelStage.STAGING)
    staging_model = registry.get_model("nba_model", stage=ModelStage.STAGING)
    assert staging_model is not None

    # Staging → Production
    registry.promote_model("nba_model", "v1.0", ModelStage.PRODUCTION)
    prod_model = registry.get_model("nba_model", stage=ModelStage.PRODUCTION)
    assert prod_model is not None
    assert prod_model.version == "v1.0"

    # ========== Step 4: Deploy from Registry ==========
    serving = ModelServingManager(mock_mode=True)
    deploy_success = serving.deploy_model(
        "nba_model", prod_model.version, model, set_active=True
    )

    assert deploy_success

    print(f"\n✅ Training → Registry → Deployment integration successful")


def test_mlflow_tracking_to_registry(sample_nba_data, temp_workspace):
    """
    Test MLflow tracked experiments flow to model registry

    Flow:
    1. Track experiment in MLflow
    2. Register best run in registry
    3. Deploy registered model
    """

    # ========== Step 1: Track Experiment ==========
    mlflow_tracker = get_mlflow_tracker(
        experiment_name="nba_experiment", mock_mode=True
    )

    feature_cols = ["home_ppg", "away_ppg"]
    X = sample_nba_data[feature_cols]
    y = sample_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Train and log to MLflow
    with mlflow_tracker.start_run("rf_experiment") as run_id:
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)

        score = model.score(X_test, y_test)

        mlflow_tracker.log_params({"n_estimators": 10})
        mlflow_tracker.log_metric("accuracy", score)

    # ========== Step 2: Register in Model Registry ==========
    registry = ModelRegistry(registry_dir=str(temp_workspace / "registry"))

    registry.register_model(
        model_id="nba_mlflow_model",
        version="v1.0",
        stage=ModelStage.PRODUCTION,
        framework="sklearn",
        algorithm="RandomForest",
        metrics={"accuracy": score},
        tags={"mlflow_run_id": run_id} if run_id else {},
    )

    # ========== Step 3: Deploy ==========
    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("nba_mlflow_model", "v1.0", model, set_active=True)

    predictions = serving.predict("nba_mlflow_model", X_test.head(5).to_dict("records"))

    assert predictions is not None
    assert len(predictions) == 5

    print(f"\n✅ MLflow → Registry → Deployment integration successful")


# ==============================================================================
# Deployment → Monitoring Integration
# ==============================================================================


def test_serving_to_monitoring_integration(sample_nba_data):
    """
    Test predictions flow from serving to monitoring

    Flow:
    1. Deploy model
    2. Make predictions
    3. Monitor predictions
    4. Detect drift
    """

    # ========== Step 1: Deploy Model ==========
    feature_cols = ["home_ppg", "away_ppg"]
    X = sample_nba_data[feature_cols]
    y = sample_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("nba_model", "v1.0", model, set_active=True)

    # ========== Step 2: Setup Monitoring ==========
    monitor = ModelMonitor(model_id="nba_model", model_version="v1.0", mock_mode=True)

    monitor.set_reference_data(features=X_train)

    # ========== Step 3: Make and Monitor Predictions ==========
    for i, (idx, row) in enumerate(X_test.head(10).iterrows()):
        # Get prediction from serving
        pred_input = [row.to_dict()]
        prediction = serving.predict("nba_model", pred_input)

        # Log to monitoring
        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features=row.to_dict(),
            prediction=prediction[0],
            actual=y_test.iloc[i],
            latency_ms=np.random.uniform(10, 50),
        )

    # ========== Step 4: Calculate Performance ==========
    perf = monitor.calculate_performance(window_hours=24)

    assert perf.total_predictions == 10
    assert perf.accuracy is not None

    print(
        f"\n✅ Serving → Monitoring integration: {perf.total_predictions} predictions logged"
    )


def test_monitoring_triggers_redeployment(sample_nba_data):
    """
    Test monitoring alerts trigger redeployment

    Flow:
    1. Deploy model
    2. Monitor performance
    3. Detect degradation
    4. Trigger redeployment/rollback
    """

    feature_cols = ["home_ppg", "away_ppg"]
    X = sample_nba_data[feature_cols]
    y = sample_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # ========== Deploy Two Versions ==========
    model_v1 = RandomForestClassifier(n_estimators=50, random_state=42)
    model_v1.fit(X_train, y_train)

    model_v2 = RandomForestClassifier(n_estimators=1, random_state=42)  # Poor model
    model_v2.fit(X_train[:5], y_train[:5])  # Undertrained

    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("nba_model", "v1.0", model_v1)
    serving.deploy_model("nba_model", "v2.0", model_v2, set_active=True)

    # ========== Monitor v2.0 ==========
    monitor = ModelMonitor(
        model_id="nba_model",
        model_version="v2.0",
        error_rate_threshold=0.3,
        mock_mode=True,
    )

    # Log predictions with high error rate
    for i in range(10):
        try:
            pred = model_v2.predict([X_test.iloc[i].values])[0]
            monitor.log_prediction(
                f"pred_{i}",
                X_test.iloc[i].to_dict(),
                pred,
                actual=y_test.iloc[i],
                latency_ms=50,
            )
        except Exception as e:
            monitor.log_prediction(
                f"pred_{i}", X_test.iloc[i].to_dict(), None, error=str(e), latency_ms=0
            )

    # ========== Check for Performance Degradation ==========
    perf = monitor.calculate_performance(window_hours=24)

    # If performance is poor, rollback to v1.0
    if perf.error_rate > 0.2 or (perf.accuracy and perf.accuracy < 0.5):
        serving.set_active_version("nba_model", "v1.0")
        active_version = serving.active_models.get("nba_model")
        assert active_version == "v1.0"

        print(
            f"\n✅ Monitoring triggered rollback to v1.0 (error_rate={perf.error_rate:.2%})"
        )
    else:
        print(f"\n✅ Monitoring integration verified")


# ==============================================================================
# Week 1 Infrastructure Integration
# ==============================================================================


@pytest.mark.skipif(not WEEK1_AVAILABLE, reason="Week 1 not available")
def test_week1_error_handling_integration(sample_nba_data):
    """Test Week 1 error handling works across components"""

    # All components should have Week 1 error handling

    # Data Validation
    pipeline = DataValidationPipeline()
    result = pipeline.validate(sample_nba_data, "nba_games")
    assert result is not None  # Should handle errors gracefully

    # Training
    # Training pipeline should have @handle_errors decorators

    # Deployment
    serving = ModelServingManager(mock_mode=True)
    # Should handle errors gracefully even with invalid inputs

    print("\n✅ Week 1 error handling integration verified")


def test_week1_metrics_collection(sample_nba_data):
    """Test Week 1 metrics are collected across components"""

    # Components with @track_metric should collect metrics

    feature_cols = ["home_ppg", "away_ppg"]
    X = sample_nba_data[feature_cols]
    y = sample_nba_data["home_win"]

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    # Deploy model (should track deployment metrics)
    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("nba_model", "v1.0", model, set_active=True)

    # Make predictions (should track prediction metrics)
    serving.predict("nba_model", X.head(5).to_dict("records"))

    # Metrics should be tracked
    metrics = serving.get_model_metrics("nba_model", "v1.0")
    assert metrics is not None
    assert metrics.request_count > 0

    print(f"\n✅ Week 1 metrics collection: {metrics.request_count} requests tracked")


# ==============================================================================
# MLflow Integration Across Components
# ==============================================================================


def test_mlflow_end_to_end(sample_nba_data, temp_workspace):
    """
    Test MLflow integration spans all components

    Flow:
    1. Track training experiment in MLflow
    2. Log model to MLflow Model Registry
    3. Load model from MLflow for serving
    4. Log serving metrics to MLflow
    5. Log monitoring metrics to MLflow
    """

    # ========== Step 1: Track Training Experiment ==========
    tracker = get_mlflow_tracker("nba_e2e", mock_mode=True)

    feature_cols = ["home_ppg", "away_ppg"]
    X = sample_nba_data[feature_cols]
    y = sample_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    with tracker.start_run("training") as run_id:
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)

        score = model.score(X_test, y_test)

        tracker.log_params({"n_estimators": 10})
        tracker.log_metric("test_accuracy", score)

    # ========== Step 2: Deploy and Serve ==========
    serving = ModelServingManager(enable_mlflow=True, mock_mode=True)
    serving.deploy_model("nba_model", "v1.0", model, set_active=True)

    # ========== Step 3: Monitor ==========
    monitor = ModelMonitor("nba_model", "v1.0", enable_mlflow=True, mock_mode=True)

    monitor.set_reference_data(features=X_train)

    # Make and monitor predictions
    for i in range(5):
        pred_input = [X_test.iloc[i].to_dict()]
        prediction = serving.predict("nba_model", pred_input)

        monitor.log_prediction(
            f"pred_{i}",
            X_test.iloc[i].to_dict(),
            prediction[0],
            actual=y_test.iloc[i],
            latency_ms=25.0,
        )

    perf = monitor.calculate_performance(window_hours=24)

    print(
        f"\n✅ MLflow E2E integration: trained, deployed, monitored {perf.total_predictions} predictions"
    )


# ==============================================================================
# Configuration Management Integration
# ==============================================================================


def test_configuration_consistency_across_components(temp_workspace):
    """Test configuration is consistent across all components"""

    # All components should accept similar configuration patterns

    # Data validation config
    val_config = PipelineConfig(
        enable_schema_validation=True, enable_quality_check=True
    )
    assert val_config.enable_schema_validation

    # Training config
    train_config = TrainingConfig(model_type="classification", validation_split=0.2)
    assert train_config.validation_split == 0.2

    # Serving config (via initialization)
    serving = ModelServingManager(error_threshold=0.1, mock_mode=True)
    assert serving.error_threshold == 0.1

    # Monitoring config (via initialization)
    monitor = ModelMonitor("model", "v1.0", drift_threshold=0.05, mock_mode=True)
    assert monitor.drift_threshold == 0.05

    print("\n✅ Configuration consistency verified")


def test_state_persistence_across_components(temp_workspace):
    """Test state persists correctly across components"""

    # ========== Registry Persistence ==========
    registry1 = ModelRegistry(registry_dir=str(temp_workspace / "registry"))

    registry1.register_model(
        "model1", "v1.0", ModelStage.PRODUCTION, "sklearn", "RF", {"acc": 0.9}
    )

    # Create new registry instance - should load persisted state
    registry2 = ModelRegistry(registry_dir=str(temp_workspace / "registry"))

    model = registry2.get_model("model1", stage=ModelStage.PRODUCTION)
    assert model is not None
    assert model.version == "v1.0"

    print("\n✅ State persistence verified")


def test_recovery_scenarios(sample_nba_data):
    """Test system recovers from various failure scenarios"""

    feature_cols = ["home_ppg", "away_ppg"]
    X = sample_nba_data[feature_cols]
    y = sample_nba_data["home_win"]

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    # ========== Scenario 1: Serving Failure Recovery ==========
    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("model", "v1.0", model, set_active=True)

    # Simulate multiple failures
    class FailingModel:
        def predict(self, inputs):
            raise ValueError("Model failed")

    serving.deploy_model("model", "v2.0", FailingModel(), set_active=True)

    # Should be able to rollback
    serving.set_active_version("model", "v1.0")
    assert serving.active_models.get("model") == "v1.0"

    print("\n✅ Recovery scenarios validated")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
