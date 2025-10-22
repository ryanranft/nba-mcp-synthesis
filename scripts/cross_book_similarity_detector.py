#!/usr/bin/env python3
"""
Cross-Book Similarity Detector for NBA MCP Synthesis

This module detects and consolidates similar recommendations across multiple books:
1. Semantic similarity detection using embeddings
2. Duplicate detection (near-identical recommendations)
3. Similar concept detection (related but not identical)
4. Recommendation consolidation and merging
5. Source attribution and provenance tracking

Features:
- OpenAI embeddings for semantic similarity
- Cosine similarity calculation
- Hierarchical clustering
- Multi-level similarity thresholds
- Consolidated recommendation generation

Author: NBA MCP Synthesis Team
Date: 2025-10-22
"""

import json
import logging
import argparse
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import OpenAI for embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("⚠️  OpenAI not available. Install with: pip install openai")


@dataclass
class SimilarityMatch:
    """Represents a similarity match between two recommendations"""
    rec1_id: str
    rec2_id: str
    rec1_book: str
    rec2_book: str
    similarity_score: float
    match_type: str  # 'duplicate', 'very_similar', 'similar', 'related'
    rec1_title: str
    rec2_title: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ConsolidatedRecommendation:
    """Represents a consolidated recommendation from multiple sources"""
    consolidated_id: str
    title: str
    description: str
    source_recommendations: List[str]  # IDs of source recommendations
    source_books: List[str]  # Books that contributed
    implementation_steps: List[str]
    priority: str
    time_estimate: str
    confidence_boost: float  # Higher confidence when multiple sources agree

    def to_dict(self) -> Dict:
        return asdict(self)


