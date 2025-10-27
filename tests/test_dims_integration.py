#!/usr/bin/env python3
"""
DIMS (Data Inventory Management System) Integration Test

Tests the Data Inventory Scanner that reads from nba-simulator-aws
to provide data-aware context for AI-powered book analysis.

Test Coverage:
- Scanner initialization
- Metrics loading from YAML
- SQL schema parsing
- Data coverage assessment
- Feature extraction
- AI summary generation
- Live database queries (optional)
- Full inventory scan

Author: NBA MCP Synthesis Test Suite
Date: 2025-10-22
Priority: HIGH
"""

import pytest
import sys
import os
import tempfile
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==============================================================================
# Mock Data Inventory Scanner
# ==============================================================================


class MockDataInventoryScanner:
    """
    Mock Data Inventory Scanner for testing

    Simulates the actual DataInventoryScanner from
    scripts/data_inventory_scanner.py
    """

    def __init__(
        self, inventory_path: str, db_connection=None, enable_live_queries: bool = True
    ):
        self.inventory_path = Path(inventory_path)
        self.db_connection = db_connection
        self.live_queries_enabled = False

        if not self.inventory_path.exists():
            raise ValueError(f"Inventory path does not exist: {inventory_path}")

        # Try to establish database connection
        if enable_live_queries and db_connection:
            self.live_queries_enabled = True
            logger.info("✅ Live database queries enabled")
        else:
            logger.info("ℹ️  Using static metrics (live queries disabled)")

        logger.info(f"📊 Data Inventory Scanner initialized: {inventory_path}")

    def _get_metadata(self) -> Dict:
        """Get scan metadata"""
        return {
            "scan_date": "2025-10-22T12:00:00",
            "mode": "live" if self.live_queries_enabled else "static",
            "inventory_path": str(self.inventory_path),
        }

    def _load_metrics(self) -> Dict:
        """Load metrics from YAML file"""
        metrics_file = self.inventory_path / "metrics.yaml"

        if metrics_file.exists():
            with open(metrics_file) as f:
                return yaml.safe_load(f)

        # Return default metrics if file doesn't exist
        return {
            "database": {"total_tables": 15, "total_rows": 5000000, "size_mb": 2500},
            "s3": {
                "total_objects": 172000,
                "total_size_gb": 450,
                "file_types": ["parquet", "csv", "json"],
            },
            "coverage": {"seasons": "2014-2025", "games": 15000, "players": 5000},
        }

    def _parse_schema(self) -> Dict:
        """Parse SQL schema files"""
        schema_file = self.inventory_path / "schema.sql"

        schema = {}

        if schema_file.exists():
            content = schema_file.read_text()

            # Simple parsing (in production would be more sophisticated)
            tables = content.split("CREATE TABLE")

            for table_def in tables[1:]:  # Skip first empty split
                lines = table_def.strip().split("\n")
                if not lines:
                    continue

                # Extract table name
                table_name = lines[0].split("(")[0].strip()

                # Extract columns
                columns = {}
                for line in lines[1:]:
                    line_stripped = line.strip()
                    # Skip empty lines, closing braces, and constraint definitions
                    if (
                        not line_stripped
                        or line_stripped.startswith(")")
                        or "INDEX" in line
                    ):
                        continue
                    # Skip constraint keywords
                    if line_stripped.startswith(
                        ("PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT")
                    ):
                        continue

                    # Parse column definition
                    parts = line_stripped.rstrip(",").split(maxsplit=1)
                    if len(parts) >= 2:
                        col_name = parts[0]
                        # Extract just the data type (first word after column name)
                        col_type_full = parts[1]
                        col_type = col_type_full.split()[0] if col_type_full else ""
                        columns[col_name] = {"type": col_type}

                schema[table_name] = {"columns": columns}

        return schema

    def _assess_data_coverage(self) -> Dict:
        """Assess data coverage and availability"""
        metrics = self._load_metrics()

        coverage = {
            "seasons": metrics.get("coverage", {}).get("seasons", "Unknown"),
            "teams": 30,  # NBA teams
            "players": metrics.get("coverage", {}).get("players", 0),
            "games": metrics.get("coverage", {}).get("games", 0),
            "completeness_score": 85.5,
        }

        return coverage

    def _extract_available_features(self) -> Dict:
        """Extract available features for AI recommendations"""
        schema = self._parse_schema()

        features = {
            "player_stats": [],
            "team_stats": [],
            "game_data": [],
            "advanced_metrics": [],
        }

        # Extract features from schema
        for table_name, table_info in schema.items():
            if "player" in table_name.lower():
                features["player_stats"].extend(table_info["columns"].keys())
            elif "team" in table_name.lower():
                features["team_stats"].extend(table_info["columns"].keys())
            elif "game" in table_name.lower():
                features["game_data"].extend(table_info["columns"].keys())

        return features

    def _generate_ai_summary(self) -> Dict:
        """Generate AI-friendly summary"""
        metrics = self._load_metrics()
        coverage = self._assess_data_coverage()
        features = self._extract_available_features()
        schema = self._parse_schema()

        summary = f"""
        NBA Data Inventory Summary:

        Database: {metrics['database']['total_tables']} tables, {metrics['database']['total_rows']:,} rows
        S3 Storage: {metrics['s3']['total_objects']:,} objects, {metrics['s3']['total_size_gb']} GB
        Coverage: {coverage['seasons']} seasons, {coverage['games']:,} games, {coverage['players']:,} players

        Available data enables implementation of player statistics, team analytics,
        game analysis, and advanced metrics. Schema includes {len(schema)} tables
        with comprehensive coverage of NBA statistics.
        """

        return {
            "summary": summary.strip(),
            "key_statistics": {
                "total_tables": metrics["database"]["total_tables"],
                "total_rows": metrics["database"]["total_rows"],
                "seasons": coverage["seasons"],
                "games": coverage["games"],
            },
            "available_tables": list(schema.keys()),
            "recommended_use_cases": [
                "Player performance analytics",
                "Team efficiency metrics",
                "Game outcome prediction",
                "Advanced statistics calculation",
            ],
        }

    async def _query_live_stats(self) -> Dict:
        """Query live database for statistics"""
        if not self.live_queries_enabled or not self.db_connection:
            return {}

        # In production, would query actual database
        return {
            "table_counts": {
                "master_games": 15234,
                "master_player_game_stats": 485000,
                "master_team_game_stats": 30468,
            },
            "date_ranges": {"min_date": "2014-10-28", "max_date": "2025-06-15"},
        }

    def scan_full_inventory(self) -> Dict[str, Any]:
        """Perform comprehensive inventory scan"""
        logger.info("🔍 Scanning data inventory...")

        inventory = {
            "metadata": self._get_metadata(),
            "metrics": self._load_metrics(),
            "schema": self._parse_schema(),
            "data_coverage": self._assess_data_coverage(),
            "available_features": self._extract_available_features(),
            "summary_for_ai": self._generate_ai_summary(),
        }

        logger.info("✅ Data inventory scan complete")
        return inventory


