#!/usr/bin/env python3
"""
Unit tests for Conflict Resolver

Tests similarity calculation, conflict detection, consensus algorithms,
and resolution strategies.
"""

import tempfile
import unittest
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from scripts.conflict_resolver import (
    ConflictResolver,
    ConflictType,
    ResolutionStrategy,
    ModelOutput,
)


class TestConflictResolver(unittest.TestCase):
    """Test suite for Conflict Resolver"""

    def setUp(self):
        """Create temporary conflict log for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.conflict_log = Path(self.temp_dir) / "test_conflicts.json"
        self.resolver = ConflictResolver(conflict_log=self.conflict_log)

    def tearDown(self):
        """Clean up temporary files"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test resolver initializes correctly"""
        self.assertIsNotNone(self.resolver)
        self.assertEqual(self.resolver.PARTIAL_AGREEMENT_THRESHOLD, 0.70)

    def test_jaccard_similarity_identical(self):
        """Test Jaccard similarity with identical sets"""
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "c"}

        similarity = self.resolver.calculate_jaccard_similarity(set1, set2)

        self.assertEqual(similarity, 1.0)

    def test_jaccard_similarity_disjoint(self):
        """Test Jaccard similarity with disjoint sets"""
        set1 = {"a", "b", "c"}
        set2 = {"d", "e", "f"}

        similarity = self.resolver.calculate_jaccard_similarity(set1, set2)

        self.assertEqual(similarity, 0.0)

    def test_jaccard_similarity_partial(self):
        """Test Jaccard similarity with partial overlap"""
        set1 = {"a", "b", "c", "d"}
        set2 = {"c", "d", "e", "f"}

        similarity = self.resolver.calculate_jaccard_similarity(set1, set2)

        # Intersection: {c, d} = 2
        # Union: {a, b, c, d, e, f} = 6
        # Similarity: 2/6 = 0.333...
        self.assertAlmostEqual(similarity, 0.333, places=2)

    def test_jaccard_similarity_empty(self):
        """Test Jaccard similarity with empty sets"""
        set1 = set()
        set2 = set()

        similarity = self.resolver.calculate_jaccard_similarity(set1, set2)

        self.assertEqual(similarity, 1.0)

    def test_text_similarity_identical(self):
        """Test text similarity with identical strings"""
        text1 = "Add authentication system"
        text2 = "Add authentication system"

        similarity = self.resolver.calculate_text_similarity(text1, text2)

        self.assertEqual(similarity, 1.0)

    def test_text_similarity_case_insensitive(self):
        """Test text similarity is case insensitive"""
        text1 = "Add Authentication System"
        text2 = "add authentication system"

        similarity = self.resolver.calculate_text_similarity(text1, text2)

        self.assertEqual(similarity, 1.0)

    def test_text_similarity_different(self):
        """Test text similarity with different strings"""
        text1 = "Add authentication"
        text2 = "Implement caching"

        similarity = self.resolver.calculate_text_similarity(text1, text2)

        self.assertLess(similarity, 0.5)

    def test_extract_recommendation_keys(self):
        """Test extracting keys from recommendations"""
        recommendations = [
            {"title": "Add Auth", "priority": "high"},
            {"title": "Add Cache", "priority": "medium"},
            {"name": "Add Logging"},
        ]

        keys = self.resolver.extract_recommendation_keys(recommendations)

        self.assertEqual(len(keys), 3)
        self.assertIn("add auth", keys)
        self.assertIn("add cache", keys)
        self.assertIn("add logging", keys)

    def test_classify_conflict_full_agreement(self):
        """Test classifying full agreement (>90%)"""
        conflict_type = self.resolver.classify_conflict_type(0.95)

        self.assertEqual(conflict_type, ConflictType.FULL_AGREEMENT)

    def test_classify_conflict_partial_agreement(self):
        """Test classifying partial agreement (70-90%)"""
        conflict_type = self.resolver.classify_conflict_type(0.75)

        self.assertEqual(conflict_type, ConflictType.PARTIAL_AGREEMENT)

    def test_classify_conflict_significant_disagreement(self):
        """Test classifying significant disagreement (50-70%)"""
        conflict_type = self.resolver.classify_conflict_type(0.60)

        self.assertEqual(conflict_type, ConflictType.SIGNIFICANT_DISAGREEMENT)

    def test_classify_conflict_complete_disagreement(self):
        """Test classifying complete disagreement (<50%)"""
        conflict_type = self.resolver.classify_conflict_type(0.30)

        self.assertEqual(conflict_type, ConflictType.COMPLETE_DISAGREEMENT)

    def test_determine_strategy_full_agreement(self):
        """Test strategy for full agreement"""
        strategy = self.resolver.determine_resolution_strategy(
            ConflictType.FULL_AGREEMENT, 2
        )

        self.assertEqual(strategy, ResolutionStrategy.CONSENSUS)

    def test_determine_strategy_partial_agreement(self):
        """Test strategy for partial agreement"""
        strategy = self.resolver.determine_resolution_strategy(
            ConflictType.PARTIAL_AGREEMENT, 2
        )

        self.assertEqual(strategy, ResolutionStrategy.UNION)

    def test_determine_strategy_significant_disagreement_two_models(self):
        """Test strategy for significant disagreement with 2 models"""
        strategy = self.resolver.determine_resolution_strategy(
            ConflictType.SIGNIFICANT_DISAGREEMENT, 2
        )

        self.assertEqual(strategy, ResolutionStrategy.HUMAN_REVIEW)

    def test_determine_strategy_complete_disagreement(self):
        """Test strategy for complete disagreement"""
        strategy = self.resolver.determine_resolution_strategy(
            ConflictType.COMPLETE_DISAGREEMENT, 2
        )

        self.assertEqual(strategy, ResolutionStrategy.HUMAN_REVIEW)

    def test_resolve_single_model(self):
        """Test resolving with single model (no conflict)"""
        recommendations = [
            {"title": "Add Auth", "priority": "high"},
            {"title": "Add Cache", "priority": "medium"},
        ]

        result = self.resolver.resolve_conflict({"gemini": recommendations})

        self.assertTrue(result.has_consensus)
        self.assertEqual(
            result.conflict_analysis.conflict_type, ConflictType.FULL_AGREEMENT
        )
        self.assertEqual(len(result.merged_output), 2)

    def test_resolve_identical_models(self):
        """Test resolving with identical model outputs"""
        recommendations = [
            {"title": "Add Auth", "priority": "high"},
            {"title": "Add Cache", "priority": "medium"},
        ]

        result = self.resolver.resolve_conflict(
            {"gemini": recommendations, "claude": recommendations}
        )

        self.assertTrue(result.has_consensus)
        self.assertEqual(
            result.conflict_analysis.conflict_type, ConflictType.FULL_AGREEMENT
        )
        self.assertEqual(result.conflict_analysis.similarity_score, 1.0)

    def test_resolve_partial_agreement(self):
        """Test resolving with partial agreement (70-90%)"""
        # To get 75% similarity: 3 common out of 4 total unique = 0.75
        gemini_recs = [
            {"title": "Add Auth", "priority": "high"},
            {"title": "Add Cache", "priority": "medium"},
            {"title": "Add Logging", "priority": "low"},
        ]

        claude_recs = [
            {"title": "Add Auth", "priority": "high"},
            {"title": "Add Cache", "priority": "medium"},
            {"title": "Add Logging", "priority": "low"},
            {"title": "Add Testing", "priority": "high"},
        ]

        result = self.resolver.resolve_conflict(
            {"gemini": gemini_recs, "claude": claude_recs}
        )

        # Should have consensus (>70% agreement)
        # 3 common items (Auth, Cache, Logging)
        # 4 total unique items (Auth, Cache, Logging, Testing)
        # Jaccard similarity = 3/4 = 0.75 = 75%
        self.assertTrue(result.has_consensus)
        self.assertEqual(
            result.conflict_analysis.conflict_type, ConflictType.PARTIAL_AGREEMENT
        )
        self.assertEqual(result.conflict_analysis.similarity_score, 0.75)

    def test_resolve_significant_disagreement(self):
        """Test resolving with significant disagreement (50-70%)"""
        gemini_recs = [
            {"title": "Add Auth", "priority": "high"},
            {"title": "Add Cache", "priority": "medium"},
            {"title": "Add Logging", "priority": "low"},
        ]

        claude_recs = [
            {"title": "Add Auth", "priority": "high"},
            {"title": "Add Monitoring", "priority": "medium"},
            {"title": "Add Metrics", "priority": "low"},
        ]

        result = self.resolver.resolve_conflict(
            {"gemini": gemini_recs, "claude": claude_recs}
        )

        # Should require review (<70% agreement)
        self.assertFalse(result.has_consensus)
        self.assertEqual(
            result.conflict_analysis.resolution_strategy,
            ResolutionStrategy.HUMAN_REVIEW,
        )

    def test_resolve_complete_disagreement(self):
        """Test resolving with complete disagreement (<50%)"""
        gemini_recs = [
            {"title": "Add Auth", "priority": "high"},
            {"title": "Add Cache", "priority": "medium"},
        ]

        claude_recs = [
            {"title": "Add Monitoring", "priority": "high"},
            {"title": "Add Metrics", "priority": "medium"},
        ]

        result = self.resolver.resolve_conflict(
            {"gemini": gemini_recs, "claude": claude_recs}
        )

        # Should definitely require review (0% agreement)
        self.assertFalse(result.has_consensus)
        self.assertEqual(
            result.conflict_analysis.conflict_type, ConflictType.COMPLETE_DISAGREEMENT
        )
        self.assertEqual(result.conflict_analysis.similarity_score, 0.0)

    def test_merge_consensus_strategy(self):
        """Test merging with CONSENSUS strategy"""
        model_outputs = {
            "gemini": ModelOutput(
                model_name="gemini", recommendations=[{"title": "Add Auth"}]
            )
        }

        merged = self.resolver.merge_recommendations(
            model_outputs, ResolutionStrategy.CONSENSUS
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["title"], "Add Auth")

    def test_merge_union_strategy(self):
        """Test merging with UNION strategy"""
        model_outputs = {
            "gemini": ModelOutput(
                model_name="gemini",
                recommendations=[{"title": "Add Auth"}, {"title": "Add Cache"}],
            ),
            "claude": ModelOutput(
                model_name="claude",
                recommendations=[{"title": "Add Auth"}, {"title": "Add Monitoring"}],
            ),
        }

        merged = self.resolver.merge_recommendations(
            model_outputs, ResolutionStrategy.UNION
        )

        # Should have 3 unique items (Auth from one model, Cache, Monitoring)
        self.assertEqual(len(merged), 3)

        # Check source models are tracked
        for rec in merged:
            self.assertIn("_source_model", rec)

    def test_merge_intersection_strategy(self):
        """Test merging with INTERSECTION strategy"""
        model_outputs = {
            "gemini": ModelOutput(
                model_name="gemini",
                recommendations=[{"title": "Add Auth"}, {"title": "Add Cache"}],
            ),
            "claude": ModelOutput(
                model_name="claude",
                recommendations=[{"title": "Add Auth"}, {"title": "Add Monitoring"}],
            ),
        }

        merged = self.resolver.merge_recommendations(
            model_outputs, ResolutionStrategy.INTERSECTION
        )

        # Should only have 1 item (Auth - common to both)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["title"], "Add Auth")

    def test_merge_weighted_vote_strategy(self):
        """Test merging with WEIGHTED_VOTE strategy"""
        model_outputs = {
            "gemini": ModelOutput(
                model_name="gemini",
                recommendations=[{"title": "Add Auth"}, {"title": "Add Cache"}],
                confidence=0.8,
            ),
            "claude": ModelOutput(
                model_name="claude",
                recommendations=[{"title": "Add Auth"}, {"title": "Add Monitoring"}],
                confidence=0.9,
            ),
        }

        merged = self.resolver.merge_recommendations(
            model_outputs, ResolutionStrategy.WEIGHTED_VOTE
        )

        # Should have 3 items with vote counts
        self.assertEqual(len(merged), 3)

        # Auth should have highest votes (both models)
        self.assertIn("_vote_count", merged[0])
        self.assertGreater(merged[0]["_vote_count"], merged[1]["_vote_count"])

    def test_request_human_review_auto_approve(self):
        """Test human review with auto-approve"""
        recommendations = [{"title": "Add Auth"}]

        result = self.resolver.resolve_conflict({"gemini": recommendations})

        review = self.resolver.request_human_review(result, auto_approve=True)

        self.assertTrue(review["approved"])
        self.assertEqual(review["strategy"], "UNION")

    def test_conflict_persistence(self):
        """Test conflicts are persisted to disk"""
        recommendations = [{"title": "Add Auth"}]

        self.resolver.resolve_conflict({"gemini": recommendations})

        # Verify conflict log was created
        self.assertTrue(self.conflict_log.exists())


if __name__ == "__main__":
    unittest.main()
