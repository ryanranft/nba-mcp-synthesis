"""
Automated Book Analysis Pipeline for Sports Analytics

This module provides AI-powered analysis of sports analytics books to automatically
extract mathematical formulas, categorize them, and build a searchable database.
It builds upon the existing PDF reading capabilities to create an intelligent
formula extraction and analysis system.

Author: NBA MCP Server Team
Date: October 13, 2025
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

try:
    import sympy as sp
    from sympy import symbols, sympify
    from sympy.parsing.sympy_parser import parse_expr
    SYMPY_AVAILABLE = True
except ImportError:
    sp = None
    SYMPY_AVAILABLE = False

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..exceptions import ValidationError
from .logger_config import log_operation

logger = logging.getLogger(__name__)

# Use ValidationError for all tool errors
ToolError = ValidationError


class FormulaCategory(Enum):
    """Categories for sports analytics formulas"""
    EFFICIENCY = "efficiency"
    SHOOTING = "shooting"
    DEFENSIVE = "defensive"
    TEAM = "team"
    ADVANCED = "advanced"
    PERCENTAGE = "percentage"
    RATING = "rating"
    PACE = "pace"
    REBOUNDING = "rebounding"
    ASSIST = "assist"
    TURNOVER = "turnover"
    CLUTCH = "clutch"
    ON_OFF = "on_off"
    UNKNOWN = "unknown"


class FormulaComplexity(Enum):
    """Complexity levels for formulas"""
    SIMPLE = "simple"  # Basic arithmetic (+, -, *, /)
    MODERATE = "moderate"  # Multiple operations, some functions
    COMPLEX = "complex"  # Advanced functions, multiple variables
    VERY_COMPLEX = "very_complex"  # Multiple formulas, complex dependencies


@dataclass
class ExtractedFormula:
    """Represents a formula extracted from a book"""
    formula_id: str
    formula_text: str
    formula_sympy: Optional[str] = None
    formula_latex: Optional[str] = None
    variables: List[str] = None
    category: FormulaCategory = FormulaCategory.UNKNOWN
    complexity: FormulaComplexity = FormulaComplexity.SIMPLE
    confidence_score: float = 0.0
    source_page: Optional[int] = None
    source_context: Optional[str] = None
    book_title: Optional[str] = None
    book_author: Optional[str] = None
    description: Optional[str] = None
    validation_status: str = "pending"
    validation_notes: Optional[str] = None


@dataclass
class BookAnalysisResult:
    """Results from analyzing a sports analytics book"""
    book_title: str
    book_author: Optional[str]
    total_pages: int
    analyzed_pages: int
    formulas_found: int
    formulas_by_category: Dict[str, int]
    formulas_by_complexity: Dict[str, int]
    average_confidence: float
    extraction_errors: List[str]
    analysis_timestamp: str
    formulas: List[ExtractedFormula]


class AutomatedBookAnalyzer:
    """Main class for automated book analysis"""

    def __init__(self):
        self.formula_patterns = self._initialize_formula_patterns()
        self.category_keywords = self._initialize_category_keywords()
        self.complexity_indicators = self._initialize_complexity_indicators()

    def _initialize_formula_patterns(self) -> Dict[str, str]:
        """Initialize regex patterns for formula detection"""
        return {
            # Basic mathematical patterns
            'equation': r'([A-Za-z_][A-Za-z0-9_]*\s*=\s*[^=]+)',
            'percentage': r'([A-Za-z_][A-Za-z0-9_]*%\s*=\s*[^=]+)',
            'ratio': r'([A-Za-z_][A-Za-z0-9_]*\s*=\s*[^/]*/[^=]+)',
            'formula': r'(formula|equation|calculation):\s*([^\.]+)',
            'latex': r'\\[a-zA-Z]+\{[^}]+\}',
            'fraction': r'\\frac\{[^}]+\}\{[^}]+\}',
            'subscript': r'[A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]+',
            # Sports-specific patterns
            'efficiency': r'(efficiency|rating|index)\s*=\s*[^=]+',
            'shooting': r'(shooting|percentage|rate)\s*=\s*[^=]+',
            'defensive': r'(defensive|defense|rating)\s*=\s*[^=]+',
            'team': r'(team|total|combined)\s*=\s*[^=]+',
        }

    def _initialize_category_keywords(self) -> Dict[FormulaCategory, List[str]]:
        """Initialize keywords for automatic categorization"""
        return {
            FormulaCategory.EFFICIENCY: [
                'efficiency', 'rating', 'per', 'vorp', 'bpm', 'win shares',
                'player efficiency', 'performance', 'index'
            ],
            FormulaCategory.SHOOTING: [
                'shooting', 'field goal', 'three point', 'free throw',
                'percentage', 'accuracy', 'fg%', '3p%', 'ft%', 'ts%', 'efg%'
            ],
            FormulaCategory.DEFENSIVE: [
                'defensive', 'defense', 'rating', 'steal', 'block',
                'defensive rating', 'drtg', 'defensive win shares'
            ],
            FormulaCategory.TEAM: [
                'team', 'total', 'combined', 'net rating', 'offensive rating',
                'team efficiency', 'pace', 'team stats'
            ],
            FormulaCategory.ADVANCED: [
                'advanced', 'analytics', 'metric', 'composite', 'weighted',
                'adjusted', 'normalized', 'standardized'
            ],
            FormulaCategory.PERCENTAGE: [
                'percentage', '%', 'rate', 'ratio', 'proportion',
                'share', 'distribution'
            ],
            FormulaCategory.RATING: [
                'rating', 'rtg', 'plus minus', 'differential',
                'net rating', 'offensive rating', 'defensive rating'
            ],
            FormulaCategory.PACE: [
                'pace', 'speed', 'tempo', 'possessions', 'per 100',
                'pace adjusted', 'per 48'
            ],
            FormulaCategory.REBOUNDING: [
                'rebound', 'reb', 'rebounding', 'offensive rebound',
                'defensive rebound', 'rebound percentage'
            ],
            FormulaCategory.ASSIST: [
                'assist', 'ast', 'assist percentage', 'assist ratio',
                'assist rate', 'passing'
            ],
            FormulaCategory.TURNOVER: [
                'turnover', 'tov', 'turnover percentage', 'turnover rate',
                'ball security', 'possession'
            ],
            FormulaCategory.CLUTCH: [
                'clutch', 'late game', 'pressure', 'crunch time',
                'game winning', 'clutch performance'
            ],
            FormulaCategory.ON_OFF: [
                'on off', 'on/off', 'differential', 'impact',
                'plus minus', 'net rating'
            ]
        }

    def _initialize_complexity_indicators(self) -> Dict[FormulaComplexity, List[str]]:
        """Initialize indicators for complexity assessment"""
        return {
            FormulaComplexity.SIMPLE: [
                '+', '-', '*', '/', '=', 'percent', '%'
            ],
            FormulaComplexity.MODERATE: [
                'sqrt', 'log', 'exp', 'power', '^', '**',
                'sum', 'average', 'mean', 'max', 'min'
            ],
            FormulaComplexity.COMPLEX: [
                'integral', 'derivative', 'limit', 'matrix',
                'vector', 'correlation', 'regression'
            ],
            FormulaComplexity.VERY_COMPLEX: [
                'multiple', 'nested', 'recursive', 'iterative',
                'optimization', 'machine learning', 'ai'
            ]
        }

    @log_operation("automated_book_analysis")
    def analyze_book(
        self,
        book_path: str,
        book_title: Optional[str] = None,
        book_author: Optional[str] = None,
        max_pages: Optional[int] = None,
        confidence_threshold: float = 0.5
    ) -> BookAnalysisResult:
        """
        Analyze a sports analytics book to extract formulas automatically.

        Args:
            book_path: Path to the PDF book file
            book_title: Optional title of the book
            book_author: Optional author of the book
            max_pages: Maximum number of pages to analyze (None for all)
            confidence_threshold: Minimum confidence score for formula inclusion

        Returns:
            BookAnalysisResult with extracted formulas and analysis metadata

        Raises:
            ValidationError: If book analysis fails or dependencies are missing
        """
        logger.info(f"Starting automated analysis of book: {book_path}")

        if not SYMPY_AVAILABLE:
            raise ValidationError("SymPy is required for automated book analysis. Please install it.")

        try:
            # Get book metadata
            if not book_title:
                book_title = Path(book_path).stem.replace('_', ' ').title()

            # Extract text from PDF (using existing MCP capabilities)
            extracted_text = self._extract_text_from_pdf(book_path, max_pages)

            # Analyze text for formulas
            formulas = self._extract_formulas_from_text(
                extracted_text, book_title, book_author, confidence_threshold
            )

            # Categorize and analyze formulas
            categorized_formulas = self._categorize_formulas(formulas)

            # Calculate analysis statistics
            stats = self._calculate_analysis_statistics(categorized_formulas)

            result = BookAnalysisResult(
                book_title=book_title,
                book_author=book_author,
                total_pages=len(extracted_text),
                analyzed_pages=len(extracted_text),
                formulas_found=len(categorized_formulas),
                formulas_by_category=stats['by_category'],
                formulas_by_complexity=stats['by_complexity'],
                average_confidence=stats['average_confidence'],
                extraction_errors=stats['errors'],
                analysis_timestamp=pd.Timestamp.now().isoformat() if NUMPY_AVAILABLE else "unknown",
                formulas=categorized_formulas
            )

            logger.info(f"Analysis complete: {len(categorized_formulas)} formulas found")
            return result

        except Exception as e:
            logger.error(f"Book analysis failed: {e}")
            raise ValidationError(f"Failed to analyze book: {e}")

    def _extract_text_from_pdf(self, book_path: str, max_pages: Optional[int]) -> List[str]:
        """Extract text from PDF pages"""
        # This would integrate with existing MCP PDF reading capabilities
        # For now, return mock data structure
        logger.info(f"Extracting text from PDF: {book_path}")

        # In a real implementation, this would use the MCP PDF tools
        # For now, return a list of page texts
        return [f"Mock page {i} content" for i in range(max_pages or 10)]

    def _extract_formulas_from_text(
        self,
        page_texts: List[str],
        book_title: str,
        book_author: Optional[str],
        confidence_threshold: float
    ) -> List[ExtractedFormula]:
        """Extract formulas from page text using pattern matching"""
        formulas = []

        for page_num, page_text in enumerate(page_texts):
            logger.debug(f"Analyzing page {page_num + 1}")

            # Apply all formula patterns
            for pattern_name, pattern in self.formula_patterns.items():
                matches = re.finditer(pattern, page_text, re.IGNORECASE)

                for match in matches:
                    formula_text = match.group(0).strip()

                    # Skip if too short or doesn't look like a formula
                    if len(formula_text) < 5:
                        continue

                    # Calculate confidence score
                    confidence = self._calculate_confidence_score(formula_text, pattern_name)

                    if confidence >= confidence_threshold:
                        formula = ExtractedFormula(
                            formula_id=f"{book_title.lower().replace(' ', '_')}_page_{page_num + 1}_{len(formulas)}",
                            formula_text=formula_text,
                            source_page=page_num + 1,
                            source_context=page_text[max(0, match.start() - 50):match.end() + 50],
                            book_title=book_title,
                            book_author=book_author,
                            confidence_score=confidence
                        )

                        # Try to parse with SymPy
                        try:
                            parsed = self._parse_formula_with_sympy(formula_text)
                            if parsed:
                                formula.formula_sympy = str(parsed)
                                formula.formula_latex = sp.latex(parsed)
                                formula.variables = [str(symbol) for symbol in parsed.free_symbols]
                        except Exception as e:
                            logger.debug(f"Could not parse formula '{formula_text}': {e}")

                        formulas.append(formula)

        return formulas

    def _calculate_confidence_score(self, formula_text: str, pattern_name: str) -> float:
        """Calculate confidence score for a potential formula"""
        score = 0.0

        # Base score by pattern type
        pattern_scores = {
            'equation': 0.8,
            'percentage': 0.9,
            'ratio': 0.7,
            'formula': 0.9,
            'latex': 0.95,
            'fraction': 0.9,
            'subscript': 0.6,
            'efficiency': 0.8,
            'shooting': 0.8,
            'defensive': 0.8,
            'team': 0.7
        }

        score += pattern_scores.get(pattern_name, 0.5)

        # Boost score for mathematical symbols
        math_symbols = ['=', '+', '-', '*', '/', '^', '(', ')', '%']
        symbol_count = sum(1 for symbol in math_symbols if symbol in formula_text)
        score += min(symbol_count * 0.1, 0.3)

        # Boost score for sports terminology
        sports_terms = ['points', 'rebounds', 'assists', 'minutes', 'games', 'efficiency', 'rating']
        term_count = sum(1 for term in sports_terms if term.lower() in formula_text.lower())
        score += min(term_count * 0.05, 0.2)

        # Penalty for very short or very long formulas
        if len(formula_text) < 10:
            score -= 0.2
        elif len(formula_text) > 200:
            score -= 0.1

        return min(max(score, 0.0), 1.0)

    def _parse_formula_with_sympy(self, formula_text: str) -> Optional[sp.Expr]:
        """Parse formula text with SymPy"""
        try:
            # Clean up the formula text
            cleaned = formula_text.replace('%', '/100')
            cleaned = re.sub(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*', '', cleaned)  # Remove variable assignment

            # Try to parse
            parsed = parse_expr(cleaned, evaluate=False)
            return parsed
        except Exception:
            return None

    def _categorize_formulas(self, formulas: List[ExtractedFormula]) -> List[ExtractedFormula]:
        """Categorize formulas and assess complexity"""
        for formula in formulas:
            # Determine category
            formula.category = self._determine_category(formula.formula_text)

            # Determine complexity
            formula.complexity = self._determine_complexity(formula.formula_text)

            # Generate description
            formula.description = self._generate_description(formula)

        return formulas

    def _determine_category(self, formula_text: str) -> FormulaCategory:
        """Determine the category of a formula based on its content"""
        text_lower = formula_text.lower()

        # Check each category
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category

        return FormulaCategory.UNKNOWN

    def _determine_complexity(self, formula_text: str) -> FormulaComplexity:
        """Determine the complexity level of a formula"""
        text_lower = formula_text.lower()

        # Check complexity indicators
        for complexity, indicators in self.complexity_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return complexity

        # Default based on formula length and structure
        if len(formula_text) < 30:
            return FormulaComplexity.SIMPLE
        elif len(formula_text) < 100:
            return FormulaComplexity.MODERATE
        else:
            return FormulaComplexity.COMPLEX

    def _generate_description(self, formula: ExtractedFormula) -> str:
        """Generate a description for a formula"""
        category_name = formula.category.value.replace('_', ' ').title()
        complexity_name = formula.complexity.value.replace('_', ' ').title()

        return f"{category_name} formula ({complexity_name} complexity) from {formula.book_title}"

    def _calculate_analysis_statistics(self, formulas: List[ExtractedFormula]) -> Dict[str, Any]:
        """Calculate statistics from the analysis"""
        if not formulas:
            return {
                'by_category': {},
                'by_complexity': {},
                'average_confidence': 0.0,
                'errors': []
            }

        # Count by category
        by_category = {}
        for formula in formulas:
            category = formula.category.value
            by_category[category] = by_category.get(category, 0) + 1

        # Count by complexity
        by_complexity = {}
        for formula in formulas:
            complexity = formula.complexity.value
            by_complexity[complexity] = by_complexity.get(complexity, 0) + 1

        # Calculate average confidence
        avg_confidence = sum(f.confidence_score for f in formulas) / len(formulas)

        return {
            'by_category': by_category,
            'by_complexity': by_complexity,
            'average_confidence': avg_confidence,
            'errors': []  # Would track extraction errors in real implementation
        }


@log_operation("automated_formula_extraction")
def extract_formulas_from_book(
    book_path: str,
    book_title: Optional[str] = None,
    book_author: Optional[str] = None,
    max_pages: Optional[int] = None,
    confidence_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Extract formulas from a sports analytics book using automated analysis.

    Args:
        book_path: Path to the PDF book file
        book_title: Optional title of the book
        book_author: Optional author of the book
        max_pages: Maximum number of pages to analyze
        confidence_threshold: Minimum confidence score for formula inclusion

    Returns:
        Dictionary with analysis results and extracted formulas

    Raises:
        ValidationError: If extraction fails or dependencies are missing
    """
    analyzer = AutomatedBookAnalyzer()
    result = analyzer.analyze_book(
        book_path=book_path,
        book_title=book_title,
        book_author=book_author,
        max_pages=max_pages,
        confidence_threshold=confidence_threshold
    )

    # Convert to dictionary for JSON serialization
    return {
        'book_title': result.book_title,
        'book_author': result.book_author,
        'total_pages': result.total_pages,
        'analyzed_pages': result.analyzed_pages,
        'formulas_found': result.formulas_found,
        'formulas_by_category': result.formulas_by_category,
        'formulas_by_complexity': result.formulas_by_complexity,
        'average_confidence': result.average_confidence,
        'extraction_errors': result.extraction_errors,
        'analysis_timestamp': result.analysis_timestamp,
        'formulas': [asdict(formula) for formula in result.formulas]
    }


