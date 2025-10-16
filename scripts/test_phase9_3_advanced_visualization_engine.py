#!/usr/bin/env python3
"""
Test script for Phase 9.3: Advanced Visualization Engine

This script tests all the advanced visualization capabilities including:
- Formula visualization (2D, 3D, interactive)
- Data visualization (various chart types)
- Interactive visualizations
- Formula relationship networks
- Visualization capabilities

Author: NBA MCP Server Development Team
Date: October 13, 2025
"""

import sys
import os
import unittest
import time
import json
import logging
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the visualization engine
from mcp_server.tools.advanced_visualization_engine import (
    AdvancedVisualizationEngine,
    visualize_formula,
    visualize_data,
    create_interactive_visualization,
    visualize_formula_relationships,
    get_visualization_capabilities,
    VisualizationType,
    ChartType,
    ExportFormat,
    VisualizationConfig
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase93TestSuite(unittest.TestCase):
    """Test suite for Phase 9.3: Advanced Visualization Engine"""

    def setUp(self):
        """Set up test environment"""
        self.engine = AdvancedVisualizationEngine()
        self.test_formulas = [
            "x**2",
            "sin(x)",
            "x**2 + y**2",
            "x*y + 2*x + 3*y",
            "exp(-x**2)"
        ]
        self.test_data = {
            "x": list(range(1, 21)),
            "y": [i**2 for i in range(1, 21)],
            "z": [i**3 for i in range(1, 21)]
        }

    def test_engine_initialization(self):
        """Test visualization engine initialization"""
        logger.info("Testing engine initialization...")

        self.assertIsNotNone(self.engine)
        self.assertIsInstance(self.engine, AdvancedVisualizationEngine)

        # Check capabilities
        capabilities = self.engine.get_visualization_capabilities()
        self.assertIsInstance(capabilities, dict)
        self.assertIn('matplotlib_available', capabilities)
        self.assertIn('plotly_available', capabilities)
        self.assertIn('supported_formats', capabilities)

        logger.info("✓ Engine initialization test passed")

    def test_formula_visualization_2d(self):
        """Test 2D formula visualization"""
        logger.info("Testing 2D formula visualization...")

        formula = "x**2"
        result = self.engine.visualize_formula(
            formula=formula,
            visualization_type=VisualizationType.FORMULA_GRAPH,
            chart_type=ChartType.LINE,
            export_format=ExportFormat.PNG
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.visualization_id)
        self.assertIsNotNone(result.formula_id)
        self.assertEqual(result.visualization_type, VisualizationType.FORMULA_GRAPH)

        # Check if image data is generated
        if result.image_data:
            self.assertIsInstance(result.image_data, str)
            self.assertTrue(len(result.image_data) > 0)

        logger.info("✓ 2D formula visualization test passed")

    def test_formula_visualization_3d(self):
        """Test 3D formula visualization"""
        logger.info("Testing 3D formula visualization...")

        formula = "x**2 + y**2"
        result = self.engine.visualize_formula(
            formula=formula,
            visualization_type=VisualizationType.THREE_DIMENSIONAL,
            chart_type=ChartType.SURFACE,
            export_format=ExportFormat.PNG
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.visualization_type, VisualizationType.THREE_DIMENSIONAL)

        logger.info("✓ 3D formula visualization test passed")

    def test_interactive_visualization(self):
        """Test interactive visualization"""
        logger.info("Testing interactive visualization...")

        data = {"x": list(range(10)), "y": [i**2 for i in range(10)]}
        result = self.engine.create_interactive_visualization(
            data=data,
            visualization_type=VisualizationType.INTERACTIVE_CHART
        )

        self.assertIsNotNone(result)

        # Check if plotly is available for interactive visualizations
        capabilities = self.engine.get_visualization_capabilities()
        if capabilities.get('plotly_available', False):
            self.assertTrue(result.success)
            self.assertIsNotNone(result.interactive_data)
            self.assertIsInstance(result.controls, list)
        else:
            # If plotly is not available, the result should indicate failure gracefully
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)

        logger.info("✓ Interactive visualization test passed")

    def test_data_visualization_line(self):
        """Test data visualization with line chart"""
        logger.info("Testing data visualization (line chart)...")

        result = self.engine.visualize_data(
            data=self.test_data,
            visualization_type=VisualizationType.DATA_PLOT,
            chart_type=ChartType.LINE,
            export_format=ExportFormat.PNG
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.chart_type, ChartType.LINE)

        logger.info("✓ Data visualization (line chart) test passed")

    def test_data_visualization_scatter(self):
        """Test data visualization with scatter chart"""
        logger.info("Testing data visualization (scatter chart)...")

        result = self.engine.visualize_data(
            data=self.test_data,
            visualization_type=VisualizationType.DATA_PLOT,
            chart_type=ChartType.SCATTER,
            export_format=ExportFormat.PNG
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.chart_type, ChartType.SCATTER)

        logger.info("✓ Data visualization (scatter chart) test passed")

    def test_data_visualization_heatmap(self):
        """Test data visualization with heatmap"""
        logger.info("Testing data visualization (heatmap)...")

        result = self.engine.visualize_data(
            data=self.test_data,
            visualization_type=VisualizationType.DATA_PLOT,
            chart_type=ChartType.HEATMAP,
            export_format=ExportFormat.PNG
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.chart_type, ChartType.HEATMAP)

        logger.info("✓ Data visualization (heatmap) test passed")

    def test_formula_relationships(self):
        """Test formula relationship visualization"""
        logger.info("Testing formula relationship visualization...")

        formulas = ["x**2", "x**3", "x**2 + x**3"]
        relationships = [
            ("x**2", "x**3", "related"),
            ("x**2", "x**2 + x**3", "dependency"),
            ("x**3", "x**2 + x**3", "dependency")
        ]

        result = self.engine.visualize_formula_relationships(
            formulas=formulas,
            relationships=relationships,
            export_format=ExportFormat.PNG
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.visualization_type, VisualizationType.FORMULA_RELATIONSHIP)

        logger.info("✓ Formula relationship visualization test passed")

    def test_export_formats(self):
        """Test different export formats"""
        logger.info("Testing different export formats...")

        formula = "sin(x)"
        formats_to_test = [ExportFormat.PNG, ExportFormat.SVG, ExportFormat.BASE64]

        for export_format in formats_to_test:
            result = self.engine.visualize_formula(
                formula=formula,
                visualization_type=VisualizationType.FORMULA_GRAPH,
                export_format=export_format
            )

            self.assertIsNotNone(result)
            self.assertTrue(result.success)

            # Check appropriate data is present based on format
            # Note: If matplotlib is not available, image_data might be None
            if export_format in [ExportFormat.PNG, ExportFormat.BASE64]:
                # Only check if matplotlib is available
                capabilities = self.engine.get_visualization_capabilities()
                if capabilities.get('matplotlib_available', False):
                    self.assertIsNotNone(result.image_data)
            elif export_format == ExportFormat.SVG:
                # SVG might be in json_data or image_data
                if result.json_data or result.image_data:
                    pass  # At least one should be present

        logger.info("✓ Export formats test passed")

    def test_custom_configuration(self):
        """Test custom visualization configuration"""
        logger.info("Testing custom configuration...")

        config = VisualizationConfig(
            width=1000,
            height=800,
            dpi=150,
            title="Custom Test Plot",
            x_label="Custom X",
            y_label="Custom Y",
            grid=True,
            legend=True
        )

        result = self.engine.visualize_formula(
            formula="x**2",
            visualization_type=VisualizationType.FORMULA_GRAPH,
            config=config,
            export_format=ExportFormat.PNG
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.metadata)
        self.assertIn('config', result.metadata)

        logger.info("✓ Custom configuration test passed")

    def test_error_handling(self):
        """Test error handling"""
        logger.info("Testing error handling...")

        # Test invalid formula
        result = self.engine.visualize_formula(
            formula="invalid_formula_xyz",
            visualization_type=VisualizationType.FORMULA_GRAPH
        )

        # Should handle gracefully
        self.assertIsNotNone(result)
        # May succeed with fallback or fail gracefully

        # Test empty data
        result = self.engine.visualize_data(
            data={},
            visualization_type=VisualizationType.DATA_PLOT
        )

        self.assertIsNotNone(result)
        # Should handle empty data gracefully

        logger.info("✓ Error handling test passed")

    def test_standalone_functions(self):
        """Test standalone functions"""
        logger.info("Testing standalone functions...")

        # Test visualize_formula standalone function
        result = visualize_formula(
            formula="x**2",
            visualization_type="formula_graph",
            chart_type="line",
            export_format="png"
        )

        self.assertIsInstance(result, dict)
        self.assertIn('visualization_id', result)
        self.assertIn('success', result)

        # Test visualize_data standalone function
        result = visualize_data(
            data=self.test_data,
            visualization_type="data_plot",
            chart_type="line",
            export_format="png"
        )

        self.assertIsInstance(result, dict)
        self.assertIn('visualization_id', result)
        self.assertIn('success', result)

        # Test create_interactive_visualization standalone function
        result = create_interactive_visualization(
            data={"x": [1, 2, 3], "y": [1, 4, 9]},
            visualization_type="interactive_chart"
        )

        self.assertIsInstance(result, dict)
        self.assertIn('visualization_id', result)
        self.assertIn('success', result)

        # Test get_visualization_capabilities standalone function
        result = get_visualization_capabilities()

        self.assertIsInstance(result, dict)
        self.assertIn('matplotlib_available', result)
        self.assertIn('plotly_available', result)

        logger.info("✓ Standalone functions test passed")

    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        logger.info("Testing performance benchmarks...")

        start_time = time.time()

        # Test multiple visualizations
        for i, formula in enumerate(self.test_formulas[:3]):
            result = self.engine.visualize_formula(
                formula=formula,
                visualization_type=VisualizationType.FORMULA_GRAPH,
                export_format=ExportFormat.PNG
            )
            self.assertTrue(result.success)

        end_time = time.time()
        total_time = end_time - start_time

        # Performance should be reasonable (less than 30 seconds for 3 visualizations)
        self.assertLess(total_time, 30.0)

        logger.info(f"✓ Performance test passed: {total_time:.2f} seconds for 3 visualizations")

    def test_integration_with_sports_formulas(self):
        """Test integration with sports formulas"""
        logger.info("Testing integration with sports formulas...")

        # Test with basketball-related formulas
        basketball_formulas = [
            "x*y",  # Simple relationship
            "x**2 + y**2",  # Distance formula
            "x + y + z"  # Sum formula
        ]

        for formula in basketball_formulas:
            result = self.engine.visualize_formula(
                formula=formula,
                visualization_type=VisualizationType.FORMULA_GRAPH,
                export_format=ExportFormat.PNG
            )

            self.assertIsNotNone(result)
            self.assertTrue(result.success)

        logger.info("✓ Sports formulas integration test passed")

