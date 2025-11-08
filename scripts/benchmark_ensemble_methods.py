#!/usr/bin/env python3
"""
Benchmark script for Ensemble Methods (8 methods)

Tests all 4 ensemble classes:
- SimpleEnsemble (predict, evaluate)
- WeightedEnsemble (predict, fit_weights)
- StackingEnsemble (fit, predict)
- DynamicEnsemble (predict, update_performance)

Goal: Test 8 methods to reach 75% coverage (67 → 75 methods)
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

from mcp_server.ensemble import (
    SimpleEnsemble,
    WeightedEnsemble,
    StackingEnsemble,
    DynamicEnsemble,
)

# Data Generators
def generate_time_series_data(n_points: int = 150) -> pd.DataFrame:
    """Generate synthetic time series data for ensemble testing."""
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', periods=n_points, freq='D')

    # Generate with trend and seasonality
    trend = np.linspace(20, 30, n_points)
    seasonal = 5 * np.sin(np.arange(n_points) * 2 * np.pi / 30)
    noise = np.random.normal(0, 2, n_points)

    values = trend + seasonal + noise

    return pd.DataFrame({
        'date': dates,
        'value': values
    })


def generate_multivariate_data(n_points: int = 150) -> pd.DataFrame:
    """Generate multivariate time series data."""
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', periods=n_points, freq='D')

    # Generate 3 correlated series
    base = np.linspace(20, 30, n_points)

    return pd.DataFrame({
        'date': dates,
        'series1': base + np.random.normal(0, 2, n_points),
        'series2': base * 1.2 + np.random.normal(0, 3, n_points),
        'series3': base * 0.8 + np.random.normal(0, 1.5, n_points)
    })


def generate_regression_data(n_samples: int = 100, n_features: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic regression data for stacking ensemble."""
    np.random.seed(42)

    X = np.random.randn(n_samples, n_features)
    # Create target with linear relationship + noise
    true_coef = np.random.randn(n_features)
    y = X @ true_coef + np.random.randn(n_samples) * 0.5

    return X, y


# Model Factories
def create_fitted_arima_models(data: pd.Series, n_models: int = 3) -> List:
    """Create multiple fitted ARIMA models with different orders."""
    from statsmodels.tsa.arima.model import ARIMA

    models = []
    orders = [(1, 0, 0), (2, 1, 0), (1, 1, 1)][:n_models]

    for order in orders:
        try:
            model = ARIMA(data, order=order)
            fitted = model.fit()
            models.append(fitted)
        except Exception as e:
            print(f"Warning: Could not fit ARIMA{order}: {e}")

    return models


def create_sklearn_models() -> List:
    """Create sklearn regression models for stacking ensemble."""
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor

    return [
        LinearRegression(),
        Ridge(alpha=1.0),
        RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
    ]


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
        print(f"  Error: {error}")

    return {
        'method': name,
        'category': category,
        'execution_time': exec_time,
        'success': success,
        'error': error
    }


# Ensemble Method Tests
def test_simple_ensemble_predict():
    """Test SimpleEnsemble.predict()"""
    data = generate_time_series_data(150)
    train_data = data['value'][:100]

    models = create_fitted_arima_models(train_data, n_models=3)
    if len(models) < 2:
        raise ValueError("Need at least 2 models for ensemble")

    ensemble = SimpleEnsemble(models=models)
    predictions = ensemble.predict(n_steps=10)

    assert len(predictions) == 10, f"Expected 10 predictions, got {len(predictions)}"
    return predictions


def test_simple_ensemble_evaluate():
    """Test SimpleEnsemble.evaluate()"""
    data = generate_time_series_data(150)
    train_data = data['value'][:100]
    test_data = data['value'][100:110]

    models = create_fitted_arima_models(train_data, n_models=3)
    if len(models) < 2:
        raise ValueError("Need at least 2 models for ensemble")

    ensemble = SimpleEnsemble(models=models)
    metrics = ensemble.evaluate(y_true=test_data.values, n_steps=10)

    assert 'rmse' in metrics, "Expected RMSE in metrics"
    assert 'mae' in metrics, "Expected MAE in metrics"
    return metrics


def test_weighted_ensemble_predict():
    """Test WeightedEnsemble.predict()"""
    data = generate_time_series_data(150)
    train_data = data['value'][:100]

    models = create_fitted_arima_models(train_data, n_models=3)
    if len(models) < 2:
        raise ValueError("Need at least 2 models for ensemble")

    # Initialize with equal weights
    weights = [1.0 / len(models)] * len(models)
    ensemble = WeightedEnsemble(models=models, weights=weights)

    result = ensemble.predict(n_steps=10)

    # Check if result is EnsembleResult or array
    if hasattr(result, 'predictions'):
        predictions = result.predictions
    else:
        predictions = result

    assert len(predictions) == 10, f"Expected 10 predictions, got {len(predictions)}"
    return result


def test_weighted_ensemble_fit_weights():
    """Test WeightedEnsemble.fit_weights()"""
    data = generate_time_series_data(150)
    train_data = data['value'][:80]
    val_data = data['value'][80:100]

    models = create_fitted_arima_models(train_data, n_models=3)
    if len(models) < 2:
        raise ValueError("Need at least 2 models for ensemble")

    # Generate predictions from each model
    predictions = []
    for model in models:
        try:
            pred = model.forecast(steps=len(val_data))
            predictions.append(pred)
        except Exception as e:
            raise ValueError(f"Model prediction failed: {e}")

    ensemble = WeightedEnsemble(models=models)
    weights = ensemble.fit_weights(y_train=val_data.values, predictions=predictions)

    assert len(weights) == len(models), f"Expected {len(models)} weights, got {len(weights)}"
    assert abs(sum(weights) - 1.0) < 0.01, f"Weights should sum to 1, got {sum(weights)}"
    return weights


