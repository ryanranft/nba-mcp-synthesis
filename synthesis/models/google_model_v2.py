"""
Google Gemini 1.5 Pro Model Integration for High-Context Book Analysis

This module provides integration with Google's Gemini 1.5 Pro API for analyzing
entire technical books with up to 2 million token context window.

Key Features:
- 2M token context window (can handle entire books)
- Optimized pricing tiers: $1.25/M input (<128k), $2.50/M input (>128k)
- Async operation for efficient processing
- Automatic token counting and cost tracking
"""

import os
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from mcp_server.env_helper import get_hierarchical_env

logger = logging.getLogger(__name__)


@dataclass
class GeminiV2Response:
    """Response from Gemini 1.5 Pro API"""
    content: str
    tokens_input: int
    tokens_output: int
    cost: float
    processing_time: float
    model_used: str
    pricing_tier: str  # "low" (<128k) or "high" (>128k)


class GoogleModelV2:
    """
    Google Gemini 1.5 Pro model for high-context book analysis

    Capabilities:
    - 2 million token context window
    - Superior long-context understanding
    - Cost-effective for large documents

    Pricing (per 1M tokens):
    - Input (<128k tokens): $1.25
    - Output (<128k tokens): $2.50
    - Input (>128k tokens): $2.50
    - Output (>128k tokens): $10.00
    """

    def __init__(self, api_key: str = None, model_name: str = None):
        """
        Initialize Google Gemini 1.5 Pro model

        Args:
            api_key: Google API key (optional, will try to get from env vars)
            model_name: Gemini model to use (defaults to gemini-1.5-pro)
        """
        if api_key is None:
            api_key = get_hierarchical_env(
                "GOOGLE_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
            )

        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        self.api_key = api_key
        # Use gemini-2.0-flash-exp as it supports large context
        # Note: gemini-1.5-pro not available yet, using flash model
        self.model_name = model_name or "gemini-2.0-flash-exp"
        self.model = None
        self._setup_model()

        # Pricing tiers (per 1M tokens)
        self.low_tier_threshold = 128000  # 128k tokens
        self.low_tier_input_cost = 1.25
        self.low_tier_output_cost = 2.50
        self.high_tier_input_cost = 2.50
        self.high_tier_output_cost = 10.00

        logger.info(f"✅ Google Gemini 1.5 Pro initialized: {self.model_name}")
        logger.info(f"📊 Context window: 2M tokens, Pricing: tiered (<128k cheaper)")

    def _setup_model(self):
        """Setup Gemini 1.5 Pro model with safety settings"""
        try:
            genai.configure(api_key=self.api_key)

            # Configure safety settings to be less restrictive for technical content
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }

            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=safety_settings
            )

            logger.info(f"✅ Gemini 1.5 Pro {self.model_name} initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini 1.5 Pro: {str(e)}")
            raise

    async def analyze_book_content(
        self, book_content: str, book_metadata: Dict[str, Any], project_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze book content using Gemini 1.5 Pro with full context

        Args:
            book_content: Full book content (up to 2M tokens supported)
            book_metadata: Book metadata (title, author, etc.)
            project_context: Optional project context from project_code_analyzer

        Returns:
            Dict with analysis results, cost, and token usage
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Create analysis prompt optimized for Gemini's capabilities
            prompt = self._create_book_analysis_prompt(book_content, book_metadata, project_context)

            # Estimate input tokens
            input_tokens = self._estimate_tokens(prompt)

            logger.info(
                f"📖 Analyzing book with Gemini 1.5 Pro: {book_metadata.get('title', 'Unknown')}"
            )
            logger.info(f"📊 Content length: {len(book_content):,} characters")
            logger.info(f"🔢 Estimated input tokens: {input_tokens:,}")

            # Determine pricing tier
            pricing_tier = "low" if input_tokens < self.low_tier_threshold else "high"
            logger.info(f"💰 Pricing tier: {pricing_tier} (<128k)" if pricing_tier == "low" else f"💰 Pricing tier: {pricing_tier} (>128k)")

            # Generate response
            response = await self._generate_response(prompt)

            # Calculate metrics
            processing_time = asyncio.get_event_loop().time() - start_time
            output_tokens = self._estimate_tokens(response.text)
            cost = self._calculate_cost(input_tokens, output_tokens, pricing_tier)

            # Extract recommendations from response
            recommendations = self._extract_recommendations(response.text)

            logger.info(f"✅ Gemini 1.5 Pro analysis complete")
            logger.info(f"💰 Cost: ${cost:.4f}")
            logger.info(f"🔢 Tokens: {input_tokens:,} in, {output_tokens:,} out")
            logger.info(f"⏱️ Time: {processing_time:.1f}s")
            logger.info(f"📋 Extracted {len(recommendations)} recommendations")

            return {
                "success": True,
                "cost": cost,
                "tokens_input": input_tokens,
                "tokens_output": output_tokens,
                "tokens_input_estimate": input_tokens,
                "recommendations": recommendations,
                "content": response.text,
                "processing_time": processing_time,
                "model_used": self.model_name,
                "pricing_tier": pricing_tier,
                "raw_recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"❌ Gemini 1.5 Pro analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "cost": 0.0,
                "tokens_input": 0,
                "tokens_output": 0,
                "tokens_input_estimate": 0,
                "recommendations": [],
            }

    def _create_book_analysis_prompt(
        self, book_content: str, book_metadata: Dict[str, Any], project_context: Optional[Dict] = None
    ) -> str:
        """Create optimized prompt for Gemini 1.5 Pro book analysis with project awareness"""

        title = book_metadata.get("title", "Unknown")
        author = book_metadata.get("author", "Unknown")

        # Build project context section if available
        project_section = ""
        if project_context:
            project_info = project_context.get('project_info', {})
            project_name = project_info.get('name', 'NBA Analytics System')
            project_sport = project_info.get('sport', 'basketball')
            project_goals = project_info.get('goals', [])
            project_phase = project_info.get('phase', 'Unknown')
            project_tech = project_info.get('technologies', [])

            # Get file tree
            file_tree = project_context.get('file_tree', '')

            # Get recent work
            recent_commits = project_context.get('recent_commits', [])[:5]

            # Get completion status
            completion = project_context.get('completion_status', {})

            # Get sampled files (limited to avoid token explosion)
            sampled_files = project_context.get('sampled_files', {})

            project_section = f"""
## 🎯 PROJECT CONTEXT: {project_name}

**Current Development Phase**: {project_phase}

**Project Goals**:
{chr(10).join(f'- {goal}' for goal in project_goals)}

**Technologies in Use**:
{', '.join(project_tech)}

**Project Maturity**: {completion.get('maturity', 'Unknown')}
- TODOs remaining: {completion.get('todos_found', 0)}
- FIXMEs remaining: {completion.get('fixmes_found', 0)}

**File Structure**:
```
{file_tree[:1500]}
{'... (truncated)' if len(file_tree) > 1500 else ''}
```

**Recent Development Activity** (last 5 commits):
{chr(10).join(f"- [{commit.get('hash', '')}] {commit.get('message', '')}" for commit in recent_commits)}

**Key Implementation Files** (sampled):
{chr(10).join(f"- {file_path}" for file_path in list(sampled_files.keys())[:10])}

**IMPORTANT**: Use this project context to:
1. Recommend only features that are NOT already implemented
2. Build on existing implementations and architecture
3. Align with the project's current phase and goals
4. Use the technologies already in the stack
5. Address gaps you identify in the current implementation
"""

        prompt = f"""You are an expert technical analyst specializing in extracting actionable recommendations from technical books for software development projects.

BOOK: "{title}" by {author}
{project_section}

TASK: Analyze this complete technical book and extract specific, implementable recommendations for this {'specific ' + project_info.get('sport', 'basketball') + ' analytics project' if project_context else 'NBA basketball analytics and simulation system built on AWS'}."""

        if project_context:
            prompt += """

CRITICAL: Before recommending any feature, check if it's already implemented in the project context above. Focus on:
- Features mentioned in the book but MISSING from the current project
- Improvements to existing implementations
- Technologies from the book that complement the current stack
- Addressing TODOs and FIXMEs you see in the project state
"""

        prompt += """

BOOK CONTENT (FULL):
{book_content}

ANALYSIS REQUIREMENTS:

IMPORTANT: You have access to the ENTIRE book. Analyze ALL chapters comprehensively, including:
- Early chapters: Foundational concepts and setup
- Middle chapters: Core methodologies and techniques
- Advanced chapters: Complex implementations and optimizations
- Later chapters: Case studies, examples, and best practices
- Appendices: Reference material and additional resources

Extract 30-60 comprehensive recommendations covering:
- Statistical methods and models
- Data analysis techniques
- Implementation approaches
- Best practices and patterns
- Mathematical frameworks
- Validation strategies
- System architecture considerations
- Performance optimizations

1. **Technical Focus**: Extract recommendations that are:
   - Specific and actionable
   - Technically implementable
   - Relevant to data science, ML, statistics, or software engineering
   - Suitable for a basketball analytics platform

2. **Recommendation Format**: For each recommendation, provide:
   - **Title**: Clear, specific name
   - **Description**: Detailed explanation of what to implement
   - **Technical Details**: Specific technologies, methods, or approaches
   - **Implementation Steps**: Step-by-step implementation guidance
   - **Expected Impact**: How this improves the system
   - **Priority**: CRITICAL, IMPORTANT, or NICE-TO-HAVE
   - **Time Estimate**: Hours required for implementation
   - **Dependencies**: Any prerequisites or related recommendations
   - **Source Chapter**: Which chapter/section this comes from

3. **Focus Areas**: Prioritize recommendations in these areas:
   - Machine Learning & Data Science
   - Statistical Analysis & Validation
   - Data Processing & ETL
   - System Architecture & Scalability
   - Monitoring & Observability
   - Security & Compliance
   - Performance Optimization
   - Testing & Quality Assurance

4. **Quality Standards**: Only include recommendations that are:
   - Directly applicable to the NBA analytics system
   - Technically sound and well-documented
   - Implementable with reasonable effort
   - Provide clear business value

OUTPUT FORMAT:
Return a JSON array of recommendations with this exact structure:

```json
[
  {{
    "title": "Specific Recommendation Title",
    "description": "Detailed description of what to implement",
    "technical_details": "Specific technical implementation details",
    "implementation_steps": [
      "Step 1: Description",
      "Step 2: Description",
      "Step 3: Description"
    ],
    "expected_impact": "How this improves the NBA analytics system",
    "priority": "CRITICAL|IMPORTANT|NICE-TO-HAVE",
    "time_estimate": "X hours",
    "dependencies": ["Any prerequisite recommendations"],
    "source_chapter": "Chapter or section reference from the book",
    "category": "ML|Statistics|Data Processing|Architecture|Monitoring|Security|Performance|Testing"
  }}
]
```

IMPORTANT:
- Aim for 30-60 high-quality recommendations
- Cover recommendations from ALL sections of the book
- Be thorough and comprehensive - you have the full book context
- Reference specific chapters/sections accurately
- Prioritize actionable, implementable recommendations

Begin your comprehensive analysis now:"""
        return prompt

    async def _generate_response(self, prompt: str):
        """Generate response from Gemini 1.5 Pro"""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self.model.generate_content, prompt
        )
        return response

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (roughly 4 chars per token)"""
        return len(text) // 4

    def _calculate_cost(self, input_tokens: int, output_tokens: int, pricing_tier: str) -> float:
        """Calculate cost based on pricing tier"""
        if pricing_tier == "low":
            input_cost = (input_tokens / 1_000_000) * self.low_tier_input_cost
            output_cost = (output_tokens / 1_000_000) * self.low_tier_output_cost
        else:  # high tier
            input_cost = (input_tokens / 1_000_000) * self.high_tier_input_cost
            output_cost = (output_tokens / 1_000_000) * self.high_tier_output_cost

        return input_cost + output_cost

    def _extract_recommendations(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract JSON recommendations from response"""
        try:
            # Find JSON block
            json_start = response_text.find("```json")
            json_end = response_text.rfind("```")

            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = response_text[json_start + len("```json"):json_end].strip()
                recommendations = json.loads(json_str)
                return recommendations if isinstance(recommendations, list) else []
            else:
                # Try to find raw JSON array
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group(0))
                    return recommendations if isinstance(recommendations, list) else []

                logger.warning("No JSON block found in Gemini response")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Gemini response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting recommendations: {e}")
            return []