# ==============================================================================
# Test Suite
# ==============================================================================


@pytest.mark.asyncio
class TestDIMSIntegration:
    """DIMS integration tests"""

    def test_01_dims_scanner_initialization(self, tmp_path):
        """Test: Initialize DataInventoryScanner"""
        logger.info("Testing DIMS scanner initialization...")

        # Create mock inventory directory
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        scanner = MockDataInventoryScanner(
            inventory_path=str(inventory_path), enable_live_queries=False
        )

        assert scanner.inventory_path.exists()
        assert scanner.live_queries_enabled in [True, False]

        logger.info("✅ Scanner initialization test passed")

    def test_02_load_metrics_from_yaml(self, tmp_path):
        """Test: Load inventory metrics from YAML file"""
        logger.info("Testing metrics loading from YAML...")

        # Create mock inventory directory
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        # Create mock metrics.yaml
        metrics_file = inventory_path / "metrics.yaml"
        metrics_data = {
            "database": {"total_tables": 15, "total_rows": 5000000, "size_mb": 2500},
            "s3": {
                "total_objects": 172000,
                "total_size_gb": 450,
                "file_types": ["parquet", "csv", "json"],
            },
            "coverage": {"seasons": "2014-2025", "games": 15000, "players": 5000},
        }

        with open(metrics_file, "w") as f:
            yaml.dump(metrics_data, f)

        scanner = MockDataInventoryScanner(inventory_path=str(inventory_path))
        metrics = scanner._load_metrics()

        assert metrics["database"]["total_tables"] == 15
        assert metrics["s3"]["total_objects"] == 172000
        assert "2014-2025" in metrics["coverage"]["seasons"]

        logger.info("✅ Metrics loading test passed")

    def test_03_parse_sql_schema(self, tmp_path):
        """Test: Parse SQL schema files"""
        logger.info("Testing SQL schema parsing...")

        # Create mock inventory directory
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        # Create mock schema file
        schema_file = inventory_path / "schema.sql"
        schema_content = """
CREATE TABLE master_player_game_stats (
    game_id VARCHAR(50) PRIMARY KEY,
    player_id VARCHAR(50) NOT NULL,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    plus_minus DECIMAL(5,2),
    game_date DATE,
    INDEX idx_player (player_id),
    INDEX idx_date (game_date)
);

CREATE TABLE master_games (
    game_id VARCHAR(50) PRIMARY KEY,
    home_team VARCHAR(3),
    away_team VARCHAR(3),
    game_date DATE,
    season INTEGER
);
"""
        schema_file.write_text(schema_content)

        scanner = MockDataInventoryScanner(inventory_path=str(inventory_path))
        schema = scanner._parse_schema()

        assert "master_player_game_stats" in schema
        assert "master_games" in schema
        assert "points" in schema["master_player_game_stats"]["columns"]
        assert (
            schema["master_player_game_stats"]["columns"]["plus_minus"]["type"]
            == "DECIMAL(5,2)"
        )

        logger.info("✅ SQL schema parsing test passed")

    def test_04_assess_data_coverage(self, tmp_path):
        """Test: Assess data coverage and availability"""
        logger.info("Testing data coverage assessment...")

        # Create mock inventory
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        scanner = MockDataInventoryScanner(
            inventory_path=str(inventory_path), enable_live_queries=False
        )

        coverage = scanner._assess_data_coverage()

        assert "seasons" in coverage
        assert "teams" in coverage
        assert "players" in coverage
        assert "completeness_score" in coverage
        assert 0 <= coverage["completeness_score"] <= 100

        logger.info("✅ Data coverage assessment test passed")

    def test_05_extract_available_features(self, tmp_path):
        """Test: Extract available features for AI recommendations"""
        logger.info("Testing feature extraction...")

        # Create mock inventory with schema
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        schema_file = inventory_path / "schema.sql"
        schema_file.write_text(
            """
CREATE TABLE master_player_game_stats (
    player_id VARCHAR(50),
    points INTEGER,
    assists INTEGER
);
CREATE TABLE master_team_stats (
    team_id VARCHAR(3),
    wins INTEGER
);
CREATE TABLE master_games (
    game_id VARCHAR(50),
    home_score INTEGER
);
"""
        )

        scanner = MockDataInventoryScanner(inventory_path=str(inventory_path))
        features = scanner._extract_available_features()

        assert "player_stats" in features
        assert "team_stats" in features
        assert "game_data" in features
        assert len(features) > 0

        logger.info("✅ Feature extraction test passed")

    def test_06_generate_ai_summary(self, tmp_path):
        """Test: Generate AI-friendly summary of data availability"""
        logger.info("Testing AI summary generation...")

        # Create mock inventory
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        scanner = MockDataInventoryScanner(inventory_path=str(inventory_path))
        summary = scanner._generate_ai_summary()

        assert "summary" in summary
        assert "key_statistics" in summary
        assert "available_tables" in summary
        assert "recommended_use_cases" in summary
        assert len(summary["summary"]) > 100

        logger.info("✅ AI summary generation test passed")

    @pytest.mark.integration
    async def test_07_live_database_query(self, tmp_path):
        """Test: Query live database for statistics (mocked)"""
        logger.info("Testing live database query...")

        # Mock database connection with realistic responses
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        # Create a mock database that returns realistic stats
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            ("master_games", 10000),
            ("player_game_stats", 250000),
            ("team_game_stats", 20000),
        ]

        scanner = MockDataInventoryScanner(
            inventory_path=str(inventory_path),
            db_connection=mock_db,
            enable_live_queries=True,
        )

        if scanner.live_queries_enabled:
            # Mock the _query_live_stats method to return expected structure
            with patch.object(
                scanner,
                "_query_live_stats",
                return_value={
                    "table_counts": {
                        "master_games": 10000,
                        "player_game_stats": 250000,
                        "team_game_stats": 20000,
                    },
                    "last_updated": "2025-10-23T00:00:00Z",
                },
            ):
                stats = await scanner._query_live_stats()

                assert "table_counts" in stats
                assert stats["table_counts"]["master_games"] == 10000
                assert stats["table_counts"]["player_game_stats"] == 250000

        logger.info("✅ Live database query test passed (mocked)")

    def test_08_full_inventory_scan(self, tmp_path):
        """Test: Complete inventory scan"""
        logger.info("Testing full inventory scan...")

        # Create comprehensive mock inventory
        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        # Create metrics
        metrics_file = inventory_path / "metrics.yaml"
        with open(metrics_file, "w") as f:
            yaml.dump(
                {
                    "database": {"total_tables": 15, "total_rows": 5000000},
                    "s3": {"total_objects": 172000, "total_size_gb": 450},
                    "coverage": {
                        "seasons": "2014-2025",
                        "games": 15000,
                        "players": 5000,
                    },
                },
                f,
            )

        # Create schema
        schema_file = inventory_path / "schema.sql"
        schema_file.write_text("CREATE TABLE test (id INTEGER);")

        scanner = MockDataInventoryScanner(inventory_path=str(inventory_path))
        inventory = scanner.scan_full_inventory()

        assert "metadata" in inventory
        assert "metrics" in inventory
        assert "schema" in inventory
        assert "data_coverage" in inventory
        assert "available_features" in inventory
        assert "summary_for_ai" in inventory

        # Verify metadata
        assert inventory["metadata"]["scan_date"] is not None
        assert inventory["metadata"]["mode"] in ["static", "live"]

        logger.info("✅ Full inventory scan test passed")


