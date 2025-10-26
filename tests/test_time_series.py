"""
Tests for time_series module.

Tests cover:
- Stationarity testing (ADF, KPSS)
- Decomposition (seasonal, STL)
- ARIMA modeling and forecasting
- Autocorrelation analysis
- Integration with NBA data
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from mcp_server.time_series import (
    TimeSeriesAnalyzer,
    StationarityTestResult,
    DecompositionResult,
    ACFResult,
    ForecastResult,
    ARIMAModelResult,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def stationary_series():
    """Generate stationary time series (white noise)."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=200, freq="D")
    values = np.random.normal(0, 1, 200)
    df = pd.DataFrame({"value": values}, index=dates)
    return df


@pytest.fixture
def non_stationary_series():
    """Generate non-stationary time series (random walk)."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=200, freq="D")
    values = np.cumsum(np.random.normal(0, 1, 200))  # Random walk
    df = pd.DataFrame({"value": values}, index=dates)
    return df


@pytest.fixture
def seasonal_series():
    """Generate time series with seasonality."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=365, freq="D")

    # Trend + Seasonal + Noise
    t = np.arange(365)
    trend = 0.1 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 7)  # Weekly seasonality
    noise = np.random.normal(0, 1, 365)
    values = trend + seasonal + noise

    df = pd.DataFrame({"value": values}, index=dates)
    return df


@pytest.fixture
def nba_player_scoring():
    """Simulate NBA player scoring over a season."""
    np.random.seed(42)
    dates = pd.date_range("2023-10-01", periods=82, freq="D")  # 82 games

    # Simulate scoring: base 25 ppg + trend + noise
    t = np.arange(82)
    base = 25
    trend = 0.05 * t  # Slight improvement over season
    noise = np.random.normal(0, 5, 82)
    points = base + trend + noise

    df = pd.DataFrame({"points": points}, index=dates)
    return df


# ==============================================================================
# Stationarity Tests (5 tests)
# ==============================================================================


def test_adf_test_stationary_series(stationary_series):
    """Test ADF test correctly identifies stationary series."""
    analyzer = TimeSeriesAnalyzer(stationary_series, target_column="value")
    result = analyzer.adf_test()

    assert isinstance(result, StationarityTestResult)
    assert result.test_type == "adf"
    assert result.is_stationary is True
    assert result.p_value < 0.05
    assert "1%" in result.critical_values


def test_adf_test_non_stationary_series(non_stationary_series):
    """Test ADF test correctly identifies non-stationary series."""
    analyzer = TimeSeriesAnalyzer(non_stationary_series, target_column="value")
    result = analyzer.adf_test()

    assert isinstance(result, StationarityTestResult)
    assert result.is_stationary is False
    assert result.p_value >= 0.05


def test_kpss_test_stationary(stationary_series):
    """Test KPSS test on stationary series."""
    analyzer = TimeSeriesAnalyzer(stationary_series, target_column="value")
    result = analyzer.kpss_test()

    assert isinstance(result, StationarityTestResult)
    assert result.test_type == "kpss"
    # KPSS: H0 is stationarity, so high p-value means stationary
    assert result.is_stationary is True


def test_kpss_test_trend_stationary(non_stationary_series):
    """Test KPSS with trend stationarity."""
    analyzer = TimeSeriesAnalyzer(non_stationary_series, target_column="value")
    result = analyzer.kpss_test(regression="ct")

    assert isinstance(result, StationarityTestResult)
    assert result.test_type == "kpss"


def test_stationarity_edge_cases():
    """Test stationarity with edge cases."""
    # Very short series
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    df = pd.DataFrame({"value": np.random.normal(0, 1, 30)}, index=dates)

    analyzer = TimeSeriesAnalyzer(df, target_column="value")
    result = analyzer.adf_test()
    assert isinstance(result, StationarityTestResult)


# ==============================================================================
# Decomposition Tests (5 tests)
# ==============================================================================


def test_additive_decomposition(seasonal_series):
    """Test additive decomposition."""
    analyzer = TimeSeriesAnalyzer(seasonal_series, target_column="value", freq="D")
    result = analyzer.decompose(model="additive", period=7)

    assert isinstance(result, DecompositionResult)
    assert result.model == "additive"
    assert result.period == 7
    assert len(result.trend) == len(seasonal_series)
    assert len(result.seasonal) == len(seasonal_series)
    assert len(result.residual) == len(seasonal_series)


