#!/usr/bin/env python3
"""
Mock Great Expectations Components

Provides mock implementations of Great Expectations classes
for testing without requiring actual GE infrastructure.

Phase 10A Week 2 - Agent 4 - Advanced Integrations

Author: NBA MCP Synthesis System
Created: 2025-10-25
"""

import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class MockExpectationResult:
    """Mock result from a single expectation"""

    success: bool
    expectation_type: str
    expectation_config: Dict[str, Any]
    exception_info: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "expectation_type": self.expectation_type,
            "expectation_config": self.expectation_config,
            "exception_info": self.exception_info or {},
            "result": self.result or {},
        }


class MockExpectationSuite:
    """
    Mock Great Expectations ExpectationSuite.

    Simulates an expectation suite for testing.
    """

    def __init__(
        self,
        suite_name: str,
        expectations: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize mock expectation suite.

        Args:
            suite_name: Name of the suite
            expectations: List of expectation configurations
        """
        self.suite_name = suite_name
        self.expectations = expectations or []

    def add_expectation(self, expectation_config: Dict[str, Any]) -> None:
        """Add an expectation to the suite"""
        self.expectations.append(expectation_config)

    def get_expectations(self) -> List[Dict[str, Any]]:
        """Get all expectations"""
        return self.expectations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "expectation_suite_name": self.suite_name,
            "expectations": self.expectations,
            "meta": {
                "great_expectations_version": "0.18.0",
                "created_at": datetime.now().isoformat(),
            },
        }


class MockValidationResult:
    """
    Mock Great Expectations ValidationResult.

    Simulates validation result for testing.
    """

    def __init__(
        self,
        success: bool = True,
        total_expectations: int = 20,
        successful_expectations: Optional[int] = None,
        dataset_name: str = "mock_dataset",
        row_count: int = 100,
    ):
        """
        Initialize mock validation result.

        Args:
            success: Overall validation success
            total_expectations: Total number of expectations
            successful_expectations: Number of successful expectations (default: all)
            dataset_name: Name of validated dataset
            row_count: Number of rows validated
        """
        self.success = success

        # Calculate expectations
        if successful_expectations is None:
            # If success=True, all pass; otherwise 80% pass
            successful_expectations = (
                total_expectations if success else int(total_expectations * 0.8)
            )

        self.total_expectations = total_expectations
        self.successful_expectations = min(successful_expectations, total_expectations)
        self.unsuccessful_expectations = (
            total_expectations - self.successful_expectations
        )

        self.dataset_name = dataset_name
        self.row_count = row_count

        # Generate mock results
        self.results = self._generate_expectation_results()

        # Statistics
        self.statistics = {
            "evaluated_expectations": self.total_expectations,
            "successful_expectations": self.successful_expectations,
            "unsuccessful_expectations": self.unsuccessful_expectations,
            "success_percent": (
                self.successful_expectations / self.total_expectations * 100
                if self.total_expectations > 0
                else 0.0
            ),
        }

        # Meta information
        self.meta = {
            "active_batch_definition": {
                "data_asset_name": self.dataset_name,
                "batch_spec": {
                    "row_count": self.row_count,
                },
            },
            "validation_time": datetime.now().isoformat(),
        }

    def _generate_expectation_results(self) -> List[MockExpectationResult]:
        """Generate mock expectation results"""
        results = []

        # Common expectation types
        expectation_types = [
            "expect_column_to_exist",
            "expect_column_values_to_not_be_null",
            "expect_column_values_to_be_unique",
            "expect_column_values_to_be_between",
            "expect_table_row_count_to_be_between",
        ]

        for i in range(self.total_expectations):
            # Determine if this expectation passes
            passes = i < self.successful_expectations

            expectation_type = random.choice(expectation_types)

            result = MockExpectationResult(
                success=passes,
                expectation_type=expectation_type,
                expectation_config={
                    "expectation_type": expectation_type,
                    "kwargs": {"column": f"column_{i % 10}"},
                },
                exception_info=(
                    None
                    if passes
                    else {
                        "raised_exception": False,
                        "exception_message": f"Expectation {i} failed",
                    }
                ),
                result={
                    "observed_value": random.random(),
                    "element_count": self.row_count,
                },
            )
            results.append(result)

        return results

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            "success": self.success,
            "statistics": self.statistics,
            "results": [r.to_dict() for r in self.results],
            "meta": self.meta,
        }


class MockCheckpoint:
    """
    Mock Great Expectations Checkpoint.

    Simulates checkpoint execution for testing.
    """

    def __init__(
        self,
        name: str,
        expectation_suite: Optional[MockExpectationSuite] = None,
        default_success: bool = True,
    ):
        """
        Initialize mock checkpoint.

        Args:
            name: Checkpoint name
            expectation_suite: Expectation suite to use
            default_success: Default validation success
        """
        self.name = name
        self.expectation_suite = expectation_suite or MockExpectationSuite(
            suite_name=f"{name}_suite"
        )
        self.default_success = default_success

    def run(
        self,
        validations: Optional[List[Dict[str, Any]]] = None,
        evaluation_parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Simulate checkpoint execution.

        Args:
            validations: List of validation configurations
            evaluation_parameters: Runtime evaluation parameters
            **kwargs: Additional checkpoint run parameters

        Returns:
            Mock checkpoint result
        """
        # Create validation result
        validation_result = MockValidationResult(
            success=self.default_success,
            total_expectations=len(self.expectation_suite.expectations) or 20,
            dataset_name=f"{self.name}_data",
        )

        # Build checkpoint result
        checkpoint_result = {
            "success": validation_result.success,
            "run_id": {
                "run_name": f"{self.name}_run",
                "run_time": datetime.now().isoformat(),
            },
            "run_results": {
                "validation_result_identifier": {
                    "validation_result": validation_result.to_json_dict(),
                }
            },
            "checkpoint_config": {
                "name": self.name,
                "config_version": 1.0,
            },
            "validation_result_url": f"file:///path/to/validations/{self.name}/",
        }

        return checkpoint_result


class MockDataContext:
    """
    Mock Great Expectations DataContext.

    Simulates GE DataContext for testing without requiring
    actual Great Expectations installation.
    """

    def __init__(
        self,
        context_root_dir: Optional[str] = None,
        checkpoints: Optional[Dict[str, MockCheckpoint]] = None,
    ):
        """
        Initialize mock data context.

        Args:
            context_root_dir: Path to GE project root (not used in mock)
            checkpoints: Dictionary of checkpoint name to MockCheckpoint
        """
        self.context_root_dir = context_root_dir or "/mock/ge/context"

        # Initialize checkpoints
        self.checkpoints = checkpoints or {
            "player_stats_checkpoint": MockCheckpoint(
                name="player_stats_checkpoint",
                default_success=True,
            ),
            "game_data_checkpoint": MockCheckpoint(
                name="game_data_checkpoint",
                default_success=True,
            ),
            "team_data_checkpoint": MockCheckpoint(
                name="team_data_checkpoint",
                default_success=True,
            ),
        }

        # Expectation suites
        self.expectation_suites = {
            "player_stats_suite": MockExpectationSuite("player_stats_suite"),
            "game_data_suite": MockExpectationSuite("game_data_suite"),
            "team_data_suite": MockExpectationSuite("team_data_suite"),
        }

    def run_checkpoint(
        self,
        checkpoint_name: str,
        validations: Optional[List[Dict[str, Any]]] = None,
        evaluation_parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> "MockCheckpointResult":
        """
        Run a checkpoint.

        Args:
            checkpoint_name: Name of checkpoint to run
            validations: Optional validation configurations
            evaluation_parameters: Optional runtime parameters
            **kwargs: Additional parameters

        Returns:
            MockCheckpointResult

        Raises:
            ValueError: If checkpoint not found
        """
        if checkpoint_name not in self.checkpoints:
            raise ValueError(
                f"Checkpoint '{checkpoint_name}' not found. "
                f"Available: {list(self.checkpoints.keys())}"
            )

        checkpoint = self.checkpoints[checkpoint_name]
        result_dict = checkpoint.run(
            validations=validations,
            evaluation_parameters=evaluation_parameters,
            **kwargs,
        )

        return MockCheckpointResult(result_dict)

    def list_checkpoints(self) -> List[str]:
        """List available checkpoint names"""
        return list(self.checkpoints.keys())

    def get_checkpoint(self, checkpoint_name: str) -> MockCheckpoint:
        """Get a checkpoint by name"""
        if checkpoint_name not in self.checkpoints:
            raise ValueError(f"Checkpoint '{checkpoint_name}' not found")
        return self.checkpoints[checkpoint_name]

    def add_checkpoint(
        self,
        checkpoint_name: str,
        checkpoint: Optional[MockCheckpoint] = None,
    ) -> None:
        """Add a checkpoint to the context"""
        if checkpoint is None:
            checkpoint = MockCheckpoint(name=checkpoint_name)
        self.checkpoints[checkpoint_name] = checkpoint

    def get_expectation_suite(self, suite_name: str) -> MockExpectationSuite:
        """Get an expectation suite by name"""
        if suite_name not in self.expectation_suites:
            # Create on-demand
            self.expectation_suites[suite_name] = MockExpectationSuite(suite_name)
        return self.expectation_suites[suite_name]


class MockCheckpointResult:
    """
    Mock checkpoint execution result.

    Wraps checkpoint result dictionary with convenience properties.
    """

    def __init__(self, result_dict: Dict[str, Any]):
        """
        Initialize mock checkpoint result.

        Args:
            result_dict: Checkpoint result dictionary
        """
        self._result_dict = result_dict
        self.success = result_dict["success"]
        self.run_results = result_dict["run_results"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self._result_dict

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access"""
        return self._result_dict[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get with default"""
        return self._result_dict.get(key, default)
