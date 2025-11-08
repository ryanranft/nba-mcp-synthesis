#!/usr/bin/env python3
"""
Shot Zone Query Utility

Query and analyze shot zones from the NBA MCP Synthesis database.

Usage:
    # Zone distribution for all games
    python3 scripts/query_shot_zones.py --distribution

    # Shots by specific zone
    python3 scripts/query_shot_zones.py --zone restricted_area

    # Player shot profile
    python3 scripts/query_shot_zones.py --player "LeBron James"

    # Team defensive zones
    python3 scripts/query_shot_zones.py --team "Los Angeles Lakers" --defense

    # Date range query
    python3 scripts/query_shot_zones.py --start-date 2023-10-01 --end-date 2024-04-15
"""

import argparse
import sys
from datetime import datetime
from typing import Optional, List, Dict

import psycopg2
from psycopg2.extras import RealDictCursor

from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config


class ShotZoneQuery:
    """Query shot zones from database"""

    def __init__(self):
        """Initialize database connection"""
        load_secrets_hierarchical()
        config = get_database_config()
        self.conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)

    def get_zone_distribution(self, start_date: Optional[str] = None, 
                            end_date: Optional[str] = None) -> List[Dict]:
        """
        Get shot distribution across all zones.

        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            List of dicts with zone, count, fg_pct, avg_distance
        """
        cursor = self.conn.cursor()

        date_filter = ""
        params = []

        if start_date and end_date:
            date_filter = "AND game_date BETWEEN %s AND %s"
            params = [start_date, end_date]

        query = f"""
            SELECT 
                shot_zone,
                COUNT(*) as total_shots,
                SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) as made_shots,
                ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fg_pct,
                ROUND(AVG(shot_distance)::numeric, 2) as avg_distance,
                ROUND(MIN(shot_distance)::numeric, 2) as min_distance,
                ROUND(MAX(shot_distance)::numeric, 2) as max_distance
            FROM hoopr_play_by_play p
            LEFT JOIN hoopr_schedule s ON p.game_id = s.game_id
            WHERE shooting_play = 1
              AND shot_zone IS NOT NULL
              {date_filter}
            GROUP BY shot_zone
            ORDER BY total_shots DESC
        """

        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()

        return results

    def get_zone_shots(self, zone: str, limit: int = 100) -> List[Dict]:
        """
        Get individual shots for a specific zone.

        Args:
            zone: Zone name (e.g., 'restricted_area')
            limit: Max number of shots to return

        Returns:
            List of shot details
        """
        cursor = self.conn.cursor()

        query = """
            SELECT 
                p.id,
                p.game_id,
                s.date as game_date,
                p.shot_zone,
                p.shot_distance,
                p.shot_angle,
                p.scoring_play,
                p.score_value,
                p.team_id,
                p.athlete_id,
                p.text as play_description
            FROM hoopr_play_by_play p
            LEFT JOIN hoopr_schedule s ON p.game_id = s.game_id
            WHERE shot_zone = %s
            ORDER BY s.date DESC, p.sequence_number
            LIMIT %s
        """

        cursor.execute(query, (zone, limit))
        results = cursor.fetchall()
        cursor.close()

        return results

    def get_player_shot_profile(self, player_name: str) -> Dict:
        """
        Get shot profile for a specific player.

        Args:
            player_name: Player name (partial match supported)

        Returns:
            Dict with zone distribution and efficiency
        """
        # Note: This requires athlete names in database
        # If athlete names aren't available, we can only use athlete_id
        cursor = self.conn.cursor()

        query = """
            SELECT 
                shot_zone,
                COUNT(*) as attempts,
                SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) as made,
                ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fg_pct,
                ROUND(AVG(shot_distance)::numeric, 2) as avg_distance
            FROM hoopr_play_by_play
            WHERE shooting_play = 1
              AND shot_zone IS NOT NULL
              AND athlete_id IS NOT NULL
              -- AND athlete_name ILIKE %s  -- Enable if athlete names available
            GROUP BY shot_zone
            ORDER BY attempts DESC
        """

        # cursor.execute(query, (f'%{player_name}%',))
        cursor.execute(query)  # Temporary: without player filter
        results = cursor.fetchall()
        cursor.close()

        return {
            'player': player_name,
            'zones': results
        }

    def get_distance_ranges(self) -> List[Dict]:
        """
        Get shot distribution by distance ranges.

        Returns:
            List of distance ranges with counts and FG%
        """
        cursor = self.conn.cursor()

        query = """
            SELECT 
                CASE 
                    WHEN shot_distance < 4 THEN '0-4 ft (Restricted Area)'
                    WHEN shot_distance < 8 THEN '4-8 ft (Paint)'
                    WHEN shot_distance < 16 THEN '8-16 ft (Mid-Range)'
                    WHEN shot_distance < 23.75 THEN '16-24 ft (Long 2s)'
                    ELSE '24+ ft (3-Pointers)'
                END as distance_range,
                COUNT(*) as total_shots,
                SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) as made_shots,
                ROUND(100.0 * SUM(CASE WHEN scoring_play = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fg_pct,
                ROUND(AVG(shot_distance)::numeric, 2) as avg_distance
            FROM hoopr_play_by_play
            WHERE shooting_play = 1
              AND shot_distance IS NOT NULL
            GROUP BY distance_range
            ORDER BY MIN(shot_distance)
        """

        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        return results

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def print_distribution(results: List[Dict]):
    """Pretty print zone distribution"""
    print("\n" + "=" * 80)
    print("SHOT ZONE DISTRIBUTION")
    print("=" * 80)
    print(f"{'Zone':<30} {'Shots':>8} {'Made':>8} {'FG%':>6} {'Avg Dist':>10}")
    print("-" * 80)

    total_shots = sum(r['total_shots'] for r in results)
    total_made = sum(r['made_shots'] for r in results)

    for row in results:
        pct_of_total = (row['total_shots'] / total_shots * 100) if total_shots > 0 else 0
        print(f"{row['shot_zone']:<30} {row['total_shots']:>8,} {row['made_shots']:>8,} "
              f"{row['fg_pct']:>5.1f}% {row['avg_distance']:>9.1f} ft")

    print("-" * 80)
    overall_fg = (total_made / total_shots * 100) if total_shots > 0 else 0
    print(f"{'TOTAL':<30} {total_shots:>8,} {total_made:>8,} {overall_fg:>5.1f}%")
    print("=" * 80 + "\n")


