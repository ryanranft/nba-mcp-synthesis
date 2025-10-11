"""
Structured Logging Configuration for NBA MCP Server

Provides JSON-based structured logging for better monitoring and debugging.
Based on best practices from ebook-mcp implementation.
"""

import logging
import json
import sys
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted log messages.

    Provides consistent structured logging across the application with
    support for additional context fields.
    """

    def __init__(self, name: str, log_level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Setup console handler with JSON formatter"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.logger.level)

        # Use basic formatter (JSON formatting done in log methods)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def _log_json(self, level: int, message: str, **context):
        """Log a JSON-formatted message with context"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": logging.getLevelName(level),
            "message": message,
            **context
        }

        # Log as JSON string
        self.logger.log(level, json.dumps(log_data))

    def debug(self, message: str, **context):
        """Log debug message with context"""
        self._log_json(logging.DEBUG, message, **context)

    def info(self, message: str, **context):
        """Log info message with context"""
        self._log_json(logging.INFO, message, **context)

    def warning(self, message: str, **context):
        """Log warning message with context"""
        self._log_json(logging.WARNING, message, **context)

    def error(self, message: str, **context):
        """Log error message with context"""
        self._log_json(logging.ERROR, message, **context)

    def critical(self, message: str, **context):
        """Log critical message with context"""
        self._log_json(logging.CRITICAL, message, **context)


# Global logger instances cache
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, log_level: int = logging.INFO) -> StructuredLogger:
    """
    Get or create a structured logger for the given module name.

    Args:
        name: Logger name (typically __name__)
        log_level: Logging level

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, log_level)
    return _loggers[name]


def log_operation(operation_name: str):
    """
    Decorator to log operations with structured JSON output.

    Logs operation start, completion, and duration with structured data.

    Usage:
        @log_operation("book_chapter_extraction")
        async def extract_chapter(book_path, chapter_id):
            ...

    Args:
        operation_name: Name of the operation being logged
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger = get_logger(func.__module__)

            # Log operation start
            logger.info(
                f"Operation started: {operation_name}",
                operation=operation_name,
                function=func.__name__,
                status="started"
            )

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Calculate duration
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Log success
                logger.info(
                    f"Operation completed: {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    status="completed",
                    duration_seconds=duration
                )

                return result

            except Exception as e:
                # Calculate duration
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Log failure
                logger.error(
                    f"Operation failed: {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    status="failed",
                    duration_seconds=duration,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger = get_logger(func.__module__)

            # Log operation start
            logger.info(
                f"Operation started: {operation_name}",
                operation=operation_name,
                function=func.__name__,
                status="started"
            )

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Calculate duration
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Log success
                logger.info(
                    f"Operation completed: {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    status="completed",
                    duration_seconds=duration
                )

                return result

            except Exception as e:
                # Calculate duration
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Log failure
                logger.error(
                    f"Operation failed: {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    status="failed",
                    duration_seconds=duration,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )

                raise

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def setup_file_logging(
    log_dir: str = "logs",
    log_file_prefix: str = "nba-mcp",
    log_level: int = logging.INFO
) -> None:
    """
    Setup file-based logging with rotation.

    Creates a logs directory and adds file handlers to all existing loggers.

    Args:
        log_dir: Directory for log files
        log_file_prefix: Prefix for log file names
        log_level: Logging level
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_path / f"{log_file_prefix}_{timestamp}.log"

    # Setup file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)

    # JSON formatter for file logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level)

    print(f"File logging enabled: {log_file}")


# Utility functions for logging contexts

def log_tool_call(
    logger: StructuredLogger,
    tool_name: str,
    params: Dict[str, Any],
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """
    Log MCP tool call with structured data.

    Args:
        logger: StructuredLogger instance
        tool_name: Name of the MCP tool
        params: Tool parameters
        success: Whether the call succeeded
        error: Error message if failed
    """
    log_data = {
        "tool": tool_name,
        "params": params,
        "success": success
    }

    if error:
        log_data["error"] = error

    if success:
        logger.info(f"Tool call: {tool_name}", **log_data)
    else:
        logger.error(f"Tool call failed: {tool_name}", **log_data)


def log_book_processing(
    logger: StructuredLogger,
    operation: str,
    book_path: str,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    """
    Log book processing operation with structured data.

    Args:
        logger: StructuredLogger instance
        operation: Operation name (e.g., "read", "extract_chapter")
        book_path: Path to the book
        success: Whether the operation succeeded
        metadata: Additional metadata (size, format, chunks, etc.)
        error: Error message if failed
    """
    log_data = {
        "operation": operation,
        "book_path": book_path,
        "success": success
    }

    if metadata:
        log_data["metadata"] = metadata

    if error:
        log_data["error"] = error

    if success:
        logger.info(f"Book processing: {operation}", **log_data)
    else:
        logger.error(f"Book processing failed: {operation}", **log_data)


# Example usage and testing
if __name__ == "__main__":
    # Setup file logging
    setup_file_logging()

    # Get logger
    logger = get_logger(__name__)

    # Test logging
    logger.info("Testing structured logging", test=True, value=123)
    logger.error("Testing error logging", error_type="TestError", details="This is a test")

    # Test operation decorator
    @log_operation("test_operation")
    async def test_async_function():
        import asyncio
        await asyncio.sleep(0.1)
        return "success"

    @log_operation("test_sync_operation")
    def test_sync_function():
        return "success"

    # Run tests
    import asyncio
    asyncio.run(test_async_function())
    test_sync_function()

    print("\nStructured logging test completed. Check logs/ directory.")
