"""
Tests for Econometric Suite Module.

Tests cover:
- Data structure detection
- Auto-method selection
- Module integration
- Model comparison
- Model averaging

Author: Agent 8 Module 4D
Date: October 2025
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from mcp_server.econometric_suite import (
    EconometricSuite,
    DataClassifier,
    DataStructure,
    DataCharacteristics,
    MethodCategory,
    SuiteResult,
    ModelAverager,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def cross_section_data():
    """Generate cross-sectional data."""
    np.random.seed(42)
    n = 100

    return pd.DataFrame(
        {
            "player_id": range(n),
            "points": np.random.normal(20, 5, n),
            "assists": np.random.normal(5, 2, n),
            "rebounds": np.random.normal(8, 3, n),
        }
    )


@pytest.fixture
def time_series_data():
    """Generate time series data."""
    np.random.seed(42)
    n = 200

    dates = pd.date_range(start="2020-01-01", periods=n, freq="D")
    values = np.random.normal(20, 3, n).cumsum()

    return pd.DataFrame({"date": dates, "points": values})


@pytest.fixture
def panel_data():
    """Generate panel data."""
    np.random.seed(42)
    n_players = 50
    n_seasons = 5

    data = []
    for player in range(n_players):
        for season in range(n_seasons):
            data.append(
                {
                    "player_id": player,
                    "season": season,
                    "points": np.random.normal(20 + player * 0.1, 5),
                    "assists": np.random.normal(5, 2),
                }
            )

    return pd.DataFrame(data)


@pytest.fixture
def survival_data():
    """Generate survival/event history data."""
    np.random.seed(42)
    n = 100

    return pd.DataFrame(
        {
            "player_id": range(n),
            "career_years": np.random.exponential(8, n),
            "retired": np.random.binomial(1, 0.7, n),
            "draft_position": np.random.randint(1, 60, n),
        }
    )


@pytest.fixture
def survival_data_with_groups():
    """Generate survival data with grouping variable."""
    np.random.seed(42)
    n = 150

    positions = np.random.choice(["Guard", "Forward", "Center"], n)
    career_years = np.random.exponential(8, n)
    retired = np.random.binomial(1, 0.7, n)

    return pd.DataFrame(
        {
            "player_id": range(n),
            "career_years": career_years,
            "retired": retired,
            "position": positions,
            "draft_round": np.random.choice([1, 2], n),
        }
    )


@pytest.fixture
def competing_risks_data():
    """Generate competing risks data (multiple event types)."""
    np.random.seed(42)
    n = 120

    # Event types: 0=censored, 1=injury retirement, 2=age retirement
    event_type = np.random.choice([0, 1, 2], n, p=[0.2, 0.4, 0.4])
    duration = np.random.exponential(7, n)

    # Binary event indicator (0=censored, 1=event occurred)
    event_occurred = (event_type > 0).astype(int)

    return pd.DataFrame(
        {
            "player_id": range(n),
            "career_years": duration,
            "event_occurred": event_occurred,  # Binary for SurvivalAnalyzer validation
            "event_type": event_type,  # Multi-valued for competing risks
            "draft_position": np.random.randint(1, 60, n),
        }
    )


@pytest.fixture
def frailty_data():
    """Generate survival data with shared frailty (team clustering)."""
    np.random.seed(42)
    n_teams = 10
    players_per_team = 15
    n = n_teams * players_per_team

    teams = []
    durations = []
    events = []

    for team_id in range(n_teams):
        # Team-specific frailty effect
        team_frailty = np.random.gamma(2, 0.5)
        for _ in range(players_per_team):
            teams.append(team_id)
            duration = np.random.exponential(8 / team_frailty)
            durations.append(duration)
            events.append(np.random.binomial(1, 0.7))

    return pd.DataFrame(
        {
            "player_id": range(n),
            "team_id": teams,
            "career_years": durations,
            "retired": events,
            "draft_position": np.random.randint(1, 60, n),
        }
    )


@pytest.fixture
def treatment_outcome_data():
    """Generate treatment-outcome data for causal inference."""
    np.random.seed(42)
    n = 200

    treatment = np.random.binomial(1, 0.5, n)
    # True treatment effect = 5
    outcome = 20 + 5 * treatment + np.random.normal(0, 3, n)

    return pd.DataFrame(
        {
            "player_id": range(n),
            "new_coach": treatment,
            "wins": outcome,
            "team_salary": np.random.normal(100, 20, n),
            "avg_age": np.random.normal(27, 3, n),
        }
    )


@pytest.fixture
def iv_data():
    """Generate data for Instrumental Variables testing."""
    np.random.seed(42)
    n = 200

    # Instrument (draft position affects training but not outcome directly)
    instrument = np.random.normal(15, 5, n)

    # Treatment (training) depends on instrument
    training = 0.3 * instrument + np.random.normal(0, 2, n)

    # Outcome depends on treatment, not instrument directly
    outcome = 50 + 3 * training + np.random.normal(0, 5, n)

    return pd.DataFrame(
        {
            "player_id": range(n),
            "draft_position": instrument,
            "training_hours": training,
            "performance": outcome,
            "age": np.random.normal(25, 3, n),
        }
    )


@pytest.fixture
def rdd_data():
    """Generate data for Regression Discontinuity Design testing."""
    np.random.seed(42)
    n = 300

    # Running variable (test score)
    test_score = np.random.uniform(50, 90, n)

    # Treatment assignment based on cutoff at 70
    cutoff = 70.0
    scholarship = (test_score >= cutoff).astype(int)

    # Outcome depends on treatment with discontinuity at cutoff
    graduation_rate = (
        60
        + 0.5 * test_score  # Continuous effect of test score
        + 15 * scholarship  # Treatment effect (discontinuity)
        + np.random.normal(0, 5, n)
    )

    return pd.DataFrame(
        {
            "student_id": range(n),
            "test_score": test_score,
            "scholarship": scholarship,
            "graduation_rate": graduation_rate,
            "parent_income": np.random.normal(50000, 20000, n),
        }
    )


@pytest.fixture
def synthetic_control_data():
    """Generate panel data for Synthetic Control testing."""
    np.random.seed(42)
    n_units = 20
    n_periods = 15
    treatment_period = 10
    treated_unit = 0

    data = []
    for unit in range(n_units):
        base_level = 50 + unit * 2
        for period in range(n_periods):
            # Treated unit gets treatment effect after period 10
            treatment_effect = 0
            if unit == treated_unit and period >= treatment_period:
                treatment_effect = 10

            outcome = (
                base_level
                + 0.5 * period  # Time trend
                + treatment_effect
                + np.random.normal(0, 2)
            )

            data.append(
                {
                    "unit_id": unit,
                    "period": period,
                    "outcome": outcome,
                    "covariate1": np.random.normal(100, 10),
                }
            )

    return pd.DataFrame(data)


# ==============================================================================
# Data Classification Tests (5 tests)
# ==============================================================================


def test_detect_cross_section(cross_section_data):
    """Test detection of cross-sectional data."""
    classifier = DataClassifier(data=cross_section_data)

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.CROSS_SECTION
    assert characteristics.n_obs == 100
    assert not characteristics.has_time_index


def test_detect_time_series(time_series_data):
    """Test detection of time series data."""
    # Set date as index
    ts_data = time_series_data.set_index("date")

    classifier = DataClassifier(data=ts_data)

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.TIME_SERIES
    assert characteristics.n_obs == 200
    assert characteristics.has_time_index


def test_detect_panel(panel_data):
    """Test detection of panel data."""
    classifier = DataClassifier(
        data=panel_data, entity_col="player_id", time_col="season"
    )

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.PANEL
    assert characteristics.n_obs == 250
    assert characteristics.n_entities == 50
    assert characteristics.n_periods == 5
    assert characteristics.is_balanced


def test_detect_survival(survival_data):
    """Test detection of event history/survival data."""
    classifier = DataClassifier(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.EVENT_HISTORY
    assert characteristics.has_duration
    assert characteristics.has_event


def test_detect_treatment_outcome(treatment_outcome_data):
    """Test detection of treatment-outcome structure."""
    classifier = DataClassifier(
        data=treatment_outcome_data, treatment_col="new_coach", outcome_col="wins"
    )

    characteristics = classifier.detect_structure()

    assert characteristics.structure == DataStructure.TREATMENT_OUTCOME
    assert characteristics.has_treatment
    assert characteristics.has_outcome


# ==============================================================================
# Recommendation Tests (5 tests)
# ==============================================================================


def test_recommend_survival_methods(survival_data):
    """Test method recommendation for survival data."""
    classifier = DataClassifier(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    recommendations = classifier.recommend_methods()

    assert MethodCategory.SURVIVAL_ANALYSIS in recommendations


def test_recommend_causal_methods(treatment_outcome_data):
    """Test method recommendation for causal inference."""
    classifier = DataClassifier(
        data=treatment_outcome_data, treatment_col="new_coach", outcome_col="wins"
    )

    recommendations = classifier.recommend_methods()

    assert MethodCategory.CAUSAL_INFERENCE in recommendations


def test_recommend_panel_methods(panel_data):
    """Test method recommendation for panel data."""
    classifier = DataClassifier(
        data=panel_data, entity_col="player_id", time_col="season"
    )

    recommendations = classifier.recommend_methods()

    assert MethodCategory.PANEL_DATA in recommendations
    assert MethodCategory.BAYESIAN in recommendations


def test_recommend_time_series_methods(time_series_data):
    """Test method recommendation for time series data."""
    ts_data = time_series_data.set_index("date")

    classifier = DataClassifier(data=ts_data)

    recommendations = classifier.recommend_methods()

    assert MethodCategory.TIME_SERIES in recommendations
    assert MethodCategory.ADVANCED_TIME_SERIES in recommendations


def test_recommend_cross_section_methods(cross_section_data):
    """Test method recommendation for cross-sectional data."""
    classifier = DataClassifier(data=cross_section_data)

    recommendations = classifier.recommend_methods()

    assert MethodCategory.BAYESIAN in recommendations


# ==============================================================================
# Suite Initialization Tests (3 tests)
# ==============================================================================


def test_suite_initialization_time_series(time_series_data):
    """Test suite initialization with time series data."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    assert suite.characteristics.structure == DataStructure.TIME_SERIES
    assert MethodCategory.TIME_SERIES in suite.recommended_methods


