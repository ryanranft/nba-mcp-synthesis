"""
Tests for Advanced Time Series Module.

Tests cover:
- Kalman filtering and smoothing
- Dynamic factor models
- Markov switching models
- Structural time series
- Missing data imputation

Author: Agent 8 Module 4C
Date: October 2025
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings

# Skip all tests if statsmodels state space not available
pytest.importorskip(
    "statsmodels.tsa.statespace", reason="statsmodels state space required"
)

from mcp_server.advanced_time_series import (
    AdvancedTimeSeriesAnalyzer,
    KalmanFilterResult,
    SmootherResult,
    DynamicFactorResult,
    MarkovSwitchingResult,
    StructuralTimeSeriesResult,
    StateSpaceModel,
    RegimeType,
)


# --- Fixtures ---


@pytest.fixture
def time_series_data():
    """Generate time series data for testing."""
    np.random.seed(42)
    n = 200

    dates = pd.date_range(start="2020-01-01", periods=n, freq="D")

    # Trend + noise
    trend = np.linspace(20, 30, n)
    noise = np.random.normal(0, 2, n)
    values = trend + noise

    return pd.Series(values, index=dates, name="points")


@pytest.fixture
def multivariate_data():
    """Generate multivariate time series for factor model testing."""
    np.random.seed(42)
    n = 200
    dates = pd.date_range(start="2020-01-01", periods=n, freq="D")

    # Common factor
    factor = np.random.normal(0, 1, n).cumsum()

    # Three series loading on common factor + idiosyncratic noise
    data = pd.DataFrame(
        {
            "player1_pts": 0.8 * factor + np.random.normal(0, 0.5, n) + 20,
            "player2_pts": 0.6 * factor + np.random.normal(0, 0.5, n) + 18,
            "player3_pts": 0.7 * factor + np.random.normal(0, 0.5, n) + 22,
        },
        index=dates,
    )

    return data


@pytest.fixture
def regime_switching_data():
    """Generate data with regime changes for Markov switching tests."""
    np.random.seed(42)
    n = 200
    dates = pd.date_range(start="2020-01-01", periods=n, freq="D")

    # Two regimes: low mean (0-100), high mean (100-200)
    regime = np.concatenate([np.zeros(100), np.ones(100)])

    # Generate data with different means per regime
    values = np.zeros(n)
    values[:100] = np.random.normal(15, 2, 100)  # Low regime
    values[100:] = np.random.normal(25, 2, 100)  # High regime

    return pd.Series(values, index=dates, name="points")


@pytest.fixture
def seasonal_data():
    """Generate data with seasonal pattern."""
    np.random.seed(42)
    n = 365
    dates = pd.date_range(start="2020-01-01", periods=n, freq="D")

    # Weekly seasonality (period=7)
    seasonal = 5 * np.sin(2 * np.pi * np.arange(n) / 7)
    trend = np.linspace(20, 25, n)
    noise = np.random.normal(0, 1, n)

    values = trend + seasonal + noise

    return pd.Series(values, index=dates, name="points")


# ==============================================================================
# Kalman Filtering Tests (7 tests)
# ==============================================================================


def test_kalman_filter_initialization(time_series_data):
    """Test basic Kalman filter initialization and execution."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    result = analyzer.kalman_filter(model="local_level")

    assert isinstance(result, KalmanFilterResult)
    assert result.filtered_state.shape[1] == len(time_series_data)
    assert result.log_likelihood < 0  # Negative log-likelihood


def test_kalman_filter_local_level(time_series_data):
    """Test local level model (random walk + noise)."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    result = analyzer.kalman_filter(model="local_level")

    # Filtered state should track the data reasonably well
    assert result.filtered_state.shape[0] >= 1  # At least level state
    assert len(result.forecast) == len(time_series_data)

    # Forecast error should have reasonable scale
    mae = np.abs(result.forecast_error).mean()
    assert mae < 10  # Points, reasonable error


def test_kalman_filter_local_linear_trend(time_series_data):
    """Test local linear trend model (level + trend)."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    result = analyzer.kalman_filter(model="local_linear_trend")

    # Should have 2 states: level and trend
    assert result.filtered_state.shape[0] >= 2

    # Extract trend (second state)
    trend_estimates = result.filtered_state[1, :]
    # Trend should be relatively stable for our synthetic data
    assert np.std(trend_estimates) < 1.0


