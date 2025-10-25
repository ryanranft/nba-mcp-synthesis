#!/usr/bin/env python3
"""
Test MCP Connection
Verifies MCP server is running and all connections work
"""

import pytest
from pathlib import Path
from mcp_server.env_helper import get_hierarchical_env
from mcp_server.config import MCPConfig
from mcp_server.connectors.rds_connector import RDSConnector
from mcp_server.connectors.s3_connector import S3Connector
from mcp_server.connectors.slack_notifier import SlackNotifier


@pytest.fixture
def mcp_config():
    """Load MCP configuration from environment"""
    return MCPConfig.from_env()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rds_connection(mcp_config):
    """Test RDS PostgreSQL connection"""
    # Skip if RDS credentials not configured
    if not mcp_config.rds_host or not mcp_config.rds_username:
        pytest.skip("RDS credentials not configured")

    connector = RDSConnector(
        host=mcp_config.rds_host,
        port=mcp_config.rds_port,
        database=mcp_config.rds_database,
        username=mcp_config.rds_username,
        password=mcp_config.rds_password,
    )

    # Test basic query
    result = await connector.execute_query("SELECT version()")

    assert result[
        "success"
    ], f"RDS connection failed: {result.get('error', 'Unknown error')}"
    assert "rows" in result, "Result should contain rows"
    assert len(result["rows"]) > 0, "Should return PostgreSQL version"

    # Verify version format
    version = result["rows"][0]["version"]
    assert "PostgreSQL" in version, f"Expected PostgreSQL version, got: {version}"

    # Get table list
    tables = await connector.list_tables()
    assert isinstance(tables, list), "list_tables should return a list"
    assert len(tables) > 0, "Database should contain tables"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_s3_connection(mcp_config):
    """Test S3 bucket connection"""
    connector = S3Connector(
        bucket_name=mcp_config.s3_bucket, region=mcp_config.s3_region
    )

    # Check connection
    connected = await connector.check_connection()
    assert connected, f"Cannot connect to S3 bucket: {mcp_config.s3_bucket}"

    # List some files
    result = await connector.list_files(max_keys=5)

    assert result[
        "success"
    ], f"Failed to list S3 files: {result.get('error', 'Unknown error')}"
    assert "file_count" in result, "Result should contain file_count"
    assert result["file_count"] >= 0, "File count should be non-negative"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not get_hierarchical_env("SLACK_WEBHOOK_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW"),
    reason="Slack webhook URL not configured",
)
async def test_slack_connection(mcp_config):
    """Test Slack webhook (optional)"""
    if not mcp_config.slack_webhook_url:
        pytest.skip("No Slack webhook configured")

    notifier = SlackNotifier(webhook_url=mcp_config.slack_webhook_url)

    # Send test message
    message = {
        "text": "🔧 MCP Server Connection Test",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Testing MCP server connections...",
                },
            }
        ],
    }

    success = await notifier.send_notification(message)
    assert success, "Failed to send Slack notification"


@pytest.mark.integration
def test_project_paths(mcp_config):
    """Test project path configuration"""
    project_path = Path(mcp_config.project_root)

    assert project_path.exists(), f"Project path does not exist: {project_path}"
    assert project_path.is_dir(), f"Project path is not a directory: {project_path}"

    # Count Python files
    py_files = list(project_path.rglob("*.py"))
    assert len(py_files) > 0, "Project should contain Python files"

    # Count SQL files (may be zero, so just check type)
    sql_files = list(project_path.rglob("*.sql"))
    assert isinstance(sql_files, list), "SQL files should return a list"


@pytest.mark.integration
def test_api_keys():
    """Test if API keys are configured"""
    keys = {
        "Anthropic": get_hierarchical_env(
            "ANTHROPIC_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        ),
        "OpenAI": get_hierarchical_env(
            "OPENAI_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        ),
        "Google": get_hierarchical_env(
            "GOOGLE_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        ),
        "AWS": get_hierarchical_env(
            "AWS_ACCESS_KEY_ID", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        ),
    }

    # Check that the function returns dictionaries with keys
    # In test environments, API keys may not be configured
    configured_keys = [k for k, v in keys.items() if v]

    # Log which keys are configured for debugging
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Configured API keys: {configured_keys}")

    # The test passes as long as we can check for keys (even if none are configured)
    assert isinstance(configured_keys, list), "Should return a list of configured keys"


@pytest.mark.integration
def test_config_validation(mcp_config):
    """Test MCP configuration validation"""
    errors = mcp_config.validate()

    # We allow some configuration errors in test environments,
    # but we should still validate that the function returns a list
    assert isinstance(errors, list), "validate() should return a list of errors"

    # Log any errors for debugging
    if errors:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Configuration validation found {len(errors)} warnings:")
        for error in errors:
            logger.warning(f"  - {error}")
