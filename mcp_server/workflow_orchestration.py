"""
Workflow Orchestration Module
Simple DAG-based workflow orchestration (Airflow-compatible design).
"""

import logging
from typing import Dict, Optional, Any, Callable, List, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class Task:
    """Workflow task"""
    task_id: str
    func: Callable
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    
    # Execution state
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class WorkflowRun:
    """Workflow execution run"""
    run_id: str
    workflow_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    tasks: Dict[str, Task] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DAG:
    """Directed Acyclic Graph for workflow orchestration"""
    
    def __init__(self, dag_id: str, description: str = "", schedule: Optional[str] = None):
        """
        Initialize DAG.
        
        Args:
            dag_id: Unique DAG identifier
            description: DAG description
            schedule: Cron-like schedule (e.g., "0 0 * * *" for daily)
        """
        self.dag_id = dag_id
        self.description = description
        self.schedule = schedule
        self.tasks: Dict[str, Task] = {}
        self.runs: List[WorkflowRun] = []
        
        # Storage for workflow metadata
        self.artifacts_path = Path(f"./workflow_artifacts/{dag_id}")
        self.artifacts_path.mkdir(parents=True, exist_ok=True)
    
    def add_task(
        self,
        task_id: str,
        func: Callable,
        dependencies: Optional[List[str]] = None,
        max_retries: int = 3,
        timeout_seconds: Optional[int] = None
    ):
        """
        Add a task to the DAG.
        
        Args:
            task_id: Unique task identifier
            func: Function to execute
            dependencies: List of task IDs this task depends on
            max_retries: Maximum retry attempts
            timeout_seconds: Task timeout
        """
        task = Task(
            task_id=task_id,
            func=func,
            dependencies=dependencies or [],
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        
        self.tasks[task_id] = task
        logger.info(f"Added task {task_id} to DAG {self.dag_id}")
    
    def _validate_dag(self) -> bool:
        """Validate DAG has no cycles"""
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dep in self.tasks[task_id].dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        for task_id in self.tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    logger.error(f"DAG {self.dag_id} has a cycle!")
                    return False
        
        return True
    
    def _topological_sort(self) -> List[str]:
        """Return tasks in execution order (topological sort)"""
        in_degree = {task_id: 0 for task_id in self.tasks}
        
        # Calculate in-degrees
        for task in self.tasks.values():
            for dep in task.dependencies:
                in_degree[task.task_id] = in_degree.get(task.task_id, 0) + 1
        
        # Find tasks with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Reduce in-degree for dependent tasks
            for task_id, task in self.tasks.items():
                if current in task.dependencies:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        
        return result
    
    def execute(self, run_id: Optional[str] = None, context: Optional[Dict] = None) -> WorkflowRun:
        """
        Execute the workflow.
        
        Args:
            run_id: Optional run identifier
            context: Optional execution context
            
        Returns:
            WorkflowRun with execution results
        """
        if not run_id:
            run_id = f"{self.dag_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        if not self._validate_dag():
            raise ValueError("DAG validation failed: cycle detected")
        
        # Create run
        run = WorkflowRun(
            run_id=run_id,
            workflow_id=self.dag_id,
            start_time=datetime.utcnow(),
            status=TaskStatus.RUNNING,
            metadata=context or {}
        )
        
        # Copy tasks for this run
        for task_id, task in self.tasks.items():
            run.tasks[task_id] = Task(
                task_id=task.task_id,
                func=task.func,
                dependencies=task.dependencies.copy(),
                max_retries=task.max_retries,
                timeout_seconds=task.timeout_seconds
            )
        
        logger.info(f"Starting workflow run: {run_id}")
        
        # Get execution order
        execution_order = self._topological_sort()
        
        # Execute tasks in order
        completed_tasks: Set[str] = set()
        failed = False
        
        for task_id in execution_order:
            task = run.tasks[task_id]
            
            # Check if dependencies completed successfully
            deps_ok = all(
                dep in completed_tasks and run.tasks[dep].status == TaskStatus.SUCCESS
                for dep in task.dependencies
            )
            
            if not deps_ok:
                task.status = TaskStatus.SKIPPED
                logger.warning(f"Task {task_id} skipped due to failed dependencies")
                continue
            
            # Execute task
            success = self._execute_task(task, context)
            
            if success:
                completed_tasks.add(task_id)
            else:
                failed = True
                logger.error(f"Task {task_id} failed")
                # Continue to mark dependent tasks as skipped
        
        # Finalize run
        run.status = TaskStatus.SUCCESS if not failed else TaskStatus.FAILED
        run.end_time = datetime.utcnow()
        
        self.runs.append(run)
        self._save_run_metadata(run)
        
        logger.info(
            f"Workflow run {run_id} completed with status {run.status.value} "
            f"in {(run.end_time - run.start_time).total_seconds():.2f}s"
        )
        
        return run
    
    def _execute_task(self, task: Task, context: Optional[Dict]) -> bool:
        """Execute a single task with retry logic"""
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.utcnow()
        
        logger.info(f"Executing task: {task.task_id}")
        
        while task.retry_count <= task.max_retries:
            try:
                # Execute task function
                task.result = task.func(context)
                task.status = TaskStatus.SUCCESS
                task.end_time = datetime.utcnow()
                
                logger.info(f"Task {task.task_id} completed successfully")
                return True
                
            except Exception as e:
                task.error = str(e)
                task.retry_count += 1
                
                if task.retry_count <= task.max_retries:
                    task.status = TaskStatus.RETRYING
                    logger.warning(
                        f"Task {task.task_id} failed (attempt {task.retry_count}/{task.max_retries}): {e}"
                    )
                else:
                    task.status = TaskStatus.FAILED
                    task.end_time = datetime.utcnow()
                    logger.error(f"Task {task.task_id} failed after {task.max_retries} retries: {e}")
                    return False
        
        return False
    
    def _save_run_metadata(self, run: WorkflowRun):
        """Save run metadata to disk"""
        metadata_file = self.artifacts_path / f"{run.run_id}_metadata.json"
        
        metadata = {
            "run_id": run.run_id,
            "workflow_id": run.workflow_id,
            "start_time": run.start_time.isoformat(),
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "status": run.status.value,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "retry_count": task.retry_count,
                    "duration_seconds": (
                        (task.end_time - task.start_time).total_seconds()
                        if task.end_time and task.start_time else None
                    ),
                    "error": task.error
                }
                for task in run.tasks.values()
            ]
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved run metadata to {metadata_file}")
    
    def get_run_history(self, limit: int = 10) -> List[Dict]:
        """Get workflow run history"""
        return [
            {
                "run_id": run.run_id,
                "status": run.status.value,
                "start_time": run.start_time.isoformat(),
                "duration_seconds": (
                    (run.end_time - run.start_time).total_seconds()
                    if run.end_time else None
                ),
                "tasks_completed": len([
                    t for t in run.tasks.values()
                    if t.status == TaskStatus.SUCCESS
                ]),
                "tasks_total": len(run.tasks)
            }
            for run in sorted(self.runs, key=lambda r: r.start_time, reverse=True)[:limit]
        ]


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("WORKFLOW ORCHESTRATION DEMO")
    print("=" * 80)
    
    # Define tasks
    def extract_data(context):
        print("  → Extracting data from database")
        return {"records": 1000}
    
    def transform_data(context):
        print("  → Transforming data")
        return {"transformed_records": 950}
    
    def validate_data(context):
        print("  → Validating data quality")
        return {"validation_passed": True}
    
    def load_to_warehouse(context):
        print("  → Loading to data warehouse")
        return {"loaded_records": 950}
    
    def send_notification(context):
        print("  → Sending completion notification")
        return {"notification_sent": True}
    
    # Create DAG
    print("\n" + "=" * 80)
    print("CREATING WORKFLOW DAG")
    print("=" * 80)
    
    dag = DAG(
        dag_id="nba_etl_pipeline",
        description="Daily ETL pipeline for NBA stats",
        schedule="0 2 * * *"  # Run at 2 AM daily
    )
    
    # Add tasks with dependencies
    dag.add_task("extract", extract_data)
    dag.add_task("transform", transform_data, dependencies=["extract"])
    dag.add_task("validate", validate_data, dependencies=["transform"])
    dag.add_task("load", load_to_warehouse, dependencies=["validate"])
    dag.add_task("notify", send_notification, dependencies=["load"])
    
    print(f"\n✅ Created DAG with {len(dag.tasks)} tasks")
    print(f"Schedule: {dag.schedule}")
    
    # Show execution order
    print("\nExecution order:")
    for i, task_id in enumerate(dag._topological_sort(), 1):
        deps = dag.tasks[task_id].dependencies
        deps_str = f" (depends on: {', '.join(deps)})" if deps else ""
        print(f"  {i}. {task_id}{deps_str}")
    
    # Execute workflow
    print("\n" + "=" * 80)
    print("EXECUTING WORKFLOW")
    print("=" * 80)
    
    run = dag.execute(context={"user_id": "admin", "date": "2025-10-12"})
    
    # Show results
    print("\n" + "=" * 80)
    print("WORKFLOW RESULTS")
    print("=" * 80)
    
    print(f"\nRun ID: {run.run_id}")
    print(f"Status: {run.status.value}")
    print(f"Duration: {(run.end_time - run.start_time).total_seconds():.2f}s")
    
    print("\nTask Results:")
    for task in run.tasks.values():
        status_icon = {
            TaskStatus.SUCCESS: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.SKIPPED: "⏭️"
        }.get(task.status, "❓")
        
        print(f"\n  {status_icon} {task.task_id}")
        print(f"     Status: {task.status.value}")
        if task.start_time and task.end_time:
            print(f"     Duration: {(task.end_time - task.start_time).total_seconds():.2f}s")
        if task.error:
            print(f"     Error: {task.error}")
    
    # Run history
    print("\n" + "=" * 80)
    print("RUN HISTORY")
    print("=" * 80)
    
    history = dag.get_run_history()
    for h in history:
        print(f"\n{h['run_id']}:")
        print(f"  Status: {h['status']}")
        print(f"  Duration: {h['duration_seconds']:.2f}s")
        print(f"  Tasks: {h['tasks_completed']}/{h['tasks_total']}")
    
    print("\n" + "=" * 80)
    print("Workflow Orchestration Demo Complete!")
    print("=" * 80)

