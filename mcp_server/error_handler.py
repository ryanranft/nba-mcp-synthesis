"""Centralized error handling"""

import logging
import traceback
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error categories for classification"""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    RATE_LIMIT = "rate_limit"
    NOT_FOUND = "not_found"
    INTERNAL = "internal"
    CONFIGURATION = "configuration"


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NBAMCPError(Exception):
    """Base exception for NBA MCP"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/API response"""
        return {
            "error": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "timestamp": self.timestamp,
        }


# Specific error types
class ValidationError(NBAMCPError):
    """Validation error"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.LOW, details)


class AuthenticationError(NBAMCPError):
    """Authentication error"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, details
        )


class AuthorizationError(NBAMCPError):
    """Authorization error"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message, ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH, details
        )


class DatabaseError(NBAMCPError):
    """Database error"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.DATABASE, ErrorSeverity.HIGH, details)


class RateLimitError(NBAMCPError):
    """Rate limit exceeded"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message, ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM, details
        )


class NotFoundError(NBAMCPError):
    """Resource not found"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.NOT_FOUND, ErrorSeverity.LOW, details)


class ErrorHandler:
    """Centralized error handler"""

    def __init__(self):
        self.error_count = 0
        self.errors_by_category = {}

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an error

        Args:
            error: Exception that occurred
            context: Additional context

        Returns:
            Error response dictionary
        """
        self.error_count += 1

        # Convert to NBAMCPError if not already
        if isinstance(error, NBAMCPError):
            mcp_error = error
        else:
            # Wrap unknown errors
            mcp_error = NBAMCPError(
                message=str(error),
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.HIGH,
                details={"original_type": type(error).__name__},
            )

        # Track by category
        category = mcp_error.category.value
        self.errors_by_category[category] = self.errors_by_category.get(category, 0) + 1

        # Log error
        log_message = f"Error [{mcp_error.category.value}]: {mcp_error.message}"
        if context:
            log_message += f" | Context: {context}"

        if mcp_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(log_message)
            logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            logger.warning(log_message)

        # Return error response
        response = mcp_error.to_dict()
        if context:
            response["context"] = context

        return response

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": self.error_count,
            "errors_by_category": self.errors_by_category,
        }


# Global error handler
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_errors(func):
    """Decorator to automatically handle errors"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handler = get_error_handler()
            return handler.handle_error(e, context={"function": func.__name__})

    return wrapper
