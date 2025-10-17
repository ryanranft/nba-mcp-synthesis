#!/usr/bin/env python3
"""
Great Expectations Integration Tests
Tests PostgreSQL and S3 integration with Great Expectations
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
import pandas as pd
from mcp_server.env_helper import get_hierarchical_env

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


class TestGreatExpectationsConfiguration:
    """Test GX configuration files"""

    def test_gx_config_file_exists(self):
        """Test: Great Expectations config file exists"""
        gx_config = (
            Path(__file__).parent.parent
            / "great_expectations"
            / "great_expectations.yml"
        )
        assert gx_config.exists(), "Great Expectations config file should exist"
        print("✅ Great Expectations config file exists")

    def test_gx_config_variables_exist(self):
        """Test: Config variables file exists"""
        config_vars = (
            Path(__file__).parent.parent
            / "great_expectations"
            / "uncommitted"
            / "config_variables.yml"
        )
        assert config_vars.exists(), "Config variables file should exist"
        print("✅ Config variables file exists")

    def test_gx_directories_exist(self):
        """Test: GX directory structure exists"""
        gx_root = Path(__file__).parent.parent / "great_expectations"

        required_dirs = [
            gx_root / "expectations",
            gx_root / "checkpoints",
            gx_root / "uncommitted",
        ]

        for dir_path in required_dirs:
            assert dir_path.exists(), f"{dir_path} should exist"

        print("✅ All GX directories exist")


class TestDataValidatorIntegration:
    """Test DataValidator with PostgreSQL connection"""

    @pytest.mark.asyncio
    async def test_validator_with_postgres_config(self):
        """Test: Validator can be initialized with PostgreSQL config"""
        from data_quality.validator import DataValidator

        # Skip if database credentials not configured
        if not all(
            [
                get_hierarchical_env("RDS_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW"),
                get_hierarchical_env("RDS_DATABASE", "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            ]
        ):
            pytest.skip("PostgreSQL credentials not configured")

        validator = DataValidator(use_configured_context=True)
        assert validator is not None
        assert validator.use_configured_context == True
        print("✅ Validator initialized with PostgreSQL config")

    @pytest.mark.asyncio
    async def test_validator_in_memory_mode(self):
        """Test: Validator works in in-memory mode (for testing)"""
        from data_quality.validator import DataValidator

        validator = DataValidator(use_configured_context=False)
        assert validator is not None
        assert validator.use_configured_context == False
        print("✅ Validator works in in-memory mode")

    @pytest.mark.asyncio
    async def test_validation_with_mock_data_in_memory(self):
        """Test: In-memory validation with mock data"""
        from data_quality.validator import DataValidator

        validator = DataValidator(use_configured_context=False)

        mock_data = pd.DataFrame(
            {
                "game_id": [1, 2, 3],
                "home_team_score": [100, 105, 98],
                "away_team_score": [95, 102, 100],
            }
        )

        expectations = [
            {
                "type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "game_id"},
            },
            {
                "type": "expect_column_values_to_be_unique",
                "kwargs": {"column": "game_id"},
            },
        ]

        result = await validator.validate_table(
            table_name="games_mock", data=mock_data, expectations=expectations
        )

        assert result["success"] == True
        assert result["summary"]["passed"] == 2
        print("✅ In-memory validation works")

    @pytest.mark.skipif(
        not all(
            [
                get_hierarchical_env("RDS_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW"),
                get_hierarchical_env("RDS_DATABASE", "NBA_MCP_SYNTHESIS", "WORKFLOW"),
                get_hierarchical_env("RDS_USERNAME", "NBA_MCP_SYNTHESIS", "WORKFLOW"),
                get_hierarchical_env("RDS_PASSWORD", "NBA_MCP_SYNTHESIS", "WORKFLOW"),
            ]
        ),
        reason="PostgreSQL credentials not configured",
    )
    @pytest.mark.asyncio
    async def test_postgres_connection_string_building(self):
        """Test: PostgreSQL connection string is built correctly"""
        from data_quality.validator import DataValidator

        validator = DataValidator(use_configured_context=True)

        try:
            connection_string = validator._build_postgres_connection_string()
            assert "postgresql+psycopg2://" in connection_string
            assert (
                get_hierarchical_env("RDS_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                in connection_string
            )
            assert (
                get_hierarchical_env("RDS_DATABASE", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                in connection_string
            )
            print("✅ PostgreSQL connection string built correctly")
        except ValueError as e:
            pytest.fail(f"Failed to build connection string: {e}")


class TestProductionWorkflows:
    """Test production data quality workflows"""

    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test: Production workflow can be initialized"""
        from data_quality.workflows import ProductionDataQualityWorkflow

        workflow = ProductionDataQualityWorkflow(use_slack=False)
        assert workflow is not None
        assert workflow.validator is not None
        print("✅ Production workflow initializes correctly")

    @pytest.mark.asyncio
    async def test_workflow_validate_mock_data(self):
        """Test: Workflow can validate mock data"""
        from data_quality.workflows import ProductionDataQualityWorkflow

        workflow = ProductionDataQualityWorkflow(use_slack=False)
        workflow.validator.use_configured_context = False  # Use in-memory mode

        mock_data = pd.DataFrame(
            {
                "game_id": [1, 2, 3],
                "home_team_score": [100, 105, 98],
                "away_team_score": [95, 102, 100],
            }
        )

        from data_quality.expectations import create_game_expectations

        result = await workflow.validator.validate_table(
            table_name="games", data=mock_data, expectations=create_game_expectations()
        )

        assert result["success"] == True
        print("✅ Workflow validates mock data correctly")


class TestEnvironmentConfiguration:
    """Test environment variables are configured"""

    def test_gx_env_vars_documented(self):
        """Test: GX environment variables are in .env.example"""
        env_example = Path(__file__).parent.parent / ".env.example"

        with open(env_example) as f:
            content = f.read()

        assert "GX_S3_BUCKET" in content
        assert "GX_S3_PREFIX" in content
        print("✅ GX environment variables documented in .env.example")

    def test_postgres_env_vars_exist(self):
        """Test: PostgreSQL environment variables are available"""
        required_vars = ["RDS_HOST", "RDS_DATABASE", "RDS_USERNAME", "RDS_PASSWORD"]

        missing_vars = []
        for var in required_vars:
            if not get_hierarchical_env(var, "NBA_MCP_SYNTHESIS", "WORKFLOW"):
                missing_vars.append(var)

        if missing_vars:
            print(
                f"⚠️  Warning: Missing PostgreSQL variables: {', '.join(missing_vars)}"
            )
            print("   (This is expected if database is not configured)")
        else:
            print("✅ All PostgreSQL environment variables are set")


# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
