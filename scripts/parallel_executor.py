#!/usr/bin/env python3
"""
Parallel Execution Manager for Tier 1

Executes independent operations in parallel to improve performance.

Performance Gains:
- Phase 2: 4-8 books analyzed simultaneously
- Phase 3: Batch recommendations in parallel
- Phase 4: Generate multiple files simultaneously

Expected Speedup:
- Total time: 8 hours → 2-3 hours (60-75% reduction)
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """
    Execute independent operations in parallel.

    Uses asyncio for I/O-bound operations (API calls)
    Uses ProcessPoolExecutor for CPU-bound operations
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize parallel executor.

        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
        logger.info(f"🔀 Parallel Executor initialized: {max_workers} workers")

    async def parallel_book_analysis(
        self, books: List[Dict], analyzer_func: Callable, batch_size: int = None
    ) -> List[Dict]:
        """
        Analyze multiple books in parallel.

        Args:
            books: List of book dictionaries
            analyzer_func: Async function to analyze a single book
            batch_size: Books per batch (defaults to max_workers)

        Returns:
            List of analysis results
        """
        if batch_size is None:
            batch_size = self.max_workers

        logger.info(
            f"📚 Analyzing {len(books)} books in parallel ({batch_size} per batch)"
        )
        start_time = time.time()

        # Split into batches
        batches = [books[i : i + batch_size] for i in range(0, len(books), batch_size)]

        all_results = []
        total_batches = len(batches)

        for batch_num, batch in enumerate(batches, 1):
            batch_start = time.time()
            logger.info(f"\n📦 Batch {batch_num}/{total_batches}: {len(batch)} books")

            # Run batch in parallel
            tasks = [analyzer_func(book) for book in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            successful = []
            failed = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"   ❌ Failed: {batch[i].get('title', 'Unknown')} - {result}"
                    )
                    failed.append(batch[i])
                else:
                    successful.append(result)

            all_results.extend(successful)

            batch_elapsed = time.time() - batch_start
            logger.info(
                f"   ✅ Batch {batch_num} complete: {len(successful)}/{len(batch)} successful ({batch_elapsed:.1f}s)"
            )

            if failed:
                logger.warning(f"   ⚠️  {len(failed)} books failed in this batch")

        total_elapsed = time.time() - start_time
        logger.info(f"\n✅ Parallel analysis complete:")
        logger.info(f"   Total books: {len(books)}")
        logger.info(f"   Successful: {len(all_results)}")
        logger.info(f"   Total time: {total_elapsed:.1f}s")
        logger.info(f"   Avg time per book: {total_elapsed/len(books):.1f}s")

        return all_results

    async def parallel_synthesis(
        self,
        recommendations: List[Dict],
        synthesizer_func: Callable,
        batch_size: int = None,
    ) -> List[Dict]:
        """
        Synthesize multiple recommendations in parallel.

        Args:
            recommendations: List of recommendation dictionaries
            synthesizer_func: Async function to synthesize a single recommendation
            batch_size: Recommendations per batch (defaults to max_workers * 2)

        Returns:
            List of synthesis results
        """
        if batch_size is None:
            batch_size = self.max_workers * 2  # Synthesis is lighter than analysis

        logger.info(
            f"🔨 Synthesizing {len(recommendations)} recommendations in parallel"
        )
        logger.info(f"   Batch size: {batch_size}")
        start_time = time.time()

        # Group by similarity to improve cache hits
        grouped = self._group_similar_recommendations(recommendations, batch_size)

        all_plans = []
        total_groups = len(grouped)

        for group_num, group in enumerate(grouped, 1):
            group_start = time.time()
            logger.info(
                f"\n📦 Group {group_num}/{total_groups}: {len(group)} recommendations"
            )

            # Process group in parallel
            tasks = [synthesizer_func(rec) for rec in group]
            plans = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            successful = []
            failed = []
            for i, plan in enumerate(plans):
                if isinstance(plan, Exception):
                    logger.error(
                        f"   ❌ Failed: {group[i].get('title', 'Unknown')} - {plan}"
                    )
                    failed.append(group[i])
                else:
                    successful.append(plan)

            all_plans.extend(successful)

            group_elapsed = time.time() - group_start
            logger.info(
                f"   ✅ Group {group_num} complete: {len(successful)}/{len(group)} successful ({group_elapsed:.1f}s)"
            )

            if failed:
                logger.warning(
                    f"   ⚠️  {len(failed)} recommendations failed in this group"
                )

        total_elapsed = time.time() - start_time
        logger.info(f"\n✅ Parallel synthesis complete:")
        logger.info(f"   Total recommendations: {len(recommendations)}")
        logger.info(f"   Successful: {len(all_plans)}")
        logger.info(f"   Total time: {total_elapsed:.1f}s")
        logger.info(f"   Avg time per rec: {total_elapsed/len(recommendations):.1f}s")

        return all_plans

    def _group_similar_recommendations(
        self, recommendations: List[Dict], batch_size: int
    ) -> List[List[Dict]]:
        """
        Group similar recommendations to improve cache hits.

        Groups by category first, then batches within each category.
        """
        # Group by category
        by_category = {}
        for rec in recommendations:
            category = rec.get("category", "uncategorized")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(rec)

        # Create batches within each category
        groups = []
        for category, recs in by_category.items():
            # Split into batches
            for i in range(0, len(recs), batch_size):
                groups.append(recs[i : i + batch_size])

        logger.info(f"   Grouped into {len(groups)} groups by similarity")
        return groups

    async def parallel_file_generation(
        self, plans: List[Dict], generator_func: Callable, batch_size: int = None
    ) -> List[Dict]:
        """
        Generate files for multiple plans in parallel.

        Args:
            plans: List of implementation plans
            generator_func: Async function to generate files for a single plan
            batch_size: Plans per batch (defaults to max_workers * 3)

        Returns:
            List of generation results
        """
        if batch_size is None:
            batch_size = self.max_workers * 3  # File generation is I/O bound

        logger.info(f"📝 Generating files for {len(plans)} plans in parallel")
        logger.info(f"   Batch size: {batch_size}")
        start_time = time.time()

        # Split into batches
        batches = [plans[i : i + batch_size] for i in range(0, len(plans), batch_size)]

        all_results = []
        total_batches = len(batches)

        for batch_num, batch in enumerate(batches, 1):
            batch_start = time.time()
            logger.info(f"\n📦 Batch {batch_num}/{total_batches}: {len(batch)} plans")

            # Run batch in parallel
            tasks = [generator_func(plan) for plan in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            successful = []
            failed = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"   ❌ Failed: {batch[i].get('title', 'Unknown')} - {result}"
                    )
                    failed.append(batch[i])
                else:
                    successful.append(result)

            all_results.extend(successful)

            batch_elapsed = time.time() - batch_start
            logger.info(
                f"   ✅ Batch {batch_num} complete: {len(successful)}/{len(batch)} successful ({batch_elapsed:.1f}s)"
            )

            if failed:
                logger.warning(f"   ⚠️  {len(failed)} plans failed in this batch")

        total_elapsed = time.time() - start_time
        logger.info(f"\n✅ Parallel file generation complete:")
        logger.info(f"   Total plans: {len(plans)}")
        logger.info(f"   Successful: {len(all_results)}")
        logger.info(f"   Total time: {total_elapsed:.1f}s")
        logger.info(f"   Avg time per plan: {total_elapsed/len(plans):.1f}s")

        return all_results

    def calculate_speedup(
        self, sequential_time: float, parallel_time: float
    ) -> Dict[str, Any]:
        """
        Calculate speedup metrics.

        Args:
            sequential_time: Time for sequential execution
            parallel_time: Time for parallel execution

        Returns:
            Dictionary with speedup metrics
        """
        speedup = sequential_time / parallel_time
        efficiency = speedup / self.max_workers
        time_saved = sequential_time - parallel_time
        percent_reduction = (time_saved / sequential_time) * 100

        return {
            "sequential_time": sequential_time,
            "parallel_time": parallel_time,
            "speedup": speedup,
            "efficiency": efficiency,
            "time_saved": time_saved,
            "percent_reduction": percent_reduction,
        }


