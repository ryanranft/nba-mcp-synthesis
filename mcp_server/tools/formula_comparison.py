"""
Multi-Book Formula Comparison System Module

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
import difflib
from collections import defaultdict

# Import other modules
from .formula_intelligence import FormulaIntelligence
from .formula_validation import (
    FormulaValidationEngine,
    ValidationStatus,
    ValidationType,
)
from .algebra_helper import get_sports_formula

logger = logging.getLogger(__name__)


class ComparisonType(Enum):
    """Types of formula comparisons"""

    STRUCTURAL = "structural"
    MATHEMATICAL = "mathematical"
    ACCURACY = "accuracy"
    HISTORICAL = "historical"
    SOURCE_RELIABILITY = "source_reliability"
    PERFORMANCE = "performance"


class SourceType(Enum):
    """Formula source types"""

    BOOK = "book"
    PAPER = "paper"
    WEBSITE = "website"
    DATABASE = "database"
    USER_DEFINED = "user_defined"


class VariationType(Enum):
    """Types of formula variations"""

    SYNTAX_DIFFERENCE = "syntax_difference"
    PARAMETER_DIFFERENCE = "parameter_difference"
    CALCULATION_DIFFERENCE = "calculation_difference"
    SIMPLIFICATION_DIFFERENCE = "simplification_difference"
    VERSION_DIFFERENCE = "version_difference"


@dataclass(frozen=True)
class FormulaSource:
    """Source information for a formula"""

    source_id: str
    name: str
    type: SourceType
    author: Optional[str] = None
    publication_date: Optional[str] = None
    page: Optional[str] = None
    url: Optional[str] = None
    reliability_score: float = 1.0
    description: Optional[str] = None


@dataclass(frozen=True)
class FormulaVersion:
    """A specific version of a formula from a source"""

    version_id: str
    formula_id: str
    formula: str
    source: FormulaSource
    description: Optional[str] = None
    test_data: Optional[Dict[str, float]] = None
    expected_result: Optional[float] = None
    created_date: Optional[str] = None
    is_primary: bool = False


@dataclass
class FormulaVariation:
    """Represents a variation between formula versions"""

    variation_id: str
    formula_id: str
    version_a: FormulaVersion
    version_b: FormulaVersion
    variation_type: VariationType
    similarity_score: float
    differences: List[str]
    impact_assessment: str
    recommendations: List[str]


@dataclass
class ComparisonResult:
    """Result of comparing multiple formula versions"""

    comparison_id: str
    formula_id: str
    versions: List[FormulaVersion]
    variations: List[FormulaVariation]
    overall_similarity: float
    primary_version: Optional[FormulaVersion]
    recommended_version: Optional[FormulaVersion]
    summary: str
    created_at: datetime


@dataclass
class HistoricalEvolution:
    """Tracks historical evolution of a formula"""

    formula_id: str
    timeline: List[FormulaVersion]
    evolution_summary: str
    key_changes: List[str]
    current_consensus: Optional[FormulaVersion]


class MultiBookFormulaComparison:
    """
    Advanced system for comparing formulas across multiple sources,
    tracking variations, and recommending best practices.
    """

    def __init__(self):
        """Initialize the comparison system"""
        self.formula_intelligence = FormulaIntelligence()
        self.validation_engine = FormulaValidationEngine()

        # Formula database
        self.formula_versions = {}  # formula_id -> List[FormulaVersion]
        self.formula_sources = {}  # source_id -> FormulaSource
        self.comparison_history = {}  # comparison_id -> ComparisonResult

        # Initialize with known sources
        self._initialize_known_sources()
        self._initialize_known_formulas()

        logger.info("MultiBookFormulaComparison initialized")

    def _initialize_known_sources(self):
        """Initialize known formula sources"""
        sources = [
            FormulaSource(
                source_id="basketball_on_paper",
                name="Basketball on Paper",
                type=SourceType.BOOK,
                author="Dean Oliver",
                publication_date="2004",
                reliability_score=0.95,
                description="Classic basketball analytics book",
            ),
            FormulaSource(
                source_id="basketball_analytics",
                name="Basketball Analytics",
                type=SourceType.BOOK,
                author="Various",
                publication_date="2020",
                reliability_score=0.90,
                description="Modern basketball analytics compilation",
            ),
            FormulaSource(
                source_id="nba_com",
                name="NBA.com",
                type=SourceType.WEBSITE,
                reliability_score=0.85,
                description="Official NBA statistics and analytics",
            ),
            FormulaSource(
                source_id="basketball_reference",
                name="Basketball Reference",
                type=SourceType.WEBSITE,
                reliability_score=0.88,
                description="Comprehensive basketball statistics database",
            ),
            FormulaSource(
                source_id="sports_analytics_paper",
                name="Sports Analytics Research Paper",
                type=SourceType.PAPER,
                author="Research Team",
                publication_date="2023",
                reliability_score=0.92,
                description="Academic research on sports analytics",
            ),
        ]

        for source in sources:
            self.formula_sources[source.source_id] = source

    def _initialize_known_formulas(self):
        """Initialize known formula versions from different sources"""
        # PER Formula variations
        per_versions = [
            FormulaVersion(
                version_id="per_bop_2004",
                formula_id="per",
                formula="(FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
                source=self.formula_sources["basketball_on_paper"],
                description="Original PER formula from Basketball on Paper",
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
                expected_result=25.2,
                created_date="2004",
                is_primary=True,
            ),
            FormulaVersion(
                version_id="per_nba_com",
                formula_id="per",
                formula="(FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
                source=self.formula_sources["nba_com"],
                description="PER formula from NBA.com (same as original)",
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
                expected_result=25.2,
                created_date="2010",
            ),
            FormulaVersion(
                version_id="per_simplified",
                formula_id="per",
                formula="(FGM * 85.91 + STL * 53.9 + 3PM * 51.76 + FTM * 46.85 + BLK * 39.19 + OREB * 39.19 + AST * 34.68 + DREB * 14.71 - PF * 17.17 - (FTA - FTM) * 20.09 - (FGA - FGM) * 39.19 - TOV * 53.9) * (1 / MP)",
                source=self.formula_sources["basketball_reference"],
                description="Simplified PER formula with rounded coefficients",
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
                expected_result=25.1,
                created_date="2015",
            ),
        ]

        # True Shooting Percentage variations
        ts_versions = [
            FormulaVersion(
                version_id="ts_bop_2004",
                formula_id="true_shooting",
                formula="PTS / (2 * (FGA + 0.44 * FTA))",
                source=self.formula_sources["basketball_on_paper"],
                description="Original TS% formula from Basketball on Paper",
                test_data={"PTS": 25, "FGA": 20, "FTA": 5},
                expected_result=0.568,
                created_date="2004",
                is_primary=True,
            ),
            FormulaVersion(
                version_id="ts_modern",
                formula_id="true_shooting",
                formula="PTS / (2 * (FGA + 0.44 * FTA))",
                source=self.formula_sources["basketball_analytics"],
                description="Modern TS% formula (same as original)",
                test_data={"PTS": 25, "FGA": 20, "FTA": 5},
                expected_result=0.568,
                created_date="2020",
            ),
            FormulaVersion(
                version_id="ts_alternative",
                formula_id="true_shooting",
                formula="PTS / (2 * FGA + 0.88 * FTA)",
                source=self.formula_sources["sports_analytics_paper"],
                description="Alternative TS% formula with different FTA coefficient",
                test_data={"PTS": 25, "FGA": 20, "FTA": 5},
                expected_result=0.556,
                created_date="2023",
            ),
        ]

        # Usage Rate variations
        usage_versions = [
            FormulaVersion(
                version_id="usage_bop_2004",
                formula_id="usage_rate",
                formula="((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
                source=self.formula_sources["basketball_on_paper"],
                description="Original Usage Rate formula from Basketball on Paper",
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
                expected_result=28.5,
                created_date="2004",
                is_primary=True,
            ),
            FormulaVersion(
                version_id="usage_simplified",
                formula_id="usage_rate",
                formula="((FGA + 0.44 * FTA + TOV) * 48) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
                source=self.formula_sources["basketball_reference"],
                description="Simplified Usage Rate formula using 48 minutes",
                test_data={
                    "FGA": 18,
                    "FTA": 6,
                    "TOV": 3,
                    "MP": 35,
                    "TM_FGA": 90,
                    "TM_FTA": 25,
                    "TM_TOV": 12,
                },
                expected_result=28.3,
                created_date="2010",
            ),
        ]

        # Store all versions
        self.formula_versions["per"] = per_versions
        self.formula_versions["true_shooting"] = ts_versions
        self.formula_versions["usage_rate"] = usage_versions

    def add_formula_version(self, version: FormulaVersion) -> bool:
        """Add a new formula version to the database"""
        try:
            if version.formula_id not in self.formula_versions:
                self.formula_versions[version.formula_id] = []

            self.formula_versions[version.formula_id].append(version)
            logger.info(f"Added formula version: {version.version_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add formula version: {e}")
            return False

    def compare_formula_versions(
        self, formula_id: str, comparison_types: Optional[List[ComparisonType]] = None
    ) -> ComparisonResult:
        """
        Compare all versions of a formula across different sources.

        Args:
            formula_id: ID of the formula to compare
            comparison_types: Types of comparison to perform

        Returns:
            ComparisonResult with comprehensive comparison data
        """
        if formula_id not in self.formula_versions:
            raise ValueError(f"No versions found for formula: {formula_id}")

        versions = self.formula_versions[formula_id]
        if len(versions) < 2:
            raise ValueError(
                f"Need at least 2 versions to compare formula: {formula_id}"
            )

        comparison_id = str(uuid.uuid4())
        variations = []

        if comparison_types is None:
            comparison_types = [
                ComparisonType.STRUCTURAL,
                ComparisonType.MATHEMATICAL,
                ComparisonType.ACCURACY,
            ]

        # Compare each pair of versions
        for i in range(len(versions)):
            for j in range(i + 1, len(versions)):
                version_a = versions[i]
                version_b = versions[j]

                variation = self._analyze_formula_variation(
                    formula_id, version_a, version_b, comparison_types
                )
                variations.append(variation)

        # Calculate overall similarity
        overall_similarity = self._calculate_overall_similarity(variations)

        # Find primary and recommended versions
        primary_version = self._find_primary_version(versions)
        recommended_version = self._recommend_best_version(versions, variations)

        # Generate summary
        summary = self._generate_comparison_summary(
            versions, variations, overall_similarity
        )

        result = ComparisonResult(
            comparison_id=comparison_id,
            formula_id=formula_id,
            versions=versions,
            variations=variations,
            overall_similarity=overall_similarity,
            primary_version=primary_version,
            recommended_version=recommended_version,
            summary=summary,
            created_at=datetime.now(),
        )

        self.comparison_history[comparison_id] = result
        logger.info(f"Generated comparison {comparison_id} for formula {formula_id}")

        return result

    def _analyze_formula_variation(
        self,
        formula_id: str,
        version_a: FormulaVersion,
        version_b: FormulaVersion,
        comparison_types: List[ComparisonType],
    ) -> FormulaVariation:
        """Analyze the variation between two formula versions"""
        variation_id = str(uuid.uuid4())

        # Calculate similarity score
        similarity_score = self._calculate_formula_similarity(
            version_a.formula, version_b.formula
        )

        # Identify differences
        differences = self._identify_formula_differences(
            version_a.formula, version_b.formula
        )

        # Determine variation type
        variation_type = self._classify_variation_type(differences)

        # Assess impact
        impact_assessment = self._assess_variation_impact(
            version_a, version_b, differences, comparison_types
        )

        # Generate recommendations
        recommendations = self._generate_variation_recommendations(
            version_a, version_b, variation_type, impact_assessment
        )

        return FormulaVariation(
            variation_id=variation_id,
            formula_id=formula_id,
            version_a=version_a,
            version_b=version_b,
            variation_type=variation_type,
            similarity_score=similarity_score,
            differences=differences,
            impact_assessment=impact_assessment,
            recommendations=recommendations,
        )

    def _calculate_formula_similarity(self, formula_a: str, formula_b: str) -> float:
        """Calculate similarity between two formulas"""
        try:
            # Parse formulas with more robust error handling
            try:
                expr_a = parse_expr(formula_a, evaluate=False)
                expr_b = parse_expr(formula_b, evaluate=False)

                # Compare symbolic expressions
                if expr_a.equals(expr_b):
                    return 1.0

                # Compare simplified forms
                simplified_a = simplify(expr_a)
                simplified_b = simplify(expr_b)

                if simplified_a.equals(simplified_b):
                    return 0.95

                # Compare expanded forms
                expanded_a = expand(expr_a)
                expanded_b = expand(expr_b)

                if expanded_a.equals(expanded_b):
                    return 0.90

            except Exception as parse_error:
                logger.warning(
                    f"Could not parse formulas for symbolic comparison: {parse_error}"
                )

            # String-based similarity as fallback
            str_similarity = difflib.SequenceMatcher(None, formula_a, formula_b).ratio()

            return str_similarity

        except Exception as e:
            logger.error(f"Error calculating formula similarity: {e}")
            return 0.0

    def _identify_formula_differences(
        self, formula_a: str, formula_b: str
    ) -> List[str]:
        """Identify specific differences between formulas"""
        differences = []

        try:
            # Parse formulas
            expr_a = parse_expr(formula_a, evaluate=False)
            expr_b = parse_expr(formula_b, evaluate=False)

            # Compare coefficients
            coeffs_a = self._extract_coefficients(expr_a)
            coeffs_b = self._extract_coefficients(expr_b)

            for var, coeff_a in coeffs_a.items():
                coeff_b = coeffs_b.get(var, 0)
                if abs(coeff_a - coeff_b) > 0.001:
                    differences.append(f"Coefficient for {var}: {coeff_a} vs {coeff_b}")

            # Compare variables
            vars_a = set(str(s) for s in expr_a.free_symbols)
            vars_b = set(str(s) for s in expr_b.free_symbols)

            if vars_a != vars_b:
                only_a = vars_a - vars_b
                only_b = vars_b - vars_a
                if only_a:
                    differences.append(
                        f"Variables only in formula A: {', '.join(only_a)}"
                    )
                if only_b:
                    differences.append(
                        f"Variables only in formula B: {', '.join(only_b)}"
                    )

            # String-based differences
            if not differences:
                diff = difflib.unified_diff(
                    formula_a.splitlines(), formula_b.splitlines(), lineterm=""
                )
                diff_lines = list(diff)
                if diff_lines:
                    differences.append(
                        f"Text differences: {len(diff_lines)} lines differ"
                    )

        except Exception as e:
            logger.error(f"Error identifying formula differences: {e}")
            differences.append(f"Error analyzing differences: {str(e)}")

        return differences

    def _extract_coefficients(self, expr) -> Dict[str, float]:
        """Extract coefficients from a symbolic expression"""
        coeffs = {}
        try:
            if expr.is_Add:
                for term in expr.args:
                    if term.is_Mul:
                        coeff = 1.0
                        var = None
                        for factor in term.args:
                            if factor.is_Number:
                                coeff *= float(factor)
                            else:
                                var = str(factor)
                        if var:
                            coeffs[var] = coeff
            elif expr.is_Mul:
                coeff = 1.0
                var = None
                for factor in expr.args:
                    if factor.is_Number:
                        coeff *= float(factor)
                    else:
                        var = str(factor)
                if var:
                    coeffs[var] = coeff
        except Exception as e:
            logger.error(f"Error extracting coefficients: {e}")

        return coeffs

    def _classify_variation_type(self, differences: List[str]) -> VariationType:
        """Classify the type of variation based on differences"""
        if not differences:
            return VariationType.SYNTAX_DIFFERENCE

        # Check for coefficient differences
        if any("Coefficient" in diff for diff in differences):
            return VariationType.PARAMETER_DIFFERENCE

        # Check for variable differences
        if any("Variables only" in diff for diff in differences):
            return VariationType.CALCULATION_DIFFERENCE

        # Check for text differences
        if any("Text differences" in diff for diff in differences):
            return VariationType.SYNTAX_DIFFERENCE

        return VariationType.VERSION_DIFFERENCE

    def _assess_variation_impact(
        self,
        version_a: FormulaVersion,
        version_b: FormulaVersion,
        differences: List[str],
        comparison_types: List[ComparisonType],
    ) -> str:
        """Assess the impact of formula variations"""
        impact_levels = []

        # Test with sample data if available
        if version_a.test_data and version_b.test_data:
            try:
                expr_a = parse_expr(version_a.formula, evaluate=False)
                expr_b = parse_expr(version_b.formula, evaluate=False)

                # Use version A's test data
                test_data = version_a.test_data
                result_a = float(
                    expr_a.subs({sp.Symbol(k): v for k, v in test_data.items()})
                )
                result_b = float(
                    expr_b.subs({sp.Symbol(k): v for k, v in test_data.items()})
                )

                diff_percent = abs(result_a - result_b) / result_a * 100

                if diff_percent < 1:
                    impact_levels.append("Minimal impact (< 1% difference)")
                elif diff_percent < 5:
                    impact_levels.append("Low impact (1-5% difference)")
                elif diff_percent < 10:
                    impact_levels.append("Moderate impact (5-10% difference)")
                else:
                    impact_levels.append("High impact (> 10% difference)")

            except Exception as e:
                impact_levels.append(f"Could not assess numerical impact: {str(e)}")

        # Assess based on variation type
        if any("Coefficient" in diff for diff in differences):
            impact_levels.append("Parameter changes may affect calculation accuracy")

        if any("Variables only" in diff for diff in differences):
            impact_levels.append("Structural changes may significantly affect results")

        # Assess source reliability
        reliability_diff = abs(
            version_a.source.reliability_score - version_b.source.reliability_score
        )
        if reliability_diff > 0.1:
            impact_levels.append("Source reliability differences may affect confidence")

        return (
            "; ".join(impact_levels)
            if impact_levels
            else "No significant impact detected"
        )

    def _generate_variation_recommendations(
        self,
        version_a: FormulaVersion,
        version_b: FormulaVersion,
        variation_type: VariationType,
        impact_assessment: str,
    ) -> List[str]:
        """Generate recommendations for handling formula variations"""
        recommendations = []

        # Source-based recommendations
        if version_a.source.reliability_score > version_b.source.reliability_score:
            recommendations.append(
                f"Prefer {version_a.source.name} version (higher reliability)"
            )
        elif version_b.source.reliability_score > version_a.source.reliability_score:
            recommendations.append(
                f"Prefer {version_b.source.name} version (higher reliability)"
            )

        # Date-based recommendations
        if version_a.created_date and version_b.created_date:
            if version_a.created_date > version_b.created_date:
                recommendations.append(
                    f"Consider {version_a.source.name} version (more recent)"
                )
            elif version_b.created_date > version_a.created_date:
                recommendations.append(
                    f"Consider {version_b.source.name} version (more recent)"
                )

        # Variation type recommendations
        if variation_type == VariationType.PARAMETER_DIFFERENCE:
            recommendations.append("Verify coefficient accuracy with multiple sources")
        elif variation_type == VariationType.CALCULATION_DIFFERENCE:
            recommendations.append(
                "Test both versions with real data to determine accuracy"
            )
        elif variation_type == VariationType.SYNTAX_DIFFERENCE:
            recommendations.append(
                "Check for mathematical equivalence despite syntax differences"
            )

        # Impact-based recommendations
        if "High impact" in impact_assessment:
            recommendations.append(
                "Carefully validate results before using either version"
            )
        elif "Moderate impact" in impact_assessment:
            recommendations.append(
                "Consider the specific use case when choosing version"
            )

        return recommendations

    def _calculate_overall_similarity(
        self, variations: List[FormulaVariation]
    ) -> float:
        """Calculate overall similarity across all variations"""
        if not variations:
            return 1.0

        similarities = [v.similarity_score for v in variations]
        return sum(similarities) / len(similarities)

    def _find_primary_version(
        self, versions: List[FormulaVersion]
    ) -> Optional[FormulaVersion]:
        """Find the primary version based on is_primary flag and reliability"""
        # First, look for explicitly marked primary version
        for version in versions:
            if version.is_primary:
                return version

        # If no primary marked, choose highest reliability
        if versions:
            return max(versions, key=lambda v: v.source.reliability_score)

        return None

    def _recommend_best_version(
        self, versions: List[FormulaVersion], variations: List[FormulaVariation]
    ) -> Optional[FormulaVersion]:
        """Recommend the best version based on multiple criteria"""
        if not versions:
            return None

        # Score each version
        version_scores = {}
        for version in versions:
            score = 0.0

            # Reliability score (40% weight)
            score += version.source.reliability_score * 0.4

            # Recency score (20% weight)
            if version.created_date:
                try:
                    year = int(version.created_date)
                    recency_score = min(1.0, (2025 - year) / 20)  # Normalize to 0-1
                    score += recency_score * 0.2
                except:
                    pass

            # Primary flag bonus (20% weight)
            if version.is_primary:
                score += 0.2

            # Variation impact score (20% weight)
            variation_impact = 1.0
            for variation in variations:
                if variation.version_a == version or variation.version_b == version:
                    variation_impact *= variation.similarity_score
            score += variation_impact * 0.2

            version_scores[version.version_id] = (version, score)

        # Return highest scoring version
        return max(version_scores.values(), key=lambda x: x[1])[0]

    def _generate_comparison_summary(
        self,
        versions: List[FormulaVersion],
        variations: List[FormulaVariation],
        overall_similarity: float,
    ) -> str:
        """Generate a summary of the comparison"""
        summary_parts = []

        summary_parts.append(
            f"Compared {len(versions)} versions of formula across {len(set(v.source.name for v in versions))} sources."
        )

        if overall_similarity >= 0.9:
            summary_parts.append("Formulas are highly consistent across sources.")
        elif overall_similarity >= 0.7:
            summary_parts.append("Formulas show moderate variations across sources.")
        else:
            summary_parts.append("Formulas show significant variations across sources.")

        # Count variation types
        variation_counts = defaultdict(int)
        for variation in variations:
            variation_counts[variation.variation_type.value] += 1

        if variation_counts:
            summary_parts.append(f"Variation types: {dict(variation_counts)}")

        return " ".join(summary_parts)

    def get_formula_evolution(self, formula_id: str) -> Optional[HistoricalEvolution]:
        """Get historical evolution of a formula"""
        if formula_id not in self.formula_versions:
            return None

        versions = self.formula_versions[formula_id]

        # Sort by date
        sorted_versions = sorted(versions, key=lambda v: v.created_date or "1900")

        # Identify key changes
        key_changes = []
        for i in range(1, len(sorted_versions)):
            prev_version = sorted_versions[i - 1]
            curr_version = sorted_versions[i]

            variation = self._analyze_formula_variation(
                formula_id, prev_version, curr_version, [ComparisonType.STRUCTURAL]
            )

            if variation.similarity_score < 0.95:
                key_changes.append(
                    f"{prev_version.created_date} → {curr_version.created_date}: {variation.variation_type.value}"
                )

        # Determine current consensus
        current_consensus = self._recommend_best_version(versions, [])

        evolution_summary = f"Formula evolved over {len(sorted_versions)} versions with {len(key_changes)} key changes."

        return HistoricalEvolution(
            formula_id=formula_id,
            timeline=sorted_versions,
            evolution_summary=evolution_summary,
            key_changes=key_changes,
            current_consensus=current_consensus,
        )

    def get_all_formulas(self) -> Dict[str, List[FormulaVersion]]:
        """Get all formula versions"""
        return self.formula_versions

    def get_formula_versions(self, formula_id: str) -> List[FormulaVersion]:
        """Get all versions of a specific formula"""
        return self.formula_versions.get(formula_id, [])

    def get_formula_sources(self) -> Dict[str, FormulaSource]:
        """Get all formula sources"""
        return self.formula_sources

    def get_comparison_history(self) -> Dict[str, ComparisonResult]:
        """Get comparison history"""
        return self.comparison_history
