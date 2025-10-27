#!/usr/bin/env python3
"""
Test script to verify Ollama can interact with NBA MCP tools.
This demonstrates how local LLMs can use your MCP server.
"""

import asyncio
import json
import pytest
from openai import OpenAI

# Connect to Ollama's OpenAI-compatible endpoint
ollama = OpenAI(
    base_url="http://34.226.246.126:11434/v1",
    api_key="ollama",  # Ollama doesn't need a real key
)


@pytest.mark.asyncio
async def test_ollama_connection():
    """Test basic Ollama connectivity."""
    print("🔍 Testing Ollama Connection...")

    try:
        response = ollama.chat.completions.create(
            model="qwen2.5-coder:32b",
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello! I am running on Ollama locally.' in one sentence.",
                }
            ],
            temperature=0.7,
            max_tokens=100,
        )

        print(f"✅ Ollama Response: {response.choices[0].message.content}\n")
        return True
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}\n")
        return False


@pytest.mark.asyncio
async def test_mcp_server():
    """Test MCP server availability."""
    print("🔍 Testing MCP Server...")

    try:
        from mcp_server.fastmcp_server import mcp

        tools = await mcp.list_tools()
        print(f"✅ MCP Server has {len(tools)} tools available")
        print(f"   Sample tools: {', '.join([t.name for t in tools[:5]])}\n")
        return True
    except Exception as e:
        print(f"❌ MCP server test failed: {e}\n")
        return False


async def demonstrate_integration():
    """Demonstrate Ollama with MCP context."""
    print("🎯 Demonstrating Ollama + MCP Integration...")
    print("-" * 60)

    # Get MCP tools
    from mcp_server.fastmcp_server import mcp

    tools = await mcp.list_tools()

    # Create a context-rich prompt
    tool_list = "\n".join([f"- {t.name}: {t.description}" for t in tools[:10]])

    prompt = f"""You are an AI assistant with access to NBA data tools.

Available MCP Tools (showing 10 of {len(tools)}):
{tool_list}

Question: What kinds of NBA data can you help me analyze?
Answer briefly in 2-3 sentences."""

    try:
        response = ollama.chat.completions.create(
            model="qwen2.5-coder:32b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )

        print(f"\n📝 Ollama's Response:")
        print(f"{response.choices[0].message.content}\n")
        print("✅ Integration working! Ollama understands MCP context.\n")
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}\n")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Ollama + MCP Integration Test")
    print("=" * 60)
    print()

    results = []

    # Test 1: Ollama connectivity
    results.append(await test_ollama_connection())

    # Test 2: MCP server
    results.append(await test_mcp_server())

    # Test 3: Integration
    results.append(await demonstrate_integration())

    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Ollama Connection: {'PASS' if results[0] else 'FAIL'}")
    print(f"✅ MCP Server: {'PASS' if results[1] else 'FAIL'}")
    print(f"✅ Integration: {'PASS' if results[2] else 'FAIL'}")
    print()

    if all(results):
        print("🎉 All tests passed! You can now use Ollama with MCP in Cursor.")
        print()
        print("Next steps:")
        print("1. Reload Cursor window (Cmd+Shift+P → 'Reload Window')")
        print("2. Look for model selector in chat interface")
        print("3. Switch from Claude to Ollama (qwen2.5-coder:32b)")
        print("4. Ask: 'What MCP tools are available?'")
    else:
        print("⚠️  Some tests failed. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
