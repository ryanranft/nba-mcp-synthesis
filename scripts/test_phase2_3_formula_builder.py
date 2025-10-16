#!/usr/bin/env python3
"""
Test script for Phase 2.3: Interactive Formula Builder

This script tests the new interactive formula builder tools implemented in Phase 2.3.
It verifies formula validation, completion suggestions, preview generation,
template management, and formula export functionality.

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_formula_builder_tools():
    """
    Tests the new interactive formula builder tools implemented in Phase 2.3.
    """
    logger.info("Starting tests for Phase 2.3 Interactive Formula Builder Tools...")

    try:
        # Test 1: formula_builder_validate
        logger.info("\n--- Testing formula_builder_validate ---")

        # Test syntax validation
        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_validate",
            {"params": {"formula": "PTS / (2 * (FGA + 0.44 * FTA))", "validation_level": "syntax"}}
        )
        result = result_tuple[1]  # Extract the actual result from the tuple
        assert result['success'], f"formula_builder_validate failed: {result['error']}"
        assert result['is_valid'], f"Formula should be valid: {result['errors']}"
        logger.info(f"Syntax validation passed: {result['formula']}")

        # Test semantic validation
        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_validate",
            {"params": {"formula": "PTS / (2 * (FGA + 0.44 * FTA))", "validation_level": "semantic"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_validate failed: {result['error']}"
        assert result['is_valid'], f"Formula should be valid: {result['errors']}"
        logger.info(f"Semantic validation passed: {result['formula']}")

        # Test sports context validation
        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_validate",
            {"params": {"formula": "(FGM * 85.910 + STL * 53.897) / MP", "validation_level": "sports_context"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_validate failed: {result['error']}"
        assert result['is_valid'], f"Formula should be valid: {result['errors']}"
        logger.info(f"Sports context validation passed: {result['formula']}")

        # Test invalid formula
        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_validate",
            {"params": {"formula": "PTS / (2 * (FGA +", "validation_level": "syntax"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_validate failed: {result['error']}"
        assert not result['is_valid'], f"Formula should be invalid: {result['errors']}"
        logger.info(f"Invalid formula correctly detected: {result['errors']}")

        # Test 2: formula_builder_suggest
        logger.info("\n--- Testing formula_builder_suggest ---")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_suggest",
            {"params": {"partial_formula": "PTS / (2 * (FGA +", "context": "shooting efficiency"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_suggest failed: {result['error']}"
        assert result['suggestion_count'] > 0, f"Should have suggestions: {result['suggestions']}"
        logger.info(f"Got {result['suggestion_count']} suggestions: {result['suggestions'][:3]}...")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_suggest",
            {"params": {"partial_formula": "(FGM * 85.910 + STL * 53.897) /", "context": "advanced metrics"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_suggest failed: {result['error']}"
        assert result['suggestion_count'] > 0, f"Should have suggestions: {result['suggestions']}"
        logger.info(f"Got {result['suggestion_count']} suggestions for PER: {result['suggestions'][:3]}...")

        # Test 3: formula_builder_preview
        logger.info("\n--- Testing formula_builder_preview ---")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_preview",
            {"params": {"formula": "PTS / (2 * (FGA + 0.44 * FTA))", "variable_values": {"PTS": 25, "FGA": 15, "FTA": 6}}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_preview failed: {result['error']}"
        assert result['latex'] is not None, f"Should have LaTeX: {result['latex']}"
        assert result['simplified'] is not None, f"Should have simplified form: {result['simplified']}"
        assert result['calculated_value'] is not None, f"Should have calculated value: {result['calculated_value']}"
        assert len(result['variables']) > 0, f"Should have variables: {result['variables']}"
        logger.info(f"Preview generated - LaTeX: {result['latex']}")
        logger.info(f"Calculated value: {result['calculated_value']}")

        # Test preview without values
        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_preview",
            {"params": {"formula": "PTS / (2 * (FGA + 0.44 * FTA))"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_preview failed: {result['error']}"
        assert result['latex'] is not None, f"Should have LaTeX: {result['latex']}"
        assert result['calculated_value'] is None, f"Should not have calculated value without inputs"
        logger.info(f"Preview without values generated - LaTeX: {result['latex']}")

        # Test 4: formula_builder_get_templates
        logger.info("\n--- Testing formula_builder_get_templates ---")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_get_templates",
            {"params": {"template_name": None, "category": "shooting"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_get_templates failed: {result['error']}"
        assert result['template_count'] > 0, f"Should have templates: {result['templates']}"
        logger.info(f"Got {result['template_count']} shooting templates")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_get_templates",
            {"params": {"template_name": "True Shooting Percentage", "category": None}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_get_templates failed: {result['error']}"
        assert result['template_count'] > 0, f"Should have TS% template: {result['templates']}"
        logger.info(f"Found TS% template: {result['templates'][0]['name']}")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_get_templates",
            {"params": {"template_name": None, "category": None}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_get_templates failed: {result['error']}"
        assert result['template_count'] > 0, f"Should have templates: {result['templates']}"
        logger.info(f"Got {result['template_count']} total templates")

        # Test 5: formula_builder_create_from_template
        logger.info("\n--- Testing formula_builder_create_from_template ---")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_create_from_template",
            {"params": {"template_name": "True Shooting Percentage", "variable_values": {"PTS": 25, "FGA": 15, "FTA": 6}}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_create_from_template failed: {result['error']}"
        assert result['result'] is not None, f"Should have calculated result: {result['result']}"
        assert result['substituted_formula'] is not None, f"Should have substituted formula: {result['substituted_formula']}"
        logger.info(f"Created formula from template - Result: {result['result']}")
        logger.info(f"Substituted formula: {result['substituted_formula']}")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_create_from_template",
            {"params": {"template_name": "Player Efficiency Rating", "variable_values": {"FGM": 8, "STL": 2, "3PM": 3, "FTM": 5, "BLK": 1, "OREB": 2, "AST": 6, "DREB": 5, "PF": 3, "FTA": 6, "FGA": 15, "TOV": 2, "MP": 35}}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_create_from_template failed: {result['error']}"
        assert result['result'] is not None, f"Should have calculated result: {result['result']}"
        logger.info(f"Created PER formula from template - Result: {result['result']}")

        # Test 6: formula_builder_export
        logger.info("\n--- Testing formula_builder_export ---")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_export",
            {"params": {"formula": "PTS / (2 * (FGA + 0.44 * FTA))", "format_type": "latex"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_export failed: {result['error']}"
        assert result['exported_content'] is not None, f"Should have exported content: {result['exported_content']}"
        logger.info(f"Exported to LaTeX: {result['exported_content']}")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_export",
            {"params": {"formula": "PTS / (2 * (FGA + 0.44 * FTA))", "format_type": "python"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_export failed: {result['error']}"
        assert result['exported_content'] is not None, f"Should have exported content: {result['exported_content']}"
        logger.info(f"Exported to Python: {result['exported_content']}")

        result_tuple = await nba_mcp_server.call_tool(
            "formula_builder_export",
            {"params": {"formula": "PTS / (2 * (FGA + 0.44 * FTA))", "format_type": "sympy"}}
        )
        result = result_tuple[1]
        assert result['success'], f"formula_builder_export failed: {result['error']}"
        assert result['exported_content'] is not None, f"Should have exported content: {result['exported_content']}"
        logger.info(f"Exported to SymPy: {result['exported_content']}")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        raise

    logger.info("\nAll Phase 2.3 Interactive Formula Builder Tests Passed!")

if __name__ == "__main__":
    asyncio.run(test_formula_builder_tools())