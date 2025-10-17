#!/usr/bin/env python3
"""
Unit Tests for Interactive Formula Builder

This module contains comprehensive unit tests for the Interactive Formula Builder
system that provides real-time validation, suggestions, and template management.

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

from mcp_server.tools.formula_builder import (
    InteractiveFormulaBuilder,
    FormulaComponent,
    FormulaTemplate,
    FormulaValidation,
    FormulaComponentType,
    ValidationLevel,
)


class TestInteractiveFormulaBuilder(unittest.TestCase):
    """Test cases for Interactive Formula Builder system"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = InteractiveFormulaBuilder()

        # Test formulas
        self.test_formulas = {
            "simple": "PTS / (2 * (FGA + 0.44 * FTA))",
            "complex": "(FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) / MP",
            "rate": "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            "differential": "ORtg - DRtg",
            "invalid": "PTS / (2 * (FGA +",  # Incomplete
        }

        # Test variable values
        self.test_values = {
            "PTS": 25.0,
            "FGA": 15.0,
            "FTA": 6.0,
            "FGM": 8.0,
            "3PM": 2.0,
            "FTM": 5.0,
            "BLK": 1.0,
            "OREB": 1.0,
            "AST": 8.0,
            "DREB": 7.0,
            "PF": 2.0,
            "TOV": 3.0,
            "MP": 38.0,
            "TM_MP": 240.0,
            "TM_FGA": 90.0,
            "TM_FTA": 25.0,
            "TM_TOV": 12.0,
            "TM_FGM": 35.0,
            "TM_REB": 45.0,
            "OPP_REB": 42.0,
            "OPP_POSS": 100.0,
            "OPP_2PA": 50.0,
            "STL": 2.0,
            "ORtg": 115.0,
            "DRtg": 108.0,
        }

    def test_formula_parsing(self):
        """Test formula parsing into components"""
        formula = self.test_formulas["simple"]
        components = self.builder.parse_formula(formula)

        self.assertIsInstance(components, list)
        self.assertGreater(len(components), 0)

        # Check component types
        for component in components:
            self.assertIsInstance(component, FormulaComponent)
            self.assertIsInstance(component.type, FormulaComponentType)
            self.assertIsInstance(component.value, str)
            self.assertIsInstance(component.position, int)
            self.assertIsInstance(component.metadata, dict)

    def test_formula_validation_syntax(self):
        """Test syntax validation"""
        # Valid formula
        result = self.builder.validate_formula(
            self.test_formulas["simple"], ValidationLevel.SYNTAX
        )

        self.assertIsInstance(result, FormulaValidation)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(result.confidence, 0.8)

        # Invalid formula
        result = self.builder.validate_formula(
            self.test_formulas["invalid"], ValidationLevel.SYNTAX
        )

        self.assertIsInstance(result, FormulaValidation)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertLess(result.confidence, 0.8)

    def test_formula_validation_semantic(self):
        """Test semantic validation"""
        result = self.builder.validate_formula(
            self.test_formulas["simple"], ValidationLevel.SEMANTIC
        )

        self.assertIsInstance(result, FormulaValidation)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(result.confidence, 0.7)

    def test_formula_validation_sports_context(self):
        """Test sports context validation"""
        result = self.builder.validate_formula(
            self.test_formulas["simple"], ValidationLevel.SPORTS_CONTEXT
        )

        self.assertIsInstance(result, FormulaValidation)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(result.confidence, 0.6)

    def test_formula_validation_units(self):
        """Test units validation"""
        result = self.builder.validate_formula(
            self.test_formulas["simple"], ValidationLevel.UNITS
        )

        self.assertIsInstance(result, FormulaValidation)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(result.confidence, 0.5)

    def test_completion_suggestions(self):
        """Test completion suggestions"""
        # Test initial suggestions
        suggestions = self.builder.suggest_completion("", "")
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

        # Test partial formula suggestions
        suggestions = self.builder.suggest_completion("PTS / (2 * (FGA +", "shooting")
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

        # Should include relevant suggestions
        suggestion_texts = [s.lower() for s in suggestions]
        self.assertTrue(
            any("0.44" in s or "fta" in s or ")" in s for s in suggestion_texts)
        )

    def test_formula_preview(self):
        """Test formula preview generation"""
        formula = self.test_formulas["simple"]

        # Test preview without values
        preview = self.builder.get_formula_preview(formula)

        self.assertIsInstance(preview, dict)
        self.assertIn("formula", preview)
        self.assertIn("latex", preview)
        self.assertIn("simplified", preview)
        self.assertIn("variables", preview)
        self.assertIn("calculated_value", preview)

        self.assertEqual(preview["formula"], formula)
        self.assertIsNotNone(preview["latex"])
        self.assertIsNotNone(preview["simplified"])
        self.assertIsInstance(preview["variables"], list)
        self.assertIsNone(preview["calculated_value"])  # No values provided

        # Test preview with values
        preview_with_values = self.builder.get_formula_preview(
            formula, self.test_values
        )

        self.assertIsInstance(preview_with_values, dict)
        self.assertIn("calculated_value", preview_with_values)
        self.assertIsNotNone(preview_with_values["calculated_value"])
        self.assertIsInstance(preview_with_values["calculated_value"], float)

    def test_template_management(self):
        """Test template management"""
        # Test getting all templates
        all_templates = self.builder.get_available_templates()
        self.assertIsInstance(all_templates, list)
        self.assertGreater(len(all_templates), 0)

        # Test getting templates by category
        shooting_templates = self.builder.get_available_templates("shooting")
        self.assertIsInstance(shooting_templates, list)
        self.assertGreater(len(shooting_templates), 0)

        # Check template structure
        for template in all_templates:
            self.assertIsInstance(template, FormulaTemplate)
            self.assertIsInstance(template.name, str)
            self.assertIsInstance(template.description, str)
            self.assertIsInstance(template.template, str)
            self.assertIsInstance(template.variables, list)
            self.assertIsInstance(template.category, str)

    def test_template_creation(self):
        """Test template-based formula creation"""
        template_name = "True Shooting Percentage"
        variable_values = {"PTS": 25.0, "FGA": 15.0, "FTA": 6.0}

        result = self.builder.create_formula_from_template(
            template_name, variable_values
        )

        self.assertIsInstance(result, dict)
        self.assertIn("template_name", result)
        self.assertIn("formula", result)
        self.assertIn("substituted_formula", result)
        self.assertIn("result", result)
        self.assertIn("variables_used", result)
        self.assertIn("description", result)

        self.assertEqual(result["template_name"], template_name)
        self.assertIsNotNone(result["result"])
        self.assertIsInstance(result["result"], float)
        self.assertEqual(result["variables_used"], variable_values)

    def test_formula_export(self):
        """Test formula export functionality"""
        formula = self.test_formulas["simple"]

        # Test LaTeX export
        latex_export = self.builder.export_formula(formula, "latex")
        self.assertIsInstance(latex_export, str)
        self.assertIn("\\", latex_export)  # Should contain LaTeX commands

        # Test Python export
        python_export = self.builder.export_formula(formula, "python")
        self.assertIsInstance(python_export, str)
        self.assertIn("PTS", python_export)  # Should contain variables

        # Test SymPy export
        sympy_export = self.builder.export_formula(formula, "sympy")
        self.assertIsInstance(sympy_export, str)
        self.assertIn("PTS", sympy_export)  # Should contain variables

        # Test JSON export
        json_export = self.builder.export_formula(formula, "json")
        self.assertIsInstance(json_export, str)
        # Should be valid JSON
        import json

        parsed_json = json.loads(json_export)
        self.assertIsInstance(parsed_json, dict)
        self.assertIn("formula", parsed_json)

    def test_variable_validation(self):
        """Test variable validation"""
        # Test valid variables
        valid_variables = [
            "PTS",
            "FGA",
            "FTA",
            "FGM",
            "3PM",
            "FTM",
            "BLK",
            "OREB",
            "AST",
            "DREB",
        ]

        for var in valid_variables:
            self.assertIn(var, self.builder.variable_info)
            var_info = self.builder.variable_info[var]
            self.assertIn("description", var_info)
            self.assertIn("range", var_info)
            self.assertIn("unit", var_info)

        # Test variable ranges
        pts_info = self.builder.variable_info["PTS"]
        pts_range = pts_info["range"]
        self.assertIsInstance(pts_range, tuple)
        self.assertEqual(len(pts_range), 2)
        self.assertLess(pts_range[0], pts_range[1])

    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test invalid formula names
        with self.assertRaises(ValueError):
            self.builder.create_formula_from_template("Invalid Template", {})

        # Test invalid export format
        with self.assertRaises(ValueError):
            self.builder.export_formula("PTS / FGA", "invalid_format")

        # Test invalid variable values
        invalid_values = {"PTS": -5.0, "FGA": 20.0, "FTA": 5.0}  # Negative PTS
        result = self.builder.create_formula_from_template(
            "True Shooting Percentage", invalid_values
        )
        self.assertIn("error", result)

    def test_complex_formula_handling(self):
        """Test handling of complex formulas"""
        complex_formula = self.test_formulas["complex"]

        # Test parsing
        components = self.builder.parse_formula(complex_formula)
        self.assertIsInstance(components, list)
        self.assertGreater(len(components), 10)  # Should have many components

        # Test validation
        result = self.builder.validate_formula(
            complex_formula, ValidationLevel.SEMANTIC
        )
        self.assertIsInstance(result, FormulaValidation)
        self.assertTrue(result.is_valid)

        # Test preview
        preview = self.builder.get_formula_preview(complex_formula)
        self.assertIsInstance(preview, dict)
        self.assertIn("variables", preview)
        self.assertGreater(len(preview["variables"]), 5)  # Should have many variables

    def test_performance(self):
        """Test performance for large formulas"""
        import time

        # Test parsing performance
        start_time = time.time()
        for _ in range(100):
            self.builder.parse_formula(self.test_formulas["simple"])
        end_time = time.time()

        # Should complete 100 parses in less than 1 second
        self.assertLess(end_time - start_time, 1.0)

        # Test validation performance
        start_time = time.time()
        for _ in range(100):
            self.builder.validate_formula(
                self.test_formulas["simple"], ValidationLevel.SYNTAX
            )
        end_time = time.time()

        # Should complete 100 validations in less than 2 seconds
        self.assertLess(end_time - start_time, 2.0)

    def test_integration_with_formula_intelligence(self):
        """Test integration with Formula Intelligence system"""
        formula = self.test_formulas["simple"]

        # Test that builder works with intelligence system
        validation_result = self.builder.validate_formula(
            formula, ValidationLevel.SPORTS_CONTEXT
        )

        self.assertIsInstance(validation_result, FormulaValidation)
        self.assertTrue(validation_result.is_valid)

        # Test suggestions integration
        suggestions = self.builder.suggest_completion(
            "PTS / (2 * (FGA +", "shooting efficiency"
        )

        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

    def test_template_categories(self):
        """Test template categories"""
        categories = ["shooting", "advanced", "defensive", "team"]

        for category in categories:
            templates = self.builder.get_available_templates(category)
            self.assertIsInstance(templates, list)

            # Check that all templates in category have correct category
            for template in templates:
                self.assertEqual(template.category.lower(), category.lower())

    def test_formula_component_types(self):
        """Test formula component type classification"""
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"
        components = self.builder.parse_formula(formula)

        # Check component types
        component_types = [comp.type for comp in components]

        self.assertIn(FormulaComponentType.VARIABLE, component_types)
        self.assertIn(FormulaComponentType.OPERATOR, component_types)
        self.assertIn(FormulaComponentType.CONSTANT, component_types)
        self.assertIn(FormulaComponentType.PARENTHESIS, component_types)

    def test_validation_levels(self):
        """Test all validation levels"""
        formula = self.test_formulas["simple"]

        levels = [
            ValidationLevel.SYNTAX,
            ValidationLevel.SEMANTIC,
            ValidationLevel.SPORTS_CONTEXT,
            ValidationLevel.UNITS,
        ]

        for level in levels:
            result = self.builder.validate_formula(formula, level)

            self.assertIsInstance(result, FormulaValidation)
            self.assertTrue(result.is_valid)
            self.assertIsInstance(result.errors, list)
            self.assertIsInstance(result.warnings, list)
            self.assertIsInstance(result.suggestions, list)
            self.assertIsInstance(result.confidence, float)
            self.assertGreaterEqual(result.confidence, 0.0)
            self.assertLessEqual(result.confidence, 1.0)


