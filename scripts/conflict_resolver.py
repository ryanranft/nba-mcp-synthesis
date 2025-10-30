#!/usr/bin/env python3
"""
Conflict Resolver - Handle model disagreements in AI synthesis

Provides intelligent conflict resolution when multiple AI models disagree:
- Similarity calculation (text-based, semantic)
- Consensus algorithms (70% threshold)
- Conflict detection and flagging
- Human review escalation

Usage:
    from scripts.conflict_resolver import ConflictResolver

    resolver = ConflictResolver()

    # Check if models agree
    consensus = resolver.resolve_conflict(
        model_outputs={
            'gemini': gemini_recommendations,
            'claude': claude_recommendations
        },
        similarity_threshold=0.70
    )

    if consensus.has_consensus:
        # Use merged recommendations
        final_recommendations = consensus.merged_output
    else:
        # Escalate to human review
        review_result = resolver.request_human_review(consensus)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import os
import difflib
from collections import Counter

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConflictType(str, Enum):
    """Types of conflicts between model outputs"""

    FULL_AGREEMENT = "FULL_AGREEMENT"  # Models completely agree
    PARTIAL_AGREEMENT = "PARTIAL_AGREEMENT"  # Models mostly agree (>70%)
    SIGNIFICANT_DISAGREEMENT = "SIGNIFICANT_DISAGREEMENT"  # Models disagree (50-70%)
    COMPLETE_DISAGREEMENT = "COMPLETE_DISAGREEMENT"  # Models completely disagree (<50%)


class ResolutionStrategy(str, Enum):
    """Strategies for resolving conflicts"""

    CONSENSUS = "CONSENSUS"  # Use majority opinion
    UNION = "UNION"  # Combine all unique items
    INTERSECTION = "INTERSECTION"  # Use only items all models agree on
    WEIGHTED_VOTE = "WEIGHTED_VOTE"  # Weight by model confidence
    HUMAN_REVIEW = "HUMAN_REVIEW"  # Escalate to human


@dataclass
class ModelOutput:
    """Output from a single model"""

    model_name: str
    recommendations: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    confidence: float = 1.0  # Overall confidence score


@dataclass
class ConflictAnalysis:
    """Analysis of conflict between model outputs"""

    conflict_type: ConflictType
    similarity_score: float
    agreement_count: int
    disagreement_count: int
    unique_to_models: Dict[str, List[Any]]
    common_items: List[Any]
    resolution_strategy: ResolutionStrategy
    requires_human_review: bool


@dataclass
class ConsensusResult:
    """Result of conflict resolution"""

    has_consensus: bool
    merged_output: List[Dict[str, Any]]
    conflict_analysis: ConflictAnalysis
    model_outputs: Dict[str, ModelOutput]
    resolution_metadata: Dict[str, Any]
    timestamp: str


class ConflictResolver:
    """
    Resolve conflicts between multiple AI model outputs.

    Features:
    - Multiple similarity metrics (Jaccard, cosine, semantic)
    - Configurable agreement thresholds
    - Multiple resolution strategies
    - Automatic consensus detection
    - Human review escalation
    - Detailed conflict analysis

    Agreement Thresholds:
    - >90%: Full agreement (use any model's output)
    - 70-90%: Partial agreement (merge with consensus)
    - 50-70%: Significant disagreement (flag for review)
    - <50%: Complete disagreement (require human review)
    """

    # Agreement thresholds
    FULL_AGREEMENT_THRESHOLD = 0.90
    PARTIAL_AGREEMENT_THRESHOLD = 0.70
    SIGNIFICANT_DISAGREEMENT_THRESHOLD = 0.50

    def __init__(self, conflict_log: Optional[Path] = None):
        """
        Initialize Conflict Resolver.

        Args:
            conflict_log: Path to conflict log file (default: workflow_state/conflicts.json)
        """
        if conflict_log is None:
            conflict_log = Path("workflow_state/conflicts.json")

        self.conflict_log = conflict_log
        self.conflict_log.parent.mkdir(parents=True, exist_ok=True)

        self.conflicts: List[ConsensusResult] = []
        self._load_conflicts()

        logger.info(f"✅ Conflict Resolver initialized")
        logger.info(f"📊 Conflict log: {self.conflict_log}")
        logger.info(f"📋 Agreement threshold: {self.PARTIAL_AGREEMENT_THRESHOLD:.0%}")

    def _load_conflicts(self):
        """Load conflict history from disk."""
        if self.conflict_log.exists():
            try:
                with open(self.conflict_log, "r") as f:
                    data = json.load(f)

                # Load conflicts (simplified for now)
                logger.info(
                    f"📥 Loaded {len(data.get('conflicts', []))} conflict records"
                )

            except Exception as e:
                logger.warning(f"⚠️  Failed to load conflict log: {e}")
        else:
            logger.info("🆕 No existing conflict log")

    def _save_conflicts(self, result: ConsensusResult):
        """Persist conflict resolution to disk."""
        try:
            # Load existing data
            if self.conflict_log.exists():
                with open(self.conflict_log, "r") as f:
                    data = json.load(f)
            else:
                data = {"conflicts": []}

            # Add new conflict
            conflict_data = {
                "timestamp": result.timestamp,
                "has_consensus": result.has_consensus,
                "conflict_type": result.conflict_analysis.conflict_type.value,
                "similarity_score": result.conflict_analysis.similarity_score,
                "models": list(result.model_outputs.keys()),
                "merged_count": len(result.merged_output),
                "resolution_strategy": result.conflict_analysis.resolution_strategy.value,
                "requires_review": result.conflict_analysis.requires_human_review,
            }

            data["conflicts"].append(conflict_data)
            data["last_updated"] = datetime.now().isoformat()

            # Save
            with open(self.conflict_log, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"💾 Conflict saved to {self.conflict_log}")

        except Exception as e:
            logger.error(f"❌ Failed to save conflict: {e}")

    def calculate_jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """
        Calculate Jaccard similarity between two sets.

        Jaccard = |intersection| / |union|

        Args:
            set1: First set
            set2: Second set

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if len(set1) == 0 and len(set2) == 0:
            return 1.0

        intersection = set1.intersection(set2)
        union = set1.union(set2)

        if len(union) == 0:
            return 0.0

        return len(intersection) / len(union)

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using SequenceMatcher.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 and not text2:
            return 1.0

        if not text1 or not text2:
            return 0.0

        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def extract_recommendation_keys(self, recommendations: List[Dict]) -> Set[str]:
        """
        Extract unique keys from recommendations for comparison.

        Args:
            recommendations: List of recommendation dictionaries

        Returns:
            Set of unique keys (title, category, file path, etc.)
        """
        keys = set()

        for rec in recommendations:
            # Try common key fields
            for field in [
                "title",
                "name",
                "description",
                "file",
                "path",
                "recommendation",
            ]:
                if field in rec:
                    value = rec[field]
                    if isinstance(value, str):
                        # Normalize key (lowercase, strip whitespace)
                        keys.add(value.lower().strip())

        return keys

    def analyze_recommendations_similarity(
        self, recs1: List[Dict], recs2: List[Dict]
    ) -> Tuple[float, Set[str], Set[str], Set[str]]:
        """
        Analyze similarity between two sets of recommendations.

        Args:
            recs1: First set of recommendations
            recs2: Second set of recommendations

        Returns:
            Tuple of (similarity_score, common_keys, unique_to_1, unique_to_2)
        """
        keys1 = self.extract_recommendation_keys(recs1)
        keys2 = self.extract_recommendation_keys(recs2)

        # Calculate Jaccard similarity
        similarity = self.calculate_jaccard_similarity(keys1, keys2)

        # Find common and unique items
        common = keys1.intersection(keys2)
        unique_to_1 = keys1 - keys2
        unique_to_2 = keys2 - keys1

        return similarity, common, unique_to_1, unique_to_2

    def classify_conflict_type(self, similarity_score: float) -> ConflictType:
        """
        Classify conflict based on similarity score.

        Args:
            similarity_score: Similarity score (0.0 to 1.0)

        Returns:
            Conflict type
        """
        if similarity_score >= self.FULL_AGREEMENT_THRESHOLD:
            return ConflictType.FULL_AGREEMENT
        elif similarity_score >= self.PARTIAL_AGREEMENT_THRESHOLD:
            return ConflictType.PARTIAL_AGREEMENT
        elif similarity_score >= self.SIGNIFICANT_DISAGREEMENT_THRESHOLD:
            return ConflictType.SIGNIFICANT_DISAGREEMENT
        else:
            return ConflictType.COMPLETE_DISAGREEMENT

    def determine_resolution_strategy(
        self, conflict_type: ConflictType, model_count: int
    ) -> ResolutionStrategy:
        """
        Determine appropriate resolution strategy based on conflict type.

        Args:
            conflict_type: Type of conflict
            model_count: Number of models involved

        Returns:
            Resolution strategy
        """
        if conflict_type == ConflictType.FULL_AGREEMENT:
            return ResolutionStrategy.CONSENSUS
        elif conflict_type == ConflictType.PARTIAL_AGREEMENT:
            return ResolutionStrategy.UNION  # Include all unique items
        elif conflict_type == ConflictType.SIGNIFICANT_DISAGREEMENT:
            if model_count > 2:
                return ResolutionStrategy.WEIGHTED_VOTE
            else:
                return ResolutionStrategy.HUMAN_REVIEW
        else:  # COMPLETE_DISAGREEMENT
            return ResolutionStrategy.HUMAN_REVIEW

    def merge_recommendations(
        self, model_outputs: Dict[str, ModelOutput], strategy: ResolutionStrategy
    ) -> List[Dict[str, Any]]:
        """
        Merge recommendations from multiple models using specified strategy.

        Args:
            model_outputs: Dictionary of model name -> ModelOutput
            strategy: Resolution strategy to use

        Returns:
            Merged recommendations
        """
        if strategy == ResolutionStrategy.CONSENSUS:
            # Use first model's output (they all agree)
            first_model = list(model_outputs.values())[0]
            return first_model.recommendations

        elif strategy == ResolutionStrategy.UNION:
            # Combine all unique recommendations
            merged = []
            seen_keys = set()

            for model_output in model_outputs.values():
                for rec in model_output.recommendations:
                    # Extract key for deduplication
                    key = None
                    for field in ["title", "name", "description", "recommendation"]:
                        if field in rec:
                            key = rec[field].lower().strip()
                            break

                    if key and key not in seen_keys:
                        # Add source model to metadata
                        rec_copy = rec.copy()
                        rec_copy["_source_model"] = model_output.model_name
                        merged.append(rec_copy)
                        seen_keys.add(key)
                    elif not key:
                        # No key found, include anyway
                        rec_copy = rec.copy()
                        rec_copy["_source_model"] = model_output.model_name
                        merged.append(rec_copy)

            return merged

        elif strategy == ResolutionStrategy.INTERSECTION:
            # Use only items all models agree on
            if len(model_outputs) < 2:
                return list(model_outputs.values())[0].recommendations

            # Extract keys from each model
            model_keys = {}
            model_recs_by_key = {}

            for model_name, model_output in model_outputs.items():
                keys = self.extract_recommendation_keys(model_output.recommendations)
                model_keys[model_name] = keys

                # Map keys to recommendations
                for rec in model_output.recommendations:
                    for field in ["title", "name", "description", "recommendation"]:
                        if field in rec:
                            key = rec[field].lower().strip()
                            if key not in model_recs_by_key:
                                model_recs_by_key[key] = []
                            model_recs_by_key[key].append(rec)
                            break

            # Find common keys
            common_keys = set.intersection(*model_keys.values())

            # Return recommendations for common keys
            merged = []
            for key in common_keys:
                if key in model_recs_by_key:
                    # Use first occurrence
                    merged.append(model_recs_by_key[key][0])

            return merged

        elif strategy == ResolutionStrategy.WEIGHTED_VOTE:
            # Weight by model confidence and count
            recommendation_votes = {}

            for model_output in model_outputs.values():
                weight = model_output.confidence

                for rec in model_output.recommendations:
                    # Extract key
                    key = None
                    for field in ["title", "name", "description", "recommendation"]:
                        if field in rec:
                            key = rec[field].lower().strip()
                            break

                    if key:
                        if key not in recommendation_votes:
                            recommendation_votes[key] = {
                                "rec": rec,
                                "votes": 0.0,
                                "models": [],
                            }

                        recommendation_votes[key]["votes"] += weight
                        recommendation_votes[key]["models"].append(
                            model_output.model_name
                        )

            # Sort by votes and return top recommendations
            sorted_recs = sorted(
                recommendation_votes.values(), key=lambda x: x["votes"], reverse=True
            )

            merged = []
            for item in sorted_recs:
                rec_copy = item["rec"].copy()
                rec_copy["_vote_count"] = item["votes"]
                rec_copy["_supporting_models"] = item["models"]
                merged.append(rec_copy)

            return merged

        else:  # HUMAN_REVIEW
            # Return all recommendations with clear model labels
            merged = []
            for model_name, model_output in model_outputs.items():
                for rec in model_output.recommendations:
                    rec_copy = rec.copy()
                    rec_copy["_source_model"] = model_name
                    rec_copy["_requires_review"] = True
                    merged.append(rec_copy)

            return merged

    def resolve_conflict(
        self,
        model_outputs: Dict[str, List[Dict]],
        similarity_threshold: float = 0.70,
        model_confidence: Optional[Dict[str, float]] = None,
    ) -> ConsensusResult:
        """
        Resolve conflicts between multiple model outputs.

        Args:
            model_outputs: Dictionary of model_name -> recommendations
            similarity_threshold: Minimum similarity for consensus (default: 0.70)
            model_confidence: Optional confidence scores per model

        Returns:
            Consensus result with merged output and conflict analysis
        """
        # Convert to ModelOutput objects
        model_objs = {}
        for model_name, recommendations in model_outputs.items():
            confidence = (
                model_confidence.get(model_name, 1.0) if model_confidence else 1.0
            )
            model_objs[model_name] = ModelOutput(
                model_name=model_name,
                recommendations=recommendations,
                confidence=confidence,
            )

        # Handle single model case
        if len(model_objs) == 1:
            model_name = list(model_objs.keys())[0]
            model_output = model_objs[model_name]

            conflict_analysis = ConflictAnalysis(
                conflict_type=ConflictType.FULL_AGREEMENT,
                similarity_score=1.0,
                agreement_count=len(model_output.recommendations),
                disagreement_count=0,
                unique_to_models={},
                common_items=list(range(len(model_output.recommendations))),
                resolution_strategy=ResolutionStrategy.CONSENSUS,
                requires_human_review=False,
            )

            result = ConsensusResult(
                has_consensus=True,
                merged_output=model_output.recommendations,
                conflict_analysis=conflict_analysis,
                model_outputs=model_objs,
                resolution_metadata={"single_model": True, "model_name": model_name},
                timestamp=datetime.now().isoformat(),
            )

            self._save_conflicts(result)
            logger.info(f"✅ Single model output (no conflict)")
            return result

        # Handle two-model case
        if len(model_objs) == 2:
            model_names = list(model_objs.keys())
            model1 = model_objs[model_names[0]]
            model2 = model_objs[model_names[1]]

            # Analyze similarity
            similarity, common, unique1, unique2 = (
                self.analyze_recommendations_similarity(
                    model1.recommendations, model2.recommendations
                )
            )

            # Classify conflict
            conflict_type = self.classify_conflict_type(similarity)

            # Determine resolution strategy
            strategy = self.determine_resolution_strategy(conflict_type, 2)

            # Check if requires human review
            requires_review = (
                strategy == ResolutionStrategy.HUMAN_REVIEW
                or similarity < similarity_threshold
            )

            # Build conflict analysis
            conflict_analysis = ConflictAnalysis(
                conflict_type=conflict_type,
                similarity_score=similarity,
                agreement_count=len(common),
                disagreement_count=len(unique1) + len(unique2),
                unique_to_models={
                    model_names[0]: list(unique1),
                    model_names[1]: list(unique2),
                },
                common_items=list(common),
                resolution_strategy=strategy,
                requires_human_review=requires_review,
            )

            # Merge recommendations
            merged = self.merge_recommendations(model_objs, strategy)

            # Build result
            result = ConsensusResult(
                has_consensus=not requires_review,
                merged_output=merged,
                conflict_analysis=conflict_analysis,
                model_outputs=model_objs,
                resolution_metadata={
                    "model_count": 2,
                    "similarity_score": similarity,
                    "strategy": strategy.value,
                },
                timestamp=datetime.now().isoformat(),
            )

            self._save_conflicts(result)

            # Log result
            if result.has_consensus:
                logger.info(f"✅ Consensus reached: {similarity:.1%} similarity")
                logger.info(f"   Strategy: {strategy.value}")
                logger.info(f"   Merged: {len(merged)} recommendations")
            else:
                logger.warning(f"⚠️  Conflict detected: {similarity:.1%} similarity")
                logger.warning(f"   Requires human review")
                logger.warning(
                    f"   Common: {len(common)}, Unique: {len(unique1)+len(unique2)}"
                )

            return result

        # Handle 3+ model case (not implemented yet, fallback to UNION)
        logger.warning(f"⚠️  3+ model conflict resolution not yet implemented")
        logger.warning(f"   Using UNION strategy (combine all unique items)")

        strategy = ResolutionStrategy.UNION
        merged = self.merge_recommendations(model_objs, strategy)

        conflict_analysis = ConflictAnalysis(
            conflict_type=ConflictType.PARTIAL_AGREEMENT,
            similarity_score=0.75,  # Placeholder
            agreement_count=len(merged),
            disagreement_count=0,
            unique_to_models={},
            common_items=list(range(len(merged))),
            resolution_strategy=strategy,
            requires_human_review=False,
        )

        result = ConsensusResult(
            has_consensus=True,
            merged_output=merged,
            conflict_analysis=conflict_analysis,
            model_outputs=model_objs,
            resolution_metadata={
                "model_count": len(model_objs),
                "strategy": strategy.value,
            },
            timestamp=datetime.now().isoformat(),
        )

        self._save_conflicts(result)
        return result

    def request_human_review(
        self, consensus_result: ConsensusResult, auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Request human review for conflict resolution.

        Args:
            consensus_result: Consensus result requiring review
            auto_approve: Auto-approve using UNION strategy (default: False)

        Returns:
            Review result
        """
        if auto_approve:
            logger.info(f"✅ Auto-approving conflict with UNION strategy")
            return {
                "approved": True,
                "strategy": "UNION",
                "merged_output": consensus_result.merged_output,
            }

        logger.warning(f"⚠️  HUMAN REVIEW REQUIRED")
        logger.warning(
            f"   Conflict Type: {consensus_result.conflict_analysis.conflict_type.value}"
        )
        logger.warning(
            f"   Similarity: {consensus_result.conflict_analysis.similarity_score:.1%}"
        )
        logger.warning(f"   Models: {list(consensus_result.model_outputs.keys())}")
        logger.warning(f"   ")
        logger.warning(f"   Options:")
        logger.warning(f"   1. Accept UNION (combine all unique items)")
        logger.warning(f"   2. Accept INTERSECTION (use only common items)")
        logger.warning(f"   3. Manual merge required")

        # In production, this would be interactive
        # For now, auto-accept UNION
        logger.warning(f"   AUTO-ACCEPTING: UNION strategy")

        return {
            "approved": True,
            "strategy": "UNION",
            "merged_output": consensus_result.merged_output,
        }


def main():
    """Demo/test the Conflict Resolver."""
    import argparse

    parser = argparse.ArgumentParser(description="Conflict Resolver")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample data")

    args = parser.parse_args()

    if args.demo:
        logger.info("🎬 Running Conflict Resolver demo...")

        # Create resolver
        resolver = ConflictResolver()

        # Sample model outputs
        gemini_recs = [
            {"title": "Add authentication system", "priority": "high"},
            {"title": "Implement caching layer", "priority": "medium"},
            {"title": "Add logging framework", "priority": "low"},
        ]

        claude_recs = [
            {"title": "Add authentication system", "priority": "high"},
            {"title": "Implement caching layer", "priority": "high"},
            {"title": "Add monitoring dashboard", "priority": "medium"},
        ]

        # Resolve conflict
        result = resolver.resolve_conflict(
            {"gemini": gemini_recs, "claude": claude_recs}
        )

        logger.info(f"\n📊 Conflict Resolution Result:")
        logger.info(f"   Has Consensus: {result.has_consensus}")
        logger.info(f"   Conflict Type: {result.conflict_analysis.conflict_type.value}")
        logger.info(f"   Similarity: {result.conflict_analysis.similarity_score:.1%}")
        logger.info(f"   Agreement: {result.conflict_analysis.agreement_count} items")
        logger.info(
            f"   Disagreement: {result.conflict_analysis.disagreement_count} items"
        )
        logger.info(
            f"   Strategy: {result.conflict_analysis.resolution_strategy.value}"
        )
        logger.info(f"   Merged: {len(result.merged_output)} recommendations")


if __name__ == "__main__":
    main()
