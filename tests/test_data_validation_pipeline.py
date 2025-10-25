"""
Tests for Data Validation Pipeline Module

**Phase 10A Week 2 - Agent 4: Data Validation & Quality - Phase 2**
Comprehensive tests for data_validation_pipeline.py module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import tempfile
import shutil

from mcp_server.data_validation_pipeline import (
    DataValidationPipeline,
    PipelineConfig,
    PipelineResult,
    PipelineStage,
    ValidationSeverity,
    ValidationIssue,
)


@pytest.fixture
def sample_player_data():
    """Sample player statistics data"""
    return pd.DataFrame(
        {
            "player_id": [1, 2, 3, 4, 5],
            "player_name": ["LeBron James", "Kevin Durant", "Stephen Curry", "Giannis Antetokounmpo", "Luka Doncic"],
            "ppg": [27.2, 29.1, 28.7, 29.9, 28.4],
            "rpg": [7.5, 7.1, 5.2, 11.6, 9.1],
            "apg": [7.3, 5.0, 6.5, 5.8, 8.7],
            "fg_pct": [0.505, 0.526, 0.481, 0.553, 0.473],
        }
    )


@pytest.fixture
def sample_game_data():
    """Sample game data"""
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
    """Sample team data"""
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


@pytest.fixture
def temp_output_dir():
    """Temporary output directory for test results"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def pipeline_config(temp_output_dir):
    """Pipeline configuration for testing"""
    return PipelineConfig(
        enable_schema_validation=True,
        enable_quality_check=True,
        enable_business_rules=True,
        enable_profiling=False,
        min_quality_score=0.9,
        max_null_percentage=0.05,
        max_duplicate_percentage=0.01,
        fail_on_critical=True,
        fail_on_error=False,
        save_results=True,
        output_dir=temp_output_dir,
    )


# Test 1: Pipeline initialization
def test_pipeline_initialization(pipeline_config):
    """Test pipeline initialization with config"""
    pipeline = DataValidationPipeline(config=pipeline_config)
    assert pipeline.config == pipeline_config
    assert pipeline.execution_history == []


# Test 2: Pipeline initialization with default config
def test_pipeline_default_config():
    """Test pipeline initialization with default config"""
    pipeline = DataValidationPipeline()
    assert pipeline.config is not None
    assert isinstance(pipeline.config, PipelineConfig)


# Test 3: Successful validation with player data
def test_validate_player_data_success(sample_player_data, pipeline_config):
    """Test successful validation of player data"""
    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(sample_player_data, "player_stats")

    assert result.pipeline_id.startswith("player_stats_")
    assert result.dataset_name == "player_stats"
    assert result.current_stage in [PipelineStage.COMPLETED, PipelineStage.FAILED]
    assert result.end_time is not None
    assert result.duration_seconds > 0
    assert result.data_summary["row_count"] == 5
    assert result.data_summary["column_count"] == 6


# Test 4: Validation with schema check
def test_validate_with_schema(sample_player_data, pipeline_config):
    """Test validation with schema check"""
    schema = {
        "columns": ["player_id", "player_name", "ppg", "rpg", "apg", "fg_pct"],
        "types": {
            "player_id": "int64",
            "player_name": "object",
            "ppg": "float64",
        },
    }

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(sample_player_data, "player_stats", schema=schema)

    # Should pass schema validation
    schema_issues = [
        i for i in result.issues if i.stage == PipelineStage.SCHEMA_VALIDATION
    ]
    # No error-level schema issues expected
    assert all(i.severity != ValidationSeverity.ERROR for i in schema_issues)


# Test 5: Schema validation - missing columns
def test_schema_validation_missing_columns(sample_player_data, pipeline_config):
    """Test schema validation with missing columns"""
    schema = {
        "columns": ["player_id", "player_name", "ppg", "rpg", "apg", "fg_pct", "missing_column"],
    }

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(sample_player_data, "player_stats", schema=schema)

    # Should have error for missing column
    schema_issues = [
        i
        for i in result.issues
        if i.stage == PipelineStage.SCHEMA_VALIDATION
        and i.severity == ValidationSeverity.ERROR
    ]
    assert len(schema_issues) > 0
    assert any("missing" in i.message.lower() for i in schema_issues)


