"""
Data Quality Testing Module
Validates data quality using expectation-based testing inspired by Great Expectations.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import numpy as np
import pandas as pd
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    expectation: str
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class DataQualityReport:
    """Comprehensive data quality report"""
    dataset_name: str
    total_expectations: int
    passed_expectations: int
    failed_expectations: int
    results: List[ValidationResult]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_expectations == 0:
            return 0.0
        return (self.passed_expectations / self.total_expectations) * 100

    @property
    def is_valid(self) -> bool:
        """Check if all expectations passed"""
        return self.failed_expectations == 0


class DataQualityValidator:
    """
    Data quality validator with expectation-based testing.
    Inspired by Great Expectations framework.
    """

    def __init__(self, dataset_name: str = "unknown"):
        """
        Initialize data quality validator.

        Args:
            dataset_name: Name of the dataset being validated
        """
        self.dataset_name = dataset_name
        self.expectations: List[Callable] = []
        self.results: List[ValidationResult] = []

    def add_expectation(self, expectation_func: Callable):
        """Add a custom expectation function"""
        self.expectations.append(expectation_func)

    def expect_column_to_exist(self, df: pd.DataFrame, column: str) -> ValidationResult:
        """Expect a column to exist in the dataframe"""
        passed = column in df.columns
        return ValidationResult(
            expectation=f"expect_column_to_exist('{column}')",
            passed=passed,
            details={
                "column": column,
                "available_columns": list(df.columns) if not passed else None
            }
        )

    def expect_column_values_to_be_unique(
        self,
        df: pd.DataFrame,
        column: str
    ) -> ValidationResult:
        """Expect all values in a column to be unique"""
        if column not in df.columns:
            return ValidationResult(
                expectation=f"expect_column_values_to_be_unique('{column}')",
                passed=False,
                details={"error": f"Column '{column}' not found"}
            )

        n_unique = df[column].nunique()
        n_total = len(df[column])
        passed = n_unique == n_total

        return ValidationResult(
            expectation=f"expect_column_values_to_be_unique('{column}')",
            passed=passed,
            details={
                "column": column,
                "unique_count": n_unique,
                "total_count": n_total,
                "duplicate_count": n_total - n_unique if not passed else 0
            }
        )

    def expect_column_values_to_not_be_null(
        self,
        df: pd.DataFrame,
        column: str,
        max_null_ratio: float = 0.0
    ) -> ValidationResult:
        """Expect column values to not be null (or within threshold)"""
        if column not in df.columns:
            return ValidationResult(
                expectation=f"expect_column_values_to_not_be_null('{column}')",
                passed=False,
                details={"error": f"Column '{column}' not found"}
            )

        null_count = df[column].isnull().sum()
        total_count = len(df[column])
        null_ratio = null_count / total_count if total_count > 0 else 0
        passed = null_ratio <= max_null_ratio

        return ValidationResult(
            expectation=f"expect_column_values_to_not_be_null('{column}', max_ratio={max_null_ratio})",
            passed=passed,
            details={
                "column": column,
                "null_count": int(null_count),
                "total_count": total_count,
                "null_ratio": float(null_ratio),
                "threshold": max_null_ratio
            }
        )

    def expect_column_values_to_be_in_set(
        self,
        df: pd.DataFrame,
        column: str,
        value_set: set
    ) -> ValidationResult:
        """Expect all column values to be in a specified set"""
        if column not in df.columns:
            return ValidationResult(
                expectation=f"expect_column_values_to_be_in_set('{column}')",
                passed=False,
                details={"error": f"Column '{column}' not found"}
            )

        unexpected_values = set(df[column].dropna().unique()) - value_set
        passed = len(unexpected_values) == 0

        return ValidationResult(
            expectation=f"expect_column_values_to_be_in_set('{column}', {value_set})",
            passed=passed,
            details={
                "column": column,
                "expected_set": list(value_set),
                "unexpected_values": list(unexpected_values) if unexpected_values else None,
                "unexpected_count": len(unexpected_values)
            }
        )

    def expect_column_values_to_be_between(
        self,
        df: pd.DataFrame,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        strict_min: bool = False,
        strict_max: bool = False
    ) -> ValidationResult:
        """Expect column values to be within a numeric range"""
        if column not in df.columns:
            return ValidationResult(
                expectation=f"expect_column_values_to_be_between('{column}')",
                passed=False,
                details={"error": f"Column '{column}' not found"}
            )

        values = df[column].dropna()

        # Check min
        if min_value is not None:
            if strict_min:
                min_violations = (values <= min_value).sum()
            else:
                min_violations = (values < min_value).sum()
        else:
            min_violations = 0

        # Check max
        if max_value is not None:
            if strict_max:
                max_violations = (values >= max_value).sum()
            else:
                max_violations = (values > max_value).sum()
        else:
            max_violations = 0

        total_violations = min_violations + max_violations
        passed = total_violations == 0

        return ValidationResult(
            expectation=f"expect_column_values_to_be_between('{column}', {min_value}, {max_value})",
            passed=passed,
            details={
                "column": column,
                "min_value": min_value,
                "max_value": max_value,
                "violations": int(total_violations),
                "min_violations": int(min_violations),
                "max_violations": int(max_violations),
                "actual_min": float(values.min()) if len(values) > 0 else None,
                "actual_max": float(values.max()) if len(values) > 0 else None
            }
        )

    def expect_column_mean_to_be_between(
        self,
        df: pd.DataFrame,
        column: str,
        min_value: float,
        max_value: float
    ) -> ValidationResult:
        """Expect column mean to be within a range"""
        if column not in df.columns:
            return ValidationResult(
                expectation=f"expect_column_mean_to_be_between('{column}')",
                passed=False,
                details={"error": f"Column '{column}' not found"}
            )

        mean_value = df[column].mean()
        passed = min_value <= mean_value <= max_value

        return ValidationResult(
            expectation=f"expect_column_mean_to_be_between('{column}', {min_value}, {max_value})",
            passed=passed,
            details={
                "column": column,
                "mean": float(mean_value),
                "expected_min": min_value,
                "expected_max": max_value
            }
        )

    def expect_column_stdev_to_be_between(
        self,
        df: pd.DataFrame,
        column: str,
        min_value: float,
        max_value: float
    ) -> ValidationResult:
        """Expect column standard deviation to be within a range"""
        if column not in df.columns:
            return ValidationResult(
                expectation=f"expect_column_stdev_to_be_between('{column}')",
                passed=False,
                details={"error": f"Column '{column}' not found"}
            )

        stdev_value = df[column].std()
        passed = min_value <= stdev_value <= max_value

        return ValidationResult(
            expectation=f"expect_column_stdev_to_be_between('{column}', {min_value}, {max_value})",
            passed=passed,
            details={
                "column": column,
                "stdev": float(stdev_value),
                "expected_min": min_value,
                "expected_max": max_value
            }
        )

    def expect_table_row_count_to_be_between(
        self,
        df: pd.DataFrame,
        min_value: int,
        max_value: int
    ) -> ValidationResult:
        """Expect table row count to be within a range"""
        row_count = len(df)
        passed = min_value <= row_count <= max_value

        return ValidationResult(
            expectation=f"expect_table_row_count_to_be_between({min_value}, {max_value})",
            passed=passed,
            details={
                "row_count": row_count,
                "expected_min": min_value,
                "expected_max": max_value
            }
        )

    def expect_table_column_count_to_equal(
        self,
        df: pd.DataFrame,
        expected_count: int
    ) -> ValidationResult:
        """Expect table to have a specific number of columns"""
        column_count = len(df.columns)
        passed = column_count == expected_count

        return ValidationResult(
            expectation=f"expect_table_column_count_to_equal({expected_count})",
            passed=passed,
            details={
                "column_count": column_count,
                "expected_count": expected_count,
                "columns": list(df.columns)
            }
        )

    def validate(self, df: pd.DataFrame) -> DataQualityReport:
        """
        Run all expectations and generate a data quality report.

        Args:
            df: DataFrame to validate

        Returns:
            DataQualityReport with validation results
        """
        self.results = []

        # Run all registered expectations
        for expectation_func in self.expectations:
            try:
                result = expectation_func(df)
                self.results.append(result)
            except Exception as e:
                logger.error(f"Error running expectation: {e}")
                self.results.append(ValidationResult(
                    expectation=str(expectation_func),
                    passed=False,
                    details={"error": str(e)}
                ))

        # Generate report
        passed_count = sum(1 for r in self.results if r.passed)
        failed_count = len(self.results) - passed_count

        report = DataQualityReport(
            dataset_name=self.dataset_name,
            total_expectations=len(self.results),
            passed_expectations=passed_count,
            failed_expectations=failed_count,
            results=self.results
        )

        # Log summary
        logger.info(
            f"Data quality validation complete for '{self.dataset_name}': "
            f"{report.success_rate:.1f}% passed ({passed_count}/{len(self.results)})"
        )

        return report

    def print_report(self, report: DataQualityReport):
        """Print a formatted validation report"""
        print("\n" + "=" * 80)
        print(f"DATA QUALITY REPORT: {report.dataset_name}")
        print("=" * 80)
        print(f"Timestamp: {report.timestamp}")
        print(f"Total Expectations: {report.total_expectations}")
        print(f"Passed: {report.passed_expectations} ✓")
        print(f"Failed: {report.failed_expectations} ✗")
        print(f"Success Rate: {report.success_rate:.1f}%")
        print(f"Overall Status: {'✅ VALID' if report.is_valid else '❌ INVALID'}")
        print("=" * 80)

        if report.failed_expectations > 0:
            print("\nFAILED EXPECTATIONS:")
            print("-" * 80)
            for result in report.results:
                if not result.passed:
                    print(f"✗ {result.expectation}")
                    for key, value in result.details.items():
                        print(f"    {key}: {value}")
                    print()


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("DATA QUALITY TESTING DEMO")
    print("=" * 80)

    # Create sample NBA dataset
    np.random.seed(42)
    df = pd.DataFrame({
        "player_id": range(1, 101),
        "player_name": [f"Player {i}" for i in range(1, 101)],
        "team": np.random.choice(["Lakers", "Warriors", "Celtics", "Heat"], 100),
        "position": np.random.choice(["PG", "SG", "SF", "PF", "C"], 100),
        "points_per_game": np.random.normal(15, 5, 100).clip(0, 35),
        "rebounds_per_game": np.random.normal(7, 3, 100).clip(0, 20),
        "assists_per_game": np.random.normal(5, 2, 100).clip(0, 15),
        "age": np.random.normal(27, 4, 100).clip(19, 40).astype(int),
        "salary": np.random.lognormal(16, 0.5, 100).astype(int)
    })

    # Add some data quality issues for testing
    df.loc[5, "points_per_game"] = None  # Missing value
    df.loc[10, "age"] = 45  # Outlier
    df.loc[15, "position"] = "UNKNOWN"  # Invalid value

    print(f"\n📊 Sample Dataset: {len(df)} rows, {len(df.columns)} columns")
    print(df.head())

    # Initialize validator
    validator = DataQualityValidator(dataset_name="nba_player_stats")

    # Add expectations
    print("\n" + "=" * 80)
    print("ADDING EXPECTATIONS")
    print("=" * 80)

    # Column existence expectations
    validator.add_expectation(
        lambda df: validator.expect_column_to_exist(df, "player_id")
    )
    validator.add_expectation(
        lambda df: validator.expect_column_to_exist(df, "player_name")
    )
    validator.add_expectation(
        lambda df: validator.expect_column_to_exist(df, "team")
    )

    # Uniqueness expectation
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_be_unique(df, "player_id")
    )

    # Null value expectations
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_not_be_null(df, "player_name", max_null_ratio=0.0)
    )
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_not_be_null(df, "points_per_game", max_null_ratio=0.01)
    )

    # Value set expectations
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_be_in_set(
            df, "position", {"PG", "SG", "SF", "PF", "C"}
        )
    )

    # Range expectations
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_be_between(
            df, "age", min_value=18, max_value=42
        )
    )
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_be_between(
            df, "points_per_game", min_value=0, max_value=40
        )
    )

    # Statistical expectations
    validator.add_expectation(
        lambda df: validator.expect_column_mean_to_be_between(
            df, "points_per_game", min_value=10, max_value=20
        )
    )
    validator.add_expectation(
        lambda df: validator.expect_column_stdev_to_be_between(
            df, "points_per_game", min_value=3, max_value=7
        )
    )

    # Table-level expectations
    validator.add_expectation(
        lambda df: validator.expect_table_row_count_to_be_between(
            df, min_value=50, max_value=150
        )
    )
    validator.add_expectation(
        lambda df: validator.expect_table_column_count_to_equal(df, expected_count=9)
    )

    print(f"Added {len(validator.expectations)} expectations")

    # Run validation
    print("\n" + "=" * 80)
    print("RUNNING VALIDATION")
    print("=" * 80)

    report = validator.validate(df)

    # Print detailed report
    validator.print_report(report)

    print("\n" + "=" * 80)
    print("Data Quality Testing Complete!")
    print("=" * 80)

