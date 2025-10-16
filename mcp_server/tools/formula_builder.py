"""
Interactive Formula Builder Module for NBA MCP Server

This module provides an interactive interface for constructing, validating,
and manipulating mathematical formulas with real-time feedback and suggestions.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from sympy import latex, simplify, expand, factor

# Import other modules
from .formula_intelligence import FormulaIntelligence

logger = logging.getLogger(__name__)

class FormulaComponentType(Enum):
    """Types of formula components"""
    VARIABLE = "variable"
    CONSTANT = "constant"
    OPERATOR = "operator"
    FUNCTION = "function"
    PARENTHESIS = "parenthesis"
    FRACTION = "fraction"
    POWER = "power"
    SUBSCRIPT = "subscript"

class ValidationLevel(Enum):
    """Validation levels for formulas"""
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    SPORTS_CONTEXT = "sports_context"
    UNITS = "units"

@dataclass
class FormulaComponent:
    """Represents a component in a formula"""
    id: str
    type: FormulaComponentType
    value: str
    position: int
    metadata: Dict[str, Any] = None

@dataclass
class FormulaTemplate:
    """Represents a formula template"""
    name: str
    description: str
    template: str
    variables: List[str]
    category: str
    example_values: Dict[str, float] = None

@dataclass
class FormulaValidation:
    """Represents validation results for a formula"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    confidence: float

# Alias for MCP tool compatibility
ValidationResult = FormulaValidation

