"""
Tests for Particle Filter Methods.

Tests base particle filter, player performance tracking, and live game probability.
"""

import pytest
import numpy as np
import pandas as pd

from mcp_server.particle_filters import (
    ParticleFilter,
    ParticleFilterResult,
    PlayerPerformanceParticleFilter,
    PlayerPerformanceResult,
    LiveGameProbabilityFilter,
    GameStateResult,
    compute_ess,
    systematic_resampling,
    multinomial_resampling,
    stratified_resampling,
    diagnose_particle_degeneracy,
    compare_resampling_methods,
    create_player_filter,
    create_game_filter,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def simple_observations():
    """Generate simple observation sequence."""
    np.random.seed(42)
    T = 50
    true_state = 10.0 + np.cumsum(np.random.normal(0, 0.1, T))
    observations = true_state + np.random.normal(0, 0.5, T)
    return observations[:, None]


@pytest.fixture
def player_game_log():
    """Generate synthetic player game log."""
    np.random.seed(123)
    T = 40  # 40 games

    dates = pd.date_range("2024-01-01", periods=T, freq="2D")

    # Simulate player with declining form
    skill = 20
    form = np.zeros(T)
    form[0] = 0
    for t in range(1, T):
        form[t] = 0.7 * form[t - 1] + np.random.normal(0, 1)

    points = np.random.poisson(np.exp(np.log(skill) + form * 0.05))

    return pd.DataFrame({"points": points, "minutes": 30}, index=dates)


@pytest.fixture
def score_updates():
    """Generate score updates for a close game."""
    return [
        (12.0, 25, 22),  # End Q1
        (24.0, 48, 45),  # Halftime
        (36.0, 70, 68),  # End Q3
        (48.0, 95, 92),  # Final
    ]


# ==============================================================================
# Resampling Algorithm Tests
# ==============================================================================


class TestResamplingAlgorithms:
    """Tests for resampling algorithms."""

    def test_compute_ess_uniform(self):
        """Test ESS with uniform weights."""
        weights = np.ones(100) / 100
        ess = compute_ess(weights)
        assert np.isclose(ess, 100.0), "ESS should equal N for uniform weights"

    def test_compute_ess_degenerate(self):
        """Test ESS with degenerate weights."""
        weights = np.zeros(100)
        weights[0] = 1.0
        ess = compute_ess(weights)
        assert np.isclose(ess, 1.0), "ESS should be 1 for single particle"

    def test_systematic_resampling_preserves_count(self):
        """Test systematic resampling returns correct number of indices."""
        weights = np.random.dirichlet(np.ones(100))
        indices = systematic_resampling(weights)
        assert len(indices) == 100
        assert np.all(indices >= 0)
        assert np.all(indices < 100)

    def test_systematic_resampling_respects_weights(self):
        """Test systematic resampling favors high-weight particles."""
        weights = np.zeros(100)
        weights[50] = 1.0  # All weight on one particle

        # Run multiple times to check consistency
        counts = np.zeros(100)
        for _ in range(10):
            indices = systematic_resampling(weights)
            for idx in indices:
                counts[idx] += 1

        # Particle 50 should be resampled most often
        assert counts[50] > counts.sum() * 0.8

    def test_multinomial_resampling(self):
        """Test multinomial resampling."""
        weights = np.random.dirichlet(np.ones(100))
        indices = multinomial_resampling(weights)
        assert len(indices) == 100

    def test_stratified_resampling(self):
        """Test stratified resampling."""
        weights = np.random.dirichlet(np.ones(100))
        indices = stratified_resampling(weights)
        assert len(indices) == 100


# ==============================================================================
# Base Particle Filter Tests
# ==============================================================================


class TestBaseParticleFilter:
    """Tests for base ParticleFilter class."""

    def test_initialization(self):
        """Test particle filter initialization."""
        pf = ParticleFilter(n_particles=500, state_dim=2)
        assert pf.n_particles == 500
        assert pf.state_dim == 2
        assert pf.resampling_threshold == 0.5

    def test_initialization_errors(self):
        """Test initialization error handling."""
        with pytest.raises(ValueError, match="at least 100"):
            ParticleFilter(n_particles=50)

        with pytest.raises(ValueError, match="must be >= 1"):
            ParticleFilter(state_dim=0)

        with pytest.raises(ValueError, match="Unknown resampling_method"):
            ParticleFilter(resampling_method="invalid")

    def test_initialize_particles_1d(self):
        """Test particle initialization for 1D state."""
        pf = ParticleFilter(n_particles=1000, state_dim=1)
        pf.initialize_particles(initial_state=np.array([5.0]), initial_variance=1.0)

        assert pf.particles.shape == (1000, 1)
        assert pf.weights.shape == (1000,)
        assert np.isclose(np.mean(pf.particles), 5.0, atol=0.5)

    def test_initialize_particles_2d(self):
        """Test particle initialization for 2D state."""
        pf = ParticleFilter(n_particles=1000, state_dim=2)
        pf.initialize_particles(
            initial_state=np.array([5.0, 10.0]), initial_variance=1.0
        )

        assert pf.particles.shape == (1000, 2)
        assert np.isclose(np.mean(pf.particles[:, 0]), 5.0, atol=0.5)
        assert np.isclose(np.mean(pf.particles[:, 1]), 10.0, atol=0.5)

    def test_predict_requires_transition_fn(self):
        """Test that predict() requires transition function."""
        pf = ParticleFilter(n_particles=100)
        pf.initialize_particles(initial_state=np.array([0.0]))

        with pytest.raises(ValueError, match="transition_fn not set"):
            pf.predict()

    def test_update_requires_observation_fn(self):
        """Test that update() requires observation function."""
        pf = ParticleFilter(n_particles=100)
        pf.initialize_particles(initial_state=np.array([0.0]))

        with pytest.raises(ValueError, match="observation_fn not set"):
            pf.update(observation=np.array([1.0]))

    def test_get_state_estimate(self):
        """Test state estimation from particles."""
        pf = ParticleFilter(n_particles=1000)
        pf.particles = np.random.normal(10, 2, size=(1000, 1))
        pf.weights = np.ones(1000) / 1000

        mean, variance = pf.get_state_estimate()

        assert np.isclose(mean[0], 10.0, atol=0.3)
        assert np.isclose(variance[0], 4.0, atol=0.5)

    def test_resample_if_needed_low_ess(self):
        """Test resampling triggers when ESS is low."""
        pf = ParticleFilter(n_particles=100, resampling_threshold=0.5)
        pf.particles = np.random.normal(0, 1, size=(100, 1))

        # Create degenerate weights (low ESS)
        pf.weights = np.zeros(100)
        pf.weights[0] = 1.0

        resampled = pf.resample_if_needed()

        assert resampled is True
        # After resampling, weights should be uniform
        assert np.allclose(pf.weights, 1.0 / 100)

    def test_resample_if_needed_high_ess(self):
        """Test resampling doesn't trigger when ESS is high."""
        pf = ParticleFilter(n_particles=100, resampling_threshold=0.5)
        pf.particles = np.random.normal(0, 1, size=(100, 1))
        pf.weights = np.ones(100) / 100  # Uniform = high ESS

        resampled = pf.resample_if_needed()

        assert resampled is False

    def test_filter_with_custom_functions(self):
        """Test full filtering with custom transition and observation."""

        def simple_transition(particles, **kwargs):
            # Random walk
            return particles + np.random.normal(0, 0.1, size=particles.shape)

        def simple_observation(particles, observation, **kwargs):
            # Gaussian likelihood
            from scipy import stats

            return stats.norm.pdf(observation[0], loc=particles[:, 0], scale=0.5)

        pf = ParticleFilter(
            n_particles=500,
            state_dim=1,
            transition_fn=simple_transition,
            observation_fn=simple_observation,
        )

        # Generate observations
        true_state = np.array([0.0])
        observations = []
        for _ in range(20):
            true_state += np.random.normal(0, 0.1)
            obs = true_state + np.random.normal(0, 0.5)
            observations.append(obs)

        observations = np.array(observations)

        result = pf.filter(observations, initial_state=np.array([0.0]))

        assert isinstance(result, ParticleFilterResult)
        assert result.states.shape == (20, 1)
        assert len(result.ess_history) == 20
        assert len(result.resampling_history) == 20


# ==============================================================================
# Player Performance Filter Tests
# ==============================================================================


class TestPlayerPerformanceParticleFilter:
    """Tests for PlayerPerformanceParticleFilter."""

    def test_initialization(self):
        """Test player filter initialization."""
        pf = PlayerPerformanceParticleFilter(n_particles=1000)

        assert pf.n_particles == 1000
        assert pf.state_dim == 2  # [skill, form]
        assert pf.skill_drift == 0.0
        assert pf.skill_volatility == 0.05
        assert pf.form_persistence == 0.7
        assert pf.form_volatility == 0.2

    def test_custom_parameters(self):
        """Test initialization with custom parameters."""
        pf = PlayerPerformanceParticleFilter(
            n_particles=500,
            skill_drift=0.01,
            skill_volatility=0.1,
            form_persistence=0.8,
            form_volatility=0.3,
        )

        assert pf.skill_drift == 0.01
        assert pf.skill_volatility == 0.1
        assert pf.form_persistence == 0.8
        assert pf.form_volatility == 0.3

    def test_transition_model(self):
        """Test state transition model."""
        pf = PlayerPerformanceParticleFilter(n_particles=1000)
        pf.initialize_particles(initial_state=np.array([3.0, 0.0]))

        initial_particles = pf.particles.copy()

        # Apply transition
        new_particles = pf._transition_model(initial_particles)

        # Check dimensions
        assert new_particles.shape == (1000, 2)

        # Skill should change (random walk with drift)
        assert not np.allclose(new_particles[:, 0], initial_particles[:, 0])

        # Form should change (AR process)
        assert not np.allclose(new_particles[:, 1], initial_particles[:, 1])

    def test_observation_likelihood(self):
        """Test observation likelihood computation."""
        pf = PlayerPerformanceParticleFilter(n_particles=100)
        pf.initialize_particles(initial_state=np.array([3.0, 0.0]))

        # Compute likelihoods for observation = 20 points
        likelihoods = pf._observation_likelihood(
            pf.particles, observation=np.array([20])
        )

        assert len(likelihoods) == 100
        assert np.all(likelihoods > 0)
        assert np.all(likelihoods < 1)

    def test_filter_player_season(self, player_game_log):
        """Test filtering player season data."""
        pf = PlayerPerformanceParticleFilter(n_particles=500)

        result = pf.filter_player_season(
            data=player_game_log, target_col="points", covariate_cols=None
        )

        assert isinstance(result, PlayerPerformanceResult)
        assert len(result.states) == len(player_game_log)
        assert result.form_states is not None
        assert result.skill_trajectory is not None

        # Check DataFrame columns
        assert "skill_mean" in result.form_states.columns
        assert "form_mean" in result.form_states.columns
        assert "skill_variance" in result.form_states.columns

    def test_filter_with_covariates(self, player_game_log):
        """Test filtering with covariates."""
        # Add covariate
        player_game_log["home_game"] = np.random.binomial(1, 0.5, len(player_game_log))

        pf = PlayerPerformanceParticleFilter(n_particles=500)

        # Note: coefficients would normally be estimated separately
        coefficients = np.array([0.1])  # Home court advantage

        result = pf.filter_player_season(
            data=player_game_log,
            target_col="points",
            covariate_cols=["home_game"],
            coefficients=coefficients,
        )

        assert isinstance(result, PlayerPerformanceResult)
        assert len(result.states) == len(player_game_log)


# ==============================================================================
# Live Game Probability Filter Tests
# ==============================================================================


class TestLiveGameProbabilityFilter:
    """Tests for LiveGameProbabilityFilter."""

    def test_initialization(self):
        """Test game filter initialization."""
        pf = LiveGameProbabilityFilter(
            n_particles=2000, home_strength=5.0, away_strength=3.0
        )

        assert pf.n_particles == 2000
        assert pf.home_strength == 5.0
        assert pf.away_strength == 3.0
        assert pf.game_length == 48.0

    def test_game_transition(self):
        """Test score difference transition."""
        pf = LiveGameProbabilityFilter(home_strength=5.0, away_strength=3.0)
        pf.initialize_particles(initial_state=np.array([0.0]))

        initial_particles = pf.particles.copy()

        # Apply transition for 1 minute
        new_particles = pf._game_transition(initial_particles, time_delta=1.0)

        # Score difference should drift toward home advantage
        mean_diff = np.mean(new_particles)
        assert mean_diff > np.mean(initial_particles)

    def test_score_likelihood(self):
        """Test score difference likelihood."""
        pf = LiveGameProbabilityFilter(n_particles=100)
        pf.initialize_particles(initial_state=np.array([5.0]))

        # Compute likelihoods for observed difference = 6
        likelihoods = pf._score_likelihood(
            pf.particles, observation=np.array([6.0]), obs_noise=1.0
        )

        assert len(likelihoods) == 100
        assert np.all(likelihoods > 0)

    def test_track_game_close(self, score_updates):
        """Test tracking a close game."""
        pf = LiveGameProbabilityFilter(
            n_particles=1000, home_strength=2.0, away_strength=2.0  # Even teams
        )

        result = pf.track_game(score_updates, initial_diff=0.0)

        assert isinstance(result, GameStateResult)
        assert len(result.time_points) == 4
        assert len(result.win_probabilities) == 4

        # Win probabilities should be between 0 and 1
        assert all(0 <= p <= 1 for p in result.win_probabilities)

        # Final score: 95-92 (home wins by 3)
        assert result.final_win_prob > 0.5

    def test_track_game_blowout(self):
        """Test tracking a blowout game."""
        # Large lead
        score_updates = [
            (12.0, 35, 15),  # Home up 20 after Q1
            (24.0, 70, 35),  # Home up 35 at half
            (36.0, 100, 55),  # Home up 45 after Q3
            (48.0, 130, 75),  # Home wins by 55
        ]

        pf = LiveGameProbabilityFilter(
            n_particles=1000, home_strength=10.0, away_strength=-5.0
        )

        result = pf.track_game(score_updates, initial_diff=0.0)

        # Home should have very high win probability throughout
        assert all(p > 0.95 for p in result.win_probabilities[1:])
        assert result.final_win_prob > 0.99

    def test_upset_detection(self):
        """Test upset probability detection."""
        # Away team (underdog) wins
        score_updates = [
            (12.0, 20, 25),  # Away leads
            (24.0, 42, 50),  # Away extends lead
            (36.0, 65, 75),  # Away still ahead
            (48.0, 85, 95),  # Away wins
        ]

        pf = LiveGameProbabilityFilter(
            n_particles=1000,
            home_strength=5.0,  # Home favored
            away_strength=0.0,
        )

        result = pf.track_game(score_updates, initial_diff=0.0)

        # This is an upset (underdog away team wins)
        assert result.upset_probability > 0


# ==============================================================================
# Utility Function Tests
# ==============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_diagnose_particle_degeneracy_good(self):
        """Test diagnostics with healthy particle filter."""
        # Create mock result with good properties
        result = ParticleFilterResult(
            states=np.zeros((10, 1)),
            state_variance=np.ones((10, 1)),
            particles=np.random.normal(0, 1, (1000, 1)),
            weights=np.ones(1000) / 1000,  # Uniform
            ess_history=[900.0] * 10,  # High ESS
            resampling_history=[False] * 10,
            log_likelihood=-50.0,
        )

        diagnostics = diagnose_particle_degeneracy(result)

        assert diagnostics["avg_ess"] == 900.0
        assert diagnostics["min_ess"] == 900.0
        assert diagnostics["resampling_rate"] == 0.0
        assert diagnostics["is_degenerate"] is False

    def test_diagnose_particle_degeneracy_bad(self):
        """Test diagnostics with degenerate particle filter."""
        # Create mock result with degenerate properties
        weights = np.zeros(1000)
        weights[0] = 1.0  # All weight on one particle

        result = ParticleFilterResult(
            states=np.zeros((10, 1)),
            state_variance=np.ones((10, 1)),
            particles=np.random.normal(0, 1, (1000, 1)),
            weights=weights,
            ess_history=[50.0] * 10,  # Low ESS
            resampling_history=[True] * 10,  # Constant resampling
            log_likelihood=-100.0,
        )

        diagnostics = diagnose_particle_degeneracy(result)

        assert diagnostics["avg_ess"] == 50.0
        assert diagnostics["resampling_rate"] == 1.0
        assert diagnostics["is_degenerate"] is True

    def test_create_player_filter(self, player_game_log):
        """Test player filter factory function."""
        pf = create_player_filter(player_game_log, n_particles=500)

        assert isinstance(pf, PlayerPerformanceParticleFilter)
        assert pf.n_particles == 500

        # Parameters should be auto-tuned from data
        assert pf.skill_volatility > 0
        assert pf.form_volatility > 0
        assert 0.5 <= pf.form_persistence <= 0.95

    def test_create_player_filter_minimal_data(self):
        """Test player filter with minimal data."""
        minimal_data = pd.DataFrame({"points": [10, 12, 11, 13, 12]})

        pf = create_player_filter(minimal_data, n_particles=500)

        # Should use defaults when data is insufficient
        assert isinstance(pf, PlayerPerformanceParticleFilter)

    def test_create_game_filter(self):
        """Test game filter factory function."""
        pf = create_game_filter(
            home_team_rating=5.0, away_team_rating=3.0, n_particles=2000
        )

        assert isinstance(pf, LiveGameProbabilityFilter)
        assert pf.n_particles == 2000
        assert pf.home_strength == 5.0
        assert pf.away_strength == 3.0


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestParticleFilterIntegration:
    """Integration tests for particle filters."""

    def test_full_player_tracking_workflow(self, player_game_log):
        """Test complete player tracking workflow."""
        # 1. Create filter
        pf = create_player_filter(player_game_log, n_particles=500)

        # 2. Filter season
        result = pf.filter_player_season(data=player_game_log, target_col="points")

        # 3. Check results
        assert isinstance(result, PlayerPerformanceResult)
        assert len(result.form_states) == len(player_game_log)

        # 4. Extract insights
        final_skill = result.skill_trajectory.iloc[-1]["skill"]
        initial_skill = result.skill_trajectory.iloc[0]["skill"]

        assert final_skill > 0  # Reasonable skill level
        assert np.abs(final_skill - initial_skill) < 2  # Skill stable over season

        # 5. Check uncertainty
        skill_variance = result.form_states["skill_variance"].mean()
        assert skill_variance > 0  # Should have uncertainty

    def test_full_game_tracking_workflow(self):
        """Test complete game tracking workflow."""
        # Simulate a comeback game
        score_updates = [
            (6.0, 12, 18),  # Away leads early
            (12.0, 25, 35),  # Away extends lead
            (18.0, 40, 48),  # Still behind
            (24.0, 55, 60),  # Halftime, down 5
            (30.0, 72, 70),  # Home takes lead!
            (36.0, 88, 82),  # Home extends lead
            (42.0, 100, 92),  # Home pulling away
            (48.0, 112, 100),  # Home wins
        ]

        # 1. Create filter
        pf = create_game_filter(home_team_rating=3.0, away_team_rating=3.0)

        # 2. Track game
        result = pf.track_game(score_updates)

        # 3. Analyze win probability evolution
        assert len(result.win_probabilities) == 8

        # Should start low (home behind), then increase
        assert result.win_probabilities[0] < 0.5
        assert result.win_probabilities[-1] > 0.9

        # Find turning point
        for i in range(len(result.win_probabilities) - 1):
            if (
                result.win_probabilities[i] < 0.5
                and result.win_probabilities[i + 1] > 0.5
            ):
                turning_point = i
                break

        # Turning point should exist (home takes lead around halftime)
        assert turning_point >= 3  # After halftime


# ==============================================================================
# Edge Cases
# ==============================================================================


class TestParticleFilterEdgeCases:
    """Test edge cases and error handling."""

    def test_very_few_particles(self):
        """Test with minimum number of particles."""
        pf = ParticleFilter(n_particles=100, state_dim=1)  # Minimum is 100

        assert pf.n_particles == 100

    def test_high_dimensional_state(self):
        """Test with high-dimensional state space."""
        pf = ParticleFilter(n_particles=1000, state_dim=10)

        pf.initialize_particles(initial_state=np.ones(10), initial_variance=1.0)

        assert pf.particles.shape == (1000, 10)

    def test_all_zero_likelihoods(self):
        """Test handling when all likelihoods are zero."""
        pf = PlayerPerformanceParticleFilter(n_particles=100)
        pf.initialize_particles(initial_state=np.array([3.0, 0.0]))

        # Extreme observation that gives zero likelihood
        pf.update(observation=np.array([1000]))  # Impossibly high

        # Weights should be reset to uniform
        assert np.allclose(pf.weights, 1.0 / 100)

    def test_empty_score_updates(self):
        """Test game tracking with no score updates."""
        pf = LiveGameProbabilityFilter()

        # Should handle empty list gracefully
        result = pf.track_game([])

        assert len(result.time_points) == 0
        assert len(result.win_probabilities) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
