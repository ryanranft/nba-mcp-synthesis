#!/usr/bin/env python3
"""
Master Self-Healing Workflow Orchestrator
Orchestrates the complete self-healing workflow with monitoring, testing, and deployment.
"""

import os
import sys
import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MasterSelfHealingOrchestrator:
    """Master orchestrator for self-healing workflow."""

    def __init__(self):
        self.start_time = time.time()
        self.iteration = 0
        self.max_iterations = 10  # Maximum iterations before stopping
        self.success_threshold = 0.8  # 80% success rate required

        # Initialize components
        self.status_checker = None
        self.model_tester = None
        self.deployment_manager = None

        # Results tracking
        self.all_results = []
        self.successful_models = set()
        self.failed_models = set()

        print("🚀 Master Self-Healing Workflow Orchestrator initialized")

    async def run_complete_workflow(self):
        """Run the complete self-healing workflow."""
        print("🚀 Starting Master Self-Healing Workflow...")
        print(f"📊 Success threshold: {self.success_threshold:.1%}")
        print(f"🔄 Max iterations: {self.max_iterations}")

        while self.iteration < self.max_iterations:
            self.iteration += 1
            print(f"\n{'='*80}")
            print(f"🔄 ITERATION {self.iteration}")
            print(f"{'='*80}")

            try:
                # Step 1: Check current status
                await self._check_current_status()

                # Step 2: Kill any stuck processes
                await self._kill_stuck_processes()

                # Step 3: Validate API keys
                await self._validate_api_keys()

                # Step 4: Test all models
                test_results = await self._test_all_models()

                # Step 5: Analyze results
                analysis = await self._analyze_results(test_results)

                # Step 6: Check if we've achieved success
                if await self._check_success():
                    print("🎉 SUCCESS! All models working correctly!")
                    break

                # Step 7: Apply fixes
                await self._apply_fixes(analysis)

                # Step 8: Wait before next iteration
                print(f"⏳ Waiting 30 seconds before next iteration...")
                await asyncio.sleep(30)

            except Exception as e:
                print(f"❌ Error in iteration {self.iteration}: {e}")
                await asyncio.sleep(30)

        # Final report
        await self._generate_final_report()

    async def _check_current_status(self):
        """Check current status of all processes."""
        print("📊 Checking current status...")

        # Import and run status checker
        from scripts.immediate_status_checker import ImmediateStatusChecker
        checker = ImmediateStatusChecker()
        status = checker.check_all_processes()

        print(f"📊 Found {len(status)} running processes")

        # Check for stuck processes
        stuck_processes = [p for p in status if p.runtime_seconds > p.expected_max_runtime]
        if stuck_processes:
            print(f"⚠️ Found {len(stuck_processes)} stuck processes")
            for process in stuck_processes:
                print(f"   - {process.name} (PID {process.pid}): {process.runtime_seconds:.1f}s")

    async def _kill_stuck_processes(self):
        """Kill any stuck processes."""
        print("🛑 Checking for stuck processes...")

        # Import and run deployment manager
        from scripts.deployment_manager import DeploymentManager
        manager = DeploymentManager()

        # Kill all deployments
        killed = manager.kill_all_deployments()
        if killed:
            print("🛑 Killed stuck processes")
            # Wait for processes to stop
            manager.wait_for_processes_to_stop()
        else:
            print("ℹ️ No stuck processes found")

    async def _validate_api_keys(self):
        """Validate all API keys."""
        print("🔑 Validating API keys...")

        required_keys = ['GOOGLE_API_KEY', 'DEEPSEEK_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
        valid_keys = 0

        for key in required_keys:
            value = os.getenv(key)
            if value and len(value) > 10:
                valid_keys += 1
                print(f"✅ {key}: Valid")
            else:
                print(f"❌ {key}: Invalid or not set")

        print(f"🔑 API Keys: {valid_keys}/{len(required_keys)} valid")

        if valid_keys < len(required_keys):
            print("⚠️ Some API keys are invalid - this may cause test failures")

    async def _test_all_models(self) -> List[Dict[str, Any]]:
        """Test all models."""
        print("🧪 Testing all models...")

        # Import and run model tester
        from scripts.individual_model_tester import IndividualModelTester
        tester = IndividualModelTester()

        results = await tester.test_all_models()

        # Convert to dict format
        test_results = []
        for result in results:
            test_results.append({
                'model_name': result.model_name,
                'success': result.success,
                'error_message': result.error_message,
                'runtime_seconds': result.runtime_seconds,
                'api_key_valid': result.api_key_valid,
                'recommendations_count': result.recommendations_count,
                'cost': result.cost,
                'timestamp': result.timestamp
            })

        return test_results

    async def _analyze_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test results."""
        print("📊 Analyzing test results...")

        successful_models = [r for r in test_results if r['success']]
        failed_models = [r for r in test_results if not r['success']]

        analysis = {
            'total_models': len(test_results),
            'successful_models': len(successful_models),
            'failed_models': len(failed_models),
            'success_rate': len(successful_models) / len(test_results) if test_results else 0,
            'successful_model_names': [r['model_name'] for r in successful_models],
            'failed_model_names': [r['model_name'] for r in failed_models],
            'issues': []
        }

        # Identify specific issues
        for result in failed_models:
            if not result['api_key_valid']:
                analysis['issues'].append(f"API key issue: {result['model_name']}")
            elif 'timeout' in result['error_message'].lower():
                analysis['issues'].append(f"Timeout issue: {result['model_name']}")
            elif 'import' in result['error_message'].lower():
                analysis['issues'].append(f"Import issue: {result['model_name']}")
            else:
                analysis['issues'].append(f"Unknown issue: {result['model_name']} - {result['error_message']}")

        print(f"📊 Analysis: {analysis['successful_models']}/{analysis['total_models']} models successful ({analysis['success_rate']:.1%})")

        if analysis['issues']:
            print("⚠️ Issues detected:")
            for issue in analysis['issues']:
                print(f"   - {issue}")

        return analysis

    async def _check_success(self) -> bool:
        """Check if we've achieved success."""
        # Check if we have enough successful models
        if len(self.successful_models) >= 3:  # At least 3 out of 4 models working
            return True

        # Check if success rate is above threshold
        if len(self.all_results) > 0:
            recent_results = self.all_results[-4:]  # Last 4 tests
            success_rate = sum(1 for r in recent_results if r['success']) / len(recent_results)
            if success_rate >= self.success_threshold:
                return True

        return False

    async def _apply_fixes(self, analysis: Dict[str, Any]):
        """Apply fixes based on analysis."""
        print("🔧 Applying fixes...")

        for issue in analysis['issues']:
            if 'API key issue' in issue:
                print(f"🔑 Fixing API key issue: {issue}")
                await self._fix_api_keys()
            elif 'timeout issue' in issue:
                print(f"⏰ Fixing timeout issue: {issue}")
                await self._fix_timeout_issues()
            elif 'import issue' in issue:
                print(f"📦 Fixing import issue: {issue}")
                await self._fix_import_issues()
            else:
                print(f"🔧 Applying general fix for: {issue}")
                await self._apply_general_fixes()

    async def _fix_api_keys(self):
        """Fix API key issues."""
        print("🔑 Fixing API keys...")

        # Load from .env.workflow
        env_file = Path(".env.workflow")
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value

            print("✅ API keys loaded from .env.workflow")
        else:
            print("❌ .env.workflow file not found")

    async def _fix_timeout_issues(self):
        """Fix timeout issues."""
        print("⏰ Fixing timeout issues...")

        # Increase timeout in model configurations
        # This would typically involve updating configuration files
        print("ℹ️ Timeout issues require manual configuration updates")

    async def _fix_import_issues(self):
        """Fix import issues."""
        print("📦 Fixing import issues...")

        # Check if all required modules exist
        required_modules = [
            'synthesis.models.google_model',
            'synthesis.models.deepseek_model',
            'synthesis.models.claude_model',
            'synthesis.models.gpt4_model'
        ]

        for module in required_modules:
            try:
                __import__(module)
                print(f"✅ {module}: Available")
            except ImportError as e:
                print(f"❌ {module}: {e}")

    async def _apply_general_fixes(self):
        """Apply general fixes."""
        print("🔧 Applying general fixes...")

        # Restart the system
        print("🔄 Restarting system...")

        # Kill all processes
        from scripts.deployment_manager import DeploymentManager
        manager = DeploymentManager()
        manager.kill_all_deployments()
        manager.wait_for_processes_to_stop()

        # Wait a bit
        await asyncio.sleep(5)

    async def _generate_final_report(self):
        """Generate final report."""
        print("\n" + "="*80)
        print("📊 FINAL REPORT")
        print("="*80)

        total_runtime = time.time() - self.start_time

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_runtime_seconds': total_runtime,
            'iterations_completed': self.iteration,
            'max_iterations': self.max_iterations,
            'successful_models': list(self.successful_models),
            'failed_models': list(self.failed_models),
            'all_results': self.all_results,
            'success_rate': len(self.successful_models) / 4 if self.successful_models else 0
        }

        print(f"⏱️ Total runtime: {total_runtime:.1f} seconds")
        print(f"🔄 Iterations completed: {self.iteration}/{self.max_iterations}")
        print(f"✅ Successful models: {len(self.successful_models)}/4")
        print(f"❌ Failed models: {len(self.failed_models)}/4")
        print(f"📊 Success rate: {report['success_rate']:.1%}")

        # Save report
        report_file = f"logs/master_workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"💾 Report saved to: {report_file}")

async def main():
    """Main function."""
    orchestrator = MasterSelfHealingOrchestrator()
    await orchestrator.run_complete_workflow()

if __name__ == "__main__":
    asyncio.run(main())

