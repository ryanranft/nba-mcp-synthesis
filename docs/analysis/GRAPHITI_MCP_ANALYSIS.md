# Graphiti MCP Analysis & Recommendations

**Repository:** https://github.com/getzep/graphiti
**Analysis Date:** October 10, 2025

---

## Executive Summary

Graphiti is a sophisticated knowledge graph MCP server that demonstrates several advanced patterns and best practices we can apply to the NBA MCP Synthesis system. The project focuses on real-time, temporal knowledge graphs with semantic search capabilities.

**Key Takeaways:**
1. Advanced async patterns with semaphore-based concurrency control
2. Standardized response types (SuccessResponse/ErrorResponse)
3. Pydantic-based validation throughout
4. Hybrid search combining semantic + keyword + graph traversal
5. Bi-temporal data model for precise historical tracking

---

## Key Features from Graphiti

### 1. Real-Time Knowledge Graphs
- **What:** Dynamic, evolving knowledge graphs with incremental updates
- **How:** Bi-temporal data model tracking event occurrence + ingestion times
- **Benefit:** Sub-second query latency with precise historical tracking

**NBA Application:**
- Track player performance evolution over time
- Build relationship graphs between players, teams, coaches
- Temporal queries: "Show me how the Warriors' lineup changed this season"

### 2. Hybrid Search Capabilities
- **What:** Combines semantic embeddings + keyword search + graph traversal
- **How:** Multi-modal retrieval system with configurable weights
- **Benefit:** More accurate, context-aware search results

**NBA Application:**
- "Find games similar to Warriors vs Lakers 2023 Finals" (semantic)
- "LeBron James 40+ points games" (keyword)
- "Players who played with both Curry and Durant" (graph traversal)

### 3. Entity Type Filtering
- **What:** Categorize data into types (Preference, Procedure, Requirement)
- **How:** Pydantic models with custom entity definitions
- **Benefit:** Structured, queryable knowledge organization

**NBA Application:**
Define entity types:
- `Player`, `Team`, `Game`, `Season`, `Coach`
- `Performance`, `Injury`, `Trade`, `Award`
- Filter queries: "Get all Trade entities involving Lakers"

---

## Best Practices Identified

### 1. MCP Tool Structure ✅ RECOMMENDED

**Graphiti Pattern:**
```python
@mcp.tool()
async def add_memory(
    message: str,
    group_id: str | None = None
) -> SuccessResponse | ErrorResponse:
    """Add new memory to the knowledge graph"""
    try:
        # Validation
        if not message:
            return ErrorResponse(error="Message cannot be empty")
        
        # Processing
        result = await graphiti.add_episode(...)
        
        # Success response
        return SuccessResponse(
            message="Memory added successfully",
            data=result.model_dump()
        )
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        return ErrorResponse(error=str(e))
```

**Current NBA Pattern:**
```python
async def execute(self, tool_name: str, arguments: Dict) -> Dict:
    try:
        if tool_name == "query_database":
            return await self._query_database(arguments)
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Recommendation:** ✅ **Adopt Standardized Response Types**

Create typed response classes:
```python
from typing import TypedDict, Literal

class SuccessResponse(TypedDict):
    success: Literal[True]
    message: str
    data: dict
    timestamp: str

class ErrorResponse(TypedDict):
    success: Literal[False]
    error: str
    error_type: str
    timestamp: str
```

**Benefits:**
- Type safety for Claude Desktop
- Consistent error handling
- Better debugging with error types
- Clearer API contracts

---

### 2. Concurrency Management ✅ RECOMMENDED

**Graphiti Pattern:**
```python
# Semaphore-based concurrency control
SEMAPHORE_LIMIT = int(os.getenv("SEMAPHORE_LIMIT", "4"))
semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

async def process_with_limit(operation):
    async with semaphore:
        return await operation()
```

**Current NBA Pattern:**
- No explicit concurrency limits
- Circuit breaker exists but no async semaphore

**Recommendation:** ✅ **Add Async Semaphore for MCP Tools**

Prevent overwhelming downstream services:
```python
# mcp_server/server.py
class NBAMCPServer:
    def __init__(self, config):
        ...
        # Add semaphore for concurrent tool execution
        self.tool_semaphore = asyncio.Semaphore(
            int(os.getenv("MCP_TOOL_CONCURRENCY", "5"))
        )
    
    async def call_tool(self, name: str, arguments: Dict):
        async with self.tool_semaphore:
            # Execute tool
            ...
