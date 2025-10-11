#!/usr/bin/env python3
"""
Comprehensive Overnight Test Suite
Runs complete Phase C testing with detailed reporting

Usage:
    # Run in background (recommended)
    nohup python scripts/overnight_test_suite.py > overnight_tests.log 2>&1 &

    # Or with explicit output
    python scripts/overnight_test_suite.py --output-dir ./test_results

Results will be in:
    - test_results/test_report.html (main report)
    - test_results/test_report.json (data)
    - test_results/performance_metrics.csv (metrics)
    - overnight_tests.log (console output)
"""

import sys
import asyncio
import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Color output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'-'*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'-'*80}{Colors.END}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


class TestResult:
    """Container for test results"""
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.duration = 0.0
        self.error = None
        self.details = {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'category': self.category,
            'passed': self.passed,
            'duration': self.duration,
            'error': self.error,
            'details': self.details,
            'timestamp': self.timestamp
        }


class TestSuite:
    """Main test suite coordinator"""

    def __init__(self, output_dir: str = "./test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.results: List[TestResult] = []
        self.start_time = time.time()
        self.summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'duration': 0.0
        }

    async def run_test(self, test_func, name: str, category: str) -> TestResult:
        """Run a single test and capture results"""
        result = TestResult(name, category)

        print(f"\n  Testing: {name}...")
        start = time.time()

        try:
            test_result = await test_func()
            result.passed = test_result.get('passed', False)
            result.details = test_result.get('details', {})
            result.error = test_result.get('error')

            if result.passed:
                print_success(f"{name} - PASSED ({result.duration:.2f}s)")
            else:
                print_error(f"{name} - FAILED: {result.error}")

        except Exception as e:
            result.passed = False
            result.error = str(e)
            print_error(f"{name} - EXCEPTION: {str(e)}")
            traceback.print_exc()

        result.duration = time.time() - start
        self.results.append(result)

        return result

    def generate_summary(self):
        """Generate test summary"""
        self.summary['total'] = len(self.results)
        self.summary['passed'] = sum(1 for r in self.results if r.passed)
        self.summary['failed'] = sum(1 for r in self.results if not r.passed)
        self.summary['duration'] = time.time() - self.start_time

    def save_results(self):
        """Save test results to files"""

        # JSON results
        json_path = self.output_dir / "test_report.json"
        with open(json_path, 'w') as f:
            json.dump({
                'summary': self.summary,
                'results': [r.to_dict() for r in self.results],
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)

        print_info(f"JSON report saved: {json_path}")

        # HTML report
        html_path = self.output_dir / "test_report.html"
        self.generate_html_report(html_path)
        print_info(f"HTML report saved: {html_path}")

        # CSV metrics
        csv_path = self.output_dir / "test_metrics.csv"
        self.generate_csv_metrics(csv_path)
        print_info(f"CSV metrics saved: {csv_path}")

    def generate_html_report(self, path: Path):
        """Generate HTML test report"""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>NBA MCP Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        .passed {{ color: #4CAF50; }}
        .failed {{ color: #f44336; }}
        .warning {{ color: #ff9800; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #333;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .status-badge {{
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-pass {{
            background: #4CAF50;
            color: white;
        }}
        .badge-fail {{
            background: #f44336;
            color: white;
        }}
        .error-details {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 0.9em;
        }}
        .category {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏀 NBA MCP Test Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <div class="metric">
                <div class="metric-label">Total Tests</div>
                <div class="metric-value">{self.summary['total']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Passed</div>
                <div class="metric-value passed">{self.summary['passed']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Failed</div>
                <div class="metric-value failed">{self.summary['failed']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Duration</div>
                <div class="metric-value">{self.summary['duration']:.1f}s</div>
            </div>
        </div>

        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""

        for result in self.results:
            status_badge = 'badge-pass' if result.passed else 'badge-fail'
            status_text = 'PASS' if result.passed else 'FAIL'
            error_html = ''

            if result.error:
                error_html = f'<div class="error-details">{result.error}</div>'

            html += f"""
                <tr>
                    <td><strong>{result.name}</strong></td>
                    <td><span class="category">{result.category}</span></td>
                    <td><span class="status-badge {status_badge}">{status_text}</span></td>
                    <td>{result.duration:.2f}s</td>
                    <td>{error_html}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        with open(path, 'w') as f:
            f.write(html)

    def generate_csv_metrics(self, path: Path):
        """Generate CSV metrics"""
        import csv

        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Test Name', 'Category', 'Status', 'Duration (s)', 'Error'])

            for result in self.results:
                writer.writerow([
                    result.name,
                    result.category,
                    'PASS' if result.passed else 'FAIL',
                    f"{result.duration:.2f}",
                    result.error or ''
                ])


# =============================================================================
# TEST IMPLEMENTATIONS
# =============================================================================

async def test_environment_setup() -> Dict:
    """Test 1: Environment setup and configuration"""
    try:
        from dotenv import load_dotenv
        import os

        load_dotenv()

        required_vars = ['RDS_HOST', 'S3_BUCKET', 'RDS_DATABASE']
        missing = [v for v in required_vars if not os.getenv(v)]

        if missing:
            return {
                'passed': False,
                'error': f"Missing environment variables: {', '.join(missing)}"
            }

        return {
            'passed': True,
            'details': {
                'env_vars_found': len(required_vars),
                'database': os.getenv('RDS_DATABASE'),
                's3_bucket': os.getenv('S3_BUCKET')
            }
        }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_fastmcp_import() -> Dict:
    """Test 2: FastMCP server import"""
    try:
        from mcp_server import fastmcp_server

        return {
            'passed': True,
            'details': {
                'server_name': fastmcp_server.mcp.name,
                'tools_registered': len(fastmcp_server.mcp._tool_manager._tools)
            }
        }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_pydantic_models() -> Dict:
    """Test 3: Pydantic model validation"""
    try:
        from mcp_server.tools.params import QueryDatabaseParams
        from mcp_server.responses import QueryResult

        # Test valid query
        params = QueryDatabaseParams(sql_query="SELECT 1")

        # Test SQL injection blocking
        try:
            bad_params = QueryDatabaseParams(sql_query="SELECT * FROM users; DROP TABLE users;")
            return {'passed': False, 'error': 'SQL injection not blocked'}
        except:
            pass  # Expected to fail

        # Test response model
        result = QueryResult(
            columns=['test'],
            rows=[[1]],
            row_count=1,
            query="SELECT 1",
            success=True
        )

        return {
            'passed': True,
            'details': {
                'validation_working': True,
                'sql_injection_blocked': True,
                'response_model_working': True
            }
        }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_lifespan_initialization() -> Dict:
    """Test 4: Lifespan resource initialization"""
    try:
        from mcp_server.fastmcp_lifespan import nba_lifespan

        class MockApp:
            pass

        app = MockApp()

        async with nba_lifespan(app) as context:
            required_keys = ['rds_connector', 's3_connector', 'glue_connector', 'config']
            missing = [k for k in required_keys if k not in context]

            if missing:
                return {
                    'passed': False,
                    'error': f"Missing context keys: {', '.join(missing)}"
                }

            return {
                'passed': True,
                'details': {
                    'resources_initialized': len(context),
                    'connectors': list(context.keys())
                }
            }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_database_connection() -> Dict:
    """Test 5: Database connectivity"""
    try:
        from mcp_server.fastmcp_lifespan import nba_lifespan

        class MockApp:
            pass

        async with nba_lifespan(MockApp()) as context:
            rds = context['rds_connector']

            # Simple query - RDS returns a dict with 'success' and 'rows' keys
            result = await rds.execute_query("SELECT 1 as test")

            if not result.get('success') or result.get('row_count', 0) == 0:
                return {'passed': False, 'error': f"No results from test query: {result.get('error', 'Unknown error')}"}

            # Count tables
            tables_result = await rds.execute_query("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            """)

            table_count = tables_result['rows'][0]['count'] if tables_result.get('success') and tables_result.get('rows') else 0

            return {
                'passed': True,
                'details': {
                    'connection_successful': True,
                    'test_query_passed': True,
                    'tables_found': table_count
                }
            }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_s3_connection() -> Dict:
    """Test 6: S3 connectivity"""
    try:
        from mcp_server.fastmcp_lifespan import nba_lifespan

        class MockApp:
            pass

        async with nba_lifespan(MockApp()) as context:
            s3 = context['s3_connector']

            # List a few files
            result = await s3.list_files(prefix="", max_keys=5)

            if not result.get('success'):
                return {'passed': False, 'error': result.get('error', 'Unknown error')}

            files = result.get('files', [])

            return {
                'passed': True,
                'details': {
                    'connection_successful': True,
                    'files_listed': len(files),
                    'sample_files': [f.get('key') for f in files[:3]] if files else []
                }
            }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_query_tool() -> Dict:
    """Test 7: Query database tool"""
    try:
        from mcp_server.fastmcp_lifespan import nba_lifespan
        from mcp_server.fastmcp_server import query_database
        from mcp_server.tools.params import QueryDatabaseParams

        class MockApp:
            pass

        class MockContext:
            class MockRequestContext:
                def __init__(self, lifespan_context):
                    self.lifespan_context = lifespan_context

            def __init__(self, lifespan_context):
                self.request_context = self.MockRequestContext(lifespan_context)
                self.logs = []

            async def info(self, msg): self.logs.append(('info', msg))
            async def debug(self, msg): self.logs.append(('debug', msg))
            async def error(self, msg): self.logs.append(('error', msg))
            async def report_progress(self, *args): pass

        async with nba_lifespan(MockApp()) as lifespan_context:
            ctx = MockContext(lifespan_context)
            params = QueryDatabaseParams(sql_query="SELECT 1 as test", max_rows=10)

            result = await query_database(params, ctx)

            if not result.success:
                return {'passed': False, 'error': result.error}

            if result.row_count != 1:
                return {'passed': False, 'error': f'Expected 1 row, got {result.row_count}'}

            return {
                'passed': True,
                'details': {
                    'rows_returned': result.row_count,
                    'columns': result.columns,
                    'context_logging': len(ctx.logs)
                }
            }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_list_tables_tool() -> Dict:
    """Test 8: List tables tool"""
    try:
        from mcp_server.fastmcp_lifespan import nba_lifespan
        from mcp_server.fastmcp_server import list_tables
        from mcp_server.tools.params import ListTablesParams

        class MockApp:
            pass

        class MockContext:
            class MockRequestContext:
                def __init__(self, lifespan_context):
                    self.lifespan_context = lifespan_context

            def __init__(self, lifespan_context):
                self.request_context = self.MockRequestContext(lifespan_context)

            async def info(self, msg): pass
            async def error(self, msg): pass

        async with nba_lifespan(MockApp()) as lifespan_context:
            ctx = MockContext(lifespan_context)
            params = ListTablesParams()

            result = await list_tables(params, ctx)

            if not result.success:
                return {'passed': False, 'error': result.error}

            if result.count == 0:
                return {'passed': False, 'error': 'No tables found'}

            return {
                'passed': True,
                'details': {
                    'tables_found': result.count,
                    'sample_tables': result.tables[:5]
                }
            }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_performance_query() -> Dict:
    """Test 9: Query performance benchmark"""
    try:
        from mcp_server.fastmcp_lifespan import nba_lifespan

        class MockApp:
            pass

        async with nba_lifespan(MockApp()) as context:
            rds = context['rds_connector']

            # Run query 10 times
            times = []
            for i in range(10):
                start = time.time()
                await rds.execute_query("SELECT 1")
                times.append(time.time() - start)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            # Check if performance is acceptable (< 1 second average)
            if avg_time > 1.0:
                return {
                    'passed': False,
                    'error': f'Performance too slow: {avg_time:.3f}s average'
                }

            return {
                'passed': True,
                'details': {
                    'iterations': len(times),
                    'avg_time_ms': avg_time * 1000,
                    'min_time_ms': min_time * 1000,
                    'max_time_ms': max_time * 1000
                }
            }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


async def test_concurrent_queries() -> Dict:
    """Test 10: Concurrent query handling"""
    try:
        from mcp_server.fastmcp_lifespan import nba_lifespan

        class MockApp:
            pass

        async with nba_lifespan(MockApp()) as context:
            rds = context['rds_connector']

            # Run 5 queries concurrently
            tasks = [
                rds.execute_query("SELECT 1")
                for _ in range(5)
            ]

            start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start

            # Check all succeeded
            failures = [r for r in results if isinstance(r, Exception)]
            if failures:
                return {
                    'passed': False,
                    'error': f'{len(failures)} concurrent queries failed'
                }

            return {
                'passed': True,
                'details': {
                    'concurrent_queries': len(tasks),
                    'all_succeeded': True,
                    'total_duration_ms': duration * 1000
                }
            }
    except Exception as e:
        return {'passed': False, 'error': str(e)}


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

async def run_all_tests(output_dir: str):
    """Run all tests and generate report"""

    suite = TestSuite(output_dir)

    print_header("NBA MCP Overnight Test Suite")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output Directory: {output_dir}")

    # Category 1: Environment & Setup
    print_section("Category 1: Environment & Setup")
    await suite.run_test(test_environment_setup, "Environment Setup", "Setup")
    await suite.run_test(test_fastmcp_import, "FastMCP Import", "Setup")
    await suite.run_test(test_pydantic_models, "Pydantic Models", "Setup")
    await suite.run_test(test_lifespan_initialization, "Lifespan Initialization", "Setup")

    # Category 2: Connectivity
    print_section("Category 2: Connectivity Tests")
    await suite.run_test(test_database_connection, "Database Connection", "Connectivity")
    await suite.run_test(test_s3_connection, "S3 Connection", "Connectivity")

    # Category 3: Tool Functionality
    print_section("Category 3: Tool Functionality")
    await suite.run_test(test_query_tool, "Query Database Tool", "Tools")
    await suite.run_test(test_list_tables_tool, "List Tables Tool", "Tools")

    # Category 4: Performance
    print_section("Category 4: Performance Benchmarks")
    await suite.run_test(test_performance_query, "Query Performance", "Performance")
    await suite.run_test(test_concurrent_queries, "Concurrent Queries", "Performance")

    # Generate reports
    print_section("Generating Reports")
    suite.generate_summary()
    suite.save_results()

    # Print summary
    print_header("Test Summary")
    print(f"Total Tests:     {suite.summary['total']}")
    print_success(f"Passed:          {suite.summary['passed']}")
    if suite.summary['failed'] > 0:
        print_error(f"Failed:          {suite.summary['failed']}")
    print(f"Total Duration:  {suite.summary['duration']:.2f}s")
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Final status
    if suite.summary['failed'] == 0:
        print_header("✅ ALL TESTS PASSED!")
        return 0
    else:
        print_header(f"❌ {suite.summary['failed']} TESTS FAILED")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='NBA MCP Overnight Test Suite')
    parser.add_argument(
        '--output-dir',
        default='./test_results',
        help='Output directory for test results (default: ./test_results)'
    )

    args = parser.parse_args()

    try:
        exit_code = asyncio.run(run_all_tests(args.output_dir))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
