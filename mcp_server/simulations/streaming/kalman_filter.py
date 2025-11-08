"""
Streaming Kalman Filter for Real-Time Game State Estimation (Agent 14, Module 1)

Provides probabilistic state estimation for live NBA games using Kalman filtering:
- Real-time score prediction
- Win probability tracking
- Uncertainty quantification
- Adaptive state updates

Integrates with:
- streaming_analytics: Event processing
- particle_filters: Advanced state estimation
- time_series: Forecasting models
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from numpy.linalg import inv

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Current game state representation"""

    # State vector components
    home_score: float
    away_score: float
    home_score_rate: float  # Points per minute
    away_score_rate: float
    home_win_prob: float
    time_remaining: float  # Minutes

    # Uncertainty (covariance)
    uncertainty: Optional[np.ndarray] = None

    # Metadata
    quarter: int = 1
    possession: Optional[str] = None  # 'home' or 'away'
    last_update: datetime = field(default_factory=datetime.now)

    def to_vector(self) -> np.ndarray:
        """Convert state to vector representation"""
        return np.array([
            self.home_score,
            self.away_score,
            self.home_score_rate,
            self.away_score_rate,
            self.home_win_prob,
            self.time_remaining
        ])

    @classmethod
    def from_vector(cls, vec: np.ndarray, **kwargs) -> 'GameState':
        """Create GameState from vector"""
        return cls(
            home_score=float(vec[0]),
            away_score=float(vec[1]),
            home_score_rate=float(vec[2]),
            away_score_rate=float(vec[3]),
            home_win_prob=float(vec[4]),
            time_remaining=float(vec[5]),
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'home_score': self.home_score,
            'away_score': self.away_score,
            'home_score_rate': self.home_score_rate,
            'away_score_rate': self.away_score_rate,
            'home_win_prob': self.home_win_prob,
            'time_remaining': self.time_remaining,
            'quarter': self.quarter,
            'possession': self.possession,
            'last_update': self.last_update.isoformat(),
        }


@dataclass
class KalmanFilterConfig:
    """Configuration for Kalman filter"""

    # Process noise (how much we expect state to change)
    process_noise_std: float = 0.1

    # Measurement noise (how noisy our observations are)
    measurement_noise_std: float = 0.5

    # Initial uncertainty
    initial_uncertainty_std: float = 5.0

    # Score rate bounds (points per minute)
    min_score_rate: float = 0.5
    max_score_rate: float = 3.0

    # Probability bounds
    min_prob: float = 0.01
    max_prob: float = 0.99


