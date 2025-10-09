#!/usr/bin/env python3
"""
Simple NBA MCP Server using FastMCP
Quick start version for immediate use
"""

import asyncio
import sys
from pathlib import Path
from mcp.server import FastMCP
from dotenv import load_dotenv
import os

# Add parent directory to path so imports work when running via stdio
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

# Create FastMCP server
mcp = FastMCP("nba-mcp-server")


@mcp.tool()
async def query_database(sql: str) -> dict:
    """
    Execute SQL query on NBA database

    Args:
        sql: SQL query to execute (SELECT only)

    Returns:
        Query results
    """
    from mcp_server.connectors.rds_connector import RDSConnector

    connector = RDSConnector(
        host=os.getenv('RDS_HOST'),
        port=int(os.getenv('RDS_PORT', 5432)),
        database=os.getenv('RDS_DATABASE'),
        username=os.getenv('RDS_USERNAME'),
        password=os.getenv('RDS_PASSWORD')
    )

    result = await connector.execute_query(sql, max_rows=100)
    connector.close()

    return result


@mcp.tool()
async def list_tables() -> dict:
    """List all tables in the NBA database"""
    from mcp_server.connectors.rds_connector import RDSConnector

    connector = RDSConnector(
        host=os.getenv('RDS_HOST'),
        port=int(os.getenv('RDS_PORT', 5432)),
        database=os.getenv('RDS_DATABASE'),
        username=os.getenv('RDS_USERNAME'),
        password=os.getenv('RDS_PASSWORD')
    )

    tables = await connector.list_tables()
    connector.close()

    return {"tables": tables, "count": len(tables)}


@mcp.tool()
async def get_table_schema(table_name: str) -> dict:
    """
    Get schema for a database table

    Args:
        table_name: Name of the table

    Returns:
        Table schema information
    """
    from mcp_server.connectors.rds_connector import RDSConnector

    connector = RDSConnector(
        host=os.getenv('RDS_HOST'),
        port=int(os.getenv('RDS_PORT', 5432)),
        database=os.getenv('RDS_DATABASE'),
        username=os.getenv('RDS_USERNAME'),
        password=os.getenv('RDS_PASSWORD')
    )

    schema = await connector.get_table_schema(table_name)
    connector.close()

    return schema


@mcp.tool()
async def list_s3_files(prefix: str = "", max_keys: int = 100) -> dict:
    """
    List files in S3 bucket

    Args:
        prefix: Prefix filter for files
        max_keys: Maximum number of files to return

    Returns:
        List of files
    """
    from mcp_server.connectors.s3_connector import S3Connector

    connector = S3Connector(
        bucket_name=os.getenv('S3_BUCKET'),
        region=os.getenv('S3_REGION', 'us-east-1')
    )

    result = await connector.list_files(prefix=prefix, max_keys=max_keys)
    return result


if __name__ == "__main__":
    print("🚀 Starting NBA MCP Server (Simple Mode)...")
    print(f"📊 Database: {os.getenv('RDS_DATABASE')}")
    print(f"🪣 S3 Bucket: {os.getenv('S3_BUCKET')}")
    print()

    mcp.run()
