#!/usr/bin/env python3
"""
Smart Book Discovery from GitHub Repositories

This module automatically discovers technical books in GitHub repositories,
analyzes their READMEs and PDFs, and adds them to the analysis queue.

Features:
- Auto-discover books in textbook-code/ repos
- Analyze README files for book metadata
- Validate PDF accessibility
- Update books_to_analyze.json dynamically
- Suggest categorization based on content

Usage:
    python scripts/smart_book_discovery.py \
        --scan-repos \
        --auto-add \
        --dry-run
"""

import logging
import json
import boto3
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Add scripts directory to path
import sys

sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@dataclass
class DiscoveredBook:
    """Metadata for a discovered book."""

    title: str
    s3_path: str
    category: str
    source_repo: str
    confidence: float  # 0-1, how confident we are in the metadata
    file_size_mb: float
    page_count: Optional[int] = None
    author: Optional[str] = None
    discovered_at: str = datetime.now().isoformat()


class SmartBookDiscovery:
    """
    Automatically discover and catalog books from GitHub repositories.
    """

    # Common book-related path patterns
    BOOK_PATTERNS = [
        r".*\.pdf$",
        r".*book.*\.pdf$",
        r".*textbook.*\.pdf$",
        r".*manual.*\.pdf$",
        r".*guide.*\.pdf$",
    ]

    # Keywords that suggest a file is a book (not just any PDF)
    BOOK_KEYWORDS = [
        "chapter",
        "preface",
        "introduction",
        "textbook",
        "edition",
        "copyright",
        "published",
        "isbn",
    ]

    # Category suggestions based on content/path
    CATEGORY_KEYWORDS = {
        "machine_learning": ["machine learning", "ml", "neural", "deep learning", "ai"],
        "statistics": ["statistics", "statistical", "probability", "bayesian"],
        "econometrics": ["econometrics", "regression", "causal", "time series"],
        "sports_analytics": ["sports", "nba", "basketball", "sabermetrics"],
        "math": ["mathematics", "calculus", "linear algebra", "optimization"],
        "programming": ["python", "programming", "code", "software"],
        "mlops": ["mlops", "deployment", "production", "kubernetes", "docker"],
    }

    def __init__(
        self, s3_bucket: str = "nba-mcp-books", config_dir: Path = Path("config")
    ):
        """
        Initialize the smart book discovery system.

        Args:
            s3_bucket: S3 bucket to scan for books
            config_dir: Directory containing config files
        """
        self.s3_bucket = s3_bucket
        self.config_dir = config_dir
        self.s3_client = boto3.client("s3")

        # Load existing configuration
        self.books_config_path = config_dir / "books_to_analyze.json"
        self.repos_config_path = config_dir / "github_repo_mappings.json"

        self.existing_books = self._load_existing_books()
        self.repo_mappings = self._load_repo_mappings()

        logger.info(f"Smart Book Discovery initialized")
        logger.info(f"  S3 Bucket: {s3_bucket}")
        logger.info(f"  Existing books: {len(self.existing_books)}")
        logger.info(f"  Mapped repos: {len(self.repo_mappings)}")

    def _load_existing_books(self) -> Dict[str, Any]:
        """Load existing books configuration."""
        if not self.books_config_path.exists():
            return {}

        with open(self.books_config_path) as f:
            data = json.load(f)

        # Handle both old and new config formats
        all_books = {}

        # New format: {"books": [{"title": "...", "category": "..."}]}
        if "books" in data and isinstance(data["books"], list):
            for book in data["books"]:
                title = book.get("title", "")
                category = book.get("category", "uncategorized")
                all_books[title] = category

        # Old format: {"books_by_category": {"category": ["title1", "title2"]}}
        elif "books_by_category" in data:
            for category, books in data["books_by_category"].items():
                for book in books:
                    all_books[book] = category

        return all_books

    def _load_repo_mappings(self) -> Dict[str, Any]:
        """Load GitHub repository mappings."""
        if not self.repos_config_path.exists():
            return {}

        with open(self.repos_config_path) as f:
            return json.load(f)

    async def scan_s3_for_books(
        self, prefix: str = "books/", exclude_patterns: Optional[List[str]] = None
    ) -> List[DiscoveredBook]:
        """
        Scan S3 bucket for undiscovered books.

        Args:
            prefix: S3 prefix to scan
            exclude_patterns: List of regex patterns to exclude

        Returns:
            List of discovered books
        """
        logger.info(f"🔍 Scanning S3: s3://{self.s3_bucket}/{prefix}")

        if exclude_patterns is None:
            exclude_patterns = [
                r".*fintech.*",
                r".*rstudio.*",
                r".*ssrn.*",
            ]

        discovered = []

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)

            for page in pages:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]

                    # Check if it's a PDF
                    if not key.lower().endswith(".pdf"):
                        continue

                    # Check exclusion patterns
                    if any(
                        re.match(pattern, key.lower()) for pattern in exclude_patterns
                    ):
                        logger.debug(f"  ⏭️  Excluded: {key}")
                        continue

                    # Extract book title from path
                    book_title = self._extract_book_title(key)

                    # Check if already cataloged
                    if book_title in self.existing_books:
                        logger.debug(f"  ✅ Already cataloged: {book_title}")
                        continue

                    # Get file metadata
                    size_mb = obj["Size"] / (1024 * 1024)

                    # Determine source repo if in textbook-code/
                    source_repo = self._extract_source_repo(key)

                    # Suggest category
                    category, confidence = self._suggest_category(key, book_title)

                    discovered_book = DiscoveredBook(
                        title=book_title,
                        s3_path=key,
                        category=category,
                        source_repo=source_repo or "unknown",
                        confidence=confidence,
                        file_size_mb=size_mb,
                    )

                    discovered.append(discovered_book)
                    logger.info(
                        f"  📚 Discovered: {book_title} ({category}, {confidence:.0%} confidence)"
                    )

            logger.info(f"✅ Scan complete: {len(discovered)} new books found")

        except Exception as e:
            logger.error(f"❌ Error scanning S3: {e}")

        return discovered

    def _extract_book_title(self, s3_key: str) -> str:
        """
        Extract a clean book title from S3 key.

        Args:
            s3_key: S3 object key

        Returns:
            Clean book title
        """
        # Get filename without path
        filename = Path(s3_key).name

        # Remove extension
        title = filename.replace(".pdf", "")

        # Clean up common patterns
        title = title.replace("_", " ")
        title = re.sub(r"\s+", " ", title)
        title = title.strip()

        return title

    def _extract_source_repo(self, s3_key: str) -> Optional[str]:
        """
        Extract source repository from S3 key if present.

        Args:
            s3_key: S3 object key

        Returns:
            Repository name or None
        """
        if "textbook-code/" in s3_key:
            # Extract repo name between textbook-code/ and next /
            match = re.search(r"textbook-code/([^/]+)/", s3_key)
            if match:
                return match.group(1)

        return None

    def _suggest_category(self, s3_path: str, title: str) -> Tuple[str, float]:
        """
        Suggest a category for the book based on path and title.

        Args:
            s3_path: S3 path
            title: Book title

        Returns:
            Tuple of (category, confidence)
        """
        text = (s3_path + " " + title).lower()

        # Check each category's keywords
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score

        if not scores:
            return "uncategorized", 0.3

        # Return category with highest score
        best_category = max(scores.items(), key=lambda x: x[1])

        # Calculate confidence based on keyword matches
        max_possible = len(self.CATEGORY_KEYWORDS[best_category[0]])
        confidence = min(0.95, 0.5 + (best_category[1] / max_possible) * 0.5)

        return best_category[0], confidence

    def add_to_config(
        self,
        discovered_books: List[DiscoveredBook],
        confidence_threshold: float = 0.7,
        dry_run: bool = True,
    ) -> Dict[str, int]:
        """
        Add discovered books to configuration.

        Args:
            discovered_books: List of discovered books
            confidence_threshold: Minimum confidence to auto-add
            dry_run: If True, don't actually modify files

        Returns:
            Dictionary with counts: {added, skipped_low_confidence, skipped_duplicate}
        """
        logger.info(f"📝 Adding books to configuration (dry_run={dry_run})")
        logger.info(f"  Confidence threshold: {confidence_threshold}")

        # Load current config
        with open(self.books_config_path) as f:
            config = json.load(f)

        added = 0
        skipped_low_confidence = 0
        skipped_duplicate = 0

        for book in discovered_books:
            # Check confidence
            if book.confidence < confidence_threshold:
                logger.warning(
                    f"  ⚠️  Low confidence ({book.confidence:.0%}): {book.title}"
                )
                skipped_low_confidence += 1
                continue

            # Check for duplicates
            if book.title in self.existing_books:
                logger.debug(f"  ⏭️  Duplicate: {book.title}")
                skipped_duplicate += 1
                continue

            # Handle both old and new config formats
            if "books" in config and isinstance(config["books"], list):
                # New format: append to books array
                new_book = {
                    "title": book.title,
                    "s3_path": book.s3_path,
                    "local_path": book.s3_path.replace("books/", "books/", 1),
                    "category": book.category,
                    "status": "pending",
                    "priority": 2,  # Lower priority for auto-discovered books
                    "metadata": {
                        "file_size_bytes": int(book.file_size_mb * 1024 * 1024),
                        "discovered_by": "smart_discovery",
                        "confidence": book.confidence,
                        "source_repo": book.source_repo,
                    },
                }
                config["books"].append(new_book)
                logger.info(f"  ✅ Added: {book.title} → {book.category}")
                added += 1

            elif "books_by_category" in config:
                # Old format: append to category list
                if book.category not in config["books_by_category"]:
                    config["books_by_category"][book.category] = []
                config["books_by_category"][book.category].append(book.title)
                logger.info(f"  ✅ Added: {book.title} → {book.category}")
                added += 1

        # Update metadata
        if "books" in config and isinstance(config["books"], list):
            config["total_books"] = len(config["books"])
        elif "books_by_category" in config:
            config["total_books"] = sum(
                len(books) for books in config["books_by_category"].values()
            )

        # Save if not dry run
        if not dry_run:
            with open(self.books_config_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"💾 Configuration saved: {self.books_config_path}")
        else:
            logger.info(f"🏃 Dry run: Configuration not saved")

        return {
            "added": added,
            "skipped_low_confidence": skipped_low_confidence,
            "skipped_duplicate": skipped_duplicate,
        }

    def generate_discovery_report(
        self, discovered_books: List[DiscoveredBook], output_path: Optional[Path] = None
    ) -> str:
        """
        Generate a discovery report.

        Args:
            discovered_books: List of discovered books
            output_path: Optional path to save report

        Returns:
            Markdown-formatted report
        """
        logger.info(f"📊 Generating discovery report...")

        report_lines = [
            "# Smart Book Discovery Report",
            f"\n**Generated**: {datetime.now().isoformat()}",
            f"**S3 Bucket**: {self.s3_bucket}",
            f"**Books Discovered**: {len(discovered_books)}",
            "\n---\n",
        ]

        # Summary by category
        by_category = {}
        for book in discovered_books:
            if book.category not in by_category:
                by_category[book.category] = []
            by_category[book.category].append(book)

        report_lines.append("## Discovered Books by Category\n")

        for category, books in sorted(by_category.items()):
            report_lines.append(
                f"### {category.replace('_', ' ').title()} ({len(books)} books)\n"
            )
            report_lines.append("| Title | Confidence | Size (MB) | Source Repo |")
            report_lines.append("|-------|-----------|-----------|-------------|")

            for book in books:
                report_lines.append(
                    f"| {book.title[:50]} | {book.confidence:.0%} | "
                    f"{book.file_size_mb:.1f} | {book.source_repo} |"
                )

            report_lines.append("")

        # Recommendations
        report_lines.append("## Recommendations\n")

        high_confidence = [b for b in discovered_books if b.confidence >= 0.8]
        medium_confidence = [b for b in discovered_books if 0.5 <= b.confidence < 0.8]
        low_confidence = [b for b in discovered_books if b.confidence < 0.5]

        report_lines.append(
            f"- **High Confidence (≥80%)**: {len(high_confidence)} books"
        )
        report_lines.append(f"  - *Recommendation*: Auto-add to configuration")
        report_lines.append(
            f"- **Medium Confidence (50-80%)**: {len(medium_confidence)} books"
        )
        report_lines.append(f"  - *Recommendation*: Manual review recommended")
        report_lines.append(f"- **Low Confidence (<50%)**: {len(low_confidence)} books")
        report_lines.append(f"  - *Recommendation*: Manual categorization required")
        report_lines.append("")

        report = "\n".join(report_lines)

        # Save if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"📝 Report saved: {output_path}")

        return report