# Usage examples
if __name__ == "__main__":
    import asyncio

    async def example_book_analyzer(book: Dict) -> Dict:
        """Example book analyzer function."""
        await asyncio.sleep(2)  # Simulate 2s per book
        return {"book": book, "result": "analyzed"}

    async def test_parallel_execution():
        """Test parallel execution."""
        executor = ParallelExecutor(max_workers=4)

        # Test with 8 books
        books = [{"title": f"Book {i}"} for i in range(8)]

        # Sequential
        start = time.time()
        for book in books:
            await example_book_analyzer(book)
        sequential_time = time.time() - start

        # Parallel
        start = time.time()
        results = await executor.parallel_book_analysis(
            books, example_book_analyzer, batch_size=4
        )
        parallel_time = time.time() - start

        # Calculate speedup
        metrics = executor.calculate_speedup(sequential_time, parallel_time)

        print(f"\n📊 Performance Comparison:")
        print(f"   Sequential: {metrics['sequential_time']:.1f}s")
        print(f"   Parallel: {metrics['parallel_time']:.1f}s")
        print(f"   Speedup: {metrics['speedup']:.2f}x")
        print(f"   Efficiency: {metrics['efficiency']:.1%}")
        print(
            f"   Time saved: {metrics['time_saved']:.1f}s ({metrics['percent_reduction']:.1f}%)"
        )

    asyncio.run(test_parallel_execution())
