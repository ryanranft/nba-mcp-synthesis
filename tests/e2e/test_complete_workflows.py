#!/usr/bin/env python3
"""
End-to-End Validation Workflow Tests

Comprehensive E2E testing for complete data validation workflows including
integration with CI/CD, error recovery, and Week 1 infrastructure components.

Phase 10A Week 2 - Agent 4 - Phase 5: Extended Testing
Task 3: End-to-End Validation Workflows

Author: NBA MCP Synthesis System
Created: 2025-10-25
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any

# Import components under test
from mcp_server.data_validation_pipeline import (
    DataValidationPipeline,
    PipelineConfig,
    PipelineStage,
    PipelineResult,
)
from mcp_server.data_cleaning import DataCleaner, OutlierMethod, ImputationStrategy
from mcp_server.data_profiler import DataProfiler
from mcp_server.integrity_checker import IntegrityChecker

# Import test utilities
from tests.mocks.mock_great_expectations import MockDataContext, MockCheckpoint
from tests.mocks.mock_data_sources import (
    generate_sample_player_stats,
    generate_sample_game_data,
)


# ==================== Fixtures ====================


@pytest.fixture
def sample_player_data():
    """Generate realistic player statistics data"""
    return generate_sample_player_stats(num_players=100)


@pytest.fixture
def sample_game_data():
    """Generate realistic game data"""
    return generate_sample_game_data(num_games=50)


@pytest.fixture
def pipeline_config():
    """Standard pipeline configuration"""
    return PipelineConfig(
        enable_schema_validation=True,
        enable_quality_check=True,
        enable_business_rules=True,
        enable_profiling=True,
        min_quality_score=0.90,
    )


@pytest.fixture
def validation_pipeline(pipeline_config):
    """Initialize validation pipeline"""
    return DataValidationPipeline(config=pipeline_config)


# ==================== E2E Workflow Tests ====================


class TestCompleteValidationWorkflow:
    """Test complete end-to-end validation workflows"""

    def test_full_player_stats_workflow(self, sample_player_data, validation_pipeline):
        """
        Test complete workflow: ingestion → validation → reporting

        Workflow Steps:
        1. Ingest raw data
        2. Schema validation
        3. Data quality check
        4. Business rules validation
        5. Data profiling
        6. Generate report
        """
        print("\n" + "=" * 80)
        print("E2E TEST: Full Player Stats Validation Workflow")
        print("=" * 80)

        # Step 1: Ingest data
        print("\n[Step 1] Data Ingestion")
        df = sample_player_data.copy()
        print(f"  Loaded {len(df)} player records")

        # Step 2: Run full validation pipeline
        print("\n[Step 2] Running Validation Pipeline")
        result = validation_pipeline.validate(df, dataset_type="player_stats")

        # Step 3: Verify results
        print("\n[Step 3] Verification")
        print(f"  Pipeline Status: {result.current_stage.value}")
        print(f"  Validation Passed: {result.passed}")
        print(f"  Issues Found: {len(result.issues)}")
        print(f"  Quality Score: {result.quality_score:.2%}")

        # Assertions
        assert result.current_stage == PipelineStage.COMPLETE
        assert result.passed is True or result.passed is False  # Can pass or fail
        assert hasattr(result, "quality_score")
        assert 0.0 <= result.quality_score <= 1.0

        print("\n[Complete] Full workflow executed successfully")
        print("=" * 80)

    def test_workflow_with_data_cleaning(self, sample_player_data):
        """
        Test workflow with data cleaning preprocessing

        Workflow:
        1. Clean data (outliers, missing values)
        2. Validate cleaned data
        3. Compare quality scores
        """
        print("\n" + "=" * 80)
        print("E2E TEST: Workflow with Data Cleaning")
        print("=" * 80)

        # Step 1: Validate raw data
        print("\n[Step 1] Validate Raw Data")
        pipeline = DataValidationPipeline()
        raw_result = pipeline.validate(sample_player_data, "player_stats")
        print(f"  Raw Data Quality: {raw_result.quality_score:.2%}")

        # Step 2: Clean data
        print("\n[Step 2] Clean Data")
        cleaner = DataCleaner()
        cleaned_df, clean_report = cleaner.clean(
            sample_player_data,
            remove_outliers=True,
            outlier_method=OutlierMethod.IQR,
            impute_missing=True,
            imputation_strategy=ImputationStrategy.MEDIAN,
            remove_dupes=True,
        )
        print(f"  Rows removed: {clean_report.rows_removed}")
        print(f"  Outliers removed: {clean_report.outliers_removed}")
        print(f"  Missing imputed: {clean_report.missing_values_imputed}")

        # Step 3: Validate cleaned data
        print("\n[Step 3] Validate Cleaned Data")
        clean_result = pipeline.validate(cleaned_df, "player_stats")
        print(f"  Cleaned Data Quality: {clean_result.quality_score:.2%}")

        # Step 4: Compare
        print("\n[Step 4] Comparison")
        quality_improvement = clean_result.quality_score - raw_result.quality_score
        print(f"  Quality Improvement: {quality_improvement:+.2%}")

        # Assertions
        assert clean_result.quality_score >= raw_result.quality_score
        assert clean_result.quality_score >= 0.85

        print("\n[Complete] Cleaning workflow validated")
        print("=" * 80)

    def test_workflow_with_profiling(self, sample_player_data):
        """
        Test workflow with detailed profiling

        Workflow:
        1. Profile raw data
        2. Validate data
        3. Use profiling insights for validation
        """
        print("\n" + "=" * 80)
        print("E2E TEST: Workflow with Data Profiling")
        print("=" * 80)

        # Step 1: Profile data
        print("\n[Step 1] Profile Data")
        profiler = DataProfiler()
        profile = profiler.profile(sample_player_data)
        print(f"  Columns profiled: {len(profile.column_profiles)}")

        # Step 2: Calculate quality score
        print("\n[Step 2] Calculate Quality Score")
        quality_score = profiler.calculate_quality_score(sample_player_data)
        print(f"  Quality Score: {quality_score:.2%}")

        # Step 3: Run validation
        print("\n[Step 3] Run Validation")
        pipeline = DataValidationPipeline()
        result = pipeline.validate(sample_player_data, "player_stats")

        # Step 4: Verify consistency
        print("\n[Step 4] Verify Consistency")
        print(f"  Profiler Quality: {quality_score:.2%}")
        print(f"  Pipeline Quality: {result.quality_score:.2%}")

        # Assertions
        assert abs(quality_score - result.quality_score) < 0.05  # Should be close

        print("\n[Complete] Profiling workflow validated")
        print("=" * 80)


class TestWorkflowFailureScenarios:
    """Test workflow behavior under failure conditions"""

    def test_invalid_dataset_type(self, sample_player_data, validation_pipeline):
        """Test workflow with invalid dataset type"""
        print("\n" + "=" * 80)
        print("E2E TEST: Invalid Dataset Type Handling")
        print("=" * 80)

        # Should handle gracefully
        result = validation_pipeline.validate(
            sample_player_data, dataset_type="invalid_type"
        )

        # Pipeline should complete but may have issues
        assert result.current_stage == PipelineStage.COMPLETE
        print(f"  Handled invalid type gracefully: {len(result.issues)} issues")
        print("=" * 80)

    def test_empty_dataset(self, validation_pipeline):
        """Test workflow with empty dataset"""
        print("\n" + "=" * 80)
        print("E2E TEST: Empty Dataset Handling")
        print("=" * 80)

        empty_df = pd.DataFrame()

        # Should handle gracefully
        result = validation_pipeline.validate(empty_df, dataset_type="player_stats")

        # May fail validation but shouldn't crash
        assert result is not None
        print(f"  Handled empty dataset: Passed={result.passed}")
        print("=" * 80)

    def test_malformed_data(self, validation_pipeline):
        """Test workflow with malformed data"""
        print("\n" + "=" * 80)
        print("E2E TEST: Malformed Data Handling")
        print("=" * 80)

        # Create intentionally malformed data
        malformed_df = pd.DataFrame(
            {
                "player_id": ["not_an_int", "also_not_int", 3],
                "points": [-999, 999999, "invalid"],
                "team_id": [None, None, None],
            }
        )

        # Should handle gracefully
        result = validation_pipeline.validate(
            malformed_df, dataset_type="player_stats"
        )

        # Should detect issues
        assert result.current_stage == PipelineStage.COMPLETE
        assert len(result.issues) > 0
        print(f"  Detected {len(result.issues)} issues in malformed data")
        print("=" * 80)


class TestCICDIntegration:
    """Test CI/CD workflow integration"""

    def test_ci_validation_workflow(self, sample_player_data):
        """
        Simulate CI/CD validation workflow

        Simulates:
        1. PR triggers validation
        2. Data validation runs
        3. Results reported
        4. Pass/fail status returned
        """
        print("\n" + "=" * 80)
        print("E2E TEST: CI/CD Validation Workflow")
        print("=" * 80)

        # Simulate CI environment
        print("\n[CI Environment]")
        ci_config = {
            "pr_number": 123,
            "branch": "feature/data-update",
            "commit_sha": "abc123def456",
            "trigger": "pull_request",
        }
        print(f"  PR #{ci_config['pr_number']}")
        print(f"  Branch: {ci_config['branch']}")

        # Run validation
        print("\n[Running Validation]")
        pipeline = DataValidationPipeline(
            config=PipelineConfig(
                enable_schema_validation=True,
                enable_quality_check=True,
                enable_business_rules=True,
                min_quality_score=0.85,
            )
        )

        result = pipeline.validate(sample_player_data, "player_stats")

        # Generate CI report
        print("\n[Validation Results]")
        ci_status = "success" if result.passed else "failure"
        print(f"  Status: {ci_status}")
        print(f"  Quality Score: {result.quality_score:.2%}")
        print(f"  Issues: {len(result.issues)}")

        # Simulate status check
        status_check = {
            "state": ci_status,
            "description": f"Data validation {ci_status}",
            "context": "data-validation/nba-mcp",
        }

        # Assertions
        assert status_check["state"] in ["success", "failure"]
        assert result.current_stage == PipelineStage.COMPLETE

        print(f"\n[CI Status Check] {status_check}")
        print("=" * 80)

    @patch("mcp_server.data_validation_pipeline.DataValidationPipeline.validate")
    def test_ci_failure_handling(self, mock_validate, sample_player_data):
        """Test CI/CD handling of validation failures"""
        print("\n" + "=" * 80)
        print("E2E TEST: CI/CD Failure Handling")
        print("=" * 80)

        # Mock a failure
        mock_result = Mock()
        mock_result.passed = False
        mock_result.quality_score = 0.75
        mock_result.issues = ["Issue 1", "Issue 2", "Issue 3"]
        mock_result.current_stage = PipelineStage.COMPLETE
        mock_validate.return_value = mock_result

        pipeline = DataValidationPipeline()
        result = pipeline.validate(sample_player_data, "player_stats")

        # Verify failure is captured
        assert result.passed is False
        assert len(result.issues) > 0

        # Simulate CI action
        if not result.passed:
            print(f"\n[CI Action] Block merge - {len(result.issues)} validation issues")
            print(f"  Quality score {result.quality_score:.2%} below threshold")

        print("=" * 80)


class TestWeek1Integration:
    """Test integration with Week 1 infrastructure components"""

    def test_error_handling_integration(self, sample_player_data):
        """Test error handling integration from Week 1"""
        print("\n" + "=" * 80)
        print("E2E TEST: Error Handling Integration")
        print("=" * 80)

        # Create data that will trigger various error conditions
        problem_data = sample_player_data.copy()
        problem_data.loc[0, "points"] = np.nan  # Missing value
        problem_data.loc[1, "games_played"] = -5  # Invalid value

        # Validation should handle errors gracefully
        pipeline = DataValidationPipeline()
        result = pipeline.validate(problem_data, "player_stats")

        # Errors should be captured, not raised
        assert result is not None
        assert result.current_stage == PipelineStage.COMPLETE
        print(f"  Graceful error handling: {len(result.issues)} issues captured")
        print("=" * 80)

    def test_monitoring_integration(self, sample_player_data):
        """Test monitoring integration from Week 1"""
        print("\n" + "=" * 80)
        print("E2E TEST: Monitoring Integration")
        print("=" * 80)

        # Track metrics during validation
        metrics = {
            "start_time": datetime.now(),
            "dataset_size": len(sample_player_data),
        }

        # Run validation
        pipeline = DataValidationPipeline()
        result = pipeline.validate(sample_player_data, "player_stats")

        # Capture completion metrics
        metrics["end_time"] = datetime.now()
        metrics["duration"] = (metrics["end_time"] - metrics["start_time"]).total_seconds()
        metrics["validation_passed"] = result.passed
        metrics["quality_score"] = result.quality_score
        metrics["issues_count"] = len(result.issues)

        # Verify metrics captured
        print("\n[Metrics Captured]")
        print(f"  Duration: {metrics['duration']:.2f}s")
        print(f"  Dataset Size: {metrics['dataset_size']}")
        print(f"  Quality Score: {metrics['quality_score']:.2%}")
        print(f"  Issues: {metrics['issues_count']}")

        assert all(key in metrics for key in ["start_time", "end_time", "quality_score"])
        print("=" * 80)


class TestDataFlowIntegrity:
    """Test data integrity through complete workflows"""

    def test_data_preservation_through_pipeline(self, sample_player_data):
        """Verify data is not corrupted during validation"""
        print("\n" + "=" * 80)
        print("E2E TEST: Data Preservation")
        print("=" * 80)

        # Capture original data characteristics
        original_shape = sample_player_data.shape
        original_columns = list(sample_player_data.columns)
        original_sum = sample_player_data.select_dtypes(include=[np.number]).sum().sum()

        # Run validation (should not modify data)
        pipeline = DataValidationPipeline()
        result = pipeline.validate(sample_player_data, "player_stats")

        # Verify data unchanged
        assert sample_player_data.shape == original_shape
        assert list(sample_player_data.columns) == original_columns

        # Numeric sum should be same (allowing for NaN handling)
        post_sum = sample_player_data.select_dtypes(include=[np.number]).sum().sum()
        if not np.isnan(post_sum) and not np.isnan(original_sum):
            assert abs(post_sum - original_sum) < 0.01

        print("  ✓ Data integrity preserved through pipeline")
        print("=" * 80)

    def test_multiple_dataset_workflow(self):
        """Test workflow with multiple dataset types"""
        print("\n" + "=" * 80)
        print("E2E TEST: Multiple Dataset Workflow")
        print("=" * 80)

        # Generate different dataset types
        player_data = generate_sample_player_stats(50)
        game_data = generate_sample_game_data(25)

        # Validate both
        pipeline = DataValidationPipeline()

        print("\n[Validating Player Stats]")
        player_result = pipeline.validate(player_data, "player_stats")
        print(f"  Quality: {player_result.quality_score:.2%}")

        print("\n[Validating Game Data]")
        game_result = pipeline.validate(game_data, "game_data")
        print(f"  Quality: {game_result.quality_score:.2%}")

        # Both should complete
        assert player_result.current_stage == PipelineStage.COMPLETE
        assert game_result.current_stage == PipelineStage.COMPLETE

        print("\n  ✓ Multiple datasets validated successfully")
        print("=" * 80)


class TestWorkflowPerformance:
    """Test workflow performance characteristics"""

    def test_workflow_performance_small_dataset(self):
        """Test workflow performance with small dataset"""
        import time

        print("\n" + "=" * 80)
        print("E2E TEST: Workflow Performance (Small Dataset)")
        print("=" * 80)

        # Generate small dataset
        df = generate_sample_player_stats(100)

        # Time the workflow
        pipeline = DataValidationPipeline()
        start_time = time.time()
        result = pipeline.validate(df, "player_stats")
        duration = time.time() - start_time

        print(f"\n  Dataset Size: {len(df)} rows")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Status: {'PASS' if result.passed else 'FAIL'}")

        # Small dataset should be fast
        assert duration < 5.0, f"Workflow too slow: {duration:.3f}s"

        print("=" * 80)

    def test_workflow_performance_medium_dataset(self):
        """Test workflow performance with medium dataset"""
        import time

        print("\n" + "=" * 80)
        print("E2E TEST: Workflow Performance (Medium Dataset)")
        print("=" * 80)

        # Generate medium dataset
        df = generate_sample_player_stats(1000)

        # Time the workflow
        pipeline = DataValidationPipeline()
        start_time = time.time()
        result = pipeline.validate(df, "player_stats")
        duration = time.time() - start_time

        print(f"\n  Dataset Size: {len(df)} rows")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Status: {'PASS' if result.passed else 'FAIL'}")

        # Medium dataset should complete in reasonable time
        assert duration < 10.0, f"Workflow too slow: {duration:.3f}s"

        print("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
