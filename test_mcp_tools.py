#!/usr/bin/env python3
"""Quick test to verify MCP server tools are accessible."""

import asyncio
from mcp_server.fastmcp_server import mcp

async def main():
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




