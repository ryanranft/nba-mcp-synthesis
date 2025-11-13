#!/usr/bin/env python3
"""
Benchmark script for Particle Filter Methods (8 methods)

Tests all particle filter implementations:
- ParticleFilter base class (7 core methods)
- PlayerPerformanceParticleFilter (filter_player_season)
- LiveGameProbabilityFilter (track_game)
- Utility functions (diagnose, compare_resampling)

Goal: Test 8+ methods to advance toward 100% coverage (75 → 83 methods)
"""

import sys
import time
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.particle_filters import (
    ParticleFilter,
    PlayerPerformanceParticleFilter,
    LiveGameProbabilityFilter,
    diagnose_particle_degeneracy,
    compare_resampling_methods,
    compute_ess,
    create_player_filter,
    create_game_filter,
)


# Data Generators
def generate_player_data(n_games: int = 50) -> pd.DataFrame:
    """Generate synthetic player game log data."""
    np.random.seed(42)

    dates = pd.date_range(start="2023-01-01", periods=n_games, freq="3D")

    # Simulate player scoring with trend and form fluctuations
    base_skill = 2.5  # log(exp(2.5)) ≈ 12.2 points per game
    skill_trend = np.linspace(0, 0.2, n_games)  # Slight improvement

    # AR(1) form component
    form = np.zeros(n_games)
    form[0] = np.random.normal(0, 0.2)
    for i in range(1, n_games):
        form[i] = 0.7 * form[i - 1] + np.random.normal(0, 0.2)

    # Generate points from Poisson
    lambda_values = np.exp(base_skill + skill_trend + form)
    points = np.random.poisson(lambda_values)

    # Add covariates
    minutes = np.random.normal(30, 5, n_games)
    minutes = np.clip(minutes, 15, 40)

    opponent_strength = np.random.normal(0, 1, n_games)

    return pd.DataFrame(
        {
            "date": dates,
            "points": points,
            "minutes": minutes,
            "opponent_strength": opponent_strength,
        }
    ).set_index("date")


def generate_game_updates(n_updates: int = 20) -> List[Tuple[float, int, int]]:
    """Generate synthetic game score updates."""
    np.random.seed(42)

    updates = []
    home_score, away_score = 0, 0

    for i in range(n_updates):
        time = 48 * (i + 1) / n_updates  # Evenly spaced updates

        # Random scoring
        home_score += np.random.poisson(2.5)
        away_score += np.random.poisson(2.3)

        updates.append((time, home_score, away_score))

    return updates


def simple_transition(particles: np.ndarray, **kwargs) -> np.ndarray:
    """Simple random walk transition for testing."""
    noise = np.random.normal(0, 0.5, size=particles.shape)
    return particles + noise


def simple_observation(
    particles: np.ndarray, observation: np.ndarray, **kwargs
) -> np.ndarray:
    """Simple Gaussian observation likelihood for testing."""
    from scipy import stats

    obs_val = observation if np.isscalar(observation) else observation[0]
    if particles.ndim == 1:
        likelihoods = stats.norm.pdf(obs_val, loc=particles, scale=1.0)
    else:
        likelihoods = stats.norm.pdf(obs_val, loc=particles[:, 0], scale=1.0)
    return np.maximum(likelihoods, 1e-300)


# Benchmark Infrastructure
def measure_performance(func):
    """Measure execution time and capture result."""
    start_time = time.time()
    try:
        result = func()
        execution_time = time.time() - start_time
        return result, execution_time, None
    except Exception as e:
        execution_time = time.time() - start_time
        return None, execution_time, str(e)


def benchmark_method(name: str, func, category: str) -> dict:
    """Benchmark a single method."""
    print(f"Testing {name}...", end=" ")

    result, exec_time, error = measure_performance(func)

    success = error is None
    status = "✓" if success else "✗"

    print(f"{status} ({exec_time:.4f}s)")
    if error:
        print(f"  Error: {error}")

    return {
        "method": name,
        "category": category,
        "execution_time": exec_time,
        "success": success,
        "error": error,
    }