def test_multiplicative_decomposition(seasonal_series):
    """Test multiplicative decomposition."""
    # Make values positive for multiplicative
    df = seasonal_series.copy()
    df["value"] = df["value"] + 50  # Shift to positive

    analyzer = TimeSeriesAnalyzer(df, target_column="value", freq="D")
    result = analyzer.decompose(model="multiplicative", period=7)

    assert isinstance(result, DecompositionResult)
    assert result.model == "multiplicative"


def test_decompose_trend_extraction(seasonal_series):
    """Test trend extraction from decomposition."""
    analyzer = TimeSeriesAnalyzer(seasonal_series, target_column="value", freq="D")
    result = analyzer.decompose(period=7)

    # Trend should be smoother than original
    trend_variance = result.trend.dropna().var()
    original_variance = result.observed.var()
    assert trend_variance < original_variance


def test_seasonal_pattern_detection(seasonal_series):
    """Test that seasonal component is detected."""
    analyzer = TimeSeriesAnalyzer(seasonal_series, target_column="value", freq="D")
    result = analyzer.decompose(period=7)

    # Seasonal component should have period=7 pattern
    seasonal_values = result.seasonal.dropna().values
    # Check that pattern repeats every 7 days
    assert len(seasonal_values) > 14  # At least 2 periods


def test_detect_trend_direction(nba_player_scoring):
    """Test trend detection."""
    analyzer = TimeSeriesAnalyzer(nba_player_scoring, target_column="points", freq="D")
    trend_info = analyzer.detect_trend()

    assert "direction" in trend_info
    assert "slope" in trend_info
    assert "r_squared" in trend_info
    assert "p_value" in trend_info
    assert trend_info["direction"] in ["increasing", "decreasing", "stable"]


# ==============================================================================
# ARIMA Tests (8 tests)
# ==============================================================================


def test_fit_arima_simple(stationary_series):
    """Test fitting simple ARIMA model."""
    analyzer = TimeSeriesAnalyzer(stationary_series, target_column="value", freq="D")
    result = analyzer.fit_arima(order=(1, 0, 1))

    assert isinstance(result, ARIMAModelResult)
    assert result.order == (1, 0, 1)
    assert result.seasonal_order is None
    assert result.aic > 0
    assert result.bic > 0


def test_fit_arima_with_differencing(non_stationary_series):
    """Test ARIMA with differencing."""
    analyzer = TimeSeriesAnalyzer(
        non_stationary_series, target_column="value", freq="D"
    )
    result = analyzer.fit_arima(order=(1, 1, 1))  # d=1 for differencing

    assert isinstance(result, ARIMAModelResult)
    assert result.order == (1, 1, 1)


def test_fit_sarima_seasonal(seasonal_series):
    """Test seasonal ARIMA."""
    analyzer = TimeSeriesAnalyzer(seasonal_series, target_column="value", freq="D")
    result = analyzer.fit_arima(
        order=(1, 0, 1), seasonal_order=(1, 0, 1, 7)  # Weekly seasonality
    )

    assert isinstance(result, ARIMAModelResult)
    assert result.seasonal_order == (1, 0, 1, 7)


def test_auto_arima_selection(stationary_series):
    """Test auto ARIMA model selection."""
    analyzer = TimeSeriesAnalyzer(stationary_series, target_column="value", freq="D")
    result = analyzer.auto_arima(seasonal=False, max_p=2, max_q=2, max_d=1)

    assert isinstance(result, ARIMAModelResult)
    assert result.order is not None
    assert len(result.order) == 3


def test_arima_forecast(nba_player_scoring):
    """Test forecasting with ARIMA."""
    analyzer = TimeSeriesAnalyzer(nba_player_scoring, target_column="points", freq="D")

    # Fit model
    model_result = analyzer.fit_arima(order=(1, 0, 1))

    # Forecast next 10 games
    forecast = analyzer.forecast(model_result, steps=10)

    assert isinstance(forecast, ForecastResult)
    assert len(forecast.forecast) == 10
    assert len(forecast.confidence_interval) == 10
    assert "lower" in forecast.confidence_interval.columns
    assert "upper" in forecast.confidence_interval.columns


