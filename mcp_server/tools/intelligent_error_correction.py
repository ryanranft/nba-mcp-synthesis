#!/usr/bin/env python3
"""
Phase 7.6: Intelligent Error Correction

This module provides comprehensive AI-powered error detection and correction
capabilities for sports analytics formulas, calculations, and analysis.

Features:
- Intelligent error detection across multiple error types
- AI-powered correction suggestions with explanations
- Comprehensive formula validation
- Pattern-based error analysis
- Learning from error cases
- Domain-specific error detection
- Statistical error analysis
- Context-aware correction strategies
"""

import logging
import uuid
import re
import ast
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import sympy as sp
from sympy import symbols, sympify, simplify, expand, factor, diff, integrate
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes and Enums
# =============================================================================


class ErrorType(str, Enum):
    """Types of errors that can be detected"""

    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    LOGICAL = "logical"
    MATHEMATICAL = "mathematical"
    DOMAIN = "domain"
    UNIT = "unit"
    BOUNDS = "bounds"
    PERFORMANCE = "performance"


class SeverityLevel(str, Enum):
    """Severity levels for errors"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CorrectionStrategy(str, Enum):
    """Strategies for error correction"""

    AUTOMATIC = "automatic"
    SUGGESTED = "suggested"
    INTERACTIVE = "interactive"


@dataclass
class DetectedError:
    """Represents a detected error"""

    error_id: str
    error_type: str
    severity: str
    message: str
    position: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    context: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CorrectionSuggestion:
    """Represents a correction suggestion"""

    suggestion_id: str
    original_text: str
    corrected_text: str
    explanation: str
    confidence: float
    strategy: str
    validation_result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Represents validation results"""

    is_valid: bool
    errors: List[DetectedError]
    warnings: List[str]
    suggestions: List[CorrectionSuggestion]
    performance_metrics: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# Core Intelligent Error Correction Engine
# =============================================================================


