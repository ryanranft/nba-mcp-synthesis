"""
Zone Classifier - Wrapper for ESPN Coordinate System

Provides zone classification for shots using ESPN/hoopR coordinate system.
Transforms ESPN coordinates to shot_location.py coordinate system for classification.

ESPN Coordinate System:
- Origin: Center court (0, 0)
- Home basket: (+41.75, 0)
- Away basket: (-41.75, 0)
- Units: Feet from center court

Shot Location System (used by shot_location.py):
- Origin: Baseline left corner (0, 0)
- Basket: (25, 5.25) - center of court, 5.25 ft from baseline
- Court dimensions: 50 ft wide x 94 ft long
"""

import math
from typing import Tuple, Optional
from dataclasses import dataclass

from .shot_location import ShotLocation, ShotZone


@dataclass
class ClassifiedShot:
    """Shot with zone classification and metadata"""

    zone: str  # Zone name (e.g., "three_above_break_center")
    distance: float  # Distance from basket in feet
    angle: float  # Angle from basket in degrees

    # ESPN coordinates (original)
    espn_x: float
    espn_y: float

    # Shot location coordinates (transformed)
    court_x: Optional[float] = None
    court_y: Optional[float] = None


class ZoneClassifier:
    """
    Classifies shots into NBA-standard zones using ESPN coordinates.

    Transforms ESPN coordinates to court coordinates and uses existing
    shot_location.py classification logic.
    """

    # ESPN coordinate system
    HOME_BASKET_X = 41.75
    AWAY_BASKET_X = -41.75
    BASKET_Y = 0.0

    # Court coordinate system (shot_location.py)
    COURT_WIDTH = 50.0  # feet
    COURT_LENGTH = 94.0  # feet
    COURT_BASKET_X = 25.0  # center of court
    COURT_BASKET_Y = 5.25  # 5.25 ft from baseline

    def classify_shot(
        self,
        espn_x: float,
        espn_y: float,
        home_team_id: int,
        offensive_team_id: int,
        period: int = 1,
        made: bool = False,
        points: int = 0,
    ) -> ClassifiedShot:
        """
        Classify a shot into NBA zone using ESPN coordinates.

        Args:
            espn_x: ESPN X coordinate (feet from center court)
            espn_y: ESPN Y coordinate (feet from center court)
            home_team_id: ID of home team
            offensive_team_id: ID of shooting team
            period: Period/quarter number (1-4 regular, 5+ OT)
            made: Whether shot was made
            points: Points scored (0, 2, or 3)

        Returns:
            ClassifiedShot with zone, distance, angle, and coordinates
        """
        # Transform ESPN coordinates to court coordinates
        court_x, court_y = self._transform_espn_to_court(
            espn_x, espn_y, home_team_id, offensive_team_id, period
        )

        # Create ShotLocation object (triggers automatic classification)
        shot_loc = ShotLocation(x=court_x, y=court_y, made=made, points=points)

        # Convert angle from radians to degrees
        angle_degrees = math.degrees(shot_loc.angle)

        return ClassifiedShot(
            zone=shot_loc.zone.value,
            distance=shot_loc.distance,
            angle=angle_degrees,
            espn_x=espn_x,
            espn_y=espn_y,
            court_x=court_x,
            court_y=court_y,
        )

    def _transform_espn_to_court(
        self,
        espn_x: float,
        espn_y: float,
        home_team_id: int,
        offensive_team_id: int,
        period: int,
    ) -> Tuple[float, float]:
        """
        Transform ESPN coordinates to court coordinates.

        ESPN System:
        - Center court (0,0)
        - Home basket: (+41.75, 0) - camera right
        - Away basket: (-41.75, 0) - camera left
        - Coordinates are BROADCAST-RELATIVE (do not adjust for halftime switch)

        Court System:
        - Baseline corner (0,0)
        - Basket at (25, 5.25)

        NBA Rule:
        - Q1/Q2 (first half): Teams at original baskets
        - Q3/Q4 (second half): Teams switch baskets at halftime
        - OT odd periods: Same as first half
        - OT even periods: Switched baskets

        Args:
            espn_x: ESPN X coordinate
            espn_y: ESPN Y coordinate
            home_team_id: Home team ID
            offensive_team_id: Shooting team ID
            period: Period/quarter number (1-4 regular, 5+ OT)

        Returns:
            (court_x, court_y) tuple
        """
        # Determine which basket the team is shooting at THIS PERIOD
        is_home_team = int(offensive_team_id) == int(home_team_id)
        is_first_half = period <= 2  # Q1/Q2 are first half

        # First half (Q1/Q2): Original baskets
        # Second half (Q3/Q4): Switched baskets
        # OT: Odd periods (5,7,9...) = first half baskets, Even (6,8,10...) = switched
        if period <= 4:
            # Regular quarters
            if is_home_team:
                basket_x = self.HOME_BASKET_X if is_first_half else self.AWAY_BASKET_X
            else:
                basket_x = self.AWAY_BASKET_X if is_first_half else self.HOME_BASKET_X
        else:
            # Overtime - use odd/even logic
            is_odd_ot = period % 2 == 1
            if is_home_team:
                basket_x = self.HOME_BASKET_X if is_odd_ot else self.AWAY_BASKET_X
            else:
                basket_x = self.AWAY_BASKET_X if is_odd_ot else self.HOME_BASKET_X

        # Calculate position relative to basket
        rel_x = espn_x - basket_x
        rel_y = espn_y - self.BASKET_Y

        # Transform to court coordinates
        # The court system has basket at (25, 5.25)
        # X: Basket at center (25), left is 0, right is 50
        # Y: Basket 5.25 ft from baseline (0), opposite baseline at 94

        # Flip coordinates if shooting at negative basket (away)
        if basket_x < 0:
            # Shooting at away basket - flip X and Y
            court_x = self.COURT_BASKET_X - rel_x
            court_y = self.COURT_BASKET_Y - rel_y
        else:
            # Shooting at home basket - standard orientation
            court_x = self.COURT_BASKET_X + rel_x
            court_y = self.COURT_BASKET_Y + rel_y

        return court_x, court_y

    def get_zone_description(self, zone_name: str) -> str:
        """
        Get human-readable description of zone.

        Args:
            zone_name: Zone identifier (e.g., "three_above_break_center")

        Returns:
            Human-readable description
        """
        descriptions = {
            "restricted_area": "Restricted Area (< 4 ft)",
            "paint_non_ra": "Paint (Non-RA)",
            "mid_range_left": "Mid-Range Left",
            "mid_range_center": "Mid-Range Center",
            "mid_range_right": "Mid-Range Right",
            "three_left_corner": "Corner Three (Left)",
            "three_right_corner": "Corner Three (Right)",
            "three_above_break_left": "Above Break Three (Left)",
            "three_above_break_center": "Above Break Three (Center)",
            "three_above_break_right": "Above Break Three (Right)",
            "backcourt": "Backcourt",
        }
        return descriptions.get(zone_name, zone_name)


# Convenience function for quick classification
def classify_shot_espn(
    espn_x: float,
    espn_y: float,
    home_team_id: int,
    offensive_team_id: int,
    period: int = 1,
    made: bool = False,
    points: int = 0,
) -> ClassifiedShot:
    """
    Quick classification function for ESPN coordinates.

    Args:
        espn_x: ESPN X coordinate
        espn_y: ESPN Y coordinate
        home_team_id: Home team ID
        offensive_team_id: Shooting team ID
        period: Period/quarter number (1-4 regular, 5+ OT)
        made: Whether shot was made
        points: Points scored

    Returns:
        ClassifiedShot with zone and metadata
    """
    classifier = ZoneClassifier()
    return classifier.classify_shot(
        espn_x, espn_y, home_team_id, offensive_team_id, period, made, points
    )
