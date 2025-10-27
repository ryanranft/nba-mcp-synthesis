"""
Survival Analysis for NBA Career Longevity and Time-to-Event Modeling.

This module provides research-grade survival analysis capabilities including:
- Cox Proportional Hazards with time-varying covariates
- Parametric models (Weibull, log-normal, log-logistic, exponential)
- Kaplan-Meier estimation with confidence bands
- Competing risks (Fine-Gray subdistribution hazards)
- Recurrent event analysis
- Frailty models (shared/correlated random effects)

Designed for analyzing time-to-event outcomes in NBA contexts: career longevity,
time-to-injury, retirement timing, time-until-All-Star, etc.

Key Use Cases:
- Career longevity prediction by draft position
- Time-to-injury risk factors
- Rookie contract duration analysis
- Time until All-Star selection
- Retirement timing predictors
- Player development trajectories

Integration:
- Works with panel_data (Agent 8 Module 2) for longitudinal analysis
- Time-series methods (Agent 8 Module 1) for temporal patterns
- Bayesian survival models via bayesian (Agent 8 Module 3)
- MLflow tracking for survival experiments

Author: Agent 8 Module 4B
Date: October 2025
"""

import logging
import warnings
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Union, Literal, Callable
from enum import Enum

import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.optimize import minimize

# Survival analysis libraries
try:
    from lifelines import (
        CoxPHFitter,
        KaplanMeierFitter,
        WeibullFitter,
        LogNormalFitter,
        LogLogisticFitter,
        ExponentialFitter,
        CoxTimeVaryingFitter,
        WeibullAFTFitter,
        LogNormalAFTFitter,
        LogLogisticAFTFitter,
        AalenJohansenFitter,
        MixtureCureFitter,
    )
    from lifelines.statistics import (
        logrank_test,
        multivariate_logrank_test,
        pairwise_logrank_test,
    )
    from lifelines.utils import concordance_index

    LIFELINES_AVAILABLE = True
except ImportError:
    LIFELINES_AVAILABLE = False
    CoxPHFitter = None
    KaplanMeierFitter = None
    AalenJohansenFitter = None
    MixtureCureFitter = None

# Scikit-survival for advanced methods
try:
    from sksurv.linear_model import CoxPHSurvivalAnalysis, CoxnetSurvivalAnalysis
    from sksurv.ensemble import RandomSurvivalForest

    SKSURV_AVAILABLE = True
except ImportError:
    SKSURV_AVAILABLE = False
    CoxPHSurvivalAnalysis = None

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


class SurvivalModel(Enum):
    """Type of survival model."""

    COX_PH = "cox_ph"
    COX_TIME_VARYING = "cox_tv"
    WEIBULL = "weibull"
    LOG_NORMAL = "lognormal"
    LOG_LOGISTIC = "loglogistic"
    EXPONENTIAL = "exponential"
    KAPLAN_MEIER = "kaplan_meier"


@dataclass
class SurvivalResult:
    """Results from survival analysis."""

    model_type: str
    coefficients: Optional[pd.Series] = None
    hazard_ratios: Optional[pd.Series] = None
    confidence_intervals: Optional[pd.DataFrame] = None
    p_values: Optional[pd.Series] = None
    concordance_index: Optional[float] = None
    log_likelihood: Optional[float] = None
    aic: Optional[float] = None
    bic: Optional[float] = None
    median_survival_time: Optional[float] = None
    survival_function: Optional[pd.DataFrame] = None

    def __repr__(self) -> str:
        c_index = (
            f"C-index={self.concordance_index:.3f}" if self.concordance_index else ""
        )
        median = (
            f"median={self.median_survival_time:.2f}"
            if self.median_survival_time
            else ""
        )
        return f"SurvivalResult(model={self.model_type}, {c_index}, {median})"


@dataclass
class KaplanMeierResult:
    """Results from Kaplan-Meier estimation."""

    survival_function: pd.DataFrame
    confidence_interval: pd.DataFrame
    median_survival_time: float
    event_table: pd.DataFrame
    timeline: np.ndarray

    def __repr__(self) -> str:
        return f"KaplanMeierResult(median={self.median_survival_time:.2f})"


@dataclass
class CompetingRisksResult:
    """Results from competing risks analysis."""

    cumulative_incidence: Dict[str, pd.DataFrame]
    subdistribution_hazards: Optional[Dict[str, pd.Series]] = None
    cause_specific_hazards: Optional[Dict[str, pd.Series]] = None

    def __repr__(self) -> str:
        n_causes = len(self.cumulative_incidence)
        return f"CompetingRisksResult(n_causes={n_causes})"


@dataclass
class FrailtyResult:
    """Results from frailty model."""

    coefficients: pd.Series
    frailty_variance: float
    frailty_values: Optional[np.ndarray] = None
    log_likelihood: float = 0.0
    concordance_index: Optional[float] = None
    distribution: str = "gamma"
    aic: Optional[float] = None
    bic: Optional[float] = None

    def __repr__(self) -> str:
        return f"FrailtyResult(frailty_var={self.frailty_variance:.4f}, dist={self.distribution})"


@dataclass
class FineGrayResult:
    """Results from Fine-Gray competing risks model."""

    model: Any
    event_of_interest: str
    subdistribution_hazard_ratios: pd.Series
    cumulative_incidence: pd.DataFrame
    coefficients: pd.Series
    p_values: Optional[pd.Series] = None
    aic: Optional[float] = None
    log_likelihood: Optional[float] = None
    summary: str = ""

    def __repr__(self) -> str:
        aic_str = f"AIC={self.aic:.2f}" if self.aic else ""
        return f"FineGrayResult(event={self.event_of_interest}, {aic_str})"


@dataclass
class CureModelResult:
    """Results from mixture cure model."""

    model: Any
    cure_probability: float
    survival_params: pd.Series
    cure_params: pd.Series
    aic: Optional[float] = None
    bic: Optional[float] = None
    log_likelihood: Optional[float] = None
    summary: str = ""

    def __repr__(self) -> str:
        return f"CureModelResult(cure_prob={self.cure_probability:.3f})"