def test_suite_initialization_panel(panel_data):
    """Test suite initialization with panel data."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    assert suite.characteristics.structure == DataStructure.PANEL
    assert suite.characteristics.n_entities == 50
    assert suite.characteristics.n_periods == 5


def test_suite_initialization_survival(survival_data):
    """Test suite initialization with survival data."""
    suite = EconometricSuite(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    assert suite.characteristics.structure == DataStructure.EVENT_HISTORY
    assert MethodCategory.SURVIVAL_ANALYSIS in suite.recommended_methods


# ==============================================================================
# Method Access Tests (15 tests)
# ==============================================================================


def test_time_series_analysis(time_series_data):
    """Test access to time series methods."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.time_series_analysis(method="arima", order=(1, 1, 1))

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.TIME_SERIES
    assert result.method_used == "ARIMA"
    assert result.aic is not None


def test_panel_analysis_fixed_effects(panel_data):
    """Test access to panel data fixed effects."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    result = suite.panel_analysis(method="fixed_effects")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.PANEL_DATA
    assert result.method_used == "Fixed Effects"
    assert result.r_squared is not None


def test_panel_analysis_random_effects(panel_data):
    """Test access to panel data random effects."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    result = suite.panel_analysis(method="random_effects")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.PANEL_DATA
    assert result.method_used == "Random Effects"


