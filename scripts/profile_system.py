#!/usr/bin/env python
"""
Profile the NBA MCP Synthesis System

Profiles key operations to establish performance baselines.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Import profiling tools
from mcp_server.profiling.performance import profile, get_profiler
from mcp_server.profiling.metrics_reporter import MetricsReporter


# ============================================================================
# Test Data Generation
# ============================================================================


def generate_sample_data(n_samples=1000):
    """Generate sample data for testing"""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "player_id": np.random.randint(1, 100, n_samples),
            "points": np.random.normal(15, 5, n_samples),
            "assists": np.random.normal(5, 2, n_samples),
            "rebounds": np.random.normal(7, 3, n_samples),
            "minutes": np.random.normal(25, 5, n_samples),
            "opponent_strength": np.random.uniform(0, 1, n_samples),
            "home_game": np.random.choice([0, 1], n_samples),
            "season": np.random.choice([2020, 2021, 2022, 2023], n_samples),
        }
    )


def generate_time_series_data(n_periods=200):
    """Generate time series data"""
    np.random.seed(42)
    dates = pd.date_range(start="2020-01-01", periods=n_periods, freq="D")

    # Create trend + seasonality + noise
    trend = np.linspace(10, 20, n_periods)
    seasonality = 5 * np.sin(np.linspace(0, 4 * np.pi, n_periods))
    noise = np.random.normal(0, 2, n_periods)

    return pd.Series(trend + seasonality + noise, index=dates, name="points_per_game")


# ============================================================================
# Profiled Test Functions
# ============================================================================


@profile
def test_data_generation_small():
    """Profile small dataset generation"""
    data = generate_sample_data(500)
    return len(data)


@profile
def test_data_generation_medium():
    """Profile medium dataset generation"""
    data = generate_sample_data(5000)
    return len(data)


@profile
def test_data_generation_large():
    """Profile large dataset generation"""
    data = generate_sample_data(50000)
    return len(data)


@profile
def test_data_processing_pipeline():
    """Profile typical data processing pipeline"""
    data = generate_sample_data(10000)

    # Feature engineering
    data["points_per_minute"] = data["points"] / (data["minutes"] + 0.1)
    data["efficiency"] = (data["points"] + data["assists"] + data["rebounds"]) / (
        data["minutes"] + 0.1
    )
    data["is_high_scorer"] = data["points"] > data["points"].quantile(0.75)

    # Filtering
    filtered = data[data["minutes"] > 10].copy()

    # Grouping and aggregation
    player_stats = filtered.groupby("player_id").agg(
        {
            "points": ["mean", "std", "max", "min"],
            "assists": ["mean", "std", "max"],
            "rebounds": ["mean", "std", "max"],
            "efficiency": ["mean", "max"],
        }
    )

    return len(player_stats)


@profile
def test_complex_aggregations():
    """Profile complex groupby and aggregation operations"""
    data = generate_sample_data(20000)

    # Multi-level grouping
    stats = data.groupby(["season", "home_game"]).agg(
        {
            "points": ["mean", "std", "count"],
            "assists": ["mean", "std"],
            "rebounds": ["mean", "std"],
            "minutes": "mean",
        }
    )

    # Pivot operations
    pivot = data.pivot_table(
        index="player_id", columns="season", values="points", aggfunc=["mean", "count"]
    )

    return stats.shape[0] + pivot.shape[0]


@profile
def test_time_series_operations():
    """Profile time series data operations"""
    ts_data = generate_time_series_data(500)

    # Rolling statistics
    rolling_mean = ts_data.rolling(window=7).mean()
    rolling_std = ts_data.rolling(window=7).std()

    # Resampling
    weekly = ts_data.resample("W").agg(["mean", "min", "max", "std"])

    # Lag features
    ts_df = pd.DataFrame(
        {
            "value": ts_data,
            "lag1": ts_data.shift(1),
            "lag7": ts_data.shift(7),
            "lag14": ts_data.shift(14),
        }
    )

    return len(weekly)


@profile
def test_statistical_operations():
    """Profile statistical calculations"""
    data = generate_sample_data(10000)

    # Correlation matrix
    corr = data[["points", "assists", "rebounds", "minutes"]].corr()

    # Quantiles
    quantiles = data["points"].quantile([0.1, 0.25, 0.5, 0.75, 0.9])

    # Z-scores
    from scipy import stats

    z_scores = np.abs(stats.zscore(data[["points", "assists", "rebounds"]]))

    # Outlier detection
    outliers = (z_scores > 3).any(axis=1).sum()

    return outliers


@profile
def test_merge_operations():
    """Profile data merging and joining"""
    data1 = generate_sample_data(5000)
    data2 = generate_sample_data(5000)

    # Inner merge
    merged_inner = pd.merge(
        data1, data2, on="player_id", how="inner", suffixes=("_1", "_2")
    )

    # Left merge
    merged_left = pd.merge(
        data1, data2, on="player_id", how="left", suffixes=("_1", "_2")
    )

    # Concatenation
    combined = pd.concat([data1, data2], ignore_index=True)

    return len(merged_inner) + len(merged_left) + len(combined)


@profile
def test_filtering_operations():
    """Profile complex filtering operations"""
    data = generate_sample_data(20000)

    # Multiple conditions
    filtered1 = data[(data["points"] > 20) & (data["minutes"] > 30)]

    # Query method
    filtered2 = data.query("points > @data.points.mean() and home_game == 1")

    # isin operations
    top_players = data.groupby("player_id")["points"].mean().nlargest(10).index
    filtered3 = data[data["player_id"].isin(top_players)]

    return len(filtered1) + len(filtered2) + len(filtered3)


@profile
def test_sorting_operations():
    """Profile sorting operations"""
    data = generate_sample_data(30000)

    # Single column sort
    sorted1 = data.sort_values("points", ascending=False)

    # Multi-column sort
    sorted2 = data.sort_values(["player_id", "points"], ascending=[True, False])

    # Sort with index
    sorted3 = data.set_index("player_id").sort_index()

    return len(sorted1)


@profile
def test_memory_intensive_operations():
    """Profile memory-intensive operations"""
    data = generate_sample_data(50000)

    # Create multiple derived columns
    for i in range(10):
        data[f"derived_{i}"] = data["points"] * np.random.random() + data["assists"]

    # Large groupby
    grouped = data.groupby("player_id").agg(
        {
            col: ["mean", "std", "min", "max"]
            for col in ["points", "assists", "rebounds"]
        }
    )

    return grouped.shape[0]


# ============================================================================
# Main Profiling Execution
# ============================================================================


def main():
    """Run system profiling and generate report"""
    print("=" * 80)
    print("NBA MCP Synthesis - System Performance Profiling")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Reset profiler
    profiler = get_profiler()
    profiler.reset()

    print("Running profiling tests...")
    print("-" * 80)

    # Run all profiling tests
    tests = [
        ("Small Dataset Generation (500 rows)", test_data_generation_small),
        ("Medium Dataset Generation (5K rows)", test_data_generation_medium),
        ("Large Dataset Generation (50K rows)", test_data_generation_large),
        ("Data Processing Pipeline", test_data_processing_pipeline),
        ("Complex Aggregations", test_complex_aggregations),
        ("Time Series Operations", test_time_series_operations),
        ("Statistical Operations", test_statistical_operations),
        ("Merge Operations", test_merge_operations),
        ("Filtering Operations", test_filtering_operations),
        ("Sorting Operations", test_sorting_operations),
        ("Memory Intensive Operations", test_memory_intensive_operations),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"  Running: {test_name}...", end=" ", flush=True)
            result = test_func()
            print(f"✓ Complete (result: {result})")
            results.append((test_name, "✓", result))
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
            results.append((test_name, "✗", str(e)))

    print()
    print("-" * 80)
    print("Profiling complete!")
    print()

    # Generate reports
    reporter = MetricsReporter(profiler)

    # 1. Console summary
    print(reporter.generate_text_report())

    # 2. Export JSON
    output_dir = Path(__file__).parent.parent / "benchmark_results"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"baseline_profile_{timestamp}.json"

    print(f"\nExporting detailed metrics to: {json_path}")
    reporter.export_to_json(str(json_path), include_raw_data=True)

    # 3. Generate HTML report
    html_path = output_dir / f"baseline_profile_{timestamp}.html"
    print(f"Generating HTML report: {html_path}")
    reporter.generate_html_report(str(html_path))

    # 4. Export CSV
    csv_path = output_dir / f"baseline_profile_{timestamp}.csv"
    print(f"Exporting CSV: {csv_path}")
    reporter.export_to_csv(str(csv_path))

    print()
    print("=" * 80)
    print("Profiling reports generated successfully!")
    print("=" * 80)
    print(f"\nReports saved to: {output_dir}")
    print(f"  - JSON: {json_path.name}")
    print(f"  - HTML: {html_path.name}")
    print(f"  - CSV: {csv_path.name}")

    # Identify bottlenecks
    bottlenecks = profiler.identify_bottlenecks(
        time_threshold_ms=100.0, call_threshold=1
    )

    if bottlenecks:
        print("\n⚠️  BOTTLENECKS IDENTIFIED:")
        print("-" * 80)
        for bottleneck in bottlenecks:
            print(f"  • {bottleneck['function_name']}")
            print(f"    - Avg time: {bottleneck['avg_time_ms']:.2f}ms")
            print(f"    - Call count: {bottleneck['call_count']}")
            print(f"    - Impact score: {bottleneck['impact_score']:.2f}")
            if "recommendations" in bottleneck:
                print(f"    - Recommendations:")
                for rec in bottleneck["recommendations"]:
                    print(f"      * {rec}")
            print()
    else:
        print("\n✅ No significant bottlenecks detected")

    # Summary statistics
    stats = profiler.get_summary()
    print("\n📊 PERFORMANCE SUMMARY:")
    print("-" * 80)
    print(f"  Total functions profiled: {stats['total_functions_profiled']}")
    print(f"  Total calls: {stats['total_calls']}")
    print(f"  Total time: {stats['total_time_ms']:.2f}ms")
    print(f"  Average time per call: {stats['avg_time_per_call_ms']:.2f}ms")

    # Slowest functions
    slowest = profiler.get_slowest_functions(n=5)
    if slowest:
        print("\n🐌 TOP 5 SLOWEST FUNCTIONS:")
        print("-" * 80)
        for i, func in enumerate(slowest, 1):
            print(f"  {i}. {func['function_name']}")
            print(
                f"     Avg: {func['avg_time_ms']:.2f}ms | Calls: {func['call_count']} | Total: {func['total_time_ms']:.2f}ms"
            )

    print()
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
