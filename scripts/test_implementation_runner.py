#!/usr/bin/env python3
"""
Test Implementation Runner Script

Build automated test runner for all generated implementations:
- Import and instantiate each implementation class
- Run setup() → execute() → cleanup() lifecycle
- Capture exceptions and log results
- Generate test report with pass/fail statistics
"""

import os
import sys
import json
import logging
import traceback
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ImplementationTestRunner:
    """Automated test runner for generated implementations."""

    def __init__(
        self, phases_dir: str = "/Users/ryanranft/nba-simulator-aws/docs/phases"
    ):
        """Initialize test runner with phases directory."""
        self.phases_dir = Path(phases_dir)
        self.test_results = []
        self.summary_stats = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run tests for all generated implementations."""
        logger.info("🚀 Starting Implementation Test Runner")

        # Load file inventory
        inventory_file = Path("analysis_results/generated_files_inventory.json")
        if not inventory_file.exists():
            logger.error(
                "File inventory not found. Run review_generated_files.py first."
            )
            return {}

        with open(inventory_file, "r") as f:
            inventory = json.load(f)

        # Get Python implementation files
        python_files = inventory.get("file_inventory", {}).get(
            "python_implementations", []
        )

        logger.info(f"📋 Found {len(python_files)} Python implementation files to test")

        # Test each implementation
        for file_info in python_files:
            file_path = Path(file_info["file_path"])
            if file_path.exists():
                test_result = self._test_implementation(file_path, file_info)
                self.test_results.append(test_result)
                self.summary_stats["total_tests"] += 1

                if test_result["status"] == "passed":
                    self.summary_stats["passed"] += 1
                elif test_result["status"] == "failed":
                    self.summary_stats["failed"] += 1
                elif test_result["status"] == "skipped":
                    self.summary_stats["skipped"] += 1
                elif test_result["status"] == "error":
                    self.summary_stats["errors"] += 1
            else:
                logger.warning(f"File not found: {file_path}")

        logger.info(
            f"✅ Completed testing {self.summary_stats['total_tests']} implementations"
        )

        return {
            "summary_stats": self.summary_stats,
            "test_results": self.test_results,
            "success_rate": (
                self.summary_stats["passed"] / self.summary_stats["total_tests"] * 100
                if self.summary_stats["total_tests"] > 0
                else 0
            ),
        }

    def _test_implementation(
        self, file_path: Path, file_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test individual implementation file."""
        test_result = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "phase": file_info.get("phase", "unknown"),
            "recommendation_id": file_info.get("recommendation_id", "unknown"),
            "status": "unknown",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "setup_result": None,
            "execute_result": None,
            "cleanup_result": None,
            "errors": [],
            "warnings": [],
        }

        try:
            logger.info(f"🧪 Testing {file_path.name}...")

            # Import the module
            module = self._import_module(file_path)
            if not module:
                test_result["status"] = "error"
                test_result["errors"].append("Failed to import module")
                return test_result

            # Find implementation class
            impl_class = self._find_implementation_class(module)
            if not impl_class:
                test_result["status"] = "skipped"
                test_result["warnings"].append("No implementation class found")
                return test_result

            # Test lifecycle: setup → execute → cleanup
            start_time = time.time()

            # Setup
            setup_result = self._test_setup(impl_class)
            test_result["setup_result"] = setup_result

            if setup_result["status"] != "passed":
                test_result["status"] = "failed"
                test_result["errors"].extend(setup_result["errors"])
                return test_result

            # Execute
            execute_result = self._test_execute(impl_class)
            test_result["execute_result"] = execute_result

            if execute_result["status"] != "passed":
                test_result["status"] = "failed"
                test_result["errors"].extend(execute_result["errors"])
                return test_result

            # Cleanup
            cleanup_result = self._test_cleanup(impl_class)
            test_result["cleanup_result"] = cleanup_result

            if cleanup_result["status"] != "passed":
                test_result["status"] = "failed"
                test_result["errors"].extend(cleanup_result["errors"])
                return test_result

            # All tests passed
            test_result["status"] = "passed"

        except Exception as e:
            test_result["status"] = "error"
            test_result["errors"].append(f"Unexpected error: {str(e)}")
            test_result["errors"].append(traceback.format_exc())
            logger.error(f"Error testing {file_path.name}: {e}")

        finally:
            test_result["end_time"] = datetime.now().isoformat()
            test_result["duration_seconds"] = time.time() - start_time

        return test_result

    def _import_module(self, file_path: Path) -> Optional[Any]:
        """Import module from file path."""
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            logger.error(f"Failed to import {file_path}: {e}")
            return None

    def _find_implementation_class(self, module: Any) -> Optional[Any]:
        """Find implementation class in module."""
        try:
            # Look for classes that end with common implementation patterns
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and not attr_name.startswith("_")
                    and (
                        attr_name.endswith("Framework")
                        or attr_name.endswith("Implementation")
                        or attr_name.endswith("System")
                        or attr_name.endswith("Manager")
                        or attr_name.endswith("Service")
                    )
                ):
                    return attr

            # Fallback: return first class found
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and not attr_name.startswith("_"):
                    return attr

            return None
        except Exception as e:
            logger.error(f"Error finding implementation class: {e}")
            return None

    def _test_setup(self, impl_class: Any) -> Dict[str, Any]:
        """Test setup method."""
        result = {"status": "unknown", "errors": [], "warnings": []}

        try:
            # Try to instantiate the class
            instance = impl_class()

            # Check if setup method exists
            if hasattr(instance, "setup"):
                try:
                    setup_result = instance.setup()
                    result["status"] = "passed"
                    result["setup_returned"] = setup_result
                except Exception as e:
                    result["status"] = "failed"
                    result["errors"].append(f"Setup method failed: {str(e)}")
            elif hasattr(instance, "__init__"):
                # If no setup method, check if __init__ works
                result["status"] = "passed"
                result["warnings"].append("No setup method found, using __init__")
            else:
                result["status"] = "failed"
                result["errors"].append("No setup method found")

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"Failed to instantiate class: {str(e)}")

        return result

    def _test_execute(self, impl_class: Any) -> Dict[str, Any]:
        """Test execute method."""
        result = {"status": "unknown", "errors": [], "warnings": []}

        try:
            # Instantiate the class
            instance = impl_class()

            # Check if execute method exists
            if hasattr(instance, "execute"):
                try:
                    execute_result = instance.execute()
                    result["status"] = "passed"
                    result["execute_returned"] = execute_result
                except Exception as e:
                    result["status"] = "failed"
                    result["errors"].append(f"Execute method failed: {str(e)}")
            elif hasattr(instance, "run"):
                try:
                    run_result = instance.run()
                    result["status"] = "passed"
                    result["execute_returned"] = run_result
                    result["warnings"].append("Using run() method instead of execute()")
                except Exception as e:
                    result["status"] = "failed"
                    result["errors"].append(f"Run method failed: {str(e)}")
            else:
                result["status"] = "failed"
                result["errors"].append("No execute or run method found")

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"Failed to test execute: {str(e)}")

        return result

    def _test_cleanup(self, impl_class: Any) -> Dict[str, Any]:
        """Test cleanup method."""
        result = {"status": "unknown", "errors": [], "warnings": []}

        try:
            # Instantiate the class
            instance = impl_class()

            # Check if cleanup method exists
            if hasattr(instance, "cleanup"):
                try:
                    cleanup_result = instance.cleanup()
                    result["status"] = "passed"
                    result["cleanup_returned"] = cleanup_result
                except Exception as e:
                    result["status"] = "failed"
                    result["errors"].append(f"Cleanup method failed: {str(e)}")
            elif hasattr(instance, "__del__"):
                # If no cleanup method, check if __del__ works
                result["status"] = "passed"
                result["warnings"].append("No cleanup method found, using __del__")
            else:
                result["status"] = "passed"  # Cleanup is optional
                result["warnings"].append("No cleanup method found (optional)")

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"Failed to test cleanup: {str(e)}")

        return result

    def generate_report(self, test_results: Dict[str, Any]) -> str:
        """Generate test report."""
        report = []
        report.append("# Implementation Test Report")
        report.append(f"**Generated:** {datetime.now().isoformat()}")
        report.append(
            f"**Total Tests:** {test_results['summary_stats']['total_tests']}"
        )
        report.append(f"**Passed:** {test_results['summary_stats']['passed']}")
        report.append(f"**Failed:** {test_results['summary_stats']['failed']}")
        report.append(f"**Skipped:** {test_results['summary_stats']['skipped']}")
        report.append(f"**Errors:** {test_results['summary_stats']['errors']}")
        report.append(f"**Success Rate:** {test_results['success_rate']:.1f}%")
        report.append("")

        # Summary by phase
        phase_stats = {}
        for test_result in test_results["test_results"]:
            phase = test_result["phase"]
            if phase not in phase_stats:
                phase_stats[phase] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "errors": 0,
                }

            phase_stats[phase]["total"] += 1
            phase_stats[phase][test_result["status"]] += 1

        report.append("## Results by Phase")
        report.append("")
        for phase, stats in sorted(phase_stats.items()):
            success_rate = (
                stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            )
            report.append(f"### {phase.title()}")
            report.append(f"- **Total:** {stats['total']}")
            report.append(f"- **Passed:** {stats['passed']}")
            report.append(f"- **Failed:** {stats['failed']}")
            report.append(f"- **Skipped:** {stats['skipped']}")
            report.append(f"- **Errors:** {stats['errors']}")
            report.append(f"- **Success Rate:** {success_rate:.1f}%")
            report.append("")

        # Detailed results
        report.append("## Detailed Test Results")
        report.append("")

        for test_result in test_results["test_results"]:
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "error": "💥",
            }.get(test_result["status"], "❓")

            report.append(f"**{status_emoji} {test_result['file_name']}**")
            report.append(f"- **Phase:** {test_result['phase']}")
            report.append(
                f"- **Recommendation ID:** {test_result['recommendation_id']}"
            )
            report.append(f"- **Status:** {test_result['status']}")
            report.append(f"- **Duration:** {test_result['duration_seconds']:.2f}s")

            if test_result["errors"]:
                report.append("- **Errors:**")
                for error in test_result["errors"]:
                    report.append(f"  - {error}")

            if test_result["warnings"]:
                report.append("- **Warnings:**")
                for warning in test_result["warnings"]:
                    report.append(f"  - {warning}")

            report.append("")

        return "\n".join(report)

    def save_results(self, test_results: Dict[str, Any], report: str):
        """Save test results and report."""
        # Save JSON results
        results_file = Path("analysis_results/implementation_test_results.json")
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, "w") as f:
            json.dump(test_results, f, indent=2)

        # Save markdown report
        report_file = Path("analysis_results/implementation_test_report.md")
        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"📊 Test results saved to {results_file}")
        logger.info(f"📋 Test report saved to {report_file}")


def main():
    """Main execution function."""
    logger.info("🚀 Starting Implementation Test Runner")

    runner = ImplementationTestRunner()

    # Run tests
    test_results = runner.run_all_tests()

    if not test_results:
        logger.error("No tests to run. Exiting.")
        return

    # Generate report
    report = runner.generate_report(test_results)

    # Save results
    runner.save_results(test_results, report)

    # Print summary
    stats = test_results["summary_stats"]
    print("\n" + "=" * 60)
    print("🧪 IMPLEMENTATION TEST RUNNER SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {stats['total_tests']}")
    print(f"Passed: {stats['passed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print(f"Success Rate: {test_results['success_rate']:.1f}%")

    print(
        f"\n✅ Test runner complete! Check analysis_results/implementation_test_report.md for full report"
    )


if __name__ == "__main__":
    main()
