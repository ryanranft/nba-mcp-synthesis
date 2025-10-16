#!/usr/bin/env python3
"""
Phase 8.2: Formula Usage Analytics

This module provides comprehensive formula usage analytics capabilities including:
- Real-time usage tracking and monitoring
- Advanced pattern recognition and analysis
- User behavior analytics and segmentation
- Performance metrics and optimization insights
- Automated reporting and alerting
- Interactive dashboards and visualizations
"""

import logging
import uuid
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64
import warnings

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes and Enums
# =============================================================================

class UsageEventType(str, Enum):
    """Types of usage events"""
    FORMULA_CALCULATION = "formula_calculation"
    FORMULA_COMPARISON = "formula_comparison"
    FORMULA_OPTIMIZATION = "formula_optimization"
    INSIGHT_GENERATION = "insight_generation"
    REPORT_GENERATION = "report_generation"
    DASHBOARD_VIEW = "dashboard_view"
    EXPORT_ACTION = "export_action"
    ERROR_EVENT = "error_event"


class UserSegment(str, Enum):
    """User segmentation categories"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    POWER_USER = "power_user"
    CASUAL_USER = "casual_user"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UsageEvent:
    """Represents a single usage event"""
    event_id: str
    user_id: str
    event_type: str
    formula_id: Optional[str]
    timestamp: datetime
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UsagePattern:
    """Represents a detected usage pattern"""
    pattern_id: str
    pattern_type: str
    frequency: int
    confidence: float
    description: str
    formulas_involved: List[str]
    user_segments: List[str]
    time_range: Tuple[datetime, datetime]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UsageInsight:
    """Represents a usage insight"""
    insight_id: str
    insight_type: str
    title: str
    description: str
    confidence: float
    impact_level: str
    recommendations: List[str]
    supporting_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UsageAlert:
    """Represents a usage alert"""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    conditions_met: List[str]
    timestamp: datetime
    resolved: bool = False
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# Core Formula Usage Analytics Engine
# =============================================================================

class FormulaUsageAnalyticsEngine:
    """Main engine for formula usage analytics"""

    def __init__(self):
        """Initialize the usage analytics engine"""
        self.usage_events: List[UsageEvent] = []
        self.usage_patterns: List[UsagePattern] = []
        self.usage_insights: List[UsageInsight] = []
        self.active_alerts: List[UsageAlert] = []
        self.user_segments: Dict[str, UserSegment] = {}
        self.performance_metrics: Dict[str, Any] = {}

        # Initialize analytics configurations
        self._initialize_analytics_configs()

        logger.info("Formula Usage Analytics Engine initialized")

    def _generate_event_id(self) -> str:
        """Generate a unique event ID"""
        return f"event_{uuid.uuid4().hex[:8]}"

    def _generate_pattern_id(self) -> str:
        """Generate a unique pattern ID"""
        return f"pattern_{uuid.uuid4().hex[:8]}"

    def _generate_insight_id(self) -> str:
        """Generate a unique insight ID"""
        return f"insight_{uuid.uuid4().hex[:8]}"

    def _generate_alert_id(self) -> str:
        """Generate a unique alert ID"""
        return f"alert_{uuid.uuid4().hex[:8]}"

    def _initialize_analytics_configs(self):
        """Initialize analytics configurations"""
        self.analytics_configs = {
            "tracking_intervals": {
                "real_time": 1,  # seconds
                "hourly": 3600,  # seconds
                "daily": 86400,  # seconds
                "weekly": 604800  # seconds
            },
            "performance_thresholds": {
                "fast_execution": 0.1,  # seconds
                "slow_execution": 1.0,  # seconds
                "high_error_rate": 0.05,  # 5%
                "low_success_rate": 0.9  # 90%
            },
            "pattern_detection": {
                "min_frequency": 5,
                "confidence_threshold": 0.7,
                "time_window_hours": 24
            }
        }

    def track_usage_event(
        self,
        user_id: str,
        event_type: str,
        formula_id: Optional[str] = None,
        duration: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track a usage event.

        Args:
            user_id: ID of the user performing the action
            event_type: Type of event
            formula_id: ID of the formula involved
            duration: Duration of the operation
            success: Whether the operation was successful
            error_message: Error message if operation failed
            metadata: Additional metadata

        Returns:
            Event ID
        """
        try:
            event = UsageEvent(
                event_id=self._generate_event_id(),
                user_id=user_id,
                event_type=event_type,
                formula_id=formula_id,
                timestamp=datetime.now(),
                duration=duration,
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )

            self.usage_events.append(event)

            # Update user segment if needed
            self._update_user_segment(user_id)

            # Check for patterns (simplified for now)
            # self._detect_usage_patterns()

            # Check for alerts
            self._check_alert_conditions()

            logger.info(f"Usage event tracked: {event_type} by user {user_id}")
            return event.event_id

        except Exception as e:
            logger.error(f"Failed to track usage event: {e}")
            return ""

    def analyze_usage_patterns(
        self,
        tracking_period: str = "week",
        formula_categories: Optional[List[str]] = None,
        user_segments: Optional[List[str]] = None,
        include_performance_metrics: bool = True,
        include_user_behavior: bool = True,
        real_time_tracking: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze usage patterns comprehensively.

        Args:
            tracking_period: Time period for analysis
            formula_categories: Specific categories to analyze
            user_segments: User segments to include
            include_performance_metrics: Whether to include performance analysis
            include_user_behavior: Whether to include user behavior analysis
            real_time_tracking: Whether to enable real-time tracking

        Returns:
            Dictionary with comprehensive usage analysis
        """
        try:
            logger.info(f"Analyzing usage patterns for {tracking_period}")

            # Filter events by time period
            filtered_events = self._filter_events_by_period(tracking_period)

            # Analyze different aspects
            analysis_results = {
                "usage_statistics": self._analyze_usage_statistics(filtered_events),
                "performance_metrics": self._analyze_performance_metrics(filtered_events) if include_performance_metrics else {},
                "user_behavior": self._analyze_user_behavior(filtered_events) if include_user_behavior else {},
                "formula_popularity": self._analyze_formula_popularity(filtered_events),
                "trend_analysis": self._analyze_usage_trends(filtered_events),
                "pattern_detection": self._detect_advanced_patterns(filtered_events) if filtered_events else []
            }

            # Generate insights
            insights = self._generate_usage_insights(analysis_results)

            result = {
                "status": "success",
                "tracking_period": tracking_period,
                "total_events": len(filtered_events),
                "analysis_results": analysis_results,
                "insights": [asdict(insight) for insight in insights],
                "patterns_detected": len(self.usage_patterns),
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "real_time_tracking": real_time_tracking
                }
            }

            logger.info(f"Usage pattern analysis completed: {len(insights)} insights generated")
            return result

        except Exception as e:
            logger.error(f"Usage pattern analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "analysis_results": {}
            }

    def generate_usage_insights(
        self,
        insight_categories: List[str] = None,
        analysis_depth: str = "deep",
        include_predictions: bool = True,
        include_comparisons: bool = True,
        confidence_threshold: float = 0.8,
        max_insights: int = 15
    ) -> Dict[str, Any]:
        """
        Generate intelligent usage insights.

        Args:
            insight_categories: Categories of insights to generate
            analysis_depth: Depth of analysis
            include_predictions: Whether to include predictions
            include_comparisons: Whether to include comparisons
            confidence_threshold: Minimum confidence threshold
            max_insights: Maximum number of insights

        Returns:
            Dictionary with generated insights
        """
        try:
            if insight_categories is None:
                insight_categories = ["frequency", "performance", "trends"]

            logger.info(f"Generating {max_insights} usage insights")

            insights = []

            # Generate insights for each category
            for category in insight_categories:
                category_insights = self._generate_category_insights(
                    category, analysis_depth, include_predictions, include_comparisons
                )
                insights.extend(category_insights)

            # Filter by confidence threshold
            filtered_insights = [
                insight for insight in insights
                if insight.confidence >= confidence_threshold
            ]

            # Sort by confidence and impact
            filtered_insights.sort(
                key=lambda x: (x.confidence, self._get_impact_score(x)),
                reverse=True
            )

            # Limit to max_insights
            final_insights = filtered_insights[:max_insights]

            result = {
                "status": "success",
                "insights_generated": len(final_insights),
                "insights": [asdict(insight) for insight in final_insights],
                "metadata": {
                    "generation_timestamp": datetime.now().isoformat(),
                    "confidence_threshold": confidence_threshold,
                    "analysis_depth": analysis_depth
                }
            }

            logger.info(f"Usage insights generated: {len(final_insights)} insights")
            return result

        except Exception as e:
            logger.error(f"Usage insight generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "insights": []
            }

    def optimize_usage_based_performance(
        self,
        optimization_focus: List[str] = None,
        target_metrics: Optional[List[str]] = None,
        optimization_method: str = "guided",
        include_ab_testing: bool = False,
        optimization_scope: str = "formula"
    ) -> Dict[str, Any]:
        """
        Optimize system performance based on usage patterns.

        Args:
            optimization_focus: Focus areas for optimization
            target_metrics: Specific metrics to optimize
            optimization_method: Method for optimization
            include_ab_testing: Whether to include A/B testing
            optimization_scope: Scope of optimization

        Returns:
            Dictionary with optimization recommendations
        """
        try:
            if optimization_focus is None:
                optimization_focus = ["performance", "usability"]

            logger.info(f"Optimizing usage-based performance for {optimization_scope}")

            # Analyze current performance
            performance_analysis = self._analyze_current_performance()

            # Generate optimization recommendations
            recommendations = []

            for focus_area in optimization_focus:
                focus_recommendations = self._generate_optimization_recommendations(
                    focus_area, performance_analysis, optimization_method
                )
                recommendations.extend(focus_recommendations)

            # Generate A/B testing recommendations if requested
            ab_testing_recommendations = []
            if include_ab_testing:
                ab_testing_recommendations = self._generate_ab_testing_recommendations(
                    recommendations
                )

            result = {
                "status": "success",
                "optimization_scope": optimization_scope,
                "performance_analysis": performance_analysis,
                "recommendations": recommendations,
                "ab_testing_recommendations": ab_testing_recommendations,
                "metadata": {
                    "optimization_timestamp": datetime.now().isoformat(),
                    "optimization_method": optimization_method
                }
            }

            logger.info(f"Usage-based optimization completed: {len(recommendations)} recommendations")
            return result

        except Exception as e:
            logger.error(f"Usage-based optimization failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "recommendations": []
            }

    def generate_usage_report(
        self,
        report_type: str = "summary",
        report_period: str = "weekly",
        include_visualizations: bool = True,
        include_recommendations: bool = True,
        include_benchmarks: bool = True,
        export_format: str = "html"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive usage reports.

        Args:
            report_type: Type of report to generate
            report_period: Period covered by the report
            include_visualizations: Whether to include visualizations
            include_recommendations: Whether to include recommendations
            include_benchmarks: Whether to include benchmarks
            export_format: Format for exporting the report

        Returns:
            Dictionary with report data and content
        """
        try:
            logger.info(f"Generating {report_type} usage report for {report_period}")

            # Gather report data
            report_data = self._gather_report_data(report_period)

            # Generate report content
            report_content = self._generate_report_content(
                report_data, report_type, include_visualizations,
                include_recommendations, include_benchmarks
            )

            # Generate visualizations if requested
            visualizations = {}
            if include_visualizations:
                visualizations = self._generate_report_visualizations(report_data)

            result = {
                "status": "success",
                "report_type": report_type,
                "report_period": report_period,
                "report_content": report_content,
                "visualizations": visualizations,
                "export_format": export_format,
                "metadata": {
                    "generation_timestamp": datetime.now().isoformat(),
                    "data_points": len(self.usage_events)
                }
            }

            logger.info(f"Usage report generated: {report_type} report")
            return result

        except Exception as e:
            logger.error(f"Usage report generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "report_content": {}
            }

    def setup_usage_alerts(
        self,
        alert_conditions: List[Dict[str, Any]],
        alert_types: List[str] = None,
        alert_frequency: str = "immediate",
        alert_thresholds: Optional[Dict[str, float]] = None,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Set up usage-based alerts.

        Args:
            alert_conditions: Conditions that trigger alerts
            alert_types: Types of alerts to send
            alert_frequency: Frequency of alert checks
            alert_thresholds: Threshold values for conditions
            include_context: Whether to include contextual information

        Returns:
            Dictionary with alert setup results
        """
        try:
            if alert_types is None:
                alert_types = ["email"]

            logger.info(f"Setting up {len(alert_conditions)} usage alerts")

            # Validate alert conditions
            validated_conditions = self._validate_alert_conditions(alert_conditions)

            # Set up alert monitoring
            alert_setup = {
                "alert_id": self._generate_alert_id(),
                "conditions": validated_conditions,
                "alert_types": alert_types,
                "frequency": alert_frequency,
                "thresholds": alert_thresholds or {},
                "include_context": include_context,
                "created_at": datetime.now().isoformat(),
                "active": True
            }

            # Store alert configuration
            self.active_alerts.append(UsageAlert(
                alert_id=alert_setup["alert_id"],
                alert_type="usage_monitoring",
                severity="medium",
                title="Usage Alert Setup",
                message=f"Alert monitoring setup with {len(validated_conditions)} conditions",
                conditions_met=[],
                timestamp=datetime.now()
            ))

            result = {
                "status": "success",
                "alert_setup": alert_setup,
                "conditions_configured": len(validated_conditions),
                "alert_types": alert_types,
                "monitoring_active": True,
                "metadata": {
                    "setup_timestamp": datetime.now().isoformat()
                }
            }

            logger.info(f"Usage alerts setup completed: {len(validated_conditions)} conditions")
            return result

        except Exception as e:
            logger.error(f"Usage alert setup failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "alert_setup": {}
            }

    def create_usage_dashboard(
        self,
        dashboard_type: str = "overview",
        dashboard_sections: List[str] = None,
        refresh_interval: int = 300,
        include_filters: bool = True,
        include_exports: bool = True,
        customization_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create interactive usage dashboards.

        Args:
            dashboard_type: Type of dashboard to create
            dashboard_sections: Sections to include
            refresh_interval: Refresh interval in seconds
            include_filters: Whether to include filters
            include_exports: Whether to include exports
            customization_options: Additional customization options

        Returns:
            Dictionary with dashboard configuration and data
        """
        try:
            if dashboard_sections is None:
                dashboard_sections = ["usage_stats", "performance", "trends"]

            logger.info(f"Creating {dashboard_type} usage dashboard")

            # Generate dashboard data
            dashboard_data = self._generate_dashboard_data(dashboard_sections)

            # Create dashboard configuration
            dashboard_config = {
                "dashboard_id": self._generate_event_id(),
                "dashboard_type": dashboard_type,
                "sections": dashboard_sections,
                "refresh_interval": refresh_interval,
                "include_filters": include_filters,
                "include_exports": include_exports,
                "customization_options": customization_options or {},
                "created_at": datetime.now().isoformat()
            }

            # Generate dashboard visualizations
            visualizations = self._generate_dashboard_visualizations(
                dashboard_data, dashboard_sections
            )

            result = {
                "status": "success",
                "dashboard_config": dashboard_config,
                "dashboard_data": dashboard_data,
                "visualizations": visualizations,
                "sections_count": len(dashboard_sections),
                "metadata": {
                    "creation_timestamp": datetime.now().isoformat(),
                    "refresh_interval": refresh_interval
                }
            }

            logger.info(f"Usage dashboard created: {dashboard_type} with {len(dashboard_sections)} sections")
            return result

        except Exception as e:
            logger.error(f"Usage dashboard creation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "dashboard_config": {}
            }

    # Helper methods
    def _filter_events_by_period(self, period: str) -> List[UsageEvent]:
        """Filter events by time period"""
        now = datetime.now()

        if period == "hour":
            cutoff = now - timedelta(hours=1)
        elif period == "day":
            cutoff = now - timedelta(days=1)
        elif period == "week":
            cutoff = now - timedelta(weeks=1)
        elif period == "month":
            cutoff = now - timedelta(days=30)
        elif period == "year":
            cutoff = now - timedelta(days=365)
        else:  # all
            cutoff = datetime.min

        return [event for event in self.usage_events if event.timestamp >= cutoff]

    def _analyze_usage_statistics(self, events: List[UsageEvent]) -> Dict[str, Any]:
        """Analyze basic usage statistics"""
        if not events:
            return {}

        total_events = len(events)
        successful_events = len([e for e in events if e.success])
        unique_users = len(set(e.user_id for e in events))
        unique_formulas = len(set(e.formula_id for e in events if e.formula_id))

        return {
            "total_events": total_events,
            "successful_events": successful_events,
            "success_rate": successful_events / total_events if total_events > 0 else 0,
            "unique_users": unique_users,
            "unique_formulas": unique_formulas,
            "avg_events_per_user": total_events / unique_users if unique_users > 0 else 0
        }

    def _analyze_performance_metrics(self, events: List[UsageEvent]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        if not events:
            return {}

        durations = [e.duration for e in events if e.duration is not None]

        if not durations:
            return {"no_duration_data": True}

        return {
            "avg_duration": np.mean(durations),
            "median_duration": np.median(durations),
            "min_duration": np.min(durations),
            "max_duration": np.max(durations),
            "fast_executions": len([d for d in durations if d < 0.1]),
            "slow_executions": len([d for d in durations if d > 1.0])
        }

    def _analyze_user_behavior(self, events: List[UsageEvent]) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        if not events:
            return {}

        user_activity = {}
        for event in events:
            if event.user_id not in user_activity:
                user_activity[event.user_id] = []
            user_activity[event.user_id].append(event)

        return {
            "most_active_users": sorted(
                user_activity.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5],
            "user_segments": self._analyze_user_segments(user_activity),
            "session_patterns": self._analyze_session_patterns(user_activity)
        }

    def _analyze_formula_popularity(self, events: List[UsageEvent]) -> Dict[str, Any]:
        """Analyze formula popularity"""
        if not events:
            return {}

        formula_usage = {}
        for event in events:
            if event.formula_id:
                formula_usage[event.formula_id] = formula_usage.get(event.formula_id, 0) + 1

        return {
            "most_popular_formulas": sorted(
                formula_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "formula_diversity": len(formula_usage),
            "usage_distribution": formula_usage
        }

    def _analyze_usage_trends(self, events: List[UsageEvent]) -> Dict[str, Any]:
        """Analyze usage trends over time"""
        if not events:
            return {}

        # Group events by hour
        hourly_usage = {}
        for event in events:
            hour_key = event.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_usage[hour_key] = hourly_usage.get(hour_key, 0) + 1

        return {
            "hourly_distribution": hourly_usage,
            "peak_usage_hour": max(hourly_usage.items(), key=lambda x: x[1])[0] if hourly_usage else None,
            "trend_direction": self._calculate_trend_direction(list(hourly_usage.values()))
        }

    def _detect_advanced_patterns(self, events: List[UsageEvent]) -> List[UsagePattern]:
        """Detect advanced usage patterns"""
        patterns = []

        # Pattern 1: Sequential formula usage
        sequential_patterns = self._detect_sequential_patterns(events)
        patterns.extend(sequential_patterns)

        # Pattern 2: Time-based patterns
        time_patterns = self._detect_time_patterns(events)
        patterns.extend(time_patterns)

        # Pattern 3: User behavior patterns
        behavior_patterns = self._detect_behavior_patterns(events)
        patterns.extend(behavior_patterns)

        return patterns

    def _detect_sequential_patterns(self, events: List[UsageEvent]) -> List[UsagePattern]:
        """Detect sequential formula usage patterns"""
        patterns = []

        # Group events by user
        user_events = {}
        for event in events:
            if event.user_id not in user_events:
                user_events[event.user_id] = []
            user_events[event.user_id].append(event)

        # Look for sequential patterns
        for user_id, user_event_list in user_events.items():
            if len(user_event_list) < 3:
                continue

            # Sort by timestamp
            user_event_list.sort(key=lambda x: x.timestamp)

            # Look for formula sequences
            for i in range(len(user_event_list) - 2):
                if (user_event_list[i].formula_id and
                    user_event_list[i+1].formula_id and
                    user_event_list[i+2].formula_id):

                    sequence = [
                        user_event_list[i].formula_id,
                        user_event_list[i+1].formula_id,
                        user_event_list[i+2].formula_id
                    ]

                    pattern = UsagePattern(
                        pattern_id=self._generate_pattern_id(),
                        pattern_type="sequential_usage",
                        frequency=1,
                        confidence=0.8,
                        description=f"Sequential usage pattern: {' -> '.join(sequence)}",
                        formulas_involved=sequence,
                        user_segments=[self.user_segments.get(user_id, UserSegment.INTERMEDIATE).value],
                        time_range=(user_event_list[i].timestamp, user_event_list[i+2].timestamp)
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_time_patterns(self, events: List[UsageEvent]) -> List[UsagePattern]:
        """Detect time-based usage patterns"""
        patterns = []

        # Group events by hour of day
        hourly_usage = {}
        for event in events:
            hour = event.timestamp.hour
            hourly_usage[hour] = hourly_usage.get(hour, 0) + 1

        # Find peak usage hours
        if hourly_usage:
            peak_hour = max(hourly_usage.items(), key=lambda x: x[1])
            if peak_hour[1] > 5:  # Minimum threshold
                pattern = UsagePattern(
                    pattern_id=self._generate_pattern_id(),
                    pattern_type="time_based",
                    frequency=peak_hour[1],
                    confidence=0.7,
                    description=f"Peak usage hour: {peak_hour[0]}:00",
                    formulas_involved=[],
                    user_segments=[],
                    time_range=(datetime.now() - timedelta(days=1), datetime.now())
                )
                patterns.append(pattern)

        return patterns

    def _detect_behavior_patterns(self, events: List[UsageEvent]) -> List[UsagePattern]:
        """Detect user behavior patterns"""
        patterns = []

        # Group events by user
        user_events = {}
        for event in events:
            if event.user_id not in user_events:
                user_events[event.user_id] = []
            user_events[event.user_id].append(event)

        # Analyze user behavior patterns
        for user_id, user_event_list in user_events.items():
            if len(user_event_list) < 5:
                continue

            # Calculate user activity metrics
            total_events = len(user_event_list)
            successful_events = len([e for e in user_event_list if e.success])
            avg_duration = np.mean([e.duration for e in user_event_list if e.duration])

            # Determine behavior pattern
            if total_events > 20 and successful_events / total_events > 0.95:
                pattern = UsagePattern(
                    pattern_id=self._generate_pattern_id(),
                    pattern_type="power_user",
                    frequency=total_events,
                    confidence=0.9,
                    description=f"Power user behavior: {total_events} events, {successful_events/total_events:.1%} success rate",
                    formulas_involved=[],
                    user_segments=[self.user_segments.get(user_id, UserSegment.ADVANCED).value],
                    time_range=(min(e.timestamp for e in user_event_list), max(e.timestamp for e in user_event_list))
                )
                patterns.append(pattern)

        return patterns

    def _generate_usage_insights(self, analysis_results: Dict[str, Any]) -> List[UsageInsight]:
        """Generate usage insights from analysis results"""
        insights = []

        # Performance insights
        if "performance_metrics" in analysis_results:
            perf_metrics = analysis_results["performance_metrics"]
            if "avg_duration" in perf_metrics:
                avg_duration = perf_metrics["avg_duration"]
                if avg_duration > 1.0:
                    insight = UsageInsight(
                        insight_id=self._generate_insight_id(),
                        insight_type="performance",
                        title="Slow Formula Execution",
                        description=f"Average execution time is {avg_duration:.2f}s, which is above optimal threshold",
                        confidence=0.8,
                        impact_level="medium",
                        recommendations=["Consider formula optimization", "Implement caching", "Review formula complexity"]
                    )
                    insights.append(insight)

        # Usage pattern insights
        if "formula_popularity" in analysis_results:
            popularity = analysis_results["formula_popularity"]
            if "most_popular_formulas" in popularity:
                most_popular = popularity["most_popular_formulas"]
                if most_popular:
                    top_formula = most_popular[0]
                    insight = UsageInsight(
                        insight_id=self._generate_insight_id(),
                        insight_type="usage",
                        title="Formula Popularity",
                        description=f"'{top_formula[0]}' is the most popular formula with {top_formula[1]} uses",
                        confidence=0.9,
                        impact_level="low",
                        recommendations=["Consider promoting similar formulas", "Create related tutorials"]
                    )
                    insights.append(insight)

        return insights

    def _generate_category_insights(
        self,
        category: str,
        depth: str,
        include_predictions: bool,
        include_comparisons: bool
    ) -> List[UsageInsight]:
        """Generate insights for a specific category"""
        insights = []

        if category == "frequency":
            insight = UsageInsight(
                insight_id=self._generate_insight_id(),
                insight_type="frequency",
                title="Usage Frequency Analysis",
                description="Analysis of how frequently formulas are used",
                confidence=0.8,
                impact_level="medium",
                recommendations=["Optimize popular formulas", "Promote underused formulas"]
            )
            insights.append(insight)

        elif category == "performance":
            insight = UsageInsight(
                insight_id=self._generate_insight_id(),
                insight_type="performance",
                title="Performance Optimization",
                description="Recommendations for improving formula performance",
                confidence=0.7,
                impact_level="high",
                recommendations=["Implement caching", "Optimize slow formulas", "Add performance monitoring"]
            )
            insights.append(insight)

        elif category == "trends":
            insight = UsageInsight(
                insight_id=self._generate_insight_id(),
                insight_type="trends",
                title="Usage Trend Analysis",
                description="Analysis of usage trends over time",
                confidence=0.6,
                impact_level="low",
                recommendations=["Monitor trend changes", "Plan capacity accordingly"]
            )
            insights.append(insight)

        return insights

    def _get_impact_score(self, insight: UsageInsight) -> float:
        """Calculate impact score for an insight"""
        impact_scores = {"low": 0.3, "medium": 0.6, "high": 0.9}
        return impact_scores.get(insight.impact_level, 0.5)

    def _update_user_segment(self, user_id: str):
        """Update user segment based on activity"""
        user_events = [e for e in self.usage_events if e.user_id == user_id]

        if len(user_events) < 5:
            segment = UserSegment.BEGINNER
        elif len(user_events) < 20:
            segment = UserSegment.INTERMEDIATE
        elif len(user_events) < 50:
            segment = UserSegment.ADVANCED
        else:
            segment = UserSegment.EXPERT

        self.user_segments[user_id] = segment

    def _check_alert_conditions(self):
        """Check for alert conditions"""
        # Simple alert checking - in production this would be more sophisticated
        recent_events = self._filter_events_by_period("hour")

        if len(recent_events) > 100:  # High usage alert
            alert = UsageAlert(
                alert_id=self._generate_alert_id(),
                alert_type="high_usage",
                severity="medium",
                title="High Usage Alert",
                message=f"High usage detected: {len(recent_events)} events in the last hour",
                conditions_met=["high_usage"],
                timestamp=datetime.now()
            )
            self.active_alerts.append(alert)

    def _validate_alert_conditions(self, conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate alert conditions"""
        validated = []
        for condition in conditions:
            if isinstance(condition, dict) and "type" in condition:
                validated.append(condition)
        return validated

    def _analyze_current_performance(self) -> Dict[str, Any]:
        """Analyze current system performance"""
        recent_events = self._filter_events_by_period("day")

        if not recent_events:
            return {"no_data": True}

        durations = [e.duration for e in recent_events if e.duration is not None]
        success_rate = len([e for e in recent_events if e.success]) / len(recent_events)

        return {
            "avg_duration": np.mean(durations) if durations else 0,
            "success_rate": success_rate,
            "total_events": len(recent_events),
            "performance_score": self._calculate_performance_score(durations, success_rate)
        }

    def _calculate_performance_score(self, durations: List[float], success_rate: float) -> float:
        """Calculate overall performance score"""
        if not durations:
            return 0.5

        avg_duration = np.mean(durations)
        duration_score = max(0, 1 - avg_duration)  # Lower duration = higher score
        success_score = success_rate

        return (duration_score + success_score) / 2

    def _generate_optimization_recommendations(
        self,
        focus_area: str,
        performance_analysis: Dict[str, Any],
        method: str
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        if focus_area == "performance":
            if performance_analysis.get("avg_duration", 0) > 0.5:
                recommendations.append("Implement formula caching for frequently used calculations")
                recommendations.append("Optimize slow-performing formulas")

        elif focus_area == "usability":
            recommendations.append("Improve formula documentation and examples")
            recommendations.append("Add formula recommendations based on user behavior")

        elif focus_area == "efficiency":
            recommendations.append("Implement batch processing for multiple calculations")
            recommendations.append("Add formula pre-computation for common scenarios")

        return recommendations

    def _generate_ab_testing_recommendations(self, recommendations: List[str]) -> List[Dict[str, Any]]:
        """Generate A/B testing recommendations"""
        ab_tests = []

        for rec in recommendations[:3]:  # Limit to top 3 recommendations
            ab_test = {
                "test_name": f"AB_Test_{len(ab_tests) + 1}",
                "description": f"A/B test for: {rec}",
                "variants": ["control", "treatment"],
                "metrics": ["success_rate", "user_satisfaction", "performance"],
                "duration_weeks": 2
            }
            ab_tests.append(ab_test)

        return ab_tests

    def _gather_report_data(self, period: str) -> Dict[str, Any]:
        """Gather data for report generation"""
        events = self._filter_events_by_period(period)

        return {
            "usage_statistics": self._analyze_usage_statistics(events),
            "performance_metrics": self._analyze_performance_metrics(events),
            "user_behavior": self._analyze_user_behavior(events),
            "formula_popularity": self._analyze_formula_popularity(events),
            "trend_analysis": self._analyze_usage_trends(events)
        }

    def _generate_report_content(
        self,
        data: Dict[str, Any],
        report_type: str,
        include_visualizations: bool,
        include_recommendations: bool,
        include_benchmarks: bool
    ) -> Dict[str, Any]:
        """Generate report content"""
        content = {
            "executive_summary": self._generate_executive_summary(data),
            "detailed_analysis": data,
            "visualizations": {} if include_visualizations else None,
            "recommendations": self._generate_report_recommendations(data) if include_recommendations else None,
            "benchmarks": self._generate_benchmarks(data) if include_benchmarks else None
        }

        return content

    def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary"""
        stats = data.get("usage_statistics", {})
        total_events = stats.get("total_events", 0)
        success_rate = stats.get("success_rate", 0)

        return f"Usage Report Summary: {total_events} total events with {success_rate:.1%} success rate"

    def _generate_report_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate report recommendations"""
        recommendations = []

        perf_metrics = data.get("performance_metrics", {})
        if perf_metrics.get("avg_duration", 0) > 0.5:
            recommendations.append("Consider implementing formula caching")

        usage_stats = data.get("usage_statistics", {})
        if usage_stats.get("success_rate", 1) < 0.95:
            recommendations.append("Investigate and fix error causes")

        return recommendations

    def _generate_benchmarks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance benchmarks"""
        perf_metrics = data.get("performance_metrics", {})

        return {
            "performance_benchmarks": {
                "target_avg_duration": 0.1,
                "current_avg_duration": perf_metrics.get("avg_duration", 0),
                "target_success_rate": 0.99,
                "current_success_rate": data.get("usage_statistics", {}).get("success_rate", 0)
            }
        }

    def _generate_report_visualizations(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate report visualizations"""
        visualizations = {}

        # Generate usage trend chart
        trend_data = data.get("trend_analysis", {})
        if "hourly_distribution" in trend_data:
            fig, ax = plt.subplots(figsize=(10, 6))

            hourly_data = trend_data["hourly_distribution"]
            hours = list(hourly_data.keys())
            counts = list(hourly_data.values())

            ax.plot(hours, counts, marker='o')
            ax.set_title("Usage Trends Over Time")
            ax.set_xlabel("Time")
            ax.set_ylabel("Event Count")

            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()

            visualizations["usage_trends"] = f"data:image/png;base64,{image_base64}"

        return visualizations

    def _generate_dashboard_data(self, sections: List[str]) -> Dict[str, Any]:
        """Generate dashboard data"""
        dashboard_data = {}

        recent_events = self._filter_events_by_period("day")

        for section in sections:
            if section == "usage_stats":
                dashboard_data[section] = self._analyze_usage_statistics(recent_events)
            elif section == "performance":
                dashboard_data[section] = self._analyze_performance_metrics(recent_events)
            elif section == "trends":
                dashboard_data[section] = self._analyze_usage_trends(recent_events)
            elif section == "recommendations":
                dashboard_data[section] = self._generate_report_recommendations({
                    "usage_statistics": self._analyze_usage_statistics(recent_events),
                    "performance_metrics": self._analyze_performance_metrics(recent_events)
                })
            elif section == "alerts":
                dashboard_data[section] = [asdict(alert) for alert in self.active_alerts[-5:]]

        return dashboard_data

    def _generate_dashboard_visualizations(
        self,
        dashboard_data: Dict[str, Any],
        sections: List[str]
    ) -> Dict[str, str]:
        """Generate dashboard visualizations"""
        visualizations = {}

        # Generate charts for each section
        for section in sections:
            if section == "usage_stats" and "usage_stats" in dashboard_data:
                # Create usage stats pie chart
                fig, ax = plt.subplots(figsize=(8, 6))

                stats = dashboard_data["usage_stats"]
                labels = ["Successful", "Failed"]
                sizes = [stats.get("successful_events", 0),
                        stats.get("total_events", 0) - stats.get("successful_events", 0)]

                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title("Event Success Rate")

                # Convert to base64
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()

                visualizations[f"{section}_chart"] = f"data:image/png;base64,{image_base64}"

        return visualizations

    def _analyze_user_segments(self, user_activity: Dict[str, List[UsageEvent]]) -> Dict[str, int]:
        """Analyze user segments"""
        segments = {}
        for user_id, events in user_activity.items():
            segment = self.user_segments.get(user_id, UserSegment.INTERMEDIATE)
            segments[segment.value] = segments.get(segment.value, 0) + 1
        return segments

    def _analyze_session_patterns(self, user_activity: Dict[str, List[UsageEvent]]) -> Dict[str, Any]:
        """Analyze session patterns"""
        session_patterns = {
            "avg_session_length": 0,
            "avg_events_per_session": 0,
            "session_frequency": {}
        }

        for user_id, events in user_activity.items():
            if len(events) > 1:
                events.sort(key=lambda x: x.timestamp)
                session_length = (events[-1].timestamp - events[0].timestamp).total_seconds()
                session_patterns["avg_session_length"] += session_length
                session_patterns["avg_events_per_session"] += len(events)

        if user_activity:
            session_patterns["avg_session_length"] /= len(user_activity)
            session_patterns["avg_events_per_session"] /= len(user_activity)

        return session_patterns

    def _calculate_trend_direction(self, values: List[int]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "insufficient_data"

        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = np.mean(first_half) if first_half else 0
        second_avg = np.mean(second_half) if second_half else 0

        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"


# =============================================================================
# Standalone Functions
# =============================================================================

# Global engine instance for standalone functions
_global_usage_analytics_engine = FormulaUsageAnalyticsEngine()


def track_usage_event(
    user_id: str,
    event_type: str,
    formula_id: Optional[str] = None,
    duration: Optional[float] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Track a usage event (standalone function).

    Args:
        user_id: ID of the user performing the action
        event_type: Type of event
        formula_id: ID of the formula involved
        duration: Duration of the operation
        success: Whether the operation was successful
        error_message: Error message if operation failed
        metadata: Additional metadata

    Returns:
        Event ID
    """
    return _global_usage_analytics_engine.track_usage_event(
        user_id=user_id,
        event_type=event_type,
        formula_id=formula_id,
        duration=duration,
        success=success,
        error_message=error_message,
        metadata=metadata
    )


def analyze_usage_patterns(
    tracking_period: str = "week",
    formula_categories: Optional[List[str]] = None,
    user_segments: Optional[List[str]] = None,
    include_performance_metrics: bool = True,
    include_user_behavior: bool = True,
    real_time_tracking: bool = False
) -> Dict[str, Any]:
    """
    Analyze usage patterns comprehensively (standalone function).

    Args:
        tracking_period: Time period for analysis
        formula_categories: Specific categories to analyze
        user_segments: User segments to include
        include_performance_metrics: Whether to include performance analysis
        include_user_behavior: Whether to include user behavior analysis
        real_time_tracking: Whether to enable real-time tracking

    Returns:
        Dictionary with comprehensive usage analysis
    """
    return _global_usage_analytics_engine.analyze_usage_patterns(
        tracking_period=tracking_period,
        formula_categories=formula_categories,
        user_segments=user_segments,
        include_performance_metrics=include_performance_metrics,
        include_user_behavior=include_user_behavior,
        real_time_tracking=real_time_tracking
    )


def generate_usage_insights(
    insight_categories: List[str] = None,
    analysis_depth: str = "deep",
    include_predictions: bool = True,
    include_comparisons: bool = True,
    confidence_threshold: float = 0.8,
    max_insights: int = 15
) -> Dict[str, Any]:
    """
    Generate intelligent usage insights (standalone function).

    Args:
        insight_categories: Categories of insights to generate
        analysis_depth: Depth of analysis
        include_predictions: Whether to include predictions
        include_comparisons: Whether to include comparisons
        confidence_threshold: Minimum confidence threshold
        max_insights: Maximum number of insights

    Returns:
        Dictionary with generated insights
    """
    return _global_usage_analytics_engine.generate_usage_insights(
        insight_categories=insight_categories,
        analysis_depth=analysis_depth,
        include_predictions=include_predictions,
        include_comparisons=include_comparisons,
        confidence_threshold=confidence_threshold,
        max_insights=max_insights
    )


def optimize_usage_based_performance(
    optimization_focus: List[str] = None,
    target_metrics: Optional[List[str]] = None,
    optimization_method: str = "guided",
    include_ab_testing: bool = False,
    optimization_scope: str = "formula"
) -> Dict[str, Any]:
    """
    Optimize system performance based on usage patterns (standalone function).

    Args:
        optimization_focus: Focus areas for optimization
        target_metrics: Specific metrics to optimize
        optimization_method: Method for optimization
        include_ab_testing: Whether to include A/B testing
        optimization_scope: Scope of optimization

    Returns:
        Dictionary with optimization recommendations
    """
    return _global_usage_analytics_engine.optimize_usage_based_performance(
        optimization_focus=optimization_focus,
        target_metrics=target_metrics,
        optimization_method=optimization_method,
        include_ab_testing=include_ab_testing,
        optimization_scope=optimization_scope
    )


def generate_usage_report(
    report_type: str = "summary",
    report_period: str = "weekly",
    include_visualizations: bool = True,
    include_recommendations: bool = True,
    include_benchmarks: bool = True,
    export_format: str = "html"
) -> Dict[str, Any]:
    """
    Generate comprehensive usage reports (standalone function).

    Args:
        report_type: Type of report to generate
        report_period: Period covered by the report
        include_visualizations: Whether to include visualizations
        include_recommendations: Whether to include recommendations
        include_benchmarks: Whether to include benchmarks
        export_format: Format for exporting the report

    Returns:
        Dictionary with report data and content
    """
    return _global_usage_analytics_engine.generate_usage_report(
        report_type=report_type,
        report_period=report_period,
        include_visualizations=include_visualizations,
        include_recommendations=include_recommendations,
        include_benchmarks=include_benchmarks,
        export_format=export_format
    )


def setup_usage_alerts(
    alert_conditions: List[Dict[str, Any]],
    alert_types: List[str] = None,
    alert_frequency: str = "immediate",
    alert_thresholds: Optional[Dict[str, float]] = None,
    include_context: bool = True
) -> Dict[str, Any]:
    """
    Set up usage-based alerts (standalone function).

    Args:
        alert_conditions: Conditions that trigger alerts
        alert_types: Types of alerts to send
        alert_frequency: Frequency of alert checks
        alert_thresholds: Threshold values for conditions
        include_context: Whether to include contextual information

    Returns:
        Dictionary with alert setup results
    """
    return _global_usage_analytics_engine.setup_usage_alerts(
        alert_conditions=alert_conditions,
        alert_types=alert_types,
        alert_frequency=alert_frequency,
        alert_thresholds=alert_thresholds,
        include_context=include_context
    )


def create_usage_dashboard(
    dashboard_type: str = "overview",
    dashboard_sections: List[str] = None,
    refresh_interval: int = 300,
    include_filters: bool = True,
    include_exports: bool = True,
    customization_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create interactive usage dashboards (standalone function).

    Args:
        dashboard_type: Type of dashboard to create
        dashboard_sections: Sections to include
        refresh_interval: Refresh interval in seconds
        include_filters: Whether to include filters
        include_exports: Whether to include exports
        customization_options: Additional customization options

    Returns:
        Dictionary with dashboard configuration and data
    """
    return _global_usage_analytics_engine.create_usage_dashboard(
        dashboard_type=dashboard_type,
        dashboard_sections=dashboard_sections,
        refresh_interval=refresh_interval,
        include_filters=include_filters,
        include_exports=include_exports,
        customization_options=customization_options
    )
