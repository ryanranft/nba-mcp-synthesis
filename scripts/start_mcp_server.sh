#!/bin/bash
# Start NBA MCP Server

echo "🚀 Starting NBA MCP Server..."
echo "📍 Working directory: $(pwd)"
echo ""

# Activate conda environment if needed
# conda activate mcp-synthesis

# Start the server
python -c "
import asyncio
from mcp.server import FastMCP
from dotenv import load_dotenv
import os
import sys

load_dotenv()

mcp = FastMCP('nba-mcp-server')

@mcp.tool()
async def query_database(sql: str) -> dict:
    '''Execute SQL query on NBA database'''
    sys.path.insert(0, '.')
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
    '''List all tables in NBA database'''
    sys.path.insert(0, '.')
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
    return {'tables': tables, 'count': len(tables)}

print('✅ NBA MCP Server running')
print(f'📊 Database: {os.getenv(\"RDS_DATABASE\")}')
print(f'🪣 S3: {os.getenv(\"S3_BUCKET\")}')
print('🔧 Available tools: query_database, list_tables')
print('')
mcp.run()
"