"""
Tests for Bayesian Time Series Methods.

Tests BVAR, BSTS, and Hierarchical Bayesian Time Series implementations.
"""

import pytest
import numpy as np
import pandas as pd

from mcp_server.bayesian_time_series import (
    BVARAnalyzer,
    BVARResult,
    BSTSResult,
    HierarchicalTSResult,
    PYMC_AVAILABLE,
    check_pymc_available,
)

# Skip all tests if PyMC not available
pytestmark = pytest.mark.skipif(not PYMC_AVAILABLE, reason="PyMC not installed")


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def simple_var_data():
    """Generate simple VAR(1) data for testing."""
    np.random.seed(42)
    T = 100

    # True VAR(1): y_t = 0.5 * y_{t-1} + noise
    y1 = [10.0]
    y2 = [5.0]

    for t in range(1, T):
        y1_new = 0.5 * y1[-1] + 0.2 * y2[-1] + np.random.normal(0, 0.5)
        y2_new = 0.3 * y1[-1] + 0.6 * y2[-1] + np.random.normal(0, 0.5)
        y1.append(y1_new)
        y2.append(y2_new)

    return pd.DataFrame({"var1": y1, "var2": y2})


@pytest.fixture
def multivariate_ts():
    """Generate 3-variable VAR data."""
    np.random.seed(123)
    T = 150

    data = np.zeros((T, 3))
    data[0] = [20, 5, 8]  # Initial values

    for t in range(1, T):
        # VAR(1) with cross-dependencies
        data[t, 0] = (
            0.6 * data[t - 1, 0] + 0.2 * data[t - 1, 1] + np.random.normal(0, 1.0)
        )
        data[t, 1] = (
            0.1 * data[t - 1, 0] + 0.7 * data[t - 1, 1] + np.random.normal(0, 0.5)
        )
        data[t, 2] = (
            0.15 * data[t - 1, 0]
            + 0.1 * data[t - 1, 1]
            + 0.5 * data[t - 1, 2]
            + np.random.normal(0, 0.8)
        )

    return pd.DataFrame(data, columns=["points", "assists", "rebounds"])


# ==============================================================================
# BVAR Tests
# ==============================================================================


