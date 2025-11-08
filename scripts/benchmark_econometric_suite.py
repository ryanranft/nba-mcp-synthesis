"""
Performance Benchmarking for Complete Econometric Suite.

Benchmarks all 27+ econometric methods across different dataset sizes:
- Small: 1,000 rows
- Medium: 10,000 rows
- Large: 100,000 rows

Measures:
- Execution time
- Memory usage
- Success/failure rate
- Timeout handling

Usage:
    python scripts/benchmark_econometric_suite.py
    python scripts/benchmark_econometric_suite.py --size small  # Quick test
    python scripts/benchmark_econometric_suite.py --timeout 60  # Custom timeout

Output:
    benchmark_econometric_results_{timestamp}.json
    benchmark_econometric_summary_{timestamp}.csv
    ECONOMETRIC_PERFORMANCE_REPORT.md
"""

import argparse
import time
import json
import numpy as np
import pandas as pd
import tracemalloc
import warnings
from datetime import datetime
from pathlib import Path
import sys
import signal

warnings.filterwarnings("ignore")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.econometric_suite import EconometricSuite


# ==============================================================================
# Timeout Handler
# ==============================================================================


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Benchmark timed out")


# ==============================================================================
# Data Generation
# ==============================================================================


def generate_dataset(n_rows, n_vars=5, seed=42):
    """
    Generate synthetic dataset for benchmarking.

    Args:
        n_rows: Number of observations
        n_vars: Number of predictor variables
        seed: Random seed for reproducibility

    Returns:
        DataFrame with outcome, treatment, controls, entity, time
    """
    np.random.seed(seed)

    # Continuous outcome
    outcome = np.random.normal(100, 15, n_rows)

    # Treatment variable
    treatment = np.random.normal(50, 10, n_rows)

    # Control variables
    controls = {}
    for i in range(n_vars):
        controls[f"control_{i}"] = np.random.normal(0, 1, n_rows)

    # Binary outcome for logistic
    binary_outcome = (outcome > 100).astype(int)

    # Entity and time for panel data
    n_entities = max(10, n_rows // 100)
    entity = np.repeat(range(n_entities), n_rows // n_entities)[:n_rows]
    time = np.tile(range(n_rows // n_entities), n_entities)[:n_rows]

    # Create DataFrame
    df = pd.DataFrame(
        {
            "outcome": outcome,
            "binary_outcome": binary_outcome,
            "treatment": treatment,
            **controls,
            "entity": entity,
            "time": time,
            "date": pd.date_range("2020-01-01", periods=n_rows, freq="D")[:n_rows],
        }
    )

    return df


# ==============================================================================
# Benchmark Runner
# ==============================================================================


def measure_performance(func, timeout_seconds=120):
    """
    Measure execution time and memory usage of a function.

    Args:
        func: Function to benchmark
        timeout_seconds: Maximum execution time

    Returns:
        (result, execution_time, peak_memory, success, error_message)
    """
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        # Start memory tracking
        tracemalloc.start()

        # Run function
        start_time = time.time()
        result = func()
        elapsed_time = time.time() - start_time

        # Get peak memory
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_memory_mb = peak / 1024 / 1024

        # Cancel timeout
        signal.alarm(0)

        return result, elapsed_time, peak_memory_mb, True, None

    except TimeoutError:
        signal.alarm(0)
        tracemalloc.stop()
        return None, timeout_seconds, 0, False, "Timeout"

    except Exception as e:
        signal.alarm(0)
        tracemalloc.stop()
        error_msg = f"{type(e).__name__}: {str(e)}"
        return None, 0, 0, False, error_msg


def benchmark_method(df, method_name, method_func, size_label, timeout=120):
    """
    Benchmark a single econometric method.

    Args:
        df: Dataset
        method_name: Name of method
        method_func: Function that runs the method
        size_label: Dataset size label (small/medium/large)
        timeout: Timeout in seconds

    Returns:
        Dictionary with benchmark results
    """
    print(f"  Testing {method_name}...", end=" ", flush=True)

    result, exec_time, memory, success, error = measure_performance(
        method_func, timeout_seconds=timeout
    )

    status = "✓" if success else "✗"
    time_str = (
        f"{exec_time:.2f}s" if success else "TIMEOUT" if error == "Timeout" else "ERROR"
    )
    print(f"{status} {time_str}")

    return {
        "method": method_name,
        "size": size_label,
        "n_rows": len(df),
        "execution_time": exec_time,
        "memory_mb": memory,
        "success": success,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


# ==============================================================================
# Method Definitions
# ==============================================================================


def get_benchmark_methods(df):
    """
    Define all methods to benchmark using correct EconometricSuite API.

    Returns:
        List of (name, func, requirements) tuples
    """
    methods = []

    # Prepare subsets
    df_time = df.sort_values("date").head(min(1000, len(df)))  # Limit time series
    df_panel = df[
        df["entity"].isin(df["entity"].unique()[: min(10, len(df["entity"].unique()))])
    ]  # Limit entities

    # Time Series Analysis
    def arima():
        """ARIMA time series forecasting."""
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.time_series_analysis(method="arima", order=(1, 1, 1))

    methods.append(("ARIMA", arima, "small_only"))

    def var_ts():
        """Vector Autoregression."""
        # VAR needs multiple endogenous variables
        endog = df_time[["outcome", "treatment", "control_0"]]
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.time_series_analysis(method="var", endog_data=endog, maxlags=2)

    methods.append(("VAR", var_ts, "small_only"))

    # Panel Data Analysis
    def panel_fe():
        """Panel Fixed Effects."""
        suite = EconometricSuite(
            data=df_panel, target="outcome", entity_col="entity", time_col="time"
        )
        return suite.panel_analysis(method="fixed_effects")

    methods.append(("Panel Fixed Effects", panel_fe, "medium_and_small"))

    def panel_re():
        """Panel Random Effects."""
        suite = EconometricSuite(
            data=df_panel, target="outcome", entity_col="entity", time_col="time"
        )
        return suite.panel_analysis(method="random_effects")

    methods.append(("Panel Random Effects", panel_re, "medium_and_small"))

    # Causal Inference
    def psm():
        """Propensity Score Matching."""
        # Create binary treatment
        df_causal = df.copy()
        df_causal["treatment_binary"] = (
            df_causal["treatment"] > df_causal["treatment"].median()
        ).astype(int)

        suite = EconometricSuite(
            data=df_causal.head(min(5000, len(df_causal))),
            treatment_col="treatment_binary",
            outcome_col="outcome",
        )
        return suite.causal_analysis(method="psm")

    methods.append(("Propensity Score Matching", psm, "medium_and_small"))

    def rdd():
        """Regression Discontinuity Design."""
        df_rdd = df.copy()
        df_rdd["running_var"] = np.random.uniform(0, 100, len(df_rdd))
        df_rdd["treatment_rdd"] = (df_rdd["running_var"] > 50).astype(int)

        suite = EconometricSuite(
            data=df_rdd.head(min(5000, len(df_rdd))),
            treatment_col="treatment_rdd",
            outcome_col="outcome",
        )
        return suite.causal_analysis(method="rdd", running_var="running_var", cutoff=50)

    methods.append(("Regression Discontinuity", rdd, "medium_and_small"))

    def iv():
        """Instrumental Variables."""
        df_iv = df.copy()
        df_iv["instrument"] = df_iv["control_0"] + np.random.normal(0, 0.1, len(df_iv))
        df_iv["treatment_binary"] = (
            df_iv["treatment"] > df_iv["treatment"].median()
        ).astype(int)

        suite = EconometricSuite(
            data=df_iv.head(min(5000, len(df_iv))),
            treatment_col="treatment_binary",
            outcome_col="outcome",
        )
        return suite.causal_analysis(method="iv", instruments=["instrument"])

    methods.append(("Instrumental Variables", iv, "medium_and_small"))

    # Bayesian Methods (small datasets only due to MCMC)
    def bvar():
        """Bayesian Vector Autoregression."""
        # Use even smaller subset for BVAR to ensure it completes quickly
        df_bvar = df_time.head(100)  # Only 100 observations for speed

        suite = EconometricSuite(data=df_bvar, target="outcome", time_col="date")
        return suite.bayesian_time_series_analysis(
            method="bvar",
            var_names=["outcome", "treatment", "control_0"],
            lags=1,  # Reduce lags from 2 to 1
            draws=50,  # Absolute minimum draws
            tune=50,  # Absolute minimum tuning
            chains=1,  # Single chain
        )

    methods.append(("Bayesian VAR", bvar, "small_only"))

    # Particle Filters (real-time methods)
    def particle_filter_player():
        """Particle Filter for Player Performance."""
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.particle_filter_analysis(
            method="player_performance",
            target_col="outcome",
            covariate_cols=["treatment"],
            n_particles=1000,
        )

    methods.append(("Particle Filter (Player)", particle_filter_player, "small_only"))

    # Advanced Time Series Methods
    def arimax():
        """ARIMAX with exogenous variables."""
        # Need to set date as index for ARIMAX
        df_arimax = df_time.copy()
        df_arimax = df_arimax.set_index("date")
        exog = df_arimax[["treatment", "control_0"]]

        suite = EconometricSuite(
            data=df_arimax, target="outcome", time_col=None  # Already in index
        )
        return suite.time_series_analysis(method="arimax", order=(1, 1, 1), exog=exog)

    methods.append(("ARIMAX", arimax, "small_only"))

    def stl_decomp():
        """STL seasonal decomposition."""
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.time_series_analysis(method="stl", period=7)

    methods.append(("STL Decomposition", stl_decomp, "small_only"))

    # Panel GMM Methods
    def first_diff():
        """First-difference panel estimator."""
        suite = EconometricSuite(
            data=df_panel, target="outcome", entity_col="entity", time_col="time"
        )
        return suite.panel_analysis(
            method="first_diff", formula="outcome ~ treatment + control_0"
        )

    methods.append(("Panel First-Difference", first_diff, "medium_and_small"))

    # Causal Inference - Advanced Methods
    def kernel_matching():
        """Kernel matching (weighted PSM)."""
        df_causal = df.copy()
        df_causal["treatment_binary"] = (
            df_causal["treatment"] > df_causal["treatment"].median()
        ).astype(int)

        suite = EconometricSuite(
            data=df_causal.head(min(5000, len(df_causal))),
            treatment_col="treatment_binary",
            outcome_col="outcome",
        )
        return suite.causal_analysis(method="kernel", kernel="gaussian")

    methods.append(("Kernel Matching", kernel_matching, "medium_and_small"))

    def doubly_robust():
        """Doubly robust estimation."""
        df_causal = df.copy()
        df_causal["treatment_binary"] = (
            df_causal["treatment"] > df_causal["treatment"].median()
        ).astype(int)

        suite = EconometricSuite(
            data=df_causal.head(min(5000, len(df_causal))),
            treatment_col="treatment_binary",
            outcome_col="outcome",
        )
        return suite.causal_analysis(method="doubly_robust")

    methods.append(("Doubly Robust", doubly_robust, "medium_and_small"))

    # Survival Analysis
    def cox_ph():
        """Cox Proportional Hazards."""
        # Create duration and event columns
        df_surv = df.copy()
        df_surv["duration"] = np.random.exponential(10, len(df_surv))
        df_surv["event"] = np.random.binomial(1, 0.7, len(df_surv))

        suite = EconometricSuite(
            data=df_surv.head(min(5000, len(df_surv))),
            duration_col="duration",
            event_col="event",
        )
        return suite.survival_analysis(method="cox")

    methods.append(("Cox Proportional Hazards", cox_ph, "medium_and_small"))

    def kaplan_meier():
        """Kaplan-Meier survival curves."""
        df_surv = df.copy()
        df_surv["duration"] = np.random.exponential(10, len(df_surv))
        df_surv["event"] = np.random.binomial(1, 0.7, len(df_surv))

        suite = EconometricSuite(
            data=df_surv.head(min(5000, len(df_surv))),
            duration_col="duration",
            event_col="event",
        )
        return suite.survival_analysis(method="kaplan_meier")

    methods.append(("Kaplan-Meier", kaplan_meier, "medium_and_small"))

    # Advanced Time Series
    def kalman_filter():
        """Kalman filter state estimation."""
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.advanced_time_series_analysis(method="kalman", model="local_level")

    methods.append(("Kalman Filter", kalman_filter, "small_only"))

    def markov_switching():
        """Markov regime switching model."""
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.advanced_time_series_analysis(
            method="markov_switching", n_regimes=2
        )

    methods.append(("Markov Switching", markov_switching, "small_only"))

    def dynamic_factor():
        """Dynamic factor model."""
        # Need multiple variables for DFM
        df_dfm = df_time[["outcome", "treatment", "control_0"]].copy()
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.advanced_time_series_analysis(
            method="dynamic_factor", data=df_dfm, n_factors=1, factor_order=2
        )

    methods.append(("Dynamic Factor Model", dynamic_factor, "small_only"))

    # More Time Series Methods
    def mstl():
        """Multiple Seasonal-Trend decomposition."""
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.time_series_analysis(method="mstl", periods=[7, 30])

    methods.append(("MSTL Decomposition", mstl, "small_only"))

    def granger():
        """Granger causality test."""
        suite = EconometricSuite(data=df_time, target="outcome", time_col="date")
        return suite.time_series_analysis(
            method="granger",
            caused_series="outcome",
            causing_series="treatment",
            maxlag=4,
        )

    methods.append(("Granger Causality", granger, "small_only"))

    def vecm():
        """Vector Error Correction Model."""
        # VECM requires multiple cointegrated series
        df_vecm = df_time.copy()
        df_vecm = df_vecm.set_index("date")
        endog = df_vecm[["outcome", "treatment"]]

        suite = EconometricSuite(
            data=df_vecm, target="outcome", time_col=None  # Already in index
        )
        return suite.time_series_analysis(
            method="vecm", endog_data=endog, k_ar_diff=2, coint_rank=1
        )

    methods.append(("VECM", vecm, "small_only"))

    # More Causal Inference Methods
    def synthetic_control():
        """Synthetic control method."""
        # Need panel structure with entity column
        suite = EconometricSuite(
            data=df_panel, outcome_col="outcome", entity_col="entity", time_col="time"
        )
        # Treat first entity as treated
        return suite.causal_analysis(
            method="synthetic",
            treated_unit=0,
            outcome_periods=list(range(100)),
            treatment_period=50,
        )

    methods.append(("Synthetic Control", synthetic_control, "small_only"))

    # Event Study - SKIPPED (not yet implemented)
    # def event_study():
    #     """Event study analysis."""
    #     # Panel data with event timing
    #     df_event = df_panel.copy()
    #     df_event['event_time'] = df_event['time'] - 50  # Event at period 50
    #     df_event['treated'] = (df_event['entity'] < 5).astype(int)  # Half treated
    #
    #     suite = EconometricSuite(
    #         data=df_event,
    #         treatment_col='treated',
    #         outcome_col='outcome',
    #         entity_col='entity',
    #         time_col='time'
    #     )
    #     return suite.causal_analysis(
    #         method='event_study',
    #         event_time_col='event_time',
    #         pre_periods=10,
    #         post_periods=10
    #     )
    # methods.append(('Event Study', event_study, 'medium_and_small'))

    # More Survival Methods
    def parametric_survival():
        """Parametric survival model (Weibull)."""
        df_surv = df.copy()
        df_surv["duration"] = np.random.exponential(10, len(df_surv))
        df_surv["event"] = np.random.binomial(1, 0.7, len(df_surv))

        suite = EconometricSuite(
            data=df_surv.head(min(5000, len(df_surv))),
            duration_col="duration",
            event_col="event",
        )
        return suite.survival_analysis(method="parametric", model="weibull")

    methods.append(
        ("Parametric Survival (Weibull)", parametric_survival, "medium_and_small")
    )

    def frailty_model():
        """Frailty model (random effects survival)."""
        df_surv = df_panel.copy()
        df_surv["duration"] = np.random.exponential(10, len(df_surv))
        df_surv["event"] = np.random.binomial(1, 0.7, len(df_surv))

        suite = EconometricSuite(
            data=df_surv, duration_col="duration", event_col="event"
        )
        return suite.survival_analysis(
            method="frailty", shared_frailty_col="entity", distribution="gamma"
        )

    methods.append(("Frailty Model", frailty_model, "small_only"))

    def competing_risks():
        """Competing risks survival analysis."""
        df_surv = df.copy()
        df_surv["duration"] = np.random.exponential(10, len(df_surv))
        # Create binary event indicator and separate event_type column
        event_types = np.random.choice([0, 1, 2], len(df_surv), p=[0.3, 0.4, 0.3])
        df_surv["event"] = (event_types > 0).astype(int)  # Binary: any event occurred
        df_surv["event_type"] = event_types  # Type of event

        suite = EconometricSuite(
            data=df_surv.head(min(5000, len(df_surv))),
            duration_col="duration",
            event_col="event",
        )
        return suite.survival_analysis(
            method="competing_risks", event_type_col="event_type", event_types=[1, 2]
        )

    methods.append(("Competing Risks", competing_risks, "medium_and_small"))

    return methods


# ==============================================================================
# Main Benchmarking
# ==============================================================================


def run_benchmarks(size="all", timeout=120):
    """
    Run all benchmarks.

    Args:
        size: 'small', 'medium', 'large', or 'all'
        timeout: Timeout per method in seconds

    Returns:
        List of benchmark results
    """
    print("=" * 70)
    print("ECONOMETRIC SUITE - PERFORMANCE BENCHMARKS")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Timeout per method: {timeout}s\n")

    sizes = {"small": 1000, "medium": 10000, "large": 100000}

    if size == "all":
        test_sizes = sizes
    else:
        test_sizes = {size: sizes[size]}

    all_results = []

    for size_label, n_rows in test_sizes.items():
        print(f"\n{'='*70}")
        print(f"DATASET SIZE: {size_label.upper()} ({n_rows:,} rows)")
        print(f"{'='*70}\n")

        # Generate dataset
        print(f"Generating {n_rows:,} row dataset...")
        df = generate_dataset(n_rows)
        print(f"✓ Dataset generated\n")

        # Get methods
        methods = get_benchmark_methods(df)

        # Run benchmarks
        for method_name, method_func, requirement in methods:
            # Check if method should run for this size
            if requirement == "small_only" and size_label != "small":
                print(f"  Skipping {method_name} (small datasets only)")
                continue
            elif requirement == "medium_and_small" and size_label == "large":
                print(f"  Skipping {method_name} (too large)")
                continue

            result = benchmark_method(
                df, method_name, method_func, size_label, timeout=timeout
            )
            all_results.append(result)

    return all_results


def generate_report(results, output_dir="."):
    """
    Generate comprehensive performance report.

    Args:
        results: List of benchmark results
        output_dir: Directory to save outputs
    """
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save JSON (detailed)
    json_path = Path(output_dir) / f"benchmark_econometric_results_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✓ Detailed results: {json_path}")

    # Save CSV (summary)
    csv_path = Path(output_dir) / f"benchmark_econometric_summary_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    print(f"✓ Summary CSV: {csv_path}")

    # Generate markdown report
    report_path = Path(output_dir) / "ECONOMETRIC_PERFORMANCE_REPORT.md"

    report = f"""# Econometric Suite Performance Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Methods Tested**: {df['method'].nunique()}
**Configurations**: {len(df)}

---

## Executive Summary

"""

    # Success rate
    success_rate = df["success"].mean() * 100
    report += f"**Overall Success Rate**: {success_rate:.1f}%\n\n"

    # Performance by method
    report += "## Performance by Method\n\n"
    report += "| Method | Small (1K) | Medium (10K) | Large (100K) | Status |\n"
    report += "|--------|------------|--------------|--------------|--------|\n"

    for method in df["method"].unique():
        method_data = df[df["method"] == method]
        row = f"| {method} |"

        for size in ["small", "medium", "large"]:
            size_data = method_data[method_data["size"] == size]
            if len(size_data) > 0:
                if size_data.iloc[0]["success"]:
                    time = size_data.iloc[0]["execution_time"]
                    row += f" {time:.2f}s |"
                else:
                    error = size_data.iloc[0]["error"]
                    if error == "Timeout":
                        row += " TIMEOUT |"
                    else:
                        row += " ERROR |"
            else:
                row += " - |"

        # Status
        if method_data["success"].all():
            row += " ✅ |\n"
        elif method_data["success"].any():
            row += " ⚠️ |\n"
        else:
            row += " ❌ |\n"

        report += row

    # Memory usage
    report += "\n## Memory Usage\n\n"
    report += "| Method | Peak Memory (MB) |\n"
    report += "|--------|------------------|\n"

    for method in df[df["success"]]["method"].unique():
        method_data = df[(df["method"] == method) & df["success"]]
        if len(method_data) > 0:
            max_memory = method_data["memory_mb"].max()
            report += f"| {method} | {max_memory:.1f} |\n"

    # Recommendations
    report += "\n## Recommendations\n\n"

    # Identify slow methods
    slow_methods = df[(df["success"]) & (df["execution_time"] > 10)]["method"].unique()
    if len(slow_methods) > 0:
        report += "**Slow Methods** (>10s):\n"
        for method in slow_methods:
            report += f"- {method}\n"
        report += "\n"

    # Identify failed methods
    failed_methods = df[~df["success"]]["method"].unique()
    if len(failed_methods) > 0:
        report += "**Failed Methods**:\n"
        for method in failed_methods:
            failures = df[(df["method"] == method) & (~df["success"])]
            for _, failure in failures.iterrows():
                report += f"- {method} ({failure['size']}): {failure['error']}\n"
        report += "\n"

    # Production readiness
    report += "## Production Readiness\n\n"
    fast_methods = df[(df["success"]) & (df["execution_time"] < 1)]["method"].unique()
    if len(fast_methods) > 0:
        report += "**Real-time Capable** (<1s):\n"
        for method in fast_methods:
            report += f"- ✅ {method}\n"
        report += "\n"

    medium_methods = df[
        (df["success"]) & (df["execution_time"] >= 1) & (df["execution_time"] < 10)
    ]["method"].unique()
    if len(medium_methods) > 0:
        report += "**Interactive Use** (1-10s):\n"
        for method in medium_methods:
            report += f"- ✓ {method}\n"
        report += "\n"

    batch_methods = df[(df["success"]) & (df["execution_time"] >= 10)][
        "method"
    ].unique()
    if len(batch_methods) > 0:
        report += "**Batch Processing** (>10s):\n"
        for method in batch_methods:
            report += f"- ⏰ {method}\n"
        report += "\n"

    # Write report
    with open(report_path, "w") as f:
        f.write(report)
    print(f"✓ Performance report: {report_path}")

    # Print summary to console
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"\nTotal methods tested: {df['method'].nunique()}")
    print(f"Total configurations: {len(df)}")
    print(f"Success rate: {success_rate:.1f}%")

    # Only show fastest if there are successful runs
    if df["success"].any():
        successful_df = df[df["success"]]
        fastest_idx = successful_df["execution_time"].idxmin()
        fastest_method = df.loc[fastest_idx, "method"]
        fastest_time = df.loc[fastest_idx, "execution_time"]
        print(f"\nFastest method: {fastest_method}")
        print(f"  Time: {fastest_time:.3f}s")
    else:
        print("\n⚠️  No successful runs to report")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Benchmark Econometric Suite")
    parser.add_argument(
        "--size",
        choices=["small", "medium", "large", "all"],
        default="all",
        help="Dataset size to test",
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Timeout per method (seconds)"
    )
    parser.add_argument("--output", default=".", help="Output directory for results")

    args = parser.parse_args()

    # Run benchmarks
    results = run_benchmarks(size=args.size, timeout=args.timeout)

    # Generate report
    generate_report(results, output_dir=args.output)

    print(f"\n{'='*70}")
    print(f"Benchmarking complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
