#!/usr/bin/env python3
"""
Recursive Book Analysis Workflow

Analyzes technical books using the MCP server, handles .acsm conversion,
tracks convergence until 3 consecutive "Nice-to-Have only" iterations,
and generates implementation plans.

Usage:
    python scripts/recursive_book_analysis.py --all
    python scripts/recursive_book_analysis.py --book "Econometric Analysis"
    python scripts/recursive_book_analysis.py --check-s3
    python scripts/recursive_book_analysis.py --upload-only
    python scripts/recursive_book_analysis.py --convert-acsm
    python scripts/recursive_book_analysis.py --resume <tracker_file>
"""

import argparse
import json
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AcsmConverter:
    """Handles conversion of DRM-protected .acsm files to PDF."""

    def __init__(self):
        # Try different possible paths for Adobe Digital Editions
        possible_paths = [
            "/Applications/Adobe Digital Editions.app",
            "/Applications/Adobe Digital Editions 4.5.app",
            "/Applications/Adobe Digital Editions 4.0.app",
        ]

        self.ade_app_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.ade_app_path = path
                break

        self.digital_editions_dir = os.path.expanduser("~/Documents/Digital Editions")

    def needs_conversion(self, file_path: str) -> bool:
        """Check if file is an .acsm file that needs conversion."""
        return file_path.endswith(".acsm")

    def is_ade_installed(self) -> bool:
        """Check if Adobe Digital Editions is installed."""
        return self.ade_app_path is not None

    def convert_acsm_with_ade(self, acsm_path: str, timeout: int = 60) -> Optional[str]:
        """
        Attempt to convert .acsm file using Adobe Digital Editions.

        Args:
            acsm_path: Path to .acsm file
            timeout: Seconds to wait for conversion

        Returns:
            Path to converted PDF if successful, None otherwise
        """
        if not self.is_ade_installed():
            logger.warning("Adobe Digital Editions not installed")
            return None

        try:
            # Open .acsm file with ADE
            logger.info(f"Opening {acsm_path} with Adobe Digital Editions...")
            subprocess.run(["open", "-a", self.ade_app_path, acsm_path])

            # Wait for conversion and check Digital Editions folder
            book_name = os.path.splitext(os.path.basename(acsm_path))[0]
            converted_pdf = self._wait_for_pdf(book_name, timeout)

            if converted_pdf:
                logger.info(f"✅ Successfully converted to: {converted_pdf}")
                return converted_pdf
            else:
                logger.warning(f"⏱️  Conversion timed out after {timeout}s")
                return None

        except Exception as e:
            logger.error(f"❌ Error during conversion: {e}")
            return None

    def _wait_for_pdf(self, book_name: str, timeout: int) -> Optional[str]:
        """Wait for PDF to appear in Digital Editions folder."""
        if not os.path.exists(self.digital_editions_dir):
            return None

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for PDF files that might match
            for filename in os.listdir(self.digital_editions_dir):
                if filename.endswith(".pdf") and book_name.lower() in filename.lower():
                    pdf_path = os.path.join(self.digital_editions_dir, filename)
                    return pdf_path

            time.sleep(2)  # Check every 2 seconds

        return None

    def prompt_manual_conversion(self, acsm_file: str) -> Optional[str]:
        """Prompt user with manual conversion instructions."""
        print(
            f"""
╔══════════════════════════════════════════════════════════════════╗
║           ⚠️  MANUAL CONVERSION REQUIRED                         ║
╚══════════════════════════════════════════════════════════════════╝

File: {acsm_file}

This is a DRM-protected .acsm file. Follow these steps:

1. Download Adobe Digital Editions:
   https://www.adobe.com/solutions/ebook/digital-editions/download.html

2. Install and open Adobe Digital Editions

3. Double-click: {acsm_file}
   (This will download the actual PDF)

4. Find the PDF in: {self.digital_editions_dir}

5. Copy it to Downloads folder as: Basketball_on_Paper.pdf

6. Rerun this script with: --resume

═══════════════════════════════════════════════════════════════════

Options:
  [Enter] - Skip this book for now
  [q]     - Quit script
  [c]     - Check if PDF was manually converted

Your choice: """,
            end="",
        )

        user_input = input().lower().strip()

        if user_input == "q":
            sys.exit(0)
        elif user_input == "c":
            # Check for manually converted PDF
            downloads_dir = os.path.expanduser("~/Downloads")
            basketball_pdf = os.path.join(downloads_dir, "Basketball_on_Paper.pdf")
            if os.path.exists(basketball_pdf):
                logger.info(f"✅ Found manually converted PDF: {basketball_pdf}")
                return basketball_pdf
            else:
                logger.warning(f"❌ PDF not found in Downloads folder")
                return None
        else:
            return None

    def check_google_books_alternative(self):
        """Display Google Books alternative instructions."""
        print(
            """
╔══════════════════════════════════════════════════════════════════╗
║           📱 ALTERNATIVE: Check Google Books                     ║
╚══════════════════════════════════════════════════════════════════╝

This book appears to be from Google Books.

1. Visit: https://play.google.com/books
2. Find "Basketball on Paper" in your library
3. Download as PDF (if available without DRM)
4. Save to Downloads folder as: Basketball_on_Paper.pdf

═══════════════════════════════════════════════════════════════════
"""
        )

    def handle_conversion(self, book: Dict) -> Optional[str]:
        """
        Handle complete conversion workflow for .acsm file.

        Returns:
            Path to converted PDF if successful, None otherwise
        """
        acsm_path = book["local_path"]

        if not os.path.exists(acsm_path):
            logger.error(f"❌ .acsm file not found: {acsm_path}")
            return None

        logger.info(f"🔄 Processing .acsm file: {book['title']}")

        # Try automated conversion first
        if self.is_ade_installed():
            converted_pdf = self.convert_acsm_with_ade(acsm_path)
            if converted_pdf:
                return converted_pdf

        # Fall back to manual instructions
        self.check_google_books_alternative()
        return self.prompt_manual_conversion(acsm_path)


