#!/usr/bin/env python3
"""
Integration Tests for NBA MCP Server

This module contains comprehensive integration tests that verify the interaction
between different components of the NBA MCP server, including end-to-end workflows.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import unittest
import pytest
import sys
import os
import asyncio
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mcp.server.fastmcp import FastMCP, Context
from mcp_server.fastmcp_server import mcp as nba_mcp_server


class TestMCPIntegration(unittest.TestCase):
    """Test cases for MCP server integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.mcp_server = nba_mcp_server

        # Test data
        self.test_player_stats = {
            "PTS": 25.0,
            "FGM": 10.0,
            "FGA": 20.0,
            "3PM": 3.0,
            "3PA": 8.0,
            "FTM": 2.0,
            "FTA": 3.0,
            "REB": 8.0,
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

    async def test_algebra_tools_integration(self):
        """Test integration between algebraic tools"""
        # Test formula calculation
        result_tuple = await self.mcp_server.call_tool(
            "algebra_sports_formula",
            {
                "params": {
                    "formula_name": "true_shooting",
                    "stats": self.test_player_stats,
                }
            },
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("result", result)
        self.assertIsInstance(result["result"], float)

        # Test formula simplification
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"
        result_tuple = await self.mcp_server.call_tool(
            "algebra_simplify", {"params": {"formula": formula}}
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("simplified", result)
        self.assertIn("latex", result)

    async def test_formula_intelligence_integration(self):
        """Test integration between formula intelligence tools"""
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        # Test formula type identification
        result_tuple = await self.mcp_server.call_tool(
            "formula_identify_type", {"params": {"formula": formula}}
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("formula_type", result)
        self.assertIn("confidence", result)

        # Test tool suggestions
        result_tuple = await self.mcp_server.call_tool(
            "formula_suggest_tools", {"params": {"formula": formula}}
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("suggested_tools", result)
        self.assertIsInstance(result["suggested_tools"], list)

        # Test variable mapping
        result_tuple = await self.mcp_server.call_tool(
            "formula_map_variables", {"params": {"formula": formula}}
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("variable_mapping", result)
        self.assertIsInstance(result["variable_mapping"], dict)

    async def test_formula_extraction_integration(self):
        """Test integration between formula extraction tools"""
        # Test formula structure analysis
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        result_tuple = await self.mcp_server.call_tool(
            "analyze_formula_structure", {"params": {"formula": formula}}
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("structure_type", result)
        self.assertIn("complexity_score", result)
        self.assertIn("variable_count", result)

        # Test LaTeX conversion
        latex_formula = r"\frac{PTS}{2 \cdot (FGA + 0.44 \cdot FTA)}"

        result_tuple = await self.mcp_server.call_tool(
            "convert_latex_to_sympy", {"params": {"latex_formula": latex_formula}}
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("sympy_expression", result)
        self.assertIn("conversion_success", result)

    async def test_formula_builder_integration(self):
        """Test integration between formula builder tools"""
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        # Test formula validation
        result_tuple = await self.mcp_server.call_tool(
            "formula_builder_validate",
            {"params": {"formula": formula, "validation_level": "syntax"}},
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("is_valid", result)
        self.assertTrue(result["is_valid"])

        # Test completion suggestions
        result_tuple = await self.mcp_server.call_tool(
            "formula_builder_suggest",
            {"params": {"partial_formula": "PTS / (2 * (FGA +", "context": "shooting"}},
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("suggestions", result)
        self.assertIsInstance(result["suggestions"], list)

        # Test formula preview
        result_tuple = await self.mcp_server.call_tool(
            "formula_builder_preview",
            {"params": {"formula": formula, "variable_values": self.test_player_stats}},
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])
        self.assertIn("latex", result)
        self.assertIn("calculated_value", result)
        self.assertIsNotNone(result["calculated_value"])

    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # Step 1: Extract formula from text (simulated)
        formula_text = "PTS / (2 * (FGA + 0.44 * FTA))"

        # Step 2: Analyze formula structure
        result_tuple = await self.mcp_server.call_tool(
            "analyze_formula_structure", {"params": {"formula": formula_text}}
        )
        structure_result = result_tuple[1]

        self.assertTrue(structure_result["success"])

        # Step 3: Identify formula type
        result_tuple = await self.mcp_server.call_tool(
            "formula_identify_type", {"params": {"formula": formula_text}}
        )
        type_result = result_tuple[1]

        self.assertTrue(type_result["success"])

        # Step 4: Validate formula
        result_tuple = await self.mcp_server.call_tool(
            "formula_builder_validate",
            {"params": {"formula": formula_text, "validation_level": "semantic"}},
        )
        validation_result = result_tuple[1]

        self.assertTrue(validation_result["success"])
        self.assertTrue(validation_result["is_valid"])

        # Step 5: Calculate with real data
        result_tuple = await self.mcp_server.call_tool(
            "algebra_sports_formula",
            {
                "params": {
                    "formula_name": "true_shooting",
                    "stats": self.test_player_stats,
                }
            },
        )
        calculation_result = result_tuple[1]

        self.assertTrue(calculation_result["success"])
        self.assertIn("result", calculation_result)

        # Step 6: Export result
        result_tuple = await self.mcp_server.call_tool(
            "formula_builder_export",
            {"params": {"formula": formula_text, "format_type": "latex"}},
        )
        export_result = result_tuple[1]

        self.assertTrue(export_result["success"])
        self.assertIn("exported_content", export_result)

    async def test_error_handling_integration(self):
        """Test error handling across integrated systems"""
        # Test invalid formula name
        result_tuple = await self.mcp_server.call_tool(
            "algebra_sports_formula",
            {
                "params": {
                    "formula_name": "invalid_formula",
                    "stats": self.test_player_stats,
                }
            },
        )
        result = result_tuple[1]

        self.assertFalse(result["success"])
        self.assertIn("error", result)

        # Test malformed formula
        result_tuple = await self.mcp_server.call_tool(
            "formula_builder_validate",
            {"params": {"formula": "PTS / (2 * (FGA +", "validation_level": "syntax"}},
        )
        result = result_tuple[1]

        self.assertTrue(result["success"])  # Should handle gracefully
        self.assertFalse(result["is_valid"])
        self.assertGreater(len(result["errors"]), 0)

        # Test missing variables
        incomplete_stats = {"PTS": 25.0, "FGA": 20.0}  # Missing FTA

        result_tuple = await self.mcp_server.call_tool(
            "algebra_sports_formula",
            {"params": {"formula_name": "true_shooting", "stats": incomplete_stats}},
        )
        result = result_tuple[1]

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    async def test_performance_integration(self):
        """Test performance across integrated systems"""
        import time

        # Test multiple rapid calculations
        start_time = time.time()

        for _ in range(10):
            result_tuple = await self.mcp_server.call_tool(
                "algebra_sports_formula",
                {
                    "params": {
                        "formula_name": "true_shooting",
                        "stats": self.test_player_stats,
                    }
                },
            )
            result = result_tuple[1]
            self.assertTrue(result["success"])

        end_time = time.time()

        # Should complete 10 calculations in reasonable time
        self.assertLess(end_time - start_time, 5.0)

    async def test_data_consistency_integration(self):
        """Test data consistency across different tools"""
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        # Test that different tools produce consistent results
        # 1. Direct calculation
        result_tuple = await self.mcp_server.call_tool(
            "algebra_sports_formula",
            {
                "params": {
                    "formula_name": "true_shooting",
                    "stats": self.test_player_stats,
                }
            },
        )
        direct_result = result_tuple[1]

        # 2. Formula preview calculation
        result_tuple = await self.mcp_server.call_tool(
            "formula_builder_preview",
            {"params": {"formula": formula, "variable_values": self.test_player_stats}},
        )
        preview_result = result_tuple[1]

        # Results should be consistent (within small tolerance)
        if direct_result["success"] and preview_result["success"]:
            direct_value = direct_result["result"]
            preview_value = preview_result["calculated_value"]

            self.assertIsNotNone(direct_value)
            self.assertIsNotNone(preview_value)

            # Should be within 1% tolerance
            tolerance = abs(direct_value) * 0.01
            self.assertLessEqual(abs(direct_value - preview_value), tolerance)


class TestWorkflowIntegration(unittest.TestCase):
    """Test cases for complete workflow integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.mcp_server = nba_mcp_server

    async def test_sports_analytics_workflow(self):
        """Test complete sports analytics workflow"""
        # Simulate analyzing a player's performance
        player_stats = {
            "PTS": 28.0,
            "FGM": 11.0,
            "FGA": 22.0,
            "3PM": 4.0,
            "3PA": 9.0,
            "FTM": 2.0,
            "FTA": 3.0,
            "REB": 7.0,
            "AST": 8.0,
            "STL": 1.0,
            "BLK": 0.0,
            "TOV": 4.0,
            "PF": 3.0,
            "MP": 36.0,
            "TM_MP": 240.0,
            "TM_FGA": 88.0,
            "TM_FTA": 24.0,
            "TM_TOV": 13.0,
            "TM_FGM": 34.0,
            "TM_REB": 44.0,
            "OPP_REB": 41.0,
            "OPP_POSS": 98.0,
            "OPP_2PA": 48.0,
        }

        # Step 1: Calculate multiple metrics
        metrics = ["true_shooting", "effective_fg", "per", "usage_rate"]
        results = {}

        for metric in metrics:
            result_tuple = await self.mcp_server.call_tool(
                "algebra_sports_formula",
                {"params": {"formula_name": metric, "stats": player_stats}},
            )
            result = result_tuple[1]

            if result["success"]:
                results[metric] = result["result"]

        # Should have calculated all metrics
        self.assertEqual(len(results), len(metrics))

        # Step 2: Analyze formula patterns
        for metric, value in results.items():
            # Get formula definition
            result_tuple = await self.mcp_server.call_tool(
                "algebra_sports_formula",
                {"params": {"formula_name": metric, "stats": {}}},
            )
            formula_result = result_tuple[1]

            if formula_result["success"]:
                formula_text = formula_result["formula"]

                # Analyze structure
                result_tuple = await self.mcp_server.call_tool(
                    "analyze_formula_structure", {"params": {"formula": formula_text}}
                )
                structure_result = result_tuple[1]

                self.assertTrue(structure_result["success"])
                self.assertIn("complexity_score", structure_result)

    async def test_formula_comparison_workflow(self):
        """Test workflow for comparing formulas"""
        formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",  # TS%
            "(FGM + 0.5 * 3PM) / FGA",  # eFG%
            "FGM / FGA",  # FG%
        ]

        # Test each formula
        for formula in formulas:
            # Analyze structure
            result_tuple = await self.mcp_server.call_tool(
                "analyze_formula_structure", {"params": {"formula": formula}}
            )
            structure_result = result_tuple[1]

            self.assertTrue(structure_result["success"])

            # Identify type
            result_tuple = await self.mcp_server.call_tool(
                "formula_identify_type", {"params": {"formula": formula}}
            )
            type_result = result_tuple[1]

            self.assertTrue(type_result["success"])

            # Validate
            result_tuple = await self.mcp_server.call_tool(
                "formula_builder_validate",
                {"params": {"formula": formula, "validation_level": "semantic"}},
            )
            validation_result = result_tuple[1]

            self.assertTrue(validation_result["success"])
            self.assertTrue(validation_result["is_valid"])

    async def test_formula_learning_workflow(self):
        """Test workflow for learning about formulas"""
        formula = "PTS / (2 * (FGA + 0.44 * FTA))"

        # Step 1: Get comprehensive analysis
        result_tuple = await self.mcp_server.call_tool(
            "formula_analyze_comprehensive", {"params": {"formula": formula}}
        )
        analysis_result = result_tuple[1]

        self.assertTrue(analysis_result["success"])
        self.assertIn("formula_type", analysis_result)
        self.assertIn("suggested_tools", analysis_result)
        self.assertIn("variable_mapping", analysis_result)

        # Step 2: Get recommendations
        result_tuple = await self.mcp_server.call_tool(
            "formula_get_recommendations",
            {"params": {"formula": formula, "context": "shooting efficiency"}},
        )
        recommendations_result = result_tuple[1]

        self.assertTrue(recommendations_result["success"])
        self.assertIn("formula_analysis", recommendations_result)
        self.assertIn("suggested_improvements", recommendations_result)
        self.assertIn("related_formulas", recommendations_result)

        # Step 3: Get template suggestions
        result_tuple = await self.mcp_server.call_tool(
            "formula_builder_get_templates",
            {"params": {"template_name": None, "category": "shooting"}},
        )
        templates_result = result_tuple[1]

        self.assertTrue(templates_result["success"])
        self.assertIn("templates", templates_result)
        self.assertGreater(len(templates_result["templates"]), 0)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
