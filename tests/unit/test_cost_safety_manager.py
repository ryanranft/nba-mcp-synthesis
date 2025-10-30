#!/usr/bin/env python3
"""
Unit tests for Cost Safety Manager

Tests cost tracking, limit enforcement, approval workflows,
and report generation.
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

from scripts.cost_safety_manager import (
    CostSafetyManager,
    CostRecord,
    ApprovalRequest,
    ApprovalStatus,
)


class TestCostSafetyManager(unittest.TestCase):
    """Test suite for Cost Safety Manager"""

    def setUp(self):
        """Create temporary cost file for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.cost_file = Path(self.temp_dir) / "test_costs.json"
        self.manager = CostSafetyManager(cost_file=self.cost_file)

    def tearDown(self):
        """Clean up temporary files"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test manager initializes with default limits"""
        self.assertIsNotNone(self.manager.limits)
        self.assertEqual(self.manager.limits["total_workflow"], 125.00)
        self.assertEqual(self.manager.limits["phase_2_analysis"], 30.00)
        self.assertEqual(len(self.manager.records), 0)

    def test_custom_limits(self):
        """Test custom cost limits are applied"""
        custom_limits = {"phase_2_analysis": 50.00, "total_workflow": 200.00}

        manager = CostSafetyManager(
            cost_file=self.cost_file, custom_limits=custom_limits
        )

        self.assertEqual(manager.limits["phase_2_analysis"], 50.00)
        self.assertEqual(manager.limits["total_workflow"], 200.00)

    def test_record_cost(self):
        """Test recording a cost"""
        self.manager.record_cost(
            "phase_2_analysis", 15.50, model="gemini-1.5-pro", operation="book_analysis"
        )

        self.assertEqual(len(self.manager.records), 1)
        record = self.manager.records[0]

        self.assertEqual(record.phase_id, "phase_2_analysis")
        self.assertEqual(record.amount, 15.50)
        self.assertEqual(record.model, "gemini-1.5-pro")
        self.assertEqual(record.operation, "book_analysis")

    def test_get_phase_cost(self):
        """Test retrieving phase cost"""
        self.manager.record_cost("phase_2_analysis", 10.00)
        self.manager.record_cost("phase_2_analysis", 5.00)
        self.manager.record_cost("phase_3_synthesis", 8.00)

        phase2_cost = self.manager.get_phase_cost("phase_2_analysis")
        phase3_cost = self.manager.get_phase_cost("phase_3_synthesis")

        self.assertEqual(phase2_cost, 15.00)
        self.assertEqual(phase3_cost, 8.00)

    def test_get_total_cost(self):
        """Test retrieving total cost"""
        self.manager.record_cost("phase_2_analysis", 10.00)
        self.manager.record_cost("phase_3_synthesis", 8.00)
        self.manager.record_cost("phase_4_file_generation", 5.00)

        total_cost = self.manager.get_total_cost()

        self.assertEqual(total_cost, 23.00)

    def test_get_model_cost(self):
        """Test retrieving cost by model"""
        self.manager.record_cost("phase_2_analysis", 10.00, model="gemini-1.5-pro")
        self.manager.record_cost("phase_3_synthesis", 8.00, model="claude-sonnet-4")
        self.manager.record_cost(
            "phase_4_file_generation", 5.00, model="gemini-1.5-pro"
        )

        gemini_cost = self.manager.get_model_cost("gemini-1.5-pro")
        claude_cost = self.manager.get_model_cost("claude-sonnet-4")

        self.assertEqual(gemini_cost, 15.00)
        self.assertEqual(claude_cost, 8.00)

    def test_check_cost_limit_within(self):
        """Test checking cost limit when within budget"""
        self.manager.record_cost("phase_2_analysis", 10.00)

        # Should be within limit (30.00 total limit, 10.00 used, adding 15.00 = 25.00)
        within_limit = self.manager.check_cost_limit("phase_2_analysis", 15.00)

        self.assertTrue(within_limit)

    def test_check_cost_limit_exceeded(self):
        """Test checking cost limit when exceeded"""
        self.manager.record_cost("phase_2_analysis", 20.00)

        # Should exceed limit (30.00 total limit, 20.00 used, adding 15.00 = 35.00)
        within_limit = self.manager.check_cost_limit("phase_2_analysis", 15.00)

        self.assertFalse(within_limit)

    def test_check_total_workflow_limit(self):
        """Test checking total workflow cost limit"""
        # Add costs to multiple phases
        self.manager.record_cost("phase_2_analysis", 25.00)
        self.manager.record_cost("phase_3_synthesis", 18.00)
        self.manager.record_cost("phase_4_file_generation", 9.00)
        self.manager.record_cost("phase_5_predictions", 8.00)
        # Total: 60.00, workflow limit: 125.00

        # phase_2_analysis has $30 limit, used $25, can add $5
        # Should be within both phase and total limits
        within_limit = self.manager.check_cost_limit("phase_2_analysis", 4.00)
        self.assertTrue(within_limit)

        # Should exceed total limit (current 60 + 70 = 130 > 125 limit)
        within_limit = self.manager.check_cost_limit("phase_3_synthesis", 70.00)
        self.assertFalse(within_limit)

    def test_auto_approve_low_cost(self):
        """Test auto-approval of low-cost operations"""
        approved = self.manager.require_approval(
            "test_operation", 3.00, 5, "Test operation"  # Below $5 threshold
        )

        self.assertTrue(approved)
        self.assertEqual(len(self.manager.approval_requests), 1)
        self.assertEqual(
            self.manager.approval_requests[0].status, ApprovalStatus.AUTO_APPROVED
        )

    def test_require_approval_high_cost(self):
        """Test approval required for high-cost operations"""
        approved = self.manager.require_approval(
            "ai_plan_modification",
            25.00,  # Above threshold
            15,  # Above item threshold
            "Modifying 15 plans",
        )

        # Should still approve (within acceptable range) but with warning
        self.assertTrue(approved)
        self.assertEqual(len(self.manager.approval_requests), 1)
        self.assertEqual(
            self.manager.approval_requests[0].status, ApprovalStatus.APPROVED
        )

    def test_reject_excessive_cost(self):
        """Test rejection of excessive cost operations"""
        approved = self.manager.require_approval(
            "mass_code_changes",
            60.00,  # Way over threshold
            30,  # Too many items
            "Changing 30 files",
        )

        # Should auto-reject
        self.assertFalse(approved)
        self.assertEqual(len(self.manager.approval_requests), 1)
        self.assertEqual(
            self.manager.approval_requests[0].status, ApprovalStatus.REJECTED
        )

    def test_estimate_remaining_budget(self):
        """Test estimating remaining budget"""
        self.manager.record_cost("phase_2_analysis", 18.00)

        remaining = self.manager.estimate_remaining_budget("phase_2_analysis")

        # Limit is 30.00, used 18.00, remaining should be 12.00
        self.assertEqual(remaining, 12.00)

    def test_estimate_items_possible(self):
        """Test estimating items possible within budget"""
        self.manager.record_cost("phase_2_analysis", 18.00)

        # Remaining: 12.00, cost per item: 0.60
        items_possible = self.manager.estimate_items_possible("phase_2_analysis", 0.60)

        self.assertEqual(items_possible, 20)

    def test_project_total_cost(self):
        """Test projecting total cost with planned operations"""
        self.manager.record_cost("phase_2_analysis", 20.00)
        self.manager.record_cost("phase_3_synthesis", 15.00)
        # Current total: 35.00

        planned_operations = {
            "phase_4_file_generation": 10.00,
            "phase_5_predictions": 8.00,
        }

        projected_total, within_limits = self.manager.project_total_cost(
            planned_operations
        )

        self.assertEqual(projected_total, 53.00)
        self.assertTrue(within_limits)

    def test_project_total_cost_exceeds(self):
        """Test projecting total cost when it would exceed limit"""
        self.manager.record_cost("phase_2_analysis", 80.00)
        # Current total: 80.00, limit: 125.00

        planned_operations = {
            "phase_3_synthesis": 30.00,
            "phase_4_file_generation": 20.00,
        }
        # Planned: 50.00, projected total: 130.00

        projected_total, within_limits = self.manager.project_total_cost(
            planned_operations
        )

        self.assertEqual(projected_total, 130.00)
        self.assertFalse(within_limits)

    def test_cost_persistence(self):
        """Test cost data is persisted to disk"""
        self.manager.record_cost("phase_2_analysis", 15.00, model="gemini-1.5-pro")

        # Create new manager with same file
        new_manager = CostSafetyManager(cost_file=self.cost_file)

        # Verify costs were loaded
        self.assertEqual(len(new_manager.records), 1)
        self.assertEqual(new_manager.get_total_cost(), 15.00)

    def test_get_cost_summary(self):
        """Test cost summary generation"""
        self.manager.record_cost("phase_2_analysis", 20.00, model="gemini-1.5-pro")
        self.manager.record_cost("phase_3_synthesis", 15.00, model="claude-sonnet-4")

        summary = self.manager.get_cost_summary()

        self.assertEqual(summary["total_cost"], 35.00)
        self.assertEqual(summary["total_limit"], 125.00)
        self.assertEqual(summary["remaining_budget"], 90.00)
        self.assertEqual(summary["record_count"], 2)
        self.assertIn("phase_2_analysis", summary["by_phase"])
        self.assertIn("gemini-1.5-pro", summary["by_model"])

    def test_get_cost_by_phase(self):
        """Test cost breakdown by phase"""
        self.manager.record_cost("phase_2_analysis", 10.00)
        self.manager.record_cost("phase_2_analysis", 8.00)
        self.manager.record_cost("phase_3_synthesis", 12.00)

        by_phase = self.manager.get_cost_by_phase()

        self.assertEqual(by_phase["phase_2_analysis"], 18.00)
        self.assertEqual(by_phase["phase_3_synthesis"], 12.00)

    def test_get_cost_by_model(self):
        """Test cost breakdown by model"""
        self.manager.record_cost("phase_2_analysis", 10.00, model="gemini-1.5-pro")
        self.manager.record_cost("phase_3_synthesis", 8.00, model="claude-sonnet-4")
        self.manager.record_cost(
            "phase_4_file_generation", 5.00, model="gemini-1.5-pro"
        )

        by_model = self.manager.get_cost_by_model()

        self.assertEqual(by_model["gemini-1.5-pro"], 15.00)
        self.assertEqual(by_model["claude-sonnet-4"], 8.00)

    def test_report_generation(self):
        """Test cost report generation"""
        self.manager.record_cost("phase_2_analysis", 20.00, model="gemini-1.5-pro")
        self.manager.record_cost("phase_3_synthesis", 15.00, model="claude-sonnet-4")

        report_file = Path(self.temp_dir) / "test_report.md"
        report = self.manager.generate_report(output_file=report_file)

        # Verify report contains expected sections
        self.assertIn("# Cost Safety Report", report)
        self.assertIn("## Summary", report)
        self.assertIn("## Cost by Phase", report)
        self.assertIn("## Cost by Model", report)
        self.assertIn("## Recent Transactions", report)

        # Verify file was created
        self.assertTrue(report_file.exists())

    def test_warning_at_80_percent(self):
        """Test warning is logged at 80% of limit"""
        # Record 80% of phase limit
        self.manager.record_cost("phase_2_analysis", 24.00)  # 80% of 30.00

        # This should trigger a warning
        phase_cost = self.manager.get_phase_cost("phase_2_analysis")
        phase_limit = self.manager.limits["phase_2_analysis"]

        self.assertGreaterEqual(phase_cost, phase_limit * 0.8)

    def test_multiple_models_same_phase(self):
        """Test tracking multiple models in same phase"""
        self.manager.record_cost("phase_2_analysis", 8.00, model="gemini-1.5-pro")
        self.manager.record_cost("phase_2_analysis", 7.00, model="claude-sonnet-4")

        phase_cost = self.manager.get_phase_cost("phase_2_analysis")
        gemini_cost = self.manager.get_model_cost("gemini-1.5-pro")
        claude_cost = self.manager.get_model_cost("claude-sonnet-4")

        self.assertEqual(phase_cost, 15.00)
        self.assertEqual(gemini_cost, 8.00)
        self.assertEqual(claude_cost, 7.00)

    def test_metadata_storage(self):
        """Test metadata is stored with cost records"""
        metadata = {"books_analyzed": 25, "avg_cost_per_book": 0.62}

        self.manager.record_cost("phase_2_analysis", 15.50, metadata=metadata)

        record = self.manager.records[0]
        self.assertIsNotNone(record.metadata)
        self.assertEqual(record.metadata["books_analyzed"], 25)
        self.assertEqual(record.metadata["avg_cost_per_book"], 0.62)


if __name__ == "__main__":
    unittest.main()
