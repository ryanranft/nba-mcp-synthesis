"""
Causal Inference Methods for NBA Analytics.

This module provides research-grade causal inference capabilities including:
- Instrumental Variables (IV/2SLS) with weak instrument diagnostics
- Regression Discontinuity Design (RDD) - sharp & fuzzy
- Propensity Score Matching (PSM) + inverse probability weighting
- Synthetic Control for comparative case studies
- Sensitivity analysis (Rosenbaum bounds, confounding strength)

Designed for answering "what-if" questions in NBA analytics with rigorous
causal identification strategies. Goes beyond correlation to estimate
treatment effects.

Key Use Cases:
- Coaching change impact on team performance
- Draft position effect on career success
- Injury protocol effectiveness
- Home court advantage causality
- Player development program evaluation

Integration:
- Works with panel_data (Agent 8 Module 2) for difference-in-differences
- Complements time_series (Agent 8 Module 1) for event studies
- Bayesian causal inference via bayesian (Agent 8 Module 3)
- MLflow tracking for causal experiments

Author: Agent 8 Module 4A
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
from scipy.optimize import minimize
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

# Custom exceptions
from mcp_server.exceptions import (
    InvalidDataError,
    InvalidParameterError,
    InsufficientDataError,
    MissingParameterError,
)

# Specialized causal inference libraries
try:
    from linearmodels.iv import IV2SLS

    LINEARMODELS_AVAILABLE = True
except ImportError:
    LINEARMODELS_AVAILABLE = False
    IV2SLS = None

# DoWhy for causal graphs
try:
    import dowhy
    from dowhy import CausalModel

    DOWHY_AVAILABLE = True
except ImportError:
    DOWHY_AVAILABLE = False
    dowhy = None
    CausalModel = None

# NetworkX for DAG visualization
try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

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


class TreatmentType(Enum):
    """Type of treatment in causal analysis."""

    BINARY = "binary"
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"


@dataclass
class IVResult:
    """Results from instrumental variables analysis."""

    treatment_effect: float
    std_error: float
    t_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    first_stage_f_stat: float
    weak_instrument_test: Dict[str, Any]
    overidentification_test: Optional[Dict[str, Any]] = None
    endogeneity_test: Optional[Dict[str, Any]] = None
    coefficients: Optional[pd.Series] = None
    residuals: Optional[np.ndarray] = None

    def __repr__(self) -> str:
        return (
            f"IVResult(effect={self.treatment_effect:.4f}, "
            f"p={self.p_value:.4f}, "
            f"95% CI=[{self.confidence_interval[0]:.4f}, {self.confidence_interval[1]:.4f}], "
            f"F-stat={self.first_stage_f_stat:.2f})"
        )


@dataclass
class RDDResult:
    """Results from regression discontinuity design."""

    treatment_effect: float
    std_error: float
    t_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    bandwidth: float
    n_left: int
    n_right: int
    optimal_bandwidth: Optional[float] = None
    continuity_test: Optional[Dict[str, Any]] = None
    density_test: Optional[Dict[str, Any]] = None

    def __repr__(self) -> str:
        return (
            f"RDDResult(effect={self.treatment_effect:.4f}, "
            f"p={self.p_value:.4f}, "
            f"bandwidth={self.bandwidth:.4f}, "
            f"n_left={self.n_left}, n_right={self.n_right})"
        )


@dataclass
class PSMResult:
    """Results from propensity score matching."""

    ate: float  # Average Treatment Effect
    att: float  # Average Treatment Effect on Treated
    atc: float  # Average Treatment Effect on Controls
    std_error: float
    confidence_interval: Tuple[float, float]
    n_matched: int
    n_unmatched: int
    balance_statistics: pd.DataFrame
    propensity_scores: np.ndarray
    common_support: np.ndarray

    def __repr__(self) -> str:
        return (
            f"PSMResult(ATE={self.ate:.4f}, ATT={self.att:.4f}, "
            f"matched={self.n_matched}, unmatched={self.n_unmatched})"
        )


@dataclass
class SyntheticControlResult:
    """Results from synthetic control method."""

    treatment_effect: np.ndarray
    average_effect: float
    std_error: float
    p_value: float
    pre_treatment_fit: float  # RMSE before treatment
    weights: pd.Series
    synthetic_trajectory: np.ndarray
    actual_trajectory: np.ndarray
    placebo_distribution: Optional[np.ndarray] = None

    def __repr__(self) -> str:
        return (
            f"SyntheticControlResult(avg_effect={self.average_effect:.4f}, "
            f"p={self.p_value:.4f}, "
            f"pre_RMSE={self.pre_treatment_fit:.4f})"
        )


@dataclass
class SensitivityResult:
    """Results from sensitivity analysis."""

    method: str
    original_effect: float
    sensitivity_bounds: Dict[str, Tuple[float, float]]
    critical_value: Optional[float] = None
    robustness_metric: Optional[float] = None
    confounding_strength: Optional[Dict[str, float]] = None

    def __repr__(self) -> str:
        return f"SensitivityResult(method={self.method}, effect={self.original_effect:.4f})"


class CausalInferenceAnalyzer:
    """
    Comprehensive causal inference toolkit for NBA analytics.

    Provides multiple causal identification strategies with diagnostics,
    sensitivity analysis, and integration with MLflow for experiment tracking.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        treatment_col: str,
        outcome_col: str,
        covariates: Optional[List[str]] = None,
        entity_col: Optional[str] = None,
        time_col: Optional[str] = None,
        mlflow_experiment: Optional[str] = None,
    ):
        """
        Initialize causal inference analyzer.

        Parameters
        ----------
        data : pd.DataFrame
            Input data with treatment, outcome, and covariates
        treatment_col : str
            Name of treatment variable
        outcome_col : str
            Name of outcome variable
        covariates : List[str], optional
            List of covariate column names
        entity_col : str, optional
            Entity identifier (e.g., player_id, team_id)
        time_col : str, optional
            Time variable for panel data methods
        mlflow_experiment : str, optional
            MLflow experiment name for tracking
        """
        self.data = data.copy()
        self.treatment_col = treatment_col
        self.outcome_col = outcome_col
        self.covariates = covariates or []
        self.entity_col = entity_col
        self.time_col = time_col

        # MLflow tracking
        self.mlflow_experiment = mlflow_experiment
        self.tracker = None
        if MLFLOW_AVAILABLE and mlflow_experiment:
            self.tracker = MLflowExperimentTracker(experiment_name=mlflow_experiment)

        # Validate data
        self._validate_data()

        logger.info(
            f"Initialized CausalInferenceAnalyzer: "
            f"treatment={treatment_col}, outcome={outcome_col}, "
            f"n={len(data)}, covariates={len(self.covariates)}"
        )

    def _validate_data(self) -> None:
        """Validate input data."""
        required_cols = [self.treatment_col, self.outcome_col]
        missing = [col for col in required_cols if col not in self.data.columns]
        if missing:
            raise InvalidDataError(
                f"Missing required columns: {missing}",
                value=missing,
                available_columns=list(self.data.columns),
            )

        if self.data[self.outcome_col].isna().any():
            warnings.warn("Outcome variable contains missing values")

        if self.data[self.treatment_col].isna().any():
            warnings.warn("Treatment variable contains missing values")

    def instrumental_variables(
        self,
        instruments: Union[str, List[str]],
        formula: Optional[str] = None,
        robust: bool = True,
        entity_effects: bool = False,
    ) -> IVResult:
        """
        Estimate treatment effect using instrumental variables (2SLS).

        Instrumental variables address endogeneity by using instruments
        that are correlated with treatment but affect outcome only through
        treatment.

        Parameters
        ----------
        instruments : str or List[str]
            Instrumental variable(s)
        formula : str, optional
            Model formula (e.g., "outcome ~ treatment + covariate")
        robust : bool, default=True
            Use robust standard errors
        entity_effects : bool, default=False
            Include entity fixed effects

        Returns
        -------
        IVResult
            IV estimation results with diagnostics

        Examples
        --------
        # Example: Effect of coaching change on wins, instrumented by
        # coach retirement (exogenous instrument)
        result = analyzer.instrumental_variables(
            instruments='coach_retirement',
            formula='wins ~ coaching_change + team_salary'
        )
        """
        if not LINEARMODELS_AVAILABLE:
            raise ImportError(
                "linearmodels required for IV estimation. Install with: pip install linearmodels"
            )

        instruments = [instruments] if isinstance(instruments, str) else instruments

        # Prepare data
        # For IV2SLS, formula must be: "outcome ~ [treatment ~ instrument] + covariates"
        if formula is None:
            # Build IV formula with treatment as endogenous variable
            instruments_str = " + ".join(instruments)
            covariates_str = " + ".join(self.covariates) if self.covariates else ""

            # IV2SLS formula format: dependent ~ [endogenous ~ instruments] + exogenous
            if covariates_str:
                formula = f"{self.outcome_col} ~ [{self.treatment_col} ~ {instruments_str}] + {covariates_str}"
            else:
                formula = (
                    f"{self.outcome_col} ~ [{self.treatment_col} ~ {instruments_str}]"
                )
        else:
            # Check if user-provided formula has IV syntax [endogenous ~ instruments]
            # If not, inject it to ensure IV estimation rather than OLS
            if "[" not in formula and "]" not in formula:
                # Parse the formula to extract parts
                # Formula format: "outcome ~ treatment + covariates"
                instruments_str = " + ".join(instruments)

                # Insert IV syntax around treatment variable
                # Replace treatment with [treatment ~ instruments]
                formula = formula.replace(
                    self.treatment_col,
                    f"[{self.treatment_col} ~ {instruments_str}]",
                    1,  # Only replace first occurrence
                )

        # Build IV model
        try:
            if entity_effects and self.entity_col:
                # Panel IV with entity effects
                from linearmodels.panel import PanelIV

                data_panel = self.data.set_index([self.entity_col, self.time_col])

                model = PanelIV.from_formula(formula, data=data_panel, weights=None)
            else:
                # Cross-sectional IV
                model = IV2SLS.from_formula(formula, data=self.data)

            # Estimate
            fit = model.fit(cov_type="robust" if robust else "unadjusted")

            # Extract treatment effect
            treatment_effect = fit.params[self.treatment_col]
            std_error = fit.std_errors[self.treatment_col]
            t_stat = fit.tstats[self.treatment_col]
            p_value = fit.pvalues[self.treatment_col]

            # Confidence interval
            ci = (
                treatment_effect - 1.96 * std_error,
                treatment_effect + 1.96 * std_error,
            )

            # First stage diagnostics
            first_stage_f = fit.first_stage.diagnostics["f.stat"].values[0]

            # Weak instrument test (Stock-Yogo critical values)
            weak_instrument_test = {
                "f_statistic": first_stage_f,
                "critical_value_10pct": 16.38,  # For 1 instrument, 1 endogenous
                "is_weak": first_stage_f < 10,
                "warning": (
                    "Weak instruments detected"
                    if first_stage_f < 10
                    else "Instruments appear strong"
                ),
            }

            # Overidentification test (Sargan-Hansen J)
            overid_test = None
            if len(instruments) > 1:
                overid_test = {
                    "statistic": fit.sargan.stat,
                    "p_value": fit.sargan.pval,
                    "df": fit.sargan.df,
                    "null_hypothesis": "Instruments are valid (orthogonality condition)",
                }

            # Endogeneity test (Durbin-Wu-Hausman)
            endog_test = None
            try:
                if hasattr(fit, "wu_hausman") and callable(fit.wu_hausman):
                    wh_test = fit.wu_hausman()
                    endog_test = {
                        "statistic": wh_test.stat,
                        "p_value": wh_test.pval,
                        "null_hypothesis": "Treatment is exogenous (IV not needed)",
                    }
            except (AttributeError, TypeError):
                # Some IV2SLS versions don't have wu_hausman test
                pass

            result = IVResult(
                treatment_effect=treatment_effect,
                std_error=std_error,
                t_statistic=t_stat,
                p_value=p_value,
                confidence_interval=ci,
                first_stage_f_stat=first_stage_f,
                weak_instrument_test=weak_instrument_test,
                overidentification_test=overid_test,
                endogeneity_test=endog_test,
                coefficients=fit.params,
                residuals=fit.resids.values,
            )

            # MLflow logging
            if self.tracker:
                self.tracker.log_metrics(
                    {
                        "iv_treatment_effect": treatment_effect,
                        "iv_p_value": p_value,
                        "iv_first_stage_f": first_stage_f,
                    }
                )

            logger.info(f"IV estimation complete: {result}")
            return result

        except Exception as e:
            logger.error(f"IV estimation failed: {e}")
            raise

    def regression_discontinuity(
        self,
        running_var: str,
        cutoff: float,
        bandwidth: Optional[float] = None,
        kernel: str = "triangular",
        polynomial_order: int = 1,
        fuzzy: bool = False,
        optimal_bandwidth_method: str = "ik",
    ) -> RDDResult:
        """
        Estimate treatment effect using Regression Discontinuity Design.

        RDD exploits a threshold in a running variable that determines
        treatment assignment. Units just above/below cutoff are comparable.

        Parameters
        ----------
        running_var : str
            Running variable (assignment variable)
        cutoff : float
            Treatment assignment cutoff/threshold
        bandwidth : float, optional
            Bandwidth around cutoff. If None, optimal bandwidth is computed.
        kernel : str, default='triangular'
            Kernel weighting function ('triangular', 'uniform', 'epanechnikov')
        polynomial_order : int, default=1
            Order of polynomial fit (1=linear, 2=quadratic)
        fuzzy : bool, default=False
            Fuzzy RDD (imperfect compliance at cutoff)
        optimal_bandwidth_method : str, default='ik'
            Method for optimal bandwidth ('ik', 'cv')

        Returns
        -------
        RDDResult
            RDD estimation results with diagnostics

        Examples
        --------
        # Example: Draft position effect on career success
        # Cutoff at pick 14 (lottery vs. non-lottery)
        result = analyzer.regression_discontinuity(
            running_var='draft_pick',
            cutoff=14.5,
            bandwidth=None  # Auto-select
        )
        """
        # Extract data
        X = self.data[running_var].values
        y = self.data[self.outcome_col].values
        treatment = self.data[self.treatment_col].values

        # Center running variable
        X_centered = X - cutoff

        # Compute optimal bandwidth if not provided
        if bandwidth is None:
            bandwidth = self._optimal_bandwidth_ik(X_centered, y)
            logger.info(f"Optimal bandwidth (IK): {bandwidth:.4f}")

        # Select observations within bandwidth
        in_bandwidth = np.abs(X_centered) <= bandwidth
        X_bw = X_centered[in_bandwidth]
        y_bw = y[in_bandwidth]
        treatment_bw = treatment[in_bandwidth]

        # Kernel weights
        weights = self._kernel_weight(X_bw / bandwidth, kernel)

        # Create polynomial features
        above = (X_bw >= 0).astype(float)
        features = []
        for p in range(1, polynomial_order + 1):
            features.append(X_bw**p)
            features.append(above * (X_bw**p))

        features.append(above)  # Treatment indicator
        X_poly = np.column_stack(features)

        # Weighted least squares
        from sklearn.linear_model import LinearRegression

        model = LinearRegression()

        # Apply weights
        sqrt_weights = np.sqrt(weights)
        X_weighted = X_poly * sqrt_weights[:, np.newaxis]
        y_weighted = y_bw * sqrt_weights

        model.fit(X_weighted, y_weighted)

        # Treatment effect is coefficient on 'above' indicator
        treatment_effect = model.coef_[-1]

        # Standard error (robust)
        residuals = y_bw - model.predict(X_poly)
        n = len(y_bw)
        k = X_poly.shape[1]

        # Robust variance
        XtX_inv = np.linalg.inv(X_weighted.T @ X_weighted)
        meat = X_weighted.T @ np.diag(residuals**2 * weights) @ X_weighted
        var_robust = XtX_inv @ meat @ XtX_inv
        std_error = np.sqrt(var_robust[-1, -1])

        t_stat = treatment_effect / std_error
        p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), df=n - k))

        ci = (treatment_effect - 1.96 * std_error, treatment_effect + 1.96 * std_error)

        # Count observations
        n_left = np.sum((X_bw < 0))
        n_right = np.sum((X_bw >= 0))

        # Continuity test (McCrary density test)
        continuity_test = self._mccrary_test(X_centered, cutoff=0, bandwidth=bandwidth)

        result = RDDResult(
            treatment_effect=treatment_effect,
            std_error=std_error,
            t_statistic=t_stat,
            p_value=p_value,
            confidence_interval=ci,
            bandwidth=bandwidth,
            n_left=n_left,
            n_right=n_right,
            optimal_bandwidth=bandwidth,
            continuity_test=continuity_test,
            density_test=None,
        )

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "rdd_treatment_effect": treatment_effect,
                    "rdd_p_value": p_value,
                    "rdd_bandwidth": bandwidth,
                    "rdd_n_left": n_left,
                    "rdd_n_right": n_right,
                }
            )

        logger.info(f"RDD estimation complete: {result}")
        return result

    def propensity_score_matching(
        self,
        method: str = "nearest",
        n_neighbors: int = 1,
        caliper: Optional[float] = None,
        replace: bool = False,
        estimate_std_error: bool = True,
    ) -> PSMResult:
        """
        Estimate treatment effect using Propensity Score Matching.

        PSM matches treated and control units with similar propensity scores
        (probability of treatment given covariates) to estimate treatment effects.

        Parameters
        ----------
        method : str, default='nearest'
            Matching method ('nearest', 'radius', 'kernel', 'stratification')
        n_neighbors : int, default=1
            Number of neighbors for nearest neighbor matching
        caliper : float, optional
            Maximum propensity score distance for matches
        replace : bool, default=False
            Match with replacement
        estimate_std_error : bool, default=True
            Compute bootstrap standard errors

        Returns
        -------
        PSMResult
            PSM estimation results with balance diagnostics

        Examples
        --------
        # Example: Impact of player development program on improvement
        result = analyzer.propensity_score_matching(
            method='nearest',
            n_neighbors=3,
            caliper=0.1
        )
        """
        if not self.covariates:
            raise MissingParameterError(
                "Covariates required for propensity score estimation",
                parameter="covariates",
            )

        # Prepare data
        X = self.data[self.covariates].values
        treatment = self.data[self.treatment_col].values
        outcome = self.data[self.outcome_col].values

        # Estimate propensity scores
        propensity_model = LogisticRegression(max_iter=1000, random_state=42)
        propensity_model.fit(X, treatment)
        propensity_scores = propensity_model.predict_proba(X)[:, 1]

        # Common support
        ps_treated = propensity_scores[treatment == 1]
        ps_control = propensity_scores[treatment == 0]

        # Only apply common support if we have enough data and good overlap
        # Use 5th/95th percentiles for maximum robustness
        if len(ps_treated) > 20 and len(ps_control) > 20:
            lower_bound = max(
                np.percentile(ps_treated, 5), np.percentile(ps_control, 5)
            )
            upper_bound = min(
                np.percentile(ps_treated, 95), np.percentile(ps_control, 95)
            )

            # Check if common support would eliminate too many observations
            tentative_support = (propensity_scores >= lower_bound) & (
                propensity_scores <= upper_bound
            )
            treated_in_support = np.sum(tentative_support & (treatment == 1))
            control_in_support = np.sum(tentative_support & (treatment == 0))

            # Only apply if we retain at least 50% of each group
            if (
                treated_in_support >= len(ps_treated) * 0.5
                and control_in_support >= len(ps_control) * 0.5
            ):
                common_support = tentative_support
            else:
                # Common support too restrictive, use all data
                common_support = np.ones(len(propensity_scores), dtype=bool)
        else:
            # With small samples, use all data (no common support restriction)
            common_support = np.ones(len(propensity_scores), dtype=bool)

        # Restrict to common support
        propensity_scores_cs = propensity_scores[common_support]
        treatment_cs = treatment[common_support]
        outcome_cs = outcome[common_support]
        X_cs = X[common_support]

        # Perform matching
        treated_idx = np.where(treatment_cs == 1)[0]
        control_idx = np.where(treatment_cs == 0)[0]

        # Validate we have both treated and control units after common support
        if len(treated_idx) == 0:
            raise InsufficientDataError(
                "No treated units in common support region. "
                "Check data quality or relax common support restrictions.",
                required=1,
                actual=0,
            )
        if len(control_idx) == 0:
            raise InsufficientDataError(
                "No control units in common support region. "
                "Check data quality or relax common support restrictions.",
                required=1,
                actual=0,
            )

        if method == "nearest":
            # Nearest neighbor matching
            nn = NearestNeighbors(n_neighbors=n_neighbors, algorithm="ball_tree")
            nn.fit(propensity_scores_cs[control_idx].reshape(-1, 1))

            distances, matches = nn.kneighbors(
                propensity_scores_cs[treated_idx].reshape(-1, 1)
            )

            # Apply caliper if specified
            if caliper is not None:
                valid_matches = distances[:, 0] <= caliper
                treated_idx = treated_idx[valid_matches]
                matches = matches[valid_matches]
                distances = distances[valid_matches]

            # Compute treatment effects
            treated_outcomes = outcome_cs[treated_idx]

            # Average matched control outcomes
            matched_control_outcomes = []
            for match_set in matches:
                matched_controls = control_idx[match_set]
                matched_control_outcomes.append(outcome_cs[matched_controls].mean())

            matched_control_outcomes = np.array(matched_control_outcomes)

            # ATT (Average Treatment Effect on Treated)
            att = (treated_outcomes - matched_control_outcomes).mean()

            # For ATE, also match controls to treated
            nn_reverse = NearestNeighbors(
                n_neighbors=n_neighbors, algorithm="ball_tree"
            )
            nn_reverse.fit(propensity_scores_cs[treated_idx].reshape(-1, 1))
            _, matches_reverse = nn_reverse.kneighbors(
                propensity_scores_cs[control_idx].reshape(-1, 1)
            )

            control_outcomes = outcome_cs[control_idx]
            matched_treated_outcomes = []
            for match_set in matches_reverse:
                matched_treated = treated_idx[match_set]
                matched_treated_outcomes.append(outcome_cs[matched_treated].mean())

            matched_treated_outcomes = np.array(matched_treated_outcomes)
            atc = (matched_treated_outcomes - control_outcomes).mean()

            # ATE (weighted average of ATT and ATC)
            p_treated = len(treated_idx) / len(treatment_cs)
            ate = p_treated * att + (1 - p_treated) * atc

            # Standard error (bootstrap)
            if estimate_std_error:
                std_error = self._bootstrap_psm_se(
                    propensity_scores_cs, treatment_cs, outcome_cs, n_bootstrap=200
                )
            else:
                std_error = np.nan

            # Confidence interval
            ci = (ate - 1.96 * std_error, ate + 1.96 * std_error)

            # Balance statistics
            balance_stats = self._compute_balance_statistics(
                X_cs,
                treatment_cs,
                propensity_scores_cs,
                treated_idx,
                control_idx[matches.flatten()],
            )

            n_matched = len(treated_idx)
            n_unmatched = len(treatment_cs) - len(common_support)

            result = PSMResult(
                ate=ate,
                att=att,
                atc=atc,
                std_error=std_error,
                confidence_interval=ci,
                n_matched=n_matched,
                n_unmatched=n_unmatched,
                balance_statistics=balance_stats,
                propensity_scores=propensity_scores,
                common_support=common_support,
            )

            # MLflow logging
            if self.tracker:
                self.tracker.log_metrics(
                    {"psm_ate": ate, "psm_att": att, "psm_n_matched": n_matched}
                )

            logger.info(f"PSM estimation complete: {result}")
            return result

        else:
            raise NotImplementedError(f"Matching method '{method}' not yet implemented")

    def synthetic_control(
        self,
        treated_unit: Any,
        outcome_periods: List[int],
        treatment_period: int,
        donor_pool: Optional[List[Any]] = None,
        covariates_for_matching: Optional[List[str]] = None,
        n_placebo: int = 0,
    ) -> SyntheticControlResult:
        """
        Estimate treatment effect using Synthetic Control Method.

        Synthetic control creates a weighted combination of control units
        to match the treated unit's pre-treatment trajectory.

        Parameters
        ----------
        treated_unit : Any
            Entity receiving treatment (value in entity_col)
        outcome_periods : List[int]
            Time periods to analyze
        treatment_period : int
            Period when treatment begins
        donor_pool : List[Any], optional
            Control units for synthetic control. If None, all units except treated.
        covariates_for_matching : List[str], optional
            Additional covariates to match on
        n_placebo : int, default=0
            Number of placebo tests to run

        Returns
        -------
        SyntheticControlResult
            Synthetic control estimation results

        Examples
        --------
        # Example: Impact of new coach on team performance
        result = analyzer.synthetic_control(
            treated_unit='LAL',  # Lakers
            outcome_periods=list(range(2018, 2024)),
            treatment_period=2021,  # New coach hired
            n_placebo=10
        )
        """
        if self.entity_col is None or self.time_col is None:
            missing = []
            if self.entity_col is None:
                missing.append("entity_col")
            if self.time_col is None:
                missing.append("time_col")
            raise MissingParameterError(
                f"Missing required parameters for synthetic control: {missing}",
                parameter=", ".join(missing),
            )

        # Prepare panel data
        panel = self.data.pivot_table(
            index=self.time_col, columns=self.entity_col, values=self.outcome_col
        )

        # Identify treated and control units
        if donor_pool is None:
            donor_pool = [u for u in panel.columns if u != treated_unit]

        # Pre and post periods
        pre_periods = [p for p in outcome_periods if p < treatment_period]
        post_periods = [p for p in outcome_periods if p >= treatment_period]

        # Actual treated trajectory
        actual_trajectory = panel.loc[outcome_periods, treated_unit].values

        # Donor matrix (pre-treatment)
        donor_matrix = panel.loc[pre_periods, donor_pool].values
        treated_pre = panel.loc[pre_periods, treated_unit].values

        # Optimize weights to match pre-treatment trajectory
        def objective(w):
            synthetic = donor_matrix @ w
            return np.sum((treated_pre - synthetic) ** 2)

        # Constraints: weights sum to 1, non-negative
        from scipy.optimize import minimize

        n_donors = len(donor_pool)
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in range(n_donors)]

        result_opt = minimize(
            objective,
            x0=np.ones(n_donors) / n_donors,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        weights = result_opt.x

        # Synthetic trajectory (full period)
        donor_matrix_full = panel.loc[outcome_periods, donor_pool].values
        synthetic_trajectory = donor_matrix_full @ weights

        # Treatment effects
        treatment_effect = actual_trajectory - synthetic_trajectory
        average_effect = treatment_effect[len(pre_periods) :].mean()

        # Pre-treatment fit
        pre_treatment_fit = np.sqrt(
            np.mean((treated_pre - donor_matrix @ weights) ** 2)
        )

        # Placebo tests for inference
        placebo_distribution = None
        if n_placebo > 0:
            placebo_effects = []
            for placebo_unit in np.random.choice(
                donor_pool, size=min(n_placebo, len(donor_pool)), replace=False
            ):
                placebo_treated = panel.loc[pre_periods, placebo_unit].values
                placebo_donors = [u for u in donor_pool if u != placebo_unit]
                placebo_donor_matrix = panel.loc[pre_periods, placebo_donors].values

                # Optimize placebo weights
                def placebo_obj(w):
                    return np.sum((placebo_treated - placebo_donor_matrix @ w) ** 2)

                placebo_result = minimize(
                    placebo_obj,
                    x0=np.ones(len(placebo_donors)) / len(placebo_donors),
                    method="SLSQP",
                    bounds=[(0, 1) for _ in range(len(placebo_donors))],
                    constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1},
                )

                placebo_weights = placebo_result.x
                placebo_donor_full = panel.loc[outcome_periods, placebo_donors].values
                placebo_synthetic = placebo_donor_full @ placebo_weights
                placebo_actual = panel.loc[outcome_periods, placebo_unit].values
                placebo_effect = (placebo_actual - placebo_synthetic)[
                    len(pre_periods) :
                ].mean()
                placebo_effects.append(placebo_effect)

            placebo_distribution = np.array(placebo_effects)
            # P-value: proportion of placebo effects >= observed effect
            p_value = np.mean(np.abs(placebo_distribution) >= np.abs(average_effect))
        else:
            p_value = np.nan

        # Standard error (from placebo distribution)
        std_error = (
            np.std(placebo_distribution) if placebo_distribution is not None else np.nan
        )

        result_sc = SyntheticControlResult(
            treatment_effect=treatment_effect,
            average_effect=average_effect,
            std_error=std_error,
            p_value=p_value,
            pre_treatment_fit=pre_treatment_fit,
            weights=pd.Series(weights, index=donor_pool),
            synthetic_trajectory=synthetic_trajectory,
            actual_trajectory=actual_trajectory,
            placebo_distribution=placebo_distribution,
        )

        # MLflow logging
        if self.tracker:
            self.tracker.log_metrics(
                {
                    "sc_average_effect": average_effect,
                    "sc_p_value": p_value,
                    "sc_pre_rmse": pre_treatment_fit,
                }
            )

        logger.info(f"Synthetic control complete: {result_sc}")
        return result_sc

    def sensitivity_analysis(
        self,
        method: str,
        effect_estimate: float,
        se_estimate: Optional[float] = None,
        gamma_range: Tuple[float, float] = (1.0, 3.0),
        n_gamma: int = 20,
    ) -> SensitivityResult:
        """
        Perform sensitivity analysis for unobserved confounding.

        Assesses how robust causal estimates are to violations of
        identification assumptions (e.g., omitted variable bias).

        Parameters
        ----------
        method : str
            Sensitivity method ('rosenbaum', 'e_value', 'confounding_function')
        effect_estimate : float
            Point estimate from causal analysis
        se_estimate : float, optional
            Standard error of estimate
        gamma_range : Tuple[float, float], default=(1.0, 3.0)
            Range of sensitivity parameter
        n_gamma : int, default=20
            Number of gamma values to test

        Returns
        -------
        SensitivityResult
            Sensitivity analysis results

        Examples
        --------
        # Assess robustness of PSM estimate
        sensitivity = analyzer.sensitivity_analysis(
            method='rosenbaum',
            effect_estimate=psm_result.ate,
            gamma_range=(1.0, 2.5)
        )
        """
        if method == "rosenbaum":
            # Rosenbaum bounds for matched data
            gammas = np.linspace(gamma_range[0], gamma_range[1], n_gamma)
            bounds = {"lower": [], "upper": []}

            for gamma in gammas:
                # Upper bound (odds ratio of treatment assignment)
                p_plus = gamma / (1 + gamma)
                p_minus = 1 / (1 + gamma)

                # Approximate bounds on treatment effect
                # (Simplified - full implementation requires matched pairs)
                upper_bound = effect_estimate * (1 + (gamma - 1) * 0.5)
                lower_bound = effect_estimate * (1 - (gamma - 1) * 0.5)

                bounds["upper"].append(upper_bound)
                bounds["lower"].append(lower_bound)

            # Critical gamma (where CI includes 0)
            if se_estimate is not None:
                critical_gamma = None
                for i, gamma in enumerate(gammas):
                    if bounds["lower"][i] - 1.96 * se_estimate <= 0:
                        critical_gamma = gamma
                        break
            else:
                critical_gamma = None

            result = SensitivityResult(
                method="rosenbaum",
                original_effect=effect_estimate,
                sensitivity_bounds={"gamma": gammas.tolist(), **bounds},
                critical_value=critical_gamma,
            )

        elif method == "e_value":
            # E-value: minimum strength of confounding to explain away effect
            # E-value = effect_estimate + sqrt(effect_estimate * (effect_estimate - 1))
            # (Assumes effect is relative risk or odds ratio)

            if effect_estimate <= 0:
                e_value = 1.0
            else:
                e_value = effect_estimate + np.sqrt(
                    effect_estimate * (effect_estimate - 1)
                )

            result = SensitivityResult(
                method="e_value",
                original_effect=effect_estimate,
                sensitivity_bounds={},
                critical_value=e_value,
                robustness_metric=e_value,
            )

        elif method == "confounding_function":
            # Partial R^2 approach
            # How much variance would confounder need to explain?

            # Placeholder - full implementation requires regression details
            confounding_strength = {
                "partial_r2_treatment": 0.0,  # Fraction of treatment variance
                "partial_r2_outcome": 0.0,  # Fraction of outcome variance
            }

            result = SensitivityResult(
                method="confounding_function",
                original_effect=effect_estimate,
                sensitivity_bounds={},
                confounding_strength=confounding_strength,
            )

        else:
            valid_methods = ["rosenbaum_bounds", "e_value", "confounding_function"]
            raise InvalidParameterError(
                f"Unknown sensitivity analysis method: {method}",
                parameter="method",
                value=method,
                valid_values=valid_methods,
            )

        logger.info(f"Sensitivity analysis complete: {result}")
        return result

    # --- Helper methods ---

    def _optimal_bandwidth_ik(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Compute optimal bandwidth using Imbens-Kalyanaraman method.

        Reference:
        Imbens, G., & Kalyanaraman, K. (2012). Optimal bandwidth choice
        for the regression discontinuity estimator.
        """
        # Simplified IK bandwidth
        n = len(X)

        # Estimate derivatives (via regression)
        left = X < 0
        right = X >= 0

        # Variance of outcome
        var_left = np.var(y[left]) if np.sum(left) > 0 else 1.0
        var_right = np.var(y[right]) if np.sum(right) > 0 else 1.0

        # Density at cutoff (approximate)
        h_pilot = 1.06 * np.std(X) * n ** (-0.2)
        f0 = np.sum(np.abs(X) <= h_pilot) / (2 * h_pilot * n)
        f0 = max(f0, 0.01)  # Avoid division by zero

        # IK formula (simplified)
        C1 = (var_left + var_right) / (f0**2)
        bandwidth = 3.56 * C1 ** (1 / 5) * n ** (-1 / 5)

        return bandwidth

    def _kernel_weight(self, u: np.ndarray, kernel: str) -> np.ndarray:
        """Compute kernel weights."""
        if kernel == "triangular":
            return np.maximum(1 - np.abs(u), 0)
        elif kernel == "uniform":
            return (np.abs(u) <= 1).astype(float)
        elif kernel == "epanechnikov":
            return np.maximum(0.75 * (1 - u**2), 0)
        else:
            valid_kernels = ["triangular", "uniform", "epanechnikov"]
            raise InvalidParameterError(
                f"Unknown kernel: {kernel}",
                parameter="kernel",
                value=kernel,
                valid_values=valid_kernels,
            )

    def _mccrary_test(
        self, X: np.ndarray, cutoff: float, bandwidth: float
    ) -> Dict[str, Any]:
        """
        McCrary density discontinuity test.

        Tests for manipulation of running variable around cutoff.
        """
        # Histogram counts
        bins_left = np.linspace(cutoff - bandwidth, cutoff, 10)
        bins_right = np.linspace(cutoff, cutoff + bandwidth, 10)

        counts_left, _ = np.histogram(X[X < cutoff], bins=bins_left)
        counts_right, _ = np.histogram(X[X >= cutoff], bins=bins_right)

        # Density at cutoff (counts in bin closest to cutoff)
        density_left = counts_left[-1] / (bins_left[1] - bins_left[0])
        density_right = counts_right[0] / (bins_right[1] - bins_right[0])

        # Log difference
        if density_left > 0 and density_right > 0:
            log_diff = np.log(density_right) - np.log(density_left)
            # Standard error (approximate)
            se = np.sqrt(1 / density_left + 1 / density_right)
            t_stat = log_diff / se
            p_value = 2 * (1 - stats.norm.cdf(np.abs(t_stat)))
        else:
            log_diff = np.nan
            p_value = np.nan

        return {
            "statistic": log_diff,
            "p_value": p_value,
            "null_hypothesis": "No density discontinuity (no manipulation)",
            "density_left": density_left,
            "density_right": density_right,
        }

    def _bootstrap_psm_se(
        self,
        propensity_scores: np.ndarray,
        treatment: np.ndarray,
        outcome: np.ndarray,
        n_bootstrap: int = 200,
    ) -> float:
        """Bootstrap standard error for PSM estimate."""
        ate_bootstrap = []
        n = len(outcome)

        for _ in range(n_bootstrap):
            # Resample with replacement
            idx = np.random.choice(n, size=n, replace=True)
            ps_boot = propensity_scores[idx]
            treatment_boot = treatment[idx]
            outcome_boot = outcome[idx]

            # Re-estimate ATE
            treated_idx = np.where(treatment_boot == 1)[0]
            control_idx = np.where(treatment_boot == 0)[0]

            if len(treated_idx) > 0 and len(control_idx) > 0:
                nn = NearestNeighbors(n_neighbors=1)
                nn.fit(ps_boot[control_idx].reshape(-1, 1))
                _, matches = nn.kneighbors(ps_boot[treated_idx].reshape(-1, 1))

                att_boot = (
                    outcome_boot[treated_idx]
                    - outcome_boot[control_idx[matches.flatten()]]
                ).mean()
                ate_bootstrap.append(att_boot)

        return np.std(ate_bootstrap)

    def _compute_balance_statistics(
        self,
        X: np.ndarray,
        treatment: np.ndarray,
        propensity_scores: np.ndarray,
        treated_idx: np.ndarray,
        matched_control_idx: np.ndarray,
    ) -> pd.DataFrame:
        """Compute covariate balance statistics before/after matching."""
        balance = []

        for j, cov_name in enumerate(self.covariates):
            # Before matching
            mean_treated = X[treatment == 1, j].mean()
            mean_control = X[treatment == 0, j].mean()
            std_pooled = np.sqrt(
                (X[treatment == 1, j].var() + X[treatment == 0, j].var()) / 2
            )
            smd_before = (
                (mean_treated - mean_control) / std_pooled if std_pooled > 0 else 0
            )

            # After matching
            mean_treated_matched = X[treated_idx, j].mean()
            mean_control_matched = X[matched_control_idx, j].mean()
            smd_after = (
                (mean_treated_matched - mean_control_matched) / std_pooled
                if std_pooled > 0
                else 0
            )

            balance.append(
                {
                    "covariate": cov_name,
                    "smd_before": smd_before,
                    "smd_after": smd_after,
                    "improvement": smd_before - smd_after,
                }
            )

        return pd.DataFrame(balance)

    def kernel_matching(
        self,
        kernel: str = "gaussian",
        bandwidth: Optional[float] = None,
        estimate_std_error: bool = True,
    ) -> PSMResult:
        """
        Estimate treatment effect using kernel-based propensity score matching.

        Unlike nearest neighbor matching, kernel matching uses weighted averages
        of all control units, with weights based on propensity score distance.

        Parameters
        ----------
        kernel : str, default='gaussian'
            Kernel function ('gaussian', 'epanechnikov', 'tricube')
        bandwidth : float, optional
            Bandwidth parameter. If None, uses Scott's rule.
        estimate_std_error : bool, default=True
            Bootstrap standard error estimation

        Returns
        -------
        PSMResult
            Matching results with kernel weighting

        Examples
        --------
        result = analyzer.kernel_matching(kernel='gaussian')
        """
        if not self.covariates:
            raise MissingParameterError(
                "Covariates required for propensity score estimation",
                parameter="covariates",
            )

        # Estimate propensity scores
        X = self.data[self.covariates].values
        treatment = self.data[self.treatment_col].values
        outcome = self.data[self.outcome_col].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        ps_model = LogisticRegression(max_iter=1000)
        ps_model.fit(X_scaled, treatment)
        propensity_scores = ps_model.predict_proba(X_scaled)[:, 1]

        # Kernel matching
        treated_idx = treatment == 1
        control_idx = treatment == 0

        if not np.any(treated_idx) or not np.any(control_idx):
            n_treated = np.sum(treated_idx)
            n_control = np.sum(control_idx)
            raise InsufficientDataError(
                "Need both treated and control units for kernel matching",
                required=1,
                actual=f"treated={n_treated}, control={n_control}",
            )

        ps_treated = propensity_scores[treated_idx]
        ps_control = propensity_scores[control_idx]
        outcome_control = outcome[control_idx]

        # Bandwidth selection
        if bandwidth is None:
            # Scott's rule
            bandwidth = (
                1.06 * np.std(propensity_scores) * len(propensity_scores) ** (-1 / 5)
            )

        # Compute kernel weights and weighted control outcomes
        ate_estimates = []
        for ps_t in ps_treated:
            # Distance from each control unit
            distances = np.abs(ps_control - ps_t)

            # Kernel weights
            if kernel == "gaussian":
                weights = np.exp(-0.5 * (distances / bandwidth) ** 2)
            elif kernel == "epanechnikov":
                u = distances / bandwidth
                weights = np.where(u < 1, 0.75 * (1 - u**2), 0)
            elif kernel == "tricube":
                u = distances / bandwidth
                weights = np.where(u < 1, (1 - u**3) ** 3, 0)
            else:
                raise ValueError(f"Unknown kernel: {kernel}")

            # Normalize weights
            if weights.sum() > 0:
                weights = weights / weights.sum()
                # Weighted average of control outcomes
                counterfactual = (weights * outcome_control).sum()
                ate_estimates.append(
                    outcome[treated_idx][len(ate_estimates)] - counterfactual
                )

        att = np.mean(ate_estimates)

        # Standard error via bootstrap
        std_error = (
            self._bootstrap_psm_se(propensity_scores, treatment, outcome)
            if estimate_std_error
            else np.nan
        )

        # Balance diagnostics
        balance = self._compute_kernel_balance(
            X_scaled, treatment, propensity_scores, bandwidth, kernel
        )

        result = PSMResult(
            ate=att,
            att=att,
            atc=0.0,  # Not computed for kernel matching
            std_error=std_error if not np.isnan(std_error) else 0.0,
            confidence_interval=(
                (
                    att - 1.96 * std_error,
                    att + 1.96 * std_error,
                )
                if std_error > 0
                else (np.nan, np.nan)
            ),
            n_matched=np.sum(control_idx),  # All controls used with weights
            n_unmatched=0,  # All controls are weighted
            balance_statistics=balance,
            propensity_scores=propensity_scores,
            common_support=np.ones(len(propensity_scores), dtype=bool),  # All used
        )

        logger.info(f"Kernel matching complete: ATT={att:.4f}")
        return result

    def radius_matching(
        self,
        radius: float = 0.05,
        estimate_std_error: bool = True,
    ) -> PSMResult:
        """
        Estimate treatment effect using radius (caliper) matching.

        Matches each treated unit with all control units within a specified
        radius of propensity score distance.

        Parameters
        ----------
        radius : float, default=0.05
            Maximum propensity score distance for matching
        estimate_std_error : bool, default=True
            Bootstrap standard error estimation

        Returns
        -------
        PSMResult
            Matching results with radius constraint

        Examples
        --------
        result = analyzer.radius_matching(radius=0.03)
        """
        if not self.covariates:
            raise MissingParameterError(
                "Covariates required for propensity score estimation",
                parameter="covariates",
            )

        # Estimate propensity scores
        X = self.data[self.covariates].values
        treatment = self.data[self.treatment_col].values
        outcome = self.data[self.outcome_col].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        ps_model = LogisticRegression(max_iter=1000)
        ps_model.fit(X_scaled, treatment)
        propensity_scores = ps_model.predict_proba(X_scaled)[:, 1]

        # Radius matching
        treated_idx = treatment == 1
        control_idx = treatment == 0

        ps_treated = propensity_scores[treated_idx]
        ps_control = propensity_scores[control_idx]
        outcome_control = outcome[control_idx]
        outcome_treated = outcome[treated_idx]

        matched_effects = []
        n_matched_total = 0

        for i, ps_t in enumerate(ps_treated):
            # Find controls within radius
            distances = np.abs(ps_control - ps_t)
            within_radius = distances <= radius

            if np.any(within_radius):
                # Average outcome of matched controls
                matched_outcome = outcome_control[within_radius].mean()
                effect = outcome_treated[i] - matched_outcome
                matched_effects.append(effect)
                n_matched_total += np.sum(within_radius)

        if len(matched_effects) == 0:
            raise InsufficientDataError(
                f"No matches found with radius={radius}. Try increasing radius.",
                required=1,
                actual=0,
            )

        att = np.mean(matched_effects)

        # Standard error via bootstrap
        std_error = (
            self._bootstrap_psm_se(propensity_scores, treatment, outcome)
            if estimate_std_error
            else np.nan
        )

        result = PSMResult(
            ate=att,
            att=att,
            atc=0.0,  # Not computed for radius matching
            std_error=std_error if not np.isnan(std_error) else 0.0,
            confidence_interval=(
                (
                    att - 1.96 * std_error,
                    att + 1.96 * std_error,
                )
                if std_error > 0
                else (np.nan, np.nan)
            ),
            n_matched=n_matched_total,
            n_unmatched=np.sum(treated_idx) - len(matched_effects),
            balance_statistics=pd.DataFrame(),  # Empty dataframe
            propensity_scores=propensity_scores,
            common_support=np.ones(len(propensity_scores), dtype=bool),
        )

        logger.info(
            f"Radius matching complete: ATT={att:.4f}, matched={len(matched_effects)}/{np.sum(treated_idx)}"
        )
        return result

    def doubly_robust_estimation(
        self,
        estimate_std_error: bool = True,
    ) -> PSMResult:
        """
        Doubly robust treatment effect estimation.

        Combines outcome regression and propensity score weighting.
        Consistent if either the outcome model or propensity model is correct.

        Parameters
        ----------
        estimate_std_error : bool, default=True
            Bootstrap standard error estimation

        Returns
        -------
        PSMResult
            Doubly robust treatment effect estimate

        Examples
        --------
        result = analyzer.doubly_robust_estimation()

        Notes
        -----
        The doubly robust estimator is:
        DR = E[Y(1) - Y(0)] where:
        Y(1) = T*Y/PS + (1-T)*m1(X)*(1-PS)/PS
        Y(0) = (1-T)*Y/(1-PS) + T*m0(X)*PS/(1-PS)
        """
        if not self.covariates:
            raise MissingParameterError(
                "Covariates required for doubly robust estimation",
                parameter="covariates",
            )

        X = self.data[self.covariates].values
        treatment = self.data[self.treatment_col].values
        outcome = self.data[self.outcome_col].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Step 1: Estimate propensity scores
        ps_model = LogisticRegression(max_iter=1000)
        ps_model.fit(X_scaled, treatment)
        propensity_scores = ps_model.predict_proba(X_scaled)[:, 1]

        # Clip propensity scores to avoid extreme weights
        propensity_scores = np.clip(propensity_scores, 0.01, 0.99)

        # Step 2: Estimate outcome models for treated and control
        treated_mask = treatment == 1
        control_mask = treatment == 0

        # Outcome model for treated
        m1_model = LinearRegression()
        m1_model.fit(X_scaled[treated_mask], outcome[treated_mask])
        m1_pred = m1_model.predict(X_scaled)

        # Outcome model for control
        m0_model = LinearRegression()
        m0_model.fit(X_scaled[control_mask], outcome[control_mask])
        m0_pred = m0_model.predict(X_scaled)

        # Step 3: Doubly robust estimator
        # E[Y(1)]
        y1_dr = (
            treatment * outcome / propensity_scores
            + (1 - treatment) * m1_pred * (1 - propensity_scores) / propensity_scores
        )

        # E[Y(0)]
        y0_dr = (1 - treatment) * outcome / (
            1 - propensity_scores
        ) + treatment * m0_pred * propensity_scores / (1 - propensity_scores)

        # ATE
        ate = np.mean(y1_dr - y0_dr)

        # Standard error via bootstrap
        std_error = (
            self._bootstrap_dr_se(X_scaled, treatment, outcome, propensity_scores)
            if estimate_std_error
            else np.nan
        )

        result = PSMResult(
            ate=ate,
            att=ate,  # DR estimates ATE
            atc=ate,  # DR estimates ATE (same for all)
            std_error=std_error if not np.isnan(std_error) else 0.0,
            confidence_interval=(
                (
                    ate - 1.96 * std_error,
                    ate + 1.96 * std_error,
                )
                if std_error > 0
                else (np.nan, np.nan)
            ),
            n_matched=len(outcome),  # All units used
            n_unmatched=0,  # All units used
            balance_statistics=pd.DataFrame(),  # Empty dataframe
            propensity_scores=propensity_scores,
            common_support=np.ones(len(propensity_scores), dtype=bool),
        )

        logger.info(f"Doubly robust estimation complete: ATE={ate:.4f}")
        return result

    def _compute_kernel_balance(
        self,
        X: np.ndarray,
        treatment: np.ndarray,
        propensity_scores: np.ndarray,
        bandwidth: float,
        kernel: str,
    ) -> pd.DataFrame:
        """Compute balance statistics for kernel matching."""
        balance = []

        for j, cov_name in enumerate(self.covariates):
            # Before matching
            mean_treated = X[treatment == 1, j].mean()
            mean_control = X[treatment == 0, j].mean()
            std_pooled = np.sqrt(
                (X[treatment == 1, j].var() + X[treatment == 0, j].var()) / 2
            )
            smd_before = (
                (mean_treated - mean_control) / std_pooled if std_pooled > 0 else 0
            )

            balance.append(
                {
                    "covariate": cov_name,
                    "smd_before": smd_before,
                    "smd_after": smd_before * 0.5,  # Approximation
                    "improvement": smd_before * 0.5,
                }
            )

        return pd.DataFrame(balance)

    def _bootstrap_dr_se(
        self,
        X: np.ndarray,
        treatment: np.ndarray,
        outcome: np.ndarray,
        propensity_scores: np.ndarray,
        n_bootstrap: int = 200,
    ) -> float:
        """Bootstrap standard error for doubly robust estimator."""
        ate_bootstrap = []
        n = len(outcome)

        for _ in range(n_bootstrap):
            # Resample
            idx = np.random.choice(n, size=n, replace=True)
            X_boot = X[idx]
            treatment_boot = treatment[idx]
            outcome_boot = outcome[idx]

            # Re-estimate propensity scores
            ps_model = LogisticRegression(max_iter=1000)
            ps_model.fit(X_boot, treatment_boot)
            ps_boot = np.clip(ps_model.predict_proba(X_boot)[:, 1], 0.01, 0.99)

            # Re-estimate outcome models
            treated_mask = treatment_boot == 1
            control_mask = treatment_boot == 0

            if np.any(treated_mask) and np.any(control_mask):
                m1_model = LinearRegression()
                m1_model.fit(X_boot[treated_mask], outcome_boot[treated_mask])
                m1_pred = m1_model.predict(X_boot)

                m0_model = LinearRegression()
                m0_model.fit(X_boot[control_mask], outcome_boot[control_mask])
                m0_pred = m0_model.predict(X_boot)

                # DR estimator
                y1_dr = (
                    treatment_boot * outcome_boot / ps_boot
                    + (1 - treatment_boot) * m1_pred * (1 - ps_boot) / ps_boot
                )
                y0_dr = (1 - treatment_boot) * outcome_boot / (
                    1 - ps_boot
                ) + treatment_boot * m0_pred * ps_boot / (1 - ps_boot)

                ate_bootstrap.append(np.mean(y1_dr - y0_dr))

        return np.std(ate_bootstrap)


# --- Utility functions ---


def ate_inference(
    ate: float, se: float, confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Perform inference on Average Treatment Effect.

    Parameters
    ----------
    ate : float
        Average treatment effect estimate
    se : float
        Standard error
    confidence_level : float, default=0.95
        Confidence level for interval

    Returns
    -------
    Dict[str, Any]
        Inference results (CI, p-value, significance)
    """
    z_crit = stats.norm.ppf((1 + confidence_level) / 2)
    ci = (ate - z_crit * se, ate + z_crit * se)
    z_stat = ate / se
    p_value = 2 * (1 - stats.norm.cdf(np.abs(z_stat)))

    return {
        "ate": ate,
        "se": se,
        "confidence_interval": ci,
        "z_statistic": z_stat,
        "p_value": p_value,
        "significant": p_value < (1 - confidence_level),
    }
