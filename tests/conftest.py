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

# Add scripts directory to path (needed for test imports)
scripts_dir = str(Path(__file__).parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

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


# pytest-xdist hook to handle isolation marker
def pytest_xdist_setupnodes(config, specs):
    """Configure pytest-xdist to respect isolation marker"""
    pass  # Marker-based isolation configured in pytest_collection_modifyitems


def pytest_collection_modifyitems(config, items):
    """Modify test collection to group isolated tests together"""
    # Group tests marked with 'isolation' to run on same worker
    for item in items:
        if "isolation" in item.keywords:
            item.add_marker(pytest.mark.xdist_group(name="isolated_tests"))


@pytest.fixture(scope="function", autouse=True)
def cleanup_script_modules(request):
    """Clean up cached script modules between test files to prevent pollution

    This fixture does NOT clean between tests in the same file, only after
    all tests in a file complete. This allows tests within a file to share
    module state while preventing pollution between different test files.
    """
    import sys

    # Don't clean up for tests that import these modules
    test_file = request.node.fspath.basename
    if test_file in (
        "test_recommendation_integration.py",
        "test_recursive_book_analysis.py",
    ):
        yield
        return

    # List of script modules that might be cached
    script_modules = [
        "phase_mapper",
        "recommendation_integrator",
        "plan_override_manager",
        "cross_project_tracker",
        "recursive_book_analysis",
    ]

    yield

    # Clean up AFTER tests in other files run
    for module_name in script_modules:
        if module_name in sys.modules:
            del sys.modules[module_name]
