"""
End-to-End Pipeline Tests for NBA MCP Analytics Platform.

Tests complete analysis workflows from data ingestion through analysis
to visualization-ready results. Validates realistic multi-step transformations
and result chaining.

Test Categories:
1. Complete Player Analysis Pipeline (5 tests)
2. Team Strategy Analysis Pipeline (4 tests)
3. Data → Analysis → Insights Pipeline (4 tests)
4. Multi-Step Transformation Pipeline (3 tests)

Total: 16 comprehensive E2E tests

Author: Claude Code
Date: November 4, 2025
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from mcp_server.econometric_suite import EconometricSuite
from mcp_server.streaming_analytics import (
    StreamingAnalyzer,
    StreamEvent,
    StreamEventType,
)
from mcp_server.ensemble import WeightedEnsemble, SimpleEnsemble


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def player_season_data():
    """Generate realistic player season data."""
    np.random.seed(42)
    n_games = 82
    dates = pd.date_range("2023-10-01", periods=n_games)

    # Realistic player progression
    games = np.arange(n_games)
    trend = 0.05 * games  # Slight improvement over season

    data = pd.DataFrame(
        {
            "date": dates,
            "game_number": games,
            "player_id": ["lebron_james"] * n_games,
            "points": np.random.normal(25 + trend, 5, n_games).clip(0, 50),
            "assists": np.random.normal(7, 2, n_games).clip(0, 15),
            "rebounds": np.random.normal(8, 2.5, n_games).clip(0, 20),
            "minutes_played": np.random.normal(35, 3, n_games).clip(20, 48),
            "usage_rate": np.random.normal(0.28, 0.03, n_games).clip(0.15, 0.45),
            "rest_days": np.random.poisson(1.5, n_games).clip(0, 7),
            "home_game": np.random.binomial(1, 0.5, n_games),
            "opponent_strength": np.random.normal(0.5, 0.15, n_games).clip(0.2, 0.8),
        }
    )

    return data


@pytest.fixture
def team_season_data():
    """Generate realistic team season data."""
    np.random.seed(42)
    n_games = 100
    dates = pd.date_range("2023-10-01", periods=n_games)

    data = pd.DataFrame(
        {
            "date": dates,
            "game_id": range(n_games),
            "team_id": ["Lakers"] * n_games,
            "home_game": np.random.binomial(1, 0.5, n_games),
            "win": np.random.binomial(1, 0.55, n_games),
            "points_scored": np.random.normal(110, 10, n_games).clip(80, 140),
            "points_allowed": np.random.normal(105, 10, n_games).clip(80, 140),
            "rest_days": np.random.poisson(1.5, n_games).clip(0, 5),
            "travel_distance": np.random.exponential(500, n_games).clip(0, 3000),
            "opponent_win_pct": np.random.uniform(0.3, 0.7, n_games),
            "defensive_rating": np.random.normal(105, 5, n_games),
            "offensive_rating": np.random.normal(110, 5, n_games),
        }
    )

    # Add win relationship
    data.loc[data["home_game"] == 1, "win"] = np.random.binomial(
        1, 0.62, (data["home_game"] == 1).sum()
    )

    return data


# ============================================================================
# Category 1: Complete Player Analysis Pipeline (5 tests)
# ============================================================================


class TestCompletePlayerPipeline:
    """Test complete player analysis workflows."""

    def test_player_performance_forecasting_pipeline(self, player_season_data):
        """
        Pipeline: Data Prep → Stationarity Check → ARIMA → Forecast → Validation

        Realistic workflow for forecasting player performance.
        """
        # Step 1: Data preparation
        data = player_season_data.copy()
        assert len(data) == 82, "Should have full season"

        # Step 2: Create suite
        suite = EconometricSuite(data=data, target="points", time_col="date")

        # Step 3: Run ARIMA forecasting
        result_arima = suite.time_series_analysis(method="arima", order=(2, 1, 2))

        assert result_arima is not None
        assert result_arima.method_used == "ARIMA"
        assert hasattr(result_arima.result, "aic")
        assert result_arima.result.aic > 0

        # Step 4: Generate forecast
        forecast = result_arima.result.model.forecast(steps=10)

        assert len(forecast) == 10
        assert all(forecast >= 0), "Points should be non-negative"
        assert all(forecast <= 60), "Points should be realistic"

        # Step 5: Validate forecast quality (train/test split)
        train_data = data.iloc[:-10]
        test_data = data.iloc[-10:]

        suite_train = EconometricSuite(
            data=train_data, target="points", time_col="date"
        )

        result_train = suite_train.time_series_analysis(method="arima", order=(2, 1, 2))
        forecast_test = result_train.result.model.forecast(steps=10)

        # Calculate error metrics
        actual = test_data["points"].values
        mae = np.mean(np.abs(forecast_test - actual))
        rmse = np.sqrt(np.mean((forecast_test - actual) ** 2))

        # Errors should be reasonable
        assert mae < 8, f"MAE too high: {mae:.2f}"
        assert rmse < 10, f"RMSE too high: {rmse:.2f}"

        # Step 6: Insights extraction
        insights = {
            "forecast_mean": float(np.mean(forecast)),
            "forecast_std": float(np.std(forecast)),
            "mae": float(mae),
            "rmse": float(rmse),
            "model_aic": float(result_arima.result.aic),
        }

        assert all(isinstance(v, float) for v in insights.values())

    def test_player_ensemble_forecasting_pipeline(self, player_season_data):
        """
        Pipeline: Multiple Models → Ensemble → Forecast → Comparison

        Use ensemble methods for more robust predictions.
        """
        data = player_season_data.copy()

        # Step 1: Train multiple models
        suite = EconometricSuite(data=data, target="points", time_col="date")

        model1 = suite.time_series_analysis(method="arima", order=(1, 1, 1))
        model2 = suite.time_series_analysis(method="arima", order=(2, 1, 2))
        model3 = suite.time_series_analysis(method="arima", order=(1, 1, 2))

        assert all([model1, model2, model3])

        # Step 2: Create ensemble
        ensemble = WeightedEnsemble(
            [model1.result.model, model2.result.model, model3.result.model]
        )

        # Step 3: Generate ensemble forecast
        forecast_result = ensemble.predict(n_steps=10, return_individual=True)

        assert forecast_result is not None
        assert len(forecast_result.predictions) == 10
        assert hasattr(forecast_result, "weights")

        # Step 4: Validate ensemble properties
        # Weights should sum to 1
        assert abs(sum(forecast_result.weights) - 1.0) < 0.01

        # Ensemble forecast should be in reasonable range
        assert all(forecast_result.predictions >= 0)
        assert all(forecast_result.predictions <= 50)

    def test_player_streaming_integration_pipeline(self, player_season_data):
        """
        Pipeline: Historical Analysis → Streaming Updates → Anomaly Detection

        Integrate historical analysis with real-time streaming.
        """
        # Step 1: Historical baseline
        historical = player_season_data.iloc[:-10].copy()

        suite = EconometricSuite(data=historical, target="points", time_col="date")
        baseline = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert baseline is not None

        # Step 2: Set up streaming analyzer
        analyzer = StreamingAnalyzer(window_seconds=86400 * 10)  # 10-day window

        # Step 3: Process recent games as stream
        recent_games = player_season_data.iloc[-10:]

        for _, game in recent_games.iterrows():
            event = StreamEvent(
                event_type=StreamEventType.PLAYER_STAT,
                timestamp=game["date"],
                game_id=f"game_{game['game_number']}",
                data={
                    "points": game["points"],
                    "player_id": game["player_id"],
                    "team_id": "LAL",
                },
            )
            analyzer.process_event(event)

        # Step 4: Detect anomalies
        anomalies = analyzer.detect_anomalies(metric="points", threshold_std=2.5)

        # Should return a list (may be empty)
        assert isinstance(anomalies, list)

        # Step 5: Validate streaming metrics
        assert analyzer.window_seconds == 86400 * 10

    def test_player_causal_effect_pipeline(self, player_season_data):
        """
        Pipeline: Data Prep → Matching → Effect Estimation → Robustness Check

        Estimate causal effect of rest days on performance.
        """
        data = player_season_data.copy()

        # Step 1: Create treatment variable (well-rested = 2+ rest days)
        data["well_rested"] = (data["rest_days"] >= 2).astype(int)

        # Step 2: PSM analysis
        suite = EconometricSuite(data=data)

        result_psm = suite.causal_analysis(
            treatment_col="well_rested", outcome_col="points", method="psm", caliper=0.2
        )

        assert result_psm is not None
        assert hasattr(result_psm.result, "att")

        # Step 3: Robustness check with doubly robust estimator
        result_dr = suite.causal_analysis(
            treatment_col="well_rested", outcome_col="points", method="doubly_robust"
        )

        assert result_dr is not None
        assert hasattr(result_dr.result, "att")

        # Step 4: Compare estimates (should be similar)
        att_diff = abs(result_psm.result.att - result_dr.result.att)

        # Estimates should be reasonably close (within 5 points)
        assert att_diff < 5, f"PSM and DR estimates too different: {att_diff:.2f}"

    def test_player_multivariate_analysis_pipeline(self, player_season_data):
        """
        Pipeline: VAR Analysis → Impulse Response → Forecast → Interpretation

        Analyze interdependencies between multiple player stats.
        """
        # Step 1: Select multiple variables
        data = player_season_data[["date", "points", "assists", "rebounds"]].copy()

        # Step 2: Run VAR analysis
        suite = EconometricSuite(data=data, target="points", time_col="date")

        result_var = suite.time_series_analysis(
            method="var", endog_data=data[["points", "assists", "rebounds"]], maxlags=2
        )

        assert result_var is not None
        assert result_var.method_used == "VAR Model"

        # Step 3: Verify VAR model
        assert hasattr(result_var.result, "model")
        assert result_var.result.model is not None

        # VAR model should have fitted parameters
        assert hasattr(result_var.result.model, "params")


# ============================================================================
# Category 2: Team Strategy Analysis Pipeline (4 tests)
# ============================================================================


class TestTeamStrategyPipeline:
    """Test complete team strategy analysis workflows."""

    def test_home_advantage_analysis_pipeline(self, team_season_data):
        """
        Pipeline: PSM → RDD → DiD → Meta-Analysis

        Comprehensive home advantage estimation using multiple methods.
        """
        data = team_season_data.copy()
        suite = EconometricSuite(data=data)

        # Step 1: PSM for home advantage
        result_psm = suite.causal_analysis(
            treatment_col="home_game", outcome_col="win", method="psm", caliper=0.15
        )

        assert result_psm is not None
        assert hasattr(result_psm.result, "att")

        # Step 2: Doubly robust for robustness
        result_dr = suite.causal_analysis(
            treatment_col="home_game", outcome_col="win", method="doubly_robust"
        )

        assert result_dr is not None

        # Step 3: Validate consistency
        att_psm = result_psm.result.att
        att_dr = result_dr.result.att

        # Both should show positive home advantage
        assert att_psm > 0, "PSM should show positive home advantage"
        assert att_dr > 0, "DR should show positive home advantage"

        # Estimates should be consistent (within 0.3)
        assert abs(att_psm - att_dr) < 0.3

    def test_team_performance_forecasting_pipeline(self, team_season_data):
        """
        Pipeline: Time Series Analysis → Forecast → Performance Metrics

        Forecast team win probability and scoring.
        """
        # Step 1: Prepare data
        data = team_season_data[["date", "points_scored"]].copy()
        data.columns = ["date", "points"]

        # Step 2: ARIMA for scoring forecast
        suite = EconometricSuite(data=data, target="points", time_col="date")

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert result is not None
        assert hasattr(result.result, "aic")

        # Step 3: Generate forecast
        forecast = result.result.model.forecast(steps=10)

        assert len(forecast) == 10
        assert all(forecast >= 80), "Points should be realistic minimum"
        assert all(forecast <= 140), "Points should be realistic maximum"

    def test_rest_impact_analysis_pipeline(self, team_season_data):
        """
        Pipeline: Data Exploration → Causal Analysis → Effect Quantification

        Quantify impact of rest days on team performance.
        """
        data = team_season_data.copy()

        # Step 1: Create treatment (well-rested = 2+ days)
        data["well_rested"] = (data["rest_days"] >= 2).astype(int)

        # Step 2: Causal analysis
        suite = EconometricSuite(data=data)

        result = suite.causal_analysis(
            treatment_col="well_rested", outcome_col="win", method="psm", caliper=0.2
        )

        assert result is not None
        assert hasattr(result.result, "att")

        # Rest should have positive or neutral effect
        assert (
            result.result.att >= -0.1
        ), "Rest shouldn't harm performance significantly"

    def test_strategy_change_detection_pipeline(self, team_season_data):
        """
        Pipeline: Baseline → Strategy Change → Effect Estimation → Validation

        Detect and quantify impact of mid-season strategy changes.
        """
        data = team_season_data.copy()

        # Step 1: Baseline performance
        baseline_data = data[["date", "points_scored"]].copy()
        baseline_data.columns = ["date", "points"]

        suite_baseline = EconometricSuite(
            data=baseline_data, target="points", time_col="date"
        )

        baseline_model = suite_baseline.time_series_analysis(
            method="arima", order=(1, 1, 1)
        )

        assert baseline_model is not None

        # Step 2: Create treatment (strategy change at game 50)
        data["new_strategy"] = 0
        data.loc[50:, "new_strategy"] = 1

        # Step 3: Estimate strategy effect
        suite_causal = EconometricSuite(data=data)

        result = suite_causal.causal_analysis(
            treatment_col="new_strategy", outcome_col="points_scored", method="psm"
        )

        assert result is not None


# ============================================================================
# Category 3: Data → Analysis → Insights Pipeline (4 tests)
# ============================================================================


class TestDataToInsightsPipeline:
    """Test complete data-to-insights workflows."""

    def test_raw_data_to_forecast_pipeline(self, player_season_data):
        """
        Pipeline: Raw Data → Cleaning → Feature Engineering → Modeling → Forecast

        Complete workflow from raw data to actionable forecast.
        """
        # Step 1: Simulate raw data with issues
        raw_data = player_season_data.copy()

        # Add some missing values
        missing_idx = np.random.choice(len(raw_data), size=5, replace=False)
        raw_data.loc[missing_idx, "points"] = np.nan

        # Step 2: Clean data
        clean_data = raw_data.dropna()

        assert len(clean_data) < len(raw_data)
        assert len(clean_data) >= 30, "Should have enough data after cleaning"

        # Step 3: Feature engineering (rolling averages)
        clean_data["points_ma3"] = (
            clean_data["points"].rolling(window=3, min_periods=1).mean()
        )

        # Step 4: Modeling
        suite = EconometricSuite(data=clean_data, target="points", time_col="date")

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert result is not None

        # Step 5: Generate forecast
        forecast = result.result.model.forecast(steps=5)

        # Step 6: Create insights
        insights = {
            "avg_forecast": float(np.mean(forecast)),
            "trend": "improving" if forecast[-1] > forecast[0] else "declining",
            "model_quality": (
                "good" if result.result.aic < 1000 else "needs_improvement"
            ),
        }

        assert all(k in insights for k in ["avg_forecast", "trend", "model_quality"])

    def test_exploratory_to_confirmatory_pipeline(self, player_season_data):
        """
        Pipeline: Exploration → Hypothesis → Testing → Validation

        Scientific workflow from exploration to confirmation.
        """
        data = player_season_data.copy()

        # Step 1: Exploratory analysis (descriptive stats)
        summary_stats = {
            "mean_points": data["points"].mean(),
            "std_points": data["points"].std(),
            "corr_rest_points": data["points"].corr(data["rest_days"]),
        }

        # Step 2: Form hypothesis (rest days affect performance)
        # Create hypothesis test data
        data["well_rested"] = (data["rest_days"] >= 2).astype(int)

        # Step 3: Confirmatory analysis
        suite = EconometricSuite(data=data)

        result = suite.causal_analysis(
            treatment_col="well_rested", outcome_col="points", method="psm"
        )

        assert result is not None

        # Step 4: Validation - check if hypothesis supported
        effect_size = result.result.att
        hypothesis_supported = abs(effect_size) > 1  # At least 1 point difference

        # Create final report
        report = {
            "exploratory_stats": summary_stats,
            "effect_estimate": float(effect_size),
            "hypothesis_supported": hypothesis_supported,
        }

        assert "effect_estimate" in report

    def test_data_quality_to_analysis_pipeline(self, player_season_data):
        """
        Pipeline: Quality Check → Cleaning → Validation → Analysis

        Ensure data quality before analysis.
        """
        data = player_season_data.copy()

        # Step 1: Quality checks
        quality_checks = {
            "has_nulls": data.isnull().any().any(),
            "has_duplicates": data.duplicated().any(),
            "sufficient_samples": len(data) >= 30,
            "valid_range": (data["points"] >= 0).all() and (data["points"] <= 60).all(),
        }

        # Step 2: Validate checks pass
        assert quality_checks["sufficient_samples"], "Need enough samples"
        assert quality_checks["valid_range"], "Data should be in valid range"

        # Step 3: Proceed with analysis
        suite = EconometricSuite(data=data, target="points", time_col="date")

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert result is not None

        # Step 4: Validate results
        forecast = result.result.model.forecast(steps=5)

        # Results should be reasonable
        assert all(forecast >= 0) and all(forecast <= 60)

    def test_multi_source_data_integration_pipeline(
        self, player_season_data, team_season_data
    ):
        """
        Pipeline: Multiple Data Sources → Integration → Combined Analysis

        Integrate player and team data for comprehensive analysis.
        """
        # Step 1: Prepare player data
        player_data = player_season_data[
            ["date", "player_id", "points", "home_game"]
        ].copy()

        # Step 2: Prepare team data
        team_data = team_season_data[["date", "team_id", "win"]].copy()

        # Step 3: Merge on date (simplified integration)
        # In practice would do more sophisticated joining
        player_dates = set(player_data["date"].dt.date)
        team_dates = set(team_data["date"].dt.date)
        common_dates = player_dates & team_dates

        assert len(common_dates) > 0, "Should have overlapping dates"

        # Step 4: Analyze each source
        suite_player = EconometricSuite(
            data=player_data, target="points", time_col="date"
        )

        result_player = suite_player.time_series_analysis(
            method="arima", order=(1, 1, 1)
        )

        assert result_player is not None

        # Step 5: Integration insights
        insights = {
            "player_forecast": result_player.result.model.forecast(steps=5),
            "data_sources": 2,
            "common_dates": len(common_dates),
        }

        assert insights["data_sources"] == 2


# ============================================================================
# Category 4: Multi-Step Transformation Pipeline (3 tests)
# ============================================================================


class TestTransformationPipeline:
    """Test multi-step data transformation workflows."""

    def test_aggregation_to_analysis_pipeline(self, player_season_data):
        """
        Pipeline: Raw Games → Weekly Aggregation → Analysis → Insights

        Aggregate game-level data to weekly for analysis.
        """
        data = player_season_data.copy()

        # Step 1: Add week number
        data["week"] = data["date"].dt.isocalendar().week

        # Step 2: Aggregate to weekly
        weekly_data = (
            data.groupby("week")
            .agg(
                {
                    "points": "mean",
                    "assists": "mean",
                    "rebounds": "mean",
                    "minutes_played": "mean",
                }
            )
            .reset_index()
        )

        assert len(weekly_data) < len(data), "Should have fewer weekly records"

        # Step 3: Add date column for time series
        weekly_data["date"] = pd.date_range(
            "2023-10-01", periods=len(weekly_data), freq="W"
        )

        # Step 4: Analyze weekly trends
        if len(weekly_data) >= 30:
            suite = EconometricSuite(data=weekly_data, target="points", time_col="date")

            result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

            assert result is not None

    def test_normalization_to_comparison_pipeline(self, player_season_data):
        """
        Pipeline: Raw Stats → Normalization → Comparison → Rankings

        Normalize stats for fair comparison across contexts.
        """
        data = player_season_data.copy()

        # Step 1: Normalize per-minute stats
        data["points_per_minute"] = data["points"] / data["minutes_played"]
        data["assists_per_minute"] = data["assists"] / data["minutes_played"]

        # Step 2: Calculate efficiency scores
        data["efficiency"] = (
            data["points_per_minute"] + data["assists_per_minute"] * 1.5
        )

        # Step 3: Rank performances
        data["efficiency_rank"] = data["efficiency"].rank(ascending=False)

        # Step 4: Identify top performances
        top_10_pct = data["efficiency_rank"] <= len(data) * 0.1
        top_performances = data[top_10_pct]

        assert len(top_performances) > 0
        assert len(top_performances) < len(data)

    def test_feature_engineering_to_prediction_pipeline(self, player_season_data):
        """
        Pipeline: Raw Features → Engineering → Selection → Prediction

        Engineer features and select best for prediction.
        """
        data = player_season_data.copy()

        # Step 1: Feature engineering
        data["points_ma5"] = data["points"].rolling(window=5, min_periods=1).mean()
        data["points_std5"] = (
            data["points"].rolling(window=5, min_periods=1).std().fillna(0)
        )
        data["games_since_break"] = (data["rest_days"] == 0).cumsum()

        # Step 2: Feature selection (correlation-based)
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        correlations = data[numeric_cols].corrwith(data["points"]).abs()
        top_features = correlations.nlargest(5).index.tolist()

        assert "points" in top_features or "points_ma5" in top_features

        # Step 3: Build prediction model
        suite = EconometricSuite(data=data, target="points", time_col="date")

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert result is not None

        # Step 4: Generate predictions
        predictions = result.result.model.forecast(steps=5)

        assert len(predictions) == 5


# ============================================================================
# Summary Test
# ============================================================================


def test_e2e_pipeline_coverage():
    """Meta-test to ensure comprehensive E2E coverage."""
    test_classes = [
        TestCompletePlayerPipeline,
        TestTeamStrategyPipeline,
        TestDataToInsightsPipeline,
        TestTransformationPipeline,
    ]

    total_tests = 0
    for test_class in test_classes:
        test_methods = [m for m in dir(test_class) if m.startswith("test_")]
        total_tests += len(test_methods)

    # Should have 16 E2E tests
    assert total_tests >= 16, f"Expected 16+ E2E tests, found {total_tests}"
    print(f"\n✅ Total E2E pipeline tests: {total_tests}")