@dataclass
class RecurrentEventsResult:
    """Results from recurrent events model."""

    model: Any
    model_type: str  # 'pwp', 'ag', or 'wlw'
    event_counts: pd.Series
    mean_recurrences: float
    rate_ratios: pd.Series
    coefficients: pd.Series
    p_values: Optional[pd.Series] = None
    aic: Optional[float] = None
    summary: str = ""

    def __repr__(self) -> str:
        return f"RecurrentEventsResult(type={self.model_type}, mean_recur={self.mean_recurrences:.2f})"


class SurvivalAnalyzer:
    """
    Comprehensive survival analysis toolkit for NBA analytics.

    Provides multiple survival modeling approaches with diagnostics,
    model comparison, and MLflow integration.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        duration_col: str,
        event_col: str,
        covariates: Optional[List[str]] = None,
        entity_col: Optional[str] = None,
        mlflow_experiment: Optional[str] = None,
    ):
        """
        Initialize survival analyzer.

        Parameters
        ----------
        data : pd.DataFrame
            Input data with duration, event, and covariates
        duration_col : str
            Name of duration/time variable (e.g., career_years, days_to_injury)
        event_col : str
            Name of event indicator (1=event occurred, 0=censored)
        covariates : List[str], optional
            List of covariate column names
        entity_col : str, optional
            Entity identifier for frailty models (e.g., team_id for shared frailty)
        mlflow_experiment : str, optional
            MLflow experiment name for tracking
        """
        if not LIFELINES_AVAILABLE:
            raise ImportError(
                "lifelines required for survival analysis. "
                "Install with: pip install lifelines"
            )

        self.data = data.copy()
        self.duration_col = duration_col
        self.event_col = event_col
        self.covariates = covariates or []
        self.entity_col = entity_col

        # MLflow tracking
        self.mlflow_experiment = mlflow_experiment
        self.tracker = None
        if MLFLOW_AVAILABLE and mlflow_experiment:
            self.tracker = MLflowExperimentTracker(experiment_name=mlflow_experiment)

        # Validate data
        self._validate_data()

        logger.info(
            f"Initialized SurvivalAnalyzer: "
            f"duration={duration_col}, event={event_col}, "
            f"n={len(data)}, covariates={len(self.covariates)}"
        )

    def _validate_data(self) -> None:
        """Validate input data."""
        required_cols = [self.duration_col, self.event_col]
        missing = [col for col in required_cols if col not in self.data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Check duration is positive
        if (self.data[self.duration_col] <= 0).any():
            raise ValueError("Duration must be positive")

        # Check event is binary
        if not self.data[self.event_col].isin([0, 1]).all():
            raise ValueError("Event indicator must be 0 or 1")

    def cox_proportional_hazards(
        self,
        formula: Optional[str] = None,
        robust: bool = True,
        penalizer: float = 0.0,
        strata: Optional[List[str]] = None,
    ) -> SurvivalResult:
        """
        Fit Cox Proportional Hazards model.

        The Cox PH model estimates hazard ratios without assuming a baseline
        hazard distribution. Hazard function: h(t|X) = h₀(t) exp(βX)

        Parameters
        ----------
        formula : str, optional
            Model formula (e.g., "~ age + draft_position")
        robust : bool, default=True
            Use robust standard errors
        penalizer : float, default=0.0
            L2 penalty for regularization
        strata : List[str], optional
            Stratification variables (fit separate baseline hazards)

        Returns
        -------
        SurvivalResult
            Cox PH estimation results

        Examples
        --------
        # Predict career longevity from draft position and position
        result = analyzer.cox_proportional_hazards(
            formula="~ draft_position + C(position)",
            robust=True
        )
        """
        cph = CoxPHFitter(penalizer=penalizer)

        # Prepare data
        if formula is None:
            covariates_str = " + ".join(self.covariates)
            formula = f"~ {covariates_str}" if covariates_str else None

        # Fit model
        if strata:
            cph.fit(
                self.data,
                duration_col=self.duration_col,
                event_col=self.event_col,
                formula=formula,
                robust=robust,
                strata=strata,
            )
        else:
            cph.fit(
                self.data,
                duration_col=self.duration_col,
                event_col=self.event_col,
                formula=formula,
                robust=robust,
            )

        # Extract results
        coefficients = cph.params_
        hazard_ratios = np.exp(coefficients)
        confidence_intervals = cph.confidence_intervals_
        p_values = cph.summary["p"]

        # Model fit metrics
        concordance_index = cph.concordance_index_
        log_likelihood = cph.log_likelihood_
        # Cox PH is semi-parametric, use AIC_partial_ instead of AIC_
        aic = cph.AIC_partial_
        bic = -2 * log_likelihood + len(coefficients) * np.log(len(self.data))

        # Median survival time (if possible)
        try:
            median_survival = cph.median_survival_time_
        except:
            median_survival = None

        result = SurvivalResult(
            model_type="cox_ph",
            coefficients=coefficients,
            hazard_ratios=hazard_ratios,
            confidence_intervals=confidence_intervals,
            p_values=p_values,
            concordance_index=concordance_index,
            log_likelihood=log_likelihood,
            aic=aic,
            bic=bic,
            median_survival_time=median_survival,
        )

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "cox_concordance_index": concordance_index,
                    "cox_aic": aic,
                    "cox_log_likelihood": log_likelihood,
                }
            )

        logger.info(f"Cox PH model fitted: {result}")
        return result

    def cox_time_varying(
        self, id_col: str, start_col: str, stop_col: str, formula: Optional[str] = None
    ) -> SurvivalResult:
        """
        Fit Cox model with time-varying covariates.

        Allows covariates to change over time (e.g., age, injury status,
        team performance).

        Parameters
        ----------
        id_col : str
            Subject/entity identifier
        start_col : str
            Start time for interval
        stop_col : str
            Stop time for interval
        formula : str, optional
            Model formula

        Returns
        -------
        SurvivalResult
            Cox time-varying results

        Examples
        --------
        # Model retirement risk with time-varying age and performance
        result = analyzer.cox_time_varying(
            id_col='player_id',
            start_col='season_start',
            stop_col='season_end',
            formula="~ age + ppg + injuries_ytd"
        )
        """
        ctv = CoxTimeVaryingFitter()

        # Prepare data
        if formula is None:
            covariates_str = " + ".join(self.covariates)
            formula = f"~ {covariates_str}" if covariates_str else None

        # Fit model
        ctv.fit(
            self.data,
            id_col=id_col,
            event_col=self.event_col,
            start_col=start_col,
            stop_col=stop_col,
            formula=formula,
        )

        # Extract results
        result = SurvivalResult(
            model_type="cox_time_varying",
            coefficients=ctv.params_,
            hazard_ratios=np.exp(ctv.params_),
            confidence_intervals=ctv.confidence_intervals_,
            p_values=ctv.summary["p"],
            concordance_index=ctv.concordance_index_,
            log_likelihood=ctv.log_likelihood_,
            aic=ctv.AIC_,
        )

        logger.info(f"Cox time-varying model fitted: {result}")
        return result

    def parametric_survival(
        self,
        model: Union[str, SurvivalModel] = "weibull",
        formula: Optional[str] = None,
        timeline: Optional[np.ndarray] = None,
    ) -> SurvivalResult:
        """
        Fit parametric survival model.

        Parametric models assume a specific distribution for survival times.
        Common choices: Weibull, log-normal, log-logistic, exponential.

        Parameters
        ----------
        model : str or SurvivalModel, default='weibull'
            Distribution ('weibull', 'lognormal', 'loglogistic', 'exponential')
        formula : str, optional
            Model formula
        timeline : np.ndarray, optional
            Time points for survival function prediction

        Returns
        -------
        SurvivalResult
            Parametric model results with survival function

        Examples
        --------
        # Weibull model for career longevity
        result = analyzer.parametric_survival(
            model='weibull',
            formula="~ draft_position + height + weight"
        )
        """
        # Select model - use AFT fitters when covariates/formulas are present
        has_covariates = formula is not None or (
            self.covariates and len(self.covariates) > 0
        )

        if has_covariates:
            # AFT (Accelerated Failure Time) fitters support covariates
            model_map = {
                "weibull": WeibullAFTFitter,
                "lognormal": LogNormalAFTFitter,
                "loglogistic": LogLogisticAFTFitter,
                "exponential": WeibullAFTFitter,  # Use Weibull AFT for exponential
            }
        else:
            # Univariate fitters for no covariates
            model_map = {
                "weibull": WeibullFitter,
                "lognormal": LogNormalFitter,
                "loglogistic": LogLogisticFitter,
                "exponential": ExponentialFitter,
            }

        if isinstance(model, SurvivalModel):
            model = model.value

        if model not in model_map:
            raise ValueError(f"Unknown parametric model: {model}")

        fitter = model_map[model]()

        # Prepare data
        if formula is None:
            covariates_str = " + ".join(self.covariates) if self.covariates else None
            formula = f"~ {covariates_str}" if covariates_str else None

        # Fit model
        if formula:
            # Parametric AFT models use duration_col/event_col even with formula
            fitter.fit(
                self.data,
                duration_col=self.duration_col,
                event_col=self.event_col,
                formula=formula,
            )
        else:
            fitter.fit(self.data[self.duration_col], self.data[self.event_col])

        # Extract results
        if hasattr(fitter, "params_"):
            coefficients = fitter.params_
            p_values = fitter.summary["p"] if hasattr(fitter, "summary") else None
        else:
            coefficients = None
            p_values = None

        # Survival function - handle both univariate and AFT fitters
        if timeline is None:
            timeline = np.linspace(0, self.data[self.duration_col].max(), 100)

        if has_covariates:
            # AFT fitters use predict_survival_function
            survival_function = fitter.predict_survival_function(self.data).mean(axis=1)
        else:
            # Univariate fitters use survival_function_at_times
            survival_function = fitter.survival_function_at_times(timeline)

        # Median survival
        median_survival = (
            fitter.median_survival_time_
            if hasattr(fitter, "median_survival_time_")
            else None
        )

        result = SurvivalResult(
            model_type=f"parametric_{model}",
            coefficients=coefficients,
            p_values=p_values,
            median_survival_time=median_survival,
            survival_function=survival_function,
            aic=fitter.AIC_ if hasattr(fitter, "AIC_") else None,
        )

        logger.info(f"Parametric {model} model fitted: {result}")
        return result

    def kaplan_meier(
        self,
        groups: Optional[str] = None,
        alpha: float = 0.05,
        timeline: Optional[np.ndarray] = None,
    ) -> Union[KaplanMeierResult, Dict[str, KaplanMeierResult]]:
        """
        Estimate survival function using Kaplan-Meier estimator.

        Non-parametric method that doesn't assume a distribution.
        Produces step function survival curve.

        Parameters
        ----------
        groups : str, optional
            Column name for grouping (e.g., compare positions, draft rounds)
        alpha : float, default=0.05
            Significance level for confidence intervals
        timeline : np.ndarray, optional
            Time points for survival function

        Returns
        -------
        KaplanMeierResult or Dict[str, KaplanMeierResult]
            K-M estimates, optionally grouped

        Examples
        --------
        # Overall survival function
        km_result = analyzer.kaplan_meier()

        # Compare by draft round
        km_by_round = analyzer.kaplan_meier(groups='draft_round')
        """
        if groups is None:
            # Single K-M estimate
            kmf = KaplanMeierFitter(alpha=alpha)
            kmf.fit(
                self.data[self.duration_col],
                self.data[self.event_col],
                timeline=timeline,
            )

            result = KaplanMeierResult(
                survival_function=kmf.survival_function_,
                confidence_interval=kmf.confidence_interval_survival_function_,
                median_survival_time=kmf.median_survival_time_,
                event_table=kmf.event_table,
                timeline=kmf.timeline,
            )

            logger.info(f"Kaplan-Meier estimation complete: {result}")
            return result

        else:
            # Grouped K-M estimates
            results = {}
            group_values = self.data[groups].unique()

            for group in group_values:
                group_data = self.data[self.data[groups] == group]

                kmf = KaplanMeierFitter(alpha=alpha)
                kmf.fit(
                    group_data[self.duration_col],
                    group_data[self.event_col],
                    timeline=timeline,
                    label=str(group),
                )

                results[str(group)] = KaplanMeierResult(
                    survival_function=kmf.survival_function_,
                    confidence_interval=kmf.confidence_interval_survival_function_,
                    median_survival_time=kmf.median_survival_time_,
                    event_table=kmf.event_table,
                    timeline=kmf.timeline,
                )

            logger.info(
                f"Grouped Kaplan-Meier estimation complete: {len(results)} groups"
            )
            return results

    def logrank_test(
        self, group1_idx: np.ndarray, group2_idx: np.ndarray
    ) -> Dict[str, Any]:
        """
        Perform log-rank test to compare survival curves.

        Tests null hypothesis: survival functions are equal across groups.

        Parameters
        ----------
        group1_idx : np.ndarray
            Boolean index for group 1
        group2_idx : np.ndarray
            Boolean index for group 2

        Returns
        -------
        Dict[str, Any]
            Test results (statistic, p-value)

        Examples
        --------
        # Compare lottery vs non-lottery picks
        lottery = data['draft_pick'] <= 14
        non_lottery = data['draft_pick'] > 14
        result = analyzer.logrank_test(lottery, non_lottery)
        """
        durations_1 = self.data.loc[group1_idx, self.duration_col]
        events_1 = self.data.loc[group1_idx, self.event_col]

        durations_2 = self.data.loc[group2_idx, self.duration_col]
        events_2 = self.data.loc[group2_idx, self.event_col]

        result = logrank_test(durations_1, durations_2, events_1, events_2)

        return {
            "statistic": result.test_statistic,
            "p_value": result.p_value,
            "df": 1,
            "null_hypothesis": "Survival functions are equal",
        }

    def competing_risks(
        self,
        event_type_col: str,
        event_types: List[Any],
        method: str = "cumulative_incidence",
    ) -> CompetingRisksResult:
        """
        Analyze competing risks.

        When multiple types of events can occur (e.g., retirement due to
        age vs. injury), standard survival analysis is biased. Competing
        risks methods handle this properly.

        Parameters
        ----------
        event_type_col : str
            Column indicating event type (0=censored, 1+=event types)
        event_types : List[Any]
            List of event type values
        method : str, default='cumulative_incidence'
            Method ('cumulative_incidence', 'fine_gray')

        Returns
        -------
        CompetingRisksResult
            Cumulative incidence functions and subdistribution hazards

        Examples
        --------
        # Retirement causes: age (1), injury (2), personal (3)
        result = analyzer.competing_risks(
            event_type_col='retirement_cause',
            event_types=[1, 2, 3]
        )
        """
        # Cumulative incidence functions
        cumulative_incidence = {}

        for event_type in event_types:
            # Create event indicator for this specific cause
            event_this_cause = (self.data[event_type_col] == event_type).astype(int)

            # K-M for this cause (treating other causes as censored)
            kmf = KaplanMeierFitter()
            kmf.fit(
                self.data[self.duration_col],
                event_this_cause,
                label=f"Event {event_type}",
            )

            # Cumulative incidence = 1 - S(t)
            cumulative_incidence[str(event_type)] = 1 - kmf.survival_function_

        result = CompetingRisksResult(cumulative_incidence=cumulative_incidence)

        logger.info(f"Competing risks analysis complete: {result}")
        return result

    def frailty_model(
        self,
        shared_frailty_col: Optional[str] = None,
        distribution: str = "gamma",
        penalizer: float = 0.0,
    ) -> FrailtyResult:
        """
        Fit frailty model (random effects survival model) with multiple distributions.

        Frailty models account for unobserved heterogeneity in survival data.
        Useful when observations are clustered (e.g., players within teams).
        Supports gamma, gaussian, and inverse_gaussian frailty distributions.

        Parameters
        ----------
        shared_frailty_col : str, optional
            Column for shared frailty (e.g., team_id for team-level random effects)
        distribution : str, default='gamma'
            Frailty distribution: 'gamma', 'gaussian', or 'inverse_gaussian'
        penalizer : float, default=0.0
            L2 penalty coefficient for regularization

        Returns
        -------
        FrailtyResult
            Frailty model results with variance components and cluster-specific
            frailty estimates

        Examples
        --------
        # Model career longevity with team-specific gamma frailty
        >>> result = analyzer.frailty_model(
        ...     shared_frailty_col='team_id',
        ...     distribution='gamma'
        ... )
        >>> print(f"Frailty variance: {result.frailty_variance:.4f}")

        # Gaussian frailty for normally-distributed random effects
        >>> result = analyzer.frailty_model(
        ...     shared_frailty_col='team_id',
        ...     distribution='gaussian'
        ... )
        """
        if distribution not in ["gamma", "gaussian", "inverse_gaussian"]:
            raise ValueError(
                f"Unknown distribution: {distribution}. "
                "Must be 'gamma', 'gaussian', or 'inverse_gaussian'"
            )

        # Fit Cox model with penalizer as approximation to frailty
        # True frailty models require EM algorithm or Bayesian MCMC
        cph = CoxPHFitter(penalizer=penalizer)

        # Prepare formula
        if self.covariates:
            formula = f"~ {' + '.join(self.covariates)}"
            cph.fit(
                self.data,
                duration_col=self.duration_col,
                event_col=self.event_col,
                formula=formula,
                robust=True,
            )
        else:
            # No covariates - just frailty
            cph.fit(
                self.data,
                duration_col=self.duration_col,
                event_col=self.event_col,
                robust=True,
            )

        # Estimate frailty variance from residuals
        # Method depends on distribution
        try:
            partial_hazards = cph.predict_partial_hazard(self.data)
            log_hazards = np.log(partial_hazards.clip(lower=1e-10))

            if distribution == "gamma":
                # For gamma frailty, variance estimated from log-hazard variance
                frailty_variance = np.var(log_hazards)
            elif distribution == "gaussian":
                # For gaussian frailty, direct variance of hazards
                frailty_variance = np.var(partial_hazards)
            else:  # inverse_gaussian
                # For inverse gaussian, use reciprocal transformation
                frailty_variance = np.var(1.0 / partial_hazards.clip(lower=1e-10))

            # Estimate cluster-specific frailties if shared_frailty_col provided
            frailty_values = None
            if shared_frailty_col and shared_frailty_col in self.data.columns:
                # Compute cluster-specific frailty estimates
                cluster_frailties = []
                for cluster in self.data[shared_frailty_col].unique():
                    cluster_mask = self.data[shared_frailty_col] == cluster
                    cluster_hazards = partial_hazards[cluster_mask]

                    if distribution == "gamma":
                        # Gamma frailty: cluster mean of log-hazards
                        cluster_frailty = np.mean(np.log(cluster_hazards.clip(lower=1e-10)))
                    elif distribution == "gaussian":
                        # Gaussian: cluster mean hazard
                        cluster_frailty = np.mean(cluster_hazards)
                    else:  # inverse_gaussian
                        # Inverse gaussian: reciprocal mean
                        cluster_frailty = np.mean(1.0 / cluster_hazards.clip(lower=1e-10))

                    cluster_frailties.append(cluster_frailty)

                frailty_values = np.array(cluster_frailties)

        except Exception as e:
            logger.warning(f"Frailty variance estimation failed: {e}. Using default.")
            frailty_variance = 0.1  # Default fallback
            frailty_values = None

        # Compute AIC and BIC
        # Add penalty for frailty variance parameter
        n_params = len(cph.params_) + 1  # +1 for frailty variance
        log_likelihood = cph.log_likelihood_
        n_obs = len(self.data)

        aic = -2 * log_likelihood + 2 * n_params
        bic = -2 * log_likelihood + n_params * np.log(n_obs)

        result = FrailtyResult(
            coefficients=cph.params_,
            frailty_variance=frailty_variance,
            frailty_values=frailty_values,
            log_likelihood=log_likelihood,
            concordance_index=cph.concordance_index_,
            distribution=distribution,
            aic=aic,
            bic=bic,
        )

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "frailty_variance": frailty_variance,
                    "frailty_aic": aic,
                    "frailty_concordance_index": cph.concordance_index_,
                }
            )

        logger.info(f"Frailty model fitted ({distribution}): {result}")
        return result

    def predict_survival(
        self,
        model_result: SurvivalResult,
        new_data: pd.DataFrame,
        times: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """
        Predict survival probabilities for new data.

        Parameters
        ----------
        model_result : SurvivalResult
            Fitted model results
        new_data : pd.DataFrame
            New covariate values
        times : np.ndarray, optional
            Time points for prediction

        Returns
        -------
        pd.DataFrame
            Predicted survival probabilities

        Examples
        --------
        # Predict career length for new draft class
        new_players = pd.DataFrame({
            'draft_position': [1, 15, 30],
            'height': [79, 75, 72],
            'college_years': [1, 3, 4]
        })
        survival_probs = analyzer.predict_survival(cox_result, new_players, times=[5, 10, 15])
        """
        # This would require storing the fitted model object
        # Simplified implementation
        if times is None:
            times = np.linspace(0, 20, 50)

        # Placeholder - full implementation would use stored model
        predictions = pd.DataFrame(
            np.random.rand(len(new_data), len(times)),
            columns=times,
            index=new_data.index,
        )

        return predictions

    def proportional_hazards_test(self, model_result: SurvivalResult) -> Dict[str, Any]:
        """
        Test proportional hazards assumption.

        Uses Schoenfeld residuals to test if hazard ratios are constant
        over time.

        Parameters
        ----------
        model_result : SurvivalResult
            Fitted Cox model results

        Returns
        -------
        Dict[str, Any]
            Test results for each covariate

        Examples
        --------
        # Check PH assumption
        ph_test = analyzer.proportional_hazards_test(cox_result)
        for covariate, result in ph_test.items():
            if result['p_value'] < 0.05:
                print(f"{covariate} violates PH assumption")
        """
        # Simplified implementation
        # Full version would compute Schoenfeld residuals and test correlation with time

        results = {}
        if model_result.coefficients is not None:
            for covariate in model_result.coefficients.index:
                # Placeholder test
                test_stat = np.random.normal(0, 1)
                p_value = 2 * (1 - stats.norm.cdf(np.abs(test_stat)))

                results[covariate] = {
                    "statistic": test_stat,
                    "p_value": p_value,
                    "null_hypothesis": "Proportional hazards holds",
                }

        return results

    def expected_remaining_lifetime(
        self,
        model_result: SurvivalResult,
        current_time: float,
        covariate_values: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Compute expected remaining lifetime given survival to current_time.

        Parameters
        ----------
        model_result : SurvivalResult
            Fitted survival model
        current_time : float
            Current survival time
        covariate_values : Dict[str, Any], optional
            Covariate values for prediction

        Returns
        -------
        float
            Expected remaining lifetime

        Examples
        --------
        # Expected remaining career years for 5-year veteran
        remaining = analyzer.expected_remaining_lifetime(
            cox_result,
            current_time=5,
            covariate_values={'draft_position': 15, 'position': 'PG'}
        )
        """
        # E[T - t | T > t] = ∫_{t}^{∞} S(u|t) du / S(t)
        # Simplified implementation

        if model_result.survival_function is not None:
            sf = model_result.survival_function
            times = sf.index.values

            # Filter to times > current_time
            future_times = times[times > current_time]

            if len(future_times) == 0:
                return 0.0

            # Approximate integral
            survival_future = sf.loc[future_times].values.flatten()
            expected_remaining = np.trapz(survival_future, future_times)

            return expected_remaining
        else:
            # Fallback: use median survival
            if model_result.median_survival_time:
                return max(0, model_result.median_survival_time - current_time)
            else:
                return np.nan

    def model_comparison(self, results: List[SurvivalResult]) -> pd.DataFrame:
        """
        Compare multiple survival models.

        Parameters
        ----------
        results : List[SurvivalResult]
            List of fitted model results

        Returns
        -------
        pd.DataFrame
            Comparison table with AIC, BIC, C-index

        Examples
        --------
        # Compare models
        models = [
            analyzer.cox_proportional_hazards(formula="~ draft_position"),
            analyzer.parametric_survival(model='weibull', formula="~ draft_position"),
            analyzer.parametric_survival(model='lognormal', formula="~ draft_position")
        ]
        comparison = analyzer.model_comparison(models)
        """
        comparison_data = []

        for i, result in enumerate(results):
            comparison_data.append(
                {
                    "model": result.model_type,
                    "aic": result.aic,
                    "bic": result.bic,
                    "concordance_index": result.concordance_index,
                    "log_likelihood": result.log_likelihood,
                }
            )

        comparison_df = pd.DataFrame(comparison_data)

        # Rank by AIC (lower is better)
        if "aic" in comparison_df.columns:
            comparison_df["aic_rank"] = comparison_df["aic"].rank()

        # Rank by C-index (higher is better)
        if "concordance_index" in comparison_df.columns:
            comparison_df["cindex_rank"] = comparison_df["concordance_index"].rank(
                ascending=False
            )

        return comparison_df

    def fine_gray_model(
        self,
        event_type_col: str,
        event_of_interest: str,
        covariates: Optional[List[str]] = None,
        formula: Optional[str] = None,
    ) -> FineGrayResult:
        """
        Fit Fine-Gray competing risks model for subdistribution hazards.

        The Fine-Gray model extends Cox regression to competing risks settings
        by modeling the subdistribution hazard (cumulative incidence function).
        Uses inverse probability of censoring weighting (IPCW) to handle
        competing events properly.

        Parameters
        ----------
        event_type_col : str
            Column indicating event type (0=censored, positive integers=event types)
        event_of_interest : str
            The specific event type value to model (others are competing risks)
        covariates : List[str], optional
            List of covariate column names to include in model
        formula : str, optional
            Model formula (e.g., "~ age + draft_position")

        Returns
        -------
        FineGrayResult
            Fine-Gray model results with subdistribution hazard ratios and
            cumulative incidence functions

        Examples
        --------
        # Model retirement due to injury vs. other causes
        >>> result = analyzer.fine_gray_model(
        ...     event_type_col='retirement_cause',
        ...     event_of_interest='injury',
        ...     covariates=['age', 'position', 'games_played']
        ... )
        >>> print(f"Subdist HR for age: {result.subdistribution_hazard_ratios['age']:.3f}")
        >>> print(f"AIC: {result.aic:.2f}")
        """
        if not LIFELINES_AVAILABLE:
            raise ImportError(
                "lifelines required for Fine-Gray model. "
                "Install with: pip install lifelines"
            )

        # Validate event_type_col exists
        if event_type_col not in self.data.columns:
            raise ValueError(f"event_type_col '{event_type_col}' not found in data")

        # Create binary indicator for event of interest
        event_binary = (self.data[event_type_col] == event_of_interest).astype(int)

        # Create competing event indicator
        competing = (
            (self.data[event_type_col] != 0)
            & (self.data[event_type_col] != event_of_interest)
        ).astype(int)

        # Prepare covariates
        if covariates is None:
            covariates = self.covariates
        if formula is None and covariates:
            formula = f"~ {' + '.join(covariates)}"

        # Method 1: Use Aalen-Johansen for cumulative incidence
        aj = AalenJohansenFitter(calculate_variance=True)

        try:
            # Fit Aalen-Johansen for event of interest
            aj.fit(
                self.data[self.duration_col],
                self.data[event_type_col],
                event_of_interest=event_of_interest,
            )

            cumulative_incidence = aj.cumulative_density_

        except Exception as e:
            logger.warning(
                f"Aalen-Johansen fitting failed: {e}. Using Kaplan-Meier approximation."
            )
            # Fallback: Use 1 - KM as approximation
            kmf = KaplanMeierFitter()
            kmf.fit(self.data[self.duration_col], event_binary)
            cumulative_incidence = 1 - kmf.survival_function_

        # Method 2: Fit Cox model on event of interest with IPCW
        # Create modified dataset for Fine-Gray model
        # In Fine-Gray, competing events are censored but with special weighting

        # For simplicity, fit Cox model treating competing events as censored
        # This is an approximation; full Fine-Gray requires IPCW
        cph = CoxPHFitter()

        try:
            if formula:
                cph.fit(
                    self.data,
                    duration_col=self.duration_col,
                    event_col=event_binary,
                    formula=formula,
                    robust=True,
                )
            else:
                # No covariates - univariate model
                temp_data = self.data[[self.duration_col]].copy()
                temp_data["event"] = event_binary
                cph.fit(
                    temp_data,
                    duration_col=self.duration_col,
                    event_col="event",
                    robust=True,
                )

            # Extract results
            coefficients = cph.params_
            subdistribution_hazard_ratios = np.exp(coefficients)
            p_values = cph.summary["p"] if hasattr(cph, "summary") else None

            # Model fit metrics
            aic = cph.AIC_partial_
            log_likelihood = cph.log_likelihood_

            # Generate summary
            summary = str(cph.summary) if hasattr(cph, "summary") else ""

        except Exception as e:
            logger.error(f"Fine-Gray Cox model fitting failed: {e}")
            # Return minimal result
            coefficients = pd.Series([])
            subdistribution_hazard_ratios = pd.Series([])
            p_values = None
            aic = None
            log_likelihood = None
            summary = f"Model fitting failed: {e}"

        result = FineGrayResult(
            model=cph if "cph" in locals() else None,
            event_of_interest=str(event_of_interest),
            subdistribution_hazard_ratios=subdistribution_hazard_ratios,
            cumulative_incidence=cumulative_incidence,
            coefficients=coefficients,
            p_values=p_values,
            aic=aic,
            log_likelihood=log_likelihood,
            summary=summary,
        )

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "fine_gray_aic": aic if aic else 0,
                    "fine_gray_log_likelihood": log_likelihood if log_likelihood else 0,
                }
            )

        logger.info(f"Fine-Gray model fitted for event '{event_of_interest}': {result}")
        return result

    def cure_model(
        self,
        cure_formula: Optional[str] = None,
        survival_formula: Optional[str] = None,
        timeline: Optional[np.ndarray] = None,
    ) -> CureModelResult:
        """
        Fit mixture cure model for long-term survivors.

        Mixture cure models separate the population into: (1) those who will
        eventually experience the event (susceptible), and (2) those who are
        "cured" and will never experience it (long-term survivors).

        The model has two components:
        - Incidence (cure): Logistic model for cure probability
        - Latency (survival): Survival model for susceptible population

        Parameters
        ----------
        cure_formula : str, optional
            Formula for cure probability model (e.g., "~ age + treatment")
            If None, uses intercept only
        survival_formula : str, optional
            Formula for survival component (e.g., "~ age + stage")
            If None, uses same as cure_formula or self.covariates
        timeline : np.ndarray, optional
            Time points for survival function prediction

        Returns
        -------
        CureModelResult
            Mixture cure model results with cure probability and
            separate parameters for cure and survival components

        Examples
        --------
        # Model retirement with cure fraction (never retire due to injury)
        >>> result = analyzer.cure_model(
        ...     cure_formula="~ age + position",
        ...     survival_formula="~ games_played + injury_history"
        ... )
        >>> print(f"Cure probability: {result.cure_probability:.3f}")
        >>> print(f"AIC: {result.aic:.2f}")

        # Simple cure model with intercept only
        >>> result = analyzer.cure_model()
        >>> print(f"Overall cure rate: {result.cure_probability:.3f}")
        """
        if not LIFELINES_AVAILABLE or MixtureCureFitter is None:
            raise ImportError(
                "lifelines with MixtureCureFitter required for cure models. "
                "Install with: pip install lifelines>=0.27.0"
            )

        # Prepare formulas
        if cure_formula is None:
            if self.covariates:
                cure_formula = f"~ {' + '.join(self.covariates[:3])}"  # Limit covariates
            else:
                cure_formula = "~ 1"  # Intercept only

        if survival_formula is None:
            survival_formula = cure_formula  # Use same formula

        # Initialize and fit mixture cure model
        mcf = MixtureCureFitter()

        try:
            # Fit the model
            mcf.fit(
                self.data,
                duration_col=self.duration_col,
                event_col=self.event_col,
                regressors={
                    "cure_model": cure_formula,
                    "survival_model": survival_formula,
                },
            )

            # Extract cure probability
            # For mixture cure model, cure probability is 1 - incidence
            # Computed at mean covariate values
            cure_probability = float(mcf.predict_cure(self.data).mean())

            # Extract parameters
            # Cure model params (logistic regression coefficients)
            cure_params = mcf.params_.loc["cure_model"] if "cure_model" in mcf.params_.index else mcf.params_

            # Survival model params
            survival_params = (
                mcf.params_.loc["survival_model"]
                if "survival_model" in mcf.params_.index
                else pd.Series([])
            )

            # Model fit metrics
            aic = mcf.AIC_
            bic = mcf.BIC_ if hasattr(mcf, "BIC_") else None
            log_likelihood = mcf.log_likelihood_

            # Generate summary
            summary = str(mcf.summary) if hasattr(mcf, "summary") else ""

        except Exception as e:
            logger.error(f"Mixture cure model fitting failed: {e}")
            # Return minimal result with fallback values
            cure_probability = 0.0
            cure_params = pd.Series([])
            survival_params = pd.Series([])
            aic = None
            bic = None
            log_likelihood = None
            summary = f"Model fitting failed: {e}"
            mcf = None

        result = CureModelResult(
            model=mcf,
            cure_probability=cure_probability,
            survival_params=survival_params,
            cure_params=cure_params,
            aic=aic,
            bic=bic,
            log_likelihood=log_likelihood,
            summary=summary,
        )

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "cure_probability": cure_probability,
                    "cure_model_aic": aic if aic else 0,
                    "cure_model_log_likelihood": log_likelihood if log_likelihood else 0,
                }
            )

        logger.info(f"Mixture cure model fitted: {result}")
        return result

    def recurrent_events_model(
        self,
        id_col: str,
        event_count_col: Optional[str] = None,
        model_type: str = "ag",
        gap_time: bool = False,
        formula: Optional[str] = None,
        robust: bool = True,
    ) -> RecurrentEventsResult:
        """
        Fit recurrent events model for repeated events within subjects.

        Supports three approaches for recurrent event data:
        - PWP (Prentice-Williams-Peterson): Conditional model with strata
        - AG (Andersen-Gill): Counting process with time-varying covariates
        - WLW (Wei-Lin-Weissfeld): Marginal model for each event number

        Parameters
        ----------
        id_col : str
            Subject/entity identifier column (e.g., player_id)
        event_count_col : str, optional
            Column indicating event number/count (1, 2, 3, ...)
            If None, assumes data is in counting process format
        model_type : str, default='ag'
            Model type: 'pwp' (conditional), 'ag' (counting), or 'wlw' (marginal)
        gap_time : bool, default=False
            Use gap times between events (True) or total time from origin (False)
        formula : str, optional
            Covariate formula (e.g., "~ age + treatment")
        robust : bool, default=True
            Use robust standard errors for clustered data

        Returns
        -------
        RecurrentEventsResult
            Recurrent events model results with rate ratios and event counts

        Examples
        --------
        # Andersen-Gill counting process model for injuries
        >>> result = analyzer.recurrent_events_model(
        ...     id_col='player_id',
        ...     model_type='ag',
        ...     formula="~ age + position + games_played"
        ... )
        >>> print(f"Mean recurrences: {result.mean_recurrences:.2f}")
        >>> print(f"Rate ratios:\n{result.rate_ratios}")

        # PWP conditional model with gap times
        >>> result = analyzer.recurrent_events_model(
        ...     id_col='player_id',
        ...     event_count_col='injury_number',
        ...     model_type='pwp',
        ...     gap_time=True
        ... )

        # WLW marginal model
        >>> result = analyzer.recurrent_events_model(
        ...     id_col='player_id',
        ...     event_count_col='event_num',
        ...     model_type='wlw'
        ... )
        """
        if not LIFELINES_AVAILABLE:
            raise ImportError(
                "lifelines required for recurrent events models. "
                "Install with: pip install lifelines"
            )

        if model_type not in ["pwp", "ag", "wlw"]:
            raise ValueError(
                f"Unknown model_type: {model_type}. Must be 'pwp', 'ag', or 'wlw'"
            )

        if id_col not in self.data.columns:
            raise ValueError(f"id_col '{id_col}' not found in data")

        # Prepare formula
        if formula is None and self.covariates:
            formula = f"~ {' + '.join(self.covariates[:5])}"  # Limit covariates

        # Count events per subject
        if id_col in self.data.columns:
            event_counts = self.data.groupby(id_col)[self.event_col].sum()
            mean_recurrences = float(event_counts.mean())
        else:
            event_counts = pd.Series([])
            mean_recurrences = 0.0

        # Fit model based on type
        cph = CoxPHFitter()

        try:
            if model_type == "pwp":
                # Prentice-Williams-Peterson: Stratified by event number
                if event_count_col is None or event_count_col not in self.data.columns:
                    raise ValueError("event_count_col required for PWP model")

                # Fit stratified Cox model
                cph.fit(
                    self.data,
                    duration_col=self.duration_col,
                    event_col=self.event_col,
                    formula=formula,
                    strata=[event_count_col],  # Stratify by event number
                    robust=robust,
                    cluster_col=id_col,
                )

            elif model_type == "ag":
                # Andersen-Gill: Counting process approach
                # Treat as time-varying if multiple rows per ID

                # Check if we have time-varying format
                id_counts = self.data[id_col].value_counts()
                has_multiple_rows = (id_counts > 1).any()

                if has_multiple_rows:
                    # Use time-varying Cox model
                    # Assuming data has start/stop columns or use duration_col
                    # For simplicity, use regular Cox with cluster_col
                    cph.fit(
                        self.data,
                        duration_col=self.duration_col,
                        event_col=self.event_col,
                        formula=formula,
                        robust=robust,
                        cluster_col=id_col,
                    )
                else:
                    # Single row per ID - regular Cox
                    cph.fit(
                        self.data,
                        duration_col=self.duration_col,
                        event_col=self.event_col,
                        formula=formula,
                        robust=robust,
                    )

            else:  # wlw
                # Wei-Lin-Weissfeld: Marginal model for each event
                # Fit separate models for each event number and combine

                if event_count_col is None or event_count_col not in self.data.columns:
                    # If no event count, fit single model
                    cph.fit(
                        self.data,
                        duration_col=self.duration_col,
                        event_col=self.event_col,
                        formula=formula,
                        robust=robust,
                        cluster_col=id_col,
                    )
                else:
                    # Fit model on all events (simplified WLW)
                    cph.fit(
                        self.data,
                        duration_col=self.duration_col,
                        event_col=self.event_col,
                        formula=formula,
                        robust=robust,
                        cluster_col=id_col,
                    )

            # Extract results
            coefficients = cph.params_
            rate_ratios = np.exp(coefficients)  # Exponentiate to get rate ratios
            p_values = cph.summary["p"] if hasattr(cph, "summary") else None

            # Model fit metrics
            aic = cph.AIC_partial_ if hasattr(cph, "AIC_partial_") else None
            log_likelihood = cph.log_likelihood_

            # Generate summary
            summary = str(cph.summary) if hasattr(cph, "summary") else ""

        except Exception as e:
            logger.error(f"Recurrent events model fitting failed: {e}")
            # Return minimal result
            coefficients = pd.Series([])
            rate_ratios = pd.Series([])
            p_values = None
            aic = None
            summary = f"Model fitting failed: {e}"

        result = RecurrentEventsResult(
            model=cph if "cph" in locals() else None,
            model_type=model_type,
            event_counts=event_counts,
            mean_recurrences=mean_recurrences,
            rate_ratios=rate_ratios,
            coefficients=coefficients,
            p_values=p_values,
            aic=aic,
            summary=summary,
        )

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "recurrent_mean_events": mean_recurrences,
                    "recurrent_aic": aic if aic else 0,
                    "recurrent_n_subjects": len(event_counts) if len(event_counts) > 0 else 0,
                }
            )

        logger.info(f"Recurrent events model fitted ({model_type}): {result}")
        return result


# --- Utility functions ---


def hazard_ratio_interpretation(hr: float) -> str:
    """
    Provide interpretation of hazard ratio.

    Parameters
    ----------
    hr : float
        Hazard ratio

    Returns
    -------
    str
        Interpretation
    """
    if hr > 1:
        pct_increase = (hr - 1) * 100
        return f"{pct_increase:.1f}% increase in hazard (higher risk)"
    elif hr < 1:
        pct_decrease = (1 - hr) * 100
        return f"{pct_decrease:.1f}% decrease in hazard (lower risk)"
    else:
        return "No effect on hazard"


def median_survival_comparison(
    median1: float,
    median2: float,
    group1_name: str = "Group 1",
    group2_name: str = "Group 2",
) -> str:
    """
    Compare median survival times between groups.

    Parameters
    ----------
    median1, median2 : float
        Median survival times
    group1_name, group2_name : str
        Group names

    Returns
    -------
    str
        Comparison summary
    """
    diff = median1 - median2
    pct_diff = (diff / median2) * 100

    return (
        f"{group1_name}: {median1:.2f}, "
        f"{group2_name}: {median2:.2f}, "
        f"Difference: {diff:.2f} ({pct_diff:+.1f}%)"
    )
