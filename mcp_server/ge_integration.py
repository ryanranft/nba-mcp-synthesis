#!/usr/bin/env python3
"""
Great Expectations Integration Module

Provides Python API for executing Great Expectations checkpoints
and integrating with the NBA MCP data validation infrastructure.

Phase 10A Week 2 - Agent 4 - Advanced Integrations

Features:
- Checkpoint execution and management
- Validation result aggregation
- Integration with Week 1 components (error handling, monitoring, RBAC)
- Alert notifications
- Result reporting and metrics

Author: NBA MCP Synthesis System
Created: 2025-10-25
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json
from dataclasses import dataclass, asdict

# Try to import Great Expectations
try:
    import great_expectations as gx
    from great_expectations.core.batch import BatchRequest
    from great_expectations.data_context import FileDataContext
    from great_expectations.checkpoint import SimpleCheckpoint

    GE_AVAILABLE = True
except ImportError:
    GE_AVAILABLE = False

# Week 1 integration
try:
    from mcp_server.error_handling import (
        handle_errors,
        MCPServerError,
        DataValidationError,
    )
    from mcp_server.logging_config import get_logger
    from mcp_server.monitoring import get_health_monitor, track_metric
    from mcp_server.rbac import require_permission

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    # Fallback decorators
    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

    def require_permission(permission: str):
        def decorator(func):
            return func

        return decorator

    def get_logger(name: str):
        return logging.getLogger(name)

    def get_health_monitor():
        return None

    def track_metric(name: str, value: Any):
        pass

    class MCPServerError(Exception):
        """Base MCP server error"""

        pass

    class DataValidationError(MCPServerError):
        """Data validation error"""

        pass


logger = get_logger(__name__)


@dataclass
class ValidationSummary:
    """Summary of validation checkpoint execution"""

    checkpoint_name: str
    success: bool
    total_expectations: int
    passed_expectations: int
    failed_expectations: int
    pass_rate: float
    execution_time_ms: float
    validation_time: str
    dataset_name: str
    row_count: int
    failed_expectation_details: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class GreatExpectationsIntegration:
    """
    Integration wrapper for Great Expectations.

    Provides a simplified Python API for executing checkpoints,
    aggregating results, and integrating with Week 1 infrastructure.

    Attributes:
        context_root_dir: Path to Great Expectations project root
        context: Great Expectations DataContext
        checkpoints: Dictionary of available checkpoints

    Example:
        >>> ge_integration = GreatExpectationsIntegration()
        >>> result = ge_integration.run_checkpoint("player_stats_checkpoint")
        >>> if result.success:
        ...     print(f"Validation passed: {result.pass_rate:.1%}")
    """

    def __init__(
        self,
        context_root_dir: Optional[Union[str, Path]] = None,
        enable_monitoring: bool = True,
    ):
        """
        Initialize Great Expectations integration.

        Args:
            context_root_dir: Path to GE project root (default: auto-detect)
            enable_monitoring: Enable Week 1 monitoring integration

        Raises:
            DataValidationError: If Great Expectations not available or context invalid
        """
        if not GE_AVAILABLE:
            raise DataValidationError(
                "Great Expectations not installed. Install with: pip install great-expectations"
            )

        # Auto-detect context root if not provided
        if context_root_dir is None:
            context_root_dir = self._find_context_root()

        self.context_root_dir = Path(context_root_dir)
        self.enable_monitoring = enable_monitoring and WEEK1_AVAILABLE

        # Initialize context
        self.context = self._initialize_context()

        # Load checkpoints
        self.checkpoints = self._load_checkpoints()

        logger.info(
            f"Initialized Great Expectations integration: "
            f"{len(self.checkpoints)} checkpoints available"
        )

    def _find_context_root(self) -> Path:
        """
        Auto-detect Great Expectations context root.

        Returns:
            Path to GE project root

        Raises:
            DataValidationError: If context root not found
        """
        # Start from current file location
        current = Path(__file__).resolve()

        # Walk up directory tree looking for great_expectations/
        for parent in [current.parent] + list(current.parents):
            ge_dir = parent / "great_expectations"
            if ge_dir.exists() and (ge_dir / "great_expectations.yml").exists():
                return parent

        raise DataValidationError(
            "Could not find Great Expectations context root. "
            "Ensure great_expectations/ directory exists with great_expectations.yml"
        )

    def _initialize_context(self) -> FileDataContext:
        """
        Initialize Great Expectations DataContext.

        Returns:
            Initialized FileDataContext

        Raises:
            DataValidationError: If context initialization fails
        """
        try:
            context = gx.get_context(context_root_dir=str(self.context_root_dir))
            logger.debug(f"Initialized GE context from {self.context_root_dir}")
            return context
        except Exception as e:
            raise DataValidationError(
                f"Failed to initialize Great Expectations context: {e}"
            ) from e

    def _load_checkpoints(self) -> Dict[str, str]:
        """
        Load available checkpoints from filesystem.

        Returns:
            Dictionary of checkpoint names to file paths
        """
        checkpoints_dir = self.context_root_dir / "great_expectations" / "checkpoints"
        checkpoints = {}

        if checkpoints_dir.exists():
            for checkpoint_file in checkpoints_dir.glob("*.yml"):
                checkpoint_name = checkpoint_file.stem
                checkpoints[checkpoint_name] = str(checkpoint_file)
                logger.debug(f"Loaded checkpoint: {checkpoint_name}")

        return checkpoints

    @handle_errors(reraise=True, notify=False)
    @require_permission("data_validator")
    def run_checkpoint(
        self,
        checkpoint_name: str,
        batch_request: Optional[BatchRequest] = None,
        evaluation_parameters: Optional[Dict[str, Any]] = None,
    ) -> ValidationSummary:
        """
        Execute a Great Expectations checkpoint.

        Args:
            checkpoint_name: Name of checkpoint to execute
            batch_request: Optional custom batch request
            evaluation_parameters: Optional runtime evaluation parameters

        Returns:
            ValidationSummary with execution results

        Raises:
            DataValidationError: If checkpoint execution fails

        Example:
            >>> result = ge_integration.run_checkpoint("player_stats_checkpoint")
            >>> print(f"Pass rate: {result.pass_rate:.1%}")
        """
        start_time = datetime.now()

        # Validate checkpoint exists
        if checkpoint_name not in self.checkpoints:
            available = ", ".join(self.checkpoints.keys())
            raise DataValidationError(
                f"Checkpoint '{checkpoint_name}' not found. "
                f"Available checkpoints: {available}"
            )

        logger.info(f"Executing checkpoint: {checkpoint_name}")

        # Build checkpoint run kwargs
        run_kwargs = {}
        if batch_request:
            run_kwargs["validations"] = [{"batch_request": batch_request}]
        if evaluation_parameters:
            run_kwargs["evaluation_parameters"] = evaluation_parameters

        # Execute checkpoint
        try:
            checkpoint_result = self.context.run_checkpoint(
                checkpoint_name=checkpoint_name, **run_kwargs
            )
        except Exception as e:
            logger.error(f"Checkpoint execution failed: {e}")
            raise DataValidationError(
                f"Failed to execute checkpoint '{checkpoint_name}': {e}"
            ) from e

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        # Parse results
        summary = self._parse_checkpoint_result(
            checkpoint_name=checkpoint_name,
            checkpoint_result=checkpoint_result,
            execution_time_ms=execution_time,
        )

        # Track metrics if monitoring enabled
        if self.enable_monitoring:
            self._track_validation_metrics(summary)

        logger.info(
            f"Checkpoint '{checkpoint_name}' completed: "
            f"{summary.pass_rate:.1%} pass rate ({summary.passed_expectations}/"
            f"{summary.total_expectations} expectations)"
        )

        return summary

    def _parse_checkpoint_result(
        self,
        checkpoint_name: str,
        checkpoint_result: Any,
        execution_time_ms: float,
    ) -> ValidationSummary:
        """
        Parse checkpoint result into ValidationSummary.

        Args:
            checkpoint_name: Name of executed checkpoint
            checkpoint_result: Raw checkpoint result from GE
            execution_time_ms: Execution time in milliseconds

        Returns:
            ValidationSummary object
        """
        # Extract first validation result (checkpoints typically have one)
        run_results = checkpoint_result.run_results
        if not run_results:
            raise DataValidationError(
                f"Checkpoint '{checkpoint_name}' returned no validation results"
            )

        # Get first validation result
        validation_result_id, validation_result = list(run_results.items())[0]

        # Extract statistics
        statistics = validation_result["validation_result"]["statistics"]
        total_expectations = statistics["evaluated_expectations"]
        passed_expectations = statistics["successful_expectations"]
        failed_expectations = statistics["unsuccessful_expectations"]
        pass_rate = (
            passed_expectations / total_expectations if total_expectations > 0 else 0.0
        )

        # Extract failed expectation details
        failed_details = []
        for result in validation_result["validation_result"]["results"]:
            if not result["success"]:
                failed_details.append(
                    {
                        "expectation_type": result["expectation_config"][
                            "expectation_type"
                        ],
                        "kwargs": result["expectation_config"]["kwargs"],
                        "exception_info": result.get("exception_info", {}),
                    }
                )

        # Extract dataset info
        meta = validation_result["validation_result"]["meta"]
        dataset_name = meta.get("active_batch_definition", {}).get(
            "data_asset_name", "unknown"
        )
        row_count = (
            meta.get("active_batch_definition", {})
            .get("batch_spec", {})
            .get("row_count", 0)
        )

        # Create summary
        return ValidationSummary(
            checkpoint_name=checkpoint_name,
            success=checkpoint_result.success,
            total_expectations=total_expectations,
            passed_expectations=passed_expectations,
            failed_expectations=failed_expectations,
            pass_rate=pass_rate,
            execution_time_ms=execution_time_ms,
            validation_time=datetime.now().isoformat(),
            dataset_name=dataset_name,
            row_count=row_count,
            failed_expectation_details=failed_details,
        )

    def _track_validation_metrics(self, summary: ValidationSummary) -> None:
        """
        Track validation metrics with Week 1 monitoring.

        Args:
            summary: Validation summary to track
        """
        if not WEEK1_AVAILABLE:
            return

        monitor = get_health_monitor()
        if monitor:
            # Track pass rate
            monitor.track_metric(
                f"ge.checkpoint.{summary.checkpoint_name}.pass_rate", summary.pass_rate
            )

            # Track execution time
            monitor.track_metric(
                f"ge.checkpoint.{summary.checkpoint_name}.execution_time_ms",
                summary.execution_time_ms,
            )

            # Track failed expectations
            monitor.track_metric(
                f"ge.checkpoint.{summary.checkpoint_name}.failed_expectations",
                summary.failed_expectations,
            )

            # Alert if pass rate below threshold
            if summary.pass_rate < 0.90:
                monitor.alert(
                    f"ge.checkpoint.{summary.checkpoint_name}.low_pass_rate",
                    f"Validation pass rate below 90%: {summary.pass_rate:.1%}",
                )

    @handle_errors(reraise=True, notify=False)
    def run_all_checkpoints(
        self,
        evaluation_parameters: Optional[Dict[str, Any]] = None,
    ) -> List[ValidationSummary]:
        """
        Execute all available checkpoints.

        Args:
            evaluation_parameters: Optional runtime evaluation parameters

        Returns:
            List of ValidationSummary for each checkpoint

        Example:
            >>> results = ge_integration.run_all_checkpoints()
            >>> for result in results:
            ...     print(f"{result.checkpoint_name}: {result.pass_rate:.1%}")
        """
        logger.info(f"Executing all checkpoints ({len(self.checkpoints)} total)")

        results = []
        for checkpoint_name in self.checkpoints.keys():
            try:
                summary = self.run_checkpoint(
                    checkpoint_name=checkpoint_name,
                    evaluation_parameters=evaluation_parameters,
                )
                results.append(summary)
            except Exception as e:
                logger.error(f"Failed to run checkpoint '{checkpoint_name}': {e}")
                # Continue with other checkpoints

        logger.info(f"Completed {len(results)}/{len(self.checkpoints)} checkpoints")
        return results

    def aggregate_results(
        self,
        summaries: List[ValidationSummary],
    ) -> Dict[str, Any]:
        """
        Aggregate multiple validation summaries.

        Args:
            summaries: List of ValidationSummary objects

        Returns:
            Aggregated statistics dictionary

        Example:
            >>> results = ge_integration.run_all_checkpoints()
            >>> aggregate = ge_integration.aggregate_results(results)
            >>> print(f"Overall pass rate: {aggregate['overall_pass_rate']:.1%}")
        """
        if not summaries:
            return {
                "total_checkpoints": 0,
                "successful_checkpoints": 0,
                "overall_pass_rate": 0.0,
                "total_expectations": 0,
                "passed_expectations": 0,
                "failed_expectations": 0,
            }

        total_checkpoints = len(summaries)
        successful_checkpoints = sum(1 for s in summaries if s.success)
        total_expectations = sum(s.total_expectations for s in summaries)
        passed_expectations = sum(s.passed_expectations for s in summaries)
        failed_expectations = sum(s.failed_expectations for s in summaries)

        overall_pass_rate = (
            passed_expectations / total_expectations if total_expectations > 0 else 0.0
        )

        return {
            "total_checkpoints": total_checkpoints,
            "successful_checkpoints": successful_checkpoints,
            "overall_pass_rate": overall_pass_rate,
            "total_expectations": total_expectations,
            "passed_expectations": passed_expectations,
            "failed_expectations": failed_expectations,
            "checkpoint_summaries": [s.to_dict() for s in summaries],
        }

    def list_checkpoints(self) -> List[str]:
        """
        Get list of available checkpoint names.

        Returns:
            List of checkpoint names
        """
        return list(self.checkpoints.keys())

    def get_checkpoint_info(self, checkpoint_name: str) -> Dict[str, Any]:
        """
        Get information about a specific checkpoint.

        Args:
            checkpoint_name: Name of checkpoint

        Returns:
            Dictionary with checkpoint information

        Raises:
            DataValidationError: If checkpoint not found
        """
        if checkpoint_name not in self.checkpoints:
            raise DataValidationError(f"Checkpoint '{checkpoint_name}' not found")

        checkpoint_path = Path(self.checkpoints[checkpoint_name])

        return {
            "name": checkpoint_name,
            "path": str(checkpoint_path),
            "exists": checkpoint_path.exists(),
            "size_bytes": (
                checkpoint_path.stat().st_size if checkpoint_path.exists() else 0
            ),
        }
