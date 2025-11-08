"""
NBA Play-by-Play Event Parser

Parses individual play-by-play events into structured box score statistics.
Based on event schema documented in docs/PLAY_BY_PLAY_EVENT_SCHEMA.md
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class BoxScoreEvent:
    """Represents a single box score contribution from an event."""
    player_id: int
    fga: int = 0
    fgm: int = 0
    fg3a: int = 0
    fg3m: int = 0
    fta: int = 0
    ftm: int = 0
    oreb: int = 0
    dreb: int = 0
    reb: int = 0
    ast: int = 0
    stl: int = 0
    blk: int = 0
    tov: int = 0
    pf: int = 0
    pts: int = 0


@dataclass
class ParsedEvent:
    """Fully parsed play-by-play event with box score contributions."""
    sequence_number: int
    type_text: str
    type_id: int
    text: str
    period: int
    clock: str
    away_score: int
    home_score: int

    # Box score contributions
    player_stats: List[BoxScoreEvent]

    # Possession tracking
    is_possession_ending: bool
    is_offensive_rebound: bool
    offensive_team_id: Optional[int]
    defensive_team_id: Optional[int]


class EventParser:
    """Parses NBA play-by-play events into box score statistics."""

    # Shot event types (all 54 shot types in database)
    # Note: Excludes 11 (Jump Ball), 70 (Shot Clock Turnover), 75 (Jumpball Violation), 615 (Jumpball)
    SHOT_TYPES = {
        # Basic shots
        92: 'Jump Shot',
        93: 'Hook Shot',
        94: 'Tip Shot',
        95: 'Layup Shot',
        96: 'Dunk Shot',

        # Running shots
        109: 'Running Layup Shot',
        113: 'Running Jump Shot',
        116: 'Running Dunk Shot',
        127: 'Layup Running Reverse',
        129: 'Running Finger Roll Layup',
        143: 'Running Alley Oop Layup Shot',
        146: 'Running Pullup Jump Shot',
        149: 'Running Alley Oop Dunk Shot',
        153: 'Running Reverse Dunk Shot',

        # Driving shots
        110: 'Driving Layup Shot',
        115: 'Driving Dunk Shot',
        119: 'Driving Hook Shot',
        126: 'Layup Driving Reverse',
        128: 'Driving Finger Roll Layup',
        134: 'Driving Jump Shot Bank',
        144: 'Driving Floating Jump Shot',
        145: 'Driving Floating Bank Jump Shot',
        152: 'Driving Reverse Dunk Shot',

        # Turnaround shots
        114: 'Turnaround Jump Shot',
        120: 'Turnaround Hook Shot',
        136: 'Turnaround Bank Jump Shot',
        137: 'Turnaround Fade Away Jump Shot',
        148: 'Turnaround Fadeaway Bank Jump Shot',

        # Cutting shots
        141: 'Cutting Layup Shot',
        142: 'Cutting Finger Roll Layup Shot',
        151: 'Cutting Dunk Shot',

        # Alley oop shots
        111: 'Alley Oop Layup Shot',
        118: 'Alley Oop Dunk Shot',

        # Reverse shots
        112: 'Reverse Layup Shot',
        117: 'Reverse Dunk Shot',

        # Fadeaway/stepback shots
        121: 'Fade Away Jump Shot',
        130: 'Floating Jump Shot',
        131: 'Pullup Jump Shot',
        132: 'Step Back Jump Shot',
        135: 'Fade Away Bank Jump Shot',
        147: 'Step Back Bank Jump Shot',

        # Putback shots
        125: 'Layup Shot Putback',
        138: 'Putback Dunk Shot',
        211: 'Dunk Putback Slam',
        212: 'Dunk Putback Reverse',

        # Bank shots
        122: 'Jump Shot Bank',
        123: 'Hook Shot Bank',
        133: 'Pullup Bank Jump Shot',
        139: 'Hook Driving Bank',
        140: 'Hook Turnaround Bank',
        209: 'Hook Jump Bank',
        210: 'Hook Running Bank',

        # Finger roll / tip shots
        124: 'Finger Roll Layup',
        150: 'Tip Dunk Shot',
    }

    # Free throw event types
    FREE_THROW_TYPES = {
        97: 'Free Throw - 1 of 1',
        98: 'Free Throw - 1 of 2',
        99: 'Free Throw - 2 of 2',
        100: 'Free Throw - 1 of 3',
        101: 'Free Throw - 2 of 3',
        102: 'Free Throw - 3 of 3',
        103: 'Free Throw - Technical',
    }

    # Turnover event types
    TURNOVER_TYPES = {
        62: 'Bad Pass\nTurnover',
        63: 'Lost Ball Turnover',
        64: 'Traveling',
        67: '3-Second Turnover',
        70: 'Shot Clock Turnover',
        74: 'Lane Violation Turnover',
        84: 'Offensive Foul Turnover',
        86: 'Out of Bounds - Step Turnover',
    }

    # Foul event types
    FOUL_TYPES = {
        22: 'Personal Take Foul',
        24: 'Offensive Charge',
        # 35: 'Technical Foul',  # REMOVED - Technical fouls don't count as personal fouls per NBA rules
        42: 'Offensive Foul',
        43: 'Loose Ball Foul',
        44: 'Shooting Foul',
        45: 'Personal Foul',
    }

    # ESPN Coordinate System (from ESPN/hoopR documentation)
    # Origin: Center court (0, 0)
    # Home team basket: (+41.75, 0)  - positive X
    # Away team basket: (-41.75, 0)  - negative X
    # Units: Feet from center court
    HOME_BASKET_X = 41.75
    AWAY_BASKET_X = -41.75
    BASKET_Y = 0.0

    # NBA 3-Point Line Specifications
    # Arc: 23.75 feet radius (when |y| <= 22 ft from basket)
    # Corner: 22 feet straight line (when |y| > 22 ft from basket, 3 ft from sideline)
    THREE_POINT_ARC_DISTANCE = 23.75
    THREE_POINT_CORNER_DISTANCE = 22.0
    CORNER_TRANSITION_Y = 22.0  # Y-distance from basket where arc transitions to corner

    def __init__(self, use_coordinates=True):
        """
        Initialize parser.

        Args:
            use_coordinates: If True, use coordinate geometry for 3-point detection when available.
                           Falls back to text-based detection when coordinates missing/invalid.
        """
        self.use_coordinates = use_coordinates

    def _is_three_pointer_by_coordinates(self, coord_x: float, coord_y: float,
                                         home_team_id: int, offensive_team_id: int) -> Optional[bool]:
        """
        Determine if shot is a 3-pointer based on court coordinates.

        Args:
            coord_x: X coordinate (feet from center court)
            coord_y: Y coordinate (feet from center court)
            home_team_id: ID of home team
            offensive_team_id: ID of offensive team (shooting team)

        Returns:
            True if 3-pointer, False if 2-pointer, None if coordinates invalid
        """
        # Check for invalid coordinates (overflow markers)
        if abs(coord_x) > 100 or abs(coord_y) > 100:
            return None

        # Determine which basket the offensive team is shooting at
        # Home team defends home basket (+41.75) and shoots at away basket (-41.75)
        # Away team defends away basket (-41.75) and shoots at home basket (+41.75)
        # Convert to int for comparison (team_id may be float)
        if int(offensive_team_id) == int(home_team_id):
            basket_x = self.HOME_BASKET_X  # Home shoots at home basket (defend away)
        else:
            basket_x = self.AWAY_BASKET_X  # Away shoots at away basket (defend home)
        basket_y = self.BASKET_Y

        # Calculate distance from basket
        rel_x = coord_x - basket_x
        rel_y = coord_y - basket_y
        distance = (rel_x**2 + rel_y**2)**0.5

        # Determine which 3-point line distance applies
        # Corner: 22 ft when shot is far from center (|y| > 22 ft from basket)
        # Arc: 23.75 ft when shot is near center (|y| <= 22 ft from basket)
        abs_y = abs(rel_y)
        if abs_y > self.CORNER_TRANSITION_Y:
            three_pt_line = self.THREE_POINT_CORNER_DISTANCE
        else:
            three_pt_line = self.THREE_POINT_ARC_DISTANCE

        # Shot is a 3-pointer if distance >= 3-point line at that position
        return distance >= three_pt_line

    def parse_event(self, event: Dict) -> ParsedEvent:
        """
        Parse a single play-by-play event into structured format.

        Args:
            event: Dictionary from hoopr_play_by_play row

        Returns:
            ParsedEvent with box score contributions and possession info
        """
        type_id = event.get('type_id')
        type_text = event.get('type_text', '')
        text = event.get('text', '')

        player_stats = []
        is_possession_ending = False
        is_offensive_rebound = False

        # Parse based on event type
        if type_id in self.SHOT_TYPES:
            stats, poss_ending = self._parse_shot_event(event)
            player_stats.extend(stats)
            is_possession_ending = poss_ending

        elif type_id in self.FREE_THROW_TYPES:
            stats, poss_ending = self._parse_free_throw_event(event)
            player_stats.extend(stats)
            is_possession_ending = poss_ending

        elif type_text in ['Offensive Rebound', 'Defensive Rebound']:
            stats, is_offensive_rebound, poss_ending = self._parse_rebound_event(event)
            player_stats.extend(stats)
            is_possession_ending = poss_ending

        elif type_id in self.TURNOVER_TYPES or 'Turnover' in type_text:
            stats = self._parse_turnover_event(event)
            player_stats.extend(stats)
            is_possession_ending = True  # All turnovers end possession

        elif type_id in self.FOUL_TYPES or ('Foul' in type_text and 'Technical' not in type_text):
            stats, poss_ending = self._parse_foul_event(event)
            player_stats.extend(stats)
            is_possession_ending = poss_ending

        return ParsedEvent(
            sequence_number=int(event.get('sequence_number', 0)),
            type_text=type_text,
            type_id=type_id,
            text=text,
            period=event.get('period_number', 1),
            clock=event.get('clock_display_value', ''),
            away_score=event.get('away_score', 0),
            home_score=event.get('home_score', 0),
            player_stats=player_stats,
            is_possession_ending=is_possession_ending,
            is_offensive_rebound=is_offensive_rebound,
            offensive_team_id=event.get('offensive_team_id'),  # Will be filled by possession tracker
            defensive_team_id=event.get('defensive_team_id'),
        )

    def _parse_shot_event(self, event: Dict) -> Tuple[List[BoxScoreEvent], bool]:
        """Parse shot attempt event with optional coordinate-based 3-point detection."""
        player_id = event.get('athlete_id_1')
        text = event.get('text', '').lower()

        if not player_id:
            return [], False

        stats = []
        possession_ending = False

        # Base: all shots are FGA +1
        shot_stat = BoxScoreEvent(player_id=int(player_id), fga=1)

        # Coordinate-based 3-pointer detection (most accurate)
        is_three_by_coords = None
        if self.use_coordinates:
            coord_x = event.get('coordinate_x')
            coord_y = event.get('coordinate_y')
            home_team_id = event.get('home_team_id')
            offensive_team_id = event.get('team_id')  # Shooting team

            if (coord_x is not None and coord_y is not None and
                home_team_id is not None and offensive_team_id is not None):
                is_three_by_coords = self._is_three_pointer_by_coordinates(
                    coord_x, coord_y, home_team_id, offensive_team_id
                )

        # Text-based 3-pointer detection (fallback)
        is_three_by_text = 'three point' in text or '3-point' in text

        # Distance-based 3-pointer detection (fallback)
        # NBA 3-point line: 22 ft in corners, 23.75 ft at arc
        # Only count >= 23 ft to avoid ambiguous 22-foot shots
        is_three_by_distance = False
        if not is_three_by_text:
            import re
            distance_match = re.search(r'(\d+)-foot', text)
            if distance_match:
                distance = int(distance_match.group(1))
                if distance >= 23:
                    is_three_by_distance = True

        # Determine final classification (priority: coordinates > text > distance)
        if is_three_by_coords is not None:
            is_three = is_three_by_coords
        elif is_three_by_text:
            is_three = True
        else:
            is_three = is_three_by_distance

        if is_three:
            shot_stat.fg3a = 1

        # Check outcome - handle both "makes/made" and "misses/missed"
        is_made = 'makes' in text or 'made' in text
        is_missed = 'misses' in text or 'missed' in text
        is_blocked = 'block' in text  # Blocked shots are always missed

        if is_made and not is_missed and not is_blocked:  # Avoid "made X misses" edge cases and blocks
            # Made shot
            shot_stat.fgm = 1

            if is_three:
                shot_stat.fg3m = 1
                shot_stat.pts = 3
            else:
                shot_stat.pts = 2

            # Check for assist - handle both "(assists)" and "Assisted by"
            assister_id = event.get('athlete_id_2')
            has_assist = 'assist' in text  # Catches both patterns
            if has_assist and assister_id:
                assist_stat = BoxScoreEvent(player_id=int(assister_id), ast=1)
                stats.append(assist_stat)

            # Made shots end possession (unless and-1, handled by following foul)
            possession_ending = True

        else:
            # Missed or blocked shot
            if is_blocked:
                blocker_id = event.get('athlete_id_2')
                if blocker_id:
                    block_stat = BoxScoreEvent(player_id=int(blocker_id), blk=1)
                    stats.append(block_stat)

            possession_ending = False  # Missed/blocked shots can be rebounded

        stats.insert(0, shot_stat)
        return stats, possession_ending

    def _parse_free_throw_event(self, event: Dict) -> Tuple[List[BoxScoreEvent], bool]:
        """Parse free throw event."""
        player_id = event.get('athlete_id_1')
        text = event.get('text', '').lower()
        type_text = event.get('type_text', '')

        if not player_id:
            return [], False

        ft_stat = BoxScoreEvent(player_id=int(player_id), fta=1)

        # Handle both "makes/made" and "misses/missed"
        is_made = 'makes' in text or 'made' in text
        is_missed = 'misses' in text or 'missed' in text

        if is_made and not is_missed:
            ft_stat.ftm = 1
            ft_stat.pts = 1

        # Possession ends after FINAL free throw in sequence
        is_final_ft = (
            '1 of 1' in type_text or
            '2 of 2' in type_text or
            '3 of 3' in type_text or
            'Technical' in type_text
        )
        possession_ending = is_final_ft

        return [ft_stat], possession_ending

    def _parse_rebound_event(self, event: Dict) -> Tuple[List[BoxScoreEvent], bool, bool]:
        """
        Parse rebound event.

        Returns:
            (stats, is_offensive_rebound, possession_ending)
        """
        player_id = event.get('athlete_id_1')
        type_text = event.get('type_text', '')

        is_offensive = 'Offensive' in type_text

        # Team rebounds (no player attribution)
        if not player_id:
            # Team rebound - tracked separately
            return [], is_offensive, not is_offensive

        # Player rebound
        reb_stat = BoxScoreEvent(player_id=int(player_id), reb=1)

        if is_offensive:
            reb_stat.oreb = 1
            # Offensive rebounds extend possession
            possession_ending = False
        else:
            reb_stat.dreb = 1
            # Defensive rebounds end possession (new possession for rebounding team)
            possession_ending = True

        return [reb_stat], is_offensive, possession_ending

    def _parse_turnover_event(self, event: Dict) -> List[BoxScoreEvent]:
        """Parse turnover event."""
        player_id = event.get('athlete_id_1')
        type_id = event.get('type_id')
        text = event.get('text', '')

        # Skip type 84 "Offensive Foul Turnover" - it duplicates type 42 "Offensive Foul"
        # Type 42 creates both the foul (pf+1) and turnover (tov+1)
        # Type 84 would create a duplicate turnover
        if type_id == 84:
            return []

        stats = []

        # Turnover
        if player_id:
            tov_stat = BoxScoreEvent(player_id=int(player_id), tov=1)
            stats.append(tov_stat)
        # else: team turnover (tracked separately)

        # Check for steal - handle both modern "steals)" and old "Stolen by"
        stealer_id = event.get('athlete_id_2')
        if 'steal' in text.lower() and stealer_id:
            steal_stat = BoxScoreEvent(player_id=int(stealer_id), stl=1)
            stats.append(steal_stat)

        return stats

    def _parse_foul_event(self, event: Dict) -> Tuple[List[BoxScoreEvent], bool]:
        """Parse foul event."""
        player_id = event.get('athlete_id_1')
        type_id = event.get('type_id')
        type_text = event.get('type_text', '')

        # Skip type 84 "Offensive Foul Turnover" - it duplicates type 42 "Offensive Foul"
        # Type 84 always follows type 42 for the same player, creating double-count
        if type_id == 84:
            return [], True  # Still mark as possession-ending

        if not player_id:
            return [], False

        foul_stat = BoxScoreEvent(player_id=int(player_id), pf=1)

        # Offensive fouls cause turnovers AND end possession
        is_offensive_foul = 'Offensive' in type_text or 'Charge' in type_text
        if is_offensive_foul:
            foul_stat.tov = 1
            possession_ending = True
        else:
            # Defensive fouls don't end possession (free throws follow)
            possession_ending = False

        return [foul_stat], possession_ending


def aggregate_player_stats(events: List[BoxScoreEvent]) -> Dict[int, Dict]:
    """
    Aggregate box score events into player totals.

    Args:
        events: List of BoxScoreEvent objects

    Returns:
        Dictionary mapping player_id to stat totals
    """
    player_totals = {}

    for event in events:
        player_id = event.player_id

        if player_id not in player_totals:
            player_totals[player_id] = {
                'fga': 0, 'fgm': 0, 'fg3a': 0, 'fg3m': 0,
                'fta': 0, 'ftm': 0, 'oreb': 0, 'dreb': 0, 'reb': 0,
                'ast': 0, 'stl': 0, 'blk': 0, 'tov': 0, 'pf': 0, 'pts': 0
            }

        # Accumulate stats
        for stat in ['fga', 'fgm', 'fg3a', 'fg3m', 'fta', 'ftm',
                     'oreb', 'dreb', 'reb', 'ast', 'stl', 'blk', 'tov', 'pf', 'pts']:
            player_totals[player_id][stat] += getattr(event, stat)

    return player_totals
