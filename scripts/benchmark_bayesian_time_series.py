#!/usr/bin/env python3
"""
Benchmark script for Bayesian Time Series Methods

Tests Bayesian time series implementations:
- BVARAnalyzer (fit, forecast, impulse_response, FEVD)
- BayesianStructuralTS (fit, forecast)
- HierarchicalBayesianTS (fit, forecast_player, compare_players)
- BayesianModelAveraging (compute_weights, predict, compare_models)

Note: These methods require PyMC. Tests will be skipped if not available.

Goal: Complete final benchmarking to reach 100% method coverage
"""

import sys
import time
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check PyMC availability
try:
    import pymc as pm
    import arviz as az
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False
    print("⚠️  WARNING: PyMC not available. Bayesian Time Series tests will be skipped.")
    print("   Install with: pip install pymc arviz")

from mcp_server.bayesian_time_series import (
    BVARAnalyzer,
    BayesianStructuralTS,
    HierarchicalBayesianTS,
    BayesianModelAveraging,
)


# Data Generators
def generate_multivariate_ts(n_points: int = 100, n_vars: int = 3) -> pd.DataFrame:
    """Generate multivariate time series for VAR models."""
    np.random.seed(42)

    # Generate correlated time series
    data = {}
    for i in range(n_vars):
        trend = np.linspace(20 + i*5, 25 + i*5, n_points)
        seasonal = 3 * np.sin(np.arange(n_points) * 2 * np.pi / 10)
        noise = np.random.normal(0, 2, n_points)
        data[f'var_{i}'] = trend + seasonal + noise

    return pd.DataFrame(data)


def generate_univariate_ts(n_points: int = 100) -> pd.Series:
    """Generate univariate time series for structural models."""
    np.random.seed(42)

    trend = np.linspace(20, 30, n_points)
    seasonal = 5 * np.sin(np.arange(n_points) * 2 * np.pi / 12)
    noise = np.random.normal(0, 2, n_points)

    return pd.Series(trend + seasonal + noise, name='value')


def generate_hierarchical_data(n_players: int = 5, n_games: int = 20) -> pd.DataFrame:
    """Generate hierarchical player-team data."""
    np.random.seed(42)

    teams = ['LAL', 'BOS', 'GSW']
    data = []

    for i in range(n_players):
        team = teams[i % len(teams)]
        player_id = f'player_{i}'

        # Player-specific baseline
        baseline = 15 + np.random.normal(0, 5)

        for game in range(n_games):
            points = baseline + np.random.normal(0, 3)
            data.append({
                'player_id': player_id,
                'team_id': team,
                'game': game,
                'points': max(0, points)
            })

    return pd.DataFrame(data)


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
    print(f"Testing {name}...", end=' ')

    result, exec_time, error = measure_performance(func)

    success = error is None
    status = "✓" if success else "✗"

    print(f"{status} ({exec_time:.4f}s)")
    if error:
        print(f"  Error: {error[:80]}")

    return {
        'method': name,
        'category': category,
        'execution_time': exec_time,
        'success': success,
        'error': error
    }


# Bayesian Time Series Method Tests
def test_bvar_init():
    """Test BVARAnalyzer.__init__()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_multivariate_ts(n_points=50, n_vars=3)

    analyzer = BVARAnalyzer(
        data=data,
        var_names=['var_0', 'var_1', 'var_2'],
        lags=2
    )

    assert analyzer.lags == 2
    assert len(analyzer.var_names) == 3
    return analyzer


def test_bvar_fit():
    """Test BVARAnalyzer.fit() - MCMC sampling"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_multivariate_ts(n_points=50, n_vars=2)

    analyzer = BVARAnalyzer(
        data=data,
        var_names=['var_0', 'var_1'],
        lags=1
    )

    # Use minimal samples for speed
    result = analyzer.fit(draws=50, tune=25, chains=1)

    assert result.trace is not None
    assert result.waic is not None
    assert result.summary is not None
    return result


def test_bvar_forecast():
    """Test BVARAnalyzer.forecast()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_multivariate_ts(n_points=50, n_vars=2)

    analyzer = BVARAnalyzer(
        data=data,
        var_names=['var_0', 'var_1'],
        lags=1
    )

    result = analyzer.fit(draws=50, tune=25, chains=1)
    forecast = analyzer.forecast(result, steps=5)

    assert 'var_0' in forecast
    assert 'var_1' in forecast
    assert len(forecast['var_0']) == 5
    return forecast


def test_bvar_impulse_response():
    """Test BVARAnalyzer.impulse_response()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_multivariate_ts(n_points=50, n_vars=2)

    analyzer = BVARAnalyzer(
        data=data,
        var_names=['var_0', 'var_1'],
        lags=1
    )

    result = analyzer.fit(draws=50, tune=25, chains=1)
    irf = analyzer.impulse_response(result, periods=10)

    assert irf is not None
    assert len(irf) > 0
    return irf


