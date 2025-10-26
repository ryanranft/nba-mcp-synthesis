"""
Tests for Econometric Suite Module.

Tests cover:
- Data structure detection
- Auto-method selection
- Module integration
- Model comparison
- Model averaging

Author: Agent 8 Module 4D
Date: October 2025
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from mcp_server.econometric_suite import (
    EconometricSuite,
    DataClassifier,
    DataStructure,
    DataCharacteristics,
    MethodCategory,
    SuiteResult,
    ModelAverager,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def cross_section_data():
    """Generate cross-sectional data."""
    np.random.seed(42)
    n = 100

    return pd.DataFrame(
        {
            "player_id": range(n),
            "points": np.random.normal(20, 5, n),
            "assists": np.random.normal(5, 2, n),
            "rebounds": np.random.normal(8, 3, n),
        }
    )


@pytest.fixture
def time_series_data():
    """Generate time series data."""
    np.random.seed(42)
    n = 200

    dates = pd.date_range(start="2020-01-01", periods=n, freq="D")
    values = np.random.normal(20, 3, n).cumsum()

    return pd.DataFrame({"date": dates, "points": values})


@pytest.fixture
def panel_data():
    """Generate panel data."""
    np.random.seed(42)
    n_players = 50
    n_seasons = 5

    data = []
    for player in range(n_players):
        for season in range(n_seasons):
            data.append(
                {
                    "player_id": player,
                    "season": season,
                    "points": np.random.normal(20 + player * 0.1, 5),
                    "assists": np.random.normal(5, 2),
                }
            )

    return pd.DataFrame(data)


@pytest.fixture
def survival_data():
    """Generate survival/event history data."""
    np.random.seed(42)
    n = 100

    return pd.DataFrame(
        {
            "player_id": range(n),
            "career_years": np.random.exponential(8, n),
            "retired": np.random.binomial(1, 0.7, n),
            "draft_position": np.random.randint(1, 60, n),
        }
    )


@pytest.fixture
def treatment_outcome_data():
    """Generate treatment-outcome data for causal inference."""
    np.random.seed(42)
    n = 200

    treatment = np.random.binomial(1, 0.5, n)
    # True treatment effect = 5
    outcome = 20 + 5 * treatment + np.random.normal(0, 3, n)

    return pd.DataFrame(
        {
            "player_id": range(n),
            "new_coach": treatment,
            "wins": outcome,
            "team_salary": np.random.normal(100, 20, n),
            "avg_age": np.random.normal(27, 3, n),
        }
    )


# ==============================================================================
# Data Classification Tests (5 tests)
# ==============================================================================


def test_detect_cross_section(cross_section_data):
    """Test detection of cross-sectional data."""
    classifier = DataClassifier(data=cross_section_data)

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.CROSS_SECTION
    assert characteristics.n_obs == 100
    assert not characteristics.has_time_index


def test_detect_time_series(time_series_data):
    """Test detection of time series data."""
    # Set date as index
    ts_data = time_series_data.set_index("date")

    classifier = DataClassifier(data=ts_data)

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.TIME_SERIES
    assert characteristics.n_obs == 200
    assert characteristics.has_time_index


def test_detect_panel(panel_data):
    """Test detection of panel data."""
    classifier = DataClassifier(
        data=panel_data, entity_col="player_id", time_col="season"
    )

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.PANEL
    assert characteristics.n_obs == 250
    assert characteristics.n_entities == 50
    assert characteristics.n_periods == 5
    assert characteristics.is_balanced


def test_detect_survival(survival_data):
    """Test detection of event history/survival data."""
    classifier = DataClassifier(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.EVENT_HISTORY
    assert characteristics.has_duration
    assert characteristics.has_event


def test_detect_treatment_outcome(treatment_outcome_data):
    """Test detection of treatment-outcome structure."""
    classifier = DataClassifier(
        data=treatment_outcome_data, treatment_col="new_coach", outcome_col="wins"
    )

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.TREATMENT_OUTCOME
    assert characteristics.has_treatment
    assert characteristics.has_outcome


# ==============================================================================
# Recommendation Tests (5 tests)
# ==============================================================================


def test_recommend_survival_methods(survival_data):
    """Test method recommendation for survival data."""
    classifier = DataClassifier(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    recommendations = classifier.recommend_methods()

    assert MethodCategory.SURVIVAL_ANALYSIS in recommendations


def test_recommend_causal_methods(treatment_outcome_data):
    """Test method recommendation for causal inference."""
    classifier = DataClassifier(
        data=treatment_outcome_data, treatment_col="new_coach", outcome_col="wins"
    )

    recommendations = classifier.recommend_methods()

    assert MethodCategory.CAUSAL_INFERENCE in recommendations


def test_recommend_panel_methods(panel_data):
    """Test method recommendation for panel data."""
    classifier = DataClassifier(
        data=panel_data, entity_col="player_id", time_col="season"
    )

    recommendations = classifier.recommend_methods()

    assert MethodCategory.PANEL_DATA in recommendations
    assert MethodCategory.BAYESIAN in recommendations


def test_recommend_time_series_methods(time_series_data):
    """Test method recommendation for time series data."""
    ts_data = time_series_data.set_index("date")

    classifier = DataClassifier(data=ts_data)

    recommendations = classifier.recommend_methods()

    assert MethodCategory.TIME_SERIES in recommendations
    assert MethodCategory.ADVANCED_TIME_SERIES in recommendations


def test_recommend_cross_section_methods(cross_section_data):
    """Test method recommendation for cross-sectional data."""
    classifier = DataClassifier(data=cross_section_data)

    recommendations = classifier.recommend_methods()

    assert MethodCategory.BAYESIAN in recommendations


# ==============================================================================
# Suite Initialization Tests (3 tests)
# ==============================================================================


def test_suite_initialization_time_series(time_series_data):
    """Test suite initialization with time series data."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    assert suite.characteristics.structure == DataStructure.TIME_SERIES
    assert MethodCategory.TIME_SERIES in suite.recommended_methods


