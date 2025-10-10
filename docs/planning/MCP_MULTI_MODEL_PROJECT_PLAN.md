# MCP-Enhanced Multi-Model Synthesis System - Project Plan

**Project Name:** NBA MCP Multi-Model Synthesis System  
**Goal:** Build an MCP server that enhances a multi-model AI synthesis system with real-time project context for the NBA Game Simulator & ML Platform  
**Target Environment:** PyCharm IDE integration  
**Build Tool:** Claude Code CLI

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Implementation Phases](#implementation-phases)
6. [Detailed Component Specifications](#detailed-component-specifications)
7. [Configuration](#configuration)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)
10. [Success Criteria](#success-criteria)

---

## Project Overview

### Context

This project combines two powerful systems:

1. **Multi-Model Synthesis System** (Already exists)
   - Queries 4+ AI models simultaneously (Claude, GPT-4o, Gemini, Ollama)
   - Synthesizes responses into superior unified answers
   - Integrates with PyCharm as external tool

2. **MCP Server** (To be built)
   - Provides real-time context from NBA project
   - Accesses RDS PostgreSQL database
   - Reads S3 data samples
   - Fetches project files
   - Queries AWS Glue metadata

### Goal

Create an MCP server that automatically gathers rich context from the NBA project and injects it into the multi-model synthesis workflow, resulting in more accurate, data-driven AI responses.

### Key Benefits

- **Context-Aware**: Models work with real NBA data, not assumptions
- **Automated**: No manual context gathering required
- **Actionable**: MCP can execute synthesized solutions
- **Intelligent**: Cross-system awareness for better decisions

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  PyCharm IDE                                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │  User selects code/writes prompt                   │    │
│  │  Triggers: External Tool                           │    │
│  └────────────────┬───────────────────────────────────┘    │
└─────────────────┬─┴───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Multi-Model Synthesis System (Enhanced)                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  1. MCP Context Gatherer (NEW)                     │    │
│  │     ├─ Connect to MCP Server                       │    │
│  │     ├─ Request relevant context                    │    │
│  │     └─ Structure context for models                │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ▼                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  2. Enhanced Model Queries (UPDATED)               │    │
│  │     ├─ Claude Sonnet 4 + MCP context               │    │
│  │     ├─ GPT-4o + MCP context                        │    │
│  │     ├─ Gemini 2.0 + MCP context                    │    │
│  │     └─ Ollama + MCP context                        │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ▼                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  3. Synthesis Engine (EXISTING)                    │    │
│  │     └─ Claude analyzes & synthesizes               │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ▼                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  4. MCP Action Executor (NEW)                      │    │
│  │     ├─ Save results to files                       │    │
│  │     ├─ Update database if applicable               │    │
│  │     ├─ Log synthesis metadata                      │    │
│  │     └─ Trigger Claude Code build (optional)        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  MCP Server (NEW - Core Component)                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  MCP Protocol Handler                              │    │
│  │  ├─ list_tools()                                   │    │
│  │  ├─ call_tool()                                    │    │
│  │  └─ get_prompt()                                   │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ▼                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Tool Implementations                              │    │
│  │  ├─ query_rds_database()                          │    │
│  │  ├─ fetch_s3_sample()                             │    │
│  │  ├─ get_glue_schema()                             │    │
│  │  ├─ read_project_file()                           │    │
│  │  ├─ search_git_history()                          │    │
│  │  ├─ save_to_project()                             │    │
│  │  └─ log_synthesis_result()                        │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   ▼                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Source Connectors                           │    │
│  │  ├─ RDS PostgreSQL Client                         │    │
│  │  ├─ S3 Boto3 Client                               │    │
│  │  ├─ AWS Glue Client                               │    │
│  │  ├─ File System Interface                         │    │
│  │  └─ Git Interface (optional)                      │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  NBA Project Infrastructure                                 │
│  ├─ RDS PostgreSQL (game data, player stats)               │
│  ├─ S3 Buckets (raw data lake, 146K JSON files)            │
│  ├─ AWS Glue (data catalog, schemas)                       │
│  └─ Local Project Files (/Users/ryanranft/nba-simulator-aws)│
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Example

**Scenario: User asks to optimize a database query**

1. **User Action**: Selects query code in PyCharm, runs synthesis tool
2. **MCP Context Gathering**: 
   - MCP queries RDS to get EXPLAIN plan
   - MCP fetches table schemas from Glue
   - MCP gets row counts and index info
   - MCP samples actual data from tables
3. **Enhanced Model Queries**:
   - All 4 models receive: original query + EXPLAIN plan + schema + data samples
   - Each model analyzes with REAL context
4. **Synthesis**: Claude combines 4 responses into optimal solution
5. **MCP Execution**: 
   - MCP saves optimized query to file
   - MCP logs the optimization in project metadata
   - (Optional) MCP creates index migration if needed

---

## Technology Stack

### MCP Server
- **Language**: Python 3.11
- **MCP SDK**: `mcp` Python package (Anthropic)
- **Database**: `psycopg2` for PostgreSQL
- **AWS**: `boto3` for S3 and Glue
- **Framework**: Async I/O with `asyncio`

### Multi-Model Synthesis (Existing + Updates)
- **Language**: Python 3.11
- **MCP Client**: `mcp` Python package
- **API Clients**: 
  - `anthropic` (Claude)
  - `openai` (GPT-4o)
  - `google-generativeai` (Gemini)
  - `ollama` (Local models)

### Infrastructure
- **Database**: AWS RDS PostgreSQL 15
- **Storage**: AWS S3
- **Catalog**: AWS Glue
- **IDE**: PyCharm (external tool integration)
- **Build**: Claude Code CLI

### Dependencies
```python
# requirements.txt
mcp>=0.9.0
anthropic>=0.8.0
openai>=1.0.0
google-generativeai>=0.3.0
ollama>=0.1.0
boto3>=1.34.0
psycopg2-binary>=2.9.0
asyncio>=3.4.3
pydantic>=2.0.0
python-dotenv>=1.0.0
```

---

## Project Structure

```
nba-mcp-synthesis/
├── README.md
├── PROJECT_PLAN.md                      # This file
├── requirements.txt
├── .env.example
├── .gitignore
│
├── mcp_server/                          # NEW: MCP Server
│   ├── __init__.py
│   ├── server.py                        # Main MCP server
│   ├── tools/                           # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── database_tools.py            # RDS queries
│   │   ├── s3_tools.py                  # S3 data fetching
│   │   ├── glue_tools.py                # Schema/catalog
│   │   ├── file_tools.py                # Project file access
│   │   └── action_tools.py              # Save/log/execute
│   ├── connectors/                      # Data source clients
│   │   ├── __init__.py
│   │   ├── rds_connector.py
│   │   ├── s3_connector.py
│   │   ├── glue_connector.py
│   │   └── file_connector.py
│   └── config/
│       ├── __init__.py
│       └── mcp_config.py                # MCP server configuration
│
├── synthesis/                           # UPDATED: Multi-Model System
│   ├── __init__.py
│   ├── multi_model_synthesis.py         # Main synthesis (UPDATED)
│   ├── mcp_client.py                    # NEW: MCP client integration
│   ├── models/                          # Model interfaces (EXISTING)
│   │   ├── __init__.py
│   │   ├── claude_model.py
│   │   ├── gpt_model.py
│   │   ├── gemini_model.py
│   │   └── ollama_model.py
│   ├── synthesizer.py                   # EXISTING: Response synthesis
│   └── config/
│       ├── __init__.py
│       └── synthesis_config.json        # UPDATED: Add MCP settings
│
├── pycharm_integration/                 # PyCharm external tool
│   ├── __init__.py
│   ├── external_tool_wrapper.py         # Entry point for PyCharm
│   └── input_handlers.py                # Process selected code/prompts
│
├── tests/                               # Comprehensive test suite
│   ├── __init__.py
│   ├── test_mcp_server.py
│   ├── test_mcp_tools.py
│   ├── test_synthesis_integration.py
│   ├── test_pycharm_integration.py
│   └── fixtures/
│       ├── sample_data.json
│       └── mock_responses.json
│
├── scripts/                             # Utility scripts
│   ├── setup_mcp_server.sh              # Install & configure MCP
│   ├── test_mcp_connection.py           # Verify MCP server
│   ├── quick_start.py                   # Demo the full system
│   └── install_pycharm_tool.py          # Configure PyCharm integration
│
├── docs/                                # Documentation
│   ├── SETUP_GUIDE.md
│   ├── MCP_TOOLS_REFERENCE.md
│   ├── SYNTHESIS_GUIDE.md
│   ├── PYCHARM_SETUP.md
│   └── TROUBLESHOOTING.md
│
└── examples/                            # Usage examples
    ├── optimize_query_example.py
    ├── generate_etl_code_example.py
    └── debug_with_context_example.py
```

---

## Implementation Phases

### Phase 1: MCP Server Foundation (Days 1-2)

**Goal**: Build working MCP server with basic NBA project connectivity

**Tasks**:
1. Set up project structure
2. Implement MCP protocol handler
3. Create RDS connector
4. Create S3 connector
5. Implement 2 basic tools:
   - `query_rds_database(sql_query)`
   - `fetch_s3_sample(file_path)`
6. Test MCP server standalone

**Deliverables**:
- Running MCP server
- Verified RDS connection
- Verified S3 connection
- Basic tool tests passing

**Success Criteria**:
- Can query RDS via MCP tool
- Can fetch S3 file via MCP tool
- MCP server responds to tool list requests

---

### Phase 2: Complete MCP Tool Suite (Days 3-4)

**Goal**: Implement all MCP tools for comprehensive NBA project access

**Tasks**:
1. Implement remaining read tools:
   - `get_glue_schema(table_name)`
   - `read_project_file(file_path)`
   - `get_table_statistics(table_name)`
   - `search_similar_games(team_id, date_range)`
2. Implement action tools:
   - `save_to_project(file_path, content)`
   - `log_synthesis_result(metadata)`
   - `execute_sql_safe(sql_query)` (read-only)
3. Add input validation for all tools
4. Add error handling and logging
5. Create tool documentation

**Deliverables**:
- 8-10 fully implemented MCP tools
- Comprehensive error handling
- Tool reference documentation
- Integration tests for each tool

**Success Criteria**:
- All tools work correctly
- Proper error messages
- Safe SQL execution (no DROP/DELETE)
- Tools handle edge cases

---

### Phase 3: MCP Client Integration (Days 5-6)

**Goal**: Integrate MCP client into existing multi-model synthesis system

**Tasks**:
1. Create MCP client wrapper (`mcp_client.py`)
2. Update `multi_model_synthesis.py`:
   - Add pre-query context gathering
   - Inject MCP context into model prompts
   - Add post-synthesis action execution
3. Update synthesis configuration:
   - Add MCP server connection settings
   - Add context gathering preferences
   - Add model-specific context formatting
4. Test MCP + synthesis integration

**Deliverables**:
- MCP client integrated into synthesis
- Updated configuration system
- Context injection working for all 4 models
- Integration tests passing

**Success Criteria**:
- Synthesis system can connect to MCP server
- Context is gathered before model queries
- All 4 models receive enriched prompts
- Actions execute after synthesis

---

### Phase 4: Enhanced Prompt Engineering (Day 7)

**Goal**: Optimize how MCP context is presented to each model

**Tasks**:
1. Design context templates for different query types:
   - Code optimization queries
   - ETL generation queries
   - Debugging queries
   - Analysis queries
2. Implement model-specific context formatting:
   - Claude prefers structured markdown
   - GPT-4o prefers JSON context
   - Gemini prefers conversational context
   - Ollama needs concise context
3. Add context relevance filtering
4. Implement token budget management

**Deliverables**:
- Context templates for 4 query types
- Model-specific formatters
- Smart context filtering
- Token budget system

**Success Criteria**:
- Each model receives optimally formatted context
- Context stays within token limits
- Relevant context is prioritized
- Irrelevant data is filtered out

---

### Phase 5: PyCharm Integration (Day 8)

**Goal**: Make the enhanced system accessible from PyCharm

**Tasks**:
1. Update external tool wrapper for PyCharm
2. Add input detection:
   - Selected code
   - Selected comments (as prompts)
   - PDF file paths
3. Add output formatting:
   - Syntax highlighting for code
   - Markdown formatting for explanations
   - Auto-save to appropriate file
4. Create PyCharm configuration guide
5. Test in PyCharm IDE

**Deliverables**:
- PyCharm external tool configuration
- Updated wrapper script
- Output formatting
- Setup guide for users

**Success Criteria**:
- Can trigger from PyCharm
- Selected code is captured
- Output opens in editor
- Formatted correctly

---

### Phase 6: Testing & Documentation (Days 9-10)

**Goal**: Comprehensive testing and complete documentation

**Tasks**:
1. Write unit tests for all components
2. Write integration tests for full workflow
3. Create end-to-end test scenarios
4. Write comprehensive documentation:
   - Setup guide
   - MCP tools reference
   - Synthesis guide
   - PyCharm setup
   - Troubleshooting guide
5. Create usage examples
6. Performance testing and optimization

**Deliverables**:
- 90%+ test coverage
- Complete documentation
- 5+ usage examples
- Performance benchmarks

**Success Criteria**:
- All tests pass
- Documentation is clear
- Examples work
- System performs well

---

### Phase 7: Production Hardening (Day 11-12)

**Goal**: Make system production-ready

**Tasks**:
1. Add comprehensive error handling
2. Implement retry logic for API calls
3. Add rate limiting for API calls
4. Implement caching for frequent queries
5. Add cost tracking for API usage
6. Create monitoring/logging system
7. Security review:
   - Credential management
   - SQL injection prevention
   - File access restrictions
8. Create deployment guide

**Deliverables**:
- Robust error handling
- Retry/rate limit logic
- Caching system
- Cost tracking
- Security hardening
- Deployment guide

**Success Criteria**:
- Handles failures gracefully
- API costs are tracked
- No security vulnerabilities
- Ready for production use

---

## Detailed Component Specifications

### Component 1: MCP Server (`mcp_server/server.py`)

**Purpose**: Central MCP server that exposes NBA project resources as tools

**Key Functions**:
```python
async def list_tools() -> List[Tool]:
    """Return list of available MCP tools"""
    
async def call_tool(name: str, arguments: dict) -> ToolResponse:
    """Execute requested tool with arguments"""
    
async def get_prompt(name: str, arguments: dict) -> str:
    """Get context-aware prompt template"""
```

**Configuration**:
```python
class MCPConfig:
    server_host: str = "localhost"
    server_port: int = 3000
    rds_host: str
    rds_database: str
    s3_bucket: str
    glue_database: str
    project_root: str
    max_query_size: int = 1000000  # bytes
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
```

**Error Handling**:
- Database connection failures
- S3 access errors
- Invalid tool arguments
- Resource not found
- Permission errors

---

### Component 2: MCP Tools (`mcp_server/tools/`)

#### Tool: `query_rds_database`
**Purpose**: Execute SQL queries on NBA database

**Input**:
```python
{
    "sql_query": "SELECT * FROM games WHERE game_date > '2024-01-01' LIMIT 10",
    "return_format": "json|csv|markdown",  # optional
    "max_rows": 100  # optional safety limit
}
```

**Output**:
```python
{
    "success": true,
    "rows": [...],
    "row_count": 10,
    "execution_time_ms": 45,
    "columns": ["game_id", "home_team", "away_team", ...],
    "formatted_result": "..."  # based on return_format
}
```

**Safety**:
- Read-only queries (SELECT, EXPLAIN)
- No DROP, DELETE, UPDATE, INSERT
- Row limit enforcement
- Query timeout (30s max)

---

#### Tool: `fetch_s3_sample`
**Purpose**: Get sample data from S3 bucket

**Input**:
```python
{
    "file_path": "box_scores/nba/401737902.json",
    "sample_size": 100,  # lines or bytes
    "sample_type": "lines|bytes|full"
}
```

**Output**:
```python
{
    "success": true,
    "file_path": "...",
    "sample_content": "...",
    "file_size": 856432,
    "file_type": "json",
    "last_modified": "2025-01-15T..."
}
```

---

#### Tool: `get_glue_schema`
**Purpose**: Retrieve table schema from AWS Glue catalog

**Input**:
```python
{
    "table_name": "player_game_stats",
    "include_partitions": false,
    "include_statistics": true
}
```

**Output**:
```python
{
    "success": true,
    "table_name": "player_game_stats",
    "columns": [
        {"name": "player_id", "type": "bigint", "nullable": false},
        {"name": "game_id", "type": "bigint", "nullable": false},
        ...
    ],
    "partition_keys": [...],
    "table_statistics": {
        "row_count": 1234567,
        "size_bytes": 45678901
    }
}
```

---

#### Tool: `read_project_file`
**Purpose**: Read files from NBA project directory

**Input**:
```python
{
    "file_path": "sql/create_tables.sql",
    "max_size": 100000  # safety limit in bytes
}
```

**Output**:
```python
{
    "success": true,
    "file_path": "...",
    "content": "...",
    "file_size": 12345,
    "file_type": "sql",
    "encoding": "utf-8"
}
```

**Safety**:
- Only files within project root
- Size limits enforced
- No binary file reading
- Path traversal prevention

---

#### Tool: `save_to_project`
**Purpose**: Save synthesized results to project

**Input**:
```python
{
    "file_path": "scripts/etl/optimized_query.sql",
    "content": "SELECT ...",
    "overwrite": false,
    "create_backup": true
}
```

**Output**:
```python
{
    "success": true,
    "file_path": "...",
    "backup_path": "...",  # if create_backup=true
    "bytes_written": 1234
}
```

---

#### Tool: `log_synthesis_result`
**Purpose**: Log metadata about synthesis operations

**Input**:
```python
{
    "operation": "query_optimization",
    "models_used": ["claude", "gpt4o", "gemini"],
    "context_sources": ["rds", "glue"],
    "execution_time": 12.5,
    "tokens_used": 8500,
    "result_quality_score": 0.95
}
```

**Output**:
```python
{
    "success": true,
    "log_id": "uuid-...",
    "timestamp": "2025-10-08T...",
    "log_file": "logs/synthesis_2025-10-08.json"
}
```

---

#### Tool: `get_table_statistics`
**Purpose**: Get comprehensive table statistics for optimization

**Input**:
```python
{
    "table_name": "player_game_stats",
    "include_indexes": true,
    "include_explain": true,
    "sample_query": "SELECT * FROM player_game_stats WHERE player_id = 123"
}
```

**Output**:
```python
{
    "success": true,
    "table_name": "player_game_stats",
    "row_count": 1234567,
    "table_size_mb": 450,
    "indexes": [
        {"name": "idx_player_id", "columns": ["player_id"], "size_mb": 12},
        ...
    ],
    "explain_plan": "...",  # if sample_query provided
    "most_expensive_queries": [...]  # from pg_stat_statements
}
```

---

### Component 3: MCP Client (`synthesis/mcp_client.py`)

**Purpose**: Client interface for synthesis system to communicate with MCP server

**Key Functions**:
```python
class MCPClient:
    async def connect(self, server_url: str):
        """Connect to MCP server"""
        
    async def gather_context(self, query_type: str, user_input: str) -> Dict:
        """Gather relevant context for query"""
        
    async def execute_action(self, action: str, params: dict) -> Dict:
        """Execute post-synthesis action"""
        
    async def call_tool(self, tool_name: str, arguments: dict) -> Dict:
        """Call specific MCP tool"""
```

**Context Gathering Logic**:
```python
async def gather_context(self, query_type: str, user_input: str):
    context = {}
    
    if query_type == "code_optimization":
        # Gather database schema
        context['schema'] = await self.call_tool("get_glue_schema", ...)
        # Gather table statistics
        context['stats'] = await self.call_tool("get_table_statistics", ...)
        # Get EXPLAIN plan if SQL query
        if self._is_sql_query(user_input):
            context['explain'] = await self.call_tool("query_rds_database", {
                "sql_query": f"EXPLAIN {user_input}"
            })
    
    elif query_type == "etl_generation":
        # Gather sample data
        context['sample_data'] = await self.call_tool("fetch_s3_sample", ...)
        # Get Glue catalog
        context['catalog'] = await self.call_tool("get_glue_schema", ...)
        
    elif query_type == "debugging":
        # Gather related files
        context['related_files'] = await self._find_related_files(user_input)
        # Get recent logs
        context['logs'] = await self.call_tool("read_project_file", {
            "file_path": "logs/etl.log"
        })
    
    return context
```

---

### Component 4: Enhanced Multi-Model Synthesis (`synthesis/multi_model_synthesis.py`)

**Updated Workflow**:
```python
async def synthesize_with_mcp_context(user_input: str, selected_code: str = None):
    """Main synthesis function with MCP enhancement"""
    
    # 1. Connect to MCP
    mcp_client = MCPClient()
    await mcp_client.connect(MCP_SERVER_URL)
    
    # 2. Detect query type
    query_type = detect_query_type(user_input, selected_code)
    
    # 3. Gather MCP context
    mcp_context = await mcp_client.gather_context(query_type, user_input)
    
    # 4. Build enhanced prompts for each model
    prompts = build_enhanced_prompts(
        user_input=user_input,
        selected_code=selected_code,
        mcp_context=mcp_context,
        query_type=query_type
    )
    
    # 5. Query all models in parallel with enhanced context
    responses = await query_all_models(prompts)
    
    # 6. Synthesize responses (existing logic)
    synthesized_result = synthesize_responses(responses)
    
    # 7. Execute post-synthesis actions via MCP
    if should_save_result(synthesized_result):
        await mcp_client.execute_action("save_to_project", {
            "file_path": determine_save_path(query_type),
            "content": synthesized_result['code'],
            "create_backup": True
        })
    
    # 8. Log synthesis metadata
    await mcp_client.execute_action("log_synthesis_result", {
        "operation": query_type,
        "models_used": ["claude", "gpt4o", "gemini", "ollama"],
        "context_sources": list(mcp_context.keys()),
        "execution_time": calculate_execution_time(),
        "tokens_used": calculate_total_tokens(responses)
    })
    
    return synthesized_result
```

**Enhanced Prompt Template**:
```python
def build_enhanced_prompt_for_claude(user_input, selected_code, mcp_context):
    return f"""
You are analyzing code with access to REAL project context.

# User Request
{user_input}

# Selected Code
```python
{selected_code}
```

# Real Project Context (from MCP)

## Database Schema
{format_schema(mcp_context.get('schema', {}))}

## Table Statistics
- Row count: {mcp_context.get('stats', {}).get('row_count', 'N/A')}
- Table size: {mcp_context.get('stats', {}).get('table_size_mb', 'N/A')} MB
- Indexes: {format_indexes(mcp_context.get('stats', {}).get('indexes', []))}

## Query Execution Plan
```
{mcp_context.get('explain', 'N/A')}
```

## Sample Data
```json
{json.dumps(mcp_context.get('sample_data', {}), indent=2)}
```

# Task
Analyze the code above using the REAL context provided and provide:
1. Issues/problems identified
2. Optimization recommendations
3. Improved code implementation

Be specific and reference the actual data/schema provided.
"""
```

---

### Component 5: Configuration System

#### MCP Server Config (`mcp_server/config/mcp_config.py`)
```python
from pydantic import BaseModel

class MCPServerConfig(BaseModel):
    # Server settings
    host: str = "localhost"
    port: int = 3000
    
    # NBA Project connections
    rds_host: str
    rds_port: int = 5432
    rds_database: str = "nba_simulator"
    rds_username: str
    rds_password: str
    
    s3_bucket: str = "nba-sim-raw-data-lake"
    s3_region: str = "us-east-1"
    
    glue_database: str = "nba_raw_data"
    glue_region: str = "us-east-1"
    
    project_root: str = "/Users/ryanranft/nba-simulator-aws"
    
    # Safety limits
    max_query_rows: int = 1000
    max_file_size_bytes: int = 1048576  # 1MB
    query_timeout_seconds: int = 30
    
    # Performance
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    
    # Security
    allowed_sql_keywords: list = ["SELECT", "EXPLAIN", "SHOW"]
    forbidden_sql_keywords: list = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE"]
    
    @classmethod
    def from_env(cls):
        """Load from environment variables"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        return cls(
            rds_host=os.getenv("RDS_HOST"),
            rds_username=os.getenv("RDS_USERNAME"),
            rds_password=os.getenv("RDS_PASSWORD"),
            # ... other env vars
        )
```

#### Synthesis Config (`synthesis/config/synthesis_config.json`)
```json
{
  "mcp_settings": {
    "enabled": true,
    "server_url": "http://localhost:3000",
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "context_gathering": {
      "auto_detect_query_type": true,
      "max_context_tokens": 4000,
      "cache_context": true
    }
  },
  
  "models": {
    "claude": {
      "enabled": true,
      "model": "claude-sonnet-4-20250514",
      "api_key_env": "ANTHROPIC_API_KEY",
      "max_tokens": 8000,
      "context_format": "markdown"
    },
    "gpt4o": {
      "enabled": true,
      "model": "gpt-4o",
      "api_key_env": "OPENAI_API_KEY",
      "max_tokens": 8000,
      "context_format": "json"
    },
    "gemini": {
      "enabled": true,
      "model": "gemini-2.0-flash-exp",
      "api_key_env": "GOOGLE_API_KEY",
      "max_tokens": 8000,
      "context_format": "conversational"
    },
    "ollama": {
      "enabled": true,
      "model": "llama3.1",
      "host": "http://localhost:11434",
      "max_tokens": 4000,
      "context_format": "concise"
    }
  },
  
  "synthesis": {
    "synthesizer_model": "claude",
    "include_individual_responses": false,
    "format_output": true,
    "auto_save_results": true,
    "save_path_template": "output/{query_type}/{timestamp}.md"
  },
  
  "query_type_detection": {
    "code_optimization": {
      "keywords": ["optimize", "faster", "performance", "slow"],
      "mcp_tools": ["get_table_statistics", "query_rds_database", "get_glue_schema"]
    },
    "etl_generation": {
      "keywords": ["etl", "extract", "transform", "load", "pipeline"],
      "mcp_tools": ["fetch_s3_sample", "get_glue_schema", "read_project_file"]
    },
    "debugging": {
      "keywords": ["bug", "error", "fix", "debug", "not working"],
      "mcp_tools": ["read_project_file", "query_rds_database"]
    },
    "analysis": {
      "keywords": ["analyze", "explain", "what", "how", "why"],
      "mcp_tools": ["query_rds_database", "fetch_s3_sample"]
    }
  }
}
```

---

### Component 6: PyCharm Integration (`pycharm_integration/external_tool_wrapper.py`)

**Entry Point Script**:
```python
#!/usr/bin/env python3
"""
PyCharm External Tool Wrapper
Entry point for multi-model synthesis with MCP context
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.multi_model_synthesis import synthesize_with_mcp_context
from synthesis.mcp_client import MCPClient

async def main():
    # Get input from PyCharm
    # PyCharm passes: $FilePath$ $SelectedText$ $Prompt$
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    selected_text = sys.argv[2] if len(sys.argv) > 2 else None
    prompt = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Determine input type
    if selected_text:
        user_input = prompt or "Analyze and improve this code"
        code = selected_text
    else:
        print("No code selected. Please select code in PyCharm and try again.")
        sys.exit(1)
    
    # Run synthesis with MCP context
    try:
        result = await synthesize_with_mcp_context(
            user_input=user_input,
            selected_code=code
        )
        
        # Format output
        output = format_for_pycharm(result)
        
        # Save to file
        output_file = save_output(output, file_path)
        
        # Open in PyCharm
        print(f"✅ Synthesis complete!")
        print(f"📄 Result saved to: {output_file}")
        print(f"\n{output}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def format_for_pycharm(result):
    """Format synthesis result for PyCharm display"""
    output = []
    output.append("# Multi-Model Synthesis Result (with MCP Context)\n")
    output.append(f"## Summary\n{result.get('summary', '')}\n")
    output.append(f"## Synthesized Solution\n```python\n{result.get('code', '')}\n```\n")
    output.append(f"## Explanation\n{result.get('explanation', '')}\n")
    
    if result.get('mcp_context_used'):
        output.append(f"## Context Sources Used\n")
        for source in result['mcp_context_used']:
            output.append(f"- {source}")
    
    return "\n".join(output)

def save_output(output, base_file_path):
    """Save output to timestamped file"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(base_file_path).parent / "synthesis_output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"synthesis_{timestamp}.md"
    output_file.write_text(output)
    
    return output_file

if __name__ == "__main__":
    asyncio.run(main())
```

**PyCharm External Tool Configuration**:
```xml
<!-- Add to PyCharm: Settings > Tools > External Tools -->
<tool>
  <name>Multi-Model Synthesis (MCP)</name>
  <description>Synthesize code using 4 AI models with NBA project context</description>
  <showInMainMenu>true</showInMainMenu>
  <showInEditor>true</showInEditor>
  <showInProject>false</showInProject>
  <showInSearchPopup>false</showInSearchPopup>
  <disabled>false</disabled>
  <useConsole>true</useConsole>
  <showConsoleOnStdOut>true</showConsoleOnStdOut>
  <showConsoleOnStdErr>true</showConsoleOnStdErr>
  <synchronizeAfterExecution>true</synchronizeAfterExecution>
  <exec>
    <program>/Users/ryanranft/miniconda3/envs/nba-aws/bin/python</program>
    <parameters>/path/to/nba-mcp-synthesis/pycharm_integration/external_tool_wrapper.py "$FilePath$" "$SelectedText$" "$Prompt$"</parameters>
    <workingDirectory>$ProjectFileDir$</workingDirectory>
  </exec>
</tool>
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# MCP Server
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3000

# AWS RDS PostgreSQL
RDS_HOST=nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com
RDS_PORT=5432
RDS_DATABASE=nba_simulator
RDS_USERNAME=postgres
RDS_PASSWORD=your_secure_password

# AWS S3
S3_BUCKET=nba-sim-raw-data-lake
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# AWS Glue
GLUE_DATABASE=nba_raw_data
GLUE_REGION=us-east-1

# NBA Project
PROJECT_ROOT=/Users/ryanranft/nba-simulator-aws

# API Keys for Models
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key

# Ollama (Local)
OLLAMA_HOST=http://localhost:11434

# Safety & Performance
MAX_QUERY_ROWS=1000
MAX_FILE_SIZE_MB=1
QUERY_TIMEOUT_SECONDS=30
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mcp_synthesis.log
```

---

## Testing Strategy

### Unit Tests

**MCP Server Tests** (`tests/test_mcp_server.py`)
```python
import pytest
from mcp_server.server import MCPServer

@pytest.mark.asyncio
async def test_list_tools():
    server = MCPServer()
    tools = await server.list_tools()
    assert len(tools) >= 8
    assert any(t.name == "query_rds_database" for t in tools)

@pytest.mark.asyncio
async def test_query_rds_database_tool():
    server = MCPServer()
    result = await server.call_tool("query_rds_database", {
        "sql_query": "SELECT COUNT(*) FROM games"
    })
    assert result["success"] is True
    assert "row_count" in result

@pytest.mark.asyncio
async def test_forbidden_sql_keywords():
    server = MCPServer()
    with pytest.raises(ValueError, match="Forbidden SQL keyword"):
        await server.call_tool("query_rds_database", {
            "sql_query": "DROP TABLE games"
        })
```

**MCP Client Tests** (`tests/test_mcp_client.py`)
```python
@pytest.mark.asyncio
async def test_gather_context_for_optimization():
    client = MCPClient()
    await client.connect("http://localhost:3000")
    
    context = await client.gather_context(
        query_type="code_optimization",
        user_input="SELECT * FROM player_game_stats"
    )
    
    assert "schema" in context
    assert "stats" in context
    assert context["stats"]["row_count"] > 0
```

### Integration Tests

**Full Synthesis Test** (`tests/test_synthesis_integration.py`)
```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_synthesis_with_mcp():
    """Test complete synthesis workflow with MCP context"""
    
    user_input = "Optimize this query"
    code = "SELECT * FROM player_game_stats WHERE player_id = 123"
    
    result = await synthesize_with_mcp_context(user_input, code)
    
    # Verify MCP context was used
    assert "mcp_context_used" in result
    assert len(result["mcp_context_used"]) > 0
    
    # Verify all models responded
    assert "claude_response" in result
    assert "gpt4o_response" in result
    assert "gemini_response" in result
    assert "ollama_response" in result
    
    # Verify synthesis occurred
    assert "synthesized_solution" in result
    assert len(result["synthesized_solution"]) > 0
```

### End-to-End Tests

**PyCharm Integration Test**
```python
def test_pycharm_integration():
    """Test external tool wrapper"""
    
    # Simulate PyCharm call
    result = subprocess.run([
        "python",
        "pycharm_integration/external_tool_wrapper.py",
        "test_file.py",
        "SELECT * FROM games",
        "Optimize this query"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "✅ Synthesis complete" in result.stdout
    assert "synthesis_output" in result.stdout
```

### Performance Tests

```python
@pytest.mark.performance
async def test_synthesis_performance():
    """Ensure synthesis completes within acceptable time"""
    
    import time
    start = time.time()
    
    result = await synthesize_with_mcp_context(
        "Optimize this code",
        "SELECT * FROM games LIMIT 100"
    )
    
    duration = time.time() - start
    
    # Should complete within 30 seconds
    assert duration < 30
    
    # Log performance metrics
    print(f"Synthesis completed in {duration:.2f} seconds")
```

---

## Deployment

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/your-username/nba-mcp-synthesis.git
cd nba-mcp-synthesis

# 2. Create virtual environment
conda create -n mcp-synthesis python=3.11
conda activate mcp-synthesis

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Start MCP server
python -m mcp_server.server

# 6. Test MCP server
python scripts/test_mcp_connection.py

# 7. Run quick start demo
python scripts/quick_start.py

# 8. Configure PyCharm
python scripts/install_pycharm_tool.py
```

### Production Deployment

**Option 1: Run MCP Server Locally**
- Keep MCP server running on development machine
- Access RDS/S3 via AWS credentials
- PyCharm connects to localhost MCP server

**Option 2: Deploy MCP Server to EC2**
- Deploy MCP server to EC2 instance (same as simulation engine)
- Reduces latency to RDS/S3
- PyCharm connects to remote MCP server

**Recommended**: Option 1 for development, Option 2 for production

---

## Success Criteria

### Functional Requirements
- [ ] MCP server successfully connects to RDS, S3, and Glue
- [ ] All 8+ MCP tools work correctly
- [ ] MCP client integrates with synthesis system
- [ ] All 4 models receive enriched context
- [ ] Synthesis produces superior results with MCP context
- [ ] PyCharm integration works seamlessly
- [ ] Results auto-save to project files

### Quality Requirements
- [ ] 90%+ test coverage
- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] Proper error handling
- [ ] Comprehensive documentation

### Performance Requirements
- [ ] Synthesis completes in <30 seconds
- [ ] MCP context gathering in <5 seconds
- [ ] Database queries in <2 seconds
- [ ] S3 fetches in <3 seconds

### User Experience Requirements
- [ ] One-click operation from PyCharm
- [ ] Clear error messages
- [ ] Formatted output
- [ ] Auto-save functionality

---

## Example Use Cases

### Use Case 1: Query Optimization

**User Action**: Selects slow SQL query in PyCharm, runs synthesis tool

**MCP Context Gathered**:
- EXPLAIN plan from RDS
- Table schema from Glue
- Index information
- Row counts and table sizes

**Model Responses**:
- **Claude**: Suggests adding composite index, rewriting subquery
- **GPT-4o**: Recommends query restructuring, different JOIN order
- **Gemini**: Identifies missing WHERE clause optimization
- **Ollama**: Suggests using materialized view

**Synthesized Result**:
```sql
-- Optimized query (synthesized from all models)
-- Added composite index: CREATE INDEX idx_player_game ON player_game_stats(player_id, game_id)
-- Restructured query to use indexed columns first
-- Eliminated unnecessary subquery

SELECT 
    pgs.player_id,
    pgs.game_id,
    pgs.points,
    pgs.rebounds,
    pgs.assists
FROM player_game_stats pgs
INNER JOIN games g ON pgs.game_id = g.game_id
WHERE pgs.player_id = 123
    AND g.game_date >= '2024-01-01'
ORDER BY g.game_date DESC
LIMIT 50;

-- Performance: 0.05s (down from 2.3s)
-- Uses index: idx_player_game
```

**MCP Actions**:
- Saves optimized query to `sql/optimized/player_stats_query.sql`
- Logs optimization metadata
- (Optional) Creates index migration file

---

### Use Case 2: ETL Code Generation

**User Action**: Writes comment "Generate ETL to load box scores from S3 to RDS", runs tool

**MCP Context Gathered**:
- Sample box score JSON from S3
- Target table schema from Glue
- Existing ETL scripts from project

**Model Responses**:
- **Claude**: Complete AWS Glue PySpark ETL script
- **GPT-4o**: Python boto3 + pandas approach
- **Gemini**: Batch processing with error handling
- **Ollama**: Simple incremental load logic

**Synthesized Result**:
Complete ETL script combining best practices from all 4 models, with:
- Schema validation
- Error handling
- Incremental loading
- Data quality checks
- Logging

**MCP Actions**:
- Saves ETL script to `scripts/etl/load_box_scores.py`
- Logs generation metadata

---

### Use Case 3: Debugging with Context

**User Action**: Selects failing code, asks "Why is this ETL job failing?"

**MCP Context Gathered**:
- Recent error logs
- Sample problematic data from S3
- Database schema
- Related ETL scripts

**Model Responses**:
- **Claude**: Identifies schema mismatch
- **GPT-4o**: Points out data type conversion issue
- **Gemini**: Finds missing null handling
- **Ollama**: Suggests retry logic

**Synthesized Result**:
Root cause analysis + fixed code addressing all issues

**MCP Actions**:
- Saves fixed code
- Logs debugging session

---

## Next Steps for Claude Code

This plan is ready for Claude Code to implement. Recommended approach:

1. **Create new repository**: `nba-mcp-synthesis`
2. **Add this plan**: Save as `PROJECT_PLAN.md`
3. **Run Claude Code**: `claude-code "Implement the MCP-Enhanced Multi-Model Synthesis System according to PROJECT_PLAN.md"`

Claude Code will:
- Read this complete specification
- Implement all phases sequentially
- Create all files and components
- Write tests
- Generate documentation
- Ask clarifying questions as needed

**Estimated Build Time with Claude Code**: 6-12 hours of autonomous development

---

## Appendix: Additional Resources

### References
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Anthropic MCP Python SDK](https://github.com/anthropics/anthropic-mcp-python)
- [AWS Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [PyCharm External Tools Guide](https://www.jetbrains.com/help/pycharm/configuring-third-party-tools.html)

### Related NBA Project Docs
- NBA Game Simulator Setup Progress Log
- AWS Architecture Documentation
- RDS Schema Documentation
- S3 Data Structure Guide

---

**End of Project Plan**

Ready for Claude Code implementation! 🚀
