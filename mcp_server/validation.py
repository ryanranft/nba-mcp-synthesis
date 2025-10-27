"""
Request validation and sanitization using Pydantic

**Phase 10A Week 2 - Agent 4: Data Validation & Quality**
Enhanced with NBA-specific validators, schema validation, and bulk validation utilities.
"""

from pydantic import field_validator, BaseModel, Field, ValidationError, ConfigDict
from typing import Optional, List, Dict, Any, Union
import re
import html
from datetime import datetime
import json
import pandas as pd


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

    @field_validator("player_name")
    @classmethod
    def sanitize_name(cls, v):
        return sanitize_html(sanitize_sql_string(v))

    @field_validator("team")
    @classmethod
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

    @field_validator("team_name")
    @classmethod
    def sanitize_team_name(cls, v):
        if v:
            return sanitize_html(sanitize_sql_string(v))
        return v


class StatsQuery(BaseModel):
    """Validate statistics query"""

    metric: str = Field(..., pattern=r"^[a-zA-Z_]+$")
    season: Optional[int] = Field(None, ge=1946, le=2100)
    min_games: int = Field(10, ge=0, le=82)
    limit: int = Field(100, ge=1, le=5000)


class DatabaseQuery(BaseModel):
    """Validate raw database query (DANGEROUS - admin only)"""

    query: str = Field(..., max_length=10000)
    params: Optional[Dict[str, Any]] = None
    max_rows: int = Field(1000, ge=1, le=10000)

    @field_validator("query")
    @classmethod
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

    book_path: str = Field(..., pattern=r"^books/[a-zA-Z0-9_\-./]+\.(pdf|epub|txt)$")
    page_number: Optional[int] = Field(None, ge=0)
    chunk_size: int = Field(50000, ge=1000, le=200000)


class MLModelRequest(BaseModel):
    """Validate ML model prediction request"""

    features: Dict[str, float] = Field(..., min_length=1, max_length=100)
    model_name: str = Field(..., pattern=r"^[a-zA-Z0-9_\-]+$", max_length=100)

    @field_validator("features")
    @classmethod
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


# NBA-Specific Validators (Phase 10A Week 2 - Agent 4)


class PlayerStatsModel(BaseModel):
    """
    Validate NBA player statistics.

    **Phase 10A Week 2 - Agent 4:** NBA-specific data validation.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    player_id: int = Field(..., gt=0, description="Unique player identifier")
    player_name: str = Field(..., min_length=1, max_length=100)
    season: int = Field(..., ge=1946, le=2100, description="NBA season year")
    team_abbreviation: Optional[str] = Field(None, max_length=3, pattern=r"^[A-Z]{3}$")
    games_played: int = Field(..., ge=0, le=82, description="Games played in season")
    minutes_per_game: float = Field(
        ..., ge=0.0, le=48.0, description="Minutes per game"
    )
    points_per_game: float = Field(..., ge=0.0, le=50.0, description="Points per game")
    rebounds_per_game: float = Field(
        ..., ge=0.0, le=25.0, description="Rebounds per game"
    )
    assists_per_game: float = Field(
        ..., ge=0.0, le=20.0, description="Assists per game"
    )
    field_goal_percentage: Optional[float] = Field(None, ge=0.0, le=1.0)
    three_point_percentage: Optional[float] = Field(None, ge=0.0, le=1.0)
    free_throw_percentage: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator("player_name")
    @classmethod
    def sanitize_player_name(cls, v):
        return sanitize_html(sanitize_sql_string(v))

    @field_validator(
        "field_goal_percentage", "three_point_percentage", "free_throw_percentage"
    )
    @classmethod
    def validate_percentage(cls, v):
        if v is not None:
            if v < 0.0 or v > 1.0:
                raise ValueError("Percentage must be between 0.0 and 1.0")
        return v


class GameDataModel(BaseModel):
    """
    Validate NBA game data.

    **Phase 10A Week 2 - Agent 4:** NBA-specific game validation.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    game_id: int = Field(..., gt=0, description="Unique game identifier")
    season: int = Field(..., ge=1946, le=2100)
    game_date: datetime = Field(..., description="Game date and time")
    home_team: str = Field(..., min_length=1, max_length=50)
    away_team: str = Field(..., min_length=1, max_length=50)
    home_score: int = Field(..., ge=0, le=200, description="Home team score")
    away_score: int = Field(..., ge=0, le=200, description="Away team score")
    overtime: bool = Field(default=False, description="Was game in overtime")
    attendance: Optional[int] = Field(None, ge=0, le=30000)

    @field_validator("home_team", "away_team")
    @classmethod
    def sanitize_team_name(cls, v):
        return sanitize_html(sanitize_sql_string(v))

    @field_validator("away_team")
    @classmethod
    def validate_teams_different(cls, v, info):
        # Note: In Pydantic V2, we use info.data instead of values
        if "home_team" in info.data and v == info.data["home_team"]:
            raise ValueError("Home and away teams must be different")
        return v


