"""
Network Visualization Module (Agent 16, Module 5)

Visualizations for network analysis:
- Passing network graphs
- Player interaction heatmaps
- Team chemistry visualizations
- Play type distribution charts
- Dynamic network animations (optional)

Integrates with:
- passing_network: Visualize pass connections
- player_interaction: Interaction matrices
- team_chemistry: Lineup chemistry graphs
- play_types: Play effectiveness charts

Requires matplotlib for plotting (optional dependency)
Requires NetworkX for graph layout (optional dependency)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

# Try to import visualization libraries (optional)
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.colors import LinearSegmentedColormap

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available, visualization disabled")

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available, graph layouts limited")


@dataclass
class VisualizationConfig:
    """Configuration for network visualizations"""

    # Figure settings
    figsize: Tuple[float, float] = (12, 8)
    dpi: int = 100

    # Color scheme
    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    positive_color: str = "#2ca02c"
    negative_color: str = "#d62728"

    # Graph settings
    node_size_scale: float = 1000.0
    edge_width_scale: float = 5.0
    min_edge_weight: float = 0.1  # Filter weak connections

    # Text settings
    show_labels: bool = True
    font_size: int = 10

    # Layout
    layout_algorithm: str = "spring"  # spring, circular, kamada_kawai


class PassingNetworkVisualizer:
    """
    Visualize passing networks as directed graphs.

    Features:
    - Node size by centrality/passes
    - Edge thickness by pass frequency
    - Color by efficiency/team
    - Multiple layout algorithms
    - Assist-only filtering
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize visualizer"""
        self.config = config or VisualizationConfig()

        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib required for visualization")

        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX required for optimal graph layouts")

    def plot_passing_network(
        self,
        graph: Any,  # nx.DiGraph
        player_names: Optional[Dict[str, str]] = None,
        centrality_metric: str = "degree",
        min_passes: int = 5,
        title: str = "Passing Network",
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Plot passing network as graph.

        Args:
            graph: NetworkX DiGraph with pass data
            player_names: Map player_id -> display name
            centrality_metric: Node size metric (degree, betweenness, pagerank)
            min_passes: Minimum passes to show edge
            title: Plot title
            ax: Matplotlib axes (creates new if None)

        Returns:
            Matplotlib axes or None if libraries unavailable
        """
        if not MATPLOTLIB_AVAILABLE or not NETWORKX_AVAILABLE:
            logger.error("Matplotlib and NetworkX required")
            return None

        if ax is None:
            fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        # Filter edges by minimum passes
        filtered_graph = nx.DiGraph()
        for u, v, data in graph.edges(data=True):
            if data.get("weight", 0) >= min_passes:
                filtered_graph.add_edge(u, v, **data)

        # Add all nodes
        for node in graph.nodes():
            if node not in filtered_graph:
                filtered_graph.add_node(node)

        if filtered_graph.number_of_nodes() == 0:
            ax.text(
                0.5,
                0.5,
                "No data to display",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title)
            return ax

        # Calculate layout
        if self.config.layout_algorithm == "spring":
            pos = nx.spring_layout(filtered_graph, k=1, iterations=50)
        elif self.config.layout_algorithm == "circular":
            pos = nx.circular_layout(filtered_graph)
        elif self.config.layout_algorithm == "kamada_kawai":
            try:
                pos = nx.kamada_kawai_layout(filtered_graph)
            except:
                pos = nx.spring_layout(filtered_graph)
        else:
            pos = nx.spring_layout(filtered_graph)

        # Calculate node sizes based on centrality
        if centrality_metric == "degree":
            centrality = dict(filtered_graph.degree(weight="weight"))
        elif centrality_metric == "betweenness":
            centrality = nx.betweenness_centrality(filtered_graph, weight="weight")
        elif centrality_metric == "pagerank":
            centrality = nx.pagerank(filtered_graph, weight="weight")
        else:
            centrality = {node: 1.0 for node in filtered_graph.nodes()}

        # Normalize centrality to node sizes
        if centrality:
            max_centrality = max(centrality.values()) if centrality.values() else 1.0
            node_sizes = [
                (centrality.get(node, 0) / max_centrality) * self.config.node_size_scale
                + 200
                for node in filtered_graph.nodes()
            ]
        else:
            node_sizes = [500 for _ in filtered_graph.nodes()]

        # Calculate edge widths
        edge_weights = [
            data["weight"] for _, _, data in filtered_graph.edges(data=True)
        ]
        if edge_weights:
            max_weight = max(edge_weights)
            edge_widths = [
                (weight / max_weight) * self.config.edge_width_scale + 0.5
                for weight in edge_weights
            ]
        else:
            edge_widths = [1.0]

        # Draw network
        nx.draw_networkx_nodes(
            filtered_graph,
            pos,
            ax=ax,
            node_size=node_sizes,
            node_color=self.config.primary_color,
            alpha=0.7,
        )

        nx.draw_networkx_edges(
            filtered_graph,
            pos,
            ax=ax,
            width=edge_widths,
            alpha=0.5,
            edge_color="gray",
            arrows=True,
            arrowsize=15,
            connectionstyle="arc3,rad=0.1",
        )

        if self.config.show_labels:
            labels = {}
            for node in filtered_graph.nodes():
                if player_names and node in player_names:
                    labels[node] = player_names[node]
                else:
                    # Truncate long IDs
                    labels[node] = node[:8] if len(node) > 8 else node

            nx.draw_networkx_labels(
                filtered_graph, pos, labels, ax=ax, font_size=self.config.font_size
            )

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")

        return ax

    def plot_assist_network(
        self,
        assist_data: List[Tuple[str, str, int]],  # (passer, receiver, assists)
        player_names: Optional[Dict[str, str]] = None,
        min_assists: int = 2,
        title: str = "Assist Network",
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Plot assist-only network.

        Args:
            assist_data: List of (passer_id, receiver_id, assist_count)
            player_names: Map player_id -> display name
            min_assists: Minimum assists to show connection
            title: Plot title
            ax: Matplotlib axes

        Returns:
            Matplotlib axes or None
        """
        if not NETWORKX_AVAILABLE:
            return None

        # Build graph from assist data
        graph = nx.DiGraph()
        for passer, receiver, assists in assist_data:
            if assists >= min_assists:
                graph.add_edge(passer, receiver, weight=assists)

        return self.plot_passing_network(
            graph,
            player_names,
            centrality_metric="degree",
            min_passes=0,  # Already filtered
            title=title,
            ax=ax,
        )


class InteractionHeatmap:
    """
    Visualize player interactions as heatmaps.

    Features:
    - Plus/minus matrices
    - Synergy scores
    - Interaction frequency
    - Hierarchical clustering
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize heatmap visualizer"""
        self.config = config or VisualizationConfig()

    def plot_interaction_matrix(
        self,
        interactions: Dict[Tuple[str, str], float],
        player_ids: List[str],
        player_names: Optional[Dict[str, str]] = None,
        metric_name: str = "Net Rating",
        cmap: str = "RdYlGn",
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Plot player interaction matrix as heatmap.

        Args:
            interactions: Map (player1, player2) -> metric value
            player_ids: Ordered list of player IDs
            player_names: Map player_id -> display name
            metric_name: Name of metric being displayed
            cmap: Matplotlib colormap name
            ax: Matplotlib axes

        Returns:
            Matplotlib axes or None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib required")
            return None

        n = len(player_ids)
        if n == 0:
            return None

        # Build matrix
        matrix = np.zeros((n, n))
        for i, p1 in enumerate(player_ids):
            for j, p2 in enumerate(player_ids):
                if i == j:
                    matrix[i, j] = np.nan  # Diagonal not applicable
                    continue

                # Check both orderings
                key1 = (p1, p2)
                key2 = (p2, p1)

                if key1 in interactions:
                    matrix[i, j] = interactions[key1]
                elif key2 in interactions:
                    matrix[i, j] = interactions[key2]
                else:
                    matrix[i, j] = 0.0

        if ax is None:
            fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        # Plot heatmap
        im = ax.imshow(matrix, cmap=cmap, aspect="auto", interpolation="nearest")

        # Add colorbar
        plt.colorbar(im, ax=ax, label=metric_name)

        # Set ticks and labels
        ax.set_xticks(np.arange(n))
        ax.set_yticks(np.arange(n))

        labels = []
        for pid in player_ids:
            if player_names and pid in player_names:
                labels.append(player_names[pid])
            else:
                labels.append(pid[:8])

        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)

        ax.set_title(
            f"Player Interaction Matrix: {metric_name}", fontsize=14, fontweight="bold"
        )

        # Add grid
        ax.set_xticks(np.arange(n) - 0.5, minor=True)
        ax.set_yticks(np.arange(n) - 0.5, minor=True)
        ax.grid(which="minor", color="white", linestyle="-", linewidth=2)

        return ax

    def plot_synergy_heatmap(
        self,
        synergy_scores: Dict[Tuple[str, str], float],
        player_ids: List[str],
        player_names: Optional[Dict[str, str]] = None,
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """Plot synergy scores as heatmap"""
        return self.plot_interaction_matrix(
            synergy_scores,
            player_ids,
            player_names,
            metric_name="Synergy Score",
            cmap="YlGn",
            ax=ax,
        )


class ChemistryVisualizer:
    """
    Visualize team chemistry and lineup performance.

    Features:
    - Lineup performance charts
    - Chemistry network graphs
    - Stagger analysis plots
    - Best/worst combinations
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize chemistry visualizer"""
        self.config = config or VisualizationConfig()

    def plot_lineup_performance(
        self,
        lineup_data: List[Dict[str, Any]],
        metric: str = "net_rating",
        top_n: int = 15,
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Plot lineup performance bar chart.

        Args:
            lineup_data: List of lineup dicts with metrics
            metric: Metric to plot (net_rating, plus_minus, offensive_rating)
            top_n: Number of lineups to show
            ax: Matplotlib axes

        Returns:
            Matplotlib axes or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        if not lineup_data:
            return None

        # Sort by metric
        sorted_lineups = sorted(
            lineup_data, key=lambda x: x.get(metric, 0), reverse=True
        )[:top_n]

        if ax is None:
            fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        # Prepare data
        labels = []
        values = []
        colors = []

        for lineup in sorted_lineups:
            # Create label from player IDs (truncated)
            players = lineup.get("players", [])
            if isinstance(players, (list, set)):
                label = ", ".join([p[:4] for p in list(players)[:3]]) + "..."
            else:
                label = str(players)[:20]

            labels.append(label)
            value = lineup.get(metric, 0)
            values.append(value)

            # Color based on positive/negative
            if value > 0:
                colors.append(self.config.positive_color)
            else:
                colors.append(self.config.negative_color)

        # Plot bars
        y_pos = np.arange(len(labels))
        ax.barh(y_pos, values, color=colors, alpha=0.7)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel(metric.replace("_", " ").title())
        ax.set_title(
            f"Top {top_n} Lineups by {metric.replace('_', ' ').title()}",
            fontsize=14,
            fontweight="bold",
        )

        # Add zero line
        ax.axvline(x=0, color="black", linestyle="--", linewidth=1, alpha=0.5)

        ax.grid(axis="x", alpha=0.3)

        return ax

    def plot_chemistry_graph(
        self,
        chemistry_scores: Dict[Tuple[str, str], float],
        player_names: Optional[Dict[str, str]] = None,
        threshold: float = 0.5,
        title: str = "Team Chemistry Network",
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Plot chemistry network (only strong connections).

        Args:
            chemistry_scores: Map (p1, p2) -> chemistry score
            player_names: Map player_id -> display name
            threshold: Minimum chemistry to show edge
            title: Plot title
            ax: Matplotlib axes

        Returns:
            Matplotlib axes or None
        """
        if not MATPLOTLIB_AVAILABLE or not NETWORKX_AVAILABLE:
            return None

        if ax is None:
            fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        # Build graph
        graph = nx.Graph()
        for (p1, p2), score in chemistry_scores.items():
            if score >= threshold:
                graph.add_edge(p1, p2, weight=score)

        if graph.number_of_nodes() == 0:
            ax.text(
                0.5,
                0.5,
                f"No chemistry scores >= {threshold}",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title)
            return ax

        # Layout
        pos = nx.spring_layout(graph, k=1.5, iterations=50)

        # Node sizes by degree
        degrees = dict(graph.degree())
        max_degree = max(degrees.values()) if degrees else 1
        node_sizes = [
            (degrees[node] / max_degree) * 800 + 300 for node in graph.nodes()
        ]

        # Edge widths by chemistry
        edge_weights = [data["weight"] for _, _, data in graph.edges(data=True)]
        max_weight = max(edge_weights) if edge_weights else 1.0
        edge_widths = [(weight / max_weight) * 4.0 + 0.5 for weight in edge_weights]

        # Draw
        nx.draw_networkx_nodes(
            graph,
            pos,
            ax=ax,
            node_size=node_sizes,
            node_color=self.config.positive_color,
            alpha=0.7,
        )

        nx.draw_networkx_edges(
            graph, pos, ax=ax, width=edge_widths, alpha=0.6, edge_color="green"
        )

        if self.config.show_labels:
            labels = {}
            for node in graph.nodes():
                if player_names and node in player_names:
                    labels[node] = player_names[node]
                else:
                    labels[node] = node[:8]

            nx.draw_networkx_labels(
                graph, pos, labels, ax=ax, font_size=self.config.font_size
            )

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")

        return ax


class PlayTypeVisualizer:
    """
    Visualize play type distributions and effectiveness.

    Features:
    - Play type distribution pie/bar charts
    - Efficiency comparison charts
    - Player play profile radar charts
    - Context-specific breakdowns (clutch, etc.)
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize play type visualizer"""
        self.config = config or VisualizationConfig()

    def plot_play_type_distribution(
        self,
        play_type_counts: Dict[str, int],
        title: str = "Play Type Distribution",
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Plot play type distribution as pie chart.

        Args:
            play_type_counts: Map play_type -> count
            title: Plot title
            ax: Matplotlib axes

        Returns:
            Matplotlib axes or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        if not play_type_counts:
            return None

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8), dpi=self.config.dpi)

        # Prepare data
        labels = []
        sizes = []
        for play_type, count in sorted(
            play_type_counts.items(), key=lambda x: x[1], reverse=True
        ):
            labels.append(play_type.replace("_", " ").title())
            sizes.append(count)

        # Plot pie chart
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title(title, fontsize=14, fontweight="bold")

        return ax

    def plot_play_type_efficiency(
        self,
        play_type_efficiencies: Dict[str, Dict[str, float]],
        metric: str = "ppp",
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Plot play type efficiency comparison.

        Args:
            play_type_efficiencies: Map play_type -> metrics dict
            metric: Metric to plot (ppp, efficiency_score, fg_pct)
            ax: Matplotlib axes

        Returns:
            Matplotlib axes or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        if not play_type_efficiencies:
            return None

        if ax is None:
            fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        # Prepare data
        play_types = []
        values = []

        for play_type, metrics in sorted(play_type_efficiencies.items()):
            play_types.append(play_type.replace("_", " ").title())
            values.append(metrics.get(metric, 0))

        # Plot bars
        x_pos = np.arange(len(play_types))
        bars = ax.bar(x_pos, values, alpha=0.7, color=self.config.primary_color)

        # Color code bars
        for i, bar in enumerate(bars):
            if values[i] >= 1.0:  # Good efficiency
                bar.set_color(self.config.positive_color)
            elif values[i] < 0.8:  # Poor efficiency
                bar.set_color(self.config.negative_color)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(play_types, rotation=45, ha="right")
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.set_title(
            f"Play Type Efficiency: {metric.replace('_', ' ').title()}",
            fontsize=14,
            fontweight="bold",
        )

        # Add reference line at league average (1.0 PPP)
        if metric == "ppp":
            ax.axhline(
                y=1.0,
                color="black",
                linestyle="--",
                linewidth=1,
                alpha=0.5,
                label="League Avg",
            )
            ax.legend()

        ax.grid(axis="y", alpha=0.3)

        return ax

    def plot_clutch_comparison(
        self,
        clutch_data: Dict[str, Any],
        player_names: Optional[Dict[str, str]] = None,
        ax: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Plot clutch vs overall performance comparison.

        Args:
            clutch_data: Clutch performance data
            player_names: Map player_id -> display name
            ax: Matplotlib axes

        Returns:
            Matplotlib axes or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        if ax is None:
            fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)

        # Extract data
        clutch_ppp = clutch_data.get("clutch_ppp", 0)
        overall_ppp = clutch_data.get("overall_ppp", 0)
        player_id = clutch_data.get("player_id", "Unknown")

        # Create grouped bar chart
        categories = ["Overall", "Clutch"]
        values = [overall_ppp, clutch_ppp]

        x_pos = np.arange(len(categories))
        bars = ax.bar(x_pos, values, alpha=0.7)

        # Color code
        bars[1].set_color(
            self.config.positive_color
            if clutch_ppp > overall_ppp
            else self.config.negative_color
        )

        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories)
        ax.set_ylabel("Points Per Play")

        # Title with player name
        player_name = (
            player_names.get(player_id, player_id) if player_names else player_id
        )
        ax.set_title(
            f"Clutch Performance: {player_name}", fontsize=14, fontweight="bold"
        )

        # Add values on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{values[i]:.2f}",
                ha="center",
                va="bottom",
            )

        ax.grid(axis="y", alpha=0.3)

        return ax