# Particle Filter Method Tests
def test_particle_filter_init():
    """Test ParticleFilter.__init__()"""
    pf = ParticleFilter(
        n_particles=500,
        state_dim=2,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
        resampling_method="systematic",
        resampling_threshold=0.5,
    )

    assert pf.n_particles == 500
    assert pf.state_dim == 2
    assert pf.resampling_threshold == 0.5
    return pf


def test_initialize_particles():
    """Test ParticleFilter.initialize_particles()"""
    pf = ParticleFilter(
        n_particles=500,
        state_dim=2,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
    )

    initial_state = np.array([1.0, 0.5])
    pf.initialize_particles(initial_state, initial_variance=0.5)

    assert pf.particles.shape == (500, 2)
    assert pf.weights.shape == (500,)
    assert np.abs(np.sum(pf.weights) - 1.0) < 1e-10
    return pf.particles


def test_predict():
    """Test ParticleFilter.predict()"""
    pf = ParticleFilter(
        n_particles=500,
        state_dim=1,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
    )

    pf.initialize_particles(np.array([5.0]), initial_variance=1.0)
    particles_before = pf.particles.copy()

    pf.predict()

    # Particles should have changed
    assert not np.allclose(pf.particles, particles_before)
    return pf.particles


def test_update():
    """Test ParticleFilter.update()"""
    pf = ParticleFilter(
        n_particles=500,
        state_dim=1,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
    )

    pf.initialize_particles(np.array([5.0]), initial_variance=1.0)
    weights_before = pf.weights.copy()

    observation = np.array([6.0])
    pf.update(observation)

    # Weights should have changed
    assert not np.allclose(pf.weights, weights_before)
    # Weights should still be normalized
    assert np.abs(np.sum(pf.weights) - 1.0) < 1e-10
    return pf.weights


def test_resample_if_needed():
    """Test ParticleFilter.resample_if_needed()"""
    pf = ParticleFilter(
        n_particles=500,
        state_dim=1,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
        resampling_threshold=0.8,  # High threshold to trigger resampling
    )

    pf.initialize_particles(np.array([5.0]), initial_variance=1.0)

    # Create degenerate weights to trigger resampling
    pf.weights = np.zeros(500)
    pf.weights[0] = 1.0

    resampled = pf.resample_if_needed()

    assert resampled == True, "Should have resampled with degenerate weights"
    # After resampling, weights should be uniform
    assert np.allclose(pf.weights, 1.0 / 500)
    return resampled


def test_get_state_estimate():
    """Test ParticleFilter.get_state_estimate()"""
    pf = ParticleFilter(
        n_particles=500,
        state_dim=2,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
    )

    initial_state = np.array([3.0, 1.5])
    pf.initialize_particles(initial_state, initial_variance=0.5)

    mean, variance = pf.get_state_estimate()

    assert mean.shape == (2,)
    assert variance.shape == (2,)
    # Mean should be close to initial state
    assert np.allclose(mean, initial_state, atol=0.5)
    return mean, variance


def test_particle_filter_filter():
    """Test ParticleFilter.filter() - complete filtering loop"""
    # Generate observations
    np.random.seed(42)
    true_state = np.cumsum(np.random.normal(0, 0.5, 30))
    observations = true_state + np.random.normal(0, 1.0, 30)

    pf = ParticleFilter(
        n_particles=1000,
        state_dim=1,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
    )

    result = pf.filter(
        observations=observations[:, None],
        initial_state=np.array([0.0]),
        initial_variance=1.0,
    )

    assert result.states.shape == (30, 1)
    assert result.state_variance.shape == (30, 1)
    assert len(result.ess_history) == 30
    assert len(result.resampling_history) == 30
    assert result.log_likelihood < 0  # Should be negative log-likelihood
    return result


