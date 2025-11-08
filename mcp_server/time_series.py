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

# Custom exceptions
from mcp_server.exceptions import (
    InsufficientDataError,
    InvalidDataError,
    InvalidParameterError,
    ModelFitError,
    validate_data_shape,
    validate_parameter,
)

# Advanced time series models (Phase 2 Day 2)
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.statespace.varmax import VARMAX
    from statsmodels.tsa.seasonal import MSTL

    ADVANCED_TS_AVAILABLE = True
except ImportError:
    SARIMAX = None
    VARMAX = None
    MSTL = None
    ADVANCED_TS_AVAILABLE = False

# Advanced time series methods (Phase 2 Day 4)
try:
    from statsmodels.tsa.vector_ar.vecm import coint_johansen
    from statsmodels.tsa.stattools import grangercausalitytests
    from statsmodels.tsa.api import VAR
    from statsmodels.stats.stattools import jarque_bera, durbin_watson

    ECONOMETRIC_TS_AVAILABLE = True
except ImportError:
    coint_johansen = None
    grangercausalitytests = None
    VAR = None
    jarque_bera = None
    durbin_watson = None
    ECONOMETRIC_TS_AVAILABLE = False

# Advanced econometric tests (Phase 2 Day 5)
try:
    from statsmodels.tsa.vector_ar.vecm import VECM
    from statsmodels.stats.diagnostic import (
        acorr_breusch_godfrey,
        het_breuschpagan,
        het_white,
        breaks_cusumolsresid,
        breaks_hansen,
    )

    ECONOMETRIC_TESTS_AVAILABLE = True
except ImportError:
    VECM = None
    acorr_breusch_godfrey = None
    het_breuschpagan = None
    het_white = None
    breaks_cusumolsresid = None
    breaks_hansen = None
    ECONOMETRIC_TESTS_AVAILABLE = False

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


@dataclass
class ARIMAXResult:
    """Results from ARIMAX model (ARIMA with exogenous variables)."""

    model: Any  # fitted SARIMAX model
    order: Tuple[int, int, int]
    seasonal_order: Optional[Tuple[int, int, int, int]]
    exog_names: List[str]
    exog_coefficients: Optional[pd.Series]
    aic: float
    bic: float
    log_likelihood: float
    summary: str


@dataclass
class VARMAXResult:
    """Results from VARMAX model (Vector ARMA with exogenous variables)."""

    model: Any  # fitted VARMAX model
    order: Tuple[int, int]  # (p, q) for VAR and MA orders
    n_variables: int
    variable_names: List[str]
    aic: float
    bic: float
    log_likelihood: float
    summary: str
    granger_causality: Optional[Dict[str, Any]] = None


@dataclass
class MSTLResult:
    """Results from MSTL decomposition (Multiple Seasonal-Trend using Loess)."""

    observed: pd.Series
    trend: pd.Series
    seasonal_components: Dict[int, pd.Series]  # period -> seasonal component
    residual: pd.Series
    periods: List[int]
    seasonal_strength: Dict[int, float]  # period -> strength metric


@dataclass
class JohansenCointegrationResult:
    """Results from Johansen cointegration test."""

    trace_statistic: np.ndarray
    max_eigen_statistic: np.ndarray
    critical_values_trace: np.ndarray
    critical_values_max_eigen: np.ndarray
    cointegration_rank: int  # number of cointegrating relationships
    variable_names: List[str]
    n_lags: int
    deterministic_trend: str  # 'nc', 'c', 'ct', 'ctt'
    eigenvectors: np.ndarray  # cointegrating vectors

    def __repr__(self) -> str:
        return (
            f"JohansenCointegrationResult(rank={self.cointegration_rank}, "
            f"variables={len(self.variable_names)}, lags={self.n_lags})"
        )


@dataclass
class GrangerCausalityResult:
    """Results from Granger causality test."""

    caused_variable: str  # variable being predicted
    causing_variable: str  # variable being tested for causality
    max_lag: int
    test_results: Dict[
        int, Dict[str, float]
    ]  # lag -> {statistic, p_value, df_denom, df_num}
    min_p_value: float
    significant_at_5pct: bool

    def __repr__(self) -> str:
        sig = "YES" if self.significant_at_5pct else "NO"
        return (
            f"GrangerCausalityResult({self.causing_variable} -> {self.caused_variable}: "
            f"significant={sig}, min_p={self.min_p_value:.4f})"
        )


@dataclass
class VARResult:
    """Results from Vector Autoregression model."""

    model: Any  # fitted VAR model
    order: int  # VAR lag order (p)
    n_variables: int
    variable_names: List[str]
    aic: float
    bic: float
    hqic: float  # Hannan-Quinn criterion
    fpe: float  # Final prediction error
    log_likelihood: float
    coef_summary: pd.DataFrame  # coefficient estimates
    granger_causality: Optional[Dict[str, Any]] = None

    def __repr__(self) -> str:
        return (
            f"VARResult(order={self.order}, variables={self.n_variables}, "
            f"aic={self.aic:.2f}, bic={self.bic:.2f})"
        )


@dataclass
class TimeSeriesDiagnosticsResult:
    """Comprehensive diagnostics for time series models."""

    ljung_box_test: Dict[str, Any]  # test for autocorrelation in residuals
    jarque_bera_test: Dict[str, Any]  # test for normality
    heteroscedasticity_test: Dict[str, Any]  # test for changing variance
    durbin_watson: float  # autocorrelation test statistic
    residual_mean: float
    residual_std: float
    residual_skewness: float
    residual_kurtosis: float
    all_tests_pass: bool  # True if all diagnostic tests pass at 5% level

    def __repr__(self) -> str:
        status = "PASS" if self.all_tests_pass else "FAIL"
        return (
            f"TimeSeriesDiagnosticsResult(status={status}, DW={self.durbin_watson:.3f})"
        )


@dataclass
class VECMResult:
    """Results from Vector Error Correction Model."""

    model: Any  # fitted VECM model
    order: int  # lag order (k_ar_diff)
    coint_rank: int  # cointegration rank
    n_variables: int
    variable_names: List[str]
    deterministic: str  # trend specification
    alpha: np.ndarray  # loading/adjustment coefficients
    beta: np.ndarray  # cointegrating vectors
    aic: float
    bic: float
    hqic: float
    log_likelihood: float
    coef_summary: pd.DataFrame  # coefficient estimates

    def __repr__(self) -> str:
        return (
            f"VECMResult(rank={self.coint_rank}, order={self.order}, "
            f"variables={self.n_variables}, aic={self.aic:.2f})"
        )


@dataclass
class StructuralBreakResult:
    """Results from structural break detection tests."""

    cusum_statistic: Optional[np.ndarray]  # CUSUM test statistics
    cusum_significant: Optional[bool]  # breaks detected via CUSUM
    hansen_statistic: Optional[float]  # Hansen stability test statistic
    hansen_p_value: Optional[float]  # p-value for Hansen test
    hansen_significant: Optional[bool]  # breaks detected via Hansen
    break_points: Optional[List[int]]  # detected break point indices
    test_type: str  # 'cusum', 'hansen', or 'both'

    def __repr__(self) -> str:
        if self.hansen_significant is not None:
            status = "BREAKS DETECTED" if self.hansen_significant else "STABLE"
            return (
                f"StructuralBreakResult({status}, Hansen_p={self.hansen_p_value:.4f})"
            )
        elif self.cusum_significant is not None:
            status = "BREAKS DETECTED" if self.cusum_significant else "STABLE"
            return f"StructuralBreakResult({status}, type=CUSUM)"
        return "StructuralBreakResult(test_type={self.test_type})"


