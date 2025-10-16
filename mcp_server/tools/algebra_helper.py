"""
Algebraic Equation Manipulation for NBA Analytics

This module provides symbolic mathematics capabilities using SymPy for:
- Equation solving and manipulation
- LaTeX rendering of mathematical expressions
- Sports analytics formula templates
- Symbolic differentiation and integration
- Matrix operations for advanced analytics

Perfect for working with complex sports analytics equations from books.
"""

from typing import Dict, List, Union, Any, Optional, Tuple
import re
import logging
from pathlib import Path

try:
    import sympy as sp
    from sympy import symbols, solve, diff, integrate, simplify, expand, factor
    from sympy import latex, pretty_print, Matrix, Symbol, Eq
    from sympy.parsing.sympy_parser import parse_expr
    SYMPY_AVAILABLE = True
except ImportError:
    sp = None
    SYMPY_AVAILABLE = False

from .sports_validation import validate_formula_inputs, ValidationError as SportsValidationError, suggest_fixes_for_error, validate_formula_consistency

from ..exceptions import ValidationError
from .logger_config import log_operation

# Initialize logger
logger = logging.getLogger(__name__)


def check_sympy_dependency():
    """Check if SymPy is available."""
    if not SYMPY_AVAILABLE:
        raise ImportError(
            "SymPy is required for algebraic operations. "
            "Install with: pip install sympy>=1.13.0"
        )


# =============================================================================
# Core Algebraic Operations
# =============================================================================

@log_operation("algebra_solve_equation")
def solve_equation(equation_str: str, variable: str = None) -> Dict[str, Any]:
    """
    Solve an algebraic equation symbolically.

    Args:
        equation_str: Equation as string (e.g., "x**2 + 2*x - 3 = 0")
        variable: Variable to solve for (auto-detected if None)

    Returns:
        Dict with solutions, LaTeX representation, and metadata

    Examples:
        >>> solve_equation("x**2 + 2*x - 3 = 0")
        {'solutions': [-3, 1], 'latex': 'x^{2} + 2 x - 3 = 0', 'variable': 'x'}

        >>> solve_equation("2*y + 5 = 13", "y")
        {'solutions': [4], 'latex': '2 y + 5 = 13', 'variable': 'y'}
    """
    check_sympy_dependency()

    try:
        # Parse the equation
        if '=' in equation_str:
            left, right = equation_str.split('=', 1)
            left_expr = parse_expr(left.strip())
            right_expr = parse_expr(right.strip())
            equation = Eq(left_expr, right_expr)
        else:
            # Assume it's an expression equal to 0
            equation = Eq(parse_expr(equation_str), 0)

        # Auto-detect variable if not specified
        if variable is None:
            variables = list(equation.free_symbols)
            if len(variables) == 1:
                variable = str(variables[0])
            else:
                raise ValueError(f"Multiple variables found: {variables}. Please specify 'variable' parameter.")

        var_symbol = symbols(variable)

        # Solve the equation
        solutions = solve(equation, var_symbol)

        # Convert to numerical values if possible
        numerical_solutions = []
        for sol in solutions:
            try:
                if sol.is_real:
                    numerical_solutions.append(float(sol.evalf()))
                else:
                    numerical_solutions.append(str(sol))
            except:
                numerical_solutions.append(str(sol))

        return {
            "solutions": numerical_solutions,
            "latex": latex(equation),
            "variable": variable,
            "equation": str(equation),
            "num_solutions": len(solutions),
            "success": True
        }

    except Exception as e:
        logger.error(f"Failed to solve equation '{equation_str}': {e}")
        return {
            "solutions": [],
            "latex": equation_str,
            "variable": variable,
            "equation": equation_str,
            "num_solutions": 0,
            "success": False,
            "error": str(e)
        }


@log_operation("algebra_simplify_expression")
def simplify_expression(expression_str: str) -> Dict[str, Any]:
    """
    Simplify an algebraic expression.

    Args:
        expression_str: Expression as string (e.g., "x**2 + 2*x + 1")

    Returns:
        Dict with simplified expression, LaTeX, and steps

    Examples:
        >>> simplify_expression("x**2 + 2*x + 1")
        {'simplified': '(x + 1)**2', 'latex': '(x + 1)^{2}', 'steps': [...]}
    """
    check_sympy_dependency()

    try:
        expr = parse_expr(expression_str)
        simplified = simplify(expr)

        return {
            "original": expression_str,
            "simplified": str(simplified),
            "latex": latex(simplified),
            "success": True
        }

    except Exception as e:
        logger.error(f"Failed to simplify expression '{expression_str}': {e}")
        return {
            "original": expression_str,
            "simplified": expression_str,
            "latex": expression_str,
            "success": False,
            "error": str(e)
        }