def test_player_performance_filter_init():
    """Test PlayerPerformanceParticleFilter.__init__()"""
    pf = PlayerPerformanceParticleFilter(
        n_particles=500,
        skill_drift=0.01,
        skill_volatility=0.05,
        form_persistence=0.7,
        form_volatility=0.2,
    )

    assert pf.n_particles == 500
    assert pf.state_dim == 2  # [skill, form]
    assert pf.skill_drift == 0.01
    assert pf.form_persistence == 0.7
    return pf


def test_filter_player_season():
    """Test PlayerPerformanceParticleFilter.filter_player_season()"""
    player_data = generate_player_data(n_games=40)

    pf = PlayerPerformanceParticleFilter(
        n_particles=500,
        skill_volatility=0.05,
        form_volatility=0.2,
        form_persistence=0.7,
    )

    result = pf.filter_player_season(data=player_data, target_col="points")

    assert result.states.shape == (40, 2)  # 40 games, 2 state dims
    assert "skill_mean" in result.form_states.columns
    assert "form_mean" in result.form_states.columns
    assert "skill" in result.skill_trajectory.columns
    assert len(result.ess_history) == 40
    return result


def test_live_game_filter_init():
    """Test LiveGameProbabilityFilter.__init__()"""
    gf = LiveGameProbabilityFilter(
        n_particles=1000,
        home_strength=5.0,
        away_strength=3.0,
        game_length=48.0,
        noise_per_minute=1.5,
    )

    assert gf.n_particles == 1000
    assert gf.state_dim == 1  # score difference
    assert gf.home_strength == 5.0
    assert gf.away_strength == 3.0
    return gf


def test_track_game():
    """Test LiveGameProbabilityFilter.track_game()"""
    score_updates = generate_game_updates(n_updates=15)

    gf = LiveGameProbabilityFilter(
        n_particles=1000, home_strength=5.0, away_strength=3.0
    )

    result = gf.track_game(score_updates=score_updates, initial_diff=0.0)

    assert len(result.time_points) == 15
    assert len(result.win_probabilities) == 15
    assert 0.0 <= result.final_win_prob <= 1.0
    assert 0.0 <= result.upset_probability <= 1.0
    return result


def test_diagnose_particle_degeneracy():
    """Test diagnose_particle_degeneracy()"""
    # Create a simple filter result
    pf = ParticleFilter(
        n_particles=500,
        state_dim=1,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
    )

    observations = np.random.normal(0, 1, 20)
    result = pf.filter(
        observations=observations[:, None], initial_state=np.array([0.0])
    )

    diagnostics = diagnose_particle_degeneracy(result)

    assert "avg_ess" in diagnostics
    assert "min_ess" in diagnostics
    assert "resampling_rate" in diagnostics
    assert "weight_entropy" in diagnostics
    assert "is_degenerate" in diagnostics
    assert isinstance(diagnostics["is_degenerate"], (bool, np.bool_))
    return diagnostics


def test_compare_resampling_methods():
    """Test compare_resampling_methods()"""
    # Generate test data
    np.random.seed(42)
    observations = np.random.normal(0, 1, 20)
    initial_state = np.array([0.0])

    comparison = compare_resampling_methods(
        observations=observations[:, None],
        initial_state=initial_state,
        pf_class=ParticleFilter,
        n_particles=500,
        state_dim=1,
        transition_fn=simple_transition,
        observation_fn=simple_observation,
    )

    assert len(comparison) == 3  # 3 resampling methods
    assert "method" in comparison.columns
    assert "log_likelihood" in comparison.columns
    assert "avg_ess" in comparison.columns
    assert set(comparison["method"]) == {"systematic", "multinomial", "stratified"}
    return comparison


def test_create_player_filter():
    """Test create_player_filter() utility"""
    player_data = generate_player_data(n_games=30)

    pf = create_player_filter(player_data=player_data, n_particles=500)

    assert isinstance(pf, PlayerPerformanceParticleFilter)
    assert pf.n_particles == 500
    assert hasattr(pf, "skill_volatility")
    assert hasattr(pf, "form_volatility")
    return pf


