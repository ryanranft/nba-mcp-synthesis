"""
Causal Inference MCP Tools - Phase 10A Agent 8 Module 4A

This module provides MCP tool wrappers for causal inference and treatment effect
estimation, exposing methods like instrumental variables, regression discontinuity,
propensity score matching, and synthetic control as FastMCP tools.

Causal methods answer "what-if" questions by estimating treatment effects from
observational data. Essential for NBA analytics to evaluate:
- Impact of coaching changes on team performance
- Effect of player trades on win probability
- Causal impact of rest days on injury risk
- Treatment effects of training programs

Tools:
1. instrumental_variables - IV/2SLS for endogeneity
2. regression_discontinuity - RDD for threshold-based treatments
3. propensity_score_matching - PSM for treatment effect estimation
4. synthetic_control - Synthetic control method for case studies
5. doubly_robust_estimation - DR estimation combining propensity and outcome models
6. sensitivity_analysis - Assess robustness to unobserved confounding

Author: Phase 10A Agent 8 Module 4A
Date: October 2025
"""

import logging
from typing import Dict, Any, List, Union, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class CausalTools:
    """
    MCP tool wrappers for causal inference methods.

    Provides treatment effect estimation from observational data using
    various identification strategies: IV, RDD, PSM, synthetic control.
    """

    def __init__(self):
        """Initialize CausalTools."""
        self.logger = logger

    # =========================================================================
    # Tool 1: Instrumental Variables
    # =========================================================================

    async def instrumental_variables(
        self,
        data: List[Dict[str, Any]],
        outcome: str,
        treatment: str,
        instruments: List[str],
        controls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Estimate treatment effects using Instrumental Variables (IV/2SLS).

        IV methods address endogeneity when treatment is correlated with
        unobserved confounders. Instruments must be:
        1. Relevant: Correlated with treatment
        2. Exogenous: Uncorrelated with outcome error term

        Args:
            data: List of observations
            outcome: Outcome variable (e.g., 'wins')
            treatment: Endogenous treatment variable (e.g., 'new_coach')
            instruments: List of instrument variables
            controls: Optional control variables

        Returns:
            Dictionary with:
            - success: True if estimation succeeded
            - treatment_effect: Estimated causal effect
            - standard_error: Standard error of estimate
            - confidence_interval: 95% CI for treatment effect
            - first_stage_f_stat: F-statistic from first stage
            - weak_instrument_test: Dict with test results
            - interpretation: Summary of results
            - error: Error message if failed

        Example:
            >>> result = await instrumental_variables(
            ...     data=team_data,
            ...     outcome='wins',
            ...     treatment='coaching_change',
            ...     instruments=['draft_pick_strength'],
            ...     controls=['team_salary', 'prior_wins']
            ... )
            >>> result['treatment_effect']
            5.2  # Coaching change causes +5.2 wins

        NBA Use Cases:
            - Effect of coaching changes (instrument: draft pick)
            - Impact of player trades (instrument: injury status)
            - Salary cap effects (instrument: market size)
        """
        try:
            from mcp_server.causal_inference import CausalInferenceAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [outcome, treatment] + instruments
            if controls:
                required.extend(controls)
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Initialize analyzer
            analyzer = CausalInferenceAnalyzer(
                data=df,
                treatment_col=treatment,
                outcome_col=outcome,
                covariates=controls or [],
            )

            # Estimate IV model
            result = analyzer.instrumental_variables(
                outcome=outcome,
                treatment=treatment,
                instruments=instruments,
                controls=controls or [],
            )

            # Extract key results
            treatment_effect = result.treatment_effect
            std_error = result.std_error
            ci_lower = treatment_effect - 1.96 * std_error
            ci_upper = treatment_effect + 1.96 * std_error

            # Weak instrument test
            weak_test = {
                "f_statistic": float(result.first_stage_f),
                "passes": result.first_stage_f > 10,  # Rule of thumb
                "interpretation": "Strong" if result.first_stage_f > 10 else "Weak",
            }

            interpretation = (
                f"IV estimate: {treatment_effect:.3f} ± {std_error:.3f}. "
                f"First-stage F-stat: {result.first_stage_f:.2f}. "
                f"Instruments: {'Strong' if weak_test['passes'] else 'Weak'}."
            )

            return {
                "success": True,
                "treatment_effect": float(treatment_effect),
                "standard_error": float(std_error),
                "confidence_interval": {
                    "lower": float(ci_lower),
                    "upper": float(ci_upper),
                },
                "first_stage_f_stat": float(result.first_stage_f),
                "weak_instrument_test": weak_test,
                "n_observations": len(df),
                "n_instruments": len(instruments),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"IV estimation failed: {str(e)}")
            return {"success": False, "error": f"IV estimation failed: {str(e)}"}

    # =========================================================================
    # Tool 2: Regression Discontinuity
    # =========================================================================

    async def regression_discontinuity(
        self,
        data: List[Dict[str, Any]],
        outcome: str,
        running_variable: str,
        cutoff: float,
        bandwidth: Optional[float] = None,
        kernel: str = "triangular",
    ) -> Dict[str, Any]:
        """
        Estimate treatment effects using Regression Discontinuity Design (RDD).

        RDD exploits discontinuous assignment of treatment at a threshold.
        Compares observations just above vs just below the cutoff to estimate
        causal effects. Valid when treatment assignment is deterministic at cutoff.

        Args:
            data: List of observations
            outcome: Outcome variable
            running_variable: Assignment variable (e.g., 'draft_position')
            cutoff: Treatment threshold (e.g., lottery cutoff = 14)
            bandwidth: Window around cutoff (default: auto-select)
            kernel: Kernel for local regression ('triangular', 'uniform')

        Returns:
            Dictionary with:
            - success: True if estimation succeeded
            - treatment_effect: RDD estimate at cutoff
            - standard_error: Standard error
            - confidence_interval: 95% CI
            - bandwidth: Bandwidth used
            - n_treated: Observations above cutoff
            - n_control: Observations below cutoff
            - interpretation: Results summary
            - error: Error message if failed

        Example:
            >>> result = await regression_discontinuity(
            ...     data=draft_data,
            ...     outcome='future_all_star',
            ...     running_variable='draft_position',
            ...     cutoff=14  # Lottery cutoff
            ... )
            >>> result['treatment_effect']
            0.15  # Top-14 pick increases all-star prob by 15%

        NBA Use Cases:
            - Effect of draft lottery on team success
            - Impact of playoff qualification threshold
            - Effect of salary cap on roster decisions
        """
        try:
            from mcp_server.causal_inference import CausalInferenceAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [outcome, running_variable]
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Create treatment indicator for RDD
            df["_rdd_treatment"] = (df[running_variable] >= cutoff).astype(int)

            # Initialize analyzer
            analyzer = CausalInferenceAnalyzer(
                data=df, treatment_col="_rdd_treatment", outcome_col=outcome
            )

            # Estimate RDD
            result = analyzer.regression_discontinuity(
                outcome=outcome,
                running_var=running_variable,
                cutoff=cutoff,
                bandwidth=bandwidth,
                kernel=kernel,
            )

            # Count treated and control
            df_rdd = df.copy()
            df_rdd["treated"] = df_rdd[running_variable] >= cutoff
            n_treated = df_rdd["treated"].sum()
            n_control = (~df_rdd["treated"]).sum()

            interpretation = (
                f"RDD estimate: {result.treatment_effect:.3f} at cutoff={cutoff}. "
                f"Bandwidth: {result.bandwidth:.2f}. "
                f"N (treated/control): {n_treated}/{n_control}."
            )

            return {
                "success": True,
                "treatment_effect": float(result.treatment_effect),
                "standard_error": float(result.std_error),
                "confidence_interval": {
                    "lower": float(result.ci_lower),
                    "upper": float(result.ci_upper),
                },
                "bandwidth": float(result.bandwidth),
                "cutoff": float(cutoff),
                "kernel": kernel,
                "n_treated": int(n_treated),
                "n_control": int(n_control),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"RDD estimation failed: {str(e)}")
            return {"success": False, "error": f"RDD estimation failed: {str(e)}"}

    # =========================================================================
    # Tool 3: Propensity Score Matching
    # =========================================================================

    async def propensity_score_matching(
        self,
        data: List[Dict[str, Any]],
        outcome: str,
        treatment: str,
        covariates: List[str],
        method: str = "nearest",
        caliper: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Estimate Average Treatment Effect using Propensity Score Matching.

        PSM matches treated and control units with similar propensity scores
        (probability of treatment given covariates). Reduces bias from
        observed confounders.

        Args:
            data: List of observations
            outcome: Outcome variable
            treatment: Binary treatment indicator (0/1)
            covariates: Variables to match on
            method: Matching method ('nearest', 'radius', 'kernel')
            caliper: Maximum propensity score distance (for nearest/radius)

        Returns:
            Dictionary with:
            - success: True if estimation succeeded
            - ate: Average Treatment Effect
            - att: Average Treatment Effect on Treated
            - standard_error: Standard error of ATE
            - confidence_interval: 95% CI
            - n_matched: Number of matched pairs
            - balance_statistics: Covariate balance before/after matching
            - interpretation: Results summary
            - error: Error message if failed

        Example:
            >>> result = await propensity_score_matching(
            ...     data=player_data,
            ...     outcome='career_length',
            ...     treatment='drafted_by_good_org',
            ...     covariates=['college_stats', 'draft_position', 'position']
            ... )
            >>> result['ate']
            2.3  # Good org extends career by 2.3 years

        NBA Use Cases:
            - Effect of coaching quality on player development
            - Impact of team facilities on injury rates
            - Effect of market size on player performance
        """
        try:
            from mcp_server.causal_inference import CausalInferenceAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [outcome, treatment] + covariates
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Validate treatment is binary
            unique_vals = df[treatment].unique()
            if not set(unique_vals).issubset({0, 1}):
                return {
                    "success": False,
                    "error": f"Treatment must be binary (0/1), got {unique_vals}",
                }

            # Initialize analyzer
            analyzer = CausalInferenceAnalyzer(
                data=df,
                treatment_col=treatment,
                outcome_col=outcome,
                covariates=covariates,
            )

            # Estimate PSM
            result = analyzer.propensity_score_matching(
                method=method,
                caliper=caliper,
            )

            # Balance statistics are already in the result
            # Calculate balance improvement from the balance_statistics DataFrame
            balance_df = result.balance_statistics
            if not balance_df.empty and 'std_diff_before' in balance_df.columns and 'std_diff_after' in balance_df.columns:
                avg_before = balance_df['std_diff_before'].abs().mean()
                avg_after = balance_df['std_diff_after'].abs().mean()
                balance_improvement = (avg_before - avg_after) / avg_before if avg_before > 0 else 0
            else:
                balance_improvement = 0.0

            interpretation = (
                f"PSM {method} matching: ATE = {result.ate:.3f}, ATT = {result.att:.3f}. "
                f"Matched {result.n_matched} pairs. "
                f"Average covariate balance improved by {balance_improvement:.1%}."
            )

            # Calculate t-stat and p-value
            t_stat = result.att / result.std_error if result.std_error > 0 else 0
            from scipy import stats
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=result.n_matched - 1))

            # Convert balance statistics DataFrame to dict format
            balance_stats_dict = {}
            if not balance_df.empty:
                for idx, row in balance_df.iterrows():
                    balance_stats_dict[str(idx)] = {
                        "before": float(row.get('std_diff_before', 0)),
                        "after": float(row.get('std_diff_after', 0))
                    }

            # Check if common support is violated
            common_support_violated = bool((result.common_support == 0).any())

            return {
                "success": True,
                "treatment_effect": float(result.att),  # Use ATT as treatment effect
                "std_error": float(result.std_error),
                "t_stat": float(t_stat),
                "p_value": float(p_value),
                "confidence_interval": result.confidence_interval,
                "n_matched": int(result.n_matched),
                "n_unmatched": int(result.n_unmatched),
                "balance_statistics": balance_stats_dict,
                "common_support_violated": common_support_violated,
                "matching_method": method,
                "interpretation": interpretation,
                "recommendations": [
                    "Check balance statistics to ensure adequate covariate balance",
                    "Inspect common support to verify sufficient overlap",
                    "Consider sensitivity analysis for unobserved confounding",
                ],
            }

        except Exception as e:
            self.logger.error(f"PSM estimation failed: {str(e)}")
            return {"success": False, "error": f"PSM estimation failed: {str(e)}"}

    # =========================================================================
    # Tool 4: Synthetic Control
    # =========================================================================

    async def synthetic_control(
        self,
        data: List[Dict[str, Any]],
        treated_unit: str,
        treatment_time: int,
        outcome: str,
        time_column: str = "time",
        unit_column: str = "unit",
    ) -> Dict[str, Any]:
        """
        Estimate treatment effect using Synthetic Control Method.

        Creates synthetic version of treated unit from weighted combination
        of control units. Compares treated unit to its synthetic counterfactual
        post-treatment. Ideal for case studies with single treated unit.

        Args:
            data: Panel data with units and time periods
            treated_unit: ID of treated unit
            treatment_time: Time period when treatment begins
            outcome: Outcome variable
            time_column: Time period column
            unit_column: Unit identifier column

        Returns:
            Dictionary with:
            - success: True if estimation succeeded
            - treatment_effect: Average effect post-treatment
            - synthetic_weights: Weights for each control unit
            - pre_treatment_fit: RMSE in pre-period
            - post_treatment_gap: Period-by-period gaps
            - interpretation: Results summary
            - error: Error message if failed

        Example:
            >>> result = await synthetic_control(
            ...     data=team_seasons,
            ...     treated_unit='Lakers',
            ...     treatment_time=2020,  # LeBron signing
            ...     outcome='wins',
            ...     unit_column='team',
            ...     time_column='season'
            ... )
            >>> result['treatment_effect']
            12.5  # LeBron caused +12.5 wins vs synthetic Lakers

        NBA Use Cases:
            - Effect of superstar acquisition on team success
            - Impact of new arena on attendance
            - Effect of coaching change on team performance
        """
        try:
            from mcp_server.causal_inference import CausalInferenceAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [unit_column, time_column, outcome]
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Validate treated unit exists
            if treated_unit not in df[unit_column].values:
                return {
                    "success": False,
                    "error": f"Treated unit '{treated_unit}' not found",
                }

            # Create treatment indicator for synthetic control
            df["_synth_treatment"] = (
                (df[unit_column] == treated_unit) & (df[time_column] >= treatment_time)
            ).astype(int)

            # Initialize analyzer
            analyzer = CausalInferenceAnalyzer(
                data=df,
                treatment_col="_synth_treatment",
                outcome_col=outcome,
                entity_col=unit_column,
                time_col=time_column,
            )

            # Estimate synthetic control
            result = analyzer.synthetic_control(
                treated_unit=treated_unit,
                treatment_time=treatment_time,
                outcome=outcome,
                time_col=time_column,
                unit_col=unit_column,
            )

            # Get synthetic weights
            weights = {
                unit: float(weight)
                for unit, weight in result.weights.items()
                if weight > 0.01  # Only show non-trivial weights
            }

            interpretation = (
                f"Synthetic control for {treated_unit} from {len(weights)} donor units. "
                f"Treatment effect: {result.treatment_effect:.2f}. "
                f"Pre-treatment RMSE: {result.pre_rmse:.2f}."
            )

            return {
                "success": True,
                "treatment_effect": float(result.treatment_effect),
                "synthetic_weights": weights,
                "pre_treatment_rmse": float(result.pre_rmse),
                "post_treatment_gaps": [float(g) for g in result.post_gaps],
                "treated_unit": treated_unit,
                "treatment_time": treatment_time,
                "n_pre_periods": int(result.n_pre_periods),
                "n_post_periods": int(result.n_post_periods),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Synthetic control failed: {str(e)}")
            return {"success": False, "error": f"Synthetic control failed: {str(e)}"}

    # =========================================================================
    # Tool 5: Doubly Robust Estimation
    # =========================================================================

    async def doubly_robust_estimation(
        self,
        data: List[Dict[str, Any]],
        outcome: str,
        treatment: str,
        covariates: List[str],
    ) -> Dict[str, Any]:
        """
        Estimate treatment effects using Doubly Robust method.

        DR combines propensity score and outcome regression models. Provides
        consistent estimates if either model is correctly specified, making
        it more robust than PSM or regression alone.

        Args:
            data: List of observations
            outcome: Outcome variable
            treatment: Binary treatment (0/1)
            covariates: Confounding variables

        Returns:
            Dictionary with:
            - success: True if estimation succeeded
            - ate: Average Treatment Effect
            - standard_error: Standard error
            - confidence_interval: 95% CI
            - interpretation: Results summary
            - error: Error message if failed

        Example:
            >>> result = await doubly_robust_estimation(
            ...     data=data,
            ...     outcome='championship_prob',
            ...     treatment='hired_elite_coach',
            ...     covariates=['roster_talent', 'salary', 'market_size']
            ... )
            >>> result['ate']
            0.08  # Elite coach adds 8% championship probability

        NBA Use Cases:
            - Robust estimates of coaching effects
            - Treatment effects with model uncertainty
            - Combine multiple identification strategies
        """
        try:
            from mcp_server.causal_inference import CausalInferenceAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [outcome, treatment] + covariates
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Initialize analyzer
            analyzer = CausalInferenceAnalyzer(
                data=df,
                treatment_col=treatment,
                outcome_col=outcome,
                covariates=covariates,
            )

            # Estimate DR
            result = analyzer.doubly_robust_estimation(
                outcome=outcome, treatment=treatment, covariates=covariates
            )

            interpretation = (
                f"Doubly robust ATE: {result.ate:.3f} ± {result.std_error:.3f}. "
                f"Consistent if either propensity or outcome model is correct."
            )

            return {
                "success": True,
                "ate": float(result.ate),
                "standard_error": float(result.std_error),
                "confidence_interval": {
                    "lower": float(result.ci_lower),
                    "upper": float(result.ci_upper),
                },
                "n_observations": len(df),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"DR estimation failed: {str(e)}")
            return {"success": False, "error": f"DR estimation failed: {str(e)}"}

    # =========================================================================
    # Tool 6: Sensitivity Analysis
    # =========================================================================

    async def sensitivity_analysis(
        self,
        data: List[Dict[str, Any]],
        outcome: str,
        treatment: str,
        covariates: List[str],
        method: str = "psm",
    ) -> Dict[str, Any]:
        """
        Assess sensitivity of treatment effect to unobserved confounding.

        Tests how strong unobserved confounders would need to be to overturn
        the estimated treatment effect. Provides bounds on causal estimates
        under different confounding assumptions.

        Args:
            data: List of observations
            outcome: Outcome variable
            treatment: Treatment variable
            covariates: Observed covariates
            method: Base method for analysis ('psm', 'iv', 'regression')

        Returns:
            Dictionary with:
            - success: True if analysis succeeded
            - base_estimate: Treatment effect from base method
            - bounds: Dict of effect bounds under different scenarios
            - robustness: Assessment of estimate robustness
            - interpretation: Summary
            - error: Error message if failed

        Example:
            >>> result = await sensitivity_analysis(
            ...     data=data,
            ...     outcome='wins',
            ...     treatment='coaching_change',
            ...     covariates=['salary', 'prior_wins'],
            ...     method='psm'
            ... )
            >>> result['robustness']
            'High'  # Effect remains significant even with strong confounding

        NBA Use Cases:
            - Validate causal claims about coaching
            - Test robustness of trade effect estimates
            - Assess confidence in policy recommendations
        """
        try:
            from mcp_server.causal_inference import CausalInferenceAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [outcome, treatment] + covariates
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Initialize analyzer
            analyzer = CausalInferenceAnalyzer(
                data=df,
                treatment_col=treatment,
                outcome_col=outcome,
                covariates=covariates,
            )

            # Run sensitivity analysis
            result = analyzer.sensitivity_analysis(
                outcome=outcome,
                treatment=treatment,
                covariates=covariates,
                method=method,
            )

            # Assess robustness
            base_significant = abs(result.base_estimate / result.base_se) > 1.96

            if result.critical_value > 2.0:
                robustness = "High"
            elif result.critical_value > 1.5:
                robustness = "Moderate"
            else:
                robustness = "Low"

            interpretation = (
                f"Base {method.upper()} estimate: {result.base_estimate:.3f}. "
                f"Robustness: {robustness}. "
                f"Unobserved confounder would need correlation ρ > {result.critical_value:.2f} to overturn."
            )

            return {
                "success": True,
                "base_estimate": float(result.base_estimate),
                "base_standard_error": float(result.base_se),
                "critical_correlation": float(result.critical_value),
                "robustness": robustness,
                "bounds": {
                    "lower": float(result.bound_lower),
                    "upper": float(result.bound_upper),
                },
                "method": method,
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Sensitivity analysis failed: {str(e)}")
            return {"success": False, "error": f"Sensitivity analysis failed: {str(e)}"}


def create_causal_tools() -> CausalTools:
    """Factory function to create causal inference tools instance."""
    return CausalTools()
