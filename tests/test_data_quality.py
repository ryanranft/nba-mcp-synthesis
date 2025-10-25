"""
Tests for data_quality.py module

**Phase 10A Week 2 - Agent 4: Data Validation & Quality**
Tests for 24 expectation methods and validation report generation.
"""

import pytest
import pandas as pd
import numpy as np
from mcp_server.data_quality import (
    DataQualityValidator,
    ValidationResult,
    DataQualityReport,
)


@pytest.fixture
def sample_nba_data():
    """Create sample NBA player data for testing"""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "player_id": range(1, 101),
            "player_name": [f"Player {i}" for i in range(1, 101)],
            "team": np.random.choice(["Lakers", "Warriors", "Celtics", "Heat"], 100),
            "position": np.random.choice(["PG", "SG", "SF", "PF", "C"], 100),
            "points_per_game": np.random.normal(15, 5, 100).clip(0, 35),
            "rebounds_per_game": np.random.normal(7, 3, 100).clip(0, 20),
            "assists_per_game": np.random.normal(5, 2, 100).clip(0, 15),
            "age": np.random.normal(27, 4, 100).clip(19, 40).astype(int),
            "salary": np.random.lognormal(16, 0.5, 100).astype(int),
        }
    )


@pytest.fixture
def validator():
    """Create a data quality validator"""
    return DataQualityValidator(dataset_name="test_nba_data")


# Test 1: expect_column_to_exist
def test_expect_column_to_exist(validator, sample_nba_data):
    """Test column existence expectation"""
    result = validator.expect_column_to_exist(sample_nba_data, "player_id")
    assert result.passed == True  # Use == instead of is for numpy boolean compatibility
    assert result.expectation == "expect_column_to_exist('player_id')"


# Test 2: expect_column_to_exist (failure case)
def test_expect_column_to_exist_failure(validator, sample_nba_data):
    """Test column existence expectation failure"""
    result = validator.expect_column_to_exist(sample_nba_data, "nonexistent_column")
    assert result.passed == False


# Test 3: expect_column_values_to_be_unique
def test_expect_column_values_to_be_unique(validator, sample_nba_data):
    """Test column uniqueness expectation"""
    result = validator.expect_column_values_to_be_unique(sample_nba_data, "player_id")
    assert result.passed == True


# Test 4: expect_column_values_to_be_unique (failure case)
def test_expect_column_values_to_be_unique_failure(validator, sample_nba_data):
    """Test column uniqueness expectation failure"""
    df = sample_nba_data.copy()
    df.loc[0, "team"] = "Lakers"
    df.loc[1, "team"] = "Lakers"  # Duplicate
    result = validator.expect_column_values_to_be_unique(df, "team")
    assert result.passed == False


# Test 5: expect_column_values_to_not_be_null
def test_expect_column_values_to_not_be_null(validator, sample_nba_data):
    """Test null value expectation"""
    result = validator.expect_column_values_to_not_be_null(
        sample_nba_data, "player_name", max_null_ratio=0.0
    )
    assert result.passed == True


# Test 6: expect_column_values_to_not_be_null (with nulls)
def test_expect_column_values_to_not_be_null_with_nulls(validator, sample_nba_data):
    """Test null value expectation with some nulls"""
    df = sample_nba_data.copy()
    df.loc[0:4, "points_per_game"] = None  # 5% nulls
    result = validator.expect_column_values_to_not_be_null(
        df, "points_per_game", max_null_ratio=0.1
    )
    assert result.passed == True


# Test 7: expect_column_values_to_be_in_set
def test_expect_column_values_to_be_in_set(validator, sample_nba_data):
    """Test value set expectation"""
    result = validator.expect_column_values_to_be_in_set(
        sample_nba_data, "position", {"PG", "SG", "SF", "PF", "C"}
    )
    assert result.passed == True


# Test 8: expect_column_values_to_be_in_set (failure case)
def test_expect_column_values_to_be_in_set_failure(validator, sample_nba_data):
    """Test value set expectation failure"""
    df = sample_nba_data.copy()
    df.loc[0, "position"] = "INVALID"
    result = validator.expect_column_values_to_be_in_set(
        df, "position", {"PG", "SG", "SF", "PF", "C"}
    )
    assert result.passed == False


# Test 9: expect_column_values_to_be_between
def test_expect_column_values_to_be_between(validator, sample_nba_data):
    """Test range expectation"""
    result = validator.expect_column_values_to_be_between(
        sample_nba_data, "age", min_value=18, max_value=45
    )
    assert result.passed == True


# Test 10: expect_column_values_to_be_between (failure case)
def test_expect_column_values_to_be_between_failure(validator, sample_nba_data):
    """Test range expectation failure"""
    df = sample_nba_data.copy()
    df.loc[0, "age"] = 50  # Out of range
    result = validator.expect_column_values_to_be_between(
        df, "age", min_value=18, max_value=45
    )
    assert result.passed == False


# Test 11: expect_column_mean_to_be_between
def test_expect_column_mean_to_be_between(validator, sample_nba_data):
    """Test mean range expectation"""
    result = validator.expect_column_mean_to_be_between(
        sample_nba_data, "points_per_game", min_value=10, max_value=20
    )
    assert result.passed == True


