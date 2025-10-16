"""
DeepSeek Model Interface
Primary model for mathematical reasoning, SQL optimization, and code generation
"""

from openai import OpenAI, AsyncOpenAI
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DeepSeekModel:
    """
    DeepSeek V3 Model Interface

    Optimized for:
    - Mathematical analysis and statistical reasoning
    - SQL query optimization
    - Code generation and debugging
    - Performance analysis

    Pricing: ~$0.14/1M input tokens, $0.28/1M output tokens (20x cheaper than GPT-4)
    """

    def __init__(self, api_key: str = None, async_mode: bool = True):
        """
        Initialize DeepSeek client

        Args:
            api_key: DeepSeek API key (if None, will try to get from environment)
            async_mode: Use async client (recommended for better performance)
        """
        # Try to get API key from parameter or environment
        if api_key:
            self.api_key = api_key
        else:
            # Try new naming convention first, then fallback to old
            self.api_key = (os.getenv("DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW") or
                           os.getenv("DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                           os.getenv("DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_TEST") or
                           os.getenv("DEEPSEEK_API_KEY"))

        if not self.api_key:
            raise ValueError("DeepSeek API key not provided and not found in environment variables")

        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        if async_mode:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=base_url)

        self.async_mode = async_mode
        logger.info(f"Initialized DeepSeek model: {self.model}")

    async def query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query DeepSeek with MCP context

        Args:
            prompt: User's query or request
            context: MCP context (database schema, table stats, sample data, etc.)
            temperature: 0.0-1.0 (use 0.2-0.3 for mathematical/SQL tasks, 0.5-0.7 for creative)
            max_tokens: Maximum response length
            system_prompt: Custom system prompt (optional)

        Returns:
            Dict with response, tokens used, cost, etc.
        """
        start_time = datetime.now()

        # Format prompt with context
        enhanced_prompt = self._format_prompt_with_context(prompt, context or {})

        # Default system prompt optimized for NBA data analysis
        if not system_prompt:
            system_prompt = self._get_default_system_prompt()

        try:
            # Call DeepSeek API
            if self.async_mode:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "model": "deepseek",
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "tokens_input": response.usage.prompt_tokens,
                "tokens_output": response.usage.completion_tokens,
                "cost": self._calculate_cost(response.usage),
                "execution_time": execution_time,
                "temperature": temperature,
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            logger.error(f"DeepSeek query failed: {e}")
            return {
                "success": False,
                "model": "deepseek",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }

    async def optimize_sql(
        self,
        sql_query: str,
        schema: Optional[Dict] = None,
        table_stats: Optional[Dict] = None,
        explain_plan: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Specialized method for SQL optimization

        Args:
            sql_query: The SQL query to optimize
            schema: Database schema information
            table_stats: Table statistics (row counts, indexes, etc.)
            explain_plan: PostgreSQL EXPLAIN output

        Returns:
            Optimized SQL query with explanation
        """
        context = {
            "query": sql_query,
            "schema": schema,
            "table_stats": table_stats,
            "explain_plan": explain_plan
        }

        prompt = f"""Optimize this SQL query for PostgreSQL:

{sql_query}

Provide:
1. Optimized query
2. Explanation of changes
3. Expected performance improvement
4. Index recommendations (if applicable)"""

        return await self.query(
            prompt=prompt,
            context=context,
            temperature=0.2,  # Low temperature for precision
            system_prompt="You are an expert PostgreSQL database optimizer specializing in NBA data analysis."
        )

    async def analyze_statistics(
        self,
        data_description: str,
        sample_data: Optional[Any] = None,
        statistical_question: str = ""
    ) -> Dict[str, Any]:
        """
        Specialized method for statistical analysis

        Args:
            data_description: Description of the data
            sample_data: Sample data for context
            statistical_question: Specific statistical question

        Returns:
            Statistical analysis and recommendations
        """
        context = {
            "data_description": data_description,
            "sample_data": sample_data
        }

        prompt = f"""Perform statistical analysis:

Data: {data_description}
Question: {statistical_question}

Provide:
1. Statistical approach
2. Mathematical formulas
3. Expected insights
4. Code implementation (Python/pandas)"""

        return await self.query(
            prompt=prompt,
            context=context,
            temperature=0.25,
            system_prompt="You are an expert statistician and data scientist specializing in sports analytics."
        )

    async def debug_code(
        self,
        code: str,
        error_message: Optional[str] = None,
        expected_behavior: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Specialized method for code debugging

        Args:
            code: The code with bugs
            error_message: Error message if available
            expected_behavior: What the code should do

        Returns:
            Fixed code with explanation
        """
        context = {
            "code": code,
            "error": error_message,
            "expected": expected_behavior
        }

        prompt = f"""Debug this code:

{code}

{f'Error: {error_message}' if error_message else ''}
{f'Expected: {expected_behavior}' if expected_behavior else ''}

Provide:
1. Root cause analysis
2. Fixed code
3. Explanation of the fix
4. Prevention recommendations"""

        return await self.query(
            prompt=prompt,
            context=context,
            temperature=0.3,
            system_prompt="You are an expert Python developer specializing in data pipelines and ETL systems."
        )

    def _format_prompt_with_context(self, prompt: str, context: Dict) -> str:
        """Format user prompt with MCP context"""
        sections = [f"User Request:\n{prompt}\n"]

        # Add relevant context sections
        if context.get("schema"):
            sections.append(f"Database Schema:\n{self._format_schema(context['schema'])}\n")

        if context.get("table_stats"):
            sections.append(f"Table Statistics:\n{self._format_stats(context['table_stats'])}\n")

        if context.get("sample_data"):
            sections.append(f"Sample Data:\n{self._format_sample_data(context['sample_data'])}\n")

        if context.get("explain_plan"):
            sections.append(f"EXPLAIN Plan:\n{context['explain_plan']}\n")

        if context.get("query"):
            sections.append(f"Current Query:\n{context['query']}\n")

        return "\n".join(sections)

    def _format_schema(self, schema: Any) -> str:
        """Format schema for prompt"""
        if isinstance(schema, dict):
            return "\n".join([f"  {k}: {v}" for k, v in schema.items()])
        return str(schema)

    def _format_stats(self, stats: Any) -> str:
        """Format statistics for prompt"""
        if isinstance(stats, dict):
            return "\n".join([f"  {k}: {v}" for k, v in stats.items()])
        return str(stats)

    def _format_sample_data(self, data: Any) -> str:
        """Format sample data for prompt"""
        if isinstance(data, list) and len(data) > 0:
            return f"  First {min(5, len(data))} rows:\n  " + "\n  ".join(str(row) for row in data[:5])
        return str(data)

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for NBA data analysis"""
        return """You are an expert AI assistant specializing in:
1. SQL query optimization for PostgreSQL databases
2. Statistical analysis and mathematical reasoning
3. Python code generation and debugging
4. NBA data analysis and sports analytics
5. ETL pipeline development

Your responses should be:
- Precise and mathematically accurate
- Optimized for performance
- Well-documented with clear explanations
- Production-ready code quality
- Consider NBA domain knowledge (player stats, team performance, game metrics)

Focus on actionable, implementable solutions."""

    def _calculate_cost(self, usage) -> float:
        """
        Calculate API cost

        DeepSeek pricing:
        - Input: $0.14 per 1M tokens
        - Output: $0.28 per 1M tokens
        """
        input_cost = (usage.prompt_tokens / 1_000_000) * 0.14
        output_cost = (usage.completion_tokens / 1_000_000) * 0.28
        return input_cost + output_cost

    async def analyze_book_content(
        self,
        book_content: str,
        book_metadata: Dict[str, Any],
        existing_recommendations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze book content and extract raw recommendations.
        Parallel to Google's analysis but with DeepSeek's perspective.

        Args:
            book_content: The full text content of the book.
            book_metadata: Dictionary containing book title, author, etc.
            existing_recommendations: List of existing recommendations for context.

        Returns:
            A dictionary containing DeepSeek's analysis and raw recommendations.
        """
        start_time = datetime.now()

        prompt = self._build_extraction_prompt(book_content, book_metadata, existing_recommendations)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for factual extraction
                max_tokens=4000
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Calculate cost: ~$0.14/1M input, $0.28/1M output
            input_cost = (response.usage.prompt_tokens / 1_000_000) * 0.14
            output_cost = (response.usage.completion_tokens / 1_000_000) * 0.28
            total_cost = input_cost + output_cost

            # Extract text from response
            response_text = response.choices[0].message.content

            # Attempt to extract JSON recommendations
            raw_recommendations = self._extract_json_from_response(response_text)

            return {
                "success": True,
                "model": "deepseek",
                "analysis_content": response_text,
                "raw_recommendations": raw_recommendations,
                "tokens_input": response.usage.prompt_tokens,
                "tokens_output": response.usage.completion_tokens,
                "cost": total_cost,
                "processing_time": execution_time,
            }

        except Exception as e:
            logger.error(f"DeepSeek analysis failed: {e}")
            return {
                "success": False,
                "model": "deepseek",
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }

    def _build_extraction_prompt(
        self,
        book_content: str,
        book_metadata: Dict[str, Any],
        existing_recommendations: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build prompt for book content analysis."""
        title = book_metadata.get('title', 'Unknown')
        author = book_metadata.get('author', 'Unknown')

        existing_context = ""
        if existing_recommendations:
            existing_context = f"""
EXISTING RECOMMENDATIONS CONTEXT:
Here are some recommendations already identified from other books or previous analyses. Avoid duplicating these, but identify new or significantly different enhancements:
{json.dumps(existing_recommendations[:5], indent=2)}
"""

        prompt = f"""You are an expert technical book analyst for an NBA basketball analytics and simulation project.
Your task is to thoroughly read and analyze the following technical book content.

IMPORTANT: This is a comprehensive technical textbook. Extract ALL relevant recommendations, including:
- Statistical methods and models
- Data analysis techniques
- Implementation approaches
- Best practices
- Mathematical frameworks
- Validation strategies

Aim for 20-50 recommendations minimum. Be thorough and comprehensive.

BOOK TITLE: "{title}"
BOOK AUTHOR: {author}

BOOK CONTENT:
{book_content}

{existing_context}

After analyzing the content, provide two main outputs:

1. **Comprehensive Analysis Summary**: A detailed summary of the book's key concepts, methodologies, and technical insights that are relevant to building and enhancing an NBA basketball analytics and simulation platform on AWS. Focus on aspects related to data processing, machine learning, statistical modeling, system architecture, performance optimization, and data quality.

2. **Raw Recommendations**: A list of potential technical recommendations directly extracted from the book. These should be raw ideas, concepts, or features that could be implemented. Do NOT synthesize or filter them yet; just extract them as they appear or are strongly implied. Each recommendation should have a brief title and description.

OUTPUT FORMAT:
Provide your response in a structured format, starting with the analysis summary, followed by a JSON array of raw recommendations.

---
## Comprehensive Analysis Summary
[Your detailed summary here, covering key concepts, methodologies, and technical insights relevant to NBA analytics on AWS.]

---
## Raw Recommendations
```json
[
  {{
    "title": "Raw Recommendation Title 1",
    "description": "Brief description of the raw recommendation 1",
    "source_chapter_or_section": "Chapter X"
  }},
  {{
    "title": "Raw Recommendation Title 2",
    "description": "Brief description of the raw recommendation 2",
    "source_chapter_or_section": "Chapter Y"
  }}
]
```
IMPORTANT: Ensure the JSON is valid and correctly formatted. Do not add any extra text outside the JSON block for the raw recommendations section.
"""
        return prompt

    def _extract_json_from_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Extracts the JSON array from the response text."""
        try:
            # Find the start and end of the JSON block
            json_start = response_text.find('```json')
            json_end = response_text.rfind('```')

            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = response_text[json_start + len('```json'):json_end].strip()
                return json.loads(json_str)
            else:
                logger.warning("No JSON block found in DeepSeek response.")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from DeepSeek response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting JSON from response: {e}")
            return []

    async def close(self):
        """Close the client connection"""
        if self.async_mode and hasattr(self.client, 'close'):
            await self.client.close()