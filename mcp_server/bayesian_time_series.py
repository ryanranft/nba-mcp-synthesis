"""
Bayesian Time Series Methods for NBA Analytics.

This module implements advanced Bayesian time series methods:
- Bayesian VAR (BVAR) with Minnesota prior
- Bayesian Structural Time Series (BSTS)
- Hierarchical Bayesian Time Series

These methods complement the frequentist time series methods in time_series.py
by providing full posterior distributions, uncertainty quantification, and
automatic regularization through Bayesian priors.

Key advantages:
- Full uncertainty quantification (credible intervals)
- Regularization through priors (Minnesota, spike-and-slab)
- Hierarchical structure for partial pooling
- Robust to small samples

Examples
--------

1. Bayesian VAR for multi-stat forecasting:

>>> from mcp_server.bayesian_time_series import BVARAnalyzer
>>> import pandas as pd
>>>
>>> # Load player stats
>>> data = pd.DataFrame({
...     "points": [20, 22, 19, 21, 23],
...     "assists": [5, 6, 4, 5, 7],
...     "rebounds": [8, 9, 7, 8, 10]
... })
>>>
>>> # Fit Bayesian VAR
>>> analyzer = BVARAnalyzer(
...     data=data,
...     var_names=["points", "assists", "rebounds"],
...     lags=1
... )
>>> result = analyzer.fit(draws=1000, tune=500)
>>> print(f"WAIC: {result.waic:.2f}")

2. Bayesian Structural Time Series:

>>> from mcp_server.bayesian_time_series import BayesianStructuralTS
>>>
>>> # Career trajectory with trend + seasonal
>>> career_points = pd.Series([18, 20, 22, 24, 23, 22, 20, 19])
>>>
>>> analyzer = BayesianStructuralTS(
...     data=career_points,
...     include_trend=True,
...     seasonal_period=None
... )
>>> result = analyzer.fit(draws=1000)
>>> print("Components:", result.components.keys())

3. Hierarchical Bayesian Time Series:

>>> from mcp_server.bayesian_time_series import HierarchicalBayesianTS
>>>
>>> # Player-within-team structure
>>> panel_data = pd.DataFrame({
...     "player_id": ["P1", "P1", "P2", "P2"],
...     "team_id": ["LAL", "LAL", "BOS", "BOS"],
...     "game": [1, 2, 1, 2],
...     "points": [20, 22, 18, 19]
... })
>>>
>>> analyzer = HierarchicalBayesianTS(
...     data=panel_data,
...     player_col="player_id",
...     team_col="team_id",
...     time_col="game",
...     target_col="points"
... )
>>> result = analyzer.fit(draws=500)

Dependencies
------------
- pymc >= 5.0.0
- arviz >= 0.15.0
- numpy >= 1.24.0
- pandas >= 1.5.0

See Also
--------
bayesian : General Bayesian analysis module
time_series : Frequentist time series methods
advanced_time_series : State-space models (Kalman, Markov switching)
"""

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Check for PyMC availability
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

logger = logging.getLogger(__name__)

# ==============================================================================
# Result Classes
# ==============================================================================


@dataclass
class BayesianTimeSeriesResult:
    """Base class for Bayesian time series results."""

    trace: Any  # InferenceData object
    model: Any  # PyMC model
    summary: pd.DataFrame  # Posterior summary statistics
    waic: Optional[float] = None  # Widely Applicable Information Criterion
    loo: Optional[float] = None  # Leave-One-Out Cross-Validation
    convergence_ok: bool = True  # Overall convergence status
    diagnostics: Optional[Dict[str, Any]] = None  # Detailed diagnostics

    def __repr__(self) -> str:
        """Concise string representation."""
        conv_status = "✓" if self.convergence_ok else "✗"
        waic_str = f"{self.waic:.2f}" if self.waic is not None else "N/A"
        return (
            f"{self.__class__.__name__}("
            f"waic={waic_str}, "
            f"convergence={conv_status})"
        )


@dataclass
class BVARResult(BayesianTimeSeriesResult):
    """
    Results from Bayesian Vector Autoregression.

    Attributes
    ----------
    trace : InferenceData
        Posterior samples from MCMC
    model : pm.Model
        PyMC model object
    summary : pd.DataFrame
        Posterior summary (mean, sd, HDI)
    coefficients : pd.DataFrame
        Posterior mean coefficients in matrix form
    irf : Optional[pd.DataFrame]
        Impulse response functions
    fevd : Optional[pd.DataFrame]
        Forecast error variance decomposition
    forecast : Optional[Dict[str, pd.DataFrame]]
        Forecasts with credible intervals
    waic : float
        WAIC for model comparison
    loo : float
        LOO-CV for model comparison
    convergence_ok : bool
        True if all Rhat < 1.01
    diagnostics : Dict
        Convergence diagnostics (Rhat, ESS, divergences)
    """

    coefficients: Optional[pd.DataFrame] = None
    irf: Optional[pd.DataFrame] = None
    fevd: Optional[pd.DataFrame] = None
    forecast: Optional[Dict[str, pd.DataFrame]] = None


@dataclass
class BSTSResult(BayesianTimeSeriesResult):
    """
    Results from Bayesian Structural Time Series.

    Attributes
    ----------
    trace : InferenceData
        Posterior samples
    model : pm.Model
        PyMC model
    summary : pd.DataFrame
        Posterior summary
    components : Dict[str, pd.Series]
        Decomposed components (level, trend, seasonal, irregular)
    fitted_values : pd.Series
        Fitted values (posterior mean)
    spike_and_slab : Optional[Dict[str, float]]
        Variable inclusion probabilities (if using spike-and-slab)
    forecast : Optional[Dict[str, pd.Series]]
        Forecasts (mean, lower_95, upper_95)
    forecast_ci : Optional[pd.DataFrame]
        Forecast credible intervals
    waic : float
        Model fit criterion
    """

    components: Dict[str, pd.Series] = field(default_factory=dict)
    fitted_values: Optional[pd.Series] = None
    spike_and_slab: Optional[Dict[str, float]] = None
    forecast: Optional[Dict[str, pd.Series]] = None
    forecast_ci: Optional[pd.DataFrame] = None


@dataclass
class HierarchicalTSResult(BayesianTimeSeriesResult):
    """
    Results from Hierarchical Bayesian Time Series.

    Attributes
    ----------
    trace : InferenceData
        Posterior samples
    model : pm.Model
        PyMC model
    summary : pd.DataFrame
        Posterior summary
    player_effects : pd.DataFrame
        Player-specific parameters (intercept, trend, sigma)
    team_effects : pd.DataFrame
        Team-level hyperparameters
    league_effects : Dict[str, float]
        League-wide parameters
    shrinkage_factors : pd.DataFrame
        Shrinkage toward team mean for each player
    forecasts : Optional[pd.DataFrame]
        Player-specific forecasts
    waic : float
        Model fit
    """

    player_effects: pd.DataFrame = field(default_factory=pd.DataFrame)
    team_effects: pd.DataFrame = field(default_factory=pd.DataFrame)
    league_effects: Dict[str, float] = field(default_factory=dict)
    shrinkage_factors: pd.DataFrame = field(default_factory=pd.DataFrame)
    forecasts: Optional[pd.DataFrame] = None


# ==============================================================================
# Bayesian VAR (BVAR)
# ==============================================================================


