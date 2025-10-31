"""
Pydantic Parameter Models for MCP Tools
Provides automatic validation for all tool parameters
Based on Graphiti MCP best practices
"""

from pydantic import ConfigDict, BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal, Tuple, Union
import re


# ============================================================================
# Database Tool Parameters
# ============================================================================


class QueryDatabaseParams(BaseModel):
    """Parameters for database query execution"""

    sql_query: str = Field(
        ..., min_length=1, max_length=10000, description="SQL SELECT query to execute"
    )
    max_rows: int = Field(
        default=1000, ge=1, le=10000, description="Maximum number of rows to return"
    )

    @field_validator("sql_query")
    @classmethod
    def validate_sql_query(cls, v):
        """Validate SQL query is safe"""
        # Only SELECT and WITH allowed
        query_upper = v.strip().upper()
        if not query_upper.startswith(("SELECT", "WITH")):
            raise ValueError("Only SELECT queries allowed. Use WITH...SELECT for CTEs.")

        # Check for forbidden keywords
        forbidden = [
            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
            "TRUNCATE",
            "ALTER",
            "CREATE",
            "GRANT",
            "REVOKE",
            "EXECUTE",
        ]
        for keyword in forbidden:
            if re.search(rf"\b{keyword}\b", query_upper):
                raise ValueError(
                    f"Forbidden SQL operation: {keyword}. Only SELECT queries are allowed."
                )

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sql_query": "SELECT * FROM games WHERE season = 2024 LIMIT 10",
                    "max_rows": 10,
                }
            ]
        }
    )


class GetTableSchemaParams(BaseModel):
    """Parameters for getting table schema"""

    table_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Table name (alphanumeric and underscore only)",
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v):
        """Additional validation for table name"""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Table name can only contain alphanumeric characters and underscores"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"table_name": "games"}, {"table_name": "player_stats"}]
        }
    )


class ListTablesParams(BaseModel):
    """Parameters for listing tables"""

    schema_name: Optional[str] = Field(
        default=None,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Optional schema name to filter tables (e.g., 'public')",
        alias="schema",
    )

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, v):
        """Validate schema name is safe"""
        if v and not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Schema name can only contain alphanumeric characters and underscores"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{}, {"schema": "public"}]},
        populate_by_name=True,
    )


# ============================================================================
# S3 Tool Parameters
# ============================================================================


class ListS3FilesParams(BaseModel):
    """Parameters for listing S3 files"""

    prefix: str = Field(
        default="", max_length=500, description="S3 prefix filter (e.g., '2024/games/')"
    )
    max_keys: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of files to return"
    )

    @field_validator("prefix")
    @classmethod
    def validate_prefix(cls, v):
        """Validate S3 prefix is safe"""
        # Prevent path traversal
        if ".." in v:
            raise ValueError("Path traversal not allowed in prefix")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"prefix": "2024/games/", "max_keys": 100},
                {"prefix": "players/", "max_keys": 50},
            ]
        }
    )


class GetS3FileParams(BaseModel):
    """Parameters for getting S3 file content"""

    file_key: str = Field(
        ..., min_length=1, max_length=1000, description="S3 object key"
    )

    @field_validator("file_key")
    @classmethod
    def validate_file_key(cls, v):
        """Validate S3 file key is safe"""
        if ".." in v:
            raise ValueError("Path traversal not allowed in file key")
        if v.startswith("/"):
            raise ValueError("File key should not start with /")
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"file_key": "2024/games/game_12345.json"}]}
    )


# ============================================================================
# Glue Tool Parameters
# ============================================================================


class GetGlueTableMetadataParams(BaseModel):
    """Parameters for getting Glue table metadata"""

    table_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Glue table name",
    )
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"table_name": "raw_games"}]}
    )


class ListGlueTablesParams(BaseModel):
    """Parameters for listing Glue tables (no parameters required)"""

    pass


# ============================================================================
# Pagination Parameters
# ============================================================================


class ListGamesParams(BaseModel):
    """Parameters for listing games with pagination"""

    season: Optional[int] = Field(
        default=None,
        ge=1946,  # First NBA season
        le=2100,
        description="Filter by season year (e.g., 2024)",
    )
    team_name: Optional[str] = Field(
        default=None, max_length=100, description="Filter by team name (home or away)"
    )
    cursor: Optional[str] = Field(
        default=None, description="Pagination cursor (base64 encoded game_id)"
    )
    limit: int = Field(default=50, ge=1, le=100, description="Number of games per page")

    @field_validator("team_name")
    @classmethod
    def validate_team_name(cls, v):
        """Validate team name is safe"""
        if v and not re.match(r"^[a-zA-Z0-9\s\-]+$", v):
            raise ValueError(
                "Team name can only contain alphanumeric, spaces, and hyphens"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"season": 2024, "limit": 50},
                {"team_name": "Lakers", "limit": 20},
                {"season": 2024, "cursor": "MTIzNDU=", "limit": 50},
            ]
        }
    )


class ListPlayersParams(BaseModel):
    """Parameters for listing players with pagination"""

    team_name: Optional[str] = Field(
        default=None, max_length=100, description="Filter by team name"
    )
    position: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Filter by position (e.g., 'PG', 'SG', 'SF')",
    )
    cursor: Optional[str] = Field(
        default=None, description="Pagination cursor (base64 encoded player_id)"
    )
    limit: int = Field(
        default=50, ge=1, le=100, description="Number of players per page"
    )

    @field_validator("team_name")
    @classmethod
    def validate_team_name(cls, v):
        """Validate team name is safe"""
        if v and not re.match(r"^[a-zA-Z0-9\s\-]+$", v):
            raise ValueError(
                "Team name can only contain alphanumeric, spaces, and hyphens"
            )
        return v

    @field_validator("position")
    @classmethod
    def validate_position(cls, v):
        """Validate position is valid"""
        valid_positions = ["PG", "SG", "SF", "PF", "C", "G", "F"]
        if v and v.upper() not in valid_positions:
            raise ValueError(f"Position must be one of: {', '.join(valid_positions)}")
        return v.upper() if v else v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"limit": 50},
                {"team_name": "Lakers", "limit": 20},
                {"position": "PG", "cursor": "MTIzNDU=", "limit": 50},
            ]
        }
    )


# ============================================================================
# Book Tool Parameters
# ============================================================================


class ListBooksParams(BaseModel):
    """Parameters for listing books"""

    prefix: str = Field(
        default="books/",
        max_length=200,
        description="S3 prefix to filter books (e.g., 'books/technical/', 'books/business/')",
    )
    max_keys: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of books to return"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"prefix": "books/"},
                {"prefix": "books/technical/", "max_keys": 50},
            ]
        }
    )


class ReadBookParams(BaseModel):
    """Parameters for reading a book with smart chunking"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path to the book (e.g., 'books/my-book.txt')",
    )
    chunk_size: int = Field(
        default=50000,
        ge=1000,
        le=200000,
        description="Characters per chunk (default: 50k, max: 200k for large context windows)",
    )
    chunk_number: int = Field(
        default=0, ge=0, description="Chunk number to retrieve (0-indexed)"
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe"""
        # Prevent path traversal
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid book path")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"book_path": "books/nba-analytics-guide.txt"},
                {
                    "book_path": "books/technical/python-best-practices.txt",
                    "chunk_size": 100000,
                    "chunk_number": 2,
                },
            ]
        }
    )


class SearchBooksParams(BaseModel):
    """Parameters for searching within books"""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    book_prefix: str = Field(
        default="books/",
        max_length=200,
        description="Limit search to books under this prefix",
    )
    max_results: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results to return"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"query": "machine learning", "max_results": 10},
                {"query": "database optimization", "book_prefix": "books/technical/"},
            ]
        }
    )


# ============================================================================
# EPUB Tool Parameters
# ============================================================================


class GetEpubMetadataParams(BaseModel):
    """Parameters for getting EPUB metadata"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to EPUB file",
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .epub"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".epub"):
            raise ValueError("File must be an EPUB (.epub)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"book_path": "books/python-guide.epub"},
                {"book_path": "books/technical/nba-analytics.epub"},
            ]
        }
    )


class GetEpubTocParams(BaseModel):
    """Parameters for getting EPUB table of contents"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to EPUB file",
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .epub"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".epub"):
            raise ValueError("File must be an EPUB (.epub)")
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"book_path": "books/python-guide.epub"}]}
    )


class ReadEpubChapterParams(BaseModel):
    """Parameters for reading EPUB chapter"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to EPUB file",
    )
    chapter_href: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Chapter href from TOC (e.g., 'chapter1.xhtml' or 'chapter1.xhtml#section1')",
    )
    format: Literal["html", "markdown", "text"] = Field(
        default="markdown", description="Output format for chapter content"
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .epub"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".epub"):
            raise ValueError("File must be an EPUB (.epub)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "book_path": "books/python-guide.epub",
                    "chapter_href": "chapter1.xhtml",
                    "format": "markdown",
                },
                {
                    "book_path": "books/python-guide.epub",
                    "chapter_href": "chapter1.xhtml#intro",
                    "format": "html",
                },
            ]
        }
    )


# ============================================================================
# PDF Tool Parameters
# ============================================================================


class GetPdfMetadataParams(BaseModel):
    """Parameters for getting PDF metadata"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file",
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"book_path": "books/statistics-textbook.pdf"},
                {"book_path": "books/technical/machine-learning.pdf"},
            ]
        }
    )


class GetPdfTocParams(BaseModel):
    """Parameters for getting PDF table of contents"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file",
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"book_path": "books/statistics-textbook.pdf"}]}
    )


class ReadPdfPageParams(BaseModel):
    """Parameters for reading a single PDF page"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file",
    )
    page_number: int = Field(..., ge=0, description="Page number (0-indexed)")
    format: Literal["text", "html", "markdown"] = Field(
        default="text", description="Output format for page content"
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "book_path": "books/statistics-textbook.pdf",
                    "page_number": 0,
                    "format": "text",
                },
                {
                    "book_path": "books/statistics-textbook.pdf",
                    "page_number": 5,
                    "format": "markdown",
                },
            ]
        }
    )


class ReadPdfPageRangeParams(BaseModel):
    """Parameters for reading a range of PDF pages"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file",
    )
    start_page: int = Field(
        ..., ge=0, description="Starting page number (0-indexed, inclusive)"
    )
    end_page: int = Field(
        ..., ge=0, description="Ending page number (0-indexed, inclusive)"
    )
    format: Literal["text", "html", "markdown"] = Field(
        default="text", description="Output format for page content"
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    @model_validator(mode="after")
    def validate_page_range(self):
        """Validate that start_page <= end_page"""
        if (
            self.start_page is not None
            and self.end_page is not None
            and self.start_page > self.end_page
        ):
            raise ValueError("start_page must be <= end_page")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "book_path": "books/statistics-textbook.pdf",
                    "start_page": 0,
                    "end_page": 10,
                    "format": "text",
                },
                {
                    "book_path": "books/statistics-textbook.pdf",
                    "start_page": 15,
                    "end_page": 20,
                    "format": "markdown",
                },
            ]
        }
    )


class ReadPdfChapterParams(BaseModel):
    """Parameters for reading a PDF chapter by title"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file",
    )
    chapter_title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Chapter title (partial match supported)",
    )
    format: Literal["text", "html", "markdown"] = Field(
        default="text", description="Output format for chapter content"
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "book_path": "books/statistics-textbook.pdf",
                    "chapter_title": "Introduction",
                    "format": "markdown",
                },
                {
                    "book_path": "books/statistics-textbook.pdf",
                    "chapter_title": "Chapter 3",
                    "format": "text",
                },
            ]
        }
    )


class SearchPdfParams(BaseModel):
    """Parameters for searching text in PDF"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file",
    )
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    context_chars: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Number of characters to include before/after match",
    )

    @field_validator("book_path")
    @classmethod
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if ".." in v or (v.startswith("/") and not v.startswith("/tmp")):
            raise ValueError("Invalid book path")
        if not v.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "book_path": "books/statistics-textbook.pdf",
                    "query": "regression analysis",
                    "context_chars": 100,
                },
                {
                    "book_path": "books/statistics-textbook.pdf",
                    "query": "hypothesis testing",
                    "context_chars": 150,
                },
            ]
        }
    )


# ============================================================================
# File Tool Parameters
# ============================================================================


class ReadProjectFileParams(BaseModel):
    """Parameters for reading project files"""

    file_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Relative path to file within project",
    )

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v):
        """Validate file path is safe"""
        # Prevent path traversal
        if ".." in v:
            raise ValueError("Path traversal not allowed")
        if v.startswith("/"):
            raise ValueError("Use relative paths only")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"file_path": "synthesis/models/ollama_model.py"}]
        }
    )


class SearchProjectFilesParams(BaseModel):
    """Parameters for searching project files"""

    pattern: str = Field(
        ..., min_length=1, max_length=200, description="Search pattern (regex or glob)"
    )
    file_pattern: Optional[str] = Field(
        default="*.py", description="File pattern to search (e.g., '*.py', '*.md')"
    )
    max_results: int = Field(
        default=50, ge=1, le=500, description="Maximum number of results"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "pattern": "def.*synthesize",
                    "file_pattern": "*.py",
                    "max_results": 20,
                }
            ]
        }
    )


# ============================================================================
# Action Tool Parameters
# ============================================================================


class SaveToProjectParams(BaseModel):
    """Parameters for saving synthesis results"""

    filename: str = Field(
        ..., min_length=1, max_length=200, description="Filename for saved output"
    )
    content: str = Field(..., min_length=1, description="Content to save")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        """Validate filename is safe"""
        if ".." in v or "/" in v:
            raise ValueError("Filename must not contain path separators or traversal")
        # Only allow safe characters
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", v):
            raise ValueError(
                "Filename can only contain alphanumeric, underscore, dash, and dot"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "filename": "lakers_analysis_2024.md",
                    "content": "# Lakers Analysis\n\n...",
                }
            ]
        }
    )


class LogSynthesisResultParams(BaseModel):
    """Parameters for logging synthesis results"""

    query: str = Field(..., min_length=1, description="Original query")
    result: Dict[str, Any] = Field(..., description="Synthesis result")
    model_used: str = Field(..., description="Model used for synthesis")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "Analyze Lakers performance",
                    "result": {"summary": "..."},
                    "model_used": "deepseek",
                }
            ]
        }
    )


class SendNotificationParams(BaseModel):
    """Parameters for sending Slack notifications"""

    message: str = Field(
        ..., min_length=1, max_length=3000, description="Notification message"
    )
    level: Literal["info", "warning", "error", "success"] = Field(
        default="info", description="Notification level"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"message": "Synthesis completed successfully", "level": "success"}
            ]
        }
    )


# ============================================================================
# Math & Statistics Tool Parameters
# ============================================================================

from typing import Union


class MathTwoNumberParams(BaseModel):
    """Parameters for operations on two numbers"""

    a: Union[int, float] = Field(..., description="First number")
    b: Union[int, float] = Field(..., description="Second number")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"a": 5, "b": 3}, {"a": 10.5, "b": 2.3}]}
    )


class MathDivideParams(BaseModel):
    """Parameters for division"""

    numerator: Union[int, float] = Field(..., description="Number being divided")
    denominator: Union[int, float] = Field(..., description="Number to divide by")

    @field_validator("denominator")
    @classmethod
    def validate_denominator(cls, v):
        if v == 0:
            raise ValueError("Denominator cannot be zero")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"numerator": 10, "denominator": 2},
                {"numerator": 7.5, "denominator": 2.5},
            ]
        }
    )


class MathNumberListParams(BaseModel):
    """Parameters for operations on a list of numbers"""

    numbers: List[Union[int, float]] = Field(
        ..., min_length=1, description="List of numbers"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"numbers": [1, 2, 3, 4, 5]}, {"numbers": [10.5, 20.3, 15.2]}]
        }
    )


class MathRoundParams(BaseModel):
    """Parameters for rounding"""

    number: Union[int, float] = Field(..., description="Number to round")
    decimals: int = Field(default=0, ge=0, le=10, description="Decimal places")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"number": 3.14159, "decimals": 2},
                {"number": 10.7, "decimals": 0},
            ]
        }
    )


class MathSingleNumberParams(BaseModel):
    """Parameters for operations on a single number"""

    number: Union[int, float] = Field(..., description="The number")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"number": 3.7}, {"number": -2.3}]}
    )


class MathAngleParams(BaseModel):
    """Parameters for angle conversion"""

    angle: float = Field(..., description="Angle value")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"angle": 180}, {"angle": 3.14159}]}
    )


class StatsPercentileParams(BaseModel):
    """Parameters for percentile calculation"""

    numbers: List[Union[int, float]] = Field(
        ..., min_length=1, description="List of numbers"
    )
    percentile: float = Field(
        ..., ge=0, le=100, description="Percentile to calculate (0-100)"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"numbers": [1, 2, 3, 4, 5], "percentile": 50},
                {"numbers": [10, 20, 30, 40], "percentile": 75},
            ]
        }
    )


class StatsVarianceParams(BaseModel):
    """Parameters for variance/std dev calculation"""

    numbers: List[Union[int, float]] = Field(
        ..., min_length=2, description="List of numbers"
    )
    sample: bool = Field(
        default=True,
        description="Calculate sample variance (True) or population variance (False)",
    )
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"numbers": [2, 4, 6, 8, 10], "sample": True}]}
    )


# ============================================================================
# NBA Metrics Parameters
# ============================================================================


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

    @field_validator("fga")
    @classmethod
    def validate_fga(cls, v, info):
        if "fgm" in info.data and v < info.data["fgm"]:
            raise ValueError("Field goals attempted must be >= field goals made")
        return v

    @field_validator("fta")
    @classmethod
    def validate_fta(cls, v, info):
        if "ftm" in info.data and v < info.data["ftm"]:
            raise ValueError("Free throws attempted must be >= free throws made")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "points": 250,
                    "rebounds": 100,
                    "assists": 80,
                    "steals": 20,
                    "blocks": 15,
                    "fgm": 95,
                    "fga": 200,
                    "ftm": 60,
                    "fta": 75,
                    "turnovers": 40,
                    "minutes": 500,
                }
            ]
        }
    )


class NbaTrueShootingParams(BaseModel):
    """Parameters for True Shooting Percentage"""

    points: Union[int, float] = Field(..., ge=0, description="Points scored")
    fga: Union[int, float] = Field(..., ge=0, description="Field goals attempted")
    fta: Union[int, float] = Field(..., ge=0, description="Free throws attempted")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"points": 250, "fga": 200, "fta": 75}]}
    )


class NbaEffectiveFgParams(BaseModel):
    """Parameters for Effective Field Goal Percentage"""

    fgm: Union[int, float] = Field(..., ge=0, description="Field goals made")
    fga: Union[int, float] = Field(..., ge=0, description="Field goals attempted")
    three_pm: Union[int, float] = Field(..., ge=0, description="Three-pointers made")

    @field_validator("fga")
    @classmethod
    def validate_fga(cls, v, info):
        if "fgm" in info.data and v < info.data["fgm"]:
            raise ValueError("FGA must be >= FGM")
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"fgm": 95, "fga": 200, "three_pm": 30}]}
    )


class NbaUsageRateParams(BaseModel):
    """Parameters for Usage Rate calculation"""

    fga: Union[int, float] = Field(..., ge=0, description="Player FGA")
    fta: Union[int, float] = Field(..., ge=0, description="Player FTA")
    turnovers: Union[int, float] = Field(..., ge=0, description="Player turnovers")
    minutes: float = Field(..., gt=0, description="Player minutes")
    team_minutes: float = Field(..., gt=0, description="Team total minutes")
    team_fga: Union[int, float] = Field(..., ge=0, description="Team FGA")
    team_fta: Union[int, float] = Field(..., ge=0, description="Team FTA")
    team_turnovers: Union[int, float] = Field(..., ge=0, description="Team turnovers")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "fga": 200,
                    "fta": 75,
                    "turnovers": 40,
                    "minutes": 500,
                    "team_minutes": 4800,
                    "team_fga": 1800,
                    "team_fta": 600,
                    "team_turnovers": 350,
                }
            ]
        }
    )


class NbaRatingParams(BaseModel):
    """Parameters for Offensive/Defensive Rating"""

    points: Union[int, float] = Field(
        ..., ge=0, description="Points (scored or allowed)"
    )
    possessions: Union[int, float] = Field(..., gt=0, description="Total possessions")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"points": 2500, "possessions": 2200}]}
    )


# ============================================================================
# Sprint 6: Advanced Analytics Parameters
# ============================================================================

# Correlation & Regression Parameters


class CorrelationParams(BaseModel):
    """Parameters for correlation calculation"""

    x: List[Union[int, float]] = Field(
        ..., min_length=2, description="First variable (list of numbers)"
    )
    y: List[Union[int, float]] = Field(
        ..., min_length=2, description="Second variable (list of numbers)"
    )

    @field_validator("y")
    @classmethod
    def validate_same_length(cls, v, info):
        if "x" in info.data and len(v) != len(info.data["x"]):
            raise ValueError(
                f"Lists must have same length: x={len(info.data['x'])}, y={len(v)}"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]}]}
    )


class CovarianceParams(BaseModel):
    """Parameters for covariance calculation"""

    x: List[Union[int, float]] = Field(..., min_length=1, description="First variable")
    y: List[Union[int, float]] = Field(..., min_length=1, description="Second variable")
    sample: bool = Field(
        default=True,
        description="Use sample covariance (n-1) if True, population (n) if False",
    )

    @field_validator("y")
    @classmethod
    def validate_same_length(cls, v, info):
        if "x" in info.data and len(v) != len(info.data["x"]):
            raise ValueError(f"Lists must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"x": [1, 2, 3, 4, 5], "y": [2, 4, 5, 4, 5], "sample": True}]
        }
    )


class LinearRegressionParams(BaseModel):
    """Parameters for linear regression"""

    x: List[Union[int, float]] = Field(
        ..., min_length=2, description="Independent variable"
    )
    y: List[Union[int, float]] = Field(
        ..., min_length=2, description="Dependent variable"
    )

    @field_validator("y")
    @classmethod
    def validate_same_length(cls, v, info):
        if "x" in info.data and len(v) != len(info.data["x"]):
            raise ValueError("Lists must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]}]}
    )


class PredictParams(BaseModel):
    """Parameters for making predictions with linear model"""

    slope: float = Field(..., description="Model slope (from regression)")
    intercept: float = Field(..., description="Model intercept (from regression)")
    x_values: List[Union[int, float]] = Field(
        ..., min_length=1, description="New x values to predict"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"slope": 2.0, "intercept": 1.0, "x_values": [6, 7, 8]}]
        }
    )


class CorrelationMatrixParams(BaseModel):
    """Parameters for correlation matrix calculation"""

    data: Dict[str, List[Union[int, float]]] = Field(
        ..., description="Dictionary mapping variable names to lists of values"
    )

    @field_validator("data")
    @classmethod
    def validate_data(cls, v):
        if not v:
            raise ValueError("Data dictionary cannot be empty")

        # Check all lists have same length
        lengths = [len(values) for values in v.values()]
        if len(set(lengths)) > 1:
            raise ValueError("All variables must have same number of observations")

        # Check minimum 2 data points
        if lengths and lengths[0] < 2:
            raise ValueError("Need at least 2 data points")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": {
                        "points": [20, 25, 22, 28],
                        "assists": [5, 7, 6, 8],
                        "rebounds": [8, 6, 7, 5],
                    }
                }
            ]
        }
    )


# Time Series Parameters


class MovingAverageParams(BaseModel):
    """Parameters for moving average calculation"""

    data: List[Union[int, float]] = Field(
        ..., min_length=1, description="Time series data"
    )
    window: int = Field(default=3, ge=1, description="Window size for moving average")

    @field_validator("window")
    @classmethod
    def validate_window(cls, v, info):
        if "data" in info.data and v > len(info.data["data"]):
            raise ValueError(
                f"Window ({v}) cannot be larger than data length ({len(info.data['data'])})"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"data": [10, 12, 14, 16, 18, 20], "window": 3}]
        }
    )


class ExponentialMovingAverageParams(BaseModel):
    """Parameters for exponential moving average"""

    data: List[Union[int, float]] = Field(
        ..., min_length=1, description="Time series data"
    )
    alpha: float = Field(
        default=0.3,
        gt=0,
        le=1,
        description="Smoothing factor (0-1, higher = more weight to recent values)",
    )
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"data": [10, 12, 14, 16, 18], "alpha": 0.3}]}
    )


class TrendDetectionParams(BaseModel):
    """Parameters for trend detection"""

    data: List[Union[int, float]] = Field(
        ..., min_length=1, description="Time series data"
    )
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"data": [10, 12, 15, 17, 20]}]}
    )


class PercentChangeParams(BaseModel):
    """Parameters for percentage change calculation"""

    current: Union[int, float] = Field(..., description="Current value")
    previous: Union[int, float] = Field(..., description="Previous value")

    @field_validator("previous")
    @classmethod
    def validate_previous(cls, v):
        if v == 0:
            raise ValueError("Previous value cannot be zero (would divide by zero)")
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"current": 120, "previous": 100}]}
    )


class GrowthRateParams(BaseModel):
    """Parameters for compound growth rate calculation"""

    start_value: Union[int, float] = Field(
        ..., gt=0, description="Initial value (must be positive)"
    )
    end_value: Union[int, float] = Field(
        ..., gt=0, description="Final value (must be positive)"
    )
    periods: int = Field(..., gt=0, description="Number of time periods")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"start_value": 100, "end_value": 150, "periods": 3}]
        }
    )


class VolatilityParams(BaseModel):
    """Parameters for volatility calculation"""

    data: List[Union[int, float]] = Field(
        ..., min_length=2, description="Time series data"
    )
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"data": [100, 102, 98, 101, 99]}]}
    )


# Advanced NBA Metrics Parameters


class FourFactorsParams(BaseModel):
    """Parameters for Four Factors calculation"""

    # Offensive stats
    fgm: Union[int, float] = Field(..., ge=0, description="Field goals made")
    fga: Union[int, float] = Field(..., ge=0, description="Field goals attempted")
    three_pm: Union[int, float] = Field(..., ge=0, description="Three-pointers made")
    tov: Union[int, float] = Field(..., ge=0, description="Turnovers")
    fta: Union[int, float] = Field(..., ge=0, description="Free throw attempts")
    orb: Union[int, float] = Field(..., ge=0, description="Offensive rebounds")
    team_orb: Union[int, float] = Field(
        ..., ge=0, description="Total team offensive rebounds"
    )
    opp_drb: Union[int, float] = Field(
        ..., ge=0, description="Opponent defensive rebounds"
    )

    # Defensive stats
    opp_fgm: Union[int, float] = Field(
        ..., ge=0, description="Opponent field goals made"
    )
    opp_fga: Union[int, float] = Field(
        ..., ge=0, description="Opponent field goals attempted"
    )
    opp_three_pm: Union[int, float] = Field(
        ..., ge=0, description="Opponent three-pointers made"
    )
    opp_tov: Union[int, float] = Field(..., ge=0, description="Opponent turnovers")
    opp_fta: Union[int, float] = Field(
        ..., ge=0, description="Opponent free throw attempts"
    )
    drb: Union[int, float] = Field(..., ge=0, description="Defensive rebounds")
    team_drb: Union[int, float] = Field(
        ..., ge=0, description="Total team defensive rebounds"
    )
    opp_orb: Union[int, float] = Field(
        ..., ge=0, description="Opponent offensive rebounds"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "fgm": 3200,
                    "fga": 7000,
                    "three_pm": 1000,
                    "tov": 1100,
                    "fta": 1800,
                    "orb": 900,
                    "team_orb": 900,
                    "opp_drb": 2800,
                    "opp_fgm": 2900,
                    "opp_fga": 6800,
                    "opp_three_pm": 800,
                    "opp_tov": 1200,
                    "opp_fta": 1600,
                    "drb": 2800,
                    "team_drb": 2800,
                    "opp_orb": 850,
                }
            ]
        }
    )


class TurnoverPercentageParams(BaseModel):
    """Parameters for turnover percentage"""

    tov: Union[int, float] = Field(..., ge=0, description="Turnovers")
    fga: Union[int, float] = Field(..., ge=0, description="Field goals attempted")
    fta: Union[int, float] = Field(..., ge=0, description="Free throws attempted")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"tov": 250, "fga": 1800, "fta": 600}]}
    )


class ReboundPercentageParams(BaseModel):
    """Parameters for rebound percentage"""

    rebounds: Union[int, float] = Field(..., ge=0, description="Player/team rebounds")
    team_rebounds: Union[int, float] = Field(
        ..., ge=0, description="Total team rebounds"
    )
    opp_rebounds: Union[int, float] = Field(..., ge=0, description="Opponent rebounds")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"rebounds": 900, "team_rebounds": 900, "opp_rebounds": 2800}]
        }
    )


class AssistPercentageParams(BaseModel):
    """Parameters for assist percentage"""

    assists: Union[int, float] = Field(..., ge=0, description="Player assists")
    minutes: float = Field(..., gt=0, description="Player minutes played")
    team_minutes: float = Field(..., gt=0, description="Team total minutes")
    team_fgm: Union[int, float] = Field(..., ge=0, description="Team field goals made")
    player_fgm: Union[int, float] = Field(
        default=0, ge=0, description="Player's own field goals made"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "assists": 500,
                    "minutes": 2000,
                    "team_minutes": 19680,
                    "team_fgm": 3200,
                    "player_fgm": 600,
                }
            ]
        }
    )


class StealPercentageParams(BaseModel):
    """Parameters for steal percentage"""

    steals: Union[int, float] = Field(..., ge=0, description="Player steals")
    minutes: float = Field(..., gt=0, description="Player minutes played")
    team_minutes: float = Field(..., gt=0, description="Team total minutes")
    opp_possessions: Union[int, float] = Field(
        ..., gt=0, description="Opponent possessions"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "steals": 120,
                    "minutes": 2000,
                    "team_minutes": 19680,
                    "opp_possessions": 8000,
                }
            ]
        }
    )


class BlockPercentageParams(BaseModel):
    """Parameters for block percentage"""

    blocks: Union[int, float] = Field(..., ge=0, description="Player blocks")
    minutes: float = Field(..., gt=0, description="Player minutes played")
    team_minutes: float = Field(..., gt=0, description="Team total minutes")
    opp_two_pa: Union[int, float] = Field(
        ..., gt=0, description="Opponent 2-point attempts"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "blocks": 100,
                    "minutes": 2000,
                    "team_minutes": 19680,
                    "opp_two_pa": 5000,
                }
            ]
        }
    )


class WinSharesParams(BaseModel):
    """Parameters for Win Shares calculation"""

    marginal_offense: float = Field(
        ..., description="Offensive contribution above average"
    )
    marginal_defense: float = Field(
        ..., description="Defensive contribution above average"
    )
    marginal_points_per_win: float = Field(
        default=30.0, gt=0, description="Points needed for a win (default: 30)"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "marginal_offense": 120,
                    "marginal_defense": 80,
                    "marginal_points_per_win": 30,
                }
            ]
        }
    )


class BoxPlusMinusParams(BaseModel):
    """Parameters for Box Plus/Minus calculation"""

    per: float = Field(..., description="Player Efficiency Rating")
    team_pace: float = Field(..., gt=0, description="Team's pace")
    league_avg_per: float = Field(
        default=15.0, gt=0, description="League average PER (default: 15.0)"
    )
    league_avg_pace: float = Field(
        default=100.0, gt=0, description="League average pace (default: 100.0)"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "per": 20,
                    "team_pace": 98,
                    "league_avg_per": 15,
                    "league_avg_pace": 100,
                }
            ]
        }
    )


# ============================================================================
# Sprint 9: Algebraic Equation Tool Parameters
# ============================================================================


class AlgebraSolveParams(BaseModel):
    """Parameters for solving algebraic equations"""

    equation: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Algebraic equation to solve (e.g., 'x**2 + 2*x - 3 = 0')",
    )
    variable: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Variable to solve for (auto-detected if not specified)",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"equation": "x**2 + 2*x - 3 = 0"},
                {"equation": "2*y + 5 = 13", "variable": "y"},
                {"equation": "x**3 - 8 = 0"},
            ]
        }
    )


class AlgebraSimplifyParams(BaseModel):
    """Parameters for simplifying algebraic expressions"""

    expression: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Algebraic expression to simplify",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"expression": "x**2 + 2*x + 1"},
                {"expression": "(x + 1)**2 - 1"},
                {"expression": "x**3 + 3*x**2 + 3*x + 1"},
            ]
        }
    )


class AlgebraDifferentiateParams(BaseModel):
    """Parameters for differentiating expressions"""

    expression: str = Field(
        ..., min_length=1, max_length=500, description="Expression to differentiate"
    )
    variable: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Variable to differentiate with respect to",
    )
    order: int = Field(
        default=1, ge=1, le=10, description="Order of differentiation (1st, 2nd, etc.)"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"expression": "x**3 + 2*x**2 + x", "variable": "x"},
                {"expression": "sin(x)", "variable": "x", "order": 2},
                {"expression": "x**2 + y**2", "variable": "x"},
            ]
        }
    )


class AlgebraIntegrateParams(BaseModel):
    """Parameters for integrating expressions"""

    expression: str = Field(
        ..., min_length=1, max_length=500, description="Expression to integrate"
    )
    variable: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Variable to integrate with respect to",
    )
    lower_limit: Optional[Union[int, float]] = Field(
        default=None, description="Lower limit for definite integral"
    )
    upper_limit: Optional[Union[int, float]] = Field(
        default=None, description="Upper limit for definite integral"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"expression": "x**2", "variable": "x"},
                {
                    "expression": "x**2",
                    "variable": "x",
                    "lower_limit": 0,
                    "upper_limit": 2,
                },
                {"expression": "sin(x)", "variable": "x"},
            ]
        }
    )


class AlgebraSportsFormulaParams(BaseModel):
    """Parameters for sports analytics formulas"""

    formula_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Name of the sports formula to use",
    )
    variables: Dict[str, Union[int, float]] = Field(
        default={}, description="Variable values for formula substitution"
    )

    @field_validator("formula_name")
    def validate_formula_name(cls, v):
        """Validate formula name"""
        valid_formulas = [
            # Original formulas
            "per",
            "true_shooting",
            "usage_rate",
            "four_factors_shooting",
            "four_factors_turnovers",
            "pace",
            # Advanced Player Metrics
            "vorp",
            "ws_per_48",
            "game_score",
            "pie",
            # Shooting Analytics
            "corner_3pt_pct",
            "rim_fg_pct",
            "midrange_efficiency",
            "catch_and_shoot_pct",
            # Defensive Metrics
            "defensive_win_shares",
            "steal_percentage",
            "block_percentage",
            "defensive_rating",
            # Team Metrics
            "net_rating",
            "offensive_efficiency",
            "defensive_efficiency",
            "pace_factor",
            # Situational Metrics
            "clutch_performance",
            "on_off_differential",
            "plus_minus_per_100",
        ]
        if v not in valid_formulas:
            raise ValueError(f"Invalid formula name. Available: {valid_formulas}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula_name": "per",
                    "variables": {
                        "FGM": 8,
                        "STL": 2,
                        "3PM": 3,
                        "FTM": 4,
                        "BLK": 1,
                        "OREB": 2,
                        "AST": 5,
                        "DREB": 6,
                        "PF": 3,
                        "FTA": 5,
                        "FGA": 15,
                        "TOV": 2,
                        "MP": 35,
                    },
                },
                {
                    "formula_name": "true_shooting",
                    "variables": {"PTS": 25, "FGA": 15, "FTA": 5},
                },
                {
                    "formula_name": "usage_rate",
                    "variables": {
                        "FGA": 15,
                        "FTA": 5,
                        "TOV": 2,
                        "TM_MP": 240,
                        "MP": 35,
                        "TM_FGA": 80,
                        "TM_FTA": 20,
                        "TM_TOV": 12,
                    },
                },
                {
                    "formula_name": "vorp",
                    "variables": {"BPM": 8.5, "POSS_PCT": 85, "TEAM_GAMES": 82},
                },
                {
                    "formula_name": "game_score",
                    "variables": {
                        "PTS": 30,
                        "FGM": 12,
                        "FGA": 20,
                        "FTA": 8,
                        "FTM": 6,
                        "OREB": 2,
                        "DREB": 8,
                        "STL": 2,
                        "AST": 7,
                        "BLK": 1,
                        "PF": 3,
                        "TOV": 4,
                    },
                },
                {
                    "formula_name": "net_rating",
                    "variables": {"ORtg": 115.5, "DRtg": 108.2},
                },
            ]
        }
    )


class AlgebraLatexParams(BaseModel):
    """Parameters for LaTeX rendering"""

    expression: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Mathematical expression to convert to LaTeX",
    )
    display_mode: bool = Field(
        default=False, description="Use display math mode ($$) instead of inline ($)"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"expression": "x**2 + 2*x + 1"},
                {"expression": "x**2 + 2*x + 1", "display_mode": True},
                {"expression": "sin(x) + cos(x)"},
            ]
        }
    )


class AlgebraMatrixParams(BaseModel):
    """Parameters for matrix operations"""

    matrix_data: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="2D list representing the matrix"
    )
    operation: str = Field(
        ..., min_length=1, max_length=20, description="Matrix operation to perform"
    )
    matrix2: Optional[List[List[Union[int, float]]]] = Field(
        default=None, description="Second matrix for multiplication operations"
    )

    @field_validator("operation")
    def validate_operation(cls, v):
        """Validate matrix operation"""
        valid_operations = [
            "determinant",
            "inverse",
            "eigenvalues",
            "multiply",
            "transpose",
        ]
        if v not in valid_operations:
            raise ValueError(f"Invalid operation. Available: {valid_operations}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"matrix_data": [[1, 2], [3, 4]], "operation": "determinant"},
                {
                    "matrix_data": [[1, 2], [3, 4]],
                    "operation": "multiply",
                    "matrix2": [[5, 6], [7, 8]],
                },
                {"matrix_data": [[2, 0], [0, 3]], "operation": "eigenvalues"},
            ]
        }
    )


class AlgebraSystemSolveParams(BaseModel):
    """Parameters for solving equation systems"""

    equations: List[str] = Field(
        ..., min_length=1, max_length=10, description="List of equation strings"
    )
    variables: List[str] = Field(
        ..., min_length=1, max_length=10, description="List of variable names"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"equations": ["x + y = 5", "x - y = 1"], "variables": ["x", "y"]},
                {"equations": ["2*x + 3*y = 13", "x - y = 1"], "variables": ["x", "y"]},
                {
                    "equations": ["x**2 + y**2 = 25", "x + y = 7"],
                    "variables": ["x", "y"],
                },
            ]
        }
    )


# ============================================================================
# Phase 2: Formula Intelligence Parameters
# ============================================================================


class FormulaAnalysisParams(BaseModel):
    """Parameters for formula analysis operations"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="Formula string to analyze"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula": "PER = (FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)"
                },
                {"formula": "TS% = PTS / (2 * (FGA + 0.44 * FTA))"},
                {
                    "formula": "USG% = ((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100"
                },
            ]
        }
    )