class BookManager:
    """Manages book uploads and S3 operations."""

    def __init__(self, s3_bucket: str):
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3")
        self.converter = AcsmConverter()

    def book_exists_in_s3(self, s3_key: str) -> bool:
        """Check if book exists in S3 bucket."""
        try:
            self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                logger.error(f"Error checking S3: {e}")
                raise

    def upload_to_s3(self, local_path: str, s3_key: str) -> bool:
        """Upload file to S3 bucket."""
        try:
            logger.info(f"📤 Uploading {os.path.basename(local_path)} to S3...")
            self.s3_client.upload_file(local_path, self.s3_bucket, s3_key)
            logger.info(f"✅ Uploaded to s3://{self.s3_bucket}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False

    def check_and_upload_books(
        self, book_list: List[Dict], skip_conversion: bool = False
    ) -> Dict:
        """
        Check S3 status and upload missing books.

        Returns:
            Dictionary with categorized results
        """
        results = {
            "already_in_s3": [],
            "uploaded": [],
            "needs_conversion": [],
            "failed": [],
            "skipped": [],
        }

        for book in book_list:
            logger.info(f"\n{'='*70}")
            logger.info(f"Processing: {book['title']}")
            logger.info(f"{'='*70}")

            # Check if already marked as in S3
            if book.get("status") == "already_in_s3":
                logger.info(f"✅ Already in S3 (pre-marked): {book['s3_path']}")
                results["already_in_s3"].append(book)
                continue

            # Check S3 directly
            if self.book_exists_in_s3(book["s3_path"]):
                logger.info(f"✅ Already in S3: {book['s3_path']}")
                results["already_in_s3"].append(book)
                continue

            # Handle conversion if needed
            if book.get("requires_conversion"):
                if skip_conversion:
                    logger.info(
                        f"⏭️  Skipping conversion (--skip-conversion): {book['title']}"
                    )
                    results["skipped"].append(book)
                    continue

                if book["conversion_type"] == "acsm_to_pdf":
                    converted_path = self.converter.handle_conversion(book)
                    if converted_path:
                        if self.upload_to_s3(converted_path, book["s3_path"]):
                            results["uploaded"].append(book)
                        else:
                            results["failed"].append(book)
                    else:
                        logger.warning(f"⚠️  Conversion needed for: {book['title']}")
                        results["needs_conversion"].append(book)
            else:
                # Regular PDF upload
                local_path = book["local_path"]
                if os.path.exists(local_path):
                    if self.upload_to_s3(local_path, book["s3_path"]):
                        results["uploaded"].append(book)
                    else:
                        results["failed"].append(book)
                else:
                    logger.error(f"❌ File not found: {local_path}")
                    results["failed"].append(book)

        return results

    def print_summary(self, results: Dict):
        """Print summary of book upload results."""
        print(
            f"""
╔══════════════════════════════════════════════════════════════════╗
║                    📊 UPLOAD SUMMARY                             ║
╚══════════════════════════════════════════════════════════════════╝

✅ Already in S3:       {len(results['already_in_s3'])} books
📤 Newly uploaded:      {len(results['uploaded'])} books
🔄 Needs conversion:    {len(results['needs_conversion'])} books
⏭️  Skipped:            {len(results['skipped'])} books
❌ Failed:              {len(results['failed'])} books

Total processed:        {sum(len(v) for v in results.values())} books

═══════════════════════════════════════════════════════════════════
"""
        )

        if results["needs_conversion"]:
            print("Books requiring conversion:")
            for book in results["needs_conversion"]:
                print(f"  - {book['title']}")
            print()

        if results["failed"]:
            print("Failed uploads:")
            for book in results["failed"]:
                print(f"  - {book['title']}")
            print()


class ProjectScanner:
    """Scans project codebases to build knowledge base."""

    def __init__(self, project_paths: List[str]):
        self.project_paths = project_paths
        self.knowledge_base = {}

    def scan_projects(self) -> Dict:
        """
        Scan all project directories and build knowledge base.

        Returns:
            Dictionary with project structure, files, and implementations
        """
        logger.info("🔍 Scanning project codebases...")

        knowledge = {"projects": {}, "total_files": 0, "modules": [], "features": []}

        for project_path in self.project_paths:
            if not os.path.exists(project_path):
                logger.warning(f"⚠️  Project path not found: {project_path}")
                continue

            project_name = os.path.basename(project_path)
            logger.info(f"  Scanning: {project_name}")

            project_info = self._scan_directory(project_path)
            knowledge["projects"][project_name] = project_info
            knowledge["total_files"] += project_info["file_count"]
            knowledge["modules"].extend(project_info["modules"])
            knowledge["features"].extend(project_info["features"])

        self.knowledge_base = knowledge
        logger.info(
            f"✅ Scanned {knowledge['total_files']} files across {len(knowledge['projects'])} projects"
        )

        return knowledge

    def _scan_directory(self, path: str) -> Dict:
        """Scan a single directory and extract information."""
        info = {
            "path": path,
            "file_count": 0,
            "modules": [],
            "features": [],
            "structure": {},
        }

        # Ignore directories
        ignore_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "venv",
            "env",
            ".venv",
            "dist",
            "build",
        }

        for root, dirs, files in os.walk(path):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            rel_path = os.path.relpath(root, path)

            for file in files:
                if file.endswith(".py"):
                    info["file_count"] += 1
                    file_path = os.path.join(root, file)

                    # Extract module name
                    if file != "__init__.py":
                        module_name = file[:-3]  # Remove .py
                        info["modules"].append(
                            {
                                "name": module_name,
                                "path": os.path.relpath(file_path, path),
                            }
                        )

                    # Try to detect features by reading file
                    features = self._detect_features(file_path)
                    info["features"].extend(features)

        return info

    def _detect_features(self, file_path: str) -> List[str]:
        """Detect implemented features by scanning file content."""
        features = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

                # Look for class definitions
                if "class " in content:
                    import re

                    classes = re.findall(r"class\s+(\w+)", content)
                    features.extend([f"Class: {cls}" for cls in classes])
        except Exception as e:
            logger.debug(f"Error reading {file_path}: {e}")

        return features


