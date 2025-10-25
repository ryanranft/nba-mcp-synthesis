"""
Data Integrity Checker Module
Data integrity and consistency validation for NBA MCP system.

**Phase 10A Week 2 - Agent 4: Data Validation & Quality - Phase 2**
Comprehensive integrity checks: referential integrity, cross-field validation, temporal consistency.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import Enum
from datetime import datetime
import pandas as pd
import numpy as np

# Week 1 Integration
try:
    from mcp_server.error_handling import handle_errors, ErrorContext
    from mcp_server.monitoring import get_health_monitor

    WEEK1_AVAILABLE = True
except ImportError:
    WEEK1_AVAILABLE = False

    def handle_errors(reraise=True, notify=False):
        def decorator(func):
            return func

        return decorator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrityViolationType(Enum):
    """Types of integrity violations"""

    REFERENTIAL = "referential"
    CROSS_FIELD = "cross_field"
    TEMPORAL = "temporal"
    BUSINESS_RULE = "business_rule"


@dataclass
class IntegrityViolation:
    """Represents an integrity violation"""

    violation_type: IntegrityViolationType
    message: str
    field_names: List[str] = dc_field(default_factory=list)
    row_indices: List[int] = dc_field(default_factory=list)
    details: Dict[str, Any] = dc_field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "violation_type": self.violation_type.value,
            "message": self.message,
            "field_names": self.field_names,
            "row_count": len(self.row_indices),
            "details": self.details,
        }


@dataclass
class IntegrityReport:
    """Report of integrity check results"""

    dataset_name: str
    timestamp: datetime
    total_checks: int
    violations: List[IntegrityViolation] = dc_field(default_factory=list)
    passed: bool = True

    @property
    def violation_count(self) -> int:
        """Total number of violations"""
        return len(self.violations)

    @property
    def violation_types(self) -> Dict[str, int]:
        """Count violations by type"""
        counts = {}
        for violation in self.violations:
            vtype = violation.violation_type.value
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp.isoformat(),
            "total_checks": self.total_checks,
            "violation_count": self.violation_count,
            "violation_types": self.violation_types,
            "violations": [v.to_dict() for v in self.violations],
            "passed": self.passed,
        }


class IntegrityChecker:
    """
    Data integrity and consistency checker.

    Provides comprehensive integrity validation:
    - Referential integrity (foreign key constraints)
    - Cross-field validation (mathematical relationships)
    - Temporal consistency (date/time logic)
    - Business rule enforcement
    - NBA-specific integrity checks
    """

    def __init__(self):
        """Initialize integrity checker"""
        self.check_history: List[IntegrityReport] = []
        logger.info("IntegrityChecker initialized")

    @handle_errors(reraise=True, notify=False)
    def check_referential_integrity(
        self,
        df: pd.DataFrame,
        column: str,
        reference_values: Set[Any],
        reference_name: str = "reference",
    ) -> List[IntegrityViolation]:
        """
        Check referential integrity (foreign key constraint).

        Args:
            df: DataFrame to check
            column: Column to validate
            reference_values: Set of valid reference values
            reference_name: Name of reference (for error messages)

        Returns:
            List of IntegrityViolation objects
        """
        violations = []

        if column not in df.columns:
            violations.append(
                IntegrityViolation(
                    violation_type=IntegrityViolationType.REFERENTIAL,
                    message=f"Column '{column}' not found in DataFrame",
                    field_names=[column],
                )
            )
            return violations

        # Find values not in reference set
        invalid_mask = ~df[column].isin(reference_values)
        invalid_rows = df[invalid_mask]

        if len(invalid_rows) > 0:
            violations.append(
                IntegrityViolation(
                    violation_type=IntegrityViolationType.REFERENTIAL,
                    message=f"{len(invalid_rows)} rows have invalid {column} values not in {reference_name}",
                    field_names=[column],
                    row_indices=invalid_rows.index.tolist(),
                    details={
                        "invalid_values": invalid_rows[column].unique().tolist()[:10],  # Limit to 10
                    },
                )
            )

        return violations

    @handle_errors(reraise=True, notify=False)
    def check_cross_field_math(
        self,
        df: pd.DataFrame,
        field_a: str,
        field_b: str,
        field_result: str,
        operation: str = "multiply",
        tolerance: float = 0.01,
    ) -> List[IntegrityViolation]:
        """
        Check mathematical relationships between fields.

        Args:
            df: DataFrame to check
            field_a: First field
            field_b: Second field
            field_result: Result field
            operation: Mathematical operation ('multiply', 'divide', 'add', 'subtract')
            tolerance: Tolerance for floating point comparison

        Returns:
            List of IntegrityViolation objects
        """
        violations = []

        # Check all fields exist
        missing_fields = [f for f in [field_a, field_b, field_result] if f not in df.columns]
        if missing_fields:
            violations.append(
                IntegrityViolation(
                    violation_type=IntegrityViolationType.CROSS_FIELD,
                    message=f"Missing fields: {missing_fields}",
                    field_names=missing_fields,
                )
            )
            return violations

        # Calculate expected values
        if operation == "multiply":
            expected = df[field_a] * df[field_b]
        elif operation == "divide":
            expected = df[field_a] / df[field_b].replace(0, np.nan)
        elif operation == "add":
            expected = df[field_a] + df[field_b]
        elif operation == "subtract":
            expected = df[field_a] - df[field_b]
        else:
            raise ValueError(f"Unknown operation: {operation}")

        # Check for violations (within tolerance)
        actual = df[field_result]
        diff = abs(expected - actual)
        invalid_mask = diff > tolerance

        invalid_rows = df[invalid_mask]

        if len(invalid_rows) > 0:
            violations.append(
                IntegrityViolation(
                    violation_type=IntegrityViolationType.CROSS_FIELD,
                    message=f"{len(invalid_rows)} rows violate {field_a} {operation} {field_b} = {field_result}",
                    field_names=[field_a, field_b, field_result],
                    row_indices=invalid_rows.index.tolist(),
                    details={"operation": operation, "tolerance": tolerance},
                )
            )

        return violations

    @handle_errors(reraise=True, notify=False)
    def check_temporal_consistency(
        self,
        df: pd.DataFrame,
        date_field: str,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
        check_sequence: bool = False,
    ) -> List[IntegrityViolation]:
        """
        Check temporal consistency.

        Args:
            df: DataFrame to check
            date_field: Date/datetime field to validate
            min_date: Minimum valid date
            max_date: Maximum valid date
            check_sequence: Whether to check dates are in sequence

        Returns:
            List of IntegrityViolation objects
        """
        violations = []

        if date_field not in df.columns:
            violations.append(
                IntegrityViolation(
                    violation_type=IntegrityViolationType.TEMPORAL,
                    message=f"Date field '{date_field}' not found",
                    field_names=[date_field],
                )
            )
            return violations

        dates = pd.to_datetime(df[date_field], errors='coerce')

        # Check for unparseable dates
        null_dates = dates.isnull()
        if null_dates.sum() > 0:
            violations.append(
                IntegrityViolation(
                    violation_type=IntegrityViolationType.TEMPORAL,
                    message=f"{null_dates.sum()} rows have invalid date values",
                    field_names=[date_field],
                    row_indices=df[null_dates].index.tolist(),
                )
            )

        # Check min/max dates
        if min_date is not None:
            too_early = dates < pd.Timestamp(min_date)
            if too_early.sum() > 0:
                violations.append(
                    IntegrityViolation(
                        violation_type=IntegrityViolationType.TEMPORAL,
                        message=f"{too_early.sum()} rows have dates before {min_date}",
                        field_names=[date_field],
                        row_indices=df[too_early].index.tolist(),
                    )
                )

        if max_date is not None:
            too_late = dates > pd.Timestamp(max_date)
            if too_late.sum() > 0:
                violations.append(
                    IntegrityViolation(
                        violation_type=IntegrityViolationType.TEMPORAL,
                        message=f"{too_late.sum()} rows have dates after {max_date}",
                        field_names=[date_field],
                        row_indices=df[too_late].index.tolist(),
                    )
                )

        # Check sequence (dates should be monotonically increasing)
        if check_sequence and len(dates) > 1:
            not_increasing = dates.diff() < pd.Timedelta(0)
            if not_increasing.sum() > 0:
                violations.append(
                    IntegrityViolation(
                        violation_type=IntegrityViolationType.TEMPORAL,
                        message=f"{not_increasing.sum()} dates are out of sequence",
                        field_names=[date_field],
                        row_indices=df[not_increasing].index.tolist(),
                    )
                )

        return violations

    @handle_errors(reraise=True, notify=False)
    def check_business_rule(
        self,
        df: pd.DataFrame,
        rule_name: str,
        condition: pd.Series,
    ) -> List[IntegrityViolation]:
        """
        Check custom business rule.

        Args:
            df: DataFrame to check
            rule_name: Name of the rule
            condition: Boolean series (True = valid, False = violation)

        Returns:
            List of IntegrityViolation objects
        """
        violations = []

        invalid_mask = ~condition
        invalid_rows = df[invalid_mask]

        if len(invalid_rows) > 0:
            violations.append(
                IntegrityViolation(
                    violation_type=IntegrityViolationType.BUSINESS_RULE,
                    message=f"{len(invalid_rows)} rows violate business rule: {rule_name}",
                    row_indices=invalid_rows.index.tolist(),
                    details={"rule_name": rule_name},
                )
            )

        return violations

    @handle_errors(reraise=True, notify=False)
    def check_nba_player_integrity(
        self, df: pd.DataFrame, valid_player_ids: Optional[Set[int]] = None
    ) -> List[IntegrityViolation]:
        """
        Check NBA player data integrity.

        Args:
            df: Player DataFrame
            valid_player_ids: Set of valid player IDs (optional)

        Returns:
            List of IntegrityViolation objects
        """
        violations = []

        # Check field goal percentage consistency (FGM / FGA = FG%)
        if all(col in df.columns for col in ["fgm", "fga", "fg_pct"]):
            fg_violations = self.check_cross_field_math(
                df, "fgm", "fga", "fg_pct", operation="divide", tolerance=0.01
            )
            violations.extend(fg_violations)

        # Check total points calculation (PPG × Games = Total Points)
        if all(col in df.columns for col in ["ppg", "games_played", "total_points"]):
            pts_violations = self.check_cross_field_math(
                df, "ppg", "games_played", "total_points", operation="multiply", tolerance=1.0
            )
            violations.extend(pts_violations)

        # Check referential integrity for player IDs
        if valid_player_ids and "player_id" in df.columns:
            ref_violations = self.check_referential_integrity(
                df, "player_id", valid_player_ids, "valid_players"
            )
            violations.extend(ref_violations)

        # Business rules
        if "games_played" in df.columns:
            # Games played should be between 0 and 82 (regular season)
            valid_games = (df["games_played"] >= 0) & (df["games_played"] <= 82)
            game_violations = self.check_business_rule(
                df, "games_played must be 0-82", valid_games
            )
            violations.extend(game_violations)

        if "minutes_per_game" in df.columns:
            # Minutes per game should be between 0 and 48 (max game length)
            valid_minutes = (df["minutes_per_game"] >= 0) & (df["minutes_per_game"] <= 48)
            minute_violations = self.check_business_rule(
                df, "minutes_per_game must be 0-48", valid_minutes
            )
            violations.extend(minute_violations)

        return violations

    @handle_errors(reraise=True, notify=False)
    def check_nba_game_integrity(
        self, df: pd.DataFrame, valid_team_ids: Optional[Set[str]] = None
    ) -> List[IntegrityViolation]:
        """
        Check NBA game data integrity.

        Args:
            df: Game DataFrame
            valid_team_ids: Set of valid team IDs (optional)

        Returns:
            List of IntegrityViolation objects
        """
        violations = []

        # Check that home and away teams are different
        if "home_team" in df.columns and "away_team" in df.columns:
            same_team = df["home_team"] == df["away_team"]
            if same_team.sum() > 0:
                violations.append(
                    IntegrityViolation(
                        violation_type=IntegrityViolationType.BUSINESS_RULE,
                        message=f"{same_team.sum()} games have same home and away team",
                        field_names=["home_team", "away_team"],
                        row_indices=df[same_team].index.tolist(),
                    )
                )

        # Check referential integrity for team IDs
        if valid_team_ids:
            if "home_team" in df.columns:
                home_violations = self.check_referential_integrity(
                    df, "home_team", valid_team_ids, "valid_teams"
                )
                violations.extend(home_violations)

            if "away_team" in df.columns:
                away_violations = self.check_referential_integrity(
                    df, "away_team", valid_team_ids, "valid_teams"
                )
                violations.extend(away_violations)

        # Check scores are non-negative
        if "home_score" in df.columns:
            valid_home_score = df["home_score"] >= 0
            home_score_violations = self.check_business_rule(
                df, "home_score must be >= 0", valid_home_score
            )
            violations.extend(home_score_violations)

        if "away_score" in df.columns:
            valid_away_score = df["away_score"] >= 0
            away_score_violations = self.check_business_rule(
                df, "away_score must be >= 0", valid_away_score
            )
            violations.extend(away_score_violations)

        # Check temporal consistency
        if "date" in df.columns:
            temporal_violations = self.check_temporal_consistency(
                df,
                "date",
                min_date=datetime(1946, 1, 1),  # NBA founded
                max_date=datetime.now(),
            )
            violations.extend(temporal_violations)

        return violations

    @handle_errors(reraise=True, notify=False)
    def check_nba_team_integrity(self, df: pd.DataFrame) -> List[IntegrityViolation]:
        """
        Check NBA team data integrity.

        Args:
            df: Team DataFrame

        Returns:
            List of IntegrityViolation objects
        """
        violations = []

        # Check win percentage calculation (wins / (wins + losses))
        if all(col in df.columns for col in ["wins", "losses", "win_pct"]):
            total_games = df["wins"] + df["losses"]
            expected_pct = df["wins"] / total_games.replace(0, np.nan)
            diff = abs(expected_pct - df["win_pct"])
            invalid_pct = diff > 0.01

            if invalid_pct.sum() > 0:
                violations.append(
                    IntegrityViolation(
                        violation_type=IntegrityViolationType.CROSS_FIELD,
                        message=f"{invalid_pct.sum()} teams have incorrect win percentage",
                        field_names=["wins", "losses", "win_pct"],
                        row_indices=df[invalid_pct].index.tolist(),
                    )
                )

        # Check wins and losses are non-negative
        if "wins" in df.columns:
            valid_wins = df["wins"] >= 0
            win_violations = self.check_business_rule(df, "wins must be >= 0", valid_wins)
            violations.extend(win_violations)

        if "losses" in df.columns:
            valid_losses = df["losses"] >= 0
            loss_violations = self.check_business_rule(df, "losses must be >= 0", valid_losses)
            violations.extend(loss_violations)

        # Check valid conference values
        if "conference" in df.columns:
            valid_conferences = {"East", "West", "Eastern", "Western"}
            conference_in_valid = df["conference"].isin(valid_conferences)
            conf_violations = self.check_business_rule(
                df, f"conference must be in {valid_conferences}", conference_in_valid
            )
            violations.extend(conf_violations)

        return violations

    @handle_errors(reraise=True, notify=False)
    def check(
        self,
        df: pd.DataFrame,
        dataset_name: str = "dataset",
        checks: Optional[List[str]] = None,
    ) -> IntegrityReport:
        """
        Perform comprehensive integrity checks.

        Args:
            df: DataFrame to check
            dataset_name: Name of the dataset
            checks: List of check names to run (None = determine from dataset_name)

        Returns:
            IntegrityReport
        """
        report = IntegrityReport(
            dataset_name=dataset_name,
            timestamp=datetime.now(),
            total_checks=0,
        )

        # Determine which checks to run
        if checks is None:
            if "player" in dataset_name.lower():
                checks = ["nba_player"]
            elif "game" in dataset_name.lower():
                checks = ["nba_game"]
            elif "team" in dataset_name.lower():
                checks = ["nba_team"]
            else:
                checks = []

        # Run checks
        for check_name in checks:
            if check_name == "nba_player":
                violations = self.check_nba_player_integrity(df)
                report.violations.extend(violations)
                report.total_checks += 1
            elif check_name == "nba_game":
                violations = self.check_nba_game_integrity(df)
                report.violations.extend(violations)
                report.total_checks += 1
            elif check_name == "nba_team":
                violations = self.check_nba_team_integrity(df)
                report.violations.extend(violations)
                report.total_checks += 1

        # Determine pass/fail
        report.passed = len(report.violations) == 0

        # Save to history
        self.check_history.append(report)

        # Track metrics
        if WEEK1_AVAILABLE:
            self._track_metrics(report)

        return report

    def _track_metrics(self, report: IntegrityReport) -> None:
        """Track integrity check metrics"""
        try:
            monitor = get_health_monitor()
            dataset = report.dataset_name

            monitor.track_metric(f"integrity.{dataset}.total_checks", report.total_checks)
            monitor.track_metric(f"integrity.{dataset}.violations", report.violation_count)
            monitor.track_metric(f"integrity.{dataset}.passed", 1 if report.passed else 0)

        except Exception as e:
            logger.error(f"Failed to track metrics: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get integrity check statistics"""
        if not self.check_history:
            return {
                "total_checks": 0,
                "total_violations": 0,
                "pass_rate": 0.0,
            }

        total_checks = sum(r.total_checks for r in self.check_history)
        total_violations = sum(r.violation_count for r in self.check_history)
        passed = sum(1 for r in self.check_history if r.passed)

        return {
            "total_checks": total_checks,
            "total_violations": total_violations,
            "pass_rate": passed / len(self.check_history) if self.check_history else 0.0,
            "datasets_checked": len(self.check_history),
        }