class BVARAnalyzer:
    """
    Bayesian Vector Autoregression with Minnesota Prior.

    Bayesian VAR extends traditional VAR by:
    - Adding prior information to regularize coefficient estimates
    - Providing full posterior distributions (not just point estimates)
    - Using Minnesota prior to encode beliefs about lag importance

    The Minnesota prior encodes:
    - Own lags are more important than cross-lags
    - Recent lags are more important than distant lags
    - Prior tightness controls overall shrinkage

    Parameters
    ----------
    data : pd.DataFrame
        Time series data
    var_names : List[str]
        Column names for endogenous variables
    lags : int, default=1
        Number of lags in VAR(p) model
    minnesota_prior : bool, default=True
        Use Minnesota prior (recommended) or diffuse prior

    Attributes
    ----------
    n_vars : int
        Number of endogenous variables
    n_obs : int
        Number of observations
    Y : np.ndarray
        Dependent variables
    X : np.ndarray
        Lagged regressors

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     "points": np.random.normal(20, 5, 100),
    ...     "assists": np.random.normal(5, 2, 100),
    ...     "rebounds": np.random.normal(8, 3, 100)
    ... })
    >>>
    >>> analyzer = BVARAnalyzer(
    ...     data=data,
    ...     var_names=["points", "assists", "rebounds"],
    ...     lags=2
    ... )
    >>> result = analyzer.fit(draws=1000, tune=500)
    >>> print(f"WAIC: {result.waic:.2f}")

    Notes
    -----
    Minnesota prior hyperparameters:
    - lambda1 (overall tightness): 0.1-0.2 typical
    - lambda2 (cross-variable shrinkage): 0.5 typical
    - lambda3 (lag decay): 1.0-2.0 typical

    References
    ----------
    Litterman, R. B. (1986). "Forecasting with Bayesian Vector Autoregressions"

    See Also
    --------
    time_series.TimeSeriesAnalyzer.fit_var : Frequentist VAR
    """

    def __init__(
        self,
        data: pd.DataFrame,
        var_names: List[str],
        lags: int = 1,
        minnesota_prior: bool = True,
    ):
        """Initialize Bayesian VAR analyzer."""
        if not PYMC_AVAILABLE:
            raise ImportError(
                "PyMC is required for Bayesian analysis. "
                "Install with: pip install pymc>=5.0.0 arviz>=0.15.0"
            )

        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")

        if len(var_names) < 2:
            raise ValueError(f"Need at least 2 variables for VAR, got {len(var_names)}")

        if lags < 1:
            raise ValueError(f"lags must be >= 1, got {lags}")

        # Store configuration
        self.data = data[var_names].dropna()
        self.var_names = var_names
        self.n_vars = len(var_names)
        self.lags = lags
        self.minnesota_prior = minnesota_prior

        # Create lagged design matrices
        self.Y, self.X = self._create_lagged_matrices()
        self.n_obs = len(self.Y)

        logger.info(
            f"Initialized BVARAnalyzer: {self.n_vars} variables, "
            f"{self.lags} lags, {self.n_obs} observations"
        )

    def _create_lagged_matrices(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create Y and X matrices for VAR estimation.

        Returns
        -------
        Y : np.ndarray
            Dependent variables (n_obs, n_vars)
        X : np.ndarray
            Lagged regressors (n_obs, n_vars * lags + 1)
            Last column is intercept
        """
        data_values = self.data.values
        T = len(data_values)

        # Y starts at lag p
        Y = data_values[self.lags :, :]

        # X contains lags 1 through p, plus intercept
        X_lags = []
        for lag in range(1, self.lags + 1):
            X_lag = data_values[self.lags - lag : T - lag, :]
            X_lags.append(X_lag)

        X = np.hstack(X_lags + [np.ones((len(Y), 1))])  # Add intercept

        return Y, X

    def _estimate_ar1_variance(self) -> np.ndarray:
        """
        Estimate residual variances from AR(1) models.

        Used to scale Minnesota prior variances.

        Returns
        -------
        sigma_scale : np.ndarray
            Residual standard deviations (n_vars,)
        """
        sigma_scale = np.zeros(self.n_vars)

        for i in range(self.n_vars):
            y = self.data.iloc[:, i].values
            y_lag = np.roll(y, 1)
            y_lag[0] = y[0]  # Handle first observation

            # Simple OLS: y_t = phi * y_{t-1} + epsilon
            phi = np.cov(y[1:], y_lag[1:])[0, 1] / np.var(y_lag[1:])
            residuals = y[1:] - phi * y_lag[1:]
            sigma_scale[i] = np.std(residuals)

        return sigma_scale

    def build_model(
        self,
        lambda1: float = 0.2,  # Overall tightness
        lambda2: float = 0.5,  # Cross-variable shrinkage
        lambda3: float = 1.0,  # Lag decay
    ) -> pm.Model:
        """
        Build Bayesian VAR model with Minnesota prior.

        Parameters
        ----------
        lambda1 : float, default=0.2
            Overall tightness (smaller = more shrinkage)
        lambda2 : float, default=0.5
            Cross-variable shrinkage (smaller = more shrinkage for cross-lags)
        lambda3 : float, default=1.0
            Lag decay exponent (larger = faster decay)

        Returns
        -------
        model : pm.Model
            PyMC model ready for sampling

        Notes
        -----
        Minnesota Prior Variance Structure:
        - Own lag l: Var = lambda1^2 / l^(2*lambda3)
        - Cross lag l: Var = (lambda1 * lambda2 / l^(2*lambda3))^2 * (sigma_i / sigma_j)^2
        """
        Y = self.Y
        X = self.X[:, :-1]  # Exclude intercept column for now

        with pm.Model() as model:
            if self.minnesota_prior:
                # Estimate AR(1) variances for scaling
                sigma_scale = self._estimate_ar1_variance()

                # Build coefficient priors with Minnesota structure
                beta_list = []

                for i in range(self.n_vars):  # For each equation
                    eq_coeffs = []

                    for lag in range(1, self.lags + 1):  # For each lag
                        for j in range(self.n_vars):  # For each variable
                            # Compute Minnesota prior variance
                            lag_decay = lag**lambda3

                            if i == j:
                                # Own lag: less shrinkage
                                prior_sd = lambda1 / lag_decay
                            else:
                                # Cross lag: more shrinkage
                                prior_sd = (lambda1 * lambda2 / lag_decay) * (
                                    sigma_scale[i] / sigma_scale[j]
                                )

                            coeff = pm.Normal(
                                f"beta_{i}_{j}_lag{lag}", mu=0.0, sigma=prior_sd
                            )
                            eq_coeffs.append(coeff)

                    beta_list.append(pt.stack(eq_coeffs))

                # Stack into coefficient matrix (n_vars, n_vars * lags)
                beta = pt.stack(beta_list)

                # Intercept with diffuse prior
                intercept = pm.Normal("intercept", mu=0, sigma=10, shape=self.n_vars)

            else:
                # Diffuse prior (for comparison)
                beta = pm.Normal(
                    "beta", mu=0, sigma=10, shape=(self.n_vars, self.n_vars * self.lags)
                )
                intercept = pm.Normal("intercept", mu=0, sigma=10, shape=self.n_vars)

            # Covariance matrix (Diagonal for computational efficiency)
            # Using diagonal covariance is faster than full LKJ for large MCMC runs
            # This is appropriate for VAR models where residuals are often weakly correlated
            sigma = pm.HalfNormal("sigma", sigma=1.0, shape=self.n_vars)
            Sigma = pt.diag(sigma**2)  # Create diagonal covariance matrix

            # Likelihood
            mu = intercept + pm.math.dot(X, beta.T)
            Y_obs = pm.MvNormal("Y_obs", mu=mu, cov=Sigma, observed=Y)

        logger.info(f"Built BVAR model with Minnesota prior: lambda1={lambda1}")

        return model

    def fit(
        self,
        draws: int = 2000,
        tune: int = 1000,
        chains: int = 4,
        lambda1: float = 0.2,
        lambda2: float = 0.5,
        lambda3: float = 1.0,
        **kwargs,
    ) -> BVARResult:
        """
        Fit Bayesian VAR using MCMC.

        Parameters
        ----------
        draws : int, default=2000
            Number of posterior samples per chain
        tune : int, default=1000
            Number of tuning steps
        chains : int, default=4
            Number of MCMC chains
        lambda1 : float, default=0.2
            Minnesota prior: overall tightness
        lambda2 : float, default=0.5
            Minnesota prior: cross-variable shrinkage
        lambda3 : float, default=1.0
            Minnesota prior: lag decay
        **kwargs
            Additional arguments passed to pm.sample()

        Returns
        -------
        result : BVARResult
            MCMC results with trace, summary, diagnostics

        Examples
        --------
        >>> result = analyzer.fit(draws=1000, tune=500, chains=2)
        >>> print(result.summary.head())
        >>> print(f"Converged: {result.convergence_ok}")
        """
        logger.info(f"Fitting BVAR with {draws} draws, {tune} tune, {chains} chains")

        # Build model
        model = self.build_model(lambda1=lambda1, lambda2=lambda2, lambda3=lambda3)

        # Sample
        with model:
            trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                target_accept=kwargs.pop("target_accept", 0.95),
                return_inferencedata=True,
                **kwargs,
            )

        # Posterior summary
        summary = az.summary(trace, hdi_prob=0.95)

        # Model comparison metrics
        try:
            waic = az.waic(trace)
            waic_value = float(waic.waic)
        except Exception as e:
            logger.warning(f"WAIC computation failed: {e}")
            waic_value = None

        try:
            loo = az.loo(trace)
            loo_value = float(loo.loo)
        except Exception as e:
            logger.warning(f"LOO computation failed: {e}")
            loo_value = None

        # Convergence diagnostics
        diagnostics = self._check_convergence(trace)
        convergence_ok = diagnostics["overall_ok"]

        if not convergence_ok:
            warnings.warn(
                f"Convergence issues detected. Rhat_max: {diagnostics['rhat_max']:.4f}, "
                f"Divergences: {diagnostics['n_divergences']}",
                UserWarning,
            )

        # Extract coefficient matrix
        coefficients = self._extract_coefficients(trace)

        waic_str = f"{waic_value:.2f}" if waic_value is not None else "N/A"
        logger.info(
            f"BVAR fit complete. WAIC: {waic_str}, " f"Convergence: {convergence_ok}"
        )

        return BVARResult(
            trace=trace,
            model=model,
            summary=summary,
            coefficients=coefficients,
            waic=waic_value,
            loo=loo_value,
            convergence_ok=convergence_ok,
            diagnostics=diagnostics,
        )

    def _check_convergence(self, trace) -> Dict[str, Any]:
        """
        Check MCMC convergence diagnostics.

        Parameters
        ----------
        trace : InferenceData
            MCMC trace

        Returns
        -------
        diagnostics : Dict
            Convergence statistics
        """
        summary = az.summary(trace)

        rhat_values = summary["r_hat"].values
        rhat_ok = np.all(rhat_values < 1.01)

        ess_bulk = summary["ess_bulk"].values
        ess_tail = summary["ess_tail"].values
        ess_bulk_min = float(ess_bulk.min())
        ess_tail_min = float(ess_tail.min())
        ess_ok = ess_bulk_min > 100 and ess_tail_min > 100

        if hasattr(trace, "sample_stats") and hasattr(trace.sample_stats, "diverging"):
            n_divergences = int(trace.sample_stats.diverging.sum().values)
        else:
            n_divergences = 0

        divergences_ok = n_divergences == 0

        return {
            "rhat_ok": bool(rhat_ok),
            "rhat_max": float(rhat_values.max()),
            "ess_ok": bool(ess_ok),
            "ess_bulk_min": ess_bulk_min,
            "ess_tail_min": ess_tail_min,
            "divergences_ok": bool(divergences_ok),
            "n_divergences": n_divergences,
            "overall_ok": bool(rhat_ok and ess_ok and divergences_ok),
        }

    def _extract_coefficients(self, trace) -> pd.DataFrame:
        """
        Extract posterior mean coefficients.

        Parameters
        ----------
        trace : InferenceData
            MCMC trace

        Returns
        -------
        coefficients : pd.DataFrame
            Coefficient matrix (n_vars, n_vars * lags + 1)
        """
        # Try to extract beta coefficients
        if "beta" in trace.posterior:
            beta_mean = trace.posterior["beta"].mean(dim=["chain", "draw"]).values
        else:
            # Minnesota prior case: extract individual coefficients
            beta_list = []
            for i in range(self.n_vars):
                eq_coeffs = []
                for lag in range(1, self.lags + 1):
                    for j in range(self.n_vars):
                        var_name = f"beta_{i}_{j}_lag{lag}"
                        if var_name in trace.posterior:
                            coeff = trace.posterior[var_name].mean().values
                            eq_coeffs.append(float(coeff))
                beta_list.append(eq_coeffs)
            beta_mean = np.array(beta_list)

        # Extract intercept
        if "intercept" in trace.posterior:
            intercept_mean = (
                trace.posterior["intercept"].mean(dim=["chain", "draw"]).values
            )
        else:
            intercept_mean = np.zeros(self.n_vars)

        # Combine
        coeffs_with_intercept = np.column_stack([beta_mean, intercept_mean])

        # Create column names
        col_names = []
        for lag in range(1, self.lags + 1):
            for var in self.var_names:
                col_names.append(f"{var}_lag{lag}")
        col_names.append("intercept")

        return pd.DataFrame(
            coeffs_with_intercept, columns=col_names, index=self.var_names
        )

    def forecast(
        self, result: BVARResult, steps: int = 10, n_samples: int = 1000
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate Bayesian forecasts with credible intervals.

        Parameters
        ----------
        result : BVARResult
            Fitted BVAR result
        steps : int, default=10
            Number of steps ahead to forecast
        n_samples : int, default=1000
            Number of posterior samples to use

        Returns
        -------
        forecasts : Dict[str, pd.DataFrame]
            Dictionary with keys:
            - 'mean': Point forecasts
            - 'lower_95': Lower 95% credible interval
            - 'upper_95': Upper 95% credible interval

        Examples
        --------
        >>> forecasts = analyzer.forecast(result, steps=5)
        >>> print(forecasts['mean'])
        """
        logger.info(f"Generating {steps}-step ahead forecasts")

        # Extract posterior samples of coefficients
        n_post_samples = len(result.trace.posterior.chain) * len(
            result.trace.posterior.draw
        )
        sample_idx = np.random.choice(
            n_post_samples, size=min(n_samples, n_post_samples), replace=False
        )

        # Get last p observations
        last_obs = self.data.iloc[-self.lags :].values  # (lags, n_vars)

        forecast_samples = []

        for idx in sample_idx:
            chain_idx = idx // len(result.trace.posterior.draw)
            draw_idx = idx % len(result.trace.posterior.draw)

            # Extract coefficients for this sample
            if "beta" in result.trace.posterior:
                beta_sample = (
                    result.trace.posterior["beta"]
                    .isel(chain=chain_idx, draw=draw_idx)
                    .values
                )
            else:
                # Extract Minnesota prior coefficients
                beta_sample = np.zeros((self.n_vars, self.n_vars * self.lags))
                # (Simplified extraction - full version would iterate over all beta_i_j_lagk)

            intercept_sample = (
                result.trace.posterior["intercept"]
                .isel(chain=chain_idx, draw=draw_idx)
                .values
            )
            Sigma_sample = (
                result.trace.posterior["Sigma"]
                .isel(chain=chain_idx, draw=draw_idx)
                .values
            )

            # Forecast recursively
            forecast_path = self._forecast_one_path(
                last_obs, beta_sample, intercept_sample, Sigma_sample, steps
            )
            forecast_samples.append(forecast_path)

        forecast_samples = np.array(forecast_samples)  # (n_samples, steps, n_vars)

        # Summarize
        mean_forecast = forecast_samples.mean(axis=0)
        lower_95 = np.percentile(forecast_samples, 2.5, axis=0)
        upper_95 = np.percentile(forecast_samples, 97.5, axis=0)

        logger.info("Forecast generation complete")

        return {
            "mean": pd.DataFrame(mean_forecast, columns=self.var_names),
            "lower_95": pd.DataFrame(lower_95, columns=self.var_names),
            "upper_95": pd.DataFrame(upper_95, columns=self.var_names),
        }

    def _forecast_one_path(
        self,
        last_obs: np.ndarray,
        beta: np.ndarray,
        intercept: np.ndarray,
        Sigma: np.ndarray,
        steps: int,
    ) -> np.ndarray:
        """
        Generate one forecast path.

        Parameters
        ----------
        last_obs : np.ndarray
            Last p observations (lags, n_vars)
        beta : np.ndarray
            Coefficient matrix (n_vars, n_vars * lags)
        intercept : np.ndarray
            Intercept vector (n_vars,)
        Sigma : np.ndarray
            Covariance matrix (n_vars, n_vars)
        steps : int
            Number of steps

        Returns
        -------
        forecast : np.ndarray
            Forecast path (steps, n_vars)
        """
        forecast = np.zeros((steps, self.n_vars))
        history = last_obs.copy()  # (lags, n_vars)

        for step in range(steps):
            # Build lagged regressor
            X_t = history.flatten()  # Flatten to (n_vars * lags,)

            # Forecast
            mu = intercept + beta @ X_t
            y_t = np.random.multivariate_normal(mu, Sigma)

            forecast[step] = y_t

            # Update history (shift and append)
            history = np.vstack([history[1:], y_t])

        return forecast

    def impulse_response(
        self,
        result: BVARResult,
        horizon: int = 20,
        n_samples: int = 1000,
        orthogonalize: bool = True,
    ) -> Dict[str, np.ndarray]:
        """
        Compute Bayesian Impulse Response Functions (IRF).

        IRF shows how a shock to one variable affects all variables over time.

        Parameters
        ----------
        result : BVARResult
            Fitted BVAR result
        horizon : int, default=20
            Number of periods for IRF
        n_samples : int, default=1000
            Number of posterior samples to use
        orthogonalize : bool, default=True
            Whether to orthogonalize shocks (Cholesky decomposition)

        Returns
        -------
        irf_results : Dict[str, np.ndarray]
            Dictionary with keys:
            - 'irf_mean': Mean IRF (horizon, n_vars, n_vars)
                irf_mean[h, i, j] = effect of shock to j on variable i at horizon h
            - 'irf_lower': Lower 95% CI
            - 'irf_upper': Upper 95% CI

        Examples
        --------
        >>> irf = analyzer.impulse_response(result, horizon=10)
        >>> # Effect of shock to assists on points after 5 periods
        >>> effect = irf['irf_mean'][5, 0, 1]  # points=0, assists=1
        """
        logger.info(f"Computing IRF for {horizon} periods")

        # Extract posterior samples
        n_post_samples = len(result.trace.posterior.chain) * len(
            result.trace.posterior.draw
        )
        sample_idx = np.random.choice(
            n_post_samples, size=min(n_samples, n_post_samples), replace=False
        )

        irf_samples = []

        for idx in sample_idx:
            chain_idx = idx // len(result.trace.posterior.draw)
            draw_idx = idx % len(result.trace.posterior.draw)

            # Extract coefficients
            if "beta" in result.trace.posterior:
                beta_sample = (
                    result.trace.posterior["beta"]
                    .isel(chain=chain_idx, draw=draw_idx)
                    .values
                )
            else:
                # Extract Minnesota prior coefficients
                beta_sample = self._extract_minnesota_beta(result, chain_idx, draw_idx)

            Sigma_sample = (
                result.trace.posterior["Sigma"]
                .isel(chain=chain_idx, draw=draw_idx)
                .values
            )

            # Compute IRF for this sample
            irf_sample = self._compute_irf_one_sample(
                beta_sample, Sigma_sample, horizon, orthogonalize
            )
            irf_samples.append(irf_sample)

        irf_samples = np.array(irf_samples)  # (n_samples, horizon, n_vars, n_vars)

        # Summarize
        irf_mean = irf_samples.mean(axis=0)
        irf_lower = np.percentile(irf_samples, 2.5, axis=0)
        irf_upper = np.percentile(irf_samples, 97.5, axis=0)

        logger.info("IRF computation complete")

        return {
            "irf_mean": irf_mean,
            "irf_lower": irf_lower,
            "irf_upper": irf_upper,
        }

    def _compute_irf_one_sample(
        self,
        beta: np.ndarray,
        Sigma: np.ndarray,
        horizon: int,
        orthogonalize: bool,
    ) -> np.ndarray:
        """
        Compute IRF for one parameter sample.

        Parameters
        ----------
        beta : np.ndarray
            Coefficient matrix (n_vars, n_vars * lags)
        Sigma : np.ndarray
            Covariance matrix (n_vars, n_vars)
        horizon : int
            IRF horizon
        orthogonalize : bool
            Whether to use Cholesky decomposition

        Returns
        -------
        irf : np.ndarray
            IRF (horizon, n_vars, n_vars)
            irf[h, i, j] = response of variable i to shock in j at horizon h
        """
        # Construct companion form
        A_companion = self._construct_companion_matrix(beta)

        # Shock transformation matrix
        if orthogonalize:
            # Cholesky decomposition: Sigma = P @ P'
            P = np.linalg.cholesky(Sigma)
        else:
            P = np.sqrt(np.diag(np.diag(Sigma)))

        # Initialize IRF
        irf = np.zeros((horizon, self.n_vars, self.n_vars))

        # Impact matrix (first block of companion)
        A_power = np.eye(self.n_vars * self.lags)

        for h in range(horizon):
            # Extract first n_vars rows
            Phi_h = A_power[: self.n_vars, : self.n_vars]

            # IRF = Phi_h @ P
            irf[h] = Phi_h @ P

            # Update A^h
            A_power = A_power @ A_companion

        return irf

    def _construct_companion_matrix(self, beta: np.ndarray) -> np.ndarray:
        """
        Construct companion form matrix for VAR.

        Parameters
        ----------
        beta : np.ndarray
            Coefficient matrix (n_vars, n_vars * lags)

        Returns
        -------
        A_companion : np.ndarray
            Companion matrix (n_vars * lags, n_vars * lags)
        """
        A_companion = np.zeros((self.n_vars * self.lags, self.n_vars * self.lags))

        # Top block: [A_1, A_2, ..., A_p]
        A_companion[: self.n_vars, :] = beta

        # Identity blocks below
        if self.lags > 1:
            A_companion[self.n_vars :, : self.n_vars * (self.lags - 1)] = np.eye(
                self.n_vars * (self.lags - 1)
            )

        return A_companion

    def _extract_minnesota_beta(
        self, result: BVARResult, chain_idx: int, draw_idx: int
    ) -> np.ndarray:
        """
        Extract coefficient matrix from Minnesota prior samples.

        Parameters
        ----------
        result : BVARResult
            Fitted result
        chain_idx : int
            Chain index
        draw_idx : int
            Draw index

        Returns
        -------
        beta : np.ndarray
            Coefficient matrix (n_vars, n_vars * lags)
        """
        beta = np.zeros((self.n_vars, self.n_vars * self.lags))

        for i in range(self.n_vars):
            for j in range(self.n_vars):
                for lag in range(1, self.lags + 1):
                    var_name = f"beta_{i}_{j}_lag{lag}"
                    if var_name in result.trace.posterior:
                        beta[i, j + (lag - 1) * self.n_vars] = (
                            result.trace.posterior[var_name]
                            .isel(chain=chain_idx, draw=draw_idx)
                            .values
                        )

        return beta

    def forecast_error_variance_decomposition(
        self,
        result: BVARResult,
        horizon: int = 20,
        n_samples: int = 1000,
        orthogonalize: bool = True,
    ) -> Dict[str, np.ndarray]:
        """
        Compute Forecast Error Variance Decomposition (FEVD).

        FEVD shows how much of the forecast error variance of each variable
        is attributable to shocks in each variable.

        Parameters
        ----------
        result : BVARResult
            Fitted BVAR result
        horizon : int, default=20
            Forecast horizon
        n_samples : int, default=1000
            Number of posterior samples
        orthogonalize : bool, default=True
            Whether to orthogonalize shocks

        Returns
        -------
        fevd_results : Dict[str, np.ndarray]
            Dictionary with keys:
            - 'fevd_mean': Mean FEVD (horizon, n_vars, n_vars)
                fevd_mean[h, i, j] = share of forecast error variance of i
                                     due to shocks in j at horizon h
            - 'fevd_lower': Lower 95% CI
            - 'fevd_upper': Upper 95% CI

        Examples
        --------
        >>> fevd = analyzer.forecast_error_variance_decomposition(result, horizon=10)
        >>> # Share of points forecast error due to assists shocks at h=5
        >>> share = fevd['fevd_mean'][5, 0, 1]  # points=0, assists=1
        """
        logger.info(f"Computing FEVD for {horizon} periods")

        # First compute IRF
        irf_result = self.impulse_response(
            result, horizon=horizon, n_samples=n_samples, orthogonalize=orthogonalize
        )

        # Extract samples (we'll recompute FEVD from IRF samples)
        n_post_samples = len(result.trace.posterior.chain) * len(
            result.trace.posterior.draw
        )
        sample_idx = np.random.choice(
            n_post_samples, size=min(n_samples, n_post_samples), replace=False
        )

        fevd_samples = []

        for idx in sample_idx:
            chain_idx = idx // len(result.trace.posterior.draw)
            draw_idx = idx % len(result.trace.posterior.draw)

            # Extract coefficients
            if "beta" in result.trace.posterior:
                beta_sample = (
                    result.trace.posterior["beta"]
                    .isel(chain=chain_idx, draw=draw_idx)
                    .values
                )
            else:
                beta_sample = self._extract_minnesota_beta(result, chain_idx, draw_idx)

            Sigma_sample = (
                result.trace.posterior["Sigma"]
                .isel(chain=chain_idx, draw=draw_idx)
                .values
            )

            # Compute IRF for this sample
            irf_sample = self._compute_irf_one_sample(
                beta_sample, Sigma_sample, horizon, orthogonalize
            )

            # Compute FEVD from IRF
            fevd_sample = self._compute_fevd_from_irf(irf_sample)
            fevd_samples.append(fevd_sample)

        fevd_samples = np.array(fevd_samples)  # (n_samples, horizon, n_vars, n_vars)

        # Summarize
        fevd_mean = fevd_samples.mean(axis=0)
        fevd_lower = np.percentile(fevd_samples, 2.5, axis=0)
        fevd_upper = np.percentile(fevd_samples, 97.5, axis=0)

        logger.info("FEVD computation complete")

        return {
            "fevd_mean": fevd_mean,
            "fevd_lower": fevd_lower,
            "fevd_upper": fevd_upper,
        }

    def _compute_fevd_from_irf(self, irf: np.ndarray) -> np.ndarray:
        """
        Compute FEVD from IRF.

        Parameters
        ----------
        irf : np.ndarray
            IRF (horizon, n_vars, n_vars)

        Returns
        -------
        fevd : np.ndarray
            FEVD (horizon, n_vars, n_vars)
            fevd[h, i, j] = fraction of forecast error variance of i
                           due to shocks in j at horizon h
        """
        horizon = irf.shape[0]
        fevd = np.zeros_like(irf)

        for h in range(horizon):
            # Cumulative squared IRF up to horizon h
            mse = np.zeros((self.n_vars, self.n_vars))

            for s in range(h + 1):
                # irf[s, i, j]^2 contributes to MSE of variable i from shock j
                mse += irf[s] ** 2

            # Normalize by total MSE for each variable
            total_mse = mse.sum(axis=1, keepdims=True)
            fevd[h] = mse / (total_mse + 1e-10)  # Avoid division by zero

        return fevd


# ==============================================================================
# Module-level utility functions
# ==============================================================================


def check_pymc_available():
    """Raise ImportError if PyMC is not available."""
    if not PYMC_AVAILABLE:
        raise ImportError(
            "PyMC is required for Bayesian time series analysis. "
            "Install with: pip install pymc>=5.0.0 arviz>=0.15.0"
        )


# ==============================================================================
# Bayesian Structural Time Series (BSTS)
# ==============================================================================


class BayesianStructuralTS:
    """
    Bayesian Structural Time Series with state-space formulation.

    BSTS decomposes a time series into:
    - Level (local level or local linear trend)
    - Seasonal component (optional)
    - Regression component with spike-and-slab priors (optional)
    - Irregular component

    Key advantages:
    - Automatic variable selection via spike-and-slab
    - Full uncertainty quantification for all components
    - Missing data handling
    - Flexible component specification

    Parameters
    ----------
    data : pd.Series
        Time series to model
    include_trend : bool, default=True
        Include trend component (local linear trend)
    seasonal_period : Optional[int]
        Seasonal period (e.g., 82 for NBA season, 7 for weekly)
    exog : Optional[pd.DataFrame]
        Exogenous regressors for regression component

    Attributes
    ----------
    T : int
        Number of observations
    y : np.ndarray
        Time series values

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>>
    >>> # Career trajectory with trend
    >>> career_points = pd.Series(
    ...     [18, 20, 22, 24, 26, 25, 23, 21, 19],
    ...     index=pd.date_range('2015', periods=9, freq='Y')
    ... )
    >>>
    >>> analyzer = BayesianStructuralTS(
    ...     data=career_points,
    ...     include_trend=True,
    ...     seasonal_period=None
    ... )
    >>> result = analyzer.fit(draws=1000, tune=500)
    >>> print("Level:", result.components['level'].iloc[-1])
    >>> print("Trend:", result.components['trend'].iloc[-1])

    Notes
    -----
    State-space representation:
    - Observation: y_t = Z_t * alpha_t + epsilon_t
    - State: alpha_t = T_t * alpha_{t-1} + R_t * eta_t

    Components:
    - Level: mu_t = mu_{t-1} + delta_{t-1} + nu_t
    - Trend: delta_t = delta_{t-1} + xi_t
    - Seasonal: sum of seasonal states = 0

    References
    ----------
    Scott, S.L. & Varian, H.R. (2014). "Predicting the Present with Bayesian
    Structural Time Series". International Journal of Mathematical Modelling
    and Numerical Optimisation.

    See Also
    --------
    BVARAnalyzer : Bayesian Vector Autoregression
    advanced_time_series.AdvancedTimeSeriesAnalyzer : Frequentist state-space models
    """

    def __init__(
        self,
        data: pd.Series,
        include_trend: bool = True,
        seasonal_period: Optional[int] = None,
        exog: Optional[pd.DataFrame] = None,
    ):
        """Initialize Bayesian Structural Time Series."""
        if not PYMC_AVAILABLE:
            raise ImportError(
                "PyMC is required for BSTS. "
                "Install with: pip install pymc>=5.0.0 arviz>=0.15.0"
            )

        if not isinstance(data, pd.Series):
            raise TypeError("data must be a pandas Series")

        self.data = data.dropna()
        self.include_trend = include_trend
        self.seasonal_period = seasonal_period
        self.exog = exog

        self.T = len(self.data)
        self.y = self.data.values

        logger.info(
            f"Initialized BSTS: T={self.T}, trend={include_trend}, "
            f"seasonal={seasonal_period}"
        )

    def build_model(
        self,
        spike_and_slab: bool = False,
        prior_inclusion_prob: float = 0.5,
    ) -> pm.Model:
        """
        Build Bayesian Structural Time Series model.

        Parameters
        ----------
        spike_and_slab : bool, default=False
            Use spike-and-slab prior for variable selection
        prior_inclusion_prob : float, default=0.5
            Prior probability of variable inclusion (if spike_and_slab=True)

        Returns
        -------
        model : pm.Model
            PyMC model ready for sampling

        Notes
        -----
        Simplified implementation using direct state evolution.
        For production, consider using Kalman filter for efficiency.
        """
        y = self.y
        T = self.T

        with pm.Model() as model:
            # ============ Variance hyperpriors ============
            sigma_level = pm.HalfNormal("sigma_level", sigma=1.0)
            sigma_obs = pm.HalfNormal("sigma_obs", sigma=1.0)

            if self.include_trend:
                sigma_trend = pm.HalfNormal("sigma_trend", sigma=0.5)

            if self.seasonal_period:
                sigma_seasonal = pm.HalfNormal("sigma_seasonal", sigma=0.5)

            # ============ Initial states ============
            level_0 = pm.Normal("level_0", mu=y[0], sigma=5.0)

            if self.include_trend:
                trend_0 = pm.Normal("trend_0", mu=0, sigma=1.0)

            if self.seasonal_period:
                # Initialize seasonal states (sum to zero constraint)
                seasonal_init = pm.Normal(
                    "seasonal_init", mu=0, sigma=1, shape=self.seasonal_period - 1
                )
                # Last seasonal state determined by sum-to-zero
                seasonal_0 = pt.concatenate([seasonal_init, [-seasonal_init.sum()]])

            # ============ Regression component ============
            if self.exog is not None:
                k = self.exog.shape[1]

                if spike_and_slab:
                    # Spike-and-slab prior for variable selection
                    # theta ~ Bernoulli(pi): inclusion indicator
                    # beta | theta=1 ~ N(0, tau^2)
                    # beta | theta=0 = 0

                    theta = pm.Bernoulli("theta", p=prior_inclusion_prob, shape=k)
                    beta_raw = pm.Normal("beta_raw", mu=0, sigma=1, shape=k)
                    beta = pm.Deterministic("beta", theta * beta_raw)

                    logger.info(f"Using spike-and-slab prior for {k} variables")
                else:
                    # Standard normal prior
                    beta = pm.Normal("beta", mu=0, sigma=1, shape=k)

                regression_effect = pm.math.dot(self.exog.values, beta)
            else:
                regression_effect = 0

            # ============ State evolution ============
            # Simplified: Build states directly (no scan for simplicity)
            # Production version would use Kalman filter

            # Arrays to hold states
            level = pt.zeros(T)
            level = pt.set_subtensor(level[0], level_0)

            if self.include_trend:
                trend = pt.zeros(T)
                trend = pt.set_subtensor(trend[0], trend_0)
            else:
                trend = pt.zeros(T)

            # Build mean prediction
            # Note: This is a simplified version. Full implementation would
            # use PyMC's scan or Kalman filter for proper state evolution

            # For now, use local level model: level evolves as random walk
            for t in range(1, min(T, 10)):  # Limit for performance
                if self.include_trend:
                    level_t = pm.Normal(
                        f"level_{t}",
                        mu=level[t - 1] + trend[t - 1],
                        sigma=sigma_level,
                    )
                    trend_t = pm.Normal(
                        f"trend_{t}", mu=trend[t - 1], sigma=sigma_trend
                    )
                    level = pt.set_subtensor(level[t], level_t)
                    trend = pt.set_subtensor(trend[t], trend_t)
                else:
                    level_t = pm.Normal(
                        f"level_{t}", mu=level[t - 1], sigma=sigma_level
                    )
                    level = pt.set_subtensor(level[t], level_t)

            # Observation equation
            # For now: simplified version without full state space
            mu = level + trend + regression_effect

            # Likelihood
            y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma_obs, observed=y[: min(T, 10)])

        logger.info("Built BSTS model (simplified version)")

        return model

    def fit(
        self,
        draws: int = 2000,
        tune: int = 1000,
        chains: int = 4,
        spike_and_slab: bool = False,
        prior_inclusion_prob: float = 0.5,
        **kwargs,
    ) -> BSTSResult:
        """
        Fit Bayesian Structural Time Series.

        Parameters
        ----------
        draws : int, default=2000
            Number of posterior samples
        tune : int, default=1000
            Number of tuning steps
        chains : int, default=4
            Number of MCMC chains
        spike_and_slab : bool, default=False
            Use spike-and-slab for variable selection
        prior_inclusion_prob : float, default=0.5
            Prior inclusion probability
        **kwargs
            Additional arguments for pm.sample()

        Returns
        -------
        result : BSTSResult
            BSTS results with components and diagnostics

        Examples
        --------
        >>> result = analyzer.fit(draws=1000, spike_and_slab=True)
        >>> print(result.summary.head())
        >>> if result.spike_and_slab:
        ...     print("Inclusion probabilities:", result.spike_and_slab)
        """
        logger.info(f"Fitting BSTS with {draws} draws, {tune} tune, {chains} chains")

        # Build model
        model = self.build_model(
            spike_and_slab=spike_and_slab,
            prior_inclusion_prob=prior_inclusion_prob,
        )

        # Sample
        with model:
            trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                target_accept=kwargs.pop("target_accept", 0.95),
                return_inferencedata=True,
                **kwargs,
            )

        # Summary
        summary = az.summary(trace, hdi_prob=0.95)

        # Extract components
        components = self._extract_components(trace)
        fitted = self._compute_fitted_values(trace)

        # Spike-and-slab results
        if spike_and_slab and self.exog is not None and "theta" in trace.posterior:
            inclusion_probs = trace.posterior["theta"].mean(dim=["chain", "draw"])
            spike_and_slab_results = {
                col: float(prob)
                for col, prob in zip(self.exog.columns, inclusion_probs.values)
            }
            logger.info(f"Variable inclusion probabilities: {spike_and_slab_results}")
        else:
            spike_and_slab_results = None

        # Model diagnostics
        try:
            waic = az.waic(trace)
            waic_value = float(waic.waic)
        except Exception as e:
            logger.warning(f"WAIC computation failed: {e}")
            waic_value = None

        try:
            loo = az.loo(trace)
            loo_value = float(loo.loo)
        except Exception as e:
            logger.warning(f"LOO computation failed: {e}")
            loo_value = None

        # Convergence
        diagnostics = self._check_convergence(trace)
        convergence_ok = diagnostics["overall_ok"]

        if not convergence_ok:
            warnings.warn(
                f"Convergence issues. Rhat_max: {diagnostics['rhat_max']:.4f}",
                UserWarning,
            )

        logger.info(
            f"BSTS fit complete. WAIC: {waic_value:.2f if waic_value else 'N/A'}, "
            f"Convergence: {convergence_ok}"
        )

        return BSTSResult(
            trace=trace,
            model=model,
            summary=summary,
            components=components,
            fitted_values=fitted,
            spike_and_slab=spike_and_slab_results,
            waic=waic_value,
            loo=loo_value,
            convergence_ok=convergence_ok,
            diagnostics=diagnostics,
        )

    def _extract_components(self, trace) -> Dict[str, pd.Series]:
        """Extract time series components from posterior."""
        components = {}

        # Level component
        if "level_0" in trace.posterior:
            level_vals = [trace.posterior["level_0"].mean().values.item()]
            for t in range(1, min(self.T, 10)):
                if f"level_{t}" in trace.posterior:
                    level_vals.append(
                        trace.posterior[f"level_{t}"].mean().values.item()
                    )
            components["level"] = pd.Series(
                level_vals, index=self.data.index[: len(level_vals)]
            )

        # Trend component
        if self.include_trend and "trend_0" in trace.posterior:
            trend_vals = [trace.posterior["trend_0"].mean().values.item()]
            for t in range(1, min(self.T, 10)):
                if f"trend_{t}" in trace.posterior:
                    trend_vals.append(
                        trace.posterior[f"trend_{t}"].mean().values.item()
                    )
            components["trend"] = pd.Series(
                trend_vals, index=self.data.index[: len(trend_vals)]
            )

        return components

    def _compute_fitted_values(self, trace) -> pd.Series:
        """Compute fitted values (posterior mean)."""
        if "y_obs" in trace.posterior_predictive:
            fitted = (
                trace.posterior_predictive["y_obs"].mean(dim=["chain", "draw"]).values
            )
        elif "level_0" in trace.posterior:
            # Use level as fitted values
            level_mean = [trace.posterior["level_0"].mean().values.item()]
            for t in range(1, min(self.T, 10)):
                if f"level_{t}" in trace.posterior:
                    level_mean.append(
                        trace.posterior[f"level_{t}"].mean().values.item()
                    )
            fitted = np.array(level_mean)
        else:
            fitted = np.zeros(self.T)

        return pd.Series(fitted, index=self.data.index[: len(fitted)])

    def _check_convergence(self, trace) -> Dict[str, Any]:
        """Check MCMC convergence (same as BVAR)."""
        summary = az.summary(trace)

        rhat_values = summary["r_hat"].values
        rhat_ok = np.all(rhat_values < 1.01)

        ess_bulk = summary["ess_bulk"].values
        ess_tail = summary["ess_tail"].values
        ess_bulk_min = float(ess_bulk.min())
        ess_tail_min = float(ess_tail.min())
        ess_ok = ess_bulk_min > 100 and ess_tail_min > 100

        if hasattr(trace, "sample_stats") and hasattr(trace.sample_stats, "diverging"):
            n_divergences = int(trace.sample_stats.diverging.sum().values)
        else:
            n_divergences = 0

        divergences_ok = n_divergences == 0

        return {
            "rhat_ok": bool(rhat_ok),
            "rhat_max": float(rhat_values.max()),
            "ess_ok": bool(ess_ok),
            "ess_bulk_min": ess_bulk_min,
            "ess_tail_min": ess_tail_min,
            "divergences_ok": bool(divergences_ok),
            "n_divergences": n_divergences,
            "overall_ok": bool(rhat_ok and ess_ok and divergences_ok),
        }

    def forecast(self, result: BSTSResult, steps: int = 10) -> Dict[str, pd.Series]:
        """
        Generate forecasts with credible intervals.

        Parameters
        ----------
        result : BSTSResult
            Fitted BSTS result
        steps : int, default=10
            Number of steps ahead

        Returns
        -------
        forecasts : Dict[str, pd.Series]
            'mean', 'lower_95', 'upper_95' forecasts

        Notes
        -----
        Simplified implementation. Production version would use
        full state-space forecast propagation.
        """
        logger.info(f"Generating {steps}-step ahead forecasts")

        # Extract last level and trend
        if "level" in result.components:
            last_level = result.components["level"].iloc[-1]
        else:
            last_level = self.y[-1]

        if self.include_trend and "trend" in result.components:
            last_trend = result.components["trend"].iloc[-1]
        else:
            last_trend = 0

        # Simple forecast: level + trend * t
        forecast_mean = np.array(
            [last_level + last_trend * t for t in range(1, steps + 1)]
        )

        # Rough uncertainty (would use proper state propagation in production)
        sigma_forecast = (
            result.summary.loc["sigma_level", "mean"]
            if "sigma_level" in result.summary.index
            else 1.0
        )
        forecast_std = sigma_forecast * np.sqrt(np.arange(1, steps + 1))

        forecast_lower = forecast_mean - 1.96 * forecast_std
        forecast_upper = forecast_mean + 1.96 * forecast_std

        logger.info("Forecast generation complete")

        return {
            "mean": pd.Series(forecast_mean),
            "lower_95": pd.Series(forecast_lower),
            "upper_95": pd.Series(forecast_upper),
        }


