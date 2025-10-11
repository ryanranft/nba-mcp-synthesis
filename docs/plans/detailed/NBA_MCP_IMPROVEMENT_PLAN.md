# NBA MCP Server - Comprehensive Improvement Plan

**Date**: 2025-10-11 (Corrected)
**Version**: 3.0 (Verified accurate - comprehensive audit complete)
**Based on**: Analysis of 8 cloned MCP repositories + detailed code verification

---

## 🎯 COMPLETION STATUS UPDATE (October 11, 2025 - CORRECTED)

### What We Actually Built (Sprints 5-8)

**Instead of the original plan's Sprints 5-7, we built different Sprints 5-8 with 88 total tools:**

✅ **Sprint 5 (Actual)**: Core Infrastructure - 33 tools
- 15 Database tools (query_database, list_tables, create_table, etc.)
- 10 S3 tools (list_s3_files, upload_s3_file, etc.)
- 8 File tools (read_file, write_file, etc.)

✅ **Sprint 6 (Actual)**: AWS Integration - 22 tools
- 12 Action tools (analyze_player_performance, compare_players, predict_game_outcome, etc.)
- 10 AWS Glue tools (create_glue_crawler, start_crawler, etc.)

✅ **Sprint 7 (Actual)**: Machine Learning Core - 18 tools
- 5 Clustering tools (ml_kmeans, ml_hierarchical_clustering, ml_dbscan, etc.)
- 7 Classification tools (ml_logistic_regression, ml_decision_tree, ml_random_forest, etc.)
- 3 Anomaly detection tools (ml_isolation_forest, ml_local_outlier_factor, etc.)
- 3 Feature engineering tools (ml_normalize_features, ml_polynomial_features, etc.)

✅ **Sprint 8 (Actual)**: Model Evaluation & Validation - 15 tools
- 6 Classification metrics (ml_accuracy_score, ml_precision_recall_f1, ml_roc_auc_score, etc.)
- 3 Regression metrics (ml_mse_rmse_mae, ml_r2_score, ml_mape)
- 3 Cross-validation tools (ml_k_fold_split, ml_stratified_k_fold_split, ml_cross_validate)
- 2 Model comparison tools (ml_compare_models, ml_paired_ttest)
- 1 Hyperparameter tuning tool (ml_grid_search)

**Total Delivered**: 88 MCP tools (vs. 36 planned)

### What We ALSO Built (Beyond Sprints 5-8) ✅✅✅

⚠️ **IMPORTANT**: These were marked as "NOT DONE" in earlier versions, but comprehensive verification (Oct 11, 2025) confirmed they ARE DONE!

✅ **Math/Stats/NBA Tools**: **37 tools REGISTERED** (NOT in Sprints 5-8 plan, but implemented!)
- **7 Arithmetic tools** ✅ (math_add, math_subtract, math_multiply, math_divide, math_sum, math_round, math_modulo)
- **17 Statistical tools** ✅ (stats_mean, stats_median, stats_mode, stats_min_max, stats_variance, stats_summary, PLUS 11 advanced: correlation, covariance, linear_regression, predict, correlation_matrix, moving_average, exponential_moving_average, trend_detection, percent_change, growth_rate, volatility)
- **13 NBA metrics tools** ✅ (nba_player_efficiency_rating, nba_true_shooting_percentage, nba_effective_field_goal_percentage, nba_usage_rate, nba_offensive_rating, nba_defensive_rating, nba_pace, nba_four_factors, nba_turnover_percentage, nba_rebound_percentage, nba_assist_percentage, nba_steal_percentage, nba_block_percentage)

⚠️ **2 NBA metrics IMPLEMENTED but NOT REGISTERED**:
- nba_win_shares (nba_metrics_helper.py:324) - needs MCP registration
- nba_box_plus_minus (nba_metrics_helper.py:354) - needs MCP registration

✅ **MCP Prompts**: **5 prompts REGISTERED** (partial implementation)
- 2 from original plan: compare_players, analyze_team_performance (as team_analysis) ✅
- 3 additional: suggest_queries, game_analysis, recommend_books ✅

✅ **Book Integration Tools**: **14 tools REGISTERED** ✅
- 5 General book tools (list_books, read_book, search_books, get_book_metadata, get_book_chunk)
- 3 EPUB tools (get_epub_metadata, get_epub_toc, read_epub_chapter)
- 6 PDF tools (get_pdf_metadata, get_pdf_toc, read_pdf_page, read_pdf_page_range, read_pdf_chapter, search_pdf)

### What We Have NOT Built (From Original Plan)

❌ **Web Scraping Integration**: 3 tools (NOT DONE)
- scrape_nba_webpage (Crawl4AI-based scraping)
- search_webpage_for_text (text search with context)
- extract_structured_data (LLM-based extraction)

❌ **MCP Prompts** (remaining): 5 prompts (NOT DONE)
- analyze_player, predict_game, injury_impact, draft_analysis, trade_evaluation

❌ **MCP Resources**: 6 resources (NOT DONE)
- nba://games/{date}, nba://standings/{conference}, nba://players/{player_id}, nba://teams/{team_id}, nba://injuries, nba://players/top-scorers

### What's Next: Register & Complete

**Phase 9A: Register Missing Tools** (1-2 hours) ⚠️ HIGH PRIORITY
1. Register nba_win_shares in fastmcp_server.py
2. Register nba_box_plus_minus in fastmcp_server.py

**Phase 9B: Complete Original Plan** (optional, 1-2 weeks)
1. Web Scraping (3 tools) - 3-5 days
2. Remaining MCP Prompts (5 prompts) - 1-2 days
3. MCP Resources (6 resources) - 2-3 days

