#!/usr/bin/env python3
"""
Naming Convention Enforcement Tool

This tool validates and enforces the context-rich naming convention for secrets:
{SERVICE}_{RESOURCE_TYPE}_{PROJECT}_{CONTEXT}

Examples:
- GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
- DB_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT
- SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import argparse


@dataclass
class NamingViolation:
    """Represents a naming convention violation"""

    file_path: str
    current_name: str
    suggested_name: str
    violation_type: str
    severity: str  # 'error', 'warning', 'info'


@dataclass
class ValidationResult:
    """Result of naming convention validation"""

    total_files: int
    compliant_files: int
    violations: List[NamingViolation]
    suggestions: Dict[str, str]


class NamingConventionEnforcer:
    """Enforces context-rich naming convention for secrets"""

    def __init__(
        self, base_path: str = "/Users/ryanranft/Desktop/++/big_cat_bets_assets"
    ):
        self.base_path = Path(base_path)

        # Define valid components
        self.valid_services = {
            "GOOGLE",
            "ANTHROPIC",
            "OPENAI",
            "DEEPSEEK",
            "OLLAMA",
            "SLACK",
            "LINEAR",
            "GITHUB",
            "DISCORD",
            "DB",
            "AWS",
            "REDIS",
            "POSTGRES",
            "MYSQL",
            "JWT",
            "OAUTH",
            "API",
        }

        self.valid_resource_types = {
            "API_KEY",
            "SECRET_KEY",
            "ACCESS_KEY",
            "PRIVATE_KEY",
            "PASSWORD",
            "TOKEN",
            "CERTIFICATE",
            "CREDENTIAL",
            "WEBHOOK_URL",
            "CONNECTION_STRING",
            "ENDPOINT",
            "HOST",
            "PORT",
            "DATABASE",
            "USERNAME",
            "USER",
        }

        self.valid_projects = {
            "NBA_MCP_SYNTHESIS",
            "NBA_SIMULATOR_AWS",
            "BIG_CAT_BETS_GLOBAL",
            "MLB_SIMULATOR",
            "NFL_SIMULATOR",
            "NHL_SIMULATOR",
            "BIG_CAT_BETS_NOTIFICATIONS",
            "BIG_CAT_BETS_HFT",
        }

        self.valid_contexts = {
            "WORKFLOW",
            "DEVELOPMENT",
            "TEST",
            "STAGING",
            "PRODUCTION",
        }

        # Common mappings for migration
        self.migration_mappings = {
            "GOOGLE_API_KEY": "GOOGLE_API_KEY",
            "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY": "OPENAI_API_KEY",
            "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY",
            "DB_PASSWORD": "DB_PASSWORD",
            "DB_HOST": "DB_HOST",
            "DB_PORT": "DB_PORT",
            "DB_NAME": "DB_NAME",
            "DB_USER": "DB_USER",
            "SLACK_WEBHOOK_URL": "SLACK_WEBHOOK_URL",
            "LINEAR_API_KEY": "LINEAR_API_KEY",
            "LINEAR_TEAM_ID": "LINEAR_TEAM_ID",
            "LINEAR_PROJECT_ID": "LINEAR_PROJECT_ID",
            "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY",
            "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_KEY",
            "S3_BUCKET": "S3_BUCKET",
            "RDS_HOST": "DB_HOST",
            "RDS_DATABASE": "DB_NAME",
            "RDS_USERNAME": "DB_USER",
            "RDS_PASSWORD": "DB_PASSWORD",
        }

    def validate_all_secrets(self) -> ValidationResult:
        """Validate naming convention for all secrets in the hierarchy"""
        violations = []
        suggestions = {}
        total_files = 0
        compliant_files = 0

        # Walk through all .env files in the hierarchy
        for env_file in self.base_path.rglob("*.env"):
            total_files += 1

            # Skip placeholder directories
            if "_placeholder" in str(env_file):
                continue

            secret_name = env_file.stem.upper()

            # Validate naming convention
            violation = self._validate_secret_name(secret_name, str(env_file))

            if violation:
                violations.append(violation)
                suggestions[secret_name] = violation.suggested_name
            else:
                compliant_files += 1

        return ValidationResult(
            total_files=total_files,
            compliant_files=compliant_files,
            violations=violations,
            suggestions=suggestions,
        )

    def _validate_secret_name(
        self, name: str, file_path: str
    ) -> Optional[NamingViolation]:
        """Validate a single secret name against naming convention"""

        # Skip if already follows convention
        if self._is_compliant_name(name):
            return None

        # Generate suggestion
        suggested_name = self._generate_suggested_name(name, file_path)

        # Determine violation type and severity
        violation_type, severity = self._classify_violation(name)

        return NamingViolation(
            file_path=file_path,
            current_name=name,
            suggested_name=suggested_name,
            violation_type=violation_type,
            severity=severity,
        )

    def _is_compliant_name(self, name: str) -> bool:
        """Check if name follows the naming convention"""
        parts = name.split("_")

        # Must have at least 4 parts
        if len(parts) < 4:
            return False

        # Check for required components
        has_service = any(part in self.valid_services for part in parts)
        has_resource_type = any(part in self.valid_resource_types for part in parts)
        has_context = any(part in self.valid_contexts for part in parts)

        return has_service and has_resource_type and has_context

    def _generate_suggested_name(self, name: str, file_path: str) -> str:
        """Generate a suggested name following the convention"""

        # Try to extract components from current name
        parts = name.split("_")

        # Identify service
        service = None
        for part in parts:
            if part in self.valid_services:
                service = part
                break

        # Identify resource type
        resource_type = None
        for part in parts:
            if part in self.valid_resource_types:
                resource_type = part
                break

        # Determine project from file path
        project = self._extract_project_from_path(file_path)

        # Determine context from file path
        context = self._extract_context_from_path(file_path)

        # Use migration mappings for common cases
        if name in self.migration_mappings:
            base_name = self.migration_mappings[name]
            return f"{base_name}_{project}_{context}"

        # Generate from components
        if service and resource_type and project and context:
            return f"{service}_{resource_type}_{project}_{context}"

        # Fallback: try to construct from what we have
        components = []
        if service:
            components.append(service)
        if resource_type:
            components.append(resource_type)
        else:
            components.append("SECRET")  # Generic fallback

        if project:
            components.append(project)
        else:
            components.append("UNKNOWN_PROJECT")

        if context:
            components.append(context)
        else:
            components.append("WORKFLOW")  # Default context

        return "_".join(components)

    def _extract_project_from_path(self, file_path: str) -> str:
        """Extract project name from file path"""
        path_parts = Path(file_path).parts

        # Look for project indicators in path
        for part in reversed(path_parts):
            if part.startswith(".env."):
                # Extract project from .env.{project}.{context}
                env_parts = part.split(".")
                if len(env_parts) >= 3:
                    project_part = env_parts[1]
                    return project_part.upper().replace("-", "_")

            # Check for known project directories
            if "nba-mcp-synthesis" in part:
                return "NBA_MCP_SYNTHESIS"
            elif "nba-simulator-aws" in part:
                return "NBA_SIMULATOR_AWS"
            elif "big_cat_bets_global" in part:
                return "BIG_CAT_BETS_GLOBAL"
            elif "big_cat_bets_notifications" in part:
                return "BIG_CAT_BETS_NOTIFICATIONS"
            elif "big_cat_bets_hft" in part:
                return "BIG_CAT_BETS_HFT"

        return "UNKNOWN_PROJECT"

    def _extract_context_from_path(self, file_path: str) -> str:
        """Extract context from file path"""
        path_parts = Path(file_path).parts

        # Look for context in directory names
        for part in reversed(path_parts):
            if part.startswith(".env."):
                # Extract context from .env.{project}.{context}
                env_parts = part.split(".")
                if len(env_parts) >= 3:
                    context_part = env_parts[2]
                    return context_part.upper()

            # Check for context directories
            if part in ["production", "development", "test", "staging"]:
                return part.upper()

        return "WORKFLOW"  # Default context

    def _classify_violation(self, name: str) -> Tuple[str, str]:
        """Classify the type and severity of a naming violation"""

        parts = name.split("_")

        # Check for common issues
        if len(parts) < 2:
            return "too_short", "error"
        elif len(parts) == 2:
            return "missing_project_context", "error"
        elif len(parts) == 3:
            return "missing_context", "warning"
        elif not any(part in self.valid_services for part in parts):
            return "unknown_service", "warning"
        elif not any(part in self.valid_resource_types for part in parts):
            return "unknown_resource_type", "warning"
        else:
            return "format_issue", "info"

    def generate_compliance_report(self, result: ValidationResult) -> str:
        """Generate a human-readable compliance report"""

        report = []
        report.append("=" * 60)
        report.append("NAMING CONVENTION COMPLIANCE REPORT")
        report.append("=" * 60)
        report.append("")

        # Summary
        compliance_rate = (
            (result.compliant_files / result.total_files * 100)
            if result.total_files > 0
            else 0
        )
        report.append(f"📊 SUMMARY:")
        report.append(f"   Total files scanned: {result.total_files}")
        report.append(f"   Compliant files: {result.compliant_files}")
        report.append(f"   Violations found: {len(result.violations)}")
        report.append(f"   Compliance rate: {compliance_rate:.1f}%")
        report.append("")

        # Violations by severity
        errors = [v for v in result.violations if v.severity == "error"]
        warnings = [v for v in result.violations if v.severity == "warning"]
        infos = [v for v in result.violations if v.severity == "info"]

        if errors:
            report.append(f"❌ ERRORS ({len(errors)}):")
            for violation in errors:
                report.append(f"   {violation.current_name}")
                report.append(f"      File: {violation.file_path}")
                report.append(f"      Suggested: {violation.suggested_name}")
                report.append("")

        if warnings:
            report.append(f"⚠️  WARNINGS ({len(warnings)}):")
            for violation in warnings:
                report.append(f"   {violation.current_name}")
                report.append(f"      File: {violation.file_path}")
                report.append(f"      Suggested: {violation.suggested_name}")
                report.append("")

        if infos:
            report.append(f"ℹ️  INFO ({len(infos)}):")
            for violation in infos:
                report.append(f"   {violation.current_name}")
                report.append(f"      File: {violation.file_path}")
                report.append(f"      Suggested: {violation.suggested_name}")
                report.append("")

        # Recommendations
        report.append("🔧 RECOMMENDATIONS:")
        if errors:
            report.append("   1. Fix all ERROR violations immediately")
        if warnings:
            report.append("   2. Address WARNING violations for better consistency")
        if infos:
            report.append("   3. Consider updating INFO violations when convenient")

        report.append("   4. Use the migration tool to automatically rename files")
        report.append("   5. Update code references to use new naming convention")
        report.append("")

        return "\n".join(report)

    def create_migration_script(
        self,
        result: ValidationResult,
        output_file: str = "migrate_naming_convention.sh",
    ) -> str:
        """Create a shell script to migrate files to new naming convention"""

        script_lines = [
            "#!/bin/bash",
            "# Auto-generated migration script for naming convention",
            "# Generated by naming_convention_enforcer.py",
            "",
            "set -e  # Exit on any error",
            "",
            "echo '🔄 Starting naming convention migration...'",
            "",
            "# Create backup directory",
            'BACKUP_DIR="/Users/ryanranft/Desktop/++/.migration_backup/$(date +%Y%m%d_%H%M%S)"',
            'mkdir -p "$BACKUP_DIR"',
            'echo "📁 Backup directory: $BACKUP_DIR"',
            "",
        ]

        # Add migration commands
        for violation in result.violations:
            if violation.severity in [
                "error",
                "warning",
            ]:  # Only migrate errors and warnings
                old_path = violation.file_path
                new_path = old_path.replace(
                    violation.current_name.lower(), violation.suggested_name.lower()
                )

                script_lines.extend(
                    [
                        f"# Migrate {violation.current_name}",
                        f'if [ -f "{old_path}" ]; then',
                        f'    echo "📝 Migrating {violation.current_name} -> {violation.suggested_name}"',
                        f'    cp "{old_path}" "$BACKUP_DIR/"',
                        f'    mv "{old_path}" "{new_path}"',
                        f'    echo "✅ Migrated successfully"',
                        f"else",
                        f'    echo "⚠️  File not found: {old_path}"',
                        f"fi",
                        "",
                    ]
                )

        script_lines.extend(
            [
                "echo '✅ Migration complete!'",
                'echo "📁 Backup location: $BACKUP_DIR"',
                "echo '🔍 Run validation again to verify compliance'",
            ]
        )

        script_content = "\n".join(script_lines)

        # Write script file
        with open(output_file, "w") as f:
            f.write(script_content)

        # Make executable
        os.chmod(output_file, 0o755)

        return script_content


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Enforce naming convention for secrets"
    )
    parser.add_argument(
        "--base-path",
        default="/Users/ryanranft/Desktop/++/big_cat_bets_assets",
        help="Base path for secrets hierarchy",
    )
    parser.add_argument(
        "--generate-migration", action="store_true", help="Generate migration script"
    )
    parser.add_argument(
        "--output", default="migration_report.txt", help="Output file for report"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Create enforcer
    enforcer = NamingConventionEnforcer(args.base_path)

    # Validate all secrets
    print("🔍 Validating naming convention compliance...")
    result = enforcer.validate_all_secrets()

    # Generate report
    report = enforcer.generate_compliance_report(result)

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"📄 Report saved to: {args.output}")
    else:
        print(report)

    # Generate migration script if requested
    if args.generate_migration:
        script_content = enforcer.create_migration_script(result)
        print("🔧 Migration script generated: migrate_naming_convention.sh")
        print("   Run: ./migrate_naming_convention.sh")

    # Exit with error code if violations found
    if result.violations:
        error_count = len([v for v in result.violations if v.severity == "error"])
        if error_count > 0:
            print(f"\n❌ Found {error_count} errors. Please fix before proceeding.")
            exit(1)
        else:
            print(
                f"\n⚠️  Found {len(result.violations)} violations. Consider fixing for better compliance."
            )
            exit(0)
    else:
        print("\n✅ All secrets follow naming convention!")
        exit(0)


if __name__ == "__main__":
    main()
