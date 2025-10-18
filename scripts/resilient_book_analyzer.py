#!/usr/bin/env python3
"""
Full Multi-Model Book Analyzer with Consensus Synthesis
Uses all 4 AI models (Google Gemini, DeepSeek, Claude, OpenAI GPT-4) with consensus voting.
Synthesizes recommendations from all models for higher quality results.

Updated to use the new unified secrets and configuration management system.
"""

import os
import sys
import asyncio
import logging
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import Counter

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from synthesis.models.google_model import GoogleModel
from synthesis.models.deepseek_model import DeepSeekModel
from synthesis.models.claude_model import ClaudeModel
from synthesis.models.gpt4_model import GPT4Model
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ResilientAnalysisResult:
    success: bool
    recommendations: List[Dict[str, Any]]
    total_cost: float
    google_cost: float
    deepseek_cost: float
    claude_cost: float
    gpt4_cost: float
    total_tokens: int
    total_time: float
    models_used: List[str]
    consensus_level: str  # "unanimous", "majority", "split"
    error: Optional[str] = None


class ResilientBookAnalyzer:
    """Multi-model analyzer using all 4 AI models with consensus synthesis."""

    def __init__(self, project: str = "nba-mcp-synthesis", context: str = "production"):
        """Initialize with unified configuration system and all 4 AI models."""
        # Load secrets using hierarchical loader - directly, not via subprocess
        logger.info(f"Loading secrets for project={project}, context={context}")
        try:
            from mcp_server.unified_secrets_manager import load_secrets_hierarchical
            # Map context to the secrets context
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

        # Initialize unified configuration manager
        try:
            self.config = UnifiedConfigurationManager(project, context)
            logger.info("✅ Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise RuntimeError(f"Failed to load configuration: {e}")

        # Initialize all 4 AI models
        self.models_available = []

        # Google Gemini (primary - fast and cheap)
        try:
            self.google_model = GoogleModel()
            self.models_available.append("Google")
            logger.info("✅ Google Gemini initialized")
        except Exception as e:
            logger.warning(f"⚠️ Google Gemini unavailable: {e}")
            self.google_model = None

        # DeepSeek (fast and cheap)
        try:
            self.deepseek_api_key = self.config.api_config.deepseek_api_key
            if self.deepseek_api_key:
                self.deepseek_model = DeepSeekModel(self.deepseek_api_key)
                self.models_available.append("DeepSeek")
                logger.info("✅ DeepSeek initialized")
            else:
                self.deepseek_model = None
        except Exception as e:
            logger.warning(f"⚠️ DeepSeek unavailable: {e}")
            self.deepseek_model = None

        # Claude (high quality, more expensive)
        try:
            self.claude_model = ClaudeModel()
            self.models_available.append("Claude")
            logger.info("✅ Claude initialized")
        except Exception as e:
            logger.warning(f"⚠️ Claude unavailable: {e}")
            self.claude_model = None

        # OpenAI GPT-4 (high quality, most expensive)
        try:
            self.gpt4_model = GPT4Model()
            self.models_available.append("GPT-4")
            logger.info("✅ GPT-4 initialized")
        except Exception as e:
            logger.warning(f"⚠️ GPT-4 unavailable: {e}")
            self.gpt4_model = None

        if not self.models_available:
            raise ValueError("No AI models available! Check API keys.")

        logger.info(
            f"✅ ResilientBookAnalyzer initialized with {len(self.models_available)} models: {', '.join(self.models_available)}"
        )

    async def analyze_book(self, book: Dict[str, Any]) -> ResilientAnalysisResult:
        """Analyze book using all available AI models with consensus synthesis."""
        start_time = datetime.now()

        logger.info(
            f"🚀 Starting multi-model analysis for: {book.get('title', 'Unknown')}"
        )
        logger.info(f"🤖 Models available: {', '.join(self.models_available)}")

        # Get book content
        book_content = book.get("content", "")
        if not book_content:
            book_content = await self._read_book_from_s3(book)
            if not book_content:
                return ResilientAnalysisResult(
                    success=False,
                    recommendations=[],
                    total_cost=0.0,
                    google_cost=0.0,
                    deepseek_cost=0.0,
                    claude_cost=0.0,
                    gpt4_cost=0.0,
                    total_tokens=0,
                    total_time=0.0,
                    models_used=[],
                    consensus_level="none",
                    error="No book content available",
                )

        # Limit content size
        if len(book_content) > 100000:
            book_content = (
                book_content[:100000] + "\n\n[Content truncated for token limits]"
            )

        logger.info(f"📖 Analyzing {len(book_content)} characters of content")

        # Run all models in parallel with error handling
        model_results = {}
        models_used = []

        # Google Gemini
        if self.google_model:
            logger.info("🔄 Analyzing with Google Gemini...")
            model_results["google"] = await self._run_model_analysis(
                self.google_model, "Google", book_content, book, timeout=60
            )
            if model_results["google"]["success"]:
                models_used.append("Google")

        # DeepSeek
        if self.deepseek_model:
            logger.info("🔄 Analyzing with DeepSeek...")
            model_results["deepseek"] = await self._run_model_analysis(
                self.deepseek_model, "DeepSeek", book_content, book, timeout=120
            )
            if model_results["deepseek"]["success"]:
                models_used.append("DeepSeek")

        # Claude
        if self.claude_model:
            logger.info("🔄 Analyzing with Claude...")
            model_results["claude"] = await self._run_claude_analysis(
                book_content, book, timeout=90
            )
            if model_results["claude"]["success"]:
                models_used.append("Claude")

        # GPT-4
        if self.gpt4_model:
            logger.info("🔄 Analyzing with GPT-4...")
            model_results["gpt4"] = await self._run_gpt4_analysis(
                book_content, book, timeout=90
            )
            if model_results["gpt4"]["success"]:
                models_used.append("GPT-4")

        # Synthesize recommendations with consensus voting
        synthesized_recs, consensus_level = self._synthesize_consensus(model_results, models_used)

        # Calculate totals
        total_cost = sum(result.get("cost", 0.0) for result in model_results.values())
        total_tokens = sum(
            result.get("tokens_input_estimate", result.get("tokens_input", 0))
            for result in model_results.values()
        )

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        logger.info(f"✅ Multi-model analysis complete!")
        logger.info(f"💰 Total cost: ${total_cost:.4f}")
        logger.info(f"🔢 Total tokens: {total_tokens:,}")
        logger.info(f"⏱️ Total time: {total_time:.1f}s")
        logger.info(f"📋 Final recommendations: {len(synthesized_recs)}")
        logger.info(f"🎯 Consensus level: {consensus_level}")

        return ResilientAnalysisResult(
            success=True,
            recommendations=synthesized_recs,
            total_cost=total_cost,
            google_cost=model_results.get("google", {}).get("cost", 0.0),
            deepseek_cost=model_results.get("deepseek", {}).get("cost", 0.0),
            claude_cost=model_results.get("claude", {}).get("cost", 0.0),
            gpt4_cost=model_results.get("gpt4", {}).get("cost", 0.0),
            total_tokens=total_tokens,
            total_time=total_time,
            models_used=models_used,
            consensus_level=consensus_level,
        )

    async def _run_model_analysis(
        self, model, model_name: str, content: str, metadata: Dict, timeout: int
    ) -> Dict:
        """Run analysis for a model with error handling."""
        try:
            result = await asyncio.wait_for(
                model.analyze_book_content(
                    book_content=content, book_metadata=metadata
                ),
                timeout=timeout,
            )

            if result.get("success", False):
                logger.info(
                    f"✅ {model_name} analysis complete: {len(result.get('recommendations', []))} recommendations"
                )
                result["model_name"] = model_name
                return result
            else:
                logger.warning(
                    f"⚠️ {model_name} analysis failed: {result.get('error', 'Unknown error')}"
                )
                return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}

        except asyncio.TimeoutError:
            logger.error(f"❌ {model_name} analysis timed out")
            return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}
        except Exception as e:
            logger.error(f"❌ {model_name} analysis failed: {str(e)}")
            return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}

    async def _run_claude_analysis(self, content: str, metadata: Dict, timeout: int) -> Dict:
        """Run Claude analysis with proper interface."""
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
                    f"✅ Claude analysis complete: {len(result.get('recommendations', []))} recommendations"
                )
                return {
                    "success": True,
                    "recommendations": result.get("recommendations", []),
                    "cost": result.get("cost", 0.0),
                    "tokens_input_estimate": result.get("input_tokens", 0),
                    "model_name": "Claude"
                }
            else:
                logger.warning(f"⚠️ Claude analysis failed: {result.get('error', 'Unknown error')}")
                return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}

        except asyncio.TimeoutError:
            logger.error("❌ Claude analysis timed out")
            return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}
        except Exception as e:
            logger.error(f"❌ Claude analysis failed: {str(e)}")
            return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}

    async def _run_gpt4_analysis(self, content: str, metadata: Dict, timeout: int) -> Dict:
        """Run GPT-4 analysis with proper interface."""
        try:
            # Extract raw recommendations from other models for synthesis
            raw_recs = []  # GPT-4 will do its own analysis

            result = await asyncio.wait_for(
                self.gpt4_model.synthesize_recommendations(
                    raw_recommendations=raw_recs,
                    book_metadata=metadata,
                    book_content=content
                ),
                timeout=timeout,
            )

            if result.get("success", False):
                logger.info(
                    f"✅ GPT-4 analysis complete: {len(result.get('recommendations', []))} recommendations"
                )
                return {
                    "success": True,
                    "recommendations": result.get("recommendations", []),
                    "cost": result.get("cost", 0.0),
                    "tokens_input_estimate": result.get("input_tokens", 0),
                    "model_name": "GPT-4"
                }
            else:
                logger.warning(f"⚠️ GPT-4 analysis failed: {result.get('error', 'Unknown error')}")
                return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}

        except asyncio.TimeoutError:
            logger.error("❌ GPT-4 analysis timed out")
            return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}
        except Exception as e:
            logger.error(f"❌ GPT-4 analysis failed: {str(e)}")
            return {"success": False, "recommendations": [], "cost": 0.0, "tokens_input_estimate": 0}

    def _synthesize_consensus(
        self, model_results: Dict, models_used: List[str]
    ) -> tuple[List[Dict], str]:
        """Synthesize recommendations using consensus voting."""
        from difflib import SequenceMatcher

        # Collect all recommendations with their sources
        all_recs = []
        for model_name, result in model_results.items():
            if result.get("success", False):
                for rec in result.get("recommendations", []):
                    rec_copy = rec.copy()
                    rec_copy["_source_model"] = model_name
                    all_recs.append(rec_copy)

        if not all_recs:
            return [], "none"

        # Group similar recommendations (70% similarity threshold)
        rec_groups = []
        for rec in all_recs:
            title = rec.get("title", "")
            if not title:
                continue

            # Find similar group
            found_group = False
            for group in rec_groups:
                group_title = group[0].get("title", "")
                similarity = SequenceMatcher(None, title.lower(), group_title.lower()).ratio()
                if similarity >= 0.7:
                    group.append(rec)
                    found_group = True
                    break

            if not found_group:
                rec_groups.append([rec])

        # Synthesize each group with consensus voting
        synthesized = []
        for group in rec_groups:
            if not group:
                continue

            # Count how many models agreed on this recommendation
            sources = [rec["_source_model"] for rec in group]
            source_count = len(set(sources))

            # Use the first recommendation as base
            synth_rec = group[0].copy()
            synth_rec.pop("_source_model", None)

            # Add consensus metadata
            synth_rec["sources"] = list(set(sources))
            synth_rec["source_count"] = source_count
            synth_rec["consensus_votes"] = len(group)

            # Priority based on consensus
            if source_count >= 3:
                synth_rec["priority"] = "CRITICAL"  # 3+ models agree
            elif source_count >= 2:
                synth_rec["priority"] = "IMPORTANT"  # 2 models agree
            else:
                synth_rec["priority"] = "NICE_TO_HAVE"  # 1 model only

            synthesized.append(synth_rec)

        # Sort by consensus (most agreed upon first)
        synthesized.sort(key=lambda x: (x["source_count"], x["consensus_votes"]), reverse=True)

        # Determine overall consensus level
        if not synthesized:
            consensus_level = "none"
        elif synthesized[0]["source_count"] == len(models_used):
            consensus_level = "unanimous"
        elif synthesized[0]["source_count"] >= len(models_used) / 2:
            consensus_level = "majority"
        else:
            consensus_level = "split"

        return synthesized, consensus_level

    async def _read_book_from_s3(self, book: Dict) -> str:
        """Read book content from S3."""
        try:
            import boto3
            import PyPDF2
            import io

            s3_path = book.get("s3_path", "")
            if not s3_path:
                logger.error("No s3_path found in book metadata")
                return ""

            s3 = boto3.client("s3")
            bucket = "nba-mcp-books-20251011"

            logger.info(f"📖 Reading book from S3: {s3_path}")

            response = s3.get_object(Bucket=bucket, Key=s3_path)
            file_content = response["Body"].read()

            if file_content.startswith(b"%PDF"):
                logger.info("📚 Extracting text from PDF...")
                text_content = self._extract_pdf_text(file_content)
                logger.info(f"✅ Extracted {len(text_content)} characters from PDF")
                return text_content
            else:
                logger.warning(f"⚠️ File is not a PDF: {s3_path}")
                return ""

        except Exception as e:
            logger.error(f"❌ Failed to read book from S3: {e}")
            return ""

    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            import PyPDF2
            import io

            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_content = ""
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to extract text from page {page_num}: {e}"
                    )
                    continue

            return text_content.strip()

        except Exception as e:
            logger.error(f"❌ Failed to extract PDF text: {e}")
            return ""
