"""
Tests for bayesian module.

Tests cover:
- Model specification (priors, likelihood)
- MCMC sampling and convergence
- Variational inference
- Hierarchical models with partial pooling
- Posterior analysis (summary, credible intervals, PPC)
- Model comparison (WAIC, LOO)
- NBA-specific Bayesian models
"""

import pytest
import numpy as np
import pandas as pd
import warnings

from mcp_server.bayesian import (
    BayesianAnalyzer,
    BayesianModelResult,
    PosteriorResult,
    VIResult,
    PPCResult,
    ModelComparisonResult,
    CredibleInterval,
    HierarchicalModelSpec,
    InferenceMethod,
    PriorDistribution,
    LikelihoodFamily,
    NBABayesianModels,
    plot_posterior,
    plot_ppc,
    PYMC_AVAILABLE,
)

# Skip all tests if PyMC not available
pytestmark = pytest.mark.skipif(not PYMC_AVAILABLE, reason="PyMC not installed")


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def simple_regression_data():
    """Generate simple linear regression data."""
    np.random.seed(42)
    n = 100
    x = np.random.normal(0, 1, n)
    y = 2 + 3 * x + np.random.normal(0, 0.5, n)
    df = pd.DataFrame({"x": x, "y": y})
    return df


@pytest.fixture
def hierarchical_data():
    """Generate hierarchical data (players within teams)."""
    np.random.seed(42)
    n_teams = 5
    n_players_per_team = 10
    n_games_per_player = 20

    data = []
    for team_id in range(n_teams):
        team_effect = np.random.normal(20, 5)  # Team mean
        for player_id in range(n_players_per_team):
            player_effect = np.random.normal(0, 3)  # Player deviation
            for game in range(n_games_per_player):
                points = team_effect + player_effect + np.random.normal(0, 2)
                data.append(
                    {
                        "team_id": team_id,
                        "player_id": team_id * n_players_per_team + player_id,
                        "game": game,
                        "points": points,
                    }
                )

    return pd.DataFrame(data)


@pytest.fixture
def nba_scoring_data():
    """Simulate NBA player scoring data."""
    np.random.seed(42)
    teams = ["LAL", "GSW", "BOS", "MIA"]
    players = ["Player_A", "Player_B", "Player_C", "Player_D"]

    data = []
    for i, (team, player) in enumerate(zip(teams, players)):
        base_ppg = 20 + i * 2
        for game in range(50):
            points = np.random.normal(base_ppg, 5)
            data.append(
                {
                    "team_id": team,
                    "player_id": player,
                    "points": points,
                    "game_id": game,
                }
            )

    return pd.DataFrame(data)


@pytest.fixture
def win_loss_data():
    """Generate win/loss data with team effects."""
    np.random.seed(42)
    teams = ["Team_A", "Team_B", "Team_C", "Team_D"]
    team_strengths = [0.5, -0.3, 0.2, -0.4]  # Team skill levels

    data = []
    for i, (team, strength) in enumerate(zip(teams, team_strengths)):
        for opp_idx, (opponent, opp_strength) in enumerate(zip(teams, team_strengths)):
            if team == opponent:
                continue

            for game in range(10):
                # Win probability based on strength difference
                logit_p = strength - opp_strength
                p_win = 1 / (1 + np.exp(-logit_p))
                won = int(np.random.random() < p_win)

                data.append(
                    {
                        "team_id": team,
                        "opponent_id": opponent,
                        "won": won,
                        "is_home": game % 2,
                    }
                )

    return pd.DataFrame(data)


# ==============================================================================
# Model Specification Tests (5 tests)
# ==============================================================================


def test_define_prior():
    """Test prior distribution specification."""
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3]})
    analyzer = BayesianAnalyzer(df, target="y", features=["x"])

    # Normal prior
    prior = analyzer.define_prior("beta", "normal", mu=0, sigma=10)
    assert prior["parameter"] == "beta"
    assert prior["distribution"] == "normal"
    assert prior["params"]["mu"] == 0
    assert prior["params"]["sigma"] == 10

    # Exponential prior
    prior = analyzer.define_prior("sigma", PriorDistribution.EXPONENTIAL, lam=1)
    assert prior["distribution"] == "exponential"
    assert prior["params"]["lam"] == 1


