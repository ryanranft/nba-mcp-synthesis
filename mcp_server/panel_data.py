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
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS, RandomEffects, PooledOLS
from linearmodels.panel.results import PanelResults
import statsmodels.api as sm
from scipy import stats

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
