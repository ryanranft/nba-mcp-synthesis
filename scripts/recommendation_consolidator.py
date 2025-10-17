#!/usr/bin/env python3
"""
Recommendation Consolidation Module

Consolidates similar recommendations across books by:
1. Finding similar recommendations using fuzzy matching
2. Merging similar recommendations into consolidated entries
3. Updating the master recommendations database
4. Generating consolidation reports

Usage:
    python scripts/recommendation_consolidator.py
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class RecommendationConsolidator:
    """Consolidates similar recommendations across books."""

    def __init__(
        self, master_recs_path: str = "analysis_results/master_recommendations.json"
    ):
        self.master_recs_path = master_recs_path
        self.similarity_threshold = (
            0.8  # 80% similarity threshold (restored to original)
        )
        self.consolidation_log = []

    def load_master_recommendations(self) -> Dict:
        """Load master recommendations from file."""
        if os.path.exists(self.master_recs_path):
            with open(self.master_recs_path, "r") as f:
                data = json.load(f)

            # Ensure all recommendations have IDs
            recommendations = data.get("recommendations", [])
            for i, rec in enumerate(recommendations):
                if "id" not in rec:
                    rec["id"] = f"rec_{i+1}_{hash(rec.get('title', '')) % 10000}"
                    logger.info(f"Generated ID for recommendation: {rec['id']}")

            return data
        else:
            logger.error(
                f"Master recommendations file not found: {self.master_recs_path}"
            )
            return {
                "recommendations": [],
                "by_category": {},
                "by_book": {},
                "last_updated": None,
            }

    def save_master_recommendations(self, data: Dict):
        """Save master recommendations to file."""
        os.makedirs(os.path.dirname(self.master_recs_path), exist_ok=True)
        data["last_updated"] = datetime.now().isoformat()

        with open(self.master_recs_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved consolidated recommendations to {self.master_recs_path}")

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        # Remove common words and extract meaningful terms
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "implement",
            "add",
            "create",
            "build",
            "develop",
            "use",
            "apply",
            "enable",
            "support",
            "system",
            "framework",
            "tool",
            "method",
            "approach",
            "technique",
            "process",
            "workflow",
        }

        # Extract words (alphanumeric sequences)
        words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

        # Filter out stop words and short words
        keywords = {word for word in words if len(word) > 3 and word not in stop_words}

        return keywords

    def find_similar_recommendations(
        self, recommendations: List[Dict]
    ) -> Dict[str, List[str]]:
        """
        Group similar recommendations using:
        - Title similarity (fuzzy matching, >80% match)
        - Category matching
        - Keyword overlap in reasoning

        Returns: {primary_rec_id: [similar_rec_ids]}
        """
        logger.info(
            f"Finding similar recommendations among {len(recommendations)} items..."
        )

        similar_groups = {}
        processed_ids = set()

        for i, rec1 in enumerate(recommendations):
            # Skip recommendations without ID
            if "id" not in rec1:
                logger.warning(
                    f"Skipping recommendation without ID: {rec1.get('title', 'Unknown')}"
                )
                continue

            if rec1["id"] in processed_ids:
                continue

            similar_recs = [rec1["id"]]
            processed_ids.add(rec1["id"])

            for j, rec2 in enumerate(recommendations[i + 1 :], i + 1):
                # Skip recommendations without ID
                if "id" not in rec2:
                    logger.warning(
                        f"Skipping recommendation without ID: {rec2.get('title', 'Unknown')}"
                    )
                    continue

                if rec2["id"] in processed_ids:
                    continue

                # Check similarity
                if self._are_similar(rec1, rec2):
                    similar_recs.append(rec2["id"])
                    processed_ids.add(rec2["id"])

            # Only create group if we found similar recommendations
            if len(similar_recs) > 1:
                primary_id = similar_recs[0]
                similar_groups[primary_id] = similar_recs[
                    1:
                ]  # Exclude primary from similar list

        logger.info(f"Found {len(similar_groups)} groups of similar recommendations")
        return similar_groups

    def _are_similar(self, rec1: Dict, rec2: Dict) -> bool:
        """Check if two recommendations are similar."""
        # Check category match
        if rec1.get("category") != rec2.get("category"):
            return False

        # Check title similarity
        title_similarity = self.calculate_similarity(
            rec1.get("title", ""), rec2.get("title", "")
        )

        if title_similarity >= self.similarity_threshold:
            return True

        # Check keyword overlap in reasoning
        reasoning1 = rec1.get("reasoning", "") + " " + rec1.get("title", "")
        reasoning2 = rec2.get("reasoning", "") + " " + rec2.get("title", "")

        keywords1 = self.extract_keywords(reasoning1)
        keywords2 = self.extract_keywords(reasoning2)

        if keywords1 and keywords2:
            overlap = len(keywords1.intersection(keywords2))
            total_unique = len(keywords1.union(keywords2))

            if total_unique > 0:
                keyword_similarity = overlap / total_unique
                if keyword_similarity >= 0.6:  # 60% keyword overlap
                    return True

        return False

    def merge_recommendations(
        self, primary_id: str, similar_ids: List[str], all_recommendations: List[Dict]
    ) -> Dict:
        """
        Merge similar recommendations into one:
        - Combine source_books lists (deduplicate)
        - Merge reasoning with book-specific sections
        - Take highest priority
        - Average or sum time estimates
        - Create consolidated ID
        - Add "merged_from" metadata
        """
        # Find primary recommendation
        primary_rec = next(
            (r for r in all_recommendations if r["id"] == primary_id), None
        )
        if not primary_rec:
            logger.error(f"Primary recommendation {primary_id} not found")
            return None

        # Find similar recommendations
        similar_recs = [r for r in all_recommendations if r["id"] in similar_ids]

        # Start with primary recommendation
        merged = primary_rec.copy()

        # Combine source books (deduplicate)
        all_source_books = set(primary_rec.get("source_books", []))
        for rec in similar_recs:
            all_source_books.update(rec.get("source_books", []))

        merged["source_books"] = sorted(list(all_source_books))

        # Merge reasoning
        reasoning_parts = [primary_rec.get("reasoning", "")]
        for rec in similar_recs:
            reasoning = rec.get("reasoning", "")
            if reasoning and reasoning not in reasoning_parts:
                reasoning_parts.append(
                    f"From {', '.join(rec.get('source_books', []))}: {reasoning}"
                )

        merged["reasoning"] = " ".join(filter(None, reasoning_parts))

        # Take highest priority
        priority_order = {"critical": 3, "important": 2, "nice_to_have": 1}
        all_priorities = [primary_rec.get("category", "nice_to_have")]
        all_priorities.extend(
            [rec.get("category", "nice_to_have") for rec in similar_recs]
        )

        highest_priority = max(all_priorities, key=lambda p: priority_order.get(p, 1))
        merged["category"] = highest_priority

        # Merge time estimates (average)
        time_estimates = []
        for rec in [primary_rec] + similar_recs:
            time_est = rec.get("time_estimate", "")
            if time_est and "week" in time_est.lower():
                # Extract number of weeks
                match = re.search(r"(\d+)", time_est)
                if match:
                    time_estimates.append(int(match.group(1)))

        if time_estimates:
            avg_weeks = sum(time_estimates) / len(time_estimates)
            merged["time_estimate"] = f"{avg_weeks:.1f} weeks"

        # Add metadata
        merged["merged_from"] = similar_ids
        merged["consolidation_date"] = datetime.now().isoformat()

        # Update ID to indicate consolidation
        merged["id"] = f"consolidated_{primary_id}"

        # Log consolidation
        self.consolidation_log.append(
            {
                "primary_id": primary_id,
                "merged_ids": similar_ids,
                "source_books": merged["source_books"],
                "final_category": highest_priority,
                "consolidation_date": merged["consolidation_date"],
            }
        )

        logger.info(
            f"Consolidated {len(similar_ids) + 1} recommendations into {merged['id']}"
        )

        return merged

    def consolidate_all(self) -> Dict:
        """
        Run full consolidation:
        1. Find all similar recommendation groups
        2. Merge each group
        3. Update master_recommendations.json
        4. Generate consolidation report
        """
        logger.info("Starting recommendation consolidation...")

        # Load current recommendations
        master_data = self.load_master_recommendations()
        recommendations = master_data.get("recommendations", [])

        if not recommendations:
            logger.warning("No recommendations found to consolidate")
            return {"consolidated": 0, "groups": 0, "original_count": 0}

        original_count = len(recommendations)

        # Find similar groups
        similar_groups = self.find_similar_recommendations(recommendations)

        if not similar_groups:
            logger.info("No similar recommendations found")
            return {
                "original_count": original_count,
                "consolidated_count": original_count,
                "groups_consolidated": 0,
                "recommendations_merged": 0,
                "reduction_percentage": 0,
                "consolidation_log": [],
                "timestamp": datetime.now().isoformat(),
            }

        # Create consolidated recommendations
        consolidated_recs = []
        processed_ids = set()

        # Process each group
        for primary_id, similar_ids in similar_groups.items():
            # Skip if already processed
            if primary_id in processed_ids:
                continue

            # Mark all IDs in this group as processed
            processed_ids.add(primary_id)
            processed_ids.update(similar_ids)

            # Merge recommendations
            merged_rec = self.merge_recommendations(
                primary_id, similar_ids, recommendations
            )
            if merged_rec:
                consolidated_recs.append(merged_rec)

        # Add non-consolidated recommendations
        for rec in recommendations:
            if rec["id"] not in processed_ids:
                consolidated_recs.append(rec)

        # Update master data
        master_data["recommendations"] = consolidated_recs

        # Rebuild indexes
        master_data["by_category"] = {}
        master_data["by_book"] = {}

        for rec in consolidated_recs:
            category = rec.get("category", "nice_to_have")
            if category not in master_data["by_category"]:
                master_data["by_category"][category] = []
            master_data["by_category"][category].append(rec["id"])

            for book in rec.get("source_books", []):
                master_data["by_book"].setdefault(book, []).append(rec["id"])

        # Save consolidated data
        self.save_master_recommendations(master_data)

        # Generate report
        consolidation_summary = {
            "original_count": original_count,
            "consolidated_count": len(consolidated_recs),
            "groups_consolidated": len(similar_groups),
            "recommendations_merged": sum(
                len(ids) + 1 for ids in similar_groups.values()
            ),
            "reduction_percentage": (
                ((original_count - len(consolidated_recs)) / original_count * 100)
                if original_count > 0
                else 0
            ),
            "consolidation_log": self.consolidation_log,
            "timestamp": datetime.now().isoformat(),
        }

        # Save consolidation report
        report_path = "analysis_results/consolidation_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(consolidation_summary, f, indent=2)

        logger.info(
            f"Consolidation complete: {original_count} -> {len(consolidated_recs)} recommendations"
        )
        logger.info(
            f"Consolidated {len(similar_groups)} groups, merged {sum(len(ids) + 1 for ids in similar_groups.values())} recommendations"
        )

        return consolidation_summary

    def generate_consolidation_report(self, summary: Dict) -> str:
        """Generate markdown consolidation report."""
        report = f"""# Recommendation Consolidation Report

