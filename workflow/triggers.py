#!/usr/bin/env python3
"""
Workflow Triggers - Event-based workflow automation
Enables cross-chat coordination and automated process chaining
"""

import os
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of workflow triggers"""
    PROCESS_COMPLETE = "process_complete"
    PROCESS_FAILED = "process_failed"
    MCP_TOOL_COMPLETE = "mcp_tool_complete"
    SYNTHESIS_COMPLETE = "synthesis_complete"
    TEST_COMPLETE = "test_complete"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"


@dataclass
class TriggerEvent:
    """Represents a trigger event"""
    event_type: TriggerType
    source: str
    timestamp: str
    data: Dict[str, Any]
    workflow_id: Optional[str] = None


class WorkflowTrigger:
    """Manages workflow triggers and event routing"""

    def __init__(self):
        self.trigger_handlers: Dict[TriggerType, List[Callable]] = {}
        self.trigger_log: List[TriggerEvent] = []
        self.max_log_size = 1000

    def register_trigger(
        self,
        trigger_type: TriggerType,
        handler: Callable[[TriggerEvent], Any]
    ):
        """Register a trigger handler"""
        if trigger_type not in self.trigger_handlers:
            self.trigger_handlers[trigger_type] = []

        self.trigger_handlers[trigger_type].append(handler)
        logger.info(f"Registered trigger handler for {trigger_type.value}")

    def emit_event(self, event: TriggerEvent):
        """Emit a trigger event"""
        # Log event
        self.trigger_log.append(event)
        if len(self.trigger_log) > self.max_log_size:
            self.trigger_log = self.trigger_log[-self.max_log_size:]

        # Call handlers
        if event.event_type in self.trigger_handlers:
            for handler in self.trigger_handlers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Trigger handler error: {e}")

    def emit_process_complete(
        self,
        process_name: str,
        source: str,
        results: Optional[Dict] = None,
        workflow_id: Optional[str] = None
    ):
        """Convenience method to emit process complete event"""
        event = TriggerEvent(
            event_type=TriggerType.PROCESS_COMPLETE,
            source=source,
            timestamp=datetime.now().isoformat(),
            data={
                "process_name": process_name,
                "results": results or {}
            },
            workflow_id=workflow_id
        )
        self.emit_event(event)

    def emit_synthesis_complete(
        self,
        query: str,
        response: str,
        cost: float,
        source: str,
        workflow_id: Optional[str] = None
    ):
        """Emit synthesis completion event"""
        event = TriggerEvent(
            event_type=TriggerType.SYNTHESIS_COMPLETE,
            source=source,
            timestamp=datetime.now().isoformat(),
            data={
                "query": query,
                "response": response,
                "cost": cost
            },
            workflow_id=workflow_id
        )
        self.emit_event(event)

    def emit_mcp_tool_complete(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Any,
        source: str,
        workflow_id: Optional[str] = None
    ):
        """Emit MCP tool completion event"""
        event = TriggerEvent(
            event_type=TriggerType.MCP_TOOL_COMPLETE,
            source=source,
            timestamp=datetime.now().isoformat(),
            data={
                "tool_name": tool_name,
                "params": params,
                "result": result
            },
            workflow_id=workflow_id
        )
        self.emit_event(event)

    def emit_test_complete(
        self,
        test_suite: str,
        tests_passed: int,
        tests_failed: int,
        coverage: Optional[float] = None,
        source: str = "pytest",
        workflow_id: Optional[str] = None
    ):
        """Emit test completion event"""
        event = TriggerEvent(
            event_type=TriggerType.TEST_COMPLETE,
            source=source,
            timestamp=datetime.now().isoformat(),
            data={
                "test_suite": test_suite,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "coverage": coverage,
                "success": tests_failed == 0
            },
            workflow_id=workflow_id
        )
        self.emit_event(event)

    def get_recent_events(
        self,
        event_type: Optional[TriggerType] = None,
        limit: int = 10
    ) -> List[TriggerEvent]:
        """Get recent trigger events"""
        events = self.trigger_log

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events[-limit:]


# Global trigger instance
_trigger_instance: Optional[WorkflowTrigger] = None


def get_trigger_manager() -> WorkflowTrigger:
    """Get or create global trigger manager"""
    global _trigger_instance

    if _trigger_instance is None:
        _trigger_instance = WorkflowTrigger()

    return _trigger_instance
