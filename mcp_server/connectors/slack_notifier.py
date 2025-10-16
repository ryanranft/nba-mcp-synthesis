"""
Slack Notifier
Sends notifications to Slack for MCP operations and synthesis results
"""

import json
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack webhook notifier for MCP operations"""

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        """Initialize Slack notifier"""
        self.webhook_url = webhook_url
        self.channel = channel

    async def send_notification(self, message: Dict[str, Any]) -> bool:
        """Send notification to Slack"""

        try:
            # Add channel if specified
            if self.channel and "channel" not in message:
                message["channel"] = self.channel

            # Send webhook request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                )

            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Slack notification failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    async def notify_synthesis_complete(
        self,
        operation: str,
        models_used: list,
        execution_time: float,
        tokens_used: int,
        success: bool = True
    ) -> bool:
        """Send synthesis completion notification"""

        emoji = "✅" if success else "❌"
        status = "completed" if success else "failed"

        message = {
            "text": f"{emoji} Multi-Model Synthesis {status}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Synthesis {status.title()}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Operation:*\n{operation}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Models:*\n{', '.join(models_used)}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{execution_time:.2f}s"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Tokens:*\n{tokens_used:,}"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Timestamp: {datetime.now().isoformat()}_"
                        }
                    ]
                }
            ]
        }

        return await self.send_notification(message)

    async def notify_workflow_start(self, config: Dict[str, Any]) -> bool:
        """Notify workflow started"""
        try:
            books_count = len(config.get('books', []))
            budget = config.get('budget', 0)

            message = {
                "text": f"🚀 Book Analysis Workflow Started - {books_count} books, ${budget:.2f} budget",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚀 Workflow Started"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Books to Analyze:*\n{books_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Budget:*\n${budget:.2f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Start Time:*\n{datetime.now().strftime('%H:%M:%S')}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Estimated Duration:*\n{books_count * 4} minutes"
                            }
                        ]
                    }
                ]
            }

            return await self.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send workflow start notification: {e}")
            return False

    async def notify_book_analysis_complete(
        self,
        book: str,
        recommendations: int,
        cost: float,
        time_taken: float = 0.0
    ) -> bool:
        """Notify single book analysis complete"""
        try:
            message = {
                "text": f"📚 Book Analysis Complete: {book} - {recommendations} recommendations",
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Book:*\n{book}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Recommendations:*\n{recommendations}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Cost:*\n${cost:.4f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:*\n{time_taken:.1f}s"
                            }
                        ]
                    }
                ]
            }

            return await self.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send book analysis complete notification: {e}")
            return False

    async def notify_integration_complete(
        self,
        phases_updated: int,
        files_generated: int,
        total_recommendations: int = 0,
        total_cost: float = 0.0
    ) -> bool:
        """Notify integration phase complete"""
        try:
            message = {
                "text": f"🔗 Integration Complete: {phases_updated} phases, {files_generated} files",
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Phases Updated:*\n{phases_updated}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Files Generated:*\n{files_generated}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Recommendations:*\n{total_recommendations}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Cost:*\n${total_cost:.4f}"
                            }
                        ]
                    }
                ]
            }

            return await self.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send integration complete notification: {e}")
            return False

    async def notify_workflow_complete(self, summary: Dict[str, Any]) -> bool:
        """Notify entire workflow complete"""
        try:
            total_books = summary.get('books_analyzed', 0)
            total_recommendations = summary.get('recommendations_generated', 0)
            total_cost = summary.get('total_cost', 0.0)
            files_generated = summary.get('files_generated', 0)
            linear_issues = summary.get('linear_issues_created', 0)

            message = {
                "text": f"✅ Workflow Complete: {total_books} books, {total_recommendations} recommendations, {files_generated} files",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Workflow Complete!"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Books:*\n{total_books}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Recommendations:*\n{total_recommendations}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Cost:*\n${total_cost:.4f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Files Generated:*\n{files_generated}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Linear Issues:*\n{linear_issues}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Completed:*\n{datetime.now().strftime('%H:%M:%S')}"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🎯 *Ready for Implementation*\n\nAll files have been generated in your NBA Simulator AWS project. Check Linear for issue tracking and implementation priority."
                        }
                    }
                ]
            }

            return await self.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send workflow complete notification: {e}")
            return False

    async def notify_mcp_tool_execution(
        self,
        tool_name: str,
        success: bool,
        execution_time: float,
        error: Optional[str] = None
    ) -> bool:
        """Send MCP tool execution notification"""

        emoji = "🔧" if success else "⚠️"

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *MCP Tool:* `{tool_name}`\n*Status:* {'Success' if success else 'Failed'}\n*Time:* {execution_time:.3f}s"
                }
            }
        ]

        if error:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{error[:200]}```"
                }
            })

        message = {
            "text": f"MCP Tool: {tool_name}",
            "blocks": blocks
        }

        return await self.send_notification(message)

    async def notify_daily_summary(
        self,
        total_syntheses: int,
        total_tools_called: int,
        total_tokens: int,
        errors_count: int
    ) -> bool:
        """Send daily summary notification"""

        message = {
            "text": "📊 Daily MCP Synthesis Summary",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Daily Summary"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Syntheses:*\n{total_syntheses}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Tools Called:*\n{total_tools_called}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Tokens Used:*\n{total_tokens:,}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Errors:*\n{errors_count}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
                        }
                    ]
                }
            ]
        }

        return await self.send_notification(message)

    async def notify_workflow_start(self, config: Dict[str, Any]) -> bool:
        """Notify workflow started"""
        try:
            books_count = len(config.get('books', []))
            budget = config.get('budget', 0)

            message = {
                "text": f"🚀 Book Analysis Workflow Started - {books_count} books, ${budget:.2f} budget",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚀 Workflow Started"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Books to Analyze:*\n{books_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Budget:*\n${budget:.2f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Start Time:*\n{datetime.now().strftime('%H:%M:%S')}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Estimated Duration:*\n{books_count * 4} minutes"
                            }
                        ]
                    }
                ]
            }

            return await self.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send workflow start notification: {e}")
            return False

    async def notify_book_analysis_complete(
        self,
        book: str,
        recommendations: int,
        cost: float,
        time_taken: float = 0.0
    ) -> bool:
        """Notify single book analysis complete"""
        try:
            message = {
                "text": f"📚 Book Analysis Complete: {book} - {recommendations} recommendations",
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Book:*\n{book}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Recommendations:*\n{recommendations}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Cost:*\n${cost:.4f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:*\n{time_taken:.1f}s"
                            }
                        ]
                    }
                ]
            }

            return await self.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send book analysis complete notification: {e}")
            return False

    async def notify_integration_complete(
        self,
        phases_updated: int,
        files_generated: int,
        total_recommendations: int = 0,
        total_cost: float = 0.0
    ) -> bool:
        """Notify integration phase complete"""
        try:
            message = {
                "text": f"🔗 Integration Complete: {phases_updated} phases, {files_generated} files",
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Phases Updated:*\n{phases_updated}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Files Generated:*\n{files_generated}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Recommendations:*\n{total_recommendations}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Cost:*\n${total_cost:.4f}"
                            }
                        ]
                    }
                ]
            }

            return await self.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send integration complete notification: {e}")
            return False

    async def notify_workflow_complete(self, summary: Dict[str, Any]) -> bool:
        """Notify entire workflow complete"""
        try:
            total_books = summary.get('books_analyzed', 0)
            total_recommendations = summary.get('recommendations_generated', 0)
            total_cost = summary.get('total_cost', 0.0)
            files_generated = summary.get('files_generated', 0)
            linear_issues = summary.get('linear_issues_created', 0)

            message = {
                "text": f"✅ Workflow Complete: {total_books} books, {total_recommendations} recommendations, {files_generated} files",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Workflow Complete!"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Books:*\n{total_books}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Recommendations:*\n{total_recommendations}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Cost:*\n${total_cost:.4f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Files Generated:*\n{files_generated}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Linear Issues:*\n{linear_issues}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Completed:*\n{datetime.now().strftime('%H:%M:%S')}"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🎯 *Ready for Implementation*\n\nAll files have been generated in your NBA Simulator AWS project. Check Linear for issue tracking and implementation priority."
                        }
                    }
                ]
            }

            return await self.send_notification(message)

        except Exception as e:
            logger.error(f"Failed to send workflow complete notification: {e}")
            return False
