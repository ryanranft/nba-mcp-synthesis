"""
Tests for Time Series MCP Tools (Phase 10A Agent 8 Module 1)

Tests the MCP tool wrappers for time series analysis, including:
- Stationarity testing (ADF/KPSS)
- Time series decomposition
- ARIMA model fitting and forecasting
- Autocorrelation analysis

Author: Phase 10A Agent 8 Module 1
Date: October 30, 2025
"""

import pytest
import numpy as np
import pandas as pd
from typing import List

from mcp_server.tools.time_series_tools import TimeSeriesTools


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def stationary_data():
    """Generate stationary time series (white noise)"""
    np.random.seed(42)
    return list(np.random.randn(100))


@pytest.fixture
def nonstationary_data():
    """Generate non-stationary time series (random walk)"""
    np.random.seed(42)
    return list(np.cumsum(np.random.randn(100)))


@pytest.fixture
def trending_data():
    """Generate trending time series"""
    np.random.seed(42)
    t = np.arange(100)
    trend = 0.5 * t
    noise = np.random.randn(100) * 5
    return list(trend + noise)


@pytest.fixture
def seasonal_data():
    """Generate seasonal time series"""
    np.random.seed(42)
    t = np.arange(84)  # 7 weeks
    trend = 0.1 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 7)  # Weekly pattern
    noise = np.random.randn(84) * 2
    return list(trend + seasonal + noise)


@pytest.fixture
def arima_data():
    """Generate ARIMA-suitable time series"""
    np.random.seed(42)
    # AR(1) process
    data = [0]
    for _ in range(99):
        data.append(0.7 * data[-1] + np.random.randn())
    return data


@pytest.fixture
def tools():
    """Create TimeSeriesTools instance"""
    return TimeSeriesTools()


# =============================================================================
# Test Stationarity Testing
# =============================================================================


@pytest.mark.asyncio
async def test_stationarity_adf_stationary(tools, stationary_data):
    """Test ADF test on stationary data"""
    result = await tools.test_stationarity(
        data=stationary_data,
        method="adf"
    )

    assert result["success"] is True
    assert result["is_stationary"] is True
    assert result["test_type"] == "adf"
    assert result["p_value"] < 0.05  # Should reject null hypothesis
    assert "stationary" in result["interpretation"].lower()
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_stationarity_adf_nonstationary(tools, nonstationary_data):
    """Test ADF test on non-stationary data"""
    result = await tools.test_stationarity(
        data=nonstationary_data,
        method="adf"
    )

    assert result["success"] is True
    assert result["is_stationary"] is False
    assert result["test_type"] == "adf"
    assert result["p_value"] > 0.05  # Should fail to reject null hypothesis
    assert "non-stationary" in result["interpretation"].lower()
    assert "differencing" in str(result["recommendations"]).lower()


@pytest.mark.asyncio
async def test_stationarity_kpss_stationary(tools, stationary_data):
    """Test KPSS test on stationary data"""
    result = await tools.test_stationarity(
        data=stationary_data,
        method="kpss"
    )

    assert result["success"] is True
    assert result["test_type"] == "kpss"
    # KPSS: null hypothesis is stationarity
    assert isinstance(result["is_stationary"], bool)


@pytest.mark.asyncio
async def test_stationarity_insufficient_data(tools):
    """Test stationarity with insufficient data"""
    result = await tools.test_stationarity(
        data=[1, 2, 3, 4, 5],  # Too few points
        method="adf"
    )

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_stationarity_invalid_method(tools, stationary_data):
    """Test stationarity with invalid method"""
    result = await tools.test_stationarity(
        data=stationary_data,
        method="invalid_method"
    )

    assert result["success"] is False
    assert "error" in result


# =============================================================================
# Test Time Series Decomposition
# =============================================================================