class TestFormulaComponent(unittest.TestCase):
    """Test cases for FormulaComponent class"""

    def test_formula_component_creation(self):
        """Test FormulaComponent creation"""
        component = FormulaComponent(
            id="test-1",
            type=FormulaComponentType.VARIABLE,
            value="PTS",
            position=0,
            metadata={"description": "Points"},
        )

        self.assertEqual(component.id, "test-1")
        self.assertEqual(component.type, FormulaComponentType.VARIABLE)
        self.assertEqual(component.value, "PTS")
        self.assertEqual(component.position, 0)
        self.assertEqual(component.metadata["description"], "Points")


class TestFormulaTemplate(unittest.TestCase):
    """Test cases for FormulaTemplate class"""

    def test_formula_template_creation(self):
        """Test FormulaTemplate creation"""
        template = FormulaTemplate(
            name="Test Template",
            description="A test template",
            template="PTS / FGA",
            variables=["PTS", "FGA"],
            category="shooting",
            example_values={"PTS": 25.0, "FGA": 20.0},
        )

        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.description, "A test template")
        self.assertEqual(template.template, "PTS / FGA")
        self.assertEqual(template.variables, ["PTS", "FGA"])
        self.assertEqual(template.category, "shooting")
        self.assertEqual(template.example_values["PTS"], 25.0)


class TestFormulaValidation(unittest.TestCase):
    """Test cases for FormulaValidation class"""

    def test_formula_validation_creation(self):
        """Test FormulaValidation creation"""
        validation = FormulaValidation(
            is_valid=True,
            errors=[],
            warnings=["Minor warning"],
            suggestions=["Good formula"],
            confidence=0.9,
        )

        self.assertTrue(validation.is_valid)
        self.assertEqual(len(validation.errors), 0)
        self.assertEqual(len(validation.warnings), 1)
        self.assertEqual(len(validation.suggestions), 1)
        self.assertEqual(validation.confidence, 0.9)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
