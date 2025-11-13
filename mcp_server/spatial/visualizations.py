"""
Visualization Utilities for Spatial Analytics (Agent 15, Module 5)

Provides visualization tools for spatial data:
- Shot chart generation
- Heatmap plotting
- Court diagrams
- Movement path visualization
- Spacing diagrams
- Defensive coverage plots

Integrates with:
- shot_location: Shot charts and efficiency maps
- court_positioning: Spacing visualizations
- defensive_spacing: Coverage maps
- player_movement: Movement paths and heatmaps

Note: Requires matplotlib for rendering (optional dependency)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Try to import matplotlib (optional)
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.collections import PatchCollection

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available, visualization features disabled")


class CourtPlotter:
    """
    Draw NBA court diagrams.

    Provides standard court layout with:
    - Three-point line
    - Free throw lane
    - Center circle
    - Basket location
    """

    # Court dimensions (feet)
    COURT_LENGTH = 94.0
    COURT_WIDTH = 50.0

    # Three-point line
    THREE_POINT_RADIUS = 23.75
    THREE_POINT_CORNER = 22.0
    THREE_POINT_CORNER_HEIGHT = 14.0

    # Paint dimensions
    PAINT_WIDTH = 16.0
    PAINT_LENGTH = 19.0

    # Basket position
    BASKET_X = 25.0
    BASKET_Y = 5.25

    def __init__(self, half_court: bool = True):
        """
        Initialize court plotter.

        Args:
            half_court: Whether to draw half court or full court
        """
        self.half_court = half_court

        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Cannot create CourtPlotter: matplotlib not available")

    def draw_court(
        self, ax: Optional[Any] = None, color: str = "black", linewidth: float = 2.0
    ) -> Any:
        """
        Draw court lines on matplotlib axes.

        Args:
            ax: Matplotlib axes (creates new if None)
            color: Line color
            linewidth: Line width

        Returns:
            Matplotlib axes object
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib required for visualization")

        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 11))

        # Set court bounds
        if self.half_court:
            ax.set_xlim(0, self.COURT_WIDTH)
            ax.set_ylim(0, self.COURT_LENGTH / 2)
        else:
            ax.set_xlim(0, self.COURT_WIDTH)
            ax.set_ylim(0, self.COURT_LENGTH)

        ax.set_aspect("equal")

        # Draw sidelines and baseline
        ax.plot(
            [0, 0],
            [0, self.COURT_LENGTH / 2 if self.half_court else self.COURT_LENGTH],
            color=color,
            linewidth=linewidth,
        )
        ax.plot(
            [self.COURT_WIDTH, self.COURT_WIDTH],
            [0, self.COURT_LENGTH / 2 if self.half_court else self.COURT_LENGTH],
            color=color,
            linewidth=linewidth,
        )
        ax.plot([0, self.COURT_WIDTH], [0, 0], color=color, linewidth=linewidth)

        # Draw three-point line
        self._draw_three_point_line(ax, color, linewidth)

        # Draw paint
        self._draw_paint(ax, color, linewidth)

        # Draw basket
        basket = patches.Circle(
            (self.BASKET_X, self.BASKET_Y),
            radius=0.75,
            linewidth=linewidth,
            edgecolor=color,
            facecolor="none",
        )
        ax.add_patch(basket)

        # Draw restricted area
        restricted = patches.Circle(
            (self.BASKET_X, self.BASKET_Y),
            radius=4.0,
            linewidth=linewidth,
            edgecolor=color,
            facecolor="none",
            linestyle="--",
        )
        ax.add_patch(restricted)

        return ax

    def _draw_three_point_line(self, ax, color, linewidth):
        """Draw three-point line"""
        # Arc
        angles = np.linspace(-np.pi / 2 + 0.4, np.pi / 2 - 0.4, 100)
        x = self.BASKET_X + self.THREE_POINT_RADIUS * np.cos(angles)
        y = self.BASKET_Y + self.THREE_POINT_RADIUS * np.sin(angles)
        ax.plot(x, y, color=color, linewidth=linewidth)

        # Corners
        ax.plot(
            [0, 3],
            [self.THREE_POINT_CORNER_HEIGHT, self.THREE_POINT_CORNER_HEIGHT],
            color=color,
            linewidth=linewidth,
        )
        ax.plot(
            [self.COURT_WIDTH - 3, self.COURT_WIDTH],
            [self.THREE_POINT_CORNER_HEIGHT, self.THREE_POINT_CORNER_HEIGHT],
            color=color,
            linewidth=linewidth,
        )

    def _draw_paint(self, ax, color, linewidth):
        """Draw free throw lane"""
        left_x = self.BASKET_X - self.PAINT_WIDTH / 2
        right_x = self.BASKET_X + self.PAINT_WIDTH / 2

        # Paint edges
        ax.plot(
            [left_x, left_x], [0, self.PAINT_LENGTH], color=color, linewidth=linewidth
        )
        ax.plot(
            [right_x, right_x], [0, self.PAINT_LENGTH], color=color, linewidth=linewidth
        )

        # Free throw line
        ax.plot(
            [left_x, right_x],
            [self.PAINT_LENGTH, self.PAINT_LENGTH],
            color=color,
            linewidth=linewidth,
        )

        # Free throw circle
        ft_circle = patches.Circle(
            (self.BASKET_X, self.PAINT_LENGTH),
            radius=6.0,
            linewidth=linewidth,
            edgecolor=color,
            facecolor="none",
        )
        ax.add_patch(ft_circle)


