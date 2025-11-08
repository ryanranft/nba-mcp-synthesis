"""
Performance Benchmarking for Bayesian Time Series Methods.

Measures execution time, memory usage, and scalability for:
- BVAR
- BSTS
- Hierarchical Bayesian TS
- Particle Filters

Usage:
    python scripts/benchmark_bayesian_methods.py

Output:
    benchmark_results.json - Detailed results
    benchmark_summary.csv - Summary table
    benchmark_plots.png - Visualization
"""

import time
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import tracemalloc
import warnings

warnings.filterwarnings("ignore")

# Add parent directory to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.bayesian_time_series import (
    BVARAnalyzer,
    BayesianStructuralTS,
    HierarchicalBayesianTS,
    check_pymc_available,
)
from mcp_server.particle_filters import (
    PlayerPerformanceParticleFilter,
    LiveGameProbabilityFilter,
    create_player_filter,
    create_game_filter,
)


# ==============================================================================
# Utility Functions
# ==============================================================================


def measure_performance(func, *args, **kwargs):
    """
    Measure execution time and memory usage of a function.

    Returns:
        result, execution_time (seconds), peak_memory (MB)
    """
    # Start memory tracking
    tracemalloc.start()

    # Run function
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed_time = time.time() - start_time

    # Get peak memory
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = peak / 1024 / 1024

    return result, elapsed_time, peak_memory_mb


def generate_var_data(T, n_vars, seed=42):
    """Generate synthetic VAR data."""
    np.random.seed(seed)

    # Random VAR(1) coefficients
    A = np.random.uniform(0.3, 0.7, (n_vars, n_vars))
    A /= np.max(np.abs(np.linalg.eigvals(A))) * 1.2  # Ensure stability

    intercept = np.random.uniform(10, 30, n_vars)
    Sigma = np.eye(n_vars) * np.random.uniform(1, 4, n_vars)

    # Simulate
    data = np.zeros((T, n_vars))
    data[0] = intercept

    for t in range(1, T):
        mu = intercept + A @ data[t - 1]
        data[t] = mu + np.random.multivariate_normal(np.zeros(n_vars), Sigma)

    columns = [f"var{i+1}" for i in range(n_vars)]
    return pd.DataFrame(data, columns=columns)


def generate_career_data(T, seed=42):
    """Generate career trajectory data."""
    np.random.seed(seed)

    # Career arc
    t_range = np.linspace(0, 1, T)
    trend = 5 * (4 * t_range * (1 - t_range))  # Inverted U
    baseline = 20
    values = baseline + trend + np.random.normal(0, 1.5, T)

    dates = pd.date_range("2015", periods=T, freq="Y")
    return pd.Series(values, index=dates)


def generate_panel_data(n_teams, n_players_per_team, n_time, seed=42):
    """Generate hierarchical panel data."""
    np.random.seed(seed)

    league_mean = 20
    data_list = []

    for team_idx in range(n_teams):
        team_mean = league_mean + np.random.normal(0, 3)

        for player_idx in range(n_players_per_team):
            player_id = f"P{team_idx}_{player_idx}"
            team_id = f"Team{team_idx}"
            player_skill = np.random.normal(0, 2)

            for t in range(n_time):
                value = team_mean + player_skill + np.random.normal(0, 2.5)
                data_list.append(
                    {
                        "player": player_id,
                        "team": team_id,
                        "time": t,
                        "points": max(value, 5),
                    }
                )

    return pd.DataFrame(data_list)


def generate_player_log(T, seed=42):
    """Generate player game log."""
    np.random.seed(seed)

    skill = 20.0 + np.cumsum(np.random.normal(0, 0.05, T))
    form = np.zeros(T)
    form[0] = 0
    for t in range(1, T):
        form[t] = 0.7 * form[t - 1] + np.random.normal(0, 1.0)

    lambda_t = np.exp(np.log(skill) + form * 0.05)
    points = np.random.poisson(lambda_t)

    dates = pd.date_range("2024-01-01", periods=T, freq="2D")
    return pd.DataFrame({"points": points, "minutes": 30}, index=dates)


# ==============================================================================
# Benchmarks
# ==============================================================================


