"""
Particle Filters for NBA Analytics.

Sequential Monte Carlo methods for real-time tracking and prediction.

Methods:
--------
1. Base ParticleFilter: Generic particle filter framework
2. PlayerPerformanceParticleFilter: Track player performance states
3. LiveGameProbabilityFilter: Real-time win probability updates

Resampling:
-----------
- Systematic resampling (default, efficient)
- Multinomial resampling
- Stratified resampling
- Effective sample size (ESS) monitoring

Use Cases:
----------
- Real-time player form tracking
- Live game win probability
- Injury impact assessment
- Performance trajectory prediction

Requirements:
-------------
- numpy >= 1.24.0
- pandas >= 1.5.0
- scipy >= 1.10.0

Author: NBA MCP Synthesis
Date: November 2025
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats


# ==============================================================================
# Result Classes
# ==============================================================================


@dataclass
class ParticleFilterResult:
    """
    Results from particle filter estimation.

    Attributes
    ----------
    states : np.ndarray
        Estimated states over time (T, state_dim)
    state_variance : np.ndarray
        State uncertainty over time (T, state_dim)
    particles : np.ndarray
        Particle cloud at final time (N_particles, state_dim)
    weights : np.ndarray
        Particle weights at final time (N_particles,)
    ess_history : List[float]
        Effective sample size history
    resampling_history : List[bool]
        When resampling occurred
    log_likelihood : float
        Total log likelihood of observations
    """

    states: np.ndarray
    state_variance: np.ndarray
    particles: np.ndarray
    weights: np.ndarray
    ess_history: List[float]
    resampling_history: List[bool]
    log_likelihood: float

    def __repr__(self) -> str:
        return (
            f"ParticleFilterResult(\n"
            f"  T={len(self.states)}, "
            f"  state_dim={self.states.shape[1] if len(self.states.shape) > 1 else 1},\n"
            f"  N_particles={len(self.particles)},\n"
            f"  log_likelihood={self.log_likelihood:.2f},\n"
            f"  avg_ESS={np.mean(self.ess_history):.1f}\n"
            f")"
        )


@dataclass
class PlayerPerformanceResult(ParticleFilterResult):
    """
    Extended result for player performance tracking.

    Additional Attributes
    ---------------------
    form_states : pd.DataFrame
        Player form over time (dates, mean, variance)
    skill_trajectory : pd.DataFrame
        Estimated skill trajectory
    regime_probabilities : Optional[pd.DataFrame]
        Regime probabilities if using mixture model
    """

    form_states: pd.DataFrame
    skill_trajectory: pd.DataFrame
    regime_probabilities: Optional[pd.DataFrame] = None


# ==============================================================================
# Resampling Algorithms
# ==============================================================================


def compute_ess(weights: np.ndarray) -> float:
    """
    Compute Effective Sample Size.

    ESS = 1 / sum(w_i^2)

    Parameters
    ----------
    weights : np.ndarray
        Normalized particle weights

    Returns
    -------
    float
        Effective sample size
    """
    return 1.0 / np.sum(weights**2)


def systematic_resampling(weights: np.ndarray) -> np.ndarray:
    """
    Systematic resampling (deterministic, low variance).

    Parameters
    ----------
    weights : np.ndarray
        Normalized particle weights (N,)

    Returns
    -------
    np.ndarray
        Resampled indices (N,)
    """
    N = len(weights)
    positions = (np.arange(N) + np.random.uniform()) / N
    cumsum = np.cumsum(weights)

    indices = np.zeros(N, dtype=int)
    i, j = 0, 0

    while i < N:
        if positions[i] < cumsum[j]:
            indices[i] = j
            i += 1
        else:
            j += 1

    return indices


def multinomial_resampling(weights: np.ndarray) -> np.ndarray:
    """
    Multinomial resampling (simple but high variance).

    Parameters
    ----------
    weights : np.ndarray
        Normalized particle weights (N,)

    Returns
    -------
    np.ndarray
        Resampled indices (N,)
    """
    N = len(weights)
    return np.random.choice(N, size=N, replace=True, p=weights)


def stratified_resampling(weights: np.ndarray) -> np.ndarray:
    """
    Stratified resampling (balance of systematic and multinomial).

    Parameters
    ----------
    weights : np.ndarray
        Normalized particle weights (N,)

    Returns
    -------
    np.ndarray
        Resampled indices (N,)
    """
    N = len(weights)
    positions = (np.arange(N) + np.random.uniform(size=N)) / N
    cumsum = np.cumsum(weights)

    indices = np.zeros(N, dtype=int)
    i, j = 0, 0

    while i < N:
        if positions[i] < cumsum[j]:
            indices[i] = j
            i += 1
        else:
            j += 1

    return indices


# ==============================================================================
# Base Particle Filter
# ==============================================================================


class ParticleFilter:
    """
    Generic Particle Filter (Sequential Monte Carlo).

    State Space Model:
    ------------------
    x_t = f(x_{t-1}, u_t) + w_t    (state transition)
    y_t = h(x_t) + v_t              (observation model)

    where:
    - x_t: latent state
    - y_t: observation
    - u_t: control input
    - w_t: process noise
    - v_t: observation noise

    Parameters
    ----------
    n_particles : int
        Number of particles
    state_dim : int
        State dimension
    transition_fn : Callable
        State transition function f(particles, **kwargs)
    observation_fn : Callable
        Observation likelihood p(y_t | x_t)
    resampling_method : str
        'systematic', 'multinomial', or 'stratified'
    resampling_threshold : float
        ESS threshold for resampling (fraction of n_particles)
    """

    def __init__(
        self,
        n_particles: int = 1000,
        state_dim: int = 1,
        transition_fn: Optional[Callable] = None,
        observation_fn: Optional[Callable] = None,
        resampling_method: str = "systematic",
        resampling_threshold: float = 0.5,
    ):
        if n_particles < 100:
            raise ValueError("n_particles should be at least 100")
        if state_dim < 1:
            raise ValueError("state_dim must be >= 1")

        self.n_particles = n_particles
        self.state_dim = state_dim
        self.transition_fn = transition_fn
        self.observation_fn = observation_fn

        # Resampling
        if resampling_method == "systematic":
            self.resampling_fn = systematic_resampling
        elif resampling_method == "multinomial":
            self.resampling_fn = multinomial_resampling
        elif resampling_method == "stratified":
            self.resampling_fn = stratified_resampling
        else:
            raise ValueError(
                f"Unknown resampling_method: {resampling_method}. "
                f"Choose 'systematic', 'multinomial', or 'stratified'"
            )

        self.resampling_threshold = resampling_threshold

        # State
        self.particles = None
        self.weights = None
        self.log_likelihood = 0.0

    def initialize_particles(
        self, initial_state: np.ndarray, initial_variance: float = 1.0
    ):
        """
        Initialize particle cloud around initial state.

        Parameters
        ----------
        initial_state : np.ndarray
            Initial state mean (state_dim,)
        initial_variance : float
            Initial state variance
        """
        if self.state_dim == 1:
            self.particles = np.random.normal(
                initial_state, np.sqrt(initial_variance), size=self.n_particles
            )[:, None]
        else:
            self.particles = np.random.multivariate_normal(
                initial_state,
                initial_variance * np.eye(self.state_dim),
                size=self.n_particles,
            )

        self.weights = np.ones(self.n_particles) / self.n_particles

    def predict(self, **kwargs):
        """
        Prediction step: propagate particles through transition model.

        Parameters
        ----------
        **kwargs : dict
            Additional arguments for transition_fn
        """
        if self.transition_fn is None:
            raise ValueError("transition_fn not set")

        self.particles = self.transition_fn(self.particles, **kwargs)

    def update(self, observation: np.ndarray, **kwargs):
        """
        Update step: reweight particles based on observation likelihood.

        Parameters
        ----------
        observation : np.ndarray
            Current observation
        **kwargs : dict
            Additional arguments for observation_fn
        """
        if self.observation_fn is None:
            raise ValueError("observation_fn not set")

        # Compute likelihoods
        likelihoods = self.observation_fn(self.particles, observation, **kwargs)

        # Update weights
        self.weights *= likelihoods
        weight_sum = np.sum(self.weights)

        if weight_sum > 0:
            self.weights /= weight_sum
            self.log_likelihood += np.log(weight_sum)
        else:
            # All likelihoods zero - reinitialize
            self.weights = np.ones(self.n_particles) / self.n_particles

    def resample_if_needed(self) -> bool:
        """
        Resample particles if ESS below threshold.

        Returns
        -------
        bool
            True if resampling occurred
        """
        ess = compute_ess(self.weights)

        if ess < self.resampling_threshold * self.n_particles:
            indices = self.resampling_fn(self.weights)
            self.particles = self.particles[indices]
            self.weights = np.ones(self.n_particles) / self.n_particles
            return True

        return False

    def get_state_estimate(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get weighted mean and variance of current state.

        Returns
        -------
        mean : np.ndarray
            Weighted mean (state_dim,)
        variance : np.ndarray
            Weighted variance (state_dim,)
        """
        mean = np.average(self.particles, weights=self.weights, axis=0)

        # Weighted variance
        diff = self.particles - mean
        variance = np.average(diff**2, weights=self.weights, axis=0)

        return mean, variance

    def filter(
        self, observations: np.ndarray, initial_state: np.ndarray, **kwargs
    ) -> ParticleFilterResult:
        """
        Run particle filter on full observation sequence.

        Parameters
        ----------
        observations : np.ndarray
            Observation sequence (T, obs_dim)
        initial_state : np.ndarray
            Initial state (state_dim,)
        **kwargs : dict
            Additional arguments for transition/observation functions

        Returns
        -------
        ParticleFilterResult
            Filtering results
        """
        T = len(observations)

        # Initialize storage
        states = np.zeros((T, self.state_dim))
        state_variance = np.zeros((T, self.state_dim))
        ess_history = []
        resampling_history = []

        # Initialize particles
        self.initialize_particles(initial_state, kwargs.get("initial_variance", 1.0))
        self.log_likelihood = 0.0

        # Filter
        for t in range(T):
            # Predict
            self.predict(**kwargs)

            # Update
            self.update(observations[t], **kwargs)

            # Get estimate
            states[t], state_variance[t] = self.get_state_estimate()

            # Resample if needed
            ess = compute_ess(self.weights)
            ess_history.append(ess)
            resampled = self.resample_if_needed()
            resampling_history.append(resampled)

        return ParticleFilterResult(
            states=states,
            state_variance=state_variance,
            particles=self.particles.copy(),
            weights=self.weights.copy(),
            ess_history=ess_history,
            resampling_history=resampling_history,
            log_likelihood=self.log_likelihood,
        )


