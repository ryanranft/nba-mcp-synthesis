"""
Time Series Analysis for NBA Performance Metrics.

This module provides comprehensive time series analysis capabilities including:
- Stationarity testing (ADF, KPSS)
- Seasonal decomposition
- ARIMA/SARIMA modeling
- Forecasting with confidence intervals
- Autocorrelation analysis

Designed for analyzing player/team performance over time, detecting trends,
seasonality, and making forecasts.

Integration:
- Works with data validation (Agent 4) for input validation
- Outputs compatible with training pipeline (Agent 5)
- MLflow tracking for ARIMA experiments
- Monitoring integration (Agent 2) for forecast accuracy

Author: Agent 8 Module 1
Date: October 2025
"""

import logging
import warnings
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List, Union
from itertools import product

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss, acf as sm_acf, pacf as sm_pacf
from statsmodels.tsa.seasonal import seasonal_decompose, STL
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox
import scipy.stats as stats

# MLflow integration
try:
    import mlflow
    from mcp_server.mlflow_integration import MLflowExperimentTracker

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    mlflow = None
    MLflowExperimentTracker = None

logger = logging.getLogger(__name__)


# ==============================================================================
# Data Classes
# ==============================================================================


@dataclass
class StationarityTestResult:
    """Results from stationarity test (ADF or KPSS)."""

    test_statistic: float
    p_value: float
    critical_values: Dict[str, float]
    is_stationary: bool
    test_type: str  # 'adf' or 'kpss'
    lags_used: Optional[int] = None
    observations: Optional[int] = None

    def __str__(self) -> str:
        status = "STATIONARY" if self.is_stationary else "NON-STATIONARY"
        return (
            f"{self.test_type.upper()} Test Result: {status}\n"
            f"  Test Statistic: {self.test_statistic:.4f}\n"
            f"  P-value: {self.p_value:.4f}\n"
            f"  Critical Values: {self.critical_values}"
        )


@dataclass
class DecompositionResult:
    """Results from time series decomposition."""

    observed: pd.Series
    trend: pd.Series
    seasonal: pd.Series
    residual: pd.Series
    model: str  # 'additive', 'multiplicative', or 'stl'
    period: Optional[int] = None

    def plot_components(self):
        """Create a 4-panel plot of decomposition components."""
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(4, 1, figsize=(12, 10))

        self.observed.plot(ax=axes[0], title="Observed")
        axes[0].set_ylabel("Observed")

        self.trend.plot(ax=axes[1], title="Trend")
        axes[1].set_ylabel("Trend")

        self.seasonal.plot(ax=axes[2], title="Seasonal")
        axes[2].set_ylabel("Seasonal")

        self.residual.plot(ax=axes[3], title="Residual")
        axes[3].set_ylabel("Residual")

        plt.tight_layout()
        return fig


@dataclass
class ACFResult:
    """Autocorrelation function results."""

    acf_values: np.ndarray
    confidence_interval: np.ndarray
    lags: np.ndarray


@dataclass
class ForecastResult:
    """Forecast results from ARIMA model."""

    forecast: pd.Series
    confidence_interval: pd.DataFrame  # columns: 'lower', 'upper'
    forecast_index: pd.Index
    model_summary: str


@dataclass
class ARIMAModelResult:
    """Fitted ARIMA model and results."""

    model: Any  # fitted statsmodels ARIMA model
    order: Tuple[int, int, int]
    seasonal_order: Optional[Tuple[int, int, int, int]]
    aic: float
    bic: float
    summary: str


# ==============================================================================
# TimeSeriesAnalyzer Class
# ==============================================================================


