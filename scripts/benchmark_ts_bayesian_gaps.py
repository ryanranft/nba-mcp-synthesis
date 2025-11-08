"""
Benchmark Time Series Diagnostics & Bayesian Model Comparison.

Tests remaining high-value methods without external dependencies:
- Time Series: Breusch-Godfrey, Heteroscedasticity, Structural Breaks,
               Validate Forecast, Time Series Diagnostics (5 methods)
- Bayesian: WAIC, LOO, Variational Inference, Hierarchical Model (4+ methods)

Total: 9+ high-priority methods

Usage:
    python scripts/benchmark_ts_bayesian_gaps.py
"""

import time
import json
import numpy as np
import pandas as pd
import warnings
from datetime import datetime
from pathlib import Path
import sys

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.time_series import TimeSeriesAnalyzer
from mcp_server.bayesian import BayesianAnalyzer, HierarchicalModelSpec


# ==============================================================================
# Data Generators
# ==============================================================================


def generate_ts_for_diagnostics(n=200, seed=42):
    """Generate time series with known properties for diagnostic testing."""
    np.random.seed(seed)

    dates = pd.date_range("2020-01-01", periods=n, freq="D")

    # Create predictors
    x1 = np.random.normal(10, 2, n)
    x2 = np.random.normal(5, 1, n)

    # Create dependent variable with some heteroscedasticity and autocorrelation
    epsilon = np.random.normal(0, 1 + 0.5 * (x1 - 10) ** 2 / 4, n)  # Heteroscedastic

    # Add autocorrelation
    for i in range(1, n):
        epsilon[i] += 0.3 * epsilon[i - 1]

    y = 5 + 0.5 * x1 + 0.3 * x2 + epsilon

    return pd.DataFrame(
        {
            "date": dates,
            "y": y,
            "x1": x1,
            "x2": x2,
        }
    )


# ==============================================================================
# Benchmark Helper
# ==============================================================================


def benchmark_method(name, func, category):
    """Benchmark a single method."""
    print(f"  {name}...", end=" ", flush=True)

    start_time = time.time()
    try:
        result = func()
        elapsed = time.time() - start_time

        print(f"✓ {elapsed:.3f}s")
        return {
            "method": name,
            "category": category,
            "execution_time": elapsed,
            "success": True,
            "error": None,
        }
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"✗ {error_msg[:70]}")

        return {
            "method": name,
            "category": category,
            "execution_time": elapsed,
            "success": False,
            "error": error_msg,
        }


# ==============================================================================
# Main Benchmark
# ==============================================================================


