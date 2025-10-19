#!/usr/bin/env python3
"""
Phase Status Manager - Track Phase States and Reruns

This system tracks the status of each phase in the workflow, including:
- Current state (not_started, in_progress, completed, failed, needs_rerun)
- Last execution timestamp
- Dependencies and prerequisites
- Whether a rerun is needed due to AI modifications

Part of Tier 2 implementation for intelligent plan management.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class PhaseState(str, Enum):
    """Possible states for a phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_RERUN = "needs_rerun"
    SKIPPED = "skipped"


@dataclass
class PhaseStatus:
    """Status information for a single phase."""
    phase_id: str
    phase_name: str
    state: PhaseState
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    last_run_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    prerequisites: List[str] = None  # List of phase IDs that must complete first
    needs_rerun_reason: Optional[str] = None
    ai_modified: bool = False  # Did AI modify this phase's outputs?
    ai_modification_timestamp: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d['state'] = self.state.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PhaseStatus':
        """Create from dictionary."""
        data = data.copy()
        data['state'] = PhaseState(data['state'])
        return cls(**data)


class PhaseStatusManager:
    """
    Manager for tracking phase status across workflow runs.
    
    Features:
    - Track state of all phases
    - Mark phases as needing rerun when AI modifies outputs
    - Check prerequisites before allowing phase execution
    - Generate comprehensive status reports
    - Handle parallel phase execution
    
    Example:
        >>> manager = PhaseStatusManager()
        >>> manager.start_phase("phase_0", "Phase 0: Setup")
        >>> manager.complete_phase("phase_0")
        >>> manager.mark_needs_rerun("phase_3", "AI modified synthesis output")
    """
    
    def __init__(self, status_file: Optional[Path] = None):
        """
        Initialize phase status manager.
        
        Args:
            status_file: Path to status JSON file. Defaults to implementation_plans/phase_status.json
        """
        if status_file is None:
            status_file = Path("implementation_plans/phase_status.json")
        
        self.status_file = status_file
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.phases: Dict[str, PhaseStatus] = {}
        self._load_status()
        
        logger.info(f"PhaseStatusManager initialized with {len(self.phases)} tracked phases")
    
    def _load_status(self):
        """Load status from JSON file."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                
                self.phases = {
                    phase_id: PhaseStatus.from_dict(phase_data)
                    for phase_id, phase_data in data.items()
                }
                
                logger.info(f"Loaded status for {len(self.phases)} phases")
            except Exception as e:
                logger.error(f"Error loading phase status: {e}")
                self.phases = {}
        else:
            logger.info("No existing phase status file, starting fresh")
            self._initialize_default_phases()
    
    def _initialize_default_phases(self):
        """Initialize default phase structure."""
        default_phases = [
            ("phase_0", "Phase 0: Cache & Discovery", []),
            ("phase_1", "Phase 1: Book Downloads", ["phase_0"]),
            ("phase_2", "Phase 2: Book Analysis", ["phase_1"]),
            ("phase_3", "Phase 3: Consolidation & Synthesis", ["phase_2"]),
            ("phase_3_5", "Phase 3.5: AI Plan Modifications", ["phase_3"]),
            ("phase_4", "Phase 4: File Generation", ["phase_3_5"]),
            ("phase_5", "Phase 5: Dry-Run Validation", ["phase_4"]),
            ("phase_6", "Phase 6: Conflict Resolution", ["phase_5"]),
            ("phase_7", "Phase 7: Manual Review", ["phase_6"]),
            ("phase_8", "Phase 8: Implementation", ["phase_7"]),
            ("phase_8_5", "Phase 8.5: Pre-Integration Validation", ["phase_8"]),
            ("phase_9", "Phase 9: Integration", ["phase_8_5"]),
            ("phase_10a", "Phase 10A: MCP Enhancements", ["phase_9"]),
            ("phase_10b", "Phase 10B: Simulator Improvements", ["phase_9"]),
            ("phase_11a", "Phase 11A: MCP Testing", ["phase_10a"]),
            ("phase_11b", "Phase 11B: Simulator Testing", ["phase_10b"]),
            ("phase_12a", "Phase 12A: MCP Deployment", ["phase_11a"]),
            ("phase_12b", "Phase 12B: Simulator Deployment", ["phase_11b"]),
        ]
        
        for phase_id, phase_name, prerequisites in default_phases:
            self.phases[phase_id] = PhaseStatus(
                phase_id=phase_id,
                phase_name=phase_name,
                state=PhaseState.NOT_STARTED,
                prerequisites=prerequisites
            )
        
        self._save_status()
        logger.info(f"Initialized {len(default_phases)} default phases")
    
    def _save_status(self):
        """Save status to JSON file."""
        try:
            data = {
                phase_id: phase.to_dict()
                for phase_id, phase in self.phases.items()
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved status for {len(self.phases)} phases")
        except Exception as e:
            logger.error(f"Error saving phase status: {e}")
    
    def start_phase(self, phase_id: str, phase_name: Optional[str] = None):
        """
        Mark a phase as started.
        
        Args:
            phase_id: Unique identifier for the phase
            phase_name: Human-readable name (optional, creates new phase if not exists)
        
        Raises:
            ValueError: If prerequisites not met
        """
        # Create phase if doesn't exist
        if phase_id not in self.phases:
            if phase_name is None:
                phase_name = phase_id.replace('_', ' ').title()
            
            self.phases[phase_id] = PhaseStatus(
                phase_id=phase_id,
                phase_name=phase_name,
                state=PhaseState.NOT_STARTED
            )
        
        phase = self.phases[phase_id]
        
        # Check prerequisites
        unmet_prereqs = self._check_prerequisites(phase_id)
        if unmet_prereqs:
            raise ValueError(
                f"Cannot start {phase_id}: Unmet prerequisites: {', '.join(unmet_prereqs)}"
            )
        
        # Update status
        phase.state = PhaseState.IN_PROGRESS
        phase.started_at = datetime.now().isoformat()
        phase.run_count += 1
        
        self._save_status()
        logger.info(f"✅ Started {phase_id}: {phase.phase_name}")
    
    def complete_phase(self, phase_id: str, duration_seconds: Optional[float] = None):
        """
        Mark a phase as completed.
        
        Args:
            phase_id: Unique identifier for the phase
            duration_seconds: How long the phase took (optional)
        """
        if phase_id not in self.phases:
            raise ValueError(f"Phase {phase_id} not found")
        
        phase = self.phases[phase_id]
        phase.state = PhaseState.COMPLETED
        phase.completed_at = datetime.now().isoformat()
        phase.success_count += 1
        phase.error_message = None
        
        if duration_seconds is not None:
            phase.last_run_duration_seconds = duration_seconds
        elif phase.started_at:
            # Calculate duration
            started = datetime.fromisoformat(phase.started_at)
            completed = datetime.fromisoformat(phase.completed_at)
            phase.last_run_duration_seconds = (completed - started).total_seconds()
        
        self._save_status()
        logger.info(f"✅ Completed {phase_id}: {phase.phase_name} (duration: {phase.last_run_duration_seconds:.1f}s)")
    
    def fail_phase(self, phase_id: str, error_message: str):
        """
        Mark a phase as failed.
        
        Args:
            phase_id: Unique identifier for the phase
            error_message: Description of the failure
        """
        if phase_id not in self.phases:
            raise ValueError(f"Phase {phase_id} not found")
        
        phase = self.phases[phase_id]
        phase.state = PhaseState.FAILED
        phase.failed_at = datetime.now().isoformat()
        phase.failure_count += 1
        phase.error_message = error_message
        
        self._save_status()
        logger.error(f"❌ Failed {phase_id}: {phase.phase_name} - {error_message}")
    
    def mark_needs_rerun(self, phase_id: str, reason: str, ai_modified: bool = True):
        """
        Mark a phase as needing rerun.
        
        Args:
            phase_id: Unique identifier for the phase
            reason: Why the rerun is needed
            ai_modified: Whether this was triggered by AI modification
        """
        if phase_id not in self.phases:
            raise ValueError(f"Phase {phase_id} not found")
        
        phase = self.phases[phase_id]
        phase.state = PhaseState.NEEDS_RERUN
        phase.needs_rerun_reason = reason
        
        if ai_modified:
            phase.ai_modified = True
            phase.ai_modification_timestamp = datetime.now().isoformat()
        
        # Also mark dependent phases
        dependent_phases = self._find_dependent_phases(phase_id)
        for dep_phase_id in dependent_phases:
            dep_phase = self.phases[dep_phase_id]
            if dep_phase.state == PhaseState.COMPLETED:
                dep_phase.state = PhaseState.NEEDS_RERUN
                dep_phase.needs_rerun_reason = f"Upstream phase {phase_id} was modified"
        
        self._save_status()
        logger.warning(f"⚠️  Marked {phase_id} for rerun: {reason}")
        if dependent_phases:
            logger.warning(f"   Also marked dependent phases: {', '.join(dependent_phases)}")
    
    def _check_prerequisites(self, phase_id: str) -> List[str]:
        """
        Check if all prerequisites for a phase are met.
        
        Args:
            phase_id: Phase to check
        
        Returns:
            List of unmet prerequisite phase IDs
        """
        if phase_id not in self.phases:
            return []
        
        phase = self.phases[phase_id]
        unmet = []
        
        for prereq_id in phase.prerequisites:
            if prereq_id not in self.phases:
                unmet.append(prereq_id)
                continue
            
            prereq = self.phases[prereq_id]
            if prereq.state != PhaseState.COMPLETED:
                unmet.append(prereq_id)
        
        return unmet
    
    def _find_dependent_phases(self, phase_id: str) -> List[str]:
        """
        Find all phases that depend on the given phase.
        
        Args:
            phase_id: Phase to check
        
        Returns:
            List of dependent phase IDs
        """
        dependent = []
        
        for other_id, other_phase in self.phases.items():
            if phase_id in other_phase.prerequisites:
                dependent.append(other_id)
        
        return dependent
    
    def get_phases_needing_rerun(self) -> List[str]:
        """Get list of phase IDs that need rerun."""
        return [
            phase_id
            for phase_id, phase in self.phases.items()
            if phase.state == PhaseState.NEEDS_RERUN
        ]
    
    def get_runnable_phases(self) -> List[str]:
        """Get list of phase IDs that can be run now (prerequisites met)."""
        runnable = []
        
        for phase_id, phase in self.phases.items():
            # Skip if already completed (unless needs rerun)
            if phase.state == PhaseState.COMPLETED:
                continue
            
            # Skip if in progress
            if phase.state == PhaseState.IN_PROGRESS:
                continue
            
            # Check prerequisites
            if not self._check_prerequisites(phase_id):
                runnable.append(phase_id)
        
        return runnable
    
    def generate_status_report(self, report_file: Optional[Path] = None) -> str:
        """
        Generate comprehensive status report.
        
        Args:
            report_file: Path to save report. Defaults to PHASE_STATUS_REPORT.md
        
        Returns:
            Report content as string
        """
        if report_file is None:
            report_file = Path("implementation_plans/PHASE_STATUS_REPORT.md")
        
        lines = []
        lines.append("# Phase Status Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().isoformat()}")
        lines.append(f"**Total Phases**: {len(self.phases)}")
        lines.append("")
        
        # Summary statistics
        state_counts = {}
        for phase in self.phases.values():
            state_counts[phase.state] = state_counts.get(phase.state, 0) + 1
        
        lines.append("## Summary")
        lines.append("")
        lines.append("| State | Count |")
        lines.append("|-------|-------|")
        for state in PhaseState:
            count = state_counts.get(state, 0)
            emoji = self._get_state_emoji(state)
            lines.append(f"| {emoji} {state.value.replace('_', ' ').title()} | {count} |")
        lines.append("")
        
        # Phases needing attention
        needs_rerun = self.get_phases_needing_rerun()
        if needs_rerun:
            lines.append("## ⚠️  Phases Needing Rerun")
            lines.append("")
            for phase_id in needs_rerun:
                phase = self.phases[phase_id]
                lines.append(f"- **{phase.phase_name}** ({phase_id})")
                lines.append(f"  - Reason: {phase.needs_rerun_reason}")
                if phase.ai_modified:
                    lines.append(f"  - AI Modified: {phase.ai_modification_timestamp}")
            lines.append("")
        
        # Runnable phases
        runnable = self.get_runnable_phases()
        if runnable:
            lines.append("## ✅ Ready to Run")
            lines.append("")
            for phase_id in runnable:
                phase = self.phases[phase_id]
                lines.append(f"- **{phase.phase_name}** ({phase_id})")
            lines.append("")
        
        # Detailed phase status
        lines.append("## Detailed Phase Status")
        lines.append("")
        
        for phase_id in sorted(self.phases.keys()):
            phase = self.phases[phase_id]
            emoji = self._get_state_emoji(phase.state)
            
            lines.append(f"### {emoji} {phase.phase_name} ({phase_id})")
            lines.append("")
            lines.append(f"- **State**: {phase.state.value.replace('_', ' ').title()}")
            lines.append(f"- **Run Count**: {phase.run_count} (✅ {phase.success_count}, ❌ {phase.failure_count})")
            
            if phase.prerequisites:
                prereq_names = [self.phases[p].phase_name for p in phase.prerequisites if p in self.phases]
                lines.append(f"- **Prerequisites**: {', '.join(prereq_names)}")
            
            if phase.started_at:
                lines.append(f"- **Started**: {phase.started_at}")
            
            if phase.completed_at:
                lines.append(f"- **Completed**: {phase.completed_at}")
                if phase.last_run_duration_seconds:
                    lines.append(f"- **Duration**: {phase.last_run_duration_seconds:.1f}s")
            
            if phase.failed_at:
                lines.append(f"- **Failed**: {phase.failed_at}")
            
            if phase.error_message:
                lines.append(f"- **Error**: {phase.error_message}")
            
            if phase.needs_rerun_reason:
                lines.append(f"- **Rerun Reason**: {phase.needs_rerun_reason}")
            
            if phase.ai_modified:
                lines.append(f"- **AI Modified**: ✓ ({phase.ai_modification_timestamp})")
            
            lines.append("")
        
        report_content = '\n'.join(lines)
        
        # Save to file
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Generated phase status report: {report_file}")
        
        return report_content
    
    def _get_state_emoji(self, state: PhaseState) -> str:
        """Get emoji for phase state."""
        emoji_map = {
            PhaseState.NOT_STARTED: "⚪",
            PhaseState.IN_PROGRESS: "🔵",
            PhaseState.COMPLETED: "✅",
            PhaseState.FAILED: "❌",
            PhaseState.NEEDS_RERUN: "⚠️",
            PhaseState.SKIPPED: "⏭️",
        }
        return emoji_map.get(state, "❓")
    
    def reset_phase(self, phase_id: str):
        """Reset a phase to NOT_STARTED state."""
        if phase_id not in self.phases:
            raise ValueError(f"Phase {phase_id} not found")
        
        phase = self.phases[phase_id]
        phase.state = PhaseState.NOT_STARTED
        phase.needs_rerun_reason = None
        phase.ai_modified = False
        phase.error_message = None
        
        self._save_status()
        logger.info(f"Reset {phase_id} to NOT_STARTED")


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("PHASE STATUS MANAGER DEMO")
    print("=" * 70)
    print()
    
    # Initialize manager
    manager = PhaseStatusManager()
    
    # Simulate phase execution
    print("Simulating phase execution...")
    print()
    
    # Phase 0
    manager.start_phase("phase_0")
    manager.complete_phase("phase_0", duration_seconds=10.5)
    
    # Phase 1
    manager.start_phase("phase_1")
    manager.complete_phase("phase_1", duration_seconds=30.2)
    
    # Phase 2
    manager.start_phase("phase_2")
    manager.complete_phase("phase_2", duration_seconds=120.5)
    
    # Phase 3
    manager.start_phase("phase_3")
    manager.complete_phase("phase_3", duration_seconds=45.0)
    
    # AI modifies Phase 3 output
    print("Simulating AI modification...")
    manager.mark_needs_rerun("phase_3", "AI improved synthesis with new recommendations")
    print()
    
    # Generate report
    print("Generating status report...")
    report = manager.generate_status_report()
    print()
    print(report)
    
    print("=" * 70)
    print("Demo complete! Check implementation_plans/PHASE_STATUS_REPORT.md")
    print("=" * 70)