def test_bvar_fevd():
    """Test BVARAnalyzer.forecast_error_variance_decomposition()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_multivariate_ts(n_points=50, n_vars=2)

    analyzer = BVARAnalyzer(
        data=data,
        var_names=['var_0', 'var_1'],
        lags=1
    )

    result = analyzer.fit(draws=50, tune=25, chains=1)
    fevd = analyzer.forecast_error_variance_decomposition(result, periods=10)

    assert fevd is not None
    assert len(fevd) > 0
    return fevd


def test_bsts_init():
    """Test BayesianStructuralTS.__init__()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_univariate_ts(n_points=50)

    analyzer = BayesianStructuralTS(
        data=data,
        include_trend=True,
        seasonal_period=12
    )

    assert analyzer.include_trend == True
    assert analyzer.seasonal_period == 12
    return analyzer


def test_bsts_fit():
    """Test BayesianStructuralTS.fit()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_univariate_ts(n_points=50)

    analyzer = BayesianStructuralTS(
        data=data,
        include_trend=True,
        seasonal_period=None  # Skip seasonal for speed
    )

    result = analyzer.fit(draws=50, tune=25, chains=1)

    assert result.trace is not None
    assert result.components is not None
    assert 'level' in result.components
    return result


def test_bsts_forecast():
    """Test BayesianStructuralTS.forecast()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_univariate_ts(n_points=50)

    analyzer = BayesianStructuralTS(
        data=data,
        include_trend=True,
        seasonal_period=None
    )

    result = analyzer.fit(draws=50, tune=25, chains=1)
    forecast = analyzer.forecast(result, steps=5)

    assert 'mean' in forecast
    assert 'lower' in forecast
    assert 'upper' in forecast
    assert len(forecast['mean']) == 5
    return forecast


def test_hierarchical_init():
    """Test HierarchicalBayesianTS.__init__()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_hierarchical_data(n_players=3, n_games=20)

    analyzer = HierarchicalBayesianTS(
        data=data,
        player_col='player_id',
        team_col='team_id',
        time_col='game',
        target_col='points'
    )

    assert analyzer.player_col == 'player_id'
    assert analyzer.target_col == 'points'
    return analyzer


def test_hierarchical_fit():
    """Test HierarchicalBayesianTS.fit()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_hierarchical_data(n_players=3, n_games=20)

    analyzer = HierarchicalBayesianTS(
        data=data,
        player_col='player_id',
        team_col='team_id',
        time_col='game',
        target_col='points'
    )

    result = analyzer.fit(draws=50, tune=25, chains=1)

    assert result.trace is not None
    assert result.shrinkage is not None
    return result


def test_hierarchical_forecast_player():
    """Test HierarchicalBayesianTS.forecast_player()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_hierarchical_data(n_players=3, n_games=20)

    analyzer = HierarchicalBayesianTS(
        data=data,
        player_col='player_id',
        team_col='team_id',
        time_col='game',
        target_col='points'
    )

    result = analyzer.fit(draws=50, tune=25, chains=1)
    forecast = analyzer.forecast_player(result, player_id='player_0', steps=5)

    assert 'mean' in forecast
    assert len(forecast['mean']) == 5
    return forecast


def test_hierarchical_compare_players():
    """Test HierarchicalBayesianTS.compare_players()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    data = generate_hierarchical_data(n_players=3, n_games=20)

    analyzer = HierarchicalBayesianTS(
        data=data,
        player_col='player_id',
        team_col='team_id',
        time_col='game',
        target_col='points'
    )

    result = analyzer.fit(draws=50, tune=25, chains=1)
    comparison = analyzer.compare_players(
        result,
        player1='player_0',
        player2='player_1'
    )

    assert 'difference_mean' in comparison
    assert 'prob_player1_better' in comparison
    return comparison


def test_bma_init():
    """Test BayesianModelAveraging.__init__()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    # Create dummy models (fitted BVARResults)
    data = generate_multivariate_ts(n_points=50, n_vars=2)

    analyzer1 = BVARAnalyzer(data=data, var_names=['var_0', 'var_1'], lags=1)
    result1 = analyzer1.fit(draws=50, tune=25, chains=1)

    analyzer2 = BVARAnalyzer(data=data, var_names=['var_0', 'var_1'], lags=2)
    result2 = analyzer2.fit(draws=50, tune=25, chains=1)

    bma = BayesianModelAveraging(models=[result1, result2])

    assert len(bma.models) == 2
    return bma


def test_bma_compute_weights():
    """Test BayesianModelAveraging.compute_weights()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    # Create dummy models
    data = generate_multivariate_ts(n_points=50, n_vars=2)

    analyzer1 = BVARAnalyzer(data=data, var_names=['var_0', 'var_1'], lags=1)
    result1 = analyzer1.fit(draws=50, tune=25, chains=1)

    analyzer2 = BVARAnalyzer(data=data, var_names=['var_0', 'var_1'], lags=2)
    result2 = analyzer2.fit(draws=50, tune=25, chains=1)

    bma = BayesianModelAveraging(models=[result1, result2])
    weights_result = bma.compute_weights()

    assert len(weights_result.weights) == 2
    assert abs(sum(weights_result.weights) - 1.0) < 0.01  # Weights sum to 1
    return weights_result


