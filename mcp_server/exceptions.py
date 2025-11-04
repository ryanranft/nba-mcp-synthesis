"""
Custom Exception Classes for NBA MCP Analytics.

This module defines custom exceptions for better error handling and user feedback.
All exceptions inherit from a base NBAAnalyticsError for easy catching.

Exception Hierarchy:
--------------------
NBAAnalyticsError (base)
├── DataError
│   ├── InsufficientDataError
│   ├── InvalidDataError
│   ├── MissingDataError
│   └── DataShapeError
├── ModelError
│   ├── ModelFitError
│   ├── ConvergenceError
│   ├── ValidationError
│   └── PredictionError
├── ConfigurationError
│   ├── InvalidParameterError
│   ├── MissingParameterError
│   └── IncompatibleParametersError
└── ComputationError
    ├── NumericalError
    ├── TimeoutError
    └── ResourceError

Author: Claude Code
Date: November 2025
"""

from typing import Any, Dict, Optional


class NBAAnalyticsError(Exception):
    """
    Base exception for all NBA analytics errors.

    All custom exceptions inherit from this class for easy catching.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize base exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        """String representation with details."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# ==============================================================================
# Data-Related Errors
# ==============================================================================


class DataError(NBAAnalyticsError):
    """Base class for data-related errors."""

    pass


class InsufficientDataError(DataError):
    """Raised when dataset doesn't have enough observations."""

    def __init__(
        self,
        message: str = "Insufficient data for analysis",
        required: Optional[int] = None,
        actual: Optional[int] = None,
        **kwargs,
    ):
        details = {}
        if required is not None:
            details["required"] = required
        if actual is not None:
            details["actual"] = actual
        details.update(kwargs)
        super().__init__(message, details=details)


class InvalidDataError(DataError):
    """Raised when data contains invalid values."""

    def __init__(
        self,
        message: str = "Invalid data detected",
        column: Optional[str] = None,
        invalid_count: Optional[int] = None,
        **kwargs,
    ):
        details = {}
        if column is not None:
            details["column"] = column
        if invalid_count is not None:
            details["invalid_count"] = invalid_count
        details.update(kwargs)
        super().__init__(message, details=details)


class MissingDataError(DataError):
    """Raised when required data is missing."""

    def __init__(
        self,
        message: str = "Missing required data",
        missing_columns: Optional[list] = None,
        missing_percentage: Optional[float] = None,
        **kwargs,
    ):
        details = {}
        if missing_columns is not None:
            details["missing_columns"] = missing_columns
        if missing_percentage is not None:
            details["missing_percentage"] = missing_percentage
        details.update(kwargs)
        super().__init__(message, details=details)


class DataShapeError(DataError):
    """Raised when data has incorrect shape or dimensions."""

    def __init__(
        self,
        message: str = "Incorrect data shape",
        expected_shape: Optional[tuple] = None,
        actual_shape: Optional[tuple] = None,
        **kwargs,
    ):
        details = {}
        if expected_shape is not None:
            details["expected_shape"] = expected_shape
        if actual_shape is not None:
            details["actual_shape"] = actual_shape
        details.update(kwargs)
        super().__init__(message, details=details)


# ==============================================================================
# Model-Related Errors
# ==============================================================================


class ModelError(NBAAnalyticsError):
    """Base class for model-related errors."""

    pass


class ModelFitError(ModelError):
    """Raised when model fitting fails."""

    def __init__(
        self,
        message: str = "Model fitting failed",
        model_type: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs,
    ):
        details = {}
        if model_type is not None:
            details["model_type"] = model_type
        if reason is not None:
            details["reason"] = reason
        details.update(kwargs)
        super().__init__(message, details=details)


