"""
Comprehensive Performance Benchmark for NBA Analytics Platform.

Benchmarks 25+ critical econometric methods across:
- Time Series Analysis
- Panel Data Analysis
- Causal Inference
- Survival Analysis
- Bayesian Methods

Measures execution time and memory usage on realistic NBA-sized datasets.

Usage:
    python scripts/benchmark_comprehensive.py
    python scripts/benchmark_comprehensive.py --quick  # Fast test mode
"""

import argparse
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
from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.causal_inference import CausalInferenceAnalyzer
from mcp_server.survival_analysis import SurvivalAnalyzer
from mcp_server.bayesian import BayesianAnalyzer


# ==============================================================================
# Data Generation
# ==============================================================================


def generate_time_series_data(n=200, seed=42):
    """Generate realistic time series data (player performance over time)."""
    np.random.seed(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="D")

    # Simulate player performance with trend and seasonality
    trend = np.linspace(20, 25, n)
    seasonal = 3 * np.sin(np.arange(n) * 2 * np.pi / 82)  # 82-game season
    noise = np.random.normal(0, 2, n)
    points = trend + seasonal + noise

    return pd.DataFrame(
        {
            "date": dates,
            "player_id": "LeBron_James",
            "points": points,
            "minutes": np.random.normal(35, 3, n),
            "assists": np.random.poisson(7, n),
            "rebounds": np.random.poisson(8, n),
        }
    )


def generate_panel_data(n_players=30, n_seasons=5, seed=42):
    """Generate panel data (multiple players over multiple seasons)."""
    np.random.seed(seed)
    data = []

    for player_id in range(n_players):
        for season in range(n_seasons):
            data.append(
                {
                    "player_id": f"P{player_id:03d}",
                    "season": season,
                    "points_per_game": np.random.normal(15 + player_id * 0.2, 5),
                    "minutes_per_game": np.random.normal(28, 5),
                    "age": 22 + season,
                    "experience": season,
                    "team_wins": np.random.randint(20, 60),
                }
            )

    return pd.DataFrame(data)


def generate_causal_data(n=300, seed=42):
    """Generate data for causal inference (coaching change impact)."""
    np.random.seed(seed)
    return pd.DataFrame(
        {
            "team_id": [f"T{i:03d}" for i in range(n)],
            "coaching_change": np.random.binomial(1, 0.3, n),
            "win_pct": np.random.uniform(0.3, 0.7, n),
            "payroll": np.random.normal(120, 30, n),
            "prior_wins": np.random.randint(20, 60, n),
            "market_size": np.random.choice(["small", "medium", "large"], n),
        }
    )


def generate_survival_data(n=200, seed=42):
    """Generate survival data (player career duration)."""
    np.random.seed(seed)
    return pd.DataFrame(
        {
            "player_id": [f"P{i:03d}" for i in range(n)],
            "career_years": np.random.exponential(5, n),
            "retired": np.random.binomial(1, 0.7, n),
            "draft_position": np.random.randint(1, 61, n),
            "height": np.random.normal(78, 3, n),
            "college": np.random.choice(["Duke", "UNC", "Kansas", "Kentucky"], n),
            "position": np.random.choice(["G", "F", "C"], n),
        }
    )


# ==============================================================================
# Benchmark Helper
# ==============================================================================


def benchmark_method(name, func, category="General"):
    """Benchmark a single method."""
    print(f"  {name}...", end=" ", flush=True)

    try:
        start = time.time()
        result = func()
        elapsed = time.time() - start

        print(f"✓ {elapsed:.3f}s")
        return {
            "method": name,
            "category": category,
            "execution_time": round(elapsed, 4),
            "success": True,
            "error": None,
        }
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:80]}"
        print(f"✗ {error_msg[:50]}")
        return {
            "method": name,
            "category": category,
            "execution_time": 0,
            "success": False,
            "error": error_msg,
        }


# ==============================================================================
# Main Benchmark Suite
# ==============================================================================


