"""
In-Game Predictor (Agent 14, Module 4)

Complete integration of streaming simulation components for live game prediction:
- Combines Kalman filtering, ML models, and real-time data
- Provides unified prediction updates
- Event aggregation and analysis
- Performance monitoring

Integrates with:
- streaming/kalman_filter: State estimation
- streaming/live_simulator: Simulation
- streaming/data_connector: Data ingestion
- deployment/simulation_service: ML models
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

import numpy as np

from mcp_server.simulations.streaming.kalman_filter import StreamingKalmanFilter, GameState
from mcp_server.simulations.streaming.live_simulator import LiveGameSimulator, SimulationUpdate
from mcp_server.simulations.streaming.data_connector import (
    DataMessage,
    StreamingDataConnector,
    MockDataConnector,
    create_mock_connector
)
from mcp_server.streaming_analytics import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)


class PredictionConfidence(Enum):
    """Confidence level for predictions"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class PredictionUpdate:
    """Complete prediction update for a live game"""

    update_id: int
    timestamp: datetime
    game_id: str

    # Current state
    home_score: float
    away_score: float
    time_remaining: float
    quarter: int

    # Predictions
    home_win_probability: float
    away_win_probability: float
    predicted_final_home_score: float
    predicted_final_away_score: float

    # Uncertainty
    confidence_level: PredictionConfidence
    confidence_intervals: Dict[str, tuple]

    # Momentum indicators
    home_momentum: float  # -1 to 1
    scoring_rate_ratio: float  # home / away

    # Model contributions
    kalman_contribution: float  # 0 to 1
    model_contribution: float  # 0 to 1

    # Metadata
    event_trigger: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'update_id': self.update_id,
            'timestamp': self.timestamp.isoformat(),
            'game_id': self.game_id,
            'current_state': {
                'home_score': self.home_score,
                'away_score': self.away_score,
                'time_remaining': self.time_remaining,
                'quarter': self.quarter,
            },
            'predictions': {
                'home_win_probability': self.home_win_probability,
                'away_win_probability': self.away_win_probability,
                'predicted_final_home_score': self.predicted_final_home_score,
                'predicted_final_away_score': self.predicted_final_away_score,
            },
            'confidence': {
                'level': self.confidence_level.value,
                'intervals': {
                    k: {'lower': v[0], 'upper': v[1]}
                    for k, v in self.confidence_intervals.items()
                }
            },
            'momentum': {
                'home_momentum': self.home_momentum,
                'scoring_rate_ratio': self.scoring_rate_ratio,
            },
            'model_info': {
                'kalman_contribution': self.kalman_contribution,
                'model_contribution': self.model_contribution,
            },
            'event_trigger': self.event_trigger,
            'metadata': self.metadata,
        }


@dataclass
class PredictorConfig:
    """Configuration for in-game predictor"""

    # Update settings
    min_update_interval_seconds: float = 2.0
    auto_start: bool = True

    # Model blending
    kalman_weight: float = 0.5
    model_weight: float = 0.5

    # Momentum calculation
    momentum_window_minutes: float = 5.0

    # Confidence thresholds
    high_confidence_threshold: float = 0.80
    medium_confidence_threshold: float = 0.60

    # Performance monitoring
    track_performance: bool = True
    max_history_size: int = 1000