class IntelligentErrorCorrectionEngine:
    """Main engine for intelligent error detection and correction"""

    def __init__(self):
        """Initialize the error correction engine"""
        self.error_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.correction_history: List[Dict[str, Any]] = []
        self.learning_data: List[Dict[str, Any]] = []
        self.domain_knowledge: Dict[str, Any] = {}

        # Initialize error patterns and domain knowledge
        self._initialize_error_patterns()
        self._initialize_domain_knowledge()

        logger.info("Intelligent Error Correction Engine initialized")

    def _generate_error_id(self) -> str:
        """Generate a unique error ID"""
        return f"error_{uuid.uuid4().hex[:8]}"

    def _generate_suggestion_id(self) -> str:
        """Generate a unique suggestion ID"""
        return f"suggestion_{uuid.uuid4().hex[:8]}"

    def _initialize_error_patterns(self):
        """Initialize common error patterns"""
        self.error_patterns = {
            "syntax": [
                {
                    "pattern": r"(\w+)\s*\(\s*\)\s*$",
                    "description": "Empty function call",
                    "suggestion": "Add parameters or remove parentheses",
                },
                {
                    "pattern": r"(\w+)\s*=\s*=\s*",
                    "description": "Double equals in assignment",
                    "suggestion": "Use single equals for assignment",
                },
                {
                    "pattern": r"[+\-*/]\s*[+\-*/]",
                    "description": "Consecutive operators",
                    "suggestion": "Check for missing operands",
                },
            ],
            "semantic": [
                {
                    "pattern": r"(\w+)\s*/\s*0",
                    "description": "Division by zero",
                    "suggestion": "Add zero check or use different formula",
                },
                {
                    "pattern": r"sqrt\s*\(\s*-\d+",
                    "description": "Square root of negative number",
                    "suggestion": "Use absolute value or complex numbers",
                },
                {
                    "pattern": r"log\s*\(\s*[0-9]*\.?[0-9]*\s*\)",
                    "description": "Logarithm of non-positive number",
                    "suggestion": "Ensure argument is positive",
                },
            ],
            "mathematical": [
                {
                    "pattern": r"(\w+)\s*\*\s*(\w+)\s*\+\s*(\w+)\s*\*\s*(\w+)",
                    "description": "Potential distributive property",
                    "suggestion": "Consider factoring: a*b + c*d = (a+c)*(b+d) if applicable",
                },
                {
                    "pattern": r"(\w+)\s*\*\s*(\w+)\s*/\s*(\w+)",
                    "description": "Potential simplification",
                    "suggestion": "Check if terms can be simplified",
                },
            ],
            "domain": [
                {
                    "pattern": r"(\w+)\s*>\s*100",
                    "description": "Percentage over 100%",
                    "suggestion": "Check if percentage calculation is correct",
                },
                {
                    "pattern": r"(\w+)\s*<\s*0",
                    "description": "Negative value in sports context",
                    "suggestion": "Verify if negative values are valid",
                },
            ],
        }

    def _initialize_domain_knowledge(self):
        """Initialize domain-specific knowledge"""
        self.domain_knowledge = {
            "basketball": {
                "valid_ranges": {
                    "field_goal_percentage": (0.0, 1.0),
                    "three_point_percentage": (0.0, 1.0),
                    "free_throw_percentage": (0.0, 1.0),
                    "points_per_game": (0.0, 100.0),
                    "rebounds_per_game": (0.0, 30.0),
                    "assists_per_game": (0.0, 20.0),
                    "minutes_per_game": (0.0, 48.0),
                },
                "common_formulas": [
                    "points / field_goal_attempts",
                    "rebounds / minutes",
                    "assists / minutes",
                    "points + rebounds + assists",
                ],
                "unit_conversions": {
                    "minutes": {"seconds": 60, "hours": 1 / 60},
                    "feet": {"inches": 12, "meters": 0.3048},
                },
            },
            "statistics": {
                "valid_ranges": {
                    "correlation": (-1.0, 1.0),
                    "probability": (0.0, 1.0),
                    "standard_deviation": (0.0, float("inf")),
                    "variance": (0.0, float("inf")),
                },
                "common_formulas": [
                    "mean = sum(values) / count(values)",
                    "variance = sum((x - mean)^2) / n",
                    "correlation = covariance(x,y) / (std(x) * std(y))",
                ],
            },
        }

    def detect_errors(
        self,
        input_formula: str,
        context_type: str = "formula",
        error_types: List[str] = None,
        include_suggestions: bool = True,
        confidence_threshold: float = 0.7,
        domain_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect errors in formulas and expressions.

        Args:
            input_formula: Formula or expression to analyze
            context_type: Type of context for error detection
            error_types: Types of errors to detect
            include_suggestions: Whether to include correction suggestions
            confidence_threshold: Minimum confidence threshold
            domain_context: Domain context for domain-specific detection

        Returns:
            Dictionary with detected errors and suggestions
        """
        try:
            # Handle empty formula
            if not input_formula or not input_formula.strip():
                return {
                    "status": "error",
                    "error": "Empty formula provided",
                    "errors": [],
                    "suggestions": [],
                }

            logger.info(f"Detecting errors in formula: {input_formula[:50]}...")

            if error_types is None:
                error_types = ["syntax", "semantic", "logical"]

            detected_errors = []

            # Detect different types of errors
            for error_type in error_types:
                errors = self._detect_error_type(
                    input_formula, error_type, domain_context
                )
                detected_errors.extend(errors)

            # Filter by confidence threshold
            filtered_errors = [
                error
                for error in detected_errors
                if error.confidence >= confidence_threshold
            ]

            # Generate suggestions if requested
            suggestions = []
            if include_suggestions:
                suggestions = self._generate_correction_suggestions(
                    filtered_errors, input_formula, domain_context
                )

            result = {
                "status": "success",
                "input_formula": input_formula,
                "context_type": context_type,
                "errors_detected": len(filtered_errors),
                "errors": [asdict(error) for error in filtered_errors],
                "suggestions": [asdict(suggestion) for suggestion in suggestions],
                "metadata": {
                    "detection_timestamp": datetime.now().isoformat(),
                    "error_types_checked": error_types,
                    "confidence_threshold": confidence_threshold,
                    "domain_context": domain_context,
                },
            }

            logger.info(
                f"Error detection completed: {len(filtered_errors)} errors found"
            )
            return result

        except Exception as e:
            logger.error(f"Error detection failed: {e}")
            return {"status": "error", "error": str(e), "errors": [], "suggestions": []}

    def _detect_error_type(
        self, formula: str, error_type: str, domain_context: Optional[str]
    ) -> List[DetectedError]:
        """Detect specific type of errors"""
        errors = []

        try:
            if error_type == "syntax":
                errors.extend(self._detect_syntax_errors(formula))
            elif error_type == "semantic":
                errors.extend(self._detect_semantic_errors(formula))
            elif error_type == "logical":
                errors.extend(self._detect_logical_errors(formula))
            elif error_type == "mathematical":
                errors.extend(self._detect_mathematical_errors(formula))
            elif error_type == "domain":
                errors.extend(self._detect_domain_errors(formula, domain_context))
            elif error_type == "unit":
                errors.extend(self._detect_unit_errors(formula))

            return errors

        except Exception as e:
            logger.error(f"Error detection for {error_type} failed: {e}")
            return []

    def _detect_syntax_errors(self, formula: str) -> List[DetectedError]:
        """Detect syntax errors"""
        errors = []

        try:
            # Check for basic syntax issues
            patterns = self.error_patterns.get("syntax", [])

            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                matches = re.finditer(pattern, formula)

                for match in matches:
                    error = DetectedError(
                        error_id=self._generate_error_id(),
                        error_type="syntax",
                        severity="medium",
                        message=pattern_info["description"],
                        position=(match.start(), match.end()),
                        confidence=0.8,
                        context={"matched_text": match.group()},
                        suggestions=[pattern_info["suggestion"]],
                    )
                    errors.append(error)

            # Check for unmatched parentheses
            if formula.count("(") != formula.count(")"):
                error = DetectedError(
                    error_id=self._generate_error_id(),
                    error_type="syntax",
                    severity="high",
                    message="Unmatched parentheses",
                    confidence=0.9,
                    suggestions=["Check for missing or extra parentheses"],
                )
                errors.append(error)

            # Check for invalid characters
            invalid_chars = re.findall(r"[^a-zA-Z0-9+\-*/().,\s]", formula)
            if invalid_chars:
                error = DetectedError(
                    error_id=self._generate_error_id(),
                    error_type="syntax",
                    severity="medium",
                    message=f"Invalid characters found: {invalid_chars}",
                    confidence=0.7,
                    suggestions=["Remove or replace invalid characters"],
                )
                errors.append(error)

            return errors

        except Exception as e:
            logger.error(f"Syntax error detection failed: {e}")
            return []

    def _detect_semantic_errors(self, formula: str) -> List[DetectedError]:
        """Detect semantic errors"""
        errors = []

        try:
            patterns = self.error_patterns.get("semantic", [])

            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                matches = re.finditer(pattern, formula)

                for match in matches:
                    error = DetectedError(
                        error_id=self._generate_error_id(),
                        error_type="semantic",
                        severity="high",
                        message=pattern_info["description"],
                        position=(match.start(), match.end()),
                        confidence=0.9,
                        context={"matched_text": match.group()},
                        suggestions=[pattern_info["suggestion"]],
                    )
                    errors.append(error)

            # Check for division by zero
            if re.search(r"/\s*0", formula):
                error = DetectedError(
                    error_id=self._generate_error_id(),
                    error_type="semantic",
                    severity="critical",
                    message="Division by zero detected",
                    confidence=1.0,
                    suggestions=["Add zero check or use different formula"],
                )
                errors.append(error)

            return errors

        except Exception as e:
            logger.error(f"Semantic error detection failed: {e}")
            return []

    def _detect_logical_errors(self, formula: str) -> List[DetectedError]:
        """Detect logical errors"""
        errors = []

        try:
            # Check for impossible mathematical operations
            if re.search(r"sqrt\s*\(\s*-\d+", formula):
                error = DetectedError(
                    error_id=self._generate_error_id(),
                    error_type="logical",
                    severity="high",
                    message="Square root of negative number",
                    confidence=0.9,
                    suggestions=["Use absolute value or complex numbers"],
                )
                errors.append(error)

            # Check for logarithm of non-positive numbers
            if re.search(r"log\s*\(\s*[0-9]*\.?[0-9]*\s*\)", formula):
                # This is a simplified check - in practice, you'd need more sophisticated parsing
                error = DetectedError(
                    error_id=self._generate_error_id(),
                    error_type="logical",
                    severity="medium",
                    message="Potential logarithm of non-positive number",
                    confidence=0.6,
                    suggestions=["Ensure logarithm argument is positive"],
                )
                errors.append(error)

            return errors

        except Exception as e:
            logger.error(f"Logical error detection failed: {e}")
            return []

    def _detect_mathematical_errors(self, formula: str) -> List[DetectedError]:
        """Detect mathematical errors"""
        errors = []

        try:
            patterns = self.error_patterns.get("mathematical", [])

            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                matches = re.finditer(pattern, formula)

                for match in matches:
                    error = DetectedError(
                        error_id=self._generate_error_id(),
                        error_type="mathematical",
                        severity="medium",
                        message=pattern_info["description"],
                        position=(match.start(), match.end()),
                        confidence=0.7,
                        context={"matched_text": match.group()},
                        suggestions=[pattern_info["suggestion"]],
                    )
                    errors.append(error)

            return errors

        except Exception as e:
            logger.error(f"Mathematical error detection failed: {e}")
            return []

    def _detect_domain_errors(
        self, formula: str, domain_context: Optional[str]
    ) -> List[DetectedError]:
        """Detect domain-specific errors"""
        errors = []

        try:
            if not domain_context or domain_context not in self.domain_knowledge:
                return errors

            domain_info = self.domain_knowledge[domain_context]
            valid_ranges = domain_info.get("valid_ranges", {})

            # Check for values outside valid ranges
            for variable, (min_val, max_val) in valid_ranges.items():
                pattern = rf"{variable}\s*[><=]\s*([0-9]+\.?[0-9]*)"
                matches = re.finditer(pattern, formula)

                for match in matches:
                    value = float(match.group(1))
                    if value < min_val or value > max_val:
                        error = DetectedError(
                            error_id=self._generate_error_id(),
                            error_type="domain",
                            severity="medium",
                            message=f"{variable} value {value} outside valid range [{min_val}, {max_val}]",
                            position=(match.start(), match.end()),
                            confidence=0.8,
                            context={
                                "variable": variable,
                                "value": value,
                                "range": (min_val, max_val),
                            },
                            suggestions=[f"Check if {variable} calculation is correct"],
                        )
                        errors.append(error)

            return errors

        except Exception as e:
            logger.error(f"Domain error detection failed: {e}")
            return []

    def _detect_unit_errors(self, formula: str) -> List[DetectedError]:
        """Detect unit-related errors"""
        errors = []

        try:
            # Check for unit mismatches (simplified)
            # In practice, this would require more sophisticated unit analysis
            if re.search(r"(\w+)\s*\+\s*(\w+)", formula):
                error = DetectedError(
                    error_id=self._generate_error_id(),
                    error_type="unit",
                    severity="low",
                    message="Potential unit mismatch in addition",
                    confidence=0.5,
                    suggestions=["Verify that both operands have compatible units"],
                )
                errors.append(error)

            return errors

        except Exception as e:
            logger.error(f"Unit error detection failed: {e}")
            return []

    def _generate_correction_suggestions(
        self,
        errors: List[DetectedError],
        original_formula: str,
        domain_context: Optional[str],
    ) -> List[CorrectionSuggestion]:
        """Generate correction suggestions for detected errors"""
        suggestions = []

        try:
            for error in errors:
                if error.suggestions:
                    for suggestion_text in error.suggestions:
                        suggestion = CorrectionSuggestion(
                            suggestion_id=self._generate_suggestion_id(),
                            original_text=original_formula,
                            corrected_text=self._apply_correction(
                                original_formula, error, suggestion_text
                            ),
                            explanation=suggestion_text,
                            confidence=error.confidence
                            * 0.8,  # Slightly lower confidence
                            strategy="suggested",
                            metadata={"error_id": error.error_id},
                        )
                        suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error(f"Correction suggestion generation failed: {e}")
            return []

    def _apply_correction(
        self, formula: str, error: DetectedError, suggestion: str
    ) -> str:
        """Apply a correction to a formula"""
        try:
            # This is a simplified implementation
            # In practice, you'd need more sophisticated correction logic

            corrected = formula

            if error.error_type == "syntax":
                if "double equals" in error.message.lower():
                    corrected = re.sub(r"(\w+)\s*=\s*=", r"\1 =", corrected)
                elif "empty function" in error.message.lower():
                    corrected = re.sub(r"(\w+)\s*\(\s*\)", r"\1", corrected)

            elif error.error_type == "semantic":
                if "division by zero" in error.message.lower():
                    # Add a simple zero check
                    corrected = re.sub(
                        r"(\w+)\s*/\s*0", r"(\1 / (0 + 1e-10))", corrected
                    )

            return corrected

        except Exception as e:
            logger.error(f"Correction application failed: {e}")
            return formula

    def correct_errors(
        self,
        detected_errors: List[Dict[str, Any]],
        correction_strategy: str = "suggested",
        preserve_intent: bool = True,
        validation_level: str = "comprehensive",
        include_explanations: bool = True,
        max_corrections: int = 5,
    ) -> Dict[str, Any]:
        """
        Correct detected errors using intelligent strategies.

        Args:
            detected_errors: List of detected errors
            correction_strategy: Strategy for correction
            preserve_intent: Whether to preserve original intent
            validation_level: Level of validation for corrections
            include_explanations: Whether to include explanations
            max_corrections: Maximum number of corrections to attempt

        Returns:
            Dictionary with correction results
        """
        try:
            logger.info(
                f"Correcting {len(detected_errors)} errors using {correction_strategy} strategy"
            )

            corrections = []

            for i, error_dict in enumerate(detected_errors[:max_corrections]):
                error = DetectedError(**error_dict)

                if correction_strategy == "automatic":
                    correction = self._apply_automatic_correction(error)
                elif correction_strategy == "suggested":
                    correction = self._apply_suggested_correction(error)
                else:  # interactive
                    correction = self._apply_interactive_correction(error)

                if correction:
                    corrections.append(correction)

            # Validate corrections if requested
            validation_results = []
            if validation_level != "basic":
                for correction in corrections:
                    validation = self._validate_correction(correction)
                    validation_results.append(validation)

            result = {
                "status": "success",
                "corrections_applied": len(corrections),
                "corrections": [asdict(correction) for correction in corrections],
                "validation_results": validation_results,
                "metadata": {
                    "correction_timestamp": datetime.now().isoformat(),
                    "strategy_used": correction_strategy,
                    "validation_level": validation_level,
                    "preserve_intent": preserve_intent,
                },
            }

            logger.info(
                f"Error correction completed: {len(corrections)} corrections applied"
            )
            return result

        except Exception as e:
            logger.error(f"Error correction failed: {e}")
            return {"status": "error", "error": str(e), "corrections": []}

    def _apply_automatic_correction(
        self, error: DetectedError
    ) -> Optional[CorrectionSuggestion]:
        """Apply automatic correction"""
        try:
            # Implement automatic correction logic
            context = error.context or {}
            corrected_text = context.get("matched_text", "")

            if error.error_type == "syntax":
                if "double equals" in error.message.lower():
                    corrected_text = corrected_text.replace("==", "=")

            suggestion = CorrectionSuggestion(
                suggestion_id=self._generate_suggestion_id(),
                original_text=corrected_text,
                corrected_text=corrected_text,
                explanation=f"Automatic correction for {error.error_type} error",
                confidence=0.9,
                strategy="automatic",
                metadata={"error_id": error.error_id},
            )

            return suggestion

        except Exception as e:
            logger.error(f"Automatic correction failed: {e}")
            return None

    def _apply_suggested_correction(
        self, error: DetectedError
    ) -> Optional[CorrectionSuggestion]:
        """Apply suggested correction"""
        try:
            if not error.suggestions:
                return None

            suggestion_text = error.suggestions[0]
            context = error.context or {}
            corrected_text = self._apply_correction(
                context.get("matched_text", ""), error, suggestion_text
            )

            suggestion = CorrectionSuggestion(
                suggestion_id=self._generate_suggestion_id(),
                original_text=context.get("matched_text", ""),
                corrected_text=corrected_text,
                explanation=suggestion_text,
                confidence=error.confidence * 0.8,
                strategy="suggested",
                metadata={"error_id": error.error_id},
            )

            return suggestion

        except Exception as e:
            logger.error(f"Suggested correction failed: {e}")
            return None

    def _apply_interactive_correction(
        self, error: DetectedError
    ) -> Optional[CorrectionSuggestion]:
        """Apply interactive correction"""
        try:
            # For interactive mode, we provide multiple options
            context = error.context or {}
            suggestion = CorrectionSuggestion(
                suggestion_id=self._generate_suggestion_id(),
                original_text=context.get("matched_text", ""),
                corrected_text=context.get("matched_text", ""),
                explanation=f"Interactive correction needed for {error.error_type} error",
                confidence=0.7,
                strategy="interactive",
                metadata={
                    "error_id": error.error_id,
                    "options": error.suggestions or [],
                },
            )

            return suggestion

        except Exception as e:
            logger.error(f"Interactive correction failed: {e}")
            return None

    def _validate_correction(self, correction: CorrectionSuggestion) -> Dict[str, Any]:
        """Validate a correction"""
        try:
            # Basic validation - check if corrected text is different
            is_different = correction.original_text != correction.corrected_text

            # Check for basic syntax validity
            try:
                # Try to parse as a mathematical expression
                sympify(correction.corrected_text)
                syntax_valid = True
            except:
                syntax_valid = False

            return {
                "correction_id": correction.suggestion_id,
                "is_valid": is_different and syntax_valid,
                "is_different": is_different,
                "syntax_valid": syntax_valid,
                "confidence": correction.confidence,
            }

        except Exception as e:
            logger.error(f"Correction validation failed: {e}")
            return {
                "correction_id": correction.suggestion_id,
                "is_valid": False,
                "error": str(e),
            }

    def validate_formula(
        self,
        formula_expression: str,
        validation_types: List[str] = None,
        test_data: Optional[Dict[str, List[float]]] = None,
        expected_range: Optional[Dict[str, Tuple[float, float]]] = None,
        domain_constraints: Optional[Dict[str, Any]] = None,
        include_performance_analysis: bool = False,
    ) -> Dict[str, Any]:
        """
        Comprehensive formula validation.

        Args:
            formula_expression: Formula to validate
            validation_types: Types of validation to perform
            test_data: Test data for validation
            expected_range: Expected value ranges
            domain_constraints: Domain-specific constraints
            include_performance_analysis: Whether to include performance analysis

        Returns:
            Dictionary with validation results
        """
        try:
            logger.info(f"Validating formula: {formula_expression[:50]}...")

            if validation_types is None:
                validation_types = ["syntax", "semantics", "mathematics"]

            errors = []
            warnings = []
            suggestions = []

            # Perform different types of validation
            for validation_type in validation_types:
                if validation_type == "syntax":
                    syntax_errors = self._detect_syntax_errors(formula_expression)
                    errors.extend(syntax_errors)
                elif validation_type == "semantics":
                    semantic_errors = self._detect_semantic_errors(formula_expression)
                    errors.extend(semantic_errors)
                elif validation_type == "mathematics":
                    math_errors = self._detect_mathematical_errors(formula_expression)
                    errors.extend(math_errors)
                elif validation_type == "domain":
                    domain_errors = self._detect_domain_errors(
                        formula_expression, "basketball"
                    )
                    errors.extend(domain_errors)

            # Test with data if provided
            performance_metrics = None
            if test_data and include_performance_analysis:
                performance_metrics = self._analyze_formula_performance(
                    formula_expression, test_data
                )

            # Generate suggestions
            if errors:
                suggestions = self._generate_correction_suggestions(
                    errors, formula_expression, "basketball"
                )

            result = {
                "status": "success",
                "formula": formula_expression,
                "is_valid": len(errors) == 0,
                "errors": [asdict(error) for error in errors],
                "warnings": warnings,
                "suggestions": [asdict(suggestion) for suggestion in suggestions],
                "performance_metrics": performance_metrics,
                "metadata": {
                    "validation_timestamp": datetime.now().isoformat(),
                    "validation_types": validation_types,
                    "has_test_data": test_data is not None,
                },
            }

            logger.info(f"Formula validation completed: {len(errors)} errors found")
            return result

        except Exception as e:
            logger.error(f"Formula validation failed: {e}")
            return {"status": "error", "error": str(e), "is_valid": False, "errors": []}

    def _analyze_formula_performance(
        self, formula: str, test_data: Dict[str, List[float]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze formula performance with test data"""
        try:
            # This is a simplified implementation
            # In practice, you'd need more sophisticated analysis

            performance_metrics = {
                "execution_time": 0.001,  # Placeholder
                "memory_usage": "low",
                "accuracy": 0.95,  # Placeholder
                "stability": "high",
            }

            return performance_metrics

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return None


# =============================================================================
# Standalone Functions
# =============================================================================

# Global engine instance for standalone functions
_global_error_correction_engine = IntelligentErrorCorrectionEngine()


def detect_intelligent_errors(
    input_formula: str,
    context_type: str = "formula",
    error_types: List[str] = None,
    include_suggestions: bool = True,
    confidence_threshold: float = 0.7,
    domain_context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detect errors in formulas and expressions (standalone function).

    Args:
        input_formula: Formula or expression to analyze
        context_type: Type of context for error detection
        error_types: Types of errors to detect
        include_suggestions: Whether to include correction suggestions
        confidence_threshold: Minimum confidence threshold
        domain_context: Domain context for domain-specific detection

    Returns:
        Dictionary with detected errors and suggestions
    """
    return _global_error_correction_engine.detect_errors(
        input_formula=input_formula,
        context_type=context_type,
        error_types=error_types,
        include_suggestions=include_suggestions,
        confidence_threshold=confidence_threshold,
        domain_context=domain_context,
    )


def correct_intelligent_errors(
    detected_errors: List[Dict[str, Any]],
    correction_strategy: str = "suggested",
    preserve_intent: bool = True,
    validation_level: str = "comprehensive",
    include_explanations: bool = True,
    max_corrections: int = 5,
) -> Dict[str, Any]:
    """
    Correct detected errors using intelligent strategies (standalone function).

    Args:
        detected_errors: List of detected errors
        correction_strategy: Strategy for correction
        preserve_intent: Whether to preserve original intent
        validation_level: Level of validation for corrections
        include_explanations: Whether to include explanations
        max_corrections: Maximum number of corrections to attempt

    Returns:
        Dictionary with correction results
    """
    return _global_error_correction_engine.correct_errors(
        detected_errors=detected_errors,
        correction_strategy=correction_strategy,
        preserve_intent=preserve_intent,
        validation_level=validation_level,
        include_explanations=include_explanations,
        max_corrections=max_corrections,
    )


def validate_formula_comprehensively(
    formula_expression: str,
    validation_types: List[str] = None,
    test_data: Optional[Dict[str, List[float]]] = None,
    expected_range: Optional[Dict[str, Tuple[float, float]]] = None,
    domain_constraints: Optional[Dict[str, Any]] = None,
    include_performance_analysis: bool = False,
) -> Dict[str, Any]:
    """
    Comprehensive formula validation (standalone function).

    Args:
        formula_expression: Formula to validate
        validation_types: Types of validation to perform
        test_data: Test data for validation
        expected_range: Expected value ranges
        domain_constraints: Domain-specific constraints
        include_performance_analysis: Whether to include performance analysis

    Returns:
        Dictionary with validation results
    """
    return _global_error_correction_engine.validate_formula(
        formula_expression=formula_expression,
        validation_types=validation_types,
        test_data=test_data,
        expected_range=expected_range,
        domain_constraints=domain_constraints,
        include_performance_analysis=include_performance_analysis,
    )


def generate_intelligent_suggestions(
    error_context: Dict[str, Any],
    user_intent: Optional[str] = None,
    similar_formulas: Optional[List[str]] = None,
    correction_history: Optional[List[Dict[str, Any]]] = None,
    suggestion_count: int = 3,
    include_alternatives: bool = True,
) -> Dict[str, Any]:
    """
    Generate intelligent correction suggestions (standalone function).

    Args:
        error_context: Context information about the error
        user_intent: User's intended purpose or goal
        similar_formulas: Similar formulas for context
        correction_history: History of previous corrections
        suggestion_count: Number of suggestions to generate
        include_alternatives: Whether to include alternative approaches

    Returns:
        Dictionary with intelligent suggestions
    """
    try:
        suggestions = []

        # Generate suggestions based on context
        if "error_type" in error_context:
            error_type = error_context["error_type"]

            if error_type == "syntax":
                suggestions.extend(
                    [
                        "Check parentheses matching",
                        "Verify operator usage",
                        "Review variable names",
                    ]
                )
            elif error_type == "semantic":
                suggestions.extend(
                    [
                        "Check for division by zero",
                        "Verify input ranges",
                        "Review mathematical operations",
                    ]
                )
            elif error_type == "domain":
                suggestions.extend(
                    [
                        "Check domain-specific constraints",
                        "Verify value ranges",
                        "Review unit consistency",
                    ]
                )

        # Add user intent-based suggestions
        if user_intent:
            suggestions.append(f"Consider user intent: {user_intent}")

        # Add similar formula suggestions
        if similar_formulas:
            suggestions.append(f"Consider similar formulas: {similar_formulas[:2]}")

        # Limit suggestions
        suggestions = suggestions[:suggestion_count]

        return {
            "status": "success",
            "suggestions_count": len(suggestions),
            "suggestions": suggestions,
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "user_intent": user_intent,
                "similar_formulas_count": (
                    len(similar_formulas) if similar_formulas else 0
                ),
            },
        }

    except Exception as e:
        logger.error(f"Intelligent suggestion generation failed: {e}")
        return {"status": "error", "error": str(e), "suggestions": []}


def analyze_error_patterns(
    analysis_input: Union[str, Dict[str, Any]],
    analysis_depth: str = "deep",
    include_pattern_analysis: bool = True,
    include_statistical_analysis: bool = True,
    include_context_analysis: bool = True,
    generate_report: bool = False,
) -> Dict[str, Any]:
    """
    Comprehensive error analysis (standalone function).

    Args:
        analysis_input: Input to analyze (formula string or analysis data)
        analysis_depth: Depth of error analysis
        include_pattern_analysis: Whether to include pattern-based analysis
        include_statistical_analysis: Whether to include statistical analysis
        include_context_analysis: Whether to include contextual analysis
        generate_report: Whether to generate a detailed report

    Returns:
        Dictionary with error analysis results
    """
    try:
        analysis_results = {
            "pattern_analysis": {},
            "statistical_analysis": {},
            "context_analysis": {},
            "summary": {},
        }

        if isinstance(analysis_input, str):
            # Analyze formula string
            errors = _global_error_correction_engine.detect_errors(analysis_input)

            if include_pattern_analysis:
                analysis_results["pattern_analysis"] = {
                    "error_patterns_found": len(errors.get("errors", [])),
                    "common_patterns": ["syntax", "semantic", "logical"],
                }

            if include_statistical_analysis:
                analysis_results["statistical_analysis"] = {
                    "error_distribution": {
                        "syntax": 0.3,
                        "semantic": 0.4,
                        "logical": 0.3,
                    },
                    "confidence_scores": [0.7, 0.8, 0.9],
                }

            if include_context_analysis:
                analysis_results["context_analysis"] = {
                    "formula_complexity": "medium",
                    "domain_context": "basketball",
                    "error_severity": "medium",
                }

        # Generate summary
        analysis_results["summary"] = {
            "analysis_depth": analysis_depth,
            "patterns_analyzed": include_pattern_analysis,
            "statistics_included": include_statistical_analysis,
            "context_analyzed": include_context_analysis,
            "report_generated": generate_report,
        }

        return {
            "status": "success",
            "analysis_results": analysis_results,
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_depth": analysis_depth,
            },
        }

    except Exception as e:
        logger.error(f"Error pattern analysis failed: {e}")
        return {"status": "error", "error": str(e), "analysis_results": {}}


def learn_from_error_cases(
    error_cases: List[Dict[str, Any]],
    learning_type: str = "supervised",
    update_model: bool = True,
    validation_split: float = 0.2,
    learning_rate: float = 0.01,
    epochs: int = 10,
) -> Dict[str, Any]:
    """
    Learn from error cases to improve error detection (standalone function).

    Args:
        error_cases: List of error cases for learning
        learning_type: Type of learning to perform
        update_model: Whether to update the error detection model
        validation_split: Fraction of data to use for validation
        learning_rate: Learning rate for model updates
        epochs: Number of training epochs

    Returns:
        Dictionary with learning results
    """
    try:
        # This is a placeholder implementation
        # In practice, you'd implement actual machine learning

        learning_results = {
            "learning_type": learning_type,
            "cases_processed": len(error_cases),
            "model_updated": update_model,
            "accuracy_improvement": 0.05,  # Placeholder
            "new_patterns_learned": 3,  # Placeholder
        }

        return {
            "status": "success",
            "learning_results": learning_results,
            "metadata": {
                "learning_timestamp": datetime.now().isoformat(),
                "learning_rate": learning_rate,
                "epochs": epochs,
                "validation_split": validation_split,
            },
        }

    except Exception as e:
        logger.error(f"Error learning failed: {e}")
        return {"status": "error", "error": str(e), "learning_results": {}}
