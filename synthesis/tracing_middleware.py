#!/usr/bin/env python3
"""
Tracing Middleware for Synthesis System
Instruments synthesis operations with distributed tracing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps

try:
    from monitoring.tracing import get_tracer, trace, traced_span
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

logger = logging.getLogger(__name__)


def trace_synthesis_operation(operation_name: str):
    """
    Decorator to trace synthesis operations

    Args:
        operation_name: Name of the synthesis operation

    Example:
        @trace_synthesis_operation("deepseek_generate")
        async def generate_with_deepseek(prompt: str):
            return response
    """
    if not TRACING_AVAILABLE:
        def no_op_decorator(func):
            return func
        return no_op_decorator

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()

            # Extract metadata
            attributes = {
                "synthesis.operation": operation_name,
                "synthesis.function": func.__name__
            }

            # Try to extract common parameters
            if 'prompt' in kwargs:
                prompt = kwargs['prompt']
                attributes["synthesis.prompt_length"] = len(str(prompt))
            if 'model' in kwargs:
                attributes["synthesis.model"] = kwargs['model']
            if 'max_tokens' in kwargs:
                attributes["synthesis.max_tokens"] = kwargs['max_tokens']

            with traced_span(f"synthesis.{operation_name}", **attributes) as span:
                start_time = datetime.now()

                try:
                    result = await func(*args, **kwargs)

                    # Add result metadata
                    duration = (datetime.now() - start_time).total_seconds()
                    span.set_attribute("synthesis.duration_seconds", duration)

                    if isinstance(result, dict):
                        if 'tokens_used' in result:
                            span.set_attribute("synthesis.tokens_used", result['tokens_used'])
                        if 'cost' in result:
                            span.set_attribute("synthesis.cost", result['cost'])
                        if 'status' in result:
                            span.set_attribute("synthesis.status", result['status'])

                    span.add_event("synthesis_complete", duration=duration)
                    return result

                except Exception as e:
                    duration = (datetime.now() - start_time).total_seconds()
                    span.set_attribute("synthesis.duration_seconds", duration)
                    span.set_attribute("synthesis.error", str(e))
                    span.add_event("synthesis_failed", error=str(e))
                    raise

        return wrapper
    return decorator


def trace_mcp_call(tool_name: str):
    """
    Decorator to trace MCP tool calls

    Args:
        tool_name: Name of the MCP tool

    Example:
        @trace_mcp_call("query_database")
        async def query_database(sql: str):
            return results
    """
    if not TRACING_AVAILABLE:
        def no_op_decorator(func):
            return func
        return no_op_decorator

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()

            attributes = {
                "mcp.tool": tool_name,
                "mcp.function": func.__name__
            }

            # Extract parameters
            if 'sql_query' in kwargs:
                sql = kwargs['sql_query']
                attributes["mcp.sql_length"] = len(sql)
                # Truncate SQL for span attribute
                attributes["mcp.sql_preview"] = sql[:100] if len(sql) > 100 else sql

            if 'table_name' in kwargs:
                attributes["mcp.table"] = kwargs['table_name']

            if 'file_path' in kwargs:
                attributes["mcp.file"] = kwargs['file_path']

            with traced_span(f"mcp.{tool_name}", **attributes) as span:
                start_time = datetime.now()

                try:
                    result = await func(*args, **kwargs)

                    # Add result metadata
                    duration = (datetime.now() - start_time).total_seconds()
                    span.set_attribute("mcp.duration_seconds", duration)

                    if isinstance(result, dict):
                        if 'success' in result:
                            span.set_attribute("mcp.success", result['success'])
                        if 'row_count' in result:
                            span.set_attribute("mcp.rows_returned", result['row_count'])

                    span.add_event("mcp_call_complete", duration=duration)
                    return result

                except Exception as e:
                    duration = (datetime.now() - start_time).total_seconds()
                    span.set_attribute("mcp.duration_seconds", duration)
                    span.set_attribute("mcp.error", str(e))
                    span.add_event("mcp_call_failed", error=str(e))
                    raise

        return wrapper
    return decorator


def trace_workflow_step(step_name: str):
    """
    Decorator to trace workflow steps

    Args:
        step_name: Name of the workflow step

    Example:
        @trace_workflow_step("run_tests")
        async def run_tests_step(**params):
            return result
    """
    if not TRACING_AVAILABLE:
        def no_op_decorator(func):
            return func
        return no_op_decorator

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()

            attributes = {
                "workflow.step": step_name,
                "workflow.function": func.__name__
            }

            # Extract workflow context
            if 'workflow_id' in kwargs:
                attributes["workflow.id"] = kwargs['workflow_id']
            if 'workflow_name' in kwargs:
                attributes["workflow.name"] = kwargs['workflow_name']

            with traced_span(f"workflow.{step_name}", **attributes) as span:
                start_time = datetime.now()

                try:
                    result = await func(*args, **kwargs)

                    duration = (datetime.now() - start_time).total_seconds()
                    span.set_attribute("workflow.step_duration", duration)

                    if isinstance(result, dict):
                        if 'status' in result:
                            span.set_attribute("workflow.step_status", result['status'])

                    span.add_event("workflow_step_complete", duration=duration)
                    return result

                except Exception as e:
                    duration = (datetime.now() - start_time).total_seconds()
                    span.set_attribute("workflow.step_duration", duration)
                    span.set_attribute("workflow.step_error", str(e))
                    span.add_event("workflow_step_failed", error=str(e))
                    raise

        return wrapper
    return decorator


class TracingContext:
    """Context manager for adding custom tracing attributes"""

    def __init__(self, span_name: str, **attributes):
        self.span_name = span_name
        self.attributes = attributes
        self.span = None

    def __enter__(self):
        if TRACING_AVAILABLE:
            self.span = traced_span(self.span_name, **self.attributes).__enter__()
        return self

    def __exit__(self, *args):
        if self.span:
            self.span.__exit__(*args)

    def add_attribute(self, key: str, value: Any):
        """Add attribute to current span"""
        if self.span and hasattr(self.span, 'set_attribute'):
            self.span.set_attribute(key, value)

    def add_event(self, name: str, **attributes):
        """Add event to current span"""
        if self.span and hasattr(self.span, 'add_event'):
            self.span.add_event(name, attributes)
