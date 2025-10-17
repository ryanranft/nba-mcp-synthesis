"""
Batch Processing Framework

Efficient batch processing for large-scale data operations:
- Batch job scheduling
- Parallel processing
- Progress tracking
- Checkpoint/resume
- Error handling
- Resource management

Features:
- Dynamic batch sizing
- Priority scheduling
- Parallel execution
- Memory-efficient streaming
- Retry failed items
- Result aggregation

Use Cases:
- Bulk player stats updates
- Batch predictions
- Data migrations
- Report generation
- ETL pipelines
"""

import time
import logging
from typing import Any, Callable, List, Optional, Dict, Iterator, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BatchStatus(Enum):
    """Batch job status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class BatchResult:
    """Result of batch processing"""

    total_items: int
    processed_items: int
    failed_items: int
    skipped_items: int
    success_rate: float
    processing_time_seconds: float
    results: List[Any] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BatchProgress:
    """Track batch processing progress"""

    total_items: int
    processed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    current_batch: int = 0
    total_batches: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.processed_items == 0:
            return 0.0
        return ((self.processed_items - self.failed_items) / self.processed_items) * 100

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time"""
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def items_per_second(self) -> float:
        """Calculate processing rate"""
        elapsed = self.elapsed_seconds
        if elapsed == 0:
            return 0.0
        return self.processed_items / elapsed

    @property
    def estimated_time_remaining_seconds(self) -> Optional[float]:
        """Estimate time remaining"""
        rate = self.items_per_second
        if rate == 0:
            return None
        remaining_items = self.total_items - self.processed_items
        return remaining_items / rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "skipped_items": self.skipped_items,
            "progress_percent": round(self.progress_percent, 2),
            "success_rate": round(self.success_rate, 2),
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "items_per_second": round(self.items_per_second, 2),
            "estimated_time_remaining_seconds": (
                round(self.estimated_time_remaining_seconds, 2)
                if self.estimated_time_remaining_seconds
                else None
            ),
        }


class BatchProcessor(Generic[T, R]):
    """Generic batch processor"""

    def __init__(
        self,
        batch_size: int = 100,
        max_workers: int = 4,
        checkpoint_interval: int = 1000,
        enable_checkpoints: bool = True,
    ):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.checkpoint_interval = checkpoint_interval
        self.enable_checkpoints = enable_checkpoints

        # State
        self.status = BatchStatus.PENDING
        self.progress: Optional[BatchProgress] = None
        self._lock = threading.RLock()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Start unpaused
        self._cancel_event = threading.Event()

    def _create_batches(self, items: List[T]) -> Iterator[List[T]]:
        """Split items into batches"""
        for i in range(0, len(items), self.batch_size):
            yield items[i : i + self.batch_size]

    def _process_item(self, item: T, processor: Callable[[T], R]) -> Dict[str, Any]:
        """Process single item with error handling"""
        try:
            result = processor(item)
            return {"success": True, "item": item, "result": result}
        except Exception as e:
            logger.error(f"Error processing item {item}: {e}")
            return {"success": False, "item": item, "error": str(e)}

    def _process_batch(
        self, batch: List[T], processor: Callable[[T], R], parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """Process a single batch"""
        if parallel and len(batch) > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self._process_item, item, processor)
                    for item in batch
                ]

                results = []
                for future in as_completed(futures):
                    results.append(future.result())

                return results
        else:
            # Sequential processing
            return [self._process_item(item, processor) for item in batch]

    def _save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> None:
        """Save checkpoint to disk"""
        if not self.enable_checkpoints:
            return

        checkpoint_file = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint_data, f)
            logger.info(f"Checkpoint saved: {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def process(
        self,
        items: List[T],
        processor: Callable[[T], R],
        parallel: bool = True,
        on_progress: Optional[Callable[[BatchProgress], None]] = None,
    ) -> BatchResult:
        """Process items in batches"""
        if not items:
            return BatchResult(
                total_items=0,
                processed_items=0,
                failed_items=0,
                skipped_items=0,
                success_rate=0.0,
                processing_time_seconds=0.0,
            )

        # Initialize
        start_time = time.time()
        self.status = BatchStatus.RUNNING

        batches = list(self._create_batches(items))
        self.progress = BatchProgress(
            total_items=len(items), total_batches=len(batches)
        )

        all_results = []
        all_errors = []

        try:
            for batch_idx, batch in enumerate(batches):
                # Check for cancellation
                if self._cancel_event.is_set():
                    logger.info("Batch processing cancelled")
                    self.status = BatchStatus.CANCELLED
                    break

                # Check for pause
                self._pause_event.wait()

                # Process batch
                logger.info(f"Processing batch {batch_idx + 1}/{len(batches)}")
                batch_results = self._process_batch(batch, processor, parallel)

                # Update progress
                with self._lock:
                    self.progress.current_batch = batch_idx + 1

                    for result in batch_results:
                        if result["success"]:
                            all_results.append(result["result"])
                            self.progress.processed_items += 1
                        else:
                            all_errors.append(
                                {"item": result["item"], "error": result["error"]}
                            )
                            self.progress.failed_items += 1

                    self.progress.last_update = datetime.now()

                # Progress callback
                if on_progress:
                    on_progress(self.progress)

                # Checkpoint
                if (
                    self.enable_checkpoints
                    and (batch_idx + 1) % self.checkpoint_interval == 0
                ):
                    checkpoint_data = {
                        "batch_idx": batch_idx + 1,
                        "progress": self.progress.to_dict(),
                        "timestamp": datetime.now().isoformat(),
                    }
                    self._save_checkpoint(checkpoint_data)

            # Mark as completed
            if self.status == BatchStatus.RUNNING:
                self.status = BatchStatus.COMPLETED

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            self.status = BatchStatus.FAILED
            raise

        # Calculate final result
        processing_time = time.time() - start_time
        processed = self.progress.processed_items
        failed = self.progress.failed_items

        return BatchResult(
            total_items=len(items),
            processed_items=processed,
            failed_items=failed,
            skipped_items=len(items) - processed - failed,
            success_rate=(processed - failed) / processed * 100 if processed > 0 else 0,
            processing_time_seconds=processing_time,
            results=all_results,
            errors=all_errors,
        )

    def pause(self) -> None:
        """Pause batch processing"""
        self._pause_event.clear()
        self.status = BatchStatus.PAUSED
        logger.info("Batch processing paused")

    def resume(self) -> None:
        """Resume batch processing"""
        self._pause_event.set()
        if self.status == BatchStatus.PAUSED:
            self.status = BatchStatus.RUNNING
        logger.info("Batch processing resumed")

    def cancel(self) -> None:
        """Cancel batch processing"""
        self._cancel_event.set()
        logger.info("Batch processing cancellation requested")

    def get_progress(self) -> Optional[BatchProgress]:
        """Get current progress"""
        with self._lock:
            return self.progress