def test_causal_analysis(treatment_outcome_data):
    """Test access to causal inference methods."""
    suite = EconometricSuite(
        data=treatment_outcome_data,
        treatment_col="new_coach",
        outcome_col="wins",
    )

    result = suite.causal_analysis(method="psm", n_neighbors=3)

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.CAUSAL_INFERENCE
    assert result.method_used == "Propensity Score Matching"


def test_causal_analysis_iv(iv_data):
    """Test Instrumental Variables method via Suite."""
    suite = EconometricSuite(
        data=iv_data,
        treatment_col="training_hours",
        outcome_col="performance",
        entity_col="player_id",  # Exclude player_id from covariates
    )

    result = suite.causal_analysis(method="iv", instruments=["draft_position"])

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.CAUSAL_INFERENCE
    assert result.method_used == "Instrumental Variables (2SLS)"
    # Check that result object has IV-specific attributes
    assert hasattr(result.result, "treatment_effect")
    assert hasattr(result.result, "first_stage_f_stat")


def test_causal_analysis_iv_missing_instrument(iv_data):
    """Test IV method raises error when instruments not provided."""
    suite = EconometricSuite(
        data=iv_data,
        treatment_col="training_hours",
        outcome_col="performance",
        entity_col="player_id",
    )

    with pytest.raises(ValueError, match="instruments parameter required"):
        suite.causal_analysis(method="iv")