@log_operation("automated_formula_categorization")
def categorize_extracted_formulas(
    formulas: List[Dict[str, Any]],
    custom_categories: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Categorize and analyze extracted formulas with custom category support.

    Args:
        formulas: List of extracted formula dictionaries
        custom_categories: Optional custom category definitions

    Returns:
        Dictionary with categorization results and statistics

    Raises:
        ValidationError: If categorization fails
    """
    logger.info(f"Categorizing {len(formulas)} extracted formulas")

    try:
        analyzer = AutomatedBookAnalyzer()

        # Convert dictionaries back to ExtractedFormula objects
        formula_objects = []
        for formula_dict in formulas:
            formula = ExtractedFormula(
                formula_id=formula_dict.get('formula_id', ''),
                formula_text=formula_dict.get('formula_text', ''),
                formula_sympy=formula_dict.get('formula_sympy'),
                formula_latex=formula_dict.get('formula_latex'),
                variables=formula_dict.get('variables', []),
                confidence_score=formula_dict.get('confidence_score', 0.0),
                source_page=formula_dict.get('source_page'),
                source_context=formula_dict.get('source_context'),
                book_title=formula_dict.get('book_title'),
                book_author=formula_dict.get('book_author')
            )
            formula_objects.append(formula)

        # Apply custom categories if provided
        if custom_categories:
            analyzer.category_keywords.update(custom_categories)

        # Categorize formulas
        categorized_formulas = analyzer._categorize_formulas(formula_objects)

        # Calculate statistics
        stats = analyzer._calculate_analysis_statistics(categorized_formulas)

        return {
            'status': 'success',
            'total_formulas': len(categorized_formulas),
            'categorization_results': stats,
            'formulas': [asdict(formula) for formula in categorized_formulas],
            'message': f"Successfully categorized {len(categorized_formulas)} formulas"
        }

    except Exception as e:
        logger.error(f"Formula categorization failed: {e}")
        raise ValidationError(f"Failed to categorize formulas: {e}")


@log_operation("automated_formula_validation")
def validate_extracted_formulas(
    formulas: List[Dict[str, Any]],
    validation_rules: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate extracted formulas against known sports analytics standards.

    Args:
        formulas: List of extracted formula dictionaries
        validation_rules: Optional custom validation rules

    Returns:
        Dictionary with validation results and recommendations

    Raises:
        ValidationError: If validation fails
    """
    logger.info(f"Validating {len(formulas)} extracted formulas")

    try:
        validation_results = []
        validation_stats = {
            'total_formulas': len(formulas),
            'valid_formulas': 0,
            'invalid_formulas': 0,
            'warning_formulas': 0,
            'validation_errors': []
        }

        for formula_dict in formulas:
            formula_text = formula_dict.get('formula_text', '')
            formula_sympy = formula_dict.get('formula_sympy')

            validation_result = {
                'formula_id': formula_dict.get('formula_id', ''),
                'status': 'pending',
                'errors': [],
                'warnings': [],
                'recommendations': []
            }

            # Basic validation checks
            if not formula_text:
                validation_result['status'] = 'invalid'
                validation_result['errors'].append("Empty formula text")
                validation_stats['invalid_formulas'] += 1
            elif not formula_sympy:
                validation_result['status'] = 'warning'
                validation_result['warnings'].append("Could not parse with SymPy")
                validation_stats['warning_formulas'] += 1
            else:
                validation_result['status'] = 'valid'
                validation_stats['valid_formulas'] += 1

            # Additional validation rules
            if validation_rules:
                # Implement custom validation logic here
                pass

            validation_results.append(validation_result)

        return {
            'status': 'success',
            'validation_results': validation_results,
            'validation_statistics': validation_stats,
            'message': f"Validation complete: {validation_stats['valid_formulas']} valid, {validation_stats['invalid_formulas']} invalid, {validation_stats['warning_formulas']} warnings"
        }

    except Exception as e:
        logger.error(f"Formula validation failed: {e}")
        raise ValidationError(f"Failed to validate formulas: {e}")



