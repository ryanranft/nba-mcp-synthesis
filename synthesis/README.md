# NBA MCP Synthesis System

Multi-model AI synthesis with MCP context gathering for the NBA Simulator project.

## Overview

This synthesis system combines three AI models with MCP (Model Context Protocol) to provide intelligent, context-aware analysis and code generation:

1. **DeepSeek V3** - Primary analysis (mathematical reasoning, SQL optimization, code generation)
2. **Claude 3.5 Sonnet** - Synthesis and explanation
3. **Ollama (Qwen2.5-Coder)** - Optional local verification (cost-free)

## Architecture

```
User Input → MCP Client → Context Gathering → DeepSeek → Claude → Ollama → Final Output
                ↓
         [Database, S3, Glue, Files]
```

## Features

### Context Gathering

The MCP Client automatically gathers relevant context based on query type:

- **SQL Optimization**: Database schemas, table statistics, EXPLAIN plans
- **Statistical Analysis**: Sample data, metadata, data types
- **ETL Generation**: Source/target schemas, sample data
- **Code Optimization**: Related files, similar code patterns
- **Debugging**: Error info, related files, table schemas
- **General Analysis**: Tables, files referenced in input

### Query Types

The system supports automatic detection of:

- `sql_optimization` - SQL query optimization
- `code_optimization` - Code improvement and refactoring
- `statistical_analysis` - Statistical analysis and math
- `etl_generation` - ETL pipeline generation
- `debugging` - Bug fixing and error resolution
- `general_analysis` - General questions and analysis

## Components

### 1. MCPClient (`mcp_client.py`)

Connects to the NBA MCP Server to gather context.

**Key Methods:**
- `connect(server_url)` - Connect to MCP server
- `call_tool(tool_name, params)` - Call an MCP tool
- `gather_context(query_type, user_input, code)` - Gather relevant context

**Helper Methods:**
- `_extract_table_names(text, source_type)` - Extract table names
- `_extract_file_references(text)` - Extract file paths
- `_extract_code_patterns(code)` - Extract functions/classes
- `_extract_error_info(text)` - Extract error information

### 2. Multi-Model Synthesis (`multi_model_synthesis.py`)

Main orchestration for multi-model synthesis.

**Main Function:**
```python
async def synthesize_with_mcp_context(
    user_input: str,
    selected_code: Optional[str] = None,
    query_type: Optional[str] = None,
    file_path: Optional[str] = None,
    mcp_server_url: str = "http://localhost:3000",
    enable_ollama_verification: bool = True,
    output_dir: Optional[str] = None
) -> Dict[str, Any]
```

**Helper Functions:**
- `detect_query_type(user_input, code)` - Auto-detect query type
- `summarize_context(context)` - Summarize MCP context for Claude
- `extract_code_from_response(response)` - Extract code blocks
- `format_final_output(...)` - Format results for saving
- `save_synthesis_result(...)` - Save to JSON/Markdown
- `quick_synthesis(prompt, code)` - Simplified API

## Usage Examples

### Basic Usage

```python
from synthesis import synthesize_with_mcp_context

result = await synthesize_with_mcp_context(
    user_input="Optimize this SQL query",
    selected_code="SELECT * FROM player_stats WHERE season = '2023-24'",
    query_type="sql_optimization"
)

print(f"Status: {result['status']}")
print(f"Solution: {result['final_code']}")
```

### Quick Synthesis

```python
from synthesis import quick_synthesis

solution = await quick_synthesis(
    prompt="Write a function to calculate win percentage"
)
print(solution)
```

### SQL Optimization

```python
result = await synthesize_with_mcp_context(
    user_input="Optimize this query for better performance",
    selected_code="""
        SELECT p.player_name, AVG(ps.points)
        FROM player_stats ps
        JOIN players p ON ps.player_id = p.id
        GROUP BY p.player_name
    """,
    query_type="sql_optimization"
)
```

### Statistical Analysis

```python
result = await synthesize_with_mcp_context(
    user_input="Calculate correlation between player height and PPG",
    query_type="statistical_analysis"
)
```

### ETL Generation

```python
result = await synthesize_with_mcp_context(
    user_input="Create ETL to transform raw game data to player_stats",
    query_type="etl_generation"
)
```

### Auto-Detect Query Type

```python
result = await synthesize_with_mcp_context(
    user_input="Fix this ZeroDivisionError in my win percentage function",
    selected_code=buggy_code
    # query_type auto-detected as 'debugging'
)
```

## Result Structure

