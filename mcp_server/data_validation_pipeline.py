"""
Data Validation Pipeline Module
Orchestrates end-to-end data validation workflows for NBA MCP system.

**Phase 10A Week 2 - Agent 4: Data Validation & Quality - Phase 2**
Comprehensive pipeline for data ingestion, schema validation, quality checks, and business rules.
"""

import logging
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Week 1 Integration
try:
    from mcp_server.error_handling import handle_errors, ErrorContext, get_error_handler
    from mcp_server.monitoring import get_health_monitor, track_metric
    from mcp_server.auth_enhanced import require_permission, Permission

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

    def require_permission(permission):
        def decorator(func):
            return func

        return decorator

    class Permission:
        READ = "read"
        WRITE = "write"
        ADMIN = "admin"

# Phase 1 Integration
try:
    from mcp_server.data_quality import DataQualityChecker, DataQualityReport
    from mcp_server.validation import (
        PlayerStatsModel,
        GameDataModel,
        TeamDataModel,
        validate_dataframe_schema,
    )

    PHASE1_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline execution stages"""

    INGESTION = "ingestion"
    SCHEMA_VALIDATION = "schema_validation"
    QUALITY_CHECK = "quality_check"
    BUSINESS_RULES = "business_rules"
    PROFILING = "profiling"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationSeverity(Enum):
    """Validation issue severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""

    stage: PipelineStage
    severity: ValidationSeverity
    message: str
    field_name: Optional[str] = None
    row_count: Optional[int] = None
    details: Dict[str, Any] = dc_field(default_factory=dict)
    timestamp: datetime = dc_field(default_factory=datetime.now)


@dataclass
class PipelineResult:
    """Result of pipeline execution"""

    pipeline_id: str
    dataset_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    current_stage: PipelineStage = PipelineStage.INGESTION
    passed: bool = False
    issues: List[ValidationIssue] = dc_field(default_factory=list)
    metrics: Dict[str, Any] = dc_field(default_factory=dict)
    data_summary: Dict[str, Any] = dc_field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Calculate pipeline duration"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def critical_issues(self) -> List[ValidationIssue]:
        """Get critical issues"""
        return [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]

    @property
    def error_issues(self) -> List[ValidationIssue]:
        """Get error issues"""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "pipeline_id": self.pipeline_id,
            "dataset_name": self.dataset_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_stage": self.current_stage.value,
            "passed": self.passed,
            "duration_seconds": self.duration_seconds,
            "issues": [
                {
                    "stage": i.stage.value,
                    "severity": i.severity.value,
                    "message": i.message,
                    "field": i.field_name,
                    "row_count": i.row_count,
                    "details": i.details,
                }
                for i in self.issues
            ],
            "metrics": self.metrics,
            "data_summary": self.data_summary,
        }


@dataclass
class PipelineConfig:
    """Configuration for validation pipeline"""

    # Stage enablement
    enable_schema_validation: bool = True
    enable_quality_check: bool = True
    enable_business_rules: bool = True
    enable_profiling: bool = False

    # Quality thresholds
    min_quality_score: float = 0.9
    max_null_percentage: float = 0.05
    max_duplicate_percentage: float = 0.01

    # Business rule thresholds (NBA-specific)
    max_points_per_game: float = 200.0
    min_points_per_game: float = 0.0
    max_field_goal_percentage: float = 1.0
    min_field_goal_percentage: float = 0.0

    # Pipeline behavior
    fail_on_critical: bool = True
    fail_on_error: bool = False
    continue_on_warning: bool = True

    # Output settings
    save_results: bool = True
    output_dir: Path = dc_field(default_factory=lambda: Path("validation_results"))