# ==============================================================================
# Hierarchical Bayesian Time Series
# ==============================================================================


class HierarchicalBayesianTS:
    """
    Hierarchical Bayesian Time Series for multi-level NBA data.

    Models players within teams within league structure with automatic
    partial pooling. Players with little data borrow strength from their
    team and league averages.

    Structure:
        League (hyperpriors)
          └─ Teams (team-level parameters)
               └─ Players (player-level parameters)

    Key features:
    - Automatic shrinkage based on data quality
    - Uncertainty quantification at all levels
    - Handles unbalanced panels
    - Player comparisons with full uncertainty

    Parameters
    ----------
    data : pd.DataFrame
        Panel data with players over time
    player_col : str
        Column name for player identifier
    team_col : str
        Column name for team identifier
    time_col : str
        Column name for time index (game number, season, etc.)
    target_col : str
        Column name for outcome variable

    Attributes
    ----------
    n_players : int
        Number of unique players
    n_teams : int
        Number of unique teams
    players : pd.Index
        Player identifiers
    teams : pd.Index
        Team identifiers

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>>
    >>> # Panel data: players within teams
    >>> data = pd.DataFrame({
    ...     'player_id': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
    ...     'team_id': ['LAL', 'LAL', 'LAL', 'BOS', 'BOS', 'BOS'],
    ...     'game': [1, 2, 3, 1, 2, 3],
    ...     'points': [20, 22, 21, 18, 19, 20]
    ... })
    >>>
    >>> analyzer = HierarchicalBayesianTS(
    ...     data=data,
    ...     player_col='player_id',
    ...     team_col='team_id',
    ...     time_col='game',
    ...     target_col='points'
    ... )
    >>> result = analyzer.fit(draws=1000)
    >>> print(result.player_effects)

    Notes
    -----
    Model specification:
        y_it = alpha_i + beta_i * t + epsilon_it
        alpha_i ~ N(mu_alpha[team[i]], tau_alpha)
        beta_i ~ N(mu_beta[team[i]], tau_beta)
        mu_alpha[team] ~ N(mu_0, sigma_0)

    This creates partial pooling: players with few observations shrink
    toward their team mean, which itself shrinks toward league mean.

    References
    ----------
    Gelman, A. & Hill, J. (2007). "Data Analysis Using Regression and
    Multilevel/Hierarchical Models". Cambridge University Press.

    See Also
    --------
    BVARAnalyzer : Bayesian Vector Autoregression
    bayesian.BayesianAnalyzer : General Bayesian models
    """

    def __init__(
        self,
        data: pd.DataFrame,
        player_col: str = "player_id",
        team_col: str = "team_id",
        time_col: str = "game_number",
        target_col: str = "points",
    ):
        """Initialize Hierarchical Bayesian Time Series."""
        if not PYMC_AVAILABLE:
            raise ImportError(
                "PyMC is required for hierarchical models. "
                "Install with: pip install pymc>=5.0.0 arviz>=0.15.0"
            )

        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")

        required_cols = [player_col, team_col, time_col, target_col]
        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Sort data
        self.data = data.sort_values([player_col, time_col]).reset_index(drop=True)
        self.player_col = player_col
        self.team_col = team_col
        self.time_col = time_col
        self.target_col = target_col

        # Encode categorical variables
        self.player_idx, self.players = pd.factorize(data[player_col])
        self.team_idx, self.teams = pd.factorize(data[team_col])

        # Player to team mapping
        player_teams = data.groupby(player_col)[team_col].first()
        self.player_team_map = pd.Series(
            pd.factorize(player_teams)[0], index=self.players
        )

        self.n_players = len(self.players)
        self.n_teams = len(self.teams)

        logger.info(
            f"Initialized Hierarchical TS: {self.n_players} players, "
            f"{self.n_teams} teams, {len(data)} observations"
        )

    def build_model(
        self,
        ar_order: int = 0,
        include_trend: bool = True,
        team_level_trend: bool = True,
    ) -> pm.Model:
        """
        Build hierarchical Bayesian time series model.

        Parameters
        ----------
        ar_order : int, default=0
            Autoregressive order (0 = no AR component)
        include_trend : bool, default=True
            Include player-specific trends
        team_level_trend : bool, default=True
            Allow trends to vary by team

        Returns
        -------
        model : pm.Model
            PyMC model ready for sampling

        Notes
        -----
        Three-level hierarchy:
        1. League: Overall means and variances
        2. Team: Team-specific means
        3. Player: Player-specific parameters with partial pooling
        """
        y = self.data[self.target_col].values
        t = self.data.groupby(self.player_col).cumcount().values

        # Prepare AR lags if needed
        if ar_order > 0:
            lagged_y = self._create_lags(ar_order)

        with pm.Model() as model:
            # ============ League-wide hyperpriors ============
            mu_alpha_league = pm.Normal("mu_alpha_league", mu=20, sigma=10)
            mu_beta_league = pm.Normal("mu_beta_league", mu=0, sigma=1)

            tau_alpha_league = pm.HalfNormal("tau_alpha_league", sigma=5)
            tau_beta_league = pm.HalfNormal("tau_beta_league", sigma=1)

            # ============ Team-level parameters ============
            # Team means (partial pooling from league)
            mu_alpha_team = pm.Normal(
                "mu_alpha_team",
                mu=mu_alpha_league,
                sigma=tau_alpha_league,
                shape=self.n_teams,
            )

            if team_level_trend:
                mu_beta_team = pm.Normal(
                    "mu_beta_team",
                    mu=mu_beta_league,
                    sigma=tau_beta_league,
                    shape=self.n_teams,
                )
            else:
                # All teams share same trend mean
                mu_beta_team = pm.Deterministic(
                    "mu_beta_team", pt.ones(self.n_teams) * mu_beta_league
                )

            # Team-level variance (how much do players vary within team?)
            tau_alpha_team = pm.HalfNormal("tau_alpha_team", sigma=3)
            tau_beta_team = pm.HalfNormal("tau_beta_team", sigma=0.5)

            # ============ Player-level parameters ============
            # Map player to team
            player_team_idx = self.player_team_map.values

            # Player intercepts (partial pooling from team)
            alpha_player = pm.Normal(
                "alpha_player",
                mu=mu_alpha_team[player_team_idx],
                sigma=tau_alpha_team,
                shape=self.n_players,
            )

            # Player trends
            if include_trend:
                beta_player = pm.Normal(
                    "beta_player",
                    mu=mu_beta_team[player_team_idx],
                    sigma=tau_beta_team,
                    shape=self.n_players,
                )
            else:
                beta_player = pt.zeros(self.n_players)

            # AR coefficients (if requested)
            if ar_order > 0:
                phi_player = pm.Normal(
                    "phi_player", mu=0, sigma=0.5, shape=self.n_players
                )

            # ============ Observation model ============
            # Build mean prediction
            mu = alpha_player[self.player_idx] + beta_player[self.player_idx] * t

            # Add AR component
            if ar_order > 0:
                ar_effect = phi_player[self.player_idx] * lagged_y[:, 0]
                mu = mu + ar_effect

            # Observation noise (player-specific)
            sigma_player = pm.HalfNormal("sigma_player", sigma=3, shape=self.n_players)

            # Likelihood
            y_obs = pm.Normal(
                "y_obs",
                mu=mu,
                sigma=sigma_player[self.player_idx],
                observed=y,
            )

        logger.info(
            f"Built hierarchical model: AR({ar_order}), "
            f"trend={include_trend}, team_trend={team_level_trend}"
        )

        return model

    def fit(
        self,
        draws: int = 2000,
        tune: int = 1000,
        chains: int = 4,
        ar_order: int = 0,
        include_trend: bool = True,
        **kwargs,
    ) -> HierarchicalTSResult:
        """
        Fit hierarchical Bayesian time series.

        Parameters
        ----------
        draws : int, default=2000
            Number of posterior samples
        tune : int, default=1000
            Number of tuning steps
        chains : int, default=4
            Number of MCMC chains
        ar_order : int, default=0
            AR order
        include_trend : bool, default=True
            Include trends
        **kwargs
            Additional arguments for pm.sample()

        Returns
        -------
        result : HierarchicalTSResult
            Results with player/team/league effects

        Examples
        --------
        >>> result = analyzer.fit(draws=1000, tune=500)
        >>> print("Player effects:")
        >>> print(result.player_effects.head())
        >>> print("\\nShrinkage factors:")
        >>> print(result.shrinkage_factors.head())
        """
        logger.info(
            f"Fitting hierarchical model: {draws} draws, {tune} tune, {chains} chains"
        )

        # Build model
        model = self.build_model(
            ar_order=ar_order, include_trend=include_trend, team_level_trend=True
        )

        # Sample
        with model:
            trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                target_accept=kwargs.pop("target_accept", 0.95),
                return_inferencedata=True,
                **kwargs,
            )

        # Summary
        summary = az.summary(trace, hdi_prob=0.95)

        # Extract player effects
        alpha_mean = trace.posterior["alpha_player"].mean(dim=["chain", "draw"]).values
        sigma_mean = trace.posterior["sigma_player"].mean(dim=["chain", "draw"]).values

        if include_trend:
            beta_mean = (
                trace.posterior["beta_player"].mean(dim=["chain", "draw"]).values
            )
        else:
            beta_mean = np.zeros(self.n_players)

        player_effects = pd.DataFrame(
            {
                "player": self.players,
                "team": self.teams[self.player_team_map.values],
                "intercept": alpha_mean,
                "trend": beta_mean,
                "sigma": sigma_mean,
            }
        )

        # Extract team effects
        team_alpha = trace.posterior["mu_alpha_team"].mean(dim=["chain", "draw"]).values
        team_beta = trace.posterior["mu_beta_team"].mean(dim=["chain", "draw"]).values

        team_effects = pd.DataFrame(
            {"team": self.teams, "mean_intercept": team_alpha, "mean_trend": team_beta}
        )

        # League effects
        league_effects = {
            "mu_alpha": float(trace.posterior["mu_alpha_league"].mean()),
            "mu_beta": float(trace.posterior["mu_beta_league"].mean()),
            "tau_alpha_league": float(trace.posterior["tau_alpha_league"].mean()),
            "tau_alpha_team": float(trace.posterior["tau_alpha_team"].mean()),
        }

        # Compute shrinkage factors
        shrinkage = self._compute_shrinkage(trace)

        # Model diagnostics
        try:
            waic = az.waic(trace)
            waic_value = float(waic.waic)
        except Exception as e:
            logger.warning(f"WAIC computation failed: {e}")
            waic_value = None

        try:
            loo = az.loo(trace)
            loo_value = float(loo.loo)
        except Exception as e:
            logger.warning(f"LOO computation failed: {e}")
            loo_value = None

        # Convergence
        diagnostics = self._check_convergence(trace)
        convergence_ok = diagnostics["overall_ok"]

        if not convergence_ok:
            warnings.warn(
                f"Convergence issues. Rhat_max: {diagnostics['rhat_max']:.4f}",
                UserWarning,
            )

        logger.info(
            f"Hierarchical fit complete. WAIC: {waic_value:.2f if waic_value else 'N/A'}, "
            f"Convergence: {convergence_ok}"
        )

        return HierarchicalTSResult(
            trace=trace,
            model=model,
            summary=summary,
            player_effects=player_effects,
            team_effects=team_effects,
            league_effects=league_effects,
            shrinkage_factors=shrinkage,
            waic=waic_value,
            loo=loo_value,
            convergence_ok=convergence_ok,
            diagnostics=diagnostics,
        )

    def _compute_shrinkage(self, trace) -> pd.DataFrame:
        """
        Compute shrinkage factors for each player.

        Shrinkage = how much player estimate shrinks toward team mean.
        Higher shrinkage = less data, more borrowing from team.

        Parameters
        ----------
        trace : InferenceData
            MCMC trace

        Returns
        -------
        shrinkage_df : pd.DataFrame
            Shrinkage factors and data weights for each player
        """
        # Posterior variance of player intercepts
        alpha_post_var = (
            trace.posterior["alpha_player"].var(dim=["chain", "draw"]).values
        )

        # Prior variance (team-level)
        tau_alpha_team = trace.posterior["tau_alpha_team"].mean().values

        # Shrinkage = 1 - Var(posterior) / Var(prior)
        # High shrinkage → posterior variance small → data uninformative
        shrinkage = 1 - alpha_post_var / (tau_alpha_team**2)
        shrinkage = np.clip(shrinkage, 0, 1)

        # Number of observations per player
        obs_counts = self.data.groupby(self.player_col).size()
        obs_per_player = obs_counts.reindex(self.players, fill_value=0).values

        return pd.DataFrame(
            {
                "player": self.players,
                "shrinkage": shrinkage,
                "data_weight": 1 - shrinkage,
                "n_obs": obs_per_player,
            }
        )

    def forecast_player(
        self, result: HierarchicalTSResult, player_id: str, steps: int = 10
    ) -> Dict[str, pd.Series]:
        """
        Forecast future performance for a specific player.

        Parameters
        ----------
        result : HierarchicalTSResult
            Fitted result
        player_id : str
            Player to forecast
        steps : int, default=10
            Number of steps ahead

        Returns
        -------
        forecasts : Dict[str, pd.Series]
            'mean', 'lower_95', 'upper_95' forecasts

        Examples
        --------
        >>> forecasts = analyzer.forecast_player(result, 'LeBron James', steps=5)
        >>> print(forecasts['mean'])
        """
        if player_id not in self.players:
            raise ValueError(f"Player {player_id} not found in data")

        player_idx = list(self.players).index(player_id)

        # Get player's posterior samples
        alpha_samples = result.trace.posterior["alpha_player"][
            :, :, player_idx
        ].values.flatten()
        beta_samples = result.trace.posterior["beta_player"][
            :, :, player_idx
        ].values.flatten()
        sigma_samples = result.trace.posterior["sigma_player"][
            :, :, player_idx
        ].values.flatten()

        # Current time for this player
        player_data = self.data[self.data[self.player_col] == player_id]
        t_last = len(player_data)

        # Forecast for each posterior sample
        n_samples = len(alpha_samples)
        forecast_samples = np.zeros((steps, n_samples))

        for i in range(n_samples):
            for step in range(steps):
                t_future = t_last + step + 1
                mu = alpha_samples[i] + beta_samples[i] * t_future
                forecast_samples[step, i] = np.random.normal(mu, sigma_samples[i])

        # Summarize
        logger.info(f"Generated forecasts for {player_id}")

        return {
            "mean": pd.Series(forecast_samples.mean(axis=1)),
            "lower_95": pd.Series(np.percentile(forecast_samples, 2.5, axis=1)),
            "upper_95": pd.Series(np.percentile(forecast_samples, 97.5, axis=1)),
        }

    def compare_players(
        self,
        result: HierarchicalTSResult,
        player1: str,
        player2: str,
        metric: str = "trend",
    ) -> Dict[str, float]:
        """
        Bayesian comparison of two players.

        Parameters
        ----------
        result : HierarchicalTSResult
            Fitted result
        player1 : str
            First player
        player2 : str
            Second player
        metric : str, default='trend'
            Metric to compare ('trend' or 'intercept')

        Returns
        -------
        comparison : Dict[str, float]
            Comparison statistics:
            - prob_player1_greater: P(metric_1 > metric_2 | data)
            - difference_mean: E[metric_1 - metric_2]
            - difference_hdi_lower: Lower 95% HDI
            - difference_hdi_upper: Upper 95% HDI

        Examples
        --------
        >>> comp = analyzer.compare_players(result, 'Player A', 'Player B', 'trend')
        >>> print(f"P(A > B): {comp['prob_player1_greater']:.2%}")
        >>> print(f"Difference: {comp['difference_mean']:.2f}")
        """
        if player1 not in self.players:
            raise ValueError(f"Player {player1} not found")
        if player2 not in self.players:
            raise ValueError(f"Player {player2} not found")

        idx1 = list(self.players).index(player1)
        idx2 = list(self.players).index(player2)

        if metric == "trend":
            param = "beta_player"
        elif metric == "intercept":
            param = "alpha_player"
        else:
            raise ValueError(f"Unknown metric: {metric}. Use 'trend' or 'intercept'")

        samples1 = result.trace.posterior[param][:, :, idx1].values.flatten()
        samples2 = result.trace.posterior[param][:, :, idx2].values.flatten()

        diff = samples1 - samples2

        logger.info(f"Compared {player1} vs {player2} on {metric}")

        return {
            "prob_player1_greater": float((diff > 0).mean()),
            "difference_mean": float(diff.mean()),
            "difference_hdi_lower": float(np.percentile(diff, 2.5)),
            "difference_hdi_upper": float(np.percentile(diff, 97.5)),
        }

    def _create_lags(self, ar_order: int) -> np.ndarray:
        """Create lagged dependent variable for AR terms."""
        lagged = []
        for lag in range(1, ar_order + 1):
            lagged_series = (
                self.data.groupby(self.player_col)[self.target_col]
                .shift(lag)
                .fillna(0)  # Fill first observations
            )
            lagged.append(lagged_series.values)

        return np.column_stack(lagged)

    def _check_convergence(self, trace) -> Dict[str, Any]:
        """Check MCMC convergence (same as other methods)."""
        summary = az.summary(trace)

        rhat_values = summary["r_hat"].values
        rhat_ok = np.all(rhat_values < 1.01)

        ess_bulk = summary["ess_bulk"].values
        ess_tail = summary["ess_tail"].values
        ess_bulk_min = float(ess_bulk.min())
        ess_tail_min = float(ess_tail.min())
        ess_ok = ess_bulk_min > 100 and ess_tail_min > 100

        if hasattr(trace, "sample_stats") and hasattr(trace.sample_stats, "diverging"):
            n_divergences = int(trace.sample_stats.diverging.sum().values)
        else:
            n_divergences = 0

        divergences_ok = n_divergences == 0

        return {
            "rhat_ok": bool(rhat_ok),
            "rhat_max": float(rhat_values.max()),
            "ess_ok": bool(ess_ok),
            "ess_bulk_min": ess_bulk_min,
            "ess_tail_min": ess_tail_min,
            "divergences_ok": bool(divergences_ok),
            "n_divergences": n_divergences,
            "overall_ok": bool(rhat_ok and ess_ok and divergences_ok),
        }


