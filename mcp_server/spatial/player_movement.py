"""
Player Movement Tracking and Analysis (Agent 15, Module 4)

Tracks and analyzes player movement patterns:
- Velocity and acceleration tracking
- Movement routes and paths
- Off-ball movement analysis
- Cutting patterns
- Screen usage
- Movement efficiency metrics

Integrates with:
- court_positioning: Movement between positions
- defensive_spacing: Defensive movement and rotations
- shot_location: Movement before shots
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import math

import numpy as np
from scipy.signal import savgol_filter
from scipy.spatial import distance

logger = logging.getLogger(__name__)


class MovementType(Enum):
    """Types of player movement"""

    STATIONARY = "stationary"
    WALKING = "walking"
    JOGGING = "jogging"
    RUNNING = "running"
    SPRINTING = "sprinting"
    CUT = "cut"
    SCREEN_SET = "screen_set"
    SCREEN_USE = "screen_use"


class MovementDirection(Enum):
    """General direction of movement"""

    TOWARD_BASKET = "toward_basket"
    AWAY_FROM_BASKET = "away_from_basket"
    LATERAL_LEFT = "lateral_left"
    LATERAL_RIGHT = "lateral_right"
    STATIONARY = "stationary"


@dataclass
class MovementFrame:
    """Player position and movement at a single frame"""

    player_id: str
    timestamp: float  # Seconds
    x: float  # Feet
    y: float  # Feet

    # Computed motion metrics
    velocity_x: Optional[float] = None  # Feet per second
    velocity_y: Optional[float] = None
    speed: Optional[float] = None  # Total speed (magnitude)
    acceleration: Optional[float] = None  # Feet per second squared
    direction: Optional[float] = None  # Direction of movement (radians)

    # Movement classification
    movement_type: Optional[MovementType] = None
    movement_direction: Optional[MovementDirection] = None

    def __post_init__(self):
        """Initialize computed fields"""
        if self.velocity_x is not None and self.velocity_y is not None:
            if self.speed is None:
                self.speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
            if self.direction is None:
                self.direction = math.atan2(self.velocity_y, self.velocity_x)
        if self.speed is not None and self.movement_type is None:
            self.movement_type = self._classify_movement_type()
        if self.velocity_y is not None and self.movement_direction is None:
            self.movement_direction = self._classify_movement_direction()

    def _classify_movement_type(self) -> MovementType:
        """Classify movement type based on speed"""
        if self.speed < 1.0:
            return MovementType.STATIONARY
        elif self.speed < 5.0:
            return MovementType.WALKING
        elif self.speed < 10.0:
            return MovementType.JOGGING
        elif self.speed < 15.0:
            return MovementType.RUNNING
        else:
            return MovementType.SPRINTING

    def _classify_movement_direction(self) -> MovementDirection:
        """Classify general movement direction"""
        if self.speed < 1.0:
            return MovementDirection.STATIONARY

        # Basket is at (25, 5.25)
        basket_direction = math.atan2(5.25 - self.y, 25 - self.x)
        angle_to_basket = abs(self.direction - basket_direction)

        # Normalize angle to [0, pi]
        angle_to_basket = min(angle_to_basket, 2 * math.pi - angle_to_basket)

        # Determine direction
        if angle_to_basket < math.pi / 4:
            return MovementDirection.TOWARD_BASKET
        elif angle_to_basket > 3 * math.pi / 4:
            return MovementDirection.AWAY_FROM_BASKET
        elif abs(self.velocity_x) > abs(self.velocity_y):
            if self.velocity_x > 0:
                return MovementDirection.LATERAL_RIGHT
            else:
                return MovementDirection.LATERAL_LEFT
        else:
            if self.velocity_y > 0:
                return MovementDirection.TOWARD_BASKET
            else:
                return MovementDirection.AWAY_FROM_BASKET

    def distance_traveled(self, other: 'MovementFrame') -> float:
        """Calculate distance traveled between two frames"""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'player_id': self.player_id,
            'timestamp': self.timestamp,
            'x': self.x,
            'y': self.y,
            'velocity_x': self.velocity_x,
            'velocity_y': self.velocity_y,
            'speed': self.speed,
            'acceleration': self.acceleration,
            'direction': self.direction,
            'movement_type': self.movement_type.value if self.movement_type else None,
            'movement_direction': self.movement_direction.value if self.movement_direction else None,
        }


@dataclass
class MovementPattern:
    """Identified movement pattern or route"""

    player_id: str
    start_time: float
    end_time: float
    frames: List[MovementFrame]

    # Pattern characteristics
    pattern_type: str  # "cut", "screen", "post_up", "spot_up", etc.
    total_distance: float = 0.0
    avg_speed: float = 0.0
    max_speed: float = 0.0
    efficiency_score: float = 0.0  # 0-1, higher = more efficient path

    def __post_init__(self):
        """Compute pattern metrics"""
        if len(self.frames) < 2:
            return

        # Calculate total distance
        distances = []
        for i in range(1, len(self.frames)):
            dist = self.frames[i].distance_traveled(self.frames[i-1])
            distances.append(dist)
        self.total_distance = sum(distances)

        # Speed statistics
        speeds = [f.speed for f in self.frames if f.speed is not None]
        if speeds:
            self.avg_speed = float(np.mean(speeds))
            self.max_speed = float(np.max(speeds))

        # Efficiency (straight-line distance / actual distance traveled)
        if self.total_distance > 0:
            straight_line = self.frames[0].distance_traveled(self.frames[-1])
            self.efficiency_score = straight_line / self.total_distance
        else:
            self.efficiency_score = 1.0

    def duration(self) -> float:
        """Get pattern duration in seconds"""
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'player_id': self.player_id,
            'pattern_type': self.pattern_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration(),
            'total_distance': self.total_distance,
            'avg_speed': self.avg_speed,
            'max_speed': self.max_speed,
            'efficiency_score': self.efficiency_score,
            'num_frames': len(self.frames),
        }


@dataclass
class VelocityAnalyzer:
    """Analyze velocity and acceleration patterns"""

    smoothing_window: int = 5  # Frames for smoothing

    def compute_velocities(
        self,
        frames: List[MovementFrame]
    ) -> List[MovementFrame]:
        """
        Compute velocities for a sequence of frames.

        Args:
            frames: List of movement frames (must be time-ordered)

        Returns:
            List of frames with velocity computed
        """
        if len(frames) < 2:
            return frames

        # Sort by timestamp
        frames = sorted(frames, key=lambda f: f.timestamp)

        # Compute velocities
        for i in range(1, len(frames)):
            prev = frames[i - 1]
            curr = frames[i]

            dt = curr.timestamp - prev.timestamp
            if dt > 0:
                curr.velocity_x = (curr.x - prev.x) / dt
                curr.velocity_y = (curr.y - prev.y) / dt
                curr.speed = math.sqrt(curr.velocity_x**2 + curr.velocity_y**2)
                curr.direction = math.atan2(curr.velocity_y, curr.velocity_x)

        # First frame (no previous frame)
        frames[0].velocity_x = frames[1].velocity_x if len(frames) > 1 else 0.0
        frames[0].velocity_y = frames[1].velocity_y if len(frames) > 1 else 0.0
        frames[0].speed = frames[1].speed if len(frames) > 1 else 0.0
        frames[0].direction = frames[1].direction if len(frames) > 1 else 0.0

        return frames

    def compute_accelerations(
        self,
        frames: List[MovementFrame]
    ) -> List[MovementFrame]:
        """
        Compute accelerations for a sequence of frames.

        Args:
            frames: List of movement frames with velocities

        Returns:
            List of frames with acceleration computed
        """
        if len(frames) < 2:
            return frames

        # Compute accelerations
        for i in range(1, len(frames)):
            prev = frames[i - 1]
            curr = frames[i]

            dt = curr.timestamp - prev.timestamp
            if dt > 0 and prev.speed is not None and curr.speed is not None:
                curr.acceleration = (curr.speed - prev.speed) / dt

        return frames

    def smooth_velocities(
        self,
        frames: List[MovementFrame]
    ) -> List[MovementFrame]:
        """
        Apply smoothing to velocity estimates.

        Args:
            frames: List of movement frames

        Returns:
            List of frames with smoothed velocities
        """
        if len(frames) < self.smoothing_window:
            return frames

        # Extract velocity components
        vx = np.array([f.velocity_x for f in frames])
        vy = np.array([f.velocity_y for f in frames])

        # Apply Savitzky-Golay filter
        try:
            vx_smooth = savgol_filter(vx, self.smoothing_window, 2)
            vy_smooth = savgol_filter(vy, self.smoothing_window, 2)

            # Update frames
            for i, frame in enumerate(frames):
                frame.velocity_x = float(vx_smooth[i])
                frame.velocity_y = float(vy_smooth[i])
                frame.speed = math.sqrt(frame.velocity_x**2 + frame.velocity_y**2)
                frame.direction = math.atan2(frame.velocity_y, frame.velocity_x)
        except:
            # If smoothing fails, return original
            pass

        return frames


class MovementTracker:
    """
    Track and analyze player movement patterns.

    Features:
    - Velocity and acceleration computation
    - Movement pattern identification
    - Cutting analysis
    - Screen detection
    - Off-ball movement evaluation
    - Movement efficiency metrics
    """

    def __init__(
        self,
        sampling_rate: float = 25.0,  # Hz (frames per second)
        smoothing_window: int = 5
    ):
        """
        Initialize movement tracker.

        Args:
            sampling_rate: Tracking data sampling rate (Hz)
            smoothing_window: Window size for velocity smoothing
        """
        self.sampling_rate = sampling_rate
        self.velocity_analyzer = VelocityAnalyzer(smoothing_window=smoothing_window)

        # Storage
        self.frames: List[MovementFrame] = []
        self.frames_by_player: Dict[str, List[MovementFrame]] = {}
        self.patterns: List[MovementPattern] = []

        logger.info(f"MovementTracker initialized: sampling_rate={sampling_rate}Hz")

    def add_frame(self, frame: MovementFrame):
        """Add a movement frame"""
        self.frames.append(frame)

        if frame.player_id not in self.frames_by_player:
            self.frames_by_player[frame.player_id] = []
        self.frames_by_player[frame.player_id].append(frame)

    def add_frames(self, frames: List[MovementFrame]):
        """Add multiple frames"""
        for frame in frames:
            self.add_frame(frame)

    def process_player_trajectory(
        self,
        player_id: str,
        compute_velocities: bool = True,
        compute_accelerations: bool = True,
        smooth_velocities: bool = True
    ) -> List[MovementFrame]:
        """
        Process trajectory for a player.

        Args:
            player_id: Player identifier
            compute_velocities: Whether to compute velocities
            compute_accelerations: Whether to compute accelerations
            smooth_velocities: Whether to smooth velocity estimates

        Returns:
            List of processed frames
        """
        frames = self.frames_by_player.get(player_id, [])

        if not frames:
            return []

        # Sort by timestamp
        frames = sorted(frames, key=lambda f: f.timestamp)

        # Compute velocities
        if compute_velocities:
            frames = self.velocity_analyzer.compute_velocities(frames)

        # Smooth velocities
        if smooth_velocities and compute_velocities:
            frames = self.velocity_analyzer.smooth_velocities(frames)

        # Compute accelerations
        if compute_accelerations and compute_velocities:
            frames = self.velocity_analyzer.compute_accelerations(frames)

        # Update movement classifications
        for frame in frames:
            if frame.speed is not None:
                frame.movement_type = frame._classify_movement_type()
                frame.movement_direction = frame._classify_movement_direction()

        return frames

    def identify_cuts(
        self,
        player_id: str,
        min_speed: float = 10.0,  # ft/s
        min_duration: float = 0.5,  # seconds
        min_distance: float = 8.0  # feet
    ) -> List[MovementPattern]:
        """
        Identify cutting movements.

        Args:
            player_id: Player identifier
            min_speed: Minimum speed to be considered a cut
            min_duration: Minimum duration of cut
            min_distance: Minimum distance traveled

        Returns:
            List of identified cut patterns
        """
        frames = self.process_player_trajectory(player_id)

        if not frames:
            return []

        cuts = []
        current_cut_frames = []
        cut_started = False

        for frame in frames:
            if frame.speed and frame.speed >= min_speed:
                current_cut_frames.append(frame)
                cut_started = True
            else:
                if cut_started and len(current_cut_frames) > 0:
                    # Check if cut meets criteria
                    duration = current_cut_frames[-1].timestamp - current_cut_frames[0].timestamp
                    if duration >= min_duration:
                        # Calculate distance
                        distance = sum(
                            current_cut_frames[i].distance_traveled(current_cut_frames[i-1])
                            for i in range(1, len(current_cut_frames))
                        )

                        if distance >= min_distance:
                            # Valid cut
                            pattern = MovementPattern(
                                player_id=player_id,
                                start_time=current_cut_frames[0].timestamp,
                                end_time=current_cut_frames[-1].timestamp,
                                frames=current_cut_frames.copy(),
                                pattern_type="cut"
                            )
                            cuts.append(pattern)

                    current_cut_frames = []
                    cut_started = False

        return cuts

    def calculate_distance_traveled(
        self,
        player_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> float:
        """
        Calculate total distance traveled by player.

        Args:
            player_id: Player identifier
            start_time: Start timestamp (None = beginning)
            end_time: End timestamp (None = end)

        Returns:
            Total distance in feet
        """
        frames = self.frames_by_player.get(player_id, [])

        # Filter by time
        if start_time or end_time:
            frames = [
                f for f in frames
                if (start_time is None or f.timestamp >= start_time) and
                   (end_time is None or f.timestamp <= end_time)
            ]

        if len(frames) < 2:
            return 0.0

        # Sort frames
        frames = sorted(frames, key=lambda f: f.timestamp)

        # Calculate distance
        total_distance = 0.0
        for i in range(1, len(frames)):
            total_distance += frames[i].distance_traveled(frames[i-1])

        return total_distance

    def calculate_avg_speed(
        self,
        player_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> float:
        """
        Calculate average speed for player.

        Args:
            player_id: Player identifier
            start_time: Start timestamp
            end_time: End timestamp

        Returns:
            Average speed in ft/s
        """
        frames = self.process_player_trajectory(player_id)

        # Filter by time
        if start_time or end_time:
            frames = [
                f for f in frames
                if (start_time is None or f.timestamp >= start_time) and
                   (end_time is None or f.timestamp <= end_time)
            ]

        if not frames:
            return 0.0

        speeds = [f.speed for f in frames if f.speed is not None]
        return float(np.mean(speeds)) if speeds else 0.0

    def get_movement_heatmap(
        self,
        player_id: str,
        grid_size: int = 50
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate movement heatmap (time spent in each location).

        Args:
            player_id: Player identifier
            grid_size: Grid resolution

        Returns:
            Tuple of (heatmap, x_edges, y_edges)
        """
        frames = self.frames_by_player.get(player_id, [])

        if not frames:
            x_edges = np.linspace(0, 50, grid_size + 1)
            y_edges = np.linspace(0, 47, grid_size + 1)
            return np.zeros((grid_size, grid_size)), x_edges, y_edges

        # Extract positions
        x_coords = np.array([f.x for f in frames])
        y_coords = np.array([f.y for f in frames])

        # Create histogram
        heatmap, x_edges, y_edges = np.histogram2d(
            x_coords,
            y_coords,
            bins=[grid_size, grid_size],
            range=[[0, 50], [0, 47]]
        )

        return heatmap.T, x_edges, y_edges

    def analyze_off_ball_movement(
        self,
        player_id: str,
        ball_handler_frames: List[MovementFrame],
        radius: float = 15.0
    ) -> Dict[str, Any]:
        """
        Analyze off-ball movement while another player has the ball.

        Args:
            player_id: Player identifier (off-ball player)
            ball_handler_frames: Frames when another player has ball
            radius: Radius to consider "near ball handler"

        Returns:
            Dictionary with off-ball movement metrics
        """
        player_frames = self.frames_by_player.get(player_id, [])

        if not player_frames or not ball_handler_frames:
            return {
                'distance_traveled': 0.0,
                'avg_speed': 0.0,
                'cuts': 0,
                'time_near_ball_handler': 0.0
            }

        # Match frames by timestamp
        matched_frames = []
        for pf in player_frames:
            # Find nearest ball handler frame
            nearest_bh = min(
                ball_handler_frames,
                key=lambda bf: abs(bf.timestamp - pf.timestamp)
            )

            if abs(nearest_bh.timestamp - pf.timestamp) < 0.1:  # Within 0.1s
                matched_frames.append((pf, nearest_bh))

        if not matched_frames:
            return {'distance_traveled': 0.0, 'avg_speed': 0.0, 'cuts': 0}

        # Calculate metrics
        distance_traveled = sum(
            matched_frames[i][0].distance_traveled(matched_frames[i-1][0])
            for i in range(1, len(matched_frames))
        )

        speeds = [pf.speed for pf, _ in matched_frames if pf.speed is not None]
        avg_speed = float(np.mean(speeds)) if speeds else 0.0

        # Time near ball handler
        time_near = sum(
            1 for pf, bf in matched_frames
            if math.sqrt((pf.x - bf.x)**2 + (pf.y - bf.y)**2) <= radius
        ) / self.sampling_rate

        # Count cuts (high-speed movements)
        cuts = sum(1 for pf, _ in matched_frames if pf.speed and pf.speed > 10.0)

        return {
            'distance_traveled': distance_traveled,
            'avg_speed': avg_speed,
            'cuts': cuts,
            'time_near_ball_handler': time_near,
            'total_time': len(matched_frames) / self.sampling_rate
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return {
            'total_frames': len(self.frames),
            'unique_players': len(self.frames_by_player),
            'patterns_identified': len(self.patterns),
            'tracking_duration': (
                self.frames[-1].timestamp - self.frames[0].timestamp
                if len(self.frames) >= 2 else 0.0
            )
        }

    def clear(self):
        """Clear all stored data"""
        self.frames.clear()
        self.frames_by_player.clear()
        self.patterns.clear()
        logger.info("Cleared all movement data")