class MasterRecommendations:
    """Manages master recommendations across all books."""

    def __init__(
        self, master_file: str = "analysis_results/master_recommendations.json"
    ):
        self.master_file = master_file
        self.recommendations = self._load_master()

    def _load_master(self) -> Dict:
        """Load existing master recommendations."""
        if os.path.exists(self.master_file):
            logger.info(f"📖 Loading master recommendations from {self.master_file}")
            with open(self.master_file, "r") as f:
                return json.load(f)
        else:
            logger.info("📝 Creating new master recommendations file")
            return {
                "recommendations": [],
                "by_category": {"critical": [], "important": [], "nice_to_have": []},
                "by_book": {},
                "last_updated": datetime.now().isoformat(),
            }

    def save_master(self):
        """Save master recommendations to file."""
        self.recommendations["last_updated"] = datetime.now().isoformat()

        os.makedirs(os.path.dirname(self.master_file), exist_ok=True)
        with open(self.master_file, "w") as f:
            json.dump(self.recommendations, f, indent=2)

        logger.info(f"💾 Saved master recommendations to {self.master_file}")

    def find_similar(self, new_rec: str, threshold: float = 0.7) -> Optional[Dict]:
        """
        Find similar recommendation in existing set.

        Uses simple string similarity for now.
        Could be enhanced with semantic similarity.
        """
        from difflib import SequenceMatcher

        # Ensure new_rec is a string
        if not isinstance(new_rec, str):
            new_rec = str(new_rec)

        for existing in self.recommendations["recommendations"]:
            similarity = SequenceMatcher(
                None, new_rec.lower(), existing["title"].lower()
            ).ratio()

            if similarity >= threshold:
                return existing

        return None

    def add_recommendation(self, rec: Dict, book_title: str):
        """Add or update recommendation in master list."""
        # Check for similar recommendation
        title = rec["title"] if isinstance(rec["title"], str) else str(rec["title"])
        similar = self.find_similar(title)

        if similar:
            # Update existing recommendation
            if book_title not in similar.get("source_books", []):
                similar.setdefault("source_books", []).append(book_title)

            # Potentially upgrade priority
            priority_order = {"nice_to_have": 0, "important": 1, "critical": 2}
            if priority_order.get(rec["category"], 0) > priority_order.get(
                similar.get("category"), 0
            ):
                logger.info(f"⬆️  Upgrading recommendation priority: {rec['title']}")
                similar["category"] = rec["category"]
        else:
            # Add new recommendation
            new_rec = {
                "id": f"rec_{len(self.recommendations['recommendations']) + 1}",
                "title": rec["title"],
                "category": rec["category"],
                "source_books": [book_title],
                "added_date": datetime.now().isoformat(),
            }

            if "reasoning" in rec:
                new_rec["reasoning"] = rec["reasoning"]

            self.recommendations["recommendations"].append(new_rec)
            self.recommendations["by_category"][rec["category"]].append(new_rec["id"])

            # Track by book
            if book_title not in self.recommendations["by_book"]:
                self.recommendations["by_book"][book_title] = []
            self.recommendations["by_book"][book_title].append(new_rec["id"])


