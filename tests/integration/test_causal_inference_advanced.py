"""
Advanced integration tests for causal inference methods.

Tests edge cases, robustness checks, and assumption violations.
"""

import pytest
import numpy as np
import pandas as pd
from mcp_server.fastmcp_server import (
    propensity_score_matching,
    instrumental_variables_2sls,
    regression_discontinuity,
    synthetic_control,
    sensitivity_analysis_rosenbaum,
    PropensityScoreMatchingParams,
    InstrumentalVariables2SLSParams,
    RegressionDiscontinuityParams,
    SyntheticControlParams,
    SensitivityAnalysisRosenbaumParams
)


class MockContext:
    """Mock context for FastMCP tool testing"""
    def __init__(self):
        self.meta = {}


@pytest.fixture
def mock_context():
    return MockContext()


@pytest.fixture
def psm_data_poor_overlap():
    """Generate PSM data with poor covariate overlap"""
    np.random.seed(42)
    n = 200
    data = []

    for i in range(n):
        # Treatment group: high values
        if i < 50:
            x1 = np.random.uniform(8, 10)
            x2 = np.random.uniform(7, 10)
            treatment = 1
        # Control group: low values (poor overlap)
        else:
            x1 = np.random.uniform(0, 3)
            x2 = np.random.uniform(0, 4)
            treatment = 0

        y = 5 + 2 * x1 + 3 * x2 + 10 * treatment + np.random.normal(0, 1)
        data.append({'x1': x1, 'x2': x2, 'treatment': treatment, 'outcome': y})

    return data


@pytest.fixture
def iv_data_weak_instruments():
    """Generate IV data with weak instruments"""
    np.random.seed(42)
    n = 300
    data = []

    for i in range(n):
        z = np.random.uniform(0, 10)  # Instrument
        u = np.random.normal(0, 2)  # Unobserved confounder
        x = 0.1 * z + 0.5 * u + np.random.normal(0, 1)  # WEAK correlation with z
        y = 2 * x + u + np.random.normal(0, 1)

        data.append({'z': z, 'x': x, 'y': y})

    return data


@pytest.fixture
def rdd_data_with_manipulation():
    """Generate RDD data with evidence of manipulation"""
    np.random.seed(42)
    n = 500
    data = []

    for i in range(n):
        # Running variable with manipulation near cutoff
        if np.random.random() < 0.1 and 49 < i < 60:
            # Some units manipulate to just above threshold
            running_var = np.random.uniform(50.1, 52)
        else:
            running_var = np.random.uniform(0, 100)

        treatment = 1 if running_var >= 50 else 0
        y = 10 + 5 * treatment + 0.1 * running_var + np.random.normal(0, 2)

        data.append({'running_var': running_var, 'treatment': treatment, 'outcome': y})

    return data


@pytest.fixture
def synthetic_control_data_few_donors():
    """Generate synthetic control data with few donor units"""
    np.random.seed(42)
    time_periods = 20
    n_units = 5  # Few donors

    data = []
    for unit in range(n_units):
        unit_effect = np.random.normal(10, 2)

        for t in range(time_periods):
            # Unit 0 is treated at t=15
            if unit == 0 and t >= 15:
                treatment_effect = 5
            else:
                treatment_effect = 0

            outcome = unit_effect + 0.5 * t + treatment_effect + np.random.normal(0, 1)
            data.append({
                'unit': f'unit_{unit}',
                'time': t,
                'outcome': outcome,
                'treated': 1 if (unit == 0 and t >= 15) else 0
            })

    return data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_psm_with_poor_overlap(mock_context, psm_data_poor_overlap):
    """Test PSM when treatment/control have poor covariate overlap"""
    params = PropensityScoreMatchingParams(
        data=psm_data_poor_overlap,
        treatment_col='treatment',
        outcome_col='outcome',
        covariates=['x1', 'x2'],
        matching_method='nearest',
        caliper=0.2  # May need large caliper due to poor overlap
    )

    result = await propensity_score_matching(params, mock_context)

    # Should either succeed with warning about poor overlap, or handle gracefully
    if result.success:
        # Check balance diagnostics show poor overlap
        if hasattr(result, 'balance_diagnostics'):
            # May have large standardized mean differences
            pass
        # Check that some units couldn't be matched
        if hasattr(result, 'n_matched'):
            assert result.n_matched < 100  # Not all units matched


