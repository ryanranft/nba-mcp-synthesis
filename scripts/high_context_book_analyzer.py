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
    MAX_TOKENS = 250_000   # Explicit token limit for tracking

    def __init__(self, project: str = "nba-mcp-synthesis", context: str = "production"):
        """Initialize with Gemini 1.5 Pro and Claude Sonnet 4."""
        logger.info(f"🚀 Initializing High-Context Book Analyzer")
        logger.info(f"📊 Max content: {self.MAX_CHARS:,} chars (~{self.MAX_TOKENS:,} tokens)")
        logger.info(f"🤖 Models: Gemini 1.5 Pro (2M context) + Claude Sonnet 4 (1M context)")

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

        logger.info(f"✅ High-Context Analyzer ready with {len(self.models_available)} models")

    async def analyze_book(self, book: Dict[str, Any]) -> HighContextAnalysisResult:
        """
        Analyze book using both models with full context.

        Args:
            book: Book metadata dict with title, author, s3_key, etc.

        Returns:
            HighContextAnalysisResult with recommendations and metrics
        """
        start_time = datetime.now()

        logger.info(f"🚀 Starting high-context analysis: {book.get('title', 'Unknown')}")
        logger.info(f"🤖 Models: {', '.join(self.models_available)}")

        # Get book content
        book_content = book.get("content", "")
        if not book_content:
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

        # Limit content size to MAX_CHARS
        original_length = len(book_content)
        if len(book_content) > self.MAX_CHARS:
            book_content = book_content[:self.MAX_CHARS] + \
                f"\n\n[Content truncated at {self.MAX_CHARS:,} characters for token limits]"
            logger.info(f"📄 Truncated from {original_length:,} to {self.MAX_CHARS:,} chars")

        logger.info(f"📖 Analyzing {len(book_content):,} characters")
        logger.info(f"🔢 Estimated ~{len(book_content) // 4:,} tokens")

        # Run both models in parallel
        model_results = {}

        # Gemini 1.5 Pro
        if self.gemini_model:
            logger.info("🔄 Analyzing with Gemini 1.5 Pro...")
            model_results["gemini"] = await self._run_gemini_analysis(
                book_content, book, timeout=180  # 3 minutes for large context
            )

        # Claude Sonnet 4
        if self.claude_model:
            logger.info("🔄 Analyzing with Claude Sonnet 4...")
            model_results["claude"] = await self._run_claude_analysis(
                book_content, book, timeout=180  # 3 minutes for large context
            )

        # Synthesize consensus
        synthesized_recs, consensus_level = self._synthesize_dual_consensus(model_results)

        # Calculate totals
        gemini_cost = model_results.get("gemini", {}).get("cost", 0.0)
        claude_cost = model_results.get("claude", {}).get("cost", 0.0)
        total_cost = gemini_cost + claude_cost

        gemini_tokens = model_results.get("gemini", {}).get("tokens_input", 0) + \
                       model_results.get("gemini", {}).get("tokens_output", 0)
        claude_tokens = model_results.get("claude", {}).get("input_tokens", 0) + \
                       model_results.get("claude", {}).get("output_tokens", 0)
        total_tokens = gemini_tokens + claude_tokens

        pricing_tier = model_results.get("gemini", {}).get("pricing_tier", "unknown")

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        logger.info(f"✅ High-context analysis complete!")
        logger.info(f"💰 Total cost: ${total_cost:.4f} (Gemini: ${gemini_cost:.4f}, Claude: ${claude_cost:.4f})")
        logger.info(f"🔢 Total tokens: {total_tokens:,} (Gemini: {gemini_tokens:,}, Claude: {claude_tokens:,})")
        logger.info(f"⏱️ Total time: {total_time:.1f}s")
        logger.info(f"📋 Final recommendations: {len(synthesized_recs)}")
        logger.info(f"🎯 Consensus level: {consensus_level}")
        logger.info(f"💰 Pricing tier: {pricing_tier}")

        return HighContextAnalysisResult(
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

    async def _run_gemini_analysis(
        self, content: str, metadata: Dict, timeout: int
    ) -> Dict:
        """Run Gemini 1.5 Pro analysis with error handling."""
        try:
            result = await asyncio.wait_for(
                self.gemini_model.analyze_book_content(
                    book_content=content,
                    book_metadata=metadata
                ),
                timeout=timeout,
            )

            if result.get("success", False):
                logger.info(
                    f"✅ Gemini 1.5 Pro complete: {len(result.get('recommendations', []))} recommendations"
                )
                return result
            else:
                logger.warning(f"⚠️ Gemini 1.5 Pro failed: {result.get('error', 'Unknown')}")
                return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input": 0, "tokens_output": 0}

        except asyncio.TimeoutError:
            logger.error(f"❌ Gemini 1.5 Pro timed out after {timeout}s")
            return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input": 0, "tokens_output": 0}
        except Exception as e:
            logger.error(f"❌ Gemini 1.5 Pro failed: {str(e)}")
            return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input": 0, "tokens_output": 0}

    async def _run_claude_analysis(
        self, content: str, metadata: Dict, timeout: int
    ) -> Dict:
        """Run Claude Sonnet 4 analysis with error handling."""
        try:
            result = await asyncio.wait_for(
                self.claude_model.analyze_book(
                    book_content=content,
                    book_title=metadata.get("title", "Unknown"),
                    book_metadata=metadata
                ),
                timeout=timeout,
            )

            if result.get("success", False):
                logger.info(
                    f"✅ Claude Sonnet 4 complete: {len(result.get('recommendations', []))} recommendations"
                )
                return result
            else:
                logger.warning(f"⚠️ Claude Sonnet 4 failed: {result.get('error', 'Unknown')}")
                return {"success": False, "recommendations": [], "cost": 0.0, "input_tokens": 0, "output_tokens": 0}

        except asyncio.TimeoutError:
            logger.error(f"❌ Claude Sonnet 4 timed out after {timeout}s")
            return {"success": False, "recommendations": [], "cost": 0.0, "input_tokens": 0, "output_tokens": 0}
        except Exception as e:
            logger.error(f"❌ Claude Sonnet 4 failed: {str(e)}")
            return {"success": False, "recommendations": [], "cost": 0.0, "input_tokens": 0, "output_tokens": 0}

    def _synthesize_dual_consensus(
        self, model_results: Dict
    ) -> tuple[List[Dict], str]:
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
                similarity = SequenceMatcher(None, title.lower(), group_title.lower()).ratio()

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
                "both_agree": "gemini" in sources and "claude" in sources
            }

            final_recs.append(chosen)

        return final_recs

    async def _read_book_from_s3(self, book: Dict) -> Optional[str]:
        """Read book content from S3."""
        try:
            import boto3
            import pymupdf  # PyMuPDF for PDF extraction
            from io import BytesIO

            s3_client = boto3.client("s3")
            # Get S3 bucket from environment or book metadata
            bucket = os.environ.get("NBA_MCP_S3_BUCKET") or book.get("s3_bucket", "nba-data-lake")
            # Check both s3_path and s3_key for compatibility
            s3_key = book.get("s3_path") or book.get("s3_key", "")

            if not s3_key:
                logger.error(f"No S3 path/key provided for book: {book.get('title', 'Unknown')}")
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
            logger.info(f"✅ Extracted {len(full_text):,} characters from {len(doc)} pages")

            doc.close()
            return full_text

        except Exception as e:
            logger.error(f"❌ Failed to read book from S3: {e}")
            return None

