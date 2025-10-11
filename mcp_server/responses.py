"""
Standardized Response Types for MCP Server
Based on best practices from Graphiti MCP implementation
"""

from typing import TypedDict, Literal, Any, Optional
from datetime import datetime
import uuid


class SuccessResponse(TypedDict):
    """Standardized success response"""
    success: Literal[True]
    message: str
    data: dict[str, Any]
    timestamp: str
    request_id: str


class ErrorResponse(TypedDict):
    """Standardized error response"""
    success: Literal[False]
    error: str
    error_type: str
    timestamp: str
    request_id: str
    details: Optional[dict[str, Any]]


def success_response(
    message: str,
    data: dict[str, Any],
    request_id: Optional[str] = None
) -> SuccessResponse:
    """
    Create a standardized success response.
    
    Args:
        message: Human-readable success message
        data: Response data payload
        request_id: Optional request identifier
        
    Returns:
        SuccessResponse with standard format
        
    Example:
        >>> success_response("Query executed", {"rows": 10, "results": [...]})
        {
            "success": True,
            "message": "Query executed",
            "data": {"rows": 10, "results": [...]},
            "timestamp": "2025-10-10T02:45:00.123456Z",
            "request_id": "abc-123"
        }
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id or str(uuid.uuid4())
    }


def error_response(
    error: str,
    error_type: str = "UnknownError",
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None
) -> ErrorResponse:
    """
    Create a standardized error response.
    
    Args:
        error: Human-readable error message
        error_type: Error classification (e.g., ValueError, DatabaseError)
        request_id: Optional request identifier
        details: Optional additional error context
        
    Returns:
        ErrorResponse with standard format
        
    Example:
        >>> error_response("Invalid query", "ValidationError", details={"field": "sql_query"})
        {
            "success": False,
            "error": "Invalid query",
            "error_type": "ValidationError",
            "timestamp": "2025-10-10T02:45:00.123456Z",
            "request_id": "abc-123",
            "details": {"field": "sql_query"}
        }
    """
    return {
        "success": False,
        "error": error,
        "error_type": error_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id or str(uuid.uuid4()),
        "details": details
    }


# Convenience functions for common error types
def validation_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None
) -> ErrorResponse:
    """Create a validation error response"""
    return error_response(error, "ValidationError", request_id, details)


def database_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None
) -> ErrorResponse:
    """Create a database error response"""
    return error_response(error, "DatabaseError", request_id, details)


def s3_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None
) -> ErrorResponse:
    """Create an S3 error response"""
    return error_response(error, "S3Error", request_id, details)


def authentication_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None
) -> ErrorResponse:
    """Create an authentication error response"""
    return error_response(error, "AuthenticationError", request_id, details)


def rate_limit_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None
) -> ErrorResponse:
    """Create a rate limit error response"""
    return error_response(error, "RateLimitError", request_id, details)


def not_found_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None
) -> ErrorResponse:
    """Create a not found error response"""
    return error_response(error, "NotFoundError", request_id, details)


# =============================================================================
# Pydantic Response Models for FastMCP
# =============================================================================

from pydantic import BaseModel, Field
from typing import List


class QueryResult(BaseModel):
    """Response for database queries"""
    columns: List[str] = Field(description="Column names")
    rows: List[List[Any]] = Field(description="Query result rows")
    row_count: int = Field(description="Number of rows returned")
    query: str = Field(description="Executed query (truncated)")
    success: bool = Field(default=True, description="Query execution status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class TableListResult(BaseModel):
    """Response for table listing"""
    tables: List[str] = Field(description="List of table names")
    count: int = Field(description="Number of tables")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class TableSchemaResult(BaseModel):
    """Response for table schema"""
    table_name: str = Field(description="Table name")
    columns: List[dict] = Field(description="Column definitions")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class S3FileResult(BaseModel):
    """Response for S3 file fetch"""
    key: str = Field(description="S3 object key")
    content: str = Field(description="File content")
    size: int = Field(description="File size in bytes")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class S3ListResult(BaseModel):
    """Response for S3 file listing"""
    files: List[str] = Field(description="List of file keys")
    count: int = Field(description="Number of files")
    prefix: str = Field(default="", description="Prefix filter used")
    truncated: bool = Field(default=False, description="Whether results were truncated")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class StandardResponse(BaseModel):
    """Generic standard response"""
    success: bool = Field(description="Success status")
    message: str = Field(description="Response message")
    data: Optional[dict] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PaginatedGamesResult(BaseModel):
    """Response for paginated games listing"""
    games: List[dict] = Field(description="List of games")
    count: int = Field(description="Number of games in this page")
    next_cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    has_more: bool = Field(default=False, description="Whether more results exist")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PaginatedPlayersResult(BaseModel):
    """Response for paginated players listing"""
    players: List[dict] = Field(description="List of players")
    count: int = Field(description="Number of players in this page")
    next_cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    has_more: bool = Field(default=False, description="Whether more results exist")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# Book Response Models
# =============================================================================

class BookListResult(BaseModel):
    """Response for book listing"""
    books: List[dict] = Field(description="List of books with metadata")
    count: int = Field(description="Number of books")
    prefix: str = Field(default="books/", description="Prefix filter used")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BookChunkResult(BaseModel):
    """Response for book chunk reading"""
    book_path: str = Field(description="S3 path to the book")
    content: str = Field(description="Book content (may contain LaTeX formulas)")
    chunk_number: int = Field(description="Current chunk number (0-indexed)")
    chunk_size: int = Field(description="Size of this chunk in characters")
    total_chunks: int = Field(description="Total number of chunks in book")
    has_more: bool = Field(description="Whether more chunks exist")
    metadata: dict = Field(description="Book metadata (size, format, math_content, etc.)")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BookSearchResult(BaseModel):
    """Response for book search"""
    results: List[dict] = Field(description="Search results with excerpts")
    count: int = Field(description="Number of results")
    query: str = Field(description="Search query used")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# EPUB Response Models
# =============================================================================

class EpubMetadataResult(BaseModel):
    """Response for EPUB metadata extraction"""
    book_path: str = Field(description="Path to EPUB file")
    title: Optional[str] = Field(default=None, description="Book title")
    author: Optional[List[str]] = Field(default=None, description="Book authors")
    language: Optional[str] = Field(default=None, description="Book language")
    identifier: Optional[str] = Field(default=None, description="Book identifier (ISBN, etc.)")
    date: Optional[str] = Field(default=None, description="Publication date")
    publisher: Optional[str] = Field(default=None, description="Publisher")
    description: Optional[str] = Field(default=None, description="Book description")
    creator: Optional[List[str]] = Field(default=None, description="Creators")
    contributor: Optional[List[str]] = Field(default=None, description="Contributors")
    subject: Optional[List[str]] = Field(default=None, description="Subjects/tags")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class EpubTocResult(BaseModel):
    """Response for EPUB table of contents"""
    book_path: str = Field(description="Path to EPUB file")
    toc: List[dict] = Field(description="Table of contents entries with title and href")
    chapter_count: int = Field(description="Number of chapters")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class EpubChapterResult(BaseModel):
    """Response for EPUB chapter extraction"""
    book_path: str = Field(description="Path to EPUB file")
    chapter_href: str = Field(description="Chapter location (href)")
    chapter_title: Optional[str] = Field(default=None, description="Chapter title")
    content: str = Field(description="Chapter content")
    format: Literal["html", "markdown", "text"] = Field(description="Content format")
    content_length: int = Field(description="Content length in characters")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# PDF Response Models
# =============================================================================

class PdfMetadataResult(BaseModel):
    """Response for PDF metadata extraction"""
    book_path: str = Field(description="Path to PDF file")
    title: Optional[str] = Field(default=None, description="Document title")
    author: Optional[str] = Field(default=None, description="Document author")
    subject: Optional[str] = Field(default=None, description="Document subject")
    creator: Optional[str] = Field(default=None, description="Creator application")
    producer: Optional[str] = Field(default=None, description="PDF producer")
    creation_date: Optional[str] = Field(default=None, description="Creation date")
    modification_date: Optional[str] = Field(default=None, description="Modification date")
    keywords: Optional[str] = Field(default=None, description="Document keywords")
    page_count: int = Field(description="Number of pages")
    has_toc: bool = Field(description="Whether PDF has table of contents")
    toc_entries: int = Field(description="Number of TOC entries")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PdfTocResult(BaseModel):
    """Response for PDF table of contents"""
    book_path: str = Field(description="Path to PDF file")
    toc: List[dict] = Field(description="TOC entries with level, title, and page number")
    entry_count: int = Field(description="Number of TOC entries")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PdfPageResult(BaseModel):
    """Response for PDF page extraction"""
    book_path: str = Field(description="Path to PDF file")
    page_number: int = Field(description="Page number (0-indexed)")
    content: str = Field(description="Page content")
    format: Literal["text", "html", "markdown"] = Field(description="Content format")
    content_length: int = Field(description="Content length in characters")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PdfPageRangeResult(BaseModel):
    """Response for PDF page range extraction"""
    book_path: str = Field(description="Path to PDF file")
    start_page: int = Field(description="Starting page number (0-indexed)")
    end_page: int = Field(description="Ending page number (0-indexed)")
    page_count: int = Field(description="Number of pages extracted")
    content: str = Field(description="Combined content from all pages")
    format: Literal["text", "html", "markdown"] = Field(description="Content format")
    content_length: int = Field(description="Content length in characters")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PdfChapterResult(BaseModel):
    """Response for PDF chapter extraction"""
    book_path: str = Field(description="Path to PDF file")
    chapter_title: str = Field(description="Chapter title")
    level: int = Field(description="TOC hierarchy level")
    start_page: int = Field(description="Starting page (1-indexed)")
    end_page: int = Field(description="Ending page (1-indexed)")
    page_count: int = Field(description="Number of pages in chapter")
    content: str = Field(description="Chapter content")
    format: Literal["text", "html", "markdown"] = Field(description="Content format")
    content_length: int = Field(description="Content length in characters")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PdfSearchResult(BaseModel):
    """Response for PDF text search"""
    book_path: str = Field(description="Path to PDF file")
    query: str = Field(description="Search query")
    results: List[dict] = Field(description="Search results with page, match, context, and position")
    match_count: int = Field(description="Number of matches found")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# Math & Stats Response Models
# =============================================================================

class MathOperationResult(BaseModel):
    """Response for mathematical operations"""
    operation: str = Field(description="Operation performed (add, subtract, multiply, etc.)")
    result: float = Field(description="Operation result")
    inputs: dict = Field(description="Input values used")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class StatsResult(BaseModel):
    """Response for statistical calculations"""
    statistic: str = Field(description="Statistic calculated (mean, median, variance, etc.)")
    result: Any = Field(description="Statistic result (may be float, int, list, or dict)")
    input_count: int = Field(description="Number of input values")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class NbaMetricResult(BaseModel):
    """Response for NBA-specific metrics"""
    metric: str = Field(description="Metric calculated (PER, TS%, eFG%, etc.)")
    result: float = Field(description="Metric value")
    inputs: dict = Field(description="Input statistics used")
    interpretation: Optional[str] = Field(default=None, description="What the metric means")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")