class FormulaValidationParams(BaseModel):
    """Parameters for formula validation operations"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="Formula string to validate"
    )
    variables: Dict[str, Union[int, float]] = Field(
        default={}, description="Variable values for validation"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula": "PER = (FGM * 85.910 + ...) / MP",
                    "variables": {"FGM": 8, "STL": 2, "MP": 35},
                },
                {
                    "formula": "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
                    "variables": {"PTS": 25, "FGA": 15, "FTA": 5},
                },
            ]
        }
    )


class FormulaUsageRecommendationParams(BaseModel):
    """Parameters for formula usage recommendation operations"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="Formula string to analyze"
    )
    context: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional context for recommendations (e.g., 'player analysis', 'team comparison')",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula": "PER = (FGM * 85.910 + ...) / MP",
                    "context": "player analysis",
                },
                {"formula": "Net Rating = ORtg - DRtg", "context": "team comparison"},
                {
                    "formula": "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
                    "context": "optimization",
                },
            ]
        }
    )


# ============================================================================
# Phase 2.2: Formula Extraction Parameters
# ============================================================================


class FormulaExtractionParams(BaseModel):
    """Parameters for formula extraction from PDFs"""

    pdf_path: str = Field(
        ..., min_length=1, max_length=500, description="Path to PDF file (S3 or local)"
    )
    pages: Optional[List[int]] = Field(
        default=None,
        description="Specific pages to extract from (if None, extracts from all pages)",
    )
    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for extracted formulas",
    )
    max_formulas: int = Field(
        default=50, ge=1, le=200, description="Maximum number of formulas to extract"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "pdf_path": "books/Basketball_on_Paper_Dean_Oliver.pdf",
                    "min_confidence": 0.7,
                },
                {
                    "pdf_path": "books/Sports_Analytics_A_Guide_for_Coaches_Managers_and_Other_Decision_Makers.pdf",
                    "pages": [50, 51, 52],
                },
                {
                    "pdf_path": "books/Basketball_Beyond_Paper_Quants_Stats_and_the_New_Frontier_of_the_NBA.pdf",
                    "max_formulas": 20,
                },
            ]
        }
    )


class LaTeXConversionParams(BaseModel):
    """Parameters for LaTeX to SymPy conversion"""

    latex_formula: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="LaTeX formula string to convert",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"latex_formula": "\\frac{PTS}{2 \\cdot (FGA + 0.44 \\cdot FTA)}"},
                {
                    "latex_formula": "PER = \\frac{FGM \\cdot 85.910 + STL \\cdot 53.897}{MP}"
                },
                {"latex_formula": "\\sum_{i=1}^{n} x_i"},
            ]
        }
    )


class FormulaStructureAnalysisParams(BaseModel):
    """Parameters for formula structure analysis"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="Formula string to analyze"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"formula": "PER = (FGM * 85.910 + STL * 53.897) / MP"},
                {"formula": "TS% = PTS / (2 * (FGA + 0.44 * FTA))"},
                {"formula": "Net Rating = ORtg - DRtg"},
            ]
        }
    )


# ============================================================================
# Phase 2.3: Interactive Formula Builder Parameters
# ============================================================================


class FormulaBuilderValidationParams(BaseModel):
    """Parameters for formula builder validation"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="Formula string to validate"
    )
    validation_level: str = Field(
        default="semantic",
        description="Validation level: syntax, semantic, sports_context, units",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula": "PER = (FGM * 85.910 + STL * 53.897) / MP",
                    "validation_level": "semantic",
                },
                {
                    "formula": "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
                    "validation_level": "sports_context",
                },
                {"formula": "x + y = z", "validation_level": "syntax"},
            ]
        }
    )


class FormulaBuilderSuggestionParams(BaseModel):
    """Parameters for formula completion suggestions"""

    partial_formula: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Partial formula string for completion suggestions",
    )
    context: Optional[str] = Field(
        default="",
        max_length=200,
        description="Optional context for suggestions (e.g., 'shooting', 'defensive')",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"partial_formula": "PTS / (2 * (FGA +", "context": "shooting"},
                {"partial_formula": "PER = (FGM *", "context": "advanced"},
                {"partial_formula": "ORtg -", "context": "team"},
            ]
        }
    )


class FormulaBuilderPreviewParams(BaseModel):
    """Parameters for formula preview generation"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="Formula string to preview"
    )
    variable_values: Optional[Dict[str, float]] = Field(
        default={}, description="Optional variable values for calculation preview"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula": "PTS / (2 * (FGA + 0.44 * FTA))",
                    "variable_values": {"PTS": 25, "FGA": 15, "FTA": 5},
                },
                {
                    "formula": "PER = (FGM * 85.910 + STL * 53.897) / MP",
                    "variable_values": {"FGM": 8, "STL": 2, "MP": 38},
                },
                {
                    "formula": "ORtg - DRtg",
                    "variable_values": {"ORtg": 115, "DRtg": 108},
                },
            ]
        }
    )


class FormulaBuilderTemplateParams(BaseModel):
    """Parameters for formula template operations"""

    template_name: Optional[str] = Field(
        default=None, description="Specific template name to retrieve"
    )
    category: Optional[str] = Field(
        default=None,
        description="Template category filter (shooting, defensive, team, advanced)",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"template_name": "True Shooting Percentage"},
                {"category": "shooting"},
                {"category": "advanced"},
            ]
        }
    )


class FormulaBuilderCreateParams(BaseModel):
    """Parameters for creating formula from template"""

    template_name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the template to use"
    )
    variable_values: Dict[str, float] = Field(
        ..., description="Values for template variables"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "template_name": "True Shooting Percentage",
                    "variable_values": {"PTS": 25, "FGA": 15, "FTA": 5},
                },
                {
                    "template_name": "Net Rating",
                    "variable_values": {"ORtg": 115, "DRtg": 108},
                },
                {
                    "template_name": "Player Efficiency Rating",
                    "variable_values": {
                        "FGM": 8,
                        "STL": 2,
                        "3PM": 2,
                        "FTM": 5,
                        "BLK": 1,
                        "OREB": 1,
                        "AST": 8,
                        "DREB": 7,
                        "PF": 2,
                        "FTA": 6,
                        "FGA": 18,
                        "TOV": 3,
                        "MP": 38,
                    },
                },
            ]
        }
    )


class FormulaBuilderExportParams(BaseModel):
    """Parameters for formula export"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="Formula string to export"
    )
    format_type: str = Field(
        default="latex", description="Export format: latex, python, sympy, json"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"formula": "PTS / (2 * (FGA + 0.44 * FTA))", "format_type": "latex"},
                {
                    "formula": "PER = (FGM * 85.910 + STL * 53.897) / MP",
                    "format_type": "python",
                },
                {"formula": "ORtg - DRtg", "format_type": "json"},
            ]
        }
    )


# ============================================================================
# Phase 3.1: Interactive Formula Playground Parameters
# ============================================================================


class PlaygroundCreateSessionParams(BaseModel):
    """Parameters for creating a playground session"""

    user_id: str = Field(..., description="User ID for the session")
    mode: str = Field(
        default="explore",
        description="Playground mode (explore, learn, build, compare, collaborate)",
    )
    template_name: Optional[str] = Field(
        default=None, description="Template name to use for the session"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "user123",
                    "mode": "explore",
                    "template_name": "Shooting Efficiency Lab",
                },
                {
                    "user_id": "user456",
                    "mode": "learn",
                    "template_name": "Advanced Metrics Workshop",
                },
                {"user_id": "user789", "mode": "build", "template_name": None},
            ]
        }
    )


class PlaygroundAddFormulaParams(BaseModel):
    """Parameters for adding a formula to a playground session"""

    session_id: str = Field(..., description="Session ID")
    formula: str = Field(..., description="Formula string to add")
    description: str = Field(default="", description="Description of the formula")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "session_id": "session123",
                    "formula": "PTS / (2 * (FGA + 0.44 * FTA))",
                    "description": "True Shooting Percentage",
                },
                {
                    "session_id": "session456",
                    "formula": "(FGM + 0.5 * 3PM) / FGA",
                    "description": "Effective Field Goal Percentage",
                },
            ]
        }
    )


class PlaygroundUpdateVariablesParams(BaseModel):
    """Parameters for updating variables in a playground session"""

    session_id: str = Field(..., description="Session ID")
    variables: Dict[str, float] = Field(
        ..., description="Dictionary of variable names and values"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "session_id": "session123",
                    "variables": {"PTS": 25.0, "FGA": 20.0, "FTA": 5.0},
                },
                {
                    "session_id": "session456",
                    "variables": {"FGM": 10.0, "3PM": 3.0, "FGA": 18.0},
                },
            ]
        }
    )


class PlaygroundCalculateResultsParams(BaseModel):
    """Parameters for calculating formula results in a playground session"""

    session_id: str = Field(..., description="Session ID")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"session_id": "session123"}]}
    )


class PlaygroundGenerateVisualizationsParams(BaseModel):
    """Parameters for generating visualizations in a playground session"""

    session_id: str = Field(..., description="Session ID")
    visualization_types: List[str] = Field(
        default=["latex", "table"],
        description="List of visualization types to generate",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"session_id": "session123", "visualization_types": ["latex", "table"]},
                {"session_id": "session456", "visualization_types": ["chart", "graph"]},
            ]
        }
    )


class PlaygroundGetRecommendationsParams(BaseModel):
    """Parameters for getting playground recommendations"""

    session_id: str = Field(..., description="Session ID")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"session_id": "session123"}]}
    )


class PlaygroundShareSessionParams(BaseModel):
    """Parameters for sharing a playground session"""

    session_id: str = Field(..., description="Session ID")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"session_id": "session123"}]}
    )


class PlaygroundGetSharedSessionParams(BaseModel):
    """Parameters for getting a shared playground session"""

    share_token: str = Field(..., description="Share token for the session")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"share_token": "abc123def456"}]}
    )


class PlaygroundCreateExperimentParams(BaseModel):
    """Parameters for creating an experiment from a playground session"""

    session_id: str = Field(..., description="Session ID")
    experiment_name: str = Field(..., description="Name for the experiment")
    description: str = Field(default="", description="Description of the experiment")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "session_id": "session123",
                    "experiment_name": "Shooting Efficiency Analysis",
                    "description": "Analysis of player shooting efficiency",
                },
                {
                    "session_id": "session456",
                    "experiment_name": "Advanced Metrics Comparison",
                    "description": "Comparison of advanced basketball metrics",
                },
            ]
        }
    )


# ============================================================================
# Sprint 7: Machine Learning Parameters
# ============================================================================

# Clustering Parameters


class KMeansClusteringParams(BaseModel):
    """Parameters for K-means clustering"""

    data: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Data points (each row is a sample, each column is a feature)",
    )
    k: int = Field(default=3, ge=1, description="Number of clusters")
    max_iterations: int = Field(
        default=100, ge=1, le=1000, description="Maximum iterations"
    )
    tolerance: float = Field(default=1e-4, gt=0, description="Convergence tolerance")
    random_seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )

    @field_validator("k")
    @classmethod
    def validate_k(cls, v, info):
        if "data" in info.data and v > len(info.data["data"]):
            raise ValueError(
                f"k ({v}) cannot exceed number of data points ({len(info.data['data'])})"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [[25, 3, 5], [22, 4, 4], [15, 2, 12]],
                    "k": 2,
                    "max_iterations": 100,
                }
            ]
        }
    )


class EuclideanDistanceParams(BaseModel):
    """Parameters for Euclidean distance calculation"""

    point1: List[Union[int, float]] = Field(
        ..., min_length=1, description="First point coordinates"
    )
    point2: List[Union[int, float]] = Field(
        ..., min_length=1, description="Second point coordinates"
    )

    @field_validator("point2")
    @classmethod
    def validate_same_length(cls, v, info):
        if "point1" in info.data and len(v) != len(info.data["point1"]):
            raise ValueError(f"Points must have same dimensions")
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"point1": [1, 2, 3], "point2": [4, 5, 6]}]}
    )


class CosineSimilarityParams(BaseModel):
    """Parameters for cosine similarity calculation"""

    vector1: List[Union[int, float]] = Field(
        ..., min_length=1, description="First vector"
    )
    vector2: List[Union[int, float]] = Field(
        ..., min_length=1, description="Second vector"
    )

    @field_validator("vector2")
    @classmethod
    def validate_same_length(cls, v, info):
        if "vector1" in info.data and len(v) != len(info.data["vector1"]):
            raise ValueError("Vectors must have same dimensions")
        return v

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"vector1": [1, 2, 3], "vector2": [2, 4, 6]}]}
    )