class RecursiveAnalyzer:
    """Performs recursive MCP-based book analysis with intelligence layer."""

    def __init__(self, config: Dict):
        self.config = config
        self.s3_bucket = config["s3_bucket"]
        self.project_context = config["project_context"]
        self.convergence_threshold = config["convergence_threshold"]
        self.max_iterations = config["max_iterations"]

        # Initialize project scanner
        self.project_paths = config.get(
            "project_paths",
            [
                "/Users/ryanranft/nba-mcp-synthesis",
                "/Users/ryanranft/nba-simulator-aws",
            ],
        )
        self.scanner = ProjectScanner(self.project_paths)

        # Initialize master recommendations
        self.master_recs = MasterRecommendations()

        # Project knowledge base (loaded on first use)
        self.knowledge_base = None

    async def analyze_book_recursively(self, book: Dict, output_dir: str) -> Dict:
        """
        Analyze a book recursively until convergence with intelligence layer.

        Args:
            book: Book metadata dictionary
            output_dir: Directory for output files

        Returns:
            Analysis results dictionary
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"📚 Starting recursive analysis: {book['title']}")
        logger.info(f"{'='*70}\n")

        # Scan projects on first run (cached for subsequent books)
        if self.knowledge_base is None:
            self.knowledge_base = self.scanner.scan_projects()

        # Initialize tracking
        tracker = {
            "book_title": book["title"],
            "s3_path": book["s3_path"],
            "start_time": datetime.now().isoformat(),
            "iterations": [],
            "convergence_achieved": False,
            "convergence_iteration": None,
            "total_recommendations": {"critical": 0, "important": 0, "nice_to_have": 0},
            "new_recommendations": 0,
            "duplicate_recommendations": 0,
            "improved_recommendations": 0,
        }

        consecutive_nice_only = 0
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"\n🔄 Iteration {iteration}/{self.max_iterations}")

            # Run intelligent MCP analysis with deduplication
            recommendations = await self._analyze_with_mcp_and_intelligence(
                book, iteration
            )

            # Track iteration
            iteration_data = {
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "recommendations": recommendations,
            }
            tracker["iterations"].append(iteration_data)

            # Update totals
            for category in ["critical", "important", "nice_to_have"]:
                tracker["total_recommendations"][category] += len(
                    recommendations.get(category, [])
                )

            # Update master recommendations
            for category in ["critical", "important", "nice_to_have"]:
                for rec_title in recommendations.get(category, []):
                    self.master_recs.add_recommendation(
                        {"title": rec_title, "category": category}, book["title"]
                    )

            # Check convergence
            has_critical = len(recommendations.get("critical", [])) > 0
            has_important = len(recommendations.get("important", [])) > 0
            has_only_nice = (
                not has_critical
                and not has_important
                and len(recommendations.get("nice_to_have", [])) > 0
            )

            if has_only_nice:
                consecutive_nice_only += 1
                logger.info(
                    f"✅ Nice-to-Have only iteration ({consecutive_nice_only}/{self.convergence_threshold})"
                )

                if consecutive_nice_only >= self.convergence_threshold:
                    logger.info(
                        f"\n🎉 CONVERGENCE ACHIEVED after {iteration} iterations!"
                    )
                    tracker["convergence_achieved"] = True
                    tracker["convergence_iteration"] = iteration
                    break
            else:
                consecutive_nice_only = 0
                logger.info(f"🔄 Still finding Critical/Important recommendations")

        tracker["end_time"] = datetime.now().isoformat()
        tracker["total_iterations"] = iteration

        # Save master recommendations
        self.master_recs.save_master()

        # Save tracker
        tracker_file = os.path.join(
            output_dir,
            f"{self._sanitize_filename(book['title'])}_convergence_tracker.json",
        )
        with open(tracker_file, "w") as f:
            json.dump(tracker, f, indent=2)

        logger.info(f"\n✅ Tracker saved: {tracker_file}")

        return tracker

    async def analyze_with_existing_context(
        self, book: Dict, existing_recs: List[Dict], iteration: int
    ) -> Dict:
        """
        Analyze book with awareness of existing recommendations.
        Only return new items not already captured.

        Args:
            book: Book metadata dictionary
            existing_recs: List of existing recommendations from master DB
            iteration: Current iteration number

        Returns:
            Dict with categorized recommendations (only new ones)
        """
        logger.info(
            "🔍 Running context-aware analysis with existing recommendations..."
        )

        # Import four-model analyzer
        from four_model_book_analyzer import FourModelBookAnalyzer

        analyzer = FourModelBookAnalyzer()
        synthesis_result = await analyzer.analyze_book(book, existing_recs)

        # Convert to expected format
        recommendations = {
            "critical": [
                r
                for r in synthesis_result.recommendations
                if r.get("priority") == "CRITICAL"
            ],
            "important": [
                r
                for r in synthesis_result.recommendations
                if r.get("priority") == "IMPORTANT"
            ],
            "nice_to_have": [],  # Only include Critical/Important from consensus
        }

        # Add cost tracking info
        logger.info(f"💰 Analysis cost: ${synthesis_result.total_cost:.4f}")
        logger.info(f"   Google: ${synthesis_result.google_cost:.4f}")
        logger.info(f"   DeepSeek: ${synthesis_result.deepseek_cost:.4f}")
        logger.info(f"   Claude: ${synthesis_result.claude_cost:.4f}")
        logger.info(f"   GPT-4: ${synthesis_result.gpt4_cost:.4f}")
        logger.info(f"🔢 Tokens used: {synthesis_result.total_tokens:,}")
        logger.info(f"⏱️ Processing time: {synthesis_result.total_time:.1f}s")

        logger.info(
            f"  Found {sum(len(v) for v in recommendations.values())} NEW recommendations"
        )
        logger.info(f"    Critical: {len(recommendations.get('critical', []))}")
        logger.info(f"    Important: {len(recommendations.get('important', []))}")
        logger.info(f"    Nice-to-Have: {len(recommendations.get('nice_to_have', []))}")

        return recommendations

    def _format_existing_recs(self, existing_recs: List[Dict]) -> str:
        """Format existing recommendations for context."""
        if not existing_recs:
            return "No existing recommendations."

        context_parts = ["EXISTING RECOMMENDATIONS:"]

        for rec in existing_recs[:50]:  # Limit to first 50 for context
            title = rec.get("title", "N/A")
            category = rec.get("category", "N/A")
            source_books = ", ".join(rec.get("source_books", []))
            reasoning = rec.get("reasoning", "No reasoning provided")

            context_parts.append(f"- {title} ({category})")
            context_parts.append(f"  Source: {source_books}")
            context_parts.append(f"  Reasoning: {reasoning}")
            context_parts.append("")

        return "\n".join(context_parts)

    def _build_context_aware_prompt(
        self, book: Dict, existing_context: str, iteration: int
    ) -> str:
        """Build prompt for context-aware analysis."""

        prompt = f"""
Analyze the book "{book['title']}" with awareness of existing recommendations.

{existing_context}

INSTRUCTIONS:
- Focus ONLY on recommendations that are genuinely NEW or significantly different
- Do NOT recommend items already covered by existing recommendations
- Look for unique concepts, approaches, or techniques not already captured
- If a concept is similar to existing recommendations, only include it if it adds substantial new value
- Prioritize recommendations that complement rather than duplicate existing ones

BOOK CONTEXT:
- Title: {book['title']}
- Category: {book.get('category', 'Unknown')}
- Iteration: {iteration}

PROJECT CONTEXT:
- Main project: NBA MCP Synthesis (Machine Learning Platform)
- Related project: NBA Simulator AWS (Basketball Analytics)
- Focus: Production-ready ML systems, NBA analytics, MLOps best practices

Return recommendations in this format:
CRITICAL: [list of critical recommendations]
IMPORTANT: [list of important recommendations]
NICE-TO-HAVE: [list of nice-to-have recommendations]

