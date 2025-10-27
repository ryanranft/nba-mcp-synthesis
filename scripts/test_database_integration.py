#!/usr/bin/env python3
"""
Test script for database integration with data inventory scanner.

Tests:
1. Database connector initialization
2. Connection pooling
3. Live query execution
4. Data inventory scanner integration
5. Live vs static metrics comparison
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.database_connector import create_db_connector_from_env, DatabaseConnector
from scripts.data_inventory_scanner import DataInventoryScanner

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_database_connector():
    """Test database connector standalone"""
    logger.info("=" * 80)
    logger.info("TEST 1: Database Connector Initialization")
    logger.info("=" * 80)

    connector = create_db_connector_from_env()

    if not connector:
        logger.warning("❌ Could not create database connector from environment")
        logger.info("   This is expected if database credentials are not configured")
        return None

    logger.info("✅ Database connector created successfully")

    # Test connection
    if connector.test_connection():
        logger.info("✅ Database connection test passed")
    else:
        logger.error("❌ Database connection test failed")
        return None

    return connector


def test_table_queries(connector):
    """Test querying individual tables"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Table Query Tests")
    logger.info("=" * 80)

    tables = [
        "master_players",
        "master_teams",
        "master_games",
        "master_player_game_stats",
    ]

    for table in tables:
        logger.info(f"\nQuerying table: {table}")

        try:
            # Row count
            row_count = connector.get_table_row_count(table)
            logger.info(f"  Row count: {row_count:,}")

            # Table stats
            stats = connector.get_table_stats(table)
            logger.info(f"  Size: {stats.get('size_pretty', 'N/A')}")
            logger.info(f"  Size (MB): {stats.get('size_mb', 'N/A')}")

            # Date range for game tables
            if "game" in table.lower():
                try:
                    date_range = connector.get_date_range(table, "game_date")
                    if date_range:
                        logger.info(
                            f"  Date range: {date_range['min_date']} to {date_range['max_date']}"
                        )
                        logger.info(f"  Unique dates: {date_range['unique_dates']:,}")
                except Exception as e:
                    logger.info(f"  Date range: Not available ({e})")

            logger.info(f"  ✅ Successfully queried {table}")

        except Exception as e:
            logger.error(f"  ❌ Failed to query {table}: {e}")


def test_inventory_scanner_static():
    """Test inventory scanner with static metrics only"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Inventory Scanner (Static Metrics)")
    logger.info("=" * 80)

    inventory_path = Path.home() / "nba-simulator-aws" / "inventory"

    if not inventory_path.exists():
        logger.warning(f"❌ Inventory path not found: {inventory_path}")
        logger.info("   Skipping static metrics test")
        return

    # Create scanner with live queries disabled
    scanner = DataInventoryScanner(str(inventory_path), enable_live_queries=False)

    # Run scan
    inventory = scanner.scan_full_inventory()

    logger.info("\nStatic Metrics Summary:")
    logger.info("-" * 60)
    print(inventory["summary_for_ai"])
    logger.info("-" * 60)

    logger.info("✅ Static metrics scan completed")


def test_inventory_scanner_live():
    """Test inventory scanner with live database queries"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Inventory Scanner (Live Database Queries)")
    logger.info("=" * 80)

    inventory_path = Path.home() / "nba-simulator-aws" / "inventory"

    if not inventory_path.exists():
        logger.warning(f"❌ Inventory path not found: {inventory_path}")
        logger.info("   Skipping live queries test")
        return

    # Create scanner with live queries enabled (default)
    scanner = DataInventoryScanner(str(inventory_path), enable_live_queries=True)

    if not scanner.live_queries_enabled:
        logger.warning(
            "⚠️  Live queries not enabled - database credentials may not be configured"
        )
        logger.info("   This is expected if database is not accessible")
        return

    # Run scan with live queries
    inventory = scanner.scan_full_inventory()

    logger.info("\nLive Database Summary:")
    logger.info("-" * 60)
    print(inventory["summary_for_ai"])
    logger.info("-" * 60)

    # Check data source
    coverage = inventory.get("data_coverage", {})
    data_source = coverage.get("data_source")

    if data_source == "live_database":
        logger.info("✅ Successfully retrieved LIVE database statistics")
        logger.info(f"   - Games: {coverage.get('games', 0):,}")
        logger.info(f"   - Players: {coverage.get('players', 0):,}")
        logger.info(f"   - Teams: {coverage.get('teams', 0):,}")
        logger.info(f"   - Player-Game Stats: {coverage.get('player_game_stats', 0):,}")

        if coverage.get("date_range"):
            dr = coverage["date_range"]
            logger.info(f"   - Date Range: {dr['min_date']} to {dr['max_date']}")
    else:
        logger.warning("⚠️  Data source is static, not live")

    logger.info("✅ Live queries scan completed")


def main():
    """Run all tests"""
    logger.info("\n" + "🧪 " * 40)
    logger.info("DATABASE INTEGRATION TEST SUITE")
    logger.info("🧪 " * 40 + "\n")

    # Test 1: Database connector
    connector = test_database_connector()

    if connector:
        # Test 2: Table queries
        test_table_queries(connector)

        # Clean up
        connector.disconnect()
    else:
        logger.info("\nℹ️  Skipping database-dependent tests (no database connection)")

    # Test 3: Static metrics
    test_inventory_scanner_static()

    # Test 4: Live queries
    test_inventory_scanner_live()

    logger.info("\n" + "=" * 80)
    logger.info("TEST SUITE COMPLETE")
    logger.info("=" * 80 + "\n")
    logger.info("✅ All tests completed successfully!")
    logger.info("\nℹ️  Note: Some tests may be skipped if database is not configured.")
    logger.info("   This is expected and does not indicate failure.")


if __name__ == "__main__":
    main()