class StreamingKalmanFilter:
    """
    Streaming Kalman Filter for real-time game state estimation.

    Uses a linear dynamical system to track:
    - Current scores
    - Scoring rates
    - Win probabilities
    - Time remaining

    Features:
    - Real-time updates as events arrive
    - Uncertainty quantification
    - Prediction ahead to game end
    - Adaptive state estimation
    """

    def __init__(self, config: Optional[KalmanFilterConfig] = None):
        """
        Initialize streaming Kalman filter.

        Args:
            config: Filter configuration
        """
        self.config = config or KalmanFilterConfig()

        # State dimension: [home_score, away_score, home_rate, away_rate, win_prob, time]
        self.state_dim = 6

        # Observation dimension: [home_score, away_score, time]
        self.obs_dim = 3

        # Initialize matrices
        self._initialize_matrices()

        # Current state
        self.state: Optional[GameState] = None
        self.covariance: Optional[np.ndarray] = None

        # History
        self.state_history: List[GameState] = []
        self.update_count = 0

        logger.info("StreamingKalmanFilter initialized")

    def _initialize_matrices(self):
        """Initialize Kalman filter matrices"""

        # State transition matrix (F)
        # Models how state evolves over time
        self.F = np.eye(self.state_dim)
        self.F[0, 2] = 1.0  # home_score += home_rate * dt
        self.F[1, 3] = 1.0  # away_score += away_rate * dt

        # Observation matrix (H)
        # Maps state to observations
        self.H = np.zeros((self.obs_dim, self.state_dim))
        self.H[0, 0] = 1.0  # Observe home_score
        self.H[1, 1] = 1.0  # Observe away_score
        self.H[2, 5] = 1.0  # Observe time_remaining

        # Process noise covariance (Q)
        self.Q = np.eye(self.state_dim) * (self.config.process_noise_std ** 2)

        # Measurement noise covariance (R)
        self.R = np.eye(self.obs_dim) * (self.config.measurement_noise_std ** 2)

        # Initial covariance (P)
        self.P_init = np.eye(self.state_dim) * (self.config.initial_uncertainty_std ** 2)

    def initialize(
        self,
        home_score: float = 0.0,
        away_score: float = 0.0,
        time_remaining: float = 48.0,
        home_score_rate: Optional[float] = None,
        away_score_rate: Optional[float] = None,
        quarter: int = 1
    ) -> GameState:
        """
        Initialize filter with starting game state.

        Args:
            home_score: Initial home team score
            away_score: Initial away team score
            time_remaining: Minutes remaining in game
            home_score_rate: Expected home scoring rate (estimated if None)
            away_score_rate: Expected away scoring rate (estimated if None)
            quarter: Current quarter

        Returns:
            Initial game state
        """
        # Estimate scoring rates if not provided
        if home_score_rate is None:
            home_score_rate = 2.0  # ~100 points per 48 minutes
        if away_score_rate is None:
            away_score_rate = 2.0

        # Initialize win probability at 50%
        home_win_prob = 0.5

        # Create initial state
        self.state = GameState(
            home_score=home_score,
            away_score=away_score,
            home_score_rate=home_score_rate,
            away_score_rate=away_score_rate,
            home_win_prob=home_win_prob,
            time_remaining=time_remaining,
            quarter=quarter,
            uncertainty=self.P_init.copy()
        )

        self.covariance = self.P_init.copy()
        self.state_history = [self.state]

        logger.info(
            f"Kalman filter initialized: home={home_score}, away={away_score}, "
            f"time={time_remaining}"
        )

        return self.state

    def predict(self, dt: float = 1.0) -> GameState:
        """
        Predict state forward in time.

        Args:
            dt: Time step (minutes)

        Returns:
            Predicted game state
        """
        if self.state is None:
            raise ValueError("Filter not initialized. Call initialize() first.")

        # Update state transition for time step
        F = self.F.copy()
        F[0, 2] = dt  # home_score increment
        F[1, 3] = dt  # away_score increment
        F[5, 5] = 1.0  # time decreases

        # Predict state
        x = self.state.to_vector()
        x_pred = F @ x

        # Decrease time remaining
        x_pred[5] = max(0, x_pred[5] - dt)

        # Predict covariance
        P_pred = F @ self.covariance @ F.T + self.Q

        # Update win probability based on score differential
        score_diff = x_pred[0] - x_pred[1]
        time_factor = np.exp(-x_pred[5] / 10.0)  # More confident near end
        x_pred[4] = self._score_diff_to_prob(score_diff, time_factor)

        # Enforce constraints
        x_pred = self._enforce_constraints(x_pred)

        # Create predicted state
        predicted_state = GameState.from_vector(
            x_pred,
            uncertainty=P_pred,
            quarter=self.state.quarter,
            possession=self.state.possession
        )

        return predicted_state

    def update(
        self,
        observation: Dict[str, float],
        dt: float = 1.0
    ) -> GameState:
        """
        Update state with new observation.

        Args:
            observation: Dictionary with 'home_score', 'away_score', 'time_remaining'
            dt: Time since last update (minutes)

        Returns:
            Updated game state
        """
        if self.state is None:
            # Auto-initialize if not done
            self.initialize(
                home_score=observation.get('home_score', 0),
                away_score=observation.get('away_score', 0),
                time_remaining=observation.get('time_remaining', 48.0)
            )

        # Predict step
        predicted_state = self.predict(dt)
        x_pred = predicted_state.to_vector()
        P_pred = predicted_state.uncertainty

        # Create observation vector
        z = np.array([
            observation.get('home_score', x_pred[0]),
            observation.get('away_score', x_pred[1]),
            observation.get('time_remaining', x_pred[5])
        ])

        # Update step (Kalman gain)
        try:
            S = self.H @ P_pred @ self.H.T + self.R
            K = P_pred @ self.H.T @ inv(S)
        except np.linalg.LinAlgError:
            logger.warning("Singular matrix in Kalman update, using prediction")
            K = np.zeros((self.state_dim, self.obs_dim))

        # Innovation (measurement residual)
        y = z - self.H @ x_pred

        # Updated state
        x_upd = x_pred + K @ y

        # Updated covariance
        P_upd = (np.eye(self.state_dim) - K @ self.H) @ P_pred

        # Update scoring rates based on observed score changes
        if self.update_count > 0 and dt > 0:
            actual_home_rate = (z[0] - self.state.home_score) / dt
            actual_away_rate = (z[1] - self.state.away_score) / dt

            # Exponential moving average
            alpha = 0.3
            x_upd[2] = alpha * actual_home_rate + (1 - alpha) * x_upd[2]
            x_upd[3] = alpha * actual_away_rate + (1 - alpha) * x_upd[3]

        # Update win probability
        score_diff = x_upd[0] - x_upd[1]
        time_factor = np.exp(-x_upd[5] / 10.0)
        x_upd[4] = self._score_diff_to_prob(score_diff, time_factor)

        # Enforce constraints
        x_upd = self._enforce_constraints(x_upd)

        # Create updated state
        self.state = GameState.from_vector(
            x_upd,
            uncertainty=P_upd,
            quarter=observation.get('quarter', self.state.quarter),
            possession=observation.get('possession', self.state.possession)
        )
        self.covariance = P_upd

        # Update history
        self.state_history.append(self.state)
        self.update_count += 1

        logger.debug(
            f"Kalman update #{self.update_count}: "
            f"home={self.state.home_score:.1f}, away={self.state.away_score:.1f}, "
            f"win_prob={self.state.home_win_prob:.3f}"
        )

        return self.state

    def predict_final_score(self) -> Tuple[float, float, Dict[str, float]]:
        """
        Predict final score at end of game.

        Returns:
            Tuple of (predicted_home_score, predicted_away_score, statistics)
        """
        if self.state is None:
            raise ValueError("Filter not initialized")

        # Predict to end of game
        current_time = self.state.time_remaining
        final_state = self.predict(dt=current_time)

        # Extract uncertainties
        final_home_std = np.sqrt(final_state.uncertainty[0, 0])
        final_away_std = np.sqrt(final_state.uncertainty[1, 1])

        statistics = {
            'home_score_mean': float(final_state.home_score),
            'away_score_mean': float(final_state.away_score),
            'home_score_std': float(final_home_std),
            'away_score_std': float(final_away_std),
            'home_win_prob': float(final_state.home_win_prob),
            'score_differential_mean': float(final_state.home_score - final_state.away_score),
            'confidence_95_lower': float(final_state.home_score - 1.96 * final_home_std),
            'confidence_95_upper': float(final_state.home_score + 1.96 * final_home_std),
        }

        return final_state.home_score, final_state.away_score, statistics

    def get_state(self) -> Optional[GameState]:
        """Get current state"""
        return self.state

    def get_confidence_interval(self, confidence: float = 0.95) -> Dict[str, Tuple[float, float]]:
        """
        Get confidence intervals for state variables.

        Args:
            confidence: Confidence level (default 0.95)

        Returns:
            Dictionary mapping variable names to (lower, upper) bounds
        """
        if self.state is None or self.covariance is None:
            return {}

        from scipy.stats import norm
        z_score = norm.ppf((1 + confidence) / 2)

        std_devs = np.sqrt(np.diag(self.covariance))
        state_vec = self.state.to_vector()

        return {
            'home_score': (
                float(state_vec[0] - z_score * std_devs[0]),
                float(state_vec[0] + z_score * std_devs[0])
            ),
            'away_score': (
                float(state_vec[1] - z_score * std_devs[1]),
                float(state_vec[1] + z_score * std_devs[1])
            ),
            'home_score_rate': (
                float(state_vec[2] - z_score * std_devs[2]),
                float(state_vec[2] + z_score * std_devs[2])
            ),
            'away_score_rate': (
                float(state_vec[3] - z_score * std_devs[3]),
                float(state_vec[3] + z_score * std_devs[3])
            ),
            'home_win_prob': (
                float(max(0, state_vec[4] - z_score * std_devs[4])),
                float(min(1, state_vec[4] + z_score * std_devs[4]))
            ),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get filter statistics"""
        if self.state is None:
            return {'initialized': False}

        return {
            'initialized': True,
            'update_count': self.update_count,
            'current_state': self.state.to_dict(),
            'uncertainty_trace': float(np.trace(self.covariance)) if self.covariance is not None else 0,
            'history_length': len(self.state_history),
        }

    def _score_diff_to_prob(self, score_diff: float, time_factor: float) -> float:
        """
        Convert score differential to win probability.

        Uses logistic function with time-dependent scaling.

        Args:
            score_diff: Home score - away score
            time_factor: Factor based on time remaining (0 to 1)

        Returns:
            Win probability (0 to 1)
        """
        # Scale based on time remaining
        # More uncertainty with more time remaining
        scale = 10.0 * (1.0 + time_factor)

        # Logistic function
        prob = 1.0 / (1.0 + np.exp(-score_diff / scale))

        # Enforce bounds
        return float(np.clip(prob, self.config.min_prob, self.config.max_prob))

    def _enforce_constraints(self, x: np.ndarray) -> np.ndarray:
        """
        Enforce physical constraints on state.

        Args:
            x: State vector

        Returns:
            Constrained state vector
        """
        x = x.copy()

        # Scores must be non-negative
        x[0] = max(0, x[0])
        x[1] = max(0, x[1])

        # Score rates must be within bounds
        x[2] = np.clip(x[2], self.config.min_score_rate, self.config.max_score_rate)
        x[3] = np.clip(x[3], self.config.min_score_rate, self.config.max_score_rate)

        # Win probability must be in [0, 1]
        x[4] = np.clip(x[4], self.config.min_prob, self.config.max_prob)

        # Time remaining must be non-negative
        x[5] = max(0, x[5])

        return x

    def reset(self):
        """Reset filter state"""
        self.state = None
        self.covariance = None
        self.state_history = []
        self.update_count = 0
        logger.info("Kalman filter reset")
