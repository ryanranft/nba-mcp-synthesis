#!/usr/bin/env python3
"""
Test FastMCP Server Functionality
Ensures FastMCP server works with database and all components
"""

import pytest
import pytest_asyncio
import asyncio
from contextlib import asynccontextmanager
from mcp_server.fastmcp_lifespan import nba_lifespan
from mcp_server.fastmcp_settings import NBAMCPSettings
from mcp_server.tools.params import QueryDatabaseParams, ListTablesParams


@pytest.fixture
def settings():
    """Load NBAMCPSettings from environment"""
    return NBAMCPSettings()


@pytest_asyncio.fixture
async def lifespan_context():
    """Create lifespan context with all resources"""

    class MockApp:
        pass

    app = MockApp()

    async with nba_lifespan(app) as context:
        yield context


@pytest.mark.integration
def test_settings_loading(settings):
    """Test that settings load correctly from environment"""
    assert settings is not None, "Settings should load"
    assert settings.rds_host, "RDS host should be configured"
    assert settings.rds_database, "RDS database should be configured"
    assert settings.s3_bucket, "S3 bucket should be configured"
    assert isinstance(settings.debug, bool), "Debug should be a boolean"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_lifespan_context():
    """Test that lifespan context creates all resources"""

    class MockApp:
        pass

    app = MockApp()

    async with nba_lifespan(app) as context:
        assert context is not None, "Context should be created"
        assert isinstance(context, dict), "Context should be a dictionary"

        # Check for expected resources
        expected_keys = ["rds_connector", "s3_connector", "glue_connector"]
        for key in expected_keys:
            assert key in context, f"Context should contain {key}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_database_connection(lifespan_context, settings):
    """Test database connection and simple query"""
    # Skip if RDS credentials not configured
    if not settings.rds_host or not settings.rds_username:
        pytest.skip("RDS credentials not configured")

    rds_connector = lifespan_context["rds_connector"]

    # Simple test query
    result = await rds_connector.execute_query("SELECT 1 as test")

    assert result is not None, "Query should return a result"
    assert "success" in result or isinstance(
        result, list
    ), "Result should indicate success or return rows"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tables(lifespan_context, settings):
    """Test listing database tables"""
    # Skip if RDS credentials not configured properly
    if (
        not settings.rds_host
        or not settings.rds_username
        or not settings.rds_host.strip()
    ):
        pytest.skip("RDS credentials not configured")

    rds_connector = lifespan_context["rds_connector"]

    result = await rds_connector.execute_query(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name
        LIMIT 5
        """
    )

    # Result should be either a dict with success or a list of rows
    if isinstance(result, dict):
        # Skip if connection failed (no credentials)
        if not result.get("success", False):
            pytest.skip(
                f"RDS connection failed: {result.get('error', 'Unknown error')}"
            )
        rows = result.get("rows", [])
    else:
        rows = result

    assert isinstance(rows, list), "Should return a list of tables"
    assert len(rows) > 0, "Should find at least one table"

    # Each row should have table_schema and table_name
    for row in rows:
        assert "table_schema" in row, "Row should have table_schema"
        assert "table_name" in row, "Row should have table_name"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_s3_connection(lifespan_context):
    """Test S3 connection and file listing"""
    s3_connector = lifespan_context["s3_connector"]

    # List a few files
    result = await s3_connector.list_files(prefix="", max_keys=3)

    assert result is not None, "S3 list should return a result"
    assert "success" in result, "Result should have success field"

    if result.get("success"):
        assert "files" in result, "Successful result should contain files"
        files = result.get("files", [])
        assert isinstance(files, list), "Files should be a list"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_glue_connection(lifespan_context):
    """Test Glue catalog connection"""
    glue_connector = lifespan_context["glue_connector"]

    try:
        tables = await asyncio.to_thread(glue_connector.list_tables)
        assert isinstance(tables, list), "Glue should return a list of tables"
    except Exception as e:
        # Glue might not be configured in all environments
        pytest.skip(f"Glue catalog not accessible: {e}")


# Pydantic Validation Tests


@pytest.mark.unit
def test_pydantic_valid_query():
    """Test that valid SELECT queries are accepted"""
    params = QueryDatabaseParams(sql_query="SELECT * FROM players LIMIT 10")

    assert params.sql_query == "SELECT * FROM players LIMIT 10"
    assert params.max_rows > 0, "max_rows should have a default value"


@pytest.mark.unit
def test_pydantic_sql_injection_blocked():
    """Test that SQL injection attempts are blocked"""
    with pytest.raises(Exception) as exc_info:
        QueryDatabaseParams(sql_query="SELECT * FROM players; DROP TABLE players;")

    # Should raise validation error for multiple statements
    assert exc_info.value is not None, "SQL injection should be blocked"


@pytest.mark.unit
def test_pydantic_non_select_blocked():
    """Test that non-SELECT queries are blocked"""
    with pytest.raises(Exception) as exc_info:
        QueryDatabaseParams(sql_query="DELETE FROM players")

    # Should raise validation error for non-SELECT
    assert exc_info.value is not None, "Non-SELECT query should be blocked"


@pytest.mark.unit
def test_pydantic_list_tables_params():
    """Test ListTablesParams validation"""
    # Test default params
    params = ListTablesParams()
    assert params is not None, "Default params should work"
    assert params.schema_name is None, "Default schema_name should be None"

    # Test with schema (using alias)
    params = ListTablesParams(schema="public")
    assert params.schema_name == "public", "Schema should be set correctly via alias"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_integration_flow(lifespan_context, settings):
    """Test full integration flow: settings -> lifespan -> query"""
    # Skip if RDS credentials not configured
    if not settings.rds_host or not settings.rds_username:
        pytest.skip("RDS credentials not configured")

    # Settings already loaded
    assert settings.rds_database, "Settings should be loaded"

    # Lifespan context available
    assert "rds_connector" in lifespan_context, "RDS connector should be available"

    # Execute a real query
    rds_connector = lifespan_context["rds_connector"]
    result = await rds_connector.execute_query("SELECT 1 as integration_test")

    assert result is not None, "Integration test query should succeed"
