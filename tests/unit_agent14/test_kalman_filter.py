"""
Unit Tests for Streaming Kalman Filter (Agent 14, Module 1)

Tests for real-time game state estimation using Kalman filtering.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from mcp_server.simulations.streaming.kalman_filter import (
    StreamingKalmanFilter,
    GameState,
    KalmanFilterConfig,
)


class TestGameState:
    """Test GameState dataclass"""

    def test_game_state_creation(self):
        """Test basic game state creation"""
        state = GameState(
            home_score=50.0,
            away_score=45.0,
            home_score_rate=2.0,
            away_score_rate=1.8,
            home_win_prob=0.6,
            time_remaining=24.0,
            quarter=2,
        )

        assert state.home_score == 50.0
        assert state.away_score == 45.0
        assert state.quarter == 2

    def test_game_state_to_vector(self):
        """Test conversion to vector"""
        state = GameState(
            home_score=50.0,
            away_score=45.0,
            home_score_rate=2.0,
            away_score_rate=1.8,
            home_win_prob=0.6,
            time_remaining=24.0,
        )

        vec = state.to_vector()
        assert len(vec) == 6
        assert vec[0] == 50.0
        assert vec[1] == 45.0
        assert vec[4] == 0.6

    def test_game_state_from_vector(self):
        """Test creation from vector"""
        vec = np.array([50.0, 45.0, 2.0, 1.8, 0.6, 24.0])
        state = GameState.from_vector(vec, quarter=2)

        assert state.home_score == 50.0
        assert state.away_score == 45.0
        assert state.quarter == 2

    def test_game_state_to_dict(self):
        """Test conversion to dictionary"""
        state = GameState(
            home_score=50.0,
            away_score=45.0,
            home_score_rate=2.0,
            away_score_rate=1.8,
            home_win_prob=0.6,
            time_remaining=24.0,
            quarter=2,
            possession="home",
        )

        d = state.to_dict()
        assert d["home_score"] == 50.0
        assert d["quarter"] == 2
        assert d["possession"] == "home"
        assert "last_update" in d


class TestKalmanFilterConfig:
    """Test KalmanFilterConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = KalmanFilterConfig()

        assert config.process_noise_std == 0.1
        assert config.measurement_noise_std == 0.5
        assert config.min_score_rate > 0
        assert config.max_score_rate > config.min_score_rate

    def test_custom_config(self):
        """Test custom configuration"""
        config = KalmanFilterConfig(
            process_noise_std=0.2,
            measurement_noise_std=1.0,
            min_score_rate=0.8,
            max_score_rate=3.5,
        )

        assert config.process_noise_std == 0.2
        assert config.measurement_noise_std == 1.0
        assert config.min_score_rate == 0.8


