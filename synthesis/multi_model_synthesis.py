"""
Multi-Model Synthesis with MCP Context
Main orchestration for DeepSeek + Claude + Ollama synthesis
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import re
import os
import sys

from .mcp_client import MCPClient
from .models import DeepSeekModel, ClaudeModel, OllamaModel

# Try to import hierarchical env helper
try:
    from mcp_server.env_helper import get_hierarchical_env
except ImportError:
    # Fallback if env_helper not available
    def get_hierarchical_env(key, project, context):
        return os.getenv(f"{key}_{project}_{context}") or os.getenv(key)

# Try to import structured logging
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp_server.logging_config import get_logger, RequestContext, PerformanceLogger

    STRUCTURED_LOGGING_AVAILABLE = True
    logger = get_logger(__name__)
except ImportError:
    STRUCTURED_LOGGING_AVAILABLE = False
    logger = logging.getLogger(__name__)

# Import Slack notifier if available
try:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp_server.connectors.slack_notifier import SlackNotifier

    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.debug("Slack notifier not available")


async def synthesize_with_mcp_context(
    user_input: str,
    selected_code: Optional[str] = None,
    query_type: Optional[str] = None,
    file_path: Optional[str] = None,
    mcp_server_url: str = "http://localhost:3000",
    enable_ollama_verification: bool = True,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main synthesis function with MCP context gathering

    Args:
        user_input: User's request or question
        selected_code: Optional code snippet selected by user
        query_type: Type of query (auto-detected if not provided)
        file_path: Optional file path context
        mcp_server_url: URL of MCP server
        enable_ollama_verification: Whether to use Ollama for verification
        output_dir: Directory to save synthesis results

    Returns:
        Comprehensive synthesis result with all model responses
    """
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("Starting Multi-Model Synthesis with MCP Context")
    logger.info(f"User Input: {user_input[:100]}...")
    logger.info(f"Query Type: {query_type or 'Auto-detect'}")
    logger.info("=" * 80)

    result = {
        "user_input": user_input,
        "selected_code": selected_code,
        "file_path": file_path,
        "start_time": start_time.isoformat(),
        "models_used": [],
        "total_cost": 0.0,
        "total_tokens": 0,
    }

    try:
        # Step 1: Connect to MCP Server
        logger.info("\n[1/7] Connecting to MCP Server...")
        mcp_client = MCPClient(server_url=mcp_server_url)
        connected = await mcp_client.connect()

        if not connected:
            logger.warning("MCP server not available - proceeding without context")
            result["mcp_status"] = "unavailable"
            mcp_context = {}
        else:
            result["mcp_status"] = "connected"

            # Step 2: Auto-detect query type if not provided
            if not query_type:
                logger.info("\n[2/7] Auto-detecting query type...")
                query_type = detect_query_type(user_input, selected_code)
                logger.info(f"Detected query type: {query_type}")

            result["query_type"] = query_type

            # Step 3: Gather context using MCP
            logger.info("\n[3/7] Gathering context from MCP server...")
            mcp_context = await mcp_client.gather_context(
                query_type=query_type, user_input=user_input, code=selected_code
            )
            logger.info(f"Context gathered: {len(mcp_context)} sections")
            result["mcp_context"] = mcp_context

        # Step 4: Query DeepSeek for primary analysis
        logger.info("\n[4/7] Querying DeepSeek for primary analysis...")
        deepseek = DeepSeekModel(async_mode=True)

        # Build enhanced prompt with context
        deepseek_prompt = _build_deepseek_prompt(
            user_input=user_input,
            code=selected_code,
            context=mcp_context,
            query_type=query_type,
        )

        deepseek_result = await deepseek.query(
            prompt=deepseek_prompt,
            context=mcp_context,
            temperature=0.2,  # Low temperature for precision
            max_tokens=4000,
        )

        result["deepseek_result"] = deepseek_result
        result["models_used"].append("deepseek")

        if deepseek_result.get("success"):
            result["total_cost"] += deepseek_result.get("cost", 0)
            result["total_tokens"] += deepseek_result.get("tokens_used", 0)
            logger.info(
                f"✓ DeepSeek completed: {deepseek_result.get('tokens_used', 0)} tokens, ${deepseek_result.get('cost', 0):.4f}"
            )
        else:
            logger.error(f"✗ DeepSeek failed: {deepseek_result.get('error')}")
            result["status"] = "partial_failure"

        # Step 5: Synthesize with Claude
        logger.info("\n[5/7] Synthesizing with Claude...")
        claude = ClaudeModel()

        context_summary = summarize_context(mcp_context)

        synthesis_result = await claude.synthesize(
            deepseek_result=deepseek_result.get("response", ""),
            original_request=user_input,
            context_summary=context_summary,
            include_verification=True,
        )

        result["claude_synthesis"] = synthesis_result
        result["models_used"].append("claude")

        if synthesis_result.get("success"):
            result["total_cost"] += synthesis_result.get("cost", 0)
            result["total_tokens"] += synthesis_result.get("tokens_used", 0)
            logger.info(
                f"✓ Claude completed: {synthesis_result.get('tokens_used', 0)} tokens, ${synthesis_result.get('cost', 0):.4f}"
            )
        else:
            logger.error(f"✗ Claude failed: {synthesis_result.get('error')}")
            result["status"] = "partial_failure"

        # Step 6: Optional verification with Ollama
        ollama_result = None
        if enable_ollama_verification:
            logger.info("\n[6/7] Verifying with Ollama (local)...")
            ollama = OllamaModel()

            if ollama.is_available():
                # Extract code from DeepSeek response
                code_to_verify = extract_code_from_response(
                    deepseek_result.get("response", "")
                )

                if code_to_verify:
                    ollama_result = await ollama.quick_verify(
                        code=code_to_verify, description=user_input
                    )

                    result["ollama_verification"] = ollama_result
                    result["models_used"].append("ollama")

                    if ollama_result.get("success"):
                        logger.info(f"✓ Ollama verification completed (local, $0.00)")
                    else:
                        logger.warning(
                            f"✗ Ollama verification failed: {ollama_result.get('error')}"
                        )
                else:
                    logger.info("No code to verify, skipping Ollama")
            else:
                logger.info("Ollama not available, skipping verification")
                result["ollama_verification"] = {"available": False}

        # Step 7: Save results
        logger.info("\n[7/7] Saving synthesis results...")

        # Calculate total execution time
        end_time = datetime.now()
        result["end_time"] = end_time.isoformat()
        result["execution_time_seconds"] = (end_time - start_time).total_seconds()

        # Extract final code and explanations
        result["final_code"] = extract_code_from_response(
            deepseek_result.get("response", "")
        )
        result["final_explanation"] = synthesis_result.get("response", "")

        # Format final output
        formatted_output = format_final_output(
            deepseek_result=deepseek_result,
            synthesis_result=synthesis_result,
            verification=ollama_result,
            context=mcp_context,
            user_input=user_input,
        )
        result["formatted_output"] = formatted_output

        # Save to file
        if output_dir or os.getenv("SYNTHESIS_OUTPUT_DIR"):
            output_path = await save_synthesis_result(
                result=result,
                output_dir=output_dir or os.getenv("SYNTHESIS_OUTPUT_DIR"),
                query_type=query_type,
            )
            result["output_file"] = output_path
            logger.info(f"✓ Results saved to: {output_path}")

        # Set final status
        if not result.get("status"):
            result["status"] = "success"

        # Log summary
        logger.info("\n" + "=" * 80)
        logger.info("Synthesis Complete!")
        logger.info(f"Status: {result['status']}")
        logger.info(f"Models used: {', '.join(result['models_used'])}")
        logger.info(f"Total tokens: {result['total_tokens']}")
        logger.info(f"Total cost: ${result['total_cost']:.4f}")
        logger.info(f"Execution time: {result['execution_time_seconds']:.2f}s")
        logger.info("=" * 80 + "\n")

        # Send Slack notification if configured
        await _send_slack_notification(
            operation=query_type or "general_analysis",
            models_used=result["models_used"],
            execution_time=result["execution_time_seconds"],
            tokens_used=result["total_tokens"],
            cost=result["total_cost"],
            success=(result["status"] == "success"),
        )

        return result

    except Exception as e:
        logger.error(f"Synthesis failed with error: {e}", exc_info=True)
        result["status"] = "failed"
        result["error"] = str(e)
        result["end_time"] = datetime.now().isoformat()

        # Calculate execution time even for failures
        if "start_time" in result:
            end_time = datetime.now()
            result["execution_time_seconds"] = (
                end_time - datetime.fromisoformat(result["start_time"])
            ).total_seconds()

        # Send failure notification to Slack
        await _send_slack_notification(
            operation=query_type or "general_analysis",
            models_used=result.get("models_used", []),
            execution_time=result.get("execution_time_seconds", 0),
            tokens_used=result.get("total_tokens", 0),
            cost=result.get("total_cost", 0),
            success=False,
            error=str(e),
        )

        return result

    finally:
        # Cleanup
        if "mcp_client" in locals():
            await mcp_client.disconnect()
        if "deepseek" in locals():
            await deepseek.close()