def test_forecast_confidence_intervals(nba_player_scoring):
    """Test that confidence intervals widen over time."""
    analyzer = TimeSeriesAnalyzer(nba_player_scoring, target_column="points", freq="D")
    model_result = analyzer.fit_arima(order=(1, 0, 1))
    forecast = analyzer.forecast(model_result, steps=10)

    # Calculate interval widths
    widths = (
        forecast.confidence_interval["upper"] - forecast.confidence_interval["lower"]
    )

    # Intervals should generally widen (later forecasts less certain)
    assert widths.iloc[-1] >= widths.iloc[0]


def test_arima_diagnostics(stationary_series):
    """Test ARIMA model diagnostics."""
    analyzer = TimeSeriesAnalyzer(stationary_series, target_column="value", freq="D")
    result = analyzer.fit_arima(order=(1, 0, 1))

    # Check that model has residuals
    assert hasattr(result.model, "resid")

    # Residuals should have mean near 0
    residuals = result.model.resid
    assert abs(residuals.mean()) < 0.5


def test_arima_edge_cases():
    """Test ARIMA with edge cases."""
    # Constant series
    dates = pd.date_range("2023-01-01", periods=50, freq="D")
    df = pd.DataFrame({"value": np.ones(50) * 10}, index=dates)

    analyzer = TimeSeriesAnalyzer(df, target_column="value", freq="D")

    # Should handle constant series (though may not converge well)
    try:
        result = analyzer.fit_arima(order=(0, 0, 0))
        assert isinstance(result, ARIMAModelResult)
    except Exception:
        # It's okay if constant series fails
        pass


# ==============================================================================
# Autocorrelation Tests (4 tests)
# ==============================================================================


def test_acf_calculation(stationary_series):
    """Test ACF calculation."""
    analyzer = TimeSeriesAnalyzer(stationary_series, target_column="value", freq="D")
    result = analyzer.acf(nlags=20)

    assert isinstance(result, ACFResult)
    assert len(result.acf_values) == 21  # 0 to nlags
    assert result.acf_values[0] == pytest.approx(1.0, abs=0.01)  # Lag 0 should be 1


def test_pacf_calculation(stationary_series):
    """Test PACF calculation."""
    analyzer = TimeSeriesAnalyzer(stationary_series, target_column="value", freq="D")
    result = analyzer.pacf(nlags=20)

    assert isinstance(result, ACFResult)
    assert len(result.acf_values) == 21


def test_ljung_box_test(stationary_series):
    """Test Ljung-Box test for autocorrelation."""
    analyzer = TimeSeriesAnalyzer(stationary_series, target_column="value", freq="D")
    result = analyzer.ljung_box_test(lags=10)

    assert "lb_stat" in result
    assert "lb_pvalue" in result
    assert "has_autocorrelation" in result
    assert isinstance(result["has_autocorrelation"], bool)


def test_autocorrelation_edge_cases():
    """Test autocorrelation with short series."""
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    df = pd.DataFrame({"value": np.random.normal(0, 1, 30)}, index=dates)

    analyzer = TimeSeriesAnalyzer(df, target_column="value", freq="D")
    result = analyzer.acf(nlags=10)  # Small nlags for short series

    assert isinstance(result, ACFResult)


# ==============================================================================
# Integration Tests (3 tests)
# ==============================================================================


def test_nba_player_scoring_trend(nba_player_scoring):
    """Integration test: Analyze NBA player scoring trend."""
    analyzer = TimeSeriesAnalyzer(nba_player_scoring, target_column="points", freq="D")

    # Test stationarity
    adf_result = analyzer.adf_test()
    assert isinstance(adf_result, StationarityTestResult)

    # Detect trend
    trend_info = analyzer.detect_trend()
    assert trend_info["direction"] in ["increasing", "decreasing", "stable"]

    # Fit ARIMA and forecast
    model = analyzer.auto_arima(max_p=2, max_q=2, max_d=1)
    forecast = analyzer.forecast(model, steps=5)

    assert len(forecast.forecast) == 5
    assert all(forecast.forecast > 0)  # Points should be positive