def test_bma_compare_models():
    """Test BayesianModelAveraging.compare_models()"""
    if not PYMC_AVAILABLE:
        raise ImportError("PyMC not available")

    # Create dummy models
    data = generate_multivariate_ts(n_points=50, n_vars=2)

    analyzer1 = BVARAnalyzer(data=data, var_names=['var_0', 'var_1'], lags=1)
    result1 = analyzer1.fit(draws=50, tune=25, chains=1)

    analyzer2 = BVARAnalyzer(data=data, var_names=['var_0', 'var_1'], lags=2)
    result2 = analyzer2.fit(draws=50, tune=25, chains=1)

    bma = BayesianModelAveraging(models=[result1, result2])
    comparison = bma.compare_models()

    assert len(comparison) == 2
    assert 'waic' in comparison.columns
    return comparison


# Main Benchmark Execution
def main():
    print("=" * 70)
    print("BAYESIAN TIME SERIES METHODS BENCHMARK")
    print("=" * 70)
    print(f"Goal: Test Bayesian time series methods")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not PYMC_AVAILABLE:
        print("\n⚠️  PyMC not available - skipping all tests")
        print("   Install with: pip install pymc arviz")
        return 2

    print()

    results = []

    # Test all Bayesian time series methods
    test_cases = [
        # BVARAnalyzer (5 methods)
        ("BVARAnalyzer.__init__", test_bvar_init, "BVAR"),
        ("BVARAnalyzer.fit", test_bvar_fit, "BVAR"),
        ("BVARAnalyzer.forecast", test_bvar_forecast, "BVAR"),
        ("BVARAnalyzer.impulse_response", test_bvar_impulse_response, "BVAR"),
        ("BVARAnalyzer.forecast_error_variance_decomposition", test_bvar_fevd, "BVAR"),

        # BayesianStructuralTS (3 methods)
        ("BayesianStructuralTS.__init__", test_bsts_init, "Structural TS"),
        ("BayesianStructuralTS.fit", test_bsts_fit, "Structural TS"),
        ("BayesianStructuralTS.forecast", test_bsts_forecast, "Structural TS"),

        # HierarchicalBayesianTS (4 methods)
        ("HierarchicalBayesianTS.__init__", test_hierarchical_init, "Hierarchical TS"),
        ("HierarchicalBayesianTS.fit", test_hierarchical_fit, "Hierarchical TS"),
        ("HierarchicalBayesianTS.forecast_player", test_hierarchical_forecast_player, "Hierarchical TS"),
        ("HierarchicalBayesianTS.compare_players", test_hierarchical_compare_players, "Hierarchical TS"),

        # BayesianModelAveraging (3 methods)
        ("BayesianModelAveraging.__init__", test_bma_init, "Model Averaging"),
        ("BayesianModelAveraging.compute_weights", test_bma_compute_weights, "Model Averaging"),
        ("BayesianModelAveraging.compare_models", test_bma_compare_models, "Model Averaging"),
    ]

    for name, test_func, category in test_cases:
        result = benchmark_method(name, test_func, category)
        results.append(result)

    # Calculate summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_tests = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total_tests - successful

    print(f"Total Methods Tested: {total_tests}")
    print(f"Successful: {successful} ({successful/total_tests*100:.1f}%)")
    print(f"Failed: {failed}")
    print()

    # Break down by category
    categories = {}
    for result in results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'success': 0}
        categories[cat]['total'] += 1
        if result['success']:
            categories[cat]['success'] += 1

    print("By Category:")
    for cat, stats in sorted(categories.items()):
        success_rate = stats['success'] / stats['total'] * 100
        print(f"  {cat}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

    # Calculate average execution time
    successful_times = [r['execution_time'] for r in results if r['success']]
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        print(f"\nAverage Execution Time: {avg_time:.4f}s")
        print(f"Fastest: {min(successful_times):.4f}s")
        print(f"Slowest: {max(successful_times):.4f}s")

    # Save results
    output_dir = Path(__file__).parent.parent / 'benchmark_results'
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save to JSON
    json_path = output_dir / f'bayesian_time_series_{timestamp}.json'
    with open(json_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'successful': successful,
            'failed': failed,
            'pymc_available': PYMC_AVAILABLE,
            'results': results
        }, f, indent=2)

    # Save to CSV
    csv_path = output_dir / f'bayesian_time_series_{timestamp}.csv'
    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)

    print(f"\n✓ Results saved to:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")

    print("\n" + "=" * 70)
    print(f"BAYESIAN TIME SERIES: {successful}/{total_tests} methods tested!")
    if successful == total_tests:
        print("🎉 ALL BAYESIAN TIME SERIES METHODS TESTED SUCCESSFULLY!")
    print("=" * 70)

    return 0 if successful == total_tests else 1


if __name__ == '__main__':
    sys.exit(main())
