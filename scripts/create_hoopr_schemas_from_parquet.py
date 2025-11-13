#!/usr/bin/env python3
"""
Create hoopr_* table schemas directly from parquet files.

This ensures the PostgreSQL schema exactly matches the parquet data.
"""

import sys
from pathlib import Path
import pandas as pd
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)

# Parquet file paths - now creating schema-qualified tables in 'raw' schema
PARQUET_SAMPLES = {
    "raw.schedule": "/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/load_nba_schedule/parquet/nba_data_2002.parquet",
    "raw.team_box": "/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/load_nba_team_box/parquet/nba_data_2002.parquet",
    "raw.player_box": "/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/load_nba_player_box/parquet/nba_data_2002.parquet",
    "raw.play_by_play": "/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/load_nba_pbp/parquet/nba_data_2002.parquet",
}

# Type mapping
TYPE_MAP = {
    "object": "TEXT",
    "int64": "BIGINT",
    "float64": "DOUBLE PRECISION",
    "bool": "BOOLEAN",
    "datetime64[ns]": "TIMESTAMP",
}


def create_schema_from_parquet(table_name: str, parquet_path: str) -> str:
    """Generate CREATE TABLE statement from parquet file."""
    df = pd.read_parquet(parquet_path)
    df = df.head(1)

    columns = []
    for col in df.columns:
        pg_type = TYPE_MAP.get(str(df[col].dtype), "TEXT")
        columns.append(f"    {col} {pg_type}")

    create_stmt = f"""DROP TABLE IF EXISTS {table_name} CASCADE;
CREATE TABLE {table_name} (
{','.join([chr(10) + c for c in columns])}
);"""

    # Add indexes (replace dots with underscores for index names)
    index_name_safe = table_name.replace(".", "_")
    if "game_id" in df.columns:
        create_stmt += (
            f"\nCREATE INDEX idx_{index_name_safe}_game_id ON {table_name}(game_id);"
        )
    if "game_date" in df.columns:
        create_stmt += f"\nCREATE INDEX idx_{index_name_safe}_game_date ON {table_name}(game_date);"

    return create_stmt


def main():
    # Load secrets and connect
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "development")
    db_config = get_database_config()
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    print("Creating hoopr_* tables from parquet schemas...")
    print("=" * 80)

    for table_name, parquet_path in PARQUET_SAMPLES.items():
        print(f"\n{table_name}:")
        print(f"  Source: {Path(parquet_path).name}")

        # Generate and execute schema
        schema_sql = create_schema_from_parquet(table_name, parquet_path)

        # Get column count
        df_sample = pd.read_parquet(parquet_path)
        num_cols = len(df_sample.columns)

        print(f"  Columns: {num_cols}")
        print(f"  Creating table...")

        cur.execute(schema_sql)
        conn.commit()

        print(f"  ✅ Created")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("✅ All tables created successfully!")
    print(
        "\nNext step: python scripts/load_parquet_to_postgres.py --context development"
    )


if __name__ == "__main__":
    main()