# ==============================================================================
# Player Performance Particle Filter
# ==============================================================================


class PlayerPerformanceParticleFilter(ParticleFilter):
    """
    Particle filter for tracking player performance state.

    State Model:
    ------------
    skill_t = skill_{t-1} + drift + noise
    form_t = rho * form_{t-1} + shock

    where:
    - skill: long-term ability (random walk with drift)
    - form: short-term fluctuations (AR(1) process)

    Observation:
    ------------
    points_t ~ Poisson(exp(skill_t + form_t + beta*X_t))

    where X_t includes minutes, opponent strength, etc.

    Parameters
    ----------
    n_particles : int
        Number of particles
    skill_drift : float
        Expected change in skill per game (default: 0)
    skill_volatility : float
        Volatility of skill changes (default: 0.05)
    form_persistence : float
        AR(1) coefficient for form (default: 0.7)
    form_volatility : float
        Volatility of form shocks (default: 0.2)
    """

    def __init__(
        self,
        n_particles: int = 1000,
        skill_drift: float = 0.0,
        skill_volatility: float = 0.05,
        form_persistence: float = 0.7,
        form_volatility: float = 0.2,
        **kwargs,
    ):
        super().__init__(
            n_particles=n_particles, state_dim=2, **kwargs
        )  # [skill, form]

        self.skill_drift = skill_drift
        self.skill_volatility = skill_volatility
        self.form_persistence = form_persistence
        self.form_volatility = form_volatility

        # Set transition and observation functions
        self.transition_fn = self._transition_model
        self.observation_fn = self._observation_likelihood

    def _transition_model(self, particles: np.ndarray, **kwargs) -> np.ndarray:
        """
        State transition: [skill, form].

        skill_t = skill_{t-1} + drift + N(0, skill_vol^2)
        form_t = rho * form_{t-1} + N(0, form_vol^2)
        """
        new_particles = particles.copy()

        # Skill: random walk with drift
        new_particles[:, 0] += self.skill_drift + np.random.normal(
            0, self.skill_volatility, size=self.n_particles
        )

        # Form: AR(1)
        new_particles[:, 1] = self.form_persistence * particles[
            :, 1
        ] + np.random.normal(0, self.form_volatility, size=self.n_particles)

        return new_particles

    def _observation_likelihood(
        self,
        particles: np.ndarray,
        observation: np.ndarray,
        covariates: Optional[np.ndarray] = None,
        coefficients: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Compute observation likelihood: Poisson(exp(skill + form + X*beta)).

        Parameters
        ----------
        particles : np.ndarray
            Particle states (N, 2)
        observation : np.ndarray
            Observed points (scalar or array)
        covariates : Optional[np.ndarray]
            Covariates X (e.g., minutes, opponent strength)
        coefficients : Optional[np.ndarray]
            Regression coefficients beta

        Returns
        -------
        np.ndarray
            Likelihoods (N,)
        """
        # Base rate: skill + form
        lambda_base = np.exp(particles[:, 0] + particles[:, 1])

        # Add covariate effects
        if covariates is not None and coefficients is not None:
            lambda_base *= np.exp(covariates @ coefficients)

        # Poisson likelihood
        obs_value = observation if np.isscalar(observation) else observation[0]

        # Clamp lambda to avoid overflow
        lambda_base = np.clip(lambda_base, 1e-10, 1e4)

        likelihoods = stats.poisson.pmf(obs_value, lambda_base)

        # Avoid zero likelihoods
        likelihoods = np.maximum(likelihoods, 1e-300)

        return likelihoods

    def filter_player_season(
        self,
        data: pd.DataFrame,
        target_col: str = "points",
        covariate_cols: Optional[List[str]] = None,
        coefficients: Optional[np.ndarray] = None,
    ) -> PlayerPerformanceResult:
        """
        Filter player performance over a season.

        Parameters
        ----------
        data : pd.DataFrame
            Player game log with dates, points, covariates
        target_col : str
            Column name for target variable (e.g., 'points')
        covariate_cols : Optional[List[str]]
            Covariate column names
        coefficients : Optional[np.ndarray]
            Regression coefficients for covariates

        Returns
        -------
        PlayerPerformanceResult
            Tracking results with form states and skill trajectory
        """
        # Extract observations
        observations = data[target_col].values

        # Initial state: estimate from first few games
        initial_skill = np.log(np.mean(observations[:5]) + 1)
        initial_form = 0.0
        initial_state = np.array([initial_skill, initial_form])

        # Prepare covariates
        if covariate_cols is not None:
            covariates = data[covariate_cols].values
        else:
            covariates = None

        # Run filter
        base_result = self.filter(
            observations=observations[:, None],
            initial_state=initial_state,
            covariates=covariates,
            coefficients=coefficients,
        )

        # Create DataFrames for interpretability
        dates = data.index if isinstance(data.index, pd.DatetimeIndex) else data.index

        form_states = pd.DataFrame(
            {
                "date": dates,
                "skill_mean": base_result.states[:, 0],
                "form_mean": base_result.states[:, 1],
                "skill_variance": base_result.state_variance[:, 0],
                "form_variance": base_result.state_variance[:, 1],
            }
        )

        skill_trajectory = pd.DataFrame(
            {
                "date": dates,
                "skill": base_result.states[:, 0],
                "skill_lower": base_result.states[:, 0]
                - 1.96 * np.sqrt(base_result.state_variance[:, 0]),
                "skill_upper": base_result.states[:, 0]
                + 1.96 * np.sqrt(base_result.state_variance[:, 0]),
            }
        )

        return PlayerPerformanceResult(
            states=base_result.states,
            state_variance=base_result.state_variance,
            particles=base_result.particles,
            weights=base_result.weights,
            ess_history=base_result.ess_history,
            resampling_history=base_result.resampling_history,
            log_likelihood=base_result.log_likelihood,
            form_states=form_states,
            skill_trajectory=skill_trajectory,
        )


# ==============================================================================
# Live Game Probability Filter
# ==============================================================================


@dataclass
class GameStateResult:
    """
    Results from live game probability filtering.

    Attributes
    ----------
    time_points : List[float]
        Game time points (minutes)
    win_probabilities : List[float]
        Win probability at each time point
    score_states : pd.DataFrame
        Estimated score states (mean, variance)
    final_win_prob : float
        Final win probability
    upset_probability : float
        Probability of upset (if underdog wins)
    """

    time_points: List[float]
    win_probabilities: List[float]
    score_states: pd.DataFrame
    final_win_prob: float
    upset_probability: float


class LiveGameProbabilityFilter(ParticleFilter):
    """
    Real-time win probability tracking during live games.

    State Model:
    ------------
    score_diff_t = score_diff_{t-1} + drift_t + noise

    where drift_t depends on:
    - Team strengths
    - Lineup quality
    - Home court advantage
    - Momentum

    Observation:
    ------------
    observed_diff_t ~ Normal(true_diff_t, obs_noise)

    Parameters
    ----------
    n_particles : int
        Number of particles
    home_strength : float
        Home team strength (e.g., net rating)
    away_strength : float
        Away team strength
    game_length : float
        Total game length in minutes (default: 48)
    noise_per_minute : float
        Score volatility per minute (default: 1.5)
    """

    def __init__(
        self,
        n_particles: int = 2000,
        home_strength: float = 0.0,
        away_strength: float = 0.0,
        game_length: float = 48.0,
        noise_per_minute: float = 1.5,
        **kwargs,
    ):
        super().__init__(n_particles=n_particles, state_dim=1, **kwargs)

        self.home_strength = home_strength
        self.away_strength = away_strength
        self.game_length = game_length
        self.noise_per_minute = noise_per_minute

        # Home court advantage (typically ~3 points)
        self.home_court = 3.0

        # Expected score difference per minute
        self.expected_drift = (
            home_strength - away_strength + self.home_court
        ) / game_length

        self.transition_fn = self._game_transition
        self.observation_fn = self._score_likelihood

    def _game_transition(
        self, particles: np.ndarray, time_delta: float = 1.0, **kwargs
    ) -> np.ndarray:
        """
        Score difference evolution.

        Parameters
        ----------
        particles : np.ndarray
            Current score differences (N, 1)
        time_delta : float
            Time elapsed in minutes
        """
        # Drift based on team strength difference
        drift = self.expected_drift * time_delta

        # Random fluctuations
        noise = np.random.normal(
            0, self.noise_per_minute * np.sqrt(time_delta), size=self.n_particles
        )

        return particles + drift + noise[:, None]

    def _score_likelihood(
        self, particles: np.ndarray, observation: np.ndarray, obs_noise: float = 0.1
    ) -> np.ndarray:
        """
        Likelihood of observing score difference given state.

        Parameters
        ----------
        particles : np.ndarray
            Score difference particles (N, 1)
        observation : np.ndarray
            Observed score difference
        obs_noise : float
            Observation noise
        """
        obs_value = observation if np.isscalar(observation) else observation[0]

        likelihoods = stats.norm.pdf(obs_value, loc=particles[:, 0], scale=obs_noise)

        return np.maximum(likelihoods, 1e-300)

    def track_game(
        self,
        score_updates: List[Tuple[float, int, int]],
        initial_diff: float = 0.0,
    ) -> GameStateResult:
        """
        Track win probability throughout a game.

        Parameters
        ----------
        score_updates : List[Tuple[float, int, int]]
            List of (time, home_score, away_score)
        initial_diff : float
            Starting score difference

        Returns
        -------
        GameStateResult
            Win probability evolution
        """
        time_points = []
        win_probabilities = []
        score_states = []

        # Initialize
        self.initialize_particles(
            initial_state=np.array([initial_diff]), initial_variance=1.0
        )

        prev_time = 0.0

        for time, home_score, away_score in score_updates:
            time_delta = time - prev_time
            score_diff = home_score - away_score

            # Predict
            self.predict(time_delta=time_delta)

            # Update
            self.update(observation=np.array([score_diff]), obs_noise=2.0)

            # Resample
            self.resample_if_needed()

            # Get estimates
            mean_diff, var_diff = self.get_state_estimate()

            # Estimate win probability
            time_remaining = self.game_length - time
            if time_remaining > 0:
                # Project to end of game
                final_diff_mean = mean_diff[0] + self.expected_drift * time_remaining
                final_diff_std = np.sqrt(
                    var_diff[0] + (self.noise_per_minute**2) * time_remaining
                )

                # Win probability = P(final_diff > 0)
                win_prob = 1 - stats.norm.cdf(
                    0, loc=final_diff_mean, scale=final_diff_std
                )
            else:
                # Game over
                win_prob = 1.0 if mean_diff[0] > 0 else 0.0

            time_points.append(time)
            win_probabilities.append(win_prob)
            score_states.append(
                {"time": time, "mean_diff": mean_diff[0], "var_diff": var_diff[0]}
            )

            prev_time = time

        # Final results
        score_states_df = pd.DataFrame(score_states)
        final_win_prob = win_probabilities[-1] if win_probabilities else 0.5

        # Upset probability (if underdog wins)
        initial_win_prob = win_probabilities[0] if win_probabilities else 0.5
        if initial_win_prob < 0.5 and final_win_prob > 0.5:
            upset_probability = final_win_prob
        elif initial_win_prob > 0.5 and final_win_prob < 0.5:
            upset_probability = 1 - final_win_prob
        else:
            upset_probability = 0.0

        return GameStateResult(
            time_points=time_points,
            win_probabilities=win_probabilities,
            score_states=score_states_df,
            final_win_prob=final_win_prob,
            upset_probability=upset_probability,
        )


# ==============================================================================
# Utility Functions
# ==============================================================================


def diagnose_particle_degeneracy(result: ParticleFilterResult) -> Dict[str, float]:
    """
    Diagnose particle filter degeneracy issues.

    Parameters
    ----------
    result : ParticleFilterResult
        Filter results to diagnose

    Returns
    -------
    Dict[str, float]
        Diagnostic metrics
    """
    avg_ess = np.mean(result.ess_history)
    min_ess = np.min(result.ess_history)
    resampling_rate = np.mean(result.resampling_history)

    # Weight concentration
    weight_entropy = -np.sum(result.weights * np.log(result.weights + 1e-300))

    return {
        "avg_ess": avg_ess,
        "min_ess": min_ess,
        "resampling_rate": resampling_rate,
        "weight_entropy": weight_entropy,
        "is_degenerate": avg_ess < 0.1 * len(result.weights),
    }


def compare_resampling_methods(
    observations: np.ndarray,
    initial_state: np.ndarray,
    pf_class: type,
    **pf_kwargs,
) -> pd.DataFrame:
    """
    Compare different resampling methods.

    Parameters
    ----------
    observations : np.ndarray
        Observation sequence
    initial_state : np.ndarray
        Initial state
    pf_class : type
        ParticleFilter class to use
    **pf_kwargs : dict
        Particle filter parameters

    Returns
    -------
    pd.DataFrame
        Comparison of methods
    """
    methods = ["systematic", "multinomial", "stratified"]
    results = []

    for method in methods:
        pf = pf_class(resampling_method=method, **pf_kwargs)
        result = pf.filter(observations, initial_state)

        results.append(
            {
                "method": method,
                "log_likelihood": result.log_likelihood,
                "avg_ess": np.mean(result.ess_history),
                "resampling_rate": np.mean(result.resampling_history),
            }
        )

    return pd.DataFrame(results)


# ==============================================================================
# NBA-Specific Helpers
# ==============================================================================


def create_player_filter(
    player_data: pd.DataFrame,
    n_particles: int = 1000,
    **kwargs,
) -> PlayerPerformanceParticleFilter:
    """
    Create a player performance filter with auto-tuned parameters.

    Parameters
    ----------
    player_data : pd.DataFrame
        Historical player data for parameter estimation
    n_particles : int
        Number of particles
    **kwargs : dict
        Additional filter parameters

    Returns
    -------
    PlayerPerformanceParticleFilter
        Configured filter
    """
    # Estimate parameters from data
    points = player_data["points"].values if "points" in player_data else None

    if points is not None and len(points) > 10:
        # Estimate volatility from data
        log_points = np.log(points + 1)
        returns = np.diff(log_points)

        skill_volatility = np.std(returns) * 0.5  # Smoother for skill
        form_volatility = np.std(returns) * 0.8  # More volatile for form

        # Estimate form persistence (AR(1) coefficient)
        if len(returns) > 1:
            form_persistence = np.corrcoef(returns[:-1], returns[1:])[0, 1]
            form_persistence = np.clip(form_persistence, 0.5, 0.95)
        else:
            form_persistence = 0.7
    else:
        # Defaults
        skill_volatility = 0.05
        form_volatility = 0.2
        form_persistence = 0.7

    return PlayerPerformanceParticleFilter(
        n_particles=n_particles,
        skill_volatility=skill_volatility,
        form_volatility=form_volatility,
        form_persistence=form_persistence,
        **kwargs,
    )


def create_game_filter(
    home_team_rating: float,
    away_team_rating: float,
    n_particles: int = 2000,
    **kwargs,
) -> LiveGameProbabilityFilter:
    """
    Create a live game probability filter.

    Parameters
    ----------
    home_team_rating : float
        Home team net rating
    away_team_rating : float
        Away team net rating
    n_particles : int
        Number of particles
    **kwargs : dict
        Additional filter parameters

    Returns
    -------
    LiveGameProbabilityFilter
        Configured filter
    """
    return LiveGameProbabilityFilter(
        n_particles=n_particles,
        home_strength=home_team_rating,
        away_strength=away_team_rating,
        **kwargs,
    )
