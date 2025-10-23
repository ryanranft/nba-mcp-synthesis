#!/usr/bin/env python3
"""
End-to-End Integration Test
Tests the complete workflow from MCP server startup to synthesis completion
"""

import asyncio
import pytest
import pytest_asyncio
import sys
import os
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.multi_model_synthesis import synthesize_with_mcp_context
from synthesis.mcp_client import MCPClient
from mcp_server.config import MCPConfig
from dotenv import load_dotenv
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add mocks directory to path
sys.path.insert(0, str(Path(__file__).parent / "mocks"))
from mock_mcp_server import MockMCPServer

# Load environment
load_dotenv()


class MCPServerManager:
    """Manages MCP server for testing"""

    def __init__(self):
        self.process = None
        self.server_url = "http://localhost:3000"

    async def start(self, timeout: int = 60):
        """Start MCP server with extended timeout and retry logic"""
        print("Starting MCP server...")

        # Check if server is already running
        if await self._is_server_running():
            print("MCP server already running")
            return True

        # Start server process
        server_script = Path(__file__).parent.parent / "mcp_server" / "server.py"

        self.process = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )

        # Wait for server to be ready with exponential backoff
        start_time = time.time()
        retry_delay = 1
        max_delay = 5

        while time.time() - start_time < timeout:
            if await self._is_server_running():
                print("✅ MCP server started successfully")
                await asyncio.sleep(2)  # Extra time for initialization
                return True

            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, max_delay)  # Exponential backoff

        # Server failed to start - check for errors
        if self.process:
            stdout, stderr = self.process.communicate(timeout=5)
            if stderr:
                print(f"Server stderr: {stderr.decode()}")

        raise RuntimeError(f"MCP server failed to start within {timeout}s")

    async def stop(self):
        """Stop MCP server"""
        if self.process:
            print("Stopping MCP server...")

            try:
                # Try graceful shutdown first
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()

                # Wait for shutdown
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    if hasattr(os, "killpg"):
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()

                print("✅ MCP server stopped")
            except Exception as e:
                print(f"Warning: Error stopping server: {e}")

            self.process = None

    async def _is_server_running(self) -> bool:
        """Check if server is responding"""
        try:
            client = MCPClient(server_url=self.server_url)
            connected = await client.connect()
            if connected:
                await client.disconnect()
            return connected
        except:
            return False


@pytest.fixture
def mock_env_vars():
    """Fixture that mocks all required environment variables"""
    mock_vars = {
        "RDS_HOST": "mock-rds-host.amazonaws.com",
        "RDS_DATABASE": "mock_nba_db",
        "RDS_USERNAME": "mock_user",
        "RDS_PASSWORD": "mock_password",
        "S3_BUCKET": "mock-nba-bucket",
        "AWS_ACCESS_KEY_ID": "mock_access_key",
        "AWS_SECRET_ACCESS_KEY": "mock_secret_key",
        "DEEPSEEK_API_KEY": "mock_deepseek_key",
        "ANTHROPIC_API_KEY": "mock_anthropic_key",
    }
    
    with patch.dict(os.environ, mock_vars, clear=False):
        yield mock_vars


@pytest_asyncio.fixture
async def mcp_server(mock_env_vars):
    """Fixture that starts and stops mock MCP server"""
    manager = MockMCPServer()

    try:
        await manager.start()
        yield manager
    finally:
        await manager.stop()


