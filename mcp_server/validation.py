"""Request validation and sanitization using Pydantic"""

from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional, List, Dict, Any
import re
import html
from datetime import datetime


# SQL Injection Prevention
def sanitize_sql_string(value: str) -> str:
    """Sanitize string for SQL (use with parameterized queries)"""
    # Remove dangerous SQL keywords/characters
    dangerous = [
        "--",
        ";",
        "/*",
        "*/",
        "xp_",
        "sp_",
        "exec",
        "execute",
        "drop",
        "delete",
        "truncate",
    ]
    sanitized = value
    for danger in dangerous:
        sanitized = sanitized.replace(danger, "")
    return sanitized.strip()


def sanitize_html(value: str) -> str:
    """Escape HTML to prevent XSS"""
    return html.escape(value)


class PlayerQuery(BaseModel):
    """Validate player query parameters"""

    player_name: str = Field(..., min_length=1, max_length=100)
    season: Optional[int] = Field(None, ge=1946, le=2100)
    team: Optional[str] = Field(None, max_length=50)

    @validator("player_name")
    def sanitize_name(cls, v):
        return sanitize_html(sanitize_sql_string(v))

    @validator("team")
    def sanitize_team(cls, v):
        if v:
            return sanitize_html(sanitize_sql_string(v))
        return v


class GameQuery(BaseModel):
    """Validate game query parameters"""

    game_id: Optional[int] = Field(None, gt=0)
    season: Optional[int] = Field(None, ge=1946, le=2100)
    team_name: Optional[str] = Field(None, max_length=50)
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)

    @validator("team_name")
    def sanitize_team_name(cls, v):
        if v:
            return sanitize_html(sanitize_sql_string(v))
        return v


class StatsQuery(BaseModel):
    """Validate statistics query"""

    metric: str = Field(..., regex=r"^[a-zA-Z_]+$")
    season: Optional[int] = Field(None, ge=1946, le=2100)
    min_games: int = Field(10, ge=0, le=82)
    limit: int = Field(100, ge=1, le=5000)


class DatabaseQuery(BaseModel):
    """Validate raw database query (DANGEROUS - admin only)"""

    query: str = Field(..., max_length=10000)
    params: Optional[Dict[str, Any]] = None
    max_rows: int = Field(1000, ge=1, le=10000)

    @validator("query")
    def validate_query_safety(cls, v):
        # Only allow SELECT statements
        if not v.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries allowed")
        # Block dangerous patterns
        dangerous = [
            "DROP",
            "DELETE",
            "TRUNCATE",
            "UPDATE",
            "INSERT",
            "ALTER",
            "CREATE",
        ]
        upper_query = v.upper()
        for danger in dangerous:
            if danger in upper_query:
                raise ValueError(f"Dangerous keyword '{danger}' not allowed")
        return v


class BookReadRequest(BaseModel):
    """Validate book read request"""

    book_path: str = Field(..., regex=r"^books/[a-zA-Z0-9_\-./]+\.(pdf|epub|txt)$")
    page_number: Optional[int] = Field(None, ge=0)
    chunk_size: int = Field(50000, ge=1000, le=200000)


class MLModelRequest(BaseModel):
    """Validate ML model prediction request"""

    features: Dict[str, float] = Field(..., min_items=1, max_items=100)
    model_name: str = Field(..., regex=r"^[a-zA-Z0-9_\-]+$", max_length=100)

    @validator("features")
    def validate_features(cls, v):
        # Check for NaN/Inf values
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Feature '{key}' must be numeric")
            if value != value:  # NaN check
                raise ValueError(f"Feature '{key}' is NaN")
            if abs(value) == float("inf"):
                raise ValueError(f"Feature '{key}' is infinite")
        return v


def validate_request(data: Dict[str, Any], model_class: type[BaseModel]) -> BaseModel:
    """
    Validate request data against a Pydantic model

    Args:
        data: Request data dictionary
        model_class: Pydantic model class to validate against

    Returns:
        Validated model instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        # Log validation error
        print(f"❌ Validation error: {e}")
        raise


# Rate limiting decorator
def rate_limit(max_calls: int, window_seconds: int):
    """Decorator for rate limiting (placeholder - implement with Redis)"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # TODO: Implement actual rate limiting with Redis
            return func(*args, **kwargs)

        return wrapper

    return decorator
