"""
Four-Model Book Analysis System
Orchestrates parallel reading by Google + DeepSeek, then synthesis voting by Claude + GPT-4.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from difflib import SequenceMatcher
from mcp_server.env_helper import get_hierarchical_env

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from synthesis.models.google_model import GoogleModel
from synthesis.models.deepseek_model import DeepSeekModel
from synthesis.models.claude_model import ClaudeModel
from synthesis.models.gpt4_model import GPT4Model

# Import circuit breaker
from circuit_breaker import circuit_manager

logger = logging.getLogger(__name__)


class FourModelBookAnalyzer:
    """
    Manages the four-stage book analysis process:
    1. Google Gemini & DeepSeek for comprehensive content analysis and raw recommendation extraction (in parallel).
    2. Claude & GPT-4 for synthesizing raw output into actionable, implementable recommendations (in parallel).
    3. Consensus voting between Claude and GPT-4 to determine priority.
    """

    def __init__(self):
        """Initializes the Google, DeepSeek, Claude, and GPT-4 models."""
        # Validate API keys first
        self._validate_api_keys()

        # Get API keys from environment variables (using hierarchical loading)
        google_api_key = get_hierarchical_env(
            "GOOGLE_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )
        deepseek_api_key = get_hierarchical_env(
            "DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )
        anthropic_api_key = get_hierarchical_env(
            "ANTHROPIC_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )
        openai_api_key = get_hierarchical_env(
            "OPENAI_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )

        self.google_model = GoogleModel()  # Will get API key from environment variables
        self.deepseek_model = DeepSeekModel()
        self.claude_model = ClaudeModel()
        self.gpt4_model = GPT4Model()
        logger.info(
            "FourModelBookAnalyzer initialized with Google, DeepSeek, Claude, and GPT-4 models."
        )

    def _validate_api_keys(self):
        """Validate API keys with helpful error messages"""
        errors = []

        if not get_hierarchical_env("GOOGLE_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
            errors.append("❌ GOOGLE_API_KEY not set")
        if not get_hierarchical_env(
            "DEEPSEEK_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        ):
            errors.append("❌ DEEPSEEK_API_KEY not set")
        if not get_hierarchical_env(
            "ANTHROPIC_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        ):
            errors.append("❌ ANTHROPIC_API_KEY not set")
        if not get_hierarchical_env("OPENAI_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"):
            errors.append("❌ OPENAI_API_KEY not set")

        if errors:
            print("\n".join(errors))
            print("\nPlease set API keys in .env file")
            raise ValueError("Missing required API keys")

    async def analyze_book(
        self,
        book: Dict,
        existing_recommendations: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Performs the full book analysis using Google Gemini, DeepSeek, Claude, and GPT-4.

        Args:
            book: Dictionary containing book metadata and content (e.g., 'content' key).
            existing_recommendations: List of existing recommendations for context.

        Returns:
            A structured object containing the synthesized recommendations, total cost, and other metrics.
        """
        total_start_time = datetime.now()
        total_cost = 0.0
        total_tokens = 0
        all_recommendations = []

        book_content = book.get("content", "")
        if not book_content:
            # Try to read book content from S3
            book_content = await self._read_book_from_s3(book)
            if not book_content:
                logger.error(
                    f"No content found for book: {book.get('title', 'Unknown')}"
                )
                return AnalysisResult(success=False, error="No book content available.")

        logger.info(f"Starting analysis for book: {book.get('title', 'Unknown')}")

        # --- Stage 1: Parallel reading by Google + DeepSeek ---
        logger.info(
            "Stage 1: Google Gemini and DeepSeek analyzing book content in parallel..."
        )
        # Stage 1: Parallel reading with circuit breaker protection
        logger.info(
            "Stage 1: Google Gemini and DeepSeek analyzing book content with circuit breaker protection..."
        )

        # Execute with circuit breaker protection
        google_result = await circuit_manager.execute_with_circuit_breaker(
            "google",
            self.google_model.analyze_book_content,
            book_content=book_content,
            book_metadata=book,
        )

        deepseek_result = await circuit_manager.execute_with_circuit_breaker(
            "deepseek",
            self.deepseek_model.analyze_book_content,
            book_content=book_content,
            book_metadata=book,
        )

        if not google_result["success"]:
            logger.warning(
                f"Google Gemini analysis failed: {google_result.get('error', 'Unknown error')}"
            )
        if not deepseek_result["success"]:
            logger.warning(
                f"DeepSeek analysis failed: {deepseek_result.get('error', 'Unknown error')}"
            )

        total_cost += google_result.get("cost", 0.0) + deepseek_result.get("cost", 0.0)
        total_tokens += google_result.get(
            "tokens_input_estimate", 0
        ) + google_result.get("tokens_output_estimate", 0)
        total_tokens += deepseek_result.get("tokens_input", 0) + deepseek_result.get(
            "tokens_output", 0
        )

        logger.info(
            f"Google Gemini completed. Cost: ${google_result.get('cost', 0.0):.4f}, Tokens: {google_result.get('tokens_input_estimate', 0) + google_result.get('tokens_output_estimate', 0):,}"
        )
        logger.info(
            f"DeepSeek completed. Cost: ${deepseek_result.get('cost', 0.0):.4f}, Tokens: {deepseek_result.get('tokens_input', 0) + deepseek_result.get('tokens_output', 0):,}"
        )

        # Merge raw recommendations from both readers
        raw_recommendations = self._merge_reader_recommendations(
            google_result.get("raw_recommendations", []),
            deepseek_result.get("raw_recommendations", []),
        )
        logger.info(
            f"Merged {len(raw_recommendations)} raw recommendations from readers."
        )

        if not raw_recommendations:
            logger.warning("No raw recommendations to synthesize. Skipping Stage 2.")
            total_time = (datetime.now() - total_start_time).total_seconds()
            return AnalysisResult(
                success=True,
                recommendations=[],
                total_cost=total_cost,
                google_cost=google_result.get("cost", 0.0),
                deepseek_cost=deepseek_result.get("cost", 0.0),
                claude_cost=0.0,
                gpt4_cost=0.0,
                total_tokens=total_tokens,
                total_time=total_time,
                google_analysis_summary=google_result.get("analysis_content", ""),
                deepseek_analysis_summary=deepseek_result.get("analysis_content", ""),
                google_raw_recommendations=google_result.get("raw_recommendations", []),
                deepseek_raw_recommendations=deepseek_result.get(
                    "raw_recommendations", []
                ),
            )

        # --- Stage 2: Parallel synthesis with circuit breaker protection ---
        logger.info(
            "Stage 2: Claude and GPT-4 synthesizing recommendations with circuit breaker protection..."
        )

        # Execute with circuit breaker protection
        claude_synthesis_result = await circuit_manager.execute_with_circuit_breaker(
            "claude",
            self.claude_model.synthesize_implementation_recommendations,
            google_analysis=google_result.get("analysis_content", ""),
            google_recommendations=raw_recommendations,
            book_metadata=book,
            existing_recommendations=existing_recommendations,
        )

        gpt4_synthesis_result = await circuit_manager.execute_with_circuit_breaker(
            "gpt4",
            self.gpt4_model.synthesize_recommendations,
            raw_recommendations=raw_recommendations,
            book_metadata=book,
            existing_recommendations=existing_recommendations,
        )

        if not claude_synthesis_result["success"]:
            logger.warning(
                f"Claude synthesis failed: {claude_synthesis_result.get('error', 'Unknown error')}"
            )
        if not gpt4_synthesis_result["success"]:
            logger.warning(
                f"GPT-4 synthesis failed: {gpt4_synthesis_result.get('error', 'Unknown error')}"
            )

        total_cost += claude_synthesis_result.get(
            "cost", 0.0
        ) + gpt4_synthesis_result.get("cost", 0.0)
        total_tokens += claude_synthesis_result.get(
            "tokens_used", 0
        ) + gpt4_synthesis_result.get("tokens_used", 0)

        logger.info(
            f"Claude synthesis completed. Cost: ${claude_synthesis_result.get('cost', 0.0):.4f}, Tokens: {claude_synthesis_result.get('tokens_used', 0):,}"
        )
        logger.info(
            f"GPT-4 synthesis completed. Cost: ${gpt4_synthesis_result.get('cost', 0.0):.4f}, Tokens: {gpt4_synthesis_result.get('tokens_used', 0):,}"
        )

        # Extract structured recommendations from Claude and GPT-4's responses
        claude_recs = await self.claude_model.extract_recommendations_from_response(
            claude_synthesis_result
        )
        gpt4_recs = gpt4_synthesis_result.get("recommendations", [])

        # --- Stage 3: Consensus voting ---
        final_recommendations = self._synthesizer_consensus_vote(claude_recs, gpt4_recs)

        total_time = (datetime.now() - total_start_time).total_seconds()

        logger.info(
            f"Analysis complete for {book.get('title', 'Unknown')}. Total Cost: ${total_cost:.4f}, Total Tokens: {total_tokens:,}, Time: {total_time:.1f}s"
        )
        logger.info(
            f"Found {len(final_recommendations)} implementable recommendations after consensus."
        )

        return AnalysisResult(
            success=True,
            recommendations=final_recommendations,
            total_cost=total_cost,
            google_cost=google_result.get("cost", 0.0),
            deepseek_cost=deepseek_result.get("cost", 0.0),
            claude_cost=claude_synthesis_result.get("cost", 0.0),
            gpt4_cost=gpt4_synthesis_result.get("cost", 0.0),
            total_tokens=total_tokens,
            total_time=total_time,
            google_analysis_summary=google_result.get("analysis_content", ""),
            deepseek_analysis_summary=deepseek_result.get("analysis_content", ""),
            google_raw_recommendations=google_result.get("raw_recommendations", []),
            deepseek_raw_recommendations=deepseek_result.get("raw_recommendations", []),
            claude_synthesis_content=claude_synthesis_result.get("content", ""),
            gpt4_synthesis_content=gpt4_synthesis_result.get("content", ""),
        )

    def _merge_reader_recommendations(
        self, google_recs: List[Dict], deepseek_recs: List[Dict]
    ) -> List[Dict]:
        """
        Merges raw recommendations from Google and DeepSeek, deduplicating based on similarity.
        """
        merged = []
        titles_in_merged = set()

        # Add Google's recommendations first
        for rec in google_recs:
            title = rec.get("title", "").lower()
            if title and title not in titles_in_merged:
                merged.append(rec)
                titles_in_merged.add(title)

        # Add DeepSeek's recommendations, checking for duplicates
        for rec_ds in deepseek_recs:
            title_ds = rec_ds.get("title", "").lower()
            is_duplicate = False
            for rec_m in merged:
                title_m = rec_m.get("title", "").lower()
                if (
                    self._calculate_similarity(title_ds, title_m) > 0.8
                ):  # High similarity threshold
                    is_duplicate = True
                    break
            if not is_duplicate and title_ds:
                merged.append(rec_ds)
                titles_in_merged.add(
                    title_ds
                )  # Add to set to prevent future duplicates

        return merged

    def _synthesizer_consensus_vote(
        self, claude_recs: List[Dict], gpt4_recs: List[Dict]
    ) -> List[Dict]:
        """
        Applies consensus voting to recommendations from Claude and GPT-4.
        - 2/2 agreement = Critical
        - 1/2 agreement = Important
        - 0/2 agreement = Skip
        """
        final_recs = []
        claude_titles = {
            r.get("title", "").lower(): r for r in claude_recs if r.get("title")
        }
        gpt4_titles = {
            r.get("title", "").lower(): r for r in gpt4_recs if r.get("title")
        }

        processed_titles = set()

        # Process Claude's recommendations
        for title, rec in claude_titles.items():
            if title in processed_titles:
                continue

            if title in gpt4_titles:
                # 2/2 agreement (Critical)
                merged_rec = self._merge_synthesized_recommendations(
                    rec, gpt4_titles[title]
                )
                merged_rec["priority"] = "CRITICAL"
                merged_rec["consensus_score"] = "2/2"
                final_recs.append(merged_rec)
                processed_titles.add(title)
                processed_titles.add(title)  # Mark GPT-4's as processed too
            else:
                # 1/2 agreement (Important)
                rec["priority"] = "IMPORTANT"
                rec["consensus_score"] = "1/2"
                final_recs.append(rec)
                processed_titles.add(title)

        # Process GPT-4's recommendations that weren't in Claude's
        for title, rec in gpt4_titles.items():
            if title not in processed_titles:
                # 1/2 agreement (Important)
                rec["priority"] = "IMPORTANT"
                rec["consensus_score"] = "1/2"
                final_recs.append(rec)
                processed_titles.add(title)

        return final_recs

    def _merge_synthesized_recommendations(self, rec1: Dict, rec2: Dict) -> Dict:
        """
        Merges two synthesized recommendations, prioritizing more detailed fields.
        This is a simplified merge; a more complex one might involve LLM for merging.
        """
        merged = rec1.copy()
        for key, value in rec2.items():
            if key not in merged or (
                isinstance(value, str) and len(value) > len(str(merged.get(key, "")))
            ):
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged.get(key), list):
                merged[key] = list(
                    set(merged[key] + value)
                )  # Merge lists, remove duplicates
        return merged

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        return SequenceMatcher(None, text1, text2).ratio()

    async def _read_book_from_s3(self, book: Dict) -> str:
        """
        Read book content from S3 and extract text from PDFs.

        Args:
            book: Book metadata with s3_path

        Returns:
            Extracted text content or empty string if failed
        """
        try:
            import boto3
            import PyPDF2
            import io

            s3_path = book.get("s3_path", "")
            if not s3_path:
                logger.error("No s3_path found in book metadata")
                return ""

            # Initialize S3 client
            s3 = boto3.client("s3")
            bucket = "nba-mcp-books-20251011"

            logger.info(f"📖 Reading book from S3: {s3_path}")

            # Download file from S3
            response = s3.get_object(Bucket=bucket, Key=s3_path)
            file_content = response["Body"].read()

            logger.info(f"📄 Downloaded {len(file_content)} bytes from S3")

            # Check if it's a PDF
            if file_content.startswith(b"%PDF"):
                logger.info("📚 Extracting text from PDF...")
                text_content = self._extract_pdf_text(file_content)
                logger.info(f"✅ Extracted {len(text_content)} characters from PDF")

                # Check if content is too large and chunk if needed
                if len(text_content) > 100000:  # ~25k tokens
                    logger.info(
                        "📄 Content is large, using first 100k characters for analysis"
                    )
                    text_content = (
                        text_content[:100000]
                        + "\n\n[Content truncated for token limits]"
                    )

                return text_content
            else:
                logger.warning(f"⚠️ File is not a PDF: {s3_path}")
                # Try to decode as text
                try:
                    text_content = file_content.decode("utf-8")
                    logger.info(f"📝 Decoded as text: {len(text_content)} characters")
                    return text_content
                except UnicodeDecodeError:
                    logger.error(f"❌ Cannot decode file content: {s3_path}")
                    return ""

        except Exception as e:
            logger.error(f"❌ Failed to read book from S3: {e}")
            return ""

    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF content using PyPDF2.

        Args:
            pdf_content: Raw PDF bytes

        Returns:
            Extracted text content
        """
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


class AnalysisResult:
    """Simple data class to hold analysis results."""

    def __init__(
        self,
        success: bool,
        recommendations: List[Dict] = None,
        total_cost: float = 0.0,
        google_cost: float = 0.0,
        deepseek_cost: float = 0.0,
        claude_cost: float = 0.0,
        gpt4_cost: float = 0.0,
        total_tokens: int = 0,
        total_time: float = 0.0,
        error: Optional[str] = None,
        google_analysis_summary: Optional[str] = None,
        deepseek_analysis_summary: Optional[str] = None,
        google_raw_recommendations: Optional[List[Dict]] = None,
        deepseek_raw_recommendations: Optional[List[Dict]] = None,
        claude_synthesis_content: Optional[str] = None,
        gpt4_synthesis_content: Optional[str] = None,
    ):
        self.success = success
        self.recommendations = recommendations if recommendations is not None else []
        self.total_cost = total_cost
        self.google_cost = google_cost
        self.deepseek_cost = deepseek_cost
        self.claude_cost = claude_cost
        self.gpt4_cost = gpt4_cost
        self.total_tokens = total_tokens
        self.total_time = total_time
        self.error = error
        self.google_analysis_summary = google_analysis_summary
        self.deepseek_analysis_summary = deepseek_analysis_summary
        self.google_raw_recommendations = google_raw_recommendations
        self.deepseek_raw_recommendations = deepseek_raw_recommendations
        self.claude_synthesis_content = claude_synthesis_content
        self.gpt4_synthesis_content = gpt4_synthesis_content
