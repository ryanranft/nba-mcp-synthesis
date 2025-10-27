#!/usr/bin/env python3
"""
Quick test script for hierarchical secrets management.

Usage:
    python test_secrets_hierarchical.py
    python test_secrets_hierarchical.py --project nba-simulator-aws
    python test_secrets_hierarchical.py --context DEVELOPMENT
"""

import sys
from pathlib import Path
import logging
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="Test hierarchical secrets management")
    parser.add_argument("--project", default="nba-mcp-synthesis", help="Project name")
    parser.add_argument("--sport", default="NBA", help="Sport name")
    parser.add_argument(
        "--context", default="WORKFLOW", help="Context (WORKFLOW/DEVELOPMENT/TEST)"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("🔐 Hierarchical Secrets Management Test")
    print("=" * 70)
    print(f"\nProject: {args.project}")
    print(f"Sport: {args.sport}")
    print(f"Context: {args.context}")
    print()

    # Step 1: Initialize secrets
    print("📥 Step 1: Loading secrets from hierarchical structure...")
    from mcp_server.secrets_loader import init_secrets

    success = init_secrets(project=args.project, sport=args.sport, context=args.context)

    if not success:
        print("❌ Failed to initialize secrets")
        print("\n💡 Troubleshooting:")
        print(f"1. Check that secrets exist at:")
        print(
            f"   /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/{args.sport}/{args.project}/"
        )
        print(f"2. Check file naming convention:")
        print(
            f"   SERVICE_RESOURCE_TYPE_{args.project.upper().replace('-', '_')}_{args.context}.env"
        )
        print(f"3. Check permissions (files: 600, dirs: 700)")
        return False

    print("✅ Secrets loaded successfully")

    # Step 2: Test accessing secrets
    print("\n🔍 Step 2: Testing secret access...")
    from mcp_server.env_helper import (
        get_api_key,
        get_database_config,
        get_aws_credential,
    )

    test_results = []

    # Test API keys
    api_keys = {
        "ANTHROPIC": get_api_key(
            "ANTHROPIC",
            project=args.project.upper().replace("-", "_"),
            context=args.context,
        ),
        "GOOGLE": get_api_key(
            "GOOGLE",
            project=args.project.upper().replace("-", "_"),
            context=args.context,
        ),
        "OPENAI": get_api_key(
            "OPENAI",
            project=args.project.upper().replace("-", "_"),
            context=args.context,
        ),
        "DEEPSEEK": get_api_key(
            "DEEPSEEK",
            project=args.project.upper().replace("-", "_"),
            context=args.context,
        ),
    }

    print("\n📋 API Keys:")
    for name, key in api_keys.items():
        if key:
            masked = f"{key[:10]}..." if len(key) > 10 else "***"
            print(f"  ✅ {name}_API_KEY: {masked}")
            test_results.append((name, True))
        else:
            print(f"  ❌ {name}_API_KEY: Not found")
            test_results.append((name, False))

    # Test database config
    print("\n🗄️  Database Config:")
    db_configs = ["RDS_HOST", "RDS_USERNAME", "RDS_PASSWORD", "RDS_DATABASE"]
    for config in db_configs:
        value = get_database_config(
            config, project=args.project.upper().replace("-", "_"), context=args.context
        )
        if value:
            masked = f"{value[:10]}..." if len(value) > 10 else "***"
            print(f"  ✅ {config}: {masked}")
        else:
            print(f"  ⚠️  {config}: Not found (optional)")

    # Test AWS credentials
    print("\n☁️  AWS Credentials:")
    aws_creds = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    for cred in aws_creds:
        value = get_aws_credential(
            cred, project=args.project.upper().replace("-", "_"), context=args.context
        )
        if value:
            masked = f"{value[:10]}..." if len(value) > 10 else "***"
            print(f"  ✅ {cred}: {masked}")
        else:
            print(f"  ⚠️  {cred}: Not found (optional)")

    # Step 3: Validate required secrets
    print("\n✔️  Step 3: Validating required secrets...")
    from mcp_server.env_helper import validate_required_envs

    required = ["ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    missing = validate_required_envs(
        required, project=args.project.upper().replace("-", "_"), context=args.context
    )

    if missing:
        print(f"  ❌ Missing required secrets: {missing}")
        print("\n💡 To fix:")
        for secret in missing:
            print(
                f"   Create file: {secret}_{args.project.upper().replace('-', '_')}_{args.context}.env"
            )
    else:
        print("  ✅ All required secrets present")

    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)

    total = len(test_results)
    passed = sum(1 for _, success in test_results if success)

    print(f"Total API keys tested: {total}")
    print(f"Found: {passed}")
    print(f"Missing: {total - passed}")

    if passed == total:
        print("\n🎉 All secrets loaded successfully!")
        return True
    elif passed > 0:
        print("\n⚠️  Some secrets loaded, but not all")
        print("This may be OK if you don't need all services")
        return True
    else:
        print("\n❌ No secrets found")
        print("\n📚 See SECRETS_MIGRATION_COMPLETE.md for setup instructions")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
