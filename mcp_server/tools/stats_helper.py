"""
Statistical Operations for NBA Analytics
Provides statistical calculations for player and team analysis

Based on patterns from math-mcp repository
"""

from typing import List, Union, Dict, Any
import math
from collections import Counter

from mcp_server.exceptions import ValidationError
from mcp_server.tools.logger_config import log_operation


# =============================================================================
# Basic Statistical Operations
# =============================================================================

@log_operation("stats_mean")
def calculate_mean(numbers: List[Union[int, float]]) -> float:
    """
    Calculate the arithmetic mean (average).

    Args:
        numbers: List of numbers

    Returns:
        Mean value

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> calculate_mean([10, 20, 30])
        20.0
        >>> calculate_mean([15.5, 22.3, 18.7])
        18.833333333333332
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    return sum(numbers) / len(numbers)


@log_operation("stats_median")
def calculate_median(numbers: List[Union[int, float]]) -> float:
    """
    Calculate the median value.

    Args:
        numbers: List of numbers

    Returns:
        Median value (middle value when sorted)

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> calculate_median([1, 3, 5])
        3.0
        >>> calculate_median([1, 2, 3, 4])
        2.5
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    mid = n // 2

    if n % 2 == 0:
        # Even number of elements - return average of middle two
        return (sorted_numbers[mid - 1] + sorted_numbers[mid]) / 2
    else:
        # Odd number of elements - return middle element
        return float(sorted_numbers[mid])


@log_operation("stats_mode")
def calculate_mode(numbers: List[Union[int, float]]) -> Union[int, float, List[Union[int, float]]]:
    """
    Find the most common number(s) in a list.

    Args:
        numbers: List of numbers

    Returns:
        Mode value(s). Returns single value if one mode,
        list if multiple modes with same frequency

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> calculate_mode([1, 2, 2, 3])
        2
        >>> calculate_mode([1, 1, 2, 2, 3])
        [1, 2]
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    # Count occurrences
    counter = Counter(numbers)
    max_count = max(counter.values())

    # Find all numbers with max count
    modes = [num for num, count in counter.items() if count == max_count]

    # Return single value if only one mode, otherwise return list
    if len(modes) == 1:
        return modes[0]
    else:
        return modes


@log_operation("stats_min")
def calculate_min(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    Find the minimum value from a list of numbers.

    Args:
        numbers: List of numbers

    Returns:
        Minimum value

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> calculate_min([10, 5, 20, 3])
        3
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    return min(numbers)


@log_operation("stats_max")
def calculate_max(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    Find the maximum value from a list of numbers.

    Args:
        numbers: List of numbers

    Returns:
        Maximum value

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> calculate_max([10, 5, 20, 3])
        20
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    return max(numbers)


# =============================================================================
# Advanced Statistical Operations
# =============================================================================

@log_operation("stats_range")
def calculate_range(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    Calculate the range (difference between max and min).

    Args:
        numbers: List of numbers

    Returns:
        Range (max - min)

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> calculate_range([10, 5, 20, 3])
        17
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    return max(numbers) - min(numbers)


@log_operation("stats_variance")
def calculate_variance(numbers: List[Union[int, float]], sample: bool = True) -> float:
    """
    Calculate the variance (measure of spread).

    Args:
        numbers: List of numbers
        sample: If True, calculate sample variance (n-1). If False, population variance (n)

    Returns:
        Variance

    Raises:
        ValidationError: If numbers list is empty or has only one element when sample=True

    Example:
        >>> calculate_variance([2, 4, 6, 8, 10])
        10.0
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    if sample and len(numbers) < 2:
        raise ValidationError(
            "Sample variance requires at least 2 numbers",
            "numbers",
            numbers
        )

    mean = calculate_mean(numbers)
    squared_diffs = [(x - mean) ** 2 for x in numbers]

    divisor = len(numbers) - 1 if sample else len(numbers)
    return sum(squared_diffs) / divisor


