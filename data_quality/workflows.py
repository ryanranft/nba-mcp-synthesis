"""
Production Data Quality Workflows
Great Expectations workflows for validating NBA database in production
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Import validator
from data_quality.validator import DataValidator
from mcp_server.env_helper import get_hierarchical_env
from data_quality.expectations import (
    create_game_expectations,
    create_player_expectations,
    create_team_expectations,
)

# Optional: Slack notifications
try:
    from mcp_server.connectors.slack_notifier import SlackNotifier

    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False


class ProductionDataQualityWorkflow:
    """
    Production workflows for data quality validation

    Features:
    - Validates all NBA tables
    - Stores results to S3
    - Sends Slack alerts on failures
    - Provides summary reports
    """

    def __init__(self, use_slack: bool = True):
        """Initialize production workflow"""
        self.validator = DataValidator(use_configured_context=True)
        self.use_slack = use_slack and SLACK_AVAILABLE

        if self.use_slack:
            webhook_url = get_hierarchical_env(
                "SLACK_WEBHOOK_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            if webhook_url:
                self.slack = SlackNotifier(webhook_url=webhook_url)
            else:
                self.slack = None
                logger.warning("SLACK_WEBHOOK_URL not configured")
        else:
            self.slack = None

    async def validate_all_tables(self) -> Dict[str, Any]:
        """
        Validate all NBA tables with predefined expectations

        Returns:
            Summary of all validation results
        """
        logger.info("Starting full database validation")

        # Define tables to validate
        tables_to_validate = [
            ("games", create_game_expectations()),
            ("players", create_player_expectations()),
            ("teams", create_team_expectations()),
        ]

        results = {}
        overall_pass_rate = []
        failed_tables = []

        for table_name, expectations in tables_to_validate:
            logger.info(f"Validating table: {table_name}")

            try:
                result = await self.validator.validate_table(
                    table_name=table_name, expectations=expectations
                )

                results[table_name] = result

                if result.get("success"):
                    pass_rate = result["summary"]["pass_rate"]
                    overall_pass_rate.append(pass_rate)

                    if pass_rate < 1.0:
                        failed_tables.append(
                            {
                                "table": table_name,
                                "pass_rate": pass_rate,
                                "failed_count": result["summary"]["failed"],
                            }
                        )
                        logger.warning(
                            f"Table {table_name} has data quality issues: "
                            f"{pass_rate*100:.1f}% pass rate"
                        )
                else:
                    logger.error(
                        f"Validation failed for table {table_name}: {result.get('error')}"
                    )
                    failed_tables.append(
                        {"table": table_name, "error": result.get("error")}
                    )

            except Exception as e:
                logger.error(f"Error validating {table_name}: {e}")
                results[table_name] = {"success": False, "error": str(e)}
                failed_tables.append({"table": table_name, "error": str(e)})

        # Calculate overall summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "tables_validated": len(tables_to_validate),
            "tables_passed": len(tables_to_validate) - len(failed_tables),
            "tables_failed": len(failed_tables),
            "overall_pass_rate": (
                sum(overall_pass_rate) / len(overall_pass_rate)
                if overall_pass_rate
                else 0
            ),
            "failed_tables": failed_tables,
            "results": results,
        }

        # Send Slack alert if there are failures
        if failed_tables and self.slack:
            await self._send_quality_alert(summary)

        return summary

    async def validate_table_incremental(
        self, table_name: str, where_clause: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate only recent/new data in a table

        Args:
            table_name: Table to validate
            where_clause: SQL WHERE clause to filter data (e.g., "game_date > '2024-01-01'")

        Returns:
            Validation results
        """
        logger.info(f"Running incremental validation for {table_name}")

        # Build SQL query for incremental data
        if where_clause:
            sql = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 1000"
        else:
            sql = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 1000"

        # Query data
        try:
            import sqlalchemy as sa

            connection_string = self.validator._build_postgres_connection_string()
            engine = sa.create_engine(connection_string)

            import pandas as pd

            data = pd.read_sql(sql, engine)
            engine.dispose()

            logger.info(f"Queried {len(data)} rows for incremental validation")

        except Exception as e:
            logger.error(f"Failed to query incremental data: {e}")
            return {"success": False, "error": f"Failed to query data: {str(e)}"}

        # Get expectations for table
        from data_quality.expectations import get_expectations_for_table

        expectations = get_expectations_for_table(table_name)

        # Validate
        result = await self.validator.validate_table(
            table_name=table_name, data=data, expectations=expectations
        )

        # Alert on failures
        if result.get("success") and result["summary"]["failed"] > 0 and self.slack:
            await self._send_incremental_alert(table_name, result)

        return result

    async def get_validation_history(
        self, table_name: Optional[str] = None, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get validation history from S3

        Args:
            table_name: Specific table (optional, None for all tables)
            days: Number of days of history to retrieve

        Returns:
            Validation history summary
        """
        # This would query S3 for stored validation results
        # For now, return placeholder
        logger.info(f"Retrieving validation history (last {days} days)")

        return {
            "message": "Validation history retrieval not yet implemented",
            "note": "Validation results are stored in S3 automatically when using configured context",
            "s3_bucket": os.getenv("GX_S3_BUCKET"),
            "s3_prefix": os.getenv("GX_S3_PREFIX"),
        }

    async def _send_quality_alert(self, summary: Dict[str, Any]):
        """Send Slack alert for data quality issues"""
        if not self.slack:
            return

        try:
            failed_count = summary["tables_failed"]
            overall_pass = summary["overall_pass_rate"] * 100

            # Build message
            message = f"⚠️ *Data Quality Alert*\n\n"
            message += f"*Tables with Issues:* {failed_count}\n"
            message += f"*Overall Pass Rate:* {overall_pass:.1f}%\n\n"

            if summary["failed_tables"]:
                message += "*Failed Tables:*\n"
                for failure in summary["failed_tables"]:
                    table = failure["table"]
                    if "pass_rate" in failure:
                        pass_rate = failure["pass_rate"] * 100
                        failed = failure["failed_count"]
                        message += f"• {table}: {pass_rate:.1f}% ({failed} failed expectations)\n"
                    else:
                        error = failure.get("error", "Unknown error")
                        message += f"• {table}: Error - {error}\n"

            await self.slack.send_message(message)
            logger.info("Data quality alert sent to Slack")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def _send_incremental_alert(self, table_name: str, result: Dict[str, Any]):
        """Send Slack alert for incremental validation failures"""
        if not self.slack:
            return

        try:
            failed = result["summary"]["failed"]
            pass_rate = result["summary"]["pass_rate"] * 100

            message = f"⚠️ *Data Quality Issue Detected*\n\n"
            message += f"*Table:* {table_name}\n"
            message += f"*Pass Rate:* {pass_rate:.1f}%\n"
            message += f"*Failed Expectations:* {failed}\n"
            message += f"*Rows Validated:* {result['rows_validated']}\n"

            await self.slack.send_message(message)
            logger.info(f"Incremental validation alert sent for {table_name}")

        except Exception as e:
            logger.error(f"Failed to send incremental alert: {e}")


# Convenience functions


async def validate_nba_database() -> Dict[str, Any]:
    """
    Validate entire NBA database

    Returns:
        Validation summary
    """
    workflow = ProductionDataQualityWorkflow()
    return await workflow.validate_all_tables()


async def validate_recent_data(table_name: str, where_clause: str) -> Dict[str, Any]:
    """
    Validate only recent/new data

    Args:
        table_name: Table to validate
        where_clause: SQL WHERE clause for filtering

    Returns:
        Validation results
    """
    workflow = ProductionDataQualityWorkflow()
    return await workflow.validate_table_incremental(table_name, where_clause)


async def get_data_quality_report(days: int = 7) -> Dict[str, Any]:
    """
    Get data quality report from validation history

    Args:
        days: Number of days of history

    Returns:
        Data quality report
    """
    workflow = ProductionDataQualityWorkflow()
    return await workflow.get_validation_history(days=days)


# CLI entry point
async def main():
    """Main entry point for running validations from command line"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--incremental":
        # Incremental validation
        table = sys.argv[2] if len(sys.argv) > 2 else "games"
        where = (
            sys.argv[3]
            if len(sys.argv) > 3
            else "created_at > NOW() - INTERVAL '1 day'"
        )

        print(f"Running incremental validation for {table}...")
        result = await validate_recent_data(table, where)

        print(f"\nValidation Results:")
        print(f"  Pass Rate: {result['summary']['pass_rate']*100:.1f}%")
        print(
            f"  Passed: {result['summary']['passed']}/{result['summary']['total_expectations']}"
        )
        print(f"  Rows Validated: {result['rows_validated']}")

    else:
        # Full validation
        print("Running full database validation...")
        summary = await validate_nba_database()

        print(f"\nValidation Summary:")
        print(f"  Tables Validated: {summary['tables_validated']}")
        print(f"  Tables Passed: {summary['tables_passed']}")
        print(f"  Tables Failed: {summary['tables_failed']}")
        print(f"  Overall Pass Rate: {summary['overall_pass_rate']*100:.1f}%")

        if summary["failed_tables"]:
            print(f"\nFailed Tables:")
            for failure in summary["failed_tables"]:
                print(f"  - {failure['table']}")


if __name__ == "__main__":
    asyncio.run(main())
