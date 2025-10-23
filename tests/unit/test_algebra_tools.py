#!/usr/bin/env python3
"""
Unit Tests for Algebraic Tools

This module contains comprehensive unit tests for all algebraic manipulation tools
in the NBA MCP server, including sports formulas, validation, and edge cases.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import unittest
import pytest
import sys
import os
from typing import Dict, Any, List
import sympy as sp
from sympy import symbols, simplify, expand, factor, diff, integrate, solve

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.tools.algebra_helper import (
    get_sports_formula,
    calculate_sports_formula,
    validate_sports_stat,
    get_formula_variables,
    simplify_formula,
    expand_formula,
    factor_formula,
    differentiate_formula,
    integrate_formula,
    solve_equation,
    substitute_variables,
    render_latex,
)
from mcp_server.tools.sports_validation import (
    validate_stat_range,
    validate_stat_type,
    get_stat_range,
    validate_formula_inputs,
)


class TestSportsFormulas(unittest.TestCase):
    """Test cases for sports analytics formulas"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_stats = {
            "PTS": 25.0,
            "FGM": 10.0,
            "FGA": 20.0,
            "3PM": 3.0,
            "3PA": 8.0,
            "FTM": 2.0,
            "FTA": 3.0,
            "REB": 8.0,
            "OREB": 3.0,  # Split REB into offensive and defensive
            "DREB": 5.0,
            "AST": 6.0,
            "STL": 2.0,
            "BLK": 1.0,
            "TOV": 3.0,
            "PF": 2.0,
            "MP": 35.0,
            "TM_MP": 240.0,
            "TM_FGA": 90.0,
            "TM_FTA": 25.0,
            "TM_TOV": 12.0,
            "TM_FGM": 35.0,
            "TM_REB": 45.0,
            "OPP_REB": 42.0,
            "OPP_POSS": 100.0,
            "OPP_2PA": 50.0,
        }

    def test_true_shooting_percentage(self):
        """Test True Shooting Percentage calculation"""
        formula = get_sports_formula("true_shooting")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "True Shooting Percentage")

        # Test with known values
        result = calculate_sports_formula("true_shooting", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertGreater(result["result"], 0)
        self.assertLessEqual(result["result"], 1.0)  # Should be a percentage

    def test_player_efficiency_rating(self):
        """Test Player Efficiency Rating calculation"""
        formula = get_sports_formula("per")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Player Efficiency Rating")

        result = calculate_sports_formula("per", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertIsInstance(result["result"], (int, float))

    def test_usage_rate(self):
        """Test Usage Rate calculation"""
        formula = get_sports_formula("usage_rate")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Usage Rate")

        result = calculate_sports_formula("usage_rate", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertGreaterEqual(result["result"], 0)
        self.assertLessEqual(result["result"], 100)  # Should be a percentage

    def test_effective_field_goal_percentage(self):
        """Test Effective Field Goal Percentage calculation"""
        formula = get_sports_formula("effective_fg")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Effective Field Goal Percentage")

        result = calculate_sports_formula("effective_fg", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertGreaterEqual(result["result"], 0)
        self.assertLessEqual(result["result"], 1.0)

    def test_assist_percentage(self):
        """Test Assist Percentage calculation"""
        formula = get_sports_formula("assist_percentage")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Assist Percentage")

        result = calculate_sports_formula("assist_percentage", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertGreaterEqual(result["result"], 0)
        self.assertLessEqual(result["result"], 100)

    def test_rebound_percentage(self):
        """Test Rebound Percentage calculation"""
        formula = get_sports_formula("rebound_percentage")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Rebound Percentage")

        result = calculate_sports_formula("rebound_percentage", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertGreaterEqual(result["result"], 0)
        self.assertLessEqual(result["result"], 100)

    def test_steal_percentage(self):
        """Test Steal Percentage calculation"""
        formula = get_sports_formula("steal_percentage")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Steal Percentage")

        result = calculate_sports_formula("steal_percentage", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertGreaterEqual(result["result"], 0)
        self.assertLessEqual(result["result"], 100)

    def test_block_percentage(self):
        """Test Block Percentage calculation"""
        formula = get_sports_formula("block_percentage")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Block Percentage")

        result = calculate_sports_formula("block_percentage", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertGreaterEqual(result["result"], 0)
        self.assertLessEqual(result["result"], 100)

    def test_turnover_percentage(self):
        """Test Turnover Percentage calculation"""
        formula = get_sports_formula("turnover_percentage")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Turnover Percentage")

        result = calculate_sports_formula("turnover_percentage", self.test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertGreaterEqual(result["result"], 0)
        self.assertLessEqual(result["result"], 100)

    def test_net_rating(self):
        """Test Net Rating calculation"""
        formula = get_sports_formula("net_rating")
        self.assertIsNotNone(formula)
        self.assertEqual(formula["name"], "Net Rating")

        # Add required stats
        test_stats = self.test_stats.copy()
        test_stats["ORtg"] = 115.0
        test_stats["DRtg"] = 108.0

        result = calculate_sports_formula("net_rating", test_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertEqual(result["result"], 7.0)  # 115 - 108 = 7

    def test_invalid_formula_name(self):
        """Test handling of invalid formula names"""
        with self.assertRaises(ValueError):
            get_sports_formula("invalid_formula")

    def test_missing_variables(self):
        """Test handling of missing required variables"""
        incomplete_stats = {"PTS": 25.0, "FGA": 20.0}  # Missing FTA for TS%

        with self.assertRaises(ValueError):
            calculate_sports_formula("true_shooting", incomplete_stats)


class TestFormulaManipulation(unittest.TestCase):
    """Test cases for formula manipulation functions"""

    def test_simplify_formula(self):
        """Test formula simplification"""
        formula = "x**2 + 2*x + 1"
        result = simplify_formula(formula)
        self.assertIsInstance(result, dict)
        self.assertIn("simplified", result)
        self.assertIn("latex", result)

    def test_expand_formula(self):
        """Test formula expansion"""
        formula = "(x + 1)**2"
        result = expand_formula(formula)
        self.assertIsInstance(result, dict)
        self.assertIn("expanded", result)
        self.assertIn("latex", result)

    def test_factor_formula(self):
        """Test formula factoring"""
        formula = "x**2 + 2*x + 1"
        result = factor_formula(formula)
        self.assertIsInstance(result, dict)
        self.assertIn("factored", result)
        self.assertIn("latex", result)

    def test_differentiate_formula(self):
        """Test formula differentiation"""
        formula = "x**2 + 3*x + 1"
        result = differentiate_formula(formula, "x")
        self.assertIsInstance(result, dict)
        self.assertIn("derivative", result)
        self.assertIn("latex", result)

    def test_integrate_formula(self):
        """Test formula integration"""
        formula = "2*x + 3"
        result = integrate_formula(formula, "x")
        self.assertIsInstance(result, dict)
        self.assertIn("integral", result)
        self.assertIn("latex", result)

    def test_solve_equation(self):
        """Test equation solving"""
        equation = "x**2 - 4"
        result = solve_equation(equation, "x")
        self.assertIsInstance(result, dict)
        self.assertIn("solutions", result)
        self.assertIn("latex", result)

    def test_substitute_variables(self):
        """Test variable substitution"""
        formula = "x**2 + y"
        substitutions = {"x": 2, "y": 3}
        result = substitute_variables(formula, substitutions)
        self.assertIsInstance(result, dict)
        self.assertIn("substituted", result)
        self.assertIn("result", result)
        self.assertEqual(result["result"], 7)  # 2**2 + 3 = 7

    def test_render_latex(self):
        """Test LaTeX rendering"""
        formula = "x**2 + 1"
        result = render_latex(formula)
        self.assertIsInstance(result, dict)
        self.assertIn("latex", result)
        self.assertIn("\\", result["latex"])  # Should contain LaTeX commands


class TestSportsValidation(unittest.TestCase):
    """Test cases for sports statistics validation"""

    def test_validate_stat_range(self):
        """Test statistics range validation"""
        # Valid ranges
        self.assertTrue(validate_stat_range("FG%", 0.5))
        self.assertTrue(validate_stat_range("FG%", 0.0))
        self.assertTrue(validate_stat_range("FG%", 1.0))

        # Invalid ranges
        self.assertFalse(validate_stat_range("FG%", 1.5))
        self.assertFalse(validate_stat_range("FG%", -0.1))

        # Valid minutes
        self.assertTrue(validate_stat_range("MP", 35.0))
        self.assertTrue(validate_stat_range("MP", 0.0))
        self.assertTrue(validate_stat_range("MP", 48.0))

        # Invalid minutes
        self.assertFalse(validate_stat_range("MP", 50.0))
        self.assertFalse(validate_stat_range("MP", -5.0))

    def test_validate_stat_type(self):
        """Test statistics type validation"""
        # Valid types
        self.assertTrue(validate_stat_type("PTS", 25))
        self.assertTrue(validate_stat_type("PTS", 25.0))
        self.assertTrue(validate_stat_type("FG%", 0.5))

        # Invalid types
        self.assertFalse(validate_stat_type("PTS", "25"))
        self.assertFalse(validate_stat_type("FG%", "0.5"))
        self.assertFalse(validate_stat_type("PTS", None))

    def test_get_stat_range(self):
        """Test getting statistics ranges"""
        range_info = get_stat_range("FG%")
        self.assertIsInstance(range_info, dict)
        self.assertIn("min", range_info)
        self.assertIn("max", range_info)
        self.assertEqual(range_info["min"], 0.0)
        self.assertEqual(range_info["max"], 1.0)

    def test_validate_formula_inputs(self):
        """Test formula input validation"""
        # Valid inputs
        valid_inputs = {"PTS": 25.0, "FGA": 20.0, "FTA": 5.0}
        result = validate_formula_inputs("true_shooting", valid_inputs)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

        # Invalid inputs
        invalid_inputs = {"PTS": "25", "FGA": 20.0, "FTA": 5.0}  # Wrong type
        result = validate_formula_inputs("true_shooting", invalid_inputs)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)


class TestEdgeCases(unittest.TestCase):
    """Test cases for edge cases and error handling"""

    def test_division_by_zero(self):
        """Test handling of division by zero"""
        # Test with zero FGA (should handle gracefully)
        stats = {"PTS": 25.0, "FGA": 0.0, "FTA": 5.0}

        with self.assertRaises((ValueError, ZeroDivisionError)):
            calculate_sports_formula("true_shooting", stats)

    def test_negative_values(self):
        """Test handling of negative values"""
        # Test with negative points (should be invalid)
        stats = {"PTS": -5.0, "FGA": 20.0, "FTA": 5.0}

        with self.assertRaises(ValueError):
            calculate_sports_formula("true_shooting", stats)

    def test_extreme_values(self):
        """Test handling of extreme values"""
        # Test with very large values
        stats = {"PTS": 1000.0, "FGA": 500.0, "FTA": 100.0}

        result = calculate_sports_formula("true_shooting", stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        # Should still produce a valid result

    def test_malformed_formulas(self):
        """Test handling of malformed formulas"""
        malformed_formulas = [
            "x**",  # Incomplete power
            "x +",  # Incomplete addition
            "**x",  # Invalid syntax
            "",  # Empty string
            "x + y +",  # Trailing operator
        ]

        for formula in malformed_formulas:
            with self.assertRaises((ValueError, SyntaxError)):
                simplify_formula(formula)

    def test_unknown_variables(self):
        """Test handling of unknown variables"""
        formula = "unknown_var + x"

        with self.assertRaises(ValueError):
            substitute_variables(formula, {"x": 2})


class TestPerformance(unittest.TestCase):
    """Test cases for performance benchmarks"""

    def test_formula_calculation_speed(self):
        """Test formula calculation speed"""
        import time

        stats = {
            "PTS": 25.0,
            "FGM": 10.0,
            "FGA": 20.0,
            "3PM": 3.0,
            "3PA": 8.0,
            "FTM": 2.0,
            "FTA": 3.0,
            "REB": 8.0,
            "OREB": 3.0,
            "DREB": 5.0,
            "AST": 6.0,
            "STL": 2.0,
            "BLK": 1.0,
            "TOV": 3.0,
            "PF": 2.0,
            "MP": 35.0,
            "TM_MP": 240.0,
            "TM_FGA": 90.0,
            "TM_FTA": 25.0,
            "TM_TOV": 12.0,
            "TM_FGM": 35.0,
            "TM_REB": 45.0,
            "OPP_REB": 42.0,
            "OPP_POSS": 100.0,
            "OPP_2PA": 50.0,
        }

        # Test multiple calculations
        start_time = time.time()
        for _ in range(100):
            calculate_sports_formula("per", stats)
        end_time = time.time()

        # Should complete 100 calculations in less than 1 second
        self.assertLess(end_time - start_time, 1.0)

    def test_large_formula_simplification(self):
        """Test simplification of large formulas"""
        import time

        # Create a large formula
        large_formula = "x**10 + 2*x**9 + 3*x**8 + 4*x**7 + 5*x**6 + 6*x**5 + 7*x**4 + 8*x**3 + 9*x**2 + 10*x + 11"

        start_time = time.time()
        result = simplify_formula(large_formula)
        end_time = time.time()

        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 5.0)
        self.assertIsInstance(result, dict)


class TestKnownResults(unittest.TestCase):
    """Test cases against known results from published sources"""

    def test_per_known_values(self):
        """Test PER calculation against known values"""
        # LeBron James 2012-13 season (approximate values)
        lebron_stats = {
            "FGM": 765,
            "STL": 103,
            "3PM": 103,
            "FTM": 403,
            "BLK": 56,
            "OREB": 85,
            "AST": 551,
            "DREB": 522,
            "PF": 118,
            "FTA": 492,
            "FGA": 1354,
            "TOV": 280,
            "MP": 2877,
        }

        result = calculate_sports_formula("per", lebron_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        # LeBron's PER was around 31.6 that season
        # Allow some tolerance for approximation
        self.assertGreater(result["result"], 25.0)
        self.assertLess(result["result"], 35.0)

    def test_ts_percentage_known_values(self):
        """Test TS% calculation against known values"""
        # Stephen Curry 2015-16 season (approximate values)
        curry_stats = {
            "PTS": 2375,  # Total points
            "FGA": 1598,  # Total field goal attempts
            "FTA": 400,  # Total free throw attempts
        }

        result = calculate_sports_formula("true_shooting", curry_stats)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        # Curry's TS% was around 0.669 that season
        self.assertGreater(result["result"], 0.6)
        self.assertLess(result["result"], 0.7)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
