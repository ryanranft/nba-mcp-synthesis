"""
Formula Validation System Module

Author: NBA MCP Server Team
Date: 2025-01-13
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import sympy as sp
from sympy import latex, simplify, expand, factor, diff, integrate, solve
from sympy.parsing.sympy_parser import parse_expr
import json
import uuid

# Import other modules
from .formula_intelligence import FormulaIntelligence
from .formula_extractor import FormulaExtractor
from .algebra_helper import get_sports_formula

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status levels"""

    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    INCONSISTENT = "inconsistent"
    UNKNOWN = "unknown"


class ValidationType(Enum):
    """Types of validation checks"""

    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    CROSS_REFERENCE = "cross_reference"
    MATHEMATICAL = "mathematical"
    DOMAIN_SPECIFIC = "domain_specific"
    PERFORMANCE = "performance"


@dataclass
class ValidationResult:
    """Result of a validation check"""

    validation_id: str
    formula_id: str
    validation_type: ValidationType
    status: ValidationStatus
    score: float  # 0.0 to 1.0
    message: str
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime
    source: Optional[str] = None


@dataclass
class FormulaReference:
    """Reference data for formula validation"""

    formula_id: str
    name: str
    formula: str
    source: str
    page: Optional[str] = None
    expected_result: Optional[float] = None
    test_data: Optional[Dict[str, float]] = None
    description: Optional[str] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report"""

    report_id: str
    formula_id: str
    overall_status: ValidationStatus
    overall_score: float
    validations: List[ValidationResult]
    summary: str
    recommendations: List[str]
    created_at: datetime
    updated_at: datetime


class FormulaValidationEngine:
    """
    Advanced formula validation system that verifies accuracy,
    consistency, and correctness of sports analytics formulas.
    """

    def __init__(self):
        """Initialize the validation engine"""
        self.formula_intelligence = FormulaIntelligence()
        self.formula_extractor = FormulaExtractor()

        # Known formula references for validation
        self.formula_references = self._initialize_formula_references()

        # Validation rules and thresholds
        self.validation_rules = self._initialize_validation_rules()

        logger.info("FormulaValidationEngine initialized")

    def _initialize_formula_references(self) -> Dict[str, FormulaReference]:
        """Initialize known formula references for validation"""
        references = {
            "per": FormulaReference(
                formula_id="per",
                name="Player Efficiency Rating",
                formula="(FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
                source="Basketball on Paper",
                page="Chapter 4",
                test_data={
                    "FGM": 10,
                    "STL": 2,
                    "3PM": 3,
                    "FTM": 5,
                    "BLK": 1,
                    "OREB": 2,
                    "AST": 8,
                    "DREB": 6,
                    "PF": 3,
                    "FTA": 6,
                    "FGA": 18,
                    "TOV": 3,
                    "MP": 35,
                },
                expected_result=25.2,  # Approximate expected PER
                description="Standard PER calculation with typical player stats",
            ),
            "true_shooting": FormulaReference(
                formula_id="true_shooting",
                name="True Shooting Percentage",
                formula="PTS / (2 * (FGA + 0.44 * FTA))",
                source="Basketball on Paper",
                page="Chapter 3",
                test_data={"PTS": 25, "FGA": 20, "FTA": 5},
                expected_result=0.568,  # 56.8% TS%
                description="True shooting percentage calculation",
            ),
            "usage_rate": FormulaReference(
                formula_id="usage_rate",
                name="Usage Rate",
                formula="((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
                source="Basketball on Paper",
                page="Chapter 5",
                test_data={
                    "FGA": 18,
                    "FTA": 6,
                    "TOV": 3,
                    "MP": 35,
                    "TM_MP": 240,
                    "TM_FGA": 90,
                    "TM_FTA": 25,
                    "TM_TOV": 12,
                },
                expected_result=28.5,  # Approximate usage rate
                description="Usage rate calculation",
            ),
            "effective_fg": FormulaReference(
                formula_id="effective_fg",
                name="Effective Field Goal Percentage",
                formula="(FGM + 0.5 * 3PM) / FGA",
                source="Basketball on Paper",
                page="Chapter 3",
                test_data={"FGM": 10, "3PM": 3, "FGA": 20},
                expected_result=0.575,  # 57.5% eFG%
                description="Effective field goal percentage",
            ),
            "net_rating": FormulaReference(
                formula_id="net_rating",
                name="Net Rating",
                formula="ORtg - DRtg",
                source="Basketball on Paper",
                page="Chapter 6",
                test_data={"ORtg": 115.2, "DRtg": 108.5},
                expected_result=6.7,
                description="Net rating calculation",
            ),
        }
        return references

    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules and thresholds"""
        return {
            "accuracy_threshold": 0.95,  # 95% accuracy required
            "consistency_threshold": 0.90,  # 90% consistency required
            "mathematical_tolerance": 0.01,  # 1% mathematical tolerance
            "domain_tolerance": 0.05,  # 5% domain-specific tolerance
            "performance_threshold": 1.0,  # 1 second max calculation time
            "required_validations": [
                ValidationType.MATHEMATICAL,
                ValidationType.ACCURACY,
                ValidationType.CONSISTENCY,
            ],
        }

    def validate_formula(
        self,
        formula: str,
        formula_id: Optional[str] = None,
        test_data: Optional[Dict[str, float]] = None,
        validation_types: Optional[List[ValidationType]] = None,
    ) -> ValidationReport:
        """
        Perform comprehensive validation of a formula.

        Args:
            formula: Formula string to validate
            formula_id: Optional identifier for the formula
            test_data: Optional test data for validation
            validation_types: Types of validation to perform

        Returns:
            ValidationReport with comprehensive validation results
        """
        report_id = str(uuid.uuid4())
        now = datetime.now()

        if formula_id is None:
            formula_id = f"formula_{hash(formula)}"

        if validation_types is None:
            validation_types = self.validation_rules["required_validations"]

        validations = []

        # Perform each type of validation
        for validation_type in validation_types:
            try:
                if validation_type == ValidationType.MATHEMATICAL:
                    result = self._validate_mathematical(formula, formula_id)
                elif validation_type == ValidationType.ACCURACY:
                    result = self._validate_accuracy(formula, formula_id, test_data)
                elif validation_type == ValidationType.CONSISTENCY:
                    result = self._validate_consistency(formula, formula_id)
                elif validation_type == ValidationType.CROSS_REFERENCE:
                    result = self._validate_cross_reference(formula, formula_id)
                elif validation_type == ValidationType.DOMAIN_SPECIFIC:
                    result = self._validate_domain_specific(formula, formula_id)
                elif validation_type == ValidationType.PERFORMANCE:
                    result = self._validate_performance(formula, formula_id, test_data)
                else:
                    continue

                validations.append(result)

            except Exception as e:
                logger.error(f"Validation error for {validation_type.value}: {e}")
                error_result = ValidationResult(
                    validation_id=str(uuid.uuid4()),
                    formula_id=formula_id,
                    validation_type=validation_type,
                    status=ValidationStatus.ERROR,
                    score=0.0,
                    message=f"Validation failed: {str(e)}",
                    details={"error": str(e)},
                    recommendations=["Fix formula syntax", "Check input data"],
                    timestamp=now,
                )
                validations.append(error_result)

        # Calculate overall status and score
        overall_status, overall_score = self._calculate_overall_status(validations)

        # Generate summary and recommendations
        summary = self._generate_summary(validations)
        recommendations = self._generate_recommendations(validations)

        report = ValidationReport(
            report_id=report_id,
            formula_id=formula_id,
            overall_status=overall_status,
            overall_score=overall_score,
            validations=validations,
            summary=summary,
            recommendations=recommendations,
            created_at=now,
            updated_at=now,
        )

        logger.info(f"Generated validation report {report_id} for formula {formula_id}")
        return report

    def _validate_mathematical(self, formula: str, formula_id: str) -> ValidationResult:
        """Validate mathematical correctness of formula"""
        try:
            # Parse the formula
            expr = parse_expr(formula, evaluate=False)

            # Check for mathematical validity
            issues = []
            score = 1.0

            # Check for division by zero potential
            if "/" in formula:
                # Look for denominators that could be zero
                if "MP" in formula and "MP" not in formula.split("/")[0]:
                    issues.append("Potential division by zero with MP")
                    score -= 0.1

            # Check for negative values in square roots
            if "sqrt" in formula.lower():
                issues.append("Square root operations may produce complex numbers")
                score -= 0.1

            # Check for reasonable mathematical operations
            if formula.count("(") != formula.count(")"):
                issues.append("Unmatched parentheses")
                score -= 0.3

            status = (
                ValidationStatus.VALID if score >= 0.9 else ValidationStatus.WARNING
            )

            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.MATHEMATICAL,
                status=status,
                score=max(0.0, score),
                message=f"Mathematical validation {'passed' if status == ValidationStatus.VALID else 'has warnings'}",
                details={
                    "parsed_expression": str(expr),
                    "issues": issues,
                    "latex": latex(expr),
                },
                recommendations=(
                    ["Fix mathematical issues"]
                    if issues
                    else ["Formula is mathematically sound"]
                ),
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.MATHEMATICAL,
                status=ValidationStatus.ERROR,
                score=0.0,
                message=f"Mathematical validation failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Fix formula syntax", "Check mathematical notation"],
                timestamp=datetime.now(),
            )

    def _validate_accuracy(
        self,
        formula: str,
        formula_id: str,
        test_data: Optional[Dict[str, float]] = None,
    ) -> ValidationResult:
        """Validate formula accuracy against known results"""
        try:
            # Get reference data if available
            reference = self.formula_references.get(formula_id)

            if reference and reference.test_data:
                test_data = reference.test_data
                expected_result = reference.expected_result
            elif test_data:
                expected_result = None
            else:
                return ValidationResult(
                    validation_id=str(uuid.uuid4()),
                    formula_id=formula_id,
                    validation_type=ValidationType.ACCURACY,
                    status=ValidationStatus.UNKNOWN,
                    score=0.5,
                    message="No test data available for accuracy validation",
                    details={"test_data_available": False},
                    recommendations=["Provide test data for accuracy validation"],
                    timestamp=datetime.now(),
                )

            # Calculate formula result
            expr = parse_expr(formula, evaluate=False)

            # Check if all variables are provided
            missing_vars = [
                str(s) for s in expr.free_symbols if str(s) not in test_data
            ]
            if missing_vars:
                return ValidationResult(
                    validation_id=str(uuid.uuid4()),
                    formula_id=formula_id,
                    validation_type=ValidationType.ACCURACY,
                    status=ValidationStatus.ERROR,
                    score=0.0,
                    message=f"Missing variables for accuracy validation: {', '.join(missing_vars)}",
                    details={"missing_variables": missing_vars},
                    recommendations=["Provide values for all formula variables"],
                    timestamp=datetime.now(),
                )

            # Calculate result
            substituted_expr = expr.subs(
                {sp.Symbol(k): v for k, v in test_data.items()}
            )
            calculated_result = float(substituted_expr)

            # Compare with expected result if available
            if expected_result is not None:
                tolerance = self.validation_rules["accuracy_threshold"]
                error_percent = (
                    abs(calculated_result - expected_result) / expected_result
                )

                if error_percent <= (1 - tolerance):
                    status = ValidationStatus.VALID
                    score = 1.0 - error_percent
                    message = f"Accuracy validation passed (error: {error_percent:.2%})"
                else:
                    status = ValidationStatus.ERROR
                    score = max(0.0, 1.0 - error_percent)
                    message = f"Accuracy validation failed (error: {error_percent:.2%})"

                details = {
                    "calculated_result": calculated_result,
                    "expected_result": expected_result,
                    "error_percent": error_percent,
                    "test_data": test_data,
                }

                recommendations = (
                    ["Formula accuracy is acceptable"]
                    if status == ValidationStatus.VALID
                    else [
                        "Check formula implementation",
                        "Verify test data accuracy",
                        "Compare with reference sources",
                    ]
                )
            else:
                status = ValidationStatus.WARNING
                score = 0.8
                message = (
                    "Accuracy validation completed (no reference result available)"
                )
                details = {
                    "calculated_result": calculated_result,
                    "test_data": test_data,
                }
                recommendations = [
                    "Provide reference result for complete accuracy validation"
                ]

            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.ACCURACY,
                status=status,
                score=score,
                message=message,
                details=details,
                recommendations=recommendations,
                timestamp=datetime.now(),
                source=reference.source if reference else None,
            )

        except Exception as e:
            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.ACCURACY,
                status=ValidationStatus.ERROR,
                score=0.0,
                message=f"Accuracy validation failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Fix formula syntax", "Check test data format"],
                timestamp=datetime.now(),
            )

    def _validate_consistency(self, formula: str, formula_id: str) -> ValidationResult:
        """Validate formula consistency across different implementations"""
        try:
            # Get reference formula if available
            reference = self.formula_references.get(formula_id)

            if not reference:
                return ValidationResult(
                    validation_id=str(uuid.uuid4()),
                    formula_id=formula_id,
                    validation_type=ValidationType.CONSISTENCY,
                    status=ValidationStatus.UNKNOWN,
                    score=0.5,
                    message="No reference formula available for consistency validation",
                    details={"reference_available": False},
                    recommendations=[
                        "Add reference formula for consistency validation"
                    ],
                    timestamp=datetime.now(),
                )

            # Compare formulas (simplified comparison)
            ref_formula = reference.formula
            consistency_score = self._calculate_formula_similarity(formula, ref_formula)

            threshold = self.validation_rules["consistency_threshold"]

            if consistency_score >= threshold:
                status = ValidationStatus.VALID
                message = f"Consistency validation passed (similarity: {consistency_score:.2%})"
            else:
                status = ValidationStatus.INCONSISTENT
                message = f"Consistency validation failed (similarity: {consistency_score:.2%})"

            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.CONSISTENCY,
                status=status,
                score=consistency_score,
                message=message,
                details={
                    "reference_formula": ref_formula,
                    "test_formula": formula,
                    "similarity_score": consistency_score,
                    "reference_source": reference.source,
                },
                recommendations=(
                    ["Formula is consistent with reference"]
                    if status == ValidationStatus.VALID
                    else [
                        "Review formula implementation",
                        "Check for calculation differences",
                        "Verify formula source",
                    ]
                ),
                timestamp=datetime.now(),
                source=reference.source,
            )

        except Exception as e:
            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.CONSISTENCY,
                status=ValidationStatus.ERROR,
                score=0.0,
                message=f"Consistency validation failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Fix formula syntax", "Check reference data"],
                timestamp=datetime.now(),
            )

    def _validate_cross_reference(
        self, formula: str, formula_id: str
    ) -> ValidationResult:
        """Validate formula against multiple sources"""
        try:
            # This would typically check against multiple books/sources
            # For now, we'll implement a basic version

            cross_ref_sources = []
            consistency_scores = []

            # Check against known references
            for ref_id, reference in self.formula_references.items():
                if ref_id != formula_id and reference.formula:
                    similarity = self._calculate_formula_similarity(
                        formula, reference.formula
                    )
                    if similarity > 0.5:  # Significant similarity
                        cross_ref_sources.append(
                            {
                                "source": reference.source,
                                "formula_id": ref_id,
                                "similarity": similarity,
                            }
                        )
                        consistency_scores.append(similarity)

            if not cross_ref_sources:
                return ValidationResult(
                    validation_id=str(uuid.uuid4()),
                    formula_id=formula_id,
                    validation_type=ValidationType.CROSS_REFERENCE,
                    status=ValidationStatus.UNKNOWN,
                    score=0.5,
                    message="No cross-reference sources found",
                    details={"cross_reference_sources": []},
                    recommendations=["Add more reference sources for cross-validation"],
                    timestamp=datetime.now(),
                )

            avg_consistency = sum(consistency_scores) / len(consistency_scores)
            threshold = self.validation_rules["consistency_threshold"]

            if avg_consistency >= threshold:
                status = ValidationStatus.VALID
                message = f"Cross-reference validation passed (avg similarity: {avg_consistency:.2%})"
            else:
                status = ValidationStatus.INCONSISTENT
                message = f"Cross-reference validation failed (avg similarity: {avg_consistency:.2%})"

            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.CROSS_REFERENCE,
                status=status,
                score=avg_consistency,
                message=message,
                details={
                    "cross_reference_sources": cross_ref_sources,
                    "average_consistency": avg_consistency,
                    "total_sources": len(cross_ref_sources),
                },
                recommendations=(
                    ["Formula is consistent across sources"]
                    if status == ValidationStatus.VALID
                    else [
                        "Review formula variations",
                        "Check source reliability",
                        "Consider formula standardization",
                    ]
                ),
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.CROSS_REFERENCE,
                status=ValidationStatus.ERROR,
                score=0.0,
                message=f"Cross-reference validation failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Fix validation system", "Check reference data"],
                timestamp=datetime.now(),
            )

    def _validate_domain_specific(
        self, formula: str, formula_id: str
    ) -> ValidationResult:
        """Validate domain-specific constraints for sports analytics"""
        try:
            issues = []
            score = 1.0

            # Check for reasonable ranges
            if "PER" in formula_id.upper() or "EFFICIENCY" in formula_id.upper():
                # PER should typically be between 0 and 50
                if not any(var in formula for var in ["MP", "MINUTES"]):
                    issues.append("PER calculation should include minutes played")
                    score -= 0.2

            # Check for percentage calculations
            if "%" in formula_id or "PERCENTAGE" in formula_id.upper():
                # Percentage formulas should result in values 0-1 or 0-100
                if "100" not in formula and "/" not in formula:
                    issues.append("Percentage calculation may be missing division")
                    score -= 0.1

            # Check for shooting formulas
            if any(
                term in formula_id.upper() for term in ["SHOOTING", "FG", "3P", "FT"]
            ):
                if "FGA" not in formula and "ATTEMPTS" not in formula:
                    issues.append("Shooting formula should include attempts")
                    score -= 0.2

            # Check for defensive formulas
            if "DEFENSIVE" in formula_id.upper() or "DEF" in formula_id.upper():
                if not any(term in formula for term in ["OPP", "OPPONENT", "ALLOWED"]):
                    issues.append("Defensive formula should consider opponent stats")
                    score -= 0.2

            status = (
                ValidationStatus.VALID if score >= 0.8 else ValidationStatus.WARNING
            )

            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.DOMAIN_SPECIFIC,
                status=status,
                score=max(0.0, score),
                message=f"Domain-specific validation {'passed' if status == ValidationStatus.VALID else 'has warnings'}",
                details={
                    "issues": issues,
                    "domain_checks": [
                        "PER calculation includes minutes",
                        "Percentage calculation includes division",
                        "Shooting formula includes attempts",
                        "Defensive formula considers opponents",
                    ],
                },
                recommendations=(
                    ["Address domain-specific issues"]
                    if issues
                    else ["Formula follows domain conventions"]
                ),
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.DOMAIN_SPECIFIC,
                status=ValidationStatus.ERROR,
                score=0.0,
                message=f"Domain-specific validation failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Fix domain validation", "Check formula structure"],
                timestamp=datetime.now(),
            )

    def _validate_performance(
        self,
        formula: str,
        formula_id: str,
        test_data: Optional[Dict[str, float]] = None,
    ) -> ValidationResult:
        """Validate formula performance and efficiency"""
        try:
            import time

            if not test_data:
                test_data = {"x": 1.0, "y": 2.0, "z": 3.0}  # Default test data

            # Measure calculation time
            start_time = time.time()

            try:
                expr = parse_expr(formula, evaluate=False)
                substituted_expr = expr.subs(
                    {sp.Symbol(k): v for k, v in test_data.items()}
                )
                result = float(substituted_expr)
                calculation_time = time.time() - start_time
            except Exception as e:
                return ValidationResult(
                    validation_id=str(uuid.uuid4()),
                    formula_id=formula_id,
                    validation_type=ValidationType.PERFORMANCE,
                    status=ValidationStatus.ERROR,
                    score=0.0,
                    message=f"Performance validation failed: {str(e)}",
                    details={"error": str(e)},
                    recommendations=["Fix formula syntax for performance testing"],
                    timestamp=datetime.now(),
                )

            threshold = self.validation_rules["performance_threshold"]

            if calculation_time <= threshold:
                status = ValidationStatus.VALID
                score = 1.0 - (calculation_time / threshold)
                message = (
                    f"Performance validation passed (time: {calculation_time:.3f}s)"
                )
            else:
                status = ValidationStatus.WARNING
                score = max(0.0, 1.0 - (calculation_time / threshold))
                message = (
                    f"Performance validation warning (time: {calculation_time:.3f}s)"
                )

            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.PERFORMANCE,
                status=status,
                score=score,
                message=message,
                details={
                    "calculation_time": calculation_time,
                    "threshold": threshold,
                    "test_data": test_data,
                    "result": result,
                },
                recommendations=(
                    ["Formula performance is acceptable"]
                    if status == ValidationStatus.VALID
                    else [
                        "Consider optimizing formula",
                        "Check for complex operations",
                        "Review calculation efficiency",
                    ]
                ),
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                validation_id=str(uuid.uuid4()),
                formula_id=formula_id,
                validation_type=ValidationType.PERFORMANCE,
                status=ValidationStatus.ERROR,
                score=0.0,
                message=f"Performance validation failed: {str(e)}",
                details={"error": str(e)},
                recommendations=[
                    "Fix performance validation",
                    "Check formula complexity",
                ],
                timestamp=datetime.now(),
            )

    def _calculate_formula_similarity(self, formula1: str, formula2: str) -> float:
        """Calculate similarity between two formulas"""
        try:
            # Simple similarity based on common terms and structure
            terms1 = set(formula1.replace(" ", "").split("+"))
            terms2 = set(formula2.replace(" ", "").split("+"))

            if not terms1 and not terms2:
                return 1.0
            if not terms1 or not terms2:
                return 0.0

            intersection = len(terms1.intersection(terms2))
            union = len(terms1.union(terms2))

            return intersection / union if union > 0 else 0.0

        except Exception:
            return 0.0

    def _calculate_overall_status(
        self, validations: List[ValidationResult]
    ) -> Tuple[ValidationStatus, float]:
        """Calculate overall validation status and score"""
        if not validations:
            return ValidationStatus.UNKNOWN, 0.0

        # Weight different validation types
        weights = {
            ValidationType.MATHEMATICAL: 0.3,
            ValidationType.ACCURACY: 0.3,
            ValidationType.CONSISTENCY: 0.2,
            ValidationType.CROSS_REFERENCE: 0.1,
            ValidationType.DOMAIN_SPECIFIC: 0.05,
            ValidationType.PERFORMANCE: 0.05,
        }

        weighted_score = 0.0
        total_weight = 0.0

        for validation in validations:
            weight = weights.get(validation.validation_type, 0.1)
            weighted_score += validation.score * weight
            total_weight += weight

        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0

        # Determine overall status
        if overall_score >= 0.9:
            status = ValidationStatus.VALID
        elif overall_score >= 0.7:
            status = ValidationStatus.WARNING
        elif overall_score >= 0.5:
            status = ValidationStatus.INCONSISTENT
        else:
            status = ValidationStatus.ERROR

        return status, overall_score

    def _generate_summary(self, validations: List[ValidationResult]) -> str:
        """Generate validation summary"""
        if not validations:
            return "No validations performed"

        status_counts = {}
        for validation in validations:
            status = validation.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        summary_parts = []
        for status, count in status_counts.items():
            summary_parts.append(f"{count} {status}")

        return f"Validation completed: {', '.join(summary_parts)}"

    def _generate_recommendations(
        self, validations: List[ValidationResult]
    ) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []

        # Collect recommendations from all validations
        for validation in validations:
            recommendations.extend(validation.recommendations)

        # Remove duplicates and prioritize
        unique_recommendations = list(set(recommendations))

        # Prioritize error-related recommendations
        error_recommendations = [
            r
            for r in unique_recommendations
            if any(word in r.lower() for word in ["fix", "error", "failed"])
        ]
        warning_recommendations = [
            r
            for r in unique_recommendations
            if any(word in r.lower() for word in ["check", "review", "consider"])
        ]
        other_recommendations = [
            r
            for r in unique_recommendations
            if r not in error_recommendations + warning_recommendations
        ]

        return error_recommendations + warning_recommendations + other_recommendations

    def add_formula_reference(self, reference: FormulaReference) -> bool:
        """Add a new formula reference for validation"""
        try:
            self.formula_references[reference.formula_id] = reference
            logger.info(f"Added formula reference: {reference.formula_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add formula reference: {e}")
            return False

    def get_formula_references(self) -> Dict[str, FormulaReference]:
        """Get all formula references"""
        return self.formula_references

    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules and thresholds"""
        return self.validation_rules