Only include recommendations that are genuinely new or significantly different from existing ones.
"""
        return prompt

    def _simulated_context_aware_analysis(
        self, book: Dict, existing_recs: List[Dict], iteration: int, prompt: str
    ) -> Dict:
        """
        Simulated context-aware analysis that demonstrates filtering.
        In production, this would use real MCP tool calls.
        """
        # Extract existing recommendation titles for comparison
        existing_titles = {rec.get("title", "").lower() for rec in existing_recs}

        # Simulate some potential recommendations based on book category
        potential_recs = {"critical": [], "important": [], "nice_to_have": []}

        book_category = book.get("category", "").lower()

        if "statistics" in book_category:
            potential_recs["critical"].extend(
                [
                    "Advanced Statistical Testing Framework",
                    "Bayesian Analysis Pipeline",
                    "Statistical Model Validation System",
                ]
            )
            potential_recs["important"].extend(
                ["Hypothesis Testing Automation", "Statistical Power Analysis Tools"]
            )
            potential_recs["nice_to_have"].extend(
                ["Interactive Statistical Dashboards", "Statistical Report Generation"]
            )
        elif "machine_learning" in book_category:
            potential_recs["critical"].extend(
                [
                    "Advanced Feature Engineering Pipeline",
                    "Model Ensemble Framework",
                    "Hyperparameter Optimization System",
                ]
            )
            potential_recs["important"].extend(
                ["Model Interpretability Tools", "Automated Model Selection"]
            )
            potential_recs["nice_to_have"].extend(
                ["ML Experiment Tracking Dashboard", "Model Performance Visualization"]
            )
        elif "econometrics" in book_category:
            potential_recs["critical"].extend(
                [
                    "Time Series Analysis Framework",
                    "Panel Data Processing System",
                    "Causal Inference Pipeline",
                ]
            )
            potential_recs["important"].extend(
                ["Econometric Model Validation", "Statistical Significance Testing"]
            )
            potential_recs["nice_to_have"].extend(
                ["Econometric Visualization Tools", "Research Paper Generation"]
            )

        # Filter out recommendations that are too similar to existing ones
        filtered_recs = {"critical": [], "important": [], "nice_to_have": []}

        for category, recs in potential_recs.items():
            for rec in recs:
                rec_lower = rec.lower()

                # Check if this recommendation is too similar to existing ones
                is_duplicate = any(
                    self._calculate_similarity(rec_lower, existing_title) > 0.7
                    for existing_title in existing_titles
                )

                if not is_duplicate:
                    filtered_recs[category].append(rec)

        # Limit recommendations per iteration to simulate realistic analysis
        max_per_category = max(1, 3 - iteration)
        for category in filtered_recs:
            filtered_recs[category] = filtered_recs[category][:max_per_category]

        return filtered_recs

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        from difflib import SequenceMatcher

        return SequenceMatcher(None, text1, text2).ratio()

    async def _analyze_with_mcp_and_intelligence(
        self, book: Dict, iteration: int
    ) -> Dict:
        """
        Perform intelligent MCP analysis with deduplication and evaluation.

        This method:
        1. Reads book content via MCP
        2. Analyzes project codebases
        3. Compares concepts from book with existing implementations
        4. Checks for duplicate recommendations
        5. Only recommends new items or improvements

        Args:
            book: Book metadata
            iteration: Current iteration number

        Returns:
            Dict with categorized recommendations
        """
        logger.info("🤖 Running resilient analysis (Google + DeepSeek only)...")

        # Import resilient analyzer
        from resilient_book_analyzer import ResilientBookAnalyzer

        analyzer = ResilientBookAnalyzer()
        analysis_result = await analyzer.analyze_book(book)

        # Convert to expected format
        recommendations = {
            "critical": [
                r
                for r in synthesis_result.recommendations
                if r.get("priority") == "CRITICAL"
            ],
            "important": [
                r
                for r in synthesis_result.recommendations
                if r.get("priority") == "IMPORTANT"
            ],
            "nice_to_have": [],  # Only include Critical/Important from consensus
        }

        # Add cost tracking info
        logger.info(f"💰 Analysis cost: ${synthesis_result.total_cost:.4f}")
        logger.info(f"   Google: ${synthesis_result.google_cost:.4f}")
        logger.info(f"   DeepSeek: ${synthesis_result.deepseek_cost:.4f}")
        logger.info(f"   Claude: ${synthesis_result.claude_cost:.4f}")
        logger.info(f"   GPT-4: ${synthesis_result.gpt4_cost:.4f}")
        logger.info(f"🔢 Tokens used: {synthesis_result.total_tokens:,}")
        logger.info(f"⏱️ Processing time: {synthesis_result.total_time:.1f}s")

        logger.info(
            f"  Found {sum(len(v) for v in recommendations.values())} recommendations"
        )
        logger.info(f"    Critical: {len(recommendations.get('critical', []))}")
        logger.info(f"    Important: {len(recommendations.get('important', []))}")
        logger.info(f"    Nice-to-Have: {len(recommendations.get('nice_to_have', []))}")

        return recommendations

    def _build_intelligent_prompt(self, book: Dict, iteration: int) -> str:
        """Build comprehensive prompt for MCP with project context."""

        # Summarize existing implementations
        modules_summary = (
            f"{len(self.knowledge_base['modules'])} modules"
            if self.knowledge_base
            else "N/A"
        )
        features_summary = (
            f"{len(self.knowledge_base['features'])} features"
            if self.knowledge_base
            else "N/A"
        )

        # Summarize existing recommendations
        existing_recs_count = len(self.master_recs.recommendations["recommendations"])

        prompt = f"""
Analyze the book "{book['title']}" in the context of the NBA MCP Synthesis project.

PROJECT CONTEXT:
- Main project: /Users/ryanranft/nba-mcp-synthesis
- Related project: /Users/ryanranft/nba-simulator-aws
- Current modules: {modules_summary}
- Current features: {features_summary}
- Existing recommendations from previous books: {existing_recs_count}

ANALYSIS INSTRUCTIONS:
1. Read relevant sections of the book (iteration {iteration})
2. Identify key concepts and recommendations from the book
3. For EACH concept:
   a. Check if we already have this implemented in the projects
   b. Check if a similar recommendation exists from previous books
   c. Evaluate the quality of existing implementation (if any)