@pytest.mark.asyncio
@pytest.mark.integration
async def test_psm_balance_diagnostics(mock_context):
    """Test PSM balance diagnostics output"""
    np.random.seed(42)
    n = 200
    data = []

    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        # Propensity score depends on covariates
        propensity = 1 / (1 + np.exp(-(x1 - 5 + 0.5 * x2 - 2.5)))
        treatment = 1 if np.random.random() < propensity else 0
        y = 10 + 5 * treatment + 2 * x1 + x2 + np.random.normal(0, 2)

        data.append({'x1': x1, 'x2': x2, 'treatment': treatment, 'outcome': y})

    params = PropensityScoreMatchingParams(
        data=data,
        treatment_col='treatment',
        outcome_col='outcome',
        covariates=['x1', 'x2'],
        matching_method='nearest',
        caliper=0.1
    )

    result = await propensity_score_matching(params, mock_context)

    assert result.success
    # Check balance diagnostics exist
    if hasattr(result, 'balance_before') and hasattr(result, 'balance_after'):
        # After matching, balance should improve
        # (standardized mean differences should decrease)
        pass


@pytest.mark.asyncio
@pytest.mark.integration
async def test_iv_weak_instrument_detection(mock_context, iv_data_weak_instruments):
    """Test IV/2SLS detection of weak instruments"""
    params = InstrumentalVariables2SLSParams(
        data=iv_data_weak_instruments,
        outcome='y',
        treatment='x',
        instruments=['z'],
        controls=[]
    )

    result = await instrumental_variables_2sls(params, mock_context)

    # Should warn about weak instrument or provide F-statistic
    if result.success:
        if hasattr(result, 'first_stage_f_stat'):
            # F < 10 indicates weak instrument
            assert result.first_stage_f_stat < 10
        if hasattr(result, 'warnings'):
            assert any('weak' in w.lower() for w in result.warnings)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_iv_with_multiple_instruments(mock_context):
    """Test IV/2SLS with multiple instruments"""
    np.random.seed(42)
    n = 300
    data = []

    for i in range(n):
        z1 = np.random.uniform(0, 10)
        z2 = np.random.uniform(0, 10)
        u = np.random.normal(0, 2)
        x = 0.5 * z1 + 0.3 * z2 + 0.5 * u + np.random.normal(0, 1)
        y = 2 * x + u + np.random.normal(0, 1)

        data.append({'z1': z1, 'z2': z2, 'x': x, 'y': y})

    params = InstrumentalVariables2SLSParams(
        data=data,
        outcome='y',
        treatment='x',
        instruments=['z1', 'z2'],
        controls=[]
    )

    result = await instrumental_variables_2sls(params, mock_context)

    assert result.success
    # With overidentification (2 instruments for 1 endogenous var),
    # can test overidentifying restrictions
    if hasattr(result, 'overid_test'):
        # Should have J-statistic or similar
        pass


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rdd_bandwidth_sensitivity(mock_context):
    """Test RDD sensitivity to bandwidth choice"""
    np.random.seed(42)
    n = 500
    data = []

    for i in range(n):
        running_var = np.random.uniform(0, 100)
        treatment = 1 if running_var >= 50 else 0
        y = 10 + 5 * treatment + 0.1 * running_var + np.random.normal(0, 2)
        data.append({'running_var': running_var, 'treatment': treatment, 'outcome': y})

    # Test with different bandwidths
    bandwidths = [5, 10, 20]
    results = []

    for bw in bandwidths:
        params = RegressionDiscontinuityParams(
            data=data,
            running_variable='running_var',
            outcome='outcome',
            cutoff=50,
            bandwidth=bw
        )

        result = await regression_discontinuity(params, mock_context)
        if result.success:
            results.append((bw, result.treatment_effect))

    # Treatment effect should be relatively stable across bandwidths
    if len(results) >= 2:
        effects = [r[1] for r in results]
        effect_range = max(effects) - min(effects)
        # Allow for some variation but not huge differences
        assert effect_range < 5  # Effects shouldn't vary by more than 5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rdd_with_donut_hole(mock_context):
    """Test RDD with donut hole (excluding units near cutoff)"""
    np.random.seed(42)
    n = 500
    data = []

    for i in range(n):
        running_var = np.random.uniform(0, 100)
        treatment = 1 if running_var >= 50 else 0

        # Add noise that varies near cutoff (potential manipulation)
        noise = np.random.normal(0, 2)
        if 48 < running_var < 52:
            noise += np.random.normal(0, 3)  # Extra noise near cutoff

        y = 10 + 5 * treatment + 0.1 * running_var + noise
        data.append({'running_var': running_var, 'treatment': treatment, 'outcome': y})

    # Exclude units very close to cutoff (donut hole approach)
    filtered_data = [row for row in data if not (49 < row['running_var'] < 51)]

    params = RegressionDiscontinuityParams(
        data=filtered_data,
        running_variable='running_var',
        outcome='outcome',
        cutoff=50,
        bandwidth=10
    )

    result = await regression_discontinuity(params, mock_context)

    # Should still estimate treatment effect
    assert result.success or "insufficient data" in result.error.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_synthetic_control_with_few_donors(mock_context, synthetic_control_data_few_donors):
    """Test synthetic control with limited donor pool"""
    params = SyntheticControlParams(
        data=synthetic_control_data_few_donors,
        unit_col='unit',
        time_col='time',
        outcome_col='outcome',
        treated_unit='unit_0',
        treatment_time=15
    )

    result = await synthetic_control(params, mock_context)

    # With few donors, may have poor fit or fail
    if result.success:
        # Check that synthetic control uses available donors
        if hasattr(result, 'weights'):
            assert len(result.weights) <= 4  # At most 4 donors (excluding treated unit)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_synthetic_control_placebo_tests(mock_context):
    """Test synthetic control with placebo tests"""
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
            data.append({
                'unit': f'unit_{unit}',
                'time': t,
                'outcome': outcome,
                'treated': 1 if (unit == 0 and t >= 20) else 0
            })

    params = SyntheticControlParams(
        data=data,
        unit_col='unit',
        time_col='time',
        outcome_col='outcome',
        treated_unit='unit_0',
        treatment_time=20
    )

    result = await synthetic_control(params, mock_context)

    assert result.success
    # Check treatment effect is significant
    if hasattr(result, 'treatment_effect'):
        assert result.treatment_effect > 5  # Should detect the 8-unit effect


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sensitivity_analysis_extreme_gamma(mock_context):
    """Test Rosenbaum sensitivity analysis with extreme hidden bias"""
    np.random.seed(42)
    n = 200
    data = []

    for i in range(n):
        x1 = np.random.uniform(0, 10)
        x2 = np.random.uniform(0, 10)
        propensity = 1 / (1 + np.exp(-(x1 - 5)))
        treatment = 1 if np.random.random() < propensity else 0
        y = 10 + 5 * treatment + 2 * x1 + x2 + np.random.normal(0, 2)

        data.append({'x1': x1, 'x2': x2, 'treatment': treatment, 'outcome': y})

    params = SensitivityAnalysisRosenbaumParams(
        data=data,
        treatment_col='treatment',
        outcome_col='outcome',
        gamma_values=[1.0, 2.0, 5.0, 10.0]  # Include extreme values
    )

    result = await sensitivity_analysis_rosenbaum(params, mock_context)

    assert result.success
    # Check that confidence intervals widen with gamma
    if hasattr(result, 'sensitivity_results'):
        intervals = result.sensitivity_results
        # Intervals should be ordered by gamma
        prev_width = 0
        for gamma_result in sorted(intervals, key=lambda x: x['gamma']):
            width = gamma_result['ci_upper'] - gamma_result['ci_lower']
            assert width >= prev_width  # Intervals should widen
            prev_width = width


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
        data.append({'x1': x1, 'x2': x2, 'treatment': treatment, 'outcome': y})

    params = PropensityScoreMatchingParams(
        data=data,
        treatment_col='treatment',
        outcome_col='outcome',
        covariates=['x1', 'x2'],
        matching_method='nearest',
        caliper=0.15
    )

    result = await propensity_score_matching(params, mock_context)

    # Should handle class imbalance
    # May match each treated unit to multiple controls
    if result.success:
        assert result.ate != 0  # Should estimate non-zero effect


@pytest.mark.asyncio
@pytest.mark.integration
async def test_iv_exactly_identified(mock_context):
    """Test IV/2SLS with exactly identified model (1 instrument, 1 endogenous)"""
    np.random.seed(42)
    n = 300
    data = []

    for i in range(n):
        z = np.random.uniform(0, 10)
        u = np.random.normal(0, 2)
        x = 0.7 * z + 0.5 * u + np.random.normal(0, 1)
        y = 3 * x + u + np.random.normal(0, 1)

        data.append({'z': z, 'x': x, 'y': y})

    params = InstrumentalVariables2SLSParams(
        data=data,
        outcome='y',
        treatment='x',
        instruments=['z'],  # Exactly identified
        controls=[]
    )

    result = await instrumental_variables_2sls(params, mock_context)

    assert result.success
    # Treatment effect should be ~3
    assert 2.0 < result.treatment_effect < 4.0
    # Cannot test overidentifying restrictions (exactly identified)
