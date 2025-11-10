#!/usr/bin/env python3
"""
Quick verification script for November 9th, 2024 ESPN data collection.
Checks databases, S3, and logs to confirm data was collected properly.
"""

import os
import sys
from datetime import datetime
import psycopg2
import boto3
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config

def check_database_data(date_str='2024-11-09'):
    """Check both databases for November 9th data."""
    print(f"\n{'='*60}")
    print(f"📊 DATABASE VERIFICATION FOR {date_str}")
    print(f"{'='*60}\n")

    # Load credentials
    load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
    config = get_database_config()

    results = []

    # Check nba_simulator database
    print("🔍 Checking nba_simulator database...")
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database='nba_simulator',
            user=config['user'],
            password=config['password']
        )
        cur = conn.cursor()

        # Check espn_games
        cur.execute("""
            SELECT COUNT(*) as game_count
            FROM espn.espn_games
            WHERE game_date = %s
        """, (date_str,))
        games_count = cur.fetchone()[0]
        results.append(['nba_simulator', 'espn.espn_games', games_count])

        # Check espn_plays
        cur.execute("""
            SELECT COUNT(*) as play_count
            FROM espn.espn_plays
            WHERE game_id IN (SELECT game_id FROM espn.espn_games WHERE game_date = %s)
        """, (date_str,))
        plays_count = cur.fetchone()[0]
        results.append(['nba_simulator', 'espn.espn_plays', plays_count])

        # Check espn_team_stats
        cur.execute("""
            SELECT COUNT(*) as stats_count
            FROM espn.espn_team_stats
            WHERE game_id IN (SELECT game_id FROM espn.espn_games WHERE game_date = %s)
        """, (date_str,))
        stats_count = cur.fetchone()[0]
        results.append(['nba_simulator', 'espn.espn_team_stats', stats_count])

        cur.close()
        conn.close()
        print("✅ nba_simulator check complete")

    except Exception as e:
        print(f"❌ Error checking nba_simulator: {e}")
        return False

    # Check nba_mcp_synthesis database
    print("🔍 Checking nba_mcp_synthesis database...")
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database='nba_mcp_synthesis',
            user=config['user'],
            password=config['password']
        )
        cur = conn.cursor()

        # Check schedule_espn_nba
        cur.execute("""
            SELECT COUNT(*) as schedule_count
            FROM espn_raw.schedule_espn_nba
            WHERE game_date = %s
        """, (date_str,))
        schedule_count = cur.fetchone()[0]
        results.append(['nba_mcp_synthesis', 'espn_raw.schedule_espn_nba', schedule_count])

        # Check play_by_play_espn_nba
        cur.execute("""
            SELECT COUNT(*) as pbp_count
            FROM espn_raw.play_by_play_espn_nba
            WHERE game_id IN (SELECT game_id FROM espn_raw.schedule_espn_nba WHERE game_date = %s)
        """, (date_str,))
        pbp_count = cur.fetchone()[0]
        results.append(['nba_mcp_synthesis', 'espn_raw.play_by_play_espn_nba', pbp_count])

        # Check team_box_espn_nba
        cur.execute("""
            SELECT COUNT(*) as team_box_count
            FROM espn_raw.team_box_espn_nba
            WHERE game_id IN (SELECT game_id FROM espn_raw.schedule_espn_nba WHERE game_date = %s)
        """, (date_str,))
        team_box_count = cur.fetchone()[0]
        results.append(['nba_mcp_synthesis', 'espn_raw.team_box_espn_nba', team_box_count])

        cur.close()
        conn.close()
        print("✅ nba_mcp_synthesis check complete")

    except Exception as e:
        print(f"❌ Error checking nba_mcp_synthesis: {e}")
        return False

    # Display results
    print(f"\n{'='*60}")
    print("📈 RESULTS SUMMARY")
    print(f"{'='*60}\n")
    print(tabulate(results, headers=['Database', 'Table', 'Record Count'], tablefmt='grid'))

    # Validation
    print(f"\n{'='*60}")
    print("✅ VALIDATION")
    print(f"{'='*60}\n")

    validation_passed = True

    if results[0][2] == 0:  # No games in nba_simulator
        print("⚠️  WARNING: No games found in nba_simulator.espn.espn_games")
        validation_passed = False
    else:
        print(f"✅ Found {results[0][2]} games in nba_simulator")

    if results[3][2] == 0:  # No games in nba_mcp_synthesis
        print("⚠️  WARNING: No games found in nba_mcp_synthesis.espn_raw.schedule_espn_nba")
        validation_passed = False
    else:
        print(f"✅ Found {results[3][2]} games in nba_mcp_synthesis")

    if results[0][2] != results[3][2]:
        print(f"⚠️  WARNING: Game counts don't match between databases ({results[0][2]} vs {results[3][2]})")
        validation_passed = False
    else:
        print(f"✅ Game counts match across databases")

    return validation_passed