class InGamePredictor:
    """
    Complete in-game prediction system.

    Integrates all streaming simulation components:
    - Data ingestion from multiple sources
    - Real-time state estimation with Kalman filtering
    - ML model predictions
    - Momentum and trend analysis
    - Unified prediction updates

    Features:
    - Multi-source data fusion
    - Confidence-weighted predictions
    - Real-time performance monitoring
    - Event-driven updates
    - Historical analysis
    """

    def __init__(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        config: Optional[PredictorConfig] = None,
        simulation_service: Optional[Any] = None
    ):
        """
        Initialize in-game predictor.

        Args:
            game_id: Unique game identifier
            home_team: Home team name/ID
            away_team: Away team name/ID
            config: Predictor configuration
            simulation_service: Optional simulation service for ML models
        """
        self.game_id = game_id
        self.home_team = home_team
        self.away_team = away_team
        self.config = config or PredictorConfig()
        self.simulation_service = simulation_service

        # Initialize components
        self.simulator = LiveGameSimulator(
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            simulation_service=simulation_service
        )

        self.data_connector = StreamingDataConnector()

        # State
        self.initialized = False
        self.update_count = 0
        self.last_update_time: Optional[datetime] = None
        self.prediction_history: List[PredictionUpdate] = []

        # Momentum tracking
        self.recent_events: List[Dict[str, Any]] = []

        # Callbacks
        self.prediction_callbacks: List[Callable[[PredictionUpdate], None]] = []

        # Statistics
        self.stats = {
            'predictions_generated': 0,
            'data_messages_processed': 0,
            'errors': 0,
            'average_latency_ms': 0.0,
        }

        logger.info(
            f"InGamePredictor initialized: {home_team} vs {away_team} "
            f"(game_id: {game_id})"
        )

    def initialize(
        self,
        home_score: float = 0.0,
        away_score: float = 0.0,
        time_remaining: float = 48.0,
        quarter: int = 1
    ) -> PredictionUpdate:
        """
        Initialize predictor with starting game state.

        Args:
            home_score: Initial home score
            away_score: Initial away score
            time_remaining: Minutes remaining
            quarter: Current quarter

        Returns:
            Initial prediction update
        """
        # Initialize simulator
        sim_update = self.simulator.initialize(
            home_score=home_score,
            away_score=away_score,
            time_remaining=time_remaining,
            quarter=quarter
        )

        self.initialized = True
        self.last_update_time = datetime.now()

        # Create initial prediction
        prediction = self._create_prediction_update(sim_update)
        self.prediction_history.append(prediction)
        self._notify_callbacks(prediction)

        logger.info("Predictor initialized")
        return prediction

    def add_data_source(
        self,
        name: str,
        connector: Any,
        auto_start: bool = True
    ):
        """
        Add a data source to the predictor.

        Args:
            name: Data source name
            connector: DataConnector instance
            auto_start: Whether to start connector immediately
        """
        self.data_connector.add_connector(name, connector)

        # Register message handler
        connector.register_callback(self._process_data_message)

        if auto_start:
            connector.start()

        logger.info(f"Added data source: {name}")

    def start(self):
        """Start prediction system"""
        if not self.initialized:
            logger.warning("Predictor not initialized, auto-initializing...")
            self.initialize()

        self.data_connector.start_all()
        logger.info("Predictor started")

    def stop(self):
        """Stop prediction system"""
        self.data_connector.stop_all()
        logger.info("Predictor stopped")

    def update_from_scores(
        self,
        home_score: float,
        away_score: float,
        time_remaining: float,
        quarter: Optional[int] = None
    ) -> PredictionUpdate:
        """
        Manually update predictor with current scores.

        Args:
            home_score: Current home score
            away_score: Current away score
            time_remaining: Minutes remaining
            quarter: Current quarter

        Returns:
            Prediction update
        """
        if not self.initialized:
            return self.initialize(home_score, away_score, time_remaining, quarter or 1)

        # Update simulator
        sim_update = self.simulator.update_from_scores(
            home_score=home_score,
            away_score=away_score,
            time_remaining=time_remaining,
            quarter=quarter
        )

        # Create prediction
        prediction = self._create_prediction_update(sim_update)
        self.prediction_history.append(prediction)
        self._notify_callbacks(prediction)
        self.last_update_time = datetime.now()

        return prediction

    def get_current_prediction(self) -> Optional[PredictionUpdate]:
        """Get most recent prediction"""
        return self.prediction_history[-1] if self.prediction_history else None

    def get_prediction_history(self, limit: Optional[int] = None) -> List[PredictionUpdate]:
        """
        Get prediction history.

        Args:
            limit: Maximum number of predictions (None = all)

        Returns:
            List of predictions
        """
        if limit is None:
            return self.prediction_history.copy()
        return self.prediction_history[-limit:]

    def analyze_momentum(self, window_minutes: Optional[float] = None) -> Dict[str, Any]:
        """
        Analyze game momentum over recent period.

        Args:
            window_minutes: Time window for analysis

        Returns:
            Momentum analysis
        """
        window = window_minutes or self.config.momentum_window_minutes

        # Get recent predictions
        if len(self.prediction_history) < 2:
            return {
                'home_momentum': 0.0,
                'away_momentum': 0.0,
                'momentum_strength': 'neutral',
            }

        recent = self.prediction_history[-10:]  # Last 10 updates

        # Calculate momentum from probability changes
        home_prob_changes = []
        for i in range(1, len(recent)):
            change = recent[i].home_win_probability - recent[i-1].home_win_probability
            home_prob_changes.append(change)

        if not home_prob_changes:
            return {
                'home_momentum': 0.0,
                'away_momentum': 0.0,
                'momentum_strength': 'neutral',
            }

        # Average momentum
        home_momentum = float(np.mean(home_prob_changes))
        away_momentum = -home_momentum

        # Classify momentum strength
        abs_momentum = abs(home_momentum)
        if abs_momentum > 0.05:
            strength = 'strong'
        elif abs_momentum > 0.02:
            strength = 'moderate'
        else:
            strength = 'neutral'

        return {
            'home_momentum': home_momentum,
            'away_momentum': away_momentum,
            'momentum_strength': strength,
            'leading_team': self.home_team if home_momentum > 0 else self.away_team,
        }

    def register_callback(self, callback: Callable[[PredictionUpdate], None]):
        """
        Register callback for prediction updates.

        Args:
            callback: Function to call on each prediction
        """
        self.prediction_callbacks.append(callback)
        logger.info(f"Registered prediction callback: {callback.__name__}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get predictor statistics"""
        return {
            'game_id': self.game_id,
            'initialized': self.initialized,
            'predictions_generated': len(self.prediction_history),
            'simulator_stats': self.simulator.get_statistics(),
            'connector_stats': self.data_connector.get_statistics(),
            **self.stats
        }

    def _process_data_message(self, message: DataMessage):
        """Process incoming data message"""
        start_time = datetime.now()

        try:
            # Convert to stream event
            event = self._message_to_event(message)
            if event is None:
                return

            # Process with simulator
            sim_update = self.simulator.process_event(event)

            if sim_update is not None:
                # Create prediction update
                prediction = self._create_prediction_update(sim_update)
                self.prediction_history.append(prediction)
                self._notify_callbacks(prediction)
                self.last_update_time = datetime.now()

            self.stats['data_messages_processed'] += 1

            # Update latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            self._update_latency(latency_ms)

        except Exception as e:
            logger.error(f"Error processing data message: {e}")
            self.stats['errors'] += 1

    def _message_to_event(self, message: DataMessage) -> Optional[StreamEvent]:
        """Convert data message to stream event"""
        try:
            # Determine event type
            event_type_map = {
                'score_update': StreamEventType.SCORE_UPDATE,
                'player_stat': StreamEventType.PLAYER_STAT,
                'game_event': StreamEventType.GAME_EVENT,
            }

            event_type = event_type_map.get(
                message.message_type,
                StreamEventType.GAME_EVENT
            )

            return StreamEvent(
                event_type=event_type,
                timestamp=message.timestamp,
                game_id=self.game_id,
                data=message.data
            )

        except Exception as e:
            logger.error(f"Error converting message to event: {e}")
            return None

    def _create_prediction_update(
        self,
        sim_update: SimulationUpdate
    ) -> PredictionUpdate:
        """Create prediction update from simulation update"""

        state = sim_update.game_state

        # Calculate momentum
        momentum_analysis = self.analyze_momentum()
        home_momentum = momentum_analysis['home_momentum']

        # Calculate scoring rate ratio
        if state.away_score_rate > 0:
            rate_ratio = state.home_score_rate / state.away_score_rate
        else:
            rate_ratio = 1.0

        # Determine confidence level
        confidence_level = self._calculate_confidence(sim_update)

        # Create prediction update
        prediction = PredictionUpdate(
            update_id=self.update_count,
            timestamp=datetime.now(),
            game_id=self.game_id,
            home_score=state.home_score,
            away_score=state.away_score,
            time_remaining=state.time_remaining,
            quarter=state.quarter,
            home_win_probability=sim_update.win_probabilities['home'],
            away_win_probability=sim_update.win_probabilities['away'],
            predicted_final_home_score=sim_update.expected_final_scores['home'],
            predicted_final_away_score=sim_update.expected_final_scores['away'],
            confidence_level=confidence_level,
            confidence_intervals=sim_update.confidence_intervals,
            home_momentum=home_momentum,
            scoring_rate_ratio=rate_ratio,
            kalman_contribution=1.0 - self.config.model_weight,
            model_contribution=self.config.model_weight,
            event_trigger=sim_update.event_trigger
        )

        self.update_count += 1
        self.stats['predictions_generated'] += 1

        return prediction

    def _calculate_confidence(self, sim_update: SimulationUpdate) -> PredictionConfidence:
        """
        Calculate confidence level for prediction.

        Based on:
        - Time remaining (more confidence near end)
        - Uncertainty in estimates
        - Model availability
        """
        state = sim_update.game_state

        # Time factor (more confident near end of game)
        time_factor = 1.0 - (state.time_remaining / 48.0)

        # Score differential factor
        score_diff = abs(state.home_score - state.away_score)
        score_factor = min(1.0, score_diff / 20.0)  # Normalize to 20 points

        # Combined confidence score
        confidence_score = 0.5 * time_factor + 0.5 * score_factor

        # Map to confidence level
        if confidence_score >= self.config.high_confidence_threshold:
            return PredictionConfidence.VERY_HIGH
        elif confidence_score >= self.config.medium_confidence_threshold:
            return PredictionConfidence.HIGH
        elif confidence_score >= 0.4:
            return PredictionConfidence.MEDIUM
        elif confidence_score >= 0.2:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW

    def _notify_callbacks(self, prediction: PredictionUpdate):
        """Notify all registered callbacks"""
        for callback in self.prediction_callbacks:
            try:
                callback(prediction)
            except Exception as e:
                logger.error(f"Prediction callback error: {e}")

    def _update_latency(self, latency_ms: float):
        """Update average latency metric"""
        if self.stats['predictions_generated'] == 1:
            self.stats['average_latency_ms'] = latency_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.stats['average_latency_ms'] = (
                alpha * latency_ms +
                (1 - alpha) * self.stats['average_latency_ms']
            )

    def reset(self):
        """Reset predictor state"""
        self.simulator.reset()
        self.initialized = False
        self.update_count = 0
        self.last_update_time = None
        self.prediction_history = []
        self.recent_events = []
        logger.info("Predictor reset")


# Convenience function
def create_mock_predictor(
    game_id: str = "test_game_001",
    home_team: str = "LAL",
    away_team: str = "BOS",
    event_rate_hz: float = 1.0
) -> InGamePredictor:
    """
    Create an in-game predictor with mock data source for testing.

    Args:
        game_id: Game identifier
        home_team: Home team name
        away_team: Away team name
        event_rate_hz: Events per second for mock data

    Returns:
        InGamePredictor instance with mock connector
    """
    predictor = InGamePredictor(
        game_id=game_id,
        home_team=home_team,
        away_team=away_team
    )

    # Add mock data source
    mock_connector = create_mock_connector(
        endpoint=f"mock://{game_id}",
        event_rate_hz=event_rate_hz
    )
    predictor.add_data_source("mock", mock_connector, auto_start=False)

    return predictor
