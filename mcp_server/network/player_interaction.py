"""
Player Interaction Analysis (Agent 16, Module 2)

Analyzes how players perform together on the court:
- Plus/minus when playing together
- Two-player synergy metrics
- Lineup performance analysis
- On-court chemistry indicators
- Complement vs redundancy analysis

Integrates with:
- passing_network: Pass-based interactions
- team_chemistry: Overall team performance
- simulations: Predicted performance together
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PlayerInteraction:
    """Interaction data for two players playing together"""

    player1_id: str
    player2_id: str

    # Time together
    possessions_together: int
    minutes_together: float

    # Performance metrics
    points_for: int  # Points scored while both on court
    points_against: int  # Points allowed while both on court
    plus_minus: float  # Net rating

    # Advanced metrics
    offensive_rating: Optional[float] = None  # Points per 100 possessions
    defensive_rating: Optional[float] = None  # Points allowed per 100 poss
    net_rating: Optional[float] = None  # Off rating - Def rating

    # Synergy indicators
    assists_between: int = 0  # Assists from one to the other
    passes_between: int = 0  # Total passes between them

    def __post_init__(self):
        """Compute advanced metrics"""
        if self.possessions_together > 0:
            if self.offensive_rating is None:
                self.offensive_rating = (
                    self.points_for / self.possessions_together
                ) * 100
            if self.defensive_rating is None:
                self.defensive_rating = (
                    self.points_against / self.possessions_together
                ) * 100
            if self.net_rating is None:
                self.net_rating = self.offensive_rating - self.defensive_rating

    def synergy_score(self) -> float:
        """
        Calculate synergy score (0-1).

        Considers:
        - Net rating (performance together)
        - Assist connection (passing synergy)
        - Minutes together (trust/chemistry)
        """
        # Net rating component (normalize to 0-1, assuming +/-20 range)
        net_rating_component = (
            min(max((self.net_rating + 20) / 40, 0), 1) * 0.5
            if self.net_rating
            else 0.5
        )

        # Assist synergy (normalize to 0-1, assuming 10 assists is high)
        assist_component = min(self.assists_between / 10.0, 1.0) * 0.3

        # Time together component (normalize, 20 min is high)
        time_component = min(self.minutes_together / 20.0, 1.0) * 0.2

        return net_rating_component + assist_component + time_component

    def complement_score(self) -> float:
        """
        Estimate how well players complement each other.

        Higher score = better complementarity
        Based on performance metrics
        """
        # If net rating is positive and they have good synergy, they complement each other
        if self.net_rating and self.net_rating > 5:
            return min(self.synergy_score() * 1.2, 1.0)
        elif self.net_rating and self.net_rating < -5:
            return max(self.synergy_score() * 0.8, 0.0)
        else:
            return self.synergy_score()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "possessions_together": self.possessions_together,
            "minutes_together": self.minutes_together,
            "plus_minus": self.plus_minus,
            "offensive_rating": self.offensive_rating,
            "defensive_rating": self.defensive_rating,
            "net_rating": self.net_rating,
            "assists_between": self.assists_between,
            "synergy_score": self.synergy_score(),
            "complement_score": self.complement_score(),
        }


@dataclass
class InteractionMetrics:
    """Aggregate interaction metrics for a player"""

    player_id: str

    # Best/worst teammates
    best_teammate_id: Optional[str] = None
    best_teammate_net_rating: float = 0.0
    worst_teammate_id: Optional[str] = None
    worst_teammate_net_rating: float = 0.0

    # Overall metrics
    avg_net_rating_with_teammates: float = 0.0
    total_teammates: int = 0

    # Synergy scores
    high_synergy_teammates: List[str] = field(default_factory=list)
    low_synergy_teammates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "player_id": self.player_id,
            "best_teammate": self.best_teammate_id,
            "best_net_rating": self.best_teammate_net_rating,
            "worst_teammate": self.worst_teammate_id,
            "worst_net_rating": self.worst_teammate_net_rating,
            "avg_net_rating": self.avg_net_rating_with_teammates,
            "total_teammates": self.total_teammates,
            "high_synergy_count": len(self.high_synergy_teammates),
            "low_synergy_count": len(self.low_synergy_teammates),
        }


class InteractionAnalyzer:
    """
    Analyze player interactions and on-court chemistry.

    Features:
    - Track performance of player pairs
    - Identify synergistic combinations
    - Detect redundancy (negative synergy)
    - Analyze lineup effectiveness
    - Recommend optimal pairings
    """

    def __init__(self):
        """Initialize interaction analyzer"""
        self.interactions: Dict[Tuple[str, str], PlayerInteraction] = {}
        self.player_lineups: Dict[str, List[Set[str]]] = defaultdict(list)

        logger.info("InteractionAnalyzer initialized")

    def add_interaction(self, interaction: PlayerInteraction):
        """Add a player interaction"""
        # Store with sorted tuple to ensure consistency
        players = tuple(sorted([interaction.player1_id, interaction.player2_id]))
        self.interactions[players] = interaction

    def add_lineup_data(
        self,
        lineup: Set[str],
        game_id: str,
        possessions: int,
        points_for: int,
        points_against: int,
        minutes: float,
    ):
        """
        Add lineup performance data.

        This creates/updates interactions for all player pairs in lineup.

        Args:
            lineup: Set of player IDs
            game_id: Game identifier
            possessions: Number of possessions
            points_for: Points scored
            points_against: Points allowed
            minutes: Minutes played together
        """
        players = list(lineup)

        # Create/update interactions for all pairs
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                p1, p2 = players[i], players[j]
                players_key = tuple(sorted([p1, p2]))

                if players_key in self.interactions:
                    # Update existing
                    interaction = self.interactions[players_key]
                    interaction.possessions_together += possessions
                    interaction.minutes_together += minutes
                    interaction.points_for += points_for
                    interaction.points_against += points_against
                    interaction.plus_minus = (
                        interaction.points_for - interaction.points_against
                    )

                    # Recompute ratings
                    if interaction.possessions_together > 0:
                        interaction.offensive_rating = (
                            interaction.points_for / interaction.possessions_together
                        ) * 100
                        interaction.defensive_rating = (
                            interaction.points_against
                            / interaction.possessions_together
                        ) * 100
                        interaction.net_rating = (
                            interaction.offensive_rating - interaction.defensive_rating
                        )
                else:
                    # Create new
                    interaction = PlayerInteraction(
                        player1_id=p1,
                        player2_id=p2,
                        possessions_together=possessions,
                        minutes_together=minutes,
                        points_for=points_for,
                        points_against=points_against,
                        plus_minus=points_for - points_against,
                    )
                    self.interactions[players_key] = interaction

        # Store lineup
        for player in players:
            self.player_lineups[player].append(lineup)

    def get_interaction(
        self, player1_id: str, player2_id: str
    ) -> Optional[PlayerInteraction]:
        """Get interaction between two players"""
        players_key = tuple(sorted([player1_id, player2_id]))
        return self.interactions.get(players_key)

    def get_player_interactions(self, player_id: str) -> List[PlayerInteraction]:
        """Get all interactions involving a player"""
        return [
            interaction
            for players, interaction in self.interactions.items()
            if player_id in players
        ]

    def calculate_player_metrics(self, player_id: str) -> InteractionMetrics:
        """Calculate interaction metrics for a player"""
        interactions = self.get_player_interactions(player_id)

        if not interactions:
            return InteractionMetrics(player_id=player_id)

        # Find best/worst teammates
        best_interaction = max(interactions, key=lambda x: x.net_rating or 0)
        worst_interaction = min(interactions, key=lambda x: x.net_rating or 0)

        # Get the other player ID
        best_teammate = (
            best_interaction.player1_id
            if best_interaction.player1_id != player_id
            else best_interaction.player2_id
        )
        worst_teammate = (
            worst_interaction.player1_id
            if worst_interaction.player1_id != player_id
            else worst_interaction.player2_id
        )

        # Average net rating
        net_ratings = [x.net_rating for x in interactions if x.net_rating is not None]
        avg_net_rating = float(np.mean(net_ratings)) if net_ratings else 0.0

        # High/low synergy teammates (synergy > 0.7 or < 0.3)
        high_synergy = []
        low_synergy = []

        for interaction in interactions:
            other_player = (
                interaction.player1_id
                if interaction.player1_id != player_id
                else interaction.player2_id
            )

            synergy = interaction.synergy_score()
            if synergy >= 0.7:
                high_synergy.append(other_player)
            elif synergy <= 0.3:
                low_synergy.append(other_player)

        return InteractionMetrics(
            player_id=player_id,
            best_teammate_id=best_teammate,
            best_teammate_net_rating=best_interaction.net_rating or 0.0,
            worst_teammate_id=worst_teammate,
            worst_teammate_net_rating=worst_interaction.net_rating or 0.0,
            avg_net_rating_with_teammates=avg_net_rating,
            total_teammates=len(interactions),
            high_synergy_teammates=high_synergy,
            low_synergy_teammates=low_synergy,
        )

    def find_best_pairings(
        self, n: int = 10, metric: str = "net_rating"
    ) -> List[Tuple[str, str, float]]:
        """
        Find best player pairings.

        Args:
            n: Number of pairings to return
            metric: Metric to sort by ('net_rating', 'synergy', 'complement')

        Returns:
            List of (player1, player2, score) tuples
        """
        pairings = []

        for (p1, p2), interaction in self.interactions.items():
            if metric == "net_rating":
                score = interaction.net_rating or 0.0
            elif metric == "synergy":
                score = interaction.synergy_score()
            elif metric == "complement":
                score = interaction.complement_score()
            else:
                score = 0.0

            pairings.append((p1, p2, score))

        # Sort by score descending
        pairings.sort(key=lambda x: x[2], reverse=True)

        return pairings[:n]

    def find_worst_pairings(
        self, n: int = 10, metric: str = "net_rating"
    ) -> List[Tuple[str, str, float]]:
        """Find worst player pairings"""
        pairings = self.find_best_pairings(n=len(self.interactions), metric=metric)
        return pairings[-n:]

    def recommend_lineup_adjustments(
        self, current_lineup: Set[str], available_players: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Recommend lineup adjustments based on interaction data.

        Args:
            current_lineup: Current lineup (player IDs)
            available_players: Available substitute players

        Returns:
            List of recommended substitutions with reasoning
        """
        recommendations = []

        # Find players with low synergy in current lineup
        for player in current_lineup:
            # Get interactions with current teammates
            teammates = current_lineup - {player}
            teammate_interactions = [
                self.get_interaction(player, teammate) for teammate in teammates
            ]
            teammate_interactions = [x for x in teammate_interactions if x is not None]

            if teammate_interactions:
                avg_synergy = np.mean(
                    [x.synergy_score() for x in teammate_interactions]
                )

                # If low synergy, recommend substitution
                if avg_synergy < 0.4:
                    # Find best replacement from available players
                    best_replacement = None
                    best_replacement_synergy = 0.0

                    for candidate in available_players:
                        # Check synergy with remaining teammates
                        candidate_interactions = [
                            self.get_interaction(candidate, teammate)
                            for teammate in teammates
                        ]
                        candidate_interactions = [
                            x for x in candidate_interactions if x
                        ]

                        if candidate_interactions:
                            candidate_synergy = np.mean(
                                [x.synergy_score() for x in candidate_interactions]
                            )

                            if candidate_synergy > best_replacement_synergy:
                                best_replacement = candidate
                                best_replacement_synergy = candidate_synergy

                    if (
                        best_replacement
                        and best_replacement_synergy > avg_synergy + 0.1
                    ):
                        recommendations.append(
                            {
                                "replace": player,
                                "with": best_replacement,
                                "current_synergy": avg_synergy,
                                "projected_synergy": best_replacement_synergy,
                                "improvement": best_replacement_synergy - avg_synergy,
                            }
                        )

        # Sort by improvement
        recommendations.sort(key=lambda x: x["improvement"], reverse=True)

        return recommendations

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            "total_interactions": len(self.interactions),
            "unique_players": len(self.player_lineups),
            "avg_minutes_together": (
                float(np.mean([x.minutes_together for x in self.interactions.values()]))
                if self.interactions
                else 0.0
            ),
            "positive_pairings": sum(
                1
                for x in self.interactions.values()
                if x.net_rating and x.net_rating > 0
            ),
            "negative_pairings": sum(
                1
                for x in self.interactions.values()
                if x.net_rating and x.net_rating < 0
            ),
        }

    def clear(self):
        """Clear all stored data"""
        self.interactions.clear()
        self.player_lineups.clear()
        logger.info("Cleared all interaction data")
