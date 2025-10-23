#!/usr/bin/env python3
"""
Recommendation Audit & Consolidation Workflow

Finds, audits, and consolidates recommendation files across the project.

This script:
1. Discovers all recommendation files
2. Extracts actionable recommendations from each file
3. Checks completion status (tests, implementations, docs)
4. Documents completed items
5. Adds pending items to master list
6. Archives processed files

Usage:
    python scripts/audit_and_consolidate_recommendations.py
    python scripts/audit_and_consolidate_recommendations.py --dry-run
    python scripts/audit_and_consolidate_recommendations.py --files "MCP_*.md"
    python scripts/audit_and_consolidate_recommendations.py --report-only
"""

import argparse
import re
import yaml
import json
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import subprocess

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class Recommendation:
    """Represents a single recommendation/action item."""

    id: str
    title: str
    source_file: str
    line_number: int
    priority: str  # HIGH, MEDIUM, LOW
    status: str  # COMPLETED, PARTIAL, NOT_STARTED, UNKNOWN
    time_estimate: Optional[str] = None
    success_criteria: List[str] = None
    action_items: List[str] = None
    description: Optional[str] = None
    evidence: Dict[str, List[str]] = None  # tests, implementations, docs found

    def __post_init__(self):
        if self.success_criteria is None:
            self.success_criteria = []
        if self.action_items is None:
            self.action_items = []
        if self.evidence is None:
            self.evidence = {"tests": [], "implementations": [], "docs": []}


