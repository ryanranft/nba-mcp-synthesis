#!/usr/bin/env python3
"""
Phase 3.5: AI-Driven Plan Modification

Analyzes implementation plans and automatically suggests/applies modifications
based on Phase 3 synthesis outputs and project context.

Features:
- Detects obsolete sections that are no longer needed
- Identifies duplicate sections that should be merged
- Proposes new sections based on synthesis recommendations
- Modifies existing sections to incorporate new insights
- Requires approval for high-impact changes
- Tracks costs and provides rollback support

Usage:
    # Analyze plan and suggest modifications (dry-run)
    python scripts/phase3_5_ai_plan_modification.py plan.md --dry-run

    # Apply modifications with auto-approval for low-impact changes
    python scripts/phase3_5_ai_plan_modification.py plan.md --auto-approve-low-impact

    # Apply modifications with manual approval for all changes
    python scripts/phase3_5_ai_plan_modification.py plan.md

    # Use specific synthesis output
    python scripts/phase3_5_ai_plan_modification.py plan.md --synthesis implementation_plans/consolidated_recommendations.json

    # Apply only specific modification types
    python scripts/phase3_5_ai_plan_modification.py plan.md --only add,modify
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from intelligent_plan_editor import IntelligentPlanEditor, PlanSection
from phase_status_manager import PhaseStatusManager
from cost_safety_manager import CostSafetyManager
from conflict_resolver import ConflictResolver

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PlanModificationProposal:
    """Proposal for modifying a plan."""

    operation: str  # ADD, MODIFY, DELETE, MERGE
    section_id: Optional[str] = None  # For MODIFY, DELETE, MERGE
    section_id_2: Optional[str] = None  # For MERGE (second section)
    title: Optional[str] = None  # For ADD
    content: Optional[str] = None  # For ADD, MODIFY
    rationale: str = ""
    confidence: float = 0.0  # 0.0-1.0
    impact: str = "low"  # low, medium, high
    source_recommendations: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def requires_approval(self, auto_approve_threshold: float = 0.8) -> bool:
        """Determine if this modification requires manual approval."""
        # High-impact always requires approval
        if self.impact == "high":
            return True

        # Medium-impact requires approval if confidence is low
        if self.impact == "medium" and self.confidence < auto_approve_threshold:
            return True

        # Low-impact only requires approval if confidence is very low
        if self.impact == "low" and self.confidence < 0.6:
            return True

        return False


class Phase3_5_AIModification:
    """
    AI-driven plan modification system.

    Analyzes implementation plans and suggests/applies modifications
    based on synthesis recommendations and project context.
    """

    def __init__(
        self,
        plan_path: Path,
        synthesis_path: Optional[Path] = None,
        auto_approve_low_impact: bool = False,
        dry_run: bool = False,
    ):
        """
        Initialize Phase 3.5 AI modification system.

        Args:
            plan_path: Path to implementation plan to modify
            synthesis_path: Path to synthesis recommendations (default: implementation_plans/consolidated_recommendations.json)
            auto_approve_low_impact: Auto-approve low-impact changes without prompting
            dry_run: Preview modifications without applying them
        """
        self.plan_path = Path(plan_path)
        self.synthesis_path = synthesis_path or Path(
            "implementation_plans/consolidated_recommendations.json"
        )
        self.auto_approve_low_impact = auto_approve_low_impact
        self.dry_run = dry_run

        # Initialize managers
        self.editor = IntelligentPlanEditor(str(self.plan_path))
        self.status_mgr = PhaseStatusManager()
        self.cost_mgr = CostSafetyManager()
        self.conflict_resolver = ConflictResolver()

        # Track proposals
        self.proposals: List[PlanModificationProposal] = []
        self.applied_modifications: List[Dict] = []
        self.rejected_modifications: List[Dict] = []

        logger.info("🤖 Phase 3.5: AI-Driven Plan Modification")
        logger.info(f"   Plan: {self.plan_path}")
        logger.info(f"   Synthesis: {self.synthesis_path}")
        logger.info(f"   Mode: {'DRY RUN' if dry_run else 'APPLY'}")
        logger.info(f"   Auto-approve low-impact: {auto_approve_low_impact}")

    def load_synthesis_recommendations(self) -> List[Dict]:
        """Load recommendations from Phase 3 synthesis."""
        if not self.synthesis_path.exists():
            logger.warning(f"⚠️  Synthesis file not found: {self.synthesis_path}")
            logger.warning("   Run Phase 3 consolidation first")
            return []

        try:
            with open(self.synthesis_path, "r") as f:
                data = json.load(f)

            recommendations = data.get("recommendations", [])
            logger.info(
                f"✅ Loaded {len(recommendations)} recommendations from synthesis"
            )
            return recommendations

        except Exception as e:
            logger.error(f"❌ Error loading synthesis: {e}")
            return []

    def analyze_plan_for_obsolete_sections(
        self, sections: List[PlanSection]
    ) -> List[PlanModificationProposal]:
        """
        Analyze plan to detect potentially obsolete sections.

        Heuristics for obsolete detection:
        - Sections marked as "TODO" or "PLACEHOLDER" in title
        - Sections with "deprecated" or "obsolete" in content
        - Empty sections (no content beyond title)
        - Sections referencing old technologies or approaches
        """
        proposals = []

        obsolete_keywords = [
            "todo",
            "placeholder",
            "deprecated",
            "obsolete",
            "to be removed",
            "legacy",
            "old approach",
        ]

        for section in sections:
            # Check title for obsolete keywords
            title_lower = section.title.lower()
            if any(kw in title_lower for kw in ["todo", "placeholder"]):
                proposals.append(
                    PlanModificationProposal(
                        operation="DELETE",
                        section_id=section.id,
                        rationale=f"Section appears to be a placeholder: '{section.title}'",
                        confidence=0.7,
                        impact="low",
                        metadata={"reason": "placeholder_detection"},
                    )
                )
                continue

            # Check for deprecated/obsolete in content
            content_lower = section.content.lower()
            if any(
                kw in content_lower
                for kw in ["deprecated", "obsolete", "to be removed"]
            ):
                proposals.append(
                    PlanModificationProposal(
                        operation="DELETE",
                        section_id=section.id,
                        rationale=f"Section marked as deprecated/obsolete in content",
                        confidence=0.85,
                        impact="medium",
                        metadata={"reason": "explicit_deprecation"},
                    )
                )
                continue

            # Check for empty sections
            if len(section.content.strip()) == 0:
                proposals.append(
                    PlanModificationProposal(
                        operation="DELETE",
                        section_id=section.id,
                        rationale=f"Empty section with no content",
                        confidence=0.9,
                        impact="low",
                        metadata={"reason": "empty_section"},
                    )
                )

        return proposals

    def analyze_plan_for_duplicates(
        self, sections: List[PlanSection], threshold: float = 0.8
    ) -> List[PlanModificationProposal]:
        """
        Analyze plan to detect duplicate sections that should be merged.

        Uses the IntelligentPlanEditor's find_duplicate_sections method.
        """
        proposals = []

        duplicates = self.editor.find_duplicate_sections(similarity_threshold=threshold)

        for sec1, sec2, similarity in duplicates:
            proposals.append(
                PlanModificationProposal(
                    operation="MERGE",
                    section_id=sec1.id,
                    section_id_2=sec2.id,
                    rationale=f"Sections are {similarity:.0%} similar and should be merged: '{sec1.title}' and '{sec2.title}'",
                    confidence=similarity,
                    impact="medium" if similarity > 0.9 else "low",
                    metadata={
                        "similarity": similarity,
                        "merge_strategy": "smart" if similarity > 0.85 else "union",
                    },
                )
            )

        return proposals

    def analyze_synthesis_for_new_sections(
        self, recommendations: List[Dict], existing_sections: List[PlanSection]
    ) -> List[PlanModificationProposal]:
        """
        Analyze synthesis recommendations to propose new plan sections.

        Maps recommendations to potential new sections based on:
        - Priority (critical recommendations → high-priority sections)
        - Category (similar recommendations grouped together)
        - Gaps in existing plan (recommendations not covered by current sections)
        """
        proposals = []

        # Group recommendations by category/theme
        critical_recs = [r for r in recommendations if r.get("priority") == "critical"]
        important_recs = [
            r for r in recommendations if r.get("priority") == "important"
        ]

        # Check if recommendations are already covered by existing sections
        existing_titles = {s.title.lower() for s in existing_sections}
        existing_content = " ".join(s.content.lower() for s in existing_sections)

        # Propose sections for critical recommendations not yet covered
        for rec in critical_recs[:5]:  # Limit to top 5 critical
            rec_title = rec.get("title", "")
            rec_desc = rec.get("description", "")

            # Skip if already covered (title match or keywords in content)
            if rec_title.lower() in existing_titles:
                continue

            # Check if keywords appear in existing content
            rec_keywords = set(rec_title.lower().split())
            if (
                len(rec_keywords.intersection(existing_content.split()))
                > len(rec_keywords) * 0.7
            ):
                continue

            # Propose new section
            proposals.append(
                PlanModificationProposal(
                    operation="ADD",
                    title=f"Implementation: {rec_title}",
                    content=f"{rec_desc}\n\n**Source:** {rec.get('source_book', 'Unknown')}\n**Priority:** Critical",
                    rationale=f"Critical recommendation from synthesis not covered in current plan",
                    confidence=0.75,
                    impact="high",
                    source_recommendations=[rec],
                    metadata={
                        "position": "end",
                        "level": 2,
                        "source_book": rec.get("source_book"),
                    },
                )
            )

        # Propose sections for important recommendations (lower confidence)
        for rec in important_recs[:3]:  # Limit to top 3 important
            rec_title = rec.get("title", "")
            rec_desc = rec.get("description", "")

            if rec_title.lower() in existing_titles:
                continue

            proposals.append(
                PlanModificationProposal(
                    operation="ADD",
                    title=f"Enhancement: {rec_title}",
                    content=f"{rec_desc}\n\n**Source:** {rec.get('source_book', 'Unknown')}\n**Priority:** Important",
                    rationale=f"Important recommendation from synthesis",
                    confidence=0.65,
                    impact="medium",
                    source_recommendations=[rec],
                    metadata={
                        "position": "end",
                        "level": 2,
                        "source_book": rec.get("source_book"),
                    },
                )
            )

        return proposals

    def analyze_synthesis_for_section_enhancements(
        self, recommendations: List[Dict], existing_sections: List[PlanSection]
    ) -> List[PlanModificationProposal]:
        """
        Analyze synthesis to propose enhancements to existing sections.

        Finds recommendations that relate to existing sections and proposes
        adding relevant information to those sections.
        """
        proposals = []

        for section in existing_sections:
            section_keywords = set(section.title.lower().split())

            # Find recommendations that match this section's keywords
            related_recs = []
            for rec in recommendations:
                rec_keywords = set(rec.get("title", "").lower().split())

                # Check keyword overlap
                overlap = len(section_keywords.intersection(rec_keywords))
                if overlap >= 2 or (overlap == 1 and len(section_keywords) <= 3):
                    related_recs.append(rec)

            # If we found related recommendations, propose enhancement
            if related_recs:
                enhancement_content = "\n\n**Related Insights:**\n"
                for rec in related_recs[:3]:  # Limit to top 3
                    enhancement_content += (
                        f"- {rec.get('title')}: {rec.get('description', '')[:100]}...\n"
                    )

                proposals.append(
                    PlanModificationProposal(
                        operation="MODIFY",
                        section_id=section.id,
                        content=enhancement_content,
                        rationale=f"Adding insights from {len(related_recs)} related recommendations",
                        confidence=0.7,
                        impact="low",
                        source_recommendations=related_recs[:3],
                        metadata={"modification_type": "append"},
                    )
                )

        return proposals

    def generate_proposals(
        self, operation_types: Optional[List[str]] = None
    ) -> List[PlanModificationProposal]:
        """
        Generate all modification proposals.

        Args:
            operation_types: List of operations to include (ADD, MODIFY, DELETE, MERGE)
                           If None, includes all types

        Returns:
            List of modification proposals
        """
        logger.info("\n" + "=" * 60)
        logger.info("ANALYZING PLAN FOR MODIFICATIONS")
        logger.info("=" * 60 + "\n")

        operation_types = operation_types or ["ADD", "MODIFY", "DELETE", "MERGE"]
        operation_types = [op.upper() for op in operation_types]

        # Load plan structure
        sections = self.editor.parse_plan_structure()
        logger.info(f"✅ Parsed plan: {len(sections)} sections")

        # Load synthesis recommendations
        recommendations = self.load_synthesis_recommendations()

        proposals = []

        # Detect obsolete sections
        if "DELETE" in operation_types:
            logger.info("\n🔍 Analyzing for obsolete sections...")
            obsolete_proposals = self.analyze_plan_for_obsolete_sections(sections)
            proposals.extend(obsolete_proposals)
            logger.info(f"   Found {len(obsolete_proposals)} obsolete section(s)")

        # Detect duplicates
        if "MERGE" in operation_types:
            logger.info("\n🔍 Analyzing for duplicate sections...")
            duplicate_proposals = self.analyze_plan_for_duplicates(sections)
            proposals.extend(duplicate_proposals)
            logger.info(f"   Found {len(duplicate_proposals)} duplicate pair(s)")

        # Propose new sections from synthesis
        if "ADD" in operation_types and recommendations:
            logger.info("\n🔍 Analyzing synthesis for new sections...")
            new_section_proposals = self.analyze_synthesis_for_new_sections(
                recommendations, sections
            )
            proposals.extend(new_section_proposals)
            logger.info(f"   Proposed {len(new_section_proposals)} new section(s)")

        # Propose enhancements to existing sections
        if "MODIFY" in operation_types and recommendations:
            logger.info("\n🔍 Analyzing synthesis for section enhancements...")
            enhancement_proposals = self.analyze_synthesis_for_section_enhancements(
                recommendations, sections
            )
            proposals.extend(enhancement_proposals)
            logger.info(f"   Proposed {len(enhancement_proposals)} enhancement(s)")

        self.proposals = proposals
        logger.info(f"\n✅ Generated {len(proposals)} total proposal(s)")

        return proposals

    def display_proposal(self, proposal: PlanModificationProposal, index: int):
        """Display a single proposal in a readable format."""
        print(f"\n{'=' * 60}")
        print(f"PROPOSAL #{index + 1}: {proposal.operation}")
        print(f"{'=' * 60}")
        print(f"Confidence: {proposal.confidence:.0%}")
        print(f"Impact: {proposal.impact.upper()}")
        print(f"Rationale: {proposal.rationale}")

        if proposal.operation == "DELETE":
            print(f"Section to delete: {proposal.section_id}")

        elif proposal.operation == "MERGE":
            print(f"Merge: {proposal.section_id}")
            print(f"  With: {proposal.section_id_2}")
            print(f"Strategy: {proposal.metadata.get('merge_strategy', 'smart')}")

        elif proposal.operation == "ADD":
            print(f"New section title: {proposal.title}")
            print(f"Content preview: {proposal.content[:150]}...")

        elif proposal.operation == "MODIFY":
            print(f"Section to modify: {proposal.section_id}")
            print(
                f"Modification type: {proposal.metadata.get('modification_type', 'append')}"
            )
            print(f"Content to add: {proposal.content[:150]}...")

        print(f"{'=' * 60}")

    def request_approval(self, proposal: PlanModificationProposal, index: int) -> bool:
        """
        Request manual approval for a proposal.

        Returns:
            True if approved, False if rejected
        """
        self.display_proposal(proposal, index)

        print("\nOptions:")
        print("  [y] Approve this modification")
        print("  [n] Reject this modification")
        print("  [s] Skip (don't apply, but don't reject)")
        print("  [a] Approve all remaining proposals")
        print("  [q] Quit (reject all remaining proposals)")

        while True:
            choice = input("\nYour choice: ").lower().strip()

            if choice == "y":
                return True
            elif choice == "n":
                return False
            elif choice == "s":
                return False  # Same as reject for now
            elif choice == "a":
                # Set flag to auto-approve all remaining
                self.auto_approve_low_impact = True
                return True
            elif choice == "q":
                logger.info("❌ User quit - rejecting all remaining proposals")
                raise KeyboardInterrupt("User requested quit")
            else:
                print("Invalid choice. Please enter y, n, s, a, or q.")

    def apply_proposal(self, proposal: PlanModificationProposal) -> bool:
        """
        Apply a single modification proposal.

        Returns:
            True if successfully applied, False otherwise
        """
        try:
            if proposal.operation == "DELETE":
                self.editor.delete_obsolete_plan(
                    section_id=proposal.section_id,
                    rationale=proposal.rationale,
                    source="ai",
                    confidence=proposal.confidence,
                    cascade=False,
                    archive=True,
                )

            elif proposal.operation == "MERGE":
                self.editor.merge_duplicate_plans(
                    section_id_1=proposal.section_id,
                    section_id_2=proposal.section_id_2,
                    merge_strategy=proposal.metadata.get("merge_strategy", "smart"),
                    keep_section="first",
                    rationale=proposal.rationale,
                    source="ai",
                    confidence=proposal.confidence,
                )

            elif proposal.operation == "ADD":
                self.editor.add_new_plan(
                    title=proposal.title,
                    content=proposal.content,
                    position=proposal.metadata.get("position", "end"),
                    level=proposal.metadata.get("level", 2),
                    rationale=proposal.rationale,
                    source="ai",
                    confidence=proposal.confidence,
                )

            elif proposal.operation == "MODIFY":
                mod_type = proposal.metadata.get("modification_type", "append")

                if mod_type == "append":
                    self.editor.modify_existing_plan(
                        section_id=proposal.section_id,
                        append_content=proposal.content,
                        rationale=proposal.rationale,
                        source="ai",
                        confidence=proposal.confidence,
                    )
                else:
                    self.editor.modify_existing_plan(
                        section_id=proposal.section_id,
                        new_content=proposal.content,
                        rationale=proposal.rationale,
                        source="ai",
                        confidence=proposal.confidence,
                    )

            return True

        except Exception as e:
            logger.error(f"❌ Error applying {proposal.operation}: {e}")
            return False

    def execute_modifications(
        self, proposals: Optional[List[PlanModificationProposal]] = None
    ) -> Dict:
        """
        Execute all approved modifications.

        Args:
            proposals: List of proposals to execute (uses self.proposals if None)

        Returns:
            Summary dictionary with applied/rejected counts
        """
        proposals = proposals or self.proposals

        if not proposals:
            logger.info("ℹ️  No proposals to execute")
            return {"applied": 0, "rejected": 0, "skipped": 0}

        logger.info("\n" + "=" * 60)
        logger.info("EXECUTING MODIFICATIONS")
        logger.info("=" * 60 + "\n")

        if self.dry_run:
            logger.info("🔍 DRY RUN - Previewing modifications without applying\n")
            for i, proposal in enumerate(proposals):
                self.display_proposal(proposal, i)

            return {
                "applied": 0,
                "rejected": 0,
                "skipped": len(proposals),
                "dry_run": True,
            }

        # Track phase status
        self.status_mgr.start_phase(
            "phase_3_5_modifications",
            metadata={
                "plan_path": str(self.plan_path),
                "total_proposals": len(proposals),
            },
        )

        applied_count = 0
        rejected_count = 0

        try:
            for i, proposal in enumerate(proposals):
                # Determine if approval is needed
                needs_approval = proposal.requires_approval(auto_approve_threshold=0.8)

                # Auto-approve if configured and low-impact
                if self.auto_approve_low_impact and not needs_approval:
                    logger.info(
                        f"✅ Auto-approving {proposal.operation} (confidence: {proposal.confidence:.0%}, impact: {proposal.impact})"
                    )
                    approved = True

                # Request manual approval
                elif needs_approval or not self.auto_approve_low_impact:
                    approved = self.request_approval(proposal, i)

                else:
                    approved = True

                # Apply if approved
                if approved:
                    logger.info(f"⏳ Applying {proposal.operation}...")

                    # Check cost limit (estimate $0.01 per modification)
                    if not self.cost_mgr.check_cost_limit(
                        "phase_3_5_modifications", 0.01
                    ):
                        logger.error("❌ Cost limit exceeded - stopping modifications")
                        rejected_count += len(proposals) - i
                        break

                    success = self.apply_proposal(proposal)

                    if success:
                        logger.info(f"✅ Successfully applied {proposal.operation}")
                        applied_count += 1
                        self.applied_modifications.append(
                            {
                                "operation": proposal.operation,
                                "timestamp": datetime.now().isoformat(),
                                "rationale": proposal.rationale,
                            }
                        )

                        # Record minimal cost
                        self.cost_mgr.record_cost(
                            "phase_3_5_modifications",
                            0.01,
                            model="heuristic_analysis",
                            operation=proposal.operation,
                        )
                    else:
                        logger.error(f"❌ Failed to apply {proposal.operation}")
                        rejected_count += 1
                        self.rejected_modifications.append(
                            {
                                "operation": proposal.operation,
                                "reason": "application_failed",
                            }
                        )
                else:
                    logger.info(f"⏭️  Rejected {proposal.operation}")
                    rejected_count += 1
                    self.rejected_modifications.append(
                        {"operation": proposal.operation, "reason": "user_rejected"}
                    )

            # Complete phase successfully
            self.status_mgr.complete_phase(
                "phase_3_5_modifications",
                metadata={"applied": applied_count, "rejected": rejected_count},
            )

        except KeyboardInterrupt:
            logger.info("\n⚠️  User interrupted - marking phase as needs rerun")
            self.status_mgr.mark_needs_rerun(
                "phase_3_5_modifications", "User interrupted"
            )
            rejected_count += len(proposals) - applied_count

        except Exception as e:
            logger.error(f"\n❌ Error during execution: {e}")
            self.status_mgr.fail_phase("phase_3_5_modifications", str(e))
            rejected_count += len(proposals) - applied_count

        logger.info(f"\n{'=' * 60}")
        logger.info(f"SUMMARY: {applied_count} applied, {rejected_count} rejected")
        logger.info(f"{'=' * 60}\n")

        return {"applied": applied_count, "rejected": rejected_count, "skipped": 0}

    def generate_report(self, summary: Dict) -> str:
        """Generate a summary report of modifications."""
        report = []
        report.append("=" * 60)
        report.append("PHASE 3.5: AI PLAN MODIFICATION REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Plan: {self.plan_path}")
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Mode: {'DRY RUN' if self.dry_run else 'APPLIED'}")
        report.append("")
        report.append("SUMMARY:")
        report.append(f"  Total proposals: {len(self.proposals)}")
        report.append(f"  Applied: {summary['applied']}")
        report.append(f"  Rejected: {summary['rejected']}")
        report.append(f"  Skipped: {summary.get('skipped', 0)}")
        report.append("")

        if self.applied_modifications:
            report.append("APPLIED MODIFICATIONS:")
            for mod in self.applied_modifications:
                report.append(f"  - {mod['operation']}: {mod['rationale']}")
            report.append("")

        if self.rejected_modifications:
            report.append("REJECTED MODIFICATIONS:")
            for mod in self.rejected_modifications:
                report.append(f"  - {mod['operation']}: {mod.get('reason', 'unknown')}")
            report.append("")

        # Cost summary
        total_cost = self.cost_mgr.get_phase_cost("phase_3_5_modifications")
        report.append(f"COST: ${total_cost:.2f}")
        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 3.5: AI-Driven Plan Modification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "plan_path", type=str, help="Path to implementation plan to modify"
    )

    parser.add_argument(
        "--synthesis",
        type=str,
        default="implementation_plans/consolidated_recommendations.json",
        help="Path to synthesis recommendations (default: implementation_plans/consolidated_recommendations.json)",
    )

    parser.add_argument(
        "--auto-approve-low-impact",
        action="store_true",
        help="Auto-approve low-impact modifications without prompting",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview modifications without applying them",
    )

    parser.add_argument(
        "--only",
        type=str,
        help="Only apply specific operation types (comma-separated: add,modify,delete,merge)",
    )

    args = parser.parse_args()

    # Parse operation types
    operation_types = None
    if args.only:
        operation_types = [op.strip().upper() for op in args.only.split(",")]
        valid_ops = ["ADD", "MODIFY", "DELETE", "MERGE"]
        for op in operation_types:
            if op not in valid_ops:
                logger.error(
                    f"Invalid operation type: {op}. Valid: {', '.join(valid_ops)}"
                )
                return 1

    # Initialize modifier
    modifier = Phase3_5_AIModification(
        plan_path=Path(args.plan_path),
        synthesis_path=Path(args.synthesis) if args.synthesis else None,
        auto_approve_low_impact=args.auto_approve_low_impact,
        dry_run=args.dry_run,
    )

    # Generate proposals
    proposals = modifier.generate_proposals(operation_types=operation_types)

    if not proposals:
        logger.info("✅ No modifications needed - plan is up to date")
        return 0

    # Execute modifications
    summary = modifier.execute_modifications(proposals)

    # Generate report
    report = modifier.generate_report(summary)
    print("\n" + report)

    # Save report to file
    report_path = Path(f"phase3_5_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    report_path.write_text(report)
    logger.info(f"\n📄 Report saved to: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
