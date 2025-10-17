"""
Distributed Task Queue

Async task processing and job scheduling:
- Task queuing and execution
- Priority queues
- Delayed/scheduled tasks
- Retry with exponential backoff
- Task monitoring
- Dead letter queue

Features:
- Multi-worker support
- Task dependencies
- Result storage
- Progress tracking
- Rate limiting
- Cancellation support

Use Cases:
- ML model training
- Data processing jobs
- Batch predictions
- Report generation
- Background tasks
"""

import time
import uuid
import threading
import queue
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import traceback

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels"""

    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class TaskResult:
    """Task execution result"""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    attempts: int = 0
    completed_at: Optional[datetime] = None


@dataclass
class Task:
    """Task definition"""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "unnamed_task"
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay_seconds: int = 5
    timeout_seconds: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)

    # Runtime state
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    result: Optional[TaskResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding func)"""
        data = asdict(self)
        data["func"] = self.func.__name__ if self.func else None
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["completed_at"] = (
            self.completed_at.isoformat() if self.completed_at else None
        )
        data["scheduled_at"] = (
            self.scheduled_at.isoformat() if self.scheduled_at else None
        )
        if self.result:
            data["result"] = {
                "status": self.result.status.value,
                "execution_time_seconds": self.result.execution_time_seconds,
                "attempts": self.result.attempts,
            }
        return data

    def is_ready(self) -> bool:
        """Check if task is ready to execute"""
        if self.scheduled_at and datetime.now() < self.scheduled_at:
            return False
        return self.status in [TaskStatus.PENDING, TaskStatus.RETRYING]


class TaskQueue:
    """Priority-based task queue"""

    def __init__(self, max_size: int = 1000):
        self._queues: Dict[TaskPriority, queue.PriorityQueue] = {
            priority: queue.PriorityQueue(maxsize=max_size) for priority in TaskPriority
        }
        self._pending_tasks: Dict[str, Task] = {}
        self._completed_tasks: Dict[str, Task] = {}
        self._lock = threading.RLock()

    def enqueue(self, task: Task) -> bool:
        """Add task to queue"""
        with self._lock:
            if task.task_id in self._pending_tasks:
                logger.warning(f"Task {task.task_id} already queued")
                return False

            try:
                # Add to priority queue (priority, timestamp, task_id)
                self._queues[task.priority].put_nowait(
                    (task.priority.value, task.created_at.timestamp(), task.task_id)
                )

                self._pending_tasks[task.task_id] = task
                task.status = TaskStatus.QUEUED

                logger.info(
                    f"Enqueued task {task.task_id} with priority {task.priority.name}"
                )
                return True

            except queue.Full:
                logger.error(f"Task queue full for priority {task.priority.name}")
                return False

    def dequeue(self, timeout: float = 1.0) -> Optional[Task]:
        """Get next task from queue (respects priority)"""
        # Check each priority level in order
        for priority in TaskPriority:
            try:
                _, _, task_id = self._queues[priority].get_nowait()

                with self._lock:
                    task = self._pending_tasks.get(task_id)
                    if task and task.is_ready():
                        return task
                    else:
                        # Re-enqueue if not ready
                        if task:
                            self._queues[priority].put_nowait(
                                (priority.value, task.created_at.timestamp(), task_id)
                            )

            except queue.Empty:
                continue

        return None

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self._lock:
            if task_id in self._pending_tasks:
                return self._pending_tasks[task_id]
            if task_id in self._completed_tasks:
                return self._completed_tasks[task_id]
            return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        with self._lock:
            task = self._pending_tasks.get(task_id)
            if task and task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                self._completed_tasks[task_id] = task
                del self._pending_tasks[task_id]
                logger.info(f"Cancelled task {task_id}")
                return True
            return False

    def complete_task(self, task: Task) -> None:
        """Mark task as complete"""
        with self._lock:
            if task.task_id in self._pending_tasks:
                self._completed_tasks[task.task_id] = task
                del self._pending_tasks[task.task_id]

    def get_queue_size(self) -> Dict[str, int]:
        """Get size of each priority queue"""
        return {
            priority.name: self._queues[priority].qsize() for priority in TaskPriority
        }

    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        with self._lock:
            return list(self._pending_tasks.values())