class RecommendationAuditor:
    """Audits and consolidates recommendation files."""

    def __init__(self, config_path: Path = None, dry_run: bool = False):
        self.dry_run = dry_run
        self.config = self.load_config(config_path)
        self.recommendations: List[Recommendation] = []
        self.processed_files: List[Path] = []

    def load_config(self, config_path: Optional[Path] = None) -> dict:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = PROJECT_ROOT / ".recommendation-audit.yaml"

        if not config_path.exists():
            print(f"⚠️  Config file not found: {config_path}")
            print("   Using default configuration")
            return self.get_default_config()

        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            return self.get_default_config()

    def get_default_config(self) -> dict:
        """Return default configuration."""
        return {
            "scan_patterns": ["*RECOMMENDATION*.md", "*ACTION*.md"],
            "exclude_dirs": [".git", "node_modules", "venv", "docs/archive"],
            "implementation_dirs": ["mcp_server/", "scripts/"],
            "test_dirs": ["tests/"],
            "docs_dirs": ["docs/"],
            "completion_keywords": ["COMPLETE", "DONE", "IMPLEMENTED"],
            "archive_dir": "docs/archive/2025-10/recommendations/",
            "master_list": "PRIORITY_ACTION_LIST.md",
            "backlog_list": "RECOMMENDATIONS_BACKLOG.md",
            "verbose": True,
        }

    # ========================================================================
    # PHASE 1: DISCOVERY & EXTRACTION
    # ========================================================================

    def find_recommendation_files(
        self, pattern_filter: Optional[str] = None
    ) -> List[Path]:
        """
        Find all recommendation files in project.

        Args:
            pattern_filter: Optional glob pattern to filter files

        Returns:
            List of Path objects for recommendation files
        """
        patterns = self.config.get("scan_patterns", [])
        exclude_dirs = self.config.get("exclude_dirs", [])
        exclude_files = self.config.get("exclude_files", [])

        if pattern_filter:
            patterns = [pattern_filter]

        found_files = []

        for pattern in patterns:
            for file_path in PROJECT_ROOT.rglob(pattern):
                # Skip if in excluded directory
                if any(excluded in str(file_path) for excluded in exclude_dirs):
                    continue

                # Skip if in excluded files list
                if file_path.name in exclude_files:
                    continue

                # Skip if not a file
                if not file_path.is_file():
                    continue

                found_files.append(file_path)

        return sorted(set(found_files))

    def extract_recommendations(self, file_path: Path) -> List[Recommendation]:
        """
        Extract actionable recommendations from a file.

        Args:
            file_path: Path to the recommendation file

        Returns:
            List of Recommendation objects
        """
        try:
            content = file_path.read_text()
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
            return []

        recommendations = []
        lines = content.split("\n")

        # Extract sections that look like recommendations
        for i, line in enumerate(lines):
            # Look for action items
            if self._is_action_item(line):
                rec = self._parse_action_item(line, lines, i, file_path)
                if rec:
                    recommendations.append(rec)

            # Look for numbered recommendations
            elif re.match(r"^\d+\.\s+\*\*(.+?)\*\*", line):
                rec = self._parse_numbered_recommendation(line, lines, i, file_path)
                if rec:
                    recommendations.append(rec)

        return recommendations

    def _is_action_item(self, line: str) -> bool:
        """Check if line contains an action item."""
        action_patterns = self.config.get("action_patterns", [])

        # Check for checkbox
        if re.match(r"^-\s*\[[ xX]\]", line):
            return True

        # Check for imperative verbs
        for pattern in action_patterns:
            if isinstance(pattern, str) and pattern in [
                "Implement",
                "Add",
                "Create",
                "Build",
            ]:
                if line.strip().startswith(pattern):
                    return True

        return False

    def _parse_action_item(
        self, line: str, lines: List[str], line_num: int, file_path: Path
    ) -> Optional[Recommendation]:
        """Parse an action item into a Recommendation."""
        # Extract title
        title = re.sub(r"^-\s*\[[ xX]\]\s*", "", line).strip()
        title = re.sub(r"^\d+\.\s*", "", title).strip()

        if not title or len(title) < 10:
            return None

        # Determine if completed (checked checkbox)
        status = "NOT_STARTED"
        if re.match(r"^-\s*\[[xX]\]", line):
            status = "COMPLETED"

        # Extract priority from surrounding context
        priority = self._extract_priority(lines, line_num)

        # Generate ID
        rec_id = self._generate_id(title, file_path)

        return Recommendation(
            id=rec_id,
            title=title,
            source_file=str(file_path.relative_to(PROJECT_ROOT)),
            line_number=line_num + 1,
            priority=priority,
            status=status,
        )

    def _parse_numbered_recommendation(
        self, line: str, lines: List[str], line_num: int, file_path: Path
    ) -> Optional[Recommendation]:
        """Parse a numbered recommendation (e.g., '1. **Title**')."""
        match = re.match(r"^\d+\.\s+\*\*(.+?)\*\*", line)
        if not match:
            return None

        title = match.group(1).strip()

        # Extract description and details from following lines
        description = []
        action_items = []
        success_criteria = []

        for i in range(line_num + 1, min(line_num + 20, len(lines))):
            next_line = lines[i].strip()

            # Stop at next numbered item or major heading
            if re.match(r"^\d+\.\s+\*\*", next_line) or next_line.startswith("## "):
                break

            # Extract action items
            if next_line.startswith("- [ ]") or next_line.startswith("- [x]"):
                action_items.append(next_line)

            # Extract success criteria
            elif "Success Criteria:" in next_line or next_line.startswith("- ✅"):
                success_criteria.append(next_line)

            # Extract description
            elif next_line and not next_line.startswith("#"):
                description.append(next_line)

        priority = self._extract_priority(lines, line_num)
        rec_id = self._generate_id(title, file_path)

        return Recommendation(
            id=rec_id,
            title=title,
            source_file=str(file_path.relative_to(PROJECT_ROOT)),
            line_number=line_num + 1,
            priority=priority,
            status="UNKNOWN",
            description=" ".join(description[:3]) if description else None,
            action_items=action_items,
            success_criteria=success_criteria,
        )

    def _extract_priority(self, lines: List[str], line_num: int) -> str:
        """Extract priority from surrounding context."""
        # Check current line and previous 5 lines for priority keywords
        search_lines = lines[max(0, line_num - 5) : line_num + 1]
        content = " ".join(search_lines).upper()

        priority_keywords = self.config.get("priority_keywords", {})

        if any(kw in content for kw in priority_keywords.get("high", [])):
            return "HIGH"
        elif any(kw in content for kw in priority_keywords.get("medium", [])):
            return "MEDIUM"
        elif any(kw in content for kw in priority_keywords.get("low", [])):
            return "LOW"

        return "MEDIUM"  # Default

    def _generate_id(self, title: str, file_path: Path) -> str:
        """Generate a unique ID for a recommendation."""
        # Extract keywords from title
        keywords = re.findall(r"\b\w+\b", title.lower())
        key_part = "_".join(keywords[:3])

        # Use file name
        file_part = file_path.stem.lower()[:15]

        # Create ID
        rec_id = f"rec_{file_part}_{key_part}"[:50]

        return rec_id

    # ========================================================================
    # PHASE 2: COMPLETION DETECTION
    # ========================================================================

    def check_completion_status(self, rec: Recommendation) -> str:
        """
        Determine if a recommendation was completed.

        Returns:
            Status string: COMPLETED, PARTIAL, IN_PROGRESS, NOT_STARTED
        """
        # If already marked as completed from checkbox, verify it
        if rec.status == "COMPLETED":
            return "COMPLETED"

        # Extract keywords from title for searching
        keywords = self._extract_keywords(rec.title)

        if not keywords:
            return "UNKNOWN"

        # Search for evidence
        tests_found = self._search_for_tests(keywords)
        impl_found = self._search_for_implementations(keywords)
        docs_found = self._search_for_documentation(keywords)

        # Update evidence
        rec.evidence = {
            "tests": tests_found,
            "implementations": impl_found,
            "docs": docs_found,
        }

        # Determine status based on evidence
        if tests_found and impl_found and docs_found:
            return "COMPLETED"
        elif impl_found and (tests_found or docs_found):
            return "PARTIAL"
        elif impl_found:
            return "IN_PROGRESS"
        else:
            return "NOT_STARTED"

    def _extract_keywords(self, title: str) -> List[str]:
        """Extract searchable keywords from title."""
        # Clean title
        title = title.lower()
        title = re.sub(r"[^\w\s]", " ", title)

        # Remove common words
        stop_words = {
            "add",
            "implement",
            "create",
            "build",
            "setup",
            "for",
            "the",
            "a",
            "an",
        }
        keywords = [w for w in title.split() if w not in stop_words and len(w) > 3]

        return keywords[:5]  # Top 5 keywords

    def _search_for_tests(self, keywords: List[str]) -> List[str]:
        """Search for test files related to keywords."""
        test_dirs = self.config.get("test_dirs", ["tests/"])
        found_tests = []

        for keyword in keywords:
            for test_dir in test_dirs:
                test_path = PROJECT_ROOT / test_dir
                if not test_path.exists():
                    continue

                # Search for test files
                for test_file in test_path.rglob(f"*{keyword}*.py"):
                    found_tests.append(str(test_file.relative_to(PROJECT_ROOT)))

                for test_file in test_path.rglob(f"test_*{keyword}*.py"):
                    found_tests.append(str(test_file.relative_to(PROJECT_ROOT)))

        return sorted(set(found_tests))

    def _search_for_implementations(self, keywords: List[str]) -> List[str]:
        """Search for implementation files related to keywords."""
        impl_dirs = self.config.get("implementation_dirs", ["mcp_server/", "scripts/"])
        found_impls = []

        for keyword in keywords:
            for impl_dir in impl_dirs:
                impl_path = PROJECT_ROOT / impl_dir
                if not impl_path.exists():
                    continue

                # Search for implementation files
                for impl_file in impl_path.rglob(f"*{keyword}*.py"):
                    found_impls.append(str(impl_file.relative_to(PROJECT_ROOT)))

        return sorted(set(found_impls))

    def _search_for_documentation(self, keywords: List[str]) -> List[str]:
        """Search for documentation related to keywords."""
        docs_dirs = self.config.get("docs_dirs", ["docs/"])
        completion_keywords = self.config.get("completion_keywords", [])
        found_docs = []

        for keyword in keywords:
            for docs_dir in docs_dirs:
                docs_path = PROJECT_ROOT / docs_dir
                if not docs_path.exists():
                    continue

                # Search for docs with keyword and completion indicator
                for doc_file in docs_path.rglob(f"*{keyword}*.md"):
                    # Check if doc indicates completion
                    for comp_kw in completion_keywords:
                        if comp_kw.lower() in doc_file.name.lower():
                            found_docs.append(str(doc_file.relative_to(PROJECT_ROOT)))
                            break

        return sorted(set(found_docs))

    # ========================================================================
    # PHASE 3: DOCUMENTATION GENERATION
    # ========================================================================

    def generate_completion_docs(self, completed: List[Recommendation]):
        """Generate documentation for completed recommendations."""
        if not completed:
            print("No completed recommendations to document.")
            return

        report_path = PROJECT_ROOT / self.config.get(
            "completion_report", "COMPLETION_REPORT.md"
        )

        if self.dry_run:
            print(f"[DRY RUN] Would create completion report: {report_path}")
            return

        # Create report
        report_content = self._create_completion_report(completed)

        # Ensure directory exists
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Write report
        report_path.write_text(report_content)
        print(f"✅ Created completion report: {report_path}")

    def _create_completion_report(self, completed: List[Recommendation]) -> str:
        """Create markdown content for completion report."""
        report = [
            "# Recommendations Completion Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Completed:** {len(completed)}",
            "",
            "---",
            "",
            "## Completed Recommendations",
            "",
        ]

        for rec in sorted(completed, key=lambda r: r.priority):
            report.extend(
                [
                    f"### {rec.title}",
                    "",
                    f"**ID:** `{rec.id}`",
                    f"**Priority:** {rec.priority}",
                    f"**Source:** {rec.source_file}:{rec.line_number}",
                    "",
                ]
            )

            # Add evidence
            if rec.evidence["tests"]:
                report.append("**Tests:**")
                for test in rec.evidence["tests"]:
                    report.append(f"- ✅ {test}")
                report.append("")

            if rec.evidence["implementations"]:
                report.append("**Implementations:**")
                for impl in rec.evidence["implementations"]:
                    report.append(f"- ✅ {impl}")
                report.append("")

            if rec.evidence["docs"]:
                report.append("**Documentation:**")
                for doc in rec.evidence["docs"]:
                    report.append(f"- ✅ {doc}")
                report.append("")

            report.append("---")
            report.append("")

        return "\n".join(report)

    def update_master_list(self, pending: List[Recommendation]):
        """Add pending recommendations to master list."""
        if not pending:
            print("No pending recommendations to add.")
            return

        backlog_path = PROJECT_ROOT / self.config.get(
            "backlog_list", "RECOMMENDATIONS_BACKLOG.md"
        )

        if self.dry_run:
            print(f"[DRY RUN] Would create backlog: {backlog_path}")
            print(f"[DRY RUN] Would add {len(pending)} pending recommendations")
            return

        # Create backlog
        backlog_content = self._create_backlog(pending)
        backlog_path.write_text(backlog_content)
        print(f"✅ Created backlog: {backlog_path}")

    def _create_backlog(self, pending: List[Recommendation]) -> str:
        """Create markdown content for backlog."""
        # Group by status and priority
        by_status = defaultdict(list)
        for rec in pending:
            by_status[rec.status].append(rec)

        backlog = [
            "# Recommendations Backlog",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Pending:** {len(pending)}",
            "",
            "---",
            "",
        ]

        # Not started (high priority first)
        if by_status["NOT_STARTED"]:
            backlog.extend(["## Not Started", ""])
            for rec in sorted(by_status["NOT_STARTED"], key=lambda r: r.priority):
                backlog.append(f"- [ ] **{rec.title}** ({rec.priority})")
                backlog.append(f"  - Source: {rec.source_file}:{rec.line_number}")
                backlog.append("")

        # Partial
        if by_status["PARTIAL"]:
            backlog.extend(["## Partial Implementations", ""])
            for rec in by_status["PARTIAL"]:
                backlog.append(f"- [~] **{rec.title}** ({rec.priority})")
                backlog.append(f"  - Source: {rec.source_file}:{rec.line_number}")
                if rec.evidence["implementations"]:
                    backlog.append(
                        f"  - Implementation: {rec.evidence['implementations'][0]}"
                    )
                backlog.append("")

        # In progress
        if by_status["IN_PROGRESS"]:
            backlog.extend(["## In Progress", ""])
            for rec in by_status["IN_PROGRESS"]:
                backlog.append(f"- [~] **{rec.title}** ({rec.priority})")
                backlog.append(f"  - Source: {rec.source_file}:{rec.line_number}")
                backlog.append("")

        return "\n".join(backlog)

    # ========================================================================
    # PHASE 4: ARCHIVE & CLEANUP
    # ========================================================================

    def archive_files(self, files: List[Path]):
        """Archive processed recommendation files."""
        if not files:
            print("No files to archive.")
            return

        archive_dir = PROJECT_ROOT / self.config.get(
            "archive_dir", "docs/archive/recommendations/"
        )

        if self.dry_run:
            print(f"[DRY RUN] Would archive {len(files)} files to: {archive_dir}")
            for file_path in files:
                print(f"  - {file_path}")
            return

        # Create archive directory
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Create backup if configured
        if self.config.get("create_backup", True):
            self._create_backup(files)

        # Move files
        for file_path in files:
            try:
                dest_path = archive_dir / file_path.name

                # If file exists, add timestamp
                if dest_path.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest_path = (
                        archive_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                    )

                # Add archive header
                self._add_archive_header(file_path, dest_path)

                print(
                    f"✅ Archived: {file_path.name} → {dest_path.relative_to(PROJECT_ROOT)}"
                )
            except Exception as e:
                print(f"❌ Error archiving {file_path.name}: {e}")

    def _add_archive_header(self, source: Path, dest: Path):
        """Add archive metadata header to file before moving."""
        try:
            content = source.read_text()

            # Count recommendations
            rec_count = len(
                [
                    r
                    for r in self.recommendations
                    if r.source_file == str(source.relative_to(PROJECT_ROOT))
                ]
            )
            completed_count = len(
                [
                    r
                    for r in self.recommendations
                    if r.source_file == str(source.relative_to(PROJECT_ROOT))
                    and r.status == "COMPLETED"
                ]
            )

            header = f"""# ARCHIVED: {source.name}

**Archived:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** Fully processed and integrated
**Recommendations Found:** {rec_count}
**Completed:** {completed_count}
**Pending:** {rec_count - completed_count}
**Backlog:** See RECOMMENDATIONS_BACKLOG.md
**Completion Report:** See docs/archive/completed/RECOMMENDATIONS_COMPLETION_REPORT.md

---

"""

            # Write to destination
            dest.write_text(header + content)

            # Remove original
            source.unlink()

        except Exception as e:
            print(f"⚠️  Error adding header to {source.name}: {e}")
            # Fallback: just move the file
            shutil.move(str(source), str(dest))

    def _create_backup(self, files: List[Path]):
        """Create backup of files before archiving."""
        backup_dir = PROJECT_ROOT / self.config.get(
            "backup_dir", "backups/recommendations/"
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / timestamp

        backup_path.mkdir(parents=True, exist_ok=True)

        for file_path in files:
            try:
                shutil.copy2(file_path, backup_path / file_path.name)
            except Exception as e:
                print(f"⚠️  Error backing up {file_path.name}: {e}")

        print(f"✅ Created backup: {backup_path.relative_to(PROJECT_ROOT)}")

    # ========================================================================
    # PHASE 5: MAIN WORKFLOW
    # ========================================================================

    def run(self, pattern_filter: Optional[str] = None, report_only: bool = False):
        """Run the full audit and consolidation workflow."""
        print("=" * 70)
        print("📋 Recommendation Audit & Consolidation Workflow")
        print("=" * 70)
        print()

        # Phase 1: Discovery
        print("Phase 1: Discovering recommendation files...")
        files = self.find_recommendation_files(pattern_filter)
        print(f"  Found {len(files)} recommendation files")
        print()

        if not files:
            print("No recommendation files found. Exiting.")
            return

        # Phase 2: Extraction
        print("Phase 2: Extracting recommendations...")
        for file_path in files:
            recs = self.extract_recommendations(file_path)
            self.recommendations.extend(recs)
            if self.config.get("verbose"):
                print(f"  {file_path.name}: {len(recs)} recommendations")
        print(f"  Total: {len(self.recommendations)} recommendations extracted")
        print()

        # Phase 3: Completion detection
        print("Phase 3: Checking completion status...")
        for rec in self.recommendations:
            rec.status = self.check_completion_status(rec)
        print()

        # Categorize
        completed = [r for r in self.recommendations if r.status == "COMPLETED"]
        partial = [r for r in self.recommendations if r.status == "PARTIAL"]
        in_progress = [r for r in self.recommendations if r.status == "IN_PROGRESS"]
        not_started = [r for r in self.recommendations if r.status == "NOT_STARTED"]

        print("📊 Status Summary:")
        print(f"  ✅ Completed: {len(completed)}")
        print(f"  🟡 Partial: {len(partial)}")
        print(f"  🔄 In Progress: {len(in_progress)}")
        print(f"  🔴 Not Started: {len(not_started)}")
        print()

        if report_only:
            print("Report-only mode. Skipping documentation and archiving.")
            self._print_detailed_report(completed, partial, in_progress, not_started)
            return

        # Phase 4: Documentation
        print("Phase 4: Generating documentation...")
        self.generate_completion_docs(completed)
        self.update_master_list(partial + in_progress + not_started)
        print()

        # Phase 5: Archiving
        print("Phase 5: Archiving processed files...")
        self.archive_files(files)
        print()

        # Final report
        print("=" * 70)
        print("✅ Workflow Complete!")
        print("=" * 70)
        self._print_detailed_report(completed, partial, in_progress, not_started)

    def _print_detailed_report(
        self,
        completed: List[Recommendation],
        partial: List[Recommendation],
        in_progress: List[Recommendation],
        not_started: List[Recommendation],
    ):
        """Print detailed report of findings."""
        print()
        print("=" * 70)
        print("📊 Detailed Report")
        print("=" * 70)
        print()

        if completed:
            print("✅ COMPLETED:")
            for rec in completed[:5]:
                print(f"  • {rec.title}")
                if rec.evidence["tests"]:
                    print(f"    Tests: {len(rec.evidence['tests'])}")
                if rec.evidence["implementations"]:
                    print(
                        f"    Implementations: {len(rec.evidence['implementations'])}"
                    )
            if len(completed) > 5:
                print(f"  ... and {len(completed) - 5} more")
            print()

        if partial:
            print("🟡 PARTIAL:")
            for rec in partial[:5]:
                print(f"  • {rec.title}")
                if rec.evidence["implementations"]:
                    print(f"    Has: {rec.evidence['implementations'][0]}")
                    print(f"    Missing: tests or docs")
            if len(partial) > 5:
                print(f"  ... and {len(partial) - 5} more")
            print()

        if not_started:
            print("🔴 NOT STARTED (High Priority):")
            high_priority = [r for r in not_started if r.priority == "HIGH"]
            for rec in high_priority[:5]:
                print(f"  • {rec.title}")
            if len(high_priority) > 5:
                print(f"  ... and {len(high_priority) - 5} more")
            print()

        print("📁 Next Steps:")
        print(f"  1. Review: RECOMMENDATIONS_BACKLOG.md")
        print(f"  2. Implement: High priority items first")
        print(f"  3. Document: Update completion report as you go")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Audit and consolidate recommendation files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/audit_and_consolidate_recommendations.py
  python scripts/audit_and_consolidate_recommendations.py --dry-run
  python scripts/audit_and_consolidate_recommendations.py --files "MCP_*.md"
  python scripts/audit_and_consolidate_recommendations.py --report-only
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    parser.add_argument(
        "--files", type=str, help="Filter files by glob pattern (e.g., 'MCP_*.md')"
    )

    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report without archiving files",
    )

    parser.add_argument("--config", type=Path, help="Path to custom configuration file")

    args = parser.parse_args()

    # Create auditor
    auditor = RecommendationAuditor(config_path=args.config, dry_run=args.dry_run)

    # Run workflow
    auditor.run(pattern_filter=args.files, report_only=args.report_only)


if __name__ == "__main__":
    main()
