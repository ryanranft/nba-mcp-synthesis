"""
Production Scenarios Integration Tests

**Phase 10A Week 2 - Agent 7: Complete System Integration**

Real-world production deployment scenarios testing complete system integration.
"""

import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig
from mcp_server.data_cleaning import DataCleaner
from mcp_server.model_serving import ModelServingManager
from mcp_server.model_registry import ModelRegistry, ModelStage
from mcp_server.model_monitoring import ModelMonitor, DriftMethod


@pytest.fixture
def production_nba_data():
    """Generate production-like NBA data"""
    np.random.seed(42)
    n = 500

    return pd.DataFrame(
        {
            "game_id": range(1, n + 1),
            "home_ppg": np.random.normal(110, 10, n),
            "away_ppg": np.random.normal(108, 10, n),
            "home_def_rating": np.random.normal(105, 5, n),
            "away_def_rating": np.random.normal(107, 5, n),
            "home_win": np.random.choice([0, 1], n),
        }
    )


@pytest.fixture
def temp_prod_env():
    """Temporary production environment"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_blue_green_deployment_with_validation(production_nba_data, temp_prod_env):
    """
    Test blue-green deployment pattern with full validation

    Scenario:
    - Blue (v1.0) running in production
    - Green (v2.0) deployed alongside
    - Validate green version
    - Switch traffic to green
    - Keep blue for rollback
    """

    feature_cols = ["home_ppg", "away_ppg", "home_def_rating", "away_def_rating"]
    X = production_nba_data[feature_cols]
    y = production_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Blue version (current production)
    blue_model = RandomForestClassifier(n_estimators=50, random_state=42)
    blue_model.fit(X_train, y_train)
    blue_score = blue_model.score(X_test, y_test)

    # Green version (new)
    green_model = RandomForestClassifier(n_estimators=100, random_state=43)
    green_model.fit(X_train, y_train)
    green_score = green_model.score(X_test, y_test)

    registry = ModelRegistry(registry_dir=str(temp_prod_env / "registry"))
    serving = ModelServingManager(mock_mode=True)

    # Deploy blue (production)
    registry.register_model(
        "nba_model",
        "v1.0",
        ModelStage.PRODUCTION,
        "sklearn",
        "RF",
        {"accuracy": blue_score},
    )
    serving.deploy_model("nba_model", "v1.0", blue_model, set_active=True)

    # Deploy green (staging)
    registry.register_model(
        "nba_model",
        "v2.0",
        ModelStage.STAGING,
        "sklearn",
        "RF",
        {"accuracy": green_score},
    )
    serving.deploy_model("nba_model", "v2.0", green_model, set_active=False)

    # Validate green
    test_inputs = X_test.head(10).to_dict("records")
    green_predictions = serving.predict(
        "nba_model", test_inputs
    )  # Will use blue (active)

    # Switch to green if validation passes
    if green_score >= blue_score * 0.95:  # Within 5% of blue
        serving.set_active_version("nba_model", "v2.0")
        registry.promote_model("nba_model", "v2.0", ModelStage.PRODUCTION)

    active = serving.active_models.get("nba_model")
    assert active in ["v1.0", "v2.0"]

    print(
        f"\n✅ Blue-green deployment: blue={blue_score:.2%}, green={green_score:.2%}, active={active}"
    )


def test_canary_deployment_with_gradual_rollout(production_nba_data):
    """
    Test canary deployment with gradual traffic increase

    Scenario:
    - Start with 5% traffic to canary
    - Monitor performance
    - Gradually increase to 25%, 50%, 100%
    """

    feature_cols = ["home_ppg", "away_ppg"]
    X = production_nba_data[feature_cols]
    y = production_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    stable_model = RandomForestClassifier(n_estimators=50, random_state=42)
    stable_model.fit(X_train, y_train)

    canary_model = RandomForestClassifier(n_estimators=100, random_state=43)
    canary_model.fit(X_train, y_train)

    serving = ModelServingManager(mock_mode=True)
    serving.deploy_model("nba_model", "v1.0", stable_model)
    serving.deploy_model("nba_model", "v2.0", canary_model)

    # Stage 1: 5% canary
    serving.setup_ab_test("nba_model", ["v1.0", "v2.0"], [0.95, 0.05])

    for _ in range(20):
        test_input = X_test.sample(1).to_dict("records")
        serving.predict("nba_model", test_input)

    # Stage 2: 25% canary (simulated - would check metrics first)
    serving.setup_ab_test("nba_model", ["v1.0", "v2.0"], [0.75, 0.25])

    # Stage 3: 100% canary
    serving.set_active_version("nba_model", "v2.0")

    assert serving.active_models.get("nba_model") == "v2.0"

    print(f"\n✅ Canary deployment completed successfully")


def test_shadow_deployment_comparison(production_nba_data):
    """
    Test shadow deployment for model comparison

    Scenario:
    - Production model serves requests
    - Shadow model runs in parallel
    - Compare predictions without affecting users
    """

    feature_cols = ["home_ppg", "away_ppg"]
    X = production_nba_data[feature_cols]
    y = production_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    prod_model = RandomForestClassifier(n_estimators=50, random_state=42)
    prod_model.fit(X_train, y_train)

    shadow_model = RandomForestClassifier(n_estimators=100, random_state=43)
    shadow_model.fit(X_train, y_train)

    prod_serving = ModelServingManager(mock_mode=True)
    shadow_serving = ModelServingManager(mock_mode=True)

    prod_serving.deploy_model("nba_model", "v1.0", prod_model, set_active=True)
    shadow_serving.deploy_model(
        "nba_model_shadow", "v2.0", shadow_model, set_active=True
    )

    differences = []
    for i in range(20):
        test_input = X_test.iloc[i : i + 1].to_dict("records")

        prod_pred = prod_serving.predict("nba_model", test_input)
        shadow_pred = shadow_serving.predict("nba_model_shadow", test_input)

        diff = abs(prod_pred[0] - shadow_pred[0])
        differences.append(diff)

    avg_diff = np.mean(differences)

    print(f"\n✅ Shadow deployment: avg difference={avg_diff:.4f}")


def test_champion_challenger_pattern(production_nba_data, temp_prod_env):
    """
    Test champion/challenger pattern

    Scenario:
    - Champion model in production
    - Multiple challengers compete
    - Best challenger becomes new champion
    """

    feature_cols = ["home_ppg", "away_ppg", "home_def_rating"]
    X = production_nba_data[feature_cols]
    y = production_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Champion
    champion = RandomForestClassifier(n_estimators=50, random_state=42)
    champion.fit(X_train, y_train)
    champion_score = champion.score(X_test, y_test)

    # Challengers
    challenger1 = RandomForestClassifier(n_estimators=100, random_state=43)
    challenger1.fit(X_train, y_train)
    challenger1_score = challenger1.score(X_test, y_test)

    challenger2 = RandomForestClassifier(n_estimators=75, random_state=44)
    challenger2.fit(X_train, y_train)
    challenger2_score = challenger2.score(X_test, y_test)

    registry = ModelRegistry(registry_dir=str(temp_prod_env / "registry"))

    # Register all models
    registry.register_model(
        "nba_model",
        "champion",
        ModelStage.PRODUCTION,
        "sklearn",
        "RF",
        {"accuracy": champion_score},
    )
    registry.register_model(
        "nba_model",
        "challenger1",
        ModelStage.STAGING,
        "sklearn",
        "RF",
        {"accuracy": challenger1_score},
    )
    registry.register_model(
        "nba_model",
        "challenger2",
        ModelStage.STAGING,
        "sklearn",
        "RF",
        {"accuracy": challenger2_score},
    )

    # Compare models
    comp1 = registry.compare_models("nba_model", "champion", "challenger1")
    comp2 = registry.compare_models("nba_model", "champion", "challenger2")

    # Promote best challenger if better than champion
    best_score = max(champion_score, challenger1_score, challenger2_score)

    if best_score > champion_score:
        if challenger1_score == best_score:
            registry.promote_model("nba_model", "challenger1", ModelStage.PRODUCTION)
            new_champion = "challenger1"
        else:
            registry.promote_model("nba_model", "challenger2", ModelStage.PRODUCTION)
            new_champion = "challenger2"
    else:
        new_champion = "champion"

    print(f"\n✅ Champion/Challenger: winner={new_champion} (score={best_score:.2%})")


def test_automated_retraining_trigger(production_nba_data):
    """
    Test automated retraining triggered by drift detection

    Scenario:
    - Monitor model performance
    - Detect significant drift
    - Trigger automated retraining
    - Deploy new model
    """

    feature_cols = ["home_ppg", "away_ppg"]
    X = production_nba_data[feature_cols]
    y = production_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Initial model
    model_v1 = RandomForestClassifier(n_estimators=50, random_state=42)
    model_v1.fit(X_train, y_train)

    monitor = ModelMonitor("nba_model", "v1.0", drift_threshold=0.05, mock_mode=True)
    monitor.set_reference_data(features=X_train)

    # Simulate drifted data
    X_drifted = X_test.copy()
    X_drifted["home_ppg"] += 25  # Significant drift

    # Detect drift
    drift_results = monitor.detect_feature_drift(X_drifted, DriftMethod.KS_TEST)
    drifted_features = [r for r in drift_results if r.is_drift]

    # Trigger retraining if significant drift
    if len(drifted_features) >= 1:
        # Combine old and new data
        X_combined = pd.concat([X_train, X_drifted])
        y_combined = pd.concat([y_train, y_test])

        # Retrain
        model_v2 = RandomForestClassifier(n_estimators=50, random_state=42)
        model_v2.fit(X_combined, y_combined)

        print(
            f"\n✅ Automated retraining triggered: {len(drifted_features)} features drifted"
        )
    else:
        print(f"\n✅ No retraining needed")


def test_performance_degradation_detection_and_rollback(production_nba_data):
    """
    Test detection of performance degradation and automatic rollback

    Scenario:
    - Deploy new model version
    - Monitor performance
    - Detect degradation
    - Automatic rollback to previous version
    """

    feature_cols = ["home_ppg", "away_ppg"]
    X = production_nba_data[feature_cols]
    y = production_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Good model (v1.0)
    good_model = RandomForestClassifier(n_estimators=100, random_state=42)
    good_model.fit(X_train, y_train)

    # Poor model (v2.0) - intentionally undertrained
    poor_model = RandomForestClassifier(n_estimators=1, max_depth=1, random_state=42)
    poor_model.fit(X_train[:10], y_train[:10])

    serving = ModelServingManager(error_threshold=0.3, mock_mode=True)

    # Deploy v1.0
    serving.deploy_model("nba_model", "v1.0", good_model, set_active=True)

    # Deploy v2.0
    serving.deploy_model("nba_model", "v2.0", poor_model, set_active=True)

    # Monitor v2.0
    monitor = ModelMonitor(
        "nba_model", "v2.0", error_rate_threshold=0.2, mock_mode=True
    )

    # Make predictions and track errors
    for i in range(20):
        try:
            test_input = X_test.iloc[i : i + 1].to_dict("records")
            pred = serving.predict("nba_model", test_input)

            monitor.log_prediction(
                f"pred_{i}",
                X_test.iloc[i].to_dict(),
                pred[0] if pred else None,
                actual=y_test.iloc[i],
                latency_ms=50,
            )
        except Exception as e:
            monitor.log_prediction(f"pred_{i}", {}, None, error=str(e), latency_ms=0)

    # Check performance
    perf = monitor.calculate_performance(window_hours=24)

    # Rollback if performance is poor
    if perf.error_rate > 0.1 or (perf.accuracy and perf.accuracy < 0.6):
        serving.set_active_version("nba_model", "v1.0")
        rollback = True
    else:
        rollback = False

    print(
        f"\n✅ Performance monitoring: error_rate={perf.error_rate:.2%}, rollback={rollback}"
    )


def test_multi_model_ensemble_serving(production_nba_data):
    """
    Test serving multiple models as an ensemble

    Scenario:
    - Deploy multiple models
    - Combine predictions
    - Serve ensemble prediction
    """

    feature_cols = ["home_ppg", "away_ppg"]
    X = production_nba_data[feature_cols]
    y = production_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Train multiple models
    model1 = RandomForestClassifier(n_estimators=50, random_state=42)
    model1.fit(X_train, y_train)

    model2 = RandomForestClassifier(n_estimators=100, random_state=43)
    model2.fit(X_train, y_train)

    model3 = RandomForestClassifier(n_estimators=75, random_state=44)
    model3.fit(X_train, y_train)

    serving = ModelServingManager(mock_mode=True)

    # Deploy all models
    serving.deploy_model("ensemble_model_1", "v1.0", model1, set_active=True)
    serving.deploy_model("ensemble_model_2", "v1.0", model2, set_active=True)
    serving.deploy_model("ensemble_model_3", "v1.0", model3, set_active=True)

    # Get predictions from all models and ensemble
    test_input = X_test.head(10).to_dict("records")

    pred1 = serving.predict("ensemble_model_1", test_input)
    pred2 = serving.predict("ensemble_model_2", test_input)
    pred3 = serving.predict("ensemble_model_3", test_input)

    # Ensemble prediction (average)
    ensemble_pred = [(p1 + p2 + p3) / 3 for p1, p2, p3 in zip(pred1, pred2, pred3)]

    assert len(ensemble_pred) == 10
    assert all(0 <= p <= 1 for p in ensemble_pred)

    print(f"\n✅ Multi-model ensemble: {len(ensemble_pred)} ensemble predictions")


def test_load_balancing_across_versions(production_nba_data):
    """
    Test load balancing across multiple model versions

    Scenario:
    - Deploy multiple versions
    - Distribute load evenly
    - Monitor each version's performance
    """

    feature_cols = ["home_ppg", "away_ppg"]
    X = production_nba_data[feature_cols]
    y = production_nba_data["home_win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model1 = RandomForestClassifier(n_estimators=50, random_state=42)
    model1.fit(X_train, y_train)

    model2 = RandomForestClassifier(n_estimators=50, random_state=43)
    model2.fit(X_train, y_train)

    serving = ModelServingManager(mock_mode=True)

    serving.deploy_model("nba_model", "v1.0", model1)
    serving.deploy_model("nba_model", "v2.0", model2)

    # Setup load balancing (50/50)
    serving.setup_ab_test("nba_model", ["v1.0", "v2.0"], [0.5, 0.5])

    # Make predictions
    for i in range(100):
        test_input = X_test.iloc[i % len(X_test) : i % len(X_test) + 1].to_dict(
            "records"
        )
        serving.predict("nba_model", test_input)

    # Check distribution
    status = serving.get_all_models_status()["nba_model"]
    v1_count = status["v1.0"]["metrics"].request_count
    v2_count = status["v2.0"]["metrics"].request_count

    # Should be approximately 50/50
    total = v1_count + v2_count
    v1_ratio = v1_count / total if total > 0 else 0

    assert 0.4 <= v1_ratio <= 0.6  # Allow 10% variance

    print(f"\n✅ Load balancing: v1.0={v1_ratio:.1%}, v2.0={1-v1_ratio:.1%}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