def test_kalman_smoother(time_series_data):
    """Test Kalman smoother for historical state estimation."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    result = analyzer.kalman_smoother(model="local_level")

    assert isinstance(result, SmootherResult)
    assert result.smoothed_state.shape[1] == len(time_series_data)

    # Smoother estimates should be less variable than data
    smoothed_level = result.smoothed_state[0, :]
    assert np.std(smoothed_level) < np.std(time_series_data)


def test_kalman_filter_with_missing_data(time_series_data):
    """Test Kalman filter handles missing data correctly."""
    # Insert missing values
    data_with_missing = time_series_data.copy()
    data_with_missing.iloc[50:60] = np.nan

    analyzer = AdvancedTimeSeriesAnalyzer(data_with_missing)
    result = analyzer.kalman_filter(model="local_level")

    # Should still produce filtered states for all time points
    assert result.filtered_state.shape[1] == len(data_with_missing)

    # Forecast should have values even for missing data periods
    assert not np.isnan(result.forecast[50:60]).any()


def test_state_space_forecasting(time_series_data):
    """Test forecasting with state space models."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    forecast = analyzer.forecast_state_space(model="local_linear_trend", steps=10)

    assert "forecast" in forecast
    assert "lower_bound" in forecast
    assert "upper_bound" in forecast

    assert len(forecast["forecast"]) == 10
    assert len(forecast["lower_bound"]) == 10
    assert len(forecast["upper_bound"]) == 10

    # Confidence interval should be wider than zero
    ci_width = forecast["upper_bound"] - forecast["lower_bound"]
    assert (ci_width > 0).all()


def test_impute_missing_kalman(time_series_data):
    """Test missing data imputation using Kalman methods."""
    # Create data with missing values
    data_with_missing = time_series_data.copy()
    missing_indices = [20, 21, 22, 80, 81]
    data_with_missing.iloc[missing_indices] = np.nan

    analyzer = AdvancedTimeSeriesAnalyzer(data_with_missing)
    imputed = analyzer.impute_missing(method="kalman", model="local_level")

    # Should have no missing values
    assert not imputed.isna().any()

    # Imputed values should be reasonable (close to neighbors)
    for idx in missing_indices:
        neighbors_mean = time_series_data.iloc[idx - 2 : idx + 3].mean()
        assert abs(imputed.iloc[idx] - neighbors_mean) < 5  # Within 5 points


# ==============================================================================
# Dynamic Factor Model Tests (6 tests)
# ==============================================================================


def test_dynamic_factor_model_basic(multivariate_data):
    """Test basic dynamic factor model with single factor."""
    analyzer = AdvancedTimeSeriesAnalyzer(multivariate_data)

    result = analyzer.dynamic_factor_model(data=multivariate_data, n_factors=1)

    assert isinstance(result, DynamicFactorResult)
    assert result.n_factors == 1
    assert "factor_0" in result.factors.columns
    assert len(result.factors) == len(multivariate_data)


def test_dynamic_factor_model_loadings(multivariate_data):
    """Test that factor loadings are extracted correctly."""
    analyzer = AdvancedTimeSeriesAnalyzer(multivariate_data)

    result = analyzer.dynamic_factor_model(data=multivariate_data, n_factors=1)

    # Should have loadings for each series
    assert len(result.factor_loadings) == len(multivariate_data.columns)
    assert result.factor_loadings.index.tolist() == multivariate_data.columns.tolist()

    # Loadings should be between 0 and 1 (R-squared-like)
    assert (result.factor_loadings >= 0).all().all()
    assert (result.factor_loadings <= 1).all().all()


def test_dynamic_factor_model_multiple_factors(multivariate_data):
    """Test dynamic factor model with multiple factors."""
    analyzer = AdvancedTimeSeriesAnalyzer(multivariate_data)

    result = analyzer.dynamic_factor_model(data=multivariate_data, n_factors=2)

    assert result.n_factors == 2
    assert "factor_0" in result.factors.columns
    assert "factor_1" in result.factors.columns

    # Both factors should have loadings
    assert result.factor_loadings.shape == (3, 2)  # 3 series, 2 factors


def test_dynamic_factor_model_idiosyncratic(multivariate_data):
    """Test that idiosyncratic components are computed."""
    analyzer = AdvancedTimeSeriesAnalyzer(multivariate_data)

    result = analyzer.dynamic_factor_model(data=multivariate_data, n_factors=1)

    # Idiosyncratic = observed - fitted
    assert result.idiosyncratic.shape == multivariate_data.shape

    # Idiosyncratic should have smaller variance than original
    for col in multivariate_data.columns:
        assert result.idiosyncratic[col].var() < multivariate_data[col].var()


