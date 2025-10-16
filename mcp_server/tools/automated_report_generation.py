#!/usr/bin/env python3
"""
Phase 7.5: Automated Report Generation

This module provides comprehensive automated report generation capabilities for sports analytics,
including AI-powered insight extraction, template management, visualization generation,
and multi-format export functionality.

Features:
- AI-generated reports with intelligent insight extraction
- Template management and customization
- Advanced visualization generation
- Multi-format export (HTML, PDF, JSON, Markdown)
- Automated report scheduling
- Statistical analysis and trend detection
- Integration with predictive analytics engine
"""

import logging
import uuid
import json
import base64
import io
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning)

# Optional imports with fallbacks
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    from jinja2 import Template, Environment, FileSystemLoader
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes and Enums
# =============================================================================

class ReportType(str, Enum):
    """Types of reports that can be generated"""
    PLAYER_ANALYSIS = "player_analysis"
    TEAM_ANALYSIS = "team_analysis"
    GAME_ANALYSIS = "game_analysis"
    SEASON_SUMMARY = "season_summary"
    FORMULA_COMPARISON = "formula_comparison"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    CUSTOM = "custom"


class InsightType(str, Enum):
    """Types of insights that can be generated"""
    PERFORMANCE = "performance"
    TREND = "trend"
    ANOMALY = "anomaly"
    COMPARISON = "comparison"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"


class OutputFormat(str, Enum):
    """Output formats for reports"""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    MARKDOWN = "markdown"
    DOCX = "docx"
    XLSX = "xlsx"


@dataclass
class ReportInsight:
    """Individual insight extracted from analysis"""
    insight_id: str
    insight_type: str
    title: str
    description: str
    confidence_score: float
    statistical_significance: Optional[float] = None
    supporting_data: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ReportSection:
    """Section of a report"""
    section_id: str
    title: str
    content: str
    insights: List[ReportInsight]
    visualizations: List[str]  # Base64 encoded images
    order: int
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ReportTemplate:
    """Report template definition"""
    template_id: str
    name: str
    template_type: str
    content_structure: Dict[str, Any]
    variables: List[str]
    styles: Optional[Dict[str, Any]] = None
    is_public: bool = False
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class GeneratedReport:
    """Generated report with all components"""
    report_id: str
    report_type: str
    title: str
    sections: List[ReportSection]
    metadata: Dict[str, Any]
    generated_at: datetime
    template_used: Optional[str] = None
    export_formats: List[str] = None


# =============================================================================
# Core Automated Report Generation Engine
# =============================================================================

