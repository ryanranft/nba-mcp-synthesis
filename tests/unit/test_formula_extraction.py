#!/usr/bin/env python3
"""
Unit Tests for Formula Extraction System

This module contains comprehensive unit tests for the Formula Extraction system
that provides automated formula extraction from PDFs and LaTeX conversion.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import unittest
import pytest
import sys
import os
from typing import Dict, Any, List
import tempfile
import json

# Add the project root to the Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mcp_server.tools.formula_extractor import (
    FormulaExtractor,
    extract_formulas_from_pdf,
    convert_latex_to_sympy,
    analyze_formula_structure,
)


class TestFormulaExtractor(unittest.TestCase):
    """Test cases for Formula Extraction system"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = FormulaExtractor()

        # Sample LaTeX formulas for testing
        self.sample_latex_formulas = [
            r"\frac{PTS}{2 \cdot (FGA + 0.44 \cdot FTA)}",  # True Shooting %
            r"\frac{FGM + 0.5 \cdot 3PM}{FGA}",  # Effective FG%
            r"\frac{(FGA + 0.44 \cdot FTA + TOV) \cdot \frac{TM\_MP}{5}}{MP \cdot (TM\_FGA + 0.44 \cdot TM\_FTA + TM\_TOV)} \cdot 100",  # Usage Rate
            r"ORtg - DRtg",  # Net Rating
            r"\frac{FGM \cdot 85.910 + STL \cdot 53.897 + 3PM \cdot 51.757 + FTM \cdot 46.845 + BLK \cdot 39.190 + OREB \cdot 39.190 + AST \cdot 34.677 + DREB \cdot 14.707 - PF \cdot 17.174 - (FTA - FTM) \cdot 20.091 - (FGA - FGM) \cdot 39.190 - TOV \cdot 53.897}{MP}",  # PER
        ]

        # Sample text with formulas
        self.sample_text_with_formulas = """
        The True Shooting Percentage is calculated as:
        TS% = PTS / (2 * (FGA + 0.44 * FTA))
        
        The Effective Field Goal Percentage is:
        eFG% = (FGM + 0.5 * 3PM) / FGA
        
        Player Efficiency Rating formula:
        PER = (FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) / MP
        """

    def test_latex_to_sympy_conversion(self):
        """Test LaTeX to SymPy conversion"""
        for latex_formula in self.sample_latex_formulas:
            result = self.extractor.convert_latex_to_sympy(latex_formula)

            self.assertIsInstance(result, dict)
            self.assertIn("sympy_expression", result)
            self.assertIn("conversion_success", result)
            self.assertIn("confidence", result)
            self.assertIn("variables", result)

            # Should successfully convert most formulas
            if result["conversion_success"]:
                self.assertIsNotNone(result["sympy_expression"])
                self.assertGreater(result["confidence"], 0.0)
                self.assertIsInstance(result["variables"], list)

    def test_formula_extraction_from_text(self):
        """Test formula extraction from text"""
        result = self.extractor.extract_formulas_from_text(
            self.sample_text_with_formulas
        )

        self.assertIsInstance(result, dict)
        self.assertIn("formulas", result)
        self.assertIn("extraction_count", result)
        self.assertIn("confidence_scores", result)

        # Should extract multiple formulas
        self.assertGreater(result["extraction_count"], 0)
        self.assertIsInstance(result["formulas"], list)
        self.assertIsInstance(result["confidence_scores"], list)

        # Check that extracted formulas are reasonable
        for formula in result["formulas"]:
            self.assertIsInstance(formula, dict)
            self.assertIn("formula_text", formula)
            self.assertIn("formula_type", formula)
            self.assertIn("confidence", formula)
            self.assertIn("variables", formula)

    def test_formula_structure_analysis(self):
        """Test formula structure analysis"""
        test_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",  # Simple division
            "(FGM + 0.5 * 3PM) / FGA",  # Addition and division
            "FGM * 85.910 + STL * 53.897 + 3PM * 51.757",  # Multiple multiplications
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",  # Complex nested
        ]

        for formula in test_formulas:
            result = self.extractor.analyze_formula_structure(formula)

            self.assertIsInstance(result, dict)
            self.assertIn("structure_type", result)
            self.assertIn("complexity_score", result)
            self.assertIn("variable_count", result)
            self.assertIn("operation_count", result)
            self.assertIn("nested_levels", result)
            self.assertIn("formula_components", result)

            # Check that analysis is reasonable
            self.assertGreaterEqual(result["complexity_score"], 0.0)
            self.assertLessEqual(result["complexity_score"], 1.0)
            self.assertGreaterEqual(result["variable_count"], 0)
            self.assertGreaterEqual(result["operation_count"], 0)
            self.assertGreaterEqual(result["nested_levels"], 0)
            self.assertIsInstance(result["formula_components"], list)

    def test_pattern_recognition(self):
        """Test pattern recognition for common formula types"""
        # Test efficiency patterns
        efficiency_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",  # TS%
            "(FGM + 0.5 * 3PM) / FGA",  # eFG%
            "FGM / FGA",  # FG%
        ]

        for formula in efficiency_formulas:
            result = self.extractor.analyze_formula_structure(formula)
            # Should recognize as efficiency-type formula
            self.assertIn("efficiency", result["structure_type"].lower())

        # Test rate patterns
        rate_formulas = [
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",  # Usage Rate
            "(AST * (TM_MP / 5)) / (MP * (TM_FGM - FGM)) * 100",  # Assist %
        ]

        for formula in rate_formulas:
            result = self.extractor.analyze_formula_structure(formula)
            # Should recognize as rate-type formula
            self.assertIn("rate", result["structure_type"].lower())

        # Test composite patterns
        composite_formulas = [
            "FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897",  # PER components
        ]

        for formula in composite_formulas:
            result = self.extractor.analyze_formula_structure(formula)
            # Should recognize as composite-type formula
            self.assertIn("composite", result["structure_type"].lower())

    def test_variable_extraction(self):
        """Test variable extraction from formulas"""
        test_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",
            "(FGM + 0.5 * 3PM) / FGA",
            "FGM * 85.910 + STL * 53.897 + 3PM * 51.757",
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
        ]

        expected_variables = [
            ["PTS", "FGA", "FTA"],
            ["FGM", "3PM", "FGA"],
            ["FGM", "STL", "3PM"],
            ["FGA", "FTA", "TOV", "TM_MP", "MP", "TM_FGA", "TM_FTA", "TM_TOV"],
        ]

        for formula, expected_vars in zip(test_formulas, expected_variables):
            result = self.extractor.analyze_formula_structure(formula)

            self.assertIsInstance(result["formula_components"], list)
            # Should extract variables correctly
            extracted_vars = [
                comp["name"]
                for comp in result["formula_components"]
                if comp["type"] == "variable"
            ]

            for expected_var in expected_vars:
                self.assertIn(expected_var, extracted_vars)

    def test_confidence_scoring(self):
        """Test confidence scoring for formula extraction"""
        # High confidence formulas (clear patterns)
        high_confidence_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",  # Clear TS% pattern
            "(FGM + 0.5 * 3PM) / FGA",  # Clear eFG% pattern
            "FGM / FGA",  # Simple FG% pattern
        ]

        for formula in high_confidence_formulas:
            result = self.extractor.analyze_formula_structure(formula)
            # Should have high confidence for clear patterns
            self.assertGreaterEqual(result.get("confidence", 0), 0.7)

        # Medium confidence formulas (complex but recognizable)
        medium_confidence_formulas = [
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",  # Usage Rate
            "(AST * (TM_MP / 5)) / (MP * (TM_FGM - FGM)) * 100",  # Assist %
        ]

        for formula in medium_confidence_formulas:
            result = self.extractor.analyze_formula_structure(formula)
            # Should have medium confidence for complex patterns
            self.assertGreaterEqual(result.get("confidence", 0), 0.4)

    def test_error_handling(self):
        """Test error handling for malformed inputs"""
        malformed_inputs = [
            "",  # Empty string
            "x**",  # Incomplete power
            "x +",  # Incomplete addition
            "**x",  # Invalid syntax
            "x + y +",  # Trailing operator
        ]

        for malformed_input in malformed_inputs:
            # Should handle gracefully or raise appropriate error
            try:
                result = self.extractor.analyze_formula_structure(malformed_input)
                # If it doesn't raise an error, should return a valid result
                self.assertIsInstance(result, dict)
                self.assertIn("structure_type", result)
            except (ValueError, SyntaxError):
                # Expected for malformed inputs
                pass

    def test_latex_special_characters(self):
        """Test handling of LaTeX special characters"""
        latex_with_special_chars = [
            r"\frac{PTS}{2 \cdot (FGA + 0.44 \cdot FTA)}",  # \cdot
            r"\frac{FGM + 0.5 \cdot 3PM}{FGA}",  # \cdot
            r"ORtg - DRtg",  # Underscores
            r"TM\_MP",  # Escaped underscores
        ]

        for latex_formula in latex_with_special_chars:
            result = self.extractor.convert_latex_to_sympy(latex_formula)

            self.assertIsInstance(result, dict)
            self.assertIn("sympy_expression", result)
            self.assertIn("conversion_success", result)

            # Should handle special characters gracefully
            if result["conversion_success"]:
                self.assertIsNotNone(result["sympy_expression"])

    def test_complex_nested_formulas(self):
        """Test handling of complex nested formulas"""
        complex_formula = "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100"

        result = self.extractor.analyze_formula_structure(complex_formula)

        self.assertIsInstance(result, dict)
        self.assertIn("structure_type", result)
        self.assertIn("complexity_score", result)
        self.assertIn("nested_levels", result)

        # Should recognize as complex
        self.assertGreater(result["complexity_score"], 0.7)
        self.assertGreater(result["nested_levels"], 2)
        self.assertGreater(result["operation_count"], 5)

    def test_performance(self):
        """Test performance for large formulas"""
        import time

        # Create a large formula
        large_formula = "PTS + AST + REB + STL + BLK - TOV - PF + FGM + FGA + 3PM + 3PA + FTM + FTA + OREB + DREB + MP + TM_MP + TM_FGA + TM_FTA + TM_TOV + TM_FGM + TM_REB + OPP_REB + OPP_POSS + OPP_2PA"

        start_time = time.time()
        result = self.extractor.analyze_formula_structure(large_formula)
        end_time = time.time()

        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0)
        self.assertIsInstance(result, dict)
        self.assertIn("structure_type", result)

    def test_integration_with_formula_intelligence(self):
        """Test integration with Formula Intelligence system"""
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        # Test that extraction works with intelligence system
        structure_result = self.extractor.analyze_formula_structure(formula)

        self.assertIsInstance(structure_result, dict)
        self.assertIn("structure_type", structure_result)
        self.assertIn("complexity_score", structure_result)

        # Test LaTeX conversion
        latex_formula = r"\frac{PTS}{2 \cdot (FGA + 0.44 \cdot FTA)}"
        conversion_result = self.extractor.convert_latex_to_sympy(latex_formula)

        self.assertIsInstance(conversion_result, dict)
        self.assertIn("sympy_expression", conversion_result)
        self.assertIn("conversion_success", conversion_result)

    def test_formula_extraction_from_pdf_simulation(self):
        """Test formula extraction simulation (without actual PDF)"""
        # Simulate PDF text extraction
        pdf_text = """
        Chapter 3: Advanced Metrics
        
        The True Shooting Percentage is calculated as:
        TS% = PTS / (2 * (FGA + 0.44 * FTA))
        
        This formula accounts for the value of three-pointers and free throws.
        
        The Effective Field Goal Percentage is:
        eFG% = (FGM + 0.5 * 3PM) / FGA
        
        This adjusts field goal percentage for the value of three-pointers.
        """

        result = self.extractor.extract_formulas_from_text(pdf_text)

        self.assertIsInstance(result, dict)
        self.assertIn("formulas", result)
        self.assertIn("extraction_count", result)

        # Should extract at least 2 formulas
        self.assertGreaterEqual(result["extraction_count"], 2)
        self.assertIsInstance(result["formulas"], list)

        # Check extracted formulas
        for formula in result["formulas"]:
            self.assertIsInstance(formula, dict)
            self.assertIn("formula_text", formula)
            self.assertIn("formula_type", formula)
            self.assertIn("confidence", formula)