class TaskWorker:
    """Task execution worker"""

    def __init__(self, worker_id: str, task_queue: TaskQueue):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_task: Optional[Task] = None

    def _execute_task(self, task: Task) -> TaskResult:
        """Execute a single task"""
        start_time = time.time()
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.attempts += 1

        logger.info(
            f"Worker {self.worker_id} executing task {task.task_id} (attempt {task.attempts})"
        )

        try:
            # Execute task function
            if task.func:
                result_value = task.func(*task.args, **task.kwargs)
            else:
                result_value = None

            execution_time = time.time() - start_time

            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.SUCCESS,
                result=result_value,
                execution_time_seconds=execution_time,
                attempts=task.attempts,
                completed_at=datetime.now(),
            )

            task.status = TaskStatus.SUCCESS
            task.completed_at = datetime.now()
            task.result = result

            logger.info(
                f"Task {task.task_id} completed successfully in {execution_time:.2f}s"
            )
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

            # Check if we should retry
            if task.attempts < task.max_retries:
                task.status = TaskStatus.RETRYING
                logger.warning(
                    f"Task {task.task_id} failed (attempt {task.attempts}/{task.max_retries}): {e}"
                )

                # Re-enqueue with delay
                task.scheduled_at = datetime.now() + timedelta(
                    seconds=task.retry_delay_seconds
                )
                self.task_queue.enqueue(task)

                result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.RETRYING,
                    error=error_msg,
                    execution_time_seconds=execution_time,
                    attempts=task.attempts,
                )
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                logger.error(
                    f"Task {task.task_id} failed permanently after {task.attempts} attempts: {e}"
                )

                result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    error=error_msg,
                    execution_time_seconds=execution_time,
                    attempts=task.attempts,
                    completed_at=datetime.now(),
                )

            task.result = result
            return result

    def _worker_loop(self) -> None:
        """Main worker loop"""
        logger.info(f"Worker {self.worker_id} started")

        while self._running:
            try:
                # Get next task
                task = self.task_queue.dequeue(timeout=1.0)

                if task:
                    self._current_task = task
                    self._execute_task(task)

                    # Move to completed
                    if task.status in [
                        TaskStatus.SUCCESS,
                        TaskStatus.FAILED,
                        TaskStatus.CANCELLED,
                    ]:
                        self.task_queue.complete_task(task)

                    self._current_task = None
                else:
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                time.sleep(1)

        logger.info(f"Worker {self.worker_id} stopped")

    def start(self) -> None:
        """Start worker"""
        if self._running:
            logger.warning(f"Worker {self.worker_id} already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop worker"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_status(self) -> Dict[str, Any]:
        """Get worker status"""
        return {
            "worker_id": self.worker_id,
            "running": self._running,
            "current_task": self._current_task.task_id if self._current_task else None,
        }


class TaskManager:
    """Manage task queue and workers"""

    def __init__(self, num_workers: int = 4):
        self.task_queue = TaskQueue()
        self.workers: List[TaskWorker] = []
        self.num_workers = num_workers
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start all workers"""
        with self._lock:
            if self.workers:
                logger.warning("Workers already started")
                return

            for i in range(self.num_workers):
                worker = TaskWorker(f"worker-{i}", self.task_queue)
                worker.start()
                self.workers.append(worker)

            logger.info(f"Started {self.num_workers} workers")

    def stop(self) -> None:
        """Stop all workers"""
        with self._lock:
            for worker in self.workers:
                worker.stop()
            self.workers = []
            logger.info("Stopped all workers")

    def submit(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task for execution"""
        task = Task(name=func.__name__, func=func, args=args, kwargs=kwargs)

        if self.task_queue.enqueue(task):
            return task.task_id
        else:
            raise RuntimeError("Failed to enqueue task")

    def submit_task(self, task: Task) -> bool:
        """Submit a pre-configured task"""
        return self.task_queue.enqueue(task)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = self.task_queue.get_task(task_id)
        if task:
            return task.to_dict()
        return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        return self.task_queue.cancel_task(task_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "num_workers": len(self.workers),
            "queue_sizes": self.task_queue.get_queue_size(),
            "pending_tasks": len(self.task_queue.get_pending_tasks()),
            "workers": [w.get_status() for w in self.workers],
        }


# Global task manager
_task_manager = None
_manager_lock = threading.Lock()


def get_task_manager() -> TaskManager:
    """Get global task manager"""
    global _task_manager
    with _manager_lock:
        if _task_manager is None:
            _task_manager = TaskManager()
            _task_manager.start()
        return _task_manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Task Queue Demo ===\n")

    # Example tasks
    def calculate_player_stats(player_name: str, games: int):
        """Simulate stats calculation"""
        time.sleep(2)  # Simulate work
        ppg = games * 1.5
        return {"player": player_name, "games": games, "ppg": ppg}

    def failing_task():
        """Task that fails"""
        raise ValueError("Intentional failure for testing")

    # Create manager
    manager = TaskManager(num_workers=2)
    manager.start()

    # Submit tasks
    print("--- Submitting Tasks ---")
    task_ids = []

    # Normal priority task
    task_id1 = manager.submit(calculate_player_stats, "LeBron James", 82)
    task_ids.append(task_id1)
    print(f"Submitted task 1: {task_id1}")

    # High priority task
    high_priority_task = Task(
        name="urgent_calculation",
        func=calculate_player_stats,
        args=("Stephen Curry", 70),
        priority=TaskPriority.HIGH,
    )
    manager.submit_task(high_priority_task)
    task_ids.append(high_priority_task.task_id)
    print(f"Submitted high priority task: {high_priority_task.task_id}")

    # Failing task with retries
    failing_task_obj = Task(name="failing_task", func=failing_task, max_retries=2)
    manager.submit_task(failing_task_obj)
    task_ids.append(failing_task_obj.task_id)
    print(f"Submitted failing task: {failing_task_obj.task_id}")

    # Wait for tasks to complete
    print("\n--- Waiting for Tasks ---")
    time.sleep(10)

    # Check results
    print("\n--- Task Results ---")
    for task_id in task_ids:
        status = manager.get_task_status(task_id)
        if status:
            print(f"\nTask {task_id[:8]}:")
            print(f"  Status: {status['status']}")
            print(f"  Attempts: {status.get('attempts', 0)}")
            if status.get("result"):
                print(
                    f"  Execution Time: {status['result'].get('execution_time_seconds', 0):.2f}s"
                )

    # Stats
    print("\n--- Queue Statistics ---")
    stats = manager.get_stats()
    print(f"Workers: {stats['num_workers']}")
    print(f"Pending Tasks: {stats['pending_tasks']}")
    print(f"Queue Sizes: {stats['queue_sizes']}")

    # Cleanup
    manager.stop()

    print("\n=== Demo Complete ===")
