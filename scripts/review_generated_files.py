#!/usr/bin/env python3
"""
Review Generated Files Script

Creates comprehensive inventory of all generated implementation files:
- Count by type: Python implementations, tests, SQL migrations, CloudFormation, guides
- List by phase: Organize files by project phases (0-9)
- Identify patterns: Analyze which recommendations generated which file types
"""

import os
import json
import logging
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GeneratedFilesReviewer:
    """Review and catalog all generated implementation files."""

    def __init__(
        self, phases_dir: str = "/Users/ryanranft/nba-simulator-aws/docs/phases"
    ):
        """Initialize the reviewer with phases directory."""
        self.phases_dir = Path(phases_dir)
        self.file_inventory = defaultdict(list)
        self.file_counts = Counter()
        self.phase_counts = defaultdict(Counter)
        self.patterns = defaultdict(list)

    def scan_files(self) -> Dict[str, Any]:
        """Scan all generated files and create comprehensive inventory."""
        logger.info("🔍 Scanning generated implementation files...")

        # File patterns to look for
        file_patterns = {
            "python_implementations": "implement_*.py",
            "test_files": "test_*.py",
            "sql_migrations": "*_migration.sql",
            "cloudformation": "*_infrastructure.yaml",
            "implementation_guides": "*_IMPLEMENTATION_GUIDE.md",
        }

        total_files = 0

        # Scan each phase directory
        for phase_dir in sorted(self.phases_dir.glob("phase_*")):
            if not phase_dir.is_dir():
                continue

            phase_name = phase_dir.name
            logger.info(f"📁 Scanning {phase_name}...")

            # Count files by type in this phase
            phase_file_counts = Counter()

            for file_type, pattern in file_patterns.items():
                files = list(phase_dir.glob(pattern))
                phase_file_counts[file_type] = len(files)
                self.file_counts[file_type] += len(files)

                # Add files to inventory
                for file_path in files:
                    file_info = self._analyze_file(file_path, file_type)
                    self.file_inventory[file_type].append(file_info)
                    self.patterns[file_type].append(file_info)
                    total_files += 1

            self.phase_counts[phase_name] = phase_file_counts

        logger.info(
            f"✅ Scanned {total_files} files across {len(self.phase_counts)} phases"
        )

        return {
            "total_files": total_files,
            "file_counts": dict(self.file_counts),
            "phase_counts": dict(self.phase_counts),
            "file_inventory": dict(self.file_inventory),
            "patterns": dict(self.patterns),
        }

    def _analyze_file(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """Analyze individual file and extract metadata."""
        try:
            stat = file_path.stat()

            # Extract recommendation ID from filename
            recommendation_id = self._extract_recommendation_id(file_path.name)

            # Read first few lines for context
            preview_lines = []
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if i >= 20:  # First 20 lines
                            break
                        preview_lines.append(line.strip())
            except Exception as e:
                logger.warning(f"Could not read preview for {file_path}: {e}")

            return {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": file_type,
                "phase": file_path.parent.name,
                "recommendation_id": recommendation_id,
                "size_bytes": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "preview_lines": preview_lines[:10],  # First 10 lines
                "line_count": self._count_lines(file_path),
            }
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": file_type,
                "phase": "unknown",
                "recommendation_id": "unknown",
                "error": str(e),
            }

    def _extract_recommendation_id(self, filename: str) -> str:
        """Extract recommendation ID from filename."""
        # Remove file extension
        name = filename.rsplit(".", 1)[0]

        # Extract ID patterns
        if name.startswith("implement_"):
            return name.replace("implement_", "")
        elif name.startswith("test_"):
            return name.replace("test_", "")
        elif name.endswith("_migration"):
            return name.replace("_migration", "")
        elif name.endswith("_infrastructure"):
            return name.replace("_infrastructure", "")
        elif name.endswith("_IMPLEMENTATION_GUIDE"):
            return name.replace("_IMPLEMENTATION_GUIDE", "")
        else:
            return name

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def generate_report(self, scan_results: Dict[str, Any]) -> str:
        """Generate comprehensive review report."""
        report = []
        report.append("# Generated Files Review Report")
        report.append(f"**Generated:** {datetime.now().isoformat()}")
        report.append(f"**Total Files:** {scan_results['total_files']}")
        report.append("")

        # File counts by type
        report.append("## File Counts by Type")
        report.append("")
        for file_type, count in scan_results["file_counts"].items():
            report.append(f"- **{file_type.replace('_', ' ').title()}:** {count}")
        report.append("")

        # Phase breakdown
        report.append("## Files by Phase")
        report.append("")
        for phase, counts in scan_results["phase_counts"].items():
            total_phase_files = sum(counts.values())
            report.append(f"### {phase.title()}")
            report.append(f"**Total Files:** {total_phase_files}")
            for file_type, count in counts.items():
                if count > 0:
                    report.append(f"- {file_type.replace('_', ' ').title()}: {count}")
            report.append("")

        # File patterns analysis
        report.append("## File Patterns Analysis")
        report.append("")

        for file_type, files in scan_results["file_inventory"].items():
            if not files:
                continue

            report.append(f"### {file_type.replace('_', ' ').title()}")

            # Group by recommendation ID
            by_rec_id = defaultdict(list)
            for file_info in files:
                by_rec_id[file_info.get("recommendation_id", "unknown")].append(
                    file_info
                )

            report.append(f"**Unique Recommendations:** {len(by_rec_id)}")
            report.append(f"**Total Files:** {len(files)}")

            # Show examples
            report.append("**Examples:**")
            for rec_id, file_list in list(by_rec_id.items())[:5]:  # First 5
                report.append(f"- {rec_id}: {len(file_list)} file(s)")
                for file_info in file_list[:2]:  # First 2 files per rec
                    report.append(
                        f"  - `{file_info['file_name']}` ({file_info.get('size_bytes', 0)} bytes)"
                    )

            if len(by_rec_id) > 5:
                report.append(f"  ... and {len(by_rec_id) - 5} more recommendations")

            report.append("")

        # Recommendations without implementations
        report.append("## Missing Implementations Analysis")
        report.append("")

        # Load master recommendations to find missing ones
        try:
            master_recs_path = Path("analysis_results/master_recommendations.json")
            if master_recs_path.exists():
                with open(master_recs_path, "r") as f:
                    master_data = json.load(f)

                all_rec_ids = {
                    rec.get("id", "") for rec in master_data.get("recommendations", [])
                }
                implemented_rec_ids = set()

                for file_type, files in scan_results["file_inventory"].items():
                    for file_info in files:
                        rec_id = file_info.get("recommendation_id", "")
                        if rec_id and rec_id != "unknown":
                            implemented_rec_ids.add(rec_id)

                missing_rec_ids = all_rec_ids - implemented_rec_ids

                report.append(f"**Total Recommendations:** {len(all_rec_ids)}")
                report.append(f"**Implemented:** {len(implemented_rec_ids)}")
                report.append(f"**Missing:** {len(missing_rec_ids)}")
                report.append(
                    f"**Success Rate:** {len(implemented_rec_ids)/len(all_rec_ids)*100:.1f}%"
                )

                if missing_rec_ids:
                    report.append("")
                    report.append("**Missing Recommendation IDs:**")
                    for rec_id in sorted(list(missing_rec_ids))[:20]:  # First 20
                        report.append(f"- {rec_id}")
                    if len(missing_rec_ids) > 20:
                        report.append(f"... and {len(missing_rec_ids) - 20} more")
            else:
                report.append("Master recommendations file not found")
        except Exception as e:
            report.append(f"Error analyzing missing implementations: {e}")

        return "\n".join(report)

    def save_results(self, scan_results: Dict[str, Any], report: str):
        """Save scan results and report to files."""
        # Save JSON results
        results_file = Path("analysis_results/generated_files_inventory.json")
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, "w") as f:
            json.dump(scan_results, f, indent=2)

        # Save markdown report
        report_file = Path("analysis_results/generated_files_review.md")
        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"📊 Results saved to {results_file}")
        logger.info(f"📋 Report saved to {report_file}")


def main():
    """Main execution function."""
    logger.info("🚀 Starting Generated Files Review")

    reviewer = GeneratedFilesReviewer()

    # Scan files
    scan_results = reviewer.scan_files()

    # Generate report
    report = reviewer.generate_report(scan_results)

    # Save results
    reviewer.save_results(scan_results, report)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 GENERATED FILES REVIEW SUMMARY")
    print("=" * 60)
    print(f"Total Files: {scan_results['total_files']}")
    print(f"File Types: {len(scan_results['file_counts'])}")
    print(f"Phases: {len(scan_results['phase_counts'])}")
    print("\nFile Counts:")
    for file_type, count in scan_results["file_counts"].items():
        print(f"  {file_type.replace('_', ' ').title()}: {count}")

    print(
        f"\n✅ Review complete! Check analysis_results/generated_files_review.md for full report"
    )


if __name__ == "__main__":
    main()
