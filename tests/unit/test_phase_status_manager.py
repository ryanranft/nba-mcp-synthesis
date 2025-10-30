#!/usr/bin/env python3
"""
Unit tests for Phase Status Manager

Tests phase state transitions, dependency tracking, rerun propagation,
and status persistence.
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from scripts.phase_status_manager import PhaseStatusManager, PhaseState, PhaseStatus


class TestPhaseStatusManager(unittest.TestCase):
    """Test suite for Phase Status Manager"""

    def setUp(self):
        """Create temporary status file for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.status_file = Path(self.temp_dir) / "test_status.json"
        self.manager = PhaseStatusManager(status_file=self.status_file)

    def tearDown(self):
        """Clean up temporary files"""
        import shutil

        # Remove entire temp directory including any files created
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test manager initializes with all phases in PENDING state"""
        self.assertEqual(len(self.manager.phases), 16)

        for phase_id, status in self.manager.phases.items():
            self.assertEqual(status.state, PhaseState.PENDING)
            self.assertIsNone(status.started_at)
            self.assertIsNone(status.completed_at)

    def test_start_phase(self):
        """Test starting a phase transitions to IN_PROGRESS"""
        phase_id = "phase_0_foundation"
        self.manager.start_phase(phase_id)

        status = self.manager.get_status(phase_id)
        self.assertEqual(status.state, PhaseState.IN_PROGRESS)
        self.assertIsNotNone(status.started_at)
        self.assertIsNone(status.completed_at)

    def test_complete_phase(self):
        """Test completing a phase transitions to COMPLETE"""
        phase_id = "phase_0_foundation"

        # Start then complete
        self.manager.start_phase(phase_id)
        self.manager.complete_phase(phase_id, metadata={"test": "data"})

        status = self.manager.get_status(phase_id)
        self.assertEqual(status.state, PhaseState.COMPLETE)
        self.assertIsNotNone(status.started_at)
        self.assertIsNotNone(status.completed_at)
        self.assertIsNotNone(status.duration_seconds)
        self.assertEqual(status.metadata["test"], "data")

    def test_fail_phase(self):
        """Test failing a phase transitions to FAILED"""
        phase_id = "phase_0_foundation"
        error_msg = "Test error message"

        # Start then fail
        self.manager.start_phase(phase_id)
        self.manager.fail_phase(phase_id, error_msg)

        status = self.manager.get_status(phase_id)
        self.assertEqual(status.state, PhaseState.FAILED)
        self.assertEqual(status.error_message, error_msg)
        self.assertIsNotNone(status.completed_at)
        self.assertIsNotNone(status.duration_seconds)

    def test_mark_needs_rerun(self):
        """Test marking a complete phase for rerun"""
        phase_id = "phase_0_foundation"
        reason = "Test rerun reason"

        # Complete phase first
        self.manager.start_phase(phase_id)
        self.manager.complete_phase(phase_id)

        # Mark for rerun
        self.manager.mark_needs_rerun(phase_id, reason)

        status = self.manager.get_status(phase_id)
        self.assertEqual(status.state, PhaseState.NEEDS_RERUN)
        self.assertEqual(status.rerun_reason, reason)

    def test_rerun_propagation(self):
        """Test that marking a phase for rerun propagates to downstream phases"""
        # Complete phase_2_analysis and phase_3_synthesis
        self.manager.start_phase("phase_2_analysis")
        self.manager.complete_phase("phase_2_analysis")

        self.manager.start_phase("phase_3_synthesis")
        self.manager.complete_phase("phase_3_synthesis")

        # Mark phase_2 for rerun
        self.manager.mark_needs_rerun("phase_2_analysis", "Test propagation")

        # Verify phase_3 is also marked for rerun
        phase2_status = self.manager.get_status("phase_2_analysis")
        phase3_status = self.manager.get_status("phase_3_synthesis")

        self.assertEqual(phase2_status.state, PhaseState.NEEDS_RERUN)
        self.assertEqual(phase3_status.state, PhaseState.NEEDS_RERUN)
        self.assertIn("phase_2_analysis", phase3_status.rerun_reason)

    def test_dependency_checking(self):
        """Test dependency checking works correctly"""
        # phase_2_analysis depends on phase_0_foundation
        # Should not start with unmet dependencies

        # Try to start phase_2 without completing phase_0
        self.manager.start_phase("phase_2_analysis")
        status = self.manager.get_status("phase_2_analysis")

        # Should still start but with dependencies_met = False
        self.assertEqual(status.state, PhaseState.IN_PROGRESS)
        self.assertFalse(status.dependencies_met)

    def test_status_persistence(self):
        """Test status is persisted to disk and can be loaded"""
        phase_id = "phase_0_foundation"

        # Complete a phase
        self.manager.start_phase(phase_id)
        self.manager.complete_phase(phase_id, metadata={"test": "data"})

        # Create new manager with same status file
        new_manager = PhaseStatusManager(status_file=self.status_file)

        # Verify status was loaded correctly
        status = new_manager.get_status(phase_id)
        self.assertEqual(status.state, PhaseState.COMPLETE)
        self.assertEqual(status.metadata["test"], "data")

    def test_phase_summary(self):
        """Test phase summary counts are correct"""
        # Complete one phase
        self.manager.start_phase("phase_0_foundation")
        self.manager.complete_phase("phase_0_foundation")

        # Fail one phase
        self.manager.start_phase("phase_1_data_inventory")
        self.manager.fail_phase("phase_1_data_inventory", "Test error")

        summary = self.manager.get_phase_summary()

        self.assertEqual(summary["COMPLETE"], 1)
        self.assertEqual(summary["FAILED"], 1)
        self.assertEqual(summary["PENDING"], 14)
        self.assertEqual(summary["IN_PROGRESS"], 0)
        self.assertEqual(summary["NEEDS_RERUN"], 0)

    def test_get_phases_by_state(self):
        """Test filtering phases by state"""
        # Complete two phases
        self.manager.start_phase("phase_0_foundation")
        self.manager.complete_phase("phase_0_foundation")

        self.manager.start_phase("phase_2_analysis")
        self.manager.complete_phase("phase_2_analysis")

        complete_phases = self.manager.get_phases_by_state(PhaseState.COMPLETE)

        self.assertEqual(len(complete_phases), 2)
        self.assertIn("phase_0_foundation", complete_phases)
        self.assertIn("phase_2_analysis", complete_phases)

    def test_reset_phase(self):
        """Test resetting a phase to PENDING"""
        phase_id = "phase_0_foundation"

        # Complete a phase
        self.manager.start_phase(phase_id)
        self.manager.complete_phase(phase_id)

        # Reset it
        self.manager.reset_phase(phase_id)

        status = self.manager.get_status(phase_id)
        self.assertEqual(status.state, PhaseState.PENDING)
        self.assertIsNone(status.started_at)
        self.assertIsNone(status.completed_at)

    def test_reset_all_phases(self):
        """Test resetting all phases to PENDING"""
        # Complete a few phases
        self.manager.start_phase("phase_0_foundation")
        self.manager.complete_phase("phase_0_foundation")

        self.manager.start_phase("phase_2_analysis")
        self.manager.complete_phase("phase_2_analysis")

        # Reset all
        self.manager.reset_all_phases()

        # Verify all are PENDING
        for phase_id, status in self.manager.phases.items():
            self.assertEqual(status.state, PhaseState.PENDING)

    def test_report_generation(self):
        """Test status report generation"""
        # Complete a phase
        self.manager.start_phase("phase_0_foundation")
        self.manager.complete_phase("phase_0_foundation")

        # Generate report
        report_file = Path(self.temp_dir) / "test_report.md"
        report = self.manager.generate_report(output_file=report_file)

        # Verify report contains expected sections
        self.assertIn("# Workflow Phase Status Report", report)
        self.assertIn("## Summary", report)
        self.assertIn("## ✅ COMPLETE", report)
        self.assertIn("## ⏳ PENDING", report)
        self.assertIn("## Phase Dependencies", report)

        # Verify file was created
        self.assertTrue(report_file.exists())

    def test_metadata_update(self):
        """Test metadata is properly updated across operations"""
        phase_id = "phase_0_foundation"

        # Start with metadata
        self.manager.start_phase(phase_id, metadata={"key1": "value1"})

        # Complete with additional metadata
        self.manager.complete_phase(phase_id, metadata={"key2": "value2"})

        status = self.manager.get_status(phase_id)
        self.assertEqual(status.metadata["key1"], "value1")
        self.assertEqual(status.metadata["key2"], "value2")

    def test_complex_dependency_chain(self):
        """Test complex dependency chain with multiple levels"""
        # Complete foundation
        self.manager.start_phase("phase_0_foundation")
        self.manager.complete_phase("phase_0_foundation")

        # Complete analysis
        self.manager.start_phase("phase_2_analysis")
        self.manager.complete_phase("phase_2_analysis")

        # Complete synthesis
        self.manager.start_phase("phase_3_synthesis")
        self.manager.complete_phase("phase_3_synthesis")

        # Complete modifications
        self.manager.start_phase("phase_3.5_modifications")
        self.manager.complete_phase("phase_3.5_modifications")

        # Complete file generation
        self.manager.start_phase("phase_4_file_generation")
        self.manager.complete_phase("phase_4_file_generation")

        # Mark analysis for rerun
        self.manager.mark_needs_rerun("phase_2_analysis", "Test cascade")

        # Verify cascade: 2 → 3 → 3.5 (not 4, it also depends on 3.5)
        phase2 = self.manager.get_status("phase_2_analysis")
        phase3 = self.manager.get_status("phase_3_synthesis")
        phase35 = self.manager.get_status("phase_3.5_modifications")

        self.assertEqual(phase2.state, PhaseState.NEEDS_RERUN)
        self.assertEqual(phase3.state, PhaseState.NEEDS_RERUN)
        self.assertEqual(phase35.state, PhaseState.NEEDS_RERUN)


if __name__ == "__main__":
    unittest.main()
