#!/usr/bin/env python3
"""
Security Module - Production Hardening
Implements rate limiting, request validation, timeout enforcement,
SQL injection prevention, and other security measures.
"""

import re
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==============================================================================
# Configuration Classes
# ==============================================================================

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # Allow burst of requests
    enabled: bool = True


@dataclass
class SecurityConfig:
    """Master security configuration"""
    # Rate limiting
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

    # Request validation
    max_request_size_bytes: int = 1_048_576  # 1MB
    max_sql_query_length: int = 10_000
    max_file_read_size: int = 10_485_760  # 10MB

    # Timeouts
    default_timeout_seconds: float = 30.0
    max_timeout_seconds: float = 120.0

    # SQL injection prevention
    forbidden_sql_keywords: Set[str] = field(default_factory=lambda: {
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE',
        'ALTER', 'CREATE', 'EXEC', 'EXECUTE', 'GRANT',
        'REVOKE', 'MERGE', 'REPLACE'
    })
    allowed_sql_keywords: Set[str] = field(default_factory=lambda: {
        'SELECT', 'EXPLAIN', 'SHOW', 'DESCRIBE', 'DESC', 'WITH'
    })

    # Path traversal prevention
    allowed_file_extensions: Set[str] = field(default_factory=lambda: {
        '.py', '.sql', '.json', '.yaml', '.yml', '.md',
        '.txt', '.csv', '.log'
    })
    forbidden_path_patterns: List[str] = field(default_factory=lambda: [
        r'\.\.',  # Parent directory
        r'~',     # Home directory
        r'/etc/', # System files
        r'/root/', # Root home
        r'\.env', # Environment files
        r'\.git', # Git files
        r'__pycache__'
    ])

    # IP blocking (for future use)
    enable_ip_blocking: bool = False
    blocked_ips: Set[str] = field(default_factory=set)
    max_failed_requests: int = 10


# ==============================================================================
# Rate Limiter
# ==============================================================================

class RateLimiter:
    """
    Token bucket rate limiter with per-client tracking
    Prevents abuse by limiting request rate per client/IP
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.client_buckets: Dict[str, Dict[str, Any]] = defaultdict(self._create_bucket)
        self._lock = asyncio.Lock()

    def _create_bucket(self) -> Dict[str, Any]:
        """Create new token bucket for client"""
        return {
            'tokens': self.config.burst_size,
            'last_update': time.time(),
            'minute_count': 0,
            'minute_start': time.time(),
            'hour_count': 0,
            'hour_start': time.time()
        }

    async def check_rate_limit(self, client_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is within rate limit

        Args:
            client_id: Unique client identifier (IP, user ID, etc.)

        Returns:
            (allowed, message) - True if allowed, message if denied
        """
        if not self.config.enabled:
            return True, None

        async with self._lock:
            bucket = self.client_buckets[client_id]
            now = time.time()

            # Refill tokens based on time elapsed
            elapsed = now - bucket['last_update']
            tokens_to_add = elapsed * (self.config.requests_per_minute / 60.0)
            bucket['tokens'] = min(
                self.config.burst_size,
                bucket['tokens'] + tokens_to_add
            )
            bucket['last_update'] = now

            # Check minute limit
            if now - bucket['minute_start'] >= 60:
                bucket['minute_count'] = 0
                bucket['minute_start'] = now

            if bucket['minute_count'] >= self.config.requests_per_minute:
                return False, f"Rate limit exceeded: {self.config.requests_per_minute} requests/minute"

            # Check hour limit
            if now - bucket['hour_start'] >= 3600:
                bucket['hour_count'] = 0
                bucket['hour_start'] = now

            if bucket['hour_count'] >= self.config.requests_per_hour:
                return False, f"Rate limit exceeded: {self.config.requests_per_hour} requests/hour"

            # Check token bucket
            if bucket['tokens'] < 1:
                wait_time = (1 - bucket['tokens']) * (60.0 / self.config.requests_per_minute)
                return False, f"Rate limit exceeded. Retry after {wait_time:.1f}s"

            # Consume token and increment counters
            bucket['tokens'] -= 1
            bucket['minute_count'] += 1
            bucket['hour_count'] += 1

            return True, None

    def reset_client(self, client_id: str):
        """Reset rate limit for specific client"""
        if client_id in self.client_buckets:
            del self.client_buckets[client_id]

    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit statistics for client"""
        if client_id not in self.client_buckets:
            return {"requests": 0, "tokens": self.config.burst_size}

        bucket = self.client_buckets[client_id]
        return {
            "tokens_remaining": int(bucket['tokens']),
            "requests_this_minute": bucket['minute_count'],
            "requests_this_hour": bucket['hour_count'],
            "burst_size": self.config.burst_size,
            "minute_limit": self.config.requests_per_minute,
            "hour_limit": self.config.requests_per_hour
        }


# ==============================================================================
# SQL Injection Prevention
# ==============================================================================

class SQLValidator:
    """
    Validates SQL queries to prevent injection and dangerous operations
    """

    def __init__(self, config: SecurityConfig):
        self.config = config

    def validate_sql_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query for security

        Args:
            query: SQL query string

        Returns:
            (valid, error_message) - True if valid, error message if invalid
        """
        if not query or not query.strip():
            return False, "Empty SQL query"

        # Check length
        if len(query) > self.config.max_sql_query_length:
            return False, f"SQL query too long (max {self.config.max_sql_query_length} characters)"

        # Normalize query for checking
        normalized = query.upper().strip()

        # Check for forbidden keywords
        for keyword in self.config.forbidden_sql_keywords:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, normalized):
                return False, f"Forbidden SQL keyword: {keyword}"

        # Check that query starts with allowed keyword
        starts_with_allowed = False
        for keyword in self.config.allowed_sql_keywords:
            if normalized.startswith(keyword):
                starts_with_allowed = True
                break

        if not starts_with_allowed:
            allowed = ', '.join(sorted(self.config.allowed_sql_keywords))
            return False, f"Query must start with allowed keyword: {allowed}"

        # Check for common SQL injection patterns
        injection_patterns = [
            r";\s*DROP",
            r";\s*DELETE",
            r";\s*INSERT",
            r";\s*UPDATE",
            r"--\s*$",  # SQL comment at end
            r"/\*.*\*/", # Multi-line comment
            r"UNION\s+SELECT",  # UNION injection
            r"OR\s+1\s*=\s*1",  # Classic injection
            r"OR\s+'1'\s*=\s*'1'",
            r"EXEC\s*\(",  # Stored procedure execution
        ]

        for pattern in injection_patterns:
            if re.search(pattern, normalized):
                return False, f"Potential SQL injection detected: pattern '{pattern}'"

        return True, None

    def sanitize_sql_identifier(self, identifier: str) -> str:
        """
        Sanitize SQL identifier (table/column name)

        Args:
            identifier: SQL identifier to sanitize

        Returns:
            Sanitized identifier
        """
        # Remove any non-alphanumeric characters except underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)

        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized

        return sanitized