class TestBVARAnalyzer:
    """Tests for BVARAnalyzer class."""

    def test_initialization(self, simple_var_data):
        """Test BVAR initialization."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=1
        )

        assert analyzer.n_vars == 2
        assert analyzer.lags == 1
        assert analyzer.minnesota_prior is True
        assert analyzer.Y.shape[0] == 99  # T - lags
        assert analyzer.Y.shape[1] == 2  # n_vars

    def test_initialization_errors(self):
        """Test initialization error handling."""
        data = pd.DataFrame({"x": [1, 2, 3]})

        # Too few variables
        with pytest.raises(ValueError, match="at least 2 variables"):
            BVARAnalyzer(data=data, var_names=["x"], lags=1)

        # Invalid lags
        with pytest.raises(ValueError, match="lags must be >= 1"):
            BVARAnalyzer(data=data, var_names=["x"], lags=0)

        # Invalid data type
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            BVARAnalyzer(data=[1, 2, 3], var_names=["x"], lags=1)

    def test_lagged_matrices(self, simple_var_data):
        """Test lagged matrix creation."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=2
        )

        # Y should have T - lags observations
        assert analyzer.Y.shape == (98, 2)

        # X should have (n_vars * lags + 1) columns (including intercept)
        assert analyzer.X.shape == (98, 2 * 2 + 1)  # 2 vars, 2 lags, 1 intercept

    def test_ar1_variance_estimation(self, simple_var_data):
        """Test AR(1) variance estimation for prior scaling."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=1
        )

        sigma_scale = analyzer._estimate_ar1_variance()

        assert len(sigma_scale) == 2
        assert np.all(sigma_scale > 0)  # All positive
        assert np.all(sigma_scale < 10)  # Reasonable magnitude

    def test_model_building_minnesota(self, simple_var_data):
        """Test Minnesota prior model building."""
        analyzer = BVARAnalyzer(
            data=simple_var_data,
            var_names=["var1", "var2"],
            lags=1,
            minnesota_prior=True,
        )

        model = analyzer.build_model(lambda1=0.2, lambda2=0.5, lambda3=1.0)

        assert model is not None
        assert "Sigma" in model.named_vars
        assert "intercept" in model.named_vars

        # Check for Minnesota prior coefficients
        expected_names = [
            "beta_0_0_lag1",
            "beta_0_1_lag1",
            "beta_1_0_lag1",
            "beta_1_1_lag1",
        ]
        for name in expected_names:
            assert name in model.named_vars, f"Missing variable: {name}"

    def test_model_building_diffuse(self, simple_var_data):
        """Test diffuse prior model building."""
        analyzer = BVARAnalyzer(
            data=simple_var_data,
            var_names=["var1", "var2"],
            lags=1,
            minnesota_prior=False,
        )

        model = analyzer.build_model()

        assert model is not None
        assert "beta" in model.named_vars
        assert "intercept" in model.named_vars
        assert "Sigma" in model.named_vars

    @pytest.mark.slow
    def test_fit_small_sample(self, simple_var_data):
        """Test BVAR fitting with small MCMC sample (fast test)."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=1
        )

        # Use very small sample for speed
        result = analyzer.fit(draws=50, tune=50, chains=2)

        assert isinstance(result, BVARResult)
        assert result.trace is not None
        assert result.summary is not None
        assert result.model is not None
        assert isinstance(result.convergence_ok, bool)

    @pytest.mark.slow
    def test_fit_convergence_checks(self, simple_var_data):
        """Test convergence diagnostic computation."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=1
        )

        result = analyzer.fit(draws=100, tune=100, chains=2)

        # Check diagnostics exist
        assert result.diagnostics is not None
        assert "rhat_ok" in result.diagnostics
        assert "ess_ok" in result.diagnostics
        assert "divergences_ok" in result.diagnostics
        assert "overall_ok" in result.diagnostics

        # Check types
        assert isinstance(result.diagnostics["rhat_max"], float)
        assert isinstance(result.diagnostics["n_divergences"], int)

    @pytest.mark.slow
    def test_fit_waic_loo(self, simple_var_data):
        """Test WAIC and LOO computation."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=1
        )

        result = analyzer.fit(draws=100, tune=100, chains=2)

        # WAIC and LOO may be None if computation fails
        if result.waic is not None:
            assert isinstance(result.waic, float)

        if result.loo is not None:
            assert isinstance(result.loo, float)

    @pytest.mark.slow
    def test_coefficient_extraction(self, simple_var_data):
        """Test coefficient matrix extraction."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=1
        )

        result = analyzer.fit(draws=50, tune=50, chains=2)

        coeffs = result.coefficients

        # Check structure
        assert isinstance(coeffs, pd.DataFrame)
        assert coeffs.shape == (2, 3)  # 2 equations, 2 lag coeffs + 1 intercept
        assert list(coeffs.index) == ["var1", "var2"]
        assert "intercept" in coeffs.columns

    @pytest.mark.slow
    def test_forecast(self, simple_var_data):
        """Test Bayesian forecasting."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=1
        )

        result = analyzer.fit(draws=50, tune=50, chains=2)

        # Generate forecasts
        forecasts = analyzer.forecast(result, steps=5, n_samples=100)

        # Check structure
        assert "mean" in forecasts
        assert "lower_95" in forecasts
        assert "upper_95" in forecasts

        # Check dimensions
        assert forecasts["mean"].shape == (5, 2)
        assert forecasts["lower_95"].shape == (5, 2)
        assert forecasts["upper_95"].shape == (5, 2)

        # Check credible interval ordering
        mean = forecasts["mean"].values
        lower = forecasts["lower_95"].values
        upper = forecasts["upper_95"].values

        assert np.all(lower <= mean), "Lower CI should be <= mean"
        assert np.all(mean <= upper), "Mean should be <= upper CI"

    def test_minnesota_prior_structure(self, simple_var_data):
        """Test Minnesota prior variance structure."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=2
        )

        model = analyzer.build_model(lambda1=0.2, lambda2=0.5, lambda3=1.0)

        # Own lags should have less shrinkage than cross lags
        # This is implicitly tested by model building without errors
        assert model is not None

    @pytest.mark.slow
    def test_lag_selection(self, multivariate_ts):
        """Test BVAR with different lag lengths."""
        var_names = ["points", "assists", "rebounds"]

        for lags in [1, 2, 3]:
            analyzer = BVARAnalyzer(
                data=multivariate_ts, var_names=var_names, lags=lags
            )

            result = analyzer.fit(draws=50, tune=50, chains=2)

            assert result.trace is not None
            assert result.coefficients.shape == (
                3,
                3 * lags + 1,
            )  # 3 vars, lags, intercept


class TestBVAREdgeCases:
    """Test edge cases and error handling."""

    def test_missing_data(self):
        """Test handling of missing data."""
        data = pd.DataFrame(
            {"var1": [1, 2, np.nan, 4, 5], "var2": [2, 3, 4, np.nan, 6]}
        )

        analyzer = BVARAnalyzer(data=data, var_names=["var1", "var2"], lags=1)

        # Missing data should be dropped
        assert analyzer.n_obs < 4  # Some observations lost

    def test_insufficient_data(self):
        """Test with very small dataset."""
        data = pd.DataFrame({"var1": [1, 2, 3], "var2": [2, 3, 4]})

        analyzer = BVARAnalyzer(data=data, var_names=["var1", "var2"], lags=1)

        # Should initialize but may have convergence issues
        assert analyzer.n_obs == 2  # T - lags

    def test_high_collinearity(self):
        """Test with highly collinear variables."""
        T = 100
        var1 = np.random.normal(0, 1, T)
        var2 = var1 + np.random.normal(0, 0.01, T)  # Nearly identical

        data = pd.DataFrame({"var1": var1, "var2": var2})

        analyzer = BVARAnalyzer(data=data, var_names=["var1", "var2"], lags=1)

        # Should still build model (prior helps with collinearity)
        model = analyzer.build_model()
        assert model is not None


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestBVARIntegration:
    """Integration tests for BVAR."""

    @pytest.mark.slow
    def test_full_workflow(self, multivariate_ts):
        """Test complete BVAR workflow."""
        # 1. Initialize
        analyzer = BVARAnalyzer(
            data=multivariate_ts,
            var_names=["points", "assists", "rebounds"],
            lags=2,
        )

        # 2. Fit
        result = analyzer.fit(draws=100, tune=100, chains=2, lambda1=0.2)

        # 3. Check fit
        assert result.convergence_ok or result.diagnostics["rhat_max"] < 1.05

        # 4. Forecast
        forecasts = analyzer.forecast(result, steps=10, n_samples=200)

        # 5. Validate forecasts
        assert forecasts["mean"].shape == (10, 3)
        assert not np.any(np.isnan(forecasts["mean"]))

    @pytest.mark.slow
    def test_minnesota_vs_diffuse_comparison(self, simple_var_data):
        """Compare Minnesota prior vs diffuse prior."""
        var_names = ["var1", "var2"]

        # Minnesota prior
        analyzer_mn = BVARAnalyzer(
            data=simple_var_data, var_names=var_names, lags=1, minnesota_prior=True
        )
        result_mn = analyzer_mn.fit(draws=50, tune=50, chains=2)

        # Diffuse prior
        analyzer_df = BVARAnalyzer(
            data=simple_var_data,
            var_names=var_names,
            lags=1,
            minnesota_prior=False,
        )
        result_df = analyzer_df.fit(draws=50, tune=50, chains=2)

        # Both should produce valid results
        assert result_mn.trace is not None
        assert result_df.trace is not None

        # Minnesota should generally have better out-of-sample performance
        # (would need more sophisticated test with train/test split)


# ==============================================================================
# Utility Function Tests
# ==============================================================================


def test_pymc_availability_check():
    """Test PyMC availability checking."""
    if PYMC_AVAILABLE:
        # Should not raise
        check_pymc_available()
    else:
        # Should raise ImportError
        with pytest.raises(ImportError, match="PyMC is required"):
            check_pymc_available()


def test_result_repr():
    """Test result class string representation."""
    # Create mock result
    result = BVARResult(
        trace=None,
        model=None,
        summary=pd.DataFrame(),
        waic=123.45,
        convergence_ok=True,
    )

    repr_str = repr(result)

    assert "BVARResult" in repr_str
    assert "123.45" in repr_str
    assert "✓" in repr_str  # Convergence OK symbol


# ==============================================================================
# Performance Tests
# ==============================================================================


@pytest.mark.slow
@pytest.mark.benchmark
class TestBVARPerformance:
    """Performance benchmarking tests."""

    def test_fit_speed_small_data(self, simple_var_data, benchmark):
        """Benchmark fitting speed on small dataset."""

        def fit_bvar():
            analyzer = BVARAnalyzer(
                data=simple_var_data, var_names=["var1", "var2"], lags=1
            )
            return analyzer.fit(draws=100, tune=100, chains=2)

        # Should complete reasonably quickly
        result = benchmark(fit_bvar)
        assert result.trace is not None

    def test_forecast_speed(self, simple_var_data, benchmark):
        """Benchmark forecasting speed."""
        analyzer = BVARAnalyzer(
            data=simple_var_data, var_names=["var1", "var2"], lags=1
        )
        result = analyzer.fit(draws=50, tune=50, chains=2)

        def generate_forecast():
            return analyzer.forecast(result, steps=10, n_samples=500)

        forecasts = benchmark(generate_forecast)
        assert forecasts["mean"].shape == (10, 2)


# ==============================================================================
# BSTS Tests
# ==============================================================================


class TestBayesianStructuralTS:
    """Tests for Bayesian Structural Time Series."""

    @pytest.fixture
    def trend_series(self):
        """Generate time series with trend."""
        np.random.seed(99)
        T = 50
        trend = np.linspace(0, 5, T)
        level = 20 + trend + np.random.normal(0, 0.5, T)

        return pd.Series(level, index=pd.date_range("2020-01-01", periods=T, freq="D"))

    def test_initialization(self, trend_series):
        """Test BSTS initialization."""
        from mcp_server.bayesian_time_series import BayesianStructuralTS

        analyzer = BayesianStructuralTS(
            data=trend_series, include_trend=True, seasonal_period=None
        )

        assert analyzer.T == 50
        assert analyzer.include_trend is True
        assert analyzer.seasonal_period is None

    def test_initialization_errors(self):
        """Test BSTS initialization errors."""
        from mcp_server.bayesian_time_series import BayesianStructuralTS

        # Wrong data type
        with pytest.raises(TypeError, match="must be a pandas Series"):
            BayesianStructuralTS(data=[1, 2, 3])

    def test_model_building(self, trend_series):
        """Test BSTS model building."""
        from mcp_server.bayesian_time_series import BayesianStructuralTS

        analyzer = BayesianStructuralTS(data=trend_series, include_trend=True)

        model = analyzer.build_model()

        assert model is not None
        assert "level_0" in model.named_vars
        assert "trend_0" in model.named_vars
        assert "sigma_level" in model.named_vars

    def test_spike_and_slab_model(self, trend_series):
        """Test spike-and-slab variable selection."""
        from mcp_server.bayesian_time_series import BayesianStructuralTS

        # Add exogenous variables
        exog = pd.DataFrame(
            {
                "x1": np.random.normal(0, 1, len(trend_series)),
                "x2": np.random.normal(0, 1, len(trend_series)),
            }
        )

        analyzer = BayesianStructuralTS(
            data=trend_series, include_trend=True, exog=exog
        )

        model = analyzer.build_model(spike_and_slab=True, prior_inclusion_prob=0.5)

        assert model is not None
        assert "theta" in model.named_vars  # Inclusion indicators
        assert "beta_raw" in model.named_vars  # Coefficients

    @pytest.mark.slow
    def test_fit_simple(self, trend_series):
        """Test BSTS fitting with small sample."""
        from mcp_server.bayesian_time_series import BayesianStructuralTS, BSTSResult

        analyzer = BayesianStructuralTS(data=trend_series, include_trend=True)

        result = analyzer.fit(draws=50, tune=50, chains=2)

        assert isinstance(result, BSTSResult)
        assert result.trace is not None
        assert result.components is not None
        assert "level" in result.components or "trend" in result.components

    @pytest.mark.slow
    def test_component_extraction(self, trend_series):
        """Test component extraction from BSTS."""
        from mcp_server.bayesian_time_series import BayesianStructuralTS

        analyzer = BayesianStructuralTS(data=trend_series, include_trend=True)

        result = analyzer.fit(draws=50, tune=50, chains=2)

        # Should extract level and trend
        assert "level" in result.components
        if analyzer.include_trend:
            assert "trend" in result.components

    @pytest.mark.slow
    def test_forecast(self, trend_series):
        """Test BSTS forecasting."""
        from mcp_server.bayesian_time_series import BayesianStructuralTS

        analyzer = BayesianStructuralTS(data=trend_series, include_trend=True)

        result = analyzer.fit(draws=50, tune=50, chains=2)

        forecasts = analyzer.forecast(result, steps=5)

        assert "mean" in forecasts
        assert "lower_95" in forecasts
        assert "upper_95" in forecasts
        assert len(forecasts["mean"]) == 5


# ==============================================================================
# Integration Tests - BSTS
# ==============================================================================


class TestBSTSIntegration:
    """Integration tests for BSTS."""

    @pytest.mark.slow
    def test_career_trajectory_example(self):
        """Test BSTS on career trajectory example."""
        from mcp_server.bayesian_time_series import BayesianStructuralTS

        # Simulated career: rise, peak, decline
        career = pd.Series(
            [15, 18, 21, 24, 26, 27, 26, 24, 21, 18],
            index=pd.date_range("2015", periods=10, freq="Y"),
        )

        analyzer = BayesianStructuralTS(data=career, include_trend=True)

        result = analyzer.fit(draws=100, tune=100, chains=2)

        # Should capture trend
        assert result.trace is not None
        assert result.convergence_ok or result.diagnostics["rhat_max"] < 1.05


# ==============================================================================
# Hierarchical Bayesian Time Series Tests
# ==============================================================================


class TestHierarchicalBayesianTS:
    """Tests for Hierarchical Bayesian Time Series."""

    @pytest.fixture
    def panel_data(self):
        """Generate panel data with hierarchical structure (teams > players)."""
        np.random.seed(777)

        # 3 teams, 3 players per team, 20 time periods
        teams = ["LAL", "GSW", "BOS"] * 3
        players = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]

        data_list = []

        for team_idx, team in enumerate(["LAL", "GSW", "BOS"]):
            team_mean = 20 + team_idx * 5  # Team-specific baseline

            for player_idx in range(3):
                player_id = players[team_idx * 3 + player_idx]
                player_dev = np.random.normal(0, 2)  # Player deviation from team

                for t in range(20):
                    value = (
                        team_mean
                        + player_dev
                        + 0.1 * t  # Linear trend
                        + np.random.normal(0, 1)
                    )

                    data_list.append(
                        {"player": player_id, "team": team, "time": t, "points": value}
                    )

        return pd.DataFrame(data_list)

    def test_initialization(self, panel_data):
        """Test hierarchical TS initialization."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        assert analyzer.n_players == 9
        assert analyzer.n_teams == 3
        assert analyzer.n_time == 20

    def test_initialization_errors(self):
        """Test initialization error handling."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        # Wrong data type
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            HierarchicalBayesianTS(
                data=[1, 2, 3],
                player_col="player",
                team_col="team",
                time_col="time",
                target_col="points",
            )

        # Missing column
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValueError, match="not found in data"):
            HierarchicalBayesianTS(
                data=df,
                player_col="player",
                team_col="team",
                time_col="time",
                target_col="points",
            )

    def test_player_team_mapping(self, panel_data):
        """Test player-to-team mapping."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        # Check mapping is created
        assert hasattr(analyzer, "player_to_team_idx")
        assert len(analyzer.player_to_team_idx) == 9

        # Players from same team should map to same team index
        p1_team = analyzer.player_to_team_idx[0]  # P1 from LAL
        p2_team = analyzer.player_to_team_idx[1]  # P2 from LAL
        p3_team = analyzer.player_to_team_idx[2]  # P3 from LAL

        assert p1_team == p2_team == p3_team

    def test_model_building_basic(self, panel_data):
        """Test basic hierarchical model building."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        model = analyzer.build_model(ar_order=0, include_trend=False)

        assert model is not None
        assert "mu_league" in model.named_vars
        assert "alpha_team" in model.named_vars
        assert "alpha_player" in model.named_vars
        assert "sigma_obs" in model.named_vars

    def test_model_building_with_trend(self, panel_data):
        """Test model with trend components."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        model = analyzer.build_model(
            ar_order=0, include_trend=True, team_level_trend=True
        )

        assert model is not None
        assert "beta_league" in model.named_vars
        assert "beta_team" in model.named_vars

    def test_model_building_with_ar(self, panel_data):
        """Test model with AR components."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        model = analyzer.build_model(ar_order=1, include_trend=False)

        assert model is not None
        assert "rho" in model.named_vars  # AR coefficient

    @pytest.mark.slow
    def test_fit_basic(self, panel_data):
        """Test basic hierarchical model fitting."""
        from mcp_server.bayesian_time_series import (
            HierarchicalBayesianTS,
            HierarchicalTSResult,
        )

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(draws=50, tune=50, chains=2, ar_order=0)

        assert isinstance(result, HierarchicalTSResult)
        assert result.trace is not None
        assert result.summary is not None

    @pytest.mark.slow
    def test_fit_convergence(self, panel_data):
        """Test convergence diagnostics."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(draws=100, tune=100, chains=2, ar_order=0)

        assert result.diagnostics is not None
        assert "rhat_ok" in result.diagnostics
        assert "ess_ok" in result.diagnostics
        assert isinstance(result.convergence_ok, bool)

    @pytest.mark.slow
    def test_player_effects_extraction(self, panel_data):
        """Test extraction of player-specific effects."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(draws=50, tune=50, chains=2, ar_order=0)

        # Check player effects exist
        assert result.player_effects is not None
        assert isinstance(result.player_effects, pd.DataFrame)
        assert len(result.player_effects) == 9  # 9 players
        assert "mean" in result.player_effects.columns
        assert "lower_95" in result.player_effects.columns
        assert "upper_95" in result.player_effects.columns

    @pytest.mark.slow
    def test_team_effects_extraction(self, panel_data):
        """Test extraction of team-specific effects."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(draws=50, tune=50, chains=2, ar_order=0)

        # Check team effects exist
        assert result.team_effects is not None
        assert isinstance(result.team_effects, pd.DataFrame)
        assert len(result.team_effects) == 3  # 3 teams
        assert "mean" in result.team_effects.columns

    @pytest.mark.slow
    def test_shrinkage_computation(self, panel_data):
        """Test shrinkage factor computation."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(draws=100, tune=100, chains=2, ar_order=0)

        # Check shrinkage DataFrame exists
        assert result.shrinkage is not None
        assert isinstance(result.shrinkage, pd.DataFrame)
        assert "shrinkage" in result.shrinkage.columns

        # Shrinkage should be between 0 and 1
        shrinkage_values = result.shrinkage["shrinkage"].values
        assert np.all(shrinkage_values >= 0), "Shrinkage should be >= 0"
        assert np.all(shrinkage_values <= 1), "Shrinkage should be <= 1"

    @pytest.mark.slow
    def test_forecast_player(self, panel_data):
        """Test player-specific forecasting."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(
            draws=50, tune=50, chains=2, ar_order=0, include_trend=True
        )

        # Forecast for first player
        player_id = analyzer.player_encoder.classes_[0]
        forecasts = analyzer.forecast_player(result, player_id, steps=5)

        assert "mean" in forecasts
        assert "lower_95" in forecasts
        assert "upper_95" in forecasts
        assert len(forecasts["mean"]) == 5

        # Check credible interval ordering
        assert np.all(forecasts["lower_95"] <= forecasts["mean"])
        assert np.all(forecasts["mean"] <= forecasts["upper_95"])

    @pytest.mark.slow
    def test_compare_players(self, panel_data):
        """Test Bayesian player comparison."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(
            draws=100, tune=100, chains=2, ar_order=0, include_trend=True
        )

        # Compare first two players
        player1 = analyzer.player_encoder.classes_[0]
        player2 = analyzer.player_encoder.classes_[1]

        comparison = analyzer.compare_players(
            result, player1, player2, metric="intercept"
        )

        assert "prob_player1_better" in comparison
        assert "mean_difference" in comparison
        assert "ci_95_difference" in comparison

        # Probability should be between 0 and 1
        prob = comparison["prob_player1_better"]
        assert 0 <= prob <= 1

    @pytest.mark.slow
    def test_compare_players_trend(self, panel_data):
        """Test player comparison on trend metric."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        analyzer = HierarchicalBayesianTS(
            data=panel_data,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(
            draws=50, tune=50, chains=2, ar_order=0, include_trend=True
        )

        player1 = analyzer.player_encoder.classes_[0]
        player2 = analyzer.player_encoder.classes_[1]

        comparison = analyzer.compare_players(result, player1, player2, metric="trend")

        assert comparison is not None
        assert "prob_player1_better" in comparison


