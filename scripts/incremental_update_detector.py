#!/usr/bin/env python3
"""
Incremental Update Detector for NBA MCP Synthesis

This module detects changes since last analysis and enables incremental updates:
1. Track checksums of books, inventory, and configuration
2. Detect what changed (new books, modified data, updated config)
3. Cache previous analysis results
4. Only re-process changed items
5. Merge cached results with new results

Features:
- SHA-256 checksums for change detection
- JSON-based state tracking
- Intelligent cache invalidation
- Selective re-analysis
- Merge strategy for combining old and new results

Author: NBA MCP Synthesis Team
Date: 2025-10-22
"""

import json
import hashlib
import logging
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class FileState:
    """Represents the state of a file for change detection"""

    file_path: str
    checksum: str
    last_modified: str
    file_size: int

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AnalysisState:
    """Represents the state of the entire analysis"""

    timestamp: str
    books_analyzed: Dict[str, FileState]  # book_name -> file state
    inventory_state: Optional[FileState] = None
    config_state: Optional[FileState] = None
    recommendations_count: int = 0
    analysis_results: Dict[str, str] = field(
        default_factory=dict
    )  # book_name -> result file path

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "books_analyzed": {k: v.to_dict() for k, v in self.books_analyzed.items()},
            "inventory_state": (
                self.inventory_state.to_dict() if self.inventory_state else None
            ),
            "config_state": self.config_state.to_dict() if self.config_state else None,
            "recommendations_count": self.recommendations_count,
            "analysis_results": self.analysis_results,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AnalysisState":
        books_analyzed = {
            k: FileState(**v) for k, v in data.get("books_analyzed", {}).items()
        }
        inventory_state = (
            FileState(**data["inventory_state"])
            if data.get("inventory_state")
            else None
        )
        config_state = (
            FileState(**data["config_state"]) if data.get("config_state") else None
        )

        return cls(
            timestamp=data["timestamp"],
            books_analyzed=books_analyzed,
            inventory_state=inventory_state,
            config_state=config_state,
            recommendations_count=data.get("recommendations_count", 0),
            analysis_results=data.get("analysis_results", {}),
        )


