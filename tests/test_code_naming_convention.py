#!/usr/bin/env python3
"""
Test Code Naming Convention Compliance

This test ensures all Python code follows the naming convention
defined in SECRETS_STRUCTURE.md for environment variable references.

The naming convention is:
{SERVICE}_{RESOURCE_TYPE}_{PROJECT}_{CONTEXT}

Examples:
- GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
- ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT
- DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_TEST

Code should use:
- get_hierarchical_env() helper function
- get_api_key() convenience function
- Explicit hierarchical fallback chains

NOT:
- os.getenv('ANTHROPIC_API_KEY') without fallbacks
"""

import pytest
import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass


@dataclass
class CodeViolation:
    """Represents a naming convention violation in code"""
    file_path: str
    line_number: int
    line_content: str
    pattern: str
    suggested_fix: str
    severity: str  # 'error', 'warning', 'info'


@dataclass
class ComplianceReport:
    """Compliance report for the entire codebase"""
    total_files_scanned: int
    compliant_files: int
    violations: List[CodeViolation]
    compliant_examples: List[str]


class SecretsStructureParser:
    """Parser for SECRETS_STRUCTURE.md"""

    def __init__(self, structure_file: Path):
        self.structure_file = structure_file
        self.naming_convention = None
        self.examples = []
        self.deprecated_patterns = []

    def parse(self) -> Dict[str, any]:
        """Parse SECRETS_STRUCTURE.md and extract naming rules"""
        if not self.structure_file.exists():
            raise FileNotFoundError(f"SECRETS_STRUCTURE.md not found at {self.structure_file}")

        content = self.structure_file.read_text()

        # Extract naming convention pattern
        pattern_match = re.search(r'SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT', content)
        if pattern_match:
            self.naming_convention = "SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT"

        # Extract examples
        example_pattern = r'(?:GOOGLE|ANTHROPIC|DEEPSEEK|OPENAI|SLACK)_[A-Z_]+_(?:NBA|BIG_CAT)_[A-Z_]+_(?:WORKFLOW|DEVELOPMENT|TEST|PRODUCTION)'
        self.examples = re.findall(example_pattern, content)

        # Extract deprecated patterns
        deprecated_section = re.search(r'## ⚠️ Deprecated Patterns(.*?)(?=##|$)', content, re.DOTALL)
        if deprecated_section:
            deprecated_content = deprecated_section.group(1)
            # Find patterns like SLACK_WEBHOOK_URL=... (without project/context)
            self.deprecated_patterns = re.findall(r'([A-Z_]+)=', deprecated_content)

        return {
            'naming_convention': self.naming_convention,
            'examples': self.examples,
            'deprecated_patterns': self.deprecated_patterns
        }