def detect_query_type(user_input: str, code: Optional[str] = None) -> str:
    """
    Auto-detect query type based on keywords

    Args:
        user_input: User's input text
        code: Optional code snippet

    Returns:
        Detected query type
    """
    text = (user_input + " " + (code or "")).lower()

    # SQL optimization keywords
    sql_keywords = [
        "optimize",
        "query",
        "sql",
        "select",
        "join",
        "index",
        "explain",
        "performance",
        "slow",
    ]
    if any(k in text for k in sql_keywords) and ("select" in text or "from" in text):
        return "sql_optimization"

    # Statistical analysis keywords
    stats_keywords = [
        "statistical",
        "statistics",
        "analysis",
        "correlation",
        "regression",
        "mean",
        "median",
        "distribution",
    ]
    if any(k in text for k in stats_keywords):
        return "statistical_analysis"

    # ETL generation keywords
    etl_keywords = [
        "etl",
        "extract",
        "transform",
        "load",
        "pipeline",
        "migration",
        "import",
        "export",
    ]
    if any(k in text for k in etl_keywords):
        return "etl_generation"

    # Debugging keywords
    debug_keywords = [
        "debug",
        "error",
        "exception",
        "bug",
        "fix",
        "traceback",
        "failing",
        "broken",
    ]
    if any(k in text for k in debug_keywords):
        return "debugging"

    # Code optimization keywords
    code_keywords = [
        "optimize code",
        "refactor",
        "improve",
        "performance",
        "faster",
        "efficient",
    ]
    if any(k in text for k in code_keywords) and code:
        return "code_optimization"

    # Default to general analysis
    return "general_analysis"


