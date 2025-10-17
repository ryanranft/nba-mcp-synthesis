"""
Test script for Phase 3.2: Advanced Visualization Engine Tools

Author: NBA MCP Server Team
Date: 2025-01-13
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP, Context
from mcp_server.fastmcp_server import mcp as nba_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Mock Context for testing
class MockContext(Context):
    def __init__(self):
        super().__init__(agent_id="test_agent", conversation_id="test_conv")
        self._logs = []

    async def info(self, message: str):
        self._logs.append(f"INFO: {message}")
        logger.info(message)

    async def error(self, message: str):
        self._logs.append(f"ERROR: {message}")
        logger.error(message)

    async def warn(self, message: str):
        self._logs.append(f"WARN: {message}")
        logger.warning(message)

    async def debug(self, message: str):
        self._logs.append(f"DEBUG: {message}")
        logger.debug(message)


async def test_visualization_tools():
    """
    Tests the new advanced visualization engine tools implemented in Phase 3.2.
    """
    logger.info("Starting tests for Phase 3.2 Advanced Visualization Engine Tools...")
    ctx = MockContext()

    try:
        # Test 1: visualization_generate - Scatter Plot
        logger.info("\n--- Testing visualization_generate (scatter) ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_generate",
            {
                "params": {
                    "visualization_type": "scatter",
                    "data": {
                        "x": [25.0, 20.0, 30.0, 15.0, 28.0],
                        "y": [15.0, 18.0, 12.0, 22.0, 16.0],
                        "labels": [
                            "Player A",
                            "Player B",
                            "Player C",
                            "Player D",
                            "Player E",
                        ],
                    },
                    "config": {
                        "title": "Player Performance Comparison",
                        "x_label": "Points per Game",
                        "y_label": "Rebounds per Game",
                    },
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"visualization_generate (scatter) failed: {result['error']}"
        assert result["visualization_type"] == "scatter"
        assert result["data"]["success"] == True
        assert result["data"]["type"] == "scatter"
        logger.info(f"Generated scatter plot: {result['data']['title']}")

        # Test 2: visualization_generate - Bar Chart
        logger.info("\n--- Testing visualization_generate (bar) ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_generate",
            {
                "params": {
                    "visualization_type": "bar",
                    "data": {
                        "x": ["Lakers", "Warriors", "Celtics", "Heat", "Nuggets"],
                        "y": [115.2, 112.8, 110.5, 108.9, 107.3],
                    },
                    "config": {
                        "title": "Team Offensive Ratings",
                        "x_label": "Teams",
                        "y_label": "Offensive Rating",
                    },
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"visualization_generate (bar) failed: {result['error']}"
        assert result["visualization_type"] == "bar"
        assert result["data"]["success"] == True
        logger.info(f"Generated bar chart: {result['data']['title']}")

        # Test 3: visualization_generate - Heatmap
        logger.info("\n--- Testing visualization_generate (heatmap) ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_generate",
            {
                "params": {
                    "visualization_type": "heatmap",
                    "data": {
                        "data": [
                            [0.45, 0.52, 0.38],
                            [0.38, 0.48, 0.42],
                            [0.52, 0.45, 0.35],
                        ]
                    },
                    "config": {"title": "Shooting Efficiency Heatmap"},
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"visualization_generate (heatmap) failed: {result['error']}"
        assert result["visualization_type"] == "heatmap"
        assert result["data"]["success"] == True
        logger.info(f"Generated heatmap: {result['data']['title']}")

        # Test 4: visualization_generate - LaTeX
        logger.info("\n--- Testing visualization_generate (latex) ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_generate",
            {
                "params": {
                    "visualization_type": "latex",
                    "data": {"formula": "PTS / (2 * (FGA + 0.44 * FTA))"},
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"visualization_generate (latex) failed: {result['error']}"
        assert result["visualization_type"] == "latex"
        assert result["data"]["success"] == True
        assert "latex_string" in result["data"]
        logger.info(f"Generated LaTeX: {result['data']['latex_string']}")

        # Test 5: visualization_export
        logger.info("\n--- Testing visualization_export ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_export",
            {
                "params": {
                    "visualization_data": {
                        "type": "scatter",
                        "data": [{"x": 25.0, "y": 15.0}],
                    },
                    "format": "png",
                    "filename": "test_chart.png",
                }
            },
        )
        result = result_tuple[1]
        assert result["success"], f"visualization_export failed: {result['error']}"
        assert result["format"] == "png"
        assert result["filename"] == "test_chart.png"
        assert result["file_path"] is not None
        logger.info(f"Exported visualization: {result['filename']}")

        # Test 6: visualization_get_templates (all templates)
        logger.info("\n--- Testing visualization_get_templates (all) ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_get_templates", {"params": {}}
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"visualization_get_templates failed: {result['error']}"
        assert result["templates"] is not None
        assert len(result["templates"]) > 0
        assert any(t["name"] == "Player Comparison" for t in result["templates"])
        logger.info(f"Retrieved {len(result['templates'])} visualization templates")

        # Test 7: visualization_get_templates (specific template)
        logger.info("\n--- Testing visualization_get_templates (specific) ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_get_templates",
            {"params": {"template_name": "player_comparison"}},
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"visualization_get_templates (specific) failed: {result['error']}"
        assert result["template"] is not None
        assert result["template"]["name"] == "Player Comparison"
        assert result["template"]["type"] == "scatter"
        logger.info(f"Retrieved specific template: {result['template']['name']}")

        # Test 8: visualization_get_config
        logger.info("\n--- Testing visualization_get_config ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_get_config",
            {
                "params": {
                    "width": 1000,
                    "height": 800,
                    "title": "Custom Chart",
                    "x_label": "Custom X",
                    "y_label": "Custom Y",
                    "color_scheme": "sports",
                    "interactive": True,
                }
            },
        )
        result = result_tuple[1]
        assert result["success"], f"visualization_get_config failed: {result['error']}"
        assert result["config"] is not None
        assert result["config"]["width"] == 1000
        assert result["config"]["height"] == 800
        assert result["config"]["title"] == "Custom Chart"
        assert result["config"]["color_scheme"] == "sports"
        logger.info(
            f"Retrieved config: {result['config']['width']}x{result['config']['height']}"
        )

        # Test 9: visualization_create_data_point
        logger.info("\n--- Testing visualization_create_data_point ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_create_data_point",
            {
                "params": {
                    "x": 25.0,
                    "y": 15.0,
                    "z": 5.0,
                    "label": "Test Player",
                    "color": "#FF6B6B",
                    "size": 10.0,
                    "metadata": {"team": "Lakers", "position": "PG"},
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"visualization_create_data_point failed: {result['error']}"
        assert result["data_point"] is not None
        assert result["data_point"]["x"] == 25.0
        assert result["data_point"]["y"] == 15.0
        assert result["data_point"]["z"] == 5.0
        assert result["data_point"]["label"] == "Test Player"
        assert result["data_point_id"] is not None
        logger.info(f"Created data point: {result['data_point']['label']}")

        # Test 10: visualization_create_dataset
        logger.info("\n--- Testing visualization_create_dataset ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_create_dataset",
            {
                "params": {
                    "name": "Test Dataset",
                    "data_points": [
                        {"x": 25.0, "y": 15.0, "label": "Player A"},
                        {"x": 20.0, "y": 18.0, "label": "Player B"},
                        {"x": 30.0, "y": 12.0, "label": "Player C"},
                    ],
                    "x_column": "points",
                    "y_column": "rebounds",
                    "metadata": {"season": "2024", "league": "NBA"},
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"visualization_create_dataset failed: {result['error']}"
        assert result["dataset"] is not None
        assert result["dataset"]["name"] == "Test Dataset"
        assert result["dataset"]["x_column"] == "points"
        assert result["dataset"]["y_column"] == "rebounds"
        assert result["data_points_count"] == 3
        assert result["dataset_id"] is not None
        logger.info(
            f"Created dataset: {result['dataset']['name']} with {result['data_points_count']} points"
        )

        # Test 11: Invalid visualization type
        logger.info("\n--- Testing invalid visualization type ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_generate",
            {
                "params": {
                    "visualization_type": "invalid_type",
                    "data": {"x": [1, 2, 3], "y": [4, 5, 6]},
                }
            },
        )
        result = result_tuple[1]
        assert not result[
            "success"
        ], f"Invalid visualization type should fail: {result}"
        assert "Unsupported visualization type" in result["error"]
        logger.info(f"Invalid visualization type correctly rejected: {result['error']}")

        # Test 12: Invalid template name
        logger.info("\n--- Testing invalid template name ---")

        result_tuple = await nba_mcp_server.call_tool(
            "visualization_get_templates",
            {"params": {"template_name": "nonexistent_template"}},
        )
        result = result_tuple[1]
        assert not result["success"], f"Invalid template name should fail: {result}"
        assert "not found" in result["error"]
        logger.info(f"Invalid template name correctly rejected: {result['error']}")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        raise  # Re-raise the exception to indicate test failure

    logger.info("\nAll Phase 3.2 Advanced Visualization Engine Tests Passed!")


if __name__ == "__main__":
    asyncio.run(test_visualization_tools())
