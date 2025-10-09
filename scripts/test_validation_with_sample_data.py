#!/usr/bin/env python3
"""
Test Data Quality Validation with Sample Data
Uses sample CSV files to demonstrate 100% pass rate
"""

import asyncio
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_quality.validator import DataValidator
from data_quality.expectations import (
    create_game_expectations,
    create_player_expectations,
    create_team_expectations
)


async def validate_with_sample_data():
    """Validate sample data to demonstrate 100% pass rates"""

    print("=" * 80)
    print("NBA MCP Synthesis - Data Quality Validation with Sample Data")
    print("=" * 80)
    print()

    # Initialize validator in test mode (in-memory)
    validator = DataValidator(use_configured_context=False)

    # Load sample data
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"

    # Test 1: Games
    print("📊 Validating GAMES table...")
    games_df = pd.read_csv(fixtures_dir / "sample_games.csv")
    games_result = await validator.validate_table(
        table_name="games",
        data=games_df,
        expectations=create_game_expectations()
    )

    print(f"   Rows validated: {games_result['rows_validated']}")
    print(f"   Pass rate: {games_result['summary']['pass_rate']*100:.1f}%")
    print(f"   Passed: {games_result['summary']['passed']}/{games_result['summary']['total_expectations']}")

    if games_result['summary']['failed'] > 0:
        print(f"   ⚠️  Failed expectations:")
        for failure in games_result['failed_expectations']:
            print(f"      - {failure['expectation']} on {failure.get('column', 'N/A')}")
    else:
        print(f"   ✅ All expectations passed!")
    print()

    # Test 2: Players
    print("📊 Validating PLAYERS table...")
    players_df = pd.read_csv(fixtures_dir / "sample_players.csv")
    players_result = await validator.validate_table(
        table_name="players",
        data=players_df,
        expectations=create_player_expectations()
    )

    print(f"   Rows validated: {players_result['rows_validated']}")
    print(f"   Pass rate: {players_result['summary']['pass_rate']*100:.1f}%")
    print(f"   Passed: {players_result['summary']['passed']}/{players_result['summary']['total_expectations']}")

    if players_result['summary']['failed'] > 0:
        print(f"   ⚠️  Failed expectations:")
        for failure in players_result['failed_expectations']:
            print(f"      - {failure['expectation']} on {failure.get('column', 'N/A')}")
    else:
        print(f"   ✅ All expectations passed!")
    print()

    # Test 3: Teams
    print("📊 Validating TEAMS table...")
    teams_df = pd.read_csv(fixtures_dir / "sample_teams.csv")
    teams_result = await validator.validate_table(
        table_name="teams",
        data=teams_df,
        expectations=create_team_expectations()
    )

    print(f"   Rows validated: {teams_result['rows_validated']}")
    print(f"   Pass rate: {teams_result['summary']['pass_rate']*100:.1f}%")
    print(f"   Passed: {teams_result['summary']['passed']}/{teams_result['summary']['total_expectations']}")

    if teams_result['summary']['failed'] > 0:
        print(f"   ⚠️  Failed expectations:")
        for failure in teams_result['failed_expectations']:
            print(f"      - {failure['expectation']} on {failure.get('column', 'N/A')}")
    else:
        print(f"   ✅ All expectations passed!")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    overall_pass = (
        games_result['summary']['pass_rate'] +
        players_result['summary']['pass_rate'] +
        teams_result['summary']['pass_rate']
    ) / 3 * 100

    print(f"Overall Pass Rate: {overall_pass:.1f}%")
    print(f"Games: {games_result['summary']['pass_rate']*100:.1f}%")
    print(f"Players: {players_result['summary']['pass_rate']*100:.1f}%")
    print(f"Teams: {teams_result['summary']['pass_rate']*100:.1f}%")

    if overall_pass == 100.0:
        print("\n✅ SUCCESS: All validations passed with 100% pass rate!")
        return 0
    else:
        print(f"\n⚠️  Some validations failed (overall: {overall_pass:.1f}%)")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(validate_with_sample_data())
    sys.exit(exit_code)
