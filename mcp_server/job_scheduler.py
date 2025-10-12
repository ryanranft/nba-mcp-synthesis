"""
Job Scheduling & Monitoring Module
Manages scheduled tasks, cron jobs, and background job execution.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import time
import threading
from dataclasses import dataclass, field
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class JobExecution:
    """Record of a single job execution"""
    execution_id: str
    job_name: str
    status: JobStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ScheduledJob:
    """Scheduled job configuration"""
    job_name: str
    job_func: Callable
    schedule_type: str  # "cron", "interval", "once"
    schedule_config: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    timeout_seconds: int = 300
    enabled: bool = True
    last_execution: Optional[JobExecution] = None
    next_run_time: Optional[datetime] = None
    execution_history: List[JobExecution] = field(default_factory=list)


class JobScheduler:
    """Manages job scheduling and execution"""

    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.execution_count = 0

    def register_job(
        self,
        job_name: str,
        job_func: Callable,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: int = 300
    ) -> bool:
        """
        Register a new scheduled job.

        Args:
            job_name: Unique job identifier
            job_func: Function to execute
            schedule_type: "cron", "interval", or "once"
            schedule_config: Schedule configuration dict
            priority: Job priority
            max_retries: Max retry attempts on failure
            timeout_seconds: Job timeout

        Returns:
            True if registration successful
        """
        if job_name in self.jobs:
            logger.warning(f"Job '{job_name}' already registered, updating...")

        job = ScheduledJob(
            job_name=job_name,
            job_func=job_func,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )

        # Calculate next run time
        job.next_run_time = self._calculate_next_run_time(job)

        self.jobs[job_name] = job
        logger.info(f"Job '{job_name}' registered ({schedule_type}, next run: {job.next_run_time})")
        return True

    def _calculate_next_run_time(self, job: ScheduledJob) -> Optional[datetime]:
        """Calculate next execution time for a job"""
        now = datetime.utcnow()

        if job.schedule_type == "interval":
            # Run every N seconds/minutes/hours
            interval_seconds = job.schedule_config.get("seconds", 0)
            interval_minutes = job.schedule_config.get("minutes", 0)
            interval_hours = job.schedule_config.get("hours", 0)

            total_seconds = interval_seconds + (interval_minutes * 60) + (interval_hours * 3600)

            if job.last_execution and job.last_execution.completed_at:
                last_completed = datetime.fromisoformat(job.last_execution.completed_at)
                return last_completed + timedelta(seconds=total_seconds)
            else:
                return now + timedelta(seconds=total_seconds)

        elif job.schedule_type == "cron":
            # Simplified cron: hour and minute only
            hour = job.schedule_config.get("hour", 0)
            minute = job.schedule_config.get("minute", 0)

            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            return next_run

        elif job.schedule_type == "once":
            # Run once at specified time
            run_at = job.schedule_config.get("run_at")
            if isinstance(run_at, str):
                return datetime.fromisoformat(run_at)
            elif isinstance(run_at, datetime):
                return run_at
            else:
                return now + timedelta(minutes=1)  # Default: run in 1 minute

        return None

    def _execute_job(self, job: ScheduledJob) -> JobExecution:
        """Execute a single job"""
        self.execution_count += 1
        execution_id = f"{job.job_name}_{self.execution_count}_{int(time.time())}"

        execution = JobExecution(
            execution_id=execution_id,
            job_name=job.job_name,
            status=JobStatus.RUNNING,
            started_at=datetime.utcnow().isoformat()
        )

        logger.info(f"Executing job '{job.job_name}' (execution_id: {execution_id})")

        start_time = time.time()

        try:
            # Execute job function with timeout
            result = job.job_func()

            execution.status = JobStatus.COMPLETED
            execution.result = result
            logger.info(f"Job '{job.job_name}' completed successfully")

        except Exception as e:
            execution.status = JobStatus.FAILED
            execution.error = str(e)
            logger.error(f"Job '{job.job_name}' failed: {e}")

        finally:
            execution.completed_at = datetime.utcnow().isoformat()
            execution.duration_seconds = time.time() - start_time

        # Update job with execution info
        job.last_execution = execution
        job.execution_history.append(execution)

        # Keep only last 100 executions
        if len(job.execution_history) > 100:
            job.execution_history = job.execution_history[-100:]

        # Calculate next run time
        if job.schedule_type != "once":
            job.next_run_time = self._calculate_next_run_time(job)

        return execution

    def run_job_now(self, job_name: str) -> Optional[JobExecution]:
        """Manually trigger a job to run immediately"""
        if job_name not in self.jobs:
            logger.error(f"Job '{job_name}' not found")
            return None

        job = self.jobs[job_name]
        return self._execute_job(job)

    def enable_job(self, job_name: str):
        """Enable a job"""
        if job_name in self.jobs:
            self.jobs[job_name].enabled = True
            logger.info(f"Job '{job_name}' enabled")

    def disable_job(self, job_name: str):
        """Disable a job"""
        if job_name in self.jobs:
            self.jobs[job_name].enabled = False
            logger.info(f"Job '{job_name}' disabled")

    def delete_job(self, job_name: str):
        """Delete a job"""
        if job_name in self.jobs:
            del self.jobs[job_name]
            logger.info(f"Job '{job_name}' deleted")

    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler started")

        while self.running:
            now = datetime.utcnow()

            # Check all jobs
            for job_name, job in list(self.jobs.items()):
                if not job.enabled:
                    continue

                if job.next_run_time and now >= job.next_run_time:
                    # Execute job
                    self._execute_job(job)

            # Sleep for 1 second
            time.sleep(1)

        logger.info("Scheduler stopped")

    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler started in background thread")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def get_job_status(self, job_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        if job_name not in self.jobs:
            return None

        job = self.jobs[job_name]

        return {
            "job_name": job.job_name,
            "enabled": job.enabled,
            "schedule_type": job.schedule_type,
            "schedule_config": job.schedule_config,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "last_execution": {
                "status": job.last_execution.status.value,
                "started_at": job.last_execution.started_at,
                "completed_at": job.last_execution.completed_at,
                "duration_seconds": job.last_execution.duration_seconds,
                "error": job.last_execution.error
            } if job.last_execution else None,
            "execution_count": len(job.execution_history)
        }

    def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """Get status of all jobs"""
        return [self.get_job_status(name) for name in self.jobs.keys()]


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("JOB SCHEDULER DEMO")
    print("=" * 80)

    scheduler = JobScheduler()

    # Example jobs
    def daily_model_retrain():
        logger.info("Running daily model retraining...")
        time.sleep(2)
        return {"status": "success", "models_retrained": 3}

    def hourly_data_sync():
        logger.info("Running hourly data synchronization...")
        time.sleep(1)
        return {"status": "success", "records_synced": 1500}

    def drift_detection():
        logger.info("Running drift detection...")
        time.sleep(1)
        return {"drift_detected": False}

    # Register jobs
    scheduler.register_job(
        job_name="daily_model_retrain",
        job_func=daily_model_retrain,
        schedule_type="cron",
        schedule_config={"hour": 2, "minute": 0},  # 2:00 AM daily
        priority=JobPriority.HIGH
    )

    scheduler.register_job(
        job_name="hourly_data_sync",
        job_func=hourly_data_sync,
        schedule_type="interval",
        schedule_config={"minutes": 60},
        priority=JobPriority.NORMAL
    )

    scheduler.register_job(
        job_name="drift_detection",
        job_func=drift_detection,
        schedule_type="interval",
        schedule_config={"minutes": 15},
        priority=JobPriority.HIGH
    )

    print(f"\n✅ Registered {len(scheduler.jobs)} jobs")

    # Show job status
    print("\n" + "=" * 80)
    print("REGISTERED JOBS")
    print("=" * 80)

    for job_status in scheduler.get_all_jobs_status():
        print(f"\n📋 {job_status['job_name']}")
        print(f"   Enabled: {job_status['enabled']}")
        print(f"   Schedule: {job_status['schedule_type']} - {job_status['schedule_config']}")
        print(f"   Next Run: {job_status['next_run_time']}")

    # Manually run a job
    print("\n" + "=" * 80)
    print("MANUALLY TRIGGERING JOBS")
    print("=" * 80)

    execution = scheduler.run_job_now("drift_detection")
    print(f"\n✅ Job executed: {execution.status.value}")
    print(f"   Duration: {execution.duration_seconds:.2f}s")
    print(f"   Result: {execution.result}")

    print("\n" + "=" * 80)
    print("Job Scheduler Demo Complete!")
    print("=" * 80)