class NetworkDashboard:
    """
    Create comprehensive network analysis dashboards.

    Combines multiple visualizations into single figure.
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize dashboard creator"""
        self.config = config or VisualizationConfig()

        self.passing_viz = PassingNetworkVisualizer(config)
        self.interaction_viz = InteractionHeatmap(config)
        self.chemistry_viz = ChemistryVisualizer(config)
        self.play_type_viz = PlayTypeVisualizer(config)

    def create_team_dashboard(
        self,
        passing_graph: Any,
        interaction_matrix: Dict[Tuple[str, str], float],
        lineup_data: List[Dict[str, Any]],
        play_type_counts: Dict[str, int],
        player_ids: List[str],
        player_names: Optional[Dict[str, str]] = None,
        title: str = "Team Network Analysis Dashboard",
    ) -> Optional[Any]:
        """
        Create comprehensive team dashboard.

        Args:
            passing_graph: NetworkX graph with passes
            interaction_matrix: Player interaction metrics
            lineup_data: Lineup performance data
            play_type_counts: Play type distribution
            player_ids: List of player IDs
            player_names: Map player_id -> display name
            title: Dashboard title

        Returns:
            Matplotlib figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig = plt.figure(figsize=(20, 12), dpi=self.config.dpi)
        fig.suptitle(title, fontsize=18, fontweight="bold")

        # Create 2x2 grid
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # 1. Passing network
        ax1 = fig.add_subplot(gs[0, 0])
        self.passing_viz.plot_passing_network(
            passing_graph, player_names, title="Passing Network", ax=ax1
        )

        # 2. Interaction heatmap
        ax2 = fig.add_subplot(gs[0, 1])
        self.interaction_viz.plot_interaction_matrix(
            interaction_matrix,
            player_ids,
            player_names,
            metric_name="Net Rating",
            ax=ax2,
        )

        # 3. Lineup performance
        ax3 = fig.add_subplot(gs[1, 0])
        self.chemistry_viz.plot_lineup_performance(
            lineup_data, metric="net_rating", ax=ax3
        )

        # 4. Play type distribution
        ax4 = fig.add_subplot(gs[1, 1])
        self.play_type_viz.plot_play_type_distribution(
            play_type_counts, title="Play Type Distribution", ax=ax4
        )

        return fig


def check_visualization_available() -> Dict[str, bool]:
    """Check which visualization libraries are available"""
    return {
        "matplotlib": MATPLOTLIB_AVAILABLE,
        "networkx": NETWORKX_AVAILABLE,
        "full_functionality": MATPLOTLIB_AVAILABLE and NETWORKX_AVAILABLE,
    }


__all__ = [
    "VisualizationConfig",
    "PassingNetworkVisualizer",
    "InteractionHeatmap",
    "ChemistryVisualizer",
    "PlayTypeVisualizer",
    "NetworkDashboard",
    "check_visualization_available",
]
