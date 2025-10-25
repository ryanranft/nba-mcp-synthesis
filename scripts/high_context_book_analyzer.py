#!/usr/bin/env python3
"""
High-Context Book Analyzer with Gemini 1.5 Pro and Claude Sonnet 4

Analyzes complete technical books using extended context windows (up to 250k tokens)
for comprehensive understanding and higher quality recommendations.

Key Features:
- Gemini 1.5 Pro: 2M token context, cost-effective
- Claude Sonnet 4: 1M token context, superior reasoning
- Reads up to 1M characters (~250k tokens) per book
- Dual-model consensus validation
- Simplified architecture compared to 4-model system

Usage:
    from scripts.high_context_book_analyzer import HighContextBookAnalyzer

    analyzer = HighContextBookAnalyzer()
    result = await analyzer.analyze_book(book_metadata)
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from synthesis.models.google_model_v2 import GoogleModelV2
from synthesis.models.claude_model_v2 import ClaudeModelV2
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class HighContextAnalysisResult:
    """Result from high-context book analysis"""

    success: bool
    recommendations: List[Dict[str, Any]]
    total_cost: float
    gemini_cost: float
    claude_cost: float
    total_tokens: int
    gemini_tokens: int
    claude_tokens: int
    total_time: float
    consensus_level: str  # "both", "gemini_only", "claude_only", "none"
    content_chars: int  # How many characters were analyzed
    pricing_tier: str  # "low" (<128k) or "high" (>128k)
    error: Optional[str] = None


class HighContextBookAnalyzer:
    """
    High-context book analyzer using Gemini 1.5 Pro and Claude Sonnet 4.

    Capabilities:
    - Reads up to 1M characters (~250k tokens) per book
    - Dual-model consensus validation
    - Cost-effective with tiered pricing
    - Full book comprehension

    Expected Performance:
    - Cost per book: ~$0.60-0.70
    - Time per book: 60-120 seconds
    - Recommendations: 30-60 per book
    - Context: 10× more than current system
    """

    # Content limits - allow full book reading
    # Note: Claude has 200k token limit, but Gemini can handle up to 2M tokens
    # System will gracefully handle if Claude exceeds limit
    MAX_CHARS = 1_000_000  # 1M characters (~250k tokens, full book capability)
    MAX_TOKENS = 250_000  # Explicit token limit for tracking

    def __init__(
        self,
        project: str = "nba-mcp-synthesis",
        context: str = "production",
        enable_cache: bool = True,
        use_local_books: bool = False,
        books_dir: Optional[str] = None,
        project_config_path: Optional[str] = None,
    ):
        """
        Initialize with Gemini 1.5 Pro and Claude Sonnet 4.

        Args:
            project: Project name for configuration
            context: Context for secrets (production, development, test)
            enable_cache: Whether to enable result caching
            use_local_books: If True, read books from local filesystem instead of S3
            books_dir: Directory to search for books (defaults to ~/Downloads)
            project_config_path: Path to project configuration JSON (for project-aware analysis)
        """
        logger.info(f"🚀 Initializing High-Context Book Analyzer")
        logger.info(
            f"📊 Max content: {self.MAX_CHARS:,} chars (~{self.MAX_TOKENS:,} tokens)"
        )
        logger.info(
            f"🤖 Models: Gemini 1.5 Pro (2M context) + Claude Sonnet 4 (1M context)"
        )

        self.use_local_books = use_local_books
        self.books_dir = books_dir
        self.project_config_path = project_config_path
        self.project_context = None

        # Load project context from workflow config or explicit path
        project_context_config = None

        # Try loading from workflow_config.yaml if not explicitly provided
        if not project_config_path:
            try:
                import yaml

                config_path = (
                    Path(__file__).parent.parent / "config" / "workflow_config.yaml"
                )
                if config_path.exists():
                    with open(config_path) as f:
                        workflow_config = yaml.safe_load(f)
                        if workflow_config.get("project_context", {}).get(
                            "enabled", False
                        ):
                            project_context_config = workflow_config["project_context"]
                            logger.info(
                                "🔍 Loading project context from workflow_config.yaml"
                            )
            except Exception as e:
                logger.warning(f"⚠️  Could not load workflow config: {e}")

        # Load project context if config path provided (legacy support)
        elif project_config_path:
            logger.info(f"🔍 Loading project context from: {project_config_path}")
            try:
                from scripts.project_code_analyzer import EnhancedProjectScanner

                scanner = EnhancedProjectScanner(project_config_path)
                self.project_context = scanner.scan_project_deeply()
                logger.info("✅ Project context loaded successfully")
                logger.info(
                    f"📂 Project: {self.project_context.get('project_info', {}).get('name', 'Unknown')}"
                )
            except Exception as e:
                logger.warning(f"⚠️  Failed to load project context: {e}")
                logger.warning("⚠️  Continuing without project context")
                self.project_context = None

        # Load context from workflow config
        if project_context_config:
            try:
                self.project_context = self._load_project_context_from_config(
                    project_context_config
                )
                logger.info("✅ Project context loaded from workflow config")
                if self.project_context:
                    projects = self.project_context.get("projects", [])
                    logger.info(f"📂 Loaded context for {len(projects)} project(s)")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load project context from config: {e}")
                logger.warning("⚠️  Continuing without project context")
                self.project_context = None

        if use_local_books:
            books_path = books_dir or str(Path.home() / "Downloads")
            logger.info(f"📚 Reading books from local filesystem: {books_path}")
        else:
            logger.info(f"📚 Reading books from S3")

        # Initialize cache
        self.enable_cache = enable_cache
        if enable_cache:
            from scripts.result_cache import ResultCache

            self.cache = ResultCache()
            logger.info("💾 Cache enabled")
        else:
            self.cache = None
            logger.info("⚠️  Cache disabled")

        # Load secrets
        logger.info(f"Loading secrets for project={project}, context={context}")
        try:
            from mcp_server.unified_secrets_manager import load_secrets_hierarchical

            secrets_context = context.upper()
            if context.lower() == "production":
                secrets_context = "WORKFLOW"
            elif context.lower() == "development":
                secrets_context = "DEVELOPMENT"
            elif context.lower() == "test":
                secrets_context = "TEST"

            success = load_secrets_hierarchical(project, "NBA", secrets_context)
            if not success:
                raise RuntimeError("Failed to load secrets")
            logger.info("✅ Secrets loaded successfully")
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
            raise RuntimeError(f"Error loading secrets: {e}")

        # Initialize configuration
        try:
            self.config = UnifiedConfigurationManager(project, context)
            logger.info("✅ Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise RuntimeError(f"Failed to load configuration: {e}")

        # Initialize models
        self.models_available = []

        # Gemini 1.5 Pro (primary reader)
        try:
            self.gemini_model = GoogleModelV2()
            self.models_available.append("Gemini 1.5 Pro")
            logger.info("✅ Gemini 1.5 Pro initialized")
        except Exception as e:
            logger.error(f"❌ Gemini 1.5 Pro initialization failed: {e}")
            self.gemini_model = None

        # Claude Sonnet 4 (synthesis validator)
        try:
            self.claude_model = ClaudeModelV2()
            self.models_available.append("Claude Sonnet 4")
            logger.info("✅ Claude Sonnet 4 initialized")
        except Exception as e:
            logger.error(f"❌ Claude Sonnet 4 initialization failed: {e}")
            self.claude_model = None

        if not self.models_available:
            raise RuntimeError("No models could be initialized. Check API keys.")

        logger.info(
            f"✅ High-Context Analyzer ready with {len(self.models_available)} models"
        )

    async def analyze_book(self, book: Dict[str, Any]) -> HighContextAnalysisResult:
        """
        Analyze book using both models with full context.

        Args:
            book: Book metadata dict with title, author, s3_key, etc.

        Returns:
            HighContextAnalysisResult with recommendations and metrics
        """
        start_time = datetime.now()

        logger.info(
            f"🚀 Starting high-context analysis: {book.get('title', 'Unknown')}"
        )
        logger.info(f"🤖 Models: {', '.join(self.models_available)}")

        # Get book content
        book_content = book.get("content", "")
        if not book_content:
            # Choose reader based on configuration with S3 fallback
            if self.use_local_books:
                logger.info("📚 Attempting to read book from local filesystem...")
                book_content = await self._read_book_from_local(book, self.books_dir)

                # Fallback to S3 if local read fails
                if not book_content:
                    logger.warning("⚠️  Book not found locally, falling back to S3...")
                    book_content = await self._read_book_from_s3(book)
                    if book_content:
                        logger.info("✅ Successfully retrieved book from S3 fallback")
            else:
                logger.info("📚 Reading book from S3...")
                book_content = await self._read_book_from_s3(book)

            if not book_content:
                return HighContextAnalysisResult(
                    success=False,
                    recommendations=[],
                    total_cost=0.0,
                    gemini_cost=0.0,
                    claude_cost=0.0,
                    total_tokens=0,
                    gemini_tokens=0,
                    claude_tokens=0,
                    total_time=0.0,
                    consensus_level="none",
                    content_chars=0,
                    pricing_tier="unknown",
                    error="No book content available",
                )

        # Check cache before expensive analysis
        if self.enable_cache and self.cache:
            content_hash = self.cache.get_content_hash(book_content)
            cached_result = self.cache.get_cached("book_analysis", content_hash)

            if cached_result:
                logger.info("💾 Using cached analysis result!")
                # Convert cached dict back to HighContextAnalysisResult
                return HighContextAnalysisResult(**cached_result)

        # Limit content size to MAX_CHARS
        original_length = len(book_content)
        if len(book_content) > self.MAX_CHARS:
            book_content = (
                book_content[: self.MAX_CHARS]
                + f"\n\n[Content truncated at {self.MAX_CHARS:,} characters for token limits]"
            )
            logger.info(
                f"📄 Truncated from {original_length:,} to {self.MAX_CHARS:,} chars"
            )

        logger.info(f"📖 Analyzing {len(book_content):,} characters")
        logger.info(f"🔢 Estimated ~{len(book_content) // 4:,} tokens")

        # Run both models in parallel
        model_results = {}

        # Gemini 1.5 Pro
        if self.gemini_model:
            logger.info("🔄 Analyzing with Gemini 1.5 Pro...")
            if self.project_context:
                logger.info("📂 Using project context for analysis")
            model_results["gemini"] = await self._run_gemini_analysis(
                book_content, book, timeout=180  # 3 minutes for large context
            )

        # Claude Sonnet 4
        if self.claude_model:
            logger.info("🔄 Analyzing with Claude Sonnet 4...")
            if self.project_context:
                logger.info("📂 Using project context for analysis")
            model_results["claude"] = await self._run_claude_analysis(
                book_content, book, timeout=180  # 3 minutes for large context
            )

        # Synthesize consensus
        synthesized_recs, consensus_level = self._synthesize_dual_consensus(
            model_results
        )

        # Validate recommendations (if project context available)
        if self.project_context:
            logger.info("🔍 Validating recommendations...")
            synthesized_recs = await self._validate_recommendations(synthesized_recs)

        # Prioritize recommendations (if project context available)
        if self.project_context:
            logger.info("📊 Prioritizing recommendations...")
            synthesized_recs = await self._prioritize_recommendations(synthesized_recs)

        # Calculate totals
        gemini_cost = model_results.get("gemini", {}).get("cost", 0.0)
        claude_cost = model_results.get("claude", {}).get("cost", 0.0)
        total_cost = gemini_cost + claude_cost

        gemini_tokens = model_results.get("gemini", {}).get(
            "tokens_input", 0
        ) + model_results.get("gemini", {}).get("tokens_output", 0)
        claude_tokens = model_results.get("claude", {}).get(
            "input_tokens", 0
        ) + model_results.get("claude", {}).get("output_tokens", 0)
        total_tokens = gemini_tokens + claude_tokens

        pricing_tier = model_results.get("gemini", {}).get("pricing_tier", "unknown")

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        logger.info(f"✅ High-context analysis complete!")
        logger.info(
            f"💰 Total cost: ${total_cost:.4f} (Gemini: ${gemini_cost:.4f}, Claude: ${claude_cost:.4f})"
        )
        logger.info(
            f"🔢 Total tokens: {total_tokens:,} (Gemini: {gemini_tokens:,}, Claude: {claude_tokens:,})"
        )
        logger.info(f"⏱️ Total time: {total_time:.1f}s")
        logger.info(f"📋 Final recommendations: {len(synthesized_recs)}")
        logger.info(f"🎯 Consensus level: {consensus_level}")
        logger.info(f"💰 Pricing tier: {pricing_tier}")

        result = HighContextAnalysisResult(
            success=True,
            recommendations=synthesized_recs,
            total_cost=total_cost,
            gemini_cost=gemini_cost,
            claude_cost=claude_cost,
            total_tokens=total_tokens,
            gemini_tokens=gemini_tokens,
            claude_tokens=claude_tokens,
            total_time=total_time,
            consensus_level=consensus_level,
            content_chars=len(book_content),
            pricing_tier=pricing_tier,
        )

        # Save to cache for future use
        if self.enable_cache and self.cache:
            content_hash = self.cache.get_content_hash(book_content)
            self.cache.save_to_cache(
                "book_analysis",
                content_hash,
                result.__dict__,
                metadata={
                    "book_title": book.get("title", "Unknown"),
                    "book_author": book.get("author", "Unknown"),
                    "analysis_date": datetime.now().isoformat(),
                    "models_used": self.models_available,
                    "content_length": len(book_content),
                },
            )

        return result

    async def _run_gemini_analysis(
        self, content: str, metadata: Dict, timeout: int
    ) -> Dict:
        """Run Gemini 1.5 Pro analysis with error handling."""
        try:
            result = await asyncio.wait_for(
                self.gemini_model.analyze_book_content(
                    book_content=content,
                    book_metadata=metadata,
                    project_context=self.project_context,
                ),
                timeout=timeout,
            )

            if result.get("success", False):
                logger.info(
                    f"✅ Gemini 1.5 Pro complete: {len(result.get('recommendations', []))} recommendations"
                )
                return result
            else:
                logger.warning(
                    f"⚠️ Gemini 1.5 Pro failed: {result.get('error', 'Unknown')}"
                )
                return {
                    "success": False,
                    "recommendations": [],
                    "cost": 0.0,
                    "tokens_input": 0,
                    "tokens_output": 0,
                }

        except asyncio.TimeoutError:
            logger.error(f"❌ Gemini 1.5 Pro timed out after {timeout}s")
            return {
                "success": False,
                "recommendations": [],
                "cost": 0.0,
                "tokens_input": 0,
                "tokens_output": 0,
            }
        except Exception as e:
            logger.error(f"❌ Gemini 1.5 Pro failed: {str(e)}")
            return {
                "success": False,
                "recommendations": [],
                "cost": 0.0,
                "tokens_input": 0,
                "tokens_output": 0,
            }

    async def _run_claude_analysis(
        self, content: str, metadata: Dict, timeout: int
    ) -> Dict:
        """Run Claude Sonnet 4 analysis with error handling."""
        try:
            result = await asyncio.wait_for(
                self.claude_model.analyze_book(
                    book_content=content,
                    book_title=metadata.get("title", "Unknown"),
                    book_metadata=metadata,
                    project_context=self.project_context,
                ),
                timeout=timeout,
            )

            if result.get("success", False):
                logger.info(
                    f"✅ Claude Sonnet 4 complete: {len(result.get('recommendations', []))} recommendations"
                )
                return result
            else:
                logger.warning(
                    f"⚠️ Claude Sonnet 4 failed: {result.get('error', 'Unknown')}"
                )
                return {
                    "success": False,
                    "recommendations": [],
                    "cost": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                }

        except asyncio.TimeoutError:
            logger.error(f"❌ Claude Sonnet 4 timed out after {timeout}s")
            return {
                "success": False,
                "recommendations": [],
                "cost": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
            }
        except Exception as e:
            logger.error(f"❌ Claude Sonnet 4 failed: {str(e)}")
            return {
                "success": False,
                "recommendations": [],
                "cost": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
            }

    def _synthesize_dual_consensus(self, model_results: Dict) -> tuple[List[Dict], str]:
        """
        Synthesize recommendations from both models with consensus tagging.

        Consensus levels:
        - "both": Both models succeeded
        - "gemini_only": Only Gemini succeeded
        - "claude_only": Only Claude succeeded
        - "none": Neither succeeded
        """
        all_recs = []

        gemini_success = model_results.get("gemini", {}).get("success", False)
        claude_success = model_results.get("claude", {}).get("success", False)

        # Collect recommendations from both models
        if gemini_success:
            for rec in model_results["gemini"].get("recommendations", []):
                rec_copy = rec.copy()
                rec_copy["_source"] = "gemini"
                all_recs.append(rec_copy)

        if claude_success:
            for rec in model_results["claude"].get("recommendations", []):
                rec_copy = rec.copy()
                rec_copy["_source"] = "claude"
                all_recs.append(rec_copy)

        if not all_recs:
            return [], "none"

        # Determine consensus level
        if gemini_success and claude_success:
            consensus_level = "both"
        elif gemini_success:
            consensus_level = "gemini_only"
        elif claude_success:
            consensus_level = "claude_only"
        else:
            consensus_level = "none"

        # Group similar recommendations (70% similarity threshold)
        deduplicated_recs = self._group_similar_recommendations(all_recs)

        logger.info(f"📊 Collected {len(all_recs)} raw recommendations")
        logger.info(f"📊 After deduplication: {len(deduplicated_recs)} recommendations")

        return deduplicated_recs, consensus_level

    def _group_similar_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Group similar recommendations and mark consensus."""
        if not recommendations:
            return []

        groups = []

        for rec in recommendations:
            title = rec.get("title", "")
            if not title:
                continue

            # Find similar group
            found_group = False
            for group in groups:
                group_title = group[0].get("title", "")
                similarity = SequenceMatcher(
                    None, title.lower(), group_title.lower()
                ).ratio()

                if similarity >= 0.70:  # 70% similarity threshold
                    group.append(rec)
                    found_group = True
                    break

            if not found_group:
                groups.append([rec])

        # For each group, use the one from Claude if available (higher quality),
        # otherwise use Gemini, and tag with consensus info
        final_recs = []
        for group in groups:
            sources = [r["_source"] for r in group]

            # Prefer Claude's version if available
            claude_recs = [r for r in group if r["_source"] == "claude"]
            if claude_recs:
                chosen = claude_recs[0]
            else:
                chosen = group[0]

            # Add consensus metadata
            chosen["_consensus"] = {
                "sources": sources,
                "count": len(sources),
                "both_agree": "gemini" in sources and "claude" in sources,
            }

            final_recs.append(chosen)

        return final_recs

    async def _read_book_from_local(
        self, book: Dict, books_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Read book content from local filesystem (default: ~/Downloads).

        Args:
            book: Book metadata dict with title and optional filename
            books_dir: Directory to search for books (defaults to ~/Downloads)

        Returns:
            Full text content of the book, or None if not found
        """
        try:
            import pymupdf  # PyMuPDF for PDF extraction
            from pathlib import Path
            import re

            # Default to Downloads folder
            if books_dir is None:
                books_dir = str(Path.home() / "Downloads")

            books_path = Path(books_dir)
            if not books_path.exists():
                logger.error(f"Books directory does not exist: {books_dir}")
                return None

            # Get book title and create search pattern
            book_title = book.get("title", "")
            if not book_title:
                logger.error("No book title provided for local search")
                return None

            # Check if filename is explicitly provided
            if "local_filename" in book:
                target_file = books_path / book["local_filename"]
                if target_file.exists() and target_file.suffix.lower() == ".pdf":
                    logger.info(f"📥 Reading from local file: {target_file.name}")
                    pdf_files = [target_file]
                else:
                    logger.error(f"Specified file not found: {book['local_filename']}")
                    return None
            else:
                # Search for matching PDF files
                # Clean title for filename matching (remove special chars, normalize spaces)
                clean_title = re.sub(r"[^\w\s-]", "", book_title.lower())
                clean_title_parts = clean_title.split()

                logger.info(f"🔍 Searching for PDFs matching: {book_title}")

                # Find all PDFs in directory
                pdf_files = list(books_path.glob("*.pdf"))

                if not pdf_files:
                    logger.warning(f"No PDF files found in {books_dir}")
                    return None

                logger.info(f"📂 Found {len(pdf_files)} PDFs in {books_dir}")

                # Score each PDF by title match
                best_match = None
                best_score = 0

                for pdf_file in pdf_files:
                    # Clean filename for comparison
                    filename_clean = re.sub(r"[^\w\s-]", "", pdf_file.stem.lower())

                    # Count matching words
                    filename_parts = filename_clean.split()
                    matches = sum(
                        1 for part in clean_title_parts if part in filename_parts
                    )
                    score = matches / len(clean_title_parts) if clean_title_parts else 0

                    if score > best_score:
                        best_score = score
                        best_match = pdf_file

                # Require at least 30% word match
                if best_score < 0.3:
                    logger.error(
                        f"No good filename match found for '{book_title}' (best score: {best_score:.2%})"
                    )
                    logger.info(
                        f"💡 Tip: Add 'local_filename' to book metadata for exact match"
                    )
                    return None

                pdf_files = [best_match]
                logger.info(
                    f"📖 Best match: {best_match.name} (score: {best_score:.2%})"
                )

            # Extract text from PDF
            pdf_path = pdf_files[0]
            logger.info(f"📚 Extracting text from {pdf_path.name}...")

            doc = pymupdf.open(pdf_path)

            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())

            full_text = "\n\n".join(text_parts)
            logger.info(
                f"✅ Extracted {len(full_text):,} characters from {len(doc)} pages"
            )

            doc.close()
            return full_text

        except Exception as e:
            logger.error(f"❌ Failed to read book from local filesystem: {e}")
            return None

    async def _read_book_from_s3(self, book: Dict) -> Optional[str]:
        """Read book content from S3."""
        try:
            import boto3
            import pymupdf  # PyMuPDF for PDF extraction
            from io import BytesIO

            s3_client = boto3.client("s3")
            # Get S3 bucket from environment or book metadata
            bucket = os.environ.get("NBA_MCP_S3_BUCKET") or book.get(
                "s3_bucket", "nba-mcp-books-20251011"
            )
            # Check both s3_path and s3_key for compatibility
            s3_key = book.get("s3_path") or book.get("s3_key", "")

            if not s3_key:
                logger.error(
                    f"No S3 path/key provided for book: {book.get('title', 'Unknown')}"
                )
                return None

            logger.info(f"📥 Reading from S3: {s3_key}")

            # Download from S3
            response = s3_client.get_object(Bucket=bucket, Key=s3_key)
            pdf_bytes = response["Body"].read()

            # Extract text from PDF
            logger.info("📚 Extracting text from PDF...")
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())

            full_text = "\n\n".join(text_parts)
            logger.info(
                f"✅ Extracted {len(full_text):,} characters from {len(doc)} pages"
            )

            doc.close()
            return full_text

        except Exception as e:
            logger.error(f"❌ Failed to read book from S3: {e}")
            return None

    async def _validate_recommendations(
        self, recommendations: List[Dict]
    ) -> List[Dict]:
        """
        Validate recommendations for quality and feasibility.

        Args:
            recommendations: List of recommendation dictionaries

        Returns:
            Validated and potentially filtered recommendations with validation metadata
        """
        from scripts.recommendation_validator import RecommendationValidator

        # Initialize validator with project inventory
        validator = RecommendationValidator(
            project_inventory=(
                self.project_context if hasattr(self, "project_context") else None
            )
        )

        validated_recs = []
        validation_stats = {
            "total": len(recommendations),
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }

        logger.info(f"🔍 Validating {len(recommendations)} recommendations...")

        for idx, rec in enumerate(recommendations):
            # Validate recommendation
            result = validator.validate_recommendation(rec)

            # Add validation metadata to recommendation
            rec["validation"] = {
                "passed": result.passed,
                "warnings_count": len(result.warnings),
                "errors_count": len(result.errors),
                "warnings": result.warnings,
                "errors": result.errors,
                "suggestions": result.suggestions,
            }

            if result.passed:
                validation_stats["passed"] += 1
                validated_recs.append(rec)
            else:
                validation_stats["failed"] += 1
                # Still include failed recommendations but mark them
                rec["validation"]["status"] = "NEEDS_REVIEW"
                validated_recs.append(rec)

            if result.warnings:
                validation_stats["warnings"] += 1

            # Log validation results for important issues
            if result.errors:
                logger.warning(
                    f"⚠️  Validation errors in '{rec.get('title', 'Unknown')}': {len(result.errors)} errors"
                )
                for error in result.errors[:3]:  # Show first 3 errors
                    logger.warning(f"   - {error}")

        # Summary
        logger.info(f"✅ Validation complete:")
        logger.info(
            f"   - Passed: {validation_stats['passed']}/{validation_stats['total']}"
        )
        logger.info(
            f"   - Failed: {validation_stats['failed']}/{validation_stats['total']}"
        )
        logger.info(
            f"   - With warnings: {validation_stats['warnings']}/{validation_stats['total']}"
        )

        return validated_recs

    async def _prioritize_recommendations(
        self, recommendations: List[Dict]
    ) -> List[Dict]:
        """
        Prioritize recommendations by impact, effort, and feasibility.

        Args:
            recommendations: List of recommendation dictionaries

        Returns:
            Prioritized and sorted recommendations with priority scores
        """
        from scripts.recommendation_prioritizer import RecommendationPrioritizer

        # Initialize prioritizer with project inventory
        prioritizer = RecommendationPrioritizer(
            project_inventory=(
                self.project_context if hasattr(self, "project_context") else None
            )
        )

        # Prioritize all recommendations
        prioritized_recs = prioritizer.prioritize_recommendations(recommendations)

        # Log category breakdown
        categories = {}
        tiers = {}

        for rec in prioritized_recs:
            score = rec.get("priority_score", {})
            category = score.get("category", "Unknown")
            tier = score.get("tier", "MEDIUM")

            categories[category] = categories.get(category, 0) + 1
            tiers[tier] = tiers.get(tier, 0) + 1

        logger.info(f"✅ Prioritization complete:")
        logger.info(f"   Categories:")
        for cat in [
            "Quick Win",
            "Strategic Project",
            "Medium Priority",
            "Low Priority",
        ]:
            count = categories.get(cat, 0)
            if count > 0:
                logger.info(f"     - {cat}: {count}")

        logger.info(f"   Priority Tiers:")
        for tier in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = tiers.get(tier, 0)
            if count > 0:
                logger.info(f"     - {tier}: {count}")

        return prioritized_recs

    def _load_project_context_from_config(self, config: Dict) -> Optional[Dict]:
        """
        Load project context from workflow config.

        Args:
            config: Project context configuration from workflow_config.yaml

        Returns:
            Dictionary containing project context information
        """
        import os

        context = {
            "projects": [],
            "context_files_content": {},
            "max_context_size": config.get("max_context_size", 500000),
        }

        # Scan each project
        for project_config in config.get("scan_projects", []):
            project_path = project_config.get("path")
            project_name = project_config.get("name")

            if not os.path.exists(project_path):
                logger.warning(f"⚠️  Project path not found: {project_path}")
                continue

            logger.info(f"📂 Scanning project: {project_name}")

            project_info = {
                "name": project_name,
                "path": project_path,
                "files": [],
                "readme_content": None,
            }

            # Read README if requested
            if project_config.get("include_readme", False):
                readme_path = os.path.join(project_path, "README.md")
                if os.path.exists(readme_path):
                    try:
                        with open(readme_path, "r", encoding="utf-8") as f:
                            project_info["readme_content"] = f.read()
                        logger.info(
                            f"  ✅ Loaded README.md ({len(project_info['readme_content'])} chars)"
                        )
                    except Exception as e:
                        logger.warning(f"  ⚠️  Could not read README: {e}")

            # Scan project structure (limited depth for performance)
            scan_depth = project_config.get("scan_depth", 2)
            try:
                for root, dirs, files in os.walk(project_path):
                    # Calculate current depth
                    depth = root[len(project_path) :].count(os.sep)
                    if depth > scan_depth:
                        continue

                    # Skip common ignore patterns
                    dirs[:] = [
                        d
                        for d in dirs
                        if d
                        not in [
                            ".git",
                            "__pycache__",
                            "node_modules",
                            "venv",
                            ".venv",
                            "dist",
                            "build",
                        ]
                    ]

                    for file in files:
                        if file.endswith(
                            (".py", ".js", ".ts", ".yaml", ".yml", ".json", ".md")
                        ):
                            rel_path = os.path.relpath(
                                os.path.join(root, file), project_path
                            )
                            project_info["files"].append(rel_path)

                logger.info(f"  ✅ Found {len(project_info['files'])} relevant files")
            except Exception as e:
                logger.warning(f"  ⚠️  Error scanning project: {e}")

            context["projects"].append(project_info)

        # Load additional context files
        for context_file in config.get("context_files", []):
            # Try to find the file in any of the scanned projects
            for project in context["projects"]:
                file_path = os.path.join(project["path"], context_file)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        context["context_files_content"][context_file] = content
                        logger.info(
                            f"  ✅ Loaded {context_file} ({len(content)} chars)"
                        )
                        break
                    except Exception as e:
                        logger.warning(f"  ⚠️  Could not read {context_file}: {e}")

        return context if context["projects"] else None
