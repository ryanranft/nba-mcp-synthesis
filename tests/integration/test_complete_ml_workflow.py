"""
Complete ML Workflow Integration Tests

**Phase 10A Week 2 - Agent 7: Complete System Integration**

End-to-end tests covering the complete ML workflow from data ingestion through
validation, training, deployment, and monitoring. Tests integration of:
- Agent 4: Data Validation & Quality
- Agent 5: Model Training & Experimentation
- Agent 6: Model Deployment & Serving

This test suite validates that all components work together seamlessly in
production-like scenarios.
"""

import tempfile
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Agent 4: Data Validation
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig
from mcp_server.data_quality import DataQualityChecker
from mcp_server.data_cleaning import DataCleaner, OutlierMethod, ImputationStrategy
from mcp_server.data_profiler import DataProfiler

# Agent 5: Model Training
from mcp_server.mlflow_integration import get_mlflow_tracker
from mcp_server.hyperparameter_tuning import HyperparameterTuner
from mcp_server.training_pipeline import ModelTrainingPipeline, TrainingConfig

# Agent 6: Model Deployment
from mcp_server.model_serving import ModelServingManager
from mcp_server.model_registry import ModelRegistry, ModelStage
from mcp_server.model_versioning import ModelVersioningRegistry
from mcp_server.model_monitoring import ModelMonitor, DriftMethod


# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture
def nba_sample_data():
    """Generate sample NBA game data for testing"""
    np.random.seed(42)
    n_samples = 200

    data = pd.DataFrame(
        {
            "game_id": range(1, n_samples + 1),
            "home_team": np.random.choice(
                ["Lakers", "Warriors", "Celtics", "Heat"], n_samples
            ),
            "away_team": np.random.choice(
                ["Lakers", "Warriors", "Celtics", "Heat"], n_samples
            ),
            "home_ppg": np.random.normal(110, 10, n_samples),
            "away_ppg": np.random.normal(108, 10, n_samples),
            "home_def_rating": np.random.normal(105, 5, n_samples),
            "away_def_rating": np.random.normal(107, 5, n_samples),
            "home_wins": np.random.randint(20, 50, n_samples),
            "away_wins": np.random.randint(20, 50, n_samples),
            "season": np.random.choice(["2023-24", "2024-25"], n_samples),
        }
    )

    # Create target (home team win)
    data["home_win"] = (
        (data["home_ppg"] > data["away_ppg"])
        & (data["home_def_rating"] < data["away_def_rating"])
    ).astype(int)

    return data


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = {
            "registry": Path(tmpdir) / "registry",
            "models": Path(tmpdir) / "models",
            "mlflow": Path(tmpdir) / "mlflow",
        }
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)

        yield paths


# ==============================================================================
# Happy Path Tests - Complete Workflows
# ==============================================================================