class IncrementalUpdateDetector:
    """Detects and handles incremental updates to analysis"""

    STATE_FILE = ".analysis_state.json"

    def __init__(
        self, state_file: Optional[str] = None, cache_dir: Optional[str] = None
    ):
        """
        Initialize incremental update detector

        Args:
            state_file: Path to state file (default: .analysis_state.json in project root)
            cache_dir: Directory to cache analysis results (default: .analysis_cache/)
        """
        self.state_file = Path(state_file) if state_file else Path(self.STATE_FILE)
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".analysis_cache")
        self.cache_dir.mkdir(exist_ok=True)

        self.current_state: Optional[AnalysisState] = None
        self.previous_state: Optional[AnalysisState] = None

        logger.info(f"📊 IncrementalUpdateDetector initialized")
        logger.info(f"   State file: {self.state_file}")
        logger.info(f"   Cache dir: {self.cache_dir}")

    def load_previous_state(self) -> Optional[AnalysisState]:
        """Load previous analysis state from disk"""
        if not self.state_file.exists():
            logger.info("   No previous state found (first run)")
            return None

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)

            state = AnalysisState.from_dict(data)
            logger.info(f"✅ Loaded previous state from {self.state_file}")
            logger.info(f"   Previous analysis: {state.timestamp}")
            logger.info(f"   Books analyzed: {len(state.books_analyzed)}")
            logger.info(f"   Recommendations: {state.recommendations_count}")

            self.previous_state = state
            return state

        except Exception as e:
            logger.error(f"❌ Error loading previous state: {e}")
            return None

    def compute_file_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of file"""
        sha256 = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"❌ Error computing checksum for {file_path}: {e}")
            return ""

    def get_file_state(self, file_path: Path) -> FileState:
        """Get current state of a file"""
        checksum = self.compute_file_checksum(file_path)
        stat = file_path.stat()

        return FileState(
            file_path=str(file_path),
            checksum=checksum,
            last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            file_size=stat.st_size,
        )

    def detect_changes(
        self,
        books_dir: str,
        inventory_file: Optional[str] = None,
        config_file: Optional[str] = None,
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Detect changes since last analysis

        Args:
            books_dir: Directory containing books
            inventory_file: Path to inventory JSON file
            config_file: Path to project config file

        Returns:
            Tuple of (new_books, modified_books, deleted_books)
        """
        logger.info("🔍 Detecting changes since last analysis...")

        # Load previous state
        previous_state = self.load_previous_state()

        # Scan current books
        books_path = Path(books_dir)
        current_books: Dict[str, FileState] = {}

        if books_path.is_dir():
            # Look for PDFs
            for pdf_file in books_path.glob("**/*.pdf"):
                book_name = pdf_file.stem
                current_books[book_name] = self.get_file_state(pdf_file)

        logger.info(f"   Current books: {len(current_books)}")

        if not previous_state:
            # First run - all books are new
            logger.info("   ✨ First run - all books are new")
            return set(current_books.keys()), set(), set()

        # Compare with previous state
        previous_books = set(previous_state.books_analyzed.keys())
        current_books_set = set(current_books.keys())

        new_books = current_books_set - previous_books
        deleted_books = previous_books - current_books_set
        potentially_modified = current_books_set & previous_books

        # Check which books were actually modified
        modified_books = set()
        for book_name in potentially_modified:
            prev_state = previous_state.books_analyzed[book_name]
            curr_state = current_books[book_name]

            if prev_state.checksum != curr_state.checksum:
                modified_books.add(book_name)

        logger.info(f"   📊 Change detection results:")
        logger.info(f"      New books: {len(new_books)}")
        logger.info(f"      Modified books: {len(modified_books)}")
        logger.info(f"      Deleted books: {len(deleted_books)}")
        logger.info(
            f"      Unchanged books: {len(potentially_modified) - len(modified_books)}"
        )

        # Check inventory changes
        if inventory_file and Path(inventory_file).exists():
            curr_inventory = self.get_file_state(Path(inventory_file))
            prev_inventory = previous_state.inventory_state

            if prev_inventory and curr_inventory.checksum != prev_inventory.checksum:
                logger.info(
                    "   ⚠️  Inventory file changed - may need to re-validate all"
                )

        # Check config changes
        if config_file and Path(config_file).exists():
            curr_config = self.get_file_state(Path(config_file))
            prev_config = previous_state.config_state

            if prev_config and curr_config.checksum != prev_config.checksum:
                logger.info("   ⚠️  Config file changed - may need to re-analyze all")

        # Store current state for later
        self.current_state = AnalysisState(
            timestamp=datetime.now().isoformat(),
            books_analyzed=current_books,
            inventory_state=(
                self.get_file_state(Path(inventory_file))
                if inventory_file and Path(inventory_file).exists()
                else None
            ),
            config_state=(
                self.get_file_state(Path(config_file))
                if config_file and Path(config_file).exists()
                else None
            ),
        )

        return new_books, modified_books, deleted_books

    def get_books_to_analyze(
        self,
        books_dir: str,
        inventory_file: Optional[str] = None,
        config_file: Optional[str] = None,
        force_full: bool = False,
    ) -> List[str]:
        """
        Get list of books that need to be analyzed

        Args:
            books_dir: Directory containing books
            inventory_file: Path to inventory JSON
            config_file: Path to project config
            force_full: Force full re-analysis (ignore cache)

        Returns:
            List of book names to analyze
        """
        if force_full:
            logger.info("🔄 Force full analysis - analyzing all books")
            books_path = Path(books_dir)
            if books_path.is_dir():
                all_books = [pdf.stem for pdf in books_path.glob("**/*.pdf")]
                logger.info(f"   Found {len(all_books)} books")
                return all_books
            return []

        # Detect changes
        new_books, modified_books, deleted_books = self.detect_changes(
            books_dir, inventory_file, config_file
        )

        # Books to analyze = new + modified
        to_analyze = list(new_books | modified_books)

        if not to_analyze:
            logger.info("✅ No changes detected - all books up to date!")
        else:
            logger.info(f"📋 Books to analyze: {len(to_analyze)}")
            for book in sorted(to_analyze)[:10]:
                status = "NEW" if book in new_books else "MODIFIED"
                logger.info(f"   [{status}] {book}")
            if len(to_analyze) > 10:
                logger.info(f"   ... and {len(to_analyze) - 10} more")

        return to_analyze

    def cache_analysis_result(
        self, book_name: str, result_data: Dict, result_file: Optional[str] = None
    ):
        """
        Cache analysis result for a book

        Args:
            book_name: Name of the book
            result_data: Analysis result data (recommendations, etc.)
            result_file: Path to result file to copy to cache
        """
        cache_file = self.cache_dir / f"{book_name}_analysis.json"

        try:
            with open(cache_file, "w") as f:
                json.dump(result_data, f, indent=2)

            logger.info(f"💾 Cached analysis result for {book_name}")

            # Also copy result file if provided
            if result_file and Path(result_file).exists():
                cache_result_file = self.cache_dir / f"{book_name}_result.md"
                shutil.copy(result_file, cache_result_file)

        except Exception as e:
            logger.error(f"❌ Error caching result for {book_name}: {e}")

    def load_cached_result(self, book_name: str) -> Optional[Dict]:
        """
        Load cached analysis result for a book

        Args:
            book_name: Name of the book

        Returns:
            Cached result data or None if not found
        """
        cache_file = self.cache_dir / f"{book_name}_analysis.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)

            logger.info(f"📂 Loaded cached result for {book_name}")
            return data

        except Exception as e:
            logger.error(f"❌ Error loading cached result for {book_name}: {e}")
            return None

    def get_cached_recommendations(
        self, books_to_skip: Optional[Set[str]] = None
    ) -> List[Dict]:
        """
        Get cached recommendations for books that don't need re-analysis

        Args:
            books_to_skip: Set of book names to skip (being re-analyzed)

        Returns:
            List of cached recommendations
        """
        if not self.previous_state:
            return []

        books_to_skip = books_to_skip or set()
        cached_recs = []

        for book_name in self.previous_state.books_analyzed:
            if book_name in books_to_skip:
                continue

            cached_result = self.load_cached_result(book_name)
            if cached_result:
                # Extract recommendations
                recs = cached_result.get("recommendations", [])
                if isinstance(recs, list):
                    cached_recs.extend(recs)

        logger.info(f"📂 Loaded {len(cached_recs)} cached recommendations")
        return cached_recs

    def merge_results(
        self, cached_recommendations: List[Dict], new_recommendations: List[Dict]
    ) -> List[Dict]:
        """
        Merge cached and new recommendations

        Args:
            cached_recommendations: Recommendations from cache
            new_recommendations: Newly analyzed recommendations

        Returns:
            Merged list of recommendations
        """
        logger.info("🔀 Merging cached and new recommendations...")
        logger.info(f"   Cached: {len(cached_recommendations)}")
        logger.info(f"   New: {len(new_recommendations)}")

        # Simple merge: concatenate
        merged = cached_recommendations + new_recommendations

        logger.info(f"   Merged total: {len(merged)}")

        return merged

    def save_state(
        self,
        recommendations_count: int,
        analysis_results: Optional[Dict[str, str]] = None,
    ):
        """
        Save current analysis state to disk

        Args:
            recommendations_count: Total number of recommendations
            analysis_results: Map of book_name -> result_file_path
        """
        if not self.current_state:
            logger.warning("⚠️  No current state to save")
            return

        self.current_state.recommendations_count = recommendations_count
        if analysis_results:
            self.current_state.analysis_results = analysis_results

        try:
            with open(self.state_file, "w") as f:
                json.dump(self.current_state.to_dict(), f, indent=2)

            logger.info(f"💾 Saved analysis state to {self.state_file}")

        except Exception as e:
            logger.error(f"❌ Error saving state: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about incremental analysis"""
        stats = {
            "has_previous_state": self.previous_state is not None,
            "cache_size_mb": 0.0,
            "cached_books": 0,
        }

        if self.cache_dir.exists():
            # Calculate cache size
            total_size = sum(
                f.stat().st_size for f in self.cache_dir.glob("**/*") if f.is_file()
            )
            stats["cache_size_mb"] = total_size / (1024 * 1024)

            # Count cached books
            stats["cached_books"] = len(list(self.cache_dir.glob("*_analysis.json")))

        if self.previous_state:
            stats["previous_analysis_date"] = self.previous_state.timestamp
            stats["previous_books_count"] = len(self.previous_state.books_analyzed)
            stats["previous_recommendations_count"] = (
                self.previous_state.recommendations_count
            )

        return stats

    def clear_cache(self):
        """Clear all cached analysis results"""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir()
            logger.info("🗑️  Cleared analysis cache")

    def invalidate_book_cache(self, book_name: str):
        """Invalidate cache for a specific book"""
        cache_file = self.cache_dir / f"{book_name}_analysis.json"
        result_file = self.cache_dir / f"{book_name}_result.md"

        if cache_file.exists():
            cache_file.unlink()
        if result_file.exists():
            result_file.unlink()

        logger.info(f"🗑️  Invalidated cache for {book_name}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Detect incremental updates and manage analysis cache"
    )
    parser.add_argument(
        "--books-dir", default="books/", help="Directory containing books"
    )
    parser.add_argument("--inventory", help="Path to inventory JSON file")
    parser.add_argument("--config", help="Path to project config file")
    parser.add_argument(
        "--state-file", help="Path to state file (default: .analysis_state.json)"
    )
    parser.add_argument(
        "--cache-dir", help="Path to cache directory (default: .analysis_cache/)"
    )
    parser.add_argument(
        "--force-full", action="store_true", help="Force full analysis (ignore cache)"
    )
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear all cached results"
    )
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")

    args = parser.parse_args()

    # Initialize detector
    detector = IncrementalUpdateDetector(
        state_file=args.state_file, cache_dir=args.cache_dir
    )

    # Handle commands
    if args.clear_cache:
        detector.clear_cache()
        return 0

    if args.stats:
        stats = detector.get_statistics()
        logger.info("")
        logger.info("📊 Cache Statistics:")
        logger.info(f"   Has previous state: {stats['has_previous_state']}")
        logger.info(f"   Cache size: {stats['cache_size_mb']:.2f} MB")
        logger.info(f"   Cached books: {stats['cached_books']}")
        if stats["has_previous_state"]:
            logger.info(
                f"   Previous analysis: {stats.get('previous_analysis_date', 'Unknown')}"
            )
            logger.info(f"   Previous books: {stats.get('previous_books_count', 0)}")
            logger.info(
                f"   Previous recommendations: {stats.get('previous_recommendations_count', 0)}"
            )
        return 0

    # Detect changes and show what needs analysis
    to_analyze = detector.get_books_to_analyze(
        books_dir=args.books_dir,
        inventory_file=args.inventory,
        config_file=args.config,
        force_full=args.force_full,
    )

    if not to_analyze:
        logger.info("✅ No books need analysis - all up to date!")
    else:
        logger.info(f"📋 {len(to_analyze)} books need analysis")

    return 0


if __name__ == "__main__":
    exit(main())