@log_operation("stats_std_dev")
def calculate_std_dev(numbers: List[Union[int, float]], sample: bool = True) -> float:
    """
    Calculate the standard deviation (square root of variance).

    Args:
        numbers: List of numbers
        sample: If True, calculate sample std dev. If False, population std dev

    Returns:
        Standard deviation

    Raises:
        ValidationError: If numbers list is empty or has only one element when sample=True

    Example:
        >>> calculate_std_dev([2, 4, 6, 8, 10])
        3.1622776601683795
    """
    variance = calculate_variance(numbers, sample)
    return math.sqrt(variance)


@log_operation("stats_percentile")
def calculate_percentile(numbers: List[Union[int, float]], percentile: float) -> float:
    """
    Calculate a specific percentile of the data.

    Args:
        numbers: List of numbers
        percentile: Percentile to calculate (0-100)

    Returns:
        Value at the given percentile

    Raises:
        ValidationError: If numbers list is empty or percentile out of range

    Example:
        >>> calculate_percentile([1, 2, 3, 4, 5], 50)
        3.0
        >>> calculate_percentile([1, 2, 3, 4, 5], 75)
        4.0
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    if not 0 <= percentile <= 100:
        raise ValidationError(
            "Percentile must be between 0 and 100",
            "percentile",
            percentile
        )

    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)

    # Calculate index
    if percentile == 100:
        return float(sorted_numbers[-1])
    elif percentile == 0:
        return float(sorted_numbers[0])

    # Linear interpolation between closest ranks
    rank = (percentile / 100) * (n - 1)
    lower_index = int(math.floor(rank))
    upper_index = int(math.ceil(rank))

    if lower_index == upper_index:
        return float(sorted_numbers[lower_index])

    # Interpolate
    lower_value = sorted_numbers[lower_index]
    upper_value = sorted_numbers[upper_index]
    fraction = rank - lower_index

    return lower_value + (upper_value - lower_value) * fraction


@log_operation("stats_quartiles")
def calculate_quartiles(numbers: List[Union[int, float]]) -> Dict[str, float]:
    """
    Calculate Q1, Q2 (median), and Q3.

    Args:
        numbers: List of numbers

    Returns:
        Dictionary with Q1, Q2, Q3 values

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> calculate_quartiles([1, 2, 3, 4, 5])
        {'Q1': 2.0, 'Q2': 3.0, 'Q3': 4.0}
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    return {
        "Q1": calculate_percentile(numbers, 25),
        "Q2": calculate_percentile(numbers, 50),  # Median
        "Q3": calculate_percentile(numbers, 75)
    }


@log_operation("stats_summary")
def calculate_summary_stats(numbers: List[Union[int, float]]) -> Dict[str, Any]:
    """
    Calculate comprehensive summary statistics.

    Args:
        numbers: List of numbers

    Returns:
        Dictionary with count, mean, median, min, max, std_dev, quartiles

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> stats = calculate_summary_stats([1, 2, 3, 4, 5])
        >>> stats['mean']
        3.0
        >>> stats['median']
        3.0
    """
    if not numbers:
        raise ValidationError(
            "Numbers list cannot be empty",
            "numbers",
            numbers
        )

    quartiles = calculate_quartiles(numbers)

    return {
        "count": len(numbers),
        "mean": calculate_mean(numbers),
        "median": calculate_median(numbers),
        "mode": calculate_mode(numbers),
        "min": calculate_min(numbers),
        "max": calculate_max(numbers),
        "range": calculate_range(numbers),
        "std_dev": calculate_std_dev(numbers) if len(numbers) > 1 else 0.0,
        "variance": calculate_variance(numbers) if len(numbers) > 1 else 0.0,
        "Q1": quartiles["Q1"],
        "Q2": quartiles["Q2"],
        "Q3": quartiles["Q3"],
        "IQR": quartiles["Q3"] - quartiles["Q1"]  # Interquartile Range
    }


# =============================================================================
# Utility Functions
# =============================================================================

def check_dependencies():
    """
    Check if all required dependencies are available.
    Statistical operations use only Python standard library.

    Raises:
        ImportError: If required modules are not available
    """
    # Statistical operations only use Python standard library
    # No external dependencies required
    pass
