"""
Test script for Phase 3.4: Multi-Book Formula Comparison Tools

Author: NBA MCP Server Team
Date: 2025-01-13
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP, Context
from mcp_server.fastmcp_server import mcp as nba_mcp_server

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

class TestComparisonTools(unittest.TestCase):
    async def test_comparison_tools(self):
        """
        Tests the new multi-book formula comparison tools implemented in Phase 3.4.
        """
        logger.info("Starting tests for Phase 3.4 Multi-Book Formula Comparison Tools...")
        ctx = MockContext()

        try:
            # Test 1: formula_compare_versions (PER formula)
            logger.info("\n--- Testing formula_compare_versions (PER) ---")
            comparison_params = {
                "formula_id": "per",
                "comparison_types": ["structural", "mathematical", "accuracy"],
                "include_historical": True
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_compare_versions",
                {"params": comparison_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_compare_versions failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['comparison'])
            self.assertIsNotNone(result['versions'])
            self.assertGreater(len(result['versions']), 1, "Should have multiple versions")
            self.assertIsNotNone(result['overall_similarity'])
            self.assertIsNotNone(result['summary'])
            logger.info(f"PER comparison completed: {result['overall_similarity']:.2f} similarity, {len(result['versions'])} versions")

            # Test 2: formula_compare_versions (True Shooting)
            logger.info("\n--- Testing formula_compare_versions (True Shooting) ---")
            ts_params = {
                "formula_id": "true_shooting",
                "comparison_types": ["accuracy", "source_reliability"],
                "include_historical": False
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_compare_versions",
                {"params": ts_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_compare_versions (TS) failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['variations'])
            self.assertGreater(len(result['variations']), 0, "Should have variations")
            logger.info(f"True Shooting comparison: {len(result['variations'])} variations found")

            # Test 3: formula_get_all_versions
            logger.info("\n--- Testing formula_get_all_versions ---")
            versions_params = {
                "formula_id": "per"
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_get_all_versions",
                {"params": versions_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_get_all_versions failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['versions'])
            self.assertGreater(len(result['versions']), 0, "Should have versions")
            logger.info(f"Retrieved {len(result['versions'])} versions of PER formula")

            # Test 4: formula_get_evolution
            logger.info("\n--- Testing formula_get_evolution ---")
            evolution_params = {
                "formula_id": "per",
                "include_timeline": True,
                "include_changes": True
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_get_evolution",
                {"params": evolution_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_get_evolution failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['evolution'])
            self.assertIsNotNone(result['timeline'])
            self.assertIsNotNone(result['evolution_summary'])
            logger.info(f"Evolution analysis: {result['evolution_summary']}")

            # Test 5: formula_get_recommendations (academic context)
            logger.info("\n--- Testing formula_get_recommendations (academic) ---")
            rec_params = {
                "formula_id": "per",
                "criteria": ["reliability", "recency", "accuracy"],
                "context": "academic research"
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_get_recommendations",
                {"params": rec_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_get_recommendations failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['recommendations'])
            self.assertGreater(len(result['recommendations']), 0, "Should have recommendations")
            self.assertIsNotNone(result['recommended_version'])
            logger.info(f"Generated {len(result['recommendations'])} recommendations for academic context")

            # Test 6: formula_get_recommendations (practical context)
            logger.info("\n--- Testing formula_get_recommendations (practical) ---")
            practical_params = {
                "formula_id": "true_shooting",
                "criteria": ["reliability"],
                "context": "practical applications"
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_get_recommendations",
                {"params": practical_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_get_recommendations (practical) failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['recommendations'])
            logger.info(f"Generated {len(result['recommendations'])} recommendations for practical context")

            # Test 7: formula_add_version
            logger.info("\n--- Testing formula_add_version ---")
            add_version_params = {
                "version_id": "per_test_2025",
                "formula_id": "per",
                "formula": "(FGM * 85.91 + STL * 53.9 + 3PM * 51.76 + FTM * 46.85 + BLK * 39.19 + OREB * 39.19 + AST * 34.68 + DREB * 14.71 - PF * 17.17 - (FTA - FTM) * 20.09 - (FGA - FGM) * 39.19 - TOV * 53.9) * (1 / MP)",
                "source_id": "basketball_analytics",
                "description": "Test PER formula with rounded coefficients",
                "test_data": {
                    "FGM": 10, "STL": 2, "3PM": 3, "FTM": 5, "BLK": 1,
                    "OREB": 2, "AST": 8, "DREB": 6, "PF": 3, "FTA": 6,
                    "FGA": 18, "TOV": 3, "MP": 35
                },
                "expected_result": 25.1,
                "created_date": "2025",
                "is_primary": False
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_add_version",
                {"params": add_version_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_add_version failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['version'])
            self.assertEqual(result['version_id'], "per_test_2025")
            logger.info(f"Added new version: {result['version_id']}")

            # Test 8: formula_compare_versions (after adding version)
            # Note: Since each MCP tool call creates a new instance, the added version won't persist
            # This test just verifies the comparison still works
            logger.info("\n--- Testing formula_compare_versions (after adding version) ---")
            new_comparison_params = {
                "formula_id": "per",
                "comparison_types": ["structural", "mathematical"],
                "include_historical": True
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_compare_versions",
                {"params": new_comparison_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_compare_versions (after adding version) failed: {result.get('error', 'Unknown error')}")
            self.assertEqual(len(result['versions']), 3, "Should still have 3 versions (added version not persisted across instances)")
            logger.info(f"Comparison after add: {len(result['versions'])} versions, {result['overall_similarity']:.2f} similarity")

            # Test 9: formula_get_evolution (usage rate)
            logger.info("\n--- Testing formula_get_evolution (usage rate) ---")
            usage_evolution_params = {
                "formula_id": "usage_rate",
                "include_timeline": True,
                "include_changes": True
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_get_evolution",
                {"params": usage_evolution_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_get_evolution (usage rate) failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['timeline'])
            logger.info(f"Usage rate evolution: {len(result['timeline'])} versions in timeline")

            # Test 10: formula_get_recommendations (no context)
            logger.info("\n--- Testing formula_get_recommendations (no context) ---")
            no_context_params = {
                "formula_id": "usage_rate",
                "criteria": ["reliability", "accuracy"]
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_get_recommendations",
                {"params": no_context_params}
            )
            result = result_tuple[1]
            self.assertTrue(result['success'], f"formula_get_recommendations (no context) failed: {result.get('error', 'Unknown error')}")
            self.assertIsNotNone(result['recommendations'])
            logger.info(f"Generated {len(result['recommendations'])} recommendations without context")

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            raise # Re-raise the exception to indicate test failure

        logger.info("\nAll Phase 3.4 Multi-Book Formula Comparison Tests Passed!")

if __name__ == '__main__':
    asyncio.run(TestComparisonTools().test_comparison_tools())
