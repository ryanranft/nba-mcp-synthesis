"""
Survival Analysis MCP Tools - Phase 10A Agent 8 Module 4B

This module provides MCP tool wrappers for survival analysis and time-to-event
modeling, including Cox proportional hazards, Kaplan-Meier curves, and
parametric survival models.

Survival analysis models time until an event occurs (or doesn't occur due to
censoring). Essential for NBA analytics to study:
- Player career length and retirement timing
- Injury duration and recovery time
- Contract duration and re-signing probability
- Team dynasty duration and rebuild cycles

Tools:
1. cox_proportional_hazards - Cox PH regression for hazard ratios
2. kaplan_meier - Non-parametric survival curves
3. logrank_test - Compare survival curves between groups
4. parametric_survival - Weibull/exponential/lognormal models
5. competing_risks - Multiple event types (trade, retire, injury)
6. predict_survival - Survival probability predictions

Author: Phase 10A Agent 8 Module 4B
Date: October 2025
"""

import logging
from typing import Dict, Any, List, Union, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SurvivalTools:
    """
    MCP tool wrappers for survival analysis methods.

    Provides time-to-event modeling for NBA career, injury, and contract
    duration analysis with censoring handling.
    """

    def __init__(self):
        """Initialize SurvivalTools."""
        self.logger = logger

    # =========================================================================
    # Tool 1: Cox Proportional Hazards
    # =========================================================================

    async def cox_proportional_hazards(
        self,
        data: List[Dict[str, Any]],
        duration_column: str,
        event_column: str,
        covariates: List[str],
    ) -> Dict[str, Any]:
        """
        Fit Cox Proportional Hazards model for survival regression.

        Cox PH models hazard rate as function of covariates. Hazard ratio
        represents multiplicative effect on event risk. Handles right-censored
        data (observations without events).

        Args:
            data: List of survival observations
            duration_column: Time to event or censoring
            event_column: Binary indicator (1=event, 0=censored)
            covariates: Predictor variables

        Returns:
            Dictionary with:
            - success: True if model fit succeeded
            - hazard_ratios: Dict of HR for each covariate
            - coefficients: Log hazard ratios (regression coefficients)
            - standard_errors: Standard errors
            - confidence_intervals: 95% CI for each HR
            - concordance: C-index (discrimination)
            - interpretation: Summary
            - error: Error message if failed

        Example:
            >>> result = await cox_proportional_hazards(
            ...     data=player_data,
            ...     duration_column='years_in_league',
            ...     event_column='retired',
            ...     covariates=['draft_pick', 'ppg', 'all_star']
            ... )
            >>> result['hazard_ratios']['all_star']
            0.45  # All-stars have 55% lower retirement hazard

        NBA Use Cases:
            - Predict player career length from draft metrics
            - Model injury recovery time based on severity
            - Estimate contract extension probability
        """
        try:
            from mcp_server.survival_analysis import SurvivalAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [duration_column, event_column] + covariates
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Initialize analyzer
            analyzer = SurvivalAnalyzer(
                data=df, duration_col=duration_column, event_col=event_column
            )

            # Fit Cox model
            result = analyzer.cox_proportional_hazards(covariates=covariates)

            # Extract results
            hazard_ratios = {}
            coefficients = {}
            std_errors = {}
            ci_dict = {}

            for cov in covariates:
                hr = result.hazard_ratios[cov]
                coef = result.coefficients[cov]
                se = result.std_errors[cov]

                hazard_ratios[cov] = float(hr)
                coefficients[cov] = float(coef)
                std_errors[cov] = float(se)
                ci_dict[cov] = {
                    "lower": float(result.confidence_intervals[cov][0]),
                    "upper": float(result.confidence_intervals[cov][1]),
                }

            interpretation = (
                f"Cox PH model fit with {len(covariates)} predictors. "
                f"Concordance index: {result.concordance:.3f}. "
                f"{result.n_events} events out of {result.n_observations} observations."
            )

            return {
                "success": True,
                "hazard_ratios": hazard_ratios,
                "coefficients": coefficients,
                "standard_errors": std_errors,
                "confidence_intervals": ci_dict,
                "concordance": float(result.concordance),
                "n_observations": int(result.n_observations),
                "n_events": int(result.n_events),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Cox PH model failed: {str(e)}")
            return {"success": False, "error": f"Cox PH model failed: {str(e)}"}

    # =========================================================================
    # Tool 2: Kaplan-Meier
    # =========================================================================

    async def kaplan_meier(
        self,
        data: List[Dict[str, Any]],
        duration_column: str,
        event_column: str,
        group_column: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Estimate non-parametric survival curves using Kaplan-Meier method.

        KM estimates survival function without parametric assumptions.
        Handles censored data. Can stratify by groups (e.g., positions,
        draft rounds).

        Args:
            data: List of survival observations
            duration_column: Time variable
            event_column: Event indicator (1=event, 0=censored)
            group_column: Optional grouping variable for stratification

        Returns:
            Dictionary with:
            - success: True if estimation succeeded
            - survival_function: Time points and survival probabilities
            - median_survival: Median time to event
            - groups: Dict of survival curves per group (if grouped)
            - interpretation: Summary
            - error: Error message if failed

        Example:
            >>> result = await kaplan_meier(
            ...     data=career_data,
            ...     duration_column='seasons',
            ...     event_column='retired',
            ...     group_column='draft_round'
            ... )
            >>> result['median_survival']
            {'round_1': 8.5, 'round_2': 5.2}  # Years

        NBA Use Cases:
            - Compare career length by draft position
            - Visualize injury recovery curves by severity
            - Estimate contract duration by team
        """
        try:
            from mcp_server.survival_analysis import SurvivalAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [duration_column, event_column]
            if group_column:
                required.append(group_column)
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Initialize analyzer
            analyzer = SurvivalAnalyzer(
                data=df, duration_col=duration_column, event_col=event_column
            )

            # Estimate KM
            result = analyzer.kaplan_meier(group_col=group_column)

            # Build response
            if group_column:
                # Multiple survival curves
                groups = {}
                median_survival = {}

                for group_name, km_result in result.items():
                    groups[group_name] = {
                        "timeline": km_result.timeline.tolist(),
                        "survival_prob": km_result.survival_prob.tolist(),
                    }
                    median_survival[group_name] = float(km_result.median_survival)

                interpretation = (
                    f"Kaplan-Meier curves estimated for {len(groups)} groups. "
                    f"Median survival ranges from {min(median_survival.values()):.1f} "
                    f"to {max(median_survival.values()):.1f}."
                )

                return {
                    "success": True,
                    "groups": groups,
                    "median_survival": median_survival,
                    "n_groups": len(groups),
                    "interpretation": interpretation,
                }
            else:
                # Single survival curve
                interpretation = (
                    f"Kaplan-Meier survival curve estimated. "
                    f"Median survival: {result.median_survival:.2f}."
                )

                return {
                    "success": True,
                    "timeline": result.timeline.tolist(),
                    "survival_prob": result.survival_prob.tolist(),
                    "median_survival": float(result.median_survival),
                    "interpretation": interpretation,
                }

        except Exception as e:
            self.logger.error(f"Kaplan-Meier failed: {str(e)}")
            return {"success": False, "error": f"Kaplan-Meier failed: {str(e)}"}

    # =========================================================================
    # Tool 3: Logrank Test
    # =========================================================================

    async def logrank_test(
        self,
        data: List[Dict[str, Any]],
        duration_column: str,
        event_column: str,
        group_column: str,
    ) -> Dict[str, Any]:
        """
        Compare survival curves between groups using logrank test.

        Tests null hypothesis that survival curves are identical across groups.
        Non-parametric test for comparing two or more survival distributions.

        Args:
            data: List of survival observations
            duration_column: Time variable
            event_column: Event indicator
            group_column: Grouping variable (2+ groups)

        Returns:
            Dictionary with:
            - success: True if test completed
            - test_statistic: Chi-square statistic
            - p_value: P-value for test
            - significant: Boolean (p < 0.05)
            - groups: List of group names
            - interpretation: Summary
            - error: Error message if failed

        Example:
            >>> result = await logrank_test(
            ...     data=career_data,
            ...     duration_column='years',
            ...     event_column='retired',
            ...     group_column='position'
            ... )
            >>> result['p_value']
            0.003  # Positions have significantly different career lengths

        NBA Use Cases:
            - Compare career lengths across positions
            - Test if injury recovery differs by treatment
            - Compare team rebuild durations
        """
        try:
            from mcp_server.survival_analysis import SurvivalAnalyzer

            df = pd.DataFrame(data)

            # Validate columns
            required = [duration_column, event_column, group_column]
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Initialize analyzer
            analyzer = SurvivalAnalyzer(
                data=df, duration_col=duration_column, event_col=event_column
            )

            # Run logrank test
            result = analyzer.logrank_test(group_col=group_column)

            groups = df[group_column].unique().tolist()
            significant = result.p_value < 0.05

            interpretation = (
                f"Logrank test comparing {len(groups)} groups. "
                f"χ²({result.df}) = {result.test_statistic:.2f}, p = {result.p_value:.4f}. "
                f"{'Significant' if significant else 'No significant'} difference in survival."
            )

            return {
                "success": True,
                "test_statistic": float(result.test_statistic),
                "degrees_of_freedom": int(result.df),
                "p_value": float(result.p_value),
                "significant": significant,
                "groups": groups,
                "n_groups": len(groups),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Logrank test failed: {str(e)}")
            return {"success": False, "error": f"Logrank test failed: {str(e)}"}

    # =========================================================================
    # Tool 4: Parametric Survival
    # =========================================================================

    async def parametric_survival(
        self,
        data: List[Dict[str, Any]],
        duration_column: str,
        event_column: str,
        distribution: str = "weibull",
        covariates: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Fit parametric survival model (Weibull, Exponential, Lognormal).

        Parametric models assume specific distribution for survival times.
        More efficient than Cox if assumptions hold. Allows extrapolation
        and direct survival probability estimates.

        Args:
            data: List of survival observations
            duration_column: Time variable
            event_column: Event indicator
            distribution: 'weibull', 'exponential', or 'lognormal'
            covariates: Optional predictor variables

        Returns:
            Dictionary with:
            - success: True if model fit succeeded
            - parameters: Distribution parameters
            - coefficients: Covariate effects (if provided)
            - median_survival: Median time to event
            - aic: Model AIC
            - interpretation: Summary
            - error: Error message if failed

        Example:
            >>> result = await parametric_survival(
            ...     data=injury_data,
            ...     duration_column='days_to_recovery',
            ...     event_column='recovered',
            ...     distribution='weibull',
            ...     covariates=['severity', 'age']
            ... )
            >>> result['median_survival']
            28.5  # Median recovery time: 28.5 days

        NBA Use Cases:
            - Model injury recovery time distributions
            - Predict career length with parametric curves
            - Extrapolate beyond observed data
        """
        try:
            from mcp_server.survival_analysis import SurvivalAnalyzer

            df = pd.DataFrame(data)

            # Validate
            required = [duration_column, event_column]
            if covariates:
                required.extend(covariates)
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Initialize analyzer
            analyzer = SurvivalAnalyzer(
                data=df, duration_col=duration_column, event_col=event_column
            )

            # Fit parametric model
            result = analyzer.parametric_survival(
                distribution=distribution, covariates=covariates or []
            )

            interpretation = (
                f"{distribution.capitalize()} survival model fit. "
                f"Median survival: {result.median_survival:.2f}. "
                f"AIC: {result.aic:.1f}."
            )

            return {
                "success": True,
                "distribution": distribution,
                "parameters": result.parameters,
                "median_survival": float(result.median_survival),
                "aic": float(result.aic),
                "coefficients": result.coefficients if covariates else {},
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Parametric survival failed: {str(e)}")
            return {"success": False, "error": f"Parametric survival failed: {str(e)}"}

    # =========================================================================
    # Tool 5: Competing Risks
    # =========================================================================

    async def competing_risks(
        self,
        data: List[Dict[str, Any]],
        duration_column: str,
        event_type_column: str,
    ) -> Dict[str, Any]:
        """
        Model competing risks (multiple mutually exclusive event types).

        Standard survival analysis assumes single event type. Competing risks
        handles multiple outcomes (e.g., retire vs trade vs injury). Estimates
        cumulative incidence for each event type.

        Args:
            data: List of observations with multiple event types
            duration_column: Time to event
            event_type_column: Event type (0=censored, 1=event1, 2=event2, ...)

        Returns:
            Dictionary with:
            - success: True if analysis succeeded
            - cumulative_incidence: Dict of CIF curves per event type
            - event_probabilities: Probability of each event type
            - interpretation: Summary
            - error: Error message if failed

        Example:
            >>> result = await competing_risks(
            ...     data=career_data,
            ...     duration_column='years',
            ...     event_type_column='exit_type'  # 0=active, 1=retire, 2=trade, 3=injury
            ... )
            >>> result['event_probabilities']
            {'retire': 0.65, 'trade': 0.25, 'injury': 0.10}

        NBA Use Cases:
            - Model career endings (retire, trade, injury)
            - Competing risks in contract scenarios
            - Multiple injury types
        """
        try:
            from mcp_server.survival_analysis import SurvivalAnalyzer

            df = pd.DataFrame(data)

            # Validate
            required = [duration_column, event_type_column]
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            # Initialize analyzer
            analyzer = SurvivalAnalyzer(
                data=df,
                duration_col=duration_column,
                event_col=event_type_column,  # Now multi-valued
            )

            # Fit competing risks model
            result = analyzer.competing_risks()

            # Extract results
            cumulative_incidence = {}
            event_probs = {}

            for event_type, cif in result.cif.items():
                cumulative_incidence[event_type] = {
                    "timeline": cif.timeline.tolist(),
                    "cif": cif.values.tolist(),
                }
                event_probs[event_type] = float(cif.values[-1])  # Final CIF

            interpretation = (
                f"Competing risks analysis with {len(event_probs)} event types. "
                f"Event probabilities: {', '.join([f'{k}={v:.2%}' for k, v in event_probs.items()])}."
            )

            return {
                "success": True,
                "cumulative_incidence": cumulative_incidence,
                "event_probabilities": event_probs,
                "n_event_types": len(event_probs),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Competing risks failed: {str(e)}")
            return {"success": False, "error": f"Competing risks failed: {str(e)}"}

    # =========================================================================
    # Tool 6: Predict Survival
    # =========================================================================

    async def predict_survival(
        self,
        model_data: List[Dict[str, Any]],
        new_data: List[Dict[str, Any]],
        duration_column: str,
        event_column: str,
        covariates: List[str],
        times: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Predict survival probabilities for new observations.

        Uses fitted Cox model to predict survival curves for new individuals.
        Useful for player career projections, injury risk assessment, etc.

        Args:
            model_data: Training data for model fitting
            new_data: New observations to predict
            duration_column: Time variable (in training data)
            event_column: Event indicator (in training data)
            covariates: Predictor variables
            times: Time points for predictions (default: observed event times)

        Returns:
            Dictionary with:
            - success: True if prediction succeeded
            - predictions: List of survival curves for each new observation
            - median_survival: Predicted median time for each observation
            - interpretation: Summary
            - error: Error message if failed

        Example:
            >>> result = await predict_survival(
            ...     model_data=historical_careers,
            ...     new_data=[{"draft_pick": 3, "ppg": 20, "all_star": 1}],
            ...     duration_column='years',
            ...     event_column='retired',
            ...     covariates=['draft_pick', 'ppg', 'all_star']
            ... )
            >>> result['median_survival'][0]
            12.5  # Predicted 12.5 year career

        NBA Use Cases:
            - Project rookie career length from draft metrics
            - Estimate injury recovery time for current injuries
            - Predict contract duration for free agents
        """
        try:
            from mcp_server.survival_analysis import SurvivalAnalyzer

            df_train = pd.DataFrame(model_data)
            df_new = pd.DataFrame(new_data)

            # Validate
            required = [duration_column, event_column] + covariates
            missing_train = [c for c in required if c not in df_train.columns]
            if missing_train:
                return {
                    "success": False,
                    "error": f"Missing training columns: {missing_train}",
                }

            missing_new = [c for c in covariates if c not in df_new.columns]
            if missing_new:
                return {
                    "success": False,
                    "error": f"Missing new data columns: {missing_new}",
                }

            # Fit model on training data
            analyzer = SurvivalAnalyzer(
                data=df_train, duration_col=duration_column, event_col=event_column
            )

            # Fit Cox model
            model = analyzer.cox_proportional_hazards(covariates=covariates)

            # Predict for new data
            predictions = analyzer.predict_survival(
                model_result=model, new_data=df_new, times=times
            )

            # Extract predictions
            pred_list = []
            median_survival = []

            for i, pred in enumerate(predictions):
                pred_list.append(
                    {
                        "timeline": pred.timeline.tolist(),
                        "survival_prob": pred.survival_prob.tolist(),
                    }
                )
                median_survival.append(float(pred.median_survival))

            interpretation = (
                f"Survival predictions for {len(df_new)} new observations. "
                f"Median predicted survival: {np.mean(median_survival):.2f}."
            )

            return {
                "success": True,
                "predictions": pred_list,
                "median_survival": median_survival,
                "n_predictions": len(df_new),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Survival prediction failed: {str(e)}")
            return {"success": False, "error": f"Survival prediction failed: {str(e)}"}


def create_survival_tools() -> SurvivalTools:
    """Factory function to create survival analysis tools instance."""
    return SurvivalTools()
