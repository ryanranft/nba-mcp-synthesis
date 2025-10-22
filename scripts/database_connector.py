#!/usr/bin/env python3
"""
Database Connection Manager for NBA Analytics

Provides centralized PostgreSQL connection handling with:
- Connection pooling
- Retry logic
- Read-only mode for safety
- Automatic connection cleanup

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-21
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str
    schema: str = "public"
    read_only: bool = True
    connect_timeout: int = 10
    max_retries: int = 3


class DatabaseConnector:
    """
    PostgreSQL database connector with pooling and retry logic.

    Features:
    - Connection pooling for performance
    - Automatic retry with exponential backoff
    - Read-only mode by default (safety)
    - Graceful connection cleanup
    - Query timeout protection
    """

    def __init__(self, config: DatabaseConfig):
        """
        Initialize database connector.

        Args:
            config: DatabaseConfig with connection parameters
        """
        self.config = config
        self.connection = None
        self.pool = None

        logger.info(f"📊 Database Connector initialized")
        logger.info(f"   Host: {config.host}")
        logger.info(f"   Database: {config.database}")
        logger.info(f"   Schema: {config.schema}")
        logger.info(f"   Read-only: {config.read_only}")

    def connect(self) -> bool:
        """
        Establish database connection with retry logic.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            import psycopg2
            from psycopg2 import pool

            logger.info("🔌 Connecting to PostgreSQL...")

            # Create connection pool (min 1, max 5 connections)
            self.pool = pool.SimpleConnectionPool(
                1,  # minconn
                5,  # maxconn
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                connect_timeout=self.config.connect_timeout
            )

            # Test connection
            test_conn = self.pool.getconn()

            if test_conn:
                # Set read-only mode if configured
                if self.config.read_only:
                    cursor = test_conn.cursor()
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.close()

                # Set schema
                cursor = test_conn.cursor()
                cursor.execute(f"SET search_path TO {self.config.schema}")
                cursor.close()

                # Return connection to pool
                self.pool.putconn(test_conn)

                logger.info("✅ Database connection established")
                return True
            else:
                logger.error("❌ Failed to get connection from pool")
                return False

        except ImportError:
            logger.error("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
            return False

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close all database connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("🔌 Database connections closed")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Usage:
            with connector.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
        """
        conn = None
        try:
            if not self.pool:
                if not self.connect():
                    raise Exception("Failed to establish database connection")

            conn = self.pool.getconn()

            # Set read-only if configured
            if self.config.read_only:
                cursor = conn.cursor()
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.close()

            yield conn

        finally:
            if conn and self.pool:
                self.pool.putconn(conn)

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False,
        timeout: int = 30
    ) -> Optional[Any]:
        """
        Execute a SQL query with retry logic.

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            fetch_one: If True, return only first row. Otherwise return all rows.
            timeout: Query timeout in seconds

        Returns:
            Query results (list of tuples) or None if error
        """
        retries = 0
        last_error = None

        while retries < self.config.max_retries:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()

                    # Set query timeout
                    cursor.execute(f"SET statement_timeout = {timeout * 1000}")

                    # Execute query
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    # Fetch results
                    if fetch_one:
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()

                    cursor.close()
                    return result

            except Exception as e:
                last_error = e
                retries += 1

                if retries < self.config.max_retries:
                    wait_time = 2 ** retries  # Exponential backoff
                    logger.warning(f"⚠️  Query failed (attempt {retries}/{self.config.max_retries}): {e}")
                    logger.warning(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Query failed after {self.config.max_retries} attempts: {e}")

        return None

    def get_table_row_count(self, table_name: str) -> Optional[int]:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Row count or None if error
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.execute_query(query, fetch_one=True)

        if result:
            return result[0]
        return None

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table statistics
        """
        stats = {
            'table_name': table_name,
            'row_count': None,
            'size_bytes': None,
            'size_mb': None,
            'last_updated': None,
        }

        # Row count
        row_count = self.get_table_row_count(table_name)
        if row_count is not None:
            stats['row_count'] = row_count

        # Table size
        size_query = f"""
            SELECT
                pg_total_relation_size('{table_name}') AS total_bytes,
                pg_size_pretty(pg_total_relation_size('{table_name}')) AS size_pretty
        """
        size_result = self.execute_query(size_query, fetch_one=True)

        if size_result:
            stats['size_bytes'] = size_result[0]
            stats['size_mb'] = round(size_result[0] / 1_000_000, 2)
            stats['size_pretty'] = size_result[1]

        # Last modification time (if possible)
        try:
            last_update_query = f"""
                SELECT MAX(last_value) as last_updated
                FROM (
                    SELECT MAX(xmax::text::bigint) as last_value
                    FROM {table_name}
                    LIMIT 1
                ) sub
            """
            # This query might not work on all setups, so we'll catch errors
            last_update_result = self.execute_query(last_update_query, fetch_one=True)
            if last_update_result and last_update_result[0]:
                stats['last_updated'] = last_update_result[0]
        except:
            pass  # Not critical if this fails

        return stats

    def get_column_stats(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific column.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            Dictionary with column statistics
        """
        stats = {
            'table': table_name,
            'column': column_name,
            'null_count': None,
            'null_percentage': None,
            'distinct_count': None,
            'min_value': None,
            'max_value': None,
        }

        # Check column type first
        type_query = f"""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = '{self.config.schema}'
            AND table_name = '{table_name}'
            AND column_name = '{column_name}'
        """
        type_result = self.execute_query(type_query, fetch_one=True)

        if not type_result:
            logger.warning(f"⚠️  Column {column_name} not found in {table_name}")
            return stats

        data_type = type_result[0]
        stats['data_type'] = data_type

        # Null counts
        null_query = f"""
            SELECT
                COUNT(*) AS total,
                COUNT({column_name}) AS non_null,
                COUNT(*) - COUNT({column_name}) AS null_count
            FROM {table_name}
        """
        null_result = self.execute_query(null_query, fetch_one=True)

        if null_result:
            total, non_null, null_count = null_result
            stats['null_count'] = null_count
            stats['null_percentage'] = round((null_count / total * 100) if total > 0 else 0, 2)

        # Distinct count
        distinct_query = f"SELECT COUNT(DISTINCT {column_name}) FROM {table_name}"
        distinct_result = self.execute_query(distinct_query, fetch_one=True)

        if distinct_result:
            stats['distinct_count'] = distinct_result[0]

        # Min/Max for numeric and date columns
        if data_type in ['integer', 'bigint', 'numeric', 'real', 'double precision', 'date', 'timestamp', 'timestamp without time zone']:
            minmax_query = f"""
                SELECT
                    MIN({column_name})::text AS min_val,
                    MAX({column_name})::text AS max_val
                FROM {table_name}
            """
            minmax_result = self.execute_query(minmax_query, fetch_one=True)

            if minmax_result:
                stats['min_value'] = minmax_result[0]
                stats['max_value'] = minmax_result[1]

        return stats

    def get_date_range(self, table_name: str, date_column: str) -> Optional[Dict[str, str]]:
        """
        Get date range for a table.

        Args:
            table_name: Name of the table
            date_column: Name of the date column

        Returns:
            Dict with min_date and max_date
        """
        query = f"""
            SELECT
                MIN({date_column})::text AS min_date,
                MAX({date_column})::text AS max_date,
                COUNT(DISTINCT {date_column}) AS unique_dates
            FROM {table_name}
        """

        result = self.execute_query(query, fetch_one=True)

        if result:
            return {
                'min_date': result[0],
                'max_date': result[1],
                'unique_dates': result[2],
                'date_column': date_column
            }

        return None

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            result = self.execute_query("SELECT 1", fetch_one=True)
            if result and result[0] == 1:
                logger.info("✅ Database connection test successful")
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False


def create_db_connector_from_env() -> Optional[DatabaseConnector]:
    """
    Create DatabaseConnector from environment variables.

    Environment variables:
    - NBA_DB_HOST or DB_HOST
    - NBA_DB_PORT or DB_PORT (default: 5432)
    - NBA_DB_NAME or DB_NAME
    - NBA_DB_USER or DB_USER
    - NBA_DB_PASSWORD or DB_PASSWORD
    - NBA_DB_SCHEMA or DB_SCHEMA (default: public)

    Returns:
        DatabaseConnector instance or None if env vars not set
    """
    from mcp_server.env_helper import get_hierarchical_env

    host = get_hierarchical_env("DB_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW")
    port = int(get_hierarchical_env("DB_PORT", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "5432")
    database = get_hierarchical_env("DB_NAME", "NBA_MCP_SYNTHESIS", "WORKFLOW")
    user = get_hierarchical_env("DB_USER", "NBA_MCP_SYNTHESIS", "WORKFLOW")
    password = get_hierarchical_env("DB_PASSWORD", "NBA_MCP_SYNTHESIS", "WORKFLOW")
    schema = get_hierarchical_env("DB_SCHEMA", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "public"

    if not all([host, database, user, password]):
        logger.warning("⚠️  Database credentials not found in environment variables")
        logger.info("   Required: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        return None

    config = DatabaseConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        schema=schema,
        read_only=True  # Safety: read-only by default
    )

    connector = DatabaseConnector(config)

    # Test connection
    if connector.connect():
        if connector.test_connection():
            return connector
        else:
            connector.disconnect()
            return None
    else:
        return None


def main():
    """CLI for testing database connection"""
    import argparse

    parser = argparse.ArgumentParser(description='Test database connection')
    parser.add_argument('--host', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--database', help='Database name')
    parser.add_argument('--user', help='Database user')
    parser.add_argument('--password', help='Database password')
    parser.add_argument('--schema', default='public', help='Database schema')
    parser.add_argument('--table', help='Test table statistics')
    args = parser.parse_args()

    # Try environment variables first
    connector = create_db_connector_from_env()

    # If env vars didn't work, use CLI args
    if not connector and args.host and args.database and args.user and args.password:
        config = DatabaseConfig(
            host=args.host,
            port=args.port,
            database=args.database,
            user=args.user,
            password=args.password,
            schema=args.schema
        )
        connector = DatabaseConnector(config)
        connector.connect()

    if not connector:
        print("❌ Failed to create database connector")
        print("   Provide credentials via environment variables or CLI arguments")
        exit(1)

    # Test connection
    if not connector.test_connection():
        print("❌ Connection test failed")
        exit(1)

    # If table specified, get stats
    if args.table:
        print(f"\n📊 Statistics for table: {args.table}")
        print("="*60)

        stats = connector.get_table_stats(args.table)
        print(f"Row count: {stats.get('row_count', 'N/A'):,}")
        print(f"Size: {stats.get('size_pretty', 'N/A')}")
        print(f"Last updated: {stats.get('last_updated', 'N/A')}")

    # Cleanup
    connector.disconnect()


if __name__ == '__main__':
    main()