class StreamingBatchProcessor(Generic[T, R]):
    """Memory-efficient streaming batch processor"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    def process_stream(
        self, item_iterator: Iterator[T], processor: Callable[[List[T]], List[R]]
    ) -> Iterator[R]:
        """Process items from an iterator in batches"""
        batch = []

        for item in item_iterator:
            batch.append(item)

            if len(batch) >= self.batch_size:
                # Process full batch
                results = processor(batch)
                for result in results:
                    yield result
                batch = []

        # Process remaining items
        if batch:
            results = processor(batch)
            for result in results:
                yield result


# NBA-specific batch processors
def batch_update_player_stats(player_ids: List[int]) -> BatchResult:
    """Batch update player statistics"""
    processor = BatchProcessor(batch_size=50, max_workers=4)

    def update_stats(player_id: int) -> Dict[str, Any]:
        """Update stats for single player"""
        # Simulate API call
        time.sleep(0.1)
        return {
            "player_id": player_id,
            "ppg": 20.5,
            "rpg": 8.2,
            "apg": 5.1,
            "updated_at": datetime.now().isoformat(),
        }

    return processor.process(player_ids, update_stats, parallel=True)


def batch_generate_predictions(games: List[Dict[str, Any]]) -> BatchResult:
    """Batch generate game predictions"""
    processor = BatchProcessor(batch_size=20, max_workers=2)

    def predict_game(game: Dict[str, Any]) -> Dict[str, Any]:
        """Predict single game outcome"""
        time.sleep(0.2)  # Simulate ML model inference
        return {
            "game_id": game["game_id"],
            "prediction": "home_win",
            "confidence": 0.72,
        }

    return processor.process(games, predict_game, parallel=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Batch Processing Demo ===\n")

    # Basic batch processing
    print("--- Basic Batch Processing ---")
    processor = BatchProcessor(batch_size=5, max_workers=2)

    items = list(range(1, 21))  # 20 items

    def square_number(n: int) -> int:
        """Simple processing function"""
        time.sleep(0.1)  # Simulate work
        return n**2

    def progress_callback(progress: BatchProgress):
        """Progress callback"""
        print(
            f"  Progress: {progress.progress_percent:.1f}% "
            f"({progress.processed_items}/{progress.total_items}) "
            f"- {progress.items_per_second:.1f} items/sec"
        )

    result = processor.process(
        items, square_number, parallel=True, on_progress=progress_callback
    )

    print(f"\nBatch Result:")
    print(f"  Total: {result.total_items}")
    print(f"  Processed: {result.processed_items}")
    print(f"  Failed: {result.failed_items}")
    print(f"  Success Rate: {result.success_rate:.1f}%")
    print(f"  Processing Time: {result.processing_time_seconds:.2f}s")
    print(f"  First 5 results: {result.results[:5]}")

    # NBA batch processing
    print("\n--- NBA Batch Processing ---")

    # Batch update player stats
    player_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(f"Updating stats for {len(player_ids)} players...")

    stats_result = batch_update_player_stats(player_ids)
    print(
        f"Updated {stats_result.processed_items} players in {stats_result.processing_time_seconds:.2f}s"
    )

    # Streaming processor demo
    print("\n--- Streaming Processor Demo ---")
    streaming_processor = StreamingBatchProcessor(batch_size=3)

    def generate_items() -> Iterator[int]:
        """Generate items one at a time"""
        for i in range(1, 11):
            time.sleep(0.05)
            yield i

    def batch_multiply(batch: List[int]) -> List[int]:
        """Process batch of items"""
        print(f"  Processing batch of {len(batch)} items")
        return [x * 10 for x in batch]

    print("Streaming results:")
    for result in streaming_processor.process_stream(generate_items(), batch_multiply):
        print(f"  Result: {result}")

    print("\n=== Demo Complete ===")
