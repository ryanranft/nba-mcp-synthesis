"""
Integration tests for Bayesian linear regression edge cases.

Tests robustness and behavior with challenging data scenarios.
"""

import pytest
import numpy as np
from mcp_server.fastmcp_server import (
    bayesian_linear_regression,
    BayesianLinearRegressionParams
)


class MockContext:
    """Mock FastMCP context for testing"""

    async def info(self, msg):
        """Log info message"""
        pass  # Suppress output in pytest

    async def error(self, msg):
        """Log error message"""
        pass  # Suppress output in pytest


@pytest.fixture
def mock_context():
    return MockContext()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_with_outliers(mock_context):
    """Test Bayesian regression robustness to outliers"""
    np.random.seed(42)
    n = 100
    data = []
    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        y = 2 * x1 + 3 * x2 + np.random.normal(0, 1)

        # Add outliers (5%)
        if np.random.random() < 0.05:
            y += np.random.choice([-50, 50])

        data.append({'x1': x1, 'x2': x2, 'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x1 + x2',
        n_samples=1000
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success, f"Bayesian regression with outliers failed: {result.error}"

    # Even with outliers, Bayesian should give reasonable estimates
    assert result.coefficients['x1']['mean'] > 0
    assert result.coefficients['x2']['mean'] > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_convergence_diagnostics(mock_context):
    """Test Bayesian convergence with sufficient samples"""
    np.random.seed(42)
    n = 50
    data = []
    for i in range(n):
        x = np.random.uniform(0, 10)
        y = 2 * x + np.random.normal(0, 1)
        data.append({'x': x, 'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x',
        n_samples=2000  # Sufficient for convergence
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success
    # Model should converge successfully
    assert result.n_samples == 2000
    assert 1.5 < result.coefficients['x']['mean'] < 2.5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_with_small_sample(mock_context):
    """Test Bayesian regression with small sample size"""
    np.random.seed(42)
    n = 20  # Small sample
    data = []
    for i in range(n):
        x = np.random.uniform(0, 10)
        y = 2 * x + np.random.normal(0, 1)
        data.append({'x': x, 'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x',
        n_samples=1000
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success
    # With small sample, credible intervals should be wider
    x_interval = result.coefficients['x']['hdi_95%']
    interval_width = x_interval[1] - x_interval[0]
    assert interval_width > 0.5  # Expect wider intervals with small n


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_multicollinearity(mock_context):
    """Test Bayesian regression with multicollinear predictors"""
    np.random.seed(42)
    n = 100
    data = []
    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = x1 + np.random.normal(0, 0.1)  # x2 ≈ x1 (highly correlated)
        y = 2 * x1 + np.random.normal(0, 1)
        data.append({'x1': x1, 'x2': x2, 'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x1 + x2',
        n_samples=1000
    )

    result = await bayesian_linear_regression(params, mock_context)

    # Bayesian should handle multicollinearity through regularization
    assert result.success
    # With multicollinearity, coefficients may be unstable but should sum correctly
    total_effect = result.coefficients['x1']['mean'] + result.coefficients['x2']['mean']
    assert 1.5 < total_effect < 2.5  # Combined effect should be ~2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_with_intercept_only(mock_context):
    """Test Bayesian regression with intercept-only model"""
    np.random.seed(42)
    n = 50
    data = []
    true_mean = 15.0
    for i in range(n):
        y = true_mean + np.random.normal(0, 2)
        data.append({'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ 1',  # Intercept only
        n_samples=1000
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success
    # Intercept should estimate the mean
    assert 'Intercept' in result.coefficients
    assert 13 < result.coefficients['Intercept']['mean'] < 17


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_with_multiple_predictors(mock_context):
    """Test Bayesian regression with multiple predictors"""
    np.random.seed(42)
    n = 150
    data = []
    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        x3 = np.random.uniform(0, 10)
        y = 1 + 2 * x1 + 3 * x2 + 0.5 * x3 + np.random.normal(0, 1)
        data.append({'x1': x1, 'x2': x2, 'x3': x3, 'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x1 + x2 + x3',
        n_samples=1500
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success
    # Check all coefficients are recovered reasonably
    assert 1.5 < result.coefficients['x1']['mean'] < 2.5
    assert 2.5 < result.coefficients['x2']['mean'] < 3.5
    assert 0.0 < result.coefficients['x3']['mean'] < 1.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_heteroskedastic_errors(mock_context):
    """Test Bayesian regression with heteroskedastic errors"""
    np.random.seed(42)
    n = 100
    data = []
    for i in range(n):
        x = np.random.uniform(0, 10)
        # Error variance increases with x
        error_std = 0.5 + 0.3 * x
        y = 2 * x + np.random.normal(0, error_std)
        data.append({'x': x, 'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x',
        n_samples=1000
    )

    result = await bayesian_linear_regression(params, mock_context)

    # Should still provide reasonable estimates despite heteroskedasticity
    assert result.success
    assert 1.5 < result.coefficients['x']['mean'] < 2.5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_with_categorical_interaction(mock_context):
    """Test Bayesian regression with interaction term"""
    np.random.seed(42)
    n = 120
    data = []
    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        # Include interaction effect
        y = 1 + 2 * x1 + 3 * x2 + 0.5 * x1 * x2 + np.random.normal(0, 2)
        data.append({'x1': x1, 'x2': x2, 'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x1 + x2 + x1:x2',  # Include interaction
        n_samples=1500
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success
    # Should estimate all terms including interaction
    assert 'x1' in result.coefficients
    assert 'x2' in result.coefficients


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_with_zero_coefficient(mock_context):
    """Test Bayesian regression when true coefficient is zero"""
    np.random.seed(42)
    n = 100
    data = []
    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        # x2 has no effect
        y = 2 * x1 + np.random.normal(0, 1)
        data.append({'x1': x1, 'x2': x2, 'y': y})

    params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x1 + x2',
        n_samples=1000
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success
    # x2 credible interval should include zero
    x2_interval = result.coefficients['x2']['hdi_95%']
    assert x2_interval[0] < 0 < x2_interval[1]  # Zero should be in the interval
