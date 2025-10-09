"""
Claude Model Interface
Secondary model for synthesis, explanation, and verification
"""

import anthropic
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

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
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-20250219"  # Claude 3.7 Sonnet (latest)
        logger.info(f"Initialized Claude model: {self.model}")

    async def synthesize(
        self,
        deepseek_result: str,
        original_request: str,
        context_summary: str,
        include_verification: bool = True
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
            include_verification=include_verification
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.5,  # Moderate temperature for clear explanations
                messages=[{"role": "user", "content": prompt}]
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
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "cost": total_cost,
                "execution_time": execution_time,
                "stop_reason": response.stop_reason
            }

        except Exception as e:
            logger.error(f"Claude synthesis failed: {e}")
            return {
                "success": False,
                "model": "claude",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }

    async def verify_solution(
        self,
        solution: str,
        problem: str,
        expected_properties: Optional[Dict] = None
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
        expected_props = f'Expected Properties:\n{expected_properties}' if expected_properties else ''
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
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "success": True,
                "model": "claude",
                "verification": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Claude verification failed: {e}")
            return {
                "success": False,
                "model": "claude",
                "error": str(e)
            }

    async def explain_code(
        self,
        code: str,
        context: Optional[str] = None,
        target_audience: str = "developers"
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
            "non-technical": "plain language explanation without technical jargon"
        }

        context_str = f'Context: {context}' if context else ''
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
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "success": True,
                "model": "claude",
                "explanation": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Claude explanation failed: {e}")
            return {
                "success": False,
                "model": "claude",
                "error": str(e)
            }

    async def generate_documentation(
        self,
        code: str,
        solution_description: str,
        context_used: Dict[str, Any]
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
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "success": True,
                "model": "claude",
                "documentation": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Claude documentation generation failed: {e}")
            return {
                "success": False,
                "model": "claude",
                "error": str(e)
            }

    def _build_synthesis_prompt(
        self,
        deepseek_result: str,
        original_request: str,
        context_summary: str,
        include_verification: bool
    ) -> str:
        """Build prompt for synthesis"""
        prompt_parts = [
            "Analyze and enhance this solution from DeepSeek V3:\n",
            f"Original Request:\n{original_request}\n",
            f"DeepSeek Solution:\n{deepseek_result}\n",
            f"Context Used:\n{context_summary}\n",
            "Please provide:\n",
            "1. Verification of the solution's correctness\n" if include_verification else "",
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
            "[Edge cases, performance, etc.]\n"
        ]

        return "".join(p for p in prompt_parts if p)

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
