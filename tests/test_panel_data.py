"""
Tests for panel_data module.

Tests cover:
- Model estimation (pooled, FE, RE)
- Model selection (Hausman, F-test)
- Robust inference
- Integration with NBA data
"""

import pytest
import numpy as np
import pandas as pd

from mcp_server.panel_data import PanelDataAnalyzer, PanelModelResult


@pytest.fixture
def balanced_panel():
    """Generate balanced panel data."""
    np.random.seed(42)

    n_entities = 50
    n_time = 10

    data = []
    for i in range(n_entities):
        entity_effect = np.random.normal(0, 2)  # Entity-specific intercept

        for t in range(n_time):
            time_effect = np.random.normal(0, 0.5)  # Time-specific shock
            x = np.random.uniform(0, 10)
            error = np.random.normal(0, 1)

            # y = entity_effect + time_effect + 2*x + error
            y = entity_effect + time_effect + 2 * x + error

            data.append({"entity_id": i, "time": t, "y": y, "x": x})

    return pd.DataFrame(data)


@pytest.fixture
def nba_player_panel():
    """Simulate NBA player panel data."""
    np.random.seed(42)

    players = [f"P{i}" for i in range(30)]
    seasons = [2020, 2021, 2022]

    data = []
    for player in players:
        player_ability = np.random.normal(20, 5)  # Base ability

        for season in seasons:
            minutes = np.random.uniform(20, 35)
            age = 25 + (season - 2020) + np.random.uniform(-2, 2)
            error = np.random.normal(0, 3)

            # Points = player_ability + 0.5*minutes - 0.3*age + error
            points = player_ability + 0.5 * minutes - 0.3 * age + error

            data.append(
                {
                    "player_id": player,
                    "season": season,
                    "points": points,
                    "minutes": minutes,
                    "age": age,
                }
            )

    return pd.DataFrame(data)


# ============================================
# Model Estimation Tests (6 tests)
# ============================================


def test_pooled_ols(balanced_panel):
    """Test pooled OLS estimation."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    result = analyzer.pooled_ols("y ~ x")

    assert isinstance(result, PanelModelResult)
    assert result.model_type == "pooled_ols"
    assert "x" in result.coefficients.index
    assert result.n_obs == len(balanced_panel)
    assert result.n_entities == 50
    assert result.n_timeperiods == 10


def test_fixed_effects(balanced_panel):
    """Test fixed effects estimation."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    result = analyzer.fixed_effects("y ~ x", entity_effects=True)

    assert isinstance(result, PanelModelResult)
    assert result.model_type == "fixed_effects"
    assert result.r_squared_within is not None
    # FE should capture entity effects → coefficient on x ~ 2
    assert 1.5 < result.coefficients["x"] < 2.5


def test_random_effects(balanced_panel):
    """Test random effects estimation."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    result = analyzer.random_effects("y ~ x")

    assert isinstance(result, PanelModelResult)
    assert result.model_type == "random_effects"
    assert result.r_squared is not None
    # Should estimate coefficient close to 2
    assert 1.5 < result.coefficients["x"] < 2.5


def test_two_way_fixed_effects(balanced_panel):
    """Test two-way FE (entity + time effects)."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    result = analyzer.fixed_effects("y ~ x", entity_effects=True, time_effects=True)

    assert isinstance(result, PanelModelResult)
    assert result.model_type == "fixed_effects"
    # Both effects should improve fit
    assert result.r_squared > 0


