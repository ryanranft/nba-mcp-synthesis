"""
Formula Context Intelligence System

This module provides intelligent formula recognition, analysis, and tool suggestions
for the NBA MCP server's algebraic equation manipulation capabilities.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class FormulaType(Enum):
    """Types of sports analytics formulas"""

    EFFICIENCY = "efficiency"  # TS%, eFG%, etc.
    RATE = "rate"  # PER, Usage Rate, etc.
    COMPOSITE = "composite"  # Win Shares, BPM, etc.
    DIFFERENTIAL = "differential"  # Plus/Minus, Net Rating, etc.
    PERCENTAGE = "percentage"  # Shooting percentages, etc.
    COUNT = "count"  # Raw statistics
    ADVANCED = "advanced"  # Complex metrics like VORP, PIE


class ToolSuggestion(Enum):
    """Suggested algebraic tools for different formula types"""

    SOLVE = "algebra_solve_equation"
    SIMPLIFY = "algebra_simplify_expression"
    DIFFERENTIATE = "algebra_differentiate"
    INTEGRATE = "algebra_integrate"
    RENDER_LATEX = "algebra_render_latex"
    MATRIX_OPS = "algebra_matrix_operations"
    SOLVE_SYSTEM = "algebra_solve_system"
    SPORTS_FORMULA = "algebra_sports_formula"


@dataclass
class FormulaAnalysis:
    """Analysis result for a formula"""

    formula_type: FormulaType
    suggested_tools: List[ToolSuggestion]
    mapped_variables: Dict[str, str]
    unit_consistency: bool
    complexity_score: float
    confidence: float
    insights: List[str]


class FormulaIntelligence:
    """Intelligent formula recognition and analysis system"""

    def __init__(self):
        """Initialize the formula intelligence system"""
        self.formula_patterns = self._build_formula_patterns()
        self.variable_mappings = self._build_variable_mappings()
        self.tool_mappings = self._build_tool_mappings()

    def _build_formula_patterns(self) -> Dict[FormulaType, List[str]]:
        """Build regex patterns for different formula types"""
        return {
            FormulaType.EFFICIENCY: [
                r"TS%|True Shooting|eFG%|Effective Field Goal",
                r"PTS\s*/\s*\(.*FGA.*FTA.*\)",
                r"\(FGM.*3PM.*\)\s*/\s*FGA",
            ],
            FormulaType.RATE: [
                r"PER|Player Efficiency|Usage Rate|USG%",
                r"\(.*\)\s*/\s*MP",
                r"per\s+\d+\s+minutes?",
            ],
            FormulaType.COMPOSITE: [
                r"Win Shares|BPM|Box Plus|VORP",
                r"Game Score|PIE|Player Impact",
                r"comprehensive.*metric",
            ],
            FormulaType.DIFFERENTIAL: [
                r"Plus/Minus|\+/-|Net Rating",
                r"ORtg.*DRtg|Offensive.*Defensive",
                r"differential|difference",
            ],
            FormulaType.PERCENTAGE: [
                r"FG%|3P%|FT%|Field Goal.*%",
                r"FGM\s*/\s*FGA",
                r"percentage.*shooting",
            ],
            FormulaType.COUNT: [
                r"PTS|Points|REB|Rebounds|AST|Assists",
                r"STL|Steals|BLK|Blocks|TOV|Turnovers",
                r"raw.*statistics?",
            ],
            FormulaType.ADVANCED: [
                r"VORP|PIE|BPM|Win Shares",
                r"advanced.*metric|complex.*formula",
                r"multiple.*components",
            ],
        }

    def _build_variable_mappings(self) -> Dict[str, str]:
        """Build mappings from book variables to standard notation"""
        return {
            # Field Goals
            "FGM": "FGM",
            "Field Goals Made": "FGM",
            "FG Made": "FGM",
            "FGA": "FGA",
            "Field Goals Attempted": "FGA",
            "FG Attempted": "FGA",
            "FG%": "FG%",
            "Field Goal %": "FG%",
            # 3-Pointers
            "3PM": "3PM",
            "3-Pointers Made": "3PM",
            "3P Made": "3PM",
            "3PA": "3PA",
            "3-Pointers Attempted": "3PA",
            "3P Attempted": "3PA",
            "3P%": "3P%",
            "3-Point %": "3P%",
            # Free Throws
            "FTM": "FTM",
            "Free Throws Made": "FTM",
            "FT Made": "FTM",
            "FTA": "FTA",
            "Free Throws Attempted": "FTA",
            "FT Attempted": "FTA",
            "FT%": "FT%",
            "Free Throw %": "FT%",
            # Other Stats
            "PTS": "PTS",
            "Points": "PTS",
            "Points Scored": "PTS",
            "REB": "REB",
            "Rebounds": "REB",
            "Total Rebounds": "REB",
            "OREB": "OREB",
            "Offensive Rebounds": "OREB",
            "Off Rebounds": "OREB",
            "DREB": "DREB",
            "Defensive Rebounds": "DREB",
            "Def Rebounds": "DREB",
            "AST": "AST",
            "Assists": "AST",
            "STL": "STL",
            "Steals": "STL",
            "BLK": "BLK",
            "Blocks": "BLK",
            "TOV": "TOV",
            "Turnovers": "TOV",
            "PF": "PF",
            "Personal Fouls": "PF",
            "Fouls": "PF",
            "MP": "MP",
            "Minutes": "MP",
            "Minutes Played": "MP",
            # Team Stats
            "TM_": "TM_",
            "Team ": "TM_",
            "OPP_": "OPP_",
            "Opponent ": "OPP_",
            # Advanced Metrics
            "PER": "PER",
            "Player Efficiency Rating": "PER",
            "TS%": "TS%",
            "True Shooting %": "TS%",
            "USG%": "USG%",
            "Usage Rate": "USG%",
            "BPM": "BPM",
            "Box Plus/Minus": "BPM",
            "VORP": "VORP",
            "Value Over Replacement": "VORP",
            "WS": "WS",
            "Win Shares": "WS",
            "PIE": "PIE",
            "Player Impact Estimate": "PIE",
        }

    def _build_tool_mappings(self) -> Dict[FormulaType, List[ToolSuggestion]]:
        """Map formula types to suggested tools"""
        return {
            FormulaType.EFFICIENCY: [
                ToolSuggestion.SIMPLIFY,
                ToolSuggestion.SPORTS_FORMULA,
                ToolSuggestion.RENDER_LATEX,
            ],
            FormulaType.RATE: [
                ToolSuggestion.SOLVE,
                ToolSuggestion.DIFFERENTIATE,
                ToolSuggestion.SPORTS_FORMULA,
            ],
            FormulaType.COMPOSITE: [
                ToolSuggestion.SIMPLIFY,
                ToolSuggestion.MATRIX_OPS,
                ToolSuggestion.SPORTS_FORMULA,
            ],
            FormulaType.DIFFERENTIAL: [
                ToolSuggestion.SOLVE_SYSTEM,
                ToolSuggestion.MATRIX_OPS,
                ToolSuggestion.RENDER_LATEX,
            ],
            FormulaType.PERCENTAGE: [
                ToolSuggestion.SIMPLIFY,
                ToolSuggestion.SPORTS_FORMULA,
                ToolSuggestion.RENDER_LATEX,
            ],
            FormulaType.COUNT: [ToolSuggestion.SIMPLIFY, ToolSuggestion.RENDER_LATEX],
            FormulaType.ADVANCED: [
                ToolSuggestion.SIMPLIFY,
                ToolSuggestion.DIFFERENTIATE,
                ToolSuggestion.INTEGRATE,
                ToolSuggestion.MATRIX_OPS,
                ToolSuggestion.SPORTS_FORMULA,
            ],
        }

    def identify_formula_type(self, formula_str: str) -> Tuple[FormulaType, float]:
        """
        Identify the type of a sports analytics formula.

        Args:
            formula_str: The formula string to analyze

        Returns:
            Tuple of (formula_type, confidence_score)
        """
        formula_lower = formula_str.lower()
        scores = {}

        for formula_type, patterns in self.formula_patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, formula_str, re.IGNORECASE):
                    score += 1.0
                if re.search(pattern, formula_lower):
                    score += 0.5

            # Normalize score
            scores[formula_type] = score / len(patterns)

        # Find best match
        best_type = max(scores.items(), key=lambda x: x[1])

        # If no clear match, try to infer from structure
        if best_type[1] < 0.3:
            best_type = self._infer_from_structure(formula_str)

        return best_type

    def _infer_from_structure(self, formula_str: str) -> Tuple[FormulaType, float]:
        """Infer formula type from mathematical structure"""
        # Check for percentage patterns
        if "/" in formula_str and "%" in formula_str:
            return FormulaType.PERCENTAGE, 0.7

        # Check for rate patterns (division by time/possessions)
        if re.search(r"/\s*(MP|MIN|POSS|GAMES?)", formula_str, re.IGNORECASE):
            return FormulaType.RATE, 0.6

        # Check for complex formulas (many operations)
        if len(re.findall(r"[+\-*/]", formula_str)) > 5:
            return FormulaType.COMPOSITE, 0.5

        # Check for differential patterns
        if re.search(r"[-]\s*|difference|differential", formula_str, re.IGNORECASE):
            return FormulaType.DIFFERENTIAL, 0.6

        # Default to efficiency
        return FormulaType.EFFICIENCY, 0.4

    def suggest_tool(self, formula_str: str) -> List[ToolSuggestion]:
        """
        Suggest which algebraic tools to use for a formula.

        Args:
            formula_str: The formula string

        Returns:
            List of suggested tools in order of priority
        """
        formula_type, confidence = self.identify_formula_type(formula_str)

        # Get base suggestions
        suggestions = self.tool_mappings.get(formula_type, [])

        # Add context-specific suggestions
        if "solve" in formula_str.lower() or "=" in formula_str:
            if ToolSuggestion.SOLVE not in suggestions:
                suggestions.insert(0, ToolSuggestion.SOLVE)

        if "simplify" in formula_str.lower() or len(formula_str) > 100:
            if ToolSuggestion.SIMPLIFY not in suggestions:
                suggestions.insert(0, ToolSuggestion.SIMPLIFY)

        if (
            "derivative" in formula_str.lower()
            or "rate of change" in formula_str.lower()
        ):
            if ToolSuggestion.DIFFERENTIATE not in suggestions:
                suggestions.insert(0, ToolSuggestion.DIFFERENTIATE)

        return suggestions

    def map_variables(self, formula_str: str) -> Dict[str, str]:
        """
        Map book variables to standard notation.

        Args:
            formula_str: The formula string

        Returns:
            Dictionary mapping original variables to standard notation
        """
        mappings = {}

        # Extract variables from formula
        variables = re.findall(r"\b[A-Z][A-Z0-9_]*\b", formula_str)

        for var in variables:
            # Direct mapping
            if var in self.variable_mappings:
                mappings[var] = self.variable_mappings[var]
            else:
                # Try partial matching
                for book_var, std_var in self.variable_mappings.items():
                    if var in book_var or book_var in var:
                        mappings[var] = std_var
                        break
                else:
                    # Keep original if no mapping found
                    mappings[var] = var

        return mappings

    def validate_units(self, formula: Dict[str, Any]) -> bool:
        """
        Ensure consistent units in a formula.

        Args:
            formula: Formula dictionary with variables and values

        Returns:
            True if units are consistent
        """
        # Check for common unit inconsistencies
        variables = formula.get("variables", {})

        # Check percentage vs decimal
        percentage_vars = ["FG%", "3P%", "FT%", "TS%", "USG%"]
        for var in percentage_vars:
            if var in variables:
                value = variables[var]
                if isinstance(value, (int, float)):
                    if value > 1.0:
                        logger.warning(
                            f"{var} value {value} appears to be percentage, should be decimal"
                        )
                        return False

        # Check minutes vs seconds
        if "MP" in variables:
            value = variables["MP"]
            if isinstance(value, (int, float)) and value > 48:
                logger.warning(f"MP value {value} seems too high for minutes played")
                return False

        # Check for negative values where they shouldn't be
        count_vars = [
            "FGM",
            "FGA",
            "FTM",
            "FTA",
            "3PM",
            "3PA",
            "PTS",
            "REB",
            "AST",
            "STL",
            "BLK",
        ]
        for var in count_vars:
            if var in variables:
                value = variables[var]
                if isinstance(value, (int, float)) and value < 0:
                    logger.warning(f"{var} value {value} is negative")
                    return False

        return True

    def analyze_formula(
        self, formula_str: str, variables: Optional[Dict[str, Any]] = None
    ) -> FormulaAnalysis:
        """
        Perform comprehensive analysis of a formula.

        Args:
            formula_str: The formula string
            variables: Optional variables dictionary for validation

        Returns:
            Complete formula analysis
        """
        # Identify formula type
        formula_type, confidence = self.identify_formula_type(formula_str)

        # Suggest tools
        suggested_tools = self.suggest_tool(formula_str)

        # Map variables
        mapped_variables = self.map_variables(formula_str)

        # Validate units if variables provided
        unit_consistency = True
        if variables:
            unit_consistency = self.validate_units({"variables": variables})

        # Calculate complexity score
        complexity_score = self._calculate_complexity(formula_str)

        # Generate insights
        insights = self._generate_insights(formula_str, formula_type, complexity_score)

        return FormulaAnalysis(
            formula_type=formula_type,
            suggested_tools=suggested_tools,
            mapped_variables=mapped_variables,
            unit_consistency=unit_consistency,
            complexity_score=complexity_score,
            confidence=confidence,
            insights=insights,
        )

    def _calculate_complexity(self, formula_str: str) -> float:
        """Calculate complexity score for a formula (0.0 to 1.0)"""
        score = 0.0

        # Length factor
        score += min(len(formula_str) / 200, 0.3)

        # Operation count
        operations = len(re.findall(r"[+\-*/]", formula_str))
        score += min(operations / 10, 0.3)

        # Variable count
        variables = len(re.findall(r"\b[A-Z][A-Z0-9_]*\b", formula_str))
        score += min(variables / 15, 0.2)

        # Parentheses depth
        max_depth = self._max_parentheses_depth(formula_str)
        score += min(max_depth / 5, 0.2)

        return min(score, 1.0)

    def _max_parentheses_depth(self, formula_str: str) -> int:
        """Calculate maximum parentheses depth"""
        max_depth = 0
        current_depth = 0

        for char in formula_str:
            if char == "(":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ")":
                current_depth -= 1

        return max_depth

    def _generate_insights(
        self, formula_str: str, formula_type: FormulaType, complexity_score: float
    ) -> List[str]:
        """Generate insights about the formula"""
        insights = []

        # Type-specific insights
        if formula_type == FormulaType.EFFICIENCY:
            insights.append(
                "This is an efficiency metric that measures shooting effectiveness"
            )
            insights.append(
                "Consider using True Shooting % for comprehensive shooting analysis"
            )

        elif formula_type == FormulaType.RATE:
            insights.append("This is a rate statistic that normalizes for playing time")
            insights.append("Use for comparing players with different minutes played")

        elif formula_type == FormulaType.COMPOSITE:
            insights.append("This is a composite metric combining multiple statistics")
            insights.append("Provides comprehensive player evaluation")

        elif formula_type == FormulaType.DIFFERENTIAL:
            insights.append(
                "This measures the difference between offensive and defensive performance"
            )
            insights.append("Useful for evaluating overall team impact")

        # Complexity insights
        if complexity_score > 0.7:
            insights.append(
                "This is a complex formula - consider breaking it into steps"
            )
        elif complexity_score < 0.3:
            insights.append(
                "This is a simple formula - easy to understand and calculate"
            )

        # Variable insights
        if "MP" in formula_str:
            insights.append(
                "Formula includes minutes played - useful for rate calculations"
            )

        if "3PM" in formula_str or "3PA" in formula_str:
            insights.append(
                "Formula accounts for 3-pointers - modern basketball consideration"
            )

        if "TOV" in formula_str:
            insights.append(
                "Formula includes turnovers - important for efficiency analysis"
            )

        return insights

    def get_formula_recommendations(
        self, formula_str: str, context: str = ""
    ) -> Dict[str, Any]:
        """
        Get comprehensive recommendations for using a formula.

        Args:
            formula_str: The formula string
            context: Optional context (e.g., "player analysis", "team comparison")

        Returns:
            Dictionary with recommendations
        """
        analysis = self.analyze_formula(formula_str)

        recommendations = {
            "formula_type": analysis.formula_type.value,
            "suggested_tools": [tool.value for tool in analysis.suggested_tools],
            "mapped_variables": analysis.mapped_variables,
            "unit_consistency": analysis.unit_consistency,
            "complexity_score": analysis.complexity_score,
            "confidence": analysis.confidence,
            "insights": analysis.insights,
            "recommendations": [],
        }

        # Context-specific recommendations
        if context.lower() == "player analysis":
            recommendations["recommendations"].extend(
                [
                    "Use this formula to compare players across different teams",
                    "Consider normalizing for pace and team context",
                    "Validate results against known player rankings",
                ]
            )

        elif context.lower() == "team comparison":
            recommendations["recommendations"].extend(
                [
                    "Apply formula to team totals for comparison",
                    "Consider opponent strength adjustments",
                    "Use for identifying team strengths and weaknesses",
                ]
            )

        elif context.lower() == "optimization":
            recommendations["recommendations"].extend(
                [
                    "Use differentiation to find optimal values",
                    "Consider constraint optimization",
                    "Test sensitivity to parameter changes",
                ]
            )

        # General recommendations based on analysis
        if analysis.complexity_score > 0.7:
            recommendations["recommendations"].append(
                "Break complex formula into smaller components for analysis"
            )

        if not analysis.unit_consistency:
            recommendations["recommendations"].append(
                "Check and standardize units before calculation"
            )

        if analysis.confidence < 0.5:
            recommendations["recommendations"].append(
                "Verify formula accuracy with multiple sources"
            )

        return recommendations


# Convenience functions for easy access
def identify_formula_type(formula_str: str) -> Tuple[FormulaType, float]:
    """Convenience function to identify formula type"""
    intelligence = FormulaIntelligence()
    return intelligence.identify_formula_type(formula_str)


def suggest_tools(formula_str: str) -> List[ToolSuggestion]:
    """Convenience function to suggest tools"""
    intelligence = FormulaIntelligence()
    return intelligence.suggest_tool(formula_str)


def map_variables(formula_str: str) -> Dict[str, str]:
    """Convenience function to map variables"""
    intelligence = FormulaIntelligence()
    return intelligence.map_variables(formula_str)


def analyze_formula(
    formula_str: str, variables: Optional[Dict[str, Any]] = None
) -> FormulaAnalysis:
    """Convenience function for complete analysis"""
    intelligence = FormulaIntelligence()
    return intelligence.analyze_formula(formula_str, variables)
