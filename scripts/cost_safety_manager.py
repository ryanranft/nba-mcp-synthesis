#!/usr/bin/env python3
"""
Cost Safety Manager - Prevent runaway API costs

Implements cost tracking and limits for all AI-powered operations.
Prevents budget overruns and provides approval gates for expensive operations.

Features:
- Per-phase cost limits
- Total workflow budget enforcement
- Approval requirements for high-cost operations
- Real-time cost tracking
- Budget warnings at 80% and 95%

Usage:
    from cost_safety_manager import CostSafetyManager

    cost_mgr = CostSafetyManager()

    # Check before expensive operation
    if cost_mgr.check_cost_limit('phase_2_analysis', estimated_cost=5.00):
        result = await expensive_operation()
        cost_mgr.track_cost('phase_2_analysis', actual_cost=4.87)
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CostRecord:
    """Record of a cost transaction."""
    timestamp: str
    phase: str
    operation: str
    estimated_cost: float
    actual_cost: float
    approved_by: str = "automatic"
    notes: str = ""


class CostSafetyManager:
    """
    Prevent runaway API costs.

    Cost Limits (per phase):
    - phase_2_analysis: $30.00 (Book analysis)
    - phase_3_synthesis: $20.00 (Claude + GPT-4 synthesis)
    - phase_3.5_modifications: $15.00 (AI plan modifications)
    - phase_5_predictions: $10.00 (Prediction enhancements)
    - total_workflow: $75.00 (Hard limit for entire workflow)

    Approval Thresholds:
    - Operations >$10.00: Require approval
    - Plans affected >5: Require approval
    - Total budget >90%: Require approval
    """

    COST_LIMITS = {
        'phase_0_discovery': 1.00,
        'phase_1_book_discovery': 0.50,
        'phase_2_analysis': 30.00,
        'phase_3_synthesis': 20.00,
        'phase_3.5_modifications': 15.00,
        'phase_4_generation': 5.00,
        'phase_5_predictions': 10.00,
        'phase_6_status': 0.50,
        'phase_7_optimization': 1.00,
        'phase_8_tracking': 0.50,
        'phase_9_integration': 2.00,
        'total_workflow': 75.00
    }

    def __init__(self, cost_log_path: Optional[Path] = None):
        """Initialize cost safety manager."""
        self.cost_log_path = cost_log_path or Path("implementation_plans/cost_tracking.json")
        self.cost_log_path.parent.mkdir(parents=True, exist_ok=True)

        self.costs = self._load_costs()
        logger.info("💰 Cost Safety Manager initialized")
        logger.info(f"   Total budget: ${self.COST_LIMITS['total_workflow']:.2f}")
        logger.info(f"   Current spending: ${self.get_total_cost():.2f}")

    def _load_costs(self) -> Dict:
        """Load cost history from disk."""
        if self.cost_log_path.exists():
            return json.loads(self.cost_log_path.read_text())
        else:
            return {
                'records': [],
                'phase_totals': {},
                'total_cost': 0.0,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }

    def _save_costs(self):
        """Save cost history to disk."""
        self.costs['last_updated'] = datetime.now().isoformat()
        self.cost_log_path.write_text(json.dumps(self.costs, indent=2))

    def check_cost_limit(self, phase: str, estimated_cost: float) -> bool:
        """
        Check if operation would exceed cost limit.

        Args:
            phase: Phase identifier (e.g., 'phase_2_analysis')
            estimated_cost: Estimated cost in USD

        Returns:
            True if within limits, False if would exceed
        """
        phase_limit = self.COST_LIMITS.get(phase, 10.00)
        phase_current = self.costs['phase_totals'].get(phase, 0.0)
        total_limit = self.COST_LIMITS['total_workflow']
        total_current = self.costs['total_cost']

        # Check phase limit
        if phase_current + estimated_cost > phase_limit:
            logger.error(f"❌ Cost limit exceeded for {phase}")
            logger.error(f"   Current: ${phase_current:.2f}")
            logger.error(f"   Estimated: ${estimated_cost:.2f}")
            logger.error(f"   Limit: ${phase_limit:.2f}")
            logger.error(f"   Would exceed by: ${(phase_current + estimated_cost - phase_limit):.2f}")
            return False

        # Check total limit
        if total_current + estimated_cost > total_limit:
            logger.error(f"❌ Total workflow budget exceeded")
            logger.error(f"   Current: ${total_current:.2f}")
            logger.error(f"   Estimated: ${estimated_cost:.2f}")
            logger.error(f"   Limit: ${total_limit:.2f}")
            logger.error(f"   Would exceed by: ${(total_current + estimated_cost - total_limit):.2f}")
            return False

        # Warning at 80%
        phase_pct = ((phase_current + estimated_cost) / phase_limit) * 100
        if phase_pct > 80:
            logger.warning(f"⚠️  {phase} at {phase_pct:.1f}% of budget")

        total_pct = ((total_current + estimated_cost) / total_limit) * 100
        if total_pct > 80:
            logger.warning(f"⚠️  Total workflow at {total_pct:.1f}% of budget")

        return True

    def require_approval(
        self,
        operation: str,
        cost: float,
        plans_affected: int = 0,
        auto_approve: bool = False
    ) -> bool:
        """
        Require human approval for expensive or impactful operations.

        Approval required if:
        - Cost > $10.00
        - Plans affected > 5
        - Total budget > 90%

        Args:
            operation: Description of operation
            cost: Estimated cost
            plans_affected: Number of plans that will be modified
            auto_approve: Auto-approve if True (--yes flag)

        Returns:
            True if approved, False otherwise
        """
        total_pct = ((self.costs['total_cost'] + cost) / self.COST_LIMITS['total_workflow']) * 100

        needs_approval = (
            cost > 10.00 or
            plans_affected > 5 or
            total_pct > 90
        )

        if not needs_approval:
            return True

        if auto_approve:
            logger.info(f"✅ Auto-approved: {operation}")
            return True

        logger.warning(f"⚠️  Approval required for: {operation}")
        logger.warning(f"   Estimated cost: ${cost:.2f}")
        if plans_affected > 0:
            logger.warning(f"   Plans affected: {plans_affected}")
        logger.warning(f"   Total budget usage: {total_pct:.1f}%")
        logger.warning(f"\n   Approve? (y/n): ")

        # In production, this would wait for user input
        # For now, default to requiring manual --yes flag
        return False

    def track_cost(
        self,
        phase: str,
        actual_cost: float,
        operation: str = "",
        estimated_cost: Optional[float] = None,
        notes: str = ""
    ):
        """
        Track actual cost after operation completes.

        Args:
            phase: Phase identifier
            actual_cost: Actual cost incurred
            operation: Description of operation
            estimated_cost: Original estimate (for accuracy tracking)
            notes: Additional notes
        """
        record = CostRecord(
            timestamp=datetime.now().isoformat(),
            phase=phase,
            operation=operation or phase,
            estimated_cost=estimated_cost or actual_cost,
            actual_cost=actual_cost,
            notes=notes
        )

        # Update records
        self.costs['records'].append(asdict(record))

        # Update totals
        if phase not in self.costs['phase_totals']:
            self.costs['phase_totals'][phase] = 0.0
        self.costs['phase_totals'][phase] += actual_cost
        self.costs['total_cost'] += actual_cost

        # Save
        self._save_costs()

        # Log
        logger.info(f"💰 Cost tracked: {phase} = ${actual_cost:.2f}")
        if estimated_cost and abs(actual_cost - estimated_cost) > 0.50:
            diff_pct = ((actual_cost - estimated_cost) / estimated_cost) * 100
            logger.info(f"   Estimate accuracy: {diff_pct:+.1f}%")

    def get_total_cost(self) -> float:
        """Get total cost spent across all phases."""
        return self.costs['total_cost']

    def get_phase_cost(self, phase: str) -> float:
        """Get total cost for specific phase."""
        return self.costs['phase_totals'].get(phase, 0.0)

    def get_remaining_budget(self, phase: Optional[str] = None) -> float:
        """Get remaining budget for phase or total workflow."""
        if phase:
            limit = self.COST_LIMITS.get(phase, 10.00)
            spent = self.get_phase_cost(phase)
            return max(0.0, limit - spent)
        else:
            limit = self.COST_LIMITS['total_workflow']
            spent = self.get_total_cost()
            return max(0.0, limit - spent)

    def generate_cost_report(self) -> str:
        """Generate human-readable cost report."""
        report = f"""# Cost Report

