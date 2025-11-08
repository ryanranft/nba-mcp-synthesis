"""
Defensive Spacing and Coverage Analysis (Agent 15, Module 3)

Analyzes defensive positioning and coverage:
- Defender assignment tracking
- Closeout distances
- Contest rates and effectiveness
- Help defense positioning
- Defensive rotations
- Coverage gaps identification

Integrates with:
- court_positioning: Spatial relationships
- shot_location: Shot contesting analysis
- player_movement: Defensive rotations
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
import math

import numpy as np
from scipy.spatial import distance

logger = logging.getLogger(__name__)


class DefensiveAssignment(Enum):
    """Types of defensive assignments"""

    MAN_TO_MAN = "man_to_man"
    ZONE = "zone"
    SWITCH = "switch"
    HELP = "help"
    DOUBLE_TEAM = "double_team"
    UNASSIGNED = "unassigned"


class ContestQuality(Enum):
    """Quality of shot contest"""

    OPEN = "open"  # > 6 feet
    WIDE_OPEN = "wide_open"  # > 10 feet
    CONTESTED = "contested"  # 4-6 feet
    TIGHTLY_CONTESTED = "tightly_contested"  # < 4 feet


@dataclass
class DefensivePosition:
    """Defensive player position relative to offensive player"""

    defender_id: str
    offensive_player_id: str
    timestamp: float

    # Positions
    defender_x: float
    defender_y: float
    offensive_x: float
    offensive_y: float

    # Computed metrics
    distance: Optional[float] = None  # Distance between players
    closeout_angle: Optional[float] = None  # Angle of approach
    assignment_type: DefensiveAssignment = DefensiveAssignment.MAN_TO_MAN

    # Shot contesting
    is_shot_attempt: bool = False
    contest_quality: Optional[ContestQuality] = None

    def __post_init__(self):
        """Compute derived metrics"""
        if self.distance is None:
            self.distance = self._compute_distance()
        if self.closeout_angle is None:
            self.closeout_angle = self._compute_closeout_angle()
        if self.is_shot_attempt and self.contest_quality is None:
            self.contest_quality = self._classify_contest_quality()

    def _compute_distance(self) -> float:
        """Compute distance between defender and offensive player"""
        dx = self.defender_x - self.offensive_x
        dy = self.defender_y - self.offensive_y
        return math.sqrt(dx * dx + dy * dy)

    def _compute_closeout_angle(self) -> float:
        """Compute angle of defender relative to offensive player (radians)"""
        dx = self.defender_x - self.offensive_x
        dy = self.defender_y - self.offensive_y
        return math.atan2(dy, dx)

    def _classify_contest_quality(self) -> ContestQuality:
        """Classify contest quality based on distance"""
        if self.distance >= 10.0:
            return ContestQuality.WIDE_OPEN
        elif self.distance >= 6.0:
            return ContestQuality.OPEN
        elif self.distance >= 4.0:
            return ContestQuality.CONTESTED
        else:
            return ContestQuality.TIGHTLY_CONTESTED

    def is_good_closeout(self, threshold: float = 4.0) -> bool:
        """Check if defender has good closeout position"""
        return self.distance <= threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'defender_id': self.defender_id,
            'offensive_player_id': self.offensive_player_id,
            'timestamp': self.timestamp,
            'distance': self.distance,
            'closeout_angle': self.closeout_angle,
            'assignment_type': self.assignment_type.value,
            'is_shot_attempt': self.is_shot_attempt,
            'contest_quality': self.contest_quality.value if self.contest_quality else None,
        }


@dataclass
class DefensiveMetrics:
    """Aggregate defensive metrics for a player or team"""

    player_or_team_id: str
    time_period: Tuple[float, float]  # (start, end) timestamps

    # Contest metrics
    total_contests: int
    tight_contests: int
    good_contests: int  # <= 4 feet
    avg_contest_distance: float

    # Contest quality distribution
    wide_open_allowed: int
    open_allowed: int
    contested: int
    tightly_contested: int

    # Closeout metrics
    avg_closeout_time: Optional[float] = None  # Seconds to close out
    successful_closeouts: int = 0
    failed_closeouts: int = 0

    # Coverage metrics
    avg_coverage_distance: float = 0.0  # Average distance to assignment
    max_coverage_gap: float = 0.0  # Largest gap in coverage

    # Help defense
    help_rotations: int = 0
    effective_help_rotations: int = 0

    def contest_rate(self) -> float:
        """Percentage of shots contested (< 6 feet)"""
        if self.total_contests == 0:
            return 0.0
        return (self.good_contests + self.tight_contests) / self.total_contests

    def tight_contest_rate(self) -> float:
        """Percentage of shots tightly contested (< 4 feet)"""
        if self.total_contests == 0:
            return 0.0
        return self.tight_contests / self.total_contests

    def open_shot_rate(self) -> float:
        """Percentage of shots left open (> 6 feet)"""
        if self.total_contests == 0:
            return 0.0
        return (self.open_allowed + self.wide_open_allowed) / self.total_contests

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'player_or_team_id': self.player_or_team_id,
            'time_period': self.time_period,
            'total_contests': self.total_contests,
            'avg_contest_distance': self.avg_contest_distance,
            'contest_rate': self.contest_rate(),
            'tight_contest_rate': self.tight_contest_rate(),
            'open_shot_rate': self.open_shot_rate(),
            'contest_quality': {
                'wide_open': self.wide_open_allowed,
                'open': self.open_allowed,
                'contested': self.contested,
                'tightly_contested': self.tightly_contested,
            },
            'closeout_metrics': {
                'avg_time': self.avg_closeout_time,
                'successful': self.successful_closeouts,
                'failed': self.failed_closeouts,
            },
            'help_defense': {
                'rotations': self.help_rotations,
                'effective_rotations': self.effective_help_rotations,
            }
        }


@dataclass
class DefensiveSpacing:
    """Team defensive spacing at a moment in time"""

    timestamp: float
    team: str

    # Spacing metrics
    avg_defender_distance_to_assignment: float
    coverage_tightness: float  # 0-1, lower = tighter coverage

    # Gap metrics
    largest_gap: float  # Largest uncovered distance
    gap_locations: List[Tuple[float, float]]  # Locations of significant gaps

    # Paint protection
    paint_occupancy: int  # Number of defenders in paint
    rim_protection_distance: float  # Distance of nearest defender to rim

    # Perimeter defense
    three_point_coverage: float  # 0-1, coverage of three-point line

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'team': self.team,
            'avg_coverage_distance': self.avg_defender_distance_to_assignment,
            'coverage_tightness': self.coverage_tightness,
            'largest_gap': self.largest_gap,
            'num_gaps': len(self.gap_locations),
            'paint_occupancy': self.paint_occupancy,
            'rim_protection_distance': self.rim_protection_distance,
            'three_point_coverage': self.three_point_coverage,
        }


class CoverageAnalyzer:
    """
    Analyze defensive coverage and spacing.

    Features:
    - Defender-to-assignment distance tracking
    - Contest rate analysis
    - Coverage gap identification
    - Help defense evaluation
    - Defensive rotation analysis
    - Closeout effectiveness
    """

    def __init__(self):
        """Initialize coverage analyzer"""
        self.defensive_positions: List[DefensivePosition] = []
        self.positions_by_defender: Dict[str, List[DefensivePosition]] = {}
        self.positions_by_offensive_player: Dict[str, List[DefensivePosition]] = {}
        self.defensive_metrics_cache: Dict[str, DefensiveMetrics] = {}

        logger.info("CoverageAnalyzer initialized")

    def add_defensive_position(self, position: DefensivePosition):
        """Add a defensive position"""
        self.defensive_positions.append(position)

        # Index by defender
        if position.defender_id not in self.positions_by_defender:
            self.positions_by_defender[position.defender_id] = []
        self.positions_by_defender[position.defender_id].append(position)

        # Index by offensive player
        if position.offensive_player_id not in self.positions_by_offensive_player:
            self.positions_by_offensive_player[position.offensive_player_id] = []
        self.positions_by_offensive_player[position.offensive_player_id].append(position)

    def add_defensive_positions(self, positions: List[DefensivePosition]):
        """Add multiple defensive positions"""
        for pos in positions:
            self.add_defensive_position(pos)

    def calculate_defender_metrics(
        self,
        defender_id: str,
        time_period: Optional[Tuple[float, float]] = None
    ) -> DefensiveMetrics:
        """
        Calculate defensive metrics for a specific defender.

        Args:
            defender_id: Defender identifier
            time_period: Optional (start, end) timestamps to filter

        Returns:
            DefensiveMetrics object
        """
        positions = self.positions_by_defender.get(defender_id, [])

        # Filter by time period
        if time_period:
            positions = [
                p for p in positions
                if time_period[0] <= p.timestamp <= time_period[1]
            ]

        if not positions:
            return DefensiveMetrics(
                player_or_team_id=defender_id,
                time_period=time_period or (0.0, 0.0),
                total_contests=0,
                tight_contests=0,
                good_contests=0,
                avg_contest_distance=0.0,
                wide_open_allowed=0,
                open_allowed=0,
                contested=0,
                tightly_contested=0
            )

        # Contest analysis
        shot_attempts = [p for p in positions if p.is_shot_attempt]
        total_contests = len(shot_attempts)

        if total_contests > 0:
            contest_distances = [p.distance for p in shot_attempts]
            avg_contest_distance = float(np.mean(contest_distances))

            # Count by quality
            wide_open = sum(1 for p in shot_attempts if p.contest_quality == ContestQuality.WIDE_OPEN)
            open_shots = sum(1 for p in shot_attempts if p.contest_quality == ContestQuality.OPEN)
            contested = sum(1 for p in shot_attempts if p.contest_quality == ContestQuality.CONTESTED)
            tightly_contested = sum(1 for p in shot_attempts if p.contest_quality == ContestQuality.TIGHTLY_CONTESTED)

            good_contests = contested + tightly_contested
            tight_contests = tightly_contested
        else:
            avg_contest_distance = 0.0
            wide_open = 0
            open_shots = 0
            contested = 0
            tightly_contested = 0
            good_contests = 0
            tight_contests = 0

        # Coverage distance (all positions, not just shots)
        all_distances = [p.distance for p in positions]
        avg_coverage_distance = float(np.mean(all_distances))
        max_coverage_gap = float(np.max(all_distances))

        return DefensiveMetrics(
            player_or_team_id=defender_id,
            time_period=time_period or (positions[0].timestamp, positions[-1].timestamp),
            total_contests=total_contests,
            tight_contests=tight_contests,
            good_contests=good_contests,
            avg_contest_distance=avg_contest_distance,
            wide_open_allowed=wide_open,
            open_allowed=open_shots,
            contested=contested,
            tightly_contested=tightly_contested,
            avg_coverage_distance=avg_coverage_distance,
            max_coverage_gap=max_coverage_gap
        )

    def calculate_team_spacing(
        self,
        positions: List[DefensivePosition],
        team: str,
        offensive_positions: Optional[List[Tuple[float, float]]] = None
    ) -> DefensiveSpacing:
        """
        Calculate defensive spacing metrics for a team.

        Args:
            positions: Defensive positions at same timestamp
            team: Team identifier
            offensive_positions: Optional offensive player positions for gap analysis

        Returns:
            DefensiveSpacing object
        """
        if not positions:
            raise ValueError("No defensive positions provided")

        timestamp = positions[0].timestamp

        # Average coverage distance
        distances = [p.distance for p in positions]
        avg_distance = float(np.mean(distances))

        # Coverage tightness (normalized)
        max_reasonable_distance = 20.0  # Beyond 20 feet is poor coverage
        coverage_tightness = 1.0 - min(avg_distance / max_reasonable_distance, 1.0)

        # Find coverage gaps
        if offensive_positions:
            gap_locations = self._find_coverage_gaps(positions, offensive_positions)
            largest_gap = max([self._gap_size(pos, positions) for pos in offensive_positions])
        else:
            gap_locations = []
            largest_gap = 0.0

        # Paint protection
        paint_occupancy = sum(
            1 for p in positions
            if abs(p.defender_x - 25) < 8 and p.defender_y < 19
        )

        # Rim protection (distance to basket at (25, 5.25))
        rim_distances = [
            math.sqrt((p.defender_x - 25)**2 + (p.defender_y - 5.25)**2)
            for p in positions
        ]
        rim_protection_distance = float(min(rim_distances)) if rim_distances else 100.0

        # Three-point line coverage (simplified)
        # Count defenders within 6 feet of three-point arc
        three_point_defenders = sum(
            1 for p in positions
            if self._distance_to_three_point_line(p.defender_x, p.defender_y) < 6.0
        )
        three_point_coverage = three_point_defenders / max(len(positions), 1)

        return DefensiveSpacing(
            timestamp=timestamp,
            team=team,
            avg_defender_distance_to_assignment=avg_distance,
            coverage_tightness=coverage_tightness,
            largest_gap=largest_gap,
            gap_locations=gap_locations,
            paint_occupancy=paint_occupancy,
            rim_protection_distance=rim_protection_distance,
            three_point_coverage=three_point_coverage
        )

    def _find_coverage_gaps(
        self,
        defensive_positions: List[DefensivePosition],
        offensive_positions: List[Tuple[float, float]],
        gap_threshold: float = 8.0
    ) -> List[Tuple[float, float]]:
        """Find locations where offensive players are poorly covered"""
        gaps = []

        for off_pos in offensive_positions:
            # Find nearest defender
            min_distance = float('inf')
            for def_pos in defensive_positions:
                dist = math.sqrt(
                    (def_pos.defender_x - off_pos[0])**2 +
                    (def_pos.defender_y - off_pos[1])**2
                )
                min_distance = min(min_distance, dist)

            if min_distance > gap_threshold:
                gaps.append(off_pos)

        return gaps

    def _gap_size(
        self,
        offensive_position: Tuple[float, float],
        defensive_positions: List[DefensivePosition]
    ) -> float:
        """Calculate gap size (distance to nearest defender)"""
        min_distance = float('inf')

        for def_pos in defensive_positions:
            dist = math.sqrt(
                (def_pos.defender_x - offensive_position[0])**2 +
                (def_pos.defender_y - offensive_position[1])**2
            )
            min_distance = min(min_distance, dist)

        return min_distance

    def _distance_to_three_point_line(self, x: float, y: float) -> float:
        """Calculate distance from point to nearest part of three-point line"""
        # Simplified: distance to arc at 23.75 feet from basket
        basket_x, basket_y = 25.0, 5.25
        distance_to_basket = math.sqrt((x - basket_x)**2 + (y - basket_y)**2)
        return abs(distance_to_basket - 23.75)

    def identify_help_defenders(
        self,
        positions: List[DefensivePosition],
        ball_handler_x: float,
        ball_handler_y: float,
        help_distance_threshold: float = 10.0
    ) -> List[str]:
        """
        Identify defenders in help position.

        Args:
            positions: All defensive positions at timestamp
            ball_handler_x: X-coordinate of ball handler
            ball_handler_y: Y-coordinate of ball handler
            help_distance_threshold: Maximum distance to be in help position

        Returns:
            List of defender IDs in help position
        """
        help_defenders = []

        # Find primary defender (closest to ball handler)
        primary_defender = None
        min_distance = float('inf')

        for pos in positions:
            dist = math.sqrt(
                (pos.defender_x - ball_handler_x)**2 +
                (pos.defender_y - ball_handler_y)**2
            )
            if dist < min_distance:
                min_distance = dist
                primary_defender = pos.defender_id

        # Identify help defenders (not primary, within help distance)
        for pos in positions:
            if pos.defender_id == primary_defender:
                continue

            dist_to_ball = math.sqrt(
                (pos.defender_x - ball_handler_x)**2 +
                (pos.defender_y - ball_handler_y)**2
            )

            if dist_to_ball <= help_distance_threshold:
                help_defenders.append(pos.defender_id)

        return help_defenders

    def calculate_closeout_effectiveness(
        self,
        defender_id: str,
        time_window: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculate closeout effectiveness for a defender.

        Args:
            defender_id: Defender identifier
            time_window: Time window for closeout analysis (seconds)

        Returns:
            Dictionary with closeout metrics
        """
        positions = self.positions_by_defender.get(defender_id, [])

        if len(positions) < 2:
            return {
                'total_closeouts': 0,
                'avg_closeout_speed': 0.0,
                'success_rate': 0.0
            }

        closeouts = []

        # Find closeout events (rapid decrease in distance)
        for i in range(1, len(positions)):
            prev_pos = positions[i - 1]
            curr_pos = positions[i]

            time_diff = curr_pos.timestamp - prev_pos.timestamp

            if time_diff <= time_window and time_diff > 0:
                distance_change = prev_pos.distance - curr_pos.distance

                # Closeout detected if distance decreased significantly
                if distance_change > 5.0:  # Closed out > 5 feet
                    closeout_speed = distance_change / time_diff
                    successful = curr_pos.distance <= 4.0  # Good closeout position

                    closeouts.append({
                        'speed': closeout_speed,
                        'successful': successful,
                        'final_distance': curr_pos.distance
                    })

        if not closeouts:
            return {
                'total_closeouts': 0,
                'avg_closeout_speed': 0.0,
                'success_rate': 0.0
            }

        total_closeouts = len(closeouts)
        avg_speed = np.mean([c['speed'] for c in closeouts])
        successful = sum(1 for c in closeouts if c['successful'])
        success_rate = successful / total_closeouts

        return {
            'total_closeouts': total_closeouts,
            'avg_closeout_speed': float(avg_speed),
            'success_rate': success_rate,
            'avg_final_distance': float(np.mean([c['final_distance'] for c in closeouts]))
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            'total_defensive_positions': len(self.defensive_positions),
            'unique_defenders': len(self.positions_by_defender),
            'unique_offensive_players': len(self.positions_by_offensive_player),
            'shot_attempts_tracked': sum(
                1 for p in self.defensive_positions if p.is_shot_attempt
            )
        }

    def clear(self):
        """Clear all stored data"""
        self.defensive_positions.clear()
        self.positions_by_defender.clear()
        self.positions_by_offensive_player.clear()
        self.defensive_metrics_cache.clear()
        logger.info("Cleared all defensive position data")