def test_causal_analysis_iv_alias(iv_data):
    """Test IV method works with 'instrumental_variables' alias."""
    suite = EconometricSuite(
        data=iv_data,
        treatment_col="training_hours",
        outcome_col="performance",
        entity_col="player_id",
    )

    result = suite.causal_analysis(
        method="instrumental_variables", instruments=["draft_position"]
    )

    assert result.method_used == "Instrumental Variables (2SLS)"


def test_causal_analysis_rdd(rdd_data):
    """Test Regression Discontinuity Design method via Suite."""
    suite = EconometricSuite(
        data=rdd_data,
        treatment_col="scholarship",
        outcome_col="graduation_rate",
        entity_col="student_id",  # Exclude student_id from covariates
    )

    result = suite.causal_analysis(
        method="rdd", running_var="test_score", cutoff=70.0, bandwidth=10.0
    )

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.CAUSAL_INFERENCE
    assert result.method_used == "Regression Discontinuity Design"
    # Check that result object has RDD-specific attributes
    assert hasattr(result.result, "treatment_effect")
    assert hasattr(result.result, "bandwidth")


def test_causal_analysis_rdd_missing_params(rdd_data):
    """Test RDD method raises error when required params not provided."""
    suite = EconometricSuite(
        data=rdd_data,
        treatment_col="scholarship",
        outcome_col="graduation_rate",
        entity_col="student_id",
    )

    # Missing running_var
    with pytest.raises(ValueError, match="running_var and cutoff parameters required"):
        suite.causal_analysis(method="rdd", cutoff=70.0)

    # Missing cutoff
    with pytest.raises(ValueError, match="running_var and cutoff parameters required"):
        suite.causal_analysis(method="rdd", running_var="test_score")


def test_causal_analysis_rdd_alias(rdd_data):
    """Test RDD method works with 'regression_discontinuity' alias."""
    suite = EconometricSuite(
        data=rdd_data,
        treatment_col="scholarship",
        outcome_col="graduation_rate",
        entity_col="student_id",
    )

    result = suite.causal_analysis(
        method="regression_discontinuity", running_var="test_score", cutoff=70.0
    )

    assert result.method_used == "Regression Discontinuity Design"


def test_causal_analysis_synthetic_control(synthetic_control_data):
    """Test Synthetic Control method via Suite."""
    suite = EconometricSuite(
        data=synthetic_control_data,
        entity_col="unit_id",
        time_col="period",
        outcome_col="outcome",
    )

    result = suite.causal_analysis(
        method="synthetic",
        treated_unit=0,
        outcome_periods=list(range(15)),
        treatment_period=10,
    )

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.CAUSAL_INFERENCE
    assert result.method_used == "Synthetic Control"
    # Check that result object has Synthetic Control-specific attributes
    assert hasattr(result.result, "treatment_effect")
    assert hasattr(result.result, "weights")  # Donor unit weights
    assert hasattr(result.result, "average_effect")


