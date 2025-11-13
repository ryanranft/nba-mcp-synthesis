"""
NBA Possession Tracker

Groups play-by-play events into discrete possessions for possession-based analytics.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from .event_parser import ParsedEvent, EventParser


@dataclass
class Possession:
    """Represents a single possession in a basketball game."""

    possession_number: int
    offensive_team_id: int
    defensive_team_id: int
    start_sequence: int
    end_sequence: int
    period: int
    start_clock: str
    end_clock: str

    # Events in this possession
    events: List[ParsedEvent] = field(default_factory=list)

    # Possession outcome
    points_scored: int = 0
    ended_by: str = ""  # 'made_shot', 'defensive_rebound', 'turnover', 'end_period'

    # Advanced metrics
    num_shot_attempts: int = 0
    offensive_rebounds: int = 0
    turnovers: int = 0


class PossessionTracker:
    """Tracks possessions from play-by-play events."""

    def __init__(self, home_team_id: int, away_team_id: int):
        """
        Initialize possession tracker.

        Args:
            home_team_id: ID of home team
            away_team_id: ID of away team
        """
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.parser = EventParser()

    def group_events_into_possessions(self, events: List[Dict]) -> List[Possession]:
        """
        Group play-by-play events into possessions.

        Args:
            events: List of raw event dictionaries from hoopr_play_by_play

        Returns:
            List of Possession objects
        """
        possessions = []
        current_possession_events = []
        current_offensive_team = None
        possession_number = 0

        # Parse all events first
        parsed_events = [self.parser.parse_event(event) for event in events]

        for i, parsed_event in enumerate(parsed_events):
            # Skip non-basketball events (timeouts, substitutions, etc.)
            if self._is_administrative_event(parsed_event):
                continue

            # Determine offensive team for this event
            offensive_team = self._determine_offensive_team(
                parsed_event, current_offensive_team, events[i]
            )

            # Check if possession changes
            possession_changed = (
                offensive_team != current_offensive_team
                and current_offensive_team is not None
            )

            # Start new possession if needed
            if possession_changed or current_offensive_team is None:
                # Finalize previous possession
                if current_possession_events:
                    possession = self._finalize_possession(
                        possession_number,
                        current_offensive_team,
                        current_possession_events,
                    )
                    possessions.append(possession)
                    possession_number += 1

                # Start new possession
                current_possession_events = []
                current_offensive_team = offensive_team

            # Add event to current possession
            current_possession_events.append(parsed_event)

            # Check if this event ends the possession
            if parsed_event.is_possession_ending:
                possession = self._finalize_possession(
                    possession_number, current_offensive_team, current_possession_events
                )
                possessions.append(possession)
                possession_number += 1

                # Next event will start new possession
                current_possession_events = []
                current_offensive_team = None  # Will be determined from next event

        # Finalize any remaining possession
        if current_possession_events and current_offensive_team:
            possession = self._finalize_possession(
                possession_number, current_offensive_team, current_possession_events
            )
            possessions.append(possession)

        return possessions

    def _is_administrative_event(self, event: ParsedEvent) -> bool:
        """Check if event is administrative (timeout, substitution, etc.)."""
        administrative_types = [
            "Substitution",
            "Full Timeout",
            "Short Timeout",
            "Official Time Out",
            "Jump Ball",  # Will handle separately for possession determination
        ]
        return event.type_text in administrative_types

    def _determine_offensive_team(
        self,
        parsed_event: ParsedEvent,
        current_offensive_team: Optional[int],
        raw_event: Dict,
    ) -> int:
        """
        Determine which team has possession for this event.

        Args:
            parsed_event: Parsed event object
            current_offensive_team: Current team with possession (or None)
            raw_event: Raw event dict (for team_id fields if available)

        Returns:
            Team ID that has possession
        """
        # For rebound events, determine based on rebound type
        if "Rebound" in parsed_event.type_text:
            if parsed_event.is_offensive_rebound:
                # Offensive rebound - same team keeps possession
                return current_offensive_team
            else:
                # Defensive rebound - possession changes
                if current_offensive_team == self.home_team_id:
                    return self.away_team_id
                else:
                    return self.home_team_id

        # For turnovers, possession changes to other team
        if "Turnover" in parsed_event.type_text:
            # Possession goes to OTHER team
            if current_offensive_team == self.home_team_id:
                return self.away_team_id
            else:
                return self.home_team_id

        # For made shots, possession changes (unless and-1)
        if any(stat.fgm > 0 for stat in parsed_event.player_stats):
            # Made shot - possession will change after this
            return current_offensive_team

        # For other events, maintain current possession
        if current_offensive_team:
            return current_offensive_team

        # If no current possession, try to infer from score change
        # (This handles start of game, after timeouts, etc.)
        return self._infer_team_from_context(parsed_event, raw_event)

    def _infer_team_from_context(
        self, parsed_event: ParsedEvent, raw_event: Dict
    ) -> int:
        """
        Infer offensive team from context when not explicitly known.

        This is used at the start of the game or after ambiguous events.
        """
        # Check if there's a team_id field in the raw event
        team_id = raw_event.get("team_id") or raw_event.get("offensive_team_id")
        if team_id:
            return int(team_id)

        # Check if player is from home or away team (would need player-team mapping)
        # For now, default to home team (will be improved with player roster data)
        return self.home_team_id

    def _finalize_possession(
        self, possession_number: int, offensive_team_id: int, events: List[ParsedEvent]
    ) -> Possession:
        """
        Finalize a possession and calculate summary statistics.

        Args:
            possession_number: Sequential possession number
            offensive_team_id: Team that had possession
            events: List of events in this possession

        Returns:
            Completed Possession object
        """
        if not events:
            # Empty possession (shouldn't happen, but handle gracefully)
            return Possession(
                possession_number=possession_number,
                offensive_team_id=offensive_team_id,
                defensive_team_id=self._get_defensive_team(offensive_team_id),
                start_sequence=0,
                end_sequence=0,
                period=1,
                start_clock="",
                end_clock="",
            )

        defensive_team_id = self._get_defensive_team(offensive_team_id)
        first_event = events[0]
        last_event = events[-1]

        # Calculate possession outcome
        points_scored = sum(stat.pts for event in events for stat in event.player_stats)

        # Count shot attempts
        num_shot_attempts = sum(
            stat.fga for event in events for stat in event.player_stats
        )

        # Count offensive rebounds
        offensive_rebounds = sum(1 for event in events if event.is_offensive_rebound)

        # Count turnovers
        turnovers = sum(stat.tov for event in events for stat in event.player_stats)

        # Determine how possession ended
        ended_by = self._determine_possession_ending(last_event)

        return Possession(
            possession_number=possession_number,
            offensive_team_id=offensive_team_id,
            defensive_team_id=defensive_team_id,
            start_sequence=first_event.sequence_number,
            end_sequence=last_event.sequence_number,
            period=first_event.period,
            start_clock=first_event.clock,
            end_clock=last_event.clock,
            events=events,
            points_scored=points_scored,
            ended_by=ended_by,
            num_shot_attempts=num_shot_attempts,
            offensive_rebounds=offensive_rebounds,
            turnovers=turnovers,
        )

    def _get_defensive_team(self, offensive_team_id: int) -> int:
        """Get the defensive team ID given the offensive team."""
        if offensive_team_id == self.home_team_id:
            return self.away_team_id
        else:
            return self.home_team_id

    def _determine_possession_ending(self, last_event: ParsedEvent) -> str:
        """Determine how the possession ended."""
        if "Rebound" in last_event.type_text and not last_event.is_offensive_rebound:
            return "defensive_rebound"
        elif "Turnover" in last_event.type_text:
            return "turnover"
        elif any(stat.fgm > 0 for stat in last_event.player_stats):
            return "made_shot"
        elif "End Period" in last_event.type_text or "End Game" in last_event.type_text:
            return "end_period"
        else:
            return "unknown"


def calculate_true_possessions(possessions: List[Possession]) -> Dict[int, int]:
    """
    Calculate true possession count for each team.

    Args:
        possessions: List of Possession objects

    Returns:
        Dictionary mapping team_id to possession count
    """
    team_possessions = {}

    for possession in possessions:
        team_id = possession.offensive_team_id
        team_possessions[team_id] = team_possessions.get(team_id, 0) + 1

    return team_possessions


def estimate_possessions_from_stats(
    fga: int, fta: int, oreb: int, tov: int, ft_constant: float = 0.44
) -> float:
    """
    Estimate possessions using standard formula.

    Args:
        fga: Field goal attempts
        fta: Free throw attempts
        oreb: Offensive rebounds
        tov: Turnovers
        ft_constant: Free throw constant (default 0.44)

    Returns:
        Estimated possession count
    """
    return fga + ft_constant * fta - oreb + tov