```

**Benefits:**
- Prevent rate limit errors with API providers (DeepSeek, Claude)
- Protect database from connection pool exhaustion
- Configurable per-environment (dev vs prod)

---

### 3. Pydantic Validation ✅ RECOMMENDED

**Graphiti Pattern:**
```python
from pydantic import BaseModel, Field

class SearchConfig(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)
    group_ids: list[str] | None = None
    entity_types: list[str] | None = None
```

**Current NBA Pattern:**
```python
# Manual validation in tool execution
if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
    return {"error": "Invalid table name"}
```

**Recommendation:** ✅ **Add Pydantic Models for All Tool Parameters**

```python
# mcp_server/tools/models.py
from pydantic import BaseModel, Field, validator

class QueryDatabaseParams(BaseModel):
    sql_query: str = Field(..., min_length=1, max_length=10000)
    max_rows: int = Field(default=1000, ge=1, le=10000)
    
    @validator('sql_query')
    def validate_sql(cls, v):
        forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT']
        if any(kw in v.upper() for kw in forbidden):
            raise ValueError("Only SELECT queries allowed")
        return v

class ListS3FilesParams(BaseModel):
    prefix: str = Field(default="", max_length=500)
    max_keys: int = Field(default=100, ge=1, le=1000)
    
class GetTableSchemaParams(BaseModel):
    table_name: str = Field(..., regex=r'^[a-zA-Z0-9_]+$')
```

**Benefits:**
- Automatic validation before execution
- Better error messages
- Type hints for IDE
- OpenAPI schema generation (if adding REST API)

---

### 4. Structured Logging with Context ✅ ALREADY IMPLEMENTED

**Graphiti Pattern:**
```python
logger.info(f"Processing {len(episodes)} episodes")
logger.error(f"Failed to add memory: {error}")
```

**Current NBA Pattern:**
```python
logger.info(
    "Tool executed successfully",
    extra={"tool": name, "result_size": len(str(result))}
)
```

**Status:** ✅ **Already following best practice**

Your current structured logging is excellent. Consider adding:
- Request duration tracking (you have this in PerformanceLogger)
- User/client attribution (you have client_id in RequestContext)
- Tool-specific metrics (query complexity, data volume)

---

### 5. Environment-Based Configuration ✅ ALREADY IMPLEMENTED

**Graphiti Pattern:**
```python
class GraphitiConfig:
    api_key: str = os.getenv("OPENAI_API_KEY")
    semaphore_limit: int = int(os.getenv("SEMAPHORE_LIMIT", "4"))
```

**Current NBA Pattern:**
```python
class MCPConfig:
    rds_host: str = os.getenv("RDS_HOST")
    rds_port: int = int(os.getenv("RDS_PORT", "5432"))
```

**Status:** ✅ **Already following best practice**

Your MCPConfig class is well-designed. Already implements:
- Environment variable loading
- Default values
- Type conversion

---

### 6. Tool Naming Convention ⚠️ CONSIDER

**Graphiti Pattern:**
- `add_memory` - verb_noun pattern
- `search_nodes` - verb_noun pattern
- `get_facts` - verb_noun pattern

**Current NBA Pattern:**
- `query_database` - verb_noun ✅
- `get_table_schema` - verb_noun_noun ✅
- `list_s3_files` - verb_noun_noun ✅

**Status:** ✅ **Already consistent**

Your naming is clear and follows verb_noun pattern. Consider standardizing prefixes:
- `query_*` for database operations
- `get_*` for retrieval operations
- `list_*` for listing operations
- `search_*` for search operations (if you add search)

---

## New Features to Consider

### 1. Semantic Search for Game Analysis 🌟 HIGH VALUE

**What:** Add semantic search over game descriptions, player performances
**How:** Use embeddings (OpenAI, DeepSeek) to find similar games/performances
**Benefit:** Natural language queries like "Find games where a player had a clutch performance"

**Implementation:**
```python
# New tool: semantic_search_games
class SemanticSearchParams(BaseModel):
    query: str = Field(..., min_length=3)
    limit: int = Field(default=10, ge=1, le=50)
    filters: dict | None = None  # season, team, player

async def semantic_search_games(params: SemanticSearchParams):
    # 1. Generate embedding for query
    embedding = await get_embedding(params.query)
    
    # 2. Search S3 game files using vector similarity
    similar_games = await vector_search(embedding, limit=params.limit)
    
    # 3. Enrich with database stats
    for game in similar_games:
        game['stats'] = await db.get_game_stats(game['game_id'])
    
    return SuccessResponse(data=similar_games)
