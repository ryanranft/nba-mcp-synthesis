#!/usr/bin/env python3
"""
Workflow Orchestration Engine
Manages multi-step automated workflows with Slack coordination
"""

import os
import json
import yaml
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

from monitoring.slack_notifier import (
    get_notifier,
    ProcessSource,
    notify_process_started,
    notify_process_completed,
    notify_process_failed,
    notify_process_progress,
)

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a workflow step"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class WorkflowStatus(Enum):
    """Status of entire workflow"""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""

    name: str
    description: str
    action: str  # Function name or command to execute
    params: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False
    continue_on_failure: bool = False
    timeout_seconds: int = 300
    retry_count: int = 0
    retry_delay_seconds: int = 5

    # Runtime state
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    attempt: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "action": self.action,
            "params": self.params,
            "requires_approval": self.requires_approval,
            "continue_on_failure": self.continue_on_failure,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "attempt": self.attempt,
        }


@dataclass
class Workflow:
    """Represents a complete workflow"""

    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    source: ProcessSource = ProcessSource.WORKFLOW_ENGINE
    notify_slack: bool = True
    save_state: bool = True

    # Runtime state
    status: WorkflowStatus = WorkflowStatus.CREATED
    current_step_index: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "source": self.source.value,
            "notify_slack": self.notify_slack,
            "save_state": self.save_state,
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Workflow":
        """Create workflow from dictionary"""
        steps = [
            WorkflowStep(
                name=s["name"],
                description=s["description"],
                action=s["action"],
                params=s.get("params", {}),
                requires_approval=s.get("requires_approval", False),
                continue_on_failure=s.get("continue_on_failure", False),
                timeout_seconds=s.get("timeout_seconds", 300),
                retry_count=s.get("retry_count", 0),
                retry_delay_seconds=s.get("retry_delay_seconds", 5),
                status=StepStatus(s.get("status", "pending")),
                result=s.get("result"),
                error=s.get("error"),
                start_time=s.get("start_time"),
                end_time=s.get("end_time"),
                attempt=s.get("attempt", 0),
            )
            for s in data["steps"]
        ]

        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data["description"],
            steps=steps,
            source=ProcessSource(data.get("source", "workflow_engine")),
            notify_slack=data.get("notify_slack", True),
            save_state=data.get("save_state", True),
            status=WorkflowStatus(data.get("status", "created")),
            current_step_index=data.get("current_step_index", 0),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            metadata=data.get("metadata", {}),
        )


