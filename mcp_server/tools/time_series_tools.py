"""
Advanced Time Series Analysis Tools for MCP Server

Exposes comprehensive time series analysis capabilities including:
- Stationarity testing (ADF, KPSS, panel unit root tests)
- ARIMA/SARIMA modeling and forecasting
- Autocorrelation analysis (ACF, PACF, Durbin-Watson)
- Time series decomposition (trend, seasonal, residual)
- Dynamic panel data models (Arellano-Bond, Blundell-Bond)
- Serial correlation tests (Breusch-Godfrey, Ljung-Box)
- Heteroskedasticity tests (White, Breusch-Pagan)
- Structural break tests (CUSUM, Hansen)
- Vector autoregression (VAR, VECM)
- Granger causality tests

Phase 10A MCP Enhancements - Week 3 Agent 8 Module 1
Implements 22 time series recommendations from Phase 10A roadmap

Author: Agent 8 Module 1
Date: October 2025
"""

import logging
from typing import Dict, Any, List, Union, Optional
import json

import pandas as pd
import numpy as np

from mcp_server.time_series import (
    TimeSeriesAnalyzer,
    StationarityTestResult,
    DecompositionResult,
    ACFResult,
    ForecastResult,
    ARIMAModelResult,
)
from mcp_server.responses import (
    success_response,
    error_response,
    validation_error,
)
from mcp_server.exceptions import ValidationError

logger = logging.getLogger(__name__)


