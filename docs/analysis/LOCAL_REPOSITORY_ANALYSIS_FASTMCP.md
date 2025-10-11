# Local Repository Analysis: FastMCP Framework & Patterns

**Date:** October 10, 2025
**Analysis Source:** Local repositories at /Users/ryanranft/modelcontextprotocol
**Status:** ✅ Complete

---

## Executive Summary

**Key Discovery:** The official Python MCP SDK includes **FastMCP**, a high-level, decorator-based framework that dramatically simplifies MCP server development compared to the low-level Server API currently used in the NBA MCP implementation.

**Impact Assessment:**
- **Code Reduction:** 50-70% less boilerplate code
- **Maintainability:** Significantly improved with declarative decorators
- **Type Safety:** Better with Pydantic integration
- **Context Management:** Elegant dependency injection pattern
- **Migration Effort:** Medium (2-4 days for NBA MCP server)

**Recommendation:** Migrate NBA MCP server to FastMCP framework to improve maintainability and reduce code complexity.

---

## Table of Contents

1. [FastMCP Framework Overview](#fastmcp-framework-overview)
2. [Key Patterns from FastMCP](#key-patterns-from-fastmcp)
3. [Reference Server Analysis](#reference-server-analysis)
4. [Comparison: Low-Level vs FastMCP](#comparison-low-level-vs-fastmcp)
5. [Migration Plan for NBA MCP](#migration-plan-for-nba-mcp)
6. [Benefits & Trade-offs](#benefits--trade-offs)
7. [Code Examples](#code-examples)

---

## FastMCP Framework Overview

### What is FastMCP?

FastMCP is an ergonomic, high-level interface for building MCP servers, similar to how FastAPI simplifies web API development. It's part of the official MCP Python SDK.

**Location:** `mcp.server.fastmcp`

**Philosophy:**
- Decorator-based API (inspired by FastAPI)
- Type-driven development with Pydantic
- Dependency injection for context
- Automatic schema generation
- Convention over configuration

### Core Components

```python
from mcp.server.fastmcp import FastMCP, Context

# 1. Create server
mcp = FastMCP("server-name")

# 2. Add tools with decorators
@mcp.tool()
async def my_tool(param: str, ctx: Context) -> str:
    await ctx.info(f"Processing {param}")
    return f"Result: {param}"

# 3. Run server
mcp.run()  # Defaults to stdio transport
```

---

## Key Patterns from FastMCP

### 1. Decorator-Based Registration

**Pattern:** Use decorators to register tools, resources, and prompts

**Benefits:**
- Self-documenting code
- Automatic schema generation from type hints
- Less boilerplate

**Example:**
```python
@mcp.tool()
def query_database(
    sql: str,
    limit: int = 100
) -> QueryResult:
    """Execute a SQL query against the database.

    Args:
        sql: SQL query to execute
        limit: Maximum number of results to return
    """
    # Function docstring becomes tool description
    # Type hints become JSON schema
    # Pydantic models for structured output
    pass
```

**Current NBA MCP Approach:**
```python
# Manual registration with extensive boilerplate
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_database":
        # Manual argument extraction
        sql = arguments.get("sql")
        limit = arguments.get("limit", 100)
        # Manual validation
        # Manual response formatting
```

---

### 2. Context Injection

**Pattern:** Request `Context` parameter for access to MCP capabilities

**Benefits:**
- Clean dependency injection
- Only available when needed
- Type-safe access to capabilities

**Context Capabilities:**
- `ctx.info()` / `ctx.debug()` / `ctx.warning()` / `ctx.error()` - Logging
- `ctx.report_progress()` - Progress updates
- `ctx.read_resource()` - Resource access
- `ctx.elicit()` - Interactive user input
- `ctx.request_id` - Request tracking
- `ctx.client_id` - Client identification
- `ctx.session` - Advanced session access

**Example:**
```python
@mcp.tool()
async def long_running_task(
    steps: int,
    ctx: Context  # ← Injected automatically
) -> str:
    await ctx.info("Starting task")

    for i in range(steps):
        progress = (i + 1) / steps
        await ctx.report_progress(
            progress=progress,
            total=1.0,
            message=f"Step {i+1}/{steps}"
        )

    await ctx.info("Task complete")
    return "Done"
```

**Detection Pattern:**
```python
# FastMCP automatically detects Context parameter by type annotation
# Name can be anything: ctx, context, c, etc.
def find_context_parameter(fn) -> str | None:
    sig = inspect.signature(fn)
    for name, param in sig.parameters.items():
        if param.annotation == Context:
            return name
    return None
```

---

### 3. Settings-Based Configuration

**Pattern:** Use Pydantic BaseSettings with environment variable support

**Benefits:**
- Environment variable support (FASTMCP_ prefix)
- .env file support
- Type validation
- Centralized configuration

**Implementation:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FASTMCP_",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Server settings
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # HTTP settings
    host: str = "127.0.0.1"
    port: int = 8000

    # Database settings (custom)
    db_path: str = "./nba.db"
    max_connections: int = 5
```

**Usage:**
```bash
# Set via environment variables
export FASTMCP_DEBUG=true
export FASTMCP_DB_PATH=/path/to/nba.db
export FASTMCP_LOG_LEVEL=DEBUG

# Or via .env file
echo "FASTMCP_DEBUG=true" > .env
```

**NBA MCP Application:**
```python
class NBASettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NBA_MCP_",
        env_file=".env",
    )

    # Database
    db_path: str = "./nba_data.db"
    db_pool_size: int = 5
    db_timeout: float = 30.0

    # S3
    s3_bucket: str = "nba-mcp-data"
    s3_region: str = "us-east-1"

    # Server
    debug: bool = False
    log_level: str = "INFO"
    max_concurrent_requests: int = 10
```

---

### 4. Structured Output Support

**Pattern:** Return Pydantic models for automatic JSON schema generation

**Benefits:**
- Automatic validation
- Type safety
- Self-documenting
- Consistent response format

**Example:**
```python
from pydantic import BaseModel

class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: float

@mcp.tool()
async def query_database(sql: str) -> QueryResult:
    """Query returns structured data automatically."""
    start = time.time()
    rows = execute_query(sql)

    return QueryResult(
        columns=get_columns(sql),
        rows=rows,
        row_count=len(rows),
        execution_time_ms=(time.time() - start) * 1000
    )
```

**FastMCP automatically:**
1. Generates JSON schema from QueryResult
2. Validates return value
3. Converts to MCP TextContent
4. Handles serialization

---

### 5. Manager Pattern

**Pattern:** Separate managers for different concerns

**Benefits:**
- Separation of concerns
- Easier testing
- Clear responsibilities

**FastMCP Implementation:**
```python
class FastMCP:
    def __init__(self):
        self._tool_manager = ToolManager(
            tools=tools,
            warn_on_duplicate_tools=True
        )
        self._resource_manager = ResourceManager(
            warn_on_duplicate_resources=True
        )
        self._prompt_manager = PromptManager(
            warn_on_duplicate_prompts=True
        )
```

**Each Manager Provides:**
- `add_*()` - Add item
- `remove_*()` - Remove item
- `list_*()` - List items
- `get_*()` - Get specific item
- Duplicate detection
- Validation

**NBA MCP Application:**
```python
# Create separate managers for different concerns
class DatabaseToolManager:
    def add_tool(self, name, fn):
        # Add database-specific tool
        pass

class S3ResourceManager:
    def add_resource(self, uri, fn):
        # Add S3-specific resource
        pass

# Use in FastMCP
mcp = FastMCP("nba-mcp")
db_manager = DatabaseToolManager(mcp)
s3_manager = S3ResourceManager(mcp)
```

---

### 6. Lifespan Management

**Pattern:** Use async context manager for startup/shutdown

**Benefits:**
- Clean resource initialization
- Guaranteed cleanup
- Shared state across requests

**Example:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastMCP):
    # Startup: Initialize shared resources
    db_pool = await create_db_pool()
    redis_client = await create_redis_client()

    # Store in lifespan context (accessible in tools)
    context = {
        "db_pool": db_pool,
        "redis": redis_client
    }

    try:
        yield context  # Server runs with these resources
    finally:
        # Shutdown: Clean up resources
        await db_pool.close()
        await redis_client.close()

# Create server with lifespan
mcp = FastMCP("nba-mcp", lifespan=lifespan)

# Access lifespan context in tools
@mcp.tool()
async def query_database(sql: str, ctx: Context) -> QueryResult:
    # Access shared resources from lifespan
    db_pool = ctx.request_context.lifespan_context["db_pool"]
    async with db_pool.connection() as conn:
        return await conn.execute(sql)
```

**NBA MCP Application:**
```python
@asynccontextmanager
async def nba_lifespan(app: FastMCP):
    # Initialize database connection pool
    db_pool = await asyncpg.create_pool(
        database="nba_data.db",
        min_size=2,
        max_size=10
    )

    # Initialize S3 client
    s3_client = aioboto3.Session().client('s3')

    # Initialize cache
    cache = await aioredis.create_redis_pool('redis://localhost')

    context = {
        "db_pool": db_pool,
        "s3_client": s3_client,
        "cache": cache
    }

    try:
        yield context
    finally:
        await db_pool.close()
        await s3_client.close()
        cache.close()
        await cache.wait_closed()
```

---

### 7. Multiple Transport Support

**Pattern:** Easy switching between transport protocols

**Benefits:**
- Flexible deployment
- Development vs production
- Client compatibility

**Transports:**
1. **stdio** - Standard input/output (default, Claude Desktop)
2. **SSE** - Server-Sent Events (HTTP streaming)
3. **streamable-http** - HTTP-based with session management

**Example:**
```python
mcp = FastMCP("nba-mcp")

# Development: stdio
mcp.run(transport="stdio")

# Production: SSE with HTTP
mcp.run(transport="sse", mount_path="/nba")

# Production: Streamable HTTP
mcp.run(transport="streamable-http")

# Custom: Get ASGI app for FastAPI integration
app = FastAPI()
app.mount("/mcp", mcp.streamable_http_app())
```

---

### 8. Dynamic Resource Templates

**Pattern:** URI templates for parameterized resources

**Benefits:**
- Dynamic resource generation
- RESTful URI patterns
- Parameter validation

**Example:**
```python
@mcp.resource("player://{player_id}/stats")
async def get_player_stats(player_id: str) -> dict:
    """Get stats for a specific player.

    URI params automatically extracted and validated.
    """
    return query_player_stats(player_id)

@mcp.resource("game://{game_id}/boxscore")
async def get_game_boxscore(game_id: str, ctx: Context) -> dict:
    """Get boxscore for a specific game."""
    await ctx.info(f"Fetching boxscore for game {game_id}")
    return query_game_boxscore(game_id)
```

**FastMCP automatically:**
- Extracts parameters from URI pattern
- Validates they match function parameters
- Registers as resource template
- Handles parameter substitution

---

## Reference Server Analysis

### Time Server (Low-Level API)

**Location:** `/Users/ryanranft/modelcontextprotocol/servers/src/time/`

**Observations:**
- Uses low-level `Server` class (not FastMCP)
- Manual tool registration with `@server.list_tools()` and `@server.call_tool()`
- Manual schema definition as dictionaries
- Manual argument extraction and validation
- Pydantic models for structured data (TimeResult, TimeConversionResult)
- Clean separation of business logic (TimeServer class)

**Code Pattern:**
```python
server = Server("mcp-time")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_current_time",
            description="Get current time in a specific timezone",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "..."}
                },
                "required": ["timezone"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    match name:
        case "get_current_time":
            timezone = arguments.get("timezone")
            result = time_server.get_current_time(timezone)
            return [TextContent(type="text", text=json.dumps(result.model_dump()))]
```

**Lessons:**
- Manual schema definition is verbose and error-prone
- Separation of server logic from business logic is good
- Match/case pattern for tool routing is clean but doesn't scale

---

### Fetch Server (Low-Level API)

**Location:** `/Users/ryanranft/modelcontextprotocol/servers/src/fetch/`

**Observations:**
- Also uses low-level Server API
- Pydantic model for input validation (Fetch model)
- Implements both tools AND prompts
- Custom error handling with McpError
- Robots.txt checking for autonomous fetching
- Content preprocessing (HTML to Markdown)

**Key Patterns:**
```python
class Fetch(BaseModel):
    """Parameters for fetching a URL."""
    url: Annotated[AnyUrl, Field(description="URL to fetch")]
    max_length: Annotated[int, Field(default=5000, gt=0, lt=1000000)]
    start_index: Annotated[int, Field(default=0, ge=0)]
    raw: Annotated[bool, Field(default=False)]

@server.call_tool()
async def call_tool(name, arguments: dict) -> list[TextContent]:
    try:
        args = Fetch(**arguments)  # ← Pydantic validation
    except ValueError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))

    # Use validated args
    content, prefix = await fetch_url(str(args.url), ...)
```

**Lessons:**
- Pydantic for input validation is essential
- Content preprocessing before sending to LLM (HTML → Markdown)
- Chunking large content with continuation pattern
- Different user agents for autonomous vs manual fetch
- Comprehensive error handling with specific error codes

---

## Comparison: Low-Level vs FastMCP

### Tool Definition

#### Low-Level API (Current NBA MCP)
```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_database",
            description="Execute a SQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results",
                        "default": 100
                    }
                },
                "required": ["sql"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_database":
        # Manual extraction
        sql = arguments.get("sql")
        limit = arguments.get("limit", 100)

        # Validate
        if not sql:
            return [TextContent(type="text", text="Error: SQL required")]

        # Execute
        result = execute_query(sql, limit)

        # Format response
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
```

**Lines of code: ~40**

#### FastMCP API
```python
class QueryParams(BaseModel):
    sql: str = Field(description="SQL query to execute")
    limit: int = Field(default=100, description="Max results")

@mcp.tool()
async def query_database(params: QueryParams, ctx: Context) -> dict:
    """Execute a SQL query."""
    await ctx.debug(f"Executing: {params.sql[:50]}...")
    result = execute_query(params.sql, params.limit)
    return result
```

**Lines of code: ~10 (75% reduction)**

**Improvements:**
- ✅ Automatic schema generation from Pydantic model
- ✅ Automatic validation
- ✅ Type safety
- ✅ Context injection
- ✅ Structured output
- ✅ Less boilerplate

---

### Resource Definition

#### Low-Level API
```python
@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="s3://bucket/file.json",
            name="NBA Data",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
    if str(uri).startswith("s3://"):
        content = await s3_client.get_object(...)
        return [ReadResourceContents(
            uri=uri,
            mimeType="application/json",
            text=content
        )]
```

**Lines of code: ~25**

#### FastMCP API
```python
@mcp.resource("s3://{bucket}/{key}")
async def get_s3_object(bucket: str, key: str, ctx: Context) -> str:
    """Fetch object from S3."""
    await ctx.info(f"Fetching s3://{bucket}/{key}")
    return await s3_client.get_object(Bucket=bucket, Key=key)
```

**Lines of code: ~5 (80% reduction)**

**Improvements:**
- ✅ URI template with parameter extraction
- ✅ Automatic MIME type detection
- ✅ Simpler implementation
- ✅ Context injection

---

### Complete Server Comparison

#### Low-Level Server
```python
# server.py (200+ lines)
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent

server = Server("nba-mcp")

# Global state management
db_connection = None

async def init_db():
    global db_connection
    db_connection = await create_connection()

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [...]  # 50+ lines of schema definitions

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    # 100+ lines of routing and logic
    if name == "tool1":
        ...
    elif name == "tool2":
        ...
    # etc.

@server.list_resources()
async def list_resources() -> list[Resource]:
    return [...]  # 30+ lines

@server.read_resource()
async def read_resource(uri: AnyUrl):
    # 40+ lines of URI parsing and routing
    pass

async def main():
    await init_db()
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, options)
    finally:
        await db_connection.close()
```

**Total: ~200+ lines**

#### FastMCP Server
```python
# server.py (50-70 lines)
from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastMCP):
    db = await create_connection()
    yield {"db": db}
    await db.close()

mcp = FastMCP("nba-mcp", lifespan=lifespan)

@mcp.tool()
async def tool1(param: str, ctx: Context) -> dict:
    """Tool 1 description."""
    db = ctx.request_context.lifespan_context["db"]
    return await db.query(param)

@mcp.tool()
async def tool2(param: str, ctx: Context) -> dict:
    """Tool 2 description."""
    return {"result": param}

@mcp.resource("data://{id}")
async def get_data(id: str) -> dict:
    """Get data by ID."""
    return {"id": id, "data": "..."}

if __name__ == "__main__":
    mcp.run()
```

**Total: ~50-70 lines (65-75% reduction)**

---

## Migration Plan for NBA MCP

### Phase 1: Preparation (1 day)

**Goal:** Set up FastMCP infrastructure without breaking existing code

**Tasks:**
1. Install latest MCP SDK with FastMCP support
   ```bash
   pip install --upgrade mcp
   ```

2. Create new settings module
   ```python
   # mcp_server/settings.py
   from pydantic_settings import BaseSettings

   class NBASettings(BaseSettings):
       model_config = SettingsConfigDict(
           env_prefix="NBA_MCP_",
           env_file=".env",
       )

       # Database
       db_path: str = "./nba_data.db"
       db_pool_size: int = 5

       # S3
       s3_bucket: str
       s3_region: str = "us-east-1"

       # Server
       debug: bool = False
       log_level: str = "INFO"
   ```

3. Create lifespan manager
   ```python
   # mcp_server/lifespan.py
   from contextlib import asynccontextmanager

   @asynccontextmanager
   async def nba_lifespan(app: FastMCP):
       # Initialize resources
       db_pool = await create_db_pool()
       s3_client = boto3.client('s3')

       context = {
           "db_pool": db_pool,
           "s3_client": s3_client
       }

       yield context

       # Cleanup
       await db_pool.close()
   ```

4. Create test FastMCP server (parallel to existing)
   ```python
   # mcp_server/fastmcp_server.py (new file, doesn't touch existing code)
   from mcp.server.fastmcp import FastMCP
   from .lifespan import nba_lifespan

   mcp = FastMCP("nba-mcp", lifespan=nba_lifespan)

   # Migrate one tool as proof of concept
   @mcp.tool()
   async def list_tables(ctx: Context) -> list[str]:
       """List all database tables."""
       db = ctx.request_context.lifespan_context["db_pool"]
       return await db.fetch("SELECT name FROM sqlite_master WHERE type='table'")
   ```

**Validation:**
- Run both old and new servers
- Verify new server works with Claude Desktop
- Compare responses

---

### Phase 2: Migrate Database Tools (1 day)

**Goal:** Convert all database tools to FastMCP

**Current Tools to Migrate:**
1. `query_database`
2. `list_tables`
3. `get_table_schema`

**Migration Pattern:**
```python
# Before (old server.py)
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_database":
        sql = arguments.get("sql")
        # ... 30 lines of validation and execution
        return [TextContent(...)]

# After (fastmcp_server.py)
@mcp.tool()
async def query_database(
    params: QueryDatabaseParams,  # ← Already have Pydantic model
    ctx: Context
) -> QueryResult:
    """Execute a SQL query against the NBA database."""
    db = ctx.request_context.lifespan_context["db_pool"]
    await ctx.debug(f"Executing query: {params.sql[:50]}...")

    # Reuse existing execute_query function
    result = await execute_query(db, params)

    await ctx.info(f"Query returned {result.row_count} rows")
    return result
```

**Reuse Existing:**
- ✅ Pydantic models from `mcp_server/tools/params.py`
- ✅ Business logic functions
- ✅ Response models from `mcp_server/responses.py`

**Changes Required:**
- ❌ Remove manual schema definitions
- ❌ Remove manual argument extraction
- ❌ Remove manual TextContent wrapping
- ✅ Add Context parameters where logging needed
- ✅ Update to use lifespan context for DB access

**Estimated Lines Changed:**
- Old: ~150 lines (tool definitions + routing)
- New: ~60 lines (decorators + logic)
- Reduction: 60%

---

### Phase 3: Migrate S3 Resources (0.5 days)

**Goal:** Convert S3 file access to resource templates

**Current Implementation:**
- Manual resource listing
- Manual URI parsing
- Manual S3 client usage

**New Implementation:**
```python
@mcp.resource("s3://nba-data/{key}")
async def get_s3_file(key: str, ctx: Context) -> str:
    """Fetch file from S3 bucket."""
    s3 = ctx.request_context.lifespan_context["s3_client"]

    await ctx.info(f"Fetching s3://nba-data/{key}")

    response = s3.get_object(Bucket="nba-data", Key=key)
    content = response['Body'].read().decode('utf-8')

    await ctx.debug(f"Retrieved {len(content)} bytes")
    return content

@mcp.resource("s3://nba-data/{prefix}/list")
async def list_s3_files(prefix: str = "") -> list[str]:
    """List files in S3 with optional prefix."""
    s3 = ctx.request_context.lifespan_context["s3_client"]

    response = s3.list_objects_v2(
        Bucket="nba-data",
        Prefix=prefix
    )

    return [obj['Key'] for obj in response.get('Contents', [])]
```

**Benefits:**
- URI templates provide RESTful interface
- Automatic parameter extraction
- Cleaner than manual URI parsing

---

### Phase 4: Testing & Validation (0.5 days)

**Goal:** Ensure feature parity and improve quality

**Test Plan:**

1. **Unit Tests**
   ```python
   # tests/test_fastmcp_tools.py
   import pytest
   from mcp_server.fastmcp_server import mcp

   @pytest.mark.asyncio
   async def test_query_database():
       result = await mcp._tool_manager.call_tool(
           "query_database",
           {"sql": "SELECT * FROM players LIMIT 5"}
       )
       assert result.row_count == 5
   ```

2. **Integration Tests**
   - Test with Claude Desktop
   - Verify all Quick Wins still work
   - Test error handling
   - Test progress reporting

3. **Validation Checklist**
   - [ ] All tools migrated
   - [ ] All resources migrated
   - [ ] Pydantic validation working
   - [ ] Security checks still enforced
   - [ ] Response formats unchanged
   - [ ] Performance similar or better

---

### Phase 5: Cleanup & Documentation (1 day)

**Goal:** Remove old code, update docs

**Tasks:**
1. Remove old `mcp_server/server.py`
2. Rename `fastmcp_server.py` to `server.py`
3. Update `README.md` with new patterns
4. Update deployment scripts
5. Create developer guide for FastMCP patterns

**Documentation Updates:**
```markdown
# NBA MCP Server

Built with FastMCP framework for clean, maintainable code.

## Adding New Tools

1. Define Pydantic model for parameters
2. Add decorated function:
   ```python
   @mcp.tool()
   async def my_tool(params: MyParams, ctx: Context) -> MyResult:
       """Tool description here."""
       # Implementation
       pass
   ```

## Running the Server

```bash
# Development (stdio)
python -m mcp_server

# Production (SSE)
python -m mcp_server --transport sse
```
```

---

## Benefits & Trade-offs

### Benefits of FastMCP

#### 1. Code Reduction (50-70%)
- Automatic schema generation from types
- No manual argument extraction
- No manual response formatting
- Built-in validation

#### 2. Better Type Safety
- Pydantic models throughout
- Type hints for parameters
- IDE autocomplete works better
- Catch errors at dev time

#### 3. Improved Maintainability
- Self-documenting decorators
- Clear separation of concerns
- Less boilerplate
- Easier to test

#### 4. Better Developer Experience
- Context injection (clean)
- Progress reporting (built-in)
- Logging (structured)
- Error handling (consistent)

#### 5. Easier Onboarding
- Familiar pattern (like FastAPI)
- Less code to understand
- Clear conventions
- Better docs

#### 6. Future-Proof
- Official framework from Anthropic
- Well-maintained
- Community support
- Regular updates

### Trade-offs

#### 1. Migration Effort
- **Cost:** 2-4 days of development
- **Risk:** Medium (breaking changes possible)
- **Mitigation:** Phased migration, parallel servers

#### 2. Learning Curve
- **Issue:** New framework to learn
- **Severity:** Low (similar to FastAPI)
- **Mitigation:** Good documentation, examples

#### 3. Less Control
- **Issue:** Framework handles more automatically
- **Impact:** Minimal (can drop to low-level when needed)
- **Mitigation:** FastMCP still exposes low-level APIs

#### 4. Dependency on FastMCP
- **Issue:** Coupled to framework
- **Risk:** Low (official SDK, well-supported)
- **Mitigation:** FastMCP is thin wrapper, can unwrap if needed

### Recommendation

**✅ Migrate to FastMCP**

**Reasoning:**
1. Benefits far outweigh costs
2. Migration is straightforward (2-4 days)
3. Code will be significantly cleaner
4. Maintenance burden reduced
5. Aligns with MCP best practices
6. Enables Phase 1 enhancements more easily

**When to Migrate:**
- After completing Quick Wins testing (Path 1)
- Before Phase 1 enhancements (caching, pooling)
- When you have 2-4 days for focused work

---

## Code Examples

### Complete NBA Tool Migration Example

#### Before: Low-Level API

```python
# mcp_server/server.py (excerpt)

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_database",
            description="Execute a SQL query against the NBA database",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["sql"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    if name == "query_database":
        # Extract arguments
        sql = arguments.get("sql")
        limit = arguments.get("limit", 100)

        # Validate
        if not sql:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "SQL query is required"})
            )]

        # Security check
        if not sql.strip().upper().startswith("SELECT"):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Only SELECT queries allowed"})
            )]

        # Execute
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute(sql)
            rows = cursor.fetchmany(limit)
            columns = [desc[0] for desc in cursor.description]

            result = {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]
        finally:
            conn.close()
```

**Lines: ~70**

#### After: FastMCP API

```python
# mcp_server/fastmcp_server.py

from mcp.server.fastmcp import FastMCP, Context
from mcp_server.tools.params import QueryDatabaseParams  # ← Already exists
from mcp_server.responses import QueryResult  # ← Already exists

mcp = FastMCP("nba-mcp", lifespan=nba_lifespan)

@mcp.tool()
async def query_database(
    params: QueryDatabaseParams,
    ctx: Context
) -> QueryResult:
    """Execute a SQL query against the NBA database.

    Only SELECT queries are allowed for security.
    """
    # Get DB from lifespan context
    db_pool = ctx.request_context.lifespan_context["db_pool"]

    # Log query (already has structured logging)
    await ctx.debug(f"Executing query: {params.sql[:50]}...")

    # Execute (reuse existing function)
    result = await execute_query_with_validation(db_pool, params)

    # Log result
    await ctx.info(f"Query returned {result.row_count} rows")

    # Return structured data (automatically converted)
    return result
```

**Lines: ~25 (64% reduction)**

**Key Improvements:**
- ✅ No manual schema definition (generated from QueryDatabaseParams)
- ✅ No manual argument extraction (Pydantic does it)
- ✅ No manual validation (done by Pydantic + existing logic)
- ✅ No manual response formatting (QueryResult → TextContent automatic)
- ✅ Built-in logging via Context
- ✅ Connection pool from lifespan context
- ✅ Type-safe throughout

---

### Complete Resource Example

#### Before: Low-Level API

```python
@server.list_resources()
async def list_resources() -> list[Resource]:
    # List all available S3 files
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket='nba-data')

    resources = []
    for obj in response.get('Contents', []):
        resources.append(Resource(
            uri=f"s3://nba-data/{obj['Key']}",
            name=obj['Key'],
            mimeType="application/json"
        ))

    return resources

@server.read_resource()
async def read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
    # Parse URI
    uri_str = str(uri)
    if not uri_str.startswith("s3://nba-data/"):
        raise ValueError("Invalid S3 URI")

    key = uri_str.replace("s3://nba-data/", "")

    # Fetch from S3
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket='nba-data', Key=key)
    content = response['Body'].read().decode('utf-8')

    return [ReadResourceContents(
        uri=uri,
        mimeType="application/json",
        text=content
    )]
```

**Lines: ~35**

#### After: FastMCP API

```python
@mcp.resource("s3://nba-data/{key}")
async def get_nba_data(key: str, ctx: Context) -> str:
    """Fetch NBA data file from S3.

    Args:
        key: S3 object key (e.g., 'players/stats.json')
    """
    s3 = ctx.request_context.lifespan_context["s3_client"]

    await ctx.info(f"Fetching s3://nba-data/{key}")

    response = s3.get_object(Bucket='nba-data', Key=key)
    content = response['Body'].read().decode('utf-8')

    await ctx.debug(f"Retrieved {len(content)} bytes")

    return content  # Automatically becomes TextContent
```

**Lines: ~12 (66% reduction)**

**Key Improvements:**
- ✅ URI template handles parameter extraction
- ✅ No manual URI parsing
- ✅ No manual resource listing (FastMCP handles template expansion)
- ✅ Automatic MIME type detection
- ✅ Built-in logging
- ✅ S3 client from lifespan context

---

### Lifespan Management Example

```python
# mcp_server/lifespan.py

from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
import asyncpg
import aioboto3
import aioredis

@asynccontextmanager
async def nba_lifespan(app: FastMCP):
    """Initialize shared resources for NBA MCP server."""

    print("🏀 Starting NBA MCP Server...")

    # 1. Initialize database pool
    print("📊 Connecting to database...")
    db_pool = await asyncpg.create_pool(
        database="nba_data.db",
        min_size=2,
        max_size=10,
        command_timeout=30
    )

    # 2. Initialize S3 client
    print("☁️  Initializing S3 client...")
    session = aioboto3.Session()
    s3_client = await session.client(
        's3',
        region_name='us-east-1'
    ).__aenter__()

    # 3. Initialize cache (optional, for Phase 1 enhancements)
    print("💾 Connecting to Redis cache...")
    cache = await aioredis.create_redis_pool(
        'redis://localhost',
        minsize=2,
        maxsize=10
    )

    # 4. Load configuration
    settings = NBASettings()

    # Create context available to all tools
    context = {
        "db_pool": db_pool,
        "s3_client": s3_client,
        "cache": cache,
        "settings": settings
    }

    print("✅ NBA MCP Server ready!")

    try:
        yield context  # Server runs here
    finally:
        # Cleanup on shutdown
        print("🛑 Shutting down NBA MCP Server...")

        await db_pool.close()
        await s3_client.__aexit__(None, None, None)
        cache.close()
        await cache.wait_closed()

        print("✅ Shutdown complete")
```

**Usage in Tools:**
```python
@mcp.tool()
async def query_database(params: QueryDatabaseParams, ctx: Context) -> QueryResult:
    """Execute database query."""

    # Access shared resources from lifespan
    db_pool = ctx.request_context.lifespan_context["db_pool"]
    cache = ctx.request_context.lifespan_context["cache"]

    # Check cache first (Phase 1 enhancement)
    cache_key = f"query:{hash(params.sql)}"
    cached = await cache.get(cache_key)
    if cached:
        await ctx.debug("Cache hit")
        return QueryResult.parse_raw(cached)

    # Execute query
    async with db_pool.acquire() as conn:
        result = await conn.fetch(params.sql)

    # Cache result
    await cache.setex(cache_key, 300, result.json())

    return result
```

---

## Next Steps

### Immediate (If Migrating)

1. **Review this document** with team
2. **Create feature branch** for migration
3. **Follow Phase 1** (preparation)
4. **Test in parallel** with existing server
5. **Migrate incrementally** (Phases 2-3)
6. **Validate thoroughly** (Phase 4)
7. **Deploy** (Phase 5)

### Alternative (If Waiting)

1. **Complete Quick Wins testing** (Path 1 from START_HERE)
2. **Decide on migration** based on testing results
3. **Schedule migration** (2-4 day block)
4. **Then proceed with Phase 1 enhancements**

### Long Term

1. **Monitor FastMCP updates** in MCP SDK
2. **Adopt new patterns** as they emerge
3. **Contribute back** learnings to community
4. **Refine patterns** based on production use

---

## Conclusion

**FastMCP Discovery Summary:**
- ✅ Found official high-level framework in Python SDK
- ✅ Dramatically simplifies MCP server development
- ✅ 50-70% code reduction vs low-level API
- ✅ Better type safety, maintainability, DX
- ✅ Well-documented with reference implementations
- ✅ Production-ready and officially supported

**Recommendation:**
Migrate NBA MCP server to FastMCP framework. The benefits (cleaner code, better maintainability, reduced complexity) far outweigh the migration cost (2-4 days).

**Best Time to Migrate:**
After completing Quick Wins testing, before implementing Phase 1 enhancements (caching, connection pooling). This sets a solid foundation for future work.

---

**Document References:**
- FastMCP Source: `/Users/ryanranft/modelcontextprotocol/python-sdk/src/mcp/server/fastmcp/`
- Reference Servers: `/Users/ryanranft/modelcontextprotocol/servers/src/`
- Python SDK Docs: `/Users/ryanranft/modelcontextprotocol/python-sdk/README.md`

**Related Documents:**
- `MCP_REPOSITORY_ANALYSIS_ADVANCED_PATTERNS.md` - Phase 1 enhancements
- `START_HERE_NEXT_STEPS.md` - Decision matrix
- `ALL_QUICK_WINS_COMPLETE.md` - Current implementation status