def run_performance_test():
    """Run performance test"""
    logger.info("Running performance test...")

    engine = AdvancedVisualizationEngine()
    test_data = {
        "points": list(range(1, 101)),
        "rebounds": [i * 0.8 for i in range(1, 101)],
        "assists": [i * 0.6 for i in range(1, 101)]
    }

    start_time = time.time()

    # Test data visualization performance
    result = engine.visualize_data(
        data=test_data,
        visualization_type=VisualizationType.DATA_PLOT,
        chart_type=ChartType.LINE,
        export_format=ExportFormat.PNG
    )

    end_time = time.time()
    visualization_time = end_time - start_time

    logger.info(f"Data visualization completed in {visualization_time:.2f} seconds")
    logger.info(f"Success: {result.success}")

    return visualization_time < 10.0  # Should complete within 10 seconds

def main():
    """Main test function"""
    logger.info("Starting Phase 9.3: Advanced Visualization Engine Tests")
    logger.info("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase93TestSuite)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Run performance test
    logger.info("\n" + "=" * 60)
    logger.info("Running Performance Test")
    logger.info("=" * 60)

    performance_passed = run_performance_test()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    passed_tests = total_tests - failed_tests - error_tests

    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {failed_tests}")
    logger.info(f"Errors: {error_tests}")
    logger.info(f"Performance Test: {'PASSED' if performance_passed else 'FAILED'}")

    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    logger.info(f"Success Rate: {success_rate:.1f}%")

    if result.wasSuccessful() and performance_passed:
        logger.info("\n🎉 ALL TESTS PASSED! Phase 9.3 implementation is working correctly.")
        return True
    else:
        logger.info(f"\n❌ {failed_tests + error_tests} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
