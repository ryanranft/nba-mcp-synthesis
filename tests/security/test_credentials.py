#!/usr/bin/env python3
"""
Credentials Testing
Tests all credentials using the unified secrets management system
"""

import pytest
import requests
from mcp_server.env_helper import get_hierarchical_env


@pytest.fixture
def project_context():
    """Default project context for tests"""
    return ("NBA_MCP_SYNTHESIS", "WORKFLOW")


# AI Model API Key Tests


@pytest.mark.security
def test_deepseek_api_key_format(project_context):
    """Test DeepSeek API key format validation"""
    api_key = get_hierarchical_env("DEEPSEEK_API_KEY", *project_context)

    if not api_key:
        pytest.skip("DeepSeek API key not configured")

    # Validate key format
    assert api_key.startswith("sk-"), "DeepSeek API key should start with 'sk-'"
    assert len(api_key) > 10, "API key should be substantial length"


@pytest.mark.security
def test_anthropic_api_key_format(project_context):
    """Test Anthropic Claude API key format validation"""
    api_key = get_hierarchical_env("ANTHROPIC_API_KEY", *project_context)

    if not api_key:
        pytest.skip("Anthropic API key not configured")

    # Validate key format
    assert api_key.startswith(
        "sk-ant-"
    ), "Anthropic API key should start with 'sk-ant-'"
    assert len(api_key) > 20, "API key should be substantial length"


@pytest.mark.security
def test_openai_api_key_format(project_context):
    """Test OpenAI GPT-4 API key format validation"""
    api_key = get_hierarchical_env("OPENAI_API_KEY", *project_context)

    if not api_key:
        pytest.skip("OpenAI API key not configured")

    # Validate key format
    assert api_key.startswith("sk-"), "OpenAI API key should start with 'sk-'"
    assert len(api_key) > 20, "API key should be substantial length"


@pytest.mark.security
def test_google_api_key_format(project_context):
    """Test Google Gemini API key format validation"""
    api_key = get_hierarchical_env("GOOGLE_API_KEY", *project_context)

    if not api_key:
        pytest.skip("Google API key not configured")

    # Validate key format
    assert api_key.startswith("AIza"), "Google API key should start with 'AIza'"
    assert len(api_key) > 30, "API key should be substantial length"


# AWS Credentials Tests


@pytest.mark.security
@pytest.mark.integration
def test_aws_credentials_format(project_context):
    """Test AWS credentials are configured"""
    access_key = get_hierarchical_env("AWS_ACCESS_KEY_ID", *project_context)
    secret_key = get_hierarchical_env("AWS_SECRET_ACCESS_KEY", *project_context)

    if not access_key or not secret_key:
        pytest.skip("AWS credentials not configured")

    # Validate format
    assert len(access_key) > 15, "AWS Access Key should be substantial length"
    assert len(secret_key) > 30, "AWS Secret Key should be substantial length"
    assert access_key.isupper() or access_key.startswith(
        "AKIA"
    ), "AWS Access Key should be uppercase or start with AKIA"


