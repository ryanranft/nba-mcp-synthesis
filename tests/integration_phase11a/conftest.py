"""
Pytest Configuration for Phase 11A Integration Tests

Provides fixtures and utilities for cross-agent integration testing.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta


@pytest.fixture
def sample_player_data():
    """Generate sample NBA player data for testing"""
    np.random.seed(42)
    n_samples = 1000

    return pd.DataFrame({
        'player_id': np.random.randint(1, 100, n_samples),
        'game_id': np.random.randint(1, 500, n_samples),
        'team_id': np.random.randint(1, 30, n_samples),
        'points': np.random.normal(15, 5, n_samples).clip(0),
        'assists': np.random.normal(5, 2, n_samples).clip(0),
        'rebounds': np.random.normal(7, 3, n_samples).clip(0),
        'minutes': np.random.normal(25, 5, n_samples).clip(0),
        'field_goal_pct': np.random.uniform(0.3, 0.6, n_samples),
        'three_point_pct': np.random.uniform(0.2, 0.5, n_samples),
        'free_throw_pct': np.random.uniform(0.6, 0.9, n_samples),
        'turnovers': np.random.normal(2, 1, n_samples).clip(0),
        'steals': np.random.normal(1, 0.5, n_samples).clip(0),
        'blocks': np.random.normal(0.5, 0.5, n_samples).clip(0),
        'fouls': np.random.normal(2, 1, n_samples).clip(0),
        'plus_minus': np.random.normal(0, 10, n_samples),
        'home_game': np.random.choice([0, 1], n_samples),
        'opponent_strength': np.random.uniform(0, 1, n_samples),
        'season': np.random.choice([2020, 2021, 2022, 2023, 2024], n_samples),
        'game_date': pd.date_range(start='2020-01-01', periods=n_samples, freq='D')
    })


@pytest.fixture
def large_player_dataset():
    """Generate large dataset for performance testing"""
    np.random.seed(42)
    n_samples = 50000

    return pd.DataFrame({
        'player_id': np.random.randint(1, 500, n_samples),
        'game_id': np.random.randint(1, 5000, n_samples),
        'points': np.random.normal(15, 5, n_samples).clip(0),
        'assists': np.random.normal(5, 2, n_samples).clip(0),
        'rebounds': np.random.normal(7, 3, n_samples).clip(0),
        'minutes': np.random.normal(25, 5, n_samples).clip(0),
        'season': np.random.choice([2020, 2021, 2022, 2023, 2024], n_samples),
        'game_date': pd.date_range(start='2020-01-01', periods=n_samples, freq='H')
    })


@pytest.fixture
def time_series_data():
    """Generate time series data for testing"""
    np.random.seed(42)
    n_periods = 500
    dates = pd.date_range(start='2020-01-01', periods=n_periods, freq='D')

    # Create realistic patterns
    trend = np.linspace(10, 20, n_periods)
    seasonality = 5 * np.sin(np.linspace(0, 8*np.pi, n_periods))
    noise = np.random.normal(0, 2, n_periods)

    return pd.Series(
        trend + seasonality + noise,
        index=dates,
        name='points_per_game'
    )


@pytest.fixture
def panel_data():
    """Generate panel data for econometric testing"""
    np.random.seed(42)
    n_players = 50
    n_periods = 20

    data = []
    for player_id in range(1, n_players + 1):
        for period in range(1, n_periods + 1):
            data.append({
                'player_id': player_id,
                'period': period,
                'points': np.random.normal(15 + player_id * 0.1, 5),
                'minutes': np.random.normal(25, 5),
                'age': 20 + period // 4,
                'experience': period // 2,
                'team_quality': np.random.uniform(0, 1)
            })

    return pd.DataFrame(data)


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs"""
    temp_dir = tempfile.mkdtemp(prefix='phase11a_test_')
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing"""
    class MockConnection:
        def __init__(self):
            self.connected = True
            self.queries_executed = []

        def execute(self, query):
            self.queries_executed.append(query)
            return {'success': True, 'rows': 100}

        def close(self):
            self.connected = False

    return MockConnection()


@pytest.fixture
def integration_test_config():
    """Configuration for integration tests"""
    return {
        'slow_query_threshold_ms': 100.0,
        'cache_enabled': True,
        'profiling_enabled': True,
        'max_workers': 4,
        'timeout_seconds': 30,
        'retry_attempts': 3
    }


@pytest.fixture
def validation_rules():
    """Standard validation rules for testing"""
    return {
        'required_columns': ['player_id', 'points', 'minutes'],
        'ranges': {
            'points': {'min': 0, 'max': 100},
            'assists': {'min': 0, 'max': 50},
            'rebounds': {'min': 0, 'max': 50},
            'minutes': {'min': 0, 'max': 48}
        },
        'unique_columns': ['game_id'],
        'data_types': {
            'player_id': 'int',
            'points': 'float',
            'assists': 'float',
            'rebounds': 'float'
        }
    }


class IntegrationTestHelper:
    """Helper utilities for integration tests"""

    @staticmethod
    def assert_performance_acceptable(execution_time_ms: float, threshold_ms: float = 1000.0):
        """Assert that execution time is within acceptable range"""
        assert execution_time_ms < threshold_ms, \
            f"Performance test failed: {execution_time_ms:.2f}ms exceeds threshold of {threshold_ms}ms"

    @staticmethod
    def assert_data_quality(df: pd.DataFrame, min_rows: int = 1):
        """Assert basic data quality requirements"""
        assert len(df) >= min_rows, f"Dataset too small: {len(df)} rows (minimum: {min_rows})"
        assert not df.empty, "DataFrame is empty"
        assert df.shape[1] > 0, "DataFrame has no columns"

    @staticmethod
    def assert_no_nulls(df: pd.DataFrame, columns: list):
        """Assert no null values in specified columns"""
        for col in columns:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' has {null_count} null values"

    @staticmethod
    def assert_workflow_success(results: dict):
        """Assert that workflow completed successfully"""
        assert 'status' in results, "Results missing 'status' field"
        assert results['status'] == 'success', f"Workflow failed: {results.get('error', 'Unknown error')}"

    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Measure function execution time"""
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        execution_time_ms = (end - start) * 1000
        return result, execution_time_ms


@pytest.fixture
def test_helper():
    """Provide test helper utilities"""
    return IntegrationTestHelper()


# Mark categories for test organization
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "agents_1_3: Tests for Agents 1-3 (error handling, monitoring, security)")
    config.addinivalue_line("markers", "agents_4_7: Tests for Agents 4-7 (validation, training, deployment)")
    config.addinivalue_line("markers", "agent_8: Tests for Agent 8 (econometric methods)")
    config.addinivalue_line("markers", "agent_9: Tests for Agent 9 (performance optimization)")
    config.addinivalue_line("markers", "end_to_end: End-to-end workflow tests")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "security: Security integration tests")
    config.addinivalue_line("markers", "slow: Slow-running tests (>10 seconds)")