class TimeSeriesAnalyzer:
    """
    Time series analysis for NBA performance metrics.

    Supports ARIMA modeling, stationarity testing, trend analysis,
    and seasonal decomposition for player/team performance over time.

    Example:
        >>> import pandas as pd
        >>> data = pd.DataFrame({
        ...     'date': pd.date_range('2023-01-01', periods=100),
        ...     'points': np.random.poisson(25, 100)
        ... })
        >>> analyzer = TimeSeriesAnalyzer(data, target_column='points', time_column='date')
        >>> stationarity = analyzer.test_stationarity()
        >>> print(stationarity.is_stationary)
    """

    def __init__(
        self,
        data: pd.DataFrame,
        target_column: str,
        time_column: Optional[str] = None,
        freq: Optional[str] = None,
        mlflow_experiment: Optional[str] = None,
    ):
        """
        Initialize TimeSeriesAnalyzer.

        Args:
            data: DataFrame containing time series data
            target_column: Name of column containing values to analyze
            time_column: Name of column containing timestamps (if None, uses index)
            freq: Frequency of time series ('D', 'W', 'M', etc.). If None, inferred.
            mlflow_experiment: Optional MLflow experiment name for tracking

        Raises:
            ValueError: If target_column not in data
            ValueError: If time series has missing values
        """
        self.data = data.copy()
        self.target_column = target_column
        self.time_column = time_column
        self.mlflow_experiment = mlflow_experiment

        # MLflow tracker
        self.mlflow_tracker = None
        if MLFLOW_AVAILABLE and mlflow_experiment:
            try:
                self.mlflow_tracker = MLflowExperimentTracker(mlflow_experiment)
            except Exception as e:
                logger.warning(f"Failed to initialize MLflow tracker: {e}")

        # Validate target column exists
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")

        # Set up time index
        if time_column:
            if time_column not in data.columns:
                raise ValueError(f"Time column '{time_column}' not found in data")
            self.data[time_column] = pd.to_datetime(self.data[time_column])
            self.data = self.data.set_index(time_column)

        # Ensure DatetimeIndex
        if not isinstance(self.data.index, pd.DatetimeIndex):
            raise ValueError("Data must have DatetimeIndex or specify time_column")

        # Sort by time
        self.data = self.data.sort_index()

        # Set frequency
        if freq:
            self.data = self.data.asfreq(freq)
            self.freq = freq
        else:
            # Infer frequency
            inferred_freq = pd.infer_freq(self.data.index)
            if inferred_freq:
                self.freq = inferred_freq
            else:
                logger.warning(
                    "Could not infer frequency. Some methods may require explicit freq."
                )
                self.freq = None

        # Extract target series
        self.series = self.data[target_column]

        # Check for missing values
        if self.series.isna().any():
            n_missing = self.series.isna().sum()
            logger.warning(
                f"Time series has {n_missing} missing values. Consider imputation."
            )

        logger.info(
            f"TimeSeriesAnalyzer initialized: {len(self.series)} observations, freq={self.freq}"
        )

    # ==========================================================================
    # Stationarity Testing
    # ==========================================================================

    def adf_test(self, maxlag: Optional[int] = None) -> StationarityTestResult:
        """
        Augmented Dickey-Fuller test for stationarity.

        H0: Series has unit root (non-stationary)
        H1: Series is stationary

        Args:
            maxlag: Maximum number of lags to use

        Returns:
            StationarityTestResult with test results
        """
        # Drop NaN values
        series_clean = self.series.dropna()

        # Run ADF test
        result = adfuller(series_clean, maxlag=maxlag, autolag="AIC")

        test_stat, p_value, lags, nobs, critical_values, _ = result

        # Interpret: reject H0 if p < 0.05 → stationary
        is_stationary = bool(p_value < 0.05)

        return StationarityTestResult(
            test_statistic=float(test_stat),
            p_value=float(p_value),
            critical_values=critical_values,
            is_stationary=is_stationary,
            test_type="adf",
            lags_used=int(lags),
            observations=int(nobs),
        )

    def kpss_test(
        self, regression: str = "c", nlags: str = "auto"
    ) -> StationarityTestResult:
        """
        KPSS test for stationarity.

        H0: Series is stationary
        H1: Series has unit root (non-stationary)

        Note: Opposite interpretation from ADF test!

        Args:
            regression: 'c' (level stationary) or 'ct' (trend stationary)
            nlags: Number of lags, or 'auto' for automatic selection

        Returns:
            StationarityTestResult with test results
        """
        series_clean = self.series.dropna()

        # Run KPSS test
        test_stat, p_value, lags, critical_values = kpss(
            series_clean, regression=regression, nlags=nlags
        )

        # Interpret: fail to reject H0 if p >= 0.05 → stationary
        is_stationary = bool(p_value >= 0.05)

        return StationarityTestResult(
            test_statistic=float(test_stat),
            p_value=float(p_value),
            critical_values=critical_values,
            is_stationary=is_stationary,
            test_type="kpss",
            lags_used=int(lags),
            observations=len(series_clean),
        )

    def test_stationarity(
        self, method: str = "adf", **kwargs
    ) -> StationarityTestResult:
        """
        Test for stationarity using specified method.

        Args:
            method: 'adf' or 'kpss'
            **kwargs: Additional arguments for specific test

        Returns:
            StationarityTestResult

        Raises:
            ValueError: If method not recognized
        """
        if method == "adf":
            return self.adf_test(**kwargs)
        elif method == "kpss":
            return self.kpss_test(**kwargs)
        else:
            raise ValueError(f"Unknown stationarity test method: {method}")

    # ==========================================================================
    # Decomposition
    # ==========================================================================

    def decompose(
        self,
        model: str = "additive",
        period: Optional[int] = None,
        method: str = "seasonal_decompose",
    ) -> DecompositionResult:
        """
        Decompose time series into trend, seasonal, and residual components.

        Args:
            model: 'additive' or 'multiplicative'
            period: Seasonal period (if None, attempts to infer)
            method: 'seasonal_decompose' or 'stl'

        Returns:
            DecompositionResult with components

        Raises:
            ValueError: If period cannot be determined
        """
        series_clean = self.series.dropna()

        # Determine period
        if period is None:
            if self.freq:
                # Infer period from frequency
                freq_map = {
                    "D": 7,  # Daily → weekly seasonality
                    "W": 52,  # Weekly → yearly seasonality
                    "M": 12,  # Monthly → yearly seasonality
                    "Q": 4,  # Quarterly → yearly seasonality
                }
                period = freq_map.get(self.freq[0], None)

            if period is None:
                raise ValueError("Cannot infer period. Please specify explicitly.")

        # Perform decomposition
        if method == "seasonal_decompose":
            decomp = seasonal_decompose(
                series_clean, model=model, period=period, extrapolate_trend="freq"
            )

            return DecompositionResult(
                observed=decomp.observed,
                trend=decomp.trend,
                seasonal=decomp.seasonal,
                residual=decomp.resid,
                model=model,
                period=period,
            )

        elif method == "stl":
            # STL decomposition (more robust)
            stl = STL(series_clean, period=period, robust=True)
            decomp = stl.fit()

            return DecompositionResult(
                observed=series_clean,
                trend=decomp.trend,
                seasonal=decomp.seasonal,
                residual=decomp.resid,
                model="stl",
                period=period,
            )
        else:
            raise ValueError(f"Unknown decomposition method: {method}")

    def detect_trend(self) -> Dict[str, Any]:
        """
        Detect trend direction and strength.

        Returns:
            Dictionary with trend information:
                - direction: 'increasing', 'decreasing', or 'stable'
                - slope: Linear regression slope
                - r_squared: Strength of trend
                - p_value: Statistical significance
        """
        series_clean = self.series.dropna()
        x = np.arange(len(series_clean))
        y = series_clean.values

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Determine direction
        if p_value < 0.05:
            if slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "slope": slope,
            "r_squared": r_value**2,
            "p_value": p_value,
            "std_err": std_err,
        }

    # ==========================================================================
    # Autocorrelation
    # ==========================================================================

    def acf(self, nlags: int = 40, alpha: float = 0.05) -> ACFResult:
        """
        Calculate autocorrelation function.

        Args:
            nlags: Number of lags to compute
            alpha: Significance level for confidence interval

        Returns:
            ACFResult with ACF values and confidence interval
        """
        series_clean = self.series.dropna()

        acf_values, confint = sm_acf(series_clean, nlags=nlags, alpha=alpha, fft=True)

        return ACFResult(
            acf_values=acf_values,
            confidence_interval=confint,
            lags=np.arange(len(acf_values)),
        )

    def pacf(self, nlags: int = 40, alpha: float = 0.05) -> ACFResult:
        """
        Calculate partial autocorrelation function.

        Args:
            nlags: Number of lags to compute
            alpha: Significance level for confidence interval

        Returns:
            ACFResult with PACF values and confidence interval
        """
        series_clean = self.series.dropna()

        pacf_values, confint = sm_pacf(
            series_clean, nlags=nlags, alpha=alpha, method="ywm"
        )

        return ACFResult(
            acf_values=pacf_values,
            confidence_interval=confint,
            lags=np.arange(len(pacf_values)),
        )

    def ljung_box_test(self, lags: int = 10) -> Dict[str, Any]:
        """
        Ljung-Box test for autocorrelation in residuals.

        H0: No autocorrelation
        H1: Autocorrelation present

        Args:
            lags: Number of lags to test

        Returns:
            Dictionary with test results
        """
        series_clean = self.series.dropna()

        result = acorr_ljungbox(series_clean, lags=lags, return_df=True)

        return {
            "lb_stat": result["lb_stat"].tolist(),
            "lb_pvalue": result["lb_pvalue"].tolist(),
            "has_autocorrelation": bool((result["lb_pvalue"] < 0.05).any()),
        }

    # ==========================================================================
    # ARIMA Modeling
    # ==========================================================================

    def fit_arima(
        self,
        order: Tuple[int, int, int],
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,
        **kwargs,
    ) -> ARIMAModelResult:
        """
        Fit ARIMA model to time series.

        Args:
            order: (p, d, q) order of ARIMA model
                p: autoregressive order
                d: differencing order
                q: moving average order
            seasonal_order: (P, D, Q, s) seasonal order
            **kwargs: Additional arguments for ARIMA

        Returns:
            ARIMAModelResult with fitted model
        """
        series_clean = self.series.dropna()

        # Fit ARIMA model
        # Note: statsmodels requires seasonal_order to be either a tuple or explicitly omitted
        if seasonal_order is not None:
            model = ARIMA(
                series_clean, order=order, seasonal_order=seasonal_order, **kwargs
            )
        else:
            model = ARIMA(series_clean, order=order, **kwargs)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            fitted_model = model.fit()

        result = ARIMAModelResult(
            model=fitted_model,
            order=order,
            seasonal_order=seasonal_order,
            aic=fitted_model.aic,
            bic=fitted_model.bic,
            summary=str(fitted_model.summary()),
        )

        # Log to MLflow if available
        if self.mlflow_tracker:
            try:
                run = self.mlflow_tracker.start_run(run_name=f"ARIMA_{order}")
                self.mlflow_tracker.log_params(
                    run,
                    {
                        "p": order[0],
                        "d": order[1],
                        "q": order[2],
                        "seasonal": seasonal_order is not None,
                    },
                )
                self.mlflow_tracker.log_metrics(
                    run, {"aic": fitted_model.aic, "bic": fitted_model.bic}
                )
                self.mlflow_tracker.end_run(run)
            except Exception as e:
                logger.warning(f"Failed to log to MLflow: {e}")

        return result

    def auto_arima(
        self,
        seasonal: bool = False,
        m: int = 1,
        max_p: int = 5,
        max_d: int = 2,
        max_q: int = 5,
        max_P: int = 2,
        max_D: int = 1,
        max_Q: int = 2,
        information_criterion: str = "aic",
    ) -> ARIMAModelResult:
        """
        Automatically select best ARIMA model using grid search.

        Args:
            seasonal: Whether to fit seasonal ARIMA
            m: Seasonal period (if seasonal=True)
            max_p: Maximum AR order
            max_d: Maximum differencing order
            max_q: Maximum MA order
            max_P: Maximum seasonal AR order
            max_D: Maximum seasonal differencing order
            max_Q: Maximum seasonal MA order
            information_criterion: 'aic' or 'bic'

        Returns:
            ARIMAModelResult with best model
        """
        series_clean = self.series.dropna()

        # Generate parameter combinations
        p_range = range(0, max_p + 1)
        d_range = range(0, max_d + 1)
        q_range = range(0, max_q + 1)

        best_score = np.inf
        best_order = None
        best_seasonal_order = None
        best_model = None

        logger.info("Starting auto ARIMA grid search...")

        # Non-seasonal models
        for p, d, q in product(p_range, d_range, q_range):
            try:
                if seasonal:
                    # Seasonal models
                    P_range = range(0, max_P + 1)
                    D_range = range(0, max_D + 1)
                    Q_range = range(0, max_Q + 1)

                    for P, D, Q in product(P_range, D_range, Q_range):
                        try:
                            with warnings.catch_warnings():
                                warnings.filterwarnings("ignore")
                                model = ARIMA(
                                    series_clean,
                                    order=(p, d, q),
                                    seasonal_order=(P, D, Q, m),
                                )
                                fitted = model.fit()

                                score = (
                                    fitted.aic
                                    if information_criterion == "aic"
                                    else fitted.bic
                                )

                                if score < best_score:
                                    best_score = score
                                    best_order = (p, d, q)
                                    best_seasonal_order = (P, D, Q, m)
                                    best_model = fitted
                        except Exception:
                            continue
                else:
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore")
                        model = ARIMA(series_clean, order=(p, d, q))
                        fitted = model.fit()

                        score = (
                            fitted.aic if information_criterion == "aic" else fitted.bic
                        )

                        if score < best_score:
                            best_score = score
                            best_order = (p, d, q)
                            best_seasonal_order = None
                            best_model = fitted
            except Exception:
                continue

        if best_model is None:
            raise ValueError("Could not find suitable ARIMA model")

        logger.info(
            f"Best model: ARIMA{best_order}, {information_criterion}={best_score:.2f}"
        )

        result = ARIMAModelResult(
            model=best_model,
            order=best_order,
            seasonal_order=best_seasonal_order,
            aic=best_model.aic,
            bic=best_model.bic,
            summary=str(best_model.summary()),
        )

        # Log to MLflow
        if self.mlflow_tracker:
            try:
                run = self.mlflow_tracker.start_run(run_name=f"AutoARIMA_{best_order}")
                self.mlflow_tracker.log_params(
                    run,
                    {
                        "p": best_order[0],
                        "d": best_order[1],
                        "q": best_order[2],
                        "seasonal": seasonal,
                        "auto_selected": True,
                    },
                )
                self.mlflow_tracker.log_metrics(
                    run, {"aic": best_model.aic, "bic": best_model.bic}
                )
                self.mlflow_tracker.end_run(run)
            except Exception as e:
                logger.warning(f"Failed to log to MLflow: {e}")

        return result

    def forecast(
        self, model_result: ARIMAModelResult, steps: int = 10, alpha: float = 0.05
    ) -> ForecastResult:
        """
        Generate forecast from fitted ARIMA model.

        Args:
            model_result: Fitted ARIMA model result
            steps: Number of steps to forecast
            alpha: Significance level for confidence interval

        Returns:
            ForecastResult with forecasts and confidence intervals
        """
        # Generate forecast
        forecast_obj = model_result.model.get_forecast(steps=steps, alpha=alpha)
        forecast_values = forecast_obj.predicted_mean
        conf_int = forecast_obj.conf_int()

        # Create forecast index
        last_date = self.series.index[-1]
        if self.freq:
            forecast_index = pd.date_range(
                start=last_date, periods=steps + 1, freq=self.freq
            )[1:]
        else:
            # If no freq, just use integer offset
            forecast_index = pd.RangeIndex(len(self.series), len(self.series) + steps)

        # Create series and dataframe
        forecast_series = pd.Series(forecast_values.values, index=forecast_index)
        conf_df = pd.DataFrame(
            {"lower": conf_int.iloc[:, 0].values, "upper": conf_int.iloc[:, 1].values},
            index=forecast_index,
        )

        return ForecastResult(
            forecast=forecast_series,
            confidence_interval=conf_df,
            forecast_index=forecast_index,
            model_summary=model_result.summary,
        )

    # ==========================================================================
    # Utility Methods
    # ==========================================================================

    def difference(self, periods: int = 1) -> pd.Series:
        """
        Difference the time series.

        Args:
            periods: Number of periods to difference

        Returns:
            Differenced series
        """
        return self.series.diff(periods=periods)

    def make_stationary(self, max_diffs: int = 2) -> Tuple[pd.Series, List[str]]:
        """
        Automatically make series stationary through differencing.

        Args:
            max_diffs: Maximum number of differences to try

        Returns:
            Tuple of (stationary_series, transformations_applied)
        """
        series = self.series.copy()
        transformations = []

        for i in range(max_diffs):
            # Test stationarity
            adf_result = self.adf_test()

            if adf_result.is_stationary:
                logger.info(f"Series is stationary after {i} differences")
                break

            # Apply differencing
            series = series.diff().dropna()
            transformations.append(f"diff_{i+1}")
            logger.info(f"Applied differencing (iteration {i+1})")

        return series, transformations

    def validate_forecast(
        self, actual: pd.Series, predicted: pd.Series
    ) -> Dict[str, float]:
        """
        Validate forecast against actual values.

        Args:
            actual: Actual observed values
            predicted: Forecasted values

        Returns:
            Dictionary with error metrics:
                - mae: Mean Absolute Error
                - mse: Mean Squared Error
                - rmse: Root Mean Squared Error
                - mape: Mean Absolute Percentage Error
        """
        # Align series
        common_index = actual.index.intersection(predicted.index)
        actual_aligned = actual.loc[common_index]
        predicted_aligned = predicted.loc[common_index]

        # Calculate errors
        errors = actual_aligned - predicted_aligned
        abs_errors = np.abs(errors)
        squared_errors = errors**2
        percentage_errors = np.abs(errors / actual_aligned) * 100

        return {
            "mae": float(abs_errors.mean()),
            "mse": float(squared_errors.mean()),
            "rmse": float(np.sqrt(squared_errors.mean())),
            "mape": float(percentage_errors.mean()),
        }
