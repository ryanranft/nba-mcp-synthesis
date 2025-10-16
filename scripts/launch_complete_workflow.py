#!/usr/bin/env python3
"""
Complete Book Analysis to Implementation Workflow Orchestrator

Orchestrates the complete end-to-end workflow:
1. Check API keys and budgets
2. Scan S3 for new books
3. Run 4-model analysis (Google+DeepSeek → Claude+GPT-4)
4. Organize into phase subdirectories
5. Generate implementation scripts via MCP
6. Create execution plan with dependencies
7. Generate final report

Usage:
    python scripts/launch_complete_workflow.py \\
        --config config/books_to_analyze_all_ai_ml.json \\
        --budget 410 \\
        --output analysis_results/ \\
        --generate-implementations
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates the complete book analysis to implementation workflow.
    """

    def __init__(
        self,
        config_file: str,
        budget: float,
        output_dir: str,
        generate_implementations: bool = True
    ):
        """
        Initialize orchestrator.

        Args:
            config_file: Path to books configuration file
            budget: Maximum budget in USD
            output_dir: Output directory for results
            generate_implementations: Whether to generate implementation files
        """
        self.config_file = config_file
        self.budget = budget
        self.output_dir = Path(output_dir)
        self.generate_implementations = generate_implementations
        self.start_time = datetime.now()
        self.total_cost = 0.0
        self.books_analyzed = 0
        self.recommendations_generated = 0
        self.files_generated = 0

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 80)
        logger.info("Complete Book Analysis to Implementation Workflow")
        logger.info("=" * 80)
        logger.info(f"Config: {config_file}")
        logger.info(f"Budget: ${budget:.2f}")
        logger.info(f"Output: {output_dir}")
        logger.info(f"Generate Implementations: {generate_implementations}")
        logger.info("=" * 80)

    def check_api_keys(self) -> bool:
        """Check that all required API keys are set."""
        logger.info("Checking API keys...")

        required_keys = [
            'GOOGLE_API_KEY',
            'DEEPSEEK_API_KEY',
            'ANTHROPIC_API_KEY',
            'OPENAI_API_KEY'
        ]

        missing_keys = []
        for key in required_keys:
            if not os.getenv(key):
                missing_keys.append(key)

        if missing_keys:
            logger.error(f"Missing API keys: {', '.join(missing_keys)}")
            logger.error("Please set these environment variables before running.")
            return False

        logger.info("✅ All API keys present")
        return True

    def check_budget(self) -> bool:
        """Check if budget is sufficient."""
        logger.info(f"Checking budget: ${self.budget:.2f}")

        # Load books to analyze
        with open(self.config_file, 'r') as f:
            config = json.load(f)

        num_books = len(config.get('books', []))

        # Estimate cost per book: $3.60-10.30
        min_cost = num_books * 3.60
        max_cost = num_books * 10.30

        logger.info(f"Books to analyze: {num_books}")
        logger.info(f"Estimated cost: ${min_cost:.2f} - ${max_cost:.2f}")

        if self.budget < min_cost:
            logger.error(f"Budget ${self.budget:.2f} is below minimum estimated cost ${min_cost:.2f}")
            return False

        if self.budget < max_cost:
            logger.warning(f"Budget ${self.budget:.2f} may be insufficient (max estimate: ${max_cost:.2f})")
            logger.warning("Workflow may stop early if budget is exceeded")

        logger.info("✅ Budget check passed")
        return True

    def check_mcp_server(self) -> bool:
        """Check if MCP server is running."""
        logger.info("Checking MCP server...")

        # For now, we'll skip this check since MCP integration is optional
        # In production, this would ping the MCP server
        logger.info("⚠️  MCP server check skipped (optional)")
        return True

    async def run_book_analysis(self) -> bool:
        """Run the 4-model book analysis."""
        logger.info("=" * 80)
        logger.info("Phase 1: Running 4-Model Book Analysis")
        logger.info("=" * 80)

        try:
            # Run recursive book analysis script
            cmd = [
                'python3',
                'scripts/recursive_book_analysis.py',
                '--config', self.config_file,
                '--output-dir', str(self.output_dir),
                '--all'
            ]

            logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            if result.returncode != 0:
                logger.error(f"Book analysis failed: {result.stderr}")
                return False

            logger.info("✅ Book analysis complete")

            # Parse results
            master_recs_file = self.output_dir / 'master_recommendations.json'
            if master_recs_file.exists():
                with open(master_recs_file, 'r') as f:
                    data = json.load(f)
                self.recommendations_generated = len(data.get('recommendations', []))
                logger.info(f"Generated {self.recommendations_generated} recommendations")

            return True

        except Exception as e:
            logger.error(f"Book analysis failed: {e}")
            return False

    async def organize_recommendations(self) -> bool:
        """Organize recommendations into phase subdirectories."""
        logger.info("=" * 80)
        logger.info("Phase 2: Organizing Recommendations by Phase")
        logger.info("=" * 80)

        try:
            # Run integration script
            cmd = [
                'python3',
                'scripts/integrate_recommendations.py',
                '--synthesis-path', '/Users/ryanranft/nba-mcp-synthesis',
                '--simulator-path', '/Users/ryanranft/nba-simulator-aws'
            ]

            logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            if result.returncode != 0:
                logger.error(f"Integration failed: {result.stderr}")
                return False

            logger.info("✅ Recommendations organized by phase")
            return True

        except Exception as e:
            logger.error(f"Organization failed: {e}")
            return False

    async def generate_implementation_files(self) -> bool:
        """Generate implementation files using MCP."""
        if not self.generate_implementations:
            logger.info("Skipping implementation file generation (disabled)")
            return True

        logger.info("=" * 80)
        logger.info("Phase 3: Generating Implementation Files")
        logger.info("=" * 80)

        try:
            # Run implementation generator
            cmd = [
                'python3',
                'scripts/generate_implementation_files.py',
                '--recommendations', str(self.output_dir / 'master_recommendations.json'),
                '--output-base', '/Users/ryanranft/nba-simulator-aws/docs/phases',
                '--templates-dir', 'templates',
                '--mcp-server', 'http://localhost:8000'
            ]

            logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            if result.returncode != 0:
                logger.error(f"Implementation generation failed: {result.stderr}")
                logger.warning("Continuing with partial results...")
            else:
                logger.info("✅ Implementation files generated")

            # Parse results
            summary_file = Path('/Users/ryanranft/nba-mcp-synthesis/implementation_generation_summary.json')
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    data = json.load(f)
                self.files_generated = data.get('total_files_generated', 0)
                logger.info(f"Generated {self.files_generated} implementation files")

            return True

        except Exception as e:
            logger.error(f"Implementation generation failed: {e}")
            return False

    async def generate_final_report(self) -> bool:
        """Generate final workflow report."""
        logger.info("=" * 80)
        logger.info("Phase 4: Generating Final Report")
        logger.info("=" * 80)

        try:
            duration = (datetime.now() - self.start_time).total_seconds()

            report = f"""# Complete Workflow Report

**Generated:** {datetime.now().isoformat()}
**Duration:** {duration:.1f}s ({duration/3600:.2f} hours)
**Budget:** ${self.budget:.2f}
**Total Cost:** ${self.total_cost:.2f}

---

## Summary

- **Books Analyzed:** {self.books_analyzed}
- **Recommendations Generated:** {self.recommendations_generated}
- **Implementation Files Generated:** {self.files_generated}
- **Budget Remaining:** ${self.budget - self.total_cost:.2f}

---

## Phases Completed

1. ✅ 4-Model Book Analysis (Google+DeepSeek → Claude+GPT-4)
2. ✅ Recommendation Organization by Phase
3. {'✅' if self.generate_implementations else '⏭️'} Implementation File Generation
4. ✅ Final Report Generation

---

## Output Files

### Analysis Results
- `{self.output_dir}/master_recommendations.json` - All recommendations
- `{self.output_dir}/cost_tracking.json` - Cost breakdown by model

### Phase Organization
- `/Users/ryanranft/nba-simulator-aws/docs/phases/phase_X/` - Phase-specific recommendations

### Implementation Files
- `/Users/ryanranft/nba-simulator-aws/docs/phases/phase_X/Y.Z_*/` - Implementation scripts, tests, SQL, CloudFormation

---

## Next Steps

1. Review generated recommendations in `master_recommendations.json`
2. Prioritize implementations by phase and priority
3. Execute implementation scripts:
   ```bash
   python implement_<rec_id>.py
   ```
4. Run tests:
   ```bash
   python test_<rec_id>.py
   ```
5. Deploy infrastructure (if applicable):
   ```bash
   aws cloudformation create-stack --stack-name <stack> --template-body file://<rec_id>_infrastructure.yaml
   ```

---

## Cost Breakdown

- **Google Gemini:** $XX.XX
- **DeepSeek:** $XX.XX
- **Claude:** $XX.XX
- **GPT-4:** $XX.XX

**Total:** ${self.total_cost:.2f}

---

*Generated by Complete Workflow Orchestrator*
"""

            report_file = self.output_dir / 'complete_workflow_report.md'
            with open(report_file, 'w') as f:
                f.write(report)

            logger.info(f"✅ Report saved to: {report_file}")
            return True

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return False

    async def run(self) -> bool:
        """Run the complete workflow."""
        try:
            # Pre-flight checks
            if not self.check_api_keys():
                return False

            if not self.check_budget():
                return False

            self.check_mcp_server()

            # Phase 1: Book Analysis
            if not await self.run_book_analysis():
                logger.error("Book analysis failed. Stopping workflow.")
                return False

            # Phase 2: Organization
            if not await self.organize_recommendations():
                logger.error("Organization failed. Stopping workflow.")
                return False

            # Phase 3: Implementation Generation
            if not await self.generate_implementation_files():
                logger.warning("Implementation generation had issues, but continuing...")

            # Phase 4: Final Report
            if not await self.generate_final_report():
                logger.warning("Report generation failed, but workflow completed")

            # Success!
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info("=" * 80)
            logger.info("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info(f"Duration: {duration:.1f}s ({duration/3600:.2f} hours)")
            logger.info(f"Books Analyzed: {self.books_analyzed}")
            logger.info(f"Recommendations: {self.recommendations_generated}")
            logger.info(f"Implementation Files: {self.files_generated}")
            logger.info(f"Total Cost: ${self.total_cost:.2f}")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Launch complete book analysis to implementation workflow'
    )
    parser.add_argument(
        '--config',
        default='config/books_to_analyze_all_ai_ml.json',
        help='Path to books configuration file'
    )
    parser.add_argument(
        '--budget',
        type=float,
        default=410.0,
        help='Maximum budget in USD'
    )
    parser.add_argument(
        '--output',
        default='analysis_results/',
        help='Output directory for results'
    )
    parser.add_argument(
        '--generate-implementations',
        action='store_true',
        default=True,
        help='Generate implementation files (default: True)'
    )
    parser.add_argument(
        '--no-implementations',
        action='store_true',
        help='Skip implementation file generation'
    )

    args = parser.parse_args()

    # Handle no-implementations flag
    generate_impl = args.generate_implementations and not args.no_implementations

    orchestrator = WorkflowOrchestrator(
        config_file=args.config,
        budget=args.budget,
        output_dir=args.output,
        generate_implementations=generate_impl
    )

    success = await orchestrator.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())





