#!/usr/bin/env python3
"""
Feature Engineering Pipeline for NBA Game Outcome Prediction

Extracts rich features from historical NBA games for training the Kelly Criterion
calibrator. Uses rolling statistics, performance splits, and situational factors.

Usage:
    python scripts/prepare_game_features.py --seasons 2021-22 2022-23 2023-24 2024-25
    python scripts/prepare_game_features.py --output data/game_features.csv
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

import numpy as np
import pandas as pd
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def query_mcp_database(sql: str) -> pd.DataFrame:
    """
    Query the NBA MCP database via the MCP tools.

    For now, this is a placeholder - the actual implementation will use
    the mcp__nba-mcp-server__query_database tool through Claude Code's MCP integration.

    In practice, you'll need to run this script through Claude Code which has access
    to the MCP server, or adapt it to use direct PostgreSQL connection.
    """
    # This will be replaced with actual MCP calls when run through Claude Code
    raise NotImplementedError(
        "This script must be run through Claude Code with MCP server access, "
        "or adapted to use direct database connection"
    )


def get_games_for_seasons(seasons: List[str]) -> pd.DataFrame:
    """Fetch all completed games for specified seasons."""
    seasons_str = "', '".join(seasons)
    query = f"""
    SELECT
        game_id,
        game_date,
        season,
        home_team_id,
        away_team_id,
        home_score,
        away_score,
        home_team_is_winner,
        completed
    FROM games
    WHERE completed = true
    AND season IN ('{seasons_str}')
    ORDER BY game_date, game_id
    """
    return query_mcp_database(query)


def get_team_game_stats(seasons: List[str]) -> pd.DataFrame:
    """Fetch detailed team game statistics."""
    seasons_str = "', '".join(seasons)
    query = f"""
    SELECT
        tgs.game_id,
        g.game_date,
        g.season,
        tgs.team_id,
        CASE WHEN tgs.team_id = g.home_team_id THEN 'home' ELSE 'away' END as location,
        tgs.points,
        tgs.field_goals_made,
        tgs.field_goals_attempted,
        tgs.three_pointers_made,
        tgs.three_pointers_attempted,
        tgs.free_throws_made,
        tgs.free_throws_attempted,
        tgs.offensive_rebounds,
        tgs.defensive_rebounds,
        tgs.assists,
        tgs.steals,
        tgs.blocks,
        tgs.turnovers,
        tgs.personal_fouls
    FROM team_game_stats tgs
    JOIN games g ON tgs.game_id = g.game_id
    WHERE g.completed = true
    AND g.season IN ('{seasons_str}')
    ORDER BY g.game_date, tgs.game_id
    """
    return query_mcp_database(query)


def calculate_rolling_stats(
    team_stats: pd.DataFrame,
    team_id: int,
    before_date: datetime,
    window: int = 10
) -> Dict[str, float]:
    """
    Calculate rolling statistics for a team based on their last N games before a given date.

    Args:
        team_stats: DataFrame with all team game statistics
        team_id: Team to calculate stats for
        before_date: Calculate stats using only games before this date
        window: Number of recent games to include (default: 10)

    Returns:
        Dictionary of rolling statistics
    """
    # Filter to team's games before the date
    team_games = team_stats[
        (team_stats['team_id'] == team_id) &
        (team_stats['game_date'] < before_date)
    ].sort_values('game_date', ascending=False).head(window)

    if len(team_games) == 0:
        return {}

    # Calculate advanced metrics
    team_games = team_games.copy()
    team_games['fg_pct'] = team_games['field_goals_made'] / team_games['field_goals_attempted'].replace(0, np.nan)
    team_games['three_pt_pct'] = team_games['three_pointers_made'] / team_games['three_pointers_attempted'].replace(0, np.nan)
    team_games['ft_pct'] = team_games['free_throws_made'] / team_games['free_throws_attempted'].replace(0, np.nan)
    team_games['total_rebounds'] = team_games['offensive_rebounds'] + team_games['defensive_rebounds']

    # Calculate true shooting % and effective FG%
    team_games['ts_pct'] = team_games['points'] / (
        2 * (team_games['field_goals_attempted'] + 0.44 * team_games['free_throws_attempted'])
    ).replace(0, np.nan)
    team_games['efg_pct'] = (
        team_games['field_goals_made'] + 0.5 * team_games['three_pointers_made']
    ) / team_games['field_goals_attempted'].replace(0, np.nan)

    # Rolling averages
    stats = {
        f'ppg_l{window}': team_games['points'].mean(),
        f'fg_pct_l{window}': team_games['fg_pct'].mean(),
        f'three_pt_pct_l{window}': team_games['three_pt_pct'].mean(),
        f'ft_pct_l{window}': team_games['ft_pct'].mean(),
        f'rebounds_l{window}': team_games['total_rebounds'].mean(),
        f'assists_l{window}': team_games['assists'].mean(),
        f'steals_l{window}': team_games['steals'].mean(),
        f'blocks_l{window}': team_games['blocks'].mean(),
        f'turnovers_l{window}': team_games['turnovers'].mean(),
        f'ts_pct_l{window}': team_games['ts_pct'].mean(),
        f'efg_pct_l{window}': team_games['efg_pct'].mean(),
        f'games_played': len(team_games)
    }

    return stats


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
        (team_stats['game_date'] < before_date) &
        (team_stats['location'] == location)
    ].sort_values('game_date', ascending=False).head(window)

    if len(team_games) == 0:
        return {}

    return {
        f'ppg_{location}_l{window}': team_games['points'].mean(),
        f'{location}_games': len(team_games)
    }


def calculate_recent_form(
    games: pd.DataFrame,
    team_id: int,
    before_date: datetime,
    window: int = 5
) -> float:
    """Calculate recent win percentage (last N games)."""
    recent_games = games[
        (games['game_date'] < before_date) &
        ((games['home_team_id'] == team_id) | (games['away_team_id'] == team_id))
    ].sort_values('game_date', ascending=False).head(window)

    if len(recent_games) == 0:
        return 0.0

    wins = 0
    for _, game in recent_games.iterrows():
        if game['home_team_id'] == team_id:
            wins += 1 if game['home_team_is_winner'] else 0
        else:
            wins += 0 if game['home_team_is_winner'] else 1

    return wins / len(recent_games)


def calculate_head_to_head(
    games: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    before_date: datetime,
    window: int = 5
) -> Dict[str, float]:
    """Calculate head-to-head history between two teams."""
    h2h_games = games[
        (games['game_date'] < before_date) &
        (
            ((games['home_team_id'] == home_team_id) & (games['away_team_id'] == away_team_id)) |
            ((games['home_team_id'] == away_team_id) & (games['away_team_id'] == home_team_id))
        )
    ].sort_values('game_date', ascending=False).head(window)

    if len(h2h_games) == 0:
        return {'h2h_home_wins': 0.0, 'h2h_games': 0}

    home_wins = 0
    for _, game in h2h_games.iterrows():
        if game['home_team_id'] == home_team_id:
            home_wins += 1 if game['home_team_is_winner'] else 0
        else:
            home_wins += 0 if game['home_team_is_winner'] else 1

    return {
        'h2h_home_wins': home_wins,
        'h2h_games': len(h2h_games),
        'h2h_home_win_pct': home_wins / len(h2h_games) if len(h2h_games) > 0 else 0.5
    }


def calculate_rest_days(
    games: pd.DataFrame,
    team_id: int,
    game_date: datetime
) -> int:
    """Calculate days of rest since last game."""
    previous_games = games[
        (games['game_date'] < game_date) &
        ((games['home_team_id'] == team_id) | (games['away_team_id'] == team_id))
    ].sort_values('game_date', ascending=False)

    if len(previous_games) == 0:
        return 7  # Default to 7 days if no previous game

    last_game_date = pd.to_datetime(previous_games.iloc[0]['game_date'])
    current_date = pd.to_datetime(game_date)
    return (current_date - last_game_date).days


def calculate_season_progress(
    games: pd.DataFrame,
    team_id: int,
    before_date: datetime
) -> float:
    """Calculate what percentage of season has been completed."""
    team_games = games[
        (games['game_date'] < before_date) &
        ((games['home_team_id'] == team_id) | (games['away_team_id'] == team_id))
    ]

    games_played = len(team_games)
    # NBA regular season is 82 games
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
        'game_date': game_date,
        'season': game['season'],
        'home_team_id': home_team,
        'away_team_id': away_team,
        'home_win': 1 if game['home_team_is_winner'] else 0,
        'home_score': game['home_score'],
        'away_score': game['away_score']
    }

    # Rolling stats for different windows
    for window in [5, 10, 20]:
        # Home team stats
        home_stats = calculate_rolling_stats(all_team_stats, home_team, game_date, window)
        for key, val in home_stats.items():
            features[f'home_{key}'] = val

        # Away team stats
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

    # Back-to-back indicator
    features['home_back_to_back'] = 1 if features['home_rest_days'] <= 1 else 0
    features['away_back_to_back'] = 1 if features['away_rest_days'] <= 1 else 0

    # Season progress
    features['home_season_progress'] = calculate_season_progress(all_games, home_team, game_date)
    features['away_season_progress'] = calculate_season_progress(all_games, away_team, game_date)

    return features


def prepare_features(seasons: List[str], min_games: int = 10) -> pd.DataFrame:
    """
    Main feature engineering pipeline.

    Args:
        seasons: List of seasons to process (e.g., ['2021-22', '2022-23'])
        min_games: Minimum games played before including in dataset

    Returns:
        DataFrame with engineered features
    """
    print(f"Fetching games for seasons: {seasons}")
    all_games = get_games_for_seasons(seasons)
    print(f"Found {len(all_games)} completed games")

    print("Fetching team game statistics...")
    all_team_stats = get_team_game_stats(seasons)
    print(f"Found {len(all_team_stats)} team game stat records")

    # Convert date columns
    all_games['game_date'] = pd.to_datetime(all_games['game_date'])
    all_team_stats['game_date'] = pd.to_datetime(all_team_stats['game_date'])

    features_list = []

    print("Extracting features for each game...")
    for idx, game in tqdm(all_games.iterrows(), total=len(all_games)):
        try:
            game_features = extract_features_for_game(game, all_games, all_team_stats)

            # Only include if both teams have played minimum games
            home_games = game_features.get('home_games_played', 0)
            away_games = game_features.get('away_games_played', 0)

            if home_games >= min_games and away_games >= min_games:
                features_list.append(game_features)
        except Exception as e:
            print(f"Error processing game {game['game_id']}: {e}")
            continue

    print(f"Successfully extracted features for {len(features_list)} games")

    df = pd.DataFrame(features_list)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Extract features from NBA historical games for Kelly Criterion calibration"
    )
    parser.add_argument(
        '--seasons',
        nargs='+',
        default=['2021-22', '2022-23', '2023-24', '2024-25'],
        help='Seasons to process (e.g., 2021-22 2022-23)'
    )
    parser.add_argument(
        '--output',
        default='data/game_features.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--min-games',
        type=int,
        default=10,
        help='Minimum games played before including team in dataset'
    )

    args = parser.parse_args()

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("NBA Game Feature Engineering Pipeline")
    print("=" * 80)
    print(f"Seasons: {args.seasons}")
    print(f"Output: {args.output}")
    print(f"Minimum games: {args.min_games}")
    print()

    # Extract features
    features_df = prepare_features(args.seasons, args.min_games)

    # Save to CSV
    print(f"Saving features to {args.output}")
    features_df.to_csv(args.output, index=False)

    print()
    print("=" * 80)
    print("Feature Engineering Complete!")
    print("=" * 80)
    print(f"Total games: {len(features_df)}")
    print(f"Total features: {len(features_df.columns)}")
    print(f"Date range: {features_df['game_date'].min()} to {features_df['game_date'].max()}")
    print()
    print("Feature columns:")
    for col in sorted(features_df.columns):
        print(f"  - {col}")
    print()
    print(f"Sample distribution:")
    print(features_df['season'].value_counts().sort_index())
    print()
    print("Next step: Run scripts/train_game_outcome_model.py")


if __name__ == '__main__':
    main()
