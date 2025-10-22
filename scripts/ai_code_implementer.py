#!/usr/bin/env python3
"""
AI Code Implementer

Uses Claude Sonnet 4 to generate complete, production-ready implementations
from recommendations. Context-aware and integrates with existing code.

Features:
- Claude API integration for code generation
- Context gathering from existing code
- Intelligent prompt engineering
- Full implementation (not just skeletons)
- Integration-aware code generation
- Error handling and logging

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-22
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import secrets management
from mcp_server.env_helper import get_api_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to import Anthropic
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("⚠️  Anthropic library not available. Install with: pip install anthropic")


@dataclass
class ImplementationContext:
    """Context for code implementation"""
    existing_code: Optional[str] = None
    existing_classes: List[str] = None
    existing_functions: List[str] = None
    database_schema: Optional[str] = None
    project_structure: Optional[str] = None
    similar_implementations: List[str] = None
    integration_strategy: Optional[str] = None


@dataclass
class GeneratedImplementation:
    """Generated code implementation"""
    code: str
    language: str
    description: str
    imports_needed: List[str]
    dependencies: List[str]
    integration_notes: str
    estimated_completeness: float  # 0.0 to 1.0


class AICodeImplementer:
    """
    Generates production-ready code using Claude Sonnet 4.

    Features:
    - Full implementation (not skeletons)
    - Context-aware generation
    - Integration with existing code
    - Multiple file types (Python, SQL, etc.)
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 8000,
        temperature: float = 0.1
    ):
        """
        Initialize AI Code Implementer.

        Args:
            model: Claude model to use
            max_tokens: Maximum tokens per generation
            temperature: Sampling temperature
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize Anthropic client
        # Use hierarchical secrets loading
        api_key = get_api_key('ANTHROPIC')
        if api_key and ANTHROPIC_AVAILABLE:
            self.client = Anthropic(api_key=api_key)
            logger.info(f"🤖 AI Code Implementer initialized")
            logger.info(f"   Model: {model}")
            logger.info(f"   Max tokens: {max_tokens}")
        else:
            self.client = None
            if not ANTHROPIC_AVAILABLE:
                logger.warning("⚠️  Anthropic library not installed")
            else:
                logger.warning("⚠️  ANTHROPIC_API_KEY not found in environment")
                logger.warning("⚠️  Make sure secrets are initialized with: from mcp_server.secrets_loader import init_secrets; init_secrets()")

    def implement_recommendation(
        self,
        recommendation: Dict[str, Any],
        context: ImplementationContext,
        integration_strategy: str = "create_new"
    ) -> Optional[GeneratedImplementation]:
        """
        Generate complete implementation for a recommendation.

        Args:
            recommendation: Recommendation dictionary
            context: Implementation context
            integration_strategy: How to integrate (create_new, extend, modify)

        Returns:
            GeneratedImplementation or None if failed
        """
        if not self.client:
            logger.error("❌ Claude client not initialized")
            return None

        title = recommendation.get('title', 'Untitled')
        logger.info(f"🤖 Generating implementation for: {title}")
        logger.info(f"   Strategy: {integration_strategy}")

        try:
            # Build prompt
            prompt = self._build_implementation_prompt(
                recommendation,
                context,
                integration_strategy
            )

            logger.info(f"   Prompt length: {len(prompt)} chars")

            # Call Claude API
            logger.info(f"   Calling Claude API...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract generated code
            generated_text = response.content[0].text

            logger.info(f"   ✅ Generated {len(generated_text)} characters")

            # Parse generated code
            implementation = self._parse_generated_code(
                generated_text,
                recommendation
            )

            return implementation

        except Exception as e:
            logger.error(f"❌ Failed to generate implementation: {e}")
            return None

    def _build_implementation_prompt(
        self,
        recommendation: Dict[str, Any],
        context: ImplementationContext,
        integration_strategy: str
    ) -> str:
        """Build comprehensive prompt for Claude"""
        title = recommendation.get('title', 'Untitled')
        description = recommendation.get('description', 'No description')
        technical_details = recommendation.get('technical_details', '')
        steps = recommendation.get('implementation_steps', [])
        time_estimate = recommendation.get('time_estimate', 'Unknown')

        # Build context section
        context_section = self._build_context_section(context)

        # Build integration instructions
        integration_instructions = self._build_integration_instructions(
            integration_strategy,
            context
        )

        # Build the prompt
        prompt = f"""You are an expert Python developer implementing a feature for an NBA analytics platform.

# Task: {title}

## Description
{description}

## Technical Details
{technical_details}

## Implementation Steps
{self._format_steps(steps)}

## Time Estimate
{time_estimate}

{context_section}

{integration_instructions}

## Requirements

