#!/usr/bin/env python3
"""
Test Configuration for NBA MCP Server

This module contains configuration settings and utilities for the test suite.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import os
import sys
from typing import Dict, Any, List

# Test configuration
TEST_CONFIG = {
    # Performance thresholds (in seconds)
    "performance_thresholds": {
        "algebra_sports_formula": 0.1,  # 100ms
        "algebra_simplify": 0.05,  # 50ms
        "formula_identify_type": 0.05,  # 50ms
        "formula_builder_validate": 0.1,  # 100ms
        "analyze_formula_structure": 0.1,  # 100ms
        "convert_latex_to_sympy": 0.2,  # 200ms
    },
    # Memory usage limits (in MB)
    "memory_limits": {
        "max_current_memory": 100,  # 100MB
        "max_peak_memory": 200,  # 200MB
    },
    # Test data
    "test_data": {
        "sample_player_stats": {
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
        },
        "test_formulas": [
            "PTS / (2 * (FGA + 0.44 * FTA))",  # True Shooting %
            "(FGM + 0.5 * 3PM) / FGA",  # Effective FG%
            "ORtg - DRtg",  # Net Rating
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",  # Usage Rate
        ],
        "latex_formulas": [
            r"\frac{PTS}{2 \cdot (FGA + 0.44 \cdot FTA)}",
            r"\frac{FGM + 0.5 \cdot 3PM}{FGA}",
            r"ORtg - DRtg",
        ],
        "complex_formulas": [
            "FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897",
            "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            "(AST * (TM_MP / 5)) / (MP * (TM_FGM - FGM)) * 100",
            "(REB * (TM_MP / 5)) / (MP * (TM_REB + OPP_REB)) * 100",
        ],
    },
    # Test iterations
    "iterations": {
        "unit_tests": 1,
        "integration_tests": 1,
        "performance_benchmarks": {
            "algebra_sports_formula": 100,
            "formula_validation": 50,
            "formula_intelligence": 50,
            "formula_extraction": 25,
            "latex_conversion": 20,
            "memory_usage": 50,
            "concurrent_operations": 10,
        },
        "scalability_tests": {
            "large_dataset_size": 100,
            "complex_formula_count": 4,
        },
    },
    # Known results for validation
    "known_results": {
        "lebron_2012_13_per": 31.6,  # Approximate PER for LeBron James 2012-13 season
        "curry_2015_16_ts": 0.669,  # Approximate TS% for Stephen Curry 2015-16 season
    },
}


def get_test_config() -> Dict[str, Any]:
    """Get the test configuration"""
    return TEST_CONFIG


def get_performance_threshold(tool_name: str) -> float:
    """Get performance threshold for a specific tool"""
    return TEST_CONFIG["performance_thresholds"].get(tool_name, 1.0)


def get_memory_limit(limit_type: str) -> float:
    """Get memory limit for a specific type"""
    return TEST_CONFIG["memory_limits"].get(limit_type, 1000.0)


def get_test_data(data_type: str) -> Any:
    """Get test data for a specific type"""
    return TEST_CONFIG["test_data"].get(data_type, {})


def get_iteration_count(test_type: str, tool_name: str = None) -> int:
    """Get iteration count for a specific test"""
    if tool_name:
        return TEST_CONFIG["iterations"][test_type].get(tool_name, 10)
    return TEST_CONFIG["iterations"].get(test_type, 1)


def get_known_result(result_name: str) -> float:
    """Get known result for validation"""
    return TEST_CONFIG["known_results"].get(result_name, 0.0)


# Test utilities
class TestUtils:
    """Utility functions for tests"""

    @staticmethod
    def create_large_dataset(size: int) -> List[Dict[str, float]]:
        """Create a large dataset for scalability testing"""
        dataset = []
        for i in range(size):
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
            dataset.append(stats)
        return dataset

    @staticmethod
    def validate_performance_result(result: Dict[str, Any], tool_name: str) -> bool:
        """Validate performance result against thresholds"""
        threshold = get_performance_threshold(tool_name)
        avg_time = result.get("avg_time", result.get("total_time", 0))
        return avg_time < threshold

    @staticmethod
    def validate_memory_result(result: Dict[str, Any]) -> bool:
        """Validate memory usage result against limits"""
        current_mb = result.get("current_memory_mb", 0)
        peak_mb = result.get("peak_memory_mb", 0)

        max_current = get_memory_limit("max_current_memory")
        max_peak = get_memory_limit("max_peak_memory")

        return current_mb < max_current and peak_mb < max_peak


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""

    @staticmethod
    def generate_player_stats_variations(count: int) -> List[Dict[str, float]]:
        """Generate variations of player stats for testing"""
        base_stats = get_test_data("sample_player_stats")
        variations = []

        for i in range(count):
            variation = base_stats.copy()
            # Add some variation to each stat
            for key, value in variation.items():
                if isinstance(value, (int, float)):
                    variation[key] = value * (0.8 + 0.4 * (i / count))
            variations.append(variation)

        return variations

    @staticmethod
    def generate_formula_variations(base_formula: str, count: int) -> List[str]:
        """Generate variations of a formula for testing"""
        variations = []

        for i in range(count):
            # Simple variation by adding small constants
            variation = base_formula.replace("PTS", f"PTS + {i * 0.1}")
            variations.append(variation)

        return variations

    @staticmethod
    def generate_malformed_inputs() -> List[str]:
        """Generate malformed inputs for error testing"""
        return [
            "",  # Empty string
            "x**",  # Incomplete power
            "x +",  # Incomplete addition
            "**x",  # Invalid syntax
            "x + y +",  # Trailing operator
            "x / 0",  # Division by zero
            "x + y = z",  # Assignment in expression
        ]


# Test assertions
class TestAssertions:
    """Custom assertions for tests"""

    @staticmethod
    def assert_performance_within_threshold(
        actual_time: float, tool_name: str, message: str = None
    ):
        """Assert that performance is within threshold"""
        threshold = get_performance_threshold(tool_name)
        if actual_time >= threshold:
            error_msg = f"Performance {actual_time:.4f}s exceeds threshold {threshold}s for {tool_name}"
            if message:
                error_msg += f": {message}"
            raise AssertionError(error_msg)

    @staticmethod
    def assert_memory_within_limits(
        current_mb: float, peak_mb: float, message: str = None
    ):
        """Assert that memory usage is within limits"""
        max_current = get_memory_limit("max_current_memory")
        max_peak = get_memory_limit("max_peak_memory")

        errors = []
        if current_mb >= max_current:
            errors.append(
                f"Current memory {current_mb:.2f}MB exceeds limit {max_current}MB"
            )
        if peak_mb >= max_peak:
            errors.append(f"Peak memory {peak_mb:.2f}MB exceeds limit {max_peak}MB")

        if errors:
            error_msg = "; ".join(errors)
            if message:
                error_msg += f": {message}"
            raise AssertionError(error_msg)

    @staticmethod
    def assert_result_within_tolerance(
        actual: float, expected: float, tolerance: float = 0.01, message: str = None
    ):
        """Assert that result is within tolerance of expected value"""
        if abs(actual - expected) > tolerance:
            error_msg = f"Result {actual} not within tolerance {tolerance} of expected {expected}"
            if message:
                error_msg += f": {message}"
            raise AssertionError(error_msg)


if __name__ == "__main__":
    # Print configuration for debugging
    print("Test Configuration:")
    print(json.dumps(TEST_CONFIG, indent=2))
