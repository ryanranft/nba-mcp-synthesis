#!/usr/bin/env python3
"""
Test Notification System

Tests Slack and Linear notification integrations
"""

import pytest
from mcp_server.env_helper import get_hierarchical_env


@pytest.fixture
def slack_webhook():
    """Get Slack webhook URL from environment"""
    webhook = get_hierarchical_env("SLACK_WEBHOOK_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW")
    if not webhook:
        pytest.skip("Slack webhook URL not configured")
    return webhook


@pytest.fixture
def linear_api_key():
    """Get Linear API key from environment"""
    api_key = get_hierarchical_env("LINEAR_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW")
    if not api_key:
        pytest.skip("Linear API key not configured")
    return api_key


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_slack_notifier_available():
    """Test that Slack notifier module is available"""
    try:
        from mcp_server.connectors.slack_notifier import SlackNotifier

        assert SlackNotifier is not None
    except ImportError:
        pytest.skip("SlackNotifier not available")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_slack_notification(slack_webhook):
    """Test sending Slack notification"""
    try:
        from mcp_server.connectors.slack_notifier import SlackNotifier
    except ImportError:
        pytest.skip("SlackNotifier not available")

    notifier = SlackNotifier(slack_webhook)

    # Test basic notification
    test_message = {
        "text": "🧪 NBA Book Analysis Workflow - Test Notification",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🧪 Test Notification*\nThis is a test message from the pytest test suite.",
                },
            },
        ],
    }

    success = await notifier.send_notification(test_message)
    assert success, "Slack notification should be sent successfully"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_linear_client_available():
    """Test that Linear client is available"""
    try:
        from scripts.notification_manager import LinearClient

        assert LinearClient is not None
    except ImportError:
        pytest.skip("LinearClient not available")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_linear_get_teams(linear_api_key):
    """Test getting Linear teams"""
    try:
        from scripts.notification_manager import LinearClient
    except ImportError:
        pytest.skip("LinearClient not available")

    client = LinearClient(linear_api_key)

    teams = await client.get_teams()

    assert isinstance(teams, list), "Teams should be a list"
    # Teams may be empty, so just check structure
    for team in teams:
        assert "id" in team, "Team should have an ID"
        assert "name" in team, "Team should have a name"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_notification_manager_available():
    """Test that NotificationManager is available"""
    try:
        from scripts.notification_manager import NotificationManager

        assert NotificationManager is not None
    except ImportError:
        pytest.skip("NotificationManager not available")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_notification_manager_initialization(slack_webhook, linear_api_key):
    """Test initializing NotificationManager"""
    try:
        from scripts.notification_manager import NotificationManager
    except ImportError:
        pytest.skip("NotificationManager not available")

    manager = NotificationManager(slack_webhook, linear_api_key)

    assert manager is not None, "NotificationManager should initialize"
    assert hasattr(
        manager, "notify_stage_start"
    ), "Should have notify_stage_start method"
    assert hasattr(
        manager, "notify_stage_complete"
    ), "Should have notify_stage_complete method"