class KnnParams(BaseModel):
    """Parameters for K-nearest neighbors"""

    point: List[Union[int, float]] = Field(
        ..., min_length=1, description="Point to classify"
    )
    data: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Training data points"
    )
    labels: List[Any] = Field(..., min_length=1, description="Labels for training data")
    k: int = Field(default=5, ge=1, description="Number of neighbors to consider")
    distance_metric: Literal["euclidean", "cosine"] = Field(
        default="euclidean", description="Distance metric to use"
    )

    @field_validator("labels")
    @classmethod
    def validate_labels_length(cls, v, info):
        if "data" in info.data and len(v) != len(info.data["data"]):
            raise ValueError("Labels must have same length as data")
        return v

    @field_validator("k")
    @classmethod
    def validate_k(cls, v, info):
        if "data" in info.data and v > len(info.data["data"]):
            raise ValueError(
                f"k ({v}) cannot exceed number of training points ({len(info.data['data'])})"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "point": [15, 8, 3],
                    "data": [[20, 5, 4], [18, 7, 5], [12, 3, 8]],
                    "labels": ["PG", "SG", "C"],
                    "k": 3,
                }
            ]
        }
    )


class HierarchicalClusteringParams(BaseModel):
    """Parameters for hierarchical clustering"""

    data: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Data points to cluster"
    )
    n_clusters: int = Field(default=3, ge=1, description="Number of clusters to form")
    linkage: Literal["single", "complete", "average"] = Field(
        default="average", description="Linkage criterion"
    )

    @field_validator("n_clusters")
    @classmethod
    def validate_n_clusters(cls, v, info):
        if "data" in info.data and v > len(info.data["data"]):
            raise ValueError(
                f"n_clusters ({v}) cannot exceed number of points ({len(info.data['data'])})"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [[25, 5], [22, 6], [15, 12]],
                    "n_clusters": 2,
                    "linkage": "average",
                }
            ]
        }
    )


# Classification Parameters


class LogisticRegressionParams(BaseModel):
    """Parameters for logistic regression training"""

    X_train: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Training features"
    )
    y_train: List[int] = Field(
        ..., min_length=1, description="Training labels (0 or 1)"
    )
    learning_rate: float = Field(
        default=0.01, gt=0, le=1, description="Learning rate for gradient descent"
    )
    max_iterations: int = Field(
        default=1000, ge=1, le=10000, description="Maximum training iterations"
    )
    tolerance: float = Field(default=1e-4, gt=0, description="Convergence tolerance")

    @field_validator("y_train")
    @classmethod
    def validate_y_train(cls, v, info):
        if "X_train" in info.data and len(v) != len(info.data["X_train"]):
            raise ValueError("X_train and y_train must have same length")
        # Validate binary labels
        unique_labels = set(v)
        if not unique_labels.issubset({0, 1}):
            raise ValueError(
                f"y_train must contain only 0 and 1. Found: {unique_labels}"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "X_train": [[25, 5, 0.6], [18, 8, 0.55], [30, 4, 0.65]],
                    "y_train": [1, 0, 1],
                    "learning_rate": 0.01,
                }
            ]
        }
    )


class LogisticPredictParams(BaseModel):
    """Parameters for logistic regression prediction"""

    X: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Features to predict"
    )
    weights: List[float] = Field(
        ..., min_length=1, description="Trained weights from logistic_regression"
    )
    threshold: float = Field(
        default=0.5, ge=0, le=1, description="Classification threshold"
    )
    return_probabilities: bool = Field(
        default=False, description="Return probabilities instead of binary predictions"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "X": [[28, 6, 0.62]],
                    "weights": [0.1, 0.5, 0.3, 0.2],
                    "threshold": 0.5,
                }
            ]
        }
    )


class NaiveBayesTrainParams(BaseModel):
    """Parameters for Naive Bayes training"""

    X_train: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Training features"
    )
    y_train: List[Any] = Field(..., min_length=1, description="Training labels")

    @field_validator("y_train")
    @classmethod
    def validate_y_train(cls, v, info):
        if "X_train" in info.data and len(v) != len(info.data["X_train"]):
            raise ValueError("X_train and y_train must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "X_train": [[198, 88, 18], [206, 95, 22], [213, 110, 15]],
                    "y_train": ["SG", "SF", "C"],
                }
            ]
        }
    )


class NaiveBayesPredictParams(BaseModel):
    """Parameters for Naive Bayes prediction"""

    X: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Features to predict"
    )
    model: Dict[str, Any] = Field(
        ..., description="Trained model from naive_bayes_train"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "X": [[200, 90, 20]],
                    "model": {"classes": ["PG", "SG"], "class_priors": {}},
                }
            ]
        }
    )


class DecisionTreeTrainParams(BaseModel):
    """Parameters for decision tree training"""

    X_train: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Training features"
    )
    y_train: List[Any] = Field(..., min_length=1, description="Training labels")
    max_depth: int = Field(default=5, ge=1, le=20, description="Maximum tree depth")
    min_samples_split: int = Field(
        default=2, ge=2, description="Minimum samples required to split"
    )

    @field_validator("y_train")
    @classmethod
    def validate_y_train(cls, v, info):
        if "X_train" in info.data and len(v) != len(info.data["X_train"]):
            raise ValueError("X_train and y_train must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "X_train": [[0.62, 115, 108], [0.55, 108, 112]],
                    "y_train": ["Playoffs", "Missed"],
                    "max_depth": 5,
                }
            ]
        }
    )


class DecisionTreePredictParams(BaseModel):
    """Parameters for decision tree prediction"""

    X: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Features to predict"
    )
    tree: Dict[str, Any] = Field(
        ..., description="Trained tree from decision_tree_train"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"X": [[0.58, 110, 110]], "tree": {"type": "split", "feature": 0}}
            ]
        }
    )


class RandomForestTrainParams(BaseModel):
    """Parameters for random forest training"""

    X_train: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Training features"
    )
    y_train: List[Any] = Field(..., min_length=1, description="Training labels")
    n_trees: int = Field(
        default=10, ge=1, le=100, description="Number of trees in forest"
    )
    max_depth: int = Field(default=5, ge=1, le=20, description="Maximum depth per tree")
    min_samples_split: int = Field(
        default=2, ge=2, description="Minimum samples to split"
    )
    random_seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )

    @field_validator("y_train")
    @classmethod
    def validate_y_train(cls, v, info):
        if "X_train" in info.data and len(v) != len(info.data["X_train"]):
            raise ValueError("X_train and y_train must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "X_train": [[28, 8, 27], [25, 6, 22]],
                    "y_train": ["MVP", "All-Star"],
                    "n_trees": 50,
                }
            ]
        }
    )


class RandomForestPredictParams(BaseModel):
    """Parameters for random forest prediction"""

    X: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Features to predict"
    )
    model: Dict[str, Any] = Field(
        ..., description="Trained model from random_forest_train"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"X": [[29, 7, 25]], "model": {"trees": [], "n_trees": 50}}]
        }
    )


# Anomaly Detection Parameters


class ZScoreOutliersParams(BaseModel):
    """Parameters for Z-score outlier detection"""

    data: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Data points to analyze"
    )
    threshold: float = Field(
        default=3.0,
        gt=0,
        description="Z-score threshold (default 3.0 = 3 standard deviations)",
    )
    labels: Optional[List[Any]] = Field(
        default=None, description="Optional labels for data points"
    )

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v, info):
        if v is not None and "data" in info.data and len(v) != len(info.data["data"]):
            raise ValueError("Labels must have same length as data")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"data": [[25, 5, 5], [22, 6, 4], [50, 12, 15]], "threshold": 3.0}
            ]
        }
    )


class IsolationForestParams(BaseModel):
    """Parameters for isolation forest anomaly detection"""

    data: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Data points to analyze"
    )
    n_trees: int = Field(
        default=100, ge=1, le=500, description="Number of isolation trees"
    )
    sample_size: Optional[int] = Field(
        default=None,
        ge=1,
        description="Samples per tree (default: min(256, len(data)))",
    )
    contamination: float = Field(
        default=0.1, gt=0, lt=0.5, description="Expected proportion of outliers"
    )
    random_seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [[25, 5], [22, 6], [28, 7]],
                    "n_trees": 100,
                    "contamination": 0.1,
                }
            ]
        }
    )


class LocalOutlierFactorParams(BaseModel):
    """Parameters for local outlier factor"""

    data: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Data points to analyze"
    )
    k: int = Field(default=20, ge=1, description="Number of neighbors to consider")
    contamination: float = Field(
        default=0.1, gt=0, lt=0.5, description="Expected proportion of outliers"
    )

    @field_validator("k")
    @classmethod
    def validate_k(cls, v, info):
        if "data" in info.data and v >= len(info.data["data"]):
            raise ValueError(
                f"k ({v}) must be less than number of points ({len(info.data['data'])})"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"data": [[25, 5], [22, 6], [28, 7]], "k": 5, "contamination": 0.1}
            ]
        }
    )


# Feature Engineering Parameters


class NormalizeFeaturesParams(BaseModel):
    """Parameters for feature normalization"""

    data: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Data to normalize"
    )
    method: Literal["min-max", "z-score", "robust", "max-abs"] = Field(
        default="min-max", description="Normalization method"
    )
    feature_range: Tuple[float, float] = Field(
        default=(0.0, 1.0), description="Target range for min-max scaling"
    )

    @field_validator("feature_range")
    @classmethod
    def validate_feature_range(cls, v):
        if v[0] >= v[1]:
            raise ValueError(f"feature_range must be (min, max): {v}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [[25, 5, 5], [22, 6, 4]],
                    "method": "min-max",
                    "feature_range": [0.0, 1.0],
                }
            ]
        }
    )


class FeatureImportanceParams(BaseModel):
    """Parameters for feature importance calculation"""

    X: List[List[Union[int, float]]] = Field(
        ..., min_length=1, description="Feature data"
    )
    y: List[Any] = Field(..., min_length=1, description="True labels")
    model_predictions: List[Any] = Field(
        ..., min_length=1, description="Baseline predictions"
    )
    n_repeats: int = Field(
        default=10, ge=1, le=100, description="Number of permutation repeats"
    )
    random_seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )

    @field_validator("y")
    @classmethod
    def validate_y(cls, v, info):
        if "X" in info.data and len(v) != len(info.data["X"]):
            raise ValueError("X and y must have same length")
        return v

    @field_validator("model_predictions")
    @classmethod
    def validate_predictions(cls, v, info):
        if "y" in info.data and len(v) != len(info.data["y"]):
            raise ValueError("model_predictions must have same length as y")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "X": [[25, 5], [22, 6]],
                    "y": [1, 0],
                    "model_predictions": [1, 0],
                    "n_repeats": 10,
                }
            ]
        }
    )


# ============================================================================
# Sprint 8: Model Evaluation & Validation Parameters
# ============================================================================

# Classification Metrics Parameters


class AccuracyScoreParams(BaseModel):
    """Parameters for accuracy score calculation"""

    y_true: List[Any] = Field(..., min_length=1, description="True labels")
    y_pred: List[Any] = Field(..., min_length=1, description="Predicted labels")

    @field_validator("y_pred")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_pred must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"y_true": [1, 0, 1, 1, 0], "y_pred": [1, 0, 1, 0, 0]}]
        }
    )


class PrecisionRecallF1Params(BaseModel):
    """Parameters for precision, recall, and F1-score calculation"""

    y_true: List[Any] = Field(..., min_length=1, description="True labels")
    y_pred: List[Any] = Field(..., min_length=1, description="Predicted labels")
    average: Literal["binary", "macro", "micro", "weighted"] = Field(
        default="binary", description="Averaging strategy for multiclass"
    )
    pos_label: Any = Field(
        default=1, description="Positive class label (for binary classification)"
    )

    @field_validator("y_pred")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_pred must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "y_true": [1, 0, 1, 1, 0, 1],
                    "y_pred": [1, 0, 1, 0, 0, 1],
                    "average": "binary",
                }
            ]
        }
    )


class ConfusionMatrixParams(BaseModel):
    """Parameters for confusion matrix calculation"""

    y_true: List[Any] = Field(..., min_length=1, description="True labels")
    y_pred: List[Any] = Field(..., min_length=1, description="Predicted labels")
    pos_label: Any = Field(
        default=1, description="Positive class label (for binary classification)"
    )

    @field_validator("y_pred")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_pred must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"y_true": [1, 0, 1, 1, 0], "y_pred": [1, 0, 1, 0, 1]}]
        }
    )


class RocAucScoreParams(BaseModel):
    """Parameters for ROC-AUC calculation"""

    y_true: List[int] = Field(
        ..., min_length=2, description="True binary labels (0 or 1)"
    )
    y_scores: List[float] = Field(
        ..., min_length=2, description="Predicted probabilities or scores"
    )
    num_thresholds: int = Field(
        default=100, ge=10, le=1000, description="Number of thresholds for ROC curve"
    )

    @field_validator("y_true")
    @classmethod
    def validate_binary_labels(cls, v):
        unique_labels = set(v)
        if not unique_labels.issubset({0, 1}):
            raise ValueError(
                f"y_true must contain only 0 and 1. Found: {unique_labels}"
            )
        return v

    @field_validator("y_scores")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_scores must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "y_true": [0, 0, 1, 1],
                    "y_scores": [0.1, 0.4, 0.35, 0.8],
                    "num_thresholds": 100,
                }
            ]
        }
    )


class ClassificationReportParams(BaseModel):
    """Parameters for classification report"""

    y_true: List[Any] = Field(..., min_length=1, description="True labels")
    y_pred: List[Any] = Field(..., min_length=1, description="Predicted labels")

    @field_validator("y_pred")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_pred must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "y_true": ["PG", "SG", "PG", "C", "PF"],
                    "y_pred": ["PG", "SG", "SG", "C", "PF"],
                }
            ]
        }
    )


class LogLossParams(BaseModel):
    """Parameters for log loss (cross-entropy) calculation"""

    y_true: List[int] = Field(
        ..., min_length=1, description="True binary labels (0 or 1)"
    )
    y_pred_proba: List[float] = Field(
        ..., min_length=1, description="Predicted probabilities"
    )
    eps: float = Field(
        default=1e-15,
        gt=0,
        lt=1,
        description="Small value to clip probabilities (avoid log(0))",
    )

    @field_validator("y_true")
    @classmethod
    def validate_binary_labels(cls, v):
        unique_labels = set(v)
        if not unique_labels.issubset({0, 1}):
            raise ValueError(
                f"y_true must contain only 0 and 1. Found: {unique_labels}"
            )
        return v

    @field_validator("y_pred_proba")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_pred_proba must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"y_true": [1, 0, 1, 0], "y_pred_proba": [0.9, 0.1, 0.8, 0.2]}]
        }
    )


# Regression Metrics Parameters


class MseRmseMaeParams(BaseModel):
    """Parameters for MSE, RMSE, and MAE calculation"""

    y_true: List[Union[int, float]] = Field(
        ..., min_length=1, description="True values"
    )
    y_pred: List[Union[int, float]] = Field(
        ..., min_length=1, description="Predicted values"
    )

    @field_validator("y_pred")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_pred must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"y_true": [3.0, -0.5, 2.0, 7.0], "y_pred": [2.5, 0.0, 2.0, 8.0]}
            ]
        }
    )


class R2ScoreParams(BaseModel):
    """Parameters for R² (coefficient of determination) calculation"""

    y_true: List[Union[int, float]] = Field(
        ..., min_length=2, description="True values"
    )
    y_pred: List[Union[int, float]] = Field(
        ..., min_length=2, description="Predicted values"
    )

    @field_validator("y_pred")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_pred must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"y_true": [3.0, -0.5, 2.0, 7.0], "y_pred": [2.5, 0.0, 2.0, 8.0]}
            ]
        }
    )


class MapeParams(BaseModel):
    """Parameters for Mean Absolute Percentage Error calculation"""

    y_true: List[Union[int, float]] = Field(
        ..., min_length=1, description="True values"
    )
    y_pred: List[Union[int, float]] = Field(
        ..., min_length=1, description="Predicted values"
    )

    @field_validator("y_true")
    @classmethod
    def validate_no_zeros(cls, v):
        if any(val == 0 for val in v):
            raise ValueError(
                "y_true cannot contain zeros (would cause division by zero)"
            )
        return v

    @field_validator("y_pred")
    @classmethod
    def validate_same_length(cls, v, info):
        if "y_true" in info.data and len(v) != len(info.data["y_true"]):
            raise ValueError("y_true and y_pred must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "y_true": [100.0, 50.0, 30.0, 20.0],
                    "y_pred": [110.0, 45.0, 35.0, 22.0],
                }
            ]
        }
    )


# Cross-Validation Parameters


class KFoldSplitParams(BaseModel):
    """Parameters for K-fold cross-validation splits"""

    n_samples: int = Field(..., ge=2, description="Total number of samples")
    n_folds: int = Field(default=5, ge=2, le=20, description="Number of folds")
    shuffle: bool = Field(
        default=True, description="Whether to shuffle data before splitting"
    )
    random_seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )

    @field_validator("n_folds")
    @classmethod
    def validate_n_folds(cls, v, info):
        if "n_samples" in info.data and v > info.data["n_samples"]:
            raise ValueError(
                f"n_folds ({v}) cannot exceed n_samples ({info.data['n_samples']})"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"n_samples": 100, "n_folds": 5, "shuffle": True}]
        }
    )


class StratifiedKFoldSplitParams(BaseModel):
    """Parameters for stratified K-fold cross-validation"""

    y: List[Any] = Field(..., min_length=2, description="Labels for stratification")
    n_folds: int = Field(default=5, ge=2, le=20, description="Number of folds")
    shuffle: bool = Field(
        default=True, description="Whether to shuffle data before splitting"
    )
    random_seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )

    @field_validator("n_folds")
    @classmethod
    def validate_n_folds(cls, v, info):
        if "y" in info.data and v > len(info.data["y"]):
            raise ValueError(
                f"n_folds ({v}) cannot exceed number of samples ({len(info.data['y'])})"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"y": [0, 0, 1, 1, 0, 1, 1, 0], "n_folds": 4, "shuffle": True}]
        }
    )


class CrossValidateParams(BaseModel):
    """Parameters for cross-validation helper"""

    n_samples: int = Field(..., ge=2, description="Total number of samples")
    n_folds: int = Field(default=5, ge=2, le=20, description="Number of folds")
    stratify: bool = Field(
        default=False, description="Use stratified K-fold (requires y labels)"
    )
    y: Optional[List[Any]] = Field(
        default=None,
        description="Labels for stratification (required if stratify=True)",
    )
    shuffle: bool = Field(default=True, description="Whether to shuffle data")
    random_seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )

    @model_validator(mode="after")
    def validate_stratify_requirements(self):
        if self.stratify and self.y is None:
            raise ValueError("y labels required when stratify=True")
        if self.y is not None and len(self.y) != self.n_samples:
            raise ValueError(
                f"Length of y ({len(self.y)}) must equal n_samples ({self.n_samples})"
            )
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"n_samples": 100, "n_folds": 5, "stratify": False, "shuffle": True}
            ]
        }
    )


# Model Comparison Parameters


class CompareModelsParams(BaseModel):
    """Parameters for comparing multiple models"""

    models: List[Dict[str, Any]] = Field(
        ..., min_length=2, description="List of models with names and predictions"
    )
    y_true: List[Any] = Field(..., min_length=1, description="True labels")
    metrics: Optional[List[str]] = Field(
        default=None,
        description="Metrics to compare (defaults to accuracy, precision, recall, f1)",
    )

    @field_validator("models")
    @classmethod
    def validate_models(cls, v):
        for model in v:
            if "name" not in model or "predictions" not in model:
                raise ValueError("Each model must have 'name' and 'predictions' keys")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "models": [
                        {"name": "Model A", "predictions": [1, 0, 1, 0]},
                        {"name": "Model B", "predictions": [1, 1, 1, 0]},
                    ],
                    "y_true": [1, 0, 1, 1],
                    "metrics": ["accuracy", "f1"],
                }
            ]
        }
    )


class PairedTTestParams(BaseModel):
    """Parameters for paired t-test"""

    scores_a: List[float] = Field(..., min_length=2, description="Scores from model A")
    scores_b: List[float] = Field(..., min_length=2, description="Scores from model B")
    alpha: float = Field(default=0.05, gt=0, lt=1, description="Significance level")

    @field_validator("scores_b")
    @classmethod
    def validate_same_length(cls, v, info):
        if "scores_a" in info.data and len(v) != len(info.data["scores_a"]):
            raise ValueError("scores_a and scores_b must have same length")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "scores_a": [0.85, 0.87, 0.82, 0.90, 0.88],
                    "scores_b": [0.80, 0.83, 0.79, 0.85, 0.82],
                    "alpha": 0.05,
                }
            ]
        }
    )


# Hyperparameter Tuning Parameters


class GridSearchParams(BaseModel):
    """Parameters for grid search parameter generation"""

    param_grid: Dict[str, List[Any]] = Field(
        ..., description="Dictionary mapping parameter names to lists of values to try"
    )
    n_combinations: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of combinations to generate (optional limit)",
    )

    @field_validator("param_grid")
    @classmethod
    def validate_param_grid(cls, v):
        if not v:
            raise ValueError("param_grid cannot be empty")
        for param_name, param_values in v.items():
            if not isinstance(param_values, list) or len(param_values) == 0:
                raise ValueError(
                    f"Parameter '{param_name}' must have at least one value"
                )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "param_grid": {
                        "learning_rate": [0.01, 0.1, 0.5],
                        "max_depth": [3, 5, 7],
                        "n_trees": [10, 50, 100],
                    }
                }
            ]
        }
    )


# ============================================================================
# Helper Functions
# ============================================================================


def validate_params(
    params_class: type[BaseModel], arguments: Dict[str, Any]
) -> BaseModel:
    """
    Validate and parse parameters using Pydantic.

    Args:
        params_class: Pydantic model class
        arguments: Raw arguments dict

    Returns:
        Validated and parsed parameters

    Raises:
        ValidationError: If validation fails

    Example:
        >>> params = validate_params(QueryDatabaseParams, {"sql_query": "SELECT 1"})
        >>> params.sql_query
        'SELECT 1'
        >>> params.max_rows
        1000
    """
    return params_class(**arguments)


# ============================================================================
# Phase 3.2: Advanced Visualization Engine Parameters
# ============================================================================


class VisualizationGenerateParams(BaseModel):
    """Parameters for generating visualizations"""

    visualization_type: str = Field(
        ..., description="Type of visualization to generate"
    )
    data: Dict[str, Any] = Field(..., description="Data to visualize")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Visualization configuration"
    )
    chart_type: Optional[str] = Field(
        default=None, description="Specific chart type for chart visualizations"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "visualization_type": "scatter",
                    "data": {
                        "x": [1, 2, 3, 4],
                        "y": [2, 4, 6, 8],
                        "labels": ["A", "B", "C", "D"],
                    },
                    "config": {
                        "title": "Sample Scatter Plot",
                        "width": 800,
                        "height": 600,
                    },
                },
                {
                    "visualization_type": "heatmap",
                    "data": {"x": [1, 2, 3], "y": [1, 2, 3], "z": [0.5, 0.8, 0.3]},
                    "config": {"title": "Performance Heatmap"},
                },
            ]
        }
    )


class VisualizationExportParams(BaseModel):
    """Parameters for exporting visualizations"""

    visualization_data: Dict[str, Any] = Field(
        ..., description="Visualization data to export"
    )
    format: str = Field(..., description="Export format (png, svg, pdf, html, json)")
    filename: Optional[str] = Field(
        default=None, description="Optional filename for export"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "visualization_data": {
                        "type": "scatter",
                        "data": [{"x": 1, "y": 2}],
                    },
                    "format": "png",
                    "filename": "my_chart.png",
                },
                {
                    "visualization_data": {
                        "type": "table",
                        "data": [["A", "B"], [1, 2]],
                    },
                    "format": "html",
                },
            ]
        }
    )


class VisualizationTemplateParams(BaseModel):
    """Parameters for getting visualization templates"""

    template_name: Optional[str] = Field(
        default=None, description="Specific template name to retrieve"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"template_name": "player_comparison"},
                {"template_name": "team_metrics"},
                {},
            ]
        }
    )


class VisualizationConfigParams(BaseModel):
    """Parameters for visualization configuration"""

    width: int = Field(default=800, description="Visualization width in pixels")
    height: int = Field(default=600, description="Visualization height in pixels")
    title: str = Field(default="", description="Visualization title")
    x_label: str = Field(default="", description="X-axis label")
    y_label: str = Field(default="", description="Y-axis label")
    z_label: str = Field(default="", description="Z-axis label (for 3D plots)")
    color_scheme: str = Field(default="default", description="Color scheme to use")
    theme: str = Field(default="light", description="Visualization theme")
    show_grid: bool = Field(default=True, description="Show grid lines")
    show_legend: bool = Field(default=True, description="Show legend")
    interactive: bool = Field(
        default=True, description="Make visualization interactive"
    )
    animation: bool = Field(default=False, description="Enable animations")
    export_format: str = Field(default="png", description="Default export format")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "width": 1000,
                    "height": 800,
                    "title": "Player Performance Analysis",
                    "x_label": "Offensive Rating",
                    "y_label": "Defensive Rating",
                    "color_scheme": "sports",
                    "interactive": True,
                },
                {
                    "width": 600,
                    "height": 400,
                    "title": "Simple Chart",
                    "theme": "dark",
                    "show_grid": False,
                },
            ]
        }
    )


class DataPointParams(BaseModel):
    """Parameters for creating data points"""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: Optional[float] = Field(default=None, description="Z coordinate (for 3D)")
    label: Optional[str] = Field(default=None, description="Data point label")
    color: Optional[str] = Field(default=None, description="Data point color")
    size: Optional[float] = Field(default=None, description="Data point size")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"x": 25.0, "y": 15.0, "label": "Player A", "color": "#FF6B6B"},
                {"x": 1.0, "y": 2.0, "z": 3.0, "label": "3D Point"},
                {"x": 10.0, "y": 20.0, "size": 5.0, "metadata": {"team": "Lakers"}},
            ]
        }
    )