```

**Data Store Options:**
- Use existing S3 + PostgreSQL (generate embeddings on-demand)
- Add Pinecone/Weaviate for vector storage (better performance)
- Use PostgreSQL pgvector extension (simplest, good performance)

---

### 2. Knowledge Graph for Player Relationships 🌟 MEDIUM VALUE

**What:** Build a graph showing player relationships (teammates, opponents, draft class)
**How:** Extract relationships from game data, build graph in Neo4j or NetworkX
**Benefit:** Graph queries like "Players who played with both Curry and LeBron"

**Implementation:**
```python
# New tool: query_player_graph
class PlayerGraphParams(BaseModel):
    player_name: str
    relationship_type: Literal["teammates", "opponents", "draft_class"]
    max_depth: int = Field(default=2, ge=1, le=3)

async def query_player_graph(params: PlayerGraphParams):
    # Build graph from database
    graph = await build_player_graph(params.relationship_type)
    
    # Traverse graph
    related = graph.neighbors(params.player_name, depth=params.max_depth)
    
    return SuccessResponse(data={
        "player": params.player_name,
        "relationships": related,
        "graph_stats": {"nodes": len(graph.nodes), "edges": len(graph.edges)}
    })
```

**Storage:**
- Option 1: Build graph on-demand from PostgreSQL (simplest)
- Option 2: Maintain graph in Neo4j (best performance)
- Option 3: Cache graph in Redis (good middle ground)

---

### 3. Temporal Queries 🌟 HIGH VALUE

**What:** Query data with temporal context ("Show performance over time")
**How:** Add time-series analysis tools
**Benefit:** Trend analysis, season-over-season comparisons

**Implementation:**
```python
# New tool: analyze_player_trend
class PlayerTrendParams(BaseModel):
    player_name: str
    metric: Literal["points", "assists", "rebounds", "efficiency"]
    time_range: str  # "2023-01-01:2024-01-01" or "last_30_days"
    aggregation: Literal["game", "week", "month"] = "game"

async def analyze_player_trend(params: PlayerTrendParams):
    # Parse time range
    start, end = parse_time_range(params.time_range)
    
    # Query database for time series
    data = await db.query(f"""
        SELECT date, {params.metric}
        FROM player_game_stats
        WHERE player_name = %s
        AND date BETWEEN %s AND %s
        ORDER BY date
    """, (params.player_name, start, end))
    
    # Calculate trend
    trend = calculate_trend(data, aggregation=params.aggregation)
    
    return SuccessResponse(data={
        "player": params.player_name,
        "metric": params.metric,
        "trend": trend,
        "statistics": {
            "mean": np.mean(data),
            "std": np.std(data),
            "trend_direction": "improving" if trend > 0 else "declining"
        }
    })
```

---

### 4. Multi-Modal Search (Hybrid) 🌟 MEDIUM VALUE

**What:** Combine SQL, semantic search, and graph traversal in one query
**How:** Implement query planner that routes to appropriate data source
**Benefit:** Complex queries like "Find games where Lakers won by >10 points with similar play styles to their 2020 championship run"

**Implementation:**
```python
# New tool: hybrid_search
class HybridSearchParams(BaseModel):
    query: str
    include_semantic: bool = True
    include_graph: bool = False
    include_sql: bool = True

async def hybrid_search(params: HybridSearchParams):
    results = {}
    
    # Parse query intent (could use LLM here)
    intent = await parse_query_intent(params.query)
    
    # SQL search (structured data)
    if params.include_sql:
        sql_query = await generate_sql(intent)
        results['sql'] = await db.execute(sql_query)
    
    # Semantic search (similarity)
    if params.include_semantic:
        embedding = await get_embedding(params.query)
        results['semantic'] = await vector_search(embedding)
    
    # Graph search (relationships)
    if params.include_graph:
        results['graph'] = await graph_search(intent)
    
    # Synthesize results
    synthesized = await synthesize_results(results, query=params.query)
    
    return SuccessResponse(data=synthesized)
