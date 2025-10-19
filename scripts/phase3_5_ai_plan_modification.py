#!/usr/bin/env python3
"""
Phase 3.5: AI Plan Modifications

This phase runs after consolidation & synthesis (Phase 3) to:
1. Analyze synthesis results for improvement opportunities
2. Autonomously ADD new plans from AI recommendations
3. MODIFY existing plans based on new insights
4. DELETE obsolete plans that are superseded
5. MERGE duplicate or overlapping plans

All operations have confidence thresholds and optional approval prompts.

Part of Tier 2 implementation - the AI intelligence layer.
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import our Tier 2 systems
import sys
sys.path.insert(0, str(Path(__file__).parent))

from intelligent_plan_editor import IntelligentPlanEditor
from conflict_resolver import ConflictResolver
from smart_integrator import SmartIntegrator
from phase_status_manager import PhaseStatusManager

logger = logging.getLogger(__name__)


class Phase35AIPlanModification:
    """
    Phase 3.5: AI-powered plan modifications.
    
    Capabilities:
    - Analyze synthesis output for gaps
    - Detect duplicate/obsolete plans
    - Propose new plans from recommendations
    - Modify existing plans with improvements
    - Request approval for high-impact changes
    
    Example:
        >>> phase = Phase35AIPlanModification()
        >>> result = await phase.run_ai_modifications()
        >>> print(f"Plans added: {result['plans_added']}")
        >>> print(f"Plans modified: {result['plans_modified']}")
    """
    
    def __init__(
        self,
        auto_approve_threshold: float = 0.85,
        enable_auto_add: bool = True,
        enable_auto_modify: bool = True,
        enable_auto_delete: bool = False,  # More conservative
        enable_auto_merge: bool = True
    ):
        """
        Initialize Phase 3.5.
        
        Args:
            auto_approve_threshold: Confidence threshold for auto-approval
            enable_auto_add: Allow automatic plan addition
            enable_auto_modify: Allow automatic plan modification
            enable_auto_delete: Allow automatic plan deletion
            enable_auto_merge: Allow automatic plan merging
        """
        self.auto_approve_threshold = auto_approve_threshold
        self.enable_auto_add = enable_auto_add
        self.enable_auto_modify = enable_auto_modify
        self.enable_auto_delete = enable_auto_delete
        self.enable_auto_merge = enable_auto_merge
        
        # Initialize subsystems
        self.plan_editor = IntelligentPlanEditor(
            require_approval_threshold=auto_approve_threshold
        )
        self.status_mgr = PhaseStatusManager()
        
        logger.info("Phase 3.5: AI Plan Modification initialized")
        logger.info(f"  Auto-approve threshold: {auto_approve_threshold:.1%}")
        logger.info(f"  Auto-add: {enable_auto_add}")
        logger.info(f"  Auto-modify: {enable_auto_modify}")
        logger.info(f"  Auto-delete: {enable_auto_delete}")
        logger.info(f"  Auto-merge: {enable_auto_merge}")
    
    async def run_ai_modifications(
        self,
        synthesis_file: Optional[Path] = None,
        dry_run: bool = False
    ) -> Dict[str, any]:
        """
        Run AI-powered plan modifications.
        
        Args:
            synthesis_file: Path to synthesis output from Phase 3
            dry_run: Preview modifications without applying
        
        Returns:
            Dict with modification results
        """
        logger.info("\n" + "=" * 70)
        logger.info("PHASE 3.5: AI PLAN MODIFICATIONS")
        logger.info("=" * 70 + "\n")
        
        start_time = datetime.now()
        
        # Mark phase as started
        if not dry_run:
            self.status_mgr.start_phase("phase_3_5", "Phase 3.5: AI Plan Modifications")
        
        try:
            # Step 1: Load synthesis results
            synthesis_data = await self._load_synthesis(synthesis_file)
            logger.info(f"Loaded synthesis with {len(synthesis_data.get('recommendations', []))} recommendations")
            
            # Step 2: Analyze current plans
            current_plans = self._analyze_current_plans()
            logger.info(f"Found {len(current_plans)} existing plans")
            
            # Step 3: Detect gaps (recommendations not in plans)
            gaps = self._detect_gaps(synthesis_data, current_plans)
            logger.info(f"Detected {len(gaps)} gaps")
            
            # Step 4: Detect duplicates
            duplicates = self._detect_duplicates(current_plans)
            logger.info(f"Detected {len(duplicates)} duplicate groups")
            
            # Step 5: Detect obsolete plans
            obsolete = self._detect_obsolete(current_plans, synthesis_data)
            logger.info(f"Detected {len(obsolete)} potentially obsolete plans")
            
            # Step 6: Propose modifications
            proposed_modifications = self._propose_modifications(
                gaps, duplicates, obsolete
            )
            
            logger.info("\nProposed Modifications:")
            logger.info(f"  ADD: {len(proposed_modifications['add'])}")
            logger.info(f"  MODIFY: {len(proposed_modifications['modify'])}")
            logger.info(f"  DELETE: {len(proposed_modifications['delete'])}")
            logger.info(f"  MERGE: {len(proposed_modifications['merge'])}")
            
            if dry_run:
                logger.info("\n🔍 DRY RUN MODE - No changes applied")
                return {
                    'dry_run': True,
                    'proposed': proposed_modifications,
                    'plans_added': 0,
                    'plans_modified': 0,
                    'plans_deleted': 0,
                    'plans_merged': 0
                }
            
            # Step 7: Apply modifications
            results = await self._apply_modifications(proposed_modifications)
            
            # Step 8: Mark phase complete
            duration = (datetime.now() - start_time).total_seconds()
            self.status_mgr.complete_phase("phase_3_5", duration)
            
            # Step 9: Trigger reruns for affected phases
            if results['plans_added'] > 0 or results['plans_modified'] > 0:
                self.status_mgr.mark_needs_rerun(
                    "phase_4",
                    reason="Phase 3.5 modified implementation plans",
                    ai_modified=True
                )
            
            logger.info("\n✅ Phase 3.5 complete")
            logger.info(f"  Added: {results['plans_added']} plans")
            logger.info(f"  Modified: {results['plans_modified']} plans")
            logger.info(f"  Deleted: {results['plans_deleted']} plans")
            logger.info(f"  Merged: {results['plans_merged']} plans")
            
            return results
        
        except Exception as e:
            logger.error(f"\n❌ Phase 3.5 failed: {e}")
            if not dry_run:
                self.status_mgr.fail_phase("phase_3_5", str(e))
            raise
    
    async def _load_synthesis(self, synthesis_file: Optional[Path]) -> Dict[str, any]:
        """Load synthesis results from Phase 3."""
        if synthesis_file is None:
            synthesis_file = Path("implementation_plans/PHASE3_SUMMARY.json")
        
        if not synthesis_file.exists():
            logger.warning(f"Synthesis file not found: {synthesis_file}")
            # Return mock data for testing
            return {
                'recommendations': [
                    {
                        'id': 'rec_test_1',
                        'title': 'Test Recommendation 1',
                        'priority': 'high'
                    }
                ]
            }
        
        with open(synthesis_file) as f:
            return json.load(f)
    
    def _analyze_current_plans(self) -> List[Dict[str, any]]:
        """Load and analyze current implementation plans."""
        plans = []
        plans_dir = Path("implementation_plans")
        
        for plan_file in plans_dir.glob("*.json"):
            # Skip non-plan files
            if plan_file.name.startswith('PHASE') or plan_file.name.startswith('phase_') or plan_file.name.startswith('nba_'):
                continue
            
            try:
                with open(plan_file) as f:
                    plan_data = json.load(f)
                    plan_data['_file'] = plan_file.name
                    plans.append(plan_data)
            except Exception as e:
                logger.warning(f"Error loading plan {plan_file}: {e}")
        
        return plans
    
    def _detect_gaps(
        self,
        synthesis_data: Dict[str, any],
        current_plans: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """Detect recommendations not covered by existing plans."""
        gaps = []
        
        recommendations = synthesis_data.get('recommendations', [])
        plan_titles = [p.get('title', '').lower() for p in current_plans]
        
        for rec in recommendations:
            rec_title = rec.get('title', '').lower()
            
            # Check if recommendation already has a plan
            has_plan = any(rec_title in plan_title or plan_title in rec_title for plan_title in plan_titles)
            
            if not has_plan:
                gaps.append({
                    'recommendation': rec,
                    'confidence': 0.8,  # Moderate confidence for gap filling
                    'reason': 'No existing plan covers this recommendation'
                })
        
        return gaps
    
    def _detect_duplicates(
        self,
        current_plans: List[Dict[str, any]]
    ) -> List[List[str]]:
        """Detect duplicate or very similar plans."""
        from difflib import SequenceMatcher
        
        duplicates = []
        used_indices = set()
        
        for i, plan1 in enumerate(current_plans):
            if i in used_indices:
                continue
            
            group = [plan1['_file'].replace('.json', '')]
            
            for j, plan2 in enumerate(current_plans[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                # Compare titles
                similarity = SequenceMatcher(
                    None,
                    plan1.get('title', '').lower(),
                    plan2.get('title', '').lower()
                ).ratio()
                
                if similarity > 0.85:  # Very similar
                    group.append(plan2['_file'].replace('.json', ''))
                    used_indices.add(j)
            
            if len(group) > 1:
                duplicates.append(group)
        
        return duplicates
    
    def _detect_obsolete(
        self,
        current_plans: List[Dict[str, any]],
        synthesis_data: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """Detect plans that may be obsolete."""
        obsolete = []
        
        # Check for old plans not mentioned in synthesis
        synthesis_topics = [
            r.get('title', '').lower() 
            for r in synthesis_data.get('recommendations', [])
        ]
        
        for plan in current_plans:
            plan_title = plan.get('title', '').lower()
            
            # Check if plan topic is mentioned in synthesis
            mentioned = any(
                topic in plan_title or plan_title in topic 
                for topic in synthesis_topics
            )
            
            if not mentioned and plan.get('priority') == 'low':
                obsolete.append({
                    'plan_id': plan['_file'].replace('.json', ''),
                    'title': plan.get('title'),
                    'confidence': 0.6,  # Low confidence for deletion
                    'reason': 'Not mentioned in latest synthesis and low priority'
                })
        
        return obsolete
    
    def _propose_modifications(
        self,
        gaps: List[Dict[str, any]],
        duplicates: List[List[str]],
        obsolete: List[Dict[str, any]]
    ) -> Dict[str, List[Dict[str, any]]]:
        """Propose specific modifications based on analysis."""
        proposals = {
            'add': [],
            'modify': [],
            'delete': [],
            'merge': []
        }
        
        # Propose ADD for gaps
        if self.enable_auto_add:
            for gap in gaps:
                rec = gap['recommendation']
                proposals['add'].append({
                    'plan_data': {
                        'id': rec.get('id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                        'title': rec.get('title'),
                        'description': rec.get('description', ''),
                        'priority': rec.get('priority', 'medium'),
                        'source': 'ai_synthesis'
                    },
                    'reason': gap['reason'],
                    'confidence': gap['confidence']
                })
        
        # Propose MERGE for duplicates
        if self.enable_auto_merge:
            for dup_group in duplicates:
                if len(dup_group) >= 2:
                    proposals['merge'].append({
                        'plan_ids': dup_group,
                        'merged_plan_id': f"merged_{dup_group[0]}",
                        'reason': f"Merging {len(dup_group)} duplicate plans",
                        'confidence': 0.75
                    })
        
        # Propose DELETE for obsolete
        if self.enable_auto_delete:
            for obs in obsolete:
                proposals['delete'].append({
                    'plan_id': obs['plan_id'],
                    'reason': obs['reason'],
                    'confidence': obs['confidence']
                })
        
        return proposals
    
    async def _apply_modifications(
        self,
        proposals: Dict[str, List[Dict[str, any]]]
    ) -> Dict[str, int]:
        """Apply proposed modifications."""
        results = {
            'plans_added': 0,
            'plans_modified': 0,
            'plans_deleted': 0,
            'plans_merged': 0,
            'approvals_needed': []
        }
        
        # Apply ADD operations
        for add_proposal in proposals['add']:
            result = self.plan_editor.add_plan(
                plan_data=add_proposal['plan_data'],
                reason=add_proposal['reason'],
                confidence=add_proposal['confidence'],
                require_approval=False
            )
            
            if result['success']:
                results['plans_added'] += 1
            elif 'approval_prompt' in result:
                results['approvals_needed'].append(result)
        
        # Apply MODIFY operations
        for modify_proposal in proposals['modify']:
            result = self.plan_editor.modify_plan(
                plan_id=modify_proposal['plan_id'],
                modifications=modify_proposal['modifications'],
                reason=modify_proposal['reason'],
                confidence=modify_proposal['confidence'],
                require_approval=False
            )
            
            if result['success']:
                results['plans_modified'] += 1
            elif 'approval_prompt' in result:
                results['approvals_needed'].append(result)
        
        # Apply DELETE operations
        for delete_proposal in proposals['delete']:
            result = self.plan_editor.delete_plan(
                plan_id=delete_proposal['plan_id'],
                reason=delete_proposal['reason'],
                confidence=delete_proposal['confidence'],
                require_approval=True  # Always require approval for deletion
            )
            
            if result['success']:
                results['plans_deleted'] += 1
            elif 'approval_prompt' in result:
                results['approvals_needed'].append(result)
        
        # Apply MERGE operations
        for merge_proposal in proposals['merge']:
            # Create merged plan data
            merged_data = {
                'id': merge_proposal['merged_plan_id'],
                'title': f"Merged: {', '.join(merge_proposal['plan_ids'][:2])}{'...' if len(merge_proposal['plan_ids']) > 2 else ''}",
                'description': 'Merged plan from duplicates'
            }
            
            result = self.plan_editor.merge_plans(
                plan_ids=merge_proposal['plan_ids'],
                merged_plan_data=merged_data,
                reason=merge_proposal['reason'],
                confidence=merge_proposal['confidence'],
                require_approval=False
            )
            
            if result['success']:
                results['plans_merged'] += 1
            elif 'approval_prompt' in result:
                results['approvals_needed'].append(result)
        
        # Log approval requests
        if results['approvals_needed']:
            logger.warning(f"\n⚠️  {len(results['approvals_needed'])} operations require manual approval")
            for approval in results['approvals_needed']:
                logger.warning(f"   - {approval.get('approval_prompt')}")
        
        return results


async def main():
    """Main entry point for Phase 3.5."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Phase 3.5: AI Plan Modifications"
    )
    parser.add_argument(
        '--synthesis-file',
        type=Path,
        help="Path to Phase 3 synthesis output"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Preview modifications without applying"
    )
    parser.add_argument(
        '--auto-approve-threshold',
        type=float,
        default=0.85,
        help="Confidence threshold for auto-approval (default: 0.85)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Run Phase 3.5
    phase = Phase35AIPlanModification(
        auto_approve_threshold=args.auto_approve_threshold
    )
    
    result = await phase.run_ai_modifications(
        synthesis_file=args.synthesis_file,
        dry_run=args.dry_run
    )
    
    # Print summary
    print("\n" + "=" * 70)
    print("PHASE 3.5 SUMMARY")
    print("=" * 70)
    print(f"Plans Added: {result['plans_added']}")
    print(f"Plans Modified: {result['plans_modified']}")
    print(f"Plans Deleted: {result['plans_deleted']}")
    print(f"Plans Merged: {result['plans_merged']}")
    
    if 'approvals_needed' in result:
        print(f"Approvals Needed: {len(result['approvals_needed'])}")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

