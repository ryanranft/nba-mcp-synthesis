"""
Custom Exception Classes for NBA MCP Server

Provides detailed error context for better debugging and user feedback.
Based on best practices from ebook-mcp implementation.
"""

from typing import Optional


class BookProcessingError(Exception):
    """
    Base exception for book processing errors with detailed context.

    Attributes:
        message: Human-readable error message
        file_path: Path to the file being processed
        operation: Operation being performed when error occurred
        original_error: Original exception if wrapped
    """

    def __init__(
        self,
        message: str,
        file_path: str,
        operation: str,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.file_path = file_path
        self.operation = operation
        self.original_error = original_error

        # Build detailed error message
        error_msg = f"{message} (file: {file_path}, operation: {operation})"
        if original_error:
            error_msg += f" - Original error: {type(original_error).__name__}: {str(original_error)}"

        super().__init__(error_msg)


class EpubProcessingError(BookProcessingError):
    """
    Exception for EPUB-specific processing errors.

    Raised when:
    - EPUB file cannot be parsed
    - TOC extraction fails
    - Chapter extraction fails
    - Invalid EPUB structure
    """
    pass


class PdfProcessingError(BookProcessingError):
    """
    Exception for PDF-specific processing errors.

    Raised when:
    - PDF file cannot be parsed
    - TOC extraction fails
    - Page/chapter extraction fails
    - Invalid PDF structure
    """
    pass


class S3AccessError(BookProcessingError):
    """
    Exception for S3 access errors.

    Raised when:
    - S3 object not found
    - Permission denied
    - Network errors
    - Bucket not accessible
    """
    pass


class ChunkingError(BookProcessingError):
    """
    Exception for chunking errors.

    Raised when:
    - Invalid chunk size
    - Chunk number out of range
    - Content cannot be chunked
    """
    pass


class MathDetectionError(Exception):
    """
    Exception for math content detection errors.

    Raised when:
    - LaTeX parsing fails
    - Invalid math content
    - Detection algorithm error
    """

    def __init__(self, message: str, content_preview: Optional[str] = None):
        self.message = message
        self.content_preview = content_preview

        error_msg = f"Math detection error: {message}"
        if content_preview:
            error_msg += f"\nContent preview: {content_preview[:100]}..."

        super().__init__(error_msg)


class RateLimitError(Exception):
    """
    Exception for rate limit violations.

    Raised when:
    - Too many requests in time window
    - API quota exceeded
    """

    def __init__(
        self,
        message: str,
        max_requests: int,
        per_seconds: int,
        retry_after: Optional[int] = None
    ):
        self.message = message
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.retry_after = retry_after or per_seconds

        error_msg = f"{message} - Limit: {max_requests} requests per {per_seconds}s. "
        error_msg += f"Retry after {self.retry_after}s."

        super().__init__(error_msg)


class ValidationError(Exception):
    """
    Exception for parameter validation errors.

    Raised when:
    - Invalid parameters provided
    - Required parameters missing
    - Parameters out of range
    """

    def __init__(self, message: str, field_name: Optional[str] = None, value: Optional[any] = None):
        self.message = message
        self.field_name = field_name
        self.value = value

        error_msg = f"Validation error: {message}"
        if field_name:
            error_msg += f" (field: {field_name}"
            if value is not None:
                error_msg += f", value: {value}"
            error_msg += ")"

        super().__init__(error_msg)


# Convenience functions for creating common errors
def file_not_found_error(file_path: str, operation: str) -> BookProcessingError:
    """Create a FileNotFoundError wrapped in BookProcessingError"""
    return BookProcessingError(
        f"File not found: {file_path}",
        file_path,
        operation,
        FileNotFoundError(file_path)
    )


def invalid_format_error(file_path: str, operation: str, expected_format: str) -> BookProcessingError:
    """Create an error for invalid file format"""
    return BookProcessingError(
        f"Invalid format. Expected: {expected_format}",
        file_path,
        operation
    )


def chapter_not_found_error(file_path: str, chapter_id: str) -> BookProcessingError:
    """Create an error for chapter not found"""
    return BookProcessingError(
        f"Chapter '{chapter_id}' not found",
        file_path,
        "chapter_extraction"
    )


def s3_bucket_error(bucket: str, key: str, operation: str) -> S3AccessError:
    """Create an S3 bucket access error"""
    return S3AccessError(
        f"Cannot access S3 bucket: {bucket}",
        f"s3://{bucket}/{key}",
        operation
    )