@pytest.mark.security
@pytest.mark.integration
@pytest.mark.slow
def test_aws_sts_identity(project_context):
    """Test AWS credentials by verifying identity with STS"""
    import boto3

    access_key = get_hierarchical_env("AWS_ACCESS_KEY_ID", *project_context)
    secret_key = get_hierarchical_env("AWS_SECRET_ACCESS_KEY", *project_context)
    region = get_hierarchical_env("AWS_REGION", *project_context) or "us-east-1"

    if not access_key or not secret_key:
        pytest.skip("AWS credentials not configured")

    # Test STS to verify credentials
    sts_client = boto3.client(
        "sts",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    identity = sts_client.get_caller_identity()

    assert "Arn" in identity, "Should return valid IAM identity"
    assert "Account" in identity, "Should return AWS account ID"


# Database Tests


@pytest.mark.security
@pytest.mark.integration
def test_database_credentials_configured(project_context):
    """Test that database credentials are configured"""
    rds_host = get_hierarchical_env("RDS_HOST", *project_context)
    rds_username = get_hierarchical_env("RDS_USERNAME", *project_context)
    rds_password = get_hierarchical_env("RDS_PASSWORD", *project_context)
    rds_database = get_hierarchical_env("RDS_DATABASE", *project_context)

    if not all([rds_host, rds_username, rds_password, rds_database]):
        pytest.skip("RDS credentials not fully configured")

    # Validate basic format
    assert len(rds_host) > 5, "RDS host should be configured"
    assert len(rds_username) > 3, "RDS username should be configured"
    assert len(rds_password) > 8, "RDS password should be substantial"
    assert len(rds_database) > 3, "RDS database name should be configured"


@pytest.mark.security
@pytest.mark.integration
@pytest.mark.slow
def test_database_connection_read_only(project_context):
    """Test database connection with read-only query"""
    import psycopg2

    rds_host = get_hierarchical_env("RDS_HOST", *project_context)
    rds_port = get_hierarchical_env("RDS_PORT", *project_context) or "5432"
    rds_database = get_hierarchical_env("RDS_DATABASE", *project_context)
    rds_username = get_hierarchical_env("RDS_USERNAME", *project_context)
    rds_password = get_hierarchical_env("RDS_PASSWORD", *project_context)

    if not all([rds_host, rds_database, rds_username, rds_password]):
        pytest.skip("RDS credentials not fully configured")

    # Connect and test read
    conn = psycopg2.connect(
        host=rds_host,
        port=int(rds_port),
        database=rds_database,
        user=rds_username,
        password=rds_password,
        sslmode="require",
        connect_timeout=10,
    )

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    assert "PostgreSQL" in version, "Should connect to PostgreSQL database"


# Integration Tests


@pytest.mark.security
@pytest.mark.integration
@pytest.mark.skipif(
    not get_hierarchical_env("SLACK_WEBHOOK_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW"),
    reason="Slack webhook URL not configured",
)
def test_slack_webhook_format(project_context):
    """Test Slack webhook URL format"""
    webhook_url = get_hierarchical_env("SLACK_WEBHOOK_URL", *project_context)

    if not webhook_url:
        pytest.skip("Slack webhook URL not configured")

    # Validate format
    assert webhook_url.startswith(
        "https://hooks.slack.com/"
    ), "Slack webhook should start with https://hooks.slack.com/"
    assert len(webhook_url) > 50, "Webhook URL should be substantial length"


@pytest.mark.security
def test_s3_bucket_configured(project_context):
    """Test that S3 bucket is configured"""
    s3_bucket = get_hierarchical_env("S3_BUCKET", *project_context)

    if not s3_bucket:
        pytest.skip("S3 bucket not configured")

    # Validate format
    assert len(s3_bucket) > 3, "S3 bucket name should be substantial"
    assert (
        s3_bucket.islower() or "-" in s3_bucket
    ), "S3 bucket names should be lowercase or contain hyphens"


@pytest.mark.security
def test_no_placeholder_values(project_context):
    """Test that credentials don't contain placeholder values"""
    # Check common keys for placeholder patterns
    keys_to_check = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ]

    placeholder_patterns = [
        "YOUR_VALUE_HERE",
        "REPLACE_ME",
        "TODO",
        "CHANGEME",
        "PLACEHOLDER",
        "XXX",
    ]

    for key_name in keys_to_check:
        value = get_hierarchical_env(key_name, *project_context)
        if value:
            for pattern in placeholder_patterns:
                assert (
                    pattern not in value.upper()
                ), f"{key_name} contains placeholder value: {pattern}"


@pytest.mark.security
def test_credentials_not_empty_strings(project_context):
    """Test that configured credentials are not empty strings"""
    keys_to_check = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "RDS_HOST",
        "RDS_USERNAME",
    ]

    for key_name in keys_to_check:
        value = get_hierarchical_env(key_name, *project_context)
        if value is not None:  # If key exists
            assert (
                value.strip() != ""
            ), f"{key_name} is configured but contains only whitespace"
