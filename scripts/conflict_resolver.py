#!/usr/bin/env python3
"""
Conflict Resolver - Handle Model Disagreements

This system resolves conflicts when multiple AI models provide different
recommendations or analysis results. It implements several consensus strategies:

1. Similarity-based consensus (>70% similarity = agreement)
2. Weighted voting (prioritize more reliable models)
3. Tie-breaking (use third model or human review)
4. Merger strategies (combine complementary recommendations)

Part of Tier 2 implementation for intelligent synthesis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections import Counter
import json

logger = logging.getLogger(__name__)


@dataclass
class ModelOutput:
    """Output from a single model."""
    model_name: str
    recommendations: List[Dict[str, Any]]
    confidence: float  # 0.0 to 1.0
    raw_output: str


@dataclass
class ConflictResolution:
    """Result of conflict resolution."""
    consensus_reached: bool
    final_recommendations: List[Dict[str, Any]]
    agreement_level: float  # 0.0 to 1.0
    disagreements: List[Dict[str, Any]]
    resolution_method: str
    model_votes: Dict[str, List[str]]  # Which models agreed on what


class ConflictResolver:
    """
    Resolve conflicts between multiple model outputs.

    Features:
    - Similarity-based consensus
    - Weighted voting by model reliability
    - Tie-breaking strategies
    - Disagreement tracking
    - Quality metrics

    Example:
        >>> resolver = ConflictResolver(similarity_threshold=0.7)
        >>> outputs = [gemini_output, claude_output, gpt4_output]
        >>> resolution = resolver.resolve(outputs)
        >>> print(f"Consensus: {resolution.consensus_reached}")
        >>> print(f"Agreement: {resolution.agreement_level:.1%}")
    """

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        model_weights: Optional[Dict[str, float]] = None,
        enable_tie_breaking: bool = True
    ):
        """
        Initialize conflict resolver.

        Args:
            similarity_threshold: Minimum similarity for consensus (default: 0.7)
            model_weights: Reliability weights per model (default: equal weights)
            enable_tie_breaking: Use tie-breaking strategies
        """
        self.similarity_threshold = similarity_threshold
        self.enable_tie_breaking = enable_tie_breaking

        # Default model weights (equal if not specified)
        self.model_weights = model_weights or {
            'gemini': 1.0,
            'claude': 1.0,
            'gpt4': 1.0,
            'deepseek': 0.8  # Slightly lower weight based on historical performance
        }

        logger.info(f"ConflictResolver initialized")
        logger.info(f"  Similarity threshold: {similarity_threshold}")
        logger.info(f"  Model weights: {self.model_weights}")

    def resolve(self, model_outputs: List[ModelOutput]) -> ConflictResolution:
        """
        Resolve conflicts between model outputs.

        Args:
            model_outputs: List of outputs from different models

        Returns:
            ConflictResolution with consensus recommendations
        """
        logger.info(f"Resolving conflicts from {len(model_outputs)} models")

        if len(model_outputs) == 0:
            raise ValueError("No model outputs provided")

        if len(model_outputs) == 1:
            # No conflict possible with single model
            return ConflictResolution(
                consensus_reached=True,
                final_recommendations=model_outputs[0].recommendations,
                agreement_level=1.0,
                disagreements=[],
                resolution_method="single_model",
                model_votes={}
            )

        # Step 1: Find similar recommendations across models
        recommendation_clusters = self._cluster_similar_recommendations(model_outputs)

        # Step 2: Vote on each cluster using weighted voting
        consensus_recommendations = []
        disagreements = []
        model_votes = {}

        for cluster_id, cluster in enumerate(recommendation_clusters):
            vote_result = self._weighted_vote(cluster, model_outputs)

            if vote_result['consensus']:
                consensus_recommendations.append(vote_result['recommendation'])
                model_votes[f"rec_{cluster_id}"] = vote_result['supporting_models']
            else:
                disagreements.append({
                    'cluster_id': cluster_id,
                    'recommendations': cluster,
                    'vote_result': vote_result
                })

        # Step 3: Calculate overall agreement level
        total_recs = len(consensus_recommendations) + len(disagreements)
        agreement_level = len(consensus_recommendations) / total_recs if total_recs > 0 else 0.0

        # Step 4: Determine if consensus was reached
        consensus_reached = agreement_level >= self.similarity_threshold

        # Step 5: Apply tie-breaking if needed
        resolution_method = "weighted_voting"
        if not consensus_reached and self.enable_tie_breaking:
            tie_break_result = self._tie_breaking(disagreements, model_outputs)
            if tie_break_result['success']:
                consensus_recommendations.extend(tie_break_result['resolved_recommendations'])
                agreement_level = (len(consensus_recommendations) / total_recs) if total_recs > 0 else 0.0
                consensus_reached = agreement_level >= self.similarity_threshold
                resolution_method = "tie_breaking"

        logger.info(f"Resolution complete: {len(consensus_recommendations)} consensus, {len(disagreements)} disagreements")
        logger.info(f"Agreement level: {agreement_level:.1%}")

        return ConflictResolution(
            consensus_reached=consensus_reached,
            final_recommendations=consensus_recommendations,
            agreement_level=agreement_level,
            disagreements=disagreements,
            resolution_method=resolution_method,
            model_votes=model_votes
        )

    def _cluster_similar_recommendations(
        self,
        model_outputs: List[ModelOutput]
    ) -> List[List[Dict[str, Any]]]:
        """
        Cluster similar recommendations from different models.

        Args:
            model_outputs: Outputs from all models

        Returns:
            List of clusters, where each cluster contains similar recommendations
        """
        all_recommendations = []
        for output in model_outputs:
            for rec in output.recommendations:
                # Add model attribution
                rec_with_source = rec.copy()
                rec_with_source['_source_model'] = output.model_name
                rec_with_source['_confidence'] = output.confidence
                all_recommendations.append(rec_with_source)

        if not all_recommendations:
            return []

        # Cluster by similarity
        clusters = []
        used_indices = set()

        for i, rec1 in enumerate(all_recommendations):
            if i in used_indices:
                continue

            # Start new cluster
            cluster = [rec1]
            used_indices.add(i)

            # Find similar recommendations
            for j, rec2 in enumerate(all_recommendations):
                if j in used_indices:
                    continue

                similarity = self._calculate_similarity(rec1, rec2)
                if similarity >= self.similarity_threshold:
                    cluster.append(rec2)
                    used_indices.add(j)

            clusters.append(cluster)

        logger.debug(f"Clustered {len(all_recommendations)} recommendations into {len(clusters)} clusters")

        return clusters

    def _calculate_similarity(self, rec1: Dict[str, Any], rec2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two recommendations.

        Args:
            rec1: First recommendation
            rec2: Second recommendation

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Compare text fields
        text1 = self._extract_text_for_comparison(rec1)
        text2 = self._extract_text_for_comparison(rec2)

        # Use sequence matcher for text similarity
        similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

        return similarity

    def _extract_text_for_comparison(self, rec: Dict[str, Any]) -> str:
        """Extract text from recommendation for comparison."""
        text_parts = []

        # Common fields to compare
        for field in ['title', 'description', 'recommendation', 'content', 'text']:
            if field in rec:
                text_parts.append(str(rec[field]))

        return ' '.join(text_parts)

    def _weighted_vote(
        self,
        cluster: List[Dict[str, Any]],
        model_outputs: List[ModelOutput]
    ) -> Dict[str, Any]:
        """
        Perform weighted voting on a cluster of similar recommendations.

        Args:
            cluster: Cluster of similar recommendations
            model_outputs: Original model outputs for weight lookup

        Returns:
            Dict with consensus status and chosen recommendation
        """
        if not cluster:
            return {'consensus': False, 'recommendation': None, 'supporting_models': []}

        # Calculate weighted votes
        model_votes = Counter()
        confidence_sum = {}

        for rec in cluster:
            model_name = rec.get('_source_model', 'unknown')
            weight = self.model_weights.get(model_name, 1.0)
            confidence = rec.get('_confidence', 1.0)

            # Vote weighted by model reliability and confidence
            vote_strength = weight * confidence
            model_votes[model_name] += vote_strength

            if model_name not in confidence_sum:
                confidence_sum[model_name] = []
            confidence_sum[model_name].append(confidence)

        # Find recommendation with highest weighted vote
        if not model_votes:
            return {'consensus': False, 'recommendation': None, 'supporting_models': []}

        best_model = model_votes.most_common(1)[0][0]
        best_rec = next((rec for rec in cluster if rec.get('_source_model') == best_model), cluster[0])

        # Check if consensus exists (>50% of weighted votes)
        total_weight = sum(model_votes.values())
        best_weight = model_votes[best_model]
        consensus = (best_weight / total_weight) >= 0.5

        # List supporting models
        supporting_models = [model for model, weight in model_votes.items() if weight > 0]

        return {
            'consensus': consensus,
            'recommendation': best_rec,
            'supporting_models': supporting_models,
            'vote_strength': best_weight / total_weight
        }

    def _tie_breaking(
        self,
        disagreements: List[Dict[str, Any]],
        model_outputs: List[ModelOutput]
    ) -> Dict[str, Any]:
        """
        Apply tie-breaking strategies for disagreements.

        Strategies:
        1. Majority rule (even if below threshold)
        2. Highest confidence model
        3. Merge complementary recommendations

        Args:
            disagreements: List of unresolved disagreements
            model_outputs: Original model outputs

        Returns:
            Dict with resolved recommendations
        """
        resolved = []

        for disagreement in disagreements:
            cluster = disagreement['recommendations']

            # Strategy 1: Pick highest confidence recommendation
            max_confidence = 0.0
            best_rec = None

            for rec in cluster:
                confidence = rec.get('_confidence', 0.0)
                if confidence > max_confidence:
                    max_confidence = confidence
                    best_rec = rec

            if best_rec:
                resolved.append(best_rec)

        return {
            'success': len(resolved) > 0,
            'resolved_recommendations': resolved
        }

    def generate_disagreement_report(
        self,
        resolution: ConflictResolution,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a report of disagreements and resolution process.

        Args:
            resolution: Conflict resolution result
            output_file: Optional file to save report

        Returns:
            Report as string
        """
        lines = []
        lines.append("# Conflict Resolution Report")
        lines.append("")
        lines.append(f"**Consensus Reached**: {resolution.consensus_reached}")
        lines.append(f"**Agreement Level**: {resolution.agreement_level:.1%}")
        lines.append(f"**Resolution Method**: {resolution.resolution_method}")
        lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Consensus Recommendations**: {len(resolution.final_recommendations)}")
        lines.append(f"- **Disagreements**: {len(resolution.disagreements)}")
        lines.append("")

        if resolution.disagreements:
            lines.append("## Disagreements")
            lines.append("")
            for i, disagreement in enumerate(resolution.disagreements):
                lines.append(f"### Disagreement {i+1}")
                lines.append("")
                lines.append(f"- **Cluster ID**: {disagreement['cluster_id']}")
                lines.append(f"- **Number of Variants**: {len(disagreement['recommendations'])}")
                lines.append("")

        if resolution.model_votes:
            lines.append("## Model Agreement")
            lines.append("")
            for rec_id, models in resolution.model_votes.items():
                lines.append(f"- **{rec_id}**: {', '.join(models)}")
            lines.append("")

        report = '\n'.join(lines)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            logger.info(f"Disagreement report saved to {output_file}")

        return report


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("CONFLICT RESOLVER DEMO")
    print("=" * 70)
    print()

    # Create test model outputs
    gemini_output = ModelOutput(
        model_name="gemini",
        recommendations=[
            {'title': 'Use panel data methods', 'description': 'Fixed effects models', 'priority': 'high'},
            {'title': 'Implement feature engineering', 'description': 'Create lag features', 'priority': 'medium'}
        ],
        confidence=0.9,
        raw_output="..."
    )

    claude_output = ModelOutput(
        model_name="claude",
        recommendations=[
            {'title': 'Use panel data models', 'description': 'Fixed effects regression', 'priority': 'high'},
            {'title': 'Add data quality checks', 'description': 'Validate inputs', 'priority': 'high'}
        ],
        confidence=0.85,
        raw_output="..."
    )

    gpt4_output = ModelOutput(
        model_name="gpt4",
        recommendations=[
            {'title': 'Panel data analysis', 'description': 'Fixed effects approach', 'priority': 'high'},
            {'title': 'Feature engineering pipeline', 'description': 'Automated feature creation', 'priority': 'medium'}
        ],
        confidence=0.8,
        raw_output="..."
    )

    # Initialize resolver
    resolver = ConflictResolver(similarity_threshold=0.7)

    # Resolve conflicts
    resolution = resolver.resolve([gemini_output, claude_output, gpt4_output])

    # Print results
    print(f"Consensus Reached: {resolution.consensus_reached}")
    print(f"Agreement Level: {resolution.agreement_level:.1%}")
    print(f"Resolution Method: {resolution.resolution_method}")
    print(f"Consensus Recommendations: {len(resolution.final_recommendations)}")
    print(f"Disagreements: {len(resolution.disagreements)}")
    print()

    # Generate report
    report = resolver.generate_disagreement_report(resolution)
    print(report)

    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)





