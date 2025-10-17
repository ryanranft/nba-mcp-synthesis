#!/usr/bin/env python3
"""
Focused Working Model Workflow
Uses only the working models (DeepSeek) with circuit breaker protection.
"""

import os
import sys
import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FocusedWorkingModelWorkflow:
    """Focused workflow using only working models."""

    def __init__(self):
        self.start_time = time.time()
        self.working_models = ["deepseek"]  # Only DeepSeek is confirmed working
        self.failed_models = ["google", "claude", "gpt4"]  # These have issues
        self.results = []

        print("🚀 Focused Working Model Workflow initialized")
        print(f"✅ Working models: {self.working_models}")
        print(f"❌ Failed models: {self.failed_models}")

    async def run_analysis(
        self, book_name: str = "Machine Learning for Absolute Beginners"
    ):
        """Run analysis using only working models."""
        print(f"\n{'='*60}")
        print(f"📚 Analyzing: {book_name}")
        print(f"{'='*60}")

        try:
            # Import only the working model
            from synthesis.models.deepseek_model import DeepSeekModel

            # Initialize model
            model = DeepSeekModel()

            # Test content
            test_content = f"This is a test analysis of the book '{book_name}' focusing on machine learning, data science, and statistical analysis for basketball analytics."
            test_metadata = {
                "title": book_name,
                "author": "Test Author",
                "category": "test",
            }

            print("🧪 Running DeepSeek analysis...")
            start_time = time.time()

            # Run analysis with timeout
            result = await asyncio.wait_for(
                model.analyze_book_content(
                    book_content=test_content, book_metadata=test_metadata
                ),
                timeout=120,  # 2 minute timeout
            )

            runtime = time.time() - start_time

            if result.get("success", False):
                recommendations = result.get("recommendations", [])
                cost = result.get("cost", 0.0)

                print(f"✅ Analysis successful!")
                print(f"   Runtime: {runtime:.1f}s")
                print(f"   Recommendations: {len(recommendations)}")
                print(f"   Cost: ${cost:.4f}")

                # Show first few recommendations
                if recommendations:
                    print(f"\n📋 Sample recommendations:")
                    for i, rec in enumerate(recommendations[:3]):
                        print(f"   {i+1}. {rec.get('title', 'Untitled')}")

                return {
                    "success": True,
                    "model": "deepseek",
                    "runtime": runtime,
                    "recommendations_count": len(recommendations),
                    "cost": cost,
                    "recommendations": recommendations,
                }
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "model": "deepseek",
                    "runtime": runtime,
                    "error": result.get("error", "Unknown error"),
                }

        except asyncio.TimeoutError:
            print("❌ Analysis timeout (2 minutes)")
            return {
                "success": False,
                "model": "deepseek",
                "runtime": 120,
                "error": "Timeout",
            }
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return {
                "success": False,
                "model": "deepseek",
                "runtime": time.time() - start_time,
                "error": str(e),
            }

    async def run_multiple_tests(self, test_count: int = 3):
        """Run multiple tests to verify consistency."""
        print(f"\n🔄 Running {test_count} tests to verify consistency...")

        test_books = [
            "Machine Learning for Absolute Beginners",
            "Statistics 601 Advanced Statistical Methods",
            "Basketball on Paper",
        ]

        for i in range(test_count):
            book_name = test_books[i % len(test_books)]
            print(f"\n🧪 Test {i+1}/{test_count}")

            result = await self.run_analysis(book_name)
            self.results.append(result)

            if result["success"]:
                print(f"✅ Test {i+1} PASSED")
            else:
                print(f"❌ Test {i+1} FAILED: {result.get('error', 'Unknown error')}")

            # Wait between tests
            if i < test_count - 1:
                print("⏳ Waiting 10 seconds before next test...")
                await asyncio.sleep(10)

        # Analyze results
        successful_tests = [r for r in self.results if r["success"]]
        failed_tests = [r for r in self.results if not r["success"]]

        print(f"\n📊 TEST SUMMARY:")
        print(f"   Total tests: {len(self.results)}")
        print(f"   Successful: {len(successful_tests)}")
        print(f"   Failed: {len(failed_tests)}")
        print(f"   Success rate: {len(successful_tests)/len(self.results):.1%}")

        if successful_tests:
            avg_runtime = sum(r["runtime"] for r in successful_tests) / len(
                successful_tests
            )
            avg_cost = sum(r["cost"] for r in successful_tests) / len(successful_tests)
            avg_recommendations = sum(
                r["recommendations_count"] for r in successful_tests
            ) / len(successful_tests)

            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"   Average runtime: {avg_runtime:.1f}s")
            print(f"   Average cost: ${avg_cost:.4f}")
            print(f"   Average recommendations: {avg_recommendations:.1f}")

        return {
            "total_tests": len(self.results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "success_rate": len(successful_tests) / len(self.results),
            "results": self.results,
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate final report."""
        total_runtime = time.time() - self.start_time

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_runtime_seconds": total_runtime,
            "working_models": self.working_models,
            "failed_models": self.failed_models,
            "test_results": self.results,
            "summary": {
                "total_tests": len(self.results),
                "successful_tests": len([r for r in self.results if r["success"]]),
                "failed_tests": len([r for r in self.results if not r["success"]]),
                "success_rate": (
                    len([r for r in self.results if r["success"]]) / len(self.results)
                    if self.results
                    else 0
                ),
            },
        }

        return report


async def main():
    """Main function."""
    print("🚀 Starting Focused Working Model Workflow...")

    # API keys should be set via environment variables or secrets manager
    # Ensure DEEPSEEK_API_KEY is set before running
    if "DEEPSEEK_API_KEY" not in os.environ:
        print("❌ ERROR: DEEPSEEK_API_KEY environment variable not set")
        print("Please set it before running:")
        print("  export DEEPSEEK_API_KEY=your_key_here")
        return

    workflow = FocusedWorkingModelWorkflow()

    # Run multiple tests
    results = await workflow.run_multiple_tests(3)

    # Generate report
    report = workflow.generate_report()

    # Save report
    report_file = (
        f"logs/focused_workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    Path("logs").mkdir(exist_ok=True)

    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Report saved to: {report_file}")

    # Final status
    if results["success_rate"] >= 0.8:
        print("🎉 SUCCESS! Working model is reliable!")
    else:
        print("⚠️ Working model has reliability issues")

    return report


if __name__ == "__main__":
    asyncio.run(main())