4. ONLY recommend if:
   - It's NOT already well-implemented
   - It's a NEW recommendation (not previously suggested)
   - OR it's an IMPROVEMENT to an existing recommendation

5. Categorize each recommendation:
   - CRITICAL: Security, stability, legal compliance
   - IMPORTANT: Performance, testing, maintainability
   - NICE-TO-HAVE: Polish, examples, minor improvements

6. For each recommendation, provide:
   - Clear title
   - Why it's needed
   - How it improves on what we have (if applicable)

GOAL: Avoid duplicate recommendations. Focus on gaps and meaningful improvements.
"""

        return prompt

    def _simulated_intelligent_analysis(
        self, book: Dict, iteration: int, prompt: str
    ) -> Dict:
        """
        Simulated intelligent analysis demonstrating deduplication logic.

        In production, this would call actual MCP tools:
        - mcp_nba-mcp-server_read_book (for book content)
        - mcp_nba-mcp-server_query_database (for project schema)
        - Custom analysis with project scanning results

        TODO: Replace with real MCP integration
        """

        # Simulate recommendations that decrease as we find fewer gaps
        if iteration == 1:
            return {
                "critical": [
                    "Implement model registry with versioning",
                    "Add comprehensive data validation pipeline",
                ],
                "important": [
                    "Enhance distributed tracing coverage",
                    "Add automated performance benchmarking",
                    "Implement feature importance tracking",
                ],
                "nice_to_have": [
                    "Add more comprehensive API examples",
                    "Improve inline documentation",
                ],
            }
        elif iteration == 2:
            # Some items already recommended/implemented
            return {
                "critical": [],  # Critical items addressed
                "important": [
                    "Add model drift detection alerts",
                    "Implement A/B testing statistical framework",
                ],
                "nice_to_have": [
                    "Create video tutorials",
                    "Add interactive documentation",
                ],
            }
        else:
            # Convergence: only minor improvements left
            return {
                "critical": [],
                "important": [],
                "nice_to_have": [
                    "Polish dashboard UI",
                    "Add code examples for edge cases",
                ],
            }

    def _sanitize_filename(self, filename: str) -> str:
        """Convert title to safe filename."""
        # Remove special characters
        safe = "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_"))
        return safe.replace(" ", "_")


class RecommendationGenerator:
    """Generates markdown reports from analysis results."""

    def generate_report(self, tracker: Dict, output_dir: str) -> str:
        """Generate comprehensive markdown report."""
        book_title = tracker["book_title"]
        safe_title = self._sanitize_filename(book_title)
        report_file = os.path.join(
            output_dir, f"{safe_title}_RECOMMENDATIONS_COMPLETE.md"
        )

        content = self._build_report_content(tracker)

        with open(report_file, "w") as f:
            f.write(content)

        logger.info(f"✅ Report generated: {report_file}")
        return report_file

    def _build_report_content(self, tracker: Dict) -> str:
        """Build markdown content for report."""
        book_title = tracker["book_title"]
        convergence_status = (
            "✅ ACHIEVED" if tracker["convergence_achieved"] else "❌ NOT ACHIEVED"
        )

        content = f"""# 📚 Recursive Analysis: {book_title}

**Analysis Date:** {tracker['start_time']}
**Total Iterations:** {tracker['total_iterations']}
**Convergence Status:** {convergence_status}
**Convergence Threshold:** 3 consecutive "Nice-to-Have only" iterations

---

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| Total Recommendations | {sum(tracker['total_recommendations'].values())} |
| Critical | {tracker['total_recommendations']['critical']} |
| Important | {tracker['total_recommendations']['important']} |
| Nice-to-Have | {tracker['total_recommendations']['nice_to_have']} |
| Iterations | {tracker['total_iterations']} |

---

## 🔄 Iteration Details

"""

        for iter_data in tracker["iterations"]:
            iter_num = iter_data["iteration"]
            recs = iter_data["recommendations"]

            content += f"""### Iteration {iter_num}

**Critical:** {len(recs.get('critical', []))}
**Important:** {len(recs.get('important', []))}
**Nice-to-Have:** {len(recs.get('nice_to_have', []))}

"""

            if recs.get("critical"):
                content += "#### 🔴 Critical\n\n"
                for rec in recs["critical"]:
                    content += f"- {rec}\n"
                content += "\n"

            if recs.get("important"):
                content += "#### 🟡 Important\n\n"
                for rec in recs["important"]:
                    content += f"- {rec}\n"
                content += "\n"

            if recs.get("nice_to_have"):
                content += "#### 🟢 Nice-to-Have\n\n"
                for rec in recs["nice_to_have"]:
                    content += f"- {rec}\n"
                content += "\n"

            content += "---\n\n"

        if tracker["convergence_achieved"]:
            content += f"""## 🎉 Convergence Achieved!

Convergence was achieved at iteration {tracker['convergence_iteration']}.

The system produced 3 consecutive iterations with ONLY Nice-to-Have recommendations,
indicating that all Critical and Important gaps have been identified and addressed.

"""
        else:
            content += """## ⚠️ Convergence Not Achieved

Maximum iterations reached without achieving convergence.
Consider extending max_iterations or reviewing analysis criteria.

"""

        content += f"""---

## 📝 Next Steps

1. Review all recommendations
2. Prioritize Critical items
3. Create implementation plans for Important items
4. Consider Nice-to-Have items for future iterations

---