class DatasetParams(BaseModel):
    """Parameters for creating datasets"""

    name: str = Field(..., description="Dataset name")
    data_points: List[Dict[str, Any]] = Field(..., description="List of data points")
    x_column: str = Field(default="x", description="X column name")
    y_column: str = Field(default="y", description="Y column name")
    z_column: Optional[str] = Field(default=None, description="Z column name")
    color_column: Optional[str] = Field(default=None, description="Color column name")
    size_column: Optional[str] = Field(default=None, description="Size column name")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Dataset metadata"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Player Stats",
                    "data_points": [
                        {"x": 25.0, "y": 15.0, "label": "Player A"},
                        {"x": 20.0, "y": 18.0, "label": "Player B"},
                    ],
                    "x_column": "points",
                    "y_column": "rebounds",
                },
                {
                    "name": "3D Data",
                    "data_points": [
                        {"x": 1.0, "y": 2.0, "z": 3.0},
                        {"x": 4.0, "y": 5.0, "z": 6.0},
                    ],
                    "z_column": "z_value",
                },
            ]
        }
    )


# ============================================================================
# Phase 3.3: Formula Validation System Parameters
# ============================================================================


class FormulaValidationParams(BaseModel):
    """Parameters for formula validation"""

    formula: str = Field(..., description="Formula string to validate")
    formula_id: Optional[str] = Field(
        default=None, description="Optional identifier for the formula"
    )
    test_data: Optional[Dict[str, float]] = Field(
        default=None, description="Test data for validation"
    )
    validation_types: Optional[List[str]] = Field(
        default=None, description="Types of validation to perform"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula": "PTS / (2 * (FGA + 0.44 * FTA))",
                    "formula_id": "true_shooting",
                    "test_data": {"PTS": 25, "FGA": 20, "FTA": 5},
                    "validation_types": ["mathematical", "accuracy", "consistency"],
                },
                {
                    "formula": "(FGM * 85.910 + STL * 53.897) / MP",
                    "formula_id": "per_simplified",
                    "validation_types": ["mathematical", "domain_specific"],
                },
            ]
        }
    )


class FormulaReferenceParams(BaseModel):
    """Parameters for adding formula references"""

    formula_id: str = Field(..., description="Unique identifier for the formula")
    name: str = Field(..., description="Human-readable name of the formula")
    formula: str = Field(..., description="Formula string")
    source: str = Field(..., description="Source of the formula (book, paper, etc.)")
    page: Optional[str] = Field(default=None, description="Page number or section")
    expected_result: Optional[float] = Field(
        default=None, description="Expected result for validation"
    )
    test_data: Optional[Dict[str, float]] = Field(
        default=None, description="Test data for validation"
    )
    description: Optional[str] = Field(
        default=None, description="Description of the formula"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula_id": "usage_rate",
                    "name": "Usage Rate",
                    "formula": "((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
                    "source": "Basketball on Paper",
                    "page": "Chapter 5",
                    "expected_result": 28.5,
                    "test_data": {
                        "FGA": 18,
                        "FTA": 6,
                        "TOV": 3,
                        "MP": 35,
                        "TM_MP": 240,
                        "TM_FGA": 90,
                        "TM_FTA": 25,
                        "TM_TOV": 12,
                    },
                    "description": "Usage rate calculation",
                }
            ]
        }
    )


class ValidationReportParams(BaseModel):
    """Parameters for retrieving validation reports"""

    report_id: Optional[str] = Field(
        default=None, description="Specific report ID to retrieve"
    )
    formula_id: Optional[str] = Field(
        default=None, description="Formula ID to get reports for"
    )
    status_filter: Optional[str] = Field(
        default=None, description="Filter by validation status"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None, description="Date range filter"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"report_id": "report_123"},
                {"formula_id": "per", "status_filter": "valid"},
                {"date_range": {"start": "2025-01-01", "end": "2025-01-31"}},
            ]
        }
    )


class ValidationComparisonParams(BaseModel):
    """Parameters for comparing formula validations"""

    formula_ids: List[str] = Field(..., description="List of formula IDs to compare")
    comparison_type: str = Field(
        default="accuracy", description="Type of comparison to perform"
    )
    test_data: Optional[Dict[str, float]] = Field(
        default=None, description="Test data for comparison"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula_ids": ["per", "true_shooting", "usage_rate"],
                    "comparison_type": "accuracy",
                    "test_data": {"PTS": 25, "FGA": 20, "FTA": 5, "MP": 35},
                }
            ]
        }
    )


class ValidationRulesParams(BaseModel):
    """Parameters for updating validation rules"""

    accuracy_threshold: Optional[float] = Field(
        default=None, description="Accuracy threshold (0.0-1.0)"
    )
    consistency_threshold: Optional[float] = Field(
        default=None, description="Consistency threshold (0.0-1.0)"
    )
    mathematical_tolerance: Optional[float] = Field(
        default=None, description="Mathematical tolerance"
    )
    domain_tolerance: Optional[float] = Field(
        default=None, description="Domain-specific tolerance"
    )
    performance_threshold: Optional[float] = Field(
        default=None, description="Performance threshold in seconds"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "accuracy_threshold": 0.95,
                    "consistency_threshold": 0.90,
                    "mathematical_tolerance": 0.01,
                    "performance_threshold": 1.0,
                }
            ]
        }
    )


# ============================================================================
# Phase 3.4: Multi-Book Formula Comparison Parameters
# ============================================================================


class FormulaComparisonParams(BaseModel):
    """Parameters for comparing formula versions"""

    formula_id: str = Field(..., description="ID of the formula to compare")
    comparison_types: Optional[List[str]] = Field(
        default=None, description="Types of comparison to perform"
    )
    include_historical: bool = Field(
        default=True, description="Include historical evolution analysis"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula_id": "per",
                    "comparison_types": ["structural", "mathematical", "accuracy"],
                    "include_historical": True,
                },
                {
                    "formula_id": "true_shooting",
                    "comparison_types": ["accuracy", "source_reliability"],
                    "include_historical": False,
                },
            ]
        }
    )


class FormulaVersionParams(BaseModel):
    """Parameters for adding a formula version"""

    version_id: str = Field(..., description="Unique identifier for this version")
    formula_id: str = Field(
        ..., description="ID of the formula this version belongs to"
    )
    formula: str = Field(..., description="Formula string")
    source_id: str = Field(..., description="ID of the source")
    description: Optional[str] = Field(
        default=None, description="Description of this version"
    )
    test_data: Optional[Dict[str, float]] = Field(
        default=None, description="Test data for validation"
    )
    expected_result: Optional[float] = Field(
        default=None, description="Expected result for validation"
    )
    created_date: Optional[str] = Field(
        default=None, description="Date this version was created"
    )
    is_primary: bool = Field(
        default=False, description="Whether this is the primary version"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "version_id": "per_modern_2023",
                    "formula_id": "per",
                    "formula": "(FGM * 85.91 + STL * 53.9) / MP",
                    "source_id": "basketball_analytics",
                    "description": "Modern simplified PER formula",
                    "test_data": {"FGM": 10, "STL": 2, "MP": 35},
                    "expected_result": 25.0,
                    "created_date": "2023",
                    "is_primary": False,
                }
            ]
        }
    )


class FormulaSourceParams(BaseModel):
    """Parameters for adding a formula source"""

    source_id: str = Field(..., description="Unique identifier for the source")
    name: str = Field(..., description="Name of the source")
    source_type: str = Field(
        ..., description="Type of source (book, paper, website, database)"
    )
    author: Optional[str] = Field(default=None, description="Author of the source")
    publication_date: Optional[str] = Field(
        default=None, description="Publication date"
    )
    page: Optional[str] = Field(default=None, description="Page number or section")
    url: Optional[str] = Field(default=None, description="URL if applicable")
    reliability_score: float = Field(
        default=1.0, description="Reliability score (0.0-1.0)"
    )
    description: Optional[str] = Field(
        default=None, description="Description of the source"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source_id": "new_analytics_book",
                    "name": "Advanced Basketball Analytics",
                    "source_type": "book",
                    "author": "Dr. Analytics Expert",
                    "publication_date": "2024",
                    "reliability_score": 0.92,
                    "description": "Latest book on basketball analytics",
                }
            ]
        }
    )


class FormulaEvolutionParams(BaseModel):
    """Parameters for retrieving formula evolution"""

    formula_id: str = Field(..., description="ID of the formula to analyze")
    include_timeline: bool = Field(
        default=True, description="Include detailed timeline"
    )
    include_changes: bool = Field(
        default=True, description="Include key changes analysis"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"formula_id": "per", "include_timeline": True, "include_changes": True}
            ]
        }
    )


class FormulaRecommendationParams(BaseModel):
    """Parameters for getting formula recommendations"""

    formula_id: str = Field(
        ..., description="ID of the formula to get recommendations for"
    )
    criteria: Optional[List[str]] = Field(
        default=None, description="Recommendation criteria"
    )
    context: Optional[str] = Field(
        default=None, description="Use context for recommendations"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "formula_id": "per",
                    "criteria": ["reliability", "recency", "accuracy"],
                    "context": "academic research",
                }
            ]
        }
    )


# ============================================================================
# Phase 5: Symbolic Regression Parameters
# ============================================================================


class SymbolicRegressionParams(BaseModel):
    """Parameters for symbolic regression formula discovery"""

    data: Dict[str, List[float]] = Field(
        ..., description="Dictionary mapping variable names to lists of values"
    )
    target_variable: str = Field(
        ..., min_length=1, max_length=50, description="Variable to predict"
    )
    input_variables: List[str] = Field(
        ..., min_length=1, max_length=10, description="Variables to use as inputs"
    )
    regression_type: Literal[
        "linear",
        "polynomial",
        "rational",
        "exponential",
        "logarithmic",
        "power",
        "custom",
    ] = Field(default="linear", description="Type of regression to perform")
    optimization_method: Literal[
        "gradient_descent",
        "genetic_algorithm",
        "simulated_annealing",
        "particle_swarm",
        "bayesian",
    ] = Field(
        default="gradient_descent", description="Method for parameter optimization"
    )
    max_complexity: int = Field(
        default=5, ge=1, le=10, description="Maximum complexity of discovered formulas"
    )
    min_r_squared: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum R-squared threshold"
    )

    @field_validator("data")
    def validate_data(cls, v):
        """Validate data structure"""
        if not v:
            raise ValueError("Data cannot be empty")

        # Check all lists have same length
        lengths = [len(values) for values in v.values()]
        if len(set(lengths)) > 1:
            raise ValueError("All variables must have the same number of data points")

        if lengths[0] < 10:
            raise ValueError("Need at least 10 data points for regression")

        return v

    @field_validator("input_variables")
    def validate_input_variables(cls, v, values):
        """Validate input variables exist in data"""
        if "data" in values.data:
            data_keys = set(values.data["data"].keys())
            for var in v:
                if var not in data_keys:
                    raise ValueError(f"Input variable '{var}' not found in data")
        return v

    @field_validator("target_variable")
    def validate_target_variable(cls, v, values):
        """Validate target variable exists in data"""
        if "data" in values.data:
            data_keys = set(values.data["data"].keys())
            if v not in data_keys:
                raise ValueError(f"Target variable '{v}' not found in data")
        return v


class FormulaValidationParams(BaseModel):
    """Parameters for validating discovered formulas"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="Formula to validate"
    )
    test_data: Dict[str, List[float]] = Field(
        ..., description="Test dataset for validation"
    )
    target_variable: str = Field(
        ..., min_length=1, max_length=50, description="Variable to predict"
    )
    threshold_r_squared: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum R-squared threshold for validation",
    )

    @field_validator("test_data")
    def validate_test_data(cls, v):
        """Validate test data structure"""
        if not v:
            raise ValueError("Test data cannot be empty")

        lengths = [len(values) for values in v.values()]
        if len(set(lengths)) > 1:
            raise ValueError("All variables must have the same number of data points")

        return v


class CustomMetricParams(BaseModel):
    """Parameters for generating custom analytics metrics"""

    formula: str = Field(
        ..., min_length=1, max_length=1000, description="The discovered formula"
    )
    metric_name: str = Field(
        ..., min_length=1, max_length=100, description="Name for the custom metric"
    )
    description: str = Field(
        ..., min_length=1, max_length=500, description="Description of the metric"
    )
    variables: List[str] = Field(
        ..., min_length=1, max_length=10, description="Variables used in the formula"
    )
    parameters: Dict[str, float] = Field(
        ..., description="Optimized parameters for the formula"
    )

    @field_validator("metric_name")
    def validate_metric_name(cls, v):
        """Validate metric name format"""
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "Metric name must start with letter and contain only letters, numbers, and underscores"
            )
        return v


class FormulaDiscoveryParams(BaseModel):
    """Parameters for discovering formulas from data patterns"""

    data: Dict[str, List[float]] = Field(
        ..., description="Dataset for formula discovery"
    )
    target_variable: str = Field(
        ..., min_length=1, max_length=50, description="Variable to predict"
    )
    discovery_method: Literal[
        "correlation", "mutual_information", "feature_importance", "genetic_programming"
    ] = Field(
        default="correlation",
        description="Method for discovering variable relationships",
    )
    max_formulas: int = Field(
        default=10, ge=1, le=50, description="Maximum number of formulas to discover"
    )
    complexity_range: Tuple[int, int] = Field(
        default=(1, 5), description="Range of formula complexity to explore"
    )

    @field_validator("complexity_range")
    def validate_complexity_range(cls, v):
        """Validate complexity range"""
        if v[0] >= v[1]:
            raise ValueError("Minimum complexity must be less than maximum complexity")
        if v[0] < 1 or v[1] > 10:
            raise ValueError("Complexity range must be between 1 and 10")
        return v


# ============================================================================
# Phase 5.2: Natural Language to Formula Parameters
# ============================================================================


class NaturalLanguageFormulaParams(BaseModel):
    """Parameters for natural language to formula conversion"""

    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language description of the formula",
    )
    context: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional context for parsing (e.g., 'basketball', 'player_stats')",
    )
    validate_formula: bool = Field(
        default=True, description="Whether to validate the parsed formula"
    )

    @field_validator("description")
    def validate_description(cls, v):
        """Validate description is not empty and contains meaningful content"""
        if not v.strip():
            raise ValueError("Description cannot be empty")

        # Check for minimum meaningful content
        words = v.split()
        if len(words) < 2:
            raise ValueError("Description must contain at least 2 words")

        return v.strip()


class FormulaSuggestionParams(BaseModel):
    """Parameters for formula suggestions based on description"""

    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language description to suggest formulas for",
    )
    context: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional context for suggestions (e.g., 'basketball', 'team_stats')",
    )
    max_suggestions: int = Field(
        default=5, ge=1, le=20, description="Maximum number of suggestions to return"
    )

    @field_validator("description")
    def validate_description(cls, v):
        """Validate description is meaningful"""
        if not v.strip():
            raise ValueError("Description cannot be empty")

        words = v.split()
        if len(words) < 2:
            raise ValueError("Description must contain at least 2 words")

        return v.strip()


class NLFormulaValidationParams(BaseModel):
    """Parameters for validating natural language formula descriptions"""

    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language description to validate",
    )
    expected_formula: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional expected formula for comparison",
    )
    strict_validation: bool = Field(
        default=False, description="Whether to use strict validation rules"
    )

    @field_validator("description")
    def validate_description(cls, v):
        """Validate description is meaningful"""
        if not v.strip():
            raise ValueError("Description cannot be empty")

        words = v.split()
        if len(words) < 2:
            raise ValueError("Description must contain at least 2 words")

        return v.strip()

    @field_validator("expected_formula")
    def validate_expected_formula(cls, v):
        """Validate expected formula if provided"""
        if v is not None:
            if not v.strip():
                raise ValueError("Expected formula cannot be empty")

            # Basic syntax check
            try:
                import sympy as sp

                sp.parse_expr(v)
            except Exception as e:
                raise ValueError(f"Invalid expected formula syntax: {e}")

        return v


# ============================================================================
# Phase 5.3: Formula Dependency Graph Parameters
# ============================================================================


class FormulaDependencyGraphParams(BaseModel):
    """Parameters for creating formula dependency graphs"""

    analyze_dependencies: bool = Field(
        default=True, description="Whether to analyze dependencies between formulas"
    )
    include_custom_formulas: bool = Field(
        default=True, description="Whether to include custom formulas in analysis"
    )
    min_dependency_strength: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Minimum dependency strength to include in graph",
    )


class FormulaDependencyVisualizationParams(BaseModel):
    """Parameters for visualizing formula dependency graphs"""

    layout: Literal["spring", "circular", "hierarchical"] = Field(
        default="spring", description="Layout algorithm for the graph visualization"
    )
    show_labels: bool = Field(
        default=True, description="Whether to show node labels in the visualization"
    )
    node_size: int = Field(
        default=1000, ge=100, le=5000, description="Size of nodes in the visualization"
    )
    edge_width: float = Field(
        default=1.0, ge=0.1, le=5.0, description="Width of edges in the visualization"
    )
    save_path: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional path to save the visualization image",
    )


class FormulaDependencyPathParams(BaseModel):
    """Parameters for finding dependency paths between formulas"""

    source_formula: str = Field(
        ..., min_length=1, max_length=100, description="Starting formula ID"
    )
    target_formula: str = Field(
        ..., min_length=1, max_length=100, description="Target formula ID"
    )
    max_depth: int = Field(
        default=5, ge=1, le=10, description="Maximum path depth to search"
    )

    @field_validator("source_formula")
    def validate_source_formula(cls, v):
        """Validate source formula ID"""
        if not v.strip():
            raise ValueError("Source formula ID cannot be empty")
        return v.strip()

    @field_validator("target_formula")
    def validate_target_formula(cls, v):
        """Validate target formula ID"""
        if not v.strip():
            raise ValueError("Target formula ID cannot be empty")
        return v.strip()


class FormulaComplexityAnalysisParams(BaseModel):
    """Parameters for analyzing formula complexity"""

    formula_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional specific formula ID to analyze (if None, analyzes all formulas)",
    )
    include_statistics: bool = Field(
        default=True, description="Whether to include statistical analysis"
    )
    include_centrality: bool = Field(
        default=True, description="Whether to include centrality measures"
    )

    @field_validator("formula_id")
    def validate_formula_id(cls, v):
        """Validate formula ID if provided"""
        if v is not None and not v.strip():
            raise ValueError("Formula ID cannot be empty")
        return v.strip() if v else None


class FormulaDependencyExportParams(BaseModel):
    """Parameters for exporting formula dependency graphs"""

    format: Literal["json", "graphml", "gexf"] = Field(
        default="json", description="Export format for the dependency graph"
    )
    include_visualization: bool = Field(
        default=False, description="Whether to include visualization data in export"
    )
    include_metadata: bool = Field(
        default=True, description="Whether to include metadata in export"
    )
    export_path: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional path to save the exported file",
    )


# ============================================================================
# Phase 6.1: Automated Book Analysis Pipeline Parameters
# ============================================================================


class AutomatedBookAnalysisParams(BaseModel):
    """Parameters for automated book analysis"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Path to the PDF book file to analyze",
    )
    book_title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional title of the book (auto-detected if not provided)",
    )
    book_author: Optional[str] = Field(
        default=None, max_length=200, description="Optional author of the book"
    )
    max_pages: Optional[int] = Field(
        default=None,
        ge=1,
        le=1000,
        description="Maximum number of pages to analyze (None for all pages)",
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for formula inclusion (0.0-1.0)",
    )

    @field_validator("book_path")
    def validate_book_path(cls, v):
        """Validate book path"""
        if not v.strip():
            raise ValueError("Book path cannot be empty")
        if not v.lower().endswith(".pdf"):
            raise ValueError("Book path must be a PDF file")
        return v.strip()


class FormulaCategorizationParams(BaseModel):
    """Parameters for categorizing extracted formulas"""

    formulas: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="List of extracted formula dictionaries to categorize",
    )
    custom_categories: Optional[Dict[str, List[str]]] = Field(
        default=None, description="Optional custom category definitions with keywords"
    )

    @field_validator("formulas")
    def validate_formulas(cls, v):
        """Validate formulas list"""
        if not v:
            raise ValueError("Formulas list cannot be empty")
        return v


class FormulaValidationParams(BaseModel):
    """Parameters for validating extracted formulas"""

    formulas: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="List of extracted formula dictionaries to validate",
    )
    validation_rules: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional custom validation rules"
    )

    @field_validator("formulas")
    def validate_formulas(cls, v):
        """Validate formulas list"""
        if not v:
            raise ValueError("Formulas list cannot be empty")
        return v


class FormulaDatabaseParams(BaseModel):
    """Parameters for building searchable formula database"""

    analysis_results: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="List of book analysis results to include in database",
    )
    include_metadata: bool = Field(
        default=True, description="Whether to include metadata in database entries"
    )
    include_relationships: bool = Field(
        default=True, description="Whether to include formula relationships in database"
    )
    export_format: Literal["json", "sqlite", "csv"] = Field(
        default="json", description="Export format for the formula database"
    )
    export_path: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional path to save the database file",
    )

    @field_validator("analysis_results")
    def validate_analysis_results(cls, v):
        """Validate analysis results"""
        if not v:
            raise ValueError("Analysis results list cannot be empty")
        return v


class FormulaSearchParams(BaseModel):
    """Parameters for searching the formula database"""

    query: str = Field(
        ..., min_length=1, max_length=200, description="Search query for formulas"
    )
    search_type: Literal["text", "category", "complexity", "variables"] = Field(
        default="text", description="Type of search to perform"
    )
    category_filter: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional category filter for search results",
    )
    complexity_filter: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Optional complexity filter for search results",
    )
    max_results: int = Field(
        default=50, ge=1, le=200, description="Maximum number of results to return"
    )

    @field_validator("query")
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()


# ============================================================================
# Phase 6.2: Cross-Reference System Parameters
# ============================================================================


class CitationParams(BaseModel):
    """Parameters for adding citations to formulas"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula being cited"
    )
    source_type: Literal[
        "book",
        "journal",
        "website",
        "database",
        "conference",
        "thesis",
        "report",
        "unknown",
    ] = Field(..., description="Type of citation source")
    title: str = Field(
        ..., min_length=1, max_length=500, description="Title of the source"
    )
    author: Optional[str] = Field(
        default=None, max_length=200, description="Author(s) of the source"
    )
    publication_date: Optional[str] = Field(
        default=None, max_length=50, description="Publication date"
    )
    publisher: Optional[str] = Field(
        default=None, max_length=200, description="Publisher information"
    )
    page_number: Optional[int] = Field(
        default=None, ge=1, le=10000, description="Page number where formula appears"
    )
    url: Optional[str] = Field(
        default=None, max_length=500, description="URL for web sources"
    )
    doi: Optional[str] = Field(
        default=None, max_length=100, description="Digital Object Identifier"
    )
    isbn: Optional[str] = Field(
        default=None, max_length=20, description="ISBN for books"
    )
    volume: Optional[str] = Field(
        default=None, max_length=50, description="Volume number"
    )
    issue: Optional[str] = Field(
        default=None, max_length=50, description="Issue number"
    )
    chapter: Optional[str] = Field(
        default=None, max_length=100, description="Chapter title or number"
    )
    section: Optional[str] = Field(
        default=None, max_length=100, description="Section title or number"
    )
    reliability_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Reliability score for the citation (0.0-1.0)",
    )

    @field_validator("formula_id")
    def validate_formula_id(cls, v):
        """Validate formula ID"""
        if not v.strip():
            raise ValueError("Formula ID cannot be empty")
        return v.strip()

    @field_validator("title")
    def validate_title(cls, v):
        """Validate title"""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class PageMappingParams(BaseModel):
    """Parameters for adding page mappings to formulas"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula"
    )
    book_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the book"
    )
    page_number: int = Field(
        ..., ge=1, le=10000, description="Page number where formula appears"
    )
    context_before: Optional[str] = Field(
        default=None, max_length=1000, description="Text context before the formula"
    )
    context_after: Optional[str] = Field(
        default=None, max_length=1000, description="Text context after the formula"
    )
    figure_references: Optional[List[str]] = Field(
        default=None, description="List of figure references"
    )
    table_references: Optional[List[str]] = Field(
        default=None, description="List of table references"
    )
    equation_number: Optional[str] = Field(
        default=None, max_length=50, description="Equation number in the book"
    )
    section_title: Optional[str] = Field(
        default=None, max_length=200, description="Title of the section"
    )
    chapter_title: Optional[str] = Field(
        default=None, max_length=200, description="Title of the chapter"
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the mapping (0.0-1.0)",
    )

    @field_validator("formula_id")
    def validate_formula_id(cls, v):
        """Validate formula ID"""
        if not v.strip():
            raise ValueError("Formula ID cannot be empty")
        return v.strip()

    @field_validator("book_id")
    def validate_book_id(cls, v):
        """Validate book ID"""
        if not v.strip():
            raise ValueError("Book ID cannot be empty")
        return v.strip()


