"""
Rest & Fatigue Feature Extractor

Extracts schedule-based features that impact team performance:
- Days of rest since last game
- Back-to-back game indicators
- Schedule density (games in recent window)
- Travel fatigue indicators

Research shows:
- Teams on 0 days rest (back-to-backs) underperform by ~3-5%
- Third game in 4 nights shows significant fatigue (~5-7% worse)
- Rest advantage (3+ days vs 0 days) worth ~4-6 points

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import psycopg2
import pandas as pd

logger = logging.getLogger(__name__)


class RestFatigueExtractor:
    """
    Extract rest and fatigue features from game schedule

    Features Generated:
    - home_rest_days: Days since home team's last game
    - away_rest_days: Days since away team's last game
    - home_back_to_back: Boolean (0 days rest)
    - away_back_to_back: Boolean (0 days rest)
    - home_third_in_4: Boolean (3rd game in 4 nights - extreme fatigue)
    - away_third_in_4: Boolean (3rd game in 4 nights - extreme fatigue)
    - rest_advantage: Difference (home_rest - away_rest)
    """

    def __init__(self, db_conn: Optional[psycopg2.extensions.connection] = None):
        """
        Initialize rest/fatigue extractor

        Args:
            db_conn: PostgreSQL database connection (optional, will create if None)
        """
        self.db_conn = db_conn
        self._cache = {}  # Cache team schedules

        logger.info("RestFatigueExtractor initialized")

    def extract_features(
        self, home_team_id: int, away_team_id: int, game_date: date
    ) -> Dict[str, float]:
        """
        Extract rest/fatigue features for a specific game

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            game_date: Date of the game

        Returns:
            Dict of feature_name -> value
        """
        features = {}

        try:
            # Get rest days for each team
            home_rest, home_schedule = self._get_rest_days(home_team_id, game_date)
            away_rest, away_schedule = self._get_rest_days(away_team_id, game_date)

            # Basic rest features
            features["home_rest_days"] = home_rest
            features["away_rest_days"] = away_rest
            features["rest_advantage"] = home_rest - away_rest

            # Back-to-back indicators
            features["home_back_to_back"] = 1.0 if home_rest == 0 else 0.0
            features["away_back_to_back"] = 1.0 if away_rest == 0 else 0.0

            # Extreme fatigue: 3rd game in 4 nights
            features["home_third_in_4"] = self._check_third_in_4_nights(
                home_schedule, game_date
            )
            features["away_third_in_4"] = self._check_third_in_4_nights(
                away_schedule, game_date
            )

            # Schedule density features
            home_games_l7 = self._count_games_in_window(
                home_schedule, game_date, days=7
            )
            away_games_l7 = self._count_games_in_window(
                away_schedule, game_date, days=7
            )

            features["home_games_last_7"] = home_games_l7
            features["away_games_last_7"] = away_games_l7
            features["schedule_density_diff"] = home_games_l7 - away_games_l7

            logger.debug(
                f"Rest features extracted: home={home_rest}d, away={away_rest}d, "
                f"home_b2b={features['home_back_to_back']}, away_b2b={features['away_back_to_back']}"
            )

        except Exception as e:
            logger.error(f"Error extracting rest/fatigue features: {e}")
            # Return default values on error
            features = {
                "home_rest_days": 1.0,
                "away_rest_days": 1.0,
                "rest_advantage": 0.0,
                "home_back_to_back": 0.0,
                "away_back_to_back": 0.0,
                "home_third_in_4": 0.0,
                "away_third_in_4": 0.0,
                "home_games_last_7": 3.0,
                "away_games_last_7": 3.0,
                "schedule_density_diff": 0.0,
            }

        return features

    def _get_rest_days(self, team_id: int, game_date: date) -> Tuple[int, List[date]]:
        """
        Calculate days of rest for a team

        Args:
            team_id: Team ID
            game_date: Current game date

        Returns:
            Tuple of (rest_days, recent_schedule)
        """
        # Check cache
        cache_key = (team_id, game_date)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Query recent games for this team
        cursor = self.db_conn.cursor()

        query = """
            SELECT game_date
            FROM games
            WHERE (CAST(home_team_id AS INTEGER) = %s OR CAST(away_team_id AS INTEGER) = %s)
              AND game_date < %s
              AND game_date >= %s - INTERVAL '14 days'
            ORDER BY game_date DESC
            LIMIT 10
        """

        cursor.execute(query, (int(team_id), int(team_id), game_date, game_date))
        rows = cursor.fetchall()

        if not rows:
            # No recent games (season start or new team)
            rest_days = 3
            schedule = []
        else:
            # Most recent game
            last_game_date = rows[0][0]

            # Calculate rest days
            rest_days = (game_date - last_game_date).days - 1

            # Build schedule list
            schedule = [row[0] for row in rows]

        # Cache result
        self._cache[cache_key] = (rest_days, schedule)

        return rest_days, schedule

    def _check_third_in_4_nights(self, schedule: List[date], game_date: date) -> float:
        """
        Check if this is the third game in 4 nights (extreme fatigue)

        Args:
            schedule: List of recent game dates (sorted desc)
            game_date: Current game date

        Returns:
            1.0 if third in 4 nights, else 0.0
        """
        if len(schedule) < 2:
            return 0.0

        # Check last 2 games
        game1_date = schedule[0]  # Most recent
        game2_date = schedule[1]  # 2nd most recent

        # All 3 games (game2, game1, current) within 4 nights?
        days_span = (game_date - game2_date).days

        if days_span <= 3:  # 4 nights = 3 day difference
            return 1.0

        return 0.0

    def _count_games_in_window(
        self, schedule: List[date], game_date: date, days: int
    ) -> int:
        """
        Count games played in last N days

        Args:
            schedule: List of recent game dates
            game_date: Current game date
            days: Window size in days

        Returns:
            Number of games in window
        """
        cutoff_date = game_date - timedelta(days=days)

        count = sum(1 for g_date in schedule if g_date >= cutoff_date)

        return count

    def extract_batch(self, games: List[Dict[str, any]]) -> pd.DataFrame:
        """
        Extract features for multiple games at once (more efficient)

        Args:
            games: List of game dicts with 'home_team_id', 'away_team_id', 'game_date'

        Returns:
            DataFrame with features for each game
        """
        features_list = []

        for game in games:
            features = self.extract_features(
                home_team_id=game["home_team_id"],
                away_team_id=game["away_team_id"],
                game_date=game["game_date"],
            )
            features["game_id"] = game.get("game_id")
            features_list.append(features)

        return pd.DataFrame(features_list)

    def clear_cache(self):
        """Clear the schedule cache"""
        self._cache = {}
        logger.info("Rest/fatigue cache cleared")


if __name__ == "__main__":
    # Test rest/fatigue extraction
    import sys
    import os
    from pathlib import Path

    # Add project root
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    from mcp_server.unified_secrets_manager import load_secrets_hierarchical
    import psycopg2

    print("=" * 70)
    print("Rest & Fatigue Feature Extractor - Test")
    print("=" * 70)
    print()

    # Load secrets
    print("📦 Loading secrets...")
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
    print("✅ Secrets loaded")
    print()

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(
        host=os.getenv("RDS_HOST"),
        port=os.getenv("RDS_PORT"),
        database=os.getenv("RDS_DATABASE"),
        user=os.getenv("RDS_USERNAME"),
        password=os.getenv("RDS_PASSWORD"),
    )
    print("✅ Database connected")
    print()

    # Initialize extractor
    extractor = RestFatigueExtractor(db_conn=conn)

    # Get a recent game for testing
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            game_id,
            home_team_id,
            away_team_id,
            game_date,
            home_team_name,
            away_team_name
        FROM games
        WHERE game_date >= CURRENT_DATE - INTERVAL '30 days'
          AND home_score IS NOT NULL
        ORDER BY game_date DESC
        LIMIT 5
    """
    )

    games = cursor.fetchall()

    if games:
        print("🧪 Testing on recent games:")
        print("-" * 70)

        for game in games:
            game_id, home_id, away_id, g_date, home_name, away_name = game

            print(f"\nGame: {away_name} @ {home_name}")
            print(f"Date: {g_date}")

            # Extract features
            features = extractor.extract_features(
                home_team_id=home_id, away_team_id=away_id, game_date=g_date
            )

            print(f"\nFeatures:")
            for key, value in features.items():
                if "back_to_back" in key or "third_in_4" in key:
                    print(f"  {key}: {'YES' if value == 1.0 else 'NO'}")
                else:
                    print(f"  {key}: {value}")

        print()
        print("✅ Feature extraction successful!")

    else:
        print("ℹ️  No recent games found")

    conn.close()
