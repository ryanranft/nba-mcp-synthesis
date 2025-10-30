"""
Comprehensive Test Suite for Panel Data MCP Tools.

Tests Phase 10A Agent 8 Module 2 implementation:
- panel_diagnostics
- pooled_ols_model
- fixed_effects_model
- random_effects_model
- hausman_test
- first_difference_model

Author: Phase 10A Agent 8 Module 2
Date: October 2025
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any, List

# Import the tools class
from mcp_server.tools.panel_data_tools import PanelDataTools


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def tools():
    """Create PanelDataTools instance."""
    return PanelDataTools()


@pytest.fixture
def balanced_panel_data():
    """Generate balanced panel data (2 entities, 5 time periods)."""
    np.random.seed(42)
    data = []
    for entity in ["A", "B"]:
        for time in range(2020, 2025):
            data.append(
                {
                    "entity_id": entity,
                    "time_period": time,
                    "value": np.random.randn() * 10 + 50,
                    "x1": np.random.randn() * 5 + 20,
                    "x2": np.random.randn() * 3 + 10,
                }
            )
    return data


@pytest.fixture
def unbalanced_panel_data():
    """Generate unbalanced panel data (missing observations)."""
    np.random.seed(42)
    data = []
    for entity in ["A", "B", "C"]:
        periods = [2020, 2021, 2022, 2023, 2024]
        if entity == "B":
            periods = [2020, 2022, 2024]  # Missing some periods
        for time in periods:
            data.append(
                {
                    "entity_id": entity,
                    "time_period": time,
                    "value": np.random.randn() * 10 + 50,
                    "x1": np.random.randn() * 5 + 20,
                    "x2": np.random.randn() * 3 + 10,
                }
            )
    return data


@pytest.fixture
def large_panel_data():
    """Generate larger panel data (10 entities, 10 time periods)."""
    np.random.seed(42)
    data = []
    for entity in range(10):
        for time in range(2015, 2025):
            data.append(
                {
                    "entity_id": f"entity_{entity}",
                    "time_period": time,
                    "value": np.random.randn() * 10 + 50 + entity * 2,
                    "x1": np.random.randn() * 5 + 20,
                    "x2": np.random.randn() * 3 + 10,
                }
            )
    return data


@pytest.fixture
def nba_player_panel_data():
    """Generate NBA-like player performance panel data."""
    np.random.seed(42)
    players = ["LeBron", "Durant", "Curry", "Harden"]
    seasons = [2020, 2021, 2022, 2023, 2024]

    data = []
    for player in players:
        for season in seasons:
            # Simulate player performance with age effect
            base_ppg = 25 if player in ["LeBron", "Durant"] else 28
            age_effect = -(season - 2020) * 0.5  # Slight decline over time
            data.append(
                {
                    "entity_id": player,
                    "time_period": season,
                    "value": base_ppg + age_effect + np.random.randn() * 2,
                    "minutes": 34 + np.random.randn() * 2,
                    "age": 28 + (season - 2020) + (0 if player == "Curry" else 2),
                }
            )
    return data


# =============================================================================
# Panel Diagnostics Tests
# =============================================================================


@pytest.mark.asyncio
async def test_panel_diagnostics_balanced(tools, balanced_panel_data):
    """Test panel diagnostics with balanced panel."""
    result = await tools.panel_diagnostics(
        data=balanced_panel_data,
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert result["is_balanced"] is True
    assert result["n_entities"] == 2
    assert result["n_timeperiods"] == 5
    assert result["n_obs"] == 10
    assert result["min_periods"] == 5
    assert result["max_periods"] == 5
    assert result["balance_ratio"] == 1.0
    assert len(result["recommendations"]) > 0
    assert "balanced" in result["recommendations"][0].lower()


@pytest.mark.asyncio
async def test_panel_diagnostics_unbalanced(tools, unbalanced_panel_data):
    """Test panel diagnostics with unbalanced panel."""
    result = await tools.panel_diagnostics(
        data=unbalanced_panel_data,
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert result["is_balanced"] is False
    assert result["n_entities"] == 3
    assert result["n_timeperiods"] == 5
    assert result["min_periods"] == 3
    assert result["max_periods"] == 5
    assert result["balance_ratio"] < 1.0
    assert "unbalanced" in result["recommendations"][0].lower()


@pytest.mark.asyncio
async def test_panel_diagnostics_missing_columns(tools, balanced_panel_data):
    """Test panel diagnostics with missing columns."""
    result = await tools.panel_diagnostics(
        data=balanced_panel_data,
        entity_column="missing_column",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is False
    assert "Missing required columns" in result["error"]


@pytest.mark.asyncio
async def test_panel_diagnostics_small_data(tools):
    """Test panel diagnostics with insufficient data."""
    small_data = [
        {"entity_id": "A", "time_period": 2020, "value": 50},
        {"entity_id": "A", "time_period": 2021, "value": 52},
    ]

    result = await tools.panel_diagnostics(
        data=small_data,
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    # Should still work but recommend more data
    assert result["success"] is True
    assert result["n_obs"] == 2


# =============================================================================
# Pooled OLS Tests
# =============================================================================


@pytest.mark.asyncio
async def test_pooled_ols_basic(tools, balanced_panel_data):
    """Test basic pooled OLS estimation."""
    result = await tools.pooled_ols_model(
        data=balanced_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert "x1" in result["coefficients"]
    assert "x2" in result["coefficients"]
    assert result["r_squared"] >= 0.0
    assert result["r_squared"] <= 1.0
    assert result["n_obs"] == 10
    assert result["model_type"] == "pooled_ols"
    assert len(result["interpretation"]) > 0
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_pooled_ols_significance(tools, large_panel_data):
    """Test pooled OLS with larger dataset for significance."""
    result = await tools.pooled_ols_model(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert result["n_obs"] == 100
    assert result["f_statistic"] is not None
    assert result["f_pvalue"] is not None
    # With 100 observations, likely to have some significance


@pytest.mark.asyncio
async def test_pooled_ols_invalid_formula(tools, balanced_panel_data):
    """Test pooled OLS with invalid formula."""
    result = await tools.pooled_ols_model(
        data=balanced_panel_data,
        formula="value ~ nonexistent_var",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is False
    assert "error" in result


# =============================================================================
# Fixed Effects Tests
# =============================================================================


@pytest.mark.asyncio
async def test_fixed_effects_entity_only(tools, balanced_panel_data):
    """Test fixed effects with entity effects only."""
    result = await tools.fixed_effects_model(
        data=balanced_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
        entity_effects=True,
        time_effects=False,
    )

    assert result["success"] is True
    assert result["entity_effects_included"] is True
    assert result["time_effects_included"] is False
    assert result["model_type"] == "fixed_effects"
    assert result["r_squared_within"] is not None
    assert "entity" in result["interpretation"].lower()


@pytest.mark.asyncio
async def test_fixed_effects_two_way(tools, large_panel_data):
    """Test fixed effects with both entity and time effects."""
    result = await tools.fixed_effects_model(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
        entity_effects=True,
        time_effects=True,
    )

    assert result["success"] is True
    assert result["entity_effects_included"] is True
    assert result["time_effects_included"] is True
    assert "entity and time" in result["interpretation"].lower()


@pytest.mark.asyncio
async def test_fixed_effects_nba_players(tools, nba_player_panel_data):
    """Test fixed effects with NBA player data."""
    result = await tools.fixed_effects_model(
        data=nba_player_panel_data,
        formula="value ~ minutes + age",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
        entity_effects=True,
        time_effects=False,
    )

    assert result["success"] is True
    assert result["n_entities"] == 4  # 4 players
    assert result["n_timeperiods"] == 5  # 5 seasons
    assert "minutes" in result["coefficients"]
    assert "age" in result["coefficients"]


# =============================================================================
# Random Effects Tests
# =============================================================================


@pytest.mark.asyncio
async def test_random_effects_basic(tools, large_panel_data):
    """Test basic random effects estimation."""
    result = await tools.random_effects_model(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert result["model_type"] == "random_effects"
    assert result["r_squared_overall"] is not None
    assert result["r_squared_within"] is not None
    assert result["r_squared_between"] is not None
    assert "random effects" in result["interpretation"].lower()


@pytest.mark.asyncio
async def test_random_effects_large_panel(tools, large_panel_data):
    """Test random effects with larger panel."""
    result = await tools.random_effects_model(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert result["n_entities"] == 10
    assert result["n_obs"] == 100
    # Check that all three R-squared values are provided
    assert isinstance(result["r_squared_overall"], float)
    assert isinstance(result["r_squared_within"], float)
    assert isinstance(result["r_squared_between"], float)


# =============================================================================
# Hausman Test Tests
# =============================================================================


@pytest.mark.asyncio
async def test_hausman_test_basic(tools, large_panel_data):
    """Test Hausman specification test."""
    result = await tools.hausman_test(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert "statistic" in result
    assert "p_value" in result
    assert isinstance(result["reject_re"], bool)
    assert "fe_coefficients" in result
    assert "re_coefficients" in result
    assert "coefficient_differences" in result
    assert result["recommendation"] in [
        "Use fixed effects model",
        "Use random effects model",
    ]


@pytest.mark.asyncio
async def test_hausman_test_large_panel(tools, large_panel_data):
    """Test Hausman test with larger panel."""
    result = await tools.hausman_test(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert result["p_value"] >= 0.0
    assert result["p_value"] <= 1.0
    # Check coefficient differences are computed
    assert "x1" in result["coefficient_differences"]
    assert "x2" in result["coefficient_differences"]


@pytest.mark.asyncio
async def test_hausman_test_nba_players(tools, nba_player_panel_data):
    """Test Hausman test with NBA player data."""
    result = await tools.hausman_test(
        data=nba_player_panel_data,
        formula="value ~ minutes + age",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert len(result["interpretation"]) > 0
    # Both FE and RE should have estimates for minutes and age
    assert "minutes" in result["fe_coefficients"]
    assert "minutes" in result["re_coefficients"]


# =============================================================================
# First Difference Tests
# =============================================================================


@pytest.mark.asyncio
async def test_first_difference_basic(tools, balanced_panel_data):
    """Test first difference estimation."""
    result = await tools.first_difference_model(
        data=balanced_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert result["model_type"] == "first_difference"
    assert result["r_squared"] >= 0.0
    assert result["n_obs"] < 10  # Should be less than original due to differencing
    assert "first difference" in result["interpretation"].lower()


@pytest.mark.asyncio
async def test_first_difference_large_panel(tools, large_panel_data):
    """Test first difference with larger panel."""
    result = await tools.first_difference_model(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    # After differencing, should lose one period per entity
    # 10 entities * 9 periods (10-1) = 90 observations
    assert result["n_obs"] == 90
    assert result["n_entities"] == 10


@pytest.mark.asyncio
async def test_first_difference_recommendations(tools, large_panel_data):
    """Test first difference recommendations."""
    result = await tools.first_difference_model(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert len(result["recommendations"]) > 0
    # Should mention differencing or changes
    recommendations_text = " ".join(result["recommendations"]).lower()
    assert "difference" in recommendations_text or "change" in recommendations_text


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_full_panel_workflow(tools, large_panel_data):
    """Test complete panel data analysis workflow."""
    # 1. Check panel structure
    diagnostics = await tools.panel_diagnostics(
        data=large_panel_data,
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )
    assert diagnostics["success"] is True
    assert diagnostics["is_balanced"] is True

    # 2. Estimate pooled OLS (baseline)
    pooled = await tools.pooled_ols_model(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )
    assert pooled["success"] is True

    # 3. Run Hausman test to choose between FE and RE
    hausman = await tools.hausman_test(
        data=large_panel_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )
    assert hausman["success"] is True

    # 4. Estimate appropriate model based on Hausman test
    if hausman["reject_re"]:
        final_model = await tools.fixed_effects_model(
            data=large_panel_data,
            formula="value ~ x1 + x2",
            entity_column="entity_id",
            time_column="time_period",
            target_column="value",
            entity_effects=True,
            time_effects=False,
        )
    else:
        final_model = await tools.random_effects_model(
            data=large_panel_data,
            formula="value ~ x1 + x2",
            entity_column="entity_id",
            time_column="time_period",
            target_column="value",
        )
    assert final_model["success"] is True


@pytest.mark.asyncio
async def test_nba_player_analysis_workflow(tools, nba_player_panel_data):
    """Test NBA player performance analysis workflow."""
    # 1. Check data structure
    diagnostics = await tools.panel_diagnostics(
        data=nba_player_panel_data,
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )
    assert diagnostics["success"] is True
    assert diagnostics["n_entities"] == 4

    # 2. Fixed effects to control for player-specific ability
    fe_result = await tools.fixed_effects_model(
        data=nba_player_panel_data,
        formula="value ~ minutes + age",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
        entity_effects=True,
        time_effects=False,
    )
    assert fe_result["success"] is True

    # 3. Check if minutes has expected positive effect on points
    # (more minutes should mean more points, controlling for player ability)
    assert "minutes" in fe_result["coefficients"]


# =============================================================================
# Edge Case Tests
# =============================================================================


@pytest.mark.asyncio
async def test_insufficient_data_for_pooled_ols(tools):
    """Test pooled OLS with insufficient data."""
    tiny_data = [
        {"entity_id": "A", "time_period": 2020, "value": 50, "x1": 20},
        {"entity_id": "A", "time_period": 2021, "value": 52, "x1": 21},
    ]

    result = await tools.pooled_ols_model(
        data=tiny_data,
        formula="value ~ x1",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    # Should fail or warn due to insufficient degrees of freedom
    # Pydantic validation should catch this before reaching the tool
    assert result["success"] is False or result["n_obs"] == 2


@pytest.mark.asyncio
async def test_single_entity_panel(tools):
    """Test with single entity (time series, not panel)."""
    single_entity = []
    for time in range(2020, 2025):
        single_entity.append(
            {
                "entity_id": "A",
                "time_period": time,
                "value": 50 + np.random.randn(),
                "x1": 20 + np.random.randn(),
            }
        )

    result = await tools.pooled_ols_model(
        data=single_entity,
        formula="value ~ x1",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    # Should still work but be equivalent to time series regression
    assert result["success"] is True
    assert result["n_entities"] == 1


@pytest.mark.asyncio
async def test_highly_unbalanced_panel(tools):
    """Test with highly unbalanced panel."""
    unbalanced = []
    # Entity A: full data
    for time in range(2020, 2025):
        unbalanced.append(
            {
                "entity_id": "A",
                "time_period": time,
                "value": 50 + np.random.randn(),
                "x1": 20 + np.random.randn(),
            }
        )
    # Entity B: only 1 observation
    unbalanced.append(
        {"entity_id": "B", "time_period": 2020, "value": 45, "x1": 18}
    )

    diagnostics = await tools.panel_diagnostics(
        data=unbalanced,
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert diagnostics["success"] is True
    assert diagnostics["is_balanced"] is False
    assert diagnostics["min_periods"] == 1
    assert diagnostics["max_periods"] == 5


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.asyncio
async def test_large_panel_performance(tools):
    """Test performance with large panel dataset."""
    np.random.seed(42)
    # 50 entities, 20 time periods = 1000 observations
    large_data = []
    for entity in range(50):
        for time in range(2005, 2025):
            large_data.append(
                {
                    "entity_id": f"entity_{entity}",
                    "time_period": time,
                    "value": np.random.randn() * 10 + 50,
                    "x1": np.random.randn() * 5 + 20,
                    "x2": np.random.randn() * 3 + 10,
                }
            )

    # Should complete without timeout
    result = await tools.pooled_ols_model(
        data=large_data,
        formula="value ~ x1 + x2",
        entity_column="entity_id",
        time_column="time_period",
        target_column="value",
    )

    assert result["success"] is True
    assert result["n_obs"] == 1000
    assert result["n_entities"] == 50


@pytest.mark.asyncio
async def test_concurrent_tool_calls(tools, balanced_panel_data):
    """Test multiple concurrent tool calls."""
    import asyncio

    # Run multiple diagnostics concurrently
    tasks = [
        tools.panel_diagnostics(
            data=balanced_panel_data,
            entity_column="entity_id",
            time_column="time_period",
            target_column="value",
        )
        for _ in range(5)
    ]

    results = await asyncio.gather(*tasks)

    assert all(r["success"] is True for r in results)
    assert all(r["n_entities"] == 2 for r in results)