class NBAConnectionParams(BaseModel):
    """Parameters for adding NBA API connections to formulas"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula"
    )
    nba_endpoint: str = Field(
        ..., min_length=1, max_length=200, description="NBA API endpoint"
    )
    data_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of NBA data"
    )
    season: Optional[str] = Field(default=None, max_length=20, description="NBA season")
    team_id: Optional[str] = Field(
        default=None, max_length=20, description="NBA team ID"
    )
    player_id: Optional[str] = Field(
        default=None, max_length=20, description="NBA player ID"
    )
    game_id: Optional[str] = Field(
        default=None, max_length=20, description="NBA game ID"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional API parameters"
    )
    sync_frequency: Literal["daily", "weekly", "monthly", "on_demand"] = Field(
        default="daily", description="How often to sync data"
    )

    @field_validator("formula_id")
    def validate_formula_id(cls, v):
        """Validate formula ID"""
        if not v.strip():
            raise ValueError("Formula ID cannot be empty")
        return v.strip()

    @field_validator("nba_endpoint")
    def validate_nba_endpoint(cls, v):
        """Validate NBA endpoint"""
        if not v.strip():
            raise ValueError("NBA endpoint cannot be empty")
        return v.strip()


class FormulaUsageParams(BaseModel):
    """Parameters for tracking formula usage"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula being used"
    )
    usage_type: Literal[
        "calculation",
        "analysis",
        "research",
        "education",
        "comparison",
        "validation",
        "unknown",
    ] = Field(..., description="Type of usage")
    user_id: Optional[str] = Field(
        default=None, max_length=100, description="ID of the user"
    )
    session_id: Optional[str] = Field(
        default=None, max_length=100, description="Session ID"
    )
    input_parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Parameters used in calculation"
    )
    calculation_result: Optional[Any] = Field(
        default=None, description="Result of the calculation"
    )
    execution_time_ms: Optional[int] = Field(
        default=None, ge=0, le=300000, description="Execution time in milliseconds"
    )
    success: bool = Field(
        default=True, description="Whether the calculation was successful"
    )
    error_message: Optional[str] = Field(
        default=None, max_length=1000, description="Error message if failed"
    )
    ip_address: Optional[str] = Field(
        default=None, max_length=45, description="IP address of the user"
    )
    user_agent: Optional[str] = Field(
        default=None, max_length=500, description="User agent string"
    )

    @field_validator("formula_id")
    def validate_formula_id(cls, v):
        """Validate formula ID"""
        if not v.strip():
            raise ValueError("Formula ID cannot be empty")
        return v.strip()


class CrossReferenceSearchParams(BaseModel):
    """Parameters for searching formulas by cross-references"""

    search_query: str = Field(
        ..., min_length=1, max_length=200, description="Search query"
    )
    search_type: Literal["all", "citations", "pages", "nba", "usage"] = Field(
        default="all", description="Type of search to perform"
    )
    max_results: int = Field(
        default=50, ge=1, le=200, description="Maximum number of results to return"
    )

    @field_validator("search_query")
    def validate_search_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()


class NBAConnectionSyncParams(BaseModel):
    """Parameters for syncing NBA data"""

    connection_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID of the NBA connection to sync",
    )

    @field_validator("connection_id")
    def validate_connection_id(cls, v):
        """Validate connection ID"""
        if not v.strip():
            raise ValueError("Connection ID cannot be empty")
        return v.strip()


class FormulaReferenceParams(BaseModel):
    """Parameters for getting formula cross-references"""

    formula_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID of the formula to get references for",
    )

    @field_validator("formula_id")
    def validate_formula_id(cls, v):
        """Validate formula ID"""
        if not v.strip():
            raise ValueError("Formula ID cannot be empty")
        return v.strip()


# ============================================================================
# Phase 7.1: Intelligent Formula Recommendations Parameters
# ============================================================================


class IntelligentRecommendationParams(BaseModel):
    """Parameters for intelligent formula recommendations"""

    context: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Context description for formula recommendations",
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="User preferences and settings"
    )
    current_formulas: Optional[List[str]] = Field(
        default=None, description="List of formulas currently being used"
    )
    analysis_type: Literal[
        "efficiency", "shooting", "defensive", "team", "player", "advanced", "all"
    ] = Field(default="all", description="Type of analysis being performed")
    max_recommendations: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of recommendations to return",
    )
    include_explanations: bool = Field(
        default=True, description="Whether to include explanations for recommendations"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for recommendations",
    )

    @field_validator("context")
    def validate_context(cls, v):
        """Validate context description"""
        if not v.strip():
            raise ValueError("Context cannot be empty")
        return v.strip()


class FormulaSuggestionParams(BaseModel):
    """Parameters for formula suggestions based on data patterns"""

    data_description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Description of the data being analyzed",
    )
    available_variables: List[str] = Field(
        ...,
        min_length=1,
        description="List of available variables for formula construction",
    )
    target_metric: Optional[str] = Field(
        default=None, max_length=100, description="Target metric or outcome to predict"
    )
    formula_complexity: Literal["simple", "moderate", "complex", "any"] = Field(
        default="any", description="Desired complexity level of suggested formulas"
    )
    include_interactions: bool = Field(
        default=True, description="Whether to include interaction terms in suggestions"
    )
    max_suggestions: int = Field(
        default=3, ge=1, le=10, description="Maximum number of formula suggestions"
    )

    @field_validator("data_description")
    def validate_data_description(cls, v):
        """Validate data description"""
        if not v.strip():
            raise ValueError("Data description cannot be empty")
        return v.strip()

    @field_validator("available_variables")
    def validate_available_variables(cls, v):
        """Validate available variables"""
        if not v:
            raise ValueError("At least one variable must be provided")

        # Check for valid variable names
        for var in v:
            if not var.strip():
                raise ValueError("Variable names cannot be empty")
            if not var.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid variable name: {var}")

        return [var.strip() for var in v]


class ContextAnalysisParams(BaseModel):
    """Parameters for analyzing user context for better recommendations"""

    user_query: str = Field(
        ..., min_length=1, max_length=1000, description="User query or request"
    )
    session_history: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Previous session history for context"
    )
    current_analysis: Optional[str] = Field(
        default=None, max_length=500, description="Current analysis being performed"
    )
    user_expertise_level: Literal["beginner", "intermediate", "advanced", "expert"] = (
        Field(
            default="intermediate",
            description="User's expertise level in sports analytics",
        )
    )
    preferred_formula_types: Optional[List[str]] = Field(
        default=None, description="User's preferred formula types"
    )
    analysis_depth: Literal["basic", "detailed", "comprehensive"] = Field(
        default="detailed", description="Desired depth of analysis"
    )

    @field_validator("user_query")
    def validate_user_query(cls, v):
        """Validate user query"""
        if not v.strip():
            raise ValueError("User query cannot be empty")
        return v.strip()


class PredictiveAnalysisParams(BaseModel):
    """Parameters for predictive analytics recommendations"""

    prediction_target: str = Field(
        ..., min_length=1, max_length=200, description="Target variable for prediction"
    )
    historical_data_description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Description of available historical data",
    )
    prediction_horizon: Literal["short_term", "medium_term", "long_term"] = Field(
        default="medium_term", description="Time horizon for predictions"
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.5,
        le=0.99,
        description="Desired confidence level for predictions",
    )
    include_uncertainty: bool = Field(
        default=True, description="Whether to include uncertainty estimates"
    )
    model_complexity: Literal["simple", "moderate", "complex"] = Field(
        default="moderate", description="Desired model complexity"
    )

    @field_validator("prediction_target")
    def validate_prediction_target(cls, v):
        """Validate prediction target"""
        if not v.strip():
            raise ValueError("Prediction target cannot be empty")
        return v.strip()

    @field_validator("historical_data_description")
    def validate_historical_data_description(cls, v):
        """Validate historical data description"""
        if not v.strip():
            raise ValueError("Historical data description cannot be empty")
        return v.strip()


class ErrorCorrectionParams(BaseModel):
    """Parameters for intelligent error correction"""

    formula_expression: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Formula expression to analyze for errors",
    )
    expected_result: Optional[float] = Field(
        default=None, description="Expected result if known"
    )
    input_values: Optional[Dict[str, float]] = Field(
        default=None, description="Input values for testing the formula"
    )
    error_tolerance: float = Field(
        default=0.01, ge=0.0, le=1.0, description="Tolerance for error detection"
    )
    correction_suggestions: bool = Field(
        default=True, description="Whether to provide correction suggestions"
    )
    validation_level: Literal["basic", "comprehensive", "expert"] = Field(
        default="comprehensive", description="Level of validation to perform"
    )

    @field_validator("formula_expression")
    def validate_formula_expression(cls, v):
        """Validate formula expression"""
        if not v.strip():
            raise ValueError("Formula expression cannot be empty")
        return v.strip()


# ============================================================================
# Phase 7.2: Automated Formula Discovery Parameters
# ============================================================================


class FormulaDiscoveryParams(BaseModel):
    """Parameters for automated formula discovery from data patterns"""

    data_description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Description of the dataset being analyzed",
    )
    available_variables: List[str] = Field(
        ...,
        min_length=2,
        description="List of available variables for formula construction",
    )
    target_variable: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Target variable to predict or analyze",
    )
    discovery_method: Literal[
        "genetic", "symbolic_regression", "pattern_matching", "hybrid"
    ] = Field(default="hybrid", description="Method for formula discovery")
    complexity_limit: Literal["simple", "moderate", "complex", "unlimited"] = Field(
        default="moderate",
        description="Maximum complexity level for discovered formulas",
    )
    max_formulas: int = Field(
        default=5, ge=1, le=20, description="Maximum number of formulas to discover"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for discovered formulas",
    )
    include_interactions: bool = Field(
        default=True,
        description="Whether to include interaction terms in discovered formulas",
    )
    validation_method: Literal["cross_validation", "holdout", "bootstrap"] = Field(
        default="cross_validation",
        description="Method for validating discovered formulas",
    )

    @field_validator("data_description")
    def validate_data_description(cls, v):
        """Validate data description"""
        if not v.strip():
            raise ValueError("Data description cannot be empty")
        return v.strip()

    @field_validator("available_variables")
    def validate_available_variables(cls, v):
        """Validate available variables"""
        if len(v) < 2:
            raise ValueError(
                "At least 2 variables must be provided for formula discovery"
            )

        for var in v:
            if not var.strip():
                raise ValueError("Variable names cannot be empty")
            if not var.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid variable name: {var}")

        return [var.strip() for var in v]


class PatternAnalysisParams(BaseModel):
    """Parameters for pattern analysis in formula discovery"""

    data_patterns: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="List of data patterns to analyze"
    )
    pattern_types: List[
        Literal[
            "linear",
            "polynomial",
            "exponential",
            "logarithmic",
            "trigonometric",
            "custom",
        ]
    ] = Field(
        default=["linear", "polynomial"], description="Types of patterns to look for"
    )
    correlation_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum correlation threshold for pattern detection",
    )
    significance_level: float = Field(
        default=0.05,
        ge=0.01,
        le=0.1,
        description="Statistical significance level for pattern validation",
    )
    max_pattern_depth: int = Field(
        default=3, ge=1, le=5, description="Maximum depth for pattern analysis"
    )

    @field_validator("data_patterns")
    def validate_data_patterns(cls, v):
        """Validate data patterns"""
        if not v:
            raise ValueError("At least one data pattern must be provided")
        return v


class FormulaValidationParams(BaseModel):
    """Parameters for validating discovered formulas"""

    formula_expressions: List[str] = Field(
        ..., min_length=1, description="List of formula expressions to validate"
    )
    test_data: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Test data for formula validation"
    )
    validation_metrics: List[
        Literal["r_squared", "mae", "rmse", "mape", "correlation"]
    ] = Field(default=["r_squared", "mae"], description="Metrics to use for validation")
    cross_validation_folds: int = Field(
        default=5, ge=2, le=10, description="Number of folds for cross-validation"
    )
    minimum_performance: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum performance threshold for formula acceptance",
    )

    @field_validator("formula_expressions")
    def validate_formula_expressions(cls, v):
        """Validate formula expressions"""
        if not v:
            raise ValueError("At least one formula expression must be provided")

        for expr in v:
            if not expr.strip():
                raise ValueError("Formula expressions cannot be empty")

        return [expr.strip() for expr in v]


class FormulaOptimizationParams(BaseModel):
    """Parameters for optimizing discovered formulas"""

    base_formula: str = Field(
        ..., min_length=1, max_length=1000, description="Base formula to optimize"
    )
    optimization_objective: Literal[
        "accuracy", "simplicity", "robustness", "balanced"
    ] = Field(default="balanced", description="Objective for formula optimization")
    optimization_method: Literal[
        "genetic_algorithm", "gradient_descent", "simulated_annealing", "particle_swarm"
    ] = Field(
        default="genetic_algorithm", description="Method for formula optimization"
    )
    max_iterations: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Maximum number of optimization iterations",
    )
    population_size: int = Field(
        default=50, ge=10, le=200, description="Population size for genetic algorithm"
    )
    mutation_rate: float = Field(
        default=0.1, ge=0.01, le=0.5, description="Mutation rate for genetic algorithm"
    )
    crossover_rate: float = Field(
        default=0.8, ge=0.1, le=1.0, description="Crossover rate for genetic algorithm"
    )

    @field_validator("base_formula")
    def validate_base_formula(cls, v):
        """Validate base formula"""
        if not v.strip():
            raise ValueError("Base formula cannot be empty")
        return v.strip()


class FormulaRankingParams(BaseModel):
    """Parameters for ranking discovered formulas"""

    discovered_formulas: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="List of discovered formulas with metadata"
    )
    ranking_criteria: List[
        Literal["accuracy", "simplicity", "novelty", "interpretability", "robustness"]
    ] = Field(
        default=["accuracy", "simplicity"], description="Criteria for ranking formulas"
    )
    weights: Optional[Dict[str, float]] = Field(
        default=None, description="Weights for ranking criteria"
    )
    reference_formulas: Optional[List[str]] = Field(
        default=None, description="Reference formulas for novelty assessment"
    )
    domain_knowledge: Optional[Dict[str, Any]] = Field(
        default=None, description="Domain-specific knowledge for ranking"
    )

    @field_validator("discovered_formulas")
    def validate_discovered_formulas(cls, v):
        """Validate discovered formulas"""
        if not v:
            raise ValueError("At least one discovered formula must be provided")
        return v


# ============================================================================
# Phase 7.3: Smart Context Analysis Parameters
# ============================================================================


class ContextAnalysisParams(BaseModel):
    """Parameters for intelligent context analysis"""

    user_query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's query or request for analysis",
    )
    session_history: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Previous session interactions and context"
    )
    available_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Available data sources and variables"
    )
    analysis_goals: Optional[List[str]] = Field(
        default=None, description="User's stated or inferred analysis goals"
    )
    expertise_level: Literal["beginner", "intermediate", "advanced", "expert"] = Field(
        default="intermediate", description="User's expertise level in sports analytics"
    )
    preferred_formulas: Optional[List[str]] = Field(
        default=None, description="User's preferred or frequently used formulas"
    )
    context_depth: Literal["shallow", "moderate", "deep"] = Field(
        default="moderate", description="Depth of context analysis to perform"
    )
    include_recommendations: bool = Field(
        default=True, description="Whether to include formula recommendations"
    )
    include_explanations: bool = Field(
        default=True, description="Whether to include detailed explanations"
    )

    @field_validator("user_query")
    def validate_user_query(cls, v):
        """Validate user query"""
        if not v.strip():
            raise ValueError("User query cannot be empty")
        return v.strip()


class UserBehaviorAnalysisParams(BaseModel):
    """Parameters for analyzing user behavior patterns"""

    user_id: str = Field(
        ..., min_length=1, max_length=100, description="Unique identifier for the user"
    )
    time_period: Literal["session", "day", "week", "month", "year"] = Field(
        default="session", description="Time period for behavior analysis"
    )
    behavior_types: List[
        Literal["formula_usage", "query_patterns", "preferences", "errors", "successes"]
    ] = Field(
        default=["formula_usage", "query_patterns"],
        description="Types of behavior to analyze",
    )
    include_patterns: bool = Field(
        default=True, description="Whether to identify behavioral patterns"
    )
    include_predictions: bool = Field(
        default=True, description="Whether to predict future behavior"
    )
    privacy_level: Literal["basic", "detailed", "comprehensive"] = Field(
        default="basic", description="Level of detail in behavior analysis"
    )

    @field_validator("user_id")
    def validate_user_id(cls, v):
        """Validate user ID"""
        if not v.strip():
            raise ValueError("User ID cannot be empty")
        return v.strip()


class ContextualRecommendationParams(BaseModel):
    """Parameters for contextual formula recommendations"""

    context_analysis: Dict[str, Any] = Field(
        ..., description="Results from context analysis"
    )
    recommendation_count: int = Field(
        default=5, ge=1, le=20, description="Number of recommendations to generate"
    )
    recommendation_types: List[
        Literal["formula", "workflow", "insight", "optimization"]
    ] = Field(default=["formula"], description="Types of recommendations to include")
    personalization_level: Literal["none", "basic", "advanced", "full"] = Field(
        default="basic", description="Level of personalization to apply"
    )
    include_alternatives: bool = Field(
        default=True, description="Whether to include alternative recommendations"
    )
    explanation_depth: Literal["brief", "detailed", "comprehensive"] = Field(
        default="detailed", description="Depth of explanations for recommendations"
    )
    confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for recommendations",
    )

    @field_validator("context_analysis")
    def validate_context_analysis(cls, v):
        """Validate context analysis"""
        if not v:
            raise ValueError("Context analysis cannot be empty")
        return v


class SessionContextParams(BaseModel):
    """Parameters for session context management"""

    session_id: str = Field(
        ..., min_length=1, max_length=100, description="Unique session identifier"
    )
    context_data: Dict[str, Any] = Field(
        ..., description="Session context data to store or retrieve"
    )
    context_type: Literal[
        "user_preferences", "analysis_state", "formula_history", "data_context"
    ] = Field(default="analysis_state", description="Type of context data")
    operation: Literal["store", "retrieve", "update", "clear"] = Field(
        default="store", description="Operation to perform on context data"
    )
    expiration_time: Optional[int] = Field(
        default=None, ge=60, le=86400, description="Context expiration time in seconds"
    )
    include_metadata: bool = Field(
        default=True, description="Whether to include metadata with context"
    )

    @field_validator("session_id")
    def validate_session_id(cls, v):
        """Validate session ID"""
        if not v.strip():
            raise ValueError("Session ID cannot be empty")
        return v.strip()


class IntelligentInsightParams(BaseModel):
    """Parameters for generating intelligent insights"""

    analysis_context: Dict[str, Any] = Field(
        ..., description="Context from analysis results"
    )
    insight_types: List[
        Literal[
            "pattern", "anomaly", "trend", "correlation", "prediction", "optimization"
        ]
    ] = Field(default=["pattern", "trend"], description="Types of insights to generate")
    insight_depth: Literal["surface", "moderate", "deep"] = Field(
        default="moderate", description="Depth of insight analysis"
    )
    include_visualizations: bool = Field(
        default=True, description="Whether to include visualization suggestions"
    )
    include_actionable_recommendations: bool = Field(
        default=True, description="Whether to include actionable recommendations"
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence for insights"
    )
    max_insights: int = Field(
        default=10, ge=1, le=50, description="Maximum number of insights to generate"
    )

    @field_validator("analysis_context")
    def validate_analysis_context(cls, v):
        """Validate analysis context"""
        if not v:
            raise ValueError("Analysis context cannot be empty")
        return v


# ============================================================================
# Phase 7.4: Predictive Analytics Engine Parameters
# ============================================================================


class PredictiveModelParams(BaseModel):
    """Parameters for predictive model training and evaluation"""

    model_type: Literal["regression", "classification", "time_series", "ensemble"] = (
        Field(default="regression", description="Type of predictive model to train")
    )
    target_variable: str = Field(
        ..., min_length=1, max_length=100, description="Target variable to predict"
    )
    feature_variables: List[str] = Field(
        ..., min_length=1, description="List of feature variables for prediction"
    )
    training_data: Dict[str, List[float]] = Field(
        ..., description="Training data with variable names as keys and values as lists"
    )
    test_data: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Test data for model evaluation"
    )
    validation_split: float = Field(
        default=0.2,
        ge=0.1,
        le=0.5,
        description="Fraction of data to use for validation",
    )
    model_parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Model-specific parameters"
    )
    cross_validation_folds: int = Field(
        default=5, ge=2, le=10, description="Number of folds for cross-validation"
    )
    performance_metrics: List[
        Literal["mse", "rmse", "mae", "r2", "accuracy", "precision", "recall", "f1"]
    ] = Field(default=["mse", "r2"], description="Performance metrics to calculate")

    @field_validator("target_variable")
    def validate_target_variable(cls, v):
        """Validate target variable"""
        if not v.strip():
            raise ValueError("Target variable cannot be empty")
        return v.strip()

    @field_validator("feature_variables")
    def validate_feature_variables(cls, v):
        """Validate feature variables"""
        if not v:
            raise ValueError("At least one feature variable must be provided")

        for var in v:
            if not var.strip():
                raise ValueError("Feature variable names cannot be empty")

        return [var.strip() for var in v]

    @field_validator("training_data")
    def validate_training_data(cls, v):
        """Validate training data"""
        if not v:
            raise ValueError("Training data cannot be empty")

        # Check that all values are lists of numbers
        for key, values in v.items():
            if not isinstance(values, list):
                raise ValueError(
                    f"Training data values must be lists, got {type(values)} for {key}"
                )
            if not values:
                raise ValueError(f"Training data list cannot be empty for {key}")
            if not all(isinstance(x, (int, float)) for x in values):
                raise ValueError(f"Training data must contain only numbers for {key}")

        return v


class PredictionParams(BaseModel):
    """Parameters for making predictions with trained models"""

    model_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identifier of the trained model to use",
    )
    input_features: Dict[str, float] = Field(
        ..., description="Input feature values for prediction"
    )
    prediction_type: Literal["single", "batch", "probability"] = Field(
        default="single", description="Type of prediction to make"
    )
    confidence_interval: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence interval for prediction (e.g., 0.95 for 95%)",
    )
    include_feature_importance: bool = Field(
        default=False, description="Whether to include feature importance in results"
    )
    include_prediction_explanation: bool = Field(
        default=False, description="Whether to include explanation of the prediction"
    )

    @field_validator("model_id")
    def validate_model_id(cls, v):
        """Validate model ID"""
        if not v.strip():
            raise ValueError("Model ID cannot be empty")
        return v.strip()

    @field_validator("input_features")
    def validate_input_features(cls, v):
        """Validate input features"""
        if not v:
            raise ValueError("Input features cannot be empty")

        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(
                    f"Feature value must be a number, got {type(value)} for {key}"
                )

        return v


class ModelEvaluationParams(BaseModel):
    """Parameters for model evaluation and validation"""

    model_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identifier of the model to evaluate",
    )
    evaluation_data: Dict[str, List[float]] = Field(
        ..., description="Data to use for evaluation"
    )
    evaluation_metrics: List[
        Literal[
            "mse", "rmse", "mae", "r2", "accuracy", "precision", "recall", "f1", "auc"
        ]
    ] = Field(
        default=["mse", "r2"], description="Metrics to calculate during evaluation"
    )
    include_cross_validation: bool = Field(
        default=True, description="Whether to perform cross-validation"
    )
    include_feature_importance: bool = Field(
        default=True, description="Whether to calculate feature importance"
    )
    include_residual_analysis: bool = Field(
        default=False, description="Whether to perform residual analysis"
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.8,
        le=0.99,
        description="Confidence level for statistical tests",
    )

    @field_validator("model_id")
    def validate_model_id(cls, v):
        """Validate model ID"""
        if not v.strip():
            raise ValueError("Model ID cannot be empty")
        return v.strip()


class TimeSeriesPredictionParams(BaseModel):
    """Parameters for time series prediction models"""

    time_series_data: Dict[str, List[float]] = Field(
        ..., description="Time series data with timestamps and values"
    )
    target_variable: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Target variable for time series prediction",
    )
    prediction_horizon: int = Field(
        default=5, ge=1, le=100, description="Number of time steps to predict ahead"
    )
    model_type: Literal["arima", "exponential_smoothing", "lstm", "prophet"] = Field(
        default="arima", description="Type of time series model to use"
    )
    seasonal_period: Optional[int] = Field(
        default=None, ge=2, le=365, description="Seasonal period for seasonal models"
    )
    trend_type: Literal["linear", "exponential", "logistic", "none"] = Field(
        default="linear", description="Type of trend to model"
    )
    include_confidence_intervals: bool = Field(
        default=True, description="Whether to include confidence intervals"
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.8,
        le=0.99,
        description="Confidence level for prediction intervals",
    )

    @field_validator("target_variable")
    def validate_target_variable(cls, v):
        """Validate target variable"""
        if not v.strip():
            raise ValueError("Target variable cannot be empty")
        return v.strip()


class EnsembleModelParams(BaseModel):
    """Parameters for ensemble model creation"""

    base_models: List[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="List of base model IDs to combine",
    )
    ensemble_method: Literal["voting", "bagging", "boosting", "stacking"] = Field(
        default="voting", description="Method for combining base models"
    )
    voting_type: Literal["hard", "soft"] = Field(
        default="hard", description="Type of voting for voting ensemble"
    )
    weights: Optional[List[float]] = Field(
        default=None, description="Weights for weighted voting (must sum to 1.0)"
    )
    meta_model_type: Optional[Literal["linear", "tree", "neural"]] = Field(
        default=None, description="Meta model type for stacking ensemble"
    )
    cross_validation_folds: int = Field(
        default=5, ge=2, le=10, description="Number of folds for meta model training"
    )
    include_model_performance: bool = Field(
        default=True, description="Whether to include individual model performance"
    )

    @field_validator("base_models")
    def validate_base_models(cls, v):
        """Validate base models"""
        if len(v) < 2:
            raise ValueError("At least 2 base models must be provided")

        for model_id in v:
            if not model_id.strip():
                raise ValueError("Model ID cannot be empty")

        return [model_id.strip() for model_id in v]

    @field_validator("weights")
    def validate_weights(cls, v):
        """Validate weights"""
        if v is not None:
            if not all(w >= 0 for w in v):
                raise ValueError("All weights must be non-negative")
            if abs(sum(v) - 1.0) > 1e-6:
                raise ValueError("Weights must sum to 1.0")
        return v


class ModelOptimizationParams(BaseModel):
    """Parameters for model hyperparameter optimization"""

    model_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identifier of the model to optimize",
    )
    optimization_method: Literal[
        "grid_search", "random_search", "bayesian", "genetic"
    ] = Field(
        default="grid_search", description="Method for hyperparameter optimization"
    )
    parameter_grid: Dict[str, List[Any]] = Field(
        ..., description="Parameter grid for optimization"
    )
    optimization_metric: str = Field(default="r2", description="Metric to optimize")
    max_iterations: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Maximum number of optimization iterations",
    )
    cv_folds: int = Field(
        default=5, ge=2, le=10, description="Number of cross-validation folds"
    )
    n_jobs: int = Field(
        default=1, ge=1, le=16, description="Number of parallel jobs for optimization"
    )
    random_seed: Optional[int] = Field(
        default=None, description="Random seed for reproducible optimization"
    )

    @field_validator("model_id")
    def validate_model_id(cls, v):
        """Validate model ID"""
        if not v.strip():
            raise ValueError("Model ID cannot be empty")
        return v.strip()

        @field_validator("parameter_grid")
        def validate_parameter_grid(cls, v):
            """Validate parameter grid"""
            if not v:
                raise ValueError("Parameter grid cannot be empty")
            return v