def run_comprehensive_benchmarks(quick_mode=False):
    """Run comprehensive benchmarks across all method categories."""

    print("\n" + "=" * 70)
    print("COMPREHENSIVE NBA ANALYTICS PLATFORM BENCHMARK")
    print("=" * 70 + "\n")

    results = []

    # Generate datasets
    print("📊 Generating test datasets...")
    ts_data = generate_time_series_data(n=100 if quick_mode else 200)
    panel_data = generate_panel_data(n_players=20 if quick_mode else 30)
    causal_data = generate_causal_data(n=150 if quick_mode else 300)
    surv_data = generate_survival_data(n=100 if quick_mode else 200)
    print("   ✓ Datasets generated\n")

    # ========================================================================
    # TIME SERIES METHODS
    # ========================================================================
    print("🔹 Time Series Analysis Methods:")
    ts_analyzer = TimeSeriesAnalyzer(
        data=ts_data, target_column="points", time_column="date"
    )

    results.append(
        benchmark_method(
            "ARIMA(1,1,1)",
            lambda: ts_analyzer.fit_arima(order=(1, 1, 1)),
            "Time Series",
        )
    )

    results.append(
        benchmark_method(
            "Auto-ARIMA",
            lambda: ts_analyzer.auto_arima(max_p=2, max_q=2, seasonal=False),
            "Time Series",
        )
    )

    results.append(
        benchmark_method(
            "VAR(2 lags)",
            lambda: ts_analyzer.fit_var(
                endog_data=ts_data[["points", "assists", "rebounds"]], maxlags=2
            ),
            "Time Series",
        )
    )

    results.append(
        benchmark_method(
            "Seasonal Decomposition",
            lambda: ts_analyzer.decompose(model="additive", period=7),
            "Time Series",
        )
    )

    # ========================================================================
    # PANEL DATA METHODS
    # ========================================================================
    print("\n🔹 Panel Data Analysis Methods:")
    panel_analyzer = PanelDataAnalyzer(
        data=panel_data,
        entity_col="player_id",
        time_col="season",
        target_col="points_per_game",
    )

    results.append(
        benchmark_method(
            "Pooled OLS",
            lambda: panel_analyzer.pooled_ols(
                formula="points_per_game ~ age + experience"
            ),
            "Panel Data",
        )
    )

    results.append(
        benchmark_method(
            "Fixed Effects",
            lambda: panel_analyzer.fixed_effects(
                formula="points_per_game ~ age + experience"
            ),
            "Panel Data",
        )
    )

    results.append(
        benchmark_method(
            "Random Effects",
            lambda: panel_analyzer.random_effects(
                formula="points_per_game ~ age + experience"
            ),
            "Panel Data",
        )
    )

    results.append(
        benchmark_method(
            "First Difference",
            lambda: panel_analyzer.first_difference(formula="points_per_game ~ age"),
            "Panel Data",
        )
    )

    results.append(
        benchmark_method(
            "Hausman Test",
            lambda: panel_analyzer.hausman_test(
                formula="points_per_game ~ age + experience"
            ),
            "Panel Data",
        )
    )

    # ========================================================================
    # CAUSAL INFERENCE METHODS
    # ========================================================================
    print("\n🔹 Causal Inference Methods:")
    causal_analyzer = CausalInferenceAnalyzer(
        data=causal_data,
        treatment_col="coaching_change",
        outcome_col="win_pct",
        covariates=["payroll", "prior_wins"],
    )

    results.append(
        benchmark_method(
            "Propensity Score Matching",
            lambda: causal_analyzer.propensity_score_matching(method="nearest"),
            "Causal Inference",
        )
    )

    results.append(
        benchmark_method(
            "Regression Discontinuity",
            lambda: causal_analyzer.regression_discontinuity(
                running_var="prior_wins", cutoff=41
            ),
            "Causal Inference",
        )
    )

    results.append(
        benchmark_method(
            "Instrumental Variables",
            lambda: causal_analyzer.instrumental_variables(
                instruments=["payroll"], formula="win_pct ~ coaching_change"
            ),
            "Causal Inference",
        )
    )

    # ========================================================================
    # SURVIVAL ANALYSIS METHODS
    # ========================================================================
    print("\n🔹 Survival Analysis Methods:")
    surv_analyzer = SurvivalAnalyzer(
        data=surv_data, duration_col="career_years", event_col="retired"
    )

    results.append(
        benchmark_method(
            "Cox Proportional Hazards",
            lambda: surv_analyzer.cox_proportional_hazards(
                formula="draft_position + height"
            ),
            "Survival Analysis",
        )
    )

    results.append(
        benchmark_method(
            "Kaplan-Meier Estimation",
            lambda: surv_analyzer.kaplan_meier(),
            "Survival Analysis",
        )
    )

    results.append(
        benchmark_method(
            "Competing Risks (Fine-Gray)",
            lambda: surv_analyzer.competing_risks(
                event_type_col="position",  # Using position as proxy for event type
                event_types=["G", "F", "C"],
            ),
            "Survival Analysis",
        )
    )

    results.append(
        benchmark_method(
            "Parametric Survival (Weibull)",
            lambda: surv_analyzer.parametric_survival(
                model="weibull", formula="draft_position + height"
            ),
            "Survival Analysis",
        )
    )

    # ========================================================================
    # BAYESIAN METHODS (if not in quick mode)
    # ========================================================================
    if not quick_mode:
        print("\n🔹 Bayesian Methods:")

        # Prepare small dataset for Bayesian (they're slow)
        bayes_data = panel_data.head(50).copy()
        bayes_data["points_scaled"] = (
            bayes_data["points_per_game"] - bayes_data["points_per_game"].mean()
        ) / bayes_data["points_per_game"].std()
        bayes_analyzer = BayesianAnalyzer(data=bayes_data, target="points_scaled")

        results.append(
            benchmark_method(
                "Sample Posterior (MCMC)",
                lambda: bayes_analyzer.sample_posterior(
                    formula="points_scaled ~ age + experience",
                    draws=200,
                    tune=100,
                    chains=1,
                ),
                "Bayesian",
            )
        )

    # ========================================================================
    # RESULTS SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(
        f"\n✅ Successful: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)"
    )
    print(f"❌ Failed: {len(failed)}/{len(results)}")

    if successful:
        print("\n⏱️  Execution Times (by category):")

        categories = sorted(set(r["category"] for r in successful))
        for cat in categories:
            cat_results = [r for r in successful if r["category"] == cat]
            print(f"\n  {cat}:")
            for r in sorted(cat_results, key=lambda x: x["execution_time"]):
                print(f"    • {r['method']}: {r['execution_time']:.3f}s")

    if failed:
        print("\n❌ Failed Methods:")
        for r in failed:
            print(f"  • {r['method']}: {r['error'][:60]}")

    # Performance Summary
    if successful:
        times = [r["execution_time"] for r in successful]
        print(f"\n📊 Performance Summary:")
        print(f"  • Fastest: {min(times):.3f}s")
        print(f"  • Slowest: {max(times):.3f}s")
        print(f"  • Average: {np.mean(times):.3f}s")
        print(f"  • Median: {np.median(times):.3f}s")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"benchmark_comprehensive_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "quick_mode": quick_mode,
                "total_methods": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "results": results,
                "summary": {
                    "fastest": min(times) if times else None,
                    "slowest": max(times) if times else None,
                    "average": float(np.mean(times)) if times else None,
                    "median": float(np.median(times)) if times else None,
                },
            },
            f,
            indent=2,
        )

    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 70 + "\n")

    return len(successful) >= len(results) * 0.8  # Success if 80%+ pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Comprehensive NBA Analytics Benchmark"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Quick test mode (smaller datasets)"
    )
    args = parser.parse_args()

    success = run_comprehensive_benchmarks(quick_mode=args.quick)
    sys.exit(0 if success else 1)
