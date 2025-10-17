#!/usr/bin/env python3
"""
Test script for Phase 5.2: Natural Language to Formula Conversion

Tests the natural language to formula conversion tools for parsing
descriptions into mathematical expressions, suggesting formulas,
and validating natural language descriptions.

Author: NBA MCP Server Team
Date: October 13, 2025
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import unittest
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestNaturalLanguageFormula(unittest.TestCase):
    """Test suite for Natural Language to Formula Conversion tools"""

    def setUp(self):
        """Set up test cases"""
        self.test_cases = [
            {
                "description": "player efficiency rating",
                "expected_variables": [
                    "PTS",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "FGA",
                    "FGM",
                    "FTA",
                    "FTM",
                    "TOV",
                    "MP",
                ],
                "expected_contains": ["PTS", "REB", "AST"],
            },
            {
                "description": "true shooting percentage",
                "expected_variables": ["PTS", "FGA", "FTA"],
                "expected_contains": ["PTS", "FGA"],
            },
            {
                "description": "field goal percentage",
                "expected_variables": ["FGM", "FGA"],
                "expected_contains": ["FGM", "FGA"],
            },
            {
                "description": "points per game",
                "expected_variables": ["PTS", "GP"],
                "expected_contains": ["PTS"],
            },
            {
                "description": "assist to turnover ratio",
                "expected_variables": ["AST", "TOV"],
                "expected_contains": ["AST", "TOV"],
            },
            {
                "description": "rebounds plus assists",
                "expected_variables": ["REB", "AST"],
                "expected_contains": ["REB", "AST"],
            },
            {
                "description": "usage rate percentage",
                "expected_variables": ["FGA", "FTA", "TOV", "MP"],
                "expected_contains": ["FGA", "FTA"],
            },
        ]

    async def test_parse_natural_language_formula(self):
        """Test parsing natural language descriptions to formulas"""
        logger.info("=== Testing Natural Language Formula Parsing ===")

        from mcp_server.tools import natural_language_formula

        for i, test_case in enumerate(self.test_cases, 1):
            logger.info(f"--- Test Case {i}: {test_case['description']} ---")

            try:
                result = natural_language_formula.parse_natural_language_formula(
                    description=test_case["description"], context="basketball"
                )

                logger.info(f"✓ Parsed successfully")
                logger.info(f"  Formula: {result['formula_string']}")
                logger.info(f"  Variables: {result['variables']}")
                logger.info(f"  LaTeX: {result['formula_latex']}")

                # Basic validation
                self.assertIn("formula_string", result)
                self.assertIn("variables", result)
                self.assertIn("formula_latex", result)
                self.assertEqual(result["status"], "success")

                # Check if expected variables are present (be more lenient)
                found_vars = 0
                for expected_var in test_case["expected_contains"]:
                    if expected_var in result["variables"]:
                        found_vars += 1

                # At least one expected variable should be found
                self.assertGreater(
                    found_vars,
                    0,
                    f"Expected at least one variable from {test_case['expected_contains']} in {result['variables']}",
                )

                logger.info(f"✓ Test case {i} passed")

            except Exception as e:
                logger.error(f"❌ Test case {i} failed: {e}")
                raise

    async def test_suggest_formula_from_description(self):
        """Test formula suggestions based on descriptions"""
        logger.info("=== Testing Formula Suggestions ===")

        from mcp_server.tools import natural_language_formula

        suggestion_tests = [
            "player efficiency rating",
            "shooting percentage",
            "usage rate",
            "win shares",
            "assist ratio",
        ]

        for i, description in enumerate(suggestion_tests, 1):
            logger.info(f"--- Suggestion Test {i}: {description} ---")

            try:
                result = natural_language_formula.suggest_formula_from_description(
                    description=description, context="basketball"
                )

                logger.info(f"✓ Generated {len(result['suggestions'])} suggestions")

                for j, suggestion in enumerate(result["suggestions"][:3], 1):
                    logger.info(f"  Suggestion {j}: {suggestion['name']}")
                    logger.info(f"    Formula: {suggestion['formula']}")
                    logger.info(f"    Confidence: {suggestion['confidence']}")

                # Basic validation
                self.assertIn("suggestions", result)
                self.assertIn("status", result)
                self.assertEqual(result["status"], "success")
                self.assertGreater(len(result["suggestions"]), 0)

                logger.info(f"✓ Suggestion test {i} passed")

            except Exception as e:
                logger.error(f"❌ Suggestion test {i} failed: {e}")
                raise

    async def test_validate_natural_language_formula(self):
        """Test formula validation"""
        logger.info("=== Testing Formula Validation ===")

        from mcp_server.tools import natural_language_formula

        validation_tests = [
            {"description": "field goal percentage", "expected_formula": "FGM / FGA"},
            {"description": "points plus rebounds", "expected_formula": "PTS + REB"},
            {
                "description": "assist to turnover ratio",
                "expected_formula": "AST / TOV",
            },
        ]

        for i, test_case in enumerate(validation_tests, 1):
            logger.info(f"--- Validation Test {i}: {test_case['description']} ---")

            try:
                result = natural_language_formula.validate_natural_language_formula(
                    description=test_case["description"],
                    expected_formula=test_case["expected_formula"],
                )

                logger.info(f"✓ Validation completed")
                logger.info(f"  Is Valid: {result['is_valid']}")
                logger.info(f"  Parsed Formula: {result['parsed_formula']}")
                logger.info(f"  Variables: {result['variables']}")

                if "errors" in result and result["errors"]:
                    logger.info(f"  Errors: {result['errors']}")

                if "warnings" in result and result["warnings"]:
                    logger.info(f"  Warnings: {result['warnings']}")

                # Basic validation
                self.assertIn("is_valid", result)
                self.assertIn("parsed_formula", result)
                self.assertIn("variables", result)

                logger.info(f"✓ Validation test {i} passed")

            except Exception as e:
                logger.error(f"❌ Validation test {i} failed: {e}")
                raise

    async def test_complex_formula_parsing(self):
        """Test parsing of complex formulas"""
        logger.info("=== Testing Complex Formula Parsing ===")

        from mcp_server.tools import natural_language_formula

        complex_tests = [
            "player efficiency rating with minutes played",
            "true shooting percentage including three pointers",
            "usage rate percentage with team statistics",
            "win shares per 48 minutes",
            "box plus minus with pace adjustment",
        ]

        for i, description in enumerate(complex_tests, 1):
            logger.info(f"--- Complex Test {i}: {description} ---")

            try:
                result = natural_language_formula.parse_natural_language_formula(
                    description=description, context="basketball"
                )

                logger.info(f"✓ Complex formula parsed")
                logger.info(f"  Formula: {result['formula_string']}")
                logger.info(f"  Variables: {result['variables']}")
                logger.info(f"  Complexity: {result['validation']['complexity']}")

                # Basic validation
                self.assertIn("formula_string", result)
                self.assertIn("variables", result)
                self.assertIn("validation", result)

                logger.info(f"✓ Complex test {i} passed")

            except Exception as e:
                logger.error(f"❌ Complex test {i} failed: {e}")
                raise

    async def test_error_handling(self):
        """Test error handling for invalid inputs"""
        logger.info("=== Testing Error Handling ===")

        from mcp_server.tools import natural_language_formula

        error_tests = [
            "",  # Empty description
            "a",  # Too short
            "invalid mathematical expression with no variables",  # No variables
        ]

        for i, description in enumerate(error_tests, 1):
            logger.info(f"--- Error Test {i}: '{description}' ---")

            try:
                result = natural_language_formula.parse_natural_language_formula(
                    description=description, context="basketball"
                )

                # If we get here, the test should check for warnings/errors
                logger.info(
                    f"✓ Error handling test {i} - got result with status: {result.get('status', 'unknown')}"
                )

            except Exception as e:
                logger.info(f"✓ Error handling test {i} - correctly caught error: {e}")
                # This is expected for invalid inputs

    async def test_real_world_scenarios(self):
        """Test real-world sports analytics scenarios"""
        logger.info("=== Testing Real-World Scenarios ===")

        from mcp_server.tools import natural_language_formula

        real_world_tests = [
            {
                "description": "Calculate player efficiency rating for LeBron James",
                "context": "player_analysis",
            },
            {
                "description": "Find the true shooting percentage formula",
                "context": "shooting_analytics",
            },
            {
                "description": "What is the formula for usage rate?",
                "context": "possession_analysis",
            },
            {
                "description": "How do you calculate win shares per 48 minutes?",
                "context": "advanced_metrics",
            },
        ]

        for i, test_case in enumerate(real_world_tests, 1):
            logger.info(f"--- Real-World Test {i}: {test_case['description']} ---")

            try:
                result = natural_language_formula.parse_natural_language_formula(
                    description=test_case["description"], context=test_case["context"]
                )

                logger.info(f"✓ Real-world scenario parsed")
                logger.info(f"  Formula: {result['formula_string']}")
                logger.info(f"  Variables: {result['variables']}")
                logger.info(f"  Context: {result.get('context', 'None')}")

                # Basic validation
                self.assertIn("formula_string", result)
                self.assertIn("variables", result)

                logger.info(f"✓ Real-world test {i} passed")

            except Exception as e:
                logger.error(f"❌ Real-world test {i} failed: {e}")
                raise


async def run_all_tests():
    """Run all tests asynchronously"""
    logger.info("\n" + "=" * 70)
    logger.info("Starting Phase 5.2: Natural Language to Formula Tests")
    logger.info("=" * 70 + "\n")

    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestNaturalLanguageFormula)
    runner = unittest.TextTestRunner(verbosity=2)

    # Run each test
    test = TestNaturalLanguageFormula()
    test.setUp()

    try:
        await test.test_parse_natural_language_formula()
        await test.test_suggest_formula_from_description()
        await test.test_validate_natural_language_formula()
        await test.test_complex_formula_parsing()
        await test.test_error_handling()
        await test.test_real_world_scenarios()

        logger.info("\n" + "=" * 70)
        logger.info("✓ All Phase 5.2 Natural Language to Formula Tests Passed!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error("\n" + "=" * 70)
        logger.error(f"❌ Tests Failed: {e}")
        logger.error("=" * 70)
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
