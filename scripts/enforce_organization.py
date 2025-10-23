#!/usr/bin/env python3
"""
Organization Enforcement Script - Enhanced Edition

Checks for files in wrong locations and suggests proper destinations.
Can be run as a pre-commit hook or manually.

Usage:
    python scripts/enforce_organization.py              # Check all files
    python scripts/enforce_organization.py --fix        # Auto-move files
    python scripts/enforce_organization.py --check-root # Check root only
    python scripts/enforce_organization.py --stats      # Show statistics
    python scripts/enforce_organization.py --verbose    # Detailed output

Exit codes:
    0 - All files properly organized
    1 - Files found in wrong locations
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime, timedelta
from collections import defaultdict

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


class OrganizationEnforcer:
    """Enforces project organization rules with enhanced features."""

    def __init__(self, fix: bool = False, verbose: bool = False, quiet: bool = False):
        self.fix = fix
        self.verbose = verbose
        self.quiet = quiet
        self.violations: List[Tuple[Path, str, str]] = []
        self.stats = {
            "total_files": 0,
            "essential_files": 0,
            "violations": 0,
            "by_category": defaultdict(int),
            "total_size_mb": 0.0,
            "largest_files": [],
            "oldest_files": [],
        }

        # Define organization rules (EXPANDED)
        self.rules = {
            # Completion/status documents
            "*_COMPLETE.md": "docs/archive/completed/",
            "*_REPORT.md": "docs/archive/reports/",
            "*_STATUS.md": "docs/archive/status/",
            "*_VERIFICATION*.md": "docs/archive/verification/",
            "*_SUCCESS.md": "docs/archive/completed/",
            "*_DONE.md": "docs/archive/completed/",
            "*_FINISHED.md": "docs/archive/completed/",
            # Results and summaries
            "*_RESULTS.md": "docs/archive/results/",
            "*_SUMMARY.md": "docs/archive/summaries/",
            "*_TEST_RESULTS.md": "docs/archive/test-results/",
            # Setup and configuration
            "*_SETUP.md": "docs/guides/",
            "*_OPTIONS.md": "docs/guides/",
            "*_CONFIG.md": "docs/guides/",
            # Features and enhancements
            "*_FEATURE.md": "docs/archive/features/",
            "*_ADDED.md": "docs/archive/additions/",
            "*_FIXED.md": "docs/archive/fixes/",
            "*_ENHANCEMENT*.md": "docs/archive/enhancements/",
            # Reference documents
            "*_REFERENCE.md": "docs/guides/",
            "*_QUICK_REFERENCE.md": "docs/guides/",
            # Preparation and security
            "*_PREPARED.md": "docs/archive/preparation/",
            "*_SECURED.md": "docs/archive/security/",
            "*_READY.md": "docs/archive/preparation/",
            # Next steps and deployment
            "*_NEXT_STEPS.md": "docs/archive/next-steps/",
            "*_DEPLOYMENT_SUMMARY.md": "docs/archive/deployment/",
            "*_LAUNCH*.md": "docs/archive/deployment/",
            # Guides and documentation
            "*_GUIDE.md": "docs/guides/",
            "*_INSTRUCTIONS.md": "docs/guides/",
            "*_QUICK_START.md": "docs/guides/",
            "*README.md": "docs/guides/",  # except main README.md
            # Plans
            "*_PLAN.md": "docs/plans/",
            "*_ACTION_PLAN.md": "docs/plans/action/",
            "*_EXPLANATION.md": "docs/plans/",
            # Test files
            "test_*.py": "tests/integration/",
            # Log files
            "*.log": "logs/",
            # JSON files
            "*_RESULTS.json": "results/",
            "*_report.json": "reports/",
            "*_SUMMARY.json": "results/",
            "credential_test_report_*.json": "test_results/",
            "validation_report*.json": "reports/",
            "*_deployment.json": "deployment/",
            "claude_desktop_config*.json": "config/",
            "cursor_mcp_config.json": "config/",
        }

        # Files that are allowed in root
        self.allowed_in_root = {
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "Dockerfile",
            ".gitignore",
            ".pre-commit-config.yaml",
            "PROJECT_STATUS.md",
            "PROJECT_MASTER_TRACKER.md",
            "PRIORITY_ACTION_LIST.md",
            "SESSION_SUMMARY.md",
        }

        # Target limits
        self.target_root_files = 20
        self.size_warning_mb = 0.5  # 500 KB
        self.size_critical_mb = 1.0  # 1 MB

    def get_file_age_days(self, file_path: Path) -> int:
        """Get file age in days since last modification."""
        try:
            mtime = file_path.stat().st_mtime
            age = datetime.now() - datetime.fromtimestamp(mtime)
            return age.days
        except:
            return 0

    def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB."""
        try:
            return file_path.stat().st_size / (1024 * 1024)
        except:
            return 0.0

    def check_file(self, file_path: Path) -> bool:
        """
        Check if a file is in the correct location.

        Returns:
            True if file is properly placed, False otherwise
        """
        # Get relative path from project root
        try:
            rel_path = file_path.relative_to(PROJECT_ROOT)
        except ValueError:
            return True  # Not in project, skip

        # If not in root, assume it's organized
        if len(rel_path.parts) > 1:
            return True

        # Check if file is allowed in root
        if file_path.name in self.allowed_in_root:
            self.stats["essential_files"] += 1
            return True

        # Check against rules
        for pattern, destination in self.rules.items():
            if file_path.match(pattern):
                # Exception: main README.md is allowed
                if file_path.name == "README.md":
                    continue

                self.violations.append((file_path, pattern, destination))
                self.stats["by_category"][destination] += 1
                self.stats["violations"] += 1
                return False

        return True

    def scan_root(self) -> int:
        """
        Scan root directory for misplaced files.

        Returns:
            Number of violations found
        """
        root_files = [
            f
            for f in PROJECT_ROOT.iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]

        self.stats["total_files"] = len(root_files)

        # Collect file info for statistics
        for file_path in root_files:
            size_mb = self.get_file_size_mb(file_path)
            age_days = self.get_file_age_days(file_path)

            self.stats["total_size_mb"] += size_mb

            # Track largest files
            self.stats["largest_files"].append((file_path.name, size_mb))

            # Track oldest files
            self.stats["oldest_files"].append((file_path.name, age_days))

            # Check organization
            self.check_file(file_path)

        # Sort and keep top 5
        self.stats["largest_files"].sort(key=lambda x: x[1], reverse=True)
        self.stats["largest_files"] = self.stats["largest_files"][:5]

        self.stats["oldest_files"].sort(key=lambda x: x[1], reverse=True)
        self.stats["oldest_files"] = self.stats["oldest_files"][:5]

        return len(self.violations)

    def fix_violations(self) -> int:
        """
        Move files to proper locations.

        Returns:
            Number of files moved
        """
        moved_count = 0

        for file_path, pattern, destination in self.violations:
            dest_dir = PROJECT_ROOT / destination
            dest_dir.mkdir(parents=True, exist_ok=True)

            dest_file = dest_dir / file_path.name

            # Check if destination file already exists
            if dest_file.exists():
                if self.verbose:
                    print(f"⚠️  SKIP (exists): {file_path.name} → {destination}")
                continue

            # Move file
            try:
                file_path.rename(dest_file)
                if not self.quiet:
                    print(f"✅ MOVED: {file_path.name} → {destination}")
                moved_count += 1
            except Exception as e:
                print(f"❌ ERROR moving {file_path.name}: {e}")

        return moved_count

    def report_violations(self):
        """Print violations report."""
        if not self.violations:
            if not self.quiet:
                print("✅ All files are properly organized!")
            return

        if not self.quiet:
            print(f"⚠️  Found {len(self.violations)} file(s) in wrong locations:\n")

            # Group violations by destination
            by_dest: Dict[str, List[Path]] = {}
            for file_path, pattern, destination in self.violations:
                if destination not in by_dest:
                    by_dest[destination] = []
                by_dest[destination].append(file_path)

            for destination, files in sorted(by_dest.items()):
                print(f"📁 Should move to {destination}:")
                for file_path in files:
                    print(f"   - {file_path.name}")
                print()

            print("To fix automatically, run:")
            print("   python scripts/enforce_organization.py --fix")

    def report_statistics(self, json_output: bool = False):
        """Print detailed statistics report."""
        if json_output:
            # JSON output for CI/CD
            output = {
                "total_files": self.stats["total_files"],
                "essential_files": self.stats["essential_files"],
                "violations": self.stats["violations"],
                "target": self.target_root_files,
                "compliance_rate": round(
                    (
                        (
                            (self.stats["total_files"] - self.stats["violations"])
                            / self.stats["total_files"]
                            * 100
                        )
                        if self.stats["total_files"] > 0
                        else 100
                    ),
                    2,
                ),
                "by_category": dict(self.stats["by_category"]),
                "total_size_mb": round(self.stats["total_size_mb"], 2),
            }
            print(json.dumps(output, indent=2))
            return

        # Human-readable statistics
        print("📊 Organization Statistics")
        print("=" * 60)
        print()

        # File counts
        print(
            f"Root Directory: {self.stats['total_files']} files (Target: <{self.target_root_files})"
        )
        print(f"  ✓ Essential: {self.stats['essential_files']} files")
        print(f"  ⚠️  Violations: {self.stats['violations']} files")
        print()

        # Compliance rate
        if self.stats["total_files"] > 0:
            compliance = (
                (self.stats["total_files"] - self.stats["violations"])
                / self.stats["total_files"]
                * 100
            )
            status_emoji = (
                "✅" if compliance >= 95 else "⚠️" if compliance >= 80 else "❌"
            )
            print(f"{status_emoji} Compliance Rate: {compliance:.1f}%")
            print()

        # By category
        if self.stats["by_category"]:
            print("By Category:")
            for dest, count in sorted(
                self.stats["by_category"].items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  📁 {dest:<35} : {count:>3} violations")
            print()

        # Size information
        print(f"Total Size: {self.stats['total_size_mb']:.2f} MB")
        print()

        # Largest files
        if self.stats["largest_files"]:
            print("Largest Files (top 5):")
            for i, (name, size_mb) in enumerate(self.stats["largest_files"], 1):
                warning = " ⚠️" if size_mb > self.size_warning_mb else ""
                print(f"  {i}. {name:<50} ({size_mb:.2f} MB){warning}")
            print()

        # Oldest files
        if self.stats["oldest_files"] and self.stats["oldest_files"][0][1] > 0:
            print("Oldest Files (top 5):")
            for i, (name, age_days) in enumerate(self.stats["oldest_files"], 1):
                warning = " 🕒" if age_days > 90 else ""
                print(f"  {i}. {name:<50} ({age_days} days old){warning}")
            print()

        # Recommendations
        if self.stats["violations"] > 0:
            print("💡 Recommendations:")
            print(
                f"  • Run with --fix to auto-organize {self.stats['violations']} files"
            )

            if self.stats["oldest_files"] and self.stats["oldest_files"][0][1] > 90:
                print("  • Consider archiving files older than 90 days")
                print("    Run: ./scripts/auto_archive.sh")

            if self.stats["total_size_mb"] > 10:
                print("  • Root directory size exceeds 10 MB")
                print("    Consider moving large files to appropriate directories")


def main():
    parser = argparse.ArgumentParser(
        description="Enforce project organization rules",
        epilog="Example: python scripts/enforce_organization.py --stats --verbose",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically move files to correct locations",
    )
    parser.add_argument(
        "--check-root",
        action="store_true",
        help="Only check root directory (default behavior)",
    )
    parser.add_argument("--stats", action="store_true", help="Show detailed statistics")
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed progress information"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Minimal output (exit code only)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output statistics as JSON (for CI/CD)"
    )
    args = parser.parse_args()

    enforcer = OrganizationEnforcer(
        fix=args.fix, verbose=args.verbose, quiet=args.quiet
    )

    # Scan for violations
    violation_count = enforcer.scan_root()

    # Show statistics if requested
    if args.stats or args.json:
        enforcer.report_statistics(json_output=args.json)
        if args.json:
            return 1 if violation_count > 0 else 0

    if violation_count == 0:
        if not args.quiet and not args.stats:
            print("✅ All files are properly organized!")
        return 0

    # Report violations (unless stats-only mode)
    if not args.stats:
        enforcer.report_violations()

    # Fix if requested
    if args.fix:
        if not args.quiet:
            print()
        moved_count = enforcer.fix_violations()
        if not args.quiet:
            print(f"\n✅ Moved {moved_count} file(s)")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