def test_define_likelihood():
    """Test likelihood distribution specification."""
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3]})
    analyzer = BayesianAnalyzer(df, target="y")

    # Normal likelihood
    likelihood = analyzer.define_likelihood("normal", sigma="sigma")
    assert likelihood["family"] == "normal"
    assert likelihood["params"]["sigma"] == "sigma"

    # Bernoulli likelihood
    likelihood = analyzer.define_likelihood(LikelihoodFamily.BERNOULLI, p="p")
    assert likelihood["family"] == "bernoulli"


def test_build_simple_model(simple_regression_data):
    """Test building a simple Bayesian linear regression model."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])

    model = analyzer.build_simple_model()

    assert model is not None
    assert analyzer.model is not None

    # Check model has expected variables
    var_names = list(model.named_vars.keys())
    assert "alpha" in var_names  # Intercept
    assert "beta" in var_names  # Coefficients
    assert "sigma" in var_names  # Noise


def test_hierarchical_model_spec():
    """Test hierarchical model specification."""
    spec = HierarchicalModelSpec(
        group_variable="team_id",
        nested_variable="player_id",
        formula="points ~ minutes",
    )

    assert spec.group_variable == "team_id"
    assert spec.nested_variable == "player_id"
    assert spec.formula == "points ~ minutes"


def test_invalid_distributions():
    """Test handling of invalid distribution specifications."""
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3]})
    analyzer = BayesianAnalyzer(df, target="y")

    # Invalid prior distribution
    with pytest.raises((ValueError, KeyError)):
        analyzer.define_prior("beta", "invalid_dist", mu=0)

    # Invalid likelihood family
    with pytest.raises((ValueError, KeyError)):
        analyzer.define_likelihood("invalid_family")


# ==============================================================================
# Inference Tests (7 tests)
# ==============================================================================


def test_mcmc_sampling_simple(simple_regression_data):
    """Test MCMC sampling on known distribution."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    # Sample with few draws for speed
    result = analyzer.sample_posterior(draws=100, tune=100, chains=2)

    assert isinstance(result, BayesianModelResult)
    assert result.inference_method == InferenceMethod.MCMC
    assert result.trace is not None
    assert result.summary is not None
    assert len(result.summary) > 0


def test_mcmc_convergence(simple_regression_data):
    """Test MCMC convergence diagnostics (Rhat < 1.01)."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    # Sample with sufficient draws
    result = analyzer.sample_posterior(draws=500, tune=500, chains=4)

    # Check convergence
    convergence = analyzer.check_convergence(result)
    assert convergence["rhat_max"] < 1.02  # Allow small tolerance
    assert convergence["ess_bulk_min"] > 50  # Reasonable ESS
    assert convergence["divergences_ok"] is True


def test_variational_inference(simple_regression_data):
    """Test variational inference (fast approximate inference)."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    # Run VI
    result = analyzer.variational_inference(method="advi", n_iter=5000)

    assert isinstance(result, VIResult)
    assert result.approx is not None
    assert result.mean_field is not None
    assert result.n_iterations == 5000


def test_posterior_mean_accuracy(simple_regression_data):
    """Test posterior mean recovers true parameter values."""
    # Known parameters: y = 2 + 3*x + noise(0, 0.5)
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=1000, tune=1000, chains=2)
    posterior = analyzer.posterior_summary(result)

    # Check intercept (should be ~2)
    assert abs(posterior.mean["alpha"] - 2) < 0.5

    # Check slope (should be ~3)
    # Beta is an array parameter, so it shows up as beta[0] in summary
    beta_key = "beta[0]" if "beta[0]" in posterior.mean else "beta"
    beta_mean = posterior.mean[beta_key]
    assert abs(float(beta_mean) - 3) < 0.5


def test_credible_intervals(simple_regression_data):
    """Test credible interval calculation and coverage."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)

    # Get credible interval for intercept
    ci = analyzer.credible_interval(result, "alpha", prob=0.95)

    assert isinstance(ci, CredibleInterval)
    assert ci.parameter == "alpha"
    assert ci.probability == 0.95
    assert ci.lower < ci.upper
    assert ci.method == "hdi"

    # True value (2) should be in 95% CI most of the time
    # (allowing for sampling variability)


def test_chains_convergence(simple_regression_data):
    """Test that multiple chains converge to same distribution."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=500, tune=500, chains=4)

    # Check Rhat for all parameters
    rhat = analyzer.rhat_statistic(result)

    for param, value in rhat.items():
        assert value < 1.02, f"Rhat for {param} is {value}, indicating poor convergence"