# ============================================================================
# Phase 7.6: Intelligent Error Correction Parameters
# ============================================================================


class ErrorDetectionParams(BaseModel):
    """Parameters for intelligent error detection in formulas and analysis"""

    input_formula: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Formula or expression to analyze for errors",
    )
    context_type: Literal["formula", "calculation", "analysis", "comparison"] = Field(
        default="formula", description="Type of context for error detection"
    )
    error_types: List[
        Literal["syntax", "semantic", "logical", "mathematical", "domain", "unit"]
    ] = Field(
        default=["syntax", "semantic", "logical"],
        description="Types of errors to detect",
    )
    include_suggestions: bool = Field(
        default=True, description="Whether to include correction suggestions"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for error detection",
    )
    domain_context: Optional[str] = Field(
        default=None,
        description="Domain context (e.g., 'basketball', 'statistics') for domain-specific error detection",
    )

    @field_validator("input_formula")
    def validate_input_formula(cls, v):
        """Validate input formula"""
        if not v.strip():
            raise ValueError("Input formula cannot be empty")
        return v.strip()


class ErrorCorrectionParams(BaseModel):
    """Parameters for intelligent error correction"""

    detected_errors: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="List of detected errors to correct"
    )
    correction_strategy: Literal["automatic", "suggested", "interactive"] = Field(
        default="suggested", description="Strategy for error correction"
    )
    preserve_intent: bool = Field(
        default=True,
        description="Whether to preserve the original intent of the formula",
    )
    validation_level: Literal["basic", "comprehensive", "strict"] = Field(
        default="comprehensive",
        description="Level of validation for corrected formulas",
    )
    include_explanations: bool = Field(
        default=True, description="Whether to include explanations for corrections"
    )
    max_corrections: int = Field(
        default=5, ge=1, le=20, description="Maximum number of corrections to attempt"
    )

    @field_validator("detected_errors")
    def validate_detected_errors(cls, v):
        """Validate detected errors"""
        if not v:
            raise ValueError("At least one error must be provided for correction")
        return v


class FormulaValidationParams(BaseModel):
    """Parameters for comprehensive formula validation"""

    formula_expression: str = Field(
        ..., min_length=1, max_length=1000, description="Formula expression to validate"
    )
    validation_types: List[
        Literal["syntax", "semantics", "mathematics", "domain", "units", "bounds"]
    ] = Field(
        default=["syntax", "semantics", "mathematics"],
        description="Types of validation to perform",
    )
    test_data: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Test data for validation"
    )
    expected_range: Optional[Dict[str, Tuple[float, float]]] = Field(
        default=None, description="Expected value ranges for validation"
    )
    domain_constraints: Optional[Dict[str, Any]] = Field(
        default=None, description="Domain-specific constraints for validation"
    )
    include_performance_analysis: bool = Field(
        default=False, description="Whether to include performance analysis"
    )

    @field_validator("formula_expression")
    def validate_formula_expression(cls, v):
        """Validate formula expression"""
        if not v.strip():
            raise ValueError("Formula expression cannot be empty")
        return v.strip()


class IntelligentSuggestionParams(BaseModel):
    """Parameters for intelligent correction suggestions"""

    error_context: Dict[str, Any] = Field(
        ..., description="Context information about the error"
    )
    user_intent: Optional[str] = Field(
        default=None, description="User's intended purpose or goal"
    )
    similar_formulas: Optional[List[str]] = Field(
        default=None, description="Similar formulas for context"
    )
    correction_history: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="History of previous corrections"
    )
    suggestion_count: int = Field(
        default=3, ge=1, le=10, description="Number of suggestions to generate"
    )
    include_alternatives: bool = Field(
        default=True, description="Whether to include alternative approaches"
    )

    @field_validator("error_context")
    def validate_error_context(cls, v):
        """Validate error context"""
        if not v:
            raise ValueError("Error context cannot be empty")
        return v


class ErrorAnalysisParams(BaseModel):
    """Parameters for comprehensive error analysis"""

    analysis_input: Union[str, Dict[str, Any]] = Field(
        ..., description="Input to analyze (formula string or analysis data)"
    )
    analysis_depth: Literal["surface", "deep", "comprehensive"] = Field(
        default="deep", description="Depth of error analysis"
    )
    include_pattern_analysis: bool = Field(
        default=True, description="Whether to include pattern-based error analysis"
    )
    include_statistical_analysis: bool = Field(
        default=True, description="Whether to include statistical error analysis"
    )
    include_context_analysis: bool = Field(
        default=True, description="Whether to include contextual error analysis"
    )
    generate_report: bool = Field(
        default=False,
        description="Whether to generate a detailed error analysis report",
    )

    @field_validator("analysis_input")
    def validate_analysis_input(cls, v):
        """Validate analysis input"""
        if isinstance(v, str) and not v.strip():
            raise ValueError("Analysis input cannot be empty")
        elif isinstance(v, dict) and not v:
            raise ValueError("Analysis input dictionary cannot be empty")
        return v


class ErrorLearningParams(BaseModel):
    """Parameters for error learning and improvement"""

    error_cases: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="List of error cases for learning"
    )
    learning_type: Literal["supervised", "unsupervised", "reinforcement"] = Field(
        default="supervised", description="Type of learning to perform"
    )
    update_model: bool = Field(
        default=True, description="Whether to update the error detection model"
    )
    validation_split: float = Field(
        default=0.2,
        ge=0.1,
        le=0.5,
        description="Fraction of data to use for validation",
    )
    learning_rate: float = Field(
        default=0.01, ge=0.001, le=0.1, description="Learning rate for model updates"
    )
    epochs: int = Field(
        default=10, ge=1, le=100, description="Number of training epochs"
    )

    @field_validator("error_cases")
    def validate_error_cases(cls, v):
        """Validate error cases"""
        if not v:
            raise ValueError("At least one error case must be provided")
        return v


# ============================================================================
# Phase 7.5: Automated Report Generation Parameters
# ============================================================================


class ReportGenerationParams(BaseModel):
    """Parameters for automated report generation"""

    report_type: Literal[
        "player_analysis",
        "team_analysis",
        "game_analysis",
        "season_summary",
        "formula_comparison",
        "predictive_analysis",
        "custom",
    ] = Field(default="player_analysis", description="Type of report to generate")
    data_source: Dict[str, Any] = Field(
        ..., description="Data source for the report (player stats, team data, etc.)"
    )
    analysis_focus: List[str] = Field(
        default=["performance", "efficiency", "trends"],
        description="Focus areas for analysis",
    )
    report_template: Optional[str] = Field(
        default=None, description="Custom report template to use"
    )
    include_visualizations: bool = Field(
        default=True, description="Whether to include charts and visualizations"
    )
    include_predictions: bool = Field(
        default=False, description="Whether to include predictive analytics"
    )
    include_comparisons: bool = Field(
        default=True, description="Whether to include comparative analysis"
    )
    output_format: Literal["html", "pdf", "json", "markdown"] = Field(
        default="html", description="Output format for the report"
    )
    customization_options: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional customization options"
    )

    @field_validator("data_source")
    def validate_data_source(cls, v):
        """Validate data source"""
        if not v:
            raise ValueError("Data source cannot be empty")
        return v

    @field_validator("analysis_focus")
    def validate_analysis_focus(cls, v):
        """Validate analysis focus areas"""
        valid_focuses = [
            "performance",
            "efficiency",
            "trends",
            "comparisons",
            "predictions",
            "insights",
        ]
        for focus in v:
            if focus not in valid_focuses:
                raise ValueError(
                    f"Invalid analysis focus: {focus}. Must be one of {valid_focuses}"
                )
        return v


class ReportInsightParams(BaseModel):
    """Parameters for generating insights from analysis data"""

    analysis_data: Dict[str, Any] = Field(
        ..., description="Analysis data to extract insights from"
    )
    insight_types: List[
        Literal[
            "performance",
            "trend",
            "anomaly",
            "comparison",
            "prediction",
            "recommendation",
        ]
    ] = Field(
        default=["performance", "trend", "comparison"],
        description="Types of insights to generate",
    )
    insight_depth: Literal["basic", "detailed", "comprehensive"] = Field(
        default="detailed", description="Depth of insight analysis"
    )
    include_statistical_significance: bool = Field(
        default=True, description="Whether to include statistical significance analysis"
    )
    confidence_threshold: float = Field(
        default=0.95, ge=0.8, le=0.99, description="Confidence threshold for insights"
    )
    max_insights: int = Field(
        default=10, ge=1, le=50, description="Maximum number of insights to generate"
    )

    @field_validator("analysis_data")
    def validate_analysis_data(cls, v):
        """Validate analysis data"""
        if not v:
            raise ValueError("Analysis data cannot be empty")
        return v


class ReportTemplateParams(BaseModel):
    """Parameters for report template management"""

    template_name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the report template"
    )
    template_type: Literal[
        "player", "team", "game", "season", "comparison", "custom"
    ] = Field(..., description="Type of template")
    template_content: Dict[str, Any] = Field(
        ..., description="Template content structure"
    )
    template_variables: List[str] = Field(
        default=[], description="Variables that can be substituted in the template"
    )
    template_styles: Optional[Dict[str, Any]] = Field(
        default=None, description="Styling options for the template"
    )
    is_public: bool = Field(
        default=False, description="Whether the template is publicly available"
    )

    @field_validator("template_name")
    def validate_template_name(cls, v):
        """Validate template name"""
        if not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.strip()

    @field_validator("template_content")
    def validate_template_content(cls, v):
        """Validate template content"""
        if not v:
            raise ValueError("Template content cannot be empty")
        return v


class ReportVisualizationParams(BaseModel):
    """Parameters for report visualization generation"""

    data_to_visualize: Dict[str, Any] = Field(
        ..., description="Data to create visualizations from"
    )
    visualization_types: List[
        Literal[
            "line_chart",
            "bar_chart",
            "scatter_plot",
            "heatmap",
            "pie_chart",
            "histogram",
            "box_plot",
        ]
    ] = Field(
        default=["line_chart", "bar_chart"],
        description="Types of visualizations to generate",
    )
    chart_style: Literal["professional", "modern", "minimal", "colorful"] = Field(
        default="professional", description="Style of the charts"
    )
    include_trend_lines: bool = Field(
        default=True, description="Whether to include trend lines in charts"
    )
    include_statistics: bool = Field(
        default=True, description="Whether to include statistical annotations"
    )
    output_resolution: Literal["low", "medium", "high", "ultra"] = Field(
        default="high", description="Resolution of generated charts"
    )
    color_scheme: Optional[str] = Field(
        default=None, description="Custom color scheme for charts"
    )

    @field_validator("data_to_visualize")
    def validate_data_to_visualize(cls, v):
        """Validate visualization data"""
        if not v:
            raise ValueError("Data to visualize cannot be empty")
        return v


class ReportExportParams(BaseModel):
    """Parameters for report export functionality"""

    report_content: Dict[str, Any] = Field(..., description="Report content to export")
    export_format: Literal["html", "pdf", "json", "markdown", "docx", "xlsx"] = Field(
        ..., description="Format to export the report in"
    )
    export_options: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional export options"
    )
    include_metadata: bool = Field(
        default=True, description="Whether to include report metadata"
    )
    compression_level: int = Field(
        default=6, ge=0, le=9, description="Compression level for exported files"
    )
    output_filename: Optional[str] = Field(
        default=None, description="Custom filename for the exported report"
    )

    @field_validator("report_content")
    def validate_report_content(cls, v):
        """Validate report content"""
        if not v:
            raise ValueError("Report content cannot be empty")
        return v

    @field_validator("output_filename")
    def validate_output_filename(cls, v):
        """Validate output filename"""
        if v is not None and not v.strip():
            raise ValueError("Output filename cannot be empty")
        return v.strip() if v else None


class ReportSchedulingParams(BaseModel):
    """Parameters for automated report scheduling"""

    schedule_name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the scheduled report"
    )
    report_config: Dict[str, Any] = Field(
        ..., description="Configuration for the report to be generated"
    )
    schedule_frequency: Literal["daily", "weekly", "monthly", "quarterly", "custom"] = (
        Field(..., description="Frequency of report generation")
    )
    schedule_time: Optional[str] = Field(
        default=None, description="Time of day to generate the report (HH:MM format)"
    )
    schedule_days: Optional[List[int]] = Field(
        default=None,
        ge=0,
        le=6,
        description="Days of the week to generate reports (0=Monday, 6=Sunday)",
    )
    recipients: List[str] = Field(
        default=[], description="List of email recipients for the report"
    )
    is_active: bool = Field(
        default=True, description="Whether the schedule is currently active"
    )

    @field_validator("schedule_name")
    def validate_schedule_name(cls, v):
        """Validate schedule name"""
        if not v.strip():
            raise ValueError("Schedule name cannot be empty")
        return v.strip()

    @field_validator("schedule_time")
    def validate_schedule_time(cls, v):
        """Validate schedule time format"""
        if v is not None:
            import re

            if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", v):
                raise ValueError("Schedule time must be in HH:MM format")
        return v


# ============================================================================
# Phase 8.1: Advanced Formula Intelligence Parameters
# ============================================================================


class FormulaDerivationParams(BaseModel):
    """Parameters for formula derivation and step-by-step breakdown"""

    formula_expression: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Formula expression to derive step-by-step",
    )
    derivation_depth: Literal["basic", "detailed", "comprehensive"] = Field(
        default="detailed", description="Depth of derivation explanation"
    )
    include_basketball_context: bool = Field(
        default=True, description="Whether to include basketball concept explanations"
    )
    show_mathematical_steps: bool = Field(
        default=True, description="Whether to show detailed mathematical steps"
    )
    include_visualization: bool = Field(
        default=False, description="Whether to include visual representation of steps"
    )
    target_audience: Literal["beginner", "intermediate", "advanced", "expert"] = Field(
        default="intermediate", description="Target audience for explanation complexity"
    )

    @field_validator("formula_expression")
    def validate_formula_expression(cls, v):
        """Validate formula expression"""
        if not v.strip():
            raise ValueError("Formula expression cannot be empty")
        return v.strip()


class FormulaUsageAnalyticsParams(BaseModel):
    """Parameters for formula usage analytics and pattern analysis"""

    analysis_period: Literal["hour", "day", "week", "month", "all"] = Field(
        default="week", description="Time period for usage analysis"
    )
    formula_categories: Optional[List[str]] = Field(
        default=None, description="Specific formula categories to analyze"
    )
    include_performance_metrics: bool = Field(
        default=True, description="Whether to include performance analysis"
    )
    include_user_patterns: bool = Field(
        default=True, description="Whether to include user behavior patterns"
    )
    generate_recommendations: bool = Field(
        default=True, description="Whether to generate usage recommendations"
    )
    export_format: Literal["json", "csv", "report"] = Field(
        default="json", description="Format for exporting analytics data"
    )


class FormulaOptimizationParams(BaseModel):
    """Parameters for formula optimization and performance analysis"""

    formula_expression: str = Field(
        ..., min_length=1, max_length=1000, description="Formula to optimize"
    )
    optimization_goals: List[Literal["speed", "accuracy", "simplicity", "memory"]] = (
        Field(
            default=["speed", "accuracy"],
            description="Optimization goals to prioritize",
        )
    )
    test_data_size: int = Field(
        default=1000,
        ge=100,
        le=100000,
        description="Size of test dataset for optimization",
    )
    include_alternatives: bool = Field(
        default=True, description="Whether to suggest alternative formulations"
    )
    benchmark_against_known: bool = Field(
        default=True, description="Whether to benchmark against known implementations"
    )
    optimization_level: Literal["basic", "aggressive", "comprehensive"] = Field(
        default="basic", description="Level of optimization to perform"
    )

    @field_validator("formula_expression")
    def validate_formula_expression(cls, v):
        """Validate formula expression"""
        if not v.strip():
            raise ValueError("Formula expression cannot be empty")
        return v.strip()


class FormulaInsightParams(BaseModel):
    """Parameters for generating formula insights and recommendations"""

    analysis_context: Dict[str, Any] = Field(
        ..., description="Context for insight generation"
    )
    insight_types: List[
        Literal["performance", "usage", "optimization", "educational", "comparison"]
    ] = Field(
        default=["performance", "usage"], description="Types of insights to generate"
    )
    include_predictions: bool = Field(
        default=False, description="Whether to include predictive insights"
    )
    include_historical_trends: bool = Field(
        default=True, description="Whether to include historical trend analysis"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for insights",
    )
    max_insights: int = Field(
        default=10, ge=1, le=50, description="Maximum number of insights to generate"
    )

    @field_validator("analysis_context")
    def validate_analysis_context(cls, v):
        """Validate analysis context"""
        if not v:
            raise ValueError("Analysis context cannot be empty")
        return v


class FormulaComparisonParams(BaseModel):
    """Parameters for comparing different formula implementations"""

    formulas_to_compare: List[str] = Field(
        ..., min_length=2, max_length=10, description="List of formulas to compare"
    )
    comparison_metrics: List[
        Literal["accuracy", "speed", "complexity", "readability", "memory"]
    ] = Field(
        default=["accuracy", "speed"], description="Metrics to use for comparison"
    )
    test_scenarios: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Specific test scenarios for comparison"
    )
    include_visualization: bool = Field(
        default=True, description="Whether to include comparison visualizations"
    )
    generate_ranking: bool = Field(
        default=True, description="Whether to generate formula rankings"
    )
    include_recommendations: bool = Field(
        default=True, description="Whether to include usage recommendations"
    )

    @field_validator("formulas_to_compare")
    def validate_formulas_to_compare(cls, v):
        """Validate formulas to compare"""
        if len(v) < 2:
            raise ValueError("At least 2 formulas must be provided for comparison")
        return v


class FormulaLearningParams(BaseModel):
    """Parameters for adaptive formula learning and improvement"""

    learning_data: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="Data for learning and improvement"
    )
    learning_objective: Literal[
        "accuracy", "performance", "user_satisfaction", "comprehensive"
    ] = Field(default="comprehensive", description="Primary learning objective")
    adaptation_rate: float = Field(
        default=0.1, ge=0.01, le=1.0, description="Rate of adaptation and learning"
    )
    include_validation: bool = Field(
        default=True, description="Whether to include validation in learning process"
    )
    update_frequency: Literal["immediate", "batch", "scheduled"] = Field(
        default="batch", description="Frequency of model updates"
    )
    learning_history_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Size of learning history to maintain",
    )

    @field_validator("learning_data")
    def validate_learning_data(cls, v):
        """Validate learning data"""
        if not v:
            raise ValueError("Learning data cannot be empty")
        return v


# ============================================================================
# Phase 9.1: Advanced Formula Intelligence Parameters
# ============================================================================


class FormulaIntelligenceAnalysisParams(BaseModel):
    """Parameters for AI-powered formula analysis"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula to analyze"
    )
    analysis_types: List[
        Literal[
            "performance",
            "complexity",
            "accuracy",
            "optimization",
            "pattern",
            "correlation",
            "prediction",
            "insight",
        ]
    ] = Field(
        default=["performance", "complexity", "accuracy"],
        description="Types of analysis to perform",
    )
    input_data: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Optional input data for analysis"
    )
    analysis_depth: Literal["basic", "detailed", "comprehensive"] = Field(
        default="comprehensive", description="Depth of analysis to perform"
    )
    include_optimization: bool = Field(
        default=True, description="Whether to include optimization analysis"
    )
    include_insights: bool = Field(
        default=True, description="Whether to include intelligent insights"
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for insights",
    )


class FormulaIntelligenceOptimizationParams(BaseModel):
    """Parameters for intelligent formula optimization"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula to optimize"
    )
    optimization_objectives: List[
        Literal[
            "accuracy",
            "speed",
            "simplicity",
            "robustness",
            "interpretability",
            "generalization",
        ]
    ] = Field(default=["accuracy", "speed"], description="Objectives for optimization")
    input_data: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Optional input data for optimization"
    )
    optimization_method: Literal[
        "genetic_algorithm", "gradient_descent", "simulated_annealing", "particle_swarm"
    ] = Field(default="genetic_algorithm", description="Method for optimization")
    max_iterations: int = Field(
        default=100, ge=10, le=1000, description="Maximum optimization iterations"
    )
    target_improvement: float = Field(
        default=0.1, ge=0.01, le=1.0, description="Target improvement percentage"
    )


class IntelligentInsightGenerationParams(BaseModel):
    """Parameters for generating intelligent insights"""

    analysis_context: Dict[str, Any] = Field(
        ..., description="Context from previous analyses"
    )
    insight_types: List[
        Literal[
            "performance_trend",
            "correlation_discovery",
            "anomaly_detection",
            "optimization_opportunity",
            "pattern_recognition",
            "predictive_insight",
            "formula_improvement",
        ]
    ] = Field(
        default=[
            "performance_trend",
            "correlation_discovery",
            "optimization_opportunity",
        ],
        description="Types of insights to generate",
    )
    data_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional data context"
    )
    insight_depth: Literal["basic", "detailed", "comprehensive"] = Field(
        default="comprehensive", description="Depth of insight generation"
    )
    max_insights: int = Field(
        default=10, ge=1, le=50, description="Maximum number of insights to generate"
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for insights",
    )


class FormulaPatternDiscoveryParams(BaseModel):
    """Parameters for discovering patterns across formulas"""

    formula_ids: List[str] = Field(
        ..., min_length=2, max_length=20, description="List of formula IDs to analyze"
    )
    pattern_types: List[
        Literal[
            "linear",
            "polynomial",
            "exponential",
            "logarithmic",
            "periodic",
            "trend",
            "correlation",
        ]
    ] = Field(
        default=["linear", "polynomial", "correlation"],
        description="Types of patterns to look for",
    )
    analysis_depth: Literal["basic", "detailed", "comprehensive"] = Field(
        default="comprehensive", description="Depth of pattern analysis"
    )
    include_correlations: bool = Field(
        default=True, description="Whether to include correlation analysis"
    )
    include_optimizations: bool = Field(
        default=True, description="Whether to include optimization analysis"
    )


class FormulaPerformanceAnalysisParams(BaseModel):
    """Parameters for formula performance analysis"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula to analyze"
    )
    performance_metrics: List[
        Literal["accuracy", "speed", "memory", "scalability", "robustness"]
    ] = Field(
        default=["accuracy", "speed"], description="Performance metrics to analyze"
    )
    test_data: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Test data for performance analysis"
    )
    benchmark_formulas: Optional[List[str]] = Field(
        default=None, description="Formulas to benchmark against"
    )
    include_comparison: bool = Field(
        default=True, description="Whether to include comparison analysis"
    )


class FormulaComplexityAnalysisParams(BaseModel):
    """Parameters for formula complexity analysis"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula to analyze"
    )
    complexity_metrics: List[
        Literal["cyclomatic", "cognitive", "halstead", "maintainability", "readability"]
    ] = Field(
        default=["cyclomatic", "cognitive", "maintainability"],
        description="Complexity metrics to calculate",
    )
    include_recommendations: bool = Field(
        default=True,
        description="Whether to include complexity reduction recommendations",
    )
    target_complexity_level: Literal[
        "simple", "moderate", "complex", "very_complex"
    ] = Field(
        default="moderate", description="Target complexity level for recommendations"
    )


class UsageTrackingParams(BaseModel):
    """Parameters for tracking formula usage patterns"""

    tracking_period: Literal["hour", "day", "week", "month", "year", "all"] = Field(
        default="week", description="Time period for usage tracking"
    )
    formula_categories: Optional[List[str]] = Field(
        default=None, description="Specific formula categories to track"
    )
    user_segments: Optional[List[str]] = Field(
        default=None,
        description="User segments to analyze (e.g., 'beginner', 'expert')",
    )
    include_performance_metrics: bool = Field(
        default=True, description="Whether to include performance tracking"
    )
    include_user_behavior: bool = Field(
        default=True, description="Whether to include user behavior analysis"
    )
    real_time_tracking: bool = Field(
        default=False, description="Whether to enable real-time tracking"
    )


class UsageInsightParams(BaseModel):
    """Parameters for generating usage insights"""

    insight_categories: List[
        Literal["frequency", "performance", "trends", "patterns", "recommendations"]
    ] = Field(
        default=["frequency", "performance", "trends"],
        description="Categories of insights to generate",
    )
    analysis_depth: Literal["surface", "deep", "comprehensive"] = Field(
        default="deep", description="Depth of analysis to perform"
    )
    include_predictions: bool = Field(
        default=True, description="Whether to include predictive insights"
    )
    include_comparisons: bool = Field(
        default=True, description="Whether to include comparative analysis"
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for insights",
    )
    max_insights: int = Field(
        default=15, ge=1, le=100, description="Maximum number of insights to generate"
    )


class UsageOptimizationParams(BaseModel):
    """Parameters for usage-based optimization"""

    optimization_focus: List[
        Literal["performance", "usability", "efficiency", "user_satisfaction"]
    ] = Field(
        default=["performance", "usability"], description="Focus areas for optimization"
    )
    target_metrics: Optional[List[str]] = Field(
        default=None, description="Specific metrics to optimize"
    )
    optimization_method: Literal["automatic", "guided", "custom"] = Field(
        default="guided", description="Method for optimization"
    )
    include_ab_testing: bool = Field(
        default=False, description="Whether to include A/B testing recommendations"
    )
    optimization_scope: Literal["formula", "interface", "workflow", "all"] = Field(
        default="formula", description="Scope of optimization"
    )