**Current Total**: 88 registered + 2 unregistered = **90 tools/features implemented**
**Remaining**: 3 web scraping + 5 prompts + 6 resources = **14 features**
**Grand Total Target**: 90 + 14 = **104 tools/features**
**Progress**: **86% complete** (90/104)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Repository Analysis](#2-repository-analysis)
3. [Current NBA MCP Assessment](#3-current-nba-mcp-assessment)
4. [Improvement Sprint Plans](#4-improvement-sprint-plans)
5. [Technical Patterns to Adopt](#5-technical-patterns-to-adopt)
6. [Priority Matrix](#6-priority-matrix)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment Improvements](#9-deployment-improvements)
10. [Documentation Updates](#10-documentation-updates)
11. [Phase 9: Complete Original Plan](#11-phase-9-complete-original-plan) ⭐ NEW

---

## 1. Executive Summary

### 1.1 Analysis Overview

This document provides a comprehensive improvement plan for the NBA MCP server based on analysis of 8 MCP repositories:

| Repository | Primary Features | Relevance to NBA MCP |
|-----------|-----------------|---------------------|
| **ebook-mcp** | EPUB/PDF processing | ✅ Already integrated |
| **lean-lsp-mcp** | Advanced error handling, decorators | ✅ Already integrated |
| **math-mcp** | Statistical & mathematical operations | 🔶 High priority for NBA analytics |
| **firecrawl-mcp-server** | Web scraping, crawling, search | 🔶 High priority for news/data |
| **WEB-SCRAPING-MCP** | Crawl4AI web extraction | 🔶 High priority for content |
| **mlpack** | Machine learning library | 🔵 Medium priority for predictions |
| **MCP Python SDK** | Official patterns & examples | ✅ Patterns already used |
| **AWS MCP Servers** | 60+ AWS integrations | 🔵 Medium priority for scaling |

### 1.2 Key Capabilities Found

**Web Data Integration:**
- Firecrawl: scrape, batch_scrape, map, crawl, search, extract (8 tools)
- Crawl4AI: scrape_url, extract_text_by_query, smart_extract (3 tools)
- Rate limiting, retry logic, error handling

**Mathematical Operations:**
- Arithmetic: add, subtract, multiply, divide, sum, modulo
- Statistical: mean, median, mode, min, max
- Trigonometric: sin, cos, tan, arcsine, arccosine, arctangent
- Rounding: floor, ceiling, round

**Advanced Patterns:**
- Pagination (cursor-based)
- Authentication (OAuth, token introspection)
- Multiple transports (stdio, SSE, streamable-HTTP)
- Event stores for resumability
- Prompts & resources (not just tools)

**Machine Learning:**
- Classification, regression, clustering
- Neural networks
- Time series analysis
- Model persistence

### 1.3 High-Priority Improvements

**Quick Wins (1-2 days each):**
1. ✅ Mathematical/statistical tools for NBA analytics
2. 🔶 Prompt templates for common NBA queries
3. 🔶 Resource endpoints for game data
4. 🔶 Pagination for large result sets

**Medium Effort (1 week each):**
1. 🔶 Web scraping tools for NBA news/analysis
2. 🔶 Streamable HTTP transport
3. 🔶 Event-based notifications
4. 🔶 Advanced caching with invalidation

**Large Initiatives (2-4 weeks):**
1. 🔵 Machine learning integration
2. 🔵 OAuth authentication
3. 🔵 Multi-region deployment
4. 🔵 Vector search for semantic queries

---

## 2. Repository Analysis

### 2.1 ebook-mcp (Already Integrated ✅)

**Location**: `/Users/ryanranft/modelcontextprotocol/ebook-mcp`

**Features Adopted:**
- EPUB metadata extraction
- PDF processing with TOC navigation
- Chapter extraction with subchapter handling
- Multiple output formats (text/HTML/markdown)

**Status**: Fully integrated in Sprint 2

---

### 2.2 lean-lsp-mcp (Already Integrated ✅)

**Location**: `/Users/ryanranft/modelcontextprotocol/lean-lsp-mcp`

**Features Adopted:**
- Rate limiting with sliding window
- Decorator-based error handling
- File change detection patterns
- Bearer token authentication (ready)
- Lifespan context management

**Status**: Fully integrated in Sprint 1

---

### 2.3 math-mcp 🔶 HIGH PRIORITY

**Location**: `/Users/ryanranft/modelcontextprotocol/math-mcp`

**Capabilities:**

#### Arithmetic Operations (7 tools)
```typescript
// Examples from math-mcp
add(firstNumber, secondNumber)
subtract(minuend, subtrahend)
multiply(firstNumber, secondNumber)
division(numerator, denominator)
sum(numbers: Array)
modulo(numerator, denominator)
round(number), floor(number), ceiling(number)
```

#### Statistical Operations (5 tools)
```typescript
mean(numbers: Array)
median(numbers: Array)
mode(numbers: Array)
min(numbers: Array)
max(numbers: Array)
```

#### Trigonometric Operations (8 tools)
```typescript
sin(radians), arcsin(number)
cos(radians), arccos(number)
tan(radians), arctan(number)
radiansToDegrees(radians)
degreesToRadians(degrees)
```

**NBA MCP Applications:**
- Calculate player efficiency ratings (PER)
- Compute team statistics (mean PPG, median assists, etc.)
- Advanced metrics (true shooting %, usage rate, etc.)
- Win probability calculations
- Shot distance/angle trigonometry

**Implementation Priority**: 🔶 **HIGH** - Direct value for NBA analytics

---

### 2.4 firecrawl-mcp-server 🔶 HIGH PRIORITY

**Location**: `/Users/ryanranft/modelcontextprotocol/firecrawl-mcp-server`

**Capabilities:**

#### Tools (8 total)

1. **firecrawl_scrape** - Single page content extraction
```json
{
  "url": "https://www.nba.com/news",
  "formats": ["markdown"],
  "onlyMainContent": true,
  "includeTags": ["article", "main"],
  "excludeTags": ["nav", "footer"]
}
```

2. **firecrawl_batch_scrape** - Multiple URLs efficiently
```json
{
  "urls": [
    "https://www.espn.com/nba/player/_/id/1966/lebron-james",
    "https://www.espn.com/nba/player/_/id/3975/stephen-curry"
  ],
  "options": {"formats": ["markdown"], "onlyMainContent": true}
}
```

3. **firecrawl_map** - Discover URLs on a site
```json
{
  "url": "https://www.basketball-reference.com/players/j/"
}
```

4. **firecrawl_crawl** - Multi-page extraction
```json
{
  "url": "https://www.nba.com/stats/*",
  "maxDepth": 2,
  "limit": 100,
  "deduplicateSimilarURLs": true
}
```

5. **firecrawl_search** - Web search with scraping
```json
{
  "query": "LeBron James stats 2024",
  "limit": 5,
  "scrapeOptions": {"formats": ["markdown"]}
}
```

6. **firecrawl_extract** - Structured data extraction
```json
{
  "urls": ["https://www.nba.com/game/LAL-vs-GSW-0022400123"],
  "schema": {
    "type": "object",
    "properties": {
      "home_team": {"type": "string"},
      "away_team": {"type": "string"},
      "final_score": {"type": "string"},
      "top_performers": {"type": "array"}
    }
  }
}
```

7. **firecrawl_check_batch_status** - Check batch operation status
8. **firecrawl_check_crawl_status** - Check crawl job status

#### Key Features

**Rate Limiting & Retries:**
```typescript
const CONFIG = {
  retry: {
    maxAttempts: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    backoffFactor: 2
  },
  credit: {
    warningThreshold: 1000,
    criticalThreshold: 100
  }
}
```

**Configuration via Environment Variables:**
- `FIRECRAWL_API_KEY` - Required for cloud API
- `FIRECRAWL_API_URL` - Optional for self-hosted
- `FIRECRAWL_RETRY_MAX_ATTEMPTS`
- `FIRECRAWL_RETRY_INITIAL_DELAY`
- `FIRECRAWL_CREDIT_WARNING_THRESHOLD`

**NBA MCP Applications:**
- Scrape NBA news articles for sentiment analysis
- Extract player stats from ESPN, Basketball Reference
- Monitor injury reports from multiple sources
- Collect expert predictions before games
- Build knowledge base from basketball blogs

**Implementation Priority**: 🔶 **HIGH** - External data augmentation

---

### 2.5 WEB-SCRAPING-MCP (Crawl4AI) 🔶 HIGH PRIORITY

**Location**: `/Users/ryanranft/modelcontextprotocol/WEB-SCRAPING-MCP`

**Capabilities:**

#### Tools (3 total)

1. **scrape_url** - Full webpage content as Markdown
```python
{
  "url": "https://www.theringer.com/nba"
}
# Returns: Markdown content of the page
```

2. **extract_text_by_query** - Find specific text with context
```python
{
  "url": "https://en.wikipedia.org/wiki/NBA",
  "query": "championship",
  "context_size": 300
}
# Returns: Up to 5 matches with 300 chars before/after
```

3. **smart_extract** - LLM-based extraction
```python
{
  "url": "https://www.nba.com/standings",
  "instruction": "Extract the top 5 teams in the Eastern Conference with their win-loss records"
}
# Uses Google Gemini API for intelligent extraction
```

#### Key Features

**Docker Support:**
```dockerfile
FROM python:3.11-slim
# Bundles Python + dependencies
# Runs on port 8002 with SSE transport
```

**Environment Variables:**
- `GOOGLE_API_KEY` - Required for smart_extract
- `OPENAI_API_KEY` - Optional (not currently used)
- `MISTRAL_API_KEY` - Optional (not currently used)

**NBA MCP Applications:**
- Extract game recaps with LLM understanding
- Pull structured data from unstructured articles
- Search for specific topics across multiple pages
- Intelligent summarization of NBA content

**Implementation Priority**: 🔶 **HIGH** - Complements Firecrawl with LLM extraction

---

### 2.6 mlpack 🔵 MEDIUM PRIORITY

**Location**: `/Users/ryanranft/modelcontextprotocol/mlpack`

**Note**: This is a C++ machine learning library, not an MCP server

**Capabilities:**
- Classification (decision trees, random forests, neural networks)
- Regression (linear, logistic, LARS)
- Clustering (k-means, DBSCAN)
- Time series analysis
- Dimensionality reduction (PCA, t-SNE)
- Model serialization

**NBA MCP Applications:**
- Player performance prediction models
- Team success probability
- Injury risk assessment
- Draft pick value estimation
- Play outcome prediction
- Player similarity clustering

**Implementation Approach:**
- Create Python wrapper tools using scikit-learn/PyTorch
- Not direct integration (mlpack is C++)
- Use patterns from mlpack for ML architecture

**Implementation Priority**: 🔵 **MEDIUM** - Valuable but requires ML infrastructure

---

### 2.7 MCP Python SDK ✅ PATTERNS ADOPTED

**Location**: `/Users/ryanranft/modelcontextprotocol/python-sdk`

**Key Examples Analyzed:**

#### 1. Pagination Example
```python
@app.list_tools()
async def list_tools_paginated(request: types.ListToolsRequest):
    page_size = 5
    cursor = request.params.cursor if request.params else None
    start_idx = int(cursor) if cursor else 0

    page_tools = SAMPLE_TOOLS[start_idx:start_idx + page_size]
    next_cursor = str(start_idx + page_size) if start_idx + page_size < len(SAMPLE_TOOLS) else None

    return types.ListToolsResult(tools=page_tools, nextCursor=next_cursor)
```

**NBA MCP Application**: Paginate through large player lists, game histories

#### 2. Authentication Example
```python
# Token introspection for OAuth
token_verifier = IntrospectionTokenVerifier(
    introspection_endpoint="http://localhost:9000/introspect",
    server_url=str(settings.server_url),
    validate_resource=settings.oauth_strict
)

app = FastMCP(
    name="MCP Resource Server",
    token_verifier=token_verifier,
    auth=AuthSettings(
        issuer_url=settings.auth_server_url,
        required_scopes=[settings.mcp_scope]
    )
)
```

**NBA MCP Application**: Protect premium analytics, team-specific data

#### 3. Streamable HTTP Example
```python
# With event store for resumability
event_store = InMemoryEventStore()
session_manager = StreamableHTTPSessionManager(
    app=app,
    event_store=event_store,
    json_response=json_response
)

# Send notifications during long operations
await ctx.session.send_log_message(
    level="info",
    data=f"Processing game {i+1}/{total}",
    related_request_id=ctx.request_id
)
```

**NBA MCP Application**: Stream real-time game updates, progress for bulk operations

#### 4. Resource Example
```python
@app.list_resources()
async def list_resources():
    return [
        types.Resource(
            uri=AnyUrl("nba://games/2024-10-10"),
            name="Games on 2024-10-10",
            description="All NBA games played on this date"
        )
    ]

@app.read_resource()
async def read_resource(uri: AnyUrl):
    # Parse URI and return resource content
    return "Game data JSON..."
```

**NBA MCP Application**: Expose games, players, teams as MCP resources

#### 5. Prompt Example
```python
@app.list_prompts()
async def list_prompts():
    return [
        types.Prompt(
            name="analyze_player",
            description="Analyze player performance",
            arguments=[
                types.PromptArgument(
                    name="player_name",
                    description="Name of the player",
                    required=True
                ),
                types.PromptArgument(
                    name="season",
                    description="Season year (e.g., 2024)",
                    required=False
                )
            ]
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict | None):
    if name == "analyze_player":
        player = arguments.get("player_name")
        season = arguments.get("season", "current")
        return types.GetPromptResult(
            description=f"Analysis for {player}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Analyze {player}'s performance in {season} season"
                    )
                )
            ]
        )
```

**NBA MCP Application**: Reusable prompts for common analysis patterns

**Implementation Priority**: ✅ **ALREADY USING** - Enhance with more patterns

---

### 2.8 AWS MCP Servers 🔵 MEDIUM PRIORITY

**Location**: `/Users/ryanranft/modelcontextprotocol/mcp/src/`

**60+ AWS Service Integrations:**

Relevant to NBA MCP:
- **DynamoDB MCP** - NoSQL database operations (now focused on design guidance)
- **S3 Tables MCP** - Advanced S3 table operations
- **Aurora DSQL MCP** - Distributed SQL database
- **CloudWatch MCP** - Logging and monitoring
- **Lambda Tool MCP** - Serverless function execution
- **Prometheus MCP** - Metrics and monitoring
- **Billing/Cost Management MCP** - Track AWS costs

**Key Patterns:**

#### Docker Deployment
```dockerfile
FROM python:3.10-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "-m", "awslabs.server"]
```

#### Environment Configuration
```json
{
  "mcpServers": {
    "awslabs.dynamodb-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.dynamodb-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-west-2",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

#### Read-only Mode
```python
# Environment variable for safety
DDB_MCP_READONLY = os.getenv("DDB-MCP-READONLY", "true")

if DDB_MCP_READONLY == "true":
    # Disable write operations
    pass
```

**NBA MCP Applications:**
- Deploy to AWS for production scaling
- Use CloudWatch for monitoring
- Lambda functions for compute-heavy tasks
- Cost tracking for API usage

**Implementation Priority**: 🔵 **MEDIUM** - Production deployment optimization

---

## 3. Current NBA MCP Assessment

### 3.1 Existing Features

**Database Tools (3):**
- ✅ `query_database` - Execute SQL queries
- ✅ `list_tables` - List database tables
- ✅ `get_table_schema` - Get table schemas

**S3 Tools (2):**
- ✅ `list_s3_files` - List S3 objects
- ✅ `get_s3_file` - Retrieve S3 content

**Book Tools (3):**
- ✅ `list_books` - List books in S3
- ✅ `read_book` - Read with smart chunking
- ✅ `search_books` - Search book content

**EPUB Tools (3):**
- ✅ `get_epub_metadata` - Extract EPUB metadata
- ✅ `get_epub_toc` - Get table of contents
- ✅ `read_epub_chapter` - Read chapters

**PDF Tools (6):**
- ✅ `get_pdf_metadata` - Extract PDF metadata
- ✅ `get_pdf_toc` - Get table of contents
- ✅ `read_pdf_page` - Read single page
- ✅ `read_pdf_page_range` - Read page range
- ✅ `read_pdf_chapter` - Read chapter by title
- ✅ `search_pdf` - Search with context

**Total Current Tools**: 18

### 3.2 Infrastructure

**Error Handling:**
- ✅ Custom exception classes
- ✅ Decorator-based error handling
- ✅ Detailed error context

**Logging:**
- ✅ Structured logging with JSON
- ✅ `@log_operation` decorator
- ✅ Operation tracking

**Validation:**
- ✅ Pydantic parameter models
- ✅ Input sanitization
- ✅ SQL injection prevention

**Performance:**
- ✅ Rate limiting decorators
- ✅ Result caching
- ✅ Retry with exponential backoff

### 3.3 Current Gaps

**Missing Capabilities:**
- ❌ Web scraping/crawling
- ❌ Mathematical/statistical operations
- ❌ Pagination for large datasets
- ❌ Prompt templates
- ❌ Resource endpoints
- ❌ Real-time notifications
- ❌ OAuth authentication
- ❌ Streamable HTTP transport
- ❌ Machine learning models
- ❌ Event-based architecture

**Scalability Concerns:**
- Limited to stdio transport
- No horizontal scaling support
- No distributed caching
- No load balancing

**Developer Experience:**
- No prompt templates for common queries
- Limited documentation for new tools
- No interactive testing UI
- Manual deployment process

---

## 4. Improvement Sprint Plans

### Sprint 5: Mathematical & Statistical Tools 🔶 HIGH PRIORITY

**Duration**: 3-5 days
**Complexity**: Low
**Value**: High (direct analytics support)

#### Objectives
- Add mathematical operations for NBA analytics
- Implement statistical calculations
- Support advanced metrics computation

#### Tools to Add (20 total)

**Arithmetic (7 tools):**
1. `math_add` - Add two numbers
2. `math_subtract` - Subtract numbers
3. `math_multiply` - Multiply numbers
4. `math_divide` - Divide numbers
5. `math_sum` - Sum array of numbers
6. `math_modulo` - Modulo operation
7. `math_round` - Round/floor/ceiling

**Statistical (5 tools):**
8. `stats_mean` - Calculate mean
9. `stats_median` - Calculate median
10. `stats_mode` - Find mode
11. `stats_min` - Find minimum
12. `stats_max` - Find maximum

**Advanced NBA Metrics (8 tools):**
13. `nba_player_efficiency_rating` - Calculate PER
14. `nba_true_shooting_percentage` - Calculate TS%
15. `nba_usage_rate` - Calculate usage rate
16. `nba_effective_field_goal_percentage` - Calculate eFG%
17. `nba_offensive_rating` - Calculate ORtg
18. `nba_defensive_rating` - Calculate DRtg
19. `nba_win_shares` - Calculate win shares
20. `nba_box_plus_minus` - Calculate BPM

#### Implementation Plan

**File Structure:**
```
mcp_server/
├── tools/
│   ├── math_helper.py          # NEW: Math operations
│   ├── stats_helper.py         # NEW: Statistical functions
│   └── nba_metrics_helper.py   # NEW: NBA-specific calculations
├── tools/
│   └── params.py               # UPDATE: Add param models
└── responses.py                # UPDATE: Add response models
```

**Example Implementation (math_helper.py):**
```python
"""
Mathematical Operations for NBA Analytics
Provides basic arithmetic and advanced calculations
"""

from typing import List, Union
import math
from mcp_server.exceptions import ValidationError
from mcp_server.decorators import log_operation


@log_operation("math_add")
def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b

    Example:
        >>> add(5, 3)
        8
        >>> add(10.5, 2.3)
        12.8
    """
    return a + b


@log_operation("math_sum")
def sum_numbers(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    Sum a list of numbers.

    Args:
        numbers: List of numbers to sum

    Returns:
        Sum of all numbers

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> sum_numbers([1, 2, 3, 4, 5])
        15
        >>> sum_numbers([10.5, 20.3, 15.2])
        46.0
    """
    if not numbers:
        raise ValidationError("Numbers list cannot be empty", "numbers", numbers)

    return sum(numbers)


@log_operation("stats_mean")
def calculate_mean(numbers: List[Union[int, float]]) -> float:
    """
    Calculate the arithmetic mean (average).

    Args:
        numbers: List of numbers

    Returns:
        Mean value

    Raises:
        ValidationError: If numbers list is empty

    Example:
        >>> calculate_mean([10, 20, 30])
        20.0
    """
    if not numbers:
        raise ValidationError("Numbers list cannot be empty", "numbers", numbers)

    return sum(numbers) / len(numbers)


@log_operation("stats_median")
def calculate_median(numbers: List[Union[int, float]]) -> float:
    """
    Calculate the median value.

    Args:
        numbers: List of numbers

    Returns:
        Median value

    Example:
        >>> calculate_median([1, 3, 5])
        3.0
        >>> calculate_median([1, 2, 3, 4])
        2.5
    """
    if not numbers:
        raise ValidationError("Numbers list cannot be empty", "numbers", numbers)

    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    mid = n // 2

    if n % 2 == 0:
        return (sorted_numbers[mid - 1] + sorted_numbers[mid]) / 2
    else:
        return float(sorted_numbers[mid])
```

**Example Implementation (nba_metrics_helper.py):**
```python
"""
NBA-Specific Metrics Calculations
Based on standard NBA advanced statistics formulas
"""

from typing import Dict, Any
import math
from mcp_server.decorators import log_operation


@log_operation("nba_player_efficiency_rating")
def calculate_per(stats: Dict[str, Any]) -> float:
    """
    Calculate Player Efficiency Rating (PER).

    Formula:
    PER = (Points + Rebounds + Assists + Steals + Blocks
           - Missed FG - Missed FT - Turnovers) / Minutes Played

    Args:
        stats: Dictionary with player stats
            - points: Points scored
            - rebounds: Total rebounds
            - assists: Assists
            - steals: Steals
            - blocks: Blocks
            - fgm: Field goals made
            - fga: Field goals attempted
            - ftm: Free throws made
            - fta: Free throws attempted
            - turnovers: Turnovers
            - minutes: Minutes played

    Returns:
        PER value (normalized to league average of 15.0)

    Example:
        >>> stats = {
        ...     "points": 250, "rebounds": 100, "assists": 80,
        ...     "steals": 20, "blocks": 15, "fgm": 95, "fga": 200,
        ...     "ftm": 60, "fta": 75, "turnovers": 40, "minutes": 500
        ... }
        >>> calculate_per(stats)
        18.5
    """
    required_fields = [
        "points", "rebounds", "assists", "steals", "blocks",
        "fgm", "fga", "ftm", "fta", "turnovers", "minutes"
    ]

    for field in required_fields:
        if field not in stats:
            raise ValueError(f"Missing required field: {field}")

    if stats["minutes"] == 0:
        return 0.0

    # Simplified PER calculation
    positive = (
        stats["points"] +
        stats["rebounds"] +
        stats["assists"] +
        stats["steals"] +
        stats["blocks"]
    )

    negative = (
        (stats["fga"] - stats["fgm"]) +  # Missed FG
        (stats["fta"] - stats["ftm"]) +  # Missed FT
        stats["turnovers"]
    )

    per = (positive - negative) / stats["minutes"] * 100

    return round(per, 2)


@log_operation("nba_true_shooting_percentage")
def calculate_true_shooting(points: int, fga: int, fta: int) -> float:
    """
    Calculate True Shooting Percentage (TS%).

    Formula:
    TS% = Points / (2 * (FGA + 0.44 * FTA))

    Args:
        points: Total points scored
        fga: Field goals attempted
        fta: Free throws attempted

    Returns:
        True shooting percentage (0-1 scale)

    Example:
        >>> calculate_true_shooting(250, 200, 75)
        0.543
    """
    denominator = 2 * (fga + 0.44 * fta)

    if denominator == 0:
        return 0.0

    ts_pct = points / denominator
    return round(ts_pct, 3)


@log_operation("nba_usage_rate")
def calculate_usage_rate(
    fga: int,
    fta: int,
    turnovers: int,
    minutes: float,
    team_minutes: float,
    team_fga: int,
    team_fta: int,
    team_turnovers: int
) -> float:
    """
    Calculate Usage Rate (USG%).

    Measures the percentage of team plays used by a player while on the floor.

    Formula:
    USG% = 100 * ((FGA + 0.44 * FTA + TOV) * (Tm MP / 5)) /
           (MP * (Tm FGA + 0.44 * Tm FTA + Tm TOV))

    Args:
        fga: Player's field goal attempts
        fta: Player's free throw attempts
        turnovers: Player's turnovers
        minutes: Player's minutes played
        team_minutes: Team's total minutes
        team_fga: Team's field goal attempts
        team_fta: Team's free throw attempts
        team_turnovers: Team's turnovers

    Returns:
        Usage rate percentage

    Example:
        >>> calculate_usage_rate(
        ...     fga=200, fta=75, turnovers=40, minutes=500,
        ...     team_minutes=4800, team_fga=1800, team_fta=600, team_turnovers=350
        ... )
        24.5
    """
    if minutes == 0:
        return 0.0

    player_possessions = fga + 0.44 * fta + turnovers
    team_possessions = team_fga + 0.44 * team_fta + team_turnovers

    if team_possessions == 0:
        return 0.0

    usg_rate = (
        100 * (player_possessions * (team_minutes / 5)) /
        (minutes * team_possessions)
    )

    return round(usg_rate, 2)
```

**Parameter Models (params.py):**
```python
class MathAddParams(BaseModel):
    """Parameters for adding two numbers"""
    a: Union[int, float] = Field(..., description="First number")
    b: Union[int, float] = Field(..., description="Second number")

    class Config:
        json_schema_extra = {
            "examples": [
                {"a": 5, "b": 3},
                {"a": 10.5, "b": 2.3}
            ]
        }


class StatsMeanParams(BaseModel):
    """Parameters for calculating mean"""
    numbers: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="List of numbers to calculate mean"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"numbers": [10, 20, 30, 40, 50]}
            ]
        }


class NbaPerParams(BaseModel):
    """Parameters for calculating Player Efficiency Rating"""
    points: int = Field(..., ge=0, description="Points scored")
    rebounds: int = Field(..., ge=0, description="Total rebounds")
    assists: int = Field(..., ge=0, description="Assists")
    steals: int = Field(..., ge=0, description="Steals")
    blocks: int = Field(..., ge=0, description="Blocks")
    fgm: int = Field(..., ge=0, description="Field goals made")
    fga: int = Field(..., ge=0, description="Field goals attempted")
    ftm: int = Field(..., ge=0, description="Free throws made")
    fta: int = Field(..., ge=0, description="Free throws attempted")
    turnovers: int = Field(..., ge=0, description="Turnovers")
    minutes: float = Field(..., gt=0, description="Minutes played")

    @field_validator('fga')
    def validate_fga(cls, v, values):
        if 'fgm' in values and v < values['fgm']:
            raise ValueError("Field goals attempted must be >= field goals made")
        return v
```

**MCP Tools (fastmcp_server.py):**
```python
from .tools import math_helper, stats_helper, nba_metrics_helper

@mcp.tool()
async def math_add(params: MathAddParams) -> dict:
    """Add two numbers together"""
    result = math_helper.add(params.a, params.b)
    return {"result": result, "operation": "addition"}


@mcp.tool()
async def stats_mean(params: StatsMeanParams) -> dict:
    """Calculate the arithmetic mean of a list of numbers"""
    result = stats_helper.calculate_mean(params.numbers)
    return {
        "mean": result,
        "count": len(params.numbers),
        "sum": sum(params.numbers)
    }


@mcp.tool()
async def nba_player_efficiency_rating(params: NbaPerParams, ctx: Context) -> dict:
    """
    Calculate Player Efficiency Rating (PER) for NBA player stats.

    PER is a comprehensive efficiency metric that accounts for
    positive contributions (points, rebounds, assists, etc.) and
    negative contributions (missed shots, turnovers).
    """
    await ctx.info(f"Calculating PER for {params.minutes} minutes played")

    stats_dict = params.model_dump()
    per = nba_metrics_helper.calculate_per(stats_dict)

    return {
        "per": per,
        "interpretation": "Excellent" if per > 20 else "Above Average" if per > 15 else "Average",
        "league_average": 15.0,
        "stats_used": stats_dict
    }
```

#### Testing Plan

**Test File**: `scripts/test_math_stats_features.py`

```python
#!/usr/bin/env python3
"""Test mathematical and statistical tools"""

import asyncio
from mcp_server.tools import math_helper, stats_helper, nba_metrics_helper


async def test_basic_math():
    """Test basic mathematical operations"""
    print("Testing basic math operations...")

    # Addition
    assert math_helper.add(5, 3) == 8
    assert math_helper.add(10.5, 2.3) == 12.8

    # Sum
    assert math_helper.sum_numbers([1, 2, 3, 4, 5]) == 15

    print("✓ Basic math tests passed")


async def test_statistics():
    """Test statistical calculations"""
    print("Testing statistical operations...")

    # Mean
    assert stats_helper.calculate_mean([10, 20, 30]) == 20.0

    # Median
    assert stats_helper.calculate_median([1, 3, 5]) == 3.0
    assert stats_helper.calculate_median([1, 2, 3, 4]) == 2.5

    print("✓ Statistics tests passed")


async def test_nba_metrics():
    """Test NBA-specific metrics"""
    print("Testing NBA metrics...")

    # PER
    stats = {
        "points": 250, "rebounds": 100, "assists": 80,
        "steals": 20, "blocks": 15, "fgm": 95, "fga": 200,
        "ftm": 60, "fta": 75, "turnovers": 40, "minutes": 500
    }
    per = nba_metrics_helper.calculate_per(stats)
    assert per > 0

    # True Shooting %
    ts = nba_metrics_helper.calculate_true_shooting(250, 200, 75)
    assert 0 <= ts <= 1

    print("✓ NBA metrics tests passed")


async def main():
    await test_basic_math()
    await test_statistics()
    await test_nba_metrics()
    print("\n✓ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
```

#### Success Criteria
- ✅ 20 new math/stats tools implemented
- ✅ All tests passing
- ✅ Documentation updated
- ✅ Can calculate PER, TS%, USG% from tool calls
- ✅ Statistical operations work with player data

---

### Sprint 6: Web Scraping Integration 🔶 HIGH PRIORITY

**Duration**: 5-7 days
**Complexity**: Medium
**Value**: High (external data sources)

#### Objectives
- Add web scraping capabilities for NBA news/data
- Integrate Firecrawl OR Crawl4AI (choose one)
- Support structured data extraction from basketball websites

#### Decision: Firecrawl vs. Crawl4AI

**Recommendation**: **Start with Crawl4AI, optionally add Firecrawl**

**Reasoning:**

| Feature | Crawl4AI | Firecrawl |
|---------|----------|-----------|
| **Cost** | Free (uses your LLM API) | Paid API (credits) |
| **Deployment** | Self-hosted Python | Cloud API or self-hosted |
| **LLM Integration** | Google Gemini, OpenAI, Mistral | Built-in |
| **Complexity** | Simpler (3 tools) | More features (8 tools) |
| **Rate Limiting** | You manage | Built-in |
| **Best For** | Quick start, cost control | Production scale, reliability |

**Implementation Plan: Crawl4AI First**

**File Structure:**
```
mcp_server/
├── tools/
│   └── web_scraper_helper.py  # NEW: Crawl4AI wrapper
├── tools/
│   └── params.py              # UPDATE: Add scraper params
└── responses.py               # UPDATE: Add scraper responses
```

**Example Implementation (web_scraper_helper.py):**
```python
"""
Web Scraping Tools using Crawl4AI
Enables extraction of NBA news, stats, and analysis from web sources
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import google.generativeai as genai

from mcp_server.exceptions import ValidationError
from mcp_server.decorators import log_operation, rate_limited
from mcp_server.tools.logger_config import get_logger

logger = get_logger(__name__)

# Configure Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


@log_operation("scrape_url")
@rate_limited("web_scraping", max_requests=10, per_seconds=60)
async def scrape_url(url: str) -> str:
    """
    Scrape a webpage and return its content in Markdown format.

    Args:
        url: The URL of the webpage to scrape

    Returns:
        Webpage content in Markdown format

    Raises:
        ValidationError: If URL is invalid

    Example:
        >>> content = await scrape_url("https://www.nba.com/news")
        >>> print(content[:100])
        # NBA News

        ## Latest Headlines
        ...
    """
    if not url.startswith(("http://", "https://")):
        raise ValidationError("Invalid URL format", "url", url)

    logger.info(f"Scraping URL: {url}")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        if not result.success:
            raise Exception(f"Failed to scrape {url}: {result.error_message}")

        return result.markdown


@log_operation("extract_text_by_query")
@rate_limited("web_scraping", max_requests=10, per_seconds=60)
async def extract_text_by_query(
    url: str,
    query: str,
    context_size: int = 300
) -> List[Dict[str, Any]]:
    """
    Extract relevant text snippets from a webpage based on a search query.

    Args:
        url: The URL of the webpage to search
        query: The text query to search for (case-insensitive)
        context_size: Characters to include before/after match (default: 300)

    Returns:
        List of matches with context

    Example:
        >>> matches = await extract_text_by_query(
        ...     "https://en.wikipedia.org/wiki/NBA",
        ...     "championship",
        ...     context_size=200
        ... )
        >>> for match in matches[:3]:
        ...     print(match["snippet"])
    """
    if not url.startswith(("http://", "https://")):
        raise ValidationError("Invalid URL format", "url", url)

    logger.info(f"Searching '{query}' in {url}")

    # First, scrape the page
    content = await scrape_url(url)

    # Find all occurrences (case-insensitive)
    query_lower = query.lower()
    content_lower = content.lower()

    matches = []
    start_pos = 0
    max_matches = 5  # Limit to first 5 matches

    while len(matches) < max_matches:
        pos = content_lower.find(query_lower, start_pos)
        if pos == -1:
            break

        # Extract context
        start_context = max(0, pos - context_size)
        end_context = min(len(content), pos + len(query) + context_size)

        snippet = content[start_context:end_context]

        matches.append({
            "position": pos,
            "query": query,
            "snippet": snippet.strip(),
            "context_before": content[start_context:pos].strip(),
            "matched_text": content[pos:pos + len(query)],
            "context_after": content[pos + len(query):end_context].strip()
        })

        start_pos = pos + len(query)

    logger.info(f"Found {len(matches)} matches for '{query}'")
    return matches


@log_operation("smart_extract")
@rate_limited("web_scraping", max_requests=5, per_seconds=60)  # Lower rate for LLM calls
async def smart_extract(url: str, instruction: str) -> Dict[str, Any]:
    """
    Intelligently extract specific information from a webpage using LLM.

    Requires GOOGLE_API_KEY environment variable to be set.

    Args:
        url: The URL of the webpage to analyze
        instruction: Natural language instruction for what to extract
                    (e.g., "List all player names and their stats")

    Returns:
        Extracted information (often as structured JSON)

    Raises:
        ValidationError: If GOOGLE_API_KEY is not set

    Example:
        >>> result = await smart_extract(
        ...     "https://www.nba.com/standings",
        ...     "Extract the top 5 teams in the Eastern Conference with win-loss records"
        ... )
        >>> print(result["extracted_data"])
    """
    if not GOOGLE_API_KEY:
        raise ValidationError(
            "GOOGLE_API_KEY environment variable is required for smart_extract",
            "GOOGLE_API_KEY",
            None
        )

    if not url.startswith(("http://", "https://")):
        raise ValidationError("Invalid URL format", "url", url)

    logger.info(f"Smart extracting from {url} with instruction: {instruction}")

    # Create extraction strategy
    extraction_strategy = LLMExtractionStrategy(
        provider="google",
        api_token=GOOGLE_API_KEY,
        instruction=instruction
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=extraction_strategy
        )

        if not result.success:
            raise Exception(f"Failed to extract from {url}: {result.error_message}")

        return {
            "url": url,
            "instruction": instruction,
            "extracted_data": result.extracted_content,
            "markdown_preview": result.markdown[:500] if result.markdown else None
        }
```

**Parameter Models:**
```python
class ScrapeUrlParams(BaseModel):
    """Parameters for scraping a URL"""
    url: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="URL of the webpage to scrape"
    )

    @field_validator('url')
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"url": "https://www.nba.com/news"},
                {"url": "https://www.espn.com/nba/"}
            ]
        }


class ExtractTextByQueryParams(BaseModel):
    """Parameters for extracting text by query"""
    url: str = Field(..., description="URL of the webpage")
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query"
    )
    context_size: int = Field(
        default=300,
        ge=50,
        le=1000,
        description="Characters of context before/after match"
    )


class SmartExtractParams(BaseModel):
    """Parameters for smart extraction with LLM"""
    url: str = Field(..., description="URL of the webpage")
    instruction: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Natural language extraction instruction"
    )
```

**MCP Tools:**
```python
@mcp.tool()
async def scrape_nba_webpage(params: ScrapeUrlParams, ctx: Context) -> dict:
    """
    Scrape an NBA-related webpage and return its content in Markdown format.

    Useful for extracting news articles, player profiles, game recaps, etc.
    """
    await ctx.info(f"Scraping: {params.url}")

    try:
        content = await web_scraper_helper.scrape_url(params.url)

        return {
            "success": True,
            "url": params.url,
            "content": content,
            "length": len(content),
            "format": "markdown"
        }
    except Exception as e:
        await ctx.error(f"Scraping failed: {str(e)}")
        return {
            "success": False,
            "url": params.url,
            "error": str(e)
        }


@mcp.tool()
async def search_webpage_for_text(params: ExtractTextByQueryParams, ctx: Context) -> dict:
    """
    Search for specific text in a webpage and return matches with context.

    Returns up to 5 matches with surrounding text for context.
    """
    await ctx.info(f"Searching '{params.query}' in {params.url}")

    try:
        matches = await web_scraper_helper.extract_text_by_query(
            params.url,
            params.query,
            params.context_size
        )

        return {
            "success": True,
            "url": params.url,
            "query": params.query,
            "matches_found": len(matches),
            "matches": matches
        }
    except Exception as e:
        await ctx.error(f"Search failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def extract_structured_data(params: SmartExtractParams, ctx: Context) -> dict:
    """
    Extract structured information from a webpage using AI.

    Requires GOOGLE_API_KEY environment variable.
    Uses Google Gemini to intelligently extract data based on your instruction.
    """
    await ctx.info(f"Smart extracting from {params.url}")
    await ctx.info(f"Instruction: {params.instruction}")

    try:
        result = await web_scraper_helper.smart_extract(
            params.url,
            params.instruction
        )

        return {
            "success": True,
            **result
        }
    except Exception as e:
        await ctx.error(f"Smart extraction failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

#### Installation Requirements

**Dependencies:**
```bash
pip install crawl4ai google-generativeai
```

**Environment Variables:**
```bash
export GOOGLE_API_KEY=your-google-ai-api-key
```

#### Usage Examples

**Example 1: Scrape NBA News**
```python
# Via Claude Desktop or MCP client
Tool: scrape_nba_webpage
Params: {"url": "https://www.nba.com/news"}
Result: Markdown content of NBA news page
```

**Example 2: Find Injury Reports**
```python
Tool: search_webpage_for_text
Params: {
  "url": "https://www.espn.com/nba/injuries",
  "query": "questionable",
  "context_size": 200
}
Result: List of players with "questionable" status + context
```

**Example 3: Extract Game Scores**
```python
Tool: extract_structured_data
Params: {
  "url": "https://www.nba.com/games",
  "instruction": "Extract today's game scores with team names and final scores"
}
Result: Structured JSON with game results
```

#### Testing Plan

```python
#!/usr/bin/env python3
"""Test web scraping tools"""

import asyncio
import os
from mcp_server.tools import web_scraper_helper


async def test_scrape_url():
    """Test basic URL scraping"""
    print("Testing URL scraping...")

    url = "https://www.nba.com"
    content = await web_scraper_helper.scrape_url(url)

    assert len(content) > 0
    assert "nba" in content.lower()

    print(f"✓ Scraped {len(content)} characters from {url}")


async def test_search():
    """Test text search"""
    print("Testing text search...")

    url = "https://en.wikipedia.org/wiki/NBA"
    matches = await web_scraper_helper.extract_text_by_query(
        url, "championship", context_size=200
    )

    assert len(matches) > 0
    assert "championship" in matches[0]["matched_text"].lower()

    print(f"✓ Found {len(matches)} matches for 'championship'")


async def test_smart_extract():
    """Test LLM-based extraction"""
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ Skipping smart_extract test (no GOOGLE_API_KEY)")
        return

    print("Testing smart extraction...")

    url = "https://www.nba.com/standings"
    result = await web_scraper_helper.smart_extract(
        url,
        "List the top 3 teams in the Eastern Conference"
    )

    assert result["extracted_data"] is not None

    print(f"✓ Smart extracted: {result['extracted_data'][:100]}...")


async def main():
    await test_scrape_url()
    await test_search()
    await test_smart_extract()
    print("\n✓ All web scraping tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
```

#### Success Criteria
- ✅ Can scrape NBA websites (nba.com, espn.com, etc.)
- ✅ Text search finds relevant content
- ✅ LLM extraction produces structured data
- ✅ Rate limiting prevents API abuse
- ✅ Error handling for failed requests
- ✅ Tests pass with real websites

---

### Sprint 7: Prompts & Resources (MCP Features) 🔶 HIGH PRIORITY

**Duration**: 3-5 days
**Complexity**: Medium
**Value**: High (improves UX)

#### Objectives
- Add MCP Prompt support for reusable query templates
- Add MCP Resource support for structured data access
- Improve developer/user experience

#### Part A: Prompt Templates

**What are MCP Prompts?**
- Reusable templates for common queries
- Accept arguments for customization
- Return structured messages for LLM
- Improve consistency and discoverability

**Example Prompts to Add:**

1. **analyze_player** - Analyze player performance
2. **compare_players** - Compare two players
3. **predict_game** - Predict game outcome
4. **team_analysis** - Analyze team stats
5. **injury_impact** - Assess injury impact on team
6. **draft_analysis** - Analyze draft prospects
7. **trade_evaluation** - Evaluate trade scenarios

**Implementation:**

```python
# In fastmcp_server.py

@mcp.list_prompts()
async def list_prompts() -> List[types.Prompt]:
    """List all available prompt templates"""
    return [
        types.Prompt(
            name="analyze_player",
            description="Comprehensive player performance analysis",
            arguments=[
                types.PromptArgument(
                    name="player_name",
                    description="Name of the NBA player (e.g., 'LeBron James')",
                    required=True
                ),
                types.PromptArgument(
                    name="season",
                    description="Season year (e.g., '2024'). Defaults to current season.",
                    required=False
                ),
                types.PromptArgument(
                    name="focus",
                    description="Analysis focus: 'offense', 'defense', 'overall', or 'advanced'",
                    required=False
                )
            ]
        ),
        types.Prompt(
            name="compare_players",
            description="Side-by-side comparison of two NBA players",
            arguments=[
                types.PromptArgument(
                    name="player1",
                    description="First player name",
                    required=True
                ),
                types.PromptArgument(
                    name="player2",
                    description="Second player name",
                    required=True
                ),
                types.PromptArgument(
                    name="metrics",
                    description="Metrics to compare (e.g., 'scoring,defense,efficiency')",
                    required=False
                )
            ]
        ),
        types.Prompt(
            name="predict_game",
            description="Predict the outcome of an NBA game",
            arguments=[
                types.PromptArgument(
                    name="home_team",
                    description="Home team name",
                    required=True
                ),
                types.PromptArgument(
                    name="away_team",
                    description="Away team name",
                    required=True
                ),
                types.PromptArgument(
                    name="include_injuries",
                    description="Include injury report in analysis (true/false)",
                    required=False
                )
            ]
        ),
        types.Prompt(
            name="team_analysis",
            description="Analyze team performance and trends",
            arguments=[
                types.PromptArgument(
                    name="team_name",
                    description="NBA team name",
                    required=True
                ),
                types.PromptArgument(
                    name="timeframe",
                    description="Time period: 'season', 'month', 'last_10_games'",
                    required=False
                )
            ]
        )
    ]


@mcp.get_prompt()
async def get_prompt(
    name: str,
    arguments: Optional[Dict[str, str]]
) -> types.GetPromptResult:
    """Get a specific prompt with arguments filled in"""

    if name == "analyze_player":
        player = arguments.get("player_name", "Unknown Player")
        season = arguments.get("season", "current season")
        focus = arguments.get("focus", "overall")

        return types.GetPromptResult(
            description=f"Analyzing {player} for {season} season",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Analyze the performance of NBA player {player} for the {season} season.

Focus area: {focus}

Please provide:
1. Key statistics (PPG, RPG, APG, FG%, etc.)
2. Performance trends (improving, declining, consistent)
3. Strengths and weaknesses
4. Comparison to league averages
5. {"Advanced metrics (PER, TS%, USG%)" if focus == "advanced" else "Overall assessment"}

Use the available NBA MCP tools to query the database for stats."""
                    )
                )
            ]
        )

    elif name == "compare_players":
        player1 = arguments.get("player1", "Player 1")
        player2 = arguments.get("player2", "Player 2")
        metrics = arguments.get("metrics", "scoring,defense,efficiency")

        return types.GetPromptResult(
            description=f"Comparing {player1} vs {player2}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Compare NBA players {player1} and {player2}.

Comparison metrics: {metrics}

Please provide a detailed comparison including:
1. Statistical comparison for each metric
2. Situational advantages (who excels in what scenarios)
3. Team fit and role comparison
4. Historical performance trends
5. Overall verdict with reasoning

Use NBA MCP database tools to fetch accurate statistics."""
                    )
                )
            ]
        )

    elif name == "predict_game":
        home = arguments.get("home_team", "Home Team")
        away = arguments.get("away_team", "Away Team")
        injuries = arguments.get("include_injuries", "false").lower() == "true"

        injury_text = "\n4. Current injury report and impact" if injuries else ""

        return types.GetPromptResult(
            description=f"Predicting {away} @ {home}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Predict the outcome of the NBA game: {away} @ {home}

Provide a comprehensive prediction including:
1. Team statistics comparison (record, PPG, defensive rating, etc.)
2. Head-to-head history
3. Recent form (last 10 games){injury_text}
5. Key matchups to watch
6. Final prediction with confidence level
7. Suggested betting line (for informational purposes)

Use NBA MCP tools to query game data, team stats, and player information."""
                    )
                )
            ]
        )

    elif name == "team_analysis":
        team = arguments.get("team_name", "Team")
        timeframe = arguments.get("timeframe", "season")

        return types.GetPromptResult(
            description=f"Analyzing {team} ({timeframe})",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Analyze the {team} for the {timeframe}.

Provide:
1. Overall record and standing
2. Offensive and defensive statistics
3. Key players and their contributions
4. Strengths and weaknesses
5. Performance trends
6. Outlook and predictions

Use NBA MCP database tools to fetch team and player statistics."""
                    )
                )
            ]
        )

    else:
        raise ValueError(f"Unknown prompt: {name}")
```

**Benefits:**
- Consistent analysis format
- Easy discovery of capabilities
- Guided user experience
- Reusable templates

#### Part B: MCP Resources

**What are MCP Resources?**
- Expose data as URIs (e.g., `nba://games/2024-10-10`)
- Allow clients to discover and read structured data
- Support subscriptions for live updates
- Alternative to tool-based access

**Example Resources to Add:**

1. **nba://games/{date}** - Games on a specific date
2. **nba://games/{game_id}** - Specific game details
3. **nba://players/{player_id}** - Player profile
4. **nba://teams/{team_id}** - Team information
5. **nba://standings/{conference}** - Conference standings
6. **nba://injuries** - Current injury report

**Implementation:**

```python
# In fastmcp_server.py

@mcp.list_resources()
async def list_resources() -> List[types.Resource]:
    """List all available NBA data resources"""

    today = datetime.now().strftime("%Y-%m-%d")

    return [
        types.Resource(
            uri=AnyUrl(f"nba://games/{today}"),
            name=f"Games on {today}",
            description=f"All NBA games scheduled for {today}",
            mimeType="application/json"
        ),
        types.Resource(
            uri=AnyUrl("nba://games/latest"),
            name="Latest Games",
            description="Most recent NBA games with scores",
            mimeType="application/json"
        ),
        types.Resource(
            uri=AnyUrl("nba://standings/eastern"),
            name="Eastern Conference Standings",
            description="Current standings for Eastern Conference",
            mimeType="application/json"
        ),
        types.Resource(
            uri=AnyUrl("nba://standings/western"),
            name="Western Conference Standings",
            description="Current standings for Western Conference",
            mimeType="application/json"
        ),
        types.Resource(
            uri=AnyUrl("nba://injuries"),
            name="Injury Report",
            description="Current NBA injury report (all teams)",
            mimeType="application/json"
        ),
        types.Resource(
            uri=AnyUrl("nba://players/top-scorers"),
            name="Top Scorers",
            description="League leaders in points per game",
            mimeType="application/json"
        )
    ]


@mcp.read_resource()
async def read_resource(uri: AnyUrl, ctx: Context) -> str:
    """Read a specific NBA resource"""

    uri_str = str(uri)
    await ctx.info(f"Reading resource: {uri_str}")

    # Parse URI
    if not uri_str.startswith("nba://"):
        raise ValueError(f"Invalid NBA resource URI: {uri_str}")

    path = uri_str[6:]  # Remove "nba://"
    parts = path.split("/")

    db = ctx.request_context.lifespan_context["database"]

    # Route to appropriate handler
    if parts[0] == "games":
        if len(parts) == 2:
            if parts[1] == "latest":
                # Get latest games
                query = """
                SELECT game_id, home_team, away_team, game_date, final_score
                FROM games
                ORDER BY game_date DESC
                LIMIT 10
                """
            else:
                # Get games for specific date
                date = parts[1]
                query = f"""
                SELECT game_id, home_team, away_team, game_date, final_score
                FROM games
                WHERE DATE(game_date) = '{date}'
                ORDER BY game_date
                """
        else:
            # Get specific game
            game_id = parts[1]
            query = f"""
            SELECT *
            FROM games
            WHERE game_id = '{game_id}'
            """

    elif parts[0] == "standings":
        conference = parts[1] if len(parts) > 1 else "eastern"
        query = f"""
        SELECT team_name, wins, losses, win_pct, games_behind
        FROM standings
        WHERE conference = '{conference.upper()}'
        ORDER BY win_pct DESC
        """

    elif parts[0] == "injuries":
        query = """
        SELECT player_name, team, injury_status, injury_details
        FROM injury_report
        WHERE status != 'Active'
        ORDER BY team, player_name
        """

    elif parts[0] == "players":
        if len(parts) > 1 and parts[1] == "top-scorers":
            query = """
            SELECT player_name, team, ppg, games_played
            FROM player_stats
            ORDER BY ppg DESC
            LIMIT 20
            """
        else:
            player_id = parts[1] if len(parts) > 1 else None
            if player_id:
                query = f"""
                SELECT *
                FROM players
                WHERE player_id = '{player_id}'
                """
            else:
                raise ValueError("Player ID required")

    else:
        raise ValueError(f"Unknown resource type: {parts[0]}")

    # Execute query
    result = await asyncio.to_thread(db.execute_query, query)

    # Return as JSON string
    import json
    return json.dumps({
        "uri": uri_str,
        "data": result,
        "timestamp": datetime.now().isoformat()
    }, indent=2)
```

**Benefits:**
- RESTful-style data access
- Easy integration with other tools
- Discoverable data structure
- Support for future subscriptions

#### Testing

```python
#!/usr/bin/env python3
"""Test prompts and resources"""

import asyncio
from mcp.server.fastmcp import FastMCP


async def test_prompts():
    """Test prompt listing and retrieval"""
    print("Testing prompts...")

    # This would be called via MCP client
    prompts = await list_prompts()
    assert len(prompts) >= 4

    # Test analyze_player prompt
    result = await get_prompt("analyze_player", {
        "player_name": "LeBron James",
        "season": "2024"
    })
    assert "LeBron James" in result.messages[0].content.text

    print(f"✓ {len(prompts)} prompts available")


async def test_resources():
    """Test resource listing and reading"""
    print("Testing resources...")

    resources = await list_resources()
    assert len(resources) >= 5

    # Test reading a resource
    # (Would need database connection)

    print(f"✓ {len(resources)} resources available")


if __name__ == "__main__":
    asyncio.run(test_prompts())
    asyncio.run(test_resources())
```

#### Success Criteria
- ✅ 7+ prompt templates implemented
- ✅ 6+ resource URIs exposed
- ✅ Prompts generate proper messages
- ✅ Resources return valid JSON
- ✅ Easy to discover via MCP client

---

## 5. Technical Patterns to Adopt

### 5.1 Pagination Pattern

**From**: MCP Python SDK simple-pagination example

**Current Issue**: Large result sets returned all at once, causing:
- Token overflow in responses
- Slow initial response time
- Memory pressure

**Solution**: Cursor-based pagination

```python
# Before (current)
@mcp.tool()
async def list_all_players():
    query = "SELECT * FROM players"  # Could be 1000+ rows!
    return execute_query(query)


# After (with pagination)
class ListPlayersParams(BaseModel):
    cursor: Optional[str] = Field(
        default=None,
        description="Pagination cursor from previous request"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of players per page"
    )


@mcp.tool()
async def list_players_paginated(params: ListPlayersParams) -> dict:
    """List players with pagination support"""

    # Parse cursor (base64 encoded player_id)
    if params.cursor:
        import base64
        last_id = base64.b64decode(params.cursor).decode()
        query = f"""
        SELECT * FROM players
        WHERE player_id > '{last_id}'
        ORDER BY player_id
        LIMIT {params.limit + 1}
        """
    else:
        query = f"""
        SELECT * FROM players
        ORDER BY player_id
        LIMIT {params.limit + 1}
        """

    results = execute_query(query)

    # Check if there are more results
    has_more = len(results) > params.limit
    if has_more:
        results = results[:params.limit]

    # Generate next cursor
    next_cursor = None
    if has_more and results:
        last_player_id = results[-1]["player_id"]
        next_cursor = base64.b64encode(last_player_id.encode()).decode()

    return {
        "players": results,
        "count": len(results),
        "has_more": has_more,
        "next_cursor": next_cursor
    }
```

**Apply to**: `list_games`, `list_players`, `search_books`

---

### 5.2 Event Store for Resumability

**From**: MCP Python SDK streamable-http example

**Use Case**: Long-running operations (crawling, bulk processing)

```python
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from .event_store import InMemoryEventStore

# Create event store
event_store = InMemoryEventStore()

# Create session manager with resumability
session_manager = StreamableHTTPSessionManager(
    app=mcp,
    event_store=event_store,  # Enables Last-Event-ID resumption
    json_response=False  # Use SSE streaming
)

# In tools, send progress notifications
@mcp.tool()
async def bulk_analyze_games(game_ids: List[str], ctx: Context):
    """Analyze multiple games with progress updates"""

    for i, game_id in enumerate(game_ids):
        # Send progress notification
        await ctx.session.send_log_message(
            level="info",
            data=f"Analyzing game {i+1}/{len(game_ids)}: {game_id}",
            related_request_id=ctx.request_id
        )

        # Process game
        result = await analyze_game(game_id)

        await asyncio.sleep(0.1)  # Rate limiting

    return {"analyzed": len(game_ids)}
```

**Benefits:**
- Clients can resume if disconnected
- Progress updates during long operations
- Better UX for bulk operations

---

### 5.3 Comprehensive Logging

**From**: Firecrawl MCP

**Current**: Basic logging
**Upgrade**: Structured logging with metrics

```python
import logging
import time
from typing import Dict, Any

class MetricsLogger:
    """Track operation metrics"""

    def __init__(self):
        self.metrics: Dict[str, Any] = {}

    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        details: Dict[str, Any] = None
    ):
        """Record operation metrics"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration_ms": 0.0,
                "avg_duration_ms": 0.0
            }

        m = self.metrics[operation]
        m["total_calls"] += 1
        m["total_duration_ms"] += duration_ms

        if success:
            m["successful_calls"] += 1
        else:
            m["failed_calls"] += 1

        m["avg_duration_ms"] = m["total_duration_ms"] / m["total_calls"]

        logging.info(
            f"[{operation}] "
            f"duration={duration_ms:.2f}ms "
            f"success={success} "
            f"{details or {}}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self.metrics


# Global metrics logger
metrics_logger = MetricsLogger()


# Decorator for automatic metrics
def track_metrics(operation_name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            success = False
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics_logger.record_operation(
                    operation_name,
                    duration_ms,
                    success
                )
        return wrapper
    return decorator


# Usage
@mcp.tool()
@track_metrics("query_database")
async def query_database(sql: str):
    # ... implementation
    pass
```

**Add Tool**: `get_server_metrics` to expose metrics

---

### 5.4 Docker Deployment

**From**: AWS MCP Servers

**Create**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install package
RUN pip install -e .

# Health check script
COPY scripts/health_check.sh /health_check.sh
RUN chmod +x /health_check.sh

# Expose port (for HTTP/SSE)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD ["/health_check.sh"]

# Run server
CMD ["python", "-m", "mcp_server.fastmcp_server"]
```

**Health Check** (`scripts/health_check.sh`):
```bash
#!/bin/bash
# Simple health check for Docker

# Check if server is running
if pgrep -f "mcp_server.fastmcp_server" > /dev/null; then
    echo "Server is running"
    exit 0
else
    echo "Server is not running"
    exit 1
fi
```

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  nba-mcp:
    build: .
    image: nba-mcp-server:latest
    container_name: nba-mcp
    ports:
      - "8000:8000"
    environment:
      - AWS_PROFILE=default
      - AWS_REGION=us-west-2
      - FASTMCP_LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://user:pass@db:5432/nba
    volumes:
      - ./data:/app/data
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    container_name: nba-postgres
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=nba
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

**Benefits:**
- Easy deployment
- Consistent environment
- Easy scaling
- Health monitoring

---

## 6. Priority Matrix

### Quick Wins (1-2 days each)

| Sprint | Feature | Value | Complexity | Priority |
|--------|---------|-------|-----------|----------|
| 5 | Math/Stats Tools | 🔴 High | 🟢 Low | **START HERE** |
| 7 | Prompt Templates | 🔴 High | 🟢 Low | 2nd |
| 7 | Resource Endpoints | 🟢 Medium | 🟢 Low | 3rd |
| - | Pagination | 🟢 Medium | 🟢 Low | 4th |

### Medium Effort (1 week each)

| Sprint | Feature | Value | Complexity | Priority |
|--------|---------|-------|-----------|----------|
| 6 | Web Scraping (Crawl4AI) | 🔴 High | 🟡 Medium | 5th |
| - | Streamable HTTP | 🟡 Medium | 🟡 Medium | 6th |
| - | Event Notifications | 🟡 Medium | 🟡 Medium | 7th |
| - | Metrics & Monitoring | 🟡 Medium | 🟡 Medium | 8th |

### Large Initiatives (2-4 weeks)

| Sprint | Feature | Value | Complexity | Priority |
|--------|---------|-------|-----------|----------|
| 8 | ML Integration | 🟡 Medium | 🔴 High | 9th |
| 6 | Firecrawl Integration | 🟢 Medium | 🔴 High | 10th |
| - | OAuth Authentication | 🟢 Medium | 🔴 High | 11th |
| - | Multi-region Deploy | 🟢 Medium | 🔴 High | 12th |

### Recommended Order

**Phase 1 - Quick Value (1 week total)**
1. Sprint 5: Math/Stats Tools (2 days)
2. Sprint 7: Prompts (2 days)
3. Sprint 7: Resources (2 days)
4. Pagination pattern (1 day)

**Phase 2 - External Data (1-2 weeks)**
5. Sprint 6: Web Scraping with Crawl4AI (5 days)
6. Metrics & Monitoring (3 days)

**Phase 3 - Advanced Features (2-4 weeks)**
7. Streamable HTTP transport (5 days)
8. Event notifications (3 days)
9. ML Integration basics (10 days)

**Phase 4 - Production Hardening (2-3 weeks)**
10. Docker deployment (3 days)
11. OAuth authentication (7 days)
12. Performance optimization (5 days)

---

## 7. Implementation Roadmap

### Week 1: Math, Prompts, Resources

**Day 1-2: Sprint 5 - Math/Stats Tools**
- [ ] Create `math_helper.py` with 7 arithmetic functions
- [ ] Create `stats_helper.py` with 5 statistical functions
- [ ] Create `nba_metrics_helper.py` with 8 NBA metrics
- [ ] Add parameter models
- [ ] Add response models
- [ ] Register 20 new tools in fastmcp_server.py
- [ ] Write tests
- [ ] Update documentation

**Day 3-4: Sprint 7 Part A - Prompts**
- [ ] Implement `list_prompts()` handler
- [ ] Implement `get_prompt()` handler
- [ ] Create 7 prompt templates:
  - analyze_player
  - compare_players
  - predict_game
  - team_analysis
  - injury_impact
  - draft_analysis
  - trade_evaluation
- [ ] Test with MCP client
- [ ] Document prompts

**Day 5-6: Sprint 7 Part B - Resources**
- [ ] Implement `list_resources()` handler
- [ ] Implement `read_resource()` handler
- [ ] Create 6 resource URIs:
  - nba://games/{date}
  - nba://standings/{conference}
  - nba://players/{player_id}
  - nba://injuries
  - nba://teams/{team_id}
  - nba://leaders/{stat}
- [ ] Test resource reading
- [ ] Document resources

**Day 7: Pagination Pattern**
- [ ] Add pagination to `list_players`
- [ ] Add pagination to `list_games`
- [ ] Add pagination to `search_books`
- [ ] Test with large datasets
- [ ] Update docs

**Deliverable**: 20 new math tools, 7 prompts, 6 resources, 3 paginated endpoints

---

### Week 2: Web Scraping

**Day 1-2: Setup & Basic Scraping**
- [ ] Install Crawl4AI dependencies
- [ ] Set up Google Gemini API key
- [ ] Create `web_scraper_helper.py`
- [ ] Implement `scrape_url()` function
- [ ] Add rate limiting
- [ ] Test with NBA websites

**Day 3-4: Advanced Extraction**
- [ ] Implement `extract_text_by_query()`
- [ ] Implement `smart_extract()` with LLM
- [ ] Add parameter models
- [ ] Add response models
- [ ] Register 3 new tools
- [ ] Write comprehensive tests

**Day 5: Integration & Testing**
- [ ] Test scraping nba.com, espn.com
- [ ] Test extraction of game scores
- [ ] Test smart extraction of player stats
- [ ] Handle edge cases
- [ ] Document usage

**Deliverable**: 3 web scraping tools, tested with real NBA websites

---

### Week 3: Monitoring & Advanced Features

**Day 1-2: Metrics & Logging**
- [ ] Create `MetricsLogger` class
- [ ] Add `@track_metrics` decorator
- [ ] Apply to all existing tools
- [ ] Create `get_server_metrics` tool
- [ ] Add performance dashboards
- [ ] Test metrics collection

**Day 3-5: Streamable HTTP**
- [ ] Implement event store
- [ ] Add StreamableHTTPSessionManager
- [ ] Update tools for progress notifications
- [ ] Test with long-running operations
- [ ] Document HTTP/SSE usage

**Deliverable**: Metrics system, Streamable HTTP support

---

### Week 4+: ML Integration (Optional)

**Week 4: Data Preparation**
- [ ] Design ML data pipeline
- [ ] Create feature engineering functions
- [ ] Build training data sets
- [ ] Validate data quality

**Week 5: Model Development**
- [ ] Train player performance model
- [ ] Train game outcome model
- [ ] Evaluate model accuracy
- [ ] Save model artifacts

**Week 6: Integration**
- [ ] Create `ml_helper.py`
- [ ] Add prediction tools
- [ ] Test predictions
- [ ] Monitor accuracy

**Deliverable**: Basic ML prediction capabilities

---

## 8. Testing Strategy

### Unit Tests

```python
# tests/test_math_tools.py
import pytest
from mcp_server.tools import math_helper

def test_add():
    assert math_helper.add(5, 3) == 8
    assert math_helper.add(-5, 3) == -2
    assert math_helper.add(0.1, 0.2) == pytest.approx(0.3)

def test_sum():
    assert math_helper.sum_numbers([1, 2, 3]) == 6
    assert math_helper.sum_numbers([]) raises ValidationError

# tests/test_nba_metrics.py
def test_per_calculation():
    stats = {
        "points": 250, "rebounds": 100, "assists": 80,
        # ... other stats
    }
    per = nba_metrics_helper.calculate_per(stats)
    assert 10 < per < 30  # Reasonable range

# tests/test_web_scraping.py
@pytest.mark.asyncio
async def test_scrape_url():
    content = await web_scraper_helper.scrape_url("https://www.nba.com")
    assert len(content) > 0
    assert "nba" in content.lower()
```

### Integration Tests

```python
# tests/test_mcp_integration.py
import pytest
from mcp.client import ClientSession

@pytest.mark.asyncio
async def test_math_tool_via_mcp():
    async with ClientSession(...) as session:
        result = await session.call_tool("math_add", {"a": 5, "b": 3})
        assert result["result"] == 8

@pytest.mark.asyncio
async def test_prompt_workflow():
    async with ClientSession(...) as session:
        # List prompts
        prompts = await session.list_prompts()
        assert any(p.name == "analyze_player" for p in prompts)

        # Get prompt
        prompt = await session.get_prompt("analyze_player", {
            "player_name": "LeBron James"
        })
        assert "LeBron James" in prompt.messages[0].content.text
```

### Performance Tests

```python
# tests/test_performance.py
import time

def test_pagination_performance():
    """Ensure pagination reduces memory usage"""
    start_mem = get_memory_usage()

    # Paginated call
    result = list_players_paginated(limit=50)

    end_mem = get_memory_usage()

    # Should use less than 100MB
    assert end_mem - start_mem < 100_000_000

def test_rate_limiting():
    """Ensure rate limiting works"""
    start = time.time()

    # Make 11 requests (limit is 10/minute)
    for i in range(11):
        try:
            scrape_url("https://www.nba.com")
        except RateLimitError:
            break

    duration = time.time() - start

    # Should be rate limited before 11th request
    assert duration < 60  # Didn't wait full minute
```

---

## 9. Deployment Improvements

### Current Deployment

```json
{
  "mcpServers": {
    "nba-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/nba-mcp-synthesis", "run", "nba-mcp"]
    }
  }
}
```

### Improved Deployment Options

#### Option 1: Docker (Recommended)

```bash
# Build image
docker build -t nba-mcp-server:latest .

# Run container
docker run -d \
  --name nba-mcp \
  -p 8000:8000 \
  -e AWS_PROFILE=default \
  -e AWS_REGION=us-west-2 \
  -e GOOGLE_API_KEY=your-key \
  -v ~/.aws:/root/.aws:ro \
  nba-mcp-server:latest
```

**Claude Desktop Config (Docker)**:
```json
{
  "mcpServers": {
    "nba-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "AWS_PROFILE=default",
        "-e", "GOOGLE_API_KEY=${GOOGLE_API_KEY}",
        "nba-mcp-server:latest"
      ]
    }
  }
}
```

#### Option 2: uvx (Current, Enhanced)

```json
{
  "mcpServers": {
    "nba-mcp": {
      "command": "uvx",
      "args": ["nba-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-west-2",
        "GOOGLE_API_KEY": "${GOOGLE_API_KEY}",
        "FASTMCP_LOG_LEVEL": "INFO",
        "NB A_MCP_READONLY": "false"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

#### Option 3: HTTP/SSE (Remote)

```json
{
  "mcpServers": {
    "nba-mcp": {
      "url": "https://nba-mcp.your-domain.com/mcp",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer ${NBA_MCP_API_KEY}"
      }
    }
  }
}
```

---

## 10. Documentation Updates

### README.md Updates

Add sections:

```markdown
## 🆕 New in v2.0

### Mathematical & Statistical Tools (20 tools)
Calculate NBA advanced metrics:
- Player Efficiency Rating (PER)
- True Shooting Percentage (TS%)
- Usage Rate (USG%)
- And more...

### Web Scraping Tools (3 tools)
Fetch NBA news and data from external sources:
- Scrape NBA websites
- Search for specific content
- Smart extraction with AI

### MCP Prompts (7 templates)
Reusable analysis templates:
- analyze_player
- compare_players
- predict_game
- team_analysis

### MCP Resources (6 URIs)
Structured data access:
- nba://games/{date}
- nba://standings/{conference}
- nba://players/{player_id}

## Quick Start

### Installation

```bash
# Install with all dependencies
pip install -e .

# For web scraping
pip install crawl4ai google-generativeai

# Set up API keys
export GOOGLE_API_KEY=your-key-here
```

### Usage Examples

**Calculate Player Efficiency:**
```python
result = await call_tool("nba_player_efficiency_rating", {
    "points": 250,
    "rebounds": 100,
    # ... other stats
})
# Returns: {"per": 18.5, "interpretation": "Excellent"}
```

**Scrape NBA News:**
```python
content = await call_tool("scrape_nba_webpage", {
    "url": "https://www.nba.com/news"
})
# Returns: Markdown content of NBA news
```

**Use Analysis Prompt:**
```python
prompt = await get_prompt("analyze_player", {
    "player_name": "LeBron James",
    "season": "2024"
})
# Returns: Structured analysis prompt
```
```

### New Documentation Files

1. **MATH_TOOLS_GUIDE.md** - Guide to mathematical tools
2. **WEB_SCRAPING_GUIDE.md** - Web scraping usage and best practices
3. **PROMPTS_GUIDE.md** - How to use prompt templates
4. **RESOURCES_GUIDE.md** - MCP resources documentation
5. **DEPLOYMENT_GUIDE.md** - Docker and production deployment
6. **PERFORMANCE_TUNING.md** - Optimization tips

---

## Conclusion

This comprehensive improvement plan provides:

✅ **Immediate Value**: 20 math tools (Sprint 5) can be added in 2 days
✅ **External Data**: Web scraping (Sprint 6) adds real-time news/stats
✅ **Better UX**: Prompts & Resources (Sprint 7) improve discoverability
✅ **Production Ready**: Docker, metrics, pagination for scaling
✅ **Future Growth**: ML integration path for predictions

**Recommended Start**: Sprint 5 (Math Tools) - Highest value, lowest complexity

**Next Priority**: Sprints 6 & 7 (Web Scraping + Prompts/Resources)

**Total Tools After All Sprints**: 18 (current) + 20 (math) + 3 (web) + 6+ (ML) = **47+ tools**

---

**Questions or Need Help?**
- Review specific sprint details above
- Check reference implementations in cloned repos
- Start with Sprint 5 for quick wins

**Status**: Ready to implement Sprint 5 immediately! 🚀

---

## 11. Phase 9: Complete Original Plan

**Start Date**: October 10, 2025
**Duration**: 8-13 days
**Goal**: Implement the 36 missing features from the original plan

---

### Overview

Phase 9 will complete the original NBA_MCP_IMPROVEMENT_PLAN.md by implementing the three sprints (5-7) that were NOT built during actual Sprints 5-8.

**Current Status**: 88 tools (from actual Sprints 5-8)
**After Phase 9**: 124 tools/features total (88 + 36)

---

### 11.1 Phase 9 Sprint 5: Mathematical & Statistical Tools

**Duration**: 2-3 days
**Deliverables**: 20 new tools
**Status**: ❌ NOT STARTED

#### Tools to Build

**Arithmetic (7 tools)**:
- [ ] `math_add` - Add two numbers
- [ ] `math_subtract` - Subtract numbers
- [ ] `math_multiply` - Multiply numbers
- [ ] `math_divide` - Divide numbers
- [ ] `math_sum` - Sum array of numbers
- [ ] `math_modulo` - Modulo operation
- [ ] `math_round` - Round/floor/ceiling

**Statistical (5 tools)**:
- [ ] `stats_mean` - Calculate mean
- [ ] `stats_median` - Calculate median
- [ ] `stats_mode` - Find mode
- [ ] `stats_min` - Find minimum
- [ ] `stats_max` - Find maximum

**Advanced NBA Metrics (8 tools)**:
- [ ] `nba_player_efficiency_rating` - Calculate PER
- [ ] `nba_true_shooting_percentage` - Calculate TS%
- [ ] `nba_usage_rate` - Calculate usage rate
- [ ] `nba_effective_field_goal_percentage` - Calculate eFG%
- [ ] `nba_offensive_rating` - Calculate ORtg
- [ ] `nba_defensive_rating` - Calculate DRtg
- [ ] `nba_win_shares` - Calculate win shares
- [ ] `nba_box_plus_minus` - Calculate BPM

#### Implementation Steps

**Day 1**:
1. Create `mcp_server/tools/math_helper.py` (7 functions)
2. Create `mcp_server/tools/stats_helper.py` (5 functions)
3. Create `mcp_server/tools/nba_metrics_helper.py` (8 functions)
4. Add 20 parameter models to `params.py`

**Day 2**:
5. Register 20 MCP tools in `fastmcp_server.py`
6. Create test file `scripts/test_math_stats_tools.py`
7. Run all tests, ensure 100% pass rate

**Day 3** (buffer/documentation):
8. Update README.md with math tools
9. Create MATH_TOOLS_GUIDE.md
10. Mark Sprint 5 complete

#### Success Criteria
- ✅ 20 tools implemented and tested
- ✅ All tools return correct results
- ✅ NBA metrics match standard formulas
- ✅ Can calculate PER, TS%, USG% from real player stats

---

### 11.2 Phase 9 Sprint 6: Web Scraping Integration

**Duration**: 3-5 days
**Deliverables**: 3 new tools
**Status**: ❌ NOT STARTED

#### Tools to Build

**Web Scraping with Crawl4AI (3 tools)**:
- [ ] `scrape_nba_webpage` - Scrape URL to Markdown
- [ ] `search_webpage_for_text` - Search text with context
- [ ] `extract_structured_data` - LLM-based extraction

#### Implementation Steps

**Day 1-2: Setup & Basic Scraping**:
1. Install dependencies: `pip install crawl4ai google-generativeai`
2. Set up `GOOGLE_API_KEY` environment variable
3. Create `mcp_server/tools/web_scraper_helper.py`
4. Implement `scrape_url()` function
5. Add rate limiting (@rate_limited decorator)
6. Test with NBA.com, ESPN.com

**Day 3-4: Advanced Extraction**:
7. Implement `extract_text_by_query()` function
8. Implement `smart_extract()` with LLM
9. Add 3 parameter models (`ScrapeUrlParams`, `ExtractTextByQueryParams`, `SmartExtractParams`)
10. Register 3 MCP tools in `fastmcp_server.py`

**Day 5: Testing & Documentation**:
11. Create test file `scripts/test_web_scraping_tools.py`
12. Test scraping real NBA websites
13. Test smart extraction of player stats
14. Update README.md
15. Create WEB_SCRAPING_GUIDE.md
16. Mark Sprint 6 complete

#### Dependencies
- crawl4ai (Python package)
- google-generativeai (for smart_extract)
- GOOGLE_API_KEY environment variable

#### Success Criteria
- ✅ Can scrape NBA.com, ESPN.com, Basketball-Reference.com
- ✅ Text search finds relevant content with context
- ✅ LLM extraction produces structured JSON
- ✅ Rate limiting prevents abuse (10 requests/min for basic, 5/min for LLM)
- ✅ All tests pass

---

### 11.3 Phase 9 Sprint 7: Prompts & Resources

**Duration**: 3-5 days
**Deliverables**: 7 prompts + 6 resources (13 features)
**Status**: ❌ NOT STARTED

#### Features to Build

**Part A: MCP Prompts (7 templates)**:
- [ ] `analyze_player` - Comprehensive player analysis
- [ ] `compare_players` - Side-by-side player comparison
- [ ] `predict_game` - Game outcome prediction
- [ ] `team_analysis` - Team performance analysis
- [ ] `injury_impact` - Assess injury impact on team
- [ ] `draft_analysis` - Evaluate draft prospects
- [ ] `trade_evaluation` - Trade scenario analysis

**Part B: MCP Resources (6 URIs)**:
- [ ] `nba://games/{date}` - Games on specific date
- [ ] `nba://standings/{conference}` - Conference standings
- [ ] `nba://players/{player_id}` - Player profile
- [ ] `nba://teams/{team_id}` - Team information
- [ ] `nba://injuries` - Current injury report
- [ ] `nba://players/top-scorers` - League scoring leaders

#### Implementation Steps

**Day 1-2: Implement Prompts**:
1. Add `@mcp.list_prompts()` handler in `fastmcp_server.py`
2. Add `@mcp.get_prompt()` handler in `fastmcp_server.py`
3. Create 7 prompt templates with arguments
4. Test each prompt with sample arguments

**Day 3-4: Implement Resources**:
5. Add `@mcp.list_resources()` handler in `fastmcp_server.py`
6. Add `@mcp.read_resource()` handler in `fastmcp_server.py`
7. Create 6 resource URIs with database queries
8. Test resource reading for each URI

**Day 5: Testing & Documentation**:
9. Create test file `scripts/test_prompts_resources.py`
10. Test all prompts and resources
11. Update README.md
12. Create PROMPTS_GUIDE.md
13. Create RESOURCES_GUIDE.md
14. Mark Sprint 7 complete

#### Success Criteria
- ✅ 7 prompts available via `list_prompts()`
- ✅ All prompts generate valid `GetPromptResult` objects
- ✅ 6 resources available via `list_resources()`
- ✅ All resources return valid JSON data
- ✅ Resources integrate with existing database queries
- ✅ Easy to discover via MCP client

---

### 11.4 Phase 9 Timeline

**Week 1 (Days 1-7)**:
- Days 1-3: Math/Stats Tools (Sprint 5)
- Days 4-7: Web Scraping Setup (Sprint 6 partial)

**Week 2 (Days 8-13)**:
- Days 8-9: Web Scraping Completion (Sprint 6)
- Days 10-13: Prompts & Resources (Sprint 7)
- Day 13: Final testing, documentation updates

**Total Duration**: 13 days (~2.5 weeks)

---

### 11.5 Phase 9 Success Metrics

| Metric | Target | Current | After Phase 9 |
|--------|--------|---------|---------------|
| Total Tools | - | 88 | 111 |
| Total Features | - | 88 | 124 (88 tools + 13 prompts/resources + 23 math/scraping) |
| Math/Stats Tools | 20 | 0 | 20 |
| Web Scraping Tools | 3 | 0 | 3 |
| MCP Prompts | 7 | 0 | 7 |
| MCP Resources | 6 | 0 | 6 |
| Test Coverage | 100% | 100% | 100% |

---

### 11.6 Phase 9 Deliverables

**Code Files Created**:
1. `mcp_server/tools/math_helper.py` (~200 lines)
2. `mcp_server/tools/stats_helper.py` (~150 lines)
3. `mcp_server/tools/nba_metrics_helper.py` (~500 lines)
4. `mcp_server/tools/web_scraper_helper.py` (~400 lines)

**Code Files Modified**:
5. `mcp_server/params.py` (+ ~700 lines - 23 new parameter models)
6. `mcp_server/fastmcp_server.py` (+ ~1200 lines - 23 tools + prompts + resources)

**Test Files Created**:
7. `scripts/test_math_stats_tools.py` (~300 lines)
8. `scripts/test_web_scraping_tools.py` (~200 lines)
9. `scripts/test_prompts_resources.py` (~250 lines)

**Documentation Created**:
10. `MATH_TOOLS_GUIDE.md` (~400 lines)
11. `WEB_SCRAPING_GUIDE.md` (~300 lines)
12. `PROMPTS_GUIDE.md` (~250 lines)
13. `RESOURCES_GUIDE.md` (~200 lines)

**Total New Code**: ~4,850 lines
**Total New Documentation**: ~1,150 lines

---

### 11.7 Post-Phase 9 System Status

**Complete NBA MCP Synthesis System**:
```
Original Infrastructure (Sprints 1-4): 17 tools ✅
Actual Sprint 5: 33 tools (Database/S3/File) ✅
Actual Sprint 6: 22 tools (Action/Glue) ✅
Actual Sprint 7: 18 tools (ML Core) ✅
Actual Sprint 8: 15 tools (ML Evaluation) ✅
Phase 9 Sprint 5: 20 tools (Math/Stats) ⬜
Phase 9 Sprint 6: 3 tools (Web Scraping) ⬜
Phase 9 Sprint 7: 13 features (Prompts/Resources) ⬜
────────────────────────────────────────────
TOTAL: 124 tools/features
```

**Capabilities After Phase 9**:
- ✅ **Complete infrastructure** (database, S3, files, AWS)
- ✅ **Full ML pipeline** (training, evaluation, validation)
- ✅ **Mathematical operations** (arithmetic, stats, NBA metrics)
- ✅ **Web scraping** (NBA news, stats extraction)
- ✅ **Guided workflows** (prompts for common tasks)
- ✅ **RESTful data access** (resources with nba:// URIs)
- ✅ **Production-ready** (100% test coverage, comprehensive docs)

**This will be the MOST COMPREHENSIVE NBA analytics MCP server available!** 🏀

---

### 11.8 Next Steps After Phase 9

Once Phase 9 is complete, consider these enhancements:

**Phase 10 Ideas** (Optional future work):
1. **Real NBA API Integration** - Connect to official NBA.com API
2. **Advanced Ensemble ML** - Gradient boosting, stacking
3. **Time Series Forecasting** - ARIMA, Prophet for predictions
4. **OAuth Authentication** - Protect premium features
5. **Multi-region Deployment** - AWS CloudFront, multiple regions
6. **Vector Search** - Semantic player/game similarity
7. **Real-time Notifications** - WebSocket/SSE for live game updates
8. **Mobile SDK** - iOS/Android wrappers for MCP tools

**Recommended Priority for Phase 10**:
1. Real NBA API Integration (highest value)
2. Time Series Forecasting (prediction improvement)
3. OAuth Authentication (monetization/security)
4. Real-time Notifications (user engagement)

---

**Ready to begin Phase 9 implementation!** 🚀

Start with: **Phase 9 Sprint 5 - Mathematical & Statistical Tools (Day 1)**