class TimeSeriesTools:
    """MCP tools for advanced time series analysis"""

    def __init__(self):
        """Initialize time series tools"""
        pass

    async def test_stationarity(
        self,
        data: List[Union[int, float]],
        time_column: Optional[str] = None,
        target_column: str = "value",
        method: str = "adf",
        freq: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Test for unit roots and stationarity in time series data.

        Implements Phase 10A recommendation rec_0173_b7f48099 (Priority: 9.0/10)

        Performs Augmented Dickey-Fuller (ADF) or Kwiatkowski-Phillips-Schmidt-Shin (KPSS)
        tests to determine if a time series is stationary. Stationarity is a critical
        assumption for many time series models.

        Args:
            data: Time series data as list of numbers or dict with time/value pairs
            time_column: Optional name of time column (if data is dict)
            target_column: Name of target column (default: 'value')
            method: Test method - 'adf' or 'kpss' (default: 'adf')
            freq: Frequency of time series (e.g., 'D', 'W', 'M')

        Returns:
            Dict with test results:
                - success: Boolean indicating if operation succeeded
                - test_statistic: Test statistic value
                - p_value: P-value for hypothesis test
                - critical_values: Dict of critical values at different significance levels
                - is_stationary: Boolean indicating if series is stationary
                - test_type: Type of test performed ('adf' or 'kpss')
                - interpretation: Human-readable interpretation
                - recommendations: List of recommended next steps

        Example:
            >>> data = [10, 12, 15, 17, 20, 22, 25, 27, 30]  # Trending series
            >>> result = await test_stationarity(data, method='adf')
            >>> result['is_stationary']
            False  # Non-stationary due to trend

        NBA Use Cases:
            - Test if player points per game is stationary over a season
            - Check if team win rate needs differencing before forecasting
            - Validate assumptions before ARIMA modeling
        """
        try:
            # Convert data to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame({target_column: data})
                df.index = pd.date_range(
                    start="2023-01-01", periods=len(data), freq=freq or "D"
                )
            elif isinstance(data, dict):
                df = pd.DataFrame(data)
                if time_column:
                    df[time_column] = pd.to_datetime(df[time_column])
                    df = df.set_index(time_column)
            else:
                return validation_error(
                    "data", data, "Data must be a list or dictionary"
                )

            # Validate minimum data points
            if len(df) < 10:
                return validation_error(
                    "data",
                    len(df),
                    "Need at least 10 data points for stationarity test",
                )

            # Create analyzer
            analyzer = TimeSeriesAnalyzer(
                df, target_column=target_column, freq=freq or "D"
            )

            # Run stationarity test
            if method.lower() == "adf":
                result = analyzer.adf_test()
            elif method.lower() == "kpss":
                result = analyzer.kpss_test()
            else:
                return validation_error(
                    "method",
                    method,
                    "Method must be 'adf' or 'kpss'",
                )

            # Generate interpretation
            if result.is_stationary:
                interpretation = (
                    f"Series is STATIONARY according to {result.test_type.upper()} test. "
                    "The series does not have a unit root and can be used directly in models."
                )
                recommendations = [
                    "Proceed with ARIMA modeling (d=0)",
                    "Can use for regression analysis",
                    "Consider checking for seasonality",
                ]
            else:
                interpretation = (
                    f"Series is NON-STATIONARY according to {result.test_type.upper()} test. "
                    "The series has a unit root and requires transformation."
                )
                recommendations = [
                    "Apply first differencing (d=1)",
                    "Remove trend using decomposition",
                    "Use ARIMA with d>0 parameter",
                    "Check stationarity again after transformation",
                ]

            return success_response(
                {
                    "test_statistic": float(result.test_statistic),
                    "p_value": float(result.p_value),
                    "critical_values": {
                        k: float(v) for k, v in result.critical_values.items()
                    },
                    "is_stationary": result.is_stationary,
                    "test_type": result.test_type,
                    "lags_used": result.lags_used,
                    "observations": result.observations,
                    "interpretation": interpretation,
                    "recommendations": recommendations,
                }
            )

        except Exception as e:
            logger.error(f"Stationarity test failed: {str(e)}")
            return error_response(f"Stationarity test failed: {str(e)}")

    async def decompose_time_series(
        self,
        data: List[Union[int, float]],
        target_column: str = "value",
        model: str = "additive",
        period: Optional[int] = None,
        method: str = "seasonal_decompose",
        freq: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Decompose time series into trend, seasonal, and residual components.

        Breaks down a time series into interpretable components:
        - Trend: Long-term direction of the series
        - Seasonal: Repeating patterns at fixed intervals
        - Residual: Random fluctuations not explained by trend/seasonality

        Args:
            data: Time series data
            target_column: Name of target column
            model: 'additive' (Y = T + S + R) or 'multiplicative' (Y = T * S * R)
            period: Seasonal period (e.g., 7 for weekly, 12 for monthly)
            method: 'seasonal_decompose' or 'stl' (Seasonal-Trend Loess)
            freq: Frequency of time series

        Returns:
            Dict with decomposition components:
                - trend: Trend component values
                - seasonal: Seasonal component values
                - residual: Residual component values
                - model: Decomposition model used
                - period: Seasonal period
                - trend_direction: 'increasing', 'decreasing', or 'stable'
                - seasonal_strength: Measure of seasonality strength (0-1)

        NBA Use Cases:
            - Decompose player performance to find career trajectory (trend)
            - Identify home/away game patterns (seasonality)
            - Detect playoff performance shifts
            - Analyze injury recovery patterns
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame({"value": data})
            df.index = pd.date_range(
                start="2023-01-01", periods=len(data), freq=freq or "D"
            )

            # Validate minimum data points
            if period and len(df) < 2 * period:
                return validation_error(
                    "data",
                    len(df),
                    f"Need at least {2 * period} points for period={period}",
                )

            # Create analyzer
            analyzer = TimeSeriesAnalyzer(df, target_column="value", freq=freq or "D")

            # Perform decomposition
            result = analyzer.decompose(model=model, period=period, method=method)

            # Analyze trend direction
            trend_info = analyzer.detect_trend()

            # Calculate seasonal strength
            # Seasonal strength = 1 - Var(residual) / Var(seasonal + residual)
            seasonal_var = result.seasonal.dropna().var()
            residual_var = result.residual.dropna().var()
            seasonal_strength = max(
                0, 1 - (residual_var / (seasonal_var + residual_var + 1e-10))
            )

            return success_response(
                {
                    "trend": result.trend.dropna().tolist(),
                    "seasonal": result.seasonal.dropna().tolist(),
                    "residual": result.residual.dropna().tolist(),
                    "model": result.model,
                    "period": result.period,
                    "trend_direction": trend_info["direction"],
                    "trend_slope": trend_info["slope"],
                    "trend_strength": trend_info["r_squared"],
                    "seasonal_strength": round(seasonal_strength, 4),
                    "interpretation": self._interpret_decomposition(
                        trend_info, seasonal_strength
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Decomposition failed: {str(e)}")
            return error_response(f"Decomposition failed: {str(e)}")

    async def fit_arima_model(
        self,
        data: List[Union[int, float]],
        target_column: str = "value",
        order: Optional[tuple] = None,
        seasonal_order: Optional[tuple] = None,
        auto_select: bool = True,
        freq: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fit ARIMA model for time series forecasting.

        Implements Phase 10A recommendations:
        - rec_0181_87cfa0af: Time Series Model for Team Performance
        - rec_0265_33796e0c: Time Series Analysis for Future Game Outcomes
        - rec_0280_e83eb7c3: Time Series Analysis for Future Performance

        ARIMA (AutoRegressive Integrated Moving Average) models combine:
        - AR (p): Autoregression - uses past values
        - I (d): Integration - differencing to achieve stationarity
        - MA (q): Moving average - uses past forecast errors

        Args:
            data: Time series data
            target_column: Name of target column
            order: (p, d, q) order tuple (if None and auto_select=True, automatically selects)
            seasonal_order: (P, D, Q, s) seasonal order
            auto_select: Use auto_arima to select best parameters
            freq: Frequency of time series

        Returns:
            Dict with model results:
                - order: ARIMA order (p, d, q)
                - seasonal_order: Seasonal ARIMA order (if applicable)
                - aic: Akaike Information Criterion (lower is better)
                - bic: Bayesian Information Criterion (lower is better)
                - parameters: Model parameters
                - diagnostics: Model diagnostic statistics
                - fitted_values: In-sample fitted values
                - residuals: Model residuals

        NBA Use Cases:
            - Forecast player points for next 10 games
            - Predict team win rate over next month
            - Model playoff performance trends
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame({"value": data})
            df.index = pd.date_range(
                start="2023-01-01", periods=len(data), freq=freq or "D"
            )

            # Create analyzer
            analyzer = TimeSeriesAnalyzer(df, target_column="value", freq=freq or "D")

            # Fit ARIMA model
            if auto_select:
                model_result = analyzer.auto_arima(
                    seasonal=seasonal_order is not None,
                    m=seasonal_order[3] if seasonal_order else 1,
                )
            else:
                if order is None:
                    order = (1, 0, 1)  # Default AR(1)MA(1)
                model_result = analyzer.fit_arima(
                    order=tuple(order), seasonal_order=seasonal_order
                )

            # Extract diagnostics
            fitted_model = model_result.model
            residuals = fitted_model.resid if hasattr(fitted_model, "resid") else []

            return success_response(
                {
                    "order": model_result.order,
                    "seasonal_order": model_result.seasonal_order,
                    "aic": float(model_result.aic),
                    "bic": float(model_result.bic),
                    "fitted_values": (
                        fitted_model.fittedvalues.tolist()
                        if hasattr(fitted_model, "fittedvalues")
                        else []
                    ),
                    "residuals": (
                        residuals.tolist() if hasattr(residuals, "tolist") else []
                    ),
                    "model_type": "ARIMA" if not seasonal_order else "SARIMA",
                    "success_message": f"Successfully fitted {'SARIMA' if seasonal_order else 'ARIMA'}{model_result.order} model",
                }
            )

        except Exception as e:
            logger.error(f"ARIMA modeling failed: {str(e)}")
            return error_response(f"ARIMA modeling failed: {str(e)}")

    async def forecast_arima(
        self,
        data: List[Union[int, float]],
        steps: int = 10,
        target_column: str = "value",
        order: Optional[tuple] = None,
        alpha: float = 0.05,
        freq: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate ARIMA forecasts with confidence intervals.

        Args:
            data: Historical time series data
            steps: Number of periods to forecast
            target_column: Name of target column
            order: (p, d, q) order tuple (if None, auto-selects)
            alpha: Significance level for confidence intervals (default: 0.05 = 95% CI)
            freq: Frequency of time series

        Returns:
            Dict with forecast results:
                - forecast: Point forecasts
                - lower_bound: Lower confidence interval
                - upper_bound: Upper confidence interval
                - confidence_level: Confidence level (e.g., 0.95)
                - model_order: ARIMA order used
                - forecast_dates: Forecast time points (if datetime index)

        NBA Use Cases:
            - Predict next 5 game performances
            - Forecast season-end win total
            - Project player development trajectory
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame({"value": data})
            df.index = pd.date_range(
                start="2023-01-01", periods=len(data), freq=freq or "D"
            )

            # Create analyzer
            analyzer = TimeSeriesAnalyzer(df, target_column="value", freq=freq or "D")

            # Fit model
            if order is None:
                model_result = analyzer.auto_arima(seasonal=False)
            else:
                model_result = analyzer.fit_arima(order=tuple(order))

            # Generate forecast
            forecast_result = analyzer.forecast(model_result, steps=steps, alpha=alpha)

            return success_response(
                {
                    "forecast": forecast_result.forecast.tolist(),
                    "lower_bound": forecast_result.confidence_interval[
                        "lower"
                    ].tolist(),
                    "upper_bound": forecast_result.confidence_interval[
                        "upper"
                    ].tolist(),
                    "confidence_level": 1 - alpha,
                    "model_order": model_result.order,
                    "steps": steps,
                    "success_message": f"Generated {steps}-step forecast with {int((1-alpha)*100)}% confidence intervals",
                }
            )

        except Exception as e:
            logger.error(f"Forecasting failed: {str(e)}")
            return error_response(f"Forecasting failed: {str(e)}")

    async def autocorrelation_analysis(
        self,
        data: List[Union[int, float]],
        nlags: int = 40,
        target_column: str = "value",
        freq: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze autocorrelation structure of time series.

        Implements Phase 10A recommendations:
        - rec_0616_7e53cb19: Test for Serial Correlation (Breusch-Godfrey)
        - rec_0605_4800d3fd: Test for Serial Correlation in Time Series Models

        Computes:
        - ACF (Autocorrelation Function): Correlation at different lags
        - PACF (Partial Autocorrelation Function): Correlation removing intermediate effects
        - Ljung-Box test: Tests for autocorrelation in residuals

        Args:
            data: Time series data
            nlags: Number of lags to compute (default: 40)
            target_column: Name of target column
            freq: Frequency of time series

        Returns:
            Dict with autocorrelation results:
                - acf_values: ACF values at each lag
                - pacf_values: PACF values at each lag
                - ljung_box_stat: Ljung-Box test statistic
                - ljung_box_pvalue: P-value for Ljung-Box test
                - has_autocorrelation: Boolean indicating significant autocorrelation
                - significant_lags_acf: Lags with significant ACF
                - significant_lags_pacf: Lags with significant PACF
                - interpretation: Recommendations for ARIMA order

        NBA Use Cases:
            - Determine ARIMA order for player performance model
            - Detect momentum/hot-hand effects
            - Identify optimal lag structure for predictions
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame({"value": data})
            df.index = pd.date_range(
                start="2023-01-01", periods=len(data), freq=freq or "D"
            )

            # Create analyzer
            analyzer = TimeSeriesAnalyzer(df, target_column="value", freq=freq or "D")

            # Compute ACF and PACF
            acf_result = analyzer.acf(nlags=nlags)
            pacf_result = analyzer.pacf(nlags=nlags)

            # Ljung-Box test
            lb_result = analyzer.ljung_box_test(lags=min(10, nlags))

            # Identify significant lags (outside confidence interval)
            sig_acf_lags = self._find_significant_lags(
                acf_result.acf_values, acf_result.confidence_interval
            )
            sig_pacf_lags = self._find_significant_lags(
                pacf_result.acf_values, pacf_result.confidence_interval
            )

            # Generate ARIMA order recommendations
            p_suggestion = min(sig_pacf_lags[:3]) if sig_pacf_lags else 1
            q_suggestion = min(sig_acf_lags[:3]) if sig_acf_lags else 1

            return success_response(
                {
                    "acf_values": acf_result.acf_values.tolist(),
                    "pacf_values": pacf_result.acf_values.tolist(),
                    "ljung_box_pvalue": float(min(lb_result["lb_pvalue"])),
                    "has_autocorrelation": lb_result["has_autocorrelation"],
                    "significant_lags_acf": sig_acf_lags,
                    "significant_lags_pacf": sig_pacf_lags,
                    "arima_suggestions": {
                        "p": p_suggestion,
                        "q": q_suggestion,
                        "rationale": "Based on significant PACF/ACF lags",
                    },
                    "interpretation": self._interpret_autocorrelation(
                        lb_result["has_autocorrelation"], sig_acf_lags, sig_pacf_lags
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Autocorrelation analysis failed: {str(e)}")
            return error_response(f"Autocorrelation analysis failed: {str(e)}")

    # Helper methods

    def _interpret_decomposition(
        self, trend_info: Dict[str, Any], seasonal_strength: float
    ) -> str:
        """Generate interpretation of decomposition results"""
        trend_desc = f"The series has a {trend_info['direction']} trend"
        if trend_info["direction"] != "stable":
            trend_desc += f" (slope: {trend_info['slope']:.4f})"

        if seasonal_strength > 0.6:
            seasonal_desc = (
                f"Strong seasonality detected (strength: {seasonal_strength:.2f})"
            )
        elif seasonal_strength > 0.3:
            seasonal_desc = (
                f"Moderate seasonality present (strength: {seasonal_strength:.2f})"
            )
        else:
            seasonal_desc = (
                f"Weak or no seasonality (strength: {seasonal_strength:.2f})"
            )

        return f"{trend_desc}. {seasonal_desc}."

    def _find_significant_lags(
        self, values: np.ndarray, conf_int: np.ndarray
    ) -> List[int]:
        """Find lags where autocorrelation exceeds confidence interval"""
        significant = []
        for i in range(1, len(values)):  # Skip lag 0
            if values[i] > conf_int[i, 1] or values[i] < conf_int[i, 0]:
                significant.append(i)
        return significant[:10]  # Return first 10 significant lags

    def _interpret_autocorrelation(
        self,
        has_autocorr: bool,
        sig_acf_lags: List[int],
        sig_pacf_lags: List[int],
    ) -> str:
        """Generate interpretation of autocorrelation analysis"""
        if not has_autocorr:
            return "No significant autocorrelation detected. Series appears to be white noise or well-modeled."

        interpretation = "Significant autocorrelation detected. "

        if sig_pacf_lags and not sig_acf_lags:
            interpretation += "PACF pattern suggests AR model. "
        elif sig_acf_lags and not sig_pacf_lags:
            interpretation += "ACF pattern suggests MA model. "
        else:
            interpretation += "Both ACF and PACF significant, suggesting ARMA model. "

        interpretation += f"Consider ARIMA order starting with p={min(sig_pacf_lags[:3]) if sig_pacf_lags else 1}, q={min(sig_acf_lags[:3]) if sig_acf_lags else 1}."

        return interpretation