def summarize_context(context: Dict[str, Any]) -> str:
    """
    Summarize MCP context for Claude

    Args:
        context: Full MCP context dictionary

    Returns:
        Concise context summary
    """
    if not context:
        return "No MCP context available"

    summary_parts = []

    # Summarize schemas
    if "schemas" in context:
        tables = list(context["schemas"].keys())
        summary_parts.append(f"Database schemas: {', '.join(tables)}")

    # Summarize table stats
    if "table_stats" in context:
        stats = context["table_stats"]
        if stats:
            summary_parts.append(f"Table statistics available for {len(stats)} tables")

    # Summarize sample data
    if "sample_data" in context:
        samples = context["sample_data"]
        if samples:
            summary_parts.append(f"Sample data loaded from {len(samples)} tables")

    # Summarize files
    if "related_files" in context or "files" in context:
        files = context.get("related_files", context.get("files", {}))
        if files:
            summary_parts.append(f"Related files: {', '.join(files.keys())}")

    # Summarize explain plan
    if "explain_plan" in context:
        summary_parts.append("SQL EXPLAIN plan available")

    # Summarize metadata
    if "metadata" in context and context["metadata"]:
        summary_parts.append(
            f"Metadata available for {len(context['metadata'])} tables"
        )

    return " | ".join(summary_parts) if summary_parts else "Minimal context available"