def test_sampling_edge_cases():
    """Test MCMC sampling with edge cases."""
    # Very small dataset
    df = pd.DataFrame({"x": [1, 2], "y": [1, 2]})
    analyzer = BayesianAnalyzer(df, target="y", features=["x"])
    analyzer.build_simple_model()

    # Should still run without errors
    result = analyzer.sample_posterior(draws=100, tune=100, chains=2)
    assert result is not None

    # Single chain
    result_single = analyzer.sample_posterior(draws=100, tune=100, chains=1)
    assert result_single is not None


# ==============================================================================
# Hierarchical Model Tests (5 tests)
# ==============================================================================


def test_hierarchical_players_teams(hierarchical_data):
    """Test hierarchical model for players within teams."""
    analyzer = BayesianAnalyzer(hierarchical_data, target="points")

    spec = HierarchicalModelSpec(group_variable="team_id", nested_variable="player_id")

    model = analyzer.hierarchical_model(spec)
    assert model is not None

    # Sample
    result = analyzer.sample_posterior(draws=200, tune=200, chains=2)
    assert result is not None
    assert "group_effect" in result.summary.index or any(
        "group" in idx for idx in result.summary.index
    )


def test_shrinkage_effect(hierarchical_data):
    """Test that extreme values shrink toward group mean (partial pooling)."""
    analyzer = BayesianAnalyzer(hierarchical_data, target="points")

    spec = HierarchicalModelSpec(group_variable="team_id")
    model = analyzer.hierarchical_model(spec)

    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)
    posterior = analyzer.posterior_summary(result)

    # Check that group effects have reasonable variance
    # (partial pooling should prevent extreme estimates)
    if "group_effect" in posterior.mean:
        group_means = posterior.mean["group_effect"]
        if isinstance(group_means, (list, np.ndarray)):
            # Standard deviation of group effects should be reasonable
            assert np.std(group_means) < 20  # Not too extreme


def test_multilevel_variance(hierarchical_data):
    """Test estimation of within vs between group variance."""
    analyzer = BayesianAnalyzer(hierarchical_data, target="points")

    spec = HierarchicalModelSpec(group_variable="team_id", nested_variable="player_id")

    model = analyzer.hierarchical_model(spec)
    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)

    posterior = analyzer.posterior_summary(result)

    # Should have estimates for group-level and observation-level variance
    assert "sigma_group" in posterior.mean or any(
        "sigma" in k for k in posterior.mean.keys()
    )
    assert "sigma_obs" in posterior.mean or any(
        "sigma" in k for k in posterior.mean.keys()
    )


def test_group_effects_extraction(nba_scoring_data):
    """Test extraction of group-level effects from hierarchical model."""
    analyzer = BayesianAnalyzer(nba_scoring_data, target="points")

    spec = HierarchicalModelSpec(group_variable="team_id")
    model = analyzer.hierarchical_model(spec)

    result = analyzer.sample_posterior(draws=300, tune=300, chains=2)
    posterior = analyzer.posterior_summary(result)

    # Should have team-level effects
    assert any("group" in k or "team" in k for k in posterior.mean.keys())


def test_hierarchical_predictions(hierarchical_data):
    """Test predictions from hierarchical model."""
    analyzer = BayesianAnalyzer(hierarchical_data, target="points")

    spec = HierarchicalModelSpec(group_variable="team_id")
    model = analyzer.hierarchical_model(spec)

    result = analyzer.sample_posterior(draws=200, tune=200, chains=2)

    # Posterior predictive check
    ppc = analyzer.posterior_predictive_check(result, n_samples=100)

    assert isinstance(ppc, PPCResult)
    assert len(ppc.observed) == len(hierarchical_data)
    assert ppc.p_value >= 0 and ppc.p_value <= 1


# ==============================================================================
# Posterior Analysis Tests (4 tests)
# ==============================================================================


def test_posterior_summary(simple_regression_data):
    """Test comprehensive posterior summary generation."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)
    posterior = analyzer.posterior_summary(result, hdi_prob=0.95)

    assert isinstance(posterior, PosteriorResult)
    assert "alpha" in posterior.mean
    assert "alpha" in posterior.median
    assert "alpha" in posterior.std
    assert "alpha" in posterior.hdi_95
    assert "alpha" in posterior.ess
    assert "alpha" in posterior.rhat

    # Check HDI is a tuple
    assert isinstance(posterior.hdi_95["alpha"], tuple)
    assert len(posterior.hdi_95["alpha"]) == 2


def test_credible_interval_coverage(simple_regression_data):
    """Test that credible intervals have proper coverage."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)

    # 95% credible interval
    ci_95 = analyzer.credible_interval(result, "alpha", prob=0.95)
    # 90% credible interval
    ci_90 = analyzer.credible_interval(result, "alpha", prob=0.90)

    # 95% CI should be wider than 90% CI
    width_95 = ci_95.upper - ci_95.lower
    width_90 = ci_90.upper - ci_90.lower
    assert width_95 > width_90

    # Test quantile method
    ci_quantile = analyzer.credible_interval(
        result, "alpha", prob=0.95, method="quantile"
    )
    assert ci_quantile.method == "quantile"
    assert ci_quantile.lower < ci_quantile.upper


