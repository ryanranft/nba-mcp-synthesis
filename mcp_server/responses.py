"""
Standardized Response Types for MCP Server
Based on best practices from Graphiti MCP implementation
"""

from typing import TypedDict, Literal, Any, Optional, Dict, List, Tuple
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
    message: str, data: dict[str, Any], request_id: Optional[str] = None
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
        "request_id": request_id or str(uuid.uuid4()),
    }


def error_response(
    error: str,
    error_type: str = "UnknownError",
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
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
        "details": details,
    }


# Convenience functions for common error types
def validation_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> ErrorResponse:
    """Create a validation error response"""
    return error_response(error, "ValidationError", request_id, details)


def database_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> ErrorResponse:
    """Create a database error response"""
    return error_response(error, "DatabaseError", request_id, details)


def s3_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> ErrorResponse:
    """Create an S3 error response"""
    return error_response(error, "S3Error", request_id, details)


def authentication_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> ErrorResponse:
    """Create an authentication error response"""
    return error_response(error, "AuthenticationError", request_id, details)


def rate_limit_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> ErrorResponse:
    """Create a rate limit error response"""
    return error_response(error, "RateLimitError", request_id, details)


def not_found_error(
    error: str,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
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
    metadata: dict = Field(
        description="Book metadata (size, format, math_content, etc.)"
    )
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
    identifier: Optional[str] = Field(
        default=None, description="Book identifier (ISBN, etc.)"
    )
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
    modification_date: Optional[str] = Field(
        default=None, description="Modification date"
    )
    keywords: Optional[str] = Field(default=None, description="Document keywords")
    page_count: int = Field(description="Number of pages")
    has_toc: bool = Field(description="Whether PDF has table of contents")
    toc_entries: int = Field(description="Number of TOC entries")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PdfTocResult(BaseModel):
    """Response for PDF table of contents"""

    book_path: str = Field(description="Path to PDF file")
    toc: List[dict] = Field(
        description="TOC entries with level, title, and page number"
    )
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
    results: List[dict] = Field(
        description="Search results with page, match, context, and position"
    )
    match_count: int = Field(description="Number of matches found")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# Math & Stats Response Models
# =============================================================================


class MathOperationResult(BaseModel):
    """Response for mathematical operations"""

    operation: str = Field(
        description="Operation performed (add, subtract, multiply, etc.)"
    )
    result: float = Field(description="Operation result")
    inputs: dict = Field(description="Input values used")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class StatsResult(BaseModel):
    """Response for statistical calculations"""

    statistic: str = Field(
        description="Statistic calculated (mean, median, variance, etc.)"
    )
    result: Any = Field(
        description="Statistic result (may be float, int, list, or dict)"
    )
    input_count: int = Field(description="Number of input values")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class NbaMetricResult(BaseModel):
    """Response for NBA-specific metrics"""

    metric: str = Field(description="Metric calculated (PER, TS%, eFG%, etc.)")
    result: float = Field(description="Metric value")
    inputs: dict = Field(description="Input statistics used")
    interpretation: Optional[str] = Field(
        default=None, description="What the metric means"
    )
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class FormulaAnalysisResult(BaseModel):
    """Response for formula analysis operations"""

    operation: str = Field(description="Operation performed")
    result: dict = Field(description="Analysis results")
    inputs: dict = Field(description="Input parameters")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class FormulaExtractionResult(BaseModel):
    """Response for formula extraction operations"""

    operation: str = Field(description="Operation performed")
    extracted_formulas: List[dict] = Field(
        description="List of extracted formulas with metadata"
    )
    total_formulas: int = Field(description="Total number of formulas extracted")
    pdf_path: str = Field(description="Path to the PDF file processed")
    pages_processed: List[int] = Field(description="Pages that were processed")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class LaTeXConversionResult(BaseModel):
    """Response for LaTeX to SymPy conversion"""

    operation: str = Field(description="Operation performed")
    latex_input: str = Field(description="Original LaTeX formula")
    sympy_output: Optional[str] = Field(description="Converted SymPy expression")
    conversion_successful: bool = Field(description="Whether conversion was successful")
    error_message: Optional[str] = Field(
        default=None, description="Error message if conversion failed"
    )
    success: bool = Field(default=True, description="Success status")


class FormulaStructureResult(BaseModel):
    """Response for formula structure analysis"""

    operation: str = Field(description="Operation performed")
    formula: str = Field(description="Analyzed formula")
    structure_analysis: dict = Field(description="Detailed structure analysis")
    suggested_tool: str = Field(description="Recommended algebraic tool")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# ============================================================================
# Phase 2.3: Interactive Formula Builder Responses
# ============================================================================


class FormulaBuilderValidationResult(BaseModel):
    """Response for formula builder validation"""

    operation: str = Field(description="Operation performed")
    formula: str = Field(description="Validated formula")
    validation_level: str = Field(description="Validation level used")
    is_valid: bool = Field(description="Whether formula is valid")
    errors: List[str] = Field(description="List of validation errors")
    warnings: List[str] = Field(description="List of validation warnings")
    suggestions: List[str] = Field(description="List of improvement suggestions")
    confidence: float = Field(description="Validation confidence score")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class FormulaBuilderSuggestionResult(BaseModel):
    """Response for formula completion suggestions"""

    operation: str = Field(description="Operation performed")
    partial_formula: str = Field(description="Partial formula provided")
    context: str = Field(description="Context for suggestions")
    suggestions: List[str] = Field(description="List of completion suggestions")
    suggestion_count: int = Field(description="Number of suggestions provided")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class FormulaBuilderPreviewResult(BaseModel):
    """Response for formula preview generation"""

    operation: str = Field(description="Operation performed")
    formula: str = Field(description="Formula string")
    latex: Optional[str] = Field(description="LaTeX representation")
    simplified: Optional[str] = Field(description="Simplified LaTeX")
    calculated_value: Optional[float] = Field(description="Calculated result")
    variables: List[str] = Field(description="Variables in formula")
    error: Optional[str] = Field(description="Error message if preview failed")
    success: bool = Field(default=True, description="Success status")


class FormulaBuilderTemplateResult(BaseModel):
    """Response for formula template operations"""

    operation: str = Field(description="Operation performed")
    templates: List[dict] = Field(description="List of available templates")
    template_count: int = Field(description="Number of templates returned")
    category: Optional[str] = Field(description="Category filter applied")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class FormulaBuilderCreateResult(BaseModel):
    """Response for creating formula from template"""

    operation: str = Field(description="Operation performed")
    template_name: str = Field(description="Template used")
    formula: str = Field(description="Original template formula")
    substituted_formula: str = Field(description="Formula with substituted values")
    result: float = Field(description="Calculated result")
    variables_used: Dict[str, float] = Field(description="Variable values used")
    description: str = Field(description="Template description")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class FormulaBuilderExportResult(BaseModel):
    """Response for formula export"""

    operation: str = Field(description="Operation performed")
    formula: str = Field(description="Original formula")
    format_type: str = Field(description="Export format used")
    exported_content: str = Field(description="Exported formula content")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# Phase 3.1: Interactive Formula Playground Responses
class PlaygroundSessionResult(BaseModel):
    """Response for playground session operations"""

    success: bool
    session_id: Optional[str] = None
    session: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PlaygroundFormulaResult(BaseModel):
    """Response for playground formula operations"""

    success: bool
    formula_entry: Optional[Dict[str, Any]] = None
    session_updated: bool = False
    error: Optional[str] = None
    warnings: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None


class PlaygroundVariablesResult(BaseModel):
    """Response for playground variable operations"""

    success: bool
    updated_variables: Optional[Dict[str, float]] = None
    session_updated: bool = False
    errors: Optional[Dict[str, str]] = None
    message: Optional[str] = None


class PlaygroundResultsResult(BaseModel):
    """Response for playground calculation results"""

    success: bool
    results: Optional[Dict[str, Any]] = None
    variables_used: Optional[Dict[str, float]] = None
    error: Optional[str] = None


class PlaygroundVisualizationsResult(BaseModel):
    """Response for playground visualizations"""

    success: bool
    visualizations: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class PlaygroundRecommendationsResult(BaseModel):
    """Response for playground recommendations"""

    success: bool
    recommendations: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class PlaygroundShareResult(BaseModel):
    """Response for playground sharing"""

    success: bool
    share_token: Optional[str] = None
    share_url: Optional[str] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class PlaygroundExperimentResult(BaseModel):
    """Response for playground experiment creation"""

    success: bool
    experiment: Optional[Dict[str, Any]] = None
    experiment_id: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Phase 3.2: Advanced Visualization Engine Response Models
# ============================================================================


class VisualizationGenerateResult(BaseModel):
    """Response for visualization generation"""

    success: bool
    visualization_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class VisualizationExportResult(BaseModel):
    """Response for visualization export"""

    success: bool
    format: Optional[str] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


class VisualizationTemplateResult(BaseModel):
    """Response for visualization templates"""

    success: bool
    templates: Optional[List[Dict[str, Any]]] = None
    template: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class VisualizationConfigResult(BaseModel):
    """Response for visualization configuration"""

    success: bool
    config: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DataPointResult(BaseModel):
    """Response for data point creation"""

    success: bool
    data_point: Optional[Dict[str, Any]] = None
    data_point_id: Optional[str] = None
    error: Optional[str] = None


class DatasetResult(BaseModel):
    """Response for dataset creation"""

    success: bool
    dataset: Optional[Dict[str, Any]] = None
    dataset_id: Optional[str] = None
    data_points_count: Optional[int] = None
    error: Optional[str] = None


# ============================================================================
# Phase 3.3: Formula Validation System Response Models
# ============================================================================


class FormulaValidationResult(BaseModel):
    """Response for formula validation"""

    success: bool
    report: Optional[Dict[str, Any]] = None
    report_id: Optional[str] = None
    overall_status: Optional[str] = None
    overall_score: Optional[float] = None
    validations: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    recommendations: Optional[List[str]] = None
    error: Optional[str] = None


class FormulaReferenceResult(BaseModel):
    """Response for formula reference operations"""

    success: bool
    reference: Optional[Dict[str, Any]] = None
    formula_id: Optional[str] = None
    references: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class ValidationReportResult(BaseModel):
    """Response for validation report retrieval"""

    success: bool
    report: Optional[Dict[str, Any]] = None
    reports: Optional[List[Dict[str, Any]]] = None
    report_id: Optional[str] = None
    error: Optional[str] = None


class ValidationComparisonResult(BaseModel):
    """Response for validation comparison"""

    success: bool
    comparison: Optional[Dict[str, Any]] = None
    formula_ids: Optional[List[str]] = None
    comparison_type: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class ValidationRulesResult(BaseModel):
    """Response for validation rules management"""

    success: bool
    rules: Optional[Dict[str, Any]] = None
    updated_rules: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# Phase 3.4: Multi-Book Formula Comparison Response Models
# ============================================================================


class FormulaComparisonResult(BaseModel):
    """Response for formula comparison"""

    success: bool
    comparison: Optional[Dict[str, Any]] = None
    comparison_id: Optional[str] = None
    formula_id: Optional[str] = None
    versions: Optional[List[Dict[str, Any]]] = None
    variations: Optional[List[Dict[str, Any]]] = None
    overall_similarity: Optional[float] = None
    primary_version: Optional[Dict[str, Any]] = None
    recommended_version: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    error: Optional[str] = None


class FormulaVersionResult(BaseModel):
    """Response for formula version operations"""

    success: bool
    version: Optional[Dict[str, Any]] = None
    version_id: Optional[str] = None
    versions: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class FormulaSourceResult(BaseModel):
    """Response for formula source operations"""

    success: bool
    source: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class FormulaEvolutionResult(BaseModel):
    """Response for formula evolution analysis"""

    success: bool
    evolution: Optional[Dict[str, Any]] = None
    formula_id: Optional[str] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    key_changes: Optional[List[str]] = None
    current_consensus: Optional[Dict[str, Any]] = None
    evolution_summary: Optional[str] = None
    error: Optional[str] = None


class FormulaRecommendationResult(BaseModel):
    """Response for formula recommendations"""

    success: bool
    recommendations: Optional[List[Dict[str, Any]]] = None
    formula_id: Optional[str] = None
    recommended_version: Optional[Dict[str, Any]] = None
    criteria: Optional[List[str]] = None
    context: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Time Series Analysis Results (Phase 10A Agent 8 Module 1)
# =============================================================================


class StationarityTestResult(BaseModel):
    """Response for stationarity testing (ADF/KPSS tests)"""

    test_statistic: float = Field(description="Test statistic value")
    p_value: float = Field(description="P-value for hypothesis test")
    critical_values: Dict[str, float] = Field(
        description="Critical values at different significance levels"
    )
    is_stationary: bool = Field(description="Whether series is stationary")
    test_type: str = Field(description="Type of test performed (adf or kpss)")
    lags_used: Optional[int] = Field(default=None, description="Number of lags used")
    observations: Optional[int] = Field(
        default=None, description="Number of observations"
    )
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(
        description="Recommended next steps for analysis"
    )
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class DecompositionResult(BaseModel):
    """Response for time series decomposition"""

    trend: List[Optional[float]] = Field(description="Trend component values")
    seasonal: List[Optional[float]] = Field(description="Seasonal component values")
    residual: List[Optional[float]] = Field(description="Residual component values")
    model: str = Field(description="Decomposition model (additive/multiplicative)")
    period: Optional[int] = Field(default=None, description="Seasonal period")
    trend_direction: str = Field(
        description="Trend direction (increasing/decreasing/stable)"
    )
    trend_slope: float = Field(description="Slope of trend component")
    trend_strength: float = Field(description="R-squared of trend fit (0-1)")
    seasonal_strength: float = Field(description="Strength of seasonality (0-1)")
    interpretation: str = Field(description="Human-readable interpretation")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ARIMAModelResult(BaseModel):
    """Response for ARIMA model fitting"""

    order: Tuple[int, int, int] = Field(description="ARIMA order (p, d, q)")
    seasonal_order: Optional[Tuple[int, int, int, int]] = Field(
        default=None, description="Seasonal ARIMA order (P, D, Q, s)"
    )
    aic: float = Field(description="Akaike Information Criterion (lower is better)")
    bic: float = Field(description="Bayesian Information Criterion (lower is better)")
    fitted_values: List[float] = Field(description="In-sample fitted values")
    residuals: List[float] = Field(description="Model residuals")
    model_type: str = Field(description="Model type (ARIMA or SARIMA)")
    success_message: str = Field(description="Success message with model details")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ForecastResult(BaseModel):
    """Response for ARIMA forecasting"""

    forecast: List[float] = Field(description="Point forecasts")
    lower_bound: List[float] = Field(description="Lower confidence interval bound")
    upper_bound: List[float] = Field(description="Upper confidence interval bound")
    confidence_level: float = Field(description="Confidence level (e.g., 0.95)")
    model_order: Tuple[int, int, int] = Field(
        description="ARIMA order used for forecasting"
    )
    steps: int = Field(description="Number of periods forecasted")
    success_message: str = Field(description="Success message with forecast details")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class AutocorrelationResult(BaseModel):
    """Response for autocorrelation analysis"""

    acf_values: List[float] = Field(description="Autocorrelation function values")
    pacf_values: List[float] = Field(
        description="Partial autocorrelation function values"
    )
    ljung_box_pvalue: float = Field(description="Ljung-Box test p-value")
    has_autocorrelation: bool = Field(
        description="Whether significant autocorrelation detected"
    )
    significant_lags_acf: List[int] = Field(
        description="Lags with significant autocorrelation"
    )
    significant_lags_pacf: List[int] = Field(
        description="Lags with significant partial autocorrelation"
    )
    arima_suggestions: Dict[str, Any] = Field(
        description="Suggested ARIMA parameters based on ACF/PACF"
    )
    interpretation: str = Field(description="Human-readable interpretation")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# Panel Data Analysis Results (Phase 10A Agent 8 Module 2)
# =============================================================================


class PanelDiagnosticsResult(BaseModel):
    """Response for panel data structure diagnostics."""

    is_balanced: bool = Field(description="Whether panel is balanced")
    n_entities: int = Field(description="Number of entities (players/teams)")
    n_timeperiods: int = Field(description="Number of time periods")
    n_obs: int = Field(description="Total number of observations")
    min_periods: int = Field(description="Minimum periods per entity")
    max_periods: int = Field(description="Maximum periods per entity")
    mean_periods: float = Field(description="Average periods per entity")
    balance_ratio: float = Field(
        description="Ratio of actual to potential observations"
    )
    recommendations: List[str] = Field(description="Analysis recommendations")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PooledOLSResult(BaseModel):
    """Response for pooled OLS regression."""

    coefficients: Dict[str, float] = Field(description="Coefficient estimates")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    t_stats: Dict[str, float] = Field(description="t-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    r_squared: float = Field(description="R-squared value")
    f_statistic: Optional[float] = Field(
        default=None, description="F-statistic for overall significance"
    )
    f_pvalue: Optional[float] = Field(
        default=None, description="P-value for F-statistic"
    )
    n_obs: int = Field(description="Number of observations")
    n_entities: int = Field(description="Number of entities")
    n_timeperiods: int = Field(description="Number of time periods")
    model_type: str = Field(default="pooled_ols", description="Model type")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class FixedEffectsResult(BaseModel):
    """Response for fixed effects regression."""

    coefficients: Dict[str, float] = Field(description="Coefficient estimates")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    t_stats: Dict[str, float] = Field(description="t-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    r_squared: float = Field(description="Overall R-squared")
    r_squared_within: Optional[float] = Field(
        default=None, description="Within R-squared"
    )
    r_squared_between: Optional[float] = Field(
        default=None, description="Between R-squared"
    )
    f_statistic: Optional[float] = Field(default=None, description="F-statistic")
    f_pvalue: Optional[float] = Field(
        default=None, description="P-value for F-statistic"
    )
    n_obs: int = Field(description="Number of observations")
    n_entities: int = Field(description="Number of entities")
    n_timeperiods: int = Field(description="Number of time periods")
    entity_effects_included: bool = Field(description="Whether entity effects included")
    time_effects_included: bool = Field(description="Whether time effects included")
    model_type: str = Field(default="fixed_effects", description="Model type")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class RandomEffectsResult(BaseModel):
    """Response for random effects regression."""

    coefficients: Dict[str, float] = Field(description="Coefficient estimates")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    t_stats: Dict[str, float] = Field(description="t-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    r_squared: float = Field(description="Overall R-squared")
    r_squared_within: Optional[float] = Field(
        default=None, description="Within R-squared"
    )
    r_squared_between: Optional[float] = Field(
        default=None, description="Between R-squared"
    )
    r_squared_overall: Optional[float] = Field(
        default=None, description="Overall R-squared (GLS)"
    )
    f_statistic: Optional[float] = Field(default=None, description="F-statistic")
    f_pvalue: Optional[float] = Field(
        default=None, description="P-value for F-statistic"
    )
    n_obs: int = Field(description="Number of observations")
    n_entities: int = Field(description="Number of entities")
    n_timeperiods: int = Field(description="Number of time periods")
    model_type: str = Field(default="random_effects", description="Model type")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class HausmanTestResult(BaseModel):
    """Response for Hausman specification test."""

    statistic: float = Field(description="Hausman test statistic (chi-squared)")
    p_value: float = Field(description="P-value for test")
    reject_re: bool = Field(
        description="Whether to reject random effects (use FE instead)"
    )
    fe_coefficients: Dict[str, float] = Field(description="Fixed effects estimates")
    re_coefficients: Dict[str, float] = Field(description="Random effects estimates")
    coefficient_differences: Dict[str, float] = Field(
        description="Differences between FE and RE"
    )
    recommendation: str = Field(description="Which model to use")
    interpretation: str = Field(description="Human-readable interpretation")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class FirstDifferenceResult(BaseModel):
    """Response for first difference regression."""

    coefficients: Dict[str, float] = Field(description="Coefficient estimates")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    t_stats: Dict[str, float] = Field(description="t-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    r_squared: float = Field(description="R-squared value")
    f_statistic: Optional[float] = Field(default=None, description="F-statistic")
    f_pvalue: Optional[float] = Field(
        default=None, description="P-value for F-statistic"
    )
    n_obs: int = Field(description="Number of observations (after differencing)")
    n_entities: int = Field(description="Number of entities")
    n_timeperiods: int = Field(
        description="Number of time periods (after differencing)"
    )
    model_type: str = Field(default="first_difference", description="Model type")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# ============================================================================
# Phase 10A - Agent 8: Advanced Econometrics Result Classes
# Module 3: Bayesian Analysis (7 results)
# Module 4A: Causal Inference (6 results)
# Module 4B: Survival Analysis (6 results)
# Module 4C: Advanced Time Series (4 results)
# Module 4D: Econometric Suite (4 results)
# Total: 27 new result classes
# ============================================================================


# ============================================================================
# Module 3: Bayesian Analysis Result Classes
# ============================================================================


class BayesianLinearRegressionResult(BaseModel):
    """Response for Bayesian linear regression."""

    posterior_mean: Dict[str, float] = Field(description="Posterior mean coefficients")
    posterior_std: Dict[str, float] = Field(description="Posterior standard deviations")
    credible_intervals: Dict[str, Dict[str, float]] = Field(description="Credible intervals (lower, upper)")
    convergence_diagnostics: Dict[str, Any] = Field(description="MCMC convergence diagnostics")
    model_fit: Dict[str, float] = Field(description="Model fit statistics (marginal likelihood, DIC, etc.)")
    n_samples: int = Field(description="Number of posterior samples drawn")
    prior_specification: Dict[str, Any] = Field(description="Prior distribution specifications used")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BayesianHierarchicalModelResult(BaseModel):
    """Response for Bayesian hierarchical/multilevel model."""

    fixed_effects: Dict[str, float] = Field(description="Fixed effect posterior means")
    fixed_effects_std: Dict[str, float] = Field(description="Fixed effect posterior std devs")
    random_effects: Dict[str, Dict[str, float]] = Field(description="Random effects by group")
    group_variances: Dict[str, float] = Field(description="Between-group variance components")
    residual_variance: float = Field(description="Within-group residual variance")
    credible_intervals: Dict[str, Dict[str, float]] = Field(description="Credible intervals")
    convergence_diagnostics: Dict[str, Any] = Field(description="Rhat, n_eff diagnostics")
    n_samples: int = Field(description="Number of MCMC samples")
    n_chains: int = Field(description="Number of parallel chains")
    n_groups: int = Field(description="Number of groups/clusters")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BayesianModelComparisonResult(BaseModel):
    """Response for Bayesian model comparison."""

    model_weights: Dict[str, float] = Field(description="Model posterior probabilities")
    comparison_table: List[Dict[str, Any]] = Field(description="Model comparison statistics")
    best_model: str = Field(description="Model with highest posterior probability")
    waic_scores: Optional[Dict[str, float]] = Field(default=None, description="WAIC scores by model")
    loo_scores: Optional[Dict[str, float]] = Field(default=None, description="LOO-CV scores by model")
    bayes_factors: Optional[Dict[str, float]] = Field(default=None, description="Bayes factors relative to best model")
    n_models: int = Field(description="Number of models compared")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BayesianCredibleIntervalsResult(BaseModel):
    """Response for Bayesian credible intervals computation."""

    credible_intervals: Dict[str, Dict[str, float]] = Field(description="Intervals by parameter (lower, upper)")
    interval_type: str = Field(description="Type of interval (hdi or equal_tailed)")
    credible_level: float = Field(description="Credibility level (e.g., 0.95)")
    posterior_means: Dict[str, float] = Field(description="Posterior mean for each parameter")
    posterior_medians: Dict[str, float] = Field(description="Posterior median for each parameter")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class MCMCDiagnosticsResult(BaseModel):
    """Response for MCMC convergence diagnostics."""

    rhat_values: Dict[str, float] = Field(description="Gelman-Rubin statistics by parameter")
    n_eff_values: Dict[str, float] = Field(description="Effective sample sizes by parameter")
    autocorrelation: Optional[Dict[str, List[float]]] = Field(default=None, description="Autocorrelation by parameter")
    geweke_scores: Optional[Dict[str, float]] = Field(default=None, description="Geweke convergence test scores")
    all_converged: bool = Field(description="Whether all parameters converged (Rhat < 1.1)")
    convergence_summary: str = Field(description="Summary of convergence status")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PosteriorPredictiveCheckResult(BaseModel):
    """Response for posterior predictive checks."""

    observed_statistics: Dict[str, float] = Field(description="Test statistics from observed data")
    replicated_statistics: Dict[str, List[float]] = Field(description="Test statistics from posterior predictive replications")
    p_values: Dict[str, float] = Field(description="Bayesian p-values for each test statistic")
    test_passed: Dict[str, bool] = Field(description="Whether each test indicates good fit")
    overall_fit_assessment: str = Field(description="Overall model fit assessment")
    n_replications: int = Field(description="Number of posterior predictive replications")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BayesianUpdatingResult(BaseModel):
    """Response for sequential Bayesian updating."""

    updated_posterior: Dict[str, Any] = Field(description="Updated posterior distribution parameters")
    posterior_mean: Dict[str, float] = Field(description="Updated posterior means")
    posterior_std: Dict[str, float] = Field(description="Updated posterior standard deviations")
    prior_mean: Dict[str, float] = Field(description="Prior means before update")
    information_gain: Dict[str, float] = Field(description="KL divergence from prior to posterior")
    n_samples: int = Field(description="Number of posterior samples")
    n_data_points: int = Field(description="Number of new data points used")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# ============================================================================
# Module 4A: Causal Inference Result Classes
# ============================================================================


class InstrumentalVariablesResult(BaseModel):
    """Response for instrumental variables estimation."""

    coefficients: Dict[str, float] = Field(description="Second-stage coefficient estimates")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    t_stats: Dict[str, float] = Field(description="t-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    first_stage_fstat: float = Field(description="First-stage F-statistic")
    weak_instruments: bool = Field(description="Whether instruments appear weak (F < 10)")
    overid_test_stat: Optional[float] = Field(default=None, description="Overidentification test statistic")
    overid_pvalue: Optional[float] = Field(default=None, description="Overidentification test p-value")
    endogeneity_test_stat: Optional[float] = Field(default=None, description="Durbin-Wu-Hausman endogeneity test statistic")
    endogeneity_pvalue: Optional[float] = Field(default=None, description="Endogeneity test p-value")
    n_instruments: int = Field(description="Number of instruments used")
    method: str = Field(description="Estimation method (2sls, liml, gmm)")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class RegressionDiscontinuityResult(BaseModel):
    """Response for regression discontinuity design."""

    treatment_effect: float = Field(description="Estimated treatment effect at cutoff")
    std_error: float = Field(description="Standard error of treatment effect")
    t_stat: float = Field(description="t-statistic")
    p_value: float = Field(description="p-value")
    confidence_interval: Tuple[float, float] = Field(description="Confidence interval (lower, upper)")
    bandwidth: float = Field(description="Bandwidth used for local estimation")
    n_obs_left: int = Field(description="Observations below cutoff")
    n_obs_right: int = Field(description="Observations above cutoff")
    polynomial_order: int = Field(description="Polynomial order used")
    continuity_tests: Dict[str, float] = Field(description="Tests for continuity of covariates at cutoff")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class DifferenceInDifferencesResult(BaseModel):
    """Response for difference-in-differences estimation."""

    treatment_effect: float = Field(description="Estimated average treatment effect on treated (ATT)")
    std_error: float = Field(description="Standard error (clustered if applicable)")
    t_stat: float = Field(description="t-statistic")
    p_value: float = Field(description="p-value")
    confidence_interval: Tuple[float, float] = Field(description="Confidence interval")
    pre_treatment_trend: Optional[float] = Field(default=None, description="Pre-treatment trend coefficient")
    parallel_trends_test_pvalue: Optional[float] = Field(default=None, description="Parallel trends test p-value")
    parallel_trends_satisfied: bool = Field(description="Whether parallel trends assumption appears satisfied")
    n_treated: int = Field(description="Number of treated units")
    n_control: int = Field(description="Number of control units")
    n_pre_periods: int = Field(description="Number of pre-treatment periods")
    n_post_periods: int = Field(description="Number of post-treatment periods")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class SyntheticControlResult(BaseModel):
    """Response for synthetic control method."""

    treatment_effect: float = Field(description="Average treatment effect on treated unit")
    time_varying_effects: Dict[str, float] = Field(description="Treatment effect by time period")
    synthetic_weights: Dict[str, float] = Field(description="Weights on donor units")
    pre_treatment_rmse: float = Field(description="RMSE in pre-treatment fit")
    placebo_pvalue: Optional[float] = Field(default=None, description="P-value from placebo tests")
    n_donors: int = Field(description="Number of donor units used")
    n_pre_periods: int = Field(description="Number of pre-treatment periods")
    n_post_periods: int = Field(description="Number of post-treatment periods")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class PropensityScoreMatchingResult(BaseModel):
    """Response for propensity score matching."""

    treatment_effect: float = Field(description="Average treatment effect on treated (ATT)")
    std_error: float = Field(description="Standard error")
    t_stat: float = Field(description="t-statistic")
    p_value: float = Field(description="p-value")
    confidence_interval: Tuple[float, float] = Field(description="Confidence interval")
    n_matched: int = Field(description="Number of successfully matched treated units")
    n_unmatched: int = Field(description="Number of unmatched treated units")
    balance_statistics: Dict[str, Dict[str, float]] = Field(description="Standardized mean differences before/after matching")
    common_support_violated: bool = Field(description="Whether common support assumption violated")
    matching_method: str = Field(description="Matching method used")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class MediationAnalysisResult(BaseModel):
    """Response for causal mediation analysis."""

    direct_effect: float = Field(description="Average direct effect (ADE)")
    indirect_effect: float = Field(description="Average causal mediation effect (ACME)")
    total_effect: float = Field(description="Total effect")
    proportion_mediated: float = Field(description="Proportion of effect mediated")
    direct_effect_ci: Tuple[float, float] = Field(description="Direct effect confidence interval")
    indirect_effect_ci: Tuple[float, float] = Field(description="Indirect effect confidence interval")
    n_bootstrap: int = Field(description="Number of bootstrap replications")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# ============================================================================
# Module 4B: Survival Analysis Result Classes
# ============================================================================


class KaplanMeierResult(BaseModel):
    """Response for Kaplan-Meier survival estimation."""

    survival_function: Dict[str, float] = Field(description="Survival probabilities by time")
    median_survival: Optional[float] = Field(default=None, description="Median survival time")
    confidence_intervals: Dict[str, Tuple[float, float]] = Field(description="CI for survival function")
    n_events: int = Field(description="Number of events observed")
    n_censored: int = Field(description="Number of censored observations")
    n_at_risk: Dict[str, int] = Field(description="Number at risk by time")
    log_rank_test_stat: Optional[float] = Field(default=None, description="Log-rank test statistic (if groups compared)")
    log_rank_pvalue: Optional[float] = Field(default=None, description="Log-rank test p-value")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class CoxProportionalHazardsResult(BaseModel):
    """Response for Cox proportional hazards regression."""

    hazard_ratios: Dict[str, float] = Field(description="Hazard ratios (exp(coefficients))")
    coefficients: Dict[str, float] = Field(description="Log hazard ratios")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    z_stats: Dict[str, float] = Field(description="z-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    confidence_intervals: Dict[str, Tuple[float, float]] = Field(description="Confidence intervals for hazard ratios")
    concordance_index: float = Field(description="Concordance index (C-index)")
    log_likelihood: float = Field(description="Partial log-likelihood")
    aic: float = Field(description="Akaike Information Criterion")
    proportional_hazards_test_pvalue: Optional[float] = Field(default=None, description="Test for proportional hazards assumption")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ParametricSurvivalResult(BaseModel):
    """Response for parametric survival models."""

    coefficients: Dict[str, float] = Field(description="Regression coefficients")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    z_stats: Dict[str, float] = Field(description="z-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    shape_parameter: Optional[float] = Field(default=None, description="Shape parameter (e.g., Weibull)")
    scale_parameter: Optional[float] = Field(default=None, description="Scale parameter")
    distribution: str = Field(description="Assumed distribution (weibull, exponential, etc.)")
    log_likelihood: float = Field(description="Log-likelihood")
    aic: float = Field(description="AIC")
    bic: float = Field(description="BIC")
    median_survival: Optional[float] = Field(default=None, description="Median survival time")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class CompetingRisksResult(BaseModel):
    """Response for competing risks analysis."""

    cumulative_incidence: Dict[str, Dict[str, float]] = Field(description="CIF by event type and time")
    subdistribution_hazards: Dict[str, float] = Field(description="Subdistribution hazard ratios")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    z_stats: Dict[str, float] = Field(description="z-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    event_of_interest: int = Field(description="Event type analyzed")
    n_events_by_type: Dict[str, int] = Field(description="Number of events by type")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class RecurrentEventsResult(BaseModel):
    """Response for recurrent events analysis."""

    coefficients: Dict[str, float] = Field(description="Regression coefficients")
    hazard_ratios: Dict[str, float] = Field(description="Hazard ratios")
    std_errors: Dict[str, float] = Field(description="Standard errors (robust)")
    z_stats: Dict[str, float] = Field(description="z-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    model_type: str = Field(description="Recurrent event model (pwp, ag, wlw)")
    total_events: int = Field(description="Total number of events")
    subjects_with_events: int = Field(description="Number of subjects with at least one event")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class TimeVaryingCovariatesResult(BaseModel):
    """Response for survival models with time-varying covariates."""

    hazard_ratios: Dict[str, float] = Field(description="Hazard ratios for time-varying covariates")
    coefficients: Dict[str, float] = Field(description="Log hazard ratios")
    std_errors: Dict[str, float] = Field(description="Standard errors")
    z_stats: Dict[str, float] = Field(description="z-statistics")
    p_values: Dict[str, float] = Field(description="p-values")
    time_varying_vars: List[str] = Field(description="List of time-varying covariate names")
    n_intervals: int = Field(description="Number of time intervals in counting process format")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# ============================================================================
# Module 4C: Advanced Time Series Result Classes
# ============================================================================


class KalmanFilterResult(BaseModel):
    """Response for Kalman filter state-space estimation."""

    filtered_states: List[Dict[str, float]] = Field(description="Filtered state estimates by time")
    smoothed_states: Optional[List[Dict[str, float]]] = Field(default=None, description="Smoothed state estimates (if smoother applied)")
    state_covariances: List[List[List[float]]] = Field(description="State covariance matrices by time")
    innovations: List[Dict[str, float]] = Field(description="One-step-ahead prediction errors")
    log_likelihood: float = Field(description="Model log-likelihood")
    aic: float = Field(description="AIC")
    bic: float = Field(description="BIC")
    parameters: Dict[str, Any] = Field(description="Estimated state-space matrices")
    forecasts: Optional[List[Dict[str, float]]] = Field(default=None, description="Out-of-sample forecasts")
    diagnostics: Dict[str, Any] = Field(description="Innovation statistics and diagnostics")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class DynamicFactorModelResult(BaseModel):
    """Response for dynamic factor model."""

    factors: List[Dict[str, float]] = Field(description="Extracted latent factors by time")
    loadings: Dict[str, Dict[str, float]] = Field(description="Factor loadings by variable")
    factor_covariance: List[List[float]] = Field(description="Factor innovation covariance matrix")
    idiosyncratic_variances: Dict[str, float] = Field(description="Variable-specific error variances")
    variance_explained: Dict[str, float] = Field(description="Variance explained by each factor")
    total_variance_explained: float = Field(description="Total variance explained by all factors")
    factor_ar_coefficients: List[List[List[float]]] = Field(description="AR coefficient matrices for factor dynamics")
    method: str = Field(description="Estimation method (ml, pc, 2step)")
    fit_statistics: Dict[str, float] = Field(description="Log-likelihood, AIC, BIC")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class MarkovSwitchingModelResult(BaseModel):
    """Response for Markov-switching regression model."""

    regime_probabilities: List[Dict[str, float]] = Field(description="Smoothed regime probabilities by time")
    regime_sequence: Dict[str, str] = Field(description="Most likely regime at each time (Viterbi path)")
    transition_matrix: Dict[str, Dict[str, float]] = Field(description="Regime transition probability matrix")
    expected_durations: Dict[str, float] = Field(description="Expected duration in each regime")
    regime_parameters: Dict[str, Dict[str, Any]] = Field(description="Parameters for each regime (mean, variance, etc.)")
    regime_statistics: Dict[str, Dict[str, Any]] = Field(description="Summary statistics by regime")
    fit_statistics: Dict[str, float] = Field(description="Log-likelihood, AIC, BIC")
    specification: Dict[str, Any] = Field(description="Model specification")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class StructuralTimeSeriesResult(BaseModel):
    """Response for structural time series decomposition."""

    components: Dict[str, Dict[str, float]] = Field(description="Extracted components (level, trend, seasonal, cycle) by time")
    component_variances: Dict[str, float] = Field(description="Variance of each component's innovations")
    fitted_values: Dict[str, float] = Field(description="Model-fitted values by time")
    residuals: Dict[str, float] = Field(description="Irregular component (residuals) by time")
    diagnostics: Dict[str, float] = Field(description="Model fit diagnostics (R², AIC, BIC)")
    specification: Dict[str, Any] = Field(description="Model specification (components, periods, stochastic flags)")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# ============================================================================
# Module 4D: Econometric Suite Result Classes
# ============================================================================


class AutoDetectEconometricMethodResult(BaseModel):
    """Response for automatic econometric method detection."""

    recommended_method: str = Field(description="Primary recommended method")
    alternative_methods: List[str] = Field(description="Alternative methods to consider")
    method_rationale: str = Field(description="Explanation for recommendation")
    confidence_score: float = Field(description="Confidence in recommendation (0-1)")
    data_diagnostics: Dict[str, Any] = Field(description="Detected data characteristics")
    implementation_guidance: Dict[str, Any] = Field(description="How to use the recommended method")
    prerequisite_checks: List[Dict[str, str]] = Field(description="Required validation steps")
    method_comparison: Dict[str, str] = Field(description="Explanation of method suitability")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class AutoAnalyzeEconometricDataResult(BaseModel):
    """Response for comprehensive automated econometric analysis."""

    primary_results: Dict[str, Any] = Field(description="Results from primary method")
    alternative_results: Dict[str, Dict[str, Any]] = Field(description="Results from alternative methods")
    robustness_checks: Dict[str, Any] = Field(description="Robustness test results")
    meta_analysis: Dict[str, Any] = Field(description="Cross-method synthesis")
    diagnostics: Dict[str, Any] = Field(description="Comprehensive diagnostic suite")
    recommendations: List[str] = Field(description="Interpretation and next steps")
    summary: Dict[str, Any] = Field(description="Overall summary statistics")
    interpretation: str = Field(description="Human-readable interpretation")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class CompareEconometricMethodsResult(BaseModel):
    """Response for comparing results across econometric methods."""

    coefficient_comparison: Dict[str, Any] = Field(description="Side-by-side coefficient estimates")
    fit_comparison: Dict[str, Any] = Field(description="Model fit statistics comparison")
    diagnostic_comparison: Dict[str, Any] = Field(description="Diagnostic test comparison")
    consensus_estimates: Dict[str, float] = Field(description="Weighted/averaged coefficient estimates")
    disagreement_analysis: Dict[str, Any] = Field(description="Where methods diverge significantly")
    recommendation: str = Field(description="Which method(s) to trust most")
    summary: Dict[str, Any] = Field(description="Comparison summary")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class EconometricModelAveragingResult(BaseModel):
    """Response for econometric model averaging."""

    averaged_coefficients: Dict[str, float] = Field(description="Model-averaged coefficient estimates")
    averaged_standard_errors: Dict[str, float] = Field(description="Model-averaged standard errors")
    confidence_intervals: Dict[str, Dict[str, float]] = Field(description="Adjusted confidence intervals")
    model_weights: Dict[str, float] = Field(description="Weight assigned to each model")
    averaged_predictions: Dict[str, float] = Field(description="Combined predictions by observation")
    model_inclusion_probabilities: Dict[str, float] = Field(description="Probability each variable matters")
    performance_metrics: Dict[str, float] = Field(description="MSE, RMSE, MAE, R²")
    individual_model_performance: Dict[str, Dict[str, float]] = Field(description="Performance by model")
    summary: Dict[str, Any] = Field(description="Model averaging summary")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: List[str] = Field(description="Recommended next steps")
    success: bool = Field(default=True, description="Success status")
    error: Optional[str] = Field(default=None, description="Error message if failed")