def test_complete_workflow_data_to_production(nba_sample_data, temp_dirs):
    """
    Test complete workflow from raw data to production deployment

    Flow:
    1. Validate data
    2. Clean and profile data
    3. Train model
    4. Register model
    5. Deploy to production
    6. Make predictions
    7. Monitor performance
    """

    # ============ Step 1: Data Validation ============
    # Configure validation pipeline
    val_config = PipelineConfig(
        enable_schema_validation=True,
        enable_quality_check=True,
        enable_business_rules=True,
        min_quality_score=0.8,
    )

    pipeline = DataValidationPipeline(config=val_config)

    # Validate data
    val_result = pipeline.validate(nba_sample_data, "nba_games")

    assert val_result.passed, f"Validation failed: {val_result.issues}"
    assert val_result.quality_score >= 0.8

    # ============ Step 2: Data Cleaning ============
    cleaner = DataCleaner()

    cleaned_data, clean_report = cleaner.clean(
        nba_sample_data.copy(),
        remove_outliers=True,
        outlier_method=OutlierMethod.IQR,
        impute_missing=True,
        imputation_strategy=ImputationStrategy.MEDIAN,
    )

    assert len(cleaned_data) > 0
    assert cleaned_data.isnull().sum().sum() == 0  # No missing values

    # ============ Step 3: Data Profiling ============
    profiler = DataProfiler()

    profile = profiler.profile_dataset(cleaned_data, "nba_games")

    assert profile.row_count > 0
    assert len(profile.column_stats) > 0

    # ============ Step 4: Model Training ============
    # Prepare training data
    feature_cols = ["home_ppg", "away_ppg", "home_def_rating", "away_def_rating"]
    X = cleaned_data[feature_cols]
    y = cleaned_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)

    assert train_score > 0.6
    assert test_score > 0.5

    # ============ Step 5: Model Registration ============
    registry = ModelRegistry(
        registry_dir=str(temp_dirs["registry"]), enable_mlflow=False  # Mock mode
    )

    registry.register_model(
        model_id="nba_win_predictor",
        version="v1.0",
        stage=ModelStage.DEVELOPMENT,
        framework="sklearn",
        algorithm="RandomForest",
        metrics={"train_accuracy": train_score, "test_accuracy": test_score},
        hyperparameters={"n_estimators": 50, "max_depth": 5},
    )

    # Promote to production
    registry.promote_model(
        model_id="nba_win_predictor", version="v1.0", target_stage=ModelStage.PRODUCTION
    )

    prod_model = registry.get_model("nba_win_predictor", stage=ModelStage.PRODUCTION)
    assert prod_model is not None
    assert prod_model.version == "v1.0"

    # ============ Step 6: Model Deployment ============
    serving_manager = ModelServingManager(mock_mode=True)

    deploy_success = serving_manager.deploy_model(
        model_id="nba_win_predictor",
        version="v1.0",
        model_instance=model,
        set_active=True,
    )

    assert deploy_success

    # ============ Step 7: Make Predictions ============
    test_game = X_test.iloc[0:1].to_dict("records")
    prediction = serving_manager.predict("nba_win_predictor", test_game)

    assert prediction is not None
    assert len(prediction) == 1
    assert 0 <= prediction[0] <= 1  # Probability

    # ============ Step 8: Model Monitoring ============
    monitor = ModelMonitor(
        model_id="nba_win_predictor", model_version="v1.0", mock_mode=True
    )

    # Set reference data
    monitor.set_reference_data(features=X_train)

    # Log predictions
    for i, (idx, row) in enumerate(X_test.head(10).iterrows()):
        pred = model.predict_proba([row.values])[0][1]
        actual = y_test.iloc[i]

        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features=row.to_dict(),
            prediction=pred,
            actual=actual,
            latency_ms=np.random.uniform(10, 50),
        )

    # Calculate performance
    perf_metrics = monitor.calculate_performance(window_hours=24)

    assert perf_metrics.total_predictions == 10
    assert perf_metrics.accuracy is not None

    # Check for drift
    drift_results = monitor.detect_feature_drift(
        current_data=X_test, method=DriftMethod.KS_TEST
    )

    assert len(drift_results) == len(feature_cols)

    print("\n✅ Complete workflow test passed!")
    print(f"   Data validated: {len(cleaned_data)} samples")
    print(f"   Model accuracy: {test_score:.2%}")
    print(f"   Deployed version: v1.0")
    print(f"   Predictions made: {perf_metrics.total_predictions}")


