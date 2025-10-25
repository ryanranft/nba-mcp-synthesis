"""
Tests for Data Profiler Module

**Phase 10A Week 2 - Agent 4: Data Validation & Quality - Phase 2**
Comprehensive tests for data_profiler.py module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from mcp_server.data_profiler import (
    DataProfiler,
    DataProfile,
    ColumnProfile,
    DriftResult,
    DriftMethod,
)


@pytest.fixture
def sample_numeric_data():
    """Sample numeric data"""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "col1": np.random.normal(100, 15, 100),
            "col2": np.random.uniform(0, 1, 100),
            "col3": np.random.poisson(5, 100),
        }
    )


@pytest.fixture
def sample_mixed_data():
    """Sample mixed data types"""
    return pd.DataFrame(
        {
            "numeric": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "categorical": ["A", "B", "A", "C", "B", "A", "D", "B", "C", "A"],
            "missing": [1, None, 3, None, 5, None, 7, None, 9, None],
        }
    )


@pytest.fixture
def sample_player_data():
    """Sample NBA player data"""
    return pd.DataFrame(
        {
            "player_id": [1, 2, 3, 4, 5],
            "player_name": ["Player1", "Player2", "Player3", "Player4", "Player5"],
            "ppg": [25.5, 28.3, 22.1, 30.2, 24.8],
            "rpg": [7.2, 8.1, 5.5, 11.3, 6.9],
            "apg": [6.5, 5.2, 8.8, 4.1, 7.3],
            "fg_pct": [0.485, 0.512, 0.461, 0.545, 0.478],
            "games_played": [75, 68, 80, 72, 77],
        }
    )


@pytest.fixture
def sample_game_data():
    """Sample NBA game data"""
    return pd.DataFrame(
        {
            "game_id": [1, 2, 3, 4, 5],
            "date": pd.date_range("2024-01-01", periods=5),
            "home_team": ["Lakers", "Warriors", "Celtics", "Bucks", "Mavericks"],
            "away_team": ["Nets", "Suns", "Heat", "76ers", "Clippers"],
            "home_score": [110, 115, 108, 120, 105],
            "away_score": [105, 112, 106, 118, 102],
        }
    )


@pytest.fixture
def sample_team_data():
    """Sample NBA team data"""
    return pd.DataFrame(
        {
            "team_id": [1, 2, 3, 4, 5],
            "team_name": ["Lakers", "Warriors", "Celtics", "Bucks", "Mavericks"],
            "conference": ["West", "West", "East", "East", "West"],
            "wins": [45, 42, 50, 48, 40],
            "losses": [37, 40, 32, 34, 42],
            "win_pct": [0.549, 0.512, 0.610, 0.585, 0.488],
        }
    )


# Test 1: DataProfiler initialization
def test_data_profiler_initialization():
    """Test DataProfiler initialization"""
    profiler = DataProfiler()
    assert profiler.profile_history == []


# Test 2: Profile single numeric column
def test_profile_column_numeric(sample_numeric_data):
    """Test profiling a numeric column"""
    profiler = DataProfiler()
    profile = profiler.profile_column(sample_numeric_data, "col1")

    assert isinstance(profile, ColumnProfile)
    assert profile.name == "col1"
    assert profile.count == 100
    assert profile.mean is not None
    assert profile.median is not None
    assert profile.std is not None
    assert profile.min_value is not None
    assert profile.max_value is not None


# Test 3: Profile single categorical column
def test_profile_column_categorical(sample_mixed_data):
    """Test profiling a categorical column"""
    profiler = DataProfiler()
    profile = profiler.profile_column(sample_mixed_data, "categorical")

    assert isinstance(profile, ColumnProfile)
    assert profile.name == "categorical"
    assert profile.unique_count == 4  # A, B, C, D
    assert profile.mode is not None
    assert profile.cardinality == 4


# Test 4: Profile column with missing values
def test_profile_column_with_missing(sample_mixed_data):
    """Test profiling a column with missing values"""
    profiler = DataProfiler()
    profile = profiler.profile_column(sample_mixed_data, "missing")

    assert profile.null_count == 5
    assert profile.null_percentage == 0.5


# Test 5: Profile entire DataFrame
def test_profile_dataframe(sample_numeric_data):
    """Test profiling entire DataFrame"""
    profiler = DataProfiler()
    profile = profiler.profile(sample_numeric_data, "test_data")

    assert isinstance(profile, DataProfile)
    assert profile.dataset_name == "test_data"
    assert profile.row_count == 100
    assert profile.column_count == 3
    assert len(profile.columns) == 3
    assert profile.correlations is not None  # Should have correlations for numeric data


# Test 6: Profile mixed data types
def test_profile_mixed_data(sample_mixed_data):
    """Test profiling mixed data types"""
    profiler = DataProfiler()
    profile = profiler.profile(sample_mixed_data, "mixed_data")

    assert profile.column_count == 3
    assert len(profile.columns) == 3

    # Check that numeric and categorical columns are profiled differently
    numeric_profile = next(c for c in profile.columns if c.name == "numeric")
    categorical_profile = next(c for c in profile.columns if c.name == "categorical")

    assert numeric_profile.mean is not None
    assert categorical_profile.mode is not None


# Test 7: Quality score calculation
def test_quality_score(sample_mixed_data):
    """Test quality score calculation"""
    profiler = DataProfiler()
    profile = profiler.profile(sample_mixed_data, "test_data")

    assert 0 <= profile.quality_score <= 1
    # Should be less than 1 due to missing values
    assert profile.quality_score < 1.0


# Test 8: Detect drift with KL divergence
def test_detect_drift_kl_divergence():
    """Test KL divergence drift detection"""
    np.random.seed(42)
    # Use identical data to ensure no drift
    values = np.random.normal(100, 15, 1000)
    reference_data = pd.DataFrame({"value": values})
    current_data = pd.DataFrame({"value": values})  # Exactly same data

    profiler = DataProfiler()
    result = profiler.detect_drift_kl_divergence(
        reference_data, current_data, "value", threshold=0.1
    )

    assert isinstance(result, DriftResult)
    assert result.column == "value"
    assert result.method == DriftMethod.KL_DIVERGENCE
    assert isinstance(result.drift_detected, bool)
    assert result.drift_score >= 0
    # Should not detect drift with identical data
    assert result.drift_score < 0.01


# Test 9: Detect drift with KS test
def test_detect_drift_ks_test():
    """Test KS test drift detection"""
    np.random.seed(42)
    reference_data = pd.DataFrame({"value": np.random.normal(100, 15, 100)})
    current_data = pd.DataFrame({"value": np.random.normal(110, 15, 100)})  # Shifted mean

    profiler = DataProfiler()
    result = profiler.detect_drift_ks_test(
        reference_data, current_data, "value", threshold=0.05
    )

    assert isinstance(result, DriftResult)
    assert result.method == DriftMethod.KS_TEST
    assert "p_value" in result.details
    # Should detect drift due to shifted mean
    assert result.drift_detected


# Test 10: Detect drift with PSI
def test_detect_drift_psi():
    """Test PSI drift detection"""
    np.random.seed(42)
    reference_data = pd.DataFrame({"value": np.random.normal(100, 15, 1000)})
    # Use same seed for reproducibility
    np.random.seed(42)
    current_data = pd.DataFrame({"value": np.random.normal(100, 15, 1000)})  # Same distribution

    profiler = DataProfiler()
    result = profiler.detect_drift_psi(
        reference_data, current_data, "value", threshold=0.5  # Higher threshold for test
    )

    assert isinstance(result, DriftResult)
    assert result.method == DriftMethod.PSI
    assert "interpretation" in result.details
    # With same seed, PSI should be very low
    assert result.drift_score < 0.5


# Test 11: Detect drift across multiple columns
def test_detect_drift_multiple_columns(sample_numeric_data):
    """Test drift detection across multiple columns"""
    np.random.seed(42)
    reference_data = sample_numeric_data.copy()
    current_data = sample_numeric_data.copy()

    profiler = DataProfiler()
    results = profiler.detect_drift(
        reference_data,
        current_data,
        columns=["col1", "col2"],
        method=DriftMethod.KL_DIVERGENCE,
    )

    assert len(results) == 2
    assert all(isinstance(r, DriftResult) for r in results)
    assert [r.column for r in results] == ["col1", "col2"]


# Test 12: NBA player stats profiling
def test_profile_nba_player_stats(sample_player_data):
    """Test NBA player stats profiling"""
    profiler = DataProfiler()
    profile = profiler.profile_nba_player_stats(sample_player_data)

    assert profile.dataset_name == "nba_player_stats"
    assert profile.column_count == 7
    # Check that expected columns are present
    column_names = [c.name for c in profile.columns]
    assert "ppg" in column_names
    assert "rpg" in column_names
    assert "apg" in column_names


# Test 13: NBA game data profiling
def test_profile_nba_game_data(sample_game_data):
    """Test NBA game data profiling"""
    profiler = DataProfiler()
    profile = profiler.profile_nba_game_data(sample_game_data)

    assert profile.dataset_name == "nba_game_data"
    column_names = [c.name for c in profile.columns]
    assert "home_score" in column_names
    assert "away_score" in column_names


# Test 14: NBA team data profiling
def test_profile_nba_team_data(sample_team_data):
    """Test NBA team data profiling"""
    profiler = DataProfiler()
    profile = profiler.profile_nba_team_data(sample_team_data)

    assert profile.dataset_name == "nba_team_data"
    column_names = [c.name for c in profile.columns]
    assert "team_name" in column_names
    assert "wins" in column_names
    assert "losses" in column_names
    assert "win_pct" in column_names


# Test 15: Profile to dict conversion
def test_profile_to_dict(sample_numeric_data):
    """Test DataProfile to_dict conversion"""
    profiler = DataProfiler()
    profile = profiler.profile(sample_numeric_data, "test_data")

    profile_dict = profile.to_dict()

    assert isinstance(profile_dict, dict)
    assert "dataset_name" in profile_dict
    assert "row_count" in profile_dict
    assert "columns" in profile_dict
    assert len(profile_dict["columns"]) == 3


# Test 16: Column profile to dict conversion
def test_column_profile_to_dict(sample_numeric_data):
    """Test ColumnProfile to_dict conversion"""
    profiler = DataProfiler()
    profile = profiler.profile_column(sample_numeric_data, "col1")

    profile_dict = profile.to_dict()

    assert isinstance(profile_dict, dict)
    assert "name" in profile_dict
    assert "dtype" in profile_dict
    assert "mean" in profile_dict


# Test 17: Drift result to dict conversion
def test_drift_result_to_dict():
    """Test DriftResult to_dict conversion"""
    np.random.seed(42)
    reference_data = pd.DataFrame({"value": np.random.normal(100, 15, 100)})
    current_data = pd.DataFrame({"value": np.random.normal(100, 15, 100)})

    profiler = DataProfiler()
    result = profiler.detect_drift_kl_divergence(
        reference_data, current_data, "value"
    )

    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert "column" in result_dict
    assert "method" in result_dict
    assert "drift_detected" in result_dict


# Test 18: Get statistics
def test_get_statistics(sample_numeric_data):
    """Test profiling statistics"""
    profiler = DataProfiler()

    # Initially empty
    stats = profiler.get_statistics()
    assert stats["total_profiles"] == 0

    # After profiling
    profiler.profile(sample_numeric_data, "test_data")
    stats = profiler.get_statistics()

    assert stats["total_profiles"] == 1
    assert "avg_quality_score" in stats
    assert "datasets_profiled" in stats
