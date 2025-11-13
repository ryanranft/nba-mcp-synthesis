"""
NBA Play-by-Play Processing Module

Converts raw play-by-play events into box score statistics and possession tracking.
"""

from .event_parser import (
    EventParser,
    BoxScoreEvent,
    ParsedEvent,
    aggregate_player_stats,
)
from .possession_tracker import (
    PossessionTracker,
    Possession,
    calculate_true_possessions,
)
from .box_score_aggregator import (
    BoxScoreAggregator,
    PlayerBoxScore,
    TeamBoxScore,
    GameBoxScore,
)

__all__ = [
    "EventParser",
    "BoxScoreEvent",
    "ParsedEvent",
    "aggregate_player_stats",
    "PossessionTracker",
    "Possession",
    "calculate_true_possessions",
    "BoxScoreAggregator",
    "PlayerBoxScore",
    "TeamBoxScore",
    "GameBoxScore",
]
