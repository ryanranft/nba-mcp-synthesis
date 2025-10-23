#!/usr/bin/env python3
"""
Recommendation Prioritization Engine

Automatically scores and ranks AI-generated recommendations based on:
- Impact (business value, user benefit, strategic alignment)
- Effort (time estimate, complexity, dependencies)
- Data availability (do we have the required data?)
- Feasibility (libraries available, validated)
- Dependencies (requires other recommendations first?)

Outputs prioritized lists:
- Quick Wins (high impact, low effort)
- Strategic Projects (high impact, high effort)
- Low Priority (low impact)
- Blocked (missing dependencies or data)

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-21
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PriorityScore:
    """Priority score breakdown for a recommendation"""

    impact_score: float  # 0-10
    effort_score: float  # 0-10 (higher = less effort)
    data_score: float  # 0-10
    feasibility_score: float  # 0-10
    dependency_score: float  # 0-10
    total_score: float  # Weighted average
    priority_tier: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # Quick Win, Strategic, Low Priority, Blocked


class RecommendationPrioritizer:
    """
    Prioritizes recommendations using multi-factor scoring algorithm.

    Scoring Factors:
    1. Impact (35%): Business value, strategic alignment, user benefit
    2. Effort (25%): Time estimate, complexity (inversed)
    3. Data Availability (20%): Required data exists in database
    4. Feasibility (15%): Libraries validated, no blockers
    5. Dependencies (5%): Can be implemented without waiting
    """

    # Scoring weights
    WEIGHTS = {
        "impact": 0.35,
        "effort": 0.25,
        "data": 0.20,
        "feasibility": 0.15,
        "dependencies": 0.05,
    }

    # Priority mappings
    PRIORITY_VALUES = {
        "CRITICAL": 10,
        "IMPORTANT": 8,
        "NICE_TO_HAVE": 5,
        "OPTIONAL": 3,
    }

    # Time estimate difficulty (hours)
    TIME_THRESHOLDS = {
        "trivial": 2,  # <= 2 hours
        "easy": 4,  # <= 4 hours
        "moderate": 8,  # <= 8 hours
        "challenging": 16,  # <= 16 hours
        "complex": 40,  # <= 40 hours
        "epic": float("inf"),  # > 40 hours
    }

    def __init__(self, project_inventory: Optional[Dict] = None):
        """
        Initialize prioritizer.

        Args:
            project_inventory: Project context with data schema, requirements, etc.
        """
        self.project_inventory = project_inventory or {}
        self.data_schema = self._extract_data_schema()
        logger.info("📊 Recommendation Prioritizer initialized")

    def _extract_data_schema(self) -> Dict[str, List[str]]:
        """Extract table.column schema from project inventory"""
        schema = {}

        inventory = self.project_inventory.get("data_inventory", {})
        tables = inventory.get("schema", {}).get("tables", {})

        for table_name, table_info in tables.items():
            column_names = table_info.get("column_names", [])
            schema[table_name] = column_names

        return schema

    def prioritize_recommendations(
        self, recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize a list of recommendations.

        Args:
            recommendations: List of recommendation dictionaries

        Returns:
            Sorted list with priority scores added
        """
        logger.info(f"🔍 Prioritizing {len(recommendations)} recommendations...")

        scored_recs = []

        for idx, rec in enumerate(recommendations):
            try:
                # Calculate priority score
                score = self.score_recommendation(rec)

                # Add score to recommendation
                rec["priority_score"] = {
                    "impact": score.impact_score,
                    "effort": score.effort_score,
                    "data": score.data_score,
                    "feasibility": score.feasibility_score,
                    "dependencies": score.dependency_score,
                    "total": score.total_score,
                    "tier": score.priority_tier,
                    "category": score.category,
                }

                scored_recs.append(rec)

            except Exception as e:
                logger.warning(
                    f"⚠️  Failed to score recommendation '{rec.get('title', 'Unknown')}': {e}"
                )
                # Add default low score
                rec["priority_score"] = {
                    "total": 0.0,
                    "tier": "LOW",
                    "category": "Unknown",
                }
                scored_recs.append(rec)

        # Sort by total score (descending)
        scored_recs.sort(
            key=lambda r: r.get("priority_score", {}).get("total", 0), reverse=True
        )

        logger.info("✅ Prioritization complete")
        self._log_priority_summary(scored_recs)

        return scored_recs

    def score_recommendation(self, recommendation: Dict[str, Any]) -> PriorityScore:
        """Calculate priority score for a single recommendation"""

        # Score each dimension
        impact_score = self._score_impact(recommendation)
        effort_score = self._score_effort(recommendation)
        data_score = self._score_data_availability(recommendation)
        feasibility_score = self._score_feasibility(recommendation)
        dependency_score = self._score_dependencies(recommendation)

        # Calculate weighted total
        total_score = (
            impact_score * self.WEIGHTS["impact"]
            + effort_score * self.WEIGHTS["effort"]
            + data_score * self.WEIGHTS["data"]
            + feasibility_score * self.WEIGHTS["feasibility"]
            + dependency_score * self.WEIGHTS["dependencies"]
        )

        # Determine priority tier
        priority_tier = self._determine_tier(recommendation, total_score)

        # Determine category
        category = self._categorize_recommendation(
            impact_score, effort_score, data_score
        )

        return PriorityScore(
            impact_score=impact_score,
            effort_score=effort_score,
            data_score=data_score,
            feasibility_score=feasibility_score,
            dependency_score=dependency_score,
            total_score=round(total_score, 2),
            priority_tier=priority_tier,
            category=category,
        )

    def _score_impact(self, rec: Dict[str, Any]) -> float:
        """Score business impact (0-10)"""
        score = 0.0

        # Base score from priority field
        priority = rec.get("priority", "NICE_TO_HAVE")
        score += self.PRIORITY_VALUES.get(priority, 5)

        # Adjust for strategic keywords
        text = (rec.get("description", "") + " " + rec.get("title", "")).lower()

        impact_keywords = {
            "prediction": 1.0,
            "accuracy": 0.8,
            "performance": 0.8,
            "model": 0.7,
            "optimization": 0.7,
            "real-time": 0.9,
            "production": 0.8,
            "scalability": 0.7,
            "monitoring": 0.6,
        }

        for keyword, weight in impact_keywords.items():
            if keyword in text:
                score += weight

        # Cap at 10
        return min(score, 10.0)

    def _score_effort(self, rec: Dict[str, Any]) -> float:
        """Score effort (0-10, higher = less effort)"""

        # Extract time estimate
        time_str = rec.get("time_estimate", "8 hours")
        hours = self._parse_hours(time_str)

        # Map hours to difficulty
        difficulty = "moderate"
        for level, threshold in self.TIME_THRESHOLDS.items():
            if hours <= threshold:
                difficulty = level
                break

        # Score based on difficulty (inverse - less time = higher score)
        difficulty_scores = {
            "trivial": 10.0,
            "easy": 9.0,
            "moderate": 7.0,
            "challenging": 5.0,
            "complex": 3.0,
            "epic": 1.0,
        }

        score = difficulty_scores.get(difficulty, 5.0)

        # Adjust for number of implementation steps
        steps = rec.get("implementation_steps", [])
        if isinstance(steps, list):
            if len(steps) > 10:
                score -= 1.0
            elif len(steps) < 3:
                score += 0.5

        return max(min(score, 10.0), 0.0)

    def _score_data_availability(self, rec: Dict[str, Any]) -> float:
        """Score data availability (0-10)"""

        if not self.data_schema:
            # No schema available - assume data exists
            return 7.0

        # Extract data references from text
        text = rec.get("description", "") + " " + rec.get("technical_details", "")
        data_refs = self._extract_data_references(text)

        if not data_refs:
            # No specific data references - neutral score
            return 7.0

        # Check how many references exist in schema
        total_refs = 0
        found_refs = 0

        for table, columns in data_refs.items():
            if table in self.data_schema:
                for col in columns:
                    total_refs += 1
                    if col in self.data_schema[table]:
                        found_refs += 1
            else:
                total_refs += len(columns)

        if total_refs == 0:
            return 7.0

        # Calculate percentage found
        percentage = found_refs / total_refs
        score = percentage * 10

        return round(score, 2)

    def _score_feasibility(self, rec: Dict[str, Any]) -> float:
        """Score technical feasibility (0-10)"""
        score = 7.0  # Default: assume feasible

        # Check validation results if available
        validation = rec.get("validation", {})

        if validation:
            passed = validation.get("passed", True)
            errors = validation.get("errors_count", 0)
            warnings = validation.get("warnings_count", 0)

            if passed and errors == 0:
                score = 10.0
            elif errors > 0:
                score = max(5.0 - errors, 0.0)
            elif warnings > 0:
                score = 8.0 - (warnings * 0.5)

        # Check for blocker keywords
        text = (
            rec.get("description", "") + " " + rec.get("technical_details", "")
        ).lower()

        blocker_keywords = ["experimental", "unstable", "deprecated", "beta", "alpha"]
        for keyword in blocker_keywords:
            if keyword in text:
                score -= 2.0

        return max(min(score, 10.0), 0.0)

    def _score_dependencies(self, rec: Dict[str, Any]) -> float:
        """Score dependency freedom (0-10, higher = fewer dependencies)"""

        # Check for dependency keywords
        text = (rec.get("description", "") + " " + rec.get("prerequisites", "")).lower()

        dependency_keywords = [
            "requires",
            "depends on",
            "prerequisite",
            "must first",
            "before this",
            "after",
            "once you have",
        ]

        dependency_count = sum(1 for kw in dependency_keywords if kw in text)

        # More dependencies = lower score
        if dependency_count == 0:
            return 10.0
        elif dependency_count == 1:
            return 8.0
        elif dependency_count == 2:
            return 6.0
        else:
            return max(4.0 - dependency_count, 0.0)

    def _determine_tier(self, rec: Dict[str, Any], total_score: float) -> str:
        """Determine priority tier based on score and original priority"""

        # Honor original priority if CRITICAL
        original_priority = rec.get("priority", "NICE_TO_HAVE")
        if original_priority == "CRITICAL" and total_score >= 6.0:
            return "CRITICAL"

        # Score-based tiers
        if total_score >= 8.0:
            return "CRITICAL"
        elif total_score >= 6.5:
            return "HIGH"
        elif total_score >= 4.5:
            return "MEDIUM"
        else:
            return "LOW"

    def _categorize_recommendation(
        self, impact: float, effort: float, data: float
    ) -> str:
        """Categorize recommendation by impact/effort matrix"""

        # Quick Wins: High impact, low effort
        if impact >= 7.0 and effort >= 7.0 and data >= 7.0:
            return "Quick Win"

        # Strategic Projects: High impact, high effort
        elif impact >= 7.0 and effort < 7.0:
            return "Strategic Project"

        # Low Priority: Low impact
        elif impact < 5.0:
            return "Low Priority"

        # Blocked: Missing data or not feasible
        elif data < 5.0:
            return "Blocked (Missing Data)"

        # Medium Priority: Everything else
        else:
            return "Medium Priority"

    def _extract_data_references(self, text: str) -> Dict[str, List[str]]:
        """Extract table.column references from text"""
        data_refs = {}

        # Pattern: table_name.column_name
        pattern = r"\b(\w+)\.(\w+)\b"

        for match in re.finditer(pattern, text):
            table = match.group(1)
            column = match.group(2)

            # Filter out likely false positives
            if table in ["self", "this", "that", "cls", "df", "pd", "np"]:
                continue

            if table not in data_refs:
                data_refs[table] = []
            if column not in data_refs[table]:
                data_refs[table].append(column)

        return data_refs

    def _parse_hours(self, time_str: str) -> float:
        """Parse time estimate string to hours"""
        try:
            # Extract number from string like "8 hours" or "8-12 hours"
            import re

            numbers = re.findall(r"\d+", time_str)
            if numbers:
                # Take average if range
                if len(numbers) > 1:
                    return (int(numbers[0]) + int(numbers[1])) / 2
                return float(numbers[0])
        except:
            pass

        return 8.0  # Default: 8 hours

    def _log_priority_summary(self, recommendations: List[Dict]):
        """Log summary of prioritization results"""
        categories = {}
        tiers = {}

        for rec in recommendations:
            score = rec.get("priority_score", {})
            category = score.get("category", "Unknown")
            tier = score.get("tier", "MEDIUM")

            categories[category] = categories.get(category, 0) + 1
            tiers[tier] = tiers.get(tier, 0) + 1

        logger.info("\n📊 Prioritization Summary:")
        logger.info("  Categories:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            logger.info(f"    - {cat}: {count}")

        logger.info("  Priority Tiers:")
        for tier in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = tiers.get(tier, 0)
            logger.info(f"    - {tier}: {count}")

    def generate_priority_report(
        self, recommendations: List[Dict], output_path: Optional[str] = None
    ) -> str:
        """Generate markdown priority report"""

        report_lines = [
            "# Recommendation Prioritization Report",
            "",
            f"**Generated**: {datetime.now().isoformat()}",
            f"**Total Recommendations**: {len(recommendations)}",
            "",
            "---",
            "",
        ]

        # Group by category
        categories = {}
        for rec in recommendations:
            cat = rec.get("priority_score", {}).get("category", "Unknown")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(rec)

        # Quick Wins section
        if "Quick Win" in categories:
            report_lines.extend(
                [
                    "## 🎯 Quick Wins (High Impact, Low Effort)",
                    "",
                    "These recommendations deliver significant value with minimal effort.",
                    "**Recommendation: Implement these first!**",
                    "",
                ]
            )

            for rec in categories["Quick Win"][:10]:  # Top 10
                self._add_recommendation_to_report(report_lines, rec)

        # Strategic Projects section
        if "Strategic Project" in categories:
            report_lines.extend(
                [
                    "",
                    "## 🚀 Strategic Projects (High Impact, Higher Effort)",
                    "",
                    "These recommendations require more effort but deliver major value.",
                    "**Recommendation: Plan these for future sprints.**",
                    "",
                ]
            )

            for rec in categories["Strategic Project"][:10]:
                self._add_recommendation_to_report(report_lines, rec)

        # Medium Priority section
        if "Medium Priority" in categories:
            report_lines.extend(
                [
                    "",
                    "## 📋 Medium Priority",
                    "",
                    f"**{len(categories['Medium Priority'])} recommendations**",
                    "",
                    "See full prioritized list for details.",
                    "",
                ]
            )

        # Low Priority section
        if "Low Priority" in categories:
            report_lines.extend(
                [
                    "",
                    "## 📉 Low Priority",
                    "",
                    f"**{len(categories['Low Priority'])} recommendations**",
                    "",
                    "These can be deferred or skipped.",
                    "",
                ]
            )

        # Blocked section
        blocked_cats = [c for c in categories.keys() if "Blocked" in c]
        if blocked_cats:
            report_lines.extend(
                [
                    "",
                    "## ⛔ Blocked Recommendations",
                    "",
                    "These recommendations have blockers that must be resolved first.",
                    "",
                ]
            )

            for cat in blocked_cats:
                for rec in categories[cat][:5]:
                    self._add_recommendation_to_report(report_lines, rec)

        report = "\n".join(report_lines)

        # Save to file if path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"💾 Priority report saved: {output_path}")

        return report

    def _add_recommendation_to_report(self, lines: List[str], rec: Dict):
        """Add recommendation details to report"""
        score = rec.get("priority_score", {})

        lines.extend(
            [
                f"### {rec.get('title', 'Untitled')}",
                "",
                f"**Priority Score**: {score.get('total', 0):.2f}/10 | "
                f"**Tier**: {score.get('tier', 'MEDIUM')} | "
                f"**Effort**: {rec.get('time_estimate', 'Unknown')}",
                "",
                f"{rec.get('description', 'No description')[:200]}...",
                "",
                "**Scores**:",
                f"- Impact: {score.get('impact', 0):.1f}/10",
                f"- Effort: {score.get('effort', 0):.1f}/10",
                f"- Data: {score.get('data', 0):.1f}/10",
                f"- Feasibility: {score.get('feasibility', 0):.1f}/10",
                "",
            ]
        )


def main():
    """CLI for testing prioritization"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Prioritize recommendations")
    parser.add_argument(
        "--recommendations", required=True, help="Path to recommendations JSON"
    )
    parser.add_argument("--inventory", help="Path to project inventory JSON")
    parser.add_argument("--output", help="Output path for prioritized JSON")
    parser.add_argument("--report", help="Output path for markdown report")
    args = parser.parse_args()

    # Load recommendations
    with open(args.recommendations, "r") as f:
        data = json.load(f)

    # Handle different file structures
    if isinstance(data, list):
        recommendations = data
    elif isinstance(data, dict):
        # Check if it's wrapped in metadata
        if "recommendations" in data:
            recommendations = data["recommendations"]
        else:
            recommendations = [data]
    else:
        recommendations = [data]

    # Load inventory if provided
    inventory = None
    if args.inventory and Path(args.inventory).exists():
        with open(args.inventory, "r") as f:
            inventory = json.load(f)

    # Prioritize
    prioritizer = RecommendationPrioritizer(inventory)
    prioritized = prioritizer.prioritize_recommendations(recommendations)

    # Save prioritized JSON
    if args.output:
        with open(args.output, "w") as f:
            json.dump(prioritized, f, indent=2)
        print(f"✅ Prioritized recommendations saved: {args.output}")

    # Generate report
    if args.report:
        report = prioritizer.generate_priority_report(prioritized, args.report)
        print(f"✅ Priority report saved: {args.report}")
    else:
        # Print top 10
        print("\n" + "=" * 80)
        print("TOP 10 PRIORITIES")
        print("=" * 80 + "\n")

        for i, rec in enumerate(prioritized[:10], 1):
            score = rec.get("priority_score", {})
            print(f"{i}. {rec.get('title', 'Untitled')}")
            print(
                f"   Score: {score.get('total', 0):.2f}/10 | {score.get('category', 'Unknown')}"
            )
            print(f"   Effort: {rec.get('time_estimate', 'Unknown')}")
            print()


if __name__ == "__main__":
    main()
