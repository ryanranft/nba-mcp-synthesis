"""
Team Chemistry and Lineup Analysis (Agent 16, Module 3)

Analyzes overall team chemistry and lineup effectiveness:
- Five-man lineup performance
- Lineup optimization
- Rotation pattern analysis
- Team cohesion metrics
- Stagger analysis (which players play together)

Integrates with:
- player_interaction: Two-player chemistry
- passing_network: Team passing patterns
- simulations: Lineup performance prediction
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict
from itertools import combinations

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LineupPerformance:
    """Performance metrics for a specific 5-player lineup"""

    lineup: Tuple[str, ...]  # Sorted tuple of 5 player IDs

    # Usage metrics
    possessions: int
    minutes: float
    games_played: int = 1

    # Performance metrics
    points_for: int
    points_against: int
    plus_minus: float

    # Advanced metrics
    offensive_rating: float = 0.0  # Points per 100 possessions
    defensive_rating: float = 0.0  # Points allowed per 100
    net_rating: float = 0.0  # Off - Def rating

    # Win/loss record (if available)
    wins: int = 0
    losses: int = 0

    def __post_init__(self):
        """Compute advanced metrics"""
        if self.possessions > 0:
            self.offensive_rating = (self.points_for / self.possessions) * 100
            self.defensive_rating = (self.points_against / self.possessions) * 100
            self.net_rating = self.offensive_rating - self.defensive_rating

        self.plus_minus = float(self.points_for - self.points_against)

    def win_percentage(self) -> float:
        """Calculate win percentage"""
        total_games = self.wins + self.losses
        return self.wins / total_games if total_games > 0 else 0.0

    def per_minute_stats(self) -> Dict[str, float]:
        """Get per-minute statistics"""
        if self.minutes == 0:
            return {}

        return {
            'points_per_minute': self.points_for / self.minutes,
            'points_allowed_per_minute': self.points_against / self.minutes,
            'plus_minus_per_minute': self.plus_minus / self.minutes
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'lineup': list(self.lineup),
            'possessions': self.possessions,
            'minutes': self.minutes,
            'games': self.games_played,
            'plus_minus': self.plus_minus,
            'offensive_rating': self.offensive_rating,
            'defensive_rating': self.defensive_rating,
            'net_rating': self.net_rating,
            'wins': self.wins,
            'losses': self.losses,
            'win_pct': self.win_percentage(),
        }


@dataclass
class ChemistryMetrics:
    """Overall team chemistry metrics"""

    team_id: str

    # Lineup diversity
    total_lineups_used: int
    avg_lineup_minutes: float
    most_used_lineup_minutes: float

    # Performance consistency
    avg_lineup_net_rating: float
    std_lineup_net_rating: float  # Lower = more consistent
    best_lineup_net_rating: float
    worst_lineup_net_rating: float

    # Chemistry indicators
    positive_lineup_pct: float  # % of lineups with positive net rating
    cohesion_score: float = 0.0  # 0-1, higher = better chemistry

    # Rotation metrics
    avg_players_per_rotation: float = 0.0
    rotation_stability: float = 0.0  # 0-1, higher = more stable

    def __post_init__(self):
        """Compute cohesion score"""
        # Cohesion based on consistency and positive performance
        consistency_component = max(0, 1.0 - (self.std_lineup_net_rating / 20.0))
        performance_component = min(max((self.avg_lineup_net_rating + 10) / 20, 0), 1)
        positive_lineup_component = self.positive_lineup_pct

        self.cohesion_score = (
            consistency_component * 0.3 +
            performance_component * 0.4 +
            positive_lineup_component * 0.3
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'team_id': self.team_id,
            'total_lineups': self.total_lineups_used,
            'avg_net_rating': self.avg_lineup_net_rating,
            'std_net_rating': self.std_lineup_net_rating,
            'best_net_rating': self.best_lineup_net_rating,
            'positive_lineup_pct': self.positive_lineup_pct,
            'cohesion_score': self.cohesion_score,
            'rotation_stability': self.rotation_stability,
        }


class ChemistryAnalyzer:
    """
    Analyze team chemistry and lineup effectiveness.

    Features:
    - Track all lineup combinations
    - Identify optimal lineups
    - Analyze rotation patterns
    - Measure team cohesion
    - Recommend lineup changes
    - Stagger analysis (which players should/shouldn't play together)
    """

    def __init__(self):
        """Initialize chemistry analyzer"""
        self.lineups: Dict[Tuple[str, ...], LineupPerformance] = {}
        self.lineups_by_team: Dict[str, Dict[Tuple[str, ...], LineupPerformance]] = defaultdict(dict)
        self.player_lineups: Dict[str, List[Tuple[str, ...]]] = defaultdict(list)

        logger.info("ChemistryAnalyzer initialized")

    def add_lineup_performance(
        self,
        players: Set[str],
        team_id: str,
        possessions: int,
        points_for: int,
        points_against: int,
        minutes: float,
        won_game: Optional[bool] = None
    ):
        """
        Add or update lineup performance data.

        Args:
            players: Set of 5 player IDs
            team_id: Team identifier
            possessions: Number of possessions
            points_for: Points scored
            points_against: Points allowed
            minutes: Minutes played
            won_game: Whether the game was won (optional)
        """
        if len(players) != 5:
            logger.warning(f"Lineup must have exactly 5 players, got {len(players)}")
            return

        # Create sorted tuple for consistent keys
        lineup_key = tuple(sorted(players))

        if lineup_key in self.lineups:
            # Update existing
            lineup = self.lineups[lineup_key]
            lineup.possessions += possessions
            lineup.minutes += minutes
            lineup.points_for += points_for
            lineup.points_against += points_against
            lineup.games_played += 1

            if won_game is not None:
                if won_game:
                    lineup.wins += 1
                else:
                    lineup.losses += 1

            # Recompute metrics
            lineup.__post_init__()
        else:
            # Create new
            lineup = LineupPerformance(
                lineup=lineup_key,
                possessions=possessions,
                minutes=minutes,
                points_for=points_for,
                points_against=points_against,
                plus_minus=float(points_for - points_against),
                wins=1 if won_game else 0,
                losses=0 if won_game or won_game is None else 1
            )
            self.lineups[lineup_key] = lineup
            self.lineups_by_team[team_id][lineup_key] = lineup

            # Index by player
            for player in players:
                self.player_lineups[player].append(lineup_key)

    def get_lineup_performance(
        self,
        players: Set[str]
    ) -> Optional[LineupPerformance]:
        """Get performance for a specific lineup"""
        lineup_key = tuple(sorted(players))
        return self.lineups.get(lineup_key)

    def get_best_lineups(
        self,
        team_id: Optional[str] = None,
        n: int = 10,
        min_minutes: float = 5.0,
        metric: str = 'net_rating'
    ) -> List[LineupPerformance]:
        """
        Get best performing lineups.

        Args:
            team_id: Filter to specific team
            n: Number of lineups to return
            min_minutes: Minimum minutes threshold
            metric: Metric to sort by ('net_rating', 'plus_minus', 'win_pct')

        Returns:
            List of LineupPerformance objects
        """
        # Filter lineups
        if team_id:
            lineups = list(self.lineups_by_team.get(team_id, {}).values())
        else:
            lineups = list(self.lineups.values())

        # Filter by minutes
        lineups = [l for l in lineups if l.minutes >= min_minutes]

        # Sort by metric
        if metric == 'net_rating':
            lineups.sort(key=lambda x: x.net_rating, reverse=True)
        elif metric == 'plus_minus':
            lineups.sort(key=lambda x: x.plus_minus, reverse=True)
        elif metric == 'win_pct':
            lineups.sort(key=lambda x: x.win_percentage(), reverse=True)
        else:
            lineups.sort(key=lambda x: x.net_rating, reverse=True)

        return lineups[:n]

    def get_worst_lineups(
        self,
        team_id: Optional[str] = None,
        n: int = 10,
        min_minutes: float = 5.0,
        metric: str = 'net_rating'
    ) -> List[LineupPerformance]:
        """Get worst performing lineups"""
        lineups = self.get_best_lineups(team_id, n=len(self.lineups), min_minutes=min_minutes, metric=metric)
        return lineups[-n:]

    def calculate_team_chemistry(
        self,
        team_id: str
    ) -> ChemistryMetrics:
        """
        Calculate overall team chemistry metrics.

        Args:
            team_id: Team identifier

        Returns:
            ChemistryMetrics object
        """
        lineups = list(self.lineups_by_team.get(team_id, {}).values())

        if not lineups:
            return ChemistryMetrics(
                team_id=team_id,
                total_lineups_used=0,
                avg_lineup_minutes=0.0,
                most_used_lineup_minutes=0.0,
                avg_lineup_net_rating=0.0,
                std_lineup_net_rating=0.0,
                best_lineup_net_rating=0.0,
                worst_lineup_net_rating=0.0,
                positive_lineup_pct=0.0
            )

        # Lineup diversity
        total_lineups = len(lineups)
        minutes_list = [l.minutes for l in lineups]
        avg_minutes = float(np.mean(minutes_list))
        most_used_minutes = float(np.max(minutes_list))

        # Performance metrics
        net_ratings = [l.net_rating for l in lineups]
        avg_net_rating = float(np.mean(net_ratings))
        std_net_rating = float(np.std(net_ratings))
        best_net_rating = float(np.max(net_ratings))
        worst_net_rating = float(np.min(net_ratings))

        # Positive lineup percentage
        positive_lineups = sum(1 for l in lineups if l.net_rating > 0)
        positive_pct = positive_lineups / total_lineups

        # Rotation stability (inverse of lineup diversity)
        # More stable = fewer lineups, more minutes on best lineups
        lineup_concentration = most_used_minutes / sum(minutes_list) if sum(minutes_list) > 0 else 0
        rotation_stability = min(lineup_concentration * 2, 1.0)  # Normalize

        return ChemistryMetrics(
            team_id=team_id,
            total_lineups_used=total_lineups,
            avg_lineup_minutes=avg_minutes,
            most_used_lineup_minutes=most_used_minutes,
            avg_lineup_net_rating=avg_net_rating,
            std_lineup_net_rating=std_net_rating,
            best_lineup_net_rating=best_net_rating,
            worst_lineup_net_rating=worst_net_rating,
            positive_lineup_pct=positive_pct,
            rotation_stability=rotation_stability
        )

    def analyze_player_lineup_impact(
        self,
        player_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a player's impact across different lineups.

        Args:
            player_id: Player identifier

        Returns:
            Dictionary with impact analysis
        """
        player_lineup_keys = self.player_lineups.get(player_id, [])

        if not player_lineup_keys:
            return {'lineups_played': 0}

        lineups = [self.lineups[key] for key in player_lineup_keys]

        # Performance in lineups
        net_ratings = [l.net_rating for l in lineups]
        avg_net_rating = float(np.mean(net_ratings))

        # Best/worst lineups
        best_lineup = max(lineups, key=lambda x: x.net_rating)
        worst_lineup = min(lineups, key=lambda x: x.net_rating)

        # Minutes distribution
        total_minutes = sum(l.minutes for l in lineups)

        return {
            'player_id': player_id,
            'lineups_played': len(lineups),
            'total_minutes': total_minutes,
            'avg_net_rating': avg_net_rating,
            'best_lineup': {
                'players': list(best_lineup.lineup),
                'net_rating': best_lineup.net_rating,
                'minutes': best_lineup.minutes
            },
            'worst_lineup': {
                'players': list(worst_lineup.lineup),
                'net_rating': worst_lineup.net_rating,
                'minutes': worst_lineup.minutes
            }
        }

    def find_optimal_lineup(
        self,
        available_players: Set[str],
        team_id: str,
        strategy: str = 'best_known'
    ) -> Dict[str, Any]:
        """
        Find optimal 5-player lineup from available players.

        Args:
            available_players: Set of available player IDs
            team_id: Team identifier
            strategy: Strategy ('best_known', 'highest_average', 'balanced')

        Returns:
            Dictionary with recommended lineup and reasoning
        """
        if len(available_players) < 5:
            return {'error': 'Need at least 5 available players'}

        if strategy == 'best_known':
            # Find best known 5-man combination
            best_lineup = None
            best_net_rating = -float('inf')

            # Check all possible 5-player combinations
            for combo in combinations(available_players, 5):
                lineup_key = tuple(sorted(combo))
                if lineup_key in self.lineups:
                    lineup = self.lineups[lineup_key]
                    if lineup.net_rating > best_net_rating and lineup.minutes >= 5.0:
                        best_net_rating = lineup.net_rating
                        best_lineup = lineup

            if best_lineup:
                return {
                    'lineup': list(best_lineup.lineup),
                    'net_rating': best_lineup.net_rating,
                    'minutes_together': best_lineup.minutes,
                    'strategy': strategy
                }

        elif strategy == 'highest_average':
            # Find combination with highest average pair-wise net rating
            # This would require player_interaction data
            pass

        # Default: return most experienced lineup
        all_lineups = list(self.lineups_by_team.get(team_id, {}).values())
        valid_lineups = [
            l for l in all_lineups
            if set(l.lineup).issubset(available_players)
        ]

        if valid_lineups:
            # Return lineup with most minutes
            best_lineup = max(valid_lineups, key=lambda x: x.minutes)
            return {
                'lineup': list(best_lineup.lineup),
                'net_rating': best_lineup.net_rating,
                'minutes_together': best_lineup.minutes,
                'strategy': 'most_experienced'
            }

        return {'error': 'No suitable lineup found'}

    def analyze_stagger_patterns(
        self,
        player1_id: str,
        player2_id: str
    ) -> Dict[str, Any]:
        """
        Analyze whether two players should be staggered (not play together).

        Args:
            player1_id: First player ID
            player2_id: Second player ID

        Returns:
            Dictionary with stagger analysis
        """
        # Find lineups with both players
        p1_lineups = set(self.player_lineups.get(player1_id, []))
        p2_lineups = set(self.player_lineups.get(player2_id, []))

        together_lineups = p1_lineups & p2_lineups
        p1_alone_lineups = p1_lineups - together_lineups
        p2_alone_lineups = p2_lineups - together_lineups

        if not together_lineups:
            return {
                'recommendation': 'no_data',
                'lineups_together': 0
            }

        # Performance together
        together_perf = [self.lineups[key] for key in together_lineups]
        together_net_rating = np.mean([l.net_rating for l in together_perf])
        together_minutes = sum(l.minutes for l in together_perf)

        # Performance apart
        p1_alone_perf = [self.lineups[key] for key in p1_alone_lineups] if p1_alone_lineups else []
        p2_alone_perf = [self.lineups[key] for key in p2_alone_lineups] if p2_alone_lineups else []

        p1_alone_net_rating = np.mean([l.net_rating for l in p1_alone_perf]) if p1_alone_perf else 0
        p2_alone_net_rating = np.mean([l.net_rating for l in p2_alone_perf]) if p2_alone_perf else 0

        # Recommendation
        avg_alone = (p1_alone_net_rating + p2_alone_net_rating) / 2

        if together_net_rating > avg_alone + 2:
            recommendation = 'play_together'
            reason = f"Better together (+{together_net_rating - avg_alone:.1f} net rating)"
        elif together_net_rating < avg_alone - 2:
            recommendation = 'stagger'
            reason = f"Better apart ({avg_alone - together_net_rating:.1f} net rating difference)"
        else:
            recommendation = 'neutral'
            reason = "Similar performance together and apart"

        return {
            'player1': player1_id,
            'player2': player2_id,
            'recommendation': recommendation,
            'reason': reason,
            'together_net_rating': float(together_net_rating),
            'apart_net_rating': float(avg_alone),
            'lineups_together': len(together_lineups),
            'minutes_together': together_minutes
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            'total_lineups': len(self.lineups),
            'unique_teams': len(self.lineups_by_team),
            'unique_players': len(self.player_lineups),
            'total_minutes_tracked': sum(l.minutes for l in self.lineups.values()),
            'avg_lineup_net_rating': float(np.mean([
                l.net_rating for l in self.lineups.values()
            ])) if self.lineups else 0.0
        }

    def clear(self):
        """Clear all stored data"""
        self.lineups.clear()
        self.lineups_by_team.clear()
        self.player_lineups.clear()
        logger.info("Cleared all chemistry data")
