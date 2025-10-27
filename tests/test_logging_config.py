"""
Comprehensive tests for logging configuration module.

Tests all logging functionality including:
- JSON formatter
- Colored formatter
- Performance logger
- Request context
- Log rotation
- Multiple handlers
- Contextual logging

Author: NBA MCP Server Team
Date: 2025-01-18
"""

import json
import logging
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mcp_server.logging_config import (
    # Formatters
    JSONFormatter,
    ColoredFormatter,
    # Performance logging
    PerformanceLogger,
    PerformanceMeasurement,
    # Request context
    RequestContext,
    request_id_var,
    client_id_var,
    # Setup and helpers
    setup_logging,
    get_logger,
    log_request,
    log_performance,
    log_error,
)


# ==============================================================================
# Test JSON Formatter
# ==============================================================================


class TestJSONFormatter:
    """Test JSON formatter for structured logging."""

    def test_json_formatter_basic_message(self):
        """Test JSON formatter with basic log message."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test"
        assert log_data["module"] == "test"
        assert log_data["line"] == 10
        assert "timestamp" in log_data

    def test_json_formatter_with_request_context(self):
        """Test JSON formatter includes request context."""
        formatter = JSONFormatter()

        # Set request context
        request_id_var.set("req_123")
        client_id_var.set("client_456")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["request_id"] == "req_123"
        assert log_data["client_id"] == "client_456"

        # Clean up
        request_id_var.set(None)
        client_id_var.set(None)

    def test_json_formatter_with_exception(self):
        """Test JSON formatter with exception information."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test error"
        assert "traceback" in log_data["exception"]

    def test_json_formatter_with_extra_fields(self):
        """Test JSON formatter includes extra fields."""
        formatter = JSONFormatter(include_extra=True)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.operation = "query_database"
        record.duration_ms = 150.5
        record.custom_field = "custom_value"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["operation"] == "query_database"
        assert log_data["duration_ms"] == 150.5
        assert log_data["custom_field"] == "custom_value"

    def test_json_formatter_without_extra_fields(self):
        """Test JSON formatter without extra fields."""
        formatter = JSONFormatter(include_extra=False)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        record.custom_field = "should_not_appear"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert "custom_field" not in log_data


# ==============================================================================
# Test Colored Formatter
# ==============================================================================


class TestColoredFormatter:
    """Test colored formatter for console output."""

    def test_colored_formatter_basic_message(self):
        """Test colored formatter with basic message."""
        formatter = ColoredFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = time.time()

        formatted = formatter.format(record)

        assert "Test message" in formatted
        assert "test" in formatted  # Logger name
        # Should contain ANSI color codes
        assert "\033[" in formatted

    def test_colored_formatter_with_request_id(self):
        """Test colored formatter includes request ID."""
        formatter = ColoredFormatter()

        request_id_var.set("req_789")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = time.time()

        formatted = formatter.format(record)

        assert "req_789" in formatted

        # Clean up
        request_id_var.set(None)

    def test_colored_formatter_different_levels(self):
        """Test colored formatter with different log levels."""
        formatter = ColoredFormatter()

        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level, level_name in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=10,
                msg=f"{level_name} message",
                args=(),
                exc_info=None,
            )
            record.created = time.time()

            formatted = formatter.format(record)

            assert level_name in formatted
            assert "\033[" in formatted  # Contains color codes

    def test_colored_formatter_with_exception(self):
        """Test colored formatter with exception."""
        formatter = ColoredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.created = time.time()

        formatted = formatter.format(record)

        assert "Error occurred" in formatted
        assert "Traceback" in formatted or "ValueError" in formatted


# ==============================================================================
# Test Performance Logger
# ==============================================================================


