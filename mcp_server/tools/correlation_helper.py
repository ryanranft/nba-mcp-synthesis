"""
Correlation and Regression Analysis
Statistical tools for analyzing relationships between variables

Pure Python implementation - no external dependencies
"""

from typing import List, Union, Dict, Any
import math

from mcp_server.exceptions import ValidationError
from mcp_server.tools.logger_config import log_operation


# =============================================================================
# Correlation Analysis
# =============================================================================

@log_operation("stats_correlation")
def calculate_correlation(x: List[Union[int, float]], y: List[Union[int, float]]) -> float:
    """
    Calculate Pearson correlation coefficient between two variables.

    Formula: r = Σ[(x - x̄)(y - ȳ)] / √[Σ(x - x̄)² × Σ(y - ȳ)²]

    Args:
        x: First variable (list of numbers)
        y: Second variable (list of numbers)

    Returns:
        Correlation coefficient (-1 to 1)
        - 1.0: Perfect positive correlation
        - 0.0: No correlation
        - -1.0: Perfect negative correlation

    Raises:
        ValidationError: If lists are empty, different lengths, or < 2 values

    Example:
        >>> x = [1, 2, 3, 4, 5]
        >>> y = [2, 4, 6, 8, 10]
        >>> calculate_correlation(x, y)
        1.0  # Perfect positive correlation

        >>> x = [1, 2, 3, 4, 5]
        >>> y = [10, 8, 6, 4, 2]
        >>> calculate_correlation(x, y)
        -1.0  # Perfect negative correlation
    """
    if not x or not y:
        raise ValidationError(
            "Both lists must be non-empty",
            "x or y",
            None
        )

    if len(x) != len(y):
        raise ValidationError(
            f"Lists must have same length: x={len(x)}, y={len(y)}",
            "x, y",
            None
        )

    if len(x) < 2:
        raise ValidationError(
            "Need at least 2 data points for correlation",
            "x, y",
            len(x)
        )

    n = len(x)

    # Calculate means
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calculate numerator: Σ[(x - x̄)(y - ȳ)]
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))

    # Calculate denominator: √[Σ(x - x̄)² × Σ(y - ȳ)²]
    sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))

    if sum_sq_x == 0 or sum_sq_y == 0:
        # One variable has no variance
        return 0.0

    denominator = math.sqrt(sum_sq_x * sum_sq_y)

    correlation = numerator / denominator

    # Handle floating point precision
    correlation = max(-1.0, min(1.0, correlation))

    return round(correlation, 4)


@log_operation("stats_covariance")
def calculate_covariance(
    x: List[Union[int, float]],
    y: List[Union[int, float]],
    sample: bool = True
) -> float:
    """
    Calculate covariance between two variables.

    Formula:
    - Sample: Cov(X,Y) = Σ[(x - x̄)(y - ȳ)] / (n-1)
    - Population: Cov(X,Y) = Σ[(x - x̄)(y - ȳ)] / n

    Args:
        x: First variable
        y: Second variable
        sample: Use sample covariance (n-1) if True, population (n) if False

    Returns:
        Covariance value

    Example:
        >>> x = [1, 2, 3, 4, 5]
        >>> y = [2, 4, 5, 4, 5]
        >>> calculate_covariance(x, y)
        2.5
    """
    if not x or not y:
        raise ValidationError(
            "Both lists must be non-empty",
            "x or y",
            None
        )

    if len(x) != len(y):
        raise ValidationError(
            f"Lists must have same length: x={len(x)}, y={len(y)}",
            "x, y",
            None
        )

    if sample and len(x) < 2:
        raise ValidationError(
            "Sample covariance requires at least 2 data points",
            "x, y",
            len(x)
        )

    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    covariance = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))

    divisor = (n - 1) if sample else n

    return round(covariance / divisor, 4)


@log_operation("stats_correlation_matrix")
def calculate_correlation_matrix(data: Dict[str, List[Union[int, float]]]) -> Dict[str, Dict[str, float]]:
    """
    Calculate correlation matrix for multiple variables.

    Args:
        data: Dictionary mapping variable names to lists of values

    Returns:
        Dictionary of dictionaries with correlations between all pairs

    Example:
        >>> data = {
        ...     "points": [20, 25, 22, 28],
        ...     "assists": [5, 7, 6, 8],
        ...     "rebounds": [8, 6, 7, 5]
        ... }
        >>> matrix = calculate_correlation_matrix(data)
        >>> matrix["points"]["assists"]
        0.98  # Strong positive correlation
    """
    if not data:
        raise ValidationError(
            "Data dictionary cannot be empty",
            "data",
            None
        )

    # Validate all lists have same length
    lengths = [len(values) for values in data.values()]
    if len(set(lengths)) > 1:
        raise ValidationError(
            "All variables must have same number of observations",
            "data",
            lengths
        )

    matrix = {}
    variables = list(data.keys())

    for var1 in variables:
        matrix[var1] = {}
        for var2 in variables:
            if var1 == var2:
                # Correlation with itself is always 1.0
                matrix[var1][var2] = 1.0
            else:
                # Calculate correlation
                corr = calculate_correlation(data[var1], data[var2])
                matrix[var1][var2] = corr

    return matrix


