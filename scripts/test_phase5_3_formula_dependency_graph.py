#!/usr/bin/env python3
"""
Test script for Phase 5.3: Formula Dependency Graph

Tests the formula dependency graph tools for creating, visualizing,
and analyzing dependencies between sports analytics formulas.

Author: NBA MCP Server Team
Date: October 13, 2025
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import unittest
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestFormulaDependencyGraph(unittest.TestCase):

    def setUp(self):
        """Set up test data for formula dependency analysis."""
        logger.info("Setting up Formula Dependency Graph tests...")

    async def test_create_dependency_graph(self):
        """Test creating a formula dependency graph"""
        logger.info("=== Testing Dependency Graph Creation ===")

        from mcp_server.tools import formula_dependency_graph

        try:
            result = formula_dependency_graph.create_formula_dependency_graph(
                formulas=None,  # Let it get formulas from algebra_helper
                analyze_dependencies=True,
                include_custom_formulas=True
            )

            logger.info(f"✓ Dependency graph created successfully")
            logger.info(f"  Nodes: {len(result.nodes)}")
            logger.info(f"  Dependencies: {len(result.dependencies)}")
            logger.info(f"  Categories: {len(result.categories)}")

            # Basic validation
            self.assertGreater(len(result.nodes), 0, "Should have at least one node")
            self.assertGreaterEqual(len(result.dependencies), 0, "Should have zero or more dependencies")
            self.assertGreater(len(result.categories), 0, "Should have at least one category")

            # Check node structure
            for formula_id, node in result.nodes.items():
                self.assertIsNotNone(node.name, f"Node {formula_id} should have a name")
                self.assertIsNotNone(node.formula, f"Node {formula_id} should have a formula")
                self.assertIsInstance(node.variables, list, f"Node {formula_id} variables should be a list")
                self.assertGreaterEqual(node.complexity_score, 1, f"Node {formula_id} should have complexity >= 1")

            logger.info("✓ Dependency graph creation test passed")

        except Exception as e:
            logger.error(f"❌ Dependency graph creation failed: {e}")
            raise

    async def test_visualize_dependency_graph(self):
        """Test visualizing the dependency graph"""
        logger.info("=== Testing Dependency Graph Visualization ===")

        from mcp_server.tools import formula_dependency_graph

        try:
            # Create graph first
            graph = formula_dependency_graph.create_formula_dependency_graph(
                formulas=None,  # Let it get formulas from algebra_helper
                analyze_dependencies=True,
                include_custom_formulas=True
            )

            # Test visualization
            result = formula_dependency_graph.visualize_dependency_graph(
                graph=graph,
                layout="spring",
                show_labels=True,
                node_size=1000,
                edge_width=1.0,
                save_path=None  # Don't save for test
            )

            logger.info(f"✓ Graph visualization created successfully")
            logger.info(f"  Status: {result['status']}")
            logger.info(f"  Visualization created: {result['visualization_created']}")
            logger.info(f"  Statistics: {result['statistics']}")

            # Basic validation
            self.assertEqual(result['status'], 'success', "Visualization should succeed")
            self.assertTrue(result['visualization_created'], "Visualization should be created")
            self.assertIn('statistics', result, "Should include statistics")

            logger.info("✓ Dependency graph visualization test passed")

        except Exception as e:
            logger.error(f"❌ Dependency graph visualization failed: {e}")
            raise

    async def test_find_dependency_paths(self):
        """Test finding dependency paths between formulas"""
        logger.info("=== Testing Dependency Path Finding ===")

        from mcp_server.tools import formula_dependency_graph

        try:
            # Create graph first
            graph = formula_dependency_graph.create_formula_dependency_graph(
                formulas=None,  # Let it get formulas from algebra_helper
                analyze_dependencies=True,
                include_custom_formulas=True
            )

            # Get two formulas to test path finding
            formula_ids = list(graph.nodes.keys())
            if len(formula_ids) >= 2:
                source_formula = formula_ids[0]
                target_formula = formula_ids[1]

                result = formula_dependency_graph.find_dependency_paths(
                    graph=graph,
                    source_formula=source_formula,
                    target_formula=target_formula,
                    max_depth=3
                )

                logger.info(f"✓ Dependency path finding completed")
                logger.info(f"  Source: {source_formula}")
                logger.info(f"  Target: {target_formula}")
                logger.info(f"  Total paths: {result['total_paths']}")
                logger.info(f"  Status: {result['status']}")

                # Basic validation
                self.assertEqual(result['status'], 'success', "Path finding should succeed")
                self.assertGreaterEqual(result['total_paths'], 0, "Should have zero or more paths")
                self.assertEqual(result['source_formula'], source_formula, "Source should match")
                self.assertEqual(result['target_formula'], target_formula, "Target should match")

                if result['total_paths'] > 0:
                    self.assertIn('strongest_path', result, "Should have strongest path")
                    logger.info(f"  Strongest path: {result['strongest_path']['description']}")

                logger.info("✓ Dependency path finding test passed")
            else:
                logger.warning("⚠ Not enough formulas to test path finding")

        except Exception as e:
            logger.error(f"❌ Dependency path finding failed: {e}")
            raise

    async def test_analyze_formula_complexity(self):
        """Test analyzing formula complexity"""
        logger.info("=== Testing Formula Complexity Analysis ===")

        from mcp_server.tools import formula_dependency_graph

        try:
            # Create graph first
            graph = formula_dependency_graph.create_formula_dependency_graph(
                formulas=None,  # Let it get formulas from algebra_helper
                analyze_dependencies=True,
                include_custom_formulas=True
            )

            # Test global complexity analysis
            result = formula_dependency_graph.analyze_formula_complexity(
                graph=graph,
                formula_id=None  # Analyze all formulas
            )

            logger.info(f"✓ Global complexity analysis completed")
            logger.info(f"  Status: {result['status']}")
            logger.info(f"  Total formulas: {result['analysis']['total_formulas']}")
            logger.info(f"  Average complexity: {result['analysis']['average_complexity']:.2f}")
            logger.info(f"  Max complexity: {result['analysis']['max_complexity']}")

            # Basic validation
            self.assertEqual(result['status'], 'success', "Complexity analysis should succeed")
            self.assertGreater(result['analysis']['total_formulas'], 0, "Should have formulas")
            self.assertGreaterEqual(result['analysis']['average_complexity'], 1, "Average complexity should be >= 1")

            # Test specific formula analysis if we have formulas
            if result['analysis']['total_formulas'] > 0:
                formula_ids = list(graph.nodes.keys())
                test_formula = formula_ids[0]

                specific_result = formula_dependency_graph.analyze_formula_complexity(
                    graph=graph,
                    formula_id=test_formula
                )

                logger.info(f"✓ Specific formula analysis completed for {test_formula}")
                logger.info(f"  Formula name: {specific_result['analysis']['formula_name']}")
                logger.info(f"  Complexity score: {specific_result['analysis']['complexity_score']}")
                logger.info(f"  Formula type: {specific_result['analysis']['formula_type']}")

                self.assertEqual(specific_result['status'], 'success', "Specific analysis should succeed")
                self.assertEqual(specific_result['analysis']['formula_id'], test_formula, "Formula ID should match")

            logger.info("✓ Formula complexity analysis test passed")

        except Exception as e:
            logger.error(f"❌ Formula complexity analysis failed: {e}")
            raise

    async def test_export_dependency_graph(self):
        """Test exporting the dependency graph"""
        logger.info("=== Testing Dependency Graph Export ===")

        from mcp_server.tools import formula_dependency_graph

        try:
            # Create graph first
            graph = formula_dependency_graph.create_formula_dependency_graph(
                formulas=None,  # Let it get formulas from algebra_helper
                analyze_dependencies=True,
                include_custom_formulas=True
            )

            # Test JSON export
            result = formula_dependency_graph.export_dependency_graph(
                graph=graph,
                format="json",
                include_visualization=False
            )

            logger.info(f"✓ Graph export completed")
            logger.info(f"  Status: {result['status']}")
            logger.info(f"  Export format: {result['export_format']}")
            logger.info(f"  Node count: {result['node_count']}")
            logger.info(f"  Dependency count: {result['dependency_count']}")

            # Basic validation
            self.assertEqual(result['status'], 'success', "Export should succeed")
            self.assertEqual(result['export_format'], 'json', "Export format should be JSON")
            self.assertGreater(result['node_count'], 0, "Should have nodes")
            self.assertGreaterEqual(result['dependency_count'], 0, "Should have zero or more dependencies")
            self.assertIn('export_data', result, "Should include export data")

            # Check export data structure
            export_data = result['export_data']
            self.assertIn('metadata', export_data, "Should have metadata")
            self.assertIn('nodes', export_data, "Should have nodes")
            self.assertIn('dependencies', export_data, "Should have dependencies")

            logger.info("✓ Dependency graph export test passed")

        except Exception as e:
            logger.error(f"❌ Dependency graph export failed: {e}")
            raise

    async def test_real_world_scenarios(self):
        """Test real-world scenarios for formula dependency analysis"""
        logger.info("=== Testing Real-World Scenarios ===")

        from mcp_server.tools import formula_dependency_graph

        try:
            # Create graph
            graph = formula_dependency_graph.create_formula_dependency_graph(
                formulas=None,  # Let it get formulas from algebra_helper
                analyze_dependencies=True,
                include_custom_formulas=True
            )

            # Scenario 1: Find most complex formulas
            complexity_result = formula_dependency_graph.analyze_formula_complexity(
                graph=graph,
                formula_id=None
            )

            most_complex = complexity_result['analysis']['most_complex_formulas']
            logger.info(f"✓ Most complex formulas identified:")
            for i, formula in enumerate(most_complex[:3], 1):
                logger.info(f"  {i}. {formula['name']} (complexity: {formula['complexity']})")

            # Scenario 2: Analyze specific formula dependencies
            if len(graph.nodes) > 0:
                test_formula = list(graph.nodes.keys())[0]
                specific_analysis = formula_dependency_graph.analyze_formula_complexity(
                    graph=graph,
                    formula_id=test_formula
                )

                analysis = specific_analysis['analysis']
                logger.info(f"✓ Formula analysis for {test_formula}:")
                logger.info(f"  Name: {analysis['formula_name']}")
                logger.info(f"  Type: {analysis['formula_type']}")
                logger.info(f"  Dependencies: {analysis['total_dependencies']}")
                logger.info(f"  Dependents: {analysis['total_dependents']}")

            # Scenario 3: Export for external analysis
            export_result = formula_dependency_graph.export_dependency_graph(
                graph=graph,
                format="json",
                include_visualization=True
            )

            logger.info(f"✓ Graph exported for external analysis")
            logger.info(f"  Format: {export_result['export_format']}")
            logger.info(f"  Nodes: {export_result['node_count']}")
            logger.info(f"  Dependencies: {export_result['dependency_count']}")

            logger.info("✓ Real-world scenarios test passed")

        except Exception as e:
            logger.error(f"❌ Real-world scenarios failed: {e}")
            raise


async def run_all_tests():
    """Runs all formula dependency graph tests."""
    logger.info("\n" + "=" * 70)
    logger.info("Starting Phase 5.3: Formula Dependency Graph Tests")
    logger.info("=" * 70 + "\n")

    # Run tests directly
    test_instance = TestFormulaDependencyGraph()
    test_instance.setUp()

    await test_instance.test_create_dependency_graph()
    await test_instance.test_visualize_dependency_graph()
    await test_instance.test_find_dependency_paths()
    await test_instance.test_analyze_formula_complexity()
    await test_instance.test_export_dependency_graph()
    await test_instance.test_real_world_scenarios()

    logger.info("\n" + "=" * 70)
    logger.info("✓ All Phase 5.3 Formula Dependency Graph Tests Passed!")
    logger.info("=" * 70 + "\n")


if __name__ == '__main__':
    asyncio.run(run_all_tests())
