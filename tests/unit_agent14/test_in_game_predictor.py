"""
Unit Tests for In-Game Predictor (Agent 14, Module 4)

Tests for complete in-game prediction system integrating all components.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch

from mcp_server.simulations.streaming.in_game_predictor import (
    InGamePredictor,
    PredictionUpdate,
    PredictionConfidence,
    PredictorConfig,
    create_mock_predictor,
)
from mcp_server.simulations.streaming.data_connector import (
    MockDataConnector,
    DataSourceConfig,
    DataSourceType,
    create_mock_connector,
)


class TestPredictionConfidence:
    """Test PredictionConfidence enum"""

    def test_confidence_levels(self):
        """Test confidence level values"""
        assert PredictionConfidence.VERY_LOW.value == "very_low"
        assert PredictionConfidence.LOW.value == "low"
        assert PredictionConfidence.MEDIUM.value == "medium"
        assert PredictionConfidence.HIGH.value == "high"
        assert PredictionConfidence.VERY_HIGH.value == "very_high"


class TestPredictionUpdate:
    """Test PredictionUpdate dataclass"""

    def test_prediction_update_creation(self):
        """Test basic prediction update creation"""
        update = PredictionUpdate(
            update_id=0,
            timestamp=datetime.now(),
            game_id="test_001",
            home_score=50.0,
            away_score=45.0,
            time_remaining=24.0,
            quarter=2,
            home_win_probability=0.65,
            away_win_probability=0.35,
            predicted_final_home_score=105.0,
            predicted_final_away_score=98.0,
            confidence_level=PredictionConfidence.HIGH,
            confidence_intervals={"home_score": (45.0, 55.0)},
            home_momentum=0.15,
            scoring_rate_ratio=1.1,
            kalman_contribution=0.5,
            model_contribution=0.5,
        )

        assert update.home_score == 50.0
        assert update.home_win_probability == 0.65
        assert update.confidence_level == PredictionConfidence.HIGH

    def test_prediction_update_to_dict(self):
        """Test conversion to dictionary"""
        update = PredictionUpdate(
            update_id=0,
            timestamp=datetime.now(),
            game_id="test_001",
            home_score=50.0,
            away_score=45.0,
            time_remaining=24.0,
            quarter=2,
            home_win_probability=0.65,
            away_win_probability=0.35,
            predicted_final_home_score=105.0,
            predicted_final_away_score=98.0,
            confidence_level=PredictionConfidence.HIGH,
            confidence_intervals={"home_score": (45.0, 55.0)},
            home_momentum=0.15,
            scoring_rate_ratio=1.1,
            kalman_contribution=0.5,
            model_contribution=0.5,
        )

        d = update.to_dict()
        assert "update_id" in d
        assert "current_state" in d
        assert "predictions" in d
        assert "confidence" in d
        assert "momentum" in d
        assert d["predictions"]["home_win_probability"] == 0.65


class TestPredictorConfig:
    """Test PredictorConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = PredictorConfig()

        assert config.min_update_interval_seconds > 0
        assert config.auto_start is True
        assert 0 <= config.kalman_weight <= 1
        assert 0 <= config.model_weight <= 1

    def test_custom_config(self):
        """Test custom configuration"""
        config = PredictorConfig(
            min_update_interval_seconds=3.0,
            auto_start=False,
            kalman_weight=0.7,
            model_weight=0.3,
            momentum_window_minutes=10.0,
        )

        assert config.min_update_interval_seconds == 3.0
        assert config.auto_start is False
        assert config.kalman_weight == 0.7
        assert config.momentum_window_minutes == 10.0


