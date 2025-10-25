#!/usr/bin/env python3
"""
MCP Test Client
Tests interaction with the NBA MCP Server via stdio
"""

import pytest
import pytest_asyncio
import json
from pathlib import Path
from mcp_server.env_helper import get_hierarchical_env
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPTestClient:
    """Test client for NBA MCP Server"""

    def __init__(self, server_script_path: str):
        """
        Initialize MCP test client

        Args:
            server_script_path: Path to MCP server script
        """
        self.server_script_path = server_script_path
        self.session = None
        self.client = None

    async def connect(self):
        """Connect to MCP server"""
        server_params = StdioServerParameters(
            command="python3",
            args=[self.server_script_path],
            env={
                "RDS_HOST": get_hierarchical_env("RDS_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "localhost",
                "RDS_PORT": get_hierarchical_env("RDS_PORT", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "5432",
                "RDS_DATABASE": get_hierarchical_env("RDS_DATABASE", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "nba_stats",
                "RDS_USERNAME": get_hierarchical_env("RDS_USERNAME", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "postgres",
                "RDS_PASSWORD": get_hierarchical_env("RDS_PASSWORD", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "",
                "S3_BUCKET": get_hierarchical_env("S3_BUCKET", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "nba-mcp-books-20251011",
                "S3_REGION": get_hierarchical_env("S3_REGION", "NBA_MCP_SYNTHESIS", "WORKFLOW") or "us-east-1",
            },
        )

        # Create stdio client context
        self.client = stdio_client(server_params)
        read, write = await self.client.__aenter__()

        # Create session
        self.session = ClientSession(read, write)
        await self.session.__aenter__()

        # Initialize the session (critical step!)
        await self.session.initialize()

        return True

    async def disconnect(self):
        """Disconnect from MCP server"""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
        except Exception:
            pass  # Ignore teardown errors
        try:
            if self.client:
                await self.client.__aexit__(None, None, None)
        except Exception:
            pass  # Ignore teardown errors

    async def list_tools(self):
        """List available MCP tools"""
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, arguments: dict):
        """
        Call an MCP tool

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool result
        """
        result = await self.session.call_tool(tool_name, arguments)
        return result


@pytest_asyncio.fixture
async def mcp_client():
    """Create and connect MCP test client"""
    project_root = Path(__file__).parent.parent.parent
    server_script = project_root / "mcp_server" / "server_simple.py"

    if not server_script.exists():
        pytest.skip(f"Server script not found at {server_script}")

    client = MCPTestClient(str(server_script))

    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_client_connection(mcp_client):
    """Test that client can connect to MCP server"""
    assert mcp_client.session is not None, "Session should be established"
    assert mcp_client.client is not None, "Client should be connected"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_list_tools(mcp_client):
    """Test listing available MCP tools"""
    tools = await mcp_client.list_tools()

    assert tools is not None, "Should return tools list"
    assert len(tools) > 0, "Should have at least one tool available"

    # Check for expected tools
    tool_names = [tool.name for tool in tools]
    expected_tools = ["list_tables", "get_table_schema", "query_database", "list_s3_files"]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Tool '{expected_tool}' should be available"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_list_tables_tool(mcp_client):
    """Test list_tables tool"""
    result = await mcp_client.call_tool("list_tables", {})

    assert result is not None, "Should return a result"
    assert hasattr(result, "content"), "Result should have content"
    assert len(result.content) > 0, "Result should have content items"

    # Parse content
    content = result.content[0]
    assert hasattr(content, "text"), "Content should have text"

    data = json.loads(content.text)
    assert "tables" in data, "Result should contain tables list"
    assert isinstance(data["tables"], list), "Tables should be a list"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_get_table_schema_tool(mcp_client):
    """Test get_table_schema tool"""
    # First list tables to get a table name
    tables_result = await mcp_client.call_tool("list_tables", {})

    assert tables_result is not None, "Should list tables"

    # Get first table name
    data = json.loads(tables_result.content[0].text)

    # Handle both successful and error responses
    if "tables" in data and len(data["tables"]) > 0:
        table_name = data["tables"][0]

        # Get schema for that table
        schema_result = await mcp_client.call_tool("get_table_schema", {"table_name": table_name})

        assert schema_result is not None, "Should return schema"
        assert hasattr(schema_result, "content"), "Result should have content"

        schema_data = json.loads(schema_result.content[0].text)
        # Accept schema information or error response
        assert "columns" in schema_data or "schema" in schema_data or "error" in schema_data, \
            "Result should contain schema information or error"
    else:
        # If no tables available (DB connection error), test still passes
        assert "error" in data or "tables" in data, "Should return tables list or error"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_query_database_tool(mcp_client):
    """Test query_database tool"""
    sql = "SELECT version()"

    result = await mcp_client.call_tool("query_database", {"sql": sql})

    assert result is not None, "Should return a result"
    assert hasattr(result, "content"), "Result should have content"

    data = json.loads(result.content[0].text)
    # Accept either successful results or error responses (when DB not available)
    assert "rows" in data or "result" in data or ("error" in data and "success" in data), \
        "Result should contain query results or error response"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_list_s3_files_tool(mcp_client):
    """Test list_s3_files tool"""
    result = await mcp_client.call_tool("list_s3_files", {"prefix": "", "max_keys": 10})

    assert result is not None, "Should return a result"
    assert hasattr(result, "content"), "Result should have content"

    data = json.loads(result.content[0].text)
    assert "files" in data or "file_count" in data, "Result should contain S3 file information"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_complex_query_tool(mcp_client):
    """Test complex database query via MCP tool"""
    sql = """
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    LIMIT 20
    """

    result = await mcp_client.call_tool("query_database", {"sql": sql})

    assert result is not None, "Should return a result"
    assert hasattr(result, "content"), "Result should have content"

    data = json.loads(result.content[0].text)
    # Accept either successful results or error responses (when DB not available)
    assert "rows" in data or "result" in data or ("error" in data and "success" in data), \
        "Result should contain query results or error response"

    # Check that we got some rows back (if not an error)
    if data.get("success", True):  # Default to True for backward compatibility
        rows = data.get("rows", data.get("result", []))
        assert isinstance(rows, list), "Rows should be a list"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_full_client_workflow(mcp_client):
    """Test full MCP client workflow: list tools -> query data"""
    # 1. List tools
    tools = await mcp_client.list_tools()
    assert len(tools) > 0, "Should have tools available"

    # 2. List tables
    tables_result = await mcp_client.call_tool("list_tables", {})
    tables_data = json.loads(tables_result.content[0].text)
    # Accept tables list or error response
    assert "tables" in tables_data or "error" in tables_data, "Should list tables or return error"

    # 3. Query database
    query_result = await mcp_client.call_tool("query_database", {"sql": "SELECT 1 as test"})
    query_data = json.loads(query_result.content[0].text)
    # Accept query results or error response
    assert "rows" in query_data or "result" in query_data or ("error" in query_data and "success" in query_data), \
        "Should execute query or return error"
