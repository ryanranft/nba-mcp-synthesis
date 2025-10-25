"""
Tests for Data Cleaning Module

**Phase 10A Week 2 - Agent 4: Data Validation & Quality - Phase 2**
Comprehensive tests for data_cleaning.py module.
"""

import pytest
import pandas as pd
import numpy as np
from scipy import stats

from mcp_server.data_cleaning import (
    DataCleaner,
    OutlierMethod,
    ImputationStrategy,
    ScalingMethod,
    CleaningReport,
)


@pytest.fixture
def sample_data_with_outliers():
    """Sample data with outliers"""
    np.random.seed(42)
    data = np.random.normal(100, 15, 100)
    # Add outliers
    data[0] = 200  # High outlier
    data[1] = 0  # Low outlier
    return pd.DataFrame({"value": data, "group": ["A"] * 50 + ["B"] * 50})


@pytest.fixture
def sample_data_with_missing():
    """Sample data with missing values"""
    return pd.DataFrame(
        {
            "numeric": [1.0, 2.0, np.nan, 4.0, 5.0, np.nan, 7.0, 8.0, 9.0, 10.0],
            "categorical": ["A", "B", None, "D", "E", "F", None, "H", "I", "J"],
            "mixed": [1, 2, 3, None, 5, 6, 7, None, 9, 10],
        }
    )


@pytest.fixture
def sample_data_with_duplicates():
    """Sample data with duplicates"""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 1, 2, 4, 5],
            "name": ["A", "B", "C", "A", "B", "D", "E"],
            "value": [10, 20, 30, 10, 20, 40, 50],
        }
    )


@pytest.fixture
def sample_numeric_data():
    """Sample numeric data for scaling"""
    return pd.DataFrame(
        {
            "col1": [1, 2, 3, 4, 5],
            "col2": [10, 20, 30, 40, 50],
            "col3": [100, 200, 300, 400, 500],
        }
    )


# Test 1: DataCleaner initialization
def test_data_cleaner_initialization():
    """Test DataCleaner initialization"""
    cleaner = DataCleaner()
    assert cleaner.cleaning_history == []


# Test 2: Detect outliers using IQR method
def test_detect_outliers_iqr(sample_data_with_outliers):
    """Test IQR outlier detection"""
    cleaner = DataCleaner()
    outlier_mask = cleaner.detect_outliers_iqr(
        sample_data_with_outliers, columns=["value"], threshold=1.5
    )

    assert isinstance(outlier_mask, pd.Series)
    assert outlier_mask.dtype == bool
    assert outlier_mask.sum() >= 2  # At least the 2 outliers we added


# Test 3: Detect outliers using Z-score method
def test_detect_outliers_zscore(sample_data_with_outliers):
    """Test Z-score outlier detection"""
    cleaner = DataCleaner()
    outlier_mask = cleaner.detect_outliers_zscore(
        sample_data_with_outliers, columns=["value"], threshold=3.0
    )

    assert isinstance(outlier_mask, pd.Series)
    assert outlier_mask.dtype == bool
    assert outlier_mask.sum() >= 2  # At least the 2 outliers we added


# Test 4: Detect outliers using Isolation Forest
def test_detect_outliers_isolation_forest(sample_data_with_outliers):
    """Test Isolation Forest outlier detection"""
    cleaner = DataCleaner()
    outlier_mask = cleaner.detect_outliers_isolation_forest(
        sample_data_with_outliers, columns=["value"], contamination=0.1
    )

    assert isinstance(outlier_mask, pd.Series)
    assert outlier_mask.dtype == bool
    # Should detect some outliers
    assert outlier_mask.sum() > 0


# Test 5: Remove outliers
def test_remove_outliers(sample_data_with_outliers):
    """Test outlier removal"""
    cleaner = DataCleaner()
    initial_rows = len(sample_data_with_outliers)

    cleaned_df, outliers_count = cleaner.remove_outliers(
        sample_data_with_outliers, method=OutlierMethod.IQR, columns=["value"]
    )

    assert len(cleaned_df) < initial_rows
    assert outliers_count == initial_rows - len(cleaned_df)
    assert outliers_count > 0


# Test 6: Impute missing values with mean
def test_impute_missing_mean(sample_data_with_missing):
    """Test mean imputation"""
    cleaner = DataCleaner()
    cleaned_df, imputed_count = cleaner.impute_missing_values(
        sample_data_with_missing, strategy=ImputationStrategy.MEAN, columns=["numeric"]
    )

    assert cleaned_df["numeric"].isnull().sum() == 0
    assert imputed_count == 2  # 2 missing values in numeric column


# Test 7: Impute missing values with median
def test_impute_missing_median(sample_data_with_missing):
    """Test median imputation"""
    cleaner = DataCleaner()
    cleaned_df, imputed_count = cleaner.impute_missing_values(
        sample_data_with_missing, strategy=ImputationStrategy.MEDIAN, columns=["numeric"]
    )

    assert cleaned_df["numeric"].isnull().sum() == 0
    assert imputed_count == 2


# Test 8: Impute missing values with mode
def test_impute_missing_mode(sample_data_with_missing):
    """Test mode imputation"""
    cleaner = DataCleaner()
    cleaned_df, imputed_count = cleaner.impute_missing_values(
        sample_data_with_missing,
        strategy=ImputationStrategy.MODE,
        columns=["categorical"],
    )

    assert cleaned_df["categorical"].isnull().sum() == 0
    assert imputed_count == 2  # 2 missing values in categorical column