**Generated:** {summary['timestamp']}

---

## Summary

- **Original Recommendations:** {summary['original_count']}
- **Consolidated Recommendations:** {summary['consolidated_count']}
- **Groups Consolidated:** {summary['groups_consolidated']}
- **Total Merged:** {summary['recommendations_merged']}
- **Reduction:** {summary['reduction_percentage']:.1f}%

---

## Consolidation Details

"""

        for i, log_entry in enumerate(summary["consolidation_log"], 1):
            report += f"""### Group {i}: {log_entry['primary_id']}

- **Primary ID:** {log_entry['primary_id']}
- **Merged IDs:** {', '.join(log_entry['merged_ids'])}
- **Source Books:** {', '.join(log_entry['source_books'])}
- **Final Category:** {log_entry['final_category']}
- **Consolidation Date:** {log_entry['consolidation_date']}

"""

        report += """---

## Impact

The consolidation process has:
- Reduced duplicate recommendations across books
- Combined similar concepts into unified recommendations
- Maintained all source book references
- Preserved the highest priority level for each group

---

*This report was generated by the Recommendation Consolidation System.*
"""

        return report


def main():
    """Main consolidation process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("🔄 Starting Recommendation Consolidation...")

    consolidator = RecommendationConsolidator()

    try:
        summary = consolidator.consolidate_all()

        print(f"\n✅ Consolidation Complete!")
        print(f"   📊 Original: {summary['original_count']} recommendations")
        print(f"   📊 Consolidated: {summary['consolidated_count']} recommendations")
        print(f"   📊 Groups: {summary['groups_consolidated']} consolidated")
        print(f"   📊 Reduction: {summary['reduction_percentage']:.1f}%")

        # Generate and save markdown report
        markdown_report = consolidator.generate_consolidation_report(summary)
        report_path = "analysis_results/consolidation_report.md"
        with open(report_path, "w") as f:
            f.write(markdown_report)

        print(f"   📄 Report saved: {report_path}")

    except Exception as e:
        logger.error(f"Consolidation failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
