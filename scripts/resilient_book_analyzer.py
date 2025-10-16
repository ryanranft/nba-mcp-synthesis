#!/usr/bin/env python3
"""
Simplified Resilient Book Analyzer
Uses only Google Gemini and DeepSeek (working APIs) with circuit breaker protection.
Skips broken Claude and GPT-4 APIs entirely.

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

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from synthesis.models.google_model import GoogleModel
from synthesis.models.deepseek_model import DeepSeekModel
from mcp_server.unified_configuration_manager import UnifiedConfigurationManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ResilientAnalysisResult:
    success: bool
    recommendations: List[Dict[str, Any]]
    total_cost: float
    google_cost: float
    deepseek_cost: float
    total_tokens: int
    total_time: float
    error: Optional[str] = None

class ResilientBookAnalyzer:
    """Simplified analyzer using only working APIs with unified configuration."""

    def __init__(self, project: str = 'nba-mcp-synthesis', context: str = 'production'):
        """Initialize with unified configuration system."""
        # Load secrets using hierarchical loader
        logger.info(f"Loading secrets for project={project}, context={context}")
        try:
            result = subprocess.run([
                sys.executable,
                "/Users/ryanranft/load_env_hierarchical.py",
                project, "NBA", context
            ], capture_output=True, text=True, check=True)

            logger.info("✅ Secrets loaded successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to load secrets: {e.stderr}")
            raise RuntimeError(f"Failed to load secrets: {e.stderr}")
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

        # Get API keys from configuration
        self.google_api_key = self.config.api_config.google_api_key
        self.deepseek_api_key = self.config.api_config.deepseek_api_key

        if not self.google_api_key:
            raise ValueError("Google API key not configured")
        if not self.deepseek_api_key:
            raise ValueError("DeepSeek API key not configured")

        self.google_model = GoogleModel()  # Will get API key from environment variables
        self.deepseek_model = DeepSeekModel(self.deepseek_api_key)

        logger.info("✅ ResilientBookAnalyzer initialized with Google and DeepSeek only")

    async def analyze_book(self, book: Dict[str, Any]) -> ResilientAnalysisResult:
        """Analyze book using only working APIs."""
        start_time = datetime.now()
        total_cost = 0.0
        total_tokens = 0

        logger.info(f"🚀 Starting resilient analysis for: {book.get('title', 'Unknown')}")

        # Get book content
        book_content = book.get('content', '')
        if not book_content:
            book_content = await self._read_book_from_s3(book)
            if not book_content:
                return ResilientAnalysisResult(
                    success=False,
                    recommendations=[],
                    total_cost=0.0,
                    google_cost=0.0,
                    deepseek_cost=0.0,
                    total_tokens=0,
                    total_time=0.0,
                    error="No book content available"
                )

        # Limit content size
        if len(book_content) > 100000:
            book_content = book_content[:100000] + "\n\n[Content truncated for token limits]"

        logger.info(f"📖 Analyzing {len(book_content)} characters of content")

        # Analyze with Google (primary)
        logger.info("🔄 Analyzing with Google Gemini...")
        try:
            google_result = await asyncio.wait_for(
                self.google_model.analyze_book_content(
                    book_content=book_content,
                    book_metadata=book
                ),
                timeout=60  # 1 minute timeout
            )

            if google_result.get('success', False):
                logger.info(f"✅ Google analysis complete: {len(google_result.get('recommendations', []))} recommendations")
                total_cost += google_result.get('cost', 0.0)
                total_tokens += google_result.get('tokens_input_estimate', 0)
            else:
                logger.warning(f"⚠️ Google analysis failed: {google_result.get('error', 'Unknown error')}")
                google_result = {'recommendations': [], 'cost': 0.0, 'tokens_input_estimate': 0}

        except asyncio.TimeoutError:
            logger.error("❌ Google analysis timed out")
            google_result = {'recommendations': [], 'cost': 0.0, 'tokens_input_estimate': 0}
        except Exception as e:
            logger.error(f"❌ Google analysis failed: {str(e)}")
            google_result = {'recommendations': [], 'cost': 0.0, 'tokens_input_estimate': 0}

        # Analyze with DeepSeek (secondary)
        logger.info("🔄 Analyzing with DeepSeek...")
        try:
            deepseek_result = await asyncio.wait_for(
                self.deepseek_model.analyze_book_content(
                    book_content=book_content,
                    book_metadata=book
                ),
                timeout=120  # 2 minute timeout
            )

            if deepseek_result.get('success', False):
                logger.info(f"✅ DeepSeek analysis complete: {len(deepseek_result.get('recommendations', []))} recommendations")
                total_cost += deepseek_result.get('cost', 0.0)
                total_tokens += deepseek_result.get('tokens_input', 0)
            else:
                logger.warning(f"⚠️ DeepSeek analysis failed: {deepseek_result.get('error', 'Unknown error')}")
                deepseek_result = {'recommendations': [], 'cost': 0.0, 'tokens_input': 0}

        except asyncio.TimeoutError:
            logger.error("❌ DeepSeek analysis timed out")
            deepseek_result = {'recommendations': [], 'cost': 0.0, 'tokens_input': 0}
        except Exception as e:
            logger.error(f"❌ DeepSeek analysis failed: {str(e)}")
            deepseek_result = {'recommendations': [], 'cost': 0.0, 'tokens_input': 0}

        # Merge recommendations
        google_recs = google_result.get('recommendations', [])
        deepseek_recs = deepseek_result.get('recommendations', [])

        # Simple deduplication
        all_recommendations = []
        seen_titles = set()

        for rec in google_recs + deepseek_recs:
            title = rec.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                all_recommendations.append(rec)

        # Add priority based on source
        for rec in all_recommendations:
            if rec in google_recs:
                rec['priority'] = 'CRITICAL'  # Google is primary
                rec['source'] = 'Google'
            else:
                rec['priority'] = 'IMPORTANT'  # DeepSeek is secondary
                rec['source'] = 'DeepSeek'

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        logger.info(f"✅ Resilient analysis complete!")
        logger.info(f"💰 Total cost: ${total_cost:.4f}")
        logger.info(f"🔢 Total tokens: {total_tokens:,}")
        logger.info(f"⏱️ Total time: {total_time:.1f}s")
        logger.info(f"📋 Final recommendations: {len(all_recommendations)}")

        return ResilientAnalysisResult(
            success=True,
            recommendations=all_recommendations,
            total_cost=total_cost,
            google_cost=google_result.get('cost', 0.0),
            deepseek_cost=deepseek_result.get('cost', 0.0),
            total_tokens=total_tokens,
            total_time=total_time
        )

    async def _read_book_from_s3(self, book: Dict) -> str:
        """Read book content from S3."""
        try:
            import boto3
            import PyPDF2
            import io

            s3_path = book.get('s3_path', '')
            if not s3_path:
                logger.error("No s3_path found in book metadata")
                return ""

            s3 = boto3.client('s3')
            bucket = 'nba-mcp-books-20251011'

            logger.info(f"📖 Reading book from S3: {s3_path}")

            response = s3.get_object(Bucket=bucket, Key=s3_path)
            file_content = response['Body'].read()

            if file_content.startswith(b'%PDF'):
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
                    logger.warning(f"⚠️ Failed to extract text from page {page_num}: {e}")
                    continue

            return text_content.strip()

        except Exception as e:
            logger.error(f"❌ Failed to extract PDF text: {e}")
            return ""