```python
{
    "status": "success",
    "query_type": "sql_optimization",
    "user_input": "...",
    "selected_code": "...",

    "mcp_status": "connected",
    "mcp_context": {
        "schemas": {...},
        "table_stats": {...},
        "explain_plan": {...}
    },

    "deepseek_result": {
        "success": True,
        "response": "...",
        "tokens_used": 1500,
        "cost": 0.0004
    },

    "claude_synthesis": {
        "success": True,
        "response": "...",
        "tokens_used": 2000,
        "cost": 0.0350
    },

    "ollama_verification": {
        "success": True,
        "verification": "...",
        "cost": 0.0
    },

    "final_code": "...",
    "final_explanation": "...",
    "formatted_output": "...",

    "models_used": ["deepseek", "claude", "ollama"],
    "total_tokens": 3500,
    "total_cost": 0.0354,
    "execution_time_seconds": 5.2,

    "output_file": "/path/to/synthesis_output/synthesis_sql_optimization_20251008_123456.json"
}
```

## Synthesis Workflow

1. **Connect to MCP Server** - Establish connection to context source
2. **Auto-detect Query Type** (if not specified) - Analyze input for keywords
3. **Gather Context** - Retrieve relevant schemas, stats, files, etc.
4. **Query DeepSeek** - Primary analysis with low temperature (0.2)
5. **Synthesize with Claude** - Enhance and explain solution
6. **Verify with Ollama** (optional) - Local verification at no cost
7. **Save Results** - JSON and Markdown output files

## Configuration

Set these environment variables:

```bash
# Model API Keys
export DEEPSEEK_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# MCP Server
export MCP_SERVER_HOST="localhost"
export MCP_SERVER_PORT="3000"

# Output Directory
export SYNTHESIS_OUTPUT_DIR="/path/to/output"

# Ollama (optional)
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="qwen2.5-coder:32b"
```

## Cost Management

The system is designed for cost efficiency:

- **DeepSeek**: ~$0.14/1M input, $0.28/1M output (20x cheaper than GPT-4)
- **Claude**: Used for synthesis only (not raw analysis)
- **Ollama**: Local model, zero API costs

**Typical costs per query:**
- SQL Optimization: $0.01 - $0.05
- Statistical Analysis: $0.02 - $0.08
- ETL Generation: $0.03 - $0.10
- Code Debugging: $0.01 - $0.04

## Output Files

Results are saved to `synthesis_output/`:

```
synthesis_output/
├── synthesis_sql_optimization_20251008_120000.json    # Full result
├── synthesis_sql_optimization_20251008_120000.md      # Formatted output
├── synthesis_statistical_analysis_20251008_120100.json
└── synthesis_statistical_analysis_20251008_120100.md
```

## Error Handling

The system includes comprehensive error handling:

- MCP server unavailable → proceeds without context
- Ollama unavailable → skips verification step
- Model API failures → captured in result with status "partial_failure"
- All errors logged with full stack traces

## Running Examples

```bash
python synthesis/example_usage.py
```

This will run 6 example scenarios demonstrating all features.

## Integration with PyCharm

The synthesis system can be called from PyCharm via the external tool wrapper:

```python
# pycharm_integration/external_tool_wrapper.py
from synthesis import synthesize_with_mcp_context

result = await synthesize_with_mcp_context(
    user_input=user_request,
    selected_code=selected_text
)
```

## Advanced Usage

### Custom System Prompts

```python
from synthesis.models import DeepSeekModel

deepseek = DeepSeekModel(async_mode=True)
result = await deepseek.query(
    prompt="Optimize this query",
    context=mcp_context,
    temperature=0.2,
    system_prompt="You are a PostgreSQL expert focusing on NBA data"
)
```

### Context Filtering

```python
# Extract only source tables
from synthesis import extract_table_name

sources = extract_table_name(user_input, source_type="source")
targets = extract_table_name(user_input, source_type="target")
```

### Batch Processing

```python
queries = [
    "Optimize query 1",
    "Analyze this code",
    "Generate ETL pipeline"
]

results = []
for query in queries:
    result = await synthesize_with_mcp_context(user_input=query)
    results.append(result)
```

## Logging

Configure logging level:

```python
import logging

logging.basicConfig(
    level=logging.INFO,  # or DEBUG for verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Performance

- **Average execution time**: 3-8 seconds
- **Context gathering**: 0.5-2 seconds
- **DeepSeek query**: 1-3 seconds
- **Claude synthesis**: 1-3 seconds
- **Ollama verification**: 0.5-1 second (local)

## Limitations

1. MCP server must be running for context gathering
2. Requires API keys for DeepSeek and Claude
3. Ollama is optional but requires local installation
4. Max context size: 4000 tokens (configurable)
5. Output files can be large for complex queries

## Future Enhancements

- [ ] Streaming responses for real-time feedback
- [ ] Multi-language support (SQL, Python, Scala, etc.)
- [ ] Cost optimization strategies
- [ ] Response caching for similar queries
- [ ] Integration with more data sources
- [ ] A/B testing different model combinations

## Support

For issues or questions:
1. Check logs in `logs/mcp_synthesis.log`
2. Review example usage patterns
3. Verify environment variables are set
4. Ensure MCP server is running
