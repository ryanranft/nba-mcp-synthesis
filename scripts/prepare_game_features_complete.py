#!/usr/bin/env python3
"""
Complete Feature Engineering Pipeline for NBA Game Predictions

This script extracts features from 4,621 historical NBA games (2021-22 through 2024-25)
and prepares them for training the Kelly Criterion calibrator.

Requirements:
    pip install pandas numpy tqdm psycopg2-binary

Database Credentials:
    This script uses the hierarchical secrets management system.
    Credentials are loaded from:
    /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/

    See .claude/claude.md for full configuration details.

Usage:
    python scripts/prepare_game_features_complete.py
    python scripts/prepare_game_features_complete.py --output data/features.csv --min-games 5
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import warnings

import numpy as np
import pandas as pd
from tqdm import tqdm

warnings.filterwarnings("ignore")

# Database connection
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("Warning: psycopg2 not installed. Install with: pip install psycopg2-binary")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)
from mcp_server.betting.feature_extractors.rest_fatigue import RestFatigueExtractor
from mcp_server.betting.feature_extractor import FeatureExtractor


def get_db_connection():
    """Create PostgreSQL database connection using hierarchical secrets."""
    if not HAS_PSYCOPG2:
        raise ImportError(
            "psycopg2 is required. Install with: pip install psycopg2-binary"
        )

    # Load secrets from hierarchical system
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")

    # Get database configuration
    db_config = get_database_config()

    # Validate all credentials loaded
    missing = [k for k, v in db_config.items() if not v]
    if missing:
        print(f"\n❌ ERROR: Missing database credentials: {missing}")
        print("Please ensure credentials are configured in:")
        print(
            "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/"
        )
        print(
            "\nSee .claude/claude.md or SECRETS_STRUCTURE.md for configuration details."
        )
        sys.exit(1)

    return psycopg2.connect(**db_config)


def fetch_games(conn, seasons: List[str]) -> pd.DataFrame:
    """Fetch all games for specified seasons."""
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
        CASE WHEN home_score > away_score THEN true ELSE false END as home_team_is_winner
    FROM games
    WHERE completed = true
    AND season IN ('{seasons_str}')
    ORDER BY game_date, game_id
    """

    print(f"Fetching games for seasons: {seasons}")
    df = pd.read_sql_query(query, conn)
    print(f"✓ Loaded {len(df)} games")
    return df


def fetch_team_stats(conn, seasons: List[str]) -> pd.DataFrame:
    """Fetch team game statistics with location info from hoopr_team_box."""
    seasons_str = "', '".join(seasons)
    query = f"""
    SELECT
        CAST(htb.game_id AS VARCHAR) as game_id,
        htb.game_date,
        CASE
            WHEN EXTRACT(MONTH FROM htb.game_date) >= 10
            THEN EXTRACT(YEAR FROM htb.game_date)::text || '-' ||
                 LPAD((EXTRACT(YEAR FROM htb.game_date) + 1 - 2000)::text, 2, '0')
            ELSE (EXTRACT(YEAR FROM htb.game_date) - 1)::text || '-' ||
                 LPAD((EXTRACT(YEAR FROM htb.game_date) - 2000)::text, 2, '0')
        END as season,
        CAST(htb.team_id AS VARCHAR) as team_id,
        htb.team_home_away as location,
        htb.team_score as points,
        htb.field_goals_made,
        htb.field_goals_attempted,
        htb.three_point_field_goals_made as three_pointers_made,
        htb.three_point_field_goals_attempted as three_pointers_attempted,
        htb.free_throws_made,
        htb.free_throws_attempted,
        htb.total_rebounds as rebounds,
        htb.assists,
        htb.steals,
        htb.blocks,
        COALESCE(htb.turnovers, htb.total_turnovers) as turnovers,
        htb.fouls as personal_fouls
    FROM hoopr_team_box htb
    WHERE htb.game_date >= '2021-10-01'
    AND CASE
            WHEN EXTRACT(MONTH FROM htb.game_date) >= 10
            THEN EXTRACT(YEAR FROM htb.game_date)::text || '-' ||
                 LPAD((EXTRACT(YEAR FROM htb.game_date) + 1 - 2000)::text, 2, '0')
            ELSE (EXTRACT(YEAR FROM htb.game_date) - 1)::text || '-' ||
                 LPAD((EXTRACT(YEAR FROM htb.game_date) - 2000)::text, 2, '0')
        END IN ('{seasons_str}')
    ORDER BY htb.game_date, htb.game_id
    """

    print(f"Fetching team statistics from hoopr_team_box...")
    df = pd.read_sql_query(query, conn)
    df["game_date"] = pd.to_datetime(df["game_date"])
    print(f"✓ Loaded {len(df)} team stat records")
    return df


