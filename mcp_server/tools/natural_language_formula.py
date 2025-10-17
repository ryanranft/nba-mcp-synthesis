"""
Natural Language to Formula Conversion

This module provides capabilities for converting natural language descriptions
of mathematical formulas into SymPy expressions. It uses pattern matching,
keyword recognition, and context analysis to parse sports analytics formulas.

Author: NBA MCP Server Team
Date: October 13, 2025
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from sympy import symbols, Symbol, Add, Mul, Pow, Rational

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.tag import pos_tag

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from ..exceptions import ValidationError
from .logger_config import log_operation

# Initialize logger
logger = logging.getLogger(__name__)

# Use ValidationError for all tool errors
ToolError = ValidationError


class NaturalLanguageFormulaParser:
    """
    Parser for converting natural language descriptions to mathematical formulas.

    Capabilities:
    - Parse sports analytics formulas from natural language
    - Handle common mathematical operations and functions
    - Support for fractions, percentages, and ratios
    - Context-aware variable recognition
    - Formula validation and error correction
    """

    def __init__(self):
        self.sports_variables = {
            # Basic stats
            "points": "PTS",
            "rebounds": "REB",
            "assists": "AST",
            "steals": "STL",
            "blocks": "BLK",
            "turnovers": "TOV",
            "field_goals_made": "FGM",
            "field_goals_attempted": "FGA",
            "three_pointers_made": "3PM",
            "three_pointers_attempted": "3PA",
            "free_throws_made": "FTM",
            "free_throws_attempted": "FTA",
            "minutes_played": "MP",
            "games_played": "GP",
            # Advanced metrics
            "player_efficiency_rating": "PER",
            "true_shooting_percentage": "TS%",
            "usage_rate": "USG%",
            "pace": "PACE",
            "offensive_rating": "ORtg",
            "defensive_rating": "DRtg",
            "net_rating": "NetRtg",
            "win_shares": "WS",
            "value_over_replacement_player": "VORP",
            "box_plus_minus": "BPM",
            "game_score": "GmSc",
            # Team stats
            "team_points": "Team_PTS",
            "team_rebounds": "Team_REB",
            "team_assists": "Team_AST",
            "team_minutes": "Team_MP",
            "opponent_points": "Opp_PTS",
            "opponent_rebounds": "Opp_REB",
            "league_average": "League_Avg",
            "replacement_level": "Replacement",
        }

        self.mathematical_operations = {
            "plus": "+",
            "add": "+",
            "addition": "+",
            "minus": "-",
            "subtract": "-",
            "subtraction": "-",
            "times": "*",
            "multiply": "*",
            "multiplication": "*",
            "divided by": "/",
            "divide": "/",
            "division": "/",
            "to the power of": "**",
            "raised to": "**",
            "exponent": "**",
            "squared": "**2",
            "cubed": "**3",
            "square root": "sqrt",
            "root": "sqrt",
            "absolute value": "abs",
            "modulus": "abs",
        }

        self.functions = {
            "maximum": "max",
            "minimum": "min",
            "average": "mean",
            "sum": "sum",
            "total": "sum",
            "count": "count",
            "logarithm": "log",
            "natural log": "ln",
            "exponential": "exp",
            "sine": "sin",
            "cosine": "cos",
            "tangent": "tan",
        }

        self.percentage_keywords = ["percent", "percentage", "%", "pct"]
        self.fraction_keywords = ["fraction", "ratio", "rate", "per"]

    def parse_natural_language_formula(self, description: str) -> Dict[str, Any]:
        """
        Parse a natural language description into a mathematical formula.

        Args:
            description: Natural language description of the formula

        Returns:
            Dictionary with parsed formula, variables, and metadata
        """
        logger.info(f"Parsing natural language formula: '{description}'")

        try:
            # Clean and normalize the description
            cleaned_description = self._clean_description(description)

            # Extract variables
            variables = self._extract_variables(cleaned_description)

            # Convert to mathematical expression
            formula_expr = self._convert_to_expression(cleaned_description, variables)

            # Validate the formula
            validation_result = self._validate_formula(formula_expr, variables)

            # Generate LaTeX representation
            latex_formula = sp.latex(formula_expr)

            result = {
                "original_description": description,
                "cleaned_description": cleaned_description,
                "formula_string": str(formula_expr),
                "formula_sympy": str(formula_expr),
                "formula_latex": latex_formula,
                "variables": variables,
                "validation": validation_result,
                "status": "success",
            }

            logger.info(f"Successfully parsed formula: {formula_expr}")
            return result

        except Exception as e:
            logger.error(f"Failed to parse natural language formula: {e}")
            raise ToolError(f"Failed to parse formula: {e}")

    def _clean_description(self, description: str) -> str:
        """Clean and normalize the natural language description."""
        # Convert to lowercase
        cleaned = description.lower()

        # Remove extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Replace common abbreviations
        replacements = {
            "pts": "points",
            "reb": "rebounds",
            "ast": "assists",
            "stl": "steals",
            "blk": "blocks",
            "tov": "turnovers",
            "fgm": "field goals made",
            "fga": "field goals attempted",
            "3pm": "three pointers made",
            "3pa": "three pointers attempted",
            "ftm": "free throws made",
            "fta": "free throws attempted",
            "mp": "minutes played",
            "gp": "games played",
        }

        for abbrev, full in replacements.items():
            cleaned = cleaned.replace(abbrev, full)

        return cleaned

    def _extract_variables(self, description: str) -> List[str]:
        """Extract variables from the description."""
        variables = []
        description_lower = description.lower()

        # Special handling for common formula types (check first)
        if "efficiency" in description_lower and "rating" in description_lower:
            # Player Efficiency Rating typically includes these variables
            variables = [
                "PTS",
                "REB",
                "AST",
                "STL",
                "BLK",
                "FGA",
                "FGM",
                "FTA",
                "FTM",
                "TOV",
                "MP",
            ]
        elif "true shooting" in description_lower:
            # True shooting percentage
            variables = ["PTS", "FGA", "FTA"]
        elif "shooting" in description_lower and "percentage" in description_lower:
            # Shooting percentage typically includes these variables
            variables = ["FGM", "FGA"]
        elif "usage" in description_lower and "rate" in description_lower:
            # Usage rate typically includes these variables
            variables = ["FGA", "FTA", "TOV", "MP"]
        elif "win" in description_lower and "shares" in description_lower:
            # Win shares typically includes these variables
            variables = ["PTS", "REB", "AST"]
        elif "assist" in description_lower and "ratio" in description_lower:
            # Assist ratio typically includes these variables
            variables = ["AST", "TOV"]
        elif "field goal" in description_lower:
            # Field goal percentage
            variables = ["FGM", "FGA"]

        # If no special handling matched, try other methods
        if not variables:
            # Look for sports variables in the original description (case insensitive)
            for var_name, abbrev in self.sports_variables.items():
                if var_name in description_lower or abbrev.lower() in description_lower:
                    variables.append(abbrev)

            # Look for mathematical variables (single letters)
            math_vars = re.findall(r"\b[a-z]\b", description)
            for var in math_vars:
                if var not in [
                    "a",
                    "an",
                    "the",
                    "is",
                    "of",
                    "to",
                    "in",
                    "on",
                    "at",
                    "by",
                    "for",
                    "with",
                ]:
                    if var not in variables:
                        variables.append(var)

            # Look for common formula patterns
            patterns = [
                r"(\w+)\s*(?:per|/)\s*(\w+)",  # "points per game"
                r"(\w+)\s*rate",  # "usage rate"
                r"(\w+)\s*percentage",  # "field goal percentage"
                r"(\w+)\s*ratio",  # "assist ratio"
            ]

            for pattern in patterns:
                matches = re.findall(pattern, description)
                for match in matches:
                    if isinstance(match, tuple):
                        # Only add variables that are actual basketball terms
                        basketball_terms = {
                            "points",
                            "rebounds",
                            "assists",
                            "steals",
                            "blocks",
                            "turnovers",
                            "field",
                            "goals",
                            "three",
                            "pointers",
                            "free",
                            "throws",
                            "minutes",
                            "games",
                        }
                        for m in match:
                            if m.lower() in basketball_terms:
                                variables.append(m.upper())
                    else:
                        if match.lower() in basketball_terms:
                            variables.append(match.upper())

            # If still no variables found, try to extract from common basketball terms
            if not variables:
                basketball_terms = {
                    "points": "PTS",
                    "rebounds": "REB",
                    "assists": "AST",
                    "steals": "STL",
                    "blocks": "BLK",
                    "turnovers": "TOV",
                    "field goals made": "FGM",
                    "field goals attempted": "FGA",
                    "three pointers made": "3PM",
                    "three pointers attempted": "3PA",
                    "free throws made": "FTM",
                    "free throws attempted": "FTA",
                    "minutes played": "MP",
                    "games played": "GP",
                }

                for term, abbrev in basketball_terms.items():
                    if term in description_lower:
                        variables.append(abbrev)

        return list(set(variables))  # Remove duplicates

    def _convert_to_expression(self, description: str, variables: List[str]) -> sp.Expr:
        """Convert the description to a SymPy expression."""
        # Start with the description
        expr_str = description

        # Replace mathematical operations
        for op_text, op_symbol in self.mathematical_operations.items():
            expr_str = expr_str.replace(op_text, op_symbol)

        # Replace functions
        for func_text, func_symbol in self.functions.items():
            expr_str = expr_str.replace(func_text, func_symbol)

        # Handle percentages
        expr_str = self._handle_percentages(expr_str)

        # Handle fractions and ratios
        expr_str = self._handle_fractions(expr_str)

        # Handle common sports formula patterns
        expr_str = self._handle_sports_patterns(expr_str, variables)

        # Clean up the expression string
        expr_str = self._clean_expression_string(expr_str)

        try:
            # Parse with SymPy
            expr = parse_expr(expr_str, evaluate=False)
            return expr
        except Exception as e:
            # If parsing fails, try to construct manually
            logger.warning(f"SymPy parsing failed, attempting manual construction: {e}")
            return self._construct_expression_manually(expr_str, variables)

    def _handle_percentages(self, expr_str: str) -> str:
        """Handle percentage conversions."""
        # Convert "X percent" to "X/100"
        expr_str = re.sub(r"(\d+(?:\.\d+)?)\s*percent", r"(\1/100)", expr_str)
        expr_str = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", expr_str)

        # Convert "percentage of X" to "X/100"
        expr_str = re.sub(r"percentage\s+of\s+(\w+)", r"(\1/100)", expr_str)

        return expr_str

    def _handle_fractions(self, expr_str: str) -> str:
        """Handle fraction and ratio conversions."""
        # Convert "X per Y" to "X/Y"
        expr_str = re.sub(r"(\w+)\s+per\s+(\w+)", r"(\1/\2)", expr_str)

        # Convert "X divided by Y" to "X/Y"
        expr_str = re.sub(r"(\w+)\s+divided\s+by\s+(\w+)", r"(\1/\2)", expr_str)

        # Convert "ratio of X to Y" to "X/Y"
        expr_str = re.sub(r"ratio\s+of\s+(\w+)\s+to\s+(\w+)", r"(\1/\2)", expr_str)

        return expr_str

    def _handle_sports_patterns(self, expr_str: str, variables: List[str]) -> str:
        """Handle common sports analytics patterns."""
        # Player Efficiency Rating pattern
        if "player efficiency rating" in expr_str or "per" in expr_str:
            expr_str = self._parse_per_pattern(expr_str)

        # True Shooting Percentage pattern
        if "true shooting percentage" in expr_str or "true shooting" in expr_str:
            expr_str = self._parse_ts_pattern(expr_str)

        # Usage Rate pattern
        if "usage rate" in expr_str:
            expr_str = self._parse_usage_rate_pattern(expr_str)

        # Win Shares pattern
        if "win shares" in expr_str:
            expr_str = self._parse_win_shares_pattern(expr_str)

        return expr_str

    def _parse_per_pattern(self, expr_str: str) -> str:
        """Parse Player Efficiency Rating pattern."""
        # PER = (1/MP) * [3P + (2/3)*AST + (2 - factor*(tmAST/tmFG))*FG + (FT*0.5*(1 + (1 - (tmAST/tmFG)) + (2/3)*(tmAST/tmFG)))]
        # Simplified version for natural language
        return "((PTS + REB + AST + STL + BLK - (FGA - FGM) - (FTA - FTM) - TOV) / MP) * 100"

    def _parse_ts_pattern(self, expr_str: str) -> str:
        """Parse True Shooting Percentage pattern."""
        return "PTS / (2 * (FGA + 0.44 * FTA))"

    def _parse_usage_rate_pattern(self, expr_str: str) -> str:
        """Parse Usage Rate pattern."""
        return "((FGA + 0.44 * FTA + TOV) * (Team_MP / 5)) / (MP * (Team_FGA + 0.44 * Team_FTA + Team_TOV)) * 100"

    def _parse_win_shares_pattern(self, expr_str: str) -> str:
        """Parse Win Shares pattern."""
        return "((PTS - League_Avg_PTS) + (REB - League_Avg_REB) + (AST - League_Avg_AST)) / 30"

    def _clean_expression_string(self, expr_str: str) -> str:
        """Clean up the expression string for parsing."""
        # Remove extra spaces around operators
        expr_str = re.sub(r"\s*([+\-*/])\s*", r"\1", expr_str)

        # Ensure proper parentheses
        expr_str = re.sub(
            r"(\w+)\s*(\w+)", r"\1 * \2", expr_str
        )  # Implicit multiplication

        # Clean up double operators
        expr_str = re.sub(r"\+\+", "+", expr_str)
        expr_str = re.sub(r"--", "+", expr_str)
        expr_str = re.sub(r"\+\-", "-", expr_str)

        return expr_str

    def _construct_expression_manually(
        self, expr_str: str, variables: List[str]
    ) -> sp.Expr:
        """Manually construct expression when parsing fails."""
        logger.info(f"Constructing expression manually with variables: {variables}")

        # This is a fallback method for complex expressions
        # For now, return a simple expression based on variables
        if len(variables) >= 2:
            return sp.Symbol(variables[0]) + sp.Symbol(variables[1])
        elif len(variables) == 1:
            return sp.Symbol(variables[0])
        else:
            # If no variables found, try to create a simple expression
            # Look for common basketball terms in the original description
            if "efficiency" in expr_str.lower():
                return sp.Symbol("PER")  # Player Efficiency Rating
            elif "shooting" in expr_str.lower():
                return sp.Symbol("FG%")  # Field Goal Percentage
            elif "usage" in expr_str.lower():
                return sp.Symbol("USG%")  # Usage Rate
            else:
                return sp.Symbol("x")  # Default variable

    def _validate_formula(self, expr: sp.Expr, variables: List[str]) -> Dict[str, Any]:
        """Validate the parsed formula."""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "complexity": self._calculate_complexity(expr),
            "variable_count": len(variables),
        }

        # Check if expression is valid
        try:
            # Try to evaluate with dummy values
            dummy_values = {var: 1 for var in variables}
            expr.subs(dummy_values)
        except Exception as e:
            validation["is_valid"] = False
            validation["errors"].append(f"Formula evaluation error: {e}")

        # Check for common issues
        if len(variables) == 0:
            validation["warnings"].append("No variables detected in formula")

        if validation["complexity"] > 10:
            validation["warnings"].append("Formula is very complex")

        return validation

    def _calculate_complexity(self, expr: sp.Expr) -> int:
        """Calculate the complexity of the expression."""
        if isinstance(expr, (sp.Add, sp.Mul)):
            return len(expr.args)
        elif isinstance(expr, sp.Pow):
            return 2
        else:
            return 1


@log_operation("nl_to_formula_parse")
def parse_natural_language_formula(
    description: str, context: Optional[str] = None, validate_formula: bool = True
) -> Dict[str, Any]:
    """
    Parse a natural language description into a mathematical formula.

    Args:
        description: Natural language description of the formula
        context: Optional context (e.g., 'basketball', 'player_stats')
        validate_formula: Whether to validate the parsed formula

    Returns:
        Dictionary with parsed formula and metadata
    """
    logger.info(f"Parsing natural language formula: '{description}'")

    parser = NaturalLanguageFormulaParser()

    try:
        result = parser.parse_natural_language_formula(description)

        # Add context information
        if context:
            result["context"] = context

        # Add validation if requested
        if validate_formula:
            result["validation"] = parser._validate_formula(
                parse_expr(result["formula_string"]), result["variables"]
            )

        logger.info(f"Successfully parsed formula: {result['formula_string']}")
        return result

    except Exception as e:
        logger.error(f"Failed to parse natural language formula: {e}")
        raise ToolError(f"Failed to parse formula: {e}")


@log_operation("nl_to_formula_suggest")
def suggest_formula_from_description(
    description: str, context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Suggest a formula based on natural language description.

    Args:
        description: Natural language description
        context: Optional context for suggestions

    Returns:
        Dictionary with suggested formulas and explanations
    """
    logger.info(f"Suggesting formula for: '{description}'")

    suggestions = []

    # Common sports analytics formulas
    sports_formulas = {
        "player efficiency rating": {
            "formula": "((PTS + REB + AST + STL + BLK - (FGA - FGM) - (FTA - FTM) - TOV) / MP) * 100",
            "description": "Player Efficiency Rating - comprehensive player performance metric",
            "variables": [
                "PTS",
                "REB",
                "AST",
                "STL",
                "BLK",
                "FGA",
                "FGM",
                "FTA",
                "FTM",
                "TOV",
                "MP",
            ],
        },
        "true shooting percentage": {
            "formula": "PTS / (2 * (FGA + 0.44 * FTA))",
            "description": "True Shooting Percentage - shooting efficiency including 3-pointers and free throws",
            "variables": ["PTS", "FGA", "FTA"],
        },
        "usage rate": {
            "formula": "((FGA + 0.44 * FTA + TOV) * (Team_MP / 5)) / (MP * (Team_FGA + 0.44 * Team_FTA + Team_TOV)) * 100",
            "description": "Usage Rate - percentage of team plays used by player",
            "variables": [
                "FGA",
                "FTA",
                "TOV",
                "Team_MP",
                "MP",
                "Team_FGA",
                "Team_FTA",
                "Team_TOV",
            ],
        },
        "win shares": {
            "formula": "((PTS - League_Avg_PTS) + (REB - League_Avg_REB) + (AST - League_Avg_AST)) / 30",
            "description": "Win Shares - player contribution to team wins",
            "variables": [
                "PTS",
                "REB",
                "AST",
                "League_Avg_PTS",
                "League_Avg_REB",
                "League_Avg_AST",
            ],
        },
        "field goal percentage": {
            "formula": "FGM / FGA",
            "description": "Field Goal Percentage - basic shooting efficiency",
            "variables": ["FGM", "FGA"],
        },
        "assist to turnover ratio": {
            "formula": "AST / TOV",
            "description": "Assist to Turnover Ratio - ball handling efficiency",
            "variables": ["AST", "TOV"],
        },
    }

    # Find matching formulas
    description_lower = description.lower()
    for formula_name, formula_info in sports_formulas.items():
        if any(keyword in description_lower for keyword in formula_name.split()):
            suggestions.append(
                {
                    "name": formula_name,
                    "formula": formula_info["formula"],
                    "description": formula_info["description"],
                    "variables": formula_info["variables"],
                    "confidence": 0.8,
                }
            )

    # If no specific matches, provide general suggestions
    if not suggestions:
        suggestions.append(
            {
                "name": "basic_efficiency",
                "formula": "PTS / MP",
                "description": "Points per minute - basic scoring efficiency",
                "variables": ["PTS", "MP"],
                "confidence": 0.5,
            }
        )

    return {
        "description": description,
        "suggestions": suggestions,
        "context": context,
        "status": "success",
    }


