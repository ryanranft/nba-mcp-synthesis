#!/usr/bin/env python3
"""
Intelligent Plan Editor - CRUD Operations for Implementation Plans

This system enables AI to autonomously:
- ADD new implementation plans
- MODIFY existing plans with improvements
- DELETE obsolete plans
- MERGE duplicate plans

All operations create automatic backups and trigger phase status updates.

Part of Tier 2 implementation for intelligent plan management.
"""

import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import difflib

logger = logging.getLogger(__name__)


@dataclass
class PlanOperation:
    """Record of a plan operation."""
    operation_type: str  # 'add', 'modify', 'delete', 'merge'
    timestamp: str
    plan_id: str
    description: str
    backup_path: Optional[str]
    changes: Dict[str, any]
    reason: str
    ai_confidence: float  # 0.0 to 1.0


class IntelligentPlanEditor:
    """
    Intelligent editor for implementation plans.

    Capabilities:
    - ADD new plans from AI recommendations
    - MODIFY existing plans with improvements
    - DELETE obsolete or superseded plans
    - MERGE duplicate or overlapping plans
    - Automatic backup before all operations
    - Change tracking and logging
    - Phase status integration

    Example:
        >>> editor = IntelligentPlanEditor()
        >>> result = editor.add_plan(plan_data, reason="AI identified gap", confidence=0.9)
        >>> print(f"Plan added: {result['plan_id']}")
    """

    def __init__(
        self,
        plans_dir: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        auto_backup: bool = True,
        require_approval_threshold: float = 0.8
    ):
        """
        Initialize intelligent plan editor.

        Args:
            plans_dir: Directory containing implementation plans
            backup_dir: Directory for backups
            auto_backup: Automatically backup before modifications
            require_approval_threshold: Confidence threshold for auto-approval
        """
        if plans_dir is None:
            plans_dir = Path("implementation_plans")

        if backup_dir is None:
            backup_dir = plans_dir / "backups"

        self.plans_dir = Path(plans_dir)
        self.backup_dir = Path(backup_dir)
        self.auto_backup = auto_backup
        self.require_approval_threshold = require_approval_threshold

        # Ensure directories exist
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Operation log
        self.log_file = self.plans_dir / "plan_operations.json"
        self.operations = self._load_operations()

        logger.info(f"IntelligentPlanEditor initialized")
        logger.info(f"  Plans directory: {self.plans_dir}")
        logger.info(f"  Auto-backup: {self.auto_backup}")
        logger.info(f"  Approval threshold: {self.require_approval_threshold}")

    def _load_operations(self) -> List[PlanOperation]:
        """Load operation history from log file."""
        if self.log_file.exists():
            try:
                with open(self.log_file) as f:
                    data = json.load(f)
                return [PlanOperation(**op) for op in data]
            except Exception as e:
                logger.warning(f"Error loading operation log: {e}")
                return []
        return []

    def _save_operations(self):
        """Save operation history to log file."""
        try:
            data = [asdict(op) for op in self.operations]
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving operation log: {e}")

    def _create_backup(self, plan_id: str, operation: str) -> Optional[str]:
        """
        Create backup of plan before modification.

        Args:
            plan_id: Plan identifier
            operation: Operation type

        Returns:
            Path to backup file or None if failed
        """
        if not self.auto_backup:
            return None

        plan_file = self.plans_dir / f"{plan_id}.json"
        if not plan_file.exists():
            logger.warning(f"Plan file not found for backup: {plan_file}")
            return None

        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{plan_id}_{operation}_{timestamp}.json"

        try:
            shutil.copy2(plan_file, backup_file)
            logger.info(f"Backup created: {backup_file}")
            return str(backup_file)
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def _log_operation(self, operation: PlanOperation):
        """Log an operation."""
        self.operations.append(operation)
        self._save_operations()

    def _load_plan(self, plan_id: str) -> Optional[Dict[str, any]]:
        """Load plan from file."""
        plan_file = self.plans_dir / f"{plan_id}.json"
        if plan_file.exists():
            try:
                with open(plan_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading plan {plan_id}: {e}")
                return None
        return None

    def _save_plan(self, plan_id: str, plan_data: Dict[str, any]):
        """Save plan to file."""
        plan_file = self.plans_dir / f"{plan_id}.json"
        try:
            with open(plan_file, 'w') as f:
                json.dump(plan_data, f, indent=2)
            logger.info(f"Plan saved: {plan_file}")
        except Exception as e:
            logger.error(f"Error saving plan {plan_id}: {e}")
            raise

    def add_plan(
        self,
        plan_data: Dict[str, any],
        reason: str,
        confidence: float = 0.9,
        require_approval: bool = False
    ) -> Dict[str, any]:
        """
        Add a new implementation plan.

        Args:
            plan_data: Plan content with id, title, description, etc.
            reason: Why this plan is being added
            confidence: AI confidence in this operation (0.0-1.0)
            require_approval: Force manual approval

        Returns:
            Dict with operation result
        """
        plan_id = plan_data.get('id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        logger.info(f"ADD PLAN: {plan_id}")
        logger.info(f"  Reason: {reason}")
        logger.info(f"  Confidence: {confidence:.1%}")

        # Check if approval needed
        needs_approval = (
            require_approval or
            confidence < self.require_approval_threshold
        )

        if needs_approval:
            logger.warning(f"⚠️  Manual approval required (confidence {confidence:.1%} < {self.require_approval_threshold:.1%})")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': 'Manual approval required',
                'confidence': confidence,
                'approval_prompt': f"Add new plan '{plan_data.get('title', plan_id)}'? (confidence: {confidence:.1%})"
            }

        # Check if plan already exists
        if (self.plans_dir / f"{plan_id}.json").exists():
            logger.error(f"Plan {plan_id} already exists")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': 'Plan already exists'
            }

        # Add metadata
        plan_data['created_at'] = datetime.now().isoformat()
        plan_data['created_by'] = 'ai'
        plan_data['confidence'] = confidence
        plan_data['reason'] = reason

        # Save plan
        try:
            self._save_plan(plan_id, plan_data)

            # Log operation
            operation = PlanOperation(
                operation_type='add',
                timestamp=datetime.now().isoformat(),
                plan_id=plan_id,
                description=f"Added new plan: {plan_data.get('title', plan_id)}",
                backup_path=None,
                changes={'new_plan': True},
                reason=reason,
                ai_confidence=confidence
            )
            self._log_operation(operation)

            logger.info(f"✅ Plan {plan_id} added successfully")

            return {
                'success': True,
                'plan_id': plan_id,
                'operation': 'add',
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Failed to add plan: {e}")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': f"Error: {str(e)}"
            }

    def modify_plan(
        self,
        plan_id: str,
        modifications: Dict[str, any],
        reason: str,
        confidence: float = 0.9,
        require_approval: bool = False
    ) -> Dict[str, any]:
        """
        Modify an existing implementation plan.

        Args:
            plan_id: ID of plan to modify
            modifications: Dict of field -> new value
            reason: Why this modification is being made
            confidence: AI confidence in this operation (0.0-1.0)
            require_approval: Force manual approval

        Returns:
            Dict with operation result
        """
        logger.info(f"MODIFY PLAN: {plan_id}")
        logger.info(f"  Modifications: {list(modifications.keys())}")
        logger.info(f"  Reason: {reason}")
        logger.info(f"  Confidence: {confidence:.1%}")

        # Load existing plan
        plan_data = self._load_plan(plan_id)
        if plan_data is None:
            logger.error(f"Plan {plan_id} not found")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': 'Plan not found'
            }

        # Check if approval needed
        needs_approval = (
            require_approval or
            confidence < self.require_approval_threshold
        )

        if needs_approval:
            logger.warning(f"⚠️  Manual approval required (confidence {confidence:.1%} < {self.require_approval_threshold:.1%})")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': 'Manual approval required',
                'confidence': confidence,
                'approval_prompt': f"Modify plan '{plan_data.get('title', plan_id)}'? Changes: {list(modifications.keys())}"
            }

        # Create backup
        backup_path = self._create_backup(plan_id, 'modify')

        # Apply modifications
        old_data = plan_data.copy()
        for key, value in modifications.items():
            plan_data[key] = value

        # Add modification metadata
        if 'modifications' not in plan_data:
            plan_data['modifications'] = []

        plan_data['modifications'].append({
            'timestamp': datetime.now().isoformat(),
            'modified_by': 'ai',
            'fields': list(modifications.keys()),
            'reason': reason,
            'confidence': confidence
        })

        plan_data['last_modified_at'] = datetime.now().isoformat()

        # Save modified plan
        try:
            self._save_plan(plan_id, plan_data)

            # Log operation
            operation = PlanOperation(
                operation_type='modify',
                timestamp=datetime.now().isoformat(),
                plan_id=plan_id,
                description=f"Modified plan: {plan_data.get('title', plan_id)}",
                backup_path=backup_path,
                changes=modifications,
                reason=reason,
                ai_confidence=confidence
            )
            self._log_operation(operation)

            logger.info(f"✅ Plan {plan_id} modified successfully")

            return {
                'success': True,
                'plan_id': plan_id,
                'operation': 'modify',
                'changes': modifications,
                'backup': backup_path,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Failed to modify plan: {e}")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': f"Error: {str(e)}"
            }

    def delete_plan(
        self,
        plan_id: str,
        reason: str,
        confidence: float = 0.9,
        require_approval: bool = False
    ) -> Dict[str, any]:
        """
        Delete an obsolete implementation plan.

        Args:
            plan_id: ID of plan to delete
            reason: Why this plan is obsolete
            confidence: AI confidence in this operation (0.0-1.0)
            require_approval: Force manual approval

        Returns:
            Dict with operation result
        """
        logger.info(f"DELETE PLAN: {plan_id}")
        logger.info(f"  Reason: {reason}")
        logger.info(f"  Confidence: {confidence:.1%}")

        # Load existing plan
        plan_data = self._load_plan(plan_id)
        if plan_data is None:
            logger.error(f"Plan {plan_id} not found")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': 'Plan not found'
            }

        # Check if approval needed (deletion always needs high confidence)
        needs_approval = (
            require_approval or
            confidence < 0.85  # Higher threshold for deletion
        )

        if needs_approval:
            logger.warning(f"⚠️  Manual approval required for deletion (confidence {confidence:.1%})")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': 'Manual approval required for deletion',
                'confidence': confidence,
                'approval_prompt': f"Delete plan '{plan_data.get('title', plan_id)}'? Reason: {reason}"
            }

        # Create backup
        backup_path = self._create_backup(plan_id, 'delete')

        # Delete plan file
        plan_file = self.plans_dir / f"{plan_id}.json"
        try:
            plan_file.unlink()

            # Log operation
            operation = PlanOperation(
                operation_type='delete',
                timestamp=datetime.now().isoformat(),
                plan_id=plan_id,
                description=f"Deleted plan: {plan_data.get('title', plan_id)}",
                backup_path=backup_path,
                changes={'deleted': True},
                reason=reason,
                ai_confidence=confidence
            )
            self._log_operation(operation)

            logger.info(f"✅ Plan {plan_id} deleted successfully")

            return {
                'success': True,
                'plan_id': plan_id,
                'operation': 'delete',
                'backup': backup_path,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Failed to delete plan: {e}")
            return {
                'success': False,
                'plan_id': plan_id,
                'reason': f"Error: {str(e)}"
            }

    def merge_plans(
        self,
        plan_ids: List[str],
        merged_plan_data: Dict[str, any],
        reason: str,
        confidence: float = 0.9,
        require_approval: bool = False
    ) -> Dict[str, any]:
        """
        Merge multiple plans into one.

        Args:
            plan_ids: List of plan IDs to merge
            merged_plan_data: Data for the merged plan
            reason: Why these plans are being merged
            confidence: AI confidence in this operation (0.0-1.0)
            require_approval: Force manual approval

        Returns:
            Dict with operation result
        """
        logger.info(f"MERGE PLANS: {', '.join(plan_ids)}")
        logger.info(f"  Reason: {reason}")
        logger.info(f"  Confidence: {confidence:.1%}")

        # Load all plans to merge
        plans_to_merge = []
        for plan_id in plan_ids:
            plan_data = self._load_plan(plan_id)
            if plan_data is None:
                logger.error(f"Plan {plan_id} not found")
                return {
                    'success': False,
                    'reason': f"Plan {plan_id} not found"
                }
            plans_to_merge.append((plan_id, plan_data))

        if len(plans_to_merge) < 2:
            return {
                'success': False,
                'reason': 'Need at least 2 plans to merge'
            }

        # Check if approval needed
        needs_approval = (
            require_approval or
            confidence < self.require_approval_threshold
        )

        if needs_approval:
            logger.warning(f"⚠️  Manual approval required (confidence {confidence:.1%})")
            titles = [p[1].get('title', p[0]) for p in plans_to_merge]
            return {
                'success': False,
                'reason': 'Manual approval required',
                'confidence': confidence,
                'approval_prompt': f"Merge plans: {', '.join(titles)}?"
            }

        # Create backups of all plans
        backups = []
        for plan_id, _ in plans_to_merge:
            backup_path = self._create_backup(plan_id, 'merge')
            if backup_path:
                backups.append(backup_path)

        # Generate merged plan ID
        merged_id = merged_plan_data.get('id', f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        # Add merge metadata
        merged_plan_data['created_at'] = datetime.now().isoformat()
        merged_plan_data['created_by'] = 'ai'
        merged_plan_data['merged_from'] = plan_ids
        merged_plan_data['merge_reason'] = reason
        merged_plan_data['confidence'] = confidence

        try:
            # Save merged plan
            self._save_plan(merged_id, merged_plan_data)

            # Delete original plans
            for plan_id, _ in plans_to_merge:
                plan_file = self.plans_dir / f"{plan_id}.json"
                plan_file.unlink()

            # Log operation
            operation = PlanOperation(
                operation_type='merge',
                timestamp=datetime.now().isoformat(),
                plan_id=merged_id,
                description=f"Merged {len(plan_ids)} plans into {merged_id}",
                backup_path='; '.join(backups) if backups else None,
                changes={'merged_from': plan_ids},
                reason=reason,
                ai_confidence=confidence
            )
            self._log_operation(operation)

            logger.info(f"✅ Plans merged successfully into {merged_id}")

            return {
                'success': True,
                'plan_id': merged_id,
                'operation': 'merge',
                'merged_from': plan_ids,
                'backups': backups,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Failed to merge plans: {e}")
            return {
                'success': False,
                'reason': f"Error: {str(e)}"
            }

    def get_operation_history(self, limit: Optional[int] = None) -> List[PlanOperation]:
        """Get operation history, optionally limited to most recent N."""
        if limit:
            return self.operations[-limit:]
        return self.operations

    def generate_changelog(self, output_file: Optional[Path] = None) -> str:
        """Generate changelog from operation history."""
        lines = []
        lines.append("# Plan Operations Changelog")
        lines.append("")
        lines.append(f"**Total Operations**: {len(self.operations)}")
        lines.append("")

        # Group by operation type
        by_type = {}
        for op in self.operations:
            if op.operation_type not in by_type:
                by_type[op.operation_type] = []
            by_type[op.operation_type].append(op)

        lines.append("## Summary")
        lines.append("")
        for op_type, ops in sorted(by_type.items()):
            lines.append(f"- **{op_type.upper()}**: {len(ops)} operations")
        lines.append("")

        # Recent operations
        lines.append("## Recent Operations")
        lines.append("")
        for op in reversed(self.operations[-10:]):  # Last 10
            lines.append(f"### {op.operation_type.upper()}: {op.plan_id}")
            lines.append("")
            lines.append(f"- **Time**: {op.timestamp}")
            lines.append(f"- **Description**: {op.description}")
            lines.append(f"- **Reason**: {op.reason}")
            lines.append(f"- **Confidence**: {op.ai_confidence:.1%}")
            if op.backup_path:
                lines.append(f"- **Backup**: `{op.backup_path}`")
            lines.append("")

        changelog = '\n'.join(lines)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(changelog)
            logger.info(f"Changelog saved to {output_file}")

        return changelog


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("INTELLIGENT PLAN EDITOR DEMO")
    print("=" * 70)
    print()

    # Initialize editor
    editor = IntelligentPlanEditor()

    # Demo 1: ADD new plan
    print("1. ADD NEW PLAN")
    print("-" * 70)
    new_plan = {
        'id': 'demo_plan_1',
        'title': 'Implement Panel Data Analysis',
        'description': 'Add fixed effects models for player analysis',
        'priority': 'high',
        'estimated_effort': 'medium'
    }

    result = editor.add_plan(
        new_plan,
        reason="AI identified gap in current analytics",
        confidence=0.95
    )
    print(f"Result: {result}")
    print()

    # Demo 2: MODIFY existing plan
    print("2. MODIFY EXISTING PLAN")
    print("-" * 70)
    result = editor.modify_plan(
        'demo_plan_1',
        modifications={
            'priority': 'critical',
            'estimated_effort': 'high',
            'notes': 'AI-enhanced: Increased priority due to dependency analysis'
        },
        reason="Dependencies analysis shows this is critical path",
        confidence=0.88
    )
    print(f"Result: {result}")
    print()

    # Demo 3: Generate changelog
    print("3. GENERATE CHANGELOG")
    print("-" * 70)
    changelog = editor.generate_changelog()
    print(changelog)

    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)