def calculate_rolling_stats(
    team_stats: pd.DataFrame, team_id: str, before_date: datetime, window: int = 10
) -> Dict[str, float]:
    """Calculate rolling statistics for a team."""
    team_games = (
        team_stats[
            (team_stats["team_id"] == team_id) & (team_stats["game_date"] < before_date)
        ]
        .sort_values("game_date", ascending=False)
        .head(window)
        .copy()
    )

    if len(team_games) == 0:
        return {f"games_played": 0}

    # Avoid division by zero
    team_games["fga"] = team_games["field_goals_attempted"].replace(0, np.nan)
    team_games["3pa"] = team_games["three_pointers_attempted"].replace(0, np.nan)
    team_games["fta"] = team_games["free_throws_attempted"].replace(0, np.nan)

    # Shooting percentages
    team_games["fg_pct"] = team_games["field_goals_made"] / team_games["fga"]
    team_games["three_pt_pct"] = team_games["three_pointers_made"] / team_games["3pa"]
    team_games["ft_pct"] = team_games["free_throws_made"] / team_games["fta"]

    # Advanced metrics
    team_games["ts_pct"] = team_games["points"] / (
        2
        * (
            team_games["field_goals_attempted"]
            + 0.44 * team_games["free_throws_attempted"]
        )
    ).replace(0, np.nan)

    team_games["efg_pct"] = (
        team_games["field_goals_made"] + 0.5 * team_games["three_pointers_made"]
    ) / team_games["fga"]

    return {
        f"ppg_l{window}": float(team_games["points"].mean()),
        f"fg_pct_l{window}": float(team_games["fg_pct"].mean()),
        f"three_pt_pct_l{window}": float(team_games["three_pt_pct"].mean()),
        f"ft_pct_l{window}": float(team_games["ft_pct"].mean()),
        f"rebounds_l{window}": float(team_games["rebounds"].mean()),
        f"assists_l{window}": float(team_games["assists"].mean()),
        f"steals_l{window}": float(team_games["steals"].mean()),
        f"blocks_l{window}": float(team_games["blocks"].mean()),
        f"turnovers_l{window}": float(team_games["turnovers"].mean()),
        f"ts_pct_l{window}": float(team_games["ts_pct"].mean()),
        f"efg_pct_l{window}": float(team_games["efg_pct"].mean()),
        f"games_played": len(team_games),
    }


def calculate_location_split(
    team_stats: pd.DataFrame,
    team_id: str,
    before_date: datetime,
    location: str,
    window: int = 20,
) -> Dict[str, float]:
    """Calculate home/away split statistics."""
    team_games = (
        team_stats[
            (team_stats["team_id"] == team_id)
            & (team_stats["game_date"] < before_date)
            & (team_stats["location"] == location)
        ]
        .sort_values("game_date", ascending=False)
        .head(window)
    )

    if len(team_games) == 0:
        return {f"{location}_games": 0}

    return {
        f"ppg_{location}_l{window}": float(team_games["points"].mean()),
        f"{location}_games": len(team_games),
    }


def calculate_recent_form(
    games: pd.DataFrame, team_id: str, before_date: datetime, window: int = 5
) -> float:
    """Calculate recent win percentage."""
    recent_games = (
        games[
            (games["game_date"] < before_date)
            & ((games["home_team_id"] == team_id) | (games["away_team_id"] == team_id))
        ]
        .sort_values("game_date", ascending=False)
        .head(window)
    )

    if len(recent_games) == 0:
        return 0.5  # Default to 50%

    wins = sum(
        (
            1
            if (row["home_team_id"] == team_id and row["home_team_is_winner"])
            or (row["away_team_id"] == team_id and not row["home_team_is_winner"])
            else 0
        )
        for _, row in recent_games.iterrows()
    )

    return wins / len(recent_games)


