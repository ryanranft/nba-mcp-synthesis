#!/usr/bin/env python3
"""
Test script for Phase 3.1: Interactive Formula Playground Tools

This script tests the new interactive formula playground tools implemented in Phase 3.1.

Author: NBA MCP Server Team
Date: 2025-01-11
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


async def test_playground_tools():
    """
    Tests the new interactive formula playground tools implemented in Phase 3.1.
    """
    logger.info("Starting tests for Phase 3.1 Interactive Formula Playground Tools...")
    ctx = MockContext()

    try:
        # Test 1: playground_create_session
        logger.info("\n--- Testing playground_create_session ---")

        # Test creating a session with template
        result_tuple = await nba_mcp_server.call_tool(
            "playground_create_session",
            {
                "params": {
                    "user_id": "test_user",
                    "mode": "explore",
                    "template_name": "Shooting Efficiency Lab",
                }
            },
        )
        result = result_tuple[1]
        assert result["success"], f"playground_create_session failed: {result['error']}"
        assert (
            result["session_id"] is not None
        ), f"Should have session_id: {result['session_id']}"
        assert (
            result["session"] is not None
        ), f"Should have session: {result['session']}"
        assert (
            len(result["session"]["formulas"]) > 0
        ), f"Should have formulas from template: {result['session']['formulas']}"
        logger.info(f"Created session with template: {result['session_id']}")

        session_id = result["session_id"]

        # Test creating a session without template
        result_tuple = await nba_mcp_server.call_tool(
            "playground_create_session",
            {
                "params": {
                    "user_id": "test_user2",
                    "mode": "build",
                    "template_name": None,
                }
            },
        )
        result = result_tuple[1]
        assert result["success"], f"playground_create_session failed: {result['error']}"
        assert (
            result["session_id"] is not None
        ), f"Should have session_id: {result['session_id']}"
        assert (
            len(result["session"]["formulas"]) == 0
        ), f"Should have no formulas without template: {result['session']['formulas']}"
        logger.info(f"Created empty session: {result['session_id']}")

        # Test 2: playground_add_formula
        logger.info("\n--- Testing playground_add_formula ---")

        result_tuple = await nba_mcp_server.call_tool(
            "playground_add_formula",
            {
                "params": {
                    "session_id": session_id,
                    "formula": "PTS / (2 * (FGA + 0.44 * FTA))",
                    "description": "True Shooting Percentage",
                }
            },
        )
        result = result_tuple[1]
        assert result["success"], f"playground_add_formula failed: {result['error']}"
        assert (
            result["formula_entry"] is not None
        ), f"Should have formula_entry: {result['formula_entry']}"
        assert result[
            "session_updated"
        ], f"Should have updated session: {result['session_updated']}"
        logger.info(f"Added formula to session: {result['formula_entry']['formula']}")

        # Test adding invalid formula
        result_tuple = await nba_mcp_server.call_tool(
            "playground_add_formula",
            {
                "params": {
                    "session_id": session_id,
                    "formula": "PTS / (2 * (FGA +",
                    "description": "Invalid formula",
                }
            },
        )
        result = result_tuple[1]
        assert not result[
            "success"
        ], f"Should fail for invalid formula: {result['success']}"
        assert (
            result["error"] is not None
        ), f"Should have error message: {result['error']}"
        logger.info(f"Correctly rejected invalid formula: {result['error']}")

        # Test 3: playground_update_variables
        logger.info("\n--- Testing playground_update_variables ---")

        result_tuple = await nba_mcp_server.call_tool(
            "playground_update_variables",
            {
                "params": {
                    "session_id": session_id,
                    "variables": {"PTS": 25.0, "FGA": 20.0, "FTA": 5.0},
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"playground_update_variables failed: {result.get('error', 'Unknown error')}"
        assert (
            result["updated_variables"] is not None
        ), f"Should have updated_variables: {result['updated_variables']}"
        assert result[
            "session_updated"
        ], f"Should have updated session: {result['session_updated']}"
        logger.info(f"Updated variables: {result['updated_variables']}")

        # Test updating with invalid values
        result_tuple = await nba_mcp_server.call_tool(
            "playground_update_variables",
            {
                "params": {
                    "session_id": session_id,
                    "variables": {"PTS": 250.0, "FGA": 20.0, "FTA": 5.0},
                }
            },
        )
        result = result_tuple[1]
        assert not result[
            "success"
        ], f"Should fail for invalid values: {result['success']}"
        assert result["errors"] is not None, f"Should have errors: {result['errors']}"
        logger.info(f"Correctly rejected invalid values: {result['errors']}")

        # Test 4: playground_calculate_results
        logger.info("\n--- Testing playground_calculate_results ---")

        result_tuple = await nba_mcp_server.call_tool(
            "playground_calculate_results", {"params": {"session_id": session_id}}
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"playground_calculate_results failed: {result['error']}"
        assert (
            result["results"] is not None
        ), f"Should have results: {result['results']}"
        assert (
            result["variables_used"] is not None
        ), f"Should have variables_used: {result['variables_used']}"
        logger.info(f"Calculated results for {len(result['results'])} formulas")

        # Test 5: playground_generate_visualizations
        logger.info("\n--- Testing playground_generate_visualizations ---")

        result_tuple = await nba_mcp_server.call_tool(
            "playground_generate_visualizations",
            {
                "params": {
                    "session_id": session_id,
                    "visualization_types": ["latex", "table"],
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"playground_generate_visualizations failed: {result['error']}"
        assert (
            result["visualizations"] is not None
        ), f"Should have visualizations: {result['visualizations']}"
        assert (
            result["session_id"] == session_id
        ), f"Should have correct session_id: {result['session_id']}"
        logger.info(
            f"Generated visualizations: {list(result['visualizations'].keys())}"
        )

        # Test 6: playground_get_recommendations
        logger.info("\n--- Testing playground_get_recommendations ---")

        result_tuple = await nba_mcp_server.call_tool(
            "playground_get_recommendations", {"params": {"session_id": session_id}}
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"playground_get_recommendations failed: {result['error']}"
        assert (
            result["recommendations"] is not None
        ), f"Should have recommendations: {result['recommendations']}"
        assert isinstance(
            result["recommendations"], list
        ), f"Should have list of recommendations: {type(result['recommendations'])}"
        logger.info(f"Got {len(result['recommendations'])} recommendations")

        # Test 7: playground_share_session
        logger.info("\n--- Testing playground_share_session ---")

        result_tuple = await nba_mcp_server.call_tool(
            "playground_share_session", {"params": {"session_id": session_id}}
        )
        result = result_tuple[1]
        assert result["success"], f"playground_share_session failed: {result['error']}"
        assert (
            result["share_token"] is not None
        ), f"Should have share_token: {result['share_token']}"
        assert (
            result["share_url"] is not None
        ), f"Should have share_url: {result['share_url']}"
        assert (
            result["session_id"] == session_id
        ), f"Should have correct session_id: {result['session_id']}"
        logger.info(f"Shared session with token: {result['share_token']}")

        share_token = result["share_token"]

        # Test 8: playground_get_shared_session
        logger.info("\n--- Testing playground_get_shared_session ---")

        result_tuple = await nba_mcp_server.call_tool(
            "playground_get_shared_session", {"params": {"share_token": share_token}}
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"playground_get_shared_session failed: {result['error']}"
        assert (
            result["session"] is not None
        ), f"Should have session: {result['session']}"
        assert (
            result["session"]["session_id"] == session_id
        ), f"Should have correct session_id: {result['session']['session_id']}"
        logger.info(f"Retrieved shared session: {result['session']['session_id']}")

        # Test 9: playground_create_experiment
        logger.info("\n--- Testing playground_create_experiment ---")

        result_tuple = await nba_mcp_server.call_tool(
            "playground_create_experiment",
            {
                "params": {
                    "session_id": session_id,
                    "experiment_name": "Shooting Efficiency Analysis",
                    "description": "Analysis of player shooting efficiency",
                }
            },
        )
        result = result_tuple[1]
        assert result[
            "success"
        ], f"playground_create_experiment failed: {result['error']}"
        assert (
            result["experiment"] is not None
        ), f"Should have experiment: {result['experiment']}"
        assert (
            result["experiment_id"] is not None
        ), f"Should have experiment_id: {result['experiment_id']}"
        logger.info(f"Created experiment: {result['experiment_id']}")

        # Test 10: End-to-end workflow
        logger.info("\n--- Testing End-to-End Workflow ---")

        # Create new session
        result_tuple = await nba_mcp_server.call_tool(
            "playground_create_session",
            {
                "params": {
                    "user_id": "workflow_test",
                    "mode": "learn",
                    "template_name": "Advanced Metrics Workshop",
                }
            },
        )
        workflow_session = result_tuple[1]
        assert workflow_session[
            "success"
        ], f"Workflow session creation failed: {workflow_session['error']}"
        workflow_session_id = workflow_session["session_id"]

        # Add custom formula
        result_tuple = await nba_mcp_server.call_tool(
            "playground_add_formula",
            {
                "params": {
                    "session_id": workflow_session_id,
                    "formula": "ORtg - DRtg",
                    "description": "Net Rating",
                }
            },
        )
        add_result = result_tuple[1]
        assert add_result[
            "success"
        ], f"Workflow formula addition failed: {add_result['error']}"

        # Update variables
        result_tuple = await nba_mcp_server.call_tool(
            "playground_update_variables",
            {
                "params": {
                    "session_id": workflow_session_id,
                    "variables": {"ORtg": 115.0, "DRtg": 108.0},
                }
            },
        )
        update_result = result_tuple[1]
        assert update_result[
            "success"
        ], f"Workflow variable update failed: {update_result['error']}"

        # Calculate results
        result_tuple = await nba_mcp_server.call_tool(
            "playground_calculate_results",
            {"params": {"session_id": workflow_session_id}},
        )
        calc_result = result_tuple[1]
        assert calc_result[
            "success"
        ], f"Workflow calculation failed: {calc_result['error']}"

        # Generate visualizations
        result_tuple = await nba_mcp_server.call_tool(
            "playground_generate_visualizations",
            {
                "params": {
                    "session_id": workflow_session_id,
                    "visualization_types": ["latex", "table"],
                }
            },
        )
        viz_result = result_tuple[1]
        assert viz_result[
            "success"
        ], f"Workflow visualization failed: {viz_result['error']}"

        logger.info("End-to-end workflow completed successfully!")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        raise  # Re-raise the exception to indicate test failure

    logger.info("\nAll Phase 3.1 Interactive Formula Playground Tests Passed!")


if __name__ == "__main__":
    asyncio.run(test_playground_tools())
