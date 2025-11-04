"""
Advanced Time Series Methods for NBA Analytics.

This module extends the basic time_series.py with advanced methods including:
- State Space Models (Kalman filtering and smoothing)
- Dynamic Factor Models (extract common factors)
- Markov Switching Models (regime changes, hot/cold streaks)
- Structural Time Series (unobserved components)

Designed for complex temporal patterns in NBA data: regime changes (hot streaks),
latent factors (team chemistry), missing data imputation, and real-time tracking.

Key Use Cases:
- Real-time performance tracking with Kalman filtering
- Detecting hot/cold streaks with Markov switching
- Team momentum as latent factor
- Missing data imputation
- Playoff vs regular season regime shifts

Integration:
- Extends TimeSeriesAnalyzer from time_series.py
- Works with panel_data for multi-entity time series
- Bayesian alternatives via bayesian.py
- MLflow tracking for experiments

Author: Agent 8 Module 4C
Date: October 2025
"""

import logging
import warnings
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Union, Literal
from enum import Enum

import numpy as np
import pandas as pd
import scipy.stats as stats

# Custom exceptions
from mcp_server.exceptions import (
    InvalidDataError,
    InvalidParameterError,
)

# State space and advanced time series
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.statespace.dynamic_factor import DynamicFactor
    from statsmodels.tsa.statespace.structural import UnobservedComponents
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    from statsmodels.tsa.statespace.kalman_filter import KalmanFilter
    from statsmodels.tsa.statespace.kalman_smoother import KalmanSmoother

    STATESPACE_AVAILABLE = True
except ImportError:
    STATESPACE_AVAILABLE = False
    SARIMAX = None
    DynamicFactor = None

# MLflow integration
try:
    import mlflow
    from mcp_server.mlflow_integration import MLflowExperimentTracker

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    mlflow = None

logger = logging.getLogger(__name__)


# ==============================================================================
# Enums and Constants
# ==============================================================================


class StateSpaceModel(str, Enum):
    """Supported state space model types."""

    LOCAL_LEVEL = "local_level"
    LOCAL_LINEAR_TREND = "local_linear_trend"
    SEASONAL = "seasonal"
    REGRESSION = "regression"


class RegimeType(str, Enum):
    """Regime types for Markov switching."""

    MEAN_SHIFT = "mean_shift"
    VARIANCE_SHIFT = "variance_shift"
    REGRESSION = "regression"


# ==============================================================================
# Data Classes
# ==============================================================================


@dataclass
class KalmanFilterResult:
    """Results from Kalman filtering."""

    filtered_state: np.ndarray
    filtered_state_cov: np.ndarray
    predicted_state: np.ndarray
    predicted_state_cov: np.ndarray
    forecast: np.ndarray
    forecast_error: np.ndarray
    log_likelihood: float

    def __repr__(self) -> str:
        return (
            f"KalmanFilterResult(\n"
            f"  states shape: {self.filtered_state.shape},\n"
            f"  log_likelihood: {self.log_likelihood:.2f}\n"
            f")"
        )


@dataclass
class SmootherResult:
    """Results from Kalman smoothing."""

    smoothed_state: np.ndarray
    smoothed_state_cov: np.ndarray
    smoothed_measurement_disturbance: Optional[np.ndarray] = None
    smoothed_state_disturbance: Optional[np.ndarray] = None

    def __repr__(self) -> str:
        return (
            f"SmootherResult(\n" f"  states shape: {self.smoothed_state.shape}\n" f")"
        )


@dataclass
class DynamicFactorResult:
    """Results from dynamic factor model."""

    factors: pd.DataFrame  # Extracted common factors
    factor_loadings: pd.DataFrame  # How each series loads on factors
    idiosyncratic: pd.DataFrame  # Series-specific components
    n_factors: int
    log_likelihood: float
    aic: float
    bic: float
    model: Any  # Fitted statsmodels model

    def __repr__(self) -> str:
        return (
            f"DynamicFactorResult(\n"
            f"  n_factors: {self.n_factors},\n"
            f"  AIC: {self.aic:.2f},\n"
            f"  BIC: {self.bic:.2f}\n"
            f")"
        )


