"""
Shot Location Modeling and Analysis (Agent 15, Module 1)

Provides comprehensive shot location analysis including:
- Shot zone classification (NBA standard zones)
- Shot efficiency by location
- Heatmap generation
- Distance and angle calculations
- Expected points by location

Integrates with:
- visualizations: Heatmap and court plot generation
- bayesian: Hierarchical shot models
- time_series: Shot tendency trends
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import math

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ShotZone(Enum):
    """NBA standard shot zones"""

    # Paint zones
    RESTRICTED_AREA = "restricted_area"  # Under basket (< 4 ft)
    PAINT_NON_RA = "paint_non_ra"  # In paint but outside restricted area

    # Mid-range zones
    MID_RANGE_LEFT = "mid_range_left"
    MID_RANGE_CENTER = "mid_range_center"
    MID_RANGE_RIGHT = "mid_range_right"

    # Three-point zones
    THREE_LEFT_CORNER = "three_left_corner"
    THREE_RIGHT_CORNER = "three_right_corner"
    THREE_ABOVE_BREAK_LEFT = "three_above_break_left"
    THREE_ABOVE_BREAK_CENTER = "three_above_break_center"
    THREE_ABOVE_BREAK_RIGHT = "three_above_break_right"

    # Backcourt
    BACKCOURT = "backcourt"


@dataclass
class ShotLocation:
    """Individual shot location"""

    x: float  # Court x-coordinate (feet, 0 = left sideline, 50 = right sideline)
    y: float  # Court y-coordinate (feet, 0 = baseline, 94 = opposite baseline)
    made: bool  # Whether shot was made
    points: int = 0  # Points scored (0, 2, or 3)
    player_id: Optional[str] = None
    game_id: Optional[str] = None
    timestamp: Optional[float] = None  # Seconds into game
    shot_type: Optional[str] = None  # "jump", "layup", "dunk", etc.

    # Computed fields
    distance: Optional[float] = None  # Distance from basket (feet)
    angle: Optional[float] = None  # Angle from basket (radians)
    zone: Optional[ShotZone] = None  # Shot zone

    def __post_init__(self):
        """Compute derived fields"""
        if self.distance is None:
            self.distance = self._compute_distance()
        if self.angle is None:
            self.angle = self._compute_angle()
        if self.zone is None:
            self.zone = self._classify_zone()
        if self.points == 0 and self.made:
            # Infer points from distance
            self.points = 3 if self.distance > 23.75 else 2

    def _compute_distance(self) -> float:
        """Compute distance from basket (at (25, 5.25))"""
        basket_x = 25.0  # Center of court
        basket_y = 5.25  # Basket is 5.25 feet from baseline

        dx = self.x - basket_x
        dy = self.y - basket_y

        return math.sqrt(dx * dx + dy * dy)

    def _compute_angle(self) -> float:
        """Compute angle from basket (radians, 0 = straight on, +/- pi = sides)"""
        basket_x = 25.0
        basket_y = 5.25

        dx = self.x - basket_x
        dy = self.y - basket_y

        return math.atan2(dx, dy)

    def _classify_zone(self) -> ShotZone:
        """Classify shot into NBA zone"""

        # Backcourt
        if self.y > 47:
            return ShotZone.BACKCOURT

        # Three-point line distance (from basket)
        three_point_distance = 23.75  # NBA three-point line
        corner_three_distance = 22.0  # Corner three is closer

        # Restricted area
        if self.distance < 4.0:
            return ShotZone.RESTRICTED_AREA

        # Corner threes (y < 14, near sidelines)
        if self.y < 14:
            if self.x < 3 and self.distance >= corner_three_distance:
                return ShotZone.THREE_LEFT_CORNER
            elif self.x > 47 and self.distance >= corner_three_distance:
                return ShotZone.THREE_RIGHT_CORNER

        # Three-point shots (above break)
        if self.distance >= three_point_distance:
            angle_deg = math.degrees(abs(self.angle))
            if angle_deg < 30:
                return ShotZone.THREE_ABOVE_BREAK_CENTER
            elif self.x < 25:
                return ShotZone.THREE_ABOVE_BREAK_LEFT
            else:
                return ShotZone.THREE_ABOVE_BREAK_RIGHT

        # Paint (non-restricted area)
        if self.distance < 8.0 and abs(self.x - 25) < 8:
            return ShotZone.PAINT_NON_RA

        # Mid-range
        angle_deg = math.degrees(abs(self.angle))
        if angle_deg < 45:
            return ShotZone.MID_RANGE_CENTER
        elif self.x < 25:
            return ShotZone.MID_RANGE_LEFT
        else:
            return ShotZone.MID_RANGE_RIGHT

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "x": self.x,
            "y": self.y,
            "made": self.made,
            "points": self.points,
            "distance": self.distance,
            "angle": self.angle,
            "zone": self.zone.value if self.zone else None,
            "player_id": self.player_id,
            "game_id": self.game_id,
            "timestamp": self.timestamp,
            "shot_type": self.shot_type,
        }


@dataclass
class ShotEfficiency:
    """Shot efficiency metrics by zone or location"""

    attempts: int
    makes: int
    fg_pct: float  # Field goal percentage
    points_per_shot: float  # Expected points per shot attempt
    effective_fg_pct: float  # Effective FG% (accounts for 3-pointers)

    # Optional breakdown
    two_point_attempts: int = 0
    two_point_makes: int = 0
    three_point_attempts: int = 0
    three_point_makes: int = 0

    # Spatial statistics
    avg_distance: Optional[float] = None
    std_distance: Optional[float] = None

    def __post_init__(self):
        """Validate and compute derived metrics"""
        if self.attempts == 0:
            self.fg_pct = 0.0
            self.points_per_shot = 0.0
            self.effective_fg_pct = 0.0

    @classmethod
    def from_shots(cls, shots: List[ShotLocation]) -> "ShotEfficiency":
        """Create efficiency metrics from shot list"""
        if not shots:
            return cls(
                attempts=0,
                makes=0,
                fg_pct=0.0,
                points_per_shot=0.0,
                effective_fg_pct=0.0,
            )

        attempts = len(shots)
        makes = sum(1 for s in shots if s.made)
        total_points = sum(s.points for s in shots)

        # Breakdown by shot value
        two_pt_attempts = sum(
            1 for s in shots if s.points == 2 or (s.points == 0 and s.distance < 23.75)
        )
        two_pt_makes = sum(1 for s in shots if s.made and s.points == 2)
        three_pt_attempts = sum(
            1 for s in shots if s.points == 3 or (s.points == 0 and s.distance >= 23.75)
        )
        three_pt_makes = sum(1 for s in shots if s.made and s.points == 3)

        # Calculate percentages
        fg_pct = makes / attempts if attempts > 0 else 0.0
        points_per_shot = total_points / attempts if attempts > 0 else 0.0

        # Effective FG% = (FGM + 0.5 * 3PM) / FGA
        effective_fg_pct = (
            (makes + 0.5 * three_pt_makes) / attempts if attempts > 0 else 0.0
        )

        # Distance statistics
        distances = [s.distance for s in shots if s.distance is not None]
        avg_distance = float(np.mean(distances)) if distances else None
        std_distance = float(np.std(distances)) if distances else None

        return cls(
            attempts=attempts,
            makes=makes,
            fg_pct=fg_pct,
            points_per_shot=points_per_shot,
            effective_fg_pct=effective_fg_pct,
            two_point_attempts=two_pt_attempts,
            two_point_makes=two_pt_makes,
            three_point_attempts=three_pt_attempts,
            three_point_makes=three_pt_makes,
            avg_distance=avg_distance,
            std_distance=std_distance,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "attempts": self.attempts,
            "makes": self.makes,
            "fg_pct": self.fg_pct,
            "points_per_shot": self.points_per_shot,
            "effective_fg_pct": self.effective_fg_pct,
            "two_point_attempts": self.two_point_attempts,
            "two_point_makes": self.two_point_makes,
            "three_point_attempts": self.three_point_attempts,
            "three_point_makes": self.three_pt_makes,
            "avg_distance": self.avg_distance,
            "std_distance": self.std_distance,
        }


class ShotLocationAnalyzer:
    """
    Comprehensive shot location analysis.

    Features:
    - Shot zone classification
    - Efficiency analysis by zone
    - Heatmap generation (2D grid)
    - Hot/cold zone identification
    - Expected points modeling
    - Player shot profile comparison
    """

    def __init__(
        self, grid_size: int = 50, court_length: float = 94.0, court_width: float = 50.0
    ):
        """
        Initialize shot location analyzer.

        Args:
            grid_size: Number of grid cells per dimension for heatmap
            court_length: Court length in feet (baseline to baseline)
            court_width: Court width in feet (sideline to sideline)
        """
        self.grid_size = grid_size
        self.court_length = court_length
        self.court_width = court_width

        # Storage
        self.shots: List[ShotLocation] = []
        self.shots_by_player: Dict[str, List[ShotLocation]] = {}
        self.shots_by_zone: Dict[ShotZone, List[ShotLocation]] = {}

        logger.info(
            f"ShotLocationAnalyzer initialized: grid={grid_size}x{grid_size}, "
            f"court={court_width}x{court_length}"
        )

    def add_shot(self, shot: ShotLocation):
        """Add a shot to the analyzer"""
        self.shots.append(shot)

        # Index by player
        if shot.player_id:
            if shot.player_id not in self.shots_by_player:
                self.shots_by_player[shot.player_id] = []
            self.shots_by_player[shot.player_id].append(shot)

        # Index by zone
        if shot.zone:
            if shot.zone not in self.shots_by_zone:
                self.shots_by_zone[shot.zone] = []
            self.shots_by_zone[shot.zone].append(shot)

    def add_shots(self, shots: List[ShotLocation]):
        """Add multiple shots"""
        for shot in shots:
            self.add_shot(shot)

    def get_zone_efficiency(self, zone: ShotZone) -> ShotEfficiency:
        """Get efficiency metrics for a specific zone"""
        zone_shots = self.shots_by_zone.get(zone, [])
        return ShotEfficiency.from_shots(zone_shots)

    def get_all_zone_efficiencies(self) -> Dict[ShotZone, ShotEfficiency]:
        """Get efficiency metrics for all zones"""
        return {zone: self.get_zone_efficiency(zone) for zone in ShotZone}

    def get_player_efficiency(self, player_id: str) -> ShotEfficiency:
        """Get efficiency metrics for a player"""
        player_shots = self.shots_by_player.get(player_id, [])
        return ShotEfficiency.from_shots(player_shots)

    def generate_heatmap(
        self,
        player_id: Optional[str] = None,
        metric: str = "fg_pct",
        min_attempts: int = 5,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate shot heatmap as a 2D grid.

        Args:
            player_id: Filter to specific player (None = all players)
            metric: Metric to display ('fg_pct', 'attempts', 'points_per_shot')
            min_attempts: Minimum attempts per cell to display

        Returns:
            Tuple of (heatmap, x_edges, y_edges) for plotting
        """
        # Filter shots
        if player_id:
            shots = self.shots_by_player.get(player_id, [])
        else:
            shots = self.shots

        if not shots:
            # Return empty heatmap
            x_edges = np.linspace(0, self.court_width, self.grid_size + 1)
            y_edges = np.linspace(0, self.court_length / 2, self.grid_size + 1)
            return np.zeros((self.grid_size, self.grid_size)), x_edges, y_edges

        # Extract coordinates
        x_coords = np.array([s.x for s in shots])
        y_coords = np.array([s.y for s in shots])

        # Create grid
        x_edges = np.linspace(0, self.court_width, self.grid_size + 1)
        y_edges = np.linspace(
            0, self.court_length / 2, self.grid_size + 1
        )  # Half court

        # Initialize grids
        attempts_grid = np.zeros((self.grid_size, self.grid_size))
        makes_grid = np.zeros((self.grid_size, self.grid_size))
        points_grid = np.zeros((self.grid_size, self.grid_size))

        # Populate grids
        for shot in shots:
            # Find grid cell
            x_idx = min(
                int(shot.x / self.court_width * self.grid_size), self.grid_size - 1
            )
            y_idx = min(
                int(shot.y / (self.court_length / 2) * self.grid_size),
                self.grid_size - 1,
            )

            attempts_grid[y_idx, x_idx] += 1
            if shot.made:
                makes_grid[y_idx, x_idx] += 1
            points_grid[y_idx, x_idx] += shot.points

        # Compute heatmap based on metric
        if metric == "fg_pct":
            # Field goal percentage
            heatmap = np.divide(
                makes_grid,
                attempts_grid,
                out=np.zeros_like(makes_grid),
                where=attempts_grid >= min_attempts,
            )
        elif metric == "attempts":
            # Shot attempt frequency
            heatmap = attempts_grid
        elif metric == "points_per_shot":
            # Expected points per shot
            heatmap = np.divide(
                points_grid,
                attempts_grid,
                out=np.zeros_like(points_grid),
                where=attempts_grid >= min_attempts,
            )
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return heatmap, x_edges, y_edges

    def identify_hot_zones(
        self,
        player_id: Optional[str] = None,
        threshold: float = 0.50,
        min_attempts: int = 10,
    ) -> List[Tuple[ShotZone, ShotEfficiency]]:
        """
        Identify hot zones (high efficiency zones).

        Args:
            player_id: Filter to specific player
            threshold: Minimum FG% to be considered "hot"
            min_attempts: Minimum attempts required

        Returns:
            List of (zone, efficiency) tuples for hot zones
        """
        hot_zones = []

        # Get zones to analyze
        if player_id:
            player_shots = self.shots_by_player.get(player_id, [])
            # Group by zone
            zone_shots = {}
            for shot in player_shots:
                if shot.zone not in zone_shots:
                    zone_shots[shot.zone] = []
                zone_shots[shot.zone].append(shot)
        else:
            zone_shots = self.shots_by_zone

        # Find hot zones
        for zone, shots in zone_shots.items():
            efficiency = ShotEfficiency.from_shots(shots)
            if efficiency.attempts >= min_attempts and efficiency.fg_pct >= threshold:
                hot_zones.append((zone, efficiency))

        # Sort by efficiency (descending)
        hot_zones.sort(key=lambda x: x[1].fg_pct, reverse=True)

        return hot_zones

    def identify_cold_zones(
        self,
        player_id: Optional[str] = None,
        threshold: float = 0.35,
        min_attempts: int = 10,
    ) -> List[Tuple[ShotZone, ShotEfficiency]]:
        """
        Identify cold zones (low efficiency zones).

        Args:
            player_id: Filter to specific player
            threshold: Maximum FG% to be considered "cold"
            min_attempts: Minimum attempts required

        Returns:
            List of (zone, efficiency) tuples for cold zones
        """
        cold_zones = []

        # Get zones to analyze
        if player_id:
            player_shots = self.shots_by_player.get(player_id, [])
            zone_shots = {}
            for shot in player_shots:
                if shot.zone not in zone_shots:
                    zone_shots[shot.zone] = []
                zone_shots[shot.zone].append(shot)
        else:
            zone_shots = self.shots_by_zone

        # Find cold zones
        for zone, shots in zone_shots.items():
            efficiency = ShotEfficiency.from_shots(shots)
            if efficiency.attempts >= min_attempts and efficiency.fg_pct <= threshold:
                cold_zones.append((zone, efficiency))

        # Sort by efficiency (ascending)
        cold_zones.sort(key=lambda x: x[1].fg_pct)

        return cold_zones

    def get_expected_points(
        self, x: float, y: float, player_id: Optional[str] = None
    ) -> float:
        """
        Get expected points for a shot at given location.

        Uses kernel density estimation around the location.

        Args:
            x: X-coordinate
            y: Y-coordinate
            player_id: Specific player (None = league average)

        Returns:
            Expected points
        """
        # Create temporary shot to get zone
        temp_shot = ShotLocation(x=x, y=y, made=False)
        zone = temp_shot.zone

        # Get efficiency for that zone
        if player_id:
            player_shots = self.shots_by_player.get(player_id, [])
            zone_shots = [s for s in player_shots if s.zone == zone]
        else:
            zone_shots = self.shots_by_zone.get(zone, [])

        if not zone_shots:
            # Default: assume 2-pointer at 40% or 3-pointer at 35%
            is_three = temp_shot.distance >= 23.75
            default_pct = 0.35 if is_three else 0.40
            return default_pct * (3 if is_three else 2)

        efficiency = ShotEfficiency.from_shots(zone_shots)
        return efficiency.points_per_shot

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            "total_shots": len(self.shots),
            "unique_players": len(self.shots_by_player),
            "zones_with_shots": len(self.shots_by_zone),
            "overall_efficiency": ShotEfficiency.from_shots(self.shots).to_dict(),
        }

    def clear(self):
        """Clear all stored shots"""
        self.shots.clear()
        self.shots_by_player.clear()
        self.shots_by_zone.clear()
        logger.info("Cleared all shot data")
