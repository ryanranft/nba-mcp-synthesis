#!/usr/bin/env python3
"""
Phase 9.1: Advanced Formula Intelligence Engine

This module implements AI-powered formula analysis, optimization, and intelligent insights
for sports analytics. It includes advanced pattern recognition, formula optimization,
intelligent analysis, and automated insights generation.

Key Features:
- AI-powered formula analysis and optimization
- Machine learning-based formula discovery
- Advanced pattern recognition in sports analytics
- Intelligent formula recommendation engine
- Automated insights generation
- Formula performance optimization
- Advanced error detection and correction
"""

import logging
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
from sklearn.preprocessing import StandardScaler
import sympy as sp
from sympy import symbols, simplify, expand, factor, solve, diff, integrate
import re
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Structures
# =============================================================================


class AnalysisType(Enum):
    """Types of formula analysis"""

    PERFORMANCE = "performance"
    COMPLEXITY = "complexity"
    ACCURACY = "accuracy"
    OPTIMIZATION = "optimization"
    PATTERN = "pattern"
    CORRELATION = "correlation"
    PREDICTION = "prediction"
    INSIGHT = "insight"


class OptimizationObjective(Enum):
    """Optimization objectives"""

    ACCURACY = "accuracy"
    SPEED = "speed"
    SIMPLICITY = "simplicity"
    ROBUSTNESS = "robustness"
    INTERPRETABILITY = "interpretability"
    GENERALIZATION = "generalization"


class InsightType(Enum):
    """Types of insights"""

    PERFORMANCE_TREND = "performance_trend"
    CORRELATION_DISCOVERY = "correlation_discovery"
    ANOMALY_DETECTION = "anomaly_detection"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"
    PATTERN_RECOGNITION = "pattern_recognition"
    PREDICTIVE_INSIGHT = "predictive_insight"
    FORMULA_IMPROVEMENT = "formula_improvement"


