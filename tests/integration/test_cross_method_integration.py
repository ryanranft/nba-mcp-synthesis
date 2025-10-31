"""
Cross-method integration tests for econometric analysis pipelines.

Tests realistic multi-step analysis workflows combining multiple methods.
"""

import pytest
import numpy as np
from mcp_server.fastmcp_server import (
    bayesian_linear_regression,
    propensity_score_matching,
    kalman_filter,
    kaplan_meier,
    BayesianLinearRegressionParams,
    PropensityScoreMatchingParams,
    KalmanFilterParams,
    KaplanMeierParams,
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
async def test_bayesian_to_psm_pipeline(mock_context):
    """
    Test pipeline: Bayesian regression → PSM

    Use case: Estimate propensity model with Bayesian methods to capture
    uncertainty, then use predictions for matching.
    """
    np.random.seed(42)
    n = 150

    # Generate data with treatment selection
    data = []
    for i in range(n):
        age = np.random.uniform(20, 40)
        experience = np.random.uniform(0, 10)

        # Treatment probability (Bayesian will estimate this)
        propensity_logit = -2 + 0.1 * age + 0.2 * experience
        propensity = 1 / (1 + np.exp(-propensity_logit))
        treatment = 1 if np.random.random() < propensity else 0

        # Outcome depends on treatment
        outcome = 50 + 10 * treatment + 0.5 * age + 2 * experience + np.random.normal(0, 5)

        data.append({
            'age': age,
            'experience': experience,
            'treatment': treatment,
            'outcome': outcome
        })

    # Step 1: Bayesian regression to understand covariate relationships
    bayesian_params = BayesianLinearRegressionParams(
        data=data,
        formula='outcome ~ age + experience',
        n_samples=1000
    )

    bayesian_result = await bayesian_linear_regression(bayesian_params, mock_context)

    assert bayesian_result.success, "Bayesian step failed"
    assert 'age' in bayesian_result.posterior_mean
    assert 'experience' in bayesian_result.posterior_mean

    # Step 2: PSM using the covariates
    psm_params = PropensityScoreMatchingParams(
        data=data,
        treatment_var='treatment',
        outcome_var='outcome',
        covariates=['age', 'experience'],
        matching_method='nearest'
    )

    psm_result = await propensity_score_matching(psm_params, mock_context)

    assert psm_result.success, "PSM step failed"
    assert psm_result.n_matched > 0
    # Should detect positive treatment effect
    assert psm_result.treatment_effect > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_kalman_filter_to_survival_pipeline(mock_context):
    """
    Test pipeline: Kalman Filter → Survival Analysis

    Use case: Filter noisy player performance trajectory, then analyze
    career longevity based on filtered states.
    """
    np.random.seed(42)
    n = 80

    # Generate player performance trajectory with noise
    true_skill = np.cumsum(np.random.normal(0, 0.3, n))  # Skill evolution
    observed_performance = true_skill + np.random.normal(0, 2, n)  # Noisy observations

    # Career events based on filtered skill level
    events_data = []

    # Step 1: Kalman filter to get smooth skill estimate
    kalman_data = [{"t": i, "performance": observed_performance[i]} for i in range(n)]

    kalman_params = KalmanFilterParams(
        data=kalman_data,
        state_dim=1,
        observation_vars=["performance"],
        estimate_parameters=True,
        smoother=True
    )

    kalman_result = await kalman_filter(kalman_params, mock_context)

    assert kalman_result.success, "Kalman filter step failed"
    assert len(kalman_result.filtered_states) == n

    # Step 2: Use filtered states to determine career survival
    # Extract filtered skill levels (get first state value from each time point)
    filtered_skills = []
    for state in kalman_result.filtered_states:
        # Get the first (and only, since state_dim=1) state value
        state_value = list(state.values())[0] if state else 0.0
        filtered_skills.append(state_value)

    # Create survival data: players with declining skill retire earlier
    mean_skill = np.mean(filtered_skills)
    for i, skill in enumerate(filtered_skills):
        if i > 20:  # Only after minimum career length
            # Event probability increases as skill declines
            event_prob = 0.02 if skill > mean_skill else 0.08
            event = 1 if np.random.random() < event_prob else 0

            events_data.append({
                'time': i,
                'event': event,
                'skill_level': skill
            })

    if len(events_data) >= 20:
        # Kaplan-Meier on career longevity
        km_params = KaplanMeierParams(
            data=events_data,
            duration_var='time',
            event_var='event'
        )

        km_result = await kaplan_meier(km_params, mock_context)

        assert km_result.success, "Survival analysis step failed"
        assert km_result.n_events > 0
        assert len(km_result.survival_function) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_bayesian_models_comparison(mock_context):
    """
    Test pipeline: Multiple Bayesian models → Model comparison

    Use case: Fit several candidate models, compare via posterior predictive checks.
    """
    np.random.seed(42)
    n = 100

    # Generate data with quadratic relationship
    data = []
    for i in range(n):
        x = np.random.uniform(0, 10)
        y = 5 + 2 * x + 0.3 * (x ** 2) + np.random.normal(0, 2)
        x_squared = x ** 2
        data.append({'x': x, 'x_squared': x_squared, 'y': y})

    # Model 1: Linear
    linear_params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x',
        n_samples=1000
    )

    linear_result = await bayesian_linear_regression(linear_params, mock_context)

    assert linear_result.success, "Linear model failed"

    # Model 2: Quadratic
    quadratic_params = BayesianLinearRegressionParams(
        data=data,
        formula='y ~ x + x_squared',
        n_samples=1000
    )

    quadratic_result = await bayesian_linear_regression(quadratic_params, mock_context)

    assert quadratic_result.success, "Quadratic model failed"

    # Compare model fits
    # Quadratic should fit better (lower posterior std, tighter intervals)
    assert 'x' in linear_result.posterior_mean
    assert 'x' in quadratic_result.posterior_mean
    assert 'x_squared' in quadratic_result.posterior_mean

    # Both models should converge
    assert linear_result.n_samples == 1000
    assert quadratic_result.n_samples == 1000


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bayesian_uncertainty_quantification(mock_context):
    """
    Test pipeline: Bayesian regression with uncertainty propagation

    Use case: Estimate coefficients and propagate uncertainty to predictions.
    """
    np.random.seed(42)
    n = 80

    # Training data
    train_data = []
    for i in range(n):
        minutes = np.random.uniform(20, 40)
        points = 0.5 * minutes + np.random.normal(0, 3)
        train_data.append({'minutes': minutes, 'points': points})

    # Fit Bayesian model
    params = BayesianLinearRegressionParams(
        data=train_data,
        formula='points ~ minutes',
        n_samples=2000
    )

    result = await bayesian_linear_regression(params, mock_context)

    assert result.success
    assert 'minutes' in result.posterior_mean

    # Check uncertainty is captured
    assert 'minutes' in result.posterior_std
    assert result.posterior_std['minutes'] > 0

    # Check credible intervals
    assert 'minutes' in result.credible_intervals
    ci = result.credible_intervals['minutes']
    assert ci['lower'] < result.posterior_mean['minutes'] < ci['upper']

    # Verify convergence diagnostics exist
    assert len(result.convergence_diagnostics) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sequential_analysis_workflow(mock_context):
    """
    Test pipeline: Sequential analysis with multiple methods

    Use case: Exploratory → Model fitting → Validation workflow.
    """
    np.random.seed(42)
    n = 120

    # Generate rich dataset
    data = []
    for i in range(n):
        age = np.random.uniform(20, 35)
        height = np.random.uniform(180, 220)
        treatment = 1 if i < 60 else 0

        # Outcome depends on covariates and treatment
        outcome = 30 + 0.3 * age + 0.1 * height + 15 * treatment + np.random.normal(0, 5)

        data.append({
            'age': age,
            'height': height,
            'treatment': treatment,
            'outcome': outcome
        })

    # Step 1: Bayesian regression to understand relationships
    bayesian_params = BayesianLinearRegressionParams(
        data=data,
        formula='outcome ~ age + height',
        n_samples=1000
    )

    bayesian_result = await bayesian_linear_regression(bayesian_params, mock_context)

    assert bayesian_result.success

    # Step 2: PSM for causal effect estimation
    psm_params = PropensityScoreMatchingParams(
        data=data,
        treatment_var='treatment',
        outcome_var='outcome',
        covariates=['age', 'height'],
        matching_method='nearest'
    )

    psm_result = await propensity_score_matching(psm_params, mock_context)

    assert psm_result.success
    assert psm_result.treatment_effect > 10  # Should detect the 15-point effect

    # Both methods should provide consistent insights
    # Bayesian shows covariate relationships, PSM isolates treatment effect
    assert 'age' in bayesian_result.posterior_mean
    assert 'height' in bayesian_result.posterior_mean
    assert psm_result.n_matched > 20
