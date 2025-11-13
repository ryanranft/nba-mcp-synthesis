#!/usr/bin/env python3
"""
Database Credentials Test Script

Tests that database credentials are properly configured in the hierarchical
secrets management system and can successfully connect to the PostgreSQL database.

Usage:
    python scripts/test_database_credentials.py
    python scripts/test_database_credentials.py --context production
    python scripts/test_database_credentials.py --context development
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


def test_secrets_loading(context: str) -> Dict[str, Any]:
    """Test that secrets can be loaded from the hierarchical system."""
    print(f"\n{'='*70}")
    print(f"Test 1: Loading Secrets ({context} context)")
    print("=" * 70)

    try:
        load_secrets_hierarchical("nba-mcp-synthesis", "NBA", context)
        print("✓ load_secrets_hierarchical() succeeded")
    except Exception as e:
        print(f"❌ Failed to load secrets: {e}")
        return {"success": False, "error": str(e)}

    try:
        config = get_database_config()
        print("✓ get_database_config() succeeded")
    except Exception as e:
        print(f"❌ Failed to get database config: {e}")
        return {"success": False, "error": str(e)}

    # Check for missing credentials
    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"❌ Missing credentials: {missing}")
        return {"success": False, "error": f"Missing: {missing}", "config": config}

    # Display loaded credentials (masked)
    print("\nLoaded credentials:")
    print(
        f"  Host: {config['host'][:30]}..."
        if len(config["host"]) > 30
        else f"  Host: {config['host']}"
    )
    print(f"  Port: {config['port']}")
    print(f"  Database: {config['database']}")
    print(f"  User: {config['user']}")
    print(f"  Password: {'*' * 10} ({len(config['password'])} chars)")

    return {"success": True, "config": config}


def test_database_connection(config: Dict[str, str]) -> Dict[str, Any]:
    """Test that we can connect to the database."""
    print(f"\n{'='*70}")
    print("Test 2: Database Connection")
    print("=" * 70)

    if not HAS_PSYCOPG2:
        print("❌ psycopg2 not installed")
        print("   Install with: pip install psycopg2-binary")
        return {"success": False, "error": "psycopg2 not installed"}

    try:
        print("Attempting connection...")
        conn = psycopg2.connect(**config)
        print("✓ Connection established")

        # Test that we can execute a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ Database version: {version[:50]}...")

        cursor.close()
        conn.close()
        print("✓ Connection closed successfully")

        return {"success": True, "version": version}

    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that database server is running")
        print("  2. Verify network connectivity to host")
        print("  3. Check security groups/firewall rules")
        print("  4. Confirm credentials are correct")
        return {"success": False, "error": str(e)}

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"success": False, "error": str(e)}


def test_data_access(config: Dict[str, str]) -> Dict[str, Any]:
    """Test that we can query NBA data from the database."""
    print(f"\n{'='*70}")
    print("Test 3: NBA Data Access")
    print("=" * 70)

    if not HAS_PSYCOPG2:
        return {"success": False, "error": "psycopg2 not installed"}

    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check games table
        cursor.execute(
            """
            SELECT COUNT(*) as total_games,
                   COUNT(DISTINCT season) as seasons,
                   MIN(game_date) as earliest_game,
                   MAX(game_date) as latest_game
            FROM games
        """
        )
        games_stats = cursor.fetchone()
        print(f"✓ Games table accessible")
        print(f"  Total games: {games_stats['total_games']:,}")
        print(f"  Seasons: {games_stats['seasons']}")
        print(
            f"  Date range: {games_stats['earliest_game']} to {games_stats['latest_game']}"
        )

        # Check team_game_stats table
        cursor.execute("SELECT COUNT(*) FROM team_game_stats")
        tgs_count = cursor.fetchone()[0]
        print(f"✓ Team game stats table accessible")
        print(f"  Records: {tgs_count:,}")

        # Get sample data
        cursor.execute(
            """
            SELECT season, COUNT(*) as games
            FROM games
            GROUP BY season
            ORDER BY season DESC
            LIMIT 5
        """
        )
        seasons = cursor.fetchall()
        print("\nRecent seasons:")
        for row in seasons:
            print(f"  {row['season']}: {row['games']} games")

        cursor.close()
        conn.close()

        return {
            "success": True,
            "total_games": games_stats["total_games"],
            "seasons": games_stats["seasons"],
        }

    except psycopg2.ProgrammingError as e:
        print(f"❌ Query failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that required tables exist (games, team_game_stats)")
        print("  2. Verify database schema is correctly loaded")
        return {"success": False, "error": str(e)}

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"success": False, "error": str(e)}


def print_summary(results: Dict[str, Dict[str, Any]]):
    """Print final test summary."""
    print(f"\n{'='*70}")
    print("Test Summary")
    print("=" * 70)

    all_passed = all(r["success"] for r in results.values())

    for test_name, result in results.items():
        status = "✓ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result["success"] and "error" in result:
            print(f"     Error: {result['error']}")

    print()
    if all_passed:
        print("🎉 All tests passed!")
        print("\nYour database credentials are properly configured.")
        print("You can now run the calibration training pipeline:")
        print("  ./run_calibration_pipeline.sh")
    else:
        print("⚠️  Some tests failed")
        print("\nPlease review the errors above and:")
        print("  1. Check .claude/claude.md for configuration instructions")
        print("  2. Verify credentials are in the correct location")
        print("  3. Ensure database server is accessible")

    print("=" * 70)
    print()

    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(
        description="Test database credentials configuration"
    )
    parser.add_argument(
        "--context",
        choices=["production", "development"],
        default="production",
        help="Secrets context to test (default: production)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("NBA MCP Synthesis - Database Credentials Test")
    print("=" * 70)
    print(f"\nContext: {args.context}")
    print("Secrets System: Hierarchical")
    print()

    # Run tests
    results = {}

    # Test 1: Secrets loading
    result1 = test_secrets_loading(args.context)
    results["Secrets Loading"] = result1

    if not result1["success"]:
        print("\n❌ Cannot proceed without valid credentials")
        print("\nRefer to documentation:")
        print("  - .claude/claude.md")
        print("  - .env.template (deprecation notice with instructions)")
        print(
            "  - /Users/ryanranft/Desktop/++/big_cat_bets_assets/SECRETS_STRUCTURE.md"
        )
        return 1

    # Test 2: Database connection
    config = result1["config"]
    result2 = test_database_connection(config)
    results["Database Connection"] = result2

    if not result2["success"]:
        print("\n❌ Cannot test data access without database connection")
        return print_summary(results)

    # Test 3: Data access
    result3 = test_data_access(config)
    results["NBA Data Access"] = result3

    # Print summary
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
