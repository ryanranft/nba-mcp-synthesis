#!/usr/bin/env python3
"""
Quick test to verify MCP server tools are accessible.

Updated to work with the new unified secrets management system.
"""

import asyncio
import subprocess
import sys
from mcp_server.fastmcp_server import mcp

async def main():
    print("NBA MCP Server - Tool Verification")
    print("=" * 40)
    print("Using unified secrets management system")
    print()

    # Load secrets using hierarchical loader
    print("Loading secrets...")
    try:
        result = subprocess.run([
            sys.executable,
            "/Users/ryanranft/load_env_hierarchical.py",
            "nba-mcp-synthesis", "NBA", "production"
        ], capture_output=True, text=True, check=True)

        print("✅ Secrets loaded successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to load secrets: {e.stderr}")
        return 1
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return 1

    print(f"✓ MCP Server: {mcp.name}")

    tools = await mcp.list_tools()
    print(f"✓ Total MCP Tools: {len(tools)}")

    print("\n✓ Available NBA MCP Tools:")
    for i, tool in enumerate(tools[:10], 1):
        print(f"  {i}. {tool.name}")

    if len(tools) > 10:
        print(f"  ... and {len(tools) - 10} more tools")

    print("\n🎉 MCP Server is ready!")

if __name__ == "__main__":
    asyncio.run(main())




