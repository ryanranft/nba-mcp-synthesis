"""
Shot Zone Analytics

Calculate zone efficiency, expected values, and player shot profiles.

Usage:
    from mcp_server.analytics import ShotZoneAnalytics
    
    analytics = ShotZoneAnalytics()
    
    # Zone efficiency
    efficiency = analytics.calculate_zone_efficiency()
    
    # Expected value by zone
    expected_value = analytics.expected_value_by_zone()
    
    # Player shot profile
    profile = analytics.player_shot_profile(player_id=2544)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
from dataclasses import dataclass

from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config


@dataclass
class ZoneEfficiency:
    """Zone efficiency metrics"""
    zone: str
    attempts: int
    made: int
    fg_pct: float
    points_per_shot: float
    expected_value: float


@dataclass
class PlayerShotProfile:
    """Player shot profile by zone"""
    player_id: int
    zone_distribution: Dict[str, int]
    zone_efficiency: Dict[str, float]
    favorite_zones: List[str]
    weak_zones: List[str]


class ShotZoneAnalytics:
    """Calculate shot zone analytics and expected values"""

    def __init__(self):
        """Initialize analytics with database connection"""
        load_secrets_hierarchical()
        config = get_database_config()
        self.conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)

    def calculate_zone_efficiency(self, season: Optional[int] = None) -> List[ZoneEfficiency]:
        """
        Calculate efficiency metrics for each zone.

        Args:
            season: Optional season filter (e.g., 2023)

        Returns:
            List of ZoneEfficiency objects
        """
        cursor = self.conn.cursor()

        season_filter = f"AND EXTRACT(YEAR FROM s.date) = {season}" if season else ""

        query = f"""
            SELECT 
                shot_zone,
                COUNT(*) as attempts,
                SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) as made,
                ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fg_pct,
                ROUND(AVG(score_value)::numeric, 3) as points_per_shot,
                ROUND((SUM(CASE WHEN scoring_play = 1 THEN score_value ELSE 0 END)::float / COUNT(*)), 3) as expected_value
            FROM hoopr_play_by_play p
            LEFT JOIN hoopr_schedule s ON p.game_id = s.game_id
            WHERE shooting_play = 1
              AND shot_zone IS NOT NULL
              {season_filter}
            GROUP BY shot_zone
            ORDER BY expected_value DESC
        """

        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        return [
            ZoneEfficiency(
                zone=row['shot_zone'],
                attempts=row['attempts'],
                made=row['made'],
                fg_pct=row['fg_pct'],
                points_per_shot=row['points_per_shot'],
                expected_value=row['expected_value']
            )
            for row in results
        ]

    def expected_value_by_zone(self) -> Dict[str, float]:
        """
        Calculate expected value (points per shot) for each zone.

        Returns:
            Dict mapping zone names to expected values
        """
        efficiencies = self.calculate_zone_efficiency()
        return {eff.zone: eff.expected_value for eff in efficiencies}

    def league_average_by_zone(self) -> Dict[str, Dict]:
        """
        Get league average FG% and expected value by zone.

        Returns:
            Dict with zone stats
        """
        cursor = self.conn.cursor()

        query = """
            SELECT 
                shot_zone,
                ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as league_avg_fg_pct,
                ROUND((SUM(CASE WHEN scoring_play = 1 THEN score_value ELSE 0 END)::float / COUNT(*)), 3) as league_avg_ev
            FROM hoopr_play_by_play
            WHERE shooting_play = 1
              AND shot_zone IS NOT NULL
            GROUP BY shot_zone
        """

        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        return {
            row['shot_zone']: {
                'fg_pct': row['league_avg_fg_pct'],
                'expected_value': row['league_avg_ev']
            }
            for row in results
        }

    def player_shot_profile(self, player_id: int) -> Optional[PlayerShotProfile]:
        """
        Generate shot profile for a specific player.

        Args:
            player_id: Athlete ID

        Returns:
            PlayerShotProfile object or None if player not found
        """
        cursor = self.conn.cursor()

        # Get zone distribution
        query = """
            SELECT 
                shot_zone,
                COUNT(*) as attempts,
                ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fg_pct
            FROM hoopr_play_by_play
            WHERE shooting_play = 1
              AND shot_zone IS NOT NULL
              AND athlete_id = %s
            GROUP BY shot_zone
            ORDER BY attempts DESC
        """

        cursor.execute(query, (player_id,))
        results = cursor.fetchall()
        cursor.close()

        if not results:
            return None

        zone_distribution = {row['shot_zone']: row['attempts'] for row in results}
        zone_efficiency = {row['shot_zone']: row['fg_pct'] for row in results}

        # Find favorite zones (top 3 by volume)
        favorite_zones = sorted(zone_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        favorite_zones = [zone for zone, _ in favorite_zones]

        # Find weak zones (lowest FG% with minimum 10 attempts)
        weak_zones = [(zone, eff) for zone, eff in zone_efficiency.items() 
                     if zone_distribution[zone] >= 10]
        weak_zones = sorted(weak_zones, key=lambda x: x[1])[:3]
        weak_zones = [zone for zone, _ in weak_zones]

        return PlayerShotProfile(
            player_id=player_id,
            zone_distribution=zone_distribution,
            zone_efficiency=zone_efficiency,
            favorite_zones=favorite_zones,
            weak_zones=weak_zones
        )

    def team_defensive_zones(self, team_id: int, season: Optional[int] = None) -> Dict[str, Dict]:
        """
        Calculate opponent FG% by zone when defending (team defensive profile).

        Args:
            team_id: Team ID
            season: Optional season filter

        Returns:
            Dict with zone defensive stats
        """
        cursor = self.conn.cursor()

        season_filter = f"AND EXTRACT(YEAR FROM s.date) = {season}" if season else ""

        query = f"""
            SELECT 
                shot_zone,
                COUNT(*) as opponent_attempts,
                SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) as opponent_made,
                ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as opponent_fg_pct
            FROM hoopr_play_by_play p
            LEFT JOIN hoopr_schedule s ON p.game_id = s.game_id
            WHERE shooting_play = 1
              AND shot_zone IS NOT NULL
              AND p.team_id != %s  -- Opponent shots
              AND (s.home_team_id = %s OR s.away_team_id = %s)  -- Team's games
              {season_filter}
            GROUP BY shot_zone
            ORDER BY opponent_attempts DESC
        """

        cursor.execute(query, (team_id, team_id, team_id))
        results = cursor.fetchall()
        cursor.close()

        return {
            row['shot_zone']: {
                'opponent_attempts': row['opponent_attempts'],
                'opponent_made': row['opponent_made'],
                'opponent_fg_pct': row['opponent_fg_pct']
            }
            for row in results
        }

    def shot_quality_score(self, zone: str, distance: float) -> float:
        """
        Calculate shot quality score (0-100) based on zone and distance.

        Higher scores = better quality shots

        Args:
            zone: Shot zone
            distance: Shot distance in feet

        Returns:
            Quality score (0-100)
        """
        # Get expected value for this zone
        ev_map = self.expected_value_by_zone()
        zone_ev = ev_map.get(zone, 1.0)

        # Base score from expected value (normalized to 0-50)
        base_score = min(50, zone_ev * 50)

        # Distance penalty (closer is better, up to 50 points)
        if distance < 4:
            distance_score = 50  # Restricted area
        elif distance < 10:
            distance_score = 40
        elif distance < 20:
            distance_score = 30
        elif distance < 25:
            distance_score = 20
        else:
            distance_score = 10

        return base_score + (distance_score * 0.5)  # Weight distance 50%

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