# ==============================================================================
# Path Traversal Prevention
# ==============================================================================

class PathValidator:
    """
    Validates file paths to prevent traversal attacks
    """

    def __init__(self, config: SecurityConfig, project_root: str):
        self.config = config
        self.project_root = project_root

    def validate_file_path(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate file path for security

        Args:
            file_path: File path to validate

        Returns:
            (valid, error_message) - True if valid, error message if invalid
        """
        import os

        if not file_path:
            return False, "Empty file path"

        # Check for forbidden patterns
        for pattern in self.config.forbidden_path_patterns:
            if re.search(pattern, file_path):
                return False, f"Forbidden path pattern: {pattern}"

        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext and ext.lower() not in self.config.allowed_file_extensions:
            allowed = ', '.join(sorted(self.config.allowed_file_extensions))
            return False, f"File extension '{ext}' not allowed. Allowed: {allowed}"

        # Resolve to absolute path and check it's within project root
        try:
            abs_path = os.path.abspath(os.path.join(self.project_root, file_path))
            abs_root = os.path.abspath(self.project_root)

            if not abs_path.startswith(abs_root):
                return False, "Path is outside project root"

        except Exception as e:
            return False, f"Invalid path: {e}"

        return True, None


# ==============================================================================
# Request Size Validation
# ==============================================================================

class RequestValidator:
    """
    Validates request sizes and parameters
    """

    def __init__(self, config: SecurityConfig):
        self.config = config

    def validate_request_size(self, data: Any) -> tuple[bool, Optional[str]]:
        """
        Validate request data size

        Args:
            data: Request data (dict, string, bytes, etc.)

        Returns:
            (valid, error_message)
        """
        import sys

        size = sys.getsizeof(data)

        if size > self.config.max_request_size_bytes:
            max_mb = self.config.max_request_size_bytes / 1_048_576
            actual_mb = size / 1_048_576
            return False, f"Request too large: {actual_mb:.2f}MB (max {max_mb:.2f}MB)"

        return True, None

    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate request parameters

        Args:
            params: Request parameters dictionary

        Returns:
            (valid, error_message)
        """
        if not isinstance(params, dict):
            return False, "Parameters must be a dictionary"

        # Check for empty parameters
        if not params:
            return False, "Empty parameters"

        # Check each parameter value
        for key, value in params.items():
            if value is None:
                continue

            # Check string lengths
            if isinstance(value, str) and len(value) > 100_000:
                return False, f"Parameter '{key}' too long (max 100,000 characters)"

        return True, None


# ==============================================================================
# Timeout Enforcement
# ==============================================================================

async def with_timeout(coro, timeout: float, operation_name: str = "Operation"):
    """
    Execute coroutine with timeout

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name for error messages

    Returns:
        Result from coroutine

    Raises:
        TimeoutError: If operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"{operation_name} timed out after {timeout}s")
        raise TimeoutError(f"{operation_name} timed out after {timeout}s")


def enforce_timeout(timeout_seconds: Optional[float] = None):
    """
    Decorator to enforce timeout on async functions

    Args:
        timeout_seconds: Timeout in seconds (None = use default)

    Example:
        @enforce_timeout(30.0)
        async def slow_operation():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            timeout = timeout_seconds or 30.0
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} timed out after {timeout}s")
                raise TimeoutError(f"{func.__name__} timed out after {timeout}s")

        return wrapper
    return decorator


