"""
Unit Tests for Simulation Validator (Agent 10, Module 1)

Tests validation of simulation inputs and outputs.
"""

import pytest
from datetime import datetime, timedelta
from mcp_server.simulations.validation.sim_validator import (
    SimulationValidator,
    ValidationResult,
    PlayerStats,
    TeamRoster,
    GameParameters,
    BoxScore
)


class TestValidationResult:
    """Test ValidationResult dataclass"""

    def test_validation_result_init(self):
        """Test ValidationResult initialization"""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert isinstance(result.validated_at, datetime)

    def test_add_error(self):
        """Test adding errors invalidates result"""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error")
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_add_warning(self):
        """Test adding warnings doesn't invalidate result"""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"

    def test_multiple_errors_and_warnings(self):
        """Test multiple errors and warnings"""
        result = ValidationResult(is_valid=True)
        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_warning("Warning 1")
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


class TestPlayerStats:
    """Test PlayerStats dataclass"""

    def test_player_stats_creation(self):
        """Test creating player stats"""
        player = PlayerStats(
            player_id="player_1",
            points=25.5,
            assists=8.0,
            rebounds=10.0,
            steals=2.0,
            blocks=1.0,
            turnovers=3.0,
            minutes=35.0
        )
        assert player.player_id == "player_1"
        assert player.points == 25.5
        assert player.assists == 8.0

    def test_player_stats_with_percentages(self):
        """Test player stats with shooting percentages"""
        player = PlayerStats(
            player_id="player_1",
            points=20.0,
            assists=5.0,
            rebounds=8.0,
            steals=1.0,
            blocks=1.0,
            turnovers=2.0,
            minutes=30.0,
            field_goal_pct=0.52,
            three_point_pct=0.38,
            free_throw_pct=0.85
        )
        assert player.field_goal_pct == 0.52
        assert player.three_point_pct == 0.38
        assert player.free_throw_pct == 0.85


class TestTeamRoster:
    """Test TeamRoster functionality"""

    def test_roster_creation(self):
        """Test creating team roster"""
        players = [
            PlayerStats("p1", 20.0, 5.0, 8.0, 1.0, 1.0, 2.0, 30.0),
            PlayerStats("p2", 15.0, 3.0, 6.0, 2.0, 0.0, 1.0, 25.0)
        ]
        roster = TeamRoster(
            team_id="team_1",
            team_name="Test Team",
            players=players,
            season="2023-24"
        )
        assert roster.team_id == "team_1"
        assert roster.get_total_players() == 2

    def test_get_player_by_id(self):
        """Test retrieving player by ID"""
        players = [
            PlayerStats("p1", 20.0, 5.0, 8.0, 1.0, 1.0, 2.0, 30.0),
            PlayerStats("p2", 15.0, 3.0, 6.0, 2.0, 0.0, 1.0, 25.0)
        ]
        roster = TeamRoster("team_1", "Test Team", players, "2023-24")

        player = roster.get_player_by_id("p1")
        assert player is not None
        assert player.player_id == "p1"
        assert player.points == 20.0

    def test_get_player_by_id_not_found(self):
        """Test retrieving non-existent player"""
        roster = TeamRoster("team_1", "Test Team", [], "2023-24")
        player = roster.get_player_by_id("nonexistent")
        assert player is None


class TestGameParameters:
    """Test GameParameters functionality"""

    def test_game_parameters_creation(self):
        """Test creating game parameters"""
        params = GameParameters(
            home_team_id="team_1",
            away_team_id="team_2",
            season="2023-24",
            game_date=datetime.now()
        )
        assert params.home_team_id == "team_1"
        assert params.away_team_id == "team_2"
        assert params.is_playoff is False
        assert params.overtime_periods == 0

    def test_validate_basic_valid(self):
        """Test validating valid game parameters"""
        params = GameParameters(
            home_team_id="team_1",
            away_team_id="team_2",
            season="2023-24",
            game_date=datetime.now()
        )
        result = params.validate_basic()
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_basic_same_teams(self):
        """Test validation fails for same home/away team"""
        params = GameParameters(
            home_team_id="team_1",
            away_team_id="team_1",
            season="2023-24",
            game_date=datetime.now()
        )
        result = params.validate_basic()
        assert result.is_valid is False
        assert any("must be different" in e for e in result.errors)

    def test_validate_basic_negative_overtime(self):
        """Test validation fails for negative overtime"""
        params = GameParameters(
            home_team_id="team_1",
            away_team_id="team_2",
            season="2023-24",
            game_date=datetime.now(),
            overtime_periods=-1
        )
        result = params.validate_basic()
        assert result.is_valid is False
        assert any("cannot be negative" in e for e in result.errors)

    def test_validate_basic_many_overtimes_warning(self):
        """Test warning for unusual overtime periods"""
        params = GameParameters(
            home_team_id="team_1",
            away_team_id="team_2",
            season="2023-24",
            game_date=datetime.now(),
            overtime_periods=15
        )
        result = params.validate_basic()
        assert len(result.warnings) > 0
        assert any("Unusual number" in w for w in result.warnings)