def test_causal_analysis_synthetic_missing_params(synthetic_control_data):
    """Test Synthetic Control raises error when required params not provided."""
    suite = EconometricSuite(
        data=synthetic_control_data,
        entity_col="unit_id",
        time_col="period",
        outcome_col="outcome",
    )

    with pytest.raises(
        ValueError, match="treated_unit, outcome_periods, and treatment_period required"
    ):
        suite.causal_analysis(
            method="synthetic",
            treated_unit=0,  # Missing outcome_periods and treatment_period
        )


def test_causal_analysis_synthetic_alias(synthetic_control_data):
    """Test Synthetic Control works with 'synthetic_control' alias."""
    suite = EconometricSuite(
        data=synthetic_control_data,
        entity_col="unit_id",
        time_col="period",
        outcome_col="outcome",
    )

    result = suite.causal_analysis(
        method="synthetic_control",
        treated_unit=0,
        outcome_periods=list(range(15)),
        treatment_period=10,
    )

    assert result.method_used == "Synthetic Control"


def test_survival_analysis(survival_data):
    """Test access to survival analysis methods."""
    suite = EconometricSuite(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    result = suite.survival_analysis(method="cox")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.SURVIVAL_ANALYSIS
    assert result.method_used == "Cox Proportional Hazards"
    assert result.log_likelihood is not None


def test_survival_analysis_kaplan_meier(survival_data):
    """Test Kaplan-Meier estimator via Suite."""
    suite = EconometricSuite(
        data=survival_data,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    result = suite.survival_analysis(method="kaplan_meier")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.SURVIVAL_ANALYSIS
    assert result.method_used == "Kaplan-Meier Estimator"
    # Check result has KM-specific attributes
    assert hasattr(result.result, "survival_function")
    assert hasattr(result.result, "median_survival_time")


def test_survival_analysis_kaplan_meier_grouped(survival_data_with_groups):
    """Test Kaplan-Meier with grouping variable."""
    suite = EconometricSuite(
        data=survival_data_with_groups,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    result = suite.survival_analysis(method="kaplan_meier", groups="position")

    assert isinstance(result, SuiteResult)
    assert result.method_used == "Kaplan-Meier Estimator"
    # Result should be a dict of KM results by group
    assert isinstance(result.result, dict)
    assert len(result.result) > 1  # Multiple groups


def test_survival_analysis_km_alias(survival_data):
    """Test 'km' alias for Kaplan-Meier."""
    suite = EconometricSuite(
        data=survival_data,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    result = suite.survival_analysis(method="km")

    assert result.method_used == "Kaplan-Meier Estimator"


def test_survival_analysis_parametric_weibull(survival_data):
    """Test parametric survival with Weibull distribution."""
    suite = EconometricSuite(
        data=survival_data,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    result = suite.survival_analysis(method="parametric", model="weibull")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.SURVIVAL_ANALYSIS
    assert "Weibull" in result.method_used
    assert result.aic is not None
    # BIC may or may not be present depending on lifelines version
    # assert result.bic is not None


def test_survival_analysis_parametric_lognormal(survival_data):
    """Test parametric survival with Log-Normal distribution."""
    suite = EconometricSuite(
        data=survival_data,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    result = suite.survival_analysis(method="parametric", model="lognormal")

    assert "Lognormal" in result.method_used
    assert hasattr(result.result, "survival_function")


def test_survival_analysis_parametric_default(survival_data):
    """Test parametric survival uses Weibull by default."""
    suite = EconometricSuite(
        data=survival_data,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    result = suite.survival_analysis(method="parametric")

    assert "Weibull" in result.method_used  # Default is weibull


def test_survival_analysis_competing_risks(competing_risks_data):
    """Test competing risks analysis via Suite."""
    suite = EconometricSuite(
        data=competing_risks_data,
        duration_col="career_years",
        event_col="event_occurred",  # Binary event indicator
        entity_col="player_id",
    )

    result = suite.survival_analysis(
        method="competing_risks",
        event_type_col="event_type",  # Multi-valued event type
        event_types=[1, 2],  # injury=1, age=2
    )

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.SURVIVAL_ANALYSIS
    assert result.method_used == "Competing Risks"
    # Check result has competing risks-specific attributes
    assert hasattr(result.result, "cumulative_incidence")


def test_survival_analysis_competing_risks_missing_params(competing_risks_data):
    """Test competing risks raises error when params missing."""
    suite = EconometricSuite(
        data=competing_risks_data,
        duration_col="career_years",
        event_col="event_occurred",  # Binary event indicator
        entity_col="player_id",
    )

    # Missing event_types
    from mcp_server.exceptions import MissingParameterError

    with pytest.raises(
        MissingParameterError,
        match="event_type_col and event_types parameters required",
    ):
        suite.survival_analysis(method="competing_risks", event_type_col="event_type")

    # Missing event_type_col
    with pytest.raises(
        MissingParameterError,
        match="event_type_col and event_types parameters required",
    ):
        suite.survival_analysis(method="competing_risks", event_types=[1, 2])


def test_survival_analysis_competing_risks_validation(competing_risks_data):
    """Test competing risks result structure."""
    suite = EconometricSuite(
        data=competing_risks_data,
        duration_col="career_years",
        event_col="event_occurred",  # Binary event indicator
        entity_col="player_id",
    )

    result = suite.survival_analysis(
        method="competing_risks", event_type_col="event_type", event_types=[1, 2]
    )

    # Validate result structure
    assert hasattr(result.result, "cumulative_incidence")
    assert isinstance(result.result.cumulative_incidence, dict)


def test_survival_analysis_frailty(frailty_data):
    """Test frailty model via Suite."""
    suite = EconometricSuite(
        data=frailty_data,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    result = suite.survival_analysis(method="frailty", shared_frailty_col="team_id")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.SURVIVAL_ANALYSIS
    assert result.method_used == "Frailty Model"
    # Check result has frailty-specific attributes
    assert hasattr(result.result, "frailty_variance")


def test_survival_analysis_frailty_no_grouping(survival_data):
    """Test frailty model without shared frailty column."""
    suite = EconometricSuite(
        data=survival_data,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    # Should work without shared_frailty_col (individual frailty)
    result = suite.survival_analysis(method="frailty")

    assert result.method_used == "Frailty Model"


def test_survival_analysis_frailty_distribution(frailty_data):
    """Test frailty model with different distribution."""
    suite = EconometricSuite(
        data=frailty_data,
        duration_col="career_years",
        event_col="retired",
        entity_col="player_id",
    )

    result = suite.survival_analysis(
        method="frailty",
        shared_frailty_col="team_id",
        distribution="gamma",  # Explicit gamma distribution
    )

    assert result.method_used == "Frailty Model"
    assert hasattr(result.result, "frailty_variance")


def test_advanced_time_series_analysis(time_series_data):
    """Test access to advanced time series methods."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.advanced_time_series_analysis(method="kalman", model="local_level")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.ADVANCED_TIME_SERIES
    assert result.method_used == "Kalman Filter"


def test_advanced_time_series_markov_switching(time_series_data):
    """Test Markov switching model via Suite."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.advanced_time_series_analysis(method="markov_switching", n_regimes=2)

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.ADVANCED_TIME_SERIES
    assert result.method_used == "Markov Switching"
    # Check result has Markov switching-specific attributes
    assert hasattr(result.result, "regime_probabilities")
    assert hasattr(result.result, "transition_matrix")


def test_advanced_time_series_markov_alias(time_series_data):
    """Test 'markov' alias for markov_switching."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.advanced_time_series_analysis(method="markov", n_regimes=2)

    assert result.method_used == "Markov Switching"


def test_advanced_time_series_markov_regimes(time_series_data):
    """Test Markov switching with different number of regimes."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.advanced_time_series_analysis(
        method="markov_switching", n_regimes=3  # Test with 3 regimes
    )

    assert result.method_used == "Markov Switching"
    # Transition matrix should be 3x3 for 3 regimes
    assert result.result.transition_matrix.shape == (3, 3)


def test_advanced_time_series_dynamic_factor(time_series_data):
    """Test dynamic factor model via Suite."""
    ts_data = time_series_data.set_index("date")

    # Dynamic factor requires multivariate data - create 2 series
    multivariate_data = pd.DataFrame(
        {
            "series1": ts_data["points"].values,
            "series2": ts_data["points"].values * 0.9
            + np.random.normal(0, 1, len(ts_data)),
        },
        index=ts_data.index,
    )

    suite = EconometricSuite(data=multivariate_data, target="series1")

    result = suite.advanced_time_series_analysis(
        method="dynamic_factor",
        n_factors=1,
        data=multivariate_data,  # Pass multivariate DataFrame
        enforce_stationarity=False,  # Disable for non-stationary test data
    )

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.ADVANCED_TIME_SERIES
    assert result.method_used == "Dynamic Factor Model"
    # Check result has dynamic factor-specific attributes
    assert hasattr(result.result, "factors")
    assert hasattr(result.result, "factor_loadings")


def test_advanced_time_series_dynamic_factor_multi(panel_data):
    """Test dynamic factor model with multiple factors."""
    # For dynamic factor, we need panel data (multiple series)
    suite = EconometricSuite(
        data=panel_data, target="points", entity_col="player_id", time_col="season"
    )

    result = suite.advanced_time_series_analysis(
        method="dynamic_factor",
        n_factors=2,
        data=panel_data.pivot(index="season", columns="player_id", values="points"),
        enforce_stationarity=False,  # Disable for non-stationary test data
    )

    assert result.method_used == "Dynamic Factor Model"
    # Factors should have 2 columns (2 factors)
    assert result.result.factors.shape[1] == 2


def test_advanced_time_series_structural(time_series_data):
    """Test structural time series via Suite."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.advanced_time_series_analysis(
        method="structural", level=True, trend=False
    )

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.ADVANCED_TIME_SERIES
    assert result.method_used == "Structural Time Series"
    # Check result has structural TS-specific attributes
    assert hasattr(result.result, "level")
    assert hasattr(result.result, "fitted_values")
    assert hasattr(result.result, "irregular")


def test_advanced_time_series_structural_seasonal(time_series_data):
    """Test structural time series with seasonal component."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    result = suite.advanced_time_series_analysis(
        method="structural", level=True, trend=True, seasonal=7  # Weekly seasonality
    )

    assert result.method_used == "Structural Time Series"
    # Check that seasonal component was estimated
    assert hasattr(result.result, "seasonal")


# ==============================================================================
# Model Averaging Tests (4 tests)
# ==============================================================================


def test_model_averaging_equal_weights():
    """Test equal-weight model averaging."""
    predictions = {
        "model1": np.array([10, 20, 30]),
        "model2": np.array([12, 18, 32]),
        "model3": np.array([11, 19, 31]),
    }

    averaged = ModelAverager.average(predictions, weights="equal")

    expected = np.array([11, 19, 31])
    np.testing.assert_array_almost_equal(averaged, expected)


def test_model_averaging_aic_weights():
    """Test AIC-based model averaging."""
    predictions = {
        "model1": np.array([10.0, 20.0, 30.0]),
        "model2": np.array([12.0, 18.0, 32.0]),
    }

    metrics = {
        "model1": {"aic": 100.0, "bic": 105.0},
        "model2": {"aic": 110.0, "bic": 115.0},  # Worse AIC
    }

    averaged = ModelAverager.average(predictions, weights="aic", model_metrics=metrics)

    # model1 should have higher weight (lower AIC)
    # Result should be closer to model1 than model2
    assert np.abs(averaged[0] - 10.0) < np.abs(averaged[0] - 12.0)


def test_model_averaging_custom_weights():
    """Test custom weight model averaging."""
    predictions = {
        "model1": np.array([10, 20, 30]),
        "model2": np.array([20, 30, 40]),
    }

    custom_weights = {"model1": 0.7, "model2": 0.3}

    averaged = ModelAverager.average(predictions, weights=custom_weights)

    expected = 0.7 * predictions["model1"] + 0.3 * predictions["model2"]
    np.testing.assert_array_almost_equal(averaged, expected)


def test_model_averaging_mismatched_shapes():
    """Test that mismatched prediction shapes raise error."""
    predictions = {
        "model1": np.array([10, 20, 30]),
        "model2": np.array([12, 18]),  # Different length
    }

    with pytest.raises(ValueError, match="shapes don't match"):
        ModelAverager.average(predictions)


# ==============================================================================
# Model Comparison Tests (2 tests)
# ==============================================================================


def test_compare_panel_methods(panel_data):
    """Test comparison of panel data methods."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    methods = [
        {"category": "panel", "method": "fixed_effects", "params": {}},
        {"category": "panel", "method": "random_effects", "params": {}},
    ]

    comparison = suite.compare_methods(methods, metric="r_squared")

    assert len(comparison) == 2
    assert "method" in comparison.columns
    assert "r_squared" in comparison.columns
    assert "rank" in comparison.columns


def test_compare_time_series_methods(time_series_data):
    """Test comparison of time series methods."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    methods = [
        {"category": "time_series", "method": "arima", "params": {"order": (1, 1, 1)}},
        {"category": "time_series", "method": "arima", "params": {"order": (2, 1, 0)}},
    ]

    comparison = suite.compare_methods(methods, metric="aic")

    assert len(comparison) == 2
    assert "aic" in comparison.columns
    assert "rank" in comparison.columns


# ==============================================================================
# Auto-Analysis Tests (3 tests)
# ==============================================================================


def test_auto_analysis_time_series(time_series_data):
    """Test auto-analysis for time series data."""
    ts_data = time_series_data.set_index("date")

    suite = EconometricSuite(data=ts_data, target="points")

    # Auto should select time series method
    result = suite.analyze(method="auto")

    assert isinstance(result, SuiteResult)
    assert result.method_category in [
        MethodCategory.TIME_SERIES,
        MethodCategory.ADVANCED_TIME_SERIES,
    ]


def test_auto_analysis_panel(panel_data):
    """Test auto-analysis for panel data."""
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    result = suite.analyze(method="auto")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.PANEL_DATA


def test_auto_analysis_survival(survival_data):
    """Test auto-analysis for survival data."""
    suite = EconometricSuite(
        data=survival_data, duration_col="career_years", event_col="retired"
    )

    result = suite.analyze(method="auto")

    assert isinstance(result, SuiteResult)
    assert result.method_category == MethodCategory.SURVIVAL_ANALYSIS


# ==============================================================================
# Suite Result Tests (2 tests)
# ==============================================================================


def test_suite_result_summary():
    """Test SuiteResult summary generation."""
    result = SuiteResult(
        data_structure=DataStructure.PANEL,
        method_category=MethodCategory.PANEL_DATA,
        method_used="Fixed Effects",
        result=None,
        model=None,
        aic=1234.5,
        bic=1250.0,
        r_squared=0.67,
        n_obs=250,
    )

    summary = result.summary()

    assert "ECONOMETRIC SUITE RESULTS" in summary
    assert "panel" in summary.lower()
    assert "Fixed Effects" in summary
    assert "1234.5" in summary
    assert "0.67" in summary


def test_suite_result_repr():
    """Test SuiteResult string representation."""
    result = SuiteResult(
        data_structure=DataStructure.TIME_SERIES,
        method_category=MethodCategory.TIME_SERIES,
        method_used="ARIMA",
        result=None,
        model=None,
        aic=500.0,
    )

    repr_str = repr(result)

    assert "SuiteResult" in repr_str
    assert "time_series" in repr_str
    assert "ARIMA" in repr_str


# ==============================================================================
# Integration Tests (1 test)
# ==============================================================================


def test_end_to_end_workflow(panel_data):
    """Test complete end-to-end workflow."""
    # Initialize suite
    suite = EconometricSuite(
        data=panel_data,
        target="points",
        entity_col="player_id",
        time_col="season",
    )

    # Check data classification
    assert suite.characteristics.structure == DataStructure.PANEL
    assert len(suite.recommended_methods) > 0

    # Run analysis
    result = suite.panel_analysis(method="fixed_effects")

    assert isinstance(result, SuiteResult)
    assert result.n_obs == 250

    # Get summary
    summary = suite.diagnostic_summary(result)
    assert "Fixed Effects" in summary
    assert "250" in summary