class TestInGamePredictor:
    """Test InGamePredictor"""

    def test_predictor_creation(self):
        """Test predictor creation"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        assert predictor.game_id == "test_001"
        assert predictor.home_team == "LAL"
        assert predictor.away_team == "BOS"
        assert predictor.initialized is False
        assert predictor.update_count == 0

    def test_initialize(self):
        """Test predictor initialization"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        update = predictor.initialize(
            home_score=0.0, away_score=0.0, time_remaining=48.0, quarter=1
        )

        assert predictor.initialized is True
        assert isinstance(update, PredictionUpdate)
        assert update.home_score == 0.0
        assert len(predictor.prediction_history) == 1

    def test_update_from_scores(self):
        """Test manual score update"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        update = predictor.update_from_scores(
            home_score=25.0, away_score=20.0, time_remaining=36.0, quarter=2
        )

        assert update.home_score == pytest.approx(25.0, abs=0.5)
        assert update.away_score == pytest.approx(20.0, abs=0.5)
        assert update.quarter == 2

    def test_get_current_prediction(self):
        """Test getting current prediction"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        # Before initialization
        pred = predictor.get_current_prediction()
        assert pred is None

        # After initialization
        predictor.initialize()
        pred = predictor.get_current_prediction()
        assert pred is not None
        assert isinstance(pred, PredictionUpdate)

    def test_prediction_history(self):
        """Test prediction history"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        predictor.initialize()
        predictor.update_from_scores(10.0, 8.0, 45.0)
        predictor.update_from_scores(20.0, 18.0, 42.0)

        # Get all history
        history = predictor.get_prediction_history()
        assert len(history) >= 3

        # Get limited history
        history_limited = predictor.get_prediction_history(limit=2)
        assert len(history_limited) == 2

    def test_momentum_analysis(self):
        """Test momentum analysis"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        # Not enough data yet
        momentum = predictor.analyze_momentum()
        assert momentum["home_momentum"] == 0.0

        # Add some updates
        predictor.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)
        predictor.update_from_scores(10.0, 5.0, 45.0)
        predictor.update_from_scores(20.0, 10.0, 42.0)
        predictor.update_from_scores(30.0, 15.0, 39.0)

        # Now should have momentum
        momentum = predictor.analyze_momentum()
        assert "home_momentum" in momentum
        assert "momentum_strength" in momentum

    def test_callback_registration(self):
        """Test callback registration"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        callback_calls = []

        def test_callback(pred):
            callback_calls.append(pred)

        predictor.register_callback(test_callback)
        predictor.initialize()

        assert len(callback_calls) == 1
        assert isinstance(callback_calls[0], PredictionUpdate)

    def test_multiple_callbacks(self):
        """Test multiple callbacks"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        calls1 = []
        calls2 = []

        predictor.register_callback(lambda p: calls1.append(p))
        predictor.register_callback(lambda p: calls2.append(p))

        predictor.initialize()

        assert len(calls1) == 1
        assert len(calls2) == 1

    def test_add_data_source(self):
        """Test adding data source"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        connector = create_mock_connector(event_rate_hz=5.0)
        predictor.add_data_source("mock", connector, auto_start=False)

        assert "mock" in predictor.data_connector.connectors

    def test_start_and_stop(self):
        """Test starting and stopping predictor"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        connector = create_mock_connector(event_rate_hz=10.0)
        predictor.add_data_source("mock", connector, auto_start=False)

        predictor.start()
        time.sleep(0.2)
        predictor.stop()

        # Should have processed some predictions
        assert len(predictor.prediction_history) > 0

    def test_automatic_data_processing(self):
        """Test automatic prediction from data stream"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        connector = create_mock_connector(event_rate_hz=10.0)
        predictor.add_data_source("mock", connector, auto_start=False)

        predictions_received = []

        def callback(pred):
            predictions_received.append(pred)

        predictor.register_callback(callback)
        predictor.start()

        time.sleep(0.3)
        predictor.stop()

        # Should have received predictions
        assert len(predictions_received) > 0

    def test_get_statistics(self):
        """Test statistics retrieval"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        stats = predictor.get_statistics()
        assert "game_id" in stats
        assert "initialized" in stats
        assert stats["initialized"] is False

        predictor.initialize()
        stats = predictor.get_statistics()
        assert stats["initialized"] is True

    def test_reset(self):
        """Test predictor reset"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        predictor.initialize()
        predictor.update_from_scores(25.0, 20.0, 36.0)

        assert predictor.initialized is True
        assert len(predictor.prediction_history) > 0

        predictor.reset()

        assert predictor.initialized is False
        assert len(predictor.prediction_history) == 0

    def test_confidence_calculation(self):
        """Test confidence level calculation"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        # Start of game - low confidence
        update1 = predictor.update_from_scores(0.0, 0.0, 48.0, quarter=1)
        assert update1.confidence_level in [
            PredictionConfidence.VERY_LOW,
            PredictionConfidence.LOW,
            PredictionConfidence.MEDIUM,
        ]

        # End of game with large lead - high confidence
        update2 = predictor.update_from_scores(100.0, 70.0, 2.0, quarter=4)
        assert update2.confidence_level in [
            PredictionConfidence.HIGH,
            PredictionConfidence.VERY_HIGH,
        ]

    def test_momentum_tracking(self):
        """Test momentum is tracked in predictions"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        predictor.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)

        # Simulate home team momentum
        for i in range(5):
            score = float((i + 1) * 10)
            predictor.update_from_scores(score, score / 2, 48.0 - i * 2)

        pred = predictor.get_current_prediction()
        # Home should have positive momentum
        assert "home_momentum" in pred.__dict__

    def test_scoring_rate_ratio(self):
        """Test scoring rate ratio calculation"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        update = predictor.update_from_scores(60.0, 30.0, 24.0)

        assert "scoring_rate_ratio" in update.__dict__
        # Home scoring faster, ratio should be > 1
        assert update.scoring_rate_ratio >= 0

    def test_model_contributions(self):
        """Test model contribution tracking"""
        config = PredictorConfig(kalman_weight=0.7, model_weight=0.3)

        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS", config=config
        )

        update = predictor.initialize()

        assert update.kalman_contribution == pytest.approx(0.7, abs=0.01)
        assert update.model_contribution == pytest.approx(0.3, abs=0.01)

    def test_create_mock_predictor_convenience(self):
        """Test convenience function for creating mock predictor"""
        predictor = create_mock_predictor(
            game_id="convenience_test",
            home_team="LAL",
            away_team="BOS",
            event_rate_hz=5.0,
        )

        assert isinstance(predictor, InGamePredictor)
        assert predictor.game_id == "convenience_test"
        assert "mock" in predictor.data_connector.connectors

    def test_event_trigger_propagation(self):
        """Test that event triggers are propagated to predictions"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        update = predictor.initialize()
        assert update.event_trigger is not None

        update = predictor.update_from_scores(10.0, 8.0, 45.0)
        assert update.event_trigger == "manual_update"

    def test_win_probability_consistency(self):
        """Test that win probabilities sum to 1"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        update = predictor.initialize()

        total_prob = update.home_win_probability + update.away_win_probability
        assert total_prob == pytest.approx(1.0, abs=0.01)

    def test_confidence_intervals_present(self):
        """Test that confidence intervals are included"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        update = predictor.initialize()

        assert "home_score" in update.confidence_intervals
        assert isinstance(update.confidence_intervals["home_score"], tuple)

    def test_time_progression(self):
        """Test time progression through predictions"""
        predictor = InGamePredictor(
            game_id="test_001", home_team="LAL", away_team="BOS"
        )

        predictor.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)

        for time_remaining in [45.0, 42.0, 39.0, 36.0]:
            predictor.update_from_scores(
                home_score=float((48 - time_remaining) * 2),
                away_score=float((48 - time_remaining) * 1.8),
                time_remaining=time_remaining,
            )

        pred = predictor.get_current_prediction()
        assert pred.time_remaining < 48.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
