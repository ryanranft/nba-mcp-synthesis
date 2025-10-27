"""
Data Inventory Scanner for NBA Analytics Project

This module scans the Data Inventory Management System (DIMS) from nba-simulator-aws
and extracts comprehensive data availability information for AI-powered book analysis.

Features:
- Reads inventory metrics.yaml for data statistics
- Parses SQL schemas for table structures
- Queries PostgreSQL for live data coverage
- Generates data-aware context for AI recommendations
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

# Import database connector for live queries
try:
    from scripts.database_connector import (
        DatabaseConnector,
        create_db_connector_from_env,
    )

    DB_CONNECTOR_AVAILABLE = True
except ImportError:
    DB_CONNECTOR_AVAILABLE = False
    logging.warning("⚠️  Database connector not available - using static metrics only")

logger = logging.getLogger(__name__)


class DataInventoryScanner:
    """
    Scans DIMS inventory to provide data-aware context for book analysis.

    This enables AI models to make specific, data-driven recommendations like:
    - "Use master_player_game_stats.plus_minus for win probability modeling"
    - "Leverage the 172k S3 objects of play-by-play data for sequence analysis"
    - "Build features from master_games table covering 2014-2025 seasons"
    """

    def __init__(
        self,
        inventory_path: str,
        db_connection: Optional[Any] = None,
        enable_live_queries: bool = True,
    ):
        """
        Initialize Data Inventory Scanner

        Args:
            inventory_path: Path to inventory/ directory in nba-simulator-aws
            db_connection: Optional database connection for live queries
            enable_live_queries: Try to connect to database for live statistics
        """
        self.inventory_path = Path(inventory_path)
        self.db_connection = db_connection
        self.live_queries_enabled = False

        if not self.inventory_path.exists():
            raise ValueError(f"Inventory path does not exist: {inventory_path}")

        # Try to establish database connection for live queries
        if enable_live_queries and DB_CONNECTOR_AVAILABLE and not db_connection:
            logger.info("🔌 Attempting to connect to database for live queries...")
            try:
                self.db_connection = create_db_connector_from_env()
                if self.db_connection:
                    self.live_queries_enabled = True
                    logger.info("✅ Live database queries enabled")
                else:
                    logger.info(
                        "ℹ️  Database credentials not found - using static metrics"
                    )
            except Exception as e:
                logger.warning(f"⚠️  Failed to connect to database: {e}")
                logger.info("ℹ️  Falling back to static metrics")

        logger.info(f"📊 Data Inventory Scanner initialized: {inventory_path}")
        if self.live_queries_enabled:
            logger.info("   Mode: LIVE QUERIES (real-time data)")
        else:
            logger.info("   Mode: STATIC METRICS (cached data)")

    def scan_full_inventory(self) -> Dict[str, Any]:
        """
        Perform comprehensive inventory scan

        Returns:
            Dict with data availability, schema, metrics, and coverage
        """
        logger.info("🔍 Scanning data inventory...")

        inventory = {
            "metadata": self._get_metadata(),
            "metrics": self._load_metrics(),
            "schema": self._parse_schema(),
            "data_coverage": self._assess_data_coverage(),
            "available_features": self._extract_available_features(),
            "system_capabilities": self._analyze_system_capabilities(),
            "summary_for_ai": self._generate_ai_summary(),
        }

        logger.info("✅ Data inventory scan complete")
        return inventory

    def _get_metadata(self) -> Dict[str, Any]:
        """Get inventory metadata"""
        config_file = self.inventory_path / "config.yaml"

        if config_file.exists():
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
            return {
                "system": config.get("system", "DIMS"),
                "version": config.get("version", "1.0.0"),
                "last_updated": config.get("last_updated", "Unknown"),
                "backend": config.get("backend", {}).get("type", "PostgreSQL"),
            }

        return {
            "system": "DIMS",
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "backend": "PostgreSQL",
        }

    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from metrics.yaml"""
        metrics_file = self.inventory_path / "metrics.yaml"

        if not metrics_file.exists():
            logger.warning(f"⚠️  Metrics file not found: {metrics_file}")
            return {}

        with open(metrics_file, "r") as f:
            metrics = yaml.safe_load(f)

        logger.info(f"📊 Loaded metrics: {len(metrics)} categories")
        return metrics

    def _parse_schema(self) -> Dict[str, Any]:
        """Parse SQL schema files to extract table structures"""
        # Check for master_schema.sql in parent directory
        schema_file = self.inventory_path.parent / "sql" / "master_schema.sql"

        if not schema_file.exists():
            logger.warning(f"⚠️  Schema file not found: {schema_file}")
            return {}

        with open(schema_file, "r") as f:
            schema_sql = f.read()

        # Extract table definitions
        tables = self._extract_tables_from_sql(schema_sql)

        logger.info(f"📋 Parsed schema: {len(tables)} tables")
        return {
            "source_file": str(schema_file),
            "tables": tables,
            "total_tables": len(tables),
        }

    def _extract_tables_from_sql(self, sql: str) -> Dict[str, Dict]:
        """Extract table structures from SQL CREATE TABLE statements"""
        tables = {}

        # Find all CREATE TABLE statements
        table_pattern = re.compile(
            r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)\s*\((.*?)\);",
            re.DOTALL | re.IGNORECASE,
        )

        for match in table_pattern.finditer(sql):
            table_name = match.group(1)
            columns_sql = match.group(2)

            # Extract column definitions
            columns = []
            column_pattern = re.compile(
                r"(\w+)\s+([\w\(\)]+)(?:\s+(PRIMARY KEY|NOT NULL|UNIQUE))*"
            )

            for col_match in column_pattern.finditer(columns_sql):
                col_name = col_match.group(1)
                col_type = col_match.group(2)

                # Skip constraint keywords
                if col_name.upper() in ["PRIMARY", "FOREIGN", "CONSTRAINT", "INDEX"]:
                    continue

                columns.append(
                    {
                        "name": col_name,
                        "type": col_type,
                    }
                )

            tables[table_name] = {
                "columns": columns,
                "column_count": len(columns),
                "column_names": [c["name"] for c in columns],
            }

        # Add known table metadata from documentation
        table_metadata = {
            "master_players": {
                "type": "dimension",
                "description": "Unified player dimension with biographical data",
                "primary_key": "player_id",
            },
            "master_teams": {
                "type": "dimension",
                "description": "Unified team dimension",
                "primary_key": "team_id",
            },
            "master_games": {
                "type": "fact",
                "description": "Game-level fact table",
                "primary_key": "game_id",
            },
            "master_player_game_stats": {
                "type": "fact",
                "description": "Player performance panel data (game-level)",
                "primary_key": ["game_id", "player_id"],
                "key_metrics": [
                    "points",
                    "rebounds",
                    "assists",
                    "plus_minus",
                    "minutes_played",
                ],
            },
        }

        # Merge metadata
        for table_name, metadata in table_metadata.items():
            if table_name in tables:
                tables[table_name].update(metadata)

        return tables

    def _query_live_database_stats(self) -> Optional[Dict[str, Any]]:
        """Query database for live statistics"""
        if not self.live_queries_enabled or not self.db_connection:
            return None

        logger.info("🔍 Querying database for live statistics...")

        live_stats = {
            "data_source": "live_database",
            "query_timestamp": datetime.now().isoformat(),
            "tables": {},
        }

        # Define tables to query
        tables_to_query = {
            "master_players": "player_id",
            "master_teams": "team_id",
            "master_games": "game_id",
            "master_player_game_stats": None,  # Composite key
        }

        for table_name, id_column in tables_to_query.items():
            try:
                # Get row count
                row_count = self.db_connection.get_table_row_count(table_name)

                # Get table stats
                table_stats = self.db_connection.get_table_stats(table_name)

                # Get date range if this is a game-related table
                date_range = None
                if "game" in table_name.lower():
                    try:
                        date_range = self.db_connection.get_date_range(
                            table_name, "game_date"
                        )
                    except:
                        pass  # Not all tables have game_date

                live_stats["tables"][table_name] = {
                    "row_count": row_count,
                    "size_bytes": table_stats.get("size_bytes"),
                    "size_mb": table_stats.get("size_mb"),
                    "size_pretty": table_stats.get("size_pretty"),
                    "date_range": date_range,
                }

                logger.info(f"   ✅ {table_name}: {row_count:,} rows")

            except Exception as e:
                logger.warning(f"   ⚠️  Failed to query {table_name}: {e}")
                live_stats["tables"][table_name] = {"error": str(e)}

        return live_stats

    def _assess_data_coverage(self) -> Dict[str, Any]:
        """Assess data coverage from live database or metrics"""

        # Try live database first
        live_stats = self._query_live_database_stats()

        if live_stats:
            # Use live database statistics
            tables = live_stats.get("tables", {})

            coverage = {
                "data_source": "live_database",
                "query_timestamp": live_stats.get("query_timestamp"),
                "games": tables.get("master_games", {}).get("row_count", 0),
                "players": tables.get("master_players", {}).get("row_count", 0),
                "teams": tables.get("master_teams", {}).get("row_count", 0),
                "player_game_stats": tables.get("master_player_game_stats", {}).get(
                    "row_count", 0
                ),
            }

            # Add date range if available
            games_table = tables.get("master_games", {})
            date_range = games_table.get("date_range")
            if date_range:
                coverage["date_range"] = {
                    "min_date": date_range.get("min_date"),
                    "max_date": date_range.get("max_date"),
                    "unique_dates": date_range.get("unique_dates"),
                }
                coverage["seasons"] = (
                    f"{date_range.get('min_date', '?')[:4]}-{date_range.get('max_date', '?')[:4]}"
                )

            # Add table sizes
            total_size_mb = sum(
                t.get("size_mb", 0)
                for t in tables.values()
                if isinstance(t.get("size_mb"), (int, float))
            )
            coverage["database_size_mb"] = round(total_size_mb, 2)
            coverage["database_size_gb"] = round(total_size_mb / 1024, 2)

            logger.info(
                f"✅ Live data coverage: {coverage['games']:,} games, {coverage['players']:,} players"
            )

        else:
            # Fall back to static metrics
            metrics = self._load_metrics()
            s3_storage = metrics.get("s3_storage", {})

            coverage = {
                "data_source": "static_metrics",
                "s3_objects": s3_storage.get("total_objects", {}).get("value", 0),
                "s3_size_gb": s3_storage.get("total_size_gb", {}).get("value", 0.0),
                "hoopr_files": s3_storage.get("hoopr_files", {}).get("value", 0),
                "seasons_estimated": "2014-2025 (estimated from commit history)",
                "games_estimated": "15000+ games (estimated)",
                "players_estimated": "5000+ players (estimated)",
            }

            # Add local data info
            local_data = metrics.get("local_data", {})
            if local_data:
                coverage["local_espn_size_gb"] = local_data.get("espn_size_gb", {}).get(
                    "value", 0
                )

        return coverage

    def _extract_available_features(self) -> List[str]:
        """Extract list of available data features for AI recommendations"""
        schema = self._parse_schema()
        tables = schema.get("tables", {})

        features = []

        # Panel data features
        if "master_player_game_stats" in tables:
            stats_cols = tables["master_player_game_stats"].get("column_names", [])
            features.extend(
                [
                    f"Player game-level stat: {col}"
                    for col in stats_cols
                    if col not in ["game_id", "player_id"]
                ]
            )

        # Dimension features
        if "master_players" in tables:
            features.append(
                "Player biographical data (height, weight, position, birth_date)"
            )

        if "master_teams" in tables:
            features.append("Team organizational data (conference, division, arena)")

        # System features
        features.extend(
            [
                "Plus/Minus calculation system (4,619 lines of code)",
                "Game outcome prediction models",
                "Player performance prediction models",
                "Play-by-play event sequences (172k S3 objects)",
            ]
        )

        return features

    def _analyze_system_capabilities(self) -> Dict[str, Any]:
        """Analyze what the system can currently do"""
        metrics = self._load_metrics()

        prediction_system = metrics.get("prediction_system", {})
        plus_minus_system = metrics.get("plus_minus_system", {})

        return {
            "prediction_system": {
                "available": bool(prediction_system),
                "total_lines": prediction_system.get("total_lines", {}).get("value", 0),
                "scripts": [
                    "fetch_upcoming_games",
                    "fetch_recent_player_data",
                    "prepare_upcoming_game_features",
                    "predict_upcoming_games",
                    "train_model_for_predictions",
                ],
            },
            "plus_minus_system": {
                "available": bool(plus_minus_system),
                "total_lines": plus_minus_system.get("total_lines", {}).get("value", 0),
                "components": plus_minus_system.get("total_lines", {}).get(
                    "components", {}
                ),
                "capabilities": [
                    "Calculate player plus/minus from play-by-play",
                    "Populate plus_minus tables in PostgreSQL",
                    "Track on-court impact for all players",
                ],
            },
            "data_pipeline": {
                "available": True,
                "s3_storage": True,
                "postgresql_backend": True,
                "local_cache": True,
            },
        }

    def _generate_ai_summary(self) -> str:
        """Generate human-readable summary for AI prompt context"""
        metrics = self._load_metrics()
        schema = self._parse_schema()
        coverage = self._assess_data_coverage()

        # Determine data source
        data_source = coverage.get("data_source", "static_metrics")
        is_live = data_source == "live_database"

        # Build coverage section based on data source
        if is_live:
            coverage_section = f"""**Data Coverage** (🔴 LIVE from database - {coverage.get('query_timestamp', 'N/A')[:19]}):
- {coverage.get('games', 0):,} games in master_games table
- {coverage.get('players', 0):,} players in master_players table
- {coverage.get('teams', 0):,} teams in master_teams table
- {coverage.get('player_game_stats', 0):,} player-game records in master_player_game_stats
- Database size: {coverage.get('database_size_mb', 0):.2f} MB ({coverage.get('database_size_gb', 0):.3f} GB)"""

            if coverage.get("date_range"):
                date_range = coverage["date_range"]
                coverage_section += f"""
- Date range: {date_range.get('min_date', 'N/A')} to {date_range.get('max_date', 'N/A')}
- Unique game dates: {date_range.get('unique_dates', 0):,}
- Seasons covered: {coverage.get('seasons', 'N/A')}"""
        else:
            coverage_section = f"""**Data Coverage** (📁 STATIC from metrics.yaml):
- {coverage.get('s3_objects', 0):,} objects in S3 ({coverage.get('s3_size_gb', 0):.2f} GB)
- Seasons: {coverage.get('seasons_estimated', 'Unknown')}
- Estimated {coverage.get('games_estimated', 'Unknown')} games, {coverage.get('players_estimated', 'Unknown')} players"""

        summary = f"""
## 📊 DATA INVENTORY SUMMARY

**Database Schema**:
- {schema.get('total_tables', 0)} core tables
- Panel Data: master_player_game_stats (game-level player performance)
- Dimensions: master_players, master_teams, master_games

{coverage_section}

**Available Systems**:
- ✅ Game Prediction System (2,103 lines of code)
- ✅ Plus/Minus Calculation System (4,619 lines of code)
- ✅ PostgreSQL panel data backend
- ✅ S3 data lake with play-by-play events

**Key Data Features Available**:
- Player biographical data (height, weight, position)
- Game-level player statistics (points, rebounds, assists, plus_minus)
- Team organizational data
- Historical game results ({coverage.get('seasons', '2014-2025')})
- Play-by-play event sequences

**IMPORTANT FOR RECOMMENDATIONS**:
When recommending features from the book, leverage these existing data assets:
1. Use master_player_game_stats for player performance analysis ({"LIVE: " + str(coverage.get('player_game_stats', 0)) + " records" if is_live else "172k+ records estimated"})
2. Reference the S3 objects of play-by-play data for sequence modeling
3. Build on the existing prediction system (2,103 lines)
4. Integrate with the plus/minus calculation system
5. Query PostgreSQL for historical panel data analysis
6. {"Database queries return REAL-TIME statistics" if is_live else "Database statistics are from cached metrics"}
"""

        return summary.strip()

    def save_inventory_report(self, output_path: str):
        """Save comprehensive inventory report to JSON"""
        inventory = self.scan_full_inventory()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(inventory, f, indent=2, default=str)

        logger.info(f"💾 Inventory report saved: {output_file}")
        return inventory


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python data_inventory_scanner.py <inventory_path>")
        print(
            "Example: python data_inventory_scanner.py /Users/ryanranft/nba-simulator-aws/inventory"
        )
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    inventory_path = sys.argv[1]
    scanner = DataInventoryScanner(inventory_path)

    # Run full scan
    inventory = scanner.scan_full_inventory()

    # Print AI summary
    print("\n" + "=" * 80)
    print(inventory["summary_for_ai"])
    print("=" * 80 + "\n")

    # Save report
    output_path = "data_inventory_report.json"
    scanner.save_inventory_report(output_path)
    print(f"\n✅ Full report saved to: {output_path}")
