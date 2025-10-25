#!/usr/bin/env python3
"""
Run overnight convergence with proper secrets loading
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical


def main():
    print("🔐 Loading secrets from hierarchical structure...")

    # Load secrets
    success = load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "WORKFLOW")

    if not success:
        print("❌ Failed to load secrets")
        return 1

    print("✅ Secrets loaded successfully")

    # Map hierarchical keys to simple keys expected by launch script
    key_mapping = {
        "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "GEMINI_API_KEY",
        "ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "CLAUDE_API_KEY",
        "OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "OPENAI_API_KEY",
        "DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW": "DEEPSEEK_API_KEY",
    }

    # Export simplified keys
    env = os.environ.copy()
    for hierarchical_key, simple_key in key_mapping.items():
        value = os.getenv(hierarchical_key)
        if value:
            env[simple_key] = value
            print(f"✅ Exported {simple_key}")

    # Verify required keys
    required_keys = ["GEMINI_API_KEY", "CLAUDE_API_KEY"]
    missing = [k for k in required_keys if k not in env]

    if missing:
        print(f"❌ Missing required keys: {', '.join(missing)}")
        return 1

    print("\n🚀 Launching overnight convergence...")
    print("")

    # Run the launch script with the environment
    # Provide "START" confirmation automatically
    script_path = Path(__file__).parent.parent / "launch_overnight_convergence.sh"

    result = subprocess.run(
        [str(script_path)],
        env=env,
        cwd=str(script_path.parent),
        input=b"START\n",  # Auto-confirm with START
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,
    )

    # Print output
    if result.stdout:
        print(result.stdout.decode("utf-8", errors="replace"))

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