def plot_shot_chart(
    shot_data: List[Dict[str, Any]],
    title: str = "Shot Chart",
    show_makes_misses: bool = True,
    heatmap: bool = False,
    ax: Optional[Any] = None,
) -> Any:
    """
    Plot shot chart.

    Args:
        shot_data: List of shot dictionaries with 'x', 'y', 'made' keys
        title: Chart title
        show_makes_misses: Whether to color by made/missed
        heatmap: Whether to show as heatmap instead of scatter
        ax: Matplotlib axes

    Returns:
        Matplotlib axes
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required for visualization")

    # Create court
    plotter = CourtPlotter(half_court=True)
    ax = plotter.draw_court(ax=ax)

    if heatmap:
        # Create heatmap
        x_coords = [s["x"] for s in shot_data]
        y_coords = [s["y"] for s in shot_data]

        heatmap, xedges, yedges = np.histogram2d(
            x_coords, y_coords, bins=50, range=[[0, 50], [0, 47]]
        )

        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
        im = ax.imshow(
            heatmap.T,
            extent=extent,
            origin="lower",
            cmap="YlOrRd",
            alpha=0.7,
            aspect="auto",
        )
        plt.colorbar(im, ax=ax, label="Shot Attempts")

    else:
        # Scatter plot
        if show_makes_misses:
            makes = [s for s in shot_data if s.get("made", False)]
            misses = [s for s in shot_data if not s.get("made", False)]

            if makes:
                ax.scatter(
                    [s["x"] for s in makes],
                    [s["y"] for s in makes],
                    c="green",
                    marker="o",
                    s=50,
                    alpha=0.6,
                    label="Made",
                )

            if misses:
                ax.scatter(
                    [s["x"] for s in misses],
                    [s["y"] for s in misses],
                    c="red",
                    marker="x",
                    s=50,
                    alpha=0.6,
                    label="Missed",
                )

            ax.legend()
        else:
            ax.scatter(
                [s["x"] for s in shot_data],
                [s["y"] for s in shot_data],
                c="blue",
                marker="o",
                s=50,
                alpha=0.6,
            )

    ax.set_title(title)
    ax.set_xlabel("Court Width (ft)")
    ax.set_ylabel("Court Length (ft)")

    return ax


def plot_heatmap(
    heatmap: np.ndarray,
    x_edges: np.ndarray,
    y_edges: np.ndarray,
    title: str = "Heatmap",
    cmap: str = "YlOrRd",
    ax: Optional[Any] = None,
) -> Any:
    """
    Plot generic heatmap on court.

    Args:
        heatmap: 2D array of values
        x_edges: X-axis bin edges
        y_edges: Y-axis bin edges
        title: Plot title
        cmap: Colormap name
        ax: Matplotlib axes

    Returns:
        Matplotlib axes
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required for visualization")

    # Create court
    plotter = CourtPlotter(half_court=True)
    ax = plotter.draw_court(ax=ax, color="gray", linewidth=1.0)

    # Plot heatmap
    extent = [x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]]
    im = ax.imshow(
        heatmap, extent=extent, origin="lower", cmap=cmap, alpha=0.7, aspect="auto"
    )

    plt.colorbar(im, ax=ax)
    ax.set_title(title)

    return ax