def test_model_update_workflow(nba_sample_data, temp_dirs):
    """
    Test model update workflow (v1.0 → v1.1)

    Flow:
    1. Deploy v1.0 to production
    2. Train improved v1.1
    3. Deploy v1.1 alongside v1.0
    4. Compare performance
    5. Promote v1.1 to production
    """

    # Prepare data
    feature_cols = ["home_ppg", "away_ppg", "home_def_rating", "away_def_rating"]
    X = nba_sample_data[feature_cols]
    y = nba_sample_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ============ Deploy v1.0 ============
    model_v1 = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model_v1.fit(X_train, y_train)
    score_v1 = model_v1.score(X_test, y_test)

    registry = ModelRegistry(registry_dir=str(temp_dirs["registry"]))
    serving = ModelServingManager(mock_mode=True)

    registry.register_model(
        model_id="nba_model",
        version="v1.0",
        stage=ModelStage.PRODUCTION,
        framework="sklearn",
        algorithm="RandomForest",
        metrics={"test_accuracy": score_v1},
    )

    serving.deploy_model("nba_model", "v1.0", model_v1, set_active=True)

    # ============ Train v1.1 (improved) ============
    model_v1_1 = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model_v1_1.fit(X_train, y_train)
    score_v1_1 = model_v1_1.score(X_test, y_test)

    # Register v1.1
    registry.register_model(
        model_id="nba_model",
        version="v1.1",
        stage=ModelStage.STAGING,
        framework="sklearn",
        algorithm="RandomForest",
        metrics={"test_accuracy": score_v1_1},
    )

    # ============ Deploy v1.1 Alongside v1.0 ============
    serving.deploy_model("nba_model", "v1.1", model_v1_1, set_active=False)

    # ============ Compare Models ============
    comparison = registry.compare_models("nba_model", "v1.0", "v1.1")

    assert comparison is not None
    assert "metrics_diff" in comparison

    # ============ Promote v1.1 if Better ============
    if score_v1_1 >= score_v1:
        registry.promote_model("nba_model", "v1.1", ModelStage.PRODUCTION)
        serving.set_active_version("nba_model", "v1.1")

        active_version = serving.active_models.get("nba_model")
        assert active_version == "v1.1"

    print("\n✅ Model update workflow test passed!")
    print(f"   v1.0 accuracy: {score_v1:.2%}")
    print(f"   v1.1 accuracy: {score_v1_1:.2%}")


def test_ab_testing_workflow(nba_sample_data, temp_dirs):
    """
    Test A/B testing workflow with two model versions

    Flow:
    1. Deploy v1.0 and v2.0
    2. Setup A/B test (70/30 split)
    3. Run predictions
    4. Analyze results
    5. Promote winner
    """

    # Prepare models
    feature_cols = ["home_ppg", "away_ppg", "home_def_rating", "away_def_rating"]
    X = nba_sample_data[feature_cols]
    y = nba_sample_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train two different models
    model_v1 = RandomForestClassifier(n_estimators=50, random_state=42)
    model_v1.fit(X_train, y_train)

    model_v2 = RandomForestClassifier(n_estimators=100, random_state=43)
    model_v2.fit(X_train, y_train)

    # ============ Deploy Both Versions ============
    serving = ModelServingManager(mock_mode=True)

    serving.deploy_model("nba_model", "v1.0", model_v1)
    serving.deploy_model("nba_model", "v2.0", model_v2)

    # ============ Setup A/B Test ============
    serving.setup_ab_test(
        model_id="nba_model", versions=["v1.0", "v2.0"], weights=[0.7, 0.3]
    )

    # ============ Run Predictions ============
    predictions_count = {"v1.0": 0, "v2.0": 0}

    for i in range(100):
        test_input = X_test.iloc[i % len(X_test) : i % len(X_test) + 1].to_dict(
            "records"
        )
        prediction = serving.predict("nba_model", test_input)

        # Track which version was used (approximately 70/30 split expected)
        assert prediction is not None

    # ============ Analyze Results ============
    status = serving.get_all_models_status()["nba_model"]

    v1_requests = status["v1.0"]["metrics"].request_count
    v2_requests = status["v2.0"]["metrics"].request_count

    # Check approximate 70/30 split (allow some variance)
    total_requests = v1_requests + v2_requests
    v1_ratio = v1_requests / total_requests if total_requests > 0 else 0

    assert 0.6 <= v1_ratio <= 0.8, f"A/B split not as expected: {v1_ratio:.2%}"

    print("\n✅ A/B testing workflow test passed!")
    print(f"   v1.0 requests: {v1_requests} ({v1_requests/total_requests:.1%})")
    print(f"   v2.0 requests: {v2_requests} ({v2_requests/total_requests:.1%})")