def test_create_game_filter():
    """Test create_game_filter() utility"""
    gf = create_game_filter(
        home_team_rating=5.0, away_team_rating=2.0, n_particles=1000
    )

    assert isinstance(gf, LiveGameProbabilityFilter)
    assert gf.n_particles == 1000
    assert gf.home_strength == 5.0
    assert gf.away_strength == 2.0
    return gf


# Main Benchmark Execution
def main():
    print("=" * 70)
    print("PARTICLE FILTER METHODS BENCHMARK")
    print("=" * 70)
    print(f"Goal: Test 14 particle filter methods")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    results = []

    # Test all particle filter methods
    test_cases = [
        # Base ParticleFilter (7 methods)
        ("ParticleFilter.__init__", test_particle_filter_init, "ParticleFilter Base"),
        (
            "ParticleFilter.initialize_particles",
            test_initialize_particles,
            "ParticleFilter Base",
        ),
        ("ParticleFilter.predict", test_predict, "ParticleFilter Base"),
        ("ParticleFilter.update", test_update, "ParticleFilter Base"),
        (
            "ParticleFilter.resample_if_needed",
            test_resample_if_needed,
            "ParticleFilter Base",
        ),
        (
            "ParticleFilter.get_state_estimate",
            test_get_state_estimate,
            "ParticleFilter Base",
        ),
        ("ParticleFilter.filter", test_particle_filter_filter, "ParticleFilter Base"),
        # PlayerPerformanceParticleFilter (2 methods)
        (
            "PlayerPerformanceParticleFilter.__init__",
            test_player_performance_filter_init,
            "Player Performance",
        ),
        (
            "PlayerPerformanceParticleFilter.filter_player_season",
            test_filter_player_season,
            "Player Performance",
        ),
        # LiveGameProbabilityFilter (2 methods)
        ("LiveGameProbabilityFilter.__init__", test_live_game_filter_init, "Live Game"),
        ("LiveGameProbabilityFilter.track_game", test_track_game, "Live Game"),
        # Utility functions (4 methods)
        (
            "diagnose_particle_degeneracy",
            test_diagnose_particle_degeneracy,
            "Utilities",
        ),
        ("compare_resampling_methods", test_compare_resampling_methods, "Utilities"),
        ("create_player_filter", test_create_player_filter, "Utilities"),
        ("create_game_filter", test_create_game_filter, "Utilities"),
    ]

    for name, test_func, category in test_cases:
        result = benchmark_method(name, test_func, category)
        results.append(result)

    # Calculate summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_tests = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total_tests - successful

    print(f"Total Methods Tested: {total_tests}")
    print(f"Successful: {successful} ({successful/total_tests*100:.1f}%)")
    print(f"Failed: {failed}")
    print()

    # Break down by category
    categories = {}
    for result in results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0}
        categories[cat]["total"] += 1
        if result["success"]:
            categories[cat]["success"] += 1

    print("By Category:")
    for cat, stats in sorted(categories.items()):
        success_rate = stats["success"] / stats["total"] * 100
        print(f"  {cat}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

    # Calculate average execution time
    successful_times = [r["execution_time"] for r in results if r["success"]]
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        print(f"\nAverage Execution Time: {avg_time:.4f}s")
        print(f"Fastest: {min(successful_times):.4f}s")
        print(f"Slowest: {max(successful_times):.4f}s")

    # Save results
    output_dir = Path(__file__).parent.parent / "benchmark_results"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save to JSON
    json_path = output_dir / f"particle_filters_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "successful": successful,
                "failed": failed,
                "results": results,
            },
            f,
            indent=2,
        )

    # Save to CSV
    csv_path = output_dir / f"particle_filters_{timestamp}.csv"
    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)

    print(f"\n✓ Results saved to:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")

    print("\n" + "=" * 70)
    print(
        f"COVERAGE UPDATE: {successful}/{total_tests} particle filter methods tested!"
    )
    print(f"Expected total coverage: 75 + {successful} = {75 + successful}/99")
    if successful == total_tests:
        print("🎉 ALL PARTICLE FILTER METHODS TESTED SUCCESSFULLY!")
    print("=" * 70)

    return 0 if successful == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())