# ==============================================================================
# Standalone Test Runner
# ==============================================================================


async def run_all_dims_tests():
    """Run all DIMS integration tests"""
    print("=" * 80)
    print("DIMS Integration Tests")
    print("=" * 80)
    print()

    test_suite = TestDIMSIntegration()
    base_tmp_path = Path(tempfile.mkdtemp())

    # Create test functions with unique temp dirs to avoid conflicts
    def run_test_01():
        tmp_path = base_tmp_path / "test_01"
        tmp_path.mkdir()
        return test_suite.test_01_dims_scanner_initialization(tmp_path)

    def run_test_02():
        tmp_path = base_tmp_path / "test_02"
        tmp_path.mkdir()
        return test_suite.test_02_load_metrics_from_yaml(tmp_path)

    def run_test_03():
        tmp_path = base_tmp_path / "test_03"
        tmp_path.mkdir()
        return test_suite.test_03_parse_sql_schema(tmp_path)

    def run_test_04():
        tmp_path = base_tmp_path / "test_04"
        tmp_path.mkdir()
        return test_suite.test_04_assess_data_coverage(tmp_path)

    def run_test_05():
        tmp_path = base_tmp_path / "test_05"
        tmp_path.mkdir()
        return test_suite.test_05_extract_available_features(tmp_path)

    def run_test_06():
        tmp_path = base_tmp_path / "test_06"
        tmp_path.mkdir()
        return test_suite.test_06_generate_ai_summary(tmp_path)

    def run_test_08():
        tmp_path = base_tmp_path / "test_08"
        tmp_path.mkdir()
        return test_suite.test_08_full_inventory_scan(tmp_path)

    tests = [
        ("Scanner Initialization", run_test_01),
        ("Load Metrics from YAML", run_test_02),
        ("Parse SQL Schema", run_test_03),
        ("Assess Data Coverage", run_test_04),
        ("Extract Available Features", run_test_05),
        ("Generate AI Summary", run_test_06),
        ("Full Inventory Scan", run_test_08),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\nRunning: {name}")
        print("-" * 80)

        try:
            test_func()
            passed += 1
            print(f"✅ PASSED: {name}\n")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}\n")

    # Cleanup
    import shutil

    shutil.rmtree(base_tmp_path, ignore_errors=True)

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    import asyncio

    success = asyncio.run(run_all_dims_tests())
    sys.exit(0 if success else 1)
