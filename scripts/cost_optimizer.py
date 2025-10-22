#!/usr/bin/env python3
"""
Cost Optimizer for NBA MCP Synthesis

This module optimizes AI model selection to minimize costs while maintaining quality:
1. Analyze book complexity (pages, technical density, structure)
2. Select optimal model tier (GPT-4o, GPT-4o-mini, GPT-3.5)
3. Track costs per book and cumulative
4. Enforce budget limits and alerts
5. Provide cost estimates before analysis
6. Generate cost reports and optimization recommendations

Features:
- Automatic complexity assessment
- Smart model selection
- Cost tracking and budgeting
- Detailed cost reports
- ROI analysis

Author: NBA MCP Synthesis Team
Date: 2025-10-22
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict
import PyPDF2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Model pricing (per 1M tokens)
MODEL_PRICING = {
    'gpt-4o': {
        'input': 2.50,   # $2.50 per 1M input tokens
        'output': 10.00, # $10.00 per 1M output tokens
        'description': 'Most capable, highest quality, expensive'
    },
    'gpt-4o-mini': {
        'input': 0.150,  # $0.15 per 1M input tokens
        'output': 0.600, # $0.60 per 1M output tokens
        'description': 'Fast, capable, cost-effective'
    },
    'gpt-3.5-turbo': {
        'input': 0.50,   # $0.50 per 1M input tokens
        'output': 1.50,  # $1.50 per 1M output tokens
        'description': 'Legacy, cheap, less capable'
    },
}


@dataclass
class BookComplexity:
    """Represents complexity assessment of a book"""
    book_name: str
    page_count: int
    estimated_tokens: int
    technical_density: str  # 'low', 'medium', 'high', 'very_high'
    has_code: bool
    has_math: bool
    has_diagrams: bool
    complexity_score: float  # 0.0 to 1.0

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CostEstimate:
    """Represents cost estimate for analyzing a book"""
    book_name: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float
    breakdown: Dict[str, float]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ActualCost:
    """Represents actual cost incurred"""
    book_name: str
    model: str
    input_tokens: int
    output_tokens: int
    total_cost: float
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)


class CostOptimizer:
    """Optimizes model selection and tracks costs"""

    # Complexity thresholds for model selection
    COMPLEXITY_THRESHOLDS = {
        'gpt-3.5-turbo': 0.3,    # Use for very simple books
        'gpt-4o-mini': 0.6,      # Use for simple to medium complexity
        'gpt-4o': 1.0,           # Use for high complexity
    }

    # Token estimation (pages to tokens)
    TOKENS_PER_PAGE = 500  # Conservative estimate

    # Output multiplier (output tokens vs input)
    OUTPUT_MULTIPLIER = {
        'analysis': 0.5,         # Analysis produces ~50% of input size
        'recommendations': 0.8,  # Recommendations ~80% of input
    }

    def __init__(
        self,
        cost_log_file: str = 'costs.json',
        budget_limit: Optional[float] = None
    ):
        """
        Initialize cost optimizer

        Args:
            cost_log_file: Path to cost log file
            budget_limit: Maximum budget in dollars (None = unlimited)
        """
        self.cost_log_file = Path(cost_log_file)
        self.budget_limit = budget_limit
        self.cost_history: List[ActualCost] = []
        self.load_cost_history()

        logger.info("💰 CostOptimizer initialized")
        logger.info(f"   Cost log: {self.cost_log_file}")
        if budget_limit:
            logger.info(f"   Budget limit: ${budget_limit:.2f}")

    def load_cost_history(self):
        """Load cost history from file"""
        if not self.cost_log_file.exists():
            logger.info("   No cost history found (first run)")
            return

        try:
            with open(self.cost_log_file, 'r') as f:
                data = json.load(f)

            self.cost_history = [
                ActualCost(**entry) for entry in data.get('cost_history', [])
            ]

            logger.info(f"✅ Loaded {len(self.cost_history)} cost entries")

        except Exception as e:
            logger.error(f"❌ Error loading cost history: {e}")

    def save_cost_history(self):
        """Save cost history to file"""
        try:
            data = {
                'cost_history': [cost.to_dict() for cost in self.cost_history],
                'total_cost': sum(c.total_cost for c in self.cost_history),
                'last_updated': datetime.now().isoformat(),
            }

            with open(self.cost_log_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"💾 Saved cost history")

        except Exception as e:
            logger.error(f"❌ Error saving cost history: {e}")

    def assess_book_complexity(self, book_path: str) -> BookComplexity:
        """
        Assess complexity of a book

        Args:
            book_path: Path to PDF file

        Returns:
            BookComplexity assessment
        """
        book_path = Path(book_path)
        book_name = book_path.stem

        logger.info(f"📊 Assessing complexity: {book_name}")

        try:
            with open(book_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                page_count = len(pdf.pages)

                # Sample first few pages for content analysis
                sample_text = ""
                for i in range(min(5, page_count)):
                    try:
                        sample_text += pdf.pages[i].extract_text()
                    except:
                        pass

        except Exception as e:
            logger.warning(f"⚠️  Error reading PDF: {e}")
            # Default to high complexity (use expensive model to be safe)
            return BookComplexity(
                book_name=book_name,
                page_count=200,  # Assume medium size
                estimated_tokens=100000,
                technical_density='high',
                has_code=True,
                has_math=True,
                has_diagrams=True,
                complexity_score=0.9
            )

        # Analyze content
        has_code = any(keyword in sample_text.lower() for keyword in [
            'def ', 'class ', 'import ', 'function', 'algorithm', 'code'
        ])

        has_math = any(keyword in sample_text.lower() for keyword in [
            'theorem', 'proof', 'equation', 'matrix', 'derivative', 'integral'
        ])

        has_diagrams = 'figure' in sample_text.lower() or 'diagram' in sample_text.lower()

        # Technical density based on vocabulary
        technical_keywords = [
            'neural', 'machine learning', 'algorithm', 'optimization',
            'statistical', 'model', 'framework', 'architecture'
        ]
        tech_keyword_count = sum(1 for kw in technical_keywords if kw in sample_text.lower())
        technical_density = 'very_high' if tech_keyword_count >= 5 else \
                           'high' if tech_keyword_count >= 3 else \
                           'medium' if tech_keyword_count >= 1 else 'low'

        # Complexity score (0.0 to 1.0)
        complexity_score = 0.0
        complexity_score += page_count / 1000  # Longer books = more complex
        complexity_score += 0.2 if has_code else 0
        complexity_score += 0.2 if has_math else 0
        complexity_score += 0.1 if has_diagrams else 0
        complexity_score += {'low': 0.1, 'medium': 0.2, 'high': 0.3, 'very_high': 0.4}[technical_density]

        complexity_score = min(1.0, complexity_score)  # Cap at 1.0

        # Estimate tokens
        estimated_tokens = page_count * self.TOKENS_PER_PAGE

        complexity = BookComplexity(
            book_name=book_name,
            page_count=page_count,
            estimated_tokens=estimated_tokens,
            technical_density=technical_density,
            has_code=has_code,
            has_math=has_math,
            has_diagrams=has_diagrams,
            complexity_score=complexity_score
        )

        logger.info(f"   Pages: {page_count}")
        logger.info(f"   Tokens: ~{estimated_tokens:,}")
        logger.info(f"   Technical density: {technical_density}")
        logger.info(f"   Complexity score: {complexity_score:.2f}")

        return complexity

    def select_optimal_model(self, complexity: BookComplexity) -> str:
        """
        Select optimal model based on complexity

        Args:
            complexity: BookComplexity assessment

        Returns:
            Model name (e.g., 'gpt-4o-mini')
        """
        score = complexity.complexity_score

        # Select model based on thresholds
        if score <= self.COMPLEXITY_THRESHOLDS['gpt-3.5-turbo']:
            model = 'gpt-3.5-turbo'
        elif score <= self.COMPLEXITY_THRESHOLDS['gpt-4o-mini']:
            model = 'gpt-4o-mini'
        else:
            model = 'gpt-4o'

        logger.info(f"✅ Selected model: {model}")
        logger.info(f"   Reason: Complexity {score:.2f} → {MODEL_PRICING[model]['description']}")

        return model

    def estimate_cost(
        self,
        complexity: BookComplexity,
        model: str,
        task: str = 'recommendations'
    ) -> CostEstimate:
        """
        Estimate cost for analyzing a book

        Args:
            complexity: BookComplexity assessment
            model: Model to use
            task: Task type ('analysis' or 'recommendations')

        Returns:
            CostEstimate
        """
        # Input tokens
        input_tokens = complexity.estimated_tokens

        # Output tokens (depends on task)
        output_multiplier = self.OUTPUT_MULTIPLIER.get(task, 0.5)
        output_tokens = int(input_tokens * output_multiplier)

        # Cost calculation
        pricing = MODEL_PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        total_cost = input_cost + output_cost

        estimate = CostEstimate(
            book_name=complexity.book_name,
            model=model,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            estimated_cost=total_cost,
            breakdown={
                'input_cost': input_cost,
                'output_cost': output_cost,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
            }
        )

        logger.info(f"💰 Cost estimate for {complexity.book_name}:")
        logger.info(f"   Model: {model}")
        logger.info(f"   Input tokens: ~{input_tokens:,}")
        logger.info(f"   Output tokens: ~{output_tokens:,}")
        logger.info(f"   Estimated cost: ${total_cost:.4f}")

        return estimate

    def check_budget(self, estimated_cost: float) -> Tuple[bool, float]:
        """
        Check if estimated cost is within budget

        Args:
            estimated_cost: Estimated cost for next analysis

        Returns:
            Tuple of (within_budget, remaining_budget)
        """
        if self.budget_limit is None:
            return True, float('inf')

        total_spent = sum(c.total_cost for c in self.cost_history)
        remaining = self.budget_limit - total_spent

        within_budget = estimated_cost <= remaining

        if not within_budget:
            logger.warning(f"⚠️  Budget exceeded!")
            logger.warning(f"   Spent: ${total_spent:.4f}")
            logger.warning(f"   Remaining: ${remaining:.4f}")
            logger.warning(f"   Estimated cost: ${estimated_cost:.4f}")
            logger.warning(f"   Over by: ${estimated_cost - remaining:.4f}")

        return within_budget, remaining

    def log_actual_cost(
        self,
        book_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> ActualCost:
        """
        Log actual cost incurred

        Args:
            book_name: Name of book analyzed
            model: Model used
            input_tokens: Actual input tokens
            output_tokens: Actual output tokens

        Returns:
            ActualCost entry
        """
        pricing = MODEL_PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        total_cost = input_cost + output_cost

        cost_entry = ActualCost(
            book_name=book_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=total_cost,
            timestamp=datetime.now().isoformat()
        )

        self.cost_history.append(cost_entry)
        self.save_cost_history()

        logger.info(f"💾 Logged cost for {book_name}: ${total_cost:.4f}")

        return cost_entry

    def get_statistics(self) -> Dict[str, Any]:
        """Get cost statistics"""
        if not self.cost_history:
            return {
                'total_cost': 0,
                'total_books': 0,
                'avg_cost_per_book': 0,
                'by_model': {},
            }

        total_cost = sum(c.total_cost for c in self.cost_history)
        total_books = len(self.cost_history)

        by_model = defaultdict(lambda: {'count': 0, 'cost': 0.0})
        for cost in self.cost_history:
            by_model[cost.model]['count'] += 1
            by_model[cost.model]['cost'] += cost.total_cost

        return {
            'total_cost': total_cost,
            'total_books': total_books,
            'avg_cost_per_book': total_cost / total_books if total_books > 0 else 0,
            'by_model': dict(by_model),
            'budget_remaining': self.budget_limit - total_cost if self.budget_limit else None,
        }

    def generate_cost_report(self, output_file: str):
        """Generate cost report"""
        logger.info(f"📄 Generating cost report: {output_file}")

        stats = self.get_statistics()

        lines = [
            '# Cost Analysis Report',
            '',
            f'**Generated**: {datetime.now().isoformat()}',
            f'**Total Books Analyzed**: {stats["total_books"]}',
            f'**Total Cost**: ${stats["total_cost"]:.4f}',
            f'**Average Cost per Book**: ${stats["avg_cost_per_book"]:.4f}',
            '',
        ]

        if self.budget_limit:
            lines.extend([
                f'**Budget Limit**: ${self.budget_limit:.2f}',
                f'**Budget Remaining**: ${stats["budget_remaining"]:.2f}',
                f'**Budget Used**: {(stats["total_cost"] / self.budget_limit * 100):.1f}%',
                '',
            ])

        lines.extend([
            '---',
            '',
            '## Cost by Model',
            '',
            '| Model | Books | Total Cost | Avg Cost | % of Total |',
            '|-------|-------|------------|----------|------------|',
        ])

        for model, data in stats['by_model'].items():
            pct = (data['cost'] / stats['total_cost'] * 100) if stats['total_cost'] > 0 else 0
            avg = data['cost'] / data['count'] if data['count'] > 0 else 0
            lines.append(
                f'| {model} | {data["count"]} | ${data["cost"]:.4f} | '
                f'${avg:.4f} | {pct:.1f}% |'
            )

        lines.extend([
            '',
            '## Recent Analyses',
            '',
            '| Book | Model | Cost | Date |',
            '|------|-------|------|------|',
        ])

        for cost in sorted(self.cost_history, key=lambda c: c.timestamp, reverse=True)[:20]:
            date = cost.timestamp[:10]
            lines.append(f'| {cost.book_name[:40]} | {cost.model} | ${cost.total_cost:.4f} | {date} |')

        Path(output_file).write_text('\n'.join(lines))
        logger.info(f"✅ Cost report generated")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Optimize model selection and track costs'
    )
    parser.add_argument(
        '--assess',
        help='Assess complexity of a book'
    )
    parser.add_argument(
        '--estimate',
        help='Estimate cost for a book'
    )
    parser.add_argument(
        '--model',
        help='Model to use for estimation (default: auto-select)'
    )
    parser.add_argument(
        '--budget',
        type=float,
        help='Set budget limit in dollars'
    )
    parser.add_argument(
        '--report',
        help='Generate cost report (markdown)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show cost statistics'
    )
    parser.add_argument(
        '--cost-log',
        default='costs.json',
        help='Path to cost log file'
    )

    args = parser.parse_args()

    # Initialize optimizer
    optimizer = CostOptimizer(
        cost_log_file=args.cost_log,
        budget_limit=args.budget
    )

    # Handle commands
    if args.stats:
        stats = optimizer.get_statistics()
        logger.info("")
        logger.info("📊 Cost Statistics:")
        logger.info(f"   Total cost: ${stats['total_cost']:.4f}")
        logger.info(f"   Total books: {stats['total_books']}")
        logger.info(f"   Avg cost/book: ${stats['avg_cost_per_book']:.4f}")
        if args.budget:
            logger.info(f"   Budget remaining: ${stats['budget_remaining']:.2f}")
        logger.info("")
        logger.info("   By model:")
        for model, data in stats['by_model'].items():
            logger.info(f"     {model}: {data['count']} books, ${data['cost']:.4f}")
        return 0

    if args.assess:
        complexity = optimizer.assess_book_complexity(args.assess)
        model = optimizer.select_optimal_model(complexity)
        logger.info(f"\n📋 Recommended model: {model}")
        return 0

    if args.estimate:
        complexity = optimizer.assess_book_complexity(args.estimate)
        model = args.model or optimizer.select_optimal_model(complexity)
        estimate = optimizer.estimate_cost(complexity, model)
        within_budget, remaining = optimizer.check_budget(estimate.estimated_cost)
        if not within_budget:
            logger.error("❌ Estimated cost exceeds budget!")
        return 0

    if args.report:
        optimizer.generate_cost_report(args.report)
        return 0

    logger.info("ℹ️  Use --help for usage information")
    return 0


if __name__ == '__main__':
    exit(main())