@log_operation("algebra_differentiate")
def differentiate_expression(expression_str: str, variable: str, order: int = 1) -> Dict[str, Any]:
    """
    Differentiate an expression with respect to a variable.

    Args:
        expression_str: Expression to differentiate
        variable: Variable to differentiate with respect to
        order: Order of differentiation (1st, 2nd, etc.)

    Returns:
        Dict with derivative, LaTeX, and metadata

    Examples:
        >>> differentiate_expression("x**3 + 2*x**2 + x", "x")
        {'derivative': '3*x**2 + 4*x + 1', 'latex': '3 x^{2} + 4 x + 1', 'order': 1}
    """
    check_sympy_dependency()

    try:
        expr = parse_expr(expression_str)
        var_symbol = symbols(variable)

        derivative = diff(expr, var_symbol, order)

        return {
            "original": expression_str,
            "derivative": str(derivative),
            "latex": latex(derivative),
            "variable": variable,
            "order": order,
            "success": True
        }

    except Exception as e:
        logger.error(f"Failed to differentiate '{expression_str}': {e}")
        return {
            "original": expression_str,
            "derivative": expression_str,
            "latex": expression_str,
            "variable": variable,
            "order": order,
            "success": False,
            "error": str(e)
        }


@log_operation("algebra_integrate")
def integrate_expression(expression_str: str, variable: str,
                        lower_limit: Optional[Union[int, float]] = None,
                        upper_limit: Optional[Union[int, float]] = None) -> Dict[str, Any]:
    """
    Integrate an expression with respect to a variable.

    Args:
        expression_str: Expression to integrate
        variable: Variable to integrate with respect to
        lower_limit: Lower limit for definite integral
        upper_limit: Upper limit for definite integral

    Returns:
        Dict with integral, LaTeX, and metadata

    Examples:
        >>> integrate_expression("x**2", "x")
        {'integral': 'x**3/3', 'latex': '\\frac{x^{3}}{3}', 'type': 'indefinite'}

        >>> integrate_expression("x**2", "x", 0, 2)
        {'integral': '8/3', 'latex': '\\frac{8}{3}', 'type': 'definite', 'value': 2.6667}
    """
    check_sympy_dependency()

    try:
        expr = parse_expr(expression_str)
        var_symbol = symbols(variable)

        if lower_limit is not None and upper_limit is not None:
            # Definite integral
            integral = integrate(expr, (var_symbol, lower_limit, upper_limit))
            numerical_value = float(integral.evalf())

            return {
                "original": expression_str,
                "integral": str(integral),
                "latex": latex(integral),
                "variable": variable,
                "type": "definite",
                "limits": [lower_limit, upper_limit],
                "value": numerical_value,
                "success": True
            }
        else:
            # Indefinite integral
            integral = integrate(expr, var_symbol)

            return {
                "original": expression_str,
                "integral": str(integral),
                "latex": latex(integral),
                "variable": variable,
                "type": "indefinite",
                "success": True
            }

    except Exception as e:
        logger.error(f"Failed to integrate '{expression_str}': {e}")
        return {
            "original": expression_str,
            "integral": expression_str,
            "latex": expression_str,
            "variable": variable,
            "success": False,
            "error": str(e)
        }


# =============================================================================
# Sports Analytics Equation Templates
# =============================================================================

