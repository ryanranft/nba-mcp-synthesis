"""
Smart Context Analysis Module for Phase 7.3

This module provides intelligent context analysis capabilities for the NBA MCP Server,
including user behavior analysis, contextual recommendations, session management,
and intelligent insight generation.

Author: NBA MCP Server Team
Phase: 7.3 - Smart Context Analysis
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


# =============================================================================
# Data Structures
# =============================================================================


class ContextDepth(Enum):
    """Context analysis depth levels"""

    SHALLOW = "shallow"
    MODERATE = "moderate"
    DEEP = "deep"


class ExpertiseLevel(Enum):
    """User expertise levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class BehaviorType(Enum):
    """Types of user behavior to analyze"""

    FORMULA_USAGE = "formula_usage"
    QUERY_PATTERNS = "query_patterns"
    PREFERENCES = "preferences"
    ERRORS = "errors"
    SUCCESSES = "successes"


class ContextType(Enum):
    """Types of context data"""

    USER_PREFERENCES = "user_preferences"
    ANALYSIS_STATE = "analysis_state"
    FORMULA_HISTORY = "formula_history"
    DATA_CONTEXT = "data_context"


class InsightType(Enum):
    """Types of insights to generate"""

    PATTERN = "pattern"
    ANOMALY = "anomaly"
    TREND = "trend"
    CORRELATION = "correlation"
    PREDICTION = "prediction"
    OPTIMIZATION = "optimization"


@dataclass
class ContextInsight:
    """Context insight data structure"""

    insight_id: str
    insight_type: str
    title: str
    description: str
    confidence: float
    relevance_score: float
    actionable: bool
    category: str
    metadata: Dict[str, Any]


@dataclass
class BehaviorPattern:
    """User behavior pattern data structure"""

    pattern_id: str
    pattern_type: str
    frequency: int
    confidence: float
    description: str
    examples: List[str]
    predictions: List[str]
    metadata: Dict[str, Any]


@dataclass
class ContextualRecommendation:
    """Contextual recommendation data structure"""

    recommendation_id: str
    recommendation_type: str
    title: str
    description: str
    confidence: float
    personalization_score: float
    reasoning: str
    alternatives: List[str]
    metadata: Dict[str, Any]


@dataclass
class SessionContext:
    """Session context data structure"""

    session_id: str
    context_type: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    metadata: Dict[str, Any]


# =============================================================================
# Core Smart Context Analysis Engine
# =============================================================================


