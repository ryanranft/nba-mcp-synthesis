"""
Unified Econometric Suite for NBA Analytics.

This module provides a high-level interface that automatically selects and applies
appropriate econometric methods based on data structure. It integrates all econometric
modules:

- time_series: ARIMA, VAR, seasonal decomposition
- panel_data: Fixed effects, random effects, difference-in-differences
- bayesian: Hierarchical models, MCMC inference
- advanced_time_series: Kalman filtering, Markov switching, dynamic factors
- causal_inference: IV, RDD, PSM, synthetic control
- survival_analysis: Cox, Kaplan-Meier, competing risks

Key Features:
- Auto-detection of data structure (cross-section, time series, panel, etc.)
- Unified API across all econometric methods
- Model comparison and averaging
- Integrated diagnostics
- MLflow experiment tracking

Author: Agent 8 Module 4D
Date: October 2025
"""

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

# Custom exceptions
from mcp_server.exceptions import (
    DataError,
    InsufficientDataError,
    InvalidDataError,
    InvalidParameterError,
    MissingParameterError,
    ModelFitError,
    validate_data_shape,
    validate_parameter,
)

# MLflow integration
try:
    import mlflow

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    mlflow = None

logger = logging.getLogger(__name__)


# ==============================================================================
# Enums and Constants
# ==============================================================================


class DataStructure(str, Enum):
    """Supported data structures for econometric analysis."""

    CROSS_SECTION = "cross_section"  # Single time point
    TIME_SERIES = "time_series"  # Single entity over time
    PANEL = "panel"  # Multiple entities over time
    EVENT_HISTORY = "event_history"  # Duration/survival data
    TREATMENT_OUTCOME = "treatment_outcome"  # Causal inference setup


class MethodCategory(str, Enum):
    """Categories of econometric methods."""

    TIME_SERIES = "time_series"
    PANEL_DATA = "panel_data"
    BAYESIAN = "bayesian"
    ADVANCED_TIME_SERIES = "advanced_time_series"
    CAUSAL_INFERENCE = "causal_inference"
    SURVIVAL_ANALYSIS = "survival_analysis"


# ==============================================================================
# Data Classes
# ==============================================================================


@dataclass
class SuiteResult:
    """Comprehensive results from econometric suite analysis."""

    data_structure: DataStructure
    method_category: MethodCategory
    method_used: str
    result: Any  # Specific result object from the method
    model: Any  # Fitted model object

    # Diagnostics (when available)
    aic: Optional[float] = None
    bic: Optional[float] = None
    log_likelihood: Optional[float] = None
    r_squared: Optional[float] = None

    # Additional metrics
    n_obs: int = 0
    n_params: int = 0

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    warnings: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """Generate human-readable summary of results."""
        lines = [
            "=" * 60,
            "ECONOMETRIC SUITE RESULTS",
            "=" * 60,
            f"Data Structure: {self.data_structure.value}",
            f"Method Category: {self.method_category.value}",
            f"Method Used: {self.method_used}",
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "MODEL FIT:",
            f"  Observations: {self.n_obs}",
            f"  Parameters: {self.n_params}",
        ]

        if self.aic is not None:
            lines.append(f"  AIC: {self.aic:.2f}")
        if self.bic is not None:
            lines.append(f"  BIC: {self.bic:.2f}")
        if self.log_likelihood is not None:
            lines.append(f"  Log-Likelihood: {self.log_likelihood:.2f}")
        if self.r_squared is not None:
            lines.append(f"  R²: {self.r_squared:.4f}")

        if self.warnings:
            lines.append("")
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def __repr__(self) -> str:
        aic_str = f"{self.aic:.2f}" if self.aic is not None else "N/A"
        return (
            f"SuiteResult(\n"
            f"  data_structure={self.data_structure.value},\n"
            f"  method={self.method_used},\n"
            f"  AIC={aic_str}\n"
            f")"
        )


@dataclass
class DataCharacteristics:
    """Characteristics of the dataset for method selection."""

    structure: DataStructure
    n_obs: int
    n_entities: Optional[int] = None
    n_periods: Optional[int] = None
    has_time_index: bool = False
    has_entity_id: bool = False
    has_treatment: bool = False
    has_outcome: bool = False
    has_duration: bool = False
    has_event: bool = False
    is_balanced: Optional[bool] = None

    def __repr__(self) -> str:
        return (
            f"DataCharacteristics(\n"
            f"  structure={self.structure.value},\n"
            f"  n_obs={self.n_obs},\n"
            f"  n_entities={self.n_entities},\n"
            f"  n_periods={self.n_periods}\n"
            f")"
        )


# ==============================================================================
# Data Classifier
# ==============================================================================


class DataClassifier:
    """
    Analyzes data structure and recommends appropriate econometric methods.

    Detects:
    - Cross-sectional data
    - Time series data
    - Panel data
    - Event history/survival data
    - Treatment-outcome causal structures
    """

    def __init__(
        self,
        data: pd.DataFrame,
        entity_col: Optional[str] = None,
        time_col: Optional[str] = None,
        duration_col: Optional[str] = None,
        event_col: Optional[str] = None,
        treatment_col: Optional[str] = None,
        outcome_col: Optional[str] = None,
    ):
        """
        Initialize data classifier.

        Args:
            data: Input DataFrame
            entity_col: Column identifying entities (for panel data)
            time_col: Column identifying time periods
            duration_col: Column with duration/time-to-event
            event_col: Column with event indicator (0/1)
            treatment_col: Column with treatment assignment
            outcome_col: Column with outcome variable
        """
        self.data = data
        self.entity_col = entity_col
        self.time_col = time_col
        self.duration_col = duration_col
        self.event_col = event_col
        self.treatment_col = treatment_col
        self.outcome_col = outcome_col

    def detect_structure(self) -> DataCharacteristics:
        """
        Detect data structure and characteristics.

        Returns:
            DataCharacteristics object with detected structure
        """
        n_obs = len(self.data)

        # Check for survival/event history data
        if self.duration_col and self.event_col:
            return DataCharacteristics(
                structure=DataStructure.EVENT_HISTORY,
                n_obs=n_obs,
                has_duration=True,
                has_event=True,
            )

        # Check for treatment-outcome structure
        if self.treatment_col and self.outcome_col:
            return DataCharacteristics(
                structure=DataStructure.TREATMENT_OUTCOME,
                n_obs=n_obs,
                has_treatment=True,
                has_outcome=True,
            )

        # Check for panel structure
        if self.entity_col and self.time_col:
            n_entities = self.data[self.entity_col].nunique()
            n_periods = self.data[self.time_col].nunique()

            # Check if balanced
            counts = self.data.groupby(self.entity_col).size()
            is_balanced = (counts == counts.iloc[0]).all()

            return DataCharacteristics(
                structure=DataStructure.PANEL,
                n_obs=n_obs,
                n_entities=n_entities,
                n_periods=n_periods,
                has_entity_id=True,
                has_time_index=True,
                is_balanced=is_balanced,
            )

        # Check for time series
        if self.time_col or isinstance(self.data.index, pd.DatetimeIndex):
            # Check if single entity
            if self.entity_col:
                n_entities = self.data[self.entity_col].nunique()
                if n_entities == 1:
                    return DataCharacteristics(
                        structure=DataStructure.TIME_SERIES,
                        n_obs=n_obs,
                        n_entities=1,
                        has_time_index=True,
                    )
            else:
                return DataCharacteristics(
                    structure=DataStructure.TIME_SERIES,
                    n_obs=n_obs,
                    has_time_index=True,
                )

        # Default to cross-section
        return DataCharacteristics(structure=DataStructure.CROSS_SECTION, n_obs=n_obs)

    def recommend_methods(
        self, characteristics: Optional[DataCharacteristics] = None
    ) -> List[MethodCategory]:
        """
        Recommend appropriate method categories based on data structure.

        Args:
            characteristics: Data characteristics (auto-detected if None)

        Returns:
            List of recommended method categories
        """
        if characteristics is None:
            characteristics = self.detect_structure()

        recommendations = []

        if characteristics.structure == DataStructure.EVENT_HISTORY:
            recommendations.append(MethodCategory.SURVIVAL_ANALYSIS)

        elif characteristics.structure == DataStructure.TREATMENT_OUTCOME:
            recommendations.append(MethodCategory.CAUSAL_INFERENCE)

        elif characteristics.structure == DataStructure.PANEL:
            recommendations.append(MethodCategory.PANEL_DATA)
            recommendations.append(MethodCategory.BAYESIAN)

        elif characteristics.structure == DataStructure.TIME_SERIES:
            recommendations.append(MethodCategory.TIME_SERIES)
            recommendations.append(MethodCategory.ADVANCED_TIME_SERIES)
            recommendations.append(MethodCategory.BAYESIAN)

        elif characteristics.structure == DataStructure.CROSS_SECTION:
            recommendations.append(MethodCategory.BAYESIAN)

        return recommendations


# ==============================================================================
# Model Averager
# ==============================================================================


