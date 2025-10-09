"""
NBA MCP Synthesis System
Multi-model synthesis with MCP context gathering
"""

from .mcp_client import MCPClient
from .multi_model_synthesis import (
    synthesize_with_mcp_context,
    detect_query_type,
    summarize_context,
    extract_code_from_response,
    format_final_output,
    save_synthesis_result,
    quick_synthesis
)

__all__ = [
    'MCPClient',
    'synthesize_with_mcp_context',
    'detect_query_type',
    'summarize_context',
    'extract_code_from_response',
    'format_final_output',
    'save_synthesis_result',
    'quick_synthesis'
]