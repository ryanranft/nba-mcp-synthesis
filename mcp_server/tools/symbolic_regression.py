"""
Symbolic Regression for Sports Analytics

This module provides symbolic regression capabilities for discovering new formulas
from NBA player and team data. It uses statistical methods and machine learning
to fit symbolic expressions to performance metrics.

Author: NBA MCP Server Team
Date: October 13, 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging
import re

try:
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr
    SYMPY_AVAILABLE = True
except ImportError:
    sp = None
    SYMPY_AVAILABLE = False

try:
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.preprocessing import PolynomialFeatures, StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ..exceptions import ValidationError
from .logger_config import log_operation

# Use ValidationError for all tool errors
ToolError = ValidationError

# Initialize logger
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are available"""
    if not SYMPY_AVAILABLE:
        raise ToolError("SymPy is required for symbolic regression. Please install it: pip install sympy")
    if not SKLEARN_AVAILABLE:
        raise ToolError("Scikit-learn is required for symbolic regression. Please install it: pip install scikit-learn")


@log_operation("symbolic_regression_discover_formula")
def discover_formula_from_data(
    data: Dict[str, List[float]],
    target_variable: str,
    input_variables: List[str],
    regression_type: str = "linear",
    optimization_method: str = "gradient_descent",
    max_complexity: int = 5,
    min_r_squared: float = 0.7,
    generations: int = 20,
    population_size: int = 500,
    tournament_size: int = 20,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Discovers a mathematical formula from given sports data using regression.

    This is a simplified version that uses polynomial regression and feature engineering
    to discover formulas. For more advanced genetic programming, consider using gplearn.

    Args:
        data: Dictionary mapping variable names to lists of values
        target_variable: The name of the variable to predict
        input_variables: A list of variable names to use as inputs
        regression_type: Type of regression ("linear", "polynomial", "custom")
        optimization_method: Method for optimization
        max_complexity: Maximum degree for polynomial features
        min_r_squared: Minimum R-squared threshold
        generations: Not used in this simplified version
        population_size: Not used in this simplified version
        tournament_size: Not used in this simplified version
        random_state: Seed for reproducibility

    Returns:
        Dictionary with discovered formula, R-squared, and metrics
    """
    check_dependencies()

    logger.info(f"Starting formula discovery for target '{target_variable}' with inputs {input_variables}")

    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)

        # Validate inputs
        if target_variable not in df.columns:
            raise ValidationError(f"Target variable '{target_variable}' not found in data")
        for var in input_variables:
            if var not in df.columns:
                raise ValidationError(f"Input variable '{var}' not found in data")

        if len(df) < 10:
            raise ValidationError("Insufficient data points. Need at least 10 for regression")

        # Prepare data
        X = df[input_variables].values
        y = df[target_variable].values

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        best_model = None
        best_r2 = -np.inf
        best_formula_str = ""
        best_complexity = 0

        if regression_type in ["polynomial", "custom"]:
            # Try different polynomial degrees
            for degree in range(1, min(max_complexity + 1, 4)):
                poly = PolynomialFeatures(degree=degree, include_bias=False)
                X_train_poly = poly.fit_transform(X_train)
                X_test_poly = poly.transform(X_test)

                # Try Ridge regression for regularization
                model = Ridge(alpha=0.1, random_state=random_state)
                model.fit(X_train_poly, y_train)

                # Predict and evaluate
                y_pred = model.predict(X_test_poly)
                r2 = r2_score(y_test, y_pred)

                if r2 > best_r2:
                    best_r2 = r2
                    best_model = (model, poly, scaler)
                    best_complexity = degree

                    # Build formula string
                    feature_names = poly.get_feature_names_out(input_variables)
                    coeffs = model.coef_
                    intercept = model.intercept_

                    terms = []
                    for i, (coeff, feat) in enumerate(zip(coeffs, feature_names)):
                        if abs(coeff) > 1e-6:  # Only include significant terms
                            # Clean up feature name (x0^2 -> x0**2 for SymPy)
                            feat_clean = feat.replace('^', '**').replace(' ', '*')
                            if coeff >= 0 and terms:
                                terms.append(f"+ {coeff:.4f}*{feat_clean}")
                            else:
                                terms.append(f"{coeff:.4f}*{feat_clean}")

                    if intercept != 0:
                        if intercept >= 0:
                            terms.append(f"+ {intercept:.4f}")
                        else:
                            terms.append(f"{intercept:.4f}")

                    best_formula_str = " ".join(terms)
        else:
            # Linear regression
            model = LinearRegression()
            model.fit(X_train_scaled, y_train)

            y_pred = model.predict(X_test_scaled)
            best_r2 = r2_score(y_test, y_pred)
            best_model = (model, None, scaler)
            best_complexity = 1

            # Build formula string
            coeffs = model.coef_
            intercept = model.intercept_

            terms = []
            for i, (coeff, var) in enumerate(zip(coeffs, input_variables)):
                if abs(coeff) > 1e-6:
                    if coeff >= 0 and terms:
                        terms.append(f"+ {coeff:.4f}*{var}")
                    else:
                        terms.append(f"{coeff:.4f}*{var}")

            if intercept != 0:
                if intercept >= 0:
                    terms.append(f"+ {intercept:.4f}")
                else:
                    terms.append(f"{intercept:.4f}")

            best_formula_str = " ".join(terms)

        if best_r2 < min_r_squared:
            raise ToolError(
                f"Best formula's R-squared ({best_r2:.2f}) is below minimum threshold ({min_r_squared})"
            )

        # Convert to SymPy if possible
        try:
            sympy_formula = parse_expr(best_formula_str, evaluate=False)
            latex_formula = sp.latex(sympy_formula)
        except Exception as e:
            logger.warning(f"Could not convert to SymPy/LaTeX: {e}")
            sympy_formula = best_formula_str
            latex_formula = best_formula_str

        # Calculate final metrics
        model_obj, poly_obj, scaler_obj = best_model
        if poly_obj:
            X_test_transformed = poly_obj.transform(X_test)
        else:
            X_test_transformed = scaler_obj.transform(X_test)

        y_pred_final = model_obj.predict(X_test_transformed)
        mse = mean_squared_error(y_test, y_pred_final)

        logger.info(f"Formula discovered with R²={best_r2:.2f}, MSE={mse:.2f}")

        return {
            "formula_string": best_formula_str,
            "formula_sympy": str(sympy_formula),
            "formula_latex": latex_formula,
            "r_squared": float(best_r2),
            "mean_squared_error": float(mse),
            "description": f"Discovered formula for {target_variable} using {regression_type} regression",
            "input_variables": input_variables,
            "target_variable": target_variable,
            "complexity": best_complexity,
            "regression_type": regression_type
        }

    except Exception as e:
        logger.error(f"Formula discovery failed: {e}")
        raise


@log_operation("symbolic_regression_validate_formula")
def validate_discovered_formula(
    formula: str,
    test_data: Dict[str, List[float]],
    target_variable: str,
    threshold_r_squared: float = 0.7
) -> Dict[str, Any]:
    """
    Validates a discovered formula against a test dataset.

    Args:
        formula: The formula string to validate
        test_data: Dictionary mapping variable names to lists of values
        target_variable: The name of the variable to predict
        threshold_r_squared: Minimum R-squared for successful validation

    Returns:
        Dictionary with validation results
    """
    check_dependencies()

    logger.info(f"Validating formula '{formula}' for target '{target_variable}'")

    try:
        # Parse formula
        sympy_formula = parse_expr(formula)

        # Create DataFrame
        df_test = pd.DataFrame(test_data)

        if target_variable not in df_test.columns:
            raise ValidationError(f"Target variable '{target_variable}' not found in test data")

        # Get input variables from formula
        input_vars = [str(s) for s in sympy_formula.free_symbols if str(s) != target_variable]

        # Ensure all input variables are in test data
        for var in input_vars:
            if var not in df_test.columns:
                raise ValidationError(f"Formula variable '{var}' not found in test data")

        # Evaluate formula for each data point
        y_true = df_test[target_variable].values
        y_pred = []

        for i in range(len(y_true)):
            subs_dict = {sp.Symbol(var): df_test[var].iloc[i] for var in input_vars}
            try:
                pred_val = float(sympy_formula.evalf(subs=subs_dict))
                y_pred.append(pred_val)
            except Exception as e:
                logger.warning(f"Error evaluating formula for data point {i}: {e}")
                y_pred.append(np.nan)

        y_pred = np.array(y_pred)

        # Filter out NaNs
        valid_mask = ~np.isnan(y_pred)
        if not np.any(valid_mask):
            raise ToolError("Formula evaluation resulted in no valid predictions")

        y_true_valid = y_true[valid_mask]
        y_pred_valid = y_pred[valid_mask]

        if len(y_true_valid) < 2:
            raise ToolError("Insufficient valid data points for R-squared calculation")

        # Calculate metrics
        r2 = r2_score(y_true_valid, y_pred_valid)
        mse = mean_squared_error(y_true_valid, y_pred_valid)
        mae = mean_absolute_error(y_true_valid, y_pred_valid)

        if r2 < threshold_r_squared:
            raise ToolError(
                f"Formula validation failed: R²={r2:.2f} < threshold={threshold_r_squared}"
            )

        logger.info(f"Formula validated successfully. R²={r2:.2f}, MSE={mse:.2f}")

        return {
            "formula": formula,
            "r_squared": float(r2),
            "mean_squared_error": float(mse),
            "mean_absolute_error": float(mae),
            "validation_status": "success",
            "description": "Formula successfully validated against test data",
            "valid_predictions": int(np.sum(valid_mask)),
            "total_predictions": len(y_true)
        }

    except Exception as e:
        logger.error(f"Formula validation failed: {e}")
        raise


@log_operation("symbolic_regression_generate_custom_metric")
def generate_custom_metric(
    formula: str,
    metric_name: str,
    description: str,
    variables: List[str],
    parameters: Dict[str, float]
) -> Dict[str, Any]:
    """
    Generates and registers a custom analytics metric.

    Args:
        formula: The discovered formula string
        metric_name: A unique name for the custom metric
        description: A description of what the metric measures
        variables: A list of input variables used in the formula
        parameters: A dictionary of optimized parameters

    Returns:
        Dictionary confirming metric creation
    """
    check_dependencies()

    logger.info(f"Generating custom metric '{metric_name}' from formula: {formula}")

    # Validate inputs
    if not metric_name or not formula or not description or not variables:
        raise ValidationError("Metric name, formula, description, and variables cannot be empty")

    # Validate metric name format
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', metric_name):
        raise ValidationError(
            "Metric name must start with letter and contain only letters, numbers, and underscores"
        )

    try:
        # Validate formula is parseable
        parse_expr(formula)
    except Exception as e:
        raise ValidationError(f"Invalid formula string: {e}")

    # In a production system, this would save to a database or config file
    # For now, we return a success message

    logger.info(f"Custom metric '{metric_name}' generated successfully")

    return {
        "status": "success",
        "metric_name": metric_name,
        "formula": formula,
        "description": description,
        "variables": variables,
        "parameters": parameters,
        "message": f"Custom metric '{metric_name}' created successfully",
        "note": "In production, this metric would be persisted to database/config"
    }


@log_operation("symbolic_regression_discover_patterns")
def discover_formula_patterns(
    data: Dict[str, List[float]],
    target_variable: str,
    discovery_method: str = "correlation",
    max_formulas: int = 10,
    complexity_range: Tuple[int, int] = (1, 5)
) -> Dict[str, Any]:
    """
    Discovers potential formula patterns from data using statistical methods.

    Args:
        data: Dataset for formula discovery
        target_variable: Variable to predict
        discovery_method: Method for discovering relationships
        max_formulas: Maximum number of patterns to discover
        complexity_range: Range of complexity to explore

    Returns:
        Dictionary with discovered patterns
    """
    check_dependencies()

    logger.info(f"Discovering patterns for target '{target_variable}' using '{discovery_method}' method")

    try:
        df = pd.DataFrame(data)

        if target_variable not in df.columns:
            raise ValidationError(f"Target variable '{target_variable}' not found in data")

        input_vars = [col for col in df.columns if col != target_variable]
        if not input_vars:
            raise ValidationError("No input variables available for pattern discovery")

        results = []

        if discovery_method == "correlation":
            # Find correlations
            correlations = df.corr()[target_variable].drop(target_variable).abs().sort_values(ascending=False)

            for var, corr in correlations.items():
                if corr > 0.5:  # Strong correlation threshold
                    formula_suggestion = f"{target_variable} = c1 * {var} + c0"
                    results.append({
                        "pattern_type": "linear_correlation",
                        "score": float(corr),
                        "suggested_formula": formula_suggestion,
                        "variables": [var, target_variable],
                        "description": f"Strong linear correlation between {target_variable} and {var}"
                    })

        elif discovery_method == "polynomial":
            # Try polynomial relationships
            for var in input_vars:
                X = df[[var]].values
                y = df[target_variable].values

                for degree in range(complexity_range[0], min(complexity_range[1] + 1, 4)):
                    poly = PolynomialFeatures(degree=degree)
                    X_poly = poly.fit_transform(X)

                    model = LinearRegression()
                    model.fit(X_poly, y)

                    r2 = model.score(X_poly, y)

                    if r2 > 0.6:  # Good fit threshold
                        feature_names = poly.get_feature_names_out([var])
                        coeffs = model.coef_

                        terms = []
                        for coeff, feat in zip(coeffs[1:], feature_names[1:]):  # Skip intercept term
                            if abs(coeff) > 1e-6:
                                feat_clean = feat.replace('^', '**')
                                terms.append(f"{coeff:.4f}*{feat_clean}")

                        formula_suggestion = f"{target_variable} = {' + '.join(terms)} + {model.intercept_:.4f}"

                        results.append({
                            "pattern_type": f"polynomial_degree_{degree}",
                            "score": float(r2),
                            "suggested_formula": formula_suggestion,
                            "variables": [var, target_variable],
                            "description": f"Polynomial relationship (degree {degree}) between {target_variable} and {var}"
                        })

        else:
            raise ToolError(f"Discovery method '{discovery_method}' not supported")

        if not results:
            raise ToolError("No significant formula patterns discovered with the given method and data")

        # Sort by score and limit
        results = sorted(results, key=lambda x: x['score'], reverse=True)[:max_formulas]

        logger.info(f"Discovered {len(results)} formula patterns")

        return {
            "status": "success",
            "discovered_patterns": results,
            "message": f"Successfully discovered {len(results)} formula patterns",
            "discovery_method": discovery_method,
            "target_variable": target_variable
        }

    except Exception as e:
        logger.error(f"Pattern discovery failed: {e}")
        raise
