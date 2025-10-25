"""
Tests for validation.py module

**Phase 10A Week 2 - Agent 4: Data Validation & Quality**
Tests for NBA-specific validators, schema validation, and bulk validation.
"""

import pytest
import pandas as pd
from datetime import datetime
from pydantic import ValidationError
from mcp_server.validation import (
    # Original validators
    PlayerQuery,
    GameQuery,
    StatsQuery,
    validate_request,
    # NBA-specific validators
    PlayerStatsModel,
    GameDataModel,
    TeamDataModel,
    # Schema validation
    validate_json_schema,
    validate_dataframe_schema,
    # Bulk validation
    ValidationResult,
    validate_batch,
    aggregate_validation_results,
)


# NBA-Specific Validator Tests (3 tests)


def test_player_stats_model_valid():
    """Test valid player stats model"""
    data = {
        "player_id": 123,
        "player_name": "LeBron James",
        "season": 2024,
        "team_abbreviation": "LAL",
        "games_played": 70,
        "minutes_per_game": 35.5,
        "points_per_game": 27.2,
        "rebounds_per_game": 8.1,
        "assists_per_game": 7.4,
        "field_goal_percentage": 0.515,
        "three_point_percentage": 0.385,
        "free_throw_percentage": 0.756,
    }

    model = PlayerStatsModel(**data)

    assert model.player_id == 123
    assert model.player_name == "LeBron James"
    assert model.points_per_game == 27.2
    assert model.field_goal_percentage == 0.515


def test_player_stats_model_invalid():
    """Test invalid player stats model"""
    data = {
        "player_id": -1,  # Invalid: must be > 0
        "player_name": "Test Player",
        "season": 2024,
        "games_played": 100,  # Invalid: max 82
        "minutes_per_game": 35.5,
        "points_per_game": 100.0,  # Invalid: max 50
        "rebounds_per_game": 8.0,
        "assists_per_game": 7.0,
    }

    with pytest.raises(ValidationError) as exc_info:
        PlayerStatsModel(**data)

    errors = exc_info.value.errors()
    error_fields = [e["loc"][0] for e in errors]
    assert "player_id" in error_fields
    assert "games_played" in error_fields
    assert "points_per_game" in error_fields


def test_game_data_model_valid():
    """Test valid game data model"""
    data = {
        "game_id": 12345,
        "season": 2024,
        "game_date": datetime(2024, 3, 15, 19, 30),
        "home_team": "Lakers",
        "away_team": "Warriors",
        "home_score": 115,
        "away_score": 110,
        "overtime": False,
        "attendance": 18997,
    }

    model = GameDataModel(**data)

    assert model.game_id == 12345
    assert model.home_team == "Lakers"
    assert model.away_team == "Warriors"
    assert model.home_score == 115


def test_game_data_model_same_teams():
    """Test game data model with same home and away teams"""
    data = {
        "game_id": 12345,
        "season": 2024,
        "game_date": datetime(2024, 3, 15, 19, 30),
        "home_team": "Lakers",
        "away_team": "Lakers",  # Same as home team
        "home_score": 115,
        "away_score": 110,
    }

    with pytest.raises(ValidationError) as exc_info:
        GameDataModel(**data)

    errors = exc_info.value.errors()
    assert any("different" in str(e["msg"]).lower() for e in errors)


def test_team_data_model_valid():
    """Test valid team data model"""
    data = {
        "team_id": 1,
        "team_name": "Los Angeles Lakers",
        "team_abbreviation": "LAL",
        "conference": "Western",
        "division": "Pacific",
        "season": 2024,
        "wins": 50,
        "losses": 32,
        "win_percentage": 0.610,
    }

    model = TeamDataModel(**data)

    assert model.team_id == 1
    assert model.team_name == "Los Angeles Lakers"
    assert model.conference == "Western"
    assert model.wins == 50


def test_team_data_model_invalid_conference():
    """Test team data model with invalid conference"""
    data = {
        "team_id": 1,
        "team_name": "Lakers",
        "team_abbreviation": "LAL",
        "conference": "Invalid",  # Must be Eastern or Western
        "division": "Pacific",
        "season": 2024,
        "wins": 50,
        "losses": 32,
    }

    with pytest.raises(ValidationError) as exc_info:
        TeamDataModel(**data)

    errors = exc_info.value.errors()
    error_fields = [e["loc"][0] for e in errors]
    assert "conference" in error_fields


# Schema Validation Tests (2 tests)


def test_validate_json_schema_valid():
    """Test JSON schema validation with valid data"""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
        },
        "required": ["name", "age"],
    }

    data = {"name": "John Doe", "age": 25}

    errors = validate_json_schema(data, schema)

    assert len(errors) == 0


def test_validate_json_schema_invalid():
    """Test JSON schema validation with invalid data"""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
        },
        "required": ["name", "age"],
    }

    data = {"name": "John Doe"}  # Missing required 'age'

    errors = validate_json_schema(data, schema)

    assert len(errors) > 0


def test_validate_dataframe_schema_valid():
    """Test DataFrame schema validation with valid data"""
    df = pd.DataFrame(
        {
            "player_id": [1, 2, 3],
            "player_name": ["Alice", "Bob", "Charlie"],
            "points": [25, 30, 22],
        }
    )

    errors = validate_dataframe_schema(
        df,
        expected_columns=["player_id", "player_name", "points"],
        column_types={"player_id": "int64", "player_name": "object", "points": "int64"},
    )

    assert len(errors) == 0


