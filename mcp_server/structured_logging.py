"""Structured Logging - IMPORTANT 16"""

import logging
import json
from typing import Dict, Any
from datetime import datetime
import sys


class StructuredLogger:
    """Structured JSON logger for better log analysis"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_json_handler()

    def _setup_json_handler(self):
        """Setup JSON formatter"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, level: str, message: str, **kwargs):
        """Log structured message"""
        log_func = getattr(self.logger, level.lower())
        log_func(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log("info", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log("error", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.log("critical", message, **kwargs)


class JSONFormatter(logging.Formatter):
    """Format logs as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "__dict__"):
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
                ]:
                    log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# Global logger instance
_structured_logger = None


def get_logger(name: str = "nba_mcp") -> StructuredLogger:
    """Get structured logger instance"""
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger(name)
    return _structured_logger


# Example usage
if __name__ == "__main__":
    logger = get_logger()
    logger.info("System started", user_id="user123", action="login")
    logger.error("Database connection failed", service="rds", error_code=500)
