#!/usr/bin/env python3
"""
Progress Tracking System for NBA MCP Synthesis

Tracks implementation progress of recommendations across:
- Priority tiers (CRITICAL, HIGH, MEDIUM, LOW)
- Categories (Quick Win, Strategic Project, etc.)
- Individual recommendations
- Books analyzed

Features:
- Git integration to detect implementations
- Manual status updates
- Progress reports and dashboards
- Visual progress bars
- Completion statistics

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-21
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import re

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ImplementationStatus:
    """Status of a recommendation implementation"""

    recommendation_id: str
    title: str
    status: str  # not_started, in_progress, completed, blocked
    started_date: Optional[str] = None
    completed_date: Optional[str] = None
    assigned_to: Optional[str] = None
    git_commits: List[str] = None
    files_created: List[str] = None
    progress_percentage: int = 0
    notes: str = ""

    def __post_init__(self):
        if self.git_commits is None:
            self.git_commits = []
        if self.files_created is None:
            self.files_created = []


class ProgressTracker:
    """
    Tracks implementation progress of recommendations.

    Features:
    - Load recommendations from JSON
    - Track status per recommendation
    - Detect implementations via git commits
    - Generate progress reports
    - Visualize completion statistics
    """

    # Status values
    STATUS_NOT_STARTED = "not_started"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_BLOCKED = "blocked"

    def __init__(
        self,
        recommendations_file: str,
        progress_file: str = "analysis_results/progress_tracker.json",
        project_root: str = ".",
    ):
        """
        Initialize progress tracker.

        Args:
            recommendations_file: Path to recommendations JSON
            progress_file: Path to save progress data
            project_root: Root directory of project (for git integration)
        """
        self.recommendations_file = Path(recommendations_file)
        self.progress_file = Path(progress_file)
        self.project_root = Path(project_root)

        # Load recommendations
        self.recommendations = self._load_recommendations()
        logger.info(f"📊 Loaded {len(self.recommendations)} recommendations")

        # Load or initialize progress
        self.progress = self._load_progress()
        logger.info(f"📈 Tracking progress for {len(self.progress)} items")

    def _load_recommendations(self) -> List[Dict]:
        """Load recommendations from JSON file"""
        with open(self.recommendations_file, "r") as f:
            data = json.load(f)

        # Handle different file structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "recommendations" in data:
                return data["recommendations"]
            else:
                return [data]
        return []

    def _load_progress(self) -> Dict[str, ImplementationStatus]:
        """Load progress tracking data"""
        if not self.progress_file.exists():
            logger.info("📝 Creating new progress tracking file")
            return self._initialize_progress()

        with open(self.progress_file, "r") as f:
            data = json.load(f)

        # Convert to ImplementationStatus objects
        progress = {}
        for rec_id, status_dict in data.items():
            progress[rec_id] = ImplementationStatus(**status_dict)

        return progress

    def _initialize_progress(self) -> Dict[str, ImplementationStatus]:
        """Initialize progress tracking for all recommendations"""
        progress = {}

        for rec in self.recommendations:
            rec_id = self._get_recommendation_id(rec)
            title = rec.get("title", "Untitled")

            progress[rec_id] = ImplementationStatus(
                recommendation_id=rec_id, title=title, status=self.STATUS_NOT_STARTED
            )

        return progress

    def _get_recommendation_id(self, rec: Dict) -> str:
        """Get unique ID for recommendation"""
        # Try existing ID fields
        for id_field in ["id", "recommendation_id", "title"]:
            if id_field in rec and rec[id_field]:
                return str(rec[id_field])

        # Fallback: use title
        return rec.get("title", "unknown")

    def save_progress(self):
        """Save progress data to file"""
        # Convert to dict
        data = {rec_id: asdict(status) for rec_id, status in self.progress.items()}

        # Ensure directory exists
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        # Save
        with open(self.progress_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Progress saved: {self.progress_file}")

    def update_status(
        self,
        recommendation_id: str,
        status: str,
        notes: str = "",
        assigned_to: Optional[str] = None,
    ):
        """
        Update implementation status of a recommendation.

        Args:
            recommendation_id: ID of recommendation
            status: New status (not_started, in_progress, completed, blocked)
            notes: Optional notes about the update
            assigned_to: Optional person assigned
        """
        if recommendation_id not in self.progress:
            logger.warning(f"⚠️  Unknown recommendation ID: {recommendation_id}")
            return

        impl_status = self.progress[recommendation_id]
        old_status = impl_status.status
        impl_status.status = status

        # Update dates
        now = datetime.now().isoformat()
        if status == self.STATUS_IN_PROGRESS and old_status == self.STATUS_NOT_STARTED:
            impl_status.started_date = now
        elif status == self.STATUS_COMPLETED:
            impl_status.completed_date = now
            impl_status.progress_percentage = 100

        # Update other fields
        if notes:
            impl_status.notes = notes
        if assigned_to:
            impl_status.assigned_to = assigned_to

        logger.info(f"📝 Updated {recommendation_id}: {old_status} → {status}")

        # Auto-save
        self.save_progress()

    def detect_implementations_from_git(self, since_date: Optional[str] = None):
        """
        Detect implementations from git commit messages.

        Searches for commit messages that reference recommendation titles.

        Args:
            since_date: Only check commits since this date (e.g., "2025-10-01")
        """
        logger.info("🔍 Detecting implementations from git commits...")

        try:
            # Build git log command
            cmd = ["git", "log", "--all", "--oneline"]
            if since_date:
                cmd.extend(["--since", since_date])

            # Run git log
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                logger.warning("⚠️  Git not available or not a git repository")
                return

            commits = result.stdout.strip().split("\n")
            logger.info(f"   Found {len(commits)} commits to analyze")

            # Check each recommendation
            updates = 0
            for rec_id, impl_status in self.progress.items():
                title = impl_status.title.lower()

                # Search for commits mentioning this recommendation
                matching_commits = []
                for commit in commits:
                    if any(word in commit.lower() for word in title.split()[:3]):
                        matching_commits.append(commit.split()[0])  # Get commit hash

                if matching_commits:
                    impl_status.git_commits = matching_commits

                    # If completed in git but not marked completed, suggest update
                    if impl_status.status == self.STATUS_NOT_STARTED:
                        logger.info(f"   💡 Detected activity for: {impl_status.title}")
                        logger.info(f"      Commits: {len(matching_commits)}")
                        impl_status.status = self.STATUS_IN_PROGRESS
                        updates += 1

            logger.info(f"✅ Updated {updates} recommendations based on git history")

            # Auto-save
            if updates > 0:
                self.save_progress()

        except Exception as e:
            logger.warning(f"⚠️  Failed to detect from git: {e}")

    def detect_implementations_from_files(self, search_dirs: List[str] = None):
        """
        Detect implementations by checking for generated code files.

        Args:
            search_dirs: Directories to search (default: ["scripts/", "generated_code/"])
        """
        if search_dirs is None:
            search_dirs = ["scripts/", "generated_code/"]

        logger.info("🔍 Detecting implementations from file system...")

        updates = 0
        for rec_id, impl_status in self.progress.items():
            # Generate expected module name from title
            module_name = self._title_to_module_name(impl_status.title)

            # Search for files
            found_files = []
            for search_dir in search_dirs:
                search_path = self.project_root / search_dir
                if not search_path.exists():
                    continue

                # Look for Python files matching module name
                for py_file in search_path.glob(f"**/{module_name}*.py"):
                    found_files.append(str(py_file.relative_to(self.project_root)))

            if found_files:
                impl_status.files_created = found_files

                # Update status if files exist
                if impl_status.status == self.STATUS_NOT_STARTED:
                    impl_status.status = self.STATUS_IN_PROGRESS
                    logger.info(f"   💡 Found files for: {impl_status.title}")
                    logger.info(f"      Files: {len(found_files)}")
                    updates += 1

        logger.info(f"✅ Updated {updates} recommendations based on file system")

        if updates > 0:
            self.save_progress()

    def _title_to_module_name(self, title: str) -> str:
        """Convert title to module name (same logic as code generator)"""
        name = re.sub(r"[^\w\s]", "", title.lower())
        name = re.sub(r"\s+", "_", name)
        return name[:50]

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall progress statistics"""
        total = len(self.progress)
        if total == 0:
            return {}

        # Count by status
        by_status = {
            self.STATUS_NOT_STARTED: 0,
            self.STATUS_IN_PROGRESS: 0,
            self.STATUS_COMPLETED: 0,
            self.STATUS_BLOCKED: 0,
        }

        for impl_status in self.progress.values():
            by_status[impl_status.status] = by_status.get(impl_status.status, 0) + 1

        # Calculate percentages
        completed_pct = (by_status[self.STATUS_COMPLETED] / total) * 100
        in_progress_pct = (by_status[self.STATUS_IN_PROGRESS] / total) * 100
        not_started_pct = (by_status[self.STATUS_NOT_STARTED] / total) * 100
        blocked_pct = (by_status[self.STATUS_BLOCKED] / total) * 100

        return {
            "total_recommendations": total,
            "by_status": by_status,
            "percentages": {
                "completed": round(completed_pct, 1),
                "in_progress": round(in_progress_pct, 1),
                "not_started": round(not_started_pct, 1),
                "blocked": round(blocked_pct, 1),
            },
            "completion_rate": round(completed_pct, 1),
        }

    def get_statistics_by_priority(self) -> Dict[str, Dict]:
        """Get progress statistics grouped by priority tier"""
        # Group by priority
        by_priority = {}

        for rec in self.recommendations:
            rec_id = self._get_recommendation_id(rec)
            if rec_id not in self.progress:
                continue

            impl_status = self.progress[rec_id]

            # Get priority from recommendation
            priority_score = rec.get("priority_score", {})
            tier = priority_score.get("tier", "MEDIUM")

            if tier not in by_priority:
                by_priority[tier] = {
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "not_started": 0,
                    "blocked": 0,
                }

            by_priority[tier]["total"] += 1
            by_priority[tier][impl_status.status] += 1

        # Calculate percentages
        for tier, stats in by_priority.items():
            total = stats["total"]
            stats["completion_rate"] = (
                round((stats["completed"] / total) * 100, 1) if total > 0 else 0
            )

        return by_priority

    def get_statistics_by_category(self) -> Dict[str, Dict]:
        """Get progress statistics grouped by category"""
        by_category = {}

        for rec in self.recommendations:
            rec_id = self._get_recommendation_id(rec)
            if rec_id not in self.progress:
                continue

            impl_status = self.progress[rec_id]

            # Get category from recommendation
            priority_score = rec.get("priority_score", {})
            category = priority_score.get("category", "Unknown")

            if category not in by_category:
                by_category[category] = {
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "not_started": 0,
                    "blocked": 0,
                }

            by_category[category]["total"] += 1
            by_category[category][impl_status.status] += 1

        # Calculate percentages
        for category, stats in by_category.items():
            total = stats["total"]
            stats["completion_rate"] = (
                round((stats["completed"] / total) * 100, 1) if total > 0 else 0
            )

        return by_category

    def generate_progress_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate markdown progress report.

        Args:
            output_file: Optional file to save report

        Returns:
            Markdown report string
        """
        stats = self.get_statistics()
        by_priority = self.get_statistics_by_priority()
        by_category = self.get_statistics_by_category()

        lines = [
            "# Implementation Progress Report",
            "",
            f"**Generated**: {datetime.now().isoformat()}",
            f"**Total Recommendations**: {stats['total_recommendations']}",
            "",
            "---",
            "",
        ]

        # Overall progress
        lines.extend(
            [
                "## 📊 Overall Progress",
                "",
                self._generate_progress_bar(stats["completion_rate"], "Completed"),
                "",
                f"- ✅ **Completed**: {stats['by_status']['completed']} ({stats['percentages']['completed']}%)",
                f"- 🔄 **In Progress**: {stats['by_status']['in_progress']} ({stats['percentages']['in_progress']}%)",
                f"- ⏸️  **Not Started**: {stats['by_status']['not_started']} ({stats['percentages']['not_started']}%)",
                f"- ⛔ **Blocked**: {stats['by_status']['blocked']} ({stats['percentages']['blocked']}%)",
                "",
            ]
        )

        # Progress by priority
        lines.extend(
            [
                "## 🎯 Progress by Priority Tier",
                "",
            ]
        )

        for tier in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if tier in by_priority:
                stats = by_priority[tier]
                lines.append(f"### {tier}")
                lines.append("")
                lines.append(
                    self._generate_progress_bar(stats["completion_rate"], tier)
                )
                lines.append("")
                lines.append(f"- Total: {stats['total']}")
                lines.append(
                    f"- Completed: {stats['completed']} ({stats['completion_rate']}%)"
                )
                lines.append(f"- In Progress: {stats['in_progress']}")
                lines.append("")

        # Progress by category
        lines.extend(
            [
                "## 📋 Progress by Category",
                "",
            ]
        )

        for category in sorted(by_category.keys()):
            stats = by_category[category]
            lines.append(f"### {category}")
            lines.append("")
            lines.append(
                self._generate_progress_bar(stats["completion_rate"], category)
            )
            lines.append("")
            lines.append(f"- Total: {stats['total']}")
            lines.append(
                f"- Completed: {stats['completed']} ({stats['completion_rate']}%)"
            )
            lines.append(f"- In Progress: {stats['in_progress']}")
            lines.append("")

        # Recently completed
        recently_completed = self._get_recently_completed(limit=10)
        if recently_completed:
            lines.extend(
                [
                    "## ✅ Recently Completed",
                    "",
                ]
            )

            for impl_status in recently_completed:
                lines.append(f"- **{impl_status.title}**")
                if impl_status.completed_date:
                    lines.append(f"  - Completed: {impl_status.completed_date[:10]}")
                if impl_status.git_commits:
                    lines.append(f"  - Commits: {len(impl_status.git_commits)}")
                lines.append("")

        # In progress
        in_progress = self._get_in_progress()
        if in_progress:
            lines.extend(
                [
                    "## 🔄 Currently In Progress",
                    "",
                ]
            )

            for impl_status in in_progress[:20]:  # Top 20
                lines.append(f"- **{impl_status.title}**")
                if impl_status.started_date:
                    lines.append(f"  - Started: {impl_status.started_date[:10]}")
                if impl_status.assigned_to:
                    lines.append(f"  - Assigned: {impl_status.assigned_to}")
                if impl_status.progress_percentage > 0:
                    lines.append(f"  - Progress: {impl_status.progress_percentage}%")
                lines.append("")

        # Blocked
        blocked = self._get_blocked()
        if blocked:
            lines.extend(
                [
                    "## ⛔ Blocked Recommendations",
                    "",
                ]
            )

            for impl_status in blocked:
                lines.append(f"- **{impl_status.title}**")
                if impl_status.notes:
                    lines.append(f"  - Notes: {impl_status.notes}")
                lines.append("")

        report = "\n".join(lines)

        # Save to file if specified
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(report)
            logger.info(f"💾 Progress report saved: {output_file}")

        return report

    def _generate_progress_bar(self, percentage: float, label: str = "") -> str:
        """Generate ASCII progress bar"""
        width = 40
        filled = int(width * percentage / 100)
        empty = width - filled

        bar = "█" * filled + "░" * empty
        return f"{label}: [{bar}] {percentage:.1f}%"

    def _get_recently_completed(self, limit: int = 10) -> List[ImplementationStatus]:
        """Get recently completed recommendations"""
        completed = [
            status
            for status in self.progress.values()
            if status.status == self.STATUS_COMPLETED and status.completed_date
        ]

        # Sort by completion date (most recent first)
        completed.sort(key=lambda x: x.completed_date or "", reverse=True)

        return completed[:limit]

    def _get_in_progress(self) -> List[ImplementationStatus]:
        """Get recommendations currently in progress"""
        return [
            status
            for status in self.progress.values()
            if status.status == self.STATUS_IN_PROGRESS
        ]

    def _get_blocked(self) -> List[ImplementationStatus]:
        """Get blocked recommendations"""
        return [
            status
            for status in self.progress.values()
            if status.status == self.STATUS_BLOCKED
        ]


def main():
    """CLI for progress tracking"""
    import argparse

    parser = argparse.ArgumentParser(description="Track implementation progress")
    parser.add_argument(
        "--recommendations", required=True, help="Path to recommendations JSON"
    )
    parser.add_argument(
        "--progress-file",
        default="analysis_results/progress_tracker.json",
        help="Path to progress tracking file",
    )
    parser.add_argument(
        "--detect-git", action="store_true", help="Detect implementations from git"
    )
    parser.add_argument(
        "--detect-files", action="store_true", help="Detect implementations from files"
    )
    parser.add_argument("--report", help="Generate progress report (output file path)")
    parser.add_argument(
        "--update-status",
        nargs=3,
        metavar=("ID", "STATUS", "NOTES"),
        help="Update status: ID STATUS NOTES",
    )

    args = parser.parse_args()

    # Initialize tracker
    tracker = ProgressTracker(
        recommendations_file=args.recommendations, progress_file=args.progress_file
    )

    # Detect implementations
    if args.detect_git:
        tracker.detect_implementations_from_git()

    if args.detect_files:
        tracker.detect_implementations_from_files()

    # Update status if requested
    if args.update_status:
        rec_id, status, notes = args.update_status
        tracker.update_status(rec_id, status, notes)

    # Generate report
    if args.report:
        tracker.generate_progress_report(args.report)
        print(f"✅ Progress report generated: {args.report}")
    else:
        # Print statistics
        stats = tracker.get_statistics()
        print("\n" + "=" * 60)
        print("IMPLEMENTATION PROGRESS")
        print("=" * 60 + "\n")

        print(f"Total Recommendations: {stats['total_recommendations']}")
        print(f"Completion Rate: {stats['completion_rate']}%\n")

        print(
            f"✅ Completed: {stats['by_status']['completed']} ({stats['percentages']['completed']}%)"
        )
        print(
            f"🔄 In Progress: {stats['by_status']['in_progress']} ({stats['percentages']['in_progress']}%)"
        )
        print(
            f"⏸️  Not Started: {stats['by_status']['not_started']} ({stats['percentages']['not_started']}%)"
        )
        print(
            f"⛔ Blocked: {stats['by_status']['blocked']} ({stats['percentages']['blocked']}%)"
        )
        print()


if __name__ == "__main__":
    main()
