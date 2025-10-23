"""
Sports Statistics Validation Helper

Provides validation functions for sports statistics to ensure
data integrity and provide meaningful error messages.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)


class StatType(Enum):
    """Types of sports statistics"""

    PERCENTAGE = "percentage"  # 0.0 to 1.0
    RATE = "rate"  # Per game, per 100 possessions, etc.
    COUNT = "count"  # Raw numbers
    MINUTES = "minutes"  # Playing time
    RATING = "rating"  # Efficiency ratings


class ValidationError(Exception):
    """Custom exception for validation errors"""

    pass


def validate_sports_stat(
    stat_name: str, value: Any, stat_type: StatType = StatType.COUNT
) -> bool:
    """
    Validate a sports statistic value.

    Args:
        stat_name: Name of the statistic
        value: Value to validate
        stat_type: Type of statistic (percentage, rate, count, etc.)

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(f"{stat_name} cannot be None")

    # Check type before conversion - reject strings even if numeric
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(
            f"{stat_name} must be a numeric type (int or float), got {type(value).__name__}"
        )

    float_value = float(value)

    if stat_type == StatType.PERCENTAGE:
        if not (0.0 <= float_value <= 1.0):
            raise ValidationError(
                f"{stat_name} must be between 0.0 and 1.0 (percentage), got {float_value}"
            )

    elif stat_type == StatType.MINUTES:
        # Use get_stat_range() to get dynamic min/max based on stat name
        stat_range = get_stat_range(stat_name)
        if not (stat_range['min'] <= float_value <= stat_range['max']):
            raise ValidationError(
                f"{stat_name} must be between {stat_range['min']} and {stat_range['max']} minutes, got {float_value}"
            )

    elif stat_type == StatType.COUNT:
        if float_value < 0:
            raise ValidationError(f"{stat_name} cannot be negative, got {float_value}")

    elif stat_type == StatType.RATE:
        if float_value < 0:
            raise ValidationError(f"{stat_name} cannot be negative, got {float_value}")

    elif stat_type == StatType.RATING:
        # Ratings can be negative (like BPM)
        pass

    return True


