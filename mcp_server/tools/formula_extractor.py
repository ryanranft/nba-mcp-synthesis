"""
Formula Extraction Module for NBA MCP Server

This module provides automated formula extraction capabilities from PDF documents,
specifically designed for sports analytics books. It can identify mathematical
formulas, convert LaTeX notation, and suggest appropriate algebraic tools.

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import sympy as sp
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import parse_expr

logger = logging.getLogger(__name__)

class FormulaType(Enum):
    """Types of formulas that can be extracted"""
    EFFICIENCY = "efficiency"
    RATE = "rate"
    COUNT = "count"
    COMPOSITE = "composite"
    DIFFERENTIAL = "differential"
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    EQUATION = "equation"
    INEQUALITY = "inequality"
    OTHER = "other"

@dataclass
class ExtractedFormula:
    """Represents an extracted formula with metadata"""
    formula_text: str
    formula_type: FormulaType
    variables: List[str]
    page_number: int
    context: str
    confidence: float
    latex_notation: Optional[str] = None
    sympy_expression: Optional[str] = None
    suggested_tools: List[str] = None

class FormulaExtractor:
    """
    Extracts mathematical formulas from PDF text content.

    This class provides pattern recognition for common formula structures,
    LaTeX extraction, and conversion to SymPy-compatible format.
    """

    def __init__(self):
        """Initialize the formula extractor with pattern definitions"""
        self.formula_patterns = {
            # Common sports analytics patterns
            r'([A-Z][A-Za-z_]*\s*=\s*[^=]+)': FormulaType.EQUATION,
            r'([A-Z][A-Za-z_]*%\s*=\s*[^=]+)': FormulaType.PERCENTAGE,
            r'([A-Z][A-Za-z_]*\s*/\s*\d+\s*=\s*[^=]+)': FormulaType.RATE,
            r'([A-Z][A-Za-z_]*\s*\+\s*[A-Z][A-Za-z_]*\s*=\s*[^=]+)': FormulaType.COMPOSITE,
            r'([A-Z][A-Za-z_]*\s*-\s*[A-Z][A-Za-z_]*\s*=\s*[^=]+)': FormulaType.DIFFERENTIAL,

            # LaTeX patterns
            r'\\[a-zA-Z]+\{[^}]+\}': FormulaType.EQUATION,
            r'\$[^$]+\$': FormulaType.EQUATION,
            r'\$\$[^$]+\$\$': FormulaType.EQUATION,

            # Mathematical expressions
            r'([a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/]\s*[a-zA-Z_][a-zA-Z0-9_]*)': FormulaType.EQUATION,
            r'([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[0-9.]+)': FormulaType.EQUATION,
        }

        # Variable mapping for sports analytics
        self.variable_mapping = {
            'pts': 'PTS', 'points': 'PTS',
            'fgm': 'FGM', 'field_goals_made': 'FGM',
            'fga': 'FGA', 'field_goals_attempted': 'FGA',
            '3pm': '3PM', 'three_pointers_made': '3PM',
            'ftm': 'FTM', 'free_throws_made': 'FTM',
            'fta': 'FTA', 'free_throws_attempted': 'FTA',
            'oreb': 'OREB', 'offensive_rebounds': 'OREB',
            'dreb': 'DREB', 'defensive_rebounds': 'DREB',
            'ast': 'AST', 'assists': 'AST',
            'stl': 'STL', 'steals': 'STL',
            'blk': 'BLK', 'blocks': 'BLK',
            'tov': 'TOV', 'turnovers': 'TOV',
            'pf': 'PF', 'personal_fouls': 'PF',
            'mp': 'MP', 'minutes_played': 'MP',
            'per': 'PER', 'player_efficiency_rating': 'PER',
            'ts': 'TS', 'true_shooting': 'TS',
            'usg': 'USG', 'usage_rate': 'USG',
            'ortg': 'ORtg', 'offensive_rating': 'ORtg',
            'drtg': 'DRtg', 'defensive_rating': 'DRtg',
            'pace': 'PACE',
            'bpm': 'BPM', 'box_plus_minus': 'BPM',
            'vorp': 'VORP', 'value_over_replacement_player': 'VORP',
            'ws': 'WS', 'win_shares': 'WS',
        }

        # Common sports analytics formula keywords
        self.sports_keywords = [
            'efficiency', 'rating', 'percentage', 'rate', 'per', 'ts', 'usg',
            'pace', 'plus_minus', 'win_shares', 'vorp', 'bpm', 'ortg', 'drtg',
            'true_shooting', 'usage_rate', 'player_efficiency', 'defensive_rating',
            'offensive_rating', 'net_rating', 'four_factors', 'clutch'
        ]

    def extract_formulas_from_text(self, text: str, page_number: int = 0) -> List[ExtractedFormula]:
        """
        Extract formulas from text content.

        Args:
            text: Text content to analyze
            page_number: Page number for context

        Returns:
            List of ExtractedFormula objects
        """
        formulas = []

        # Split text into lines for better context
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check each pattern
            for pattern, formula_type in self.formula_patterns.items():
                matches = re.finditer(pattern, line, re.IGNORECASE)

                for match in matches:
                    formula_text = match.group(1) if match.groups() else match.group(0)

                    # Clean up the formula
                    formula_text = self._clean_formula_text(formula_text)

                    if self._is_valid_formula(formula_text):
                        # Extract variables
                        variables = self._extract_variables(formula_text)

                        # Determine confidence based on context
                        confidence = self._calculate_confidence(formula_text, line, formula_type)

                        # Get context (surrounding lines)
                        context = self._get_context(lines, line_num)

                        # Convert to LaTeX if possible
                        latex_notation = self._convert_to_latex(formula_text)

                        # Convert to SymPy if possible
                        sympy_expression = self._convert_to_sympy(formula_text)

                        # Suggest tools
                        suggested_tools = self._suggest_tools(formula_text, formula_type)

                        formula = ExtractedFormula(
                            formula_text=formula_text,
                            formula_type=formula_type,
                            variables=variables,
                            page_number=page_number,
                            context=context,
                            confidence=confidence,
                            latex_notation=latex_notation,
                            sympy_expression=sympy_expression,
                            suggested_tools=suggested_tools
                        )

                        formulas.append(formula)

        # Remove duplicates and sort by confidence
        formulas = self._remove_duplicates(formulas)
        formulas.sort(key=lambda x: x.confidence, reverse=True)

        return formulas

    def extract_latex_from_text(self, text: str) -> List[str]:
        """
        Extract LaTeX formulas from text.

        Args:
            text: Text content to analyze

        Returns:
            List of LaTeX formula strings
        """
        latex_patterns = [
            r'\$([^$]+)\$',  # Inline math
            r'\$\$([^$]+)\$\$',  # Display math
            r'\\[a-zA-Z]+\{[^}]+\}',  # LaTeX commands
            r'\\begin\{equation\}.*?\\end\{equation\}',  # Equation environment
            r'\\begin\{align\}.*?\\end\{align\}',  # Align environment
        ]

        latex_formulas = []

        for pattern in latex_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                latex_formulas.append(match.group(1) if match.groups() else match.group(0))

        return latex_formulas

    def convert_latex_to_sympy(self, latex_str: str) -> Optional[str]:
        """
        Convert LaTeX formula to SymPy-compatible format.

        Args:
            latex_str: LaTeX formula string

        Returns:
            SymPy-compatible string or None if conversion fails
        """
        try:
            # Clean up LaTeX
            latex_str = latex_str.strip()

            # Remove common LaTeX formatting
            latex_str = re.sub(r'\\[a-zA-Z]+\{([^}]+)\}', r'\1', latex_str)
            latex_str = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', latex_str)
            latex_str = re.sub(r'\\cdot', '*', latex_str)
            latex_str = re.sub(r'\\times', '*', latex_str)
            latex_str = re.sub(r'\\div', '/', latex_str)
            latex_str = re.sub(r'\\pm', '+-', latex_str)
            latex_str = re.sub(r'\\mp', '-+', latex_str)

            # Try to parse with SymPy
            try:
                expr = parse_latex(latex_str)
                return str(expr)
            except:
                # Fallback to manual parsing
                return self._manual_latex_conversion(latex_str)

        except Exception as e:
            logger.warning(f"Failed to convert LaTeX to SymPy: {e}")
            return None

    def analyze_formula_structure(self, formula: str) -> Dict[str, Any]:
        """
        Analyze the structure of a formula.

        Args:
            formula: Formula string to analyze

        Returns:
            Dictionary with structure analysis
        """
        analysis = {
            'has_equality': '=' in formula,
            'has_inequality': any(op in formula for op in ['<', '>', '<=', '>=']),
            'operators': re.findall(r'[+\-*/^]', formula),
            'variables': self._extract_variables(formula),
            'constants': re.findall(r'\b\d+\.?\d*\b', formula),
            'complexity_score': len(re.findall(r'[+\-*/^()]', formula)),
            'is_percentage': '%' in formula,
            'is_ratio': '/' in formula and '=' in formula,
            'is_composite': len(re.findall(r'[+\-]', formula)) > 1,
        }

        return analysis

    def suggest_algebraic_tool(self, formula: str) -> str:
        """
        Suggest which algebraic tool to use for a formula.

        Args:
            formula: Formula string

        Returns:
            Suggested tool name
        """
        analysis = self.analyze_formula_structure(formula)

        if analysis['has_equality'] and not analysis['has_inequality']:
            if analysis['complexity_score'] > 5:
                return 'algebra_simplify_expression'
            else:
                return 'algebra_solve_equation'
        elif analysis['is_percentage'] or analysis['is_ratio']:
            return 'algebra_sports_formula'
        elif analysis['complexity_score'] > 10:
            return 'algebra_simplify_expression'
        else:
            return 'algebra_render_latex'

    def _clean_formula_text(self, formula_text: str) -> str:
        """Clean and normalize formula text"""
        # Remove extra whitespace
        formula_text = re.sub(r'\s+', ' ', formula_text.strip())

        # Remove common prefixes/suffixes
        formula_text = re.sub(r'^(formula|equation|formula:)\s*', '', formula_text, flags=re.IGNORECASE)
        formula_text = re.sub(r'\s*(formula|equation)$', '', formula_text, flags=re.IGNORECASE)

        return formula_text

    def _is_valid_formula(self, formula_text: str) -> bool:
        """Check if text represents a valid formula"""
        if len(formula_text) < 3:
            return False

        # Must contain at least one variable or operator
        has_variable = re.search(r'[a-zA-Z_][a-zA-Z0-9_]*', formula_text)
        has_operator = re.search(r'[+\-*/=]', formula_text)

        if not (has_variable or has_operator):
            return False

        # Check for sports analytics relevance
        formula_lower = formula_text.lower()
        has_sports_keyword = any(keyword in formula_lower for keyword in self.sports_keywords)

        # If it has sports keywords, it's likely valid
        if has_sports_keyword:
            return True

        # Otherwise, check for mathematical structure
        return bool(re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*[=+\-*/]', formula_text))

    def _extract_variables(self, formula_text: str) -> List[str]:
        """Extract variables from formula text"""
        # Find all potential variables
        variables = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', formula_text)

        # Filter out common words and constants
        common_words = {'and', 'or', 'the', 'of', 'in', 'to', 'for', 'with', 'by', 'per', 'rate', 'percentage'}
        variables = [var for var in variables if var.lower() not in common_words and not var.isdigit()]

        # Map to standard notation
        mapped_variables = []
        for var in variables:
            mapped_var = self.variable_mapping.get(var.lower(), var.upper())
            mapped_variables.append(mapped_var)

        return list(set(mapped_variables))  # Remove duplicates

    def _calculate_confidence(self, formula_text: str, context_line: str, formula_type: FormulaType) -> float:
        """Calculate confidence score for extracted formula"""
        confidence = 0.5  # Base confidence

        # Increase confidence for sports analytics keywords
        formula_lower = formula_text.lower()
        context_lower = context_line.lower()

        sports_keyword_count = sum(1 for keyword in self.sports_keywords if keyword in formula_lower or keyword in context_lower)
        confidence += min(sports_keyword_count * 0.1, 0.3)

        # Increase confidence for mathematical structure
        if '=' in formula_text:
            confidence += 0.2
        if any(op in formula_text for op in ['+', '-', '*', '/']):
            confidence += 0.1
        if re.search(r'[A-Z][A-Za-z_]*', formula_text):  # Uppercase variables
            confidence += 0.1

        # Decrease confidence for very short or very long formulas
        if len(formula_text) < 5:
            confidence -= 0.2
        elif len(formula_text) > 200:
            confidence -= 0.1

        return min(max(confidence, 0.0), 1.0)

    def _get_context(self, lines: List[str], line_num: int, context_lines: int = 2) -> str:
        """Get context around a formula"""
        start = max(0, line_num - context_lines)
        end = min(len(lines), line_num + context_lines + 1)
        return '\n'.join(lines[start:end])

    def _convert_to_latex(self, formula_text: str) -> Optional[str]:
        """Convert formula to LaTeX notation"""
        try:
            # Simple conversion for common patterns
            latex = formula_text

            # Convert common operators
            latex = re.sub(r'\*', r' \\cdot ', latex)
            latex = re.sub(r'/', r' \\frac{}{}', latex)
            latex = re.sub(r'\^', r'^', latex)

            # Wrap in math mode
            if not latex.startswith('$'):
                latex = f'${latex}$'

            return latex
        except Exception:
            return None

    def _convert_to_sympy(self, formula_text: str) -> Optional[str]:
        """Convert formula to SymPy expression"""
        try:
            # Clean the formula for SymPy
            sympy_text = formula_text

            # Replace common patterns
            sympy_text = re.sub(r'\^', '**', sympy_text)
            sympy_text = re.sub(r'\b(\d+)\s*([a-zA-Z_][a-zA-Z0-9_]*)\b', r'\1*\2', sympy_text)

            # Try to parse
            expr = parse_expr(sympy_text)
            return str(expr)
        except Exception:
            return None

    def _suggest_tools(self, formula_text: str, formula_type: FormulaType) -> List[str]:
        """Suggest appropriate tools for the formula"""
        tools = ['formula_identify_type', 'formula_map_variables']

        if formula_type == FormulaType.EQUATION:
            tools.extend(['algebra_solve_equation', 'algebra_simplify_expression'])
        elif formula_type in [FormulaType.EFFICIENCY, FormulaType.PERCENTAGE, FormulaType.RATE]:
            tools.append('algebra_sports_formula')
        elif formula_type == FormulaType.COMPOSITE:
            tools.extend(['algebra_simplify_expression', 'algebra_solve_equation'])

        tools.append('algebra_render_latex')

        return tools

    def _remove_duplicates(self, formulas: List[ExtractedFormula]) -> List[ExtractedFormula]:
        """Remove duplicate formulas"""
        seen = set()
        unique_formulas = []

        for formula in formulas:
            # Create a signature for comparison
            signature = (formula.formula_text.lower().strip(), formula.page_number)

            if signature not in seen:
                seen.add(signature)
                unique_formulas.append(formula)

        return unique_formulas

    def _manual_latex_conversion(self, latex_str: str) -> Optional[str]:
        """Manual conversion for complex LaTeX patterns"""
        try:
            # Handle fractions
            latex_str = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', latex_str)

            # Handle subscripts and superscripts
            latex_str = re.sub(r'\^\{([^}]+)\}', r'**(\1)', latex_str)
            latex_str = re.sub(r'\^([a-zA-Z0-9])', r'**\1', latex_str)

            # Handle Greek letters
            greek_map = {
                '\\alpha': 'alpha', '\\beta': 'beta', '\\gamma': 'gamma',
                '\\delta': 'delta', '\\epsilon': 'epsilon', '\\theta': 'theta',
                '\\lambda': 'lambda', '\\mu': 'mu', '\\pi': 'pi', '\\sigma': 'sigma',
                '\\tau': 'tau', '\\phi': 'phi', '\\omega': 'omega'
            }

            for latex_greek, sympy_greek in greek_map.items():
                latex_str = latex_str.replace(latex_greek, sympy_greek)

            return latex_str
        except Exception:
            return None




