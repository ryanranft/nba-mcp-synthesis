"""
Network Analysis Module (Agent 16)

Advanced network analysis for NBA player interactions:
- Passing network analysis
- Player interaction modeling
- Team chemistry metrics
- Play-type effectiveness networks
- Graph-based visualizations

Key Modules:
- passing_network: Pass frequency, efficiency, network metrics
- player_interaction: On-court relationships, +/- analysis
- team_chemistry: Synergy metrics, lineup effectiveness
- play_types: Play-type classification and effectiveness
- network_viz: Graph visualizations

Integrates with:
- spatial: Court positioning for pass analysis
- simulations: Game simulation data
- time_series: Temporal network patterns

Requires NetworkX for graph operations (optional dependency)
"""

from mcp_server.network.passing_network import (
    Pass,
    PassingNetwork,
    PassingMetrics,
    NetworkAnalyzer,
)
from mcp_server.network.player_interaction import (
    PlayerInteraction,
    InteractionMetrics,
    InteractionAnalyzer,
)
from mcp_server.network.team_chemistry import (
    LineupPerformance,
    ChemistryMetrics,
    ChemistryAnalyzer,
)
from mcp_server.network.play_types import (
    PlayType,
    PlaySequence,
    PlayTypeAnalyzer,
)
from mcp_server.network.network_viz import (
    VisualizationConfig,
    PassingNetworkVisualizer,
    InteractionHeatmap,
    ChemistryVisualizer,
    PlayTypeVisualizer,
    NetworkDashboard,
    check_visualization_available,
)

__all__ = [
    # Passing network
    "Pass",
    "PassingNetwork",
    "PassingMetrics",
    "NetworkAnalyzer",
    # Player interaction
    "PlayerInteraction",
    "InteractionMetrics",
    "InteractionAnalyzer",
    # Team chemistry
    "LineupPerformance",
    "ChemistryMetrics",
    "ChemistryAnalyzer",
    # Play types
    "PlayType",
    "PlaySequence",
    "PlayTypeAnalyzer",
    # Visualizations
    "VisualizationConfig",
    "PassingNetworkVisualizer",
    "InteractionHeatmap",
    "ChemistryVisualizer",
    "PlayTypeVisualizer",
    "NetworkDashboard",
    "check_visualization_available",
]
