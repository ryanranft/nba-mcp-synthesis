"""
Time Series Analysis Tools
Tools for analyzing trends, patterns, and changes over time

Pure Python implementation - no external dependencies
"""

from typing import List, Union, Dict, Any, Optional
import math

from mcp_server.exceptions import ValidationError
from mcp_server.tools.logger_config import log_operation


# =============================================================================
# Moving Averages
# =============================================================================


@log_operation("stats_moving_average")
def calculate_moving_average(
    data: List[Union[int, float]], window: int = 3
) -> List[Optional[float]]:
    """
    Calculate simple moving average (SMA).

    Smooths time series data by averaging values in a sliding window.

    Args:
        data: Time series data
        window: Window size (default: 3)

    Returns:
        List of smoothed values (first window-1 values are None)

    Example:
        >>> data = [10, 12, 14, 16, 18, 20]
        >>> calculate_moving_average(data, window=3)
        [None, None, 12.0, 14.0, 16.0, 18.0]
    """
    if not data:
        raise ValidationError("Data cannot be empty", "data", None)

    if window < 1:
        raise ValidationError("Window size must be at least 1", "window", window)

    if window > len(data):
        raise ValidationError(
            f"Window ({window}) cannot be larger than data length ({len(data)})",
            "window",
            window,
        )

    result = []

    for i in range(len(data)):
        if i < window - 1:
            # Not enough data points yet
            result.append(None)
        else:
            # Calculate average of window
            window_data = data[i - window + 1 : i + 1]
            avg = sum(window_data) / window
            result.append(round(avg, 2))

    return result


@log_operation("stats_exponential_moving_average")
def calculate_exponential_moving_average(
    data: List[Union[int, float]], alpha: float = 0.3
) -> List[float]:
    """
    Calculate exponential moving average (EMA).

    Gives more weight to recent observations.

    Formula: EMA[t] = α × data[t] + (1-α) × EMA[t-1]

    Args:
        data: Time series data
        alpha: Smoothing factor (0-1, default: 0.3)
               Higher alpha = more weight to recent values

    Returns:
        List of EMA values

    Example:
        >>> data = [10, 12, 14, 16, 18]
        >>> calculate_exponential_moving_average(data, alpha=0.3)
        [10.0, 10.6, 11.62, 12.93, 14.45]
    """
    if not data:
        raise ValidationError("Data cannot be empty", "data", None)

    if not 0 < alpha <= 1:
        raise ValidationError(
            "Alpha must be between 0 and 1 (exclusive of 0)", "alpha", alpha
        )

    result = []
    ema = data[0]  # Initialize with first value

    for value in data:
        ema = alpha * value + (1 - alpha) * ema
        result.append(round(ema, 2))

    return result


# =============================================================================
# Trend Analysis
# =============================================================================


@log_operation("stats_trend_detection")
def detect_trend(data: List[Union[int, float]]) -> Dict[str, Any]:
    """
    Detect if data is trending up, down, or stable.

    Uses linear regression to find trend direction and strength.

    Args:
        data: Time series data

    Returns:
        Dictionary with:
        - trend: "increasing", "decreasing", or "stable"
        - slope: Trend slope (positive = increasing)
        - confidence: R² value (0-1, how well data fits trend)

    Example:
        >>> data = [10, 12, 15, 17, 20]
        >>> detect_trend(data)
        {
            "trend": "increasing",
            "slope": 2.5,
            "confidence": 0.99
        }
    """
    if not data:
        raise ValidationError("Data cannot be empty", "data", None)

    if len(data) < 2:
        return {"trend": "stable", "slope": 0.0, "confidence": 0.0}

    # Use time index as x-axis
    x = list(range(len(data)))
    y = data

    # Calculate regression slope
    n = len(data)
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

    if denominator == 0:
        slope = 0.0
    else:
        slope = numerator / denominator

    # Calculate R²
    intercept = mean_y - slope * mean_x
    y_pred = [slope * x[i] + intercept for i in range(n)]

    ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
    ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))

    if ss_tot == 0:
        r_squared = 1.0 if ss_res == 0 else 0.0
    else:
        r_squared = 1 - (ss_res / ss_tot)
        r_squared = max(0.0, min(1.0, r_squared))

    # Determine trend direction
    # Use threshold to avoid calling tiny slopes a trend
    threshold = 0.01 * (max(y) - min(y)) if max(y) != min(y) else 0.01

    if slope > threshold:
        trend = "increasing"
    elif slope < -threshold:
        trend = "decreasing"
    else:
        trend = "stable"

    return {"trend": trend, "slope": round(slope, 4), "confidence": round(r_squared, 4)}


