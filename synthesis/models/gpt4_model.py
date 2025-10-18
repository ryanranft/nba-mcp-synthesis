"""
GPT-4 Model Interface
Secondary synthesizer for cross-validation and consensus voting.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from openai import AsyncOpenAI
from mcp_server.env_helper import get_hierarchical_env

logger = logging.getLogger(__name__)


class GPT4Model:
    """
    GPT-4 Model Interface

    Optimized for:
    - Cross-validation of synthesized recommendations
    - Priority assessment and refinement
    - High-quality, nuanced understanding

    Pricing: ~$10/1M input tokens, $30/1M output tokens
    """

    def __init__(self):
        """Initialize GPT-4 client"""
        # Try new naming convention first, then fallback to old
        api_key = get_hierarchical_env(
            "OPENAI_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )

        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = AsyncOpenAI(api_key=api_key)
        # Try new naming convention first, then fallback to old
        self.model = (
            get_hierarchical_env("OPENAI_MODEL", "NBA_MCP_SYNTHESIS", "WORKFLOW")
            or "gpt-4-turbo-preview"
        )  # Fallback to default
        logger.info(f"Initialized GPT-4 model: {self.model}")

    async def synthesize_recommendations(
        self,
        raw_recommendations: List[Dict[str, Any]],
        book_metadata: Dict[str, Any],
        existing_recommendations: Optional[List[Dict[str, Any]]] = None,
        book_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize raw recommendations into specific, implementable recommendations for the NBA Simulator AWS project.
        This method is similar to Claude's synthesis, providing a second opinion for consensus.

        Args:
            raw_recommendations: Raw recommendations extracted by reader models.
            book_metadata: Metadata of the book being analyzed.
            existing_recommendations: List of existing recommendations for context.

        Returns:
            A dictionary containing GPT-4's synthesized recommendations and cost/token info.
        """
        start_time = datetime.now()

        prompt = self._build_synthesis_prompt(
            raw_recommendations=raw_recommendations,
            book_metadata=book_metadata,
            existing_recommendations=existing_recommendations,
            book_content=book_content,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Low temperature for precise synthesis
                max_tokens=4000,
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Calculate cost: GPT-4 Turbo pricing ~$10/1M input, $30/1M output
            input_cost = (response.usage.prompt_tokens / 1_000_000) * 10.0
            output_cost = (response.usage.completion_tokens / 1_000_000) * 30.0
            total_cost = input_cost + output_cost

            # Extract structured recommendations from GPT-4's response
            synthesized_recommendations = self._extract_recommendations_from_response(
                response.choices[0].message.content
            )

            return {
                "success": True,
                "model": "gpt4",
                "content": response.choices[0].message.content,
                "recommendations": synthesized_recommendations,
                "tokens_used": response.usage.total_tokens,
                "tokens_input": response.usage.prompt_tokens,
                "tokens_output": response.usage.completion_tokens,
                "cost": total_cost,
                "processing_time": execution_time,
                "stop_reason": response.choices[0].finish_reason,
            }

        except Exception as e:
            logger.error(f"GPT-4 synthesis failed: {e}")
            return {
                "success": False,
                "model": "gpt4",
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds(),
            }

    def _build_synthesis_prompt(
        self,
        raw_recommendations: List[Dict[str, Any]],
        book_metadata: Dict[str, Any],
        existing_recommendations: Optional[List[Dict[str, Any]]] = None,
        book_content: Optional[str] = None,
    ) -> str:
        """Build prompt for implementation synthesis"""

        title = book_metadata.get("title", "Unknown")
        author = book_metadata.get("author", "Unknown")

        # If book_content is provided, analyze it directly
        if book_content:
            prompt = f"""You are an expert technical analyst extracting recommendations from technical books for NBA analytics systems.

BOOK: {title}

Analyze this book content and extract 10-30 actionable recommendations:

{book_content[:50000]}

Return JSON array format:
[
  {{
    "title": "...",
    "description": "...",
    "priority": "CRITICAL|IMPORTANT|NICE-TO-HAVE",
    "category": "ML|Statistics|Architecture|etc"
  }}
]

Return ONLY the JSON array, no additional text."""
            return prompt

        # Original synthesis logic (synthesize from raw_recommendations)
        existing_context = ""
        if existing_recommendations:
            existing_context = f"""
EXISTING RECOMMENDATIONS CONTEXT:
{json.dumps(existing_recommendations[:5], indent=2)}

Focus on finding NEW or SIGNIFICANTLY DIFFERENT recommendations that aren't already covered.
"""

        prompt = f"""You are an expert software architect specializing in implementing technical recommendations for NBA basketball analytics systems.

BOOK: "{title}" by {author}

TASK: Synthesize the provided raw recommendations into specific, implementable recommendations for the NBA Simulator AWS project.

RAW RECOMMENDATIONS:
{json.dumps(raw_recommendations, indent=2)}

{existing_context}

SYNTHESIS REQUIREMENTS:

1. **Implementation Focus**: Transform raw ideas into:
    - Specific technical implementations
    - Concrete code/architecture patterns
    - Detailed implementation steps
    - Integration with existing NBA Simulator AWS phases

2. **NBA Project Context**: Ensure recommendations are:
    - Applicable to basketball analytics and simulation
    - Compatible with AWS infrastructure
    - Aligned with existing project phases (0-9)
    - Implementable with Python, SQL, and AWS services

3. **Quality Standards**: Only include recommendations that:
    - Provide clear technical value
    - Are specific and actionable
    - Include implementation details
    - Have reasonable time estimates
    - Address real gaps in the current system

4. **Priority Classification**:
    - **CRITICAL**: Security, stability, core functionality
    - **IMPORTANT**: Performance, scalability, user experience
    - **NICE-TO-HAVE**: Enhancements, optimizations, nice features

OUTPUT FORMAT:
Return a JSON array of synthesized recommendations:

```json
[
  {{
    "title": "Specific Implementation Title",
    "description": "Detailed description of what to implement",
    "technical_details": "Specific technical implementation details",
    "implementation_steps": [
      "Step 1: Specific implementation step",
      "Step 2: Specific implementation step",
      "Step 3: Specific implementation step"
    ],
    "expected_impact": "How this improves the NBA analytics system",
    "priority": "CRITICAL|IMPORTANT|NICE-TO-HAVE",
    "time_estimate": "X hours",
    "dependencies": ["Any prerequisite recommendations"],
    "source_chapter": "Chapter or section reference",
    "category": "ML|Statistics|Data Processing|Architecture|Monitoring|Security|Performance|Testing",
    "mapped_phase": "Phase number (1-9) where this fits",
    "aws_services": ["AWS services needed"],
    "implementation_notes": "Specific notes for NBA project integration"
  }}
]
```

IMPORTANT:
- Synthesize 5-12 high-quality, implementable recommendations
- Focus on practical solutions, not theoretical concepts
- Ensure each recommendation is specific to the NBA project
- Include AWS service integration details
- Map recommendations to appropriate project phases
- Provide clear implementation guidance

Begin synthesis now:"""
        return prompt

    def _extract_recommendations_from_response(
        self, response_text: str
    ) -> List[Dict[str, Any]]:
        """Extracts the JSON array of recommendations from the response text."""
        try:
            json_start = response_text.find("```json")
            json_end = response_text.rfind("```")

            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = response_text[json_start + len("```json") : json_end].strip()
                return json.loads(json_str)
            else:
                logger.warning("No JSON block found in GPT-4 response.")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from GPT-4 response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting JSON from response: {e}")
            return []
