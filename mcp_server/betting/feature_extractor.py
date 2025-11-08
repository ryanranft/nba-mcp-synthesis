"""
Feature Extraction Module for Betting Predictions

Extracts real-time features from the NBA database for making betting decisions.
Replaces placeholder features with actual team statistics, head-to-head records,
and other relevant features used by the trained ensemble model.

This module bridges the gap between:
1. Historical feature engineering (prepare_game_features.py) used for training
2. Real-time prediction features needed for live betting

Features Extracted:
------------------
1. Team Statistics (last 10 games rolling average):
   - Points per game (offensive/defensive)
   - Field goal percentage
   - Three-point percentage
   - Free throw percentage
   - Rebounds (offensive/defensive/total)
   - Assists, steals, blocks, turnovers
   - Pace (possessions per game)

2. Head-to-Head Record:
   - Win/loss record in matchup
   - Average point differential
   - Recent meetings (last 3-5 games)

3. Home/Away Splits:
   - Home win percentage
   - Away win percentage
   - Home/away offensive/defensive ratings

4. Advanced Metrics:
   - Effective field goal percentage (eFG%)
   - True shooting percentage (TS%)
   - Offensive/defensive rating
   - Net rating
   - Four factors (shooting, turnovers, rebounding, free throws)

5. Rest & Schedule:
   - Days of rest
   - Back-to-back indicator
   - Travel distance (if available)

6. Injuries & Lineup:
   - Key player absence indicator
   - Minutes distribution

Example Usage:
-------------
    from mcp_server.betting.feature_extractor import FeatureExtractor
    import psycopg2

    # Connect to database
    db_conn = psycopg2.connect(...)

    # Initialize extractor
    extractor = FeatureExtractor(db_conn)

    # Extract features for upcoming game
    features = extractor.extract_game_features(
        home_team_id=1610612747,  # LAL
        away_team_id=1610612744,  # GSW
        game_date='2025-01-05'
    )

    # Use features for prediction
    model = load_model('ensemble_game_outcome_model.pkl')
    prediction = model.predict(features)
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Import specialized feature extractors
from mcp_server.betting.feature_extractors.rest_fatigue import RestFatigueExtractor
from mcp_server.betting.feature_extractors.player_features import PlayerFeatureExtractor


class FeatureExtractor:
    """
    Extract real-time features from NBA database for betting predictions

    This class queries the database to build feature vectors matching
    the format expected by the trained ensemble model.
    """

    def __init__(self, db_conn: psycopg2.extensions.connection):
        """
        Initialize feature extractor

        Args:
            db_conn: PostgreSQL database connection
        """
        self.db_conn = db_conn

        # Initialize specialized extractors
        self.rest_fatigue_extractor = RestFatigueExtractor(db_conn)
        self.player_feature_extractor = PlayerFeatureExtractor(db_conn)

    def extract_game_features(
        self,
        home_team_id: int,
        away_team_id: int,
        game_date: str,
        lookback_games: int = 10
    ) -> Dict[str, float]:
        """
        Extract all features for a game

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            game_date: Game date (YYYY-MM-DD)
            lookback_games: Deprecated, now uses multiple windows [5, 10, 20]

        Returns:
            Dictionary of features matching ensemble model input format
        """
        # Convert game_date string to datetime for consistency
        if isinstance(game_date, str):
            game_date_dt = datetime.strptime(game_date, '%Y-%m-%d')
            game_date_obj = game_date_dt.date()
        else:
            game_date_obj = game_date
            game_date_dt = datetime.combine(game_date, datetime.min.time())

        # Combine all features
        features = {}

        # Get rolling stats for multiple windows (L5, L10, L20)
        for window in [5, 10, 20]:
            home_stats = self._get_team_recent_stats(home_team_id, game_date, window, is_home=True)
            away_stats = self._get_team_recent_stats(away_team_id, game_date, window, is_home=False)

            # Add home team features with window suffix
            for key, value in home_stats.items():
                if key in ['home_win_pct', 'away_win_pct', 'win_pct', 'wins_last_10', 'losses_last_10']:
                    # Skip these - they're not window-specific
                    continue
                features[f'home_{key}_l{window}'] = value

            # Add away team features with window suffix
            for key, value in away_stats.items():
                if key in ['home_win_pct', 'away_win_pct', 'win_pct', 'wins_last_10', 'losses_last_10']:
                    # Skip these - they're not window-specific
                    continue
                features[f'away_{key}_l{window}'] = value

        # Add games_played count for L10 (used for minimum game filtering)
        home_stats_10 = self._get_team_recent_stats(home_team_id, game_date, 10, is_home=True)
        away_stats_10 = self._get_team_recent_stats(away_team_id, game_date, 10, is_home=False)
        features['home_games_played'] = home_stats_10.get('games_played', 0)
        features['away_games_played'] = away_stats_10.get('games_played', 0)

        # Location-specific rolling stats (home team AT home, away team ON road)
        home_at_home_stats = self._get_location_specific_stats(home_team_id, game_date, location='home', window=20)
        away_on_road_stats = self._get_location_specific_stats(away_team_id, game_date, location='away', window=20)

        for key, value in home_at_home_stats.items():
            features[f'home_{key}'] = value
        for key, value in away_on_road_stats.items():
            features[f'away_{key}'] = value

        # Recent form (win % in last 5 games)
        features['home_form_l5'] = self._get_recent_form(home_team_id, game_date, window=5)
        features['away_form_l5'] = self._get_recent_form(away_team_id, game_date, window=5)

        # Season progress
        features['home_season_progress'] = self._get_season_progress(home_team_id, game_date_dt)
        features['away_season_progress'] = self._get_season_progress(away_team_id, game_date_dt)

        # Get head-to-head record
        h2h_stats = self._get_head_to_head_stats(home_team_id, away_team_id, game_date)
        features.update(h2h_stats)

        # Extract rest & fatigue features using specialized extractor
        rest_fatigue_features = self.rest_fatigue_extractor.extract_features(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            game_date=game_date_obj
        )

        # Rest & fatigue features (prefix: rest__)
        for key, value in rest_fatigue_features.items():
            features[f'rest__{key}'] = value

        # Legacy rest features for backwards compatibility (using old simple method)
        home_rest_legacy = self._get_rest_days(home_team_id, game_date)
        away_rest_legacy = self._get_rest_days(away_team_id, game_date)
        features['base__home_rest_days'] = home_rest_legacy
        features['base__away_rest_days'] = away_rest_legacy
        features['base__home_back_to_back'] = 1 if home_rest_legacy <= 1 else 0
        features['base__away_back_to_back'] = 1 if away_rest_legacy <= 1 else 0

        # Extract player-level features (NEW: Phase 1 enhancement)
        player_features = self.player_feature_extractor.extract_features(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            game_date=game_date
        )

        # Player features (prefix: player__)
        for key, value in player_features.items():
            features[f'player__{key}'] = value

        return features

    def _get_team_recent_stats(
        self,
        team_id: int,
        as_of_date: str,
        n_games: int = 10,
        is_home: bool = True
    ) -> Dict[str, float]:
        """
        Get team's recent performance statistics

        Args:
            team_id: Team ID
            as_of_date: Date cutoff (exclude games after this)
            n_games: Number of recent games
            is_home: Whether to include home/away split

        Returns:
            Dictionary of team statistics
        """
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

        # Get recent games for this team from hoopr_team_box (before the target date)
        query = """
            SELECT
                g.game_date,
                g.home_team_id,
                g.away_team_id,
                g.home_score,
                g.away_score,
                htb.team_score as pts,
                htb.field_goals_made as fgm,
                htb.field_goals_attempted as fga,
                htb.three_point_field_goals_made as fg3m,
                htb.three_point_field_goals_attempted as fg3a,
                htb.free_throws_made as ftm,
                htb.free_throws_attempted as fta,
                htb.total_rebounds as reb,
                htb.assists as ast,
                htb.steals as stl,
                htb.blocks as blk,
                COALESCE(htb.turnovers, htb.total_turnovers) as turnover
            FROM games g
            JOIN hoopr_team_box htb ON g.game_id = CAST(htb.game_id AS VARCHAR)
                AND CAST(htb.team_id AS INTEGER) = %s
            WHERE (CAST(g.home_team_id AS INTEGER) = %s OR CAST(g.away_team_id AS INTEGER) = %s)
            AND g.game_date < %s
            AND g.home_score IS NOT NULL  -- Game has been played
            ORDER BY g.game_date DESC
            LIMIT %s
        """

        cursor.execute(query, (team_id, team_id, team_id, as_of_date, n_games))
        games = cursor.fetchall()

        if not games or len(games) == 0:
            # No recent games - return default stats
            return self._default_team_stats()

        # Calculate rolling averages
        stats = {
            'ppg': [],
            'fg_pct': [],
            'fg3_pct': [],
            'ft_pct': [],
            'reb': [],
            'ast': [],
            'stl': [],
            'blk': [],
            'tov': [],
            'wins': 0,
            'losses': 0
        }

        for game in games:
            is_team_home = game['home_team_id'] == team_id

            # Points scored (from hoopr_team_box)
            pts = game['pts'] or 0  # Team's score from hoopr_team_box

            # Opponent's score from games table
            opp_pts = game['away_score'] if is_team_home else game['home_score']

            # Win/loss
            if pts > opp_pts:
                stats['wins'] += 1
            else:
                stats['losses'] += 1

            # Game stats (always available from hoopr_team_box)
            stats['ppg'].append(game['pts'] or 0)
            stats['reb'].append(game['reb'] or 0)
            stats['ast'].append(game['ast'] or 0)
            stats['stl'].append(game['stl'] or 0)
            stats['blk'].append(game['blk'] or 0)
            stats['tov'].append(game['turnover'] or 0)

            # Calculate percentages
            fgm = game['fgm'] or 0
            fga = game['fga'] or 1  # Avoid division by zero
            stats['fg_pct'].append(fgm / fga if fga > 0 else 0)

            fg3m = game['fg3m'] or 0
            fg3a = game['fg3a'] or 1
            stats['fg3_pct'].append(fg3m / fg3a if fg3a > 0 else 0)

            ftm = game['ftm'] or 0
            fta = game['fta'] or 1
            stats['ft_pct'].append(ftm / fta if fta > 0 else 0)

        # Calculate advanced metrics (TS% and eFG%)
        ts_pcts = []
        efg_pcts = []
        for game in games:
            pts = game['pts'] or 0
            fgm = game['fgm'] or 0
            fga = game['fga'] or 1
            fg3m = game['fg3m'] or 0
            fta = game['fta'] or 1

            # True Shooting % = PTS / (2 * (FGA + 0.44 * FTA))
            ts_denominator = 2 * (fga + 0.44 * fta)
            ts_pct = pts / ts_denominator if ts_denominator > 0 else 0
            ts_pcts.append(ts_pct)

            # Effective FG% = (FGM + 0.5 * 3PM) / FGA
            efg_pct = (fgm + 0.5 * fg3m) / fga if fga > 0 else 0
            efg_pcts.append(efg_pct)

        # Calculate averages
        result = {
            'ppg': np.mean(stats['ppg']) if stats['ppg'] else 100.0,
            'fg_pct': np.mean(stats['fg_pct']) if stats['fg_pct'] else 0.45,
            'three_pt_pct': np.mean(stats['fg3_pct']) if stats['fg3_pct'] else 0.35,  # Renamed to match batch
            'ft_pct': np.mean(stats['ft_pct']) if stats['ft_pct'] else 0.75,
            'rebounds': np.mean(stats['reb']) if stats['reb'] else 45.0,  # Renamed to match batch
            'assists': np.mean(stats['ast']) if stats['ast'] else 25.0,  # Renamed to match batch
            'steals': np.mean(stats['stl']) if stats['stl'] else 7.0,  # Renamed to match batch
            'blocks': np.mean(stats['blk']) if stats['blk'] else 5.0,  # Renamed to match batch
            'turnovers': np.mean(stats['tov']) if stats['tov'] else 13.0,  # Renamed to match batch
            'ts_pct': np.mean(ts_pcts) if ts_pcts else 0.55,  # True Shooting %
            'efg_pct': np.mean(efg_pcts) if efg_pcts else 0.52,  # Effective FG%
            'win_pct': stats['wins'] / (stats['wins'] + stats['losses']) if (stats['wins'] + stats['losses']) > 0 else 0.5,
            'wins_last_10': stats['wins'],
            'losses_last_10': stats['losses'],
            'games_played': len(games)  # Add games played count
        }

        # Home/away specific stats
        if is_home:
            home_games = [g for g in games if g['home_team_id'] == team_id]
            if home_games:
                home_wins = sum(1 for g in home_games if g['home_score'] > g['away_score'])
                result['home_win_pct'] = home_wins / len(home_games)
            else:
                result['home_win_pct'] = 0.55  # Slight home court advantage default
        else:
            away_games = [g for g in games if g['away_team_id'] == team_id]
            if away_games:
                away_wins = sum(1 for g in away_games if g['away_score'] > g['home_score'])
                result['away_win_pct'] = away_wins / len(away_games)
            else:
                result['away_win_pct'] = 0.45  # Slight away disadvantage default

        return result

    def _get_head_to_head_stats(
        self,
        home_team_id: int,
        away_team_id: int,
        as_of_date: str,
        lookback_years: int = 3
    ) -> Dict[str, float]:
        """
        Get head-to-head statistics between two teams

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            as_of_date: Date cutoff
            lookback_years: Years to look back for H2H history

        Returns:
            Dictionary of head-to-head stats
        """
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

        # Get recent matchups
        cutoff_date = (datetime.strptime(as_of_date, '%Y-%m-%d') - timedelta(days=365 * lookback_years)).strftime('%Y-%m-%d')

        query = """
            SELECT
                home_team_id,
                away_team_id,
                home_score,
                away_score
            FROM games
            WHERE ((CAST(home_team_id AS INTEGER) = %s AND CAST(away_team_id AS INTEGER) = %s)
                OR (CAST(home_team_id AS INTEGER) = %s AND CAST(away_team_id AS INTEGER) = %s))
            AND game_date >= %s
            AND game_date < %s
            AND home_score IS NOT NULL
            ORDER BY game_date DESC
            LIMIT 10
        """

        cursor.execute(query, (
            home_team_id, away_team_id,
            away_team_id, home_team_id,
            cutoff_date, as_of_date
        ))

        games = cursor.fetchall()

        if not games or len(games) == 0:
            # No H2H history - return neutral stats
            return {
                'h2h_home_wins': 0,
                'h2h_away_wins': 0,
                'h2h_total_games': 0,
                'h2h_home_win_pct': 0.5,
                'h2h_avg_point_diff': 0.0
            }

        # Calculate H2H stats
        home_wins = 0
        point_diffs = []

        for game in games:
            if game['home_team_id'] == home_team_id:
                # Target home team was home
                if game['home_score'] > game['away_score']:
                    home_wins += 1
                point_diffs.append(game['home_score'] - game['away_score'])
            else:
                # Target home team was away
                if game['away_score'] > game['home_score']:
                    home_wins += 1
                point_diffs.append(game['away_score'] - game['home_score'])

        total_games = len(games)
        away_wins = total_games - home_wins

        return {
            'h2h_home_wins': home_wins,
            'h2h_away_wins': away_wins,
            'h2h_total_games': total_games,
            'h2h_home_win_pct': home_wins / total_games if total_games > 0 else 0.5,
            'h2h_avg_point_diff': np.mean(point_diffs) if point_diffs else 0.0
        }

    def _get_rest_days(self, team_id: int, game_date: str) -> int:
        """
        Calculate days of rest before a game

        Args:
            team_id: Team ID
            game_date: Game date (YYYY-MM-DD)

        Returns:
            Number of days of rest
        """
        cursor = self.db_conn.cursor()

        query = """
            SELECT MAX(game_date) as last_game
            FROM games
            WHERE (CAST(home_team_id AS INTEGER) = %s OR CAST(away_team_id AS INTEGER) = %s)
            AND game_date < %s
            AND home_score IS NOT NULL
        """

        cursor.execute(query, (int(team_id), int(team_id), game_date))
        result = cursor.fetchone()

        if result and result[0]:
            last_game_date = result[0]
            current_date = datetime.strptime(game_date, '%Y-%m-%d').date()
            if isinstance(last_game_date, str):
                last_game_date = datetime.strptime(last_game_date, '%Y-%m-%d').date()

            rest_days = (current_date - last_game_date).days
            return rest_days
        else:
            # No previous game found - return large number (well rested)
            return 7

    def _default_team_stats(self) -> Dict[str, float]:
        """Return default team stats when no data available"""
        return {
            'ppg': 110.0,  # League average
            'fg_pct': 0.46,
            'three_pt_pct': 0.36,
            'ft_pct': 0.78,
            'rebounds': 45.0,
            'assists': 25.0,
            'steals': 7.5,
            'blocks': 5.0,
            'turnovers': 13.0,
            'ts_pct': 0.55,
            'efg_pct': 0.52,
            'win_pct': 0.5,
            'wins_last_10': 5,
            'losses_last_10': 5,
            'home_win_pct': 0.55,
            'away_win_pct': 0.45,
            'games_played': 0
        }

    def _get_location_specific_stats(
        self,
        team_id: int,
        as_of_date: str,
        location: str,
        window: int = 20
    ) -> Dict[str, float]:
        """
        Get location-specific rolling stats (home team AT home, away team ON road)

        Args:
            team_id: Team ID
            as_of_date: Date cutoff (exclude games after this)
            location: 'home' or 'away'
            window: Number of recent games at that location

        Returns:
            Dictionary with ppg_{location}_l{window} and {location}_games
        """
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

        # Query for location-specific games using hoopr_team_box
        query = """
            SELECT
                htb.team_score as pts
            FROM hoopr_team_box htb
            JOIN games g ON g.game_id = CAST(htb.game_id AS VARCHAR)
            WHERE CAST(htb.team_id AS INTEGER) = %s
            AND htb.team_home_away = %s
            AND g.game_date < %s
            AND g.home_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT %s
        """

        cursor.execute(query, (team_id, location, as_of_date, window))
        games = cursor.fetchall()

        if not games or len(games) == 0:
            return {
                f'ppg_{location}_l{window}': 110.0,  # Default
                f'{location}_games': 0
            }

        # Calculate PPG at location
        ppg = np.mean([g['pts'] for g in games if g['pts'] is not None])

        return {
            f'ppg_{location}_l{window}': float(ppg),
            f'{location}_games': len(games)
        }

    def _get_recent_form(
        self,
        team_id: int,
        as_of_date: str,
        window: int = 5
    ) -> float:
        """
        Calculate recent win percentage (form)

        Args:
            team_id: Team ID
            as_of_date: Date cutoff
            window: Number of recent games

        Returns:
            Win percentage in last {window} games
        """
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                home_team_id,
                away_team_id,
                home_score,
                away_score
            FROM games
            WHERE (CAST(home_team_id AS INTEGER) = %s OR CAST(away_team_id AS INTEGER) = %s)
            AND game_date < %s
            AND home_score IS NOT NULL
            ORDER BY game_date DESC
            LIMIT %s
        """

        cursor.execute(query, (team_id, team_id, as_of_date, window))
        games = cursor.fetchall()

        if not games or len(games) == 0:
            return 0.5  # Default 50%

        # Calculate wins
        wins = 0
        for game in games:
            if game['home_team_id'] == team_id:
                # Team was home
                if game['home_score'] > game['away_score']:
                    wins += 1
            else:
                # Team was away
                if game['away_score'] > game['home_score']:
                    wins += 1

        return wins / len(games)

    def _get_season_progress(
        self,
        team_id: int,
        as_of_date: datetime
    ) -> float:
        """
        Calculate season completion percentage

        Args:
            team_id: Team ID
            as_of_date: Date cutoff (as datetime)

        Returns:
            Percentage of season completed (games_played / 82)
        """
        cursor = self.db_conn.cursor()

        # Get season from as_of_date
        # NBA season: Oct-Apr (crosses calendar year)
        # If month >= 10, season is current_year to next_year
        # If month < 10, season is previous_year to current_year
        year = as_of_date.year
        month = as_of_date.month

        if month >= 10:
            season = f"{year}-{str(year + 1)[-2:]}"
        else:
            season = f"{year - 1}-{str(year)[-2:]}"

        # Count games played by team in current season before as_of_date
        query = """
            SELECT COUNT(*) as games_played
            FROM games
            WHERE (CAST(home_team_id AS INTEGER) = %s OR CAST(away_team_id AS INTEGER) = %s)
            AND season = %s
            AND game_date < %s
            AND home_score IS NOT NULL
        """

        cursor.execute(query, (team_id, team_id, season, as_of_date.date()))
        result = cursor.fetchone()

        games_played = result[0] if result and result[0] else 0

        # NBA regular season is 82 games
        return min(games_played / 82.0, 1.0)

    def get_todays_games(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of games for a specific date

        Args:
            target_date: Date in YYYY-MM-DD format (default: today)

        Returns:
            List of game dictionaries with team info
        """
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')

        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                g.game_id,
                g.game_date,
                g.home_team_id,
                g.visitor_team_id as away_team_id,
                ht.full_name as home_team_name,
                vt.full_name as away_team_name,
                ht.abbreviation as home_team_abbr,
                vt.abbreviation as away_team_abbr
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.team_id
            JOIN teams vt ON g.visitor_team_id = vt.team_id
            WHERE g.game_date = %s
            AND g.home_team_pts IS NULL  -- Game hasn't been played yet
            ORDER BY g.game_date
        """

        cursor.execute(query, (target_date,))
        games = cursor.fetchall()

        return [dict(game) for game in games]