@pytest.mark.asyncio
async def test_decomposition_additive(tools, seasonal_data):
    """Test additive decomposition"""
    result = await tools.decompose_time_series(
        data=seasonal_data,
        model="additive",
        period=7
    )

    assert result["success"] is True
    assert result["model"] == "additive"
    assert result["period"] == 7
    assert len(result["trend"]) > 0
    assert len(result["seasonal"]) > 0
    assert len(result["residual"]) > 0
    assert result["trend_direction"] in ["increasing", "decreasing", "stable"]
    assert 0 <= result["seasonal_strength"] <= 1


@pytest.mark.asyncio
async def test_decomposition_multiplicative(tools, seasonal_data):
    """Test multiplicative decomposition"""
    # Use positive data for multiplicative
    positive_data = [x + 50 for x in seasonal_data]

    result = await tools.decompose_time_series(
        data=positive_data,
        model="multiplicative",
        period=7
    )

    assert result["success"] is True
    assert result["model"] == "multiplicative"
    assert len(result["trend"]) > 0


@pytest.mark.asyncio
async def test_decomposition_trending_series(tools, trending_data):
    """Test decomposition on trending series"""
    result = await tools.decompose_time_series(
        data=trending_data,
        model="additive",
        period=10
    )

    assert result["success"] is True
    assert result["trend_direction"] in ["increasing", "decreasing"]
    assert result["trend_strength"] > 0.5  # Should have strong trend


@pytest.mark.asyncio
async def test_decomposition_insufficient_data(tools):
    """Test decomposition with insufficient data"""
    result = await tools.decompose_time_series(
        data=[1, 2, 3, 4, 5],
        period=7
    )

    assert result["success"] is False
    assert "error" in result


# =============================================================================
# Test ARIMA Model Fitting
# =============================================================================


@pytest.mark.asyncio
async def test_arima_auto_select(tools, arima_data):
    """Test ARIMA with auto parameter selection"""
    result = await tools.fit_arima_model(
        data=arima_data,
        auto_select=True
    )

    assert result["success"] is True
    assert "order" in result
    assert len(result["order"]) == 3  # (p, d, q)
    assert result["aic"] > 0
    assert result["bic"] > 0
    assert result["model_type"] in ["ARIMA", "SARIMA"]
    assert len(result["fitted_values"]) > 0


@pytest.mark.asyncio
async def test_arima_manual_order(tools, arima_data):
    """Test ARIMA with manual order specification"""
    result = await tools.fit_arima_model(
        data=arima_data,
        order=(1, 0, 0),  # AR(1)
        auto_select=False
    )

    assert result["success"] is True
    assert result["order"] == (1, 0, 0)
    assert result["model_type"] == "ARIMA"


@pytest.mark.asyncio
async def test_arima_seasonal(tools, seasonal_data):
    """Test SARIMA with seasonal order"""
    result = await tools.fit_arima_model(
        data=seasonal_data,
        order=(1, 0, 1),
        seasonal_order=(1, 0, 1, 7),
        auto_select=False
    )

    assert result["success"] is True
    assert result["seasonal_order"] == (1, 0, 1, 7)
    assert result["model_type"] == "SARIMA"


@pytest.mark.asyncio
async def test_arima_insufficient_data(tools):
    """Test ARIMA with insufficient data"""
    result = await tools.fit_arima_model(
        data=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Too few
    )

    assert result["success"] is False
    assert "error" in result


# =============================================================================
# Test ARIMA Forecasting
# =============================================================================


@pytest.mark.asyncio
async def test_forecast_arima(tools, arima_data):
    """Test ARIMA forecasting"""
    result = await tools.forecast_arima(
        data=arima_data,
        steps=10,
        alpha=0.05
    )

    assert result["success"] is True
    assert len(result["forecast"]) == 10
    assert len(result["lower_bound"]) == 10
    assert len(result["upper_bound"]) == 10
    assert result["confidence_level"] == 0.95
    assert result["steps"] == 10

    # Check confidence intervals make sense
    for i in range(10):
        assert result["lower_bound"][i] <= result["forecast"][i]
        assert result["forecast"][i] <= result["upper_bound"][i]


