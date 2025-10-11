"""
NBA MCP Server - FastMCP Implementation
Modern, declarative MCP server using FastMCP framework

This is a parallel implementation to server.py that uses the FastMCP framework
for cleaner, more maintainable code with 50-70% less boilerplate.
"""

import asyncio
from mcp.server.fastmcp import FastMCP, Context

# Import lifespan and settings
from .fastmcp_lifespan import nba_lifespan
from .fastmcp_settings import NBAMCPSettings

# Import Pydantic models (from Quick Win #3)
from .tools.params import (
    QueryDatabaseParams,
    ListTablesParams,
    GetTableSchemaParams,
    GetS3FileParams,
    ListS3FilesParams,
    ListGamesParams,
    ListPlayersParams,
    ListBooksParams,
    ReadBookParams,
    SearchBooksParams,
    GetEpubMetadataParams,
    GetEpubTocParams,
    ReadEpubChapterParams,
    GetPdfMetadataParams,
    GetPdfTocParams,
    ReadPdfPageParams,
    ReadPdfPageRangeParams,
    ReadPdfChapterParams,
    SearchPdfParams,
    # Math/Stats parameters (Sprint 5)
    MathTwoNumberParams,
    MathDivideParams,
    MathNumberListParams,
    MathRoundParams,
    MathSingleNumberParams,
    StatsPercentileParams,
    StatsVarianceParams,
    NbaPerParams,
    NbaTrueShootingParams,
    NbaEffectiveFgParams,
    NbaUsageRateParams,
    NbaRatingParams,
    # Sprint 6 parameters
    CorrelationParams,
    CovarianceParams,
    LinearRegressionParams,
    PredictParams,
    CorrelationMatrixParams,
    MovingAverageParams,
    ExponentialMovingAverageParams,
    TrendDetectionParams,
    PercentChangeParams,
    GrowthRateParams,
    VolatilityParams,
    FourFactorsParams,
    TurnoverPercentageParams,
    ReboundPercentageParams,
    AssistPercentageParams,
    StealPercentageParams,
    BlockPercentageParams,
    WinSharesParams,
    BoxPlusMinusParams,
    # Sprint 7 parameters (ML)
    KMeansClusteringParams,
    EuclideanDistanceParams,
    CosineSimilarityParams,
    KnnParams,
    HierarchicalClusteringParams,
    LogisticRegressionParams,
    LogisticPredictParams,
    NaiveBayesTrainParams,
    NaiveBayesPredictParams,
    DecisionTreeTrainParams,
    DecisionTreePredictParams,
    RandomForestTrainParams,
    RandomForestPredictParams,
    ZScoreOutliersParams,
    IsolationForestParams,
    LocalOutlierFactorParams,
    NormalizeFeaturesParams,
    FeatureImportanceParams,
    # Sprint 8 parameters (Model Evaluation & Validation)
    AccuracyScoreParams,
    PrecisionRecallF1Params,
    ConfusionMatrixParams,
    RocAucScoreParams,
    ClassificationReportParams,
    LogLossParams,
    MseRmseMaeParams,
    R2ScoreParams,
    MapeParams,
    KFoldSplitParams,
    StratifiedKFoldSplitParams,
    CrossValidateParams,
    CompareModelsParams,
    PairedTTestParams,
    GridSearchParams
)

# Import response models
from .responses import (
    QueryResult,
    TableListResult,
    TableSchemaResult,
    S3FileResult,
    S3ListResult,
    StandardResponse,
    PaginatedGamesResult,
    PaginatedPlayersResult,
    BookListResult,
    BookChunkResult,
    BookSearchResult,
    EpubMetadataResult,
    EpubTocResult,
    EpubChapterResult,
    PdfMetadataResult,
    PdfTocResult,
    PdfPageResult,
    PdfPageRangeResult,
    PdfChapterResult,
    PdfSearchResult,
    # Math/Stats responses (Sprint 5)
    MathOperationResult,
    StatsResult,
    NbaMetricResult
)

# Initialize settings
settings = NBAMCPSettings()

# Create FastMCP server with lifespan
mcp = FastMCP(
    name="nba-mcp-fastmcp",
    instructions="NBA MCP Server providing access to NBA database, S3 data lake, and Glue catalog via FastMCP framework",
    debug=settings.debug,
    log_level=settings.log_level,
    host=settings.host,
    port=settings.port,
    lifespan=nba_lifespan,
    warn_on_duplicate_tools=settings.warn_on_duplicate_tools,
    warn_on_duplicate_resources=settings.warn_on_duplicate_resources,
    warn_on_duplicate_prompts=settings.warn_on_duplicate_prompts
)


# =============================================================================
# Database Tools
# =============================================================================

@mcp.tool()
async def query_database(
    params: QueryDatabaseParams,
    ctx: Context
) -> QueryResult:
    """
    Execute a SQL query against the NBA PostgreSQL database.

    Only SELECT queries are allowed for security reasons.
    The query is validated for SQL injection attempts before execution.

    Args:
        params: Query parameters (sql, limit)
        ctx: FastMCP context for logging and progress

    Returns:
        QueryResult with columns, rows, and metadata
    """
    await ctx.info(f"Executing database query...")
    await ctx.debug(f"SQL: {params.sql_query[:100]}...")

    # Get RDS connector from lifespan context
    rds_connector = ctx.request_context.lifespan_context["rds_connector"]

    try:
        # The QueryDatabaseParams model already validates:
        # - SQL injection attempts
        # - Only SELECT statements
        # - Proper limit bounds

        # Execute query
        await ctx.report_progress(0.3, 1.0, "Executing query...")

        # RDS connector execute_query is already async
        results = await rds_connector.execute_query(
            params.sql_query,
            max_rows=params.max_rows
        )

        await ctx.report_progress(0.8, 1.0, "Processing results...")

        # Extract columns and rows from dict response
        # RDS connector returns: {"success": True, "rows": [...], "row_count": N, "columns": [...]}
        if results.get('success') and results.get('rows'):
            result_rows = results['rows']
            columns = list(result_rows[0].keys()) if result_rows and hasattr(result_rows[0], 'keys') else results.get('columns', [])
            rows = [list(row.values()) if hasattr(row, 'values') else list(row) for row in result_rows]
        else:
            columns = []
            rows = []

        result = QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            query=params.sql_query[:200],  # Truncate for response
            success=True
        )

        await ctx.info(f"Query completed: {result.row_count} rows returned")
        await ctx.report_progress(1.0, 1.0, "Complete")

        return result

    except Exception as e:
        await ctx.error(f"Query failed: {str(e)}")
        return QueryResult(
            columns=[],
            rows=[],
            row_count=0,
            query=params.sql_query[:200],
            success=False,
            error=str(e)
        )


