"""
Panel Data Analysis for NBA Multi-Entity, Multi-Period Data.

This module provides panel data econometric methods including:
- Fixed effects (within) models
- Random effects (GLS) models
- Pooled OLS estimation
- Model selection tests (Hausman, F-test)
- Robust inference (clustered SE, heteroskedasticity-robust SE)

Designed for analyzing player/team performance across multiple seasons or games,
accounting for entity-specific and time-specific effects.

Integration:
- Works with data validation (Agent 4) for panel structure validation
- Complements time series analysis (Session 01)
- Outputs features for ML training pipeline (Agent 5)

Author: Agent 8 Module 2
Date: October 2025
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS, RandomEffects, PooledOLS, FirstDifferenceOLS
from linearmodels.panel.results import PanelResults
import statsmodels.api as sm
from scipy import stats

# Dynamic panel GMM (Phase 2 Day 6)
try:
    from pydynpd import regression as pydynpd_reg

    PYDYNPD_AVAILABLE = True
except ImportError:
    PYDYNPD_AVAILABLE = False
    pydynpd_reg = None

logger = logging.getLogger(__name__)


@dataclass
class PanelModelResult:
    """Results from panel data model estimation."""

    coefficients: pd.Series
    std_errors: pd.Series
    t_stats: pd.Series
    p_values: pd.Series
    r_squared: float
    r_squared_within: Optional[float] = None
    r_squared_between: Optional[float] = None
    r_squared_overall: Optional[float] = None
    f_statistic: Optional[float] = None
    f_pvalue: Optional[float] = None
    n_obs: int = 0
    n_entities: int = 0
    n_timeperiods: int = 0
    model_type: str = ""  # 'pooled', 'fixed_effects', 'random_effects', etc.
    entity_effects: Optional[pd.Series] = None
    time_effects: Optional[pd.Series] = None

    def summary(self) -> str:
        """Generate summary string."""
        s = f"{self.model_type.upper()} Model Results\n"
        s += "=" * 60 + "\n"
        s += f"R-squared: {self.r_squared:.4f}\n"
        if self.r_squared_within is not None:
            s += f"R-squared (within): {self.r_squared_within:.4f}\n"
        if self.r_squared_between is not None:
            s += f"R-squared (between): {self.r_squared_between:.4f}\n"
        s += f"Observations: {self.n_obs}\n"
        s += f"Entities: {self.n_entities}\n"
        s += f"Time periods: {self.n_timeperiods}\n"
        s += "\nCoefficients:\n"
        s += pd.DataFrame(
            {
                "coef": self.coefficients,
                "std_err": self.std_errors,
                "t": self.t_stats,
                "p>|t|": self.p_values,
            }
        ).to_string()
        return s


# ==============================================================================
# Dynamic Panel GMM Result Classes (Phase 2 Day 6)
# ==============================================================================


@dataclass
class DifferenceGMMResult:
    """Results from Arellano-Bond Difference GMM estimation.

    The Difference GMM estimator (Arellano & Bond, 1991) removes fixed effects
    by taking first differences and uses lagged levels as instruments. It's
    designed for dynamic panel data models with:
    - Lagged dependent variables
    - Endogenous regressors
    - Individual fixed effects
    - Short time periods (small T, large N)

    Attributes
    ----------
    coefficients : pd.Series
        Estimated coefficients
    std_errors : pd.Series
        Standard errors (Windmeijer-corrected for two-step)
    t_stats : pd.Series
        t-statistics
    p_values : pd.Series
        p-values for coefficients
    n_obs : int
        Number of observations used
    n_entities : int
        Number of entities (players/teams)
    n_timeperiods : int
        Number of time periods
    n_instruments : int
        Number of instruments used
    gmm_type : str
        'one_step' or 'two_step'
    ar1_pvalue : Optional[float]
        Arellano-Bond AR(1) test p-value (should reject H0)
    ar2_pvalue : Optional[float]
        Arellano-Bond AR(2) test p-value (should not reject H0)
    hansen_pvalue : Optional[float]
        Hansen J-test p-value for overidentifying restrictions
    collapsed : bool
        Whether instruments were collapsed to reduce proliferation

    Notes
    -----
    - AR(1) test should reject null (expect first-order autocorrelation in differences)
    - AR(2) test should not reject null (no second-order autocorrelation)
    - Hansen test checks validity of overidentifying restrictions
    - Two-step GMM is more efficient but requires Windmeijer correction

    Examples
    --------
    >>> # Player performance dynamics
    >>> result = analyzer.difference_gmm(
    ...     formula='points ~ lag(points, 1) + minutes + age',
    ...     gmm_type='two_step',
    ...     max_lags=3,
    ...     collapse=True
    ... )
    >>> print(f"Points persistence: {result.coefficients['lag(points, 1)']:.3f}")
    >>> print(f"AR(2) valid: {result.ar2_pvalue > 0.05}")
    """

    coefficients: pd.Series
    std_errors: pd.Series
    t_stats: pd.Series
    p_values: pd.Series
    n_obs: int
    n_entities: int
    n_timeperiods: int
    n_instruments: int
    gmm_type: str  # 'one_step' or 'two_step'
    ar1_pvalue: Optional[float] = None
    ar2_pvalue: Optional[float] = None
    hansen_pvalue: Optional[float] = None
    collapsed: bool = False


@dataclass
class SystemGMMResult:
    """Results from Blundell-Bond System GMM estimation.

    The System GMM estimator (Blundell & Bond, 1998) combines the difference
    equation with a levels equation, using additional moment conditions. It's
    more efficient than Difference GMM, especially for persistent series.

    Attributes
    ----------
    coefficients : pd.Series
        Estimated coefficients
    std_errors : pd.Series
        Standard errors (Windmeijer-corrected for two-step)
    t_stats : pd.Series
        t-statistics
    p_values : pd.Series
        p-values for coefficients
    n_obs : int
        Number of observations used
    n_entities : int
        Number of entities (players/teams)
    n_timeperiods : int
        Number of time periods
    n_instruments : int
        Number of instruments used (difference + level)
    gmm_type : str
        'one_step' or 'two_step'
    ar1_pvalue : Optional[float]
        Arellano-Bond AR(1) test p-value
    ar2_pvalue : Optional[float]
        Arellano-Bond AR(2) test p-value
    hansen_pvalue : Optional[float]
        Hansen J-test p-value for all instruments
    diff_hansen_pvalue : Optional[float]
        Difference-in-Hansen test for level instruments
    collapsed : bool
        Whether instruments were collapsed

    Notes
    -----
    - System GMM adds levels equation with first-differenced instruments
    - More efficient than Difference GMM for persistent dependent variables
    - Additional instruments require stronger exogeneity assumptions
    - Difference-in-Hansen tests validity of additional level instruments
    - Preferred when autoregressive parameter is close to 1

    Examples
    --------
    >>> # Team wins with persistent performance
    >>> result = analyzer.system_gmm(
    ...     formula='wins ~ lag(wins, 1) + payroll + avg_age',
    ...     gmm_type='two_step',
    ...     max_lags=4,
    ...     collapse=True
    ... )
    >>> print(f"Wins persistence: {result.coefficients['lag(wins, 1)']:.3f}")
    >>> print(f"Hansen test valid: {result.hansen_pvalue > 0.10}")
    """

    coefficients: pd.Series
    std_errors: pd.Series
    t_stats: pd.Series
    p_values: pd.Series
    n_obs: int
    n_entities: int
    n_timeperiods: int
    n_instruments: int
    gmm_type: str  # 'one_step' or 'two_step'
    ar1_pvalue: Optional[float] = None
    ar2_pvalue: Optional[float] = None
    hansen_pvalue: Optional[float] = None
    diff_hansen_pvalue: Optional[float] = None
    collapsed: bool = False


@dataclass
class GMMDiagnosticResult:
    """Results from GMM diagnostic tests.

    Provides specification tests for dynamic panel GMM models:
    - Arellano-Bond tests for serial correlation
    - Hansen J-test for overidentifying restrictions
    - Difference-in-Hansen test for instrument subsets

    Attributes
    ----------
    ar1_statistic : float
        AR(1) test statistic
    ar1_pvalue : float
        AR(1) p-value (should reject: expect AR(1) in differences)
    ar2_statistic : float
        AR(2) test statistic
    ar2_pvalue : float
        AR(2) p-value (should not reject: no AR(2) in levels)
    hansen_statistic : Optional[float]
        Hansen J-statistic (overidentification)
    hansen_pvalue : Optional[float]
        Hansen J p-value (high values indicate valid instruments)
    hansen_df : Optional[int]
        Degrees of freedom for Hansen test
    diff_hansen_statistic : Optional[float]
        Difference-in-Hansen statistic
    diff_hansen_pvalue : Optional[float]
        Difference-in-Hansen p-value (tests subset of instruments)
    sargan_statistic : Optional[float]
        Sargan test statistic (not robust to heteroscedasticity)
    sargan_pvalue : Optional[float]
        Sargan test p-value

    Notes
    -----
    Interpretation Guide:
    - AR(1): Reject H0 (p < 0.05) → Expected for first-differenced errors
    - AR(2): Do not reject H0 (p > 0.05) → No second-order correlation (good)
    - Hansen: Do not reject H0 (p > 0.10) → Instruments are valid (good)
    - Hansen very high (p → 1) → Possible weak instruments (concerning)
    - Diff-Hansen: Tests additional instruments in System GMM

    Examples
    --------
    >>> # Test GMM specification
    >>> diag = analyzer.gmm_diagnostics(gmm_result)
    >>> print(f"AR(1) rejected: {diag.ar1_pvalue < 0.05} (expected: True)")
    >>> print(f"AR(2) rejected: {diag.ar2_pvalue < 0.05} (expected: False)")
    >>> print(f"Hansen valid: {0.10 < diag.hansen_pvalue < 0.95}")
    """

    ar1_statistic: float
    ar1_pvalue: float
    ar2_statistic: float
    ar2_pvalue: float
    hansen_statistic: Optional[float] = None
    hansen_pvalue: Optional[float] = None
    hansen_df: Optional[int] = None
    diff_hansen_statistic: Optional[float] = None
    diff_hansen_pvalue: Optional[float] = None
    sargan_statistic: Optional[float] = None
    sargan_pvalue: Optional[float] = None


@dataclass
class FirstDifferenceResult:
    """Results from First Difference OLS estimation.

    First-differencing removes time-invariant fixed effects by taking
    differences: Δy_it = y_it - y_i,t-1. Simpler than GMM but doesn't
    handle endogeneity or lagged dependent variables.

    Attributes
    ----------
    coefficients : pd.Series
        Estimated coefficients on differenced variables
    std_errors : pd.Series
        Standard errors
    t_stats : pd.Series
        t-statistics
    p_values : pd.Series
        p-values
    r_squared : float
        R-squared for differenced model
    n_obs : int
        Number of observations (N*(T-1))
    n_entities : int
        Number of entities
    n_timeperiods : int
        Number of time periods
    f_statistic : Optional[float]
        F-statistic for overall significance
    f_pvalue : Optional[float]
        F-test p-value

    Notes
    -----
    - Removes all time-invariant heterogeneity (individual effects)
    - Cannot include time-invariant variables (eliminated by differencing)
    - Suitable when strict exogeneity holds and no lagged dependent variables
    - More efficient than fixed effects when T=2
    - Comparison baseline for GMM estimators

    Examples
    --------
    >>> # Simple performance change model
    >>> result = analyzer.first_difference(
    ...     formula='points ~ minutes + age'
    ... )
    >>> print(f"Effect of Δminutes on Δpoints: {result.coefficients['minutes']:.3f}")
    """

    coefficients: pd.Series
    std_errors: pd.Series
    t_stats: pd.Series
    p_values: pd.Series
    r_squared: float
    n_obs: int
    n_entities: int
    n_timeperiods: int
    f_statistic: Optional[float] = None
    f_pvalue: Optional[float] = None


class PanelDataAnalyzer:
    """
    Panel data analysis for multi-entity, multi-period NBA data.

    Supports fixed effects, random effects, pooled OLS, and various
    panel data diagnostics for analyzing player/team performance
    across seasons.

    Example:
        >>> import pandas as pd
        >>> import numpy as np
        >>> data = pd.DataFrame({
        ...     'player_id': ['A', 'A', 'B', 'B'] * 10,
        ...     'season': [2020, 2021, 2020, 2021] * 10,
        ...     'points': np.random.poisson(20, 40),
        ...     'minutes': np.random.uniform(25, 35, 40)
        ... })
        >>> analyzer = PanelDataAnalyzer(
        ...     data, entity_col='player_id', time_col='season', target_col='points'
        ... )
        >>> fe_result = analyzer.fixed_effects('points ~ minutes')
    """

    def __init__(
        self, data: pd.DataFrame, entity_col: str, time_col: str, target_col: str
    ):
        """
        Initialize PanelDataAnalyzer.

        Args:
            data: DataFrame containing panel data
            entity_col: Column identifying entities (player_id, team_id)
            time_col: Column identifying time periods (season, game_number)
            target_col: Column containing dependent variable

        Raises:
            ValueError: If columns not in data or panel structure invalid
        """
        # Validate columns
        for col in [entity_col, time_col, target_col]:
            if col not in data.columns:
                raise ValueError(f"Column '{col}' not found in data")

        self.data = data.copy()
        self.entity_col = entity_col
        self.time_col = time_col
        self.target_col = target_col

        # Set multi-index
        self.data = self.data.set_index([entity_col, time_col])

        # Store panel dimensions
        self.n_entities = len(self.data.index.get_level_values(0).unique())
        self.n_timeperiods = len(self.data.index.get_level_values(1).unique())
        self.n_obs = len(self.data)

        logger.info(
            f"Panel data initialized: {self.n_entities} entities, "
            f"{self.n_timeperiods} time periods, {self.n_obs} observations"
        )

    def balance_check(self) -> Dict[str, Any]:
        """
        Check if panel is balanced (equal observations per entity).

        Returns:
            Dictionary with balance information
        """
        entity_counts = self.data.groupby(level=0).size()

        is_balanced = len(entity_counts.unique()) == 1

        return {
            "is_balanced": is_balanced,
            "min_periods": int(entity_counts.min()),
            "max_periods": int(entity_counts.max()),
            "mean_periods": float(entity_counts.mean()),
            "n_entities": self.n_entities,
            "n_timeperiods": self.n_timeperiods,
        }

    def pooled_ols(self, formula: str) -> PanelModelResult:
        """
        Estimate pooled OLS model (ignores panel structure).

        Args:
            formula: Model formula (e.g., 'points ~ minutes + age')

        Returns:
            PanelModelResult
        """
        model = PooledOLS.from_formula(formula, data=self.data)
        result = model.fit()

        return self._extract_panel_result(result, "pooled_ols")

    def fixed_effects(
        self, formula: str, entity_effects: bool = True, time_effects: bool = False
    ) -> PanelModelResult:
        """
        Estimate fixed effects (within) model.

        Args:
            formula: Model formula
            entity_effects: Include entity (player/team) fixed effects
            time_effects: Include time (season) fixed effects

        Returns:
            PanelModelResult
        """
        # Add EntityEffects and TimeEffects to formula if requested
        formula_with_effects = formula
        if entity_effects:
            formula_with_effects += " + EntityEffects"
        if time_effects:
            formula_with_effects += " + TimeEffects"

        model = PanelOLS.from_formula(formula_with_effects, data=self.data)
        result = model.fit()

        panel_result = self._extract_panel_result(result, "fixed_effects")

        # Extract entity/time effects if present
        if entity_effects and hasattr(result, "estimated_effects"):
            panel_result.entity_effects = result.estimated_effects

        return panel_result

    def random_effects(self, formula: str) -> PanelModelResult:
        """
        Estimate random effects (GLS) model.

        Args:
            formula: Model formula

        Returns:
            PanelModelResult
        """
        model = RandomEffects.from_formula(formula, data=self.data)
        result = model.fit()

        return self._extract_panel_result(result, "random_effects")

    def _extract_panel_result(
        self, result: PanelResults, model_type: str
    ) -> PanelModelResult:
        """Extract PanelModelResult from linearmodels result."""

        # Basic stats
        coefficients = result.params
        std_errors = result.std_errors
        t_stats = result.tstats
        p_values = result.pvalues

        # R-squared values
        r_squared = result.rsquared if hasattr(result, "rsquared") else 0.0
        r_squared_within = (
            result.rsquared_within if hasattr(result, "rsquared_within") else None
        )
        r_squared_between = (
            result.rsquared_between if hasattr(result, "rsquared_between") else None
        )
        r_squared_overall = (
            result.rsquared_overall if hasattr(result, "rsquared_overall") else None
        )

        # F-statistic
        f_stat = result.f_statistic.stat if hasattr(result, "f_statistic") else None
        f_pval = result.f_statistic.pval if hasattr(result, "f_statistic") else None

        return PanelModelResult(
            coefficients=coefficients,
            std_errors=std_errors,
            t_stats=t_stats,
            p_values=p_values,
            r_squared=r_squared,
            r_squared_within=r_squared_within,
            r_squared_between=r_squared_between,
            r_squared_overall=r_squared_overall,
            f_statistic=f_stat,
            f_pvalue=f_pval,
            n_obs=result.nobs,
            n_entities=self.n_entities,
            n_timeperiods=self.n_timeperiods,
            model_type=model_type,
        )

    def hausman_test(
        self,
        formula: str,
        fe_result: Optional[PanelModelResult] = None,
        re_result: Optional[PanelModelResult] = None,
    ) -> Dict[str, Any]:
        """
        Hausman test for choosing between FE and RE models.

        H0: Random effects model is consistent and efficient
        H1: Fixed effects model is consistent (reject RE)

        Args:
            formula: Model formula
            fe_result: Pre-computed FE result (optional)
            re_result: Pre-computed RE result (optional)

        Returns:
            Dictionary with test results
        """
        # Estimate models if not provided
        if fe_result is None:
            fe_result = self.fixed_effects(formula)

        if re_result is None:
            re_result = self.random_effects(formula)

        # Hausman test statistic
        # H = (b_FE - b_RE)' * [Var(b_FE) - Var(b_RE)]^(-1) * (b_FE - b_RE)

        b_diff = fe_result.coefficients - re_result.coefficients

        var_diff = np.diag(fe_result.std_errors**2) - np.diag(re_result.std_errors**2)

        # Test statistic
        try:
            h_stat = float(b_diff.T @ np.linalg.inv(var_diff) @ b_diff)
            df = len(b_diff)
            p_value = float(1 - stats.chi2.cdf(h_stat, df))

            # Interpret
            use_fe = p_value < 0.05  # Reject RE if p < 0.05

            return {
                "h_statistic": h_stat,
                "p_value": p_value,
                "degrees_of_freedom": df,
                "recommendation": "fixed_effects" if use_fe else "random_effects",
            }

        except np.linalg.LinAlgError:
            logger.warning("Hausman test: variance matrix not positive definite")
            return {
                "h_statistic": np.nan,
                "p_value": np.nan,
                "degrees_of_freedom": len(b_diff),
                "recommendation": "inconclusive",
            }

    def f_test_effects(self, formula: str) -> Dict[str, Any]:
        """
        F-test for presence of entity effects (pooled vs FE).

        H0: Pooled OLS is adequate (no entity effects)
        H1: Fixed effects needed

        Args:
            formula: Model formula

        Returns:
            Dictionary with F-test results
        """
        # Estimate both models
        pooled_result = self.pooled_ols(formula)
        fe_result = self.fixed_effects(formula, entity_effects=True)

        # Manual calculation
        # F = [(RSS_pooled - RSS_fe) / (N-1)] / [RSS_fe / (NT - N - K)]

        rss_pooled = pooled_result.n_obs * (1 - pooled_result.r_squared)
        rss_fe = fe_result.n_obs * (1 - fe_result.r_squared)

        df1 = self.n_entities - 1
        k = len(fe_result.coefficients)
        df2 = fe_result.n_obs - self.n_entities - k

        if df2 <= 0:
            logger.warning(f"Invalid degrees of freedom for F-test: df2={df2}")
            return {
                "f_statistic": np.nan,
                "p_value": np.nan,
                "df1": df1,
                "df2": df2,
                "recommendation": "inconclusive",
            }

        # Handle edge cases
        if rss_fe == 0 or np.isclose(rss_fe, 0):
            logger.warning("FE model has perfect fit (RSS=0), F-test inconclusive")
            return {
                "f_statistic": np.inf,
                "p_value": 0.0,
                "df1": df1,
                "df2": df2,
                "recommendation": "fixed_effects",
            }

        # Calculate F-statistic
        f_stat = float(((rss_pooled - rss_fe) / df1) / (rss_fe / df2))

        # If F-stat is negative, pooled model fits better (shouldn't happen but can in practice)
        if f_stat < 0:
            logger.warning(
                f"F-statistic is negative ({f_stat:.4f}), pooled model fits better"
            )
            return {
                "f_statistic": 0.0,
                "p_value": 1.0,
                "df1": df1,
                "df2": df2,
                "recommendation": "pooled_ols",
            }

        p_value = float(1 - stats.f.cdf(f_stat, df1, df2))
        use_fe = p_value < 0.05

        return {
            "f_statistic": f_stat,
            "p_value": p_value,
            "df1": df1,
            "df2": df2,
            "recommendation": "fixed_effects" if use_fe else "pooled_ols",
        }

    def clustered_standard_errors(
        self, formula: str, cluster_entity: bool = True
    ) -> PanelModelResult:
        """
        Estimate model with clustered standard errors.

        Args:
            formula: Model formula
            cluster_entity: Cluster by entity (default: True)

        Returns:
            PanelModelResult with clustered SE
        """
        model = PanelOLS.from_formula(formula, data=self.data)

        # Fit with clustered standard errors
        result = model.fit(cov_type="clustered", cluster_entity=cluster_entity)

        return self._extract_panel_result(result, "clustered_se")

    # ==============================================================================
    # Dynamic Panel GMM Methods (Phase 2 Day 6)
    # ==============================================================================

    def first_difference(
        self, formula: str, cluster_entity: bool = True
    ) -> FirstDifferenceResult:
        """
        Estimate first-difference model to remove fixed effects.

        First-differencing transforms the model to Δy_it = Δx_it'β + Δε_it,
        eliminating time-invariant individual effects. Simpler than GMM but
        does not handle endogeneity or lagged dependent variables.

        Args:
            formula: Model formula (e.g., 'points ~ minutes + age')
            cluster_entity: Cluster standard errors by entity (default: True)

        Returns:
            FirstDifferenceResult

        Raises:
            ValueError: If formula is invalid

        Examples:
            >>> # Analyze change in player points
            >>> result = analyzer.first_difference(
            ...     formula='points ~ minutes + age'
            ... )
            >>> print(f"Effect of Δminutes: {result.coefficients['minutes']:.3f}")
            >>>
            >>> # Team performance changes
            >>> result = analyzer.first_difference(
            ...     formula='wins ~ payroll + avg_age',
            ...     cluster_entity=True
            ... )

        Notes:
            - Removes all time-invariant variables (e.g., player position)
            - Suitable when T=2 or strict exogeneity holds
            - Cannot include lagged dependent variables (endogeneity)
            - Clustered SE recommended for heteroscedasticity
        """
        model = FirstDifferenceOLS.from_formula(formula, data=self.data)

        # Fit with optional clustering
        if cluster_entity:
            result = model.fit(cov_type="clustered", cluster_entity=True)
        else:
            result = model.fit()

        # Extract results
        coefficients = result.params
        std_errors = result.std_errors
        t_stats = result.tstats
        p_values = result.pvalues
        r_squared = result.rsquared if hasattr(result, "rsquared") else 0.0
        f_stat = result.f_statistic.stat if hasattr(result, "f_statistic") else None
        f_pval = result.f_statistic.pval if hasattr(result, "f_statistic") else None

        return FirstDifferenceResult(
            coefficients=coefficients,
            std_errors=std_errors,
            t_stats=t_stats,
            p_values=p_values,
            r_squared=r_squared,
            n_obs=result.nobs,
            n_entities=self.n_entities,
            n_timeperiods=self.n_timeperiods,
            f_statistic=f_stat,
            f_pvalue=f_pval,
        )

    def difference_gmm(
        self,
        formula: str,
        gmm_type: str = "two_step",
        max_lags: int = 3,
        collapse: bool = False,
    ) -> DifferenceGMMResult:
        """
        Estimate Arellano-Bond Difference GMM for dynamic panel data.

        Difference GMM (Arellano & Bond, 1991) removes fixed effects via
        first-differencing and uses lagged levels as instruments. Designed
        for models with lagged dependent variables and endogenous regressors.

        Args:
            formula: Model formula with lag notation (e.g., 'points ~ lag(points, 1) + minutes')
                     Use 'lag(var, n)' for lagged variables
            gmm_type: 'one_step' or 'two_step' (default: 'two_step')
                     Two-step is more efficient with Windmeijer SE correction
            max_lags: Maximum lags for instruments (default: 3)
                     Higher values use more instruments but risk overfitting
            collapse: Collapse instrument matrix to reduce proliferation (default: False)

        Returns:
            DifferenceGMMResult with coefficients and diagnostic tests

        Raises:
            ImportError: If pydynpd not available
            ValueError: If formula invalid or data structure incompatible

        Examples:
            >>> # Player scoring persistence
            >>> result = analyzer.difference_gmm(
            ...     formula='points ~ lag(points, 1) + minutes + age',
            ...     gmm_type='two_step',
            ...     max_lags=3,
            ...     collapse=True
            ... )
            >>> print(f"Points persistence: {result.coefficients['lag(points, 1)']:.3f}")
            >>> print(f"AR(1) rejected: {result.ar1_pvalue < 0.05} (expected: True)")
            >>> print(f"AR(2) valid: {result.ar2_pvalue > 0.05} (expected: True)")
            >>>
            >>> # Team wins dynamics
            >>> result = analyzer.difference_gmm(
            ...     formula='wins ~ lag(wins, 1) + lag(wins, 2) + payroll',
            ...     gmm_type='two_step',
            ...     max_lags=4
            ... )

        Notes:
            - Requires T >= 4 for identification with max_lags=2
            - AR(1) test should reject (expect autocorrelation in differences)
            - AR(2) test should not reject (no 2nd-order correlation in levels)
            - Hansen test p-value should be moderate (0.10 < p < 0.95)
            - Use collapse=True if instruments >> observations
        """
        if not PYDYNPD_AVAILABLE:
            raise ImportError(
                "pydynpd not available. Install with: pip install pydynpd>=0.2.1"
            )

        # Build pydynpd command string
        # Format: "dependent_var | independent_vars | gmm(dependent, lags) | nolevel"
        # pydynpd uses its own syntax, so we need to convert our formula

        # Parse formula (simplified - assumes format like 'y ~ x1 + x2 + lag(y, 1)')
        parts = formula.replace(" ", "").split("~")
        if len(parts) != 2:
            raise ValueError("Formula must be of form 'y ~ x1 + x2'")

        dependent_var = parts[0]
        independent_vars = parts[1].split("+")

        # Separate lagged dependent vars from other regressors
        lag_terms = [v for v in independent_vars if v.startswith("lag(")]
        other_vars = [v for v in independent_vars if not v.startswith("lag(")]

        # Build pydynpd command
        # Simplified: "y | x1 x2 | gmm(y, 2:4) | nolevel timedumm"
        cmd_vars = " ".join(other_vars) if other_vars else ""
        cmd_gmm = f"gmm({dependent_var}, 2:{max_lags+2})"
        if collapse:
            cmd_gmm += " collapse"

        command_str = f"{dependent_var} | {cmd_vars} | {cmd_gmm} | nolevel"
        if gmm_type == "two_step":
            command_str += " twostep"

        # Reset index to get entity and time columns
        df_reset = self.data.reset_index()
        entity_col = df_reset.columns[0]
        time_col = df_reset.columns[1]

        try:
            # Estimate using pydynpd
            gmm = pydynpd_reg.abond(
                command_str, df_reset, identifiers=[entity_col, time_col]
            )

            # Extract results from pydynpd output
            # Note: pydynpd stores results in specific attributes
            coefficients = pd.Series(gmm.models[0].beta, index=gmm.models[0].var_names)
            std_errors = pd.Series(
                np.sqrt(np.diag(gmm.models[0].variance)), index=gmm.models[0].var_names
            )
            t_stats = coefficients / std_errors
            p_values = 2 * (1 - stats.norm.cdf(np.abs(t_stats)))

            # Extract diagnostic test results
            ar1_pval = gmm.models[0].ar1_pvalue if hasattr(gmm.models[0], "ar1_pvalue") else None
            ar2_pval = gmm.models[0].ar2_pvalue if hasattr(gmm.models[0], "ar2_pvalue") else None
            hansen_pval = gmm.models[0].hansen_pvalue if hasattr(gmm.models[0], "hansen_pvalue") else None

            n_instruments = (
                gmm.models[0].n_instruments if hasattr(gmm.models[0], "n_instruments") else 0
            )

            return DifferenceGMMResult(
                coefficients=coefficients,
                std_errors=std_errors,
                t_stats=t_stats,
                p_values=p_values,
                n_obs=gmm.models[0].n_obs if hasattr(gmm.models[0], "n_obs") else self.n_obs,
                n_entities=self.n_entities,
                n_timeperiods=self.n_timeperiods,
                n_instruments=n_instruments,
                gmm_type=gmm_type,
                ar1_pvalue=ar1_pval,
                ar2_pvalue=ar2_pval,
                hansen_pvalue=hansen_pval,
                collapsed=collapse,
            )

        except Exception as e:
            logger.error(f"Difference GMM estimation failed: {str(e)}")
            raise ValueError(f"GMM estimation failed: {str(e)}")

    def system_gmm(
        self,
        formula: str,
        gmm_type: str = "two_step",
        max_lags: int = 3,
        collapse: bool = False,
    ) -> SystemGMMResult:
        """
        Estimate Blundell-Bond System GMM for dynamic panel data.

        System GMM (Blundell & Bond, 1998) augments Difference GMM by adding
        a levels equation with first-differenced instruments. More efficient
        than Difference GMM, especially for persistent dependent variables.

        Args:
            formula: Model formula with lag notation
            gmm_type: 'one_step' or 'two_step' (default: 'two_step')
            max_lags: Maximum lags for instruments (default: 3)
            collapse: Collapse instrument matrix (default: False)

        Returns:
            SystemGMMResult with coefficients and diagnostic tests

        Raises:
            ImportError: If pydynpd not available
            ValueError: If formula invalid

        Examples:
            >>> # Highly persistent player performance
            >>> result = analyzer.system_gmm(
            ...     formula='points ~ lag(points, 1) + minutes + age',
            ...     gmm_type='two_step',
            ...     max_lags=4,
            ...     collapse=True
            ... )
            >>> print(f"Persistence: {result.coefficients['lag(points, 1)']:.3f}")
            >>> print(f"Hansen valid: {0.10 < result.hansen_pvalue < 0.95}")
            >>> print(f"Diff-Hansen: {result.diff_hansen_pvalue:.3f}")
            >>>
            >>> # Team wins with strong persistence
            >>> result = analyzer.system_gmm(
            ...     formula='wins ~ lag(wins, 1) + payroll + avg_age',
            ...     gmm_type='two_step'
            ... )

        Notes:
            - System GMM = Difference GMM + Levels equation
            - Levels use Δy_{t-1}, Δx_{t-1} as instruments
            - More efficient for AR(1) coefficient close to 1
            - Requires stronger exogeneity assumptions
            - Difference-in-Hansen tests validity of level instruments
            - Prefer System GMM when Difference GMM shows weak instruments
        """
        if not PYDYNPD_AVAILABLE:
            raise ImportError(
                "pydynpd not available. Install with: pip install pydynpd>=0.2.1"
            )

        # Parse formula (same as difference_gmm)
        parts = formula.replace(" ", "").split("~")
        if len(parts) != 2:
            raise ValueError("Formula must be of form 'y ~ x1 + x2'")

        dependent_var = parts[0]
        independent_vars = parts[1].split("+")

        lag_terms = [v for v in independent_vars if v.startswith("lag(")]
        other_vars = [v for v in independent_vars if not v.startswith("lag(")]

        # Build pydynpd command for System GMM
        # Key difference: remove "nolevel" to include levels equation
        cmd_vars = " ".join(other_vars) if other_vars else ""
        cmd_gmm = f"gmm({dependent_var}, 2:{max_lags+2})"
        if collapse:
            cmd_gmm += " collapse"

        command_str = f"{dependent_var} | {cmd_vars} | {cmd_gmm}"
        if gmm_type == "two_step":
            command_str += " twostep"

        # Reset index
        df_reset = self.data.reset_index()
        entity_col = df_reset.columns[0]
        time_col = df_reset.columns[1]

        try:
            # Estimate System GMM
            gmm = pydynpd_reg.abond(
                command_str, df_reset, identifiers=[entity_col, time_col]
            )

            # Extract results
            coefficients = pd.Series(gmm.models[0].beta, index=gmm.models[0].var_names)
            std_errors = pd.Series(
                np.sqrt(np.diag(gmm.models[0].variance)), index=gmm.models[0].var_names
            )
            t_stats = coefficients / std_errors
            p_values = 2 * (1 - stats.norm.cdf(np.abs(t_stats)))

            # Extract diagnostics
            ar1_pval = gmm.models[0].ar1_pvalue if hasattr(gmm.models[0], "ar1_pvalue") else None
            ar2_pval = gmm.models[0].ar2_pvalue if hasattr(gmm.models[0], "ar2_pvalue") else None
            hansen_pval = gmm.models[0].hansen_pvalue if hasattr(gmm.models[0], "hansen_pvalue") else None
            diff_hansen_pval = (
                gmm.models[0].diff_hansen_pvalue
                if hasattr(gmm.models[0], "diff_hansen_pvalue")
                else None
            )

            n_instruments = (
                gmm.models[0].n_instruments if hasattr(gmm.models[0], "n_instruments") else 0
            )

            return SystemGMMResult(
                coefficients=coefficients,
                std_errors=std_errors,
                t_stats=t_stats,
                p_values=p_values,
                n_obs=gmm.models[0].n_obs if hasattr(gmm.models[0], "n_obs") else self.n_obs,
                n_entities=self.n_entities,
                n_timeperiods=self.n_timeperiods,
                n_instruments=n_instruments,
                gmm_type=gmm_type,
                ar1_pvalue=ar1_pval,
                ar2_pvalue=ar2_pval,
                hansen_pvalue=hansen_pval,
                diff_hansen_pvalue=diff_hansen_pval,
                collapsed=collapse,
            )

        except Exception as e:
            logger.error(f"System GMM estimation failed: {str(e)}")
            raise ValueError(f"System GMM estimation failed: {str(e)}")

    def gmm_diagnostics(
        self, gmm_result: Union[DifferenceGMMResult, SystemGMMResult]
    ) -> GMMDiagnosticResult:
        """
        Extract and interpret GMM diagnostic tests from estimated results.

        Provides comprehensive diagnostics for dynamic panel GMM models:
        - Arellano-Bond tests for serial correlation (AR(1), AR(2))
        - Hansen J-test for overidentifying restrictions
        - Difference-in-Hansen test (System GMM only)

        Args:
            gmm_result: Previously estimated Difference or System GMM result

        Returns:
            GMMDiagnosticResult with test statistics and p-values

        Examples:
            >>> # After estimating GMM
            >>> gmm_res = analyzer.difference_gmm(formula='points ~ lag(points, 1) + minutes')
            >>> diag = analyzer.gmm_diagnostics(gmm_res)
            >>>
            >>> # Interpret diagnostics
            >>> print("Diagnostic Results:")
            >>> print(f"AR(1) test: stat={diag.ar1_statistic:.2f}, p={diag.ar1_pvalue:.3f}")
            >>> print(f"  → Expected to reject (p < 0.05): {diag.ar1_pvalue < 0.05}")
            >>> print(f"AR(2) test: stat={diag.ar2_statistic:.2f}, p={diag.ar2_pvalue:.3f}")
            >>> print(f"  → Should not reject (p > 0.05): {diag.ar2_pvalue > 0.05}")
            >>> print(f"Hansen J: stat={diag.hansen_statistic:.2f}, p={diag.hansen_pvalue:.3f}")
            >>> print(f"  → Valid instruments (0.10 < p < 0.95): {0.10 < diag.hansen_pvalue < 0.95}")

        Notes:
            Interpretation Guide:

            AR(1) Test:
            - H0: No first-order autocorrelation in differenced errors
            - Expected: Reject (p < 0.05) due to MA(1) process from differencing
            - Rejection confirms model is correctly differenced

            AR(2) Test:
            - H0: No second-order autocorrelation in differenced errors
            - Expected: Do not reject (p > 0.05)
            - Rejection suggests model misspecification

            Hansen J Test:
            - H0: Overidentifying restrictions are valid (instruments exogenous)
            - Expected: 0.10 < p-value < 0.95
            - Very low p (< 0.10): Instruments likely invalid
            - Very high p (> 0.95): Possible weak instruments

            Difference-in-Hansen (System GMM):
            - Tests validity of additional level instruments
            - Expected: p > 0.10
            - Rejection suggests level instruments are invalid
        """
        # Extract test statistics from GMM result
        ar1_stat = (
            stats.norm.ppf(1 - gmm_result.ar1_pvalue / 2)
            if gmm_result.ar1_pvalue is not None
            else np.nan
        )
        ar2_stat = (
            stats.norm.ppf(1 - gmm_result.ar2_pvalue / 2)
            if gmm_result.ar2_pvalue is not None
            else np.nan
        )

        # Hansen test statistics (approximated from p-value if not directly available)
        hansen_df = (
            gmm_result.n_instruments - len(gmm_result.coefficients)
            if gmm_result.n_instruments > 0
            else 0
        )

        hansen_stat = (
            stats.chi2.ppf(1 - gmm_result.hansen_pvalue, hansen_df)
            if gmm_result.hansen_pvalue is not None and hansen_df > 0
            else None
        )

        # Difference-in-Hansen (System GMM only)
        diff_hansen_stat = None
        diff_hansen_pval = None
        if isinstance(gmm_result, SystemGMMResult):
            if gmm_result.diff_hansen_pvalue is not None:
                diff_hansen_pval = gmm_result.diff_hansen_pvalue
                # Approximate statistic from p-value
                diff_hansen_stat = stats.chi2.ppf(1 - diff_hansen_pval, df=1)

        return GMMDiagnosticResult(
            ar1_statistic=ar1_stat,
            ar1_pvalue=gmm_result.ar1_pvalue if gmm_result.ar1_pvalue is not None else np.nan,
            ar2_statistic=ar2_stat,
            ar2_pvalue=gmm_result.ar2_pvalue if gmm_result.ar2_pvalue is not None else np.nan,
            hansen_statistic=hansen_stat,
            hansen_pvalue=gmm_result.hansen_pvalue,
            hansen_df=hansen_df if hansen_df > 0 else None,
            diff_hansen_statistic=diff_hansen_stat,
            diff_hansen_pvalue=diff_hansen_pval,
        )
