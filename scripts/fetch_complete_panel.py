#!/usr/bin/env python3
"""
Fetch complete player-season panel data directly from database.
This bypasses MCP tools to avoid context overflow.
"""

import csv
import os
import sys
import psycopg2
import psycopg2.extras
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add mcp_server to path to import secrets manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from mcp_server.unified_secrets_manager import UnifiedSecretsManager
except ImportError:
    UnifiedSecretsManager = None


def fetch_player_seasons():
    """Fetch all player-season data and save to CSV."""

    # Load environment variables using unified secrets manager if available
    if UnifiedSecretsManager:
        print("Loading secrets using Unified Secrets Manager...")
        secrets_manager = UnifiedSecretsManager()
        result = secrets_manager.load_secrets_hierarchical(
            project="nba-mcp-synthesis", sport="NBA", context="production"
        )
        if result.success:
            # Set them in os.environ
            for key, value in secrets_manager.secrets.items():
                os.environ[key] = value
            print(f"✓ Loaded {len(secrets_manager.secrets)} secrets")

            # Debug: show all secrets (masked passwords)
            print("\nAll loaded secrets:")
            for key in sorted(secrets_manager.secrets.keys()):
                value = secrets_manager.secrets[key]
                # Mask sensitive values
                if "PASSWORD" in key or "SECRET" in key or "KEY" in key:
                    display_value = f"{'*' * min(len(value), 8)}"
                else:
                    display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"  {key}: {display_value}")
        else:
            print(f"✗ Failed to load secrets: {result.errors}")
            sys.exit(1)
    else:
        load_dotenv()

    # Get database credentials using the correct hierarchical naming
    # Format: RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW (as used in config.py)
    project = "NBA_MCP_SYNTHESIS"
    contexts = ["WORKFLOW", "DEVELOPMENT", "TEST", "PRODUCTION"]

    db_host = None
    db_port = 5432
    db_name = "nba_simulator"
    db_user = None
    db_password = None

    # Try each context in order
    for context in contexts:
        if not db_host:
            db_host = os.getenv(f"RDS_HOST_{project}_{context}")
        if not db_port or db_port == 5432:
            port_str = os.getenv(f"RDS_PORT_{project}_{context}")
            if port_str:
                db_port = int(port_str)
        if not db_name or db_name == "nba_simulator":
            db_name = os.getenv(f"RDS_DATABASE_{project}_{context}") or db_name
        if not db_user:
            db_user = os.getenv(f"RDS_USERNAME_{project}_{context}")
        if not db_password:
            db_password = os.getenv(f"RDS_PASSWORD_{project}_{context}")

    if not all([db_host, db_user, db_password]):
        print("Error: Missing database credentials in environment variables")
        print(
            "Required: RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW, RDS_USERNAME_..., RDS_PASSWORD_..."
        )
        print(f"\nFound:")
        print(f"  Host: {'✓' if db_host else '✗'}")
        print(f"  User: {'✓' if db_user else '✗'}")
        print(f"  Password: {'✓' if db_password else '✗'}")
        sys.exit(1)

    # Output file
    output_file = Path("data/player_seasons_panel.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"=" * 70)
    print(f"Fetching player-season panel data")
    print(f"Database: {db_host}:{db_port}/{db_name}")
    print(f"Output: {output_file}")
    print(f"=" * 70)

    # SQL query
    query = """
SELECT
    athlete_id::text as player_id,
    CASE
        WHEN EXTRACT(MONTH FROM DATE(game_date)) >= 10 THEN
            EXTRACT(YEAR FROM DATE(game_date))
        ELSE EXTRACT(YEAR FROM DATE(game_date)) - 1
    END as season_year,
    CASE
        WHEN EXTRACT(MONTH FROM DATE(game_date)) >= 10 THEN
            EXTRACT(YEAR FROM DATE(game_date))::text || '-' ||
            RIGHT((EXTRACT(YEAR FROM DATE(game_date)) + 1)::text, 2)
        ELSE
            (EXTRACT(YEAR FROM DATE(game_date)) - 1)::text || '-' ||
            RIGHT(EXTRACT(YEAR FROM DATE(game_date))::text, 2)
    END as season,
    COUNT(*) as games_played,
    ROUND(AVG(points)::numeric, 2) as ppg,
    ROUND(AVG(assists)::numeric, 2) as apg,
    ROUND(AVG(rebounds)::numeric, 2) as rpg,
    ROUND(AVG(minutes)::numeric, 2) as mpg,
    ROUND(SUM(points)::numeric, 0) as total_points,
    ROUND(AVG(CASE WHEN starter = 1 THEN 1.0 ELSE 0.0 END)::numeric, 3) as starter_pct,
    COUNT(DISTINCT team_id) as teams_played_for
FROM hoopr_player_box
WHERE game_date >= '2015-10-01'
    AND game_date < '2024-07-01'
    AND season_type = 2
    AND minutes > 5
    AND active = 1
GROUP BY athlete_id, season_year, season
HAVING COUNT(*) >= 10
ORDER BY athlete_id, season_year
"""

    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        print("✓ Connected successfully")

        # Execute query
        print("\nExecuting query...")
        start_time = datetime.now()

        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        execution_time = (datetime.now() - start_time).total_seconds()
        print(f"✓ Query completed in {execution_time:.2f}s")
        print(f"✓ Fetched {len(rows)} player-seasons")

        # Write to CSV
        print(f"\nWriting to CSV: {output_file}")
        with open(output_file, "w", newline="") as csvfile:
            if rows:
                fieldnames = list(rows[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        print(f"✓ Saved {len(rows)} records to {output_file}")

        # Show sample of data
        print(f"\nSample data (first 3 rows):")
        print("-" * 70)
        for i, row in enumerate(rows[:3]):
            print(f"\nRow {i+1}:")
            for key, value in row.items():
                print(f"  {key}: {value}")

        # Connection will be closed automatically
        conn.close()
        print(f"\n{'=' * 70}")
        print(f"✓ Successfully fetched player-season panel data")
        print(f"  Records: {len(rows)}")
        print(f"  File: {output_file}")
        print(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")
        print(f"{'=' * 70}")

        return len(rows)

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    fetch_player_seasons()
