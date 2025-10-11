"""
Pydantic Parameter Models for MCP Tools
Provides automatic validation for all tool parameters
Based on Graphiti MCP best practices
"""

from pydantic import BaseModel, Field, validator, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal, Tuple, Union
import re


# ============================================================================
# Database Tool Parameters
# ============================================================================

class QueryDatabaseParams(BaseModel):
    """Parameters for database query execution"""
    
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
        description="Maximum number of rows to return"
    )
    
    @validator('sql_query')
    def validate_sql_query(cls, v):
        """Validate SQL query is safe"""
        # Only SELECT and WITH allowed
        query_upper = v.strip().upper()
        if not query_upper.startswith(('SELECT', 'WITH')):
            raise ValueError("Only SELECT queries allowed. Use WITH...SELECT for CTEs.")
        
        # Check for forbidden keywords
        forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 
                    'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE']
        for keyword in forbidden:
            if re.search(rf'\b{keyword}\b', query_upper):
                raise ValueError(f"Forbidden SQL operation: {keyword}. Only SELECT queries are allowed.")
        
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "sql_query": "SELECT * FROM games WHERE season = 2024 LIMIT 10",
                    "max_rows": 10
                }
            ]
        }


class GetTableSchemaParams(BaseModel):
    """Parameters for getting table schema"""
    
    table_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_]+$',
        description="Table name (alphanumeric and underscore only)"
    )
    
    @validator('table_name')
    def validate_table_name(cls, v):
        """Additional validation for table name"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Table name can only contain alphanumeric characters and underscores")
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {"table_name": "games"},
                {"table_name": "player_stats"}
            ]
        }


class ListTablesParams(BaseModel):
    """Parameters for listing tables"""

    schema_name: Optional[str] = Field(
        default=None,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_]+$',
        description="Optional schema name to filter tables (e.g., 'public')",
        alias="schema"
    )

    @validator('schema_name')
    def validate_schema_name(cls, v):
        """Validate schema name is safe"""
        if v and not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Schema name can only contain alphanumeric characters and underscores")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {},
                {"schema": "public"}
            ]
        }
        populate_by_name = True  # Allow using alias or field name


# ============================================================================
# S3 Tool Parameters
# ============================================================================

class ListS3FilesParams(BaseModel):
    """Parameters for listing S3 files"""
    
    prefix: str = Field(
        default="",
        max_length=500,
        description="S3 prefix filter (e.g., '2024/games/')"
    )
    max_keys: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of files to return"
    )
    
    @validator('prefix')
    def validate_prefix(cls, v):
        """Validate S3 prefix is safe"""
        # Prevent path traversal
        if '..' in v:
            raise ValueError("Path traversal not allowed in prefix")
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {"prefix": "2024/games/", "max_keys": 100},
                {"prefix": "players/", "max_keys": 50}
            ]
        }


class GetS3FileParams(BaseModel):
    """Parameters for getting S3 file content"""
    
    file_key: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="S3 object key"
    )
    
    @validator('file_key')
    def validate_file_key(cls, v):
        """Validate S3 file key is safe"""
        if '..' in v:
            raise ValueError("Path traversal not allowed in file key")
        if v.startswith('/'):
            raise ValueError("File key should not start with /")
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {"file_key": "2024/games/game_12345.json"}
            ]
        }


# ============================================================================
# Glue Tool Parameters
# ============================================================================

class GetGlueTableMetadataParams(BaseModel):
    """Parameters for getting Glue table metadata"""
    
    table_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_]+$',
        description="Glue table name"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {"table_name": "raw_games"}
            ]
        }


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
        description="Filter by season year (e.g., 2024)"
    )
    team_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Filter by team name (home or away)"
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Pagination cursor (base64 encoded game_id)"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of games per page"
    )

    @validator('team_name')
    def validate_team_name(cls, v):
        """Validate team name is safe"""
        if v and not re.match(r'^[a-zA-Z0-9\s\-]+$', v):
            raise ValueError("Team name can only contain alphanumeric, spaces, and hyphens")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"season": 2024, "limit": 50},
                {"team_name": "Lakers", "limit": 20},
                {"season": 2024, "cursor": "MTIzNDU=", "limit": 50}
            ]
        }


class ListPlayersParams(BaseModel):
    """Parameters for listing players with pagination"""

    team_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Filter by team name"
    )
    position: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Filter by position (e.g., 'PG', 'SG', 'SF')"
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Pagination cursor (base64 encoded player_id)"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of players per page"
    )

    @validator('team_name')
    def validate_team_name(cls, v):
        """Validate team name is safe"""
        if v and not re.match(r'^[a-zA-Z0-9\s\-]+$', v):
            raise ValueError("Team name can only contain alphanumeric, spaces, and hyphens")
        return v

    @validator('position')
    def validate_position(cls, v):
        """Validate position is valid"""
        valid_positions = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F']
        if v and v.upper() not in valid_positions:
            raise ValueError(f"Position must be one of: {', '.join(valid_positions)}")
        return v.upper() if v else v

    class Config:
        json_schema_extra = {
            "examples": [
                {"limit": 50},
                {"team_name": "Lakers", "limit": 20},
                {"position": "PG", "cursor": "MTIzNDU=", "limit": 50}
            ]
        }


# ============================================================================
# Book Tool Parameters
# ============================================================================

class ListBooksParams(BaseModel):
    """Parameters for listing books"""

    prefix: str = Field(
        default="books/",
        max_length=200,
        description="S3 prefix to filter books (e.g., 'books/technical/', 'books/business/')"
    )
    max_keys: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of books to return"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"prefix": "books/"},
                {"prefix": "books/technical/", "max_keys": 50}
            ]
        }


class ReadBookParams(BaseModel):
    """Parameters for reading a book with smart chunking"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path to the book (e.g., 'books/my-book.txt')"
    )
    chunk_size: int = Field(
        default=50000,
        ge=1000,
        le=200000,
        description="Characters per chunk (default: 50k, max: 200k for large context windows)"
    )
    chunk_number: int = Field(
        default=0,
        ge=0,
        description="Chunk number to retrieve (0-indexed)"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe"""
        # Prevent path traversal
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid book path")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/nba-analytics-guide.txt"},
                {"book_path": "books/technical/python-best-practices.txt", "chunk_size": 100000, "chunk_number": 2}
            ]
        }


class SearchBooksParams(BaseModel):
    """Parameters for searching within books"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query"
    )
    book_prefix: str = Field(
        default="books/",
        max_length=200,
        description="Limit search to books under this prefix"
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"query": "machine learning", "max_results": 10},
                {"query": "database optimization", "book_prefix": "books/technical/"}
            ]
        }


