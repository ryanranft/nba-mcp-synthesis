"""
Visualization Utilities for Bayesian Time Series Methods.

Provides plotting functions for BVAR, BSTS, Hierarchical TS, and Particle Filters.

Functions:
----------
BVAR Visualizations:
- plot_irf: Impulse response functions with credible intervals
- plot_fevd: Forecast error variance decomposition
- plot_bvar_forecast: Multi-step ahead forecasts
- plot_bvar_diagnostics: Convergence diagnostics

BSTS Visualizations:
- plot_bsts_components: Decompose time series into components
- plot_bsts_forecast: Forecast with uncertainty
- plot_variable_selection: Spike-and-slab inclusion probabilities

Hierarchical TS Visualizations:
- plot_hierarchical_effects: Player and team effects
- plot_shrinkage: Shrinkage estimates
- plot_player_comparison: Bayesian player comparisons

Particle Filter Visualizations:
- plot_particle_cloud: Particle distribution over time
- plot_state_evolution: State trajectory with uncertainty
- plot_win_probability: Live game win probability

Dependencies:
-------------
- matplotlib >= 3.6.0
- seaborn >= 0.12.0
- numpy >= 1.24.0
- pandas >= 1.5.0

Author: NBA MCP Synthesis
Date: November 2025
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple

# Set default style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10


# ==============================================================================
# BVAR Visualizations
# ==============================================================================


def plot_irf(
    irf_results: Dict[str, np.ndarray],
    var_names: List[str],
    shock_var: Optional[int] = None,
    response_var: Optional[int] = None,
    figsize: Tuple[int, int] = (14, 10),
    save_path: Optional[str] = None,
):
    """
    Plot Impulse Response Functions with credible intervals.

    Parameters
    ----------
    irf_results : Dict[str, np.ndarray]
        IRF results from BVARAnalyzer.impulse_response()
    var_names : List[str]
        Variable names
    shock_var : Optional[int]
        If specified, plot only responses to this shock
    response_var : Optional[int]
        If specified, plot only this variable's responses
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> irf = analyzer.impulse_response(result, horizon=20)
    >>> plot_irf(irf, var_names=['points', 'assists', 'rebounds'])
    """
    irf_mean = irf_results["irf_mean"]
    irf_lower = irf_results["irf_lower"]
    irf_upper = irf_results["irf_upper"]

    horizon, n_vars, _ = irf_mean.shape

    if shock_var is not None and response_var is not None:
        # Plot single IRF
        fig, ax = plt.subplots(figsize=(8, 5))
        _plot_single_irf(
            ax,
            irf_mean[:, response_var, shock_var],
            irf_lower[:, response_var, shock_var],
            irf_upper[:, response_var, shock_var],
            f"Response of {var_names[response_var]} to {var_names[shock_var]} shock",
        )
    else:
        # Plot grid
        fig, axes = plt.subplots(n_vars, n_vars, figsize=figsize, sharex=True)

        for i in range(n_vars):
            for j in range(n_vars):
                ax = axes[i, j] if n_vars > 1 else axes

                _plot_single_irf(
                    ax,
                    irf_mean[:, i, j],
                    irf_lower[:, i, j],
                    irf_upper[:, i, j],
                    f"{var_names[i]} ← {var_names[j]}",
                )

                # Only show x-label on bottom row
                if i == n_vars - 1:
                    ax.set_xlabel("Horizon")

                # Only show y-label on left column
                if j == 0:
                    ax.set_ylabel("Response")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def _plot_single_irf(ax, mean, lower, upper, title):
    """Helper to plot single IRF with credible interval."""
    horizon = len(mean)
    ax.plot(range(horizon), mean, "b-", linewidth=2, label="Mean")
    ax.fill_between(range(horizon), lower, upper, alpha=0.3, color="b", label="95% CI")
    ax.axhline(0, color="k", linestyle="--", linewidth=0.8)
    ax.set_title(title, fontsize=9)
    ax.grid(True, alpha=0.3)


def plot_fevd(
    fevd_results: Dict[str, np.ndarray],
    var_names: List[str],
    response_var: int = 0,
    plot_type: str = "stacked",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None,
):
    """
    Plot Forecast Error Variance Decomposition.

    Parameters
    ----------
    fevd_results : Dict[str, np.ndarray]
        FEVD results from BVARAnalyzer.forecast_error_variance_decomposition()
    var_names : List[str]
        Variable names
    response_var : int
        Variable to plot FEVD for
    plot_type : str
        'stacked' for stacked area, 'heatmap' for all variables
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> fevd = analyzer.forecast_error_variance_decomposition(result, horizon=20)
    >>> plot_fevd(fevd, var_names=['points', 'assists', 'rebounds'], response_var=0)
    """
    fevd_mean = fevd_results["fevd_mean"]
    horizon, n_vars, _ = fevd_mean.shape

    if plot_type == "stacked":
        # Stacked area chart for one variable
        fig, ax = plt.subplots(figsize=figsize)

        # Stack FEVDs
        fevd_var = fevd_mean[:, response_var, :]  # (horizon, n_vars)

        ax.stackplot(
            range(horizon),
            *[fevd_var[:, j] for j in range(n_vars)],
            labels=var_names,
            alpha=0.7,
        )

        ax.set_xlabel("Horizon", fontsize=12)
        ax.set_ylabel("Fraction of Forecast Error Variance", fontsize=12)
        ax.set_title(
            f"FEVD of {var_names[response_var]}: Contribution by Shock Source",
            fontsize=14,
        )
        ax.legend(loc="best", fontsize=10)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)

    elif plot_type == "heatmap":
        # Heatmap for all variables at specific horizon
        final_horizon = horizon - 1
        fevd_final = fevd_mean[final_horizon, :, :]  # (n_vars, n_vars)

        fig, ax = plt.subplots(figsize=(8, 7))

        sns.heatmap(
            fevd_final * 100,  # Convert to percentage
            annot=True,
            fmt=".1f",
            cmap="YlOrRd",
            xticklabels=var_names,
            yticklabels=var_names,
            cbar_kws={"label": "% of Forecast Error Variance"},
            ax=ax,
        )

        ax.set_title(f"FEVD at Horizon {final_horizon}", fontsize=14)
        ax.set_xlabel("Shock Source", fontsize=12)
        ax.set_ylabel("Response Variable", fontsize=12)

    else:
        raise ValueError(f"Unknown plot_type: {plot_type}")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_bvar_forecast(
    forecasts: Dict[str, pd.DataFrame],
    historical_data: pd.DataFrame,
    var_names: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (14, 8),
    save_path: Optional[str] = None,
):
    """
    Plot BVAR forecasts with credible intervals.

    Parameters
    ----------
    forecasts : Dict[str, pd.DataFrame]
        Forecast results from BVARAnalyzer.forecast()
    historical_data : pd.DataFrame
        Historical data
    var_names : Optional[List[str]]
        Variables to plot (default: all)
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> forecasts = analyzer.forecast(result, steps=10)
    >>> plot_bvar_forecast(forecasts, analyzer.data)
    """
    mean = forecasts["mean"]
    lower = forecasts["lower_95"]
    upper = forecasts["upper_95"]

    if var_names is None:
        var_names = mean.columns.tolist()

    n_vars = len(var_names)

    fig, axes = plt.subplots(n_vars, 1, figsize=figsize, sharex=True)

    if n_vars == 1:
        axes = [axes]

    for idx, var in enumerate(var_names):
        ax = axes[idx]

        # Historical data
        hist_len = len(historical_data)
        ax.plot(
            range(hist_len),
            historical_data[var],
            "k-",
            linewidth=1.5,
            label="Historical",
        )

        # Forecast
        forecast_x = range(hist_len, hist_len + len(mean))
        ax.plot(forecast_x, mean[var], "b-", linewidth=2, label="Forecast")
        ax.fill_between(
            forecast_x, lower[var], upper[var], alpha=0.3, color="b", label="95% CI"
        )

        ax.set_ylabel(var, fontsize=11)
        ax.grid(True, alpha=0.3)

        if idx == 0:
            ax.legend(loc="best")

    axes[-1].set_xlabel("Time", fontsize=12)
    plt.suptitle("BVAR Forecasts with 95% Credible Intervals", fontsize=14)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


# ==============================================================================
# Hierarchical TS Visualizations
# ==============================================================================


def plot_hierarchical_effects(
    result,
    analyzer,
    effect_type: str = "player",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None,
):
    """
    Plot hierarchical effects with credible intervals.

    Parameters
    ----------
    result : HierarchicalTSResult
        Result from HierarchicalBayesianTS.fit()
    analyzer : HierarchicalBayesianTS
        Fitted analyzer
    effect_type : str
        'player' or 'team'
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> plot_hierarchical_effects(result, analyzer, effect_type='player')
    """
    fig, ax = plt.subplots(figsize=figsize)

    if effect_type == "player":
        effects = result.player_effects
        names = analyzer.player_encoder.classes_
        title = "Player Effects (Deviations from Team Mean)"
    else:
        effects = result.team_effects
        names = analyzer.team_encoder.classes_
        title = "Team Effects (Deviations from League Mean)"

    # Sort by mean effect
    effects = effects.sort_values("mean")

    y_pos = np.arange(len(effects))

    ax.barh(
        y_pos,
        effects["mean"],
        xerr=effects["mean"] - effects["lower_95"],
        capsize=3,
        alpha=0.7,
        color="steelblue",
    )
    ax.axvline(0, color="k", linestyle="--", linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names[effects.index], fontsize=9)
    ax.set_xlabel("Effect Size", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_shrinkage(
    result,
    analyzer,
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None,
):
    """
    Plot shrinkage estimates for players.

    Parameters
    ----------
    result : HierarchicalTSResult
        Result from HierarchicalBayesianTS.fit()
    analyzer : HierarchicalBayesianTS
        Fitted analyzer
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> plot_shrinkage(result, analyzer)
    """
    fig, ax = plt.subplots(figsize=figsize)

    shrinkage = result.shrinkage.sort_values("shrinkage")
    names = analyzer.player_encoder.classes_

    y_pos = np.arange(len(shrinkage))

    ax.barh(y_pos, shrinkage["shrinkage"], alpha=0.7, color="coral")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names[shrinkage.index], fontsize=9)
    ax.set_xlabel("Shrinkage (0=No pooling, 1=Complete pooling)", fontsize=12)
    ax.set_title("Player Shrinkage Estimates: Borrowing from Team Mean", fontsize=14)
    ax.set_xlim(0, 1)
    ax.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_player_comparison(
    comparison: Dict,
    player1_name: str,
    player2_name: str,
    metric: str = "intercept",
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None,
):
    """
    Plot Bayesian player comparison.

    Parameters
    ----------
    comparison : Dict
        Result from HierarchicalBayesianTS.compare_players()
    player1_name : str
        First player name
    player2_name : str
        Second player name
    metric : str
        Metric being compared
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> comp = analyzer.compare_players(result, 'Player1', 'Player2')
    >>> plot_player_comparison(comp, 'Player1', 'Player2')
    """
    fig, ax = plt.subplots(figsize=figsize)

    prob = comparison["prob_player1_better"]
    mean_diff = comparison["mean_difference"]
    ci_lower, ci_upper = comparison["ci_95_difference"]

    # Bar chart showing probability
    ax.barh([0], [prob], color="green" if prob > 0.5 else "red", alpha=0.7)
    ax.axvline(0.5, color="k", linestyle="--", linewidth=1, label="Even odds")
    ax.set_yticks([0])
    ax.set_yticklabels([f"{player1_name} vs {player2_name}"])
    ax.set_xlabel(f"P({player1_name} > {player2_name})", fontsize=12)
    ax.set_xlim(0, 1)
    ax.set_title(
        f"Bayesian Comparison on {metric.capitalize()}\n"
        f"Mean difference: {mean_diff:.2f} [95% CI: {ci_lower:.2f}, {ci_upper:.2f}]",
        fontsize=13,
    )
    ax.legend()

    # Add text annotation
    ax.text(
        prob,
        0,
        f" {prob:.1%}",
        ha="left" if prob < 0.5 else "right",
        va="center",
        fontsize=12,
        fontweight="bold",
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


# ==============================================================================
# Particle Filter Visualizations
# ==============================================================================


def plot_state_evolution(
    result,
    state_names: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (14, 8),
    save_path: Optional[str] = None,
):
    """
    Plot particle filter state evolution with uncertainty.

    Parameters
    ----------
    result : ParticleFilterResult or PlayerPerformanceResult
        Filter result
    state_names : Optional[List[str]]
        Names for state dimensions
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> result = pf.filter_player_season(data, target_col='points')
    >>> plot_state_evolution(result, state_names=['skill', 'form'])
    """
    states = result.states
    state_variance = result.state_variance
    T, state_dim = states.shape

    if state_names is None:
        state_names = [f"State {i}" for i in range(state_dim)]

    fig, axes = plt.subplots(state_dim, 1, figsize=figsize, sharex=True)

    if state_dim == 1:
        axes = [axes]

    for dim in range(state_dim):
        ax = axes[dim]

        mean = states[:, dim]
        std = np.sqrt(state_variance[:, dim])

        ax.plot(range(T), mean, "b-", linewidth=2, label="Estimated state")
        ax.fill_between(
            range(T),
            mean - 2 * std,
            mean + 2 * std,
            alpha=0.3,
            color="b",
            label="95% CI",
        )

        ax.set_ylabel(state_names[dim], fontsize=11)
        ax.grid(True, alpha=0.3)

        if dim == 0:
            ax.legend(loc="best")

    axes[-1].set_xlabel("Time", fontsize=12)
    plt.suptitle("State Evolution with Uncertainty", fontsize=14)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_win_probability(
    result,
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None,
):
    """
    Plot live game win probability evolution.

    Parameters
    ----------
    result : GameStateResult
        Result from LiveGameProbabilityFilter.track_game()
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> result = pf.track_game(score_updates)
    >>> plot_win_probability(result)
    """
    fig, ax = plt.subplots(figsize=figsize)

    time_points = result.time_points
    win_probs = result.win_probabilities

    ax.plot(time_points, win_probs, "b-", linewidth=3)
    ax.fill_between(
        time_points,
        0.5,
        win_probs,
        where=(np.array(win_probs) >= 0.5),
        alpha=0.3,
        color="green",
        label="Home favored",
    )
    ax.fill_between(
        time_points,
        win_probs,
        0.5,
        where=(np.array(win_probs) < 0.5),
        alpha=0.3,
        color="red",
        label="Away favored",
    )

    ax.axhline(0.5, color="k", linestyle="--", linewidth=1, alpha=0.5)
    ax.set_xlabel("Game Time (minutes)", fontsize=12)
    ax.set_ylabel("Home Team Win Probability", fontsize=12)
    ax.set_title("Live Win Probability Tracker", fontsize=14)
    ax.set_ylim(0, 1)
    ax.set_xlim(0, 48)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    # Add final probability text
    final_prob = win_probs[-1]
    ax.text(
        time_points[-1],
        final_prob,
        f" Final: {final_prob:.1%}",
        ha="left",
        va="center",
        fontsize=11,
        fontweight="bold",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_ess_history(
    result,
    figsize: Tuple[int, int] = (12, 5),
    save_path: Optional[str] = None,
):
    """
    Plot Effective Sample Size (ESS) over time.

    Parameters
    ----------
    result : ParticleFilterResult
        Filter result
    figsize : Tuple[int, int]
        Figure size
    save_path : Optional[str]
        Path to save figure

    Examples
    --------
    >>> plot_ess_history(result)
    """
    fig, ax = plt.subplots(figsize=figsize)

    ess_history = result.ess_history
    resampling_history = result.resampling_history

    ax.plot(ess_history, "b-", linewidth=2, label="ESS")

    # Mark resampling points
    resampling_times = [t for t, r in enumerate(resampling_history) if r]
    ax.scatter(
        resampling_times,
        [ess_history[t] for t in resampling_times],
        color="red",
        s=100,
        marker="x",
        label="Resampling",
        zorder=5,
    )

    ax.axhline(
        len(result.weights) * 0.5,
        color="orange",
        linestyle="--",
        label="Threshold (50%)",
        alpha=0.7,
    )

    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Effective Sample Size", fontsize=12)
    ax.set_title("Particle Filter Degeneracy Monitoring", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig
