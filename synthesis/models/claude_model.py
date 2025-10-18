"""
Claude Model Interface
Secondary model for synthesis, explanation, and verification
"""

import anthropic
import os
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_server.env_helper import get_hierarchical_env

logger = logging.getLogger(__name__)


class ClaudeModel:
    """
    Claude 3.5 Sonnet Model Interface

    Optimized for:
    - Synthesizing multi-model results
    - Explaining complex solutions clearly
    - Verifying mathematical reasoning
    - Generating implementation documentation

    Used sparingly to minimize cost (more expensive than DeepSeek)
    """

    def __init__(self):
        """Initialize Claude client"""
        # Try new naming convention first, then fallback to old
        api_key = get_hierarchical_env(
            "ANTHROPIC_API_KEY", "NBA_MCP_SYNTHESIS", "WORKFLOW"
        )

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        self.client = anthropic.Anthropic(api_key=api_key)
        # Try new naming convention first, then fallback to old
        self.model = (
            get_hierarchical_env("CLAUDE_MODEL", "NBA_MCP_SYNTHESIS", "WORKFLOW")
            or "claude-3-7-sonnet-20250219"
        )  # Fallback to default
        logger.info(f"Initialized Claude model: {self.model}")

    async def analyze_book(
        self,
        book_content: str,
        book_title: str,
        book_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze book content and extract recommendations.

        Args:
            book_content: Full book text content
            book_title: Title of the book
            book_metadata: Book metadata dictionary

        Returns:
            Dict with success, recommendations, cost, input_tokens
        """
        start_time = datetime.now()

        prompt = f"""You are an expert technical analyst extracting actionable recommendations from technical books for NBA analytics and simulation systems.

BOOK: "{book_title}"

TASK: Analyze this book and extract specific, implementable recommendations for an NBA basketball analytics platform built on AWS.

BOOK CONTENT:
{book_content[:50000]}

Extract 10-30 recommendations in JSON format:
[
  {{
    "title": "Recommendation title",
    "description": "What to implement",
    "technical_details": "Implementation specifics",
    "implementation_steps": ["Step 1", "Step 2"],
    "priority": "CRITICAL|IMPORTANT|NICE-TO-HAVE",
    "category": "ML|Statistics|Architecture|etc"
  }}
]

Return ONLY the JSON array, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
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

            # Calculate cost (Claude pricing)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"✅ Claude analyzed {book_title}: {len(recommendations)} recommendations")

            return {
                "success": True,
                "recommendations": recommendations,
                "cost": cost,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"❌ Claude analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": [],
                "cost": 0.0,
                "input_tokens": 0
            }

    async def synthesize(
        self,
        deepseek_result: str,
        original_request: str,
        context_summary: str,
        include_verification: bool = True,
    ) -> Dict[str, Any]:
        """
        Synthesize and explain DeepSeek's solution

        Args:
            deepseek_result: The solution from DeepSeek
            original_request: User's original request
            context_summary: Summary of MCP context used
            include_verification: Whether to verify the mathematical reasoning

        Returns:
            Synthesized result with explanation and verification
        """
        start_time = datetime.now()

        prompt = self._build_synthesis_prompt(
            deepseek_result=deepseek_result,
            original_request=original_request,
            context_summary=context_summary,
            include_verification=include_verification,
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.5,  # Moderate temperature for clear explanations
                messages=[{"role": "user", "content": prompt}],
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Calculate cost (Claude pricing: ~$3/1M input, $15/1M output)
            input_cost = (response.usage.input_tokens / 1_000_000) * 3.0
            output_cost = (response.usage.output_tokens / 1_000_000) * 15.0
            total_cost = input_cost + output_cost

            return {
                "success": True,
                "model": "claude",
                "response": response.content[0].text,
                "tokens_used": response.usage.input_tokens
                + response.usage.output_tokens,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "cost": total_cost,
                "execution_time": execution_time,
                "stop_reason": response.stop_reason,
            }

        except Exception as e:
            logger.error(f"Claude synthesis failed: {e}")
            return {
                "success": False,
                "model": "claude",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    async def verify_solution(
        self, solution: str, problem: str, expected_properties: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Verify a solution's correctness

        Args:
            solution: The solution to verify
            problem: The original problem
            expected_properties: Expected properties of the solution

        Returns:
            Verification result
        """
        expected_props = (
            f"Expected Properties:\n{expected_properties}"
            if expected_properties
            else ""
        )
        prompt = f"""Verify this solution:

Problem:
{problem}

Solution:
{solution}

{expected_props}

Please verify:
1. Mathematical accuracy
2. Logical correctness
3. Edge cases handled
4. Performance implications
5. Any potential issues

Provide a clear verification report."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,  # Low temperature for precision
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "success": True,
                "model": "claude",
                "verification": response.content[0].text,
                "tokens_used": response.usage.input_tokens
                + response.usage.output_tokens,
            }

        except Exception as e:
            logger.error(f"Claude verification failed: {e}")
            return {"success": False, "model": "claude", "error": str(e)}

    async def explain_code(
        self,
        code: str,
        context: Optional[str] = None,
        target_audience: str = "developers",
    ) -> Dict[str, Any]:
        """
        Generate clear explanation of code

        Args:
            code: The code to explain
            context: Additional context about the code
            target_audience: "developers", "analysts", or "non-technical"

        Returns:
            Clear explanation tailored to audience
        """
        audience_prompts = {
            "developers": "technical implementation details and best practices",
            "analysts": "business logic and data transformations",
            "non-technical": "plain language explanation without technical jargon",
        }

        context_str = f"Context: {context}" if context else ""
        prompt = f"""Explain this code clearly for {target_audience}:

{code}

{context_str}

Focus on {audience_prompts.get(target_audience, 'clear understanding')}.

Provide:
1. Overview (what it does)
2. Step-by-step explanation
3. Key concepts
4. Usage examples"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "success": True,
                "model": "claude",
                "explanation": response.content[0].text,
                "tokens_used": response.usage.input_tokens
                + response.usage.output_tokens,
            }

        except Exception as e:
            logger.error(f"Claude explanation failed: {e}")
            return {"success": False, "model": "claude", "error": str(e)}

    async def generate_documentation(
        self, code: str, solution_description: str, context_used: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive documentation

        Args:
            code: The implemented code
            solution_description: Description of the solution
            context_used: MCP context that was used

        Returns:
            Markdown documentation
        """
        prompt = f"""Generate comprehensive documentation for this implementation:

Solution:
{solution_description}

Code:
{code}

Context Used:
{self._format_context(context_used)}

Generate markdown documentation including:
1. Overview
2. Requirements
3. Implementation details
4. Usage examples
5. Configuration
6. Testing recommendations
7. Performance considerations"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "success": True,
                "model": "claude",
                "documentation": response.content[0].text,
                "tokens_used": response.usage.input_tokens
                + response.usage.output_tokens,
            }

        except Exception as e:
            logger.error(f"Claude documentation generation failed: {e}")
            return {"success": False, "model": "claude", "error": str(e)}

    def _build_synthesis_prompt(
        self,
        deepseek_result: str,
        original_request: str,
        context_summary: str,
        include_verification: bool,
    ) -> str:
        """Build prompt for synthesis"""
        prompt_parts = [
            "Analyze and enhance this solution from DeepSeek V3:\n",
            f"Original Request:\n{original_request}\n",
            f"DeepSeek Solution:\n{deepseek_result}\n",
            f"Context Used:\n{context_summary}\n",
            "Please provide:\n",
            (
                "1. Verification of the solution's correctness\n"
                if include_verification
                else ""
            ),
            "2. Clear explanation for implementation\n",
            "3. Any missing considerations or edge cases\n",
            "4. Specific implementation steps\n",
            "5. Testing recommendations\n",
            "\nFormat your response as:\n",
            "## Verification\n",
            "[Verify the solution]\n\n",
            "## Explanation\n",
            "[Clear explanation]\n\n",
            "## Implementation Steps\n",
            "[Step-by-step guide]\n\n",
            "## Additional Considerations\n",
            "[Edge cases, performance, etc.]\n",
        ]

        return "".join(p for p in prompt_parts if p)

    async def synthesize_implementation_recommendations(
        self,
        google_analysis: str,
        google_recommendations: List[Dict[str, Any]],
        book_metadata: Dict[str, Any],
        existing_recommendations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize Google's book analysis into implementation recommendations

        Args:
            google_analysis: Google's analysis of the book
            google_recommendations: Raw recommendations from Google
            book_metadata: Book metadata
            existing_recommendations: Existing recommendations for context

        Returns:
            Claude response with synthesized recommendations
        """
        start_time = datetime.now()

        prompt = self._build_implementation_synthesis_prompt(
            google_analysis=google_analysis,
            google_recommendations=google_recommendations,
            book_metadata=book_metadata,
            existing_recommendations=existing_recommendations,
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,  # Low temperature for precise synthesis
                messages=[{"role": "user", "content": prompt}],
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Calculate cost
            input_cost = (response.usage.input_tokens / 1_000_000) * 3.0
            output_cost = (response.usage.output_tokens / 1_000_000) * 15.0
            total_cost = input_cost + output_cost

            return {
                "success": True,
                "model": "claude",
                "content": response.content[0].text,
                "tokens_used": response.usage.input_tokens
                + response.usage.output_tokens,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "cost": total_cost,
                "processing_time": execution_time,
                "stop_reason": response.stop_reason,
            }

        except Exception as e:
            logger.error(f"Claude implementation synthesis failed: {e}")
            return {
                "success": False,
                "model": "claude",
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds(),
            }

    async def extract_recommendations_from_response(
        self, response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract structured recommendations from Claude response with robust parsing"""
        if not response.get("success"):
            return []

        try:
            content = response["content"]

            # Try direct JSON parse first
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "recommendations" in data:
                    return data["recommendations"]
                elif isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

            # Try to find JSON blocks
            import re

            json_pattern = r"```json\s*(\{.*?\})\s*```"
            matches = re.findall(json_pattern, content, re.DOTALL)

            for match in matches:
                try:
                    data = json.loads(match)
                    if "recommendations" in data:
                        return data["recommendations"]
                except json.JSONDecodeError:
                    continue

            # Try to find JSON array directly
            json_pattern = r"```json\s*(\[.*?\])\s*```"
            matches = re.findall(json_pattern, content, re.DOTALL)

            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

            # Try to find JSON array in content with better error handling
            json_start = content.find("[")
            json_end = content.rfind("]") + 1

            if json_start != -1 and json_end > json_start:
                json_content = content[json_start:json_end]

                # Try to repair common JSON issues
                json_content = self._repair_json(json_content)

                try:
                    recommendations = json.loads(json_content)

                    # Validate recommendations
                    valid_recommendations = []
                    for rec in recommendations:
                        if self._validate_recommendation(rec):
                            valid_recommendations.append(rec)
                        else:
                            logger.warning(
                                f"Skipping invalid recommendation: {rec.get('title', 'Unknown')}"
                            )

                    return valid_recommendations
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse repaired JSON: {str(e)}")
                    logger.error(f"JSON content: {json_content[:500]}...")
                    return []

            logger.warning("No valid JSON recommendations found in Claude response")
            return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude JSON response: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Failed to extract recommendations: {str(e)}")
            return []

    def _repair_json(self, json_str: str) -> str:
        """Attempt to repair common JSON issues"""
        try:
            # Remove trailing commas
            json_str = re.sub(r",\s*}", "}", json_str)
            json_str = re.sub(r",\s*]", "]", json_str)

            # Fix unescaped quotes in strings
            json_str = re.sub(r'(?<!\\)"(?=.*?":)', r'\\"', json_str)

            # Remove any non-JSON content before/after
            json_start = json_str.find("[")
            json_end = json_str.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                json_str = json_str[json_start:json_end]

            return json_str
        except Exception as e:
            logger.warning(f"Failed to repair JSON: {str(e)}")
            return json_str

    def _build_implementation_synthesis_prompt(
        self,
        google_analysis: str,
        google_recommendations: List[Dict[str, Any]],
        book_metadata: Dict[str, Any],
        existing_recommendations: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build prompt for implementation synthesis"""

        title = book_metadata.get("title", "Unknown")
        author = book_metadata.get("author", "Unknown")

        existing_context = ""
        if existing_recommendations:
            existing_context = f"""
EXISTING RECOMMENDATIONS CONTEXT:
{json.dumps(existing_recommendations[:5], indent=2)}

Focus on finding NEW or SIGNIFICANTLY DIFFERENT recommendations that aren't already covered.
"""

        prompt = f"""You are an expert software architect specializing in implementing technical recommendations for NBA basketball analytics systems.

BOOK: "{title}" by {author}

TASK: Synthesize Google's book analysis into specific, implementable recommendations for the NBA Simulator AWS project.

GOOGLE'S ANALYSIS:
{google_analysis}

GOOGLE'S RAW RECOMMENDATIONS:
{json.dumps(google_recommendations, indent=2)}

{existing_context}

SYNTHESIS REQUIREMENTS:

1. **Implementation Focus**: Transform Google's analysis into:
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

    def _validate_recommendation(self, rec: Dict[str, Any]) -> bool:
        """Validate recommendation structure"""
        required_fields = [
            "title",
            "description",
            "priority",
            "time_estimate",
            "mapped_phase",
        ]
        return all(field in rec for field in required_fields)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt"""
        if not context:
            return "No specific context"

        formatted = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                formatted.append(f"{key}: {len(value)} items")
            else:
                formatted.append(f"{key}: {str(value)[:100]}")

        return "\n".join(formatted)
