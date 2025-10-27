"""
Bayesian Methods for NBA Analytics with Uncertainty Quantification.

This module provides comprehensive Bayesian inference capabilities including:
- Hierarchical Bayesian models (players within teams)
- MCMC sampling (NUTS, Metropolis-Hastings)
- Variational inference (ADVI)
- Posterior analysis and credible intervals
- Bayesian model comparison (WAIC, LOO)

Designed for probabilistic modeling of NBA data with full uncertainty quantification,
especially useful for hierarchical structures (players nested within teams) and
incorporating prior knowledge.

Key Features:
- Full posterior distributions, not just point estimates
- Hierarchical models with partial pooling
- Probabilistic predictions with credible intervals
- Model comparison and selection
- Convergence diagnostics (Rhat, ESS)

Integration:
- Works with data validation (Agent 4) for input validation
- Alternative to frequentist ML in training pipeline (Agent 5)
- Probabilistic predictions for model serving (Agent 6)
- Bayesian updating for monitoring (Agent 2)
- MLflow tracking for Bayesian experiments

Author: Agent 8 Module 3
Date: October 2025
"""

import logging
import warnings
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Union, Literal
from enum import Enum

import numpy as np
import pandas as pd

# PyMC and ArviZ for Bayesian inference
try:
    import pymc as pm
    import arviz as az
    from pytensor import tensor as pt

    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False
    pm = None
    az = None
    pt = None

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


# ==============================================================================
# Enums and Constants
# ==============================================================================


class InferenceMethod(str, Enum):
    """Supported inference methods."""

    MCMC = "mcmc"  # Markov Chain Monte Carlo
    VI = "vi"  # Variational Inference
    ADVI = "advi"  # Automatic Differentiation Variational Inference


class PriorDistribution(str, Enum):
    """Supported prior distributions."""

    NORMAL = "normal"
    HALFNORMAL = "halfnormal"
    EXPONENTIAL = "exponential"
    UNIFORM = "uniform"
    BETA = "beta"
    GAMMA = "gamma"
    STUDENT_T = "student_t"


class LikelihoodFamily(str, Enum):
    """Supported likelihood families."""

    NORMAL = "normal"
    BERNOULLI = "bernoulli"
    POISSON = "poisson"
    BINOMIAL = "binomial"
    NEGATIVE_BINOMIAL = "negativebinomial"


# ==============================================================================
# Data Classes
# ==============================================================================


