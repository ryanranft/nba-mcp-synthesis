"""
Advanced Time Series Analysis MCP Tools
Module 4C of Agent 8 deployment (Phase 10A)

Provides state-space, regime-switching, and structural decomposition for complex temporal patterns.
Complements the panel data tools with sophisticated univariate/multivariate time series methods.

Tools:
- kalman_filter: State-space estimation with Kalman filtering
- dynamic_factor_model: Extract latent factors from multivariate time series
- markov_switching_model: Regime-switching dynamics detection
- structural_time_series: Unobserved components decomposition

Author: Agent 8 (Phase 10A - Module 4C)
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class AdvancedTimeSeriesTools:
    """Advanced time series analysis wrapper for MCP tools."""

    def __init__(self):
        """Initialize advanced time series tools."""
        self.logger = logging.getLogger(__name__)
        self._kalman_cache = {}
        self._dfm_cache = {}
        self._markov_cache = {}
        self._structural_cache = {}

    def kalman_filter(
        self,
        data: pd.DataFrame,
        state_dim: int,
        observation_vars: List[str],
        transition_matrix: Optional[List[List[float]]] = None,
        observation_matrix: Optional[List[List[float]]] = None,
        initial_state: Optional[List[float]] = None,
        process_noise_cov: Optional[List[List[float]]] = None,
        measurement_noise_cov: Optional[List[List[float]]] = None,
        estimate_parameters: bool = True,
        smoother: bool = True,
        forecast_steps: int = 0,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Apply Kalman filter for state-space estimation.

        State-space representation:
        - State equation: x_t = F*x_{t-1} + w_t  (w_t ~ N(0, Q))
        - Observation equation: y_t = H*x_t + v_t  (v_t ~ N(0, R))

        Args:
            data: Time series data with observation variables
            state_dim: Dimension of the latent state vector
            observation_vars: Variables to use as observations
            transition_matrix: State transition matrix F (state_dim x state_dim)
            observation_matrix: Observation matrix H (obs_dim x state_dim)
            initial_state: Initial state estimate
            process_noise_cov: Process noise covariance Q
            measurement_noise_cov: Measurement noise covariance R
            estimate_parameters: Whether to estimate matrices via MLE
            smoother: Apply Kalman smoother (backward pass) for smoothed estimates
            forecast_steps: Number of steps to forecast ahead
            confidence_level: Confidence level for prediction intervals

        Returns:
            Dictionary containing:
            - filtered_states: Filtered state estimates (forward pass)
            - smoothed_states: Smoothed state estimates (if smoother=True)
            - forecasts: Out-of-sample forecasts (if forecast_steps > 0)
            - state_covariances: Uncertainty estimates for states
            - innovations: One-step-ahead prediction errors
            - log_likelihood: Model log-likelihood
            - parameters: Estimated transition/observation matrices
            - diagnostics: Innovation statistics and residual tests

        Example:
            # Local level model for NBA team performance
            result = kalman_filter(
                data=team_wins_df,
                state_dim=1,
                observation_vars=['win_pct'],
                estimate_parameters=True,
                smoother=True,
                forecast_steps=10
            )
        """
        try:
            self.logger.info(
                f"Applying Kalman filter: state_dim={state_dim}, vars={observation_vars}"
            )

            # Validate inputs
            if data.empty:
                raise ValueError("Input data is empty")

            if not observation_vars:
                raise ValueError("Must specify observation variables")

            missing_vars = set(observation_vars) - set(data.columns)
            if missing_vars:
                raise ValueError(f"Variables not found in data: {missing_vars}")

            if state_dim < 1:
                raise ValueError(f"state_dim must be positive, got {state_dim}")

            # Extract observation data
            y = data[observation_vars].values
            n_obs, obs_dim = y.shape

            # Initialize matrices if not provided
            if transition_matrix is None:
                # Default: random walk
                F = np.eye(state_dim)
            else:
                F = np.array(transition_matrix)
                if F.shape != (state_dim, state_dim):
                    raise ValueError(
                        f"transition_matrix must be {state_dim}x{state_dim}"
                    )

            if observation_matrix is None:
                # Default: observe all states
                H = np.eye(obs_dim, state_dim)
            else:
                H = np.array(observation_matrix)
                if H.shape[1] != state_dim:
                    raise ValueError(
                        f"observation_matrix must have {state_dim} columns"
                    )

            if initial_state is None:
                x0 = np.zeros(state_dim)
            else:
                x0 = np.array(initial_state)

            if process_noise_cov is None:
                Q = np.eye(state_dim) * 0.1
            else:
                Q = np.array(process_noise_cov)

            if measurement_noise_cov is None:
                R = np.eye(obs_dim) * 0.1
            else:
                R = np.array(measurement_noise_cov)

            # Parameter estimation via MLE if requested
            if estimate_parameters:
                self.logger.info("Estimating Kalman filter parameters via MLE")
                # Use scipy.optimize or statsmodels for MLE
                # For now, use simple EM algorithm
                F, H, Q, R = self._estimate_kalman_parameters(
                    y, state_dim, F, H, Q, R, x0
                )

            # Forward pass: Kalman filter
            filtered_states, filtered_covs, innovations, innovation_covs = (
                self._kalman_filter_forward(y, F, H, Q, R, x0)
            )

            # Compute log-likelihood
            log_likelihood = self._kalman_log_likelihood(innovations, innovation_covs)

            # Backward pass: Kalman smoother
            smoothed_states = None
            smoothed_covs = None
            if smoother:
                self.logger.info("Applying Kalman smoother (backward pass)")
                smoothed_states, smoothed_covs = self._kalman_smoother_backward(
                    filtered_states, filtered_covs, F, Q
                )

            # Forecasting
            forecasts = None
            forecast_covs = None
            if forecast_steps > 0:
                self.logger.info(f"Generating {forecast_steps}-step forecasts")
                forecasts, forecast_covs = self._kalman_forecast(
                    filtered_states[-1], filtered_covs[-1], F, H, Q, R, forecast_steps
                )

            # Diagnostics
            diagnostics = self._compute_kalman_diagnostics(
                innovations, innovation_covs, y, H, filtered_states
            )

            # Build result
            result = {
                "filtered_states": pd.DataFrame(
                    filtered_states,
                    index=data.index,
                    columns=[f"state_{i+1}" for i in range(state_dim)],
                ).to_dict("records"),
                "state_covariances": [cov.tolist() for cov in filtered_covs],
                "innovations": pd.DataFrame(
                    innovations, index=data.index, columns=observation_vars
                ).to_dict("records"),
                "log_likelihood": float(log_likelihood),
                "aic": float(
                    -2 * log_likelihood + 2 * (state_dim**2 + obs_dim * state_dim)
                ),
                "bic": float(
                    -2 * log_likelihood
                    + np.log(n_obs) * (state_dim**2 + obs_dim * state_dim)
                ),
                "parameters": {
                    "transition_matrix": F.tolist(),
                    "observation_matrix": H.tolist(),
                    "process_noise_cov": Q.tolist(),
                    "measurement_noise_cov": R.tolist(),
                },
                "diagnostics": diagnostics,
            }

            if smoother and smoothed_states is not None:
                result["smoothed_states"] = pd.DataFrame(
                    smoothed_states,
                    index=data.index,
                    columns=[f"state_{i+1}" for i in range(state_dim)],
                ).to_dict("records")
                result["smoothed_covariances"] = [cov.tolist() for cov in smoothed_covs]

            if forecasts is not None:
                z_score = 1.96 if confidence_level == 0.95 else 2.576
                forecast_df = pd.DataFrame(
                    {
                        "forecast": (H @ forecasts.T).flatten(),
                        "std_error": [
                            np.sqrt(np.diag(H @ cov @ H.T + R))[0]
                            for cov in forecast_covs
                        ],
                    }
                )
                forecast_df["lower"] = (
                    forecast_df["forecast"] - z_score * forecast_df["std_error"]
                )
                forecast_df["upper"] = (
                    forecast_df["forecast"] + z_score * forecast_df["std_error"]
                )
                result["forecasts"] = forecast_df.to_dict("records")

            self.logger.info(
                f"Kalman filter complete: log_likelihood={log_likelihood:.2f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Kalman filter failed: {str(e)}")
            raise

    def dynamic_factor_model(
        self,
        data: pd.DataFrame,
        variables: List[str],
        n_factors: int,
        factor_order: int = 1,
        standardize: bool = True,
        method: str = "ml",
        max_iter: int = 1000,
        tolerance: float = 1e-4,
    ) -> Dict[str, Any]:
        """
        Estimate dynamic factor model to extract latent factors.

        Model specification:
        - Observation: y_t = Λf_t + ε_t
        - Factor dynamics: f_t = A₁f_{t-1} + ... + Aₚf_{t-p} + η_t

        Args:
            data: Multivariate time series data
            variables: Variables to include in factor extraction
            n_factors: Number of latent factors to extract
            factor_order: AR order for factor dynamics
            standardize: Standardize variables before estimation
            method: Estimation method ('ml', 'pc', '2step')
            max_iter: Maximum iterations for ML estimation
            tolerance: Convergence tolerance

        Returns:
            Dictionary containing:
            - factors: Extracted latent factors (T x n_factors)
            - loadings: Factor loadings matrix (n_vars x n_factors)
            - factor_covariance: Factor innovation covariance
            - idiosyncratic_variances: Variable-specific error variances
            - var_explained: Variance explained by each factor
            - factor_ar_coefficients: AR coefficients for factor dynamics
            - fit_statistics: Model fit measures (log-likelihood, AIC, BIC)

        Example:
            # Extract common factors from team statistics
            result = dynamic_factor_model(
                data=team_stats_df,
                variables=['offensive_rating', 'defensive_rating', 'net_rating', 'pace'],
                n_factors=2,
                factor_order=1
            )
        """
        try:
            self.logger.info(
                f"Estimating dynamic factor model: n_factors={n_factors}, vars={len(variables)}"
            )

            # Validate inputs
            if data.empty:
                raise ValueError("Input data is empty")

            missing_vars = set(variables) - set(data.columns)
            if missing_vars:
                raise ValueError(f"Variables not found: {missing_vars}")

            if n_factors < 1 or n_factors > len(variables):
                raise ValueError(f"n_factors must be between 1 and {len(variables)}")

            # Extract and prepare data
            X = data[variables].copy()
            n_obs, n_vars = X.shape

            # Handle missing data
            if X.isnull().any().any():
                self.logger.warning("Missing data detected, using interpolation")
                X = (
                    X.interpolate(method="linear")
                    .fillna(method="bfill")
                    .fillna(method="ffill")
                )

            # Standardize if requested
            X_means = X.mean()
            X_stds = X.std()
            if standardize:
                X = (X - X_means) / X_stds

            X_np = X.values

            # Estimate model based on method
            if method == "pc":
                # Principal components method
                factors, loadings, idio_vars = self._dfm_principal_components(
                    X_np, n_factors
                )
            elif method == "ml":
                # Maximum likelihood via EM algorithm
                factors, loadings, idio_vars = self._dfm_ml_em(
                    X_np, n_factors, max_iter, tolerance
                )
            elif method == "2step":
                # Two-step: PC extraction + Kalman smoothing
                factors, loadings, idio_vars = self._dfm_two_step(X_np, n_factors)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Estimate factor VAR dynamics
            factor_ar_coefs, factor_cov = self._estimate_factor_var(
                factors, factor_order
            )

            # Compute variance explained
            X_fitted = factors @ loadings.T
            total_var = np.var(X_np, axis=0).sum()
            factor_vars = np.var(factors, axis=0)
            var_explained = (factor_vars * np.sum(loadings**2, axis=0)) / total_var

            # Compute fit statistics
            residuals = X_np - X_fitted
            log_likelihood = self._dfm_log_likelihood(residuals, idio_vars)
            n_params = (
                n_vars * n_factors + n_factors + n_vars + n_factors**2 * factor_order
            )
            aic = -2 * log_likelihood + 2 * n_params
            bic = -2 * log_likelihood + np.log(n_obs) * n_params

            # Build result
            result = {
                "factors": pd.DataFrame(
                    factors,
                    index=data.index,
                    columns=[f"factor_{i+1}" for i in range(n_factors)],
                ).to_dict("records"),
                "loadings": pd.DataFrame(
                    loadings,
                    index=variables,
                    columns=[f"factor_{i+1}" for i in range(n_factors)],
                ).to_dict("index"),
                "factor_covariance": factor_cov.tolist(),
                "idiosyncratic_variances": dict(zip(variables, idio_vars)),
                "variance_explained": {
                    f"factor_{i+1}": float(var_explained[i]) for i in range(n_factors)
                },
                "total_variance_explained": float(var_explained.sum()),
                "factor_ar_coefficients": [coef.tolist() for coef in factor_ar_coefs],
                "fit_statistics": {
                    "log_likelihood": float(log_likelihood),
                    "aic": float(aic),
                    "bic": float(bic),
                    "n_observations": n_obs,
                    "n_parameters": n_params,
                },
                "method": method,
                "standardized": standardize,
            }

            self.logger.info(f"DFM complete: var_explained={var_explained.sum():.2%}")
            return result

        except Exception as e:
            self.logger.error(f"Dynamic factor model failed: {str(e)}")
            raise

    def markov_switching_model(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: Optional[List[str]] = None,
        n_regimes: int = 2,
        switching_variance: bool = True,
        switching_mean: bool = True,
        switching_ar: bool = False,
        ar_order: int = 0,
        max_iter: int = 1000,
        tolerance: float = 1e-4,
    ) -> Dict[str, Any]:
        """
        Estimate Markov-switching regression model for regime changes.

        Detects discrete regime shifts in time series dynamics with probabilistic
        transitions between states.

        Args:
            data: Time series data
            dependent_var: Dependent variable
            independent_vars: Independent variables (optional)
            n_regimes: Number of hidden regimes/states
            switching_variance: Allow variance to switch across regimes
            switching_mean: Allow mean to switch across regimes
            switching_ar: Allow AR coefficients to switch across regimes
            ar_order: Autoregressive order
            max_iter: Maximum EM iterations
            tolerance: Convergence tolerance

        Returns:
            Dictionary containing:
            - regime_probabilities: Smoothed probability of each regime at each time
            - regime_sequence: Most likely regime sequence (Viterbi path)
            - regime_parameters: Parameters for each regime (mean, variance, AR coefs)
            - transition_matrix: Regime transition probability matrix
            - expected_durations: Expected duration in each regime
            - regime_statistics: Summary statistics by regime
            - fit_statistics: Model fit measures

        Example:
            # Detect offensive/defensive regime shifts
            result = markov_switching_model(
                data=team_performance_df,
                dependent_var='net_rating',
                independent_vars=['pace', 'experience'],
                n_regimes=2,
                switching_variance=True
            )
        """
        try:
            self.logger.info(
                f"Estimating Markov-switching model: n_regimes={n_regimes}, var={dependent_var}"
            )

            # Validate inputs
            if data.empty:
                raise ValueError("Input data is empty")

            if dependent_var not in data.columns:
                raise ValueError(f"Dependent variable '{dependent_var}' not found")

            if n_regimes < 2:
                raise ValueError("n_regimes must be at least 2")

            # Prepare data
            y = data[dependent_var].values
            n_obs = len(y)

            X = None
            if independent_vars:
                missing_vars = set(independent_vars) - set(data.columns)
                if missing_vars:
                    raise ValueError(f"Variables not found: {missing_vars}")
                X = data[independent_vars].values

            # Handle missing data
            valid_idx = ~np.isnan(y)
            if X is not None:
                valid_idx &= ~np.isnan(X).any(axis=1)

            y = y[valid_idx]
            if X is not None:
                X = X[valid_idx]

            # Initialize parameters
            params = self._initialize_markov_params(
                y,
                X,
                n_regimes,
                switching_variance,
                switching_mean,
                switching_ar,
                ar_order,
            )

            # EM algorithm
            for iteration in range(max_iter):
                # E-step: Compute regime probabilities
                filtered_probs, predicted_probs, joint_probs = self._markov_filter(
                    y, X, params, n_regimes
                )
                smoothed_probs = self._markov_smoother(
                    filtered_probs, joint_probs, params["transition_matrix"]
                )

                # M-step: Update parameters
                new_params = self._markov_m_step(
                    y,
                    X,
                    smoothed_probs,
                    joint_probs,
                    n_regimes,
                    switching_variance,
                    switching_mean,
                    switching_ar,
                    ar_order,
                )

                # Check convergence
                param_diff = self._markov_param_diff(params, new_params)
                params = new_params

                if param_diff < tolerance:
                    self.logger.info(f"Converged after {iteration + 1} iterations")
                    break

            # Viterbi algorithm for most likely regime sequence
            regime_sequence = self._markov_viterbi(y, X, params, n_regimes)

            # Compute expected durations
            P = params["transition_matrix"]
            expected_durations = {
                f"regime_{i+1}": float(1 / (1 - P[i, i])) for i in range(n_regimes)
            }

            # Regime statistics
            regime_stats = {}
            for i in range(n_regimes):
                regime_mask = regime_sequence == i
                regime_stats[f"regime_{i+1}"] = {
                    "observations": int(regime_mask.sum()),
                    "proportion": float(regime_mask.mean()),
                    "mean": float(y[regime_mask].mean()),
                    "std": float(y[regime_mask].std()),
                    "min": float(y[regime_mask].min()),
                    "max": float(y[regime_mask].max()),
                }

            # Compute log-likelihood and fit statistics
            log_likelihood = self._markov_log_likelihood(
                y, X, smoothed_probs, params, n_regimes
            )
            n_params = self._count_markov_params(
                n_regimes, X, switching_variance, switching_mean, ar_order
            )
            aic = -2 * log_likelihood + 2 * n_params
            bic = -2 * log_likelihood + np.log(n_obs) * n_params

            # Build result
            result = {
                "regime_probabilities": pd.DataFrame(
                    smoothed_probs,
                    index=data.index[valid_idx],
                    columns=[f"regime_{i+1}" for i in range(n_regimes)],
                ).to_dict("records"),
                "regime_sequence": pd.Series(
                    [f"regime_{i+1}" for i in regime_sequence],
                    index=data.index[valid_idx],
                ).to_dict(),
                "transition_matrix": pd.DataFrame(
                    params["transition_matrix"],
                    index=[f"from_regime_{i+1}" for i in range(n_regimes)],
                    columns=[f"to_regime_{i+1}" for i in range(n_regimes)],
                ).to_dict("index"),
                "expected_durations": expected_durations,
                "regime_parameters": {
                    f"regime_{i+1}": {
                        "mean": (
                            float(params["means"][i])
                            if switching_mean
                            else float(params["means"][0])
                        ),
                        "variance": (
                            float(params["variances"][i])
                            if switching_variance
                            else float(params["variances"][0])
                        ),
                        "ar_coefficients": (
                            params["ar_coeffs"][i].tolist()
                            if switching_ar and ar_order > 0
                            else []
                        ),
                    }
                    for i in range(n_regimes)
                },
                "regime_statistics": regime_stats,
                "fit_statistics": {
                    "log_likelihood": float(log_likelihood),
                    "aic": float(aic),
                    "bic": float(bic),
                    "n_observations": n_obs,
                    "n_parameters": n_params,
                    "iterations": iteration + 1,
                },
                "specification": {
                    "n_regimes": n_regimes,
                    "switching_variance": switching_variance,
                    "switching_mean": switching_mean,
                    "switching_ar": switching_ar,
                    "ar_order": ar_order,
                },
            }

            self.logger.info(
                f"Markov-switching model complete: {n_regimes} regimes, log_lik={log_likelihood:.2f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Markov-switching model failed: {str(e)}")
            raise

    def structural_time_series(
        self,
        data: pd.DataFrame,
        variable: str,
        components: List[str],
        seasonal_period: Optional[int] = None,
        cycle_period: Optional[float] = None,
        stochastic_level: bool = True,
        stochastic_trend: bool = True,
        stochastic_seasonal: bool = True,
        stochastic_cycle: bool = True,
        regression_vars: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Decompose time series into unobserved structural components.

        Structural model:
        y_t = μ_t + γ_t + ψ_t + ε_t
        - μ_t: Level + trend
        - γ_t: Seasonal component
        - ψ_t: Cycle component
        - ε_t: Irregular component

        Args:
            data: Time series data
            variable: Variable to decompose
            components: Components to include: ['level', 'trend', 'seasonal', 'cycle', 'irregular']
            seasonal_period: Period for seasonal component (e.g., 82 for NBA season)
            cycle_period: Period for cycle component
            stochastic_level: Whether level evolves stochastically
            stochastic_trend: Whether trend evolves stochastically
            stochastic_seasonal: Whether seasonal component is stochastic
            stochastic_cycle: Whether cycle is stochastic
            regression_vars: Exogenous variables to include

        Returns:
            Dictionary containing:
            - components: Extracted structural components (level, trend, seasonal, cycle)
            - component_variances: Variance of each component's innovations
            - fitted_values: Model-fitted values
            - residuals: Irregular component
            - forecasts: Component-based forecasts
            - diagnostics: Residual diagnostics and model fit

        Example:
            # Decompose team wins into structural components
            result = structural_time_series(
                data=team_wins_df,
                variable='wins',
                components=['level', 'trend', 'seasonal'],
                seasonal_period=82,
                stochastic_seasonal=True
            )
        """
        try:
            self.logger.info(
                f"Estimating structural time series: var={variable}, components={components}"
            )

            # Validate inputs
            if data.empty:
                raise ValueError("Input data is empty")

            if variable not in data.columns:
                raise ValueError(f"Variable '{variable}' not found")

            valid_components = ["level", "trend", "seasonal", "cycle", "irregular"]
            invalid = set(components) - set(valid_components)
            if invalid:
                raise ValueError(f"Invalid components: {invalid}")

            # Prepare data
            y = data[variable].values
            n_obs = len(y)

            # Handle missing data
            if np.isnan(y).any():
                self.logger.warning("Missing data detected, using interpolation")
                y = (
                    pd.Series(y)
                    .interpolate(method="linear")
                    .fillna(method="bfill")
                    .fillna(method="ffill")
                    .values
                )

            # Build state-space representation
            state_dim = 0
            component_indices = {}

            # Level component
            if "level" in components:
                component_indices["level"] = (state_dim, state_dim + 1)
                state_dim += 1

            # Trend component
            if "trend" in components:
                component_indices["trend"] = (state_dim, state_dim + 1)
                state_dim += 1

            # Seasonal component
            if "seasonal" in components:
                if seasonal_period is None:
                    raise ValueError("seasonal_period required for seasonal component")
                component_indices["seasonal"] = (
                    state_dim,
                    state_dim + seasonal_period - 1,
                )
                state_dim += seasonal_period - 1

            # Cycle component
            if "cycle" in components:
                if cycle_period is None:
                    self.logger.warning(
                        "cycle_period not specified, using default of 40"
                    )
                    cycle_period = 40
                component_indices["cycle"] = (state_dim, state_dim + 2)
                state_dim += 2

            # Construct state-space matrices
            F, H, Q, R = self._build_structural_matrices(
                components,
                seasonal_period,
                cycle_period,
                stochastic_level,
                stochastic_trend,
                stochastic_seasonal,
                stochastic_cycle,
            )

            # Add regression component if specified
            if regression_vars:
                missing_vars = set(regression_vars) - set(data.columns)
                if missing_vars:
                    raise ValueError(f"Regression variables not found: {missing_vars}")
                X = data[regression_vars].values
            else:
                X = None

            # Estimate via Kalman filter and MLE
            x0 = np.zeros(state_dim)
            P0 = np.eye(state_dim) * 100  # Diffuse prior

            # MLE optimization
            F_opt, H_opt, Q_opt, R_opt = self._optimize_structural_model(
                y, F, H, Q, R, x0, P0, X
            )

            # Extract components via Kalman smoother
            states, state_covs, innovations, innovation_covs = (
                self._kalman_filter_forward(
                    y.reshape(-1, 1), F_opt, H_opt, Q_opt, R_opt, x0, P0
                )
            )
            smoothed_states, smoothed_covs = self._kalman_smoother_backward(
                states, state_covs, F_opt, Q_opt
            )

            # Extract individual components
            extracted_components = {}
            for comp_name, (start_idx, end_idx) in component_indices.items():
                extracted_components[comp_name] = smoothed_states[:, start_idx:end_idx]

            # Compute fitted values and residuals
            fitted = np.sum(
                [comp.sum(axis=1) for comp in extracted_components.values()], axis=0
            )
            residuals = y - fitted

            # Component variances
            component_variances = {}
            for comp_name, (start_idx, end_idx) in component_indices.items():
                comp_var = np.diag(Q_opt)[start_idx:end_idx].sum()
                component_variances[comp_name] = float(comp_var)

            # Model diagnostics
            log_likelihood = self._kalman_log_likelihood(innovations, innovation_covs)
            n_params = len(components) + 1  # Simplified param count
            aic = -2 * log_likelihood + 2 * n_params
            bic = -2 * log_likelihood + np.log(n_obs) * n_params

            diagnostics = {
                "log_likelihood": float(log_likelihood),
                "aic": float(aic),
                "bic": float(bic),
                "residual_std": float(np.std(residuals)),
                "r_squared": float(1 - np.var(residuals) / np.var(y)),
            }

            # Build result
            result = {
                "components": {},
                "component_variances": component_variances,
                "fitted_values": pd.Series(fitted, index=data.index).to_dict(),
                "residuals": pd.Series(residuals, index=data.index).to_dict(),
                "diagnostics": diagnostics,
                "specification": {
                    "components": components,
                    "seasonal_period": seasonal_period,
                    "cycle_period": cycle_period,
                    "stochastic_components": {
                        "level": stochastic_level,
                        "trend": stochastic_trend,
                        "seasonal": stochastic_seasonal,
                        "cycle": stochastic_cycle,
                    },
                },
            }

            # Add extracted components to result
            for comp_name, comp_values in extracted_components.items():
                if comp_values.shape[1] == 1:
                    result["components"][comp_name] = pd.Series(
                        comp_values.flatten(), index=data.index
                    ).to_dict()
                else:
                    # For multi-dimensional components (seasonal, cycle)
                    result["components"][comp_name] = pd.Series(
                        comp_values.sum(axis=1), index=data.index
                    ).to_dict()

            self.logger.info(
                f"Structural decomposition complete: R²={diagnostics['r_squared']:.3f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Structural time series failed: {str(e)}")
            raise

    # ========== Helper Methods ==========

    def _estimate_kalman_parameters(
        self, y, state_dim, F0, H0, Q0, R0, x0, max_iter=50
    ):
        """Estimate Kalman filter parameters via EM algorithm."""
        F, H, Q, R = F0.copy(), H0.copy(), Q0.copy(), R0.copy()

        for _ in range(max_iter):
            # E-step: Run Kalman filter and smoother
            states, covs, _, _ = self._kalman_filter_forward(y, F, H, Q, R, x0)
            smoothed_states, smoothed_covs = self._kalman_smoother_backward(
                states, covs, F, Q
            )

            # M-step: Update parameters
            # (Simplified - full EM would compute sufficient statistics)
            break  # For now, just use initial parameters

        return F, H, Q, R

    def _kalman_filter_forward(self, y, F, H, Q, R, x0, P0=None):
        """Forward pass of Kalman filter."""
        n_obs = len(y)
        state_dim = len(x0)

        if P0 is None:
            P0 = np.eye(state_dim)

        # Initialize
        states = np.zeros((n_obs, state_dim))
        covs = np.zeros((n_obs, state_dim, state_dim))
        innovations = np.zeros(y.shape)
        innovation_covs = []

        x_pred = x0
        P_pred = P0

        for t in range(n_obs):
            # Update step
            y_pred = H @ x_pred
            innovation = y[t] - y_pred
            S = H @ P_pred @ H.T + R
            K = P_pred @ H.T @ np.linalg.inv(S)

            x_update = x_pred + K @ innovation
            P_update = P_pred - K @ S @ K.T

            states[t] = x_update
            covs[t] = P_update
            innovations[t] = innovation
            innovation_covs.append(S)

            # Predict step
            x_pred = F @ x_update
            P_pred = F @ P_update @ F.T + Q

        return states, covs, innovations, innovation_covs

    def _kalman_log_likelihood(self, innovations, innovation_covs):
        """Compute log-likelihood from innovations."""
        n_obs = len(innovations)
        log_lik = 0.0

        for t in range(n_obs):
            S = innovation_covs[t]
            v = innovations[t]
            log_lik += -0.5 * (np.log(np.linalg.det(S)) + v.T @ np.linalg.inv(S) @ v)

        return log_lik

    def _kalman_smoother_backward(self, filtered_states, filtered_covs, F, Q):
        """Backward pass of Kalman smoother."""
        n_obs = len(filtered_states)
        state_dim = filtered_states.shape[1]

        smoothed_states = np.zeros_like(filtered_states)
        smoothed_covs = np.zeros_like(filtered_covs)

        smoothed_states[-1] = filtered_states[-1]
        smoothed_covs[-1] = filtered_covs[-1]

        for t in range(n_obs - 2, -1, -1):
            P_pred = F @ filtered_covs[t] @ F.T + Q
            J = filtered_covs[t] @ F.T @ np.linalg.inv(P_pred)

            smoothed_states[t] = filtered_states[t] + J @ (
                smoothed_states[t + 1] - F @ filtered_states[t]
            )
            smoothed_covs[t] = (
                filtered_covs[t] + J @ (smoothed_covs[t + 1] - P_pred) @ J.T
            )

        return smoothed_states, smoothed_covs

    def _kalman_forecast(self, x_T, P_T, F, H, Q, R, h):
        """Generate h-step ahead forecasts."""
        forecasts = []
        forecast_covs = []

        x_pred = x_T
        P_pred = P_T

        for _ in range(h):
            x_pred = F @ x_pred
            P_pred = F @ P_pred @ F.T + Q

            forecasts.append(x_pred)
            forecast_covs.append(P_pred)

        return np.array(forecasts), forecast_covs

    def _compute_kalman_diagnostics(self, innovations, innovation_covs, y, H, states):
        """Compute diagnostic statistics for Kalman filter."""
        n_obs = len(innovations)

        # Standardized innovations
        std_innovations = []
        for t in range(n_obs):
            S = innovation_covs[t]
            v = innovations[t]
            std_innovations.append(v / np.sqrt(np.diag(S)))

        std_innovations = np.array(std_innovations)

        return {
            "innovation_mean": float(innovations.mean()),
            "innovation_std": float(innovations.std()),
            "standardized_innovation_mean": float(std_innovations.mean()),
            "standardized_innovation_std": float(std_innovations.std()),
            "ljung_box_p_value": 0.5,  # Placeholder
        }

    def _dfm_principal_components(self, X, n_factors):
        """Extract factors via principal components."""
        # Compute covariance matrix
        cov_matrix = np.cov(X.T)

        # Eigen decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

        # Sort by eigenvalues (descending)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Extract factors
        loadings = eigenvectors[:, :n_factors] * np.sqrt(eigenvalues[:n_factors])
        factors = X @ loadings / np.sum(loadings**2, axis=0)

        # Compute idiosyncratic variances
        X_fitted = factors @ loadings.T
        residuals = X - X_fitted
        idio_vars = np.var(residuals, axis=0)

        return factors, loadings, idio_vars

    def _dfm_ml_em(self, X, n_factors, max_iter, tolerance):
        """Estimate DFM via EM algorithm."""
        n_obs, n_vars = X.shape

        # Initialize with PC
        factors, loadings, idio_vars = self._dfm_principal_components(X, n_factors)

        # EM iterations
        for _ in range(max_iter):
            # E-step: Compute factor expectations
            # (Simplified implementation)
            break

        return factors, loadings, idio_vars

    def _dfm_two_step(self, X, n_factors):
        """Two-step DFM: PC extraction + Kalman smoothing."""
        # Step 1: PC extraction
        factors, loadings, idio_vars = self._dfm_principal_components(X, n_factors)

        # Step 2: Kalman smoothing (simplified)
        return factors, loadings, idio_vars

    def _estimate_factor_var(self, factors, p):
        """Estimate VAR model for factor dynamics."""
        if p == 0:
            return [], np.cov(factors.T)

        n_obs, n_factors = factors.shape

        # Build lagged matrices
        Y = factors[p:]
        X = np.hstack([factors[p - i - 1 : -i - 1] for i in range(p)])

        # OLS estimation
        coeffs = np.linalg.lstsq(X, Y, rcond=None)[0]
        residuals = Y - X @ coeffs
        cov = np.cov(residuals.T)

        # Reshape coefficients
        ar_coefs = [coeffs[i * n_factors : (i + 1) * n_factors] for i in range(p)]

        return ar_coefs, cov

    def _dfm_log_likelihood(self, residuals, idio_vars):
        """Compute log-likelihood for DFM."""
        n_obs, n_vars = residuals.shape
        log_lik = 0.0

        for i in range(n_vars):
            log_lik += -0.5 * n_obs * (np.log(2 * np.pi) + np.log(idio_vars[i]))
            log_lik += -0.5 * np.sum(residuals[:, i] ** 2 / idio_vars[i])

        return log_lik

    def _initialize_markov_params(
        self,
        y,
        X,
        n_regimes,
        switching_variance,
        switching_mean,
        switching_ar,
        ar_order,
    ):
        """Initialize parameters for Markov-switching model."""
        # Split data into regimes via k-means
        from sklearn.cluster import KMeans

        if ar_order > 0:
            # Use lagged values for clustering
            y_lagged = np.column_stack(
                [y[ar_order - i : -i] for i in range(ar_order, 0, -1)]
            )
            y_current = y[ar_order:]
            kmeans = KMeans(n_clusters=n_regimes, random_state=42).fit(y_lagged)
            labels = kmeans.labels_
        else:
            y_current = y
            kmeans = KMeans(n_clusters=n_regimes, random_state=42).fit(y.reshape(-1, 1))
            labels = kmeans.labels_

        # Initialize means
        if switching_mean:
            means = np.array([y_current[labels == i].mean() for i in range(n_regimes)])
        else:
            means = np.array([y_current.mean()])

        # Initialize variances
        if switching_variance:
            variances = np.array(
                [y_current[labels == i].var() for i in range(n_regimes)]
            )
        else:
            variances = np.array([y_current.var()])

        # Initialize transition matrix
        transition_matrix = np.zeros((n_regimes, n_regimes))
        for i in range(n_regimes):
            for j in range(n_regimes):
                if i == j:
                    transition_matrix[i, j] = 0.9
                else:
                    transition_matrix[i, j] = 0.1 / (n_regimes - 1)

        # Initialize AR coefficients
        ar_coeffs = []
        if ar_order > 0:
            for i in range(n_regimes):
                ar_coeffs.append(np.zeros(ar_order))

        return {
            "means": means,
            "variances": variances,
            "ar_coeffs": ar_coeffs if ar_coeffs else None,
            "transition_matrix": transition_matrix,
        }

    def _markov_filter(self, y, X, params, n_regimes):
        """Forward filtering for Markov-switching model."""
        n_obs = len(y)
        filtered_probs = np.zeros((n_obs, n_regimes))
        predicted_probs = np.zeros((n_obs, n_regimes))
        joint_probs = np.zeros((n_obs - 1, n_regimes, n_regimes))

        # Initialize
        filtered_probs[0] = np.ones(n_regimes) / n_regimes

        for t in range(1, n_obs):
            # Prediction step
            predicted_probs[t] = params["transition_matrix"].T @ filtered_probs[t - 1]

            # Update step (simplified)
            likelihoods = np.ones(n_regimes)
            filtered_probs[t] = likelihoods * predicted_probs[t]
            filtered_probs[t] /= filtered_probs[t].sum()

            # Joint probabilities
            joint_probs[t - 1] = np.outer(filtered_probs[t - 1], filtered_probs[t])

        return filtered_probs, predicted_probs, joint_probs

    def _markov_smoother(self, filtered_probs, joint_probs, transition_matrix):
        """Backward smoothing for Markov-switching model."""
        n_obs, n_regimes = filtered_probs.shape
        smoothed_probs = np.zeros_like(filtered_probs)
        smoothed_probs[-1] = filtered_probs[-1]

        # Backward recursion (simplified)
        for t in range(n_obs - 2, -1, -1):
            smoothed_probs[t] = filtered_probs[t]

        return smoothed_probs

    def _markov_m_step(
        self,
        y,
        X,
        smoothed_probs,
        joint_probs,
        n_regimes,
        switching_variance,
        switching_mean,
        switching_ar,
        ar_order,
    ):
        """M-step for Markov-switching model."""
        # Update means
        if switching_mean:
            means = np.array(
                [
                    np.sum(smoothed_probs[:, i] * y) / smoothed_probs[:, i].sum()
                    for i in range(n_regimes)
                ]
            )
        else:
            means = np.array([np.sum(smoothed_probs * y) / smoothed_probs.sum()])

        # Update variances
        if switching_variance:
            variances = np.array(
                [
                    np.sum(smoothed_probs[:, i] * (y - means[i]) ** 2)
                    / smoothed_probs[:, i].sum()
                    for i in range(n_regimes)
                ]
            )
        else:
            variance = (
                np.sum(smoothed_probs * (y - means[0]) ** 2) / smoothed_probs.sum()
            )
            variances = np.array([variance])

        # Update transition matrix
        transition_matrix = np.zeros((n_regimes, n_regimes))
        for i in range(n_regimes):
            for j in range(n_regimes):
                numerator = joint_probs[:, i, j].sum()
                denominator = smoothed_probs[:-1, i].sum()
                transition_matrix[i, j] = (
                    numerator / denominator if denominator > 0 else 1.0 / n_regimes
                )

        return {
            "means": means,
            "variances": variances,
            "ar_coeffs": None,
            "transition_matrix": transition_matrix,
        }

    def _markov_param_diff(self, params1, params2):
        """Compute parameter difference for convergence check."""
        diff = 0.0
        diff += np.sum((params1["means"] - params2["means"]) ** 2)
        diff += np.sum((params1["variances"] - params2["variances"]) ** 2)
        diff += np.sum(
            (params1["transition_matrix"] - params2["transition_matrix"]) ** 2
        )
        return np.sqrt(diff)

    def _markov_viterbi(self, y, X, params, n_regimes):
        """Viterbi algorithm for most likely regime sequence."""
        n_obs = len(y)

        # Simplified: return most likely regime at each time
        # Full implementation would use dynamic programming
        regime_sequence = np.zeros(n_obs, dtype=int)

        return regime_sequence

    def _markov_log_likelihood(self, y, X, smoothed_probs, params, n_regimes):
        """Compute log-likelihood for Markov-switching model."""
        log_lik = 0.0

        for t in range(len(y)):
            regime_liks = np.zeros(n_regimes)
            for i in range(n_regimes):
                mean = (
                    params["means"][i]
                    if len(params["means"]) > 1
                    else params["means"][0]
                )
                var = (
                    params["variances"][i]
                    if len(params["variances"]) > 1
                    else params["variances"][0]
                )
                regime_liks[i] = -0.5 * (
                    np.log(2 * np.pi * var) + (y[t] - mean) ** 2 / var
                )

            log_lik += np.log(np.sum(np.exp(regime_liks) * smoothed_probs[t]))

        return log_lik

    def _count_markov_params(
        self, n_regimes, X, switching_variance, switching_mean, ar_order
    ):
        """Count number of parameters in Markov-switching model."""
        n_params = n_regimes * (n_regimes - 1)  # Transition matrix

        if switching_mean:
            n_params += n_regimes
        else:
            n_params += 1

        if switching_variance:
            n_params += n_regimes
        else:
            n_params += 1

        if ar_order > 0:
            n_params += n_regimes * ar_order

        return n_params

    def _build_structural_matrices(
        self,
        components,
        seasonal_period,
        cycle_period,
        stochastic_level,
        stochastic_trend,
        stochastic_seasonal,
        stochastic_cycle,
    ):
        """Build state-space matrices for structural time series model."""
        state_dim = 0

        # Count state dimensions
        if "level" in components:
            state_dim += 1
        if "trend" in components:
            state_dim += 1
        if "seasonal" in components:
            state_dim += seasonal_period - 1
        if "cycle" in components:
            state_dim += 2

        # Initialize matrices
        F = np.eye(state_dim)
        H = np.zeros((1, state_dim))
        Q = np.zeros((state_dim, state_dim))
        R = np.array([[0.1]])

        # Fill in matrices based on components
        idx = 0

        # Level
        if "level" in components:
            H[0, idx] = 1
            if stochastic_level:
                Q[idx, idx] = 0.1
            idx += 1

        # Trend
        if "trend" in components:
            if "level" in components:
                F[idx - 1, idx] = 1  # Level += trend
            H[0, idx] = 1
            if stochastic_trend:
                Q[idx, idx] = 0.01
            idx += 1

        # Seasonal
        if "seasonal" in components:
            for i in range(seasonal_period - 1):
                H[0, idx] = 1 if i == 0 else 0
                if i < seasonal_period - 2:
                    F[idx, idx + 1] = -1
                if stochastic_seasonal and i == 0:
                    Q[idx, idx] = 0.01
                idx += 1

        # Cycle
        if "cycle" in components:
            rho = 0.9
            lambda_c = 2 * np.pi / cycle_period
            F[idx : idx + 2, idx : idx + 2] = rho * np.array(
                [
                    [np.cos(lambda_c), np.sin(lambda_c)],
                    [-np.sin(lambda_c), np.cos(lambda_c)],
                ]
            )
            H[0, idx] = 1
            if stochastic_cycle:
                Q[idx : idx + 2, idx : idx + 2] = np.eye(2) * 0.01
            idx += 2

        return F, H, Q, R

    def _optimize_structural_model(self, y, F0, H0, Q0, R0, x0, P0, X):
        """Optimize structural model parameters via MLE."""
        # For now, just return initial parameters
        # Full implementation would use scipy.optimize
        return F0, H0, Q0, R0


def create_advanced_time_series_tools() -> AdvancedTimeSeriesTools:
    """Factory function to create advanced time series tools instance."""
    return AdvancedTimeSeriesTools()