class TestPerformanceLogger:
    """Test performance logging functionality."""

    def test_performance_logger_start_end(self):
        """Test performance logger start/end methods."""
        logger = logging.getLogger("test_perf")
        perf_logger = PerformanceLogger(logger)

        with patch.object(logger, "debug") as mock_debug, patch.object(
            logger, "info"
        ) as mock_info:

            perf_logger.start("test_operation")
            time.sleep(0.1)
            perf_logger.end("test_operation")

            # Check that debug and info were called
            mock_debug.assert_called_once()
            mock_info.assert_called_once()

            # Check info call had duration
            call_args = mock_info.call_args
            assert "extra" in call_args[1]
            assert "duration_ms" in call_args[1]["extra"]
            assert call_args[1]["extra"]["duration_ms"] >= 100

    def test_performance_logger_without_start(self):
        """Test performance logger end without start logs warning."""
        logger = logging.getLogger("test_perf")
        perf_logger = PerformanceLogger(logger)

        with patch.object(logger, "warning") as mock_warning:
            perf_logger.end("test_operation")

            # Should log warning
            mock_warning.assert_called_once()

    def test_performance_logger_with_extra_fields(self):
        """Test performance logger with extra fields."""
        logger = logging.getLogger("test_perf")
        perf_logger = PerformanceLogger(logger)

        with patch.object(logger, "debug"), patch.object(logger, "info") as mock_info:

            perf_logger.start("test_operation")
            time.sleep(0.05)
            perf_logger.end("test_operation", query="SELECT *", rows=100)

            # Check extra fields were included
            call_args = mock_info.call_args
            assert call_args[1]["extra"]["query"] == "SELECT *"
            assert call_args[1]["extra"]["rows"] == 100

    def test_performance_measurement_context_manager(self):
        """Test PerformanceMeasurement context manager."""
        logger = logging.getLogger("test_perf")

        with patch.object(logger, "debug") as mock_debug, patch.object(
            logger, "info"
        ) as mock_info:

            with PerformanceMeasurement(logger, "test_operation"):
                time.sleep(0.05)

            # Should log start and completion
            mock_debug.assert_called_once()
            mock_info.assert_called_once()

            # Check completion had duration and success
            call_args = mock_info.call_args
            assert "extra" in call_args[1]
            assert call_args[1]["extra"]["success"] is True
            assert "duration_ms" in call_args[1]["extra"]

    def test_performance_measurement_with_exception(self):
        """Test PerformanceMeasurement with exception."""
        logger = logging.getLogger("test_perf")

        with patch.object(logger, "debug"), patch.object(logger, "error") as mock_error:

            try:
                with PerformanceMeasurement(logger, "test_operation"):
                    raise ValueError("Test error")
            except ValueError:
                pass

            # Should log error with performance data
            mock_error.assert_called_once()

            call_args = mock_error.call_args
            assert call_args[1]["extra"]["success"] is False
            assert "duration_ms" in call_args[1]["extra"]
            assert "error" in call_args[1]["extra"]

    def test_performance_logger_measure_method(self):
        """Test PerformanceLogger.measure() context manager."""
        logger = logging.getLogger("test_perf")
        perf_logger = PerformanceLogger(logger)

        with patch.object(logger, "debug"), patch.object(logger, "info") as mock_info:

            with perf_logger.measure("test_operation"):
                time.sleep(0.05)

            mock_info.assert_called_once()


# ==============================================================================
# Test Request Context
# ==============================================================================


class TestRequestContext:
    """Test request context tracking."""

    def test_request_context_basic(self):
        """Test basic request context."""
        logger = logging.getLogger("test_context")

        with patch.object(logger, "info") as mock_info:
            with RequestContext(logger, "test_operation"):
                pass

            # Should log start and completion
            assert mock_info.call_count == 2

            # Check first call (start)
            start_call = mock_info.call_args_list[0]
            assert "Request started" in start_call[0][0]
            assert start_call[1]["extra"]["phase"] == "start"

            # Check second call (complete)
            complete_call = mock_info.call_args_list[1]
            assert "Request completed" in complete_call[0][0]
            assert complete_call[1]["extra"]["phase"] == "complete"
            assert complete_call[1]["extra"]["success"] is True

    def test_request_context_with_client_id(self):
        """Test request context with client ID."""
        logger = logging.getLogger("test_context")

        with patch.object(logger, "info") as mock_info:
            with RequestContext(logger, "test_operation", client_id="client_123"):
                pass

            # Check that client_id is included
            start_call = mock_info.call_args_list[0]
            assert start_call[1]["extra"]["client_id"] == "client_123"

    def test_request_context_with_custom_request_id(self):
        """Test request context with custom request ID."""
        logger = logging.getLogger("test_context")

        with patch.object(logger, "info") as mock_info:
            with RequestContext(logger, "test_operation", request_id="custom_req_id"):
                pass

            # Check that custom request_id is used
            start_call = mock_info.call_args_list[0]
            assert start_call[1]["extra"]["request_id"] == "custom_req_id"

    def test_request_context_with_exception(self):
        """Test request context with exception."""
        logger = logging.getLogger("test_context")

        with patch.object(logger, "info"), patch.object(logger, "error") as mock_error:

            try:
                with RequestContext(logger, "test_operation"):
                    raise ValueError("Test error")
            except ValueError:
                pass

            # Should log error
            mock_error.assert_called_once()

            call_args = mock_error.call_args
            assert "Request failed" in call_args[0][0]
            assert call_args[1]["extra"]["phase"] == "error"
            assert call_args[1]["extra"]["success"] is False
            assert call_args[1]["extra"]["error_type"] == "ValueError"

    def test_request_context_sets_context_vars(self):
        """Test that request context sets context variables."""
        logger = logging.getLogger("test_context")

        with RequestContext(
            logger, "test_operation", client_id="client_123", request_id="req_456"
        ):
            # Context vars should be set inside context
            assert request_id_var.get() == "req_456"
            assert client_id_var.get() == "client_123"

        # Context vars should be cleared after context
        assert request_id_var.get() is None
        assert client_id_var.get() is None

    def test_request_context_duration_tracking(self):
        """Test that request context tracks duration."""
        logger = logging.getLogger("test_context")

        with patch.object(logger, "info") as mock_info:
            with RequestContext(logger, "test_operation"):
                time.sleep(0.1)

            # Check completion call has duration
            complete_call = mock_info.call_args_list[1]
            assert "duration_ms" in complete_call[1]["extra"]
            assert complete_call[1]["extra"]["duration_ms"] >= 100


