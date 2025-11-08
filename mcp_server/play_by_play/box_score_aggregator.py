"""
NBA Box Score Aggregator

Converts play-by-play events into complete player and team box scores.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from .event_parser import EventParser, aggregate_player_stats
from .possession_tracker import PossessionTracker, calculate_true_possessions


@dataclass
class PlayerBoxScore:
    """Complete box score for a single player."""
    player_id: int
    team_id: int
    minutes: int  # Will need to be calculated from substitution events

    # Shooting
    fgm: int = 0
    fga: int = 0
    fg_pct: float = 0.0
    fg3m: int = 0
    fg3a: int = 0
    fg3_pct: float = 0.0
    ftm: int = 0
    fta: int = 0
    ft_pct: float = 0.0

    # Rebounds
    oreb: int = 0
    dreb: int = 0
    reb: int = 0

    # Other stats
    ast: int = 0
    stl: int = 0
    blk: int = 0
    tov: int = 0
    pf: int = 0
    pts: int = 0

    # Advanced metrics
    plus_minus: int = 0


@dataclass
class TeamBoxScore:
    """Complete box score for a team."""
    team_id: int

    # Shooting
    fgm: int = 0
    fga: int = 0
    fg_pct: float = 0.0
    fg3m: int = 0
    fg3a: int = 0
    fg3_pct: float = 0.0
    ftm: int = 0
    fta: int = 0
    ft_pct: float = 0.0

    # Rebounds
    oreb: int = 0
    dreb: int = 0
    reb: int = 0
    team_rebounds: int = 0  # Rebounds not attributed to players

    # Other stats
    ast: int = 0
    stl: int = 0
    blk: int = 0
    tov: int = 0
    team_turnovers: int = 0  # Turnovers not attributed to players
    total_turnovers: int = 0  # Player + team turnovers
    pf: int = 0
    pts: int = 0

    # Possession-based metrics
    possessions: int = 0
    true_possessions: int = 0  # From play-by-play
    estimated_possessions: float = 0.0  # From formula
    pace: float = 0.0  # Possessions per 48 minutes
    offensive_rating: float = 0.0  # Points per 100 possessions
    defensive_rating: float = 0.0  # Points allowed per 100 possessions


@dataclass
class GameBoxScore:
    """Complete box score for entire game."""
    game_id: str
    home_team_id: int
    away_team_id: int

    home_score: int
    away_score: int

    # Player box scores
    home_players: List[PlayerBoxScore]
    away_players: List[PlayerBoxScore]

    # Team box scores
    home_team: TeamBoxScore
    away_team: TeamBoxScore

    # Possession data
    total_possessions: int
    home_possessions: int
    away_possessions: int


class BoxScoreAggregator:
    """Aggregates play-by-play events into complete box scores."""

    def __init__(self):
        self.parser = EventParser()

    def generate_box_scores_from_pbp(
        self,
        game_id: str,
        events: List[Dict],
        home_team_id: int,
        away_team_id: int,
        player_team_mapping: Dict[int, int]  # Map player_id -> team_id
    ) -> GameBoxScore:
        """
        Generate complete box scores from play-by-play events.

        Args:
            game_id: Game identifier
            events: List of play-by-play event dictionaries
            home_team_id: Home team ID
            away_team_id: Away team ID
            player_team_mapping: Dictionary mapping player IDs to team IDs

        Returns:
            Complete GameBoxScore object
        """
        # Parse all events
        parsed_events = [self.parser.parse_event(event) for event in events]

        # Group into possessions
        tracker = PossessionTracker(home_team_id, away_team_id)
        possessions = tracker.group_events_into_possessions(events)

        # Calculate true possession counts
        possession_counts = calculate_true_possessions(possessions)
        home_possessions = possession_counts.get(home_team_id, 0)
        away_possessions = possession_counts.get(away_team_id, 0)

        # Aggregate player stats
        all_player_events = []
        for event in parsed_events:
            all_player_events.extend(event.player_stats)

        player_stats = aggregate_player_stats(all_player_events)

        # Split players by team
        home_players = []
        away_players = []

        for player_id, stats in player_stats.items():
            team_id = player_team_mapping.get(player_id)

            if not team_id:
                continue  # Skip players without team assignment

            player_box_score = PlayerBoxScore(
                player_id=player_id,
                team_id=team_id,
                minutes=0,  # TODO: Calculate from substitutions
                **stats
            )

            # Calculate percentages
            player_box_score.fg_pct = (
                stats['fgm'] / stats['fga'] if stats['fga'] > 0 else 0.0
            )
            player_box_score.fg3_pct = (
                stats['fg3m'] / stats['fg3a'] if stats['fg3a'] > 0 else 0.0
            )
            player_box_score.ft_pct = (
                stats['ftm'] / stats['fta'] if stats['fta'] > 0 else 0.0
            )

            if team_id == home_team_id:
                home_players.append(player_box_score)
            else:
                away_players.append(player_box_score)

        # Aggregate team stats
        home_team_stats = self._aggregate_team_stats(
            home_team_id,
            home_players,
            home_possessions
        )
        away_team_stats = self._aggregate_team_stats(
            away_team_id,
            away_players,
            away_possessions
        )

        # Add opponent defensive rating
        if home_possessions > 0:
            home_team_stats.defensive_rating = (away_team_stats.pts / home_possessions) * 100
        if away_possessions > 0:
            away_team_stats.defensive_rating = (home_team_stats.pts / away_possessions) * 100

        # Get final scores from last event
        final_event = parsed_events[-1] if parsed_events else None
        home_score = final_event.home_score if final_event else 0
        away_score = final_event.away_score if final_event else 0

        return GameBoxScore(
            game_id=game_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_score=home_score,
            away_score=away_score,
            home_players=home_players,
            away_players=away_players,
            home_team=home_team_stats,
            away_team=away_team_stats,
            total_possessions=home_possessions + away_possessions,
            home_possessions=home_possessions,
            away_possessions=away_possessions,
        )

    def _aggregate_team_stats(
        self,
        team_id: int,
        players: List[PlayerBoxScore],
        true_possessions: int
    ) -> TeamBoxScore:
        """Aggregate player stats into team totals."""
        team = TeamBoxScore(team_id=team_id, true_possessions=true_possessions)

        for player in players:
            team.fgm += player.fgm
            team.fga += player.fga
            team.fg3m += player.fg3m
            team.fg3a += player.fg3a
            team.ftm += player.ftm
            team.fta += player.fta
            team.oreb += player.oreb
            team.dreb += player.dreb
            team.reb += player.reb
            team.ast += player.ast
            team.stl += player.stl
            team.blk += player.blk
            team.tov += player.tov
            team.pf += player.pf
            team.pts += player.pts

        # Calculate team percentages
        team.fg_pct = team.fgm / team.fga if team.fga > 0 else 0.0
        team.fg3_pct = team.fg3m / team.fg3a if team.fg3a > 0 else 0.0
        team.ft_pct = team.ftm / team.fta if team.fta > 0 else 0.0

        # Calculate total turnovers (player + team)
        team.total_turnovers = team.tov + team.team_turnovers

        # Calculate estimated possessions using formula
        team.estimated_possessions = (
            team.fga + 0.44 * team.fta - team.oreb + team.total_turnovers
        )

        # Set possessions
        team.possessions = true_possessions

        # Calculate pace (possessions per 48 minutes)
        # Assuming 48-minute game (adjust for overtime if needed)
        team.pace = (true_possessions / 48.0) * 48 if true_possessions > 0 else 0.0

        # Calculate offensive rating (points per 100 possessions)
        if true_possessions > 0:
            team.offensive_rating = (team.pts / true_possessions) * 100
        else:
            team.offensive_rating = 0.0

        return team