class ModelAverager:
    """
    Combine predictions from multiple econometric models.

    Supports various weighting schemes:
    - Equal weights
    - AIC-based weights
    - BIC-based weights
    - Performance-based weights
    - Custom weights
    """

    @staticmethod
    def average(
        predictions: Dict[str, np.ndarray],
        weights: Union[str, Dict[str, float]] = "equal",
        model_metrics: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> np.ndarray:
        """
        Average predictions with optional weighting.

        Args:
            predictions: Dict mapping model names to prediction arrays
            weights: Weighting scheme or custom weight dict
            model_metrics: Optional dict with model fit metrics (AIC, BIC, etc.)

        Returns:
            Averaged predictions

        Examples:
            >>> predictions = {'model1': arr1, 'model2': arr2}
            >>> avg = ModelAverager.average(predictions, weights='equal')
        """
        if not predictions:
            raise ValueError("No predictions provided")

        # Convert to arrays
        pred_arrays = list(predictions.values())
        n_models = len(pred_arrays)

        # Ensure all predictions have same shape
        shapes = [p.shape for p in pred_arrays]
        if len(set(shapes)) > 1:
            raise ValueError(f"Prediction shapes don't match: {shapes}")

        # Compute weights
        if isinstance(weights, dict):
            # Custom weights
            weight_arr = np.array([weights[name] for name in predictions.keys()])
        elif weights == "equal":
            weight_arr = np.ones(n_models) / n_models
        elif weights in ["aic", "bic"] and model_metrics is not None:
            # Information criteria weights (lower is better)
            ic_values = np.array(
                [model_metrics[name][weights] for name in predictions.keys()]
            )
            # Convert to weights using Akaike weights formula
            delta_ic = ic_values - ic_values.min()
            likelihood = np.exp(-0.5 * delta_ic)
            weight_arr = likelihood / likelihood.sum()
        elif weights == "performance" and model_metrics is not None:
            # Performance-based (higher is better, e.g., R²)
            if "r_squared" in list(model_metrics.values())[0]:
                r2_values = np.array(
                    [model_metrics[name]["r_squared"] for name in predictions.keys()]
                )
                weight_arr = r2_values / r2_values.sum()
            else:
                logger.warning("R² not available, using equal weights")
                weight_arr = np.ones(n_models) / n_models
        else:
            logger.warning(f"Unknown weighting scheme '{weights}', using equal weights")
            weight_arr = np.ones(n_models) / n_models

        # Normalize weights
        weight_arr = weight_arr / weight_arr.sum()

        # Compute weighted average
        averaged = sum(w * p for w, p in zip(weight_arr, pred_arrays))

        logger.info(f"Averaged {n_models} models with weights: {weight_arr}")
        return averaged


# ==============================================================================
# Econometric Suite
# ==============================================================================


class EconometricSuite:
    """
    Unified interface for all econometric methods.

    Automatically selects appropriate methods based on data structure and
    provides access to all econometric modules through a single API.

    Examples:
        >>> # Auto-detect and analyze
        >>> suite = EconometricSuite(data=df, target='points')
        >>> result = suite.analyze(method='auto')
        >>>
        >>> # Panel data analysis
        >>> suite = EconometricSuite(
        ...     data=df,
        ...     target='points',
        ...     entity_col='player_id',
        ...     time_col='season'
        ... )
        >>> result = suite.panel_analysis(method='fixed_effects')
        >>>
        >>> # Compare methods
        >>> comparison = suite.compare_methods(
        ...     methods=['fixed_effects', 'random_effects'],
        ...     metric='bic'
        ... )
    """

    def __init__(
        self,
        data: pd.DataFrame,
        target: Optional[str] = None,
        entity_col: Optional[str] = None,
        time_col: Optional[str] = None,
        duration_col: Optional[str] = None,
        event_col: Optional[str] = None,
        treatment_col: Optional[str] = None,
        outcome_col: Optional[str] = None,
        mlflow_experiment: Optional[str] = None,
    ):
        """
        Initialize econometric suite.

        Args:
            data: Input DataFrame
            target: Target variable name (for regression/prediction)
            entity_col: Column identifying entities (for panel data)
            time_col: Column identifying time periods
            duration_col: Column with duration/time-to-event
            event_col: Column with event indicator (0/1)
            treatment_col: Column with treatment assignment
            outcome_col: Column with outcome variable
            mlflow_experiment: MLflow experiment name for tracking
        """
        # Validate inputs
        if not isinstance(data, pd.DataFrame):
            raise InvalidDataError(
                "Data must be a pandas DataFrame", value=type(data).__name__
            )

        if data.empty:
            raise InsufficientDataError("DataFrame is empty", required=1, actual=0)

        validate_data_shape(data, min_rows=2)

        # Store attributes
        self.data = data
        self.target = target
        self.entity_col = entity_col
        self.time_col = time_col
        self.duration_col = duration_col
        self.event_col = event_col
        self.treatment_col = treatment_col
        self.outcome_col = outcome_col
        self.mlflow_experiment = mlflow_experiment

        # Classify data
        self.classifier = DataClassifier(
            data=data,
            entity_col=entity_col,
            time_col=time_col,
            duration_col=duration_col,
            event_col=event_col,
            treatment_col=treatment_col,
            outcome_col=outcome_col,
        )

        self.characteristics = self.classifier.detect_structure()
        self.recommended_methods = self.classifier.recommend_methods(
            self.characteristics
        )

        # MLflow setup
        if mlflow_experiment and MLFLOW_AVAILABLE:
            mlflow.set_experiment(mlflow_experiment)

        logger.info(
            f"Initialized EconometricSuite: {self.characteristics.structure.value}, "
            f"{len(data)} observations"
        )

    # ==========================================================================
    # Auto Analysis
    # ==========================================================================

    def analyze(self, method: str = "auto", **kwargs) -> SuiteResult:
        """
        Auto-select and run appropriate analysis.

        Args:
            method: Analysis method
                - 'auto': Auto-detect best method based on data structure
                - Specific method name (delegates to appropriate module)
            **kwargs: Additional parameters passed to the method

        Returns:
            SuiteResult with analysis results

        Examples:
            >>> result = suite.analyze(method='auto')
            >>> result = suite.analyze(method='arima', order=(1, 1, 1))
        """
        if self.mlflow_experiment and MLFLOW_AVAILABLE:
            with mlflow.start_run():
                return self._analyze_impl(method, **kwargs)
        else:
            return self._analyze_impl(method, **kwargs)

    def _analyze_impl(self, method: str, **kwargs) -> SuiteResult:
        """Internal implementation of analyze."""
        # Log data characteristics to MLflow
        if self.mlflow_experiment and MLFLOW_AVAILABLE:
            mlflow.log_params(
                {
                    "data_structure": self.characteristics.structure.value,
                    "n_obs": self.characteristics.n_obs,
                    "n_entities": self.characteristics.n_entities,
                    "n_periods": self.characteristics.n_periods,
                    "method": method,
                }
            )

        # Auto-select method based on data structure
        if method == "auto":
            if self.characteristics.structure == DataStructure.EVENT_HISTORY:
                return self.survival_analysis(**kwargs)
            elif self.characteristics.structure == DataStructure.TREATMENT_OUTCOME:
                return self.causal_analysis(**kwargs)
            elif self.characteristics.structure == DataStructure.PANEL:
                return self.panel_analysis(**kwargs)
            elif self.characteristics.structure == DataStructure.TIME_SERIES:
                return self.time_series_analysis(**kwargs)
            else:
                raise ValueError(
                    f"Cannot auto-select method for {self.characteristics.structure.value}"
                )
        else:
            # Delegate to appropriate module based on method name
            # This would require a method registry
            raise NotImplementedError(
                f"Specific method selection '{method}' not yet implemented"
            )

    # ==========================================================================
    # Module Access Methods
    # ==========================================================================

    def regression(
        self,
        target: Optional[str] = None,
        predictors: Optional[list[str]] = None,
        formula: Optional[str] = None,
    ) -> SuiteResult:
        """
        Run basic OLS regression.

        Args:
            target: Target/outcome variable (uses self.target if None)
            predictors: List of predictor variables (all numeric columns if None)
            formula: Optional R-style formula (e.g., "y ~ x1 + x2")

        Returns:
            SuiteResult with regression results

        Examples:
            >>> # Simple regression
            >>> result = suite.regression(target='points', predictors=['minutes'])
            >>>
            >>> # Multiple regression
            >>> result = suite.regression(
            ...     target='points',
            ...     predictors=['minutes', 'rebounds', 'assists']
            ... )
        """
        import statsmodels.api as sm
        from statsmodels.formula.api import ols

        # Determine target
        target = target or self.target
        if not target:
            raise ValueError("Target variable must be specified")

        # Build formula or use provided one
        if formula:
            model = ols(formula, data=self.data).fit()
            result_target = target
        else:
            # Determine predictors
            if predictors is None:
                # Use all numeric columns except target
                predictors = [
                    col
                    for col in self.data.columns
                    if col != target
                    and pd.api.types.is_numeric_dtype(self.data[col])
                    and not pd.api.types.is_datetime64_any_dtype(self.data[col])
                    and not pd.api.types.is_object_dtype(
                        self.data[col]
                    )  # Exclude object columns
                    and not pd.api.types.is_string_dtype(
                        self.data[col]
                    )  # Exclude string columns
                ]

            if not predictors:
                raise ValueError("No valid predictors found")

            # Prepare data - ensure only numeric data
            X = self.data[predictors].copy()
            y = self.data[target].copy()

            # Convert to numeric, coercing errors
            for col in predictors:
                if X[col].dtype == "object":
                    X[col] = pd.to_numeric(X[col], errors="coerce")

            # Remove NaN values
            combined = pd.concat([y, X], axis=1).dropna()
            y = combined[target]
            X = combined[predictors]

            # Add constant
            X = sm.add_constant(X)

            # Fit model
            model = sm.OLS(y, X).fit()
            result_target = target

        # Extract results
        result = {
            "coefficients": model.params.to_dict(),
            "pvalues": model.pvalues.to_dict(),
            "rsquared": model.rsquared,
            "rsquared_adj": model.rsquared_adj,
            "fvalue": model.fvalue,
            "f_pvalue": model.f_pvalue,
            "aic": model.aic,
            "bic": model.bic,
            "nobs": int(model.nobs),
        }

        # Build parameters dict
        params = {
            "target": result_target,
        }
        if predictors:
            params["predictors"] = predictors
        if formula:
            params["formula"] = formula

        return self._create_suite_result(
            method_category="regression",
            method_used="ols",
            result=result,
            model=model,
            aic=model.aic,
            bic=model.bic,
            r_squared=model.rsquared,
            n_obs=int(model.nobs),
            n_params=len(model.params),
            parameters=params,
        )

    def time_series_analysis(self, method: str = "arima", **kwargs) -> SuiteResult:
        """
        Access time series analysis methods.

        Args:
            method: Time series method:
                - 'arima': ARIMA modeling
                - 'auto_arima': Automatic ARIMA model selection
                - 'arimax': ARIMA with exogenous variables (Phase 2)
                - 'varmax': Vector ARMA with exogenous variables (Phase 2)
                - 'mstl': Multiple Seasonal-Trend decomposition (Phase 2)
                - 'stl': Enhanced STL decomposition (Phase 2)
                - 'johansen'/'cointegration': Johansen cointegration test (Phase 2 Day 4)
                - 'granger'/'granger_causality': Granger causality test (Phase 2 Day 4)
                - 'var': Vector Autoregression model (Phase 2 Day 4)
                - 'diagnostics'/'ts_diagnostics': Time series diagnostics (Phase 2 Day 4)
                - 'vecm': Vector Error Correction Model (Phase 2 Day 5)
                - 'structural_breaks'/'breaks'/'cusum'/'hansen': Structural break detection (Phase 2 Day 5)
                - 'breusch_godfrey'/'bg_test'/'bg': Breusch-Godfrey autocorrelation test (Phase 2 Day 5)
                - 'heteroscedasticity'/'het_test'/'breusch_pagan'/'white': Heteroscedasticity tests (Phase 2 Day 5)
            **kwargs: Method-specific parameters:
                For ARIMAX: order, exog (required), seasonal_order
                For VARMAX: endog_data (required), order, exog, trend
                For MSTL: periods (required), windows, iterate
                For STL: period (required), seasonal, trend, robust
                For Johansen: endog_data (required), det_order, k_ar_diff
                For Granger: caused_series (required), causing_series (required), maxlag
                For VAR: endog_data (required), maxlags, ic, trend
                For Diagnostics: residuals (required), lags, alpha
                For VECM: endog_data (required), coint_rank (required), k_ar_diff, deterministic
                For Structural Breaks: model_result (required), test_type
                For Breusch-Godfrey: model_result (required), nlags
                For Heteroscedasticity: model_result (required), test_type

        Returns:
            SuiteResult with time series analysis results

        Examples:
            >>> # ARIMA
            >>> result = suite.time_series_analysis(method='arima', order=(1,1,1))
            >>>
            >>> # ARIMAX with exogenous variables
            >>> exog_data = df[['assists', 'opponent_rating']]
            >>> result = suite.time_series_analysis(
            ...     method='arimax',
            ...     order=(1,1,1),
            ...     exog=exog_data
            ... )
            >>>
            >>> # VARMAX for multivariate series
            >>> endog = df[['points', 'assists', 'rebounds']]
            >>> result = suite.time_series_analysis(
            ...     method='varmax',
            ...     endog_data=endog,
            ...     order=(2, 1)
            ... )
            >>>
            >>> # MSTL with multiple seasonal patterns
            >>> result = suite.time_series_analysis(
            ...     method='mstl',
            ...     periods=[7, 365]  # weekly + yearly
            ... )
            >>>
            >>> # Enhanced STL
            >>> result = suite.time_series_analysis(
            ...     method='stl',
            ...     period=7,
            ...     robust=True
            ... )
            >>>
            >>> # Johansen cointegration test
            >>> endog = df[['points', 'assists', 'rebounds']]
            >>> result = suite.time_series_analysis(
            ...     method='johansen',
            ...     endog_data=endog,
            ...     k_ar_diff=2
            ... )
            >>>
            >>> # Granger causality test
            >>> result = suite.time_series_analysis(
            ...     method='granger',
            ...     caused_series='points',
            ...     causing_series='assists',
            ...     maxlag=4
            ... )
            >>>
            >>> # VAR model
            >>> endog = df[['points', 'assists', 'rebounds']]
            >>> result = suite.time_series_analysis(
            ...     method='var',
            ...     endog_data=endog,
            ...     maxlags=5,
            ...     ic='aic'
            ... )
            >>>
            >>> # Time series diagnostics
            >>> arima_result = suite.time_series_analysis(method='arima', order=(1,1,1))
            >>> residuals = arima_result.result.model.resid
            >>> diag = suite.time_series_analysis(
            ...     method='diagnostics',
            ...     residuals=residuals,
            ...     lags=10
            ... )
            >>>
            >>> # VECM (after Johansen test confirms cointegration)
            >>> johansen_result = suite.time_series_analysis(
            ...     method='johansen',
            ...     endog_data=endog,
            ...     k_ar_diff=2
            ... )
            >>> vecm_result = suite.time_series_analysis(
            ...     method='vecm',
            ...     endog_data=endog,
            ...     coint_rank=johansen_result.result.cointegration_rank,
            ...     k_ar_diff=2
            ... )
            >>>
            >>> # Structural break detection
            >>> import statsmodels.api as sm
            >>> X = sm.add_constant(df[['games', 'minutes']])
            >>> y = df['points']
            >>> ols_result = sm.OLS(y, X).fit()
            >>> breaks = suite.time_series_analysis(
            ...     method='structural_breaks',
            ...     model_result=ols_result,
            ...     test_type='both'
            ... )
            >>>
            >>> # Breusch-Godfrey autocorrelation test
            >>> bg_result = suite.time_series_analysis(
            ...     method='breusch_godfrey',
            ...     model_result=ols_result,
            ...     nlags=4
            ... )
            >>>
            >>> # Heteroscedasticity tests
            >>> het_result = suite.time_series_analysis(
            ...     method='heteroscedasticity',
            ...     model_result=ols_result,
            ...     test_type='both'
            ... )
        """
        from mcp_server.time_series import TimeSeriesAnalyzer

        # Validate inputs
        if self.target is None:
            raise MissingParameterError(
                "target column must be specified for time series analysis",
                parameter="target",
                context="time_series_analysis",
            )

        if self.target not in self.data.columns:
            raise InvalidDataError(
                f"Target column '{self.target}' not found in data", column=self.target
            )

        # Validate method
        valid_methods = [
            "arima",
            "auto_arima",
            "arimax",
            "var",
            "varmax",
            "stl",
            "mstl",
            "granger",
            "granger_causality",
            "johansen",
            "cointegration",
            "vecm",
            "structural_breaks",
            "breaks",
            "diagnostics",
            "ts_diagnostics",
            "breusch_godfrey",
            "bg_test",
            "bg",
            "heteroscedasticity",
            "het_test",
        ]
        validate_parameter("method", method, valid_values=valid_methods)

        # Validate sufficient data for time series
        validate_data_shape(self.data, min_rows=30)

        try:
            # Pass time_col to analyzer so it can set DatetimeIndex if needed
            time_column_param = (
                self.time_col if hasattr(self, "time_col") and self.time_col else None
            )
            analyzer = TimeSeriesAnalyzer(
                data=self.data, target_column=self.target, time_column=time_column_param
            )
        except Exception as e:
            raise ModelFitError(
                "Failed to create TimeSeriesAnalyzer",
                model_type="time_series",
                reason=str(e),
            ) from e

        if method == "arima":
            # Set default order if not provided
            if "order" not in kwargs:
                kwargs["order"] = (1, 1, 1)
            result = analyzer.fit_arima(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="ARIMA",
                result=result,
                model=result.model,
                aic=result.aic,
                bic=result.bic,
            )
        elif method == "auto_arima":
            result = analyzer.auto_arima(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Auto-ARIMA",
                result=result,
                model=result.model,
                aic=result.aic,
                bic=result.bic,
            )

        # Phase 2 Day 2: New time series methods
        elif method == "arimax":
            # ARIMAX: ARIMA with exogenous variables
            exog = kwargs.get("exog")
            if exog is None:
                raise ValueError("exog parameter required for ARIMAX method")

            if "order" not in kwargs:
                kwargs["order"] = (1, 1, 1)

            result = analyzer.fit_arimax(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="ARIMAX",
                result=result,
                model=result.model,
                aic=result.aic,
                bic=result.bic,
                log_likelihood=result.log_likelihood,
            )

        elif method == "varmax":
            # VARMAX: Vector ARMA with exogenous variables
            endog_data = kwargs.get("endog_data")
            if endog_data is None:
                raise ValueError("endog_data parameter required for VARMAX method")

            result = analyzer.fit_varmax(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="VARMAX",
                result=result,
                model=result.model,
                aic=result.aic,
                bic=result.bic,
                log_likelihood=result.log_likelihood,
            )

        elif method == "mstl":
            # MSTL: Multiple Seasonal-Trend decomposition
            periods = kwargs.get("periods")
            if periods is None:
                raise ValueError("periods parameter required for MSTL method")

            result = analyzer.mstl_decompose(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="MSTL",
                result=result,
                model=None,
            )

        elif method == "stl":
            # Enhanced STL decomposition
            period = kwargs.get("period")
            if period is None:
                raise ValueError("period parameter required for STL method")

            result = analyzer.stl_decompose(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="STL",
                result=result,
                model=None,
            )

        # Phase 2 Day 4: Advanced econometric time series methods
        elif method in ["johansen", "johansen_test", "cointegration"]:
            # Johansen cointegration test
            endog_data = kwargs.get("endog_data")
            if endog_data is None:
                raise ValueError("endog_data parameter required for Johansen test")

            result = analyzer.johansen_test(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Johansen Cointegration Test",
                result=result,
                model=None,
            )

        elif method in ["granger", "granger_causality", "granger_test"]:
            # Granger causality test
            caused_series = kwargs.get("caused_series")
            causing_series = kwargs.get("causing_series")
            if caused_series is None or causing_series is None:
                raise ValueError(
                    "Both caused_series and causing_series required for Granger causality test"
                )

            result = analyzer.granger_causality_test(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Granger Causality Test",
                result=result,
                model=None,
            )

        elif method == "var":
            # Vector Autoregression model
            endog_data = kwargs.get("endog_data")
            if endog_data is None:
                raise ValueError("endog_data parameter required for VAR model")

            result = analyzer.fit_var(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="VAR Model",
                result=result,
                model=result.model,
                aic=result.aic,
                bic=result.bic,
                log_likelihood=result.log_likelihood,
            )

        elif method in ["diagnostics", "ts_diagnostics", "time_series_diagnostics"]:
            # Time series diagnostics
            residuals = kwargs.get("residuals")
            if residuals is None:
                raise ValueError("residuals parameter required for diagnostics")

            result = analyzer.time_series_diagnostics(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Time Series Diagnostics",
                result=result,
                model=None,
            )

        # Phase 2 Day 5: Advanced econometric tests
        elif method == "vecm":
            # Vector Error Correction Model
            endog_data = kwargs.get("endog_data")
            coint_rank = kwargs.get("coint_rank")
            if endog_data is None or coint_rank is None:
                raise ValueError("endog_data and coint_rank required for VECM")

            result = analyzer.fit_vecm(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="VECM",
                result=result,
                model=result.model,
                aic=result.aic,
                bic=result.bic,
                log_likelihood=result.log_likelihood,
            )

        elif method in ["structural_breaks", "breaks", "cusum", "hansen"]:
            # Structural break detection
            model_result = kwargs.get("model_result")
            if model_result is None:
                raise ValueError(
                    "model_result parameter required for structural break tests"
                )

            result = analyzer.detect_structural_breaks(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Structural Break Detection",
                result=result,
                model=None,
            )

        elif method in ["breusch_godfrey", "bg_test", "bg"]:
            # Breusch-Godfrey autocorrelation test
            model_result = kwargs.get("model_result")
            if model_result is None:
                raise ValueError(
                    "model_result parameter required for Breusch-Godfrey test"
                )

            result = analyzer.breusch_godfrey_test(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Breusch-Godfrey Test",
                result=result,
                model=None,
            )

        elif method in ["heteroscedasticity", "het_test", "breusch_pagan", "white"]:
            # Heteroscedasticity tests
            model_result = kwargs.get("model_result")
            if model_result is None:
                raise ValueError(
                    "model_result parameter required for heteroscedasticity tests"
                )

            result = analyzer.heteroscedasticity_tests(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Heteroscedasticity Tests",
                result=result,
                model=None,
            )

        else:
            raise ValueError(f"Unknown time series method: {method}")

    def panel_analysis(self, method: str = "fixed_effects", **kwargs) -> SuiteResult:
        """
        Access panel data analysis methods including dynamic panel GMM.

        Supports static panel methods (pooled OLS, fixed/random effects) and
        dynamic panel GMM methods (Arellano-Bond, Blundell-Bond) for models with
        lagged dependent variables and endogeneity.

        Args:
            method: Panel method to use. Options:
                Static Panel:
                - 'fixed_effects', 'fe': Fixed effects (within) estimator
                - 'random_effects', 're': Random effects (GLS) estimator
                - 'pooled_ols', 'pooled': Pooled OLS (ignores panel structure)

                Dynamic Panel GMM (Phase 2 Day 6):
                - 'first_diff', 'fd', 'first_difference': First-difference OLS
                - 'diff_gmm', 'arellano_bond', 'ab_gmm': Difference GMM (Arellano-Bond)
                - 'sys_gmm', 'system_gmm', 'bb_gmm', 'blundell_bond': System GMM (Blundell-Bond)
                - 'gmm_diagnostics', 'gmm_tests': GMM diagnostic tests

            **kwargs: Method-specific parameters

        Returns:
            SuiteResult with panel analysis results

        Examples:
            >>> # Static panel methods
            >>> result = suite.panel_analysis(method='fixed_effects')
            >>>
            >>> # First-difference estimator
            >>> result = suite.panel_analysis(
            ...     method='first_diff',
            ...     formula='points ~ minutes + age'
            ... )
            >>>
            >>> # Arellano-Bond Difference GMM
            >>> result = suite.panel_analysis(
            ...     method='diff_gmm',
            ...     formula='points ~ lag(points, 1) + minutes + age',
            ...     gmm_type='two_step',
            ...     max_lags=3,
            ...     collapse=True
            ... )
            >>> print(f"Points persistence: {result.result.coefficients['lag(points, 1)']:.3f}")
            >>> print(f"AR(2) valid: {result.result.ar2_pvalue > 0.05}")
            >>>
            >>> # Blundell-Bond System GMM (for persistent series)
            >>> result = suite.panel_analysis(
            ...     method='system_gmm',
            ...     formula='wins ~ lag(wins, 1) + payroll + avg_age',
            ...     gmm_type='two_step',
            ...     max_lags=4
            ... )
            >>> print(f"Hansen J-test: {result.result.hansen_pvalue:.3f}")

        Notes:
            GMM Method Selection:
            - Use First-Difference OLS when no lagged dependent variable
            - Use Difference GMM (Arellano-Bond) for dynamic panels
            - Use System GMM (Blundell-Bond) for highly persistent series
            - Check AR(2) and Hansen tests to validate GMM specification
        """
        from mcp_server.panel_data import PanelDataAnalyzer

        # Validate method parameter
        valid_methods = [
            "fixed_effects",
            "fe",
            "random_effects",
            "re",
            "pooled_ols",
            "pooled",
            "first_diff",
            "fd",
            "first_difference",
            "diff_gmm",
            "arellano_bond",
            "ab_gmm",
            "difference_gmm",
            "sys_gmm",
            "system_gmm",
            "bb_gmm",
            "blundell_bond",
            "gmm_diagnostics",
            "gmm_tests",
        ]
        validate_parameter("method", method, valid_values=valid_methods)

        # Validate required columns
        if self.entity_col is None or self.time_col is None:
            missing = []
            if self.entity_col is None:
                missing.append("entity_col")
            if self.time_col is None:
                missing.append("time_col")
            raise MissingParameterError(
                "entity_col and time_col must be specified for panel analysis",
                parameter=" and ".join(missing),
                context="panel_analysis",
            )

        if self.target is None:
            raise MissingParameterError(
                "target column must be specified for panel analysis",
                parameter="target",
                context="panel_analysis",
            )

        # Validate columns exist in data
        if self.entity_col not in self.data.columns:
            raise InvalidDataError(
                f"Entity column '{self.entity_col}' not found in data",
                column=self.entity_col,
            )
        if self.time_col not in self.data.columns:
            raise InvalidDataError(
                f"Time column '{self.time_col}' not found in data", column=self.time_col
            )
        if self.target not in self.data.columns:
            raise InvalidDataError(
                f"Target column '{self.target}' not found in data", column=self.target
            )

        # Validate minimum data for panel analysis (need multiple entities and time periods)
        validate_data_shape(self.data, min_rows=10)

        # Create analyzer with error handling
        try:
            analyzer = PanelDataAnalyzer(
                data=self.data,
                entity_col=self.entity_col,
                time_col=self.time_col,
                target_col=self.target,
            )
        except Exception as e:
            raise ModelFitError(
                "Failed to create PanelDataAnalyzer", model_type="panel", reason=str(e)
            ) from e

        # Build formula: target ~ 1 (intercept only, entity/time effects handled by method)
        formula = f"{self.target} ~ 1"

        if method == "fixed_effects":
            result = analyzer.fixed_effects(formula=formula, **kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.PANEL_DATA,
                method_used="Fixed Effects",
                result=result,
                model=None,  # PanelModelResult doesn't have model attribute
                r_squared=result.r_squared,
            )
        elif method == "random_effects":
            result = analyzer.random_effects(formula=formula, **kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.PANEL_DATA,
                method_used="Random Effects",
                result=result,
                model=None,  # PanelModelResult doesn't have model attribute
                r_squared=result.r_squared,
            )

        # Phase 2 Day 6: Dynamic Panel GMM Methods
        elif method in ["first_diff", "fd", "first_difference"]:
            # First-difference OLS
            formula_str = kwargs.pop(
                "formula", formula
            )  # Use pop to remove from kwargs
            result = analyzer.first_difference(formula=formula_str, **kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.PANEL_DATA,
                method_used="First-Difference OLS",
                result=result,
                model=None,
                r_squared=result.r_squared,
            )

        elif method in ["diff_gmm", "arellano_bond", "ab_gmm", "difference_gmm"]:
            # Arellano-Bond Difference GMM
            formula_str = kwargs.pop("formula", None)  # Use pop to remove from kwargs
            if formula_str is None:
                raise MissingParameterError(
                    "formula parameter required for Difference GMM",
                    parameter="formula",
                    context="panel_analysis(method=diff_gmm)",
                )

            result = analyzer.difference_gmm(formula=formula_str, **kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.PANEL_DATA,
                method_used="Arellano-Bond Difference GMM",
                result=result,
                model=None,
                n_obs=result.n_obs,
                n_params=len(result.coefficients),
            )

        elif method in ["sys_gmm", "system_gmm", "bb_gmm", "blundell_bond"]:
            # Blundell-Bond System GMM
            formula_str = kwargs.pop("formula", None)  # Use pop to remove from kwargs
            if formula_str is None:
                raise MissingParameterError(
                    "formula parameter required for System GMM",
                    parameter="formula",
                    context="panel_analysis(method=system_gmm)",
                )

            result = analyzer.system_gmm(formula=formula_str, **kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.PANEL_DATA,
                method_used="Blundell-Bond System GMM",
                result=result,
                model=None,
                n_obs=result.n_obs,
                n_params=len(result.coefficients),
            )

        elif method in ["gmm_diagnostics", "gmm_tests"]:
            # GMM diagnostic tests
            gmm_result = kwargs.get("gmm_result")
            if gmm_result is None:
                raise MissingParameterError(
                    "gmm_result parameter required for GMM diagnostics. "
                    "Pass result from diff_gmm or system_gmm.",
                    parameter="gmm_result",
                    context="panel_analysis(method=gmm_diagnostics)",
                )

            result = analyzer.gmm_diagnostics(gmm_result=gmm_result)
            return self._create_suite_result(
                method_category=MethodCategory.PANEL_DATA,
                method_used="GMM Diagnostic Tests",
                result=result,
                model=None,
            )

        else:
            # This should never happen due to validate_parameter, but keep for safety
            raise InvalidParameterError(
                f"Unknown panel method: {method}", parameter="method", value=method
            )

    def causal_analysis(
        self,
        treatment_col: Optional[str] = None,
        outcome_col: Optional[str] = None,
        method: str = "psm",
        **kwargs,
    ) -> SuiteResult:
        """
        Access causal inference methods.

        Args:
            treatment_col: Treatment variable (uses self.treatment_col if None)
            outcome_col: Outcome variable (uses self.outcome_col if None)
            method: Causal method:
                - 'psm': Propensity Score Matching
                - 'iv' or 'instrumental_variables': Instrumental Variables (2SLS)
                - 'rdd' or 'regression_discontinuity': Regression Discontinuity Design
                - 'synthetic' or 'synthetic_control': Synthetic Control Method
                - 'kernel' or 'kernel_matching': Kernel Matching (weighted PSM)
                - 'radius' or 'radius_matching': Radius (Caliper) Matching
                - 'doubly_robust' or 'doubly_robust_estimation': Doubly Robust Estimation
            **kwargs: Method-specific parameters:
                For IV: instruments (required), formula, robust, entity_effects
                For RDD: running_var (required), cutoff (required), bandwidth, kernel,
                        polynomial_order, fuzzy, optimal_bandwidth_method
                For Synthetic: treated_unit (required), outcome_periods (required),
                              treatment_period (required), donor_pool, covariates_for_matching,
                              n_placebo
                For Kernel: kernel ('gaussian', 'epanechnikov', 'tricube'), bandwidth,
                           estimate_std_error
                For Radius: radius (default 0.05), estimate_std_error
                For Doubly Robust: estimate_std_error

        Returns:
            SuiteResult with causal analysis results

        Examples:
            >>> # Propensity Score Matching
            >>> result = suite.causal_analysis(
            ...     treatment_col='new_coach',
            ...     outcome_col='wins',
            ...     method='psm'
            ... )
            >>> # Instrumental Variables
            >>> result = suite.causal_analysis(
            ...     treatment_col='training',
            ...     outcome_col='performance',
            ...     method='iv',
            ...     instruments=['prior_exposure']
            ... )
            >>> # Regression Discontinuity
            >>> result = suite.causal_analysis(
            ...     treatment_col='scholarship',
            ...     outcome_col='graduation_rate',
            ...     method='rdd',
            ...     running_var='test_score',
            ...     cutoff=70.0
            ... )
            >>> # Kernel Matching
            >>> result = suite.causal_analysis(
            ...     treatment_col='training',
            ...     outcome_col='performance',
            ...     method='kernel',
            ...     kernel='gaussian'
            ... )
            >>> # Doubly Robust
            >>> result = suite.causal_analysis(
            ...     treatment_col='treatment',
            ...     outcome_col='outcome',
            ...     method='doubly_robust'
            ... )
        """
        from mcp_server.causal_inference import CausalInferenceAnalyzer

        # Validate method
        valid_methods = [
            "psm",
            "iv",
            "instrumental_variables",
            "rdd",
            "regression_discontinuity",
            "synthetic",
            "synthetic_control",
            "kernel",
            "kernel_matching",
            "radius",
            "radius_matching",
            "doubly_robust",
            "doubly_robust_estimation",
        ]
        validate_parameter("method", method, valid_values=valid_methods)

        # Validate sufficient data
        validate_data_shape(self.data, min_rows=20)

        # Synthetic Control handles treatment differently (no treatment_col needed)
        if method == "synthetic" or method == "synthetic_control":
            outcome = outcome_col or self.outcome_col
            if outcome is None:
                raise MissingParameterError(
                    "outcome_col must be specified for synthetic control",
                    parameter="outcome_col",
                    context="causal_analysis",
                )

            treated_unit = kwargs.get("treated_unit")
            outcome_periods = kwargs.get("outcome_periods")
            treatment_period = kwargs.get("treatment_period")

            if (
                treated_unit is None
                or outcome_periods is None
                or treatment_period is None
            ):
                raise ValueError(
                    "treated_unit, outcome_periods, and treatment_period required for synthetic control"
                )

            # For synthetic control, create analyzer with dummy treatment (not used)
            analyzer = CausalInferenceAnalyzer(
                data=self.data,
                treatment_col=self.entity_col,  # Dummy, not actually used
                outcome_col=outcome,
                covariates=[],
                entity_col=self.entity_col,
                time_col=self.time_col,
            )

            result = analyzer.synthetic_control(
                treated_unit=treated_unit,
                outcome_periods=outcome_periods,
                treatment_period=treatment_period,
                donor_pool=kwargs.get("donor_pool"),
                covariates_for_matching=kwargs.get("covariates_for_matching"),
                n_placebo=kwargs.get("n_placebo", 0),
            )
            return self._create_suite_result(
                method_category=MethodCategory.CAUSAL_INFERENCE,
                method_used="Synthetic Control",
                result=result,
                model=None,
            )

        # For other methods, require treatment_col
        treatment = treatment_col or self.treatment_col
        outcome = outcome_col or self.outcome_col

        if treatment is None or outcome is None:
            raise MissingParameterError(
                "treatment_col and outcome_col must be specified for causal analysis",
                parameter="treatment_col, outcome_col",
                context="causal_analysis",
            )

        # Validate columns exist
        if treatment not in self.data.columns:
            raise InvalidDataError(
                f"Treatment column '{treatment}' not found in data", column=treatment
            )
        if outcome not in self.data.columns:
            raise InvalidDataError(
                f"Outcome column '{outcome}' not found in data", column=outcome
            )

        # For IV, exclude instruments from covariates
        instruments = kwargs.get("instruments", [])
        if isinstance(instruments, str):
            instruments = [instruments]

        # Filter out datetime columns and non-numeric columns
        exclude_cols = [
            treatment,
            outcome,
            self.entity_col,
            self.time_col,
        ] + instruments
        covariates = [
            col
            for col in self.data.columns
            if col not in exclude_cols
            and not pd.api.types.is_datetime64_any_dtype(self.data[col])
            and pd.api.types.is_numeric_dtype(self.data[col])
        ]

        analyzer = CausalInferenceAnalyzer(
            data=self.data,
            treatment_col=treatment,
            outcome_col=outcome,
            covariates=covariates[:10],  # Limit covariates
        )

        if method == "psm":
            result = analyzer.propensity_score_matching(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.CAUSAL_INFERENCE,
                method_used="Propensity Score Matching",
                result=result,
                model=None,  # PSMResult doesn't have model attribute
            )

        elif method == "iv" or method == "instrumental_variables":
            # Instrumental Variables (2SLS)
            instruments = kwargs.get("instruments")
            if instruments is None:
                raise ValueError("instruments parameter required for IV method")

            result = analyzer.instrumental_variables(
                instruments=instruments,
                formula=kwargs.get("formula"),
                robust=kwargs.get("robust", True),
                entity_effects=kwargs.get("entity_effects", False),
            )
            return self._create_suite_result(
                method_category=MethodCategory.CAUSAL_INFERENCE,
                method_used="Instrumental Variables (2SLS)",
                result=result,
                model=None,
            )

        elif method == "rdd" or method == "regression_discontinuity":
            # Regression Discontinuity Design
            running_var = kwargs.get("running_var")
            cutoff = kwargs.get("cutoff")
            if running_var is None or cutoff is None:
                raise ValueError(
                    "running_var and cutoff parameters required for RDD method"
                )

            result = analyzer.regression_discontinuity(
                running_var=running_var,
                cutoff=cutoff,
                bandwidth=kwargs.get("bandwidth"),
                kernel=kwargs.get("kernel", "triangular"),
                polynomial_order=kwargs.get("polynomial_order", 1),
                fuzzy=kwargs.get("fuzzy", False),
                optimal_bandwidth_method=kwargs.get("optimal_bandwidth_method", "ik"),
            )
            return self._create_suite_result(
                method_category=MethodCategory.CAUSAL_INFERENCE,
                method_used="Regression Discontinuity Design",
                result=result,
                model=None,
            )

        elif method == "kernel" or method == "kernel_matching":
            # Kernel Matching (weighted PSM)
            result = analyzer.kernel_matching(
                kernel=kwargs.get("kernel", "gaussian"),
                bandwidth=kwargs.get("bandwidth"),
                estimate_std_error=kwargs.get("estimate_std_error", True),
            )
            return self._create_suite_result(
                method_category=MethodCategory.CAUSAL_INFERENCE,
                method_used="Kernel Matching",
                result=result,
                model=None,
            )

        elif method == "radius" or method == "radius_matching":
            # Radius (Caliper) Matching
            result = analyzer.radius_matching(
                radius=kwargs.get("radius", 0.05),
                estimate_std_error=kwargs.get("estimate_std_error", True),
            )
            return self._create_suite_result(
                method_category=MethodCategory.CAUSAL_INFERENCE,
                method_used="Radius Matching",
                result=result,
                model=None,
            )

        elif method == "doubly_robust" or method == "doubly_robust_estimation":
            # Doubly Robust Estimation
            result = analyzer.doubly_robust_estimation(
                estimate_std_error=kwargs.get("estimate_std_error", True),
            )
            return self._create_suite_result(
                method_category=MethodCategory.CAUSAL_INFERENCE,
                method_used="Doubly Robust Estimation",
                result=result,
                model=None,
            )

        else:
            raise ValueError(f"Unknown causal method: {method}")

    def survival_analysis(
        self,
        duration_col: Optional[str] = None,
        event_col: Optional[str] = None,
        method: str = "cox",
        **kwargs,
    ) -> SuiteResult:
        """
        Access survival analysis methods.

        Args:
            duration_col: Duration variable (uses self.duration_col if None)
            event_col: Event indicator (uses self.event_col if None)
            method: Survival method:
                - 'cox': Cox Proportional Hazards (default)
                - 'kaplan_meier' or 'km': Kaplan-Meier estimator
                - 'parametric': Parametric survival models (Weibull, Log-Normal, etc.)
                - 'competing_risks': Competing risks analysis
                - 'frailty' or 'complete_frailty': Frailty model with multiple distributions
                - 'fine_gray': Fine-Gray competing risks regression
                - 'cure' or 'cure_model': Mixture cure model
                - 'recurrent_events' or 'pwp'/'ag'/'wlw': Recurrent events models
            **kwargs: Method-specific parameters:
                For KM: groups, alpha, timeline
                For Parametric: model ('weibull', 'lognormal', 'loglogistic', 'exponential'),
                               formula, timeline
                For Competing Risks: event_type_col (required), event_types (required), method
                For Frailty: shared_frailty_col, distribution ('gamma', 'gaussian',
                             'inverse_gaussian'), penalizer
                For Fine-Gray: event_type_col (required), event_of_interest (required),
                              covariates, formula
                For Cure Model: cure_formula, survival_formula, timeline
                For Recurrent Events: id_col (required), event_count_col, model_type
                                     ('pwp', 'ag', 'wlw'), gap_time, formula, robust

        Returns:
            SuiteResult with survival analysis results

        Examples:
            >>> # Cox Proportional Hazards
            >>> result = suite.survival_analysis(
            ...     duration_col='career_years',
            ...     event_col='retired',
            ...     method='cox'
            ... )
            >>> # Kaplan-Meier
            >>> result = suite.survival_analysis(
            ...     duration_col='career_years',
            ...     event_col='retired',
            ...     method='kaplan_meier',
            ...     groups='position'
            ... )
            >>> # Parametric (Weibull)
            >>> result = suite.survival_analysis(
            ...     duration_col='career_years',
            ...     event_col='retired',
            ...     method='parametric',
            ...     model='weibull'
            ... )
            >>> # Frailty model with gaussian distribution
            >>> result = suite.survival_analysis(
            ...     duration_col='career_years',
            ...     event_col='retired',
            ...     method='frailty',
            ...     shared_frailty_col='team_id',
            ...     distribution='gaussian'
            ... )
            >>> # Fine-Gray competing risks
            >>> result = suite.survival_analysis(
            ...     duration_col='career_years',
            ...     event_col='retired',
            ...     method='fine_gray',
            ...     event_type_col='retirement_cause',
            ...     event_of_interest='injury'
            ... )
            >>> # Mixture cure model
            >>> result = suite.survival_analysis(
            ...     duration_col='career_years',
            ...     event_col='retired',
            ...     method='cure',
            ...     cure_formula='~ age + position'
            ... )
            >>> # Recurrent events (Andersen-Gill)
            >>> result = suite.survival_analysis(
            ...     duration_col='days_between_injuries',
            ...     event_col='injury_occurred',
            ...     method='ag',
            ...     id_col='player_id'
            ... )
        """
        from mcp_server.survival_analysis import SurvivalAnalyzer

        # Validate method parameter
        valid_methods = [
            "cox",
            "kaplan_meier",
            "km",
            "parametric",
            "competing_risks",
            "frailty",
            "complete_frailty",
            "fine_gray",
            "fine_gray_competing_risks",
            "cure",
            "cure_model",
            "recurrent_events",
            "pwp",
            "ag",
            "wlw",
        ]
        validate_parameter("method", method, valid_values=valid_methods)

        duration = duration_col or self.duration_col
        event = event_col or self.event_col

        # Validate required parameters
        if duration is None or event is None:
            missing = []
            if duration is None:
                missing.append("duration_col")
            if event is None:
                missing.append("event_col")
            raise MissingParameterError(
                "duration_col and event_col must be specified for survival analysis",
                parameter=" and ".join(missing),
                context="survival_analysis",
            )

        # Validate columns exist in data
        if duration not in self.data.columns:
            raise InvalidDataError(
                f"Duration column '{duration}' not found in data", column=duration
            )
        if event not in self.data.columns:
            raise InvalidDataError(
                f"Event column '{event}' not found in data", column=event
            )

        # Validate minimum data for survival analysis
        validate_data_shape(self.data, min_rows=10)

        # Filter out datetime columns and non-numeric columns
        exclude_cols = [duration, event, self.entity_col, self.time_col]
        covariates = [
            col
            for col in self.data.columns
            if col not in exclude_cols
            and not pd.api.types.is_datetime64_any_dtype(self.data[col])
            and pd.api.types.is_numeric_dtype(self.data[col])
        ]

        # Create analyzer with error handling
        try:
            analyzer = SurvivalAnalyzer(
                data=self.data,
                duration_col=duration,
                event_col=event,
                covariates=covariates[:10],  # Limit covariates
            )
        except Exception as e:
            raise ModelFitError(
                "Failed to create SurvivalAnalyzer",
                model_type="survival",
                reason=str(e),
            ) from e

        if method == "cox":
            result = analyzer.cox_proportional_hazards(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.SURVIVAL_ANALYSIS,
                method_used="Cox Proportional Hazards",
                result=result,
                model=None,  # SurvivalResult doesn't have model attribute
                log_likelihood=result.log_likelihood,
                aic=result.aic,
                bic=result.bic,
            )

        elif method == "kaplan_meier" or method == "km":
            # Kaplan-Meier non-parametric estimator
            result = analyzer.kaplan_meier(
                groups=kwargs.get("groups"),
                alpha=kwargs.get("alpha", 0.05),
                timeline=kwargs.get("timeline"),
            )
            # Handle grouped vs ungrouped results
            if isinstance(result, dict):
                # Grouped K-M returns dict of results
                # For Suite, we'll wrap the first group's result
                first_group = list(result.values())[0]
                return self._create_suite_result(
                    method_category=MethodCategory.SURVIVAL_ANALYSIS,
                    method_used="Kaplan-Meier Estimator",
                    result=result,  # Store full dict
                    model=None,
                )
            else:
                return self._create_suite_result(
                    method_category=MethodCategory.SURVIVAL_ANALYSIS,
                    method_used="Kaplan-Meier Estimator",
                    result=result,
                    model=None,
                )

        elif method == "parametric":
            # Parametric survival models
            model_type = kwargs.get("model", "weibull")
            result = analyzer.parametric_survival(
                model=model_type,
                formula=kwargs.get("formula"),
                timeline=kwargs.get("timeline"),
            )
            return self._create_suite_result(
                method_category=MethodCategory.SURVIVAL_ANALYSIS,
                method_used=f"Parametric Survival ({model_type.capitalize()})",
                result=result,
                model=None,
                aic=result.aic,
                bic=result.bic,
                log_likelihood=result.log_likelihood,
            )

        elif method == "competing_risks":
            # Competing risks analysis
            event_type_col = kwargs.get("event_type_col")
            event_types = kwargs.get("event_types")

            if event_type_col is None or event_types is None:
                missing = []
                if event_type_col is None:
                    missing.append("event_type_col")
                if event_types is None:
                    missing.append("event_types")
                raise MissingParameterError(
                    "event_type_col and event_types parameters required for competing_risks method",
                    parameter=" and ".join(missing),
                    context="survival_analysis(method=competing_risks)",
                )

            result = analyzer.competing_risks(
                event_type_col=event_type_col,
                event_types=event_types,
                method=kwargs.get("method", "cumulative_incidence"),
            )
            return self._create_suite_result(
                method_category=MethodCategory.SURVIVAL_ANALYSIS,
                method_used="Competing Risks",
                result=result,
                model=None,
            )

        elif method == "frailty" or method == "complete_frailty":
            # Frailty model (random effects survival)
            result = analyzer.frailty_model(
                shared_frailty_col=kwargs.get("shared_frailty_col"),
                distribution=kwargs.get("distribution", "gamma"),
                penalizer=kwargs.get("penalizer", 0.0),
            )
            return self._create_suite_result(
                method_category=MethodCategory.SURVIVAL_ANALYSIS,
                method_used="Frailty Model",
                result=result,
                model=None,
                aic=result.aic if hasattr(result, "aic") else None,
                bic=result.bic if hasattr(result, "bic") else None,
                log_likelihood=(
                    result.log_likelihood if hasattr(result, "log_likelihood") else None
                ),
            )

        elif method == "fine_gray" or method == "fine_gray_competing_risks":
            # Fine-Gray competing risks model
            event_type_col = kwargs.get("event_type_col")
            event_of_interest = kwargs.get("event_of_interest")

            if event_type_col is None or event_of_interest is None:
                missing = []
                if event_type_col is None:
                    missing.append("event_type_col")
                if event_of_interest is None:
                    missing.append("event_of_interest")
                raise MissingParameterError(
                    "event_type_col and event_of_interest required for Fine-Gray model",
                    parameter=" and ".join(missing),
                    context="survival_analysis(method=fine_gray)",
                )

            result = analyzer.fine_gray_model(
                event_type_col=event_type_col,
                event_of_interest=event_of_interest,
                covariates=kwargs.get("covariates"),
                formula=kwargs.get("formula"),
            )
            return self._create_suite_result(
                method_category=MethodCategory.SURVIVAL_ANALYSIS,
                method_used="Fine-Gray Competing Risks",
                result=result,
                model=None,
                aic=result.aic if hasattr(result, "aic") else None,
                log_likelihood=(
                    result.log_likelihood if hasattr(result, "log_likelihood") else None
                ),
            )

        elif method == "cure" or method == "cure_model":
            # Mixture cure model
            result = analyzer.cure_model(
                cure_formula=kwargs.get("cure_formula"),
                survival_formula=kwargs.get("survival_formula"),
                timeline=kwargs.get("timeline"),
            )
            return self._create_suite_result(
                method_category=MethodCategory.SURVIVAL_ANALYSIS,
                method_used="Mixture Cure Model",
                result=result,
                model=None,
                aic=result.aic if hasattr(result, "aic") else None,
                bic=result.bic if hasattr(result, "bic") else None,
                log_likelihood=(
                    result.log_likelihood if hasattr(result, "log_likelihood") else None
                ),
            )

        elif method == "recurrent_events" or method in ["pwp", "ag", "wlw"]:
            # Recurrent events model
            id_col = kwargs.get("id_col")
            if id_col is None:
                raise ValueError("id_col required for recurrent events model")

            # Determine model_type from method name
            if method in ["pwp", "ag", "wlw"]:
                model_type = method
            else:
                model_type = kwargs.get("model_type", "ag")

            result = analyzer.recurrent_events_model(
                id_col=id_col,
                event_count_col=kwargs.get("event_count_col"),
                model_type=model_type,
                gap_time=kwargs.get("gap_time", False),
                formula=kwargs.get("formula"),
                robust=kwargs.get("robust", True),
            )
            return self._create_suite_result(
                method_category=MethodCategory.SURVIVAL_ANALYSIS,
                method_used=f"Recurrent Events ({result.model_type.upper()})",
                result=result,
                model=None,
                aic=result.aic if hasattr(result, "aic") else None,
            )

        else:
            raise ValueError(f"Unknown survival method: {method}")

    def bayesian_analysis(self, method: str = "hierarchical", **kwargs) -> SuiteResult:
        """
        Access Bayesian analysis methods.

        Args:
            method: Bayesian method ('hierarchical', 'regression', 'time_series')
            **kwargs: Method-specific parameters

        Returns:
            SuiteResult with Bayesian analysis results

        Examples:
            >>> result = suite.bayesian_analysis(method='hierarchical')
        """
        from mcp_server.bayesian import BayesianAnalyzer

        if self.target is None:
            raise ValueError("target column must be specified for Bayesian analysis")

        analyzer = BayesianAnalyzer(self.data, target_col=self.target)

        if method == "hierarchical":
            result = analyzer.hierarchical_regression(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.BAYESIAN,
                method_used="Bayesian Hierarchical Regression",
                result=result,
                model=result.model,
            )
        else:
            raise ValueError(f"Unknown Bayesian method: {method}")

    def bayesian_time_series_analysis(
        self, method: str = "bvar", **kwargs
    ) -> SuiteResult:
        """
        Access Bayesian time series methods.

        Methods include:
        - BVAR: Bayesian Vector Autoregression with Minnesota prior
        - BSTS: Bayesian Structural Time Series (coming soon)
        - Hierarchical TS: Multi-level time series (coming soon)

        Args:
            method: Bayesian TS method:
                - 'bvar' or 'bayesian_var': Bayesian VAR with Minnesota prior
                - 'bsts' or 'structural': Bayesian Structural Time Series (Week 2)
                - 'hierarchical_ts': Hierarchical Bayesian Time Series (Week 3)
            **kwargs: Method-specific parameters

        BVAR Parameters:
            var_names: List[str] - Variable names for VAR
            lags: int - Number of lags (default=1)
            draws: int - MCMC draws (default=2000)
            tune: int - MCMC tuning steps (default=1000)
            chains: int - Number of chains (default=4)
            lambda1: float - Overall tightness (default=0.2)
            lambda2: float - Cross-variable shrinkage (default=0.5)
            lambda3: float - Lag decay (default=1.0)

        Returns:
            SuiteResult with Bayesian time series results

        Examples:
            >>> # Bayesian VAR
            >>> result = suite.bayesian_time_series_analysis(
            ...     method='bvar',
            ...     var_names=['points', 'assists', 'rebounds'],
            ...     lags=2,
            ...     draws=1000
            ... )
            >>> print(f"WAIC: {result.result.waic:.2f}")
            >>>
            >>> # Access forecasts
            >>> forecasts = analyzer.forecast(result.result, steps=10)
        """
        from mcp_server.bayesian_time_series import (
            BVARAnalyzer,
            PYMC_AVAILABLE,
            check_pymc_available,
        )

        # Validate method parameter
        valid_methods = [
            "bvar",
            "bayesian_var",
            "bsts",
            "structural",
            "hierarchical_ts",
        ]
        validate_parameter("method", method, valid_values=valid_methods)

        # Validate minimum data for Bayesian analysis
        validate_data_shape(self.data, min_rows=30)

        # Check PyMC availability
        check_pymc_available()

        if method == "bvar" or method == "bayesian_var":
            # Bayesian Vector Autoregression
            var_names = kwargs.pop("var_names", None)
            if var_names is None:
                # Try to infer from data columns
                if isinstance(self.data, pd.DataFrame):
                    var_names = self.data.columns.tolist()[:3]  # Use first 3 columns
                    logger.info(f"Auto-selected variables: {var_names}")
                else:
                    raise MissingParameterError(
                        "var_names must be specified for BVAR",
                        parameter="var_names",
                        context="bayesian_time_series_analysis(method=bvar)",
                    )

            # Validate var_names columns exist
            for var in var_names:
                if var not in self.data.columns:
                    raise InvalidDataError(
                        f"Variable '{var}' not found in data", column=var
                    )

            lags = kwargs.pop("lags", 1)

            # Initialize analyzer with error handling
            try:
                analyzer = BVARAnalyzer(
                    data=self.data, var_names=var_names, lags=lags, minnesota_prior=True
                )
            except Exception as e:
                raise ModelFitError(
                    "Failed to create BVARAnalyzer",
                    model_type="bayesian_var",
                    reason=str(e),
                ) from e

            # Fit model with error handling
            try:
                result = analyzer.fit(**kwargs)
            except Exception as e:
                raise ModelFitError(
                    "Failed to fit Bayesian VAR model",
                    model_type="bayesian_var",
                    reason=str(e),
                ) from e

            return self._create_suite_result(
                method_category=MethodCategory.BAYESIAN,
                method_used="Bayesian VAR (Minnesota Prior)",
                result=result,
                model=result.model,
                aic=result.waic,  # Use WAIC as AIC analog
                n_obs=analyzer.n_obs,
                n_params=len(result.summary) if result.summary is not None else 0,
            )

        elif method == "bsts" or method == "structural":
            # Bayesian Structural Time Series (Week 2 - Coming Soon)
            raise NotImplementedError(
                "Bayesian Structural Time Series (BSTS) coming in Week 2. "
                "Stay tuned!"
            )

        elif method == "hierarchical_ts":
            # Hierarchical Bayesian Time Series (Week 3 - Coming Soon)
            raise NotImplementedError(
                "Hierarchical Bayesian Time Series coming in Week 3. " "Stay tuned!"
            )

        else:
            # This should never happen due to validate_parameter, but keep for safety
            raise InvalidParameterError(
                f"Unknown Bayesian time series method: {method}",
                parameter="method",
                value=method,
                valid_values=valid_methods,
            )

    def particle_filter_analysis(
        self, method: str = "player_performance", **kwargs
    ) -> SuiteResult:
        """
        Access particle filter methods for real-time tracking.

        Particle filters (Sequential Monte Carlo) are ideal for:
        - Real-time player performance tracking
        - Live game win probability updates
        - Non-linear state estimation
        - Bayesian filtering with arbitrary distributions

        Methods include:
        - player_performance: Track player skill and form over time
        - live_game: Real-time win probability tracking
        - custom: Generic particle filter with custom dynamics

        Args:
            method: Particle filter method:
                - 'player_performance': Track player skill/form (default)
                - 'live_game': Live win probability tracking
                - 'custom': Generic particle filter
            **kwargs: Method-specific parameters

        Player Performance Parameters:
            target_col: str - Target variable (e.g., 'points')
            covariate_cols: List[str] - Covariates (e.g., ['minutes', 'opponent_strength'])
            n_particles: int - Number of particles (default=1000)
            skill_drift: float - Expected skill change per game (default=0)
            skill_volatility: float - Skill noise (default=0.05)
            form_persistence: float - Form AR(1) coefficient (default=0.7)
            form_volatility: float - Form noise (default=0.2)

        Live Game Parameters:
            score_updates: List[Tuple[float, int, int]] - (time, home_score, away_score)
            home_team_rating: float - Home team net rating
            away_team_rating: float - Away team net rating
            n_particles: int - Number of particles (default=2000)

        Returns:
            SuiteResult with particle filter results

        Examples:
            >>> # Track player performance
            >>> result = suite.particle_filter_analysis(
            ...     method='player_performance',
            ...     target_col='points',
            ...     covariate_cols=['minutes', 'home_game'],
            ...     n_particles=1000
            ... )
            >>> print(result.result.form_states)
            >>>
            >>> # Live game tracking
            >>> score_updates = [(12, 25, 22), (24, 48, 45), (36, 70, 68), (48, 95, 92)]
            >>> result = suite.particle_filter_analysis(
            ...     method='live_game',
            ...     score_updates=score_updates,
            ...     home_team_rating=5.0,
            ...     away_team_rating=3.0
            ... )
            >>> print(f"Final win prob: {result.result.final_win_prob:.1%}")
        """
        from mcp_server.particle_filters import (
            PlayerPerformanceParticleFilter,
            LiveGameProbabilityFilter,
            ParticleFilter,
            create_player_filter,
            create_game_filter,
        )

        if method == "player_performance":
            # Player performance tracking
            target_col = kwargs.pop("target_col", "points")
            covariate_cols = kwargs.pop("covariate_cols", None)
            coefficients = kwargs.pop("coefficients", None)

            # Use auto-tuned filter if data available
            if hasattr(self, "data") and self.data is not None:
                pf = create_player_filter(self.data, **kwargs)
                result = pf.filter_player_season(
                    data=self.data,
                    target_col=target_col,
                    covariate_cols=covariate_cols,
                    coefficients=coefficients,
                )
            else:
                raise ValueError(
                    "player_performance method requires data to be set in EconometricSuite"
                )

            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Particle Filter: Player Performance",
                result=result,
                model=None,
                n_obs=len(result.states),
                n_params=2,  # skill, form
            )

        elif method == "live_game":
            # Live game win probability tracking
            score_updates = kwargs.pop("score_updates", None)
            if score_updates is None:
                raise ValueError("score_updates required for live_game method")

            home_team_rating = kwargs.pop("home_team_rating", 0.0)
            away_team_rating = kwargs.pop("away_team_rating", 0.0)
            initial_diff = kwargs.pop("initial_diff", 0.0)

            pf = create_game_filter(
                home_team_rating=home_team_rating,
                away_team_rating=away_team_rating,
                **kwargs,
            )

            result = pf.track_game(
                score_updates=score_updates, initial_diff=initial_diff
            )

            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Particle Filter: Live Game Probability",
                result=result,
                model=None,
                n_obs=len(result.time_points),
                n_params=1,  # score_diff
            )

        elif method == "custom":
            # Generic particle filter
            n_particles = kwargs.pop("n_particles", 1000)
            state_dim = kwargs.pop("state_dim", 1)
            transition_fn = kwargs.pop("transition_fn", None)
            observation_fn = kwargs.pop("observation_fn", None)

            if transition_fn is None or observation_fn is None:
                raise ValueError(
                    "custom method requires transition_fn and observation_fn"
                )

            pf = ParticleFilter(
                n_particles=n_particles,
                state_dim=state_dim,
                transition_fn=transition_fn,
                observation_fn=observation_fn,
                **kwargs,
            )

            # Require observations and initial_state
            observations = kwargs.pop("observations", None)
            initial_state = kwargs.pop("initial_state", None)

            if observations is None or initial_state is None:
                raise ValueError(
                    "custom method requires observations and initial_state"
                )

            result = pf.filter(observations, initial_state, **kwargs)

            return self._create_suite_result(
                method_category=MethodCategory.TIME_SERIES,
                method_used="Particle Filter: Custom",
                result=result,
                model=None,
                n_obs=len(observations),
                n_params=state_dim,
            )

        else:
            raise ValueError(
                f"Unknown particle filter method: {method}. "
                f"Available: 'player_performance', 'live_game', 'custom'"
            )

    def advanced_time_series_analysis(
        self, method: str = "kalman", **kwargs
    ) -> SuiteResult:
        """
        Access advanced time series methods.

        Args:
            method: Advanced method:
                - 'kalman': Kalman filter for state estimation
                - 'markov_switching' or 'markov': Markov switching models
                - 'dynamic_factor': Dynamic factor models
                - 'structural': Structural time series (unobserved components)
            **kwargs: Method-specific parameters:
                For Kalman: model ('local_level', 'local_linear_trend', 'seasonal'), exog
                For Markov: n_regimes, regime_type, exog, switching_variance
                For Dynamic Factor: data (DataFrame), n_factors, factor_order
                For Structural: level, trend, seasonal, cycle

        Returns:
            SuiteResult with advanced time series results

        Examples:
            >>> # Kalman filter
            >>> result = suite.advanced_time_series_analysis(
            ...     method='kalman',
            ...     model='local_level'
            ... )
            >>> # Markov switching
            >>> result = suite.advanced_time_series_analysis(
            ...     method='markov_switching',
            ...     n_regimes=2
            ... )
            >>> # Dynamic factor
            >>> result = suite.advanced_time_series_analysis(
            ...     method='dynamic_factor',
            ...     n_factors=2
            ... )
        """
        from mcp_server.advanced_time_series import AdvancedTimeSeriesAnalyzer

        # Validate method parameter
        valid_methods = [
            "kalman",
            "markov_switching",
            "markov",
            "dynamic_factor",
            "structural",
        ]
        validate_parameter("method", method, valid_values=valid_methods)

        # Validate target
        if self.target is None:
            raise MissingParameterError(
                "target column must be specified for advanced time series analysis",
                parameter="target",
                context="advanced_time_series_analysis",
            )

        # Validate target exists in data
        if self.target not in self.data.columns:
            raise InvalidDataError(
                f"Target column '{self.target}' not found in data", column=self.target
            )

        # Validate minimum data for advanced time series
        validate_data_shape(self.data, min_rows=30)

        # Create analyzer with error handling
        try:
            analyzer = AdvancedTimeSeriesAnalyzer(self.data[self.target])
        except Exception as e:
            raise ModelFitError(
                "Failed to create AdvancedTimeSeriesAnalyzer",
                model_type="advanced_time_series",
                reason=str(e),
            ) from e

        if method == "kalman":
            result = analyzer.kalman_filter(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.ADVANCED_TIME_SERIES,
                method_used="Kalman Filter",
                result=result,
                model=None,
                log_likelihood=result.log_likelihood,
            )

        elif method == "markov_switching" or method == "markov":
            # Markov switching regime models
            n_regimes = kwargs.get("n_regimes", 2)
            result = analyzer.markov_switching(
                n_regimes=n_regimes,
                regime_type=kwargs.get("regime_type", "mean_shift"),
                exog=kwargs.get("exog"),
                switching_variance=kwargs.get("switching_variance", False),
            )
            return self._create_suite_result(
                method_category=MethodCategory.ADVANCED_TIME_SERIES,
                method_used="Markov Switching",
                result=result,
                model=None,
                aic=result.aic if hasattr(result, "aic") else None,
                bic=result.bic if hasattr(result, "bic") else None,
                log_likelihood=(
                    result.log_likelihood if hasattr(result, "log_likelihood") else None
                ),
            )

        elif method == "dynamic_factor":
            # Dynamic factor model
            # For dynamic factor, we might need multivariate data
            data_for_dfm = kwargs.get("data", self.data)
            n_factors = kwargs.get("n_factors", 1)
            factor_order = kwargs.get("factor_order", 2)

            # Extract model_kwargs (anything not data, n_factors, factor_order)
            model_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k not in ["data", "n_factors", "factor_order"]
            }

            result = analyzer.dynamic_factor_model(
                data=data_for_dfm if isinstance(data_for_dfm, pd.DataFrame) else None,
                n_factors=n_factors,
                factor_order=factor_order,
                **model_kwargs,  # Pass through additional kwargs like enforce_stationarity
            )
            return self._create_suite_result(
                method_category=MethodCategory.ADVANCED_TIME_SERIES,
                method_used="Dynamic Factor Model",
                result=result,
                model=None,
                aic=result.aic if hasattr(result, "aic") else None,
                bic=result.bic if hasattr(result, "bic") else None,
                log_likelihood=(
                    result.log_likelihood if hasattr(result, "log_likelihood") else None
                ),
            )

        elif method == "structural":
            # Structural time series (unobserved components)
            result = analyzer.structural_time_series(
                level=kwargs.get("level", True),
                trend=kwargs.get("trend", False),
                seasonal=kwargs.get("seasonal"),
                cycle=kwargs.get("cycle", False),
            )
            return self._create_suite_result(
                method_category=MethodCategory.ADVANCED_TIME_SERIES,
                method_used="Structural Time Series",
                result=result,
                model=None,
                aic=result.aic if hasattr(result, "aic") else None,
                bic=result.bic if hasattr(result, "bic") else None,
                log_likelihood=(
                    result.log_likelihood if hasattr(result, "log_likelihood") else None
                ),
            )

        else:
            # This should never happen due to validate_parameter, but keep for safety
            raise InvalidParameterError(
                f"Unknown advanced time series method: {method}",
                parameter="method",
                value=method,
                valid_values=valid_methods,
            )

    # ==========================================================================
    # Model Comparison and Averaging
    # ==========================================================================

    def compare_methods(
        self, methods: List[Dict[str, Any]], metric: str = "aic"
    ) -> pd.DataFrame:
        """
        Compare multiple methods.

        Args:
            methods: List of method specifications, each dict with:
                - 'category': Method category (e.g., 'time_series')
                - 'method': Specific method (e.g., 'arima')
                - 'params': Method parameters
            metric: Comparison metric ('aic', 'bic', 'r_squared')

        Returns:
            DataFrame with comparison results

        Examples:
            >>> comparison = suite.compare_methods(
            ...     methods=[
            ...         {'category': 'panel', 'method': 'fixed_effects', 'params': {}},
            ...         {'category': 'panel', 'method': 'random_effects', 'params': {}}
            ...     ],
            ...     metric='bic'
            ... )
        """
        results = []

        for spec in methods:
            category = spec["category"]
            method = spec["method"]
            params = spec.get("params", {})

            try:
                if category == "time_series":
                    result = self.time_series_analysis(method=method, **params)
                elif category == "panel":
                    result = self.panel_analysis(method=method, **params)
                elif category == "causal":
                    result = self.causal_analysis(method=method, **params)
                elif category == "survival":
                    result = self.survival_analysis(method=method, **params)
                elif category == "bayesian":
                    result = self.bayesian_analysis(method=method, **params)
                elif category == "advanced_time_series":
                    result = self.advanced_time_series_analysis(method=method, **params)
                else:
                    logger.warning(f"Unknown category: {category}")
                    continue

                results.append(
                    {
                        "method": result.method_used,
                        "aic": result.aic,
                        "bic": result.bic,
                        "r_squared": result.r_squared,
                        "log_likelihood": result.log_likelihood,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to run {category}/{method}: {e}")
                continue

        comparison_df = pd.DataFrame(results)

        # Add ranking column
        if metric in comparison_df.columns and comparison_df[metric].notna().any():
            # Lower is better for AIC/BIC, higher is better for R²
            ascending = metric in ["aic", "bic"]
            comparison_df["rank"] = comparison_df[metric].rank(ascending=ascending)
            comparison_df = comparison_df.sort_values("rank")

        return comparison_df

    # ==========================================================================
    # Utility Methods
    # ==========================================================================

    def _create_suite_result(
        self,
        method_category: MethodCategory,
        method_used: str,
        result: Any,
        model: Any,
        **kwargs,
    ) -> SuiteResult:
        """Create SuiteResult object with common fields."""
        # Allow n_obs override from kwargs, otherwise use len(self.data)
        if "n_obs" not in kwargs:
            kwargs["n_obs"] = len(self.data)

        suite_result = SuiteResult(
            data_structure=self.characteristics.structure,
            method_category=method_category,
            method_used=method_used,
            result=result,
            model=model,
            **kwargs,
        )

        # Log to MLflow
        if self.mlflow_experiment and MLFLOW_AVAILABLE:
            metrics = {}
            if suite_result.aic is not None:
                metrics["aic"] = suite_result.aic
            if suite_result.bic is not None:
                metrics["bic"] = suite_result.bic
            if suite_result.r_squared is not None:
                metrics["r_squared"] = suite_result.r_squared
            if suite_result.log_likelihood is not None:
                metrics["log_likelihood"] = suite_result.log_likelihood

            if metrics:
                mlflow.log_metrics(metrics)

        return suite_result

    def diagnostic_summary(self, result: SuiteResult) -> str:
        """
        Generate diagnostic summary for a result.

        Args:
            result: SuiteResult to summarize

        Returns:
            Diagnostic summary string
        """
        return result.summary()

    def __repr__(self) -> str:
        return (
            f"EconometricSuite(\n"
            f"  data_structure={self.characteristics.structure.value},\n"
            f"  n_obs={len(self.data)},\n"
            f"  recommended_methods={[m.value for m in self.recommended_methods]}\n"
            f")"
        )