**Generated:** {datetime.now().isoformat()}
**Book:** {book_title}
**S3 Path:** {tracker['s3_path']}
"""

        return content

    def _sanitize_filename(self, filename: str) -> str:
        """Convert title to safe filename."""
        safe = "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_"))
        return safe.replace(" ", "_")


class PlanGenerator:
    """Generates implementation plans from recommendations."""

    def generate_plans(self, tracker: Dict, output_dir: str) -> List[str]:
        """Generate implementation plans for recommendations."""
        book_title = tracker["book_title"]
        safe_title = self._sanitize_filename(book_title)

        # Create plans directory for this book
        plans_dir = os.path.join(output_dir, f"{safe_title}_plans")
        os.makedirs(plans_dir, exist_ok=True)

        generated_plans = []

        # Collect all unique recommendations
        all_recs = {"critical": set(), "important": set(), "nice_to_have": set()}

        for iter_data in tracker["iterations"]:
            recs = iter_data["recommendations"]
            for category in ["critical", "important", "nice_to_have"]:
                all_recs[category].update(recs.get(category, []))

        # Generate plans for critical and important items
        plan_num = 1
        for category in ["critical", "important"]:
            for rec in sorted(all_recs[category]):
                plan_file = self._generate_plan_file(
                    rec, category, plan_num, plans_dir, book_title
                )
                generated_plans.append(plan_file)
                plan_num += 1

        # Generate master README
        readme_file = self._generate_plans_readme(all_recs, plans_dir, book_title)
        generated_plans.append(readme_file)

        logger.info(f"✅ Generated {len(generated_plans)} implementation plans")
        return generated_plans

    def _generate_plan_file(
        self,
        recommendation: str,
        category: str,
        plan_num: int,
        plans_dir: str,
        book_title: str,
    ) -> str:
        """Generate individual implementation plan file."""
        safe_rec = self._sanitize_filename(recommendation)
        plan_file = os.path.join(plans_dir, f"{plan_num:02d}_{safe_rec}.md")

        priority = "🔴 HIGH" if category == "critical" else "🟡 MEDIUM"

        content = f"""# Implementation Plan: {recommendation}

**Source:** {book_title}
**Category:** {category.replace('_', ' ').title()}
**Priority:** {priority}
**Estimated Time:** TBD
**Difficulty:** TBD

---

## 🎯 Goal

{recommendation}

---

## 📋 Prerequisites

- [ ] Review current implementation
- [ ] Identify affected components
- [ ] Plan testing strategy

---

## 🔧 Implementation Steps

### Step 1: Analysis

Analyze current state and identify gaps.

### Step 2: Design

Design solution architecture.

### Step 3: Implementation

Implement the solution.

### Step 4: Testing

Write and run tests.

### Step 5: Documentation

Document the implementation.

---

## ✅ Success Criteria

- [ ] Feature implemented
- [ ] Tests passing
- [ ] Documentation complete
- [ ] Code reviewed

---

## 🧪 Testing

### Unit Tests

TBD

### Integration Tests

TBD

---

## 📚 References

- {book_title}

---

**Generated:** {datetime.now().isoformat()}
"""

        with open(plan_file, "w") as f:
            f.write(content)

        return plan_file

    def _generate_plans_readme(
        self, all_recs: Dict, plans_dir: str, book_title: str
    ) -> str:
        """Generate README for implementation plans."""
        readme_file = os.path.join(plans_dir, "README.md")

        total_plans = len(all_recs["critical"]) + len(all_recs["important"])

        content = f"""# 🚀 Implementation Plans: {book_title}

**Generated:** {datetime.now().isoformat()}
**Total Plans:** {total_plans}

---

## 📋 Plan Overview

### 🔴 Critical Priority ({len(all_recs['critical'])} plans)

"""

        plan_num = 1
        for rec in sorted(all_recs["critical"]):
            safe_rec = self._sanitize_filename(rec)
            content += f"{plan_num}. [{rec}]({plan_num:02d}_{safe_rec}.md)\n"
            plan_num += 1

        content += (
            f"\n### 🟡 Important Priority ({len(all_recs['important'])} plans)\n\n"
        )

        for rec in sorted(all_recs["important"]):
            safe_rec = self._sanitize_filename(rec)
            content += f"{plan_num}. [{rec}]({plan_num:02d}_{safe_rec}.md)\n"
            plan_num += 1

        content += """
---

## 🎯 Recommended Order

1. Complete all Critical plans first
2. Then work on Important plans
3. Nice-to-Have items can be done as time permits

---

## 📊 Progress Tracker

Track your implementation progress:

| # | Plan | Status | Date |
|---|------|--------|------|
"""

        plan_num = 1
        for category in ["critical", "important"]:
            for rec in sorted(all_recs[category]):
                content += f"| {plan_num} | {rec} | 🔲 TODO | - |\n"
                plan_num += 1

        content += """
---

## 📞 Support

Questions? Refer back to the analysis report or the source book.

---

