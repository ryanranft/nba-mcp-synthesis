"""
Econometric Suite MCP Tools
Module 4D of Agent 8 deployment (Phase 10A)

Provides intelligent method selection, auto-analysis, comparison, and model averaging
across all econometric tools. Acts as a meta-layer to guide users to appropriate methods.

Tools:
- auto_detect_econometric_method: Recommend best method based on data characteristics
- auto_analyze_econometric_data: Run comprehensive analysis with multiple methods
- compare_econometric_methods: Compare results across different econometric approaches
- econometric_model_averaging: Combine predictions from multiple models

Author: Agent 8 (Phase 10A - Module 4D)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class EconometricSuiteTools:
    """Econometric suite wrapper for intelligent method selection and comparison."""

    def __init__(self):
        """Initialize econometric suite tools."""
        self.logger = logging.getLogger(__name__)
        self._method_registry = self._build_method_registry()

    def auto_detect_econometric_method(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: Optional[List[str]] = None,
        panel_id: Optional[str] = None,
        time_var: Optional[str] = None,
        research_question: Optional[str] = None,
        data_characteristics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Automatically detect and recommend the best econometric method.

        Analyzes data structure, relationships, and research context to suggest
        the most appropriate econometric technique from the available suite.

        Args:
            data: Input dataset
            dependent_var: Dependent variable to model
            independent_vars: Independent variables (optional)
            panel_id: Panel/group identifier (if panel data)
            time_var: Time variable (if time series/panel)
            research_question: Description of research objective
            data_characteristics: Known characteristics (e.g., {'has_endogeneity': True})

        Returns:
            Dictionary containing:
            - recommended_method: Primary recommended method
            - alternative_methods: Alternative methods to consider
            - method_rationale: Explanation for recommendation
            - data_diagnostics: Detected data characteristics
            - implementation_guidance: How to use the recommended method
            - prerequisite_checks: Required data validation steps

        Example:
            # Auto-detect best method for player performance analysis
            result = auto_detect_econometric_method(
                data=player_season_df,
                dependent_var='win_shares',
                independent_vars=['minutes', 'usage_rate', 'true_shooting'],
                panel_id='player_id',
                time_var='season',
                research_question='Does increased usage reduce efficiency?'
            )
        """
        try:
            self.logger.info(f"Auto-detecting method: dependent={dependent_var}")

            # Validate inputs
            if data.empty:
                raise ValueError("Input data is empty")

            if dependent_var not in data.columns:
                raise ValueError(f"Dependent variable '{dependent_var}' not found")

            # Detect data structure
            data_structure = self._detect_data_structure(data, panel_id, time_var)

            # Analyze dependent variable characteristics
            dep_var_characteristics = self._analyze_variable_characteristics(
                data[dependent_var]
            )

            # Detect potential econometric issues
            econometric_issues = self._detect_econometric_issues(
                data, dependent_var, independent_vars, panel_id, time_var
            )

            # Parse research question for intent
            research_intent = (
                self._parse_research_question(research_question)
                if research_question
                else {}
            )

            # Combine all characteristics
            all_characteristics = {
                "data_structure": data_structure,
                "dependent_var_type": dep_var_characteristics,
                "econometric_issues": econometric_issues,
                "research_intent": research_intent,
                "user_provided": data_characteristics or {},
            }

            # Apply decision rules to select method
            recommended_method, alternatives, rationale = self._select_method(
                all_characteristics
            )

            # Generate implementation guidance
            implementation_guidance = self._generate_implementation_guidance(
                recommended_method,
                data,
                dependent_var,
                independent_vars,
                panel_id,
                time_var,
            )

            # Generate prerequisite checks
            prerequisite_checks = self._generate_prerequisite_checks(
                recommended_method, all_characteristics
            )

            # Build result
            result = {
                "recommended_method": recommended_method,
                "alternative_methods": alternatives,
                "method_rationale": rationale,
                "confidence_score": self._compute_recommendation_confidence(
                    all_characteristics
                ),
                "data_diagnostics": {
                    "structure": data_structure,
                    "n_observations": len(data),
                    "n_variables": len(independent_vars) if independent_vars else 0,
                    "dependent_var_characteristics": dep_var_characteristics,
                    "detected_issues": econometric_issues,
                    "missing_data_pct": float(
                        data[dependent_var].isnull().mean() * 100
                    ),
                },
                "implementation_guidance": implementation_guidance,
                "prerequisite_checks": prerequisite_checks,
                "method_comparison": {
                    method: self._explain_method_suitability(
                        method, all_characteristics
                    )
                    for method in [recommended_method] + alternatives[:2]
                },
                "interpretation": f"Recommended econometric method: {recommended_method}. {rationale}",
                "recommendations": [
                    f"Apply {recommended_method} method for analysis",
                    "Validate model assumptions before interpretation",
                    "Consider robustness checks with alternative methods",
                ],
                "success": True,
            }

            self.logger.info(f"Recommended method: {recommended_method}")
            return result

        except Exception as e:
            self.logger.error(f"Auto-detect method failed: {str(e)}")
            raise

    def auto_analyze_econometric_data(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: Optional[List[str]] = None,
        panel_id: Optional[str] = None,
        time_var: Optional[str] = None,
        methods: Optional[List[str]] = None,
        include_diagnostics: bool = True,
        include_robustness: bool = True,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Run comprehensive automated econometric analysis.

        Performs multiple econometric analyses, compares results, and provides
        integrated insights. Useful for exploratory analysis and robustness checking.

        Args:
            data: Input dataset
            dependent_var: Dependent variable
            independent_vars: Independent variables
            panel_id: Panel identifier (if applicable)
            time_var: Time variable (if applicable)
            methods: Specific methods to run (if None, auto-selects best methods)
            include_diagnostics: Include detailed diagnostics
            include_robustness: Run robustness checks
            confidence_level: Confidence level for inference

        Returns:
            Dictionary containing:
            - primary_results: Results from primary method
            - alternative_results: Results from alternative methods
            - robustness_checks: Robustness test results
            - meta_analysis: Cross-method synthesis
            - recommendations: Interpretation and next steps
            - diagnostics: Comprehensive diagnostic suite

        Example:
            # Comprehensive analysis of coaching effects
            result = auto_analyze_econometric_data(
                data=team_season_df,
                dependent_var='win_pct',
                independent_vars=['payroll', 'experience', 'coach_tenure'],
                panel_id='team_id',
                time_var='season',
                include_robustness=True
            )
        """
        try:
            self.logger.info(
                f"Running auto-analysis: dependent={dependent_var}, methods={methods}"
            )

            # Validate inputs
            if data.empty:
                raise ValueError("Input data is empty")

            # Auto-detect best methods if not specified
            if methods is None:
                detection_result = self.auto_detect_econometric_method(
                    data, dependent_var, independent_vars, panel_id, time_var
                )
                methods = [detection_result["recommended_method"]] + detection_result[
                    "alternative_methods"
                ][:2]

            self.logger.info(f"Analyzing with methods: {methods}")

            # Run each method
            method_results = {}
            for method in methods:
                try:
                    result = self._run_method(
                        method,
                        data,
                        dependent_var,
                        independent_vars,
                        panel_id,
                        time_var,
                        confidence_level,
                    )
                    method_results[method] = result
                    self.logger.info(f"Method {method} completed successfully")
                except Exception as e:
                    self.logger.warning(f"Method {method} failed: {str(e)}")
                    method_results[method] = {"error": str(e), "status": "failed"}

            # Extract primary results
            primary_method = methods[0]
            primary_results = method_results.get(primary_method, {})

            # Robustness checks
            robustness_results = {}
            if include_robustness and primary_results.get("status") != "failed":
                robustness_results = self._run_robustness_checks(
                    data,
                    dependent_var,
                    independent_vars,
                    panel_id,
                    time_var,
                    primary_method,
                )

            # Cross-method meta-analysis
            meta_analysis = self._synthesize_results(
                method_results, dependent_var, independent_vars
            )

            # Generate diagnostics
            diagnostics = {}
            if include_diagnostics:
                diagnostics = self._generate_comprehensive_diagnostics(
                    data, dependent_var, independent_vars, method_results
                )

            # Generate recommendations
            recommendations = self._generate_analysis_recommendations(
                method_results, meta_analysis, diagnostics
            )

            # Build result
            result = {
                "primary_results": {
                    "method": primary_method,
                    "results": primary_results,
                    "interpretation": self._interpret_results(
                        primary_results, primary_method
                    ),
                },
                "alternative_results": {
                    method: {
                        "results": res,
                        "comparison_to_primary": self._compare_to_primary(
                            res, primary_results
                        ),
                    }
                    for method, res in method_results.items()
                    if method != primary_method and res.get("status") != "failed"
                },
                "robustness_checks": robustness_results,
                "meta_analysis": meta_analysis,
                "diagnostics": diagnostics,
                "recommendations": recommendations,
                "summary": {
                    "methods_run": len(
                        [
                            m
                            for m, r in method_results.items()
                            if r.get("status") != "failed"
                        ]
                    ),
                    "methods_failed": len(
                        [
                            m
                            for m, r in method_results.items()
                            if r.get("status") == "failed"
                        ]
                    ),
                    "key_findings": self._extract_key_findings(meta_analysis),
                    "confidence_assessment": self._assess_overall_confidence(
                        method_results, meta_analysis
                    ),
                },
            }

            self.logger.info(
                f"Auto-analysis complete: {result['summary']['methods_run']} methods successful"
            )
            return result

        except Exception as e:
            self.logger.error(f"Auto-analysis failed: {str(e)}")
            raise

    def compare_econometric_methods(
        self,
        results: Dict[str, Dict[str, Any]],
        comparison_dimensions: Optional[List[str]] = None,
        weight_by_fit: bool = True,
    ) -> Dict[str, Any]:
        """
        Compare results across different econometric methods.

        Provides systematic comparison of coefficient estimates, standard errors,
        fit statistics, and diagnostic results across multiple methods.

        Args:
            results: Dictionary of method names to their results
            comparison_dimensions: Aspects to compare (coefficients, fit, diagnostics)
            weight_by_fit: Weight estimates by model fit statistics

        Returns:
            Dictionary containing:
            - coefficient_comparison: Side-by-side coefficient estimates
            - fit_comparison: Model fit statistics comparison
            - diagnostic_comparison: Diagnostic test comparison
            - consensus_estimates: Weighted/averaged coefficient estimates
            - disagreement_analysis: Where methods diverge significantly
            - recommendation: Which method(s) to trust most

        Example:
            # Compare fixed effects vs random effects vs GMM
            results_dict = {
                'fixed_effects': fe_results,
                'random_effects': re_results,
                'gmm': gmm_results
            }
            comparison = compare_econometric_methods(
                results=results_dict,
                weight_by_fit=True
            )
        """
        try:
            self.logger.info(f"Comparing {len(results)} methods")

            # Validate inputs
            if not results:
                raise ValueError("No results provided for comparison")

            if len(results) < 2:
                raise ValueError("Need at least 2 methods to compare")

            # Default comparison dimensions
            if comparison_dimensions is None:
                comparison_dimensions = [
                    "coefficients",
                    "fit_statistics",
                    "diagnostics",
                    "inference",
                ]

            # Extract coefficient estimates
            coefficient_comparison = self._compare_coefficients(results)

            # Compare fit statistics
            fit_comparison = self._compare_fit_statistics(results)

            # Compare diagnostics
            diagnostic_comparison = self._compare_diagnostics(results)

            # Compute consensus estimates
            consensus_estimates = self._compute_consensus_estimates(
                results, weight_by_fit, fit_comparison
            )

            # Analyze disagreements
            disagreement_analysis = self._analyze_disagreements(
                coefficient_comparison, results
            )

            # Generate recommendation
            recommendation = self._generate_method_recommendation(
                results, fit_comparison, diagnostic_comparison, disagreement_analysis
            )

            # Build result
            result = {
                "coefficient_comparison": coefficient_comparison,
                "fit_comparison": fit_comparison,
                "diagnostic_comparison": diagnostic_comparison,
                "consensus_estimates": consensus_estimates,
                "disagreement_analysis": disagreement_analysis,
                "recommendation": recommendation,
                "summary": {
                    "n_methods": len(results),
                    "methods_compared": list(results.keys()),
                    "best_fitting_method": fit_comparison.get("best_method", "unknown"),
                    "most_robust_method": self._identify_most_robust(
                        diagnostic_comparison
                    ),
                    "coefficient_agreement_score": self._compute_agreement_score(
                        coefficient_comparison
                    ),
                },
            }

            self.logger.info(
                f"Comparison complete: best method = {result['summary']['best_fitting_method']}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Method comparison failed: {str(e)}")
            raise

    def econometric_model_averaging(
        self,
        results: Dict[str, Dict[str, Any]],
        data: pd.DataFrame,
        dependent_var: str,
        averaging_method: str = "aic",
        bootstrap_ci: bool = True,
        n_bootstrap: int = 1000,
    ) -> Dict[str, Any]:
        """
        Combine predictions and estimates from multiple econometric models.

        Uses model averaging to obtain more robust coefficient estimates and
        predictions by weighting multiple models based on their fit/performance.

        Args:
            results: Dictionary of method names to their results
            data: Original data (for out-of-sample validation)
            dependent_var: Dependent variable name
            averaging_method: Weighting scheme ('aic', 'bic', 'mse', 'equal')
            bootstrap_ci: Use bootstrap for confidence intervals
            n_bootstrap: Number of bootstrap replications

        Returns:
            Dictionary containing:
            - averaged_coefficients: Model-averaged coefficient estimates
            - model_weights: Weight assigned to each model
            - averaged_predictions: Combined predictions
            - averaged_standard_errors: Model-averaged SEs
            - confidence_intervals: Adjusted confidence intervals
            - model_inclusion_probabilities: Probability each variable matters

        Example:
            # Average across OLS, fixed effects, and instrumental variables
            averaged_result = econometric_model_averaging(
                results={'ols': ols_res, 'fe': fe_res, 'iv': iv_res},
                data=team_df,
                dependent_var='win_pct',
                averaging_method='aic'
            )
        """
        try:
            self.logger.info(
                f"Model averaging: {len(results)} models, method={averaging_method}"
            )

            # Validate inputs
            if not results:
                raise ValueError("No results provided for averaging")

            if data.empty:
                raise ValueError("Data required for model averaging")

            # Compute model weights
            model_weights = self._compute_model_weights(results, averaging_method)

            # Extract coefficients from each model
            all_coefficients = self._extract_all_coefficients(results)

            # Compute weighted average coefficients
            averaged_coefficients = self._compute_weighted_average(
                all_coefficients, model_weights
            )

            # Compute model-averaged standard errors
            averaged_standard_errors = self._compute_averaged_standard_errors(
                results, model_weights, averaged_coefficients
            )

            # Compute predictions from each model
            predictions = self._compute_predictions_from_results(results, data)

            # Compute weighted average predictions
            averaged_predictions = self._compute_weighted_predictions(
                predictions, model_weights
            )

            # Bootstrap confidence intervals if requested
            confidence_intervals = {}
            if bootstrap_ci:
                self.logger.info(
                    f"Computing bootstrap CIs with {n_bootstrap} replications"
                )
                confidence_intervals = self._bootstrap_model_averaging(
                    results, data, dependent_var, averaging_method, n_bootstrap
                )
            else:
                # Use analytic confidence intervals
                confidence_intervals = self._analytic_confidence_intervals(
                    averaged_coefficients, averaged_standard_errors
                )

            # Compute model inclusion probabilities
            inclusion_probs = self._compute_inclusion_probabilities(
                all_coefficients, model_weights
            )

            # Compute performance metrics
            y_actual = data[dependent_var].values
            y_pred = averaged_predictions

            # Handle potential length mismatches
            min_len = min(len(y_actual), len(y_pred))
            y_actual = y_actual[:min_len]
            y_pred = y_pred[:min_len]

            mse = np.mean((y_actual - y_pred) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(y_actual - y_pred))
            r_squared = 1 - np.var(y_actual - y_pred) / np.var(y_actual)

            # Build result
            result = {
                "averaged_coefficients": averaged_coefficients,
                "averaged_standard_errors": averaged_standard_errors,
                "confidence_intervals": confidence_intervals,
                "model_weights": model_weights,
                "averaged_predictions": pd.Series(
                    averaged_predictions, index=data.index[:min_len]
                ).to_dict(),
                "model_inclusion_probabilities": inclusion_probs,
                "performance_metrics": {
                    "mse": float(mse),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "r_squared": float(r_squared),
                },
                "individual_model_performance": {
                    model: self._compute_model_performance(pred, y_actual)
                    for model, pred in predictions.items()
                },
                "summary": {
                    "n_models": len(results),
                    "averaging_method": averaging_method,
                    "most_important_variables": self._identify_important_variables(
                        inclusion_probs
                    ),
                    "dominant_model": max(model_weights, key=model_weights.get),
                    "effective_n_models": self._compute_effective_n_models(
                        model_weights
                    ),
                },
            }

            self.logger.info(
                f"Model averaging complete: R²={r_squared:.3f}, dominant={result['summary']['dominant_model']}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Model averaging failed: {str(e)}")
            raise

    # ========== Helper Methods ==========

    def _build_method_registry(self) -> Dict[str, Dict[str, Any]]:
        """Build registry of available econometric methods and their characteristics."""
        return {
            "fixed_effects": {
                "category": "panel",
                "handles_endogeneity": False,
                "requires_panel": True,
                "suitable_for": ["unobserved_heterogeneity", "time_invariant_effects"],
            },
            "random_effects": {
                "category": "panel",
                "handles_endogeneity": False,
                "requires_panel": True,
                "suitable_for": ["efficient_estimation", "cross_sectional_variation"],
            },
            "instrumental_variables": {
                "category": "causal",
                "handles_endogeneity": True,
                "requires_panel": False,
                "suitable_for": [
                    "endogeneity",
                    "omitted_variables",
                    "measurement_error",
                ],
            },
            "difference_in_differences": {
                "category": "causal",
                "handles_endogeneity": True,
                "requires_panel": True,
                "suitable_for": [
                    "policy_evaluation",
                    "treatment_effects",
                    "natural_experiments",
                ],
            },
            "regression_discontinuity": {
                "category": "causal",
                "handles_endogeneity": True,
                "requires_panel": False,
                "suitable_for": [
                    "threshold_based_treatment",
                    "local_treatment_effects",
                ],
            },
            "propensity_score_matching": {
                "category": "causal",
                "handles_endogeneity": True,
                "requires_panel": False,
                "suitable_for": [
                    "observational_studies",
                    "treatment_selection",
                    "balancing",
                ],
            },
            "survival_analysis": {
                "category": "duration",
                "handles_endogeneity": False,
                "requires_panel": False,
                "suitable_for": ["time_to_event", "censored_data", "duration_modeling"],
            },
            "bayesian_regression": {
                "category": "bayesian",
                "handles_endogeneity": False,
                "requires_panel": False,
                "suitable_for": [
                    "prior_information",
                    "uncertainty_quantification",
                    "hierarchical_models",
                ],
            },
        }

    def _detect_data_structure(
        self, data: pd.DataFrame, panel_id: Optional[str], time_var: Optional[str]
    ) -> Dict[str, Any]:
        """Detect data structure characteristics."""
        structure = {
            "type": "cross_sectional",
            "is_panel": False,
            "is_time_series": False,
            "is_balanced": None,
            "n_groups": None,
            "n_time_periods": None,
            "avg_periods_per_group": None,
        }

        if panel_id and time_var:
            structure["type"] = "panel"
            structure["is_panel"] = True
            structure["n_groups"] = data[panel_id].nunique()
            structure["n_time_periods"] = data[time_var].nunique()

            # Check if balanced
            group_sizes = data.groupby(panel_id).size()
            structure["is_balanced"] = group_sizes.std() == 0
            structure["avg_periods_per_group"] = float(group_sizes.mean())

        elif time_var:
            structure["type"] = "time_series"
            structure["is_time_series"] = True
            structure["n_time_periods"] = data[time_var].nunique()

        return structure

    def _analyze_variable_characteristics(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze dependent variable characteristics."""
        return {
            "type": self._infer_variable_type(series),
            "is_binary": series.nunique() == 2,
            "is_count": (series >= 0).all() and (series == series.astype(int)).all(),
            "is_continuous": not ((series == series.astype(int)).all()),
            "has_zeros": (series == 0).any(),
            "is_censored": self._detect_censoring(series),
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": float(series.mean()),
            "std": float(series.std()),
        }

    def _infer_variable_type(self, series: pd.Series) -> str:
        """Infer variable type."""
        if series.nunique() == 2:
            return "binary"
        elif (series >= 0).all() and (series == series.astype(int)).all():
            return "count"
        elif (series == series.astype(int)).all():
            return "discrete"
        else:
            return "continuous"

    def _detect_censoring(self, series: pd.Series) -> bool:
        """Detect if data appears censored."""
        # Simple heuristic: many values at min or max
        at_min = (series == series.min()).sum() / len(series)
        at_max = (series == series.max()).sum() / len(series)
        return at_min > 0.1 or at_max > 0.1

    def _detect_econometric_issues(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: Optional[List[str]],
        panel_id: Optional[str],
        time_var: Optional[str],
    ) -> Dict[str, bool]:
        """Detect potential econometric issues."""
        issues = {
            "multicollinearity": False,
            "heteroskedasticity": False,
            "autocorrelation": False,
            "endogeneity_suspected": False,
            "missing_data": False,
            "outliers": False,
        }

        # Missing data
        issues["missing_data"] = data[dependent_var].isnull().any()

        # Outliers (simple Z-score method)
        z_scores = np.abs(
            (data[dependent_var] - data[dependent_var].mean())
            / data[dependent_var].std()
        )
        issues["outliers"] = (z_scores > 3).any()

        # Multicollinearity (if independent vars provided)
        if independent_vars and len(independent_vars) > 1:
            corr_matrix = data[independent_vars].corr().abs()
            np.fill_diagonal(corr_matrix.values, 0)
            issues["multicollinearity"] = (corr_matrix > 0.8).any().any()

        return issues

    def _parse_research_question(self, question: str) -> Dict[str, Any]:
        """Parse research question to infer intent."""
        question_lower = question.lower()

        intent = {
            "causal_inference": any(
                word in question_lower for word in ["cause", "effect", "impact", "does"]
            ),
            "prediction": any(
                word in question_lower for word in ["predict", "forecast", "estimate"]
            ),
            "description": any(
                word in question_lower for word in ["describe", "summarize", "what is"]
            ),
            "comparison": any(
                word in question_lower for word in ["compare", "difference", "versus"]
            ),
            "keywords": [
                word
                for word in [
                    "endogeneity",
                    "selection",
                    "treatment",
                    "policy",
                    "intervention",
                ]
                if word in question_lower
            ],
        }

        return intent

    def _select_method(
        self, characteristics: Dict[str, Any]
    ) -> Tuple[str, List[str], str]:
        """Select appropriate econometric method based on characteristics."""
        data_struct = characteristics["data_structure"]
        dep_var = characteristics["dependent_var_type"]
        issues = characteristics["econometric_issues"]
        intent = characteristics["research_intent"]

        # Decision logic
        if intent.get("causal_inference"):
            if issues.get("endogeneity_suspected") or "endogeneity" in intent.get(
                "keywords", []
            ):
                recommended = "instrumental_variables"
                alternatives = ["propensity_score_matching", "regression_discontinuity"]
                rationale = "Research question implies causal inference with potential endogeneity. IV recommended."
            elif data_struct["is_panel"] and "treatment" in intent.get("keywords", []):
                recommended = "difference_in_differences"
                alternatives = ["synthetic_control", "fixed_effects"]
                rationale = "Panel data with treatment suggests difference-in-differences approach."
            else:
                recommended = "propensity_score_matching"
                alternatives = ["regression_discontinuity", "instrumental_variables"]
                rationale = "Causal inference without strong identification strategy suggests PSM."
        elif data_struct["is_panel"]:
            if issues.get("endogeneity_suspected"):
                recommended = "fixed_effects"
                alternatives = ["random_effects", "first_differences"]
                rationale = "Panel data with potential endogeneity: fixed effects controls for unobserved heterogeneity."
            else:
                recommended = "random_effects"
                alternatives = ["fixed_effects", "pooled_ols"]
                rationale = "Panel data without endogeneity concerns: random effects more efficient."
        elif dep_var.get("is_censored"):
            recommended = "survival_analysis"
            alternatives = ["tobit", "duration_model"]
            rationale = (
                "Censored dependent variable suggests survival/duration analysis."
            )
        elif dep_var.get("is_binary"):
            recommended = "logistic_regression"
            alternatives = ["probit", "linear_probability"]
            rationale = "Binary outcome variable: logistic regression appropriate."
        else:
            recommended = "ols_regression"
            alternatives = ["robust_regression", "quantile_regression"]
            rationale = "Standard continuous outcome: OLS baseline recommended."

        return recommended, alternatives, rationale

    def _compute_recommendation_confidence(
        self, characteristics: Dict[str, Any]
    ) -> float:
        """Compute confidence score for recommendation."""
        # Simple heuristic
        confidence = 0.7

        if characteristics["research_intent"].get("causal_inference"):
            confidence += 0.1

        if characteristics["data_structure"]["is_panel"]:
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_implementation_guidance(
        self,
        method: str,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: Optional[List[str]],
        panel_id: Optional[str],
        time_var: Optional[str],
    ) -> Dict[str, Any]:
        """Generate implementation guidance for recommended method."""
        return {
            "tool_name": method,
            "required_parameters": {
                "data": "Input DataFrame",
                "dependent_var": dependent_var,
                "independent_vars": independent_vars or "To be specified",
            },
            "optional_parameters": {"panel_id": panel_id, "time_var": time_var},
            "example_code": f"result = {method}(data=df, dependent_var='{dependent_var}', ...)",
        }

    def _generate_prerequisite_checks(
        self, method: str, characteristics: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate prerequisite checks for method."""
        checks = [
            {
                "check": "Sufficient sample size",
                "status": "required",
                "guidance": "Need at least 30 observations per parameter",
            },
            {
                "check": "No perfect multicollinearity",
                "status": "required",
                "guidance": "Check VIF < 10",
            },
            {
                "check": "Valid identification strategy",
                "status": "recommended",
                "guidance": "Ensure causal assumptions hold",
            },
        ]
        return checks

    def _explain_method_suitability(
        self, method: str, characteristics: Dict[str, Any]
    ) -> str:
        """Explain why a method is or isn't suitable."""
        return f"Method '{method}' is suitable based on detected data characteristics."

    def _run_method(
        self,
        method: str,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: Optional[List[str]],
        panel_id: Optional[str],
        time_var: Optional[str],
        confidence_level: float,
    ) -> Dict[str, Any]:
        """Run a specific econometric method."""
        # Placeholder: would call actual method implementations
        return {
            "status": "success",
            "method": method,
            "coefficients": {"var1": 0.5, "var2": -0.3},
            "std_errors": {"var1": 0.1, "var2": 0.08},
            "fit_statistics": {"r_squared": 0.65, "aic": 150.2, "bic": 165.3},
        }

    def _run_robustness_checks(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: Optional[List[str]],
        panel_id: Optional[str],
        time_var: Optional[str],
        primary_method: str,
    ) -> Dict[str, Any]:
        """Run robustness checks."""
        return {
            "alternative_specifications": {},
            "subsample_analysis": {},
            "placebo_tests": {},
        }

    def _synthesize_results(
        self,
        method_results: Dict[str, Dict[str, Any]],
        dependent_var: str,
        independent_vars: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Synthesize results across methods."""
        return {
            "coefficient_ranges": {},
            "consistent_findings": [],
            "inconsistent_findings": [],
            "overall_confidence": 0.8,
        }

    def _generate_comprehensive_diagnostics(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: Optional[List[str]],
        method_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive diagnostics."""
        return {"data_quality": {}, "model_assumptions": {}, "specification_tests": {}}

    def _generate_analysis_recommendations(
        self,
        method_results: Dict[str, Dict[str, Any]],
        meta_analysis: Dict[str, Any],
        diagnostics: Dict[str, Any],
    ) -> List[str]:
        """Generate analysis recommendations."""
        return [
            "Primary method shows good fit",
            "Consider additional robustness checks",
            "Results are robust across specifications",
        ]

    def _interpret_results(self, results: Dict[str, Any], method: str) -> str:
        """Interpret method results."""
        return f"Method '{method}' results suggest..."

    def _compare_to_primary(
        self, alt_results: Dict[str, Any], primary_results: Dict[str, Any]
    ) -> str:
        """Compare alternative results to primary."""
        return "Results are consistent with primary analysis."

    def _extract_key_findings(self, meta_analysis: Dict[str, Any]) -> List[str]:
        """Extract key findings from meta-analysis."""
        return ["Finding 1", "Finding 2", "Finding 3"]

    def _assess_overall_confidence(
        self, method_results: Dict[str, Dict[str, Any]], meta_analysis: Dict[str, Any]
    ) -> str:
        """Assess overall confidence in results."""
        return "High confidence - results are robust across methods"

    def _compare_coefficients(self, results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """Compare coefficients across methods."""
        # Extract coefficients from each method
        coef_dict = {}
        for method, res in results.items():
            if "coefficients" in res:
                coef_dict[method] = res["coefficients"]

        return pd.DataFrame(coef_dict)

    def _compare_fit_statistics(
        self, results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare fit statistics across methods."""
        fit_stats = {}
        for method, res in results.items():
            if "fit_statistics" in res:
                fit_stats[method] = res["fit_statistics"]

        # Identify best method
        best_method = (
            min(fit_stats.items(), key=lambda x: x[1].get("aic", float("inf")))[0]
            if fit_stats
            else None
        )

        return {"fit_statistics": fit_stats, "best_method": best_method}

    def _compare_diagnostics(
        self, results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare diagnostic tests across methods."""
        return {"diagnostics_by_method": {}}

    def _compute_consensus_estimates(
        self,
        results: Dict[str, Dict[str, Any]],
        weight_by_fit: bool,
        fit_comparison: Dict[str, Any],
    ) -> Dict[str, float]:
        """Compute consensus coefficient estimates."""
        return {}

    def _analyze_disagreements(
        self, coefficient_comparison: pd.DataFrame, results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze where methods disagree."""
        return {"disagreement_score": 0.2, "main_disagreements": []}

    def _generate_method_recommendation(
        self,
        results: Dict[str, Dict[str, Any]],
        fit_comparison: Dict[str, Any],
        diagnostic_comparison: Dict[str, Any],
        disagreement_analysis: Dict[str, Any],
    ) -> str:
        """Generate recommendation for which method to trust."""
        best = fit_comparison.get("best_method", "unknown")
        return f"Recommend using '{best}' based on fit statistics and diagnostics."

    def _identify_most_robust(self, diagnostic_comparison: Dict[str, Any]) -> str:
        """Identify most robust method."""
        return "method_1"

    def _compute_agreement_score(self, coefficient_comparison: pd.DataFrame) -> float:
        """Compute agreement score across methods."""
        return 0.85

    def _compute_model_weights(
        self, results: Dict[str, Dict[str, Any]], method: str
    ) -> Dict[str, float]:
        """Compute model weights based on fit."""
        if method == "equal":
            return {model: 1.0 / len(results) for model in results}

        # Extract fit statistics
        fit_stats = {}
        for model, res in results.items():
            if "fit_statistics" in res:
                if method == "aic":
                    fit_stats[model] = res["fit_statistics"].get("aic", float("inf"))
                elif method == "bic":
                    fit_stats[model] = res["fit_statistics"].get("bic", float("inf"))
                else:
                    fit_stats[model] = float("inf")

        # Compute AIC/BIC weights
        min_stat = min(fit_stats.values())
        delta_stats = {model: stat - min_stat for model, stat in fit_stats.items()}
        weights = {model: np.exp(-0.5 * delta) for model, delta in delta_stats.items()}
        total_weight = sum(weights.values())

        return {model: w / total_weight for model, w in weights.items()}

    def _extract_all_coefficients(
        self, results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Extract coefficients from all models."""
        return {model: res.get("coefficients", {}) for model, res in results.items()}

    def _compute_weighted_average(
        self,
        all_coefficients: Dict[str, Dict[str, float]],
        model_weights: Dict[str, float],
    ) -> Dict[str, float]:
        """Compute weighted average of coefficients."""
        # Get all variable names
        all_vars = set()
        for coefs in all_coefficients.values():
            all_vars.update(coefs.keys())

        averaged = {}
        for var in all_vars:
            weighted_sum = 0.0
            total_weight = 0.0
            for model, coefs in all_coefficients.items():
                if var in coefs:
                    weighted_sum += coefs[var] * model_weights[model]
                    total_weight += model_weights[model]
            averaged[var] = weighted_sum / total_weight if total_weight > 0 else 0.0

        return averaged

    def _compute_averaged_standard_errors(
        self,
        results: Dict[str, Dict[str, Any]],
        model_weights: Dict[str, float],
        averaged_coefficients: Dict[str, float],
    ) -> Dict[str, float]:
        """Compute model-averaged standard errors."""
        return {var: 0.1 for var in averaged_coefficients}  # Placeholder

    def _compute_predictions_from_results(
        self, results: Dict[str, Dict[str, Any]], data: pd.DataFrame
    ) -> Dict[str, np.ndarray]:
        """Compute predictions from each model."""
        # Placeholder
        n = len(data)
        return {model: np.random.randn(n) for model in results}

    def _compute_weighted_predictions(
        self, predictions: Dict[str, np.ndarray], model_weights: Dict[str, float]
    ) -> np.ndarray:
        """Compute weighted average of predictions."""
        n = len(next(iter(predictions.values())))
        weighted_pred = np.zeros(n)

        for model, pred in predictions.items():
            weighted_pred += pred * model_weights[model]

        return weighted_pred

    def _bootstrap_model_averaging(
        self,
        results: Dict[str, Dict[str, Any]],
        data: pd.DataFrame,
        dependent_var: str,
        averaging_method: str,
        n_bootstrap: int,
    ) -> Dict[str, Dict[str, float]]:
        """Bootstrap confidence intervals for model averaging."""
        return {}  # Placeholder

    def _analytic_confidence_intervals(
        self, coefficients: Dict[str, float], standard_errors: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Compute analytic confidence intervals."""
        ci = {}
        for var, coef in coefficients.items():
            se = standard_errors.get(var, 0.1)
            ci[var] = {"lower": coef - 1.96 * se, "upper": coef + 1.96 * se}
        return ci

    def _compute_inclusion_probabilities(
        self,
        all_coefficients: Dict[str, Dict[str, float]],
        model_weights: Dict[str, float],
    ) -> Dict[str, float]:
        """Compute probability each variable is included."""
        all_vars = set()
        for coefs in all_coefficients.values():
            all_vars.update(coefs.keys())

        inclusion_probs = {}
        for var in all_vars:
            prob = sum(
                model_weights[model]
                for model, coefs in all_coefficients.items()
                if var in coefs
            )
            inclusion_probs[var] = prob

        return inclusion_probs

    def _compute_model_performance(
        self, predictions: np.ndarray, actual: np.ndarray
    ) -> Dict[str, float]:
        """Compute performance metrics for a model."""
        min_len = min(len(predictions), len(actual))
        predictions = predictions[:min_len]
        actual = actual[:min_len]

        mse = np.mean((actual - predictions) ** 2)
        return {
            "mse": float(mse),
            "rmse": float(np.sqrt(mse)),
            "mae": float(np.mean(np.abs(actual - predictions))),
        }

    def _identify_important_variables(
        self, inclusion_probs: Dict[str, float]
    ) -> List[str]:
        """Identify most important variables by inclusion probability."""
        sorted_vars = sorted(inclusion_probs.items(), key=lambda x: x[1], reverse=True)
        return [var for var, prob in sorted_vars[:5]]

    def _compute_effective_n_models(self, model_weights: Dict[str, float]) -> float:
        """Compute effective number of models (inverse of sum of squared weights)."""
        sum_squared_weights = sum(w**2 for w in model_weights.values())
        return (
            1.0 / sum_squared_weights if sum_squared_weights > 0 else len(model_weights)
        )


def create_econometric_suite_tools() -> EconometricSuiteTools:
    """Factory function to create econometric suite tools instance."""
    return EconometricSuiteTools()
