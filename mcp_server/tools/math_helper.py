"""
Mathematical Operations for NBA Analytics
Provides basic arithmetic and advanced calculations

Based on patterns from math-mcp repository
"""

from typing import List, Union
import math

from mcp_server.exceptions import ValidationError
from mcp_server.tools.logger_config import log_operation


# =============================================================================
# Arithmetic Operations
# =============================================================================


@log_operation("math_add")
def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Add two numbers together.

    Args:
        a: First number (addend)
        b: Second number (addend)

    Returns:
        Sum of a and b

    Example:
        >>> add(5, 3)
        8
        >>> add(10.5, 2.3)
        12.8
    """
    return a + b


@log_operation("math_subtract")
def subtract(
    minuend: Union[int, float], subtrahend: Union[int, float]
) -> Union[int, float]:
    """
    Subtract the second number from the first number.

    Args:
        minuend: The number to subtract from
        subtrahend: The number being subtracted

    Returns:
        Difference of minuend - subtrahend

    Example:
        >>> subtract(10, 3)
        7
        >>> subtract(5.5, 2.3)
        3.2
    """
    return minuend - subtrahend


@log_operation("math_multiply")
def multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Multiply two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b

    Example:
        >>> multiply(5, 3)
        15
        >>> multiply(2.5, 4)
        10.0
    """
    return a * b


@log_operation("math_divide")
def divide(numerator: Union[int, float], denominator: Union[int, float]) -> float:
    """
    Divide the first number by the second number.

    Args:
        numerator: The number being divided
        denominator: The number to divide by

    Returns:
        Quotient of numerator / denominator

    Raises:
        ValidationError: If denominator is zero

    Example:
        >>> divide(10, 2)
        5.0
        >>> divide(7, 2)
        3.5
    """
    if denominator == 0:
        raise ValidationError(
            "Division by zero is not allowed", "denominator", denominator
        )
    return numerator / denominator


@log_operation("math_sum")
def sum_numbers(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    Sum a list of numbers.

    Args:
        numbers: List of numbers to sum

    Returns:
        Sum of all numbers

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> sum_numbers([1, 2, 3, 4, 5])
        15
        >>> sum_numbers([10.5, 20.3, 15.2])
        46.0
    """
    if not numbers:
        raise ValidationError("Numbers list cannot be empty", "numbers", numbers)

    return sum(numbers)


@log_operation("math_modulo")
def modulo(
    numerator: Union[int, float], denominator: Union[int, float]
) -> Union[int, float]:
    """
    Calculate the remainder when dividing two numbers.

    Args:
        numerator: The number being divided
        denominator: The number to divide by

    Returns:
        Remainder of numerator % denominator

    Raises:
        ValidationError: If denominator is zero

    Example:
        >>> modulo(10, 3)
        1
        >>> modulo(17, 5)
        2
    """
    if denominator == 0:
        raise ValidationError(
            "Modulo by zero is not allowed", "denominator", denominator
        )
    return numerator % denominator


# =============================================================================
# Rounding Operations
# =============================================================================


@log_operation("math_round")
def round_number(number: Union[int, float], decimals: int = 0) -> Union[int, float]:
    """
    Round a number to the nearest integer or specified decimal places.

    Args:
        number: The number to round
        decimals: Number of decimal places (default: 0)

    Returns:
        Rounded number

    Example:
        >>> round_number(3.7)
        4
        >>> round_number(3.14159, 2)
        3.14
    """
    return round(number, decimals)


@log_operation("math_floor")
def floor(number: Union[int, float]) -> int:
    """
    Round a number down to the nearest integer.

    Args:
        number: The number to round down

    Returns:
        Largest integer less than or equal to number

    Example:
        >>> floor(3.7)
        3
        >>> floor(-2.3)
        -3
    """
    return math.floor(number)


@log_operation("math_ceiling")
def ceiling(number: Union[int, float]) -> int:
    """
    Round a number up to the nearest integer.

    Args:
        number: The number to round up

    Returns:
        Smallest integer greater than or equal to number

    Example:
        >>> ceiling(3.2)
        4
        >>> ceiling(-2.7)
        -2
    """
    return math.ceil(number)


# =============================================================================
# Trigonometric Operations (for shot angle calculations, etc.)
# =============================================================================


@log_operation("math_sin")
def sine(radians: float) -> float:
    """
    Calculate the sine of an angle in radians.

    Args:
        radians: Angle in radians

    Returns:
        Sine of the angle (-1 to 1)

    Example:
        >>> sine(0)
        0.0
        >>> sine(math.pi / 2)
        1.0
    """
    return math.sin(radians)


@log_operation("math_cos")
def cosine(radians: float) -> float:
    """
    Calculate the cosine of an angle in radians.

    Args:
        radians: Angle in radians

    Returns:
        Cosine of the angle (-1 to 1)

    Example:
        >>> cosine(0)
        1.0
        >>> cosine(math.pi)
        -1.0
    """
    return math.cos(radians)


@log_operation("math_tan")
def tangent(radians: float) -> float:
    """
    Calculate the tangent of an angle in radians.

    Args:
        radians: Angle in radians

    Returns:
        Tangent of the angle

    Example:
        >>> tangent(0)
        0.0
        >>> tangent(math.pi / 4)
        1.0
    """
    return math.tan(radians)


@log_operation("math_degrees_to_radians")
def degrees_to_radians(degrees: float) -> float:
    """
    Convert degrees to radians.

    Args:
        degrees: Angle in degrees

    Returns:
        Angle in radians

    Example:
        >>> degrees_to_radians(180)
        3.141592653589793
        >>> degrees_to_radians(90)
        1.5707963267948966
    """
    return math.radians(degrees)


@log_operation("math_radians_to_degrees")
def radians_to_degrees(radians: float) -> float:
    """
    Convert radians to degrees.

    Args:
        radians: Angle in radians

    Returns:
        Angle in degrees

    Example:
        >>> radians_to_degrees(math.pi)
        180.0
        >>> radians_to_degrees(math.pi / 2)
        90.0
    """
    return math.degrees(radians)


# =============================================================================
# Utility Functions
# =============================================================================


def check_dependencies():
    """
    Check if all required dependencies are available.
    Math operations use only Python standard library.

    Raises:
        ImportError: If required modules are not available
    """
    # Math operations only use Python standard library
    # No external dependencies required
    pass
