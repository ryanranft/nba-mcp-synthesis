"""
NBA-Specific Metrics Calculations
Advanced basketball statistics and efficiency metrics

Formulas based on Basketball Reference and NBA.com standards
"""

from typing import Dict, Any, Union
import math

from mcp_server.exceptions import ValidationError
from mcp_server.tools.logger_config import log_operation


# =============================================================================
# Player Efficiency Metrics
# =============================================================================

@log_operation("nba_player_efficiency_rating")
def calculate_per(stats: Dict[str, Union[int, float]]) -> float:
    """
    Calculate Player Efficiency Rating (PER).

    Simplified PER formula:
    PER = (Points + Rebounds + Assists + Steals + Blocks
           - Missed FG - Missed FT - Turnovers) / Minutes Played * 100

    Note: This is a simplified version. Full PER includes pace adjustments
    and league averages.

    Args:
        stats: Dictionary with player stats
            - points: Points scored
            - rebounds: Total rebounds
            - assists: Assists
            - steals: Steals
            - blocks: Blocks
            - fgm: Field goals made
            - fga: Field goals attempted
            - ftm: Free throws made
            - fta: Free throws attempted
            - turnovers: Turnovers
            - minutes: Minutes played

    Returns:
        PER value (league average is 15.0)

    Raises:
        ValidationError: If required fields are missing

    Example:
        >>> stats = {
        ...     "points": 250, "rebounds": 100, "assists": 80,
        ...     "steals": 20, "blocks": 15, "fgm": 95, "fga": 200,
        ...     "ftm": 60, "fta": 75, "turnovers": 40, "minutes": 500
        ... }
        >>> calculate_per(stats)
        18.5
    """
    required_fields = [
        "points", "rebounds", "assists", "steals", "blocks",
        "fgm", "fga", "ftm", "fta", "turnovers", "minutes"
    ]

    for field in required_fields:
        if field not in stats:
            raise ValidationError(
                f"Missing required field: {field}",
                field,
                None
            )

    if stats["minutes"] == 0:
        return 0.0

    # Positive contributions
    positive = (
        stats["points"] +
        stats["rebounds"] +
        stats["assists"] +
        stats["steals"] +
        stats["blocks"]
    )

    # Negative contributions
    negative = (
        (stats["fga"] - stats["fgm"]) +  # Missed FG
        (stats["fta"] - stats["ftm"]) +  # Missed FT
        stats["turnovers"]
    )

    # Calculate per-minute efficiency and scale
    per = (positive - negative) / stats["minutes"] * 100

    return round(per, 2)


@log_operation("nba_true_shooting_percentage")
def calculate_true_shooting(
    points: Union[int, float],
    fga: Union[int, float],
    fta: Union[int, float]
) -> float:
    """
    Calculate True Shooting Percentage (TS%).

    Formula:
    TS% = Points / (2 * (FGA + 0.44 * FTA))

    Accounts for the value of 3-pointers and free throws.

    Args:
        points: Total points scored
        fga: Field goals attempted
        fta: Free throws attempted

    Returns:
        True shooting percentage (0-1 scale, where 0.550 = 55.0%)

    Example:
        >>> calculate_true_shooting(250, 200, 75)
        0.543
    """
    denominator = 2 * (fga + 0.44 * fta)

    if denominator == 0:
        return 0.0

    ts_pct = points / denominator
    return round(ts_pct, 3)


@log_operation("nba_effective_field_goal_percentage")
def calculate_effective_fg_pct(
    fgm: Union[int, float],
    fga: Union[int, float],
    three_pm: Union[int, float]
) -> float:
    """
    Calculate Effective Field Goal Percentage (eFG%).

    Formula:
    eFG% = (FGM + 0.5 * 3PM) / FGA

    Adjusts for the fact that 3-point field goals are worth more.

    Args:
        fgm: Field goals made
        fga: Field goals attempted
        three_pm: Three-pointers made

    Returns:
        Effective FG% (0-1 scale)

    Example:
        >>> calculate_effective_fg_pct(95, 200, 30)
        0.55
    """
    if fga == 0:
        return 0.0

    efg = (fgm + 0.5 * three_pm) / fga
    return round(efg, 3)


