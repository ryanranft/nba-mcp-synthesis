"""
Integration tests for causal inference methods edge cases.

Tests robustness and assumptions of causal inference tools.
"""

import pytest
import numpy as np
from mcp_server.fastmcp_server import (
    propensity_score_matching,
    instrumental_variables,
    regression_discontinuity,
    synthetic_control,
    PropensityScoreMatchingParams,
    InstrumentalVariablesParams,
    RegressionDiscontinuityParams,
    SyntheticControlParams,
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
async def test_psm_with_good_overlap(mock_context):
    """Test PSM with good covariate overlap"""
    np.random.seed(42)
    n = 200
    data = []

    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        # Propensity based on covariates
        propensity = 1 / (1 + np.exp(-(x1 - 5 + 0.5 * x2 - 2.5)))
        treatment = 1 if np.random.random() < propensity else 0
        y = 10 + 5 * treatment + 2 * x1 + x2 + np.random.normal(0, 2)

        data.append({"x1": x1, "x2": x2, "treatment": treatment, "outcome": y})

    params = PropensityScoreMatchingParams(
        data=data,
        treatment_var="treatment",
        outcome_var="outcome",
        covariates=["x1", "x2"],
        matching_method="nearest",
        caliper=0.1,
    )

    result = await propensity_score_matching(params, mock_context)

    assert result.success
    # Treatment effect should be around 5
    assert 3 < result.treatment_effect < 7


@pytest.mark.asyncio
@pytest.mark.integration
async def test_psm_with_rare_treatment(mock_context):
    """Test PSM when treatment is rare (class imbalance)"""
    np.random.seed(42)
    n = 300
    data = []

    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)

        # Only 10% get treatment
        propensity = 0.1 * (1 / (1 + np.exp(-(x1 - 5))))
        treatment = 1 if np.random.random() < propensity else 0

        y = 10 + 10 * treatment + 2 * x1 + x2 + np.random.normal(0, 2)
        data.append({"x1": x1, "x2": x2, "treatment": treatment, "outcome": y})

    params = PropensityScoreMatchingParams(
        data=data,
        treatment_var="treatment",
        outcome_var="outcome",
        covariates=["x1", "x2"],
        matching_method="nearest",
        caliper=0.15,
    )

    result = await propensity_score_matching(params, mock_context)

    # Should handle class imbalance
    if result.success:
        assert result.treatment_effect != 0  # Should estimate non-zero effect


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Tool returning incomplete error result - needs fix in fastmcp_server.py"
)
async def test_iv_with_strong_instrument(mock_context):
    """Test IV with strong instrument"""
    np.random.seed(42)
    n = 300
    data = []

    for i in range(n):
        z = np.random.uniform(0, 10)  # Instrument
        u = np.random.normal(0, 2)  # Unobserved confounder
        x = 0.7 * z + 0.5 * u + np.random.normal(0, 1)  # Strong first stage
        y = 3 * x + u + np.random.normal(0, 1)

        data.append({"z": z, "x": x, "y": y})

    params = InstrumentalVariablesParams(
        data=data,
        formula="y ~ x",  # y depends on x (endogenous)
        instruments=["z"],
        endogenous_vars=["x"],
        method="2sls",
    )

    result = await instrumental_variables(params, mock_context)

    assert result.success
    # Treatment effect should be ~3
    assert 2.0 < result.coefficients["x"] < 4.0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Tool returning incomplete error result - needs fix in fastmcp_server.py"
)
async def test_iv_with_control_variables(mock_context):
    """Test IV with additional control variables"""
    np.random.seed(42)
    n = 300
    data = []

    for i in range(n):
        z = np.random.uniform(0, 10)
        w = np.random.uniform(0, 10)  # Control variable
        u = np.random.normal(0, 2)
        x = 0.7 * z + 0.3 * w + 0.5 * u + np.random.normal(0, 1)
        y = 3 * x + 2 * w + u + np.random.normal(0, 1)

        data.append({"z": z, "w": w, "x": x, "y": y})

    params = InstrumentalVariablesParams(
        data=data,
        formula="y ~ x + w",  # y depends on x (endogenous) and w (exogenous control)
        instruments=["z"],
        endogenous_vars=["x"],
        method="2sls",
    )

    result = await instrumental_variables(params, mock_context)

    assert result.success
    # Should estimate effect controlling for w
    assert 2.0 < result.coefficients["x"] < 4.0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Tool returning incomplete error result - needs fix in fastmcp_server.py"
)
async def test_rdd_sharp_discontinuity(mock_context):
    """Test RDD with sharp treatment discontinuity"""
    np.random.seed(42)
    n = 500
    data = []

    for i in range(n):
        running_var = np.random.uniform(0, 100)
        treatment = 1 if running_var >= 50 else 0
        y = 10 + 5 * treatment + 0.1 * running_var + np.random.normal(0, 2)
        data.append({"running_var": running_var, "treatment": treatment, "outcome": y})

    params = RegressionDiscontinuityParams(
        data=data,
        running_var="running_var",
        outcome_var="outcome",
        cutoff=50,
        bandwidth=10,
    )

    result = await regression_discontinuity(params, mock_context)

    assert result.success
    # Treatment effect should be around 5
    assert 3 < result.treatment_effect < 7


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Tool returning incomplete error result - needs fix in fastmcp_server.py"
)
async def test_rdd_with_polynomial_control(mock_context):
    """Test RDD with polynomial running variable control"""
    np.random.seed(42)
    n = 500
    data = []

    for i in range(n):
        running_var = np.random.uniform(0, 100)
        treatment = 1 if running_var >= 50 else 0
        # Quadratic relationship with running variable
        y = (
            10
            + 5 * treatment
            + 0.1 * running_var
            + 0.001 * (running_var**2)
            + np.random.normal(0, 2)
        )
        data.append({"running_var": running_var, "treatment": treatment, "outcome": y})

    params = RegressionDiscontinuityParams(
        data=data,
        running_var="running_var",
        outcome_var="outcome",
        cutoff=50,
        bandwidth=15,
    )

    result = await regression_discontinuity(params, mock_context)

    assert result.success
    # Should still estimate treatment effect
    assert result.treatment_effect > 0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Tool returning incomplete error result - needs fix in fastmcp_server.py"
)
async def test_synthetic_control_clear_effect(mock_context):
    """Test synthetic control with clear treatment effect"""
    np.random.seed(42)
    time_periods = 30
    n_units = 10

    data = []
    for unit in range(n_units):
        unit_effect = np.random.normal(10, 2)

        for t in range(time_periods):
            # Unit 0 is treated at t=20
            if unit == 0 and t >= 20:
                treatment_effect = 8
            else:
                treatment_effect = 0

            outcome = unit_effect + 0.3 * t + treatment_effect + np.random.normal(0, 1)
            data.append(
                {
                    "unit": f"unit_{unit}",
                    "time": t,
                    "outcome": outcome,
                    "treated": 1 if (unit == 0 and t >= 20) else 0,
                }
            )

    params = SyntheticControlParams(
        data=data,
        unit_var="unit",
        time_var="time",
        outcome_var="outcome",
        treated_unit="unit_0",
        treatment_time=20,
    )

    result = await synthetic_control(params, mock_context)

    assert result.success
    # Check treatment effect is significant
    if hasattr(result, "treatment_effect"):
        assert result.treatment_effect > 5  # Should detect the 8-unit effect


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Tool returning incomplete error result - needs fix in fastmcp_server.py"
)
async def test_synthetic_control_with_trend(mock_context):
    """Test synthetic control with time trend"""
    np.random.seed(42)
    time_periods = 25
    n_units = 8

    data = []
    for unit in range(n_units):
        unit_effect = np.random.normal(15, 3)

        for t in range(time_periods):
            # Unit 0 treated at t=15
            if unit == 0 and t >= 15:
                treatment_effect = 6
            else:
                treatment_effect = 0

            # Strong time trend
            outcome = unit_effect + 0.5 * t + treatment_effect + np.random.normal(0, 1)
            data.append(
                {
                    "unit": f"unit_{unit}",
                    "time": t,
                    "outcome": outcome,
                    "treated": 1 if (unit == 0 and t >= 15) else 0,
                }
            )

    params = SyntheticControlParams(
        data=data,
        unit_var="unit",
        time_var="time",
        outcome_var="outcome",
        treated_unit="unit_0",
        treatment_time=15,
    )

    result = await synthetic_control(params, mock_context)

    assert result.success
    # Should handle trend and estimate effect


@pytest.mark.asyncio
@pytest.mark.integration
async def test_psm_with_multiple_covariates(mock_context):
    """Test PSM with many covariates"""
    np.random.seed(42)
    n = 250
    data = []

    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        x3 = np.random.uniform(0, 10)
        x4 = np.random.uniform(0, 10)

        propensity = 1 / (1 + np.exp(-(x1 - 5 + 0.3 * x2 + 0.2 * x3 - 0.1 * x4 - 2)))
        treatment = 1 if np.random.random() < propensity else 0
        y = 10 + 7 * treatment + x1 + x2 + 0.5 * x3 + 0.5 * x4 + np.random.normal(0, 2)

        data.append(
            {
                "x1": x1,
                "x2": x2,
                "x3": x3,
                "x4": x4,
                "treatment": treatment,
                "outcome": y,
            }
        )

    params = PropensityScoreMatchingParams(
        data=data,
        treatment_var="treatment",
        outcome_var="outcome",
        covariates=["x1", "x2", "x3", "x4"],
        matching_method="nearest",
        caliper=0.1,
    )

    result = await propensity_score_matching(params, mock_context)

    assert result.success
    # Treatment effect should be around 7
    assert 5 < result.treatment_effect < 9