# ==============================================================================
# Test Logging Setup
# ==============================================================================


class TestLoggingSetup:
    """Test logging configuration setup."""

    def test_setup_logging_creates_log_dir(self):
        """Test that setup_logging creates log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            setup_logging(log_dir=str(log_dir), enable_file=True)

            assert log_dir.exists()
            assert log_dir.is_dir()

    def test_setup_logging_creates_log_files(self):
        """Test that setup_logging creates log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            setup_logging(log_dir=str(log_dir), enable_file=True)

            # Log a message to trigger file creation
            logger = get_logger("test")
            logger.info("Test message")

            # Check that log files were created
            assert (log_dir / "application.log").exists()

    def test_setup_logging_console_only(self):
        """Test setup_logging with console only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            root_logger = setup_logging(
                log_dir=str(log_dir), enable_console=True, enable_file=False
            )

            # Should have console handler
            console_handlers = [
                h
                for h in root_logger.handlers
                if isinstance(h, logging.StreamHandler)
                and not hasattr(h, "baseFilename")
            ]
            assert len(console_handlers) > 0

    def test_setup_logging_file_only(self):
        """Test setup_logging with file only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            root_logger = setup_logging(
                log_dir=str(log_dir), enable_console=False, enable_file=True
            )

            # Should have file handlers
            file_handlers = [
                h for h in root_logger.handlers if hasattr(h, "baseFilename")
            ]
            assert len(file_handlers) > 0

    def test_setup_logging_json_formatting(self):
        """Test setup_logging with JSON formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            setup_logging(log_dir=str(log_dir), enable_json=True, enable_console=True)

            root_logger = logging.getLogger()

            # Check that at least one handler uses JSON formatter
            json_formatters = [
                h.formatter
                for h in root_logger.handlers
                if isinstance(h.formatter, JSONFormatter)
            ]
            assert len(json_formatters) > 0

    def test_setup_logging_colored_formatting(self):
        """Test setup_logging with colored formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            setup_logging(log_dir=str(log_dir), enable_json=False, enable_console=True)

            root_logger = logging.getLogger()

            # Check that at least one handler uses colored formatter
            colored_formatters = [
                h.formatter
                for h in root_logger.handlers
                if isinstance(h.formatter, ColoredFormatter)
            ]
            assert len(colored_formatters) > 0

    def test_setup_logging_log_levels(self):
        """Test setup_logging with different log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            with tempfile.TemporaryDirectory() as tmpdir:
                log_dir = Path(tmpdir) / "logs"

                root_logger = setup_logging(log_level=level, log_dir=str(log_dir))

                assert root_logger.level == getattr(logging, level)


# ==============================================================================
# Test Helper Functions
# ==============================================================================


class TestHelperFunctions:
    """Test logging helper functions."""

    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test_logger")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_log_request(self):
        """Test log_request helper function."""
        logger = get_logger("test")

        with patch.object(logger, "info") as mock_info:
            log_request(logger, "test_operation", user_id="user_123")

            mock_info.assert_called_once()
            call_args = mock_info.call_args

            assert "test_operation" in call_args[0][0]
            assert call_args[1]["extra"]["operation"] == "test_operation"
            assert call_args[1]["extra"]["user_id"] == "user_123"

    def test_log_performance(self):
        """Test log_performance helper function."""
        logger = get_logger("test")

        with patch.object(logger, "info") as mock_info:
            log_performance(
                logger, "query_operation", duration_ms=150.5, query="SELECT *"
            )

            mock_info.assert_called_once()
            call_args = mock_info.call_args

            assert call_args[1]["extra"]["operation"] == "query_operation"
            assert call_args[1]["extra"]["duration_ms"] == 150.5
            assert call_args[1]["extra"]["query"] == "SELECT *"
            assert call_args[1]["extra"]["performance_metric"] is True

    def test_log_error(self):
        """Test log_error helper function."""
        logger = get_logger("test")
        error = ValueError("Test error")

        with patch.object(logger, "error") as mock_error:
            log_error(logger, "test_operation", error, user_id="user_123")

            mock_error.assert_called_once()
            call_args = mock_error.call_args

            assert call_args[1]["extra"]["operation"] == "test_operation"
            assert call_args[1]["extra"]["error_type"] == "ValueError"
            assert call_args[1]["extra"]["error_message"] == "Test error"
            assert call_args[1]["extra"]["user_id"] == "user_123"
            assert call_args[1]["exc_info"] is True


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_full_logging_flow(self):
        """Test complete logging flow with all components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            # Setup logging
            setup_logging(
                log_level="DEBUG",
                log_dir=str(log_dir),
                enable_json=True,
                enable_console=False,
                enable_file=True,
            )

            logger = get_logger("integration_test")

            # Use request context
            with RequestContext(logger, "test_operation", client_id="client_123"):
                # Log some messages
                logger.info("Processing started")

                # Use performance logger
                perf = PerformanceLogger(logger)
                with perf.measure("database_query"):
                    time.sleep(0.05)
                    logger.debug("Query executed")

                # Log error
                try:
                    raise ValueError("Test error")
                except ValueError as e:
                    log_error(logger, "test_operation", e)

            # Check that logs were written
            app_log = log_dir / "application.log"
            assert app_log.exists()

            # Read and parse logs
            with open(app_log, "r") as f:
                logs = [json.loads(line) for line in f if line.strip()]

            # Verify logs
            assert len(logs) > 0

            # Check that some logs have request_id
            logs_with_request_id = [log for log in logs if "request_id" in log]
            assert len(logs_with_request_id) > 0

            # Check that performance logs have duration
            perf_logs = [log for log in logs if "duration_ms" in log]
            assert len(perf_logs) > 0

    def test_error_log_separation(self):
        """Test that errors are logged to separate file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            setup_logging(
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True,
            )

            logger = get_logger("test")

            # Log info and error
            logger.info("Info message")
            logger.error("Error message")

            # Check both log files
            app_log = log_dir / "application.log"
            error_log = log_dir / "errors.log"

            assert app_log.exists()
            assert error_log.exists()

            # Application log should have both
            with open(app_log, "r") as f:
                app_logs = [json.loads(line) for line in f if line.strip()]

            assert len(app_logs) >= 2

            # Error log should only have errors
            with open(error_log, "r") as f:
                error_logs = [json.loads(line) for line in f if line.strip()]

            assert len(error_logs) >= 1
            assert all(log["level"] == "ERROR" for log in error_logs)

    def test_performance_log_filtering(self):
        """Test that performance logs are filtered correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            setup_logging(
                log_dir=str(log_dir),
                enable_console=False,
                enable_file=True,
            )

            logger = get_logger("test")

            # Log regular message
            logger.info("Regular message")

            # Log performance metric
            log_performance(logger, "test_op", duration_ms=100.0)

            # Check performance log
            perf_log = log_dir / "performance.log"
            assert perf_log.exists()

            with open(perf_log, "r") as f:
                perf_logs = [json.loads(line) for line in f if line.strip()]

            # Should only have performance logs
            assert all("duration_ms" in log for log in perf_logs)