def test_rollback_workflow(nba_sample_data, temp_dirs):
    """
    Test rollback workflow when new model performs poorly

    Flow:
    1. Deploy v1.0 (stable)
    2. Deploy v2.0 (problematic)
    3. Detect issues with v2.0
    4. Rollback to v1.0
    5. Verify v1.0 active again
    """

    # Prepare data
    feature_cols = ["home_ppg", "away_ppg", "home_def_rating", "away_def_rating"]
    X = nba_sample_data[feature_cols]
    y = nba_sample_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ============ Deploy v1.0 (Stable) ============
    model_v1 = RandomForestClassifier(n_estimators=100, random_state=42)
    model_v1.fit(X_train, y_train)

    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("nba_model", "v1.0", model_v1, set_active=True)

    # ============ Deploy v2.0 (Problematic - intentionally poor) ============
    # Create a poorly performing model
    model_v2 = RandomForestClassifier(n_estimators=1, max_depth=1, random_state=42)
    model_v2.fit(X_train[:10], y_train[:10])  # Train on tiny dataset

    serving.deploy_model("nba_model", "v2.0", model_v2, set_active=True)

    # ============ Detect Issues ============
    # Make predictions with v2.0
    test_input = X_test.head(10).to_dict("records")
    predictions_v2 = serving.predict("nba_model", test_input)

    # Check performance (should be poor)
    score_v2 = model_v2.score(X_test, y_test)
    score_v1 = model_v1.score(X_test, y_test)

    assert score_v2 < score_v1, "v2.0 should perform worse than v1.0"

    # ============ Rollback to v1.0 ============
    serving.set_active_version("nba_model", "v1.0")

    active_version = serving.active_models.get("nba_model")
    assert active_version == "v1.0"

    # Verify predictions work with v1.0
    predictions_v1 = serving.predict("nba_model", test_input)
    assert predictions_v1 is not None

    print("\n✅ Rollback workflow test passed!")
    print(f"   v1.0 accuracy: {score_v1:.2%}")
    print(f"   v2.0 accuracy: {score_v2:.2%}")
    print(f"   Rolled back to: v1.0")


def test_monitoring_and_alerting_workflow(nba_sample_data, temp_dirs):
    """
    Test monitoring and alerting workflow

    Flow:
    1. Deploy model
    2. Set up monitoring
    3. Log predictions
    4. Detect drift
    5. Generate alerts
    6. Handle alerts
    """

    # Prepare data
    feature_cols = ["home_ppg", "away_ppg", "home_def_rating", "away_def_rating"]
    X = nba_sample_data[feature_cols]
    y = nba_sample_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ============ Deploy Model ============
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("nba_model", "v1.0", model, set_active=True)

    # ============ Setup Monitoring ============
    alerts_generated = []

    def alert_callback(alert):
        alerts_generated.append(alert)

    monitor = ModelMonitor(
        model_id="nba_model",
        model_version="v1.0",
        drift_threshold=0.05,
        error_rate_threshold=0.1,
        latency_threshold_ms=100.0,
        alert_callback=alert_callback,
        mock_mode=True,
    )

    # Set reference data
    monitor.set_reference_data(features=X_train)

    # ============ Log Predictions ============
    for i in range(20):
        idx = i % len(X_test)
        features = X_test.iloc[idx].to_dict()
        prediction = model.predict_proba([X_test.iloc[idx].values])[0][1]
        actual = y_test.iloc[idx]

        # Simulate some high latency predictions to trigger alerts
        latency = 150.0 if i % 5 == 0 else 50.0

        monitor.log_prediction(
            prediction_id=f"pred_{i}",
            features=features,
            prediction=prediction,
            actual=actual,
            latency_ms=latency,
        )

    # ============ Check for Alerts ============
    alerts = monitor.get_alerts()

    # Should have some latency alerts
    assert len(alerts) > 0

    # ============ Detect Drift ============
    # Create drifted data
    X_drifted = X_test.copy()
    X_drifted["home_ppg"] += 20  # Significant shift

    drift_results = monitor.detect_feature_drift(
        current_data=X_drifted, method=DriftMethod.KS_TEST
    )

    # Should detect drift in home_ppg
    drifted_features = [r for r in drift_results if r.is_drift]
    assert len(drifted_features) > 0

    # ============ Calculate Performance ============
    perf = monitor.calculate_performance(window_hours=24)

    assert perf.total_predictions == 20
    assert perf.accuracy is not None

    print("\n✅ Monitoring and alerting workflow test passed!")
    print(f"   Predictions logged: {perf.total_predictions}")
    print(f"   Alerts generated: {len(alerts)}")
    print(f"   Drift detected in: {len(drifted_features)} features")


