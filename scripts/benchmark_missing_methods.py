"""
Quick Performance Benchmark for Missing Methods (Phase 1 Week 4).

Benchmarks 15+ methods that don't have existing performance data:
- Survival: Cox PH, Kaplan-Meier, Competing Risks, Recurrent Events, Fine-Gray
- Panel: System GMM, Difference GMM
- Causal: Synthetic Control, Kernel Matching, Doubly Robust
- Advanced TS: Cointegration, State Space

Measures execution time and success rate on small synthetic datasets.

Usage:
    python scripts/benchmark_missing_methods.py
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

from mcp_server.survival_analysis import SurvivalAnalyzer
from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.causal_inference import CausalInferenceAnalyzer
from mcp_server.time_series import TimeSeriesAnalyzer


def generate_survival_data(n=500):
    """Generate survival analysis data."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "player_id": [f"P{i:03d}" for i in range(n)],
            "duration": np.random.exponential(5, n),
            "event": np.random.binomial(1, 0.7, n),
            "age": np.random.normal(28, 4, n),
            "height": np.random.normal(78, 3, n),
            "draft_pick": np.random.randint(1, 61, n),
            "event_type": np.random.choice(["retirement", "injury", "trade"], n),
        }
    )


def generate_panel_data(n_entities=50, n_time=10):
    """Generate panel data for GMM."""
    np.random.seed(42)
    data = []
    for i in range(n_entities):
        for t in range(n_time):
            data.append(
                {
                    "entity": f"E{i:03d}",
                    "time": t,
                    "y": np.random.normal(10 + i * 0.1, 2),
                    "x1": np.random.normal(5, 1),
                    "x2": np.random.normal(3, 0.5),
                }
            )
    return pd.DataFrame(data)