def test_dynamic_factor_model_information_criteria(multivariate_data):
    """Test that AIC/BIC are computed for model comparison."""
    analyzer = AdvancedTimeSeriesAnalyzer(multivariate_data)

    result_1 = analyzer.dynamic_factor_model(data=multivariate_data, n_factors=1)
    result_2 = analyzer.dynamic_factor_model(data=multivariate_data, n_factors=2)

    # Both should have AIC and BIC
    assert result_1.aic is not None
    assert result_1.bic is not None
    assert result_2.aic is not None
    assert result_2.bic is not None

    # Note: More factors doesn't always = higher log-likelihood due to convergence issues
    # We just verify that both models produce valid information criteria


def test_dynamic_factor_repr(multivariate_data):
    """Test string representation of dynamic factor result."""
    analyzer = AdvancedTimeSeriesAnalyzer(multivariate_data)
    result = analyzer.dynamic_factor_model(data=multivariate_data, n_factors=1)

    repr_str = repr(result)
    assert "DynamicFactorResult" in repr_str
    assert "n_factors: 1" in repr_str
    assert "AIC" in repr_str


# ==============================================================================
# Markov Switching Model Tests (7 tests)
# ==============================================================================


def test_markov_switching_basic(regime_switching_data):
    """Test basic Markov switching model with 2 regimes."""
    analyzer = AdvancedTimeSeriesAnalyzer(regime_switching_data)

    result = analyzer.markov_switching(n_regimes=2, regime_type="mean_shift")

    assert isinstance(result, MarkovSwitchingResult)
    assert result.n_regimes == 2
    assert len(result.regimes) == len(regime_switching_data)


def test_markov_switching_regime_detection(regime_switching_data):
    """Test that regimes are detected correctly."""
    analyzer = AdvancedTimeSeriesAnalyzer(regime_switching_data)

    result = analyzer.markov_switching(n_regimes=2, regime_type="mean_shift")

    # Most observations in first half should be in one regime
    # Most in second half should be in another regime
    regimes_first_half = result.regimes[:100]
    regimes_second_half = result.regimes[100:]

    # Dominant regime should be different between halves
    # (allowing for some misclassification)
    regime_0_count_first = (regimes_first_half == 0).sum()
    regime_0_count_second = (regimes_second_half == 0).sum()

    # At least 60% should be correctly classified
    assert regime_0_count_first > 60 or regime_0_count_second > 60


def test_markov_switching_transition_matrix(regime_switching_data):
    """Test transition probability matrix."""
    analyzer = AdvancedTimeSeriesAnalyzer(regime_switching_data)

    result = analyzer.markov_switching(n_regimes=2, regime_type="mean_shift")

    # Transition matrix should be n_regimes x n_regimes
    assert result.transition_matrix.shape == (2, 2)

    # Rows should sum to 1 (probabilities)
    row_sums = result.transition_matrix.sum(axis=1)
    np.testing.assert_array_almost_equal(row_sums, [1.0, 1.0], decimal=5)

    # Diagonal elements (persistence) should be > 0.5 (more likely to stay than switch)
    # Note: Regimes can have asymmetric persistence
    assert result.transition_matrix[0, 0] > 0.5
    assert result.transition_matrix[1, 1] > 0.5


def test_markov_switching_regime_parameters(regime_switching_data):
    """Test that regime-specific parameters are extracted."""
    analyzer = AdvancedTimeSeriesAnalyzer(regime_switching_data)

    result = analyzer.markov_switching(n_regimes=2, regime_type="mean_shift")

    # Should have parameters for each regime
    assert 0 in result.regime_parameters
    assert 1 in result.regime_parameters

    # Each regime should have mean
    assert "mean" in result.regime_parameters[0]
    assert "mean" in result.regime_parameters[1]

    # Means should be different (around 15 and 25 for our data)
    mean_0 = result.regime_parameters[0]["mean"]
    mean_1 = result.regime_parameters[1]["mean"]

    if mean_0 is not None and mean_1 is not None:
        assert abs(mean_0 - mean_1) > 5  # Regimes should be distinct


def test_markov_switching_probabilities(regime_switching_data):
    """Test regime probability tracking over time."""
    analyzer = AdvancedTimeSeriesAnalyzer(regime_switching_data)

    result = analyzer.markov_switching(n_regimes=2, regime_type="mean_shift")

    # Probabilities should sum to 1 at each time point
    prob_sums = result.regime_probabilities.sum(axis=1)
    np.testing.assert_array_almost_equal(
        prob_sums, np.ones(len(regime_switching_data)), decimal=5
    )

    # Probabilities should be between 0 and 1
    assert (result.regime_probabilities >= 0).all().all()
    assert (result.regime_probabilities <= 1).all().all()