class TestFormulaExtractionIntegration(unittest.TestCase):
    """Test cases for integration with other systems"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = FormulaExtractor()

    def test_extraction_with_validation(self):
        """Test extraction with formula validation"""
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        # Extract structure
        structure = self.extractor.analyze_formula_structure(formula)

        # Validate extraction
        self.assertIsInstance(structure, dict)
        self.assertIn("structure_type", structure)
        self.assertIn("confidence", structure)

        # Should have reasonable confidence
        self.assertGreaterEqual(structure["confidence"], 0.0)
        self.assertLessEqual(structure["confidence"], 1.0)

    def test_extraction_with_sports_context(self):
        """Test extraction with sports analytics context"""
        sports_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",  # TS%
            "(FGM + 0.5 * 3PM) / FGA",  # eFG%
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",  # Usage Rate
            "ORtg - DRtg",  # Net Rating
        ]

        for formula in sports_formulas:
            result = self.extractor.analyze_formula_structure(formula)

            # Should extract sports-related information
            self.assertIsInstance(result, dict)
            self.assertIn("structure_type", result)
            self.assertIn("variable_count", result)

            # Should identify variables correctly
            self.assertGreater(result["variable_count"], 0)

    def test_extraction_with_latex_conversion(self):
        """Test extraction with LaTeX conversion"""
        latex_formulas = [
            r"\frac{PTS}{2 \cdot (FGA + 0.44 \cdot FTA)}",
            r"\frac{FGM + 0.5 \cdot 3PM}{FGA}",
            r"ORtg - DRtg",
        ]

        for latex_formula in latex_formulas:
            # Convert LaTeX to SymPy
            conversion_result = self.extractor.convert_latex_to_sympy(latex_formula)

            self.assertIsInstance(conversion_result, dict)
            self.assertIn("sympy_expression", conversion_result)
            self.assertIn("conversion_success", conversion_result)

            # If conversion successful, analyze structure
            if conversion_result["conversion_success"]:
                sympy_expr = conversion_result["sympy_expression"]
                structure_result = self.extractor.analyze_formula_structure(
                    str(sympy_expr)
                )

                self.assertIsInstance(structure_result, dict)
                self.assertIn("structure_type", structure_result)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
