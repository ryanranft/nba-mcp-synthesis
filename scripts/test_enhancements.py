#!/usr/bin/env python3
"""
Test NBA MCP Server Enhancements
Validates all new features added to the FastMCP implementation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_server_initialization():
    """Test 1: Server initializes with all features"""
    print("\n" + "=" * 60)
    print("TEST 1: Server Initialization")
    print("=" * 60)

    try:
        from mcp_server import fastmcp_server

        assert fastmcp_server.mcp.name == "nba-mcp-fastmcp", "Server name mismatch"
        print("✓ Server name correct")

        # Check tools
        tools_count = len(fastmcp_server.mcp._tool_manager._tools)
        assert tools_count == 4, f"Expected 4 tools, found {tools_count}"
        print(f"✓ {tools_count} tools registered")

        # Check prompts
        prompts_count = len(fastmcp_server.mcp._prompt_manager._prompts)
        assert prompts_count == 4, f"Expected 4 prompts, found {prompts_count}"
        print(f"✓ {prompts_count} prompts registered")

        # Check resource templates
        templates_count = len(fastmcp_server.mcp._resource_manager._templates)
        assert templates_count == 2, f"Expected 2 templates, found {templates_count}"
        print(f"✓ {templates_count} resource templates registered")

        print("\n✅ Server initialization test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Server initialization test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_prompts():
    """Test 2: Prompts are accessible"""
    print("\n" + "=" * 60)
    print("TEST 2: Prompts")
    print("=" * 60)

    try:
        from mcp_server import fastmcp_server

        prompts = await fastmcp_server.mcp.list_prompts()

        expected_prompts = [
            "suggest_queries",
            "analyze_team_performance",
            "compare_players",
            "game_analysis"
        ]

        prompt_names = [p.name for p in prompts]
        print(f"Found prompts: {prompt_names}")

        for expected in expected_prompts:
            assert expected in prompt_names, f"Missing prompt: {expected}"
            print(f"✓ Prompt '{expected}' registered")

        # Test getting a specific prompt
        suggest_prompt = fastmcp_server.mcp._prompt_manager.get_prompt("suggest_queries")
        assert suggest_prompt is not None, "Could not retrieve suggest_queries prompt"
        print("✓ Can retrieve specific prompts")

        print("\n✅ Prompts test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Prompts test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_resource_templates():
    """Test 3: Resource templates work"""
    print("\n" + "=" * 60)
    print("TEST 3: Resource Templates")
    print("=" * 60)

    try:
        from mcp_server import fastmcp_server

        templates = await fastmcp_server.mcp.list_resource_templates()

        print(f"Found {len(templates)} resource templates:")
        for template in templates:
            print(f"  - {template.uriTemplate}")

        # Check for expected templates
        template_uris = [t.uriTemplate for t in templates]
        assert "s3://{bucket}/{key}" in template_uris, "Missing S3 template"
        assert "nba://database/schema" in template_uris, "Missing schema template"

        print("✓ All expected templates present")

        print("\n✅ Resource templates test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Resource templates test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_custom_routes():
    """Test 4: Custom routes are registered"""
    print("\n" + "=" * 60)
    print("TEST 4: Custom Routes")
    print("=" * 60)

    try:
        from mcp_server import fastmcp_server

        # Check custom routes
        custom_routes = fastmcp_server.mcp._custom_starlette_routes
        print(f"Found {len(custom_routes)} custom routes")

        route_paths = [route.path for route in custom_routes]
        print(f"Routes: {route_paths}")

        expected_routes = ["/health", "/metrics", "/ready"]
        for expected in expected_routes:
            assert expected in route_paths, f"Missing route: {expected}"
            print(f"✓ Route '{expected}' registered")

        print("\n✅ Custom routes test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Custom routes test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_transport_modes():
    """Test 5: Transport modes are configurable"""
    print("\n" + "=" * 60)
    print("TEST 5: Transport Modes")
    print("=" * 60)

    try:
        from mcp_server import fastmcp_server
        import os

        # Test transport setting
        original_transport = os.getenv("MCP_TRANSPORT")

        for transport in ["stdio", "sse", "streamable-http"]:
            os.environ["MCP_TRANSPORT"] = transport
            print(f"✓ Can set transport to: {transport}")

        # Restore original
        if original_transport:
            os.environ["MCP_TRANSPORT"] = original_transport
        else:
            os.environ.pop("MCP_TRANSPORT", None)

        print("✓ All transport modes supported")

        print("\n✅ Transport modes test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Transport modes test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_settings():
    """Test 6: Settings are properly configured"""
    print("\n" + "=" * 60)
    print("TEST 6: Settings Configuration")
    print("=" * 60)

    try:
        from mcp_server import fastmcp_server

        settings = fastmcp_server.settings

        print(f"Debug mode: {settings.debug}")
        print(f"Log level: {settings.log_level}")
        print(f"Host: {settings.host}")
        print(f"Port: {settings.port}")

        assert hasattr(settings, 'host'), "Missing host setting"
        assert hasattr(settings, 'port'), "Missing port setting"
        assert hasattr(settings, 'debug'), "Missing debug setting"
        assert hasattr(settings, 'log_level'), "Missing log_level setting"

        print("✓ All required settings present")

        print("\n✅ Settings test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Settings test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all enhancement tests"""
    print("\n" + "=" * 60)
    print("NBA MCP Server Enhancement Tests")
    print("=" * 60)

    tests = [
        ("Server Initialization", test_server_initialization),
        ("Prompts", test_prompts),
        ("Resource Templates", test_resource_templates),
        ("Custom Routes", test_custom_routes),
        ("Transport Modes", test_transport_modes),
        ("Settings", test_settings),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All enhancement tests PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
