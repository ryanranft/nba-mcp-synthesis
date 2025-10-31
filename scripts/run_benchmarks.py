"""
Run all performance benchmarks and generate comprehensive report.

This script runs benchmarks for all working Phase 10A econometric tools
and generates a detailed performance report with timing and memory metrics.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.benchmarks.benchmark_framework import BenchmarkFramework
from tests.benchmarks.test_performance_benchmarks import (
    MockContext,
    generate_regression_data,
    generate_treatment_data,
    generate_survival_data,
    generate_time_series_data,
)
from mcp_server.fastmcp_server import (
    bayesian_linear_regression,
    BayesianLinearRegressionParams,
    propensity_score_matching,
    PropensityScoreMatchingParams,
    kaplan_meier,
    KaplanMeierParams,
    kalman_filter,
    KalmanFilterParams,
)


async def main():
    """Run all benchmarks and generate report."""
    print("=" * 70)
    print("PHASE 10A ECONOMETRIC TOOLS - PERFORMANCE BENCHMARK SUITE")
    print("=" * 70)
    print("\nRunning comprehensive benchmarks across 4 working tools...")
    print("Dataset sizes: Small (50-100), Medium (200-500), Large (500-1000)\n")

    framework = BenchmarkFramework(output_dir="benchmark_results")
    ctx = MockContext()

    # ==========================================================================
    # Bayesian Linear Regression Benchmarks
    # ==========================================================================
    print("\n🔬 Benchmarking: Bayesian Linear Regression")
    print("-" * 70)

    # Small
    data = generate_regression_data(n=50, n_predictors=3)
    params = BayesianLinearRegressionParams(
        data=data, formula="y ~ x1 + x2 + x3", n_samples=1000
    )
    result = await framework.benchmark_tool(
        "bayesian_linear_regression",
        bayesian_linear_regression,
        params,
        ctx,
        "small",
        50,
        iterations=3,
    )
    print(
        f"  Small (n=50):   {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Small (n=50): FAILED"
    )

    # Medium
    data = generate_regression_data(n=200, n_predictors=5)
    params = BayesianLinearRegressionParams(
        data=data, formula="y ~ x1 + x2 + x3 + x4 + x5", n_samples=1000
    )
    result = await framework.benchmark_tool(
        "bayesian_linear_regression",
        bayesian_linear_regression,
        params,
        ctx,
        "medium",
        200,
        iterations=3,
    )
    print(
        f"  Medium (n=200): {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Medium (n=200): FAILED"
    )

    # Large
    data = generate_regression_data(n=500, n_predictors=5)
    params = BayesianLinearRegressionParams(
        data=data, formula="y ~ x1 + x2 + x3 + x4 + x5", n_samples=1000
    )
    result = await framework.benchmark_tool(
        "bayesian_linear_regression",
        bayesian_linear_regression,
        params,
        ctx,
        "large",
        500,
        iterations=1,
    )
    print(
        f"  Large (n=500):  {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Large (n=500): FAILED"
    )

    # ==========================================================================
    # Propensity Score Matching Benchmarks
    # ==========================================================================
    print("\n🔬 Benchmarking: Propensity Score Matching")
    print("-" * 70)

    # Small
    data = generate_treatment_data(n=100)
    params = PropensityScoreMatchingParams(
        data=data,
        treatment_var="treatment",
        outcome_var="outcome",
        covariates=["age", "income"],
        matching_method="nearest",
    )
    result = await framework.benchmark_tool(
        "propensity_score_matching",
        propensity_score_matching,
        params,
        ctx,
        "small",
        100,
        iterations=3,
    )
    print(
        f"  Small (n=100):   {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Small (n=100): FAILED"
    )

    # Medium
    data = generate_treatment_data(n=500)
    params = PropensityScoreMatchingParams(
        data=data,
        treatment_var="treatment",
        outcome_var="outcome",
        covariates=["age", "income"],
        matching_method="nearest",
    )
    result = await framework.benchmark_tool(
        "propensity_score_matching",
        propensity_score_matching,
        params,
        ctx,
        "medium",
        500,
        iterations=3,
    )
    print(
        f"  Medium (n=500):  {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Medium (n=500): FAILED"
    )

    # Large
    data = generate_treatment_data(n=1000)
    params = PropensityScoreMatchingParams(
        data=data,
        treatment_var="treatment",
        outcome_var="outcome",
        covariates=["age", "income"],
        matching_method="nearest",
    )
    result = await framework.benchmark_tool(
        "propensity_score_matching",
        propensity_score_matching,
        params,
        ctx,
        "large",
        1000,
        iterations=1,
    )
    print(
        f"  Large (n=1000):  {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Large (n=1000): FAILED"
    )

    # ==========================================================================
    # Kaplan-Meier Benchmarks
    # ==========================================================================
    print("\n🔬 Benchmarking: Kaplan-Meier Survival Analysis")
    print("-" * 70)

    # Small
    data = generate_survival_data(n=50)
    params = KaplanMeierParams(data=data, duration_var="time", event_var="event")
    result = await framework.benchmark_tool(
        "kaplan_meier", kaplan_meier, params, ctx, "small", 50, iterations=3
    )
    print(
        f"  Small (n=50):    {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Small (n=50): FAILED"
    )

    # Medium
    data = generate_survival_data(n=200)
    params = KaplanMeierParams(data=data, duration_var="time", event_var="event")
    result = await framework.benchmark_tool(
        "kaplan_meier", kaplan_meier, params, ctx, "medium", 200, iterations=3
    )
    print(
        f"  Medium (n=200):  {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Medium (n=200): FAILED"
    )

    # Large
    data = generate_survival_data(n=1000)
    params = KaplanMeierParams(data=data, duration_var="time", event_var="event")
    result = await framework.benchmark_tool(
        "kaplan_meier", kaplan_meier, params, ctx, "large", 1000, iterations=1
    )
    print(
        f"  Large (n=1000):  {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Large (n=1000): FAILED"
    )

    # ==========================================================================
    # Kalman Filter Benchmarks
    # ==========================================================================
    print("\n🔬 Benchmarking: Kalman Filter Time Series")
    print("-" * 70)

    # Small
    data = generate_time_series_data(n=50)
    params = KalmanFilterParams(
        data=data,
        state_dim=1,
        observation_vars=["obs"],
        estimate_parameters=True,
        smoother=True,
    )
    result = await framework.benchmark_tool(
        "kalman_filter", kalman_filter, params, ctx, "small", 50, iterations=3
    )
    print(
        f"  Small (n=50):    {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Small (n=50): FAILED"
    )

    # Medium
    data = generate_time_series_data(n=200)
    params = KalmanFilterParams(
        data=data,
        state_dim=1,
        observation_vars=["obs"],
        estimate_parameters=True,
        smoother=True,
    )
    result = await framework.benchmark_tool(
        "kalman_filter", kalman_filter, params, ctx, "medium", 200, iterations=3
    )
    print(
        f"  Medium (n=200):  {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Medium (n=200): FAILED"
    )

    # Large
    data = generate_time_series_data(n=500)
    params = KalmanFilterParams(
        data=data,
        state_dim=1,
        observation_vars=["obs"],
        estimate_parameters=True,
        smoother=True,
    )
    result = await framework.benchmark_tool(
        "kalman_filter", kalman_filter, params, ctx, "large", 500, iterations=1
    )
    print(
        f"  Large (n=500):   {result.execution_time_ms:6.2f}ms | ✓"
        if result.success
        else "  Large (n=500): FAILED"
    )

    # ==========================================================================
    # Generate and Save Report
    # ==========================================================================
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 70)

    framework.print_summary()

    # Save to JSON
    filepath = framework.save_results(filename="phase10a_performance_benchmarks.json")
    print(f"\n✅ Full benchmark results saved to: {filepath}")

    # Print key findings
    summary = framework.generate_summary()
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)

    if "by_tool" in summary:
        print("\nAverage execution time by tool:")
        for tool, metrics in summary["by_tool"].items():
            print(f"  {tool:40s} {metrics['avg_time_ms']:8.2f}ms")

    if "threshold_violations" in summary and summary["threshold_violations"]:
        print(
            f"\n⚠️  Performance threshold violations: {len(summary['threshold_violations'])}"
        )
        for violation in summary["threshold_violations"][:5]:
            print(
                f"  - {violation['tool']} ({violation['size']}): {violation['time_ms']:.2f}ms"
            )
    else:
        print("\n✅ All benchmarks met performance thresholds!")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
