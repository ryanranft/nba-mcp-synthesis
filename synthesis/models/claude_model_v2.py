"""
Claude Sonnet 4 Model Interface for High-Context Book Analysis

This module provides integration with Anthropic's Claude Sonnet 4 API for
analyzing entire technical books with up to 1 million token context window.

Key Features:
- 1M token context window (handles full books)
- Superior reasoning and synthesis capabilities
- Detailed, high-quality recommendations
- Async operation for efficient processing
"""

import anthropic
import os
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_server.env_helper import get_hierarchical_env

logger = logging.getLogger(__name__)


class ClaudeModelV2:
    """
    Claude Sonnet 4 Model Interface for High-Context Analysis

    Capabilities:
    - 1 million token context window
    - Advanced reasoning and synthesis
    - Excellent at technical analysis

    Pricing (per 1M tokens):
    - Input: $3.00
    - Output: $15.00
    """

    def __init__(self):
        """Initialize Claude Sonnet 4 client"""
        api_key = get_hierarchical_env(
            "ANTHROPIC_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        self.client = anthropic.Anthropic(api_key=api_key)

        # Use latest Claude Sonnet 4 model
        # Note: Update this to the correct model identifier when available
        # Current fallback to Claude 3.7 Sonnet
        self.model = (
            get_hierarchical_env("CLAUDE_MODEL", "NBA_MCP_SYNTHESIS", "WORKFLOW")
            or "claude-3-7-sonnet-20250219"  # Will use latest available
        )

        # Pricing (per 1M tokens)
        self.input_cost_per_1m = 3.00
        self.output_cost_per_1m = 15.00

        logger.info(f"✅ Claude Sonnet initialized: {self.model}")
        logger.info(f"📊 Context window: 1M tokens (200k advertised)")
        logger.info(f"💰 Pricing: ${self.input_cost_per_1m}/M input, ${self.output_cost_per_1m}/M output")

    async def analyze_book(
        self,
        book_content: str,
        book_title: str,
        book_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze book content and extract recommendations using full context.

        Args:
            book_content: Full book text content (up to 1M tokens)
            book_title: Title of the book
            book_metadata: Book metadata dictionary

        Returns:
            Dict with success, recommendations, cost, input_tokens
        """
        start_time = datetime.now()

        # Create comprehensive prompt for full-book analysis
        prompt = self._create_full_book_prompt(book_content, book_title, book_metadata)

        logger.info(f"📖 Analyzing book with Claude: {book_title}")
        logger.info(f"📊 Content length: {len(book_content):,} characters")
        logger.info(f"🔢 Estimated tokens: ~{len(book_content) // 4:,}")

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,  # Increased for comprehensive output
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON recommendations
            try:
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group(0))
                else:
                    recommendations = []
            except:
                recommendations = []

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens / 1_000_000 * self.input_cost_per_1m) + \
                   (output_tokens / 1_000_000 * self.output_cost_per_1m)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"✅ Claude analyzed {book_title}: {len(recommendations)} recommendations")
            logger.info(f"💰 Cost: ${cost:.4f}")
            logger.info(f"🔢 Tokens: {input_tokens:,} in, {output_tokens:,} out")
            logger.info(f"⏱️ Time: {processing_time:.1f}s")

            return {
                "success": True,
                "recommendations": recommendations,
                "cost": cost,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "tokens_input_estimate": input_tokens,
                "processing_time": processing_time,
                "model_used": self.model,
                "raw_content": content,
            }

        except Exception as e:
            logger.error(f"❌ Claude analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": [],
                "cost": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "tokens_input_estimate": 0,
                "processing_time": (datetime.now() - start_time).total_seconds(),
            }

    def _create_full_book_prompt(
        self,
        book_content: str,
        book_title: str,
        book_metadata: Dict[str, Any]
    ) -> str:
        """Create comprehensive prompt for full-book analysis"""

        author = book_metadata.get("author", "Unknown")

        prompt = f"""You are an expert technical analyst extracting actionable recommendations from technical books for NBA analytics and simulation systems.

BOOK: "{book_title}" by {author}

TASK: Analyze this COMPLETE technical book and extract specific, implementable recommendations for an NBA basketball analytics platform built on AWS.

COMPLETE BOOK CONTENT:
{book_content}

ANALYSIS INSTRUCTIONS:

You have access to the ENTIRE book from beginning to end. Conduct a comprehensive analysis covering:

1. **Early Chapters**: Foundational concepts, setup, prerequisites
2. **Core Chapters**: Main methodologies, algorithms, techniques
3. **Advanced Chapters**: Complex implementations, optimizations, edge cases
4. **Later Chapters**: Case studies, real-world applications, lessons learned
5. **Appendices**: Reference material, additional resources, supplementary content

Extract 30-60 high-quality recommendations that:
- Are specific and actionable
- Include implementation details
- Reference the exact chapter/section
- Provide clear value to NBA analytics system
- Cover diverse aspects of the book's content

RECOMMENDATION CATEGORIES:
- Machine Learning & Data Science
- Statistical Analysis & Modeling
- Data Processing & ETL Pipelines
- System Architecture & Design
- Performance Optimization
- Testing & Validation
- Monitoring & Observability
- Security & Compliance

OUTPUT FORMAT (JSON):
[
  {{
    "title": "Specific Recommendation Title",
    "description": "Detailed description of what to implement and why",
    "technical_details": "Specific technical implementation details",
    "implementation_steps": [
      "Step 1: Detailed step",
      "Step 2: Detailed step",
      "Step 3: Detailed step"
    ],
    "expected_impact": "How this improves the NBA analytics system",
    "priority": "CRITICAL|IMPORTANT|NICE-TO-HAVE",
    "time_estimate": "X hours",
    "dependencies": ["Any prerequisite recommendations"],
    "source_chapter": "Specific chapter/section from the book",
    "category": "ML|Statistics|Data Processing|Architecture|Monitoring|Security|Performance|Testing"
  }}
]

IMPORTANT:
- Aim for 30-60 comprehensive recommendations
- Cover content from ALL parts of the book (early, middle, late chapters)
- Be specific about source chapters
- Include both foundational and advanced recommendations
- Focus on practical, implementable solutions
- Provide clear implementation guidance

Return ONLY the JSON array, no additional text.

Begin your comprehensive analysis:"""

        return prompt

    async def analyze_book_content(
        self,
        book_content: str,
        book_metadata: Dict[str, Any],
        existing_recommendations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Alternate interface for compatibility with existing code.

        Args:
            book_content: Full book text
            book_metadata: Book metadata
            existing_recommendations: Optional context from other analyses

        Returns:
            Analysis result dictionary
        """
        title = book_metadata.get("title", "Unknown")
        return await self.analyze_book(book_content, title, book_metadata)