```

---

## Implementation Priorities

### 🔥 HIGH PRIORITY (Implement Soon)

1. **Standardized Response Types** (2 hours)
   - Create `SuccessResponse` and `ErrorResponse` TypedDicts
   - Update all tools to use these types
   - Benefits: Better type safety, consistent error handling

2. **Async Semaphore for Concurrency** (1 hour)
   - Add semaphore to NBAMCPServer
   - Configure via environment variable
   - Benefits: Prevent rate limiting, protect downstream services

3. **Pydantic Parameter Validation** (4 hours)
   - Create models for all tool parameters
   - Add validators for SQL, file paths, etc.
   - Benefits: Automatic validation, better errors, type safety

4. **Temporal Query Support** (6 hours)
   - Add time-range parsing
   - Implement trend analysis tools
   - Benefits: Enable time-series analysis, season comparisons

### ⚡ MEDIUM PRIORITY (Consider for Phase 4)

5. **Semantic Search** (10-15 hours)
   - Set up vector database (pgvector or Pinecone)
   - Generate embeddings for game descriptions
   - Implement semantic search tool
   - Benefits: Natural language game/player search

6. **Player Knowledge Graph** (8-12 hours)
   - Build graph from existing data
   - Implement graph traversal queries
   - Add graph visualization
   - Benefits: Relationship queries, network analysis

### 🎯 LOW PRIORITY (Future Enhancement)

7. **Hybrid Multi-Modal Search** (15-20 hours)
   - Implement query intent parser
   - Build result synthesis
   - Add query planning
   - Benefits: Complex, multi-faceted queries

---

## Code Examples to Implement

### 1. Standardized Response Types

Create `mcp_server/responses.py`:
```python
from typing import TypedDict, Literal, Any
from datetime import datetime

class SuccessResponse(TypedDict):
    success: Literal[True]
    message: str
    data: dict[str, Any]
    timestamp: str
    request_id: str

class ErrorResponse(TypedDict):
    success: Literal[False]
    error: str
    error_type: str
    timestamp: str
    request_id: str

def success_response(
    message: str,
    data: dict[str, Any],
    request_id: str = None
) -> SuccessResponse:
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id or "default"
    }

def error_response(
    error: str,
    error_type: str = "UnknownError",
    request_id: str = None
) -> ErrorResponse:
    return {
        "success": False,
        "error": error,
        "error_type": error_type,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id or "default"
    }
```

Update tools to use:
```python
# mcp_server/tools/database_tools.py
from mcp_server.responses import success_response, error_response

async def execute(self, tool_name: str, arguments: Dict):
    try:
        if tool_name == "query_database":
            result = await self._query_database(arguments)
            return success_response(
                message="Query executed successfully",
                data=result
            )
    except Exception as e:
        return error_response(
            error=str(e),
            error_type=type(e).__name__
        )
```

### 2. Async Concurrency Control

Update `mcp_server/server.py`:
```python
import asyncio
import os

class NBAMCPServer:
    def __init__(self, config: Optional[MCPConfig] = None):
        self.config = config or MCPConfig.from_env()
        
        # Add concurrency control
        concurrency_limit = int(os.getenv("MCP_TOOL_CONCURRENCY", "5"))
        self.tool_semaphore = asyncio.Semaphore(concurrency_limit)
        
        logger.info(f"MCP tool concurrency limit: {concurrency_limit}")
        
        # ... rest of init
    
    @self.server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
        # Limit concurrent tool executions
        async with self.tool_semaphore:
            # ... existing tool execution logic
```

### 3. Pydantic Parameter Models

Create `mcp_server/tools/params.py`:
```python
from pydantic import BaseModel, Field, validator
import re

class QueryDatabaseParams(BaseModel):
    sql_query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="SQL SELECT query to execute"
    )
    max_rows: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum rows to return"
    )
    
    @validator('sql_query')
    def validate_sql_query(cls, v):
        # Only SELECT allowed
        if not v.strip().upper().startswith(('SELECT', 'WITH')):
            raise ValueError("Only SELECT queries allowed")
        
        # Check for forbidden keywords
        forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE']
        for keyword in forbidden:
            if re.search(rf'\b{keyword}\b', v.upper()):
                raise ValueError(f"Forbidden keyword: {keyword}")
        
        return v

class ListS3FilesParams(BaseModel):
    prefix: str = Field(
        default="",
        max_length=500,
        description="S3 prefix filter"
    )
    max_keys: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum files to list"
    )

class GetTableSchemaParams(BaseModel):
    table_name: str = Field(
        ...,
        regex=r'^[a-zA-Z0-9_]+$',
        description="Table name (alphanumeric and underscore only)"
    )
```

Update tools to use Pydantic:
```python
from mcp_server.tools.params import QueryDatabaseParams

