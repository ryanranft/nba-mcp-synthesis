"""
Spatial & Visual Analytics Module (Agent 15)

Advanced spatial analysis for NBA data:
- Shot location modeling and efficiency zones
- Court positioning and spacing analysis
- Defensive metrics and coverage
- Player movement patterns
- Interactive visualizations

Key Modules:
- shot_location: Shot modeling, heatmaps, efficiency zones
- court_positioning: Spatial positioning analysis
- defensive_spacing: Defensive metrics and spacing
- player_movement: Movement tracking and patterns
- visualizations: Interactive plots and animations

Integrates with:
- simulations: Game simulation data
- time_series: Temporal patterns
- bayesian: Hierarchical spatial models
"""

from mcp_server.spatial.shot_location import (
    ShotLocation,
    ShotZone,
    ShotLocationAnalyzer,
    ShotEfficiency,
)
from mcp_server.spatial.court_positioning import (
    CourtPosition,
    PositionAnalyzer,
    SpacingMetrics,
)
from mcp_server.spatial.defensive_spacing import (
    DefensiveMetrics,
    CoverageAnalyzer,
    DefensiveSpacing,
)
from mcp_server.spatial.player_movement import (
    MovementTracker,
    MovementPattern,
    VelocityAnalyzer,
    MovementFrame,
)
from mcp_server.spatial.visualizations import (
    CourtPlotter,
    plot_shot_chart,
    plot_heatmap,
    plot_player_positions,
    plot_movement_path,
    is_visualization_available,
)

__all__ = [
    # Shot location
    "ShotLocation",
    "ShotZone",
    "ShotLocationAnalyzer",
    "ShotEfficiency",
    # Court positioning
    "CourtPosition",
    "PositionAnalyzer",
    "SpacingMetrics",
    # Defensive spacing
    "DefensiveMetrics",
    "CoverageAnalyzer",
    "DefensiveSpacing",
    # Player movement
    "MovementTracker",
    "MovementPattern",
    "VelocityAnalyzer",
    "MovementFrame",
    # Visualizations
    "CourtPlotter",
    "plot_shot_chart",
    "plot_heatmap",
    "plot_player_positions",
    "plot_movement_path",
    "is_visualization_available",
]