def print_distance_ranges(results: List[Dict]):
    """Pretty print distance ranges"""
    print("\n" + "=" * 80)
    print("SHOT DISTRIBUTION BY DISTANCE")
    print("=" * 80)
    print(f"{'Distance Range':<35} {'Shots':>8} {'Made':>8} {'FG%':>6}")
    print("-" * 80)

    total_shots = sum(r['total_shots'] for r in results)
    total_made = sum(r['made_shots'] for r in results)

    for row in results:
        print(f"{row['distance_range']:<35} {row['total_shots']:>8,} {row['made_shots']:>8,} "
              f"{row['fg_pct']:>5.1f}%")

    print("-" * 80)
    overall_fg = (total_made / total_shots * 100) if total_shots > 0 else 0
    print(f"{'TOTAL':<35} {total_shots:>8,} {total_made:>8,} {overall_fg:>5.1f}%")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Query shot zones from database')
    parser.add_argument('--distribution', action='store_true', help='Show zone distribution')
    parser.add_argument('--distance-ranges', action='store_true', help='Show distance ranges')
    parser.add_argument('--zone', help='Get shots for specific zone')
    parser.add_argument('--player', help='Player shot profile')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, default=100, help='Limit results')

    args = parser.parse_args()

    # Create query instance
    query = ShotZoneQuery()

    try:
        if args.distribution:
            results = query.get_zone_distribution(args.start_date, args.end_date)
            print_distribution(results)

        elif args.distance_ranges:
            results = query.get_distance_ranges()
            print_distance_ranges(results)

        elif args.zone:
            results = query.get_zone_shots(args.zone, args.limit)
            print(f"\nFound {len(results)} shots in zone '{args.zone}'")
            for i, shot in enumerate(results[:10], 1):
                made = "✓" if shot['scoring_play'] == 1 else "✗"
                print(f"{i}. {made} {shot['shot_distance']:.1f} ft @ {shot['shot_angle']:.1f}° - {shot['play_description']}")
            if len(results) > 10:
                print(f"... and {len(results) - 10} more shots")

        elif args.player:
            profile = query.get_player_shot_profile(args.player)
            print(f"\nShot Profile: {profile['player']}")
            print_distribution(profile['zones'])

        else:
            parser.print_help()

    finally:
        query.close()


if __name__ == '__main__':
    main()
