#!/usr/bin/env python3
"""
Organization Enforcement Script

Checks for files in wrong locations and suggests proper destinations.
Can be run as a pre-commit hook or manually.

Usage:
    python scripts/enforce_organization.py              # Check all files
    python scripts/enforce_organization.py --fix        # Auto-move files
    python scripts/enforce_organization.py --check-root # Check root only

Exit codes:
    0 - All files properly organized
    1 - Files found in wrong locations
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


class OrganizationEnforcer:
    """Enforces project organization rules."""

    def __init__(self, fix: bool = False):
        self.fix = fix
        self.violations: List[Tuple[Path, str, str]] = []

        # Define organization rules
        self.rules = {
            # Completion/status documents
            '*_COMPLETE.md': 'docs/archive/completed/',
            '*_REPORT.md': 'docs/archive/reports/',
            '*_STATUS.md': 'docs/archive/status/',
            '*_VERIFICATION*.md': 'docs/archive/verification/',
            '*_SUCCESS.md': 'docs/archive/completed/',

            # Guides and documentation
            '*_GUIDE.md': 'docs/guides/',
            '*_INSTRUCTIONS.md': 'docs/guides/',
            '*_QUICK_START.md': 'docs/guides/',
            '*README.md': 'docs/guides/',  # except main README.md

            # Plans
            '*_PLAN.md': 'docs/plans/',
            '*_ACTION_PLAN.md': 'docs/plans/action/',
            '*_EXPLANATION.md': 'docs/plans/',

            # Test files
            'test_*.py': 'tests/integration/',

            # Log files
            '*.log': 'logs/',

            # JSON files
            '*_RESULTS.json': 'results/',
            '*_report.json': 'reports/',
            'credential_test_report_*.json': 'test_results/',
            'validation_report*.json': 'reports/',
            '*_deployment.json': 'deployment/',
            'claude_desktop_config*.json': 'config/',
            'cursor_mcp_config.json': 'config/',
        }

        # Files that are allowed in root
        self.allowed_in_root = {
            'README.md',
            'LICENSE',
            'CHANGELOG.md',
            'requirements.txt',
            'pyproject.toml',
            'setup.py',
            'Dockerfile',
            '.gitignore',
            '.pre-commit-config.yaml',
            'PROJECT_STATUS.md',
            'PROJECT_MASTER_TRACKER.md',
            'PRIORITY_ACTION_LIST.md',
            'SESSION_SUMMARY.md',
        }

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
            return True

        # Check against rules
        for pattern, destination in self.rules.items():
            if file_path.match(pattern):
                # Exception: main README.md is allowed
                if file_path.name == 'README.md':
                    continue

                self.violations.append((
                    file_path,
                    pattern,
                    destination
                ))
                return False

        return True

    def scan_root(self) -> int:
        """
        Scan root directory for misplaced files.

        Returns:
            Number of violations found
        """
        root_files = [
            f for f in PROJECT_ROOT.iterdir()
            if f.is_file() and not f.name.startswith('.')
        ]

        for file_path in root_files:
            self.check_file(file_path)

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
                print(f"⚠️  SKIP (exists): {file_path.name} → {destination}")
                continue

            # Move file
            try:
                file_path.rename(dest_file)
                print(f"✅ MOVED: {file_path.name} → {destination}")
                moved_count += 1
            except Exception as e:
                print(f"❌ ERROR moving {file_path.name}: {e}")

        return moved_count

    def report_violations(self):
        """Print violations report."""
        if not self.violations:
            print("✅ All files are properly organized!")
            return

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


def main():
    parser = argparse.ArgumentParser(
        description='Enforce project organization rules'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically move files to correct locations'
    )
    parser.add_argument(
        '--check-root',
        action='store_true',
        help='Only check root directory'
    )
    args = parser.parse_args()

    enforcer = OrganizationEnforcer(fix=args.fix)

    # Scan for violations
    violation_count = enforcer.scan_root()

    if violation_count == 0:
        print("✅ All files are properly organized!")
        return 0

    # Report violations
    enforcer.report_violations()

    # Fix if requested
    if args.fix:
        print()
        moved_count = enforcer.fix_violations()
        print(f"\n✅ Moved {moved_count} file(s)")
        return 0

    return 1


if __name__ == '__main__':
    sys.exit(main())
