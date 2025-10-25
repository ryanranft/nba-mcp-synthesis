"""
Tests for Integrity Checker Module

**Phase 10A Week 2 - Agent 4: Data Validation & Quality - Phase 2**
Comprehensive tests for integrity_checker.py module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from mcp_server.integrity_checker import (
    IntegrityChecker,
    IntegrityReport,
    IntegrityViolation,
    IntegrityViolationType,
)


@pytest.fixture
def sample_player_data():
    """Sample NBA player data"""
    return pd.DataFrame(
        {
            "player_id": [1, 2, 3, 4, 5],
            "player_name": ["Player1", "Player2", "Player3", "Player4", "Player5"],
            "ppg": [25.0, 28.0, 22.0, 30.0, 24.0],
            "games_played": [75, 68, 80, 72, 77],
            "fgm": [8.5, 9.2, 7.8, 10.1, 8.3],
            "fga": [18.0, 17.5, 16.9, 18.3, 17.1],
            "fg_pct": [0.472, 0.526, 0.461, 0.552, 0.485],
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


# Test 1: IntegrityChecker initialization
def test_integrity_checker_initialization():
    """Test IntegrityChecker initialization"""
    checker = IntegrityChecker()
    assert checker.check_history == []


# Test 2: Check referential integrity - valid
def test_check_referential_integrity_valid():
    """Test referential integrity with valid data"""
    df = pd.DataFrame({"team_id": [1, 2, 3, 1, 2]})
    valid_ids = {1, 2, 3}

    checker = IntegrityChecker()
    violations = checker.check_referential_integrity(df, "team_id", valid_ids)

    assert len(violations) == 0


# Test 3: Check referential integrity - invalid
def test_check_referential_integrity_invalid():
    """Test referential integrity with invalid data"""
    df = pd.DataFrame({"team_id": [1, 2, 99, 1, 88]})  # 99 and 88 are invalid
    valid_ids = {1, 2, 3}

    checker = IntegrityChecker()
    violations = checker.check_referential_integrity(df, "team_id", valid_ids)

    assert len(violations) == 1
    assert violations[0].violation_type == IntegrityViolationType.REFERENTIAL
    assert len(violations[0].row_indices) == 2  # 2 invalid rows


# Test 4: Check cross-field math - multiplication
def test_check_cross_field_math_multiply():
    """Test cross-field multiplication"""
    df = pd.DataFrame(
        {
            "field_a": [2, 3, 4],
            "field_b": [5, 6, 7],
            "result": [10, 18, 28],
        }
    )

    checker = IntegrityChecker()
    violations = checker.check_cross_field_math(
        df, "field_a", "field_b", "result", operation="multiply"
    )

    assert len(violations) == 0


# Test 5: Check cross-field math - invalid multiplication
def test_check_cross_field_math_multiply_invalid():
    """Test cross-field multiplication with errors"""
    df = pd.DataFrame(
        {
            "field_a": [2, 3, 4],
            "field_b": [5, 6, 7],
            "result": [10, 20, 28],  # 18 should be 18, not 20
        }
    )

    checker = IntegrityChecker()
    violations = checker.check_cross_field_math(
        df, "field_a", "field_b", "result", operation="multiply", tolerance=0.01
    )

    assert len(violations) == 1
    assert violations[0].violation_type == IntegrityViolationType.CROSS_FIELD
    assert len(violations[0].row_indices) == 1  # 1 invalid row


# Test 6: Check temporal consistency - valid dates
def test_check_temporal_consistency_valid():
    """Test temporal consistency with valid dates"""
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=5)})

    checker = IntegrityChecker()
    violations = checker.check_temporal_consistency(
        df,
        "date",
        min_date=datetime(2024, 1, 1),
        max_date=datetime(2024, 12, 31),
    )

    assert len(violations) == 0


# Test 7: Check temporal consistency - out of range dates
def test_check_temporal_consistency_out_of_range():
    """Test temporal consistency with out of range dates"""
    df = pd.DataFrame(
        {
            "date": [
                datetime(2023, 12, 31),  # Too early
                datetime(2024, 1, 1),
                datetime(2024, 1, 2),
                datetime(2025, 1, 1),  # Too late
            ]
        }
    )

    checker = IntegrityChecker()
    violations = checker.check_temporal_consistency(
        df,
        "date",
        min_date=datetime(2024, 1, 1),
        max_date=datetime(2024, 12, 31),
    )

    assert len(violations) == 2  # 1 too early, 1 too late


# Test 8: Check temporal consistency - sequence
def test_check_temporal_consistency_sequence():
    """Test temporal consistency sequence check"""
    df = pd.DataFrame(
        {
            "date": [
                datetime(2024, 1, 1),
                datetime(2024, 1, 3),
                datetime(2024, 1, 2),  # Out of sequence
                datetime(2024, 1, 4),
            ]
        }
    )

    checker = IntegrityChecker()
    violations = checker.check_temporal_consistency(df, "date", check_sequence=True)

    assert len(violations) == 1
    assert violations[0].violation_type == IntegrityViolationType.TEMPORAL


# Test 9: Check business rule
def test_check_business_rule():
    """Test custom business rule"""
    df = pd.DataFrame({"value": [1, 2, 3, 150, 5]})  # 150 violates rule

    checker = IntegrityChecker()
    rule_condition = df["value"] < 100
    violations = checker.check_business_rule(df, "value must be < 100", rule_condition)

    assert len(violations) == 1
    assert violations[0].violation_type == IntegrityViolationType.BUSINESS_RULE
    assert len(violations[0].row_indices) == 1


# Test 10: Check NBA player integrity - valid
def test_check_nba_player_integrity_valid(sample_player_data):
    """Test NBA player integrity with valid data"""
    checker = IntegrityChecker()
    violations = checker.check_nba_player_integrity(sample_player_data)

    # May have some tolerance violations in FG%, but should be minimal
    assert len(violations) <= 2  # Allow for small rounding differences


# Test 11: Check NBA player integrity - invalid games
def test_check_nba_player_integrity_invalid_games():
    """Test NBA player integrity with invalid games played"""
    df = pd.DataFrame(
        {
            "player_id": [1, 2],
            "games_played": [75, 100],  # 100 exceeds max 82
        }
    )

    checker = IntegrityChecker()
    violations = checker.check_nba_player_integrity(df)

    assert len(violations) >= 1
    # Should have violation for games > 82


# Test 12: Check NBA game integrity - valid
def test_check_nba_game_integrity_valid(sample_game_data):
    """Test NBA game integrity with valid data"""
    checker = IntegrityChecker()
    violations = checker.check_nba_game_integrity(sample_game_data)

    assert len(violations) == 0


# Test 13: Check NBA game integrity - same teams
def test_check_nba_game_integrity_same_teams():
    """Test NBA game integrity with same home/away team"""
    df = pd.DataFrame(
        {
            "game_id": [1, 2],
            "home_team": ["Lakers", "Warriors"],
            "away_team": ["Lakers", "Suns"],  # Lakers play themselves
        }
    )

    checker = IntegrityChecker()
    violations = checker.check_nba_game_integrity(df)

    assert len(violations) >= 1
    # Should detect same team violation


# Test 14: Check NBA team integrity - valid
def test_check_nba_team_integrity_valid(sample_team_data):
    """Test NBA team integrity with valid data"""
    checker = IntegrityChecker()
    violations = checker.check_nba_team_integrity(sample_team_data)

    # Should have no or minimal violations (small rounding in win_pct)
    assert len(violations) <= 1


# Test 15: Check NBA team integrity - invalid win percentage
def test_check_nba_team_integrity_invalid_win_pct():
    """Test NBA team integrity with invalid win percentage"""
    df = pd.DataFrame(
        {
            "wins": [50, 40],
            "losses": [32, 42],
            "win_pct": [0.610, 0.9],  # 0.9 is wrong (should be ~0.488)
        }
    )

    checker = IntegrityChecker()
    violations = checker.check_nba_team_integrity(df)

    assert len(violations) >= 1
    # Should detect incorrect win percentage


# Test 16: Comprehensive check with report
def test_comprehensive_check(sample_player_data):
    """Test comprehensive integrity check"""
    checker = IntegrityChecker()
    report = checker.check(sample_player_data, dataset_name="player_data")

    assert isinstance(report, IntegrityReport)
    assert report.dataset_name == "player_data"
    assert report.total_checks >= 1
    assert isinstance(report.passed, bool)
    assert report.violation_count == len(report.violations)


# Bonus tests to reach 16 total


# Test 17: IntegrityReport to_dict
def test_integrity_report_to_dict(sample_player_data):
    """Test IntegrityReport to_dict conversion"""
    checker = IntegrityChecker()
    report = checker.check(sample_player_data, "test_data")

    report_dict = report.to_dict()

    assert isinstance(report_dict, dict)
    assert "dataset_name" in report_dict
    assert "total_checks" in report_dict
    assert "violations" in report_dict


# Test 18: Get statistics
def test_get_statistics(sample_player_data):
    """Test integrity checker statistics"""
    checker = IntegrityChecker()

    # Initially empty
    stats = checker.get_statistics()
    assert stats["total_checks"] == 0

    # After check
    checker.check(sample_player_data, "test_data")
    stats = checker.get_statistics()

    assert stats["datasets_checked"] == 1
    assert "pass_rate" in stats