def benchmark_bvar():
    """Benchmark BVAR with different configurations."""
    print("\n" + "=" * 70)
    print("BENCHMARKING: Bayesian VAR (BVAR)")
    print("=" * 70)

    results = []
    configs = [
        {
            "T": 50,
            "n_vars": 2,
            "lags": 1,
            "draws": 500,
            "name": "Small (2 vars, 1 lag)",
        },
        {
            "T": 100,
            "n_vars": 3,
            "lags": 2,
            "draws": 500,
            "name": "Medium (3 vars, 2 lags)",
        },
        {
            "T": 150,
            "n_vars": 4,
            "lags": 2,
            "draws": 500,
            "name": "Large (4 vars, 2 lags)",
        },
        {
            "T": 100,
            "n_vars": 3,
            "lags": 2,
            "draws": 1000,
            "name": "Medium (1000 draws)",
        },
    ]

    for config in configs:
        print(f"\nConfig: {config['name']}")

        # Generate data
        data = generate_var_data(config["T"], config["n_vars"])
        var_names = data.columns.tolist()

        # Initialize
        analyzer = BVARAnalyzer(data=data, var_names=var_names, lags=config["lags"])

        # Benchmark fitting
        def fit_func():
            return analyzer.fit(
                draws=config["draws"], tune=config["draws"], chains=2, lambda1=0.2
            )

        result, exec_time, memory = measure_performance(fit_func)

        # Extract metrics
        convergence = result.convergence_ok
        rhat_max = result.diagnostics["rhat_max"]
        n_params = len(result.summary) if result.summary is not None else 0

        results.append(
            {
                "method": "BVAR",
                "config": config["name"],
                "T": config["T"],
                "n_vars": config["n_vars"],
                "lags": config["lags"],
                "draws": config["draws"],
                "execution_time": exec_time,
                "memory_mb": memory,
                "convergence": convergence,
                "rhat_max": rhat_max,
                "n_params": n_params,
            }
        )

        print(
            f"  Time: {exec_time:.1f}s | Memory: {memory:.1f} MB | Converged: {convergence}"
        )

    return results


def benchmark_bsts():
    """Benchmark BSTS."""
    print("\n" + "=" * 70)
    print("BENCHMARKING: Bayesian Structural Time Series (BSTS)")
    print("=" * 70)

    results = []
    configs = [
        {"T": 20, "draws": 500, "name": "Short series (20)"},
        {"T": 50, "draws": 500, "name": "Medium series (50)"},
        {"T": 100, "draws": 500, "name": "Long series (100)"},
    ]

    for config in configs:
        print(f"\nConfig: {config['name']}")

        # Generate data
        data = generate_career_data(config["T"])

        # Initialize
        analyzer = BayesianStructuralTS(
            data=data, include_trend=True, seasonal_period=None
        )

        # Benchmark
        def fit_func():
            return analyzer.fit(draws=config["draws"], tune=config["draws"], chains=2)

        result, exec_time, memory = measure_performance(fit_func)

        convergence = result.convergence_ok
        rhat_max = result.diagnostics["rhat_max"]

        results.append(
            {
                "method": "BSTS",
                "config": config["name"],
                "T": config["T"],
                "draws": config["draws"],
                "execution_time": exec_time,
                "memory_mb": memory,
                "convergence": convergence,
                "rhat_max": rhat_max,
            }
        )

        print(
            f"  Time: {exec_time:.1f}s | Memory: {memory:.1f} MB | Converged: {convergence}"
        )

    return results