@log_operation("nl_to_formula_validate")
def validate_natural_language_formula(
    description: str, expected_formula: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate a natural language formula description.

    Args:
        description: Natural language description
        expected_formula: Optional expected formula for comparison

    Returns:
        Dictionary with validation results
    """
    logger.info(f"Validating natural language formula: '{description}'")

    try:
        # Parse the formula
        parsed_result = parse_natural_language_formula(description)

        validation = {
            "description": description,
            "parsed_formula": parsed_result["formula_string"],
            "is_valid": parsed_result["validation"]["is_valid"],
            "errors": parsed_result["validation"]["errors"],
            "warnings": parsed_result["validation"]["warnings"],
            "complexity": parsed_result["validation"]["complexity"],
            "variables": parsed_result["variables"],
        }

        # Compare with expected formula if provided
        if expected_formula:
            try:
                parsed_expected = parse_expr(expected_formula)
                parsed_actual = parse_expr(parsed_result["formula_string"])

                # Check if formulas are equivalent
                validation["matches_expected"] = parsed_expected.equals(parsed_actual)
                validation["expected_formula"] = expected_formula
            except Exception as e:
                validation["comparison_error"] = str(e)

        return validation

    except Exception as e:
        logger.error(f"Failed to validate natural language formula: {e}")
        return {
            "description": description,
            "is_valid": False,
            "errors": [str(e)],
            "status": "error",
        }