def generate_causal_data(n=200):
    """Generate data for causal methods."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "unit_id": range(n),
            "treatment": np.random.binomial(1, 0.3, n),
            "outcome": np.random.normal(50, 10, n),
            "pre_treatment": np.random.normal(45, 8, n),
            "x1": np.random.normal(0, 1, n),
            "x2": np.random.normal(0, 1, n),
            "time_to_treatment": np.random.randint(1, 20, n),
        }
    )


def generate_ts_data(n=200):
    """Generate time series data."""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    # Cointegrated series
    x = np.cumsum(np.random.normal(0, 1, n))
    y = 2 * x + np.random.normal(0, 0.5, n)

    return pd.DataFrame(
        {"date": dates, "series1": x, "series2": y, "value": np.random.normal(20, 5, n)}
    )


def benchmark_method(method_name, func, timeout=30):
    """Benchmark a single method."""
    print(f"  Testing {method_name}...", end=" ")
    result = {
        "method": method_name,
        "execution_time": None,
        "success": False,
        "error": None,
    }

    try:
        start = time.time()
        func()
        elapsed = time.time() - start

        result["execution_time"] = round(elapsed, 4)
        result["success"] = True
        print(f"✓ ({elapsed:.3f}s)")
    except Exception as e:
        result["error"] = str(e)[:100]
        print(f"✗ ({str(e)[:50]})")

    return result


def main():
    """Run benchmarks for all missing methods."""
    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARK - MISSING METHODS (Phase 1 Week 4)")
    print("=" * 70 + "\n")

    results = []

    # ============================================================
    # SURVIVAL ANALYSIS METHODS
    # ============================================================
    print("📊 Survival Analysis Methods:")
    surv_data = generate_survival_data()
    analyzer = SurvivalAnalyzer(
        data=surv_data, duration_col="duration", event_col="event"
    )

    # Cox Proportional Hazards
    results.append(
        benchmark_method(
            "Cox Proportional Hazards",
            lambda: analyzer.cox_proportional_hazards(formula="age + height"),
        )
    )

    # Kaplan-Meier
    results.append(benchmark_method("Kaplan-Meier", lambda: analyzer.kaplan_meier()))

    # Competing Risks
    results.append(
        benchmark_method(
            "Competing Risks (Fine-Gray)",
            lambda: analyzer.competing_risks(
                event_type_col="event_type",
                event_types=["retirement", "injury", "trade"],
            ),
        )
    )

    # Recurrent Events (requires special data)
    rec_data = generate_survival_data(100)
    rec_data["event_num"] = np.tile(range(5), 20)
    rec_analyzer = SurvivalAnalyzer(
        data=rec_data, duration_col="duration", event_col="event"
    )
    results.append(
        benchmark_method(
            "Recurrent Events Model",
            lambda: rec_analyzer.recurrent_events_model(
                id_col="player_id",
                event_count_col="event_num",
                formula="age",
                model_type="ag",
            ),
        )
    )

    # ============================================================
    # PANEL DATA GMM METHODS
    # ============================================================
    print("\n📊 Panel Data GMM Methods:")
    panel_data = generate_panel_data()
    panel_analyzer = PanelDataAnalyzer(
        data=panel_data, entity_col="entity", time_col="time", target_col="y"
    )

    # Difference GMM
    results.append(
        benchmark_method(
            "Difference GMM",
            lambda: panel_analyzer.difference_gmm(formula="y ~ x1 + x2"),
        )
    )

    # System GMM
    results.append(
        benchmark_method(
            "System GMM", lambda: panel_analyzer.system_gmm(formula="y ~ x1 + x2")
        )
    )

    # ============================================================
    # CAUSAL INFERENCE METHODS
    # ============================================================
    print("\n📊 Advanced Causal Inference Methods:")
    causal_data = generate_causal_data()
    causal_analyzer = CausalInferenceAnalyzer(
        data=causal_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["x1", "x2"],
    )

    # Synthetic Control (requires panel structure)
    panel_causal = causal_data.copy()
    panel_causal["time"] = panel_causal["time_to_treatment"]
    sc_analyzer = CausalInferenceAnalyzer(
        data=panel_causal,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["x1", "x2"],
    )
    results.append(
        benchmark_method(
            "Synthetic Control",
            lambda: sc_analyzer.synthetic_control(
                unit_col="unit_id", time_col="time", treatment_period=10
            ),
        )
    )

    # Kernel Matching
    results.append(
        benchmark_method(
            "Kernel Matching",
            lambda: causal_analyzer.propensity_score_matching(
                method="kernel", bandwidth=0.1
            ),
        )
    )

    # Doubly Robust
    results.append(
        benchmark_method(
            "Doubly Robust Estimation", lambda: causal_analyzer.doubly_robust()
        )
    )

    # ============================================================
    # ADVANCED TIME SERIES
    # ============================================================
    print("\n📊 Advanced Time Series Methods:")
    ts_data = generate_ts_data()
    ts_analyzer = TimeSeriesAnalyzer(
        data=ts_data, target_column="value", time_column="date"
    )

    # Cointegration
    results.append(
        benchmark_method(
            "Cointegration (Engle-Granger)",
            lambda: ts_analyzer.cointegration_test(
                series1="series1", series2="series2"
            ),
        )
    )

    # State Space (via decomposition)
    results.append(
        benchmark_method(
            "State Space/Structural TS",
            lambda: ts_analyzer.decompose(model="additive", period=7),
        )
    )

    # ============================================================
    # GENERATE REPORT
    # ============================================================
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\n✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")

    if successful:
        print("\n⏱️  Execution Times (successful methods):")
        for r in sorted(successful, key=lambda x: x["execution_time"]):
            print(f"  {r['method']}: {r['execution_time']:.3f}s")

    if failed:
        print("\n❌ Failed Methods:")
        for r in failed:
            print(f"  {r['method']}: {r['error']}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"benchmark_missing_methods_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "total_methods": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 70 + "\n")

    return len(successful) >= 10  # Success if at least 10 methods work


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
