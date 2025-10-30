#!/usr/bin/env python3
"""
Phase Status Manager - Track and manage workflow phase states

Provides centralized tracking of phase execution status with support for:
- State transitions (PENDING → IN_PROGRESS → COMPLETE/FAILED)
- Rerun detection and marking
- Status persistence and recovery
- Comprehensive status reporting

States:
- PENDING: Phase not yet started
- IN_PROGRESS: Phase currently executing
- COMPLETE: Phase completed successfully
- FAILED: Phase failed with errors
- NEEDS_RERUN: Phase complete but requires rerun due to upstream changes

Usage:
    from scripts.phase_status_manager import PhaseStatusManager

    status_mgr = PhaseStatusManager()

    # Start phase
    status_mgr.start_phase("phase_2_analysis")

    # Complete phase
    status_mgr.complete_phase("phase_2_analysis", {"books_analyzed": 45})

    # Mark for rerun
    status_mgr.mark_needs_rerun("phase_3_synthesis", "New books added")

    # Generate report
    status_mgr.generate_report()
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PhaseState(str, Enum):
    """Phase execution states"""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    NEEDS_RERUN = "NEEDS_RERUN"


@dataclass
class PhaseStatus:
    """Status information for a single phase"""

    phase_id: str
    state: PhaseState
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    rerun_reason: Optional[str] = None
    skip_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    dependencies_met: bool = True
    last_updated: Optional[str] = None


class PhaseStatusManager:
    """
    Centralized phase status tracking and management.

    Features:
    - State machine for phase transitions
    - Dependency tracking
    - Rerun detection
    - Status persistence
    - Comprehensive reporting

    State Transitions:
    PENDING → IN_PROGRESS → COMPLETE
    PENDING → IN_PROGRESS → FAILED
    COMPLETE → NEEDS_RERUN (when upstream changes)
    NEEDS_RERUN → IN_PROGRESS (when rerun starts)
    """

    # Define all workflow phases
    ALL_PHASES = [
        "phase_0_foundation",
        "phase_1_data_inventory",
        "phase_2_analysis",
        "phase_3_synthesis",
        "phase_3.5_modifications",
        "phase_4_file_generation",
        "phase_5_predictions",
        "phase_6_validation",
        "phase_7_integration_prep",
        "phase_8_smart_integration",
        "phase_8.5_validation",
        "phase_9_integration",
        "phase_10a_mcp_improvements",
        "phase_10b_simulator_improvements",
        "phase_11_documentation",
        "phase_12_deployment",
    ]

    # Phase dependencies (phase -> list of dependencies)
    DEPENDENCIES = {
        "phase_1_data_inventory": ["phase_0_foundation"],
        "phase_2_analysis": ["phase_0_foundation"],
        "phase_3_synthesis": ["phase_2_analysis"],
        "phase_3.5_modifications": ["phase_3_synthesis"],
        "phase_4_file_generation": ["phase_3_synthesis", "phase_3.5_modifications"],
        "phase_5_predictions": ["phase_2_analysis"],
        "phase_6_validation": ["phase_4_file_generation"],
        "phase_7_integration_prep": ["phase_4_file_generation"],
        "phase_8_smart_integration": ["phase_7_integration_prep"],
        "phase_8.5_validation": ["phase_8_smart_integration"],
        "phase_9_integration": ["phase_8.5_validation"],
        "phase_10a_mcp_improvements": ["phase_9_integration"],
        "phase_10b_simulator_improvements": ["phase_9_integration"],
        "phase_11_documentation": ["phase_9_integration"],
        "phase_12_deployment": ["phase_11_documentation"],
    }

    def __init__(self, status_file: Optional[Path] = None):
        """
        Initialize Phase Status Manager.

        Args:
            status_file: Path to status JSON file (default: workflow_state/phase_status.json)
        """
        if status_file is None:
            status_file = Path("workflow_state/phase_status.json")

        self.status_file = status_file
        self.status_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing status or initialize
        self.phases: Dict[str, PhaseStatus] = self._load_status()

        logger.info(f"✅ Phase Status Manager initialized")
        logger.info(f"📊 Status file: {self.status_file}")
        logger.info(f"📋 Tracking {len(self.phases)} phases")

    def _load_status(self) -> Dict[str, PhaseStatus]:
        """Load phase status from disk or initialize if not exists."""
        if self.status_file.exists():
            try:
                with open(self.status_file, "r") as f:
                    data = json.load(f)

                phases = {}
                for phase_id, phase_data in data.get("phases", {}).items():
                    phases[phase_id] = PhaseStatus(
                        phase_id=phase_data["phase_id"],
                        state=PhaseState(phase_data["state"]),
                        started_at=phase_data.get("started_at"),
                        completed_at=phase_data.get("completed_at"),
                        duration_seconds=phase_data.get("duration_seconds"),
                        error_message=phase_data.get("error_message"),
                        rerun_reason=phase_data.get("rerun_reason"),
                        metadata=phase_data.get("metadata"),
                        dependencies_met=phase_data.get("dependencies_met", True),
                        last_updated=phase_data.get("last_updated"),
                    )

                logger.info(f"📥 Loaded status for {len(phases)} phases from disk")
                return phases

            except Exception as e:
                logger.warning(f"⚠️  Failed to load status file: {e}")
                logger.info("🔄 Initializing fresh status")
                return self._initialize_fresh_status()
        else:
            logger.info("🆕 No existing status file, initializing fresh")
            return self._initialize_fresh_status()

    def _initialize_fresh_status(self) -> Dict[str, PhaseStatus]:
        """Initialize fresh status for all phases."""
        phases = {}
        for phase_id in self.ALL_PHASES:
            phases[phase_id] = PhaseStatus(
                phase_id=phase_id,
                state=PhaseState.PENDING,
                last_updated=datetime.now().isoformat(),
            )
        return phases

    def _save_status(self):
        """Persist current status to disk."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "phases": {
                    phase_id: asdict(status) for phase_id, status in self.phases.items()
                },
            }

            with open(self.status_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"💾 Status saved to {self.status_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save status: {e}")

    def start_phase(self, phase_id: str, metadata: Optional[Dict] = None):
        """
        Mark phase as started.

        Args:
            phase_id: Phase identifier
            metadata: Optional metadata to store
        """
        if phase_id not in self.phases:
            logger.warning(f"⚠️  Unknown phase: {phase_id}")
            self.phases[phase_id] = PhaseStatus(
                phase_id=phase_id,
                state=PhaseState.PENDING,
                last_updated=datetime.now().isoformat(),
            )

        status = self.phases[phase_id]

        # Check dependencies
        dependencies_met = self._check_dependencies(phase_id)

        if not dependencies_met:
            logger.warning(f"⚠️  Dependencies not met for {phase_id}")
            unmet = self._get_unmet_dependencies(phase_id)
            logger.warning(f"   Unmet: {', '.join(unmet)}")

        # Update status
        status.state = PhaseState.IN_PROGRESS
        status.started_at = datetime.now().isoformat()
        status.completed_at = None
        status.duration_seconds = None
        status.error_message = None
        status.dependencies_met = dependencies_met
        status.last_updated = datetime.now().isoformat()

        if metadata:
            status.metadata = metadata

        self._save_status()

        logger.info(f"🚀 Phase started: {phase_id}")
        if not dependencies_met:
            logger.warning(f"⚠️  Starting with unmet dependencies")

    def complete_phase(self, phase_id: str, metadata: Optional[Dict] = None):
        """
        Mark phase as completed successfully.

        Args:
            phase_id: Phase identifier
            metadata: Optional metadata to store (results, metrics, etc.)
        """
        if phase_id not in self.phases:
            logger.error(f"❌ Cannot complete unknown phase: {phase_id}")
            return

        status = self.phases[phase_id]

        # Calculate duration
        if status.started_at:
            started = datetime.fromisoformat(status.started_at)
            duration = (datetime.now() - started).total_seconds()
            status.duration_seconds = duration

        # Update status
        status.state = PhaseState.COMPLETE
        status.completed_at = datetime.now().isoformat()
        status.error_message = None
        status.last_updated = datetime.now().isoformat()

        if metadata:
            if status.metadata:
                status.metadata.update(metadata)
            else:
                status.metadata = metadata

        self._save_status()

        # Check if any downstream phases need rerun
        self._propagate_completion(phase_id)

        duration_str = (
            f"{status.duration_seconds:.1f}s" if status.duration_seconds else "unknown"
        )
        logger.info(f"✅ Phase completed: {phase_id} ({duration_str})")

    def fail_phase(
        self, phase_id: str, error_message: str, metadata: Optional[Dict] = None
    ):
        """
        Mark phase as failed.

        Args:
            phase_id: Phase identifier
            error_message: Error description
            metadata: Optional metadata to store
        """
        if phase_id not in self.phases:
            logger.error(f"❌ Cannot fail unknown phase: {phase_id}")
            return

        status = self.phases[phase_id]

        # Calculate duration
        if status.started_at:
            started = datetime.fromisoformat(status.started_at)
            duration = (datetime.now() - started).total_seconds()
            status.duration_seconds = duration

        # Update status
        status.state = PhaseState.FAILED
        status.completed_at = datetime.now().isoformat()
        status.error_message = error_message
        status.last_updated = datetime.now().isoformat()

        if metadata:
            if status.metadata:
                status.metadata.update(metadata)
            else:
                status.metadata = metadata

        self._save_status()

        logger.error(f"❌ Phase failed: {phase_id}")
        logger.error(f"   Error: {error_message}")

    def skip_phase(self, phase_id: str, reason: str, metadata: Optional[Dict] = None):
        """
        Skip a phase (mark it as not applicable for this run).

        Args:
            phase_id: Phase identifier
            reason: Reason for skipping
            metadata: Optional metadata to store
        """
        if phase_id not in self.phases:
            logger.error(f"❌ Cannot skip unknown phase: {phase_id}")
            return

        status = self.phases[phase_id]

        # Update status to PENDING with skip metadata
        status.state = PhaseState.PENDING
        status.skip_reason = reason
        status.last_updated = datetime.now().isoformat()

        if metadata:
            if status.metadata:
                status.metadata.update(metadata)
                status.metadata["skipped"] = True
            else:
                status.metadata = {"skipped": True, **metadata}
        else:
            if status.metadata:
                status.metadata["skipped"] = True
            else:
                status.metadata = {"skipped": True}

        self._save_status()

        logger.info(f"⏭️  Phase skipped: {phase_id}")
        logger.info(f"   Reason: {reason}")

    def mark_needs_rerun(self, phase_id: str, reason: str):
        """
        Mark phase as needing rerun due to upstream changes.

        Args:
            phase_id: Phase identifier
            reason: Reason for rerun
        """
        if phase_id not in self.phases:
            logger.error(f"❌ Cannot mark unknown phase for rerun: {phase_id}")
            return

        status = self.phases[phase_id]

        # Only mark COMPLETE phases for rerun
        if status.state != PhaseState.COMPLETE:
            logger.warning(f"⚠️  Cannot mark non-complete phase for rerun: {phase_id}")
            return

        status.state = PhaseState.NEEDS_RERUN
        status.rerun_reason = reason
        status.last_updated = datetime.now().isoformat()

        self._save_status()

        logger.info(f"🔄 Phase marked for rerun: {phase_id}")
        logger.info(f"   Reason: {reason}")

        # Propagate to downstream phases
        self._propagate_rerun(phase_id)

    def _check_dependencies(self, phase_id: str) -> bool:
        """Check if all dependencies for phase are met."""
        dependencies = self.DEPENDENCIES.get(phase_id, [])

        for dep in dependencies:
            if dep not in self.phases:
                return False

            dep_status = self.phases[dep]
            if dep_status.state not in [PhaseState.COMPLETE]:
                return False

        return True

    def _get_unmet_dependencies(self, phase_id: str) -> List[str]:
        """Get list of unmet dependencies for phase."""
        dependencies = self.DEPENDENCIES.get(phase_id, [])
        unmet = []

        for dep in dependencies:
            if dep not in self.phases:
                unmet.append(dep)
            elif self.phases[dep].state != PhaseState.COMPLETE:
                unmet.append(dep)

        return unmet

    def _propagate_completion(self, phase_id: str):
        """
        When a phase completes, check if any previously NEEDS_RERUN
        downstream phases can now be marked as dependencies met.
        """
        # This is mostly informational - we don't auto-transition
        # Just log that downstream phases might be ready
        pass

    def _propagate_rerun(self, phase_id: str):
        """
        When a phase is marked for rerun, propagate to all downstream phases.
        """
        # Find all phases that depend on this one
        downstream = []
        for phase, deps in self.DEPENDENCIES.items():
            if phase_id in deps:
                downstream.append(phase)

        # Recursively mark downstream phases for rerun
        for downstream_phase in downstream:
            if downstream_phase in self.phases:
                status = self.phases[downstream_phase]

                # Only mark COMPLETE phases (don't disturb IN_PROGRESS or FAILED)
                if status.state == PhaseState.COMPLETE:
                    reason = f"Upstream phase requires rerun: {phase_id}"
                    self.mark_needs_rerun(downstream_phase, reason)

    def get_status(self, phase_id: str) -> Optional[PhaseStatus]:
        """Get status for a specific phase."""
        return self.phases.get(phase_id)

    def get_all_status(self) -> Dict[str, PhaseStatus]:
        """Get status for all phases."""
        return self.phases.copy()

    def get_phase_summary(self) -> Dict[str, int]:
        """Get summary counts by state."""
        summary = {
            "PENDING": 0,
            "IN_PROGRESS": 0,
            "COMPLETE": 0,
            "FAILED": 0,
            "NEEDS_RERUN": 0,
        }

        for status in self.phases.values():
            summary[status.state.value] += 1

        return summary

    def get_phases_by_state(self, state: PhaseState) -> List[str]:
        """Get list of phase IDs in a given state."""
        return [
            phase_id
            for phase_id, status in self.phases.items()
            if status.state == state
        ]

    def reset_phase(self, phase_id: str):
        """Reset phase to PENDING state."""
        if phase_id not in self.phases:
            logger.error(f"❌ Cannot reset unknown phase: {phase_id}")
            return

        status = self.phases[phase_id]
        status.state = PhaseState.PENDING
        status.started_at = None
        status.completed_at = None
        status.duration_seconds = None
        status.error_message = None
        status.rerun_reason = None
        status.last_updated = datetime.now().isoformat()

        self._save_status()

        logger.info(f"🔄 Phase reset: {phase_id}")

    def reset_all_phases(self):
        """Reset all phases to PENDING state."""
        for phase_id in self.phases.keys():
            self.reset_phase(phase_id)

        logger.info("🔄 All phases reset to PENDING")

    def generate_report(self, output_file: Optional[Path] = None) -> str:
        """
        Generate comprehensive status report.

        Args:
            output_file: Optional file to write report to

        Returns:
            Report content as string
        """
        if output_file is None:
            output_file = Path("PHASE_STATUS_REPORT.md")

        report_lines = []

        # Header
        report_lines.append("# Workflow Phase Status Report")
        report_lines.append("")
        report_lines.append(
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Summary
        summary = self.get_phase_summary()
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append(f"- **Total Phases:** {len(self.phases)}")
        report_lines.append(f"- **Pending:** {summary['PENDING']}")
        report_lines.append(f"- **In Progress:** {summary['IN_PROGRESS']}")
        report_lines.append(f"- **Complete:** {summary['COMPLETE']}")
        report_lines.append(f"- **Failed:** {summary['FAILED']}")
        report_lines.append(f"- **Needs Rerun:** {summary['NEEDS_RERUN']}")
        report_lines.append("")

        # Progress bar
        total = len(self.phases)
        complete = summary["COMPLETE"]
        progress_pct = (complete / total * 100) if total > 0 else 0
        progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
        report_lines.append(f"**Progress:** [{progress_bar}] {progress_pct:.1f}%")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Detailed status by category
        for state in [
            PhaseState.IN_PROGRESS,
            PhaseState.FAILED,
            PhaseState.NEEDS_RERUN,
            PhaseState.COMPLETE,
            PhaseState.PENDING,
        ]:
            phases_in_state = self.get_phases_by_state(state)

            if not phases_in_state:
                continue

            # State emoji and title
            emoji = {
                PhaseState.PENDING: "⏳",
                PhaseState.IN_PROGRESS: "🔄",
                PhaseState.COMPLETE: "✅",
                PhaseState.FAILED: "❌",
                PhaseState.NEEDS_RERUN: "🔁",
            }.get(state, "📋")

            report_lines.append(f"## {emoji} {state.value} ({len(phases_in_state)})")
            report_lines.append("")

            for phase_id in phases_in_state:
                status = self.phases[phase_id]
                report_lines.append(f"### {phase_id}")
                report_lines.append("")

                if status.started_at:
                    report_lines.append(f"- **Started:** {status.started_at}")

                if status.completed_at:
                    report_lines.append(f"- **Completed:** {status.completed_at}")

                if status.duration_seconds:
                    mins = int(status.duration_seconds // 60)
                    secs = int(status.duration_seconds % 60)
                    report_lines.append(f"- **Duration:** {mins}m {secs}s")

                if status.error_message:
                    report_lines.append(f"- **Error:** {status.error_message}")

                if status.rerun_reason:
                    report_lines.append(f"- **Rerun Reason:** {status.rerun_reason}")

                if not status.dependencies_met:
                    unmet = self._get_unmet_dependencies(phase_id)
                    report_lines.append(f"- **Unmet Dependencies:** {', '.join(unmet)}")

                if status.metadata:
                    report_lines.append(f"- **Metadata:**")
                    for key, value in status.metadata.items():
                        report_lines.append(f"  - `{key}`: {value}")

                report_lines.append("")

        report_lines.append("---")
        report_lines.append("")
        report_lines.append("## Phase Dependencies")
        report_lines.append("")

        for phase_id in self.ALL_PHASES:
            deps = self.DEPENDENCIES.get(phase_id, [])
            if deps:
                report_lines.append(f"- **{phase_id}** → depends on: {', '.join(deps)}")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append(f"*Report generated by Phase Status Manager v1.0*")

        # Join and save
        report_content = "\n".join(report_lines)

        try:
            with open(output_file, "w") as f:
                f.write(report_content)

            logger.info(f"📊 Status report generated: {output_file}")
        except Exception as e:
            logger.error(f"❌ Failed to write report: {e}")

        return report_content


def main():
    """Demo/test the Phase Status Manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Phase Status Manager")
    parser.add_argument(
        "--reset", action="store_true", help="Reset all phases to PENDING"
    )
    parser.add_argument("--report", action="store_true", help="Generate status report")
    parser.add_argument("--start", type=str, help="Start a phase")
    parser.add_argument("--complete", type=str, help="Complete a phase")
    parser.add_argument("--fail", type=str, help="Fail a phase")
    parser.add_argument("--error", type=str, help="Error message for failure")
    parser.add_argument("--rerun", type=str, help="Mark phase for rerun")
    parser.add_argument("--reason", type=str, help="Reason for rerun")
    parser.add_argument("--status", type=str, help="Get status for specific phase")

    args = parser.parse_args()

    # Initialize manager
    manager = PhaseStatusManager()

    if args.reset:
        logger.info("🔄 Resetting all phases...")
        manager.reset_all_phases()
        logger.info("✅ All phases reset to PENDING")

    elif args.start:
        logger.info(f"🚀 Starting phase: {args.start}")
        manager.start_phase(args.start)

    elif args.complete:
        logger.info(f"✅ Completing phase: {args.complete}")
        manager.complete_phase(args.complete)

    elif args.fail:
        error_msg = args.error or "Unknown error"
        logger.info(f"❌ Failing phase: {args.fail}")
        manager.fail_phase(args.fail, error_msg)

    elif args.rerun:
        reason = args.reason or "Manual rerun requested"
        logger.info(f"🔁 Marking phase for rerun: {args.rerun}")
        manager.mark_needs_rerun(args.rerun, reason)

    elif args.status:
        status = manager.get_status(args.status)
        if status:
            logger.info(f"\n📊 Status for {args.status}:")
            logger.info(f"   State: {status.state.value}")
            logger.info(f"   Started: {status.started_at or 'N/A'}")
            logger.info(f"   Completed: {status.completed_at or 'N/A'}")
            logger.info(f"   Duration: {status.duration_seconds or 'N/A'}s")
            if status.error_message:
                logger.info(f"   Error: {status.error_message}")
            if status.rerun_reason:
                logger.info(f"   Rerun Reason: {status.rerun_reason}")
        else:
            logger.error(f"❌ Unknown phase: {args.status}")

    if args.report or not any(
        [args.reset, args.start, args.complete, args.fail, args.rerun, args.status]
    ):
        # Generate report by default or if --report specified
        logger.info("📊 Generating status report...")
        report = manager.generate_report()
        logger.info(f"\n{report}")


if __name__ == "__main__":
    main()