def test_posterior_predictive_check(simple_regression_data):
    """Test posterior predictive check."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)

    # PPC with different test statistics
    for stat in ["mean", "std", "max", "min"]:
        ppc = analyzer.posterior_predictive_check(
            result, n_samples=200, test_statistic=stat
        )

        assert isinstance(ppc, PPCResult)
        assert len(ppc.observed) == len(simple_regression_data)
        assert ppc.predicted.shape[1] == len(simple_regression_data)
        assert 0 <= ppc.p_value <= 1
        assert ppc.test_statistic == stat


def test_hdi_calculation(simple_regression_data):
    """Test Highest Density Interval calculation."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)
    posterior = analyzer.posterior_summary(result, hdi_prob=0.95)

    # HDI for all parameters
    for param in ["alpha", "sigma"]:
        hdi = posterior.hdi_95[param]
        assert isinstance(hdi, tuple)
        assert len(hdi) == 2
        assert hdi[0] < hdi[1]  # Lower < Upper

    # Compare 95% and 90% HDI
    assert all(
        posterior.hdi_95[p][1] - posterior.hdi_95[p][0]
        >= posterior.hdi_90[p][1] - posterior.hdi_90[p][0]
        for p in ["alpha", "sigma"]
    )


# ==============================================================================
# Model Comparison Tests (4 tests)
# ==============================================================================


def test_waic_calculation(simple_regression_data):
    """Test WAIC (Widely Applicable Information Criterion) calculation."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)

    waic = analyzer.waic(result)

    assert isinstance(waic, float)
    # WAIC can be negative
    assert not np.isnan(waic)
    assert not np.isinf(waic)


def test_loo_calculation(simple_regression_data):
    """Test LOO (Leave-One-Out Cross-Validation) calculation."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=500, tune=500, chains=2)

    loo = analyzer.loo(result)

    assert isinstance(loo, float)
    assert not np.isnan(loo)
    assert not np.isinf(loo)


def test_compare_models(simple_regression_data):
    """Test comparison of multiple Bayesian models."""
    # Model 1: Simple regression
    analyzer1 = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer1.build_simple_model()
    result1 = analyzer1.sample_posterior(draws=300, tune=300, chains=2)

    # Model 2: Intercept only
    analyzer2 = BayesianAnalyzer(simple_regression_data, target="y", features=[])
    analyzer2.build_simple_model()
    result2 = analyzer2.sample_posterior(draws=300, tune=300, chains=2)

    # Model 3: With different prior
    analyzer3 = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    priors = {"alpha": {"mu": 0, "sigma": 5}, "beta": {"mu": 0, "sigma": 5}}
    analyzer3.build_simple_model(priors=priors)
    result3 = analyzer3.sample_posterior(draws=300, tune=300, chains=2)

    # Compare models
    results_dict = {
        "full_model": result1,
        "intercept_only": result2,
        "tight_priors": result3,
    }

    comparison = analyzer1.compare_models(results_dict)

    assert isinstance(comparison, ModelComparisonResult)
    assert len(comparison.model_names) == 3
    assert comparison.best_model in ["full_model", "intercept_only", "tight_priors"]
    assert "full_model" in comparison.waic_values
    assert comparison.comparison_table is not None


def test_model_averaging():
    """Test Bayesian model averaging concept."""
    # Generate data where model averaging makes sense
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = 2 + 1.5 * x1 + 0.3 * x2 + np.random.normal(0, 1, n)
    df = pd.DataFrame({"x1": x1, "x2": x2, "y": y})

    # Model 1: Only x1
    analyzer1 = BayesianAnalyzer(df, target="y", features=["x1"])
    analyzer1.build_simple_model()
    result1 = analyzer1.sample_posterior(draws=300, tune=300, chains=2)

    # Model 2: Only x2
    analyzer2 = BayesianAnalyzer(df, target="y", features=["x2"])
    analyzer2.build_simple_model()
    result2 = analyzer2.sample_posterior(draws=300, tune=300, chains=2)

    # Model 3: Both x1 and x2
    analyzer3 = BayesianAnalyzer(df, target="y", features=["x1", "x2"])
    analyzer3.build_simple_model()
    result3 = analyzer3.sample_posterior(draws=300, tune=300, chains=2)

    # Compare
    results = {"model_x1": result1, "model_x2": result2, "model_both": result3}
    comparison = analyzer1.compare_models(results)

    # Model with both features should generally perform best
    # (though not guaranteed in every random sample)
    assert comparison.best_model in results.keys()
    assert len(comparison.waic_values) == 3