@log_operation("algebra_sports_formula")
def get_sports_formula(formula_name: str, **kwargs) -> Dict[str, Any]:
    """
    Get predefined sports analytics formulas with symbolic manipulation.

    Args:
        formula_name: Name of the formula (e.g., "per", "true_shooting", "usage_rate")
        **kwargs: Variable values for substitution

    Returns:
        Dict with formula, LaTeX, substituted values, and result

    Available Formulas:
        Core Metrics:
        - "per": Player Efficiency Rating
        - "true_shooting": True Shooting Percentage
        - "usage_rate": Usage Rate
        - "four_factors_shooting": Effective Field Goal Percentage
        - "four_factors_turnovers": Turnover Percentage
        - "pace": Pace calculation

        Advanced Player Metrics:
        - "vorp": Value Over Replacement Player
        - "ws_per_48": Win Shares per 48 minutes
        - "game_score": Game Score
        - "pie": Player Impact Estimate
        - "bpm_offensive": Offensive Box Plus/Minus
        - "bpm_defensive": Defensive Box Plus/Minus
        - "win_shares_offensive": Offensive Win Shares

        Shooting Analytics:
        - "corner_3pt_pct": Corner 3-Point Percentage
        - "rim_fg_pct": Rim Field Goal Percentage
        - "midrange_efficiency": Midrange Shooting Efficiency
        - "catch_and_shoot_pct": Catch and Shoot Percentage
        - "effective_field_goal_percentage": Effective Field Goal Percentage
        - "true_shooting_percentage": True Shooting Percentage
        - "shooting_efficiency_differential": Shooting Efficiency vs League Average

        Defensive Metrics:
        - "defensive_win_shares": Defensive Win Shares
        - "steal_percentage": Steal Percentage
        - "block_percentage": Block Percentage
        - "defensive_rating": Defensive Rating
        - "defensive_impact": Defensive Impact on Team
        - "defensive_rebound_percentage": Defensive Rebound Percentage

        Team Metrics:
        - "net_rating": Net Rating
        - "offensive_efficiency": Offensive Efficiency
        - "defensive_efficiency": Defensive Efficiency
        - "pace_factor": Pace Factor
        - "team_efficiency_differential": Team Efficiency Differential
        - "pace_adjusted_offensive_rating": Pace-Adjusted Offensive Rating
        - "pace_adjusted_defensive_rating": Pace-Adjusted Defensive Rating

        Situational Metrics:
        - "clutch_performance": Clutch Performance
        - "on_off_differential": On/Off Court Differential
        - "plus_minus_per_100": Plus/Minus per 100 possessions
        - "clutch_time_rating": Clutch Time Rating
        - "offensive_impact": Offensive Impact on Team

        Percentage Metrics:
        - "assist_percentage": Assist Percentage
        - "rebound_percentage": Rebound Percentage
        - "turnover_percentage": Turnover Percentage
        - "free_throw_rate": Free Throw Rate
        - "offensive_rebound_percentage": Offensive Rebound Percentage
        - "possession_usage": Possession Usage

        Advanced Analytics:
        - "pace_adjusted_stats": Pace Adjusted Statistics
        - "player_efficiency_rating": Player Efficiency Rating (alias for per)
    """
    check_sympy_dependency()

    # Define sports analytics formulas
    formulas = {
        "per": {
            "formula": "PER = (FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
            "variables": ["FGM", "STL", "3PM", "FTM", "BLK", "OREB", "AST", "DREB", "PF", "FTA", "FGA", "TOV", "MP"],
            "description": "Player Efficiency Rating - comprehensive player value metric"
        },

        "true_shooting": {
            "formula": "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
            "variables": ["PTS", "FGA", "FTA"],
            "description": "True Shooting Percentage - accounts for 3-pointers and free throws"
        },

        "usage_rate": {
            "formula": "USG% = ((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
            "variables": ["FGA", "FTA", "TOV", "TM_MP", "MP", "TM_FGA", "TM_FTA", "TM_TOV"],
            "description": "Usage Rate - percentage of team plays used by player"
        },

        "four_factors_shooting": {
            "formula": "eFG% = (FGM + 0.5 * 3PM) / FGA",
            "variables": ["FGM", "3PM", "FGA"],
            "description": "Effective Field Goal Percentage - adjusts for 3-pointers"
        },

        "four_factors_turnovers": {
            "formula": "TOV% = TOV / (FGA + 0.44 * FTA + TOV) * 100",
            "variables": ["TOV", "FGA", "FTA"],
            "description": "Turnover Percentage - turnovers per 100 plays"
        },

        "pace": {
            "formula": "Pace = 48 * ((TM_POSS + OPP_POSS) / (2 * TM_MP))",
            "variables": ["TM_POSS", "OPP_POSS", "TM_MP"],
            "description": "Pace - possessions per 48 minutes"
        },

        # Advanced Player Metrics
        "vorp": {
            "formula": "VORP = (BPM - (-2.0)) * (POSS_PCT / 100) * (TEAM_GAMES / 82)",
            "variables": ["BPM", "POSS_PCT", "TEAM_GAMES"],
            "description": "Value Over Replacement Player - measures value above replacement level"
        },

        "ws_per_48": {
            "formula": "WS/48 = (WS * 48 * TEAM_GAMES) / MP",
            "variables": ["WS", "TEAM_GAMES", "MP"],
            "description": "Win Shares per 48 minutes - win shares normalized to 48 minutes"
        },

        "game_score": {
            "formula": "Game Score = PTS + 0.4 * FGM - 0.7 * FGA - 0.4 * (FTA - FTM) + 0.7 * OREB + 0.3 * DREB + STL + 0.7 * AST + 0.7 * BLK - 0.4 * PF - TOV",
            "variables": ["PTS", "FGM", "FGA", "FTA", "FTM", "OREB", "DREB", "STL", "AST", "BLK", "PF", "TOV"],
            "description": "Game Score - single-game performance metric"
        },

        "pie": {
            "formula": "PIE = (PTS + FGM + FTM - FGA - FTA + DREB + (0.5 * OREB) + AST + STL + (0.5 * BLK) - PF - TOV) / (GmPTS + GmFGM + GmFTM - GmFGA - GmFTA + GmDREB + (0.5 * GmOREB) + GmAST + GmSTL + (0.5 * GmBLK) - GmPF - GmTOV)",
            "variables": ["PTS", "FGM", "FTM", "FGA", "FTA", "DREB", "OREB", "AST", "STL", "BLK", "PF", "TOV", "GmPTS", "GmFGM", "GmFTM", "GmFGA", "GmFTA", "GmDREB", "GmOREB", "GmAST", "GmSTL", "GmBLK", "GmPF", "GmTOV"],
            "description": "Player Impact Estimate - percentage of team's positive contributions"
        },

        # Shooting Analytics
        "corner_3pt_pct": {
            "formula": "Corner 3PT% = Corner_3PM / Corner_3PA",
            "variables": ["Corner_3PM", "Corner_3PA"],
            "description": "Corner 3-Point Percentage - shooting efficiency from corner"
        },

        "rim_fg_pct": {
            "formula": "Rim FG% = Rim_FGM / Rim_FGA",
            "variables": ["Rim_FGM", "Rim_FGA"],
            "description": "Rim Field Goal Percentage - shooting efficiency at the rim"
        },

        "midrange_efficiency": {
            "formula": "Midrange Efficiency = Midrange_FGM / Midrange_FGA",
            "variables": ["Midrange_FGM", "Midrange_FGA"],
            "description": "Midrange Shooting Efficiency - shooting from midrange areas"
        },

        "catch_and_shoot_pct": {
            "formula": "Catch & Shoot% = C&S_FGM / C&S_FGA",
            "variables": ["C&S_FGM", "C&S_FGA"],
            "description": "Catch and Shoot Percentage - shooting off passes"
        },

        # Defensive Metrics
        "defensive_win_shares": {
            "formula": "DWS = (DRtg - 110) * (MP / 48) * (TEAM_PACE / 100)",
            "variables": ["DRtg", "MP", "TEAM_PACE"],
            "description": "Defensive Win Shares - defensive contribution to team wins"
        },

        "steal_percentage": {
            "formula": "STL% = (STL * (TM_MP / 5)) / (MP * OPP_POSS) * 100",
            "variables": ["STL", "TM_MP", "MP", "OPP_POSS"],
            "description": "Steal Percentage - steals per 100 opponent possessions"
        },

        "block_percentage": {
            "formula": "BLK% = (BLK * (TM_MP / 5)) / (MP * OPP_2PA) * 100",
            "variables": ["BLK", "TM_MP", "MP", "OPP_2PA"],
            "description": "Block Percentage - blocks per 100 opponent 2-point attempts"
        },

        "defensive_rating": {
            "formula": "DRtg = 100 * (OPP_PTS / OPP_POSS)",
            "variables": ["OPP_PTS", "OPP_POSS"],
            "description": "Defensive Rating - points allowed per 100 possessions"
        },

        # Team Metrics
        "net_rating": {
            "formula": "Net Rating = ORtg - DRtg",
            "variables": ["ORtg", "DRtg"],
            "description": "Net Rating - difference between offensive and defensive rating"
        },

        "offensive_efficiency": {
            "formula": "Offensive Efficiency = (PTS / POSS) * 100",
            "variables": ["PTS", "POSS"],
            "description": "Offensive Efficiency - points per 100 possessions"
        },

        "defensive_efficiency": {
            "formula": "Defensive Efficiency = (OPP_PTS / OPP_POSS) * 100",
            "variables": ["OPP_PTS", "OPP_POSS"],
            "description": "Defensive Efficiency - points allowed per 100 possessions"
        },

        "pace_factor": {
            "formula": "Pace Factor = PACE / League_Avg_Pace",
            "variables": ["PACE", "League_Avg_Pace"],
            "description": "Pace Factor - team pace relative to league average"
        },

        # Situational Metrics
        "clutch_performance": {
            "formula": "Clutch Performance = (Clutch_PTS + Clutch_AST + Clutch_REB) / Clutch_MIN",
            "variables": ["Clutch_PTS", "Clutch_AST", "Clutch_REB", "Clutch_MIN"],
            "description": "Clutch Performance - performance in close game situations"
        },

        "on_off_differential": {
            "formula": "On/Off Differential = Team_ORtg_On - Team_ORtg_Off",
            "variables": ["Team_ORtg_On", "Team_ORtg_Off"],
            "description": "On/Off Court Differential - team performance with/without player"
        },

        "plus_minus_per_100": {
            "formula": "Plus/Minus per 100 = (Plus_Minus * 100) / MP",
            "variables": ["Plus_Minus", "MP"],
            "description": "Plus/Minus per 100 possessions - point differential normalized"
        },

        # Additional Advanced Metrics
        "bpm_offensive": {
            "formula": "OBPM = (Raw_OBPM * Pace_Adjustment) + League_Avg_OBPM",
            "variables": ["Raw_OBPM", "Pace_Adjustment", "League_Avg_OBPM"],
            "description": "Offensive Box Plus/Minus - offensive contribution per 100 possessions"
        },

        "bpm_defensive": {
            "formula": "DBPM = (Raw_DBPM * Pace_Adjustment) + League_Avg_DBPM",
            "variables": ["Raw_DBPM", "Pace_Adjustment", "League_Avg_DBPM"],
            "description": "Defensive Box Plus/Minus - defensive contribution per 100 possessions"
        },

        "win_shares_offensive": {
            "formula": "OWS = (PTS - League_Avg_PTS_per_Poss * POSS) * (MP / (TEAM_MP / 5))",
            "variables": ["PTS", "League_Avg_PTS_per_Poss", "POSS", "MP", "TEAM_MP"],
            "description": "Offensive Win Shares - offensive contribution to team wins"
        },

        "assist_percentage": {
            "formula": "AST% = (AST * (TM_MP / 5)) / (MP * (TM_FGM - Player_FGM)) * 100",
            "variables": ["AST", "TM_MP", "MP", "TM_FGM", "Player_FGM"],
            "description": "Assist Percentage - assists per 100 teammate field goals"
        },

        "rebound_percentage": {
            "formula": "REB% = (REB * (TM_MP / 5)) / (MP * (TM_REB + OPP_REB)) * 100",
            "variables": ["REB", "TM_MP", "MP", "TM_REB", "OPP_REB"],
            "description": "Rebound Percentage - rebounds per 100 available rebounds"
        },

        "turnover_percentage": {
            "formula": "TOV% = TOV / (FGA + 0.44 * FTA + TOV) * 100",
            "variables": ["TOV", "FGA", "FTA"],
            "description": "Turnover Percentage - turnovers per 100 plays"
        },

        "free_throw_rate": {
            "formula": "FTR = FTA / FGA",
            "variables": ["FTA", "FGA"],
            "description": "Free Throw Rate - free throw attempts per field goal attempt"
        },

        "effective_field_goal_percentage": {
            "formula": "eFG% = (FGM + 0.5 * 3PM) / FGA",
            "variables": ["FGM", "3PM", "FGA"],
            "description": "Effective Field Goal Percentage - adjusts for 3-pointers"
        },

        "true_shooting_percentage": {
            "formula": "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
            "variables": ["PTS", "FGA", "FTA"],
            "description": "True Shooting Percentage - accounts for all shooting"
        },

        "player_efficiency_rating": {
            "formula": "PER = (FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
            "variables": ["FGM", "STL", "3PM", "FTM", "BLK", "OREB", "AST", "DREB", "PF", "FTA", "FGA", "TOV", "MP"],
            "description": "Player Efficiency Rating - comprehensive player value"
        },

        "pace_adjusted_stats": {
            "formula": "Pace_Adjusted = (Stat * League_Avg_Pace) / Team_Pace",
            "variables": ["Stat", "League_Avg_Pace", "Team_Pace"],
            "description": "Pace Adjusted Statistics - normalizes stats for pace differences"
        },

        "clutch_time_rating": {
            "formula": "Clutch Rating = (Clutch_PTS + Clutch_AST + Clutch_REB - Clutch_TOV) / Clutch_MIN * 48",
            "variables": ["Clutch_PTS", "Clutch_AST", "Clutch_REB", "Clutch_TOV", "Clutch_MIN"],
            "description": "Clutch Time Rating - performance in clutch situations per 48 minutes"
        },

        "defensive_impact": {
            "formula": "Defensive Impact = (Team_DRtg_Off - Team_DRtg_On) * (MP / TEAM_MP)",
            "variables": ["Team_DRtg_Off", "Team_DRtg_On", "MP", "TEAM_MP"],
            "description": "Defensive Impact - team defensive rating change with player on court"
        },

        "offensive_impact": {
            "formula": "Offensive Impact = (Team_ORtg_On - Team_ORtg_Off) * (MP / TEAM_MP)",
            "variables": ["Team_ORtg_On", "Team_ORtg_Off", "MP", "TEAM_MP"],
            "description": "Offensive Impact - team offensive rating change with player on court"
        },

        "shooting_efficiency_differential": {
            "formula": "Shooting Efficiency Differential = Player_eFG% - League_Avg_eFG%",
            "variables": ["Player_eFG%", "League_Avg_eFG%"],
            "description": "Shooting Efficiency Differential - player efficiency vs league average"
        },

        "possession_usage": {
            "formula": "Possession Usage = (FGA + 0.44 * FTA + TOV) / Team_Possessions * 100",
            "variables": ["FGA", "FTA", "TOV", "Team_Possessions"],
            "description": "Possession Usage - percentage of team possessions used by player"
        },

        "defensive_rebound_percentage": {
            "formula": "DRB% = (DREB * (TM_MP / 5)) / (MP * (TM_DREB + OPP_OREB)) * 100",
            "variables": ["DREB", "TM_MP", "MP", "TM_DREB", "OPP_OREB"],
            "description": "Defensive Rebound Percentage - defensive rebounds per 100 available"
        },

        "offensive_rebound_percentage": {
            "formula": "ORB% = (OREB * (TM_MP / 5)) / (MP * (TM_OREB + OPP_DREB)) * 100",
            "variables": ["OREB", "TM_MP", "MP", "TM_OREB", "OPP_DREB"],
            "description": "Offensive Rebound Percentage - offensive rebounds per 100 available"
        },

        "team_efficiency_differential": {
            "formula": "Team Efficiency Differential = Team_ORtg - Team_DRtg",
            "variables": ["Team_ORtg", "Team_DRtg"],
            "description": "Team Efficiency Differential - net rating for team performance"
        },

        "pace_adjusted_offensive_rating": {
            "formula": "Pace-Adjusted ORtg = ORtg * (League_Avg_Pace / Team_Pace)",
            "variables": ["ORtg", "League_Avg_Pace", "Team_Pace"],
            "description": "Pace-Adjusted Offensive Rating - offensive rating normalized for pace"
        },

        "pace_adjusted_defensive_rating": {
            "formula": "Pace-Adjusted DRtg = DRtg * (League_Avg_Pace / Team_Pace)",
            "variables": ["DRtg", "League_Avg_Pace", "Team_Pace"],
            "description": "Pace-Adjusted Defensive Rating - defensive rating normalized for pace"
        }
    }

    if formula_name not in formulas:
        available = list(formulas.keys())
        raise ValueError(f"Unknown formula '{formula_name}'. Available: {available}")

    formula_info = formulas[formula_name]

    try:
        # Validate inputs if variables are provided
        if kwargs:
            try:
                validated_kwargs = validate_formula_inputs(formula_name, kwargs)
                # Check for consistency warnings
                warnings = validate_formula_consistency(formula_name, validated_kwargs)
                if warnings:
                    logger.warning(f"Formula consistency warnings for {formula_name}: {warnings}")
            except SportsValidationError as e:
                suggestions = suggest_fixes_for_error(str(e), formula_name)
                error_msg = f"Validation error for {formula_name}: {e}"
                if suggestions:
                    error_msg += f"\nSuggestions: {'; '.join(suggestions)}"
                raise ValueError(error_msg)

        # Parse the formula
        formula_parts = formula_info["formula"].split("=", 1)
        if len(formula_parts) != 2:
            raise ValueError(f"Invalid formula format: {formula_info['formula']}")

        left_side = formula_parts[0].strip()
        right_side = formula_parts[1].strip()

        # Substitute values if provided
        substituted_formula = right_side
        substituted_values = {}

        for var in formula_info["variables"]:
            if var in kwargs:
                substituted_values[var] = kwargs[var]
                # Replace variable names with their values
                substituted_formula = substituted_formula.replace(var, str(kwargs[var]))

        # Calculate result if all variables are provided
        result = None
        if len(substituted_values) == len(formula_info["variables"]):
            try:
                # Clean up the formula for parsing
                clean_formula = substituted_formula.replace(" ", "")
                expr = parse_expr(clean_formula)
                result = float(expr.evalf())
            except Exception as parse_error:
                logger.warning(f"Could not parse substituted formula '{substituted_formula}': {parse_error}")
                # Try manual calculation for common patterns
                try:
                    # Simple manual calculation for basic arithmetic
                    result = eval(substituted_formula)
                except:
                    pass

        return {
            "formula_name": formula_name,
            "formula": formula_info["formula"],
            "latex": formula_info["formula"],  # Use original formula for LaTeX
            "variables": formula_info["variables"],
            "description": formula_info["description"],
            "substituted_values": substituted_values,
            "substituted_formula": substituted_formula,
            "result": result,
            "success": True
        }

    except Exception as e:
        logger.error(f"Failed to process formula '{formula_name}': {e}")
        return {
            "formula_name": formula_name,
            "formula": formula_info["formula"],
            "latex": formula_info["formula"],
            "variables": formula_info["variables"],
            "description": formula_info["description"],
            "success": False,
            "error": str(e)
        }


