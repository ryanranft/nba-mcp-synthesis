"""
Phase 7.1: Intelligent Formula Recommendations System

This module provides AI-powered formula recommendations based on user context,
usage patterns, and intelligent analysis of sports analytics needs.

Features:
- Context-aware formula recommendations
- User preference learning
- Formula suggestion based on data patterns
- Predictive analytics recommendations
- Intelligent error correction
- Smart context analysis
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import sympy as sp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class RecommendationType(Enum):
    """Types of formula recommendations"""
    EFFICIENCY = "efficiency"
    SHOOTING = "shooting"
    DEFENSIVE = "defensive"
    TEAM = "team"
    PLAYER = "player"
    ADVANCED = "advanced"
    PREDICTIVE = "predictive"
    CUSTOM = "custom"


class ConfidenceLevel(Enum):
    """Confidence levels for recommendations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class UserExpertiseLevel(Enum):
    """User expertise levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class FormulaRecommendation:
    """A formula recommendation with metadata"""
    formula_id: str
    formula_name: str
    formula_expression: str
    recommendation_type: RecommendationType
    confidence_score: float
    explanation: str
    use_case: str
    prerequisites: List[str] = field(default_factory=list)
    related_formulas: List[str] = field(default_factory=list)
    complexity_level: str = "moderate"
    created_at: datetime = field(default_factory=datetime.now)
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class UserContext:
    """User context for recommendations"""
    user_id: Optional[str] = None
    expertise_level: UserExpertiseLevel = UserExpertiseLevel.INTERMEDIATE
    preferred_formula_types: List[str] = field(default_factory=list)
    current_analysis: Optional[str] = None
    session_history: List[Dict[str, Any]] = field(default_factory=list)
    recent_formulas: List[str] = field(default_factory=list)
    analysis_depth: str = "detailed"


@dataclass
class RecommendationContext:
    """Context for generating recommendations"""
    user_query: str
    data_description: Optional[str] = None
    available_variables: List[str] = field(default_factory=list)
    target_metric: Optional[str] = None
    analysis_type: str = "all"
    user_context: Optional[UserContext] = None


# =============================================================================
# Core Recommendation Engine
# =============================================================================

class IntelligentRecommendationEngine:
    """
    AI-powered formula recommendation engine that provides intelligent
    suggestions based on user context, data patterns, and usage history.
    """

    def __init__(self):
        """Initialize the recommendation engine"""
        self.formula_database = self._load_formula_database()
        self.user_preferences = {}
        self.usage_patterns = {}
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self._build_formula_embeddings()

        logger.info("Intelligent Recommendation Engine initialized")

    def _load_formula_database(self) -> Dict[str, Dict[str, Any]]:
        """Load the comprehensive formula database"""
        try:
            from .algebra_helper import get_sports_formula

            # Get all available formulas
            formulas = {}

            # Common sports analytics formulas
            formula_list = [
                "per", "true_shooting", "usage_rate", "effective_fg_percentage",
                "offensive_rating", "defensive_rating", "pace", "win_shares",
                "box_plus_minus", "vorp", "game_score", "pie",
                "corner_3pt_pct", "rim_fg_pct", "midrange_efficiency",
                "catch_shoot_pct", "defensive_win_shares", "steal_pct",
                "block_pct", "assist_percentage", "rebound_percentage",
                "turnover_percentage", "free_throw_rate", "clutch_performance",
                "on_off_differential", "plus_minus_per_100", "offensive_box_plus_minus",
                "defensive_box_plus_minus", "offensive_win_shares", "pace_adjusted_stats",
                "clutch_time_rating", "defensive_impact", "offensive_impact",
                "shooting_efficiency_differential", "possession_usage",
                "defensive_rebound_percentage", "offensive_rebound_percentage",
                "team_efficiency_differential", "pace_adjusted_offensive_rating",
                "pace_adjusted_defensive_rating"
            ]

            for formula_id in formula_list:
                try:
                    formula_info = get_sports_formula(formula_id)
                    if formula_info:
                        formulas[formula_id] = {
                            "name": formula_info.get("name", formula_id),
                            "expression": formula_info.get("expression", ""),
                            "description": formula_info.get("description", ""),
                            "variables": formula_info.get("variables", {}),
                            "category": self._categorize_formula(formula_id),
                            "complexity": self._assess_complexity(formula_info.get("expression", "")),
                            "use_cases": self._identify_use_cases(formula_id)
                        }
                except Exception as e:
                    logger.warning(f"Could not load formula {formula_id}: {e}")
                    continue

            logger.info(f"Loaded {len(formulas)} formulas into database")
            return formulas

        except Exception as e:
            logger.error(f"Error loading formula database: {e}")
            return {}

    def _categorize_formula(self, formula_id: str) -> str:
        """Categorize formula by type"""
        categories = {
            "per": "efficiency",
            "true_shooting": "shooting",
            "effective_fg_percentage": "shooting",
            "usage_rate": "efficiency",
            "offensive_rating": "team",
            "defensive_rating": "defensive",
            "pace": "team",
            "win_shares": "efficiency",
            "box_plus_minus": "advanced",
            "vorp": "advanced",
            "game_score": "efficiency",
            "pie": "efficiency",
            "corner_3pt_pct": "shooting",
            "rim_fg_pct": "shooting",
            "midrange_efficiency": "shooting",
            "catch_shoot_pct": "shooting",
            "defensive_win_shares": "defensive",
            "steal_pct": "defensive",
            "block_pct": "defensive",
            "assist_percentage": "player",
            "rebound_percentage": "player",
            "turnover_percentage": "player",
            "free_throw_rate": "shooting",
            "clutch_performance": "advanced",
            "on_off_differential": "advanced",
            "plus_minus_per_100": "advanced",
            "offensive_box_plus_minus": "advanced",
            "defensive_box_plus_minus": "advanced",
            "offensive_win_shares": "efficiency",
            "pace_adjusted_stats": "advanced",
            "clutch_time_rating": "advanced",
            "defensive_impact": "defensive",
            "offensive_impact": "offensive",
            "shooting_efficiency_differential": "shooting",
            "possession_usage": "efficiency",
            "defensive_rebound_percentage": "defensive",
            "offensive_rebound_percentage": "offensive",
            "team_efficiency_differential": "team",
            "pace_adjusted_offensive_rating": "team",
            "pace_adjusted_defensive_rating": "team"
        }
        return categories.get(formula_id, "general")

    def _assess_complexity(self, expression: str) -> str:
        """Assess formula complexity"""
        if not expression:
            return "simple"

        # Count operations and variables
        operation_count = len(re.findall(r'[+\-*/]', expression))
        variable_count = len(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', expression))

        if operation_count <= 3 and variable_count <= 3:
            return "simple"
        elif operation_count <= 6 and variable_count <= 6:
            return "moderate"
        else:
            return "complex"

    def _identify_use_cases(self, formula_id: str) -> List[str]:
        """Identify common use cases for formula"""
        use_cases = {
            "per": ["player evaluation", "performance comparison", "MVP analysis"],
            "true_shooting": ["shooting efficiency", "scoring analysis", "player comparison"],
            "usage_rate": ["player workload", "team role analysis", "injury risk"],
            "offensive_rating": ["team performance", "offensive analysis", "game planning"],
            "defensive_rating": ["defensive analysis", "team comparison", "strategy evaluation"],
            "pace": ["game tempo", "team style", "matchup analysis"],
            "win_shares": ["player value", "team contribution", "contract analysis"],
            "box_plus_minus": ["advanced analytics", "player impact", "lineup analysis"],
            "vorp": ["player value", "replacement level", "team building"],
            "game_score": ["single game analysis", "performance tracking", "player comparison"]
        }
        return use_cases.get(formula_id, ["general analysis"])

    def _build_formula_embeddings(self):
        """Build TF-IDF embeddings for formula descriptions"""
        try:
            descriptions = []
            self.formula_ids = []

            for formula_id, formula_info in self.formula_database.items():
                description = f"{formula_info.get('name', '')} {formula_info.get('description', '')} {' '.join(formula_info.get('use_cases', []))}"
                descriptions.append(description)
                self.formula_ids.append(formula_id)

            if descriptions:
                self.formula_embeddings = self.vectorizer.fit_transform(descriptions)
                logger.info(f"Built embeddings for {len(descriptions)} formulas")
            else:
                self.formula_embeddings = None
                logger.warning("No descriptions available for embedding")

        except Exception as e:
            logger.error(f"Error building formula embeddings: {e}")
            self.formula_embeddings = None

    def get_intelligent_recommendations(
        self,
        context: RecommendationContext,
        max_recommendations: int = 5,
        confidence_threshold: float = 0.7
    ) -> List[FormulaRecommendation]:
        """
        Get intelligent formula recommendations based on context

        Args:
            context: Recommendation context
            max_recommendations: Maximum number of recommendations
            confidence_threshold: Minimum confidence threshold

        Returns:
            List of formula recommendations
        """
        try:
            logger.info(f"Generating recommendations for context: {context.user_query[:50]}...")

            # Analyze context
            context_analysis = self._analyze_context(context)

            # Generate recommendations based on different strategies
            recommendations = []

            # Strategy 1: Semantic similarity
            semantic_recs = self._get_semantic_recommendations(context, context_analysis)
            recommendations.extend(semantic_recs)

            # Strategy 2: Category-based recommendations
            category_recs = self._get_category_recommendations(context, context_analysis)
            recommendations.extend(category_recs)

            # Strategy 3: User preference-based recommendations
            preference_recs = self._get_preference_recommendations(context, context_analysis)
            recommendations.extend(preference_recs)

            # Strategy 4: Data pattern-based recommendations
            pattern_recs = self._get_pattern_recommendations(context, context_analysis)
            recommendations.extend(pattern_recs)

            # Remove duplicates and filter by confidence
            unique_recommendations = self._deduplicate_recommendations(recommendations)
            filtered_recommendations = [
                rec for rec in unique_recommendations
                if rec.confidence_score >= confidence_threshold
            ]

            # Sort by confidence and relevance
            sorted_recommendations = sorted(
                filtered_recommendations,
                key=lambda x: (x.confidence_score, self._calculate_relevance_score(x, context)),
                reverse=True
            )

            # Return top recommendations
            final_recommendations = sorted_recommendations[:max_recommendations]

            logger.info(f"Generated {len(final_recommendations)} recommendations")
            return final_recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return self._get_fallback_recommendations(context.analysis_type, max_recommendations)

    def _analyze_context(self, context: RecommendationContext) -> Dict[str, Any]:
        """Analyze the recommendation context"""
        analysis = {
            "keywords": self._extract_keywords(context.user_query),
            "analysis_type": context.analysis_type,
            "target_metric": context.target_metric,
            "available_variables": context.available_variables,
            "user_expertise": context.user_context.expertise_level if context.user_context else UserExpertiseLevel.INTERMEDIATE,
            "preferred_categories": [],
            "complexity_preference": "moderate"
        }

        # Extract preferred categories from query
        query_lower = context.user_query.lower()
        if any(word in query_lower for word in ["shooting", "shot", "scoring", "points"]):
            analysis["preferred_categories"].append("shooting")
        if any(word in query_lower for word in ["defense", "defensive", "defend", "steal", "block"]):
            analysis["preferred_categories"].append("defensive")
        if any(word in query_lower for word in ["efficiency", "effective", "per", "rating"]):
            analysis["preferred_categories"].append("efficiency")
        if any(word in query_lower for word in ["team", "teamwork", "lineup", "rotation"]):
            analysis["preferred_categories"].append("team")
        if any(word in query_lower for word in ["advanced", "complex", "sophisticated"]):
            analysis["complexity_preference"] = "complex"
        elif any(word in query_lower for word in ["simple", "basic", "easy"]):
            analysis["complexity_preference"] = "simple"

        return analysis

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        # Filter out common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have",
            "has", "had", "do", "does", "did", "will", "would", "could", "should",
            "may", "might", "can", "this", "that", "these", "those", "i", "you",
            "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"
        }

        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords

    def _get_semantic_recommendations(
        self,
        context: RecommendationContext,
        analysis: Dict[str, Any]
    ) -> List[FormulaRecommendation]:
        """Get recommendations based on semantic similarity"""
        recommendations = []

        if not self.formula_embeddings:
            return recommendations

        try:
            # Create query embedding
            query_text = f"{context.user_query} {context.data_description or ''}"
            query_embedding = self.vectorizer.transform([query_text])

            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.formula_embeddings)[0]

            # Get top similar formulas
            top_indices = np.argsort(similarities)[::-1][:10]

            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    formula_id = self.formula_ids[idx]
                    formula_info = self.formula_database[formula_id]

                    recommendation = FormulaRecommendation(
                        formula_id=formula_id,
                        formula_name=formula_info["name"],
                        formula_expression=formula_info["expression"],
                        recommendation_type=RecommendationType(formula_info["category"]),
                        confidence_score=float(similarities[idx]),
                        explanation=f"Semantically similar to your query about {analysis['keywords'][:3] if analysis['keywords'] else 'sports analytics'}",
                        use_case=formula_info["use_cases"][0] if formula_info["use_cases"] else "general analysis",
                        complexity_level=formula_info["complexity"]
                    )
                    recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error in semantic recommendations: {e}")

        return recommendations

    def _get_category_recommendations(
        self,
        context: RecommendationContext,
        analysis: Dict[str, Any]
    ) -> List[FormulaRecommendation]:
        """Get recommendations based on category matching"""
        recommendations = []

        target_categories = analysis["preferred_categories"]
        if not target_categories:
            target_categories = [context.analysis_type] if context.analysis_type != "all" else ["efficiency", "shooting", "defensive"]

        for formula_id, formula_info in self.formula_database.items():
            if formula_info["category"] in target_categories:
                # Calculate confidence based on category match and complexity preference
                confidence = 0.8 if formula_info["category"] in target_categories else 0.5

                # Adjust confidence based on complexity preference
                if analysis["complexity_preference"] == formula_info["complexity"]:
                    confidence += 0.1
                elif analysis["complexity_preference"] == "simple" and formula_info["complexity"] == "complex":
                    confidence -= 0.2

                recommendation = FormulaRecommendation(
                    formula_id=formula_id,
                    formula_name=formula_info["name"],
                    formula_expression=formula_info["expression"],
                    recommendation_type=RecommendationType(formula_info["category"]),
                    confidence_score=confidence,
                    explanation=f"Recommended for {formula_info['category']} analysis based on your query",
                    use_case=formula_info["use_cases"][0] if formula_info["use_cases"] else "general analysis",
                    complexity_level=formula_info["complexity"]
                )
                recommendations.append(recommendation)

        return recommendations

    def _get_preference_recommendations(
        self,
        context: RecommendationContext,
        analysis: Dict[str, Any]
    ) -> List[FormulaRecommendation]:
        """Get recommendations based on user preferences"""
        recommendations = []

        if not context.user_context:
            return recommendations

        # Get user's preferred formula types
        preferred_types = context.user_context.preferred_formula_types
        if not preferred_types:
            return recommendations

        for formula_id, formula_info in self.formula_database.items():
            if any(pref_type in formula_info["name"].lower() or pref_type in formula_info["category"]
                   for pref_type in preferred_types):

                recommendation = FormulaRecommendation(
                    formula_id=formula_id,
                    formula_name=formula_info["name"],
                    formula_expression=formula_info["expression"],
                    recommendation_type=RecommendationType(formula_info["category"]),
                    confidence_score=0.9,  # High confidence for user preferences
                    explanation=f"Matches your preference for {preferred_types[0]} formulas",
                    use_case=formula_info["use_cases"][0] if formula_info["use_cases"] else "general analysis",
                    complexity_level=formula_info["complexity"]
                )
                recommendations.append(recommendation)

        return recommendations

    def _get_pattern_recommendations(
        self,
        context: RecommendationContext,
        analysis: Dict[str, Any]
    ) -> List[FormulaRecommendation]:
        """Get recommendations based on data patterns"""
        recommendations = []

        if not context.available_variables:
            return recommendations

        # Match formulas based on available variables
        for formula_id, formula_info in self.formula_database.items():
            formula_vars = set(formula_info["variables"].keys())
            available_vars = set(context.available_variables)

            # Calculate overlap
            overlap = len(formula_vars.intersection(available_vars))
            total_vars = len(formula_vars)

            if overlap > 0:
                confidence = overlap / total_vars

                recommendation = FormulaRecommendation(
                    formula_id=formula_id,
                    formula_name=formula_info["name"],
                    formula_expression=formula_info["expression"],
                    recommendation_type=RecommendationType(formula_info["category"]),
                    confidence_score=confidence,
                    explanation=f"Uses {overlap}/{total_vars} of your available variables",
                    use_case=formula_info["use_cases"][0] if formula_info["use_cases"] else "general analysis",
                    complexity_level=formula_info["complexity"]
                )
                recommendations.append(recommendation)

        return recommendations

    def _deduplicate_recommendations(
        self,
        recommendations: List[FormulaRecommendation]
    ) -> List[FormulaRecommendation]:
        """Remove duplicate recommendations, keeping the highest confidence"""
        seen = {}

        for rec in recommendations:
            if rec.formula_id not in seen or seen[rec.formula_id].confidence_score < rec.confidence_score:
                seen[rec.formula_id] = rec

        return list(seen.values())

    def _calculate_relevance_score(
        self,
        recommendation: FormulaRecommendation,
        context: RecommendationContext
    ) -> float:
        """Calculate relevance score for recommendation"""
        score = 0.0

        # Base score from confidence
        score += recommendation.confidence_score * 0.5

        # Bonus for matching analysis type
        if context.analysis_type != "all" and recommendation.recommendation_type.value == context.analysis_type:
            score += 0.3

        # Bonus for matching user expertise level
        if context.user_context:
            if context.user_context.expertise_level == UserExpertiseLevel.BEGINNER and recommendation.complexity_level == "simple":
                score += 0.2
            elif context.user_context.expertise_level == UserExpertiseLevel.EXPERT and recommendation.complexity_level == "complex":
                score += 0.2

        return min(score, 1.0)

    def suggest_formulas_from_data(
        self,
        data_description: str,
        available_variables: List[str],
        target_metric: Optional[str] = None,
        formula_complexity: str = "any",
        max_suggestions: int = 3
    ) -> List[FormulaRecommendation]:
        """
        Suggest formulas based on available data and variables

        Args:
            data_description: Description of the data
            available_variables: List of available variables
            target_metric: Target metric to predict
            formula_complexity: Desired complexity level
            max_suggestions: Maximum number of suggestions

        Returns:
            List of formula suggestions
        """
        try:
            logger.info(f"Suggesting formulas for data with {len(available_variables)} variables")

            suggestions = []

            # Create context for pattern-based recommendations
            context = RecommendationContext(
                user_query=f"Analyze {data_description} with variables {', '.join(available_variables)}",
                data_description=data_description,
                available_variables=available_variables,
                target_metric=target_metric
            )

            # Get pattern-based recommendations
            pattern_recs = self._get_pattern_recommendations(context, self._analyze_context(context))

            # Filter by complexity if specified
            if formula_complexity != "any":
                pattern_recs = [
                    rec for rec in pattern_recs
                    if rec.complexity_level == formula_complexity
                ]

            # Sort by confidence and return top suggestions
            sorted_suggestions = sorted(pattern_recs, key=lambda x: x.confidence_score, reverse=True)

            return sorted_suggestions[:max_suggestions]

        except Exception as e:
            logger.error(f"Error suggesting formulas from data: {e}")
            return []

    def analyze_user_context(
        self,
        user_query: str,
        session_history: Optional[List[Dict[str, Any]]] = None,
        current_analysis: Optional[str] = None,
        user_expertise_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Analyze user context for better recommendations

        Args:
            user_query: User's query or request
            session_history: Previous session history
            current_analysis: Current analysis being performed
            user_expertise_level: User's expertise level

        Returns:
            Context analysis results
        """
        try:
            logger.info(f"Analyzing user context for query: {user_query[:50]}...")

            analysis = {
                "keywords": self._extract_keywords(user_query),
                "expertise_level": user_expertise_level,
                "analysis_type": self._infer_analysis_type(user_query),
                "complexity_preference": self._infer_complexity_preference(user_query, user_expertise_level),
                "preferred_categories": self._infer_preferred_categories(user_query),
                "session_patterns": self._analyze_session_patterns(session_history) if session_history else {},
                "recommendation_strategy": self._determine_recommendation_strategy(user_query, user_expertise_level)
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing user context: {e}")
            return {}

    def _infer_analysis_type(self, query: str) -> str:
        """Infer the type of analysis from user query"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["shooting", "shot", "scoring", "points", "fg", "3pt"]):
            return "shooting"
        elif any(word in query_lower for word in ["defense", "defensive", "defend", "steal", "block"]):
            return "defensive"
        elif any(word in query_lower for word in ["efficiency", "effective", "per", "rating", "win shares"]):
            return "efficiency"
        elif any(word in query_lower for word in ["team", "teamwork", "lineup", "rotation"]):
            return "team"
        elif any(word in query_lower for word in ["player", "individual", "personal"]):
            return "player"
        elif any(word in query_lower for word in ["advanced", "complex", "sophisticated", "bpm", "vorp"]):
            return "advanced"
        else:
            return "all"

    def _infer_complexity_preference(self, query: str, expertise_level: str) -> str:
        """Infer complexity preference from query and expertise"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["simple", "basic", "easy", "straightforward"]):
            return "simple"
        elif any(word in query_lower for word in ["complex", "advanced", "sophisticated", "detailed"]):
            return "complex"
        elif expertise_level == "beginner":
            return "simple"
        elif expertise_level == "expert":
            return "complex"
        else:
            return "moderate"

    def _infer_preferred_categories(self, query: str) -> List[str]:
        """Infer preferred categories from query"""
        categories = []
        query_lower = query.lower()

        if any(word in query_lower for word in ["shooting", "shot", "scoring", "points"]):
            categories.append("shooting")
        if any(word in query_lower for word in ["defense", "defensive", "defend"]):
            categories.append("defensive")
        if any(word in query_lower for word in ["efficiency", "effective", "per"]):
            categories.append("efficiency")
        if any(word in query_lower for word in ["team", "teamwork", "lineup"]):
            categories.append("team")
        if any(word in query_lower for word in ["player", "individual"]):
            categories.append("player")
        if any(word in query_lower for word in ["advanced", "complex", "bpm", "vorp"]):
            categories.append("advanced")

        return categories if categories else ["efficiency", "shooting", "defensive"]

    def _analyze_session_patterns(self, session_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze session history for patterns"""
        if not session_history:
            return {}

        patterns = {
            "frequent_formulas": [],
            "preferred_categories": [],
            "average_complexity": "moderate",
            "session_length": len(session_history)
        }

        # Analyze frequent formulas
        formula_counts = {}
        category_counts = {}
        complexity_counts = {"simple": 0, "moderate": 0, "complex": 0}

        for session in session_history:
            if "formula_id" in session:
                formula_id = session["formula_id"]
                formula_counts[formula_id] = formula_counts.get(formula_id, 0) + 1

                # Get formula info
                if formula_id in self.formula_database:
                    formula_info = self.formula_database[formula_id]
                    category = formula_info["category"]
                    complexity = formula_info["complexity"]

                    category_counts[category] = category_counts.get(category, 0) + 1
                    complexity_counts[complexity] += 1

        # Set patterns
        patterns["frequent_formulas"] = sorted(formula_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        patterns["preferred_categories"] = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # Determine average complexity
        total_complexity = sum(complexity_counts.values())
        if total_complexity > 0:
            if complexity_counts["complex"] / total_complexity > 0.5:
                patterns["average_complexity"] = "complex"
            elif complexity_counts["simple"] / total_complexity > 0.5:
                patterns["average_complexity"] = "simple"
            else:
                patterns["average_complexity"] = "moderate"

        return patterns

    def _determine_recommendation_strategy(self, query: str, expertise_level: str) -> str:
        """Determine the best recommendation strategy"""
        if expertise_level == "beginner":
            return "category_based"
        elif expertise_level == "expert":
            return "semantic_similarity"
        else:
            return "hybrid"

    def get_predictive_recommendations(
        self,
        prediction_target: str,
        historical_data_description: str,
        prediction_horizon: str = "medium_term",
        confidence_level: float = 0.95
    ) -> List[FormulaRecommendation]:
        """
        Get recommendations for predictive analytics

        Args:
            prediction_target: Target variable for prediction
            historical_data_description: Description of historical data
            prediction_horizon: Time horizon for predictions
            confidence_level: Desired confidence level

        Returns:
            List of predictive formula recommendations
        """
        try:
            logger.info(f"Generating predictive recommendations for {prediction_target}")

            # Create context for predictive analysis
            context = RecommendationContext(
                user_query=f"Predict {prediction_target} using {historical_data_description}",
                data_description=historical_data_description,
                target_metric=prediction_target,
                analysis_type="predictive"
            )

            # Get recommendations
            recommendations = self.get_intelligent_recommendations(context, max_recommendations=5)

            # Filter for predictive formulas
            predictive_formulas = [
                "pace", "offensive_rating", "defensive_rating", "win_shares",
                "box_plus_minus", "vorp", "game_score", "pie"
            ]

            predictive_recs = [
                rec for rec in recommendations
                if rec.formula_id in predictive_formulas
            ]

            # Adjust confidence based on prediction horizon
            for rec in predictive_recs:
                if prediction_horizon == "short_term":
                    rec.confidence_score *= 1.1
                elif prediction_horizon == "long_term":
                    rec.confidence_score *= 0.9

                rec.explanation = f"Recommended for predicting {prediction_target} over {prediction_horizon} horizon"

            return predictive_recs

        except Exception as e:
            logger.error(f"Error generating predictive recommendations: {e}")
            return []

    def detect_and_correct_errors(
        self,
        formula_expression: str,
        expected_result: Optional[float] = None,
        input_values: Optional[Dict[str, float]] = None,
        error_tolerance: float = 0.01
    ) -> Dict[str, Any]:
        """
        Detect and suggest corrections for formula errors

        Args:
            formula_expression: Formula expression to analyze
            expected_result: Expected result if known
            input_values: Input values for testing
            error_tolerance: Tolerance for error detection

        Returns:
            Error analysis and correction suggestions
        """
        try:
            logger.info(f"Analyzing formula for errors: {formula_expression[:50]}...")

            analysis = {
                "has_errors": False,
                "error_types": [],
                "correction_suggestions": [],
                "confidence": 0.0,
                "validated_result": None
            }

            # Parse and validate formula
            try:
                expr = sp.parse_expr(formula_expression)
                analysis["confidence"] += 0.3
            except Exception as e:
                analysis["has_errors"] = True
                analysis["error_types"].append("syntax_error")
                analysis["correction_suggestions"].append(f"Syntax error: {str(e)}")
                return analysis

            # Check for common errors
            if "//" in formula_expression:
                analysis["has_errors"] = True
                analysis["error_types"].append("integer_division")
                analysis["correction_suggestions"].append("Use '/' instead of '//' for division")

            if "**" in formula_expression and "**" not in ["**2", "**3"]:
                analysis["has_errors"] = True
                analysis["error_types"].append("exponentiation")
                analysis["correction_suggestions"].append("Consider using '^' or 'pow()' for exponentiation")

            # Test with input values if provided
            if input_values:
                try:
                    # Substitute values
                    substituted_expr = expr.subs(input_values)
                    result = float(substituted_expr.evalf())
                    analysis["validated_result"] = result
                    analysis["confidence"] += 0.4

                    # Compare with expected result
                    if expected_result is not None:
                        error_magnitude = abs(result - expected_result) / abs(expected_result) if expected_result != 0 else abs(result)
                        if error_magnitude > error_tolerance:
                            analysis["has_errors"] = True
                            analysis["error_types"].append("calculation_error")
                            analysis["correction_suggestions"].append(f"Result {result} differs from expected {expected_result}")
                        else:
                            analysis["confidence"] += 0.3

                except Exception as e:
                    analysis["has_errors"] = True
                    analysis["error_types"].append("evaluation_error")
                    analysis["correction_suggestions"].append(f"Evaluation error: {str(e)}")

            return analysis

        except Exception as e:
            logger.error(f"Error in error detection: {e}")
            return {
                "has_errors": True,
                "error_types": ["analysis_error"],
                "correction_suggestions": [f"Analysis error: {str(e)}"],
                "confidence": 0.0,
                "validated_result": None
            }


    def _get_semantic_recommendations(self, context: RecommendationContext, analysis: Dict[str, Any]) -> List[FormulaRecommendation]:
        """Get recommendations based on semantic similarity"""
        try:
            recommendations = []
            if not self.formula_embeddings:
                return recommendations

            # Simple keyword-based matching for now
            keywords = analysis.get("keywords", [])
            for formula_id, formula_info in self.formula_database.items():
                score = 0.0
                formula_text = f"{formula_info['name']} {formula_info['description']}".lower()

                for keyword in keywords:
                    if keyword.lower() in formula_text:
                        score += 0.2

                if score > 0.0:
                    recommendation = FormulaRecommendation(
                        formula_id=formula_id,
                        formula_name=formula_info["name"],
                        formula_expression=formula_info["expression"],
                        confidence_score=min(score, 0.9),
                        explanation=f"Recommended based on semantic similarity to '{context.user_query}'",
                        recommendation_type=RecommendationType.SEMANTIC_SIMILARITY,
                        complexity_level=self._assess_complexity(formula_info["expression"]),
                        use_cases=self._identify_use_cases(formula_id),
                        category=self._categorize_formula(formula_id)
                    )
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting semantic recommendations: {e}")
            return []

    def _get_category_recommendations(self, context: RecommendationContext, analysis: Dict[str, Any]) -> List[FormulaRecommendation]:
        """Get recommendations based on category analysis"""
        try:
            recommendations = []
            analysis_type = context.analysis_type

            for formula_id, formula_info in self.formula_database.items():
                category = self._categorize_formula(formula_id)

                if analysis_type == "all" or analysis_type in category:
                    recommendation = FormulaRecommendation(
                        formula_id=formula_id,
                        formula_name=formula_info["name"],
                        formula_expression=formula_info["expression"],
                        confidence_score=0.7,
                        explanation=f"Recommended for {analysis_type} analysis",
                        recommendation_type=RecommendationType.CATEGORY_BASED,
                        complexity_level=self._assess_complexity(formula_info["expression"]),
                        use_cases=self._identify_use_cases(formula_id),
                        category=category
                    )
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting category recommendations: {e}")
            return []

    def _get_preference_recommendations(self, context: RecommendationContext, analysis: Dict[str, Any]) -> List[FormulaRecommendation]:
        """Get recommendations based on user preferences"""
        try:
            recommendations = []
            user_expertise = analysis.get("user_expertise", UserExpertiseLevel.INTERMEDIATE)

            for formula_id, formula_info in self.formula_database.items():
                complexity = self._assess_complexity(formula_info["expression"])

                # Match complexity to expertise level
                if (user_expertise == UserExpertiseLevel.BEGINNER and complexity == "simple") or \
                   (user_expertise == UserExpertiseLevel.INTERMEDIATE and complexity in ["simple", "moderate"]) or \
                   (user_expertise == UserExpertiseLevel.ADVANCED and complexity in ["moderate", "complex"]) or \
                   (user_expertise == UserExpertiseLevel.EXPERT):

                    recommendation = FormulaRecommendation(
                        formula_id=formula_id,
                        formula_name=formula_info["name"],
                        formula_expression=formula_info["expression"],
                        confidence_score=0.6,
                        explanation=f"Recommended based on {user_expertise.value} expertise level",
                        recommendation_type=RecommendationType.USER_PREFERENCE,
                        complexity_level=complexity,
                        use_cases=self._identify_use_cases(formula_id),
                        category=self._categorize_formula(formula_id)
                    )
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting preference recommendations: {e}")
            return []

    def _get_pattern_recommendations(self, context: RecommendationContext, analysis: Dict[str, Any]) -> List[FormulaRecommendation]:
        """Get recommendations based on data patterns"""
        try:
            recommendations = []
            available_variables = context.available_variables or []

            if not available_variables:
                return recommendations

            for formula_id, formula_info in self.formula_database.items():
                expression = formula_info["expression"]
                variable_matches = 0

                # Count how many available variables are used in the formula
                for var in available_variables:
                    if var.lower() in expression.lower():
                        variable_matches += 1

                if variable_matches > 0:
                    score = variable_matches / len(available_variables)
                    recommendation = FormulaRecommendation(
                        formula_id=formula_id,
                        formula_name=formula_info["name"],
                        formula_expression=formula_info["expression"],
                        confidence_score=score,
                        explanation=f"Uses {variable_matches} of your available variables",
                        recommendation_type=RecommendationType.DATA_PATTERN,
                        complexity_level=self._assess_complexity(formula_info["expression"]),
                        use_cases=self._identify_use_cases(formula_id),
                        category=self._categorize_formula(formula_id)
                    )
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting pattern recommendations: {e}")
            return []

    def _deduplicate_recommendations(self, recommendations: List[FormulaRecommendation]) -> List[FormulaRecommendation]:
        """Remove duplicate recommendations"""
        seen = set()
        unique = []

        for rec in recommendations:
            if rec.formula_id not in seen:
                seen.add(rec.formula_id)
                unique.append(rec)

        return unique

    def _calculate_relevance_score(self, recommendation: FormulaRecommendation, context: RecommendationContext) -> float:
        """Calculate relevance score for a recommendation"""
        score = 0.0

        # Base score from confidence
        score += recommendation.confidence_score * 0.5

        # Bonus for matching analysis type
        if context.analysis_type in recommendation.category:
            score += 0.3

        # Bonus for appropriate complexity
        if context.user_context and context.user_context.expertise_level == UserExpertiseLevel.BEGINNER:
            if recommendation.complexity_level == "simple":
                score += 0.2
        elif context.user_context and context.user_context.expertise_level == UserExpertiseLevel.EXPERT:
            if recommendation.complexity_level == "complex":
                score += 0.2

        return min(score, 1.0)

    def _get_fallback_recommendations(self, analysis_type: str, max_recommendations: int) -> List[FormulaRecommendation]:
        """Get fallback recommendations when intelligent analysis fails"""
        try:
            # Get basic recommendations based on analysis type
            fallback_formulas = {
                "efficiency": ["per", "true_shooting", "usage_rate"],
                "shooting": ["true_shooting", "effective_field_goal_percentage", "free_throw_rate"],
                "defensive": ["defensive_rating", "steal_percentage", "block_percentage"],
                "team": ["pace", "offensive_efficiency", "defensive_efficiency"],
                "player": ["per", "game_score", "vorp"],
                "advanced": ["bpm_offensive", "bpm_defensive", "win_shares_offensive"],
                "all": ["per", "true_shooting", "defensive_rating", "pace", "game_score"]
            }

            formula_ids = fallback_formulas.get(analysis_type, fallback_formulas["all"])
            recommendations = []

            for formula_id in formula_ids[:max_recommendations]:
                if formula_id in self.formula_database:
                    formula_info = self.formula_database[formula_id]
                    recommendation = FormulaRecommendation(
                        formula_id=formula_id,
                        formula_name=formula_info["name"],
                        formula_expression=formula_info["expression"],
                        confidence_score=0.6,  # Moderate confidence for fallback
                        explanation=f"Recommended based on {analysis_type} analysis",
                        recommendation_type=RecommendationType.CATEGORY_BASED,
                        complexity_level=self._assess_complexity(formula_info["expression"]),
                        use_cases=self._identify_use_cases(formula_id),
                        category=self._categorize_formula(formula_id)
                    )
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting fallback recommendations: {e}")
            return []


# =============================================================================
# Standalone Functions for MCP Tools
# =============================================================================

def get_intelligent_recommendations(
    context: str,
    user_preferences: Optional[Dict[str, Any]] = None,
    current_formulas: Optional[List[str]] = None,
    analysis_type: str = "all",
    max_recommendations: int = 5,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Get intelligent formula recommendations based on context

    Args:
        context: Context description for recommendations
        user_preferences: User preferences and settings
        current_formulas: List of formulas currently being used
        analysis_type: Type of analysis being performed
        max_recommendations: Maximum number of recommendations
        confidence_threshold: Minimum confidence threshold

    Returns:
        Dictionary with recommendations and metadata
    """
    try:
        # Initialize engine
        engine = IntelligentRecommendationEngine()

        # Create user context
        user_context = UserContext(
            preferred_formula_types=user_preferences.get("preferred_types", []) if user_preferences else [],
            expertise_level=UserExpertiseLevel(user_preferences.get("expertise_level", "intermediate")) if user_preferences else UserExpertiseLevel.INTERMEDIATE,
            recent_formulas=current_formulas or []
        )

        # Create recommendation context
        rec_context = RecommendationContext(
            user_query=context,
            analysis_type=analysis_type,
            user_context=user_context
        )

        # Get recommendations
        recommendations = engine.get_intelligent_recommendations(
            rec_context,
            max_recommendations=max_recommendations,
            confidence_threshold=confidence_threshold
        )

        # Convert to dictionary format
        result = {
            "status": "success",
            "recommendations": [],
            "total_recommendations": len(recommendations),
            "context_analysis": engine._analyze_context(rec_context),
            "metadata": {
                "analysis_type": analysis_type,
                "confidence_threshold": confidence_threshold,
                "max_recommendations": max_recommendations
            }
        }

        for rec in recommendations:
            rec_dict = {
                "formula_id": rec.formula_id,
                "formula_name": rec.formula_name,
                "formula_expression": rec.formula_expression,
                "recommendation_type": rec.recommendation_type.value,
                "confidence_score": rec.confidence_score,
                "explanation": rec.explanation,
                "use_case": rec.use_case,
                "complexity_level": rec.complexity_level,
                "recommendation_id": rec.recommendation_id
            }
            result["recommendations"].append(rec_dict)

        return result

    except Exception as e:
        logger.error(f"Error in get_intelligent_recommendations: {e}")
        return {
            "status": "error",
            "error": str(e),
            "recommendations": [],
            "total_recommendations": 0
        }


def suggest_formulas_from_data_patterns(
    data_description: str,
    available_variables: List[str],
    target_metric: Optional[str] = None,
    formula_complexity: str = "any",
    max_suggestions: int = 3
) -> Dict[str, Any]:
    """
    Suggest formulas based on data patterns and available variables

    Args:
        data_description: Description of the data
        available_variables: List of available variables
        target_metric: Target metric to predict
        formula_complexity: Desired complexity level
        max_suggestions: Maximum number of suggestions

    Returns:
        Dictionary with formula suggestions
    """
    try:
        # Initialize engine
        engine = IntelligentRecommendationEngine()

        # Get suggestions
        suggestions = engine.suggest_formulas_from_data(
            data_description,
            available_variables,
            target_metric,
            formula_complexity,
            max_suggestions
        )

        # Convert to dictionary format
        result = {
            "status": "success",
            "suggestions": [],
            "total_suggestions": len(suggestions),
            "data_analysis": {
                "data_description": data_description,
                "available_variables": available_variables,
                "target_metric": target_metric,
                "formula_complexity": formula_complexity
            }
        }

        for suggestion in suggestions:
            suggestion_dict = {
                "formula_id": suggestion.formula_id,
                "formula_name": suggestion.formula_name,
                "formula_expression": suggestion.formula_expression,
                "recommendation_type": suggestion.recommendation_type.value,
                "confidence_score": suggestion.confidence_score,
                "explanation": suggestion.explanation,
                "use_case": suggestion.use_case,
                "complexity_level": suggestion.complexity_level,
                "recommendation_id": suggestion.recommendation_id
            }
            result["suggestions"].append(suggestion_dict)

        return result

    except Exception as e:
        logger.error(f"Error in suggest_formulas_from_data_patterns: {e}")
        return {
            "status": "error",
            "error": str(e),
            "suggestions": [],
            "total_suggestions": 0
        }


def analyze_user_context_for_recommendations(
    user_query: str,
    session_history: Optional[List[Dict[str, Any]]] = None,
    current_analysis: Optional[str] = None,
    user_expertise_level: str = "intermediate"
) -> Dict[str, Any]:
    """
    Analyze user context for better recommendations

    Args:
        user_query: User's query or request
        session_history: Previous session history
        current_analysis: Current analysis being performed
        user_expertise_level: User's expertise level

    Returns:
        Context analysis results
    """
    try:
        # Initialize engine
        engine = IntelligentRecommendationEngine()

        # Analyze context
        analysis = engine.analyze_user_context(
            user_query,
            session_history,
            current_analysis,
            user_expertise_level
        )

        return {
            "status": "success",
            "context_analysis": analysis,
            "recommendations": {
                "analysis_type": analysis.get("analysis_type", "all"),
                "complexity_preference": analysis.get("complexity_preference", "moderate"),
                "preferred_categories": analysis.get("preferred_categories", []),
                "recommendation_strategy": analysis.get("recommendation_strategy", "hybrid")
            }
        }

    except Exception as e:
        logger.error(f"Error in analyze_user_context_for_recommendations: {e}")
        return {
            "status": "error",
            "error": str(e),
            "context_analysis": {}
        }


def get_predictive_analytics_recommendations(
    prediction_target: str,
    historical_data_description: str,
    prediction_horizon: str = "medium_term",
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Get recommendations for predictive analytics

    Args:
        prediction_target: Target variable for prediction
        historical_data_description: Description of historical data
        prediction_horizon: Time horizon for predictions
        confidence_level: Desired confidence level

    Returns:
        Dictionary with predictive recommendations
    """
    try:
        # Initialize engine
        engine = IntelligentRecommendationEngine()

        # Get recommendations
        recommendations = engine.get_predictive_recommendations(
            prediction_target,
            historical_data_description,
            prediction_horizon,
            confidence_level
        )

        # Convert to dictionary format
        result = {
            "status": "success",
            "recommendations": [],
            "total_recommendations": len(recommendations),
            "predictive_analysis": {
                "prediction_target": prediction_target,
                "historical_data_description": historical_data_description,
                "prediction_horizon": prediction_horizon,
                "confidence_level": confidence_level
            }
        }

        for rec in recommendations:
            rec_dict = {
                "formula_id": rec.formula_id,
                "formula_name": rec.formula_name,
                "formula_expression": rec.formula_expression,
                "recommendation_type": rec.recommendation_type.value,
                "confidence_score": rec.confidence_score,
                "explanation": rec.explanation,
                "use_case": rec.use_case,
                "complexity_level": rec.complexity_level,
                "recommendation_id": rec.recommendation_id
            }
            result["recommendations"].append(rec_dict)

        return result

    except Exception as e:
        logger.error(f"Error in get_predictive_analytics_recommendations: {e}")
        return {
            "status": "error",
            "error": str(e),
            "recommendations": [],
            "total_recommendations": 0
        }


def detect_and_correct_formula_errors(
    formula_expression: str,
    expected_result: Optional[float] = None,
    input_values: Optional[Dict[str, float]] = None,
    error_tolerance: float = 0.01
) -> Dict[str, Any]:
    """
    Detect and suggest corrections for formula errors

    Args:
        formula_expression: Formula expression to analyze
        expected_result: Expected result if known
        input_values: Input values for testing
        error_tolerance: Tolerance for error detection

    Returns:
        Error analysis and correction suggestions
    """
    try:
        # Initialize engine
        engine = IntelligentRecommendationEngine()

        # Detect errors
        analysis = engine.detect_and_correct_errors(
            formula_expression,
            expected_result,
            input_values,
            error_tolerance
        )

        return {
            "status": "success",
            "error_analysis": analysis,
            "formula_expression": formula_expression,
            "correction_recommendations": analysis.get("correction_suggestions", [])
        }

    except Exception as e:
        logger.error(f"Error in detect_and_correct_formula_errors: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_analysis": {
                "has_errors": True,
                "error_types": ["analysis_error"],
                "correction_suggestions": [f"Analysis error: {str(e)}"],
                "confidence": 0.0
            }
        }
