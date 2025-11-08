#!/usr/bin/env python3
"""
MCP-Integrated Feature Engineering Pipeline

This version directly integrates with Claude Code's MCP server access
to extract NBA game features.

Note: This script is designed to be run WITH Claude Code's MCP integration.
For standalone execution, use prepare_game_features.py with direct DB connection.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import json

import numpy as np
import pandas as pd
from tqdm import tqdm

# This will be populated by Claude Code when executing
MCP_QUERY_RESULTS = {}


def load_games_data() -> pd.DataFrame:
    """Load games data from MCP query results."""
    if 'games' not in MCP_QUERY_RESULTS:
        raise ValueError("Games data not loaded. Run MCP query first.")
    return pd.DataFrame(MCP_QUERY_RESULTS['games'])


def load_team_stats_data() -> pd.DataFrame:
    """Load team stats data from MCP query results."""
    if 'team_stats' not in MCP_QUERY_RESULTS:
        raise ValueError("Team stats data not loaded. Run MCP query first.")
    return pd.DataFrame(MCP_QUERY_RESULTS['team_stats'])


def calculate_rolling_stats(
    team_stats: pd.DataFrame,
    team_id: int,
    before_date: datetime,
    window: int = 10
) -> Dict[str, float]:
    """Calculate rolling statistics for a team."""
    team_games = team_stats[
        (team_stats['team_id'] == team_id) &
        (pd.to_datetime(team_stats['game_date']) < before_date)
    ].copy()

    team_games = team_games.sort_values('game_date', ascending=False).head(window)

    if len(team_games) == 0:
        return {f'games_played': 0}

    # Calculate shooting percentages
    team_games['fg_pct'] = team_games['field_goals_made'] / team_games['field_goals_attempted'].replace(0, np.nan)
    team_games['three_pt_pct'] = team_games['three_pointers_made'] / team_games['three_pointers_attempted'].replace(0, np.nan)
    team_games['ft_pct'] = team_games['free_throws_made'] / team_games['free_throws_attempted'].replace(0, np.nan)
    team_games['total_rebounds'] = team_games['offensive_rebounds'] + team_games['defensive_rebounds']

    # Advanced metrics
    team_games['ts_pct'] = team_games['points'] / (
        2 * (team_games['field_goals_attempted'] + 0.44 * team_games['free_throws_attempted'])
    ).replace(0, np.nan)
    team_games['efg_pct'] = (
        team_games['field_goals_made'] + 0.5 * team_games['three_pointers_made']
    ) / team_games['field_goals_attempted'].replace(0, np.nan)

    return {
        f'ppg_l{window}': float(team_games['points'].mean()),
        f'fg_pct_l{window}': float(team_games['fg_pct'].mean()),
        f'three_pt_pct_l{window}': float(team_games['three_pt_pct'].mean()),
        f'ft_pct_l{window}': float(team_games['ft_pct'].mean()),
        f'rebounds_l{window}': float(team_games['total_rebounds'].mean()),
        f'assists_l{window}': float(team_games['assists'].mean()),
        f'steals_l{window}': float(team_games['steals'].mean()),
        f'blocks_l{window}': float(team_games['blocks'].mean()),
        f'turnovers_l{window}': float(team_games['turnovers'].mean()),
        f'ts_pct_l{window}': float(team_games['ts_pct'].mean()),
        f'efg_pct_l{window}': float(team_games['efg_pct'].mean()),
        f'games_played': len(team_games)
    }


def calculate_location_split(
    team_stats: pd.DataFrame,
    team_id: int,
    before_date: datetime,
    location: str,
    window: int = 20
) -> Dict[str, float]:
    """Calculate home/away split statistics."""
    team_games = team_stats[
        (team_stats['team_id'] == team_id) &
        (pd.to_datetime(team_stats['game_date']) < before_date) &
        (team_stats['location'] == location)
    ].copy()

    team_games = team_games.sort_values('game_date', ascending=False).head(window)

    if len(team_games) == 0:
        return {f'{location}_games': 0}

    return {
        f'ppg_{location}_l{window}': float(team_games['points'].mean()),
        f'{location}_games': len(team_games)
    }


def calculate_recent_form(
    games: pd.DataFrame,
    team_id: int,
    before_date: datetime,
    window: int = 5
) -> float:
    """Calculate recent win percentage."""
    recent_games = games[
        (pd.to_datetime(games['game_date']) < before_date) &
        ((games['home_team_id'] == team_id) | (games['away_team_id'] == team_id))
    ].copy()

    recent_games = recent_games.sort_values('game_date', ascending=False).head(window)

    if len(recent_games) == 0:
        return 0.5

    wins = sum(
        1 if (row['home_team_id'] == team_id and row['home_team_is_winner']) or
             (row['away_team_id'] == team_id and not row['home_team_is_winner'])
        else 0
        for _, row in recent_games.iterrows()
    )

    return wins / len(recent_games)


def calculate_head_to_head(
    games: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    before_date: datetime,
    window: int = 5
) -> Dict[str, float]:
    """Calculate head-to-head history."""
    h2h_games = games[
        (pd.to_datetime(games['game_date']) < before_date) &
        (
            ((games['home_team_id'] == home_team_id) & (games['away_team_id'] == away_team_id)) |
            ((games['home_team_id'] == away_team_id) & (games['away_team_id'] == home_team_id))
        )
    ].copy()

    h2h_games = h2h_games.sort_values('game_date', ascending=False).head(window)

    if len(h2h_games) == 0:
        return {'h2h_home_wins': 0, 'h2h_games': 0, 'h2h_home_win_pct': 0.5}

    home_wins = sum(
        1 if (row['home_team_id'] == home_team_id and row['home_team_is_winner']) or
             (row['away_team_id'] == home_team_id and not row['home_team_is_winner'])
        else 0
        for _, row in h2h_games.iterrows()
    )

    return {
        'h2h_home_wins': home_wins,
        'h2h_games': len(h2h_games),
        'h2h_home_win_pct': home_wins / len(h2h_games)
    }


def calculate_rest_days(
    games: pd.DataFrame,
    team_id: int,
    game_date: datetime
) -> int:
    """Calculate days of rest since last game."""
    previous_games = games[
        (pd.to_datetime(games['game_date']) < game_date) &
        ((games['home_team_id'] == team_id) | (games['away_team_id'] == team_id))
    ].copy()

    previous_games = previous_games.sort_values('game_date', ascending=False)

    if len(previous_games) == 0:
        return 7

    last_game_date = pd.to_datetime(previous_games.iloc[0]['game_date'])
    return (game_date - last_game_date).days


def calculate_season_progress(
    games: pd.DataFrame,
    team_id: int,
    before_date: datetime
) -> float:
    """Calculate season completion percentage."""
    team_games = games[
        (pd.to_datetime(games['game_date']) < before_date) &
        ((games['home_team_id'] == team_id) | (games['away_team_id'] == team_id))
    ]

    games_played = len(team_games)
    return min(games_played / 82.0, 1.0)


def extract_features_for_game(
    game: pd.Series,
    all_games: pd.DataFrame,
    all_team_stats: pd.DataFrame
) -> Dict:
    """Extract all features for a single game."""
    game_date = pd.to_datetime(game['game_date'])
    home_team = game['home_team_id']
    away_team = game['away_team_id']

    features = {
        'game_id': game['game_id'],
        'game_date': str(game_date.date()),
        'season': game['season'],
        'home_team_id': home_team,
        'away_team_id': away_team,
        'home_win': 1 if game['home_team_is_winner'] else 0,
        'home_score': game['home_score'],
        'away_score': game['away_score']
    }

    # Rolling stats for different windows
    for window in [5, 10, 20]:
        home_stats = calculate_rolling_stats(all_team_stats, home_team, game_date, window)
        for key, val in home_stats.items():
            features[f'home_{key}'] = val

        away_stats = calculate_rolling_stats(all_team_stats, away_team, game_date, window)
        for key, val in away_stats.items():
            features[f'away_{key}'] = val

    # Location splits
    home_at_home = calculate_location_split(all_team_stats, home_team, game_date, 'home', 20)
    for key, val in home_at_home.items():
        features[f'home_{key}'] = val

    away_on_road = calculate_location_split(all_team_stats, away_team, game_date, 'away', 20)
    for key, val in away_on_road.items():
        features[f'away_{key}'] = val

    # Recent form
    features['home_form_l5'] = calculate_recent_form(all_games, home_team, game_date, 5)
    features['away_form_l5'] = calculate_recent_form(all_games, away_team, game_date, 5)

    # Head to head
    h2h = calculate_head_to_head(all_games, home_team, away_team, game_date, 5)
    features.update(h2h)

    # Rest days
    features['home_rest_days'] = calculate_rest_days(all_games, home_team, game_date)
    features['away_rest_days'] = calculate_rest_days(all_games, away_team, game_date)

    # Back-to-back indicators
    features['home_back_to_back'] = 1 if features['home_rest_days'] <= 1 else 0
    features['away_back_to_back'] = 1 if features['away_rest_days'] <= 1 else 0

    # Season progress
    features['home_season_progress'] = calculate_season_progress(all_games, home_team, game_date)
    features['away_season_progress'] = calculate_season_progress(all_games, away_team, game_date)

    return features


def process_features(min_games: int = 10) -> pd.DataFrame:
    """Process features from loaded MCP data."""
    print("Loading data from MCP results...")
    all_games = load_games_data()
    all_team_stats = load_team_stats_data()

    print(f"Loaded {len(all_games)} games and {len(all_team_stats)} team stat records")

    all_games['game_date'] = pd.to_datetime(all_games['game_date'])
    all_team_stats['game_date'] = pd.to_datetime(all_team_stats['game_date'])

    features_list = []

    print("Extracting features for each game...")
    for idx, (_, game) in enumerate(tqdm(all_games.iterrows(), total=len(all_games))):
        try:
            game_features = extract_features_for_game(game, all_games, all_team_stats)

            # Only include if both teams have played minimum games
            home_games = game_features.get('home_games_played', 0)
            away_games = game_features.get('away_games_played', 0)

            if home_games >= min_games and away_games >= min_games:
                features_list.append(game_features)

        except Exception as e:
            print(f"Error processing game {game.get('game_id', 'unknown')}: {e}")
            continue

    print(f"Successfully extracted features for {len(features_list)} games")
    return pd.DataFrame(features_list)


if __name__ == '__main__':
    print("This script requires MCP query results to be populated.")
    print("It should be run through Claude Code with MCP integration.")
    print("\nFor standalone use, populate MCP_QUERY_RESULTS dict with:")
    print("  - 'games': DataFrame with games table")
    print("  - 'team_stats': DataFrame with team_game_stats + location info")
