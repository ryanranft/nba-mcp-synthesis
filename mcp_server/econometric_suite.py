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
        return DataCharacteristics(
            structure=DataStructure.CROSS_SECTION, n_obs=n_obs
        )

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
            ic_values = np.array([model_metrics[name][weights] for name in predictions.keys()])
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
        self.recommended_methods = self.classifier.recommend_methods(self.characteristics)

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
            raise NotImplementedError(f"Specific method selection '{method}' not yet implemented")

    # ==========================================================================
    # Module Access Methods
    # ==========================================================================

    def time_series_analysis(self, method: str = "arima", **kwargs) -> SuiteResult:
        """
        Access time series analysis methods.

        Args:
            method: Time series method ('arima', 'var', 'seasonal_decompose')
            **kwargs: Method-specific parameters

        Returns:
            SuiteResult with time series analysis results

        Examples:
            >>> result = suite.time_series_analysis(method='arima', order=(1,1,1))
        """
        from mcp_server.time_series import TimeSeriesAnalyzer

        if self.target is None:
            raise ValueError("target column must be specified for time series analysis")

        analyzer = TimeSeriesAnalyzer(data=self.data, target_column=self.target)

        if method == "arima":
            # Set default order if not provided
            if 'order' not in kwargs:
                kwargs['order'] = (1, 1, 1)
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
        else:
            raise ValueError(f"Unknown time series method: {method}")

    def panel_analysis(self, method: str = "fixed_effects", **kwargs) -> SuiteResult:
        """
        Access panel data analysis methods.

        Args:
            method: Panel method ('fixed_effects', 'random_effects', 'pooled_ols', 'diff_in_diff')
            **kwargs: Method-specific parameters

        Returns:
            SuiteResult with panel analysis results

        Examples:
            >>> result = suite.panel_analysis(method='fixed_effects')
        """
        from mcp_server.panel_data import PanelDataAnalyzer

        if self.entity_col is None or self.time_col is None:
            raise ValueError("entity_col and time_col must be specified for panel analysis")

        if self.target is None:
            raise ValueError("target column must be specified for panel analysis")

        analyzer = PanelDataAnalyzer(
            data=self.data,
            entity_col=self.entity_col,
            time_col=self.time_col,
            target_col=self.target,
        )

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
        else:
            raise ValueError(f"Unknown panel method: {method}")

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
            method: Causal method ('iv', 'rdd', 'psm', 'synthetic_control')
            **kwargs: Method-specific parameters

        Returns:
            SuiteResult with causal analysis results

        Examples:
            >>> result = suite.causal_analysis(
            ...     treatment_col='new_coach',
            ...     outcome_col='wins',
            ...     method='psm'
            ... )
        """
        from mcp_server.causal_inference import CausalInferenceAnalyzer

        treatment = treatment_col or self.treatment_col
        outcome = outcome_col or self.outcome_col

        if treatment is None or outcome is None:
            raise ValueError("treatment_col and outcome_col must be specified")

        covariates = [
            col for col in self.data.columns if col not in [treatment, outcome, self.entity_col, self.time_col]
        ]

        analyzer = CausalInferenceAnalyzer(
            data=self.data, treatment_col=treatment, outcome_col=outcome, covariates=covariates[:10]  # Limit covariates
        )

        if method == "psm":
            result = analyzer.propensity_score_matching(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.CAUSAL_INFERENCE,
                method_used="Propensity Score Matching",
                result=result,
                model=None,  # PSMResult doesn't have model attribute
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
            method: Survival method ('cox', 'weibull', 'kaplan_meier')
            **kwargs: Method-specific parameters

        Returns:
            SuiteResult with survival analysis results

        Examples:
            >>> result = suite.survival_analysis(
            ...     duration_col='career_years',
            ...     event_col='retired',
            ...     method='cox'
            ... )
        """
        from mcp_server.survival_analysis import SurvivalAnalyzer

        duration = duration_col or self.duration_col
        event = event_col or self.event_col

        if duration is None or event is None:
            raise ValueError("duration_col and event_col must be specified")

        covariates = [
            col for col in self.data.columns if col not in [duration, event, self.entity_col, self.time_col]
        ]

        analyzer = SurvivalAnalyzer(
            data=self.data,
            duration_col=duration,
            event_col=event,
            covariates=covariates[:10],  # Limit covariates
        )

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

    def advanced_time_series_analysis(self, method: str = "kalman", **kwargs) -> SuiteResult:
        """
        Access advanced time series methods.

        Args:
            method: Advanced method ('kalman', 'markov_switching', 'dynamic_factor')
            **kwargs: Method-specific parameters

        Returns:
            SuiteResult with advanced time series results

        Examples:
            >>> result = suite.advanced_time_series_analysis(method='kalman')
        """
        from mcp_server.advanced_time_series import AdvancedTimeSeriesAnalyzer

        if self.target is None:
            raise ValueError("target column must be specified")

        analyzer = AdvancedTimeSeriesAnalyzer(self.data[self.target])

        if method == "kalman":
            result = analyzer.kalman_filter(**kwargs)
            return self._create_suite_result(
                method_category=MethodCategory.ADVANCED_TIME_SERIES,
                method_used="Kalman Filter",
                result=result,
                model=None,
                log_likelihood=result.log_likelihood,
            )
        else:
            raise ValueError(f"Unknown advanced time series method: {method}")

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
            category = spec['category']
            method = spec['method']
            params = spec.get('params', {})

            try:
                if category == 'time_series':
                    result = self.time_series_analysis(method=method, **params)
                elif category == 'panel':
                    result = self.panel_analysis(method=method, **params)
                elif category == 'causal':
                    result = self.causal_analysis(method=method, **params)
                elif category == 'survival':
                    result = self.survival_analysis(method=method, **params)
                elif category == 'bayesian':
                    result = self.bayesian_analysis(method=method, **params)
                elif category == 'advanced_time_series':
                    result = self.advanced_time_series_analysis(method=method, **params)
                else:
                    logger.warning(f"Unknown category: {category}")
                    continue

                results.append(
                    {
                        'method': result.method_used,
                        'aic': result.aic,
                        'bic': result.bic,
                        'r_squared': result.r_squared,
                        'log_likelihood': result.log_likelihood,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to run {category}/{method}: {e}")
                continue

        comparison_df = pd.DataFrame(results)

        # Add ranking column
        if metric in comparison_df.columns and comparison_df[metric].notna().any():
            # Lower is better for AIC/BIC, higher is better for R²
            ascending = metric in ['aic', 'bic']
            comparison_df['rank'] = comparison_df[metric].rank(ascending=ascending)
            comparison_df = comparison_df.sort_values('rank')

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
        suite_result = SuiteResult(
            data_structure=self.characteristics.structure,
            method_category=method_category,
            method_used=method_used,
            result=result,
            model=model,
            n_obs=len(self.data),
            **kwargs,
        )

        # Log to MLflow
        if self.mlflow_experiment and MLFLOW_AVAILABLE:
            metrics = {}
            if suite_result.aic is not None:
                metrics['aic'] = suite_result.aic
            if suite_result.bic is not None:
                metrics['bic'] = suite_result.bic
            if suite_result.r_squared is not None:
                metrics['r_squared'] = suite_result.r_squared
            if suite_result.log_likelihood is not None:
                metrics['log_likelihood'] = suite_result.log_likelihood

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
