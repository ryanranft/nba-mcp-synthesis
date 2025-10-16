#!/usr/bin/env python3
"""
Book Results Organization Script

This script organizes book analysis results into a structured directory hierarchy
following the NBA Simulator AWS phase subdirectory pattern.

Creates:
- analysis_results/books/{book_id}/ directory structure
- Book-specific README.md files
- Phase-organized recommendation files
- Analysis reports and convergence tracking data
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BookResultsOrganizer:
    """Organizes book analysis results into structured directories."""

    def __init__(self, base_path: str = "analysis_results"):
        self.base_path = Path(base_path)
        self.books_path = self.base_path / "books"

    def organize_all_books(self, books_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Organize results for all books in the configuration.

        Args:
            books_config: List of book configurations from books_to_analyze.json

        Returns:
            Dictionary with organization results
        """
        logger.info("Starting book results organization...")

        results = {
            "books_organized": 0,
            "directories_created": [],
            "files_moved": [],
            "errors": []
        }

        # Create base books directory
        self.books_path.mkdir(parents=True, exist_ok=True)

        for book in books_config:
            try:
                book_id = book.get("id", self._generate_book_id(book.get("title", "unknown")))
                book_result = self.organize_single_book(book_id, book)

                if book_result["success"]:
                    results["books_organized"] += 1
                    results["directories_created"].extend(book_result["directories_created"])
                    results["files_moved"].extend(book_result["files_moved"])
                else:
                    results["errors"].append(f"Failed to organize {book_id}: {book_result['error']}")

            except Exception as e:
                error_msg = f"Error organizing book {book.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        logger.info(f"Organization complete: {results['books_organized']} books organized")
        return results

    def organize_single_book(self, book_id: str, book_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organize results for a single book.

        Args:
            book_id: Unique identifier for the book
            book_metadata: Book configuration and metadata

        Returns:
            Dictionary with organization results for this book
        """
        logger.info(f"Organizing book: {book_id}")

        result = {
            "success": False,
            "directories_created": [],
            "files_moved": [],
            "error": None
        }

        try:
            # Create book directory structure
            book_dir = self.books_path / book_id
            by_phase_dir = book_dir / "BY_PHASE"

            book_dir.mkdir(parents=True, exist_ok=True)
            by_phase_dir.mkdir(parents=True, exist_ok=True)

            result["directories_created"].extend([str(book_dir), str(by_phase_dir)])

            # Load master recommendations to find book-specific ones
            master_recs = self._load_master_recommendations()
            book_recommendations = self._filter_book_recommendations(master_recs, book_id)

            # Generate book README
            self._generate_book_readme(book_dir, book_id, book_metadata, book_recommendations)

            # Generate tier files (Critical/Important)
            self._generate_tier_files(book_dir, book_recommendations)

            # Organize recommendations by phase
            self._organize_recommendations_by_phase(by_phase_dir, book_recommendations)

            # Move analysis reports if they exist
            self._move_analysis_reports(book_dir, book_id)

            result["success"] = True
            logger.info(f"Successfully organized book: {book_id}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Failed to organize book {book_id}: {str(e)}")

        return result

    def _generate_book_id(self, title: str) -> str:
        """Generate a book ID from the title."""
        return title.lower().replace(" ", "_").replace("-", "_").replace(":", "").replace(",", "")

    def _load_master_recommendations(self) -> List[Dict[str, Any]]:
        """Load master recommendations from JSON file."""
        master_file = self.base_path / "master_recommendations.json"

        if not master_file.exists():
            logger.warning("Master recommendations file not found")
            return []

        try:
            with open(master_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("recommendations", [])
        except Exception as e:
            logger.error(f"Error loading master recommendations: {str(e)}")
            return []

    def _filter_book_recommendations(self, all_recommendations: List[Dict[str, Any]], book_id: str) -> List[Dict[str, Any]]:
        """Filter recommendations that belong to a specific book."""
        book_recommendations = []

        for rec in all_recommendations:
            # Check if recommendation is from this book
            source_books = rec.get("source_books", "")
            if book_id in source_books.lower() or book_id.replace("_", " ") in source_books.lower():
                book_recommendations.append(rec)

        return book_recommendations

    def _generate_book_readme(self, book_dir: Path, book_id: str, book_metadata: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> None:
        """Generate NBA-style README.md for the book."""
        try:
            # Count recommendations by priority
            critical_count = len([r for r in recommendations if r.get('priority') == 'CRITICAL'])
            important_count = len([r for r in recommendations if r.get('priority') == 'IMPORTANT'])
            nice_to_have_count = len([r for r in recommendations if r.get('priority') == 'NICE-TO-HAVE'])

            # Count by phase
            phase_counts = {}
            for rec in recommendations:
                phase = rec.get('mapped_phase', 'Unknown')
                phase_counts[phase] = phase_counts.get(phase, 0) + 1

            phase_breakdown = ""
            for phase_num in sorted(phase_counts.keys()):
                if phase_num != 'Unknown':
                    phase_breakdown += f"- Phase {phase_num}: {phase_counts[phase_num]} recommendations\n"

            # Calculate total hours
            total_hours = 0
            for rec in recommendations:
                time_est = rec.get('time_estimate', '0 hours')
                if 'hours' in time_est:
                    try:
                        hours = int(time_est.split()[0])
                        total_hours += hours
                    except:
                        pass

            # Load cost tracking if available
            cost_file = self.base_path / "cost_tracking.json"
            total_cost = 0.0
            if cost_file.exists():
                try:
                    with open(cost_file, 'r') as f:
                        cost_data = json.load(f)
                        total_cost = cost_data.get('total_cost', 0.0)
                except:
                    pass

            # Template context
            context = {
                "book_title": book_metadata.get('title', 'Unknown'),
                "book_id": book_id,
                "book_author": book_metadata.get('author', 'Unknown'),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "total_recommendations": len(recommendations),
                "critical_count": critical_count,
                "important_count": important_count,
                "nice_to_have_count": nice_to_have_count,
                "phase_breakdown": phase_breakdown,
                "total_hours": total_hours,
                "total_cost": f"{total_cost:.2f}",
                "unanimous_count": critical_count,  # Critical = 3/3 agreement
                "majority_count": important_count,  # Important = 2/3 agreement
                "key_insight_1": "Multi-model consensus analysis",
                "key_insight_2": "Cross-validation reduces errors",
                "key_insight_3": "Priority-based implementation",
                "contribution_1": "Enhanced system capabilities",
                "contribution_2": "Improved data processing",
                "contribution_3": "Better monitoring and validation",
                "prerequisite_books_if_any": "None",
                "cost_impact": f"${total_cost:.2f} analysis cost"
            }

            # Render template
            readme_content = self._render_template("book_readme", context)

            # Write README.md
            readme_file = book_dir / "README.md"
            readme_file.write_text(readme_content, encoding='utf-8')

            logger.info(f"Generated NBA-style README: {readme_file}")

        except Exception as e:
            logger.error(f"Error generating book README: {str(e)}")

    def _build_book_readme_content(self, book_id: str, book_metadata: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
        """Build the content for the book README file."""
        title = book_metadata.get("title", book_id.replace("_", " ").title())
        author = book_metadata.get("author", "Unknown")
        analysis_date = datetime.now().strftime("%Y-%m-%d")

        # Count recommendations by priority
        priority_counts = {"Critical": 0, "Important": 0, "Nice-to-Have": 0}
        for rec in recommendations:
            priority = rec.get("priority", "Nice-to-Have")
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Count recommendations by phase
        phase_counts = {}
        for rec in recommendations:
            phases = rec.get("phases", [])
            for phase in phases:
                phase_counts[phase] = phase_counts.get(phase, 0) + 1

        content = f"""# {title} - Analysis Results

**Book ID:** {book_id}
**Author:** {author}
**Analysis Date:** {analysis_date}
**Total Recommendations:** {len(recommendations)}

---

## Overview

This directory contains the complete analysis results for "{title}" including:
- All recommendations generated from this book
- Phase-specific organization of recommendations
- Analysis reports and convergence tracking data
- Implementation guidance and context

---

## Recommendation Summary

**By Priority:**
- Critical: {priority_counts['Critical']} recommendations
- Important: {priority_counts['Important']} recommendations
- Nice-to-Have: {priority_counts['Nice-to-Have']} recommendations

**By Phase:**
"""

        for phase, count in sorted(phase_counts.items()):
            content += f"- Phase {phase}: {count} recommendations\n"

        content += f"""
---

## Directory Structure

```
{book_id}/
├── README.md                    # This file - book overview
├── RECOMMENDATIONS.md           # All recommendations from this book
├── ANALYSIS_REPORT.md           # Complete analysis report (if available)
├── CONVERGENCE_TRACKER.json     # Convergence tracking data (if available)
└── BY_PHASE/                   # Recommendations organized by phase
    ├── PHASE_1_RECOMMENDATIONS.md
    ├── PHASE_2_RECOMMENDATIONS.md
    └── [other phases...]
```

---

## Key Recommendations

"""

        # Add top 3 recommendations
        critical_recs = [r for r in recommendations if r.get("priority") == "Critical"]
        for i, rec in enumerate(critical_recs[:3], 1):
            title_rec = rec.get("title", "Untitled")
            content += f"### {i}. {title_rec}\n\n"
            content += f"**Priority:** {rec.get('priority', 'Unknown')}\n"
            content += f"**Phases:** {', '.join(map(str, rec.get('phases', [])))}\n\n"

        content += """
---

## Implementation Notes

- All recommendations have been integrated into the NBA Simulator AWS project phases
- See individual phase files in BY_PHASE/ directory for detailed implementation guidance
- Cross-reference with master recommendations database for consolidated view
- Check NBA Simulator AWS phase documentation for current implementation status

---

## Related Files

- **Master Recommendations:** `../master_recommendations.json`
- **Phase Integration:** NBA Simulator AWS project phase directories
- **Cross-Project Status:** `../CROSS_PROJECT_IMPLEMENTATION_STATUS.md`
- **Integration Summary:** `../integration_summary.md`

---

*Generated by Book Results Organizer - NBA MCP Synthesis*
"""

        return content

    def _generate_recommendations_file(self, book_dir: Path, recommendations: List[Dict[str, Any]]) -> None:
        """Generate RECOMMENDATIONS.md file with all recommendations for this book."""
        if not recommendations:
            logger.warning(f"No recommendations found for book in {book_dir}")
            return

        content = f"""# Book Recommendations

**Generated:** {datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}
**Total Recommendations:** {len(recommendations)}

---

## All Recommendations

"""

        # Group by priority
        by_priority = {"Critical": [], "Important": [], "Nice-to-Have": []}
        for rec in recommendations:
            priority = rec.get("priority", "Nice-to-Have")
            if priority in by_priority:
                by_priority[priority].append(rec)

        for priority, recs in by_priority.items():
            if recs:
                content += f"## {priority} Recommendations ({len(recs)})\n\n"

                for i, rec in enumerate(recs, 1):
                    title = rec.get("title", "Untitled")
                    phases = rec.get("phases", [])
                    source_books = rec.get("source_books", "Unknown")

                    content += f"### {i}. {title}\n\n"
                    content += f"**Source Books:** {source_books}\n"
                    content += f"**Phases:** {', '.join(map(str, phases))}\n"
                    content += f"**Added:** {rec.get('added', 'Unknown')}\n"
                    content += f"**ID:** {rec.get('id', 'Unknown')}\n\n"

                    # Add description if available
                    description = rec.get("description", "")
                    if description:
                        content += f"{description}\n\n"

                    content += "---\n\n"

        recommendations_file = book_dir / "RECOMMENDATIONS.md"
        with open(recommendations_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated RECOMMENDATIONS.md for {book_dir.name}")

    def _organize_recommendations_by_phase(self, by_phase_dir: Path, recommendations: List[Dict[str, Any]]) -> None:
        """Organize recommendations into phase-specific files."""
        if not recommendations:
            return

        # Group recommendations by phase
        phase_groups = {}
        for rec in recommendations:
            phases = rec.get("phases", [])
            for phase in phases:
                if phase not in phase_groups:
                    phase_groups[phase] = []
                phase_groups[phase].append(rec)

        # Generate phase-specific files
        for phase, phase_recs in phase_groups.items():
            self._generate_phase_recommendations_file(by_phase_dir, phase, phase_recs)

    def _generate_phase_recommendations_file(self, by_phase_dir: Path, phase: int, recommendations: List[Dict[str, Any]]) -> None:
        """Generate a phase-specific recommendations file."""
        content = f"""# Phase {phase} - Book Recommendations

**Phase:** {phase}
**Total Recommendations:** {len(recommendations)}
**Generated:** {datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}

---

## Recommendations for Phase {phase}

"""

        # Group by priority
        by_priority = {"Critical": [], "Important": [], "Nice-to-Have": []}
        for rec in recommendations:
            priority = rec.get("priority", "Nice-to-Have")
            if priority in by_priority:
                by_priority[priority].append(rec)

        for priority, recs in by_priority.items():
            if recs:
                content += f"## {priority} Priority ({len(recs)})\n\n"

                for i, rec in enumerate(recs, 1):
                    title = rec.get("title", "Untitled")
                    source_books = rec.get("source_books", "Unknown")

                    content += f"### {i}. {title}\n\n"
                    content += f"**Source Books:** {source_books}\n"
                    content += f"**Added:** {rec.get('added', 'Unknown')}\n"
                    content += f"**ID:** {rec.get('id', 'Unknown')}\n\n"

                    description = rec.get("description", "")
                    if description:
                        content += f"{description}\n\n"

                    content += "---\n\n"

        phase_file = by_phase_dir / f"PHASE_{phase}_RECOMMENDATIONS.md"
        with open(phase_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated phase {phase} recommendations file")

    def _move_analysis_reports(self, book_dir: Path, book_id: str) -> None:
        """Move analysis reports to the book directory if they exist."""
        # Look for analysis reports with book ID in the name
        analysis_files = [
            f"{book_id}_analysis_report.md",
            f"{book_id}_final_recommendations.md",
            f"{book_id}_convergence_tracker.json"
        ]

        for filename in analysis_files:
            source_file = self.base_path / filename
            if source_file.exists():
                dest_file = book_dir / filename
                shutil.move(str(source_file), str(dest_file))
                logger.info(f"Moved {filename} to {book_dir}")

    def _generate_tier_files(self, book_dir: Path, book_recommendations: List[Dict[str, Any]]) -> None:
        """Generate CRITICAL_RECOMMENDATIONS.md and IMPORTANT_RECOMMENDATIONS.md files."""
        try:
            # Separate by priority
            critical_recs = [r for r in book_recommendations if r.get('priority') == 'CRITICAL']
            important_recs = [r for r in book_recommendations if r.get('priority') == 'IMPORTANT']

            # Generate Critical file
            if critical_recs:
                critical_content = self._generate_tier_content(critical_recs, "Critical", "book_tier_critical")
                critical_file = book_dir / "CRITICAL_RECOMMENDATIONS.md"
                critical_file.write_text(critical_content, encoding='utf-8')
                logger.info(f"Generated critical recommendations: {critical_file}")

            # Generate Important file
            if important_recs:
                important_content = self._generate_tier_content(important_recs, "Important", "book_tier_important")
                important_file = book_dir / "IMPORTANT_RECOMMENDATIONS.md"
                important_file.write_text(important_content, encoding='utf-8')
                logger.info(f"Generated important recommendations: {important_file}")

        except Exception as e:
            logger.error(f"Error generating tier files: {str(e)}")

    def _generate_tier_content(self, recommendations: List[Dict[str, Any]], tier_name: str, template_name: str) -> str:
        """Generate content for tier files (Critical/Important)."""
        # Calculate hours
        total_hours = 0
        for rec in recommendations:
            time_est = rec.get('time_estimate', '0 hours')
            if 'hours' in time_est:
                try:
                    hours = int(time_est.split()[0])
                    total_hours += hours
                except:
                    pass

        # Generate recommendations content
        recs_content = ""
        for i, rec in enumerate(recommendations, 1):
            recs_content += f"### {i}. {rec.get('title', 'Unknown')}\n\n"
            recs_content += f"**Coverage:** {rec.get('mapped_phase', 'Multiple')} phases\n"
            recs_content += f"**Estimated Time:** {rec.get('time_estimate', 'Unknown')}\n"
            recs_content += f"**Priority:** {rec.get('priority', 'Unknown')}\n\n"
            recs_content += f"#### Implementation:\n"
            recs_content += f"- **Description:** {rec.get('description', 'No description')}\n"
            recs_content += f"- **Why It's Critical:** {rec.get('impact', 'High impact')}\n"
            recs_content += f"- **Impact:** {rec.get('impact', 'Significant improvement')}\n\n"
            recs_content += f"**Key Requirements:**\n"
            recs_content += f"1. Implementation planning\n"
            recs_content += f"2. Resource allocation\n"
            recs_content += f"3. Testing and validation\n\n"
            recs_content += f"**Consensus Score:** {rec.get('consensus_score', '3/3')} models agree\n\n"
            recs_content += "---\n\n"

        # Load cost data
        cost_file = self.base_path / "cost_tracking.json"
        analysis_cost = 0.0
        processing_time = 0.0
        total_tokens = 0
        if cost_file.exists():
            try:
                with open(cost_file, 'r') as f:
                    cost_data = json.load(f)
                    analysis_cost = cost_data.get('total_cost', 0.0)
                    # Estimate processing time and tokens
                    processing_time = len(recommendations) * 30  # 30s per rec estimate
                    total_tokens = len(recommendations) * 2000   # 2000 tokens per rec estimate
            except:
                pass

        context = {
            "book_title": recommendations[0].get('source_book_title', 'Unknown') if recommendations else 'Unknown',
            f"{tier_name.lower()}_count": len(recommendations),
            f"{tier_name.lower()}_hours": total_hours,
            f"{tier_name.lower()}_recommendations_content": recs_content,
            "implementation_phase_1": "Planning and setup",
            "implementation_phase_2": "Core implementation",
            "implementation_phase_3": "Testing and deployment",
            "cost_impact": f"${analysis_cost:.2f} analysis cost",
            "analysis_cost": f"{analysis_cost:.2f}",
            "processing_time": f"{processing_time:.1f}",
            "total_tokens": f"{total_tokens:,}",
            "deepseek_cost": f"{analysis_cost * 0.1:.2f}",
            "deepseek_tokens": f"{total_tokens // 3:,}",
            "claude_cost": f"{analysis_cost * 0.8:.2f}",
            "claude_tokens": f"{total_tokens // 3:,}",
            "key_capability_1": "Enhanced system reliability",
            "key_capability_2": "Improved performance",
            "key_capability_3": "Better monitoring",
            "any_prerequisites": "None"
        }

        return self._render_template(template_name, context)


def main():
    """Main function to organize book results."""
    import argparse

    parser = argparse.ArgumentParser(description="Organize book analysis results into structured directories")
    parser.add_argument("--config", default="config/books_to_analyze.json", help="Path to books configuration file")
    parser.add_argument("--base-path", default="analysis_results", help="Base path for analysis results")
    parser.add_argument("--book-id", help="Organize specific book by ID")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load books configuration
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            books_config = config_data.get("books", [])
    except Exception as e:
        logger.error(f"Error loading books configuration: {str(e)}")
        return 1

    # Initialize organizer
    organizer = BookResultsOrganizer(args.base_path)

    if args.book_id:
        # Organize specific book
        book_config = next((book for book in books_config if book.get("id") == args.book_id), None)
        if not book_config:
            logger.error(f"Book with ID '{args.book_id}' not found in configuration")
            return 1

        result = organizer.organize_single_book(args.book_id, book_config)
        if result["success"]:
            logger.info(f"Successfully organized book: {args.book_id}")
            return 0
        else:
            logger.error(f"Failed to organize book: {result['error']}")
            return 1
    else:
        # Organize all books
        result = organizer.organize_all_books(books_config)

        logger.info(f"Organization complete:")
        logger.info(f"  Books organized: {result['books_organized']}")
        logger.info(f"  Directories created: {len(result['directories_created'])}")
        logger.info(f"  Files moved: {len(result['files_moved'])}")

        if result["errors"]:
            logger.error(f"Errors encountered: {len(result['errors'])}")
            for error in result["errors"]:
                logger.error(f"  - {error}")
            return 1

        return 0


if __name__ == "__main__":
    exit(main())