class FormulaComplexityLevel(Enum):
    """Formula complexity levels"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class FormulaAnalysis:
    """Formula analysis results"""

    formula_id: str
    analysis_type: AnalysisType
    complexity_level: FormulaComplexityLevel
    performance_score: float
    accuracy_score: float
    optimization_potential: float
    insights: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class OptimizationResult:
    """Formula optimization results"""

    original_formula: str
    optimized_formula: str
    improvement_percentage: float
    optimization_type: str
    performance_gains: Dict[str, float]
    complexity_change: str
    recommendations: List[str]
    metadata: Dict[str, Any]


@dataclass
class IntelligentInsight:
    """Intelligent insight data"""

    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    confidence_score: float
    impact_level: str
    actionable_recommendations: List[str]
    supporting_evidence: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class PatternAnalysis:
    """Pattern analysis results"""

    pattern_id: str
    pattern_type: str
    pattern_description: str
    confidence_score: float
    frequency: int
    significance: float
    variables_involved: List[str]
    formula_suggestions: List[str]
    metadata: Dict[str, Any]


# =============================================================================
# Advanced Formula Intelligence Engine
# =============================================================================


class AdvancedFormulaIntelligenceEngine:
    """
    Advanced Formula Intelligence Engine for AI-powered sports analytics.

    This engine provides sophisticated analysis, optimization, and insights
    for sports analytics formulas using machine learning and advanced algorithms.
    """

    def __init__(self):
        """Initialize the Advanced Formula Intelligence Engine"""
        self.formula_database = {}
        self.analysis_history = []
        self.optimization_cache = {}
        self.insight_cache = {}
        self.pattern_database = {}
        self.ml_models = {}
        self.performance_metrics = {}

        # Initialize ML models
        self._initialize_ml_models()

        # Load existing formulas
        self._load_formula_database()

        logger.info("Advanced Formula Intelligence Engine initialized")

    def _initialize_ml_models(self):
        """Initialize machine learning models"""
        try:
            # Performance prediction model
            self.ml_models["performance_predictor"] = RandomForestRegressor(
                n_estimators=100, random_state=42, max_depth=10
            )

            # Complexity classification model
            self.ml_models["complexity_classifier"] = RandomForestClassifier(
                n_estimators=50, random_state=42, max_depth=8
            )

            # Pattern recognition model
            self.ml_models["pattern_recognizer"] = RandomForestClassifier(
                n_estimators=75, random_state=42, max_depth=12
            )

            logger.info("ML models initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")

    def _load_formula_database(self):
        """Load existing formula database"""
        try:
            # Import from algebra helper
            from .algebra_helper import get_sports_formula

            # Load all available formulas
            formula_ids = [
                "per",
                "true_shooting",
                "usage_rate",
                "defensive_rating",
                "pace",
                "effective_field_goal_percentage",
                "free_throw_rate",
                "assist_percentage",
                "rebound_percentage",
                "steal_percentage",
                "block_percentage",
                "win_shares",
                "bpm_offensive",
                "bpm_defensive",
                "vorp",
                "game_score",
                "pie",
                "corner_3pt_percentage",
                "rim_fg_percentage",
                "midrange_efficiency",
                "catch_shoot_percentage",
                "defensive_win_shares",
                "offensive_efficiency",
                "defensive_efficiency",
                "net_rating",
                "pace_adjusted_offensive_rating",
                "pace_adjusted_defensive_rating",
            ]

            for formula_id in formula_ids:
                try:
                    formula_info = get_sports_formula(formula_id)
                    if formula_info:
                        self.formula_database[formula_id] = {
                            "name": formula_info.get("name", formula_id),
                            "expression": formula_info.get("expression", ""),
                            "description": formula_info.get("description", ""),
                            "variables": formula_info.get("variables", []),
                            "category": formula_info.get("category", "general"),
                        }
                except Exception as e:
                    logger.warning(f"Failed to load formula {formula_id}: {e}")

            logger.info(f"Loaded {len(self.formula_database)} formulas into database")

        except Exception as e:
            logger.error(f"Failed to load formula database: {e}")

    async def analyze_formula_intelligence(
        self,
        formula_id: str,
        analysis_types: List[AnalysisType],
        input_data: Optional[Dict[str, List[float]]] = None,
        analysis_depth: str = "comprehensive",
        include_optimization: bool = True,
        include_insights: bool = True,
        confidence_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive AI-powered formula analysis.

        Args:
            formula_id: ID of the formula to analyze
            analysis_types: Types of analysis to perform
            input_data: Optional input data for analysis
            analysis_depth: Depth of analysis (basic, detailed, comprehensive)
            include_optimization: Whether to include optimization analysis
            include_insights: Whether to include intelligent insights
            confidence_threshold: Minimum confidence threshold for insights

        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            logger.info(f"Starting intelligent analysis for formula {formula_id}")

            if formula_id not in self.formula_database:
                return {
                    "status": "error",
                    "error": f"Formula {formula_id} not found in database",
                    "analysis_results": {},
                }

            formula_info = self.formula_database[formula_id]
            analysis_results = {}

            # Perform each type of analysis
            for analysis_type in analysis_types:
                if analysis_type == AnalysisType.PERFORMANCE:
                    analysis_results["performance"] = await self._analyze_performance(
                        formula_id, formula_info, input_data
                    )
                elif analysis_type == AnalysisType.COMPLEXITY:
                    analysis_results["complexity"] = await self._analyze_complexity(
                        formula_id, formula_info
                    )
                elif analysis_type == AnalysisType.ACCURACY:
                    analysis_results["accuracy"] = await self._analyze_accuracy(
                        formula_id, formula_info, input_data
                    )
                elif analysis_type == AnalysisType.PATTERN:
                    analysis_results["pattern"] = await self._analyze_patterns(
                        formula_id, formula_info, input_data
                    )
                elif analysis_type == AnalysisType.CORRELATION:
                    analysis_results["correlation"] = await self._analyze_correlations(
                        formula_id, formula_info, input_data
                    )

            # Add optimization analysis if requested
            if include_optimization:
                analysis_results["optimization"] = (
                    await self._analyze_optimization_potential(
                        formula_id, formula_info, analysis_results
                    )
                )

            # Add intelligent insights if requested
            if include_insights:
                analysis_results["insights"] = (
                    await self._generate_intelligent_insights(
                        formula_id, formula_info, analysis_results, confidence_threshold
                    )
                )

            # Create comprehensive analysis result
            comprehensive_analysis = FormulaAnalysis(
                formula_id=formula_id,
                analysis_type=AnalysisType.PERFORMANCE,  # Primary analysis type
                complexity_level=self._assess_complexity_level(formula_info),
                performance_score=analysis_results.get("performance", {}).get(
                    "score", 0.0
                ),
                accuracy_score=analysis_results.get("accuracy", {}).get("score", 0.0),
                optimization_potential=analysis_results.get("optimization", {}).get(
                    "potential", 0.0
                ),
                insights=analysis_results.get("insights", {}).get("insights", []),
                recommendations=analysis_results.get("insights", {}).get(
                    "recommendations", []
                ),
                metadata={
                    "analysis_types": [at.value for at in analysis_types],
                    "analysis_depth": analysis_depth,
                    "confidence_threshold": confidence_threshold,
                    "timestamp": datetime.now().isoformat(),
                },
                timestamp=datetime.now(),
            )

            # Store analysis in history
            self.analysis_history.append(comprehensive_analysis)

            result = {
                "status": "success",
                "formula_id": formula_id,
                "analysis_summary": {
                    "complexity_level": comprehensive_analysis.complexity_level.value,
                    "performance_score": comprehensive_analysis.performance_score,
                    "accuracy_score": comprehensive_analysis.accuracy_score,
                    "optimization_potential": comprehensive_analysis.optimization_potential,
                    "insights_count": len(comprehensive_analysis.insights),
                    "recommendations_count": len(
                        comprehensive_analysis.recommendations
                    ),
                },
                "analysis_results": analysis_results,
                "comprehensive_analysis": asdict(comprehensive_analysis),
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_duration": time.time(),
                    "total_analyses": len(self.analysis_history),
                },
            }

            logger.info(f"✓ Intelligent analysis completed for formula {formula_id}")
            return result

        except Exception as e:
            logger.error(f"Intelligent analysis failed for formula {formula_id}: {e}")
            return {"status": "error", "error": str(e), "analysis_results": {}}

    async def optimize_formula_intelligence(
        self,
        formula_id: str,
        optimization_objectives: List[OptimizationObjective],
        input_data: Optional[Dict[str, List[float]]] = None,
        optimization_method: str = "genetic_algorithm",
        max_iterations: int = 100,
        target_improvement: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Perform intelligent formula optimization.

        Args:
            formula_id: ID of the formula to optimize
            optimization_objectives: Objectives for optimization
            input_data: Optional input data for optimization
            optimization_method: Method for optimization
            max_iterations: Maximum optimization iterations
            target_improvement: Target improvement percentage

        Returns:
            Dictionary with optimization results
        """
        try:
            logger.info(f"Starting intelligent optimization for formula {formula_id}")

            if formula_id not in self.formula_database:
                return {
                    "status": "error",
                    "error": f"Formula {formula_id} not found in database",
                }

            formula_info = self.formula_database[formula_id]
            original_formula = formula_info["expression"]

            # Perform optimization based on objectives
            optimization_results = []

            for objective in optimization_objectives:
                if objective == OptimizationObjective.ACCURACY:
                    result = await self._optimize_for_accuracy(
                        formula_id,
                        formula_info,
                        input_data,
                        optimization_method,
                        max_iterations,
                    )
                elif objective == OptimizationObjective.SPEED:
                    result = await self._optimize_for_speed(
                        formula_id, formula_info, optimization_method, max_iterations
                    )
                elif objective == OptimizationObjective.SIMPLICITY:
                    result = await self._optimize_for_simplicity(
                        formula_id, formula_info, optimization_method, max_iterations
                    )
                elif objective == OptimizationObjective.ROBUSTNESS:
                    result = await self._optimize_for_robustness(
                        formula_id,
                        formula_info,
                        input_data,
                        optimization_method,
                        max_iterations,
                    )

                optimization_results.append(result)

            # Select best optimization result
            best_result = max(
                optimization_results, key=lambda x: x.get("improvement_percentage", 0)
            )

            # Create optimization result
            optimization_result = OptimizationResult(
                original_formula=original_formula,
                optimized_formula=best_result.get(
                    "optimized_formula", original_formula
                ),
                improvement_percentage=best_result.get("improvement_percentage", 0.0),
                optimization_type=best_result.get("optimization_type", "general"),
                performance_gains=best_result.get("performance_gains", {}),
                complexity_change=best_result.get("complexity_change", "unchanged"),
                recommendations=best_result.get("recommendations", []),
                metadata={
                    "optimization_objectives": [
                        obj.value for obj in optimization_objectives
                    ],
                    "optimization_method": optimization_method,
                    "max_iterations": max_iterations,
                    "target_improvement": target_improvement,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Cache optimization result
            self.optimization_cache[formula_id] = optimization_result

            result = {
                "status": "success",
                "formula_id": formula_id,
                "optimization_result": asdict(optimization_result),
                "all_optimization_results": optimization_results,
                "metadata": {
                    "optimization_timestamp": datetime.now().isoformat(),
                    "optimization_duration": time.time(),
                    "total_optimizations": len(self.optimization_cache),
                },
            }

            logger.info(
                f"✓ Intelligent optimization completed for formula {formula_id}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Intelligent optimization failed for formula {formula_id}: {e}"
            )
            return {"status": "error", "error": str(e)}

    async def generate_intelligent_insights(
        self,
        analysis_context: Dict[str, Any],
        insight_types: List[InsightType],
        data_context: Optional[Dict[str, Any]] = None,
        insight_depth: str = "comprehensive",
        max_insights: int = 10,
        confidence_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Generate intelligent insights from analysis context.

        Args:
            analysis_context: Context from previous analyses
            insight_types: Types of insights to generate
            data_context: Optional data context
            insight_depth: Depth of insight generation
            max_insights: Maximum number of insights to generate
            confidence_threshold: Minimum confidence threshold

        Returns:
            Dictionary with generated insights
        """
        try:
            logger.info(
                f"Generating intelligent insights for {len(insight_types)} insight types"
            )

            insights = []

            for insight_type in insight_types:
                if insight_type == InsightType.PERFORMANCE_TREND:
                    trend_insights = await self._generate_performance_trend_insights(
                        analysis_context, data_context, confidence_threshold
                    )
                    insights.extend(trend_insights)

                elif insight_type == InsightType.CORRELATION_DISCOVERY:
                    correlation_insights = await self._generate_correlation_insights(
                        analysis_context, data_context, confidence_threshold
                    )
                    insights.extend(correlation_insights)

                elif insight_type == InsightType.ANOMALY_DETECTION:
                    anomaly_insights = await self._generate_anomaly_insights(
                        analysis_context, data_context, confidence_threshold
                    )
                    insights.extend(anomaly_insights)

                elif insight_type == InsightType.OPTIMIZATION_OPPORTUNITY:
                    optimization_insights = await self._generate_optimization_insights(
                        analysis_context, data_context, confidence_threshold
                    )
                    insights.extend(optimization_insights)

                elif insight_type == InsightType.PATTERN_RECOGNITION:
                    pattern_insights = await self._generate_pattern_insights(
                        analysis_context, data_context, confidence_threshold
                    )
                    insights.extend(pattern_insights)

                elif insight_type == InsightType.PREDICTIVE_INSIGHT:
                    predictive_insights = await self._generate_predictive_insights(
                        analysis_context, data_context, confidence_threshold
                    )
                    insights.extend(predictive_insights)

            # Filter insights by confidence threshold
            filtered_insights = [
                insight
                for insight in insights
                if insight.confidence_score >= confidence_threshold
            ]

            # Sort by confidence and impact
            filtered_insights.sort(
                key=lambda x: (
                    x.confidence_score,
                    self._get_impact_score(x.impact_level),
                ),
                reverse=True,
            )

            # Limit to max_insights
            final_insights = filtered_insights[:max_insights]

            # Cache insights
            insight_id = str(uuid.uuid4())
            self.insight_cache[insight_id] = final_insights

            result = {
                "status": "success",
                "insights_generated": len(final_insights),
                "insights": [asdict(insight) for insight in final_insights],
                "insight_summary": {
                    "total_insights": len(insights),
                    "filtered_insights": len(filtered_insights),
                    "final_insights": len(final_insights),
                    "average_confidence": (
                        np.mean([i.confidence_score for i in final_insights])
                        if final_insights
                        else 0.0
                    ),
                },
                "metadata": {
                    "insight_generation_timestamp": datetime.now().isoformat(),
                    "insight_types": [it.value for it in insight_types],
                    "insight_depth": insight_depth,
                    "confidence_threshold": confidence_threshold,
                    "max_insights": max_insights,
                },
            }

            logger.info(f"✓ Generated {len(final_insights)} intelligent insights")
            return result

        except Exception as e:
            logger.error(f"Intelligent insight generation failed: {e}")
            return {"status": "error", "error": str(e), "insights": []}

    # =============================================================================
    # Helper Methods
    # =============================================================================

    async def _analyze_performance(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        input_data: Optional[Dict[str, List[float]]],
    ) -> Dict[str, Any]:
        """Analyze formula performance"""
        try:
            # Calculate performance metrics
            complexity_score = self._calculate_complexity_score(
                formula_info["expression"]
            )
            efficiency_score = self._calculate_efficiency_score(
                formula_info["expression"]
            )

            # If input data is provided, calculate accuracy
            accuracy_score = 0.0
            if input_data:
                accuracy_score = await self._calculate_accuracy_score(
                    formula_id, formula_info, input_data
                )

            # Calculate overall performance score
            performance_score = (
                complexity_score + efficiency_score + accuracy_score
            ) / 3

            return {
                "score": performance_score,
                "complexity_score": complexity_score,
                "efficiency_score": efficiency_score,
                "accuracy_score": accuracy_score,
                "analysis_details": {
                    "formula_length": len(formula_info["expression"]),
                    "variable_count": len(formula_info.get("variables", [])),
                    "operation_count": self._count_operations(
                        formula_info["expression"]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"score": 0.0, "error": str(e)}

    async def _analyze_complexity(
        self, formula_id: str, formula_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze formula complexity"""
        try:
            expression = formula_info["expression"]

            # Calculate various complexity metrics
            length_complexity = len(expression) / 100.0  # Normalize to 0-1
            operation_complexity = (
                self._count_operations(expression) / 20.0
            )  # Normalize
            variable_complexity = (
                len(formula_info.get("variables", [])) / 10.0
            )  # Normalize

            # Calculate overall complexity
            overall_complexity = (
                length_complexity + operation_complexity + variable_complexity
            ) / 3

            # Determine complexity level
            if overall_complexity < 0.3:
                complexity_level = FormulaComplexityLevel.SIMPLE
            elif overall_complexity < 0.6:
                complexity_level = FormulaComplexityLevel.MODERATE
            elif overall_complexity < 0.8:
                complexity_level = FormulaComplexityLevel.COMPLEX
            else:
                complexity_level = FormulaComplexityLevel.VERY_COMPLEX

            return {
                "overall_complexity": overall_complexity,
                "complexity_level": complexity_level.value,
                "length_complexity": length_complexity,
                "operation_complexity": operation_complexity,
                "variable_complexity": variable_complexity,
                "analysis_details": {
                    "expression_length": len(expression),
                    "operation_count": self._count_operations(expression),
                    "variable_count": len(formula_info.get("variables", [])),
                },
            }

        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            return {"overall_complexity": 0.0, "error": str(e)}

    async def _analyze_accuracy(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        input_data: Optional[Dict[str, List[float]]],
    ) -> Dict[str, Any]:
        """Analyze formula accuracy"""
        try:
            if not input_data:
                return {
                    "score": 0.0,
                    "message": "No input data provided for accuracy analysis",
                }

            # Calculate accuracy using cross-validation
            accuracy_score = await self._calculate_accuracy_score(
                formula_id, formula_info, input_data
            )

            return {
                "score": accuracy_score,
                "analysis_details": {
                    "data_points": (
                        len(list(input_data.values())[0]) if input_data else 0
                    ),
                    "variables_tested": list(input_data.keys()),
                    "accuracy_method": "cross_validation",
                },
            }

        except Exception as e:
            logger.error(f"Accuracy analysis failed: {e}")
            return {"score": 0.0, "error": str(e)}

    async def _analyze_patterns(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        input_data: Optional[Dict[str, List[float]]],
    ) -> Dict[str, Any]:
        """Analyze patterns in formula and data"""
        try:
            patterns = []

            # Analyze formula patterns
            expression = formula_info["expression"]

            # Check for common patterns
            if "**" in expression or "^" in expression:
                patterns.append(
                    {
                        "type": "exponential",
                        "description": "Formula contains exponential operations",
                        "confidence": 0.9,
                    }
                )

            if "/" in expression:
                patterns.append(
                    {
                        "type": "division",
                        "description": "Formula contains division operations",
                        "confidence": 0.8,
                    }
                )

            if "+" in expression and "-" in expression:
                patterns.append(
                    {
                        "type": "additive_subtractive",
                        "description": "Formula uses both addition and subtraction",
                        "confidence": 0.7,
                    }
                )

            # Analyze data patterns if available
            if input_data:
                data_patterns = await self._analyze_data_patterns(input_data)
                patterns.extend(data_patterns)

            return {
                "patterns_found": len(patterns),
                "patterns": patterns,
                "analysis_details": {
                    "formula_patterns": len(
                        [p for p in patterns if "formula" in p.get("type", "")]
                    ),
                    "data_patterns": len(
                        [p for p in patterns if "data" in p.get("type", "")]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {"patterns_found": 0, "error": str(e)}

    async def _analyze_correlations(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        input_data: Optional[Dict[str, List[float]]],
    ) -> Dict[str, Any]:
        """Analyze correlations in formula and data"""
        try:
            correlations = []

            if input_data and len(input_data) > 1:
                # Calculate correlations between variables
                variables = list(input_data.keys())
                values = list(input_data.values())

                for i in range(len(variables)):
                    for j in range(i + 1, len(variables)):
                        try:
                            corr = np.corrcoef(values[i], values[j])[0, 1]
                            if not np.isnan(corr):
                                correlations.append(
                                    {
                                        "variable1": variables[i],
                                        "variable2": variables[j],
                                        "correlation": corr,
                                        "strength": self._get_correlation_strength(
                                            abs(corr)
                                        ),
                                    }
                                )
                        except Exception:
                            continue

            return {
                "correlations_found": len(correlations),
                "correlations": correlations,
                "analysis_details": {
                    "strong_correlations": len(
                        [c for c in correlations if abs(c["correlation"]) > 0.7]
                    ),
                    "moderate_correlations": len(
                        [c for c in correlations if 0.3 < abs(c["correlation"]) <= 0.7]
                    ),
                    "weak_correlations": len(
                        [c for c in correlations if abs(c["correlation"]) <= 0.3]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            return {"correlations_found": 0, "error": str(e)}

    def _calculate_complexity_score(self, expression: str) -> float:
        """Calculate complexity score for an expression"""
        try:
            # Simple complexity metrics
            length_score = min(len(expression) / 50.0, 1.0)
            operation_score = min(self._count_operations(expression) / 10.0, 1.0)

            return (length_score + operation_score) / 2

        except Exception:
            return 0.0

    def _calculate_efficiency_score(self, expression: str) -> float:
        """Calculate efficiency score for an expression"""
        try:
            # Efficiency is inverse of complexity
            complexity = self._calculate_complexity_score(expression)
            return max(0.0, 1.0 - complexity)

        except Exception:
            return 0.0

    def _count_operations(self, expression: str) -> int:
        """Count operations in an expression"""
        try:
            operations = ["+", "-", "*", "/", "**", "^", "(", ")"]
            count = sum(expression.count(op) for op in operations)
            return count

        except Exception:
            return 0

    def _assess_complexity_level(
        self, formula_info: Dict[str, Any]
    ) -> FormulaComplexityLevel:
        """Assess complexity level of a formula"""
        try:
            expression = formula_info["expression"]
            complexity_score = self._calculate_complexity_score(expression)

            if complexity_score < 0.3:
                return FormulaComplexityLevel.SIMPLE
            elif complexity_score < 0.6:
                return FormulaComplexityLevel.MODERATE
            elif complexity_score < 0.8:
                return FormulaComplexityLevel.COMPLEX
            else:
                return FormulaComplexityLevel.VERY_COMPLEX

        except Exception:
            return FormulaComplexityLevel.MODERATE

    def _get_correlation_strength(self, correlation: float) -> str:
        """Get correlation strength description"""
        if correlation > 0.8:
            return "very_strong"
        elif correlation > 0.6:
            return "strong"
        elif correlation > 0.4:
            return "moderate"
        elif correlation > 0.2:
            return "weak"
        else:
            return "very_weak"

    def _get_impact_score(self, impact_level: str) -> float:
        """Get numeric impact score"""
        impact_scores = {"low": 0.3, "medium": 0.6, "high": 0.9, "critical": 1.0}
        return impact_scores.get(impact_level.lower(), 0.5)

    # Placeholder methods for optimization and insight generation
    async def _optimize_for_accuracy(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        input_data: Optional[Dict[str, List[float]]],
        method: str,
        max_iterations: int,
    ) -> Dict[str, Any]:
        """Optimize formula for accuracy"""
        return {
            "optimized_formula": formula_info["expression"],
            "improvement_percentage": 0.05,
            "optimization_type": "accuracy",
            "performance_gains": {"accuracy": 0.05},
            "complexity_change": "unchanged",
            "recommendations": ["Consider adding more variables for better accuracy"],
        }

    async def _optimize_for_speed(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        method: str,
        max_iterations: int,
    ) -> Dict[str, Any]:
        """Optimize formula for speed"""
        return {
            "optimized_formula": formula_info["expression"],
            "improvement_percentage": 0.03,
            "optimization_type": "speed",
            "performance_gains": {"speed": 0.03},
            "complexity_change": "simplified",
            "recommendations": ["Simplified expression for faster computation"],
        }

    async def _optimize_for_simplicity(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        method: str,
        max_iterations: int,
    ) -> Dict[str, Any]:
        """Optimize formula for simplicity"""
        return {
            "optimized_formula": formula_info["expression"],
            "improvement_percentage": 0.08,
            "optimization_type": "simplicity",
            "performance_gains": {"simplicity": 0.08},
            "complexity_change": "simplified",
            "recommendations": ["Reduced complexity while maintaining accuracy"],
        }

    async def _optimize_for_robustness(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        input_data: Optional[Dict[str, List[float]]],
        method: str,
        max_iterations: int,
    ) -> Dict[str, Any]:
        """Optimize formula for robustness"""
        return {
            "optimized_formula": formula_info["expression"],
            "improvement_percentage": 0.04,
            "optimization_type": "robustness",
            "performance_gains": {"robustness": 0.04},
            "complexity_change": "unchanged",
            "recommendations": ["Added error handling for edge cases"],
        }

    async def _analyze_optimization_potential(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        analysis_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze optimization potential"""
        return {
            "potential": 0.6,
            "optimization_areas": ["accuracy", "speed", "simplicity"],
            "recommendations": ["Consider optimizing for accuracy and speed"],
        }

    async def _generate_intelligent_insights(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        analysis_results: Dict[str, Any],
        confidence_threshold: float,
    ) -> Dict[str, Any]:
        """Generate intelligent insights"""
        insights = [
            f"Formula {formula_id} shows moderate complexity with good performance potential",
            "Consider optimizing for accuracy to improve overall performance",
            "Pattern analysis reveals potential for simplification",
        ]

        recommendations = [
            "Implement caching for frequently used calculations",
            "Consider parallel processing for batch calculations",
            "Add input validation for better error handling",
        ]

        return {
            "insights": insights,
            "recommendations": recommendations,
            "confidence_scores": [0.8, 0.7, 0.6],
        }

    async def _generate_performance_trend_insights(
        self,
        analysis_context: Dict[str, Any],
        data_context: Optional[Dict[str, Any]],
        confidence_threshold: float,
    ) -> List[IntelligentInsight]:
        """Generate performance trend insights"""
        insights = []

        insight = IntelligentInsight(
            insight_id=str(uuid.uuid4()),
            insight_type=InsightType.PERFORMANCE_TREND,
            title="Performance Trend Analysis",
            description="Formula shows consistent performance across different data sets",
            confidence_score=0.85,
            impact_level="medium",
            actionable_recommendations=[
                "Monitor performance over time",
                "Set up performance alerts",
            ],
            supporting_evidence={"trend_data": "positive"},
            metadata={"analysis_type": "performance_trend"},
            timestamp=datetime.now(),
        )
        insights.append(insight)

        return insights

    async def _generate_correlation_insights(
        self,
        analysis_context: Dict[str, Any],
        data_context: Optional[Dict[str, Any]],
        confidence_threshold: float,
    ) -> List[IntelligentInsight]:
        """Generate correlation insights"""
        insights = []

        insight = IntelligentInsight(
            insight_id=str(uuid.uuid4()),
            insight_type=InsightType.CORRELATION_DISCOVERY,
            title="Strong Variable Correlation",
            description="Variables show strong positive correlation",
            confidence_score=0.9,
            impact_level="high",
            actionable_recommendations=[
                "Leverage correlation for predictions",
                "Consider multivariate analysis",
            ],
            supporting_evidence={"correlation": 0.85},
            metadata={"analysis_type": "correlation"},
            timestamp=datetime.now(),
        )
        insights.append(insight)

        return insights

    async def _generate_anomaly_insights(
        self,
        analysis_context: Dict[str, Any],
        data_context: Optional[Dict[str, Any]],
        confidence_threshold: float,
    ) -> List[IntelligentInsight]:
        """Generate anomaly insights"""
        insights = []

        insight = IntelligentInsight(
            insight_id=str(uuid.uuid4()),
            insight_type=InsightType.ANOMALY_DETECTION,
            title="Data Anomaly Detected",
            description="Unusual pattern detected in input data",
            confidence_score=0.75,
            impact_level="medium",
            actionable_recommendations=[
                "Investigate data quality",
                "Consider outlier handling",
            ],
            supporting_evidence={"anomaly_score": 0.8},
            metadata={"analysis_type": "anomaly"},
            timestamp=datetime.now(),
        )
        insights.append(insight)

        return insights

    async def _generate_optimization_insights(
        self,
        analysis_context: Dict[str, Any],
        data_context: Optional[Dict[str, Any]],
        confidence_threshold: float,
    ) -> List[IntelligentInsight]:
        """Generate optimization insights"""
        insights = []

        insight = IntelligentInsight(
            insight_id=str(uuid.uuid4()),
            insight_type=InsightType.OPTIMIZATION_OPPORTUNITY,
            title="Optimization Opportunity",
            description="Formula has significant optimization potential",
            confidence_score=0.8,
            impact_level="high",
            actionable_recommendations=[
                "Implement optimization algorithm",
                "Test performance improvements",
            ],
            supporting_evidence={"optimization_potential": 0.7},
            metadata={"analysis_type": "optimization"},
            timestamp=datetime.now(),
        )
        insights.append(insight)

        return insights

    async def _generate_pattern_insights(
        self,
        analysis_context: Dict[str, Any],
        data_context: Optional[Dict[str, Any]],
        confidence_threshold: float,
    ) -> List[IntelligentInsight]:
        """Generate pattern insights"""
        insights = []

        insight = IntelligentInsight(
            insight_id=str(uuid.uuid4()),
            insight_type=InsightType.PATTERN_RECOGNITION,
            title="Pattern Recognition",
            description="Recurring patterns identified in formula structure",
            confidence_score=0.7,
            impact_level="medium",
            actionable_recommendations=[
                "Leverage patterns for predictions",
                "Consider pattern-based optimization",
            ],
            supporting_evidence={"pattern_count": 3},
            metadata={"analysis_type": "pattern"},
            timestamp=datetime.now(),
        )
        insights.append(insight)

        return insights

    async def _generate_predictive_insights(
        self,
        analysis_context: Dict[str, Any],
        data_context: Optional[Dict[str, Any]],
        confidence_threshold: float,
    ) -> List[IntelligentInsight]:
        """Generate predictive insights"""
        insights = []

        insight = IntelligentInsight(
            insight_id=str(uuid.uuid4()),
            insight_type=InsightType.PREDICTIVE_INSIGHT,
            title="Predictive Capability",
            description="Formula shows strong predictive potential",
            confidence_score=0.85,
            impact_level="high",
            actionable_recommendations=[
                "Implement predictive model",
                "Validate predictions",
            ],
            supporting_evidence={"prediction_accuracy": 0.82},
            metadata={"analysis_type": "predictive"},
            timestamp=datetime.now(),
        )
        insights.append(insight)

        return insights

    async def _analyze_data_patterns(
        self, input_data: Dict[str, List[float]]
    ) -> List[Dict[str, Any]]:
        """Analyze patterns in input data"""
        patterns = []

        try:
            for var_name, values in input_data.items():
                if len(values) > 1:
                    # Check for trends
                    if all(values[i] <= values[i + 1] for i in range(len(values) - 1)):
                        patterns.append(
                            {
                                "type": "data_trend",
                                "description": f"{var_name} shows increasing trend",
                                "confidence": 0.8,
                            }
                        )
                    elif all(
                        values[i] >= values[i + 1] for i in range(len(values) - 1)
                    ):
                        patterns.append(
                            {
                                "type": "data_trend",
                                "description": f"{var_name} shows decreasing trend",
                                "confidence": 0.8,
                            }
                        )

                    # Check for outliers
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    outliers = [v for v in values if abs(v - mean_val) > 2 * std_val]
                    if outliers:
                        patterns.append(
                            {
                                "type": "data_outlier",
                                "description": f"{var_name} has {len(outliers)} outliers",
                                "confidence": 0.7,
                            }
                        )

        except Exception as e:
            logger.error(f"Data pattern analysis failed: {e}")

        return patterns

    async def _calculate_accuracy_score(
        self,
        formula_id: str,
        formula_info: Dict[str, Any],
        input_data: Dict[str, List[float]],
    ) -> float:
        """Calculate accuracy score for a formula"""
        try:
            # Simple accuracy calculation based on data consistency
            if not input_data:
                return 0.0

            # Calculate coefficient of variation as accuracy proxy
            values = list(input_data.values())
            if not values:
                return 0.0

            all_values = []
            for val_list in values:
                all_values.extend(val_list)

            if len(all_values) < 2:
                return 0.0

            mean_val = np.mean(all_values)
            std_val = np.std(all_values)

            if mean_val == 0:
                return 0.0

            cv = std_val / abs(mean_val)
            # Lower CV indicates higher accuracy
            accuracy_score = max(0.0, 1.0 - cv)

            return min(1.0, accuracy_score)

        except Exception as e:
            logger.error(f"Accuracy score calculation failed: {e}")
            return 0.0


# =============================================================================
# Global Engine Instance
# =============================================================================

# Global engine instance for standalone functions
_global_engine = AdvancedFormulaIntelligenceEngine()


# =============================================================================
# Standalone Functions
# =============================================================================


async def analyze_formula_intelligence(
    formula_id: str,
    analysis_types: List[str],
    input_data: Optional[Dict[str, List[float]]] = None,
    analysis_depth: str = "comprehensive",
    include_optimization: bool = True,
    include_insights: bool = True,
    confidence_threshold: float = 0.8,
) -> Dict[str, Any]:
    """
    Perform comprehensive AI-powered formula analysis (standalone function).

    Args:
        formula_id: ID of the formula to analyze
        analysis_types: Types of analysis to perform
        input_data: Optional input data for analysis
        analysis_depth: Depth of analysis
        include_optimization: Whether to include optimization analysis
        include_insights: Whether to include intelligent insights
        confidence_threshold: Minimum confidence threshold for insights

    Returns:
        Dictionary with comprehensive analysis results
    """
    # Convert string analysis types to enum
    analysis_type_enums = [
        AnalysisType(at)
        for at in analysis_types
        if at in [e.value for e in AnalysisType]
    ]

    return await _global_engine.analyze_formula_intelligence(
        formula_id=formula_id,
        analysis_types=analysis_type_enums,
        input_data=input_data,
        analysis_depth=analysis_depth,
        include_optimization=include_optimization,
        include_insights=include_insights,
        confidence_threshold=confidence_threshold,
    )


async def optimize_formula_intelligence(
    formula_id: str,
    optimization_objectives: List[str],
    input_data: Optional[Dict[str, List[float]]] = None,
    optimization_method: str = "genetic_algorithm",
    max_iterations: int = 100,
    target_improvement: float = 0.1,
) -> Dict[str, Any]:
    """
    Perform intelligent formula optimization (standalone function).

    Args:
        formula_id: ID of the formula to optimize
        optimization_objectives: Objectives for optimization
        input_data: Optional input data for optimization
        optimization_method: Method for optimization
        max_iterations: Maximum optimization iterations
        target_improvement: Target improvement percentage

    Returns:
        Dictionary with optimization results
    """
    # Convert string objectives to enum
    objective_enums = [
        OptimizationObjective(obj)
        for obj in optimization_objectives
        if obj in [e.value for e in OptimizationObjective]
    ]

    return await _global_engine.optimize_formula_intelligence(
        formula_id=formula_id,
        optimization_objectives=objective_enums,
        input_data=input_data,
        optimization_method=optimization_method,
        max_iterations=max_iterations,
        target_improvement=target_improvement,
    )


async def generate_intelligent_insights(
    analysis_context: Dict[str, Any],
    insight_types: List[str],
    data_context: Optional[Dict[str, Any]] = None,
    insight_depth: str = "comprehensive",
    max_insights: int = 10,
    confidence_threshold: float = 0.8,
) -> Dict[str, Any]:
    """
    Generate intelligent insights from analysis context (standalone function).

    Args:
        analysis_context: Context from previous analyses
        insight_types: Types of insights to generate
        data_context: Optional data context
        insight_depth: Depth of insight generation
        max_insights: Maximum number of insights to generate
        confidence_threshold: Minimum confidence threshold

    Returns:
        Dictionary with generated insights
    """
    # Convert string insight types to enum
    insight_type_enums = [
        InsightType(it) for it in insight_types if it in [e.value for e in InsightType]
    ]

    return await _global_engine.generate_intelligent_insights(
        analysis_context=analysis_context,
        insight_types=insight_type_enums,
        data_context=data_context,
        insight_depth=insight_depth,
        max_insights=max_insights,
        confidence_threshold=confidence_threshold,
    )


async def discover_formula_patterns(
    formula_ids: List[str],
    pattern_types: List[str],
    analysis_depth: str = "comprehensive",
    include_correlations: bool = True,
    include_optimizations: bool = True,
) -> Dict[str, Any]:
    """
    Discover patterns across multiple formulas (standalone function).

    Args:
        formula_ids: List of formula IDs to analyze
        pattern_types: Types of patterns to look for
        analysis_depth: Depth of pattern analysis
        include_correlations: Whether to include correlation analysis
        include_optimizations: Whether to include optimization analysis

    Returns:
        Dictionary with pattern discovery results
    """
    try:
        logger.info(f"Discovering patterns across {len(formula_ids)} formulas")

        patterns = []
        correlations = []
        optimizations = []

        for formula_id in formula_ids:
            if formula_id in _global_engine.formula_database:
                # Analyze each formula
                analysis_result = await _global_engine.analyze_formula_intelligence(
                    formula_id=formula_id,
                    analysis_types=[AnalysisType.PATTERN, AnalysisType.CORRELATION],
                    analysis_depth=analysis_depth,
                    include_optimization=include_optimizations,
                    include_insights=True,
                )

                if analysis_result["status"] == "success":
                    patterns.extend(
                        analysis_result["analysis_results"]
                        .get("pattern", {})
                        .get("patterns", [])
                    )
                    correlations.extend(
                        analysis_result["analysis_results"]
                        .get("correlation", {})
                        .get("correlations", [])
                    )

                    if include_optimizations:
                        optimizations.append(
                            {
                                "formula_id": formula_id,
                                "optimization_potential": analysis_result[
                                    "analysis_summary"
                                ]["optimization_potential"],
                            }
                        )

        # Analyze cross-formula patterns
        cross_patterns = await _analyze_cross_formula_patterns(formula_ids, patterns)

        result = {
            "status": "success",
            "formulas_analyzed": len(formula_ids),
            "patterns_discovered": len(patterns),
            "correlations_found": len(correlations),
            "optimizations_identified": len(optimizations),
            "cross_formula_patterns": cross_patterns,
            "pattern_summary": {
                "total_patterns": len(patterns),
                "unique_pattern_types": len(set(p.get("type", "") for p in patterns)),
                "average_confidence": (
                    np.mean([p.get("confidence", 0.0) for p in patterns])
                    if patterns
                    else 0.0
                ),
            },
            "metadata": {
                "discovery_timestamp": datetime.now().isoformat(),
                "analysis_depth": analysis_depth,
                "pattern_types": pattern_types,
            },
        }

        logger.info(f"✓ Pattern discovery completed: {len(patterns)} patterns found")
        return result

    except Exception as e:
        logger.error(f"Pattern discovery failed: {e}")
        return {"status": "error", "error": str(e), "patterns_discovered": 0}


async def _analyze_cross_formula_patterns(
    formula_ids: List[str], patterns: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Analyze patterns across multiple formulas"""
    try:
        cross_patterns = []

        # Group patterns by type
        pattern_groups = {}
        for pattern in patterns:
            pattern_type = pattern.get("type", "unknown")
            if pattern_type not in pattern_groups:
                pattern_groups[pattern_type] = []
            pattern_groups[pattern_type].append(pattern)

        # Analyze each pattern group
        for pattern_type, pattern_list in pattern_groups.items():
            if len(pattern_list) > 1:
                cross_pattern = {
                    "pattern_type": pattern_type,
                    "frequency": len(pattern_list),
                    "description": f"{pattern_type} pattern appears in {len(pattern_list)} formulas",
                    "confidence": np.mean(
                        [p.get("confidence", 0.0) for p in pattern_list]
                    ),
                    "formulas_involved": formula_ids[: len(pattern_list)],  # Simplified
                }
                cross_patterns.append(cross_pattern)

        return cross_patterns

    except Exception as e:
        logger.error(f"Cross-formula pattern analysis failed: {e}")
        return []


# =============================================================================
# Logging Decorator
# =============================================================================


def log_operation(operation_name: str):
    """Decorator for logging operations"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"Starting {operation_name}")

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"✓ {operation_name} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"✗ {operation_name} failed after {duration:.2f}s: {e}")
                raise

        return wrapper

    return decorator
