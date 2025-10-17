#!/usr/bin/env python3
"""
Comprehensive Test Runner for NBA MCP Server

This script runs all unit tests, integration tests, and performance benchmarks
for the NBA MCP server, providing a complete testing suite.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import unittest
import sys
import os
import asyncio
import time
import json
from typing import Dict, Any, List
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_unit_tests():
    """Run all unit tests"""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)

    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), "unit")
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped) if hasattr(result, "skipped") else 0,
        "success": result.wasSuccessful(),
    }


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)

    # Discover and run integration tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), "integration")
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped) if hasattr(result, "skipped") else 0,
        "success": result.wasSuccessful(),
    }


async def run_performance_benchmarks():
    """Run all performance benchmarks"""
    print("\n" + "=" * 60)
    print("RUNNING PERFORMANCE BENCHMARKS")
    print("=" * 60)

    # Import and run performance benchmarks
    from tests.benchmarks.test_performance import (
        TestPerformanceBenchmarks,
        TestScalabilityBenchmarks,
    )

    # Run performance benchmarks
    perf_tests = TestPerformanceBenchmarks()
    perf_tests.setUp()

    benchmark_results = await perf_tests.run_all_benchmarks()

    # Run scalability benchmarks
    scalability_tests = TestScalabilityBenchmarks()
    scalability_tests.setUp()

    large_dataset_result = await scalability_tests.test_large_dataset_performance()
    complex_formula_result = await scalability_tests.test_complex_formula_performance()

    return {
        "benchmarks": benchmark_results,
        "large_dataset": large_dataset_result,
        "complex_formula": complex_formula_result,
    }


def generate_test_report(results: Dict[str, Any]):
    """Generate a comprehensive test report"""
    print("\n" + "=" * 60)
    print("TEST REPORT SUMMARY")
    print("=" * 60)

    # Unit test results
    unit_results = results.get("unit_tests", {})
    print(f"Unit Tests:")
    print(f"  Tests Run: {unit_results.get('tests_run', 0)}")
    print(f"  Failures: {unit_results.get('failures', 0)}")
    print(f"  Errors: {unit_results.get('errors', 0)}")
    print(f"  Skipped: {unit_results.get('skipped', 0)}")
    print(f"  Success: {'✓' if unit_results.get('success', False) else '✗'}")

    # Integration test results
    integration_results = results.get("integration_tests", {})
    print(f"\nIntegration Tests:")
    print(f"  Tests Run: {integration_results.get('tests_run', 0)}")
    print(f"  Failures: {integration_results.get('failures', 0)}")
    print(f"  Errors: {integration_results.get('errors', 0)}")
    print(f"  Skipped: {integration_results.get('skipped', 0)}")
    print(f"  Success: {'✓' if integration_results.get('success', False) else '✗'}")

    # Performance benchmark results
    perf_results = results.get("performance_benchmarks", {})
    if perf_results:
        print(f"\nPerformance Benchmarks:")

        benchmarks = perf_results.get("benchmarks", {})
        passed_benchmarks = sum(
            1 for result in benchmarks.values() if result.get("passed", False)
        )
        total_benchmarks = len(benchmarks)

        print(f"  Benchmarks Passed: {passed_benchmarks}/{total_benchmarks}")
        print(f"  Success Rate: {passed_benchmarks/total_benchmarks*100:.1f}%")

        # Show individual benchmark results
        for tool_name, result in benchmarks.items():
            status = "✓" if result.get("passed", False) else "✗"
            avg_time = result.get("avg_time", result.get("total_time", 0))
            print(f"    {tool_name:20} | {status} | {avg_time:.4f}s")

        # Scalability results
        large_dataset = perf_results.get("large_dataset", {})
        complex_formula = perf_results.get("complex_formula", {})

        print(f"\nScalability Tests:")
        print(
            f"  Large Dataset: {'✓' if large_dataset.get('passed', False) else '✗'} ({large_dataset.get('dataset_size', 0)} records)"
        )
        print(
            f"  Complex Formulas: {'✓' if complex_formula.get('passed', False) else '✗'} ({complex_formula.get('formulas_tested', 0)} formulas)"
        )

    # Overall success
    overall_success = (
        unit_results.get("success", False)
        and integration_results.get("success", False)
        and (
            perf_results.get("benchmarks", {}).get("passed", True)
            if perf_results
            else True
        )
    )

    print(f"\n{'=' * 60}")
    print(
        f"OVERALL RESULT: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}"
    )
    print(f"{'=' * 60}")

    return overall_success


def save_test_results(results: Dict[str, Any], filename: str = "test_results.json"):
    """Save test results to JSON file"""
    try:
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nTest results saved to: {filename}")
    except Exception as e:
        print(f"Failed to save test results: {e}")


async def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="NBA MCP Server Test Runner")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration-only", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--benchmarks-only", action="store_true", help="Run only performance benchmarks"
    )
    parser.add_argument(
        "--save-results", action="store_true", help="Save results to JSON file"
    )
    parser.add_argument(
        "--output-file", default="test_results.json", help="Output file for results"
    )

    args = parser.parse_args()

    print("NBA MCP Server - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    try:
        # Run unit tests
        if not args.integration_only and not args.benchmarks_only:
            results["unit_tests"] = run_unit_tests()

        # Run integration tests
        if not args.unit_only and not args.benchmarks_only:
            results["integration_tests"] = run_integration_tests()

        # Run performance benchmarks
        if not args.unit_only and not args.integration_only:
            results["performance_benchmarks"] = await run_performance_benchmarks()

        # Generate report
        overall_success = generate_test_report(results)

        # Save results if requested
        if args.save_results:
            save_test_results(results, args.output_file)

        # Exit with appropriate code
        sys.exit(0 if overall_success else 1)

    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest execution failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