def validate_formula_inputs(
    formula_name: str, variables: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate inputs for a specific sports formula.

    Args:
        formula_name: Name of the formula
        variables: Dictionary of variable values

    Returns:
        Validated variables dictionary

    Raises:
        ValidationError: If validation fails
    """
    # Define validation rules for each formula
    validation_rules = {
        "per": {
            "FGM": StatType.COUNT,
            "STL": StatType.COUNT,
            "3PM": StatType.COUNT,
            "FTM": StatType.COUNT,
            "BLK": StatType.COUNT,
            "OREB": StatType.COUNT,
            "AST": StatType.COUNT,
            "DREB": StatType.COUNT,
            "PF": StatType.COUNT,
            "FTA": StatType.COUNT,
            "FGA": StatType.COUNT,
            "TOV": StatType.COUNT,
            "MP": StatType.MINUTES,
        },
        "true_shooting": {
            "PTS": StatType.COUNT,
            "FGA": StatType.COUNT,
            "FTA": StatType.COUNT,
        },
        "usage_rate": {
            "FGA": StatType.COUNT,
            "FTA": StatType.COUNT,
            "TOV": StatType.COUNT,
            "TM_MP": StatType.MINUTES,
            "MP": StatType.MINUTES,
            "TM_FGA": StatType.COUNT,
            "TM_FTA": StatType.COUNT,
            "TM_TOV": StatType.COUNT,
        },
        "four_factors_shooting": {
            "FGM": StatType.COUNT,
            "3PM": StatType.COUNT,
            "FGA": StatType.COUNT,
        },
        "four_factors_turnovers": {
            "TOV": StatType.COUNT,
            "FGA": StatType.COUNT,
            "FTA": StatType.COUNT,
        },
        "pace": {
            "TM_POSS": StatType.COUNT,
            "OPP_POSS": StatType.COUNT,
            "TM_MP": StatType.MINUTES,
        },
        "vorp": {
            "BPM": StatType.RATING,
            "POSS_PCT": StatType.PERCENTAGE,
            "TEAM_GAMES": StatType.COUNT,
        },
        "ws_per_48": {
            "WS": StatType.RATE,
            "TEAM_GAMES": StatType.COUNT,
            "MP": StatType.MINUTES,
        },
        "game_score": {
            "PTS": StatType.COUNT,
            "FGM": StatType.COUNT,
            "FGA": StatType.COUNT,
            "FTA": StatType.COUNT,
            "FTM": StatType.COUNT,
            "OREB": StatType.COUNT,
            "DREB": StatType.COUNT,
            "STL": StatType.COUNT,
            "AST": StatType.COUNT,
            "BLK": StatType.COUNT,
            "PF": StatType.COUNT,
            "TOV": StatType.COUNT,
        },
        "pie": {
            "PTS": StatType.COUNT,
            "FGM": StatType.COUNT,
            "FTM": StatType.COUNT,
            "FGA": StatType.COUNT,
            "FTA": StatType.COUNT,
            "DREB": StatType.COUNT,
            "OREB": StatType.COUNT,
            "AST": StatType.COUNT,
            "STL": StatType.COUNT,
            "BLK": StatType.COUNT,
            "PF": StatType.COUNT,
            "TOV": StatType.COUNT,
            "GmPTS": StatType.COUNT,
            "GmFGM": StatType.COUNT,
            "GmFTM": StatType.COUNT,
            "GmFGA": StatType.COUNT,
            "GmFTA": StatType.COUNT,
            "GmDREB": StatType.COUNT,
            "GmOREB": StatType.COUNT,
            "GmAST": StatType.COUNT,
            "GmSTL": StatType.COUNT,
            "GmBLK": StatType.COUNT,
            "GmPF": StatType.COUNT,
            "GmTOV": StatType.COUNT,
        },
        "corner_3pt_pct": {"Corner_3PM": StatType.COUNT, "Corner_3PA": StatType.COUNT},
        "rim_fg_pct": {"Rim_FGM": StatType.COUNT, "Rim_FGA": StatType.COUNT},
        "midrange_efficiency": {
            "Midrange_FGM": StatType.COUNT,
            "Midrange_FGA": StatType.COUNT,
        },
        "catch_and_shoot_pct": {"C&S_FGM": StatType.COUNT, "C&S_FGA": StatType.COUNT},
        "defensive_win_shares": {
            "DRtg": StatType.RATING,
            "MP": StatType.MINUTES,
            "TEAM_PACE": StatType.RATE,
        },
        "steal_percentage": {
            "STL": StatType.COUNT,
            "TM_MP": StatType.MINUTES,
            "MP": StatType.MINUTES,
            "OPP_POSS": StatType.COUNT,
        },
        "block_percentage": {
            "BLK": StatType.COUNT,
            "TM_MP": StatType.MINUTES,
            "MP": StatType.MINUTES,
            "OPP_2PA": StatType.COUNT,
        },
        "defensive_rating": {"OPP_PTS": StatType.COUNT, "OPP_POSS": StatType.COUNT},
        "net_rating": {"ORtg": StatType.RATING, "DRtg": StatType.RATING},
        "offensive_efficiency": {"PTS": StatType.COUNT, "POSS": StatType.COUNT},
        "defensive_efficiency": {"OPP_PTS": StatType.COUNT, "OPP_POSS": StatType.COUNT},
        "pace_factor": {"PACE": StatType.RATE, "League_Avg_Pace": StatType.RATE},
        "clutch_performance": {
            "Clutch_PTS": StatType.COUNT,
            "Clutch_AST": StatType.COUNT,
            "Clutch_REB": StatType.COUNT,
            "Clutch_MIN": StatType.MINUTES,
        },
        "on_off_differential": {
            "Team_ORtg_On": StatType.RATING,
            "Team_ORtg_Off": StatType.RATING,
        },
        "plus_minus_per_100": {"Plus_Minus": StatType.RATING, "MP": StatType.MINUTES},
    }

    if formula_name not in validation_rules:
        logger.warning(f"No validation rules defined for formula: {formula_name}")
        return {"valid": True, "variables": variables}

    rules = validation_rules[formula_name]
    validated_vars = {}
    errors = []

    for var_name, var_value in variables.items():
        if var_name in rules:
            try:
                validate_sports_stat(var_name, var_value, rules[var_name])
                validated_vars[var_name] = var_value
            except ValidationError as e:
                logger.error(f"Validation failed for {formula_name}.{var_name}: {e}")
                errors.append(f"{var_name}: {e}")
                # Don't raise - collect errors and return them
        else:
            logger.warning(
                f"No validation rule for variable {var_name} in formula {formula_name}"
            )
            validated_vars[var_name] = var_value

    # If there are errors, return invalid result
    if errors:
        return {"valid": False, "variables": validated_vars, "errors": errors}

    return {"valid": True, "variables": validated_vars, "errors": []}


def suggest_fixes_for_error(error_message: str, formula_name: str) -> List[str]:
    """
    Suggest fixes for common validation errors.

    Args:
        error_message: The error message
        formula_name: Name of the formula

    Returns:
        List of suggested fixes
    """
    suggestions = []

    if "cannot be negative" in error_message:
        suggestions.append("Check that all statistics are non-negative")
        suggestions.append("Verify data source accuracy")

    elif "must be between 0.0 and 1.0" in error_message:
        suggestions.append("Convert percentage to decimal (e.g., 0.45 for 45%)")
        suggestions.append("Check if percentage was already converted")

    elif "must be between 0.0 and 48.0 minutes" in error_message:
        suggestions.append("Check minutes played are within game limits")
        suggestions.append("Verify time format (minutes, not seconds)")

    elif "must be a number" in error_message:
        suggestions.append("Ensure all inputs are numeric")
        suggestions.append("Remove any text or special characters")

    elif "cannot be None" in error_message:
        suggestions.append("Provide a value for all required variables")
        suggestions.append("Check data completeness")

    # Formula-specific suggestions
    if formula_name == "per":
        suggestions.append(
            "PER requires all 13 variables: FGM, STL, 3PM, FTM, BLK, OREB, AST, DREB, PF, FTA, FGA, TOV, MP"
        )
        suggestions.append("Ensure MP (minutes played) > 0")

    elif formula_name == "true_shooting":
        suggestions.append("TS% requires: PTS, FGA, FTA")
        suggestions.append("Ensure FGA + FTA > 0 to avoid division by zero")

    elif formula_name == "usage_rate":
        suggestions.append("Usage Rate requires team and player statistics")
        suggestions.append("Ensure MP > 0 and team minutes > 0")

    return suggestions


def validate_formula_consistency(
    formula_name: str, variables: Dict[str, Any]
) -> List[str]:
    """
    Check for logical consistency in formula inputs.

    Args:
        formula_name: Name of the formula
        variables: Dictionary of variable values

    Returns:
        List of consistency warnings
    """
    warnings = []

    # General consistency checks
    if "FGM" in variables and "FGA" in variables:
        if variables["FGM"] > variables["FGA"]:
            warnings.append("Field goals made cannot exceed field goals attempted")

    if "FTM" in variables and "FTA" in variables:
        if variables["FTM"] > variables["FTA"]:
            warnings.append("Free throws made cannot exceed free throws attempted")

    if "3PM" in variables and "FGM" in variables:
        if variables["3PM"] > variables["FGM"]:
            warnings.append("3-pointers made cannot exceed total field goals made")

    if "OREB" in variables and "DREB" in variables:
        total_rebounds = variables["OREB"] + variables["DREB"]
        if total_rebounds > 50:  # Reasonable upper bound
            warnings.append(f"Total rebounds ({total_rebounds}) seems unusually high")

    # Formula-specific checks
    if formula_name == "per":
        if variables.get("MP", 0) == 0:
            warnings.append("PER calculation requires MP > 0")

        if variables.get("FGA", 0) == 0 and variables.get("FTA", 0) == 0:
            warnings.append("Player with no shot attempts may have unusual PER")

    elif formula_name == "true_shooting":
        if variables.get("FGA", 0) + 0.44 * variables.get("FTA", 0) == 0:
            warnings.append("TS% calculation requires FGA + 0.44*FTA > 0")

    elif formula_name == "usage_rate":
        team_total = (
            variables.get("TM_FGA", 0)
            + 0.44 * variables.get("TM_FTA", 0)
            + variables.get("TM_TOV", 0)
        )
        if team_total == 0:
            warnings.append(
                "Usage Rate calculation requires team total possessions > 0"
            )

    return warnings


def get_formula_requirements(formula_name: str) -> Dict[str, str]:
    """
    Get the requirements and descriptions for a formula.

    Args:
        formula_name: Name of the formula

    Returns:
        Dictionary mapping variable names to descriptions
    """
    requirements = {
        "per": {
            "FGM": "Field Goals Made",
            "STL": "Steals",
            "3PM": "3-Pointers Made",
            "FTM": "Free Throws Made",
            "BLK": "Blocks",
            "OREB": "Offensive Rebounds",
            "AST": "Assists",
            "DREB": "Defensive Rebounds",
            "PF": "Personal Fouls",
            "FTA": "Free Throw Attempts",
            "FGA": "Field Goal Attempts",
            "TOV": "Turnovers",
            "MP": "Minutes Played",
        },
        "true_shooting": {
            "PTS": "Points Scored",
            "FGA": "Field Goal Attempts",
            "FTA": "Free Throw Attempts",
        },
        "usage_rate": {
            "FGA": "Player Field Goal Attempts",
            "FTA": "Player Free Throw Attempts",
            "TOV": "Player Turnovers",
            "TM_MP": "Team Minutes Played",
            "MP": "Player Minutes Played",
            "TM_FGA": "Team Field Goal Attempts",
            "TM_FTA": "Team Free Throw Attempts",
            "TM_TOV": "Team Turnovers",
        },
        "vorp": {
            "BPM": "Box Plus/Minus",
            "POSS_PCT": "Possession Percentage (0.0-1.0)",
            "TEAM_GAMES": "Team Games Played",
        },
        "game_score": {
            "PTS": "Points",
            "FGM": "Field Goals Made",
            "FGA": "Field Goal Attempts",
            "FTA": "Free Throw Attempts",
            "FTM": "Free Throws Made",
            "OREB": "Offensive Rebounds",
            "DREB": "Defensive Rebounds",
            "STL": "Steals",
            "AST": "Assists",
            "BLK": "Blocks",
            "PF": "Personal Fouls",
            "TOV": "Turnovers",
        },
    }

    return requirements.get(formula_name, {})


# =============================================================================
# Additional Validation Functions for Test Compatibility
# =============================================================================


def get_stat_range(stat_name: str) -> Dict[str, float]:
    """
    Get the valid range for a sports statistic.

    Args:
        stat_name: Name of the statistic

    Returns:
        Dictionary with 'min' and 'max' values

    Example:
        >>> get_stat_range('PTS')
        {'min': 0, 'max': 150}
    """
    stat_ranges = {
        'PTS': {'min': 0, 'max': 150},
        'AST': {'min': 0, 'max': 50},
        'REB': {'min': 0, 'max': 50},
        'STL': {'min': 0, 'max': 20},
        'BLK': {'min': 0, 'max': 20},
        'FG%': {'min': 0, 'max': 1},
        'FT%': {'min': 0, 'max': 1},
        '3P%': {'min': 0, 'max': 1},
            'MP': {'min': 0, 'max': 4000},  # Player minutes (48 per game × 82 games = 3936 max season)
            'MIN': {'min': 0, 'max': 4000},  # Alias for MP
        'TM_MP': {'min': 0, 'max': 240},  # Team minutes (48 × 5 players)
        'TEAM_MP': {'min': 0, 'max': 240},  # Alias for TM_MP
        'FGA': {'min': 0, 'max': 100},
        'FGM': {'min': 0, 'max': 100},
        'FTA': {'min': 0, 'max': 50},
        'FTM': {'min': 0, 'max': 50},
        '3PA': {'min': 0, 'max': 50},
        '3PM': {'min': 0, 'max': 50},
        'TOV': {'min': 0, 'max': 20},
        'PF': {'min': 0, 'max': 10},
        'TM_FGA': {'min': 0, 'max': 200},  # Team field goal attempts
        'TM_FTA': {'min': 0, 'max': 100},  # Team free throw attempts
        'TM_TOV': {'min': 0, 'max': 50},  # Team turnovers
    }

    stat_upper = stat_name.upper()
    return stat_ranges.get(stat_upper, {'min': 0, 'max': float('inf')})


def validate_stat_range(stat_name: str, value: float) -> bool:
    """
    Validate if a statistic value is within acceptable range.

    Args:
        stat_name: Name of the statistic
        value: Value to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_stat_range('PTS', 25)
        True
        >>> validate_stat_range('PTS', 200)
        False
    """
    range_dict = get_stat_range(stat_name)
    return range_dict['min'] <= value <= range_dict['max']


def validate_stat_type(stat_name: str, value: Any) -> bool:
    """
    Validate if a statistic value is the correct type.

    Args:
        stat_name: Name of the statistic
        value: Value to validate

    Returns:
        True if correct type, False otherwise

    Example:
        >>> validate_stat_type('PTS', 25)
        True
        >>> validate_stat_type('PTS', "twenty-five")
        False
    """
    # Check if value is already a number (int or float)
    # Reject strings even if they're numeric (like "25")
    return isinstance(value, (int, float)) and not isinstance(value, bool)