# =============================================================================
# Regression Analysis
# =============================================================================

@log_operation("stats_linear_regression")
def calculate_linear_regression(
    x: List[Union[int, float]],
    y: List[Union[int, float]]
) -> Dict[str, Any]:
    """
    Perform simple linear regression (y = mx + b).

    Uses least squares method to find best-fit line.

    Args:
        x: Independent variable
        y: Dependent variable

    Returns:
        Dictionary with:
        - slope: Regression slope (m)
        - intercept: Y-intercept (b)
        - r_squared: Coefficient of determination (R²)
        - equation: String representation of equation

    Raises:
        ValidationError: If lists are invalid

    Example:
        >>> x = [1, 2, 3, 4, 5]
        >>> y = [2, 4, 6, 8, 10]
        >>> model = calculate_linear_regression(x, y)
        >>> model['slope']
        2.0
        >>> model['intercept']
        0.0
        >>> model['r_squared']
        1.0  # Perfect fit
    """
    if not x or not y:
        raise ValidationError(
            "Both lists must be non-empty",
            "x or y",
            None
        )

    if len(x) != len(y):
        raise ValidationError(
            f"Lists must have same length: x={len(x)}, y={len(y)}",
            "x, y",
            None
        )

    if len(x) < 2:
        raise ValidationError(
            "Need at least 2 data points for regression",
            "x, y",
            len(x)
        )

    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calculate slope: m = Σ[(x - x̄)(y - ȳ)] / Σ[(x - x̄)²]
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

    if denominator == 0:
        raise ValidationError(
            "X variable has no variance (all values are the same)",
            "x",
            x
        )

    slope = numerator / denominator

    # Calculate intercept: b = ȳ - m*x̄
    intercept = mean_y - slope * mean_x

    # Calculate R² (coefficient of determination)
    r_squared = calculate_r_squared(x, y, slope, intercept)

    # Build equation string
    if intercept >= 0:
        equation = f"y = {slope:.4f}x + {intercept:.4f}"
    else:
        equation = f"y = {slope:.4f}x - {abs(intercept):.4f}"

    return {
        "slope": round(slope, 4),
        "intercept": round(intercept, 4),
        "r_squared": round(r_squared, 4),
        "equation": equation
    }


@log_operation("stats_predict")
def predict_values(
    slope: float,
    intercept: float,
    x_values: List[Union[int, float]]
) -> List[float]:
    """
    Make predictions using linear regression model.

    Args:
        slope: Model slope (from regression)
        intercept: Model intercept (from regression)
        x_values: New x values to predict

    Returns:
        List of predicted y values

    Example:
        >>> # After fitting: y = 2x + 1
        >>> slope, intercept = 2.0, 1.0
        >>> predict_values(slope, intercept, [6, 7, 8])
        [13.0, 15.0, 17.0]
    """
    if not x_values:
        raise ValidationError(
            "Must provide at least one x value to predict",
            "x_values",
            None
        )

    predictions = [slope * x + intercept for x in x_values]

    return [round(pred, 4) for pred in predictions]


@log_operation("stats_r_squared")
def calculate_r_squared(
    x: List[Union[int, float]],
    y: List[Union[int, float]],
    slope: float,
    intercept: float
) -> float:
    """
    Calculate R² (coefficient of determination).

    R² measures how well the regression line fits the data.
    - 1.0 = perfect fit
    - 0.0 = no better than using mean

    Formula: R² = 1 - (SS_res / SS_tot)
    Where:
    - SS_res = Σ(y - ŷ)²  (residual sum of squares)
    - SS_tot = Σ(y - ȳ)²  (total sum of squares)

    Args:
        x: Independent variable
        y: Dependent variable (actual values)
        slope: Regression slope
        intercept: Regression intercept

    Returns:
        R² value (0 to 1)

    Example:
        >>> x = [1, 2, 3, 4, 5]
        >>> y = [2, 4, 6, 8, 10]
        >>> calculate_r_squared(x, y, 2.0, 0.0)
        1.0  # Perfect fit
    """
    if len(x) != len(y):
        raise ValidationError(
            "Lists must have same length",
            "x, y",
            None
        )

    n = len(y)
    mean_y = sum(y) / n

    # Predicted values: ŷ = mx + b
    y_pred = [slope * x[i] + intercept for i in range(n)]

    # SS_res: Σ(y - ŷ)²
    ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))

    # SS_tot: Σ(y - ȳ)²
    ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))

    if ss_tot == 0:
        # Y has no variance
        return 1.0 if ss_res == 0 else 0.0

    r_squared = 1 - (ss_res / ss_tot)

    # Handle floating point precision (R² should be 0 to 1)
    r_squared = max(0.0, min(1.0, r_squared))

    return r_squared


# =============================================================================
# Utility Functions
# =============================================================================

def check_dependencies():
    """
    Check if all required dependencies are available.
    Correlation/regression use only Python standard library.

    Raises:
        ImportError: If required modules are not available
    """
    # Only uses Python standard library
    # No external dependencies required
    pass
