"""
Google Gemini Model Integration for Book Analysis

This module provides integration with Google's Gemini API for reading and analyzing
technical books. Gemini is used for the heavy lifting due to its high token limits
and low cost, while Claude handles synthesis.
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
class GeminiResponse:
    """Response from Gemini API"""
    content: str
    tokens_used: int
    cost: float
    processing_time: float
    model_used: str

class GoogleModel:
    """Google Gemini model for book analysis"""

    def __init__(self, api_key: str = None, model_name: str = None):
        """
        Initialize Google Gemini model

        Args:
            api_key: Google API key (optional, will try to get from env vars)
            model_name: Gemini model to use (defaults to env var or gemini-2.0-flash-exp)
        """
        # Try new naming convention first, then fallback to old
        if api_key is None:
            api_key = get_hierarchical_env("GOOGLE_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW")
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
            
        self.api_key = api_key
        # Try new naming convention first, then fallback to old
        self.model_name = (model_name or 
                          get_hierarchical_env("GOOGLE_MODEL", "NBA_MCP_SYNTHESIS", "WORKFLOW") or
                          "gemini-2.0-flash-exp")  # Fallback to default
        self.model = None
        self._setup_model()

        # Cost tracking (per 1M tokens)
        self.input_cost_per_1m = 0.0035  # $0.0035 per 1M input tokens
        self.output_cost_per_1m = 0.0105  # $0.0105 per 1M output tokens

    def _setup_model(self):
        """Setup Gemini model with safety settings"""
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

            logger.info(f"✅ Google Gemini {self.model_name} initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Gemini: {str(e)}")
            raise

    async def analyze_book_content(self, book_content: str, book_metadata: Dict[str, Any]) -> GeminiResponse:
        """
        Analyze book content using Gemini

        Args:
            book_content: Full book content (can be very large)
            book_metadata: Book metadata (title, author, etc.)

        Returns:
            GeminiResponse with analysis results
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Create analysis prompt optimized for Gemini's capabilities
            prompt = self._create_book_analysis_prompt(book_content, book_metadata)

            logger.info(f"📖 Analyzing book with Gemini: {book_metadata.get('title', 'Unknown')}")
            logger.info(f"📊 Content length: {len(book_content):,} characters")

            # Generate response
            response = await self._generate_response(prompt)

            # Calculate metrics
            processing_time = asyncio.get_event_loop().time() - start_time
            tokens_used = self._estimate_tokens(prompt + response.text)
            cost = self._calculate_cost(len(prompt), len(response.text))

            # Extract recommendations from response
            recommendations = self._extract_recommendations(response.text)

            logger.info(f"✅ Gemini analysis complete")
            logger.info(f"💰 Cost: ${cost:.4f}")
            logger.info(f"🔢 Tokens: {tokens_used:,}")
            logger.info(f"⏱️ Time: {processing_time:.1f}s")
            logger.info(f"📋 Extracted {len(recommendations)} recommendations")

            return {
                "success": True,
                "cost": cost,
                "tokens_input_estimate": tokens_used,
                "tokens_output_estimate": 0,  # Gemini doesn't separate input/output
                "recommendations": recommendations,
                "content": response.text,
                "processing_time": processing_time,
                "model_used": self.model_name,
                "raw_recommendations": recommendations  # Add this for compatibility
            }

        except Exception as e:
            logger.error(f"❌ Gemini analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "cost": 0.0,
                "tokens_input_estimate": 0,
                "tokens_output_estimate": 0,
                "recommendations": []
            }

    def _create_book_analysis_prompt(self, book_content: str, book_metadata: Dict[str, Any]) -> str:
        """Create optimized prompt for Gemini book analysis"""

        title = book_metadata.get('title', 'Unknown')
        author = book_metadata.get('author', 'Unknown')

        prompt = f"""You are an expert technical analyst specializing in extracting actionable recommendations from technical books for software development projects.

BOOK: "{title}" by {author}

TASK: Analyze this technical book and extract specific, implementable recommendations for an NBA basketball analytics and simulation system built on AWS.

BOOK CONTENT:
{book_content}

ANALYSIS REQUIREMENTS:

IMPORTANT: This is a comprehensive technical textbook. Extract ALL relevant recommendations, including:
- Statistical methods and models
- Data analysis techniques
- Implementation approaches
- Best practices
- Mathematical frameworks
- Validation strategies

Aim for 20-50 recommendations minimum. Be thorough and comprehensive.

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
    "source_chapter": "Chapter or section reference",
    "category": "ML|Statistics|Data Processing|Architecture|Monitoring|Security|Performance|Testing"
  }}
]
```

IMPORTANT:
- Extract 5-15 high-quality recommendations
- Focus on practical, implementable solutions
- Ensure each recommendation is specific and actionable
- Prioritize recommendations that provide clear technical value
- Include implementation details, not just high-level concepts

Begin your analysis now:"""

        return prompt

    async def _generate_response(self, prompt: str) -> Any:
        """Generate response from Gemini model"""
        try:
            # Use asyncio to run the synchronous Gemini call with timeout
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt)
                ),
                timeout=60  # 1 minute timeout for individual API call
            )
            return response
        except asyncio.TimeoutError:
            logger.error("❌ Gemini API call timed out after 60 seconds")
            raise Exception("Gemini API timeout")
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {str(e)}")
            raise

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimation: ~4 characters per token for English text
        return len(text) // 4

    def _calculate_cost(self, input_chars: int, output_chars: int) -> float:
        """Calculate cost based on character count"""
        # Convert characters to tokens (rough estimation)
        input_tokens = input_chars // 4
        output_tokens = output_chars // 4

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_1m

        return input_cost + output_cost

    async def extract_recommendations_from_response(self, response: GeminiResponse) -> List[Dict[str, Any]]:
        """
        Extract structured recommendations from Gemini response

        Args:
            response: Gemini response containing analysis

        Returns:
            List of structured recommendations
        """
        try:
            # Parse JSON from response content
            content = response.content.strip()

            # Find JSON array in the response
            json_start = content.find('[')
            json_end = content.rfind(']') + 1

            if json_start == -1 or json_end == 0:
                logger.warning("No JSON array found in Gemini response")
                return []

            json_content = content[json_start:json_end]
            recommendations = json.loads(json_content)

            # Validate and clean recommendations
            cleaned_recommendations = []
            for rec in recommendations:
                if self._validate_recommendation(rec):
                    cleaned_recommendations.append(rec)
                else:
                    logger.warning(f"Skipping invalid recommendation: {rec.get('title', 'Unknown')}")

            logger.info(f"✅ Extracted {len(cleaned_recommendations)} valid recommendations from Gemini")
            return cleaned_recommendations

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Gemini JSON response: {str(e)}")
            logger.error(f"Response content: {response.content[:500]}...")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to extract recommendations: {str(e)}")
            return []

    def _validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate recommendation structure"""
        required_fields = ['title', 'description', 'priority', 'time_estimate']
        return all(field in rec for field in required_fields)

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible"""
        try:
            test_response = await self._generate_response("Hello, this is a test.")
            return test_response is not None
        except Exception as e:
            logger.error(f"❌ Gemini health check failed: {str(e)}")
            return False

    def _extract_recommendations(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract recommendations from Gemini response text.

        Args:
            response_text: Raw response from Gemini

        Returns:
            List of recommendation dictionaries
        """
        try:
            # Look for JSON in the response
            import json
            import re

            # Try to find JSON blocks in the response
            json_pattern = r'```json\s*(\[.*?\])\s*```'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)

            if json_matches:
                for json_str in json_matches:
                    try:
                        data = json.loads(json_str)
                        if isinstance(data, list):
                            return data
                    except json.JSONDecodeError:
                        continue

            # Try to find JSON array without code blocks
            json_pattern = r'\[.*?\]'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)

            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    if isinstance(data, list):
                        return data
                except json.JSONDecodeError:
                    continue

            # Try to find JSON object with recommendations field
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)

            if json_matches:
                for json_str in json_matches:
                    try:
                        data = json.loads(json_str)
                        if 'recommendations' in data:
                            return data['recommendations']
                    except json.JSONDecodeError:
                        continue

            # Try to find JSON object without code blocks
            json_pattern = r'\{.*?"recommendations".*?\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)

            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    if 'recommendations' in data:
                        return data['recommendations']
                except json.JSONDecodeError:
                    continue

            # Fallback: return empty list
            logger.warning("No valid JSON recommendations found in Gemini response")
            return []

        except Exception as e:
            logger.error(f"❌ Failed to extract recommendations from Gemini response: {str(e)}")
            return []
