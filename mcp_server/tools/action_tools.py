"""
Action Tools for MCP Server
Provides tools for saving results, logging, and notifications
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_server.connectors.slack_notifier import SlackNotifier

logger = logging.getLogger(__name__)


class ActionTools:
    """Tools for actions like saving, logging, and notifications"""

    def __init__(
        self,
        project_root: str,
        synthesis_output_dir: str,
        slack_notifier: Optional[SlackNotifier] = None,
    ):
        """
        Initialize action tools.

        Args:
            project_root: Root directory of the project
            synthesis_output_dir: Directory for saving synthesis results
            slack_notifier: Optional Slack notifier for sending notifications
        """
        self.project_root = Path(project_root).resolve()
        self.output_dir = Path(synthesis_output_dir).resolve()
        self.slack = slack_notifier

        # Create output directory if it doesn't exist
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Synthesis output directory: {self.output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")

        # Create logs directory for metadata
        self.logs_dir = self.output_dir / "logs"
        try:
            self.logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create logs directory: {e}")

    def _validate_output_path(
        self, file_path: str
    ) -> tuple[bool, Optional[Path], Optional[str]]:
        """
        Validate output file path to ensure it's within output directory.

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, resolved_path, error_message)
        """
        try:
            # Convert to absolute path if relative
            if os.path.isabs(file_path):
                path = Path(file_path).resolve()
            else:
                path = (self.output_dir / file_path).resolve()

            # Check if path is within output directory
            try:
                path.relative_to(self.output_dir)
            except ValueError:
                return False, None, f"Path outside output directory: {file_path}"

            return True, path, None

        except Exception as e:
            return False, None, f"Invalid path: {str(e)}"

    async def save_to_project(
        self, file_path: str, content: str, overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Save synthesis results to the project.

        Args:
            file_path: Path for the output file (relative to output_dir or absolute)
            content: Content to save
            overwrite: Whether to overwrite existing files (default: False)

        Returns:
            Dict with save status or error
        """
        try:
            # Validate path
            is_valid, path, error = self._validate_output_path(file_path)
            if not is_valid:
                logger.warning(f"Invalid save path: {file_path}")
                return {"success": False, "error": error, "file_path": file_path}

            # Check if file exists and overwrite is not allowed
            if path.exists() and not overwrite:
                logger.warning(f"File already exists and overwrite=False: {path}")
                return {
                    "success": False,
                    "error": f"File already exists. Use overwrite=True to replace it.",
                    "file_path": str(path),
                }

            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            logger.info(f"Saving file: {path} ({len(content)} bytes)")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            # Get file stats
            stats = path.stat()

            return {
                "success": True,
                "file_path": str(path),
                "relative_path": str(path.relative_to(self.output_dir)),
                "size": stats.st_size,
                "size_kb": round(stats.st_size / 1024, 2),
                "overwritten": path.exists() and overwrite,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error saving file: {e}", exc_info=True)
            return {"success": False, "error": str(e), "file_path": file_path}

    async def log_synthesis_result(
        self,
        operation: str,
        models_used: List[str],
        context_sources: List[str],
        tokens_used: int,
        cost: float,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log synthesis operation metadata.

        Args:
            operation: Description of the synthesis operation
            models_used: List of AI models used
            context_sources: List of context sources (RDS, S3, files, etc.)
            tokens_used: Total tokens consumed
            cost: Estimated cost in USD
            success: Whether operation succeeded (default: True)
            error: Error message if failed
            metadata: Additional metadata to log

        Returns:
            Dict with logging status
        """
        try:
            timestamp = datetime.now()

            # Create log entry
            log_entry = {
                "timestamp": timestamp.isoformat(),
                "operation": operation,
                "success": success,
                "models_used": models_used,
                "context_sources": context_sources,
                "tokens_used": tokens_used,
                "cost_usd": cost,
                "error": error,
                "metadata": metadata or {},
            }

            # Save to daily log file
            log_file = (
                self.logs_dir / f"synthesis_{timestamp.strftime('%Y-%m-%d')}.jsonl"
            )

            logger.info(f"Logging synthesis result: {operation} (success={success})")

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

            return {
                "success": True,
                "log_file": str(log_file),
                "timestamp": timestamp.isoformat(),
                "operation": operation,
            }

        except Exception as e:
            logger.error(f"Error logging synthesis result: {e}", exc_info=True)
            return {"success": False, "error": str(e), "operation": operation}

    async def send_slack_notification(
        self, message: str, blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send notification to Slack.

        Args:
            message: Text message to send
            blocks: Optional Slack block kit blocks for rich formatting

        Returns:
            Dict with notification status
        """
        try:
            # Check if Slack notifier is configured
            if not self.slack:
                logger.warning("Slack notifier not configured")
                return {
                    "success": False,
                    "error": "Slack notifier not configured. Set SLACK_WEBHOOK_URL in environment.",
                    "message": message,
                }

            logger.info(f"Sending Slack notification: {message[:50]}...")

            # Prepare notification payload
            payload = {"text": message}

            if blocks:
                payload["blocks"] = blocks

            # Send notification
            result = await self.slack.send_notification(payload)

            return {
                "success": result,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}", exc_info=True)
            return {"success": False, "error": str(e), "message": message}

    async def notify_synthesis_complete(
        self,
        operation: str,
        models_used: List[str],
        execution_time: float,
        tokens_used: int,
        cost: float,
        success: bool = True,
    ) -> Dict[str, Any]:
        """
        Send synthesis completion notification to Slack.

        Args:
            operation: Description of the synthesis operation
            models_used: List of AI models used
            execution_time: Execution time in seconds
            tokens_used: Total tokens consumed
            cost: Estimated cost in USD
            success: Whether operation succeeded

        Returns:
            Dict with notification status
        """
        try:
            if not self.slack:
                logger.debug("Slack notifier not configured, skipping notification")
                return {
                    "success": False,
                    "error": "Slack notifier not configured",
                    "operation": operation,
                }

            logger.info(f"Sending synthesis completion notification")

            # Use the SlackNotifier's built-in method
            result = await self.slack.notify_synthesis_complete(
                operation=operation,
                models_used=models_used,
                execution_time=execution_time,
                tokens_used=tokens_used,
                success=success,
            )

            return {
                "success": result,
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error sending synthesis notification: {e}", exc_info=True)
            return {"success": False, "error": str(e), "operation": operation}

    async def get_synthesis_logs(
        self, date: Optional[str] = None, max_entries: int = 100
    ) -> Dict[str, Any]:
        """
        Retrieve synthesis logs for a specific date.

        Args:
            date: Date in YYYY-MM-DD format (default: today)
            max_entries: Maximum number of log entries to return

        Returns:
            Dict with log entries or error
        """
        try:
            # Use today if no date specified
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            log_file = self.logs_dir / f"synthesis_{date}.jsonl"

            if not log_file.exists():
                return {
                    "success": True,
                    "date": date,
                    "log_count": 0,
                    "logs": [],
                    "message": f"No logs found for {date}",
                }

            logger.info(f"Reading synthesis logs for {date}")

            # Read log entries
            logs = []
            with open(log_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= max_entries:
                        break
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse log line: {line[:50]}")
                        continue

            return {
                "success": True,
                "date": date,
                "log_count": len(logs),
                "logs": logs,
                "log_file": str(log_file),
            }

        except Exception as e:
            logger.error(f"Error reading synthesis logs: {e}", exc_info=True)
            return {"success": False, "error": str(e), "date": date}

    async def create_synthesis_report(
        self, date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a summary report of synthesis operations.

        Args:
            date: Date in YYYY-MM-DD format (default: today)

        Returns:
            Dict with report summary or error
        """
        try:
            # Get logs for the date
            logs_result = await self.get_synthesis_logs(date=date)

            if not logs_result["success"]:
                return logs_result

            logs = logs_result["logs"]

            if not logs:
                return {
                    "success": True,
                    "date": logs_result["date"],
                    "message": "No synthesis operations found",
                }

            # Calculate statistics
            total_syntheses = len(logs)
            successful = sum(1 for log in logs if log.get("success", False))
            failed = total_syntheses - successful
            total_tokens = sum(log.get("tokens_used", 0) for log in logs)
            total_cost = sum(log.get("cost_usd", 0) for log in logs)

            # Collect unique models and sources
            all_models = set()
            all_sources = set()
            for log in logs:
                all_models.update(log.get("models_used", []))
                all_sources.update(log.get("context_sources", []))

            report = {
                "success": True,
                "date": logs_result["date"],
                "summary": {
                    "total_syntheses": total_syntheses,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": (
                        round(successful / total_syntheses * 100, 1)
                        if total_syntheses > 0
                        else 0
                    ),
                    "total_tokens": total_tokens,
                    "total_cost_usd": round(total_cost, 4),
                    "models_used": sorted(list(all_models)),
                    "context_sources": sorted(list(all_sources)),
                },
                "operations": [
                    {
                        "timestamp": log.get("timestamp"),
                        "operation": log.get("operation"),
                        "success": log.get("success"),
                        "tokens": log.get("tokens_used"),
                        "cost": log.get("cost_usd"),
                    }
                    for log in logs
                ],
            }

            logger.info(
                f"Generated synthesis report for {logs_result['date']}: {total_syntheses} operations"
            )

            return report

        except Exception as e:
            logger.error(f"Error creating synthesis report: {e}", exc_info=True)
            return {"success": False, "error": str(e), "date": date}
