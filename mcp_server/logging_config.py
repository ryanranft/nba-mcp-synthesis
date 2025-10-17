#!/usr/bin/env python3
"""
Structured Logging Configuration - Production Hardening
Implements JSON structured logging, request ID tracking, performance metrics,
and centralized log management for production systems.
"""

import logging
import json
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Context variable for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
client_id_var: ContextVar[Optional[str]] = ContextVar("client_id", default=None)


# ==============================================================================
# JSON Formatter
# ==============================================================================


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON
    Includes request ID, timestamps, and structured fields
    """

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: LogRecord to format

        Returns:
            JSON string
        """
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        client_id = client_id_var.get()
        if client_id:
            log_data["client_id"] = client_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields
        if self.include_extra:
            # Add any extra fields passed to the logger
            for key, value in record.__dict__.items():
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "getMessage",
                    "taskName",
                ]:
                    try:
                        # Only include JSON-serializable values
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)

        return json.dumps(log_data)


# ==============================================================================
# Human-Readable Formatter (for development)
# ==============================================================================


class ColoredFormatter(logging.Formatter):
    """
    Formatter with color coding for console output
    Useful for development/debugging
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors"""
        # Color the level name
        level_color = self.COLORS.get(record.levelname, "")
        colored_level = f"{level_color}{record.levelname:8}{self.RESET}"

        # Build formatted message
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        # Add request ID if available
        request_id = request_id_var.get()
        request_str = f" [{request_id[:8]}]" if request_id else ""

        message = (
            f"{timestamp} {colored_level} "
            f"{self.BOLD}{record.name}{self.RESET}{request_str}: "
            f"{record.getMessage()}"
        )

        # Add exception if present
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        return message


# ==============================================================================
# Performance Metrics Logger
# ==============================================================================


class PerformanceLogger:
    """
    Helper class for logging performance metrics
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_time: Optional[float] = None

    def start(self, operation: str):
        """Start timing an operation"""
        self.start_time = time.time()
        self.logger.debug(f"Started: {operation}")

    def end(self, operation: str, **extra_fields):
        """End timing and log performance"""
        if self.start_time is None:
            self.logger.warning(f"Performance timer not started for: {operation}")
            return

        duration = time.time() - self.start_time
        self.logger.info(
            f"Completed: {operation}",
            extra={
                "operation": operation,
                "duration_ms": round(duration * 1000, 2),
                "duration_seconds": round(duration, 3),
                **extra_fields,
            },
        )
        self.start_time = None

    def measure(self, operation: str):
        """Context manager for measuring performance"""
        return PerformanceMeasurement(self.logger, operation)


class PerformanceMeasurement:
    """Context manager for performance measurement"""

    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Started: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type is not None:
            # Log error with performance data
            self.logger.error(
                f"Failed: {self.operation}",
                extra={
                    "operation": self.operation,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(exc_val),
                    "success": False,
                },
                exc_info=(exc_type, exc_val, exc_tb),
            )
        else:
            # Log success with performance data
            self.logger.info(
                f"Completed: {self.operation}",
                extra={
                    "operation": self.operation,
                    "duration_ms": round(duration * 1000, 2),
                    "success": True,
                },
            )


# ==============================================================================
# Request Context Manager
# ==============================================================================


class RequestContext:
    """
    Context manager for request tracking
    Automatically assigns request ID and tracks request lifecycle
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        client_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.logger = logger
        self.operation = operation
        self.client_id = client_id
        self.request_id = request_id or str(uuid.uuid4())
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Enter request context"""
        # Set context variables
        request_id_var.set(self.request_id)
        if self.client_id:
            client_id_var.set(self.client_id)

        self.start_time = time.time()

        self.logger.info(
            f"Request started: {self.operation}",
            extra={
                "operation": self.operation,
                "request_id": self.request_id,
                "client_id": self.client_id,
                "phase": "start",
            },
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit request context"""
        duration = time.time() - self.start_time

        if exc_type is not None:
            self.logger.error(
                f"Request failed: {self.operation}",
                extra={
                    "operation": self.operation,
                    "request_id": self.request_id,
                    "client_id": self.client_id,
                    "phase": "error",
                    "duration_ms": round(duration * 1000, 2),
                    "error_type": exc_type.__name__,
                    "error_message": str(exc_val),
                    "success": False,
                },
                exc_info=(exc_type, exc_val, exc_tb),
            )
        else:
            self.logger.info(
                f"Request completed: {self.operation}",
                extra={
                    "operation": self.operation,
                    "request_id": self.request_id,
                    "client_id": self.client_id,
                    "phase": "complete",
                    "duration_ms": round(duration * 1000, 2),
                    "success": True,
                },
            )

        # Clear context variables
        request_id_var.set(None)
        client_id_var.set(None)


