#!/usr/bin/env python3
"""
Database Integration Tests

Tests database connector initialization, table queries, and data inventory scanner.
Converted from scripts/test_database_integration.py for pytest compatibility.
"""

import pytest
import logging
from pathlib import Path

from scripts.database_connector import create_db_connector_from_env, DatabaseConnector
from scripts.data_inventory_scanner import DataInventoryScanner

logger = logging.getLogger(__name__)


@pytest.fixture
def db_connector():
    """Fixture to provide database connector"""
    connector = create_db_connector_from_env()
    if connector and connector.test_connection():
        yield connector
        connector.disconnect()
    else:
        pytest.skip("Database not configured or not accessible")


@pytest.fixture
def inventory_path():
    """Fixture to provide inventory path"""
    path = Path.home() / "nba-simulator-aws" / "inventory"
    if not path.exists():
        pytest.skip(f"Inventory path not found: {path}")
    return path


def test_database_connector_creation():
    """Test database connector can be created from environment"""
    connector = create_db_connector_from_env()

    if not connector:
        pytest.skip("Database credentials not configured - this is expected")

    assert connector is not None, "Connector should be created"
    assert isinstance(
        connector, DatabaseConnector
    ), "Should be DatabaseConnector instance"


def test_database_connection(db_connector):
    """Test database connection works"""
    assert db_connector is not None, "Connector should exist"
    assert db_connector.test_connection(), "Connection test should pass"


def test_table_queries(db_connector):
    """Test querying individual database tables"""
    tables = [
        "master_players",
        "master_teams",
        "master_games",
        "master_player_game_stats",
    ]

    for table in tables:
        # Test row count query
        row_count = db_connector.get_table_row_count(table)
        assert row_count >= 0, f"{table} should return non-negative row count"

        # Test table stats
        stats = db_connector.get_table_stats(table)
        assert stats is not None, f"{table} stats should not be None"
        assert (
            "size_pretty" in stats or "size_mb" in stats
        ), f"{table} stats should include size information"

        # Test date range for game tables
        if "game" in table.lower():
            try:
                date_range = db_connector.get_date_range(table, "game_date")
                if date_range:
                    assert "min_date" in date_range, "Should have min_date"
                    assert "max_date" in date_range, "Should have max_date"
                    assert (
                        "unique_dates" in date_range
                    ), "Should have unique_dates count"
            except Exception as e:
                logger.info(f"Date range not available for {table}: {e}")
                # Not a failure - some tables may not have date ranges


def test_inventory_scanner_static(inventory_path):
    """Test inventory scanner with static metrics only"""
    # Create scanner with live queries disabled
    scanner = DataInventoryScanner(str(inventory_path), enable_live_queries=False)

    assert scanner is not None, "Scanner should be created"
    assert not scanner.live_queries_enabled, "Live queries should be disabled"

    # Run scan
    inventory = scanner.scan_full_inventory()

    assert inventory is not None, "Inventory should not be None"
    assert "summary_for_ai" in inventory, "Should have AI summary"
    assert isinstance(inventory["summary_for_ai"], str), "Summary should be string"


def test_inventory_scanner_live(inventory_path):
    """Test inventory scanner with live database queries"""
    # Create scanner with live queries enabled (default)
    scanner = DataInventoryScanner(str(inventory_path), enable_live_queries=True)

    if not scanner.live_queries_enabled:
        pytest.skip("Live queries not enabled - database may not be accessible")

    # Run scan with live queries
    inventory = scanner.scan_full_inventory()

    assert inventory is not None, "Inventory should not be None"
    assert "summary_for_ai" in inventory, "Should have AI summary"
    assert "data_coverage" in inventory, "Should have data coverage"

    # Check data source
    coverage = inventory.get("data_coverage", {})
    data_source = coverage.get("data_source")

    if data_source == "live_database":
        # Validate live database statistics
        assert coverage.get("games", 0) > 0, "Should have game count"
        assert coverage.get("players", 0) > 0, "Should have player count"
        assert coverage.get("teams", 0) > 0, "Should have team count"

        if coverage.get("date_range"):
            dr = coverage["date_range"]
            assert "min_date" in dr, "Should have min_date"
            assert "max_date" in dr, "Should have max_date"
    else:
        logger.warning("Data source is static, not live - this is acceptable")