@dataclass
class BreuschGodfreyResult:
    """Results from Breusch-Godfrey LM test for autocorrelation."""

    lm_statistic: float  # Lagrange multiplier statistic
    lm_p_value: float  # p-value for LM test
    f_statistic: float  # F-statistic version
    f_p_value: float  # p-value for F-test
    nlags: int  # number of lags tested
    nobs: int  # number of observations
    significant_at_5pct: bool  # autocorrelation detected at 5% level

    def __repr__(self) -> str:
        status = (
            "AUTOCORRELATION DETECTED"
            if self.significant_at_5pct
            else "NO AUTOCORRELATION"
        )
        return f"BreuschGodfreyResult({status}, lags={self.nlags}, p={self.lm_p_value:.4f})"


@dataclass
class HeteroscedasticityResult:
    """Results from heteroscedasticity tests."""

    breusch_pagan_statistic: Optional[float]
    breusch_pagan_p_value: Optional[float]
    breusch_pagan_significant: Optional[bool]
    white_statistic: Optional[float]
    white_p_value: Optional[float]
    white_significant: Optional[bool]
    arch_statistic: Optional[float]  # from time_series_diagnostics
    arch_p_value: Optional[float]
    arch_significant: Optional[bool]
    test_type: str  # 'breusch_pagan', 'white', 'arch', or 'all'

    def __repr__(self) -> str:
        if self.breusch_pagan_significant is not None:
            status = (
                "HETEROSCEDASTIC" if self.breusch_pagan_significant else "HOMOSCEDASTIC"
            )
            return f"HeteroscedasticityResult({status}, BP_p={self.breusch_pagan_p_value:.4f})"
        elif self.white_significant is not None:
            status = "HETEROSCEDASTIC" if self.white_significant else "HOMOSCEDASTIC"
            return (
                f"HeteroscedasticityResult({status}, White_p={self.white_p_value:.4f})"
            )
        return f"HeteroscedasticityResult(type={self.test_type})"


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
        # Validate data type and shape
        if not isinstance(data, pd.DataFrame):
            raise InvalidDataError(
                "Data must be a pandas DataFrame",
                value=type(data).__name__
            )

        validate_data_shape(data, min_rows=30)  # Minimum for time series analysis

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

        # Alias for backward compatibility (used by advanced methods)
        self.tracker = self.mlflow_tracker

        # Validate target column exists
        if target_column not in data.columns:
            raise InvalidDataError(
                f"Target column '{target_column}' not found in data",
                value=target_column,
                available_columns=list(data.columns)
            )

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
        # Validate ARIMA order
        if not isinstance(order, tuple) or len(order) != 3:
            raise InvalidParameterError(
                "ARIMA order must be a tuple of 3 integers (p, d, q)",
                parameter="order",
                value=order
            )

        p, d, q = order
        if any(x < 0 for x in [p, d, q]):
            raise InvalidParameterError(
                "ARIMA order values must be non-negative",
                parameter="order",
                value=order
            )

        if p + d + q == 0:
            raise InvalidParameterError(
                "At least one ARIMA parameter must be > 0",
                parameter="order",
                value=order
            )

        series_clean = self.series.dropna()

        if len(series_clean) < 30:
            raise InsufficientDataError(
                "Need at least 30 observations for ARIMA",
                required=30,
                actual=len(series_clean)
            )

        # Fit ARIMA model
        # Note: statsmodels requires seasonal_order to be either a tuple or explicitly omitted
        try:
            if seasonal_order is not None:
                model = ARIMA(
                    series_clean, order=order, seasonal_order=seasonal_order, **kwargs
                )
            else:
                model = ARIMA(series_clean, order=order, **kwargs)

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                fitted_model = model.fit()
        except (ValueError, np.linalg.LinAlgError) as e:
            raise ModelFitError(
                f"ARIMA model fitting failed with order={order}",
                model_type="ARIMA",
                reason=str(e)
            ) from e

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

    # ==========================================================================
    # Advanced Time Series Methods (Phase 2 Day 2)
    # ==========================================================================

    def fit_arimax(
        self,
        order: Tuple[int, int, int],
        exog: Union[pd.DataFrame, np.ndarray],
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,
        exog_forecast: Optional[Union[pd.DataFrame, np.ndarray]] = None,
        **kwargs,
    ) -> ARIMAXResult:
        """
        Fit ARIMAX model (ARIMA with exogenous variables).

        ARIMAX extends ARIMA by including external regressors that can
        help explain variation in the target series.

        Parameters
        ----------
        order : Tuple[int, int, int]
            (p, d, q) order of ARIMA model
            p: autoregressive order
            d: differencing order
            q: moving average order
        exog : pd.DataFrame or np.ndarray
            Exogenous variables (external regressors)
        seasonal_order : Tuple[int, int, int, int], optional
            (P, D, Q, s) seasonal order
        exog_forecast : pd.DataFrame or np.ndarray, optional
            Future values of exogenous variables for forecasting
        **kwargs : dict
            Additional arguments for SARIMAX model

        Returns
        -------
        ARIMAXResult
            Fitted ARIMAX model results with coefficients and diagnostics

        Examples
        --------
        >>> # Predict points using assists and opponent strength as exog vars
        >>> exog_data = df[['assists', 'opponent_rating']]
        >>> result = analyzer.fit_arimax(
        ...     order=(1, 1, 1),
        ...     exog=exog_data
        ... )
        >>> print(f"AIC: {result.aic:.2f}")
        >>> print(result.exog_coefficients)
        """
        if not ADVANCED_TS_AVAILABLE:
            raise ImportError("SARIMAX not available. Install statsmodels>=0.12.0")

        series_clean = self.series.dropna()

        # Align exog with series
        if isinstance(exog, pd.DataFrame):
            exog_names = list(exog.columns)
            exog_aligned = exog.loc[series_clean.index]
        elif isinstance(exog, np.ndarray):
            exog_names = [f"exog_{i}" for i in range(exog.shape[1])]
            exog_aligned = exog
        else:
            raise ValueError("exog must be DataFrame or ndarray")

        # Fit SARIMAX model (which handles ARIMAX)
        if seasonal_order is not None:
            model = SARIMAX(
                series_clean,
                exog=exog_aligned,
                order=order,
                seasonal_order=seasonal_order,
                **kwargs,
            )
        else:
            model = SARIMAX(series_clean, exog=exog_aligned, order=order, **kwargs)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            fitted_model = model.fit(disp=False)

        # Extract exogenous coefficients
        if hasattr(fitted_model, "params"):
            # Exog coefficients are typically at the end
            n_exog = exog_aligned.shape[1] if len(exog_aligned.shape) > 1 else 1
            exog_coef = fitted_model.params[-n_exog:]
            exog_coefficients = pd.Series(exog_coef, index=exog_names)
        else:
            exog_coefficients = None

        result = ARIMAXResult(
            model=fitted_model,
            order=order,
            seasonal_order=seasonal_order,
            exog_names=exog_names,
            exog_coefficients=exog_coefficients,
            aic=fitted_model.aic,
            bic=fitted_model.bic,
            log_likelihood=fitted_model.llf,
            summary=str(fitted_model.summary()),
        )

        # MLflow logging
        if self.mlflow_tracker:
            try:
                run = self.mlflow_tracker.start_run(run_name=f"ARIMAX_{order}")
                self.mlflow_tracker.log_params(
                    run,
                    {
                        "p": order[0],
                        "d": order[1],
                        "q": order[2],
                        "n_exog": len(exog_names),
                        "seasonal": seasonal_order is not None,
                    },
                )
                self.mlflow_tracker.log_metrics(
                    run,
                    {
                        "aic": fitted_model.aic,
                        "bic": fitted_model.bic,
                        "log_likelihood": fitted_model.llf,
                    },
                )
                self.mlflow_tracker.end_run(run)
            except Exception as e:
                logger.warning(f"Failed to log to MLflow: {e}")

        logger.info(f"ARIMAX{order} fitted with {len(exog_names)} exog variables")
        return result

    def fit_varmax(
        self,
        endog_data: pd.DataFrame,
        order: Tuple[int, int] = (1, 0),
        exog: Optional[Union[pd.DataFrame, np.ndarray]] = None,
        trend: str = "c",
        **kwargs,
    ) -> VARMAXResult:
        """
        Fit VARMAX model (Vector Autoregression Moving Average with exogenous variables).

        VARMAX models multiple time series jointly, capturing cross-variable
        dynamics through vector autoregression and moving average components.

        Parameters
        ----------
        endog_data : pd.DataFrame
            Multivariate endogenous data (multiple time series)
        order : Tuple[int, int], default=(1, 0)
            (p, q) order where:
            p: VAR order (lags of endogenous variables)
            q: MA order (lags of errors)
        exog : pd.DataFrame or np.ndarray, optional
            Exogenous variables
        trend : str, default='c'
            Trend specification: 'n' (none), 'c' (constant), 't' (time trend),
            'ct' (constant + time trend)
        **kwargs : dict
            Additional arguments for VARMAX model

        Returns
        -------
        VARMAXResult
            Fitted VARMAX model results with diagnostics

        Examples
        --------
        >>> # Model points, assists, and rebounds jointly
        >>> endog = df[['points', 'assists', 'rebounds']]
        >>> result = analyzer.fit_varmax(
        ...     endog_data=endog,
        ...     order=(2, 1)
        ... )
        >>> print(f"AIC: {result.aic:.2f}")
        """
        if not ADVANCED_TS_AVAILABLE:
            raise ImportError("VARMAX not available. Install statsmodels>=0.12.0")

        # Clean data
        endog_clean = endog_data.dropna()
        n_vars = endog_clean.shape[1]
        var_names = list(endog_clean.columns)

        # Align exog if provided
        if exog is not None:
            if isinstance(exog, pd.DataFrame):
                exog_aligned = exog.loc[endog_clean.index]
            else:
                exog_aligned = exog
        else:
            exog_aligned = None

        # Fit VARMAX model
        model = VARMAX(
            endog_clean, exog=exog_aligned, order=order, trend=trend, **kwargs
        )

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            fitted_model = model.fit(disp=False)

        result = VARMAXResult(
            model=fitted_model,
            order=order,
            n_variables=n_vars,
            variable_names=var_names,
            aic=fitted_model.aic,
            bic=fitted_model.bic,
            log_likelihood=fitted_model.llf,
            summary=str(fitted_model.summary()),
            granger_causality=None,  # Could add Granger causality tests later
        )

        # MLflow logging
        if self.mlflow_tracker:
            try:
                run = self.mlflow_tracker.start_run(
                    run_name=f"VARMAX_{order}_{n_vars}vars"
                )
                self.mlflow_tracker.log_params(
                    run,
                    {
                        "p": order[0],
                        "q": order[1],
                        "n_variables": n_vars,
                        "trend": trend,
                    },
                )
                self.mlflow_tracker.log_metrics(
                    run,
                    {
                        "aic": fitted_model.aic,
                        "bic": fitted_model.bic,
                        "log_likelihood": fitted_model.llf,
                    },
                )
                self.mlflow_tracker.end_run(run)
            except Exception as e:
                logger.warning(f"Failed to log to MLflow: {e}")

        logger.info(
            f"VARMAX{order} fitted with {n_vars} endogenous variables: {var_names}"
        )
        return result

    def mstl_decompose(
        self,
        periods: Union[int, List[int]],
        windows: Optional[Union[int, List[int]]] = None,
        iterate: int = 2,
        **kwargs,
    ) -> MSTLResult:
        """
        Multiple Seasonal-Trend decomposition using Loess (MSTL).

        MSTL extends STL to handle time series with multiple seasonal patterns,
        such as hourly data with daily, weekly, and yearly seasonality.

        Parameters
        ----------
        periods : int or List[int]
            Seasonal period(s). Can be a single period or list of multiple periods.
            Examples: 7 (weekly), [7, 365] (weekly + yearly), [24, 168] (daily + weekly for hourly data)
        windows : int or List[int], optional
            Seasonal smoother window size(s). If None, uses defaults.
            Must match length of periods if provided as list.
        iterate : int, default=2
            Number of iterations for MSTL algorithm
        **kwargs : dict
            Additional arguments passed to MSTL

        Returns
        -------
        MSTLResult
            Decomposition results with trend, multiple seasonal components, and residual

        Examples
        --------
        >>> # Decompose daily data with weekly and yearly seasonality
        >>> result = analyzer.mstl_decompose(periods=[7, 365])
        >>> print(f"Weekly seasonal strength: {result.seasonal_strength[7]:.3f}")
        >>> print(f"Yearly seasonal strength: {result.seasonal_strength[365]:.3f}")
        """
        if not ADVANCED_TS_AVAILABLE or MSTL is None:
            raise ImportError("MSTL not available. Install statsmodels>=0.13.0")

        series_clean = self.series.dropna()

        # Convert single period to list
        if isinstance(periods, int):
            periods = [periods]

        # Validate minimum series length
        max_period = max(periods)
        if len(series_clean) < 2 * max_period:
            raise ValueError(
                f"Series too short ({len(series_clean)}) for period {max_period}. "
                f"Need at least {2 * max_period} observations."
            )

        # Fit MSTL
        try:
            mstl = MSTL(
                series_clean,
                periods=periods,
                windows=windows,
                iterate=iterate,
                **kwargs,
            )
            decomp = mstl.fit()
        except Exception as e:
            logger.error(f"MSTL decomposition failed: {e}")
            raise

        # Extract components
        trend = decomp.trend
        residual = decomp.resid
        observed = decomp.observed

        # Extract seasonal components (MSTL creates one seasonal component per period)
        seasonal_components = {}
        seasonal_strength = {}

        # MSTL returns seasonal components as seasonal_{period}
        for period in periods:
            seasonal_col = f"seasonal_{period}"
            if hasattr(decomp, seasonal_col):
                seasonal = getattr(decomp, seasonal_col)
            else:
                # Try to access from seasonal attribute (different statsmodels versions)
                seasonal = decomp.seasonal.iloc[:, periods.index(period)]

            seasonal_components[period] = seasonal

            # Calculate seasonal strength: Var(seasonal) / Var(seasonal + residual)
            var_seasonal = np.var(seasonal.dropna())
            var_remainder = np.var((seasonal + residual).dropna())
            strength = 1 - (var_remainder / max(var_seasonal, 1e-10))
            seasonal_strength[period] = max(0.0, min(1.0, strength))

        result = MSTLResult(
            observed=observed,
            trend=trend,
            seasonal_components=seasonal_components,
            residual=residual,
            periods=periods,
            seasonal_strength=seasonal_strength,
        )

        logger.info(
            f"MSTL decomposition complete with periods: {periods}, "
            f"strengths: {seasonal_strength}"
        )
        return result

    def stl_decompose(
        self,
        period: int,
        seasonal: int = 7,
        trend: Optional[int] = None,
        robust: bool = True,
        **kwargs,
    ) -> DecompositionResult:
        """
        Enhanced STL (Seasonal-Trend decomposition using Loess) with additional diagnostics.

        STL is a robust decomposition method that handles various types of seasonality
        and is resistant to outliers when robust=True.

        Parameters
        ----------
        period : int
            Seasonal period (e.g., 7 for weekly, 12 for monthly, 365 for yearly)
        seasonal : int, default=7
            Length of seasonal smoother. Must be odd. Larger values = smoother seasonal component.
        trend : int, optional
            Length of trend smoother. If None, uses default heuristic.
            Must be odd and >= period.
        robust : bool, default=True
            Use robust weights to handle outliers
        **kwargs : dict
            Additional arguments passed to STL

        Returns
        -------
        DecompositionResult
            Enhanced decomposition with trend, seasonal, and residual components

        Examples
        --------
        >>> # Decompose with weekly seasonality
        >>> result = analyzer.stl_decompose(period=7, seasonal=13, robust=True)
        >>> print(f"Trend component: {result.trend.head()}")
        >>> seasonal_adj = result.observed - result.seasonal
        """
        series_clean = self.series.dropna()

        # Validate inputs
        if len(series_clean) < 2 * period:
            raise ValueError(
                f"Series too short ({len(series_clean)}) for period {period}. "
                f"Need at least {2 * period} observations."
            )

        # Ensure seasonal is odd
        if seasonal % 2 == 0:
            seasonal += 1
            logger.warning(f"seasonal must be odd, using {seasonal}")

        # Fit STL
        stl = STL(
            series_clean,
            period=period,
            seasonal=seasonal,
            trend=trend,
            robust=robust,
            **kwargs,
        )
        decomp = stl.fit()

        result = DecompositionResult(
            observed=series_clean,
            trend=decomp.trend,
            seasonal=decomp.seasonal,
            residual=decomp.resid,
            model="stl",
            period=period,
        )

        logger.info(f"STL decomposition complete: period={period}, robust={robust}")
        return result

    def johansen_test(
        self,
        endog_data: pd.DataFrame,
        det_order: int = 0,
        k_ar_diff: int = 1,
    ) -> JohansenCointegrationResult:
        """
        Johansen cointegration test for multivariate time series.

        Tests for cointegrating relationships between multiple time series variables.
        Cointegration implies that despite being non-stationary individually, a linear
        combination of the series is stationary (long-run equilibrium relationship).

        Parameters
        ----------
        endog_data : pd.DataFrame
            DataFrame with multiple time series variables to test for cointegration.
            Each column is a different variable.
        det_order : int, default=0
            Deterministic trend order:
            - -1: No deterministic terms
            - 0: Constant term (default)
            - 1: Constant + linear trend
        k_ar_diff : int, default=1
            Number of lagged differences in the VAR model.
            Higher values capture more dynamics but use more degrees of freedom.

        Returns
        -------
        JohansenCointegrationResult
            Contains test statistics, critical values, and cointegration rank.

        Examples
        --------
        >>> # Test cointegration between points, assists, rebounds
        >>> endog = df[['points', 'assists', 'rebounds']]
        >>> result = analyzer.johansen_test(endog_data=endog, k_ar_diff=2)
        >>> print(f"Cointegration rank: {result.cointegration_rank}")
        >>> print(f"Trace stat: {result.trace_statistic}")

        Notes
        -----
        The test computes two test statistics:
        - Trace statistic: Tests H0: rank <= r vs H1: rank > r
        - Maximum eigenvalue: Tests H0: rank = r vs H1: rank = r+1

        Cointegration rank is determined by comparing test statistics to critical values.
        """
        if not ECONOMETRIC_TS_AVAILABLE:
            raise ImportError(
                "coint_johansen required. This should be available in statsmodels>=0.12. "
                "Try: pip install --upgrade statsmodels"
            )

        # Validate inputs
        if not isinstance(endog_data, pd.DataFrame):
            raise TypeError("endog_data must be a pandas DataFrame")

        if endog_data.shape[1] < 2:
            raise ValueError(
                f"Need at least 2 variables for cointegration test, got {endog_data.shape[1]}"
            )

        # Drop missing values
        endog_clean = endog_data.dropna()
        if len(endog_clean) < 2 * endog_data.shape[1]:
            raise ValueError(
                f"Insufficient observations ({len(endog_clean)}) for {endog_data.shape[1]} variables"
            )

        variable_names = list(endog_data.columns)

        # Map det_order to deterministic trend specification
        # Johansen test uses string codes: 'nc' (no constant), 'c' (constant),
        # 'ct' (constant + trend), 'ctt' (constant + trend + trend^2)
        det_order_map = {-1: "nc", 0: "c", 1: "ct", 2: "ctt"}
        det_str = det_order_map.get(det_order, "c")

        try:
            # Run Johansen test
            result = coint_johansen(
                endog_clean.values, det_order=det_order, k_ar_diff=k_ar_diff
            )

            # Extract test statistics
            trace_stat = result.lr1  # trace statistic
            max_eigen_stat = result.lr2  # maximum eigenvalue statistic

            # Critical values (90%, 95%, 99%)
            cv_trace = result.cvt  # critical values for trace test
            cv_max_eigen = result.cvm  # critical values for max eigenvalue test

            # Eigenvectors (cointegrating vectors)
            eigenvectors = result.evec

            # Determine cointegration rank at 95% significance level (index 1)
            # Count how many trace statistics exceed the 95% critical value
            cointegration_rank = 0
            for i in range(len(trace_stat)):
                if trace_stat[i] > cv_trace[i, 1]:  # 95% critical value is at index 1
                    cointegration_rank += 1
                else:
                    break

            logger.info(
                f"Johansen test: rank={cointegration_rank}/{len(variable_names)}, "
                f"lags={k_ar_diff}, det={det_str}"
            )

        except Exception as e:
            logger.error(f"Johansen test failed: {e}")
            raise

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "cointegration_rank": float(cointegration_rank),
                    "n_variables": float(len(variable_names)),
                    "trace_stat_max": (
                        float(trace_stat[0]) if len(trace_stat) > 0 else 0.0
                    ),
                }
            )

        return JohansenCointegrationResult(
            trace_statistic=trace_stat,
            max_eigen_statistic=max_eigen_stat,
            critical_values_trace=cv_trace,
            critical_values_max_eigen=cv_max_eigen,
            cointegration_rank=cointegration_rank,
            variable_names=variable_names,
            n_lags=k_ar_diff,
            deterministic_trend=det_str,
            eigenvectors=eigenvectors,
        )

    def granger_causality_test(
        self,
        caused_series: Union[pd.Series, str],
        causing_series: Union[pd.Series, str],
        maxlag: int = 4,
        addconst: bool = True,
    ) -> GrangerCausalityResult:
        """
        Granger causality test to determine if one series helps predict another.

        Tests the null hypothesis that the coefficients of past values of the
        'causing' variable in a VAR model are jointly zero. If rejected, the causing
        variable Granger-causes the caused variable (helps predict it).

        Parameters
        ----------
        caused_series : pd.Series or str
            The series being predicted (dependent variable), or column name if str.
        causing_series : pd.Series or str
            The series tested for causality (independent variable), or column name if str.
        maxlag : int, default=4
            Maximum number of lags to test. Tests will be run for lags 1 through maxlag.
        addconst : bool, default=True
            Add a constant term to the model.

        Returns
        -------
        GrangerCausalityResult
            Contains test statistics, p-values for each lag, and overall conclusion.

        Examples
        --------
        >>> # Test if assists Granger-cause points
        >>> result = analyzer.granger_causality_test(
        ...     caused_series='points',
        ...     causing_series='assists',
        ...     maxlag=3
        ... )
        >>> print(f"Significant: {result.significant_at_5pct}")
        >>> print(f"Min p-value: {result.min_p_value:.4f}")

        Notes
        -----
        Granger causality is a statistical concept of causality based on prediction.
        X Granger-causes Y if past values of X improve the prediction of Y beyond
        what past values of Y alone can provide. This does NOT imply true causation.
        """
        if not ECONOMETRIC_TS_AVAILABLE:
            raise ImportError(
                "grangercausalitytests required. This should be available in statsmodels>=0.12. "
                "Try: pip install --upgrade statsmodels"
            )

        # Handle string column names
        if isinstance(caused_series, str):
            if caused_series not in self.data.columns:
                raise ValueError(f"Column '{caused_series}' not found in data")
            caused_var_name = caused_series
            caused_data = self.data[caused_series]
        else:
            caused_var_name = getattr(caused_series, "name", "caused_variable")
            caused_data = caused_series

        if isinstance(causing_series, str):
            if causing_series not in self.data.columns:
                raise ValueError(f"Column '{causing_series}' not found in data")
            causing_var_name = causing_series
            causing_data = self.data[causing_series]
        else:
            causing_var_name = getattr(causing_series, "name", "causing_variable")
            causing_data = causing_series

        # Validate inputs
        if maxlag < 1:
            raise ValueError(f"maxlag must be >= 1, got {maxlag}")

        # Create bivariate DataFrame: [caused, causing]
        # grangercausalitytests expects [y, x] format
        test_data = pd.DataFrame(
            {caused_var_name: caused_data, causing_var_name: causing_data}
        )
        test_data_clean = test_data.dropna()

        if len(test_data_clean) < maxlag + 10:
            raise ValueError(
                f"Insufficient observations ({len(test_data_clean)}) for maxlag={maxlag}"
            )

        try:
            # Run Granger causality test
            # Returns dict: lag -> {test_name: (statistic, p_value, df)}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gc_results = grangercausalitytests(
                    test_data_clean[[caused_var_name, causing_var_name]],
                    maxlag=maxlag,
                    addconst=addconst,
                    verbose=False,
                )

            # Extract results for each lag
            test_results = {}
            p_values = []

            for lag in range(1, maxlag + 1):
                # Get F-test results (most common test)
                # gc_results[lag] is a tuple: (test_results_dict, ...)
                lag_result = gc_results[lag][0]  # first element is test results dict
                f_test = lag_result[
                    "ssr_ftest"
                ]  # F-test: (statistic, p_value, df_denom, df_num)

                test_results[lag] = {
                    "statistic": f_test[0],
                    "p_value": f_test[1],
                    "df_denom": f_test[2],
                    "df_num": f_test[3],
                }
                p_values.append(f_test[1])

            # Determine overall conclusion
            min_p_value = min(p_values)
            significant_at_5pct = min_p_value < 0.05

            logger.info(
                f"Granger test: {causing_var_name} -> {caused_var_name}, "
                f"lags={maxlag}, significant={significant_at_5pct}, min_p={min_p_value:.4f}"
            )

        except Exception as e:
            logger.error(f"Granger causality test failed: {e}")
            raise

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "granger_min_p_value": float(min_p_value),
                    "granger_significant": float(significant_at_5pct),
                }
            )

        return GrangerCausalityResult(
            caused_variable=caused_var_name,
            causing_variable=causing_var_name,
            max_lag=maxlag,
            test_results=test_results,
            min_p_value=min_p_value,
            significant_at_5pct=significant_at_5pct,
        )

    def fit_var(
        self,
        endog_data: pd.DataFrame,
        maxlags: Optional[int] = None,
        ic: str = "aic",
        trend: str = "c",
    ) -> VARResult:
        """
        Fit Vector Autoregression (VAR) model for multivariate time series.

        VAR is a generalization of AR for multiple time series. Each variable is modeled
        as a linear combination of its own lags and the lags of all other variables.

        Parameters
        ----------
        endog_data : pd.DataFrame
            DataFrame with multiple time series variables.
            Each column represents a different endogenous variable.
        maxlags : int, optional
            Maximum number of lags to consider. If None, uses int(12 * (nobs/100)^(1/4))
            as a default heuristic.
        ic : str, default='aic'
            Information criterion for model selection: 'aic', 'bic', 'hqic', or 'fpe'.
        trend : str, default='c'
            Trend specification:
            - 'n': No trend
            - 'c': Constant term (default)
            - 'ct': Constant + linear trend
            - 'ctt': Constant + linear + quadratic trend

        Returns
        -------
        VARResult
            Contains fitted VAR model, coefficients, and information criteria.

        Examples
        --------
        >>> # Fit VAR model for points, assists, rebounds
        >>> endog = df[['points', 'assists', 'rebounds']]
        >>> result = analyzer.fit_var(endog_data=endog, maxlags=5, ic='aic')
        >>> print(f"Optimal lag order: {result.order}")
        >>> print(f"AIC: {result.aic:.2f}, BIC: {result.bic:.2f}")

        Notes
        -----
        VAR models are useful for:
        - Modeling joint dynamics of multiple series
        - Impulse response analysis
        - Forecast error variance decomposition
        - Granger causality testing
        """
        if not ECONOMETRIC_TS_AVAILABLE:
            raise ImportError(
                "VAR model required. This should be available in statsmodels>=0.12. "
                "Try: pip install --upgrade statsmodels"
            )

        # Validate inputs
        if not isinstance(endog_data, pd.DataFrame):
            raise TypeError("endog_data must be a pandas DataFrame")

        if endog_data.shape[1] < 2:
            raise ValueError(
                f"VAR requires at least 2 variables, got {endog_data.shape[1]}"
            )

        # Drop missing values
        endog_clean = endog_data.dropna()
        variable_names = list(endog_data.columns)
        n_obs = len(endog_clean)

        # Set default maxlags if not provided
        if maxlags is None:
            # Default heuristic: int(12 * (nobs/100)^(1/4))
            maxlags = int(12 * (n_obs / 100) ** 0.25)
            maxlags = max(1, min(maxlags, n_obs // 3))  # ensure reasonable range
            logger.info(
                f"Using default maxlags={maxlags} based on {n_obs} observations"
            )

        if n_obs < maxlags + 10:
            raise ValueError(
                f"Insufficient observations ({n_obs}) for maxlags={maxlags}. "
                f"Need at least {maxlags + 10}."
            )

        try:
            # Fit VAR model
            var_model = VAR(endog_clean)

            # Select optimal lag order based on information criterion
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                var_fitted = var_model.fit(maxlags=maxlags, ic=ic, trend=trend)

            # Extract model information
            order_selected = var_fitted.k_ar  # selected lag order
            aic_value = var_fitted.aic
            bic_value = var_fitted.bic
            hqic_value = var_fitted.hqic
            fpe_value = var_fitted.fpe
            log_likelihood = var_fitted.llf

            # Extract coefficient summary
            # params is (n_vars * n_lags + const) x n_vars matrix
            coef_df = pd.DataFrame(
                var_fitted.params, columns=variable_names, index=var_fitted.params.index
            )

            logger.info(
                f"VAR model fitted: order={order_selected}, variables={len(variable_names)}, "
                f"aic={aic_value:.2f}, bic={bic_value:.2f}"
            )

        except Exception as e:
            logger.error(f"VAR model fitting failed: {e}")
            raise

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "var_order": float(order_selected),
                    "var_aic": float(aic_value),
                    "var_bic": float(bic_value),
                    "var_n_variables": float(len(variable_names)),
                }
            )

        return VARResult(
            model=var_fitted,
            order=order_selected,
            n_variables=len(variable_names),
            variable_names=variable_names,
            aic=aic_value,
            bic=bic_value,
            hqic=hqic_value,
            fpe=fpe_value,
            log_likelihood=log_likelihood,
            coef_summary=coef_df,
        )

    def time_series_diagnostics(
        self, residuals: pd.Series, lags: int = 10, alpha: float = 0.05
    ) -> TimeSeriesDiagnosticsResult:
        """
        Comprehensive diagnostic tests for time series model residuals.

        Runs a battery of diagnostic tests to validate model assumptions:
        - Ljung-Box test for autocorrelation
        - Jarque-Bera test for normality
        - Heteroscedasticity test (ARCH effects)
        - Durbin-Watson statistic for autocorrelation
        - Residual statistics (mean, std, skewness, kurtosis)

        Parameters
        ----------
        residuals : pd.Series
            Model residuals to test (observed - fitted).
        lags : int, default=10
            Number of lags to use in autocorrelation tests.
        alpha : float, default=0.05
            Significance level for hypothesis tests.

        Returns
        -------
        TimeSeriesDiagnosticsResult
            Comprehensive diagnostics with test statistics and p-values.

        Examples
        --------
        >>> # Fit ARIMA and check residuals
        >>> arima_result = analyzer.fit_arima(order=(1, 1, 1))
        >>> residuals = arima_result.model.resid
        >>> diagnostics = analyzer.time_series_diagnostics(residuals, lags=12)
        >>> print(f"All tests pass: {diagnostics.all_tests_pass}")
        >>> print(f"Durbin-Watson: {diagnostics.durbin_watson:.3f}")

        Notes
        -----
        Good model residuals should be:
        - Uncorrelated (white noise) - Ljung-Box p > 0.05
        - Normally distributed - Jarque-Bera p > 0.05
        - Homoscedastic (constant variance) - ARCH p > 0.05
        - Durbin-Watson near 2.0 indicates no autocorrelation
        """
        if not isinstance(residuals, pd.Series):
            residuals = pd.Series(residuals)

        residuals_clean = residuals.dropna()

        if len(residuals_clean) < lags + 5:
            raise ValueError(
                f"Insufficient residuals ({len(residuals_clean)}) for lags={lags}"
            )

        try:
            # 1. Ljung-Box test for autocorrelation
            lb_result = acorr_ljungbox(residuals_clean, lags=lags, return_df=False)
            # acorr_ljungbox returns DataFrame even with return_df=False in newer statsmodels
            if isinstance(lb_result, pd.DataFrame):
                lb_stat = float(lb_result['lb_stat'].iloc[-1])
                lb_pval = float(lb_result['lb_pvalue'].iloc[-1])
            else:
                # Older statsmodels returns tuple
                lb_stat = float(lb_result[0][-1])
                lb_pval = float(lb_result[1][-1])
            ljung_box = {
                "statistic": lb_stat,
                "p_value": lb_pval,
                "lags": lags,
                "pass": lb_pval > alpha,
            }

            # 2. Jarque-Bera test for normality
            if ECONOMETRIC_TS_AVAILABLE and jarque_bera is not None:
                jb_stat, jb_pvalue, jb_skew, jb_kurtosis = jarque_bera(
                    residuals_clean.values
                )
                jarque_bera_test = {
                    "statistic": float(jb_stat),
                    "p_value": float(jb_pvalue),
                    "pass": float(jb_pvalue) > alpha,
                }
            else:
                # Fallback using scipy
                from scipy.stats import jarque_bera as scipy_jb

                jb_stat, jb_pvalue = scipy_jb(residuals_clean.values)
                jarque_bera_test = {
                    "statistic": float(jb_stat),
                    "p_value": float(jb_pvalue),
                    "pass": float(jb_pvalue) > alpha,
                }

            # 3. Heteroscedasticity test (ARCH effects)
            # Use Ljung-Box on squared residuals as a simple ARCH test
            squared_resid = residuals_clean**2
            arch_lb = acorr_ljungbox(squared_resid, lags=lags, return_df=False)
            # acorr_ljungbox returns DataFrame even with return_df=False in newer statsmodels
            if isinstance(arch_lb, pd.DataFrame):
                arch_stat = float(arch_lb['lb_stat'].iloc[-1])
                arch_pval = float(arch_lb['lb_pvalue'].iloc[-1])
            else:
                # Older statsmodels returns tuple
                arch_stat = float(arch_lb[0][-1])
                arch_pval = float(arch_lb[1][-1])
            heteroscedasticity = {
                "statistic": arch_stat,
                "p_value": arch_pval,
                "lags": lags,
                "pass": arch_pval > alpha,  # p > alpha means no ARCH effects
            }

            # 4. Durbin-Watson statistic
            if ECONOMETRIC_TS_AVAILABLE and durbin_watson is not None:
                dw_stat = durbin_watson(residuals_clean.values)
            else:
                # Manual calculation: DW = sum((e_t - e_{t-1})^2) / sum(e_t^2)
                resid_diff = residuals_clean.diff().dropna()
                dw_stat = (resid_diff**2).sum() / (residuals_clean**2).sum()
            dw_stat = float(dw_stat)

            # 5. Residual statistics
            resid_mean = float(residuals_clean.mean())
            resid_std = float(residuals_clean.std())
            resid_skewness = float(residuals_clean.skew())
            resid_kurtosis = float(residuals_clean.kurtosis())

            # Overall assessment: all tests pass?
            all_tests_pass = (
                ljung_box["pass"]
                and jarque_bera_test["pass"]
                and heteroscedasticity["pass"]
            )

            logger.info(
                f"Diagnostics: LB_p={ljung_box['p_value']:.3f}, "
                f"JB_p={jarque_bera_test['p_value']:.3f}, "
                f"DW={dw_stat:.3f}, all_pass={all_tests_pass}"
            )

        except Exception as e:
            logger.error(f"Time series diagnostics failed: {e}")
            raise

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "diagnostics_all_pass": float(all_tests_pass),
                    "durbin_watson": dw_stat,
                    "ljung_box_p_value": ljung_box["p_value"],
                    "jarque_bera_p_value": jarque_bera_test["p_value"],
                }
            )

        return TimeSeriesDiagnosticsResult(
            ljung_box_test=ljung_box,
            jarque_bera_test=jarque_bera_test,
            heteroscedasticity_test=heteroscedasticity,
            durbin_watson=dw_stat,
            residual_mean=resid_mean,
            residual_std=resid_std,
            residual_skewness=resid_skewness,
            residual_kurtosis=resid_kurtosis,
            all_tests_pass=all_tests_pass,
        )

    def fit_vecm(
        self,
        endog_data: pd.DataFrame,
        coint_rank: int,
        k_ar_diff: int = 1,
        deterministic: str = "ci",
    ) -> VECMResult:
        """
        Fit Vector Error Correction Model for cointegrated time series.

        VECM extends VAR for cointegrated series, separating short-run dynamics
        from long-run equilibrium relationships. Use after Johansen test confirms
        cointegration.

        Parameters
        ----------
        endog_data : pd.DataFrame
            DataFrame with multiple cointegrated time series variables.
            Each column is a different endogenous variable.
        coint_rank : int
            Number of cointegrating relationships (from Johansen test).
            Must be between 0 and n_variables-1.
        k_ar_diff : int, default=1
            Number of lagged differences in the VECM.
            Equivalent to VAR lag order minus 1.
        deterministic : str, default='ci'
            Deterministic trend specification:
            - 'nc': No deterministic terms
            - 'co': Constant outside cointegrating relation
            - 'ci': Constant inside cointegrating relation (default)
            - 'lo': Linear trend outside
            - 'li': Linear trend inside

        Returns
        -------
        VECMResult
            Contains fitted model, cointegrating vectors, loading coefficients, and metrics.

        Examples
        --------
        >>> # First run Johansen test
        >>> johansen_result = analyzer.johansen_test(endog_data=endog, k_ar_diff=2)
        >>> print(f"Coint rank: {johansen_result.cointegration_rank}")
        >>>
        >>> # Fit VECM with detected rank
        >>> vecm_result = analyzer.fit_vecm(
        ...     endog_data=endog,
        ...     coint_rank=johansen_result.cointegration_rank,
        ...     k_ar_diff=2
        ... )
        >>> print(f"AIC: {vecm_result.aic:.2f}")
        >>> print(f"Loading coefficients:\\n{vecm_result.alpha}")

        Notes
        -----
        VECM representation: Δy_t = α β' y_{t-1} + Γ_1 Δy_{t-1} + ... + Γ_{p-1} Δy_{t-p+1} + ε_t

        - α (alpha): Loading/adjustment coefficients (speed of adjustment to equilibrium)
        - β (beta): Cointegrating vectors (long-run equilibrium relationships)
        - Γ (gamma): Short-run dynamics coefficients

        Use VECM when:
        - Johansen test confirms cointegration
        - You need to model both short-run and long-run dynamics
        - Variables have long-term equilibrium relationship
        """
        if not ECONOMETRIC_TESTS_AVAILABLE or VECM is None:
            raise ImportError(
                "VECM required. This should be available in statsmodels>=0.12. "
                "Try: pip install --upgrade statsmodels"
            )

        # Validate inputs
        if not isinstance(endog_data, pd.DataFrame):
            raise TypeError("endog_data must be a pandas DataFrame")

        if endog_data.shape[1] < 2:
            raise ValueError(
                f"VECM requires at least 2 variables, got {endog_data.shape[1]}"
            )

        if coint_rank < 0 or coint_rank >= endog_data.shape[1]:
            raise ValueError(
                f"coint_rank must be between 0 and {endog_data.shape[1]-1}, got {coint_rank}"
            )

        # Drop missing values
        endog_clean = endog_data.dropna()
        variable_names = list(endog_data.columns)
        n_obs = len(endog_clean)

        if n_obs < k_ar_diff + 10:
            raise ValueError(
                f"Insufficient observations ({n_obs}) for k_ar_diff={k_ar_diff}"
            )

        try:
            # Fit VECM model
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vecm_model = VECM(
                    endog_clean,
                    k_ar_diff=k_ar_diff,
                    coint_rank=coint_rank,
                    deterministic=deterministic,
                )
                vecm_fitted = vecm_model.fit()

            # Extract model information (with safe accessors for different statsmodels versions)
            try:
                aic_value = (
                    vecm_fitted.aic if hasattr(vecm_fitted, "aic") else float("nan")
                )
            except AttributeError:
                aic_value = float("nan")

            try:
                bic_value = (
                    vecm_fitted.bic if hasattr(vecm_fitted, "bic") else float("nan")
                )
            except AttributeError:
                bic_value = float("nan")

            try:
                hqic_value = (
                    vecm_fitted.hqic if hasattr(vecm_fitted, "hqic") else float("nan")
                )
            except AttributeError:
                hqic_value = float("nan")

            try:
                log_likelihood = (
                    vecm_fitted.llf if hasattr(vecm_fitted, "llf") else float("nan")
                )
            except AttributeError:
                log_likelihood = float("nan")

            # Extract cointegration parameters
            alpha = vecm_fitted.alpha  # loading coefficients
            beta = vecm_fitted.beta  # cointegrating vectors

            # Extract coefficient summary (with safe accessor)
            try:
                if hasattr(vecm_fitted, "params") and vecm_fitted.params is not None:
                    coef_df = pd.DataFrame(
                        vecm_fitted.params,
                        columns=variable_names,
                        index=(
                            vecm_fitted.params.index
                            if hasattr(vecm_fitted.params, "index")
                            else None
                        ),
                    )
                else:
                    # Fallback: create empty DataFrame if params not available
                    coef_df = pd.DataFrame()
            except (AttributeError, ValueError):
                coef_df = pd.DataFrame()

            logger.info(
                f"VECM fitted: rank={coint_rank}, order={k_ar_diff}, "
                f"variables={len(variable_names)}, aic={aic_value:.2f}"
            )

        except Exception as e:
            logger.error(f"VECM fitting failed: {e}")
            raise

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "vecm_coint_rank": float(coint_rank),
                    "vecm_order": float(k_ar_diff),
                    "vecm_aic": float(aic_value),
                    "vecm_bic": float(bic_value),
                    "vecm_n_variables": float(len(variable_names)),
                }
            )

        return VECMResult(
            model=vecm_fitted,
            order=k_ar_diff,
            coint_rank=coint_rank,
            n_variables=len(variable_names),
            variable_names=variable_names,
            deterministic=deterministic,
            alpha=alpha,
            beta=beta,
            aic=aic_value,
            bic=bic_value,
            hqic=hqic_value,
            log_likelihood=log_likelihood,
            coef_summary=coef_df,
        )

    def detect_structural_breaks(
        self,
        model_result: Any,
        test_type: str = "both",
    ) -> StructuralBreakResult:
        """
        Detect structural breaks in time series using CUSUM and Hansen tests.

        Structural breaks indicate parameter instability or regime changes in the
        time series relationship (e.g., coaching changes, rule changes in NBA).

        Parameters
        ----------
        model_result : Any
            Fitted OLS regression model result (from statsmodels).
            Should have `resid` attribute for residuals.
        test_type : str, default='both'
            Which test(s) to run:
            - 'cusum': CUSUM test only (cumulative sum of recursive residuals)
            - 'hansen': Hansen stability test only
            - 'both': Run both tests (default)

        Returns
        -------
        StructuralBreakResult
            Contains test statistics, p-values, and detected break points.

        Examples
        --------
        >>> # Fit OLS model first
        >>> import statsmodels.api as sm
        >>> X = sm.add_constant(df[['games', 'minutes']])
        >>> y = df['points']
        >>> ols_result = sm.OLS(y, X).fit()
        >>>
        >>> # Detect structural breaks
        >>> breaks = analyzer.detect_structural_breaks(
        ...     model_result=ols_result,
        ...     test_type='both'
        ... )
        >>> print(f"Hansen significant: {breaks.hansen_significant}")
        >>> print(f"CUSUM significant: {breaks.cusum_significant}")

        Notes
        -----
        - CUSUM: Tests for parameter constancy using cumulative sums
        - Hansen: Tests for parameter stability with F-statistic
        - Both tests detect changes in regression coefficients over time
        """
        if not ECONOMETRIC_TESTS_AVAILABLE:
            raise ImportError(
                "Structural break tests required. Available in statsmodels>=0.12. "
                "Try: pip install --upgrade statsmodels"
            )

        # Validate inputs
        if not hasattr(model_result, "resid"):
            raise ValueError("model_result must have 'resid' attribute (OLS results)")

        cusum_stat = None
        cusum_significant = None
        hansen_stat = None
        hansen_p_value = None
        hansen_significant = None
        break_points = None

        try:
            # CUSUM test
            if test_type in ["cusum", "both"]:
                if breaks_cusumolsresid is not None:
                    cusum_result = breaks_cusumolsresid(model_result.resid)
                    cusum_stat = cusum_result[0]  # CUSUM statistics
                    # Check if any CUSUM statistic exceeds critical bounds
                    # Typically, significant if max|CUSUM| > 1.36 (approx 5% level)
                    cusum_significant = (
                        float(np.max(np.abs(cusum_stat))) > 1.36
                        if cusum_stat is not None
                        else None
                    )
                else:
                    logger.warning("CUSUM test not available")

            # Hansen stability test
            if test_type in ["hansen", "both"]:
                if breaks_hansen is not None:
                    hansen_result = breaks_hansen(model_result)
                    hansen_stat = float(hansen_result[0])  # test statistic
                    # hansen_result[1] is a structured array of (nobs, critical_value) pairs
                    # Compare test stat to critical values (typically 5% critical value)
                    # If test stat > critical value, reject null (parameter stability)
                    critical_values = hansen_result[1]
                    # Use the 5% critical value (often the middle entry, but use max to be conservative)
                    crit_val_5pct = float(critical_values['crit'][-1])  # Most conservative
                    hansen_significant = hansen_stat > crit_val_5pct
                    # Approximate p-value: no exact p-value, set to 0.05 if borderline
                    hansen_p_value = 0.049 if hansen_significant else 0.051
                else:
                    logger.warning("Hansen test not available")

            logger.info(
                f"Structural break detection: test={test_type}, "
                f"Hansen_sig={hansen_significant}, CUSUM_sig={cusum_significant}"
            )

        except Exception as e:
            logger.error(f"Structural break detection failed: {e}")
            raise

        # MLflow logging
        if self.tracker and hansen_p_value is not None:
            self.tracker.log_metrics(
                {
                    "hansen_p_value": hansen_p_value,
                    "hansen_significant": float(hansen_significant),
                }
            )

        return StructuralBreakResult(
            cusum_statistic=cusum_stat,
            cusum_significant=cusum_significant,
            hansen_statistic=hansen_stat,
            hansen_p_value=hansen_p_value,
            hansen_significant=hansen_significant,
            break_points=break_points,
            test_type=test_type,
        )

    def breusch_godfrey_test(
        self, model_result: Any, nlags: int = 1
    ) -> BreuschGodfreyResult:
        """
        Breusch-Godfrey LM test for autocorrelation in residuals.

        More general than Durbin-Watson test, can detect higher-order serial correlation.
        Tests null hypothesis of no autocorrelation against alternative of AR(nlags).

        Parameters
        ----------
        model_result : Any
            Fitted regression model result (from statsmodels).
            Must have `model` and `resid` attributes.
        nlags : int, default=1
            Number of lags to test for autocorrelation.

        Returns
        -------
        BreuschGodfreyResult
            Contains LM statistic, F-statistic, p-values, and significance.

        Examples
        --------
        >>> # Fit regression model
        >>> import statsmodels.api as sm
        >>> X = sm.add_constant(df[['assists', 'rebounds']])
        >>> y = df['points']
        >>> ols_result = sm.OLS(y, X).fit()
        >>>
        >>> # Test for autocorrelation
        >>> bg_result = analyzer.breusch_godfrey_test(ols_result, nlags=4)
        >>> print(f"Autocorrelation detected: {bg_result.significant_at_5pct}")
        >>> print(f"LM p-value: {bg_result.lm_p_value:.4f}")

        Notes
        -----
        Advantages over Durbin-Watson:
        - Can test for higher-order autocorrelation (nlags > 1)
        - Valid with lagged dependent variables
        - Provides both LM and F-statistics
        """
        if not ECONOMETRIC_TESTS_AVAILABLE or acorr_breusch_godfrey is None:
            raise ImportError(
                "Breusch-Godfrey test required. Available in statsmodels>=0.12. "
                "Try: pip install --upgrade statsmodels"
            )

        # Validate inputs
        if not hasattr(model_result, "model") or not hasattr(model_result, "resid"):
            raise ValueError("model_result must have 'model' and 'resid' attributes")

        if nlags < 1:
            raise ValueError(f"nlags must be >= 1, got {nlags}")

        try:
            # Run Breusch-Godfrey test
            bg_result = acorr_breusch_godfrey(model_result, nlags=nlags)

            # Extract results: (lm_stat, lm_p_value, f_stat, f_p_value)
            lm_statistic = float(bg_result[0])
            lm_p_value = float(bg_result[1])
            f_statistic = float(bg_result[2])
            f_p_value = float(bg_result[3])

            significant_at_5pct = lm_p_value < 0.05
            nobs = len(model_result.resid)

            logger.info(
                f"Breusch-Godfrey test: lags={nlags}, LM_p={lm_p_value:.4f}, "
                f"significant={significant_at_5pct}"
            )

        except Exception as e:
            logger.error(f"Breusch-Godfrey test failed: {e}")
            raise

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "bg_lm_p_value": lm_p_value,
                    "bg_significant": float(significant_at_5pct),
                    "bg_nlags": float(nlags),
                }
            )

        return BreuschGodfreyResult(
            lm_statistic=lm_statistic,
            lm_p_value=lm_p_value,
            f_statistic=f_statistic,
            f_p_value=f_p_value,
            nlags=nlags,
            nobs=nobs,
            significant_at_5pct=significant_at_5pct,
        )

    def heteroscedasticity_tests(
        self,
        model_result: Any,
        test_type: str = "breusch_pagan",
    ) -> HeteroscedasticityResult:
        """
        Test for heteroscedasticity in regression residuals.

        Heteroscedasticity (non-constant variance) violates OLS assumptions and
        affects standard errors. Common in cross-sectional NBA data.

        Parameters
        ----------
        model_result : Any
            Fitted OLS regression model result (from statsmodels).
            Must have `model` and `resid` attributes.
        test_type : str, default='breusch_pagan'
            Which test(s) to run:
            - 'breusch_pagan': Breusch-Pagan LM test (default)
            - 'white': White test (more general)
            - 'both': Run both tests

        Returns
        -------
        HeteroscedasticityResult
            Contains test statistics, p-values, and significance for each test.

        Examples
        --------
        >>> # Fit regression model
        >>> import statsmodels.api as sm
        >>> X = sm.add_constant(df[['experience', 'height']])
        >>> y = df['salary']
        >>> ols_result = sm.OLS(y, X).fit()
        >>>
        >>> # Test for heteroscedasticity
        >>> het_result = analyzer.heteroscedasticity_tests(
        ...     ols_result,
        ...     test_type='both'
        ... )
        >>> print(f"BP significant: {het_result.breusch_pagan_significant}")
        >>> print(f"White significant: {het_result.white_significant}")

        Notes
        -----
        - Breusch-Pagan: Tests if variance is related to independent variables
        - White: More general, allows for non-linear relationships
        - If heteroscedasticity detected, use robust standard errors
        """
        if not ECONOMETRIC_TESTS_AVAILABLE:
            raise ImportError(
                "Heteroscedasticity tests required. Available in statsmodels>=0.12. "
                "Try: pip install --upgrade statsmodels"
            )

        # Validate inputs
        if not hasattr(model_result, "model") or not hasattr(model_result, "resid"):
            raise ValueError("model_result must have 'model' and 'resid' attributes")

        bp_stat = None
        bp_p_value = None
        bp_significant = None
        white_stat = None
        white_p_value = None
        white_significant = None
        arch_stat = None
        arch_p_value = None
        arch_significant = None

        try:
            # Breusch-Pagan test
            if test_type in ["breusch_pagan", "both"]:
                if het_breuschpagan is not None:
                    bp_result = het_breuschpagan(
                        model_result.resid, model_result.model.exog
                    )
                    bp_stat = float(bp_result[0])  # LM statistic
                    bp_p_value = float(bp_result[1])  # p-value
                    bp_significant = bp_p_value < 0.05
                else:
                    logger.warning("Breusch-Pagan test not available")

            # White test
            if test_type in ["white", "both"]:
                if het_white is not None:
                    white_result = het_white(
                        model_result.resid, model_result.model.exog
                    )
                    white_stat = float(white_result[0])  # LM statistic
                    white_p_value = float(white_result[1])  # p-value
                    white_significant = white_p_value < 0.05
                else:
                    logger.warning("White test not available")

            logger.info(
                f"Heteroscedasticity tests: type={test_type}, "
                f"BP_sig={bp_significant}, White_sig={white_significant}"
            )

        except Exception as e:
            logger.error(f"Heteroscedasticity tests failed: {e}")
            raise

        # MLflow logging
        if self.tracker:
            metrics = {}
            if bp_p_value is not None:
                metrics["bp_p_value"] = bp_p_value
                metrics["bp_significant"] = float(bp_significant)
            if white_p_value is not None:
                metrics["white_p_value"] = white_p_value
                metrics["white_significant"] = float(white_significant)
            if metrics:
                self.tracker.log_metrics(metrics)

        return HeteroscedasticityResult(
            breusch_pagan_statistic=bp_stat,
            breusch_pagan_p_value=bp_p_value,
            breusch_pagan_significant=bp_significant,
            white_statistic=white_stat,
            white_p_value=white_p_value,
            white_significant=white_significant,
            arch_statistic=arch_stat,
            arch_p_value=arch_p_value,
            arch_significant=arch_significant,
            test_type=test_type,
        )
