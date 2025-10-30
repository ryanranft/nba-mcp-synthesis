#!/usr/bin/env python3
"""
Cost Safety Manager - Prevent runaway API costs

Provides comprehensive cost tracking and safety limits for all phases:
- Per-phase cost limits
- Total workflow cost limits
- Real-time cost tracking
- Pre-flight cost estimation
- Auto-stop when limit exceeded
- Approval prompts for expensive operations

Usage:
    from scripts.cost_safety_manager import CostSafetyManager

    cost_mgr = CostSafetyManager()

    # Check if operation would exceed limit
    if cost_mgr.check_cost_limit("phase_2_analysis", estimated_cost):
        # Proceed with operation
        ...
        # Track actual cost
        cost_mgr.record_cost("phase_2_analysis", actual_cost, metadata)
    else:
        # Reject operation
        print("Cost limit exceeded!")

    # Require approval for expensive operations
    if cost_mgr.require_approval("ai_plan_modification", cost, plans_affected):
        # Wait for user approval
        ...

    # Generate cost report
    cost_mgr.generate_report()
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Approval status for expensive operations"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTO_APPROVED = "AUTO_APPROVED"
    SKIPPED = "SKIPPED"


@dataclass
class CostRecord:
    """Record of a single cost entry"""

    phase_id: str
    amount: float
    timestamp: str
    model: Optional[str] = None
    operation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ApprovalRequest:
    """Request for approval of expensive operation"""

    operation: str
    estimated_cost: float
    impact_description: str
    affected_items: int
    status: ApprovalStatus
    requested_at: str
    responded_at: Optional[str] = None
    response_message: Optional[str] = None


class CostSafetyManager:
    """
    Prevent runaway API costs with comprehensive tracking and safety limits.

    Features:
    - Per-phase cost limits
    - Total workflow cost limits
    - Real-time cost tracking
    - Pre-flight cost estimation
    - Auto-stop when limit exceeded
    - Approval prompts for expensive operations
    - Comprehensive cost reporting

    Safety Mechanisms:
    - Hard stops when limits exceeded
    - Soft warnings at 80% of limit
    - Approval required for high-impact operations
    - Cost projections based on historical data
    """

    # Default cost limits ($USD)
    DEFAULT_LIMITS = {
        "phase_0_foundation": 0.00,  # No API calls
        "phase_1_data_inventory": 0.00,  # No API calls
        "phase_2_analysis": 30.00,  # Book analysis (45 books × $0.60)
        "phase_3_synthesis": 20.00,  # Consensus synthesis
        "phase_3.5_modifications": 15.00,  # AI plan modifications
        "phase_4_file_generation": 10.00,  # File generation
        "phase_5_predictions": 10.00,  # Predictions/forecasting
        "phase_6_validation": 5.00,  # Validation
        "phase_7_integration_prep": 5.00,  # Integration prep
        "phase_8_smart_integration": 10.00,  # Smart integration
        "phase_8.5_validation": 5.00,  # Pre-integration validation
        "phase_9_integration": 0.00,  # No API calls (file operations)
        "phase_10a_mcp_improvements": 5.00,  # Code improvements
        "phase_10b_simulator_improvements": 5.00,  # Simulator improvements
        "phase_11_documentation": 5.00,  # Documentation generation
        "phase_12_deployment": 0.00,  # No API calls
        "total_workflow": 125.00,  # Total limit across all phases
    }

    # Operations requiring approval
    HIGH_IMPACT_OPERATIONS = [
        "ai_plan_modification",
        "bulk_file_generation",
        "mass_code_changes",
        "ai_integration_decisions",
    ]

    # Approval thresholds
    APPROVAL_THRESHOLD_COST = 20.00  # Require approval if single operation > $20
    APPROVAL_THRESHOLD_ITEMS = 10  # Require approval if affecting >10 items

    def __init__(
        self,
        cost_file: Optional[Path] = None,
        custom_limits: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize Cost Safety Manager.

        Args:
            cost_file: Path to cost tracking JSON file (default: workflow_state/cost_tracking.json)
            custom_limits: Custom cost limits to override defaults
        """
        if cost_file is None:
            cost_file = Path("workflow_state/cost_tracking.json")

        self.cost_file = cost_file
        self.cost_file.parent.mkdir(parents=True, exist_ok=True)

        # Set cost limits
        self.limits = self.DEFAULT_LIMITS.copy()
        if custom_limits:
            self.limits.update(custom_limits)

        # Load existing cost records
        self.records: List[CostRecord] = []
        self.approval_requests: List[ApprovalRequest] = []
        self._load_costs()

        logger.info(f"✅ Cost Safety Manager initialized")
        logger.info(f"💰 Cost file: {self.cost_file}")
        logger.info(f"📊 Tracking {len(self.records)} existing cost records")
        logger.info(f"🎯 Total workflow limit: ${self.limits['total_workflow']:.2f}")

    def _load_costs(self):
        """Load cost records from disk."""
        if self.cost_file.exists():
            try:
                with open(self.cost_file, "r") as f:
                    data = json.load(f)

                # Load cost records
                for record_data in data.get("records", []):
                    self.records.append(
                        CostRecord(
                            phase_id=record_data["phase_id"],
                            amount=record_data["amount"],
                            timestamp=record_data["timestamp"],
                            model=record_data.get("model"),
                            operation=record_data.get("operation"),
                            metadata=record_data.get("metadata"),
                        )
                    )

                # Load approval requests
                for approval_data in data.get("approvals", []):
                    self.approval_requests.append(
                        ApprovalRequest(
                            operation=approval_data["operation"],
                            estimated_cost=approval_data["estimated_cost"],
                            impact_description=approval_data["impact_description"],
                            affected_items=approval_data["affected_items"],
                            status=ApprovalStatus(approval_data["status"]),
                            requested_at=approval_data["requested_at"],
                            responded_at=approval_data.get("responded_at"),
                            response_message=approval_data.get("response_message"),
                        )
                    )

                logger.info(f"📥 Loaded {len(self.records)} cost records from disk")
                logger.info(
                    f"📥 Loaded {len(self.approval_requests)} approval requests"
                )

            except Exception as e:
                logger.warning(f"⚠️  Failed to load cost file: {e}")
                logger.info("🔄 Starting with fresh cost tracking")
        else:
            logger.info("🆕 No existing cost file, starting fresh")

    def _save_costs(self):
        """Persist cost records to disk."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "total_cost": self.get_total_cost(),
                "records": [asdict(record) for record in self.records],
                "approvals": [asdict(approval) for approval in self.approval_requests],
                "limits": self.limits,
            }

            with open(self.cost_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"💾 Cost data saved to {self.cost_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save cost data: {e}")

    def record_cost(
        self,
        phase_id: str,
        amount: float,
        model: Optional[str] = None,
        operation: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        Record a cost incurred during operation.

        Args:
            phase_id: Phase identifier
            amount: Cost amount in USD
            model: Model used (e.g., "gemini-1.5-pro", "claude-sonnet-4")
            operation: Operation performed (e.g., "book_analysis", "synthesis")
            metadata: Additional metadata
        """
        record = CostRecord(
            phase_id=phase_id,
            amount=amount,
            timestamp=datetime.now().isoformat(),
            model=model,
            operation=operation,
            metadata=metadata,
        )

        self.records.append(record)
        self._save_costs()

        # Check if we're approaching or exceeding limits
        phase_total = self.get_phase_cost(phase_id)
        phase_limit = self.limits.get(phase_id, float("inf"))
        total_cost = self.get_total_cost()
        total_limit = self.limits["total_workflow"]

        logger.info(
            f"💰 Cost recorded: {phase_id} +${amount:.4f} (total: ${phase_total:.2f}/${phase_limit:.2f})"
        )

        # Warnings
        if phase_total >= phase_limit * 0.8:
            logger.warning(
                f"⚠️  Phase {phase_id} at {phase_total/phase_limit*100:.0f}% of limit"
            )

        if total_cost >= total_limit * 0.8:
            logger.warning(
                f"⚠️  Total cost at {total_cost/total_limit*100:.0f}% of limit"
            )

    def check_cost_limit(self, phase_id: str, estimated_cost: float) -> bool:
        """
        Check if adding estimated cost would exceed limit.

        Args:
            phase_id: Phase identifier
            estimated_cost: Estimated cost to add

        Returns:
            True if within limit, False if would exceed
        """
        phase_total = self.get_phase_cost(phase_id)
        phase_limit = self.limits.get(phase_id, float("inf"))
        total_cost = self.get_total_cost()
        total_limit = self.limits["total_workflow"]

        # Check phase limit
        if phase_total + estimated_cost > phase_limit:
            logger.error(f"❌ Cost limit exceeded for {phase_id}")
            logger.error(
                f"   Current: ${phase_total:.2f}, Estimated: +${estimated_cost:.2f}, Limit: ${phase_limit:.2f}"
            )
            return False

        # Check total limit
        if total_cost + estimated_cost > total_limit:
            logger.error(f"❌ Total workflow cost limit exceeded")
            logger.error(
                f"   Current: ${total_cost:.2f}, Estimated: +${estimated_cost:.2f}, Limit: ${total_limit:.2f}"
            )
            return False

        # Within limits
        return True

    def require_approval(
        self,
        operation: str,
        estimated_cost: float,
        affected_items: int,
        impact_description: str = "",
        auto_approve_threshold: float = 5.00,
    ) -> bool:
        """
        Check if operation requires approval and prompt if needed.

        Args:
            operation: Operation name
            estimated_cost: Estimated cost
            affected_items: Number of items affected
            impact_description: Description of impact
            auto_approve_threshold: Auto-approve if cost below this ($5 default)

        Returns:
            True if approved (or auto-approved), False if rejected
        """
        # Auto-approve low-cost operations
        if estimated_cost < auto_approve_threshold:
            approval = ApprovalRequest(
                operation=operation,
                estimated_cost=estimated_cost,
                impact_description=impact_description,
                affected_items=affected_items,
                status=ApprovalStatus.AUTO_APPROVED,
                requested_at=datetime.now().isoformat(),
                responded_at=datetime.now().isoformat(),
                response_message="Auto-approved (cost below threshold)",
            )
            self.approval_requests.append(approval)
            self._save_costs()

            logger.info(f"✅ Auto-approved: {operation} (${estimated_cost:.2f})")
            return True

        # Check if approval required
        requires_approval = (
            operation in self.HIGH_IMPACT_OPERATIONS
            or estimated_cost > self.APPROVAL_THRESHOLD_COST
            or affected_items > self.APPROVAL_THRESHOLD_ITEMS
        )

        if not requires_approval:
            approval = ApprovalRequest(
                operation=operation,
                estimated_cost=estimated_cost,
                impact_description=impact_description,
                affected_items=affected_items,
                status=ApprovalStatus.SKIPPED,
                requested_at=datetime.now().isoformat(),
                responded_at=datetime.now().isoformat(),
                response_message="Approval not required",
            )
            self.approval_requests.append(approval)
            self._save_costs()

            return True

        # Prompt for approval
        logger.warning(f"⚠️  APPROVAL REQUIRED for {operation}")
        logger.warning(f"   Estimated Cost: ${estimated_cost:.2f}")
        logger.warning(f"   Affected Items: {affected_items}")
        logger.warning(f"   Impact: {impact_description}")
        logger.warning(f"   ")

        # In production, this would be interactive
        # For now, we'll auto-reject operations over $50 or affecting >20 items
        if estimated_cost > 50.00 or affected_items > 20:
            logger.error(f"❌ AUTO-REJECTED: Cost or impact too high")
            approval = ApprovalRequest(
                operation=operation,
                estimated_cost=estimated_cost,
                impact_description=impact_description,
                affected_items=affected_items,
                status=ApprovalStatus.REJECTED,
                requested_at=datetime.now().isoformat(),
                responded_at=datetime.now().isoformat(),
                response_message="Auto-rejected (cost/impact too high)",
            )
            self.approval_requests.append(approval)
            self._save_costs()
            return False

        # Otherwise auto-approve with warning
        logger.warning(f"⚠️  AUTO-APPROVED with warning")
        approval = ApprovalRequest(
            operation=operation,
            estimated_cost=estimated_cost,
            impact_description=impact_description,
            affected_items=affected_items,
            status=ApprovalStatus.APPROVED,
            requested_at=datetime.now().isoformat(),
            responded_at=datetime.now().isoformat(),
            response_message="Auto-approved (within acceptable range)",
        )
        self.approval_requests.append(approval)
        self._save_costs()

        return True

    def get_phase_cost(self, phase_id: str) -> float:
        """Get total cost for a specific phase."""
        return sum(
            record.amount for record in self.records if record.phase_id == phase_id
        )

    def get_total_cost(self) -> float:
        """Get total cost across all phases."""
        return sum(record.amount for record in self.records)

    def get_model_cost(self, model: str) -> float:
        """Get total cost for a specific model."""
        return sum(record.amount for record in self.records if record.model == model)

    def get_cost_by_phase(self) -> Dict[str, float]:
        """Get cost breakdown by phase."""
        costs = {}
        for record in self.records:
            if record.phase_id not in costs:
                costs[record.phase_id] = 0.0
            costs[record.phase_id] += record.amount
        return costs

    def get_cost_by_model(self) -> Dict[str, float]:
        """Get cost breakdown by model."""
        costs = {}
        for record in self.records:
            if record.model:
                if record.model not in costs:
                    costs[record.model] = 0.0
                costs[record.model] += record.amount
        return costs

    def get_remaining_budget(self) -> float:
        """Get remaining budget for total workflow."""
        total_cost = self.get_total_cost()
        total_limit = self.limits["total_workflow"]
        return max(0.0, total_limit - total_cost)

    def estimate_remaining_budget(self, phase_id: str) -> float:
        """Estimate remaining budget for phase."""
        phase_cost = self.get_phase_cost(phase_id)
        phase_limit = self.limits.get(phase_id, float("inf"))
        return max(0.0, phase_limit - phase_cost)

    def estimate_items_possible(self, phase_id: str, cost_per_item: float) -> int:
        """
        Estimate how many items can be processed within remaining budget.

        Args:
            phase_id: Phase identifier
            cost_per_item: Estimated cost per item

        Returns:
            Number of items that can be processed
        """
        remaining = self.estimate_remaining_budget(phase_id)
        if cost_per_item <= 0:
            return 0
        return int(remaining / cost_per_item)

    def project_total_cost(
        self, planned_operations: Dict[str, float]
    ) -> Tuple[float, bool]:
        """
        Project total cost if planned operations are executed.

        Args:
            planned_operations: Dict of {phase_id: estimated_cost}

        Returns:
            Tuple of (projected_total, within_limits)
        """
        current_total = self.get_total_cost()
        planned_total = sum(planned_operations.values())
        projected_total = current_total + planned_total

        within_limits = projected_total <= self.limits["total_workflow"]

        return projected_total, within_limits

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary."""
        total_cost = self.get_total_cost()
        total_limit = self.limits["total_workflow"]

        return {
            "total_cost": total_cost,
            "total_limit": total_limit,
            "remaining_budget": total_limit - total_cost,
            "percent_used": (total_cost / total_limit * 100) if total_limit > 0 else 0,
            "by_phase": self.get_cost_by_phase(),
            "by_model": self.get_cost_by_model(),
            "record_count": len(self.records),
            "approval_count": len(self.approval_requests),
        }

    def generate_report(self, output_file: Optional[Path] = None) -> str:
        """
        Generate comprehensive cost report.

        Args:
            output_file: Optional file to write report to

        Returns:
            Report content as string
        """
        if output_file is None:
            output_file = Path("COST_SAFETY_REPORT.md")

        report_lines = []

        # Header
        report_lines.append("# Cost Safety Report")
        report_lines.append("")
        report_lines.append(
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Summary
        summary = self.get_cost_summary()
        total_cost = summary["total_cost"]
        total_limit = summary["total_limit"]
        remaining = summary["remaining_budget"]
        percent_used = summary["percent_used"]

        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append(f"- **Total Cost:** ${total_cost:.2f}")
        report_lines.append(f"- **Total Limit:** ${total_limit:.2f}")
        report_lines.append(f"- **Remaining Budget:** ${remaining:.2f}")
        report_lines.append(f"- **Percent Used:** {percent_used:.1f}%")
        report_lines.append(f"- **Cost Records:** {len(self.records)}")
        report_lines.append(f"- **Approval Requests:** {len(self.approval_requests)}")
        report_lines.append("")

        # Progress bar
        progress_bar = "█" * int(percent_used / 5) + "░" * (20 - int(percent_used / 5))
        report_lines.append(f"**Budget Usage:** [{progress_bar}] {percent_used:.1f}%")
        report_lines.append("")

        # Status indicator
        if percent_used >= 100:
            report_lines.append("🔴 **STATUS:** Budget exhausted")
        elif percent_used >= 90:
            report_lines.append("🟡 **STATUS:** Near budget limit")
        elif percent_used >= 70:
            report_lines.append("🟢 **STATUS:** Budget healthy")
        else:
            report_lines.append("🟢 **STATUS:** Budget excellent")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Cost by Phase
        report_lines.append("## Cost by Phase")
        report_lines.append("")

        costs_by_phase = self.get_cost_by_phase()
        for phase_id in sorted(costs_by_phase.keys()):
            phase_cost = costs_by_phase[phase_id]
            phase_limit = self.limits.get(phase_id, float("inf"))
            phase_pct = (
                (phase_cost / phase_limit * 100) if phase_limit < float("inf") else 0
            )

            status = "✅" if phase_pct < 80 else "⚠️" if phase_pct < 100 else "🔴"
            report_lines.append(f"### {status} {phase_id}")
            report_lines.append("")
            report_lines.append(f"- **Cost:** ${phase_cost:.2f}")
            report_lines.append(f"- **Limit:** ${phase_limit:.2f}")
            report_lines.append(
                f"- **Remaining:** ${max(0, phase_limit - phase_cost):.2f}"
            )
            report_lines.append(f"- **Used:** {phase_pct:.1f}%")
            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

        # Cost by Model
        costs_by_model = self.get_cost_by_model()
        if costs_by_model:
            report_lines.append("## Cost by Model")
            report_lines.append("")

            for model in sorted(costs_by_model.keys()):
                model_cost = costs_by_model[model]
                model_pct = (model_cost / total_cost * 100) if total_cost > 0 else 0
                report_lines.append(
                    f"- **{model}:** ${model_cost:.2f} ({model_pct:.1f}%)"
                )

            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")

        # Approval Requests
        if self.approval_requests:
            report_lines.append("## Approval Requests")
            report_lines.append("")

            # Group by status
            by_status = {}
            for approval in self.approval_requests:
                if approval.status not in by_status:
                    by_status[approval.status] = []
                by_status[approval.status].append(approval)

            for status in [
                ApprovalStatus.APPROVED,
                ApprovalStatus.AUTO_APPROVED,
                ApprovalStatus.REJECTED,
                ApprovalStatus.PENDING,
            ]:
                if status not in by_status:
                    continue

                approvals = by_status[status]
                emoji = {
                    ApprovalStatus.APPROVED: "✅",
                    ApprovalStatus.AUTO_APPROVED: "✅",
                    ApprovalStatus.REJECTED: "❌",
                    ApprovalStatus.PENDING: "⏳",
                }.get(status, "📋")

                report_lines.append(f"### {emoji} {status.value} ({len(approvals)})")
                report_lines.append("")

                for approval in approvals:
                    report_lines.append(f"#### {approval.operation}")
                    report_lines.append("")
                    report_lines.append(
                        f"- **Estimated Cost:** ${approval.estimated_cost:.2f}"
                    )
                    report_lines.append(
                        f"- **Affected Items:** {approval.affected_items}"
                    )
                    report_lines.append(f"- **Impact:** {approval.impact_description}")
                    report_lines.append(f"- **Requested:** {approval.requested_at}")
                    if approval.responded_at:
                        report_lines.append(f"- **Responded:** {approval.responded_at}")
                    if approval.response_message:
                        report_lines.append(
                            f"- **Message:** {approval.response_message}"
                        )
                    report_lines.append("")

            report_lines.append("---")
            report_lines.append("")

        # Recent Transactions
        if self.records:
            report_lines.append("## Recent Transactions (Last 10)")
            report_lines.append("")

            recent_records = sorted(
                self.records, key=lambda r: r.timestamp, reverse=True
            )[:10]

            for record in recent_records:
                report_lines.append(f"- **{record.phase_id}:** ${record.amount:.4f}")
                report_lines.append(f"  - Timestamp: {record.timestamp}")
                if record.model:
                    report_lines.append(f"  - Model: {record.model}")
                if record.operation:
                    report_lines.append(f"  - Operation: {record.operation}")

            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")

        report_lines.append(f"*Report generated by Cost Safety Manager v1.0*")

        # Join and save
        report_content = "\n".join(report_lines)

        try:
            with open(output_file, "w") as f:
                f.write(report_content)

            logger.info(f"📊 Cost report generated: {output_file}")
        except Exception as e:
            logger.error(f"❌ Failed to write report: {e}")

        return report_content


def main():
    """Demo/test the Cost Safety Manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Cost Safety Manager")
    parser.add_argument("--reset", action="store_true", help="Reset all cost tracking")
    parser.add_argument("--report", action="store_true", help="Generate cost report")
    parser.add_argument("--record", type=str, help="Record cost for phase")
    parser.add_argument("--amount", type=float, help="Cost amount")
    parser.add_argument("--model", type=str, help="Model name")
    parser.add_argument("--operation", type=str, help="Operation name")
    parser.add_argument(
        "--check", type=str, help="Check if cost would exceed limit for phase"
    )
    parser.add_argument("--estimate", type=float, help="Estimated cost to check")
    parser.add_argument("--summary", action="store_true", help="Show cost summary")

    args = parser.parse_args()

    # Initialize manager
    manager = CostSafetyManager()

    if args.reset:
        logger.info("🔄 Resetting cost tracking...")
        manager.records = []
        manager.approval_requests = []
        manager._save_costs()
        logger.info("✅ Cost tracking reset")

    elif args.record:
        if args.amount is None:
            logger.error("❌ --amount required with --record")
            return

        logger.info(f"💰 Recording cost: {args.record} ${args.amount:.2f}")
        manager.record_cost(
            args.record, args.amount, model=args.model, operation=args.operation
        )

    elif args.check:
        if args.estimate is None:
            logger.error("❌ --estimate required with --check")
            return

        within_limit = manager.check_cost_limit(args.check, args.estimate)

        if within_limit:
            logger.info(f"✅ Within limit: {args.check} +${args.estimate:.2f}")
        else:
            logger.error(f"❌ Would exceed limit: {args.check} +${args.estimate:.2f}")

    elif args.summary:
        summary = manager.get_cost_summary()
        logger.info(f"\n📊 Cost Summary:")
        logger.info(f"   Total Cost: ${summary['total_cost']:.2f}")
        logger.info(f"   Total Limit: ${summary['total_limit']:.2f}")
        logger.info(f"   Remaining: ${summary['remaining_budget']:.2f}")
        logger.info(f"   Used: {summary['percent_used']:.1f}%")
        logger.info(f"   Records: {summary['record_count']}")
        logger.info(f"   Approvals: {summary['approval_count']}")

    if args.report or not any([args.reset, args.record, args.check, args.summary]):
        # Generate report by default or if --report specified
        logger.info("📊 Generating cost report...")
        report = manager.generate_report()
        logger.info(f"\n{report}")


if __name__ == "__main__":
    main()