def test_stacking_ensemble_fit():
    """Test StackingEnsemble.fit()"""
    X, y = generate_regression_data(n_samples=100, n_features=5)

    base_models = create_sklearn_models()
    from sklearn.linear_model import Ridge
    meta_model = Ridge(alpha=0.1)

    ensemble = StackingEnsemble(
        base_models=base_models,
        meta_model=meta_model,
        cv_folds=3
    )

    # Fit on training data
    X_train, y_train = X[:80], y[:80]
    ensemble.fit(X_train, y_train)

    # Check that meta model was fitted
    assert hasattr(ensemble.meta_model, 'coef_'), "Meta model should be fitted"
    return ensemble


def test_stacking_ensemble_predict():
    """Test StackingEnsemble.predict()"""
    X, y = generate_regression_data(n_samples=100, n_features=5)

    base_models = create_sklearn_models()
    from sklearn.linear_model import Ridge
    meta_model = Ridge(alpha=0.1)

    ensemble = StackingEnsemble(
        base_models=base_models,
        meta_model=meta_model,
        cv_folds=3
    )

    # Fit and predict
    X_train, y_train = X[:80], y[:80]
    X_test = X[80:]

    ensemble.fit(X_train, y_train)
    predictions = ensemble.predict(X_test)

    assert len(predictions) == len(X_test), f"Expected {len(X_test)} predictions, got {len(predictions)}"
    return predictions


def test_dynamic_ensemble_predict():
    """Test DynamicEnsemble.predict()"""
    data = generate_time_series_data(150)
    train_data = data['value'][:100]

    models = create_fitted_arima_models(train_data, n_models=3)
    if len(models) < 2:
        raise ValueError("Need at least 2 models for ensemble")

    ensemble = DynamicEnsemble(
        models=models,
        window_size=10,
        selection_metric='mae',
        top_k=2
    )

    # Initialize performance history with some data
    for i in range(10):
        y_true = data['value'][100 + i]
        preds = [25.0 + np.random.randn() for _ in models]  # Mock predictions
        ensemble.update_performance(y_true, preds)

    # Now predict
    predictions, selected_indices = ensemble.predict(n_steps=1)

    assert len(predictions) == 1, f"Expected 1 prediction, got {len(predictions)}"
    assert len(selected_indices) <= 2, f"Expected at most 2 selected models, got {len(selected_indices)}"
    return predictions, selected_indices


def test_dynamic_ensemble_update_performance():
    """Test DynamicEnsemble.update_performance()"""
    data = generate_time_series_data(150)
    train_data = data['value'][:100]

    models = create_fitted_arima_models(train_data, n_models=3)
    if len(models) < 2:
        raise ValueError("Need at least 2 models for ensemble")

    ensemble = DynamicEnsemble(
        models=models,
        window_size=5,
        selection_metric='rmse',
        top_k=2
    )

    # Update performance multiple times
    for i in range(10):
        y_true = data['value'][100 + i]
        preds = [y_true + np.random.randn() for _ in models]
        ensemble.update_performance(y_true, preds)

    # Check that history is maintained
    assert len(ensemble.performance_history) > 0, "Performance history should be populated"
    assert len(ensemble.performance_history) <= 5, f"History should be capped at window_size=5"

    return ensemble.performance_history


# Main Benchmark Execution
def main():
    print("=" * 70)
    print("ENSEMBLE METHODS BENCHMARK")
    print("=" * 70)
    print(f"Goal: Test 8 methods to reach 75% coverage (67 → 75 methods)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    results = []

    # Test all 8 ensemble methods
    test_cases = [
        ("SimpleEnsemble.predict", test_simple_ensemble_predict, "Simple Ensemble"),
        ("SimpleEnsemble.evaluate", test_simple_ensemble_evaluate, "Simple Ensemble"),
        ("WeightedEnsemble.predict", test_weighted_ensemble_predict, "Weighted Ensemble"),
        ("WeightedEnsemble.fit_weights", test_weighted_ensemble_fit_weights, "Weighted Ensemble"),
        ("StackingEnsemble.fit", test_stacking_ensemble_fit, "Stacking Ensemble"),
        ("StackingEnsemble.predict", test_stacking_ensemble_predict, "Stacking Ensemble"),
        ("DynamicEnsemble.predict", test_dynamic_ensemble_predict, "Dynamic Ensemble"),
        ("DynamicEnsemble.update_performance", test_dynamic_ensemble_update_performance, "Dynamic Ensemble"),
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

    print("By Ensemble Type:")
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
    json_path = output_dir / f'ensemble_methods_{timestamp}.json'
    with open(json_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'successful': successful,
            'failed': failed,
            'results': results
        }, f, indent=2)

    # Save to CSV
    csv_path = output_dir / f'ensemble_methods_{timestamp}.csv'
    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)

    print(f"\n✓ Results saved to:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")

    print("\n" + "=" * 70)
    print(f"COVERAGE UPDATE: {successful}/8 ensemble methods tested successfully!")
    print(f"Expected total coverage: 67 + {successful} = {67 + successful}/99")
    print(f"Target: 75/99 (75%)")
    if successful == 8:
        print("🎉 GOAL ACHIEVED! All 8 ensemble methods tested!")
    print("=" * 70)

    return 0 if successful == total_tests else 1


if __name__ == '__main__':
    sys.exit(main())