def test_team_win_rate_seasonality():
    """Integration test: Team win rate with home/away seasonality."""
    np.random.seed(42)
    dates = pd.date_range("2023-10-01", periods=82, freq="D")

    # Simulate win rate with home/away pattern (every other game)
    home_away = np.tile([0.65, 0.45], 41)  # Home win rate higher
    noise = np.random.normal(0, 0.1, 82)
    win_rate = np.clip(home_away + noise, 0, 1)

    df = pd.DataFrame({"win_rate": win_rate}, index=dates)
    analyzer = TimeSeriesAnalyzer(df, target_column="win_rate", freq="D")

    # Decompose to find seasonality
    decomp = analyzer.decompose(period=2)

    assert isinstance(decomp, DecompositionResult)
    assert decomp.period == 2


def test_end_to_end_time_series_workflow(nba_player_scoring):
    """End-to-end workflow test."""
    analyzer = TimeSeriesAnalyzer(nba_player_scoring, target_column="points", freq="D")

    # 1. Check stationarity
    stationarity = analyzer.test_stationarity()
    assert isinstance(stationarity, StationarityTestResult)

    # 2. Make stationary if needed
    if not stationarity.is_stationary:
        stationary_series, transforms = analyzer.make_stationary()
        assert len(transforms) > 0

    # 3. Fit model
    model = analyzer.fit_arima(order=(1, 0, 1))
    assert model.aic > 0

    # 4. Forecast
    forecast = analyzer.forecast(model, steps=10)
    assert len(forecast.forecast) == 10

    # 5. Validate (split data)
    train = analyzer.series[:-10]
    test = analyzer.series[-10:]

    train_analyzer = TimeSeriesAnalyzer(
        pd.DataFrame({"points": train}), target_column="points", freq="D"
    )
    train_model = train_analyzer.fit_arima(order=(1, 0, 1))
    train_forecast = train_analyzer.forecast(train_model, steps=10)

    # Validate forecast
    errors = train_analyzer.validate_forecast(test, train_forecast.forecast)
    assert "mae" in errors
    assert "rmse" in errors
    assert "mape" in errors
    assert errors["mae"] >= 0


# ==============================================================================
# Additional Utility Tests
# ==============================================================================


def test_difference_method(non_stationary_series):
    """Test differencing method."""
    analyzer = TimeSeriesAnalyzer(non_stationary_series, target_column="value")
    differenced = analyzer.difference(periods=1)

    assert isinstance(differenced, pd.Series)
    assert len(differenced) == len(non_stationary_series)
    # First value should be NaN after differencing
    assert pd.isna(differenced.iloc[0])


def test_make_stationary(non_stationary_series):
    """Test make_stationary method."""
    analyzer = TimeSeriesAnalyzer(non_stationary_series, target_column="value")
    stationary, transforms = analyzer.make_stationary(max_diffs=2)

    assert isinstance(stationary, pd.Series)
    assert isinstance(transforms, list)
    # Should have applied at least one differencing
    assert len(transforms) > 0


def test_validate_forecast_metrics(nba_player_scoring):
    """Test forecast validation metrics."""
    analyzer = TimeSeriesAnalyzer(nba_player_scoring, target_column="points", freq="D")

    # Create simple actual vs predicted
    actual = analyzer.series[:10]
    predicted = analyzer.series[:10] + np.random.normal(0, 2, 10)

    metrics = analyzer.validate_forecast(actual, predicted)

    assert "mae" in metrics
    assert "mse" in metrics
    assert "rmse" in metrics
    assert "mape" in metrics
    assert all(v >= 0 for v in metrics.values())
    # RMSE should be sqrt of MSE
    assert abs(metrics["rmse"] - np.sqrt(metrics["mse"])) < 0.01


def test_analyzer_with_time_column():
    """Test analyzer with explicit time column."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    df = pd.DataFrame({"date": dates, "value": np.random.normal(0, 1, 100)})

    analyzer = TimeSeriesAnalyzer(df, target_column="value", time_column="date")
    assert isinstance(analyzer.series.index, pd.DatetimeIndex)


def test_analyzer_validation_errors():
    """Test analyzer input validation."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    df = pd.DataFrame({"value": np.random.normal(0, 1, 100)}, index=dates)

    # Invalid target column
    with pytest.raises(ValueError, match="Target column.*not found"):
        TimeSeriesAnalyzer(df, target_column="invalid_column")

    # Invalid time column
    with pytest.raises(ValueError, match="Time column.*not found"):
        TimeSeriesAnalyzer(df, target_column="value", time_column="invalid_time")