class UsageReportingParams(BaseModel):
    """Parameters for generating usage reports"""

    report_type: Literal["summary", "detailed", "executive", "technical", "custom"] = (
        Field(default="summary", description="Type of report to generate")
    )
    report_period: Literal["daily", "weekly", "monthly", "quarterly", "yearly"] = Field(
        default="weekly", description="Period covered by the report"
    )
    include_visualizations: bool = Field(
        default=True, description="Whether to include charts and graphs"
    )
    include_recommendations: bool = Field(
        default=True, description="Whether to include actionable recommendations"
    )
    include_benchmarks: bool = Field(
        default=True, description="Whether to include performance benchmarks"
    )
    export_format: Literal["html", "pdf", "json", "csv", "excel"] = Field(
        default="html", description="Format for exporting the report"
    )


class UsageAlertParams(BaseModel):
    """Parameters for setting up usage alerts"""

    alert_conditions: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="Conditions that trigger alerts"
    )
    alert_types: List[Literal["email", "webhook", "dashboard", "sms"]] = Field(
        default=["email"], description="Types of alerts to send"
    )
    alert_frequency: Literal["immediate", "hourly", "daily", "weekly"] = Field(
        default="immediate", description="Frequency of alert checks"
    )
    alert_thresholds: Optional[Dict[str, float]] = Field(
        default=None, description="Threshold values for alert conditions"
    )
    include_context: bool = Field(
        default=True, description="Whether to include contextual information in alerts"
    )

    @field_validator("alert_conditions")
    def validate_alert_conditions(cls, v):
        """Validate alert conditions"""
        if not v:
            raise ValueError("At least one alert condition must be provided")
        return v


class UsageDashboardParams(BaseModel):
    """Parameters for creating usage dashboards"""

    dashboard_type: Literal["overview", "detailed", "real_time", "custom"] = Field(
        default="overview", description="Type of dashboard to create"
    )
    dashboard_sections: List[
        Literal["usage_stats", "performance", "trends", "recommendations", "alerts"]
    ] = Field(
        default=["usage_stats", "performance", "trends"],
        description="Sections to include in the dashboard",
    )
    refresh_interval: int = Field(
        default=300, ge=60, le=3600, description="Dashboard refresh interval in seconds"
    )
    include_filters: bool = Field(
        default=True, description="Whether to include filtering options"
    )
    include_exports: bool = Field(
        default=True, description="Whether to include export functionality"
    )
    customization_options: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional customization options"
    )


# ============================================================================
# Phase 9.2: Multi-Modal Formula Processing Parameters
# ============================================================================


class TextFormulaProcessingParams(BaseModel):
    """Parameters for text-based formula processing"""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Input text containing formula descriptions",
    )
    context: Optional[str] = Field(
        default=None,
        max_length=100,
        description='Optional context (e.g., "basketball", "statistics")',
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for extraction",
    )
    extraction_methods: List[Literal["direct", "pattern", "nlp", "context"]] = Field(
        default=["direct", "pattern", "context"],
        description="Methods to use for formula extraction",
    )
    include_validation: bool = Field(
        default=True, description="Whether to include formula validation"
    )


class ImageFormulaProcessingParams(BaseModel):
    """Parameters for image-based formula processing"""

    image_data: str = Field(
        ..., min_length=1, description="Image data (base64 string or file path)"
    )
    image_format: Literal["base64", "file_path", "url"] = Field(
        default="base64", description="Format of the image data"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for extraction",
    )
    preprocessing_options: List[
        Literal["grayscale", "threshold", "denoise", "enhance"]
    ] = Field(
        default=["grayscale", "threshold"], description="Image preprocessing options"
    )
    ocr_language: str = Field(
        default="eng", max_length=10, description="OCR language code"
    )
    include_text_extraction: bool = Field(
        default=True, description="Whether to include raw text extraction"
    )


class DataFormulaProcessingParams(BaseModel):
    """Parameters for data-driven formula generation"""

    data: Dict[str, List[float]] = Field(
        ...,
        min_length=2,
        description="Dictionary with variable names as keys and data lists as values",
    )
    target_variable: str = Field(
        ..., min_length=1, max_length=50, description="Name of the target variable"
    )
    method: Literal["regression", "correlation", "pattern", "symbolic_regression"] = (
        Field(default="regression", description="Method for formula generation")
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
    include_statistics: bool = Field(
        default=True, description="Whether to include statistical analysis"
    )
    max_complexity: int = Field(
        default=10, ge=1, le=50, description="Maximum formula complexity"
    )

    @field_validator("data")
    def validate_data(cls, v):
        """Validate data structure"""
        if not v:
            raise ValueError("Data dictionary cannot be empty")

        # Check that all values are lists of numbers
        for key, values in v.items():
            if not isinstance(values, list):
                raise ValueError(f'Data for "{key}" must be a list')
            if len(values) < 2:
                raise ValueError(f'Data for "{key}" must have at least 2 values')
            if not all(isinstance(x, (int, float)) for x in values):
                raise ValueError(f'All values for "{key}" must be numbers')

        return v


class CrossModalValidationParams(BaseModel):
    """Parameters for cross-modal formula validation"""

    formula_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the formula to validate"
    )
    validation_methods: List[
        Literal["syntax", "semantics", "mathematical", "domain", "consistency"]
    ] = Field(
        default=["syntax", "semantics", "mathematical"],
        description="Validation methods to use",
    )
    confidence_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
    include_recommendations: bool = Field(
        default=True, description="Whether to include improvement recommendations"
    )
    include_discrepancy_analysis: bool = Field(
        default=True, description="Whether to include discrepancy analysis"
    )
    validation_depth: Literal["basic", "detailed", "comprehensive"] = Field(
        default="comprehensive", description="Depth of validation to perform"
    )


class MultiModalCapabilitiesParams(BaseModel):
    """Parameters for getting multi-modal processing capabilities"""

    include_detailed_info: bool = Field(
        default=False, description="Whether to include detailed capability information"
    )
    check_dependencies: bool = Field(
        default=True, description="Whether to check for required dependencies"
    )
    include_performance_info: bool = Field(
        default=False, description="Whether to include performance information"
    )


# ============================================================================
# Phase 9.3: Advanced Visualization Engine Parameters
# ============================================================================


class FormulaVisualizationParams(BaseModel):
    """Parameters for formula visualization"""

    formula: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Mathematical formula string to visualize",
    )
    visualization_type: Literal[
        "formula_graph",
        "data_plot",
        "formula_relationship",
        "interactive_chart",
        "three_dimensional",
        "real_time",
        "static_chart",
    ] = Field(default="formula_graph", description="Type of visualization to create")
    chart_type: Literal[
        "line",
        "scatter",
        "bar",
        "histogram",
        "heatmap",
        "surface",
        "contour",
        "network",
        "tree",
        "sankey",
    ] = Field(default="line", description="Type of chart to create")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Visualization configuration options"
    )
    variables: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Variable values for plotting"
    )
    export_format: Literal["png", "jpg", "svg", "pdf", "html", "json", "base64"] = (
        Field(default="png", description="Export format for the visualization")
    )


class DataVisualizationParams(BaseModel):
    """Parameters for data visualization"""

    data: Dict[str, List[float]] = Field(
        ...,
        min_length=1,
        description="Data dictionary with variable names as keys and data lists as values",
    )
    visualization_type: Literal[
        "formula_graph",
        "data_plot",
        "formula_relationship",
        "interactive_chart",
        "three_dimensional",
        "real_time",
        "static_chart",
    ] = Field(default="data_plot", description="Type of visualization to create")
    chart_type: Literal[
        "line",
        "scatter",
        "bar",
        "histogram",
        "heatmap",
        "surface",
        "contour",
        "network",
        "tree",
        "sankey",
    ] = Field(default="line", description="Type of chart to create")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Visualization configuration options"
    )
    export_format: Literal["png", "jpg", "svg", "pdf", "html", "json", "base64"] = (
        Field(default="png", description="Export format for the visualization")
    )

    @field_validator("data")
    def validate_data(cls, v):
        """Validate data structure"""
        if not v:
            raise ValueError("Data dictionary cannot be empty")

        # Check that all values are lists of numbers
        for key, values in v.items():
            if not isinstance(values, list):
                raise ValueError(f"Data for '{key}' must be a list")
            if len(values) < 1:
                raise ValueError(f"Data for '{key}' must have at least 1 value")
            if not all(isinstance(x, (int, float)) for x in values):
                raise ValueError(f"All values for '{key}' must be numbers")

        return v


class InteractiveVisualizationParams(BaseModel):
    """Parameters for interactive visualization"""

    data: Dict[str, Any] = Field(..., description="Data for interactive visualization")
    visualization_type: Literal[
        "formula_graph",
        "data_plot",
        "formula_relationship",
        "interactive_chart",
        "three_dimensional",
        "real_time",
        "static_chart",
    ] = Field(
        default="interactive_chart", description="Type of visualization to create"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Visualization configuration options"
    )
    include_controls: bool = Field(
        default=True, description="Whether to include interactive controls"
    )
    auto_update: bool = Field(
        default=False, description="Whether to enable automatic updates"
    )


class FormulaRelationshipVisualizationParams(BaseModel):
    """Parameters for formula relationship visualization"""

    formulas: List[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of formula strings to visualize relationships between",
    )
    relationships: List[Tuple[str, str, str]] = Field(
        default=[], description="List of (formula1, formula2, relationship_type) tuples"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Visualization configuration options"
    )
    export_format: Literal["png", "jpg", "svg", "pdf", "html", "json", "base64"] = (
        Field(default="png", description="Export format for the visualization")
    )
    include_labels: bool = Field(
        default=True, description="Whether to include formula labels"
    )
    show_weights: bool = Field(
        default=False, description="Whether to show relationship weights"
    )


class VisualizationCapabilitiesParams(BaseModel):
    """Parameters for getting visualization capabilities"""

    include_detailed_info: bool = Field(
        default=False, description="Whether to include detailed capability information"
    )
    check_dependencies: bool = Field(
        default=True, description="Whether to check for required dependencies"
    )
    include_performance_info: bool = Field(
        default=False, description="Whether to include performance information"
    )
    test_visualizations: bool = Field(
        default=False, description="Whether to test visualization capabilities"
    )


# ============================================================================
# Phase 10.1: Production Deployment Pipeline Parameters
# ============================================================================


class DeploymentParams(BaseModel):
    """Parameters for application deployment"""

    environment: Literal["development", "staging", "production", "testing"] = Field(
        ..., description="Target environment for deployment"
    )
    version: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Version to deploy (e.g., 'v1.2.3', 'latest')",
    )
    strategy: Literal["blue_green", "rolling", "canary", "recreate"] = Field(
        default="rolling", description="Deployment strategy to use"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional deployment configuration options"
    )
    replicas: Optional[int] = Field(
        default=None, ge=1, le=100, description="Number of replicas to deploy"
    )
    cpu_limit: Optional[str] = Field(
        default=None, description="CPU limit per replica (e.g., '1000m', '2')"
    )
    memory_limit: Optional[str] = Field(
        default=None, description="Memory limit per replica (e.g., '1Gi', '2G')"
    )
    health_check_path: Optional[str] = Field(
        default="/health", description="Health check endpoint path"
    )
    rollback_enabled: bool = Field(
        default=True, description="Whether rollback is enabled for this deployment"
    )
    auto_rollback_on_failure: bool = Field(
        default=True, description="Whether to automatically rollback on failure"
    )


class RollbackParams(BaseModel):
    """Parameters for deployment rollback"""

    deployment_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID of the deployment to rollback",
    )
    target_version: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Specific version to rollback to (optional)",
    )
    force: bool = Field(
        default=False, description="Force rollback even if target version is older"
    )
    preserve_data: bool = Field(
        default=True, description="Whether to preserve data during rollback"
    )


class HealthCheckParams(BaseModel):
    """Parameters for health check"""

    endpoint: str = Field(..., min_length=1, description="Health check endpoint URL")
    timeout: int = Field(
        default=30, ge=1, le=300, description="Timeout in seconds for health check"
    )
    retries: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    interval: int = Field(
        default=10, ge=1, le=60, description="Interval between retries in seconds"
    )
    expected_status_code: int = Field(
        default=200, ge=100, le=599, description="Expected HTTP status code"
    )


class SecurityScanParams(BaseModel):
    """Parameters for security scan"""

    image_name: str = Field(..., min_length=1, description="Docker image name to scan")
    scan_type: Literal["vulnerability", "malware", "secrets", "compliance"] = Field(
        default="vulnerability", description="Type of security scan to perform"
    )
    severity_threshold: Literal["critical", "high", "medium", "low"] = Field(
        default="high", description="Minimum severity threshold for reporting"
    )
    fail_on_critical: bool = Field(
        default=True,
        description="Whether to fail deployment on critical vulnerabilities",
    )
    fail_on_high: bool = Field(
        default=False,
        description="Whether to fail deployment on high-severity vulnerabilities",
    )
    include_recommendations: bool = Field(
        default=True, description="Whether to include remediation recommendations"
    )


class PerformanceTestParams(BaseModel):
    """Parameters for performance test"""

    endpoint: str = Field(..., min_length=1, description="Endpoint URL to test")
    test_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Performance test configuration"
    )
    duration_seconds: int = Field(
        default=60, ge=10, le=3600, description="Test duration in seconds"
    )
    concurrent_users: int = Field(
        default=10, ge=1, le=1000, description="Number of concurrent users"
    )
    requests_per_second: int = Field(
        default=100, ge=1, le=10000, description="Target requests per second"
    )
    max_response_time_ms: int = Field(
        default=500,
        ge=100,
        le=10000,
        description="Maximum acceptable response time in milliseconds",
    )
    max_error_rate: float = Field(
        default=0.01,
        ge=0.0,
        le=1.0,
        description="Maximum acceptable error rate (0.0 to 1.0)",
    )


class DeploymentStatusParams(BaseModel):
    """Parameters for getting deployment status"""

    deployment_id: str = Field(
        ..., min_length=1, max_length=100, description="ID of the deployment to check"
    )
    include_logs: bool = Field(
        default=False, description="Whether to include deployment logs"
    )
    include_metrics: bool = Field(
        default=True, description="Whether to include performance metrics"
    )


class DeploymentListParams(BaseModel):
    """Parameters for listing deployments"""

    environment: Optional[
        Literal["development", "staging", "production", "testing"]
    ] = Field(default=None, description="Filter by environment")
    status: Optional[
        Literal[
            "pending", "in_progress", "success", "failed", "rolled_back", "cancelled"
        ]
    ] = Field(default=None, description="Filter by deployment status")
    limit: int = Field(
        default=50, ge=1, le=1000, description="Maximum number of deployments to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of deployments to skip")
    include_metadata: bool = Field(
        default=True, description="Whether to include deployment metadata"
    )


class DeploymentHistoryParams(BaseModel):
    """Parameters for getting deployment history"""

    environment: Optional[
        Literal["development", "staging", "production", "testing"]
    ] = Field(default=None, description="Filter by environment")
    days: int = Field(
        default=30, ge=1, le=365, description="Number of days to include in history"
    )
    include_rollbacks: bool = Field(
        default=True, description="Whether to include rollback operations"
    )
    include_failed: bool = Field(
        default=True, description="Whether to include failed deployments"
    )


# ============================================================================
# Phase 10.2: Performance Monitoring & Optimization Parameters
# ============================================================================


class PerformanceMonitoringParams(BaseModel):
    """Parameters for performance monitoring operations"""

    config_path: Optional[str] = Field(
        default=None, description="Path to performance monitoring configuration file"
    )
    collection_interval: Optional[int] = Field(
        default=None, ge=1, le=300, description="Metrics collection interval in seconds"
    )


class PerformanceMetricParams(BaseModel):
    """Parameters for recording performance metrics"""

    metric_type: Literal[
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "network_io",
        "response_time",
        "throughput",
        "error_rate",
        "active_connections",
        "queue_size",
        "cache_hit_rate",
        "database_connections",
        "formula_calculation_time",
        "api_response_time",
        "memory_leaks",
        "garbage_collection",
    ] = Field(..., description="Type of metric to record")
    value: float = Field(..., description="Metric value")
    tags: Optional[Dict[str, str]] = Field(
        default=None, description="Optional tags for the metric"
    )


class RequestPerformanceParams(BaseModel):
    """Parameters for recording request performance"""

    response_time: float = Field(..., ge=0, description="Response time in milliseconds")
    success: bool = Field(..., description="Whether the request was successful")
    endpoint: str = Field(default="", description="API endpoint that was called")


class AlertRuleParams(BaseModel):
    """Parameters for creating alert rules"""

    metric_type: Literal[
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "network_io",
        "response_time",
        "throughput",
        "error_rate",
        "active_connections",
        "queue_size",
        "cache_hit_rate",
        "database_connections",
        "formula_calculation_time",
        "api_response_time",
        "memory_leaks",
        "garbage_collection",
    ] = Field(..., description="Type of metric to monitor")
    threshold: float = Field(..., description="Threshold value for the alert")
    operator: Literal[">", "<", ">=", "<=", "==", "!="] = Field(
        ..., description="Comparison operator"
    )
    severity: Literal["info", "warning", "critical", "emergency"] = Field(
        ..., description="Alert severity level"
    )
    duration_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Duration in seconds before alert triggers",
    )
    description: str = Field(default="", description="Description of the alert rule")


class MetricHistoryParams(BaseModel):
    """Parameters for getting metric history"""

    metric_type: Literal[
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "network_io",
        "response_time",
        "throughput",
        "error_rate",
        "active_connections",
        "queue_size",
        "cache_hit_rate",
        "database_connections",
        "formula_calculation_time",
        "api_response_time",
        "memory_leaks",
        "garbage_collection",
    ] = Field(..., description="Type of metric to get history for")
    hours: int = Field(
        default=24, ge=1, le=168, description="Number of hours of history to retrieve"
    )


class PerformanceReportParams(BaseModel):
    """Parameters for generating performance reports"""

    hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Number of hours to analyze for the report",
    )
    include_recommendations: bool = Field(
        default=True, description="Whether to include optimization recommendations"
    )
    include_alerts: bool = Field(
        default=True, description="Whether to include alert analysis"
    )


class OptimizationParams(BaseModel):
    """Parameters for performance optimization"""

    optimization_type: Literal[
        "memory_optimization",
        "cpu_optimization",
        "cache_optimization",
        "database_optimization",
        "network_optimization",
        "formula_optimization",
        "concurrency_optimization",
    ] = Field(..., description="Type of optimization to apply")
    auto_apply: bool = Field(
        default=False, description="Whether to automatically apply the optimization"
    )
    dry_run: bool = Field(
        default=False,
        description="Whether to simulate the optimization without applying it",
    )


class MonitoringStatusParams(BaseModel):
    """Parameters for getting monitoring status"""

    include_metrics: bool = Field(
        default=True, description="Whether to include current metrics in status"
    )
    include_alerts: bool = Field(
        default=True, description="Whether to include active alerts in status"
    )
    include_baselines: bool = Field(
        default=False, description="Whether to include performance baselines"
    )


# ============================================================================
# Phase 10.3: Documentation & Training Parameters
# ============================================================================


class DocumentationGenerationParams(BaseModel):
    """Parameters for generating documentation"""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Title of the documentation"
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Description of the documentation",
    )
    doc_type: Literal[
        "user_guide",
        "api_documentation",
        "tutorial",
        "reference_guide",
        "training_material",
        "quick_start",
        "troubleshooting",
        "examples",
    ] = Field(default="user_guide", description="Type of documentation to generate")


class TutorialGenerationParams(BaseModel):
    """Parameters for generating tutorials"""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Title of the tutorial"
    )
    level: Literal["beginner", "intermediate", "advanced", "expert"] = Field(
        ..., description="Training difficulty level"
    )
    objectives: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Learning objectives for the tutorial",
    )
    estimated_duration: Optional[int] = Field(
        default=None, ge=15, le=480, description="Estimated duration in minutes"
    )


class TrainingModuleParams(BaseModel):
    """Parameters for creating training modules"""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Title of the training module"
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Description of the training module",
    )
    level: Literal["beginner", "intermediate", "advanced", "expert"] = Field(
        ..., description="Training difficulty level"
    )
    prerequisites: Optional[List[str]] = Field(
        default=None, description="Prerequisites for the training module"
    )
    learning_objectives: Optional[List[str]] = Field(
        default=None, description="Learning objectives for the module"
    )


class QuickStartGuideParams(BaseModel):
    """Parameters for generating quick start guides"""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Title of the quick start guide"
    )
    include_installation: bool = Field(
        default=True, description="Whether to include installation instructions"
    )
    include_examples: bool = Field(
        default=True, description="Whether to include code examples"
    )
    include_troubleshooting: bool = Field(
        default=True, description="Whether to include troubleshooting section"
    )


class ComprehensiveDocumentationParams(BaseModel):
    """Parameters for generating comprehensive documentation"""

    project_title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Title of the documentation project",
    )
    include_user_guide: bool = Field(
        default=True, description="Whether to include user guide"
    )
    include_api_docs: bool = Field(
        default=True, description="Whether to include API documentation"
    )
    include_tutorials: bool = Field(
        default=True, description="Whether to include tutorials"
    )
    include_training_modules: bool = Field(
        default=True, description="Whether to include training modules"
    )
    include_quick_start: bool = Field(
        default=True, description="Whether to include quick start guide"
    )


class DocumentationExportParams(BaseModel):
    """Parameters for exporting documentation"""

    doc_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID of the documentation to export",
    )
    format_type: Literal["markdown", "html", "pdf", "json", "rst"] = Field(
        ..., description="Output format for the documentation"
    )
    include_metadata: bool = Field(
        default=True, description="Whether to include metadata in export"
    )
    custom_styling: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom styling options for export"
    )


class DocumentationStatusParams(BaseModel):
    """Parameters for getting documentation status"""

    include_generated_docs: bool = Field(
        default=True, description="Whether to include list of generated documents"
    )
    include_training_modules: bool = Field(
        default=True, description="Whether to include list of training modules"
    )
    include_file_sizes: bool = Field(
        default=False, description="Whether to include file sizes"
    )
    include_generation_times: bool = Field(
        default=False, description="Whether to include generation timestamps"
    )


# ============================================================================
# Time Series Analysis Tool Parameters (Phase 10A Agent 8 Module 1)
# ============================================================================


class TestStationarityParams(BaseModel):
    """Parameters for stationarity testing (ADF/KPSS tests)

    Implements rec_0173_b7f48099: Test for Unit Roots and Stationarity
    Priority: 9.0/10, Effort: 8 hours
    """

    data: List[Union[int, float]] = Field(
        ...,
        min_length=10,
        description="Time series data as list of numbers (minimum 10 points required)",
    )
    time_column: Optional[str] = Field(
        default=None, description="Name of time column if data includes timestamps"
    )
    target_column: str = Field(
        default="value", description="Name of the target column to analyze"
    )
    method: Literal["adf", "kpss"] = Field(
        default="adf",
        description="Stationarity test method: 'adf' (Augmented Dickey-Fuller) or 'kpss' (Kwiatkowski-Phillips-Schmidt-Shin)",
    )
    freq: Optional[str] = Field(
        default=None,
        description="Frequency of time series (e.g., 'D' for daily, 'W' for weekly, 'M' for monthly)",
    )

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v):
        """Ensure sufficient data points"""
        if len(v) < 10:
            raise ValueError("Need at least 10 data points for stationarity test")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [10, 12, 15, 17, 20, 22, 25, 27, 30, 32],
                    "method": "adf",
                    "freq": "D",
                }
            ]
        }
    )


class DecomposeTimeSeriesParams(BaseModel):
    """Parameters for time series decomposition into trend/seasonal/residual"""

    data: List[Union[int, float]] = Field(
        ...,
        min_length=14,
        description="Time series data (minimum 14 points for seasonal decomposition)",
    )
    target_column: str = Field(default="value", description="Name of the target column")
    model: Literal["additive", "multiplicative"] = Field(
        default="additive",
        description="Decomposition model: 'additive' (Y=T+S+R) or 'multiplicative' (Y=T*S*R)",
    )
    period: Optional[int] = Field(
        default=None,
        ge=2,
        description="Seasonal period (e.g., 7 for weekly, 12 for monthly, 82 for NBA season)",
    )
    method: Literal["seasonal_decompose", "stl"] = Field(
        default="seasonal_decompose",
        description="Decomposition method: 'seasonal_decompose' or 'stl' (Seasonal-Trend Loess)",
    )
    freq: Optional[str] = Field(default=None, description="Frequency of time series")

    @field_validator("data")
    @classmethod
    def validate_sufficient_data(cls, v):
        """Ensure enough data for decomposition"""
        if len(v) < 14:
            raise ValueError("Need at least 14 data points for decomposition")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [25, 28, 22, 26, 29, 24, 27, 30, 25, 28, 32, 27, 29, 31],
                    "model": "additive",
                    "period": 7,
                    "method": "seasonal_decompose",
                }
            ]
        }
    )


class FitARIMAModelParams(BaseModel):
    """Parameters for ARIMA model fitting

    Implements Phase 10A recommendations:
    - rec_0181_87cfa0af: Time Series Model for Team Performance
    - rec_0265_33796e0c: Time Series Analysis for Future Game Outcomes
    """

    data: List[Union[int, float]] = Field(
        ...,
        min_length=20,
        description="Time series data (minimum 20 points for reliable ARIMA estimation)",
    )
    target_column: str = Field(default="value", description="Name of the target column")
    order: Optional[Tuple[int, int, int]] = Field(
        default=None,
        description="ARIMA order (p, d, q): p=AR order, d=differencing, q=MA order",
    )
    seasonal_order: Optional[Tuple[int, int, int, int]] = Field(
        default=None, description="Seasonal ARIMA order (P, D, Q, s): s=seasonal period"
    )
    auto_select: bool = Field(
        default=True,
        description="Use auto_arima to automatically select best parameters",
    )
    freq: Optional[str] = Field(default=None, description="Frequency of time series")

    @field_validator("data")
    @classmethod
    def validate_sufficient_data(cls, v):
        """Ensure enough data for ARIMA"""
        if len(v) < 20:
            raise ValueError(
                "Need at least 20 data points for reliable ARIMA estimation"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [
                        25,
                        27,
                        26,
                        28,
                        30,
                        29,
                        31,
                        32,
                        30,
                        33,
                        35,
                        34,
                        36,
                        38,
                        37,
                        39,
                        41,
                        40,
                        42,
                        44,
                    ],
                    "auto_select": True,
                },
                {
                    "data": [
                        25,
                        27,
                        26,
                        28,
                        30,
                        29,
                        31,
                        32,
                        30,
                        33,
                        35,
                        34,
                        36,
                        38,
                        37,
                        39,
                        41,
                        40,
                        42,
                        44,
                    ],
                    "order": [1, 0, 1],
                    "auto_select": False,
                },
            ]
        }
    )