# =============================================================================
# LaTeX Rendering and Display
# =============================================================================

@log_operation("algebra_render_latex")
def render_equation_latex(expression_str: str, display_mode: bool = False) -> Dict[str, Any]:
    """
    Convert a mathematical expression to LaTeX format.

    Args:
        expression_str: Mathematical expression as string
        display_mode: Use display math mode ($$) instead of inline ($)

    Returns:
        Dict with LaTeX code and rendering info

    Examples:
        >>> render_equation_latex("x**2 + 2*x + 1")
        {'latex': 'x^{2} + 2 x + 1', 'display_mode': False, 'inline': '$x^{2} + 2 x + 1$'}

        >>> render_equation_latex("x**2 + 2*x + 1", display_mode=True)
        {'latex': 'x^{2} + 2 x + 1', 'display_mode': True, 'display': '$$x^{2} + 2 x + 1$$'}
    """
    check_sympy_dependency()

    try:
        expr = parse_expr(expression_str)
        latex_code = latex(expr)

        result = {
            "expression": expression_str,
            "latex": latex_code,
            "display_mode": display_mode,
            "success": True
        }

        if display_mode:
            result["display"] = f"$${latex_code}$$"
        else:
            result["inline"] = f"${latex_code}$"

        return result

    except Exception as e:
        logger.error(f"Failed to render LaTeX for '{expression_str}': {e}")
        return {
            "expression": expression_str,
            "latex": expression_str,
            "display_mode": display_mode,
            "success": False,
            "error": str(e)
        }


