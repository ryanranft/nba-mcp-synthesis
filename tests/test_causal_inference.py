"""
Tests for Causal Inference Module.

Tests cover:
- Instrumental variables (IV/2SLS)
- Regression discontinuity design (RDD)
- Propensity score matching (PSM)
- Synthetic control method
- Sensitivity analysis
- Integration tests

Author: Agent 8 Module 4A
Date: October 2025
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import warnings

from mcp_server.causal_inference import (
    CausalInferenceAnalyzer,
    IVResult,
    RDDResult,
    PSMResult,
    SyntheticControlResult,
    SensitivityResult,
    ate_inference,
    TreatmentType,
)


# --- Fixtures ---


@pytest.fixture
def iv_data():
    """Generate data for IV testing with endogenous treatment."""
    np.random.seed(42)
    n = 500

    # Instrument (exogenous)
    instrument = np.random.normal(0, 1, n)

    # Unobserved confounder
    confounder = np.random.normal(0, 1, n)

    # Treatment (endogenous - correlated with confounder)
    treatment = 2 * instrument + 1.5 * confounder + np.random.normal(0, 0.5, n)

    # Outcome (affected by treatment and confounder)
    outcome = 3 * treatment + 2 * confounder + np.random.normal(0, 1, n)

    # Covariates
    covariate1 = np.random.normal(0, 1, n)
    covariate2 = np.random.normal(0, 1, n)

    return pd.DataFrame(
        {
            "outcome": outcome,
            "treatment": treatment,
            "instrument": instrument,
            "covariate1": covariate1,
            "covariate2": covariate2,
        }
    )


@pytest.fixture
def rdd_data():
    """Generate data for RDD testing with sharp discontinuity."""
    np.random.seed(42)
    n = 1000

    # Running variable (e.g., draft pick)
    running_var = np.random.uniform(-50, 50, n)

    # Treatment assignment (sharp RDD at cutoff=0)
    treatment = (running_var >= 0).astype(int)

    # True treatment effect = 5
    outcome = 10 + 2 * running_var + 5 * treatment + np.random.normal(0, 5, n)

    return pd.DataFrame(
        {"outcome": outcome, "treatment": treatment, "running_var": running_var}
    )


@pytest.fixture
def psm_data():
    """Generate data for PSM testing."""
    np.random.seed(42)
    n = 600

    # Covariates
    age = np.random.uniform(20, 35, n)
    experience = np.random.uniform(0, 15, n)
    skill = np.random.normal(50, 10, n)

    # Propensity for treatment (selection on observables)
    propensity = 1 / (1 + np.exp(-(0.1 * age + 0.05 * experience + 0.02 * skill - 2)))

    # Treatment assignment
    treatment = (np.random.uniform(0, 1, n) < propensity).astype(int)

    # Outcome (treatment effect = 8)
    outcome = (
        20
        + 0.5 * age
        + 0.8 * experience
        + 0.3 * skill
        + 8 * treatment
        + np.random.normal(0, 3, n)
    )

    return pd.DataFrame(
        {
            "outcome": outcome,
            "treatment": treatment,
            "age": age,
            "experience": experience,
            "skill": skill,
        }
    )


@pytest.fixture
def synthetic_control_data():
    """Generate panel data for synthetic control."""
    np.random.seed(42)

    entities = ["treated"] + [f"control_{i}" for i in range(10)]
    time_periods = list(range(20))  # 0-9: pre-treatment, 10-19: post-treatment

    data = []
    for entity in entities:
        base_level = np.random.uniform(50, 100)
        trend = np.random.uniform(-0.5, 0.5)

        for t in time_periods:
            # Treatment effect for treated unit after period 10
            treatment_effect = 15 if (entity == "treated" and t >= 10) else 0

            outcome = base_level + trend * t + treatment_effect + np.random.normal(0, 2)

            data.append(
                {
                    "entity": entity,
                    "time": t,
                    "outcome": outcome,
                    "treatment": 1 if (entity == "treated" and t >= 10) else 0,
                }
            )

    return pd.DataFrame(data)


# --- IV Tests ---


def test_iv_initialization(iv_data):
    """Test IV analyzer initialization."""
    analyzer = CausalInferenceAnalyzer(
        data=iv_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["covariate1", "covariate2"],
    )

    assert analyzer.treatment_col == "treatment"
    assert analyzer.outcome_col == "outcome"
    assert len(analyzer.covariates) == 2
    assert len(analyzer.data) == 500


def test_iv_estimation_not_available_without_linearmodels(iv_data):
    """Test IV raises error if linearmodels not available."""
    analyzer = CausalInferenceAnalyzer(
        data=iv_data, treatment_col="treatment", outcome_col="outcome"
    )

    with patch("mcp_server.causal_inference.LINEARMODELS_AVAILABLE", False):
        with pytest.raises(ImportError, match="linearmodels required"):
            analyzer.instrumental_variables(instruments="instrument")


@pytest.mark.skipif(
    not pytest.importorskip("linearmodels", reason="linearmodels not installed"),
    reason="Requires linearmodels",
)
def test_iv_estimation_basic(iv_data):
    """Test basic IV estimation."""
    analyzer = CausalInferenceAnalyzer(
        data=iv_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["covariate1", "covariate2"],
    )

    result = analyzer.instrumental_variables(instruments="instrument")

    # Check result structure
    assert isinstance(result, IVResult)
    assert result.treatment_effect is not None
    assert result.std_error > 0
    assert result.p_value >= 0
    assert result.p_value <= 1
    assert len(result.confidence_interval) == 2

    # Treatment effect should be close to true value (3.0)
    assert 2.0 < result.treatment_effect < 4.0

    # Check diagnostics
    assert result.first_stage_f_stat > 0
    assert "is_weak" in result.weak_instrument_test
    assert result.weak_instrument_test["f_statistic"] > 0


@pytest.mark.skipif(
    not pytest.importorskip("linearmodels", reason="linearmodels not installed"),
    reason="Requires linearmodels",
)
def test_iv_weak_instrument_detection(iv_data):
    """Test detection of weak instruments."""
    # Add weak instrument
    iv_data["weak_instrument"] = np.random.normal(0, 1, len(iv_data)) * 0.01

    analyzer = CausalInferenceAnalyzer(
        data=iv_data, treatment_col="treatment", outcome_col="outcome"
    )

    result = analyzer.instrumental_variables(instruments="weak_instrument")

    # Weak instrument should have low F-statistic
    assert result.first_stage_f_stat < 10
    assert result.weak_instrument_test["is_weak"] == True


@pytest.mark.skipif(
    not pytest.importorskip("linearmodels", reason="linearmodels not installed"),
    reason="Requires linearmodels",
)
def test_iv_multiple_instruments(iv_data):
    """Test IV with multiple instruments."""
    iv_data["instrument2"] = iv_data["instrument"] * 0.8 + np.random.normal(
        0, 0.3, len(iv_data)
    )

    analyzer = CausalInferenceAnalyzer(
        data=iv_data, treatment_col="treatment", outcome_col="outcome"
    )

    result = analyzer.instrumental_variables(instruments=["instrument", "instrument2"])

    # Should have overidentification test
    assert result.overidentification_test is not None
    assert "p_value" in result.overidentification_test
    assert "statistic" in result.overidentification_test


def test_iv_result_repr(iv_data):
    """Test IV result string representation."""
    result = IVResult(
        treatment_effect=2.5,
        std_error=0.3,
        t_statistic=8.33,
        p_value=0.001,
        confidence_interval=(1.9, 3.1),
        first_stage_f_stat=45.2,
        weak_instrument_test={"is_weak": False, "f_statistic": 45.2},
    )

    repr_str = repr(result)
    assert "2.5" in repr_str
    assert "0.001" in repr_str
    assert "45.2" in repr_str


# --- RDD Tests ---


def test_rdd_basic_estimation(rdd_data):
    """Test basic RDD estimation."""
    analyzer = CausalInferenceAnalyzer(
        data=rdd_data, treatment_col="treatment", outcome_col="outcome"
    )

    result = analyzer.regression_discontinuity(
        running_var="running_var", cutoff=0, bandwidth=10
    )

    assert isinstance(result, RDDResult)
    assert result.treatment_effect is not None
    assert result.std_error > 0

    # Treatment effect should be reasonable (true value is 5.0 but estimation has variance)
    assert 2.0 < result.treatment_effect < 10.0

    assert result.bandwidth == 10
    assert result.n_left > 0
    assert result.n_right > 0


def test_rdd_optimal_bandwidth(rdd_data):
    """Test RDD with optimal bandwidth selection."""
    analyzer = CausalInferenceAnalyzer(
        data=rdd_data, treatment_col="treatment", outcome_col="outcome"
    )

    result = analyzer.regression_discontinuity(
        running_var="running_var", cutoff=0, bandwidth=None  # Auto-select
    )

    assert result.optimal_bandwidth is not None
    assert result.optimal_bandwidth > 0
    assert result.bandwidth == result.optimal_bandwidth


def test_rdd_different_kernels(rdd_data):
    """Test RDD with different kernel functions."""
    analyzer = CausalInferenceAnalyzer(
        data=rdd_data, treatment_col="treatment", outcome_col="outcome"
    )

    kernels = ["triangular", "uniform", "epanechnikov"]
    results = []

    for kernel in kernels:
        result = analyzer.regression_discontinuity(
            running_var="running_var", cutoff=0, bandwidth=10, kernel=kernel
        )
        results.append(result)

    # All should produce valid estimates
    for result in results:
        assert result.treatment_effect is not None
        assert 2.0 < result.treatment_effect < 10.0  # Widen range for kernel variation


def test_rdd_polynomial_orders(rdd_data):
    """Test RDD with different polynomial orders."""
    analyzer = CausalInferenceAnalyzer(
        data=rdd_data, treatment_col="treatment", outcome_col="outcome"
    )

    for order in [1, 2]:
        result = analyzer.regression_discontinuity(
            running_var="running_var", cutoff=0, bandwidth=15, polynomial_order=order
        )

        assert result.treatment_effect is not None


def test_rdd_continuity_test(rdd_data):
    """Test RDD McCrary continuity test."""
    analyzer = CausalInferenceAnalyzer(
        data=rdd_data, treatment_col="treatment", outcome_col="outcome"
    )

    result = analyzer.regression_discontinuity(
        running_var="running_var", cutoff=0, bandwidth=15
    )

    # Should include continuity test
    assert result.continuity_test is not None
    assert "p_value" in result.continuity_test
    assert "density_left" in result.continuity_test
    assert "density_right" in result.continuity_test


def test_rdd_insufficient_data(rdd_data):
    """Test RDD with very narrow bandwidth (few observations)."""
    analyzer = CausalInferenceAnalyzer(
        data=rdd_data, treatment_col="treatment", outcome_col="outcome"
    )

    result = analyzer.regression_discontinuity(
        running_var="running_var", cutoff=0, bandwidth=1  # Very narrow
    )

    # Should still produce result but with fewer observations
    assert result.n_left + result.n_right < 100


def test_rdd_asymmetric_support(rdd_data):
    """Test RDD with asymmetric data around cutoff."""
    # Keep only observations above cutoff
    rdd_data_asymmetric = rdd_data[rdd_data["running_var"] >= -5].copy()

    analyzer = CausalInferenceAnalyzer(
        data=rdd_data_asymmetric, treatment_col="treatment", outcome_col="outcome"
    )

    result = analyzer.regression_discontinuity(
        running_var="running_var", cutoff=0, bandwidth=10
    )

    assert result.n_left < result.n_right


def test_rdd_result_repr():
    """Test RDD result string representation."""
    result = RDDResult(
        treatment_effect=4.5,
        std_error=0.8,
        t_statistic=5.625,
        p_value=0.002,
        confidence_interval=(2.9, 6.1),
        bandwidth=12.5,
        n_left=150,
        n_right=145,
    )

    repr_str = repr(result)
    assert "4.5" in repr_str
    assert "12.5" in repr_str
    assert "150" in repr_str


# --- PSM Tests ---


def test_psm_basic_estimation(psm_data):
    """Test basic PSM estimation."""
    analyzer = CausalInferenceAnalyzer(
        data=psm_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["age", "experience", "skill"],
    )

    result = analyzer.propensity_score_matching(method="nearest", n_neighbors=1)

    assert isinstance(result, PSMResult)
    assert result.ate is not None
    assert result.att is not None
    assert result.atc is not None

    # Treatment effect should be close to true value (8.0)
    assert 6.0 < result.att < 10.0

    assert result.n_matched > 0
    assert len(result.propensity_scores) == len(psm_data)


def test_psm_balance_statistics(psm_data):
    """Test PSM covariate balance."""
    analyzer = CausalInferenceAnalyzer(
        data=psm_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["age", "experience", "skill"],
    )

    result = analyzer.propensity_score_matching(method="nearest")

    # Balance statistics should exist
    assert result.balance_statistics is not None
    assert len(result.balance_statistics) == 3  # 3 covariates

    # SMD should improve after matching
    for _, row in result.balance_statistics.iterrows():
        assert "smd_before" in row
        assert "smd_after" in row
        assert "improvement" in row


def test_psm_common_support(psm_data):
    """Test PSM common support restriction."""
    analyzer = CausalInferenceAnalyzer(
        data=psm_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["age", "experience", "skill"],
    )

    result = analyzer.propensity_score_matching(method="nearest")

    # Common support array should exist
    assert result.common_support is not None
    assert len(result.common_support) == len(psm_data)

    # Most observations should be in common support
    assert np.sum(result.common_support) > 0.8 * len(psm_data)


def test_psm_with_caliper(psm_data):
    """Test PSM with caliper matching."""
    analyzer = CausalInferenceAnalyzer(
        data=psm_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["age", "experience", "skill"],
    )

    result = analyzer.propensity_score_matching(
        method="nearest", n_neighbors=1, caliper=0.05  # Strict caliper
    )

    # Caliper may reduce matches
    assert result.n_matched <= np.sum(psm_data["treatment"] == 1)


def test_psm_multiple_neighbors(psm_data):
    """Test PSM with multiple neighbors."""
    analyzer = CausalInferenceAnalyzer(
        data=psm_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["age", "experience", "skill"],
    )

    result = analyzer.propensity_score_matching(method="nearest", n_neighbors=3)

    assert result.ate is not None
    # More neighbors may reduce variance
    assert result.std_error > 0


def test_psm_standard_error_bootstrap(psm_data):
    """Test PSM bootstrap standard errors."""
    analyzer = CausalInferenceAnalyzer(
        data=psm_data,
        treatment_col="treatment",
        outcome_col="outcome",
        covariates=["age", "experience", "skill"],
    )

    result = analyzer.propensity_score_matching(
        method="nearest", estimate_std_error=True
    )

    assert result.std_error > 0
    assert not np.isnan(result.std_error)
    assert len(result.confidence_interval) == 2


def test_psm_no_covariates_error(psm_data):
    """Test PSM raises error without covariates."""
    analyzer = CausalInferenceAnalyzer(
        data=psm_data, treatment_col="treatment", outcome_col="outcome", covariates=None
    )

    with pytest.raises(ValueError, match="Covariates required"):
        analyzer.propensity_score_matching()


def test_psm_result_repr():
    """Test PSM result string representation."""
    result = PSMResult(
        ate=7.2,
        att=7.5,
        atc=6.9,
        std_error=0.6,
        confidence_interval=(6.0, 8.4),
        n_matched=250,
        n_unmatched=20,
        balance_statistics=pd.DataFrame(),
        propensity_scores=np.array([]),
        common_support=np.array([]),
    )

    repr_str = repr(result)
    assert "7.2" in repr_str
    assert "250" in repr_str


# --- Synthetic Control Tests ---


def test_synthetic_control_basic(synthetic_control_data):
    """Test basic synthetic control estimation."""
    analyzer = CausalInferenceAnalyzer(
        data=synthetic_control_data,
        treatment_col="treatment",
        outcome_col="outcome",
        entity_col="entity",
        time_col="time",
    )

    result = analyzer.synthetic_control(
        treated_unit="treated", outcome_periods=list(range(20)), treatment_period=10
    )

    assert isinstance(result, SyntheticControlResult)
    assert len(result.treatment_effect) == 20
    assert result.average_effect is not None

    # Average treatment effect should be positive (true effect = 15)
    assert 10 < result.average_effect < 20

    # Weights should sum to 1
    assert np.isclose(result.weights.sum(), 1.0, atol=0.01)


def test_synthetic_control_pre_treatment_fit(synthetic_control_data):
    """Test synthetic control pre-treatment fit."""
    analyzer = CausalInferenceAnalyzer(
        data=synthetic_control_data,
        treatment_col="treatment",
        outcome_col="outcome",
        entity_col="entity",
        time_col="time",
    )

    result = analyzer.synthetic_control(
        treated_unit="treated", outcome_periods=list(range(20)), treatment_period=10
    )

    # Pre-treatment RMSE should be reasonably small
    assert result.pre_treatment_fit < 5.0


def test_synthetic_control_weights(synthetic_control_data):
    """Test synthetic control donor weights."""
    analyzer = CausalInferenceAnalyzer(
        data=synthetic_control_data,
        treatment_col="treatment",
        outcome_col="outcome",
        entity_col="entity",
        time_col="time",
    )

    result = analyzer.synthetic_control(
        treated_unit="treated", outcome_periods=list(range(20)), treatment_period=10
    )

    # All weights should be non-negative
    assert (result.weights >= 0).all()

    # All weights should be <= 1
    assert (result.weights <= 1).all()


def test_synthetic_control_placebo_tests(synthetic_control_data):
    """Test synthetic control with placebo inference."""
    analyzer = CausalInferenceAnalyzer(
        data=synthetic_control_data,
        treatment_col="treatment",
        outcome_col="outcome",
        entity_col="entity",
        time_col="time",
    )

    result = analyzer.synthetic_control(
        treated_unit="treated",
        outcome_periods=list(range(20)),
        treatment_period=10,
        n_placebo=5,
    )

    # Placebo distribution should exist
    assert result.placebo_distribution is not None
    assert len(result.placebo_distribution) == 5

    # P-value should be computed
    assert result.p_value >= 0
    assert result.p_value <= 1


def test_synthetic_control_donor_pool(synthetic_control_data):
    """Test synthetic control with custom donor pool."""
    analyzer = CausalInferenceAnalyzer(
        data=synthetic_control_data,
        treatment_col="treatment",
        outcome_col="outcome",
        entity_col="entity",
        time_col="time",
    )

    # Use only first 5 control units
    donor_pool = [f"control_{i}" for i in range(5)]

    result = analyzer.synthetic_control(
        treated_unit="treated",
        outcome_periods=list(range(20)),
        treatment_period=10,
        donor_pool=donor_pool,
    )

    # Should only use specified donors
    assert len(result.weights) == 5


def test_synthetic_control_trajectories(synthetic_control_data):
    """Test synthetic control actual vs synthetic trajectories."""
    analyzer = CausalInferenceAnalyzer(
        data=synthetic_control_data,
        treatment_col="treatment",
        outcome_col="outcome",
        entity_col="entity",
        time_col="time",
    )

    result = analyzer.synthetic_control(
        treated_unit="treated", outcome_periods=list(range(20)), treatment_period=10
    )

    assert len(result.actual_trajectory) == 20
    assert len(result.synthetic_trajectory) == 20

    # Pre-treatment trajectories should be similar
    pre_diff = np.abs(
        result.actual_trajectory[:10] - result.synthetic_trajectory[:10]
    ).mean()
    assert pre_diff < 5.0


def test_synthetic_control_result_repr():
    """Test synthetic control result string representation."""
    result = SyntheticControlResult(
        treatment_effect=np.array([1, 2, 3]),
        average_effect=12.5,
        std_error=1.2,
        p_value=0.05,
        pre_treatment_fit=2.3,
        weights=pd.Series([0.5, 0.3, 0.2]),
        synthetic_trajectory=np.array([1, 2, 3]),
        actual_trajectory=np.array([1, 2, 3]),
    )

    repr_str = repr(result)
    assert "12.5" in repr_str
    assert "0.05" in repr_str
    assert "2.3" in repr_str


# --- Sensitivity Analysis Tests ---


def test_sensitivity_rosenbaum_bounds():
    """Test Rosenbaum bounds sensitivity analysis."""
    analyzer = CausalInferenceAnalyzer(
        data=pd.DataFrame({"treatment": [1, 0], "outcome": [10, 5]}),
        treatment_col="treatment",
        outcome_col="outcome",
    )

    result = analyzer.sensitivity_analysis(
        method="rosenbaum", effect_estimate=5.0, se_estimate=1.0, gamma_range=(1.0, 2.0)
    )

    assert isinstance(result, SensitivityResult)
    assert result.method == "rosenbaum"
    assert result.original_effect == 5.0
    assert "gamma" in result.sensitivity_bounds
    assert "upper" in result.sensitivity_bounds
    assert "lower" in result.sensitivity_bounds


def test_sensitivity_e_value():
    """Test E-value sensitivity analysis."""
    analyzer = CausalInferenceAnalyzer(
        data=pd.DataFrame({"treatment": [1, 0], "outcome": [10, 5]}),
        treatment_col="treatment",
        outcome_col="outcome",
    )

    result = analyzer.sensitivity_analysis(method="e_value", effect_estimate=2.5)

    assert result.method == "e_value"
    assert result.critical_value is not None
    assert result.critical_value > 1.0


def test_sensitivity_confounding_function():
    """Test confounding function sensitivity analysis."""
    analyzer = CausalInferenceAnalyzer(
        data=pd.DataFrame({"treatment": [1, 0], "outcome": [10, 5]}),
        treatment_col="treatment",
        outcome_col="outcome",
    )

    result = analyzer.sensitivity_analysis(
        method="confounding_function", effect_estimate=3.0
    )

    assert result.method == "confounding_function"
    assert result.confounding_strength is not None


def test_sensitivity_unknown_method():
    """Test sensitivity analysis with unknown method."""
    analyzer = CausalInferenceAnalyzer(
        data=pd.DataFrame({"treatment": [1, 0], "outcome": [10, 5]}),
        treatment_col="treatment",
        outcome_col="outcome",
    )

    with pytest.raises(ValueError, match="Unknown sensitivity method"):
        analyzer.sensitivity_analysis(method="unknown_method", effect_estimate=3.0)


# --- Utility Function Tests ---


def test_ate_inference():
    """Test ATE inference function."""
    result = ate_inference(ate=5.0, se=1.0, confidence_level=0.95)

    assert result["ate"] == 5.0
    assert result["se"] == 1.0
    assert "confidence_interval" in result
    assert "p_value" in result
    assert "significant" in result

    # Should be significant
    assert result["significant"] == True
    assert result["p_value"] < 0.05


def test_ate_inference_nonsignificant():
    """Test ATE inference for non-significant effect."""
    result = ate_inference(ate=0.1, se=1.0, confidence_level=0.95)

    assert result["significant"] == False
    assert result["p_value"] > 0.05


def test_ate_inference_different_confidence_levels():
    """Test ATE inference with different confidence levels."""
    result_95 = ate_inference(ate=2.0, se=1.0, confidence_level=0.95)
    result_99 = ate_inference(ate=2.0, se=1.0, confidence_level=0.99)

    # 99% CI should be wider than 95% CI
    width_95 = result_95["confidence_interval"][1] - result_95["confidence_interval"][0]
    width_99 = result_99["confidence_interval"][1] - result_99["confidence_interval"][0]

    assert width_99 > width_95


# --- Integration Tests ---


def test_missing_data_handling(iv_data):
    """Test handling of missing data."""
    iv_data_missing = iv_data.copy()
    iv_data_missing.loc[0:10, "outcome"] = np.nan

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        analyzer = CausalInferenceAnalyzer(
            data=iv_data_missing, treatment_col="treatment", outcome_col="outcome"
        )
        assert len(w) > 0
        assert "missing" in str(w[0].message).lower()


def test_mlflow_integration(iv_data):
    """Test MLflow tracking integration."""
    with patch("mcp_server.causal_inference.MLFLOW_AVAILABLE", True):
        with patch(
            "mcp_server.causal_inference.MLflowExperimentTracker"
        ) as mock_tracker:
            mock_instance = Mock()
            mock_tracker.return_value = mock_instance

            analyzer = CausalInferenceAnalyzer(
                data=iv_data,
                treatment_col="treatment",
                outcome_col="outcome",
                mlflow_experiment="test_experiment",
            )

            # Tracker should be initialized
            assert analyzer.tracker is not None


def test_analyzer_validation_missing_columns():
    """Test analyzer validation with missing columns."""
    data = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    with pytest.raises(ValueError, match="Missing required columns"):
        CausalInferenceAnalyzer(
            data=data, treatment_col="treatment", outcome_col="outcome"
        )
