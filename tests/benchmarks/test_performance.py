#!/usr/bin/env python3
"""
Performance Benchmarks for NBA MCP Server

This module contains comprehensive performance benchmarks for all components
of the NBA MCP server, including speed tests, memory usage, and scalability tests.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import unittest
import pytest
import sys
import os
import time
import asyncio
import psutil
import tracemalloc
from typing import Dict, Any, List
import statistics

# Add the project root to the Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mcp.server.fastmcp import FastMCP, Context
from mcp_server.fastmcp_server import mcp as nba_mcp_server


class TestPerformanceBenchmarks(unittest.TestCase):
    """Test cases for performance benchmarks"""

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

        # Performance thresholds (in seconds)
        self.thresholds = {
            "algebra_sports_formula": 0.1,  # 100ms
            "algebra_simplify": 0.05,  # 50ms
            "formula_identify_type": 0.05,  # 50ms
            "formula_builder_validate": 0.1,  # 100ms
            "analyze_formula_structure": 0.1,  # 100ms
            "convert_latex_to_sympy": 0.2,  # 200ms
        }

    async def benchmark_algebra_sports_formula(self):
        """Benchmark sports formula calculations"""
        iterations = 100
        times = []

        for _ in range(iterations):
            start_time = time.time()

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

            end_time = time.time()
            times.append(end_time - start_time)

            self.assertTrue(result["success"])

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)
        min_time = min(times)

        print(f"\nSports Formula Calculation Benchmark:")
        print(f"  Iterations: {iterations}")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Median time: {median_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")

        # Check against threshold
        threshold = self.thresholds["algebra_sports_formula"]
        self.assertLess(
            avg_time,
            threshold,
            f"Average time {avg_time:.4f}s exceeds threshold {threshold}s",
        )

        return {
            "tool": "algebra_sports_formula",
            "iterations": iterations,
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "threshold": threshold,
            "passed": avg_time < threshold,
        }

    async def benchmark_formula_validation(self):
        """Benchmark formula validation performance"""
        iterations = 50
        times = []

        test_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",
            "(FGM + 0.5 * 3PM) / FGA",
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            "FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897",
        ]

        for formula in test_formulas:
            for _ in range(iterations // len(test_formulas)):
                start_time = time.time()

                result_tuple = await self.mcp_server.call_tool(
                    "formula_builder_validate",
                    {"params": {"formula": formula, "validation_level": "semantic"}},
                )
                result = result_tuple[1]

                end_time = time.time()
                times.append(end_time - start_time)

                self.assertTrue(result["success"])

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)
        min_time = min(times)

        print(f"\nFormula Validation Benchmark:")
        print(f"  Iterations: {len(times)}")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Median time: {median_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")

        # Check against threshold
        threshold = self.thresholds["formula_builder_validate"]
        self.assertLess(
            avg_time,
            threshold,
            f"Average time {avg_time:.4f}s exceeds threshold {threshold}s",
        )

        return {
            "tool": "formula_builder_validate",
            "iterations": len(times),
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "threshold": threshold,
            "passed": avg_time < threshold,
        }

    async def benchmark_formula_intelligence(self):
        """Benchmark formula intelligence performance"""
        iterations = 50
        times = []

        test_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",
            "(FGM + 0.5 * 3PM) / FGA",
            "ORtg - DRtg",
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
        ]

        for formula in test_formulas:
            for _ in range(iterations // len(test_formulas)):
                start_time = time.time()

                result_tuple = await self.mcp_server.call_tool(
                    "formula_identify_type", {"params": {"formula": formula}}
                )
                result = result_tuple[1]

                end_time = time.time()
                times.append(end_time - start_time)

                self.assertTrue(result["success"])

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)
        min_time = min(times)

        print(f"\nFormula Intelligence Benchmark:")
        print(f"  Iterations: {len(times)}")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Median time: {median_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")

        # Check against threshold
        threshold = self.thresholds["formula_identify_type"]
        self.assertLess(
            avg_time,
            threshold,
            f"Average time {avg_time:.4f}s exceeds threshold {threshold}s",
        )

        return {
            "tool": "formula_identify_type",
            "iterations": len(times),
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "threshold": threshold,
            "passed": avg_time < threshold,
        }

    async def benchmark_formula_extraction(self):
        """Benchmark formula extraction performance"""
        iterations = 25
        times = []

        test_formulas = [
            "PTS / (2 * (FGA + 0.44 * FTA))",
            "(FGM + 0.5 * 3PM) / FGA",
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            "FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897",
        ]

        for formula in test_formulas:
            for _ in range(iterations // len(test_formulas)):
                start_time = time.time()

                result_tuple = await self.mcp_server.call_tool(
                    "analyze_formula_structure", {"params": {"formula": formula}}
                )
                result = result_tuple[1]

                end_time = time.time()
                times.append(end_time - start_time)

                self.assertTrue(result["success"])

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)
        min_time = min(times)

        print(f"\nFormula Extraction Benchmark:")
        print(f"  Iterations: {len(times)}")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Median time: {median_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")

        # Check against threshold
        threshold = self.thresholds["analyze_formula_structure"]
        self.assertLess(
            avg_time,
            threshold,
            f"Average time {avg_time:.4f}s exceeds threshold {threshold}s",
        )

        return {
            "tool": "analyze_formula_structure",
            "iterations": len(times),
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "threshold": threshold,
            "passed": avg_time < threshold,
        }

    async def benchmark_latex_conversion(self):
        """Benchmark LaTeX to SymPy conversion performance"""
        iterations = 20
        times = []

        latex_formulas = [
            r"\frac{PTS}{2 \cdot (FGA + 0.44 \cdot FTA)}",
            r"\frac{FGM + 0.5 \cdot 3PM}{FGA}",
            r"ORtg - DRtg",
            r"\frac{(FGA + 0.44 \cdot FTA + TOV) \cdot \frac{TM\_MP}{5}}{MP \cdot (TM\_FGA + 0.44 \cdot TM\_FTA + TM\_TOV)} \cdot 100",
        ]

        for latex_formula in latex_formulas:
            for _ in range(iterations // len(latex_formulas)):
                start_time = time.time()

                result_tuple = await self.mcp_server.call_tool(
                    "convert_latex_to_sympy",
                    {"params": {"latex_formula": latex_formula}},
                )
                result = result_tuple[1]

                end_time = time.time()
                times.append(end_time - start_time)

                self.assertTrue(result["success"])

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)
        min_time = min(times)

        print(f"\nLaTeX Conversion Benchmark:")
        print(f"  Iterations: {len(times)}")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Median time: {median_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")

        # Check against threshold
        threshold = self.thresholds["convert_latex_to_sympy"]
        self.assertLess(
            avg_time,
            threshold,
            f"Average time {avg_time:.4f}s exceeds threshold {threshold}s",
        )

        return {
            "tool": "convert_latex_to_sympy",
            "iterations": len(times),
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "threshold": threshold,
            "passed": avg_time < threshold,
        }

    async def benchmark_memory_usage(self):
        """Benchmark memory usage during operations"""
        # Start memory tracking
        tracemalloc.start()

        # Perform operations
        operations = 50
        for _ in range(operations):
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

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024

        print(f"\nMemory Usage Benchmark:")
        print(f"  Operations: {operations}")
        print(f"  Current memory: {current_mb:.2f} MB")
        print(f"  Peak memory: {peak_mb:.2f} MB")

        # Check memory usage is reasonable (less than 100MB for 50 operations)
        self.assertLess(
            current_mb, 100, f"Current memory usage {current_mb:.2f} MB exceeds 100MB"
        )
        self.assertLess(
            peak_mb, 200, f"Peak memory usage {peak_mb:.2f} MB exceeds 200MB"
        )

        return {
            "operations": operations,
            "current_memory_mb": current_mb,
            "peak_memory_mb": peak_mb,
            "passed": current_mb < 100 and peak_mb < 200,
        }

    async def benchmark_concurrent_operations(self):
        """Benchmark concurrent operations"""

        async def single_operation():
            result_tuple = await self.mcp_server.call_tool(
                "algebra_sports_formula",
                {
                    "params": {
                        "formula_name": "true_shooting",
                        "stats": self.test_player_stats,
                    }
                },
            )
            return result_tuple[1]

        # Test concurrent operations
        concurrent_count = 10
        start_time = time.time()

        tasks = [single_operation() for _ in range(concurrent_count)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all operations succeeded
        for result in results:
            self.assertTrue(result["success"])

        print(f"\nConcurrent Operations Benchmark:")
        print(f"  Concurrent operations: {concurrent_count}")
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Average time per operation: {total_time / concurrent_count:.4f}s")

        # Should complete in reasonable time
        self.assertLess(
            total_time,
            5.0,
            f"Total time {total_time:.4f}s exceeds 5s for {concurrent_count} operations",
        )

        return {
            "concurrent_count": concurrent_count,
            "total_time": total_time,
            "avg_time_per_operation": total_time / concurrent_count,
            "passed": total_time < 5.0,
        }

    async def run_all_benchmarks(self):
        """Run all benchmarks and return results"""
        print("Starting NBA MCP Server Performance Benchmarks...")

        results = {}

        # Run individual benchmarks
        results["sports_formula"] = await self.benchmark_algebra_sports_formula()
        results["formula_validation"] = await self.benchmark_formula_validation()
        results["formula_intelligence"] = await self.benchmark_formula_intelligence()
        results["formula_extraction"] = await self.benchmark_formula_extraction()
        results["latex_conversion"] = await self.benchmark_latex_conversion()
        results["memory_usage"] = await self.benchmark_memory_usage()
        results["concurrent_operations"] = await self.benchmark_concurrent_operations()

        # Summary
        print(f"\n{'='*60}")
        print("PERFORMANCE BENCHMARK SUMMARY")
        print(f"{'='*60}")

        passed_count = 0
        total_count = len(results)

        for tool_name, result in results.items():
            status = "PASS" if result["passed"] else "FAIL"
            print(
                f"{tool_name:20} | {status:4} | {result.get('avg_time', result.get('total_time', 0)):.4f}s"
            )
            if result["passed"]:
                passed_count += 1

        print(f"{'='*60}")
        print(f"Overall: {passed_count}/{total_count} benchmarks passed")
        print(f"Success rate: {passed_count/total_count*100:.1f}%")
        print(f"{'='*60}")

        return results


class TestScalabilityBenchmarks(unittest.TestCase):
    """Test cases for scalability benchmarks"""

    def setUp(self):
        """Set up test fixtures"""
        self.mcp_server = nba_mcp_server

    async def test_large_dataset_performance(self):
        """Test performance with large datasets"""
        # Create large dataset
        large_dataset = []
        for i in range(100):
            stats = {
                "PTS": 20.0 + i * 0.1,
                "FGM": 8.0 + i * 0.05,
                "FGA": 18.0 + i * 0.1,
                "3PM": 2.0 + i * 0.02,
                "3PA": 6.0 + i * 0.05,
                "FTM": 2.0 + i * 0.01,
                "FTA": 3.0 + i * 0.02,
                "REB": 6.0 + i * 0.03,
                "AST": 5.0 + i * 0.02,
                "STL": 1.0 + i * 0.01,
                "BLK": 0.5 + i * 0.005,
                "TOV": 2.0 + i * 0.01,
                "PF": 2.0 + i * 0.01,
                "MP": 30.0 + i * 0.1,
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
            large_dataset.append(stats)

        # Benchmark processing large dataset
        start_time = time.time()

        for stats in large_dataset:
            result_tuple = await self.mcp_server.call_tool(
                "algebra_sports_formula",
                {"params": {"formula_name": "true_shooting", "stats": stats}},
            )
            result = result_tuple[1]
            self.assertTrue(result["success"])

        end_time = time.time()
        total_time = end_time - start_time

        print(f"\nLarge Dataset Performance:")
        print(f"  Dataset size: {len(large_dataset)} records")
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Average time per record: {total_time / len(large_dataset):.4f}s")

        # Should process 100 records in reasonable time
        self.assertLess(
            total_time,
            10.0,
            f"Total time {total_time:.4f}s exceeds 10s for {len(large_dataset)} records",
        )

        return {
            "dataset_size": len(large_dataset),
            "total_time": total_time,
            "avg_time_per_record": total_time / len(large_dataset),
            "passed": total_time < 10.0,
        }

    async def test_complex_formula_performance(self):
        """Test performance with complex formulas"""
        complex_formulas = [
            "FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897",
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            "(AST * (TM_MP / 5)) / (MP * (TM_FGM - FGM)) * 100",
            "(REB * (TM_MP / 5)) / (MP * (TM_REB + OPP_REB)) * 100",
        ]

        stats = {
            "FGM": 10.0,
            "STL": 2.0,
            "3PM": 3.0,
            "FTM": 5.0,
            "BLK": 1.0,
            "OREB": 2.0,
            "AST": 8.0,
            "DREB": 6.0,
            "PF": 3.0,
            "FTA": 6.0,
            "FGA": 18.0,
            "TOV": 3.0,
            "MP": 35.0,
            "TM_MP": 240.0,
            "TM_FGA": 90.0,
            "TM_FTA": 25.0,
            "TM_TOV": 12.0,
            "TM_FGM": 35.0,
            "TM_REB": 45.0,
            "OPP_REB": 42.0,
        }

        times = []

        for formula in complex_formulas:
            start_time = time.time()

            result_tuple = await self.mcp_server.call_tool(
                "formula_builder_validate",
                {"params": {"formula": formula, "validation_level": "semantic"}},
            )
            result = result_tuple[1]

            end_time = time.time()
            times.append(end_time - start_time)

            self.assertTrue(result["success"])

        avg_time = statistics.mean(times)
        max_time = max(times)

        print(f"\nComplex Formula Performance:")
        print(f"  Formulas tested: {len(complex_formulas)}")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")

        # Complex formulas should still complete in reasonable time
        self.assertLess(
            avg_time,
            0.5,
            f"Average time {avg_time:.4f}s exceeds 0.5s for complex formulas",
        )

        return {
            "formulas_tested": len(complex_formulas),
            "avg_time": avg_time,
            "max_time": max_time,
            "passed": avg_time < 0.5,
        }


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