class ForecastARIMAParams(BaseModel):
    """Parameters for ARIMA forecasting"""

    data: List[Union[int, float]] = Field(
        ..., min_length=20, description="Historical time series data"
    )
    steps: int = Field(
        default=10, ge=1, le=100, description="Number of periods to forecast (1-100)"
    )
    target_column: str = Field(default="value", description="Name of the target column")
    order: Optional[Tuple[int, int, int]] = Field(
        default=None,
        description="ARIMA order (p, d, q). If None, auto-selects best order",
    )
    alpha: float = Field(
        default=0.05,
        gt=0.0,
        lt=1.0,
        description="Significance level for confidence intervals (default: 0.05 = 95% CI)",
    )
    freq: Optional[str] = Field(default=None, description="Frequency of time series")

    @field_validator("alpha")
    @classmethod
    def validate_alpha(cls, v):
        """Validate alpha is reasonable"""
        if v <= 0 or v >= 1:
            raise ValueError("Alpha must be between 0 and 1 (exclusive)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [
                        25,
                        27,
                        26,
                        28,
                        30,
                        29,
                        31,
                        32,
                        30,
                        33,
                        35,
                        34,
                        36,
                        38,
                        37,
                        39,
                        41,
                        40,
                        42,
                        44,
                    ],
                    "steps": 10,
                    "alpha": 0.05,
                }
            ]
        }
    )


class AutocorrelationAnalysisParams(BaseModel):
    """Parameters for autocorrelation analysis (ACF/PACF/Ljung-Box)

    Implements Phase 10A recommendations:
    - rec_0616_7e53cb19: Test for Serial Correlation (Breusch-Godfrey)
    - rec_0605_4800d3fd: Test for Serial Correlation in Time Series Models
    """

    data: List[Union[int, float]] = Field(
        ..., min_length=20, description="Time series data for autocorrelation analysis"
    )
    nlags: int = Field(
        default=40, ge=1, le=100, description="Number of lags to compute (1-100)"
    )
    target_column: str = Field(default="value", description="Name of the target column")
    freq: Optional[str] = Field(default=None, description="Frequency of time series")

    @field_validator("nlags")
    @classmethod
    def validate_nlags(cls, v, info):
        """Ensure nlags is reasonable relative to data length"""
        data = info.data.get("data")
        if data and v >= len(data) / 2:
            raise ValueError(
                f"nlags ({v}) should be less than half the data length ({len(data)})"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [
                        25,
                        27,
                        26,
                        28,
                        30,
                        29,
                        31,
                        32,
                        30,
                        33,
                        35,
                        34,
                        36,
                        38,
                        37,
                        39,
                        41,
                        40,
                        42,
                        44,
                        43,
                        45,
                        47,
                        46,
                        48,
                        50,
                    ],
                    "nlags": 20,
                }
            ]
        }
    )


# =============================================================================
# Panel Data Analysis Parameters (Phase 10A Agent 8 Module 2)
# =============================================================================


class PanelDiagnosticsParams(BaseModel):
    """Parameters for panel data diagnostics.

    Implements rec_0625_1b208ec4: Panel Data Models with Fixed and Random Effects
    Priority: 9.0/10, Effort: 40 hours
    """

    data: List[Dict[str, Any]] = Field(
        ...,
        min_length=10,
        description="Panel data as list of dictionaries (minimum 10 observations required)",
    )
    entity_column: str = Field(
        default="entity_id",
        description="Column name identifying entities (e.g., player_id, team_id)",
    )
    time_column: str = Field(
        default="time_period",
        description="Column name identifying time periods (e.g., season, game_number)",
    )
    target_column: str = Field(
        default="value", description="Column name containing dependent variable"
    )

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v):
        if len(v) < 10:
            raise ValueError("Need at least 10 observations for panel diagnostics")
        return v


class PooledOLSParams(BaseModel):
    """Parameters for pooled OLS regression.

    Implements rec_0625_1b208ec4: Panel Data Models with Fixed and Random Effects
    Priority: 9.0/10, Effort: 40 hours
    """

    data: List[Dict[str, Any]] = Field(
        ...,
        min_length=20,
        description="Panel data as list of dictionaries (minimum 20 observations required)",
    )
    formula: str = Field(
        ..., min_length=3, description="Model formula (e.g., 'value ~ x1 + x2')"
    )
    entity_column: str = Field(
        default="entity_id", description="Column name identifying entities"
    )
    time_column: str = Field(
        default="time_period", description="Column name identifying time periods"
    )
    target_column: str = Field(
        default="value", description="Column name containing dependent variable"
    )

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v):
        if len(v) < 20:
            raise ValueError("Need at least 20 observations for pooled OLS")
        return v


class FixedEffectsParams(BaseModel):
    """Parameters for fixed effects regression.

    Implements rec_0625_1b208ec4: Panel Data Models with Fixed and Random Effects
    Priority: 9.0/10, Effort: 40 hours
    """

    data: List[Dict[str, Any]] = Field(
        ...,
        min_length=20,
        description="Panel data as list of dictionaries (minimum 20 observations required)",
    )
    formula: str = Field(
        ..., min_length=3, description="Model formula (e.g., 'value ~ x1 + x2')"
    )
    entity_column: str = Field(
        default="entity_id", description="Column name identifying entities"
    )
    time_column: str = Field(
        default="time_period", description="Column name identifying time periods"
    )
    target_column: str = Field(
        default="value", description="Column name containing dependent variable"
    )
    entity_effects: bool = Field(
        default=True, description="Include entity-specific fixed effects"
    )
    time_effects: bool = Field(
        default=False, description="Include time-specific fixed effects"
    )

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v):
        if len(v) < 20:
            raise ValueError("Need at least 20 observations for fixed effects")
        return v


class RandomEffectsParams(BaseModel):
    """Parameters for random effects regression.

    Implements rec_0625_1b208ec4: Panel Data Models with Fixed and Random Effects
    Priority: 9.0/10, Effort: 40 hours
    """

    data: List[Dict[str, Any]] = Field(
        ...,
        min_length=30,
        description="Panel data as list of dictionaries (minimum 30 observations required)",
    )
    formula: str = Field(
        ..., min_length=3, description="Model formula (e.g., 'value ~ x1 + x2')"
    )
    entity_column: str = Field(
        default="entity_id", description="Column name identifying entities"
    )
    time_column: str = Field(
        default="time_period", description="Column name identifying time periods"
    )
    target_column: str = Field(
        default="value", description="Column name containing dependent variable"
    )

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v):
        if len(v) < 30:
            raise ValueError("Need at least 30 observations for random effects")
        return v


class HausmanTestParams(BaseModel):
    """Parameters for Hausman specification test (FE vs RE).

    Implements rec_0625_1b208ec4: Panel Data Models with Fixed and Random Effects
    Priority: 9.0/10, Effort: 40 hours
    """

    data: List[Dict[str, Any]] = Field(
        ...,
        min_length=30,
        description="Panel data as list of dictionaries (minimum 30 observations required)",
    )
    formula: str = Field(
        ..., min_length=3, description="Model formula (e.g., 'value ~ x1 + x2')"
    )
    entity_column: str = Field(
        default="entity_id", description="Column name identifying entities"
    )
    time_column: str = Field(
        default="time_period", description="Column name identifying time periods"
    )
    target_column: str = Field(
        default="value", description="Column name containing dependent variable"
    )

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v):
        if len(v) < 30:
            raise ValueError("Need at least 30 observations for Hausman test")
        return v


class FirstDifferenceParams(BaseModel):
    """Parameters for first difference regression.

    Implements rec_0625_1b208ec4: Panel Data Models with Fixed and Random Effects
    Priority: 9.0/10, Effort: 40 hours
    """

    data: List[Dict[str, Any]] = Field(
        ...,
        min_length=30,
        description="Panel data as list of dictionaries (minimum 30 observations required)",
    )
    formula: str = Field(
        ..., min_length=3, description="Model formula (e.g., 'value ~ x1 + x2')"
    )
    entity_column: str = Field(
        default="entity_id", description="Column name identifying entities"
    )
    time_column: str = Field(
        default="time_period", description="Column name identifying time periods"
    )
    target_column: str = Field(
        default="value", description="Column name containing dependent variable"
    )

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v):
        if len(v) < 30:
            raise ValueError("Need at least 30 observations for first difference model")
        return v


# ============================================================================
# Phase 10A - Agent 8: Advanced Econometrics Parameter Schemas
# Module 3: Bayesian Analysis Tools (7 tools)
# Module 4A: Causal Inference Tools (6 tools)
# Module 4B: Survival Analysis Tools (6 tools)
# Module 4C: Advanced Time Series Tools (4 tools)
# Module 4D: Econometric Suite Tools (4 tools)
# Total: 27 new parameter schemas
# ============================================================================


# ============================================================================
# Module 3: Bayesian Analysis Parameters
# ============================================================================


class BayesianLinearRegressionParams(BaseModel):
    """Parameters for Bayesian linear regression with conjugate priors."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=10, description="Data as list of dictionaries"
    )
    formula: str = Field(
        ..., min_length=3, description="Model formula (e.g., 'y ~ x1 + x2')"
    )
    prior_mean: Optional[List[float]] = Field(
        default=None, description="Prior mean for coefficients (optional)"
    )
    prior_variance: Optional[float] = Field(
        default=1.0, ge=0.001, description="Prior variance scaling parameter"
    )
    n_samples: int = Field(
        default=5000, ge=1000, le=50000, description="Number of posterior samples"
    )
    credible_interval: float = Field(
        default=0.95, ge=0.5, le=0.99, description="Credible interval level"
    )


class BayesianHierarchicalModelParams(BaseModel):
    """Parameters for Bayesian hierarchical/multilevel model."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Hierarchical data as list of dictionaries"
    )
    formula: str = Field(
        ..., min_length=5, description="Model formula with random effects syntax"
    )
    group_column: str = Field(
        ..., description="Column name identifying groups/clusters"
    )
    n_samples: int = Field(
        default=5000, ge=1000, le=50000, description="Number of MCMC samples"
    )
    n_chains: int = Field(
        default=4, ge=1, le=8, description="Number of parallel MCMC chains"
    )
    warmup: int = Field(
        default=1000, ge=100, le=10000, description="Number of warmup iterations"
    )


class BayesianModelComparisonParams(BaseModel):
    """Parameters for Bayesian model comparison and selection."""

    models: List[Dict[str, Any]] = Field(
        ..., min_length=2, description="List of model specifications to compare"
    )
    data: List[Dict[str, Any]] = Field(
        ..., min_length=20, description="Data for model comparison"
    )
    comparison_method: Literal["waic", "loo", "dic", "bayes_factor"] = Field(
        default="waic", description="Method for model comparison"
    )
    n_samples: int = Field(
        default=5000, ge=1000, le=50000, description="Posterior samples per model"
    )


class BayesianCredibleIntervalsParams(BaseModel):
    """Parameters for computing Bayesian credible intervals."""

    posterior_samples: List[List[float]] = Field(
        ..., min_length=1000, description="Posterior samples for each parameter"
    )
    parameter_names: List[str] = Field(
        ..., min_length=1, description="Names of parameters"
    )
    credible_level: float = Field(
        default=0.95, ge=0.5, le=0.99, description="Credible interval level"
    )
    interval_type: Literal["hdi", "equal_tailed"] = Field(
        default="hdi", description="Type of credible interval"
    )


class MCMCDiagnosticsParams(BaseModel):
    """Parameters for MCMC convergence diagnostics."""

    samples: List[List[float]] = Field(
        ..., min_length=1000, description="MCMC samples from all chains"
    )
    parameter_names: List[str] = Field(
        ..., min_length=1, description="Parameter names"
    )
    n_chains: int = Field(
        default=4, ge=2, le=8, description="Number of chains"
    )
    diagnostics: List[Literal["rhat", "neff", "geweke", "autocorr"]] = Field(
        default=["rhat", "neff"], description="Diagnostics to compute"
    )


class PosteriorPredictiveCheckParams(BaseModel):
    """Parameters for posterior predictive checks."""

    observed_data: List[float] = Field(
        ..., min_length=10, description="Observed data values"
    )
    posterior_samples: List[List[float]] = Field(
        ..., min_length=1000, description="Posterior samples for parameters"
    )
    model_function: str = Field(
        ..., description="Model specification for generating predictions"
    )
    n_replications: int = Field(
        default=1000, ge=100, le=10000, description="Number of posterior predictive replications"
    )
    test_statistics: List[str] = Field(
        default=["mean", "std", "min", "max"], description="Test statistics to compute"
    )


class BayesianUpdatingParams(BaseModel):
    """Parameters for sequential Bayesian updating."""

    prior_distribution: Dict[str, Any] = Field(
        ..., description="Prior distribution specification"
    )
    new_data: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="New data for updating"
    )
    parameter_names: List[str] = Field(
        ..., min_length=1, description="Parameters to update"
    )
    n_samples: int = Field(
        default=5000, ge=1000, le=50000, description="Number of posterior samples"
    )


# ============================================================================
# Module 4A: Causal Inference Parameters
# ============================================================================


class InstrumentalVariablesParams(BaseModel):
    """Parameters for instrumental variables (IV/2SLS) estimation."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Data as list of dictionaries"
    )
    formula: str = Field(
        ..., min_length=5, description="Structural equation formula"
    )
    instruments: List[str] = Field(
        ..., min_length=1, description="List of instrument variable names"
    )
    endogenous_vars: List[str] = Field(
        ..., min_length=1, description="List of endogenous variable names"
    )
    method: Literal["2sls", "liml", "gmm"] = Field(
        default="2sls", description="Estimation method"
    )


class RegressionDiscontinuityParams(BaseModel):
    """Parameters for regression discontinuity design (RDD)."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=50, description="Data with running variable"
    )
    outcome_var: str = Field(
        ..., description="Outcome variable name"
    )
    running_var: str = Field(
        ..., description="Running/forcing variable name"
    )
    cutoff: float = Field(
        ..., description="Treatment assignment cutoff"
    )
    bandwidth: Optional[float] = Field(
        default=None, ge=0.001, description="Bandwidth for local estimation (auto if None)"
    )
    polynomial_order: int = Field(
        default=1, ge=1, le=4, description="Polynomial order for local regression"
    )
    kernel: Literal["triangular", "rectangular", "epanechnikov"] = Field(
        default="triangular", description="Kernel function"
    )


class DifferenceInDifferencesParams(BaseModel):
    """Parameters for difference-in-differences estimation."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=40, description="Panel data with treatment and control groups"
    )
    outcome_var: str = Field(
        ..., description="Outcome variable name"
    )
    treatment_var: str = Field(
        ..., description="Treatment indicator variable"
    )
    time_var: str = Field(
        ..., description="Time period variable"
    )
    group_var: str = Field(
        ..., description="Group identifier variable"
    )
    covariates: Optional[List[str]] = Field(
        default=None, description="Control variables"
    )
    cluster_var: Optional[str] = Field(
        default=None, description="Variable for clustered standard errors"
    )


class SyntheticControlParams(BaseModel):
    """Parameters for synthetic control method."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=50, description="Panel data for treated and control units"
    )
    outcome_var: str = Field(
        ..., description="Outcome variable name"
    )
    unit_var: str = Field(
        ..., description="Unit identifier variable"
    )
    time_var: str = Field(
        ..., description="Time period variable"
    )
    treated_unit: Union[str, int] = Field(
        ..., description="ID of treated unit"
    )
    treatment_time: Union[str, int] = Field(
        ..., description="Time of treatment intervention"
    )
    predictors: Optional[List[str]] = Field(
        default=None, description="Predictor variables for matching"
    )


class PropensityScoreMatchingParams(BaseModel):
    """Parameters for propensity score matching."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=50, description="Data with treatment and control observations"
    )
    treatment_var: str = Field(
        ..., description="Treatment indicator variable (binary)"
    )
    outcome_var: str = Field(
        ..., description="Outcome variable name"
    )
    covariates: List[str] = Field(
        ..., min_length=1, description="Variables for propensity score model"
    )
    matching_method: Literal["nearest", "caliper", "radius", "kernel"] = Field(
        default="nearest", description="Matching algorithm"
    )
    n_neighbors: int = Field(
        default=1, ge=1, le=10, description="Number of matches per treated unit"
    )
    caliper: Optional[float] = Field(
        default=None, ge=0.001, le=0.5, description="Maximum propensity score distance"
    )


class MediationAnalysisParams(BaseModel):
    """Parameters for causal mediation analysis."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Data with treatment, mediator, and outcome"
    )
    treatment_var: str = Field(
        ..., description="Treatment variable name"
    )
    mediator_var: str = Field(
        ..., description="Mediator variable name"
    )
    outcome_var: str = Field(
        ..., description="Outcome variable name"
    )
    covariates: Optional[List[str]] = Field(
        default=None, description="Confounding variables"
    )
    n_bootstrap: int = Field(
        default=1000, ge=100, le=10000, description="Bootstrap replications for inference"
    )


# ============================================================================
# Module 4B: Survival Analysis Parameters
# ============================================================================


class KaplanMeierParams(BaseModel):
    """Parameters for Kaplan-Meier survival estimation."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=20, description="Survival data"
    )
    duration_var: str = Field(
        ..., description="Duration/time variable name"
    )
    event_var: str = Field(
        ..., description="Event indicator variable (1=event, 0=censored)"
    )
    group_var: Optional[str] = Field(
        default=None, description="Grouping variable for stratified analysis"
    )
    confidence_level: float = Field(
        default=0.95, ge=0.5, le=0.99, description="Confidence level"
    )


class CoxProportionalHazardsParams(BaseModel):
    """Parameters for Cox proportional hazards regression."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Survival data with covariates"
    )
    duration_var: str = Field(
        ..., description="Duration/time variable name"
    )
    event_var: str = Field(
        ..., description="Event indicator variable"
    )
    covariates: List[str] = Field(
        ..., min_length=1, description="Covariate variable names"
    )
    strata: Optional[List[str]] = Field(
        default=None, description="Stratification variables"
    )
    robust: bool = Field(
        default=True, description="Use robust standard errors"
    )


class ParametricSurvivalParams(BaseModel):
    """Parameters for parametric survival models."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Survival data"
    )
    duration_var: str = Field(
        ..., description="Duration variable name"
    )
    event_var: str = Field(
        ..., description="Event indicator variable"
    )
    covariates: List[str] = Field(
        ..., min_length=1, description="Covariate variables"
    )
    distribution: Literal["weibull", "exponential", "lognormal", "loglogistic"] = Field(
        default="weibull", description="Assumed survival time distribution"
    )


class CompetingRisksParams(BaseModel):
    """Parameters for competing risks analysis."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Data with multiple event types"
    )
    duration_var: str = Field(
        ..., description="Duration variable name"
    )
    event_type_var: str = Field(
        ..., description="Event type variable (0=censored, 1,2,...=event types)"
    )
    covariates: Optional[List[str]] = Field(
        default=None, description="Covariate variables"
    )
    event_of_interest: int = Field(
        default=1, ge=1, description="Event type to focus on"
    )


class RecurrentEventsParams(BaseModel):
    """Parameters for recurrent events analysis."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Data with repeated events per subject"
    )
    subject_var: str = Field(
        ..., description="Subject/ID variable name"
    )
    time_var: str = Field(
        ..., description="Event time variable"
    )
    event_var: str = Field(
        ..., description="Event indicator"
    )
    covariates: Optional[List[str]] = Field(
        default=None, description="Covariate variables"
    )
    model_type: Literal["pwp", "ag", "wlw"] = Field(
        default="pwp", description="Recurrent event model type"
    )


class TimeVaryingCovariatesParams(BaseModel):
    """Parameters for survival models with time-varying covariates."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Data in counting process format"
    )
    start_var: str = Field(
        ..., description="Interval start time variable"
    )
    stop_var: str = Field(
        ..., description="Interval stop time variable"
    )
    event_var: str = Field(
        ..., description="Event indicator at stop time"
    )
    subject_var: str = Field(
        ..., description="Subject identifier variable"
    )
    covariates: List[str] = Field(
        ..., min_length=1, description="Time-varying covariate names"
    )


# ============================================================================
# Module 4C: Advanced Time Series Parameters
# ============================================================================


class KalmanFilterParams(BaseModel):
    """Parameters for Kalman filter state-space estimation."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=20, description="Time series data"
    )
    state_dim: int = Field(
        ..., ge=1, le=10, description="Dimension of latent state vector"
    )
    observation_vars: List[str] = Field(
        ..., min_length=1, description="Observable variable names"
    )
    estimate_parameters: bool = Field(
        default=True, description="Estimate state-space matrices via MLE"
    )
    smoother: bool = Field(
        default=True, description="Apply Kalman smoother"
    )
    forecast_steps: int = Field(
        default=0, ge=0, le=100, description="Number of forecast steps"
    )


class DynamicFactorModelParams(BaseModel):
    """Parameters for dynamic factor model estimation."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Multivariate time series data"
    )
    variables: List[str] = Field(
        ..., min_length=2, description="Variables for factor extraction"
    )
    n_factors: int = Field(
        ..., ge=1, le=10, description="Number of latent factors"
    )
    factor_order: int = Field(
        default=1, ge=0, le=4, description="AR order for factor dynamics"
    )
    method: Literal["ml", "pc", "2step"] = Field(
        default="ml", description="Estimation method"
    )


class MarkovSwitchingModelParams(BaseModel):
    """Parameters for Markov-switching regression model."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=50, description="Time series data"
    )
    dependent_var: str = Field(
        ..., description="Dependent variable name"
    )
    independent_vars: Optional[List[str]] = Field(
        default=None, description="Independent variable names"
    )
    n_regimes: int = Field(
        default=2, ge=2, le=5, description="Number of regimes/states"
    )
    switching_variance: bool = Field(
        default=True, description="Allow variance to switch across regimes"
    )
    switching_mean: bool = Field(
        default=True, description="Allow mean to switch across regimes"
    )


class StructuralTimeSeriesParams(BaseModel):
    """Parameters for structural time series decomposition."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=30, description="Time series data"
    )
    variable: str = Field(
        ..., description="Variable to decompose"
    )
    components: List[Literal["level", "trend", "seasonal", "cycle", "irregular"]] = Field(
        ..., min_length=1, description="Structural components to include"
    )
    seasonal_period: Optional[int] = Field(
        default=None, ge=2, le=365, description="Period for seasonal component"
    )
    stochastic_level: bool = Field(
        default=True, description="Stochastic level component"
    )
    stochastic_seasonal: bool = Field(
        default=True, description="Stochastic seasonal component"
    )


# ============================================================================
# Module 4D: Econometric Suite Parameters
# ============================================================================


class AutoDetectEconometricMethodParams(BaseModel):
    """Parameters for automatic econometric method detection."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=20, description="Input dataset"
    )
    dependent_var: str = Field(
        ..., description="Dependent variable name"
    )
    independent_vars: Optional[List[str]] = Field(
        default=None, description="Independent variable names"
    )
    panel_id: Optional[str] = Field(
        default=None, description="Panel/group identifier"
    )
    time_var: Optional[str] = Field(
        default=None, description="Time variable"
    )
    research_question: Optional[str] = Field(
        default=None, max_length=500, description="Research question description"
    )


class AutoAnalyzeEconometricDataParams(BaseModel):
    """Parameters for comprehensive automated econometric analysis."""

    data: List[Dict[str, Any]] = Field(
        ..., min_length=20, description="Input dataset"
    )
    dependent_var: str = Field(
        ..., description="Dependent variable name"
    )
    independent_vars: Optional[List[str]] = Field(
        default=None, description="Independent variable names"
    )
    panel_id: Optional[str] = Field(
        default=None, description="Panel identifier"
    )
    time_var: Optional[str] = Field(
        default=None, description="Time variable"
    )
    methods: Optional[List[str]] = Field(
        default=None, description="Specific methods to run (auto-detect if None)"
    )
    include_robustness: bool = Field(
        default=True, description="Run robustness checks"
    )


class CompareEconometricMethodsParams(BaseModel):
    """Parameters for comparing results across econometric methods."""

    results: Dict[str, Dict[str, Any]] = Field(
        ..., min_length=2, description="Dictionary of method names to results"
    )
    comparison_dimensions: Optional[List[str]] = Field(
        default=None, description="Aspects to compare"
    )
    weight_by_fit: bool = Field(
        default=True, description="Weight estimates by model fit"
    )


class EconometricModelAveragingParams(BaseModel):
    """Parameters for econometric model averaging."""

    results: Dict[str, Dict[str, Any]] = Field(
        ..., min_length=2, description="Dictionary of method names to results"
    )
    data: List[Dict[str, Any]] = Field(
        ..., min_length=20, description="Original data for validation"
    )
    dependent_var: str = Field(
        ..., description="Dependent variable name"
    )
    averaging_method: Literal["aic", "bic", "mse", "equal"] = Field(
        default="aic", description="Weighting scheme for averaging"
    )
    bootstrap_ci: bool = Field(
        default=True, description="Use bootstrap for confidence intervals"
    )
    n_bootstrap: int = Field(
        default=1000, ge=100, le=10000, description="Bootstrap replications"
    )