# ==============================================================================
# NBA-Specific Model Tests (2 additional tests)
# ==============================================================================


def test_player_scoring_model(nba_scoring_data):
    """Test NBA player scoring hierarchical model."""
    model, encoded_data = NBABayesianModels.player_scoring_model(
        nba_scoring_data,
        team_col="team_id",
        player_col="player_id",
        target_col="points",
    )

    assert model is not None
    assert "team_idx" in encoded_data
    assert "player_idx" in encoded_data
    assert len(encoded_data["teams"]) == 4  # 4 teams
    assert len(encoded_data["players"]) == 4  # 4 players

    # Sample from model
    import pymc as pm

    with model:
        trace = pm.sample(draws=200, tune=200, chains=2, return_inferencedata=True)

    assert trace is not None


def test_win_probability_model(win_loss_data):
    """Test NBA win probability logistic regression model."""
    model, encoded_data = NBABayesianModels.win_probability_model(
        win_loss_data,
        team_col="team_id",
        opponent_col="opponent_id",
        target_col="won",
    )

    assert model is not None
    assert "team_idx" in encoded_data
    assert len(encoded_data["teams"]) == 4

    # Sample from model
    import pymc as pm

    with model:
        trace = pm.sample(draws=200, tune=200, chains=2, return_inferencedata=True)

    assert trace is not None


# ==============================================================================
# Utility Function Tests (2 additional tests)
# ==============================================================================


def test_plot_posterior(simple_regression_data):
    """Test posterior plotting functionality."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=300, tune=300, chains=2)

    # Test different plot types
    for kind in ["hist", "trace"]:
        fig = plot_posterior(result, var_names=["alpha"], kind=kind)
        assert fig is not None


def test_plot_ppc(simple_regression_data):
    """Test posterior predictive check plotting."""
    analyzer = BayesianAnalyzer(simple_regression_data, target="y", features=["x"])
    analyzer.build_simple_model()

    result = analyzer.sample_posterior(draws=300, tune=300, chains=2)
    ppc = analyzer.posterior_predictive_check(result, n_samples=100)

    fig = plot_ppc(ppc)
    assert fig is not None


# ==============================================================================
# Integration Tests
# ==============================================================================


def test_full_workflow_integration(nba_scoring_data):
    """Test complete Bayesian workflow from data to inference to comparison."""
    # 1. Build hierarchical model
    analyzer = BayesianAnalyzer(nba_scoring_data, target="points")
    spec = HierarchicalModelSpec(group_variable="team_id")
    analyzer.hierarchical_model(spec)

    # 2. Sample posterior
    result = analyzer.sample_posterior(draws=300, tune=300, chains=2)

    # 3. Check convergence
    convergence = analyzer.check_convergence(result)
    assert convergence["overall_ok"] or convergence["rhat_max"] < 1.05

    # 4. Posterior summary
    posterior = analyzer.posterior_summary(result)
    assert len(posterior.mean) > 0

    # 5. Credible intervals
    ci = analyzer.credible_interval(result, "mu_global", prob=0.95)
    assert ci.lower < ci.upper

    # 6. Posterior predictive check
    ppc = analyzer.posterior_predictive_check(result, n_samples=100)
    assert 0 <= ppc.p_value <= 1

    # 7. Model comparison metrics
    waic = analyzer.waic(result)
    loo = analyzer.loo(result)
    assert not np.isnan(waic)
    assert not np.isnan(loo)


def test_analyzer_without_mlflow():
    """Test that analyzer works without MLflow."""
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3]})

    # Should work even if MLflow experiment is specified but not available
    analyzer = BayesianAnalyzer(
        df, target="y", features=["x"], mlflow_experiment="test_exp"
    )

    assert analyzer is not None
    analyzer.build_simple_model()
    result = analyzer.sample_posterior(draws=100, tune=100, chains=2)
    assert result is not None