def benchmark_hierarchical():
    """Benchmark Hierarchical Bayesian TS."""
    print("\n" + "=" * 70)
    print("BENCHMARKING: Hierarchical Bayesian Time Series")
    print("=" * 70)

    results = []
    configs = [
        {
            "n_teams": 3,
            "n_players": 3,
            "n_time": 20,
            "draws": 500,
            "name": "Small (3T, 9P)",
        },
        {
            "n_teams": 5,
            "n_players": 3,
            "n_time": 20,
            "draws": 500,
            "name": "Medium (5T, 15P)",
        },
        {
            "n_teams": 5,
            "n_players": 5,
            "n_time": 20,
            "draws": 500,
            "name": "Large (5T, 25P)",
        },
    ]

    for config in configs:
        print(f"\nConfig: {config['name']}")

        # Generate data
        data = generate_panel_data(
            config["n_teams"], config["n_players"], config["n_time"]
        )

        # Initialize
        analyzer = HierarchicalBayesianTS(
            data=data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        # Benchmark
        def fit_func():
            return analyzer.fit(
                draws=config["draws"], tune=config["draws"], chains=2, ar_order=0
            )

        result, exec_time, memory = measure_performance(fit_func)

        convergence = result.convergence_ok
        rhat_max = result.diagnostics["rhat_max"]
        n_total_players = config["n_teams"] * config["n_players"]

        results.append(
            {
                "method": "Hierarchical TS",
                "config": config["name"],
                "n_teams": config["n_teams"],
                "n_players": n_total_players,
                "n_time": config["n_time"],
                "draws": config["draws"],
                "execution_time": exec_time,
                "memory_mb": memory,
                "convergence": convergence,
                "rhat_max": rhat_max,
            }
        )

        print(
            f"  Time: {exec_time:.1f}s | Memory: {memory:.1f} MB | Converged: {convergence}"
        )

    return results


def benchmark_particle_filters():
    """Benchmark Particle Filters."""
    print("\n" + "=" * 70)
    print("BENCHMARKING: Particle Filters")
    print("=" * 70)

    results = []

    # Player performance filter
    configs_player = [
        {"n_particles": 500, "T": 40, "name": "Player (500 particles)"},
        {"n_particles": 1000, "T": 40, "name": "Player (1000 particles)"},
        {"n_particles": 2000, "T": 40, "name": "Player (2000 particles)"},
    ]

    for config in configs_player:
        print(f"\nConfig: {config['name']}")

        # Generate data
        data = generate_player_log(config["T"])

        # Initialize
        pf = create_player_filter(data, n_particles=config["n_particles"])

        # Benchmark
        def filter_func():
            return pf.filter_player_season(data=data, target_col="points")

        result, exec_time, memory = measure_performance(filter_func)

        avg_ess = np.mean(result.ess_history)
        resampling_rate = np.mean(result.resampling_history)

        results.append(
            {
                "method": "Particle Filter",
                "variant": "Player Performance",
                "config": config["name"],
                "n_particles": config["n_particles"],
                "T": config["T"],
                "execution_time": exec_time,
                "memory_mb": memory,
                "avg_ess": avg_ess,
                "resampling_rate": resampling_rate,
            }
        )

        print(
            f"  Time: {exec_time:.2f}s | Memory: {memory:.1f} MB | Avg ESS: {avg_ess:.0f}"
        )

    # Live game filter
    print(f"\nConfig: Live Game (2000 particles)")

    score_updates = [
        (12.0, 25, 22),
        (24.0, 48, 45),
        (36.0, 70, 68),
        (48.0, 95, 92),
    ]

    pf_game = create_game_filter(
        home_team_rating=3.0, away_team_rating=2.0, n_particles=2000
    )

    def game_func():
        return pf_game.track_game(score_updates=score_updates)

    result, exec_time, memory = measure_performance(game_func)

    results.append(
        {
            "method": "Particle Filter",
            "variant": "Live Game",
            "config": "Live Game (2000 particles)",
            "n_particles": 2000,
            "T": len(score_updates),
            "execution_time": exec_time,
            "memory_mb": memory,
            "final_win_prob": result.final_win_prob,
        }
    )

    print(f"  Time: {exec_time:.2f}s | Memory: {memory:.1f} MB")

    return results


# ==============================================================================
# Main
# ==============================================================================


def main():
    """Run all benchmarks."""
    print("=" * 70)
    print("BAYESIAN TIME SERIES METHODS - PERFORMANCE BENCHMARKS")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check PyMC
    check_pymc_available()
    print("✓ PyMC available\n")

    all_results = []

    # Run benchmarks
    try:
        all_results.extend(benchmark_bvar())
    except Exception as e:
        print(f"BVAR benchmark failed: {e}")

    try:
        all_results.extend(benchmark_bsts())
    except Exception as e:
        print(f"BSTS benchmark failed: {e}")

    try:
        all_results.extend(benchmark_hierarchical())
    except Exception as e:
        print(f"Hierarchical benchmark failed: {e}")

    try:
        all_results.extend(benchmark_particle_filters())
    except Exception as e:
        print(f"Particle filter benchmark failed: {e}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON (detailed)
    json_path = f"benchmark_results_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n✓ Detailed results saved to: {json_path}")

    # CSV (summary)
    df_results = pd.DataFrame(all_results)
    csv_path = f"benchmark_summary_{timestamp}.csv"
    df_results.to_csv(csv_path, index=False)
    print(f"✓ Summary table saved to: {csv_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print("\nExecution Times:")
    print(df_results[["method", "config", "execution_time"]].to_string(index=False))

    print("\nMemory Usage:")
    print(df_results[["method", "config", "memory_mb"]].to_string(index=False))

    print(f"\n{'='*70}")
    print(f"Benchmarking complete at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total configurations tested: {len(all_results)}")
    print(f"{'='*70}")

    return all_results


if __name__ == "__main__":
    results = main()