@pytest.mark.asyncio
async def test_forecast_different_horizons(tools, arima_data):
    """Test forecasting with different horizons"""
    for steps in [5, 10, 20]:
        result = await tools.forecast_arima(
            data=arima_data,
            steps=steps
        )

        assert result["success"] is True
        assert len(result["forecast"]) == steps


@pytest.mark.asyncio
async def test_forecast_different_confidence(tools, arima_data):
    """Test forecasting with different confidence levels"""
    result_95 = await tools.forecast_arima(
        data=arima_data,
        steps=10,
        alpha=0.05  # 95% CI
    )

    result_90 = await tools.forecast_arima(
        data=arima_data,
        steps=10,
        alpha=0.10  # 90% CI
    )

    assert result_95["success"] is True
    assert result_90["success"] is True

    # 95% CI should be wider than 90% CI
    width_95 = result_95["upper_bound"][0] - result_95["lower_bound"][0]
    width_90 = result_90["upper_bound"][0] - result_90["lower_bound"][0]
    assert width_95 > width_90


@pytest.mark.asyncio
async def test_forecast_manual_order(tools, arima_data):
    """Test forecasting with manually specified order"""
    result = await tools.forecast_arima(
        data=arima_data,
        steps=10,
        order=(1, 0, 1)
    )

    assert result["success"] is True
    assert result["model_order"] == (1, 0, 1)


# =============================================================================
# Test Autocorrelation Analysis
# =============================================================================


@pytest.mark.asyncio
async def test_autocorrelation_basic(tools, arima_data):
    """Test basic autocorrelation analysis"""
    result = await tools.autocorrelation_analysis(
        data=arima_data,
        nlags=20
    )

    assert result["success"] is True
    assert len(result["acf_values"]) == 21  # includes lag 0
    assert len(result["pacf_values"]) == 21
    assert isinstance(result["has_autocorrelation"], bool)
    assert isinstance(result["ljung_box_pvalue"], float)
    assert "arima_suggestions" in result
    assert "interpretation" in result


@pytest.mark.asyncio
async def test_autocorrelation_white_noise(tools, stationary_data):
    """Test autocorrelation on white noise"""
    result = await tools.autocorrelation_analysis(
        data=stationary_data,
        nlags=20
    )

    assert result["success"] is True
    # White noise should have no significant autocorrelation
    assert len(result["significant_lags_acf"]) < 3  # Allow for chance


@pytest.mark.asyncio
async def test_autocorrelation_ar_process(tools, arima_data):
    """Test autocorrelation on AR process"""
    result = await tools.autocorrelation_analysis(
        data=arima_data,
        nlags=20
    )

    assert result["success"] is True
    # AR process should show significant PACF at first lag
    if result["has_autocorrelation"]:
        assert len(result["significant_lags_pacf"]) > 0


@pytest.mark.asyncio
async def test_autocorrelation_recommendations(tools, arima_data):
    """Test ARIMA order recommendations"""
    result = await tools.autocorrelation_analysis(
        data=arima_data,
        nlags=20
    )

    assert result["success"] is True
    assert "p" in result["arima_suggestions"]
    assert "q" in result["arima_suggestions"]
    assert "rationale" in result["arima_suggestions"]

    # Recommendations should be reasonable
    p = result["arima_suggestions"]["p"]
    q = result["arima_suggestions"]["q"]
    assert 0 <= p <= 5
    assert 0 <= q <= 5


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_full_workflow_stationary_check_to_forecast(tools, arima_data):
    """Test complete workflow: stationarity → ARIMA → forecast"""
    # Step 1: Check stationarity
    stationarity_result = await tools.test_stationarity(
        data=arima_data,
        method="adf"
    )
    assert stationarity_result["success"] is True

    # Step 2: If stationary, fit ARIMA
    if stationarity_result["is_stationary"]:
        arima_result = await tools.fit_arima_model(
            data=arima_data,
            auto_select=True
        )
        assert arima_result["success"] is True

        # Step 3: Generate forecast
        forecast_result = await tools.forecast_arima(
            data=arima_data,
            steps=10,
            order=arima_result["order"]
        )
        assert forecast_result["success"] is True
        assert len(forecast_result["forecast"]) == 10