# Test 6: Schema validation - extra columns
def test_schema_validation_extra_columns(sample_player_data, pipeline_config):
    """Test schema validation with extra columns"""
    schema = {
        "columns": ["player_id", "player_name", "ppg"],
    }

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(sample_player_data, "player_stats", schema=schema)

    # Should have warning for extra columns
    schema_issues = [
        i
        for i in result.issues
        if i.stage == PipelineStage.SCHEMA_VALIDATION
        and i.severity == ValidationSeverity.WARNING
    ]
    assert len(schema_issues) > 0
    assert any("unexpected" in i.message.lower() or "extra" in i.message.lower() for i in schema_issues)


# Test 7: Quality check - null values
def test_quality_check_null_values(pipeline_config):
    """Test quality check with null values"""
    df_with_nulls = pd.DataFrame(
        {
            "col1": [1, 2, None, 4, 5, None, None, 8, 9, 10],  # 30% nulls
            "col2": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
        }
    )

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(df_with_nulls, "test_data")

    # Should have warning for high null percentage
    quality_issues = [
        i
        for i in result.issues
        if i.stage == PipelineStage.QUALITY_CHECK and "null" in i.message.lower()
    ]
    assert len(quality_issues) > 0


# Test 8: Quality check - duplicates
def test_quality_check_duplicates(pipeline_config):
    """Test quality check with duplicate rows"""
    df_with_dupes = pd.DataFrame(
        {
            "col1": [1, 2, 3, 1, 2],  # 2 duplicates
            "col2": ["a", "b", "c", "a", "b"],
        }
    )

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(df_with_dupes, "test_data")

    # Should detect duplicates
    quality_issues = [
        i
        for i in result.issues
        if i.stage == PipelineStage.QUALITY_CHECK and "duplicate" in i.message.lower()
    ]
    assert len(quality_issues) > 0


# Test 9: Business rules - player stats validation
def test_business_rules_player_stats(pipeline_config):
    """Test business rules for player stats"""
    invalid_player_data = pd.DataFrame(
        {
            "player_id": [1, 2],
            "player_name": ["Player1", "Player2"],
            "ppg": [-5, 250],  # Invalid: negative and too high
            "fg_pct": [1.5, -0.2],  # Invalid: >1 and negative
        }
    )

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(invalid_player_data, "player_stats")

    # Should have business rule errors
    business_issues = [
        i
        for i in result.issues
        if i.stage == PipelineStage.BUSINESS_RULES
    ]
    assert len(business_issues) > 0


# Test 10: Business rules - game data validation
def test_business_rules_game_data(sample_game_data, pipeline_config):
    """Test business rules for game data"""
    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(sample_game_data, "game_results")

    # Valid game data should pass
    business_errors = [
        i
        for i in result.issues
        if i.stage == PipelineStage.BUSINESS_RULES
        and i.severity == ValidationSeverity.ERROR
    ]
    assert len(business_errors) == 0


# Test 11: Business rules - invalid game scores
def test_business_rules_invalid_game_scores(pipeline_config):
    """Test business rules with invalid game scores"""
    invalid_game_data = pd.DataFrame(
        {
            "game_id": [1, 2],
            "home_score": [-10, 250],  # Invalid: negative and unrealistic
            "away_score": [100, 105],
        }
    )

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(invalid_game_data, "game_results")

    # Should have business rule errors
    business_issues = [
        i
        for i in result.issues
        if i.stage == PipelineStage.BUSINESS_RULES
    ]
    assert len(business_issues) > 0


# Test 12: Business rules - team data validation
def test_business_rules_team_data(sample_team_data, pipeline_config):
    """Test business rules for team data"""
    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(sample_team_data, "team_standings")

    # Valid team data should pass
    business_errors = [
        i
        for i in result.issues
        if i.stage == PipelineStage.BUSINESS_RULES
        and i.severity == ValidationSeverity.ERROR
    ]
    assert len(business_errors) == 0


# Test 13: Business rules - invalid win percentage
def test_business_rules_invalid_win_percentage(pipeline_config):
    """Test business rules with invalid win percentage"""
    invalid_team_data = pd.DataFrame(
        {
            "team_id": [1, 2],
            "team_name": ["Team1", "Team2"],
            "team": ["Team1", "Team2"],  # Add team column for team detection
            "win_pct": [1.5, -0.2],  # Invalid: >1 and negative
        }
    )

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(invalid_team_data, "team_data")  # Use "team" in name

    # Should have business rule errors
    business_issues = [
        i
        for i in result.issues
        if i.stage == PipelineStage.BUSINESS_RULES
    ]
    # Check that at least one business rule issue was found
    assert len(business_issues) > 0, f"Expected business rule issues but got: {result.issues}"