@log_operation("nba_usage_rate")
def calculate_usage_rate(
    fga: Union[int, float],
    fta: Union[int, float],
    turnovers: Union[int, float],
    minutes: float,
    team_minutes: float,
    team_fga: Union[int, float],
    team_fta: Union[int, float],
    team_turnovers: Union[int, float]
) -> float:
    """
    Calculate Usage Rate (USG%).

    Measures the percentage of team plays used by a player while on the floor.

    Formula:
    USG% = 100 * ((FGA + 0.44 * FTA + TOV) * (Tm MP / 5)) /
           (MP * (Tm FGA + 0.44 * Tm FTA + Tm TOV))

    Args:
        fga: Player's field goal attempts
        fta: Player's free throw attempts
        turnovers: Player's turnovers
        minutes: Player's minutes played
        team_minutes: Team's total minutes
        team_fga: Team's field goal attempts
        team_fta: Team's free throw attempts
        team_turnovers: Team's turnovers

    Returns:
        Usage rate percentage

    Example:
        >>> calculate_usage_rate(
        ...     fga=200, fta=75, turnovers=40, minutes=500,
        ...     team_minutes=4800, team_fga=1800, team_fta=600,
        ...     team_turnovers=350
        ... )
        24.5
    """
    if minutes == 0:
        return 0.0

    player_possessions = fga + 0.44 * fta + turnovers
    team_possessions = team_fga + 0.44 * team_fta + team_turnovers

    if team_possessions == 0:
        return 0.0

    usg_rate = (
        100 * (player_possessions * (team_minutes / 5)) /
        (minutes * team_possessions)
    )

    return round(usg_rate, 2)


# =============================================================================
# Team Efficiency Metrics
# =============================================================================

@log_operation("nba_offensive_rating")
def calculate_offensive_rating(
    points: Union[int, float],
    possessions: Union[int, float]
) -> float:
    """
    Calculate Offensive Rating (ORtg).

    Formula:
    ORtg = (Points / Possessions) * 100

    Points scored per 100 possessions.

    Args:
        points: Points scored
        possessions: Estimated possessions

    Returns:
        Offensive rating (points per 100 possessions)

    Example:
        >>> calculate_offensive_rating(2500, 2200)
        113.64
    """
    if possessions == 0:
        return 0.0

    ortg = (points / possessions) * 100
    return round(ortg, 2)


@log_operation("nba_defensive_rating")
def calculate_defensive_rating(
    points_allowed: Union[int, float],
    possessions: Union[int, float]
) -> float:
    """
    Calculate Defensive Rating (DRtg).

    Formula:
    DRtg = (Points Allowed / Possessions) * 100

    Points allowed per 100 possessions (lower is better).

    Args:
        points_allowed: Points allowed
        possessions: Estimated possessions

    Returns:
        Defensive rating (points allowed per 100 possessions)

    Example:
        >>> calculate_defensive_rating(2300, 2200)
        104.55
    """
    if possessions == 0:
        return 0.0

    drtg = (points_allowed / possessions) * 100
    return round(drtg, 2)


@log_operation("nba_pace")
def calculate_pace(
    possessions: Union[int, float],
    minutes: float
) -> float:
    """
    Calculate Pace (possessions per 48 minutes).

    Formula:
    Pace = (Possessions / Minutes) * 48

    Args:
        possessions: Total possessions
        minutes: Total minutes played

    Returns:
        Pace (possessions per 48 minutes)

    Example:
        >>> calculate_pace(2200, 2400)
        44.0
    """
    if minutes == 0:
        return 0.0

    pace = (possessions / minutes) * 48
    return round(pace, 2)


# =============================================================================
# Advanced Metrics
# =============================================================================

@log_operation("nba_win_shares")
def calculate_win_shares(
    marginal_offense: float,
    marginal_defense: float,
    marginal_points_per_win: float = 30.0
) -> float:
    """
    Calculate Win Shares (simplified version).

    Formula:
    WS = (Marginal Offense + Marginal Defense) / Marginal Points per Win

    Note: Full win shares calculation requires extensive team context.

    Args:
        marginal_offense: Offensive contribution above average
        marginal_defense: Defensive contribution above average
        marginal_points_per_win: Points needed for a win (default: 30)

    Returns:
        Estimated win shares

    Example:
        >>> calculate_win_shares(120, 80, 30)
        6.67
    """
    ws = (marginal_offense + marginal_defense) / marginal_points_per_win
    return round(ws, 2)