async def execute(self, tool_name: str, arguments: Dict):
    if tool_name == "query_database":
        # Validate with Pydantic
        try:
            params = QueryDatabaseParams(**arguments)
        except ValidationError as e:
            return error_response(
                error=str(e),
                error_type="ValidationError"
            )
        
        # Execute with validated params
        result = await self._query_database(
            params.sql_query,
            params.max_rows
        )
        return success_response("Query executed", result)
```

---

## Configuration Recommendations

### Environment Variables to Add

```bash
# Concurrency control
MCP_TOOL_CONCURRENCY=5  # Max concurrent tool executions

# Response formatting
MCP_INCLUDE_METADATA=true  # Include metadata in responses
MCP_RESPONSE_FORMAT=json  # Response format

# Feature flags (for gradual rollout)
ENABLE_SEMANTIC_SEARCH=false
ENABLE_GRAPH_QUERIES=false
ENABLE_TEMPORAL_ANALYSIS=true

# Vector search (if implementing semantic search)
VECTOR_DB_TYPE=pgvector  # or pinecone, weaviate
VECTOR_DB_URL=postgresql://...
EMBEDDING_PROVIDER=openai  # or deepseek
EMBEDDING_MODEL=text-embedding-3-small
```

---

## Testing Recommendations

Based on Graphiti's testing approach:

### 1. Add Integration Tests for MCP Tools

```python
# tests/integration/test_mcp_tools.py
import pytest
from mcp_server.server import NBAMCPServer

@pytest.mark.asyncio
async def test_query_database_tool():
    server = NBAMCPServer()
    
    result = await server.call_tool(
        "query_database",
        {"sql_query": "SELECT COUNT(*) FROM games", "max_rows": 1}
    )
    
    assert result["success"] is True
    assert "data" in result
    assert result["data"]["row_count"] >= 0

@pytest.mark.asyncio
async def test_invalid_sql_rejected():
    server = NBAMCPServer()
    
    result = await server.call_tool(
        "query_database",
        {"sql_query": "DROP TABLE games", "max_rows": 1}
    )
    
    assert result["success"] is False
    assert "Forbidden" in result["error"]
```

### 2. Add Performance Tests

```python
# tests/performance/test_concurrency.py
import pytest
import asyncio

@pytest.mark.asyncio
async def test_concurrent_tool_execution():
    server = NBAMCPServer()
    
    # Execute 10 queries concurrently
    tasks = [
        server.call_tool("query_database", {"sql_query": "SELECT 1"})
        for _ in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # All should succeed
    assert all(r["success"] for r in results)
    
    # Should respect concurrency limit (no more than 5 concurrent)
    # Check via logs or instrumentation
```

---

## Summary of Recommendations

### ✅ Quick Wins (Implement This Week)

1. **Standardized Response Types** - 2 hours
   - Immediate benefit: Better type safety
   - Low risk: Backwards compatible

2. **Async Semaphore** - 1 hour
   - Immediate benefit: Prevent rate limiting
   - Low risk: Just adds limit, doesn't change behavior

3. **Pydantic Validation** - 4 hours
   - Immediate benefit: Better error messages
   - Low risk: Catches errors earlier

**Total Time: ~7 hours** for significant improvements

### 🎯 Medium-Term (Next Sprint)

4. **Temporal Analysis Tools** - 6 hours
5. **Enhanced Testing** - 4 hours
6. **Documentation Updates** - 2 hours

**Total Time: ~12 hours** for complete enhancement

### 🚀 Future Enhancements (Phase 4+)

7. Semantic Search - 15 hours
8. Knowledge Graph - 12 hours
9. Hybrid Multi-Modal Search - 20 hours

---

## Conclusion

Graphiti demonstrates excellent MCP server patterns that we can apply to NBA MCP Synthesis:

**Adopt Immediately:**
- Standardized response types (SuccessResponse/ErrorResponse)
- Async semaphore for concurrency control
- Pydantic parameter validation

**Consider for Future:**
- Semantic search for game similarity
- Knowledge graphs for player relationships
- Temporal analysis for trends

**Already Doing Well:**
- Structured logging with context
- Environment-based configuration
- Consistent tool naming

The NBA MCP system is already well-architected. These enhancements will make it more robust, type-safe, and feature-rich.

---

**Next Steps:**
Would you like me to:
1. Implement the "Quick Wins" (response types, semaphore, Pydantic)?
2. Continue analyzing other MCP repositories?
3. Prioritize one specific feature to implement fully?