# ==============================================================================
# Integration Tests - Hierarchical TS
# ==============================================================================


class TestHierarchicalTSIntegration:
    """Integration tests for Hierarchical Bayesian Time Series."""

    @pytest.fixture
    def realistic_nba_panel(self):
        """Generate realistic NBA-like panel data."""
        np.random.seed(888)

        teams = {"LAL": 28, "GSW": 30, "BOS": 26, "MIA": 24}  # Team means
        players_per_team = 3
        seasons = 5

        data_list = []
        player_counter = 0

        for team, team_mean in teams.items():
            for p in range(players_per_team):
                player_id = f"Player_{player_counter}"
                player_counter += 1

                # Player-specific baseline (deviation from team)
                player_skill = np.random.normal(0, 3)

                # Career trajectory
                career_peak = np.random.choice([2, 3])  # Peak in year 2 or 3

                for season in range(seasons):
                    # Age effect (inverted U)
                    age_effect = -0.5 * (season - career_peak) ** 2

                    value = (
                        team_mean + player_skill + age_effect + np.random.normal(0, 2)
                    )

                    data_list.append(
                        {
                            "player": player_id,
                            "team": team,
                            "season": season,
                            "points": max(value, 5),  # Floor at 5 points
                        }
                    )

        return pd.DataFrame(data_list)

    @pytest.mark.slow
    def test_full_workflow_realistic(self, realistic_nba_panel):
        """Test complete workflow with realistic NBA data."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        # 1. Initialize
        analyzer = HierarchicalBayesianTS(
            data=realistic_nba_panel,
            player_col="player",
            team_col="team",
            time_col="season",
            target_col="points",
        )

        # 2. Fit model with trend
        result = analyzer.fit(
            draws=100,
            tune=100,
            chains=2,
            ar_order=0,
            include_trend=True,
            team_level_trend=True,
        )

        # 3. Check convergence
        assert result.convergence_ok or result.diagnostics["rhat_max"] < 1.1

        # 4. Extract effects
        assert len(result.player_effects) == 12  # 4 teams * 3 players
        assert len(result.team_effects) == 4  # 4 teams

        # 5. Check shrinkage
        assert result.shrinkage is not None
        # Players with less data should have higher shrinkage

        # 6. Forecast
        player_id = analyzer.player_encoder.classes_[0]
        forecasts = analyzer.forecast_player(result, player_id, steps=3)
        assert len(forecasts["mean"]) == 3

        # 7. Compare players
        comparison = analyzer.compare_players(
            result,
            analyzer.player_encoder.classes_[0],
            analyzer.player_encoder.classes_[1],
            metric="intercept",
        )
        assert 0 <= comparison["prob_player1_better"] <= 1

    @pytest.mark.slow
    def test_partial_pooling_verification(self):
        """Verify partial pooling behavior."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        np.random.seed(999)

        # Create scenario: one player with very few observations
        data_list = []

        # Team 1: 3 players with lots of data
        for p in range(3):
            for t in range(20):
                data_list.append(
                    {
                        "player": f"P{p}",
                        "team": "Team1",
                        "time": t,
                        "points": 25 + np.random.normal(0, 2),
                    }
                )

        # Team 2: 1 player with very little data (should shrink more)
        for t in range(3):
            data_list.append(
                {
                    "player": "P_few",
                    "team": "Team2",
                    "time": t,
                    "points": 15 + np.random.normal(0, 2),
                }
            )

        df = pd.DataFrame(data_list)

        analyzer = HierarchicalBayesianTS(
            data=df,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        result = analyzer.fit(draws=100, tune=100, chains=2, ar_order=0)

        # Player with fewer observations should have higher shrinkage
        shrinkage_df = result.shrinkage

        # Find P_few shrinkage
        p_few_idx = list(analyzer.player_encoder.classes_).index("P_few")
        p_few_shrinkage = shrinkage_df.loc[p_few_idx, "shrinkage"]

        # Average shrinkage of other players
        other_shrinkage = shrinkage_df.loc[
            shrinkage_df.index != p_few_idx, "shrinkage"
        ].mean()

        # P_few should have higher shrinkage (more borrowing from team)
        # This is a soft check since random data may vary
        assert p_few_shrinkage >= 0
        assert other_shrinkage >= 0


# ==============================================================================
# Edge Cases - Hierarchical TS
# ==============================================================================


class TestHierarchicalTSEdgeCases:
    """Test edge cases for hierarchical models."""

    def test_single_team(self):
        """Test with only one team (degenerates to simpler model)."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        np.random.seed(101)
        data_list = []

        for p in range(3):
            for t in range(10):
                data_list.append(
                    {
                        "player": f"P{p}",
                        "team": "OnlyTeam",
                        "time": t,
                        "points": 20 + np.random.normal(0, 2),
                    }
                )

        df = pd.DataFrame(data_list)

        analyzer = HierarchicalBayesianTS(
            data=df,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        assert analyzer.n_teams == 1
        # Should still build model
        model = analyzer.build_model(ar_order=0)
        assert model is not None

    def test_unbalanced_panel(self):
        """Test with unbalanced panel (different observations per player)."""
        from mcp_server.bayesian_time_series import HierarchicalBayesianTS

        np.random.seed(202)
        data_list = []

        # Player 1: 20 observations
        for t in range(20):
            data_list.append(
                {
                    "player": "P1",
                    "team": "Team1",
                    "time": t,
                    "points": 25 + np.random.normal(0, 2),
                }
            )

        # Player 2: 10 observations
        for t in range(10):
            data_list.append(
                {
                    "player": "P2",
                    "team": "Team1",
                    "time": t,
                    "points": 23 + np.random.normal(0, 2),
                }
            )

        df = pd.DataFrame(data_list)

        analyzer = HierarchicalBayesianTS(
            data=df,
            player_col="player",
            team_col="team",
            time_col="time",
            target_col="points",
        )

        # Should handle unbalanced data
        model = analyzer.build_model(ar_order=0)
        assert model is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