def test_balance_check(balanced_panel):
    """Test panel balance checking."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    balance_info = analyzer.balance_check()

    assert balance_info["is_balanced"] is True
    assert balance_info["min_periods"] == balance_info["max_periods"]
    assert balance_info["n_entities"] == 50
    assert balance_info["n_timeperiods"] == 10


def test_unbalanced_panel():
    """Test with unbalanced panel."""
    data = pd.DataFrame(
        {
            "entity_id": [1, 1, 1, 2, 2, 3],
            "time": [1, 2, 3, 1, 2, 1],
            "y": [1, 2, 3, 4, 5, 6],
            "x": [1, 1, 1, 1, 1, 1],
        }
    )

    analyzer = PanelDataAnalyzer(
        data, entity_col="entity_id", time_col="time", target_col="y"
    )

    balance_info = analyzer.balance_check()

    assert balance_info["is_balanced"] is False
    assert balance_info["min_periods"] == 1
    assert balance_info["max_periods"] == 3


# ============================================
# Model Selection Tests (4 tests)
# ============================================


def test_hausman_test(balanced_panel):
    """Test Hausman test for FE vs RE."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    hausman_result = analyzer.hausman_test("y ~ x")

    assert "h_statistic" in hausman_result
    assert "p_value" in hausman_result
    assert "recommendation" in hausman_result
    assert hausman_result["recommendation"] in [
        "fixed_effects",
        "random_effects",
        "inconclusive",
    ]


def test_f_test_effects(balanced_panel):
    """Test F-test for entity effects."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    f_test_result = analyzer.f_test_effects("y ~ x")

    assert "f_statistic" in f_test_result
    assert "p_value" in f_test_result
    assert "recommendation" in f_test_result
    assert f_test_result["recommendation"] in ["fixed_effects", "pooled_ols"]
    # F-statistic should be non-negative
    assert f_test_result["f_statistic"] >= 0 or np.isnan(f_test_result["f_statistic"])


def test_clustered_standard_errors(balanced_panel):
    """Test clustered standard errors."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    result = analyzer.clustered_standard_errors("y ~ x", cluster_entity=True)

    assert isinstance(result, PanelModelResult)
    assert result.model_type == "clustered_se"
    assert "x" in result.coefficients.index


def test_hausman_test_with_precomputed(balanced_panel):
    """Test Hausman test with pre-computed results."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    # Pre-compute models
    fe = analyzer.fixed_effects("y ~ x")
    re = analyzer.random_effects("y ~ x")

    # Run test with pre-computed results
    hausman_result = analyzer.hausman_test("y ~ x", fe_result=fe, re_result=re)

    assert hausman_result["recommendation"] in [
        "fixed_effects",
        "random_effects",
        "inconclusive",
    ]


# ============================================
# NBA Integration Tests (5 tests)
# ============================================


def test_nba_player_performance_panel(nba_player_panel):
    """Integration test: NBA player performance panel."""
    analyzer = PanelDataAnalyzer(
        nba_player_panel, entity_col="player_id", time_col="season", target_col="points"
    )

    # Test fixed effects
    fe_result = analyzer.fixed_effects("points ~ minutes + age", entity_effects=True)

    assert fe_result.coefficients["minutes"] > 0  # More minutes → more points
    # Age coefficient might be negative (decline) but could vary in simulated data


def test_panel_data_workflow(nba_player_panel):
    """End-to-end panel data workflow."""
    analyzer = PanelDataAnalyzer(
        nba_player_panel, entity_col="player_id", time_col="season", target_col="points"
    )

    # 1. Check balance
    balance = analyzer.balance_check()
    assert balance["is_balanced"] is True

    # 2. Estimate models
    pooled = analyzer.pooled_ols("points ~ minutes + age")
    fe = analyzer.fixed_effects("points ~ minutes + age")
    re = analyzer.random_effects("points ~ minutes + age")

    # 3. Model selection
    hausman = analyzer.hausman_test("points ~ minutes + age", fe, re)
    f_test = analyzer.f_test_effects("points ~ minutes + age")

    # 4. Verify results
    assert all([pooled, fe, re, hausman, f_test])


def test_panel_model_result_summary(balanced_panel):
    """Test PanelModelResult summary method."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    result = analyzer.fixed_effects("y ~ x")
    summary = result.summary()

    assert "FIXED_EFFECTS Model Results" in summary
    assert "R-squared" in summary
    assert "Coefficients:" in summary
    assert "x" in summary