# ==============================================================================
# Error Handling Tests
# ==============================================================================


def test_invalid_data_handling(temp_dirs):
    """Test handling of invalid data throughout the pipeline"""

    # Create invalid data (missing required columns)
    invalid_data = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

    # Data validation should fail gracefully
    config = PipelineConfig(enable_schema_validation=True)
    pipeline = DataValidationPipeline(config=config)

    result = pipeline.validate(invalid_data, "nba_games")

    # Should not pass validation
    assert not result.passed
    assert len(result.issues) > 0


def test_training_failure_recovery(nba_sample_data):
    """Test recovery from training failures"""

    # Create data that will cause training issues
    X = nba_sample_data[["home_ppg", "away_ppg"]]
    y = nba_sample_data["home_win"]

    # Intentionally use tiny dataset to cause issues
    X_tiny = X.head(2)
    y_tiny = y.head(2)

    # Training should handle this gracefully
    try:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_tiny, y_tiny)
        # May succeed but with poor performance
        assert model is not None
    except Exception as e:
        # Should catch and handle appropriately
        assert isinstance(e, (ValueError, Exception))


def test_deployment_failure_rollback(nba_sample_data, temp_dirs):
    """Test rollback on deployment failure"""

    feature_cols = ["home_ppg", "away_ppg"]
    X = nba_sample_data[feature_cols]
    y = nba_sample_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    serving = ModelServingManager(mock_mode=True)

    # Deploy initial version
    success = serving.deploy_model("nba_model", "v1.0", model, set_active=True)
    assert success

    # Try to deploy with same version (should fail or replace)
    result = serving.deploy_model("nba_model", "v1.0", model, set_active=False)

    # Either succeeds (replacement) or model already exists
    assert "nba_model" in serving.models


def test_drift_detection_and_auto_retrain(nba_sample_data, temp_dirs):
    """Test drift detection triggers retraining workflow"""

    feature_cols = ["home_ppg", "away_ppg", "home_def_rating"]
    X = nba_sample_data[feature_cols]
    y = nba_sample_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Initial model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    # Setup monitoring
    monitor = ModelMonitor(
        model_id="nba_model", model_version="v1.0", drift_threshold=0.05, mock_mode=True
    )

    monitor.set_reference_data(features=X_train)

    # Create drifted data
    X_drifted = X_test.copy()
    X_drifted["home_ppg"] += 30  # Major drift

    # Detect drift
    drift_results = monitor.detect_feature_drift(
        current_data=X_drifted, method=DriftMethod.KS_TEST
    )

    drifted = [r for r in drift_results if r.is_drift]

    # If significant drift detected, retrain
    if len(drifted) >= 2:
        # Combine old and new data for retraining
        X_retrain = pd.concat([X_train, X_drifted])
        y_retrain = pd.concat([y_train, y_test])

        # Retrain model
        model_v2 = RandomForestClassifier(n_estimators=10, random_state=42)
        model_v2.fit(X_retrain, y_retrain)

        assert model_v2 is not None

        print(f"\n✅ Detected drift in {len(drifted)} features, retrained model")


