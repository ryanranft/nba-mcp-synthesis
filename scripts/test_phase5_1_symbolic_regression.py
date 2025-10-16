#!/usr/bin/env python3
"""
Test script for Phase 5.1: Symbolic Regression for Sports Analytics

Tests the symbolic regression tools for discovering formulas from data,
generating custom metrics, and identifying patterns.

Author: NBA MCP Server Team
Date: October 13, 2025
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import unittest
import logging
import numpy as np
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestSymbolicRegression(unittest.TestCase):
    """Test suite for Symbolic Regression tools"""

    def setUp(self):
        """Set up test data"""
        # Generate synthetic NBA data
        np.random.seed(42)
        n_samples = 100

        # Simulate player stats
        self.test_data = {
            "points": list(20 + 10 * np.random.randn(n_samples)),
            "rebounds": list(8 + 3 * np.random.randn(n_samples)),
            "assists": list(5 + 2 * np.random.randn(n_samples)),
            "minutes": list(30 + 5 * np.random.randn(n_samples)),
        }

        # Create a known relationship: PER-like metric
        # PER ≈ (points * 1.5 + rebounds * 0.8 + assists * 1.2) / minutes
        self.test_data["efficiency"] = [
            (p * 1.5 + r * 0.8 + a * 1.2) / m + np.random.randn() * 0.5
            for p, r, a, m in zip(
                self.test_data["points"],
                self.test_data["rebounds"],
                self.test_data["assists"],
                self.test_data["minutes"]
            )
        ]

    async def test_discover_formula_linear(self):
        """Test linear formula discovery"""
        logger.info("=== Testing Linear Formula Discovery ===")

        from mcp_server.tools import symbolic_regression

        try:
            result = symbolic_regression.discover_formula_from_data(
                data=self.test_data,
                target_variable="efficiency",
                input_variables=["points", "rebounds", "assists", "minutes"],
                regression_type="linear",
                min_r_squared=0.3,  # Lower threshold for test data
                random_state=42
            )

            logger.info(f"✓ Formula discovered: {result['formula_string']}")
            logger.info(f"  R²: {result['r_squared']:.3f}")
            logger.info(f"  MSE: {result['mean_squared_error']:.3f}")
            logger.info(f"  Complexity: {result['complexity']}")

            self.assertIn('formula_string', result)
            self.assertIn('r_squared', result)
            self.assertGreater(result['r_squared'], 0.3)

            logger.info("✓ Linear formula discovery test passed")

        except Exception as e:
            logger.error(f"❌ Linear formula discovery failed: {e}")
            raise

    async def test_discover_formula_polynomial(self):
        """Test polynomial formula discovery"""
        logger.info("=== Testing Polynomial Formula Discovery ===")

        from mcp_server.tools import symbolic_regression

        try:
            result = symbolic_regression.discover_formula_from_data(
                data=self.test_data,
                target_variable="efficiency",
                input_variables=["points", "rebounds"],
                regression_type="polynomial",
                max_complexity=3,
                min_r_squared=0.4,
                random_state=42
            )

            logger.info(f"✓ Formula discovered: {result['formula_string']}")
            logger.info(f"  R²: {result['r_squared']:.3f}")
            logger.info(f"  Complexity: {result['complexity']}")

            self.assertIn('formula_string', result)
            self.assertIn('r_squared', result)
            self.assertGreater(result['r_squared'], 0.4)

            logger.info("✓ Polynomial formula discovery test passed")

        except Exception as e:
            logger.error(f"❌ Polynomial formula discovery failed: {e}")
            raise

    async def test_validate_formula(self):
        """Test formula validation"""
        logger.info("=== Testing Formula Validation ===")

        from mcp_server.tools import symbolic_regression

        try:
            # First discover a formula
            discovery_result = symbolic_regression.discover_formula_from_data(
                data=self.test_data,
                target_variable="efficiency",
                input_variables=["points", "rebounds"],
                regression_type="linear",
                min_r_squared=0.3,
                random_state=42
            )

            formula = discovery_result['formula_string']
            logger.info(f"  Discovered formula: {formula}")

            # Validate it on the same data (should pass)
            validation_result = symbolic_regression.validate_discovered_formula(
                formula=formula,
                test_data=self.test_data,
                target_variable="efficiency",
                threshold_r_squared=0.3
            )

            logger.info(f"✓ Formula validated successfully")
            logger.info(f"  R²: {validation_result['r_squared']:.3f}")
            logger.info(f"  MSE: {validation_result['mean_squared_error']:.3f}")
            logger.info(f"  Valid predictions: {validation_result['valid_predictions']}/{validation_result['total_predictions']}")

            self.assertEqual(validation_result['validation_status'], 'success')
            self.assertGreater(validation_result['r_squared'], 0.3)

            logger.info("✓ Formula validation test passed")

        except Exception as e:
            logger.error(f"❌ Formula validation failed: {e}")
            raise

    async def test_generate_custom_metric(self):
        """Test custom metric generation"""
        logger.info("=== Testing Custom Metric Generation ===")

        from mcp_server.tools import symbolic_regression

        try:
            result = symbolic_regression.generate_custom_metric(
                formula="1.5*points + 0.8*rebounds + 1.2*assists",
                metric_name="custom_efficiency",
                description="Custom player efficiency metric",
                variables=["points", "rebounds", "assists"],
                parameters={"weight_points": 1.5, "weight_rebounds": 0.8, "weight_assists": 1.2}
            )

            logger.info(f"✓ Custom metric created: {result['metric_name']}")
            logger.info(f"  Formula: {result['formula']}")
            logger.info(f"  Description: {result['description']}")

            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['metric_name'], 'custom_efficiency')

            logger.info("✓ Custom metric generation test passed")

        except Exception as e:
            logger.error(f"❌ Custom metric generation failed: {e}")
            raise

    async def test_discover_patterns_correlation(self):
        """Test pattern discovery using correlation"""
        logger.info("=== Testing Pattern Discovery (Correlation) ===")

        from mcp_server.tools import symbolic_regression

        try:
            result = symbolic_regression.discover_formula_patterns(
                data=self.test_data,
                target_variable="efficiency",
                discovery_method="correlation",
                max_formulas=5,
                complexity_range=(1, 3)
            )

            logger.info(f"✓ Discovered {len(result['discovered_patterns'])} patterns")

            for i, pattern in enumerate(result['discovered_patterns'][:3], 1):
                logger.info(f"  Pattern {i}:")
                logger.info(f"    Type: {pattern['pattern_type']}")
                logger.info(f"    Score: {pattern['score']:.3f}")
                logger.info(f"    Formula: {pattern['suggested_formula']}")

            self.assertEqual(result['status'], 'success')
            self.assertGreater(len(result['discovered_patterns']), 0)

            logger.info("✓ Pattern discovery (correlation) test passed")

        except Exception as e:
            logger.error(f"❌ Pattern discovery (correlation) failed: {e}")
            raise

    async def test_discover_patterns_polynomial(self):
        """Test pattern discovery using polynomial method"""
        logger.info("=== Testing Pattern Discovery (Polynomial) ===")

        from mcp_server.tools import symbolic_regression

        try:
            result = symbolic_regression.discover_formula_patterns(
                data=self.test_data,
                target_variable="efficiency",
                discovery_method="polynomial",
                max_formulas=5,
                complexity_range=(1, 3)
            )

            logger.info(f"✓ Discovered {len(result['discovered_patterns'])} polynomial patterns")

            for i, pattern in enumerate(result['discovered_patterns'][:3], 1):
                logger.info(f"  Pattern {i}:")
                logger.info(f"    Type: {pattern['pattern_type']}")
                logger.info(f"    Score: {pattern['score']:.3f}")

            self.assertEqual(result['status'], 'success')
            self.assertGreater(len(result['discovered_patterns']), 0)

            logger.info("✓ Pattern discovery (polynomial) test passed")

        except Exception as e:
            logger.error(f"❌ Pattern discovery (polynomial) failed: {e}")
            raise

    async def test_real_world_scenario(self):
        """Test a real-world scenario: discovering a shooting efficiency formula"""
        logger.info("=== Testing Real-World Scenario: Shooting Efficiency ===")

        from mcp_server.tools import symbolic_regression

        try:
            # Create shooting data
            shooting_data = {
                "two_pt_made": list(5 + 3 * np.random.randn(50)),
                "three_pt_made": list(2 + 1.5 * np.random.randn(50)),
                "free_throws_made": list(4 + 2 * np.random.randn(50)),
                "total_attempts": list(15 + 4 * np.random.randn(50)),
            }

            # True shooting percentage-like metric
            shooting_data["shooting_efficiency"] = [
                (2*tpm + 3*threepm + ftm) / max(ta, 1) * 100
                for tpm, threepm, ftm, ta in zip(
                    shooting_data["two_pt_made"],
                    shooting_data["three_pt_made"],
                    shooting_data["free_throws_made"],
                    shooting_data["total_attempts"]
                )
            ]

            # Discover formula
            result = symbolic_regression.discover_formula_from_data(
                data=shooting_data,
                target_variable="shooting_efficiency",
                input_variables=["two_pt_made", "three_pt_made", "free_throws_made", "total_attempts"],
                regression_type="linear",
                min_r_squared=0.7,
                random_state=42
            )

            logger.info(f"✓ Shooting efficiency formula discovered")
            logger.info(f"  Formula: {result['formula_string']}")
            logger.info(f"  R²: {result['r_squared']:.3f}")

            # Generate custom metric
            metric_result = symbolic_regression.generate_custom_metric(
                formula=result['formula_string'],
                metric_name="discovered_shooting_efficiency",
                description="Data-driven shooting efficiency metric",
                variables=result['input_variables'],
                parameters={"r_squared": result['r_squared']}
            )

            logger.info(f"✓ Custom metric '{metric_result['metric_name']}' created")

            self.assertGreater(result['r_squared'], 0.7)
            self.assertEqual(metric_result['status'], 'success')

            logger.info("✓ Real-world scenario test passed")

        except Exception as e:
            logger.error(f"❌ Real-world scenario failed: {e}")
            raise


async def run_all_tests():
    """Run all tests asynchronously"""
    logger.info("\n" + "="*70)
    logger.info("Starting Phase 5.1: Symbolic Regression Tests")
    logger.info("="*70 + "\n")

    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestSymbolicRegression)
    runner = unittest.TextTestRunner(verbosity=2)

    # Run each test
    test = TestSymbolicRegression()
    test.setUp()

    try:
        await test.test_discover_formula_linear()
        await test.test_discover_formula_polynomial()
        await test.test_validate_formula()
        await test.test_generate_custom_metric()
        await test.test_discover_patterns_correlation()
        await test.test_discover_patterns_polynomial()
        await test.test_real_world_scenario()

        logger.info("\n" + "="*70)
        logger.info("✓ All Phase 5.1 Symbolic Regression Tests Passed!")
        logger.info("="*70)

    except Exception as e:
        logger.error("\n" + "="*70)
        logger.error(f"❌ Tests Failed: {e}")
        logger.error("="*70)
        raise


if __name__ == '__main__':
    asyncio.run(run_all_tests())

