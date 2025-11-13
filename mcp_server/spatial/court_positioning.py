"""
Court Positioning and Spacing Analysis (Agent 15, Module 2)

Analyzes spatial positioning of players on the court:
- Player position tracking
- Team spacing metrics
- Court coverage analysis
- Position-based clustering
- Offensive/defensive formations

Integrates with:
- shot_location: Shot selection based on spacing
- defensive_spacing: Defensive coverage
- player_movement: Movement into positions
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
import math

import numpy as np
from scipy.spatial import distance, Voronoi
from scipy.cluster import hierarchy
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


class CourtRegion(Enum):
    """Court regions for position classification"""

    PAINT = "paint"
    LEFT_WING = "left_wing"
    RIGHT_WING = "right_wing"
    LEFT_CORNER = "left_corner"
    RIGHT_CORNER = "right_corner"
    TOP_OF_KEY = "top_of_key"
    MID_RANGE_LEFT = "mid_range_left"
    MID_RANGE_RIGHT = "mid_range_right"
    BACKCOURT = "backcourt"


@dataclass
class CourtPosition:
    """Player position on court at a moment in time"""

    player_id: str
    x: float  # Feet from left sideline (0-50)
    y: float  # Feet from baseline (0-94)
    timestamp: float  # Seconds into game
    team: str  # "home" or "away"
    has_ball: bool = False

    # Computed fields
    region: Optional[CourtRegion] = None
    distance_to_basket: Optional[float] = None

    def __post_init__(self):
        """Compute derived fields"""
        if self.region is None:
            self.region = self._classify_region()
        if self.distance_to_basket is None:
            self.distance_to_basket = self._compute_distance_to_basket()

    def _classify_region(self) -> CourtRegion:
        """Classify position into court region"""

        # Backcourt
        if self.y > 47:
            return CourtRegion.BACKCOURT

        # Paint (within the key)
        if abs(self.x - 25) < 8 and self.y < 19:
            return CourtRegion.PAINT

        # Corners
        if self.y < 14:
            if self.x < 10:
                return CourtRegion.LEFT_CORNER
            elif self.x > 40:
                return CourtRegion.RIGHT_CORNER

        # Wings
        if 14 <= self.y < 28:
            if self.x < 20:
                return CourtRegion.LEFT_WING
            elif self.x > 30:
                return CourtRegion.RIGHT_WING

        # Top of key
        if self.y >= 19 and self.y < 28 and abs(self.x - 25) < 15:
            return CourtRegion.TOP_OF_KEY

        # Mid-range
        if self.y < 28:
            if self.x < 25:
                return CourtRegion.MID_RANGE_LEFT
            else:
                return CourtRegion.MID_RANGE_RIGHT

        return CourtRegion.TOP_OF_KEY  # Default

    def _compute_distance_to_basket(self) -> float:
        """Compute distance to nearest basket"""
        # Assume offensive basket at (25, 5.25)
        basket_x = 25.0
        basket_y = 5.25

        dx = self.x - basket_x
        dy = self.y - basket_y

        return math.sqrt(dx * dx + dy * dy)

    def distance_to(self, other: "CourtPosition") -> float:
        """Compute Euclidean distance to another position"""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "player_id": self.player_id,
            "x": self.x,
            "y": self.y,
            "timestamp": self.timestamp,
            "team": self.team,
            "has_ball": self.has_ball,
            "region": self.region.value if self.region else None,
            "distance_to_basket": self.distance_to_basket,
        }


@dataclass
class SpacingMetrics:
    """Team spacing metrics at a moment in time"""

    timestamp: float
    team: str

    # Spacing metrics
    avg_distance_between_players: float  # Average pairwise distance
    std_distance_between_players: float  # Std dev of pairwise distances
    min_distance_between_players: float  # Minimum distance (how crowded)
    max_distance_between_players: float  # Maximum distance (how spread)

    # Coverage metrics
    court_coverage_area: float  # Area covered by convex hull (sq ft)
    perimeter_length: float  # Perimeter of player formation (ft)

    # Compactness
    compactness_score: float  # 0-1, lower = more compact, higher = more spread

    # Formation centroid
    centroid_x: float
    centroid_y: float

    # Number of players
    num_players: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "team": self.team,
            "avg_distance": self.avg_distance_between_players,
            "std_distance": self.std_distance_between_players,
            "min_distance": self.min_distance_between_players,
            "max_distance": self.max_distance_between_players,
            "coverage_area": self.court_coverage_area,
            "perimeter": self.perimeter_length,
            "compactness": self.compactness_score,
            "centroid": (self.centroid_x, self.centroid_y),
            "num_players": self.num_players,
        }


class PositionAnalyzer:
    """
    Analyze court positioning and spatial relationships.

    Features:
    - Team spacing analysis
    - Court coverage metrics
    - Position clustering (formations)
    - Player distribution analysis
    - Optimal spacing recommendations
    """

    def __init__(self):
        """Initialize position analyzer"""
        self.positions: List[CourtPosition] = []
        self.positions_by_team: Dict[str, List[CourtPosition]] = {}
        self.spacing_history: List[SpacingMetrics] = []

        logger.info("PositionAnalyzer initialized")

    def add_position(self, position: CourtPosition):
        """Add a player position"""
        self.positions.append(position)

        if position.team not in self.positions_by_team:
            self.positions_by_team[position.team] = []
        self.positions_by_team[position.team].append(position)

    def add_positions(self, positions: List[CourtPosition]):
        """Add multiple positions"""
        for pos in positions:
            self.add_position(pos)

    def analyze_spacing(
        self, positions: List[CourtPosition], team: Optional[str] = None
    ) -> SpacingMetrics:
        """
        Analyze spacing for a set of positions.

        Args:
            positions: List of player positions at same timestamp
            team: Team identifier

        Returns:
            SpacingMetrics object
        """
        if not positions:
            raise ValueError("No positions provided")

        # Filter to team if specified
        if team:
            positions = [p for p in positions if p.team == team]

        if len(positions) < 2:
            raise ValueError("Need at least 2 positions for spacing analysis")

        timestamp = positions[0].timestamp
        team = team or positions[0].team

        # Compute pairwise distances
        coords = np.array([[p.x, p.y] for p in positions])
        dist_matrix = distance.cdist(coords, coords)

        # Get upper triangle (unique pairs)
        triu_indices = np.triu_indices_from(dist_matrix, k=1)
        pairwise_distances = dist_matrix[triu_indices]

        # Distance statistics
        avg_dist = float(np.mean(pairwise_distances))
        std_dist = float(np.std(pairwise_distances))
        min_dist = float(np.min(pairwise_distances))
        max_dist = float(np.max(pairwise_distances))

        # Coverage area (convex hull)
        if len(positions) >= 3:
            try:
                from scipy.spatial import ConvexHull

                hull = ConvexHull(coords)
                coverage_area = float(hull.volume)  # In 2D, volume = area
                perimeter = float(hull.area)  # In 2D, area = perimeter
            except:
                coverage_area = 0.0
                perimeter = 0.0
        else:
            coverage_area = 0.0
            perimeter = 0.0

        # Compactness score (inverse of spread)
        # Normalize by court dimensions (50 x 47 half-court)
        max_possible_dist = math.sqrt(50**2 + 47**2)
        compactness = 1.0 - (avg_dist / max_possible_dist)

        # Centroid
        centroid_x = float(np.mean([p.x for p in positions]))
        centroid_y = float(np.mean([p.y for p in positions]))

        return SpacingMetrics(
            timestamp=timestamp,
            team=team,
            avg_distance_between_players=avg_dist,
            std_distance_between_players=std_dist,
            min_distance_between_players=min_dist,
            max_distance_between_players=max_dist,
            court_coverage_area=coverage_area,
            perimeter_length=perimeter,
            compactness_score=compactness,
            centroid_x=centroid_x,
            centroid_y=centroid_y,
            num_players=len(positions),
        )

    def get_player_separation(
        self, player1_id: str, player2_id: str, timestamp: Optional[float] = None
    ) -> Optional[float]:
        """
        Get distance between two players at a timestamp.

        Args:
            player1_id: First player ID
            player2_id: Second player ID
            timestamp: Specific timestamp (None = most recent)

        Returns:
            Distance in feet, or None if not found
        """
        # Find positions
        if timestamp is None:
            # Most recent
            p1_pos = next(
                (p for p in reversed(self.positions) if p.player_id == player1_id), None
            )
            p2_pos = next(
                (p for p in reversed(self.positions) if p.player_id == player2_id), None
            )
        else:
            # At specific timestamp
            p1_pos = next(
                (
                    p
                    for p in self.positions
                    if p.player_id == player1_id and abs(p.timestamp - timestamp) < 0.1
                ),
                None,
            )
            p2_pos = next(
                (
                    p
                    for p in self.positions
                    if p.player_id == player2_id and abs(p.timestamp - timestamp) < 0.1
                ),
                None,
            )

        if p1_pos and p2_pos:
            return p1_pos.distance_to(p2_pos)

        return None

    def identify_formation(
        self, positions: List[CourtPosition], n_clusters: int = 3
    ) -> Dict[str, Any]:
        """
        Identify offensive formation using clustering.

        Args:
            positions: Player positions
            n_clusters: Number of clusters (e.g., 3 for inside/wing/perimeter)

        Returns:
            Dictionary with formation analysis
        """
        if len(positions) < n_clusters:
            return {"formation": "insufficient_data"}

        # Extract coordinates
        coords = np.array([[p.x, p.y] for p in positions])

        # K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coords)

        # Analyze clusters
        clusters = []
        for i in range(n_clusters):
            cluster_positions = [p for j, p in enumerate(positions) if labels[j] == i]
            cluster_coords = coords[labels == i]

            if len(cluster_coords) > 0:
                centroid = kmeans.cluster_centers_[i]
                avg_distance_to_basket = float(
                    np.mean([p.distance_to_basket for p in cluster_positions])
                )

                clusters.append(
                    {
                        "cluster_id": i,
                        "num_players": len(cluster_positions),
                        "centroid": tuple(centroid),
                        "avg_distance_to_basket": avg_distance_to_basket,
                        "player_ids": [p.player_id for p in cluster_positions],
                    }
                )

        # Sort clusters by distance to basket
        clusters.sort(key=lambda x: x["avg_distance_to_basket"])

        return {
            "formation": f"{len(clusters)}_cluster",
            "clusters": clusters,
            "spacing": self.analyze_spacing(positions).to_dict(),
        }

    def find_open_spaces(
        self, positions: List[CourtPosition], grid_size: int = 20
    ) -> np.ndarray:
        """
        Identify open spaces on the court using Voronoi diagram.

        Args:
            positions: Current player positions
            grid_size: Grid resolution for heatmap

        Returns:
            Heatmap of open space (higher values = more open)
        """
        if len(positions) < 3:
            # Not enough points for Voronoi
            return np.ones((grid_size, grid_size))

        # Create grid
        x_grid = np.linspace(0, 50, grid_size)
        y_grid = np.linspace(0, 47, grid_size)
        xx, yy = np.meshgrid(x_grid, y_grid)
        grid_points = np.column_stack([xx.ravel(), yy.ravel()])

        # Player positions
        player_coords = np.array([[p.x, p.y] for p in positions])

        # Compute distance to nearest player for each grid point
        distances = distance.cdist(grid_points, player_coords)
        min_distances = distances.min(axis=1)

        # Reshape to grid
        open_space_map = min_distances.reshape(grid_size, grid_size)

        return open_space_map

    def get_region_occupancy(
        self, positions: List[CourtPosition]
    ) -> Dict[CourtRegion, int]:
        """
        Get number of players in each court region.

        Args:
            positions: Player positions

        Returns:
            Dictionary mapping region to player count
        """
        occupancy = {region: 0 for region in CourtRegion}

        for pos in positions:
            if pos.region:
                occupancy[pos.region] += 1

        return occupancy

    def calculate_optimal_spacing(
        self, num_players: int = 5, formation: str = "spread"
    ) -> List[Tuple[float, float]]:
        """
        Calculate optimal player positions for given formation.

        Args:
            num_players: Number of players to position
            formation: Formation type ("spread", "compact", "motion")

        Returns:
            List of (x, y) coordinates for optimal positions
        """
        if formation == "spread":
            # Maximum spacing formation (4-out-1-in)
            positions = [
                (25, 8),  # Center near basket
                (10, 20),  # Left wing
                (40, 20),  # Right wing
                (8, 8),  # Left corner
                (42, 8),  # Right corner
            ]

        elif formation == "compact":
            # More compact formation (everyone close to basket)
            positions = [
                (25, 8),  # Center
                (20, 12),  # Left block
                (30, 12),  # Right block
                (15, 18),  # Left elbow
                (35, 18),  # Right elbow
            ]

        elif formation == "motion":
            # Balanced motion offense
            positions = [
                (25, 10),  # High post
                (15, 15),  # Left wing
                (35, 15),  # Right wing
                (10, 8),  # Left corner
                (40, 8),  # Right corner
            ]

        else:
            raise ValueError(f"Unknown formation: {formation}")

        return positions[:num_players]

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        teams = list(self.positions_by_team.keys())
        stats = {
            "total_positions": len(self.positions),
            "unique_teams": len(teams),
            "spacing_measurements": len(self.spacing_history),
        }

        # Per-team stats
        for team in teams:
            team_positions = self.positions_by_team[team]
            stats[f"{team}_positions"] = len(team_positions)

        return stats

    def clear(self):
        """Clear all stored positions"""
        self.positions.clear()
        self.positions_by_team.clear()
        self.spacing_history.clear()
        logger.info("Cleared all position data")
