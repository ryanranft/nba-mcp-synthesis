#!/usr/bin/env python3
"""
A/B Testing Framework for Model Combinations

This module provides automated A/B testing capabilities for comparing different
AI model combinations in book analysis and synthesis tasks.

Features:
- Test Gemini vs Claude vs mixed approaches
- Compare synthesis quality metrics
- Measure cost/performance trade-offs
- Generate comprehensive comparison reports

Usage:
    python scripts/ab_testing_framework.py \
        --test gemini-vs-claude \
        --books 5 \
        --output results/ab_test_report.md
"""

import logging
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

# Add scripts directory to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@dataclass
class ModelConfig:
    """Configuration for a model combination test."""

    name: str
    description: str
    primary_model: str  # "gemini" or "claude"
    secondary_model: Optional[str] = None  # For mixed approaches
    use_consensus: bool = True
    similarity_threshold: float = 0.70


@dataclass
class TestResult:
    """Results from testing a single model configuration."""

    config_name: str
    book_title: str

    # Quality Metrics
    recommendations_found: int
    critical_count: int
    important_count: int
    nice_to_have_count: int
    convergence_achieved: bool
    iterations_required: int

    # Cost Metrics
    total_cost_usd: float
    gemini_cost_usd: float
    claude_cost_usd: float

    # Performance Metrics
    processing_time_seconds: float
    tokens_used: int
    cache_hits: int

    # Content Metrics
    characters_analyzed: int
    pages_analyzed: int

    # Timestamp
    timestamp: str = datetime.now().isoformat()


