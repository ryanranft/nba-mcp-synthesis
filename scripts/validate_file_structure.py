#!/usr/bin/env python3
"""
Validate File Structure Script

Verifies all generated files follow correct structure:
- Python files: Check imports, class structure, setup/execute/cleanup methods
- Test files: Verify test fixtures, assertions, mock usage
- SQL migrations: Validate up/down migrations, rollback procedures
- CloudFormation: Check resource definitions, parameter structure
- Guides: Ensure prerequisites, steps, validation sections present
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileStructureValidator:
    """Validates structure of generated implementation files."""

    def __init__(self, phases_dir: str = "/Users/ryanranft/nba-simulator-aws/docs/phases"):
        """Initialize validator with phases directory."""
        self.phases_dir = Path(phases_dir)
        self.validation_results = defaultdict(list)
        self.errors = []
        self.warnings = []

    def validate_all_files(self) -> Dict[str, Any]:
        """Validate structure of all generated files."""
        logger.info("🔍 Validating file structures...")

        # Load file inventory
        inventory_file = Path("analysis_results/generated_files_inventory.json")
        if not inventory_file.exists():
            logger.error("File inventory not found. Run review_generated_files.py first.")
            return {}

        with open(inventory_file, 'r') as f:
            inventory = json.load(f)

        total_validated = 0

        # Validate each file type
        for file_type, files in inventory.get('file_inventory', {}).items():
            logger.info(f"📋 Validating {file_type}...")

            for file_info in files:
                file_path = Path(file_info['file_path'])
                if file_path.exists():
                    validation_result = self._validate_file(file_path, file_type)
                    self.validation_results[file_type].append(validation_result)
                    total_validated += 1
                else:
                    logger.warning(f"File not found: {file_path}")

        logger.info(f"✅ Validated {total_validated} files")

        return {
            'total_validated': total_validated,
            'validation_results': dict(self.validation_results),
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': self._generate_summary()
        }

    def _validate_file(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """Validate individual file structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            validation_result = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_type': file_type,
                'phase': file_path.parent.name,
                'valid': True,
                'issues': [],
                'checks_passed': [],
                'checks_failed': []
            }

            # Validate based on file type
            if file_type == 'python_implementations':
                self._validate_python_implementation(content, validation_result)
            elif file_type == 'test_files':
                self._validate_test_file(content, validation_result)
            elif file_type == 'sql_migrations':
                self._validate_sql_migration(content, validation_result)
            elif file_type == 'cloudformation':
                self._validate_cloudformation(content, validation_result)
            elif file_type == 'implementation_guides':
                self._validate_implementation_guide(content, validation_result)

            return validation_result

        except Exception as e:
            logger.error(f"Error validating {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_type': file_type,
                'valid': False,
                'error': str(e)
            }

    def _validate_python_implementation(self, content: str, result: Dict[str, Any]):
        """Validate Python implementation file structure."""
        checks = [
            ('has_shebang', self._check_shebang, content),
            ('has_docstring', self._check_docstring, content),
            ('has_imports', self._check_imports, content),
            ('has_class_definition', self._check_class_definition, content),
            ('has_setup_method', self._check_setup_method, content),
            ('has_execute_method', self._check_execute_method, content),
            ('has_cleanup_method', self._check_cleanup_method, content),
            ('has_logging', self._check_logging, content),
            ('has_error_handling', self._check_error_handling, content),
            ('has_type_hints', self._check_type_hints, content)
        ]

        for check_name, check_func, *args in checks:
            try:
                if check_func(*args):
                    result['checks_passed'].append(check_name)
                else:
                    result['checks_failed'].append(check_name)
                    result['issues'].append(f"Missing {check_name.replace('_', ' ')}")
            except Exception as e:
                result['checks_failed'].append(check_name)
                result['issues'].append(f"Error checking {check_name}: {e}")

        if result['checks_failed']:
            result['valid'] = False

    def _validate_test_file(self, content: str, result: Dict[str, Any]):
        """Validate test file structure."""
        checks = [
            ('has_test_imports', self._check_test_imports, content),
            ('has_test_class', self._check_test_class, content),
            ('has_test_methods', self._check_test_methods, content),
            ('has_assertions', self._check_assertions, content),
            ('has_fixtures', self._check_fixtures, content),
            ('has_mock_usage', self._check_mock_usage, content)
        ]

        for check_name, check_func, *args in checks:
            try:
                if check_func(*args):
                    result['checks_passed'].append(check_name)
                else:
                    result['checks_failed'].append(check_name)
                    result['issues'].append(f"Missing {check_name.replace('_', ' ')}")
            except Exception as e:
                result['checks_failed'].append(check_name)
                result['issues'].append(f"Error checking {check_name}: {e}")

        if result['checks_failed']:
            result['valid'] = False

    def _validate_sql_migration(self, content: str, result: Dict[str, Any]):
        """Validate SQL migration file structure."""
        checks = [
            ('has_up_migration', self._check_up_migration, content),
            ('has_down_migration', self._check_down_migration, content),
            ('has_rollback', self._check_rollback, content),
            ('has_comments', self._check_sql_comments, content)
        ]

        for check_name, check_func, *args in checks:
            try:
                if check_func(*args):
                    result['checks_passed'].append(check_name)
                else:
                    result['checks_failed'].append(check_name)
                    result['issues'].append(f"Missing {check_name.replace('_', ' ')}")
            except Exception as e:
                result['checks_failed'].append(check_name)
                result['issues'].append(f"Error checking {check_name}: {e}")

        if result['checks_failed']:
            result['valid'] = False

    def _validate_cloudformation(self, content: str, result: Dict[str, Any]):
        """Validate CloudFormation file structure."""
        checks = [
            ('has_resources', self._check_cloudformation_resources, content),
            ('has_parameters', self._check_cloudformation_parameters, content),
            ('has_outputs', self._check_cloudformation_outputs, content),
            ('has_description', self._check_cloudformation_description, content)
        ]

        for check_name, check_func, *args in checks:
            try:
                if check_func(*args):
                    result['checks_passed'].append(check_name)
                else:
                    result['checks_failed'].append(check_name)
                    result['issues'].append(f"Missing {check_name.replace('_', ' ')}")
            except Exception as e:
                result['checks_failed'].append(check_name)
                result['issues'].append(f"Error checking {check_name}: {e}")

        if result['checks_failed']:
            result['valid'] = False

    def _validate_implementation_guide(self, content: str, result: Dict[str, Any]):
        """Validate implementation guide structure."""
        checks = [
            ('has_title', self._check_guide_title, content),
            ('has_prerequisites', self._check_prerequisites, content),
            ('has_steps', self._check_implementation_steps, content),
            ('has_validation', self._check_validation_section, content),
            ('has_troubleshooting', self._check_troubleshooting, content)
        ]

        for check_name, check_func, *args in checks:
            try:
                if check_func(*args):
                    result['checks_passed'].append(check_name)
                else:
                    result['checks_failed'].append(check_name)
                    result['issues'].append(f"Missing {check_name.replace('_', ' ')}")
            except Exception as e:
                result['checks_failed'].append(check_name)
                result['issues'].append(f"Error checking {check_name}: {e}")

        if result['checks_failed']:
            result['valid'] = False

    # Check functions for Python implementations
    def _check_shebang(self, content: str) -> bool:
        return content.startswith('#!/usr/bin/env python3')

    def _check_docstring(self, content: str) -> bool:
        return '"""' in content[:500] or "'''" in content[:500]

    def _check_imports(self, content: str) -> bool:
        return 'import ' in content or 'from ' in content

    def _check_class_definition(self, content: str) -> bool:
        return re.search(r'class\s+\w+', content) is not None

    def _check_setup_method(self, content: str) -> bool:
        return 'def setup(' in content or 'def __init__(' in content

    def _check_execute_method(self, content: str) -> bool:
        return 'def execute(' in content or 'def run(' in content

    def _check_cleanup_method(self, content: str) -> bool:
        return 'def cleanup(' in content or 'def __del__(' in content

    def _check_logging(self, content: str) -> bool:
        return 'logging' in content or 'logger' in content

    def _check_error_handling(self, content: str) -> bool:
        return 'try:' in content and 'except' in content

    def _check_type_hints(self, content: str) -> bool:
        return '->' in content or ': ' in content

    # Check functions for test files
    def _check_test_imports(self, content: str) -> bool:
        return 'import pytest' in content or 'import unittest' in content

    def _check_test_class(self, content: str) -> bool:
        return re.search(r'class\s+Test\w+', content) is not None

    def _check_test_methods(self, content: str) -> bool:
        return re.search(r'def\s+test_\w+', content) is not None

    def _check_assertions(self, content: str) -> bool:
        return 'assert ' in content or 'self.assertEqual' in content

    def _check_fixtures(self, content: str) -> bool:
        return '@pytest.fixture' in content or 'def setUp(' in content

    def _check_mock_usage(self, content: str) -> bool:
        return 'mock' in content.lower() or 'patch' in content

    # Check functions for SQL migrations
    def _check_up_migration(self, content: str) -> bool:
        return '-- UP' in content.upper() or 'CREATE' in content.upper()

    def _check_down_migration(self, content: str) -> bool:
        return '-- DOWN' in content.upper() or 'DROP' in content.upper()

    def _check_rollback(self, content: str) -> bool:
        return 'ROLLBACK' in content.upper() or '-- ROLLBACK' in content.upper()

    def _check_sql_comments(self, content: str) -> bool:
        return '--' in content

    # Check functions for CloudFormation
    def _check_cloudformation_resources(self, content: str) -> bool:
        return 'Resources:' in content

    def _check_cloudformation_parameters(self, content: str) -> bool:
        return 'Parameters:' in content

    def _check_cloudformation_outputs(self, content: str) -> bool:
        return 'Outputs:' in content

    def _check_cloudformation_description(self, content: str) -> bool:
        return 'Description:' in content

    # Check functions for implementation guides
    def _check_guide_title(self, content: str) -> bool:
        return content.startswith('#') or 'Title:' in content

    def _check_prerequisites(self, content: str) -> bool:
        return 'Prerequisites' in content or 'Requirements' in content

    def _check_implementation_steps(self, content: str) -> bool:
        return 'Steps:' in content or 'Implementation:' in content

    def _check_validation_section(self, content: str) -> bool:
        return 'Validation' in content or 'Testing' in content

    def _check_troubleshooting(self, content: str) -> bool:
        return 'Troubleshooting' in content or 'Issues' in content

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        summary = {
            'total_files': sum(len(files) for files in self.validation_results.values()),
            'valid_files': 0,
            'invalid_files': 0,
            'by_file_type': {},
            'common_issues': defaultdict(int)
        }

        for file_type, files in self.validation_results.items():
            valid_count = sum(1 for f in files if f.get('valid', False))
            invalid_count = len(files) - valid_count

            summary['by_file_type'][file_type] = {
                'total': len(files),
                'valid': valid_count,
                'invalid': invalid_count,
                'success_rate': valid_count / len(files) * 100 if files else 0
            }

            summary['valid_files'] += valid_count
            summary['invalid_files'] += invalid_count

            # Count common issues
            for file_info in files:
                for issue in file_info.get('issues', []):
                    summary['common_issues'][issue] += 1

        return summary

    def generate_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate validation report."""
        report = []
        report.append("# File Structure Validation Report")
        report.append(f"**Generated:** {Path().cwd()}")
        report.append(f"**Total Files Validated:** {validation_results['total_validated']}")
        report.append("")

        # Summary
        summary = validation_results['summary']
        report.append("## Validation Summary")
        report.append("")
        report.append(f"- **Total Files:** {summary['total_files']}")
        report.append(f"- **Valid Files:** {summary['valid_files']}")
        report.append(f"- **Invalid Files:** {summary['invalid_files']}")
        report.append(f"- **Overall Success Rate:** {summary['valid_files']/summary['total_files']*100:.1f}%")
        report.append("")

        # By file type
        report.append("## Results by File Type")
        report.append("")
        for file_type, stats in summary['by_file_type'].items():
            report.append(f"### {file_type.replace('_', ' ').title()}")
            report.append(f"- **Total:** {stats['total']}")
            report.append(f"- **Valid:** {stats['valid']}")
            report.append(f"- **Invalid:** {stats['invalid']}")
            report.append(f"- **Success Rate:** {stats['success_rate']:.1f}%")
            report.append("")

        # Common issues
        if summary['common_issues']:
            report.append("## Common Issues")
            report.append("")
            for issue, count in sorted(summary['common_issues'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"- **{issue}:** {count} files")
            report.append("")

        # Detailed results
        report.append("## Detailed Results")
        report.append("")
        for file_type, files in validation_results['validation_results'].items():
            if not files:
                continue

            report.append(f"### {file_type.replace('_', ' ').title()}")
            report.append("")

            for file_info in files:
                status = "✅" if file_info.get('valid', False) else "❌"
                report.append(f"**{status} {file_info['file_name']}**")

                if file_info.get('checks_passed'):
                    report.append(f"- Passed: {', '.join(file_info['checks_passed'])}")

                if file_info.get('checks_failed'):
                    report.append(f"- Failed: {', '.join(file_info['checks_failed'])}")

                if file_info.get('issues'):
                    report.append(f"- Issues: {', '.join(file_info['issues'])}")

                report.append("")

        return "\n".join(report)

    def save_results(self, validation_results: Dict[str, Any], report: str):
        """Save validation results and report."""
        # Save JSON results
        results_file = Path("analysis_results/file_structure_validation.json")
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2)

        # Save markdown report
        report_file = Path("analysis_results/file_structure_validation_report.md")
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"📊 Validation results saved to {results_file}")
        logger.info(f"📋 Validation report saved to {report_file}")


def main():
    """Main execution function."""
    logger.info("🚀 Starting File Structure Validation")

    validator = FileStructureValidator()

    # Validate files
    validation_results = validator.validate_all_files()

    if not validation_results:
        logger.error("No files to validate. Exiting.")
        return

    # Generate report
    report = validator.generate_report(validation_results)

    # Save results
    validator.save_results(validation_results, report)

    # Print summary
    summary = validation_results['summary']
    print("\n" + "="*60)
    print("📋 FILE STRUCTURE VALIDATION SUMMARY")
    print("="*60)
    print(f"Total Files: {summary['total_files']}")
    print(f"Valid Files: {summary['valid_files']}")
    print(f"Invalid Files: {summary['invalid_files']}")
    print(f"Success Rate: {summary['valid_files']/summary['total_files']*100:.1f}%")

    print("\nBy File Type:")
    for file_type, stats in summary['by_file_type'].items():
        print(f"  {file_type.replace('_', ' ').title()}: {stats['valid']}/{stats['total']} ({stats['success_rate']:.1f}%)")

    if summary['common_issues']:
        print("\nTop Issues:")
        for issue, count in list(summary['common_issues'].items())[:5]:
            print(f"  {issue}: {count} files")

    print(f"\n✅ Validation complete! Check analysis_results/file_structure_validation_report.md for full report")


if __name__ == "__main__":
    main()