# Test 12: expect_column_stdev_to_be_between
def test_expect_column_stdev_to_be_between(validator, sample_nba_data):
    """Test standard deviation range expectation"""
    result = validator.expect_column_stdev_to_be_between(
        sample_nba_data, "points_per_game", min_value=1, max_value=10
    )
    assert result.passed == True


# Test 13: expect_table_row_count_to_be_between
def test_expect_table_row_count_to_be_between(validator, sample_nba_data):
    """Test row count range expectation"""
    result = validator.expect_table_row_count_to_be_between(
        sample_nba_data, min_value=50, max_value=150
    )
    assert result.passed == True


# Test 14: expect_table_column_count_to_equal
def test_expect_table_column_count_to_equal(validator, sample_nba_data):
    """Test column count expectation"""
    result = validator.expect_table_column_count_to_equal(
        sample_nba_data, expected_count=9
    )
    assert result.passed == True


# Test 15: expect_column_values_to_match_pattern
def test_expect_column_values_to_match_pattern(validator):
    """Test pattern matching expectation"""
    df = pd.DataFrame(
        {"email": ["user1@example.com", "user2@example.com", "user3@example.com"]}
    )
    result = validator.expect_column_values_to_match_pattern(
        df, "email", pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"
    )
    assert result.passed == True


# Test 16: expect_column_values_to_be_of_type
def test_expect_column_values_to_be_of_type(validator, sample_nba_data):
    """Test type expectation"""
    result = validator.expect_column_values_to_be_of_type(
        sample_nba_data, "player_id", expected_type="int"
    )
    assert result.passed == True


# Test 17: expect_column_pair_correlation_to_be_less_than
def test_expect_column_pair_correlation_to_be_less_than(validator, sample_nba_data):
    """Test correlation expectation"""
    result = validator.expect_column_pair_correlation_to_be_less_than(
        sample_nba_data, "points_per_game", "rebounds_per_game", max_correlation=0.95
    )
    assert result.passed == True


# Test 18: expect_column_median_to_be_between
def test_expect_column_median_to_be_between(validator, sample_nba_data):
    """Test median range expectation"""
    result = validator.expect_column_median_to_be_between(
        sample_nba_data, "points_per_game", min_value=10, max_value=20
    )
    assert result.passed == True


# Test 19: expect_column_quantile_to_be_between
def test_expect_column_quantile_to_be_between(validator, sample_nba_data):
    """Test quantile range expectation"""
    result = validator.expect_column_quantile_to_be_between(
        sample_nba_data, "points_per_game", quantile=0.75, min_value=15, max_value=25
    )
    assert result.passed == True


# Test 20: expect_column_sum_to_be_between
def test_expect_column_sum_to_be_between(validator, sample_nba_data):
    """Test sum range expectation"""
    result = validator.expect_column_sum_to_be_between(
        sample_nba_data, "points_per_game", min_value=1000, max_value=2000
    )
    assert result.passed == True


# Test 21: expect_column_proportion_of_unique_values_to_be_between
def test_expect_column_proportion_of_unique_values_to_be_between(
    validator, sample_nba_data
):
    """Test unique value proportion expectation"""
    result = validator.expect_column_proportion_of_unique_values_to_be_between(
        sample_nba_data, "player_id", min_proportion=0.9, max_proportion=1.0
    )
    assert result.passed == True


# Test 22: expect_table_row_count_to_equal
def test_expect_table_row_count_to_equal(validator, sample_nba_data):
    """Test exact row count expectation"""
    result = validator.expect_table_row_count_to_equal(
        sample_nba_data, expected_count=100
    )
    assert result.passed == True


# Test 23: expect_column_max_to_be_between
def test_expect_column_max_to_be_between(validator, sample_nba_data):
    """Test maximum value range expectation"""
    result = validator.expect_column_max_to_be_between(
        sample_nba_data, "age", min_value=35, max_value=50
    )
    assert result.passed == True


# Test 24: expect_column_min_to_be_between
def test_expect_column_min_to_be_between(validator, sample_nba_data):
    """Test minimum value range expectation"""
    result = validator.expect_column_min_to_be_between(
        sample_nba_data, "age", min_value=18, max_value=25
    )
    assert result.passed == True


# Test 25: Complete validation workflow with report generation
def test_complete_validation_workflow(validator, sample_nba_data):
    """Test complete validation workflow with report"""
    # Add multiple expectations
    validator.add_expectation(
        lambda df: validator.expect_column_to_exist(df, "player_id")
    )
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_be_unique(df, "player_id")
    )
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_not_be_null(
            df, "player_name", max_null_ratio=0.0
        )
    )
    validator.add_expectation(
        lambda df: validator.expect_column_values_to_be_in_set(
            df, "position", {"PG", "SG", "SF", "PF", "C"}
        )
    )
    validator.add_expectation(
        lambda df: validator.expect_table_row_count_to_be_between(
            df, min_value=50, max_value=150
        )
    )

    # Run validation
    report = validator.validate(sample_nba_data)

    # Verify report
    assert isinstance(report, DataQualityReport)
    assert report.total_expectations == 5
    assert report.passed_expectations >= 4  # Most should pass
    assert report.success_rate >= 80.0  # At least 80% pass rate
    assert report.is_valid or report.failed_expectations <= 1
