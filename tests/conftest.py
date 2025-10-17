# Test Configuration for Unified Secrets Manager

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
TEST_CONFIG = {
    "secrets_dir": "/tmp/test_secrets",
    "project": "test-project",
    "sport": "TEST",
    "context": "test",
    "mock_secrets": {
        "GOOGLE_API_KEY_TEST_PROJECT_TEST": "test_google_key",
        "ANTHROPIC_API_KEY_TEST_PROJECT_TEST": "test_anthropic_key",
        "DB_PASSWORD_TEST_PROJECT_TEST": "test_db_password",
    },
}


# Fixtures
@pytest.fixture
def temp_secrets_dir():
    """Create a temporary directory for secrets testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_secrets_manager():
    """Create a mock secrets manager"""
    from mcp_server.unified_secrets_manager import UnifiedSecretsManager

    sm = UnifiedSecretsManager()
    sm.secrets = TEST_CONFIG["mock_secrets"]
    sm.aliases = {
        "GOOGLE_API_KEY": "GOOGLE_API_KEY_TEST_PROJECT_TEST",
        "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY_TEST_PROJECT_TEST",
        "DB_PASSWORD": "DB_PASSWORD_TEST_PROJECT_TEST",
    }
    return sm


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager"""
    from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

    config = UnifiedConfigurationManager(TEST_CONFIG["project"], TEST_CONFIG["context"])
    return config