@dataclass
class MarkovSwitchingResult:
    """Results from Markov switching model."""

    regimes: np.ndarray  # Regime assignments (0, 1, ...)
    regime_probabilities: pd.DataFrame  # Filtered probabilities over time
    transition_matrix: np.ndarray  # Transition probabilities
    regime_parameters: Dict[int, Dict[str, float]]  # Parameters by regime
    n_regimes: int
    log_likelihood: float
    aic: float
    bic: float
    model: Any

    def get_regime_periods(self, regime: int) -> List[Tuple[int, int]]:
        """Get start/end indices of periods in specified regime."""
        in_regime = (self.regimes == regime).astype(int)
        diff = np.diff(np.concatenate([[0], in_regime, [0]]))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        return list(zip(starts, ends))

    def __repr__(self) -> str:
        return (
            f"MarkovSwitchingResult(\n"
            f"  n_regimes: {self.n_regimes},\n"
            f"  AIC: {self.aic:.2f},\n"
            f"  most_likely_regime: {np.argmax(np.bincount(self.regimes.astype(int)))}\n"
            f")"
        )


@dataclass
class StructuralTimeSeriesResult:
    """Results from structural (unobserved components) time series."""

    level: pd.Series
    trend: Optional[pd.Series]
    seasonal: Optional[pd.Series]
    cycle: Optional[pd.Series]
    irregular: pd.Series
    fitted_values: pd.Series
    log_likelihood: float
    aic: float
    bic: float
    model: Any

    def __repr__(self) -> str:
        components = ["level"]
        if self.trend is not None:
            components.append("trend")
        if self.seasonal is not None:
            components.append("seasonal")
        if self.cycle is not None:
            components.append("cycle")

        return (
            f"StructuralTimeSeriesResult(\n"
            f"  components: {', '.join(components)},\n"
            f"  AIC: {self.aic:.2f},\n"
            f"  BIC: {self.bic:.2f}\n"
            f")"
        )


# ==============================================================================
# AdvancedTimeSeriesAnalyzer Class
# ==============================================================================


