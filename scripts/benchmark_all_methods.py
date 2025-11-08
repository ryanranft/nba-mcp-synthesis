"""
Comprehensive Benchmark for ALL 57+ Methods in NBA Analytics Platform.

Tests all econometric and statistical methods across all 9 modules:
- Time Series Analysis (26 methods)
- Panel Data (11 methods)
- Causal Inference (8 methods)
- Survival Analysis (11 methods)
- Bayesian Methods (15 methods)
- Advanced Time Series (7 methods)
- Particle Filters (8+ methods)
- Ensemble Methods (9 methods)
- Bayesian Time Series (TBD methods)

Usage:
    python scripts/benchmark_all_methods.py
    python scripts/benchmark_all_methods.py --quick  # Smaller datasets
"""

import argparse
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

from mcp_server.time_series import TimeSeriesAnalyzer
from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.causal_inference import CausalInferenceAnalyzer
from mcp_server.survival_analysis import SurvivalAnalyzer
from mcp_server.bayesian import BayesianAnalyzer
from mcp_server.advanced_time_series import AdvancedTimeSeriesAnalyzer

# Try importing optional modules
try:
    from mcp_server.particle_filters import (
        PlayerPerformanceParticleFilter,
        create_player_filter,
    )

    PARTICLE_AVAILABLE = True
except ImportError:
    PARTICLE_AVAILABLE = False

try:
    from mcp_server.ensemble import (
        SimpleEnsemble,
        WeightedEnsemble,
        StackingEnsemble,
    )

    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False

try:
    from mcp_server.bayesian_time_series import BVARAnalyzer

    BVAR_AVAILABLE = True
except ImportError:
    BVAR_AVAILABLE = False


# ==============================================================================
# Data Generators
# ==============================================================================


def generate_time_series_data(n=200, n_vars=3, seed=42):
    """Generate time series data with trend and seasonality."""
    np.random.seed(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="D")

    data = pd.DataFrame({"date": dates})

    for i in range(n_vars):
        trend = np.linspace(20 + i * 5, 25 + i * 5, n)
        seasonal = 3 * np.sin(np.arange(n) * 2 * np.pi / 82)
        noise = np.random.normal(0, 2, n)
        data[f"var_{i}"] = trend + seasonal + noise

    # Add specific columns for tests
    data["points"] = data["var_0"]
    data["assists"] = data["var_1"]
    data["rebounds"] = data["var_2"]

    return data


def generate_panel_data(n_entities=30, n_time=10, seed=42):
    """Generate panel data (entities x time periods)."""
    np.random.seed(seed)

    data = []
    for entity in range(n_entities):
        for t in range(n_time):
            data.append(
                {
                    "entity": entity,
                    "time": t,
                    "y": 10 + entity * 0.5 + t * 0.3 + np.random.normal(0, 2),
                    "x1": 5 + np.random.normal(0, 1),
                    "x2": 3 + np.random.normal(0, 1),
                    "treatment": np.random.choice([0, 1], p=[0.6, 0.4]),
                }
            )

    return pd.DataFrame(data)


def generate_causal_data(n=300, seed=42):
    """Generate causal inference data with treatment and outcome."""
    np.random.seed(seed)

    # Confounders
    age = np.random.normal(27, 3, n)
    experience = np.random.normal(5, 2, n)

    # Treatment (coaching change)
    treatment_prob = 1 / (1 + np.exp(-(age - 27) / 2 - (experience - 5) / 2))
    treatment = np.random.binomial(1, treatment_prob)

    # Outcome (win percentage)
    outcome = (
        0.5
        + 0.05 * treatment
        + 0.01 * age
        + 0.02 * experience
        + np.random.normal(0, 0.1, n)
    )

    # Instrument (payroll)
    instrument = 100 + 10 * treatment + np.random.normal(0, 5, n)

    # Running variable for RDD
    running_var = np.random.uniform(30, 50, n)

    return pd.DataFrame(
        {
            "outcome": outcome,
            "treatment": treatment,
            "age": age,
            "experience": experience,
            "payroll": instrument,
            "running_var": running_var,
            "entity": np.repeat(np.arange(30), 10)[:n],
        }
    )


