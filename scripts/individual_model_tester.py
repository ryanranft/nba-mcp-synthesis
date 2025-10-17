#!/usr/bin/env python3
"""
Individual Model Tester
Tests each model individually to identify specific issues.
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from mcp_server.env_helper import get_hierarchical_env

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class ModelTestResult:
    model_name: str
    success: bool
    error_message: Optional[str]
    runtime_seconds: float
    api_key_valid: bool
    recommendations_count: int
    cost: float
    timestamp: str


class IndividualModelTester:
    """Test each model individually."""

    def __init__(self):
        self.test_content = "This is a test book about machine learning, data science, and statistical analysis for basketball analytics."
        self.test_metadata = {
            "title": "Test Book for Model Validation",
            "author": "Test Author",
            "category": "test",
        }
        self.results: List[ModelTestResult] = []

    async def test_all_models(self) -> List[ModelTestResult]:
        """Test all models."""
        print("🧪 Testing all models individually...")

        models = ["google", "deepseek", "claude", "gpt4"]

        for model in models:
            print(f"\n{'='*50}")
            print(f"🧪 Testing {model.upper()} model...")
            print(f"{'='*50}")

            result = await self.test_model(model)
            self.results.append(result)

            if result.success:
                print(f"✅ {model.upper()} test PASSED")
                print(f"   Runtime: {result.runtime_seconds:.1f}s")
                print(f"   Recommendations: {result.recommendations_count}")
                print(f"   Cost: ${result.cost:.4f}")
            else:
                print(f"❌ {model.upper()} test FAILED")
                print(f"   Error: {result.error_message}")
                print(f"   Runtime: {result.runtime_seconds:.1f}s")

        return self.results

    async def test_model(self, model_name: str) -> ModelTestResult:
        """Test a specific model."""
        start_time = time.time()

        try:
            # Import the model
            if model_name == "google":
                from synthesis.models.google_model import GoogleModel

                model = GoogleModel()  # Will get API key from environment variables
            elif model_name == "deepseek":
                from synthesis.models.deepseek_model import DeepSeekModel

                model = DeepSeekModel()
            elif model_name == "claude":
                from synthesis.models.claude_model import ClaudeModel

                model = ClaudeModel()
            elif model_name == "gpt4":
                from synthesis.models.gpt4_model import GPT4Model

                model = GPT4Model()
            else:
                raise ValueError(f"Unknown model: {model_name}")

            # Test API key
            api_key_valid = await self._test_api_key(model_name)

            if not api_key_valid:
                return ModelTestResult(
                    model_name=model_name,
                    success=False,
                    error_message="API key not valid",
                    runtime_seconds=time.time() - start_time,
                    api_key_valid=False,
                    recommendations_count=0,
                    cost=0.0,
                    timestamp=datetime.now().isoformat(),
                )

            # Test model functionality
            result = await asyncio.wait_for(
                model.analyze_book_content(
                    book_content=self.test_content, book_metadata=self.test_metadata
                ),
                timeout=120,  # 2 minute timeout
            )

            runtime = time.time() - start_time

            return ModelTestResult(
                model_name=model_name,
                success=result.get("success", False),
                error_message=result.get("error"),
                runtime_seconds=runtime,
                api_key_valid=True,
                recommendations_count=len(result.get("recommendations", [])),
                cost=result.get("cost", 0.0),
                timestamp=datetime.now().isoformat(),
            )

        except asyncio.TimeoutError:
            return ModelTestResult(
                model_name=model_name,
                success=False,
                error_message="Test timeout (2 minutes)",
                runtime_seconds=time.time() - start_time,
                api_key_valid=False,
                recommendations_count=0,
                cost=0.0,
                timestamp=datetime.now().isoformat(),
            )
        except Exception as e:
            return ModelTestResult(
                model_name=model_name,
                success=False,
                error_message=str(e),
                runtime_seconds=time.time() - start_time,
                api_key_valid=False,
                recommendations_count=0,
                cost=0.0,
                timestamp=datetime.now().isoformat(),
            )

    async def _test_api_key(self, model_name: str) -> bool:
        """Test if API key is valid."""
        # Try new naming convention first, then fallback to old
        api_key = get_hierarchical_env(
            f"{model_name.upper()}_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )

        if not api_key:
            print(f"❌ {model_name.upper()}_API_KEY not set")
            return False

        if len(api_key) < 10:
            print(f"❌ {model_name.upper()}_API_KEY too short")
            return False

        # Basic format validation
        if model_name == "google" and not api_key.startswith("AIza"):
            print(
                f"❌ {model_name.upper()}_API_KEY invalid format (should start with 'AIza')"
            )
            return False

        if model_name == "deepseek" and not api_key.startswith("sk-"):
            print(
                f"❌ {model_name.upper()}_API_KEY invalid format (should start with 'sk-')"
            )
            return False

        if model_name == "claude" and not api_key.startswith("sk-ant-"):
            print(
                f"❌ {model_name.upper()}_API_KEY invalid format (should start with 'sk-ant-')"
            )
            return False

        if model_name == "gpt4" and not api_key.startswith("sk-"):
            print(
                f"❌ {model_name.upper()}_API_KEY invalid format (should start with 'sk-')"
            )
            return False

        print(f"✅ {model_name.upper()}_API_KEY format valid")
        return True

    def generate_report(self) -> Dict[str, Any]:
        """Generate test report."""
        successful_models = [r for r in self.results if r.success]
        failed_models = [r for r in self.results if not r.success]

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_models_tested": len(self.results),
            "successful_models": len(successful_models),
            "failed_models": len(failed_models),
            "success_rate": (
                len(successful_models) / len(self.results) if self.results else 0
            ),
            "results": [
                {
                    "model_name": r.model_name,
                    "success": r.success,
                    "error_message": r.error_message,
                    "runtime_seconds": r.runtime_seconds,
                    "api_key_valid": r.api_key_valid,
                    "recommendations_count": r.recommendations_count,
                    "cost": r.cost,
                    "timestamp": r.timestamp,
                }
                for r in self.results
            ],
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        for result in self.results:
            if not result.success:
                if not result.api_key_valid:
                    recommendations.append(
                        f"Fix {result.model_name.upper()} API key: {result.error_message}"
                    )
                elif "timeout" in result.error_message.lower():
                    recommendations.append(
                        f"Increase timeout for {result.model_name.upper()} model"
                    )
                elif "import" in result.error_message.lower():
                    recommendations.append(
                        f"Fix import issues for {result.model_name.upper()} model"
                    )
                else:
                    recommendations.append(
                        f"Debug {result.model_name.upper()} model: {result.error_message}"
                    )

        return recommendations


async def main():
    """Main function."""
    print("🚀 Starting Individual Model Testing...")

    tester = IndividualModelTester()
    results = await tester.test_all_models()

    # Generate report
    report = tester.generate_report()

    # Save report
    report_file = (
        f"logs/model_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 TEST SUMMARY:")
    print(f"   Total models tested: {report['total_models_tested']}")
    print(f"   Successful: {report['successful_models']}")
    print(f"   Failed: {report['failed_models']}")
    print(f"   Success rate: {report['success_rate']:.1%}")

    if report["recommendations"]:
        print(f"\n🔧 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"   - {rec}")

    print(f"\n💾 Report saved to: {report_file}")

    return report


if __name__ == "__main__":
    asyncio.run(main())