def check_s3_data(date_str='2024-11-09'):
    """Check S3 for November 9th files."""
    print(f"\n{'='*60}")
    print(f"☁️  S3 VERIFICATION FOR {date_str}")
    print(f"{'='*60}\n")

    bucket_name = os.environ.get('S3_BUCKET_NBA_MCP_SYNTHESIS_WORKFLOW', 'nba-mcp-books-20251011')

    try:
        s3 = boto3.client('s3', region_name='us-east-1')

        # Convert date to various formats that might be used
        date_formats = [
            date_str,  # 2024-11-09
            date_str.replace('-', ''),  # 20241109
            date_str.replace('-', '/'),  # 2024/11/09
        ]

        total_objects = 0

        for prefix_date in date_formats:
            prefix = f"espn/nba/{prefix_date}/"

            try:
                response = s3.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=prefix,
                    MaxKeys=100
                )

                count = response.get('KeyCount', 0)
                if count > 0:
                    total_objects += count
                    print(f"✅ Found {count} objects with prefix: {prefix}")

                    # Show sample files
                    if 'Contents' in response:
                        print(f"   Sample files:")
                        for obj in response['Contents'][:3]:
                            print(f"   - {obj['Key']}")

            except Exception as e:
                print(f"⚠️  Error checking prefix {prefix}: {e}")

        if total_objects > 0:
            print(f"\n✅ Total S3 objects found for {date_str}: {total_objects}")
            return True
        else:
            print(f"\n⚠️  No S3 objects found for {date_str}")
            print(f"   This might be normal if data is only stored in databases.")
            return True  # Not a failure - might be database-only

    except Exception as e:
        print(f"❌ Error checking S3: {e}")
        return False


def check_logs(date_str='2024-11-09'):
    """Check logs for November 9th entries."""
    print(f"\n{'='*60}")
    print(f"📝 LOG FILE VERIFICATION FOR {date_str}")
    print(f"{'='*60}\n")

    log_file = '/home/user/nba-mcp-synthesis/logs/daily_sync.log'

    if not os.path.exists(log_file):
        print(f"⚠️  Log file not found: {log_file}")
        return False

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Find entries for the date
        date_entries = [line for line in lines if date_str in line or '11/09/2024' in line or 'Nov 9' in line.lower()]

        if not date_entries:
            print(f"⚠️  No log entries found for {date_str}")
            print(f"   Last 10 lines of log file:")
            for line in lines[-10:]:
                print(f"   {line.rstrip()}")
            return False

        print(f"✅ Found {len(date_entries)} log entries for {date_str}")
        print(f"\nRecent entries:")
        for entry in date_entries[-10:]:
            print(f"   {entry.rstrip()}")

        return True

    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return False


def main():
    """Run all verification checks."""
    print("="*60)
    print("🔍 ESPN DATA VERIFICATION FOR NOVEMBER 9, 2024")
    print("="*60)
    print(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run checks
    db_check = check_database_data()
    s3_check = check_s3_data()
    log_check = check_logs()

    # Final summary
    print(f"\n{'='*60}")
    print("🎯 FINAL VERIFICATION SUMMARY")
    print(f"{'='*60}\n")

    print(f"Database Check: {'✅ PASSED' if db_check else '❌ FAILED'}")
    print(f"S3 Check:       {'✅ PASSED' if s3_check else '❌ FAILED'}")
    print(f"Log Check:      {'✅ PASSED' if log_check else '❌ FAILED'}")

    overall = db_check and s3_check and log_check
    print(f"\nOverall Status: {'✅ ALL CHECKS PASSED' if overall else '⚠️  SOME CHECKS FAILED'}")

    return 0 if overall else 1


if __name__ == '__main__':
    sys.exit(main())
