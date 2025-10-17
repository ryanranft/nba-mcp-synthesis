"""
Real-time progress tracking dashboard for workflow
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowDashboard:
    """Track and report workflow progress"""

    def __init__(self, notification_manager):
        """
        Initialize dashboard

        Args:
            notification_manager: NotificationManager instance
        """
        self.notifier = notification_manager
        self.progress = {
            "current_stage": None,
            "books_analyzed": 0,
            "total_books": 0,
            "recommendations_generated": 0,
            "cost_spent": 0.0,
            "files_generated": 0,
            "linear_issues_created": 0,
            "start_time": None,
            "last_update": None,
        }

        # Progress tracking settings
        self.update_interval = 300  # 5 minutes
        self.last_progress_notification = None

        logger.info("Workflow dashboard initialized")

    def update_stage(self, stage: str):
        """Update current stage"""
        self.progress["current_stage"] = stage
        self.progress["last_update"] = datetime.now()
        logger.info(f"Stage updated: {stage}")

    def update_book_progress(self, books_analyzed: int, total_books: int):
        """Update book analysis progress"""
        self.progress["books_analyzed"] = books_analyzed
        self.progress["total_books"] = total_books
        self.progress["last_update"] = datetime.now()

        # Send progress update if significant change
        percentage = (books_analyzed / total_books) * 100 if total_books > 0 else 0

        # Send update every 25% or every 5 books
        should_update = (
            percentage % 25 == 0
            or books_analyzed % 5 == 0
            or books_analyzed == total_books
        )

        if should_update:
            asyncio.create_task(self._send_progress_update())

    def update_recommendations(self, count: int):
        """Update recommendations count"""
        self.progress["recommendations_generated"] = count
        self.progress["last_update"] = datetime.now()

    def update_cost(self, cost: float):
        """Update total cost"""
        self.progress["cost_spent"] = cost
        self.progress["last_update"] = datetime.now()

    def update_files_generated(self, count: int):
        """Update files generated count"""
        self.progress["files_generated"] = count
        self.progress["last_update"] = datetime.now()

    def update_linear_issues(self, count: int):
        """Update Linear issues count"""
        self.progress["linear_issues_created"] = count
        self.progress["last_update"] = datetime.now()

    def start_tracking(self):
        """Start progress tracking"""
        self.progress["start_time"] = datetime.now()
        logger.info("Progress tracking started")

    async def _send_progress_update(self):
        """Send progress update to Slack"""
        try:
            if not self.progress["total_books"]:
                return

            percentage = (
                self.progress["books_analyzed"] / self.progress["total_books"]
            ) * 100

            # Calculate ETA
            eta_minutes = self._calculate_eta()

            message = {
                "text": f"📊 Progress Update: {percentage:.0f}% Complete",
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Current Stage:*\n{self.progress['current_stage'] or 'Unknown'}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Progress:*\n{percentage:.0f}% complete",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Books Analyzed:*\n{self.progress['books_analyzed']}/{self.progress['total_books']}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Recommendations:*\n{self.progress['recommendations_generated']}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Cost Spent:*\n${self.progress['cost_spent']:.4f}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*ETA:*\n{eta_minutes:.0f} minutes",
                            },
                        ],
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_Last update: {datetime.now().strftime('%H:%M:%S')}_",
                            }
                        ],
                    },
                ],
            }

            await self.notifier.slack.send_notification(message)
            self.last_progress_notification = datetime.now()

        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

    def _calculate_eta(self) -> float:
        """Calculate estimated time to completion"""
        if not self.progress["start_time"] or not self.progress["total_books"]:
            return 0.0

        elapsed = (datetime.now() - self.progress["start_time"]).total_seconds() / 60
        books_remaining = self.progress["total_books"] - self.progress["books_analyzed"]

        if self.progress["books_analyzed"] == 0:
            return 0.0

        avg_time_per_book = elapsed / self.progress["books_analyzed"]
        return books_remaining * avg_time_per_book

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary"""
        percentage = 0.0
        if self.progress["total_books"] > 0:
            percentage = (
                self.progress["books_analyzed"] / self.progress["total_books"]
            ) * 100

        eta_minutes = self._calculate_eta()

        return {
            "current_stage": self.progress["current_stage"],
            "percentage_complete": percentage,
            "books_analyzed": self.progress["books_analyzed"],
            "total_books": self.progress["total_books"],
            "recommendations_generated": self.progress["recommendations_generated"],
            "cost_spent": self.progress["cost_spent"],
            "files_generated": self.progress["files_generated"],
            "linear_issues_created": self.progress["linear_issues_created"],
            "eta_minutes": eta_minutes,
            "elapsed_minutes": (
                (datetime.now() - self.progress["start_time"]).total_seconds() / 60
                if self.progress["start_time"]
                else 0
            ),
        }

    async def send_final_summary(self):
        """Send final progress summary"""
        try:
            summary = self.get_progress_summary()

            message = {
                "text": "📊 Final Progress Summary",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "📊 Final Summary"},
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Duration:*\n{summary['elapsed_minutes']:.1f} minutes",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Books Analyzed:*\n{summary['books_analyzed']}/{summary['total_books']}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Recommendations:*\n{summary['recommendations_generated']}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Cost:*\n${summary['cost_spent']:.4f}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Files Generated:*\n{summary['files_generated']}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Linear Issues:*\n{summary['linear_issues_created']}",
                            },
                        ],
                    },
                ],
            }

            await self.notifier.slack.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send final summary: {e}")
