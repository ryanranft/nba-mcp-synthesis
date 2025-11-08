"""
Benchmark Priority Gap Methods (Panel GMM + Time Series Diagnostics).

Tests high-value methods identified as coverage gaps:
- Panel Data: Difference GMM, System GMM, GMM Diagnostics (3 methods)
- Time Series: Breusch-Godfrey, Heteroscedasticity, Structural Breaks,
               Validate Forecast, Time Series Diagnostics (5 methods)

Total: 8 high-priority methods

Usage:
    python scripts/benchmark_priority_gaps.py
"""

import time
import json
import traceback
import numpy as np
import pandas as pd
import warnings
from datetime import datetime
from pathlib import Path
import sys

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.time_series import TimeSeriesAnalyzer


# ==============================================================================
# Data Generators
# ==============================================================================


def generate_dynamic_panel_data(n_entities=50, n_time=10, seed=42):
    """Generate dynamic panel data for GMM estimation."""
    np.random.seed(seed)

    data = []
    for entity in range(n_entities):
        # Entity-specific effect
        alpha_i = np.random.normal(0, 1)

        # Initial value
        y_lag = 10 + alpha_i

        for t in range(n_time):
            # Dynamic panel: y_it = rho * y_{i,t-1} + beta * x_it + alpha_i + epsilon_it
            x = np.random.normal(5, 1)
            epsilon = np.random.normal(0, 0.5)

            # True parameters: rho=0.7, beta=0.5
            y = 0.7 * y_lag + 0.5 * x + alpha_i + epsilon

            data.append(
                {
                    "entity": entity,
                    "time": t,
                    "y": y,
                    "x": x,
                    "y_lag": y_lag,
                }
            )

            y_lag = y

    return pd.DataFrame(data)


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


def benchmark_method(name, func, category, timeout=60):
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

        # Print full traceback for debugging
        # traceback.print_exc()

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
    """Run benchmark of priority gap methods."""

    print("=" * 70)
    print("PRIORITY GAP METHODS BENCHMARK")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # ========================================================================
    # PANEL DATA GMM (3 methods)
    # ========================================================================
    print("🔹 Panel Data GMM Methods:")

    panel_data = generate_dynamic_panel_data(n_entities=50, n_time=10)
    panel = PanelDataAnalyzer(
        data=panel_data, entity_col="entity", time_col="time", target_col="y"
    )

    # Test Difference GMM
    def test_diff_gmm():
        # Formula: y ~ x (lag of y handled by GMM internally)
        # pydynpd automatically instruments with lags
        return panel.difference_gmm(
            formula="y ~ x",
            gmm_type="two_step",
            max_lags=2,
        )

    diff_gmm_result = None
    result = benchmark_method(
        "Difference GMM (Arellano-Bond)", test_diff_gmm, "Panel Data"
    )
    results.append(result)
    if result["success"]:
        diff_gmm_result = test_diff_gmm()

    # Test System GMM
    def test_sys_gmm():
        # Formula: y ~ x (lag of y handled by GMM internally)
        return panel.system_gmm(
            formula="y ~ x",
            gmm_type="two_step",
            max_lags=2,
        )

    sys_gmm_result = None
    result = benchmark_method("System GMM (Blundell-Bond)", test_sys_gmm, "Panel Data")
    results.append(result)
    if result["success"]:
        sys_gmm_result = test_sys_gmm()

    # Test GMM Diagnostics (if we have a result)
    if diff_gmm_result is not None:

        def test_gmm_diag():
            return panel.gmm_diagnostics(diff_gmm_result)

        results.append(benchmark_method("GMM Diagnostics", test_gmm_diag, "Panel Data"))
    else:
        print("  GMM Diagnostics... ✗ Skipped (no GMM result)")
        results.append(
            {
                "method": "GMM Diagnostics",
                "category": "Panel Data",
                "execution_time": 0,
                "success": False,
                "error": "Skipped - Difference GMM failed",
            }
        )

    # ========================================================================
    # TIME SERIES DIAGNOSTICS (5 methods)
    # ========================================================================
    print("\n🔹 Time Series Diagnostic Methods:")

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

        def test_bg():
            return ts.breusch_godfrey_test(model_result, nlags=2)

        results.append(benchmark_method("Breusch-Godfrey Test", test_bg, "Time Series"))
    else:
        print("  Breusch-Godfrey Test... ✗ Skipped (no model)")
        results.append(
            {
                "method": "Breusch-Godfrey Test",
                "category": "Time Series",
                "execution_time": 0,
                "success": False,
                "error": "Skipped - OLS fit failed",
            }
        )

    # Test Heteroscedasticity
    if model_result is not None:

        def test_hetero_bp():
            return ts.heteroscedasticity_tests(model_result, test_type="breusch_pagan")

        def test_hetero_white():
            return ts.heteroscedasticity_tests(model_result, test_type="white")

        results.append(
            benchmark_method(
                "Heteroscedasticity (Breusch-Pagan)", test_hetero_bp, "Time Series"
            )
        )
        results.append(
            benchmark_method(
                "Heteroscedasticity (White)", test_hetero_white, "Time Series"
            )
        )
    else:
        for test_name in [
            "Heteroscedasticity (Breusch-Pagan)",
            "Heteroscedasticity (White)",
        ]:
            print(f"  {test_name}... ✗ Skipped (no model)")
            results.append(
                {
                    "method": test_name,
                    "category": "Time Series",
                    "execution_time": 0,
                    "success": False,
                    "error": "Skipped - OLS fit failed",
                }
            )

    # Test Structural Breaks
    if model_result is not None:

        def test_breaks():
            return ts.detect_structural_breaks(model_result, test_type="both")

        results.append(
            benchmark_method("Detect Structural Breaks", test_breaks, "Time Series")
        )
    else:
        print("  Detect Structural Breaks... ✗ Skipped (no model)")
        results.append(
            {
                "method": "Detect Structural Breaks",
                "category": "Time Series",
                "execution_time": 0,
                "success": False,
                "error": "Skipped - OLS fit failed",
            }
        )

    # Test Time Series Diagnostics
    if residuals is not None:

        def test_ts_diag():
            return ts.time_series_diagnostics(residuals, lags=10)

        results.append(
            benchmark_method("Time Series Diagnostics", test_ts_diag, "Time Series")
        )
    else:
        print("  Time Series Diagnostics... ✗ Skipped (no residuals)")
        results.append(
            {
                "method": "Time Series Diagnostics",
                "category": "Time Series",
                "execution_time": 0,
                "success": False,
                "error": "Skipped - no residuals",
            }
        )

    # Test Validate Forecast
    # Fit ARIMA and forecast for validation
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
        ts_train.fit_arima(order=(1, 0, 1))

        # Forecast
        forecast = ts_train.forecast(steps=len(test_data))

        # Validate
        actual = test_data.set_index("date")["y"]
        predicted = pd.Series(forecast["mean"], index=actual.index)

        return ts.validate_forecast(actual, predicted)

    results.append(
        benchmark_method("Validate Forecast", test_validate_forecast, "Time Series")
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
    for category in ["Panel Data", "Time Series"]:
        cat_results = [r for r in results if r["category"] == category]
        cat_success = [r for r in cat_results if r["success"]]
        print(
            f"  {category}: {len(cat_success)}/{len(cat_results)} ({100*len(cat_success)/len(cat_results):.0f}%)"
        )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_priority_gaps_{timestamp}.json"

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
