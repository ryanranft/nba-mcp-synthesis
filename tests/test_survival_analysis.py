"""
Tests for Survival Analysis Module.

Tests cover:
- Cox proportional hazards
- Cox time-varying covariates
- Parametric survival models
- Kaplan-Meier estimation
- Competing risks
- Frailty models
- Model diagnostics and utilities

Author: Agent 8 Module 4B
Date: October 2025
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import warnings

# Skip all tests if lifelines not available
pytest.importorskip("lifelines", reason="lifelines required for survival analysis")

from mcp_server.survival_analysis import (
    SurvivalAnalyzer,
    SurvivalResult,
    KaplanMeierResult,
    CompetingRisksResult,
    FrailtyResult,
    hazard_ratio_interpretation,
    median_survival_comparison,
    SurvivalModel
)


# --- Fixtures ---

@pytest.fixture
def survival_data():
    """Generate survival data for testing."""
    np.random.seed(42)
    n = 300

    # Covariates
    draft_position = np.random.randint(1, 61, n)
    height = np.random.normal(78, 4, n)
    age_drafted = np.random.uniform(19, 24, n)

    # Baseline hazard with covariate effects
    # Hazard increases with draft position, decreases with height
    baseline_hazard = 0.05
    hazard = baseline_hazard * np.exp(
        0.02 * draft_position - 0.05 * (height - 78)
    )

    # Generate survival times (exponential distribution)
    survival_time = np.random.exponential(1 / hazard)

    # Censoring (30% censored)
    censored = np.random.rand(n) < 0.3
    event = (~censored).astype(int)

    return pd.DataFrame({
        'career_years': survival_time,
        'retired': event,
        'draft_position': draft_position,
        'height': height,
        'age_drafted': age_drafted
    })


@pytest.fixture
def time_varying_data():
    """Generate time-varying covariate data."""
    np.random.seed(42)

    player_ids = [f'player_{i}' for i in range(50)]
    data = []

    for player_id in player_ids:
        n_seasons = np.random.randint(3, 15)
        base_ppg = np.random.uniform(5, 25)

        for season in range(n_seasons):
            age = 22 + season
            ppg = base_ppg + np.random.normal(0, 3) - 0.5 * season  # Decline over time

            # Event in final season (retirement)
            event = 1 if season == n_seasons - 1 else 0

            data.append({
                'player_id': player_id,
                'start': season,
                'stop': season + 1,
                'age': age,
                'ppg': ppg,
                'retired': event
            })

    return pd.DataFrame(data)


@pytest.fixture
def competing_risks_data():
    """Generate competing risks data (multiple event types)."""
    np.random.seed(42)
    n = 200

    draft_position = np.random.randint(1, 61, n)

    # Event types: 0=censored, 1=retire_age, 2=retire_injury, 3=retire_personal
    event_probs = np.array([0.2, 0.4, 0.3, 0.1])
    event_type = np.random.choice([0, 1, 2, 3], size=n, p=event_probs)

    # Survival times
    survival_time = np.random.exponential(8, n)

    return pd.DataFrame({
        'career_years': survival_time,
        'event_type': event_type,
        'draft_position': draft_position
    })


# --- Cox PH Tests ---

def test_survival_analyzer_initialization(survival_data):
    """Test survival analyzer initialization."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position', 'height']
    )

    assert analyzer.duration_col == 'career_years'
    assert analyzer.event_col == 'retired'
    assert len(analyzer.covariates) == 2
    assert len(analyzer.data) == 300


def test_cox_ph_basic(survival_data):
    """Test basic Cox proportional hazards model."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position', 'height']
    )

    result = analyzer.cox_proportional_hazards()

    assert isinstance(result, SurvivalResult)
    assert result.model_type == 'cox_ph'
    assert result.coefficients is not None
    assert len(result.coefficients) == 2
    assert result.concordance_index is not None
    assert 0 <= result.concordance_index <= 1


def test_cox_ph_hazard_ratios(survival_data):
    """Test Cox PH hazard ratios."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position']
    )

    result = analyzer.cox_proportional_hazards()

    # draft_position coefficient should be positive (higher pick = shorter career)
    assert result.coefficients['draft_position'] > 0

    # Hazard ratio should be > 1
    assert result.hazard_ratios['draft_position'] > 1


def test_cox_ph_with_formula(survival_data):
    """Test Cox PH with formula."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    result = analyzer.cox_proportional_hazards(
        formula="~ draft_position + height"
    )

    assert result.coefficients is not None
    assert 'draft_position' in result.coefficients.index


def test_cox_ph_robust_se(survival_data):
    """Test Cox PH with robust standard errors."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position']
    )

    result_robust = analyzer.cox_proportional_hazards(robust=True)
    result_regular = analyzer.cox_proportional_hazards(robust=False)

    # Both should produce results
    assert result_robust.coefficients is not None
    assert result_regular.coefficients is not None


