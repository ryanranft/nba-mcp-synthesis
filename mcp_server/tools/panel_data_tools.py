"""
Panel Data MCP Tools - Phase 10A Agent 8 Module 2.

This module provides MCP tool wrappers for panel data econometric analysis,
exposing the underlying panel data methods as FastMCP tools accessible via
Claude Desktop and other MCP clients.

Implements Phase 10A recommendation rec_0625_1b208ec4:
"Implement Panel Data Models with Fixed and Random Effects"
Priority: 9.0/10, Effort: 40 hours

Tools:
1. panel_diagnostics - Check panel structure and balance
2. pooled_ols_model - Pooled OLS regression (ignores panel structure)
3. fixed_effects_model - Fixed effects (within) regression
4. random_effects_model - Random effects GLS regression
5. hausman_test - Test FE vs RE specification
6. first_difference_model - First differencing for dynamics

Author: Phase 10A Agent 8 Module 2
Date: October 2025
"""

import logging
from typing import Dict, Any, List, Union, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PanelDataTools:
    """
    MCP tool wrappers for panel data econometric analysis.

    This class provides thin wrappers around the PanelDataAnalyzer implementation,
    converting between MCP-friendly data formats (lists, dicts) and the underlying
    pandas-based panel data analysis methods.
    """

    def __init__(self):
        """Initialize PanelDataTools."""
        self.logger = logger

    # =========================================================================
    # Tool 1: Panel Diagnostics
    # =========================================================================

    async def panel_diagnostics(
        self,
        data: List[Dict[str, Any]],
        entity_column: str = "entity_id",
        time_column: str = "time_period",
        target_column: str = "value",
    ) -> Dict[str, Any]:
        """
        Check panel structure and balance.

        Analyzes the panel data structure to determine if it's balanced
        (equal observations per entity) and provides summary statistics
        about the panel dimensions.

        Implements Phase 10A rec_0625_1b208ec4 (Priority: 9.0/10)

        Args:
            data: List of dictionaries containing panel data
            entity_column: Column identifying entities (player_id, team_id)
            time_column: Column identifying time periods (season, game)
            target_column: Column containing dependent variable

        Returns:
            Dictionary containing:
            - is_balanced: Whether panel is balanced
            - n_entities: Number of entities
            - n_timeperiods: Number of time periods
            - n_obs: Total observations
            - min_periods: Minimum periods per entity
            - max_periods: Maximum periods per entity
            - mean_periods: Average periods per entity
            - balance_ratio: Actual/potential observations ratio
            - recommendations: List of analysis recommendations
            - success: True if analysis succeeded
            - error: Error message if failed
        """
        try:
            from mcp_server.panel_data import PanelDataAnalyzer

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Validate required columns
            required_cols = [entity_column, time_column, target_column]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error": f"Missing required columns: {missing_cols}",
                }

            # Create analyzer
            analyzer = PanelDataAnalyzer(
                data=df,
                entity_col=entity_column,
                time_col=time_column,
                target_col=target_column,
            )

            # Get balance check
            balance_info = analyzer.balance_check()

            # Calculate balance ratio
            potential_obs = balance_info["n_entities"] * balance_info["n_timeperiods"]
            actual_obs = analyzer.n_obs
            balance_ratio = actual_obs / potential_obs if potential_obs > 0 else 0

            # Generate recommendations
            recommendations = []
            if balance_info["is_balanced"]:
                recommendations.append(
                    "Panel is balanced - can use standard panel methods"
                )
                recommendations.append(
                    "Consider fixed effects or random effects models"
                )
            else:
                recommendations.append(
                    "Panel is unbalanced - use robust standard errors"
                )
                recommendations.append(
                    "Consider using methods that handle unbalanced panels"
                )

            if balance_info["n_timeperiods"] < 5:
                recommendations.append(
                    "Short time dimension - fixed effects may have limited power"
                )

            if balance_info["n_entities"] < 20:
                recommendations.append(
                    "Small number of entities - random effects may be unreliable"
                )

            # Return results
            return {
                "success": True,
                "is_balanced": balance_info["is_balanced"],
                "n_entities": balance_info["n_entities"],
                "n_timeperiods": balance_info["n_timeperiods"],
                "n_obs": actual_obs,
                "min_periods": balance_info["min_periods"],
                "max_periods": balance_info["max_periods"],
                "mean_periods": balance_info["mean_periods"],
                "balance_ratio": float(balance_ratio),
                "recommendations": recommendations,
            }

        except Exception as e:
            self.logger.error(f"Panel diagnostics failed: {str(e)}")
            return {"success": False, "error": f"Panel diagnostics failed: {str(e)}"}

    # =========================================================================
    # Tool 2: Pooled OLS Model
    # =========================================================================

    async def pooled_ols_model(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        entity_column: str = "entity_id",
        time_column: str = "time_period",
        target_column: str = "value",
    ) -> Dict[str, Any]:
        """
        Estimate pooled OLS model (ignores panel structure).

        Pooled OLS treats all observations as independent, ignoring the
        panel structure. This provides a baseline for comparison with
        panel methods that account for entity/time effects.

        Implements Phase 10A rec_0625_1b208ec4 (Priority: 9.0/10)

        Args:
            data: List of dictionaries containing panel data
            formula: Model formula (e.g., 'value ~ x1 + x2')
            entity_column: Column identifying entities
            time_column: Column identifying time periods
            target_column: Column containing dependent variable

        Returns:
            Dictionary containing:
            - coefficients: Dict of coefficient estimates
            - std_errors: Dict of standard errors
            - t_stats: Dict of t-statistics
            - p_values: Dict of p-values
            - r_squared: R-squared value
            - f_statistic: F-statistic for overall significance
            - f_pvalue: P-value for F-statistic
            - n_obs: Number of observations
            - n_entities: Number of entities
            - n_timeperiods: Number of time periods
            - model_type: 'pooled_ols'
            - interpretation: Human-readable interpretation
            - recommendations: List of next steps
            - success: True if estimation succeeded
            - error: Error message if failed
        """
        try:
            from mcp_server.panel_data import PanelDataAnalyzer

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Validate required columns
            required_cols = [entity_column, time_column, target_column]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error": f"Missing required columns: {missing_cols}",
                }

            # Create analyzer
            analyzer = PanelDataAnalyzer(
                data=df,
                entity_col=entity_column,
                time_col=time_column,
                target_col=target_column,
            )

            # Estimate pooled OLS
            result = analyzer.pooled_ols(formula)

            # Generate interpretation
            r2 = result.r_squared
            n_coef = len(result.coefficients)
            interpretation = (
                f"Pooled OLS model estimated with R² = {r2:.4f}. "
                f"Model includes {n_coef} coefficients. "
                f"This baseline model ignores panel structure and treats all observations as independent."
            )

            # Generate recommendations
            recommendations = []
            recommendations.append(
                "Compare with fixed effects model to test for entity-specific effects"
            )
            recommendations.append(
                "Use Hausman test to choose between fixed and random effects"
            )
            if result.f_pvalue is not None and result.f_pvalue < 0.05:
                recommendations.append(
                    "Model is statistically significant overall (F-test p < 0.05)"
                )

            # Return results
            return {
                "success": True,
                "coefficients": result.coefficients.to_dict(),
                "std_errors": result.std_errors.to_dict(),
                "t_stats": result.t_stats.to_dict(),
                "p_values": result.p_values.to_dict(),
                "r_squared": float(result.r_squared),
                "f_statistic": (
                    float(result.f_statistic)
                    if result.f_statistic is not None
                    else None
                ),
                "f_pvalue": (
                    float(result.f_pvalue) if result.f_pvalue is not None else None
                ),
                "n_obs": result.n_obs,
                "n_entities": result.n_entities,
                "n_timeperiods": result.n_timeperiods,
                "model_type": "pooled_ols",
                "interpretation": interpretation,
                "recommendations": recommendations,
            }

        except Exception as e:
            self.logger.error(f"Pooled OLS estimation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Pooled OLS estimation failed: {str(e)}",
            }

    # =========================================================================
    # Tool 3: Fixed Effects Model
    # =========================================================================

    async def fixed_effects_model(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        entity_column: str = "entity_id",
        time_column: str = "time_period",
        target_column: str = "value",
        entity_effects: bool = True,
        time_effects: bool = False,
    ) -> Dict[str, Any]:
        """
        Estimate fixed effects (within) model.

        Fixed effects estimation removes entity-specific (and optionally
        time-specific) unobserved heterogeneity by demeaning within each
        entity/time. This controls for all time-invariant confounders.

        Implements Phase 10A rec_0625_1b208ec4 (Priority: 9.0/10)

        Args:
            data: List of dictionaries containing panel data
            formula: Model formula (e.g., 'value ~ x1 + x2')
            entity_column: Column identifying entities
            time_column: Column identifying time periods
            target_column: Column containing dependent variable
            entity_effects: Include entity fixed effects
            time_effects: Include time fixed effects

        Returns:
            Dictionary containing:
            - coefficients: Dict of coefficient estimates
            - std_errors: Dict of standard errors
            - t_stats: Dict of t-statistics
            - p_values: Dict of p-values
            - r_squared: Overall R-squared
            - r_squared_within: Within R-squared (variation within entities)
            - r_squared_between: Between R-squared (variation between entities)
            - f_statistic: F-statistic
            - f_pvalue: P-value for F-statistic
            - n_obs: Number of observations
            - n_entities: Number of entities
            - n_timeperiods: Number of time periods
            - entity_effects_included: Whether entity effects included
            - time_effects_included: Whether time effects included
            - model_type: 'fixed_effects'
            - interpretation: Human-readable interpretation
            - recommendations: List of next steps
            - success: True if estimation succeeded
            - error: Error message if failed
        """
        try:
            from mcp_server.panel_data import PanelDataAnalyzer

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Validate required columns
            required_cols = [entity_column, time_column, target_column]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error": f"Missing required columns: {missing_cols}",
                }

            # Create analyzer
            analyzer = PanelDataAnalyzer(
                data=df,
                entity_col=entity_column,
                time_col=time_column,
                target_col=target_column,
            )

            # Estimate fixed effects
            result = analyzer.fixed_effects(
                formula=formula,
                entity_effects=entity_effects,
                time_effects=time_effects,
            )

            # Generate interpretation
            effects_type = []
            if entity_effects:
                effects_type.append("entity")
            if time_effects:
                effects_type.append("time")
            effects_str = " and ".join(effects_type) if effects_type else "no"

            r2_within = result.r_squared_within or result.r_squared
            interpretation = (
                f"Fixed effects model estimated with {effects_str} fixed effects. "
                f"Within R² = {r2_within:.4f}, which measures fit of time-varying variables. "
                f"Model controls for all time-invariant entity characteristics."
            )

            # Generate recommendations
            recommendations = []
            if entity_effects and not time_effects:
                recommendations.append(
                    "Consider adding time effects if there are common time trends"
                )
            recommendations.append(
                "Use Hausman test to compare with random effects model"
            )
            recommendations.append(
                "Consider clustered standard errors if within-entity correlation suspected"
            )

            # Return results
            return {
                "success": True,
                "coefficients": result.coefficients.to_dict(),
                "std_errors": result.std_errors.to_dict(),
                "t_stats": result.t_stats.to_dict(),
                "p_values": result.p_values.to_dict(),
                "r_squared": float(result.r_squared),
                "r_squared_within": (
                    float(result.r_squared_within)
                    if result.r_squared_within is not None
                    else None
                ),
                "r_squared_between": (
                    float(result.r_squared_between)
                    if result.r_squared_between is not None
                    else None
                ),
                "f_statistic": (
                    float(result.f_statistic)
                    if result.f_statistic is not None
                    else None
                ),
                "f_pvalue": (
                    float(result.f_pvalue) if result.f_pvalue is not None else None
                ),
                "n_obs": result.n_obs,
                "n_entities": result.n_entities,
                "n_timeperiods": result.n_timeperiods,
                "entity_effects_included": entity_effects,
                "time_effects_included": time_effects,
                "model_type": "fixed_effects",
                "interpretation": interpretation,
                "recommendations": recommendations,
            }

        except Exception as e:
            self.logger.error(f"Fixed effects estimation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Fixed effects estimation failed: {str(e)}",
            }

    # =========================================================================
    # Tool 4: Random Effects Model
    # =========================================================================

    async def random_effects_model(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        entity_column: str = "entity_id",
        time_column: str = "time_period",
        target_column: str = "value",
    ) -> Dict[str, Any]:
        """
        Estimate random effects (GLS) model.

        Random effects assumes entity-specific effects are uncorrelated with
        regressors and uses GLS estimation to account for within-entity
        correlation. More efficient than fixed effects if assumption holds.

        Implements Phase 10A rec_0625_1b208ec4 (Priority: 9.0/10)

        Args:
            data: List of dictionaries containing panel data
            formula: Model formula (e.g., 'value ~ x1 + x2')
            entity_column: Column identifying entities
            time_column: Column identifying time periods
            target_column: Column containing dependent variable

        Returns:
            Dictionary containing:
            - coefficients: Dict of coefficient estimates
            - std_errors: Dict of standard errors
            - t_stats: Dict of t-statistics
            - p_values: Dict of p-values
            - r_squared: Overall R-squared
            - r_squared_within: Within R-squared
            - r_squared_between: Between R-squared
            - r_squared_overall: Overall R-squared
            - f_statistic: F-statistic
            - f_pvalue: P-value for F-statistic
            - n_obs: Number of observations
            - n_entities: Number of entities
            - n_timeperiods: Number of time periods
            - model_type: 'random_effects'
            - interpretation: Human-readable interpretation
            - recommendations: List of next steps
            - success: True if estimation succeeded
            - error: Error message if failed
        """
        try:
            from mcp_server.panel_data import PanelDataAnalyzer

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Validate required columns
            required_cols = [entity_column, time_column, target_column]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error": f"Missing required columns: {missing_cols}",
                }

            # Create analyzer
            analyzer = PanelDataAnalyzer(
                data=df,
                entity_col=entity_column,
                time_col=time_column,
                target_col=target_column,
            )

            # Estimate random effects
            result = analyzer.random_effects(formula)

            # Generate interpretation
            r2_overall = result.r_squared_overall or result.r_squared
            r2_within = result.r_squared_within or 0
            r2_between = result.r_squared_between or 0

            interpretation = (
                f"Random effects model estimated with overall R² = {r2_overall:.4f}. "
                f"Within R² = {r2_within:.4f}, Between R² = {r2_between:.4f}. "
                f"Model assumes entity effects are uncorrelated with regressors."
            )

            # Generate recommendations
            recommendations = []
            recommendations.append(
                "Use Hausman test to verify random effects assumption"
            )
            recommendations.append("If Hausman test rejects, use fixed effects instead")
            if r2_between > r2_within:
                recommendations.append(
                    "Between variation is stronger - model captures cross-sectional differences well"
                )
            else:
                recommendations.append(
                    "Within variation is stronger - consider fixed effects model"
                )

            # Return results
            return {
                "success": True,
                "coefficients": result.coefficients.to_dict(),
                "std_errors": result.std_errors.to_dict(),
                "t_stats": result.t_stats.to_dict(),
                "p_values": result.p_values.to_dict(),
                "r_squared": float(result.r_squared),
                "r_squared_within": (
                    float(result.r_squared_within)
                    if result.r_squared_within is not None
                    else None
                ),
                "r_squared_between": (
                    float(result.r_squared_between)
                    if result.r_squared_between is not None
                    else None
                ),
                "r_squared_overall": (
                    float(result.r_squared_overall)
                    if result.r_squared_overall is not None
                    else None
                ),
                "f_statistic": (
                    float(result.f_statistic)
                    if result.f_statistic is not None
                    else None
                ),
                "f_pvalue": (
                    float(result.f_pvalue) if result.f_pvalue is not None else None
                ),
                "n_obs": result.n_obs,
                "n_entities": result.n_entities,
                "n_timeperiods": result.n_timeperiods,
                "model_type": "random_effects",
                "interpretation": interpretation,
                "recommendations": recommendations,
            }

        except Exception as e:
            self.logger.error(f"Random effects estimation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Random effects estimation failed: {str(e)}",
            }

    # =========================================================================
    # Tool 5: Hausman Test
    # =========================================================================

    async def hausman_test(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        entity_column: str = "entity_id",
        time_column: str = "time_period",
        target_column: str = "value",
    ) -> Dict[str, Any]:
        """
        Hausman test for fixed vs random effects specification.

        Tests whether entity-specific effects are correlated with regressors.
        If test rejects (p < 0.05), use fixed effects; otherwise random effects
        is more efficient.

        Implements Phase 10A rec_0625_1b208ec4 (Priority: 9.0/10)

        Args:
            data: List of dictionaries containing panel data
            formula: Model formula (e.g., 'value ~ x1 + x2')
            entity_column: Column identifying entities
            time_column: Column identifying time periods
            target_column: Column containing dependent variable

        Returns:
            Dictionary containing:
            - statistic: Hausman test statistic
            - p_value: P-value for test
            - reject_re: Whether to reject random effects (use FE instead)
            - fe_coefficients: Fixed effects coefficient estimates
            - re_coefficients: Random effects coefficient estimates
            - coefficient_differences: Differences between FE and RE estimates
            - recommendation: Which model to use
            - interpretation: Human-readable interpretation
            - success: True if test succeeded
            - error: Error message if failed
        """
        try:
            from mcp_server.panel_data import PanelDataAnalyzer

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Validate required columns
            required_cols = [entity_column, time_column, target_column]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error": f"Missing required columns: {missing_cols}",
                }

            # Create analyzer
            analyzer = PanelDataAnalyzer(
                data=df,
                entity_col=entity_column,
                time_col=time_column,
                target_col=target_column,
            )

            # Estimate both models
            fe_result = analyzer.fixed_effects(
                formula, entity_effects=True, time_effects=False
            )
            re_result = analyzer.random_effects(formula)

            # Run Hausman test
            test_result = analyzer.hausman_test(
                formula=formula, fe_result=fe_result, re_result=re_result
            )

            # Extract results
            statistic = test_result["h_statistic"]
            p_value = test_result["p_value"]
            reject_re = p_value < 0.05

            # Calculate coefficient differences
            common_vars = set(fe_result.coefficients.index) & set(
                re_result.coefficients.index
            )
            coef_diff = {
                var: float(fe_result.coefficients[var] - re_result.coefficients[var])
                for var in common_vars
            }

            # Generate interpretation and recommendation
            if reject_re:
                recommendation = "Use fixed effects model"
                interpretation = (
                    f"Hausman test rejects random effects (χ² = {statistic:.4f}, p = {p_value:.4f}). "
                    f"Entity-specific effects are correlated with regressors. "
                    f"Fixed effects is the appropriate specification."
                )
            else:
                recommendation = "Use random effects model"
                interpretation = (
                    f"Hausman test does not reject random effects (χ² = {statistic:.4f}, p = {p_value:.4f}). "
                    f"Entity-specific effects appear uncorrelated with regressors. "
                    f"Random effects is more efficient."
                )

            # Return results
            return {
                "success": True,
                "statistic": float(statistic),
                "p_value": float(p_value),
                "reject_re": reject_re,
                "fe_coefficients": fe_result.coefficients.to_dict(),
                "re_coefficients": re_result.coefficients.to_dict(),
                "coefficient_differences": coef_diff,
                "recommendation": recommendation,
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Hausman test failed: {str(e)}")
            return {"success": False, "error": f"Hausman test failed: {str(e)}"}

    # =========================================================================
    # Tool 6: First Difference Model
    # =========================================================================

    async def first_difference_model(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        entity_column: str = "entity_id",
        time_column: str = "time_period",
        target_column: str = "value",
    ) -> Dict[str, Any]:
        """
        Estimate first difference model for panel data.

        First differencing removes entity-specific fixed effects by taking
        differences between consecutive time periods. This is useful for
        dynamic models and when there are lagged dependent variables.

        Implements Phase 10A rec_0625_1b208ec4 (Priority: 9.0/10)

        Args:
            data: List of dictionaries containing panel data
            formula: Model formula (e.g., 'value ~ x1 + x2')
            entity_column: Column identifying entities
            time_column: Column identifying time periods
            target_column: Column containing dependent variable

        Returns:
            Dictionary containing:
            - coefficients: Dict of coefficient estimates
            - std_errors: Dict of standard errors
            - t_stats: Dict of t-statistics
            - p_values: Dict of p-values
            - r_squared: R-squared value
            - f_statistic: F-statistic
            - f_pvalue: P-value for F-statistic
            - n_obs: Number of observations (after differencing)
            - n_entities: Number of entities
            - n_timeperiods: Number of time periods (after differencing)
            - model_type: 'first_difference'
            - interpretation: Human-readable interpretation
            - recommendations: List of next steps
            - success: True if estimation succeeded
            - error: Error message if failed
        """
        try:
            from mcp_server.panel_data import PanelDataAnalyzer

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Validate required columns
            required_cols = [entity_column, time_column, target_column]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error": f"Missing required columns: {missing_cols}",
                }

            # Create analyzer
            analyzer = PanelDataAnalyzer(
                data=df,
                entity_col=entity_column,
                time_col=time_column,
                target_col=target_column,
            )

            # Estimate first difference model
            result = analyzer.first_difference(formula)

            # Generate interpretation
            r2 = result.r_squared
            interpretation = (
                f"First difference model estimated with R² = {r2:.4f}. "
                f"Model removes entity-specific fixed effects by differencing. "
                f"Coefficients represent impact of changes in X on changes in Y."
            )

            # Generate recommendations
            recommendations = []
            recommendations.append(
                "First differencing eliminates time-invariant entity effects"
            )
            recommendations.append(
                "Coefficients show impact of changes in X on changes in Y"
            )
            recommendations.append(
                "Consider clustering standard errors by entity for robust inference"
            )
            if r2 < 0.3:
                recommendations.append(
                    "Low R² suggests changes in Y are not well explained by changes in X"
                )

            # Return results
            return {
                "success": True,
                "coefficients": result.coefficients.to_dict(),
                "std_errors": result.std_errors.to_dict(),
                "t_stats": result.t_stats.to_dict(),
                "p_values": result.p_values.to_dict(),
                "r_squared": float(result.r_squared),
                "f_statistic": (
                    float(result.f_statistic)
                    if result.f_statistic is not None
                    else None
                ),
                "f_pvalue": (
                    float(result.f_pvalue) if result.f_pvalue is not None else None
                ),
                "n_obs": result.n_obs,
                "n_entities": result.n_entities,
                "n_timeperiods": result.n_timeperiods,
                "model_type": "first_difference",
                "interpretation": interpretation,
                "recommendations": recommendations,
            }

        except Exception as e:
            self.logger.error(f"First difference estimation failed: {str(e)}")
            return {
                "success": False,
                "error": f"First difference estimation failed: {str(e)}",
            }