# ==============================================================================
# Logging Configuration
# ==============================================================================


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    enable_json: bool = True,
    enable_console: bool = True,
    enable_file: bool = True,
    max_file_size_mb: int = 100,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Setup structured logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (None = logs/)
        enable_json: Enable JSON structured logging
        enable_console: Enable console output
        enable_file: Enable file logging
        max_file_size_mb: Max size of each log file
        backup_count: Number of backup log files to keep

    Returns:
        Configured root logger
    """
    # Create log directory
    if log_dir is None:
        log_dir = Path("logs")
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (colored, human-readable)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        if enable_json:
            console_handler.setFormatter(JSONFormatter(include_extra=True))
        else:
            console_handler.setFormatter(ColoredFormatter())

        root_logger.addHandler(console_handler)

    # File handler (JSON structured)
    if enable_file:
        # Main application log (JSON)
        app_log_file = log_dir / "application.log"
        app_handler = RotatingFileHandler(
            app_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
        )
        app_handler.setLevel(logging.DEBUG)  # Log everything to file
        app_handler.setFormatter(JSONFormatter(include_extra=True))
        root_logger.addHandler(app_handler)

        # Error log (separate file for errors)
        error_log_file = log_dir / "errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter(include_extra=True))
        root_logger.addHandler(error_handler)

        # Performance log (for performance metrics)
        perf_log_file = log_dir / "performance.log"
        perf_handler = RotatingFileHandler(
            perf_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.addFilter(lambda record: hasattr(record, "duration_ms"))
        perf_handler.setFormatter(JSONFormatter(include_extra=True))
        root_logger.addHandler(perf_handler)

        # Access log (for request tracking)
        access_log_file = log_dir / "access.log"
        access_handler = RotatingFileHandler(
            access_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
        )
        access_handler.setLevel(logging.INFO)
        access_handler.addFilter(lambda record: hasattr(record, "request_id"))
        access_handler.setFormatter(JSONFormatter(include_extra=True))
        root_logger.addHandler(access_handler)

    # Log startup message
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_dir": str(log_dir),
            "json_enabled": enable_json,
            "console_enabled": enable_console,
            "file_enabled": enable_file,
        },
    )

    return root_logger


# ==============================================================================
# Helper Functions
# ==============================================================================


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_request(logger: logging.Logger, operation: str, **kwargs):
    """
    Log a request with structured data

    Args:
        logger: Logger instance
        operation: Operation name
        **kwargs: Additional fields to log
    """
    logger.info(f"Request: {operation}", extra={"operation": operation, **kwargs})


def log_performance(
    logger: logging.Logger, operation: str, duration_ms: float, **kwargs
):
    """
    Log performance metrics

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        **kwargs: Additional fields to log
    """
    logger.info(
        f"Performance: {operation}",
        extra={
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "performance_metric": True,
            **kwargs,
        },
    )


def log_error(logger: logging.Logger, operation: str, error: Exception, **kwargs):
    """
    Log an error with structured data

    Args:
        logger: Logger instance
        operation: Operation name
        error: Exception that occurred
        **kwargs: Additional fields to log
    """
    logger.error(
        f"Error: {operation}",
        extra={
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs,
        },
        exc_info=True,
    )


# ==============================================================================
# Example Usage
# ==============================================================================


def example_usage():
    """Example of using structured logging"""

    # Setup logging
    setup_logging(
        log_level="DEBUG",
        enable_json=False,  # Use colored output for console
        enable_file=True,
    )

    # Get logger
    logger = get_logger(__name__)

    # Example 1: Simple logging
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("Warning message")

    # Example 2: Request context
    with RequestContext(logger, "process_query", client_id="client_123"):
        logger.info("Processing query", extra={"query": "SELECT * FROM games"})
        time.sleep(0.1)  # Simulate work

    # Example 3: Performance measurement
    perf = PerformanceLogger(logger)
    with perf.measure("database_query"):
        time.sleep(0.2)  # Simulate query

    # Example 4: Error logging
    try:
        raise ValueError("Example error")
    except Exception as e:
        log_error(logger, "example_operation", e, user_id="user_456")

    print("\n✅ Structured logging examples completed")
    print("📝 Check logs/ directory for output files")


if __name__ == "__main__":
    example_usage()