# ==============================================================================
# Security Manager (Main Interface)
# ==============================================================================

class SecurityManager:
    """
    Central security manager that coordinates all security features
    """

    def __init__(self, config: SecurityConfig, project_root: str):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit)
        self.sql_validator = SQLValidator(config)
        self.path_validator = PathValidator(config, project_root)
        self.request_validator = RequestValidator(config)

        # Track failed requests for IP blocking
        self.failed_requests: Dict[str, List[float]] = defaultdict(list)

    async def validate_request(
        self,
        client_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Comprehensive request validation

        Args:
            client_id: Client identifier
            tool_name: Name of tool being called
            arguments: Tool arguments

        Returns:
            (valid, error_message)
        """
        # 1. Check rate limit
        allowed, message = await self.rate_limiter.check_rate_limit(client_id)
        if not allowed:
            logger.warning(f"Rate limit exceeded for client {client_id}: {message}")
            return False, message

        # 2. Validate request size
        valid, message = self.request_validator.validate_request_size(arguments)
        if not valid:
            logger.warning(f"Request size validation failed for {client_id}: {message}")
            return False, message

        # 3. Validate parameters
        valid, message = self.request_validator.validate_parameters(arguments)
        if not valid:
            logger.warning(f"Parameter validation failed for {client_id}: {message}")
            return False, message

        # 4. Tool-specific validation
        if tool_name in ('query_database', 'query_rds_database'):
            sql_query = arguments.get('sql') or arguments.get('sql_query')
            if sql_query:
                valid, message = self.sql_validator.validate_sql_query(sql_query)
                if not valid:
                    logger.warning(f"SQL validation failed for {client_id}: {message}")
                    self._record_failed_request(client_id)
                    return False, message

        elif tool_name in ('read_file', 'read_project_file'):
            file_path = arguments.get('file_path') or arguments.get('path')
            if file_path:
                valid, message = self.path_validator.validate_file_path(file_path)
                if not valid:
                    logger.warning(f"Path validation failed for {client_id}: {message}")
                    self._record_failed_request(client_id)
                    return False, message

        return True, None

    def _record_failed_request(self, client_id: str):
        """Record failed request for IP blocking"""
        now = time.time()

        # Remove old failures (older than 1 hour)
        self.failed_requests[client_id] = [
            t for t in self.failed_requests[client_id]
            if now - t < 3600
        ]

        # Add new failure
        self.failed_requests[client_id].append(now)

        # Check if client should be blocked
        if len(self.failed_requests[client_id]) >= self.config.max_failed_requests:
            logger.error(
                f"Client {client_id} exceeded max failed requests "
                f"({self.config.max_failed_requests}). Consider blocking."
            )

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            "rate_limiter_enabled": self.config.rate_limit.enabled,
            "active_clients": len(self.rate_limiter.client_buckets),
            "clients_with_failures": len(self.failed_requests),
            "total_failed_requests": sum(len(fails) for fails in self.failed_requests.values())
        }


# ==============================================================================
# Example Usage
# ==============================================================================

async def example_usage():
    """Example of using the security module"""

    # Create security configuration
    config = SecurityConfig(
        rate_limit=RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100
        )
    )

    # Create security manager
    security = SecurityManager(config, project_root="/Users/ryanranft/nba-mcp-synthesis")

    # Validate a database query request
    client_id = "test_client_1"
    tool_name = "query_database"
    arguments = {
        "sql_query": "SELECT * FROM games WHERE game_date > '2024-01-01' LIMIT 10"
    }

    valid, message = await security.validate_request(client_id, tool_name, arguments)

    if valid:
        print("✅ Request validated successfully")
    else:
        print(f"❌ Request validation failed: {message}")

    # Try an invalid SQL query
    bad_arguments = {
        "sql_query": "DROP TABLE games"
    }

    valid, message = await security.validate_request(client_id, tool_name, bad_arguments)
    print(f"\nInvalid SQL validation: {message}")

    # Get security stats
    stats = security.get_security_stats()
    print(f"\nSecurity stats: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())
