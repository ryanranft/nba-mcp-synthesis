# Integration Tests for Unified Secrets Manager

import pytest
import os
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mcp_server.unified_secrets_manager import (
    UnifiedSecretsManager,
    get_secrets_manager,
    load_secrets_hierarchical,
)
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager


class TestSecretsManagerIntegration:
    """Integration tests for secrets manager"""

    def test_end_to_end_loading(self, temp_secrets_dir):
        """Test end-to-end secret loading process"""
        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")
        (secret_dir / "ANTHROPIC_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")
        (secret_dir / "DEEPSEEK_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Mock the directory structure
        with patch("os.path.exists", return_value=True):
            sm = UnifiedSecretsManager(base_path=temp_secrets_dir)
            sm.load_secrets("test_project", "TEST", "test", base_path=temp_secrets_dir)

            assert sm.project == "test_project"
            assert sm.sport == "TEST"
            assert sm.context == "test"
            assert len(sm.secrets) == 3
            assert len(sm.aliases) == 3
            assert sm.validate_secrets() is True

    def test_hierarchical_loader_integration(self, temp_secrets_dir):
        """Test integration with hierarchical loader"""
        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Mock the hierarchical loader
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Secrets loaded successfully"

            result = load_secrets_hierarchical("test_project", "TEST", "test")
            assert result is True

    def test_configuration_manager_integration(self, temp_secrets_dir):
        """Test integration with configuration manager"""
        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")
        (secret_dir / "ANTHROPIC_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")
        (secret_dir / "DEEPSEEK_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Mock the directory structure
        with patch("os.path.exists", return_value=True):
            config = UnifiedConfigurationManager("test_project", "test")

            assert config.project == "test_project"
            assert config.context == "test"
            assert config.context_key == "TEST"

    def test_environment_variable_integration(self, temp_secrets_dir):
        """Test integration with environment variables"""
        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Mock the directory structure
        with patch("os.path.exists", return_value=True):
            sm = UnifiedSecretsManager(base_path=temp_secrets_dir)
            sm.load_secrets("test_project", "TEST", "test", base_path=temp_secrets_dir)

            # Test environment variable access
            assert sm.get_secret("GOOGLE_API_KEY_TEST_PROJECT_TEST") == "test_key"
            assert sm.get_secret("GOOGLE_API_KEY") == "test_key"  # Alias

    def test_error_recovery_integration(self, temp_secrets_dir):
        """Test error recovery in integration scenarios"""
        sm = UnifiedSecretsManager(base_path=temp_secrets_dir)

        # Test with missing secrets directory
        with patch("os.path.exists", return_value=False):
            result = sm.load_secrets("invalid_project", "INVALID", "invalid")
            assert result is False

        # Test with partial secrets
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        with patch("os.path.exists", return_value=True):
            sm.load_secrets("test_project", "TEST", "test", base_path=temp_secrets_dir)

            # Should have partial secrets
            assert len(sm.secrets) == 1
            assert sm.validate_secrets() is False  # Missing required secrets

    def test_performance_integration(self, temp_secrets_dir):
        """Test performance in integration scenarios"""
        # Create many test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)

        for i in range(100):
            (secret_dir / f"TEST_SECRET_{i}_TEST_PROJECT_TEST.env").write_text(
                f"test_value_{i}"
            )

        # Mock the directory structure
        with patch("os.path.exists", return_value=True):
            sm = UnifiedSecretsManager(base_path=temp_secrets_dir)
            sm.load_secrets("test_project", "TEST", "test", base_path=temp_secrets_dir)

            assert len(sm.secrets) == 100
            assert len(sm.aliases) == 100

    def test_concurrent_access_integration(self, temp_secrets_dir):
        """Test concurrent access in integration scenarios"""
        import threading
        import time

        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        results = []

        def load_secrets():
            with patch("os.path.exists", return_value=True):
                sm = UnifiedSecretsManager(base_path=temp_secrets_dir)
                result = sm.load_secrets("test_project", "TEST", "test", base_path=temp_secrets_dir)
                results.append(result)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=load_secrets)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All threads should succeed
        assert all(results)
        assert len(results) == 5

    def test_memory_usage_integration(self, temp_secrets_dir):
        """Test memory usage in integration scenarios"""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)

        for i in range(1000):
            (secret_dir / f"TEST_SECRET_{i}_TEST_PROJECT_TEST.env").write_text(
                f"test_value_{i}"
            )

        # Mock the directory structure
        with patch("os.path.exists", return_value=True):
            sm = UnifiedSecretsManager(base_path=temp_secrets_dir)
            sm.load_secrets("test_project", "TEST", "test", base_path=temp_secrets_dir)

            # Get final memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable (less than 10MB)
            assert memory_increase < 10 * 1024 * 1024

    def test_file_system_integration(self, temp_secrets_dir):
        """Test file system integration"""
        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Test file system operations
        assert secret_dir.exists()
        assert (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").exists()

        # Test reading from file system
        with patch("os.path.exists", return_value=True):
            sm = UnifiedSecretsManager(base_path=temp_secrets_dir)
            sm.load_secrets("test_project", "TEST", "test", base_path=temp_secrets_dir)

            assert sm.get_secret("GOOGLE_API_KEY_TEST_PROJECT_TEST") == "test_key"

    def test_network_integration(self):
        """Test network integration (AWS Secrets Manager)"""
        sm = UnifiedSecretsManager(base_path=temp_secrets_dir)

        # Mock AWS client
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.get_secret_value.return_value = {
                "SecretString": '{"GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"}'
            }
            mock_boto.return_value = mock_client

            result = sm._load_from_aws("test-secret")
            assert result == {"GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "test_key"}

            # Verify AWS client was called
            mock_boto.assert_called_once()
            mock_client.get_secret_value.assert_called_once_with(SecretId="test-secret")

    def test_logging_integration(self, temp_secrets_dir):
        """Test logging integration"""
        import logging

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # Create test secret files
        secret_dir = Path(temp_secrets_dir) / "test_project" / ".env.test_project.test"
        secret_dir.mkdir(parents=True)
        (secret_dir / "GOOGLE_API_KEY_TEST_PROJECT_TEST.env").write_text("test_key")

        # Mock the directory structure
        with patch("os.path.exists", return_value=True):
            sm = UnifiedSecretsManager(base_path=temp_secrets_dir)
            sm.load_secrets("test_project", "TEST", "test", base_path=temp_secrets_dir)

            # Log some information
            logger.info(f"Loaded {len(sm.secrets)} secrets")
            logger.info(f"Created {len(sm.aliases)} aliases")

            # Verify logging worked
            assert len(sm.secrets) == 1
            assert len(sm.aliases) == 1