def plot_player_positions(
    positions: List[Dict[str, Any]],
    title: str = "Player Positions",
    show_labels: bool = True,
    ax: Optional[Any] = None,
) -> Any:
    """
    Plot player positions on court.

    Args:
        positions: List of position dicts with 'x', 'y', 'player_id', 'team' keys
        title: Plot title
        show_labels: Whether to show player IDs
        ax: Matplotlib axes

    Returns:
        Matplotlib axes
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required for visualization")

    # Create court
    plotter = CourtPlotter(half_court=True)
    ax = plotter.draw_court(ax=ax)

    # Plot by team
    home_positions = [p for p in positions if p.get("team") == "home"]
    away_positions = [p for p in positions if p.get("team") == "away"]

    if home_positions:
        ax.scatter(
            [p["x"] for p in home_positions],
            [p["y"] for p in home_positions],
            c="blue",
            marker="o",
            s=200,
            alpha=0.7,
            label="Home",
            edgecolors="white",
            linewidths=2,
        )

        if show_labels:
            for p in home_positions:
                ax.text(
                    p["x"],
                    p["y"],
                    p.get("player_id", "?"),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white",
                )

    if away_positions:
        ax.scatter(
            [p["x"] for p in away_positions],
            [p["y"] for p in away_positions],
            c="red",
            marker="o",
            s=200,
            alpha=0.7,
            label="Away",
            edgecolors="white",
            linewidths=2,
        )

        if show_labels:
            for p in away_positions:
                ax.text(
                    p["x"],
                    p["y"],
                    p.get("player_id", "?"),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white",
                )

    ax.legend()
    ax.set_title(title)

    return ax


def plot_movement_path(
    frames: List[Dict[str, Any]],
    title: str = "Movement Path",
    show_speed: bool = True,
    ax: Optional[Any] = None,
) -> Any:
    """
    Plot player movement path.

    Args:
        frames: List of movement frame dicts with 'x', 'y', 'speed' keys
        title: Plot title
        show_speed: Whether to color by speed
        ax: Matplotlib axes

    Returns:
        Matplotlib axes
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required for visualization")

    # Create court
    plotter = CourtPlotter(half_court=True)
    ax = plotter.draw_court(ax=ax)

    x_coords = [f["x"] for f in frames]
    y_coords = [f["y"] for f in frames]

    if show_speed and all("speed" in f for f in frames):
        speeds = [f["speed"] for f in frames]

        # Plot with color based on speed
        points = np.array([x_coords, y_coords]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        from matplotlib.collections import LineCollection

        lc = LineCollection(segments, cmap="viridis", linewidth=3)
        lc.set_array(np.array(speeds))
        ax.add_collection(lc)

        plt.colorbar(lc, ax=ax, label="Speed (ft/s)")
    else:
        # Simple path
        ax.plot(x_coords, y_coords, "b-", linewidth=2, alpha=0.7)

    # Mark start and end
    ax.scatter(
        x_coords[0], y_coords[0], c="green", marker="o", s=100, label="Start", zorder=10
    )
    ax.scatter(
        x_coords[-1], y_coords[-1], c="red", marker="s", s=100, label="End", zorder=10
    )

    ax.legend()
    ax.set_title(title)

    return ax


def create_shot_efficiency_zones_plot(
    zone_efficiencies: Dict[str, Dict[str, float]],
    title: str = "Shot Efficiency by Zone",
) -> Any:
    """
    Create bar chart of shot efficiency by zone.

    Args:
        zone_efficiencies: Dict mapping zone names to efficiency dicts
        title: Plot title

    Returns:
        Matplotlib figure
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib required for visualization")

    zones = list(zone_efficiencies.keys())
    fg_pcts = [zone_efficiencies[z].get("fg_pct", 0) for z in zones]
    attempts = [zone_efficiencies[z].get("attempts", 0) for z in zones]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # FG% by zone
    ax1.barh(zones, fg_pcts, color="steelblue")
    ax1.set_xlabel("Field Goal %")
    ax1.set_title("Field Goal % by Zone")
    ax1.set_xlim(0, 1.0)
    ax1.grid(axis="x", alpha=0.3)

    # Attempts by zone
    ax2.barh(zones, attempts, color="coral")
    ax2.set_xlabel("Attempts")
    ax2.set_title("Shot Attempts by Zone")
    ax2.grid(axis="x", alpha=0.3)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    return fig


# Utility function to check if matplotlib is available
def is_visualization_available() -> bool:
    """Check if visualization features are available"""
    return MATPLOTLIB_AVAILABLE