class TestSimulationValidator:
    """Test SimulationValidator class"""

    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return SimulationValidator()

    @pytest.fixture
    def valid_player(self):
        """Create valid player stats"""
        return PlayerStats(
            player_id="player_1",
            points=25.0,
            assists=8.0,
            rebounds=10.0,
            steals=2.0,
            blocks=1.0,
            turnovers=3.0,
            minutes=35.0,
            field_goal_pct=0.52,
            three_point_pct=0.38,
            free_throw_pct=0.85
        )

    @pytest.fixture
    def valid_roster(self, valid_player):
        """Create valid team roster"""
        players = [valid_player]
        for i in range(2, 13):  # 12 players total
            players.append(PlayerStats(
                player_id=f"player_{i}",
                points=10.0,
                assists=3.0,
                rebounds=5.0,
                steals=1.0,
                blocks=0.5,
                turnovers=2.0,
                minutes=20.0
            ))
        return TeamRoster("team_1", "Test Team", players, "2023-24")

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly"""
        assert validator.strict_mode is False
        assert validator.validation_count == 0
        assert validator.error_count == 0
        assert validator.warning_count == 0

    def test_validate_player_stats_valid(self, validator, valid_player):
        """Test validating valid player stats"""
        result = validator._validate_player_stats(valid_player)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_player_stats_negative_points(self, validator):
        """Test validation fails for negative points"""
        player = PlayerStats("p1", -10.0, 5.0, 8.0, 1.0, 1.0, 2.0, 30.0)
        result = validator._validate_player_stats(player)
        assert result.is_valid is False
        assert any("negative points" in e for e in result.errors)

    def test_validate_player_stats_excessive_points(self, validator):
        """Test warning for excessive points"""
        player = PlayerStats("p1", 150.0, 5.0, 8.0, 1.0, 1.0, 2.0, 30.0)
        result = validator._validate_player_stats(player)
        assert len(result.warnings) > 0
        assert any("unusually high points" in w for w in result.warnings)

    def test_validate_player_stats_invalid_fg_pct(self, validator):
        """Test validation fails for invalid FG%"""
        player = PlayerStats(
            "p1", 20.0, 5.0, 8.0, 1.0, 1.0, 2.0, 30.0,
            field_goal_pct=1.5  # Invalid > 1.0
        )
        result = validator._validate_player_stats(player)
        assert result.is_valid is False
        assert any("invalid FG%" in e for e in result.errors)

    def test_validate_roster_valid(self, validator, valid_roster):
        """Test validating valid roster"""
        result = validator.validate_roster(valid_roster)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_roster_too_few_players(self, validator):
        """Test validation fails for too few players"""
        roster = TeamRoster(
            "team_1", "Test Team",
            [PlayerStats("p1", 20.0, 5.0, 8.0, 1.0, 1.0, 2.0, 30.0)],
            "2023-24"
        )
        result = validator.validate_roster(roster)
        assert result.is_valid is False
        assert any("too few players" in e for e in result.errors)

    def test_validate_roster_duplicate_players(self, validator):
        """Test validation fails for duplicate player IDs"""
        players = [
            PlayerStats("p1", 20.0, 5.0, 8.0, 1.0, 1.0, 2.0, 30.0),
            PlayerStats("p1", 15.0, 3.0, 6.0, 2.0, 0.0, 1.0, 25.0),  # Duplicate ID
            PlayerStats("p2", 10.0, 2.0, 5.0, 1.0, 0.0, 2.0, 20.0),
            PlayerStats("p3", 12.0, 4.0, 7.0, 1.0, 1.0, 1.0, 22.0),
            PlayerStats("p4", 18.0, 6.0, 6.0, 2.0, 0.0, 3.0, 28.0),
            PlayerStats("p5", 14.0, 3.0, 5.0, 1.0, 1.0, 2.0, 24.0)
        ]
        roster = TeamRoster("team_1", "Test Team", players, "2023-24")
        result = validator.validate_roster(roster)
        assert result.is_valid is False
        assert any("Duplicate player ID" in e for e in result.errors)

    def test_validate_game_parameters_valid(self, validator):
        """Test validating valid game parameters"""
        params = GameParameters(
            "team_1", "team_2", "2023-24",
            datetime.now() - timedelta(days=1)
        )
        result = validator.validate_game_parameters(params)
        assert result.is_valid is True

    def test_validate_game_parameters_future_date(self, validator):
        """Test warning for future game date"""
        params = GameParameters(
            "team_1", "team_2", "2023-24",
            datetime.now() + timedelta(days=30)
        )
        result = validator.validate_game_parameters(params)
        assert len(result.warnings) > 0
        assert any("in the future" in w for w in result.warnings)

    def test_validate_box_score_valid(self, validator):
        """Test validating valid box score"""
        home_stats = {
            "p1": PlayerStats("p1", 25.0, 8.0, 10.0, 2.0, 1.0, 3.0, 35.0),
            "p2": PlayerStats("p2", 20.0, 5.0, 7.0, 1.0, 0.0, 2.0, 30.0),
            "p3": PlayerStats("p3", 15.0, 3.0, 5.0, 1.0, 1.0, 1.0, 25.0),
            "p4": PlayerStats("p4", 18.0, 4.0, 6.0, 2.0, 0.0, 2.0, 28.0),
            "p5": PlayerStats("p5", 12.0, 2.0, 4.0, 0.0, 1.0, 1.0, 20.0)
        }
        away_stats = {
            "p6": PlayerStats("p6", 22.0, 7.0, 9.0, 1.0, 1.0, 2.0, 33.0),
            "p7": PlayerStats("p7", 18.0, 4.0, 6.0, 2.0, 0.0, 1.0, 28.0),
            "p8": PlayerStats("p8", 16.0, 3.0, 5.0, 1.0, 1.0, 2.0, 26.0),
            "p9": PlayerStats("p9", 14.0, 5.0, 4.0, 1.0, 0.0, 3.0, 24.0),
            "p10": PlayerStats("p10", 12.0, 2.0, 3.0, 1.0, 0.0, 1.0, 20.0)
        }

        box_score = BoxScore(
            home_score=90,
            away_score=82,
            home_stats=home_stats,
            away_stats=away_stats,
            quarters=[(22, 20), (23, 21), (24, 20), (21, 21)]
        )

        result = validator.validate_box_score(box_score)
        assert result.is_valid is True

    def test_validate_box_score_quarter_mismatch(self, validator):
        """Test validation fails for quarter score mismatch"""
        box_score = BoxScore(
            home_score=100,
            away_score=95,
            home_stats={},
            away_stats={},
            quarters=[(25, 20), (25, 22), (25, 24), (20, 24)]  # Sum to 95/90, not 100/95
        )

        result = validator.validate_box_score(box_score)
        assert result.is_valid is False
        assert any("score mismatch" in e.lower() for e in result.errors)

    def test_validator_statistics(self, validator, valid_roster):
        """Test validator statistics tracking"""
        # Perform some validations
        validator.validate_roster(valid_roster)
        validator.validate_roster(valid_roster)

        stats = validator.get_statistics()
        assert stats['total_validations'] == 2
        assert stats['strict_mode'] is False

    def test_validator_reset_statistics(self, validator, valid_roster):
        """Test resetting validator statistics"""
        validator.validate_roster(valid_roster)
        validator.reset_statistics()

        stats = validator.get_statistics()
        assert stats['total_validations'] == 0
        assert stats['total_errors'] == 0
        assert stats['total_warnings'] == 0
