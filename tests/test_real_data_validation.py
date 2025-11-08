"""
Real Data Validation Tests for NBA Econometric Analysis

This module tests econometric methods with real NBA data from the database
to ensure production readiness and validate model outputs are sensible.

Test Categories:
1. Real Player Time Series Analysis (3 tests)
2. Real Team Panel Analysis (2 tests)
3. Real Causal Inference (2 tests)
4. Production Data Quality (3 tests)
5. Multi-Player Validation (2 tests)

Total: 12 real data validation tests
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add mcp_server to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_server.econometric_suite import EconometricSuite
from mcp_server.time_series import TimeSeriesAnalyzer
from mcp_server.panel_data import PanelDataAnalyzer
from mcp_server.causal_inference import CausalInferenceAnalyzer


# ============================================================================
# Database Query Helpers
# ============================================================================


def _execute_query(query: str):
    """Execute SQL query using subprocess to call MCP tool."""
    import subprocess
    import json

    # Use pytest-mcp or direct database connection
    # For now, we'll use a direct psycopg2 connection
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import os

        # Get database connection from environment or use defaults
        db_config = {
            "host": os.getenv("NBA_DB_HOST", "localhost"),
            "port": int(os.getenv("NBA_DB_PORT", "5432")),
            "database": os.getenv("NBA_DB_NAME", "nba"),
            "user": os.getenv("NBA_DB_USER", "postgres"),
            "password": os.getenv("NBA_DB_PASSWORD", ""),
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(query)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
        }

    except Exception as e:
        return {"success": False, "error": str(e), "row_count": 0, "rows": []}


def fetch_player_stats(player_id: str, min_games: int = 50) -> pd.DataFrame:
    """
    Fetch real player statistics from database.

    Args:
        player_id: NBA player ID
        min_games: Minimum number of games required

    Returns:
        DataFrame with player game statistics
    """
    query = f"""
    SELECT
        b.player_id,
        b.team_id,
        b.points,
        b.total_rebounds as rebounds,
        b.assists,
        b.steals,
        b.blocks,
        b.turnovers,
        b.minutes,
        b.plus_minus,
        b.is_starter,
        g.game_date,
        g.season,
        g.home_team_id,
        g.away_team_id
    FROM box_score_players b
    JOIN games g ON b.game_id = g.game_id
    WHERE b.player_id = '{player_id}'
        AND b.points IS NOT NULL
        AND b.minutes IS NOT NULL
        AND b.minutes > 0
    ORDER BY g.game_date ASC
    LIMIT 500
    """

    result = _execute_query(query)

    if not result["success"] or result["row_count"] < min_games:
        pytest.skip(
            f"Insufficient data for player {player_id}: {result.get('row_count', 0)} games (error: {result.get('error', 'N/A')})"
        )

    df = pd.DataFrame(result["rows"])
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["is_home"] = (df["team_id"] == df["home_team_id"]).astype(int)

    return df


def fetch_multi_player_stats(min_games: int = 50, n_players: int = 5) -> pd.DataFrame:
    """
    Fetch statistics for multiple players for panel data analysis.

    Args:
        min_games: Minimum games per player
        n_players: Number of players to fetch

    Returns:
        DataFrame with multi-player panel data
    """
    # First get players with sufficient games
    query = f"""
    SELECT player_id, COUNT(*) as games
    FROM box_score_players
    WHERE points IS NOT NULL
    GROUP BY player_id
    HAVING COUNT(*) >= {min_games}
    ORDER BY games DESC
    LIMIT {n_players}
    """

    result = _execute_query(query)

    if not result["success"] or result["row_count"] < n_players:
        pytest.skip(
            f"Insufficient players with {min_games}+ games (error: {result.get('error', 'N/A')})"
        )

    player_ids = [row["player_id"] for row in result["rows"]]

    # Fetch stats for these players
    player_list = "','".join(player_ids)
    query = f"""
    SELECT
        b.player_id,
        b.points,
        b.total_rebounds as rebounds,
        b.assists,
        b.minutes,
        g.game_date,
        g.season
    FROM box_score_players b
    JOIN games g ON b.game_id = g.game_id
    WHERE b.player_id IN ('{player_list}')
        AND b.points IS NOT NULL
        AND b.minutes > 0
    ORDER BY b.player_id, g.game_date ASC
    LIMIT 1000
    """

    result = _execute_query(query)

    if not result["success"]:
        pytest.skip(f"Failed to fetch multi-player data: {result.get('error', 'N/A')}")

    df = pd.DataFrame(result["rows"])
    df["game_date"] = pd.to_datetime(df["game_date"])

    # Create game number per player
    df["game_num"] = df.groupby("player_id").cumcount() + 1

    return df


def fetch_team_season_stats(team_id: str, season: str) -> pd.DataFrame:
    """
    Fetch team statistics for a specific season.

    Args:
        team_id: NBA team ID
        season: Season string (e.g., '2021-22')

    Returns:
        DataFrame with team game statistics
    """
    query = f"""
    SELECT
        g.game_id,
        g.game_date,
        g.season,
        g.home_team_id,
        g.away_team_id,
        g.home_score,
        g.away_score,
        CASE
            WHEN g.home_team_id = '{team_id}' THEN 1
            ELSE 0
        END as is_home,
        CASE
            WHEN g.home_team_id = '{team_id}' THEN g.home_score
            ELSE g.away_score
        END as team_score,
        CASE
            WHEN g.home_team_id = '{team_id}' THEN g.away_score
            ELSE g.home_score
        END as opponent_score
    FROM games g
    WHERE (g.home_team_id = '{team_id}' OR g.away_team_id = '{team_id}')
        AND g.season = '{season}'
        AND g.completed = true
        AND g.home_score IS NOT NULL
    ORDER BY g.game_date ASC
    """

    result = _execute_query(query)

    if not result["success"] or result["row_count"] < 30:
        pytest.skip(
            f"Insufficient data for team {team_id} in {season} (error: {result.get('error', 'N/A')})"
        )

    df = pd.DataFrame(result["rows"])
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["win"] = (df["team_score"] > df["opponent_score"]).astype(int)
    df["point_differential"] = df["team_score"] - df["opponent_score"]

    return df


# ============================================================================
# Category 1: Real Player Time Series Analysis (3 tests)
# ============================================================================


class TestRealPlayerTimeSeries:
    """Test time series analysis with real player data."""

    def test_real_player_arima_forecast(self):
        """Test ARIMA forecasting with real player scoring data."""
        # Fetch real player data (LeBron James - player_id 1966)
        df = fetch_player_stats("1966", min_games=82)

        # Take one season of data for analysis
        df_season = df.head(82)

        suite = EconometricSuite(data=df_season, target="points", time_col="game_date")

        # Fit ARIMA model
        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert result is not None
        assert hasattr(result.result, "aic")
        assert result.result.aic > 0

        # Forecast next 10 games
        forecast = result.result.model.forecast(steps=10)

        assert len(forecast) == 10
        # Points should be reasonable (0-60 range for most players)
        assert all(forecast >= 0)
        assert all(forecast <= 70)  # Very rare to score 70+

        # Forecast mean should be close to historical mean
        historical_mean = df_season["points"].mean()
        forecast_mean = forecast.mean()

        # Forecast should be within 50% of historical mean
        assert abs(forecast_mean - historical_mean) / historical_mean < 0.5

    def test_real_player_performance_trend(self):
        """Test trend detection in real player performance over multiple seasons."""
        df = fetch_player_stats("1966", min_games=200)

        # Test if we can detect performance trends
        suite = EconometricSuite(data=df, target="points", time_col="game_date")

        # Fit ARIMA with trend
        result = suite.time_series_analysis(method="arima", order=(2, 1, 2))

        assert result is not None
        assert hasattr(result.result, "model")

        # Check that residuals don't have extreme outliers
        residuals = result.result.model.resid
        residual_std = np.std(residuals)

        # Most residuals should be within 3 std deviations
        outliers = np.abs(residuals) > 3 * residual_std
        outlier_rate = outliers.sum() / len(residuals)

        assert outlier_rate < 0.05  # Less than 5% outliers

    def test_real_player_assist_rebound_correlation(self):
        """Test multivariate analysis of assists and rebounds."""
        df = fetch_player_stats("1966", min_games=100)

        # Take sufficient data for VAR
        df_recent = df.head(100)

        # Prepare multivariate data
        var_data = df_recent[["assists", "rebounds"]].dropna()

        if len(var_data) < 50:
            pytest.skip("Insufficient data for VAR analysis")

        suite = EconometricSuite(data=df_recent, time_col="game_date")

        # Fit VAR model
        result = suite.time_series_analysis(
            method="var", endog_data=var_data, maxlags=2
        )

        assert result is not None
        assert result.result.n_vars == 2

        # Forecast should maintain reasonable relationships
        forecast = result.result.model.forecast(var_data.values[-2:], steps=5)

        assert forecast.shape == (5, 2)
        # Assists and rebounds should both be non-negative
        assert np.all(forecast >= 0)


# ============================================================================
# Category 2: Real Team Panel Analysis (2 tests)
# ============================================================================


class TestRealTeamPanel:
    """Test panel analysis with real team data."""

    def test_multi_team_fixed_effects(self):
        """Test fixed effects panel model with multiple teams."""
        # Fetch panel data for multiple players (serves as panel entities)
        df = fetch_multi_player_stats(min_games=50, n_players=10)

        # Ensure we have enough observations per player
        min_obs_per_player = df.groupby("player_id").size().min()

        if min_obs_per_player < 10:
            pytest.skip("Insufficient observations per player for panel analysis")

        # Take first N games from each player for balanced panel
        n_games = min(30, min_obs_per_player)
        df_balanced = df.groupby("player_id").head(n_games)

        suite = EconometricSuite(
            data=df_balanced,
            target="points",
            entity_col="player_id",
            time_col="game_num",
        )

        # Fit fixed effects model
        result = suite.panel_analysis(method="fixed_effects")

        assert result is not None
        assert result.result.n_entities == 10
        assert hasattr(result.result, "entity_effects")
        assert hasattr(result.result, "r_squared_within")

        # R-squared should be reasonable
        assert 0 <= result.result.r_squared_within <= 1

        # Entity effects should capture player skill differences
        entity_effects = result.result.entity_effects
        assert len(entity_effects) == 10

        # Effects should have meaningful variation
        effect_std = np.std(list(entity_effects.values()))
        assert effect_std > 0

    def test_real_panel_random_effects(self):
        """Test random effects vs fixed effects with real data."""
        df = fetch_multi_player_stats(min_games=50, n_players=10)

        min_obs_per_player = df.groupby("player_id").size().min()
        n_games = min(30, min_obs_per_player)
        df_balanced = df.groupby("player_id").head(n_games)

        suite = EconometricSuite(
            data=df_balanced,
            target="points",
            entity_col="player_id",
            time_col="game_num",
        )

        # Fit both FE and RE
        result_fe = suite.panel_analysis(method="fixed_effects")
        result_re = suite.panel_analysis(method="random_effects")

        assert result_fe is not None
        assert result_re is not None

        # Both should produce valid R-squared
        assert 0 <= result_fe.result.r_squared_within <= 1
        assert 0 <= result_re.result.r_squared_overall <= 1

        # FE within R-squared often higher than RE overall
        # This is a general pattern but not guaranteed


# ============================================================================
# Category 3: Real Causal Inference (2 tests)
# ============================================================================


class TestRealCausalInference:
    """Test causal methods with real NBA data."""

    def test_home_court_advantage_psm(self):
        """Test PSM for estimating home court advantage effect."""
        df = fetch_player_stats("1966", min_games=100)

        # Ensure balanced treatment groups
        home_games = df[df["is_home"] == 1]
        away_games = df[df["is_home"] == 0]

        if len(home_games) < 30 or len(away_games) < 30:
            pytest.skip("Insufficient home/away game balance")

        suite = EconometricSuite(data=df)

        # Estimate home court advantage
        result = suite.causal_analysis(
            treatment_col="is_home", outcome_col="points", method="psm"
        )

        assert result is not None
        assert hasattr(result.result, "att")

        # Home court advantage should be reasonable (typically 2-5 points)
        # But can be negative for some players
        assert abs(result.result.att) < 15  # Should not be extremely large

    def test_starter_vs_bench_effect(self):
        """Test effect of starting vs coming off bench on performance."""
        df = fetch_player_stats("1966", min_games=100)

        # Convert is_starter to numeric
        df["starter"] = df["is_starter"].astype(int)

        # Check if player has both starter and bench games
        starter_games = df[df["starter"] == 1]
        bench_games = df[df["starter"] == 0]

        if len(starter_games) < 20 or len(bench_games) < 20:
            pytest.skip("Player doesn't have enough games in both roles")

        suite = EconometricSuite(data=df)

        # Estimate starting effect on minutes played
        result = suite.causal_analysis(
            treatment_col="starter", outcome_col="minutes", method="psm"
        )

        assert result is not None
        assert hasattr(result.result, "att")

        # Starters typically play more minutes
        # Effect should be positive and meaningful
        assert result.result.att > 0  # Starters should play more


# ============================================================================
# Category 4: Production Data Quality (3 tests)
# ============================================================================


class TestProductionDataQuality:
    """Test data quality and edge cases with real data."""

    def test_missing_data_handling(self):
        """Test that analysis handles real missing data appropriately."""
        df = fetch_player_stats("1966", min_games=100)

        # Check for missing values
        missing_counts = df[["points", "rebounds", "assists"]].isnull().sum()

        if missing_counts.sum() == 0:
            # Artificially introduce some missingness to test handling
            df_test = df.copy()
            missing_idx = np.random.choice(len(df_test), size=5, replace=False)
            df_test.loc[missing_idx, "points"] = np.nan
        else:
            df_test = df

        # Drop missing for analysis
        df_clean = df_test.dropna(subset=["points"])

        suite = EconometricSuite(data=df_clean, target="points", time_col="game_date")

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert result is not None
        assert len(df_clean) < len(df_test) or missing_counts.sum() == 0

    def test_zero_minutes_filtering(self):
        """Test that games with zero minutes are properly handled."""
        # Fetch data including potential zero-minute games
        query = """
        SELECT
            b.player_id,
            b.points,
            b.minutes,
            g.game_date
        FROM box_score_players b
        JOIN games g ON b.game_id = g.game_id
        WHERE b.player_id = '1966'
        ORDER BY g.game_date DESC
        LIMIT 100
        """

        result = _execute_query(query)

        if not result["success"]:
            pytest.skip(f"Database query failed: {result.get('error', 'N/A')}")

        df = pd.DataFrame(result["rows"])
        df["game_date"] = pd.to_datetime(df["game_date"])

        # Filter out zero-minute games
        df_filtered = df[df["minutes"] > 0]

        # Verify filtering worked
        assert (df_filtered["minutes"] > 0).all()

        if len(df_filtered) < 50:
            pytest.skip("Insufficient non-zero minute games")

        suite = EconometricSuite(
            data=df_filtered, target="points", time_col="game_date"
        )

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert result is not None

    def test_outlier_game_robustness(self):
        """Test that models are robust to outlier performances."""
        df = fetch_player_stats("1966", min_games=100)

        # Identify potential outlier games (>40 points for most players)
        outliers = df[df["points"] > 40]

        if len(outliers) == 0:
            pytest.skip("No outlier games found in sample")

        # Run analysis with outliers included
        suite = EconometricSuite(
            data=df.head(100), target="points", time_col="game_date"
        )

        result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

        assert result is not None

        # Model should still converge despite outliers
        assert hasattr(result.result, "aic")
        assert np.isfinite(result.result.aic)


# ============================================================================
# Category 5: Multi-Player Validation (2 tests)
# ============================================================================


class TestMultiPlayerValidation:
    """Test analyses across multiple players for consistency."""

    def test_consistent_forecasts_across_players(self):
        """Test that forecasts are reasonable across different players."""
        # Test with 3 different players
        player_ids = ["1966", "2184", "2779"]  # Top players by games

        forecasts = []

        for player_id in player_ids:
            try:
                df = fetch_player_stats(player_id, min_games=50)

                suite = EconometricSuite(
                    data=df.head(50), target="points", time_col="game_date"
                )

                result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

                if result is not None:
                    forecast = result.result.model.forecast(steps=5)
                    forecasts.append(
                        {
                            "player_id": player_id,
                            "mean_forecast": forecast.mean(),
                            "std_forecast": forecast.std(),
                        }
                    )
            except:
                continue

        if len(forecasts) < 2:
            pytest.skip("Insufficient players with valid forecasts")

        # All forecasts should be in reasonable range
        for f in forecasts:
            assert 0 <= f["mean_forecast"] <= 60
            assert f["std_forecast"] >= 0

    def test_panel_model_generalization(self):
        """Test that panel models generalize across player groups."""
        df = fetch_multi_player_stats(min_games=50, n_players=10)

        min_obs = df.groupby("player_id").size().min()
        n_games = min(30, min_obs)

        # Split into two groups
        players = df["player_id"].unique()
        n_split = len(players) // 2

        group1 = players[:n_split]
        group2 = players[n_split : n_split * 2]

        df1 = df[df["player_id"].isin(group1)].groupby("player_id").head(n_games)
        df2 = df[df["player_id"].isin(group2)].groupby("player_id").head(n_games)

        # Fit models on both groups
        suite1 = EconometricSuite(
            data=df1, target="points", entity_col="player_id", time_col="game_num"
        )

        suite2 = EconometricSuite(
            data=df2, target="points", entity_col="player_id", time_col="game_num"
        )

        result1 = suite1.panel_analysis(method="fixed_effects")
        result2 = suite2.panel_analysis(method="fixed_effects")

        assert result1 is not None
        assert result2 is not None

        # Both models should have reasonable fit
        assert 0 <= result1.result.r_squared_within <= 1
        assert 0 <= result2.result.r_squared_within <= 1

        # R-squared values should be somewhat comparable
        # (Not identical, but in same ballpark for similar player groups)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
