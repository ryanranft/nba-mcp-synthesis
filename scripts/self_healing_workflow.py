#!/usr/bin/env python3
"""
Self-Healing Model Testing and Deployment Workflow
Automatically monitors, detects issues, patches, and redeploys until all models work correctly.
"""

import os
import sys
import json
import time
import psutil
import subprocess
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import signal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    pid: int
    name: str
    start_time: float
    command: str
    status: str
    runtime_seconds: float
    expected_max_runtime: int = 300  # 5 minutes default


@dataclass
class TestResult:
    test_name: str
    success: bool
    error_message: Optional[str]
    runtime_seconds: float
    timestamp: str
    api_keys_verified: bool
    recommendations: List[str]


@dataclass
class DeploymentStatus:
    deployment_id: str
    status: str
    start_time: float
    last_activity: float
    process_count: int
    log_file_size: int
    errors_detected: List[str]


class SelfHealingWorkflow:
    """Self-healing workflow that monitors, detects issues, patches, and redeploys."""

    def __init__(self, config_file: str = "config/books_to_analyze_all_ai_ml.json"):
        self.config_file = config_file
        self.start_time = time.time()
        self.test_results: List[TestResult] = []
        self.deployment_status: Dict[str, DeploymentStatus] = {}
        self.process_monitor = ProcessMonitor()
        self.api_validator = APIKeyValidator()
        self.patch_manager = PatchManager()

        # Configuration
        self.max_test_runtime = 300  # 5 minutes
        self.max_deployment_runtime = 3600  # 1 hour
        self.check_interval = 30  # 30 seconds
        self.max_retries = 3

        # Logging
        self.log_file = (
            f"logs/self_healing_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        Path("logs").mkdir(exist_ok=True)

        logger.info("🔧 Self-Healing Workflow initialized")

    async def run_continuous_monitoring(self):
        """Run continuous monitoring with self-healing capabilities."""
        logger.info("🚀 Starting continuous self-healing monitoring...")

        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Monitoring Iteration {iteration}")
            logger.info(f"{'='*60}")

            try:
                # 1. Check for running processes
                running_processes = await self.process_monitor.get_running_processes()
                logger.info(f"📊 Found {len(running_processes)} running processes")

                # 2. Validate API keys
                api_status = await self.api_validator.validate_all_keys()
                logger.info(f"🔑 API Keys Status: {api_status}")

                # 3. Check deployment status
                deployment_status = await self.check_deployment_status()

                # 4. Detect issues and patch
                issues_detected = await self.detect_issues(
                    running_processes, api_status, deployment_status
                )

                if issues_detected:
                    logger.warning(f"⚠️ Detected {len(issues_detected)} issues")
                    await self.patch_and_redeploy(issues_detected)
                else:
                    logger.info("✅ No issues detected")

                # 5. Run tests if needed
                if await self.should_run_tests():
                    await self.run_model_tests()

                # 6. Log status
                await self.log_status(
                    iteration, running_processes, api_status, deployment_status
                )

                # 7. Wait before next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Error in monitoring iteration {iteration}: {e}")
                await asyncio.sleep(self.check_interval)

    async def detect_issues(
        self, processes: List[ProcessInfo], api_status: Dict, deployment_status: Dict
    ) -> List[str]:
        """Detect issues in running processes, API keys, and deployments."""
        issues = []

        # Check for stuck processes
        for process in processes:
            if process.runtime_seconds > process.expected_max_runtime:
                issues.append(
                    f"Stuck process: {process.name} (PID {process.pid}) running for {process.runtime_seconds:.1f}s"
                )

        # Check API key issues
        for api_name, status in api_status.items():
            if not status.get("valid", False):
                issues.append(
                    f"Invalid API key: {api_name} - {status.get('error', 'Unknown error')}"
                )

        # Check deployment issues
        for deployment_id, status in deployment_status.items():
            if status.get("errors_detected"):
                issues.extend(
                    [
                        f"Deployment {deployment_id}: {error}"
                        for error in status["errors_detected"]
                    ]
                )

        return issues

    async def patch_and_redeploy(self, issues: List[str]):
        """Patch detected issues and redeploy."""
        logger.info("🔧 Patching and redeploying...")

        for issue in issues:
            logger.info(f"🔍 Analyzing issue: {issue}")

            if "Stuck process" in issue:
                await self.kill_stuck_processes()
            elif "Invalid API key" in issue:
                await self.fix_api_keys()
            elif "Deployment" in issue:
                await self.restart_deployment()

        # Wait for processes to stop
        await self.wait_for_processes_to_stop()

        # Redeploy
        await self.redeploy_system()

    async def kill_stuck_processes(self):
        """Kill stuck processes."""
        logger.info("🛑 Killing stuck processes...")

        processes = await self.process_monitor.get_running_processes()
        for process in processes:
            if process.runtime_seconds > process.expected_max_runtime:
                logger.info(
                    f"🛑 Killing stuck process: {process.name} (PID {process.pid})"
                )
                try:
                    os.kill(process.pid, signal.SIGKILL)
                    logger.info(f"✅ Killed process {process.pid}")
                except ProcessLookupError:
                    logger.info(f"ℹ️ Process {process.pid} already terminated")
                except Exception as e:
                    logger.error(f"❌ Failed to kill process {process.pid}: {e}")

    async def wait_for_processes_to_stop(self, timeout: int = 30):
        """Wait for processes to stop with timeout."""
        logger.info("⏳ Waiting for processes to stop...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            processes = await self.process_monitor.get_running_processes()
            if not processes:
                logger.info("✅ All processes stopped")
                return True

            logger.info(f"⏳ {len(processes)} processes still running...")
            await asyncio.sleep(2)

        logger.warning("⚠️ Timeout waiting for processes to stop")
        return False

    async def run_model_tests(self):
        """Run tests for all models."""
        logger.info("🧪 Running model tests...")

        models_to_test = ["google", "deepseek", "claude", "gpt4"]

        for model in models_to_test:
            logger.info(f"🧪 Testing {model} model...")

            start_time = time.time()
            try:
                result = await self.test_model(model)
                runtime = time.time() - start_time

                test_result = TestResult(
                    test_name=f"{model}_model_test",
                    success=result["success"],
                    error_message=result.get("error"),
                    runtime_seconds=runtime,
                    timestamp=datetime.now().isoformat(),
                    api_keys_verified=result.get("api_key_valid", False),
                    recommendations=result.get("recommendations", []),
                )

                self.test_results.append(test_result)

                if result["success"]:
                    logger.info(f"✅ {model} model test passed ({runtime:.1f}s)")
                else:
                    logger.error(f"❌ {model} model test failed: {result.get('error')}")

            except Exception as e:
                logger.error(f"❌ {model} model test error: {e}")
                test_result = TestResult(
                    test_name=f"{model}_model_test",
                    success=False,
                    error_message=str(e),
                    runtime_seconds=time.time() - start_time,
                    timestamp=datetime.now().isoformat(),
                    api_keys_verified=False,
                    recommendations=[],
                )
                self.test_results.append(test_result)

    async def test_model(self, model_name: str) -> Dict[str, Any]:
        """Test a specific model."""
        try:
            # Create a simple test script for each model
            test_script = f"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from synthesis.models.{model_name}_model import {model_name.title()}Model

async def test_model():
    try:
        api_key = os.getenv('{model_name.upper()}_API_KEY')
        if not api_key:
            return {{'success': False, 'error': 'API key not set', 'api_key_valid': False}}

        model = {model_name.title()}Model()

        # Test with simple content
        test_content = "This is a test book about machine learning and data science."
        test_metadata = {{'title': 'Test Book', 'author': 'Test Author'}}

        result = await model.analyze_book_content(
            book_content=test_content,
            book_metadata=test_metadata
        )

        return {{
            'success': result.get('success', False),
            'error': result.get('error'),
            'api_key_valid': True,
            'recommendations': result.get('recommendations', [])
        }}

    except Exception as e:
        return {{'success': False, 'error': str(e), 'api_key_valid': False}}

if __name__ == "__main__":
    result = asyncio.run(test_model())
    print(json.dumps(result))
"""

            # Write test script
            test_file = f"temp_test_{model_name}.py"
            with open(test_file, "w") as f:
                f.write(test_script)

            # Run test with timeout
            try:
                result = subprocess.run(
                    ["python3", test_file],
                    capture_output=True,
                    text=True,
                    timeout=60,  # 1 minute timeout
                )

                if result.returncode == 0:
                    return json.loads(result.stdout)
                else:
                    return {
                        "success": False,
                        "error": result.stderr,
                        "api_key_valid": False,
                    }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": "Test timeout",
                    "api_key_valid": False,
                }
            finally:
                # Clean up test file
                if os.path.exists(test_file):
                    os.remove(test_file)

        except Exception as e:
            return {"success": False, "error": str(e), "api_key_valid": False}

    async def should_run_tests(self) -> bool:
        """Determine if tests should be run."""
        # Run tests if no recent successful tests
        recent_tests = [
            t
            for t in self.test_results
            if datetime.fromisoformat(t.timestamp)
            > datetime.now() - timedelta(minutes=10)
        ]

        if not recent_tests:
            return True

        # Run tests if any failed
        failed_tests = [t for t in recent_tests if not t.success]
        if failed_tests:
            return True

        return False

    async def check_deployment_status(self) -> Dict[str, Any]:
        """Check status of deployments."""
        status = {}

        # Check log files
        log_files = list(Path("logs").glob("workflow_*.log"))
        for log_file in log_files:
            deployment_id = log_file.stem
            try:
                stat = log_file.stat()
                status[deployment_id] = {
                    "last_modified": stat.st_mtime,
                    "size": stat.st_size,
                    "errors_detected": await self.detect_log_errors(log_file),
                }
            except Exception as e:
                logger.error(f"❌ Error checking log file {log_file}: {e}")

        return status

    async def detect_log_errors(self, log_file: Path) -> List[str]:
        """Detect errors in log file."""
        errors = []
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-100:]:  # Check last 100 lines
                    if "ERROR" in line or "❌" in line or "Failed" in line:
                        errors.append(line.strip())
        except Exception as e:
            logger.error(f"❌ Error reading log file {log_file}: {e}")

        return errors

    async def log_status(
        self,
        iteration: int,
        processes: List[ProcessInfo],
        api_status: Dict,
        deployment_status: Dict,
    ):
        """Log current status."""
        status = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "processes": [asdict(p) for p in processes],
            "api_status": api_status,
            "deployment_status": deployment_status,
            "test_results": [
                asdict(t) for t in self.test_results[-10:]
            ],  # Last 10 tests
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(status) + "\n")


class ProcessMonitor:
    """Monitor running processes."""

    def __init__(self):
        self.target_processes = [
            "automated_workflow.py",
            "simplified_recursive_analysis.py",
            "resilient_book_analyzer.py",
            "four_model_book_analyzer.py",
            "recursive_book_analysis.py",
        ]

    async def get_running_processes(self) -> List[ProcessInfo]:
        """Get information about running processes."""
        processes = []

        for proc in psutil.process_iter(["pid", "name", "create_time", "cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""

                # Check if this is one of our target processes
                for target in self.target_processes:
                    if target in cmdline:
                        runtime = time.time() - proc.info["create_time"]

                        process_info = ProcessInfo(
                            pid=proc.info["pid"],
                            name=proc.info["name"],
                            start_time=proc.info["create_time"],
                            command=cmdline,
                            status="running",
                            runtime_seconds=runtime,
                            expected_max_runtime=self._get_expected_runtime(target),
                        )

                        processes.append(process_info)
                        break

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes

    def _get_expected_runtime(self, process_name: str) -> int:
        """Get expected maximum runtime for a process."""
        runtime_map = {
            "automated_workflow.py": 3600,  # 1 hour
            "simplified_recursive_analysis.py": 300,  # 5 minutes
            "resilient_book_analyzer.py": 300,  # 5 minutes
            "four_model_book_analyzer.py": 300,  # 5 minutes
            "recursive_book_analysis.py": 300,  # 5 minutes
        }
        return runtime_map.get(process_name, 300)


class APIKeyValidator:
    """Validate API keys."""

    def __init__(self):
        self.required_keys = [
            "GOOGLE_API_KEY",
            "DEEPSEEK_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
        ]

    async def validate_all_keys(self) -> Dict[str, Dict[str, Any]]:
        """Validate all required API keys."""
        status = {}

        for key_name in self.required_keys:
            status[key_name] = await self.validate_key(key_name)

        return status

    async def validate_key(self, key_name: str) -> Dict[str, Any]:
        """Validate a specific API key."""
        try:
            api_key = os.getenv(key_name)

            if not api_key:
                return {"valid": False, "error": "Key not set"}

            if len(api_key) < 10:
                return {"valid": False, "error": "Key too short"}

            # Basic format validation
            if key_name == "GOOGLE_API_KEY" and not api_key.startswith("AIza"):
                return {"valid": False, "error": "Invalid Google API key format"}

            if key_name == "DEEPSEEK_API_KEY" and not api_key.startswith("sk-"):
                return {"valid": False, "error": "Invalid DeepSeek API key format"}

            if key_name == "ANTHROPIC_API_KEY" and not api_key.startswith("sk-ant-"):
                return {"valid": False, "error": "Invalid Anthropic API key format"}

            if key_name == "OPENAI_API_KEY" and not api_key.startswith("sk-"):
                return {"valid": False, "error": "Invalid OpenAI API key format"}

            return {"valid": True, "error": None}

        except Exception as e:
            return {"valid": False, "error": str(e)}


class PatchManager:
    """Manage patches and fixes."""

    def __init__(self):
        self.patch_history = []

    async def fix_api_keys(self):
        """Fix API key issues."""
        logger.info("🔑 Fixing API key issues...")

        # Load from .env.workflow
        env_file = Path(".env.workflow")
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value

            logger.info("✅ API keys loaded from .env.workflow")
        else:
            logger.error("❌ .env.workflow file not found")

    async def restart_deployment(self):
        """Restart deployment."""
        logger.info("🔄 Restarting deployment...")

        # Kill existing processes
        processes = await ProcessMonitor().get_running_processes()
        for process in processes:
            try:
                os.kill(process.pid, signal.SIGKILL)
                logger.info(f"🛑 Killed process {process.pid}")
            except ProcessLookupError:
                pass

        # Wait for processes to stop
        await asyncio.sleep(5)

        # Restart deployment
        await self.redeploy_system()

    async def redeploy_system(self):
        """Redeploy the system."""
        logger.info("🚀 Redeploying system...")

        # Launch new deployment
        cmd = [
            "python3",
            "scripts/automated_workflow.py",
            "--config",
            "config/books_to_analyze_all_ai_ml.json",
            "--budget",
            "410.0",
            "--output",
            "analysis_results/",
        ]

        # Add environment variables
        env = os.environ.copy()

        # Launch in background
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        logger.info(f"🚀 Launched new deployment (PID: {process.pid})")


async def main():
    """Main function."""
    workflow = SelfHealingWorkflow()
    await workflow.run_continuous_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