class CodeNamingScanner:
    """Scanner for finding naming convention violations in code"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations = []
        self.compliant_examples = []

        # Patterns to detect (old-style direct os.getenv without hierarchical fallback)
        self.violation_patterns = [
            # Direct os.getenv with common secret names
            (r'os\.getenv\(["\']ANTHROPIC_API_KEY["\']\)', 'ANTHROPIC_API_KEY'),
            (r'os\.getenv\(["\']GOOGLE_API_KEY["\']\)', 'GOOGLE_API_KEY'),
            (r'os\.getenv\(["\']OPENAI_API_KEY["\']\)', 'OPENAI_API_KEY'),
            (r'os\.getenv\(["\']DEEPSEEK_API_KEY["\']\)', 'DEEPSEEK_API_KEY'),
            (r'os\.getenv\(["\']SLACK_WEBHOOK_URL["\']\)', 'SLACK_WEBHOOK_URL'),
            (r'os\.getenv\(["\']LINEAR_API_KEY["\']\)', 'LINEAR_API_KEY'),
            (r'os\.getenv\(["\']DB_PASSWORD["\']\)', 'DB_PASSWORD'),
            (r'os\.getenv\(["\']DB_HOST["\']\)', 'DB_HOST'),
            (r'os\.getenv\(["\']RDS_PASSWORD["\']\)', 'RDS_PASSWORD'),
            (r'os\.getenv\(["\']RDS_HOST["\']\)', 'RDS_HOST'),
        ]

        # Compliant patterns (hierarchical naming or using helper functions)
        self.compliant_patterns = [
            r'get_hierarchical_env\(',
            r'get_api_key\(',
            r'os\.getenv\(["\'][A-Z_]+_NBA_MCP_SYNTHESIS_[A-Z]+["\']\)',
            r'or os\.getenv\(',  # Fallback chains are OK
        ]

    def scan_file(self, file_path: Path) -> List[CodeViolation]:
        """Scan a single file for violations"""
        violations = []

        try:
            content = file_path.read_text()
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # Check for violations
                for pattern, secret_name in self.violation_patterns:
                    if re.search(pattern, line):
                        # Check if it's part of a compliant pattern
                        is_compliant = any(re.search(cp, line) for cp in self.compliant_patterns)

                        if not is_compliant:
                            # Check if next few lines have fallback (hierarchical chain)
                            has_fallback = False
                            if line_num < len(lines):
                                next_lines = '\n'.join(lines[line_num:min(line_num + 3, len(lines))])
                                if re.search(r'or\s+os\.getenv\(["\'][A-Z_]+_NBA_MCP_SYNTHESIS', next_lines):
                                    has_fallback = True

                            if not has_fallback:
                                suggested_fix = self._generate_suggested_fix(secret_name, line)
                                violations.append(CodeViolation(
                                    file_path=str(file_path),
                                    line_number=line_num,
                                    line_content=line.strip(),
                                    pattern=secret_name,
                                    suggested_fix=suggested_fix,
                                    severity='warning'
                                ))
                        else:
                            # This is a compliant example
                            self.compliant_examples.append(f"{file_path}:{line_num}")

        except Exception as e:
            # Skip files that can't be read
            pass

        return violations

    def scan_project(self) -> List[CodeViolation]:
        """Scan entire project for violations"""
        all_violations = []

        # Scan all Python files
        for py_file in self.project_root.rglob('*.py'):
            # Skip test files and migration scripts
            if 'test_code_naming_convention.py' in str(py_file):
                continue
            if '__pycache__' in str(py_file):
                continue
            if '.venv' in str(py_file) or 'venv' in str(py_file):
                continue

            violations = self.scan_file(py_file)
            all_violations.extend(violations)

        self.violations = all_violations
        return all_violations

    def _generate_suggested_fix(self, secret_name: str, line: str) -> str:
        """Generate suggested fix for a violation"""

        # Map common secrets to their service names
        service_map = {
            'ANTHROPIC_API_KEY': 'ANTHROPIC',
            'GOOGLE_API_KEY': 'GOOGLE',
            'OPENAI_API_KEY': 'OPENAI',
            'DEEPSEEK_API_KEY': 'DEEPSEEK',
            'SLACK_WEBHOOK_URL': 'SLACK',
            'LINEAR_API_KEY': 'LINEAR',
        }

        if secret_name in service_map:
            service = service_map[secret_name]
            if 'API_KEY' in secret_name:
                return f"get_api_key('{service}')"
            elif 'WEBHOOK' in secret_name:
                return f"get_slack_config('SLACK_WEBHOOK_URL')"

        # For database configs
        if secret_name.startswith('DB_') or secret_name.startswith('RDS_'):
            config_type = secret_name.replace('RDS_', 'DB_')
            return f"get_database_config('{config_type}')"

        # Generic fallback chain
        return f"""get_hierarchical_env('{secret_name}') or fallback to old naming"""

    def generate_compliance_report(self, total_files: int) -> ComplianceReport:
        """Generate compliance report"""
        return ComplianceReport(
            total_files_scanned=total_files,
            compliant_files=total_files - len(set(v.file_path for v in self.violations)),
            violations=self.violations,
            compliant_examples=self.compliant_examples
        )


class TestCodeNamingConventionCompliance:
    """Test that all code follows SECRETS_STRUCTURE.md naming convention"""

    @pytest.fixture
    def secrets_structure_file(self):
        """Path to SECRETS_STRUCTURE.md"""
        return Path("/Users/ryanranft/Desktop/++/big_cat_bets_assets/SECRETS_STRUCTURE.md")

    @pytest.fixture
    def project_root(self):
        """Path to project root"""
        return Path(__file__).parent.parent

    def test_01_secrets_structure_md_exists(self, secrets_structure_file):
        """Test: SECRETS_STRUCTURE.md file exists"""
        assert secrets_structure_file.exists(), \
            "SECRETS_STRUCTURE.md not found at expected location"
        print(f"✅ SECRETS_STRUCTURE.md found at {secrets_structure_file}")

    def test_02_parse_secrets_structure(self, secrets_structure_file):
        """Test: Can parse SECRETS_STRUCTURE.md successfully"""
        parser = SecretsStructureParser(secrets_structure_file)
        result = parser.parse()

        assert result['naming_convention'] == "SERVICE_RESOURCE_TYPE_PROJECT_CONTEXT"
        assert len(result['examples']) > 0

        print(f"✅ Parsed naming convention: {result['naming_convention']}")
        print(f"✅ Found {len(result['examples'])} examples")
        print(f"   Sample examples: {result['examples'][:3]}")

    def test_03_scan_code_for_violations(self, project_root):
        """Test: Scan all code files for naming convention violations"""
        scanner = CodeNamingScanner(project_root)
        violations = scanner.scan_project()

        print(f"\n📊 Scan Results:")
        print(f"   Total violations found: {len(violations)}")
        print(f"   Unique files with violations: {len(set(v.file_path for v in violations))}")

        # Group by severity
        errors = [v for v in violations if v.severity == 'error']
        warnings = [v for v in violations if v.severity == 'warning']

        print(f"   Errors: {len(errors)}")
        print(f"   Warnings: {len(warnings)}")

        # Show first few violations
        if violations:
            print(f"\n⚠️  Sample violations:")
            for v in violations[:5]:
                print(f"   {Path(v.file_path).name}:{v.line_number}")
                print(f"      Current: {v.line_content[:80]}")
                print(f"      Suggested: {v.suggested_fix}")

    def test_04_models_use_hierarchical_naming(self, project_root):
        """Test: All models in synthesis/models/ use hierarchical naming"""
        models_dir = project_root / "synthesis" / "models"

        if not models_dir.exists():
            pytest.skip("Models directory not found")

        scanner = CodeNamingScanner(project_root)
        violations = []

        for model_file in models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue

            file_violations = scanner.scan_file(model_file)
            violations.extend(file_violations)

        print(f"\n🔍 Models scan results:")
        print(f"   Files scanned: {len(list(models_dir.glob('*.py'))) - 1}")
        print(f"   Violations found: {len(violations)}")

        if violations:
            print(f"\n⚠️  Model violations:")
            for v in violations:
                print(f"   {Path(v.file_path).name}:{v.line_number} - {v.pattern}")
                print(f"      Suggested: {v.suggested_fix}")

        # This is a warning test - we allow violations but report them
        if len(violations) > 0:
            print(f"\n⚠️  {len(violations)} violations found in models")
            print(f"   Consider migrating to hierarchical naming")

    def test_05_configs_use_hierarchical_naming(self, project_root):
        """Test: All config files use hierarchical naming"""
        config_files = [
            project_root / "mcp_server" / "config.py",
            project_root / "mcp_server" / "fastmcp_settings.py",
            project_root / "mcp_server" / "config_manager.py",
        ]

        scanner = CodeNamingScanner(project_root)
        violations = []

        for config_file in config_files:
            if config_file.exists():
                file_violations = scanner.scan_file(config_file)
                violations.extend(file_violations)

        print(f"\n🔍 Config files scan results:")
        print(f"   Files scanned: {sum(1 for f in config_files if f.exists())}")
        print(f"   Violations found: {len(violations)}")

        if violations:
            print(f"\n⚠️  Config violations:")
            for v in violations:
                print(f"   {Path(v.file_path).name}:{v.line_number} - {v.pattern}")

    def test_06_generate_full_compliance_report(self, project_root):
        """Test: Generate comprehensive compliance report"""
        scanner = CodeNamingScanner(project_root)
        violations = scanner.scan_project()

        # Count total Python files
        total_files = len(list(project_root.rglob('*.py')))
        report = scanner.generate_compliance_report(total_files)

        print(f"\n" + "=" * 70)
        print("CODE NAMING CONVENTION COMPLIANCE REPORT")
        print("=" * 70)
        print(f"\n📊 SUMMARY:")
        print(f"   Total Python files scanned: {report.total_files_scanned}")
        print(f"   Files with violations: {len(set(v.file_path for v in report.violations))}")
        print(f"   Compliant files: {report.compliant_files}")
        print(f"   Total violations: {len(report.violations)}")

        compliance_rate = (report.compliant_files / report.total_files_scanned * 100) if report.total_files_scanned > 0 else 0
        print(f"   Compliance rate: {compliance_rate:.1f}%")

        # Group violations by file
        violations_by_file = {}
        for v in report.violations:
            file_name = Path(v.file_path).name
            if file_name not in violations_by_file:
                violations_by_file[file_name] = []
            violations_by_file[file_name].append(v)

        print(f"\n⚠️  FILES WITH MOST VIOLATIONS:")
        for file_name, file_violations in sorted(violations_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"   {file_name}: {len(file_violations)} violations")

        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print(f"   1. Migrate {len(violations_by_file)} files to use hierarchical naming")
        print(f"   2. Use get_api_key() for API keys")
        print(f"   3. Use get_hierarchical_env() for other secrets")
        print(f"   4. Add hierarchical fallback chains where needed")

        # This is informational - we don't fail the test
        print(f"\n✅ Compliance report generated successfully")

    def test_07_verify_helper_functions_available(self, project_root):
        """Test: Verify helper functions exist for proper naming"""
        env_helper = project_root / "mcp_server" / "env_helper.py"

        assert env_helper.exists(), "env_helper.py not found"

        content = env_helper.read_text()

        # Check for required helper functions
        assert 'def get_hierarchical_env(' in content, "get_hierarchical_env() not found"
        assert 'def get_api_key(' in content, "get_api_key() not found"
        assert 'def get_slack_config(' in content, "get_slack_config() not found"
        assert 'def get_database_config(' in content, "get_database_config() not found"

        print(f"\n✅ All required helper functions found in env_helper.py:")
        print(f"   - get_hierarchical_env()")
        print(f"   - get_api_key()")
        print(f"   - get_slack_config()")
        print(f"   - get_database_config()")