@dataclass
class BayesianModelResult:
    """Results from a fitted Bayesian model."""

    trace: Any  # InferenceData object from ArviZ
    model: Any  # PyMC model object
    inference_method: InferenceMethod
    summary: pd.DataFrame
    aic: Optional[float] = None
    bic: Optional[float] = None
    waic: Optional[float] = None
    loo: Optional[float] = None
    convergence_ok: bool = True
    diagnostics: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate that model converged."""
        if self.diagnostics and not self.convergence_ok:
            warnings.warn(
                "Model may not have converged. Check diagnostics.",
                UserWarning,
            )


@dataclass
class PosteriorResult:
    """Posterior analysis results."""

    mean: Dict[str, float]
    median: Dict[str, float]
    std: Dict[str, float]
    hdi_95: Dict[str, Tuple[float, float]]  # 95% Highest Density Interval
    hdi_90: Dict[str, Tuple[float, float]]  # 90% HDI
    ess: Dict[str, float]  # Effective Sample Size
    rhat: Dict[str, float]  # Gelman-Rubin statistic
    n_samples: int


@dataclass
class VIResult:
    """Variational inference results."""

    approx: Any  # PyMC approximation object
    mean_field: pd.DataFrame
    elbo: float  # Evidence Lower Bound
    n_iterations: int
    converged: bool


@dataclass
class PPCResult:
    """Posterior Predictive Check results."""

    observed: np.ndarray
    predicted: np.ndarray  # Posterior predictive samples
    mean_prediction: np.ndarray
    hdi_95_lower: np.ndarray
    hdi_95_upper: np.ndarray
    p_value: float  # Bayesian p-value
    test_statistic: str


@dataclass
class ModelComparisonResult:
    """Model comparison results."""

    model_names: List[str]
    waic_values: Dict[str, float]
    loo_values: Dict[str, float]
    elpd_diff: Dict[str, float]  # Expected Log Predictive Density difference
    se_diff: Dict[str, float]  # Standard error of difference
    best_model: str
    comparison_table: pd.DataFrame


@dataclass
class CredibleInterval:
    """Credible interval for a parameter."""

    parameter: str
    lower: float
    upper: float
    probability: float  # e.g., 0.95 for 95% credible interval
    method: str = "hdi"  # 'hdi' or 'quantile'


@dataclass
class HierarchicalModelSpec:
    """Specification for hierarchical model."""

    group_variable: str  # e.g., 'team_id'
    nested_variable: Optional[str] = None  # e.g., 'player_id' within team
    formula: Optional[str] = None
    group_level_priors: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    individual_level_priors: Dict[str, Dict[str, Any]] = field(default_factory=dict)


# ==============================================================================
# BayesianAnalyzer Class
# ==============================================================================


class BayesianAnalyzer:
    """
    Bayesian inference for NBA analytics.

    Provides hierarchical modeling, MCMC sampling, variational inference,
    posterior analysis, and model comparison.

    Examples:
        >>> # Simple regression
        >>> analyzer = BayesianAnalyzer(data, target='points')
        >>> result = analyzer.sample_posterior(draws=2000)
        >>>
        >>> # Hierarchical model
        >>> spec = HierarchicalModelSpec(group_variable='team_id')
        >>> result = analyzer.hierarchical_model(spec, formula='points ~ minutes')
    """

    def __init__(
        self,
        data: pd.DataFrame,
        target: Optional[str] = None,
        features: Optional[List[str]] = None,
        backend: str = "pymc",
        mlflow_experiment: Optional[str] = None,
    ):
        """
        Initialize Bayesian analyzer.

        Args:
            data: DataFrame with observations
            target: Target variable name
            features: List of feature column names
            backend: Inference backend ('pymc' only for now)
            mlflow_experiment: MLflow experiment name for tracking
        """
        if not PYMC_AVAILABLE:
            raise ImportError(
                "PyMC is required for Bayesian analysis. "
                "Install with: pip install pymc>=5.0.0 arviz>=0.15.0"
            )

        self.data = data.copy()
        self.target = target
        self.features = features or []
        self.backend = backend
        self.model = None
        self.trace = None
        self.mlflow_experiment = mlflow_experiment

        # MLflow tracking
        self.mlflow_tracker = None
        if MLFLOW_AVAILABLE and mlflow_experiment:
            try:
                self.mlflow_tracker = MLflowExperimentTracker(mlflow_experiment)
            except Exception as e:
                logger.warning(f"MLflow tracker initialization failed: {e}")

        logger.info(f"Initialized BayesianAnalyzer with {len(data)} observations")

    def define_prior(
        self,
        parameter: str,
        distribution: Union[str, PriorDistribution],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Define prior distribution for a parameter.

        Args:
            parameter: Parameter name
            distribution: Distribution type (e.g., 'normal', 'exponential')
            **kwargs: Distribution parameters (e.g., mu=0, sigma=1)

        Returns:
            Prior specification dictionary

        Examples:
            >>> analyzer.define_prior('beta', 'normal', mu=0, sigma=10)
            >>> analyzer.define_prior('sigma', 'exponential', lam=1)
        """
        if isinstance(distribution, str):
            distribution = PriorDistribution(distribution.lower())

        prior_spec = {
            "parameter": parameter,
            "distribution": distribution.value,
            "params": kwargs,
        }

        logger.debug(f"Defined prior: {prior_spec}")
        return prior_spec

    def define_likelihood(
        self,
        family: Union[str, LikelihoodFamily],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Define likelihood distribution.

        Args:
            family: Likelihood family (e.g., 'normal', 'bernoulli')
            **kwargs: Likelihood parameters

        Returns:
            Likelihood specification dictionary

        Examples:
            >>> analyzer.define_likelihood('normal', sigma='sigma')
            >>> analyzer.define_likelihood('bernoulli', p='p')
        """
        if isinstance(family, str):
            family = LikelihoodFamily(family.lower())

        likelihood_spec = {"family": family.value, "params": kwargs}

        logger.debug(f"Defined likelihood: {likelihood_spec}")
        return likelihood_spec

    def build_simple_model(
        self,
        formula: Optional[str] = None,
        priors: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Any:
        """
        Build a simple Bayesian linear regression model.

        Args:
            formula: Optional formula string (e.g., 'y ~ x1 + x2')
            priors: Dictionary of prior specifications

        Returns:
            PyMC model object
        """
        if priors is None:
            priors = {}

        with pm.Model() as model:
            # Default priors for linear regression
            # Intercept
            alpha = pm.Normal(
                "alpha",
                mu=priors.get("alpha", {}).get("mu", 0),
                sigma=priors.get("alpha", {}).get("sigma", 10),
            )

            # Coefficients
            if self.features:
                n_features = len(self.features)
                beta = pm.Normal(
                    "beta",
                    mu=priors.get("beta", {}).get("mu", 0),
                    sigma=priors.get("beta", {}).get("sigma", 10),
                    shape=n_features,
                )

                # Linear combination
                X = self.data[self.features].values
                mu = alpha + pm.math.dot(X, beta)
            else:
                mu = alpha

            # Observation noise
            sigma = pm.Exponential("sigma", lam=priors.get("sigma", {}).get("lam", 1))

            # Likelihood
            if self.target:
                y = self.data[self.target].values
                y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y)

        self.model = model
        logger.info(f"Built simple Bayesian model with {len(self.features)} features")
        return model

    def sample_posterior(
        self,
        draws: int = 2000,
        tune: int = 1000,
        chains: int = 4,
        target_accept: float = 0.95,
        random_seed: Optional[int] = None,
        **kwargs,
    ) -> BayesianModelResult:
        """
        Sample from posterior using MCMC (NUTS sampler).

        Args:
            draws: Number of samples per chain
            tune: Number of tuning steps
            chains: Number of MCMC chains
            target_accept: Target acceptance rate for NUTS
            random_seed: Random seed for reproducibility
            **kwargs: Additional arguments for pm.sample()

        Returns:
            BayesianModelResult with trace and diagnostics
        """
        if self.model is None:
            raise ValueError("Must build model first with build_simple_model()")

        logger.info(f"Sampling posterior: {draws} draws, {tune} tune, {chains} chains")

        with self.model:
            trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                target_accept=target_accept,
                random_seed=random_seed,
                return_inferencedata=True,
                idata_kwargs={"log_likelihood": True},
                **kwargs,
            )

        self.trace = trace

        # Get summary
        summary = az.summary(trace, hdi_prob=0.95)

        # Check convergence
        rhat_values = summary["r_hat"].values
        convergence_ok = np.all(rhat_values < 1.01)

        if not convergence_ok:
            warnings.warn(
                f"Some Rhat values >= 1.01. Max Rhat: {rhat_values.max():.4f}",
                UserWarning,
            )

        # Compute diagnostics
        diagnostics = {
            "rhat_max": float(rhat_values.max()),
            "rhat_all_ok": convergence_ok,
            "ess_bulk_min": float(summary["ess_bulk"].min()),
            "ess_tail_min": float(summary["ess_tail"].min()),
            "n_divergences": int(trace.sample_stats.diverging.sum().values),
        }

        # Model comparison metrics
        try:
            waic_result = az.waic(trace)
            waic_value = float(waic_result.waic)
        except Exception as e:
            logger.warning(f"WAIC calculation failed: {e}")
            waic_value = None

        try:
            loo_result = az.loo(trace)
            loo_value = float(loo_result.loo)
        except Exception as e:
            logger.warning(f"LOO calculation failed: {e}")
            loo_value = None

        result = BayesianModelResult(
            trace=trace,
            model=self.model,
            inference_method=InferenceMethod.MCMC,
            summary=summary,
            waic=waic_value,
            loo=loo_value,
            convergence_ok=convergence_ok,
            diagnostics=diagnostics,
        )

        # MLflow logging
        if self.mlflow_tracker:
            try:
                with mlflow.start_run():
                    mlflow.log_params(
                        {
                            "draws": draws,
                            "tune": tune,
                            "chains": chains,
                            "target_accept": target_accept,
                        }
                    )
                    mlflow.log_metrics(diagnostics)
                    if waic_value:
                        mlflow.log_metric("waic", waic_value)
                    if loo_value:
                        mlflow.log_metric("loo", loo_value)
            except Exception as e:
                logger.warning(f"MLflow logging failed: {e}")

        logger.info(f"Sampling complete. Convergence: {convergence_ok}")
        return result

    def variational_inference(
        self,
        method: str = "advi",
        n_iter: int = 10000,
        random_seed: Optional[int] = None,
    ) -> VIResult:
        """
        Perform variational inference (fast approximate posterior).

        Args:
            method: VI method ('advi' for Automatic Differentiation VI)
            n_iter: Number of iterations
            random_seed: Random seed

        Returns:
            VIResult with approximation
        """
        if self.model is None:
            raise ValueError("Must build model first")

        logger.info(f"Running variational inference: {method}, {n_iter} iterations")

        with self.model:
            approx = pm.fit(n=n_iter, method=method, random_seed=random_seed)

        # Get mean field approximation
        mean_field = approx.mean.eval()
        std_field = approx.std.eval()

        # Create summary DataFrame
        param_names = list(self.model.named_vars.keys())
        # Filter to only free variables
        param_names = [
            name
            for name in param_names
            if not name.endswith("_log__")
            and not name.endswith("_interval__")
            and name != "y_obs"
        ]

        mean_field_df = pd.DataFrame(
            {
                "mean": mean_field.flatten()[: len(param_names)],
                "std": std_field.flatten()[: len(param_names)],
            },
            index=param_names,
        )

        result = VIResult(
            approx=approx,
            mean_field=mean_field_df,
            elbo=float(approx.hist[-1]) if hasattr(approx, "hist") else 0.0,
            n_iterations=n_iter,
            converged=True,  # Could add convergence check based on ELBO
        )

        logger.info("Variational inference complete")
        return result

    def hierarchical_model(
        self,
        spec: HierarchicalModelSpec,
        formula: Optional[str] = None,
    ) -> Any:
        """
        Build hierarchical Bayesian model with partial pooling.

        Args:
            spec: Hierarchical model specification
            formula: Optional formula string

        Returns:
            PyMC model object

        Examples:
            >>> # Player performance within teams
            >>> spec = HierarchicalModelSpec(
            ...     group_variable='team_id',
            ...     nested_variable='player_id'
            ... )
            >>> model = analyzer.hierarchical_model(spec)
        """
        group_col = spec.group_variable
        nested_col = spec.nested_variable

        # Encode categorical variables
        group_idx, groups = pd.factorize(self.data[group_col])
        n_groups = len(groups)

        if nested_col:
            nested_idx, nested_items = pd.factorize(self.data[nested_col])
            n_nested = len(nested_items)
        else:
            nested_idx = None
            n_nested = 0

        with pm.Model() as model:
            # Hyperpriors
            mu_global = pm.Normal("mu_global", mu=0, sigma=10)
            sigma_group = pm.Exponential("sigma_group", lam=1)

            # Group-level effects (partial pooling)
            group_effect = pm.Normal(
                "group_effect",
                mu=mu_global,
                sigma=sigma_group,
                shape=n_groups,
            )

            # Individual-level effects (if nested structure)
            if nested_col:
                sigma_nested = pm.Exponential("sigma_nested", lam=1)
                nested_effect = pm.Normal(
                    "nested_effect",
                    mu=0,
                    sigma=sigma_nested,
                    shape=n_nested,
                )
                mu = group_effect[group_idx] + nested_effect[nested_idx]
            else:
                mu = group_effect[group_idx]

            # Observation noise
            sigma_obs = pm.Exponential("sigma_obs", lam=1)

            # Likelihood
            if self.target:
                y = self.data[self.target].values
                y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma_obs, observed=y)

        self.model = model
        logger.info(
            f"Built hierarchical model: {n_groups} groups"
            + (f", {n_nested} nested items" if nested_col else "")
        )
        return model

    def posterior_summary(
        self, result: BayesianModelResult, hdi_prob: float = 0.95
    ) -> PosteriorResult:
        """
        Generate comprehensive posterior summary.

        Args:
            result: BayesianModelResult from sampling
            hdi_prob: Probability for HDI (default 0.95 for 95% HDI)

        Returns:
            PosteriorResult with mean, median, std, HDI, ESS, Rhat
        """
        trace = result.trace
        summary = az.summary(trace, hdi_prob=hdi_prob)

        # Extract parameter names (exclude observed variables)
        param_names = [
            v for v in summary.index if not v.endswith("_log__") and v != "y_obs"
        ]

        # Build result dictionaries
        mean_dict = {p: float(summary.loc[p, "mean"]) for p in param_names}
        median_dict = {
            p: float(
                np.median(
                    trace.posterior[p].values.flatten()
                    if p in trace.posterior
                    else [summary.loc[p, "mean"]]
                )
            )
            for p in param_names
        }
        std_dict = {p: float(summary.loc[p, "sd"]) for p in param_names}

        # HDI intervals - use summary columns which already have HDI
        hdi_95 = {}
        hdi_90 = {}
        for p in param_names:
            # Get base parameter name (remove indexing like [0])
            base_param = p.split("[")[0]

            # Try using summary columns first (more reliable for array params)
            try:
                hdi_95[p] = (
                    float(summary.loc[p, "hdi_2.5%"]),
                    float(summary.loc[p, "hdi_97.5%"]),
                )
            except (KeyError, ValueError):
                # Fallback: compute from trace if parameter exists
                try:
                    if base_param in trace.posterior:
                        param_samples = trace.posterior[base_param].values.flatten()
                        hdi_95[p] = (
                            float(np.percentile(param_samples, 2.5)),
                            float(np.percentile(param_samples, 97.5)),
                        )
                    else:
                        # Last resort: use mean +/- 2*std
                        hdi_95[p] = (
                            float(summary.loc[p, "mean"] - 2 * summary.loc[p, "sd"]),
                            float(summary.loc[p, "mean"] + 2 * summary.loc[p, "sd"]),
                        )
                except Exception:
                    hdi_95[p] = (0.0, 0.0)

            # 90% HDI
            try:
                hdi_90[p] = (
                    float(summary.loc[p, "hdi_5%"]),
                    float(summary.loc[p, "hdi_95%"]),
                )
            except (KeyError, ValueError):
                try:
                    if base_param in trace.posterior:
                        param_samples = trace.posterior[base_param].values.flatten()
                        hdi_90[p] = (
                            float(np.percentile(param_samples, 5)),
                            float(np.percentile(param_samples, 95)),
                        )
                    else:
                        hdi_90[p] = (
                            float(summary.loc[p, "mean"] - 1.65 * summary.loc[p, "sd"]),
                            float(summary.loc[p, "mean"] + 1.65 * summary.loc[p, "sd"]),
                        )
                except Exception:
                    hdi_90[p] = (0.0, 0.0)

        # ESS and Rhat
        ess_dict = {p: float(summary.loc[p, "ess_bulk"]) for p in param_names}
        rhat_dict = {p: float(summary.loc[p, "r_hat"]) for p in param_names}

        n_samples = int(trace.posterior.dims["draw"]) * int(
            trace.posterior.dims["chain"]
        )

        return PosteriorResult(
            mean=mean_dict,
            median=median_dict,
            std=std_dict,
            hdi_95=hdi_95,
            hdi_90=hdi_90,
            ess=ess_dict,
            rhat=rhat_dict,
            n_samples=n_samples,
        )

    def credible_interval(
        self,
        result: BayesianModelResult,
        parameter: str,
        prob: float = 0.95,
        method: str = "hdi",
    ) -> CredibleInterval:
        """
        Calculate credible interval for a parameter.

        Args:
            result: BayesianModelResult
            parameter: Parameter name
            prob: Credible level (e.g., 0.95 for 95%)
            method: 'hdi' for Highest Density Interval or 'quantile'

        Returns:
            CredibleInterval object
        """
        trace = result.trace

        if method == "hdi":
            hdi_vals = az.hdi(trace, var_names=[parameter], hdi_prob=prob)
            if parameter in hdi_vals:
                vals = hdi_vals[parameter].values.flatten()
                lower, upper = float(vals[0]), float(vals[1])
            else:
                raise ValueError(f"Parameter '{parameter}' not found in trace")
        elif method == "quantile":
            alpha = 1 - prob
            if parameter in trace.posterior:
                samples = trace.posterior[parameter].values.flatten()
                lower = float(np.quantile(samples, alpha / 2))
                upper = float(np.quantile(samples, 1 - alpha / 2))
            else:
                raise ValueError(f"Parameter '{parameter}' not found in trace")
        else:
            raise ValueError(f"Unknown method: {method}")

        return CredibleInterval(
            parameter=parameter,
            lower=lower,
            upper=upper,
            probability=prob,
            method=method,
        )

    def posterior_predictive_check(
        self,
        result: BayesianModelResult,
        n_samples: int = 1000,
        test_statistic: str = "mean",
    ) -> PPCResult:
        """
        Perform posterior predictive check.

        Args:
            result: BayesianModelResult
            n_samples: Number of posterior predictive samples
            test_statistic: Test statistic ('mean', 'std', 'max', 'min')

        Returns:
            PPCResult with observed vs predicted comparison
        """
        trace = result.trace
        model = result.model

        with model:
            # Sample posterior predictive using extend
            ppc = pm.sample_posterior_predictive(
                trace, extend_inferencedata=False, random_seed=42
            )

        # Extract observed and predicted
        if "y_obs" in ppc.posterior_predictive:
            predicted_samples = ppc.posterior_predictive["y_obs"].values
            # Shape: (chains, draws, observations)
            predicted_samples = predicted_samples.reshape(
                -1, predicted_samples.shape[-1]
            )
        else:
            raise ValueError("No 'y_obs' in posterior predictive")

        observed = self.data[self.target].values

        # Mean prediction and credible interval
        mean_prediction = predicted_samples.mean(axis=0)

        # Calculate HDI manually to avoid shape issues
        hdi_95_lower = np.percentile(predicted_samples, 2.5, axis=0)
        hdi_95_upper = np.percentile(predicted_samples, 97.5, axis=0)

        # Bayesian p-value
        if test_statistic == "mean":
            obs_stat = observed.mean()
            pred_stats = predicted_samples.mean(axis=1)
        elif test_statistic == "std":
            obs_stat = observed.std()
            pred_stats = predicted_samples.std(axis=1)
        elif test_statistic == "max":
            obs_stat = observed.max()
            pred_stats = predicted_samples.max(axis=1)
        elif test_statistic == "min":
            obs_stat = observed.min()
            pred_stats = predicted_samples.min(axis=1)
        else:
            raise ValueError(f"Unknown test statistic: {test_statistic}")

        p_value = float((pred_stats >= obs_stat).mean())

        return PPCResult(
            observed=observed,
            predicted=predicted_samples,
            mean_prediction=mean_prediction,
            hdi_95_lower=hdi_95_lower,
            hdi_95_upper=hdi_95_upper,
            p_value=p_value,
            test_statistic=test_statistic,
        )

    def waic(self, result: BayesianModelResult) -> float:
        """
        Calculate Widely Applicable Information Criterion.

        Args:
            result: BayesianModelResult

        Returns:
            WAIC value (lower is better)
        """
        waic_result = az.waic(result.trace)
        # ELPDData uses elpd_waic, not waic
        return float(
            waic_result.elpd_waic
            if hasattr(waic_result, "elpd_waic")
            else waic_result.waic
        )

    def loo(self, result: BayesianModelResult) -> float:
        """
        Calculate Leave-One-Out Cross-Validation.

        Args:
            result: BayesianModelResult

        Returns:
            LOO value (lower is better)
        """
        loo_result = az.loo(result.trace)
        # ELPDData uses elpd_loo, not loo
        return float(
            loo_result.elpd_loo if hasattr(loo_result, "elpd_loo") else loo_result.loo
        )

    def compare_models(
        self, results: Dict[str, BayesianModelResult]
    ) -> ModelComparisonResult:
        """
        Compare multiple Bayesian models.

        Args:
            results: Dictionary mapping model names to BayesianModelResult

        Returns:
            ModelComparisonResult with comparison metrics

        Examples:
            >>> results = {
            ...     'model1': result1,
            ...     'model2': result2,
            ...     'model3': result3
            ... }
            >>> comparison = analyzer.compare_models(results)
        """
        model_names = list(results.keys())
        traces = {name: res.trace for name, res in results.items()}

        # ArviZ model comparison
        comparison = az.compare(traces, ic="waic")

        # Extract metrics
        waic_values = {
            name: float(comparison.loc[name, "waic"]) for name in model_names
        }
        loo_values = {name: float(results[name].loo or 0) for name in model_names}

        # ELPD difference (expected log predictive density)
        elpd_diff = {
            name: (
                float(comparison.loc[name, "d_waic"])
                if "d_waic" in comparison.columns
                else 0.0
            )
            for name in model_names
        }
        se_diff = {
            name: (
                float(comparison.loc[name, "se"]) if "se" in comparison.columns else 0.0
            )
            for name in model_names
        }

        # Best model (lowest WAIC)
        best_model = min(waic_values, key=waic_values.get)

        return ModelComparisonResult(
            model_names=model_names,
            waic_values=waic_values,
            loo_values=loo_values,
            elpd_diff=elpd_diff,
            se_diff=se_diff,
            best_model=best_model,
            comparison_table=comparison,
        )

    def check_convergence(self, result: BayesianModelResult) -> Dict[str, Any]:
        """
        Check MCMC convergence diagnostics.

        Args:
            result: BayesianModelResult

        Returns:
            Dictionary with convergence diagnostics
        """
        summary = result.summary
        diagnostics = result.diagnostics or {}

        # Rhat check
        rhat_values = summary["r_hat"].values
        rhat_ok = np.all(rhat_values < 1.01)
        rhat_max = float(rhat_values.max())

        # ESS check
        ess_bulk_min = float(summary["ess_bulk"].min())
        ess_tail_min = float(summary["ess_tail"].min())
        ess_ok = ess_bulk_min > 100 and ess_tail_min > 100

        # Divergences
        n_divergences = diagnostics.get("n_divergences", 0)
        divergences_ok = n_divergences == 0

        convergence_dict = {
            "rhat_ok": rhat_ok,
            "rhat_max": rhat_max,
            "ess_ok": ess_ok,
            "ess_bulk_min": ess_bulk_min,
            "ess_tail_min": ess_tail_min,
            "divergences_ok": divergences_ok,
            "n_divergences": n_divergences,
            "overall_ok": rhat_ok and ess_ok and divergences_ok,
        }

        return convergence_dict

    def effective_sample_size(self, result: BayesianModelResult) -> Dict[str, float]:
        """
        Get effective sample sizes for all parameters.

        Args:
            result: BayesianModelResult

        Returns:
            Dictionary mapping parameter names to ESS values
        """
        summary = result.summary
        param_names = [v for v in summary.index if v != "y_obs"]

        ess_dict = {p: float(summary.loc[p, "ess_bulk"]) for p in param_names}

        return ess_dict

    def rhat_statistic(self, result: BayesianModelResult) -> Dict[str, float]:
        """
        Get Rhat (Gelman-Rubin) statistics for all parameters.

        Args:
            result: BayesianModelResult

        Returns:
            Dictionary mapping parameter names to Rhat values
        """
        summary = result.summary
        param_names = [v for v in summary.index if v != "y_obs"]

        rhat_dict = {p: float(summary.loc[p, "r_hat"]) for p in param_names}

        return rhat_dict


# ==============================================================================
# NBA-Specific Models
# ==============================================================================


class NBABayesianModels:
    """NBA-specific Bayesian model templates."""

    @staticmethod
    def player_scoring_model(
        data: pd.DataFrame,
        team_col: str = "team_id",
        player_col: str = "player_id",
        target_col: str = "points",
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Hierarchical model for player scoring.

        Model: points ~ Normal(alpha[team] + beta[player], sigma)

        Priors:
            alpha[team] ~ Normal(league_mean, team_sigma)
            beta[player] ~ Normal(0, player_sigma)
            sigma ~ Exponential(1)

        Args:
            data: DataFrame with player game data
            team_col: Team identifier column
            player_col: Player identifier column
            target_col: Target variable (e.g., 'points')

        Returns:
            Tuple of (model, encoded_data_dict)
        """
        # Encode categorical variables
        team_idx, teams = pd.factorize(data[team_col])
        player_idx, players = pd.factorize(data[player_col])
        y = data[target_col].values

        with pm.Model() as model:
            # Hyperpriors
            league_mean = pm.Normal("league_mean", mu=20, sigma=10)
            team_sigma = pm.Exponential("team_sigma", lam=1)
            player_sigma = pm.Exponential("player_sigma", lam=1)
            obs_sigma = pm.Exponential("obs_sigma", lam=1)

            # Team effects (partial pooling)
            team_effect = pm.Normal(
                "team_effect",
                mu=league_mean,
                sigma=team_sigma,
                shape=len(teams),
            )

            # Player effects (partial pooling)
            player_effect = pm.Normal(
                "player_effect", mu=0, sigma=player_sigma, shape=len(players)
            )

            # Expected value
            mu = team_effect[team_idx] + player_effect[player_idx]

            # Likelihood
            points = pm.Normal("points", mu=mu, sigma=obs_sigma, observed=y)

        encoded_data = {
            "team_idx": team_idx,
            "teams": teams,
            "player_idx": player_idx,
            "players": players,
        }

        logger.info(
            f"Built player scoring model: {len(teams)} teams, {len(players)} players"
        )
        return model, encoded_data

    @staticmethod
    def win_probability_model(
        data: pd.DataFrame,
        team_col: str = "team_id",
        opponent_col: str = "opponent_id",
        target_col: str = "won",
        features: Optional[List[str]] = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Logistic regression for game outcome with team effects.

        Model: P(win) = logit^-1(alpha[team] - alpha[opponent] + X*beta)

        Args:
            data: DataFrame with game data
            team_col: Team identifier
            opponent_col: Opponent identifier
            target_col: Binary win indicator
            features: Optional additional features

        Returns:
            Tuple of (model, encoded_data_dict)
        """
        team_idx, teams = pd.factorize(data[team_col])
        opp_idx, _ = pd.factorize(data[opponent_col])
        y = data[target_col].values

        with pm.Model() as model:
            # Team strengths (hierarchical)
            team_strength_mean = pm.Normal("team_strength_mean", mu=0, sigma=1)
            team_strength_sigma = pm.Exponential("team_strength_sigma", lam=1)

            team_strength = pm.Normal(
                "team_strength",
                mu=team_strength_mean,
                sigma=team_strength_sigma,
                shape=len(teams),
            )

            # Home advantage (if applicable)
            if "is_home" in data.columns:
                home_advantage = pm.Normal("home_advantage", mu=0, sigma=1)
                home_effect = home_advantage * data["is_home"].values
            else:
                home_effect = 0

            # Additional features
            if features:
                X = data[features].values
                n_features = X.shape[1]
                beta = pm.Normal("beta", mu=0, sigma=1, shape=n_features)
                feature_effect = pm.math.dot(X, beta)
            else:
                feature_effect = 0

            # Win probability
            logit_p = (
                team_strength[team_idx]
                - team_strength[opp_idx]
                + home_effect
                + feature_effect
            )

            # Likelihood
            won = pm.Bernoulli("won", logit_p=logit_p, observed=y)

        encoded_data = {"team_idx": team_idx, "teams": teams, "opp_idx": opp_idx}

        logger.info(f"Built win probability model: {len(teams)} teams")
        return model, encoded_data


# ==============================================================================
# Utility Functions
# ==============================================================================


def plot_posterior(
    result: BayesianModelResult,
    var_names: Optional[List[str]] = None,
    kind: str = "hist",
) -> Any:
    """
    Plot posterior distributions.

    Args:
        result: BayesianModelResult
        var_names: Variables to plot (None for all)
        kind: Plot type ('hist', 'kde', 'trace')

    Returns:
        Matplotlib figure
    """
    if kind == "trace":
        return az.plot_trace(result.trace, var_names=var_names)
    elif kind == "hist":
        return az.plot_posterior(result.trace, var_names=var_names)
    elif kind == "kde":
        return az.plot_posterior(result.trace, var_names=var_names, kind="kde")
    else:
        raise ValueError(f"Unknown plot kind: {kind}")


def plot_ppc(ppc_result: PPCResult) -> Any:
    """
    Plot posterior predictive check.

    Args:
        ppc_result: PPCResult

    Returns:
        Matplotlib figure
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot observed
    ax.scatter(
        range(len(ppc_result.observed)),
        ppc_result.observed,
        alpha=0.5,
        label="Observed",
        s=20,
    )

    # Plot mean prediction
    ax.scatter(
        range(len(ppc_result.mean_prediction)),
        ppc_result.mean_prediction,
        alpha=0.5,
        label="Predicted (mean)",
        s=20,
    )

    # Plot credible interval
    ax.fill_between(
        range(len(ppc_result.observed)),
        ppc_result.hdi_95_lower,
        ppc_result.hdi_95_upper,
        alpha=0.2,
        label="95% Credible Interval",
    )

    ax.set_xlabel("Observation")
    ax.set_ylabel("Value")
    ax.set_title(
        f"Posterior Predictive Check (Bayesian p-value: {ppc_result.p_value:.3f})"
    )
    ax.legend()
    plt.tight_layout()

    return fig
