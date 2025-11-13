"""
Live Game Simulator (Agent 14, Module 2)

Provides real-time simulation capabilities for live NBA games:
- Integration with Kalman filter for state tracking
- Model-based probability updates
- Real-time win probability calculation
- Event-driven simulation updates

Integrates with:
- streaming/kalman_filter: State estimation
- deployment/simulation_service: Model predictions
- streaming_analytics: Live game tracking
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

import numpy as np

from mcp_server.simulations.streaming.kalman_filter import (
    StreamingKalmanFilter,
    GameState,
    KalmanFilterConfig,
)
from mcp_server.streaming_analytics import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)


@dataclass
class SimulationUpdate:
    """Update from live simulation"""

    update_id: int
    timestamp: datetime
    game_state: GameState
    win_probabilities: Dict[str, float]
    expected_final_scores: Dict[str, float]
    confidence_intervals: Dict[str, tuple]
    model_prediction: Optional[Dict[str, Any]] = None
    event_trigger: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "update_id": self.update_id,
            "timestamp": self.timestamp.isoformat(),
            "game_state": self.game_state.to_dict(),
            "win_probabilities": self.win_probabilities,
            "expected_final_scores": self.expected_final_scores,
            "confidence_intervals": {
                k: {"lower": v[0], "upper": v[1]}
                for k, v in self.confidence_intervals.items()
            },
            "model_prediction": self.model_prediction,
            "event_trigger": self.event_trigger,
        }


@dataclass
class LiveSimulatorConfig:
    """Configuration for live simulator"""

    # Kalman filter config
    kalman_config: Optional[KalmanFilterConfig] = None

    # Update frequency
    min_update_interval_seconds: float = 1.0

    # Model integration
    use_model_predictions: bool = True
    model_weight: float = (
        0.5  # Weight for model vs Kalman (0=Kalman only, 1=model only)
    )

    # Significant event thresholds
    significant_score_change: float = 5.0  # Points
    significant_prob_change: float = 0.1  # 10% probability change

    # History retention
    max_history_size: int = 1000


class LiveGameSimulator:
    """
    Real-time game simulator combining Kalman filtering and ML models.

    Features:
    - Kalman filter for probabilistic state tracking
    - Integration with trained ML models
    - Real-time win probability updates
    - Event-driven simulation
    - Confidence intervals and uncertainty quantification
    """

    def __init__(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        config: Optional[LiveSimulatorConfig] = None,
        simulation_service: Optional[Any] = None,
    ):
        """
        Initialize live game simulator.

        Args:
            game_id: Unique game identifier
            home_team: Home team name/ID
            away_team: Away team name/ID
            config: Simulator configuration
            simulation_service: Optional SimulationService for model predictions
        """
        self.game_id = game_id
        self.home_team = home_team
        self.away_team = away_team
        self.config = config or LiveSimulatorConfig()
        self.simulation_service = simulation_service

        # Initialize Kalman filter
        self.kalman_filter = StreamingKalmanFilter(config=self.config.kalman_config)

        # State
        self.initialized = False
        self.update_count = 0
        self.last_update_time: Optional[datetime] = None
        self.update_history: List[SimulationUpdate] = []

        # Event callbacks
        self.callbacks: List[Callable[[SimulationUpdate], None]] = []

        logger.info(
            f"LiveGameSimulator initialized: {home_team} vs {away_team} "
            f"(game_id: {game_id})"
        )

    def initialize(
        self,
        home_score: float = 0.0,
        away_score: float = 0.0,
        time_remaining: float = 48.0,
        quarter: int = 1,
    ) -> SimulationUpdate:
        """
        Initialize simulator with starting game state.

        Args:
            home_score: Initial home score
            away_score: Initial away score
            time_remaining: Minutes remaining
            quarter: Current quarter

        Returns:
            Initial simulation update
        """
        # Initialize Kalman filter
        self.kalman_filter.initialize(
            home_score=home_score,
            away_score=away_score,
            time_remaining=time_remaining,
            quarter=quarter,
        )

        self.initialized = True
        self.last_update_time = datetime.now()

        # Create initial update
        update = self._create_update(event_trigger="initialization")

        self.update_history.append(update)
        self._notify_callbacks(update)

        logger.info(
            f"Simulator initialized: {home_score}-{away_score}, "
            f"{time_remaining} min remaining"
        )

        return update

    def process_event(self, event: StreamEvent) -> Optional[SimulationUpdate]:
        """
        Process streaming event and update simulation.

        Args:
            event: Stream event to process

        Returns:
            Simulation update if significant change occurred
        """
        if not self.initialized:
            # Auto-initialize from first event
            home_score = event.data.get("home_score", 0)
            away_score = event.data.get("away_score", 0)
            time_remaining = event.data.get("time_remaining", 48.0)
            quarter = event.data.get("quarter", 1)

            return self.initialize(home_score, away_score, time_remaining, quarter)

        # Check update frequency
        now = datetime.now()
        if self.last_update_time is not None:
            elapsed = (now - self.last_update_time).total_seconds()
            if elapsed < self.config.min_update_interval_seconds:
                return None

        # Extract observation from event
        observation = self._event_to_observation(event)
        if observation is None:
            return None

        # Calculate time delta
        dt = self._calculate_time_delta()

        # Update Kalman filter
        prev_state = self.kalman_filter.get_state()
        self.kalman_filter.update(observation, dt=dt)

        # Check if update is significant
        if not self._is_significant_update(prev_state):
            return None

        # Create update
        update = self._create_update(
            event_trigger=event.event_type.value if event.event_type else None
        )

        self.update_history.append(update)
        self._notify_callbacks(update)
        self.last_update_time = now

        logger.debug(
            f"Processed event: {event.event_type.value if event.event_type else 'unknown'}, "
            f"win_prob={update.win_probabilities['home']:.3f}"
        )

        return update

    def update_from_scores(
        self,
        home_score: float,
        away_score: float,
        time_remaining: float,
        quarter: Optional[int] = None,
        possession: Optional[str] = None,
    ) -> SimulationUpdate:
        """
        Update simulation with current scores (manual update).

        Args:
            home_score: Current home score
            away_score: Current away score
            time_remaining: Minutes remaining
            quarter: Current quarter
            possession: Current possession ('home' or 'away')

        Returns:
            Simulation update
        """
        if not self.initialized:
            return self.initialize(home_score, away_score, time_remaining, quarter or 1)

        # Create observation
        observation = {
            "home_score": home_score,
            "away_score": away_score,
            "time_remaining": time_remaining,
        }

        if quarter is not None:
            observation["quarter"] = quarter
        if possession is not None:
            observation["possession"] = possession

        # Calculate time delta
        dt = self._calculate_time_delta()

        # Update Kalman filter
        self.kalman_filter.update(observation, dt=dt)

        # Create update
        update = self._create_update(event_trigger="manual_update")

        self.update_history.append(update)
        self._notify_callbacks(update)
        self.last_update_time = datetime.now()

        return update

    def predict_final_score(self) -> Dict[str, Any]:
        """
        Predict final score at end of game.

        Returns:
            Dictionary with predictions and statistics
        """
        if not self.initialized:
            raise ValueError("Simulator not initialized")

        home_final, away_final, stats = self.kalman_filter.predict_final_score()

        # Get model prediction if available
        model_prediction = None
        if self.config.use_model_predictions and self.simulation_service:
            try:
                model_prediction = self._get_model_prediction()
            except Exception as e:
                logger.warning(f"Model prediction failed: {e}")

        # Combine Kalman and model predictions if available
        if model_prediction:
            w = self.config.model_weight
            home_final = w * model_prediction["home_score"] + (1 - w) * home_final
            away_final = w * model_prediction["away_score"] + (1 - w) * away_final

        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "predicted_home_score": float(home_final),
            "predicted_away_score": float(away_final),
            "kalman_statistics": stats,
            "model_prediction": model_prediction,
        }

    def get_current_state(self) -> Optional[GameState]:
        """Get current game state"""
        return self.kalman_filter.get_state()

    def get_history(self, limit: Optional[int] = None) -> List[SimulationUpdate]:
        """
        Get update history.

        Args:
            limit: Maximum number of updates to return (None = all)

        Returns:
            List of simulation updates
        """
        if limit is None:
            return self.update_history.copy()
        return self.update_history[-limit:]

    def register_callback(self, callback: Callable[[SimulationUpdate], None]):
        """
        Register callback for simulation updates.

        Args:
            callback: Function to call on each update
        """
        self.callbacks.append(callback)
        logger.info(f"Registered callback: {callback.__name__}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get simulator statistics"""
        return {
            "game_id": self.game_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "initialized": self.initialized,
            "update_count": self.update_count,
            "history_length": len(self.update_history),
            "kalman_stats": self.kalman_filter.get_statistics(),
            "callbacks_registered": len(self.callbacks),
        }

    def _create_update(self, event_trigger: Optional[str] = None) -> SimulationUpdate:
        """Create simulation update from current state"""
        state = self.kalman_filter.get_state()
        if state is None:
            raise ValueError("Kalman filter has no state")

        # Get confidence intervals
        confidence_intervals = self.kalman_filter.get_confidence_interval()

        # Calculate win probabilities
        win_probabilities = {
            "home": float(state.home_win_prob),
            "away": float(1.0 - state.home_win_prob),
        }

        # Predict final scores
        home_final, away_final, _ = self.kalman_filter.predict_final_score()
        expected_final_scores = {
            "home": float(home_final),
            "away": float(away_final),
        }

        # Get model prediction if available
        model_prediction = None
        if self.config.use_model_predictions and self.simulation_service:
            try:
                model_prediction = self._get_model_prediction()
                # Blend predictions
                w = self.config.model_weight
                if model_prediction:
                    win_probabilities["home"] = (
                        w
                        * model_prediction.get(
                            "home_win_prob", win_probabilities["home"]
                        )
                        + (1 - w) * win_probabilities["home"]
                    )
                    win_probabilities["away"] = 1.0 - win_probabilities["home"]
            except Exception as e:
                logger.debug(f"Model prediction unavailable: {e}")

        update = SimulationUpdate(
            update_id=self.update_count,
            timestamp=datetime.now(),
            game_state=state,
            win_probabilities=win_probabilities,
            expected_final_scores=expected_final_scores,
            confidence_intervals=confidence_intervals,
            model_prediction=model_prediction,
            event_trigger=event_trigger,
        )

        self.update_count += 1
        return update

    def _event_to_observation(self, event: StreamEvent) -> Optional[Dict[str, float]]:
        """Convert stream event to Kalman observation"""
        observation = {}

        if event.event_type == StreamEventType.SCORE_UPDATE:
            if "score" in event.data:
                score = event.data["score"]
                observation["home_score"] = score.get("home", 0)
                observation["away_score"] = score.get("away", 0)
            else:
                observation["home_score"] = event.data.get("home_score", 0)
                observation["away_score"] = event.data.get("away_score", 0)

        elif event.event_type == StreamEventType.GAME_EVENT:
            observation["home_score"] = event.data.get("home_score", 0)
            observation["away_score"] = event.data.get("away_score", 0)

        elif event.event_type == StreamEventType.PLAYER_STAT:
            # May contain partial score info
            if "home_score" in event.data and "away_score" in event.data:
                observation["home_score"] = event.data["home_score"]
                observation["away_score"] = event.data["away_score"]

        # Extract time and metadata
        observation["time_remaining"] = event.data.get("time_remaining", 0)
        observation["quarter"] = event.data.get("quarter")
        observation["possession"] = event.data.get("possession")

        return observation if observation else None

    def _calculate_time_delta(self) -> float:
        """Calculate time since last update in minutes"""
        if self.last_update_time is None:
            return 1.0

        elapsed_seconds = (datetime.now() - self.last_update_time).total_seconds()
        return elapsed_seconds / 60.0  # Convert to minutes

    def _is_significant_update(self, prev_state: Optional[GameState]) -> bool:
        """Check if update is significant enough to publish"""
        if prev_state is None:
            return True

        current_state = self.kalman_filter.get_state()
        if current_state is None:
            return False

        # Check score change
        score_change = abs(
            (current_state.home_score - current_state.away_score)
            - (prev_state.home_score - prev_state.away_score)
        )
        if score_change >= self.config.significant_score_change:
            return True

        # Check probability change
        prob_change = abs(current_state.home_win_prob - prev_state.home_win_prob)
        if prob_change >= self.config.significant_prob_change:
            return True

        # Always update on quarter change
        if current_state.quarter != prev_state.quarter:
            return True

        return False

    def _get_model_prediction(self) -> Optional[Dict[str, Any]]:
        """Get prediction from ML model"""
        if not self.simulation_service:
            return None

        state = self.kalman_filter.get_state()
        if state is None:
            return None

        # Create features for model (simplified)
        features = {
            "score_differential": state.home_score - state.away_score,
            "home_score_rate": state.home_score_rate,
            "away_score_rate": state.away_score_rate,
            "time_remaining": state.time_remaining,
            "quarter": float(state.quarter),
        }

        # This would call the actual simulation service
        # For now, return None to indicate no model available
        return None

    def _notify_callbacks(self, update: SimulationUpdate):
        """Notify all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def reset(self):
        """Reset simulator state"""
        self.kalman_filter.reset()
        self.initialized = False
        self.update_count = 0
        self.last_update_time = None
        self.update_history = []
        logger.info("Simulator reset")
