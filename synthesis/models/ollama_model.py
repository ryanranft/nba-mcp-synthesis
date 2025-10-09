"""
Ollama Model Interface
Optional local model for quick verification and iteration
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OllamaModel:
    """
    Ollama Local Model Interface

    Optimized for:
    - Quick local verification
    - Fast iterations during development
    - Offline functionality
    - Code review

    Recommended model: Qwen2.5-Coder:32b
    Note: Ollama is optional - gracefully degrades if not available
    """

    def __init__(self):
        """Initialize Ollama client"""
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b")
        self.available = False

        try:
            import ollama
            self.client = ollama
            self.available = self._check_availability()
            if self.available:
                logger.info(f"Initialized Ollama model: {self.model}")
            else:
                logger.warning("Ollama server not available - local verification disabled")
        except ImportError:
            logger.warning("Ollama package not installed - local verification disabled")
            self.client = None

    def _check_availability(self) -> bool:
        """Check if Ollama server is running"""
        try:
            # Try to list models to check if server is running
            self.client.list()
            return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    async def quick_verify(
        self,
        code: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Quick local verification of code

        Args:
            code: The code to verify
            description: Optional description of what the code should do

        Returns:
            Verification result (or None if Ollama not available)
        """
        if not self.available:
            return {
                "success": False,
                "model": "ollama",
                "error": "Ollama not available",
                "available": False
            }

        start_time = datetime.now()

        prompt = f"""Verify this code:

{code}

{f'Expected behavior: {description}' if description else ''}

Provide a quick review focusing on:
1. Syntax correctness
2. Logic errors
3. Common bugs
4. Performance issues

Keep it concise."""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "model": "ollama",
                "verification": response['message']['content'],
                "execution_time": execution_time,
                "cost": 0.0,  # Local model - no cost
                "available": True
            }

        except Exception as e:
            logger.error(f"Ollama verification failed: {e}")
            return {
                "success": False,
                "model": "ollama",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "available": True
            }

    async def suggest_improvements(
        self,
        code: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest code improvements

        Args:
            code: The code to improve
            context: Context about the code

        Returns:
            Improvement suggestions
        """
        if not self.available:
            return {
                "success": False,
                "model": "ollama",
                "error": "Ollama not available",
                "available": False
            }

        prompt = f"""Suggest improvements for this code:

{code}

{f'Context: {context}' if context else ''}

Suggest:
1. Performance optimizations
2. Code clarity improvements
3. Best practices
4. Potential refactoring

Be specific and actionable."""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return {
                "success": True,
                "model": "ollama",
                "suggestions": response['message']['content'],
                "cost": 0.0,
                "available": True
            }

        except Exception as e:
            logger.error(f"Ollama suggestion failed: {e}")
            return {
                "success": False,
                "model": "ollama",
                "error": str(e),
                "available": True
            }

    async def explain_diff(
        self,
        original_code: str,
        modified_code: str
    ) -> Dict[str, Any]:
        """
        Explain the differences between two code versions

        Args:
            original_code: Original version
            modified_code: Modified version

        Returns:
            Explanation of changes
        """
        if not self.available:
            return {
                "success": False,
                "model": "ollama",
                "error": "Ollama not available",
                "available": False
            }

        prompt = f"""Explain the changes between these code versions:

ORIGINAL:
{original_code}

MODIFIED:
{modified_code}

Explain:
1. What changed
2. Why the changes might have been made
3. Impact of the changes

Be concise and focus on key differences."""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return {
                "success": True,
                "model": "ollama",
                "explanation": response['message']['content'],
                "cost": 0.0,
                "available": True
            }

        except Exception as e:
            logger.error(f"Ollama diff explanation failed: {e}")
            return {
                "success": False,
                "model": "ollama",
                "error": str(e),
                "available": True
            }

    async def query(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        General query method for Ollama

        Args:
            prompt: The prompt to send
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments

        Returns:
            Query result
        """
        if not self.available:
            return {
                "success": False,
                "model": "ollama",
                "error": "Ollama not available",
                "available": False
            }

        start_time = datetime.now()

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "model": "ollama",
                "response": response['message']['content'],
                "tokens_used": len(response['message']['content'].split()),  # Approximate
                "execution_time": execution_time,
                "cost": 0.0,  # Local model - no cost
                "available": True
            }

        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return {
                "success": False,
                "model": "ollama",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "available": True
            }

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        return self.available

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if not self.available:
            return {
                "available": False,
                "model": self.model,
                "host": self.host
            }

        try:
            models = self.client.list()
            model_names = [m['name'] for m in models.get('models', [])]

            return {
                "available": True,
                "model": self.model,
                "host": self.host,
                "model_exists": self.model in model_names,
                "available_models": model_names
            }

        except Exception as e:
            return {
                "available": False,
                "model": self.model,
                "host": self.host,
                "error": str(e)
            }