def test_cox_ph_penalized(survival_data):
    """Test Cox PH with L2 penalty."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position', 'height']
    )

    result = analyzer.cox_proportional_hazards(penalizer=0.1)

    # Penalized coefficients should be smaller
    assert result.coefficients is not None


def test_cox_ph_model_fit_metrics(survival_data):
    """Test Cox PH model fit metrics."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position']
    )

    result = analyzer.cox_proportional_hazards()

    assert result.log_likelihood is not None
    assert result.aic is not None
    assert result.bic is not None
    assert result.concordance_index >= 0.5  # Should be better than random


# --- Cox Time-Varying Tests ---

def test_cox_time_varying_basic(time_varying_data):
    """Test Cox time-varying covariates model."""
    analyzer = SurvivalAnalyzer(
        data=time_varying_data,
        duration_col='stop',
        event_col='retired',
        covariates=['age', 'ppg']
    )

    result = analyzer.cox_time_varying(
        id_col='player_id',
        start_col='start',
        stop_col='stop'
    )

    assert isinstance(result, SurvivalResult)
    assert result.model_type == 'cox_time_varying'
    assert result.coefficients is not None


def test_cox_time_varying_with_formula(time_varying_data):
    """Test Cox time-varying with formula."""
    analyzer = SurvivalAnalyzer(
        data=time_varying_data,
        duration_col='stop',
        event_col='retired'
    )

    result = analyzer.cox_time_varying(
        id_col='player_id',
        start_col='start',
        stop_col='stop',
        formula="~ age + ppg"
    )

    assert 'age' in result.coefficients.index
    assert 'ppg' in result.coefficients.index


# --- Parametric Model Tests ---

def test_parametric_weibull(survival_data):
    """Test Weibull parametric model."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position']
    )

    result = analyzer.parametric_survival(model='weibull')

    assert result.model_type == 'parametric_weibull'
    assert result.median_survival_time is not None
    assert result.survival_function is not None


def test_parametric_lognormal(survival_data):
    """Test log-normal parametric model."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    result = analyzer.parametric_survival(model='lognormal')

    assert result.model_type == 'parametric_lognormal'


def test_parametric_loglogistic(survival_data):
    """Test log-logistic parametric model."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    result = analyzer.parametric_survival(model='loglogistic')

    assert result.model_type == 'parametric_loglogistic'


def test_parametric_exponential(survival_data):
    """Test exponential parametric model."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    result = analyzer.parametric_survival(model='exponential')

    assert result.model_type == 'parametric_exponential'


def test_parametric_with_covariates(survival_data):
    """Test parametric model with covariates."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position', 'height']
    )

    result = analyzer.parametric_survival(
        model='weibull',
        formula="~ draft_position + height"
    )

    assert result.coefficients is not None


# --- Kaplan-Meier Tests ---

def test_kaplan_meier_basic(survival_data):
    """Test basic Kaplan-Meier estimation."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    result = analyzer.kaplan_meier()

    assert isinstance(result, KaplanMeierResult)
    assert result.survival_function is not None
    assert result.confidence_interval is not None
    assert result.median_survival_time > 0


def test_kaplan_meier_grouped(survival_data):
    """Test Kaplan-Meier with grouping."""
    # Add draft round
    survival_data['draft_round'] = (survival_data['draft_position'] <= 30).astype(int)

    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    results = analyzer.kaplan_meier(groups='draft_round')

    assert isinstance(results, dict)
    assert len(results) == 2
    assert '0' in results or '1' in results


def test_kaplan_meier_confidence_interval(survival_data):
    """Test Kaplan-Meier confidence intervals."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    result = analyzer.kaplan_meier(alpha=0.05)

    # CI should have lower and upper bounds
    assert result.confidence_interval is not None
    assert len(result.confidence_interval.columns) >= 2


def test_kaplan_meier_event_table(survival_data):
    """Test Kaplan-Meier event table."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    result = analyzer.kaplan_meier()

    assert result.event_table is not None
    # Event table should have at_risk, observed, censored columns


def test_logrank_test(survival_data):
    """Test log-rank test."""
    survival_data['lottery'] = (survival_data['draft_position'] <= 14)

    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired'
    )

    group1 = survival_data['lottery']
    group2 = ~survival_data['lottery']

    result = analyzer.logrank_test(group1, group2)

    assert 'statistic' in result
    assert 'p_value' in result
    assert result['p_value'] >= 0
    assert result['p_value'] <= 1


# --- Competing Risks Tests ---

def test_competing_risks_basic(competing_risks_data):
    """Test basic competing risks analysis."""
    # Convert to binary event
    competing_risks_data['any_event'] = (competing_risks_data['event_type'] > 0).astype(int)

    analyzer = SurvivalAnalyzer(
        data=competing_risks_data,
        duration_col='career_years',
        event_col='any_event'
    )

    result = analyzer.competing_risks(
        event_type_col='event_type',
        event_types=[1, 2, 3]
    )

    assert isinstance(result, CompetingRisksResult)
    assert len(result.cumulative_incidence) == 3


