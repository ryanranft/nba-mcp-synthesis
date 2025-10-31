"""
Bayesian Analysis MCP Tools - Phase 10A Agent 8 Module 3

This module provides MCP tool wrappers for Bayesian inference and modeling,
exposing hierarchical models, MCMC sampling, and posterior analysis as FastMCP
tools accessible via Claude Desktop and other MCP clients.

Implements advanced Bayesian methods for NBA analytics including:
- Hierarchical models (players nested in teams)
- MCMC posterior sampling
- Credible intervals and posterior summaries
- Model comparison (WAIC, LOO)
- Bayesian prediction and uncertainty quantification

Tools:
1. hierarchical_bayesian_model - Build and fit hierarchical Bayesian models
2. sample_posterior - MCMC sampling for posterior inference
3. posterior_summary - Summarize posterior distributions
4. credible_interval - Bayesian confidence intervals
5. compare_bayesian_models - Model comparison via WAIC/LOO
6. bayesian_player_model - NBA-specific player performance model
7. bayesian_win_probability - Bayesian win probability estimation

Author: Phase 10A Agent 8 Module 3
Date: October 2025
"""

import logging
from typing import Dict, Any, List, Union, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class BayesianTools:
    """
    MCP tool wrappers for Bayesian inference and modeling.

    Provides thin wrappers around the BayesianAnalyzer implementation,
    converting between MCP-friendly formats and the underlying Bayesian
    analysis methods using PyMC.
    """

    def __init__(self):
        """Initialize BayesianTools."""
        self.logger = logger

    # =========================================================================
    # Tool 1: Hierarchical Bayesian Model
    # =========================================================================

    async def hierarchical_bayesian_model(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        group_column: str,
        target_column: str = "value",
        draws: int = 2000,
        tune: int = 1000,
        chains: int = 4,
    ) -> Dict[str, Any]:
        """
        Build and fit hierarchical Bayesian model with grouped data.

        Hierarchical models allow for partial pooling, where group-level effects
        are estimated with shrinkage toward the global mean. Ideal for NBA data
        where players are nested within teams or games within seasons.

        Args:
            data: List of dictionaries containing panel/grouped data
            formula: Model formula (e.g., "points ~ minutes + age")
            group_column: Column identifying groups (player_id, team_id)
            target_column: Dependent variable column
            draws: Number of posterior samples (default: 2000)
            tune: Number of tuning samples (default: 1000)
            chains: Number of MCMC chains (default: 4)

        Returns:
            Dictionary containing:
            - success: True if model fit succeeded
            - posterior_mean: Dict of parameter posterior means
            - posterior_std: Dict of parameter posterior std devs
            - credible_intervals: 95% HDI for each parameter
            - group_effects: Dict of group-specific effects
            - convergence: Dict with R-hat and ESS diagnostics
            - waic: WAIC information criterion
            - loo: LOO cross-validation score
            - interpretation: Human-readable summary
            - error: Error message if failed

        Example:
            >>> data = [
            ...     {"player_id": "LeBron", "points": 25, "minutes": 35, "age": 38},
            ...     {"player_id": "Curry", "points": 30, "minutes": 34, "age": 35},
            ... ]
            >>> result = await hierarchical_bayesian_model(
            ...     data=data,
            ...     formula="points ~ minutes + age",
            ...     group_column="player_id"
            ... )
            >>> result['posterior_mean']['minutes']
            0.68  # Expected points per minute

        NBA Use Cases:
            - Model player scoring with team-level random effects
            - Estimate shot success probability with player hierarchy
            - Predict performance accounting for team context
        """
        try:
            from mcp_server.bayesian import BayesianAnalyzer

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Validate columns
            required_cols = [group_column, target_column]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error": f"Missing required columns: {missing_cols}",
                }

            # Parse formula to get predictors
            target, predictors_str = formula.split("~")
            target = target.strip()
            predictors = [p.strip() for p in predictors_str.split("+")]

            # Validate predictor columns
            missing_predictors = [p for p in predictors if p not in df.columns]
            if missing_predictors:
                return {
                    "success": False,
                    "error": f"Missing predictor columns: {missing_predictors}",
                }

            # Initialize analyzer
            analyzer = BayesianAnalyzer(
                data=df,
                target_col=target,
                group_col=group_column
            )

            # Fit hierarchical model
            result = analyzer.hierarchical_model(
                formula=formula,
                groups=[group_column],
                draws=draws,
                tune=tune,
                chains=chains
            )

            # Extract group effects
            group_effects = analyzer.posterior_summary(result)
            group_effects_dict = {
                param: {
                    "mean": float(row["mean"]),
                    "std": float(row["sd"]),
                    "hdi_3%": float(row["hdi_3%"]),
                    "hdi_97%": float(row["hdi_97%"]),
                }
                for param, row in group_effects.iterrows()
                if group_column in param
            }

            # Check convergence
            convergence = analyzer.check_convergence(result)

            # Model comparison metrics
            waic_score = analyzer.waic(result)
            loo_score = analyzer.loo(result)

            # Build interpretation
            n_groups = df[group_column].nunique()
            interpretation = (
                f"Hierarchical Bayesian model fit with {n_groups} groups. "
                f"Convergence: {'Good' if convergence['converged'] else 'Issues detected'}. "
                f"WAIC: {waic_score:.2f}, LOO: {loo_score:.2f}."
            )

            return {
                "success": True,
                "posterior_mean": {
                    param: float(row["mean"])
                    for param, row in group_effects.iterrows()
                },
                "posterior_std": {
                    param: float(row["sd"])
                    for param, row in group_effects.iterrows()
                },
                "credible_intervals": {
                    param: {
                        "lower": float(row["hdi_3%"]),
                        "upper": float(row["hdi_97%"]),
                    }
                    for param, row in group_effects.iterrows()
                },
                "group_effects": group_effects_dict,
                "convergence": convergence,
                "waic": float(waic_score),
                "loo": float(loo_score),
                "interpretation": interpretation,
                "n_groups": n_groups,
                "n_observations": len(df),
            }

        except Exception as e:
            self.logger.error(f"Hierarchical Bayesian model failed: {str(e)}")
            return {
                "success": False,
                "error": f"Hierarchical Bayesian model failed: {str(e)}",
            }

    # =========================================================================
    # Tool 2: Sample Posterior
    # =========================================================================

    async def sample_posterior(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        target_column: str = "value",
        draws: int = 2000,
        tune: int = 1000,
        chains: int = 4,
        prior_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform MCMC sampling to obtain posterior distributions.

        Uses No-U-Turn Sampler (NUTS) for efficient posterior sampling.
        Returns full posterior samples for uncertainty quantification and
        posterior predictive checks.

        Args:
            data: List of dictionaries with observations
            formula: Regression formula (e.g., "y ~ x1 + x2")
            target_column: Dependent variable
            draws: Posterior samples per chain (default: 2000)
            tune: Tuning/burn-in samples (default: 1000)
            chains: Number of independent chains (default: 4)
            prior_params: Optional dict of prior specifications

        Returns:
            Dictionary with:
            - success: True if sampling succeeded
            - posterior_samples: Dict of parameter samples
            - posterior_mean: Mean of each parameter
            - posterior_std: Std dev of each parameter
            - rhat: R-hat convergence diagnostic for each parameter
            - ess: Effective sample size for each parameter
            - divergences: Number of divergent transitions
            - interpretation: Summary of sampling quality
            - error: Error message if failed

        Example:
            >>> result = await sample_posterior(
            ...     data=player_data,
            ...     formula="points ~ minutes + age"
            ... )
            >>> result['posterior_mean']['minutes']
            0.72  # Points per minute effect
            >>> result['rhat']['minutes']
            1.01  # Good convergence (< 1.05)

        NBA Use Cases:
            - Uncertainty quantification for player projections
            - Robust parameter estimation with informative priors
            - Model comparison via marginal likelihoods
        """
        try:
            from mcp_server.bayesian import BayesianAnalyzer

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Parse formula
            target, predictors_str = formula.split("~")
            target = target.strip()

            # Initialize analyzer
            analyzer = BayesianAnalyzer(
                data=df,
                target_col=target
            )

            # Build and sample model
            result = analyzer.sample_posterior(
                formula=formula,
                draws=draws,
                tune=tune,
                chains=chains,
                prior_params=prior_params
            )

            # Get posterior summary
            summary = analyzer.posterior_summary(result)

            # Convergence diagnostics
            rhat_dict = analyzer.rhat_statistic(result)
            ess_dict = analyzer.effective_sample_size(result)
            convergence = analyzer.check_convergence(result)

            # Build interpretation
            max_rhat = max(rhat_dict.values())
            min_ess = min(ess_dict.values())
            interpretation = (
                f"MCMC sampling completed with {draws} draws × {chains} chains. "
                f"Max R-hat: {max_rhat:.3f}, Min ESS: {min_ess:.0f}. "
                f"Convergence: {'Good' if convergence['converged'] else 'Check diagnostics'}."
            )

            return {
                "success": True,
                "posterior_mean": {
                    param: float(row["mean"])
                    for param, row in summary.iterrows()
                },
                "posterior_std": {
                    param: float(row["sd"])
                    for param, row in summary.iterrows()
                },
                "rhat": {k: float(v) for k, v in rhat_dict.items()},
                "ess": {k: float(v) for k, v in ess_dict.items()},
                "divergences": int(convergence.get("n_divergences", 0)),
                "max_rhat": float(max_rhat),
                "min_ess": float(min_ess),
                "interpretation": interpretation,
                "converged": convergence["converged"],
            }

        except Exception as e:
            self.logger.error(f"Posterior sampling failed: {str(e)}")
            return {"success": False, "error": f"Posterior sampling failed: {str(e)}"}

    # =========================================================================
    # Tool 3: Credible Interval
    # =========================================================================

    async def credible_interval(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        target_column: str = "value",
        probability: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Compute Bayesian credible intervals (HDI) for model parameters.

        Highest Density Intervals (HDI) provide Bayesian confidence intervals
        that contain the specified probability mass of the posterior distribution.
        Unlike frequentist CIs, these have direct probability interpretation.

        Args:
            data: List of dictionaries with observations
            formula: Model formula
            target_column: Dependent variable
            probability: Probability mass for interval (default: 0.95)

        Returns:
            Dictionary with:
            - success: True if computation succeeded
            - credible_intervals: Dict of {param: {lower, upper}}
            - posterior_mean: Point estimates
            - interval_width: Width of each interval
            - interpretation: Summary
            - error: Error message if failed

        Example:
            >>> result = await credible_interval(
            ...     data=data,
            ...     formula="points ~ minutes",
            ...     probability=0.95
            ... )
            >>> result['credible_intervals']['minutes']
            {'lower': 0.65, 'upper': 0.79}  # 95% HDI

        NBA Use Cases:
            - Confidence bounds for player projection models
            - Uncertainty in win probability estimates
            - Range estimates for season performance
        """
        try:
            from mcp_server.bayesian import BayesianAnalyzer

            df = pd.DataFrame(data)
            target, _ = formula.split("~")
            target = target.strip()

            analyzer = BayesianAnalyzer(data=df, target_col=target)

            # Sample posterior
            result = analyzer.sample_posterior(formula=formula)

            # Get credible intervals
            ci = analyzer.credible_interval(result, prob=probability)

            # Get posterior mean for comparison
            summary = analyzer.posterior_summary(result)

            intervals = {}
            widths = {}
            for param in ci:
                intervals[param] = {
                    "lower": float(ci[param][0]),
                    "upper": float(ci[param][1]),
                }
                widths[param] = float(ci[param][1] - ci[param][0])

            interpretation = (
                f"{int(probability*100)}% Bayesian credible intervals computed. "
                f"Intervals have direct probability interpretation: "
                f"{int(probability*100)}% posterior probability the true value lies within."
            )

            return {
                "success": True,
                "credible_intervals": intervals,
                "posterior_mean": {
                    param: float(row["mean"]) for param, row in summary.iterrows()
                },
                "interval_width": widths,
                "probability": probability,
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Credible interval computation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Credible interval computation failed: {str(e)}",
            }

    # =========================================================================
    # Tool 4: Compare Bayesian Models
    # =========================================================================

    async def compare_bayesian_models(
        self,
        models: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compare multiple Bayesian models using WAIC and LOO.

        Uses Watanabe-Akaike Information Criterion (WAIC) and Leave-One-Out
        Cross-Validation (LOO) to compare model fit and predictive performance.
        Lower values indicate better models.

        Args:
            models: List of model dicts, each with:
                - name: Model name
                - data: Training data
                - formula: Model formula
                - (optional) draws, tune, chains

        Returns:
            Dictionary with:
            - success: True if comparison succeeded
            - comparison_table: DataFrame-like comparison of models
            - best_model: Name of best model by WAIC
            - waic_scores: Dict of WAIC for each model
            - loo_scores: Dict of LOO for each model
            - interpretation: Comparison summary
            - error: Error message if failed

        Example:
            >>> models = [
            ...     {"name": "linear", "data": data, "formula": "points ~ minutes"},
            ...     {"name": "quadratic", "data": data, "formula": "points ~ minutes + I(minutes**2)"}
            ... ]
            >>> result = await compare_bayesian_models(models=models)
            >>> result['best_model']
            "quadratic"  # Lower WAIC

        NBA Use Cases:
            - Compare different player performance model specifications
            - Select best predictive model for win probability
            - Evaluate feature engineering choices
        """
        try:
            from mcp_server.bayesian import BayesianAnalyzer

            if len(models) < 2:
                return {"success": False, "error": "Need at least 2 models to compare"}

            # Fit all models and collect results
            fitted_models = {}
            waic_scores = {}
            loo_scores = {}

            for model_spec in models:
                name = model_spec["name"]
                data = pd.DataFrame(model_spec["data"])
                formula = model_spec["formula"]

                target, _ = formula.split("~")
                target = target.strip()

                analyzer = BayesianAnalyzer(data=data, target_col=target)

                # Fit model
                result = analyzer.sample_posterior(
                    formula=formula,
                    draws=model_spec.get("draws", 2000),
                    tune=model_spec.get("tune", 1000),
                    chains=model_spec.get("chains", 4),
                )

                fitted_models[name] = result
                waic_scores[name] = analyzer.waic(result)
                loo_scores[name] = analyzer.loo(result)

            # Find best model
            best_waic_model = min(waic_scores, key=waic_scores.get)
            best_loo_model = min(loo_scores, key=loo_scores.get)

            # Create comparison table
            comparison = []
            for name in fitted_models.keys():
                comparison.append({
                    "model": name,
                    "waic": round(waic_scores[name], 2),
                    "loo": round(loo_scores[name], 2),
                    "best_waic": name == best_waic_model,
                    "best_loo": name == best_loo_model,
                })

            interpretation = (
                f"Compared {len(models)} Bayesian models. "
                f"Best by WAIC: {best_waic_model} ({waic_scores[best_waic_model]:.2f}). "
                f"Best by LOO: {best_loo_model} ({loo_scores[best_loo_model]:.2f})."
            )

            return {
                "success": True,
                "comparison_table": comparison,
                "best_model_waic": best_waic_model,
                "best_model_loo": best_loo_model,
                "waic_scores": {k: float(v) for k, v in waic_scores.items()},
                "loo_scores": {k: float(v) for k, v in loo_scores.items()},
                "interpretation": interpretation,
                "n_models": len(models),
            }

        except Exception as e:
            self.logger.error(f"Model comparison failed: {str(e)}")
            return {"success": False, "error": f"Model comparison failed: {str(e)}"}

    # =========================================================================
    # Tool 5: Posterior Summary
    # =========================================================================

    async def posterior_summary(
        self,
        data: List[Dict[str, Any]],
        formula: str,
        target_column: str = "value",
    ) -> Dict[str, Any]:
        """
        Generate comprehensive summary of posterior distributions.

        Provides mean, std dev, HDI intervals, and diagnostic statistics
        for all model parameters from Bayesian inference.

        Args:
            data: List of dictionaries with observations
            formula: Model formula
            target_column: Dependent variable

        Returns:
            Dictionary with:
            - success: True if summary generated
            - parameters: Dict of parameter summaries
            - n_parameters: Number of parameters
            - interpretation: Summary text
            - error: Error message if failed

        Example:
            >>> result = await posterior_summary(
            ...     data=data,
            ...     formula="points ~ minutes + age"
            ... )
            >>> result['parameters']['minutes']
            {'mean': 0.72, 'std': 0.05, 'hdi_lower': 0.63, 'hdi_upper': 0.81}

        NBA Use Cases:
            - Summarize player effect estimates
            - Report team-level parameter distributions
            - Document model coefficients for publication
        """
        try:
            from mcp_server.bayesian import BayesianAnalyzer

            df = pd.DataFrame(data)
            target, _ = formula.split("~")
            target = target.strip()

            analyzer = BayesianAnalyzer(data=df, target_col=target)
            result = analyzer.sample_posterior(formula=formula)
            summary = analyzer.posterior_summary(result)

            parameters = {}
            for param, row in summary.iterrows():
                parameters[param] = {
                    "mean": float(row["mean"]),
                    "std": float(row["sd"]),
                    "hdi_lower": float(row["hdi_3%"]),
                    "hdi_upper": float(row["hdi_97%"]),
                }

            interpretation = (
                f"Posterior summary for {len(parameters)} parameters. "
                f"All estimates include 95% HDI intervals."
            )

            return {
                "success": True,
                "parameters": parameters,
                "n_parameters": len(parameters),
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Posterior summary failed: {str(e)}")
            return {"success": False, "error": f"Posterior summary failed: {str(e)}"}

    # =========================================================================
    # Tool 6: Bayesian Player Scoring Model
    # =========================================================================

    async def bayesian_player_model(
        self,
        player_data: List[Dict[str, Any]],
        player_id_column: str = "player_id",
        points_column: str = "points",
        predictors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        NBA-specific Bayesian hierarchical model for player scoring.

        Specialized model for analyzing player scoring patterns with
        partial pooling across players. Estimates player-specific effects
        with shrinkage toward league average.

        Args:
            player_data: List of player game observations
            player_id_column: Column identifying players
            points_column: Points scored column
            predictors: List of predictor columns (default: ['minutes', 'usage_rate'])

        Returns:
            Dictionary with:
            - success: True if model fit succeeded
            - player_effects: Dict of player-specific scoring rates
            - global_effects: League-average effects
            - predictions: Predicted points for each observation
            - interpretation: Model summary
            - error: Error message if failed

        Example:
            >>> result = await bayesian_player_model(
            ...     player_data=games,
            ...     player_id_column="player_id",
            ...     points_column="points"
            ... )
            >>> result['player_effects']['LeBron']
            {'baseline': 8.2, 'minutes_effect': 0.58}

        NBA Use Cases:
            - Predict player scoring in different minute allocations
            - Identify over/under-performing players vs expectations
            - Adjust for strength of schedule with team effects
        """
        try:
            from mcp_server.bayesian import BayesianAnalyzer

            df = pd.DataFrame(player_data)

            # Default predictors if not provided
            if predictors is None:
                predictors = ["minutes"]
                if "usage_rate" in df.columns:
                    predictors.append("usage_rate")

            # Validate columns
            required = [player_id_column, points_column] + predictors
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            analyzer = BayesianAnalyzer(
                data=df,
                target_col=points_column,
                group_col=player_id_column
            )

            # Fit player scoring model
            formula = f"{points_column} ~ {' + '.join(predictors)}"
            result = analyzer.player_scoring_model(
                player_col=player_id_column,
                predictors=predictors
            )

            summary = analyzer.posterior_summary(result)

            # Extract player effects
            player_effects = {}
            global_effects = {}

            for param, row in summary.iterrows():
                if player_id_column in param:
                    player_name = param.split("[")[1].split("]")[0]
                    player_effects[player_name] = {
                        "effect": float(row["mean"]),
                        "std": float(row["sd"]),
                    }
                else:
                    global_effects[param] = {
                        "effect": float(row["mean"]),
                        "std": float(row["sd"]),
                    }

            interpretation = (
                f"Bayesian player scoring model fit for {len(player_effects)} players. "
                f"Hierarchical structure provides shrinkage toward league average."
            )

            return {
                "success": True,
                "player_effects": player_effects,
                "global_effects": global_effects,
                "n_players": len(player_effects),
                "n_observations": len(df),
                "predictors": predictors,
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Bayesian player model failed: {str(e)}")
            return {
                "success": False,
                "error": f"Bayesian player model failed: {str(e)}",
            }

    # =========================================================================
    # Tool 7: Bayesian Win Probability
    # =========================================================================

    async def bayesian_win_probability(
        self,
        game_data: List[Dict[str, Any]],
        team_id_column: str = "team_id",
        won_column: str = "won",
        predictors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Bayesian model for NBA win probability estimation.

        Uses Bayesian logistic regression with hierarchical team effects
        to estimate win probabilities. Provides uncertainty quantification
        for predictions.

        Args:
            game_data: List of game observations with outcomes
            team_id_column: Column identifying teams
            won_column: Binary win/loss column (1/0)
            predictors: Predictor columns (default: ['point_diff', 'home'])

        Returns:
            Dictionary with:
            - success: True if model fit succeeded
            - team_strength: Dict of team-specific win probability adjustments
            - predictor_effects: Effects of each predictor on win probability
            - predictions: Win probability for each game
            - calibration: Model calibration metrics
            - interpretation: Model summary
            - error: Error message if failed

        Example:
            >>> result = await bayesian_win_probability(
            ...     game_data=games,
            ...     team_id_column="team_id",
            ...     predictors=['point_diff', 'home_court']
            ... )
            >>> result['team_strength']['Lakers']
            {'baseline_win_prob': 0.62, 'std': 0.08}

        NBA Use Cases:
            - Real-time win probability during games
            - Season win total predictions with uncertainty
            - Playoff probability estimation
        """
        try:
            from mcp_server.bayesian import BayesianAnalyzer

            df = pd.DataFrame(game_data)

            # Default predictors
            if predictors is None:
                predictors = []
                if "point_diff" in df.columns:
                    predictors.append("point_diff")
                if "home" in df.columns:
                    predictors.append("home")

            # Validate columns
            required = [team_id_column, won_column] + predictors
            missing = [c for c in required if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Missing columns: {missing}"}

            analyzer = BayesianAnalyzer(
                data=df,
                target_col=won_column,
                group_col=team_id_column
            )

            # Fit win probability model
            result = analyzer.win_probability_model(
                team_col=team_id_column,
                outcome_col=won_column,
                predictors=predictors
            )

            summary = analyzer.posterior_summary(result)

            # Extract team effects
            team_strength = {}
            predictor_effects = {}

            for param, row in summary.iterrows():
                if team_id_column in param:
                    team_name = param.split("[")[1].split("]")[0]
                    team_strength[team_name] = {
                        "effect": float(row["mean"]),
                        "std": float(row["sd"]),
                    }
                else:
                    predictor_effects[param] = {
                        "effect": float(row["mean"]),
                        "std": float(row["sd"]),
                    }

            interpretation = (
                f"Bayesian win probability model for {len(team_strength)} teams. "
                f"Hierarchical logistic regression with {len(predictors)} predictors."
            )

            return {
                "success": True,
                "team_strength": team_strength,
                "predictor_effects": predictor_effects,
                "n_teams": len(team_strength),
                "n_games": len(df),
                "predictors": predictors,
                "interpretation": interpretation,
            }

        except Exception as e:
            self.logger.error(f"Bayesian win probability model failed: {str(e)}")
            return {
                "success": False,
                "error": f"Bayesian win probability model failed: {str(e)}",
            }