1. **Production-Ready Code**: Generate complete, working implementations with:
   - Comprehensive error handling
   - Detailed logging using Python's logging module
   - Full type hints (from typing import ...)
   - Complete docstrings (Google style)
   - Input validation
   - Edge case handling

2. **Code Quality**:
   - Follow PEP 8 style guide
   - Use meaningful variable names
   - Keep functions focused and small
   - Add comments for complex logic
   - Include TODO comments only where truly necessary

3. **Testing Considerations**:
   - Design code to be testable
   - Use dependency injection where appropriate
   - Avoid hard-coded values
   - Make external dependencies mockable

4. **Integration**:
   - Match existing code style
   - Reuse existing utilities/helpers
   - Follow project conventions
   - Import from existing modules when possible

## Output Format

Provide ONLY the complete Python code implementation. Structure your response as:

```python
#!/usr/bin/env python3
\"\"\"
[Module docstring]
\"\"\"

[Complete implementation]

if __name__ == "__main__":
    # CLI or testing code
    pass
```

Do NOT include:
- Explanations before or after code
- Markdown headings
- Multiple code blocks
- Incomplete implementations

Generate complete, production-ready code now:"""

        return prompt

    def _build_context_section(self, context: ImplementationContext) -> str:
        """Build context section of prompt"""
        sections = []

        if context.existing_code:
            sections.append(f"""
## Existing Code Context

The target file already exists with the following structure:

```python
{context.existing_code[:2000]}  # Truncated for brevity
```

Classes: {', '.join(context.existing_classes) if context.existing_classes else 'None'}
Functions: {', '.join(context.existing_functions) if context.existing_functions else 'None'}
""")

        if context.database_schema:
            sections.append(f"""
## Database Schema

{context.database_schema}
""")

        if context.similar_implementations:
            sections.append(f"""
## Similar Implementations in Project

Reference these existing implementations for style and patterns:

{chr(10).join(f'- {impl}' for impl in context.similar_implementations[:3])}
""")

        if context.project_structure:
            sections.append(f"""
## Project Structure

{context.project_structure}
""")

        return '\n'.join(sections) if sections else "## Context\n\nNo existing code context."

    def _build_integration_instructions(
        self,
        strategy: str,
        context: ImplementationContext
    ) -> str:
        """Build integration-specific instructions"""
        if strategy == "create_new":
            return """
## Integration Strategy: Create New Module

Create a completely new, standalone module with:
- All necessary imports
- Complete class/function implementations
- Main block for CLI usage
- No dependencies on existing code (unless explicitly importing utilities)
"""

        elif strategy == "extend_existing":
            return f"""
## Integration Strategy: Extend Existing Code

Add new functionality to the existing module:
- Add new methods to existing classes
- Maintain existing code style and patterns
- Do NOT modify existing functions
- Ensure backward compatibility
- Add imports as needed at the top
"""

        elif strategy == "modify_existing":
            return """
## Integration Strategy: Modify Existing Code