def test_suite_initialization_panel(panel_data):
    """Test suite initialization with panel data."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    assert suite.characteristics.structure == DataStructure.PANEL
    assert suite.characteristics.n_entities == 50
    assert suite.characteristics.n_periods == 5


def test_suite_initialization_survival(survival_data):
    """Test suite initialization with survival data."""
    suite = EconometricSuite(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    assert suite.characteristics.structure == DataStructure.EVENT_HISTORY
    assert MethodCategory.SURVIVAL_ANALYSIS in suite.recommended_methods


# ==============================================================================
# Method Access Tests (6 tests)
# ==============================================================================


def test_time_series_analysis(time_series_data):
    """Test access to time series methods."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.TIME_SERIES
    assert result.method_used == "ARIMA"
    assert result.aic is not None


def test_panel_analysis_fixed_effects(panel_data):
    """Test access to panel data fixed effects."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    result = suite.panel_analysis(method="fixed_effects")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.PANEL_DATA
    assert result.method_used == "Fixed Effects"
    assert result.r_squared is not None


def test_panel_analysis_random_effects(panel_data):
    """Test access to panel data random effects."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    result = suite.panel_analysis(method="random_effects")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.PANEL_DATA
    assert result.method_used == "Random Effects"


def test_causal_analysis(treatment_outcome_data):
    """Test access to causal inference methods."""
    suite = EconometricSuite(
        data=treatment_outcome_data,
        treatment_col="new_coach",
        outcome_col="wins",
    )

    result = suite.causal_analysis(method="psm", n_neighbors=3)

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.CAUSAL_INFERENCE
    assert result.method_used == "Propensity Score Matching"


