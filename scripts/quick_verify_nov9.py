#!/usr/bin/env python3
"""
Simplified November 9th verification - just the essentials.
Run this in your production environment with database access.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install psycopg2-binary")
    sys.exit(1)


def check_data(date_str='2024-11-09'):
    """Quick check for a specific date."""

    print("=" * 60)
    print(f"🔍 QUICK CHECK FOR {date_str}")
    print("=" * 60)
    print()

    # Load credentials
    try:
        load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
        config = get_database_config()
        print("✅ Credentials loaded")
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        return False

    # Check both databases
    databases = [
        ('nba_simulator', 'espn.espn_games', 'espn.espn_plays'),
        ('nba_mcp_synthesis', 'espn_raw.schedule_espn_nba', 'espn_raw.play_by_play_espn_nba')
    ]

    results = {}

    for db_name, games_table, plays_table in databases:
        print(f"\n📊 Checking {db_name}...")

        try:
            # Connect
            conn_config = config.copy()
            conn_config['database'] = db_name
            conn = psycopg2.connect(**conn_config)
            cur = conn.cursor()

            # Count games
            cur.execute(f"""
                SELECT COUNT(*) FROM {games_table}
                WHERE game_date = %s
            """, (date_str,))
            games_count = cur.fetchone()[0]

            # Count plays
            cur.execute(f"""
                SELECT COUNT(*) FROM {plays_table}
                WHERE game_id IN (
                    SELECT game_id FROM {games_table}
                    WHERE game_date = %s
                )
            """, (date_str,))
            plays_count = cur.fetchone()[0]

            results[db_name] = {
                'games': games_count,
                'plays': plays_count
            }

            print(f"  Games: {games_count}")
            print(f"  Plays: {plays_count}")

            if games_count > 0:
                print(f"  ✅ Data found")
            else:
                print(f"  ⚠️  No data found")

            cur.close()
            conn.close()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[db_name] = {'error': str(e)}

    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)

    if 'nba_simulator' in results and 'games' in results['nba_simulator']:
        sim_games = results['nba_simulator']['games']
        mcp_games = results.get('nba_mcp_synthesis', {}).get('games', 0)

        if sim_games > 0 and mcp_games > 0:
            print(f"\n✅ SUCCESS!")
            print(f"   • nba_simulator: {sim_games} games")
            print(f"   • nba_mcp_synthesis: {mcp_games} games")

            if sim_games == mcp_games:
                print(f"   • Databases are in sync ✓")
            else:
                print(f"   • ⚠️  Database counts don't match")

        elif sim_games == 0:
            print(f"\n⚠️  NO DATA FOUND for {date_str}")
            print(f"\nPossible reasons:")
            print(f"   1. No games were scheduled on {date_str}")
            print(f"   2. Overnight collection hasn't run yet")
            print(f"   3. Collection failed (check logs)")
            print(f"\nTo collect manually:")
            print(f"   python scripts/espn_incremental_scraper.py --start-date {date_str} --end-date {date_str}")

        else:
            print(f"\n⚠️  PARTIAL DATA")
            print(f"   Some databases have data, others don't")

    else:
        print("\n❌ UNABLE TO VERIFY")
        print("   Database connection issues")

    print()
    return True


if __name__ == '__main__':
    date = sys.argv[1] if len(sys.argv) > 1 else '2024-11-09'
    check_data(date)