class TeamDataModel(BaseModel):
    """
    Validate NBA team data.

    **Phase 10A Week 2 - Agent 4:** NBA-specific team validation.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    team_id: int = Field(..., gt=0, description="Unique team identifier")
    team_name: str = Field(..., min_length=1, max_length=100)
    team_abbreviation: str = Field(
        ..., min_length=2, max_length=3, pattern=r"^[A-Z]{2,3}$"
    )
    conference: str = Field(..., pattern=r"^(Eastern|Western)$")
    division: str = Field(
        ..., pattern=r"^(Atlantic|Central|Southeast|Northwest|Pacific|Southwest)$"
    )
    season: int = Field(..., ge=1946, le=2100)
    wins: int = Field(..., ge=0, le=82)
    losses: int = Field(..., ge=0, le=82)
    win_percentage: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator("team_name")
    @classmethod
    def sanitize_name(cls, v):
        return sanitize_html(sanitize_sql_string(v))

    @field_validator("win_percentage")
    @classmethod
    def validate_win_percentage(cls, v, info):
        if v is not None and "wins" in info.data and "losses" in info.data:
            wins = info.data["wins"]
            losses = info.data["losses"]
            total_games = wins + losses
            if total_games > 0:
                expected_pct = wins / total_games
                # Allow small floating point tolerance
                if abs(v - expected_pct) > 0.001:
                    raise ValueError(
                        f"Win percentage {v} doesn't match wins/losses: "
                        f"expected {expected_pct:.3f}"
                    )
        return v


# Schema Validation Utilities (Phase 10A Week 2 - Agent 4)


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against JSON Schema.

    **Phase 10A Week 2 - Agent 4:** Schema validation utility.

    Args:
        data: Data to validate
        schema: JSON Schema definition

    Returns:
        List of validation error messages (empty if valid)

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {"type": "string"},
        ...         "age": {"type": "integer", "minimum": 0}
        ...     },
        ...     "required": ["name", "age"]
        ... }
        >>> errors = validate_json_schema({"name": "John", "age": 25}, schema)
        >>> len(errors)
        0
    """
    try:
        import jsonschema

        jsonschema.validate(instance=data, schema=schema)
        return []
    except ImportError:
        return ["jsonschema package not installed. Run: pip install jsonschema"]
    except jsonschema.ValidationError as e:
        return [str(e.message)]
    except jsonschema.SchemaError as e:
        return [f"Invalid schema: {e.message}"]


def validate_dataframe_schema(
    df: pd.DataFrame,
    expected_columns: List[str],
    column_types: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Validate DataFrame schema.

    **Phase 10A Week 2 - Agent 4:** DataFrame schema validation.

    Args:
        df: DataFrame to validate
        expected_columns: List of required column names
        column_types: Optional dict of {column_name: expected_dtype}

    Returns:
        List of validation error messages (empty if valid)

    Example:
        >>> df = pd.DataFrame({"name": ["John"], "age": [25]})
        >>> errors = validate_dataframe_schema(
        ...     df,
        ...     expected_columns=["name", "age"],
        ...     column_types={"name": "object", "age": "int64"}
        ... )
        >>> len(errors)
        0
    """
    errors = []

    # Check required columns
    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {sorted(missing_cols)}")

    # Check column types
    if column_types:
        for col, expected_type in column_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if actual_type != expected_type:
                    errors.append(
                        f"Column '{col}' has type '{actual_type}', expected '{expected_type}'"
                    )

    return errors


# Bulk Validation Utilities (Phase 10A Week 2 - Agent 4)


class ValidationResult(BaseModel):
    """Result of a validation operation"""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None


def validate_batch(
    records: List[Dict[str, Any]], model_class: type[BaseModel]
) -> Dict[str, Any]:
    """
    Validate a batch of records.

    **Phase 10A Week 2 - Agent 4:** Bulk validation utility.

    Args:
        records: List of records to validate
        model_class: Pydantic model class for validation

    Returns:
        Dictionary with validation summary:
        - total: Total records processed
        - valid: Number of valid records
        - invalid: Number of invalid records
        - results: List of ValidationResult objects

    Example:
        >>> records = [
        ...     {"player_id": 1, "player_name": "John", "season": 2024, "games_played": 82},
        ...     {"player_id": -1, "player_name": "Jane", "season": 2024, "games_played": 100},
        ... ]
        >>> result = validate_batch(records, PlayerStatsModel)
        >>> result["valid"]
        1
    """
    results = []
    valid_count = 0
    invalid_count = 0

    for i, record in enumerate(records):
        try:
            validated = model_class(**record)
            results.append(
                ValidationResult(
                    is_valid=True,
                    validated_data=validated.model_dump(),
                )
            )
            valid_count += 1
        except ValidationError as e:
            error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            results.append(
                ValidationResult(
                    is_valid=False,
                    errors=error_messages,
                    validated_data=record,
                )
            )
            invalid_count += 1

    return {
        "total": len(records),
        "valid": valid_count,
        "invalid": invalid_count,
        "results": results,
    }


def aggregate_validation_results(
    results: List[ValidationResult],
) -> Dict[str, Any]:
    """
    Aggregate validation results into summary statistics.

    **Phase 10A Week 2 - Agent 4:** Result aggregation utility.

    Args:
        results: List of ValidationResult objects

    Returns:
        Dictionary with aggregated statistics:
        - total: Total records
        - valid_count: Number of valid records
        - invalid_count: Number of invalid records
        - success_rate: Percentage of valid records
        - common_errors: Most frequent errors

    Example:
        >>> results = [
        ...     ValidationResult(is_valid=True),
        ...     ValidationResult(is_valid=False, errors=["Invalid value"]),
        ... ]
        >>> summary = aggregate_validation_results(results)
        >>> summary["success_rate"]
        50.0
    """
    total = len(results)
    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = total - valid_count

    # Count error frequencies
    error_counts: Dict[str, int] = {}
    for result in results:
        for error in result.errors:
            error_counts[error] = error_counts.get(error, 0) + 1

    # Sort errors by frequency
    common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]  # Top 10

    success_rate = (valid_count / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "success_rate": success_rate,
        "common_errors": [
            {"error": err, "count": count} for err, count in common_errors
        ],
    }
