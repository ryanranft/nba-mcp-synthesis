#!/usr/bin/env python3
"""
Discover ESPN database structure in nba_simulator database.

This script connects to the nba_simulator database and discovers:
  - All schemas and tables
  - ESPN-related table structures
  - Row counts and data ranges
  - Column types and constraints
  - Common join keys

Output: JSON report of ESPN schema structure for migration planning

Author: NBA MCP Synthesis
Date: 2025-11-08
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config


def print_header(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print('=' * 80)


def print_section(title):
    """Print formatted subsection."""
    print(f"\n{title}")
    print('-' * 80)


def discover_schemas(conn):
    """Discover all schemas in the database."""
    print_section("Discovering Schemas")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)

        schemas = [row[0] for row in cur.fetchall()]

        for schema in schemas:
            print(f"  📁 {schema}")

        return schemas


def discover_tables(conn, schema):
    """Discover all tables in a schema with row counts."""
    with conn.cursor() as cur:
        # Get all tables in schema
        cur.execute(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """, (schema,))

        tables = []

        for (table_name,) in cur.fetchall():
            # Get row count
            cur.execute(f"SELECT COUNT(*) FROM {schema}.{table_name};")
            row_count = cur.fetchone()[0]

            tables.append({
                'name': table_name,
                'row_count': row_count
            })

        return tables


def get_table_structure(conn, schema, table):
    """Get detailed structure of a table."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get column information
        cur.execute("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """, (schema, table))

        columns = cur.fetchall()

        # Get primary keys
        cur.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass
              AND i.indisprimary;
        """, (f"{schema}.{table}",))

        primary_keys = [row['attname'] for row in cur.fetchall()]

        # Get indexes
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = %s AND tablename = %s
            ORDER BY indexname;
        """, (schema, table))

        indexes = cur.fetchall()

        return {
            'columns': [dict(col) for col in columns],
            'primary_keys': primary_keys,
            'indexes': [dict(idx) for idx in indexes]
        }


def get_date_range(conn, schema, table):
    """Try to get date range from common date columns."""
    with conn.cursor() as cur:
        # Check for common date column names
        date_columns = ['game_date', 'date', 'commence_time', 'created_at', 'updated_at']

        for col in date_columns:
            try:
                cur.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s
                      AND table_name = %s
                      AND column_name = %s;
                """, (schema, table, col))

                if cur.fetchone():
                    # Column exists, get range
                    cur.execute(f"""
                        SELECT
                            MIN({col})::TEXT as min_date,
                            MAX({col})::TEXT as max_date
                        FROM {schema}.{table};
                    """)

                    result = cur.fetchone()
                    if result and result[0]:
                        return {
                            'column': col,
                            'min_date': result[0],
                            'max_date': result[1]
                        }
            except Exception:
                continue

        return None


def identify_common_keys(conn, schema, table):
    """Identify common join keys (game_id, player_id, team_id, etc.)."""
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                  AND column_name LIKE '%_id'
                ORDER BY ordinal_position;
            """, (schema, table))

            results = cur.fetchall()
            return [{'name': row[0], 'type': row[1]} for row in results]
        except Exception:
            return []


def main():
    """Main discovery function."""
    print_header("ESPN Database Schema Discovery")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Database: nba_simulator (localhost:5432)")

    # Connect to RDS nba_simulator database (production context)
    print_section("Connecting to Database")
    try:
        # Load production secrets to get RDS nba_simulator database
        load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
        db_config = get_database_config()

        print(f"  Database: {db_config.get('database', 'nba_simulator')}")
        print(f"  Host: {db_config.get('host', 'RDS')[:30]}...")

        conn = psycopg2.connect(**db_config)
        print("  ✅ Connection established")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        sys.exit(1)

    # Discover schemas
    schemas = discover_schemas(conn)

    # Build complete database structure
    database_structure = {
        'database': 'nba_simulator',
        'discovered_at': datetime.now().isoformat(),
        'schemas': {}
    }

    # Discover tables in each schema
    print_header("Discovering Tables")

    for schema in schemas:
        print_section(f"Schema: {schema}")

        tables = discover_tables(conn, schema)
        total_rows = sum(t['row_count'] for t in tables)

        print(f"  Tables: {len(tables)}")
        print(f"  Total Rows: {total_rows:,}")
        print()

        schema_info = {
            'table_count': len(tables),
            'total_rows': total_rows,
            'tables': {}
        }

        for table_info in tables:
            table_name = table_info['name']
            row_count = table_info['row_count']

            print(f"    📊 {table_name:40s} {row_count:>12,} rows")

            # Get detailed structure
            structure = get_table_structure(conn, schema, table_name)
            date_range = get_date_range(conn, schema, table_name)
            common_keys = identify_common_keys(conn, schema, table_name)

            schema_info['tables'][table_name] = {
                'row_count': row_count,
                'structure': structure,
                'date_range': date_range,
                'common_keys': common_keys
            }

        database_structure['schemas'][schema] = schema_info

    # Save discovery report
    output_file = Path(__file__).parent.parent / 'reports' / 'espn_schema_discovery.json'
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(database_structure, f, indent=2, default=str)

    print_header("Discovery Summary")
    print(f"  Total Schemas: {len(schemas)}")
    print(f"  Total Tables: {sum(s['table_count'] for s in database_structure['schemas'].values())}")
    print(f"  Total Rows: {sum(s['total_rows'] for s in database_structure['schemas'].values()):,}")
    print(f"\n  📄 Report saved: {output_file}")

    # Identify ESPN-related tables
    print_section("ESPN-Related Tables")

    espn_tables = []
    for schema, schema_info in database_structure['schemas'].items():
        for table_name, table_info in schema_info['tables'].items():
            if 'espn' in table_name.lower():
                espn_tables.append({
                    'schema': schema,
                    'table': table_name,
                    'rows': table_info['row_count']
                })

    if espn_tables:
        print(f"  Found {len(espn_tables)} ESPN tables:")
        for t in espn_tables:
            print(f"    • {t['schema']}.{t['table']:40s} {t['rows']:>12,} rows")
    else:
        print("  ⚠️  No tables with 'espn' in name found")
        print("  Searching for raw or web-scraped data patterns...")

    conn.close()
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
