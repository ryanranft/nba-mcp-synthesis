"""
Benchmark Phase 2: Advanced Time Series & Bayesian Time Series Methods.

Tests:
- Advanced Time Series: Kalman Smoother, Structural TS, Impute Missing, Forecast State Space (4 methods)
- Bayesian Time Series: BVAR Impulse Response, FEVD (2 methods)
- Simple Methods: Sensitivity Analysis, Balance Check (2 methods)

Total: 8 methods to reach ~69% coverage

Usage:
    python scripts/benchmark_phase2_advanced.py
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

from mcp_server.advanced_time_series import AdvancedTimeSeriesAnalyzer
from mcp_server.bayesian_time_series import BVARAnalyzer
from mcp_server.causal_inference import CausalInferenceAnalyzer
from mcp_server.panel_data import PanelDataAnalyzer


# ==============================================================================
# Data Generators
# ==============================================================================


def generate_time_series_data(n=200, seed=42):
    """Generate time series data for state space methods."""
    np.random.seed(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="D")

    # Generate data with trend, seasonality, and noise
    t = np.arange(n)
    trend = 0.1 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 7)  # Weekly seasonality
    noise = np.random.normal(0, 2, n)

    y = 100 + trend + seasonal + noise

    return pd.DataFrame(
        {
            "date": dates,
            "value": y,
        }
    )


def generate_multivariate_ts(n=150, p=3, seed=42):
    """Generate multivariate time series for BVAR."""
    np.random.seed(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="D")

    # Generate VAR data
    data = {}
    for i in range(p):
        # Each series has some autocorrelation and cross-correlation
        series = np.zeros(n)
        series[0] = np.random.normal(10, 2)

        for t in range(1, n):
            # AR component
            ar_component = 0.5 * series[t - 1]
            # Random shock
            shock = np.random.normal(0, 1)
            series[t] = ar_component + shock

        data[f"var{i+1}"] = series

    df = pd.DataFrame(data)
    df["date"] = dates

    return df


def generate_causal_data(n=500, seed=42):
    """Generate data for sensitivity analysis."""
    np.random.seed(seed)

    # Covariates
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)

    # Treatment (with confounding)
    treatment_prob = 1 / (1 + np.exp(-(0.5 * x1 + 0.3 * x2)))
    treatment = np.random.binomial(1, treatment_prob, n)

    # Outcome (with treatment effect)
    y = 2 + 0.5 * x1 + 0.3 * x2 + 1.5 * treatment + np.random.normal(0, 1, n)

    return pd.DataFrame(
        {
            "y": y,
            "treatment": treatment,
            "x1": x1,
            "x2": x2,
        }
    )


def generate_panel_data(n_entities=50, n_periods=10, seed=42):
    """Generate panel data for balance check."""
    np.random.seed(seed)

    data = []
    for entity_id in range(n_entities):
        # Some entities have missing periods (unbalanced panel)
        periods = n_periods if entity_id % 3 != 0 else n_periods - 2

        for period in range(periods):
            data.append(
                {
                    "entity_id": entity_id,
                    "time_period": period,
                    "y": np.random.normal(10, 2),
                    "x": np.random.normal(5, 1),
                }
            )

    return pd.DataFrame(data)


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
    """Run Phase 2 benchmark."""

    print("=" * 70)
    print("PHASE 2: ADVANCED TIME SERIES & BAYESIAN TIME SERIES BENCHMARK")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # ========================================================================
    # ADVANCED TIME SERIES (4 methods)
    # ========================================================================
    print("🔹 Advanced Time Series Methods:")

    ts_data = generate_time_series_data(n=200)
    # AdvancedTimeSeriesAnalyzer takes Series or DataFrame with index as datetime
    ts_series = ts_data.set_index("date")["value"]
    ats = AdvancedTimeSeriesAnalyzer(
        data=ts_series,
        freq="D",
    )

    # Test Kalman Smoother
    results.append(
        benchmark_method(
            "Kalman Smoother (state space smoothing)",
            lambda: ats.kalman_smoother(model="local_level"),
            "Advanced Time Series",
        )
    )

    # Test Structural Time Series
    results.append(
        benchmark_method(
            "Structural Time Series (level + seasonal)",
            lambda: ats.structural_time_series(level=True, seasonal=7, trend=False),
            "Advanced Time Series",
        )
    )

    # Test Impute Missing
    # Add some missing values
    ts_series_missing = ts_series.copy()
    ts_series_missing.iloc[10:15] = np.nan
    ats_missing = AdvancedTimeSeriesAnalyzer(
        data=ts_series_missing,
        freq="D",
    )

    results.append(
        benchmark_method(
            "Impute Missing (Kalman filter)",
            lambda: ats_missing.impute_missing(method="kalman", model="local_level"),
            "Advanced Time Series",
        )
    )

    # Test Forecast State Space
    results.append(
        benchmark_method(
            "Forecast State Space (10 steps)",
            lambda: ats.forecast_state_space(model="local_level", steps=10),
            "Advanced Time Series",
        )
    )

    # ========================================================================
    # BAYESIAN TIME SERIES (2 methods)
    # ========================================================================
    print("\n🔹 Bayesian Time Series Methods:")

    bvar_data = generate_multivariate_ts(n=150, p=3)
    bvar = BVARAnalyzer(
        data=bvar_data,
        var_names=["var1", "var2", "var3"],
        lags=2,  # lags is in __init__
        minnesota_prior=True,
    )

    # Fit BVAR model first
    print("  [Fitting BVAR model...]", end=" ")
    try:
        bvar_result = bvar.fit(  # Method is just `fit()`
            draws=200,  # Small for speed
            tune=100,
            chains=2,
        )
        print("✓")
        bvar_fitted = True
    except Exception as e:
        print(f"✗ {e}")
        bvar_fitted = False
        bvar_result = None

    if bvar_fitted and bvar_result is not None:
        # Test Impulse Response
        results.append(
            benchmark_method(
                "BVAR Impulse Response (20 periods)",
                lambda: bvar.impulse_response(bvar_result, horizon=20, n_samples=100),
                "Bayesian Time Series",
            )
        )

        # Test Forecast Error Variance Decomposition
        results.append(
            benchmark_method(
                "Forecast Error Variance Decomposition",
                lambda: bvar.forecast_error_variance_decomposition(
                    bvar_result, horizon=20, n_samples=100
                ),
                "Bayesian Time Series",
            )
        )

    # ========================================================================
    # SIMPLE METHODS (2 methods)
    # ========================================================================
    print("\n🔹 Simple Methods:")

    # Test Sensitivity Analysis
    causal_data = generate_causal_data(n=500)
    causal = CausalInferenceAnalyzer(
        data=causal_data,
        outcome_col="y",
        treatment_col="treatment",
        covariates=["x1", "x2"],
    )

    results.append(
        benchmark_method(
            "Sensitivity Analysis (confounding)",
            lambda: causal.sensitivity_analysis(
                method="rosenbaum",
                effect_estimate=1.5,
                se_estimate=0.2,
                gamma_range=(1.0, 2.0),
            ),
            "Causal Inference",
        )
    )

    # Test Balance Check
    panel_data = generate_panel_data(n_entities=50, n_periods=10)
    panel = PanelDataAnalyzer(
        data=panel_data,
        entity_col="entity_id",
        time_col="time_period",
        target_col="y",  # Required parameter
    )

    results.append(
        benchmark_method(
            "Balance Check (panel structure)",
            lambda: panel.balance_check(),
            "Panel Data",
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
    for category in [
        "Advanced Time Series",
        "Bayesian Time Series",
        "Causal Inference",
        "Panel Data",
    ]:
        cat_results = [r for r in results if r["category"] == category]
        cat_success = [r for r in cat_results if r["success"]]
        if cat_results:
            print(
                f"  {category}: {len(cat_success)}/{len(cat_results)} ({100*len(cat_success)/len(cat_results):.0f}%)"
            )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_phase2_advanced_{timestamp}.json"

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