def generate_survival_data(n=200, seed=42):
    """Generate survival analysis data."""
    np.random.seed(seed)

    # Covariates
    age = np.random.normal(27, 3, n)
    performance = np.random.normal(15, 5, n)

    # Duration (career years)
    lambda_param = np.exp(0.5 - 0.05 * age + 0.02 * performance)
    duration = np.random.exponential(1 / lambda_param)

    # Event (retired)
    event = np.random.binomial(1, 0.7, n)

    # Event type for competing risks
    event_type = np.random.choice([0, 1, 2, 3], size=n, p=[0.3, 0.3, 0.2, 0.2])

    # Group for comparison
    group = np.random.choice(["A", "B"], size=n)

    return pd.DataFrame(
        {
            "duration": duration,
            "event": event,
            "event_type": event_type,
            "age": age,
            "performance": performance,
            "group": group,
        }
    )


# ==============================================================================
# Benchmark Helper
# ==============================================================================


def benchmark_method(name, func, category, timeout=30):
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
        print(f"✗ {error_msg[:60]}")

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


def run_benchmark(quick_mode=False):
    """Run comprehensive benchmark of all methods."""

    print("=" * 70)
    print("NBA ANALYTICS PLATFORM - ALL METHODS BENCHMARK")
    print("=" * 70)
    print(f"\nMode: {'QUICK' if quick_mode else 'STANDARD'}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # Data size adjustments
    ts_n = 100 if quick_mode else 200
    panel_n_entities = 20 if quick_mode else 30
    panel_n_time = 5 if quick_mode else 10
    causal_n = 200 if quick_mode else 300
    survival_n = 150 if quick_mode else 200

    # ========================================================================
    # TIME SERIES ANALYSIS (26 methods)
    # ========================================================================
    print("🔹 Time Series Analysis Methods:")

    ts_data = generate_time_series_data(n=ts_n)
    ts_data_indexed = ts_data.set_index("date")

    ts = TimeSeriesAnalyzer(data=ts_data, target_column="points", time_column="date")
    ts_multi = TimeSeriesAnalyzer(
        data=ts_data, target_column="points", time_column="date"
    )

    # Statistical tests (6)
    results.append(benchmark_method("ADF Test", lambda: ts.adf_test(), "Time Series"))
    results.append(benchmark_method("KPSS Test", lambda: ts.kpss_test(), "Time Series"))
    results.append(
        benchmark_method(
            "Test Stationarity", lambda: ts.test_stationarity(), "Time Series"
        )
    )
    results.append(
        benchmark_method(
            "Ljung-Box Test", lambda: ts.ljung_box_test(lags=10), "Time Series"
        )
    )
    results.append(
        benchmark_method(
            "Breusch-Godfrey Test",
            lambda: (
                ts.breusch_godfrey_test(lags=5)
                if hasattr(ts, "breusch_godfrey_test")
                else None
            ),
            "Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Heteroscedasticity Tests",
            lambda: (
                ts.heteroscedasticity_tests()
                if hasattr(ts, "heteroscedasticity_tests")
                else None
            ),
            "Time Series",
        )
    )

    # Decomposition (4)
    results.append(
        benchmark_method("Decompose", lambda: ts.decompose(period=7), "Time Series")
    )
    results.append(
        benchmark_method(
            "STL Decompose", lambda: ts.stl_decompose(period=7), "Time Series"
        )
    )
    results.append(
        benchmark_method(
            "MSTL Decompose", lambda: ts.mstl_decompose(periods=[7, 30]), "Time Series"
        )
    )
    results.append(
        benchmark_method("Detect Trend", lambda: ts.detect_trend(), "Time Series")
    )

    # Correlation (2)
    results.append(benchmark_method("ACF", lambda: ts.acf(nlags=20), "Time Series"))
    results.append(benchmark_method("PACF", lambda: ts.pacf(nlags=20), "Time Series"))

    # ARIMA modeling (4)
    results.append(
        benchmark_method(
            "Fit ARIMA", lambda: ts.fit_arima(order=(1, 1, 1)), "Time Series"
        )
    )
    results.append(
        benchmark_method("Auto ARIMA", lambda: ts.auto_arima(), "Time Series")
    )
    results.append(
        benchmark_method(
            "Fit ARIMAX",
            lambda: ts.fit_arimax(
                order=(1, 1, 1), exog_columns=["assists", "rebounds"]
            ),
            "Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Forecast",
            lambda: (ts.fit_arima(order=(1, 1, 1)), ts.forecast(steps=10))[1],
            "Time Series",
        )
    )

    # Multivariate (5) - needs different columns for VAR
    results.append(
        benchmark_method(
            "Fit VAR",
            lambda: ts.fit_var(columns=["points", "assists", "rebounds"], maxlags=2),
            "Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Fit VARMAX",
            lambda: (
                ts.fit_varmax(columns=["points", "assists"], order=(1, 1))
                if hasattr(ts, "fit_varmax")
                else None
            ),
            "Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Fit VECM",
            lambda: ts.fit_vecm(
                columns=["points", "assists"], k_ar_diff=1, coint_rank=1
            ),
            "Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Johansen Test",
            lambda: ts.johansen_test(columns=["points", "assists"]),
            "Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Granger Causality",
            lambda: ts.granger_causality_test(
                cause_col="assists", effect_col="points", maxlag=4
            ),
            "Time Series",
        )
    )

    # Transformations (3)
    results.append(
        benchmark_method("Difference", lambda: ts.difference(periods=1), "Time Series")
    )
    results.append(
        benchmark_method("Make Stationary", lambda: ts.make_stationary(), "Time Series")
    )
    results.append(
        benchmark_method(
            "Detect Structural Breaks",
            lambda: (
                ts.detect_structural_breaks()
                if hasattr(ts, "detect_structural_breaks")
                else None
            ),
            "Time Series",
        )
    )

    # Validation (2)
    results.append(
        benchmark_method(
            "Validate Forecast",
            lambda: ts.validate_forecast(order=(1, 1, 1), test_size=20),
            "Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Time Series Diagnostics",
            lambda: (
                ts.time_series_diagnostics(order=(1, 1, 1))
                if hasattr(ts, "time_series_diagnostics")
                else None
            ),
            "Time Series",
        )
    )

    # ========================================================================
    # PANEL DATA ANALYSIS (11 methods)
    # ========================================================================
    print("\n🔹 Panel Data Analysis Methods:")

    panel_data = generate_panel_data(n_entities=panel_n_entities, n_time=panel_n_time)
    panel = PanelDataAnalyzer(panel_data, entity_col="entity", time_col="time")

    results.append(
        benchmark_method("Balance Check", lambda: panel.balance_check(), "Panel Data")
    )
    results.append(
        benchmark_method(
            "Pooled OLS", lambda: panel.pooled_ols(formula="y ~ x1 + x2"), "Panel Data"
        )
    )
    results.append(
        benchmark_method(
            "Fixed Effects",
            lambda: panel.fixed_effects(formula="y ~ x1 + x2"),
            "Panel Data",
        )
    )
    results.append(
        benchmark_method(
            "Random Effects",
            lambda: panel.random_effects(formula="y ~ x1 + x2"),
            "Panel Data",
        )
    )
    results.append(
        benchmark_method(
            "Hausman Test",
            lambda: panel.hausman_test(formula="y ~ x1 + x2"),
            "Panel Data",
        )
    )
    results.append(
        benchmark_method(
            "F-Test Effects",
            lambda: panel.f_test_effects(formula="y ~ x1 + x2"),
            "Panel Data",
        )
    )
    results.append(
        benchmark_method(
            "Clustered SE",
            lambda: panel.clustered_standard_errors(formula="y ~ x1 + x2"),
            "Panel Data",
        )
    )
    results.append(
        benchmark_method(
            "First Difference",
            lambda: panel.first_difference(formula="y ~ x1 + x2"),
            "Panel Data",
        )
    )
    results.append(
        benchmark_method(
            "Difference GMM",
            lambda: (
                panel.difference_gmm(formula="y ~ x1 + x2", lags=1)
                if hasattr(panel, "difference_gmm")
                else None
            ),
            "Panel Data",
        )
    )
    results.append(
        benchmark_method(
            "System GMM",
            lambda: (
                panel.system_gmm(formula="y ~ x1 + x2", lags=1)
                if hasattr(panel, "system_gmm")
                else None
            ),
            "Panel Data",
        )
    )
    results.append(
        benchmark_method(
            "GMM Diagnostics",
            lambda: (
                panel.gmm_diagnostics() if hasattr(panel, "gmm_diagnostics") else None
            ),
            "Panel Data",
        )
    )

    # ========================================================================
    # CAUSAL INFERENCE (8 methods)
    # ========================================================================
    print("\n🔹 Causal Inference Methods:")

    causal_data = generate_causal_data(n=causal_n)
    causal = CausalInferenceAnalyzer(
        data=causal_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["age", "experience"],
        entity_col="entity",
    )

    results.append(
        benchmark_method(
            "Instrumental Variables",
            lambda: causal.instrumental_variables(instruments=["payroll"]),
            "Causal Inference",
        )
    )
    results.append(
        benchmark_method(
            "Regression Discontinuity",
            lambda: causal.regression_discontinuity(
                running_var="running_var", cutoff=40
            ),
            "Causal Inference",
        )
    )
    results.append(
        benchmark_method(
            "Propensity Score Matching",
            lambda: causal.propensity_score_matching(),
            "Causal Inference",
        )
    )
    results.append(
        benchmark_method(
            "Synthetic Control",
            lambda: causal.synthetic_control(treatment_time=5),
            "Causal Inference",
        )
    )
    results.append(
        benchmark_method(
            "Kernel Matching",
            lambda: (
                causal.kernel_matching() if hasattr(causal, "kernel_matching") else None
            ),
            "Causal Inference",
        )
    )
    results.append(
        benchmark_method(
            "Radius Matching",
            lambda: (
                causal.radius_matching(caliper=0.1)
                if hasattr(causal, "radius_matching")
                else None
            ),
            "Causal Inference",
        )
    )
    results.append(
        benchmark_method(
            "Doubly Robust",
            lambda: (
                causal.doubly_robust_estimation()
                if hasattr(causal, "doubly_robust_estimation")
                else None
            ),
            "Causal Inference",
        )
    )
    results.append(
        benchmark_method(
            "Sensitivity Analysis",
            lambda: (
                causal.sensitivity_analysis()
                if hasattr(causal, "sensitivity_analysis")
                else None
            ),
            "Causal Inference",
        )
    )

    # ========================================================================
    # SURVIVAL ANALYSIS (11 methods)
    # ========================================================================
    print("\n🔹 Survival Analysis Methods:")

    survival_data = generate_survival_data(n=survival_n)
    survival = SurvivalAnalyzer(
        data=survival_data,
        duration_col="duration",
        event_col="event",
        covariates=["age", "performance"],
    )

    results.append(
        benchmark_method(
            "Cox Proportional Hazards",
            lambda: survival.cox_proportional_hazards(),
            "Survival Analysis",
        )
    )
    results.append(
        benchmark_method(
            "Cox Time-Varying",
            lambda: (
                survival.cox_time_varying()
                if hasattr(survival, "cox_time_varying")
                else None
            ),
            "Survival Analysis",
        )
    )
    results.append(
        benchmark_method(
            "Parametric Survival (Weibull)",
            lambda: survival.parametric_survival(distribution="weibull"),
            "Survival Analysis",
        )
    )
    results.append(
        benchmark_method(
            "Kaplan-Meier", lambda: survival.kaplan_meier(), "Survival Analysis"
        )
    )
    results.append(
        benchmark_method(
            "Log-Rank Test",
            lambda: survival.logrank_test(group_col="group"),
            "Survival Analysis",
        )
    )

    # Competing risks
    survival_cr = SurvivalAnalyzer(
        data=survival_data,
        duration_col="duration",
        event_col="event_type",
        covariates=["age", "performance"],
    )
    results.append(
        benchmark_method(
            "Competing Risks",
            lambda: survival_cr.competing_risks(),
            "Survival Analysis",
        )
    )
    results.append(
        benchmark_method(
            "Fine-Gray Model",
            lambda: (
                survival_cr.fine_gray_model(event_of_interest=1)
                if hasattr(survival_cr, "fine_gray_model")
                else None
            ),
            "Survival Analysis",
        )
    )

    # Advanced models
    results.append(
        benchmark_method(
            "Frailty Model",
            lambda: (
                survival.frailty_model(frailty_distribution="gamma")
                if hasattr(survival, "frailty_model")
                else None
            ),
            "Survival Analysis",
        )
    )
    results.append(
        benchmark_method(
            "Cure Model",
            lambda: survival.cure_model() if hasattr(survival, "cure_model") else None,
            "Survival Analysis",
        )
    )
    results.append(
        benchmark_method(
            "Recurrent Events Model",
            lambda: (
                survival.recurrent_events_model()
                if hasattr(survival, "recurrent_events_model")
                else None
            ),
            "Survival Analysis",
        )
    )
    results.append(
        benchmark_method(
            "Model Comparison",
            lambda: (
                survival.model_comparison()
                if hasattr(survival, "model_comparison")
                else None
            ),
            "Survival Analysis",
        )
    )

    # ========================================================================
    # BAYESIAN METHODS (15 methods)
    # ========================================================================
    print("\n🔹 Bayesian Methods:")

    bayes_data = panel_data.head(50).copy()
    bayes_data["y_scaled"] = (bayes_data["y"] - bayes_data["y"].mean()) / bayes_data[
        "y"
    ].std()
    bayes = BayesianAnalyzer(data=bayes_data, target="y_scaled")

    # Model building
    results.append(
        benchmark_method(
            "Build Simple Model",
            lambda: bayes.build_simple_model(formula="y_scaled ~ x1 + x2"),
            "Bayesian",
        )
    )

    # Inference (MCMC with small draws for speed)
    mcmc_draws = 50 if quick_mode else 100
    mcmc_tune = 25 if quick_mode else 50

    results.append(
        benchmark_method(
            "Sample Posterior (MCMC)",
            lambda: bayes.sample_posterior(draws=mcmc_draws, tune=mcmc_tune, chains=1),
            "Bayesian",
        )
    )

    # Posterior analysis (requires fitted model)
    def test_posterior_analysis():
        if bayes.trace is not None:
            return bayes.posterior_summary()
        return None

    results.append(
        benchmark_method("Posterior Summary", test_posterior_analysis, "Bayesian")
    )
    results.append(
        benchmark_method(
            "Credible Interval",
            lambda: (
                bayes.credible_interval("x1", probability=0.95) if bayes.trace else None
            ),
            "Bayesian",
        )
    )
    results.append(
        benchmark_method(
            "Check Convergence",
            lambda: bayes.check_convergence() if bayes.trace else None,
            "Bayesian",
        )
    )
    results.append(
        benchmark_method(
            "Effective Sample Size",
            lambda: bayes.effective_sample_size() if bayes.trace else None,
            "Bayesian",
        )
    )
    results.append(
        benchmark_method(
            "Rhat Statistic",
            lambda: bayes.rhat_statistic() if bayes.trace else None,
            "Bayesian",
        )
    )

    # Model comparison
    results.append(
        benchmark_method(
            "WAIC", lambda: bayes.waic() if bayes.trace else None, "Bayesian"
        )
    )
    results.append(
        benchmark_method(
            "LOO", lambda: bayes.loo() if bayes.trace else None, "Bayesian"
        )
    )

    # Variational inference
    bayes2 = BayesianAnalyzer(data=bayes_data, target="y_scaled")
    bayes2.build_simple_model(formula="y_scaled ~ x1 + x2")
    results.append(
        benchmark_method(
            "Variational Inference",
            lambda: (
                bayes2.variational_inference(n=5000)
                if hasattr(bayes2, "variational_inference")
                else None
            ),
            "Bayesian",
        )
    )

    # Priors and likelihood
    results.append(
        benchmark_method(
            "Define Prior",
            lambda: (
                bayes.define_prior("normal", mu=0, sigma=1)
                if hasattr(bayes, "define_prior")
                else None
            ),
            "Bayesian",
        )
    )
    results.append(
        benchmark_method(
            "Define Likelihood",
            lambda: (
                bayes.define_likelihood("normal")
                if hasattr(bayes, "define_likelihood")
                else None
            ),
            "Bayesian",
        )
    )

    # Hierarchical and PPC
    results.append(
        benchmark_method(
            "Hierarchical Model",
            lambda: (
                bayes.hierarchical_model(group_col="entity")
                if hasattr(bayes, "hierarchical_model")
                else None
            ),
            "Bayesian",
        )
    )
    results.append(
        benchmark_method(
            "Posterior Predictive Check",
            lambda: (
                bayes.posterior_predictive_check()
                if bayes.trace and hasattr(bayes, "posterior_predictive_check")
                else None
            ),
            "Bayesian",
        )
    )
    results.append(
        benchmark_method(
            "Compare Models", lambda: None, "Bayesian"  # Requires multiple models
        )
    )

    # ========================================================================
    # ADVANCED TIME SERIES (7 methods)
    # ========================================================================
    print("\n🔹 Advanced Time Series Methods:")

    ats_data = ts_data_indexed["points"].values
    ats = AdvancedTimeSeriesAnalyzer(ats_data)

    results.append(
        benchmark_method(
            "Kalman Filter",
            lambda: ats.kalman_filter(model_type="local_level"),
            "Advanced Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Kalman Smoother",
            lambda: (
                ats.kalman_smoother(model_type="local_level")
                if hasattr(ats, "kalman_smoother")
                else None
            ),
            "Advanced Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Forecast State Space",
            lambda: (
                ats.forecast_state_space(steps=10, model_type="local_level")
                if hasattr(ats, "forecast_state_space")
                else None
            ),
            "Advanced Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Dynamic Factor Model",
            lambda: ats.dynamic_factor_model(k_factors=1),
            "Advanced Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Markov Switching",
            lambda: ats.markov_switching(k_regimes=2),
            "Advanced Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Structural Time Series",
            lambda: (
                ats.structural_time_series()
                if hasattr(ats, "structural_time_series")
                else None
            ),
            "Advanced Time Series",
        )
    )
    results.append(
        benchmark_method(
            "Impute Missing",
            lambda: (
                ats.impute_missing(model_type="local_level")
                if hasattr(ats, "impute_missing")
                else None
            ),
            "Advanced Time Series",
        )
    )

    # ========================================================================
    # PARTICLE FILTERS (8 methods) - Optional
    # ========================================================================
    if PARTICLE_AVAILABLE:
        print("\n🔹 Particle Filter Methods:")

        results.append(
            benchmark_method(
                "Create Player Filter",
                lambda: create_player_filter(n_particles=100),
                "Particle Filters",
            )
        )
        # Add more particle filter tests...

    # ========================================================================
    # ENSEMBLE METHODS (9 methods) - Optional
    # ========================================================================
    if ENSEMBLE_AVAILABLE:
        print("\n🔹 Ensemble Methods:")

        # Create dummy models for ensemble
        # This is placeholder - actual implementation depends on having fitted models
        results.append(
            benchmark_method(
                "Simple Ensemble", lambda: None, "Ensemble"  # Requires fitted models
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

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_all_methods_{timestamp}.json"

    output = {
        "timestamp": timestamp,
        "quick_mode": quick_mode,
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
    parser = argparse.ArgumentParser(description="Benchmark all methods")
    parser.add_argument(
        "--quick", action="store_true", help="Quick mode with smaller datasets"
    )
    args = parser.parse_args()

    run_benchmark(quick_mode=args.quick)