@mcp.tool()
async def list_tables(
    params: ListTablesParams,
    ctx: Context
) -> TableListResult:
    """
    List all tables in the NBA database with optional schema filter.

    Args:
        params: Optional schema name to filter tables
        ctx: FastMCP context

    Returns:
        TableListResult with list of tables
    """
    await ctx.info("Listing database tables...")

    rds_connector = ctx.request_context.lifespan_context["rds_connector"]

    try:
        # Build query based on schema filter
        if params.schema_name:
            query = f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{params.schema_name}'
                ORDER BY table_name
            """
        else:
            query = """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
            """

        results = await rds_connector.execute_query(query)

        # RDS connector returns dict with 'rows' key
        if not results.get('success'):
            raise Exception(results.get('error', 'Query failed'))

        result_rows = results.get('rows', [])

        if params.schema_name:
            tables = [row['table_name'] for row in result_rows]
        else:
            tables = [f"{row['table_schema']}.{row['table_name']}" for row in result_rows]

        await ctx.info(f"Found {len(tables)} tables")

        return TableListResult(
            tables=tables,
            count=len(tables),
            success=True
        )

    except Exception as e:
        await ctx.error(f"Failed to list tables: {str(e)}")
        return TableListResult(
            tables=[],
            count=0,
            success=False,
            error=str(e)
        )


@mcp.tool()
async def get_table_schema(
    params: GetTableSchemaParams,
    ctx: Context
) -> TableSchemaResult:
    """
    Get the schema (column definitions) for a specific table.

    Args:
        params: Table name (can include schema: schema.table)
        ctx: FastMCP context

    Returns:
        TableSchemaResult with column definitions
    """
    await ctx.info(f"Getting schema for table: {params.table_name}")

    rds_connector = ctx.request_context.lifespan_context["rds_connector"]

    try:
        # Parse schema and table name
        if '.' in params.table_name:
            schema, table = params.table_name.split('.', 1)
        else:
            schema = 'public'
            table = params.table_name

        query = f"""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
              AND table_name = '{table}'
            ORDER BY ordinal_position
        """

        results = await rds_connector.execute_query(query)

        # RDS connector returns dict with 'rows' key
        if not results.get('success') or not results.get('rows'):
            return TableSchemaResult(
                table_name=params.table_name,
                columns=[],
                success=False,
                error=f"Table '{params.table_name}' not found"
            )

        result_rows = results['rows']

        columns = [
            {
                "name": row['column_name'],
                "type": row['data_type'],
                "nullable": row['is_nullable'] == 'YES',
                "default": row['column_default']
            }
            for row in result_rows
        ]

        await ctx.info(f"Found {len(columns)} columns")

        return TableSchemaResult(
            table_name=params.table_name,
            columns=columns,
            success=True
        )

    except Exception as e:
        await ctx.error(f"Failed to get schema: {str(e)}")
        return TableSchemaResult(
            table_name=params.table_name,
            columns=[],
            success=False,
            error=str(e)
        )


# =============================================================================
# Paginated Tools
# =============================================================================

import base64

@mcp.tool()
async def list_games(
    params: ListGamesParams,
    ctx: Context
) -> PaginatedGamesResult:
    """
    List NBA games with cursor-based pagination.

    Supports filtering by season and team, with efficient pagination for large result sets.

    Args:
        params: Pagination and filter parameters
        ctx: FastMCP context

    Returns:
        PaginatedGamesResult with games and pagination info
    """
    await ctx.info(f"Listing games (limit: {params.limit})...")

    rds_connector = ctx.request_context.lifespan_context["rds_connector"]

    try:
        # Decode cursor to get starting game_id
        start_game_id = 0
        if params.cursor:
            try:
                start_game_id = int(base64.b64decode(params.cursor).decode())
            except Exception as e:
                await ctx.error(f"Invalid cursor: {str(e)}")
                return PaginatedGamesResult(
                    games=[],
                    count=0,
                    success=False,
                    error="Invalid pagination cursor"
                )

        # Build query with filters
        where_clauses = ["game_id > $1"]
        query_params = [start_game_id]
        param_counter = 2

        if params.season:
            where_clauses.append(f"season = ${param_counter}")
            query_params.append(params.season)
            param_counter += 1

        if params.team_name:
            where_clauses.append(f"(home_team ILIKE ${param_counter} OR away_team ILIKE ${param_counter})")
            query_params.append(f"%{params.team_name}%")
            param_counter += 1

        where_clause = " AND ".join(where_clauses)

        # Fetch one extra row to determine if there are more results
        query = f"""
            SELECT game_id, game_date, season, home_team, away_team,
                   home_score, away_score, venue, attendance
            FROM games
            WHERE {where_clause}
            ORDER BY game_id
            LIMIT ${param_counter}
        """
        query_params.append(params.limit + 1)

        results = await rds_connector.execute_query(query, params=tuple(query_params))

        if not results.get('success'):
            raise Exception(results.get('error', 'Query failed'))

        rows = results.get('rows', [])
        has_more = len(rows) > params.limit

        # Remove extra row if present
        if has_more:
            rows = rows[:-1]

        # Generate next cursor
        next_cursor = None
        if has_more and rows:
            last_game_id = rows[-1]['game_id']
            next_cursor = base64.b64encode(str(last_game_id).encode()).decode()

        # Convert rows to dicts
        games = [dict(row) for row in rows]

        await ctx.info(f"Retrieved {len(games)} games, has_more={has_more}")

        return PaginatedGamesResult(
            games=games,
            count=len(games),
            next_cursor=next_cursor,
            has_more=has_more,
            success=True
        )

    except Exception as e:
        await ctx.error(f"Failed to list games: {str(e)}")
        return PaginatedGamesResult(
            games=[],
            count=0,
            success=False,
            error=str(e)
        )


@mcp.tool()
async def list_players(
    params: ListPlayersParams,
    ctx: Context
) -> PaginatedPlayersResult:
    """
    List NBA players with cursor-based pagination.

    Supports filtering by team and position, with efficient pagination for large result sets.

    Args:
        params: Pagination and filter parameters
        ctx: FastMCP context

    Returns:
        PaginatedPlayersResult with players and pagination info
    """
    await ctx.info(f"Listing players (limit: {params.limit})...")

    rds_connector = ctx.request_context.lifespan_context["rds_connector"]

    try:
        # Decode cursor to get starting player_id
        start_player_id = 0
        if params.cursor:
            try:
                start_player_id = int(base64.b64decode(params.cursor).decode())
            except Exception as e:
                await ctx.error(f"Invalid cursor: {str(e)}")
                return PaginatedPlayersResult(
                    players=[],
                    count=0,
                    success=False,
                    error="Invalid pagination cursor"
                )

        # Build query with filters
        where_clauses = ["player_id > $1"]
        query_params = [start_player_id]
        param_counter = 2

        if params.team_name:
            where_clauses.append(f"team ILIKE ${param_counter}")
            query_params.append(f"%{params.team_name}%")
            param_counter += 1

        if params.position:
            where_clauses.append(f"position = ${param_counter}")
            query_params.append(params.position)
            param_counter += 1

        where_clause = " AND ".join(where_clauses)

        # Fetch one extra row to determine if there are more results
        query = f"""
            SELECT DISTINCT player_id, player_name, team, position,
                   jersey_number, height, weight
            FROM players
            WHERE {where_clause}
            ORDER BY player_id
            LIMIT ${param_counter}
        """
        query_params.append(params.limit + 1)

        results = await rds_connector.execute_query(query, params=tuple(query_params))

        if not results.get('success'):
            raise Exception(results.get('error', 'Query failed'))

        rows = results.get('rows', [])
        has_more = len(rows) > params.limit

        # Remove extra row if present
        if has_more:
            rows = rows[:-1]

        # Generate next cursor
        next_cursor = None
        if has_more and rows:
            last_player_id = rows[-1]['player_id']
            next_cursor = base64.b64encode(str(last_player_id).encode()).decode()

        # Convert rows to dicts
        players = [dict(row) for row in rows]

        await ctx.info(f"Retrieved {len(players)} players, has_more={has_more}")

        return PaginatedPlayersResult(
            players=players,
            count=len(players),
            next_cursor=next_cursor,
            has_more=has_more,
            success=True
        )

    except Exception as e:
        await ctx.error(f"Failed to list players: {str(e)}")
        return PaginatedPlayersResult(
            players=[],
            count=0,
            success=False,
            error=str(e)
        )


# =============================================================================
# S3 Resources (using resource templates)
# =============================================================================

@mcp.resource("s3://{bucket}/{key}")
async def get_s3_file(
    bucket: str,
    key: str,
    ctx: Context
) -> str:
    """
    Fetch a file from S3 bucket.

    This is a resource template that matches URIs like:
    s3://my-bucket/path/to/file.json

    Args:
        bucket: S3 bucket name
        key: Object key (path)
        ctx: FastMCP context

    Returns:
        File contents as string
    """
    await ctx.info(f"Fetching s3://{bucket}/{key}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Fetch from S3
        content = await asyncio.to_thread(
            s3_connector.get_object,
            key
        )

        await ctx.debug(f"Retrieved {len(content)} bytes")

        return content

    except Exception as e:
        await ctx.error(f"Failed to fetch S3 file: {str(e)}")
        raise  # Resources should raise exceptions on error


@mcp.resource("book://{book_path}")
async def get_book_metadata(
    book_path: str,
    ctx: Context
) -> str:
    """
    Get book metadata without reading full content.

    This resource provides quick access to book information including:
    - File size and format
    - Math content detection
    - Preview (first 500 characters)
    - Chunk information

    URI format: book://books/my-book.txt

    Args:
        book_path: S3 path to book (e.g., "books/my-book.txt")
        ctx: FastMCP context

    Returns:
        JSON string with book metadata
    """
    await ctx.info(f"Fetching metadata for: {book_path}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Get S3 metadata
        response = s3_connector.s3_client.head_object(
            Bucket=s3_connector.bucket_name,
            Key=book_path
        )

        # Read first 5000 characters for math detection
        content = await asyncio.to_thread(
            s3_connector.get_object,
            book_path
        )

        total_size = len(content)
        preview = content[:500]
        math_info = detect_math_content(content[:5000])

        # Calculate chunking info
        default_chunk_size = 50000
        total_chunks = math.ceil(total_size / default_chunk_size)

        metadata = {
            "path": book_path,
            "size": response['ContentLength'],
            "last_modified": response['LastModified'].isoformat(),
            "format": book_path.split('.')[-1] if '.' in book_path else 'unknown',
            "total_chunks": total_chunks,
            "has_math": math_info['has_math'],
            "math_difficulty": math_info['difficulty_score'],
            "latex_formulas": math_info['latex_formulas'],
            "recommended_mcp": math_info['recommended_mcp'],
            "preview": preview
        }

        import json
        return json.dumps(metadata, indent=2)

    except Exception as e:
        await ctx.error(f"Failed to fetch book metadata: {str(e)}")
        raise


@mcp.resource("book://{book_path}/chunk/{chunk_number}")
async def get_book_chunk(
    book_path: str,
    chunk_number: int,
    ctx: Context
) -> str:
    """
    Get a specific chunk of a book directly via resource URI.

    Useful for direct access to book sections without tool calls.
    Default chunk size: 50k characters.

    URI format: book://books/my-book.txt/chunk/0

    Args:
        book_path: S3 path to book
        chunk_number: Chunk index (0-based)
        ctx: FastMCP context

    Returns:
        Book chunk content as string
    """
    await ctx.info(f"Fetching {book_path} chunk {chunk_number}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Fetch full content
        content = await asyncio.to_thread(
            s3_connector.get_object,
            book_path
        )

        # Extract chunk
        chunk_size = 50000  # Default chunk size for resources
        total_size = len(content)
        total_chunks = math.ceil(total_size / chunk_size)

        if chunk_number >= total_chunks:
            raise ValueError(f"Chunk {chunk_number} out of range (total: {total_chunks})")

        start_idx = chunk_number * chunk_size
        end_idx = min(start_idx + chunk_size, total_size)
        chunk_content = content[start_idx:end_idx]

        await ctx.debug(f"Retrieved chunk {chunk_number + 1}/{total_chunks}")

        return chunk_content

    except Exception as e:
        await ctx.error(f"Failed to fetch book chunk: {str(e)}")
        raise


# =============================================================================
# S3 Tools
# =============================================================================

@mcp.tool()
async def list_s3_files(
    params: ListS3FilesParams,
    ctx: Context
) -> S3ListResult:
    """
    List files in the NBA data lake S3 bucket.

    Args:
        params: Prefix and max_keys parameters
        ctx: FastMCP context

    Returns:
        S3ListResult with list of file keys
    """
    await ctx.info(f"Listing S3 files with prefix: {params.prefix or '(root)'}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # List objects
        files = await asyncio.to_thread(
            s3_connector.list_objects,
            prefix=params.prefix,
            max_keys=params.max_keys
        )

        await ctx.info(f"Found {len(files)} files")

        return S3ListResult(
            files=files,
            count=len(files),
            prefix=params.prefix,
            truncated=len(files) == params.max_keys,
            success=True
        )

    except Exception as e:
        await ctx.error(f"Failed to list S3 files: {str(e)}")
        return S3ListResult(
            files=[],
            count=0,
            prefix=params.prefix,
            truncated=False,
            success=False,
            error=str(e)
        )


# =============================================================================
# Book Tools - Read and search books with math content
# =============================================================================

import re
import math

def detect_math_content(content: str) -> dict:
    """
    Detect mathematical content in text.

    Returns dict with:
        has_math: bool
        latex_formulas: int
        math_symbols: int
        difficulty_score: float (0-1)
    """
    # LaTeX patterns
    latex_inline = len(re.findall(r'\$[^\$]+\$', content))
    latex_display = len(re.findall(r'\$\$[^\$]+\$\$', content))
    latex_env = len(re.findall(r'\\begin\{(equation|align|matrix|array)\}', content))

    # Math symbols
    math_symbols = len(re.findall(r'[∑∫∂∇√±×÷≤≥≠≈∞αβγδεθλμσπωΔΣΠΩ]', content))

    # Common math operators/functions
    math_funcs = len(re.findall(r'\b(sin|cos|tan|log|ln|exp|sqrt|sum|integral|derivative|limit)\b', content, re.IGNORECASE))

    total_latex = latex_inline + latex_display + latex_env
    has_math = total_latex > 0 or math_symbols > 5 or math_funcs > 3

    # Difficulty score (0-1)
    # More LaTeX and symbols = higher difficulty
    difficulty_score = min(1.0, (total_latex * 0.1 + math_symbols * 0.01 + math_funcs * 0.05))

    return {
        "has_math": has_math,
        "latex_formulas": total_latex,
        "math_symbols": math_symbols,
        "math_functions": math_funcs,
        "difficulty_score": round(difficulty_score, 2),
        "recommended_mcp": "math-mcp" if has_math else None
    }


@mcp.tool()
async def list_books(
    params: ListBooksParams,
    ctx: Context
) -> BookListResult:
    """
    List books available in S3 with metadata detection.

    Scans books/ prefix in S3 and detects math content in first chunk.
    Perfect for finding books to read with Google Gemini's large context window.

    Args:
        params: Prefix and max_keys parameters
        ctx: FastMCP context

    Returns:
        BookListResult with books and metadata
    """
    await ctx.info(f"Listing books with prefix: {params.prefix}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # List all books
        file_keys = await asyncio.to_thread(
            s3_connector.list_objects,
            prefix=params.prefix,
            max_keys=params.max_keys
        )

        await ctx.report_progress(0.3, 1.0, f"Found {len(file_keys)} books, analyzing...")

        books = []
        for i, key in enumerate(file_keys):
            try:
                # Get object metadata (size, last modified)
                response = s3_connector.s3_client.head_object(
                    Bucket=s3_connector.bucket_name,
                    Key=key
                )

                # Read first 5000 characters to detect math content
                content = await asyncio.to_thread(
                    s3_connector.get_object,
                    key
                )
                preview = content[:5000]
                math_info = detect_math_content(preview)

                books.append({
                    "path": key,
                    "size": response['ContentLength'],
                    "last_modified": response['LastModified'].isoformat(),
                    "format": key.split('.')[-1] if '.' in key else 'unknown',
                    "has_math": math_info['has_math'],
                    "math_difficulty": math_info['difficulty_score'],
                    "recommended_mcp": math_info['recommended_mcp']
                })

                if (i + 1) % 10 == 0:
                    await ctx.report_progress(0.3 + 0.5 * (i / len(file_keys)), 1.0, f"Analyzed {i + 1}/{len(file_keys)} books")

            except Exception as e:
                await ctx.error(f"Failed to analyze book {key}: {str(e)}")
                # Still include book with minimal metadata
                books.append({
                    "path": key,
                    "size": 0,
                    "last_modified": None,
                    "format": key.split('.')[-1] if '.' in key else 'unknown',
                    "has_math": False,
                    "error": str(e)
                })

        await ctx.info(f"Listed {len(books)} books ({sum(1 for b in books if b.get('has_math')) } with math content)")
        await ctx.report_progress(1.0, 1.0, "Complete")

        return BookListResult(
            books=books,
            count=len(books),
            prefix=params.prefix,
            success=True
        )

    except Exception as e:
        await ctx.error(f"Failed to list books: {str(e)}")
        return BookListResult(
            books=[],
            count=0,
            prefix=params.prefix,
            success=False,
            error=str(e)
        )


@mcp.tool()
async def read_book(
    params: ReadBookParams,
    ctx: Context
) -> BookChunkResult:
    """
    Read a book from S3 in chunks with LaTeX preservation.

    Books are chunked to fit within LLM token limits. LaTeX formulas and
    mathematical notation are preserved for accurate reading.

    Recommended chunk sizes:
    - 50k chars: GPT-4, Claude (default)
    - 100k chars: Claude, Gemini
    - 200k chars: Gemini 1.5 Pro (max)

    Args:
        params: Book path, chunk size, and chunk number
        ctx: FastMCP context

    Returns:
        BookChunkResult with content and metadata
    """
    await ctx.info(f"Reading book: {params.book_path}, chunk {params.chunk_number}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Fetch full book content
        await ctx.report_progress(0.2, 1.0, "Fetching book from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        total_size = len(content)
        total_chunks = math.ceil(total_size / params.chunk_size)

        # Validate chunk number
        if params.chunk_number >= total_chunks:
            return BookChunkResult(
                book_path=params.book_path,
                content="",
                chunk_number=params.chunk_number,
                chunk_size=params.chunk_size,
                total_chunks=total_chunks,
                has_more=False,
                metadata={"total_size": total_size},
                success=False,
                error=f"Chunk {params.chunk_number} out of range (total: {total_chunks})"
            )

        # Extract chunk
        await ctx.report_progress(0.6, 1.0, f"Extracting chunk {params.chunk_number + 1}/{total_chunks}...")

        start_idx = params.chunk_number * params.chunk_size
        end_idx = min(start_idx + params.chunk_size, total_size)
        chunk_content = content[start_idx:end_idx]

        # Detect math content
        math_info = detect_math_content(chunk_content)

        # Build metadata
        metadata = {
            "total_size": total_size,
            "format": params.book_path.split('.')[-1] if '.' in params.book_path else 'unknown',
            "has_math": math_info['has_math'],
            "latex_formulas": math_info['latex_formulas'],
            "math_difficulty": math_info['difficulty_score'],
            "recommended_mcp": math_info['recommended_mcp']
        }

        await ctx.info(f"Read chunk {params.chunk_number + 1}/{total_chunks} ({len(chunk_content)} chars)")
        await ctx.report_progress(1.0, 1.0, "Complete")

        return BookChunkResult(
            book_path=params.book_path,
            content=chunk_content,
            chunk_number=params.chunk_number,
            chunk_size=len(chunk_content),
            total_chunks=total_chunks,
            has_more=params.chunk_number < total_chunks - 1,
            metadata=metadata,
            success=True
        )

    except Exception as e:
        await ctx.error(f"Failed to read book: {str(e)}")
        return BookChunkResult(
            book_path=params.book_path,
            content="",
            chunk_number=params.chunk_number,
            chunk_size=params.chunk_size,
            total_chunks=0,
            has_more=False,
            metadata={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def search_books(
    params: SearchBooksParams,
    ctx: Context
) -> BookSearchResult:
    """
    Search for text across all books with excerpt extraction.

    Performs simple text search (case-insensitive) across all books
    under the specified prefix. Returns matching excerpts with context.

    Future enhancement: Add vector embeddings for semantic search.

    Args:
        params: Search query, book prefix, and max results
        ctx: FastMCP context

    Returns:
        BookSearchResult with matching excerpts
    """
    await ctx.info(f"Searching books for: '{params.query}'")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # List all books
        await ctx.report_progress(0.1, 1.0, "Listing books...")

        file_keys = await asyncio.to_thread(
            s3_connector.list_objects,
            prefix=params.book_prefix,
            max_keys=1000
        )

        await ctx.info(f"Searching {len(file_keys)} books...")

        results = []
        query_lower = params.query.lower()

        for i, key in enumerate(file_keys):
            if len(results) >= params.max_results:
                break

            try:
                # Read book
                content = await asyncio.to_thread(
                    s3_connector.get_object,
                    key
                )

                content_lower = content.lower()

                # Find all matches
                matches = []
                start_pos = 0
                while start_pos < len(content_lower):
                    pos = content_lower.find(query_lower, start_pos)
                    if pos == -1:
                        break
                    matches.append(pos)
                    start_pos = pos + 1

                if matches:
                    # Extract excerpt from first match (with context)
                    match_pos = matches[0]
                    excerpt_start = max(0, match_pos - 100)
                    excerpt_end = min(len(content), match_pos + len(params.query) + 100)
                    excerpt = content[excerpt_start:excerpt_end]

                    # Add ellipsis if truncated
                    if excerpt_start > 0:
                        excerpt = "..." + excerpt
                    if excerpt_end < len(content):
                        excerpt = excerpt + "..."

                    # Calculate chunk number where match occurs
                    chunk_number = match_pos // 50000  # Default chunk size

                    results.append({
                        "book_path": key,
                        "excerpt": excerpt,
                        "match_count": len(matches),
                        "match_position": match_pos,
                        "chunk_number": chunk_number,
                        "relevance_score": min(1.0, len(matches) / 10)  # Simple relevance
                    })

                    await ctx.debug(f"Found {len(matches)} matches in {key}")

                if (i + 1) % 10 == 0:
                    await ctx.report_progress(0.1 + 0.8 * (i / len(file_keys)), 1.0, f"Searched {i + 1}/{len(file_keys)} books")

            except Exception as e:
                await ctx.error(f"Failed to search book {key}: {str(e)}")
                continue

        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)

        await ctx.info(f"Found {len(results)} results across {len(file_keys)} books")
        await ctx.report_progress(1.0, 1.0, "Complete")

        return BookSearchResult(
            results=results[:params.max_results],
            count=len(results),
            query=params.query,
            success=True
        )

    except Exception as e:
        await ctx.error(f"Failed to search books: {str(e)}")
        return BookSearchResult(
            results=[],
            count=0,
            query=params.query,
            success=False,
            error=str(e)
        )


# =============================================================================
# EPUB Tools - Read and process EPUB books
# =============================================================================

from .tools import epub_helper
from .decorators import handle_book_errors
import tempfile
import os


@mcp.tool()
@handle_book_errors
async def get_epub_metadata(
    params: GetEpubMetadataParams,
    ctx: Context
) -> EpubMetadataResult:
    """
    Get metadata from an EPUB file.

    Extracts title, author, publisher, language, and other metadata fields.

    Args:
        params: EPUB file path (S3 or local)
        ctx: FastMCP context

    Returns:
        EpubMetadataResult with metadata fields
    """
    await ctx.info(f"Extracting EPUB metadata: {params.book_path}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading EPUB from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Extract metadata
            await ctx.report_progress(0.5, 1.0, "Extracting metadata...")

            metadata = await asyncio.to_thread(
                epub_helper.get_metadata,
                tmp_path
            )

            await ctx.info(f"Extracted metadata: title={metadata.get('title', 'N/A')}")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return EpubMetadataResult(
                book_path=params.book_path,
                title=metadata.get('title'),
                author=metadata.get('creator'),
                language=metadata.get('language'),
                identifier=metadata.get('identifier'),
                date=metadata.get('date'),
                publisher=metadata.get('publisher'),
                description=metadata.get('description'),
                creator=metadata.get('creator'),
                contributor=metadata.get('contributor'),
                subject=metadata.get('subject'),
                success=True
            )

        finally:
            # Cleanup temp file
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to extract EPUB metadata: {str(e)}")
        return EpubMetadataResult(
            book_path=params.book_path,
            success=False,
            error=str(e)
        )


@mcp.tool()
@handle_book_errors
async def get_epub_toc(
    params: GetEpubTocParams,
    ctx: Context
) -> EpubTocResult:
    """
    Get table of contents from an EPUB file.

    Returns chapter titles and their hrefs for navigation.

    Args:
        params: EPUB file path (S3 or local)
        ctx: FastMCP context

    Returns:
        EpubTocResult with TOC entries
    """
    await ctx.info(f"Extracting EPUB TOC: {params.book_path}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading EPUB from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Extract TOC
            await ctx.report_progress(0.5, 1.0, "Extracting table of contents...")

            toc_entries = await asyncio.to_thread(
                epub_helper.get_toc,
                tmp_path
            )

            # Convert to dict format
            toc = [{"title": title, "href": href} for title, href in toc_entries]

            await ctx.info(f"Extracted {len(toc)} TOC entries")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return EpubTocResult(
                book_path=params.book_path,
                toc=toc,
                chapter_count=len(toc),
                success=True
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to extract EPUB TOC: {str(e)}")
        return EpubTocResult(
            book_path=params.book_path,
            toc=[],
            chapter_count=0,
            success=False,
            error=str(e)
        )


@mcp.tool()
@handle_book_errors
async def read_epub_chapter(
    params: ReadEpubChapterParams,
    ctx: Context
) -> EpubChapterResult:
    """
    Read a specific chapter from an EPUB file.

    Extracts chapter content with proper subchapter handling.
    Supports HTML, Markdown, and plain text output.

    Args:
        params: EPUB file path, chapter href, and format
        ctx: FastMCP context

    Returns:
        EpubChapterResult with chapter content
    """
    await ctx.info(f"Reading EPUB chapter: {params.chapter_href}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading EPUB from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Read EPUB book
            await ctx.report_progress(0.4, 1.0, "Opening EPUB...")

            book = await asyncio.to_thread(
                epub_helper.read_epub,
                tmp_path
            )

            # Extract chapter
            await ctx.report_progress(0.6, 1.0, f"Extracting chapter in {params.format} format...")

            if params.format == "html":
                chapter_content = await asyncio.to_thread(
                    epub_helper.extract_chapter_html,
                    book,
                    params.chapter_href
                )
            elif params.format == "markdown":
                chapter_content = await asyncio.to_thread(
                    epub_helper.extract_chapter_markdown,
                    book,
                    params.chapter_href
                )
            else:  # text
                chapter_content = await asyncio.to_thread(
                    epub_helper.extract_chapter_plain_text,
                    book,
                    params.chapter_href
                )

            await ctx.info(f"Extracted chapter ({len(chapter_content)} chars)")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return EpubChapterResult(
                book_path=params.book_path,
                chapter_href=params.chapter_href,
                content=chapter_content,
                format=params.format,
                content_length=len(chapter_content),
                success=True
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to read EPUB chapter: {str(e)}")
        return EpubChapterResult(
            book_path=params.book_path,
            chapter_href=params.chapter_href,
            content="",
            format=params.format,
            content_length=0,
            success=False,
            error=str(e)
        )


# =============================================================================
# PDF Tools - Read and process PDF documents
# =============================================================================

from .tools import pdf_helper


@mcp.tool()
@handle_book_errors
async def get_pdf_metadata(
    params: GetPdfMetadataParams,
    ctx: Context
) -> PdfMetadataResult:
    """
    Get metadata from a PDF file.

    Extracts title, author, creation date, page count, and TOC information.

    Args:
        params: PDF file path (S3 or local)
        ctx: FastMCP context

    Returns:
        PdfMetadataResult with metadata fields
    """
    await ctx.info(f"Extracting PDF metadata: {params.book_path}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading PDF from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Extract metadata
            await ctx.report_progress(0.5, 1.0, "Extracting metadata...")

            metadata = await asyncio.to_thread(
                pdf_helper.get_metadata,
                tmp_path
            )

            await ctx.info(f"Extracted metadata: {metadata.get('page_count', 0)} pages")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return PdfMetadataResult(
                book_path=params.book_path,
                title=metadata.get('title'),
                author=metadata.get('author'),
                subject=metadata.get('subject'),
                creator=metadata.get('creator'),
                producer=metadata.get('producer'),
                creation_date=metadata.get('creation_date'),
                modification_date=metadata.get('modification_date'),
                keywords=metadata.get('keywords'),
                page_count=metadata.get('page_count', 0),
                has_toc=metadata.get('has_toc', False),
                toc_entries=metadata.get('toc_entries', 0),
                success=True
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to extract PDF metadata: {str(e)}")
        return PdfMetadataResult(
            book_path=params.book_path,
            page_count=0,
            has_toc=False,
            toc_entries=0,
            success=False,
            error=str(e)
        )


@mcp.tool()
@handle_book_errors
async def get_pdf_toc(
    params: GetPdfTocParams,
    ctx: Context
) -> PdfTocResult:
    """
    Get table of contents from a PDF file.

    Returns chapter titles, levels, and page numbers.

    Args:
        params: PDF file path (S3 or local)
        ctx: FastMCP context

    Returns:
        PdfTocResult with TOC entries
    """
    await ctx.info(f"Extracting PDF TOC: {params.book_path}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading PDF from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Extract TOC
            await ctx.report_progress(0.5, 1.0, "Extracting table of contents...")

            toc_entries = await asyncio.to_thread(
                pdf_helper.get_toc,
                tmp_path
            )

            # Convert to dict format
            toc = [{"level": level, "title": title, "page": page} for level, title, page in toc_entries]

            await ctx.info(f"Extracted {len(toc)} TOC entries")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return PdfTocResult(
                book_path=params.book_path,
                toc=toc,
                entry_count=len(toc),
                success=True
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to extract PDF TOC: {str(e)}")
        return PdfTocResult(
            book_path=params.book_path,
            toc=[],
            entry_count=0,
            success=False,
            error=str(e)
        )


@mcp.tool()
@handle_book_errors
async def read_pdf_page(
    params: ReadPdfPageParams,
    ctx: Context
) -> PdfPageResult:
    """
    Read a single page from a PDF file.

    Supports text, HTML, and Markdown output formats.

    Args:
        params: PDF file path, page number, and format
        ctx: FastMCP context

    Returns:
        PdfPageResult with page content
    """
    await ctx.info(f"Reading PDF page {params.page_number}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading PDF from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Extract page
            await ctx.report_progress(0.6, 1.0, f"Extracting page in {params.format} format...")

            if params.format == "html":
                page_content = await asyncio.to_thread(
                    pdf_helper.extract_page_html,
                    tmp_path,
                    params.page_number
                )
            elif params.format == "markdown":
                page_content = await asyncio.to_thread(
                    pdf_helper.extract_page_markdown,
                    tmp_path,
                    params.page_number
                )
            else:  # text
                page_content = await asyncio.to_thread(
                    pdf_helper.extract_page_text,
                    tmp_path,
                    params.page_number
                )

            await ctx.info(f"Extracted page ({len(page_content)} chars)")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return PdfPageResult(
                book_path=params.book_path,
                page_number=params.page_number,
                content=page_content,
                format=params.format,
                content_length=len(page_content),
                success=True
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to read PDF page: {str(e)}")
        return PdfPageResult(
            book_path=params.book_path,
            page_number=params.page_number,
            content="",
            format=params.format,
            content_length=0,
            success=False,
            error=str(e)
        )


@mcp.tool()
@handle_book_errors
async def read_pdf_page_range(
    params: ReadPdfPageRangeParams,
    ctx: Context
) -> PdfPageRangeResult:
    """
    Read a range of pages from a PDF file.

    Extracts multiple consecutive pages with optional page breaks.

    Args:
        params: PDF file path, start/end pages, and format
        ctx: FastMCP context

    Returns:
        PdfPageRangeResult with combined content
    """
    await ctx.info(f"Reading PDF pages {params.start_page}-{params.end_page}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading PDF from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Extract page range
            await ctx.report_progress(0.6, 1.0, f"Extracting pages in {params.format} format...")

            range_content = await asyncio.to_thread(
                pdf_helper.extract_page_range,
                tmp_path,
                params.start_page,
                params.end_page,
                params.format
            )

            page_count = params.end_page - params.start_page + 1
            await ctx.info(f"Extracted {page_count} pages ({len(range_content)} chars)")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return PdfPageRangeResult(
                book_path=params.book_path,
                start_page=params.start_page,
                end_page=params.end_page,
                page_count=page_count,
                content=range_content,
                format=params.format,
                content_length=len(range_content),
                success=True
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to read PDF page range: {str(e)}")
        return PdfPageRangeResult(
            book_path=params.book_path,
            start_page=params.start_page,
            end_page=params.end_page,
            page_count=0,
            content="",
            format=params.format,
            content_length=0,
            success=False,
            error=str(e)
        )


@mcp.tool()
@handle_book_errors
async def read_pdf_chapter(
    params: ReadPdfChapterParams,
    ctx: Context
) -> PdfChapterResult:
    """
    Read a chapter from a PDF by title.

    Uses TOC to find chapter boundaries and extract content.

    Args:
        params: PDF file path, chapter title, and format
        ctx: FastMCP context

    Returns:
        PdfChapterResult with chapter content
    """
    await ctx.info(f"Reading PDF chapter: {params.chapter_title}")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading PDF from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Extract chapter
            await ctx.report_progress(0.5, 1.0, f"Extracting chapter in {params.format} format...")

            chapter_data = await asyncio.to_thread(
                pdf_helper.extract_chapter,
                tmp_path,
                params.chapter_title,
                params.format
            )

            await ctx.info(f"Extracted chapter: {chapter_data['page_count']} pages")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return PdfChapterResult(
                book_path=params.book_path,
                chapter_title=chapter_data['title'],
                level=chapter_data['level'],
                start_page=chapter_data['start_page'],
                end_page=chapter_data['end_page'],
                page_count=chapter_data['page_count'],
                content=chapter_data['content'],
                format=params.format,
                content_length=len(chapter_data['content']),
                success=True
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to read PDF chapter: {str(e)}")
        return PdfChapterResult(
            book_path=params.book_path,
            chapter_title=params.chapter_title,
            level=0,
            start_page=0,
            end_page=0,
            page_count=0,
            content="",
            format=params.format,
            content_length=0,
            success=False,
            error=str(e)
        )


@mcp.tool()
@handle_book_errors
async def search_pdf(
    params: SearchPdfParams,
    ctx: Context
) -> PdfSearchResult:
    """
    Search for text in a PDF file.

    Returns matches with page numbers, position, and surrounding context.

    Args:
        params: PDF file path, search query, and context size
        ctx: FastMCP context

    Returns:
        PdfSearchResult with search results
    """
    await ctx.info(f"Searching PDF for: '{params.query}'")

    s3_connector = ctx.request_context.lifespan_context["s3_connector"]

    try:
        # Download from S3 to temp file
        await ctx.report_progress(0.2, 1.0, "Downloading PDF from S3...")

        content = await asyncio.to_thread(
            s3_connector.get_object,
            params.book_path
        )

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(content.encode() if isinstance(content, str) else content)
            tmp_path = tmp.name

        try:
            # Search PDF
            await ctx.report_progress(0.5, 1.0, "Searching PDF...")

            search_results = await asyncio.to_thread(
                pdf_helper.search_text_in_pdf,
                tmp_path,
                params.query,
                params.context_chars
            )

            await ctx.info(f"Found {len(search_results)} matches")
            await ctx.report_progress(1.0, 1.0, "Complete")

            return PdfSearchResult(
                book_path=params.book_path,
                query=params.query,
                results=search_results,
                match_count=len(search_results),
                success=True
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        await ctx.error(f"Failed to search PDF: {str(e)}")
        return PdfSearchResult(
            book_path=params.book_path,
            query=params.query,
            results=[],
            match_count=0,
            success=False,
            error=str(e)
        )


# =============================================================================
# Math & Stats Tools - Sprint 5
# =============================================================================

from .tools import (
    math_helper,
    stats_helper,
    nba_metrics_helper,
    correlation_helper,
    timeseries_helper,
    # Sprint 7 ML helpers
    ml_clustering_helper,
    ml_classification_helper,
    ml_anomaly_helper,
    ml_feature_helper,
    # Sprint 8 ML Evaluation & Validation helpers
    ml_evaluation_helper,
    ml_validation_helper
)


@mcp.tool()
async def math_add(
    params: MathTwoNumberParams,
    ctx: Context
) -> MathOperationResult:
    """
    Add two numbers together.

    Args:
        params: Two numbers (a, b)
        ctx: FastMCP context

    Returns:
        MathOperationResult with sum
    """
    await ctx.info(f"Adding {params.a} + {params.b}")

    try:
        result = math_helper.add(params.a, params.b)

        return MathOperationResult(
            operation="add",
            result=result,
            inputs={"a": params.a, "b": params.b},
            success=True
        )
    except Exception as e:
        await ctx.error(f"Math operation failed: {str(e)}")
        return MathOperationResult(
            operation="add",
            result=0.0,
            inputs={"a": params.a, "b": params.b},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def math_subtract(
    params: MathTwoNumberParams,
    ctx: Context
) -> MathOperationResult:
    """
    Subtract the second number from the first number.

    Args:
        params: Two numbers (minuend=a, subtrahend=b)
        ctx: FastMCP context

    Returns:
        MathOperationResult with difference
    """
    await ctx.info(f"Subtracting {params.a} - {params.b}")

    try:
        result = math_helper.subtract(params.a, params.b)

        return MathOperationResult(
            operation="subtract",
            result=result,
            inputs={"minuend": params.a, "subtrahend": params.b},
            success=True
        )
    except Exception as e:
        await ctx.error(f"Math operation failed: {str(e)}")
        return MathOperationResult(
            operation="subtract",
            result=0.0,
            inputs={"minuend": params.a, "subtrahend": params.b},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def math_multiply(
    params: MathTwoNumberParams,
    ctx: Context
) -> MathOperationResult:
    """
    Multiply two numbers together.

    Args:
        params: Two numbers (a, b)
        ctx: FastMCP context

    Returns:
        MathOperationResult with product
    """
    await ctx.info(f"Multiplying {params.a} * {params.b}")

    try:
        result = math_helper.multiply(params.a, params.b)

        return MathOperationResult(
            operation="multiply",
            result=result,
            inputs={"a": params.a, "b": params.b},
            success=True
        )
    except Exception as e:
        await ctx.error(f"Math operation failed: {str(e)}")
        return MathOperationResult(
            operation="multiply",
            result=0.0,
            inputs={"a": params.a, "b": params.b},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def math_divide(
    params: MathDivideParams,
    ctx: Context
) -> MathOperationResult:
    """
    Divide the first number by the second number.

    Args:
        params: numerator and denominator (denominator cannot be zero)
        ctx: FastMCP context

    Returns:
        MathOperationResult with quotient
    """
    await ctx.info(f"Dividing {params.numerator} / {params.denominator}")

    try:
        result = math_helper.divide(params.numerator, params.denominator)

        return MathOperationResult(
            operation="divide",
            result=result,
            inputs={"numerator": params.numerator, "denominator": params.denominator},
            success=True
        )
    except Exception as e:
        await ctx.error(f"Math operation failed: {str(e)}")
        return MathOperationResult(
            operation="divide",
            result=0.0,
            inputs={"numerator": params.numerator, "denominator": params.denominator},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def math_sum(
    params: MathNumberListParams,
    ctx: Context
) -> MathOperationResult:
    """
    Sum a list of numbers.

    Args:
        params: List of numbers to sum
        ctx: FastMCP context

    Returns:
        MathOperationResult with total sum
    """
    await ctx.info(f"Summing {len(params.numbers)} numbers")

    try:
        result = math_helper.sum_numbers(params.numbers)

        return MathOperationResult(
            operation="sum",
            result=result,
            inputs={"numbers": params.numbers, "count": len(params.numbers)},
            success=True
        )
    except Exception as e:
        await ctx.error(f"Math operation failed: {str(e)}")
        return MathOperationResult(
            operation="sum",
            result=0.0,
            inputs={"numbers": params.numbers},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def math_round(
    params: MathRoundParams,
    ctx: Context
) -> MathOperationResult:
    """
    Round a number to specified decimal places.

    Args:
        params: Number to round and decimal places
        ctx: FastMCP context

    Returns:
        MathOperationResult with rounded value
    """
    await ctx.info(f"Rounding {params.number} to {params.decimals} decimal places")

    try:
        result = math_helper.round_number(params.number, params.decimals)

        return MathOperationResult(
            operation="round",
            result=result,
            inputs={"number": params.number, "decimals": params.decimals},
            success=True
        )
    except Exception as e:
        await ctx.error(f"Math operation failed: {str(e)}")
        return MathOperationResult(
            operation="round",
            result=0.0,
            inputs={"number": params.number},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def math_modulo(
    params: MathTwoNumberParams,
    ctx: Context
) -> MathOperationResult:
    """
    Calculate the remainder when dividing two numbers.

    Args:
        params: Two numbers (a % b)
        ctx: FastMCP context

    Returns:
        MathOperationResult with remainder
    """
    await ctx.info(f"Calculating {params.a} % {params.b}")

    try:
        result = math_helper.modulo(params.a, params.b)

        return MathOperationResult(
            operation="modulo",
            result=result,
            inputs={"numerator": params.a, "denominator": params.b},
            success=True
        )
    except Exception as e:
        await ctx.error(f"Math operation failed: {str(e)}")
        return MathOperationResult(
            operation="modulo",
            result=0.0,
            inputs={"numerator": params.a, "denominator": params.b},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_mean(
    params: MathNumberListParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate the arithmetic mean (average) of a list of numbers.

    Args:
        params: List of numbers
        ctx: FastMCP context

    Returns:
        StatsResult with mean value
    """
    await ctx.info(f"Calculating mean of {len(params.numbers)} numbers")

    try:
        result = stats_helper.calculate_mean(params.numbers)

        return StatsResult(
            statistic="mean",
            result=result,
            input_count=len(params.numbers),
            success=True
        )
    except Exception as e:
        await ctx.error(f"Stats calculation failed: {str(e)}")
        return StatsResult(
            statistic="mean",
            result=0.0,
            input_count=len(params.numbers),
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_median(
    params: MathNumberListParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate the median value of a list of numbers.

    Args:
        params: List of numbers
        ctx: FastMCP context

    Returns:
        StatsResult with median value
    """
    await ctx.info(f"Calculating median of {len(params.numbers)} numbers")

    try:
        result = stats_helper.calculate_median(params.numbers)

        return StatsResult(
            statistic="median",
            result=result,
            input_count=len(params.numbers),
            success=True
        )
    except Exception as e:
        await ctx.error(f"Stats calculation failed: {str(e)}")
        return StatsResult(
            statistic="median",
            result=0.0,
            input_count=len(params.numbers),
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_mode(
    params: MathNumberListParams,
    ctx: Context
) -> StatsResult:
    """
    Find the most common number(s) in a list.

    Args:
        params: List of numbers
        ctx: FastMCP context

    Returns:
        StatsResult with mode value(s)
    """
    await ctx.info(f"Calculating mode of {len(params.numbers)} numbers")

    try:
        result = stats_helper.calculate_mode(params.numbers)

        return StatsResult(
            statistic="mode",
            result=result,
            input_count=len(params.numbers),
            success=True
        )
    except Exception as e:
        await ctx.error(f"Stats calculation failed: {str(e)}")
        return StatsResult(
            statistic="mode",
            result=None,
            input_count=len(params.numbers),
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_min_max(
    params: MathNumberListParams,
    ctx: Context
) -> StatsResult:
    """
    Get minimum and maximum values from a list of numbers.

    Args:
        params: List of numbers
        ctx: FastMCP context

    Returns:
        StatsResult with dict containing min and max
    """
    await ctx.info(f"Finding min/max of {len(params.numbers)} numbers")

    try:
        min_val = stats_helper.calculate_min(params.numbers)
        max_val = stats_helper.calculate_max(params.numbers)

        return StatsResult(
            statistic="min_max",
            result={"min": min_val, "max": max_val, "range": max_val - min_val},
            input_count=len(params.numbers),
            success=True
        )
    except Exception as e:
        await ctx.error(f"Stats calculation failed: {str(e)}")
        return StatsResult(
            statistic="min_max",
            result={},
            input_count=len(params.numbers),
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_variance(
    params: StatsVarianceParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate variance and standard deviation.

    Args:
        params: List of numbers and whether to use sample variance
        ctx: FastMCP context

    Returns:
        StatsResult with variance and standard deviation
    """
    await ctx.info(f"Calculating variance of {len(params.numbers)} numbers")

    try:
        variance = stats_helper.calculate_variance(params.numbers, params.sample)
        std_dev = stats_helper.calculate_std_dev(params.numbers, params.sample)

        return StatsResult(
            statistic="variance",
            result={"variance": variance, "std_dev": std_dev, "sample": params.sample},
            input_count=len(params.numbers),
            success=True
        )
    except Exception as e:
        await ctx.error(f"Stats calculation failed: {str(e)}")
        return StatsResult(
            statistic="variance",
            result={},
            input_count=len(params.numbers),
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_summary(
    params: MathNumberListParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate comprehensive summary statistics.

    Includes count, mean, median, mode, min, max, range, std_dev, variance, and quartiles.

    Args:
        params: List of numbers
        ctx: FastMCP context

    Returns:
        StatsResult with comprehensive statistics
    """
    await ctx.info(f"Calculating summary statistics for {len(params.numbers)} numbers")

    try:
        result = stats_helper.calculate_summary_stats(params.numbers)

        return StatsResult(
            statistic="summary",
            result=result,
            input_count=len(params.numbers),
            success=True
        )
    except Exception as e:
        await ctx.error(f"Stats calculation failed: {str(e)}")
        return StatsResult(
            statistic="summary",
            result={},
            input_count=len(params.numbers),
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_player_efficiency_rating(
    params: NbaPerParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Player Efficiency Rating (PER).

    PER is an all-in-one basketball rating that summarizes a player's statistical accomplishments.
    League average is 15.0.

    Args:
        params: Player statistics (points, rebounds, assists, etc.)
        ctx: FastMCP context

    Returns:
        NbaMetricResult with PER value
    """
    await ctx.info(f"Calculating PER for player statistics")

    try:
        stats_dict = {
            "points": params.points,
            "rebounds": params.rebounds,
            "assists": params.assists,
            "steals": params.steals,
            "blocks": params.blocks,
            "fgm": params.fgm,
            "fga": params.fga,
            "ftm": params.ftm,
            "fta": params.fta,
            "turnovers": params.turnovers,
            "minutes": params.minutes
        }

        result = nba_metrics_helper.calculate_per(stats_dict)

        return NbaMetricResult(
            metric="PER",
            result=result,
            inputs=stats_dict,
            interpretation=f"PER of {result} (league average is 15.0)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"NBA metric calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="PER",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_true_shooting_percentage(
    params: NbaTrueShootingParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate True Shooting Percentage (TS%).

    TS% accounts for the value of 3-pointers and free throws.
    League average is typically around 0.550 (55.0%).

    Args:
        params: Points, field goal attempts, free throw attempts
        ctx: FastMCP context

    Returns:
        NbaMetricResult with TS% value
    """
    await ctx.info(f"Calculating TS% for player")

    try:
        result = nba_metrics_helper.calculate_true_shooting(
            params.points,
            params.fga,
            params.fta
        )

        inputs = {"points": params.points, "fga": params.fga, "fta": params.fta}

        return NbaMetricResult(
            metric="TS%",
            result=result,
            inputs=inputs,
            interpretation=f"True Shooting % of {result:.1%} (league avg ~55%)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"NBA metric calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="TS%",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_effective_field_goal_percentage(
    params: NbaEffectiveFgParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Effective Field Goal Percentage (eFG%).

    eFG% adjusts for the fact that 3-point field goals are worth more than 2-pointers.

    Args:
        params: Field goals made, attempted, and three-pointers made
        ctx: FastMCP context

    Returns:
        NbaMetricResult with eFG% value
    """
    await ctx.info(f"Calculating eFG% for player")

    try:
        result = nba_metrics_helper.calculate_effective_fg_pct(
            params.fgm,
            params.fga,
            params.three_pm
        )

        inputs = {"fgm": params.fgm, "fga": params.fga, "three_pm": params.three_pm}

        return NbaMetricResult(
            metric="eFG%",
            result=result,
            inputs=inputs,
            interpretation=f"Effective FG% of {result:.1%}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"NBA metric calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="eFG%",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_usage_rate(
    params: NbaUsageRateParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Usage Rate (USG%).

    Measures the percentage of team plays used by a player while on the floor.

    Args:
        params: Player and team statistics
        ctx: FastMCP context

    Returns:
        NbaMetricResult with USG% value
    """
    await ctx.info(f"Calculating USG% for player")

    try:
        result = nba_metrics_helper.calculate_usage_rate(
            params.fga,
            params.fta,
            params.turnovers,
            params.minutes,
            params.team_minutes,
            params.team_fga,
            params.team_fta,
            params.team_turnovers
        )

        inputs = {
            "player_fga": params.fga,
            "player_fta": params.fta,
            "player_tov": params.turnovers,
            "player_min": params.minutes
        }

        return NbaMetricResult(
            metric="USG%",
            result=result,
            inputs=inputs,
            interpretation=f"Usage Rate of {result}%",
            success=True
        )
    except Exception as e:
        await ctx.error(f"NBA metric calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="USG%",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_offensive_rating(
    params: NbaRatingParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Offensive Rating (ORtg).

    Points scored per 100 possessions.

    Args:
        params: Points and possessions
        ctx: FastMCP context

    Returns:
        NbaMetricResult with ORtg value
    """
    await ctx.info(f"Calculating Offensive Rating")

    try:
        result = nba_metrics_helper.calculate_offensive_rating(
            params.points,
            params.possessions
        )

        inputs = {"points": params.points, "possessions": params.possessions}

        return NbaMetricResult(
            metric="ORtg",
            result=result,
            inputs=inputs,
            interpretation=f"Offensive Rating of {result} points per 100 possessions",
            success=True
        )
    except Exception as e:
        await ctx.error(f"NBA metric calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="ORtg",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_defensive_rating(
    params: NbaRatingParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Defensive Rating (DRtg).

    Points allowed per 100 possessions (lower is better).

    Args:
        params: Points allowed and possessions
        ctx: FastMCP context

    Returns:
        NbaMetricResult with DRtg value
    """
    await ctx.info(f"Calculating Defensive Rating")

    try:
        result = nba_metrics_helper.calculate_defensive_rating(
            params.points,
            params.possessions
        )

        inputs = {"points_allowed": params.points, "possessions": params.possessions}

        return NbaMetricResult(
            metric="DRtg",
            result=result,
            inputs=inputs,
            interpretation=f"Defensive Rating of {result} points allowed per 100 possessions (lower is better)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"NBA metric calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="DRtg",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_pace(
    params: NbaRatingParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Pace (possessions per 48 minutes).

    Measures how fast a team plays.

    Args:
        params: Possessions (in points field) and minutes
        ctx: FastMCP context

    Returns:
        NbaMetricResult with Pace value
    """
    await ctx.info(f"Calculating Pace")

    try:
        # Use points field for possessions, possessions field for minutes
        result = nba_metrics_helper.calculate_pace(
            params.points,  # possessions
            params.possessions  # minutes
        )

        inputs = {"possessions": params.points, "minutes": params.possessions}

        return NbaMetricResult(
            metric="Pace",
            result=result,
            inputs=inputs,
            interpretation=f"Pace of {result} possessions per 48 minutes",
            success=True
        )
    except Exception as e:
        await ctx.error(f"NBA metric calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="Pace",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


# =============================================================================
# Sprint 6: Advanced Analytics Tools
# =============================================================================

# Correlation & Regression Tools

@mcp.tool()
async def stats_correlation(
    params: CorrelationParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate Pearson correlation coefficient between two variables.

    Measures linear relationship between variables (-1 to 1).

    Args:
        params: Two lists of numbers (x and y)
        ctx: FastMCP context

    Returns:
        StatsResult with correlation coefficient
    """
    await ctx.info(f"Calculating correlation between {len(params.x)} data points")

    try:
        result = correlation_helper.calculate_correlation(params.x, params.y)

        return StatsResult(
            operation="correlation",
            result=result,
            inputs={"x": params.x, "y": params.y},
            interpretation=f"Correlation: {result} ({'strong positive' if result > 0.7 else 'moderate positive' if result > 0.3 else 'weak/no' if result > -0.3 else 'moderate negative' if result > -0.7 else 'strong negative'})",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Correlation calculation failed: {str(e)}")
        return StatsResult(
            operation="correlation",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_covariance(
    params: CovarianceParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate covariance between two variables.

    Measures how two variables vary together.

    Args:
        params: Two lists of numbers and sample flag
        ctx: FastMCP context

    Returns:
        StatsResult with covariance
    """
    await ctx.info(f"Calculating {'sample' if params.sample else 'population'} covariance")

    try:
        result = correlation_helper.calculate_covariance(params.x, params.y, params.sample)

        return StatsResult(
            operation="covariance",
            result=result,
            inputs={"x": params.x, "y": params.y, "sample": params.sample},
            interpretation=f"Covariance: {result}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Covariance calculation failed: {str(e)}")
        return StatsResult(
            operation="covariance",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_linear_regression(
    params: LinearRegressionParams,
    ctx: Context
) -> dict:
    """
    Perform simple linear regression (y = mx + b).

    Finds best-fit line using least squares method.

    Args:
        params: Independent (x) and dependent (y) variables
        ctx: FastMCP context

    Returns:
        Dictionary with slope, intercept, r_squared, and equation
    """
    await ctx.info(f"Performing linear regression on {len(params.x)} data points")

    try:
        result = correlation_helper.calculate_linear_regression(params.x, params.y)
        result["success"] = True
        result["inputs"] = {"x": params.x, "y": params.y}

        return result
    except Exception as e:
        await ctx.error(f"Linear regression failed: {str(e)}")
        return {
            "slope": 0.0,
            "intercept": 0.0,
            "r_squared": 0.0,
            "equation": "",
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def stats_predict(
    params: PredictParams,
    ctx: Context
) -> dict:
    """
    Make predictions using linear regression model.

    Uses model parameters to predict new values.

    Args:
        params: Model slope, intercept, and new x values
        ctx: FastMCP context

    Returns:
        Dictionary with predictions
    """
    await ctx.info(f"Making {len(params.x_values)} predictions")

    try:
        predictions = correlation_helper.predict_values(
            params.slope,
            params.intercept,
            params.x_values
        )

        return {
            "predictions": predictions,
            "model": {"slope": params.slope, "intercept": params.intercept},
            "x_values": params.x_values,
            "success": True
        }
    except Exception as e:
        await ctx.error(f"Prediction failed: {str(e)}")
        return {
            "predictions": [],
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def stats_correlation_matrix(
    params: CorrelationMatrixParams,
    ctx: Context
) -> dict:
    """
    Calculate correlation matrix for multiple variables.

    Shows correlations between all pairs of variables.

    Args:
        params: Dictionary of variable name -> values
        ctx: FastMCP context

    Returns:
        Dictionary with correlation matrix
    """
    await ctx.info(f"Calculating correlation matrix for {len(params.data)} variables")

    try:
        matrix = correlation_helper.calculate_correlation_matrix(params.data)

        return {
            "correlation_matrix": matrix,
            "variables": list(params.data.keys()),
            "success": True
        }
    except Exception as e:
        await ctx.error(f"Correlation matrix failed: {str(e)}")
        return {
            "correlation_matrix": {},
            "success": False,
            "error": str(e)
        }


# Time Series Analysis Tools

@mcp.tool()
async def stats_moving_average(
    params: MovingAverageParams,
    ctx: Context
) -> dict:
    """
    Calculate simple moving average (SMA).

    Smooths time series by averaging values in sliding window.

    Args:
        params: Time series data and window size
        ctx: FastMCP context

    Returns:
        Dictionary with smoothed values
    """
    await ctx.info(f"Calculating {params.window}-period moving average")

    try:
        result = timeseries_helper.calculate_moving_average(params.data, params.window)

        return {
            "moving_average": result,
            "window": params.window,
            "original_data": params.data,
            "success": True
        }
    except Exception as e:
        await ctx.error(f"Moving average failed: {str(e)}")
        return {
            "moving_average": [],
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def stats_exponential_moving_average(
    params: ExponentialMovingAverageParams,
    ctx: Context
) -> dict:
    """
    Calculate exponential moving average (EMA).

    Weighted moving average giving more weight to recent values.

    Args:
        params: Time series data and alpha (smoothing factor)
        ctx: FastMCP context

    Returns:
        Dictionary with EMA values
    """
    await ctx.info(f"Calculating EMA with alpha={params.alpha}")

    try:
        result = timeseries_helper.calculate_exponential_moving_average(params.data, params.alpha)

        return {
            "ema": result,
            "alpha": params.alpha,
            "original_data": params.data,
            "success": True
        }
    except Exception as e:
        await ctx.error(f"EMA calculation failed: {str(e)}")
        return {
            "ema": [],
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def stats_trend_detection(
    params: TrendDetectionParams,
    ctx: Context
) -> dict:
    """
    Detect if data is trending up, down, or stable.

    Uses linear regression to identify trend direction and strength.

    Args:
        params: Time series data
        ctx: FastMCP context

    Returns:
        Dictionary with trend, slope, and confidence
    """
    await ctx.info(f"Detecting trend in {len(params.data)} data points")

    try:
        result = timeseries_helper.detect_trend(params.data)
        result["success"] = True
        result["data"] = params.data

        return result
    except Exception as e:
        await ctx.error(f"Trend detection failed: {str(e)}")
        return {
            "trend": "unknown",
            "slope": 0.0,
            "confidence": 0.0,
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def stats_percent_change(
    params: PercentChangeParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate percentage change from previous to current value.

    Positive = increase, negative = decrease.

    Args:
        params: Current and previous values
        ctx: FastMCP context

    Returns:
        StatsResult with percent change
    """
    await ctx.info(f"Calculating percent change: {params.previous} → {params.current}")

    try:
        result = timeseries_helper.calculate_percent_change(params.current, params.previous)

        return StatsResult(
            operation="percent_change",
            result=result,
            inputs={"current": params.current, "previous": params.previous},
            interpretation=f"{result}% {'increase' if result > 0 else 'decrease' if result < 0 else 'no change'}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Percent change failed: {str(e)}")
        return StatsResult(
            operation="percent_change",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_growth_rate(
    params: GrowthRateParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate compound annual/period growth rate (CAGR).

    Average growth rate over multiple periods.

    Args:
        params: Start value, end value, and number of periods
        ctx: FastMCP context

    Returns:
        StatsResult with growth rate per period
    """
    await ctx.info(f"Calculating growth rate over {params.periods} periods")

    try:
        result = timeseries_helper.calculate_growth_rate(
            params.start_value,
            params.end_value,
            params.periods
        )

        return StatsResult(
            operation="growth_rate",
            result=result,
            inputs={
                "start_value": params.start_value,
                "end_value": params.end_value,
                "periods": params.periods
            },
            interpretation=f"{result}% growth per period",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Growth rate calculation failed: {str(e)}")
        return StatsResult(
            operation="growth_rate",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def stats_volatility(
    params: VolatilityParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate volatility (coefficient of variation).

    Measures relative variability. Lower = more consistent.

    Args:
        params: Time series data
        ctx: FastMCP context

    Returns:
        StatsResult with volatility percentage
    """
    await ctx.info(f"Calculating volatility for {len(params.data)} data points")

    try:
        result = timeseries_helper.calculate_volatility(params.data)

        return StatsResult(
            operation="volatility",
            result=result,
            inputs={"data": params.data},
            interpretation=f"{result}% volatility ({'low' if result < 15 else 'moderate' if result < 30 else 'high'} variability)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Volatility calculation failed: {str(e)}")
        return StatsResult(
            operation="volatility",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


# Advanced NBA Metrics Tools

@mcp.tool()
async def nba_four_factors(
    params: FourFactorsParams,
    ctx: Context
) -> dict:
    """
    Calculate Dean Oliver's Four Factors of Basketball Success.

    The Four Factors (in order of importance):
    1. Shooting (eFG%)
    2. Turnovers (TOV%)
    3. Rebounding (ORB%/DRB%)
    4. Free Throws (FTR)

    Args:
        params: Complete offensive and defensive stats
        ctx: FastMCP context

    Returns:
        Dictionary with offensive and defensive Four Factors
    """
    await ctx.info("Calculating Four Factors")

    try:
        # Convert params to dict
        stats = params.model_dump()

        result = nba_metrics_helper.calculate_four_factors(stats)
        result["success"] = True

        return result
    except Exception as e:
        await ctx.error(f"Four Factors calculation failed: {str(e)}")
        return {
            "offensive": {},
            "defensive": {},
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def nba_turnover_percentage(
    params: TurnoverPercentageParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Turnover Percentage (TOV%).

    Estimate of turnovers per 100 plays. Lower is better.

    Args:
        params: Turnovers, FGA, and FTA
        ctx: FastMCP context

    Returns:
        NbaMetricResult with TOV%
    """
    await ctx.info("Calculating TOV%")

    try:
        result = nba_metrics_helper.calculate_turnover_percentage(
            params.tov,
            params.fga,
            params.fta
        )

        return NbaMetricResult(
            metric="TOV%",
            result=result,
            inputs={"tov": params.tov, "fga": params.fga, "fta": params.fta},
            interpretation=f"{result}% turnover rate ({'excellent' if result < 12 else 'good' if result < 14 else 'average' if result < 16 else 'poor'})",
            success=True
        )
    except Exception as e:
        await ctx.error(f"TOV% calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="TOV%",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_rebound_percentage(
    params: ReboundPercentageParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Rebound Percentage (REB%).

    Percentage of available rebounds grabbed.

    Args:
        params: Rebounds, team rebounds, opponent rebounds
        ctx: FastMCP context

    Returns:
        NbaMetricResult with REB%
    """
    await ctx.info("Calculating REB%")

    try:
        result = nba_metrics_helper.calculate_rebound_percentage(
            params.rebounds,
            params.team_rebounds,
            params.opp_rebounds
        )

        return NbaMetricResult(
            metric="REB%",
            result=result,
            inputs={
                "rebounds": params.rebounds,
                "team_rebounds": params.team_rebounds,
                "opp_rebounds": params.opp_rebounds
            },
            interpretation=f"{result}% rebound rate",
            success=True
        )
    except Exception as e:
        await ctx.error(f"REB% calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="REB%",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_assist_percentage(
    params: AssistPercentageParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Assist Percentage (AST%).

    Percentage of teammate FGs assisted while on court.

    Args:
        params: Assists, minutes, team stats
        ctx: FastMCP context

    Returns:
        NbaMetricResult with AST%
    """
    await ctx.info("Calculating AST%")

    try:
        result = nba_metrics_helper.calculate_assist_percentage(
            params.assists,
            params.minutes,
            params.team_minutes,
            params.team_fgm,
            params.player_fgm
        )

        return NbaMetricResult(
            metric="AST%",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"{result}% assist rate ({'elite playmaker' if result > 30 else 'good playmaker' if result > 20 else 'average' if result > 15 else 'low'})",
            success=True
        )
    except Exception as e:
        await ctx.error(f"AST% calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="AST%",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_steal_percentage(
    params: StealPercentageParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Steal Percentage (STL%).

    Steals per 100 opponent possessions while on court.

    Args:
        params: Steals, minutes, opponent possessions
        ctx: FastMCP context

    Returns:
        NbaMetricResult with STL%
    """
    await ctx.info("Calculating STL%")

    try:
        result = nba_metrics_helper.calculate_steal_percentage(
            params.steals,
            params.minutes,
            params.team_minutes,
            params.opp_possessions
        )

        return NbaMetricResult(
            metric="STL%",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"{result}% steal rate ({'elite' if result > 3 else 'good' if result > 2 else 'average'})",
            success=True
        )
    except Exception as e:
        await ctx.error(f"STL% calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="STL%",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_block_percentage(
    params: BlockPercentageParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Block Percentage (BLK%).

    Percentage of opponent 2PA blocked while on court.

    Args:
        params: Blocks, minutes, opponent 2PA
        ctx: FastMCP context

    Returns:
        NbaMetricResult with BLK%
    """
    await ctx.info("Calculating BLK%")

    try:
        result = nba_metrics_helper.calculate_block_percentage(
            params.blocks,
            params.minutes,
            params.team_minutes,
            params.opp_two_pa
        )

        return NbaMetricResult(
            metric="BLK%",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"{result}% block rate ({'elite rim protector' if result > 6 else 'good rim protector' if result > 4 else 'average' if result > 2 else 'low'})",
            success=True
        )
    except Exception as e:
        await ctx.error(f"BLK% calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="BLK%",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_win_shares(
    params: WinSharesParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Win Shares (WS).

    Measures player contribution in wins. Combines offensive and defensive contributions.
    Higher is better (league leaders typically ~12-15 WS per season).

    Args:
        params: Marginal offense, marginal defense, marginal points per win
        ctx: FastMCP context

    Returns:
        NbaMetricResult with WS value
    """
    await ctx.info("Calculating Win Shares")

    try:
        result = nba_metrics_helper.calculate_win_shares(
            params.marginal_offense,
            params.marginal_defense,
            params.marginal_points_per_win
        )

        return NbaMetricResult(
            metric="WS",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Win Shares: {result:.2f} (league leaders typically 12-15 WS per season)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Win Shares calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="WS",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def nba_box_plus_minus(
    params: BoxPlusMinusParams,
    ctx: Context
) -> NbaMetricResult:
    """
    Calculate Box Plus/Minus (BPM).

    Measures player contribution per 100 possessions relative to league average.
    0.0 = league average, positive = above average, negative = below average.

    Args:
        params: Player Efficiency Rating, team pace, league averages
        ctx: FastMCP context

    Returns:
        NbaMetricResult with BPM value
    """
    await ctx.info("Calculating Box Plus/Minus")

    try:
        result = nba_metrics_helper.calculate_box_plus_minus(
            params.per,
            params.team_pace,
            params.league_avg_per,
            params.league_avg_pace
        )

        return NbaMetricResult(
            metric="BPM",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Box Plus/Minus: {result:+.1f} ({'above' if result > 0 else 'below' if result < 0 else 'at'} league average)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Box Plus/Minus calculation failed: {str(e)}")
        return NbaMetricResult(
            metric="BPM",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


# =============================================================================
# Machine Learning Tools - Sprint 7
# =============================================================================

# Clustering Tools

@mcp.tool()
async def ml_kmeans_clustering(
    params: KMeansClusteringParams,
    ctx: Context
) -> StatsResult:
    """
    Perform K-means clustering on player/team data.

    Groups data points into K clusters based on similarity.
    Useful for player grouping, team archetypes, performance tiers.

    Args:
        params: Data points, k (number of clusters), parameters
        ctx: FastMCP context

    Returns:
        StatsResult with cluster assignments and centroids
    """
    await ctx.info(f"Running K-means clustering (k={params.k})")

    try:
        result = ml_clustering_helper.kmeans_clustering(
            data=params.data,
            k=params.k,
            max_iterations=params.max_iterations,
            tolerance=params.tolerance,
            random_seed=params.random_seed
        )

        return StatsResult(
            operation="kmeans_clustering",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Clustered {len(params.data)} points into {params.k} groups. Converged: {result['converged']}, Iterations: {result['iterations']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"K-means clustering failed: {str(e)}")
        return StatsResult(
            operation="kmeans_clustering",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_euclidean_distance(
    params: EuclideanDistanceParams,
    ctx: Context
) -> MathOperationResult:
    """
    Calculate Euclidean distance between two points.

    Measures straight-line distance in n-dimensional space.
    Used for similarity comparison, nearest neighbor search.

    Args:
        params: Two points (lists of coordinates)
        ctx: FastMCP context

    Returns:
        MathOperationResult with distance
    """
    await ctx.info("Calculating Euclidean distance")

    try:
        result = ml_clustering_helper.calculate_euclidean_distance(
            params.point1,
            params.point2
        )

        return MathOperationResult(
            operation="euclidean_distance",
            result=result,
            inputs=params.model_dump(),
            success=True
        )
    except Exception as e:
        await ctx.error(f"Euclidean distance calculation failed: {str(e)}")
        return MathOperationResult(
            operation="euclidean_distance",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_cosine_similarity(
    params: CosineSimilarityParams,
    ctx: Context
) -> MathOperationResult:
    """
    Calculate cosine similarity between two vectors.

    Measures similarity based on direction (angle), not magnitude.
    Better than Euclidean for normalized comparisons.

    Args:
        params: Two vectors
        ctx: FastMCP context

    Returns:
        MathOperationResult with similarity (-1 to 1)
    """
    await ctx.info("Calculating cosine similarity")

    try:
        result = ml_clustering_helper.calculate_cosine_similarity(
            params.vector1,
            params.vector2
        )

        interpretation = "identical" if result > 0.95 else "very similar" if result > 0.8 else "similar" if result > 0.5 else "different" if result > 0 else "opposite"

        return MathOperationResult(
            operation="cosine_similarity",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Similarity: {result:.3f} ({interpretation})",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Cosine similarity calculation failed: {str(e)}")
        return MathOperationResult(
            operation="cosine_similarity",
            result=0.0,
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_knn_classify(
    params: KnnParams,
    ctx: Context
) -> StatsResult:
    """
    Classify a point using K-nearest neighbors.

    Predicts class based on K most similar training examples.
    Simple, interpretable, no training phase needed.

    Args:
        params: Point to classify, training data, labels, k
        ctx: FastMCP context

    Returns:
        StatsResult with prediction and neighbors
    """
    await ctx.info(f"Running K-NN classification (k={params.k})")

    try:
        result = ml_clustering_helper.find_nearest_neighbors(
            point=params.point,
            data=params.data,
            labels=params.labels,
            k=params.k,
            distance_metric=params.distance_metric
        )

        return StatsResult(
            operation="knn_classify",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Predicted: {result['prediction']} (confidence: {result['confidence']:.1%})",
            success=True
        )
    except Exception as e:
        await ctx.error(f"K-NN classification failed: {str(e)}")
        return StatsResult(
            operation="knn_classify",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_hierarchical_clustering(
    params: HierarchicalClusteringParams,
    ctx: Context
) -> StatsResult:
    """
    Perform hierarchical (agglomerative) clustering.

    Builds hierarchy by merging most similar clusters.
    Good for discovering natural groupings without preset K.

    Args:
        params: Data, n_clusters, linkage method
        ctx: FastMCP context

    Returns:
        StatsResult with clusters and dendrogram
    """
    await ctx.info(f"Running hierarchical clustering ({params.linkage} linkage)")

    try:
        result = ml_clustering_helper.hierarchical_clustering(
            data=params.data,
            n_clusters=params.n_clusters,
            linkage=params.linkage
        )

        return StatsResult(
            operation="hierarchical_clustering",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Created {result['final_clusters']} clusters using {params.linkage} linkage",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Hierarchical clustering failed: {str(e)}")
        return StatsResult(
            operation="hierarchical_clustering",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# Classification Tools

@mcp.tool()
async def ml_logistic_regression_train(
    params: LogisticRegressionParams,
    ctx: Context
) -> StatsResult:
    """
    Train a logistic regression classifier.

    Binary classification using sigmoid function and gradient descent.
    Predicts probability of class 1 vs class 0.

    Args:
        params: Training data (X, y), learning rate, iterations
        ctx: FastMCP context

    Returns:
        StatsResult with trained weights and training info
    """
    await ctx.info(f"Training logistic regression ({len(params.X_train)} samples)")

    try:
        result = ml_classification_helper.logistic_regression(
            X_train=params.X_train,
            y_train=params.y_train,
            learning_rate=params.learning_rate,
            max_iterations=params.max_iterations,
            tolerance=params.tolerance
        )

        return StatsResult(
            operation="logistic_regression_train",
            result=result,
            inputs={"n_samples": len(params.X_train), "n_features": result['num_features']},
            interpretation=f"Model trained in {result['iterations']} iterations. Converged: {result['converged']}, Loss: {result['final_loss']:.4f}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Logistic regression training failed: {str(e)}")
        return StatsResult(
            operation="logistic_regression_train",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_logistic_predict(
    params: LogisticPredictParams,
    ctx: Context
) -> StatsResult:
    """
    Make predictions using trained logistic regression model.

    Args:
        params: Features (X), trained weights, threshold
        ctx: FastMCP context

    Returns:
        StatsResult with predictions and probabilities
    """
    await ctx.info(f"Predicting {len(params.X)} samples with logistic regression")

    try:
        result = ml_classification_helper.logistic_predict(
            X=params.X,
            weights=params.weights,
            threshold=params.threshold,
            return_probabilities=params.return_probabilities
        )

        return StatsResult(
            operation="logistic_predict",
            result=result,
            inputs={"n_samples": len(params.X)},
            interpretation=f"Predicted {result['num_samples']} samples",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Logistic prediction failed: {str(e)}")
        return StatsResult(
            operation="logistic_predict",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_naive_bayes_train(
    params: NaiveBayesTrainParams,
    ctx: Context
) -> StatsResult:
    """
    Train a Gaussian Naive Bayes classifier.

    Assumes features are independent given class.
    Fast, works well with small datasets, handles multiple classes.

    Args:
        params: Training data (X, y)
        ctx: FastMCP context

    Returns:
        StatsResult with trained model (class stats)
    """
    await ctx.info(f"Training Naive Bayes ({len(params.X_train)} samples)")

    try:
        result = ml_classification_helper.naive_bayes_train(
            X_train=params.X_train,
            y_train=params.y_train
        )

        return StatsResult(
            operation="naive_bayes_train",
            result=result,
            inputs={"n_samples": len(params.X_train)},
            interpretation=f"Model trained for {len(result['classes'])} classes",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Naive Bayes training failed: {str(e)}")
        return StatsResult(
            operation="naive_bayes_train",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_naive_bayes_predict(
    params: NaiveBayesPredictParams,
    ctx: Context
) -> StatsResult:
    """
    Make predictions using trained Naive Bayes model.

    Args:
        params: Features (X), trained model
        ctx: FastMCP context

    Returns:
        StatsResult with predictions and probabilities
    """
    await ctx.info(f"Predicting {len(params.X)} samples with Naive Bayes")

    try:
        result = ml_classification_helper.naive_bayes_predict(
            X=params.X,
            model=params.model
        )

        return StatsResult(
            operation="naive_bayes_predict",
            result=result,
            inputs={"n_samples": len(params.X)},
            interpretation=f"Predicted {result['num_samples']} samples",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Naive Bayes prediction failed: {str(e)}")
        return StatsResult(
            operation="naive_bayes_predict",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_decision_tree_train(
    params: DecisionTreeTrainParams,
    ctx: Context
) -> StatsResult:
    """
    Train a decision tree classifier (CART algorithm).

    Builds binary tree using Gini impurity.
    Interpretable (decision paths), handles non-linear patterns.

    Args:
        params: Training data, max depth, min samples
        ctx: FastMCP context

    Returns:
        StatsResult with trained tree
    """
    await ctx.info(f"Training decision tree (max_depth={params.max_depth})")

    try:
        result = ml_classification_helper.decision_tree_train(
            X_train=params.X_train,
            y_train=params.y_train,
            max_depth=params.max_depth,
            min_samples_split=params.min_samples_split
        )

        return StatsResult(
            operation="decision_tree_train",
            result=result,
            inputs={"n_samples": len(params.X_train)},
            interpretation=f"Tree trained with {result['num_leaves']} leaves",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Decision tree training failed: {str(e)}")
        return StatsResult(
            operation="decision_tree_train",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_decision_tree_predict(
    params: DecisionTreePredictParams,
    ctx: Context
) -> StatsResult:
    """
    Make predictions using trained decision tree.

    Args:
        params: Features (X), trained tree
        ctx: FastMCP context

    Returns:
        StatsResult with predictions and decision paths
    """
    await ctx.info(f"Predicting {len(params.X)} samples with decision tree")

    try:
        result = ml_classification_helper.decision_tree_predict(
            X=params.X,
            tree=params.tree
        )

        return StatsResult(
            operation="decision_tree_predict",
            result=result,
            inputs={"n_samples": len(params.X)},
            interpretation=f"Predicted {result['num_samples']} samples",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Decision tree prediction failed: {str(e)}")
        return StatsResult(
            operation="decision_tree_predict",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_random_forest_train(
    params: RandomForestTrainParams,
    ctx: Context
) -> StatsResult:
    """
    Train a random forest classifier (ensemble of trees).

    Trains multiple decision trees on bootstrap samples.
    More robust than single tree, reduces overfitting.

    Args:
        params: Training data, n_trees, parameters
        ctx: FastMCP context

    Returns:
        StatsResult with trained forest
    """
    await ctx.info(f"Training random forest ({params.n_trees} trees)")

    try:
        result = ml_classification_helper.random_forest_train(
            X_train=params.X_train,
            y_train=params.y_train,
            n_trees=params.n_trees,
            max_depth=params.max_depth,
            min_samples_split=params.min_samples_split,
            random_seed=params.random_seed
        )

        return StatsResult(
            operation="random_forest_train",
            result=result,
            inputs={"n_samples": len(params.X_train)},
            interpretation=f"Forest trained with {result['n_trees']} trees",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Random forest training failed: {str(e)}")
        return StatsResult(
            operation="random_forest_train",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_random_forest_predict(
    params: RandomForestPredictParams,
    ctx: Context
) -> StatsResult:
    """
    Make predictions using trained random forest.

    Args:
        params: Features (X), trained model
        ctx: FastMCP context

    Returns:
        StatsResult with predictions and vote counts
    """
    await ctx.info(f"Predicting {len(params.X)} samples with random forest")

    try:
        result = ml_classification_helper.random_forest_predict(
            X=params.X,
            model=params.model
        )

        return StatsResult(
            operation="random_forest_predict",
            result=result,
            inputs={"n_samples": len(params.X)},
            interpretation=f"Predicted {result['num_samples']} samples using {result['n_trees']} trees",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Random forest prediction failed: {str(e)}")
        return StatsResult(
            operation="random_forest_predict",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# Anomaly Detection Tools

@mcp.tool()
async def ml_zscore_outliers(
    params: ZScoreOutliersParams,
    ctx: Context
) -> StatsResult:
    """
    Detect outliers using Z-score method.

    Points with |z-score| > threshold are outliers.
    Simple, fast, works well for normally distributed data.

    Args:
        params: Data, threshold (default 3.0), optional labels
        ctx: FastMCP context

    Returns:
        StatsResult with outliers and z-scores
    """
    await ctx.info(f"Detecting outliers with Z-score (threshold={params.threshold})")

    try:
        result = ml_anomaly_helper.detect_outliers_zscore(
            data=params.data,
            threshold=params.threshold,
            labels=params.labels
        )

        return StatsResult(
            operation="zscore_outliers",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Found {result['outlier_count']} outliers ({result['outlier_percentage']:.1f}%)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Z-score outlier detection failed: {str(e)}")
        return StatsResult(
            operation="zscore_outliers",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_isolation_forest(
    params: IsolationForestParams,
    ctx: Context
) -> StatsResult:
    """
    Detect anomalies using Isolation Forest algorithm.

    Anomalies are easier to isolate (shorter path in tree).
    Works well for high-dimensional data, no assumptions about distribution.

    Args:
        params: Data, n_trees, contamination
        ctx: FastMCP context

    Returns:
        StatsResult with anomalies and scores
    """
    await ctx.info(f"Running Isolation Forest ({params.n_trees} trees)")

    try:
        result = ml_anomaly_helper.isolation_forest(
            data=params.data,
            n_trees=params.n_trees,
            sample_size=params.sample_size,
            contamination=params.contamination,
            random_seed=params.random_seed
        )

        return StatsResult(
            operation="isolation_forest",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Found {result['anomaly_count']} anomalies ({result['anomaly_percentage']:.1f}%)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Isolation forest failed: {str(e)}")
        return StatsResult(
            operation="isolation_forest",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_local_outlier_factor(
    params: LocalOutlierFactorParams,
    ctx: Context
) -> StatsResult:
    """
    Detect anomalies using Local Outlier Factor (LOF).

    Measures local density deviation w.r.t. neighbors.
    Catches context-dependent outliers that global methods miss.

    Args:
        params: Data, k (neighbors), contamination
        ctx: FastMCP context

    Returns:
        StatsResult with anomalies and LOF scores
    """
    await ctx.info(f"Running Local Outlier Factor (k={params.k})")

    try:
        result = ml_anomaly_helper.local_outlier_factor(
            data=params.data,
            k=params.k,
            contamination=params.contamination
        )

        return StatsResult(
            operation="local_outlier_factor",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Found {result['anomaly_count']} anomalies ({result['anomaly_percentage']:.1f}%)",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Local outlier factor failed: {str(e)}")
        return StatsResult(
            operation="local_outlier_factor",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# Feature Engineering Tools

@mcp.tool()
async def ml_normalize_features(
    params: NormalizeFeaturesParams,
    ctx: Context
) -> StatsResult:
    """
    Normalize/standardize features for ML.

    Methods: min-max (to range), z-score (mean=0, std=1),
    robust (median/IQR), max-abs (to [-1,1]).

    Args:
        params: Data, method, feature_range (for min-max)
        ctx: FastMCP context

    Returns:
        StatsResult with normalized data and statistics
    """
    await ctx.info(f"Normalizing features ({params.method})")

    try:
        result = ml_feature_helper.normalize_features(
            data=params.data,
            method=params.method,
            feature_range=params.feature_range
        )

        return StatsResult(
            operation="normalize_features",
            result=result,
            inputs=params.model_dump(),
            interpretation=f"Normalized {result['num_samples']} samples with {result['num_features']} features using {params.method}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Feature normalization failed: {str(e)}")
        return StatsResult(
            operation="normalize_features",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_feature_importance(
    params: FeatureImportanceParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate feature importance using permutation importance.

    Measures how much performance drops when feature is shuffled.
    Shows which features are most important for predictions.

    Args:
        params: Features (X), labels (y), model predictions, n_repeats
        ctx: FastMCP context

    Returns:
        StatsResult with importance scores and ranking
    """
    await ctx.info(f"Calculating feature importance ({params.n_repeats} repeats)")

    try:
        result = ml_feature_helper.calculate_feature_importance(
            X=params.X,
            y=params.y,
            model_predictions=params.model_predictions,
            n_repeats=params.n_repeats,
            random_seed=params.random_seed
        )

        return StatsResult(
            operation="feature_importance",
            result=result,
            inputs={"n_features": result['num_features']},
            interpretation=f"Most important feature: #{result['feature_ranking'][0]} (score: {result['importance_scores'][result['feature_ranking'][0]]:.3f})",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Feature importance calculation failed: {str(e)}")
        return StatsResult(
            operation="feature_importance",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# =============================================================================
# Sprint 8: ML Evaluation & Validation Tools
# =============================================================================

# Classification Metrics (6 tools)

@mcp.tool()
async def ml_accuracy_score(
    params: AccuracyScoreParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate classification accuracy score.

    Accuracy measures the proportion of correct predictions.
    Useful for balanced datasets where all classes are equally important.

    NBA Use Cases:
    - Evaluate All-Star prediction models
    - Assess win/loss prediction accuracy
    - Validate playoff qualification predictions

    Returns:
    - accuracy: Accuracy score (0-1)
    - percentage: Accuracy as percentage
    - correct_predictions: Number of correct predictions
    - total_predictions: Total number of predictions
    - interpretation: Quality rating (Excellent/Good/Fair/Poor)
    """
    await ctx.info(f"Calculating accuracy score for {len(params.y_true)} predictions")

    try:
        result = ml_evaluation_helper.accuracy_score(
            y_true=params.y_true,
            y_pred=params.y_pred
        )

        return StatsResult(
            operation="accuracy_score",
            result=result,
            inputs={"n_predictions": len(params.y_true)},
            interpretation=f"Accuracy: {result['percentage']:.2f}% - {result['interpretation']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Accuracy score calculation failed: {str(e)}")
        return StatsResult(
            operation="accuracy_score",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_precision_recall_f1(
    params: PrecisionRecallF1Params,
    ctx: Context
) -> StatsResult:
    """
    Calculate precision, recall, and F1-score for classification.

    - Precision: What proportion of positive predictions are correct?
    - Recall: What proportion of actual positives are identified?
    - F1-Score: Harmonic mean of precision and recall

    NBA Use Cases:
    - Evaluate injury risk prediction (high recall needed)
    - Assess MVP candidate identification (balance precision/recall)
    - Validate draft success prediction models

    Returns:
    - precision: Positive predictive value (0-1)
    - recall: True positive rate (0-1)
    - f1_score: Harmonic mean of precision and recall
    - support: Number of samples per class
    - interpretation: Quality assessment
    """
    await ctx.info(f"Calculating precision, recall, and F1-score (average={params.average})")

    try:
        result = ml_evaluation_helper.precision_recall_f1(
            y_true=params.y_true,
            y_pred=params.y_pred,
            average=params.average,
            pos_label=params.pos_label
        )

        return StatsResult(
            operation="precision_recall_f1",
            result=result,
            inputs={"average": params.average, "n_predictions": len(params.y_true)},
            interpretation=f"F1={result['f1_score']:.3f}, Precision={result['precision']:.3f}, Recall={result['recall']:.3f}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Precision/recall/F1 calculation failed: {str(e)}")
        return StatsResult(
            operation="precision_recall_f1",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_confusion_matrix(
    params: ConfusionMatrixParams,
    ctx: Context
) -> StatsResult:
    """
    Generate confusion matrix for binary classification.

    Shows true positives, false positives, true negatives, false negatives.
    Essential for understanding model error patterns.

    NBA Use Cases:
    - Analyze All-Star prediction errors (false positives vs false negatives)
    - Evaluate playoff berth prediction mistakes
    - Assess player position classification confusion

    Returns:
    - matrix: 2x2 confusion matrix [[TN, FP], [FN, TP]]
    - true_positives: Correctly predicted positive cases
    - false_positives: Incorrectly predicted positive cases
    - true_negatives: Correctly predicted negative cases
    - false_negatives: Incorrectly predicted negative cases
    - accuracy: Overall accuracy
    - sensitivity: True positive rate (recall)
    - specificity: True negative rate
    - interpretation: Analysis of error patterns
    """
    await ctx.info(f"Generating confusion matrix for {len(params.y_true)} predictions")

    try:
        result = ml_evaluation_helper.confusion_matrix(
            y_true=params.y_true,
            y_pred=params.y_pred,
            pos_label=params.pos_label
        )

        return StatsResult(
            operation="confusion_matrix",
            result=result,
            inputs={"pos_label": params.pos_label, "n_predictions": len(params.y_true)},
            interpretation=f"TP={result['true_positives']}, FP={result['false_positives']}, TN={result['true_negatives']}, FN={result['false_negatives']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Confusion matrix generation failed: {str(e)}")
        return StatsResult(
            operation="confusion_matrix",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_roc_auc_score(
    params: RocAucScoreParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate ROC curve and AUC score for binary classification.

    ROC (Receiver Operating Characteristic) shows classifier performance
    across all thresholds. AUC (Area Under Curve) summarizes overall quality.

    NBA Use Cases:
    - Evaluate All-Star probability predictions
    - Assess draft success likelihood models
    - Validate playoff qualification probability models

    Returns:
    - auc: Area under ROC curve (0-1, higher is better)
    - roc_curve: List of (fpr, tpr, threshold) points
    - interpretation: AUC quality rating
    - optimal_threshold: Threshold maximizing TPR - FPR
    """
    await ctx.info(f"Calculating ROC-AUC score with {params.num_thresholds} thresholds")

    try:
        result = ml_evaluation_helper.roc_auc_score(
            y_true=params.y_true,
            y_scores=params.y_scores,
            num_thresholds=params.num_thresholds
        )

        return StatsResult(
            operation="roc_auc_score",
            result=result,
            inputs={"num_thresholds": params.num_thresholds, "n_predictions": len(params.y_true)},
            interpretation=f"AUC={result['auc']:.3f} - {result['interpretation']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"ROC-AUC calculation failed: {str(e)}")
        return StatsResult(
            operation="roc_auc_score",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_classification_report(
    params: ClassificationReportParams,
    ctx: Context
) -> StatsResult:
    """
    Generate comprehensive classification report with per-class metrics.

    Provides precision, recall, F1-score, and support for each class,
    plus macro/weighted averages.

    NBA Use Cases:
    - Evaluate multi-position classification (PG/SG/SF/PF/C)
    - Assess player tier classification (All-Star/Starter/Rotation/Bench)
    - Validate team performance classification (Elite/Playoff/Mediocre/Lottery)

    Returns:
    - per_class_metrics: Dict of metrics for each class
    - macro_avg: Unweighted average across classes
    - weighted_avg: Sample-weighted average
    - overall_accuracy: Total accuracy
    - interpretation: Summary of model performance
    """
    await ctx.info(f"Generating classification report for {len(params.y_true)} predictions")

    try:
        result = ml_evaluation_helper.classification_report(
            y_true=params.y_true,
            y_pred=params.y_pred
        )

        num_classes = len(result['per_class_metrics'])
        return StatsResult(
            operation="classification_report",
            result=result,
            inputs={"n_predictions": len(params.y_true), "n_classes": num_classes},
            interpretation=f"{num_classes} classes - Macro F1={result['macro_avg']['f1_score']:.3f}, Accuracy={result['overall_accuracy']:.3f}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Classification report generation failed: {str(e)}")
        return StatsResult(
            operation="classification_report",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_log_loss(
    params: LogLossParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate log loss (cross-entropy loss) for probabilistic predictions.

    Measures prediction confidence calibration. Lower is better.
    Penalizes confident wrong predictions heavily.

    NBA Use Cases:
    - Evaluate All-Star probability calibration
    - Assess playoff qualification likelihood models
    - Validate win probability predictions

    Returns:
    - log_loss: Cross-entropy loss (lower is better)
    - mean_predicted_probability: Average probability assigned to true class
    - interpretation: Loss quality rating
    """
    await ctx.info(f"Calculating log loss for {len(params.y_true)} probabilistic predictions")

    try:
        result = ml_evaluation_helper.log_loss(
            y_true=params.y_true,
            y_pred_proba=params.y_pred_proba,
            eps=params.eps
        )

        return StatsResult(
            operation="log_loss",
            result=result,
            inputs={"eps": params.eps, "n_predictions": len(params.y_true)},
            interpretation=f"Log Loss={result['log_loss']:.4f} - {result['interpretation']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Log loss calculation failed: {str(e)}")
        return StatsResult(
            operation="log_loss",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# Regression Metrics (3 tools)

@mcp.tool()
async def ml_mse_rmse_mae(
    params: MseRmseMaeParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate MSE, RMSE, and MAE for regression predictions.

    - MSE: Mean Squared Error (penalizes large errors)
    - RMSE: Root Mean Squared Error (same units as target)
    - MAE: Mean Absolute Error (robust to outliers)

    NBA Use Cases:
    - Evaluate points-per-game prediction accuracy
    - Assess win total forecasting error
    - Validate salary prediction models

    Returns:
    - mse: Mean squared error
    - rmse: Root mean squared error
    - mae: Mean absolute error
    - interpretation: Error magnitude assessment
    """
    await ctx.info(f"Calculating MSE, RMSE, MAE for {len(params.y_true)} predictions")

    try:
        result = ml_evaluation_helper.mse_rmse_mae(
            y_true=params.y_true,
            y_pred=params.y_pred
        )

        return StatsResult(
            operation="mse_rmse_mae",
            result=result,
            inputs={"n_predictions": len(params.y_true)},
            interpretation=f"RMSE={result['rmse']:.3f}, MAE={result['mae']:.3f}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"MSE/RMSE/MAE calculation failed: {str(e)}")
        return StatsResult(
            operation="mse_rmse_mae",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_r2_score(
    params: R2ScoreParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate R² (coefficient of determination) for regression.

    R² measures proportion of variance explained by the model.
    - 1.0: Perfect prediction
    - 0.0: Model no better than mean baseline
    - Negative: Model worse than mean baseline

    NBA Use Cases:
    - Evaluate PPG prediction model fit
    - Assess team win total regression quality
    - Validate player valuation models

    Returns:
    - r2_score: Coefficient of determination
    - interpretation: Model fit quality rating
    """
    await ctx.info(f"Calculating R² score for {len(params.y_true)} predictions")

    try:
        result = ml_evaluation_helper.r2_score(
            y_true=params.y_true,
            y_pred=params.y_pred
        )

        return StatsResult(
            operation="r2_score",
            result=result,
            inputs={"n_predictions": len(params.y_true)},
            interpretation=f"R²={result['r2_score']:.3f} - {result['interpretation']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"R² calculation failed: {str(e)}")
        return StatsResult(
            operation="r2_score",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_mape(
    params: MapeParams,
    ctx: Context
) -> StatsResult:
    """
    Calculate Mean Absolute Percentage Error (MAPE).

    MAPE measures average prediction error as a percentage.
    Scale-independent, useful for comparing across different ranges.

    NBA Use Cases:
    - Evaluate PPG prediction percentage error
    - Assess salary prediction accuracy
    - Validate revenue forecasting models

    Returns:
    - mape: Mean absolute percentage error (%)
    - interpretation: Error magnitude rating

    Note: y_true cannot contain zeros (division by zero)
    """
    await ctx.info(f"Calculating MAPE for {len(params.y_true)} predictions")

    try:
        result = ml_evaluation_helper.mean_absolute_percentage_error(
            y_true=params.y_true,
            y_pred=params.y_pred
        )

        return StatsResult(
            operation="mape",
            result=result,
            inputs={"n_predictions": len(params.y_true)},
            interpretation=f"MAPE={result['mape']:.2f}% - {result['interpretation']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"MAPE calculation failed: {str(e)}")
        return StatsResult(
            operation="mape",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# Cross-Validation (3 tools)

@mcp.tool()
async def ml_k_fold_split(
    params: KFoldSplitParams,
    ctx: Context
) -> StatsResult:
    """
    Generate K-fold cross-validation splits.

    Divides data into K equal-sized folds for robust model evaluation.
    Each fold serves as validation set once while others are training set.

    NBA Use Cases:
    - Validate All-Star prediction models across seasons
    - Evaluate playoff models on different data subsets
    - Test player performance models with cross-validation

    Returns:
    - n_folds: Number of folds
    - n_samples: Total number of samples
    - fold_sizes: List of samples per fold
    - splits: List of (train_indices, val_indices) for each fold
    - interpretation: Split configuration summary
    """
    await ctx.info(f"Generating {params.n_folds}-fold CV splits for {params.n_samples} samples")

    try:
        result = ml_validation_helper.k_fold_split(
            n_samples=params.n_samples,
            n_folds=params.n_folds,
            shuffle=params.shuffle,
            random_seed=params.random_seed
        )

        return StatsResult(
            operation="k_fold_split",
            result=result,
            inputs={"n_folds": params.n_folds, "n_samples": params.n_samples},
            interpretation=f"{params.n_folds} folds, fold sizes: {result['fold_sizes']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"K-fold split generation failed: {str(e)}")
        return StatsResult(
            operation="k_fold_split",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_stratified_k_fold_split(
    params: StratifiedKFoldSplitParams,
    ctx: Context
) -> StatsResult:
    """
    Generate stratified K-fold cross-validation splits.

    Ensures each fold has same class distribution as full dataset.
    Critical for imbalanced classification tasks.

    NBA Use Cases:
    - Validate All-Star models (imbalanced: few All-Stars, many non-All-Stars)
    - Evaluate MVP prediction (highly imbalanced: 1 MVP, many non-MVPs)
    - Test position classification (some positions rarer than others)

    Returns:
    - n_folds: Number of folds
    - n_samples: Total number of samples
    - class_distribution: Samples per class across folds
    - splits: List of (train_indices, val_indices) for each fold
    - interpretation: Stratification summary
    """
    await ctx.info(f"Generating stratified {params.n_folds}-fold CV splits for {len(params.y)} samples")

    try:
        result = ml_validation_helper.stratified_k_fold_split(
            y=params.y,
            n_folds=params.n_folds,
            shuffle=params.shuffle,
            random_seed=params.random_seed
        )

        return StatsResult(
            operation="stratified_k_fold_split",
            result=result,
            inputs={"n_folds": params.n_folds, "n_samples": len(params.y)},
            interpretation=f"{params.n_folds} stratified folds, class distribution: {result['class_distribution']}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Stratified K-fold split generation failed: {str(e)}")
        return StatsResult(
            operation="stratified_k_fold_split",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_cross_validate(
    params: CrossValidateParams,
    ctx: Context
) -> StatsResult:
    """
    Cross-validation helper that automatically chooses K-fold or stratified K-fold.

    Simplifies cross-validation by handling both standard and stratified splits
    with a single interface.

    NBA Use Cases:
    - Quick model validation setup
    - Standardize CV across different prediction tasks
    - Automate train/validation split generation

    Returns:
    - cv_type: Type of CV used (k-fold or stratified)
    - n_folds: Number of folds
    - n_samples: Total number of samples
    - splits: List of (train_indices, val_indices)
    - interpretation: CV configuration summary
    """
    cv_type = "stratified K-fold" if params.stratify else "K-fold"
    await ctx.info(f"Setting up {cv_type} cross-validation ({params.n_folds} folds, {params.n_samples} samples)")

    try:
        result = ml_validation_helper.cross_validate(
            n_samples=params.n_samples,
            n_folds=params.n_folds,
            stratify=params.stratify,
            y=params.y,
            shuffle=params.shuffle,
            random_seed=params.random_seed
        )

        return StatsResult(
            operation="cross_validate",
            result=result,
            inputs={"n_folds": params.n_folds, "stratify": params.stratify},
            interpretation=f"{result['cv_type']}: {params.n_folds} folds, {params.n_samples} samples",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Cross-validation setup failed: {str(e)}")
        return StatsResult(
            operation="cross_validate",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# Model Comparison (2 tools)

@mcp.tool()
async def ml_compare_models(
    params: CompareModelsParams,
    ctx: Context
) -> StatsResult:
    """
    Compare multiple models side-by-side with various metrics.

    Evaluate multiple models on same data to identify best performer.
    Supports custom metric selection.

    NBA Use Cases:
    - Compare All-Star prediction models (Logistic vs Naive Bayes vs Random Forest)
    - Evaluate playoff qualification algorithms
    - Benchmark player clustering methods

    Returns:
    - models: List of model names
    - metrics_computed: Metrics calculated for comparison
    - comparison_table: Dict of {metric: {model: score}}
    - best_model_per_metric: Best model for each metric
    - interpretation: Overall comparison summary
    """
    await ctx.info(f"Comparing {len(params.models)} models on {len(params.y_true)} samples")

    try:
        result = ml_validation_helper.compare_models(
            models=params.models,
            y_true=params.y_true,
            metrics=params.metrics
        )

        return StatsResult(
            operation="compare_models",
            result=result,
            inputs={"n_models": len(params.models), "n_samples": len(params.y_true)},
            interpretation=f"Compared {len(params.models)} models on {len(result['metrics_computed'])} metrics",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Model comparison failed: {str(e)}")
        return StatsResult(
            operation="compare_models",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


@mcp.tool()
async def ml_paired_ttest(
    params: PairedTTestParams,
    ctx: Context
) -> StatsResult:
    """
    Perform paired t-test to assess if two models are statistically different.

    Tests null hypothesis that model performance difference is zero.
    Use with cross-validation scores to determine if one model is
    significantly better than another.

    NBA Use Cases:
    - Test if Random Forest significantly outperforms Logistic Regression
    - Validate statistical significance of model improvements
    - Compare clustering algorithms rigorously

    Returns:
    - t_statistic: Paired t-test statistic
    - p_value: Probability of observing difference by chance
    - degrees_of_freedom: Sample size - 1
    - mean_difference: Average score difference (A - B)
    - is_significant: Whether difference is significant at alpha level
    - interpretation: Statistical conclusion
    """
    await ctx.info(f"Running paired t-test on {len(params.scores_a)} CV scores (alpha={params.alpha})")

    try:
        result = ml_validation_helper.paired_ttest(
            scores_a=params.scores_a,
            scores_b=params.scores_b,
            alpha=params.alpha
        )

        return StatsResult(
            operation="paired_ttest",
            result=result,
            inputs={"alpha": params.alpha, "n_folds": len(params.scores_a)},
            interpretation=f"p={result['p_value']:.4f}, {'significant' if result['is_significant'] else 'not significant'} at α={params.alpha}",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Paired t-test failed: {str(e)}")
        return StatsResult(
            operation="paired_ttest",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# Hyperparameter Tuning (1 tool)

@mcp.tool()
async def ml_grid_search(
    params: GridSearchParams,
    ctx: Context
) -> StatsResult:
    """
    Generate parameter combinations for grid search hyperparameter tuning.

    Creates all possible combinations of parameters to test.
    Essential for finding optimal model configurations.

    NBA Use Cases:
    - Tune K-means clustering (k, max_iterations, tolerance)
    - Optimize Random Forest (n_trees, max_depth, min_samples_split)
    - Configure Logistic Regression (learning_rate, max_iterations)

    Returns:
    - param_grid: Original parameter grid
    - n_combinations: Total number of combinations
    - combinations: List of parameter dictionaries to test
    - interpretation: Grid search configuration summary
    """
    await ctx.info(f"Generating grid search combinations for {len(params.param_grid)} parameters")

    try:
        result = ml_validation_helper.grid_search(
            param_grid=params.param_grid,
            n_combinations=params.n_combinations
        )

        return StatsResult(
            operation="grid_search",
            result=result,
            inputs={"n_parameters": len(params.param_grid)},
            interpretation=f"Generated {result['n_combinations']} parameter combinations",
            success=True
        )
    except Exception as e:
        await ctx.error(f"Grid search generation failed: {str(e)}")
        return StatsResult(
            operation="grid_search",
            result={},
            inputs={},
            success=False,
            error=str(e)
        )


# =============================================================================
# Prompts - Guide users on how to interact with NBA data
# =============================================================================

@mcp.prompt()
async def suggest_queries() -> list[dict]:
    """
    Suggest common NBA queries and show what data is available.

    This prompt helps users understand what they can query.
    """
    return [{
        "role": "user",
        "content": {
            "type": "text",
            "text": """# NBA Database Query Examples

I can help you analyze NBA data! Here are some example queries:

## 🏀 Player Statistics
- "Show me LeBron James' stats for the 2023-24 season"
- "Compare Stephen Curry and Damian Lillard's three-point shooting"
- "Who are the top 10 scorers this season?"
- "Show me player efficiency ratings (PER) for point guards"

## 🏆 Team Analysis
- "What is the Lakers' win-loss record this season?"
- "Show me the top 5 teams by offensive rating"
- "Compare the Warriors and Celtics defensive stats"
- "Which team has the best home court advantage?"

## 📊 Game Data
- "Show me all games from December 2023"
- "What were the highest scoring games this season?"
- "Show me Lakers vs Celtics game history"
- "Display playoff bracket results"

## 📈 Advanced Analytics
- "Calculate team net rating over the last 10 games"
- "Show correlation between pace and offensive efficiency"
- "Compare player stats in wins vs losses"

**Available Tables:**
Use `list_tables` to see all available tables, or `get_table_schema` to see column definitions.

What NBA data would you like to explore?"""
        }
    }]


@mcp.prompt()
async def analyze_team_performance(team_name: str, season: str = "2024") -> list[dict]:
    """
    Generate a comprehensive team performance analysis prompt.

    Args:
        team_name: NBA team name (e.g., "Lakers", "Warriors", "Celtics")
        season: Season year (default: "2024")
    """
    return [{
        "role": "user",
        "content": {
            "type": "text",
            "text": f"""# Analyze {team_name} Performance - {season} Season

Please provide a comprehensive analysis of the {team_name}'s performance including:

## 📊 Overall Record
- Win-loss record and winning percentage
- Home vs away performance
- Conference standings

## 🎯 Offensive Performance
- Points per game
- Field goal percentage
- Three-point shooting percentage
- Free throw percentage
- Assists per game
- Offensive rating

## 🛡️ Defensive Performance
- Points allowed per game
- Opponent field goal percentage
- Steals and blocks per game
- Defensive rating

## ⭐ Key Players
- Top 3 scorers with averages
- Leading rebounder and assists leader
- Most efficient player (PER/TS%)

## 📈 Trends
- Recent form (last 10 games)
- Month-by-month performance
- Performance against playoff teams

## 🏆 Playoff Outlook
- Current playoff position
- Strength of remaining schedule
- Key factors for success

Use the NBA database to gather this data and provide insights."""
        }
    }]


@mcp.prompt()
async def compare_players(player1: str, player2: str, season: str = "2024") -> list[dict]:
    """
    Generate a detailed player comparison prompt.

    Args:
        player1: First player name
        player2: Second player name
        season: Season year (default: "2024")
    """
    return [{
        "role": "user",
        "content": {
            "type": "text",
            "text": f"""# Player Comparison: {player1} vs {player2} ({season} Season)

Please compare these two players across multiple dimensions:

## 📊 Traditional Stats
- Points per game
- Rebounds per game
- Assists per game
- Steals and blocks
- Field goal percentage
- Three-point percentage
- Free throw percentage

## 📈 Advanced Metrics
- Player Efficiency Rating (PER)
- True Shooting Percentage (TS%)
- Usage Rate
- Win Shares
- Box Plus/Minus
- Value Over Replacement Player (VORP)

## 🎯 Shooting Analysis
- Shot distribution by zone
- Shooting percentages by distance
- Clutch performance (last 5 minutes)
- Performance on back-to-backs

## 🏆 Impact Analysis
- Team record when starting
- Plus/minus differential
- Performance in wins vs losses
- Head-to-head matchups

## 💪 Strengths & Weaknesses
Identify each player's:
- Greatest strengths
- Areas for improvement
- Best matchups
- Situational advantages

Query the NBA database and provide a data-driven comparison."""
        }
    }]


@mcp.prompt()
async def game_analysis(game_id: str) -> list[dict]:
    """
    Generate a detailed game analysis prompt.

    Args:
        game_id: Unique game identifier
    """
    return [{
        "role": "user",
        "content": {
            "type": "text",
            "text": f"""# Game Analysis: Game ID {game_id}

Please analyze this game in detail:

## 📋 Game Overview
- Teams and final score
- Date and venue
- Quarter-by-quarter breakdown
- Attendance

## ⭐ Key Performances
- Top scorers from each team
- Best stat lines
- Efficiency leaders
- Plus/minus leaders

## 📊 Team Statistics
- Shooting percentages (FG%, 3P%, FT%)
- Rebounds (offensive/defensive)
- Assists and turnovers
- Points in the paint
- Fast break points
- Bench contribution

## 🔄 Game Flow
- Largest lead
- Lead changes
- Runs and momentum shifts
- Critical moments (last 2 minutes)

## 🎯 Turning Points
- Key plays or runs
- Impact of substitutions
- Coaching decisions
- Injury impacts

Use the box score and play-by-play data to provide comprehensive analysis."""
        }
    }]


@mcp.prompt()
async def recommend_books(
    project_goal: str,
    current_knowledge: str = "Beginner",
    focus_area: str = "General"
) -> list[dict]:
    """
    Get AI-driven book recommendations based on project goals.

    Perfect for Google Gemini to analyze your book library and recommend
    reading paths. Includes math content awareness for technical books.

    Args:
        project_goal: What you want to build/learn (e.g., "NBA player prediction system")
        current_knowledge: Your current skill level (Beginner/Intermediate/Advanced)
        focus_area: Specific area of focus (e.g., "Machine Learning", "Statistics", "NBA Analytics")
    """
    return [{
        "role": "user",
        "content": {
            "type": "text",
            "text": f"""# Book Recommendations for: {project_goal}

## 📚 Your Goal
**Project**: {project_goal}
**Current Level**: {current_knowledge}
**Focus Area**: {focus_area}

## 🎯 Task
Please analyze the available books in the library and recommend:

### 1. Discovery Phase
First, use `list_books` to see what books are available. Pay attention to:
- Book titles and paths
- `has_math` flag (indicates mathematical content)
- `math_difficulty` score (0-1, higher = more advanced math)
- `recommended_mcp` field (suggests "math-mcp" if book has formulas)

### 2. Selection Criteria
Recommend books that:
- Match the project goal and focus area
- Align with current knowledge level
- Build progressively (start easy, increase difficulty)
- Cover complementary topics (theory + practice)

### 3. Math Content Handling
For books with `has_math: true`:
- Note that LaTeX formulas are preserved when reading
- Suggest using **math-mcp** server alongside for computations
- Example workflow: Read formula → Extract values → math-mcp tools → Compute

**Available math-mcp tools**:
- Basic: add, subtract, multiply, division, modulo, sum
- Statistics: mean, median, mode, min, max
- Trigonometry: sin, cos, tan, arcsin, arccos, arctan
- Rounding: floor, ceiling, round
- Conversion: degreesToRadians, radiansToDegrees

### 4. Reading Strategy
Recommend:
- **Reading order** (which book first, second, third)
- **Key sections** to focus on (use `search_books` to find topics)
- **Chunk size** based on content:
  - 50k chars: Default, works with all LLMs
  - 100k chars: For denser technical content (Gemini/Claude)
  - 200k chars: For long chapters (Gemini 1.5 Pro only)
- **Time estimates** (pages/chapters to read)
- **Practical exercises** from books to implement

### 5. Integration Plan
Show how books connect to project:
- Which book covers foundational concepts?
- Which book provides implementation details?
- Which book offers advanced techniques?
- How do books complement each other?

### 6. Math-MCP Integration Examples
For math books, provide examples like:

**Example 1: Statistics Book**
```
Book: "Standard deviation: σ = √(Σ(x-μ)²/n)"
You read formula, I extract: x = [23, 28, 25, 30, 27]
Call math-mcp:
  1. mean(x) → 26.6
  2. subtract each value from mean → [-3.6, 1.4, -1.6, 3.4, 0.4]
  3. multiply each by itself → [12.96, 1.96, 2.56, 11.56, 0.16]
  4. sum() → 29.2
  5. division(29.2, 5) → 5.84
  6. √5.84 → 2.42 (use calculator or approximation)
Result: σ ≈ 2.42
```

**Example 2: Trigonometry Book**
```
Book: "Convert 45° to radians and find sine"
Call math-mcp:
  1. degreesToRadians(45) → 0.7854
  2. sin(0.7854) → 0.7071
Result: sin(45°) ≈ 0.707
```

## 📖 Output Format
Provide:
1. **Recommended Books** (3-5 books, prioritized)
2. **Reading Order** with rationale
3. **Key Chapters/Sections** to focus on
4. **Math Integration Points** (where to use math-mcp)
5. **Time Estimate** for each book
6. **Practical Milestones** (what you'll be able to build after each book)

## 🚀 Getting Started
Now use `list_books` to discover the library, then provide your personalized reading plan!"""
        }
    }]


# =============================================================================
# Completions - Argument Auto-Complete
# =============================================================================

# Note: Completions are currently not supported in FastMCP's stdio transport.
# They are documented here for future use when FastMCP adds full completion support.
# For now, these are commented out to avoid errors.

# @mcp.completion()
# async def team_name_completion(argument_name: str, argument_value: str, ctx: Context) -> list[str]:
#     """Provide team name completions as user types."""
#     rds = ctx.request_context.lifespan_context["rds_connector"]
#     query = """
#         SELECT DISTINCT team_name FROM (
#             SELECT home_team as team_name FROM games
#             UNION SELECT away_team as team_name FROM games
#         ) teams
#         WHERE LOWER(team_name) LIKE LOWER($1)
#         ORDER BY team_name LIMIT 10
#     """
#     results = await rds.execute_query(query, params=(f"%{argument_value}%",))
#     return [row['team_name'] for row in results.get('rows', [])] if results.get('success') else []


# =============================================================================
# Resource Templates - NBA Data Access
# =============================================================================

@mcp.resource("nba://database/schema")
async def database_schema(ctx: Context) -> str:
    """
    Get complete database schema as a resource.

    Returns JSON with all tables and their structures.
    """
    await ctx.info("Fetching database schema...")

    rds_connector = ctx.request_context.lifespan_context["rds_connector"]

    try:
        # Get all tables
        tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        tables_result = await rds_connector.execute_query(tables_query)

        if not tables_result.get('success'):
            return '{"error": "Failed to fetch tables"}'

        schema_info = {}

        # Get schema for each table
        for table_row in tables_result['rows']:
            table_name = table_row['table_name']

            columns_query = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            columns_result = await rds_connector.execute_query(columns_query)

            if columns_result.get('success'):
                schema_info[table_name] = [
                    {
                        'name': col['column_name'],
                        'type': col['data_type'],
                        'nullable': col['is_nullable'] == 'YES',
                        'default': col['column_default']
                    }
                    for col in columns_result['rows']
                ]

        import json
        return json.dumps(schema_info, indent=2)

    except Exception as e:
        await ctx.error(f"Failed to fetch schema: {str(e)}")
        return f'{{"error": "{str(e)}"}}'


# =============================================================================
# Custom Routes - Health Checks & Metrics
# =============================================================================

from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime
import time

# Metrics tracking
query_count = 0
error_count = 0
start_time = time.time()


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """
    Health check endpoint for load balancers and monitoring.

    Returns JSON with service status and component health.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - start_time),
        "components": {}
    }

    # Check database connectivity
    try:
        from .fastmcp_lifespan import nba_lifespan

        class MockApp:
            pass

        async with nba_lifespan(MockApp()) as context:
            rds = context['rds_connector']
            result = await rds.execute_query("SELECT 1 as health_check")

            if result.get('success'):
                health_status["components"]["database"] = {
                    "status": "healthy",
                    "message": "Connection successful"
                }
            else:
                health_status["components"]["database"] = {
                    "status": "unhealthy",
                    "message": result.get('error', 'Query failed')
                }
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check S3 connectivity
    try:
        from .fastmcp_lifespan import nba_lifespan

        class MockApp:
            pass

        async with nba_lifespan(MockApp()) as context:
            s3 = context['s3_connector']
            result = await asyncio.to_thread(
                s3.list_objects,
                prefix="",
                max_keys=1
            )

            health_status["components"]["s3"] = {
                "status": "healthy",
                "message": "Connection successful"
            }
    except Exception as e:
        health_status["components"]["s3"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503
    return JSONResponse(health_status, status_code=status_code)


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(request: Request) -> JSONResponse:
    """
    Prometheus-compatible metrics endpoint.

    Returns current operational metrics.
    """
    uptime = int(time.time() - start_time)

    metrics = {
        "service": "nba-mcp-server",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "metrics": {
            "queries_total": query_count,
            "errors_total": error_count,
            "success_rate": (query_count - error_count) / max(query_count, 1),
            "queries_per_minute": (query_count / max(uptime / 60, 1))
        },
        "timestamp": datetime.now().isoformat()
    }

    return JSONResponse(metrics)


@mcp.custom_route("/ready", methods=["GET"])
async def readiness_check(request: Request) -> JSONResponse:
    """
    Kubernetes readiness probe endpoint.

    Returns 200 if service is ready to accept traffic.
    """
    try:
        # Quick check - can we import required modules?
        from .fastmcp_lifespan import nba_lifespan
        from .fastmcp_settings import NBAMCPSettings

        return JSONResponse({
            "ready": True,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "ready": False,
            "error": str(e)
        }, status_code=503)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """
    Main entry point for FastMCP server.

    Supports multiple transport modes via environment variable or command line.
    Default: stdio (for Claude Desktop)
    """
    import os
    import sys

    # Determine transport mode
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    # Allow override via command line arg
    if len(sys.argv) > 1:
        transport = sys.argv[1]

    print("=" * 60)
    print("NBA MCP Server (FastMCP)")
    print("=" * 60)
    print(f"Transport:     {transport}")
    print(f"Debug mode:    {settings.debug}")
    print(f"Log level:     {settings.log_level}")

    if transport in ["streamable-http", "sse"]:
        print(f"Host:          {settings.host}")
        print(f"Port:          {settings.port}")

    print("=" * 60)
    print("")

    # Validate transport
    valid_transports = ["stdio", "sse", "streamable-http"]
    if transport not in valid_transports:
        print(f"ERROR: Invalid transport '{transport}'")
        print(f"Valid options: {', '.join(valid_transports)}")
        sys.exit(1)

    # Run with selected transport
    try:
        if transport == "stdio":
            print("✓ Running with STDIO transport (Claude Desktop)")
            mcp.run(transport="stdio")
        elif transport == "sse":
            print("✓ Running with SSE transport")
            print(f"  Connect at: http://{settings.host}:{settings.port}/sse")
            mcp.run(transport="sse")
        elif transport == "streamable-http":
            print("✓ Running with StreamableHTTP transport")
            print(f"  Endpoint: http://{settings.host}:{settings.port}{settings.streamable_http_path}")
            print(f"  Health check: http://{settings.host}:{settings.port}/health")
            print(f"  Metrics: http://{settings.host}:{settings.port}/metrics")
            mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()