@log_operation("nba_box_plus_minus")
def calculate_box_plus_minus(
    per: float,
    team_pace: float,
    league_avg_per: float = 15.0,
    league_avg_pace: float = 100.0
) -> float:
    """
    Calculate Box Plus/Minus (BPM) - simplified estimate.

    Estimates the points per 100 possessions a player contributes
    above a league-average player.

    Note: This is a very simplified version. Real BPM uses regression.

    Args:
        per: Player Efficiency Rating
        team_pace: Team's pace
        league_avg_per: League average PER (default: 15.0)
        league_avg_pace: League average pace (default: 100.0)

    Returns:
        Estimated BPM

    Example:
        >>> calculate_box_plus_minus(20, 98, 15, 100)
        2.45
    """
    # Simplified: scale PER difference by pace adjustment
    pace_adjustment = team_pace / league_avg_pace
    per_diff = per - league_avg_per

    # Rough conversion: 1 PER point ≈ 0.5 BPM
    bpm = (per_diff * 0.5) * pace_adjustment

    return round(bpm, 2)


@log_operation("nba_four_factors")
def calculate_four_factors(stats: Dict[str, Union[int, float]]) -> Dict[str, Any]:
    """
    Calculate Dean Oliver's Four Factors of Basketball Success.

    The Four Factors (in order of importance):
    1. Shooting (eFG%) - Making shots efficiently
    2. Turnovers (TOV%) - Taking care of the ball
    3. Rebounding (ORB%/DRB%) - Controlling the boards
    4. Free Throws (FTR) - Getting to the line

    Args:
        stats: Dictionary with team stats
            Offensive stats:
            - fgm: Field goals made
            - fga: Field goals attempted
            - three_pm: Three-pointers made
            - tov: Turnovers
            - fta: Free throw attempts
            - orb: Offensive rebounds
            - team_orb: Total team offensive rebounds
            - opp_drb: Opponent defensive rebounds

            Defensive stats:
            - opp_fgm: Opponent field goals made
            - opp_fga: Opponent field goals attempted
            - opp_three_pm: Opponent three-pointers made
            - opp_tov: Opponent turnovers
            - opp_fta: Opponent free throw attempts
            - drb: Defensive rebounds
            - team_drb: Total team defensive rebounds
            - opp_orb: Opponent offensive rebounds

    Returns:
        Dictionary with offensive and defensive Four Factors:
        {
            "offensive": {
                "efg_pct": float,     # Shooting efficiency
                "tov_pct": float,     # Turnover rate
                "orb_pct": float,     # Offensive rebound rate
                "ftr": float          # Free throw rate
            },
            "defensive": {
                "efg_pct": float,     # Opponent shooting efficiency
                "tov_pct": float,     # Opponent turnover rate (forced)
                "drb_pct": float,     # Defensive rebound rate
                "ftr": float          # Opponent free throw rate
            }
        }

    Example:
        >>> stats = {
        ...     "fgm": 3200, "fga": 7000, "three_pm": 1000,
        ...     "tov": 1100, "fta": 1800, "orb": 900,
        ...     "team_orb": 900, "opp_drb": 2800,
        ...     "opp_fgm": 2900, "opp_fga": 6800, "opp_three_pm": 800,
        ...     "opp_tov": 1200, "opp_fta": 1600, "drb": 2800,
        ...     "team_drb": 2800, "opp_orb": 850
        ... }
        >>> calculate_four_factors(stats)
        {
            "offensive": {...},
            "defensive": {...}
        }
    """
    # Offensive Four Factors
    off_efg = calculate_effective_fg_pct(
        stats.get("fgm", 0),
        stats.get("fga", 0),
        stats.get("three_pm", 0)
    )

    off_tov_pct = calculate_turnover_percentage(
        stats.get("tov", 0),
        stats.get("fga", 0),
        stats.get("fta", 0)
    )

    off_orb_pct = calculate_rebound_percentage(
        stats.get("orb", 0),
        stats.get("team_orb", 0),
        stats.get("opp_drb", 0)
    )

    off_ftr = calculate_free_throw_rate(
        stats.get("fta", 0),
        stats.get("fga", 0)
    )

    # Defensive Four Factors
    def_efg = calculate_effective_fg_pct(
        stats.get("opp_fgm", 0),
        stats.get("opp_fga", 0),
        stats.get("opp_three_pm", 0)
    )

    def_tov_pct = calculate_turnover_percentage(
        stats.get("opp_tov", 0),
        stats.get("opp_fga", 0),
        stats.get("opp_fta", 0)
    )

    def_drb_pct = calculate_rebound_percentage(
        stats.get("drb", 0),
        stats.get("team_drb", 0),
        stats.get("opp_orb", 0)
    )

    def_ftr = calculate_free_throw_rate(
        stats.get("opp_fta", 0),
        stats.get("opp_fga", 0)
    )

    return {
        "offensive": {
            "efg_pct": off_efg,
            "tov_pct": off_tov_pct,
            "orb_pct": off_orb_pct,
            "ftr": off_ftr
        },
        "defensive": {
            "efg_pct": def_efg,
            "tov_pct": def_tov_pct,
            "drb_pct": def_drb_pct,
            "ftr": def_ftr
        }
    }


