"""
Tests for Unified Secrets Manager integration

Updated to test the new unified secrets management system.
"""

import pytest
import os
import subprocess
import sys
from unittest.mock import Mock, patch, MagicMock
from mcp_server.unified_secrets_manager import (
    UnifiedSecretsManager,
    get_secrets_manager,
    load_secrets_hierarchical,
)


class TestUnifiedSecretsManager:
    """Test UnifiedSecretsManager class"""

    def test_initialization(self):
        """Test UnifiedSecretsManager initializes correctly"""
        sm = UnifiedSecretsManager()
        assert sm.project is None
        assert sm.sport is None
        assert sm.context is None
        assert sm.secrets == {}
        assert sm.aliases == {}

    def test_load_secrets_from_files(self):
        """Test loading secrets from individual .env files"""
        sm = UnifiedSecretsManager()

        # Mock the directory structure
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data="test_secret_value")
        ):

            secrets_dir = "/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production"

            result = sm._load_secrets_from_files(secrets_dir)
            assert result == {}

    def test_context_detection(self):
        """Test automatic context detection"""
        sm = UnifiedSecretsManager()

        # Test CI/CD detection
        with patch.dict(os.environ, {"CI": "true"}):
            context = sm._detect_context()
            assert context == "test"

        # Test Docker detection
        with patch.dict(os.environ, {"DOCKER_CONTAINER": "true"}):
            context = sm._detect_context()
            assert context == "production"

        # Test development detection
        with patch.dict(os.environ, {"USER": "developer"}):
            context = sm._detect_context()
            assert context == "development"

    def test_naming_convention_validation(self):
        """Test naming convention validation"""
        sm = UnifiedSecretsManager()

        # Valid names
        assert sm._is_valid_naming_convention(
            "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"
        )
        assert sm._is_valid_naming_convention(
            "DB_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT"
        )
        assert sm._is_valid_naming_convention(
            "SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW"
        )

        # Invalid names
        assert not sm._is_valid_naming_convention("GOOGLE_API_KEY")
        assert not sm._is_valid_naming_convention("INVALID_NAME")
        assert not sm._is_valid_naming_convention(
            "GOOGLE_KEY_NBA_WORKFLOW"
        )  # Missing resource type

    def test_aws_fallback(self):
        """Test AWS Secrets Manager fallback"""
        sm = UnifiedSecretsManager()

        # Mock AWS client
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.get_secret_value.return_value = {
                "SecretString": '{"GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"}'
            }
            mock_boto.return_value = mock_client

            result = sm._load_from_aws("test-secret")
            assert result == {"GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"}

    def test_hierarchical_loading(self):
        """Test hierarchical secret loading"""
        # Mock the hierarchical loader
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Secrets loaded successfully"

            result = load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
            assert result is True

    def test_get_secret(self):
        """Test getting a secret by name"""
        sm = UnifiedSecretsManager()
        sm.secrets = {"GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"}

        assert sm.get_secret("GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW") == "test_key"
        assert sm.get_secret("NONEXISTENT_KEY") is None

    def test_create_aliases(self):
        """Test creating backward-compatible aliases"""
        sm = UnifiedSecretsManager()
        sm.secrets = {
            "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key",
            "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW": "test_password",
        }

        sm._create_aliases()

        assert "GOOGLE_API_KEY" in sm.aliases
        assert "DB_PASSWORD" in sm.aliases
        assert (
            sm.aliases["GOOGLE_API_KEY"] == "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"
        )


def mock_open(read_data):
    """Helper function to mock file opening"""
    from unittest.mock import mock_open as _mock_open

    return _mock_open(read_data=read_data)


class TestSecretsManagerIntegration:
    """Integration tests for secrets manager"""

    def test_end_to_end_loading(self):
        """Test end-to-end secret loading process"""
        # This test would require actual secret files to be present
        # For now, we'll test the structure
        sm = UnifiedSecretsManager()

        # Test that the manager can be initialized
        assert sm is not None

        # Test that secrets can be loaded (even if empty)
        sm.load_secrets("nba-mcp-synthesis", "NBA", "production")
        assert isinstance(sm.secrets, dict)
        assert isinstance(sm.aliases, dict)


class TestConfigurationIntegration:
    """Test integration with unified configuration manager"""

    def test_config_with_secrets(self):
        """Test that configuration manager works with loaded secrets"""
        # Load secrets first
        result = load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")
        assert result is True

        # Test configuration manager
        from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

        config = UnifiedConfigurationManager("nba-mcp-synthesis", "production")

        # Verify configuration loaded
        assert config is not None
        assert config.api_config is not None
        assert config.workflow_config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
