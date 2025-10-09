#!/usr/bin/env python3
"""
Environment Validation Script
Validates all required environment variables and connections before deployment
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import boto3
import psycopg2
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()


class ValidationStatus(Enum):
    """Status of validation check"""
    PASS = "✅"
    FAIL = "❌"
    WARN = "⚠️"
    SKIP = "⏭️"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    category: str
    check: str
    status: ValidationStatus
    message: str
    required: bool = True


class EnvironmentValidator:
    """Validates environment configuration and connectivity"""

    def __init__(self, env_file: str = ".env"):
        """Initialize validator"""
        self.env_file = env_file
        self.results: List[ValidationResult] = []

        # Load environment
        if not load_dotenv(env_file):
            console.print(f"[yellow]Warning: Could not load {env_file}[/yellow]")

    def validate_all(self) -> bool:
        """Run all validation checks"""
        console.print(Panel.fit(
            "NBA MCP Synthesis - Environment Validation",
            style="bold white on blue"
        ))

        # Run all checks
        self.check_required_env_vars()
        self.check_optional_env_vars()
        self.check_aws_credentials()
        self.check_database_connection()
        self.check_s3_access()
        self.check_glue_access()
        self.check_api_keys()
        self.check_project_directories()
        self.check_python_dependencies()

        # Display results
        self.display_results()

        # Return overall status
        return self.get_overall_status()

    def check_required_env_vars(self):
        """Check required environment variables"""
        required_vars = [
            ("RDS_HOST", "Database hostname"),
            ("RDS_PORT", "Database port"),
            ("RDS_DATABASE", "Database name"),
            ("RDS_USERNAME", "Database username"),
            ("RDS_PASSWORD", "Database password"),
            ("S3_BUCKET", "S3 bucket name"),
            ("S3_REGION", "S3 region"),
            ("AWS_ACCESS_KEY_ID", "AWS access key"),
            ("AWS_SECRET_ACCESS_KEY", "AWS secret key"),
            ("DEEPSEEK_API_KEY", "DeepSeek API key"),
            ("ANTHROPIC_API_KEY", "Anthropic API key"),
        ]

        for var, description in required_vars:
            value = os.getenv(var)

            if not value:
                self.results.append(ValidationResult(
                    category="Environment Variables",
                    check=f"{var}",
                    status=ValidationStatus.FAIL,
                    message=f"Missing {description}",
                    required=True
                ))
            elif value.startswith("your_") or value == "your-":
                self.results.append(ValidationResult(
                    category="Environment Variables",
                    check=f"{var}",
                    status=ValidationStatus.FAIL,
                    message=f"Placeholder value detected",
                    required=True
                ))
            else:
                # Mask sensitive values
                display_value = value[:8] + "***" if len(value) > 8 else "***"
                self.results.append(ValidationResult(
                    category="Environment Variables",
                    check=f"{var}",
                    status=ValidationStatus.PASS,
                    message=f"Set ({display_value})",
                    required=True
                ))

    def check_optional_env_vars(self):
        """Check optional environment variables"""
        optional_vars = [
            ("GLUE_DATABASE", "AWS Glue database"),
            ("GLUE_REGION", "AWS Glue region"),
            ("OLLAMA_HOST", "Ollama server URL"),
            ("OLLAMA_MODEL", "Ollama model name"),
            ("SLACK_WEBHOOK_URL", "Slack webhook"),
            ("PROJECT_ROOT", "Project root directory"),
            ("SYNTHESIS_OUTPUT_DIR", "Output directory"),
        ]

        for var, description in optional_vars:
            value = os.getenv(var)

            if not value:
                self.results.append(ValidationResult(
                    category="Optional Variables",
                    check=f"{var}",
                    status=ValidationStatus.SKIP,
                    message=f"Not set (optional)",
                    required=False
                ))
            else:
                self.results.append(ValidationResult(
                    category="Optional Variables",
                    check=f"{var}",
                    status=ValidationStatus.PASS,
                    message=f"Set",
                    required=False
                ))

    def check_aws_credentials(self):
        """Verify AWS credentials are valid"""
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()

            self.results.append(ValidationResult(
                category="AWS Credentials",
                check="AWS Authentication",
                status=ValidationStatus.PASS,
                message=f"Valid (Account: {identity['Account']})",
                required=True
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                category="AWS Credentials",
                check="AWS Authentication",
                status=ValidationStatus.FAIL,
                message=f"Invalid: {str(e)}",
                required=True
            ))

    def check_database_connection(self):
        """Test database connectivity"""
        try:
            conn = psycopg2.connect(
                host=os.getenv('RDS_HOST'),
                port=os.getenv('RDS_PORT', 5432),
                database=os.getenv('RDS_DATABASE'),
                user=os.getenv('RDS_USERNAME'),
                password=os.getenv('RDS_PASSWORD'),
                connect_timeout=10
            )

            # Test query
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            table_count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            self.results.append(ValidationResult(
                category="Database",
                check="PostgreSQL Connection",
                status=ValidationStatus.PASS,
                message=f"Connected ({table_count} tables found)",
                required=True
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                category="Database",
                check="PostgreSQL Connection",
                status=ValidationStatus.FAIL,
                message=f"Failed: {str(e)[:50]}...",
                required=True
            ))

    def check_s3_access(self):
        """Test S3 bucket access"""
        try:
            s3 = boto3.client('s3', region_name=os.getenv('S3_REGION', 'us-east-1'))
            bucket = os.getenv('S3_BUCKET')

            # Try to list objects (limit 1)
            response = s3.list_objects_v2(Bucket=bucket, MaxKeys=1)

            object_count = response.get('KeyCount', 0)

            self.results.append(ValidationResult(
                category="AWS S3",
                check="S3 Bucket Access",
                status=ValidationStatus.PASS,
                message=f"Accessible (bucket: {bucket})",
                required=True
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                category="AWS S3",
                check="S3 Bucket Access",
                status=ValidationStatus.FAIL,
                message=f"Failed: {str(e)[:50]}...",
                required=True
            ))

    def check_glue_access(self):
        """Test AWS Glue access"""
        glue_db = os.getenv('GLUE_DATABASE')

        if not glue_db:
            self.results.append(ValidationResult(
                category="AWS Glue",
                check="Glue Database",
                status=ValidationStatus.SKIP,
                message="Not configured (optional)",
                required=False
            ))
            return

        try:
            glue = boto3.client('glue', region_name=os.getenv('GLUE_REGION', 'us-east-1'))
            response = glue.get_database(Name=glue_db)

            # Count tables
            tables_response = glue.get_tables(DatabaseName=glue_db)
            table_count = len(tables_response.get('TableList', []))

            self.results.append(ValidationResult(
                category="AWS Glue",
                check="Glue Database",
                status=ValidationStatus.PASS,
                message=f"Accessible ({table_count} tables)",
                required=False
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                category="AWS Glue",
                check="Glue Database",
                status=ValidationStatus.WARN,
                message=f"Failed: {str(e)[:50]}...",
                required=False
            ))

    def check_api_keys(self):
        """Validate API keys for AI models"""
        # DeepSeek
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        if deepseek_key and len(deepseek_key) > 10 and not deepseek_key.startswith('your_'):
            self.results.append(ValidationResult(
                category="API Keys",
                check="DeepSeek API Key",
                status=ValidationStatus.PASS,
                message=f"Set ({deepseek_key[:8]}***)",
                required=True
            ))
        else:
            self.results.append(ValidationResult(
                category="API Keys",
                check="DeepSeek API Key",
                status=ValidationStatus.FAIL,
                message="Invalid or missing",
                required=True
            ))

        # Anthropic
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and len(anthropic_key) > 10 and not anthropic_key.startswith('your_'):
            self.results.append(ValidationResult(
                category="API Keys",
                check="Anthropic API Key",
                status=ValidationStatus.PASS,
                message=f"Set ({anthropic_key[:8]}***)",
                required=True
            ))
        else:
            self.results.append(ValidationResult(
                category="API Keys",
                check="Anthropic API Key",
                status=ValidationStatus.FAIL,
                message="Invalid or missing",
                required=True
            ))

        # Ollama (optional)
        ollama_host = os.getenv('OLLAMA_HOST')
        if ollama_host:
            self.results.append(ValidationResult(
                category="API Keys",
                check="Ollama Server",
                status=ValidationStatus.PASS,
                message=f"Configured ({ollama_host})",
                required=False
            ))

    def check_project_directories(self):
        """Check required directories exist"""
        directories = [
            ("logs", "Log directory", True),
            ("synthesis_output", "Output directory", True),
            ("cache", "Cache directory", False),
        ]

        for dir_name, description, required in directories:
            dir_path = Path(dir_name)

            if dir_path.exists():
                self.results.append(ValidationResult(
                    category="Directories",
                    check=dir_name,
                    status=ValidationStatus.PASS,
                    message=f"Exists",
                    required=required
                ))
            else:
                # Try to create if required
                if required:
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        self.results.append(ValidationResult(
                            category="Directories",
                            check=dir_name,
                            status=ValidationStatus.PASS,
                            message=f"Created",
                            required=required
                        ))
                    except Exception as e:
                        self.results.append(ValidationResult(
                            category="Directories",
                            check=dir_name,
                            status=ValidationStatus.FAIL,
                            message=f"Cannot create: {e}",
                            required=required
                        ))
                else:
                    self.results.append(ValidationResult(
                        category="Directories",
                        check=dir_name,
                        status=ValidationStatus.SKIP,
                        message=f"Not created (optional)",
                        required=required
                    ))

    def check_python_dependencies(self):
        """Check critical Python packages are installed"""
        packages = [
            ("boto3", "AWS SDK"),
            ("psycopg2", "PostgreSQL client"),
            ("anthropic", "Anthropic SDK"),
            ("openai", "OpenAI SDK (for DeepSeek)"),
            ("rich", "Terminal formatting"),
            ("mcp", "MCP SDK"),
        ]

        for package, description in packages:
            try:
                __import__(package)
                self.results.append(ValidationResult(
                    category="Python Packages",
                    check=package,
                    status=ValidationStatus.PASS,
                    message="Installed",
                    required=True
                ))
            except ImportError:
                self.results.append(ValidationResult(
                    category="Python Packages",
                    check=package,
                    status=ValidationStatus.FAIL,
                    message="Not installed",
                    required=True
                ))

    def display_results(self):
        """Display validation results in a table"""
        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Display each category
        for category, checks in categories.items():
            console.print(f"\n[bold cyan]{category}[/bold cyan]")

            table = Table(show_header=True, header_style="bold")
            table.add_column("Check", style="white", width=30)
            table.add_column("Status", width=5)
            table.add_column("Message", style="dim")

            for result in checks:
                status_color = {
                    ValidationStatus.PASS: "green",
                    ValidationStatus.FAIL: "red",
                    ValidationStatus.WARN: "yellow",
                    ValidationStatus.SKIP: "dim"
                }[result.status]

                table.add_row(
                    result.check,
                    f"[{status_color}]{result.status.value}[/{status_color}]",
                    result.message
                )

            console.print(table)

    def get_overall_status(self) -> bool:
        """Get overall validation status"""
        # Check if any required checks failed
        failed_required = [r for r in self.results if r.required and r.status == ValidationStatus.FAIL]
        warnings = [r for r in self.results if r.status == ValidationStatus.WARN]

        console.print("\n" + "="*80 + "\n")

        if failed_required:
            console.print(Panel(
                f"[bold red]❌ Validation Failed[/bold red]\n\n"
                f"Failed checks: {len(failed_required)}\n"
                f"Warnings: {len(warnings)}\n\n"
                f"[yellow]Fix the failed checks before deployment.[/yellow]",
                style="red"
            ))

            # List failed checks
            console.print("\n[bold red]Failed Required Checks:[/bold red]")
            for result in failed_required:
                console.print(f"  ❌ {result.category} → {result.check}: {result.message}")

            return False

        elif warnings:
            console.print(Panel(
                f"[bold yellow]⚠️  Validation Passed with Warnings[/bold yellow]\n\n"
                f"Warnings: {len(warnings)}\n\n"
                f"[dim]System can proceed but some optional features may not work.[/dim]",
                style="yellow"
            ))
            return True

        else:
            console.print(Panel(
                f"[bold green]✅ All Validation Checks Passed[/bold green]\n\n"
                f"System is ready for deployment!",
                style="green"
            ))
            return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate NBA MCP Synthesis environment")
    parser.add_argument('--env-file', default='.env', help='Environment file to validate')
    parser.add_argument('--exit-on-failure', action='store_true',
                       help='Exit with non-zero code if validation fails')

    args = parser.parse_args()

    # Run validation
    validator = EnvironmentValidator(env_file=args.env_file)
    success = validator.validate_all()

    # Exit with appropriate code
    if args.exit_on_failure and not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