# Test 14: Custom validation rules
def test_custom_validation_rules(sample_player_data, pipeline_config):
    """Test custom validation rules"""

    def custom_rule_passes(df):
        """Custom rule that always passes"""
        return True

    def custom_rule_fails(df):
        """Custom rule that always fails"""
        return False

    def custom_rule_error(df):
        """Custom rule that returns error message"""
        return "Custom validation error"

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(
        sample_player_data,
        "player_stats",
        custom_rules=[custom_rule_passes, custom_rule_fails, custom_rule_error],
    )

    # Should have issues from failing custom rules
    custom_issues = [
        i
        for i in result.issues
        if "custom" in i.message.lower()
    ]
    assert len(custom_issues) >= 2  # At least from fails and error


# Test 15: Custom rule exception handling
def test_custom_rule_exception(sample_player_data, pipeline_config):
    """Test custom rule exception handling"""

    def custom_rule_raises(df):
        """Custom rule that raises exception"""
        raise ValueError("Test exception")

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(
        sample_player_data, "player_stats", custom_rules=[custom_rule_raises]
    )

    # Should handle exception gracefully
    exception_issues = [
        i
        for i in result.issues
        if "exception" in i.message.lower() or "raised" in i.message.lower()
    ]
    assert len(exception_issues) > 0


# Test 16: Empty dataset validation
def test_empty_dataset_validation(pipeline_config):
    """Test validation of empty dataset"""
    empty_df = pd.DataFrame()

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(empty_df, "empty_data")

    # Should have error for empty dataset
    ingestion_issues = [
        i
        for i in result.issues
        if i.stage == PipelineStage.INGESTION and "empty" in i.message.lower()
    ]
    assert len(ingestion_issues) > 0


# Test 17: Small dataset warning
def test_small_dataset_warning(pipeline_config):
    """Test warning for small dataset"""
    small_df = pd.DataFrame({"col1": [1, 2, 3]})

    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(small_df, "small_data")

    # Should have warning for small dataset
    ingestion_warnings = [
        i
        for i in result.issues
        if i.stage == PipelineStage.INGESTION
        and i.severity == ValidationSeverity.WARNING
    ]
    assert len(ingestion_warnings) > 0


# Test 18: Results persistence
def test_results_persistence(sample_player_data, pipeline_config, temp_output_dir):
    """Test that results are persisted to disk"""
    pipeline = DataValidationPipeline(config=pipeline_config)
    result = pipeline.validate(sample_player_data, "player_stats")

    # Check that results file exists
    results_files = list(temp_output_dir.glob("*.json"))
    assert len(results_files) > 0

    # Verify file contains valid JSON
    with open(results_files[0], "r") as f:
        saved_result = json.load(f)

    assert saved_result["pipeline_id"] == result.pipeline_id
    assert saved_result["dataset_name"] == result.dataset_name


# Test 19: Execution history
def test_execution_history(sample_player_data, sample_game_data, pipeline_config):
    """Test execution history tracking"""
    pipeline = DataValidationPipeline(config=pipeline_config)

    # Execute multiple validations
    pipeline.validate(sample_player_data, "player_stats")
    pipeline.validate(sample_game_data, "game_results")

    # Check history
    history = pipeline.get_execution_history()
    assert len(history) == 2

    # Filter by dataset
    player_history = pipeline.get_execution_history(dataset_name="player_stats")
    assert len(player_history) == 1
    assert player_history[0].dataset_name == "player_stats"


# Test 20: Pipeline statistics
def test_pipeline_statistics(sample_player_data, pipeline_config):
    """Test pipeline statistics"""
    pipeline = DataValidationPipeline(config=pipeline_config)

    # Initially empty
    stats = pipeline.get_statistics()
    assert stats["total_executions"] == 0
    assert stats["success_rate"] == 0.0

    # After execution
    pipeline.validate(sample_player_data, "player_stats")
    stats = pipeline.get_statistics()
    assert stats["total_executions"] == 1
    assert stats["avg_duration_seconds"] > 0
