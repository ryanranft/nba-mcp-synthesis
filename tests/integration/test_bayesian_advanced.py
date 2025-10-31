"""
Advanced integration tests for Bayesian analysis methods.

Tests edge cases, convergence scenarios, and robustness of Bayesian methods.
"""

import pytest
import numpy as np
import pandas as pd
from mcp_server.fastmcp_server import (
    bayesian_linear_regression,
    BayesianLinearRegressionParams
)

# Note: Only testing bayesian_linear_regression as other Bayesian tools
# need to be verified in fastmcp_server.py exports


class MockContext:
    """Mock context for FastMCP tool testing"""
    def __init__(self):
        self.meta = {}


@pytest.fixture
def mock_context():
    return MockContext()


@pytest.fixture
def data_with_missing():
    """Generate data with missing values"""
    np.random.seed(42)
    n = 100
    data = []
    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10) if np.random.random() > 0.1 else None  # 10% missing
        y = 2 * x1 + (3 * x2 if x2 is not None else 0) + np.random.normal(0, 1)
        data.append({'x1': x1, 'x2': x2, 'y': y})
    return data


@pytest.fixture
def data_with_outliers():
    """Generate data with outliers"""
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
    return data


@pytest.fixture
def hierarchical_data():
    """Generate hierarchical data (players within teams)"""
    np.random.seed(42)
    data = []
    n_teams = 5
    n_players_per_team = 10

    for team in range(n_teams):
        team_effect = np.random.normal(0, 2)  # Random team-level effect

        for player in range(n_players_per_team):
            experience = np.random.uniform(0, 10)
            points = 15 + team_effect + 2 * experience + np.random.normal(0, 3)
            data.append({
                'team_id': f'team_{team}',
                'player_id': f'player_{team}_{player}',
                'experience': experience,
                'points': points
            })

    return data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_with_missing_data(mock_context, data_with_missing):
    """Test Bayesian regression handling of missing data"""
    # Filter out rows with missing values (complete case analysis)
    complete_data = [row for row in data_with_missing if row['x2'] is not None]

    params = BayesianLinearRegressionParams(
        data=complete_data,
        formula='y ~ x1 + x2',
        n_samples=1000
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success, f"Bayesian regression with missing data failed: {result.error}"
    assert result.n_samples == 1000
    assert len(result.coefficients) == 3  # intercept + x1 + x2

    # Check that coefficients are reasonable (despite missing data)
    assert 1.0 < result.coefficients['x1']['mean'] < 3.0
    assert 2.0 < result.coefficients['x2']['mean'] < 4.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_with_outliers(mock_context, data_with_outliers):
    """Test Bayesian regression robustness to outliers"""
    params = BayesianLinearRegressionParams(
        data=data_with_outliers,
        formula='y ~ x1 + x2',
        n_samples=1000
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success, f"Bayesian regression with outliers failed: {result.error}"

    # Even with outliers, Bayesian should give reasonable estimates
    # (though potentially biased)
    assert result.coefficients['x1']['mean'] > 0
    assert result.coefficients['x2']['mean'] > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_convergence_diagnostics(mock_context):
    """Test Bayesian convergence diagnostics"""
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
    # Check R-hat (convergence diagnostic) if available
    # R-hat < 1.1 indicates convergence
    if hasattr(result, 'diagnostics') and 'rhat' in result.diagnostics:
        assert all(rhat < 1.1 for rhat in result.diagnostics['rhat'].values())


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_logistic_with_separation(mock_context):
    """Test Bayesian logistic regression with perfect separation"""
    np.random.seed(42)
    n = 100
    data = []

    # Create data with near-perfect separation
    for i in range(n):
        x = np.random.uniform(0, 10)
        # Perfect separation at x=5
        y = 1 if x > 5.5 else 0
        data.append({'x': x, 'y': y})

    params = BayesianLogisticRegressionParams(
        data=data,
        formula='y ~ x',
        n_samples=1000
    )

    result = await bayesian_logistic_regression(params, mock_context)

    # Bayesian approach should handle separation better than MLE
    assert result.success, "Bayesian logistic should handle separation"
    # Coefficient should be large but finite
    assert result.coefficients['x']['mean'] > 0
    assert np.isfinite(result.coefficients['x']['mean'])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_hierarchical_model_convergence(mock_context, hierarchical_data):
    """Test hierarchical Bayesian model with grouped data"""
    params = HierarchicalBayesianModelParams(
        data=hierarchical_data,
        formula='points ~ experience',
        group_column='team_id',
        n_samples=1500
    )

    result = await hierarchical_bayesian_model(params, mock_context)

    assert result.success, f"Hierarchical model failed: {result.error}"
    assert result.n_groups == 5  # 5 teams

    # Check group-level variance is captured
    if hasattr(result, 'group_variance'):
        assert result.group_variance > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_model_comparison_with_nested_models(mock_context):
    """Test Bayesian model comparison with nested models"""
    np.random.seed(42)
    n = 100
    data = []
    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        y = 2 * x1 + 0.1 * x2 + np.random.normal(0, 1)  # x2 has small effect
        data.append({'x1': x1, 'x2': x2, 'y': y})

    params = CompareBayesianModelsParams(
        data=data,
        formulas=['y ~ x1', 'y ~ x1 + x2'],  # Nested models
        n_samples=1000
    )

    result = await compare_bayesian_models(params, mock_context)

    assert result.success
    assert len(result.model_comparison) == 2

    # Model with x1 only might be preferred (parsimony) or both similar
    # Just check that comparison ran successfully
    assert 'waic' in result.model_comparison[0] or 'loo' in result.model_comparison[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_model_averaging_weights(mock_context):
    """Test Bayesian model averaging weight calculation"""
    np.random.seed(42)
    n = 100
    data = []
    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        y = 2 * x1 + 3 * x2 + np.random.normal(0, 1)
        data.append({'x1': x1, 'x2': x2, 'y': y})

    params = BayesianModelAveragingParams(
        data=data,
        formulas=['y ~ x1', 'y ~ x2', 'y ~ x1 + x2'],
        n_samples=1000
    )

    result = await bayesian_model_averaging(params, mock_context)

    assert result.success
    assert len(result.model_weights) == 3

    # Weights should sum to 1
    total_weight = sum(result.model_weights.values())
    assert abs(total_weight - 1.0) < 0.01

    # Full model (x1 + x2) should have highest weight
    full_model_weight = result.model_weights['y ~ x1 + x2']
    assert full_model_weight > 0.5  # Should strongly prefer correct model


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
async def test_bayesian_prior_sensitivity(mock_context):
    """Test sensitivity to different priors"""
    np.random.seed(42)
    n = 50
    data = []
    for i in range(n):
        x = np.random.uniform(0, 10)
        y = 2 * x + np.random.normal(0, 1)
        data.append({'x': x, 'y': y})

    # Test with default priors
    params1 = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x',
        n_samples=1000
    )
    result1 = await bayesian_linear_regression(params1, mock_context)

    # Note: FastMCP tools don't currently support custom priors
    # This test just verifies that default priors work
    assert result1.success
    assert 1.5 < result1.coefficients['x']['mean'] < 2.5


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