def calculate_head_to_head(
    games: pd.DataFrame,
    home_team_id: str,
    away_team_id: str,
    before_date: datetime,
    window: int = 5,
) -> Dict[str, float]:
    """Calculate head-to-head history."""
    h2h_games = (
        games[
            (games["game_date"] < before_date)
            & (
                (
                    (games["home_team_id"] == home_team_id)
                    & (games["away_team_id"] == away_team_id)
                )
                | (
                    (games["home_team_id"] == away_team_id)
                    & (games["away_team_id"] == home_team_id)
                )
            )
        ]
        .sort_values("game_date", ascending=False)
        .head(window)
    )

    if len(h2h_games) == 0:
        return {"h2h_home_wins": 0, "h2h_games": 0, "h2h_home_win_pct": 0.5}

    home_wins = sum(
        (
            1
            if (row["home_team_id"] == home_team_id and row["home_team_is_winner"])
            or (row["away_team_id"] == home_team_id and not row["home_team_is_winner"])
            else 0
        )
        for _, row in h2h_games.iterrows()
    )

    return {
        "h2h_home_wins": home_wins,
        "h2h_games": len(h2h_games),
        "h2h_home_win_pct": home_wins / len(h2h_games),
    }


def calculate_rest_days(games: pd.DataFrame, team_id: str, game_date: datetime) -> int:
    """Calculate days of rest since last game."""
    previous_games = games[
        (games["game_date"] < game_date)
        & ((games["home_team_id"] == team_id) | (games["away_team_id"] == team_id))
    ].sort_values("game_date", ascending=False)

    if len(previous_games) == 0:
        return 7  # Default

    last_game_date = previous_games.iloc[0]["game_date"]
    return (game_date - last_game_date).days


def calculate_season_progress(
    games: pd.DataFrame, team_id: str, before_date: datetime
) -> float:
    """Calculate season completion percentage."""
    team_games = games[
        (games["game_date"] < before_date)
        & ((games["home_team_id"] == team_id) | (games["away_team_id"] == team_id))
    ]
    return min(len(team_games) / 82.0, 1.0)


def extract_features_for_game(
    game: pd.Series,
    all_games: pd.DataFrame,
    all_team_stats: pd.DataFrame,
    rest_extractor: RestFatigueExtractor = None,
) -> Dict:
    """Extract all features for a single game."""
    game_date = game["game_date"]
    home_team = game["home_team_id"]
    away_team = game["away_team_id"]

    features = {
        "game_id": game["game_id"],
        "game_date": str(game_date.date()),
        "season": game["season"],
        "home_team_id": home_team,
        "away_team_id": away_team,
        "home_win": 1 if game["home_team_is_winner"] else 0,
        "home_score": game["home_score"],
        "away_score": game["away_score"],
    }

    # Rolling stats for different windows
    for window in [5, 10, 20]:
        home_stats = calculate_rolling_stats(
            all_team_stats, home_team, game_date, window
        )
        for key, val in home_stats.items():
            features[f"home_{key}"] = val

        away_stats = calculate_rolling_stats(
            all_team_stats, away_team, game_date, window
        )
        for key, val in away_stats.items():
            features[f"away_{key}"] = val

    # Location splits
    home_at_home = calculate_location_split(
        all_team_stats, home_team, game_date, "home", 20
    )
    for key, val in home_at_home.items():
        features[f"home_{key}"] = val

    away_on_road = calculate_location_split(
        all_team_stats, away_team, game_date, "away", 20
    )
    for key, val in away_on_road.items():
        features[f"away_{key}"] = val

    # Recent form
    features["home_form_l5"] = calculate_recent_form(all_games, home_team, game_date, 5)
    features["away_form_l5"] = calculate_recent_form(all_games, away_team, game_date, 5)

    # Head to head
    h2h = calculate_head_to_head(all_games, home_team, away_team, game_date, 5)
    features.update(h2h)

    # Rest & Fatigue features using specialized extractor
    if rest_extractor is not None:
        # Convert game_date to date object if needed
        game_date_obj = game_date.date() if hasattr(game_date, "date") else game_date

        # Extract rest/fatigue features with rest__ prefix
        rest_features = rest_extractor.extract_features(
            home_team_id=int(home_team),
            away_team_id=int(away_team),
            game_date=game_date_obj,
        )
        for key, val in rest_features.items():
            features[f"rest__{key}"] = val

    # Legacy rest features for backwards compatibility (base__ prefix)
    features["base__home_rest_days"] = calculate_rest_days(
        all_games, home_team, game_date
    )
    features["base__away_rest_days"] = calculate_rest_days(
        all_games, away_team, game_date
    )
    features["base__home_back_to_back"] = (
        1 if features["base__home_rest_days"] <= 1 else 0
    )
    features["base__away_back_to_back"] = (
        1 if features["base__away_rest_days"] <= 1 else 0
    )

    # Season progress
    features["home_season_progress"] = calculate_season_progress(
        all_games, home_team, game_date
    )
    features["away_season_progress"] = calculate_season_progress(
        all_games, away_team, game_date
    )

    return features