class CrossBookSimilarityDetector:
    """Detects and consolidates similar recommendations across books"""

    # Similarity thresholds
    THRESHOLD_DUPLICATE = 0.95  # Near-identical
    THRESHOLD_VERY_SIMILAR = 0.85  # Very similar concept
    THRESHOLD_SIMILAR = 0.75  # Similar concept
    THRESHOLD_RELATED = 0.65  # Related concept

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize similarity detector

        Args:
            openai_api_key: OpenAI API key for embeddings (defaults to env var)
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

        if not OPENAI_AVAILABLE:
            logger.error("❌ OpenAI library not available. Cannot compute embeddings.")
            self.client = None
        elif not self.api_key:
            logger.warning("⚠️  No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("✅ OpenAI client initialized")

        self.embeddings_cache: Dict[str, List[float]] = {}
        self.recommendations: List[Dict] = []
        self.similarity_matches: List[SimilarityMatch] = []
        self.consolidated_recommendations: List[ConsolidatedRecommendation] = []

    def load_recommendations_from_multiple_books(
        self,
        book_analysis_dir: str
    ) -> List[Dict]:
        """
        Load recommendations from all books in analysis directory

        Args:
            book_analysis_dir: Directory containing book analysis results

        Returns:
            List of all recommendations with book source metadata
        """
        logger.info(f"📖 Loading recommendations from: {book_analysis_dir}")

        all_recommendations = []
        analysis_dir = Path(book_analysis_dir)

        # Find all *_RECOMMENDATIONS_COMPLETE.md files
        recommendation_files = list(analysis_dir.glob("*_RECOMMENDATIONS_COMPLETE.md"))

        if not recommendation_files:
            logger.warning(f"⚠️  No recommendation files found in {book_analysis_dir}")
            return []

        logger.info(f"   Found {len(recommendation_files)} book analysis files")

        # For each book, look for corresponding JSON files
        for md_file in recommendation_files:
            book_name = md_file.stem.replace('_RECOMMENDATIONS_COMPLETE', '')

            # Try to find JSON file with recommendations
            json_candidates = [
                analysis_dir / f"{book_name}_recommendations.json",
                analysis_dir / f"{book_name}.json",
                analysis_dir / "consolidated_recommendations.json",
            ]

            json_file = None
            for candidate in json_candidates:
                if candidate.exists():
                    json_file = candidate
                    break

            if not json_file:
                logger.warning(f"   ⚠️  No JSON found for {book_name}, skipping")
                continue

            # Load recommendations from JSON
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                # Handle different JSON formats
                if isinstance(data, list):
                    book_recs = data
                elif isinstance(data, dict):
                    if 'recommendations' in data:
                        book_recs = data['recommendations']
                    else:
                        book_recs = [data]
                else:
                    logger.warning(f"   ⚠️  Invalid JSON format in {json_file}")
                    continue

                # Add book source metadata
                for rec in book_recs:
                    rec['source_book'] = book_name
                    rec['source_file'] = str(json_file)

                all_recommendations.extend(book_recs)
                logger.info(f"   ✅ Loaded {len(book_recs)} recommendations from {book_name}")

            except Exception as e:
                logger.error(f"   ❌ Error loading {json_file}: {e}")
                continue

        logger.info(f"📊 Total recommendations loaded: {len(all_recommendations)}")
        self.recommendations = all_recommendations
        return all_recommendations

    def load_recommendations_from_file(self, file_path: str) -> List[Dict]:
        """
        Load recommendations from a single consolidated file

        Args:
            file_path: Path to recommendations JSON file

        Returns:
            List of recommendations
        """
        logger.info(f"📖 Loading recommendations from: {file_path}")

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Handle different JSON formats
        if isinstance(data, list):
            recommendations = data
        elif isinstance(data, dict):
            if 'recommendations' in data:
                recommendations = data['recommendations']
            else:
                recommendations = [data]
        else:
            logger.error("❌ Invalid JSON format")
            return []

        # Add source book from metadata if available
        for i, rec in enumerate(recommendations):
            if 'source_book' not in rec:
                rec['source_book'] = rec.get('book', f'unknown_book_{i}')

        logger.info(f"📊 Loaded {len(recommendations)} recommendations")
        self.recommendations = recommendations
        return recommendations

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get OpenAI embedding for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if failed
        """
        if not self.client:
            logger.error("❌ OpenAI client not initialized")
            return None

        # Check cache
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]

        try:
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"  # Fast and cost-effective
            )

            embedding = response.data[0].embedding
            self.embeddings_cache[text] = embedding
            return embedding

        except Exception as e:
            logger.error(f"❌ Error getting embedding: {e}")
            return None

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        magnitude1 = np.linalg.norm(vec1)
        magnitude2 = np.linalg.norm(vec2)

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        similarity = dot_product / (magnitude1 * magnitude2)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, similarity))

    def _get_text_for_embedding(self, rec: Dict) -> str:
        """Get text from recommendation for embedding"""
        text_parts = []

        # Title (weighted more)
        if 'title' in rec:
            text_parts.append(rec['title'])
            text_parts.append(rec['title'])  # Add twice for emphasis

        # Description
        if 'description' in rec:
            text_parts.append(rec['description'])

        # Implementation steps (first 3)
        if 'implementation_steps' in rec:
            steps = rec['implementation_steps']
            if isinstance(steps, list):
                text_parts.extend(steps[:3])

        return ' '.join(text_parts)

    def detect_similarities(
        self,
        min_threshold: float = None
    ) -> List[SimilarityMatch]:
        """
        Detect similarities between all recommendations

        Args:
            min_threshold: Minimum similarity to report (default: THRESHOLD_RELATED)

        Returns:
            List of similarity matches
        """
        if min_threshold is None:
            min_threshold = self.THRESHOLD_RELATED

        logger.info("🔍 Detecting similarities between recommendations...")
        logger.info(f"   Total recommendations: {len(self.recommendations)}")
        logger.info(f"   Minimum threshold: {min_threshold}")

        if not self.client:
            logger.error("❌ Cannot detect similarities without OpenAI client")
            return []

        # Step 1: Compute embeddings for all recommendations
        logger.info("📊 Computing embeddings...")
        embeddings = []

        for i, rec in enumerate(self.recommendations):
            if (i + 1) % 10 == 0:
                logger.info(f"   Progress: {i + 1}/{len(self.recommendations)}")

            text = self._get_text_for_embedding(rec)
            embedding = self.get_embedding(text)

            if embedding is None:
                logger.warning(f"   ⚠️  Failed to get embedding for rec {i}")
                embeddings.append(None)
            else:
                embeddings.append(embedding)

        logger.info(f"✅ Computed {sum(1 for e in embeddings if e is not None)} embeddings")

        # Step 2: Compare all pairs
        logger.info("🔍 Comparing all pairs...")
        matches = []
        total_comparisons = len(self.recommendations) * (len(self.recommendations) - 1) // 2

        comparison_count = 0
        for i in range(len(self.recommendations)):
            for j in range(i + 1, len(self.recommendations)):
                comparison_count += 1

                if comparison_count % 1000 == 0:
                    logger.info(f"   Progress: {comparison_count}/{total_comparisons}")

                # Skip if embeddings failed
                if embeddings[i] is None or embeddings[j] is None:
                    continue

                # Skip if same book (looking for cross-book similarities)
                rec1 = self.recommendations[i]
                rec2 = self.recommendations[j]

                if rec1.get('source_book') == rec2.get('source_book'):
                    continue

                # Compute similarity
                similarity = self.compute_similarity(embeddings[i], embeddings[j])

                # Check if above threshold
                if similarity >= min_threshold:
                    # Determine match type
                    if similarity >= self.THRESHOLD_DUPLICATE:
                        match_type = 'duplicate'
                    elif similarity >= self.THRESHOLD_VERY_SIMILAR:
                        match_type = 'very_similar'
                    elif similarity >= self.THRESHOLD_SIMILAR:
                        match_type = 'similar'
                    else:
                        match_type = 'related'

                    match = SimilarityMatch(
                        rec1_id=rec1.get('recommendation_id', f'rec_{i}'),
                        rec2_id=rec2.get('recommendation_id', f'rec_{j}'),
                        rec1_book=rec1.get('source_book', 'unknown'),
                        rec2_book=rec2.get('source_book', 'unknown'),
                        similarity_score=similarity,
                        match_type=match_type,
                        rec1_title=rec1.get('title', 'Unknown'),
                        rec2_title=rec2.get('title', 'Unknown')
                    )

                    matches.append(match)

        logger.info(f"✅ Found {len(matches)} similarity matches")

        # Log breakdown by type
        by_type = defaultdict(int)
        for match in matches:
            by_type[match.match_type] += 1

        logger.info("   Matches by type:")
        for match_type in ['duplicate', 'very_similar', 'similar', 'related']:
            count = by_type[match_type]
            if count > 0:
                logger.info(f"     - {match_type}: {count}")

        self.similarity_matches = matches
        return matches

    def consolidate_recommendations(
        self,
        min_similarity: float = None
    ) -> List[ConsolidatedRecommendation]:
        """
        Consolidate similar recommendations into merged recommendations

        Args:
            min_similarity: Minimum similarity for consolidation (default: THRESHOLD_SIMILAR)

        Returns:
            List of consolidated recommendations
        """
        if min_similarity is None:
            min_similarity = self.THRESHOLD_SIMILAR

        logger.info("🔨 Consolidating similar recommendations...")
        logger.info(f"   Minimum similarity: {min_similarity}")

        # Filter matches by minimum similarity
        consolidation_matches = [
            m for m in self.similarity_matches
            if m.similarity_score >= min_similarity
        ]

        logger.info(f"   {len(consolidation_matches)} matches above threshold")

        # Group recommendations into clusters
        clusters = self._build_clusters(consolidation_matches)

        logger.info(f"   Found {len(clusters)} clusters")

        # Create consolidated recommendations
        consolidated = []
        for i, cluster in enumerate(clusters):
            if len(cluster) < 2:
                continue  # Skip singleton clusters

            # Get all recommendations in cluster
            cluster_recs = [self._find_recommendation_by_id(rec_id) for rec_id in cluster]
            cluster_recs = [r for r in cluster_recs if r is not None]

            if not cluster_recs:
                continue

            # Merge recommendations
            consolidated_rec = self._merge_recommendations(cluster_recs, i)
            consolidated.append(consolidated_rec)

        logger.info(f"✅ Created {len(consolidated)} consolidated recommendations")

        self.consolidated_recommendations = consolidated
        return consolidated

    def _build_clusters(self, matches: List[SimilarityMatch]) -> List[Set[str]]:
        """
        Build clusters of similar recommendations using union-find

        Args:
            matches: List of similarity matches

        Returns:
            List of clusters (each cluster is a set of recommendation IDs)
        """
        # Union-find data structure
        parent = {}

        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])  # Path compression
            return parent[x]

        def union(x, y):
            root_x = find(x)
            root_y = find(y)
            if root_x != root_y:
                parent[root_x] = root_y

        # Build clusters
        for match in matches:
            union(match.rec1_id, match.rec2_id)

        # Group by root
        clusters_dict = defaultdict(set)
        all_rec_ids = set()
        for match in matches:
            all_rec_ids.add(match.rec1_id)
            all_rec_ids.add(match.rec2_id)

        for rec_id in all_rec_ids:
            root = find(rec_id)
            clusters_dict[root].add(rec_id)

        return list(clusters_dict.values())

    def _find_recommendation_by_id(self, rec_id: str) -> Optional[Dict]:
        """Find recommendation by ID"""
        for rec in self.recommendations:
            if rec.get('recommendation_id') == rec_id or rec.get('id') == rec_id:
                return rec
        return None

    def _merge_recommendations(
        self,
        recommendations: List[Dict],
        cluster_id: int
    ) -> ConsolidatedRecommendation:
        """
        Merge multiple similar recommendations into one consolidated recommendation

        Args:
            recommendations: List of recommendations to merge
            cluster_id: Cluster ID for consolidated recommendation

        Returns:
            Consolidated recommendation
        """
        # Use most common title (or first if all different)
        titles = [r.get('title', '') for r in recommendations]
        title = max(set(titles), key=titles.count) if titles else f"Consolidated Recommendation {cluster_id}"

        # Combine descriptions
        descriptions = [r.get('description', '') for r in recommendations if r.get('description')]
        if descriptions:
            description = f"Consolidated from {len(recommendations)} sources:\n\n" + "\n\n".join(
                f"- {desc[:200]}..." if len(desc) > 200 else f"- {desc}"
                for desc in descriptions[:3]
            )
        else:
            description = f"Consolidated recommendation from {len(recommendations)} sources"

        # Merge implementation steps (deduplicate)
        all_steps = []
        for rec in recommendations:
            steps = rec.get('implementation_steps', [])
            if isinstance(steps, list):
                all_steps.extend(steps)

        # Deduplicate steps (keep unique, preserve order)
        unique_steps = []
        seen = set()
        for step in all_steps:
            step_lower = step.lower().strip()
            if step_lower not in seen:
                seen.add(step_lower)
                unique_steps.append(step)

        # Take highest priority
        priorities = [r.get('priority', 'MEDIUM') for r in recommendations]
        priority_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NICE_TO_HAVE']
        priority = min(priorities, key=lambda p: priority_order.index(p) if p in priority_order else 999)

        # Average time estimates (convert to hours, average, convert back)
        time_estimates = []
        for rec in recommendations:
            estimate_str = rec.get('time_estimate', '0 hours')
            try:
                hours = float(estimate_str.split()[0])
                time_estimates.append(hours)
            except:
                pass

        if time_estimates:
            avg_hours = sum(time_estimates) / len(time_estimates)
            time_estimate = f"{avg_hours:.1f} hours"
        else:
            time_estimate = "Unknown"

        # Source attribution
        source_rec_ids = [r.get('recommendation_id', r.get('id', '')) for r in recommendations]
        source_books = list(set(r.get('source_book', 'unknown') for r in recommendations))

        # Confidence boost (more sources = higher confidence)
        confidence_boost = min(1.0 + (len(recommendations) - 1) * 0.1, 2.0)

        return ConsolidatedRecommendation(
            consolidated_id=f"consolidated_cluster_{cluster_id}",
            title=title,
            description=description,
            source_recommendations=source_rec_ids,
            source_books=source_books,
            implementation_steps=unique_steps[:10],  # Limit to top 10
            priority=priority,
            time_estimate=time_estimate,
            confidence_boost=confidence_boost
        )

    def export_similarity_report(self, output_file: str):
        """Export similarity analysis to markdown report"""
        logger.info(f"📤 Exporting similarity report: {output_file}")

        lines = [
            '# Cross-Book Similarity Analysis Report',
            '',
            f'**Generated**: {datetime.now().isoformat()}',
            f'**Total Recommendations Analyzed**: {len(self.recommendations)}',
            f'**Similarity Matches Found**: {len(self.similarity_matches)}',
            f'**Consolidated Recommendations**: {len(self.consolidated_recommendations)}',
            '',
            '---',
            '',
            '## Summary',
            '',
        ]

        # Books analyzed
        books = set(r.get('source_book', 'unknown') for r in self.recommendations)
        lines.append(f'**Books Analyzed**: {len(books)}')
        lines.append('')

        # Matches by type
        by_type = defaultdict(int)
        for match in self.similarity_matches:
            by_type[match.match_type] += 1

        lines.append('**Matches by Type**:')
        for match_type in ['duplicate', 'very_similar', 'similar', 'related']:
            count = by_type[match_type]
            lines.append(f'- {match_type}: {count}')
        lines.append('')

        # Top similarity matches
        lines.extend([
            '## Top Similarity Matches',
            '',
            '| Score | Type | Book 1 | Recommendation 1 | Book 2 | Recommendation 2 |',
            '|-------|------|--------|------------------|--------|------------------|',
        ])

        # Sort by similarity score
        top_matches = sorted(self.similarity_matches, key=lambda m: m.similarity_score, reverse=True)[:50]

        for match in top_matches:
            lines.append(
                f'| {match.similarity_score:.3f} | {match.match_type} | '
                f'{match.rec1_book[:20]} | {match.rec1_title[:30]} | '
                f'{match.rec2_book[:20]} | {match.rec2_title[:30]} |'
            )

        # Consolidated recommendations
        if self.consolidated_recommendations:
            lines.extend([
                '',
                '## Consolidated Recommendations',
                '',
            ])

            for cons_rec in self.consolidated_recommendations:
                lines.extend([
                    f'### {cons_rec.title}',
                    '',
                    f'**Consolidated ID**: `{cons_rec.consolidated_id}`',
                    f'**Priority**: {cons_rec.priority}',
                    f'**Time Estimate**: {cons_rec.time_estimate}',
                    f'**Confidence Boost**: {cons_rec.confidence_boost:.2f}x',
                    f'**Source Books**: {", ".join(cons_rec.source_books)}',
                    f'**Source Recommendations**: {len(cons_rec.source_recommendations)}',
                    '',
                    f'{cons_rec.description}',
                    '',
                ])

        # Write to file
        Path(output_file).write_text('\n'.join(lines))
        logger.info(f"✅ Similarity report exported")

    def export_consolidated_recommendations(self, output_file: str):
        """Export consolidated recommendations to JSON"""
        logger.info(f"📤 Exporting consolidated recommendations: {output_file}")

        output_data = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'total_source_recommendations': len(self.recommendations),
                'total_consolidated': len(self.consolidated_recommendations),
                'books_analyzed': list(set(r.get('source_book', 'unknown') for r in self.recommendations)),
            },
            'consolidated_recommendations': [rec.to_dict() for rec in self.consolidated_recommendations],
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"✅ Consolidated recommendations exported")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Detect and consolidate similar recommendations across books'
    )
    parser.add_argument(
        '--recommendations',
        help='Path to single recommendations JSON file'
    )
    parser.add_argument(
        '--analysis-dir',
        help='Directory containing multiple book analysis results'
    )
    parser.add_argument(
        '--min-threshold',
        type=float,
        default=0.65,
        help='Minimum similarity threshold (0.0-1.0)'
    )
    parser.add_argument(
        '--consolidate-threshold',
        type=float,
        default=0.75,
        help='Minimum similarity for consolidation (0.0-1.0)'
    )
    parser.add_argument(
        '--report',
        help='Output path for similarity report (markdown)'
    )
    parser.add_argument(
        '--consolidated-output',
        help='Output path for consolidated recommendations (JSON)'
    )

    args = parser.parse_args()

    if not args.recommendations and not args.analysis_dir:
        logger.error("❌ Must provide either --recommendations or --analysis-dir")
        return 1

    # Initialize detector
    detector = CrossBookSimilarityDetector()

    # Load recommendations
    if args.recommendations:
        detector.load_recommendations_from_file(args.recommendations)
    else:
        detector.load_recommendations_from_multiple_books(args.analysis_dir)

    if not detector.recommendations:
        logger.error("❌ No recommendations loaded")
        return 1

    # Detect similarities
    matches = detector.detect_similarities(min_threshold=args.min_threshold)

    # Consolidate recommendations
    if matches:
        consolidated = detector.consolidate_recommendations(min_similarity=args.consolidate_threshold)

    # Export results
    if args.report:
        detector.export_similarity_report(args.report)

    if args.consolidated_output:
        detector.export_consolidated_recommendations(args.consolidated_output)

    logger.info("✅ Cross-book similarity detection complete!")

    return 0


if __name__ == '__main__':
    exit(main())