def run_benchmark():
    """Run benchmark of Time Series and Bayesian gaps."""

    print("=" * 70)
    print("TIME SERIES DIAGNOSTICS & BAYESIAN METHODS BENCHMARK")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # ========================================================================
    # TIME SERIES DIAGNOSTICS (5 methods)
    # ========================================================================
    print("🔹 Time Series Diagnostic Methods:")

    ts_data = generate_ts_for_diagnostics(n=200)
    ts = TimeSeriesAnalyzer(
        data=ts_data,
        target_column="y",
        time_column="date",
    )

    # Fit a model first to get residuals and model_result
    print("  [Fitting OLS model for diagnostics...]", end=" ")
    try:
        # Use statsmodels OLS for regression
        import statsmodels.api as sm

        X = ts_data[["x1", "x2"]]
        X = sm.add_constant(X)
        y = ts_data["y"]

        model_result = sm.OLS(y, X).fit()
        residuals = model_result.resid
        print("✓")
    except Exception as e:
        print(f"✗ {e}")
        model_result = None
        residuals = None

    # Test Breusch-Godfrey
    if model_result is not None:
        results.append(
            benchmark_method(
                "Breusch-Godfrey Test (AR autocorrelation)",
                lambda: ts.breusch_godfrey_test(model_result, nlags=2),
                "Time Series",
            )
        )

    # Test Heteroscedasticity - Breusch-Pagan
    if model_result is not None:
        results.append(
            benchmark_method(
                "Heteroscedasticity Test (Breusch-Pagan)",
                lambda: ts.heteroscedasticity_tests(
                    model_result, test_type="breusch_pagan"
                ),
                "Time Series",
            )
        )

    # Test Heteroscedasticity - White
    if model_result is not None:
        results.append(
            benchmark_method(
                "Heteroscedasticity Test (White)",
                lambda: ts.heteroscedasticity_tests(model_result, test_type="white"),
                "Time Series",
            )
        )

    # Test Structural Breaks
    if model_result is not None:
        results.append(
            benchmark_method(
                "Detect Structural Breaks (CUSUM & Hansen)",
                lambda: ts.detect_structural_breaks(model_result, test_type="both"),
                "Time Series",
            )
        )

    # Test Time Series Diagnostics
    if residuals is not None:
        results.append(
            benchmark_method(
                "Time Series Diagnostics (comprehensive)",
                lambda: ts.time_series_diagnostics(residuals, lags=10),
                "Time Series",
            )
        )

    # Test Validate Forecast
    def test_validate_forecast():
        # Split data into train/test
        train_size = int(0.8 * len(ts_data))
        train_data = ts_data.iloc[:train_size]
        test_data = ts_data.iloc[train_size:]

        # Fit ARIMA on training data
        ts_train = TimeSeriesAnalyzer(
            data=train_data,
            target_column="y",
            time_column="date",
        )
        arima_result = ts_train.fit_arima(order=(1, 0, 1))

        # Forecast
        forecast_result = ts_train.forecast(arima_result, steps=len(test_data))

        # Validate
        actual = test_data.set_index("date")["y"]
        # ForecastResult has .forecast attribute containing the forecast Series
        predicted = forecast_result.forecast
        # Align indices
        predicted = pd.Series(predicted.values, index=actual.index)

        return ts.validate_forecast(actual, predicted)

    results.append(
        benchmark_method(
            "Validate Forecast (MAE/RMSE/MAPE)", test_validate_forecast, "Time Series"
        )
    )

    # ========================================================================
    # BAYESIAN METHODS (6+ methods)
    # ========================================================================
    print("\n🔹 Bayesian Methods:")

    # Generate data for Bayesian analysis
    bayes_data = ts_data.head(50).copy()
    bayes_data["y_scaled"] = (bayes_data["y"] - bayes_data["y"].mean()) / bayes_data[
        "y"
    ].std()

    # Build and sample a model for testing
    print("  [Fitting Bayesian model for diagnostics...]", end=" ")
    try:
        bayes = BayesianAnalyzer(data=bayes_data, target="y_scaled")
        bayes.build_simple_model(formula="y_scaled ~ x1 + x2")
        bayes_result = bayes.sample_posterior(draws=100, tune=50, chains=2)  # Small for speed
        print("✓")
        model_fitted = True
    except Exception as e:
        print(f"✗ {e}")
        model_fitted = False
        bayes_result = None

    if model_fitted and bayes_result is not None:
        # Test WAIC
        results.append(
            benchmark_method(
                "WAIC (Watanabe-Akaike Information Criterion)",
                lambda: bayes.waic(bayes_result),
                "Bayesian",
            )
        )

        # Test LOO
        results.append(
            benchmark_method(
                "LOO (Leave-One-Out Cross-Validation)", lambda: bayes.loo(bayes_result), "Bayesian"
            )
        )

        # Test Effective Sample Size
        results.append(
            benchmark_method(
                "Effective Sample Size",
                lambda: bayes.effective_sample_size(bayes_result),
                "Bayesian",
            )
        )

        # Test Rhat Statistic
        results.append(
            benchmark_method(
                "Rhat Statistic (convergence diagnostic)",
                lambda: bayes.rhat_statistic(bayes_result),
                "Bayesian",
            )
        )

        # Test Posterior Predictive Check
        if hasattr(bayes, "posterior_predictive_check"):
            results.append(
                benchmark_method(
                    "Posterior Predictive Check",
                    lambda: bayes.posterior_predictive_check(bayes_result),
                    "Bayesian",
                )
            )

    # Test Variational Inference (independent of MCMC)
    bayes_vi = BayesianAnalyzer(data=bayes_data, target="y_scaled")
    bayes_vi.build_simple_model(formula="y_scaled ~ x1 + x2")

    if hasattr(bayes_vi, "variational_inference"):
        results.append(
            benchmark_method(
                "Variational Inference (ADVI)",
                lambda: bayes_vi.variational_inference(n_iter=10000),
                "Bayesian",
            )
        )

    # Test Hierarchical Model building
    # Add a grouping variable
    bayes_data["group"] = np.random.choice(["A", "B", "C"], len(bayes_data))
    bayes_hier = BayesianAnalyzer(data=bayes_data, target="y_scaled")

    if hasattr(bayes_hier, "hierarchical_model"):

        def test_hierarchical():
            # Create hierarchical model spec
            spec = HierarchicalModelSpec(group_variable="group")
            bayes_hier.hierarchical_model(spec, formula="y_scaled ~ x1 + x2")
            # Sample to verify it works
            bayes_hier.sample_posterior(draws=50, tune=25, chains=1)
            return True

        results.append(
            benchmark_method(
                "Hierarchical Model (partial pooling)", test_hierarchical, "Bayesian"
            )
        )

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(
        f"\n✅ Successful: {len(successful)}/{len(results)} ({100*len(successful)/len(results):.1f}%)"
    )
    print(f"❌ Failed: {len(failed)}/{len(results)}")

    if successful:
        times = [r["execution_time"] for r in successful]
        print(f"\n⏱️  Execution Times:")
        print(f"  • Fastest: {min(times):.3f}s")
        print(f"  • Slowest: {max(times):.3f}s")
        print(f"  • Average: {np.mean(times):.3f}s")
        print(f"  • Median: {np.median(times):.3f}s")

    if failed:
        print(f"\n❌ Failed Methods:")
        for r in failed:
            print(f"  • {r['method']}: {r['error'][:80]}")

    # Category breakdown
    print(f"\n📊 By Category:")
    for category in ["Time Series", "Bayesian"]:
        cat_results = [r for r in results if r["category"] == category]
        cat_success = [r for r in cat_results if r["success"]]
        if cat_results:
            print(
                f"  {category}: {len(cat_success)}/{len(cat_results)} ({100*len(cat_success)/len(cat_results):.0f}%)"
            )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_ts_bayesian_gaps_{timestamp}.json"

    output = {
        "timestamp": timestamp,
        "total_methods": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "results": results,
        "summary": {
            "fastest": (
                min([r["execution_time"] for r in successful]) if successful else None
            ),
            "slowest": (
                max([r["execution_time"] for r in successful]) if successful else None
            ),
            "average": (
                np.mean([r["execution_time"] for r in successful])
                if successful
                else None
            ),
            "median": (
                np.median([r["execution_time"] for r in successful])
                if successful
                else None
            ),
        },
    }

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n📄 Results saved to: {filename}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    run_benchmark()
