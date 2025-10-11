#!/usr/bin/env python3
"""
Deployment Validation Script
Validates FastMCP server deployment before going live

Usage:
    python scripts/validate_deployment.py
    python scripts/validate_deployment.py --strict
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ValidationCheck:
    """Single validation check"""

    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.message = ""
        self.critical = False


class DeploymentValidator:
    """Validates deployment readiness"""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.checks: List[ValidationCheck] = []

    def add_check(
        self,
        name: str,
        category: str,
        passed: bool,
        message: str,
        critical: bool = False
    ):
        """Add a validation check"""
        check = ValidationCheck(name, category)
        check.passed = passed
        check.message = message
        check.critical = critical
        self.checks.append(check)

    async def validate_environment(self):
        """Validate environment variables"""

        print("\n" + "=" * 60)
        print("1. Environment Configuration")
        print("=" * 60)

        try:
            # Try to load settings through pydantic-settings
            from mcp_server.fastmcp_settings import NBAMCPSettings

            settings = NBAMCPSettings()

            # Check if key settings are populated
            # (name, value, is_critical)
            checks = [
                ("RDS Host", settings.rds_host, True),
                ("RDS Port", str(settings.rds_port), True),
                ("RDS Database", settings.rds_database, True),
                ("RDS Username", settings.rds_username, True),
                ("RDS Password", "***" if settings.rds_password else "", False),  # Non-critical - may not be needed for local dev
                ("S3 Bucket", settings.s3_bucket, True),
                ("S3 Region", settings.s3_region, True),
                ("Glue Database", settings.glue_database, True),
            ]

            all_passed = True
            for name, value, is_critical in checks:
                passed = value is not None and len(str(value)) > 0
                if is_critical:
                    all_passed = all_passed and passed

                status = "✅" if passed else ("❌" if is_critical else "⚠️")
                display_value = "***" if "Password" in name else (value[:20] + "..." if len(str(value)) > 20 else value)
                print(f"  {status} {name}: {display_value if passed else 'Missing (optional)' if not is_critical else 'Missing'}")

                self.add_check(
                    name=f"Config: {name}",
                    category="Environment",
                    passed=passed,
                    message=f"{name} is {'configured' if passed else 'missing'}",
                    critical=is_critical
                )

            if all_passed:
                print(f"\n  ✅ All configuration loaded successfully")

        except Exception as e:
            print(f"  ❌ Failed to load settings: {e}")
            self.add_check(
                name="Settings initialization",
                category="Environment",
                passed=False,
                message=f"Failed to load settings: {e}",
                critical=True
            )

    async def validate_imports(self):
        """Validate Python imports"""

        print("\n" + "=" * 60)
        print("2. Python Dependencies")
        print("=" * 60)

        imports_to_check = [
            ("mcp.server.fastmcp", "FastMCP", True),
            ("pydantic", "BaseModel", True),
            ("asyncpg", None, False),  # Optional - handled by RDS connector
            ("boto3", None, True),
            ("mcp_server.fastmcp_server", "mcp", True),
            ("mcp_server.fastmcp_lifespan", "nba_lifespan", True),
            ("mcp_server.fastmcp_settings", "NBAMCPSettings", True),
        ]

        for module_name, attr_name, is_critical in imports_to_check:
            try:
                if attr_name:
                    module = __import__(module_name, fromlist=[attr_name])
                    getattr(module, attr_name)
                    import_str = f"{module_name}.{attr_name}"
                else:
                    __import__(module_name)
                    import_str = module_name

                print(f"  ✅ {import_str}")
                self.add_check(
                    name=f"Import: {import_str}",
                    category="Dependencies",
                    passed=True,
                    message=f"Successfully imported {import_str}",
                    critical=is_critical
                )

            except Exception as e:
                import_str = f"{module_name}.{attr_name}" if attr_name else module_name
                status = "❌" if is_critical else "⚠️"
                print(f"  {status} {import_str}: {e}")
                self.add_check(
                    name=f"Import: {import_str}",
                    category="Dependencies",
                    passed=False,
                    message=f"Failed to import {import_str}: {e}",
                    critical=is_critical
                )

    async def validate_database_connection(self):
        """Validate database connectivity"""

        print("\n" + "=" * 60)
        print("3. Database Connection")
        print("=" * 60)

        try:
            from mcp_server.fastmcp_lifespan import nba_lifespan

            class MockApp:
                pass

            app = MockApp()

            async with nba_lifespan(app) as context:
                rds_connector = context["rds_connector"]

                # Test connection
                result = await rds_connector.execute_query("SELECT 1 as test")

                if result and len(result) > 0:
                    print("  ✅ Database connection successful")
                    print(f"  ✅ Query execution working")

                    self.add_check(
                        name="Database connection",
                        category="Connectivity",
                        passed=True,
                        message="Successfully connected and queried database",
                        critical=True
                    )

                    # Test table access
                    tables = await rds_connector.execute_query("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        LIMIT 1
                    """)

                    if tables:
                        print(f"  ✅ Can access database tables")
                        self.add_check(
                            name="Database table access",
                            category="Connectivity",
                            passed=True,
                            message="Successfully accessed database tables"
                        )
                    else:
                        print(f"  ⚠️  No tables found in public schema")
                        self.add_check(
                            name="Database table access",
                            category="Connectivity",
                            passed=False,
                            message="No tables found in public schema"
                        )

                else:
                    raise Exception("Query returned no results")

        except Exception as e:
            print(f"  ❌ Database connection failed: {e}")
            self.add_check(
                name="Database connection",
                category="Connectivity",
                passed=False,
                message=f"Database connection failed: {e}",
                critical=True
            )

    async def validate_s3_connection(self):
        """Validate S3 connectivity"""

        print("\n" + "=" * 60)
        print("4. S3 Connection")
        print("=" * 60)

        try:
            from mcp_server.fastmcp_lifespan import nba_lifespan

            class MockApp:
                pass

            app = MockApp()

            async with nba_lifespan(app) as context:
                s3_connector = context["s3_connector"]

                # Test listing (using correct method name)
                result = await s3_connector.list_files(prefix="", max_keys=1)

                if result.get("success"):
                    print(f"  ✅ S3 connection successful")
                    print(f"  ✅ Can list files")

                    self.add_check(
                        name="S3 connection",
                        category="Connectivity",
                        passed=True,
                        message="Successfully connected to S3 and listed files"
                    )
                else:
                    raise Exception(result.get("error", "Unknown error"))

        except Exception as e:
            print(f"  ⚠️  S3 connection: {e}")
            self.add_check(
                name="S3 connection",
                category="Connectivity",
                passed=False,
                message=f"S3 connection failed: {e}",
                critical=False  # S3 is optional
            )

    async def validate_tools(self):
        """Validate MCP tools"""

        print("\n" + "=" * 60)
        print("5. MCP Tools")
        print("=" * 60)

        try:
            from mcp_server.fastmcp_server import mcp

            # Check tools are registered (await the coroutine)
            tools = await mcp.list_tools()

            expected_tools = [
                "query_database",
                "list_tables",
                "get_table_schema",
                "list_s3_files"
            ]

            for tool_name in expected_tools:
                found = any(t.name == tool_name for t in tools)

                status = "✅" if found else "❌"
                print(f"  {status} Tool registered: {tool_name}")

                self.add_check(
                    name=f"Tool: {tool_name}",
                    category="Tools",
                    passed=found,
                    message=f"Tool '{tool_name}' {'registered' if found else 'not found'}",
                    critical=True
                )

        except Exception as e:
            print(f"  ❌ Tool validation failed: {e}")
            self.add_check(
                name="Tool validation",
                category="Tools",
                passed=False,
                message=f"Failed to validate tools: {e}",
                critical=True
            )

    async def validate_pydantic_models(self):
        """Validate Pydantic validation"""

        print("\n" + "=" * 60)
        print("6. Input Validation (Pydantic)")
        print("=" * 60)

        try:
            from mcp_server.tools.params import QueryDatabaseParams

            # Test 1: Valid query
            try:
                params = QueryDatabaseParams(sql_query="SELECT * FROM players LIMIT 10")
                print("  ✅ Valid SELECT query accepted")
                self.add_check(
                    name="Pydantic: Valid query",
                    category="Validation",
                    passed=True,
                    message="Valid SELECT query accepted"
                )
            except Exception as e:
                print(f"  ❌ Valid query rejected: {e}")
                self.add_check(
                    name="Pydantic: Valid query",
                    category="Validation",
                    passed=False,
                    message=f"Valid query rejected: {e}",
                    critical=True
                )

            # Test 2: SQL injection blocked
            try:
                params = QueryDatabaseParams(sql_query="SELECT * FROM players; DROP TABLE players;")
                print("  ❌ SQL injection NOT blocked!")
                self.add_check(
                    name="Pydantic: SQL injection blocking",
                    category="Validation",
                    passed=False,
                    message="SQL injection not blocked!",
                    critical=True
                )
            except Exception:
                print("  ✅ SQL injection blocked")
                self.add_check(
                    name="Pydantic: SQL injection blocking",
                    category="Validation",
                    passed=True,
                    message="SQL injection properly blocked"
                )

            # Test 3: Non-SELECT blocked
            try:
                params = QueryDatabaseParams(sql_query="DELETE FROM players")
                print("  ❌ Non-SELECT query NOT blocked!")
                self.add_check(
                    name="Pydantic: Non-SELECT blocking",
                    category="Validation",
                    passed=False,
                    message="Non-SELECT query not blocked!",
                    critical=True
                )
            except Exception:
                print("  ✅ Non-SELECT query blocked")
                self.add_check(
                    name="Pydantic: Non-SELECT blocking",
                    category="Validation",
                    passed=True,
                    message="Non-SELECT queries properly blocked"
                )

        except Exception as e:
            print(f"  ❌ Pydantic validation failed: {e}")
            self.add_check(
                name="Pydantic validation",
                category="Validation",
                passed=False,
                message=f"Validation setup failed: {e}",
                critical=True
            )

    def print_summary(self):
        """Print validation summary"""

        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        # Count by category
        categories = {}
        for check in self.checks:
            if check.category not in categories:
                categories[check.category] = {"total": 0, "passed": 0, "critical": 0}

            categories[check.category]["total"] += 1
            if check.passed:
                categories[check.category]["passed"] += 1
            if check.critical and not check.passed:
                categories[check.category]["critical"] += 1

        # Print category summaries
        for category, counts in categories.items():
            passed = counts["passed"]
            total = counts["total"]
            critical = counts["critical"]

            status = "✅" if passed == total else "⚠️" if critical == 0 else "❌"
            print(f"\n{status} {category}: {passed}/{total} passed")

            if critical > 0:
                print(f"   ⚠️  {critical} critical failures")

        # Overall status
        total_checks = len(self.checks)
        passed_checks = sum(1 for c in self.checks if c.passed)
        critical_failures = sum(1 for c in self.checks if c.critical and not c.passed)

        print(f"\n{'=' * 60}")
        print(f"Overall: {passed_checks}/{total_checks} checks passed")

        if critical_failures > 0:
            print(f"❌ {critical_failures} critical failures - NOT READY FOR DEPLOYMENT")
            return False
        elif passed_checks == total_checks:
            print(f"✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
            return True
        else:
            if self.strict:
                print(f"⚠️  Some non-critical checks failed - NOT READY (strict mode)")
                return False
            else:
                print(f"⚠️  Some non-critical checks failed - DEPLOYMENT POSSIBLE")
                return True

    async def run_all_checks(self) -> bool:
        """Run all validation checks"""

        print("\n🔍 FastMCP Deployment Validation")
        print(f"Mode: {'Strict' if self.strict else 'Standard'}")

        await self.validate_environment()
        await self.validate_imports()
        await self.validate_database_connection()
        await self.validate_s3_connection()
        await self.validate_tools()
        await self.validate_pydantic_models()

        return self.print_summary()


async def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description="Validate FastMCP deployment")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: all checks must pass"
    )

    args = parser.parse_args()

    validator = DeploymentValidator(strict=args.strict)

    try:
        ready = await validator.run_all_checks()

        print("\n" + "=" * 60)

        if ready:
            print("\n✅ Deployment validation PASSED\n")
            return 0
        else:
            print("\n❌ Deployment validation FAILED\n")
            return 1

    except Exception as e:
        print(f"\n❌ Validation error: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
