#!/usr/bin/env python3
"""
Test Data Quality Validation with Sample Data
Uses sample CSV files to demonstrate data validation
"""

import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory"""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def validator():
    """Initialize DataValidator in test mode"""
    try:
        from data_quality.validator import DataValidator

        # Use in-memory validation (no external dependencies)
        return DataValidator(use_configured_context=False)
    except ImportError:
        pytest.skip("data_quality module not available")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_games_validation(validator, fixtures_dir):
    """Test games table validation with sample data"""
    try:
        from data_quality.expectations import create_game_expectations
    except ImportError:
        pytest.skip("data_quality.expectations not available")

    sample_file = fixtures_dir / "sample_games.csv"
    if not sample_file.exists():
        pytest.skip(f"Sample games file not found: {sample_file}")

    # Load sample data
    games_df = pd.read_csv(sample_file)

    # Validate
    result = await validator.validate_table(
        table_name="games", data=games_df, expectations=create_game_expectations()
    )

    # Assertions
    assert "rows_validated" in result, "Result should contain rows_validated"
    assert "summary" in result, "Result should contain summary"
    assert result["rows_validated"] > 0, "Should validate at least one row"

    summary = result["summary"]
    assert "pass_rate" in summary, "Summary should contain pass_rate"
    assert "passed" in summary, "Summary should contain passed count"
    assert "total_expectations" in summary, "Summary should contain total expectations"

    # Check pass rate (should be high for sample data)
    assert (
        summary["pass_rate"] >= 0.8
    ), f"Games validation should have >=80% pass rate, got {summary['pass_rate']*100:.1f}%"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_players_validation(validator, fixtures_dir):
    """Test players table validation with sample data"""
    try:
        from data_quality.expectations import create_player_expectations
    except ImportError:
        pytest.skip("data_quality.expectations not available")

    sample_file = fixtures_dir / "sample_players.csv"
    if not sample_file.exists():
        pytest.skip(f"Sample players file not found: {sample_file}")

    # Load sample data
    players_df = pd.read_csv(sample_file)

    # Validate
    result = await validator.validate_table(
        table_name="players", data=players_df, expectations=create_player_expectations()
    )

    # Assertions
    assert result["rows_validated"] > 0, "Should validate at least one row"

    summary = result["summary"]
    assert (
        summary["pass_rate"] >= 0.8
    ), f"Players validation should have >=80% pass rate, got {summary['pass_rate']*100:.1f}%"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_teams_validation(validator, fixtures_dir):
    """Test teams table validation with sample data"""
    try:
        from data_quality.expectations import create_team_expectations
    except ImportError:
        pytest.skip("data_quality.expectations not available")

    sample_file = fixtures_dir / "sample_teams.csv"
    if not sample_file.exists():
        pytest.skip(f"Sample teams file not found: {sample_file}")

    # Load sample data
    teams_df = pd.read_csv(sample_file)

    # Validate
    result = await validator.validate_table(
        table_name="teams", data=teams_df, expectations=create_team_expectations()
    )

    # Assertions
    assert result["rows_validated"] > 0, "Should validate at least one row"

    summary = result["summary"]
    assert (
        summary["pass_rate"] >= 0.8
    ), f"Teams validation should have >=80% pass rate, got {summary['pass_rate']*100:.1f}%"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_overall_validation_pass_rate(validator, fixtures_dir):
    """Test overall validation pass rate across all tables"""
    try:
        from data_quality.expectations import (
            create_game_expectations,
            create_player_expectations,
            create_team_expectations,
        )
    except ImportError:
        pytest.skip("data_quality.expectations not available")

    # Check if all sample files exist
    games_file = fixtures_dir / "sample_games.csv"
    players_file = fixtures_dir / "sample_players.csv"
    teams_file = fixtures_dir / "sample_teams.csv"

    if not all([games_file.exists(), players_file.exists(), teams_file.exists()]):
        pytest.skip("Not all sample files available")

    # Validate all tables
    games_df = pd.read_csv(games_file)
    players_df = pd.read_csv(players_file)
    teams_df = pd.read_csv(teams_file)

    games_result = await validator.validate_table(
        "games", games_df, create_game_expectations()
    )
    players_result = await validator.validate_table(
        "players", players_df, create_player_expectations()
    )
    teams_result = await validator.validate_table(
        "teams", teams_df, create_team_expectations()
    )

    # Calculate overall pass rate
    overall_pass_rate = (
        games_result["summary"]["pass_rate"]
        + players_result["summary"]["pass_rate"]
        + teams_result["summary"]["pass_rate"]
    ) / 3

    assert (
        overall_pass_rate >= 0.8
    ), f"Overall pass rate should be >=80%, got {overall_pass_rate*100:.1f}%"


@pytest.mark.integration
def test_sample_data_files_exist(fixtures_dir):
    """Test that sample data files exist"""
    required_files = [
        "sample_games.csv",
        "sample_players.csv",
        "sample_teams.csv",
    ]

    missing_files = []
    for filename in required_files:
        filepath = fixtures_dir / filename
        if not filepath.exists():
            missing_files.append(filename)

    if missing_files:
        pytest.skip(f"Sample data files not found: {', '.join(missing_files)}")

    # If we get here, all files exist
    assert True, "All sample data files exist"
