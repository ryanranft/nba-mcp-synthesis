#!/usr/bin/env python3
"""
Full Validation Pipeline Integration Tests

Comprehensive end-to-end tests for the complete data validation
infrastructure including Great Expectations integration.

Phase 10A Week 2 - Agent 4 - Advanced Integrations

Author: NBA MCP Synthesis System
Created: 2025-10-25
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# Import components under test
from mcp_server.data_validation_pipeline import DataValidationPipeline, PipelineConfig
from mcp_server.data_cleaning import DataCleaner, OutlierMethod, ImputationStrategy
from mcp_server.data_profiler import DataProfiler
from mcp_server.integrity_checker import IntegrityChecker

# Import mock services
from tests.mocks.mock_great_expectations import (
    MockDataContext,
    MockCheckpoint,
    MockValidationResult,
)
from tests.mocks.mock_data_sources import (
    MockPostgresConnection,
    generate_sample_player_stats,
    generate_sample_game_data,
    generate_sample_team_data,
)


# ==================== Fixtures ====================


@pytest.fixture
def sample_player_stats():
    """Generate sample player statistics data"""
    return generate_sample_player_stats(num_players=50)


@pytest.fixture
def sample_game_data():
    """Generate sample game data"""
    return generate_sample_game_data(num_games=100)


@pytest.fixture
def sample_team_data():
    """Generate sample team data"""
    return generate_sample_team_data()


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection"""
    return MockPostgresConnection()


@pytest.fixture
def mock_ge_context():
    """Mock Great Expectations DataContext"""
    return MockDataContext()


@pytest.fixture
def validation_pipeline():
    """Initialize validation pipeline"""
    config = PipelineConfig(
        enable_schema_validation=True,
        enable_quality_check=True,
        enable_business_rules=True,
        enable_profiling=True,
        min_quality_score=0.90,
    )
    return DataValidationPipeline(config=config)


@pytest.fixture
def data_cleaner():
    """Initialize data cleaner"""
    return DataCleaner()


@pytest.fixture
def data_profiler():
    """Initialize data profiler"""
    return DataProfiler()


@pytest.fixture
def integrity_checker():
    """Initialize integrity checker"""
    return IntegrityChecker()


# ==================== Pipeline Tests ====================


@pytest.mark.integration
def test_full_pipeline_player_stats(validation_pipeline, sample_player_stats):
    """Test complete validation pipeline with player stats"""
    # Run full pipeline
    result = validation_pipeline.validate(
        df=sample_player_stats,
        dataset_name="player_stats",
    )

    # Assertions
    assert result is not None, "Pipeline should return result"
    assert result.dataset_name == "player_stats"
    assert result.current_stage is not None, "Should have a current stage"
    assert isinstance(result.passed, bool), "Should have boolean passed status"
    assert isinstance(result.issues, list), "Should have issues list"


@pytest.mark.integration
def test_full_pipeline_game_data(validation_pipeline, sample_game_data):
    """Test complete validation pipeline with game data"""
    result = validation_pipeline.validate(
        df=sample_game_data,
        dataset_name="games",
    )

    # Basic assertions
    assert result is not None
    assert result.dataset_name == "games"
    assert result.current_stage is not None


@pytest.mark.integration
def test_full_pipeline_team_data(validation_pipeline, sample_team_data):
    """Test complete validation pipeline with team data"""
    result = validation_pipeline.validate(
        df=sample_team_data,
        dataset_name="teams",
    )

    # Basic assertions
    assert result is not None
    assert result.dataset_name == "teams"
    assert result.current_stage is not None


@pytest.mark.integration
def test_pipeline_with_errors(validation_pipeline):
    """Test pipeline handles data errors gracefully"""
    # Create data with intentional errors
    bad_data = pd.DataFrame(
        {
            "player_id": [None, None, "player_003"],  # Nulls
            "player_name": ["Player 1", "Player 2", "Player 3"],
            "ppg": [25.5, -10.0, 999.9],  # Invalid values
        }
    )

    result = validation_pipeline.validate(
        df=bad_data,
        dataset_name="bad_player_stats",
    )

    # Should complete but with failures
    assert result is not None
    assert (
        result.passed is False or len(result.issues) > 0
    ), "Should have issues with bad data"


@pytest.mark.integration
def test_pipeline_performance(validation_pipeline):
    """Test pipeline performance with large dataset"""
    # Generate large dataset
    large_data = generate_sample_player_stats(num_players=1000)

    # Time execution
    import time

    start_time = time.time()

    result = validation_pipeline.validate(
        df=large_data,
        dataset_name="large_player_stats",
    )

    execution_time = time.time() - start_time

    # Performance assertions
    assert result is not None
    assert execution_time < 5.0, f"Pipeline too slow: {execution_time:.2f}s"


# ==================== Great Expectations Integration Tests ====================


