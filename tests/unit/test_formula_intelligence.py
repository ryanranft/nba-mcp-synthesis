#!/usr/bin/env python3
"""
Unit Tests for Formula Intelligence System

This module contains comprehensive unit tests for the Formula Intelligence system
that provides context-aware formula recognition, tool suggestions, and validation.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import unittest
import pytest
import sys
import os
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mcp_server.tools.formula_intelligence import (
    FormulaIntelligence,
    FormulaType,
    identify_formula_type,
    suggest_tools,
    map_variables,
    validate_units,
    analyze_comprehensive,
    get_recommendations,
)


class TestFormulaIntelligence(unittest.TestCase):
    """Test cases for Formula Intelligence system"""

    def setUp(self):
        """Set up test fixtures"""
        self.intelligence = FormulaIntelligence()

        # Test formulas
        self.test_formulas = {
            "true_shooting": "PTS / (2 * (FGA + 0.44 * FTA))",
            "per": "(FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
            "usage_rate": "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            "net_rating": "ORtg - DRtg",
            "effective_fg": "(FGM + 0.5 * 3PM) / FGA",
            "assist_percentage": "(AST * (TM_MP / 5)) / (MP * (TM_FGM - FGM)) * 100",
            "rebound_percentage": "(REB * (TM_MP / 5)) / (MP * (TM_REB + OPP_REB)) * 100",
            "steal_percentage": "(STL * (TM_MP / 5)) / (MP * OPP_POSS) * 100",
            "block_percentage": "(BLK * (TM_MP / 5)) / (MP * OPP_2PA) * 100",
            "turnover_percentage": "(TOV * (TM_MP / 5)) / (MP * (FGA + 0.44 * FTA + TOV)) * 100",
        }

    def test_formula_type_identification(self):
        """Test formula type identification"""
        # Test efficiency formulas
        ts_type, confidence = self.intelligence.identify_formula_type(
            self.test_formulas["true_shooting"]
        )
        self.assertEqual(ts_type, FormulaType.EFFICIENCY)
        self.assertGreater(confidence, 0.7)

        efg_type, confidence = self.intelligence.identify_formula_type(
            self.test_formulas["effective_fg"]
        )
        self.assertEqual(efg_type, FormulaType.EFFICIENCY)
        self.assertGreater(confidence, 0.7)

        # Test rate formulas
        usage_type, confidence = self.intelligence.identify_formula_type(
            self.test_formulas["usage_rate"]
        )
        self.assertEqual(usage_type, FormulaType.RATE)
        self.assertGreater(confidence, 0.7)

        ast_type, confidence = self.intelligence.identify_formula_type(
            self.test_formulas["assist_percentage"]
        )
        self.assertEqual(ast_type, FormulaType.RATE)
        self.assertGreater(confidence, 0.7)

        # Test composite formulas
        per_type, confidence = self.intelligence.identify_formula_type(
            self.test_formulas["per"]
        )
        self.assertEqual(per_type, FormulaType.COMPOSITE)
        self.assertGreater(confidence, 0.7)

        # Test differential formulas
        net_type, confidence = self.intelligence.identify_formula_type(
            self.test_formulas["net_rating"]
        )
        self.assertEqual(net_type, FormulaType.DIFFERENTIAL)
        self.assertGreater(confidence, 0.7)

    def test_tool_suggestions(self):
        """Test tool suggestion functionality"""
        # Test efficiency formula suggestions
        ts_suggestions = self.intelligence.suggest_tools(
            self.test_formulas["true_shooting"]
        )
        self.assertIsInstance(ts_suggestions, list)
        self.assertGreater(len(ts_suggestions), 0)
        self.assertIn("algebra_sports_formula", ts_suggestions)

        # Test composite formula suggestions
        per_suggestions = self.intelligence.suggest_tools(self.test_formulas["per"])
        self.assertIsInstance(per_suggestions, list)
        self.assertGreater(len(per_suggestions), 0)
        self.assertIn("algebra_sports_formula", per_suggestions)

        # Test rate formula suggestions
        usage_suggestions = self.intelligence.suggest_tools(
            self.test_formulas["usage_rate"]
        )
        self.assertIsInstance(usage_suggestions, list)
        self.assertGreater(len(usage_suggestions), 0)
        self.assertIn("algebra_sports_formula", usage_suggestions)

    def test_variable_mapping(self):
        """Test variable mapping functionality"""
        # Test standard NBA variables
        ts_mapping = self.intelligence.map_variables(
            self.test_formulas["true_shooting"]
        )
        self.assertIsInstance(ts_mapping, dict)
        self.assertIn("PTS", ts_mapping)
        self.assertIn("FGA", ts_mapping)
        self.assertIn("FTA", ts_mapping)

        # Test complex formula variables
        per_mapping = self.intelligence.map_variables(self.test_formulas["per"])
        self.assertIsInstance(per_mapping, dict)
        self.assertIn("FGM", per_mapping)
        self.assertIn("STL", per_mapping)
        self.assertIn("MP", per_mapping)

        # Test rate formula variables
        usage_mapping = self.intelligence.map_variables(
            self.test_formulas["usage_rate"]
        )
        self.assertIsInstance(usage_mapping, dict)
        self.assertIn("FGA", usage_mapping)
        self.assertIn("FTA", usage_mapping)
        self.assertIn("TOV", usage_mapping)
        self.assertIn("MP", usage_mapping)
        self.assertIn("TM_MP", usage_mapping)

    def test_unit_validation(self):
        """Test unit validation functionality"""
        # Test efficiency formula units
        ts_units = self.intelligence.validate_units(
            {
                "formula": self.test_formulas["true_shooting"],
                "variables": {"PTS": "points", "FGA": "attempts", "FTA": "attempts"},
            }
        )
        self.assertIsInstance(ts_units, dict)
        self.assertIn("is_valid", ts_units)
        self.assertIn("unit_analysis", ts_units)

        # Test rate formula units
        usage_units = self.intelligence.validate_units(
            {
                "formula": self.test_formulas["usage_rate"],
                "variables": {
                    "FGA": "attempts",
                    "FTA": "attempts",
                    "TOV": "turnovers",
                    "MP": "minutes",
                    "TM_MP": "minutes",
                    "TM_FGA": "attempts",
                    "TM_FTA": "attempts",
                    "TM_TOV": "turnovers",
                },
            }
        )
        self.assertIsInstance(usage_units, dict)
        self.assertIn("is_valid", usage_units)
        self.assertIn("unit_analysis", usage_units)

    def test_comprehensive_analysis(self):
        """Test comprehensive formula analysis"""
        analysis = self.intelligence.analyze_comprehensive(
            self.test_formulas["true_shooting"]
        )

        self.assertIsInstance(analysis, dict)
        self.assertIn("formula_type", analysis)
        self.assertIn("confidence", analysis)
        self.assertIn("suggested_tools", analysis)
        self.assertIn("variable_mapping", analysis)
        self.assertIn("unit_validation", analysis)
        self.assertIn("complexity_score", analysis)
        self.assertIn("recommendations", analysis)

        # Check that all components are present
        self.assertIsInstance(analysis["formula_type"], FormulaType)
        self.assertIsInstance(analysis["confidence"], float)
        self.assertIsInstance(analysis["suggested_tools"], list)
        self.assertIsInstance(analysis["variable_mapping"], dict)
        self.assertIsInstance(analysis["unit_validation"], dict)
        self.assertIsInstance(analysis["complexity_score"], float)
        self.assertIsInstance(analysis["recommendations"], list)

    def test_recommendations(self):
        """Test recommendation system"""
        recommendations = self.intelligence.get_recommendations(
            self.test_formulas["true_shooting"], context="shooting efficiency"
        )

        self.assertIsInstance(recommendations, dict)
        self.assertIn("formula_analysis", recommendations)
        self.assertIn("suggested_improvements", recommendations)
        self.assertIn("related_formulas", recommendations)
        self.assertIn("best_practices", recommendations)
        self.assertIn("common_pitfalls", recommendations)

        # Check that all components are present
        self.assertIsInstance(recommendations["formula_analysis"], dict)
        self.assertIsInstance(recommendations["suggested_improvements"], list)
        self.assertIsInstance(recommendations["related_formulas"], list)
        self.assertIsInstance(recommendations["best_practices"], list)
        self.assertIsInstance(recommendations["common_pitfalls"], list)


class TestFormulaTypeEnum(unittest.TestCase):
    """Test cases for FormulaType enum"""

    def test_formula_type_values(self):
        """Test FormulaType enum values"""
        self.assertEqual(FormulaType.EFFICIENCY.value, "efficiency")
        self.assertEqual(FormulaType.RATE.value, "rate")
        self.assertEqual(FormulaType.COMPOSITE.value, "composite")
        self.assertEqual(FormulaType.DIFFERENTIAL.value, "differential")
        self.assertEqual(FormulaType.OTHER.value, "other")

    def test_formula_type_membership(self):
        """Test FormulaType enum membership"""
        self.assertIn(FormulaType.EFFICIENCY, FormulaType)
        self.assertIn(FormulaType.RATE, FormulaType)
        self.assertIn(FormulaType.COMPOSITE, FormulaType)
        self.assertIn(FormulaType.DIFFERENTIAL, FormulaType)
        self.assertIn(FormulaType.OTHER, FormulaType)


class TestEdgeCases(unittest.TestCase):
    """Test cases for edge cases and error handling"""

    def setUp(self):
        """Set up test fixtures"""
        self.intelligence = FormulaIntelligence()

    def test_empty_formula(self):
        """Test handling of empty formulas"""
        with self.assertRaises(ValueError):
            self.intelligence.identify_formula_type("")

    def test_malformed_formula(self):
        """Test handling of malformed formulas"""
        malformed_formulas = [
            "x**",  # Incomplete power
            "x +",  # Incomplete addition
            "**x",  # Invalid syntax
            "x + y +",  # Trailing operator
        ]

        for formula in malformed_formulas:
            # Should handle gracefully or raise appropriate error
            try:
                result = self.intelligence.identify_formula_type(formula)
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)
            except (ValueError, SyntaxError):
                # Expected for malformed formulas
                pass

    def test_unknown_variables(self):
        """Test handling of unknown variables"""
        formula_with_unknown = "unknown_var + PTS"

        # Should handle unknown variables gracefully
        mapping = self.intelligence.map_variables(formula_with_unknown)
        self.assertIsInstance(mapping, dict)
        # Should still map known variables
        self.assertIn("PTS", mapping)

    def test_complex_nested_formula(self):
        """Test handling of complex nested formulas"""
        complex_formula = (
            "((PTS + AST) * (FGM / FGA)) / (MP / 48) + (STL + BLK) / (TOV + 1)"
        )

        # Should handle complex formulas
        analysis = self.intelligence.analyze_comprehensive(complex_formula)
        self.assertIsInstance(analysis, dict)
        self.assertIn("formula_type", analysis)
        self.assertIn("complexity_score", analysis)
        self.assertGreater(analysis["complexity_score"], 0.5)  # Should be complex

    def test_formula_with_constants(self):
        """Test handling of formulas with constants"""
        formula_with_constants = "PTS * 0.44 + FGA * 2.0 + FTA * 1.0"

        analysis = self.intelligence.analyze_comprehensive(formula_with_constants)
        self.assertIsInstance(analysis, dict)
        self.assertIn("formula_type", analysis)
        self.assertIn("variable_mapping", analysis)

        # Should identify variables correctly
        mapping = analysis["variable_mapping"]
        self.assertIn("PTS", mapping)
        self.assertIn("FGA", mapping)
        self.assertIn("FTA", mapping)


class TestPerformance(unittest.TestCase):
    """Test cases for performance benchmarks"""

    def setUp(self):
        """Set up test fixtures"""
        self.intelligence = FormulaIntelligence()

    def test_analysis_speed(self):
        """Test analysis speed for typical formulas"""
        import time

        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        start_time = time.time()
        for _ in range(100):
            self.intelligence.analyze_comprehensive(formula)
        end_time = time.time()

        # Should complete 100 analyses in less than 2 seconds
        self.assertLess(end_time - start_time, 2.0)

    def test_large_formula_analysis(self):
        """Test analysis of large formulas"""
        import time

        # Create a large formula
        large_formula = "PTS + AST + REB + STL + BLK - TOV - PF + FGM + FGA + 3PM + 3PA + FTM + FTA + OREB + DREB + MP + TM_MP + TM_FGA + TM_FTA + TM_TOV + TM_FGM + TM_REB + OPP_REB + OPP_POSS + OPP_2PA"

        start_time = time.time()
        analysis = self.intelligence.analyze_comprehensive(large_formula)
        end_time = time.time()

        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0)
        self.assertIsInstance(analysis, dict)


class TestIntegration(unittest.TestCase):
    """Test cases for integration with other systems"""

    def setUp(self):
        """Set up test fixtures"""
        self.intelligence = FormulaIntelligence()

    def test_formula_intelligence_integration(self):
        """Test integration with formula intelligence system"""
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        # Test that all components work together
        analysis = self.intelligence.analyze_comprehensive(formula)

        # Verify integration
        self.assertIsInstance(analysis["formula_type"], FormulaType)
        self.assertIsInstance(analysis["suggested_tools"], list)
        self.assertIsInstance(analysis["variable_mapping"], dict)
        self.assertIsInstance(analysis["unit_validation"], dict)

        # Test recommendations integration
        recommendations = self.intelligence.get_recommendations(formula, "shooting")
        self.assertIsInstance(recommendations, dict)
        self.assertIn("formula_analysis", recommendations)

    def test_sports_context_integration(self):
        """Test integration with sports analytics context"""
        sports_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",  # TS%
            "(FGM + 0.5 * 3PM) / FGA",  # eFG%
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",  # Usage Rate
            "ORtg - DRtg",  # Net Rating
        ]

        for formula in sports_formulas:
            analysis = self.intelligence.analyze_comprehensive(formula)

            # Should identify as sports-related
            self.assertIsInstance(analysis["formula_type"], FormulaType)
            self.assertGreater(
                analysis["confidence"], 0.3
            )  # Should have some confidence

            # Should provide sports-specific recommendations
            recommendations = self.intelligence.get_recommendations(
                formula, "basketball"
            )
            self.assertIsInstance(recommendations, dict)
            self.assertIn("best_practices", recommendations)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