class AdvancedTimeSeriesAnalyzer:
    """
    Advanced time series analysis for NBA analytics.

    Provides state space models, dynamic factors, Markov switching, and
    structural time series methods.

    Examples:
        >>> # Kalman filtering for real-time tracking
        >>> analyzer = AdvancedTimeSeriesAnalyzer(data['points'])
        >>> result = analyzer.kalman_filter(model='local_level')
        >>>
        >>> # Detect hot/cold streaks
        >>> result = analyzer.markov_switching(n_regimes=2)
        >>> hot_streaks = result.get_regime_periods(regime=1)
        >>>
        >>> # Extract team momentum factor
        >>> result = analyzer.dynamic_factor_model(
        ...     data[['player1_pts', 'player2_pts', 'player3_pts']],
        ...     n_factors=1
        ... )
    """

    def __init__(
        self,
        data: Union[pd.Series, pd.DataFrame],
        freq: Optional[str] = None,
        mlflow_experiment: Optional[str] = None,
    ):
        """
        Initialize advanced time series analyzer.

        Args:
            data: Time series data (Series for univariate, DataFrame for multivariate)
            freq: Frequency of the time series ('D', 'W', 'M', etc.)
            mlflow_experiment: MLflow experiment name for tracking

        Raises:
            ImportError: If statsmodels state space models not available
        """
        if not STATESPACE_AVAILABLE:
            raise ImportError(
                "statsmodels state space models required for advanced time series. "
                "Ensure statsmodels>=0.14.0 is installed."
            )

        self.data = data
        self.freq = freq or getattr(data.index, "freq", None)

        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            logger.warning(
                "Data index is not DatetimeIndex. Some methods may not work."
            )

        # MLflow setup
        self.mlflow_experiment = mlflow_experiment
        if mlflow_experiment and MLFLOW_AVAILABLE:
            mlflow.set_experiment(mlflow_experiment)

        logger.info(
            f"Initialized AdvancedTimeSeriesAnalyzer with data shape: {data.shape}"
        )

    # ==========================================================================
    # State Space Models & Kalman Filtering
    # ==========================================================================

    def kalman_filter(
        self,
        model: Union[str, StateSpaceModel] = "local_level",
        exog: Optional[pd.DataFrame] = None,
        **model_kwargs,
    ) -> KalmanFilterResult:
        """
        Apply Kalman filter for state estimation and forecasting.

        The Kalman filter is optimal for:
        - Real-time state tracking (online updates)
        - Missing data imputation
        - Signal extraction from noisy observations
        - Forecasting with uncertainty

        Args:
            model: Model type ('local_level', 'local_linear_trend', 'seasonal', 'regression')
            exog: Exogenous variables (for regression model)
            **model_kwargs: Additional model parameters

        Returns:
            KalmanFilterResult with filtered states and forecasts

        Examples:
            >>> # Track player performance in real-time
            >>> result = analyzer.kalman_filter(model='local_level')
            >>> current_state = result.filtered_state[-1]
            >>>
            >>> # With trend
            >>> result = analyzer.kalman_filter(model='local_linear_trend')
        """
        if isinstance(model, StateSpaceModel):
            model = model.value

        # Build state space model
        if model == "local_level":
            mod = UnobservedComponents(self.data, level="local level", **model_kwargs)
        elif model == "local_linear_trend":
            mod = UnobservedComponents(
                self.data, level="local linear trend", **model_kwargs
            )
        elif model == "seasonal":
            season_period = model_kwargs.pop("seasonal_period", 12)
            mod = UnobservedComponents(
                self.data, level="local level", seasonal=season_period, **model_kwargs
            )
        elif model == "regression" and exog is not None:
            mod = SARIMAX(self.data, exog=exog, order=(0, 0, 0), **model_kwargs)
        else:
            valid_models = ["local_level", "local_linear_trend", "seasonal", "regression"]
            raise InvalidParameterError(
                f"Unknown state space model: {model}",
                parameter="model",
                value=model,
                valid_values=valid_models
            )

        # Fit model
        fitted = mod.fit(disp=False)

        # Extract Kalman filter results
        kf_results = fitted.filter_results

        result = KalmanFilterResult(
            filtered_state=kf_results.filtered_state,  # Shape: (k_states, nobs)
            filtered_state_cov=kf_results.filtered_state_cov,
            predicted_state=kf_results.predicted_state,
            predicted_state_cov=kf_results.predicted_state_cov,
            forecast=fitted.fittedvalues.values,
            forecast_error=fitted.resid.values,
            log_likelihood=fitted.llf,
        )

        logger.info(
            f"Kalman filter applied: model={model}, llf={result.log_likelihood:.2f}"
        )
        return result

    def kalman_smoother(
        self, model: Union[str, StateSpaceModel] = "local_level", **model_kwargs
    ) -> SmootherResult:
        """
        Apply Kalman smoother for optimal state estimates using all data.

        The smoother uses both past and future observations, providing
        better estimates than the filter (which only uses past data).

        Use for:
        - Historical state reconstruction
        - Missing data imputation (better than filter)
        - Extracting smooth trends

        Args:
            model: Model type
            **model_kwargs: Additional model parameters

        Returns:
            SmootherResult with smoothed states

        Examples:
            >>> # Smooth historical player performance
            >>> result = analyzer.kalman_smoother(model='local_linear_trend')
            >>> smooth_trend = result.smoothed_state[1, :]  # Trend component
        """
        if isinstance(model, StateSpaceModel):
            model = model.value

        # Build and fit model (same as filter)
        if model == "local_level":
            mod = UnobservedComponents(self.data, level="local level", **model_kwargs)
        elif model == "local_linear_trend":
            mod = UnobservedComponents(
                self.data, level="local linear trend", **model_kwargs
            )
        else:
            valid_models = ["local_level", "local_linear_trend"]
            raise InvalidParameterError(
                f"Model {model} not supported for Kalman smoother",
                parameter="model",
                value=model,
                valid_values=valid_models
            )

        fitted = mod.fit(disp=False)

        # Extract smoother results
        sm_results = fitted.smoother_results

        result = SmootherResult(
            smoothed_state=sm_results.smoothed_state,  # Shape: (k_states, nobs)
            smoothed_state_cov=sm_results.smoothed_state_cov,
        )

        logger.info(f"Kalman smoother applied: model={model}")
        return result

    def forecast_state_space(
        self,
        model: Union[str, StateSpaceModel] = "local_level",
        steps: int = 10,
        exog_forecast: Optional[pd.DataFrame] = None,
        alpha: float = 0.05,
        **model_kwargs,
    ) -> Dict[str, Any]:
        """
        Forecast using state space model.

        Args:
            model: Model type
            steps: Number of steps ahead to forecast
            exog_forecast: Future exogenous variables (for regression)
            alpha: Significance level for confidence intervals
            **model_kwargs: Additional model parameters

        Returns:
            Dict with 'forecast', 'lower_bound', 'upper_bound'

        Examples:
            >>> forecast = analyzer.forecast_state_space(
            ...     model='local_linear_trend',
            ...     steps=10
            ... )
            >>> print(forecast['forecast'])
        """
        if isinstance(model, StateSpaceModel):
            model = model.value

        # Build and fit model
        if model == "local_level":
            mod = UnobservedComponents(self.data, level="local level", **model_kwargs)
        elif model == "local_linear_trend":
            mod = UnobservedComponents(
                self.data, level="local linear trend", **model_kwargs
            )
        elif model == "regression" and exog_forecast is not None:
            # Not implemented in full - would need SARIMAX with exog
            raise NotImplementedError("Regression forecasting not fully implemented")
        else:
            valid_models = ["local_level", "local_linear_trend", "regression"]
            raise InvalidParameterError(
                f"Unknown state space model for forecasting: {model}",
                parameter="model",
                value=model,
                valid_values=valid_models
            )

        fitted = mod.fit(disp=False)

        # Forecast
        forecast_obj = fitted.get_forecast(steps=steps)
        forecast_mean = forecast_obj.predicted_mean
        forecast_ci = forecast_obj.conf_int(alpha=alpha)

        result = {
            "forecast": forecast_mean,
            "lower_bound": forecast_ci.iloc[:, 0],
            "upper_bound": forecast_ci.iloc[:, 1],
            "model": fitted,
        }

        logger.info(f"Forecast {steps} steps ahead with {model}")
        return result

    # ==========================================================================
    # Dynamic Factor Models
    # ==========================================================================

    def dynamic_factor_model(
        self,
        data: Optional[pd.DataFrame] = None,
        n_factors: int = 1,
        factor_order: int = 2,
        **model_kwargs,
    ) -> DynamicFactorResult:
        """
        Fit dynamic factor model to extract common latent factors.

        Dynamic factor models decompose multiple time series into:
        - Common factors (shared across series)
        - Idiosyncratic components (series-specific)

        NBA Use Cases:
        - Team momentum/chemistry as latent factor
        - League-wide trends
        - Multi-player performance modeling

        Args:
            data: DataFrame with multiple time series (if None, uses self.data)
            n_factors: Number of latent factors to extract
            factor_order: AR order for factors
            **model_kwargs: Additional model parameters

        Returns:
            DynamicFactorResult with factors and loadings

        Examples:
            >>> # Extract team momentum from multiple players
            >>> result = analyzer.dynamic_factor_model(
            ...     data=team_stats[['player1_pts', 'player2_pts', 'player3_pts']],
            ...     n_factors=1
            ... )
            >>> team_momentum = result.factors['factor_0']
            >>> print("Factor loadings:", result.factor_loadings)
        """
        if data is None:
            if not isinstance(self.data, pd.DataFrame):
                raise InvalidDataError(
                    "Data must be a DataFrame for dynamic factor model",
                    value=type(self.data).__name__
                )
            data = self.data

        # Fit dynamic factor model
        mod = DynamicFactor(
            data, k_factors=n_factors, factor_order=factor_order, **model_kwargs
        )

        fitted = mod.fit(disp=False)

        # Extract factors
        factors = fitted.factors.filtered
        factor_cols = [f"factor_{i}" for i in range(n_factors)]
        factors_df = pd.DataFrame(factors.T, index=data.index, columns=factor_cols)

        # Factor loadings (how each series loads on factors)
        loadings = fitted.coefficients_of_determination
        loadings_df = pd.DataFrame(loadings, index=data.columns, columns=factor_cols)

        # Idiosyncratic components
        idiosyncratic = data - fitted.fittedvalues

        result = DynamicFactorResult(
            factors=factors_df,
            factor_loadings=loadings_df,
            idiosyncratic=idiosyncratic,
            n_factors=n_factors,
            log_likelihood=fitted.llf,
            aic=fitted.aic,
            bic=fitted.bic,
            model=fitted,
        )

        logger.info(
            f"Dynamic factor model fitted: {n_factors} factors, "
            f"AIC={result.aic:.2f}, BIC={result.bic:.2f}"
        )
        return result

    # ==========================================================================
    # Markov Switching Models
    # ==========================================================================

    def markov_switching(
        self,
        n_regimes: int = 2,
        regime_type: Union[str, RegimeType] = "mean_shift",
        exog: Optional[pd.DataFrame] = None,
        switching_variance: bool = False,
        **model_kwargs,
    ) -> MarkovSwitchingResult:
        """
        Fit Markov switching model to detect regime changes.

        Markov switching models allow parameters to change across unobserved
        regimes (states), useful for detecting structural breaks or phases.

        NBA Use Cases:
        - Hot/cold shooting streaks
        - Season phases (early/mid/late season performance differences)
        - Playoff vs regular season regime shifts
        - Injury recovery phases

        Args:
            n_regimes: Number of regimes (typically 2-3)
            regime_type: Type of switching ('mean_shift', 'variance_shift', 'regression')
            exog: Exogenous variables for regression
            switching_variance: Allow variance to switch across regimes
            **model_kwargs: Additional model parameters

        Returns:
            MarkovSwitchingResult with regime assignments and probabilities

        Examples:
            >>> # Detect hot/cold streaks in shooting
            >>> result = analyzer.markov_switching(
            ...     n_regimes=2,
            ...     regime_type='mean_shift'
            ... )
            >>> print("Regime 0 mean:", result.regime_parameters[0]['mean'])
            >>> print("Regime 1 mean:", result.regime_parameters[1]['mean'])
            >>> hot_streaks = result.get_regime_periods(regime=1)
        """
        if isinstance(regime_type, RegimeType):
            regime_type = regime_type.value

        # Build Markov switching model
        if regime_type == "mean_shift":
            mod = MarkovRegression(
                self.data,
                k_regimes=n_regimes,
                trend="c",  # Constant (intercept) that switches
                switching_variance=switching_variance,
                **model_kwargs,
            )
        elif regime_type == "regression" and exog is not None:
            mod = MarkovRegression(
                self.data,
                k_regimes=n_regimes,
                trend="c",
                exog=exog,
                switching_variance=switching_variance,
                **model_kwargs,
            )
        else:
            valid_regime_types = ["mean_shift", "variance_shift", "regression"]
            raise InvalidParameterError(
                f"Regime type '{regime_type}' not supported or exogenous variables missing for regression",
                parameter="regime_type",
                value=regime_type,
                valid_values=valid_regime_types
            )

        # Fit model
        fitted = mod.fit(disp=False)

        # Extract regime probabilities and assignments
        regime_probs = fitted.smoothed_marginal_probabilities

        # Most likely regime at each time point (use numpy array)
        if isinstance(regime_probs, pd.DataFrame):
            regimes = regime_probs.values.argmax(axis=1)
            regime_probs_array = regime_probs.values
        else:
            regimes = regime_probs.argmax(axis=1)
            regime_probs_array = regime_probs

        # Create DataFrame for probabilities
        regime_probs_df = pd.DataFrame(
            regime_probs_array,
            index=self.data.index,
            columns=[f"regime_{i}" for i in range(n_regimes)],
        )

        # Transition matrix (squeeze and transpose for proper row-stochastic form)
        # statsmodels stores as [to_regime, from_regime], but we want [from_regime, to_regime]
        transition_matrix = fitted.regime_transition.squeeze().T

        # Regime-specific parameters
        regime_params = {}
        for i in range(n_regimes):
            regime_params[i] = {
                "mean": (
                    fitted.params[f"const[{i}]"]
                    if f"const[{i}]" in fitted.params
                    else None
                ),
                "variance": (
                    fitted.params[f"sigma2[{i}]"]
                    if switching_variance
                    else fitted.params.get("sigma2", None)
                ),
            }

        result = MarkovSwitchingResult(
            regimes=regimes,
            regime_probabilities=regime_probs_df,
            transition_matrix=transition_matrix,
            regime_parameters=regime_params,
            n_regimes=n_regimes,
            log_likelihood=fitted.llf,
            aic=fitted.aic,
            bic=fitted.bic,
            model=fitted,
        )

        logger.info(
            f"Markov switching model fitted: {n_regimes} regimes, "
            f"AIC={result.aic:.2f}"
        )
        return result

    # ==========================================================================
    # Structural Time Series (Unobserved Components)
    # ==========================================================================

    def structural_time_series(
        self,
        level: bool = True,
        trend: bool = False,
        seasonal: Optional[int] = None,
        cycle: bool = False,
        **model_kwargs,
    ) -> StructuralTimeSeriesResult:
        """
        Fit structural (unobserved components) time series model.

        Decomposes series into interpretable components:
        - Level: Current baseline value
        - Trend: Rate of change
        - Seasonal: Periodic patterns
        - Cycle: Business cycle-like oscillations
        - Irregular: Random noise

        NBA Use Cases:
        - Decompose player performance into skill level + trend
        - Seasonal patterns (back-to-backs, month effects)
        - Career trajectory modeling

        Args:
            level: Include level component
            trend: Include trend component
            seasonal: Seasonal period (e.g., 7 for weekly, 82 for season games)
            cycle: Include cycle component
            **model_kwargs: Additional model parameters

        Returns:
            StructuralTimeSeriesResult with estimated components

        Examples:
            >>> # Decompose player scoring into level + trend + irregular
            >>> result = analyzer.structural_time_series(
            ...     level=True,
            ...     trend=True,
            ...     seasonal=None
            ... )
            >>> print("Current level:", result.level.iloc[-1])
            >>> print("Trend:", result.trend.iloc[-1])
        """
        # Determine level specification
        if level and trend:
            level_spec = "local linear trend"
        elif level:
            level_spec = "local level"
        else:
            level_spec = None

        # Build unobserved components model
        mod = UnobservedComponents(
            self.data, level=level_spec, seasonal=seasonal, cycle=cycle, **model_kwargs
        )

        fitted = mod.fit(disp=False)

        # Extract components from fitted model
        components = {}

        # Level - always present when level is specified
        if level:
            components["level"] = fitted.level.smoothed
        else:
            components["level"] = pd.Series(np.nan, index=self.data.index)

        # Trend - only present for local linear trend
        if trend and hasattr(fitted, "trend"):
            components["trend"] = pd.Series(
                fitted.trend.smoothed, index=self.data.index
            )
        else:
            components["trend"] = None

        # Seasonal - only present when seasonal specified
        if seasonal is not None and hasattr(fitted, "seasonal"):
            components["seasonal"] = pd.Series(
                fitted.seasonal.smoothed, index=self.data.index
            )
        else:
            components["seasonal"] = None

        # Cycle - only present when cycle specified
        if cycle and hasattr(fitted, "cycle"):
            components["cycle"] = pd.Series(
                fitted.cycle.smoothed, index=self.data.index
            )
        else:
            components["cycle"] = None

        # Irregular (residuals)
        components["irregular"] = fitted.resid

        result = StructuralTimeSeriesResult(
            level=components["level"],
            trend=components["trend"],
            seasonal=components["seasonal"],
            cycle=components["cycle"],
            irregular=components["irregular"],
            fitted_values=fitted.fittedvalues,
            log_likelihood=fitted.llf,
            aic=fitted.aic,
            bic=fitted.bic,
            model=fitted,
        )

        logger.info(
            f"Structural time series fitted: "
            f"level={level}, trend={trend}, seasonal={seasonal}, "
            f"AIC={result.aic:.2f}"
        )
        return result

    # ==========================================================================
    # Utility Methods
    # ==========================================================================

    def impute_missing(
        self, method: str = "kalman", model: str = "local_level", **kwargs
    ) -> pd.Series:
        """
        Impute missing values using state space methods.

        Args:
            method: Imputation method ('kalman')
            model: State space model for Kalman imputation
            **kwargs: Additional parameters

        Returns:
            Series with imputed values

        Examples:
            >>> # Impute missing player stats
            >>> imputed = analyzer.impute_missing(method='kalman', model='local_linear_trend')
        """
        if method == "kalman":
            # Use Kalman smoother for optimal imputation
            smoother_result = self.kalman_smoother(model=model, **kwargs)

            # Use smoothed level as imputation
            imputed = self.data.copy()
            missing_mask = self.data.isna()

            if missing_mask.any():
                # Get smoothed level (first state, shape: (nobs,))
                smoothed_level = smoother_result.smoothed_state[0, :]

                # Ensure we can index properly
                if isinstance(imputed, pd.Series):
                    # For Series, use boolean indexing on the values
                    imputed_values = imputed.values
                    imputed_values[missing_mask.values] = smoothed_level[
                        missing_mask.values
                    ]
                    imputed = pd.Series(
                        imputed_values, index=imputed.index, name=imputed.name
                    )

            return imputed
        else:
            valid_methods = ["kalman"]
            raise InvalidParameterError(
                f"Unknown imputation method: {method}",
                parameter="method",
                value=method,
                valid_values=valid_methods
            )

    def __repr__(self) -> str:
        return (
            f"AdvancedTimeSeriesAnalyzer(\n"
            f"  data shape: {self.data.shape},\n"
            f"  freq: {self.freq}\n"
            f")"
        )
