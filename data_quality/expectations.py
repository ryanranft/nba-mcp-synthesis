"""
Data Quality Expectations
Predefined expectation suites for NBA data tables
"""

from typing import List, Dict, Any


def create_game_expectations() -> List[Dict[str, Any]]:
    """
    Create expectations for games table

    Returns:
        List of expectation configurations
    """
    return [
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "game_id"},
        },
        {"type": "expect_column_values_to_be_unique", "kwargs": {"column": "game_id"}},
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "game_date"},
        },
        {
            "type": "expect_column_values_to_be_between",
            "kwargs": {"column": "home_team_score", "min_value": 0, "max_value": 200},
        },
        {
            "type": "expect_column_values_to_be_between",
            "kwargs": {"column": "away_team_score", "min_value": 0, "max_value": 200},
        },
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "home_team_id"},
        },
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "away_team_id"},
        },
    ]


def create_player_expectations() -> List[Dict[str, Any]]:
    """
    Create expectations for players table

    Returns:
        List of expectation configurations
    """
    return [
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "player_id"},
        },
        {
            "type": "expect_column_values_to_be_unique",
            "kwargs": {"column": "player_id"},
        },
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "player_name"},
        },
        {
            "type": "expect_column_values_to_be_between",
            "kwargs": {
                "column": "points",
                "min_value": 0,
                "max_value": 100,  # Single game max
            },
        },
        {
            "type": "expect_column_values_to_be_between",
            "kwargs": {"column": "rebounds", "min_value": 0, "max_value": 50},
        },
        {
            "type": "expect_column_values_to_be_between",
            "kwargs": {"column": "assists", "min_value": 0, "max_value": 30},
        },
    ]


def create_team_expectations() -> List[Dict[str, Any]]:
    """
    Create expectations for teams table

    Returns:
        List of expectation configurations
    """
    return [
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "team_id"},
        },
        {"type": "expect_column_values_to_be_unique", "kwargs": {"column": "team_id"}},
        {
            "type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": "team_name"},
        },
    ]


# Expectation suite registry
EXPECTATION_SUITES = {
    "games": create_game_expectations,
    "players": create_player_expectations,
    "teams": create_team_expectations,
}


def get_expectations_for_table(table_name: str) -> List[Dict[str, Any]]:
    """
    Get predefined expectations for a table

    Args:
        table_name: Name of the table

    Returns:
        List of expectations, or empty list if none defined
    """
    suite_func = EXPECTATION_SUITES.get(table_name)
    if suite_func:
        return suite_func()
    return []