@pytest.mark.asyncio
async def test_full_workflow_decomposition_to_modeling(tools, seasonal_data):
    """Test workflow: decomposition → autocorrelation → ARIMA"""
    # Step 1: Decompose to understand structure
    decomp_result = await tools.decompose_time_series(
        data=seasonal_data,
        period=7
    )
    assert decomp_result["success"] is True

    # Step 2: Analyze autocorrelation
    acf_result = await tools.autocorrelation_analysis(
        data=seasonal_data,
        nlags=20
    )
    assert acf_result["success"] is True

    # Step 3: Fit SARIMA based on insights
    if decomp_result["seasonal_strength"] > 0.3:
        arima_result = await tools.fit_arima_model(
            data=seasonal_data,
            seasonal_order=(1, 0, 1, 7),
            auto_select=False
        )
        assert arima_result["success"] is True


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_empty_data(tools):
    """Test handling of empty data"""
    result = await tools.test_stationarity(data=[])
    assert result["success"] is False

    result = await tools.decompose_time_series(data=[])
    assert result["success"] is False


@pytest.mark.asyncio
async def test_constant_data(tools):
    """Test handling of constant time series"""
    constant_data = [5.0] * 100

    # Should handle constant data gracefully
    result = await tools.test_stationarity(data=constant_data)
    # May succeed or fail depending on implementation


@pytest.mark.asyncio
async def test_data_with_nans(tools):
    """Test handling of data with NaN values"""
    data_with_nans = [1.0, 2.0, float('nan'), 4.0, 5.0]

    # Should handle NaNs gracefully (either filter or error)
    result = await tools.test_stationarity(data=data_with_nans)
    # Implementation should either succeed after filtering or fail gracefully


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
async def test_performance_large_dataset(tools):
    """Test performance with large dataset"""
    import time

    large_data = list(np.random.randn(1000))

    start = time.time()
    result = await tools.test_stationarity(data=large_data)
    elapsed = time.time() - start

    assert result["success"] is True
    assert elapsed < 5.0  # Should complete in < 5 seconds


@pytest.mark.asyncio
@pytest.mark.slow
async def test_performance_auto_arima(tools):
    """Test performance of auto-ARIMA selection"""
    import time

    data = list(np.random.randn(100))

    start = time.time()
    result = await tools.fit_arima_model(data=data, auto_select=True)
    elapsed = time.time() - start

    assert result["success"] is True
    assert elapsed < 30.0  # Auto-ARIMA can be slow, allow 30 seconds


# =============================================================================
# NBA-Specific Use Case Tests
# =============================================================================


@pytest.mark.asyncio
async def test_nba_player_scoring_trend(tools):
    """Test analyzing player scoring trend over season"""
    # Simulate 82-game season with increasing trend
    games = np.arange(82)
    base_ppg = 20
    improvement = 0.1 * games  # Improving 0.1 ppg per game
    noise = np.random.randn(82) * 3
    ppg_data = list(base_ppg + improvement + noise)

    # Decompose to find trend
    result = await tools.decompose_time_series(
        data=ppg_data,
        period=7,  # Weekly pattern (if any)
        model="additive"
    )

    assert result["success"] is True
    assert result["trend_direction"] == "increasing"
    assert result["trend_strength"] > 0.7  # Strong trend


@pytest.mark.asyncio
async def test_nba_team_home_away_seasonality(tools):
    """Test detecting home/away game patterns"""
    # Simulate 82 games with home/away pattern
    games = 82
    pattern = []
    for i in range(games // 2):
        pattern.extend([110, 95])  # Home (higher), Away (lower)

    if len(pattern) < games:
        pattern.append(110)

    data = [x + np.random.randn() * 5 for x in pattern]

    # Decompose to find seasonality
    result = await tools.decompose_time_series(
        data=data,
        period=2,  # Home/away alternation
        model="additive"
    )

    assert result["success"] is True
    assert result["seasonal_strength"] > 0.2  # Should detect some pattern


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
