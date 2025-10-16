#!/usr/bin/env python3
"""
Test script for Phase 7.2: Automated Formula Discovery

This script tests the automated formula discovery functionality including:
- Formula discovery from data patterns
- Pattern analysis
- Formula validation
- Formula optimization
- Formula ranking

Usage:
    python3 scripts/test_phase7_2_automated_formula_discovery.py
"""

import sys
import os
import unittest
import time
import json
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.tools.automated_formula_discovery import (
    AutomatedFormulaDiscoveryEngine,
    discover_formulas_from_data_patterns,
    analyze_patterns_for_formula_discovery,
    validate_discovered_formula_performance,
    optimize_formula_performance,
    rank_formulas_by_performance,
    DiscoveryMethod,
    ComplexityLevel
)


class Phase72TestSuite(unittest.TestCase):
    """Test suite for Phase 7.2: Automated Formula Discovery"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = AutomatedFormulaDiscoveryEngine()
        self.test_variables = ["points", "rebounds", "assists", "minutes", "field_goals_made"]
        self.test_data_patterns = [
            {
                "points": [25, 30, 22, 28, 35],
                "rebounds": [8, 10, 6, 9, 12],
                "assists": [5, 7, 4, 6, 8]
            },
            {
                "minutes": [35, 38, 32, 36, 40],
                "field_goals_made": [10, 12, 8, 11, 14],
                "points": [25, 30, 22, 28, 35]
            }
        ]
        self.test_formulas = [
            "points * rebounds / minutes",
            "assists + rebounds",
            "field_goals_made / minutes * 100",
            "points / (rebounds + assists)"
        ]

    def test_automated_formula_discovery_engine_initialization(self):
        """Test initialization of the discovery engine"""
        print("Testing discovery engine initialization...")

        self.assertIsNotNone(self.engine)
        self.assertIsInstance(self.engine.discovered_formulas, dict)
        self.assertIsInstance(self.engine.pattern_results, dict)
        self.assertIsInstance(self.engine.optimization_results, dict)

        print("✓ Discovery engine initialization test passed")

    def test_formula_discovery_from_data_patterns(self):
        """Test formula discovery from data patterns"""
        print("Testing formula discovery from data patterns...")

        result = discover_formulas_from_data_patterns(
            data_description="NBA player statistics",
            available_variables=self.test_variables,
            target_variable="points",
            discovery_method="hybrid",
            complexity_limit="moderate",
            max_formulas=3,
            confidence_threshold=0.6
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("discovered_formulas", result)
        self.assertIn("discovery_summary", result)
        self.assertGreaterEqual(result["final_count"], 0)

        # Check discovered formulas structure
        for formula in result["discovered_formulas"]:
            self.assertIn("formula_id", formula)
            self.assertIn("expression", formula)
            self.assertIn("confidence_score", formula)
            self.assertIn("discovery_method", formula)

        print(f"✓ Formula discovery test passed: {result['final_count']} formulas discovered")

    def test_pattern_analysis_for_formula_discovery(self):
        """Test pattern analysis for formula discovery"""
        print("Testing pattern analysis for formula discovery...")

        result = analyze_patterns_for_formula_discovery(
            data_patterns=self.test_data_patterns,
            pattern_types=["linear", "polynomial"],
            correlation_threshold=0.5,
            significance_level=0.05
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("pattern_results", result)
        self.assertIn("analysis_summary", result)
        self.assertGreaterEqual(result["total_patterns"], 0)

        # Check pattern results structure
        for pattern in result["pattern_results"]:
            self.assertIn("pattern_id", pattern)
            self.assertIn("pattern_type", pattern)
            self.assertIn("correlation", pattern)
            self.assertIn("formula_expression", pattern)

        print(f"✓ Pattern analysis test passed: {result['total_patterns']} patterns found")

    def test_formula_validation_performance(self):
        """Test formula validation performance"""
        print("Testing formula validation performance...")

        result = validate_discovered_formula_performance(
            formula_expressions=self.test_formulas,
            test_data=None,
            validation_metrics=["r_squared", "mae"],
            minimum_performance=0.5
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("validation_results", result)
        self.assertIn("validation_summary", result)
        self.assertGreaterEqual(result["validated_formulas"], 0)

        # Check validation results structure
        for validation in result["validation_results"]:
            self.assertIn("formula_id", validation)
            self.assertIn("expression", validation)
            self.assertIn("validation_metrics", validation)
            self.assertIn("validation_status", validation)

        print(f"✓ Formula validation test passed: {result['validated_formulas']} formulas validated")

    def test_formula_optimization(self):
        """Test formula optimization"""
        print("Testing formula optimization...")

        base_formula = "points * rebounds / minutes"

        result = optimize_formula_performance(
            base_formula=base_formula,
            optimization_objective="balanced",
            optimization_method="genetic_algorithm",
            max_iterations=50
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("optimization_result", result)
        self.assertIn("optimization_summary", result)

        # Check optimization result structure
        opt_result = result["optimization_result"]
        self.assertIn("original_formula", opt_result)
        self.assertIn("optimized_formula", opt_result)
        self.assertIn("improvement_score", opt_result)
        self.assertIn("optimization_method", opt_result)

        print(f"✓ Formula optimization test passed: {opt_result['improvement_score']:.2%} improvement")

    def test_formula_ranking_by_performance(self):
        """Test formula ranking by performance"""
        print("Testing formula ranking by performance...")

        # Create sample discovered formulas
        discovered_formulas = [
            {
                "formula_id": "formula_1",
                "expression": "points * rebounds / minutes",
                "accuracy_score": 0.8,
                "complexity_score": 0.3,
                "confidence_score": 0.75
            },
            {
                "formula_id": "formula_2",
                "expression": "assists + rebounds",
                "accuracy_score": 0.6,
                "complexity_score": 0.1,
                "confidence_score": 0.65
            },
            {
                "formula_id": "formula_3",
                "expression": "field_goals_made / minutes * 100",
                "accuracy_score": 0.7,
                "complexity_score": 0.2,
                "confidence_score": 0.7
            }
        ]

        result = rank_formulas_by_performance(
            discovered_formulas=discovered_formulas,
            ranking_criteria=["accuracy", "simplicity"],
            weights={"accuracy": 0.7, "simplicity": 0.3}
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("ranking_results", result)
        self.assertIn("ranking_summary", result)
        self.assertEqual(len(result["ranking_results"]), len(discovered_formulas))

        # Check ranking results structure
        for ranking in result["ranking_results"]:
            self.assertIn("formula_id", ranking)
            self.assertIn("ranking_score", ranking)
            self.assertIn("rank", ranking)
            self.assertIn("criteria_scores", ranking)

        print(f"✓ Formula ranking test passed: {len(result['ranking_results'])} formulas ranked")

    def test_discovery_methods(self):
        """Test different discovery methods"""
        print("Testing different discovery methods...")

        methods = ["genetic", "symbolic_regression", "pattern_matching", "hybrid"]

        for method in methods:
            result = discover_formulas_from_data_patterns(
                data_description=f"Test with {method} method",
                available_variables=self.test_variables[:3],
                discovery_method=method,
                max_formulas=2,
                confidence_threshold=0.5
            )

            self.assertEqual(result["status"], "success")
            self.assertIn("discovery_summary", result)
            self.assertEqual(result["discovery_summary"]["method_used"], method)

        print("✓ Discovery methods test passed")

    def test_complexity_limits(self):
        """Test different complexity limits"""
        print("Testing different complexity limits...")

        complexity_levels = ["simple", "moderate", "complex", "unlimited"]

        for complexity in complexity_levels:
            result = discover_formulas_from_data_patterns(
                data_description=f"Test with {complexity} complexity",
                available_variables=self.test_variables[:3],
                complexity_limit=complexity,
                max_formulas=2,
                confidence_threshold=0.5
            )

            self.assertEqual(result["status"], "success")
            self.assertIn("discovery_summary", result)
            self.assertEqual(result["discovery_summary"]["complexity_limit"], complexity)

        print("✓ Complexity limits test passed")

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("Testing error handling...")

        # Test with invalid variables
        result = discover_formulas_from_data_patterns(
            data_description="Test with invalid variables",
            available_variables=[],  # Empty variables
            max_formulas=1
        )

        # Should handle gracefully
        self.assertIn("status", result)

        # Test with invalid formula expressions
        result = validate_discovered_formula_performance(
            formula_expressions=["invalid formula expression"],
            minimum_performance=0.5
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("validation_results", result)

        print("✓ Error handling test passed")

    def test_performance_metrics(self):
        """Test performance and timing"""
        print("Testing performance metrics...")

        start_time = time.time()

        # Test formula discovery performance
        result = discover_formulas_from_data_patterns(
            data_description="Performance test",
            available_variables=self.test_variables,
            max_formulas=5,
            confidence_threshold=0.6
        )

        discovery_time = time.time() - start_time

        self.assertEqual(result["status"], "success")
        self.assertLess(discovery_time, 10.0)  # Should complete within 10 seconds

        print(f"✓ Performance test passed: Discovery completed in {discovery_time:.2f} seconds")

    def test_standalone_functions(self):
        """Test standalone functions"""
        print("Testing standalone functions...")

        # Test pattern analysis standalone
        patterns = analyze_patterns_for_formula_discovery(
            data_patterns=self.test_data_patterns,
            pattern_types=["linear"]
        )

        self.assertEqual(patterns["status"], "success")

        # Test validation standalone
        validation = validate_discovered_formula_performance(
            formula_expressions=["points + rebounds"]
        )

        self.assertEqual(validation["status"], "success")

        # Test optimization standalone
        optimization = optimize_formula_performance(
            base_formula="points * rebounds"
        )

        self.assertEqual(optimization["status"], "success")

        print("✓ Standalone functions test passed")

    def test_integration_with_sports_formulas(self):
        """Test integration with existing sports formulas"""
        print("Testing integration with sports formulas...")

        # Test that the engine can load sports formulas
        self.assertIsInstance(self.engine.sports_formulas, dict)

        # Test discovery with sports-related variables
        sports_variables = ["points", "rebounds", "assists", "field_goals_attempted", "field_goals_made"]

        result = discover_formulas_from_data_patterns(
            data_description="NBA player efficiency analysis",
            available_variables=sports_variables,
            discovery_method="pattern_matching",
            max_formulas=3
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("discovered_formulas", result)

        print("✓ Sports formulas integration test passed")


def run_performance_benchmark():
    """Run performance benchmark tests"""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK TESTS")
    print("="*60)

    engine = AutomatedFormulaDiscoveryEngine()
    test_variables = ["points", "rebounds", "assists", "minutes", "field_goals_made", "field_goals_attempted"]

    # Benchmark formula discovery
    start_time = time.time()
    result = discover_formulas_from_data_patterns(
        data_description="Performance benchmark",
        available_variables=test_variables,
        discovery_method="hybrid",
        max_formulas=10,
        confidence_threshold=0.7
    )
    discovery_time = time.time() - start_time

    print(f"Formula Discovery: {discovery_time:.2f}s ({result['final_count']} formulas)")

    # Benchmark pattern analysis
    test_patterns = [
        {"points": list(range(10, 31)), "rebounds": list(range(5, 16)), "assists": list(range(3, 11))},
        {"minutes": list(range(20, 41)), "field_goals_made": list(range(5, 16)), "field_goals_attempted": list(range(10, 21))}
    ]

    start_time = time.time()
    patterns = analyze_patterns_for_formula_discovery(
        data_patterns=test_patterns,
        pattern_types=["linear", "polynomial"]
    )
    pattern_time = time.time() - start_time

    total_patterns = patterns.get('total_patterns', 0)
    print(f"Pattern Analysis: {pattern_time:.2f}s ({total_patterns} patterns)")

    # Benchmark validation
    test_formulas = [
        "points * rebounds / minutes",
        "assists + rebounds",
        "field_goals_made / field_goals_attempted * 100",
        "points / (rebounds + assists)",
        "minutes * points / 100"
    ]

    start_time = time.time()
    validation = validate_discovered_formula_performance(
        formula_expressions=test_formulas,
        validation_metrics=["r_squared", "mae", "rmse"]
    )
    validation_time = time.time() - start_time

    print(f"Formula Validation: {validation_time:.2f}s ({validation['validated_formulas']} formulas)")

    total_time = discovery_time + pattern_time + validation_time
    print(f"\nTotal Benchmark Time: {total_time:.2f}s")

    return {
        "discovery_time": discovery_time,
        "pattern_time": pattern_time,
        "validation_time": validation_time,
        "total_time": total_time,
        "formulas_discovered": result['final_count'],
        "patterns_found": patterns['total_patterns'],
        "formulas_validated": validation['validated_formulas']
    }


def main():
    """Main test function"""
    print("="*60)
    print("PHASE 7.2: AUTOMATED FORMULA DISCOVERY - TEST SUITE")
    print("="*60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase72TestSuite)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Run performance benchmark
    benchmark_results = run_performance_benchmark()

    # Save results
    results = {
        "test_results": {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        },
        "benchmark_results": benchmark_results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open("phase_7_2_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nTest results saved to: phase_7_2_test_results.json")

    # Return success/failure
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
