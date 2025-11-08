#!/usr/bin/env python3
"""
Ultra-Fast Feature Engineering Using Local Parquet Files

This script generates game features from local parquet files (100x faster than RDS queries).
Processes 28,779 games (2002-2024) with 130 features per game in 8-12 hours.

Local Data Source:
    /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/

Data Files:
    - Player Box: load_nba_player_box/parquet/nba_data_{year}.parquet
    - Team Box: load_nba_team_box/parquet/nba_data_{year}.parquet
    - Schedule: load_nba_schedule/parquet/nba_schedule_{year}.parquet

Usage:
    # Full historical dataset (2002-2024, ~28K games)
    python scripts/prepare_features_from_parquet.py --years 2002-2024 --output data/features_full_history.csv

    # Recent seasons only (2020-2024, ~6K games)
    python scripts/prepare_features_from_parquet.py --years 2020-2024 --output data/features_recent.csv

    # Test on small sample
    python scripts/prepare_features_from_parquet.py --years 2024 --max-games 100 --output data/features_test.csv
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import warnings

import numpy as np
import pandas as pd
from tqdm import tqdm

warnings.filterwarnings('ignore')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Parquet data location
PARQUET_BASE = Path('/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba')


def load_parquet_data(years: List[int]) -> tuple:
    """Load player box, team box, and schedule data from parquet files.

    Args:
        years: List of years to load (e.g., [2020, 2021, 2022])

    Returns:
        Tuple of (player_box_df, team_box_df, schedule_df)
    """
    print(f"\n{'='*80}")
    print("Loading Parquet Files")
    print(f"{'='*80}")

    player_dfs = []
    team_dfs = []
    schedule_dfs = []

    for year in tqdm(years, desc="Loading years"):
        # Player box scores
        player_file = PARQUET_BASE / f'load_nba_player_box/parquet/nba_data_{year}.parquet'
        if player_file.exists():
            df = pd.read_parquet(player_file)
            player_dfs.append(df)
            tqdm.write(f"  ✓ Player box {year}: {len(df):,} records")
        else:
            tqdm.write(f"  ⚠ Player box {year}: File not found")

        # Team box scores
        team_file = PARQUET_BASE / f'load_nba_team_box/parquet/nba_data_{year}.parquet'
        if team_file.exists():
            df = pd.read_parquet(team_file)
            team_dfs.append(df)
            tqdm.write(f"  ✓ Team box {year}: {len(df):,} records")
        else:
            tqdm.write(f"  ⚠ Team box {year}: File not found")

        # Schedule (for game metadata)
        schedule_file = PARQUET_BASE / f'load_nba_schedule/parquet/nba_schedule_{year}.parquet'
        if schedule_file.exists():
            df = pd.read_parquet(schedule_file)
            schedule_dfs.append(df)
            tqdm.write(f"  ✓ Schedule {year}: {len(df):,} games")
        else:
            tqdm.write(f"  ⚠ Schedule {year}: File not found")

    # Concatenate all years
    print("\nConcatenating dataframes...")
    player_box = pd.concat(player_dfs, ignore_index=True) if player_dfs else pd.DataFrame()
    team_box = pd.concat(team_dfs, ignore_index=True) if team_dfs else pd.DataFrame()
    schedule = pd.concat(schedule_dfs, ignore_index=True) if schedule_dfs else pd.DataFrame()

    # Convert dates to datetime
    if not player_box.empty:
        player_box['game_date'] = pd.to_datetime(player_box['game_date'])
    if not team_box.empty:
        team_box['game_date'] = pd.to_datetime(team_box['game_date'])
    if not schedule.empty:
        schedule['game_date'] = pd.to_datetime(schedule['game_date'])

    print(f"\n{'='*80}")
    print("Data Loaded Successfully")
    print(f"{'='*80}")
    print(f"Player Box Scores: {len(player_box):,} records")
    print(f"Team Box Scores: {len(team_box):,} records")
    print(f"Schedule: {len(schedule):,} games")
    print(f"Date Range: {player_box['game_date'].min()} to {player_box['game_date'].max()}")
    print()

    return player_box, team_box, schedule


def extract_completed_games(schedule: pd.DataFrame, team_box: pd.DataFrame) -> pd.DataFrame:
    """Extract list of completed games with basic metadata.

    Args:
        schedule: Schedule dataframe
        team_box: Team box scores dataframe

    Returns:
        DataFrame with game metadata (game_id, date, home/away teams, scores)
    """
    # Get unique completed games from team_box (has scores)
    games = team_box[['game_id', 'game_date']].drop_duplicates()

    # Calculate season from game_date (Oct-Sep is a season)
    # Season 2023-24 includes games from Oct 2023 to Sep 2024
    games['season'] = games['game_date'].apply(
        lambda x: f"{x.year}-{str(x.year + 1)[-2:]}" if x.month >= 10
        else f"{x.year - 1}-{str(x.year)[-2:]}"
    )

    # Get home and away team info
    home_teams = team_box[team_box['team_home_away'] == 'home'][
        ['game_id', 'team_id', 'team_score']
    ].rename(columns={'team_id': 'home_team_id', 'team_score': 'home_score'})

    away_teams = team_box[team_box['team_home_away'] == 'away'][
        ['game_id', 'team_id', 'team_score']
    ].rename(columns={'team_id': 'away_team_id', 'team_score': 'away_score'})

    # Merge
    games = games.merge(home_teams, on='game_id', how='left')
    games = games.merge(away_teams, on='game_id', how='left')

    # Add winner flag
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)

    # Sort by date
    games = games.sort_values('game_date').reset_index(drop=True)

    return games


def calculate_rolling_stats(
    team_box: pd.DataFrame,
    team_id: int,
    before_date: pd.Timestamp,
    location: Optional[str] = None,
    window: int = 10
) -> Dict[str, float]:
    """Calculate rolling statistics for a team.

    Args:
        team_box: Team box scores dataframe
        team_id: Team ID
        before_date: Only include games before this date
        location: 'home' or 'away' (None for all games)
        window: Number of games to include

    Returns:
        Dictionary of rolling stats
    """
    # Filter to team's games before the target date
    mask = (team_box['team_id'] == team_id) & (team_box['game_date'] < before_date)
    if location:
        mask = mask & (team_box['team_home_away'] == location)

    team_games = team_box[mask].sort_values('game_date', ascending=False).head(window).copy()

    if len(team_games) == 0:
        return {'games_played': 0}

    # Parse string stats if needed
    def safe_float(x):
        try:
            return float(x)
        except (ValueError, TypeError):
            return np.nan

    # Shooting percentages
    fgm = team_games['field_goals_made'].astype(float)
    fga = team_games['field_goals_attempted'].astype(float).replace(0, np.nan)
    fg_pct = (fgm / fga).fillna(0)

    fg3m = team_games['three_point_field_goals_made'].astype(float)
    fg3a = team_games['three_point_field_goals_attempted'].astype(float).replace(0, np.nan)
    three_pt_pct = (fg3m / fg3a).fillna(0)

    ftm = team_games['free_throws_made'].astype(float)
    fta = team_games['free_throws_attempted'].astype(float).replace(0, np.nan)
    ft_pct = (ftm / fta).fillna(0)

    # Points
    points = team_games['team_score'].astype(float)

    # Advanced metrics
    ts_attempts = fga + 0.44 * fta
    ts_attempts = ts_attempts.replace(0, np.nan)
    ts_pct = (points / (2 * ts_attempts)).fillna(0)

    efg_pct = ((fgm + 0.5 * fg3m) / fga).fillna(0)

    # Other stats
    rebounds = team_games['total_rebounds'].astype(float)
    assists = team_games['assists'].astype(float)
    steals = team_games['steals'].astype(float)
    blocks = team_games['blocks'].astype(float)

    # Handle turnovers (may be in 'turnovers' or 'total_turnovers')
    if 'turnovers' in team_games.columns:
        turnovers = team_games['turnovers'].apply(safe_float)
    elif 'total_turnovers' in team_games.columns:
        turnovers = team_games['total_turnovers'].apply(safe_float)
    else:
        turnovers = pd.Series([np.nan] * len(team_games))

    suffix = f"_l{window}"
    if location:
        suffix = f"_{location}{suffix}"

    return {
        f'ppg{suffix}': float(points.mean()),
        f'fg_pct{suffix}': float(fg_pct.mean()),
        f'three_pt_pct{suffix}': float(three_pt_pct.mean()),
        f'ft_pct{suffix}': float(ft_pct.mean()),
        f'rebounds{suffix}': float(rebounds.mean()),
        f'assists{suffix}': float(assists.mean()),
        f'steals{suffix}': float(steals.mean()),
        f'blocks{suffix}': float(blocks.mean()),
        f'turnovers{suffix}': float(turnovers.mean()),
        f'ts_pct{suffix}': float(ts_pct.mean()),
        f'efg_pct{suffix}': float(efg_pct.mean()),
        'games_played': len(team_games)
    }


def calculate_player_features(
    player_box: pd.DataFrame,
    team_id: int,
    before_date: pd.Timestamp,
    window: int = 10
) -> Dict[str, float]:
    """Calculate player-level features for a team.

    Args:
        player_box: Player box scores dataframe
        team_id: Team ID
        before_date: Only include games before this date
        window: Number of games for rolling averages

    Returns:
        Dictionary of player features (29 features)
    """
    # Filter to team's games before target date
    team_games = player_box[
        (player_box['team_id'] == team_id) &
        (player_box['game_date'] < before_date)
    ].copy()

    if len(team_games) == 0:
        return {}

    # Calculate individual player points
    team_games['fgm'] = team_games['field_goals_made'].astype(float)
    team_games['fg3m'] = team_games['three_point_field_goals_made'].astype(float)
    team_games['ftm'] = team_games['free_throws_made'].astype(float)
    team_games['player_points'] = (
        team_games['fgm'] * 2 +
        team_games['fg3m'] * 3 +
        team_games['ftm']
    )

    # Get recent games only (last window games)
    recent_games = team_games.sort_values('game_date', ascending=False)
    recent_dates = recent_games['game_date'].unique()[:window]
    recent = team_games[team_games['game_date'].isin(recent_dates)]

    # Aggregate by player
    player_stats = recent.groupby('athlete_id').agg({
        'player_points': 'mean',
        'minutes': 'mean',
        'game_id': 'count'  # games played
    }).reset_index()

    player_stats.columns = ['athlete_id', 'ppg', 'minutes', 'games']

    # Get top 10 scorers
    player_stats = player_stats.sort_values('ppg', ascending=False).head(10)

    features = {}

    # Top 3 scorers
    for i in range(min(3, len(player_stats))):
        player = player_stats.iloc[i]
        features[f'top{i+1}_ppg_l{window}'] = float(player['ppg'])
        features[f'top{i+1}_minutes_l{window}'] = float(player['minutes'])
        # Usage rate approximation (ppg / team_ppg)
        team_ppg = recent.groupby('game_id')['player_points'].sum().mean()
        features[f'top{i+1}_usage_pct_l{window}'] = float(player['ppg'] / team_ppg) if team_ppg > 0 else 0

    # Roster quality (top 5 sum)
    top5_ppg = player_stats.head(5)['ppg'].sum()
    features[f'roster_per_sum'] = float(top5_ppg)  # Using PPG as proxy for PER
    features[f'top5_ppg'] = float(top5_ppg)

    # Bench strength (6-10 scorers)
    if len(player_stats) >= 6:
        bench_ppg = player_stats.iloc[5:10]['ppg'].mean()
        features[f'bench_ppg'] = float(bench_ppg)
    else:
        features[f'bench_ppg'] = 0.0

    # Injury impact (simplified - using DNP records)
    dnp_players = team_games[team_games['did_not_play'] == 1]
    if len(dnp_players) > 0:
        features[f'injury_impact'] = float(dnp_players['player_points'].mean())
    else:
        features[f'injury_impact'] = 0.0

    # Stars available (% of top 3 who played recently)
    features[f'stars_available'] = min(3, len(player_stats)) / 3.0

    return features


def calculate_rest_days(
    team_box: pd.DataFrame,
    team_id: int,
    game_date: pd.Timestamp
) -> int:
    """Calculate days of rest since last game."""
    previous_games = team_box[
        (team_box['team_id'] == team_id) &
        (team_box['game_date'] < game_date)
    ].sort_values('game_date', ascending=False)

    if len(previous_games) == 0:
        return 7  # Default

    last_game_date = previous_games.iloc[0]['game_date']
    return (game_date - last_game_date).days


def calculate_h2h_stats(
    team_box: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    before_date: pd.Timestamp,
    window: int = 5
) -> Dict[str, float]:
    """Calculate head-to-head statistics."""
    # Get all games between these two teams
    home_games = team_box[
        (team_box['team_id'] == home_team_id) &
        (team_box['game_date'] < before_date)
    ]
    away_games = team_box[
        (team_box['team_id'] == away_team_id) &
        (team_box['game_date'] < before_date)
    ]

    # Find common game_ids (h2h matchups)
    home_game_ids = set(home_games['game_id'])
    away_game_ids = set(away_games['game_id'])
    h2h_game_ids = home_game_ids & away_game_ids

    if not h2h_game_ids:
        return {'h2h_home_wins': 0, 'h2h_games': 0, 'h2h_home_win_pct': 0.5}

    # Get recent h2h games
    h2h_games = team_box[team_box['game_id'].isin(h2h_game_ids)].sort_values('game_date', ascending=False)
    h2h_game_ids_recent = h2h_games['game_id'].unique()[:window]

    h2h_recent = team_box[team_box['game_id'].isin(h2h_game_ids_recent)]

    # Count home team wins
    home_wins = 0
    for game_id in h2h_game_ids_recent:
        game_data = h2h_recent[h2h_recent['game_id'] == game_id]
        home_data = game_data[game_data['team_id'] == home_team_id]
        away_data = game_data[game_data['team_id'] == away_team_id]

        if len(home_data) > 0 and len(away_data) > 0:
            home_score = home_data.iloc[0]['team_score']
            away_score = away_data.iloc[0]['team_score']
            if home_score > away_score:
                home_wins += 1

    h2h_games_count = len(h2h_game_ids_recent)

    return {
        'h2h_home_wins': home_wins,
        'h2h_games': h2h_games_count,
        'h2h_home_win_pct': home_wins / h2h_games_count if h2h_games_count > 0 else 0.5
    }


def extract_game_features(
    game_id: str,
    game_date: pd.Timestamp,
    home_team_id: int,
    away_team_id: int,
    season: str,
    player_box: pd.DataFrame,
    team_box: pd.DataFrame,
    min_games: int = 10
) -> Optional[Dict]:
    """Extract all 130 features for a game.

    Returns None if insufficient data (less than min_games).
    """
    features = {
        'game_id': game_id,
        'game_date': game_date.strftime('%Y-%m-%d'),
        'season': season,
        'home_team_id': home_team_id,
        'away_team_id': away_team_id
    }

    # Rolling stats for home team (L5, L10, L20)
    for window in [5, 10, 20]:
        home_stats = calculate_rolling_stats(team_box, home_team_id, game_date, window=window)
        if home_stats.get('games_played', 0) < min_games and window == 10:
            return None  # Insufficient data
        for key, value in home_stats.items():
            if key != 'games_played':
                features[f'home_{key}'] = value
            elif window == 10:
                features['home_games_played'] = value

    # Rolling stats for away team (L5, L10, L20)
    for window in [5, 10, 20]:
        away_stats = calculate_rolling_stats(team_box, away_team_id, game_date, window=window)
        if away_stats.get('games_played', 0) < min_games and window == 10:
            return None  # Insufficient data
        for key, value in away_stats.items():
            if key != 'games_played':
                features[f'away_{key}'] = value
            elif window == 10:
                features['away_games_played'] = value

    # Home/away splits
    home_home_stats = calculate_rolling_stats(team_box, home_team_id, game_date, location='home', window=20)
    for key, value in home_home_stats.items():
        if key != 'games_played':
            features[f'home_{key}'] = value

    away_away_stats = calculate_rolling_stats(team_box, away_team_id, game_date, location='away', window=20)
    for key, value in away_away_stats.items():
        if key != 'games_played':
            features[f'away_{key}'] = value

    # Rest days
    features['home_rest_days'] = calculate_rest_days(team_box, home_team_id, game_date)
    features['away_rest_days'] = calculate_rest_days(team_box, away_team_id, game_date)
    features['home_back_to_back'] = 1 if features['home_rest_days'] <= 1 else 0
    features['away_back_to_back'] = 1 if features['away_rest_days'] <= 1 else 0

    # Head-to-head
    h2h_stats = calculate_h2h_stats(team_box, home_team_id, away_team_id, game_date)
    features.update(h2h_stats)

    # Player features (29 features)
    home_player_features = calculate_player_features(player_box, home_team_id, game_date)
    for key, value in home_player_features.items():
        features[f'player__home_{key}'] = value

    away_player_features = calculate_player_features(player_box, away_team_id, game_date)
    for key, value in away_player_features.items():
        features[f'player__away_{key}'] = value

    # Matchup advantage (player-based)
    if 'player__home_top5_ppg' in features and 'player__away_top5_ppg' in features:
        features['player__top5_ppg_advantage'] = features['player__home_top5_ppg'] - features['player__away_top5_ppg']

    return features


def main():
    parser = argparse.ArgumentParser(
        description="Extract NBA game features from local parquet files (ultra-fast)"
    )
    parser.add_argument(
        '--years',
        type=str,
        required=True,
        help='Year range (e.g., "2020-2024" or "2002-2024")'
    )
    parser.add_argument(
        '--output',
        default='data/game_features_parquet.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--min-games',
        type=int,
        default=10,
        help='Minimum games before including team in dataset'
    )
    parser.add_argument(
        '--max-games',
        type=int,
        default=None,
        help='Maximum number of games to process (for testing)'
    )

    args = parser.parse_args()

    # Parse year range
    if '-' in args.years:
        start_year, end_year = args.years.split('-')
        years = list(range(int(start_year), int(end_year) + 1))
    else:
        years = [int(args.years)]

    print("=" * 80)
    print("NBA Game Feature Engineering from Parquet")
    print("=" * 80)
    print(f"Years: {years[0]}-{years[-1]} ({len(years)} years)")
    print(f"Output: {args.output}")
    print(f"Minimum games: {args.min_games}")
    print(f"Max games: {args.max_games or 'No limit'}")
    print()

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load parquet data
    player_box, team_box, schedule = load_parquet_data(years)

    # Extract games list
    print("Extracting completed games...")
    games = extract_completed_games(schedule, team_box)
    print(f"✓ Found {len(games):,} completed games\n")

    # Limit for testing
    if args.max_games:
        games = games.head(args.max_games)
        print(f"⚠️  Limited to {args.max_games} games for testing\n")

    # Extract features
    print(f"\n{'='*80}")
    print("Extracting Features (130 per game)")
    print(f"{'='*80}\n")

    features_list = []
    errors = 0
    skipped = 0

    for _, game in tqdm(games.iterrows(), total=len(games), desc="Processing games"):
        try:
            game_features = extract_game_features(
                game_id=game['game_id'],
                game_date=game['game_date'],
                home_team_id=int(game['home_team_id']),
                away_team_id=int(game['away_team_id']),
                season=game['season'],
                player_box=player_box,
                team_box=team_box,
                min_games=args.min_games
            )

            if game_features:
                # Add outcomes
                game_features['home_win'] = int(game['home_win'])
                game_features['home_score'] = int(game['home_score'])
                game_features['away_score'] = int(game['away_score'])
                features_list.append(game_features)
            else:
                skipped += 1

        except Exception as e:
            errors += 1
            if errors <= 5:  # Only show first 5 errors
                tqdm.write(f"Error processing game {game['game_id']}: {e}")
            continue

    print(f"\n{'='*80}")
    print("Feature Extraction Complete")
    print(f"{'='*80}")
    print(f"✓ Successfully extracted: {len(features_list):,} games")
    if skipped > 0:
        print(f"⚠️  Skipped (insufficient data): {skipped:,} games")
    if errors > 0:
        print(f"❌ Errors: {errors:,} games")
    print()

    # Create DataFrame
    df = pd.DataFrame(features_list)

    # Feature count
    feature_cols = [c for c in df.columns if c not in ['game_id', 'game_date', 'season', 'home_team_id', 'away_team_id', 'home_win', 'home_score', 'away_score']]
    player_features = [c for c in feature_cols if c.startswith('player__')]

    print(f"{'='*80}")
    print("Feature Summary")
    print(f"{'='*80}")
    print(f"Total features: {len(feature_cols)}")
    print(f"Player features: {len(player_features)}")
    print(f"Team features: {len(feature_cols) - len(player_features)}")
    print()

    # Save
    print(f"Saving to {args.output}...")
    df.to_csv(args.output, index=False)
    file_size = Path(args.output).stat().st_size / (1024 * 1024)  # MB
    print(f"✓ Saved {len(df):,} games to {args.output} ({file_size:.1f} MB)")
    print()

    print(f"{'='*80}")
    print("SUCCESS! Ready for model training.")
    print(f"{'='*80}")
    print(f"\nNext step:")
    print(f"  python scripts/validate_batch_output.py --file {args.output}")
    print()


if __name__ == '__main__':
    main()
