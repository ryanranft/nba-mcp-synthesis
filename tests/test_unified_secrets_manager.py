# Test Suite for Unified Secrets Manager

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

from mcp_server.unified_secrets_manager import (
    UnifiedSecretsManager,
    get_secrets_manager,
    load_secrets_hierarchical
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

    def test_load_secrets_from_files(self, temp_secrets_dir):
        """Test loading secrets from individual .env files"""
        sm = UnifiedSecretsManager()

        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)

        # Create test secret files
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_google_key")
        (secret_dir / "ANTHROPIC_API_KEY_TEST_PROJECT_TEST.env").write_text("test_anthropic_key")

        # Test loading secrets
        result = sm._load_secrets_from_files(str(secret_dir))

        assert result == {
            "GOOGLE_API_KEY_TEST_PROJECT_TEST": "test_google_key",
            "ANTHROPIC_API_KEY_TEST_PROJECT_TEST": "test_anthropic_key"
        }

    def test_context_detection(self):
        """Test automatic context detection"""
        sm = UnifiedSecretsManager()

        # Test CI/CD detection
        with patch.dict(os.environ, {'CI': 'true'}):
            context = sm._detect_context()
            assert context == 'test'

        # Test Docker detection
        with patch.dict(os.environ, {'DOCKER_CONTAINER': 'true'}):
            context = sm._detect_context()
            assert context == 'production'

        # Test development detection
        with patch.dict(os.environ, {'USER': 'developer'}):
            context = sm._detect_context()
            assert context == 'development'

    def test_naming_convention_validation(self):
        """Test naming convention validation"""
        sm = UnifiedSecretsManager()

        # Valid names
        assert sm._is_valid_naming_convention("GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW")
        assert sm._is_valid_naming_convention("DB_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        assert sm._is_valid_naming_convention("SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW")

        # Invalid names
        assert not sm._is_valid_naming_convention("GOOGLE_API_KEY")
        assert not sm._is_valid_naming_convention("INVALID_NAME")
        assert not sm._is_valid_naming_convention("GOOGLE_KEY_NBA_WORKFLOW")  # Missing resource type

    def test_aws_fallback(self):
        """Test AWS Secrets Manager fallback"""
        sm = UnifiedSecretsManager()

        # Mock AWS client
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_client.get_secret_value.return_value = {
                'SecretString': '{"GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"}'
            }
            mock_boto.return_value = mock_client

            result = sm._load_from_aws("test-secret")
            assert result == {"GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"}

    def test_hierarchical_loading(self):
        """Test hierarchical secret loading"""
        # Mock the hierarchical loader
        with patch('subprocess.run') as mock_run:
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
            "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW": "test_password"
        }

        sm._create_aliases()

        assert "GOOGLE_API_KEY" in sm.aliases
        assert "DB_PASSWORD" in sm.aliases
        assert sm.aliases["GOOGLE_API_KEY"] == "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"

    def test_load_secrets(self, temp_secrets_dir):
        """Test loading secrets with project, sport, and context"""
        sm = UnifiedSecretsManager()

        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Mock the directory structure
        with patch('os.path.exists', return_value=True):
            sm.load_secrets("test_project", "TEST", "test")

            assert sm.project == "test_project"
            assert sm.sport == "TEST"
            assert sm.context == "test"
            assert "GOOGLE_API_KEY_TEST_PROJECT_TEST" in sm.secrets

    def test_get_all_secrets(self):
        """Test getting all secrets"""
        sm = UnifiedSecretsManager()
        sm.secrets = {
            "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key",
            "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW": "test_password"
        }

        all_secrets = sm.get_all_secrets()
        assert len(all_secrets) == 2
        assert "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW" in all_secrets
        assert "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW" in all_secrets

    def test_get_aliases(self):
        """Test getting all aliases"""
        sm = UnifiedSecretsManager()
        sm.aliases = {
            "GOOGLE_API_KEY": "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW",
            "DB_PASSWORD": "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW"
        }

        all_aliases = sm.get_aliases()
        assert len(all_aliases) == 2
        assert "GOOGLE_API_KEY" in all_aliases
        assert "DB_PASSWORD" in all_aliases

    def test_validate_secrets(self):
        """Test secret validation"""
        sm = UnifiedSecretsManager()
        sm.secrets = {
            "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key",
            "ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key",
            "DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"
        }

        # Test with valid secrets
        assert sm.validate_secrets() is True

        # Test with missing required secrets
        sm.secrets = {}
        assert sm.validate_secrets() is False

    def test_export_secrets(self, temp_secrets_dir):
        """Test exporting secrets to file"""
        sm = UnifiedSecretsManager()
        sm.secrets = {
            "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key",
            "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW": "test_password"
        }
        sm.aliases = {
            "GOOGLE_API_KEY": "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW",
            "DB_PASSWORD": "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW"
        }

        output_file = Path(temp_secrets_dir) / "exported_secrets.env"
        sm.export_secrets(str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW" in content
        assert "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW" in content
        assert "GOOGLE_API_KEY" in content
        assert "DB_PASSWORD" in content

    def test_clear_secrets(self):
        """Test clearing secrets"""
        sm = UnifiedSecretsManager()
        sm.secrets = {"GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"}
        sm.aliases = {"GOOGLE_API_KEY": "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"}

        sm.clear_secrets()

        assert sm.secrets == {}
        assert sm.aliases == {}

    def test_reload_secrets(self, temp_secrets_dir):
        """Test reloading secrets"""
        sm = UnifiedSecretsManager()
        sm.project = "test_project"
        sm.sport = "TEST"
        sm.context = "test"

        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Mock the directory structure
        with patch('os.path.exists', return_value=True):
            sm.reload_secrets()

            assert "GOOGLE_API_KEY_TEST_PROJECT_TEST" in sm.secrets
            assert sm.secrets["GOOGLE_API_KEY_TEST_PROJECT_TEST"] == "test_key"

    def test_error_handling(self):
        """Test error handling"""
        sm = UnifiedSecretsManager()

        # Test with invalid project
        with patch('os.path.exists', return_value=False):
            result = sm.load_secrets("invalid_project", "INVALID", "invalid")
            assert result is False

        # Test with invalid context
        with patch('os.path.exists', return_value=False):
            result = sm.load_secrets("test_project", "TEST", "invalid")
            assert result is False

    def test_integration(self, temp_secrets_dir):
        """Test integration with real file system"""
        sm = UnifiedSecretsManager()

        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")
        (secret_dir / "ANTHROPIC_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Mock the directory structure
        with patch('os.path.exists', return_value=True):
            sm.load_secrets("test_project", "TEST", "test")

            assert sm.project == "test_project"
            assert sm.sport == "TEST"
            assert sm.context == "test"
            assert len(sm.secrets) == 2
            assert len(sm.aliases) == 2
            assert sm.validate_secrets() is True

