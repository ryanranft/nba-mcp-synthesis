"""
Visualize Bayesian Methods Benchmark Results.

Creates comprehensive plots from benchmark data.

Usage:
    python scripts/visualize_benchmarks.py benchmark_results.json

Output:
    benchmark_visualization.png - Multi-panel figure
"""

import json
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (16, 12)
plt.rcParams["font.size"] = 10


def load_results(filepath):
    """Load benchmark results from JSON."""
    with open(filepath, "r") as f:
        return json.load(f)


def create_visualization(results, output_path="benchmark_visualization.png"):
    """Create comprehensive visualization of benchmark results."""
    df = pd.DataFrame(results)

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # 1. Execution Time by Method
    ax1 = fig.add_subplot(gs[0, 0])
    methods = df.groupby("method")["execution_time"].agg(["mean", "std", "min", "max"])
    methods = methods.sort_values("mean")

    ax1.barh(
        methods.index,
        methods["mean"],
        xerr=methods["std"],
        alpha=0.7,
        color="steelblue",
        capsize=5,
    )
    ax1.set_xlabel("Execution Time (seconds)")
    ax1.set_title("Average Execution Time by Method", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3, axis="x")

    # 2. Memory Usage by Method
    ax2 = fig.add_subplot(gs[0, 1])
    memory = df.groupby("method")["memory_mb"].agg(["mean", "std"])
    memory = memory.sort_values("mean")

    ax2.barh(
        memory.index,
        memory["mean"],
        xerr=memory["std"],
        alpha=0.7,
        color="coral",
        capsize=5,
    )
    ax2.set_xlabel("Memory Usage (MB)")
    ax2.set_title("Average Memory Usage by Method", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="x")

    # 3. BVAR Scalability
    ax3 = fig.add_subplot(gs[1, 0])
    bvar_df = df[df["method"] == "BVAR"].copy()
    if not bvar_df.empty and "n_vars" in bvar_df.columns:
        bvar_df = bvar_df.sort_values("n_vars")
        ax3.plot(
            bvar_df["n_vars"],
            bvar_df["execution_time"],
            "o-",
            linewidth=2,
            markersize=8,
            label="Execution Time",
        )
        ax3.set_xlabel("Number of Variables")
        ax3.set_ylabel("Execution Time (seconds)")
        ax3.set_title("BVAR Scalability", fontsize=12, fontweight="bold")
        ax3.grid(True, alpha=0.3)
        ax3.legend()

    # 4. Hierarchical Scalability
    ax4 = fig.add_subplot(gs[1, 1])
    hier_df = df[df["method"] == "Hierarchical TS"].copy()
    if not hier_df.empty and "n_players" in hier_df.columns:
        hier_df = hier_df.sort_values("n_players")
        ax4.plot(
            hier_df["n_players"],
            hier_df["execution_time"],
            "s-",
            linewidth=2,
            markersize=8,
            color="green",
            label="Execution Time",
        )
        ax4.set_xlabel("Number of Players")
        ax4.set_ylabel("Execution Time (seconds)")
        ax4.set_title("Hierarchical TS Scalability", fontsize=12, fontweight="bold")
        ax4.grid(True, alpha=0.3)
        ax4.legend()

    # 5. Particle Filter Performance
    ax5 = fig.add_subplot(gs[2, 0])
    pf_df = df[df["method"] == "Particle Filter"].copy()
    if not pf_df.empty and "n_particles" in pf_df.columns:
        player_pf = pf_df[pf_df["variant"] == "Player Performance"].copy()
        if not player_pf.empty:
            player_pf = player_pf.sort_values("n_particles")
            ax5.plot(
                player_pf["n_particles"],
                player_pf["execution_time"],
                "o-",
                linewidth=2,
                markersize=8,
                color="purple",
                label="Execution Time",
            )
            ax5.set_xlabel("Number of Particles")
            ax5.set_ylabel("Execution Time (seconds)")
            ax5.set_title("Particle Filter Scalability", fontsize=12, fontweight="bold")
            ax5.grid(True, alpha=0.3)
            ax5.legend()

    # 6. Summary Table
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.axis("off")

    # Create summary table
    summary_data = []
    for method in df["method"].unique():
        method_df = df[df["method"] == method]
        summary_data.append(
            [
                method,
                f"{method_df['execution_time'].mean():.1f}s",
                f"{method_df['memory_mb'].mean():.0f} MB",
                len(method_df),
            ]
        )

    table = ax6.table(
        cellText=summary_data,
        colLabels=["Method", "Avg Time", "Avg Memory", "Configs"],
        cellLoc="center",
        loc="center",
        colWidths=[0.4, 0.2, 0.2, 0.2],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Style header
    for i in range(4):
        table[(0, i)].set_facecolor("#4472C4")
        table[(0, i)].set_text_props(weight="bold", color="white")

    # Alternate row colors
    for i in range(1, len(summary_data) + 1):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor("#E7E6E6")

    ax6.set_title("Summary Statistics", fontsize=12, fontweight="bold", pad=20)

    # Main title
    fig.suptitle(
        "Bayesian Time Series Methods - Performance Benchmarks",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Visualization saved to: {output_path}")

    return fig


def create_convergence_plot(results, output_path="benchmark_convergence.png"):
    """Plot convergence diagnostics."""
    df = pd.DataFrame(results)

    # Filter methods with convergence metrics
    conv_df = df[df["convergence"].notna()].copy()

    if conv_df.empty:
        print("No convergence data available")
        return None

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Convergence rate
    conv_counts = conv_df.groupby("method")["convergence"].agg(["sum", "count"])
    conv_counts["rate"] = conv_counts["sum"] / conv_counts["count"] * 100

    axes[0].bar(conv_counts.index, conv_counts["rate"], alpha=0.7, color="green")
    axes[0].set_ylabel("Convergence Rate (%)")
    axes[0].set_title("Convergence Success Rate", fontsize=12, fontweight="bold")
    axes[0].set_ylim(0, 105)
    axes[0].grid(True, alpha=0.3, axis="y")
    axes[0].tick_params(axis="x", rotation=45)

    # Rhat distribution
    rhat_df = conv_df[conv_df["rhat_max"].notna()].copy()
    if not rhat_df.empty:
        methods = rhat_df["method"].unique()
        rhat_data = [
            rhat_df[rhat_df["method"] == m]["rhat_max"].values for m in methods
        ]

        bp = axes[1].boxplot(rhat_data, labels=methods, patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_facecolor("lightblue")

        axes[1].axhline(
            1.05, color="red", linestyle="--", linewidth=2, label="Threshold (1.05)"
        )
        axes[1].set_ylabel("Max Rhat")
        axes[1].set_title(
            "Convergence Diagnostics (Rhat)", fontsize=12, fontweight="bold"
        )
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis="y")
        axes[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Convergence plot saved to: {output_path}")

    return fig


def print_summary(results):
    """Print text summary of benchmark results."""
    df = pd.DataFrame(results)

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    # Overall statistics
    print("\nOverall Statistics:")
    print(f"  Total configurations: {len(df)}")
    print(f"  Methods tested: {df['method'].nunique()}")
    print(f"  Total execution time: {df['execution_time'].sum():.1f}s")
    print(f"  Average execution time: {df['execution_time'].mean():.1f}s")
    print(f"  Average memory usage: {df['memory_mb'].mean():.1f} MB")

    # By method
    print("\nBy Method:")
    for method in df["method"].unique():
        method_df = df[df["method"] == method]
        print(f"\n  {method}:")
        print(f"    Configurations: {len(method_df)}")
        print(
            f"    Avg execution time: {method_df['execution_time'].mean():.1f}s "
            + f"(range: {method_df['execution_time'].min():.1f}s - {method_df['execution_time'].max():.1f}s)"
        )
        print(
            f"    Avg memory: {method_df['memory_mb'].mean():.1f} MB "
            + f"(range: {method_df['memory_mb'].min():.1f} - {method_df['memory_mb'].max():.1f} MB)"
        )

        if (
            "convergence" in method_df.columns
            and method_df["convergence"].notna().any()
        ):
            conv_rate = method_df["convergence"].mean() * 100
            print(f"    Convergence rate: {conv_rate:.0f}%")

    print("\n" + "=" * 70)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python visualize_benchmarks.py <benchmark_results.json>")
        # Try to find most recent results
        results_files = list(Path(".").glob("benchmark_results_*.json"))
        if results_files:
            filepath = max(results_files, key=lambda p: p.stat().st_mtime)
            print(f"Using most recent file: {filepath}")
        else:
            print("No benchmark results found")
            return
    else:
        filepath = sys.argv[1]

    # Load results
    print(f"Loading results from: {filepath}")
    results = load_results(filepath)
    print(f"✓ Loaded {len(results)} benchmark results")

    # Print summary
    print_summary(results)

    # Create visualizations
    print("\nCreating visualizations...")
    create_visualization(results)
    create_convergence_plot(results)

    print("\n✓ Visualization complete!")


if __name__ == "__main__":
    main()