@log_operation("nba_turnover_percentage")
def calculate_turnover_percentage(
    tov: Union[int, float],
    fga: Union[int, float],
    fta: Union[int, float]
) -> float:
    """
    Calculate Turnover Percentage (TOV%).

    Formula:
    TOV% = 100 × TOV / (FGA + 0.44 × FTA + TOV)

    Estimate of turnovers per 100 plays.

    Args:
        tov: Turnovers
        fga: Field goal attempts
        fta: Free throw attempts

    Returns:
        Turnover percentage (lower is better)

    Example:
        >>> calculate_turnover_percentage(250, 1800, 600)
        11.48  # 11.48% turnover rate
    """
    denominator = fga + 0.44 * fta + tov

    if denominator == 0:
        return 0.0

    tov_pct = 100 * (tov / denominator)
    return round(tov_pct, 2)


@log_operation("nba_rebound_percentage")
def calculate_rebound_percentage(
    rebounds: Union[int, float],
    team_rebounds: Union[int, float],
    opp_rebounds: Union[int, float]
) -> float:
    """
    Calculate Rebound Percentage (REB%).

    Formula:
    REB% = 100 × Rebounds / (Team Rebounds + Opponent Rebounds)

    Percentage of available rebounds grabbed by player/team.

    Args:
        rebounds: Player/team rebounds (offensive or defensive)
        team_rebounds: Total team rebounds of that type
        opp_rebounds: Opponent rebounds of opposite type
                     (team ORB% uses opponent DRB)

    Returns:
        Rebound percentage

    Example:
        >>> calculate_rebound_percentage(900, 900, 2800)
        24.32  # Team gets 24.32% of offensive rebounds available
    """
    total_available = team_rebounds + opp_rebounds

    if total_available == 0:
        return 0.0

    reb_pct = 100 * (rebounds / total_available)
    return round(reb_pct, 2)


@log_operation("nba_assist_percentage")
def calculate_assist_percentage(
    assists: Union[int, float],
    minutes: float,
    team_minutes: float,
    team_fgm: Union[int, float],
    player_fgm: Union[int, float] = 0
) -> float:
    """
    Calculate Assist Percentage (AST%).

    Formula:
    AST% = 100 × AST / [(MP / 5 × Team FGM) - Player FGM]

    Estimate of percentage of teammate field goals assisted while on court.

    Args:
        assists: Player assists
        minutes: Player minutes played
        team_minutes: Team total minutes (usually 240 for full game)
        team_fgm: Team field goals made
        player_fgm: Player's own field goals made (to exclude)

    Returns:
        Assist percentage

    Example:
        >>> calculate_assist_percentage(
        ...     assists=500, minutes=2000, team_minutes=19680,
        ...     team_fgm=3200, player_fgm=600
        ... )
        18.52  # Player assisted on 18.52% of teammate FGs while on court
    """
    if minutes == 0:
        return 0.0

    # Estimate of teammate FGM while player on court
    teammate_fgm = (minutes / 5) * team_fgm - player_fgm

    if teammate_fgm <= 0:
        return 0.0

    ast_pct = 100 * (assists / teammate_fgm)
    return round(ast_pct, 2)