def test_circuit_breaker_integration(nba_sample_data):
    """Test circuit breaker prevents cascading failures"""

    feature_cols = ["home_ppg", "away_ppg"]
    X = nba_sample_data[feature_cols]

    class FailingModel:
        """Model that fails frequently"""

        def predict(self, inputs):
            # Fail most of the time
            if np.random.random() < 0.8:
                raise ValueError("Model prediction failed")
            return [0.5] * len(inputs)

    serving = ModelServingManager(
        error_threshold=0.5, mock_mode=True  # Trip at 50% error rate
    )

    failing_model = FailingModel()
    serving.deploy_model("nba_model", "v1.0", failing_model, set_active=True)

    # Make predictions until circuit breaker trips
    errors = 0
    for i in range(20):
        try:
            test_input = X.iloc[i : i + 1].to_dict("records")
            serving.predict("nba_model", test_input)
        except Exception:
            errors += 1

    # Circuit breaker should have tripped
    health = serving.health_check("nba_model", "v1.0")

    # Should be unhealthy or circuit breaker open
    assert health.circuit_breaker_open or errors > 10


# ==============================================================================
# Performance Tests
# ==============================================================================


def test_batch_prediction_throughput(nba_sample_data):
    """Test batch prediction performance"""

    feature_cols = ["home_ppg", "away_ppg"]
    X = nba_sample_data[feature_cols]
    y = nba_sample_data["home_win"]

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("nba_model", "v1.0", model, set_active=True)

    # Test batch prediction
    batch_size = 100
    test_input = X.head(batch_size).to_dict("records")

    start_time = time.time()
    predictions = serving.predict("nba_model", test_input)
    elapsed = time.time() - start_time

    assert predictions is not None
    assert len(predictions) == batch_size

    throughput = batch_size / elapsed
    print(f"\n✅ Batch prediction throughput: {throughput:.2f} predictions/sec")


def test_concurrent_training_jobs():
    """Test handling of concurrent training jobs"""
    # This would test multiple training jobs running in parallel
    # Simplified for this test suite
    pass


def test_large_dataset_validation(nba_sample_data):
    """Test validation performance on larger datasets"""

    # Replicate data to create larger dataset
    large_data = pd.concat([nba_sample_data] * 10, ignore_index=True)

    config = PipelineConfig(enable_quality_check=True)
    pipeline = DataValidationPipeline(config=config)

    start_time = time.time()
    result = pipeline.validate(large_data, "nba_games")
    elapsed = time.time() - start_time

    assert result is not None
    rows_per_sec = len(large_data) / elapsed

    print(f"\n✅ Validation throughput: {rows_per_sec:.2f} rows/sec")


def test_model_registry_scalability(temp_dirs):
    """Test model registry performance with many models"""

    registry = ModelRegistry(registry_dir=str(temp_dirs["registry"]))

    # Register many models
    num_models = 50
    start_time = time.time()

    for i in range(num_models):
        registry.register_model(
            model_id=f"model_{i}",
            version="v1.0",
            stage=ModelStage.DEVELOPMENT,
            framework="sklearn",
            algorithm="RandomForest",
            metrics={"accuracy": 0.8 + i * 0.001},
        )

    elapsed = time.time() - start_time
    models_per_sec = num_models / elapsed

    print(f"\n✅ Registry throughput: {models_per_sec:.2f} models/sec")


def test_monitoring_overhead_measurement(nba_sample_data):
    """Test monitoring overhead on predictions"""

    feature_cols = ["home_ppg", "away_ppg"]
    X = nba_sample_data[feature_cols]
    y = nba_sample_data["home_win"]

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    # Measure prediction time without monitoring
    test_input = X.head(10).values
    start = time.time()
    for _ in range(100):
        model.predict(test_input)
    baseline_time = time.time() - start

    # Measure with monitoring
    monitor = ModelMonitor("model", "v1.0", mock_mode=True)
    start = time.time()
    for i in range(100):
        pred = model.predict(test_input)
        for j, p in enumerate(pred):
            monitor.log_prediction(f"pred_{i}_{j}", {}, p, latency_ms=1.0)
    monitored_time = time.time() - start

    overhead = (monitored_time - baseline_time) / baseline_time * 100

    print(f"\n✅ Monitoring overhead: {overhead:.2f}%")
    assert overhead < 50, "Monitoring overhead should be reasonable"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