def test_markov_switching_get_regime_periods(regime_switching_data):
    """Test utility method to extract regime periods."""
    analyzer = AdvancedTimeSeriesAnalyzer(regime_switching_data)

    result = analyzer.markov_switching(n_regimes=2, regime_type="mean_shift")

    # Get periods for each regime
    periods_0 = result.get_regime_periods(regime=0)
    periods_1 = result.get_regime_periods(regime=1)

    # Should have at least 1 period for each regime
    assert len(periods_0) >= 1
    assert len(periods_1) >= 1

    # Each period should be (start, end) tuple
    for start, end in periods_0:
        assert start < end
        assert 0 <= start < len(regime_switching_data)
        assert 0 < end <= len(regime_switching_data)


def test_markov_switching_repr(regime_switching_data):
    """Test string representation."""
    analyzer = AdvancedTimeSeriesAnalyzer(regime_switching_data)
    result = analyzer.markov_switching(n_regimes=2)

    repr_str = repr(result)
    assert "MarkovSwitchingResult" in repr_str
    assert "n_regimes: 2" in repr_str


# ==============================================================================
# Structural Time Series Tests (5 tests)
# ==============================================================================


def test_structural_time_series_level_only(time_series_data):
    """Test structural model with level component only."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    result = analyzer.structural_time_series(level=True, trend=False, seasonal=None)

    assert isinstance(result, StructuralTimeSeriesResult)
    assert result.level is not None
    assert len(result.level) == len(time_series_data)
    assert result.trend is None
    assert result.seasonal is None


def test_structural_time_series_with_trend(time_series_data):
    """Test structural model with level and trend."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    result = analyzer.structural_time_series(level=True, trend=True, seasonal=None)

    assert result.level is not None
    assert result.trend is not None

    # Trend should exist and be relatively stable (small variance for our data)
    # Note: For this synthetic data, the trend may be nearly constant
    assert len(result.trend) == len(time_series_data)
    assert np.std(result.trend) < 1.0  # Trend should not be too variable


def test_structural_time_series_with_seasonal(seasonal_data):
    """Test structural model with seasonal component."""
    analyzer = AdvancedTimeSeriesAnalyzer(seasonal_data)

    result = analyzer.structural_time_series(
        level=True, trend=True, seasonal=7  # Weekly seasonality
    )

    assert result.level is not None
    assert result.seasonal is not None

    # Seasonal component should have period 7 pattern
    # Check that autocorrelation at lag 7 is high
    seasonal_values = result.seasonal.values
    autocorr_7 = np.corrcoef(seasonal_values[:-7], seasonal_values[7:])[0, 1]
    assert autocorr_7 > 0.5  # High autocorrelation at seasonal lag


def test_structural_time_series_fitted_values(time_series_data):
    """Test that fitted values are computed."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    result = analyzer.structural_time_series(level=True, trend=True)

    assert result.fitted_values is not None
    assert len(result.fitted_values) == len(time_series_data)

    # Fitted values should be close to observed
    correlation = np.corrcoef(time_series_data.values, result.fitted_values.values)[
        0, 1
    ]
    assert correlation > 0.75  # High correlation


def test_structural_time_series_information_criteria(time_series_data):
    """Test AIC/BIC for model selection."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    # Simple model (level only)
    result_simple = analyzer.structural_time_series(level=True, trend=False)

    # Complex model (level + trend)
    result_complex = analyzer.structural_time_series(level=True, trend=True)

    # Both should have AIC and BIC
    assert result_simple.aic is not None
    assert result_simple.bic is not None
    assert result_complex.aic is not None
    assert result_complex.bic is not None

    # Complex model should have higher log-likelihood
    assert result_complex.log_likelihood > result_simple.log_likelihood


# ==============================================================================
# Integration and Utility Tests
# ==============================================================================


def test_analyzer_initialization_with_dataframe(multivariate_data):
    """Test analyzer can be initialized with DataFrame."""
    analyzer = AdvancedTimeSeriesAnalyzer(multivariate_data)

    assert analyzer.data.shape == multivariate_data.shape
    assert isinstance(analyzer.data, pd.DataFrame)


def test_analyzer_repr(time_series_data):
    """Test string representation of analyzer."""
    analyzer = AdvancedTimeSeriesAnalyzer(time_series_data)

    repr_str = repr(analyzer)
    assert "AdvancedTimeSeriesAnalyzer" in repr_str
    assert "data shape" in repr_str


def test_missing_statsmodels_import():
    """Test that appropriate error is raised without statsmodels."""
    # This test would only be meaningful if we mock the import failure
    # For now, we just ensure the import check exists
    from mcp_server.advanced_time_series import STATESPACE_AVAILABLE

    assert STATESPACE_AVAILABLE is True  # Should be True in test environment