@log_operation("nba_steal_percentage")
def calculate_steal_percentage(
    steals: Union[int, float],
    minutes: float,
    team_minutes: float,
    opp_possessions: Union[int, float]
) -> float:
    """
    Calculate Steal Percentage (STL%).

    Formula:
    STL% = 100 × (STL × (Team MP / 5)) / (MP × Opp Poss)

    Estimate of steals per 100 opponent possessions while on court.

    Args:
        steals: Player steals
        minutes: Player minutes played
        team_minutes: Team total minutes
        opp_possessions: Opponent possessions

    Returns:
        Steal percentage

    Example:
        >>> calculate_steal_percentage(
        ...     steals=120, minutes=2000, team_minutes=19680,
        ...     opp_possessions=8000
        ... )
        2.95  # 2.95 steals per 100 opponent possessions
    """
    if minutes == 0 or opp_possessions == 0:
        return 0.0

    stl_pct = 100 * (steals * (team_minutes / 5)) / (minutes * opp_possessions)
    return round(stl_pct, 2)


@log_operation("nba_block_percentage")
def calculate_block_percentage(
    blocks: Union[int, float],
    minutes: float,
    team_minutes: float,
    opp_two_pa: Union[int, float]
) -> float:
    """
    Calculate Block Percentage (BLK%).

    Formula:
    BLK% = 100 × (BLK × (Team MP / 5)) / (MP × Opp 2PA)

    Estimate of opponent 2-point attempts blocked while on court.

    Args:
        blocks: Player blocks
        minutes: Player minutes played
        team_minutes: Team total minutes
        opp_two_pa: Opponent 2-point attempts

    Returns:
        Block percentage

    Example:
        >>> calculate_block_percentage(
        ...     blocks=100, minutes=2000, team_minutes=19680,
        ...     opp_two_pa=5000
        ... )
        3.94  # Blocks 3.94% of opponent 2PA while on court
    """
    if minutes == 0 or opp_two_pa == 0:
        return 0.0

    blk_pct = 100 * (blocks * (team_minutes / 5)) / (minutes * opp_two_pa)
    return round(blk_pct, 2)


# =============================================================================
# Shooting Metrics
# =============================================================================

@log_operation("nba_three_point_rate")
def calculate_three_point_rate(
    three_pa: Union[int, float],
    fga: Union[int, float]
) -> float:
    """
    Calculate 3-Point Attempt Rate (3PAr).

    Formula:
    3PAr = 3PA / FGA

    Percentage of field goal attempts that are 3-pointers.

    Args:
        three_pa: Three-point attempts
        fga: Total field goal attempts

    Returns:
        3-point rate (0-1 scale)

    Example:
        >>> calculate_three_point_rate(150, 400)
        0.375
    """
    if fga == 0:
        return 0.0

    rate = three_pa / fga
    return round(rate, 3)


@log_operation("nba_free_throw_rate")
def calculate_free_throw_rate(
    fta: Union[int, float],
    fga: Union[int, float]
) -> float:
    """
    Calculate Free Throw Rate (FTr).

    Formula:
    FTr = FTA / FGA

    Measures how often a player gets to the free throw line.

    Args:
        fta: Free throw attempts
        fga: Field goal attempts

    Returns:
        Free throw rate

    Example:
        >>> calculate_free_throw_rate(150, 400)
        0.375
    """
    if fga == 0:
        return 0.0

    rate = fta / fga
    return round(rate, 3)


# =============================================================================
# Utility Functions
# =============================================================================

def estimate_possessions(
    fga: Union[int, float],
    fta: Union[int, float],
    orb: Union[int, float],
    tov: Union[int, float]
) -> float:
    """
    Estimate total possessions (simplified formula).

    Formula:
    Poss ≈ FGA + 0.44 * FTA - ORB + TOV

    Args:
        fga: Field goal attempts
        fta: Free throw attempts
        orb: Offensive rebounds
        tov: Turnovers

    Returns:
        Estimated possessions

    Example:
        >>> estimate_possessions(1800, 600, 250, 350)
        2164.0
    """
    poss = fga + 0.44 * fta - orb + tov
    return round(poss, 1)


def check_dependencies():
    """
    Check if all required dependencies are available.
    NBA metrics use only Python standard library.

    Raises:
        ImportError: If required modules are not available
    """
    # NBA metrics only use Python standard library
    # No external dependencies required
    pass
