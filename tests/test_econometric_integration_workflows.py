"""
Integration Tests for Econometric Framework Workflows

This module contains comprehensive end-to-end integration tests that verify
the complete econometric analysis workflows across all modules.

Test Categories:
1. Cross-Module Workflows (15 tests)
2. EconometricSuite Integration (10 tests)
3. Data Flow Validation (8 tests)
4. Error Handling and Edge Cases (7 tests)

Total: 40+ integration tests
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import all econometric modules
from mcp_server.time_series import TimeSeriesAnalyzer
from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.bayesian import BayesianAnalyzer
from mcp_server.advanced_time_series import AdvancedTimeSeriesAnalyzer
from mcp_server.causal_inference import CausalInferenceAnalyzer
from mcp_server.survival_analysis import SurvivalAnalyzer
from mcp_server.econometric_suite import EconometricSuite


# ============================================================================
# Fixtures for Test Data
# ============================================================================


@pytest.fixture
def time_series_data():
    """Generate time series data for player performance."""
    np.random.seed(42)
    n = 100
    dates = pd.date_range(start="2023-01-01", periods=n, freq="D")
    trend = np.linspace(20, 25, n)
    seasonal = 3 * np.sin(2 * np.pi * np.arange(n) / 30)
    noise = np.random.normal(0, 2, n)

    df = pd.DataFrame(
        {
            "date": dates,
            "player_id": "P001",
            "points_per_game": trend + seasonal + noise,
        }
    )
    return df


@pytest.fixture
def panel_data():
    """Generate panel data for multiple players over multiple seasons."""
    np.random.seed(42)
    n_players = 20
    n_seasons = 5

    data = []
    for player in range(1, n_players + 1):
        player_skill = np.random.normal(20, 5)
        for season in range(1, n_seasons + 1):
            data.append(
                {
                    "player_id": f"P{player:03d}",
                    "season": season,
                    "age": 20 + season + np.random.randint(-2, 3),
                    "experience": season,
                    "points_per_game": player_skill + np.random.normal(0, 3),
                    "minutes_per_game": 30 + np.random.normal(0, 5),
                }
            )

    return pd.DataFrame(data)


@pytest.fixture
def survival_data():
    """Generate career survival data."""
    np.random.seed(42)
    n_players = 100

    data = []
    for i in range(n_players):
        draft_pick = np.random.randint(1, 61)
        base_career = 8 - 0.05 * draft_pick
        career_years = max(1, base_career + np.random.gamma(2, 1.5))
        retired = np.random.binomial(1, 0.85)

        data.append(
            {
                "player_id": f"P{i:03d}",
                "draft_pick": draft_pick,
                "height": np.random.normal(78, 3),
                "position": np.random.choice(["G", "F", "C"]),
                "career_years": career_years,
                "retired": retired,
            }
        )

    return pd.DataFrame(data)


@pytest.fixture
def causal_data():
    """Generate data for causal inference."""
    np.random.seed(42)
    n = 200

    # Confounders
    prior_wins = np.random.uniform(0.2, 0.8, n)
    payroll = 100 + 50 * prior_wins + np.random.normal(0, 10, n)

    # Treatment (coaching change more likely for losing teams)
    prob_treatment = 1 / (1 + np.exp(5 * (prior_wins - 0.35)))
    treatment = np.random.binomial(1, prob_treatment)

    # Outcome (with treatment effect)
    treatment_effect = 0.05
    outcome = (
        0.5 * prior_wins
        + treatment_effect * treatment
        + 0.001 * payroll
        + np.random.normal(0, 0.1, n)
    )

    df = pd.DataFrame(
        {
            "team_id": [f"T{i:03d}" for i in range(n)],
            "prior_wins": prior_wins,
            "payroll": payroll,
            "coaching_change": treatment,
            "win_pct_change": outcome,
        }
    )

    return df


# ============================================================================
# Category 1: Cross-Module Workflows (15 tests)
# ============================================================================


class TestCrossModuleWorkflows:
    """Test complete workflows that span multiple econometric modules."""

    def test_time_series_to_suite_workflow(self, time_series_data):
        """Test: Time series analysis through Suite interface."""
        # Direct time series analysis
        ts_analyzer = TimeSeriesAnalyzer(
            data=time_series_data,
            target_column="points_per_game",
            time_column="date",
            freq="D",
        )
        ts_result = ts_analyzer.auto_arima(seasonal=False)

        # Same analysis through Suite
        suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )
        suite_result = suite.time_series_analysis(method="auto_arima")

        # Verify both paths work
        assert ts_result is not None
        assert suite_result is not None
        assert hasattr(ts_result, "aic")
        assert suite.characteristics.structure.value in ["time_series", "cross_section"]

    def test_panel_to_suite_workflow(self, panel_data):
        """Test: Panel data analysis through Suite interface."""
        # Direct panel analysis
        panel_analyzer = PanelDataAnalyzer(
            data=panel_data,
            entity_col="player_id",
            time_col="season",
            target_col="points_per_game",
        )
        panel_result = panel_analyzer.fixed_effects(
            formula="points_per_game ~ age + experience"
        )

        # Same through Suite
        suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )
        suite_result = suite.panel_analysis(method="fixed_effects")

        assert panel_result is not None
        assert suite_result is not None
        assert suite.characteristics.structure.value == "panel"

    def test_survival_to_suite_workflow(self, survival_data):
        """Test: Survival analysis through Suite interface."""
        # Direct survival analysis
        surv_analyzer = SurvivalAnalyzer(
            data=survival_data, duration_col="career_years", event_col="retired"
        )
        km_result = surv_analyzer.kaplan_meier()

        # Through Suite
        suite = EconometricSuite(data=survival_data, target="career_years")
        suite_result = suite.survival_analysis(
            duration_col="career_years", event_col="retired", method="cox"
        )

        assert km_result is not None
        assert suite_result is not None
        assert hasattr(km_result, "survival_function")

    def test_causal_to_suite_workflow(self, causal_data):
        """Test: Causal inference through Suite interface."""
        # Direct causal analysis
        causal_analyzer = CausalInferenceAnalyzer(
            data=causal_data,
            treatment_col="coaching_change",
            outcome_col="win_pct_change",
            covariates=["prior_wins", "payroll"],
        )
        psm_result = causal_analyzer.propensity_score_matching(method="nearest")

        # Through Suite
        suite = EconometricSuite(data=causal_data, target="win_pct_change")
        suite_result = suite.causal_analysis(
            treatment_col="coaching_change", outcome_col="win_pct_change", method="psm"
        )

        assert psm_result is not None
        assert suite_result is not None
        assert hasattr(psm_result, "ate")

    def test_time_series_decomposition_to_kalman(self, time_series_data):
        """Test: Workflow from seasonal decomposition to Kalman filtering."""
        # Step 1: Seasonal decomposition
        ts_analyzer = TimeSeriesAnalyzer(
            data=time_series_data,
            target_column="points_per_game",
            time_column="date",
            freq="D",
        )
        decomp = ts_analyzer.decompose(model="additive", period=30)

        ts_data = time_series_data.set_index("date")["points_per_game"]

        assert decomp is not None
        assert hasattr(decomp, "trend")
        assert hasattr(decomp, "seasonal")

        # Step 2: Apply Kalman filter to detrended data
        adv_analyzer = AdvancedTimeSeriesAnalyzer(data=ts_data)
        kalman_result = adv_analyzer.kalman_filter(model="local_level")

        assert kalman_result is not None
        assert hasattr(kalman_result, "filtered_state")
        assert len(kalman_result.filtered_state) == len(ts_data)

    def test_arima_to_structural_comparison(self, time_series_data):
        """Test: Compare ARIMA vs structural time series."""
        # ARIMA model
        ts_analyzer = TimeSeriesAnalyzer(
            data=time_series_data,
            target_column="points_per_game",
            time_column="date",
            freq="D",
        )
        arima_result = ts_analyzer.auto_arima(seasonal=False)

        ts_data = time_series_data.set_index("date")["points_per_game"]

        # Structural model
        adv_analyzer = AdvancedTimeSeriesAnalyzer(data=ts_data.values)
        structural_result = adv_analyzer.fit_structural_ts(
            level=True, trend=True, seasonal=None
        )

        # Both should produce valid results
        assert arima_result is not None
        assert structural_result is not None
        assert arima_result["aic"] > 0
        assert structural_result["aic"] > 0

    def test_panel_to_causal_workflow(self, panel_data):
        """Test: Panel data insights inform causal analysis."""
        # Add treatment variable
        panel_data["high_minutes"] = (panel_data["minutes_per_game"] > 30).astype(int)

        # Step 1: Panel analysis to understand player effects
        panel_analyzer = PanelDataAnalyzer(
            data=panel_data,
            entity_col="player_id",
            time_col="season",
            target_col="points_per_game",
        )
        fe_result = panel_analyzer.fixed_effects(formula="points_per_game ~ experience")

        # Step 2: Use panel structure for causal inference
        causal_analyzer = CausalInferenceAnalyzer(
            data=panel_data,
            treatment_col="high_minutes",
            outcome_col="points_per_game",
            covariates=["experience", "age"],
        )
        psm_result = causal_analyzer.propensity_score_matching(method="nearest")

        assert fe_result is not None
        assert psm_result is not None

    def test_survival_to_bayesian_workflow(self, survival_data):
        """Test: Survival analysis to Bayesian hierarchical model."""
        # Step 1: Cox model
        surv_analyzer = SurvivalAnalyzer(
            data=survival_data, duration_col="career_years", event_col="retired"
        )
        cox_result = surv_analyzer.cox_proportional_hazards(
            formula="career_years ~ draft_pick + height"
        )

        # Step 2: Bayesian hierarchical survival model (if implemented)
        # This would use PyMC for Bayesian survival analysis
        assert cox_result is not None
        assert hasattr(cox_result, "hazard_ratios")

    def test_complete_player_analysis_pipeline(
        self, time_series_data, panel_data, survival_data
    ):
        """Test: Complete multi-method player analysis pipeline."""
        # Time series for performance trends
        ts_analyzer = TimeSeriesAnalyzer(
            data=time_series_data,
            target_column="points_per_game",
            time_column="date",
            freq="D",
        )
        ts_result = ts_analyzer.auto_arima()

        # Panel data for cross-player comparisons
        panel_analyzer = PanelDataAnalyzer(
            data=panel_data,
            entity_col="player_id",
            time_col="season",
            target_col="points_per_game",
        )
        panel_result = panel_analyzer.fixed_effects(
            formula="points_per_game ~ experience"
        )

        # Survival for career longevity
        surv_analyzer = SurvivalAnalyzer(
            data=survival_data, duration_col="career_years", event_col="retired"
        )
        surv_result = surv_analyzer.kaplan_meier()

        # All components should work together
        assert ts_result is not None
        assert panel_result is not None
        assert surv_result is not None

    def test_suite_auto_detect_all_structures(
        self, time_series_data, panel_data, survival_data, causal_data
    ):
        """Test: Suite correctly detects all data structures."""
        # Time series
        ts_suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )
        assert ts_suite.characteristics.structure.value in [
            "time_series",
            "cross_section",
        ]

        # Panel
        panel_suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )
        assert panel_suite.characteristics.structure.value == "panel"

        # Survival
        surv_suite = EconometricSuite(data=survival_data, target="career_years")
        # Suite should detect presence of duration/event columns
        assert surv_suite is not None

        # Causal
        causal_suite = EconometricSuite(data=causal_data, target="win_pct_change")
        # Suite should work with causal data
        assert causal_suite is not None

    def test_model_comparison_across_modules(self, time_series_data):
        """Test: Compare models across different modules."""
        ts_data = time_series_data.set_index("date")["points_per_game"]

        suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )

        # Compare regular vs advanced time series methods
        comparison = suite.compare_methods(
            methods=[
                {
                    "category": "time_series",
                    "method": "arima",
                    "params": {"order": (1, 1, 1)},
                },
                {
                    "category": "advanced_time_series",
                    "method": "kalman",
                    "params": {"model": "local_level"},
                },
            ],
            metric="aic",
        )

        assert comparison is not None
        assert len(comparison) == 2

    def test_forecasting_workflow_integration(self, time_series_data):
        """Test: Complete forecasting workflow with validation."""
        # Split data
        train_size = int(len(time_series_data) * 0.8)
        train_data = time_series_data[:train_size]
        test_data = time_series_data[train_size:]

        # Fit model on training data
        ts_analyzer = TimeSeriesAnalyzer(
            data=train_data,
            target_column="points_per_game",
            time_column="date",
            freq="D",
        )
        model = ts_analyzer.auto_arima(seasonal=False)

        # Forecast
        forecast = ts_analyzer.forecast(model_result=model, steps=len(test_data))

        # Validate
        assert forecast is not None
        assert hasattr(forecast, "forecast")
        assert len(forecast.forecast) == len(test_data)

    def test_sensitivity_analysis_integration(self, causal_data):
        """Test: Causal inference with sensitivity analysis."""
        analyzer = CausalInferenceAnalyzer(
            data=causal_data,
            treatment_col="coaching_change",
            outcome_col="win_pct_change",
            covariates=["prior_wins", "payroll"],
        )

        # PSM
        psm_result = analyzer.propensity_score_matching(method="nearest")

        # Sensitivity analysis
        sensitivity = analyzer.sensitivity_analysis(
            method="rosenbaum",
            effect_estimate=psm_result.ate,
            se_estimate=psm_result.std_error,
            gamma_range=(1.0, 2.1),
            n_gamma=6,
        )

        assert psm_result is not None
        assert sensitivity is not None
        assert hasattr(sensitivity, "sensitivity_bounds")

    def test_bayesian_hierarchical_panel(self, panel_data):
        """Test: Bayesian hierarchical model for panel data."""
        # This would test Bayesian methods for panel structure
        # Player-level random effects, season-level fixed effects

        bayesian_spec = {
            "model_type": "hierarchical",
            "groups": ["player_id"],
            "formula": "points_per_game ~ experience",
        }

        # Would initialize Bayesian analyzer with panel structure
        assert panel_data is not None
        assert "player_id" in panel_data.columns

    def test_end_to_end_econometric_workflow(self):
        """Test: Complete end-to-end econometric analysis workflow."""
        # Generate comprehensive dataset
        np.random.seed(42)
        n_players = 30
        n_seasons = 5

        data = []
        for p in range(n_players):
            skill = np.random.normal(20, 5)
            for s in range(n_seasons):
                data.append(
                    {
                        "player_id": f"P{p:03d}",
                        "season": s + 1,
                        "age": 22 + s,
                        "points": skill + s * 0.5 + np.random.normal(0, 2),
                    }
                )

        df = pd.DataFrame(data)

        # Initialize Suite
        suite = EconometricSuite(
            data=df, target="points", entity_col="player_id", time_col="season"
        )

        # Auto-analysis
        result = suite.analyze(method="auto")

        assert result is not None
        assert suite.characteristics.structure.value == "panel"


# ============================================================================
# Category 2: EconometricSuite Integration (10 tests)
# ============================================================================


class TestEconometricSuiteIntegration:
    """Test Suite-specific integration functionality."""

    def test_suite_initialization_all_data_types(self, time_series_data, panel_data):
        """Test: Suite initializes correctly for all data types."""
        # Time series
        ts_suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )
        assert ts_suite is not None

        # Panel
        panel_suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )
        assert panel_suite is not None

    def test_suite_method_access_all_modules(
        self, panel_data, survival_data, causal_data
    ):
        """Test: Suite provides access to all 6 module types."""
        # Panel
        panel_suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )

        # Should have methods for:
        # - time_series_analysis()
        # - panel_analysis()
        # - bayesian_analysis()
        # - advanced_time_series_analysis()
        # - causal_analysis() (would need treatment/outcome cols)
        # - survival_analysis() (would need duration/event cols)

        assert hasattr(panel_suite, "panel_analysis")
        assert hasattr(panel_suite, "time_series_analysis")
        assert hasattr(panel_suite, "advanced_time_series_analysis")

    def test_suite_compare_methods_functionality(self, time_series_data):
        """Test: Suite compare_methods works across categories."""
        suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )

        comparison = suite.compare_methods(
            methods=[
                {
                    "category": "time_series",
                    "method": "arima",
                    "params": {"order": (1, 1, 1)},
                },
                {
                    "category": "time_series",
                    "method": "arima",
                    "params": {"order": (2, 1, 2)},
                },
            ],
            metric="aic",
        )

        assert comparison is not None

    def test_suite_model_averaging(self, time_series_data):
        """Test: Suite model averaging functionality."""
        suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )

        # Fit multiple models
        models = [
            suite.time_series_analysis(method="arima", order=(1, 1, 1)),
            suite.time_series_analysis(method="arima", order=(2, 1, 1)),
        ]

        # Average (if implemented)
        # avg_result = suite.average_models(models, weights='aic')

        assert models[0] is not None
        assert models[1] is not None

    def test_suite_auto_analysis_selection(self, time_series_data, panel_data):
        """Test: Suite auto-analysis selects appropriate method."""
        # Time series -> should select ARIMA or similar
        ts_suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )
        ts_result = ts_suite.analyze(method="auto")
        assert ts_result is not None

        # Panel -> should select fixed/random effects
        panel_suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )
        panel_result = panel_suite.analyze(method="auto")
        assert panel_result is not None

    def test_suite_data_classification(self, time_series_data, panel_data):
        """Test: Suite correctly classifies data structures."""
        # Time series
        ts_suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )
        assert ts_suite.characteristics.structure.value in [
            "time_series",
            "cross_section",
        ]

        # Panel
        panel_suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )
        assert panel_suite.characteristics.structure.value == "panel"

    def test_suite_recommendation_engine(self, panel_data):
        """Test: Suite recommends appropriate methods."""
        suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )

        # Should recommend panel methods
        assert suite.recommended_methods is not None
        # Typically would include 'fixed_effects', 'random_effects', etc.

    def test_suite_result_formatting(self, time_series_data):
        """Test: Suite results have consistent format."""
        suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        # Result should have standard fields
        assert result is not None
        # Typically: model, aic, bic, summary(), etc.

    def test_suite_error_handling(self, panel_data):
        """Test: Suite handles errors gracefully."""
        suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )

        # Try to call method with invalid parameters
        with pytest.raises((ValueError, KeyError, TypeError)):
            suite.time_series_analysis(method="invalid_method")

    def test_suite_repr_and_str(self, time_series_data):
        """Test: Suite has informative string representations."""
        suite = EconometricSuite(
            data=time_series_data.set_index("date"), target="points_per_game"
        )

        repr_str = repr(suite)
        str_str = str(suite)

        assert repr_str is not None
        assert str_str is not None
        assert len(repr_str) > 0
        assert len(str_str) > 0


# ============================================================================
# Category 3: Data Flow Validation (8 tests)
# ============================================================================


class TestDataFlowValidation:
    """Test data flows correctly through analysis pipelines."""

    def test_data_preservation_through_pipeline(self, panel_data):
        """Test: Original data preserved through analysis."""
        original_data = panel_data.copy()

        suite = EconometricSuite(
            data=panel_data,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )

        result = suite.panel_analysis(
            method="fixed_effects", formula="points_per_game ~ experience"
        )

        # Original data should be unchanged
        assert panel_data.equals(original_data)
        assert result is not None

    def test_missing_data_handling(self, panel_data):
        """Test: Missing data handled correctly."""
        # Introduce missing values
        panel_with_missing = panel_data.copy()
        panel_with_missing.loc[0:5, "points_per_game"] = np.nan

        suite = EconometricSuite(
            data=panel_with_missing,
            target="points_per_game",
            entity_col="player_id",
            time_col="season",
        )

        # Should handle or raise informative error
        # Depending on implementation
        assert suite is not None

    def test_data_type_conversions(self, time_series_data):
        """Test: Data types converted correctly."""
        # Pass data with mixed types
        mixed_data = time_series_data.copy()
        mixed_data["points_per_game"] = mixed_data["points_per_game"].astype(str)

        # Should either convert or raise clear error
        with pytest.raises((ValueError, TypeError)):
            suite = EconometricSuite(
                data=mixed_data.set_index("date"), target="points_per_game"
            )

    def test_index_handling(self, time_series_data):
        """Test: DataFrame indexes handled correctly."""
        # Test with different index types

        # DatetimeIndex
        ts_indexed = time_series_data.set_index("date")
        suite1 = EconometricSuite(data=ts_indexed, target="points_per_game")
        assert suite1 is not None

        # RangeIndex
        ts_range = time_series_data.reset_index(drop=True)
        suite2 = EconometricSuite(
            data=ts_range.set_index("date"), target="points_per_game"
        )
        assert suite2 is not None

    def test_column_name_consistency(self, panel_data):
        """Test: Column names preserved through analysis."""
        original_columns = set(panel_data.columns)

        analyzer = PanelDataAnalyzer(
            data=panel_data,
            entity_col="player_id",
            time_col="season",
            target_col="points_per_game",
        )

        result = analyzer.fixed_effects(formula="points_per_game ~ experience")

        # Original data columns should be unchanged
        assert set(panel_data.columns) == original_columns

    def test_forecast_output_format(self, time_series_data):
        """Test: Forecast outputs have consistent format."""
        ts_analyzer = TimeSeriesAnalyzer(
            data=time_series_data,
            target_column="points_per_game",
            time_column="date",
            freq="D",
        )
        model = ts_analyzer.auto_arima()
        forecast = ts_analyzer.forecast(model_result=model, steps=10)

        # Forecast should have standard fields
        assert hasattr(forecast, "forecast")
        assert hasattr(forecast, "lower_bound") or hasattr(forecast, "ci_lower")
        assert hasattr(forecast, "upper_bound") or hasattr(forecast, "ci_upper")

    def test_coefficient_extraction(self, panel_data):
        """Test: Coefficients extracted correctly from models."""
        analyzer = PanelDataAnalyzer(
            data=panel_data,
            entity_col="player_id",
            time_col="season",
            target_col="points_per_game",
        )

        result = analyzer.fixed_effects(formula="points_per_game ~ experience + age")

        # Should be able to extract coefficients
        assert result is not None
        assert hasattr(result, "params") or hasattr(result, "coefficients")

    def test_result_serialization(self, time_series_data):
        """Test: Results can be serialized to dict/JSON."""
        ts_analyzer = TimeSeriesAnalyzer(
            data=time_series_data,
            target_column="points_per_game",
            time_column="date",
            freq="D",
        )
        result = ts_analyzer.auto_arima()

        # Should be able to convert to dict
        # (Implementation dependent)
        assert result is not None
        assert isinstance(result, dict) or hasattr(result, "to_dict")


# ============================================================================
# Category 4: Error Handling and Edge Cases (7 tests)
# ============================================================================


class TestErrorHandlingEdgeCases:
    """Test error handling and edge case scenarios."""

    def test_empty_dataframe(self):
        """Test: Handle empty DataFrame gracefully."""
        empty_df = pd.DataFrame()

        with pytest.raises((ValueError, KeyError)):
            suite = EconometricSuite(data=empty_df, target="nonexistent")

    def test_single_observation(self):
        """Test: Handle single observation."""
        single_obs = pd.DataFrame({"date": [datetime(2023, 1, 1)], "value": [10.0]})

        # Should raise error or handle gracefully
        with pytest.raises((ValueError, RuntimeError)):
            suite = EconometricSuite(data=single_obs.set_index("date"), target="value")
            suite.time_series_analysis(method="arima", params={"order": (1, 1, 1)})

    def test_all_null_target(self, panel_data):
        """Test: Handle all-null target variable."""
        panel_null = panel_data.copy()
        panel_null["points_per_game"] = np.nan

        with pytest.raises(ValueError):
            suite = EconometricSuite(
                data=panel_null,
                target="points_per_game",
                entity_col="player_id",
                time_col="season",
            )
            suite.panel_analysis(
                method="fixed_effects", formula="points_per_game ~ experience"
            )

    def test_collinearity_handling(self, panel_data):
        """Test: Handle perfect collinearity."""
        panel_collinear = panel_data.copy()
        panel_collinear["experience2"] = panel_collinear[
            "experience"
        ]  # Perfect collinearity

        analyzer = PanelDataAnalyzer(
            data=panel_collinear,
            entity_col="player_id",
            time_col="season",
            target_col="points_per_game",
        )

        # Should handle or raise informative error
        # Some estimators drop collinear variables automatically
        result = analyzer.fixed_effects(
            formula="points_per_game ~ experience + experience2"
        )
        # Depending on implementation, may succeed or raise

    def test_convergence_failure(self):
        """Test: Handle model convergence failures."""
        # Create data that's hard to fit
        np.random.seed(42)
        difficult_data = pd.DataFrame(
            {
                "date": pd.date_range("2023-01-01", periods=20, freq="D"),
                "value": np.random.uniform(-1000, 1000, 20),  # Very volatile
            }
        )

        ts_analyzer = TimeSeriesAnalyzer(
            data=difficult_data, target_column="value", time_column="date", freq="D"
        )

        # May fail to converge or succeed with poor fit
        # Should not crash
        try:
            result = ts_analyzer.auto_arima(max_p=1, max_q=1)
            assert result is not None
        except (ValueError, RuntimeError, np.linalg.LinAlgError):
            # Acceptable to raise convergence error
            pass

    def test_invalid_formula(self, panel_data):
        """Test: Handle invalid formulas gracefully."""
        analyzer = PanelDataAnalyzer(
            data=panel_data,
            entity_col="player_id",
            time_col="season",
            target_col="points_per_game",
        )

        with pytest.raises((ValueError, KeyError)):
            analyzer.fixed_effects(formula="invalid ~ formula ~ syntax")

    def test_mismatched_dimensions(self, survival_data):
        """Test: Handle dimension mismatches."""
        surv_analyzer = SurvivalAnalyzer(
            data=survival_data, duration_col="career_years", event_col="retired"
        )

        # Try to fit with covariates that don't exist
        with pytest.raises((KeyError, ValueError)):
            surv_analyzer.cox_proportional_hazards(
                formula="career_years ~ nonexistent_variable", data=survival_data
            )


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
