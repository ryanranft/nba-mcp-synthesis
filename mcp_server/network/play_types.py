"""
Play Type Analysis (Agent 16, Module 4)

Analyzes different offensive play types and their effectiveness:
- Play type classification (pick and roll, isolation, post-up, etc.)
- Play effectiveness metrics
- Play sequence tracking
- Context-aware analysis (score, time, etc.)
- Player-specific play preferences

Integrates with:
- passing_network: Passes during plays
- spatial: Player positioning during plays
- shot_location: Shot outcomes from plays
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class PlayType(Enum):
    """Types of offensive plays"""

    # Ball-handler plays
    PICK_AND_ROLL = "pick_and_roll"  # Ball handler pick and roll
    ISOLATION = "isolation"  # Iso play
    TRANSITION = "transition"  # Fast break

    # Off-ball plays
    SPOT_UP = "spot_up"  # Catch and shoot
    CUT = "cut"  # Cutting to basket
    OFF_SCREEN = "off_screen"  # Coming off screen
    HANDOFF = "handoff"  # Hand-off action

    # Post plays
    POST_UP = "post_up"  # Post-up play

    # Team plays
    MOTION = "motion"  # Motion offense
    SET_PLAY = "set_play"  # Designed play

    # Offensive rebounds
    PUTBACK = "putback"  # Offensive rebound putback

    # Other
    MISCELLANEOUS = "miscellaneous"


@dataclass
class PlayOutcome:
    """Outcome of a play"""

    resulted_in_shot: bool
    shot_made: Optional[bool] = None
    points_scored: int = 0
    resulted_in_turnover: bool = False
    resulted_in_foul: bool = False
    free_throws_made: int = 0
    free_throws_attempted: int = 0

    def points_per_play(self) -> float:
        """Calculate points per play (PPP)"""
        return float(self.points_scored)

    def is_successful(self) -> bool:
        """Determine if play was successful"""
        if self.resulted_in_turnover:
            return False
        if self.resulted_in_shot and self.shot_made:
            return True
        if self.resulted_in_foul and self.free_throws_made > 0:
            return True
        return self.points_scored > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'resulted_in_shot': self.resulted_in_shot,
            'shot_made': self.shot_made,
            'points_scored': self.points_scored,
            'turnover': self.resulted_in_turnover,
            'foul_drawn': self.resulted_in_foul,
            'free_throws': f"{self.free_throws_made}/{self.free_throws_attempted}",
            'successful': self.is_successful(),
            'ppp': self.points_per_play()
        }


@dataclass
class PlaySequence:
    """Complete play sequence"""

    play_id: str
    play_type: PlayType
    primary_player_id: str  # Main ball handler/shooter
    secondary_player_id: Optional[str] = None  # Screener/passer
    timestamp: float = 0.0
    game_id: Optional[str] = None

    # Context
    quarter: int = 1
    time_remaining: float = 0.0
    score_differential: int = 0  # Positive = team ahead

    # Play characteristics
    outcome: Optional[PlayOutcome] = None
    passes_in_play: int = 0
    duration: float = 0.0  # Seconds

    # Defenders involved
    primary_defender_id: Optional[str] = None

    def __post_init__(self):
        """Initialize default outcome if not provided"""
        if self.outcome is None:
            self.outcome = PlayOutcome(resulted_in_shot=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'play_id': self.play_id,
            'play_type': self.play_type.value,
            'primary_player': self.primary_player_id,
            'secondary_player': self.secondary_player_id,
            'quarter': self.quarter,
            'time_remaining': self.time_remaining,
            'score_diff': self.score_differential,
            'outcome': self.outcome.to_dict() if self.outcome else None,
            'passes': self.passes_in_play,
            'duration': self.duration
        }


@dataclass
class PlayTypeEfficiency:
    """Efficiency metrics for a specific play type"""

    play_type: PlayType
    player_id: Optional[str] = None  # Specific player or None for team

    # Volume
    total_plays: int = 0
    possessions_used: int = 0

    # Outcomes
    shots_attempted: int = 0
    shots_made: int = 0
    turnovers: int = 0
    fouls_drawn: int = 0

    # Scoring
    total_points: int = 0
    points_per_play: float = 0.0

    # Efficiency
    effective_fg_pct: float = 0.0
    turnover_rate: float = 0.0
    usage_rate: float = 0.0  # % of possessions ending in this play type

    def __post_init__(self):
        """Compute efficiency metrics"""
        if self.total_plays > 0:
            self.points_per_play = self.total_points / self.total_plays

            if self.shots_attempted > 0:
                # Simplified eFG% (would need 3PT data for accuracy)
                self.effective_fg_pct = self.shots_made / self.shots_attempted

            self.turnover_rate = self.turnovers / self.total_plays

    def efficiency_score(self) -> float:
        """
        Combined efficiency score (0-100).

        Higher = more efficient play type
        """
        # PPP component (normalize to 0-1, assuming 1.5 PPP is elite)
        ppp_component = min(self.points_per_play / 1.5, 1.0) * 50

        # Success rate component (FG% + foul drawing)
        success_rate = (self.shots_made + self.fouls_drawn) / max(self.total_plays, 1)
        success_component = min(success_rate, 1.0) * 30

        # Low turnover component
        turnover_component = max(0, (1.0 - self.turnover_rate * 2)) * 20

        return ppp_component + success_component + turnover_component

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'play_type': self.play_type.value,
            'player_id': self.player_id,
            'total_plays': self.total_plays,
            'points_per_play': self.points_per_play,
            'fg_pct': self.shots_made / max(self.shots_attempted, 1),
            'turnover_rate': self.turnover_rate,
            'efficiency_score': self.efficiency_score(),
            'shots': f"{self.shots_made}/{self.shots_attempted}",
        }


class PlayTypeAnalyzer:
    """
    Analyze play types and their effectiveness.

    Features:
    - Track all play sequences
    - Calculate play type efficiency
    - Identify player strengths/weaknesses
    - Context-aware analysis (clutch, etc.)
    - Recommend optimal play calls
    """

    def __init__(self):
        """Initialize play type analyzer"""
        self.plays: List[PlaySequence] = []
        self.plays_by_type: Dict[PlayType, List[PlaySequence]] = {pt: [] for pt in PlayType}
        self.plays_by_player: Dict[str, List[PlaySequence]] = {}

        logger.info("PlayTypeAnalyzer initialized")

    def add_play(self, play: PlaySequence):
        """Add a play sequence"""
        self.plays.append(play)

        # Index by type
        self.plays_by_type[play.play_type].append(play)

        # Index by player
        if play.primary_player_id not in self.plays_by_player:
            self.plays_by_player[play.primary_player_id] = []
        self.plays_by_player[play.primary_player_id].append(play)

    def add_plays(self, plays: List[PlaySequence]):
        """Add multiple plays"""
        for play in plays:
            self.add_play(play)

    def calculate_play_type_efficiency(
        self,
        play_type: PlayType,
        player_id: Optional[str] = None,
        context_filter: Optional[Dict[str, Any]] = None
    ) -> PlayTypeEfficiency:
        """
        Calculate efficiency for a play type.

        Args:
            play_type: Type of play
            player_id: Specific player (None = all players)
            context_filter: Optional context filters (quarter, score_diff, etc.)

        Returns:
            PlayTypeEfficiency object
        """
        # Filter plays
        if player_id:
            plays = [
                p for p in self.plays_by_player.get(player_id, [])
                if p.play_type == play_type
            ]
        else:
            plays = self.plays_by_type[play_type]

        # Apply context filter
        if context_filter:
            plays = self._apply_context_filter(plays, context_filter)

        if not plays:
            return PlayTypeEfficiency(play_type=play_type, player_id=player_id)

        # Calculate metrics
        total_plays = len(plays)
        shots_attempted = sum(1 for p in plays if p.outcome and p.outcome.resulted_in_shot)
        shots_made = sum(
            1 for p in plays
            if p.outcome and p.outcome.resulted_in_shot and p.outcome.shot_made
        )
        turnovers = sum(1 for p in plays if p.outcome and p.outcome.resulted_in_turnover)
        fouls_drawn = sum(1 for p in plays if p.outcome and p.outcome.resulted_in_foul)
        total_points = sum(p.outcome.points_scored for p in plays if p.outcome)

        return PlayTypeEfficiency(
            play_type=play_type,
            player_id=player_id,
            total_plays=total_plays,
            possessions_used=total_plays,  # Simplified
            shots_attempted=shots_attempted,
            shots_made=shots_made,
            turnovers=turnovers,
            fouls_drawn=fouls_drawn,
            total_points=total_points
        )

    def get_player_play_profile(
        self,
        player_id: str
    ) -> Dict[str, Any]:
        """
        Get play type profile for a player.

        Args:
            player_id: Player identifier

        Returns:
            Dictionary with play type breakdown and efficiency
        """
        plays = self.plays_by_player.get(player_id, [])

        if not plays:
            return {'player_id': player_id, 'total_plays': 0}

        # Count by play type
        play_type_counts = {}
        for play_type in PlayType:
            count = sum(1 for p in plays if p.play_type == play_type)
            if count > 0:
                play_type_counts[play_type.value] = count

        # Calculate efficiency for each play type
        play_type_efficiencies = {}
        for play_type in PlayType:
            efficiency = self.calculate_play_type_efficiency(play_type, player_id)
            if efficiency.total_plays > 0:
                play_type_efficiencies[play_type.value] = {
                    'plays': efficiency.total_plays,
                    'ppp': efficiency.points_per_play,
                    'efficiency_score': efficiency.efficiency_score()
                }

        # Find best/worst play types
        if play_type_efficiencies:
            best_play_type = max(
                play_type_efficiencies.items(),
                key=lambda x: x[1]['efficiency_score']
            )
            worst_play_type = min(
                play_type_efficiencies.items(),
                key=lambda x: x[1]['efficiency_score']
            )
        else:
            best_play_type = None
            worst_play_type = None

        return {
            'player_id': player_id,
            'total_plays': len(plays),
            'play_type_distribution': play_type_counts,
            'play_type_efficiency': play_type_efficiencies,
            'best_play_type': best_play_type[0] if best_play_type else None,
            'worst_play_type': worst_play_type[0] if worst_play_type else None,
        }

    def analyze_clutch_performance(
        self,
        player_id: Optional[str] = None,
        clutch_time_remaining: float = 2.0,  # Last 2 minutes
        close_score_diff: int = 5  # Within 5 points
    ) -> Dict[str, Any]:
        """
        Analyze clutch time performance.

        Args:
            player_id: Specific player (None = all players)
            clutch_time_remaining: Definition of clutch time (minutes)
            close_score_diff: Definition of close game (points)

        Returns:
            Dictionary with clutch performance metrics
        """
        # Filter to clutch situations
        clutch_filter = {
            'max_time_remaining': clutch_time_remaining,
            'max_score_diff': close_score_diff
        }

        if player_id:
            plays = self.plays_by_player.get(player_id, [])
        else:
            plays = self.plays

        clutch_plays = self._apply_context_filter(plays, clutch_filter)

        if not clutch_plays:
            return {'clutch_plays': 0}

        # Calculate clutch efficiency
        total_clutch = len(clutch_plays)
        clutch_points = sum(p.outcome.points_scored for p in clutch_plays if p.outcome)
        clutch_ppp = clutch_points / total_clutch if total_clutch > 0 else 0.0

        # Success rate
        successful = sum(1 for p in clutch_plays if p.outcome and p.outcome.is_successful())
        success_rate = successful / total_clutch if total_clutch > 0 else 0.0

        # Compare to overall performance
        if player_id:
            overall_plays = self.plays_by_player.get(player_id, [])
        else:
            overall_plays = self.plays

        overall_points = sum(p.outcome.points_scored for p in overall_plays if p.outcome)
        overall_ppp = overall_points / len(overall_plays) if overall_plays else 0.0

        clutch_improvement = clutch_ppp - overall_ppp

        return {
            'player_id': player_id,
            'clutch_plays': total_clutch,
            'clutch_ppp': clutch_ppp,
            'clutch_success_rate': success_rate,
            'overall_ppp': overall_ppp,
            'clutch_vs_overall': clutch_improvement,
            'is_clutch_performer': clutch_improvement > 0.1
        }

    def recommend_play_call(
        self,
        player_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend best play type for a player in given context.

        Args:
            player_id: Player identifier
            context: Game context (score_diff, time_remaining, etc.)

        Returns:
            Dictionary with recommendation and reasoning
        """
        plays = self.plays_by_player.get(player_id, [])

        if not plays:
            return {'error': 'No play data for player'}

        # Apply context filter if provided
        if context:
            filtered_plays = self._apply_context_filter(plays, context)
            if filtered_plays:
                plays = filtered_plays

        # Calculate efficiency for each play type
        efficiencies = {}
        for play_type in PlayType:
            eff = self.calculate_play_type_efficiency(play_type, player_id, context)
            if eff.total_plays >= 3:  # Need minimum sample size
                efficiencies[play_type] = eff

        if not efficiencies:
            return {'error': 'Insufficient data for recommendation'}

        # Find best play type
        best_play_type = max(
            efficiencies.items(),
            key=lambda x: x[1].efficiency_score()
        )

        play_type, efficiency = best_play_type

        return {
            'recommended_play': play_type.value,
            'efficiency_score': efficiency.efficiency_score(),
            'points_per_play': efficiency.points_per_play,
            'sample_size': efficiency.total_plays,
            'reason': f"{efficiency.points_per_play:.2f} PPP on {efficiency.total_plays} plays"
        }

    def _apply_context_filter(
        self,
        plays: List[PlaySequence],
        context_filter: Dict[str, Any]
    ) -> List[PlaySequence]:
        """Apply context filtering to plays"""
        filtered = plays

        if 'quarter' in context_filter:
            filtered = [p for p in filtered if p.quarter == context_filter['quarter']]

        if 'max_time_remaining' in context_filter:
            max_time = context_filter['max_time_remaining']
            filtered = [p for p in filtered if p.time_remaining <= max_time]

        if 'min_time_remaining' in context_filter:
            min_time = context_filter['min_time_remaining']
            filtered = [p for p in filtered if p.time_remaining >= min_time]

        if 'max_score_diff' in context_filter:
            max_diff = context_filter['max_score_diff']
            filtered = [p for p in filtered if abs(p.score_differential) <= max_diff]

        if 'winning' in context_filter:
            if context_filter['winning']:
                filtered = [p for p in filtered if p.score_differential > 0]
            else:
                filtered = [p for p in filtered if p.score_differential < 0]

        return filtered

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            'total_plays': len(self.plays),
            'unique_players': len(self.plays_by_player),
            'play_type_distribution': {
                pt.value: len(plays)
                for pt, plays in self.plays_by_type.items()
                if len(plays) > 0
            },
            'avg_points_per_play': float(np.mean([
                p.outcome.points_scored for p in self.plays if p.outcome
            ])) if self.plays else 0.0
        }

    def clear(self):
        """Clear all stored data"""
        self.plays.clear()
        self.plays_by_type = {pt: [] for pt in PlayType}
        self.plays_by_player.clear()
        logger.info("Cleared all play type data")