@log_operation("stats_percent_change")
def calculate_percent_change(
    current: Union[int, float], previous: Union[int, float]
) -> float:
    """
    Calculate percentage change from previous to current value.

    Formula: ((current - previous) / previous) × 100

    Args:
        current: Current value
        previous: Previous value

    Returns:
        Percentage change (positive = increase, negative = decrease)

    Raises:
        ValidationError: If previous value is zero

    Example:
        >>> calculate_percent_change(120, 100)
        20.0  # 20% increase

        >>> calculate_percent_change(80, 100)
        -20.0  # 20% decrease
    """
    if previous == 0:
        raise ValidationError(
            "Previous value cannot be zero (would divide by zero)", "previous", previous
        )

    change = ((current - previous) / abs(previous)) * 100

    return round(change, 2)


@log_operation("stats_growth_rate")
def calculate_growth_rate(
    start_value: Union[int, float], end_value: Union[int, float], periods: int
) -> float:
    """
    Calculate compound annual/period growth rate (CAGR).

    Formula: ((end_value / start_value) ^ (1/periods) - 1) × 100

    Args:
        start_value: Initial value
        end_value: Final value
        periods: Number of time periods

    Returns:
        Growth rate per period (as percentage)

    Example:
        >>> calculate_growth_rate(100, 150, 3)
        14.47  # 14.47% growth per period
    """
    if start_value <= 0:
        raise ValidationError(
            "Start value must be positive", "start_value", start_value
        )

    if end_value <= 0:
        raise ValidationError("End value must be positive", "end_value", end_value)

    if periods <= 0:
        raise ValidationError("Periods must be positive", "periods", periods)

    # CAGR = (end/start)^(1/periods) - 1
    ratio = end_value / start_value
    growth_rate = (ratio ** (1 / periods) - 1) * 100

    return round(growth_rate, 2)


@log_operation("stats_volatility")
def calculate_volatility(data: List[Union[int, float]]) -> float:
    """
    Calculate volatility (coefficient of variation).

    Measures relative variability: (std_dev / mean) × 100

    Lower values indicate more consistent/stable performance.

    Args:
        data: Time series data

    Returns:
        Coefficient of variation (as percentage)

    Example:
        >>> data = [100, 102, 98, 101, 99]
        >>> calculate_volatility(data)
        1.51  # Low volatility (stable)

        >>> data = [100, 150, 80, 130, 90]
        >>> calculate_volatility(data)
        24.19  # High volatility (unstable)
    """
    if not data:
        raise ValidationError("Data cannot be empty", "data", None)

    if len(data) < 2:
        return 0.0

    # Calculate mean
    mean = sum(data) / len(data)

    if mean == 0:
        raise ValidationError(
            "Cannot calculate volatility when mean is zero", "data", mean
        )

    # Calculate standard deviation
    variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
    std_dev = math.sqrt(variance)

    # Coefficient of variation
    cv = (std_dev / abs(mean)) * 100

    return round(cv, 2)


# =============================================================================
# Utility Functions
# =============================================================================


def check_dependencies():
    """
    Check if all required dependencies are available.
    Time series tools use only Python standard library.

    Raises:
        ImportError: If required modules are not available
    """
    # Only uses Python standard library
    # No external dependencies required
    pass