def extract_code_from_response(response: str) -> Optional[str]:
    """
    Extract code blocks from model response

    Args:
        response: Model's response text

    Returns:
        Extracted code or None
    """
    if not response:
        return None

    # Extract code from markdown code blocks
    code_pattern = r"```(?:python|sql|bash)?\n(.*?)```"
    matches = re.findall(code_pattern, response, re.DOTALL)

    if matches:
        # Return the largest code block (likely the main solution)
        return max(matches, key=len).strip()

    # If no code blocks, check if entire response looks like code
    if response.strip().startswith(("def ", "class ", "SELECT", "import", "from ")):
        return response.strip()

    return None


def format_final_output(
    deepseek_result: Dict[str, Any],
    synthesis_result: Dict[str, Any],
    verification: Optional[Dict[str, Any]],
    context: Dict[str, Any],
    user_input: str,
) -> str:
    """
    Format final output for saving

    Args:
        deepseek_result: DeepSeek's analysis result
        synthesis_result: Claude's synthesis result
        verification: Optional Ollama verification
        context: MCP context used
        user_input: Original user input

    Returns:
        Formatted markdown output
    """
    output_lines = [
        "# Multi-Model Synthesis Result",
        "",
        "## Original Request",
        user_input,
        "",
        "## Context Used",
        summarize_context(context),
        "",
        "## DeepSeek Analysis",
        deepseek_result.get("response", "No response available"),
        "",
        "## Claude Synthesis",
        synthesis_result.get("response", "No response available"),
        "",
    ]

    # Add verification if available
    if verification and verification.get("success"):
        output_lines.extend(
            [
                "## Ollama Verification",
                verification.get("verification", "No verification available"),
                "",
            ]
        )

    # Add metadata
    output_lines.extend(
        [
            "## Synthesis Metadata",
            f"- DeepSeek Tokens: {deepseek_result.get('tokens_used', 0)}",
            f"- DeepSeek Cost: ${deepseek_result.get('cost', 0):.4f}",
            f"- Claude Tokens: {synthesis_result.get('tokens_used', 0)}",
            f"- Claude Cost: ${synthesis_result.get('cost', 0):.4f}",
            f"- Total Cost: ${(deepseek_result.get('cost', 0) + synthesis_result.get('cost', 0)):.4f}",
            "",
        ]
    )

    return "\n".join(output_lines)