def test_invalid_column_names():
    """Test error handling for invalid column names."""
    data = pd.DataFrame(
        {
            "entity": [1, 1, 2, 2],
            "time": [1, 2, 1, 2],
            "y": [1, 2, 3, 4],
            "x": [1, 1, 1, 1],
        }
    )

    with pytest.raises(ValueError, match="Column 'invalid' not found"):
        PanelDataAnalyzer(data, entity_col="invalid", time_col="time", target_col="y")


def test_model_comparison(nba_player_panel):
    """Test comparison across different panel models."""
    analyzer = PanelDataAnalyzer(
        nba_player_panel, entity_col="player_id", time_col="season", target_col="points"
    )

    pooled = analyzer.pooled_ols("points ~ minutes")
    fe = analyzer.fixed_effects("points ~ minutes")
    re = analyzer.random_effects("points ~ minutes")

    # FE should have higher within R-squared
    assert fe.r_squared_within is not None

    # All should estimate positive coefficient on minutes
    assert pooled.coefficients["minutes"] > 0
    assert fe.coefficients["minutes"] > 0
    assert re.coefficients["minutes"] > 0


# ============================================
# Edge Cases & Validation Tests (5 tests)
# ============================================


def test_small_panel():
    """Test with very small panel."""
    data = pd.DataFrame(
        {
            "entity": [1, 1, 2, 2],
            "time": [1, 2, 1, 2],
            "y": [1, 2, 3, 4],
            "x": [1, 2, 1, 2],
        }
    )

    analyzer = PanelDataAnalyzer(
        data, entity_col="entity", time_col="time", target_col="y"
    )

    result = analyzer.pooled_ols("y ~ x")
    assert isinstance(result, PanelModelResult)


def test_single_regressor(balanced_panel):
    """Test with single independent variable."""
    analyzer = PanelDataAnalyzer(
        balanced_panel, entity_col="entity_id", time_col="time", target_col="y"
    )

    result = analyzer.fixed_effects("y ~ x")
    assert len(result.coefficients) == 1
    assert "x" in result.coefficients.index


def test_multiple_regressors():
    """Test with multiple independent variables."""
    np.random.seed(42)

    data = []
    for i in range(20):
        for t in range(5):
            data.append(
                {
                    "entity": i,
                    "time": t,
                    "y": np.random.normal(10, 2),
                    "x1": np.random.uniform(0, 5),
                    "x2": np.random.uniform(0, 5),
                    "x3": np.random.uniform(0, 5),
                }
            )

    df = pd.DataFrame(data)

    analyzer = PanelDataAnalyzer(
        df, entity_col="entity", time_col="time", target_col="y"
    )

    result = analyzer.fixed_effects("y ~ x1 + x2 + x3")
    assert len(result.coefficients) == 3
    assert all(var in result.coefficients.index for var in ["x1", "x2", "x3"])


def test_f_test_edge_case_small_sample():
    """Test F-test with edge case of very small sample."""
    data = pd.DataFrame(
        {
            "entity": [1, 1, 2, 2, 3, 3],
            "time": [1, 2, 1, 2, 1, 2],
            "y": [1, 2, 3, 4, 5, 6],
            "x": [1, 2, 3, 4, 5, 6],
        }
    )

    analyzer = PanelDataAnalyzer(
        data, entity_col="entity", time_col="time", target_col="y"
    )

    # This should still work even with small sample
    result = analyzer.f_test_effects("y ~ x")
    assert "f_statistic" in result


def test_time_varying_covariates(nba_player_panel):
    """Test with time-varying covariates (minutes, age)."""
    analyzer = PanelDataAnalyzer(
        nba_player_panel, entity_col="player_id", time_col="season", target_col="points"
    )

    # Fixed effects should absorb time-invariant player ability
    fe_result = analyzer.fixed_effects("points ~ minutes + age")

    # Within-player variation should still show positive effect of minutes
    assert fe_result.coefficients["minutes"] > 0
    assert fe_result.r_squared_within is not None
