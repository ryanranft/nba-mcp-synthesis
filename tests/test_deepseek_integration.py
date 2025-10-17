"""
Tests for DeepSeek Model Integration
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.models.deepseek_model import DeepSeekModel
from mcp_server.env_helper import get_hierarchical_env


@pytest.mark.asyncio
async def test_deepseek_connection():
    """Test basic connection to DeepSeek API"""
    # Skip if no API key
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        pytest.skip("DEEPSEEK_API_KEY not set")

    model = DeepSeekModel()
    result = await model.query(prompt="What is 2 + 2?", temperature=0.2)

    assert result["success"] is True
    assert "response" in result
    assert result["cost"] < 0.001  # Should be very cheap


@pytest.mark.asyncio
async def test_sql_optimization():
    """Test SQL optimization functionality"""
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        pytest.skip("DEEPSEEK_API_KEY not set")

    model = DeepSeekModel()
    sql = "SELECT * FROM player_game_stats WHERE player_id = 123"

    result = await model.optimize_sql(
        sql_query=sql, table_stats={"row_count": 100000, "has_index_on_player_id": True}
    )

    assert result["success"] is True
    assert "response" in result
    assert result["cost"] < 0.01  # Should be very cheap


@pytest.mark.asyncio
async def test_statistical_analysis():
    """Test statistical analysis functionality"""
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        pytest.skip("DEEPSEEK_API_KEY not set")

    model = DeepSeekModel()

    result = await model.analyze_statistics(
        data_description="Player points per game over a season",
        statistical_question="Calculate the correlation between points and assists",
    )

    assert result["success"] is True
    assert "response" in result


@pytest.mark.asyncio
async def test_code_debugging():
    """Test code debugging functionality"""
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        pytest.skip("DEEPSEEK_API_KEY not set")

    model = DeepSeekModel()

    buggy_code = """
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

result = calculate_average([])  # Bug: Division by zero
"""

    result = await model.debug_code(
        code=buggy_code,
        error_message="ZeroDivisionError: division by zero",
        expected_behavior="Should handle empty list gracefully",
    )

    assert result["success"] is True
    assert "response" in result


@pytest.mark.asyncio
async def test_temperature_control():
    """Test that temperature affects randomness"""
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        pytest.skip("DEEPSEEK_API_KEY not set")

    model = DeepSeekModel()

    # Low temperature (more deterministic)
    result_low = await model.query(
        prompt="Explain what a basketball assist is in one sentence.", temperature=0.1
    )

    # Higher temperature (more creative)
    result_high = await model.query(
        prompt="Explain what a basketball assist is in one sentence.", temperature=0.8
    )

    assert result_low["success"] is True
    assert result_high["success"] is True
    assert result_low["temperature"] == 0.1
    assert result_high["temperature"] == 0.8


@pytest.mark.asyncio
async def test_cost_calculation():
    """Test cost calculation is accurate"""
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        pytest.skip("DEEPSEEK_API_KEY not set")

    model = DeepSeekModel()

    result = await model.query(prompt="Hello", temperature=0.3)

    assert result["success"] is True
    assert "cost" in result
    assert result["cost"] > 0
    assert result["cost"] < 0.001  # Very cheap for simple query
    assert "tokens_used" in result
    assert "tokens_input" in result
    assert "tokens_output" in result


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling with invalid input"""
    model = DeepSeekModel()

    # Test with empty prompt
    result = await model.query(prompt="", temperature=0.3)

    # Should handle gracefully (might succeed with empty response or fail gracefully)
    assert "success" in result


@pytest.mark.asyncio
async def test_context_formatting():
    """Test context is properly formatted"""
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        pytest.skip("DEEPSEEK_API_KEY not set")

    model = DeepSeekModel()

    context = {
        "schema": {"player_id": "INTEGER", "name": "VARCHAR"},
        "table_stats": {"row_count": 1000},
        "sample_data": [{"player_id": 1, "name": "LeBron"}],
    }

    result = await model.query(
        prompt="Analyze this data", context=context, temperature=0.2
    )

    assert result["success"] is True


def test_model_initialization():
    """Test model can be initialized"""
    model = DeepSeekModel()
    assert model.model == os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


@pytest.mark.asyncio
async def test_sync_mode():
    """Test synchronous mode works"""
    if not get_hierarchical_env("DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
        pytest.skip("DEEPSEEK_API_KEY not set")

    # Initialize in sync mode
    model = DeepSeekModel(async_mode=False)

    # Note: Still need to use await since the wrapper is async
    result = await model.query(prompt="What is 1 + 1?", temperature=0.2)

    assert result["success"] is True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