**Good luck with your implementation!** 🚀
"""

        with open(readme_file, "w") as f:
            f.write(content)

        return readme_file

    def _sanitize_filename(self, filename: str) -> str:
        """Convert title to safe filename."""
        safe = "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_"))
        return safe.replace(" ", "_")


def load_config(config_path: str) -> Dict:
    """Load books configuration from JSON file."""
    with open(config_path, "r") as f:
        return json.load(f)


async def main():
    """Main entry point for recursive book analysis."""
    parser = argparse.ArgumentParser(
        description="Recursive Book Analysis Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/recursive_book_analysis.py --all
  python scripts/recursive_book_analysis.py --book "Econometric Analysis"
  python scripts/recursive_book_analysis.py --check-s3
  python scripts/recursive_book_analysis.py --upload-only
  python scripts/recursive_book_analysis.py --convert-acsm
  python scripts/recursive_book_analysis.py --resume tracker.json
        """,
    )

    parser.add_argument(
        "--all", action="store_true", help="Analyze all books in configuration"
    )
    parser.add_argument("--book", type=str, help="Analyze specific book by title")
    parser.add_argument(
        "--check-s3", action="store_true", help="Check which books are in S3"
    )
    parser.add_argument(
        "--upload-only", action="store_true", help="Upload missing books only"
    )
    parser.add_argument(
        "--convert-acsm", action="store_true", help="Handle .acsm conversions only"
    )
    parser.add_argument(
        "--resume",
        type=str,
        metavar="TRACKER_FILE",
        help="Resume previous analysis from tracker file",
    )
    parser.add_argument(
        "--skip-conversion", action="store_true", help="Skip books that need conversion"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/books_to_analyze.json",
        help="Path to books configuration file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="analysis_results",
        help="Output directory for results",
    )

    args = parser.parse_args()

    # Load configuration
    if not os.path.exists(args.config):
        logger.error(f"❌ Configuration file not found: {args.config}")
        sys.exit(1)

    config_data = load_config(args.config)
    books = config_data["books"]
    analysis_config = config_data.get(
        "analysis_config", config_data.get("analysis_settings", {})
    )

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize managers
    book_manager = BookManager(analysis_config["s3_bucket"])

    # Handle different commands
    if args.check_s3:
        logger.info("\n📋 Checking S3 status for all books...\n")
        for book in books:
            exists = book_manager.book_exists_in_s3(book["s3_path"])
            status = "✅ In S3" if exists else "❌ Missing"
            print(f"{status}: {book['title']}")
        return

    if args.upload_only:
        logger.info("\n📤 Uploading missing books to S3...\n")
        results = book_manager.check_and_upload_books(books, args.skip_conversion)
        book_manager.print_summary(results)
        return

    if args.convert_acsm:
        logger.info("\n🔄 Handling .acsm conversions...\n")
        converter = AcsmConverter()
        for book in books:
            if book.get("requires_conversion"):
                converter.handle_conversion(book)
        return

    if args.resume:
        logger.info(f"\n🔄 Resuming analysis from: {args.resume}\n")
        # TODO: Implement resume functionality
        logger.warning("⚠️  Resume functionality not yet implemented")
        return

    # Filter books if specific book requested
    books_to_analyze = books
    if args.book:
        books_to_analyze = [b for b in books if args.book.lower() in b["title"].lower()]
        if not books_to_analyze:
            logger.error(f"❌ Book not found: {args.book}")
            sys.exit(1)
    elif not args.all:
        logger.error("❌ Please specify --all or --book <title>")
        parser.print_help()
        sys.exit(1)

    # Upload books if needed
    logger.info("\n📤 Checking and uploading books to S3...\n")
    results = book_manager.check_and_upload_books(
        books_to_analyze, args.skip_conversion
    )
    book_manager.print_summary(results)

    # Analyze books
    analyzer = RecursiveAnalyzer(analysis_config)
    report_gen = RecommendationGenerator()
    plan_gen = PlanGenerator()

    analysis_results = []

    for book in books_to_analyze:
        # Skip if needs conversion and wasn't converted
        if book in results["needs_conversion"] or book in results["skipped"]:
            logger.warning(
                f"⏭️  Skipping analysis for: {book['title']} (needs conversion)"
            )
            continue

        # Run recursive analysis
        tracker = await analyzer.analyze_book_recursively(book, args.output_dir)

        # Generate report
        report_file = report_gen.generate_report(tracker, args.output_dir)

        # Generate implementation plans
        plan_files = plan_gen.generate_plans(tracker, args.output_dir)

        analysis_results.append(
            {
                "book": book,
                "tracker": tracker,
                "report_file": report_file,
                "plan_files": plan_files,
            }
        )

    # Generate master summary
    if len(analysis_results) > 1:
        _generate_master_summary(analysis_results, args.output_dir)

    logger.info(f"\n{'='*70}")
    logger.info("🎉 ANALYSIS COMPLETE!")
    logger.info(f"{'='*70}\n")
    logger.info(f"Results saved to: {args.output_dir}/")
    logger.info(f"Books analyzed: {len(analysis_results)}")


def _generate_master_summary(analysis_results: List[Dict], output_dir: str):
    """Generate master summary combining all book analyses."""
    summary_file = os.path.join(output_dir, "ALL_BOOKS_MASTER_SUMMARY.md")

    total_recs = {"critical": 0, "important": 0, "nice_to_have": 0}
    total_iterations = 0
    converged_count = 0

    content = f"""# 📚 Master Summary: All Books Analysis

**Generated:** {datetime.now().isoformat()}
**Total Books Analyzed:** {len(analysis_results)}

---

## 📊 Aggregate Statistics

"""

    for result in analysis_results:
        tracker = result["tracker"]
        total_iterations += tracker["total_iterations"]
        if tracker["convergence_achieved"]:
            converged_count += 1

        for category in ["critical", "important", "nice_to_have"]:
            total_recs[category] += tracker["total_recommendations"][category]

    content += f"""
| Metric | Value |
|--------|-------|
| Total Books | {len(analysis_results)} |
| Converged | {converged_count} |
| Total Iterations | {total_iterations} |
| Avg Iterations/Book | {total_iterations / len(analysis_results):.1f} |
| Total Critical | {total_recs['critical']} |
| Total Important | {total_recs['important']} |
| Total Nice-to-Have | {total_recs['nice_to_have']} |
| **Total Recommendations** | **{sum(total_recs.values())}** |

---

## 📖 Per-Book Results

"""

    for result in analysis_results:
        book = result["book"]
        tracker = result["tracker"]
        status = "✅" if tracker["convergence_achieved"] else "⏳"

        content += f"""### {status} {book['title']}

- **Iterations:** {tracker['total_iterations']}
- **Critical:** {tracker['total_recommendations']['critical']}
- **Important:** {tracker['total_recommendations']['important']}
- **Nice-to-Have:** {tracker['total_recommendations']['nice_to_have']}
- **Report:** [{os.path.basename(result['report_file'])}]({os.path.basename(result['report_file'])})

"""

    content += """---

## 🎯 Next Steps

1. Review individual book reports
2. Prioritize recommendations across all books
3. Implement Critical items first
4. Create consolidated implementation roadmap

---

**Happy implementing!** 🚀
"""

    with open(summary_file, "w") as f:
        f.write(content)

    logger.info(f"✅ Master summary generated: {summary_file}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
