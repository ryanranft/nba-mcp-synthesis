"""
AWS Secrets Manager integration for NBA MCP
Provides secure credential retrieval

⚠️  DEPRECATION NOTICE ⚠️
This module is deprecated and will be removed in a future version.
Please migrate to the new unified secrets management system:

1. Use mcp_server.unified_secrets_manager.UnifiedSecretsManager
2. Use /Users/ryanranft/load_env_hierarchical.py for loading secrets
3. Use context-rich naming convention (e.g., GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW)

Migration Guide:
- Replace SecretsManager with UnifiedSecretsManager
- Use hierarchical secret loading with context detection
- Store secrets in /Users/ryanranft/Desktop/++/big_cat_bets_assets/ structure
- Load secrets using the hierarchical loader before initializing other components

For more details, see:
- /centralized-secrets-management.plan.md
- mcp_server/unified_secrets_manager.py
- /Users/ryanranft/load_env_hierarchical.py

This file will be removed in version 2.0.0
"""
import boto3
import json
import os
from functools import lru_cache
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    """Manages secure credential retrieval from AWS Secrets Manager"""

    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize Secrets Manager client

        Args:
            region_name: AWS region for Secrets Manager
        """
        # Deprecation warning
        import warnings
        warnings.warn(
            "SecretsManager is deprecated. Use UnifiedSecretsManager instead. "
            "See mcp_server/unified_secrets_manager.py for migration guide.",
            DeprecationWarning,
            stacklevel=2
        )

        self.region_name = region_name
        self.client = None
        self._initialize_client()
        logger.warning(f"⚠️  DEPRECATED: SecretsManager initialized for region: {region_name}")
        logger.warning("⚠️  Please migrate to UnifiedSecretsManager")

    def _initialize_client(self):
        """Initialize boto3 Secrets Manager client"""
        try:
            self.client = boto3.client('secretsmanager', region_name=self.region_name)
            logger.info(f"✅ Secrets Manager client initialized (region: {self.region_name})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Secrets Manager client: {e}")
            raise

    @lru_cache(maxsize=10)
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager

        Args:
            secret_name: Name of the secret in Secrets Manager

        Returns:
            Dictionary containing secret values

        Raises:
            Exception if secret cannot be retrieved
        """
        try:
            logger.debug(f"Fetching secret: {secret_name}")

            response = self.client.get_secret_value(SecretId=secret_name)

            # Parse secret string
            if 'SecretString' in response:
                secret = json.loads(response['SecretString'])
                logger.debug(f"✅ Secret retrieved: {secret_name}")
                return secret
            else:
                # Binary secrets (not used for this project)
                raise ValueError(f"Secret {secret_name} is binary, expected JSON")

        except self.client.exceptions.ResourceNotFoundException:
            logger.error(f"❌ Secret not found: {secret_name}")
            raise ValueError(f"Secret '{secret_name}' not found in Secrets Manager")
        except Exception as e:
            logger.error(f"❌ Error retrieving secret {secret_name}: {e}")
            raise

    def get_database_credentials(self, environment: str = 'production') -> Dict[str, Any]:
        """
        Get database credentials

        Args:
            environment: Environment name (production, staging, dev)

        Returns:
            Database connection parameters
        """
        secret_name = f'nba-mcp/{environment}/database'
        return self.get_secret(secret_name)

    def get_aws_credentials(self, environment: str = 'production') -> Dict[str, Any]:
        """
        Get AWS credentials

        Args:
            environment: Environment name

        Returns:
            AWS credentials
        """
        secret_name = f'nba-mcp/{environment}/aws'
        return self.get_secret(secret_name)

    def get_s3_config(self, environment: str = 'production') -> Dict[str, Any]:
        """
        Get S3 configuration

        Args:
            environment: Environment name

        Returns:
            S3 configuration
        """
        secret_name = f'nba-mcp/{environment}/s3'
        return self.get_secret(secret_name)

    def rotate_secret(self, secret_name: str) -> bool:
        """
        Trigger secret rotation

        Args:
            secret_name: Name of secret to rotate

        Returns:
            True if rotation triggered successfully
        """
        try:
            self.client.rotate_secret(SecretId=secret_name)
            logger.info(f"✅ Secret rotation triggered: {secret_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to rotate secret {secret_name}: {e}")
            return False

    def clear_cache(self):
        """Clear the secret cache (useful for testing or after rotation)"""
        self.get_secret.cache_clear()
        logger.info("🔄 Secret cache cleared")


# Global instance
_secrets_manager: Optional[SecretsManager] = None

def get_secrets_manager() -> SecretsManager:
    """Get or create global SecretsManager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        region = os.getenv('AWS_REGION', 'us-east-1')
        _secrets_manager = SecretsManager(region_name=region)
    return _secrets_manager


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from Secrets Manager or fall back to env vars

    Returns:
        Database connection parameters
    """
    # Check if using local credentials
    if os.getenv('USE_LOCAL_CREDENTIALS', '').lower() == 'true':
        logger.info("Using local credentials from .env")
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'nba_stats'),
            'port': int(os.getenv('DB_PORT', 5432))
        }

    # Use Secrets Manager
    env = os.getenv('NBA_MCP_ENV', 'production')
    sm = get_secrets_manager()
    return sm.get_database_credentials(environment=env)


def get_s3_bucket() -> str:
    """
    Get S3 bucket name from Secrets Manager or env var

    Returns:
        S3 bucket name
    """
    # Check if using local credentials
    if os.getenv('USE_LOCAL_CREDENTIALS', '').lower() == 'true':
        return os.getenv('S3_BUCKET', 'nba-mcp-books-20251011')

    # Use Secrets Manager
    env = os.getenv('NBA_MCP_ENV', 'production')
    sm = get_secrets_manager()
    config = sm.get_s3_config(environment=env)
    return config['bucket']

