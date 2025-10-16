#!/usr/bin/env python3
"""
Plan Override Manager for Recommendation Organization & Integration System

Manages plan overrides when new recommendations suggest better approaches.
"""

import json
import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class PlanOverrideManager:
    """
    Manages plan overrides when new recommendations suggest better approaches.
    """
    
    def __init__(self, simulator_path: str):
        self.simulator_path = simulator_path
        self.changes_log = []
        
        # Ensure simulator path exists
        if not os.path.exists(simulator_path):
            raise ValueError(f"Simulator path does not exist: {simulator_path}")
    
    def analyze_plan_conflicts(self, phase_num: int, new_recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze if new recommendations conflict with existing plans.
        
        Args:
            phase_num: Phase number (0-9)
            new_recommendations: List of new recommendations
            
        Returns:
            dict: {
                'conflicts': [],
                'enhancements': [],
                'new_additions': []
            }
        """
        existing_plan = self._load_phase_plan(phase_num)
        
        conflicts = []
        enhancements = []
        new_additions = []
        
        for rec in new_recommendations:
            analysis = self._analyze_recommendation(rec, existing_plan)
            
            if analysis['type'] == 'conflict':
                conflicts.append(rec)
            elif analysis['type'] == 'enhancement':
                enhancements.append(rec)
            else:
                new_additions.append(rec)
        
        logger.info(f"Phase {phase_num} analysis: {len(conflicts)} conflicts, {len(enhancements)} enhancements, {len(new_additions)} new additions")
        
        return {
            'conflicts': conflicts,
            'enhancements': enhancements,
            'new_additions': new_additions
        }
    
    def propose_plan_updates(self, phase_num: int, analysis: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Propose updates to phase plan.
        
        Args:
            phase_num: Phase number
            analysis: Conflict analysis results
            
        Returns:
            dict: Proposal data
        """
        proposal = {
            'phase': phase_num,
            'date': datetime.now().isoformat(),
            'conflicts': analysis['conflicts'],
            'enhancements': analysis['enhancements'],
            'new_additions': analysis['new_additions'],
            'action_required': len(analysis['conflicts']) > 0,
            'safe_updates_count': len(analysis['enhancements']) + len(analysis['new_additions']),
            'conflicts_count': len(analysis['conflicts'])
        }
        
        # Write proposal to file
        output_path = os.path.join(
            self.simulator_path,
            f'docs/phases/phase_{phase_num}/PROPOSED_UPDATES.md'
        )
        
        self._write_proposal(output_path, proposal)
        
        return proposal
    
    def apply_safe_updates(self, phase_num: int, proposal: Dict[str, Any]) -> Dict[str, int]:
        """
        Apply non-conflicting updates automatically.
        
        Args:
            phase_num: Phase number
            proposal: Proposal data
            
        Returns:
            dict: Results of applied updates
        """
        applied_count = 0
        
        # Apply enhancements
        for rec in proposal['enhancements']:
            if self._enhance_plan(phase_num, rec):
                applied_count += 1
        
        # Apply new additions
        for rec in proposal['new_additions']:
            if self._add_to_plan(phase_num, rec):
                applied_count += 1
        
        # Log changes
        self.changes_log.append({
            'phase': phase_num,
            'enhancements': len(proposal['enhancements']),
            'additions': len(proposal['new_additions']),
            'conflicts_pending': len(proposal['conflicts']),
            'applied_count': applied_count,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Applied {applied_count} safe updates to Phase {phase_num}")
        
        return {
            'applied': applied_count,
            'pending': len(proposal['conflicts'])
        }
    
    def _load_phase_plan(self, phase_num: int) -> Dict[str, Any]:
        """Load existing phase plan."""
        plan_files = [
            f'docs/phases/phase_{phase_num}/PHASE_{phase_num}_INDEX.md',
            f'docs/phases/phase_{phase_num}/README.md',
            f'docs/phases/phase_{phase_num}/index.md'
        ]
        
        for plan_file in plan_files:
            plan_path = os.path.join(self.simulator_path, plan_file)
            if os.path.exists(plan_path):
                try:
                    with open(plan_path, 'r') as f:
                        content = f.read()
                    return {
                        'file_path': plan_path,
                        'content': content,
                        'exists': True
                    }
                except Exception as e:
                    logger.warning(f"Error reading plan file {plan_path}: {e}")
        
        return {
            'file_path': None,
            'content': '',
            'exists': False
        }
    
    def _analyze_recommendation(self, rec: Dict[str, Any], existing_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single recommendation against existing plan.
        
        Returns:
            dict: {'type': 'conflict'|'enhancement'|'new', 'reason': str}
        """
        rec_title = rec.get('title', '').lower()
        rec_reasoning = rec.get('reasoning', '').lower()
        rec_text = f"{rec_title} {rec_reasoning}"
        
        plan_content = existing_plan.get('content', '').lower()
        
        # Check for conflicts (contradictory approaches)
        conflict_keywords = [
            'instead of', 'rather than', 'alternative to', 'replace',
            'different approach', 'contradicts', 'conflicts with'
        ]
        
        for keyword in conflict_keywords:
            if keyword in rec_text:
                return {
                    'type': 'conflict',
                    'reason': f'Contains conflicting language: "{keyword}"'
                }
        
        # Check for enhancements (improvements to existing)
        enhancement_keywords = [
            'improve', 'enhance', 'optimize', 'better', 'upgrade',
            'extend', 'add to', 'build upon', 'strengthen'
        ]
        
        for keyword in enhancement_keywords:
            if keyword in rec_text:
                return {
                    'type': 'enhancement',
                    'reason': f'Enhances existing approach: "{keyword}"'
                }
        
        # Check if recommendation already exists in plan
        if existing_plan.get('exists', False):
            # Look for similar concepts in existing plan
            similar_concepts = self._find_similar_concepts(rec_text, plan_content)
            if similar_concepts:
                return {
                    'type': 'enhancement',
                    'reason': f'Similar to existing: {similar_concepts}'
                }
        
        # Default to new addition
        return {
            'type': 'new',
            'reason': 'New recommendation not found in existing plan'
        }
    
    def _find_similar_concepts(self, rec_text: str, plan_content: str) -> List[str]:
        """Find similar concepts between recommendation and plan."""
        # Extract key terms from recommendation
        rec_terms = self._extract_key_terms(rec_text)
        
        similar_concepts = []
        for term in rec_terms:
            if term in plan_content and len(term) > 3:  # Avoid very short matches
                similar_concepts.append(term)
        
        return similar_concepts[:3]  # Return top 3 matches
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text."""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Extract words longer than 3 characters
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Filter out stop words
        key_terms = [word for word in words if word not in stop_words]
        
        return key_terms
    
    def _enhance_plan(self, phase_num: int, rec: Dict[str, Any]) -> bool:
        """Enhance existing plan with recommendation."""
        try:
            plan = self._load_phase_plan(phase_num)
            if not plan.get('exists', False):
                return False
            
            # Add recommendation to plan
            enhancement_text = f"\n\n## Enhancement from Book Analysis\n\n**{rec.get('title', 'Untitled')}**\n\n{rec.get('reasoning', 'No additional reasoning provided.')}\n\n*Source: {', '.join(rec.get('source_books', ['Unknown']))}*\n"
            
            updated_content = plan['content'] + enhancement_text
            
            with open(plan['file_path'], 'w') as f:
                f.write(updated_content)
            
            logger.info(f"Enhanced Phase {phase_num} plan with: {rec.get('title', 'Untitled')}")
            return True
            
        except Exception as e:
            logger.error(f"Error enhancing plan for Phase {phase_num}: {e}")
            return False
    
    def _add_to_plan(self, phase_num: int, rec: Dict[str, Any]) -> bool:
        """Add new recommendation to plan."""
        try:
            plan = self._load_phase_plan(phase_num)
            
            if not plan.get('exists', False):
                # Create new plan file
                plan_dir = os.path.join(self.simulator_path, f'docs/phases/phase_{phase_num}')
                os.makedirs(plan_dir, exist_ok=True)
                
                plan_path = os.path.join(plan_dir, f'PHASE_{phase_num}_INDEX.md')
                
                # Create basic plan structure
                content = f"""# Phase {phase_num} - Implementation Plan

**Generated:** {datetime.now().isoformat()}

## Overview

This phase focuses on [Phase description].

## Recommendations from Book Analysis

### {rec.get('title', 'Untitled')}

{rec.get('reasoning', 'No additional reasoning provided.')}

*Source: {', '.join(rec.get('source_books', ['Unknown']))}*

## Implementation Tasks

- [ ] Implement {rec.get('title', 'recommendation')}
- [ ] Test implementation
- [ ] Document changes

## Notes

This plan was automatically generated based on book analysis recommendations.
"""
            else:
                # Add to existing plan
                addition_text = f"\n\n### {rec.get('title', 'Untitled')}\n\n{rec.get('reasoning', 'No additional reasoning provided.')}\n\n*Source: {', '.join(rec.get('source_books', ['Unknown']))}*\n"
                
                content = plan['content'] + addition_text
                plan_path = plan['file_path']
            
            with open(plan_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Added to Phase {phase_num} plan: {rec.get('title', 'Untitled')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to plan for Phase {phase_num}: {e}")
            return False
    
    def _write_proposal(self, output_path: str, proposal: Dict[str, Any]) -> None:
        """Write proposal to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        content = f"""# Proposed Updates for Phase {proposal['phase']}

**Generated:** {proposal['date']}
**Action Required:** {'Yes' if proposal['action_required'] else 'No'}

---

## Summary

- **Safe Updates:** {proposal['safe_updates_count']} (will be applied automatically)
- **Conflicts:** {proposal['conflicts_count']} (require manual review)

---

## Safe Updates (Applied Automatically)

### Enhancements ({len(proposal['enhancements'])})

"""
        
        for i, rec in enumerate(proposal['enhancements'], 1):
            content += f"""#### {i}. {rec.get('title', 'Untitled')}

**Source:** {', '.join(rec.get('source_books', ['Unknown']))}
**Reasoning:** {rec.get('reasoning', 'No additional reasoning provided.')}

"""
        
        content += f"""
### New Additions ({len(proposal['new_additions'])})

"""
        
        for i, rec in enumerate(proposal['new_additions'], 1):
            content += f"""#### {i}. {rec.get('title', 'Untitled')}

**Source:** {', '.join(rec.get('source_books', ['Unknown']))}
**Reasoning:** {rec.get('reasoning', 'No additional reasoning provided.')}

"""
        
        if proposal['conflicts']:
            content += f"""
---

## Conflicts Requiring Manual Review ({len(proposal['conflicts'])})

⚠️ **These recommendations may conflict with existing plans and require manual review.**

"""
            
            for i, rec in enumerate(proposal['conflicts'], 1):
                content += f"""#### {i}. {rec.get('title', 'Untitled')}

**Source:** {', '.join(rec.get('source_books', ['Unknown']))}
**Reasoning:** {rec.get('reasoning', 'No additional reasoning provided.')}

**Action Required:** Review this recommendation against existing Phase {proposal['phase']} plans and decide whether to:
- Accept the recommendation and update existing plans
- Reject the recommendation
- Modify the recommendation to align with existing plans

"""
        
        content += f"""
---

## Next Steps

1. **Review Conflicts** (if any)
   - Check each conflict carefully
   - Decide on resolution approach
   - Update plans as needed

2. **Verify Safe Updates**
   - Review automatically applied enhancements
   - Ensure they align with project goals
   - Adjust implementation details if needed

3. **Update Documentation**
   - Reflect changes in phase documentation
   - Update project timelines if needed
   - Communicate changes to team

---

*This proposal was generated by the Plan Override Manager.*
"""
        
        with open(output_path, 'w') as f:
            f.write(content)
    
    def get_changes_log(self) -> List[Dict[str, Any]]:
        """Get log of all changes made."""
        return self.changes_log.copy()
    
    def save_changes_log(self, output_path: str) -> None:
        """Save changes log to file."""
        with open(output_path, 'w') as f:
            json.dump(self.changes_log, f, indent=2)


def test_plan_override_manager():
    """Test the PlanOverrideManager functionality."""
    # Create test simulator directory
    test_simulator = "/tmp/test_simulator"
    os.makedirs(test_simulator, exist_ok=True)
    
    # Create test phase directory and plan
    phase_dir = os.path.join(test_simulator, "docs", "phases", "phase_5")
    os.makedirs(phase_dir, exist_ok=True)
    
    test_plan_content = """# Phase 5 - Machine Learning Models

## Current Plan
- Implement basic ML models
- Add model training pipeline
- Create prediction endpoints

## Implementation Tasks
- [ ] Set up ML framework
- [ ] Train initial models
- [ ] Deploy models
"""
    
    plan_file = os.path.join(phase_dir, "PHASE_5_INDEX.md")
    with open(plan_file, 'w') as f:
        f.write(test_plan_content)
    
    # Test manager
    manager = PlanOverrideManager(test_simulator)
    
    print("🧪 Testing PlanOverrideManager...")
    
    # Test recommendations
    test_recommendations = [
        {
            'title': 'Improve model training pipeline',
            'category': 'important',
            'source_books': ['Test Book'],
            'reasoning': 'Enhance existing training with better validation'
        },
        {
            'title': 'Add model versioning with MLflow',
            'category': 'critical',
            'source_books': ['Test Book'],
            'reasoning': 'Track models and enable rollbacks'
        },
        {
            'title': 'Replace ML framework with different approach',
            'category': 'critical',
            'source_books': ['Test Book'],
            'reasoning': 'Use different framework instead of current one'
        }
    ]
    
    # Analyze conflicts
    analysis = manager.analyze_plan_conflicts(5, test_recommendations)
    print(f"  Analysis: {len(analysis['conflicts'])} conflicts, {len(analysis['enhancements'])} enhancements, {len(analysis['new_additions'])} new")
    
    # Propose updates
    proposal = manager.propose_plan_updates(5, analysis)
    print(f"  Proposal: {proposal['safe_updates_count']} safe updates, {proposal['conflicts_count']} conflicts")
    
    # Apply safe updates
    results = manager.apply_safe_updates(5, proposal)
    print(f"  Applied: {results['applied']} updates, {results['pending']} pending")
    
    # Check changes log
    changes = manager.get_changes_log()
    print(f"  Changes logged: {len(changes)} entries")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_simulator)
    
    print("✅ PlanOverrideManager test completed!")


if __name__ == "__main__":
    test_plan_override_manager()