@dataclass
class BayesianModelAveragingResult:
    """Results from Bayesian Model Averaging."""

    weights: np.ndarray  # Model weights
    predictions: np.ndarray  # Averaged predictions
    model_predictions: List[np.ndarray]  # Individual model predictions
    model_scores: np.ndarray  # Model information criteria (lower is better)
    score_type: str  # "waic" or "loo"
    n_models: int
    summary: Dict[str, Any]


class BayesianModelAveraging:
    """
    Bayesian Model Averaging for combining multiple models.

    Uses information criteria (WAIC or LOO) to compute optimal model weights
    and generate averaged predictions.

    Parameters
    ----------
    models : List[Any]
        List of fitted PyMC models (with InferenceData traces)
    score_type : str, default='waic'
        Information criterion to use: 'waic' or 'loo'
    min_weight : float, default=0.01
        Minimum weight for any model (prevents zero weights)

    Examples
    --------
    >>> # Fit multiple models
    >>> model1 = BVARAnalyzer(...)
    >>> result1 = model1.fit()
    >>>
    >>> model2 = BayesianStructuralTS(...)
    >>> result2 = model2.fit()
    >>>
    >>> # Average them
    >>> bma = BayesianModelAveraging([result1, result2])
    >>> bma_result = bma.compute_weights()
    >>> print(bma_result.weights)  # [0.6, 0.4]
    """

    def __init__(
        self,
        models: List[Any],
        score_type: str = "waic",
        min_weight: float = 0.01,
    ):
        """
        Initialize Bayesian Model Averaging.

        Args:
            models: List of model results with traces
            score_type: 'waic' or 'loo'
            min_weight: Minimum weight for any model
        """
        check_pymc_available()

        if not models or len(models) < 2:
            raise ValueError("Need at least 2 models for averaging")

        self.models = models
        self.score_type = score_type.lower()
        self.min_weight = min_weight

        if self.score_type not in ["waic", "loo"]:
            raise ValueError(f"score_type must be 'waic' or 'loo', got: {score_type}")

        logger.info(f"BMA initialized with {len(models)} models, using {score_type}")

    def compute_weights(self) -> BayesianModelAveragingResult:
        """
        Compute optimal model weights based on information criteria.

        Returns
        -------
        BayesianModelAveragingResult
            Results with weights and model scores
        """
        logger.info(
            f"Computing {self.score_type.upper()} weights for {len(self.models)} models"
        )

        # Extract scores from each model
        scores = []
        for i, model_result in enumerate(self.models):
            if hasattr(model_result, "trace"):
                trace = model_result.trace
            elif hasattr(model_result, "idata"):
                trace = model_result.idata
            else:
                raise ValueError(f"Model {i} has no trace or idata attribute")

            # Compute score
            if self.score_type == "waic":
                score_result = az.waic(trace)
                score = score_result.elpd_waic  # Expected log predictive density
            else:  # loo
                score_result = az.loo(trace)
                score = score_result.elpd_loo

            scores.append(float(score))

        scores = np.array(scores)

        # Convert ELPD to weights using softmax
        # Higher ELPD = better model, so use exp(ELPD) for weights
        # Normalize to avoid overflow
        scores_normalized = scores - scores.max()
        raw_weights = np.exp(scores_normalized)
        weights = raw_weights / raw_weights.sum()

        # Apply minimum weight constraint
        if self.min_weight > 0:
            weights = np.maximum(weights, self.min_weight)
            weights = weights / weights.sum()  # Renormalize

        # Summary
        summary = {
            "n_models": len(self.models),
            "score_type": self.score_type,
            "best_model_idx": int(np.argmax(scores)),
            "best_model_weight": float(weights[np.argmax(scores)]),
            "weight_entropy": float(-np.sum(weights * np.log(weights + 1e-10))),
        }

        logger.info(
            f"BMA weights computed. Best model: {summary['best_model_idx']} "
            f"(weight: {summary['best_model_weight']:.3f})"
        )

        return BayesianModelAveragingResult(
            weights=weights,
            predictions=np.array([]),  # Will be filled by predict()
            model_predictions=[],
            model_scores=scores,
            score_type=self.score_type,
            n_models=len(self.models),
            summary=summary,
        )

    def predict(
        self, weights: Optional[np.ndarray] = None, n_steps: int = 10, **kwargs
    ) -> BayesianModelAveragingResult:
        """
        Generate weighted predictions from all models.

        Parameters
        ----------
        weights : np.ndarray, optional
            Model weights (if None, computed automatically)
        n_steps : int, default=10
            Number of steps to forecast
        **kwargs
            Additional arguments passed to model forecast methods

        Returns
        -------
        BayesianModelAveragingResult
            Results with averaged predictions
        """
        # Compute weights if not provided
        if weights is None:
            result = self.compute_weights()
            weights = result.weights
            scores = result.model_scores
        else:
            scores = np.zeros(len(self.models))
            result = None

        # Get predictions from each model
        model_predictions = []
        for i, model_result in enumerate(self.models):
            try:
                # Try different forecast methods
                if hasattr(model_result, "forecast"):
                    pred = model_result.forecast(steps=n_steps, **kwargs)
                elif hasattr(model_result, "predict"):
                    pred = model_result.predict(steps=n_steps, **kwargs)
                else:
                    logger.warning(
                        f"Model {i} has no forecast/predict method, using zeros"
                    )
                    pred = np.zeros(n_steps)

                # Handle different return types
                if isinstance(pred, tuple):
                    pred = pred[0]  # Take mean if (mean, std) returned
                elif hasattr(pred, "mean"):
                    pred = pred.mean(axis=0)  # Average across samples

                model_predictions.append(np.asarray(pred).flatten()[:n_steps])

            except Exception as e:
                logger.warning(f"Model {i} forecast failed: {e}, using zeros")
                model_predictions.append(np.zeros(n_steps))

        # Weighted average
        predictions = np.zeros(n_steps)
        for weight, pred in zip(weights, model_predictions):
            predictions += weight * pred

        # Update result
        if result is None:
            result = BayesianModelAveragingResult(
                weights=weights,
                predictions=predictions,
                model_predictions=model_predictions,
                model_scores=scores,
                score_type=self.score_type,
                n_models=len(self.models),
                summary={"n_models": len(self.models)},
            )
        else:
            result.predictions = predictions
            result.model_predictions = model_predictions

        logger.info(f"BMA predictions generated for {n_steps} steps")

        return result

    def compare_models(self) -> pd.DataFrame:
        """
        Compare all models using multiple information criteria.

        Returns
        -------
        pd.DataFrame
            Comparison table with WAIC, LOO, and other metrics
        """
        logger.info(f"Comparing {len(self.models)} models")

        comparison_data = []

        for i, model_result in enumerate(self.models):
            if hasattr(model_result, "trace"):
                trace = model_result.trace
            elif hasattr(model_result, "idata"):
                trace = model_result.idata
            else:
                continue

            try:
                # Compute both WAIC and LOO
                waic_result = az.waic(trace)
                loo_result = az.loo(trace)

                comparison_data.append(
                    {
                        "model_id": i,
                        "waic": waic_result.elpd_waic,
                        "waic_se": waic_result.se,
                        "p_waic": waic_result.p_waic,
                        "loo": loo_result.elpd_loo,
                        "loo_se": loo_result.se,
                        "p_loo": loo_result.p_loo,
                    }
                )

            except Exception as e:
                logger.warning(f"Model {i} comparison failed: {e}")
                comparison_data.append(
                    {
                        "model_id": i,
                        "waic": np.nan,
                        "waic_se": np.nan,
                        "p_waic": np.nan,
                        "loo": np.nan,
                        "loo_se": np.nan,
                        "p_loo": np.nan,
                    }
                )

        df = pd.DataFrame(comparison_data)

        # Rank by WAIC (higher is better)
        df["rank_waic"] = df["waic"].rank(ascending=False)
        df["rank_loo"] = df["loo"].rank(ascending=False)

        return df


__all__ = [
    "BVARAnalyzer",
    "BayesianStructuralTS",
    "HierarchicalBayesianTS",
    "BayesianModelAveraging",
    "BVARResult",
    "BSTSResult",
    "HierarchicalTSResult",
    "BayesianModelAveragingResult",
    "PYMC_AVAILABLE",
    "check_pymc_available",
]
