"""
Data Validator using Great Expectations
Validates NBA data quality automatically with PostgreSQL and S3 integration
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Check if Great Expectations is available
try:
    import great_expectations as gx
    from great_expectations.core import ExpectationSuite
    from great_expectations.data_context import FileDataContext

    GX_AVAILABLE = True
except ImportError:
    GX_AVAILABLE = False
    logger.warning(
        "Great Expectations not installed. Install with: pip install great-expectations"
    )


class DataValidator:
    """
    Data validation using Great Expectations with PostgreSQL and S3 integration

    Usage:
        # Use with configured GX context (PostgreSQL + S3)
        validator = DataValidator(use_configured_context=True)
        result = await validator.validate_table("games")

        # Use with in-memory validation (for testing)
        validator = DataValidator(use_configured_context=False)
        result = await validator.validate_table("games", data=mock_df)
    """

    def __init__(
        self, context_path: Optional[str] = None, use_configured_context: bool = True
    ):
        """
        Initialize data validator

        Args:
            context_path: Path to Great Expectations context (default: ./great_expectations)
            use_configured_context: Use PostgreSQL/S3 config (True) or in-memory (False)
        """
        self.use_configured_context = use_configured_context
        # GX 1.7.0 uses gx/ subdirectory
        default_path = Path(__file__).parent.parent / "great_expectations" / "gx"
        self.context_path = context_path or str(default_path)
        self.context = None

        if GX_AVAILABLE:
            self._initialize_context()
        else:
            logger.error("Great Expectations not available")

    def _initialize_context(self):
        """Initialize Great Expectations context"""
        try:
            if not self.use_configured_context:
                # Always use ephemeral context when use_configured_context=False
                self.context = gx.get_context()
                logger.info(
                    "Great Expectations ephemeral context initialized (explicit)"
                )
            elif os.path.exists(self.context_path):
                # Use configured context with PostgreSQL and S3
                self.context = gx.get_context(context_root_dir=self.context_path)
                logger.info(
                    f"Great Expectations context initialized from {self.context_path}"
                )
            else:
                # Use ephemeral context for testing
                self.context = gx.get_context()
                logger.info("Great Expectations ephemeral context initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GX context: {e}")
            logger.warning("Falling back to ephemeral context")
            try:
                self.context = gx.get_context()
            except Exception as fallback_error:
                logger.error(f"Ephemeral context also failed: {fallback_error}")
                self.context = None

    def _build_postgres_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment variables"""
        # Try new naming convention first, then fallback to old
        username = (
            os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW")
            or os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_DEVELOPMENT")
            or os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_TEST")
            or os.getenv("RDS_USERNAME")
        )  # Fallback to old name

        password = (
            os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW")
            or os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT")
            or os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_TEST")
            or os.getenv("RDS_PASSWORD")
        )  # Fallback to old name

        host = (
            os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW")
            or os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT")
            or os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_TEST")
            or os.getenv("RDS_HOST")
        )  # Fallback to old name

        port = os.getenv("RDS_PORT", "5432")

        database = (
            os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW")
            or os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT")
            or os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_TEST")
            or os.getenv("RDS_DATABASE")
        )  # Fallback to old name

        if not all([username, password, host, database]):
            raise ValueError(
                "Missing required PostgreSQL credentials. "
                "Ensure RDS_USERNAME, RDS_PASSWORD, RDS_HOST, and RDS_DATABASE are set."
            )

        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

    async def validate_table(
        self,
        table_name: str,
        data: Optional[pd.DataFrame] = None,
        expectations: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a table using Great Expectations

        Args:
            table_name: Name of table to validate
            data: DataFrame to validate (optional, will query from PostgreSQL if not provided)
            expectations: Custom expectations (optional)

        Returns:
            Validation results with summary and details
        """
        if not GX_AVAILABLE:
            return {"success": False, "error": "Great Expectations not installed"}

        try:
            # If no data provided and using configured context, query from PostgreSQL
            if data is None and self.use_configured_context:
                connection_string = self._build_postgres_connection_string()

                try:
                    # Query data from PostgreSQL
                    import sqlalchemy as sa

                    engine = sa.create_engine(connection_string)
                    data = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 1000", engine)
                    engine.dispose()
                    logger.info(
                        f"Queried {len(data)} rows from PostgreSQL table: {table_name}"
                    )

                except Exception as e:
                    logger.error(f"Failed to query PostgreSQL: {e}")
                    return {
                        "success": False,
                        "error": f"Failed to query table from PostgreSQL: {str(e)}",
                    }

            # If still no data, query via MCP (fallback)
            elif data is None:
                try:
                    from synthesis.mcp_client import MCPClient

                    client = MCPClient()
                    await client.connect()

                    result = await client.call_tool(
                        "query_database",
                        {"sql": f"SELECT * FROM {table_name} LIMIT 1000"},
                    )

                    if not result.get("success"):
                        return {
                            "success": False,
                            "error": f"Failed to query table via MCP: {result.get('error')}",
                        }

                    data = pd.DataFrame(result.get("results", []))
                    await client.disconnect()
                    logger.info(
                        f"Queried {len(data)} rows via MCP for table: {table_name}"
                    )

                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to query table via MCP: {str(e)}",
                    }

            # Define common expectations
            if expectations is None:
                expectations = self._get_default_expectations(table_name)

            # Validate data
            validation_results = []
            for expectation in expectations:
                try:
                    exp_type = expectation["type"]
                    exp_kwargs = expectation.get("kwargs", {})

                    if exp_type == "expect_column_values_to_not_be_null":
                        column = exp_kwargs["column"]
                        if column not in data.columns:
                            validation_results.append(
                                {
                                    "expectation": exp_type,
                                    "column": column,
                                    "success": False,
                                    "error": f"Column '{column}' not found in data",
                                }
                            )
                            continue

                        null_count = data[column].isnull().sum()
                        validation_results.append(
                            {
                                "expectation": exp_type,
                                "column": column,
                                "success": null_count == 0,
                                "null_count": int(null_count),
                            }
                        )

                    elif exp_type == "expect_column_values_to_be_between":
                        column = exp_kwargs["column"]
                        if column not in data.columns:
                            validation_results.append(
                                {
                                    "expectation": exp_type,
                                    "column": column,
                                    "success": False,
                                    "error": f"Column '{column}' not found in data",
                                }
                            )
                            continue

                        min_val = exp_kwargs.get("min_value")
                        max_val = exp_kwargs.get("max_value")

                        out_of_range = data[
                            (data[column] < min_val) | (data[column] > max_val)
                        ].shape[0]

                        validation_results.append(
                            {
                                "expectation": exp_type,
                                "column": column,
                                "success": out_of_range == 0,
                                "out_of_range_count": int(out_of_range),
                                "min_value": min_val,
                                "max_value": max_val,
                            }
                        )

                    elif exp_type == "expect_column_values_to_be_unique":
                        column = exp_kwargs["column"]
                        if column not in data.columns:
                            validation_results.append(
                                {
                                    "expectation": exp_type,
                                    "column": column,
                                    "success": False,
                                    "error": f"Column '{column}' not found in data",
                                }
                            )
                            continue

                        duplicates = data[column].duplicated().sum()
                        validation_results.append(
                            {
                                "expectation": exp_type,
                                "column": column,
                                "success": duplicates == 0,
                                "duplicate_count": int(duplicates),
                            }
                        )

                except Exception as e:
                    validation_results.append(
                        {"expectation": exp_type, "success": False, "error": str(e)}
                    )

            # Summary
            total_expectations = len(validation_results)
            passed = sum(1 for r in validation_results if r.get("success"))
            failed_expectations = [
                r for r in validation_results if not r.get("success")
            ]

            result = {
                "success": True,
                "table_name": table_name,
                "rows_validated": len(data),
                "validation_time": datetime.now().isoformat(),
                "summary": {
                    "total_expectations": total_expectations,
                    "passed": passed,
                    "failed": total_expectations - passed,
                    "pass_rate": (
                        passed / total_expectations if total_expectations > 0 else 0
                    ),
                },
                "results": validation_results,
                "failed_expectations": failed_expectations,
            }

            # Store results to S3 if using configured context
            if self.use_configured_context and self.context:
                try:
                    self._store_validation_results_to_s3(table_name, result)
                except Exception as e:
                    logger.warning(f"Failed to store validation results to S3: {e}")

            return result

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"success": False, "error": str(e), "table_name": table_name}

    def _store_validation_results_to_s3(
        self, table_name: str, validation_result: Dict[str, Any]
    ):
        """Store validation results to S3 using GX validation store"""
        try:
            # This would use GX's validation store configuration
            # For now, log that results would be stored
            logger.info(
                f"Validation results for {table_name} ready for S3 storage "
                f"(Pass rate: {validation_result['summary']['pass_rate']*100:.1f}%)"
            )

            # In production, GX automatically stores validation results to S3
            # when validation is run through GX Checkpoints
            # See: data_quality/workflows.py for production validation workflows

        except Exception as e:
            logger.warning(f"Failed to store validation results: {e}")

    def _get_default_expectations(self, table_name: str) -> List[Dict]:
        """Get default expectations for a table"""
        # Import predefined expectations
        try:
            from data_quality.expectations import get_expectations_for_table

            expectations = get_expectations_for_table(table_name)
            if expectations:
                return expectations
        except ImportError:
            pass

        # Fallback: generic expectations
        return [
            {
                "type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "id"} if "id" in ["id"] else {"column": "game_id"},
            }
        ]


# Convenience function
async def validate_data(
    table_name: str, use_postgres: bool = True, **kwargs
) -> Dict[str, Any]:
    """
    Quick validation function

    Args:
        table_name: Table to validate
        use_postgres: Use PostgreSQL connection (True) or in-memory (False)
        **kwargs: Additional arguments for DataValidator

    Returns:
        Validation results
    """
    validator = DataValidator(use_configured_context=use_postgres)
    return await validator.validate_table(table_name, **kwargs)