def main():
    parser = argparse.ArgumentParser(
        description="Extract NBA game features for Kelly Criterion calibration"
    )
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=["2021-22", "2022-23", "2023-24", "2024-25"],
        help="Seasons to process",
    )
    parser.add_argument(
        "--output", default="data/game_features.csv", help="Output CSV file path"
    )
    parser.add_argument(
        "--min-games",
        type=int,
        default=10,
        help="Minimum games before including team in dataset",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("NBA Game Feature Engineering Pipeline")
    print("=" * 80)
    print(f"Seasons: {args.seasons}")
    print(f"Output: {args.output}")
    print(f"Minimum games: {args.min_games}")
    print()

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    print("Connecting to database...")
    conn = get_db_connection()
    print("✓ Connected\n")

    # Initialize unified feature extractor (includes player features)
    print("Initializing feature extractors...")
    feature_extractor = FeatureExtractor(db_conn=conn)
    print("✓ FeatureExtractor initialized (includes 29 player-level features)\n")

    try:
        # Fetch data
        all_games = fetch_games(conn, args.seasons)
        all_team_stats = fetch_team_stats(conn, args.seasons)

        # Convert dates
        all_games["game_date"] = pd.to_datetime(all_games["game_date"])

        print()
        print("Extracting features...")
        print("-" * 80)

        features_list = []
        errors = 0

        for _, game in tqdm(
            all_games.iterrows(), total=len(all_games), desc="Processing games"
        ):
            try:
                # Use unified FeatureExtractor (includes player features)
                game_features = feature_extractor.extract_game_features(
                    home_team_id=int(game["home_team_id"]),
                    away_team_id=int(game["away_team_id"]),
                    game_date=game["game_date"].strftime("%Y-%m-%d"),
                )

                # Add metadata
                game_features["game_id"] = game["game_id"]
                game_features["game_date"] = str(game["game_date"].date())
                game_features["season"] = game["season"]
                game_features["home_team_id"] = int(game["home_team_id"])
                game_features["away_team_id"] = int(game["away_team_id"])
                game_features["home_win"] = 1 if game["home_team_is_winner"] else 0
                game_features["home_score"] = game["home_score"]
                game_features["away_score"] = game["away_score"]

                # Only include if both teams have played minimum games
                home_games = game_features.get("home_games_played", 0)
                away_games = game_features.get("away_games_played", 0)

                if home_games >= args.min_games and away_games >= args.min_games:
                    features_list.append(game_features)

            except Exception as e:
                errors += 1
                if errors <= 5:  # Only show first 5 errors
                    tqdm.write(f"Error processing game {game['game_id']}: {e}")
                continue

        print()
        print(f"✓ Successfully extracted features for {len(features_list)} games")
        if errors > 0:
            print(f"⚠ Skipped {errors} games due to errors")

        # Create DataFrame
        df = pd.DataFrame(features_list)

        # Save to CSV
        print(f"\nSaving to {args.output}...")
        df.to_csv(args.output, index=False)
        print("✓ Saved successfully")

        # Summary statistics
        print()
        print("=" * 80)
        print("Feature Engineering Complete!")
        print("=" * 80)
        print(f"Total games: {len(df)}")
        print(f"Total features: {len(df.columns)}")
        print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")
        print()
        print("Games by season:")
        print(df["season"].value_counts().sort_index())
        print()
        print("Home team win rate:", f"{df['home_win'].mean():.1%}")
        print()
        print("Feature columns created:", len(df.columns))
        print()
        print("Next steps:")
        print("  1. Run: python scripts/train_game_outcome_model.py")
        print("  2. This will train ensemble model on your features")
        print("  3. Then run backtest to generate calibration data")

    finally:
        conn.close()
        print("\n✓ Database connection closed")


if __name__ == "__main__":
    main()