class ConvergenceError(ModelError):
    """Raised when iterative algorithm doesn't converge."""

    def __init__(
        self,
        message: str = "Algorithm failed to converge",
        max_iter: Optional[int] = None,
        tolerance: Optional[float] = None,
        final_value: Optional[float] = None,
        **kwargs,
    ):
        details = {}
        if max_iter is not None:
            details["max_iter"] = max_iter
        if tolerance is not None:
            details["tolerance"] = tolerance
        if final_value is not None:
            details["final_value"] = final_value
        details.update(kwargs)
        super().__init__(message, details=details)


class ValidationError(ModelError):
    """Raised when model validation fails."""

    def __init__(
        self,
        message: str = "Model validation failed",
        validation_metric: Optional[str] = None,
        threshold: Optional[float] = None,
        actual_value: Optional[float] = None,
        **kwargs,
    ):
        details = {}
        if validation_metric is not None:
            details["validation_metric"] = validation_metric
        if threshold is not None:
            details["threshold"] = threshold
        if actual_value is not None:
            details["actual_value"] = actual_value
        details.update(kwargs)
        super().__init__(message, details=details)


class PredictionError(ModelError):
    """Raised when prediction/forecasting fails."""

    def __init__(
        self,
        message: str = "Prediction failed",
        n_steps: Optional[int] = None,
        reason: Optional[str] = None,
        **kwargs,
    ):
        details = {}
        if n_steps is not None:
            details["n_steps"] = n_steps
        if reason is not None:
            details["reason"] = reason
        details.update(kwargs)
        super().__init__(message, details=details)


# ==============================================================================
# Configuration-Related Errors
# ==============================================================================


class ConfigurationError(NBAAnalyticsError):
    """Base class for configuration-related errors."""

    pass


class InvalidParameterError(ConfigurationError):
    """Raised when parameter value is invalid."""

    def __init__(
        self,
        message: str = "Invalid parameter value",
        parameter: Optional[str] = None,
        value: Any = None,
        valid_values: Optional[list] = None,
        **kwargs,
    ):
        details = {}
        if parameter is not None:
            details["parameter"] = parameter
        if value is not None:
            details["value"] = value
        if valid_values is not None:
            details["valid_values"] = valid_values
        details.update(kwargs)
        super().__init__(message, details=details)


class MissingParameterError(ConfigurationError):
    """Raised when required parameter is missing."""

    def __init__(
        self,
        message: str = "Missing required parameter",
        parameter: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs,
    ):
        details = {}
        if parameter is not None:
            details["parameter"] = parameter
        if context is not None:
            details["context"] = context
        details.update(kwargs)
        super().__init__(message, details=details)


class IncompatibleParametersError(ConfigurationError):
    """Raised when parameter combination is invalid."""

    def __init__(
        self,
        message: str = "Incompatible parameter combination",
        parameters: Optional[list] = None,
        reason: Optional[str] = None,
        **kwargs,
    ):
        details = {}
        if parameters is not None:
            details["parameters"] = parameters
        if reason is not None:
            details["reason"] = reason
        details.update(kwargs)
        super().__init__(message, details=details)


# ==============================================================================
# Computation-Related Errors
# ==============================================================================


class ComputationError(NBAAnalyticsError):
    """Base class for computation-related errors."""

    pass


class NumericalError(ComputationError):
    """Raised when numerical computation fails (overflow, underflow, etc.)."""

    def __init__(
        self,
        message: str = "Numerical computation error",
        operation: Optional[str] = None,
        values: Optional[Dict[str, float]] = None,
        **kwargs,
    ):
        details = {}
        if operation is not None:
            details["operation"] = operation
        if values is not None:
            details["values"] = values
        details.update(kwargs)
        super().__init__(message, details=details)