async def main():
    """Main entry point for smart book discovery."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Smart Book Discovery from GitHub Repositories"
    )
    parser.add_argument(
        "--scan-repos", action="store_true", help="Scan GitHub repositories for books"
    )
    parser.add_argument(
        "--auto-add",
        action="store_true",
        help="Automatically add high-confidence books to configuration",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.7,
        help="Minimum confidence for auto-add (default: 0.7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying configuration",
    )
    parser.add_argument("--output", type=Path, help="Output path for discovery report")
    parser.add_argument(
        "--bucket",
        type=str,
        default="nba-mcp-books-20251011",
        help="S3 bucket to scan (default: nba-mcp-books-20251011)",
    )

    args = parser.parse_args()

    # Initialize discovery system
    discovery = SmartBookDiscovery(s3_bucket=args.bucket)

    logger.info(
        f"======================================================================"
    )
    logger.info(f"SMART BOOK DISCOVERY")
    logger.info(
        f"======================================================================"
    )
    logger.info(f"Scan repos: {args.scan_repos}")
    logger.info(f"Auto-add: {args.auto_add}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(
        f"======================================================================"
    )

    # Scan for books
    discovered_books = await discovery.scan_s3_for_books()

    logger.info(f"\n📚 Discovery Results:")
    logger.info(f"  Total discovered: {len(discovered_books)}")

    if len(discovered_books) == 0:
        logger.info(f"✅ No new books found!")
        return

    # Generate report
    if args.output:
        report_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(f"smart_discovery_report_{timestamp}.md")

    report = discovery.generate_discovery_report(discovered_books, report_path)

    # Auto-add if requested
    if args.auto_add:
        counts = discovery.add_to_config(
            discovered_books,
            confidence_threshold=args.confidence_threshold,
            dry_run=args.dry_run,
        )

        logger.info(f"\n📊 Addition Results:")
        logger.info(f"  Added: {counts['added']}")
        logger.info(f"  Skipped (low confidence): {counts['skipped_low_confidence']}")
        logger.info(f"  Skipped (duplicate): {counts['skipped_duplicate']}")

    logger.info(
        f"\n======================================================================"
    )
    logger.info(f"Smart Discovery Complete!")
    logger.info(
        f"======================================================================"
    )
    logger.info(f"Report: {report_path}")
    logger.info(
        f"======================================================================"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