**Generated:** {datetime.now().isoformat()}
**Total Budget:** ${self.COST_LIMITS['total_workflow']:.2f}
**Total Spent:** ${self.get_total_cost():.2f}
**Remaining:** ${self.get_remaining_budget():.2f}
**Budget Used:** {(self.get_total_cost() / self.COST_LIMITS['total_workflow'] * 100):.1f}%

## Per-Phase Breakdown

| Phase | Limit | Spent | Remaining | % Used |
|-------|-------|-------|-----------|--------|
"""

        for phase, limit in sorted(self.COST_LIMITS.items()):
            if phase == 'total_workflow':
                continue
            spent = self.get_phase_cost(phase)
            remaining = max(0.0, limit - spent)
            pct = (spent / limit * 100) if limit > 0 else 0

            status = "✅" if pct < 80 else "⚠️" if pct < 95 else "❌"
            report += f"| {phase} | ${limit:.2f} | ${spent:.2f} | ${remaining:.2f} | {status} {pct:.1f}% |\n"

        report += f"\n## Recent Transactions\n\n"

        # Show last 10 transactions
        recent = self.costs['records'][-10:]
        for record in reversed(recent):
            report += f"- **{record['timestamp']}**: {record['phase']} - ${record['actual_cost']:.2f} ({record['operation']})\n"

        return report

    def save_cost_report(self, output_path: Optional[Path] = None):
        """Save cost report to markdown file."""
        output_path = output_path or Path("implementation_plans/COST_REPORT.md")
        report = self.generate_cost_report()
        output_path.write_text(report)
        logger.info(f"📊 Cost report saved: {output_path}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Initialize manager
    cost_mgr = CostSafetyManager()

    # Example: Check before expensive operation
    phase = 'phase_2_analysis'
    estimated = 5.00

    if cost_mgr.check_cost_limit(phase, estimated):
        print(f"✅ Operation approved: ${estimated:.2f}")

        # Simulate operation
        actual = 4.87
        cost_mgr.track_cost(phase, actual, operation="Analyze 5 books", estimated_cost=estimated)

    # Generate report
    cost_mgr.save_cost_report()
    print("\n" + cost_mgr.generate_cost_report())