def test_competing_risks_cumulative_incidence(competing_risks_data):
    """Test cumulative incidence functions."""
    competing_risks_data['any_event'] = (competing_risks_data['event_type'] > 0).astype(int)

    analyzer = SurvivalAnalyzer(
        data=competing_risks_data,
        duration_col='career_years',
        event_col='any_event'
    )

    result = analyzer.competing_risks(
        event_type_col='event_type',
        event_types=[1, 2]
    )

    # CIF should be DataFrames
    assert '1' in result.cumulative_incidence
    assert '2' in result.cumulative_incidence


# --- Frailty Model Tests ---

def test_frailty_model_basic(survival_data):
    """Test basic frailty model."""
    # Add team ID for shared frailty
    survival_data['team_id'] = np.random.choice(['LAL', 'GSW', 'BOS', 'MIA'], len(survival_data))

    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position'],
        entity_col='team_id'
    )

    result = analyzer.frailty_model(shared_frailty_col='team_id')

    assert isinstance(result, FrailtyResult)
    assert result.frailty_variance >= 0


def test_frailty_variance(survival_data):
    """Test frailty variance estimation."""
    survival_data['team_id'] = np.random.choice(['LAL', 'GSW'], len(survival_data))

    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position'],
        entity_col='team_id'
    )

    result = analyzer.frailty_model()

    # Frailty variance should be positive
    assert result.frailty_variance > 0


# --- Model Comparison Tests ---

def test_model_comparison(survival_data):
    """Test model comparison."""
    analyzer = SurvivalAnalyzer(
        data=survival_data,
        duration_col='career_years',
        event_col='retired',
        covariates=['draft_position']
    )

    cox_result = analyzer.cox_proportional_hazards()
    weibull_result = analyzer.parametric_survival(model='weibull')
    lognormal_result = analyzer.parametric_survival(model='lognormal')

    comparison = analyzer.model_comparison([cox_result, weibull_result, lognormal_result])

    assert isinstance(comparison, pd.DataFrame)
    assert len(comparison) == 3
    assert 'aic' in comparison.columns or 'concordance_index' in comparison.columns


# --- Utility Function Tests ---

def test_hazard_ratio_interpretation():
    """Test hazard ratio interpretation."""
    # HR > 1 (increased risk)
    interp1 = hazard_ratio_interpretation(1.5)
    assert 'increase' in interp1.lower()

    # HR < 1 (decreased risk)
    interp2 = hazard_ratio_interpretation(0.7)
    assert 'decrease' in interp2.lower()

    # HR = 1 (no effect)
    interp3 = hazard_ratio_interpretation(1.0)
    assert 'no effect' in interp3.lower()


def test_median_survival_comparison():
    """Test median survival comparison."""
    result = median_survival_comparison(
        median1=10.5,
        median2=8.0,
        group1_name="Lottery",
        group2_name="Non-lottery"
    )

    assert "10.5" in result
    assert "8.0" in result
    assert "Lottery" in result


# --- Validation Tests ---

def test_validation_missing_columns():
    """Test validation with missing columns."""
    data = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})

    with pytest.raises(ValueError, match='Missing required columns'):
        SurvivalAnalyzer(
            data=data,
            duration_col='duration',
            event_col='event'
        )


def test_validation_negative_duration():
    """Test validation with negative duration."""
    data = pd.DataFrame({
        'duration': [-1, 2, 3],
        'event': [1, 0, 1]
    })

    with pytest.raises(ValueError, match='Duration must be positive'):
        SurvivalAnalyzer(
            data=data,
            duration_col='duration',
            event_col='event'
        )


def test_validation_non_binary_event():
    """Test validation with non-binary event."""
    data = pd.DataFrame({
        'duration': [1, 2, 3],
        'event': [0, 1, 2]  # Should be 0 or 1
    })

    with pytest.raises(ValueError, match='Event indicator must be 0 or 1'):
        SurvivalAnalyzer(
            data=data,
            duration_col='duration',
            event_col='event'
        )


# --- Integration Tests ---

def test_mlflow_integration(survival_data):
    """Test MLflow tracking integration."""
    with patch('mcp_server.survival_analysis.MLFLOW_AVAILABLE', True):
        with patch('mcp_server.survival_analysis.MLflowExperimentTracker') as mock_tracker:
            mock_instance = Mock()
            mock_tracker.return_value = mock_instance

            analyzer = SurvivalAnalyzer(
                data=survival_data,
                duration_col='career_years',
                event_col='retired',
                mlflow_experiment='test_experiment'
            )

            assert analyzer.tracker is not None
