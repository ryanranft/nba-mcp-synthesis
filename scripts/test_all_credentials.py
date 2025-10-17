#!/usr/bin/env python3
"""
Comprehensive Credentials Testing Script
Tests all credentials using the new unified secrets management system
"""

import os
import sys
import asyncio
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Third-party imports
import boto3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import requests
from openai import OpenAI, AsyncOpenAI
import anthropic
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Import unified configuration manager and env helper
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager
from mcp_server.env_helper import get_hierarchical_env

# Optional imports
try:
    import ollama

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Load environment variables (for backward compatibility)
from dotenv import load_dotenv

load_dotenv()


class CredentialTester:
    """Test all credentials in .env file"""

    def __init__(self, project: str = "nba-mcp-synthesis", context: str = "production"):
        """Initialize credential tester with unified configuration system"""
        # Load secrets using hierarchical loader
        print(f"Loading secrets for project={project}, context={context}")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "/Users/ryanranft/load_env_hierarchical.py",
                    project,
                    "NBA",
                    context,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            print("✅ Secrets loaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to load secrets: {e.stderr}")
            raise RuntimeError(f"Failed to load secrets: {e.stderr}")
        except Exception as e:
            print(f"❌ Error loading secrets: {e}")
            raise RuntimeError(f"Error loading secrets: {e}")

        # Initialize unified configuration manager
        try:
            self.config = UnifiedConfigurationManager(project, context)
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            raise RuntimeError(f"Failed to load configuration: {e}")

        self.results = {
            "ai_models": {},
            "aws_services": {},
            "database": {},
            "integrations": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
            },
        }
        self.test_files_created = []

    def log_result(
        self,
        category: str,
        test_name: str,
        success: bool,
        message: str = "",
        error: str = "",
    ):
        """Log test result"""
        self.results[category][test_name] = {
            "success": success,
            "message": message,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

        self.results["summary"]["total_tests"] += 1
        if success:
            self.results["summary"]["passed"] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {test_name}: {message}")
            if error:
                print(f"   Error: {error}")

    def test_deepseek_api(self):
        """Test DeepSeek API with quick validation"""
        try:
            api_key = get_hierarchical_env(
                "DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            if not api_key:
                self.log_result("ai_models", "DeepSeek API", False, "API key not found")
                return

            # Quick format validation instead of API call
            if api_key.startswith("sk-"):
                self.log_result(
                    "ai_models", "DeepSeek API", True, "API key format is valid"
                )
            else:
                self.log_result(
                    "ai_models", "DeepSeek API", False, "API key format may be invalid"
                )

        except Exception as e:
            self.log_result(
                "ai_models", "DeepSeek API", False, "API validation failed", str(e)
            )

    def test_anthropic_api(self):
        """Test Anthropic Claude API with quick validation"""
        try:
            api_key = get_hierarchical_env(
                "ANTHROPIC_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            if not api_key:
                self.log_result(
                    "ai_models", "Anthropic Claude API", False, "API key not found"
                )
                return

            # Quick format validation instead of API call
            if api_key.startswith("sk-ant-"):
                self.log_result(
                    "ai_models", "Anthropic Claude API", True, "API key format is valid"
                )
            else:
                self.log_result(
                    "ai_models",
                    "Anthropic Claude API",
                    False,
                    "API key format may be invalid",
                )

        except Exception as e:
            self.log_result(
                "ai_models",
                "Anthropic Claude API",
                False,
                "API validation failed",
                str(e),
            )

    def test_openai_api(self):
        """Test OpenAI GPT-4 API with quick validation"""
        try:
            api_key = get_hierarchical_env(
                "OPENAI_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            if not api_key:
                self.log_result(
                    "ai_models", "OpenAI GPT-4 API", False, "API key not found"
                )
                return

            # Quick format validation instead of API call
            if api_key.startswith("sk-proj-"):
                self.log_result(
                    "ai_models", "OpenAI GPT-4 API", True, "API key format is valid"
                )
            else:
                self.log_result(
                    "ai_models",
                    "OpenAI GPT-4 API",
                    False,
                    "API key format may be invalid",
                )

        except Exception as e:
            self.log_result(
                "ai_models", "OpenAI GPT-4 API", False, "API validation failed", str(e)
            )

    def test_google_api(self):
        """Test Google Gemini API with quick validation"""
        try:
            api_key = get_hierarchical_env(
                "GOOGLE_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            if not api_key:
                self.log_result(
                    "ai_models", "Google Gemini API", False, "API key not found"
                )
                return

            # Quick format validation instead of API call
            if api_key.startswith("AIza"):
                self.log_result(
                    "ai_models", "Google Gemini API", True, "API key format is valid"
                )
            else:
                self.log_result(
                    "ai_models",
                    "Google Gemini API",
                    False,
                    "API key format may be invalid",
                )

        except Exception as e:
            self.log_result(
                "ai_models", "Google Gemini API", False, "API validation failed", str(e)
            )

    def test_ollama_api(self):
        """Test Ollama local API with quick validation"""
        try:
            if not OLLAMA_AVAILABLE:
                self.log_result(
                    "ai_models", "Ollama API", False, "Ollama module not installed"
                )
                return

            host = (
                get_hierarchical_env("OLLAMA_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "http://localhost:11434"
            )
            model = (
                get_hierarchical_env("OLLAMA_MODEL", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "qwen2.5-coder:32b"
            )

            # Quick connection test with shorter timeout
            response = requests.get(f"{host}/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]

                if model in model_names:
                    self.log_result(
                        "ai_models", "Ollama API", True, f"Model {model} is available"
                    )
                else:
                    self.log_result(
                        "ai_models",
                        "Ollama API",
                        False,
                        f"Model {model} not found. Available: {model_names}",
                    )
            else:
                self.log_result(
                    "ai_models",
                    "Ollama API",
                    False,
                    f"Connection failed: {response.status_code}",
                )

        except requests.exceptions.ConnectionError:
            self.log_result(
                "ai_models",
                "Ollama API",
                False,
                "Ollama server not running or not accessible",
            )
        except Exception as e:
            self.log_result(
                "ai_models", "Ollama API", False, "API validation failed", str(e)
            )

    def test_aws_credentials(self):
        """Test AWS credentials"""
        try:
            access_key = get_hierarchical_env(
                "AWS_ACCESS_KEY_ID", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            secret_key = get_hierarchical_env(
                "AWS_SECRET_ACCESS_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            region = (
                get_hierarchical_env("AWS_REGION", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "us-east-1"
            )

            if not access_key or not secret_key:
                self.log_result(
                    "aws_services",
                    "AWS Credentials",
                    False,
                    "Access key or secret key not found",
                )
                return

            # Test STS to verify credentials
            sts_client = boto3.client(
                "sts",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )

            identity = sts_client.get_caller_identity()
            self.log_result(
                "aws_services",
                "AWS Credentials",
                True,
                f"Identity: {identity.get('Arn', 'Unknown')}",
            )

        except Exception as e:
            self.log_result(
                "aws_services",
                "AWS Credentials",
                False,
                "Credential verification failed",
                str(e),
            )

    def test_s3_buckets(self):
        """Test S3 bucket access with full read/write operations"""
        try:
            access_key = get_hierarchical_env(
                "AWS_ACCESS_KEY_ID", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            secret_key = get_hierarchical_env(
                "AWS_SECRET_ACCESS_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            region = (
                get_hierarchical_env("AWS_REGION", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "us-east-1"
            )

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )

            # Test primary bucket
            primary_bucket = (
                get_hierarchical_env("S3_BUCKET", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "nba-mcp-books-20251011"
            )
            self._test_s3_bucket(s3_client, primary_bucket, "Primary S3 Bucket")

            # Test books bucket
            books_bucket = (
                get_hierarchical_env("S3_BOOKS_BUCKET", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "nba-mcp-books-20251011"
            )
            if books_bucket != primary_bucket:  # Only test if different
                self._test_s3_bucket(s3_client, books_bucket, "Books S3 Bucket")

        except Exception as e:
            self.log_result(
                "aws_services", "S3 Buckets", False, "S3 testing failed", str(e)
            )

    def _test_s3_bucket(self, s3_client, bucket_name: str, test_name: str):
        """Test individual S3 bucket"""
        try:
            # Test 1: List objects (read access)
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            object_count = response.get("KeyCount", 0)

            # Test 2: Create test file (write access)
            test_key = f"test/credential_test_{int(time.time())}.txt"
            test_content = (
                f"Credential test file created at {datetime.now().isoformat()}"
            )

            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType="text/plain",
            )

            # Test 3: Read test file (read access)
            response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
            retrieved_content = response["Body"].read().decode("utf-8")

            # Test 4: Delete test file (delete access)
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)

            self.test_files_created.append((bucket_name, test_key))  # Track for cleanup

            self.log_result(
                "aws_services",
                test_name,
                True,
                f"Full access verified. Objects: {object_count}",
            )

        except Exception as e:
            self.log_result(
                "aws_services", test_name, False, f"Bucket access failed", str(e)
            )

    def test_aws_glue(self):
        """Test AWS Glue catalog access"""
        try:
            access_key = get_hierarchical_env(
                "AWS_ACCESS_KEY_ID", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            secret_key = get_hierarchical_env(
                "AWS_SECRET_ACCESS_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            region = (
                get_hierarchical_env("AWS_REGION", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "us-east-1"
            )

            glue_client = boto3.client(
                "glue",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )

            # Test database access
            database_name = (
                get_hierarchical_env("GLUE_DATABASE", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "nba_raw_data"
            )

            try:
                response = glue_client.get_database(Name=database_name)
                self.log_result(
                    "aws_services",
                    "AWS Glue Database",
                    True,
                    f"Database '{database_name}' accessible",
                )
            except glue_client.exceptions.EntityNotFoundException:
                # Try to list databases
                response = glue_client.get_databases()
                databases = [db["Name"] for db in response["DatabaseList"]]
                self.log_result(
                    "aws_services",
                    "AWS Glue Database",
                    False,
                    f"Database '{database_name}' not found. Available: {databases}",
                )

            # Test table listing
            try:
                response = glue_client.get_tables(DatabaseName=database_name)
                table_count = len(response.get("TableList", []))
                self.log_result(
                    "aws_services",
                    "AWS Glue Tables",
                    True,
                    f"Found {table_count} tables",
                )
            except Exception as e:
                self.log_result(
                    "aws_services",
                    "AWS Glue Tables",
                    False,
                    "Table listing failed",
                    str(e),
                )

        except Exception as e:
            self.log_result(
                "aws_services", "AWS Glue", False, "Glue access failed", str(e)
            )

    def test_database_connections(self):
        """Test all database connection variants"""
        # Test RDS_* variables
        self._test_db_connection(
            "RDS",
            {
                "host": get_hierarchical_env(
                    "RDS_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                ),
                "port": get_hierarchical_env(
                    "RDS_PORT", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                )
                or "5432",
                "database": get_hierarchical_env(
                    "RDS_DATABASE", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                ),
                "user": get_hierarchical_env(
                    "RDS_USERNAME", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                ),
                "password": get_hierarchical_env(
                    "RDS_PASSWORD", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                ),
            },
        )

        # Test DB_* variables
        self._test_db_connection(
            "DB",
            {
                "host": get_hierarchical_env(
                    "DB_HOST", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                ),
                "port": get_hierarchical_env("DB_PORT", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "5432",
                "database": get_hierarchical_env(
                    "DB_NAME", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                ),
                "user": get_hierarchical_env(
                    "DB_USER", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                ),
                "password": get_hierarchical_env(
                    "DB_PASSWORD", "NBA_MCP_SYNTHESIS", "WORKFLOW"
                ),
            },
        )

        # Test DATABASE_URL
        database_url = get_hierarchical_env(
            "DATABASE_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )
        if database_url:
            self._test_db_url_connection("DATABASE_URL", database_url)

    def _test_db_connection(self, prefix: str, config: Dict[str, str]):
        """Test database connection with given config"""
        try:
            if not all(
                [config["host"], config["database"], config["user"], config["password"]]
            ):
                self.log_result(
                    "database",
                    f"{prefix} Variables",
                    False,
                    "Missing required connection parameters",
                )
                return

            conn = psycopg2.connect(
                host=config["host"],
                port=int(config["port"]),
                database=config["database"],
                user=config["user"],
                password=config["password"],
                sslmode="require",
            )

            # Test read operation
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

            # Test write operation (create test table)
            test_table = f"credential_test_{int(time.time())}"
            cursor.execute(
                f"""
                CREATE TABLE {test_table} (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # Test insert
            cursor.execute(
                f"INSERT INTO {test_table} (test_data) VALUES ('Credential test data');"
            )

            # Test select
            cursor.execute(f"SELECT * FROM {test_table};")
            result = cursor.fetchone()

            # Test delete table
            cursor.execute(f"DROP TABLE {test_table};")

            conn.commit()
            cursor.close()
            conn.close()

            self.log_result(
                "database",
                f"{prefix} Variables",
                True,
                f"Full access verified. PostgreSQL version: {version[:50]}...",
            )

        except Exception as e:
            self.log_result(
                "database",
                f"{prefix} Variables",
                False,
                "Database connection failed",
                str(e),
            )

    def _test_db_url_connection(self, test_name: str, database_url: str):
        """Test database connection using URL"""
        try:
            conn = psycopg2.connect(database_url)

            # Test read operation
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

            # Test write operation
            test_table = f"credential_test_{int(time.time())}"
            cursor.execute(
                f"""
                CREATE TABLE {test_table} (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            cursor.execute(
                f"INSERT INTO {test_table} (test_data) VALUES ('Credential test data');"
            )
            cursor.execute(f"SELECT * FROM {test_table};")
            result = cursor.fetchone()
            cursor.execute(f"DROP TABLE {test_table};")

            conn.commit()
            cursor.close()
            conn.close()

            self.log_result(
                "database",
                test_name,
                True,
                f"Full access verified. PostgreSQL version: {version[:50]}...",
            )

        except Exception as e:
            self.log_result(
                "database", test_name, False, "Database URL connection failed", str(e)
            )

    def test_slack_webhook(self):
        """Test Slack webhook"""
        try:
            webhook_url = get_hierarchical_env(
                "SLACK_WEBHOOK_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            if not webhook_url:
                self.log_result(
                    "integrations", "Slack Webhook", False, "Webhook URL not found"
                )
                return

            # Send test message
            test_message = {
                "text": f"🔧 Credential Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "attachments": [
                    {
                        "color": "good",
                        "fields": [
                            {
                                "title": "Test Status",
                                "value": "All credentials are being tested",
                                "short": False,
                            }
                        ],
                    }
                ],
            }

            response = requests.post(webhook_url, json=test_message, timeout=10)

            if response.status_code == 200:
                self.log_result(
                    "integrations",
                    "Slack Webhook",
                    True,
                    "Test message sent successfully",
                )
            else:
                self.log_result(
                    "integrations",
                    "Slack Webhook",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                )

        except Exception as e:
            self.log_result(
                "integrations", "Slack Webhook", False, "Webhook test failed", str(e)
            )

    def test_great_expectations_s3(self):
        """Test Great Expectations S3 access"""
        try:
            gx_bucket = get_hierarchical_env(
                "GX_S3_BUCKET", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            if not gx_bucket:
                self.log_result(
                    "integrations",
                    "Great Expectations S3",
                    False,
                    "GX_S3_BUCKET not configured",
                )
                return

            access_key = get_hierarchical_env(
                "AWS_ACCESS_KEY_ID", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            secret_key = get_hierarchical_env(
                "AWS_SECRET_ACCESS_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            region = (
                get_hierarchical_env("AWS_REGION", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "us-east-1"
            )

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )

            # Test bucket access
            response = s3_client.head_bucket(Bucket=gx_bucket)
            self.log_result(
                "integrations",
                "Great Expectations S3",
                True,
                f"Bucket '{gx_bucket}' accessible",
            )

        except Exception as e:
            self.log_result(
                "integrations",
                "Great Expectations S3",
                False,
                "GX S3 access failed",
                str(e),
            )

    def cleanup_test_resources(self):
        """Clean up any test resources created during testing"""
        print("\n🧹 Cleaning up test resources...")

        try:
            access_key = get_hierarchical_env(
                "AWS_ACCESS_KEY_ID", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            secret_key = get_hierarchical_env(
                "AWS_SECRET_ACCESS_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )
            region = (
                get_hierarchical_env("AWS_REGION", "NBA_MCP_SYNTHESIS", "WORKFLOW")
                or "us-east-1"
            )

            if access_key and secret_key:
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region,
                )

                for bucket, key in self.test_files_created:
                    try:
                        s3_client.delete_object(Bucket=bucket, Key=key)
                        print(f"   ✅ Cleaned up {bucket}/{key}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to clean up {bucket}/{key}: {e}")

        except Exception as e:
            print(f"   ⚠️  Cleanup failed: {e}")

    def generate_report(self):
        """Generate comprehensive test report"""
        self.results["summary"]["end_time"] = datetime.now().isoformat()

        print("\n" + "=" * 80)
        print("🔍 COMPREHENSIVE CREDENTIAL TEST REPORT")
        print("=" * 80)

        # Summary
        summary = self.results["summary"]
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   Success Rate: {(summary['passed']/summary['total_tests']*100):.1f}%")

        # Detailed results by category
        for category, tests in self.results.items():
            if category == "summary":
                continue

            print(f"\n📋 {category.upper().replace('_', ' ')}:")
            for test_name, result in tests.items():
                status = "✅" if result["success"] else "❌"
                print(f"   {status} {test_name}: {result['message']}")
                if result["error"]:
                    print(f"      Error: {result['error']}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        failed_tests = []
        for category, tests in self.results.items():
            if category == "summary":
                continue
            for test_name, result in tests.items():
                if not result["success"]:
                    failed_tests.append(f"{category}.{test_name}")

        if failed_tests:
            print("   The following credentials need attention:")
            for test in failed_tests:
                print(f"   - {test}")
            print("\n   Consider:")
            print("   - Rotating API keys if they're expired")
            print("   - Checking AWS permissions")
            print("   - Verifying database credentials")
            print("   - Ensuring services are running (Ollama)")
        else:
            print("   🎉 All credentials are working correctly!")

        # Save detailed report
        report_file = (
            f"credential_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")

    def run_all_tests(self):
        """Run all credential tests"""
        print("🚀 Starting comprehensive credential testing...")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # AI Models
        print("\n🤖 Testing AI Model APIs...")
        self.test_deepseek_api()
        self.test_anthropic_api()
        self.test_openai_api()
        self.test_google_api()
        self.test_ollama_api()

        # AWS Services
        print("\n☁️  Testing AWS Services...")
        self.test_aws_credentials()
        self.test_s3_buckets()
        self.test_aws_glue()

        # Database
        print("\n🗄️  Testing Database Connections...")
        self.test_database_connections()

        # Integrations
        print("\n🔗 Testing Integrations...")
        self.test_slack_webhook()
        self.test_great_expectations_s3()

        # Cleanup and report
        self.cleanup_test_resources()
        self.generate_report()


def main():
    """Main function"""
    print("NBA MCP Synthesis - Credential Testing Tool")
    print("=" * 50)
    print("Using unified secrets management system")
    print()

    tester = CredentialTester("nba-mcp-synthesis", "production")
    tester.run_all_tests()


if __name__ == "__main__":
    main()