class SmartContextAnalysisEngine:
    """
    Core engine for intelligent context analysis and recommendations.

    Provides capabilities for:
    - User context analysis
    - Behavior pattern recognition
    - Contextual recommendations
    - Session management
    - Intelligent insight generation
    """

    def __init__(self):
        """Initialize the smart context analysis engine"""
        self.session_contexts: Dict[str, SessionContext] = {}
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.behavior_patterns: Dict[str, List[BehaviorPattern]] = {}
        self.context_cache: Dict[str, Any] = {}

        # Initialize with default patterns
        self._initialize_default_patterns()

        logger.info("Smart Context Analysis Engine initialized")

    def _initialize_default_patterns(self):
        """Initialize default behavior patterns and context templates"""
        try:
            # Default behavior patterns
            self.default_patterns = {
                "formula_usage": {
                    "efficiency_focused": "User frequently uses efficiency metrics like PER, TS%, and Usage Rate",
                    "defensive_focused": "User shows preference for defensive metrics and analysis",
                    "shooting_focused": "User primarily analyzes shooting statistics and percentages",
                    "team_focused": "User focuses on team-level metrics and analysis",
                },
                "query_patterns": {
                    "comparative": "User frequently asks for comparisons between players or teams",
                    "predictive": "User often requests predictive analysis and forecasting",
                    "diagnostic": "User asks diagnostic questions about performance issues",
                    "exploratory": "User explores data with open-ended questions",
                },
            }

            # Context templates
            self.context_templates = {
                "analysis_state": {
                    "current_formulas": [],
                    "analysis_goals": [],
                    "data_sources": [],
                    "progress": 0.0,
                },
                "user_preferences": {
                    "expertise_level": "intermediate",
                    "preferred_formulas": [],
                    "analysis_style": "balanced",
                    "visualization_preference": "charts",
                },
            }

            logger.info("Default patterns and templates initialized")

        except Exception as e:
            logger.error(f"Error initializing default patterns: {e}")

    def analyze_user_context_intelligently(
        self,
        user_query: str,
        session_history: Optional[List[Dict[str, Any]]] = None,
        available_data: Optional[Dict[str, Any]] = None,
        analysis_goals: Optional[List[str]] = None,
        expertise_level: str = "intermediate",
        preferred_formulas: Optional[List[str]] = None,
        context_depth: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Perform intelligent analysis of user context.

        Args:
            user_query: User's query or request
            session_history: Previous session interactions
            available_data: Available data sources and variables
            analysis_goals: User's analysis goals
            expertise_level: User's expertise level
            preferred_formulas: User's preferred formulas
            context_depth: Depth of analysis to perform

        Returns:
            Dictionary with context analysis results
        """
        try:
            logger.info(f"Analyzing user context: {context_depth} depth")

            # Extract context elements
            context_elements = self._extract_context_elements(
                user_query, session_history, available_data
            )

            # Analyze query intent
            query_intent = self._analyze_query_intent(user_query, context_elements)

            # Generate insights based on depth
            insights = self._generate_context_insights(
                context_elements, query_intent, context_depth
            )

            # Analyze user expertise and preferences
            user_profile = self._analyze_user_profile(
                expertise_level, preferred_formulas, session_history
            )

            # Generate recommendations if requested
            recommendations = []
            if context_depth in ["moderate", "deep"]:
                recommendations = self._generate_context_recommendations(
                    context_elements, user_profile, query_intent
                )

            result = {
                "status": "success",
                "context_analysis": {
                    "query_intent": query_intent,
                    "context_elements": context_elements,
                    "user_profile": user_profile,
                    "insights": [asdict(insight) for insight in insights],
                    "recommendations": [asdict(rec) for rec in recommendations],
                    "analysis_depth": context_depth,
                    "confidence_score": self._calculate_context_confidence(
                        context_elements
                    ),
                },
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "context_depth": context_depth,
                    "insights_count": len(insights),
                    "recommendations_count": len(recommendations),
                },
            }

            logger.info(
                f"Context analysis completed: {len(insights)} insights, {len(recommendations)} recommendations"
            )
            return result

        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "context_analysis": {},
                "metadata": {},
            }

    def analyze_user_behavior_patterns(
        self,
        user_id: str,
        time_period: str = "session",
        behavior_types: List[str] = None,
        include_patterns: bool = True,
        include_predictions: bool = True,
        privacy_level: str = "basic",
    ) -> Dict[str, Any]:
        """
        Analyze user behavior patterns for personalization.

        Args:
            user_id: Unique user identifier
            time_period: Time period for analysis
            behavior_types: Types of behavior to analyze
            include_patterns: Whether to identify patterns
            include_predictions: Whether to predict future behavior
            privacy_level: Level of detail in analysis

        Returns:
            Dictionary with behavior analysis results
        """
        try:
            logger.info(f"Analyzing behavior patterns for user: {user_id}")

            if behavior_types is None:
                behavior_types = ["formula_usage", "query_patterns"]

            # Get user behavior data
            behavior_data = self._get_user_behavior_data(user_id, time_period)

            # Analyze each behavior type
            behavior_analysis = {}
            patterns = []

            for behavior_type in behavior_types:
                analysis = self._analyze_behavior_type(
                    behavior_data, behavior_type, privacy_level
                )
                behavior_analysis[behavior_type] = analysis

                if include_patterns:
                    behavior_patterns = self._identify_behavior_patterns(
                        analysis, behavior_type
                    )
                    patterns.extend(behavior_patterns)

            # Generate predictions if requested
            predictions = []
            if include_predictions and patterns:
                predictions = self._generate_behavior_predictions(patterns, user_id)

            # Update user profile
            self._update_user_profile(user_id, behavior_analysis, patterns)

            result = {
                "status": "success",
                "behavior_analysis": {
                    "user_id": user_id,
                    "time_period": time_period,
                    "behavior_types": behavior_types,
                    "analysis_results": behavior_analysis,
                    "patterns": [asdict(pattern) for pattern in patterns],
                    "predictions": predictions,
                    "privacy_level": privacy_level,
                },
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "patterns_count": len(patterns),
                    "predictions_count": len(predictions),
                    "privacy_compliant": True,
                },
            }

            logger.info(
                f"Behavior analysis completed: {len(patterns)} patterns, {len(predictions)} predictions"
            )
            return result

        except Exception as e:
            logger.error(f"Behavior analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "behavior_analysis": {},
                "metadata": {},
            }

    def generate_contextual_recommendations(
        self,
        context_analysis: Dict[str, Any],
        recommendation_count: int = 5,
        recommendation_types: List[str] = None,
        personalization_level: str = "basic",
        include_alternatives: bool = True,
        explanation_depth: str = "detailed",
        confidence_threshold: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Generate contextual recommendations based on analysis.

        Args:
            context_analysis: Results from context analysis
            recommendation_count: Number of recommendations to generate
            recommendation_types: Types of recommendations to include
            personalization_level: Level of personalization
            include_alternatives: Whether to include alternatives
            explanation_depth: Depth of explanations
            confidence_threshold: Minimum confidence threshold

        Returns:
            Dictionary with contextual recommendations
        """
        try:
            logger.info(f"Generating {recommendation_count} contextual recommendations")

            # Handle empty context analysis
            if not context_analysis:
                logger.warning(
                    "Empty context analysis provided, using fallback recommendations"
                )
                return self._generate_fallback_recommendations(
                    recommendation_count, recommendation_types, personalization_level
                )

            if recommendation_types is None:
                recommendation_types = ["formula"]

            # Extract context elements
            query_intent = context_analysis.get("query_intent", {})
            user_profile = context_analysis.get("user_profile", {})
            insights = context_analysis.get("insights", [])

            # Generate recommendations for each type
            recommendations = []

            for rec_type in recommendation_types:
                type_recommendations = self._generate_type_recommendations(
                    rec_type,
                    query_intent,
                    user_profile,
                    insights,
                    personalization_level,
                    confidence_threshold,
                )
                recommendations.extend(type_recommendations)

            # Sort by confidence and relevance
            recommendations = sorted(
                recommendations,
                key=lambda x: (x.confidence, x.personalization_score),
                reverse=True,
            )[:recommendation_count]

            # Add alternatives if requested
            alternatives = []
            if include_alternatives and recommendations:
                alternatives = self._generate_alternative_recommendations(
                    recommendations, explanation_depth
                )

            result = {
                "status": "success",
                "recommendations": [asdict(rec) for rec in recommendations],
                "alternatives": alternatives,
                "metadata": {
                    "generation_timestamp": datetime.now().isoformat(),
                    "recommendation_count": len(recommendations),
                    "personalization_level": personalization_level,
                    "explanation_depth": explanation_depth,
                    "confidence_threshold": confidence_threshold,
                },
            }

            logger.info(
                f"Contextual recommendations generated: {len(recommendations)} recommendations"
            )
            return result

        except Exception as e:
            logger.error(f"Contextual recommendation generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "recommendations": [],
                "metadata": {},
            }

    def manage_session_context(
        self,
        session_id: str,
        context_data: Dict[str, Any],
        context_type: str = "analysis_state",
        operation: str = "store",
        expiration_time: Optional[int] = None,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Manage session context data.

        Args:
            session_id: Unique session identifier
            context_data: Context data to manage
            context_type: Type of context data
            operation: Operation to perform
            expiration_time: Expiration time in seconds
            include_metadata: Whether to include metadata

        Returns:
            Dictionary with operation results
        """
        try:
            logger.info(f"Managing session context: {operation} for {session_id}")

            now = datetime.now()
            expires_at = None

            if expiration_time:
                expires_at = now + timedelta(seconds=expiration_time)

            if operation == "store":
                session_context = SessionContext(
                    session_id=session_id,
                    context_type=context_type,
                    data=context_data,
                    created_at=now,
                    updated_at=now,
                    expires_at=expires_at,
                    metadata=(
                        {"operation": "store", "timestamp": now.isoformat()}
                        if include_metadata
                        else {}
                    ),
                )
                self.session_contexts[session_id] = session_context

            elif operation == "retrieve":
                if session_id in self.session_contexts:
                    session_context = self.session_contexts[session_id]
                    # Check expiration
                    if session_context.expires_at and now > session_context.expires_at:
                        del self.session_contexts[session_id]
                        return {
                            "status": "error",
                            "error": "Session context expired",
                            "operation_result": {},
                        }
                    context_data = session_context.data
                else:
                    return {
                        "status": "error",
                        "error": "Session context not found",
                        "operation_result": {},
                    }

            elif operation == "update":
                if session_id in self.session_contexts:
                    session_context = self.session_contexts[session_id]
                    session_context.data.update(context_data)
                    session_context.updated_at = now
                    if include_metadata:
                        session_context.metadata["last_update"] = now.isoformat()
                else:
                    return {
                        "status": "error",
                        "error": "Session context not found for update",
                        "operation_result": {},
                    }

            elif operation == "clear":
                if session_id in self.session_contexts:
                    del self.session_contexts[session_id]
                context_data = {}
                expires_at = None

            result = {
                "status": "success",
                "operation_result": {
                    "session_id": session_id,
                    "operation": operation,
                    "context_type": context_type,
                    "context_data": context_data,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "metadata": (
                        self.session_contexts.get(
                            session_id,
                            SessionContext(
                                "", "", {}, datetime.now(), datetime.now(), None, {}
                            ),
                        ).metadata
                        if include_metadata
                        else {}
                    ),
                },
                "metadata": {
                    "operation_timestamp": now.isoformat(),
                    "session_count": len(self.session_contexts),
                },
            }

            logger.info(f"Session context {operation} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Session context management failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "operation_result": {},
                "metadata": {},
            }

    def generate_intelligent_insights(
        self,
        analysis_context: Dict[str, Any],
        insight_types: List[str] = None,
        insight_depth: str = "moderate",
        include_visualizations: bool = True,
        include_actionable_recommendations: bool = True,
        confidence_threshold: float = 0.7,
        max_insights: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate intelligent insights from analysis context.

        Args:
            analysis_context: Context from analysis results
            insight_types: Types of insights to generate
            insight_depth: Depth of insight analysis
            include_visualizations: Whether to include visualization suggestions
            include_actionable_recommendations: Whether to include actionable recommendations
            confidence_threshold: Minimum confidence for insights
            max_insights: Maximum number of insights to generate

        Returns:
            Dictionary with intelligent insights
        """
        try:
            logger.info(f"Generating intelligent insights: {insight_types}")

            if insight_types is None:
                insight_types = ["pattern", "trend"]

            # Extract analysis data
            analysis_data = self._extract_analysis_data(analysis_context)

            # Generate insights for each type
            insights = []

            for insight_type in insight_types:
                type_insights = self._generate_type_insights(
                    insight_type, analysis_data, insight_depth, confidence_threshold
                )
                insights.extend(type_insights)

            # Sort by confidence and relevance
            insights = sorted(
                insights, key=lambda x: (x.confidence, x.relevance_score), reverse=True
            )[:max_insights]

            # Add visualizations if requested
            visualizations = []
            if include_visualizations and insights:
                visualizations = self._generate_visualization_suggestions(insights)

            # Add actionable recommendations if requested
            actionable_recommendations = []
            if include_actionable_recommendations and insights:
                actionable_recommendations = self._generate_actionable_recommendations(
                    insights, analysis_data
                )

            result = {
                "status": "success",
                "insights": [asdict(insight) for insight in insights],
                "visualizations": visualizations,
                "actionable_recommendations": actionable_recommendations,
                "metadata": {
                    "generation_timestamp": datetime.now().isoformat(),
                    "insights_count": len(insights),
                    "insight_types": insight_types,
                    "insight_depth": insight_depth,
                    "confidence_threshold": confidence_threshold,
                },
            }

            logger.info(f"Intelligent insights generated: {len(insights)} insights")
            return result

        except Exception as e:
            logger.error(f"Intelligent insight generation failed: {e}")
            return {"status": "error", "error": str(e), "insights": [], "metadata": {}}

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _extract_context_elements(
        self,
        user_query: str,
        session_history: Optional[List[Dict[str, Any]]],
        available_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract context elements from user input"""
        try:
            elements = {
                "query_keywords": self._extract_keywords(user_query),
                "query_intent": self._classify_query_intent(user_query),
                "data_availability": available_data or {},
                "session_context": session_history or [],
                "temporal_context": self._analyze_temporal_context(session_history),
            }
            return elements
        except Exception as e:
            logger.error(f"Error extracting context elements: {e}")
            return {}

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from user query"""
        try:
            # Simple keyword extraction
            keywords = re.findall(r"\b\w+\b", query.lower())
            # Filter out common words
            stop_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
            }
            keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 2]
            return keywords[:10]  # Limit to top 10 keywords
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []

    def _classify_query_intent(self, query: str) -> str:
        """Classify the intent of the user query"""
        try:
            query_lower = query.lower()

            if any(
                word in query_lower
                for word in ["compare", "comparison", "vs", "versus"]
            ):
                return "comparative"
            elif any(
                word in query_lower
                for word in ["predict", "forecast", "future", "will"]
            ):
                return "predictive"
            elif any(word in query_lower for word in ["why", "what", "how", "explain"]):
                return "diagnostic"
            elif any(word in query_lower for word in ["show", "find", "get", "list"]):
                return "exploratory"
            else:
                return "general"
        except Exception as e:
            logger.error(f"Error classifying query intent: {e}")
            return "general"

    def _analyze_temporal_context(
        self, session_history: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze temporal context from session history"""
        try:
            if not session_history:
                return {"session_length": 0, "recent_activity": []}

            recent_activity = (
                session_history[-5:] if len(session_history) > 5 else session_history
            )
            return {
                "session_length": len(session_history),
                "recent_activity": recent_activity,
                "activity_pattern": (
                    "increasing" if len(session_history) > 3 else "stable"
                ),
            }
        except Exception as e:
            logger.error(f"Error analyzing temporal context: {e}")
            return {"session_length": 0, "recent_activity": []}

    def _analyze_query_intent(
        self, query: str, context_elements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze query intent with context"""
        try:
            intent = self._classify_query_intent(query)
            keywords = context_elements.get("query_keywords", [])

            return {
                "primary_intent": intent,
                "confidence": 0.8,  # Simplified confidence calculation
                "keywords": keywords,
                "complexity": (
                    "high"
                    if len(keywords) > 5
                    else "medium" if len(keywords) > 2 else "low"
                ),
                "domain": self._identify_domain(keywords),
            }
        except Exception as e:
            logger.error(f"Error analyzing query intent: {e}")
            return {
                "primary_intent": "general",
                "confidence": 0.5,
                "keywords": [],
                "complexity": "low",
                "domain": "general",
            }

    def _identify_domain(self, keywords: List[str]) -> str:
        """Identify the domain of the query based on keywords"""
        try:
            domain_keywords = {
                "efficiency": ["per", "efficiency", "rating", "usage"],
                "shooting": ["shooting", "fg", "3pt", "free throw"],
                "defensive": ["defense", "steal", "block", "rebound"],
                "team": ["team", "roster", "lineup", "chemistry"],
                "player": ["player", "individual", "personal"],
            }

            for domain, domain_kw in domain_keywords.items():
                if any(kw in keywords for kw in domain_kw):
                    return domain

            return "general"
        except Exception as e:
            logger.error(f"Error identifying domain: {e}")
            return "general"

    def _generate_context_insights(
        self,
        context_elements: Dict[str, Any],
        query_intent: Dict[str, Any],
        context_depth: str,
    ) -> List[ContextInsight]:
        """Generate context insights based on analysis depth"""
        try:
            insights = []

            # Basic insights for all depths
            if query_intent.get("primary_intent") == "comparative":
                insight = ContextInsight(
                    insight_id="comparative_intent",
                    insight_type="pattern",
                    title="Comparative Analysis Intent",
                    description="User is seeking comparative analysis between entities",
                    confidence=0.8,
                    relevance_score=0.9,
                    actionable=True,
                    category="intent",
                    metadata={"intent_type": "comparative"},
                )
                insights.append(insight)

            # Moderate and deep insights
            if context_depth in ["moderate", "deep"]:
                domain = query_intent.get("domain", "general")
                if domain != "general":
                    insight = ContextInsight(
                        insight_id=f"{domain}_domain",
                        insight_type="pattern",
                        title=f"{domain.title()} Domain Focus",
                        description=f"User is focusing on {domain} analysis",
                        confidence=0.7,
                        relevance_score=0.8,
                        actionable=True,
                        category="domain",
                        metadata={"domain": domain},
                    )
                    insights.append(insight)

            # Deep insights only
            if context_depth == "deep":
                complexity = query_intent.get("complexity", "low")
                if complexity == "high":
                    insight = ContextInsight(
                        insight_id="high_complexity",
                        insight_type="pattern",
                        title="High Complexity Query",
                        description="User is asking a complex question requiring detailed analysis",
                        confidence=0.6,
                        relevance_score=0.7,
                        actionable=True,
                        category="complexity",
                        metadata={"complexity": complexity},
                    )
                    insights.append(insight)

            return insights

        except Exception as e:
            logger.error(f"Error generating context insights: {e}")
            return []

    def _analyze_user_profile(
        self,
        expertise_level: str,
        preferred_formulas: Optional[List[str]],
        session_history: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Analyze user profile from provided information"""
        try:
            profile = {
                "expertise_level": expertise_level,
                "preferred_formulas": preferred_formulas or [],
                "analysis_style": self._determine_analysis_style(expertise_level),
                "experience_indicator": self._calculate_experience_indicator(
                    session_history
                ),
                "preferences": self._infer_preferences(
                    preferred_formulas, session_history
                ),
            }
            return profile
        except Exception as e:
            logger.error(f"Error analyzing user profile: {e}")
            return {
                "expertise_level": expertise_level,
                "preferred_formulas": [],
                "analysis_style": "balanced",
            }

    def _determine_analysis_style(self, expertise_level: str) -> str:
        """Determine analysis style based on expertise level"""
        style_mapping = {
            "beginner": "guided",
            "intermediate": "balanced",
            "advanced": "detailed",
            "expert": "comprehensive",
        }
        return style_mapping.get(expertise_level, "balanced")

    def _calculate_experience_indicator(
        self, session_history: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Calculate experience indicator from session history"""
        try:
            if not session_history:
                return 0.5  # Default moderate experience

            # Simple calculation based on session length and diversity
            session_count = len(session_history)
            diversity_score = len(
                set(str(interaction) for interaction in session_history)
            ) / max(session_count, 1)

            return min(0.2 + (session_count * 0.1) + (diversity_score * 0.3), 1.0)
        except Exception as e:
            logger.error(f"Error calculating experience indicator: {e}")
            return 0.5

    def _infer_preferences(
        self,
        preferred_formulas: Optional[List[str]],
        session_history: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Infer user preferences from available data"""
        try:
            preferences = {
                "formula_types": [],
                "analysis_depth": "moderate",
                "visualization_preference": "charts",
            }

            if preferred_formulas:
                # Analyze formula types
                efficiency_formulas = [
                    f
                    for f in preferred_formulas
                    if any(
                        term in f.lower() for term in ["per", "efficiency", "rating"]
                    )
                ]
                shooting_formulas = [
                    f
                    for f in preferred_formulas
                    if any(term in f.lower() for term in ["shooting", "fg", "3pt"])
                ]

                if efficiency_formulas:
                    preferences["formula_types"].append("efficiency")
                if shooting_formulas:
                    preferences["formula_types"].append("shooting")

            return preferences
        except Exception as e:
            logger.error(f"Error inferring preferences: {e}")
            return {
                "formula_types": [],
                "analysis_depth": "moderate",
                "visualization_preference": "charts",
            }

    def _generate_context_recommendations(
        self,
        context_elements: Dict[str, Any],
        user_profile: Dict[str, Any],
        query_intent: Dict[str, Any],
    ) -> List[ContextualRecommendation]:
        """Generate contextual recommendations"""
        try:
            recommendations = []

            # Generate recommendations based on intent
            intent = query_intent.get("primary_intent", "general")
            domain = query_intent.get("domain", "general")

            if intent == "comparative":
                rec = ContextualRecommendation(
                    recommendation_id="comparative_formulas",
                    recommendation_type="formula",
                    title="Comparative Analysis Formulas",
                    description="Use these formulas for comparative analysis",
                    confidence=0.8,
                    personalization_score=0.7,
                    reasoning="Based on comparative intent detected",
                    alternatives=["PER", "TS%", "Usage Rate"],
                    metadata={"intent": intent, "domain": domain},
                )
                recommendations.append(rec)

            # Generate domain-specific recommendations
            if domain != "general":
                rec = ContextualRecommendation(
                    recommendation_id=f"{domain}_formulas",
                    recommendation_type="formula",
                    title=f"{domain.title()} Analysis Formulas",
                    description=f"Recommended formulas for {domain} analysis",
                    confidence=0.7,
                    personalization_score=0.6,
                    reasoning=f"Based on {domain} domain focus",
                    alternatives=self._get_domain_formulas(domain),
                    metadata={"domain": domain},
                )
                recommendations.append(rec)

            return recommendations

        except Exception as e:
            logger.error(f"Error generating context recommendations: {e}")
            return []

    def _get_domain_formulas(self, domain: str) -> List[str]:
        """Get formulas relevant to a specific domain"""
        domain_formulas = {
            "efficiency": ["PER", "TS%", "Usage Rate", "eFG%"],
            "shooting": ["TS%", "eFG%", "3PT%", "FT%"],
            "defensive": ["Defensive Rating", "Steal%", "Block%", "DRB%"],
            "team": ["Pace", "Offensive Rating", "Defensive Rating", "Net Rating"],
            "player": ["PER", "Game Score", "VORP", "BPM"],
        }
        return domain_formulas.get(domain, ["PER", "TS%"])

    def _calculate_context_confidence(self, context_elements: Dict[str, Any]) -> float:
        """Calculate confidence score for context analysis"""
        try:
            confidence = 0.5  # Base confidence

            # Increase confidence based on available context
            if context_elements.get("query_keywords"):
                confidence += 0.2

            if context_elements.get("session_context"):
                confidence += 0.1

            if context_elements.get("data_availability"):
                confidence += 0.1

            return min(confidence, 1.0)
        except Exception as e:
            logger.error(f"Error calculating context confidence: {e}")
            return 0.5

    def _get_user_behavior_data(self, user_id: str, time_period: str) -> Dict[str, Any]:
        """Get user behavior data for analysis"""
        try:
            # This would typically connect to a database
            # For now, return mock data
            return {
                "formula_usage": ["PER", "TS%", "Usage Rate"],
                "query_patterns": [
                    "compare players",
                    "team analysis",
                    "shooting stats",
                ],
                "session_count": 5,
                "last_activity": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting user behavior data: {e}")
            return {}

    def _analyze_behavior_type(
        self, behavior_data: Dict[str, Any], behavior_type: str, privacy_level: str
    ) -> Dict[str, Any]:
        """Analyze specific behavior type"""
        try:
            if behavior_type == "formula_usage":
                return self._analyze_formula_usage(behavior_data, privacy_level)
            elif behavior_type == "query_patterns":
                return self._analyze_query_patterns(behavior_data, privacy_level)
            else:
                return {
                    "type": behavior_type,
                    "analysis": "Basic analysis",
                    "confidence": 0.5,
                }
        except Exception as e:
            logger.error(f"Error analyzing behavior type {behavior_type}: {e}")
            return {
                "type": behavior_type,
                "analysis": "Error in analysis",
                "confidence": 0.0,
            }

    def _analyze_formula_usage(
        self, behavior_data: Dict[str, Any], privacy_level: str
    ) -> Dict[str, Any]:
        """Analyze formula usage patterns"""
        try:
            formulas = behavior_data.get("formula_usage", [])
            usage_count = Counter(formulas)

            analysis = {
                "most_used": usage_count.most_common(3),
                "usage_diversity": len(set(formulas)),
                "preferred_categories": self._categorize_formulas(formulas),
                "privacy_level": privacy_level,
            }

            return analysis
        except Exception as e:
            logger.error(f"Error analyzing formula usage: {e}")
            return {"most_used": [], "usage_diversity": 0, "preferred_categories": []}

    def _analyze_query_patterns(
        self, behavior_data: Dict[str, Any], privacy_level: str
    ) -> Dict[str, Any]:
        """Analyze query patterns"""
        try:
            queries = behavior_data.get("query_patterns", [])

            analysis = {
                "query_types": self._classify_queries(queries),
                "query_complexity": self._assess_query_complexity(queries),
                "common_themes": self._extract_common_themes(queries),
                "privacy_level": privacy_level,
            }

            return analysis
        except Exception as e:
            logger.error(f"Error analyzing query patterns: {e}")
            return {
                "query_types": [],
                "query_complexity": "medium",
                "common_themes": [],
            }

    def _categorize_formulas(self, formulas: List[str]) -> List[str]:
        """Categorize formulas by type"""
        try:
            categories = []
            for formula in formulas:
                if any(
                    term in formula.lower() for term in ["per", "efficiency", "rating"]
                ):
                    categories.append("efficiency")
                elif any(term in formula.lower() for term in ["shooting", "fg", "3pt"]):
                    categories.append("shooting")
                elif any(
                    term in formula.lower() for term in ["defense", "steal", "block"]
                ):
                    categories.append("defensive")

            return list(set(categories))
        except Exception as e:
            logger.error(f"Error categorizing formulas: {e}")
            return []

    def _classify_queries(self, queries: List[str]) -> List[str]:
        """Classify query types"""
        try:
            types = []
            for query in queries:
                intent = self._classify_query_intent(query)
                types.append(intent)
            return list(set(types))
        except Exception as e:
            logger.error(f"Error classifying queries: {e}")
            return []

    def _assess_query_complexity(self, queries: List[str]) -> str:
        """Assess overall query complexity"""
        try:
            if not queries:
                return "low"

            avg_length = sum(len(query.split()) for query in queries) / len(queries)
            if avg_length > 5:
                return "high"
            elif avg_length > 3:
                return "medium"
            else:
                return "low"
        except Exception as e:
            logger.error(f"Error assessing query complexity: {e}")
            return "medium"

    def _extract_common_themes(self, queries: List[str]) -> List[str]:
        """Extract common themes from queries"""
        try:
            all_words = []
            for query in queries:
                words = re.findall(r"\b\w+\b", query.lower())
                all_words.extend(words)

            word_count = Counter(all_words)
            common_words = [
                word for word, count in word_count.most_common(5) if count > 1
            ]
            return common_words
        except Exception as e:
            logger.error(f"Error extracting common themes: {e}")
            return []

    def _identify_behavior_patterns(
        self, analysis: Dict[str, Any], behavior_type: str
    ) -> List[BehaviorPattern]:
        """Identify behavior patterns from analysis"""
        try:
            patterns = []

            if behavior_type == "formula_usage":
                most_used = analysis.get("most_used", [])
                if most_used:
                    pattern = BehaviorPattern(
                        pattern_id=f"formula_preference_{len(patterns)}",
                        pattern_type="formula_preference",
                        frequency=most_used[0][1] if most_used else 1,
                        confidence=0.8,
                        description=f"User prefers {most_used[0][0]} formula",
                        examples=[most_used[0][0]] if most_used else [],
                        predictions=["Likely to use similar formulas"],
                        metadata={"behavior_type": behavior_type},
                    )
                    patterns.append(pattern)

            return patterns
        except Exception as e:
            logger.error(f"Error identifying behavior patterns: {e}")
            return []

    def _generate_behavior_predictions(
        self, patterns: List[BehaviorPattern], user_id: str
    ) -> List[str]:
        """Generate behavior predictions from patterns"""
        try:
            predictions = []

            for pattern in patterns:
                if pattern.pattern_type == "formula_preference":
                    predictions.append(
                        f"User will likely continue using {pattern.examples[0]} formula"
                    )

            return predictions[:5]  # Limit to 5 predictions
        except Exception as e:
            logger.error(f"Error generating behavior predictions: {e}")
            return []

    def _update_user_profile(
        self,
        user_id: str,
        behavior_analysis: Dict[str, Any],
        patterns: List[BehaviorPattern],
    ):
        """Update user profile with behavior analysis results"""
        try:
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {}

            self.user_profiles[user_id].update(
                {
                    "last_analysis": datetime.now().isoformat(),
                    "behavior_analysis": behavior_analysis,
                    "patterns": [asdict(pattern) for pattern in patterns],
                    "profile_confidence": 0.7,
                }
            )
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")

    def _generate_type_recommendations(
        self,
        rec_type: str,
        query_intent: Dict[str, Any],
        user_profile: Dict[str, Any],
        insights: List[Dict[str, Any]],
        personalization_level: str,
        confidence_threshold: float,
    ) -> List[ContextualRecommendation]:
        """Generate recommendations for specific type"""
        try:
            recommendations = []

            if rec_type == "formula":
                # Generate formula recommendations
                domain = query_intent.get("domain", "general")
                formulas = self._get_domain_formulas(domain)

                for formula in formulas[:3]:  # Limit to 3 formulas
                    rec = ContextualRecommendation(
                        recommendation_id=f"formula_{formula.lower()}",
                        recommendation_type="formula",
                        title=f"{formula} Formula",
                        description=f"Use {formula} for {domain} analysis",
                        confidence=0.8,
                        personalization_score=0.7,
                        reasoning=f"Recommended for {domain} analysis",
                        alternatives=[],
                        metadata={"formula": formula, "domain": domain},
                    )
                    recommendations.append(rec)

            return recommendations
        except Exception as e:
            logger.error(f"Error generating type recommendations: {e}")
            return []

    def _generate_alternative_recommendations(
        self, recommendations: List[ContextualRecommendation], explanation_depth: str
    ) -> List[str]:
        """Generate alternative recommendations"""
        try:
            alternatives = []

            for rec in recommendations[:2]:  # Limit to top 2 recommendations
                if rec.recommendation_type == "formula":
                    alternatives.append(
                        f"Alternative: Consider {rec.title} with different parameters"
                    )

            return alternatives
        except Exception as e:
            logger.error(f"Error generating alternative recommendations: {e}")
            return []

    def _generate_fallback_recommendations(
        self,
        recommendation_count: int,
        recommendation_types: Optional[List[str]],
        personalization_level: str,
    ) -> Dict[str, Any]:
        """Generate fallback recommendations when context analysis is empty"""
        try:
            if recommendation_types is None:
                recommendation_types = ["formula"]

            # Generate basic recommendations
            recommendations = []

            for rec_type in recommendation_types:
                if rec_type == "formula":
                    # Basic formula recommendations
                    basic_formulas = [
                        "PER",
                        "TS%",
                        "Usage Rate",
                        "eFG%",
                        "Defensive Rating",
                    ]

                    for formula in basic_formulas[:recommendation_count]:
                        rec = ContextualRecommendation(
                            recommendation_id=f"fallback_{formula.lower()}",
                            recommendation_type="formula",
                            title=f"{formula} Formula",
                            description=f"Basic recommendation for {formula} analysis",
                            confidence=0.6,  # Lower confidence for fallback
                            personalization_score=0.3,  # Lower personalization
                            reasoning="Fallback recommendation due to limited context",
                            alternatives=[],
                            metadata={"fallback": True, "formula": formula},
                        )
                        recommendations.append(rec)

            return {
                "status": "success",
                "recommendations": [asdict(rec) for rec in recommendations],
                "alternatives": [],
                "metadata": {
                    "generation_timestamp": datetime.now().isoformat(),
                    "recommendation_count": len(recommendations),
                    "personalization_level": personalization_level,
                    "fallback_mode": True,
                    "note": "Generated fallback recommendations due to empty context analysis",
                },
            }

        except Exception as e:
            logger.error(f"Error generating fallback recommendations: {e}")
            return {
                "status": "error",
                "error": str(e),
                "recommendations": [],
                "metadata": {},
            }

    def _extract_analysis_data(
        self, analysis_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract analysis data from context"""
        try:
            return {
                "formulas_used": analysis_context.get("formulas_used", []),
                "analysis_results": analysis_context.get("results", {}),
                "data_points": analysis_context.get("data_points", []),
                "metrics": analysis_context.get("metrics", {}),
            }
        except Exception as e:
            logger.error(f"Error extracting analysis data: {e}")
            return {}

    def _generate_type_insights(
        self,
        insight_type: str,
        analysis_data: Dict[str, Any],
        insight_depth: str,
        confidence_threshold: float,
    ) -> List[ContextInsight]:
        """Generate insights for specific type"""
        try:
            insights = []

            if insight_type == "pattern":
                # Generate pattern insights
                formulas_used = analysis_data.get("formulas_used", [])
                if formulas_used:
                    insight = ContextInsight(
                        insight_id="formula_pattern",
                        insight_type="pattern",
                        title="Formula Usage Pattern",
                        description=f"User frequently uses {', '.join(formulas_used[:3])} formulas",
                        confidence=0.8,
                        relevance_score=0.7,
                        actionable=True,
                        category="usage",
                        metadata={"formulas": formulas_used},
                    )
                    insights.append(insight)

            elif insight_type == "trend":
                # Generate trend insights
                metrics = analysis_data.get("metrics", {})
                if metrics:
                    insight = ContextInsight(
                        insight_id="metric_trend",
                        insight_type="trend",
                        title="Metric Trend Analysis",
                        description="Analysis shows interesting trends in the data",
                        confidence=0.7,
                        relevance_score=0.8,
                        actionable=True,
                        category="trend",
                        metadata={"metrics": list(metrics.keys())},
                    )
                    insights.append(insight)

            return insights
        except Exception as e:
            logger.error(f"Error generating type insights: {e}")
            return []

    def _generate_visualization_suggestions(
        self, insights: List[ContextInsight]
    ) -> List[str]:
        """Generate visualization suggestions for insights"""
        try:
            suggestions = []

            for insight in insights[:3]:  # Limit to top 3 insights
                if insight.insight_type == "pattern":
                    suggestions.append(f"Bar chart showing {insight.title}")
                elif insight.insight_type == "trend":
                    suggestions.append(f"Line chart displaying {insight.title}")

            return suggestions
        except Exception as e:
            logger.error(f"Error generating visualization suggestions: {e}")
            return []

    def _generate_actionable_recommendations(
        self, insights: List[ContextInsight], analysis_data: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations from insights"""
        try:
            recommendations = []

            for insight in insights[:3]:  # Limit to top 3 insights
                if insight.actionable:
                    recommendations.append(f"Action: {insight.description}")

            return recommendations
        except Exception as e:
            logger.error(f"Error generating actionable recommendations: {e}")
            return []


# =============================================================================
# Standalone Functions
# =============================================================================


def analyze_user_context_intelligently(
    user_query: str,
    session_history: Optional[List[Dict[str, Any]]] = None,
    available_data: Optional[Dict[str, Any]] = None,
    analysis_goals: Optional[List[str]] = None,
    expertise_level: str = "intermediate",
    preferred_formulas: Optional[List[str]] = None,
    context_depth: str = "moderate",
) -> Dict[str, Any]:
    """
    Standalone function for intelligent user context analysis.

    Args:
        user_query: User's query or request
        session_history: Previous session interactions
        available_data: Available data sources and variables
        analysis_goals: User's analysis goals
        expertise_level: User's expertise level
        preferred_formulas: User's preferred formulas
        context_depth: Depth of analysis to perform

    Returns:
        Dictionary with context analysis results
    """
    engine = SmartContextAnalysisEngine()
    return engine.analyze_user_context_intelligently(
        user_query=user_query,
        session_history=session_history,
        available_data=available_data,
        analysis_goals=analysis_goals,
        expertise_level=expertise_level,
        preferred_formulas=preferred_formulas,
        context_depth=context_depth,
    )


def analyze_user_behavior_patterns(
    user_id: str,
    time_period: str = "session",
    behavior_types: List[str] = None,
    include_patterns: bool = True,
    include_predictions: bool = True,
    privacy_level: str = "basic",
) -> Dict[str, Any]:
    """
    Standalone function for user behavior pattern analysis.

    Args:
        user_id: Unique user identifier
        time_period: Time period for analysis
        behavior_types: Types of behavior to analyze
        include_patterns: Whether to identify patterns
        include_predictions: Whether to predict future behavior
        privacy_level: Level of detail in analysis

    Returns:
        Dictionary with behavior analysis results
    """
    engine = SmartContextAnalysisEngine()
    return engine.analyze_user_behavior_patterns(
        user_id=user_id,
        time_period=time_period,
        behavior_types=behavior_types,
        include_patterns=include_patterns,
        include_predictions=include_predictions,
        privacy_level=privacy_level,
    )


def generate_contextual_recommendations(
    context_analysis: Dict[str, Any],
    recommendation_count: int = 5,
    recommendation_types: List[str] = None,
    personalization_level: str = "basic",
    include_alternatives: bool = True,
    explanation_depth: str = "detailed",
    confidence_threshold: float = 0.6,
) -> Dict[str, Any]:
    """
    Standalone function for contextual recommendation generation.

    Args:
        context_analysis: Results from context analysis
        recommendation_count: Number of recommendations to generate
        recommendation_types: Types of recommendations to include
        personalization_level: Level of personalization
        include_alternatives: Whether to include alternatives
        explanation_depth: Depth of explanations
        confidence_threshold: Minimum confidence threshold

    Returns:
        Dictionary with contextual recommendations
    """
    engine = SmartContextAnalysisEngine()
    return engine.generate_contextual_recommendations(
        context_analysis=context_analysis,
        recommendation_count=recommendation_count,
        recommendation_types=recommendation_types,
        personalization_level=personalization_level,
        include_alternatives=include_alternatives,
        explanation_depth=explanation_depth,
        confidence_threshold=confidence_threshold,
    )


def manage_session_context(
    session_id: str,
    context_data: Dict[str, Any],
    context_type: str = "analysis_state",
    operation: str = "store",
    expiration_time: Optional[int] = None,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """
    Standalone function for session context management.

    Args:
        session_id: Unique session identifier
        context_data: Context data to manage
        context_type: Type of context data
        operation: Operation to perform
        expiration_time: Expiration time in seconds
        include_metadata: Whether to include metadata

    Returns:
        Dictionary with operation results
    """
    engine = SmartContextAnalysisEngine()
    return engine.manage_session_context(
        session_id=session_id,
        context_data=context_data,
        context_type=context_type,
        operation=operation,
        expiration_time=expiration_time,
        include_metadata=include_metadata,
    )


def generate_intelligent_insights(
    analysis_context: Dict[str, Any],
    insight_types: List[str] = None,
    insight_depth: str = "moderate",
    include_visualizations: bool = True,
    include_actionable_recommendations: bool = True,
    confidence_threshold: float = 0.7,
    max_insights: int = 10,
) -> Dict[str, Any]:
    """
    Standalone function for intelligent insight generation.

    Args:
        analysis_context: Context from analysis results
        insight_types: Types of insights to generate
        insight_depth: Depth of insight analysis
        include_visualizations: Whether to include visualization suggestions
        include_actionable_recommendations: Whether to include actionable recommendations
        confidence_threshold: Minimum confidence for insights
        max_insights: Maximum number of insights to generate

    Returns:
        Dictionary with intelligent insights
    """
    engine = SmartContextAnalysisEngine()
    return engine.generate_intelligent_insights(
        analysis_context=analysis_context,
        insight_types=insight_types,
        insight_depth=insight_depth,
        include_visualizations=include_visualizations,
        include_actionable_recommendations=include_actionable_recommendations,
        confidence_threshold=confidence_threshold,
        max_insights=max_insights,
    )
