"""
Google Gemini + Claude Synthesis Book Analyzer

This analyzer uses Google Gemini for reading books (high token limits, low cost)
and Claude for synthesizing implementation recommendations.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from synthesis.models.google_model import GoogleModel
from synthesis.models.claude_model import ClaudeModel
from scripts.cost_tracker import CostTracker

logger = logging.getLogger(__name__)

@dataclass
class SynthesisResult:
    """Result from Google + Claude synthesis"""
    recommendations: List[Dict[str, Any]]
    google_analysis: str
    claude_synthesis: str
    total_cost: float
    total_tokens: int
    total_time: float
    google_cost: float
    claude_cost: float
    processing_details: Dict[str, Any]

class GoogleClaudeBookAnalyzer:
    """Book analyzer using Google Gemini + Claude synthesis"""

    def __init__(self, google_api_key: str, claude_api_key: str):
        """
        Initialize the analyzer

        Args:
            google_api_key: Google Gemini API key
            claude_api_key: Claude API key
        """
        self.google_model = GoogleGeminiModel(google_api_key)
        self.claude_model = ClaudeModel(claude_api_key)
        self.cost_tracker = CostTracker()

        logger.info("✅ Google + Claude Book Analyzer initialized")

    async def analyze_book(self, book: Dict[str, Any], existing_recommendations: Optional[List[Dict[str, Any]]] = None) -> SynthesisResult:
        """
        Analyze a book using Google Gemini + Claude synthesis

        Args:
            book: Book metadata and content
            existing_recommendations: Existing recommendations for context-aware analysis

        Returns:
            SynthesisResult with recommendations and analysis details
        """
        start_time = asyncio.get_event_loop().time()

        try:
            logger.info(f"📖 Starting Google + Claude analysis: {book.get('title', 'Unknown')}")

            # Step 1: Google Gemini reads and analyzes the book
            logger.info("🔍 Step 1: Google Gemini reading book...")
            google_response = await self.google_model.analyze_book_content(
                book_content=book.get('content', ''),
                book_metadata=book
            )

            # Extract raw recommendations from Google
            google_recommendations = await self.google_model.extract_recommendations_from_response(google_response)

            logger.info(f"✅ Google analysis complete: {len(google_recommendations)} raw recommendations")

            # Step 2: Claude synthesizes implementation recommendations
            logger.info("🧠 Step 2: Claude synthesizing implementation recommendations...")
            claude_response = await self.claude_model.synthesize_implementation_recommendations(
                google_analysis=google_response.content,
                google_recommendations=google_recommendations,
                book_metadata=book,
                existing_recommendations=existing_recommendations
            )

            # Extract final recommendations from Claude
            final_recommendations = await self.claude_model.extract_recommendations_from_response(claude_response)

            logger.info(f"✅ Claude synthesis complete: {len(final_recommendations)} final recommendations")

            # Calculate totals
            total_time = asyncio.get_event_loop().time() - start_time
            total_cost = google_response.cost + claude_response.cost
            total_tokens = google_response.tokens_used + claude_response.tokens_used

            # Track costs
            self.cost_tracker.track_analysis(
                model="google_gemini",
                tokens=google_response.tokens_used,
                cost=google_response.cost,
                analysis_time=google_response.processing_time
            )

            self.cost_tracker.track_analysis(
                model="claude",
                tokens=claude_response.tokens_used,
                cost=claude_response.cost,
                analysis_time=claude_response.processing_time
            )

            logger.info(f"💰 Total cost: ${total_cost:.4f} (Google: ${google_response.cost:.4f}, Claude: ${claude_response.cost:.4f})")
            logger.info(f"🔢 Total tokens: {total_tokens:,}")
            logger.info(f"⏱️ Total time: {total_time:.1f}s")

            return SynthesisResult(
                recommendations=final_recommendations,
                google_analysis=google_response.content,
                claude_synthesis=claude_response.content,
                total_cost=total_cost,
                total_tokens=total_tokens,
                total_time=total_time,
                google_cost=google_response.cost,
                claude_cost=claude_response.cost,
                processing_details={
                    "google_tokens": google_response.tokens_used,
                    "claude_tokens": claude_response.tokens_used,
                    "google_time": google_response.processing_time,
                    "claude_time": claude_response.processing_time,
                    "book_title": book.get('title', 'Unknown'),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"❌ Google + Claude analysis failed: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, bool]:
        """Check health of both models"""
        google_healthy = await self.google_model.health_check()
        claude_healthy = await self.claude_model.health_check()

        return {
            "google_gemini": google_healthy,
            "claude": claude_healthy,
            "overall": google_healthy and claude_healthy
        }

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary"""
        return self.cost_tracker.get_summary()