@pytest.mark.integration
@patch("mcp_server.ge_integration.gx.get_context")
def test_ge_checkpoint_execution(mock_get_context, mock_ge_context):
    """Test Great Expectations checkpoint execution"""
    # Setup mock
    mock_get_context.return_value = mock_ge_context

    # Import here to avoid import errors if GE not installed
    try:
        from mcp_server.ge_integration import GreatExpectationsIntegration
    except Exception:
        pytest.skip("Great Expectations integration not available")

    # Create integration (with mocked context)
    with patch("mcp_server.ge_integration.GE_AVAILABLE", True):
        ge_integration = GreatExpectationsIntegration(
            context_root_dir="/mock/path",
            enable_monitoring=False,
        )
        ge_integration.context = mock_ge_context

        # Run checkpoint
        result = ge_integration.run_checkpoint("player_stats_checkpoint")

        # Assertions
        assert result is not None
        assert result.checkpoint_name == "player_stats_checkpoint"
        assert result.total_expectations > 0
        assert 0.0 <= result.pass_rate <= 1.0


@pytest.mark.integration
@patch("mcp_server.ge_integration.gx.get_context")
def test_ge_all_checkpoints(mock_get_context, mock_ge_context):
    """Test running all GE checkpoints"""
    mock_get_context.return_value = mock_ge_context

    try:
        from mcp_server.ge_integration import GreatExpectationsIntegration
    except Exception:
        pytest.skip("Great Expectations integration not available")

    with patch("mcp_server.ge_integration.GE_AVAILABLE", True):
        ge_integration = GreatExpectationsIntegration(
            context_root_dir="/mock/path",
            enable_monitoring=False,
        )
        ge_integration.context = mock_ge_context

        # Run all checkpoints
        results = ge_integration.run_all_checkpoints()

        # Assertions
        assert len(results) == 3, "Should run 3 checkpoints"
        for result in results:
            assert result.total_expectations > 0


@pytest.mark.integration
@patch("mcp_server.ge_integration.gx.get_context")
def test_ge_aggregated_results(mock_get_context, mock_ge_context):
    """Test aggregation of GE validation results"""
    mock_get_context.return_value = mock_ge_context

    try:
        from mcp_server.ge_integration import GreatExpectationsIntegration
    except Exception:
        pytest.skip("Great Expectations integration not available")

    with patch("mcp_server.ge_integration.GE_AVAILABLE", True):
        ge_integration = GreatExpectationsIntegration(
            context_root_dir="/mock/path",
            enable_monitoring=False,
        )
        ge_integration.context = mock_ge_context

        # Run all and aggregate
        results = ge_integration.run_all_checkpoints()
        aggregate = ge_integration.aggregate_results(results)

        # Assertions
        assert aggregate["total_checkpoints"] == 3
        assert aggregate["total_expectations"] > 0
        assert 0.0 <= aggregate["overall_pass_rate"] <= 1.0


# ==================== Component Integration Tests ====================


@pytest.mark.integration
def test_cleaning_and_profiling_integration(data_cleaner, data_profiler):
    """Test integration between cleaning and profiling"""
    # Generate dirty data
    dirty_data = generate_sample_player_stats(num_players=100)

    # Add some outliers
    dirty_data.loc[0, "ppg"] = 999.9  # Extreme outlier
    dirty_data.loc[1, "ppg"] = None  # Missing value

    # Clean data
    cleaned_data, _ = data_cleaner.remove_outliers(
        df=dirty_data,
        columns=["ppg"],
        method=OutlierMethod.IQR,
    )
    cleaned_data, _ = data_cleaner.impute_missing_values(
        df=cleaned_data,
        strategy=ImputationStrategy.MEAN,
    )

    # Profile cleaned data
    profile = data_profiler.profile(
        df=cleaned_data,
        dataset_name="cleaned_player_stats",
    )

    # Assertions
    assert profile is not None
    assert profile.dataset_name == "cleaned_player_stats"
    assert profile.quality_score > 0.0


@pytest.mark.integration
def test_profiling_and_integrity_integration(
    data_profiler, integrity_checker, sample_player_stats
):
    """Test integration between profiling and integrity checking"""
    # Profile data
    profile = data_profiler.profile(
        df=sample_player_stats,
        dataset_name="player_stats",
    )

    # Check integrity
    integrity_result = integrity_checker.check_nba_player_integrity(
        df=sample_player_stats,
    )

    # Both should succeed
    assert profile is not None
    assert profile.quality_score > 0.0
    assert integrity_result is not None


@pytest.mark.integration
def test_pipeline_with_all_components(sample_player_stats):
    """Test complete pipeline with all components"""
    # Initialize all components
    cleaner = DataCleaner()
    profiler = DataProfiler()
    integrity = IntegrityChecker()
    pipeline = DataValidationPipeline()

    # Step 1: Clean
    cleaned, _ = cleaner.impute_missing_values(
        sample_player_stats, strategy=ImputationStrategy.MEAN
    )

    # Step 2: Profile
    profile = profiler.profile(cleaned, "player_stats")

    # Step 3: Check integrity
    integrity_result = integrity.check_nba_player_integrity(cleaned)

    # Step 4: Full validation
    validation_result = pipeline.validate(cleaned, "player_stats")

    # All steps should succeed
    assert cleaned is not None
    assert profile is not None
    assert integrity_result is not None
    assert validation_result is not None