async def save_synthesis_result(
    result: Dict[str, Any], output_dir: str, query_type: str
) -> str:
    """
    Save synthesis result to file

    Args:
        result: Full synthesis result
        output_dir: Output directory path
        query_type: Type of query for filename

    Returns:
        Path to saved file
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"synthesis_{query_type}_{timestamp}.json"
    file_path = output_path / filename

    # Save JSON result
    with open(file_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    # Also save formatted markdown
    md_filename = f"synthesis_{query_type}_{timestamp}.md"
    md_path = output_path / md_filename

    with open(md_path, "w") as f:
        f.write(result.get("formatted_output", "No output available"))

    logger.info(f"Saved synthesis result to {file_path}")
    logger.info(f"Saved formatted output to {md_path}")

    return str(file_path)


def _build_deepseek_prompt(
    user_input: str, code: Optional[str], context: Dict[str, Any], query_type: str
) -> str:
    """
    Build enhanced prompt for DeepSeek

    Args:
        user_input: User's input
        code: Optional code snippet
        context: MCP context
        query_type: Type of query

    Returns:
        Enhanced prompt with context
    """
    prompt_parts = [user_input]

    # Add code if provided
    if code:
        prompt_parts.append(f"\n\nCode to analyze:\n```\n{code}\n```")

    # Add relevant context based on query type
    if query_type == "sql_optimization" and context.get("schemas"):
        prompt_parts.append("\n\nAvailable table schemas:")
        for table, schema in context.get("schemas", {}).items():
            prompt_parts.append(f"\nTable: {table}")
            if isinstance(schema, dict) and "columns" in schema:
                for col in schema["columns"]:
                    prompt_parts.append(f"  - {col.get('name')}: {col.get('type')}")

    if context.get("table_stats"):
        prompt_parts.append("\n\nTable statistics:")
        for table, stats in context.get("table_stats", {}).items():
            prompt_parts.append(f"\nTable: {table}")
            prompt_parts.append(f"  - Rows: {stats.get('row_count', 'N/A')}")
            prompt_parts.append(f"  - Size: {stats.get('size_mb', 'N/A')} MB")

    if context.get("explain_plan"):
        plan = context["explain_plan"]
        prompt_parts.append(f"\n\nEXPLAIN Plan:\n{plan.get('plan', 'N/A')}")

    return "\n".join(prompt_parts)


def extract_table_name(text: str, source_type: Optional[str] = None) -> List[str]:
    """
    Extract table names from text

    Args:
        text: Text to search
        source_type: Optional filter for 'source' or 'target' tables

    Returns:
        List of table names
    """
    # Delegate to MCPClient helper
    client = MCPClient()
    return client._extract_table_names(text, source_type)


def extract_file_reference(text: str) -> List[str]:
    """
    Extract file paths from text

    Args:
        text: Text to search

    Returns:
        List of file paths
    """
    # Delegate to MCPClient helper
    client = MCPClient()
    return client._extract_file_references(text)


def calculate_total_time(start_time: datetime, end_time: datetime) -> float:
    """
    Calculate execution time in seconds

    Args:
        start_time: Start datetime
        end_time: End datetime

    Returns:
        Execution time in seconds
    """
    return (end_time - start_time).total_seconds()


# Convenience function for quick synthesis
async def quick_synthesis(prompt: str, code: Optional[str] = None, **kwargs) -> str:
    """
    Quick synthesis function that returns just the final code/solution

    Args:
        prompt: User's request
        code: Optional code snippet
        **kwargs: Additional arguments for synthesize_with_mcp_context

    Returns:
        Final code or solution as string
    """
    result = await synthesize_with_mcp_context(
        user_input=prompt, selected_code=code, **kwargs
    )

    if result.get("status") == "success":
        return result.get("final_code") or result.get("final_explanation", "")
    else:
        raise RuntimeError(f"Synthesis failed: {result.get('error', 'Unknown error')}")


async def _send_slack_notification(
    operation: str,
    models_used: List[str],
    execution_time: float,
    tokens_used: int,
    cost: float,
    success: bool = True,
    error: Optional[str] = None,
):
    """
    Send Slack notification for synthesis completion

    Args:
        operation: Type of operation
        models_used: List of models used
        execution_time: Execution time in seconds
        tokens_used: Total tokens used
        cost: Total cost in dollars
        success: Whether synthesis succeeded
        error: Optional error message
    """
    if not SLACK_AVAILABLE:
        return

    # Check if Slack webhook is configured using hierarchical naming
    webhook_url = get_hierarchical_env("SLACK_WEBHOOK_URL", "NBA_MCP_SYNTHESIS", "WORKFLOW")
    if not webhook_url:
        logger.debug("Slack webhook not configured, skipping notification")
        return

    try:
        # Initialize Slack notifier
        slack = SlackNotifier(
            webhook_url=webhook_url, channel=os.getenv("SLACK_CHANNEL")  # Optional
        )

        # Send notification
        await slack.notify_synthesis_complete(
            operation=operation,
            models_used=models_used,
            execution_time=execution_time,
            tokens_used=tokens_used,
            success=success,
        )

        # If there was an error, send additional error context
        if not success and error:
            await slack.send_notification(
                {
                    "text": f"Error details: {error[:500]}",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"```{error[:1000]}```"},
                        }
                    ],
                }
            )

        logger.debug(
            f"Slack notification sent: {operation} {'success' if success else 'failed'}"
        )

    except Exception as e:
        # Don't let Slack failures break synthesis
        logger.warning(f"Failed to send Slack notification: {e}")