class TimeoutError(ComputationError):
    """Raised when computation exceeds time limit."""

    def __init__(
        self,
        message: str = "Computation timed out",
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        details = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation is not None:
            details["operation"] = operation
        details.update(kwargs)
        super().__init__(message, details=details)


class ResourceError(ComputationError):
    """Raised when system resources are insufficient."""

    def __init__(
        self,
        message: str = "Insufficient system resources",
        resource_type: Optional[str] = None,
        required: Optional[float] = None,
        available: Optional[float] = None,
        **kwargs,
    ):
        details = {}
        if resource_type is not None:
            details["resource_type"] = resource_type
        if required is not None:
            details["required"] = required
        if available is not None:
            details["available"] = available
        details.update(kwargs)
        super().__init__(message, details=details)


# ==============================================================================
# Convenience Functions
# ==============================================================================


def validate_data_shape(
    data,
    min_rows: Optional[int] = None,
    min_cols: Optional[int] = None,
    expected_shape: Optional[tuple] = None,
) -> None:
    """
    Validate data shape and raise appropriate error if invalid.

    Args:
        data: Data to validate (DataFrame or array)
        min_rows: Minimum number of rows required
        min_cols: Minimum number of columns required
        expected_shape: Exact expected shape

    Raises:
        DataShapeError: If shape is invalid
        InsufficientDataError: If not enough rows
    """
    import numpy as np
    import pandas as pd

    # Get shape
    if isinstance(data, pd.DataFrame):
        actual_shape = data.shape
    elif isinstance(data, (np.ndarray, list)):
        actual_shape = np.array(data).shape
    else:
        raise InvalidDataError(f"Unsupported data type: {type(data)}")

    # Check minimum rows
    if min_rows is not None and actual_shape[0] < min_rows:
        raise InsufficientDataError(
            f"Need at least {min_rows} rows", required=min_rows, actual=actual_shape[0]
        )

    # Check minimum columns
    if min_cols is not None and len(actual_shape) > 1 and actual_shape[1] < min_cols:
        raise DataShapeError(
            f"Need at least {min_cols} columns",
            expected_shape=(actual_shape[0], min_cols),
            actual_shape=actual_shape,
        )

    # Check exact shape
    if expected_shape is not None and actual_shape != expected_shape:
        raise DataShapeError(
            f"Expected shape {expected_shape}, got {actual_shape}",
            expected_shape=expected_shape,
            actual_shape=actual_shape,
        )


def validate_parameter(
    param_name: str,
    value: Any,
    valid_values: Optional[list] = None,
    value_type: Optional[type] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> None:
    """
    Validate parameter value and raise appropriate error if invalid.

    Args:
        param_name: Name of parameter
        value: Parameter value to validate
        valid_values: List of valid values (for categorical params)
        value_type: Expected type
        min_value: Minimum value (for numeric params)
        max_value: Maximum value (for numeric params)

    Raises:
        InvalidParameterError: If parameter is invalid
    """
    # Check type
    if value_type is not None and not isinstance(value, value_type):
        raise InvalidParameterError(
            f"Parameter '{param_name}' must be {value_type.__name__}",
            parameter=param_name,
            value=value,
        )

    # Check valid values
    if valid_values is not None and value not in valid_values:
        raise InvalidParameterError(
            f"Parameter '{param_name}' must be one of {valid_values}",
            parameter=param_name,
            value=value,
            valid_values=valid_values,
        )

    # Check range
    if min_value is not None and value < min_value:
        raise InvalidParameterError(
            f"Parameter '{param_name}' must be >= {min_value}",
            parameter=param_name,
            value=value,
        )

    if max_value is not None and value > max_value:
        raise InvalidParameterError(
            f"Parameter '{param_name}' must be <= {max_value}",
            parameter=param_name,
            value=value,
        )


__all__ = [
    # Base
    "NBAAnalyticsError",
    # Data errors
    "DataError",
    "InsufficientDataError",
    "InvalidDataError",
    "MissingDataError",
    "DataShapeError",
    # Model errors
    "ModelError",
    "ModelFitError",
    "ConvergenceError",
    "ValidationError",
    "PredictionError",
    # Configuration errors
    "ConfigurationError",
    "InvalidParameterError",
    "MissingParameterError",
    "IncompatibleParametersError",
    # Computation errors
    "ComputationError",
    "NumericalError",
    "TimeoutError",
    "ResourceError",
    # Utilities
    "validate_data_shape",
    "validate_parameter",
]