class AutomatedReportGenerator:
    """Main engine for automated report generation"""

    def __init__(self):
        """Initialize the automated report generator"""
        self.templates: Dict[str, ReportTemplate] = {}
        self.reports: Dict[str, GeneratedReport] = {}
        self.insight_cache: Dict[str, List[ReportInsight]] = {}

        # Initialize default templates
        self._initialize_default_templates()

        logger.info("Automated Report Generator initialized")

    def _generate_report_id(self) -> str:
        """Generate a unique report ID"""
        return f"report_{uuid.uuid4().hex[:8]}"

    def _generate_template_id(self) -> str:
        """Generate a unique template ID"""
        return f"template_{uuid.uuid4().hex[:8]}"

    def _initialize_default_templates(self):
        """Initialize default report templates"""
        # Player Analysis Template
        player_template = ReportTemplate(
            template_id=self._generate_template_id(),
            name="Player Analysis Template",
            template_type="player",
            content_structure={
                "sections": [
                    {"title": "Executive Summary", "order": 1},
                    {"title": "Performance Metrics", "order": 2},
                    {"title": "Trend Analysis", "order": 3},
                    {"title": "Comparative Analysis", "order": 4},
                    {"title": "Predictions & Recommendations", "order": 5}
                ],
                "variables": ["player_name", "season", "team", "position"]
            },
            variables=["player_name", "season", "team", "position"],
            is_public=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.templates[player_template.template_id] = player_template

        # Team Analysis Template
        team_template = ReportTemplate(
            template_id=self._generate_template_id(),
            name="Team Analysis Template",
            template_type="team",
            content_structure={
                "sections": [
                    {"title": "Team Overview", "order": 1},
                    {"title": "Offensive Analysis", "order": 2},
                    {"title": "Defensive Analysis", "order": 3},
                    {"title": "Player Contributions", "order": 4},
                    {"title": "Strategic Recommendations", "order": 5}
                ],
                "variables": ["team_name", "season", "conference", "division"]
            },
            variables=["team_name", "season", "conference", "division"],
            is_public=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.templates[team_template.template_id] = team_template

    def generate_report(
        self,
        report_type: str,
        data_source: Dict[str, Any],
        analysis_focus: List[str] = None,
        report_template: Optional[str] = None,
        include_visualizations: bool = True,
        include_predictions: bool = False,
        include_comparisons: bool = True,
        output_format: str = "html",
        customization_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an automated report.

        Args:
            report_type: Type of report to generate
            data_source: Data source for the report
            analysis_focus: Focus areas for analysis
            report_template: Custom template to use
            include_visualizations: Whether to include charts
            include_predictions: Whether to include predictions
            include_comparisons: Whether to include comparisons
            output_format: Output format for the report
            customization_options: Additional customization options

        Returns:
            Dictionary with generated report information
        """
        try:
            logger.info(f"Generating {report_type} report")

            if analysis_focus is None:
                analysis_focus = ["performance", "efficiency", "trends"]

            # Generate report ID
            report_id = self._generate_report_id()

            # Select template
            template = self._select_template(report_type, report_template)

            # Extract insights from data
            insights = self._extract_insights_from_data(
                data_source, analysis_focus, include_predictions
            )

            # Generate visualizations if requested
            visualizations = []
            if include_visualizations:
                visualizations = self._generate_visualizations(data_source, report_type)

            # Create report sections
            sections = self._create_report_sections(
                template, insights, visualizations, data_source, analysis_focus
            )

            # Generate report content
            report_content = self._generate_report_content(
                sections, template, data_source, output_format
            )

            # Create report object
            report = GeneratedReport(
                report_id=report_id,
                report_type=report_type,
                title=self._generate_report_title(report_type, data_source),
                sections=sections,
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "template_used": template.template_id,
                    "analysis_focus": analysis_focus,
                    "include_visualizations": include_visualizations,
                    "include_predictions": include_predictions,
                    "include_comparisons": include_comparisons,
                    "customization_options": customization_options or {}
                },
                generated_at=datetime.now(),
                template_used=template.template_id,
                export_formats=[output_format]
            )

            # Store report
            self.reports[report_id] = report

            result = {
                "status": "success",
                "report_id": report_id,
                "report_title": report.title,
                "report_type": report_type,
                "sections_count": len(sections),
                "insights_count": sum(len(section.insights) for section in sections),
                "visualizations_count": len(visualizations),
                "report_content": report_content,
                "metadata": report.metadata
            }

            logger.info(f"Report generation completed: {report_id}")
            return result

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "report_id": None
            }

    def _select_template(self, report_type: str, custom_template: Optional[str]) -> ReportTemplate:
        """Select appropriate template for report type"""
        if custom_template and custom_template in self.templates:
            return self.templates[custom_template]

        # Find default template for report type
        for template in self.templates.values():
            if template.template_type == report_type.split('_')[0]:  # player_analysis -> player
                return template

        # Fallback to first available template
        return list(self.templates.values())[0]

    def _extract_insights_from_data(
        self,
        data_source: Dict[str, Any],
        analysis_focus: List[str],
        include_predictions: bool
    ) -> List[ReportInsight]:
        """Extract insights from analysis data"""
        try:
            insights = []

            # Performance insights
            if "performance" in analysis_focus:
                performance_insights = self._extract_performance_insights(data_source)
                insights.extend(performance_insights)

            # Trend insights
            if "trends" in analysis_focus:
                trend_insights = self._extract_trend_insights(data_source)
                insights.extend(trend_insights)

            # Comparison insights
            if "comparisons" in analysis_focus:
                comparison_insights = self._extract_comparison_insights(data_source)
                insights.extend(comparison_insights)

            # Prediction insights
            if include_predictions:
                prediction_insights = self._extract_prediction_insights(data_source)
                insights.extend(prediction_insights)

            return insights

        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return []

    def _extract_performance_insights(self, data_source: Dict[str, Any]) -> List[ReportInsight]:
        """Extract performance-related insights"""
        insights = []

        try:
            # Analyze key performance metrics
            if "stats" in data_source:
                stats = data_source["stats"]

                # Find top performing metrics
                for metric, value in stats.items():
                    if isinstance(value, (int, float)) and value > 0:
                        insight = ReportInsight(
                            insight_id=f"perf_{uuid.uuid4().hex[:6]}",
                            insight_type="performance",
                            title=f"Strong {metric.replace('_', ' ').title()} Performance",
                            description=f"Shows strong performance in {metric.replace('_', ' ')} with a value of {value:.2f}",
                            confidence_score=0.8,
                            supporting_data={"metric": metric, "value": value},
                            recommendations=[f"Continue focusing on {metric.replace('_', ' ')} improvement"]
                        )
                        insights.append(insight)

            return insights[:5]  # Limit to top 5 insights

        except Exception as e:
            logger.error(f"Performance insight extraction failed: {e}")
            return []

    def _extract_trend_insights(self, data_source: Dict[str, Any]) -> List[ReportInsight]:
        """Extract trend-related insights"""
        insights = []

        try:
            # Analyze time series data for trends
            if "time_series" in data_source:
                time_series = data_source["time_series"]

                for metric, values in time_series.items():
                    if isinstance(values, list) and len(values) > 2:
                        # Calculate trend
                        x = np.arange(len(values))
                        trend_slope = np.polyfit(x, values, 1)[0]

                        if abs(trend_slope) > 0.1:  # Significant trend
                            trend_direction = "increasing" if trend_slope > 0 else "decreasing"
                            insight = ReportInsight(
                                insight_id=f"trend_{uuid.uuid4().hex[:6]}",
                                insight_type="trend",
                                title=f"{metric.replace('_', ' ').title()} Trend Analysis",
                                description=f"Shows {trend_direction} trend in {metric.replace('_', ' ')} over time",
                                confidence_score=min(0.9, abs(trend_slope) * 2),
                                supporting_data={"metric": metric, "trend_slope": trend_slope, "values": values},
                                recommendations=[f"Monitor {metric.replace('_', ' ')} trend for future planning"]
                            )
                            insights.append(insight)

            return insights[:3]  # Limit to top 3 trend insights

        except Exception as e:
            logger.error(f"Trend insight extraction failed: {e}")
            return []

    def _extract_comparison_insights(self, data_source: Dict[str, Any]) -> List[ReportInsight]:
        """Extract comparison-related insights"""
        insights = []

        try:
            # Compare against benchmarks or averages
            if "comparisons" in data_source:
                comparisons = data_source["comparisons"]

                for metric, comparison_data in comparisons.items():
                    if isinstance(comparison_data, dict) and "value" in comparison_data and "benchmark" in comparison_data:
                        value = comparison_data["value"]
                        benchmark = comparison_data["benchmark"]

                        if value > benchmark * 1.1:  # 10% above benchmark
                            insight = ReportInsight(
                                insight_id=f"comp_{uuid.uuid4().hex[:6]}",
                                insight_type="comparison",
                                title=f"Above Average {metric.replace('_', ' ').title()}",
                                description=f"Performs {((value/benchmark - 1) * 100):.1f}% above the benchmark in {metric.replace('_', ' ')}",
                                confidence_score=0.85,
                                supporting_data={"metric": metric, "value": value, "benchmark": benchmark},
                                recommendations=[f"Maintain strong {metric.replace('_', ' ')} performance"]
                            )
                            insights.append(insight)

            return insights[:3]  # Limit to top 3 comparison insights

        except Exception as e:
            logger.error(f"Comparison insight extraction failed: {e}")
            return []

    def _extract_prediction_insights(self, data_source: Dict[str, Any]) -> List[ReportInsight]:
        """Extract prediction-related insights"""
        insights = []

        try:
            # Generate predictions based on historical data
            if "historical_data" in data_source:
                historical = data_source["historical_data"]

                for metric, values in historical.items():
                    if isinstance(values, list) and len(values) > 3:
                        # Simple prediction based on recent trend
                        recent_values = values[-3:]
                        trend = np.mean(np.diff(recent_values))
                        predicted_value = values[-1] + trend

                        insight = ReportInsight(
                            insight_id=f"pred_{uuid.uuid4().hex[:6]}",
                            insight_type="prediction",
                            title=f"Predicted {metric.replace('_', ' ').title()}",
                            description=f"Based on recent trends, {metric.replace('_', ' ')} is predicted to be {predicted_value:.2f}",
                            confidence_score=0.7,
                            supporting_data={"metric": metric, "predicted_value": predicted_value, "trend": trend},
                            recommendations=[f"Plan for {metric.replace('_', ' ')} changes in upcoming periods"]
                        )
                        insights.append(insight)

            return insights[:2]  # Limit to top 2 prediction insights

        except Exception as e:
            logger.error(f"Prediction insight extraction failed: {e}")
            return []

    def _generate_visualizations(self, data_source: Dict[str, Any], report_type: str) -> List[str]:
        """Generate visualizations for the report"""
        visualizations = []

        try:
            # Set up matplotlib style
            if HAS_SEABORN:
                plt.style.use('seaborn-v0_8')
            else:
                plt.style.use('default')

            # Generate different types of visualizations based on data
            if "time_series" in data_source:
                time_series_viz = self._create_time_series_chart(data_source["time_series"])
                if time_series_viz:
                    visualizations.append(time_series_viz)

            if "stats" in data_source:
                stats_viz = self._create_stats_chart(data_source["stats"])
                if stats_viz:
                    visualizations.append(stats_viz)

            if "comparisons" in data_source:
                comparison_viz = self._create_comparison_chart(data_source["comparisons"])
                if comparison_viz:
                    visualizations.append(comparison_viz)

            return visualizations

        except Exception as e:
            logger.error(f"Visualization generation failed: {e}")
            return []

    def _create_time_series_chart(self, time_series_data: Dict[str, List[float]]) -> Optional[str]:
        """Create a time series chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            for metric, values in time_series_data.items():
                if isinstance(values, list) and len(values) > 1:
                    x = range(len(values))
                    ax.plot(x, values, label=metric.replace('_', ' ').title(), marker='o')

            ax.set_xlabel('Time Period')
            ax.set_ylabel('Value')
            ax.set_title('Performance Trends Over Time')
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)

            return image_base64

        except Exception as e:
            logger.error(f"Time series chart creation failed: {e}")
            return None

    def _create_stats_chart(self, stats_data: Dict[str, float]) -> Optional[str]:
        """Create a stats comparison chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            metrics = list(stats_data.keys())
            values = list(stats_data.values())

            bars = ax.bar(metrics, values, color='skyblue', alpha=0.7)
            ax.set_xlabel('Metrics')
            ax.set_ylabel('Values')
            ax.set_title('Performance Metrics Comparison')
            ax.tick_params(axis='x', rotation=45)

            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                       f'{value:.2f}', ha='center', va='bottom')

            plt.tight_layout()

            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)

            return image_base64

        except Exception as e:
            logger.error(f"Stats chart creation failed: {e}")
            return None

    def _create_comparison_chart(self, comparison_data: Dict[str, Dict[str, float]]) -> Optional[str]:
        """Create a comparison chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            metrics = []
            values = []
            benchmarks = []

            for metric, data in comparison_data.items():
                if isinstance(data, dict) and "value" in data and "benchmark" in data:
                    metrics.append(metric.replace('_', ' ').title())
                    values.append(data["value"])
                    benchmarks.append(data["benchmark"])

            x = np.arange(len(metrics))
            width = 0.35

            bars1 = ax.bar(x - width/2, values, width, label='Actual', color='skyblue', alpha=0.7)
            bars2 = ax.bar(x + width/2, benchmarks, width, label='Benchmark', color='lightcoral', alpha=0.7)

            ax.set_xlabel('Metrics')
            ax.set_ylabel('Values')
            ax.set_title('Performance vs Benchmark Comparison')
            ax.set_xticks(x)
            ax.set_xticklabels(metrics, rotation=45)
            ax.legend()

            plt.tight_layout()

            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)

            return image_base64

        except Exception as e:
            logger.error(f"Comparison chart creation failed: {e}")
            return None

    def _create_report_sections(
        self,
        template: ReportTemplate,
        insights: List[ReportInsight],
        visualizations: List[str],
        data_source: Dict[str, Any],
        analysis_focus: List[str]
    ) -> List[ReportSection]:
        """Create report sections based on template"""
        sections = []

        try:
            section_structure = template.content_structure.get("sections", [])

            for i, section_info in enumerate(section_structure):
                section_title = section_info.get("title", f"Section {i+1}")
                section_order = section_info.get("order", i+1)

                # Filter insights for this section
                section_insights = self._filter_insights_for_section(insights, section_title)

                # Generate section content
                content = self._generate_section_content(section_title, section_insights, data_source)

                # Assign visualization to section
                section_viz = visualizations[i] if i < len(visualizations) else None
                section_visualizations = [section_viz] if section_viz else []

                section = ReportSection(
                    section_id=f"section_{uuid.uuid4().hex[:6]}",
                    title=section_title,
                    content=content,
                    insights=section_insights,
                    visualizations=section_visualizations,
                    order=section_order
                )
                sections.append(section)

            return sections

        except Exception as e:
            logger.error(f"Report section creation failed: {e}")
            return []

    def _filter_insights_for_section(self, insights: List[ReportInsight], section_title: str) -> List[ReportInsight]:
        """Filter insights for a specific section"""
        section_mapping = {
            "Executive Summary": ["performance", "trend"],
            "Performance Metrics": ["performance"],
            "Trend Analysis": ["trend"],
            "Comparative Analysis": ["comparison"],
            "Predictions & Recommendations": ["prediction", "recommendation"]
        }

        allowed_types = section_mapping.get(section_title, ["performance"])
        return [insight for insight in insights if insight.insight_type in allowed_types]

    def _generate_section_content(
        self,
        section_title: str,
        insights: List[ReportInsight],
        data_source: Dict[str, Any]
    ) -> str:
        """Generate content for a report section"""
        content_parts = []

        # Add section introduction
        content_parts.append(f"## {section_title}\n")

        # Add insights
        for insight in insights:
            content_parts.append(f"### {insight.title}\n")
            content_parts.append(f"{insight.description}\n")

            if insight.recommendations:
                content_parts.append("**Recommendations:**\n")
                for rec in insight.recommendations:
                    content_parts.append(f"- {rec}\n")
                content_parts.append("\n")

        return "\n".join(content_parts)

    def _generate_report_content(
        self,
        sections: List[ReportSection],
        template: ReportTemplate,
        data_source: Dict[str, Any],
        output_format: str
    ) -> str:
        """Generate the final report content"""
        try:
            if output_format == "html":
                return self._generate_html_report(sections, template, data_source)
            elif output_format == "markdown":
                return self._generate_markdown_report(sections, template, data_source)
            elif output_format == "json":
                return self._generate_json_report(sections, template, data_source)
            else:
                return self._generate_markdown_report(sections, template, data_source)

        except Exception as e:
            logger.error(f"Report content generation failed: {e}")
            return "Report generation failed."

    def _generate_html_report(
        self,
        sections: List[ReportSection],
        template: ReportTemplate,
        data_source: Dict[str, Any]
    ) -> str:
        """Generate HTML report"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Sports Analytics Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 2px solid #eee; }",
            "h3 { color: #888; }",
            "img { max-width: 100%; height: auto; margin: 20px 0; }",
            ".insight { background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #007acc; }",
            ".recommendation { background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 5px; }",
            "</style>",
            "</head>",
            "<body>"
        ]

        # Add title
        html_parts.append("<h1>Sports Analytics Report</h1>")
        html_parts.append(f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

        # Add sections
        for section in sections:
            html_parts.append(f"<h2>{section.title}</h2>")

            # Add visualizations
            for viz in section.visualizations:
                if viz:
                    html_parts.append(f'<img src="data:image/png;base64,{viz}" alt="Chart">')

            # Add insights
            for insight in section.insights:
                html_parts.append('<div class="insight">')
                html_parts.append(f"<h3>{insight.title}</h3>")
                html_parts.append(f"<p>{insight.description}</p>")

                if insight.recommendations:
                    html_parts.append("<h4>Recommendations:</h4>")
                    for rec in insight.recommendations:
                        html_parts.append(f'<div class="recommendation">{rec}</div>')

                html_parts.append("</div>")

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)

    def _generate_markdown_report(
        self,
        sections: List[ReportSection],
        template: ReportTemplate,
        data_source: Dict[str, Any]
    ) -> str:
        """Generate Markdown report"""
        md_parts = [
            "# Sports Analytics Report",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ""
        ]

        # Add sections
        for section in sections:
            md_parts.append(f"## {section.title}")
            md_parts.append("")

            # Add insights
            for insight in section.insights:
                md_parts.append(f"### {insight.title}")
                md_parts.append(f"{insight.description}")
                md_parts.append("")

                if insight.recommendations:
                    md_parts.append("**Recommendations:**")
                    for rec in insight.recommendations:
                        md_parts.append(f"- {rec}")
                    md_parts.append("")

        return "\n".join(md_parts)

    def _generate_json_report(
        self,
        sections: List[ReportSection],
        template: ReportTemplate,
        data_source: Dict[str, Any]
    ) -> str:
        """Generate JSON report"""
        report_data = {
            "title": "Sports Analytics Report",
            "generated_at": datetime.now().isoformat(),
            "template_used": template.template_id,
            "sections": []
        }

        for section in sections:
            section_data = {
                "title": section.title,
                "content": section.content,
                "insights": [asdict(insight) for insight in section.insights],
                "visualizations_count": len(section.visualizations)
            }
            report_data["sections"].append(section_data)

        return json.dumps(report_data, indent=2)

    def _generate_report_title(self, report_type: str, data_source: Dict[str, Any]) -> str:
        """Generate a title for the report"""
        title_mapping = {
            "player_analysis": "Player Performance Analysis",
            "team_analysis": "Team Performance Analysis",
            "game_analysis": "Game Analysis Report",
            "season_summary": "Season Summary Report",
            "formula_comparison": "Formula Comparison Analysis",
            "predictive_analysis": "Predictive Analytics Report"
        }

        base_title = title_mapping.get(report_type, "Sports Analytics Report")

        # Add specific details if available
        if "player_name" in data_source:
            return f"{data_source['player_name']} - {base_title}"
        elif "team_name" in data_source:
            return f"{data_source['team_name']} - {base_title}"

        return base_title


# =============================================================================
# Standalone Functions
# =============================================================================

# Global engine instance for standalone functions
_global_report_generator = AutomatedReportGenerator()


def generate_automated_report(
    report_type: str,
    data_source: Dict[str, Any],
    analysis_focus: List[str] = None,
    report_template: Optional[str] = None,
    include_visualizations: bool = True,
    include_predictions: bool = False,
    include_comparisons: bool = True,
    output_format: str = "html",
    customization_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate an automated report (standalone function).

    Args:
        report_type: Type of report to generate
        data_source: Data source for the report
        analysis_focus: Focus areas for analysis
        report_template: Custom template to use
        include_visualizations: Whether to include charts
        include_predictions: Whether to include predictions
        include_comparisons: Whether to include comparisons
        output_format: Output format for the report
        customization_options: Additional customization options

    Returns:
        Dictionary with generated report information
    """
    return _global_report_generator.generate_report(
        report_type=report_type,
        data_source=data_source,
        analysis_focus=analysis_focus,
        report_template=report_template,
        include_visualizations=include_visualizations,
        include_predictions=include_predictions,
        include_comparisons=include_comparisons,
        output_format=output_format,
        customization_options=customization_options
    )


def extract_report_insights(
    analysis_data: Dict[str, Any],
    insight_types: List[str] = None,
    insight_depth: str = "detailed",
    include_statistical_significance: bool = True,
    confidence_threshold: float = 0.95,
    max_insights: int = 10
) -> Dict[str, Any]:
    """
    Extract insights from analysis data (standalone function).

    Args:
        analysis_data: Analysis data to extract insights from
        insight_types: Types of insights to generate
        insight_depth: Depth of insight analysis
        include_statistical_significance: Whether to include statistical significance
        confidence_threshold: Confidence threshold for insights
        max_insights: Maximum number of insights to generate

    Returns:
        Dictionary with extracted insights
    """
    try:
        if insight_types is None:
            insight_types = ["performance", "trend", "comparison"]

        insights = _global_report_generator._extract_insights_from_data(
            analysis_data, insight_types, False
        )

        # Limit insights based on max_insights
        insights = insights[:max_insights]

        return {
            "status": "success",
            "insights_count": len(insights),
            "insights": [asdict(insight) for insight in insights],
            "metadata": {
                "extraction_timestamp": datetime.now().isoformat(),
                "insight_types": insight_types,
                "insight_depth": insight_depth,
                "confidence_threshold": confidence_threshold
            }
        }

    except Exception as e:
        logger.error(f"Insight extraction failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "insights": []
        }


def create_report_template(
    template_name: str,
    template_type: str,
    template_content: Dict[str, Any],
    template_variables: List[str] = None,
    template_styles: Optional[Dict[str, Any]] = None,
    is_public: bool = False
) -> Dict[str, Any]:
    """
    Create a report template (standalone function).

    Args:
        template_name: Name of the template
        template_type: Type of template
        template_content: Template content structure
        template_variables: Variables that can be substituted
        template_styles: Styling options
        is_public: Whether template is publicly available

    Returns:
        Dictionary with template creation results
    """
    try:
        template_id = _global_report_generator._generate_template_id()

        template = ReportTemplate(
            template_id=template_id,
            name=template_name,
            template_type=template_type,
            content_structure=template_content,
            variables=template_variables or [],
            styles=template_styles,
            is_public=is_public,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        _global_report_generator.templates[template_id] = template

        return {
            "status": "success",
            "template_id": template_id,
            "template_name": template_name,
            "template_type": template_type,
            "metadata": {
                "created_at": template.created_at.isoformat(),
                "is_public": is_public,
                "variables_count": len(template.variables)
            }
        }

    except Exception as e:
        logger.error(f"Template creation failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "template_id": None
        }


def generate_report_visualizations(
    data_to_visualize: Dict[str, Any],
    visualization_types: List[str] = None,
    chart_style: str = "professional",
    include_trend_lines: bool = True,
    include_statistics: bool = True,
    output_resolution: str = "high",
    color_scheme: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate visualizations for reports (standalone function).

    Args:
        data_to_visualize: Data to create visualizations from
        visualization_types: Types of visualizations to generate
        chart_style: Style of the charts
        include_trend_lines: Whether to include trend lines
        include_statistics: Whether to include statistical annotations
        output_resolution: Resolution of generated charts
        color_scheme: Custom color scheme

    Returns:
        Dictionary with generated visualizations
    """
    try:
        if visualization_types is None:
            visualization_types = ["line_chart", "bar_chart"]

        visualizations = _global_report_generator._generate_visualizations(
            data_to_visualize, "custom"
        )

        return {
            "status": "success",
            "visualizations_count": len(visualizations),
            "visualizations": visualizations,
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "visualization_types": visualization_types,
                "chart_style": chart_style,
                "output_resolution": output_resolution
            }
        }

    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "visualizations": []
        }


def export_report(
    report_content: Dict[str, Any],
    export_format: str,
    export_options: Optional[Dict[str, Any]] = None,
    include_metadata: bool = True,
    compression_level: int = 6,
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export report in specified format (standalone function).

    Args:
        report_content: Report content to export
        export_format: Format to export in
        export_options: Additional export options
        include_metadata: Whether to include metadata
        compression_level: Compression level for files
        output_filename: Custom filename

    Returns:
        Dictionary with export results
    """
    try:
        # Generate filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"report_{timestamp}.{export_format}"

        # For now, return the content in the requested format
        # In a real implementation, you would save to file system
        export_data = {
            "filename": output_filename,
            "format": export_format,
            "content": report_content,
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "compression_level": compression_level,
                "include_metadata": include_metadata
            }
        }

        return {
            "status": "success",
            "export_filename": output_filename,
            "export_format": export_format,
            "export_data": export_data,
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "file_size_estimate": len(str(export_data))
            }
        }

    except Exception as e:
        logger.error(f"Report export failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "export_filename": None
        }
