#!/usr/bin/env python3
"""
Workflow Integration Hooks
Add event emission to synthesis and MCP processes
"""

import logging
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime

# Import workflow components
try:
    from workflow.triggers import get_trigger_manager, TriggerType
    from monitoring.slack_notifier import (
        get_notifier,
        ProcessSource,
        notify_process_started,
        notify_process_completed,
        notify_process_failed,
    )

    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False

logger = logging.getLogger(__name__)


def with_workflow_notifications(
    process_name: str,
    source: ProcessSource = ProcessSource.WORKFLOW_ENGINE,
    notify_slack: bool = True,
    emit_events: bool = True,
):
    """
    Decorator to add workflow notifications to any async function

    Args:
        process_name: Name of the process
        source: Source of the process
        notify_slack: Whether to send Slack notifications
        emit_events: Whether to emit workflow trigger events

    Example:
        @with_workflow_notifications("NBA Data Analysis", ProcessSource.CLAUDE_CODE)
        async def analyze_data(query: str):
            # Your code here
            return results
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not WORKFLOW_AVAILABLE:
                # If workflow not available, just execute function
                return await func(*args, **kwargs)

            # Generate process ID
            import uuid

            process_id = str(uuid.uuid4())

            # Extract metadata from function args/kwargs
            metadata = {
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            }

            # Add specific metadata based on kwargs
            if "query" in kwargs:
                metadata["query"] = kwargs["query"][:200]  # Truncate long queries
            if "table_name" in kwargs:
                metadata["table_name"] = kwargs["table_name"]

            # Notify start
            if notify_slack:
                notify_process_started(process_id, process_name, source, metadata)

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Extract result metadata
                result_metadata = {}
                if isinstance(result, dict):
                    # Extract useful info from result
                    for key in [
                        "status",
                        "cost",
                        "tokens_used",
                        "row_count",
                        "success",
                    ]:
                        if key in result:
                            result_metadata[key] = result[key]

                # Notify completion
                if notify_slack:
                    notify_process_completed(
                        process_id, process_name, source, result_metadata
                    )

                # Emit event
                if emit_events:
                    trigger_manager = get_trigger_manager()
                    trigger_manager.emit_process_complete(
                        process_name, source.value, result_metadata
                    )

                return result

            except Exception as e:
                # Notify failure
                if notify_slack:
                    notify_process_failed(
                        process_id, process_name, source, str(e), metadata
                    )

                # Re-raise exception
                raise

        return wrapper

    return decorator


def notify_synthesis_complete(
    query: str,
    response: str,
    cost: float,
    source: str = "synthesis",
    workflow_id: Optional[str] = None,
):
    """
    Notify that a synthesis process has completed

    Args:
        query: The query that was processed
        response: The synthesized response
        cost: Cost of the synthesis
        source: Source of the synthesis
        workflow_id: Optional workflow ID
    """
    if not WORKFLOW_AVAILABLE:
        return

    trigger_manager = get_trigger_manager()
    trigger_manager.emit_synthesis_complete(
        query=query,
        response=response,
        cost=cost,
        source=source,
        workflow_id=workflow_id,
    )


def notify_mcp_tool_complete(
    tool_name: str,
    params: Dict[str, Any],
    result: Any,
    source: str = "mcp_server",
    workflow_id: Optional[str] = None,
):
    """
    Notify that an MCP tool has completed

    Args:
        tool_name: Name of the MCP tool
        params: Parameters passed to the tool
        result: Result from the tool
        source: Source of the call
        workflow_id: Optional workflow ID
    """
    if not WORKFLOW_AVAILABLE:
        return

    trigger_manager = get_trigger_manager()
    trigger_manager.emit_mcp_tool_complete(
        tool_name=tool_name,
        params=params,
        result=result,
        source=source,
        workflow_id=workflow_id,
    )


def notify_test_complete(
    test_suite: str,
    tests_passed: int,
    tests_failed: int,
    coverage: Optional[float] = None,
    source: str = "pytest",
    workflow_id: Optional[str] = None,
):
    """
    Notify that a test suite has completed

    Args:
        test_suite: Name of the test suite
        tests_passed: Number of tests passed
        tests_failed: Number of tests failed
        coverage: Optional coverage percentage
        source: Source of the tests
        workflow_id: Optional workflow ID
    """
    if not WORKFLOW_AVAILABLE:
        return

    trigger_manager = get_trigger_manager()
    trigger_manager.emit_test_complete(
        test_suite=test_suite,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        coverage=coverage,
        source=source,
        workflow_id=workflow_id,
    )


# Convenience function for simple process notifications
async def run_with_notifications(
    process_name: str,
    func,
    *args,
    source: ProcessSource = ProcessSource.WORKFLOW_ENGINE,
    notify_slack: bool = True,
    **kwargs
):
    """
    Run a function with workflow notifications

    Args:
        process_name: Name of the process
        func: Function to execute
        *args: Arguments for the function
        source: Source of the process
        notify_slack: Whether to send Slack notifications
        **kwargs: Keyword arguments for the function

    Returns:
        Result from the function
    """
    if not WORKFLOW_AVAILABLE:
        # If workflow not available, just execute function
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    import uuid
    import asyncio

    process_id = str(uuid.uuid4())

    # Notify start
    if notify_slack:
        notify_process_started(process_id, process_name, source, {})

    try:
        # Execute function
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        # Notify completion
        if notify_slack:
            notify_process_completed(process_id, process_name, source, {})

        return result

    except Exception as e:
        # Notify failure
        if notify_slack:
            notify_process_failed(process_id, process_name, source, str(e))
        raise