def test_survival_analysis(survival_data):
    """Test access to survival analysis methods."""
    suite = EconometricSuite(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    result = suite.survival_analysis(method="cox")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.SURVIVAL_ANALYSIS
    assert result.method_used == "Cox Proportional Hazards"
    assert result.log_likelihood is not None


def test_advanced_time_series_analysis(time_series_data):
    """Test access to advanced time series methods."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.advanced_time_series_analysis(
        method="kalman", model="local_level"
    )

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.ADVANCED_TIME_SERIES
    assert result.method_used == "Kalman Filter"


# ==============================================================================
# Model Averaging Tests (4 tests)
# ==============================================================================


def test_model_averaging_equal_weights():
    """Test equal-weight model averaging."""
    predictions = {
        "model1": np.array([10, 20, 30]),
        "model2": np.array([12, 18, 32]),
        "model3": np.array([11, 19, 31]),
    }

    averaged = ModelAverager.average(predictions, weights="equal")

    expected = np.array([11, 19, 31])
    np.testing.assert_array_almost_equal(averaged, expected)


def test_model_averaging_aic_weights():
    """Test AIC-based model averaging."""
    predictions = {
        "model1": np.array([10.0, 20.0, 30.0]),
        "model2": np.array([12.0, 18.0, 32.0]),
    }

    metrics = {
        "model1": {"aic": 100.0, "bic": 105.0},
        "model2": {"aic": 110.0, "bic": 115.0},  # Worse AIC
    }

    averaged = ModelAverager.average(
        predictions, weights="aic", model_metrics=metrics
    )

    # model1 should have higher weight (lower AIC)
    # Result should be closer to model1 than model2
    assert np.abs(averaged[0] - 10.0) < np.abs(averaged[0] - 12.0)


def test_model_averaging_custom_weights():
    """Test custom weight model averaging."""
    predictions = {
        "model1": np.array([10, 20, 30]),
        "model2": np.array([20, 30, 40]),
    }

    custom_weights = {"model1": 0.7, "model2": 0.3}

    averaged = ModelAverager.average(predictions, weights=custom_weights)

    expected = 0.7 * predictions["model1"] + 0.3 * predictions["model2"]
    np.testing.assert_array_almost_equal(averaged, expected)


def test_model_averaging_mismatched_shapes():
    """Test that mismatched prediction shapes raise error."""
    predictions = {
        "model1": np.array([10, 20, 30]),
        "model2": np.array([12, 18]),  # Different length
    }

    with pytest.raises(ValueError, match="shapes don't match"):
        ModelAverager.average(predictions)


# ==============================================================================
# Model Comparison Tests (2 tests)
# ==============================================================================


def test_compare_panel_methods(panel_data):
    """Test comparison of panel data methods."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    methods = [
        {"category": "panel", "method": "fixed_effects", "params": {}},
        {"category": "panel", "method": "random_effects", "params": {}},
    ]

    comparison = suite.compare_methods(methods, metric="r_squared")

    assert len(comparison) == 2
    assert "method" in comparison.columns
    assert "r_squared" in comparison.columns
    assert "rank" in comparison.columns


def test_compare_time_series_methods(time_series_data):
    """Test comparison of time series methods."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    methods = [
        {"category": "time_series", "method": "arima", "params": {"order": (1, 1, 1)}},
        {"category": "time_series", "method": "arima", "params": {"order": (2, 1, 0)}},
    ]

    comparison = suite.compare_methods(methods, metric="aic")

    assert len(comparison) == 2
    assert "aic" in comparison.columns
    assert "rank" in comparison.columns


# ==============================================================================
# Auto-Analysis Tests (3 tests)
# ==============================================================================


def test_auto_analysis_time_series(time_series_data):
    """Test auto-analysis for time series data."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    # Auto should select time series method
    result = suite.analyze(method="auto")

    assert isinstance(result, SuiteResult)
    assert result.method_category in [
        MethodCategory.TIME_SERIES,
        MethodCategory.ADVANCED_TIME_SERIES,
    ]


def test_auto_analysis_panel(panel_data):
    """Test auto-analysis for panel data."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    result = suite.analyze(method="auto")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.PANEL_DATA


def test_auto_analysis_survival(survival_data):
    """Test auto-analysis for survival data."""
    suite = EconometricSuite(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    result = suite.analyze(method="auto")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.SURVIVAL_ANALYSIS


# ==============================================================================
# Suite Result Tests (2 tests)
# ==============================================================================


def test_suite_result_summary():
    """Test SuiteResult summary generation."""
    result = SuiteResult(
        data_structure=DataStructure.PANEL,
        method_category=MethodCategory.PANEL_DATA,
        method_used="Fixed Effects",
        result=None,
        model=None,
        aic=1234.5,
        bic=1250.0,
        r_squared=0.67,
        n_obs=250,
    )

    summary = result.summary()

    assert "ECONOMETRIC SUITE RESULTS" in summary
    assert "panel" in summary.lower()
    assert "Fixed Effects" in summary
    assert "1234.5" in summary
    assert "0.67" in summary


def test_suite_result_repr():
    """Test SuiteResult string representation."""
    result = SuiteResult(
        data_structure=DataStructure.TIME_SERIES,
        method_category=MethodCategory.TIME_SERIES,
        method_used="ARIMA",
        result=None,
        model=None,
        aic=500.0,
    )

    repr_str = repr(result)

    assert "SuiteResult" in repr_str
    assert "time_series" in repr_str
    assert "ARIMA" in repr_str


# ==============================================================================
# Integration Tests (1 test)
# ==============================================================================


def test_end_to_end_workflow(panel_data):
    """Test complete end-to-end workflow."""
    # Initialize suite
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    # Check data classification
    assert suite.characteristics.structure == DataStructure.PANEL
    assert len(suite.recommended_methods) > 0

    # Run analysis
    result = suite.panel_analysis(method="fixed_effects")

    assert isinstance(result, SuiteResult)
    assert result.n_obs == 250

    # Get summary
    summary = suite.diagnostic_summary(result)
    assert "Fixed Effects" in summary
    assert "250" in summary