def test_validate_dataframe_schema_missing_columns():
    """Test DataFrame schema validation with missing columns"""
    df = pd.DataFrame({"player_id": [1, 2, 3], "points": [25, 30, 22]})

    errors = validate_dataframe_schema(
        df, expected_columns=["player_id", "player_name", "points"]
    )

    assert len(errors) > 0
    assert any("missing" in err.lower() for err in errors)


# Bulk Validation Tests (2 tests)


def test_validate_batch_all_valid():
    """Test batch validation with all valid records"""
    records = [
        {
            "player_id": 1,
            "player_name": "Player 1",
            "season": 2024,
            "games_played": 70,
            "minutes_per_game": 30.0,
            "points_per_game": 20.0,
            "rebounds_per_game": 7.0,
            "assists_per_game": 5.0,
        },
        {
            "player_id": 2,
            "player_name": "Player 2",
            "season": 2024,
            "games_played": 75,
            "minutes_per_game": 32.0,
            "points_per_game": 22.0,
            "rebounds_per_game": 8.0,
            "assists_per_game": 6.0,
        },
    ]

    result = validate_batch(records, PlayerStatsModel)

    assert result["total"] == 2
    assert result["valid"] == 2
    assert result["invalid"] == 0
    assert len(result["results"]) == 2
    assert all(r.is_valid for r in result["results"])


def test_validate_batch_mixed_validity():
    """Test batch validation with mixed valid/invalid records"""
    records = [
        {
            "player_id": 1,
            "player_name": "Valid Player",
            "season": 2024,
            "games_played": 70,
            "minutes_per_game": 30.0,
            "points_per_game": 20.0,
            "rebounds_per_game": 7.0,
            "assists_per_game": 5.0,
        },
        {
            "player_id": -1,  # Invalid
            "player_name": "Invalid Player",
            "season": 2024,
            "games_played": 100,  # Invalid
            "minutes_per_game": 30.0,
            "points_per_game": 20.0,
            "rebounds_per_game": 7.0,
            "assists_per_game": 5.0,
        },
    ]

    result = validate_batch(records, PlayerStatsModel)

    assert result["total"] == 2
    assert result["valid"] == 1
    assert result["invalid"] == 1


def test_aggregate_validation_results():
    """Test aggregation of validation results"""
    results = [
        ValidationResult(is_valid=True, validated_data={"id": 1}),
        ValidationResult(is_valid=True, validated_data={"id": 2}),
        ValidationResult(
            is_valid=False,
            errors=["Invalid value", "Missing field"],
            validated_data={"id": 3},
        ),
        ValidationResult(
            is_valid=False, errors=["Invalid value"], validated_data={"id": 4}
        ),
    ]

    summary = aggregate_validation_results(results)

    assert summary["total"] == 4
    assert summary["valid_count"] == 2
    assert summary["invalid_count"] == 2
    assert summary["success_rate"] == 50.0
    assert len(summary["common_errors"]) > 0
    assert summary["common_errors"][0]["error"] == "Invalid value"
    assert summary["common_errors"][0]["count"] == 2


# Original Validator Tests (Enhanced Coverage - 8 tests)


def test_player_query_valid():
    """Test valid player query"""
    data = {"player_name": "LeBron James", "season": 2024, "team": "Lakers"}

    query = PlayerQuery(**data)

    assert query.player_name == "LeBron James"
    assert query.season == 2024


def test_player_query_sanitization():
    """Test player query sanitization"""
    data = {
        "player_name": "<script>alert('xss')</script>",
        "season": 2024,
    }

    query = PlayerQuery(**data)

    # Should be sanitized (HTML escaped, script tags removed)
    assert "<script>" not in query.player_name or "&lt;script&gt;" in query.player_name
    # The dangerous parts should be escaped/removed
    assert query.player_name != "<script>alert('xss')</script>"


def test_game_query_valid():
    """Test valid game query"""
    data = {
        "game_id": 12345,
        "season": 2024,
        "team_name": "Lakers",
        "limit": 100,
        "offset": 0,
    }

    query = GameQuery(**data)

    assert query.game_id == 12345
    assert query.limit == 100


def test_game_query_limits():
    """Test game query with limit constraints"""
    data = {"season": 2024, "limit": 5000}  # Exceeds max of 1000

    with pytest.raises(ValidationError):
        GameQuery(**data)


def test_stats_query_valid():
    """Test valid stats query"""
    data = {"metric": "points_per_game", "season": 2024, "min_games": 20, "limit": 500}

    query = StatsQuery(**data)

    assert query.metric == "points_per_game"
    assert query.min_games == 20


def test_stats_query_invalid_metric():
    """Test stats query with invalid metric pattern"""
    data = {"metric": "invalid-metric!", "season": 2024}  # Contains invalid characters

    with pytest.raises(ValidationError):
        StatsQuery(**data)


def test_validate_request_function():
    """Test validate_request utility function"""
    data = {"player_name": "Test Player", "season": 2024}

    validated = validate_request(data, PlayerQuery)

    assert isinstance(validated, PlayerQuery)
    assert validated.player_name == "Test Player"


def test_validate_request_function_failure():
    """Test validate_request utility function with invalid data"""
    data = {"player_name": "Test Player", "season": 1800}  # Season too early

    with pytest.raises(ValidationError):
        validate_request(data, PlayerQuery)