# ============================================================================
# EPUB Tool Parameters
# ============================================================================

class GetEpubMetadataParams(BaseModel):
    """Parameters for getting EPUB metadata"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to EPUB file"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .epub"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.epub'):
            raise ValueError("File must be an EPUB (.epub)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/python-guide.epub"},
                {"book_path": "books/technical/nba-analytics.epub"}
            ]
        }


class GetEpubTocParams(BaseModel):
    """Parameters for getting EPUB table of contents"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to EPUB file"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .epub"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.epub'):
            raise ValueError("File must be an EPUB (.epub)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/python-guide.epub"}
            ]
        }


class ReadEpubChapterParams(BaseModel):
    """Parameters for reading EPUB chapter"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to EPUB file"
    )
    chapter_href: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Chapter href from TOC (e.g., 'chapter1.xhtml' or 'chapter1.xhtml#section1')"
    )
    format: Literal["html", "markdown", "text"] = Field(
        default="markdown",
        description="Output format for chapter content"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .epub"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.epub'):
            raise ValueError("File must be an EPUB (.epub)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/python-guide.epub", "chapter_href": "chapter1.xhtml", "format": "markdown"},
                {"book_path": "books/python-guide.epub", "chapter_href": "chapter1.xhtml#intro", "format": "html"}
            ]
        }


# ============================================================================
# PDF Tool Parameters
# ============================================================================

class GetPdfMetadataParams(BaseModel):
    """Parameters for getting PDF metadata"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/statistics-textbook.pdf"},
                {"book_path": "books/technical/machine-learning.pdf"}
            ]
        }


class GetPdfTocParams(BaseModel):
    """Parameters for getting PDF table of contents"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/statistics-textbook.pdf"}
            ]
        }


class ReadPdfPageParams(BaseModel):
    """Parameters for reading a single PDF page"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file"
    )
    page_number: int = Field(
        ...,
        ge=0,
        description="Page number (0-indexed)"
    )
    format: Literal["text", "html", "markdown"] = Field(
        default="text",
        description="Output format for page content"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/statistics-textbook.pdf", "page_number": 0, "format": "text"},
                {"book_path": "books/statistics-textbook.pdf", "page_number": 5, "format": "markdown"}
            ]
        }


class ReadPdfPageRangeParams(BaseModel):
    """Parameters for reading a range of PDF pages"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file"
    )
    start_page: int = Field(
        ...,
        ge=0,
        description="Starting page number (0-indexed, inclusive)"
    )
    end_page: int = Field(
        ...,
        ge=0,
        description="Ending page number (0-indexed, inclusive)"
    )
    format: Literal["text", "html", "markdown"] = Field(
        default="text",
        description="Output format for page content"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    @model_validator(mode='after')
    def validate_page_range(self):
        """Validate that start_page <= end_page"""
        if self.start_page is not None and self.end_page is not None and self.start_page > self.end_page:
            raise ValueError("start_page must be <= end_page")
        return self

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/statistics-textbook.pdf", "start_page": 0, "end_page": 10, "format": "text"},
                {"book_path": "books/statistics-textbook.pdf", "start_page": 15, "end_page": 20, "format": "markdown"}
            ]
        }


class ReadPdfChapterParams(BaseModel):
    """Parameters for reading a PDF chapter by title"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file"
    )
    chapter_title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Chapter title (partial match supported)"
    )
    format: Literal["text", "html", "markdown"] = Field(
        default="text",
        description="Output format for chapter content"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/statistics-textbook.pdf", "chapter_title": "Introduction", "format": "markdown"},
                {"book_path": "books/statistics-textbook.pdf", "chapter_title": "Chapter 3", "format": "text"}
            ]
        }


class SearchPdfParams(BaseModel):
    """Parameters for searching text in PDF"""

    book_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="S3 path or local path to PDF file"
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query"
    )
    context_chars: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Number of characters to include before/after match"
    )

    @validator('book_path')
    def validate_book_path(cls, v):
        """Validate book path is safe and is .pdf"""
        if '..' in v or (v.startswith('/') and not v.startswith('/tmp')):
            raise ValueError("Invalid book path")
        if not v.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF (.pdf)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"book_path": "books/statistics-textbook.pdf", "query": "regression analysis", "context_chars": 100},
                {"book_path": "books/statistics-textbook.pdf", "query": "hypothesis testing", "context_chars": 150}
            ]
        }


# ============================================================================
# File Tool Parameters
# ============================================================================

class ReadProjectFileParams(BaseModel):
    """Parameters for reading project files"""
    
    file_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Relative path to file within project"
    )
    
    @validator('file_path')
    def validate_file_path(cls, v):
        """Validate file path is safe"""
        # Prevent path traversal
        if '..' in v:
            raise ValueError("Path traversal not allowed")
        if v.startswith('/'):
            raise ValueError("Use relative paths only")
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {"file_path": "synthesis/models/ollama_model.py"}
            ]
        }


class SearchProjectFilesParams(BaseModel):
    """Parameters for searching project files"""
    
    pattern: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search pattern (regex or glob)"
    )
    file_pattern: Optional[str] = Field(
        default="*.py",
        description="File pattern to search (e.g., '*.py', '*.md')"
    )
    max_results: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of results"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "pattern": "def.*synthesize",
                    "file_pattern": "*.py",
                    "max_results": 20
                }
            ]
        }


# ============================================================================
# Action Tool Parameters
# ============================================================================

