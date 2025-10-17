#!/usr/bin/env python3
"""
Enhanced Slack Notifier for Workflow Automation
Sends rich notifications for process lifecycle events and enables cross-chat coordination
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class ProcessStatus(Enum):
    """Process lifecycle statuses"""

    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProcessSource(Enum):
    """Source of the process"""

    CLAUDE_CODE = "claude_code"
    PYCHARM = "pycharm"
    MCP_SERVER = "mcp_server"
    WEB_CHAT = "web_chat"
    API = "api"
    WORKFLOW_ENGINE = "workflow_engine"


@dataclass
class ProcessEvent:
    """Represents a process lifecycle event"""

    process_id: str
    process_name: str
    status: ProcessStatus
    source: ProcessSource
    timestamp: str
    metadata: Dict[str, Any]
    thread_ts: Optional[str] = None  # Slack thread timestamp for grouping

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "process_id": self.process_id,
            "process_name": self.process_name,
            "status": self.status.value,
            "source": self.source.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "thread_ts": self.thread_ts,
        }


@dataclass
class WorkflowAction:
    """Action that can be triggered from Slack"""

    action_id: str
    action_name: str
    workflow_id: str
    callback: Optional[Callable] = None


class SlackNotifier:
    """Enhanced Slack notifier for workflow automation"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.process_threads: Dict[str, str] = {}  # process_id -> thread_ts
        self.pending_actions: Dict[str, WorkflowAction] = {}

    def _get_status_emoji(self, status: ProcessStatus) -> str:
        """Get emoji for status"""
        emoji_map = {
            ProcessStatus.STARTED: "🚀",
            ProcessStatus.IN_PROGRESS: "⏳",
            ProcessStatus.COMPLETED: "✅",
            ProcessStatus.FAILED: "❌",
            ProcessStatus.PENDING_APPROVAL: "⏸️",
            ProcessStatus.APPROVED: "👍",
            ProcessStatus.REJECTED: "👎",
        }
        return emoji_map.get(status, "ℹ️")

    def _get_status_color(self, status: ProcessStatus) -> str:
        """Get color for status"""
        color_map = {
            ProcessStatus.STARTED: "#36a64f",
            ProcessStatus.IN_PROGRESS: "#2196F3",
            ProcessStatus.COMPLETED: "#00C853",
            ProcessStatus.FAILED: "#FF0000",
            ProcessStatus.PENDING_APPROVAL: "#FFA500",
            ProcessStatus.APPROVED: "#00C853",
            ProcessStatus.REJECTED: "#FF0000",
        }
        return color_map.get(status, "#808080")

    def _get_source_icon(self, source: ProcessSource) -> str:
        """Get icon for source"""
        icon_map = {
            ProcessSource.CLAUDE_CODE: "💻",
            ProcessSource.PYCHARM: "🐍",
            ProcessSource.MCP_SERVER: "🔌",
            ProcessSource.WEB_CHAT: "🌐",
            ProcessSource.API: "🔗",
            ProcessSource.WORKFLOW_ENGINE: "⚙️",
        }
        return icon_map.get(source, "📋")

    def notify_process_event(
        self,
        event: ProcessEvent,
        next_steps: Optional[List[str]] = None,
        enable_actions: bool = False,
    ) -> Optional[str]:
        """
        Send process lifecycle notification to Slack

        Args:
            event: Process event to notify about
            next_steps: Optional list of next steps to display
            enable_actions: Whether to include interactive action buttons

        Returns:
            Thread timestamp for grouping related messages
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return None

        emoji = self._get_status_emoji(event.status)
        color = self._get_status_color(event.status)
        source_icon = self._get_source_icon(event.source)

        # Build message fields
        fields = [
            {"title": "Process", "value": event.process_name, "short": True},
            {
                "title": "Status",
                "value": f"{emoji} {event.status.value.replace('_', ' ').title()}",
                "short": True,
            },
            {
                "title": "Source",
                "value": f"{source_icon} {event.source.value.replace('_', ' ').title()}",
                "short": True,
            },
            {"title": "Process ID", "value": event.process_id, "short": True},
        ]

        # Add metadata fields
        if event.metadata:
            for key, value in event.metadata.items():
                # Skip large values
                if isinstance(value, str) and len(value) > 200:
                    value = value[:197] + "..."
                fields.append(
                    {
                        "title": key.replace("_", " ").title(),
                        "value": str(value),
                        "short": len(str(value)) < 40,
                    }
                )

        # Build attachment
        attachment = {
            "color": color,
            "title": f"{emoji} {event.process_name}",
            "fields": fields,
            "footer": "NBA MCP Synthesis - Workflow Automation",
            "ts": int(datetime.fromisoformat(event.timestamp).timestamp()),
        }

        # Add next steps if provided
        if next_steps:
            next_steps_text = "\n".join([f"• {step}" for step in next_steps])
            attachment["fields"].append(
                {"title": "Next Steps", "value": next_steps_text, "short": False}
            )

        # Build message
        message = {
            "text": f"{emoji} Process Update: {event.process_name}",
            "attachments": [attachment],
        }

        # Add to thread if this process has one
        if event.process_id in self.process_threads:
            message["thread_ts"] = self.process_threads[event.process_id]
        elif event.thread_ts:
            message["thread_ts"] = event.thread_ts
            self.process_threads[event.process_id] = event.thread_ts

        # Note: Interactive actions require Slack App with proper OAuth
        # For webhook-based notifications, we include action suggestions in text
        if enable_actions and event.status == ProcessStatus.PENDING_APPROVAL:
            attachment["fields"].append(
                {
                    "title": "Actions Available",
                    "value": "Reply to this thread with:\n• `approve` - Approve and continue\n• `reject` - Reject and halt\n• `retry` - Retry the process",
                    "short": False,
                }
            )

        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)

            if response.status_code == 200:
                logger.info(f"✅ Sent Slack notification for {event.process_id}")
                # Store thread timestamp if this is the first message
                # Note: Webhooks don't return thread_ts, so we track it manually
                if event.process_id not in self.process_threads:
                    # Use timestamp as pseudo thread_ts for tracking
                    thread_ts = str(int(datetime.now().timestamp()))
                    self.process_threads[event.process_id] = thread_ts
                    return thread_ts
                return self.process_threads.get(event.process_id)
            else:
                logger.error(
                    f"Failed to send Slack notification: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return None

    def notify_workflow_complete(
        self,
        workflow_id: str,
        workflow_name: str,
        duration_seconds: float,
        steps_completed: int,
        results: Optional[Dict] = None,
    ) -> bool:
        """Send workflow completion notification"""

        emoji = "🎉"
        color = "#00C853"

        fields = [
            {"title": "Workflow", "value": workflow_name, "short": True},
            {"title": "Duration", "value": f"{duration_seconds:.1f}s", "short": True},
            {"title": "Steps Completed", "value": str(steps_completed), "short": True},
        ]

        if results:
            for key, value in results.items():
                fields.append(
                    {
                        "title": key.replace("_", " ").title(),
                        "value": str(value),
                        "short": len(str(value)) < 40,
                    }
                )

        message = {
            "text": f"{emoji} Workflow Complete: {workflow_name}",
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} Workflow Complete: {workflow_name}",
                    "fields": fields,
                    "footer": "NBA MCP Synthesis - Workflow Automation",
                    "ts": int(datetime.now().timestamp()),
                }
            ],
        }

        # Add to thread if exists
        if workflow_id in self.process_threads:
            message["thread_ts"] = self.process_threads[workflow_id]

        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending workflow completion: {e}")
            return False

    def notify_workflow_failed(
        self,
        workflow_id: str,
        workflow_name: str,
        error_message: str,
        failed_step: str,
        duration_seconds: float,
    ) -> bool:
        """Send workflow failure notification"""

        emoji = "💥"
        color = "#FF0000"

        message = {
            "text": f"{emoji} Workflow Failed: {workflow_name}",
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} Workflow Failed: {workflow_name}",
                    "fields": [
                        {"title": "Failed Step", "value": failed_step, "short": True},
                        {
                            "title": "Duration",
                            "value": f"{duration_seconds:.1f}s",
                            "short": True,
                        },
                        {"title": "Error", "value": error_message, "short": False},
                    ],
                    "footer": "NBA MCP Synthesis - Workflow Automation",
                    "ts": int(datetime.now().timestamp()),
                }
            ],
        }

        # Add to thread if exists
        if workflow_id in self.process_threads:
            message["thread_ts"] = self.process_threads[workflow_id]

        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending workflow failure: {e}")
            return False

    def request_approval(
        self,
        process_id: str,
        process_name: str,
        description: str,
        timeout_minutes: int = 60,
    ) -> bool:
        """Request approval for a process"""

        event = ProcessEvent(
            process_id=process_id,
            process_name=process_name,
            status=ProcessStatus.PENDING_APPROVAL,
            source=ProcessSource.WORKFLOW_ENGINE,
            timestamp=datetime.now().isoformat(),
            metadata={"description": description, "timeout_minutes": timeout_minutes},
        )

        thread_ts = self.notify_process_event(
            event,
            next_steps=[
                "Review the request details",
                "Reply with 'approve' to continue or 'reject' to halt",
            ],
            enable_actions=True,
        )

        return thread_ts is not None

    def clear_thread(self, process_id: str):
        """Clear thread tracking for a process"""
        if process_id in self.process_threads:
            del self.process_threads[process_id]


# Global notifier instance
_notifier_instance: Optional[SlackNotifier] = None


def get_notifier() -> SlackNotifier:
    """Get or create global notifier instance"""
    global _notifier_instance

    if _notifier_instance is None:
        _notifier_instance = SlackNotifier()

    return _notifier_instance


# Convenience functions


def notify_process_started(
    process_id: str,
    process_name: str,
    source: ProcessSource,
    metadata: Optional[Dict] = None,
) -> Optional[str]:
    """Notify that a process has started"""
    notifier = get_notifier()
    event = ProcessEvent(
        process_id=process_id,
        process_name=process_name,
        status=ProcessStatus.STARTED,
        source=source,
        timestamp=datetime.now().isoformat(),
        metadata=metadata or {},
    )
    return notifier.notify_process_event(event)


def notify_process_progress(
    process_id: str,
    process_name: str,
    source: ProcessSource,
    progress_message: str,
    metadata: Optional[Dict] = None,
) -> Optional[str]:
    """Notify about process progress"""
    notifier = get_notifier()
    event = ProcessEvent(
        process_id=process_id,
        process_name=process_name,
        status=ProcessStatus.IN_PROGRESS,
        source=source,
        timestamp=datetime.now().isoformat(),
        metadata={**(metadata or {}), "progress": progress_message},
    )
    return notifier.notify_process_event(event)


def notify_process_completed(
    process_id: str,
    process_name: str,
    source: ProcessSource,
    results: Optional[Dict] = None,
    next_steps: Optional[List[str]] = None,
) -> Optional[str]:
    """Notify that a process has completed"""
    notifier = get_notifier()
    event = ProcessEvent(
        process_id=process_id,
        process_name=process_name,
        status=ProcessStatus.COMPLETED,
        source=source,
        timestamp=datetime.now().isoformat(),
        metadata=results or {},
    )
    return notifier.notify_process_event(event, next_steps=next_steps)


def notify_process_failed(
    process_id: str,
    process_name: str,
    source: ProcessSource,
    error_message: str,
    metadata: Optional[Dict] = None,
) -> Optional[str]:
    """Notify that a process has failed"""
    notifier = get_notifier()
    event = ProcessEvent(
        process_id=process_id,
        process_name=process_name,
        status=ProcessStatus.FAILED,
        source=source,
        timestamp=datetime.now().isoformat(),
        metadata={**(metadata or {}), "error": error_message},
    )
    return notifier.notify_process_event(event)


# CLI for testing
if __name__ == "__main__":
    import sys
    import uuid

    print("=" * 60)
    print("NBA MCP Synthesis - Slack Notifier Test")
    print("=" * 60)
    print()

    notifier = SlackNotifier()

    if not notifier.webhook_url:
        print("❌ SLACK_WEBHOOK_URL not set in environment")
        print()
        print("To configure:")
        print("1. Create a Slack webhook at https://api.slack.com/messaging/webhooks")
        print("2. Set: export SLACK_WEBHOOK_URL='your-webhook-url'")
        sys.exit(1)

    print("📡 Testing workflow notifications...")
    print()

    # Test process lifecycle
    process_id = str(uuid.uuid4())

    # Started
    print("1. Sending 'process started' notification...")
    thread_ts = notify_process_started(
        process_id,
        "Test NBA Analysis",
        ProcessSource.CLAUDE_CODE,
        {"query": "Analyze Lakers performance in 2023"},
    )
    print(f"   ✅ Sent (thread: {thread_ts})")

    # Progress
    print("2. Sending 'process progress' notification...")
    notify_process_progress(
        process_id,
        "Test NBA Analysis",
        ProcessSource.CLAUDE_CODE,
        "Retrieved 50 games from database",
        {"games_found": 50},
    )
    print("   ✅ Sent")

    # Completed
    print("3. Sending 'process completed' notification...")
    notify_process_completed(
        process_id,
        "Test NBA Analysis",
        ProcessSource.CLAUDE_CODE,
        {"games_analyzed": 50, "win_rate": "68%"},
        [
            "Review the analysis results",
            "Share with team",
            "Schedule follow-up analysis",
        ],
    )
    print("   ✅ Sent")

    # Test workflow completion
    print("4. Sending 'workflow complete' notification...")
    notifier.notify_workflow_complete(
        "workflow-123",
        "Automated Testing Pipeline",
        45.3,
        5,
        {"tests_passed": 71, "coverage": "98.6%"},
    )
    print("   ✅ Sent")

    print()
    print("=" * 60)
    print("✅ All test notifications sent!")
    print("Check your Slack channel to verify.")
    print("=" * 60)