@log_operation("algebra_parse_latex")
def parse_latex_equation(latex_str: str) -> Dict[str, Any]:
    """
    Parse a LaTeX equation back to SymPy expression.

    Args:
        latex_str: LaTeX equation string

    Returns:
        Dict with parsed expression and metadata

    Examples:
        >>> parse_latex_equation("x^{2} + 2x + 1")
        {'expression': 'x**2 + 2*x + 1', 'latex': 'x^{2} + 2 x + 1', 'success': True}
    """
    check_sympy_dependency()

    try:
        # Remove LaTeX delimiters if present
        clean_latex = latex_str.strip()
        if clean_latex.startswith('$') and clean_latex.endswith('$'):
            clean_latex = clean_latex[1:-1]
        if clean_latex.startswith('$$') and clean_latex.endswith('$$'):
            clean_latex = clean_latex[2:-2]

        # Convert LaTeX to SymPy expression
        expr = sp.latex2sympy(clean_latex)

        return {
            "latex": latex_str,
            "expression": str(expr),
            "simplified_latex": latex(expr),
            "success": True
        }

    except Exception as e:
        logger.error(f"Failed to parse LaTeX '{latex_str}': {e}")
        return {
            "latex": latex_str,
            "expression": latex_str,
            "success": False,
            "error": str(e)
        }