class ABTestingFramework:
    """
    Framework for running A/B tests on different model combinations.
    """

    # Predefined test configurations
    CONFIGS = {
        "gemini_only": ModelConfig(
            name="gemini_only",
            description="Gemini 1.5 Pro only (no consensus)",
            primary_model="gemini",
            secondary_model=None,
            use_consensus=False,
        ),
        "claude_only": ModelConfig(
            name="claude_only",
            description="Claude Sonnet 4 only (no consensus)",
            primary_model="claude",
            secondary_model=None,
            use_consensus=False,
        ),
        "gemini_claude_consensus": ModelConfig(
            name="gemini_claude_consensus",
            description="Gemini + Claude with 70% consensus",
            primary_model="gemini",
            secondary_model="claude",
            use_consensus=True,
            similarity_threshold=0.70,
        ),
        "gemini_claude_high_consensus": ModelConfig(
            name="gemini_claude_high_consensus",
            description="Gemini + Claude with 85% consensus",
            primary_model="gemini",
            secondary_model="claude",
            use_consensus=True,
            similarity_threshold=0.85,
        ),
    }

    def __init__(self, results_dir: Path = Path("ab_testing_results")):
        """
        Initialize the A/B testing framework.

        Args:
            results_dir: Directory to store test results
        """
        self.results_dir = results_dir
        self.results_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"A/B Testing Framework initialized")
        logger.info(f"Results directory: {self.results_dir}")

    async def run_single_test(
        self, config: ModelConfig, book_path: str, book_title: str
    ) -> TestResult:
        """
        Run a single A/B test with the specified configuration.

        Args:
            config: Model configuration to test
            book_path: Path to the book file
            book_title: Title of the book

        Returns:
            TestResult with all metrics
        """
        logger.info(f"🧪 Running test: {config.name} on {book_title}")

        # Integrate with actual high_context_book_analyzer
        try:
            # Dynamically import to avoid circular dependencies
            from high_context_book_analyzer import HighContextBookAnalyzer

            # Create analyzer with config settings
            analyzer = HighContextBookAnalyzer(
                model_combination=self._config_to_model_combination(config),
                consensus_threshold=config.similarity_threshold,
            )

            # Run analysis
            start_time = datetime.now()
            analysis_result = await analyzer.analyze_book_async(book_path)
            processing_time = (datetime.now() - start_time).total_seconds()

            # Extract metrics from analysis result
            recommendations = analysis_result.get("recommendations", [])
            convergence_tracker = analysis_result.get("convergence_tracker", {})
            cost_data = analysis_result.get("cost", {})

            # Count by priority
            critical_count = sum(
                1 for r in recommendations if r.get("priority") == "critical"
            )
            important_count = sum(
                1 for r in recommendations if r.get("priority") == "important"
            )
            nice_to_have_count = sum(
                1 for r in recommendations if r.get("priority") == "nice-to-have"
            )

            result = TestResult(
                config_name=config.name,
                book_title=book_title,
                recommendations_found=len(recommendations),
                critical_count=critical_count,
                important_count=important_count,
                nice_to_have_count=nice_to_have_count,
                convergence_achieved=convergence_tracker.get(
                    "convergence_achieved", False
                ),
                iterations_required=convergence_tracker.get("iterations_completed", 0),
                total_cost_usd=cost_data.get("total", 0.0),
                gemini_cost_usd=cost_data.get("gemini", 0.0),
                claude_cost_usd=cost_data.get("claude", 0.0),
                processing_time_seconds=processing_time,
                tokens_used=cost_data.get("tokens_used", 0),
                cache_hits=analysis_result.get("cache_hits", 0),
                characters_analyzed=analysis_result.get("characters_analyzed", 0),
                pages_analyzed=analysis_result.get("pages_analyzed", 0),
            )

            logger.info(
                f"  ✅ Test complete: {result.recommendations_found} recommendations"
            )
            logger.info(f"  💰 Cost: ${result.total_cost_usd:.4f}")
            logger.info(f"  ⏱️  Time: {result.processing_time_seconds:.1f}s")

            return result

        except Exception as e:
            logger.error(f"  ❌ Test failed: {e}")
            # Return minimal result on failure
            return TestResult(
                config_name=config.name,
                book_title=book_title,
                recommendations_found=0,
                critical_count=0,
                important_count=0,
                nice_to_have_count=0,
                convergence_achieved=False,
                iterations_required=0,
                total_cost_usd=0.0,
                gemini_cost_usd=0.0,
                claude_cost_usd=0.0,
                processing_time_seconds=0.0,
                tokens_used=0,
                cache_hits=0,
                characters_analyzed=0,
                pages_analyzed=0,
            )

    def _config_to_model_combination(self, config: ModelConfig) -> str:
        """
        Convert ModelConfig to model_combination string.

        Args:
            config: ModelConfig instance

        Returns:
            Model combination string
        """
        if config.use_consensus and config.secondary_model:
            return "gemini+claude"
        elif config.primary_model == "gemini":
            return "gemini_only"
        elif config.primary_model == "claude":
            return "claude_only"
        else:
            return "gemini+claude"

    async def run_comparison_test(
        self, config_names: List[str], book_paths: List[str], book_titles: List[str]
    ) -> Dict[str, List[TestResult]]:
        """
        Run A/B comparison across multiple configurations and books.

        Args:
            config_names: Names of configurations to test
            book_paths: List of book paths
            book_titles: List of book titles

        Returns:
            Dictionary mapping config names to lists of test results
        """
        logger.info(f"🚀 Starting A/B comparison test")
        logger.info(f"  Configurations: {', '.join(config_names)}")
        logger.info(f"  Books: {len(book_paths)}")

        results = {config_name: [] for config_name in config_names}

        for book_path, book_title in zip(book_paths, book_titles):
            logger.info(f"\n📚 Testing book: {book_title}")

            for config_name in config_names:
                config = self.CONFIGS[config_name]
                result = await self.run_single_test(config, book_path, book_title)
                results[config_name].append(result)

        logger.info(f"\n✅ A/B test complete!")
        return results

    def generate_comparison_report(
        self, results: Dict[str, List[TestResult]], output_path: Optional[Path] = None
    ) -> str:
        """
        Generate a comprehensive comparison report.

        Args:
            results: Dictionary of test results by configuration
            output_path: Optional path to save the report

        Returns:
            Markdown-formatted report
        """
        logger.info(f"📊 Generating comparison report...")

        report_lines = [
            "# A/B Testing Comparison Report",
            f"\n**Generated**: {datetime.now().isoformat()}",
            f"**Configurations Tested**: {len(results)}",
            f"**Books Analyzed**: {len(next(iter(results.values())))}",
            "\n---\n",
        ]

        # Summary Table
        report_lines.append("## Summary Comparison\n")
        report_lines.append(
            "| Configuration | Avg Recommendations | Avg Cost | Avg Time | Quality Score |"
        )
        report_lines.append(
            "|--------------|---------------------|----------|----------|---------------|"
        )

        for config_name, test_results in results.items():
            avg_recs = sum(r.recommendations_found for r in test_results) / len(
                test_results
            )
            avg_cost = sum(r.total_cost_usd for r in test_results) / len(test_results)
            avg_time = sum(r.processing_time_seconds for r in test_results) / len(
                test_results
            )

            # Calculate quality score (critical * 3 + important * 2 + nice * 1)
            avg_quality = sum(
                r.critical_count * 3 + r.important_count * 2 + r.nice_to_have_count
                for r in test_results
            ) / len(test_results)

            report_lines.append(
                f"| {config_name} | {avg_recs:.1f} | ${avg_cost:.4f} | {avg_time:.1f}s | {avg_quality:.1f} |"
            )

        # Detailed Metrics
        report_lines.append("\n## Detailed Metrics\n")

        for config_name, test_results in results.items():
            config = self.CONFIGS[config_name]
            report_lines.append(f"### {config_name}\n")
            report_lines.append(f"**Description**: {config.description}\n")

            report_lines.append(
                "| Book | Recs | Critical | Important | Nice | Cost | Time | Convergence |"
            )
            report_lines.append(
                "|------|------|----------|-----------|------|------|------|-------------|"
            )

            for result in test_results:
                convergence = "✅" if result.convergence_achieved else "❌"
                report_lines.append(
                    f"| {result.book_title[:30]} | {result.recommendations_found} | "
                    f"{result.critical_count} | {result.important_count} | "
                    f"{result.nice_to_have_count} | ${result.total_cost_usd:.4f} | "
                    f"{result.processing_time_seconds:.1f}s | {convergence} |"
                )

            report_lines.append("")

        # Cost Analysis
        report_lines.append("## Cost Analysis\n")

        for config_name, test_results in results.items():
            total_cost = sum(r.total_cost_usd for r in test_results)
            total_gemini = sum(r.gemini_cost_usd for r in test_results)
            total_claude = sum(r.claude_cost_usd for r in test_results)

            report_lines.append(f"### {config_name}")
            report_lines.append(f"- Total Cost: ${total_cost:.4f}")
            report_lines.append(
                f"- Gemini Cost: ${total_gemini:.4f} ({total_gemini/total_cost*100:.1f}%)"
            )
            report_lines.append(
                f"- Claude Cost: ${total_claude:.4f} ({total_claude/total_cost*100:.1f}%)"
            )
            report_lines.append("")

        # Recommendations
        report_lines.append("## Recommendations\n")

        # Find best configurations
        best_quality_config = max(
            results.items(),
            key=lambda x: sum(
                r.critical_count * 3 + r.important_count * 2 + r.nice_to_have_count
                for r in x[1]
            )
            / len(x[1]),
        )[0]

        best_cost_config = min(
            results.items(),
            key=lambda x: sum(r.total_cost_usd for r in x[1]) / len(x[1]),
        )[0]

        best_speed_config = min(
            results.items(),
            key=lambda x: sum(r.processing_time_seconds for r in x[1]) / len(x[1]),
        )[0]

        report_lines.append(f"- **Best Quality**: `{best_quality_config}`")
        report_lines.append(f"- **Lowest Cost**: `{best_cost_config}`")
        report_lines.append(f"- **Fastest**: `{best_speed_config}`")
        report_lines.append("")

        report = "\n".join(report_lines)

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"📝 Report saved: {output_path}")

        return report

    def save_results_json(
        self, results: Dict[str, List[TestResult]], output_path: Optional[Path] = None
    ):
        """
        Save raw results as JSON for further analysis.

        Args:
            results: Dictionary of test results
            output_path: Path to save JSON file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.results_dir / f"ab_test_{timestamp}.json"

        # Convert dataclasses to dicts
        json_results = {
            config_name: [asdict(result) for result in test_results]
            for config_name, test_results in results.items()
        }

        with open(output_path, "w") as f:
            json.dump(json_results, f, indent=2)

        logger.info(f"💾 Results saved: {output_path}")


async def main():
    """Main entry point for A/B testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="A/B Testing Framework for Model Combinations"
    )
    parser.add_argument(
        "--test",
        choices=["gemini-vs-claude", "consensus-comparison", "all"],
        default="gemini-vs-claude",
        help="Type of A/B test to run",
    )
    parser.add_argument(
        "--books", type=int, default=3, help="Number of books to test (default: 3)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for report (default: ab_testing_results/report_TIMESTAMP.md)",
    )

    args = parser.parse_args()

    # Initialize framework
    framework = ABTestingFramework()

    # Define test configurations based on test type
    if args.test == "gemini-vs-claude":
        config_names = ["gemini_only", "claude_only"]
    elif args.test == "consensus-comparison":
        config_names = [
            "gemini_only",
            "gemini_claude_consensus",
            "gemini_claude_high_consensus",
        ]
    else:  # 'all'
        config_names = list(framework.CONFIGS.keys())

    # Mock book data for testing
    # TODO: Replace with actual book discovery
    book_paths = [f"books/book_{i}.pdf" for i in range(args.books)]
    book_titles = [f"Test Book {i+1}" for i in range(args.books)]

    logger.info(
        f"======================================================================"
    )
    logger.info(f"A/B TESTING: {args.test}")
    logger.info(
        f"======================================================================"
    )
    logger.info(f"Configurations: {', '.join(config_names)}")
    logger.info(f"Books: {args.books}")
    logger.info(
        f"======================================================================"
    )

    # Run tests
    results = await framework.run_comparison_test(
        config_names=config_names, book_paths=book_paths, book_titles=book_titles
    )

    # Generate report
    if args.output:
        report_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = framework.results_dir / f"ab_test_report_{timestamp}.md"

    report = framework.generate_comparison_report(results, report_path)

    # Save JSON results
    json_path = report_path.with_suffix(".json")
    framework.save_results_json(results, json_path)

    logger.info(
        f"\n======================================================================"
    )
    logger.info(f"A/B Testing Complete!")
    logger.info(
        f"======================================================================"
    )
    logger.info(f"Report: {report_path}")
    logger.info(f"Data: {json_path}")
    logger.info(
        f"======================================================================"
    )


if __name__ == "__main__":
    asyncio.run(main())