class InteractiveFormulaBuilder:
    """
    Interactive formula builder with real-time validation and suggestions.

    Provides a visual interface for constructing mathematical formulas
    with drag-and-drop components, real-time validation, and intelligent
    suggestions based on sports analytics context.
    """

    def __init__(self):
        """Initialize the formula builder"""
        self.sports_variables = {
            'PTS': {'description': 'Points', 'range': (0, 150), 'unit': 'points'},
            'FGM': {'description': 'Field Goals Made', 'range': (0, 60), 'unit': 'shots'},
            'FGA': {'description': 'Field Goals Attempted', 'range': (0, 100), 'unit': 'shots'},
            '3PM': {'description': '3-Pointers Made', 'range': (0, 30), 'unit': 'shots'},
            'FTM': {'description': 'Free Throws Made', 'range': (0, 40), 'unit': 'shots'},
            'FTA': {'description': 'Free Throws Attempted', 'range': (0, 50), 'unit': 'shots'},
            'OREB': {'description': 'Offensive Rebounds', 'range': (0, 30), 'unit': 'rebounds'},
            'DREB': {'description': 'Defensive Rebounds', 'range': (0, 40), 'unit': 'rebounds'},
            'AST': {'description': 'Assists', 'range': (0, 30), 'unit': 'assists'},
            'STL': {'description': 'Steals', 'range': (0, 15), 'unit': 'steals'},
            'BLK': {'description': 'Blocks', 'range': (0, 15), 'unit': 'blocks'},
            'TOV': {'description': 'Turnovers', 'range': (0, 20), 'unit': 'turnovers'},
            'PF': {'description': 'Personal Fouls', 'range': (0, 6), 'unit': 'fouls'},
            'MP': {'description': 'Minutes Played', 'range': (0, 60), 'unit': 'minutes'},
            'PER': {'description': 'Player Efficiency Rating', 'range': (0, 50), 'unit': 'rating'},
            'TS': {'description': 'True Shooting', 'range': (0, 1), 'unit': 'percentage'},
            'USG': {'description': 'Usage Rate', 'range': (0, 100), 'unit': 'percentage'},
            'ORtg': {'description': 'Offensive Rating', 'range': (80, 130), 'unit': 'rating'},
            'DRtg': {'description': 'Defensive Rating', 'range': (80, 130), 'unit': 'rating'},
            'PACE': {'description': 'Pace', 'range': (80, 120), 'unit': 'possessions'},
            'BPM': {'description': 'Box Plus/Minus', 'range': (-20, 20), 'unit': 'rating'},
            'VORP': {'description': 'Value Over Replacement Player', 'range': (-5, 10), 'unit': 'rating'},
            'WS': {'description': 'Win Shares', 'range': (-5, 25), 'unit': 'shares'},
        }

        self.formula_templates = self._initialize_templates()
        self.operators = ['+', '-', '*', '/', '^', '**', '=', '>', '<', '>=', '<=']
        self.functions = ['sqrt', 'log', 'ln', 'exp', 'sin', 'cos', 'tan', 'abs', 'max', 'min']

    def _initialize_templates(self) -> List[FormulaTemplate]:
        """Initialize common sports analytics formula templates"""
        templates = [
            FormulaTemplate(
                name="True Shooting Percentage",
                description="Measures shooting efficiency accounting for 3-pointers and free throws",
                template="PTS / (2 * (FGA + 0.44 * FTA))",
                variables=["PTS", "FGA", "FTA"],
                category="shooting",
                example_values={"PTS": 25, "FGA": 15, "FTA": 5}
            ),
            FormulaTemplate(
                name="Player Efficiency Rating",
                description="All-in-one basketball rating",
                template="(FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
                variables=["FGM", "STL", "3PM", "FTM", "BLK", "OREB", "AST", "DREB", "PF", "FTA", "FGA", "TOV", "MP"],
                category="advanced",
                example_values={"FGM": 8, "STL": 2, "3PM": 2, "FTM": 5, "BLK": 1, "OREB": 1, "AST": 8, "DREB": 7, "PF": 2, "FTA": 6, "FGA": 18, "TOV": 3, "MP": 38}
            ),
            FormulaTemplate(
                name="Usage Rate",
                description="Percentage of team plays used by player",
                template="((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
                variables=["FGA", "FTA", "TOV", "TM_MP", "MP", "TM_FGA", "TM_FTA", "TM_TOV"],
                category="advanced",
                example_values={"FGA": 18, "FTA": 6, "TOV": 3, "TM_MP": 240, "MP": 38, "TM_FGA": 90, "TM_FTA": 25, "TM_TOV": 12}
            ),
            FormulaTemplate(
                name="Net Rating",
                description="Difference between offensive and defensive rating",
                template="ORtg - DRtg",
                variables=["ORtg", "DRtg"],
                category="team",
                example_values={"ORtg": 115, "DRtg": 108}
            ),
            FormulaTemplate(
                name="Effective Field Goal Percentage",
                description="Field goal percentage adjusted for 3-pointers",
                template="(FGM + 0.5 * 3PM) / FGA",
                variables=["FGM", "3PM", "FGA"],
                category="shooting",
                example_values={"FGM": 8, "3PM": 2, "FGA": 18}
            ),
            FormulaTemplate(
                name="Assist Percentage",
                description="Percentage of teammate field goals assisted",
                template="(AST * (TM_MP / 5)) / (MP * (TM_FGM - FGM)) * 100",
                variables=["AST", "TM_MP", "MP", "TM_FGM", "FGM"],
                category="advanced",
                example_values={"AST": 8, "TM_MP": 240, "MP": 38, "TM_FGM": 35, "FGM": 8}
            ),
            FormulaTemplate(
                name="Rebound Percentage",
                description="Percentage of available rebounds grabbed",
                template="(REB * (TM_MP / 5)) / (MP * (TM_REB + OPP_REB)) * 100",
                variables=["REB", "TM_MP", "MP", "TM_REB", "OPP_REB"],
                category="advanced",
                example_values={"REB": 8, "TM_MP": 240, "MP": 38, "TM_REB": 45, "OPP_REB": 42}
            ),
            FormulaTemplate(
                name="Steal Percentage",
                description="Steals per 100 opponent possessions",
                template="(STL * (TM_MP / 5)) / (MP * OPP_POSS) * 100",
                variables=["STL", "TM_MP", "MP", "OPP_POSS"],
                category="defensive",
                example_values={"STL": 2, "TM_MP": 240, "MP": 38, "OPP_POSS": 100}
            ),
            FormulaTemplate(
                name="Block Percentage",
                description="Blocks per 100 opponent 2-point attempts",
                template="(BLK * (TM_MP / 5)) / (MP * OPP_2PA) * 100",
                variables=["BLK", "TM_MP", "MP", "OPP_2PA"],
                category="defensive",
                example_values={"BLK": 1, "TM_MP": 240, "MP": 38, "OPP_2PA": 50}
            ),
            FormulaTemplate(
                name="Turnover Percentage",
                description="Turnovers per 100 plays",
                template="(TOV * (TM_MP / 5)) / (MP * (FGA + 0.44 * FTA + TOV)) * 100",
                variables=["TOV", "TM_MP", "MP", "FGA", "FTA"],
                category="advanced",
                example_values={"TOV": 3, "TM_MP": 240, "MP": 38, "FGA": 18, "FTA": 6}
            )
        ]
        return templates

    def parse_formula(self, formula_str: str) -> List[FormulaComponent]:
        """
        Parse a formula string into components.

        Args:
            formula_str: Formula string to parse

        Returns:
            List of FormulaComponent objects
        """
        components = []
        position = 0

        # Tokenize the formula
        tokens = self._tokenize_formula(formula_str)

        for token in tokens:
            component_type = self._classify_token(token)
            component = FormulaComponent(
                id=f"comp_{position}",
                type=component_type,
                value=token,
                position=position,
                metadata=self._get_token_metadata(token, component_type)
            )
            components.append(component)
            position += 1

        return components

    def validate_formula(self, formula_str: str, validation_level: ValidationLevel = ValidationLevel.SEMANTIC) -> ValidationResult:
        """
        Validate a formula at the specified level.

        Args:
            formula_str: Formula string to validate
            validation_level: Level of validation to perform

        Returns:
            FormulaValidation object with results
        """
        errors = []
        warnings = []
        suggestions = []
        confidence = 1.0

        # Syntax validation
        if validation_level in [ValidationLevel.SYNTAX, ValidationLevel.SEMANTIC, ValidationLevel.SPORTS_CONTEXT, ValidationLevel.UNITS]:
            syntax_valid, syntax_errors = self._validate_syntax(formula_str)
            if not syntax_valid:
                errors.extend(syntax_errors)
                confidence -= 0.3
            else:
                suggestions.append("Formula syntax is valid")

        # Semantic validation
        if validation_level in [ValidationLevel.SEMANTIC, ValidationLevel.SPORTS_CONTEXT, ValidationLevel.UNITS]:
            semantic_valid, semantic_errors, semantic_warnings = self._validate_semantics(formula_str)
            if not semantic_valid:
                errors.extend(semantic_errors)
                confidence -= 0.2
            warnings.extend(semantic_warnings)

        # Sports context validation
        if validation_level in [ValidationLevel.SPORTS_CONTEXT, ValidationLevel.UNITS]:
            sports_valid, sports_errors, sports_suggestions = self._validate_sports_context(formula_str)
            if not sports_valid:
                errors.extend(sports_errors)
                confidence -= 0.2
            suggestions.extend(sports_suggestions)

        # Units validation
        if validation_level == ValidationLevel.UNITS:
            units_valid, units_errors, units_warnings = self._validate_units(formula_str)
            if not units_valid:
                errors.extend(units_errors)
                confidence -= 0.1
            warnings.extend(units_warnings)

        confidence = max(0.0, confidence)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            confidence=confidence
        )

    def suggest_completion(self, partial_formula: str, context: str = "") -> List[str]:
        """
        Suggest completions for a partial formula.

        Args:
            partial_formula: Partial formula string
            context: Optional context for suggestions

        Returns:
            List of suggested completions
        """
        suggestions = []

        # Analyze the partial formula
        components = self.parse_formula(partial_formula)
        if not components:
            return self._get_initial_suggestions()

        last_component = components[-1]

        # Suggest based on last component type
        if last_component.type == FormulaComponentType.VARIABLE:
            suggestions.extend(self._suggest_operators())
            suggestions.extend(self._suggest_functions())
        elif last_component.type == FormulaComponentType.OPERATOR:
            suggestions.extend(self._suggest_variables())
            suggestions.extend(self._suggest_constants())
        elif last_component.type == FormulaComponentType.FUNCTION:
            suggestions.append("(")
        elif last_component.value == "(":
            suggestions.extend(self._suggest_variables())
            suggestions.extend(self._suggest_constants())
        elif last_component.value == ")":
            suggestions.extend(self._suggest_operators())
        else:
            suggestions.extend(self._suggest_variables())
            suggestions.extend(self._suggest_operators())

        # Add template-based suggestions
        template_suggestions = self._suggest_from_templates(partial_formula, context)
        suggestions.extend(template_suggestions)

        return list(set(suggestions))  # Remove duplicates

    def get_formula_preview(self, formula_str: str, variable_values: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Get a preview of the formula with LaTeX rendering and calculation.

        Args:
            formula_str: Formula string
            variable_values: Optional values for variables

        Returns:
            Dictionary with preview information
        """
        preview = {
            "formula": formula_str,
            "latex": None,
            "simplified": None,
            "calculated_value": None,
            "variables": [],
            "error": None
        }

        try:
            # Extract variables
            variables = self._extract_variables(formula_str)
            preview["variables"] = variables

            # Generate LaTeX
            try:
                expr = parse_expr(formula_str)
                preview["latex"] = latex(expr)
                preview["simplified"] = latex(simplify(expr))
            except Exception as e:
                preview["error"] = f"LaTeX generation failed: {str(e)}"

            # Calculate value if variables provided
            if variable_values:
                try:
                    calculated = self._calculate_formula(formula_str, variable_values)
                    preview["calculated_value"] = calculated
                except Exception as e:
                    preview["error"] = f"Calculation failed: {str(e)}"

        except Exception as e:
            preview["error"] = f"Preview generation failed: {str(e)}"

        return preview

    def get_available_templates(self, category: str = None) -> List[FormulaTemplate]:
        """
        Get available formula templates, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of FormulaTemplate objects
        """
        if category:
            return [template for template in self.formula_templates if template.category == category]
        return self.formula_templates

    def create_formula_from_template(self, template_name: str, variable_values: Dict[str, float]) -> Dict[str, Any]:
        """
        Create a formula from a template with provided variable values.

        Args:
            template_name: Name of the template to use
            variable_values: Values for template variables

        Returns:
            Dictionary with formula information
        """
        template = next((t for t in self.formula_templates if t.name == template_name), None)
        if not template:
            return {"error": f"Template '{template_name}' not found"}

        # Validate that all required variables are provided
        missing_vars = set(template.variables) - set(variable_values.keys())
        if missing_vars:
            return {"error": f"Missing variables: {', '.join(missing_vars)}"}

        # Substitute values into template
        formula_str = template.template
        for var, value in variable_values.items():
            formula_str = formula_str.replace(var, str(value))

        # Calculate result
        try:
            result = self._calculate_formula(formula_str, variable_values)
        except Exception as e:
            return {"error": f"Calculation failed: {str(e)}"}

        return {
            "template_name": template_name,
            "formula": template.template,
            "substituted_formula": formula_str,
            "result": result,
            "variables_used": variable_values,
            "description": template.description
        }

    def export_formula(self, formula_str: str, format_type: str = "latex") -> str:
        """
        Export formula in specified format.

        Args:
            formula_str: Formula string to export
            format_type: Export format (latex, python, sympy, json)

        Returns:
            Exported formula string
        """
        try:
            expr = parse_expr(formula_str)

            if format_type == "latex":
                return latex(expr)
            elif format_type == "python":
                return str(expr)
            elif format_type == "sympy":
                return str(expr)
            elif format_type == "json":
                return json.dumps({
                    "formula": formula_str,
                    "latex": latex(expr),
                    "variables": self._extract_variables(formula_str),
                    "simplified": str(simplify(expr))
                }, indent=2)
            else:
                return f"Unsupported format: {format_type}"

        except Exception as e:
            return f"Export failed: {str(e)}"

    def _tokenize_formula(self, formula_str: str) -> List[str]:
        """Tokenize formula string into components"""
        # Simple tokenizer - can be enhanced
        tokens = []
        current_token = ""

        for char in formula_str:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif char in self.operators + ['(', ')', '[', ']', '{', '}']:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(char)
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        return tokens

    def _classify_token(self, token: str) -> FormulaComponentType:
        """Classify a token as a component type"""
        if token in self.operators:
            return FormulaComponentType.OPERATOR
        elif token in ['(', ')', '[', ']', '{', '}']:
            return FormulaComponentType.PARENTHESIS
        elif token in self.functions:
            return FormulaComponentType.FUNCTION
        elif token.replace('.', '').replace('-', '').isdigit():
            return FormulaComponentType.CONSTANT
        elif token.upper() in self.sports_variables:
            return FormulaComponentType.VARIABLE
        else:
            return FormulaComponentType.VARIABLE  # Default to variable

    def _get_token_metadata(self, token: str, component_type: FormulaComponentType) -> Dict[str, Any]:
        """Get metadata for a token"""
        metadata = {"token": token, "type": component_type.value}

        if component_type == FormulaComponentType.VARIABLE and token.upper() in self.sports_variables:
            metadata.update(self.sports_variables[token.upper()])

        return metadata

    def _validate_syntax(self, formula_str: str) -> Tuple[bool, List[str]]:
        """Validate formula syntax"""
        errors = []

        # Check for balanced parentheses
        paren_count = 0
        for char in formula_str:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count < 0:
                    errors.append("Unmatched closing parenthesis")
                    break

        if paren_count > 0:
            errors.append("Unmatched opening parenthesis")

        # Check for consecutive operators
        tokens = self._tokenize_formula(formula_str)
        for i in range(len(tokens) - 1):
            if (tokens[i] in self.operators and
                tokens[i+1] in self.operators and
                not (tokens[i] in ['-', '+'] and tokens[i+1] in ['-', '+'])):
                errors.append(f"Consecutive operators: {tokens[i]} {tokens[i+1]}")

        return len(errors) == 0, errors

    def _validate_semantics(self, formula_str: str) -> Tuple[bool, List[str], List[str]]:
        """Validate formula semantics"""
        errors = []
        warnings = []

        try:
            expr = parse_expr(formula_str)
            # Basic semantic checks passed
        except Exception as e:
            errors.append(f"Semantic error: {str(e)}")

        # Check for division by zero potential
        if '/' in formula_str and '0' in formula_str:
            warnings.append("Potential division by zero")

        return len(errors) == 0, errors, warnings

    def _validate_sports_context(self, formula_str: str) -> Tuple[bool, List[str], List[str]]:
        """Validate formula in sports analytics context"""
        errors = []
        suggestions = []

        variables = self._extract_variables(formula_str)
        sports_vars = [var for var in variables if var.upper() in self.sports_variables]

        if not sports_vars:
            suggestions.append("Consider using sports analytics variables (PTS, FGM, FGA, etc.)")

        # Check for common sports formula patterns
        if 'PTS' in variables and 'FGA' in variables and 'FTA' in variables:
            suggestions.append("This looks like a shooting efficiency formula - consider True Shooting Percentage")

        if 'PER' in variables:
            suggestions.append("PER is a complex formula - ensure all components are included")

        return True, errors, suggestions

    def _validate_units(self, formula_str: str) -> Tuple[bool, List[str], List[str]]:
        """Validate formula units"""
        errors = []
        warnings = []

        # Basic unit validation - can be enhanced
        variables = self._extract_variables(formula_str)

        for var in variables:
            if var.upper() in self.sports_variables:
                var_info = self.sports_variables[var.upper()]
                if 'unit' in var_info:
                    warnings.append(f"Variable {var} has unit: {var_info['unit']}")

        return True, errors, warnings

    def _extract_variables(self, formula_str: str) -> List[str]:
        """Extract variables from formula string"""
        variables = []
        tokens = self._tokenize_formula(formula_str)

        for token in tokens:
            if (self._classify_token(token) == FormulaComponentType.VARIABLE and
                token.upper() in self.sports_variables):
                variables.append(token.upper())

        return list(set(variables))

    def _calculate_formula(self, formula_str: str, variable_values: Dict[str, float]) -> float:
        """Calculate formula with given variable values"""
        # Substitute variables with values
        substituted = formula_str
        for var, value in variable_values.items():
            substituted = substituted.replace(var, str(value))

        # Parse and evaluate
        expr = parse_expr(substituted)
        return float(expr.evalf())

    def _get_initial_suggestions(self) -> List[str]:
        """Get initial suggestions for empty formula"""
        return ["PTS", "FGM", "FGA", "PER", "TS", "USG", "ORtg", "DRtg"]

    def _suggest_operators(self) -> List[str]:
        """Suggest operators"""
        return ["+", "-", "*", "/", "=", "^"]

    def _suggest_functions(self) -> List[str]:
        """Suggest functions"""
        return ["sqrt", "log", "abs", "max", "min"]

    def _suggest_variables(self) -> List[str]:
        """Suggest sports variables"""
        return list(self.sports_variables.keys())

    def _suggest_constants(self) -> List[str]:
        """Suggest constants"""
        return ["0", "1", "2", "0.44", "100", "48"]

    def _suggest_from_templates(self, partial_formula: str, context: str) -> List[str]:
        """Suggest completions based on templates"""
        suggestions = []

        # Find templates that match the partial formula
        for template in self.formula_templates:
            if any(var in partial_formula for var in template.variables):
                suggestions.append(f"Template: {template.name}")

        return suggestions
