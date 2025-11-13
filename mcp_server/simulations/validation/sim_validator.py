"""
Simulation Validator (Agent 10, Module 1)

Validates simulation inputs and outputs to ensure data quality,
consistency, and plausibility for NBA game simulations.

Integrates with:
- Agent 2 (Monitoring): Track validation performance
- Agent 4 (Data Validation): Reuse validation patterns
- Agent 9 (Performance): Profile validation operations
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)

    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)


@dataclass
class PlayerStats:
    """Player statistics for validation"""

    player_id: str
    points: float
    assists: float
    rebounds: float
    steals: float
    blocks: float
    turnovers: float
    minutes: float
    field_goal_pct: Optional[float] = None
    three_point_pct: Optional[float] = None
    free_throw_pct: Optional[float] = None


@dataclass
class TeamRoster:
    """Team roster for validation"""

    team_id: str
    team_name: str
    players: List[PlayerStats]
    season: str

    def get_total_players(self) -> int:
        """Get total number of players"""
        return len(self.players)

    def get_player_by_id(self, player_id: str) -> Optional[PlayerStats]:
        """Get player by ID"""
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None


@dataclass
class GameParameters:
    """Game simulation parameters"""

    home_team_id: str
    away_team_id: str
    season: str
    game_date: datetime
    is_playoff: bool = False
    overtime_periods: int = 0

    def validate_basic(self) -> ValidationResult:
        """Validate basic game parameters"""
        result = ValidationResult(is_valid=True)

        if not self.home_team_id:
            result.add_error("Home team ID is required")

        if not self.away_team_id:
            result.add_error("Away team ID is required")

        if self.home_team_id == self.away_team_id:
            result.add_error("Home and away teams must be different")

        if self.overtime_periods < 0:
            result.add_error("Overtime periods cannot be negative")

        if self.overtime_periods > 10:
            result.add_warning(
                f"Unusual number of overtime periods: {self.overtime_periods}"
            )

        return result


@dataclass
class BoxScore:
    """Game box score for validation"""

    home_score: int
    away_score: int
    home_stats: Dict[str, PlayerStats]
    away_stats: Dict[str, PlayerStats]
    quarters: List[Tuple[int, int]]  # (home_score, away_score) per quarter

    def get_total_home_score(self) -> int:
        """Calculate total home score from quarters"""
        return sum(q[0] for q in self.quarters)

    def get_total_away_score(self) -> int:
        """Calculate total away score from quarters"""
        return sum(q[1] for q in self.quarters)


class SimulationValidator:
    """
    Validates simulation inputs and outputs for NBA game simulations.

    Features:
    - Input validation (rosters, parameters)
    - Output validation (box scores, statistics)
    - Statistical property checks
    - Consistency validation
    """

    # Validation thresholds
    MIN_PLAYERS_PER_TEAM = 5
    MAX_PLAYERS_PER_TEAM = 15
    MIN_MINUTES_PER_PLAYER = 0.0
    MAX_MINUTES_PER_PLAYER = 60.0  # Including overtime
    MAX_POINTS_PER_PLAYER = 100
    MAX_ASSISTS_PER_PLAYER = 30
    MAX_REBOUNDS_PER_PLAYER = 40
    MAX_STEALS_PER_PLAYER = 15
    MAX_BLOCKS_PER_PLAYER = 20
    MAX_TURNOVERS_PER_PLAYER = 20
    MIN_TEAM_SCORE = 0
    MAX_TEAM_SCORE = 200
    NORMAL_QUARTERS = 4
    MAX_OVERTIME_PERIODS = 10

    def __init__(self, strict_mode: bool = False):
        """
        Initialize simulator validator.

        Args:
            strict_mode: If True, warnings become errors
        """
        self.strict_mode = strict_mode
        self.validation_count = 0
        self.error_count = 0
        self.warning_count = 0

    def validate_roster(self, roster: TeamRoster) -> ValidationResult:
        """
        Validate team roster.

        Args:
            roster: Team roster to validate

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(is_valid=True)

        # Check roster size
        num_players = roster.get_total_players()
        if num_players < self.MIN_PLAYERS_PER_TEAM:
            result.add_error(
                f"Team {roster.team_id} has too few players: {num_players}"
            )
        elif num_players > self.MAX_PLAYERS_PER_TEAM:
            result.add_warning(f"Team {roster.team_id} has many players: {num_players}")

        # Validate each player
        player_ids = set()
        for player in roster.players:
            # Check for duplicate IDs
            if player.player_id in player_ids:
                result.add_error(f"Duplicate player ID: {player.player_id}")
            player_ids.add(player.player_id)

            # Validate player stats
            player_result = self._validate_player_stats(player)
            result.errors.extend(player_result.errors)
            result.warnings.extend(player_result.warnings)
            if not player_result.is_valid:
                result.is_valid = False

        self.validation_count += 1
        if result.errors:
            self.error_count += 1
        if result.warnings:
            self.warning_count += 1

        return result

    def _validate_player_stats(self, player: PlayerStats) -> ValidationResult:
        """
        Validate individual player statistics.

        Args:
            player: Player stats to validate

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        # Validate stat ranges
        if player.points < 0:
            result.add_error(f"Player {player.player_id}: negative points")
        elif player.points > self.MAX_POINTS_PER_PLAYER:
            result.add_warning(
                f"Player {player.player_id}: unusually high points: {player.points}"
            )

        if player.assists < 0:
            result.add_error(f"Player {player.player_id}: negative assists")
        elif player.assists > self.MAX_ASSISTS_PER_PLAYER:
            result.add_warning(
                f"Player {player.player_id}: unusually high assists: {player.assists}"
            )

        if player.rebounds < 0:
            result.add_error(f"Player {player.player_id}: negative rebounds")
        elif player.rebounds > self.MAX_REBOUNDS_PER_PLAYER:
            result.add_warning(
                f"Player {player.player_id}: unusually high rebounds: {player.rebounds}"
            )

        if player.steals < 0:
            result.add_error(f"Player {player.player_id}: negative steals")
        elif player.steals > self.MAX_STEALS_PER_PLAYER:
            result.add_warning(
                f"Player {player.player_id}: unusually high steals: {player.steals}"
            )

        if player.blocks < 0:
            result.add_error(f"Player {player.player_id}: negative blocks")
        elif player.blocks > self.MAX_BLOCKS_PER_PLAYER:
            result.add_warning(
                f"Player {player.player_id}: unusually high blocks: {player.blocks}"
            )

        if player.turnovers < 0:
            result.add_error(f"Player {player.player_id}: negative turnovers")
        elif player.turnovers > self.MAX_TURNOVERS_PER_PLAYER:
            result.add_warning(
                f"Player {player.player_id}: unusually high turnovers: {player.turnovers}"
            )

        if player.minutes < self.MIN_MINUTES_PER_PLAYER:
            result.add_error(f"Player {player.player_id}: negative minutes")
        elif player.minutes > self.MAX_MINUTES_PER_PLAYER:
            result.add_warning(
                f"Player {player.player_id}: minutes exceed game length: {player.minutes}"
            )

        # Validate percentages
        if player.field_goal_pct is not None:
            if not (0.0 <= player.field_goal_pct <= 1.0):
                result.add_error(
                    f"Player {player.player_id}: invalid FG%: {player.field_goal_pct}"
                )

        if player.three_point_pct is not None:
            if not (0.0 <= player.three_point_pct <= 1.0):
                result.add_error(
                    f"Player {player.player_id}: invalid 3P%: {player.three_point_pct}"
                )

        if player.free_throw_pct is not None:
            if not (0.0 <= player.free_throw_pct <= 1.0):
                result.add_error(
                    f"Player {player.player_id}: invalid FT%: {player.free_throw_pct}"
                )

        return result

    def validate_game_parameters(self, params: GameParameters) -> ValidationResult:
        """
        Validate game simulation parameters.

        Args:
            params: Game parameters to validate

        Returns:
            ValidationResult
        """
        result = params.validate_basic()

        # Additional validations
        if params.game_date > datetime.now():
            result.add_warning("Game date is in the future")

        self.validation_count += 1
        if result.errors:
            self.error_count += 1
        if result.warnings:
            self.warning_count += 1

        return result

    def validate_box_score(self, box_score: BoxScore) -> ValidationResult:
        """
        Validate game box score output.

        Args:
            box_score: Box score to validate

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        # Validate scores
        if box_score.home_score < self.MIN_TEAM_SCORE:
            result.add_error(f"Invalid home score: {box_score.home_score}")
        elif box_score.home_score > self.MAX_TEAM_SCORE:
            result.add_warning(f"Unusually high home score: {box_score.home_score}")

        if box_score.away_score < self.MIN_TEAM_SCORE:
            result.add_error(f"Invalid away score: {box_score.away_score}")
        elif box_score.away_score > self.MAX_TEAM_SCORE:
            result.add_warning(f"Unusually high away score: {box_score.away_score}")

        # Validate quarter consistency
        total_home = box_score.get_total_home_score()
        total_away = box_score.get_total_away_score()

        if total_home != box_score.home_score:
            result.add_error(
                f"Home score mismatch: {box_score.home_score} != {total_home} (sum of quarters)"
            )

        if total_away != box_score.away_score:
            result.add_error(
                f"Away score mismatch: {box_score.away_score} != {total_away} (sum of quarters)"
            )

        # Validate number of quarters
        num_quarters = len(box_score.quarters)
        if num_quarters < self.NORMAL_QUARTERS:
            result.add_error(f"Too few quarters: {num_quarters}")
        elif num_quarters > self.NORMAL_QUARTERS + self.MAX_OVERTIME_PERIODS:
            result.add_warning(f"Unusual number of quarters: {num_quarters}")

        # Validate player stats sum to team stats
        self._validate_team_totals(box_score, result)

        self.validation_count += 1
        if result.errors:
            self.error_count += 1
        if result.warnings:
            self.warning_count += 1

        return result

    def _validate_team_totals(self, box_score: BoxScore, result: ValidationResult):
        """
        Validate that individual player stats sum correctly to team totals.

        Args:
            box_score: Box score to validate
            result: ValidationResult to update
        """
        # Sum home team stats
        home_total_points = sum(p.points for p in box_score.home_stats.values())

        # Allow small discrepancy for rounding
        if abs(home_total_points - box_score.home_score) > 1:
            result.add_warning(
                f"Home player points ({home_total_points}) don't match team score ({box_score.home_score})"
            )

        # Sum away team stats
        away_total_points = sum(p.points for p in box_score.away_stats.values())

        if abs(away_total_points - box_score.away_score) > 1:
            result.add_warning(
                f"Away player points ({away_total_points}) don't match team score ({box_score.away_score})"
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics.

        Returns:
            Dict with validation stats
        """
        return {
            "total_validations": self.validation_count,
            "total_errors": self.error_count,
            "total_warnings": self.warning_count,
            "error_rate": (
                self.error_count / self.validation_count
                if self.validation_count > 0
                else 0
            ),
            "warning_rate": (
                self.warning_count / self.validation_count
                if self.validation_count > 0
                else 0
            ),
            "strict_mode": self.strict_mode,
        }

    def reset_statistics(self):
        """Reset validation counters"""
        self.validation_count = 0
        self.error_count = 0
        self.warning_count = 0
