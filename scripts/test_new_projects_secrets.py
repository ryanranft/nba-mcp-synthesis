#!/usr/bin/env python3
"""
Test script for new projects secret loading
Tests nba-simulator-aws and nba_mcp_synthesis_global secret loading
"""

import os
import sys
import subprocess
from pathlib import Path
from mcp_server.env_helper import get_hierarchical_env


def test_secret_loading(project, sport, context):
    """Test secret loading for a specific project"""
    print(f"\n🧪 Testing {project} ({context})...")

    # Load secrets using unified secrets manager directly
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from mcp_server.unified_secrets_manager import load_secrets_hierarchical

        success = load_secrets_hierarchical(project, sport, context)

        if success:
            print(f"✅ Secrets loaded successfully")
            return True
        else:
            print(f"❌ Failed to load secrets")
            return False
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return False


def test_environment_variables(project, context):
    """Test if environment variables are set correctly"""
    print(f"\n🔍 Checking environment variables for {project}...")

    # Define expected variables based on project
    if project == "nba-simulator-aws":
        expected_vars = [
            f"AWS_ACCESS_KEY_ID_NBA_SIMULATOR_AWS_{context}",
            f"AWS_SECRET_ACCESS_KEY_NBA_SIMULATOR_AWS_{context}",
            f"AWS_REGION_NBA_SIMULATOR_AWS_{context}",
            f"RDS_HOST_NBA_SIMULATOR_AWS_{context}",
            f"S3_BUCKET_NBA_SIMULATOR_AWS_{context}",
        ]
    elif project == "nba_mcp_synthesis_global":
        expected_vars = [
            f"TIMEZONE_GLOBAL_{context}",
            f"NBA_API_KEY_GLOBAL_{context}",
            f"SPORTSDATA_API_KEY_GLOBAL_{context}",
        ]
    else:
        print(f"❌ Unknown project: {project}")
        return False

    success_count = 0
    for var in expected_vars:
        value = get_hierarchical_env(
            var.split("_")[0] + "_" + "_".join(var.split("_")[1:-1]),
            "NBA_MCP_SYNTHESIS",
            context,
        )
        if value:
            print(
                f"✅ {var}: {value[:10]}..."
                if len(value) > 10
                else f"✅ {var}: {value}"
            )
            success_count += 1
        else:
            print(f"❌ {var}: Not set")

    print(
        f"\n📊 Success rate: {success_count}/{len(expected_vars)} ({success_count/len(expected_vars)*100:.1f}%)"
    )
    return success_count == len(expected_vars)


def main():
    """Main test function"""
    print("🚀 Testing New Projects Secret Loading")
    print("=" * 50)

    # Test nba-simulator-aws development
    success1 = test_secret_loading("nba-simulator-aws", "NBA", "DEVELOPMENT")
    if success1:
        test_environment_variables("nba-simulator-aws", "DEVELOPMENT")

    # Test nba_mcp_synthesis_global development
    success2 = test_secret_loading("nba_mcp_synthesis_global", "NBA", "DEVELOPMENT")
    if success2:
        test_environment_variables("nba_mcp_synthesis_global", "DEVELOPMENT")

    # Test nba_mcp_synthesis_global production
    success3 = test_secret_loading("nba_mcp_synthesis_global", "NBA", "WORKFLOW")
    if success3:
        test_environment_variables("nba_mcp_synthesis_global", "WORKFLOW")

    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"nba-simulator-aws (development): {'✅ PASS' if success1 else '❌ FAIL'}")
    print(
        f"nba_mcp_synthesis_global (development): {'✅ PASS' if success2 else '❌ FAIL'}"
    )
    print(
        f"nba_mcp_synthesis_global (production): {'✅ PASS' if success3 else '❌ FAIL'}"
    )

    overall_success = success1 and success2 and success3
    print(
        f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}"
    )

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
