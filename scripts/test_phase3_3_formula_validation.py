"""
Test script for Phase 3.3: Formula Validation System Tools

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


class TestValidationTools(unittest.TestCase):
    async def test_validation_tools(self):
        """
        Tests the new formula validation system tools implemented in Phase 3.3.
        """
        logger.info("Starting tests for Phase 3.3 Formula Validation System Tools...")
        ctx = MockContext()

        try:
            # Test 1: formula_validate (mathematical validation)
            logger.info("\n--- Testing formula_validate (mathematical) ---")
            validation_params = {
                "formula": "PTS / (2 * (FGA + 0.44 * FTA))",
                "formula_id": "true_shooting_test",
                "test_data": {"PTS": 25, "FGA": 20, "FTA": 5},
                "validation_types": ["mathematical", "accuracy", "consistency"],
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_validate", {"params": validation_params}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_validate failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["report"])
            self.assertIsNotNone(result["overall_status"])
            self.assertIsNotNone(result["overall_score"])
            logger.info(
                f"Validation completed: {result['overall_status']} (score: {result['overall_score']:.2f})"
            )

            # Test 2: formula_validate (PER formula)
            logger.info("\n--- Testing formula_validate (PER) ---")
            per_params = {
                "formula": "(FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
                "formula_id": "per_test",
                "test_data": {
                    "FGM": 10,
                    "STL": 2,
                    "3PM": 3,
                    "FTM": 5,
                    "BLK": 1,
                    "OREB": 2,
                    "AST": 8,
                    "DREB": 6,
                    "PF": 3,
                    "FTA": 6,
                    "FGA": 18,
                    "TOV": 3,
                    "MP": 35,
                },
                "validation_types": ["mathematical", "accuracy", "domain_specific"],
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_validate", {"params": per_params}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_validate (PER) failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["report"])
            logger.info(
                f"PER validation completed: {result['overall_status']} (score: {result['overall_score']:.2f})"
            )

            # Test 3: formula_validate (domain-specific validation)
            logger.info("\n--- Testing formula_validate (domain-specific) ---")
            domain_params = {
                "formula": "FGM / FGA",
                "formula_id": "field_goal_percentage",
                "validation_types": ["domain_specific", "mathematical"],
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_validate", {"params": domain_params}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_validate (domain-specific) failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["report"])
            logger.info(
                f"Domain-specific validation completed: {result['overall_status']} (score: {result['overall_score']:.2f})"
            )

            # Test 4: formula_add_reference
            logger.info("\n--- Testing formula_add_reference ---")
            reference_params = {
                "formula_id": "test_formula",
                "name": "Test Formula",
                "formula": "x + y",
                "source": "Test Source",
                "page": "Page 1",
                "expected_result": 5.0,
                "test_data": {"x": 2.0, "y": 3.0},
                "description": "A simple test formula",
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_add_reference", {"params": reference_params}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_add_reference failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["reference"])
            self.assertEqual(result["formula_id"], "test_formula")
            logger.info(f"Added formula reference: {result['formula_id']}")

            # Test 5: formula_get_references
            logger.info("\n--- Testing formula_get_references ---")
            result_tuple = await nba_mcp_server.call_tool(
                "formula_get_references", {"params": {}}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_get_references failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["references"])
            self.assertGreater(len(result["references"]), 0)
            logger.info(f"Retrieved {len(result['references'])} formula references.")

            # Test 6: formula_compare_validations
            logger.info("\n--- Testing formula_compare_validations ---")
            comparison_params = {
                "formula_ids": ["per", "true_shooting", "effective_fg"],
                "comparison_type": "accuracy",
                "test_data": {"PTS": 25, "FGA": 20, "FTA": 5, "MP": 35},
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_compare_validations", {"params": comparison_params}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_compare_validations failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["comparison"])
            self.assertIsNotNone(result["results"])
            logger.info(
                f"Compared {len(result['results'])} formulas for {result['comparison_type']}"
            )

            # Test 7: formula_get_validation_rules
            logger.info("\n--- Testing formula_get_validation_rules ---")
            rules_params = {
                "accuracy_threshold": 0.95,
                "consistency_threshold": 0.90,
                "performance_threshold": 1.0,
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_get_validation_rules", {"params": rules_params}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_get_validation_rules failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["rules"])
            logger.info(f"Retrieved validation rules: {result['rules']}")

            # Test 8: formula_validate (performance validation)
            logger.info("\n--- Testing formula_validate (performance) ---")
            performance_params = {
                "formula": "x**2 + y**2 + z**2",
                "formula_id": "performance_test",
                "test_data": {"x": 1.0, "y": 2.0, "z": 3.0},
                "validation_types": ["performance", "mathematical"],
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_validate", {"params": performance_params}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_validate (performance) failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["report"])
            logger.info(
                f"Performance validation completed: {result['overall_status']} (score: {result['overall_score']:.2f})"
            )

            # Test 9: formula_validate (cross-reference validation)
            logger.info("\n--- Testing formula_validate (cross-reference) ---")
            crossref_params = {
                "formula": "PTS / (2 * (FGA + 0.44 * FTA))",
                "formula_id": "true_shooting_crossref",
                "validation_types": ["cross_reference", "consistency"],
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_validate", {"params": crossref_params}
            )
            result = result_tuple[1]
            self.assertTrue(
                result["success"],
                f"formula_validate (cross-reference) failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["report"])
            logger.info(
                f"Cross-reference validation completed: {result['overall_status']} (score: {result['overall_score']:.2f})"
            )

            # Test 10: formula_validate (invalid formula)
            logger.info("\n--- Testing formula_validate (invalid formula) ---")
            invalid_params = {
                "formula": "invalid_syntax_formula +",
                "formula_id": "invalid_test",
                "validation_types": ["mathematical"],
            }
            result_tuple = await nba_mcp_server.call_tool(
                "formula_validate", {"params": invalid_params}
            )
            result = result_tuple[1]
            # This should succeed but with error status
            self.assertTrue(
                result["success"],
                f"formula_validate (invalid) failed: {result.get('error', 'Unknown error')}",
            )
            self.assertIsNotNone(result["report"])
            # Should have error status for invalid formula
            self.assertIn(result["overall_status"], ["error", "warning"])
            logger.info(
                f"Invalid formula validation completed: {result['overall_status']} (score: {result['overall_score']:.2f})"
            )

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            raise  # Re-raise the exception to indicate test failure

        logger.info("\nAll Phase 3.3 Formula Validation System Tests Passed!")


if __name__ == "__main__":
    asyncio.run(TestValidationTools().test_validation_tools())
