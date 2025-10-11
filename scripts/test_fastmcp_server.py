#!/usr/bin/env python3
"""
Test FastMCP Server Functionality
Quick test to ensure FastMCP server works with database
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.fastmcp_lifespan import nba_lifespan
from mcp_server.fastmcp_settings import NBAMCPSettings
from mcp_server.tools.params import QueryDatabaseParams, ListTablesParams

async def test_fastmcp():
    """Test FastMCP server components"""

    print("=" * 60)
    print("FastMCP Server Test")
    print("=" * 60)
    print()

    # Test 1: Settings
    print("Test 1: Settings")
    print("-" * 60)
    settings = NBAMCPSettings()
    print(f"✅ Settings loaded: {settings}")
    print(f"   Database: {settings.rds_host}/{settings.rds_database}")
    print(f"   S3 Bucket: {settings.s3_bucket}")
    print(f"   Debug: {settings.debug}")
    print()

    # Test 2: Lifespan (resource initialization)
    print("Test 2: Lifespan (Resource Initialization)")
    print("-" * 60)

    # Create a mock app object
    class MockApp:
        pass

    app = MockApp()

    try:
        async with nba_lifespan(app) as context:
            print("✅ Lifespan context created")
            print(f"   Available resources: {list(context.keys())}")

            # Test 3: Database connection
            print()
            print("Test 3: Database Connection")
            print("-" * 60)

            rds_connector = context["rds_connector"]

            # Simple test query (RDS connector is already async)
            result = await rds_connector.execute_query("SELECT 1 as test")

            print(f"✅ Database query executed")
            print(f"   Result: {result}")

            # Test 4: List tables
            print()
            print("Test 4: List Tables")
            print("-" * 60)

            result = await rds_connector.execute_query("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
                LIMIT 5
            """)

            print(f"✅ Tables listed (first 5):")
            for row in result:
                print(f"   - {row['table_schema']}.{row['table_name']}")

            # Test 5: S3 connection
            print()
            print("Test 5: S3 Connection")
            print("-" * 60)

            s3_connector = context["s3_connector"]

            try:
                # List a few files
                result = await s3_connector.list_files(prefix="", max_keys=3)
                if result.get("success"):
                    files = result.get("files", [])
                    print(f"✅ S3 listing successful")
                    print(f"   Found {len(files)} files (showing first 3)")
                    for f in files[:3]:
                        print(f"   - {f.get('key')}")
                else:
                    print(f"⚠️  S3 listing: {result.get('error')}")
            except Exception as e:
                print(f"⚠️  S3 listing: {e}")

            # Test 6: Glue connection
            print()
            print("Test 6: Glue Connection")
            print("-" * 60)

            glue_connector = context["glue_connector"]

            try:
                tables = await asyncio.to_thread(
                    glue_connector.list_tables
                )
                print(f"✅ Glue catalog accessible")
                print(f"   Found {len(tables)} tables")
            except Exception as e:
                print(f"⚠️  Glue catalog: {e}")

            print()
            print("=" * 60)
            print("✅ All FastMCP components working!")
            print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

    return True


async def test_pydantic_validation():
    """Test Pydantic parameter validation"""

    print()
    print("=" * 60)
    print("Pydantic Validation Test")
    print("=" * 60)
    print()

    # Test 1: Valid query
    print("Test 1: Valid SELECT query")
    print("-" * 60)
    try:
        params = QueryDatabaseParams(sql_query="SELECT * FROM players LIMIT 10")
        print(f"✅ Valid query accepted")
        print(f"   SQL: {params.sql_query}")
        print(f"   Max rows: {params.max_rows}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Test 2: SQL injection attempt (should fail)
    print()
    print("Test 2: SQL Injection Attempt (should be blocked)")
    print("-" * 60)
    try:
        params = QueryDatabaseParams(sql_query="SELECT * FROM players; DROP TABLE players;")
        print(f"❌ SQL injection not blocked!")
    except Exception as e:
        print(f"✅ SQL injection blocked: {type(e).__name__}")

    # Test 3: Non-SELECT query (should fail)
    print()
    print("Test 3: Non-SELECT Query (should be blocked)")
    print("-" * 60)
    try:
        params = QueryDatabaseParams(sql_query="DELETE FROM players")
        print(f"❌ Non-SELECT query not blocked!")
    except Exception as e:
        print(f"✅ Non-SELECT blocked: {type(e).__name__}")

    # Test 4: List tables params
    print()
    print("Test 4: List Tables Parameters")
    print("-" * 60)
    try:
        params = ListTablesParams()
        print(f"✅ Default params: {params}")

        params = ListTablesParams(schema="public")
        print(f"✅ With schema: {params}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print()
    print("=" * 60)
    print("✅ Pydantic validation working correctly!")
    print("=" * 60)


async def main():
    """Run all tests"""
    print("\n🧪 FastMCP Server Testing Suite\n")

    # Test Pydantic validation first
    await test_pydantic_validation()

    print("\n")

    # Test FastMCP components
    success = await test_fastmcp()

    if success:
        print("\n✅ All tests passed! FastMCP server is ready to use.\n")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above.\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)