# ==============================================================================
# Performance Tests
# ==============================================================================


class TestLoggingPerformance:
    """Test logging performance."""

    def test_json_formatter_performance(self):
        """Test JSON formatter performance."""
        formatter = JSONFormatter()

        records = []
        for i in range(100):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=i,
                msg=f"Message {i}",
                args=(),
                exc_info=None,
            )
            records.append(record)

        start_time = time.time()
        for record in records:
            formatter.format(record)
        elapsed = time.time() - start_time

        # Should format 100 records in under 0.1 seconds
        assert elapsed < 0.1

    def test_performance_logger_overhead(self):
        """Test performance logger overhead."""
        logger = get_logger("test_perf")
        logger.setLevel(logging.CRITICAL)  # Disable actual logging

        start_time = time.time()
        for _ in range(100):
            perf = PerformanceLogger(logger)
            with perf.measure("test_op"):
                pass
        elapsed = time.time() - start_time

        # Should have minimal overhead
        assert elapsed < 0.5

    def test_request_context_overhead(self):
        """Test request context overhead."""
        logger = get_logger("test_context")
        logger.setLevel(logging.CRITICAL)  # Disable actual logging

        start_time = time.time()
        for _ in range(100):
            with RequestContext(logger, "test_op"):
                pass
        elapsed = time.time() - start_time

        # Should have minimal overhead
        assert elapsed < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