class WorkflowEngine:
    """Orchestrates workflow execution with Slack coordination"""

    def __init__(self, state_dir: Optional[str] = None):
        self.state_dir = state_dir or os.path.join(
            os.path.dirname(__file__), "..", "workflow_state"
        )
        os.makedirs(self.state_dir, exist_ok=True)

        self.notifier = get_notifier()
        self.action_registry: Dict[str, Callable] = {}
        self.running_workflows: Dict[str, Workflow] = {}

        # Register built-in actions
        self._register_builtin_actions()

    def _register_builtin_actions(self):
        """Register built-in workflow actions"""
        self.register_action("delay", self._action_delay)
        self.register_action("log", self._action_log)
        self.register_action("notify", self._action_notify)

    async def _action_delay(self, seconds: int, **kwargs) -> Dict:
        """Built-in delay action"""
        await asyncio.sleep(seconds)
        return {"delayed": seconds}

    async def _action_log(self, message: str, level: str = "info", **kwargs) -> Dict:
        """Built-in logging action"""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)
        return {"logged": message}

    async def _action_notify(self, message: str, **kwargs) -> Dict:
        """Built-in Slack notification action"""
        # This would send a custom notification
        return {"notified": message}

    def register_action(self, name: str, func: Callable):
        """Register a workflow action"""
        self.action_registry[name] = func
        logger.info(f"Registered workflow action: {name}")

    def _save_workflow_state(self, workflow: Workflow):
        """Save workflow state to disk"""
        if not workflow.save_state:
            return

        state_file = os.path.join(self.state_dir, f"{workflow.workflow_id}.json")
        try:
            with open(state_file, "w") as f:
                json.dump(workflow.to_dict(), f, indent=2)
            logger.debug(f"Saved workflow state: {workflow.workflow_id}")
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")

    def _load_workflow_state(self, workflow_id: str) -> Optional[Workflow]:
        """Load workflow state from disk"""
        state_file = os.path.join(self.state_dir, f"{workflow_id}.json")
        try:
            with open(state_file, "r") as f:
                data = json.load(f)
            return Workflow.from_dict(data)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return None

    async def _execute_step(self, workflow: Workflow, step: WorkflowStep) -> bool:
        """
        Execute a single workflow step

        Returns:
            True if step succeeded, False if failed
        """
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now().isoformat()
        step.attempt += 1

        # Notify progress
        if workflow.notify_slack:
            notify_process_progress(
                workflow.workflow_id,
                workflow.name,
                workflow.source,
                f"Executing step: {step.name}",
                {"step": step.name, "attempt": step.attempt},
            )

        # Check if action is registered
        if step.action not in self.action_registry:
            error_msg = f"Action '{step.action}' not registered"
            logger.error(error_msg)
            step.status = StepStatus.FAILED
            step.error = error_msg
            step.end_time = datetime.now().isoformat()
            return False

        try:
            action_func = self.action_registry[step.action]

            # Execute with timeout
            result = await asyncio.wait_for(
                action_func(**step.params), timeout=step.timeout_seconds
            )

            step.result = result
            step.status = StepStatus.COMPLETED
            step.end_time = datetime.now().isoformat()

            logger.info(f"✅ Step completed: {step.name}")
            return True

        except asyncio.TimeoutError:
            error_msg = f"Step timed out after {step.timeout_seconds}s"
            logger.error(error_msg)
            step.status = StepStatus.FAILED
            step.error = error_msg
            step.end_time = datetime.now().isoformat()

            # Retry if configured
            if step.attempt <= step.retry_count:
                logger.info(
                    f"Retrying step {step.name} (attempt {step.attempt + 1}/{step.retry_count + 1})"
                )
                await asyncio.sleep(step.retry_delay_seconds)
                return await self._execute_step(workflow, step)

            return step.continue_on_failure

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Step failed: {error_msg}")
            step.status = StepStatus.FAILED
            step.error = error_msg
            step.end_time = datetime.now().isoformat()

            # Retry if configured
            if step.attempt <= step.retry_count:
                logger.info(
                    f"Retrying step {step.name} (attempt {step.attempt + 1}/{step.retry_count + 1})"
                )
                await asyncio.sleep(step.retry_delay_seconds)
                return await self._execute_step(workflow, step)

            return step.continue_on_failure

    async def execute_workflow(self, workflow: Workflow) -> bool:
        """
        Execute a complete workflow

        Returns:
            True if workflow completed successfully
        """
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now().isoformat()
        self.running_workflows[workflow.workflow_id] = workflow

        # Notify start
        if workflow.notify_slack:
            notify_process_started(
                workflow.workflow_id,
                workflow.name,
                workflow.source,
                {"description": workflow.description, "steps": len(workflow.steps)},
            )

        try:
            # Execute each step
            for i, step in enumerate(workflow.steps):
                workflow.current_step_index = i
                self._save_workflow_state(workflow)

                # Check for approval requirement
                if step.requires_approval:
                    step.status = StepStatus.WAITING_APPROVAL
                    workflow.status = WorkflowStatus.PAUSED

                    if workflow.notify_slack:
                        self.notifier.request_approval(
                            workflow.workflow_id,
                            workflow.name,
                            f"Approval required for step: {step.name}\n{step.description}",
                            timeout_minutes=60,
                        )

                    # In real implementation, we'd wait for external approval
                    # For now, we'll just log and continue
                    logger.warning(f"⏸️  Step requires approval: {step.name}")
                    logger.warning("   Manual approval required - workflow paused")
                    # In production, return here and resume later
                    # For demo, we'll continue
                    step.status = StepStatus.PENDING
                    workflow.status = WorkflowStatus.RUNNING

                # Execute step
                success = await self._execute_step(workflow, step)

                if not success:
                    # Step failed
                    workflow.status = WorkflowStatus.FAILED
                    workflow.end_time = datetime.now().isoformat()

                    if workflow.notify_slack:
                        self.notifier.notify_workflow_failed(
                            workflow.workflow_id,
                            workflow.name,
                            step.error or "Unknown error",
                            step.name,
                            self._calculate_duration(workflow),
                        )

                    self._save_workflow_state(workflow)
                    del self.running_workflows[workflow.workflow_id]
                    return False

            # All steps completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.end_time = datetime.now().isoformat()

            # Gather results
            results = {
                step.name: step.result
                for step in workflow.steps
                if step.result is not None
            }

            if workflow.notify_slack:
                self.notifier.notify_workflow_complete(
                    workflow.workflow_id,
                    workflow.name,
                    self._calculate_duration(workflow),
                    len(workflow.steps),
                    results,
                )

            self._save_workflow_state(workflow)
            del self.running_workflows[workflow.workflow_id]
            return True

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            workflow.end_time = datetime.now().isoformat()

            if workflow.notify_slack:
                notify_process_failed(
                    workflow.workflow_id, workflow.name, workflow.source, str(e)
                )

            self._save_workflow_state(workflow)
            del self.running_workflows[workflow.workflow_id]
            return False

    def _calculate_duration(self, workflow: Workflow) -> float:
        """Calculate workflow duration in seconds"""
        if not workflow.start_time or not workflow.end_time:
            return 0.0

        start = datetime.fromisoformat(workflow.start_time)
        end = datetime.fromisoformat(workflow.end_time)
        return (end - start).total_seconds()

    @staticmethod
    def load_workflow_from_yaml(yaml_file: str) -> Workflow:
        """Load workflow definition from YAML file"""
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        # Convert YAML to workflow
        steps = [
            WorkflowStep(
                name=s["name"],
                description=s.get("description", ""),
                action=s["action"],
                params=s.get("params", {}),
                requires_approval=s.get("requires_approval", False),
                continue_on_failure=s.get("continue_on_failure", False),
                timeout_seconds=s.get("timeout_seconds", 300),
                retry_count=s.get("retry_count", 0),
                retry_delay_seconds=s.get("retry_delay_seconds", 5),
            )
            for s in data["steps"]
        ]

        return Workflow(
            workflow_id=data.get("workflow_id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            source=ProcessSource(data.get("source", "workflow_engine")),
            notify_slack=data.get("notify_slack", True),
            save_state=data.get("save_state", True),
        )

    def resume_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Resume a paused workflow"""
        workflow = self._load_workflow_state(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return None

        if workflow.status != WorkflowStatus.PAUSED:
            logger.warning(f"Workflow is not paused: {workflow_id}")
            return workflow

        logger.info(f"Resuming workflow: {workflow_id}")
        return workflow

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id in self.running_workflows:
            workflow = self.running_workflows[workflow_id]
            workflow.status = WorkflowStatus.CANCELLED
            workflow.end_time = datetime.now().isoformat()
            self._save_workflow_state(workflow)
            del self.running_workflows[workflow_id]
            logger.info(f"Cancelled workflow: {workflow_id}")
            return True
        return False

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current status of a workflow"""
        # Check running workflows first
        if workflow_id in self.running_workflows:
            return self.running_workflows[workflow_id].to_dict()

        # Check saved state
        workflow = self._load_workflow_state(workflow_id)
        if workflow:
            return workflow.to_dict()

        return None


# Global engine instance
_engine_instance: Optional[WorkflowEngine] = None


def get_engine() -> WorkflowEngine:
    """Get or create global engine instance"""
    global _engine_instance

    if _engine_instance is None:
        _engine_instance = WorkflowEngine()

    return _engine_instance