# =============================================================================
# Matrix Operations for Advanced Analytics
# =============================================================================

@log_operation("algebra_matrix_operations")
def matrix_operations(matrix_data: List[List[Union[int, float]]],
                     operation: str,
                     **kwargs) -> Dict[str, Any]:
    """
    Perform matrix operations for advanced analytics.

    Args:
        matrix_data: 2D list representing the matrix
        operation: Operation to perform ("determinant", "inverse", "eigenvalues", "multiply")
        **kwargs: Additional parameters (e.g., matrix2 for multiplication)

    Returns:
        Dict with operation result and metadata

    Examples:
        >>> matrix_operations([[1, 2], [3, 4]], "determinant")
        {'operation': 'determinant', 'result': -2, 'success': True}

        >>> matrix_operations([[1, 2], [3, 4]], "multiply", matrix2=[[5, 6], [7, 8]])
        {'operation': 'multiply', 'result': [[19, 22], [43, 50]], 'success': True}
    """
    check_sympy_dependency()

    try:
        matrix = Matrix(matrix_data)

        if operation == "determinant":
            result = matrix.det()

        elif operation == "inverse":
            result = matrix.inv()

        elif operation == "eigenvalues":
            eigenvals = matrix.eigenvals()
            result = list(eigenvals.keys())

        elif operation == "multiply":
            if "matrix2" not in kwargs:
                raise ValueError("matrix2 parameter required for multiplication")
            matrix2 = Matrix(kwargs["matrix2"])
            result = matrix * matrix2

        elif operation == "transpose":
            result = matrix.T

        else:
            raise ValueError(f"Unknown operation '{operation}'. Available: determinant, inverse, eigenvalues, multiply, transpose")

        # Convert result to appropriate format
        if hasattr(result, 'tolist'):
            result_data = result.tolist()
        else:
            result_data = result

        return {
            "operation": operation,
            "input_matrix": matrix_data,
            "result": result_data,
            "latex": latex(result) if hasattr(result, '__iter__') else str(result),
            "success": True
        }

    except Exception as e:
        logger.error(f"Failed matrix operation '{operation}': {e}")
        return {
            "operation": operation,
            "input_matrix": matrix_data,
            "result": None,
            "success": False,
            "error": str(e)
        }


