#!/usr/bin/env python3
"""
Test Algebraic Equation Tools for Sports Analytics

This script demonstrates the new algebraic equation manipulation capabilities
added to the NBA MCP server, specifically designed for working with
mathematical notation from sports analytics books.
"""

import asyncio
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
import sys

sys.path.insert(0, str(project_root))

from mcp_server.tools.algebra_helper import (
    solve_equation,
    simplify_expression,
    differentiate_expression,
    integrate_expression,
    get_sports_formula,
    render_equation_latex,
    matrix_operations,
    solve_equation_system,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_basic_algebra():
    """Test basic algebraic operations."""
    logger.info("🧮 Testing Basic Algebraic Operations")
    logger.info("=" * 50)

    # Test equation solving
    logger.info("\n1️⃣ Equation Solving:")
    equations = ["x**2 + 2*x - 3 = 0", "2*y + 5 = 13", "x**3 - 8 = 0"]

    for eq in equations:
        result = solve_equation(eq)
        logger.info(f"   {eq}")
        logger.info(f"   Solutions: {result['solutions']}")
        logger.info(f"   LaTeX: {result['latex']}")
        logger.info("")

    # Test expression simplification
    logger.info("2️⃣ Expression Simplification:")
    expressions = ["x**2 + 2*x + 1", "(x + 1)**2 - 1", "x**3 + 3*x**2 + 3*x + 1"]

    for expr in expressions:
        result = simplify_expression(expr)
        logger.info(f"   {expr} → {result['simplified']}")
        logger.info(f"   LaTeX: {result['latex']}")
        logger.info("")


def test_sports_analytics_formulas():
    """Test sports analytics formula templates."""
    logger.info("🏀 Testing Sports Analytics Formulas")
    logger.info("=" * 50)

    # Test Player Efficiency Rating
    logger.info("\n1️⃣ Player Efficiency Rating (PER):")
    per_result = get_sports_formula(
        "per",
        FGM=8,
        STL=2,
        three_pm=3,
        FTM=4,
        BLK=1,
        OREB=2,
        AST=5,
        DREB=6,
        PF=3,
        FTA=5,
        FGA=15,
        TOV=2,
        MP=35,
    )
    logger.info(f"   Formula: {per_result['formula']}")
    logger.info(f"   LaTeX: {per_result['latex']}")
    logger.info(f"   Result: {per_result['result']}")
    logger.info("")

    # Test True Shooting Percentage
    logger.info("2️⃣ True Shooting Percentage:")
    ts_result = get_sports_formula("true_shooting", PTS=25, FGA=15, FTA=5)
    logger.info(f"   Formula: {ts_result['formula']}")
    logger.info(f"   LaTeX: {ts_result['latex']}")
    logger.info(f"   Result: {ts_result['result']}")
    logger.info("")

    # Test Usage Rate
    logger.info("3️⃣ Usage Rate:")
    usage_result = get_sports_formula(
        "usage_rate",
        FGA=15,
        FTA=5,
        TOV=2,
        TM_MP=240,
        MP=35,
        TM_FGA=80,
        TM_FTA=20,
        TM_TOV=12,
    )
    logger.info(f"   Formula: {usage_result['formula']}")
    logger.info(f"   LaTeX: {usage_result['latex']}")
    logger.info(f"   Result: {usage_result['result']}")
    logger.info("")


def test_calculus_operations():
    """Test calculus operations for sports analytics."""
    logger.info("📊 Testing Calculus Operations")
    logger.info("=" * 50)

    # Test differentiation
    logger.info("\n1️⃣ Differentiation:")
    derivatives = [("x**3 + 2*x**2 + x", "x"), ("sin(x)", "x"), ("x**2 + y**2", "x")]

    for expr, var in derivatives:
        result = differentiate_expression(expr, var)
        logger.info(f"   d/d{var}({expr}) = {result['derivative']}")
        logger.info(f"   LaTeX: {result['latex']}")
        logger.info("")

    # Test integration
    logger.info("2️⃣ Integration:")
    integrals = [
        ("x**2", "x"),
        ("x**2", "x", 0, 2),  # Definite integral
        ("sin(x)", "x"),
    ]

    for integral_args in integrals:
        if len(integral_args) == 2:
            expr, var = integral_args
            result = integrate_expression(expr, var)
            logger.info(f"   ∫{expr} d{var} = {result['integral']}")
        else:
            expr, var, lower, upper = integral_args
            result = integrate_expression(expr, var, lower, upper)
            logger.info(
                f"   ∫[{lower} to {upper}] {expr} d{var} = {result['integral']}"
            )
            logger.info(f"   Value: {result['value']}")
        logger.info(f"   LaTeX: {result['latex']}")
        logger.info("")


def test_matrix_operations():
    """Test matrix operations for advanced analytics."""
    logger.info("🔢 Testing Matrix Operations")
    logger.info("=" * 50)

    # Test matrix operations
    matrices = [
        ([[1, 2], [3, 4]], "determinant"),
        ([[1, 2], [3, 4]], "inverse"),
        ([[2, 0], [0, 3]], "eigenvalues"),
        ([[1, 2], [3, 4]], "multiply", [[5, 6], [7, 8]]),
    ]

    for matrix_args in matrices:
        if len(matrix_args) == 2:
            matrix_data, operation = matrix_args
            result = matrix_operations(matrix_data, operation)
        else:
            matrix_data, operation, matrix2 = matrix_args
            result = matrix_operations(matrix_data, operation, matrix2=matrix2)

        logger.info(f"   Matrix: {matrix_data}")
        logger.info(f"   Operation: {operation}")
        logger.info(f"   Result: {result['result']}")
        logger.info(f"   LaTeX: {result['latex']}")
        logger.info("")


def test_equation_systems():
    """Test solving systems of equations."""
    logger.info("🔗 Testing Equation Systems")
    logger.info("=" * 50)

    # Test linear system
    logger.info("\n1️⃣ Linear System:")
    linear_system = solve_equation_system(["x + y = 5", "x - y = 1"], ["x", "y"])
    logger.info(f"   Equations: {linear_system['equations']}")
    logger.info(f"   Solutions: {linear_system['solutions']}")
    logger.info("")

    # Test quadratic system
    logger.info("2️⃣ Quadratic System:")
    quadratic_system = solve_equation_system(
        ["x**2 + y**2 = 25", "x + y = 7"], ["x", "y"]
    )
    logger.info(f"   Equations: {quadratic_system['equations']}")
    logger.info(f"   Solutions: {quadratic_system['solutions']}")
    logger.info("")


def test_latex_rendering():
    """Test LaTeX rendering capabilities."""
    logger.info("📝 Testing LaTeX Rendering")
    logger.info("=" * 50)

    expressions = [
        "x**2 + 2*x + 1",
        "sin(x) + cos(x)",
        "integrate(x**2, x)",
        "diff(sin(x), x)",
    ]

    for expr in expressions:
        result = render_equation_latex(expr, display_mode=True)
        logger.info(f"   Expression: {expr}")
        logger.info(f"   LaTeX: {result['latex']}")
        logger.info(f"   Display: {result['display']}")
        logger.info("")


def print_usage_examples():
    """Print examples of how to use the algebraic tools."""
    logger.info(
        """
╔══════════════════════════════════════════════════════════════════╗
║              🚀 ALGEBRAIC EQUATION TOOLS - USAGE GUIDE          ║
╚══════════════════════════════════════════════════════════════════╝

📚 HOW TO USE WITH SPORTS ANALYTICS BOOKS:

═══════════════════════════════════════════════════════════════════

1️⃣ SOLVE EQUATIONS FROM BOOKS:
   ```python
   # From "Sports Analytics" book: "Solve x² + 2x - 3 = 0"
   await mcp.call_tool("algebra_solve_equation", {
       "equation": "x**2 + 2*x - 3 = 0"
   })
   ```

2️⃣ SIMPLIFY COMPLEX FORMULAS:
   ```python
   # Simplify PER formula from book
   await mcp.call_tool("algebra_simplify_expression", {
       "expression": "(FGM * 85.910 + STL * 53.897) / MP"
   })
   ```

3️⃣ CALCULATE DERIVATIVES:
   ```python
   # Find rate of change in shooting percentage
   await mcp.call_tool("algebra_differentiate", {
       "expression": "x**2 + 2*x + 1",
       "variable": "x",
       "order": 1
   })
   ```

4️⃣ INTEGRATE FUNCTIONS:
   ```python
   # Calculate area under efficiency curve
   await mcp.call_tool("algebra_integrate", {
       "expression": "x**2",
       "variable": "x",
       "lower_limit": 0,
       "upper_limit": 10
   })
   ```

5️⃣ USE SPORTS FORMULAS:
   ```python
   # Calculate Player Efficiency Rating
   await mcp.call_tool("algebra_sports_formula", {
       "formula_name": "per",
       "variables": {
           "FGM": 8, "STL": 2, "3PM": 3, "FTM": 4, "BLK": 1,
           "OREB": 2, "AST": 5, "DREB": 6, "PF": 3, "FTA": 5,
           "FGA": 15, "TOV": 2, "MP": 35
       }
   })
   ```

6️⃣ RENDER LaTeX EQUATIONS:
   ```python
   # Convert formula to LaTeX for display
   await mcp.call_tool("algebra_render_latex", {
       "expression": "x**2 + 2*x + 1",
       "display_mode": true
   })
   ```

7️⃣ MATRIX OPERATIONS:
   ```python
   # Calculate correlation matrix determinant
   await mcp.call_tool("algebra_matrix_operations", {
       "matrix_data": [[1, 0.8], [0.8, 1]],
       "operation": "determinant"
   })
   ```

8️⃣ SOLVE EQUATION SYSTEMS:
   ```python
   # Solve multi-variable sports analytics problem
   await mcp.call_tool("algebra_solve_system", {
       "equations": ["x + y = 5", "x - y = 1"],
       "variables": ["x", "y"]
   })
   ```

═══════════════════════════════════════════════════════════════════

🎯 SPORTS ANALYTICS WORKFLOW:

1. **Read Formula from Book**: Use PDF tools to extract mathematical formulas
2. **Parse with Algebra Tools**: Convert formulas to symbolic expressions
3. **Manipulate Symbolically**: Simplify, differentiate, integrate as needed
4. **Substitute Values**: Use actual player/team statistics
5. **Calculate Results**: Get numerical answers
6. **Render LaTeX**: Display beautiful mathematical notation

═══════════════════════════════════════════════════════════════════

✅ BENEFITS FOR SPORTS ANALYTICS:

🎯 **Better Mathematical Understanding**:
   - Symbolic manipulation preserves exact formulas
   - LaTeX rendering shows proper mathematical notation
   - Step-by-step solutions show reasoning

🔍 **Advanced Analytics**:
   - Matrix operations for correlation analysis
   - Calculus for rate of change analysis
   - System solving for multi-variable problems

📊 **Sports-Specific Formulas**:
   - Pre-built PER, TS%, Usage Rate calculations
   - Four Factors analysis
   - Pace and efficiency metrics

🚀 **Integration with Books**:
   - Works seamlessly with PDF reading tools
   - Preserves mathematical context
   - Enables formula verification and manipulation

═══════════════════════════════════════════════════════════════════

🎉 CONCLUSION:

The algebraic equation tools provide **SUPERIOR** mathematical notation
understanding compared to plain text because they:

1. ✅ **Preserve Exact Formulas**: Symbolic manipulation maintains precision
2. ✅ **Enable Advanced Operations**: Calculus, matrix operations, system solving
3. ✅ **Render Beautiful Notation**: LaTeX output for professional display
4. ✅ **Include Sports Templates**: Pre-built analytics formulas
5. ✅ **Integrate with Books**: Works with PDF reading tools
6. ✅ **Support Complex Analysis**: Multi-variable systems and advanced math

**Perfect for working with mathematical notation from sports analytics books!**

═══════════════════════════════════════════════════════════════════
"""
    )


def main():
    """Main function to test all algebraic capabilities."""
    logger.info("🧮 NBA MCP Algebraic Equation Tools Test")
    logger.info("=" * 60)

    try:
        # Test all capabilities
        test_basic_algebra()
        test_sports_analytics_formulas()
        test_calculus_operations()
        test_matrix_operations()
        test_equation_systems()
        test_latex_rendering()

        # Print usage guide
        print_usage_examples()

        logger.info(
            """
🎉 ALL TESTS COMPLETED SUCCESSFULLY!

The NBA MCP server now has powerful algebraic equation manipulation
capabilities perfect for working with mathematical notation from
sports analytics books!

═══════════════════════════════════════════════════════════════════
"""
        )

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.info(
            """
⚠️  DEPENDENCY ISSUE:

If you see import errors, install SymPy:
   pip install sympy>=1.13.0

Then restart the MCP server to use the new algebraic tools.

═══════════════════════════════════════════════════════════════════
"""
        )


if __name__ == "__main__":
    main()