Carefully modify existing code:
- Preserve existing functionality
- Add new features alongside existing ones
- Maintain backward compatibility
- Update docstrings to reflect changes
- Add detailed comments explaining modifications
"""

        else:
            return "## Integration Strategy: Standard implementation"

    def _format_steps(self, steps: List[str]) -> str:
        """Format implementation steps"""
        if not steps:
            return "No specific steps provided."

        formatted = []
        for i, step in enumerate(steps, 1):
            formatted.append(f"{i}. {step}")

        return '\n'.join(formatted)

    def _parse_generated_code(
        self,
        generated_text: str,
        recommendation: Dict[str, Any]
    ) -> GeneratedImplementation:
        """Parse and validate generated code"""
        # Extract code from markdown if present
        code_match = re.search(r'```python\n(.*?)```', generated_text, re.DOTALL)

        if code_match:
            code = code_match.group(1).strip()
        else:
            # Assume entire response is code
            code = generated_text.strip()

        # Extract imports
        imports = self._extract_imports(code)

        # Estimate completeness based on code characteristics
        completeness = self._estimate_completeness(code)

        # Extract description from docstring
        description_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        description = description_match.group(1).strip() if description_match else recommendation.get('title', 'Implementation')

        return GeneratedImplementation(
            code=code,
            language='python',
            description=description,
            imports_needed=imports,
            dependencies=[],  # Could parse requirements from imports
            integration_notes="Generated code ready for integration",
            estimated_completeness=completeness
        )

    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code"""
        import_lines = []
        for line in code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                import_lines.append(stripped)

        return import_lines

    def _estimate_completeness(self, code: str) -> float:
        """Estimate how complete the implementation is"""
        score = 0.0

        # Check for key indicators
        if 'def ' in code:
            score += 0.2
        if 'class ' in code:
            score += 0.2
        if 'logging' in code:
            score += 0.1
        if 'raise ' in code or 'except ' in code:
            score += 0.1
        if '"""' in code:  # Has docstrings
            score += 0.1
        if 'if __name__' in code:
            score += 0.1
        if 'typing' in code or ': ' in code:  # Type hints
            score += 0.1
        if len(code) > 500:  # Substantial code
            score += 0.1

        return min(score, 1.0)

    def generate_sql_implementation(
        self,
        recommendation: Dict[str, Any],
        database_schema: Optional[str] = None
    ) -> Optional[GeneratedImplementation]:
        """Generate SQL implementation"""
        if not self.client:
            logger.error("❌ Claude client not initialized")
            return None

        title = recommendation.get('title', 'Untitled')
        logger.info(f"🤖 Generating SQL implementation for: {title}")

        prompt = f"""Generate a complete SQL implementation for: {title}

Description: {recommendation.get('description', '')}

Technical Details: {recommendation.get('technical_details', '')}

{f"Database Schema:{chr(10)}{database_schema}" if database_schema else ""}

Generate production-ready SQL with:
- Complete DDL (CREATE TABLE, INDEX, etc.)
- Stored procedures if needed
- Comments explaining each section
- Performance considerations (indexes, etc.)
- Error handling where applicable

Provide ONLY the SQL code, no explanations:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            sql_code = response.content[0].text.strip()

            # Extract from markdown if present
            code_match = re.search(r'```sql\n(.*?)```', sql_code, re.DOTALL)
            if code_match:
                sql_code = code_match.group(1).strip()

            return GeneratedImplementation(
                code=sql_code,
                language='sql',
                description=title,
                imports_needed=[],
                dependencies=[],
                integration_notes="SQL implementation",
                estimated_completeness=0.9
            )

        except Exception as e:
            logger.error(f"❌ Failed to generate SQL: {e}")
            return None

    def generate_config_implementation(
        self,
        recommendation: Dict[str, Any],
        config_format: str = 'yaml'
    ) -> Optional[GeneratedImplementation]:
        """Generate configuration file"""
        if not self.client:
            logger.error("❌ Claude client not initialized")
            return None

        title = recommendation.get('title', 'Untitled')
        logger.info(f"🤖 Generating {config_format.upper()} config for: {title}")

        prompt = f"""Generate a {config_format.upper()} configuration file for: {title}

Description: {recommendation.get('description', '')}

Generate a well-structured, production-ready {config_format.upper()} configuration with:
- Clear comments explaining each setting
- Sensible defaults
- Environment-specific sections if needed
- Validation-friendly structure

Provide ONLY the {config_format.upper()} content, no explanations:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            config_code = response.content[0].text.strip()

            # Extract from markdown if present
            code_match = re.search(rf'```{config_format}\n(.*?)```', config_code, re.DOTALL)
            if code_match:
                config_code = code_match.group(1).strip()

            return GeneratedImplementation(
                code=config_code,
                language=config_format,
                description=title,
                imports_needed=[],
                dependencies=[],
                integration_notes=f"{config_format.upper()} configuration",
                estimated_completeness=0.9
            )

        except Exception as e:
            logger.error(f"❌ Failed to generate config: {e}")
            return None


def main():
    """CLI for testing AI code implementer"""
    import argparse

    parser = argparse.ArgumentParser(description='Test AI Code Implementer')
    parser.add_argument('--recommendation', required=True, help='Recommendation JSON file')
    parser.add_argument('--output', help='Output file for generated code')
    args = parser.parse_args()

    # Load recommendation
    with open(args.recommendation, 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        rec = data[0]
    elif isinstance(data, dict) and 'recommendations' in data:
        rec = data['recommendations'][0]
    else:
        rec = data

    # Initialize implementer
    implementer = AICodeImplementer()

    # Create context
    context = ImplementationContext()

    # Generate implementation
    print(f"\n{'='*60}")
    print(f"Generating implementation for: {rec.get('title', 'Untitled')}")
    print(f"{'='*60}\n")

    implementation = implementer.implement_recommendation(
        recommendation=rec,
        context=context,
        integration_strategy="create_new"
    )

    if implementation:
        print(f"✅ Implementation generated successfully")
        print(f"   Language: {implementation.language}")
        print(f"   Completeness: {implementation.estimated_completeness:.1%}")
        print(f"   Imports: {len(implementation.imports_needed)}")
        print(f"   Code length: {len(implementation.code)} characters")

        if args.output:
            with open(args.output, 'w') as f:
                f.write(implementation.code)
            print(f"\n💾 Saved to: {args.output}")
        else:
            print(f"\n{'-'*60}")
            print(f"Generated Code:")
            print(f"{'-'*60}\n")
            print(implementation.code[:500])
            print(f"\n... (truncated)")
    else:
        print(f"❌ Failed to generate implementation")


if __name__ == '__main__':
    main()
