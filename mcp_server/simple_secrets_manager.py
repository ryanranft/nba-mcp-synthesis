"""
Simplified Secrets Manager for NBA MCP Synthesis
Works with centralized secrets loaded via loader scripts
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from environment variables
    (Secrets should be pre-loaded by loader scripts)

    Returns:
        Database connection parameters
    """
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'nba_stats'),
        'port': int(os.getenv('DB_PORT', 5432))
    }

    # Verify critical database variables are loaded
    if not config['password']:
        logger.warning("DB_PASSWORD not found in environment. Check if secrets were loaded.")

    return config

def get_s3_bucket() -> str:
    """
    Get S3 bucket name from environment variables
    (Secrets should be pre-loaded by loader scripts)

    Returns:
        S3 bucket name
    """
    bucket = os.getenv('S3_BUCKET', 'nba-mcp-books-20251011')

    if not bucket:
        logger.warning("S3_BUCKET not found in environment. Check if secrets were loaded.")

    return bucket

def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for specified provider

    Args:
        provider: API provider ('google', 'deepseek', 'anthropic', 'openai')

    Returns:
        API key or None if not found
    """
    key_map = {
        'google': 'GOOGLE_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY'
    }

    env_var = key_map.get(provider.lower())
    if not env_var:
        logger.error(f"Unknown API provider: {provider}")
        return None

    api_key = os.getenv(env_var)
    if not api_key:
        logger.warning(f"{env_var} not found in environment. Check if secrets were loaded.")

    return api_key

def get_slack_config() -> Dict[str, str]:
    """
    Get Slack configuration

    Returns:
        Dictionary with Slack webhook URL and channel
    """
    return {
        'webhook_url': os.getenv('SLACK_WEBHOOK_URL', ''),
        'channel': os.getenv('SLACK_CHANNEL', '#nba-simulator-notifications')
    }

def get_linear_config() -> Dict[str, str]:
    """
    Get Linear configuration

    Returns:
        Dictionary with Linear API key, team ID, and project ID
    """
    return {
        'api_key': os.getenv('LINEAR_API_KEY', ''),
        'team_id': os.getenv('LINEAR_TEAM_ID', ''),
        'project_id': os.getenv('LINEAR_PROJECT_ID', '')
    }

def verify_secrets_loaded() -> bool:
    """
    Verify that critical secrets are loaded

    Returns:
        True if all critical secrets are present
    """
    critical_vars = [
        'GOOGLE_API_KEY',
        'DEEPSEEK_API_KEY',
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY'
    ]

    missing = []
    for var in critical_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        logger.error(f"Missing critical environment variables: {missing}")
        logger.error("Please run the appropriate loader script first:")
        logger.error("  python load_env_nba_mcp_synthesis_workflow.py")
        logger.error("  python load_env_nba_mcp_synthesis_local.py")
        return False

    logger.info("✅ All critical secrets verified")
    return True