# Test 9: Impute missing values with forward fill
def test_impute_missing_forward_fill(sample_data_with_missing):
    """Test forward fill imputation"""
    cleaner = DataCleaner()
    cleaned_df, imputed_count = cleaner.impute_missing_values(
        sample_data_with_missing,
        strategy=ImputationStrategy.FORWARD_FILL,
        columns=["numeric"],
    )

    # Should reduce missing values (but maybe not all if first value is null)
    assert cleaned_df["numeric"].isnull().sum() <= sample_data_with_missing["numeric"].isnull().sum()


# Test 10: Remove duplicates
def test_remove_duplicates(sample_data_with_duplicates):
    """Test duplicate removal"""
    cleaner = DataCleaner()
    initial_rows = len(sample_data_with_duplicates)

    cleaned_df, duplicates_count = cleaner.remove_duplicates(
        sample_data_with_duplicates, keep="first"
    )

    assert len(cleaned_df) < initial_rows
    assert duplicates_count == 2  # 2 duplicate rows
    assert len(cleaned_df) == 5  # 7 - 2 = 5 unique rows


# Test 11: Remove duplicates with subset
def test_remove_duplicates_subset(sample_data_with_duplicates):
    """Test duplicate removal with subset"""
    cleaner = DataCleaner()

    cleaned_df, duplicates_count = cleaner.remove_duplicates(
        sample_data_with_duplicates, subset=["id"], keep="first"
    )

    # Should remove based on id column only
    assert len(cleaned_df) == 5  # ids: 1, 2, 3, 4, 5
    assert duplicates_count == 2


# Test 12: Scale features with MinMax
def test_scale_features_minmax(sample_numeric_data):
    """Test MinMax scaling"""
    cleaner = DataCleaner()
    scaled_df = cleaner.scale_features(
        sample_numeric_data, method=ScalingMethod.MINMAX, columns=["col1"]
    )

    # MinMax scaling should result in values between 0 and 1
    assert scaled_df["col1"].min() == 0.0
    assert scaled_df["col1"].max() == 1.0


# Test 13: Scale features with Standard scaling
def test_scale_features_standard(sample_numeric_data):
    """Test Standard scaling"""
    cleaner = DataCleaner()
    scaled_df = cleaner.scale_features(
        sample_numeric_data, method=ScalingMethod.STANDARD, columns=["col1"]
    )

    # Standard scaling should have mean ~0 and std ~1
    # Use ddof=0 for population std (same as sklearn)
    assert abs(scaled_df["col1"].mean()) < 1e-10
    assert abs(scaled_df["col1"].std(ddof=0) - 1.0) < 1e-10


# Test 14: Scale features with Robust scaling
def test_scale_features_robust(sample_numeric_data):
    """Test Robust scaling"""
    cleaner = DataCleaner()
    scaled_df = cleaner.scale_features(
        sample_numeric_data, method=ScalingMethod.ROBUST, columns=["col1"]
    )

    # Robust scaling uses median and IQR
    assert isinstance(scaled_df, pd.DataFrame)
    assert "col1" in scaled_df.columns


# Test 15: Convert types
def test_convert_types():
    """Test type conversion"""
    df = pd.DataFrame(
        {
            "int_col": ["1", "2", "3"],
            "float_col": ["1.5", "2.5", "3.5"],
            "date_col": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )

    cleaner = DataCleaner()
    converted_df, conversions = cleaner.convert_types(
        df,
        type_map={
            "int_col": "int",
            "float_col": "float",
            "date_col": "datetime",
        },
    )

    assert pd.api.types.is_integer_dtype(converted_df["int_col"])
    assert pd.api.types.is_float_dtype(converted_df["float_col"])
    assert pd.api.types.is_datetime64_any_dtype(converted_df["date_col"])
    assert conversions == 3


# Test 16: Comprehensive clean method
def test_clean_comprehensive():
    """Test comprehensive cleaning"""
    # Create messy data
    np.random.seed(42)
    data = {
        "value": list(np.random.normal(100, 15, 98)) + [200, 0],  # Add outliers
        "category": ["A", "B"] * 49 + [None, None],  # Add missing
    }
    df = pd.DataFrame(data)

    # Add duplicates
    df = pd.concat([df, df.iloc[:2]], ignore_index=True)

    cleaner = DataCleaner()
    cleaned_df, report = cleaner.clean(
        df,
        remove_outliers=True,
        outlier_method=OutlierMethod.IQR,
        impute_missing=True,
        imputation_strategy=ImputationStrategy.MODE,
        remove_dupes=True,
        scale_features=False,
    )

    # Check report
    assert isinstance(report, CleaningReport)
    assert report.rows_before == 102
    assert report.rows_after < report.rows_before
    assert report.duplicates_removed == 2
    assert len(report.operations) > 0


# Test 17: Clean with scaling
def test_clean_with_scaling(sample_numeric_data):
    """Test cleaning with feature scaling"""
    cleaner = DataCleaner()
    cleaned_df, report = cleaner.clean(
        sample_numeric_data,
        remove_outliers=False,
        impute_missing=False,
        remove_dupes=False,
        scale_features=True,
        scaling_method=ScalingMethod.STANDARD,
    )

    assert len(report.scaled_columns) == 3  # All 3 numeric columns
    assert "Scaled" in " ".join(report.operations)


# Test 18: Get statistics
def test_get_statistics():
    """Test cleaning statistics"""
    cleaner = DataCleaner()

    # Initially empty
    stats = cleaner.get_statistics()
    assert stats["total_cleanings"] == 0

    # After cleaning
    df = pd.DataFrame({"col1": [1, 2, 3, 1, 2]})
    cleaner.clean(df, remove_dupes=True, remove_outliers=False, impute_missing=False)

    stats = cleaner.get_statistics()
    assert stats["total_cleanings"] == 1
    assert stats["total_duplicates_removed"] == 2