class SaveToProjectParams(BaseModel):
    """Parameters for saving synthesis results"""
    
    filename: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Filename for saved output"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Content to save"
    )
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename is safe"""
        if '..' in v or '/' in v:
            raise ValueError("Filename must not contain path separators or traversal")
        # Only allow safe characters
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError("Filename can only contain alphanumeric, underscore, dash, and dot")
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "filename": "lakers_analysis_2024.md",
                    "content": "# Lakers Analysis\n\n..."
                }
            ]
        }


class LogSynthesisResultParams(BaseModel):
    """Parameters for logging synthesis results"""
    
    query: str = Field(..., min_length=1, description="Original query")
    result: Dict[str, Any] = Field(..., description="Synthesis result")
    model_used: str = Field(..., description="Model used for synthesis")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query": "Analyze Lakers performance",
                    "result": {"summary": "..."},
                    "model_used": "deepseek"
                }
            ]
        }


class SendNotificationParams(BaseModel):
    """Parameters for sending Slack notifications"""
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=3000,
        description="Notification message"
    )
    level: Literal["info", "warning", "error", "success"] = Field(
        default="info",
        description="Notification level"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "message": "Synthesis completed successfully",
                    "level": "success"
                }
            ]
        }


# ============================================================================
# Math & Statistics Tool Parameters
# ============================================================================

from typing import Union

class MathTwoNumberParams(BaseModel):
    """Parameters for operations on two numbers"""
    a: Union[int, float] = Field(..., description="First number")
    b: Union[int, float] = Field(..., description="Second number")

    class Config:
        json_schema_extra = {
            "examples": [
                {"a": 5, "b": 3},
                {"a": 10.5, "b": 2.3}
            ]
        }


class MathDivideParams(BaseModel):
    """Parameters for division"""
    numerator: Union[int, float] = Field(..., description="Number being divided")
    denominator: Union[int, float] = Field(..., description="Number to divide by")

    @field_validator('denominator')
    @classmethod
    def validate_denominator(cls, v):
        if v == 0:
            raise ValueError("Denominator cannot be zero")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"numerator": 10, "denominator": 2},
                {"numerator": 7.5, "denominator": 2.5}
            ]
        }


class MathNumberListParams(BaseModel):
    """Parameters for operations on a list of numbers"""
    numbers: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="List of numbers"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"numbers": [1, 2, 3, 4, 5]},
                {"numbers": [10.5, 20.3, 15.2]}
            ]
        }


class MathRoundParams(BaseModel):
    """Parameters for rounding"""
    number: Union[int, float] = Field(..., description="Number to round")
    decimals: int = Field(default=0, ge=0, le=10, description="Decimal places")

    class Config:
        json_schema_extra = {
            "examples": [
                {"number": 3.14159, "decimals": 2},
                {"number": 10.7, "decimals": 0}
            ]
        }


class MathSingleNumberParams(BaseModel):
    """Parameters for operations on a single number"""
    number: Union[int, float] = Field(..., description="The number")

    class Config:
        json_schema_extra = {
            "examples": [
                {"number": 3.7},
                {"number": -2.3}
            ]
        }


class MathAngleParams(BaseModel):
    """Parameters for angle conversion"""
    angle: float = Field(..., description="Angle value")

    class Config:
        json_schema_extra = {
            "examples": [
                {"angle": 180},
                {"angle": 3.14159}
            ]
        }


class StatsPercentileParams(BaseModel):
    """Parameters for percentile calculation"""
    numbers: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="List of numbers"
    )
    percentile: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentile to calculate (0-100)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"numbers": [1, 2, 3, 4, 5], "percentile": 50},
                {"numbers": [10, 20, 30, 40], "percentile": 75}
            ]
        }


class StatsVarianceParams(BaseModel):
    """Parameters for variance/std dev calculation"""
    numbers: List[Union[int, float]] = Field(
        ...,
        min_length=2,
        description="List of numbers"
    )
    sample: bool = Field(
        default=True,
        description="Calculate sample variance (True) or population variance (False)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"numbers": [2, 4, 6, 8, 10], "sample": True}
            ]
        }


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

    @field_validator('fga')
    @classmethod
    def validate_fga(cls, v, info):
        if 'fgm' in info.data and v < info.data['fgm']:
            raise ValueError("Field goals attempted must be >= field goals made")
        return v

    @field_validator('fta')
    @classmethod
    def validate_fta(cls, v, info):
        if 'ftm' in info.data and v < info.data['ftm']:
            raise ValueError("Free throws attempted must be >= free throws made")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "points": 250, "rebounds": 100, "assists": 80,
                    "steals": 20, "blocks": 15, "fgm": 95, "fga": 200,
                    "ftm": 60, "fta": 75, "turnovers": 40, "minutes": 500
                }
            ]
        }


class NbaTrueShootingParams(BaseModel):
    """Parameters for True Shooting Percentage"""
    points: Union[int, float] = Field(..., ge=0, description="Points scored")
    fga: Union[int, float] = Field(..., ge=0, description="Field goals attempted")
    fta: Union[int, float] = Field(..., ge=0, description="Free throws attempted")

    class Config:
        json_schema_extra = {
            "examples": [
                {"points": 250, "fga": 200, "fta": 75}
            ]
        }


class NbaEffectiveFgParams(BaseModel):
    """Parameters for Effective Field Goal Percentage"""
    fgm: Union[int, float] = Field(..., ge=0, description="Field goals made")
    fga: Union[int, float] = Field(..., ge=0, description="Field goals attempted")
    three_pm: Union[int, float] = Field(..., ge=0, description="Three-pointers made")

    @field_validator('fga')
    @classmethod
    def validate_fga(cls, v, info):
        if 'fgm' in info.data and v < info.data['fgm']:
            raise ValueError("FGA must be >= FGM")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"fgm": 95, "fga": 200, "three_pm": 30}
            ]
        }


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

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "fga": 200, "fta": 75, "turnovers": 40, "minutes": 500,
                    "team_minutes": 4800, "team_fga": 1800,
                    "team_fta": 600, "team_turnovers": 350
                }
            ]
        }


class NbaRatingParams(BaseModel):
    """Parameters for Offensive/Defensive Rating"""
    points: Union[int, float] = Field(..., ge=0, description="Points (scored or allowed)")
    possessions: Union[int, float] = Field(..., gt=0, description="Total possessions")

    class Config:
        json_schema_extra = {
            "examples": [
                {"points": 2500, "possessions": 2200}
            ]
        }


# ============================================================================
# Sprint 6: Advanced Analytics Parameters
# ============================================================================

# Correlation & Regression Parameters

class CorrelationParams(BaseModel):
    """Parameters for correlation calculation"""
    x: List[Union[int, float]] = Field(
        ...,
        min_length=2,
        description="First variable (list of numbers)"
    )
    y: List[Union[int, float]] = Field(
        ...,
        min_length=2,
        description="Second variable (list of numbers)"
    )

    @field_validator('y')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'x' in info.data and len(v) != len(info.data['x']):
            raise ValueError(f"Lists must have same length: x={len(info.data['x'])}, y={len(v)}")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "x": [1, 2, 3, 4, 5],
                    "y": [2, 4, 6, 8, 10]
                }
            ]
        }


class CovarianceParams(BaseModel):
    """Parameters for covariance calculation"""
    x: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="First variable"
    )
    y: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Second variable"
    )
    sample: bool = Field(
        default=True,
        description="Use sample covariance (n-1) if True, population (n) if False"
    )

    @field_validator('y')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'x' in info.data and len(v) != len(info.data['x']):
            raise ValueError(f"Lists must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"x": [1, 2, 3, 4, 5], "y": [2, 4, 5, 4, 5], "sample": True}
            ]
        }


class LinearRegressionParams(BaseModel):
    """Parameters for linear regression"""
    x: List[Union[int, float]] = Field(
        ...,
        min_length=2,
        description="Independent variable"
    )
    y: List[Union[int, float]] = Field(
        ...,
        min_length=2,
        description="Dependent variable"
    )

    @field_validator('y')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'x' in info.data and len(v) != len(info.data['x']):
            raise ValueError("Lists must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "x": [1, 2, 3, 4, 5],
                    "y": [2, 4, 6, 8, 10]
                }
            ]
        }


class PredictParams(BaseModel):
    """Parameters for making predictions with linear model"""
    slope: float = Field(..., description="Model slope (from regression)")
    intercept: float = Field(..., description="Model intercept (from regression)")
    x_values: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="New x values to predict"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "slope": 2.0,
                    "intercept": 1.0,
                    "x_values": [6, 7, 8]
                }
            ]
        }


class CorrelationMatrixParams(BaseModel):
    """Parameters for correlation matrix calculation"""
    data: Dict[str, List[Union[int, float]]] = Field(
        ...,
        description="Dictionary mapping variable names to lists of values"
    )

    @field_validator('data')
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

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "data": {
                        "points": [20, 25, 22, 28],
                        "assists": [5, 7, 6, 8],
                        "rebounds": [8, 6, 7, 5]
                    }
                }
            ]
        }


# Time Series Parameters

class MovingAverageParams(BaseModel):
    """Parameters for moving average calculation"""
    data: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Time series data"
    )
    window: int = Field(
        default=3,
        ge=1,
        description="Window size for moving average"
    )

    @field_validator('window')
    @classmethod
    def validate_window(cls, v, info):
        if 'data' in info.data and v > len(info.data['data']):
            raise ValueError(f"Window ({v}) cannot be larger than data length ({len(info.data['data'])})")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"data": [10, 12, 14, 16, 18, 20], "window": 3}
            ]
        }


class ExponentialMovingAverageParams(BaseModel):
    """Parameters for exponential moving average"""
    data: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Time series data"
    )
    alpha: float = Field(
        default=0.3,
        gt=0,
        le=1,
        description="Smoothing factor (0-1, higher = more weight to recent values)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"data": [10, 12, 14, 16, 18], "alpha": 0.3}
            ]
        }


class TrendDetectionParams(BaseModel):
    """Parameters for trend detection"""
    data: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Time series data"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"data": [10, 12, 15, 17, 20]}
            ]
        }


class PercentChangeParams(BaseModel):
    """Parameters for percentage change calculation"""
    current: Union[int, float] = Field(..., description="Current value")
    previous: Union[int, float] = Field(..., description="Previous value")

    @field_validator('previous')
    @classmethod
    def validate_previous(cls, v):
        if v == 0:
            raise ValueError("Previous value cannot be zero (would divide by zero)")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"current": 120, "previous": 100}
            ]
        }


class GrowthRateParams(BaseModel):
    """Parameters for compound growth rate calculation"""
    start_value: Union[int, float] = Field(..., gt=0, description="Initial value (must be positive)")
    end_value: Union[int, float] = Field(..., gt=0, description="Final value (must be positive)")
    periods: int = Field(..., gt=0, description="Number of time periods")

    class Config:
        json_schema_extra = {
            "examples": [
                {"start_value": 100, "end_value": 150, "periods": 3}
            ]
        }


class VolatilityParams(BaseModel):
    """Parameters for volatility calculation"""
    data: List[Union[int, float]] = Field(
        ...,
        min_length=2,
        description="Time series data"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"data": [100, 102, 98, 101, 99]}
            ]
        }


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
    team_orb: Union[int, float] = Field(..., ge=0, description="Total team offensive rebounds")
    opp_drb: Union[int, float] = Field(..., ge=0, description="Opponent defensive rebounds")

    # Defensive stats
    opp_fgm: Union[int, float] = Field(..., ge=0, description="Opponent field goals made")
    opp_fga: Union[int, float] = Field(..., ge=0, description="Opponent field goals attempted")
    opp_three_pm: Union[int, float] = Field(..., ge=0, description="Opponent three-pointers made")
    opp_tov: Union[int, float] = Field(..., ge=0, description="Opponent turnovers")
    opp_fta: Union[int, float] = Field(..., ge=0, description="Opponent free throw attempts")
    drb: Union[int, float] = Field(..., ge=0, description="Defensive rebounds")
    team_drb: Union[int, float] = Field(..., ge=0, description="Total team defensive rebounds")
    opp_orb: Union[int, float] = Field(..., ge=0, description="Opponent offensive rebounds")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "fgm": 3200, "fga": 7000, "three_pm": 1000,
                    "tov": 1100, "fta": 1800, "orb": 900,
                    "team_orb": 900, "opp_drb": 2800,
                    "opp_fgm": 2900, "opp_fga": 6800, "opp_three_pm": 800,
                    "opp_tov": 1200, "opp_fta": 1600, "drb": 2800,
                    "team_drb": 2800, "opp_orb": 850
                }
            ]
        }


class TurnoverPercentageParams(BaseModel):
    """Parameters for turnover percentage"""
    tov: Union[int, float] = Field(..., ge=0, description="Turnovers")
    fga: Union[int, float] = Field(..., ge=0, description="Field goals attempted")
    fta: Union[int, float] = Field(..., ge=0, description="Free throws attempted")

    class Config:
        json_schema_extra = {
            "examples": [
                {"tov": 250, "fga": 1800, "fta": 600}
            ]
        }


class ReboundPercentageParams(BaseModel):
    """Parameters for rebound percentage"""
    rebounds: Union[int, float] = Field(..., ge=0, description="Player/team rebounds")
    team_rebounds: Union[int, float] = Field(..., ge=0, description="Total team rebounds")
    opp_rebounds: Union[int, float] = Field(..., ge=0, description="Opponent rebounds")

    class Config:
        json_schema_extra = {
            "examples": [
                {"rebounds": 900, "team_rebounds": 900, "opp_rebounds": 2800}
            ]
        }


class AssistPercentageParams(BaseModel):
    """Parameters for assist percentage"""
    assists: Union[int, float] = Field(..., ge=0, description="Player assists")
    minutes: float = Field(..., gt=0, description="Player minutes played")
    team_minutes: float = Field(..., gt=0, description="Team total minutes")
    team_fgm: Union[int, float] = Field(..., ge=0, description="Team field goals made")
    player_fgm: Union[int, float] = Field(default=0, ge=0, description="Player's own field goals made")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "assists": 500, "minutes": 2000, "team_minutes": 19680,
                    "team_fgm": 3200, "player_fgm": 600
                }
            ]
        }


class StealPercentageParams(BaseModel):
    """Parameters for steal percentage"""
    steals: Union[int, float] = Field(..., ge=0, description="Player steals")
    minutes: float = Field(..., gt=0, description="Player minutes played")
    team_minutes: float = Field(..., gt=0, description="Team total minutes")
    opp_possessions: Union[int, float] = Field(..., gt=0, description="Opponent possessions")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "steals": 120, "minutes": 2000,
                    "team_minutes": 19680, "opp_possessions": 8000
                }
            ]
        }


class BlockPercentageParams(BaseModel):
    """Parameters for block percentage"""
    blocks: Union[int, float] = Field(..., ge=0, description="Player blocks")
    minutes: float = Field(..., gt=0, description="Player minutes played")
    team_minutes: float = Field(..., gt=0, description="Team total minutes")
    opp_two_pa: Union[int, float] = Field(..., gt=0, description="Opponent 2-point attempts")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "blocks": 100, "minutes": 2000,
                    "team_minutes": 19680, "opp_two_pa": 5000
                }
            ]
        }


# ============================================================================
# Sprint 7: Machine Learning Parameters
# ============================================================================

# Clustering Parameters

class KMeansClusteringParams(BaseModel):
    """Parameters for K-means clustering"""
    data: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Data points (each row is a sample, each column is a feature)"
    )
    k: int = Field(
        default=3,
        ge=1,
        description="Number of clusters"
    )
    max_iterations: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum iterations"
    )
    tolerance: float = Field(
        default=1e-4,
        gt=0,
        description="Convergence tolerance"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    @field_validator('k')
    @classmethod
    def validate_k(cls, v, info):
        if 'data' in info.data and v > len(info.data['data']):
            raise ValueError(f"k ({v}) cannot exceed number of data points ({len(info.data['data'])})")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "data": [[25, 3, 5], [22, 4, 4], [15, 2, 12]],
                    "k": 2,
                    "max_iterations": 100
                }
            ]
        }


class EuclideanDistanceParams(BaseModel):
    """Parameters for Euclidean distance calculation"""
    point1: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="First point coordinates"
    )
    point2: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Second point coordinates"
    )

    @field_validator('point2')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'point1' in info.data and len(v) != len(info.data['point1']):
            raise ValueError(f"Points must have same dimensions")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"point1": [1, 2, 3], "point2": [4, 5, 6]}
            ]
        }


class CosineSimilarityParams(BaseModel):
    """Parameters for cosine similarity calculation"""
    vector1: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="First vector"
    )
    vector2: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Second vector"
    )

    @field_validator('vector2')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'vector1' in info.data and len(v) != len(info.data['vector1']):
            raise ValueError("Vectors must have same dimensions")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {"vector1": [1, 2, 3], "vector2": [2, 4, 6]}
            ]
        }


class KnnParams(BaseModel):
    """Parameters for K-nearest neighbors"""
    point: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Point to classify"
    )
    data: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Training data points"
    )
    labels: List[Any] = Field(
        ...,
        min_length=1,
        description="Labels for training data"
    )
    k: int = Field(
        default=5,
        ge=1,
        description="Number of neighbors to consider"
    )
    distance_metric: Literal["euclidean", "cosine"] = Field(
        default="euclidean",
        description="Distance metric to use"
    )

    @field_validator('labels')
    @classmethod
    def validate_labels_length(cls, v, info):
        if 'data' in info.data and len(v) != len(info.data['data']):
            raise ValueError("Labels must have same length as data")
        return v

    @field_validator('k')
    @classmethod
    def validate_k(cls, v, info):
        if 'data' in info.data and v > len(info.data['data']):
            raise ValueError(f"k ({v}) cannot exceed number of training points ({len(info.data['data'])})")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "point": [15, 8, 3],
                    "data": [[20, 5, 4], [18, 7, 5], [12, 3, 8]],
                    "labels": ["PG", "SG", "C"],
                    "k": 3
                }
            ]
        }


class HierarchicalClusteringParams(BaseModel):
    """Parameters for hierarchical clustering"""
    data: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Data points to cluster"
    )
    n_clusters: int = Field(
        default=3,
        ge=1,
        description="Number of clusters to form"
    )
    linkage: Literal["single", "complete", "average"] = Field(
        default="average",
        description="Linkage criterion"
    )

    @field_validator('n_clusters')
    @classmethod
    def validate_n_clusters(cls, v, info):
        if 'data' in info.data and v > len(info.data['data']):
            raise ValueError(f"n_clusters ({v}) cannot exceed number of points ({len(info.data['data'])})")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "data": [[25, 5], [22, 6], [15, 12]],
                    "n_clusters": 2,
                    "linkage": "average"
                }
            ]
        }


# Classification Parameters

class LogisticRegressionParams(BaseModel):
    """Parameters for logistic regression training"""
    X_train: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Training features"
    )
    y_train: List[int] = Field(
        ...,
        min_length=1,
        description="Training labels (0 or 1)"
    )
    learning_rate: float = Field(
        default=0.01,
        gt=0,
        le=1,
        description="Learning rate for gradient descent"
    )
    max_iterations: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum training iterations"
    )
    tolerance: float = Field(
        default=1e-4,
        gt=0,
        description="Convergence tolerance"
    )

    @field_validator('y_train')
    @classmethod
    def validate_y_train(cls, v, info):
        if 'X_train' in info.data and len(v) != len(info.data['X_train']):
            raise ValueError("X_train and y_train must have same length")
        # Validate binary labels
        unique_labels = set(v)
        if not unique_labels.issubset({0, 1}):
            raise ValueError(f"y_train must contain only 0 and 1. Found: {unique_labels}")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X_train": [[25, 5, 0.6], [18, 8, 0.55], [30, 4, 0.65]],
                    "y_train": [1, 0, 1],
                    "learning_rate": 0.01
                }
            ]
        }


class LogisticPredictParams(BaseModel):
    """Parameters for logistic regression prediction"""
    X: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Features to predict"
    )
    weights: List[float] = Field(
        ...,
        min_length=1,
        description="Trained weights from logistic_regression"
    )
    threshold: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Classification threshold"
    )
    return_probabilities: bool = Field(
        default=False,
        description="Return probabilities instead of binary predictions"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X": [[28, 6, 0.62]],
                    "weights": [0.1, 0.5, 0.3, 0.2],
                    "threshold": 0.5
                }
            ]
        }


class NaiveBayesTrainParams(BaseModel):
    """Parameters for Naive Bayes training"""
    X_train: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Training features"
    )
    y_train: List[Any] = Field(
        ...,
        min_length=1,
        description="Training labels"
    )

    @field_validator('y_train')
    @classmethod
    def validate_y_train(cls, v, info):
        if 'X_train' in info.data and len(v) != len(info.data['X_train']):
            raise ValueError("X_train and y_train must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X_train": [[198, 88, 18], [206, 95, 22], [213, 110, 15]],
                    "y_train": ["SG", "SF", "C"]
                }
            ]
        }


class NaiveBayesPredictParams(BaseModel):
    """Parameters for Naive Bayes prediction"""
    X: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Features to predict"
    )
    model: Dict[str, Any] = Field(
        ...,
        description="Trained model from naive_bayes_train"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X": [[200, 90, 20]],
                    "model": {"classes": ["PG", "SG"], "class_priors": {}}
                }
            ]
        }


class DecisionTreeTrainParams(BaseModel):
    """Parameters for decision tree training"""
    X_train: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Training features"
    )
    y_train: List[Any] = Field(
        ...,
        min_length=1,
        description="Training labels"
    )
    max_depth: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum tree depth"
    )
    min_samples_split: int = Field(
        default=2,
        ge=2,
        description="Minimum samples required to split"
    )

    @field_validator('y_train')
    @classmethod
    def validate_y_train(cls, v, info):
        if 'X_train' in info.data and len(v) != len(info.data['X_train']):
            raise ValueError("X_train and y_train must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X_train": [[0.62, 115, 108], [0.55, 108, 112]],
                    "y_train": ["Playoffs", "Missed"],
                    "max_depth": 5
                }
            ]
        }


class DecisionTreePredictParams(BaseModel):
    """Parameters for decision tree prediction"""
    X: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Features to predict"
    )
    tree: Dict[str, Any] = Field(
        ...,
        description="Trained tree from decision_tree_train"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X": [[0.58, 110, 110]],
                    "tree": {"type": "split", "feature": 0}
                }
            ]
        }


class RandomForestTrainParams(BaseModel):
    """Parameters for random forest training"""
    X_train: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Training features"
    )
    y_train: List[Any] = Field(
        ...,
        min_length=1,
        description="Training labels"
    )
    n_trees: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of trees in forest"
    )
    max_depth: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum depth per tree"
    )
    min_samples_split: int = Field(
        default=2,
        ge=2,
        description="Minimum samples to split"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    @field_validator('y_train')
    @classmethod
    def validate_y_train(cls, v, info):
        if 'X_train' in info.data and len(v) != len(info.data['X_train']):
            raise ValueError("X_train and y_train must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X_train": [[28, 8, 27], [25, 6, 22]],
                    "y_train": ["MVP", "All-Star"],
                    "n_trees": 50
                }
            ]
        }


class RandomForestPredictParams(BaseModel):
    """Parameters for random forest prediction"""
    X: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Features to predict"
    )
    model: Dict[str, Any] = Field(
        ...,
        description="Trained model from random_forest_train"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X": [[29, 7, 25]],
                    "model": {"trees": [], "n_trees": 50}
                }
            ]
        }


# Anomaly Detection Parameters

class ZScoreOutliersParams(BaseModel):
    """Parameters for Z-score outlier detection"""
    data: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Data points to analyze"
    )
    threshold: float = Field(
        default=3.0,
        gt=0,
        description="Z-score threshold (default 3.0 = 3 standard deviations)"
    )
    labels: Optional[List[Any]] = Field(
        default=None,
        description="Optional labels for data points"
    )

    @field_validator('labels')
    @classmethod
    def validate_labels(cls, v, info):
        if v is not None and 'data' in info.data and len(v) != len(info.data['data']):
            raise ValueError("Labels must have same length as data")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "data": [[25, 5, 5], [22, 6, 4], [50, 12, 15]],
                    "threshold": 3.0
                }
            ]
        }


class IsolationForestParams(BaseModel):
    """Parameters for isolation forest anomaly detection"""
    data: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Data points to analyze"
    )
    n_trees: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Number of isolation trees"
    )
    sample_size: Optional[int] = Field(
        default=None,
        ge=1,
        description="Samples per tree (default: min(256, len(data)))"
    )
    contamination: float = Field(
        default=0.1,
        gt=0,
        lt=0.5,
        description="Expected proportion of outliers"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "data": [[25, 5], [22, 6], [28, 7]],
                    "n_trees": 100,
                    "contamination": 0.1
                }
            ]
        }


class LocalOutlierFactorParams(BaseModel):
    """Parameters for local outlier factor"""
    data: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Data points to analyze"
    )
    k: int = Field(
        default=20,
        ge=1,
        description="Number of neighbors to consider"
    )
    contamination: float = Field(
        default=0.1,
        gt=0,
        lt=0.5,
        description="Expected proportion of outliers"
    )

    @field_validator('k')
    @classmethod
    def validate_k(cls, v, info):
        if 'data' in info.data and v >= len(info.data['data']):
            raise ValueError(f"k ({v}) must be less than number of points ({len(info.data['data'])})")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "data": [[25, 5], [22, 6], [28, 7]],
                    "k": 5,
                    "contamination": 0.1
                }
            ]
        }


# Feature Engineering Parameters

class NormalizeFeaturesParams(BaseModel):
    """Parameters for feature normalization"""
    data: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Data to normalize"
    )
    method: Literal["min-max", "z-score", "robust", "max-abs"] = Field(
        default="min-max",
        description="Normalization method"
    )
    feature_range: Tuple[float, float] = Field(
        default=(0.0, 1.0),
        description="Target range for min-max scaling"
    )

    @field_validator('feature_range')
    @classmethod
    def validate_feature_range(cls, v):
        if v[0] >= v[1]:
            raise ValueError(f"feature_range must be (min, max): {v}")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "data": [[25, 5, 5], [22, 6, 4]],
                    "method": "min-max",
                    "feature_range": [0.0, 1.0]
                }
            ]
        }


class FeatureImportanceParams(BaseModel):
    """Parameters for feature importance calculation"""
    X: List[List[Union[int, float]]] = Field(
        ...,
        min_length=1,
        description="Feature data"
    )
    y: List[Any] = Field(
        ...,
        min_length=1,
        description="True labels"
    )
    model_predictions: List[Any] = Field(
        ...,
        min_length=1,
        description="Baseline predictions"
    )
    n_repeats: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of permutation repeats"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    @field_validator('y')
    @classmethod
    def validate_y(cls, v, info):
        if 'X' in info.data and len(v) != len(info.data['X']):
            raise ValueError("X and y must have same length")
        return v

    @field_validator('model_predictions')
    @classmethod
    def validate_predictions(cls, v, info):
        if 'y' in info.data and len(v) != len(info.data['y']):
            raise ValueError("model_predictions must have same length as y")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "X": [[25, 5], [22, 6]],
                    "y": [1, 0],
                    "model_predictions": [1, 0],
                    "n_repeats": 10
                }
            ]
        }


# ============================================================================
# Sprint 8: Model Evaluation & Validation Parameters
# ============================================================================

# Classification Metrics Parameters

class AccuracyScoreParams(BaseModel):
    """Parameters for accuracy score calculation"""
    y_true: List[Any] = Field(
        ...,
        min_length=1,
        description="True labels"
    )
    y_pred: List[Any] = Field(
        ...,
        min_length=1,
        description="Predicted labels"
    )

    @field_validator('y_pred')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_pred must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": [1, 0, 1, 1, 0],
                    "y_pred": [1, 0, 1, 0, 0]
                }
            ]
        }


class PrecisionRecallF1Params(BaseModel):
    """Parameters for precision, recall, and F1-score calculation"""
    y_true: List[Any] = Field(
        ...,
        min_length=1,
        description="True labels"
    )
    y_pred: List[Any] = Field(
        ...,
        min_length=1,
        description="Predicted labels"
    )
    average: Literal["binary", "macro", "micro", "weighted"] = Field(
        default="binary",
        description="Averaging strategy for multiclass"
    )
    pos_label: Any = Field(
        default=1,
        description="Positive class label (for binary classification)"
    )

    @field_validator('y_pred')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_pred must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": [1, 0, 1, 1, 0, 1],
                    "y_pred": [1, 0, 1, 0, 0, 1],
                    "average": "binary"
                }
            ]
        }


class ConfusionMatrixParams(BaseModel):
    """Parameters for confusion matrix calculation"""
    y_true: List[Any] = Field(
        ...,
        min_length=1,
        description="True labels"
    )
    y_pred: List[Any] = Field(
        ...,
        min_length=1,
        description="Predicted labels"
    )
    pos_label: Any = Field(
        default=1,
        description="Positive class label (for binary classification)"
    )

    @field_validator('y_pred')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_pred must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": [1, 0, 1, 1, 0],
                    "y_pred": [1, 0, 1, 0, 1]
                }
            ]
        }


class RocAucScoreParams(BaseModel):
    """Parameters for ROC-AUC calculation"""
    y_true: List[int] = Field(
        ...,
        min_length=2,
        description="True binary labels (0 or 1)"
    )
    y_scores: List[float] = Field(
        ...,
        min_length=2,
        description="Predicted probabilities or scores"
    )
    num_thresholds: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Number of thresholds for ROC curve"
    )

    @field_validator('y_true')
    @classmethod
    def validate_binary_labels(cls, v):
        unique_labels = set(v)
        if not unique_labels.issubset({0, 1}):
            raise ValueError(f"y_true must contain only 0 and 1. Found: {unique_labels}")
        return v

    @field_validator('y_scores')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_scores must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": [0, 0, 1, 1],
                    "y_scores": [0.1, 0.4, 0.35, 0.8],
                    "num_thresholds": 100
                }
            ]
        }


class ClassificationReportParams(BaseModel):
    """Parameters for classification report"""
    y_true: List[Any] = Field(
        ...,
        min_length=1,
        description="True labels"
    )
    y_pred: List[Any] = Field(
        ...,
        min_length=1,
        description="Predicted labels"
    )

    @field_validator('y_pred')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_pred must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": ["PG", "SG", "PG", "C", "PF"],
                    "y_pred": ["PG", "SG", "SG", "C", "PF"]
                }
            ]
        }


class LogLossParams(BaseModel):
    """Parameters for log loss (cross-entropy) calculation"""
    y_true: List[int] = Field(
        ...,
        min_length=1,
        description="True binary labels (0 or 1)"
    )
    y_pred_proba: List[float] = Field(
        ...,
        min_length=1,
        description="Predicted probabilities"
    )
    eps: float = Field(
        default=1e-15,
        gt=0,
        lt=1,
        description="Small value to clip probabilities (avoid log(0))"
    )

    @field_validator('y_true')
    @classmethod
    def validate_binary_labels(cls, v):
        unique_labels = set(v)
        if not unique_labels.issubset({0, 1}):
            raise ValueError(f"y_true must contain only 0 and 1. Found: {unique_labels}")
        return v

    @field_validator('y_pred_proba')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_pred_proba must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": [1, 0, 1, 0],
                    "y_pred_proba": [0.9, 0.1, 0.8, 0.2]
                }
            ]
        }


# Regression Metrics Parameters

class MseRmseMaeParams(BaseModel):
    """Parameters for MSE, RMSE, and MAE calculation"""
    y_true: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="True values"
    )
    y_pred: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Predicted values"
    )

    @field_validator('y_pred')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_pred must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": [3.0, -0.5, 2.0, 7.0],
                    "y_pred": [2.5, 0.0, 2.0, 8.0]
                }
            ]
        }


class R2ScoreParams(BaseModel):
    """Parameters for R² (coefficient of determination) calculation"""
    y_true: List[Union[int, float]] = Field(
        ...,
        min_length=2,
        description="True values"
    )
    y_pred: List[Union[int, float]] = Field(
        ...,
        min_length=2,
        description="Predicted values"
    )

    @field_validator('y_pred')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_pred must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": [3.0, -0.5, 2.0, 7.0],
                    "y_pred": [2.5, 0.0, 2.0, 8.0]
                }
            ]
        }


class MapeParams(BaseModel):
    """Parameters for Mean Absolute Percentage Error calculation"""
    y_true: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="True values"
    )
    y_pred: List[Union[int, float]] = Field(
        ...,
        min_length=1,
        description="Predicted values"
    )

    @field_validator('y_true')
    @classmethod
    def validate_no_zeros(cls, v):
        if any(val == 0 for val in v):
            raise ValueError("y_true cannot contain zeros (would cause division by zero)")
        return v

    @field_validator('y_pred')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'y_true' in info.data and len(v) != len(info.data['y_true']):
            raise ValueError("y_true and y_pred must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y_true": [100.0, 50.0, 30.0, 20.0],
                    "y_pred": [110.0, 45.0, 35.0, 22.0]
                }
            ]
        }


# Cross-Validation Parameters

class KFoldSplitParams(BaseModel):
    """Parameters for K-fold cross-validation splits"""
    n_samples: int = Field(
        ...,
        ge=2,
        description="Total number of samples"
    )
    n_folds: int = Field(
        default=5,
        ge=2,
        le=20,
        description="Number of folds"
    )
    shuffle: bool = Field(
        default=True,
        description="Whether to shuffle data before splitting"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    @field_validator('n_folds')
    @classmethod
    def validate_n_folds(cls, v, info):
        if 'n_samples' in info.data and v > info.data['n_samples']:
            raise ValueError(f"n_folds ({v}) cannot exceed n_samples ({info.data['n_samples']})")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "n_samples": 100,
                    "n_folds": 5,
                    "shuffle": True
                }
            ]
        }


class StratifiedKFoldSplitParams(BaseModel):
    """Parameters for stratified K-fold cross-validation"""
    y: List[Any] = Field(
        ...,
        min_length=2,
        description="Labels for stratification"
    )
    n_folds: int = Field(
        default=5,
        ge=2,
        le=20,
        description="Number of folds"
    )
    shuffle: bool = Field(
        default=True,
        description="Whether to shuffle data before splitting"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    @field_validator('n_folds')
    @classmethod
    def validate_n_folds(cls, v, info):
        if 'y' in info.data and v > len(info.data['y']):
            raise ValueError(f"n_folds ({v}) cannot exceed number of samples ({len(info.data['y'])})")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "y": [0, 0, 1, 1, 0, 1, 1, 0],
                    "n_folds": 4,
                    "shuffle": True
                }
            ]
        }


class CrossValidateParams(BaseModel):
    """Parameters for cross-validation helper"""
    n_samples: int = Field(
        ...,
        ge=2,
        description="Total number of samples"
    )
    n_folds: int = Field(
        default=5,
        ge=2,
        le=20,
        description="Number of folds"
    )
    stratify: bool = Field(
        default=False,
        description="Use stratified K-fold (requires y labels)"
    )
    y: Optional[List[Any]] = Field(
        default=None,
        description="Labels for stratification (required if stratify=True)"
    )
    shuffle: bool = Field(
        default=True,
        description="Whether to shuffle data"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    @model_validator(mode='after')
    def validate_stratify_requirements(self):
        if self.stratify and self.y is None:
            raise ValueError("y labels required when stratify=True")
        if self.y is not None and len(self.y) != self.n_samples:
            raise ValueError(f"Length of y ({len(self.y)}) must equal n_samples ({self.n_samples})")
        return self

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "n_samples": 100,
                    "n_folds": 5,
                    "stratify": False,
                    "shuffle": True
                }
            ]
        }


# Model Comparison Parameters

class CompareModelsParams(BaseModel):
    """Parameters for comparing multiple models"""
    models: List[Dict[str, Any]] = Field(
        ...,
        min_length=2,
        description="List of models with names and predictions"
    )
    y_true: List[Any] = Field(
        ...,
        min_length=1,
        description="True labels"
    )
    metrics: Optional[List[str]] = Field(
        default=None,
        description="Metrics to compare (defaults to accuracy, precision, recall, f1)"
    )

    @field_validator('models')
    @classmethod
    def validate_models(cls, v):
        for model in v:
            if 'name' not in model or 'predictions' not in model:
                raise ValueError("Each model must have 'name' and 'predictions' keys")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "models": [
                        {"name": "Model A", "predictions": [1, 0, 1, 0]},
                        {"name": "Model B", "predictions": [1, 1, 1, 0]}
                    ],
                    "y_true": [1, 0, 1, 1],
                    "metrics": ["accuracy", "f1"]
                }
            ]
        }


class PairedTTestParams(BaseModel):
    """Parameters for paired t-test"""
    scores_a: List[float] = Field(
        ...,
        min_length=2,
        description="Scores from model A"
    )
    scores_b: List[float] = Field(
        ...,
        min_length=2,
        description="Scores from model B"
    )
    alpha: float = Field(
        default=0.05,
        gt=0,
        lt=1,
        description="Significance level"
    )

    @field_validator('scores_b')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'scores_a' in info.data and len(v) != len(info.data['scores_a']):
            raise ValueError("scores_a and scores_b must have same length")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "scores_a": [0.85, 0.87, 0.82, 0.90, 0.88],
                    "scores_b": [0.80, 0.83, 0.79, 0.85, 0.82],
                    "alpha": 0.05
                }
            ]
        }


# Hyperparameter Tuning Parameters

class GridSearchParams(BaseModel):
    """Parameters for grid search parameter generation"""
    param_grid: Dict[str, List[Any]] = Field(
        ...,
        description="Dictionary mapping parameter names to lists of values to try"
    )
    n_combinations: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of combinations to generate (optional limit)"
    )

    @field_validator('param_grid')
    @classmethod
    def validate_param_grid(cls, v):
        if not v:
            raise ValueError("param_grid cannot be empty")
        for param_name, param_values in v.items():
            if not isinstance(param_values, list) or len(param_values) == 0:
                raise ValueError(f"Parameter '{param_name}' must have at least one value")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "param_grid": {
                        "learning_rate": [0.01, 0.1, 0.5],
                        "max_depth": [3, 5, 7],
                        "n_trees": [10, 50, 100]
                    }
                }
            ]
        }


# ============================================================================
# Helper Functions
# ============================================================================

def validate_params(params_class: type[BaseModel], arguments: Dict[str, Any]) -> BaseModel:
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