# =============================================================================
# Equation System Solving
# =============================================================================

@log_operation("algebra_solve_system")
def solve_equation_system(equations: List[str], variables: List[str]) -> Dict[str, Any]:
    """
    Solve a system of equations.

    Args:
        equations: List of equation strings
        variables: List of variable names

    Returns:
        Dict with solutions and metadata

    Examples:
        >>> solve_equation_system(["x + y = 5", "x - y = 1"], ["x", "y"])
        {'solutions': {'x': 3, 'y': 2}, 'success': True}
    """
    check_sympy_dependency()

    try:
        # Parse equations
        parsed_equations = []
        for eq_str in equations:
            if '=' in eq_str:
                left, right = eq_str.split('=', 1)
                left_expr = parse_expr(left.strip())
                right_expr = parse_expr(right.strip())
                parsed_equations.append(Eq(left_expr, right_expr))
            else:
                parsed_equations.append(Eq(parse_expr(eq_str), 0))

        # Create variable symbols
        var_symbols = symbols(variables)

        # Solve the system
        solutions = solve(parsed_equations, var_symbols)

        # Convert solutions to dictionary
        if isinstance(solutions, dict):
            solution_dict = {str(k): float(v.evalf()) if v.is_real else str(v) for k, v in solutions.items()}
        else:
            solution_dict = {}
            for i, sol in enumerate(solutions):
                if isinstance(sol, dict):
                    solution_dict.update({str(k): float(v.evalf()) if v.is_real else str(v) for k, v in sol.items()})

        return {
            "equations": equations,
            "variables": variables,
            "solutions": solution_dict,
            "num_solutions": len(solutions) if isinstance(solutions, list) else 1,
            "success": True
        }

    except Exception as e:
        logger.error(f"Failed to solve equation system: {e}")
        return {
            "equations": equations,
            "variables": variables,
            "solutions": {},
            "success": False,
            "error": str(e)
        }