class DataValidationPipeline:
    """
    End-to-end data validation pipeline.

    Orchestrates multi-stage validation workflow:
    1. Data ingestion
    2. Schema validation
    3. Data quality checks
    4. Business rule enforcement
    5. Data profiling (optional)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize validation pipeline.

        Args:
            config: Pipeline configuration (uses defaults if not provided)
        """
        self.config = config or PipelineConfig()
        self.execution_history: List[PipelineResult] = []

        # Initialize Phase 1 components if available
        if PHASE1_AVAILABLE:
            self.quality_checker = DataQualityChecker("pipeline")
        else:
            self.quality_checker = None

        logger.info("DataValidationPipeline initialized with config: %s", self.config)

    @handle_errors(reraise=True, notify=False)
    def validate(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        schema: Optional[Dict[str, Any]] = None,
        custom_rules: Optional[List[Callable]] = None,
    ) -> PipelineResult:
        """
        Execute full validation pipeline.

        Args:
            df: DataFrame to validate
            dataset_name: Name of the dataset
            schema: Expected schema (column names and types)
            custom_rules: Custom validation rules

        Returns:
            PipelineResult with validation outcome
        """
        pipeline_id = f"{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = PipelineResult(
            pipeline_id=pipeline_id,
            dataset_name=dataset_name,
            start_time=datetime.now(),
        )

        try:
            # Stage 1: Ingestion
            result.current_stage = PipelineStage.INGESTION
            self._validate_ingestion(df, result)

            # Stage 2: Schema Validation
            if self.config.enable_schema_validation and schema:
                result.current_stage = PipelineStage.SCHEMA_VALIDATION
                self._validate_schema(df, schema, result)

            # Stage 3: Quality Check
            if self.config.enable_quality_check:
                result.current_stage = PipelineStage.QUALITY_CHECK
                self._validate_quality(df, result)

            # Stage 4: Business Rules
            if self.config.enable_business_rules:
                result.current_stage = PipelineStage.BUSINESS_RULES
                self._validate_business_rules(df, dataset_name, result)

            # Stage 5: Custom Rules
            if custom_rules:
                for rule in custom_rules:
                    self._apply_custom_rule(df, rule, result)

            # Stage 6: Profiling (optional)
            if self.config.enable_profiling:
                result.current_stage = PipelineStage.PROFILING
                self._profile_data(df, result)

            # Determine pass/fail
            result.passed = self._determine_pass_fail(result)
            result.current_stage = (
                PipelineStage.COMPLETED if result.passed else PipelineStage.FAILED
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            result.current_stage = PipelineStage.FAILED
            result.passed = False
            result.issues.append(
                ValidationIssue(
                    stage=result.current_stage,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Pipeline execution failed: {str(e)}",
                )
            )

        finally:
            result.end_time = datetime.now()
            self.execution_history.append(result)

            # Save results if configured
            if self.config.save_results:
                self._save_results(result)

            # Track metrics if Week 1 available
            if WEEK1_AVAILABLE:
                self._track_metrics(result)

        return result

    def _validate_ingestion(self, df: pd.DataFrame, result: PipelineResult) -> None:
        """Validate data ingestion"""
        result.data_summary["row_count"] = len(df)
        result.data_summary["column_count"] = len(df.columns)
        result.data_summary["columns"] = list(df.columns)
        result.data_summary["dtypes"] = {
            col: str(dtype) for col, dtype in df.dtypes.items()
        }

        # Check for empty dataset
        if len(df) == 0:
            result.issues.append(
                ValidationIssue(
                    stage=PipelineStage.INGESTION,
                    severity=ValidationSeverity.ERROR,
                    message="Dataset is empty",
                )
            )

        # Check for minimum rows
        if len(df) < 10:
            result.issues.append(
                ValidationIssue(
                    stage=PipelineStage.INGESTION,
                    severity=ValidationSeverity.WARNING,
                    message=f"Dataset has only {len(df)} rows",
                    row_count=len(df),
                )
            )

    def _validate_schema(
        self, df: pd.DataFrame, schema: Dict[str, Any], result: PipelineResult
    ) -> None:
        """Validate DataFrame schema"""
        expected_columns = set(schema.get("columns", []))
        actual_columns = set(df.columns)

        # Check for missing columns
        missing_columns = expected_columns - actual_columns
        if missing_columns:
            result.issues.append(
                ValidationIssue(
                    stage=PipelineStage.SCHEMA_VALIDATION,
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required columns: {missing_columns}",
                    details={"missing_columns": list(missing_columns)},
                )
            )

        # Check for unexpected columns
        extra_columns = actual_columns - expected_columns
        if extra_columns:
            result.issues.append(
                ValidationIssue(
                    stage=PipelineStage.SCHEMA_VALIDATION,
                    severity=ValidationSeverity.WARNING,
                    message=f"Unexpected columns found: {extra_columns}",
                    details={"extra_columns": list(extra_columns)},
                )
            )

        # Validate column types
        expected_types = schema.get("types", {})
        for col, expected_type in expected_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if actual_type != expected_type:
                    result.issues.append(
                        ValidationIssue(
                            stage=PipelineStage.SCHEMA_VALIDATION,
                            severity=ValidationSeverity.WARNING,
                            message=f"Column '{col}' has type '{actual_type}', expected '{expected_type}'",
                            field_name=col,
                            details={
                                "expected_type": expected_type,
                                "actual_type": actual_type,
                            },
                        )
                    )

    def _validate_quality(self, df: pd.DataFrame, result: PipelineResult) -> None:
        """Validate data quality"""
        # Check null values
        null_counts = df.isnull().sum()
        total_rows = len(df)

        for col in df.columns:
            null_pct = null_counts[col] / total_rows if total_rows > 0 else 0
            if null_pct > self.config.max_null_percentage:
                result.issues.append(
                    ValidationIssue(
                        stage=PipelineStage.QUALITY_CHECK,
                        severity=ValidationSeverity.WARNING,
                        message=f"Column '{col}' has {null_pct:.2%} null values (threshold: {self.config.max_null_percentage:.2%})",
                        field_name=col,
                        details={"null_percentage": null_pct, "null_count": int(null_counts[col])},
                    )
                )

        # Check duplicates
        duplicate_count = df.duplicated().sum()
        duplicate_pct = duplicate_count / total_rows if total_rows > 0 else 0
        if duplicate_pct > self.config.max_duplicate_percentage:
            result.issues.append(
                ValidationIssue(
                    stage=PipelineStage.QUALITY_CHECK,
                    severity=ValidationSeverity.WARNING,
                    message=f"Dataset has {duplicate_pct:.2%} duplicate rows (threshold: {self.config.max_duplicate_percentage:.2%})",
                    row_count=int(duplicate_count),
                    details={"duplicate_percentage": duplicate_pct},
                )
            )

        # Use Phase 1 quality checker if available
        if self.quality_checker and PHASE1_AVAILABLE:
            try:
                quality_report = self.quality_checker.validate(df)
                result.metrics["quality_score"] = quality_report.success_rate

                if quality_report.success_rate < self.config.min_quality_score:
                    result.issues.append(
                        ValidationIssue(
                            stage=PipelineStage.QUALITY_CHECK,
                            severity=ValidationSeverity.ERROR,
                            message=f"Quality score {quality_report.success_rate:.2%} below threshold {self.config.min_quality_score:.2%}",
                            details={"quality_report": quality_report.to_dict()},
                        )
                    )
            except Exception as e:
                logger.warning(f"Quality checker failed: {e}")

    def _validate_business_rules(
        self, df: pd.DataFrame, dataset_name: str, result: PipelineResult
    ) -> None:
        """Validate NBA-specific business rules"""
        # Player stats validation
        if "player" in dataset_name.lower() or "ppg" in df.columns:
            self._validate_player_stats(df, result)

        # Game data validation
        if "game" in dataset_name.lower() or any(
            col in df.columns for col in ["home_score", "away_score"]
        ):
            self._validate_game_data(df, result)

        # Team data validation
        if "team" in dataset_name.lower() or "win_pct" in df.columns:
            self._validate_team_data(df, result)

    def _validate_player_stats(
        self, df: pd.DataFrame, result: PipelineResult
    ) -> None:
        """Validate player statistics"""
        # Check PPG range
        if "ppg" in df.columns:
            invalid_ppg = df[
                (df["ppg"] < 0) | (df["ppg"] > self.config.max_points_per_game)
            ]
            if len(invalid_ppg) > 0:
                result.issues.append(
                    ValidationIssue(
                        stage=PipelineStage.BUSINESS_RULES,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_ppg)} rows with invalid PPG values",
                        field_name="ppg",
                        row_count=len(invalid_ppg),
                    )
                )

        # Check FG% range
        if "fg_pct" in df.columns:
            invalid_fg = df[
                (df["fg_pct"] < self.config.min_field_goal_percentage)
                | (df["fg_pct"] > self.config.max_field_goal_percentage)
            ]
            if len(invalid_fg) > 0:
                result.issues.append(
                    ValidationIssue(
                        stage=PipelineStage.BUSINESS_RULES,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_fg)} rows with invalid FG% values",
                        field_name="fg_pct",
                        row_count=len(invalid_fg),
                    )
                )

    def _validate_game_data(self, df: pd.DataFrame, result: PipelineResult) -> None:
        """Validate game data"""
        # Check score validity
        if "home_score" in df.columns and "away_score" in df.columns:
            invalid_scores = df[(df["home_score"] < 0) | (df["away_score"] < 0)]
            if len(invalid_scores) > 0:
                result.issues.append(
                    ValidationIssue(
                        stage=PipelineStage.BUSINESS_RULES,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_scores)} rows with negative scores",
                        row_count=len(invalid_scores),
                    )
                )

            # Check for unrealistic scores
            unrealistic_scores = df[
                (df["home_score"] > 200) | (df["away_score"] > 200)
            ]
            if len(unrealistic_scores) > 0:
                result.issues.append(
                    ValidationIssue(
                        stage=PipelineStage.BUSINESS_RULES,
                        severity=ValidationSeverity.WARNING,
                        message=f"Found {len(unrealistic_scores)} rows with unusually high scores (>200)",
                        row_count=len(unrealistic_scores),
                    )
                )

    def _validate_team_data(self, df: pd.DataFrame, result: PipelineResult) -> None:
        """Validate team data"""
        # Check win percentage
        if "win_pct" in df.columns:
            invalid_pct = df[(df["win_pct"] < 0) | (df["win_pct"] > 1)]
            if len(invalid_pct) > 0:
                result.issues.append(
                    ValidationIssue(
                        stage=PipelineStage.BUSINESS_RULES,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_pct)} rows with invalid win percentage",
                        field_name="win_pct",
                        row_count=len(invalid_pct),
                    )
                )

    def _apply_custom_rule(
        self, df: pd.DataFrame, rule: Callable, result: PipelineResult
    ) -> None:
        """Apply custom validation rule"""
        try:
            rule_result = rule(df)
            if isinstance(rule_result, str):
                # Rule returned an error message
                result.issues.append(
                    ValidationIssue(
                        stage=PipelineStage.BUSINESS_RULES,
                        severity=ValidationSeverity.WARNING,
                        message=f"Custom rule failed: {rule_result}",
                    )
                )
            elif not rule_result:
                # Rule returned False
                result.issues.append(
                    ValidationIssue(
                        stage=PipelineStage.BUSINESS_RULES,
                        severity=ValidationSeverity.WARNING,
                        message=f"Custom rule '{rule.__name__}' failed",
                    )
                )
        except Exception as e:
            result.issues.append(
                ValidationIssue(
                    stage=PipelineStage.BUSINESS_RULES,
                    severity=ValidationSeverity.ERROR,
                    message=f"Custom rule '{rule.__name__}' raised exception: {str(e)}",
                )
            )

    def _profile_data(self, df: pd.DataFrame, result: PipelineResult) -> None:
        """Generate data profile"""
        profile = {
            "numeric_columns": [],
            "categorical_columns": [],
            "datetime_columns": [],
        }

        for col in df.columns:
            dtype = df[col].dtype
            if pd.api.types.is_numeric_dtype(dtype):
                profile["numeric_columns"].append(
                    {
                        "name": col,
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "median": float(df[col].median()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None,
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    }
                )
            elif pd.api.types.is_categorical_dtype(dtype) or dtype == object:
                profile["categorical_columns"].append(
                    {
                        "name": col,
                        "unique_values": int(df[col].nunique()),
                        "most_common": str(df[col].mode()[0]) if len(df[col].mode()) > 0 else None,
                    }
                )
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                profile["datetime_columns"].append(
                    {
                        "name": col,
                        "min": df[col].min().isoformat() if not df[col].isnull().all() else None,
                        "max": df[col].max().isoformat() if not df[col].isnull().all() else None,
                    }
                )

        result.data_summary["profile"] = profile

    def _determine_pass_fail(self, result: PipelineResult) -> bool:
        """Determine if pipeline passed or failed"""
        if self.config.fail_on_critical and result.critical_issues:
            return False
        if self.config.fail_on_error and result.error_issues:
            return False
        return True

    def _save_results(self, result: PipelineResult) -> None:
        """Save validation results to disk"""
        try:
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            output_file = self.config.output_dir / f"{result.pipeline_id}.json"

            with open(output_file, "w") as f:
                json.dump(result.to_dict(), f, indent=2, default=str)

            logger.info(f"Validation results saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    def _track_metrics(self, result: PipelineResult) -> None:
        """Track metrics with Week 1 monitoring"""
        try:
            monitor = get_health_monitor()
            dataset = result.dataset_name

            # Track success/failure
            monitor.track_metric(f"validation.{dataset}.passed", 1 if result.passed else 0)

            # Track duration
            monitor.track_metric(
                f"validation.{dataset}.duration_seconds", result.duration_seconds
            )

            # Track issue counts
            monitor.track_metric(
                f"validation.{dataset}.critical_issues", len(result.critical_issues)
            )
            monitor.track_metric(
                f"validation.{dataset}.error_issues", len(result.error_issues)
            )
            monitor.track_metric(f"validation.{dataset}.total_issues", len(result.issues))

            # Alert on critical issues
            if result.critical_issues:
                logger.warning(
                    f"Critical validation issues found for {dataset}: {len(result.critical_issues)}"
                )

        except Exception as e:
            logger.error(f"Failed to track metrics: {e}")

    @require_permission(Permission.READ)
    def get_execution_history(
        self, dataset_name: Optional[str] = None, limit: int = 10
    ) -> List[PipelineResult]:
        """
        Get pipeline execution history.

        Args:
            dataset_name: Filter by dataset name (optional)
            limit: Maximum number of results to return

        Returns:
            List of PipelineResult objects
        """
        history = self.execution_history

        if dataset_name:
            history = [r for r in history if r.dataset_name == dataset_name]

        return history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
            }

        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.passed)

        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_duration_seconds": sum(r.duration_seconds for r in self.execution_history)
            / total
            if total > 0
            else 0.0,
        }