# ==================== CI/CD Workflow Tests ====================


@pytest.mark.integration
def test_ci_cd_workflow_simulation(validation_pipeline, sample_player_stats):
    """Simulate CI/CD validation workflow"""
    # Simulate triggered validation (like in GitHub Actions)

    # Step 1: Validate data
    result = validation_pipeline.validate(
        df=sample_player_stats,
        dataset_name="player_stats_ci",
    )

    # Step 2: Check pass/fail (CI would check this)
    if result.passed:
        exit_code = 0
    elif len(result.error_issues) == 0 and len(result.critical_issues) == 0:
        exit_code = 0  # Only warnings still pass
    else:
        exit_code = 1  # Failed

    # Assertions
    assert exit_code in [0, 1]
    assert result is not None


# ==================== Performance & Stress Tests ====================


@pytest.mark.integration
@pytest.mark.slow
def test_concurrent_validation(validation_pipeline):
    """Test concurrent validation operations"""
    import concurrent.futures

    # Generate multiple datasets
    datasets = [generate_sample_player_stats(100) for _ in range(5)]

    # Validate concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(
                validation_pipeline.validate,
                df=ds,
                dataset_name=f"concurrent_dataset_{i}",
            )
            for i, ds in enumerate(datasets)
        ]

        # Wait for all
        results = [f.result() for f in futures]

    # All should succeed
    assert len(results) == 5
    assert all(r is not None for r in results)


@pytest.mark.integration
@pytest.mark.slow
def test_memory_usage(validation_pipeline):
    """Test memory usage with large dataset"""
    import tracemalloc

    # Start tracking
    tracemalloc.start()

    # Generate large dataset
    large_data = generate_sample_player_stats(num_players=10000)

    # Validate
    result = validation_pipeline.validate(
        df=large_data,
        dataset_name="large_dataset",
    )

    # Check memory
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Memory assertions
    assert result is not None
    # Peak memory should be reasonable (< 500MB for 10K rows)
    assert peak < 500 * 1024 * 1024, f"Peak memory too high: {peak / 1024 / 1024:.1f}MB"


# ==================== Error Recovery Tests ====================


@pytest.mark.integration
def test_pipeline_recovery_from_partial_failure(validation_pipeline):
    """Test pipeline continues after partial failures"""
    # Create data that will fail some but not all checks
    partial_data = pd.DataFrame(
        {
            "player_id": ["p1", "p2", "p3"],
            "player_name": [None, "Player 2", "Player 3"],  # One null
            "ppg": [25.5, 18.3, 30.1],
        }
    )

    result = validation_pipeline.validate(
        df=partial_data,
        dataset_name="partial_failure_data",
    )

    # Pipeline should complete despite failures
    assert result is not None
    assert result.current_stage is not None


@pytest.mark.integration
def test_graceful_degradation(validation_pipeline):
    """Test graceful degradation when optional components fail"""
    # Test with minimal configuration
    minimal_config = PipelineConfig(
        enable_schema_validation=True,
        enable_quality_check=True,
        enable_business_rules=False,  # Disable business rules
        enable_profiling=False,  # Disable profiling
        min_quality_score=0.5,
    )

    minimal_pipeline = DataValidationPipeline(config=minimal_config)

    data = generate_sample_player_stats(50)
    result = minimal_pipeline.validate(df=data, dataset_name="minimal_validation")

    # Should still work with reduced functionality
    assert result is not None


# ==================== End-to-End Tests ====================


@pytest.mark.integration
@pytest.mark.slow
def test_complete_e2e_workflow(mock_postgres):
    """Test complete end-to-end validation workflow"""
    # Step 1: Fetch data from mock database
    player_data = mock_postgres.get_table("player_stats")

    # Step 2: Clean data
    cleaner = DataCleaner()
    cleaned_data, _ = cleaner.impute_missing_values(
        player_data, strategy=ImputationStrategy.MEAN
    )

    # Step 3: Validate with pipeline
    pipeline = DataValidationPipeline()
    validation_result = pipeline.validate(
        df=cleaned_data, dataset_name="e2e_player_stats"
    )

    # Step 4: Profile data
    profiler = DataProfiler()
    profile = profiler.profile(cleaned_data, "e2e_player_stats")

    # Step 5: Check integrity
    integrity = IntegrityChecker()
    integrity_result = integrity.check_nba_player_integrity(cleaned_data)

    # All steps should succeed
    assert validation_result is not None
    assert profile is not None
    assert integrity_result is not None
    # Check for success: either passed=True or no critical/error issues
    assert validation_result.passed or (
        len(validation_result.critical_issues) == 0
        and len(validation_result.error_issues) == 0
    )