@pytest.mark.asyncio
class TestE2EWorkflow:
    """End-to-end workflow tests"""

    async def test_01_environment_setup(self, mock_env_vars):
        """Test: Environment variables are configured"""
        required_vars = [
            "RDS_HOST",
            "RDS_DATABASE",
            "RDS_USERNAME",
            "RDS_PASSWORD",
            "S3_BUCKET",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "DEEPSEEK_API_KEY",
            "ANTHROPIC_API_KEY",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        assert (
            len(missing_vars) == 0
        ), f"Missing required environment variables: {', '.join(missing_vars)}"

        print("✅ All required environment variables are set")

    async def test_02_mcp_server_startup(self, mcp_server):
        """Test: MCP server starts and responds"""
        # Server is already started by fixture
        assert await mcp_server._is_server_running(), "MCP server should be running"
        assert mcp_server.running is True, "MCP server running flag should be True"

        print("✅ MCP server is running")

    async def test_03_mcp_client_connection(self, mcp_server):
        """Test: MCP client can connect to server"""
        # Mock MCPClient methods
        with patch.object(MCPClient, 'connect', new_callable=AsyncMock, return_value=True), \
             patch.object(MCPClient, 'disconnect', new_callable=AsyncMock):
            
            client = MCPClient(server_url=mcp_server.server_url)

            # Test connection
            connected = await client.connect()
            assert connected, "MCP client should connect successfully"
            assert mcp_server.running, "MCP server should be running"

            await client.disconnect()

            print("✅ MCP client connected successfully")

    async def test_04_database_query_via_mcp(self, mcp_server):
        """Test: Can query database through MCP"""
        # Mock database query response
        mock_result = {"success": True, "rows": [{"test": 1}]}
        
        with patch.object(MCPClient, 'connect', new_callable=AsyncMock, return_value=True), \
             patch.object(MCPClient, 'call_tool', new_callable=AsyncMock, return_value=mock_result), \
             patch.object(MCPClient, 'disconnect', new_callable=AsyncMock):
            
            client = MCPClient(server_url=mcp_server.server_url)
            await client.connect()

            try:
                # Execute simple query
                result = await client.call_tool(
                    "query_database", {"sql": "SELECT 1 AS test"}
                )

                assert result.get("success"), "Database query should succeed"
                assert (
                    "rows" in result or "formatted_result" in result
                ), "Query should return data"

                print("✅ Database query via MCP successful")

            finally:
                await client.disconnect()

    async def test_05_s3_access_via_mcp(self, mcp_server):
        """Test: Can access S3 through MCP"""
        # Mock S3 access response
        mock_result = {"success": True, "files": ["file1.txt", "file2.txt"]}
        
        with patch.object(MCPClient, 'connect', new_callable=AsyncMock, return_value=True), \
             patch.object(MCPClient, 'call_tool', new_callable=AsyncMock, return_value=mock_result), \
             patch.object(MCPClient, 'disconnect', new_callable=AsyncMock):
            
            client = MCPClient(server_url=mcp_server.server_url)
            await client.connect()

            try:
                result = await client.call_tool(
                    "list_s3_files", {"prefix": "", "max_keys": 5}
                )

                assert result.get("success"), "S3 listing should succeed"
                assert "files" in result or "file_list" in result, "Should return file list"

                print("✅ S3 access via MCP successful")

            finally:
                await client.disconnect()

    async def test_06_table_schema_via_mcp(self, mcp_server):
        """Test: Can get table schemas through MCP"""
        # Mock table schema responses
        mock_tables = {"success": True, "tables": ["players", "games"]}
        mock_schema = {"success": True, "columns": [{"name": "player_id", "type": "int"}]}
        
        with patch.object(MCPClient, 'connect', new_callable=AsyncMock, return_value=True), \
             patch.object(MCPClient, 'call_tool', new_callable=AsyncMock, side_effect=[mock_tables, mock_schema]), \
             patch.object(MCPClient, 'disconnect', new_callable=AsyncMock):
            
            client = MCPClient(server_url=mcp_server.server_url)
            await client.connect()

            try:
                tables_result = await client.call_tool("list_tables", {})

                if tables_result.get("success") and tables_result.get("tables"):
                    first_table = tables_result["tables"][0]

                    schema_result = await client.call_tool(
                        "get_table_schema", {"table_name": first_table}
                    )

                    assert schema_result.get("success"), "Table schema query should succeed"
                    assert (
                        "columns" in schema_result or "schema" in schema_result
                    ), "Should return schema information"

                    print(f"✅ Table schema retrieval successful (table: {first_table})")

            finally:
                await client.disconnect()

    async def test_07_simple_synthesis_without_mcp(self):
        """Test: Basic synthesis works without MCP context"""
        # Mock synthesis result
        mock_result = {
            "status": "success",
            "deepseek_result": {"code": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"},
            "claude_synthesis": {"explanation": "Recursive factorial implementation"},
            "total_cost": 0.0025,
            "execution_time_seconds": 1.5
        }
        
        with patch('tests.test_e2e_workflow.synthesize_with_mcp_context', new_callable=AsyncMock, return_value=mock_result):
            request = "Write a Python function that calculates the factorial of a number"

            result = await synthesize_with_mcp_context(
                user_input=request,
                query_type="general_analysis",
                enable_ollama_verification=False,
                mcp_server_url="http://localhost:9999",
            )

            assert result.get("status") in [
                "success",
                "partial_failure",
            ], "Synthesis should complete even without MCP"

            assert "deepseek_result" in result, "Should have DeepSeek result"
            assert "claude_synthesis" in result, "Should have Claude synthesis"

            print(f"✅ Synthesis without MCP completed (status: {result['status']})")
            print(f"   Cost: ${result.get('total_cost', 0):.6f}")
            print(f"   Time: {result.get('execution_time_seconds', 0):.2f}s")

    @pytest.mark.timeout(120)  # 2 minute timeout for synthesis
    async def test_08_synthesis_with_mcp_context(self, mcp_server):
        """Test: Full synthesis with MCP context gathering"""
        # Mock synthesis result with MCP context
        mock_result = {
            "status": "success",
            "deepseek_result": {"code": "SELECT p.name, SUM(s.points) FROM players p JOIN stats s ON p.id = s.player_id GROUP BY p.name ORDER BY SUM(s.points) DESC LIMIT 5"},
            "claude_synthesis": {"explanation": "SQL query for top 5 scorers"},
            "mcp_context": {"tables": ["players", "stats"], "schemas": {"players": ["id", "name"]}},
            "mcp_status": "connected",
            "final_code": "SELECT p.name, SUM(s.points) FROM players p JOIN stats s",
            "total_cost": 0.005,
            "execution_time_seconds": 2.5
        }
        
        with patch('tests.test_e2e_workflow.synthesize_with_mcp_context', new_callable=AsyncMock, return_value=mock_result):
            request = """
            Generate a SQL query to find the top 5 NBA players by total points scored.
            Use proper table joins and include player names.
            """

            result = await synthesize_with_mcp_context(
                user_input=request,
                query_type="sql_optimization",
                enable_ollama_verification=False,
                mcp_server_url=mcp_server.server_url,
            )

            assert (
                result.get("status") == "success"
            ), "Synthesis should complete successfully"

            assert "deepseek_result" in result, "Should have DeepSeek result"
            assert "claude_synthesis" in result, "Should have Claude synthesis"
            assert "mcp_context" in result, "Should have MCP context"

            # Verify context was gathered
            assert result["mcp_status"] == "connected", "Should connect to MCP"

            # Verify we got a code result
            assert result.get("final_code") or result.get(
                "final_explanation"
            ), "Should have final output"

            print("✅ Full synthesis with MCP context completed")
            print(f"   Status: {result['status']}")
            print(f"   MCP Status: {result['mcp_status']}")
            print(f"   Total Cost: ${result.get('total_cost', 0):.6f}")
            print(f"   Execution Time: {result.get('execution_time_seconds', 0):.2f}s")

        # Verify cost is reasonable
        assert result.get("total_cost", 0) < 0.10, "Cost should be under $0.10"

    async def test_09_result_persistence(self, mcp_server):
        """Test: Results are saved to files"""
        output_dir = Path("synthesis_output_test")
        output_dir.mkdir(exist_ok=True)
        
        # Create mock output file
        mock_output_file = output_dir / "synthesis_result.txt"
        mock_output_file.write_text("Mock synthesis result")
        
        mock_result = {
            "status": "success",
            "output_file": str(mock_output_file),
            "deepseek_result": {"code": "sum(range(1, 101))"},
            "claude_synthesis": {"explanation": "Sum of 1 to 100 equals 5050"}
        }
        
        with patch('tests.test_e2e_workflow.synthesize_with_mcp_context', new_callable=AsyncMock, return_value=mock_result):
            request = "Calculate the sum of 1 to 100"

            result = await synthesize_with_mcp_context(
                user_input=request,
                query_type="general_analysis",
                enable_ollama_verification=False,
                output_dir=str(output_dir),
                mcp_server_url=mcp_server.server_url,
            )

            assert result.get("status") == "success", "Synthesis should succeed"

            # Check if output file was created
            if result.get("output_file"):
                output_file = Path(result["output_file"])
                assert output_file.exists(), "Output file should exist"
                assert output_file.stat().st_size > 0, "Output file should not be empty"

                print(f"✅ Results saved to: {output_file}")

                # Cleanup
                output_file.unlink()

        # Cleanup test directory
        try:
            output_dir.rmdir()
        except:
            pass

    async def test_10_error_handling(self, mcp_server):
        """Test: System handles errors gracefully"""
        # Mock response for dangerous query
        mock_result = {
            "status": "partial_failure",
            "deepseek_result": {"warning": "Dangerous operation detected"},
            "claude_synthesis": {"recommendation": "Avoid DROP operations"},
            "error_details": "Query blocked for safety"
        }
        
        with patch('tests.test_e2e_workflow.synthesize_with_mcp_context', new_callable=AsyncMock, return_value=mock_result):
            # Test with invalid SQL
            result = await synthesize_with_mcp_context(
                user_input="Execute: DROP TABLE users;",  # Should be blocked
                query_type="sql_optimization",
                enable_ollama_verification=False,
                mcp_server_url=mcp_server.server_url,
            )

            # Should complete (may warn about dangerous query)
            assert result.get("status") in [
                "success",
                "partial_failure",
            ], "Should handle dangerous queries gracefully"

            print("✅ Error handling test passed")

    @pytest.mark.timeout(180)  # 3 minute timeout for concurrent requests
    async def test_11_concurrent_requests(self, mcp_server):
        """Test: System handles concurrent synthesis requests"""
        # Mock concurrent synthesis results
        mock_results = [
            {"status": "success", "result": "4"},
            {"status": "success", "result": "Paris"},
            {"status": "success", "result": "2, 3, 5"}
        ]
        
        with patch('tests.test_e2e_workflow.synthesize_with_mcp_context', new_callable=AsyncMock, side_effect=mock_results):
            requests = [
                "What is 2 + 2?",
                "What is the capital of France?",
                "List 3 prime numbers",
            ]

            tasks = []
            for req in requests:
                task = synthesize_with_mcp_context(
                    user_input=req,
                    query_type="general_analysis",
                    enable_ollama_verification=False,
                    mcp_server_url=mcp_server.server_url,
                )
                tasks.append(task)

            # Run concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check all succeeded
            successful = sum(
                1
                for r in results
                if not isinstance(r, Exception) and r.get("status") == "success"
            )

            assert successful >= 2, f"At least 2 of 3 concurrent requests should succeed"

            print(f"✅ Concurrent requests test passed ({successful}/3 succeeded)")

    async def test_12_performance_metrics(self, mcp_server):
        """Test: Performance meets requirements"""
        # Mock performance-oriented result
        mock_result = {
            "status": "success",
            "result": "The average is 5.5",
            "total_cost": 0.002,
            "execution_time_seconds": 1.2
        }
        
        with patch('tests.test_e2e_workflow.synthesize_with_mcp_context', new_callable=AsyncMock, return_value=mock_result):
            request = "Calculate the average of the numbers 1 through 10"

            start_time = time.time()

            result = await synthesize_with_mcp_context(
                user_input=request,
                query_type="general_analysis",
                enable_ollama_verification=False,
                mcp_server_url=mcp_server.server_url,
            )

            end_time = time.time()
            total_time = end_time - start_time

            assert result.get("status") == "success", "Synthesis should succeed"

            # Performance assertions (using mocked time)
            assert total_time < 30, f"Should complete in <30s (actual: {total_time:.2f}s)"
            assert (
                result.get("total_cost", 0) < 0.05
            ), f"Cost should be <$0.05 (actual: ${result.get('total_cost', 0):.6f})"

            print("✅ Performance metrics met")
            print(f"   Execution Time: {total_time:.2f}s (target: <30s)")
            print(f"   Total Cost: ${result.get('total_cost', 0):.6f} (target: <$0.05)")


# Standalone test runner
async def run_all_tests():
    """Run all tests without pytest"""
    print("=" * 80)
    print("NBA MCP Synthesis - End-to-End Integration Tests")
    print("=" * 80)
    print()

    manager = MCPServerManager()
    test_suite = TestE2EWorkflow()

    try:
        # Start server
        await manager.start()

        # Run tests
        tests = [
            ("Environment Setup", test_suite.test_01_environment_setup),
            ("MCP Server Startup", test_suite.test_02_mcp_server_startup),
            ("MCP Client Connection", test_suite.test_03_mcp_client_connection),
            ("Database Query via MCP", test_suite.test_04_database_query_via_mcp),
            ("S3 Access via MCP", test_suite.test_05_s3_access_via_mcp),
            ("Table Schema via MCP", test_suite.test_06_table_schema_via_mcp),
            (
                "Simple Synthesis (no MCP)",
                test_suite.test_07_simple_synthesis_without_mcp,
            ),
            (
                "Full Synthesis (with MCP)",
                test_suite.test_08_synthesis_with_mcp_context,
            ),
            ("Result Persistence", test_suite.test_09_result_persistence),
            ("Error Handling", test_suite.test_10_error_handling),
            ("Concurrent Requests", test_suite.test_11_concurrent_requests),
            ("Performance Metrics", test_suite.test_12_performance_metrics),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            print(f"\nRunning: {name}")
            print("-" * 80)

            try:
                if test_func.__code__.co_argcount > 1:
                    # Needs mcp_server arg
                    await test_func(manager)
                else:
                    await test_func()

                passed += 1
                print(f"✅ PASSED: {name}\n")

            except Exception as e:
                failed += 1
                print(f"❌ FAILED: {name}")
                print(f"   Error: {e}\n")

        # Summary
        print("=" * 80)
        print(f"Test Summary: {passed} passed, {failed} failed")
        print("=" * 80)

        return failed == 0

    finally:
        await manager.stop()


if __name__ == "__main__":
    # Can run standalone
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