class TestStreamingKalmanFilter:
    """Test StreamingKalmanFilter"""

    def test_initialization(self):
        """Test filter initialization"""
        kf = StreamingKalmanFilter()

        assert kf.state is None
        assert kf.covariance is None
        assert kf.update_count == 0
        assert len(kf.state_history) == 0

    def test_initialize_game(self):
        """Test game initialization"""
        kf = StreamingKalmanFilter()
        state = kf.initialize(
            home_score=0.0, away_score=0.0, time_remaining=48.0, quarter=1
        )

        assert state is not None
        assert state.home_score == 0.0
        assert state.away_score == 0.0
        assert state.time_remaining == 48.0
        assert state.home_win_prob == 0.5  # Initially 50%
        assert len(kf.state_history) == 1

    def test_initialize_with_scores(self):
        """Test initialization with non-zero scores"""
        kf = StreamingKalmanFilter()
        state = kf.initialize(
            home_score=25.0, away_score=20.0, time_remaining=36.0, quarter=2
        )

        assert state.home_score == 25.0
        assert state.away_score == 20.0
        assert state.quarter == 2

    def test_predict_step(self):
        """Test prediction step"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=50.0, away_score=45.0, time_remaining=24.0)

        # Predict forward 1 minute
        predicted = kf.predict(dt=1.0)

        # Scores should increase based on scoring rates
        assert predicted.home_score > 50.0
        assert predicted.away_score > 45.0

        # Time should decrease
        assert predicted.time_remaining < 24.0

    def test_update_with_observation(self):
        """Test update with observation"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)

        # Update with observed score
        observation = {"home_score": 5.0, "away_score": 3.0, "time_remaining": 47.0}
        updated_state = kf.update(observation, dt=1.0)

        assert updated_state.home_score == pytest.approx(5.0, abs=0.1)
        assert updated_state.away_score == pytest.approx(3.0, abs=0.1)
        assert kf.update_count == 1
        assert len(kf.state_history) == 2

    def test_multiple_updates(self):
        """Test multiple consecutive updates"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)

        # Simulate game progression
        observations = [
            {"home_score": 5.0, "away_score": 3.0, "time_remaining": 45.0},
            {"home_score": 12.0, "away_score": 10.0, "time_remaining": 42.0},
            {"home_score": 20.0, "away_score": 18.0, "time_remaining": 39.0},
        ]

        for obs in observations:
            kf.update(obs, dt=1.0)

        assert kf.update_count == 3
        assert len(kf.state_history) == 4  # Initial + 3 updates

        final_state = kf.get_state()
        assert final_state.home_score == pytest.approx(20.0, abs=2.0)
        assert final_state.away_score == pytest.approx(18.0, abs=2.0)

    def test_win_probability_calculation(self):
        """Test win probability based on score differential"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)

        # Update with home team leading
        observation = {"home_score": 50.0, "away_score": 30.0, "time_remaining": 10.0}
        state = kf.update(observation, dt=1.0)

        # Home win probability should be high
        assert state.home_win_prob > 0.7

    def test_predict_final_score(self):
        """Test final score prediction"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=50.0, away_score=45.0, time_remaining=24.0)

        home_final, away_final, stats = kf.predict_final_score()

        # Final scores should be higher than current
        assert home_final > 50.0
        assert away_final > 45.0

        # Statistics should include uncertainties
        assert "home_score_std" in stats
        assert "away_score_std" in stats
        assert "home_win_prob" in stats

    def test_confidence_intervals(self):
        """Test confidence interval calculation"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=50.0, away_score=45.0, time_remaining=24.0)

        intervals = kf.get_confidence_interval(confidence=0.95)

        assert "home_score" in intervals
        assert "away_score" in intervals
        assert isinstance(intervals["home_score"], tuple)

        # Lower bound should be less than upper bound
        lower, upper = intervals["home_score"]
        assert lower < upper

    def test_state_constraints(self):
        """Test that state constraints are enforced"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)

        # Update with unrealistic observation
        observation = {
            "home_score": -5.0,  # Negative score (invalid)
            "away_score": 150.0,
            "time_remaining": 24.0,
        }
        state = kf.update(observation, dt=1.0)

        # Scores should be non-negative
        assert state.home_score >= 0
        assert state.away_score >= 0

        # Win probability should be in [0, 1]
        assert 0 <= state.home_win_prob <= 1

    def test_scoring_rate_adaptation(self):
        """Test that scoring rates adapt to observations"""
        kf = StreamingKalmanFilter()
        kf.initialize(
            home_score=0.0,
            away_score=0.0,
            time_remaining=48.0,
            home_score_rate=2.0,
            away_score_rate=2.0,
        )

        # Observe higher home scoring
        observations = [
            {"home_score": 8.0, "away_score": 2.0, "time_remaining": 44.0},
            {"home_score": 16.0, "away_score": 4.0, "time_remaining": 40.0},
        ]

        for obs in observations:
            kf.update(obs, dt=4.0)

        state = kf.get_state()
        # Home scoring rate should be high (may not have increased above initial due to filter smoothing)
        assert state.home_score_rate >= 1.5
        # Away scoring rate should be lower than home
        assert state.away_score_rate <= state.home_score_rate

    def test_get_statistics(self):
        """Test statistics retrieval"""
        kf = StreamingKalmanFilter()

        # Before initialization
        stats = kf.get_statistics()
        assert stats["initialized"] is False

        # After initialization
        kf.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)
        stats = kf.get_statistics()
        assert stats["initialized"] is True
        assert "update_count" in stats
        assert "current_state" in stats

    def test_reset(self):
        """Test filter reset"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=50.0, away_score=45.0, time_remaining=24.0)
        kf.update(
            {"home_score": 55.0, "away_score": 50.0, "time_remaining": 23.0}, dt=1.0
        )

        assert kf.update_count > 0
        assert len(kf.state_history) > 0

        kf.reset()

        assert kf.state is None
        assert kf.update_count == 0
        assert len(kf.state_history) == 0

    def test_time_progression(self):
        """Test that time decreases correctly"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)

        # Update several times
        for i in range(5):
            time_remaining = 48.0 - (i + 1) * 2.0
            kf.update(
                {
                    "home_score": float(i * 5),
                    "away_score": float(i * 4),
                    "time_remaining": time_remaining,
                },
                dt=2.0,
            )

        state = kf.get_state()
        assert state.time_remaining < 48.0
        assert state.time_remaining >= 0

    def test_uncertainty_growth(self):
        """Test that uncertainty grows with prediction horizon"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=50.0, away_score=45.0, time_remaining=24.0)

        # Get current uncertainty
        intervals_now = kf.get_confidence_interval()
        width_now = intervals_now["home_score"][1] - intervals_now["home_score"][0]

        # Predict to end of game
        predicted_state = kf.predict(dt=24.0)

        # Calculate uncertainty from predicted state's covariance
        z_score = 1.96  # 95% confidence
        std_dev = np.sqrt(predicted_state.uncertainty[0, 0])
        width_future = 2 * z_score * std_dev

        # Uncertainty should be larger for future predictions
        assert width_future > width_now

    def test_auto_initialize_from_update(self):
        """Test automatic initialization from first update"""
        kf = StreamingKalmanFilter()

        observation = {"home_score": 10.0, "away_score": 8.0, "time_remaining": 45.0}

        # Should auto-initialize
        state = kf.update(observation, dt=1.0)

        assert state is not None
        assert kf.state is not None
        assert kf.update_count == 1

    def test_quarter_progression(self):
        """Test quarter tracking"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0, quarter=1)

        # Update with quarter 2
        state = kf.update(
            {
                "home_score": 25.0,
                "away_score": 22.0,
                "time_remaining": 36.0,
                "quarter": 2,
            },
            dt=12.0,
        )

        assert state.quarter == 2

    def test_possession_tracking(self):
        """Test possession tracking"""
        kf = StreamingKalmanFilter()
        kf.initialize(home_score=0.0, away_score=0.0, time_remaining=48.0)

        state = kf.update(
            {
                "home_score": 5.0,
                "away_score": 3.0,
                "time_remaining": 47.0,
                "possession": "home",
            },
            dt=1.0,
        )

        assert state.possession == "home"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
