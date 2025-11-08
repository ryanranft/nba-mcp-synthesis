"""
Player-Level Feature Extraction for NBA Betting

Extracts player-level features from hoopr_player_box to enhance team-level predictions.
Supports better moneyline predictions and enables spread/totals modeling.

Features Extracted:
------------------
1. Top Scorers (top 3 players by PPG L10)
2. Roster Strength (sum of PER for top 5 players)
3. Injury Impact (missing players' contribution)
4. Position Matchups (PG vs PG, SG vs SG, etc.)
5. Star Player Availability

Example Usage:
-------------
    from mcp_server.betting.feature_extractors.player_features import PlayerFeatureExtractor
    import psycopg2

    conn = psycopg2.connect(...)
    extractor = PlayerFeatureExtractor(conn)

    # Extract features for a game
    features = extractor.extract_features(
        home_team_id=1610612747,  # LAL
        away_team_id=1610612744,  # GSW
        game_date='2025-01-05'
    )

    # Returns dict with ~20-30 player-level features
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor


class PlayerFeatureExtractor:
    """
    Extract player-level features from hoopr_player_box for betting predictions
    """

    def __init__(self, db_conn: psycopg2.extensions.connection):
        """
        Initialize player feature extractor

        Args:
            db_conn: PostgreSQL database connection
        """
        self.db_conn = db_conn

        # Position mappings (for matchup analysis)
        self.positions = ['PG', 'SG', 'SF', 'PF', 'C']

    def extract_features(
        self,
        home_team_id: int,
        away_team_id: int,
        game_date: str
    ) -> Dict[str, float]:
        """
        Extract all player-level features for a game

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            game_date: Game date (YYYY-MM-DD)

        Returns:
            Dictionary of player-level features
        """
        features = {}

        # Convert game_date to datetime if string
        if isinstance(game_date, str):
            game_date_dt = datetime.strptime(game_date, '%Y-%m-%d')
        else:
            game_date_dt = game_date

        # 1. Top Scorers (top 3 by PPG L10)
        home_top_scorers = self._get_top_scorers(home_team_id, game_date_dt, n=3, lookback=10)
        away_top_scorers = self._get_top_scorers(away_team_id, game_date_dt, n=3, lookback=10)

        # Add top scorer features
        for i, scorer in enumerate(home_top_scorers, 1):
            features[f'home_top{i}_ppg_l10'] = scorer['ppg']
            features[f'home_top{i}_minutes_l10'] = scorer['minutes']
            features[f'home_top{i}_usage_pct_l10'] = scorer['usage_pct']

        for i, scorer in enumerate(away_top_scorers, 1):
            features[f'away_top{i}_ppg_l10'] = scorer['ppg']
            features[f'away_top{i}_minutes_l10'] = scorer['minutes']
            features[f'away_top{i}_usage_pct_l10'] = scorer['usage_pct']

        # 2. Roster Strength (sum of PER for top 5 players)
        features['home_roster_per_sum'] = self._get_roster_strength(home_team_id, game_date_dt, n=5)
        features['away_roster_per_sum'] = self._get_roster_strength(away_team_id, game_date_dt, n=5)

        # 3. Injury Impact (estimated PPG lost from missing players)
        features['home_injury_impact'] = self._get_injury_impact(home_team_id, game_date_dt)
        features['away_injury_impact'] = self._get_injury_impact(away_team_id, game_date_dt)

        # 4. Star Player Availability (binary: are top 3 scorers available?)
        features['home_stars_available'] = self._check_star_availability(home_team_id, game_date_dt)
        features['away_stars_available'] = self._check_star_availability(away_team_id, game_date_dt)

        # 5. Depth Score (bench strength - PPG from players ranked 6-10)
        features['home_bench_ppg'] = self._get_bench_strength(home_team_id, game_date_dt)
        features['away_bench_ppg'] = self._get_bench_strength(away_team_id, game_date_dt)

        # 6. Position Matchups (average PPG by position: home vs away)
        matchup_features = self._get_position_matchups(home_team_id, away_team_id, game_date_dt)
        features.update(matchup_features)

        return features

    def _get_top_scorers(
        self,
        team_id: int,
        as_of_date: datetime,
        n: int = 3,
        lookback: int = 10
    ) -> List[Dict[str, float]]:
        """
        Get top N scorers for a team based on recent PPG

        Args:
            team_id: Team ID
            as_of_date: Date cutoff
            n: Number of top scorers to return
            lookback: Number of recent games to consider

        Returns:
            List of dicts with player stats (ppg, minutes, usage_pct)
        """
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

        # Query to get player stats for recent games
        query = """
        WITH player_games AS (
            SELECT
                pb.athlete_id,
                pb.athlete_display_name,
                (pb.field_goals_made * 2 + pb.three_point_field_goals_made * 3 + pb.free_throws_made) as points,
                pb.minutes,
                pb.field_goals_attempted as fga,
                pb.free_throws_attempted as fta,
                pb.turnovers as tov,
                g.game_date
            FROM hoopr_player_box pb
            JOIN games g ON g.game_id = CAST(pb.game_id AS VARCHAR)
            WHERE CAST(pb.team_id AS INTEGER) = %s
            AND g.game_date < %s
            AND pb.minutes > 0  -- Player actually played
            AND pb.did_not_play = 0
            ORDER BY g.game_date DESC
        ),
        player_recent_stats AS (
            SELECT
                athlete_id,
                athlete_display_name,
                AVG(points) as ppg,
                AVG(minutes) as avg_minutes,
                COUNT(*) as games_played,
                -- Usage rate approximation: (FGA + 0.44 * FTA + TOV) / minutes
                AVG((fga + 0.44 * fta + COALESCE(tov, 0)) / NULLIF(minutes, 0)) * 100 as usage_pct
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (PARTITION BY athlete_id ORDER BY game_date DESC) as rn
                FROM player_games
            ) recent
            WHERE rn <= %s  -- Last N games
            GROUP BY athlete_id, athlete_display_name
            HAVING COUNT(*) >= 3  -- Must have played at least 3 games
        )
        SELECT
            athlete_id,
            athlete_display_name,
            ppg,
            avg_minutes as minutes,
            COALESCE(usage_pct, 20.0) as usage_pct,  -- Default usage rate
            games_played
        FROM player_recent_stats
        ORDER BY ppg DESC
        LIMIT %s
        """

        cursor.execute(query, (team_id, as_of_date.date(), lookback, n))
        results = cursor.fetchall()

        # Convert to list of dicts
        top_scorers = []
        for i, row in enumerate(results):
            top_scorers.append({
                'athlete_id': row['athlete_id'],
                'athlete_name': row['athlete_display_name'],
                'ppg': float(row['ppg']) if row['ppg'] else 0.0,
                'minutes': float(row['minutes']) if row['minutes'] else 0.0,
                'usage_pct': float(row['usage_pct']) if row['usage_pct'] else 20.0,
                'games_played': row['games_played']
            })

        # Fill with defaults if fewer than n players found
        while len(top_scorers) < n:
            top_scorers.append({
                'athlete_id': None,
                'athlete_name': 'Unknown',
                'ppg': 0.0,
                'minutes': 0.0,
                'usage_pct': 0.0,
                'games_played': 0
            })

        return top_scorers

    def _get_roster_strength(
        self,
        team_id: int,
        as_of_date: datetime,
        n: int = 5
    ) -> float:
        """
        Calculate roster strength as sum of PER for top N players

        PER approximation: (PTS + REB + AST + STL + BLK - TOV - (FGA - FGM)) / MIN

        Args:
            team_id: Team ID
            as_of_date: Date cutoff
            n: Number of top players to consider

        Returns:
            Sum of PER for top N players
        """
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

        query = """
        WITH player_games AS (
            SELECT
                pb.athlete_id,
                (pb.field_goals_made * 2 + pb.three_point_field_goals_made * 3 + pb.free_throws_made) as points,
                pb.rebounds as rebounds,
                pb.assists,
                pb.steals,
                pb.blocks,
                pb.turnovers as turnovers,
                pb.field_goals_made as fgm,
                pb.field_goals_attempted as fga,
                pb.minutes,
                g.game_date
            FROM hoopr_player_box pb
            JOIN games g ON g.game_id = CAST(pb.game_id AS VARCHAR)
            WHERE CAST(pb.team_id AS INTEGER) = %s
            AND g.game_date < %s
            AND pb.minutes > 0
            AND pb.did_not_play = 0
            ORDER BY g.game_date DESC
        ),
        player_recent_per AS (
            SELECT
                athlete_id,
                AVG(
                    CASE WHEN minutes > 0 THEN
                        (points + rebounds + assists + steals + blocks - turnovers - (fga - fgm)) / minutes
                    ELSE 0 END
                ) * 48 as per  -- Normalize to per-48-minutes
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (PARTITION BY athlete_id ORDER BY game_date DESC) as rn
                FROM player_games
            ) recent
            WHERE rn <= 10  -- Last 10 games
            GROUP BY athlete_id
            HAVING COUNT(*) >= 3
        )
        SELECT per
        FROM player_recent_per
        ORDER BY per DESC
        LIMIT %s
        """

        cursor.execute(query, (team_id, as_of_date.date(), n))
        results = cursor.fetchall()

        # Sum PER for top N players
        total_per = sum(row['per'] for row in results if row['per'])

        return float(total_per) if total_per else 0.0

    def _get_injury_impact(
        self,
        team_id: int,
        as_of_date: datetime
    ) -> float:
        """
        Estimate injury impact as PPG lost from missing players

        Simplified version: Returns 0.0 for now
        (Full implementation requires better schema understanding)

        Args:
            team_id: Team ID
            as_of_date: Date cutoff

        Returns:
            Estimated PPG lost from injuries/absences (currently 0.0)
        """
        # Simplified implementation - return 0.0 for now
        # TODO: Implement proper injury tracking once schema is clarified
        return 0.0

    def _check_star_availability(
        self,
        team_id: int,
        as_of_date: datetime
    ) -> float:
        """
        Check if star players (top 3 scorers) are available

        Returns:
            Percentage of top 3 scorers available (0.0 to 1.0)
        """
        # Get top 3 scorers
        top_scorers = self._get_top_scorers(team_id, as_of_date, n=3, lookback=10)

        if not top_scorers or all(s['athlete_id'] is None for s in top_scorers):
            return 1.0  # No data, assume available

        # Check how many are playing in recent games (not DNP)
        cursor = self.db_conn.cursor()

        # Get most recent game
        query_recent_game = """
        SELECT MAX(g.game_date) as last_game
        FROM games g
        WHERE (CAST(g.home_team_id AS INTEGER) = %s OR CAST(g.away_team_id AS INTEGER) = %s)
        AND g.game_date < %s
        AND g.home_score IS NOT NULL
        """

        cursor.execute(query_recent_game, (team_id, team_id, as_of_date.date()))
        last_game_result = cursor.fetchone()

        if not last_game_result or not last_game_result[0]:
            return 1.0  # No recent game, assume available

        last_game_date = last_game_result[0]

        # Check if top scorers played in last game
        available_count = 0
        for scorer in top_scorers:
            if scorer['athlete_id'] is None:
                continue

            query_played = """
            SELECT COUNT(*) as played
            FROM hoopr_player_box pb
            JOIN games g ON g.game_id = CAST(pb.game_id AS VARCHAR)
            WHERE pb.athlete_id = %s
            AND g.game_date = %s
            AND pb.minutes > 0
            AND pb.did_not_play = 0
            """

            cursor.execute(query_played, (scorer['athlete_id'], last_game_date))
            played_result = cursor.fetchone()

            if played_result and played_result[0] > 0:
                available_count += 1

        return available_count / 3.0  # Percentage of top 3 available

    def _get_bench_strength(
        self,
        team_id: int,
        as_of_date: datetime
    ) -> float:
        """
        Calculate bench strength as average PPG from players ranked 6-10

        Args:
            team_id: Team ID
            as_of_date: Date cutoff

        Returns:
            Average PPG from bench players (6th-10th best scorers)
        """
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

        query = """
        WITH player_games AS (
            SELECT
                pb.athlete_id,
                (pb.field_goals_made * 2 + pb.three_point_field_goals_made * 3 + pb.free_throws_made) as points,
                g.game_date
            FROM hoopr_player_box pb
            JOIN games g ON g.game_id = CAST(pb.game_id AS VARCHAR)
            WHERE CAST(pb.team_id AS INTEGER) = %s
            AND g.game_date < %s
            AND pb.minutes > 0
            AND pb.did_not_play = 0
            ORDER BY g.game_date DESC
        ),
        player_recent_ppg AS (
            SELECT
                athlete_id,
                AVG(points) as ppg
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (PARTITION BY athlete_id ORDER BY game_date DESC) as rn
                FROM player_games
            ) recent
            WHERE rn <= 10  -- Last 10 games
            GROUP BY athlete_id
            HAVING COUNT(*) >= 3
        ),
        ranked_players AS (
            SELECT
                ppg,
                ROW_NUMBER() OVER (ORDER BY ppg DESC) as rank
            FROM player_recent_ppg
        )
        SELECT AVG(ppg) as bench_ppg
        FROM ranked_players
        WHERE rank BETWEEN 6 AND 10  -- 6th to 10th best scorers
        """

        cursor.execute(query, (team_id, as_of_date.date()))
        result = cursor.fetchone()

        bench_ppg = result['bench_ppg'] if result and result['bench_ppg'] else 0.0

        return float(bench_ppg)

    def _get_position_matchups(
        self,
        home_team_id: int,
        away_team_id: int,
        as_of_date: datetime
    ) -> Dict[str, float]:
        """
        Calculate position-based matchup advantages

        Compares average PPG by position for home team vs away team

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            as_of_date: Date cutoff

        Returns:
            Dict with position matchup features (e.g., 'pg_matchup_advantage': 2.5)
        """
        # Note: hoopr_player_box doesn't have position info directly
        # We'll use players table to get positions
        # For now, return simplified matchup based on top scorer differential

        # Get total PPG for each team's top players
        home_top_ppg = sum(s['ppg'] for s in self._get_top_scorers(home_team_id, as_of_date, n=5))
        away_top_ppg = sum(s['ppg'] for s in self._get_top_scorers(away_team_id, as_of_date, n=5))

        matchup_advantage = home_top_ppg - away_top_ppg

        # Simplified matchup features (can be expanded with position-specific data later)
        return {
            'top5_ppg_advantage': float(matchup_advantage),
            'home_top5_ppg': float(home_top_ppg),
            'away_top5_ppg': float(away_top_ppg)
        }
